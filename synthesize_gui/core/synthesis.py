"""
GLASS LAS (Local Anomaly Synthesis) extracted as a stand-alone callable.

Mirrors the synthesis section of `datasets.mvtec.MVTecDataset.__getitem__`
(lines 172-212) without any of the dataset-iteration / fg_mask path logic
or DataLoader wiring. The intent is that this module is the *only* place
where Perlin x DTD blending is implemented in this workspace; the GUI app
and `dump_synthetic.py` both call into here.

Output modes:
  - working_size (default 288): the resolution at which the Perlin anomaly
    mask is generated. Must be square; Perlin generation is square-only
    upstream. The OK image and texture are NOT downsampled to this size --
    only the mask is. The beta-blend runs at the full output resolution so
    non-anomalous regions stay bit-identical to the source image (no
    downscale->upscale roundtrip and no ImageNet normalize roundtrip, which
    were the two sources of whole-image "texture" degradation).
  - output_size (None or int):
        None -> blend + return at the original PIL image size (Q3 default)
        int  -> blend + return at this square size
                (used by `dump_synthetic.py` to keep regression == 288)

The function is pure: same global RNG state in -> same output out. Caller
is expected to seed *three* RNGs before invoking:

    np.random.seed(s)
    torch.manual_seed(s)
    imgaug.seed(s)        # perlin.py uses imgaug.iaa.Affine internally

Missing the imgaug seed will give visually similar but pixel-different output
runs even with identical np/torch seeds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import PIL.Image
import torch
from torchvision import transforms

from ._vendored.perlin import perlin_mask


@dataclass
class SynthParams:
    """Knobs exposed to the GUI / CLI for one synthesis call."""

    working_size: int = 288
    output_size: Optional[int] = None  # None => preserve original image size
    perlin_scale_min: int = 0  # exponent: 2**min is the smallest scale
    perlin_scale_max: int = 6  # exponent: 2**max is the largest scale
    beta_mean: float = 0.5
    beta_std: float = 0.1
    rand_aug: bool = True
    downsampling: int = 8  # working_size // downsampling -> feat_size for mask_s
    use_foreground: bool = False  # if True, fg_mask must be provided
    device: str = "auto"  # "auto" -> CUDA if available else CPU; "cuda"; "cpu"


@dataclass
class SynthResult:
    """Output of a single LAS call."""

    ng_image_bgr: np.ndarray  # H x W x 3, BGR uint8 (cv2-friendly)
    mask_uint8: np.ndarray  # H x W, 0/255 uint8 binary mask at output res
    mask_l_float: np.ndarray  # H_work x W_work, 0/1 float mask at working res
    mask_s_float: np.ndarray  # feat x feat, 0/1 float mask at feature res
    beta_used: float
    perlin_thr_kind: str  # "or", "and", or "single" (which combination was sampled)


def _resolve_device(name: str) -> torch.device:
    """Map SynthParams.device to a torch.device.

    "auto" -> CUDA when a GPU is visible, else CPU (no hard dependency on a
    GPU being present, so the same build runs on CPU-only machines).
    "cuda"/"gpu" -> CUDA, hard-erroring if unavailable (explicit opt-in).
    "cpu" -> force CPU.
    """
    n = (name or "auto").strip().lower()
    if n == "cpu":
        return torch.device("cpu")
    if n in ("cuda", "gpu"):
        if not torch.cuda.is_available():
            raise RuntimeError(
                "device='cuda' requested but torch.cuda.is_available() is "
                "False (no CUDA GPU / driver visible to this build)."
            )
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _image_to_unit_tensor(
    image: PIL.Image.Image, target_hw: Tuple[int, int]
) -> torch.Tensor:
    """OK image -> 3xHxW float tensor in [0, 1], WITHOUT ImageNet normalize.

    When the image is already at the target resolution (the common
    output_size=None case) the source pixels are used verbatim, so any
    region the anomaly mask does not touch round-trips back to the exact
    original bytes. A genuine resolution change triggers a single
    high-quality resize -- never the old downscale->upscale roundtrip.
    """
    h, w = target_hw
    img = image.convert("RGB")
    if img.height != h or img.width != w:
        img = img.resize((w, h), PIL.Image.LANCZOS)
    arr = np.array(img, dtype=np.uint8)  # np.array copies -> writable tensor
    return torch.from_numpy(arr).permute(2, 0, 1).contiguous().float() / 255.0


def _texture_to_unit_tensor(
    texture: PIL.Image.Image, target_hw: Tuple[int, int], rand_aug: bool
) -> torch.Tensor:
    """Texture -> 3xHxW float tensor in [0, 1] covering the full output frame.

    Mirrors `MVTecDataset.rand_augmenter`'s 3-from-pool pick so the global
    np.random draw order is unchanged (seeded runs stay reproducible), but
    produces an un-normalized tensor at the output resolution instead of a
    normalized square `working_size` crop. Resize(max(h, w)) guarantees both
    edges are >= the crop, so CenterCrop((h, w)) always has full coverage.
    """
    h, w = target_hw
    tex = texture.convert("RGB")
    steps = [transforms.Resize(max(h, w))]
    if rand_aug:
        list_aug = [
            transforms.ColorJitter(contrast=(0.8, 1.2)),
            transforms.ColorJitter(brightness=(0.8, 1.2)),
            transforms.ColorJitter(saturation=(0.8, 1.2), hue=(-0.2, 0.2)),
            transforms.RandomHorizontalFlip(p=1),
            transforms.RandomVerticalFlip(p=1),
            transforms.RandomGrayscale(p=1),
            transforms.RandomAutocontrast(p=1),
            transforms.RandomEqualize(p=1),
            transforms.RandomAffine(degrees=(-45, 45)),
        ]
        aug_idx = np.random.choice(np.arange(len(list_aug)), 3, replace=False)
        steps += [list_aug[aug_idx[0]], list_aug[aug_idx[1]], list_aug[aug_idx[2]]]
    steps += [transforms.CenterCrop((h, w)), transforms.ToTensor()]
    return transforms.Compose(steps)(tex)


def _resize_mask_uint8(mask: np.ndarray, target_hw: Tuple[int, int]) -> np.ndarray:
    """Nearest-neighbor upsample of a 0/255 binary mask."""
    import cv2
    h, w = target_hw
    if mask.shape[0] == h and mask.shape[1] == w:
        return mask
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)


def synthesize_one(
    image: PIL.Image.Image,
    texture: PIL.Image.Image,
    params: SynthParams,
    fg_mask: Optional[PIL.Image.Image] = None,
) -> SynthResult:
    """Run one LAS step. See module docstring.

    Args:
        image:    OK (normal) source image, RGB.
        texture:  Anomaly source texture, RGB.
        params:   Knobs; see SynthParams.
        fg_mask:  Optional foreground mask (any mode; will be converted to {0,1}).
                  Required iff params.use_foreground is True.
    """
    if params.working_size <= 0:
        raise ValueError("working_size must be positive")
    if params.working_size % params.downsampling != 0:
        raise ValueError(
            f"working_size ({params.working_size}) must be divisible by "
            f"downsampling ({params.downsampling})"
        )
    if params.use_foreground and fg_mask is None:
        raise ValueError("use_foreground=True but fg_mask is None")

    # Resolution at which we composite the final image. output_size=None
    # keeps the source resolution so untouched regions stay bit-identical to
    # the original (no whole-image downscale/upscale, no normalize roundtrip).
    if params.output_size is None:
        target_h, target_w = image.height, image.width
    else:
        target_h = target_w = int(params.output_size)

    work = params.working_size
    feat = work // params.downsampling
    device = _resolve_device(params.device)

    # --- 1. OK image + texture at OUTPUT resolution (un-normalized) ---------
    # The texture transform consumes the np.random.choice draw first, exactly
    # as the original working-size pipeline did, so the global RNG draw order
    # is unchanged and seeded runs stay reproducible.
    tex_t = _texture_to_unit_tensor(
        texture, (target_h, target_w), params.rand_aug
    ).to(device)
    img_t = _image_to_unit_tensor(image, (target_h, target_w)).to(device)

    # --- 2. Foreground mask (working res; perlin_mask is square-only) ------
    if params.use_foreground:
        # Match MVTecDataset: ToTensor then ceil to {0,1}, take channel 0.
        fg_t = transforms.Compose([
            transforms.Resize(work),
            transforms.CenterCrop(work),
            transforms.ToTensor(),
        ])(fg_mask)
        mask_fg = torch.ceil(fg_t[0])
    else:
        # Scalar tensor [1] broadcasts to ones inside perlin_mask; matches
        # MVTecDataset's `mask_fg = torch.tensor([1])` default.
        mask_fg = torch.tensor([1])

    # --- 3. Perlin mask at working resolution ------------------------------
    # perlin_mask (vendored, unmodifiable) is numpy/imgaug, square-only, and
    # CPU-bound; only the mask is generated at `work`, never the image.
    img_shape = (3, work, work)
    mask_s_np, mask_l_np = perlin_mask(
        img_shape,
        feat,
        params.perlin_scale_min,
        params.perlin_scale_max,
        mask_fg,
        flag=1,
    )

    # --- 4. Soft-upsample the mask to OUTPUT resolution --------------------
    # perlin_mask returns a hard {0,1} field at `work`; bilinear upsampling
    # gives a soft alpha so the blend boundary is anti-aliased at the output
    # resolution instead of a nearest-neighbour staircase.
    import cv2
    mask_soft = cv2.resize(
        mask_l_np.astype(np.float32),
        (target_w, target_h),
        interpolation=cv2.INTER_LINEAR,
    )
    m_t = torch.from_numpy(np.clip(mask_soft, 0.0, 1.0))[None, :, :].to(device)

    # --- 5. Beta blend at OUTPUT resolution (runs on `device`) -------------
    beta = float(np.clip(np.random.normal(loc=params.beta_mean, scale=params.beta_std), 0.2, 0.8))
    aug_t = (
        img_t * (1.0 - m_t)
        + (1.0 - beta) * tex_t * m_t
        + beta * img_t * m_t
    )

    # --- 6. To BGR uint8. Where m == 0, aug_t == img_t exactly, and since
    #        img_t is the raw source (uint8 -> /255 -> *255 -> rint is the
    #        identity) non-anomalous pixels round-trip back to the original
    #        bytes -- zero background degradation. -------------------------
    arr = aug_t.detach().cpu().numpy().transpose(1, 2, 0)  # HxWx3 RGB [0,1]
    arr = np.clip(arr[:, :, ::-1], 0.0, 1.0)               # RGB -> BGR
    ng_bgr = np.rint(arr * 255.0).astype(np.uint8)

    # --- 7. Binary GT mask at output res (MVTec ground_truth convention) --
    mask_l_uint8 = (mask_l_np > 0.5).astype(np.uint8) * 255
    mask_uint8 = _resize_mask_uint8(mask_l_uint8, (target_h, target_w))

    return SynthResult(
        ng_image_bgr=ng_bgr,
        mask_uint8=mask_uint8,
        mask_l_float=mask_l_np.astype(np.float32),
        mask_s_float=mask_s_np.astype(np.float32),
        beta_used=beta,
        perlin_thr_kind="combined",  # internal kind is opaque; perlin.py samples it
    )

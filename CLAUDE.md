# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This workspace wraps an upstream research codebase **and** builds a GUI application on top of its anomaly-synthesis branch:

- `GLASS/` — upstream PyTorch implementation (its own git repo, MIT-licensed, mirror of `cqylunlun/GLASS`, gitignored from the parent repo). Treat as the working root for any model/training change.
- `GLASS/dump_synthetic.py` — local CLI helper (added by this workspace, not upstream). Since 2026-05-02 it is a thin wrapper that delegates to `synthesizer_app.core.synthesis.synthesize_one`; output layout (`original/synthetic/mask/panel`) is unchanged for backward compat.
- `GLASS/synthesizer_app/` — **NG-data synthesis GUI app**, the long-term deliverable. Lives inside the GLASS clone for development convenience but is **also published as a standalone public repo** (see "Standalone publication" below).
  - `core/synthesis.py` — pure LAS function `synthesize_one(image, texture, params, fg_mask=None) -> SynthResult`. Single source of truth for Perlin × DTD blending in this workspace.
  - `core/_vendored/perlin.py` — vendored copy of upstream `GLASS/perlin.py` (MIT, attribution preserved). `synthesis.py` imports from here, **not** from `GLASS/perlin.py`, so the app is clone-and-run self-contained.
  - `core/io_utils.py` — generic recursive image enumeration (so non-DTD texture sources can plug in later).
  - `core/exporter.py` — MVTec-compatible writer (`train/good`, `test/synthetic`, `ground_truth/synthetic`, `run.json`).
  - `ui/custom_styles_jp.py`, `ui/TR_inc_logo.png` — TOMOMI RESEARCH unified GUI style assets, copied from `skills/tomomi-gui-style/`.
  - `ui/gui_main_ui.py`, `gui_main.py` — pure Tkinter + ttk app (no Pygubu, per user decision). Threaded batch worker + `queue.Queue`-based main-thread dispatch.
  - `tests/test_synthesis.py` — unittest for shape, determinism, fg-mask validation.
  - `LICENSE`, `LICENSE_GLASS`, `README.md`, `requirements.txt` — standalone-repo metadata.
- `GLASS/requirements_original.txt` — verbatim copy of `requirements.txt`. Used as the canonical install for `glass_env`.
- `GLASS/requirements_updated_current_env.txt` — abandoned attempt to install GLASS into the system's Python 3.13 env. Kept for history only; do not install from it.
- `00.docs/` — reference PDF of the GLASS paper (`2407.09359v1.pdf`, ECCV 2024) **and** `GLASS_synth_gui_plan.md` (the GUI-app implementation plan with phase breakdown and confirmed decisions).
- `01.reports/GLASS_execution_plan.md` — detailed reproduction plan (datasets, risks, commands).
- `01.reports/GLASS_dependency_install_report.md` — record of how `glass_env` was actually built and verified, including the imgaug × NumPy 2.x detour.
- `synthetic_dump/<class>/{original,synthetic,mask,panel}/` — sample output of `dump_synthetic.py`. Inspectable evidence of the LAS branch's synthesis quality.
- `skills/` — local Claude skills (`karphathy-guidelines/`, `tomomi-gui-style/`). The GUI-style skill is the design system the synthesizer GUI must follow.

## Environment

Use the existing **`glass_env` conda environment** for anything GLASS-related. Don't try to reuse the system `synthetic_data_py313` (Python 3.13 + numpy 2.x); the upstream `imgaug==0.4.0` calls `np.sctypes` which was removed in NumPy 2.0, and there are no Python 3.13 wheels for `numpy<2`.

`glass_env` was built to match the upstream pinning exactly:

- **conda env path**: `C:\Users\seong\anaconda3\envs\glass_env`
- **Python**: 3.9.15
- **PyTorch**: 2.1.2+cu118 / torchvision 0.16.2+cu118 (installed from `https://download.pytorch.org/whl/cu118` *before* `pip install -r requirements_original.txt`, otherwise pip auto-picks a CPU wheel)
- **CUDA wheel**: cu118; the local NVIDIA driver (595.97) supports CUDA 13 but is forward-compatible with cu118 binaries — verified working at runtime
- **GPU**: NVIDIA RTX 3060 Laptop, **6 GB VRAM** — the upstream `--batch_size 8` setting may OOM; smoke test ran with `--batch_size 2`
- **All other deps** at their upstream pins (numpy 1.26.3, imgaug 0.4.0, timm 0.9.12, pandas 1.5.2, etc.)

Conda is not on `PATH` in the default Git Bash session. Either invoke the env's interpreter directly:

```bash
GLASS_PY="C:/Users/seong/anaconda3/envs/glass_env/python.exe"
"$GLASS_PY" main.py ...
```

…or activate via the full conda path:

```bash
"C:/Users/seong/anaconda3/Scripts/conda.exe" activate glass_env
```

## Local datasets and quirks (this workstation)

These paths are pinned for the host the workspace lives on. Pass them via CLI; do **not** edit upstream `shell/run-*.sh` to bake them in (those edits would dirty the upstream working tree).

| Flag | Path | Notes |
|---|---|---|
| `--datapath` (mvtec) | `C:/Datasets-rev002/01.MVTEC_Anomaly_Detection` | All 15 standard classes present |
| `--augpath` | `C:/Datasets-rev002/DTD/images` | Full DTD r1.0.1: 47 categories × ~120 jpg = 5640 jpg |

Dataset quirks already accommodated:

- **Class name mismatch**: the local layout has `leather_original` instead of `leather`. A Windows directory junction `C:\Datasets-rev002\01.MVTEC_Anomaly_Detection\leather` → `leather_original` was created so GLASS's hardcoded class name resolves correctly. Don't rename the junction or the underlying folder.
- **No `fg_mask/`**: the official Foreground Mask zip from the README's Google Drive has not been downloaded. **Run with `--fg 0`** until it is. `--fg 1` will crash inside `MVTecDataset.__getitem__` because of the missing `fg_mask/<class>/<file>.png` lookup.
- **`leather`/`carpet` shells contain extra sibling folders** (`capsule_wo_bg_clean`, `transistor-original`, `carpet/test-backup`, etc.). Harmless — GLASS only iterates folders matching its hardcoded class list. Don't include them in `-d` flags.

## Reproduction state

End-to-end smoke test on `mvtec_carpet` succeeded (2026-05-01):

- Command: `--meta_epochs 1 --limit 8 --batch_size 2 --distribution 2 --fg 0 -d carpet`
- Runtime: ~11 min (≈8 min was first-iteration CUDA warmup; subsequent iterations ≈1 sec each)
- Result: I-AUROC 92.42 / P-AUROC 93.90 / P-PRO 78.03 with only 10 training samples seen (well below the paper's 99.9 / 99.3 but the pipeline runs cleanly)
- Artifacts produced: `GLASS/results/models/backbone_0/mvtec_carpet/{ckpt.pth, ckpt_best_0.pth, tb/}`, 117 PNGs each in `results/{training,eval}/mvtec_carpet/`, `results/results.csv`

What this means for future runs:

- Full upstream training (`--meta_epochs 640 --limit 392 --batch_size 8` × 15 classes) is not feasible on the 6 GB GPU within reasonable wall time. Either drop to a much smaller `meta_epochs`/`limit`, swap to a smaller backbone, or use the upstream-released checkpoints for evaluation (`--test test`).
- For "does the synthesis look right" investigations, prefer `dump_synthetic.py` (no GPU at all) over running training.
- `--distribution 2` (force manifold) is the cleanest setting for isolated runs because it skips the xlsx side-effect machinery; only switch back to `--distribution 0/1` when you specifically want the spectrogram judgment.

`onnx`, `onnxruntime-gpu`, and `onnxsim` are installed (per upstream pins) but the export workflow has not been exercised on this workstation. `onnxruntime-gpu==1.18.1` is built for CUDA 11.8 + cuDNN 8.x; if it fails at runtime under the current driver, fall back to CPU `onnxruntime`.

## Running training and evaluation

All entry points go through `GLASS/main.py`, a click chain of three subcommands invoked in order: top-level options → `net ...` → `dataset ...`. Driver scripts in `GLASS/shell/run-*.sh` show the canonical argument set per dataset (`run-mvtec.sh`, `run-visa.sh`, `run-mpdd.sh`, `run-wfdd.sh`, `run-mad-man.sh`, `run-mad-sys.sh`, `run-custom.sh`).

Important conventions baked into those shell scripts:

- They `cd ..` first so `python main.py` runs from the `GLASS/` root, not from `shell/`. Output paths like `./results/...` and `./datasets/excel/...` are resolved relative to `GLASS/`.
- Top-level `--test ckpt` = train + evaluate; `--test test` = evaluation only (loads `ckpt_best_*.pth` from the model dir).
- `--datapath` and `--augpath` must exist (click validates with `exists=True`). `augpath` is the DTD texture dataset used to synthesize anomalies.
- `-d` repeats per subdataset (class). The shell scripts build `flags=()` from a `classes=(...)` array.
- For a new dataset, copy `run-custom.sh` and adapt; `main.py` only knows four dataset registries (`mvtec`, `visa`, `mpdd`, `wfdd`), and `mpdd`/`wfdd` reuse `MVTecDataset`. A "custom" dataset must follow MVTec's directory layout (`<class>/{train,test,ground_truth}/...`).

To run a single class on MVTec for debugging, edit the `classes=(...)` array in the shell script (or invoke `python main.py ... -d <class> mvtec <datapath> <augpath>` directly).

## Distribution / foreground flags (non-obvious)

These two args control GLASS's two modeling choices and have meanings beyond plain bool:

`--distribution`:
- `0` — read SVD/manifold choice from `./datasets/excel/<dataset>_distribution.xlsx` (the file `main.py` writes after a spectrogram-judgment pass).
- `1` — judge per-class by image-level spectrogram (`utils.distribution_judge`); training short-circuits and writes the xlsx row instead of training.
- `2` — force manifold (`svd=0`).
- `3` — force hypersphere (`svd=1`).
- `4` — read the xlsx but invert the choice.

`--fg`:
- `0` — no foreground mask.
- `1` — load `<datapath>/fg_mask/<class>/<file>.png` for every train image. Required by Perlin-mask synthesis when used.
- `2` — read per-class foreground decision from the xlsx.

If `--fg 1`, the foreground mask folder must exist alongside the class folders or training will crash inside `MVTecDataset.__getitem__`.

The first run on a new dataset is typically `--distribution 1 --test ckpt` to populate the xlsx; subsequent runs use `--distribution 0`.

## Pretrained results

The README documents a Google Drive `results/` folder with `ckpt_best_*.pth` weights for MVTec. Drop it at `GLASS/results/` before running with `--test test`. `glass.GLASS.tester` looks up `ckpt_best*` via glob in `<results_path>/models/backbone_<i>/<dataset>_<class>/`.

## ONNX export

`GLASS/onnx/pth2onnx.py` exports a single trained checkpoint to ONNX, then runs `onnxsim.simplify`. The script has hardcoded paths (`/root/.cache/torch/hub/...` for backbone weights, `../results/models/backbone_0/wfdd_grid_cloth/...` for the checkpoint) — edit them before running. `onnx/ort.py` is a standalone CUDA inference smoke test against the exported model.

## Code architecture

The training pipeline is built around three composed pieces:

1. **Backbone feature extractor** (`backbones.py` + `common.NetworkFeatureAggregator`). `backbones.load(name)` returns a torchvision/timm pretrained model. Features are pulled via forward hooks on named layers (`-le layer2 -le layer3` for the wide_resnet50_2 default), and the last-requested layer raises `LastLayerToExtractReachedException` to short-circuit the rest of the forward pass. Patches are extracted by `model.PatchMaker` (Unfold with `patchsize=3`, `stride=1`), mean-pooled to `pretrain_embed_dimension`, and aggregated to `target_embed_dimension`.

2. **Anomaly synthesis** (`datasets/mvtec.py` + `perlin.py`). For each training sample, a random DTD texture is loaded, a Perlin-noise mask is generated and (optionally) ANDed with the foreground mask, and the augmented image is `image * (1 - mask) + (1 - β) * aug * mask + β * image * mask` with `β ~ N(mean, std)` clipped to `[0.2, 0.8]`. `mask_s` (downsampled, feature-resolution) is the per-patch label fed to the discriminator.

3. **Discriminator + projection + gradient-ascent mining** (`glass.py` + `model.py`). `Projection` is an MLP applied to feature patches; `Discriminator` is a small MLP+sigmoid that scores each patch as anomalous. Per training step (`_train_discriminator`):
   - True features and Gaussian-perturbed copies are scored; BCE loss trains the discriminator to separate them.
   - Inner loop (`--step`, default 20) does gradient ascent on `gaus_feats` w.r.t. `gaus_loss` to mine harder negatives, projecting them back onto an annulus around the class center `c` (svd=1, hypersphere) or around the true features (svd=0, manifold) every 5 steps. `--radius` controls the projection quantile.
   - Synthesized fake features (from the Perlin-masked augmentations) get a focal loss against `mask_s`; with `--p > 0`, only the hardest top-p quantile contributes.
   - One epoch is capped at `--limit` samples (default 392) regardless of dataset size.

`GLASS.trainer` runs `--meta_epochs` of this, evaluates every `--eval_epochs` epoch on the val/test loader, and keeps the checkpoint with the best `image_auroc + pixel_auroc`. `GLASS.tester` reloads the best checkpoint and recomputes metrics including PRO (`metrics.compute_pro`, ~minutes per class).

## Outputs and side effects to be aware of

A run scribbles into several `GLASS/`-relative paths:
- `./results/models/backbone_<i>/<dataset>_<class>/ckpt_best_<epoch>.pth` — best checkpoint (only one kept; older ones are deleted in-place).
- `./results/models/.../ckpt.pth` — latest (overwritten every epoch).
- `./results/models/.../tb/` — TensorBoard logs.
- `./results/training/<dataset>_<class>/` — image / GT / heatmap triptychs from the most recent eval.
- `./results/eval/<dataset>_<class>/` — copy of `training/` snapshotted when a new best was set.
- `./results/judge/{avg,fft}/<flag>/<name>.png` — spectrogram-judgment artifacts (only when `--distribution 1`).
- `./datasets/excel/<dataset>_distribution.xlsx` — distribution/foreground decisions, created and read by both `main.py` and the dataset class. `MVTecDataset` reads it during `__init__` if `--fg 2`.
- `./results/results.csv` — aggregate metrics, rewritten after each class.

`utils.create_storage_folder` ignores `log_project`/`log_group`/`run_name` despite their being CLI options — `results_path` is used verbatim. Don't rely on the iteration/overwrite mode argument either.

## Skills in this workspace

`skills/karphathy-guidelines/SKILL.md` and `skills/tomomi-gui-style/SKILL.md` are local skills available to Claude Code in this directory. **The GUI-style skill is now load-bearing** — `synthesizer_app/ui/` must follow it (Meiryo 12 / `primary.TButton` / `custom.TLabelframe` / TR copyright footer / threaded workers + `root.after(0, ...)` posting).

## NG-data synthesis GUI app (work in progress)

The end deliverable of this workspace is **a Tkinter desktop app that synthesizes NG (anomaly) images + binary masks for downstream AI anomaly-detection training**. The GLASS reproduction work was groundwork for this; the app reuses GLASS's LAS branch only (GAS / discriminator / training loop are out of scope).

Confirmed decisions (see `00.docs/GLASS_synth_gui_plan.md` §10):

| Decision | Value |
|---|---|
| GUI framework | pure Tkinter + ttk (no Pygubu) |
| Output format | MVTec-compatible only (`<class>/test/synthetic/`, `<class>/ground_truth/synthetic/`) |
| OK-image resolution | preserve original (synthesize at `working_size=288` internally, then resize to source res) |
| Texture source | extensible: any directory walked recursively for image files (DTD today, in-house defect photos later) |
| Class scope | one class per app instance |
| Foreground mask absent | warn but proceed |
| `dump_synthetic.py` | refactored to call `synthesizer_app.core.synthesis` (regression-checked) |

Phase status: **Phase 0 (skeleton) and Phase 1 (core synthesis function + CLI refactor + unit tests) are done as of 2026-05-02.** Phase 2 (minimum GUI: load OK + texture + output dirs, single preview) is the next step.

### Synthesis API (single source of truth)

```python
from synthesizer_app.core.synthesis import SynthParams, synthesize_one
import numpy as np, torch, imgaug

# All three RNGs must be seeded for reproducibility — perlin.py uses imgaug
# internally (iaa.Affine rotate), which has its own RNG.
np.random.seed(0); torch.manual_seed(0); imgaug.seed(0)

result = synthesize_one(
    image=PIL.Image.open("ok.png").convert("RGB"),
    texture=PIL.Image.open("dtd.jpg").convert("RGB"),
    params=SynthParams(working_size=288, output_size=None),  # None = preserve source res
)
# result.ng_image_bgr  : H x W x 3 BGR uint8 at output res
# result.mask_uint8    : H x W   0/255 uint8 binary mask at output res
# result.beta_used     : the sampled beta (for logging / labels.csv)
```

`working_size` must be divisible by `downsampling` (default 8) — Perlin mask generation is square-only upstream, so non-square output is achieved by synthesizing at a square `working_size` and resizing to the source aspect ratio at the end.

Run unit tests:

```bash
cd GLASS && "$GLASS_PY" -m unittest synthesizer_app.tests.test_synthesis -v
```

### Standalone publication

`synthesizer_app/` is **also pushed to its own public repo** at https://github.com/kotai2003/glass-synthesizer-app, default branch `main`. The mechanism is `git subtree split --prefix=synthesizer_app` from the **GLASS inner repo** into a `syn_split` branch, then `git push syn_origin syn_split:main`. Two repos hold the same code:

| Repo | Role | Push target |
|---|---|---|
| `cqylunlun/GLASS` (this clone's origin) | upstream mirror, **never push to it** | — |
| `kotai2003/glass-synthesizer-app` (`syn_origin`) | standalone distribution of `synthesizer_app/` | `git push syn_origin syn_split:main` after each split |

When you change anything under `GLASS/synthesizer_app/`, the workflow to publish is:
1. Commit inside the GLASS inner repo as usual.
2. Re-run `git subtree split --prefix=synthesizer_app -b syn_split` (overwrites the local branch with the up-to-date split).
3. `git push syn_origin syn_split:main`.

The vendored `core/_vendored/perlin.py` is what makes the standalone repo runnable without GLASS — never replace it with a `from perlin import ...` that reaches into GLASS root, or the standalone repo will break on clone.

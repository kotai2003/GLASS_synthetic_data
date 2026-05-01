# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This workspace wraps an upstream research codebase rather than being a single project:

- `GLASS/` — the actual PyTorch implementation (its own git repo, MIT-licensed, mirror of `cqylunlun/GLASS`). All code edits happen here.
- `00.docs/` — reference PDF of the GLASS paper (`2407.09359v1.pdf`, ECCV 2024).
- `skills/` — local Claude skills (`karphathy-guidelines/`, `tomomi-gui-style/`). These are guideline/style packs, not part of the model code.

Treat `GLASS/` as the working root for any model/training change.

## Environment

The upstream README pins Python 3.9.15, CUDA 11.8, PyTorch 2.1.2 + torchvision 0.16.2, and was developed on an NVIDIA A800 (80 GB). Recreating the env:

```
conda create -n glass_env python=3.9.15
conda activate glass_env
pip install -r GLASS/requirements.txt
```

`onnx`, `onnxruntime-gpu`, and `onnxsim` are pinned for the export pipeline; do not bump them casually.

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

`skills/karphathy-guidelines/SKILL.md` and `skills/tomomi-gui-style/SKILL.md` are local skills available to Claude Code in this directory. The GUI-style skill is unrelated to the GLASS model code and only applies if you start building Tkinter/ttk tooling around it.

# GLASS 実行計画レポート

- **対象リポジトリ**: [`cqylunlun/GLASS`](https://github.com/cqylunlun/GLASS)
- **論文**: *A Unified Anomaly Synthesis Strategy with Gradient Ascent for Industrial Anomaly Detection and Localization* (ECCV 2024)
- **clone 先**: `./GLASS/`
- **clone 時 commit**: `f788d567db552820d744ca2d93e989265aad8c45` (`update readme`, 2026-03-30)
- **作成日**: 2026-05-01
- **対象 OS**: Windows 11 Home (10.0.26200) / `bash` (Git for Windows 想定)

このレポートは「実行する前に何を確認・準備すべきか」を整理したものであり、コードや環境の変更はまだ行っていません。

---

## 1. リポジトリ構成

### 1.1 ディレクトリツリー（要点のみ）

```
01.GLASS/                            ← 本ワークスペースのルート
├── 00.docs/
│   └── 2407.09359v1.pdf             ← 論文 PDF
├── GLASS/                           ← clone した実装本体（独立した git repo）
│   ├── main.py                      ← エントリポイント（click chain）
│   ├── glass.py                     ← GLASS モデル本体（学習・評価ループ）
│   ├── model.py                     ← Discriminator / Projection / PatchMaker
│   ├── backbones.py                 ← torchvision/timm のバックボーン定義
│   ├── common.py                    ← 特徴量抽出・前処理・後処理
│   ├── datasets/
│   │   ├── __init__.py
│   │   ├── mvtec.py                 ← MVTec / MPDD / WFDD 共通 Dataset
│   │   └── visa.py                  ← VisA 専用 Dataset（マスク処理が異なる）
│   ├── perlin.py                    ← Perlin ノイズによる合成マスク
│   ├── loss.py                      ← FocalLoss
│   ├── metrics.py                   ← AUROC / AP / PRO
│   ├── utils.py                     ← seed, device, FFT 判定, IO
│   ├── shell/                       ← 7 個の実行スクリプト（後述）
│   ├── onnx/
│   │   ├── pth2onnx.py              ← .pth → .onnx 変換
│   │   └── ort.py                   ← ONNX Runtime での推論サンプル
│   ├── figures/                     ← README 用画像
│   ├── requirements.txt
│   ├── README.md
│   └── LICENSE                      ← MIT
├── skills/                          ← Claude Code 用ローカルスキル（実行に無関係）
├── 01.reports/                      ← 本レポートの保存先
└── CLAUDE.md
```

### 1.2 主要ファイルの役割

| ファイル | 役割 |
|---|---|
| `main.py` | `click` の `@main.command("net")` / `@main.command("dataset")` を chain して 1 行で呼び出す。`@main.result_callback()` の `run()` が学習・評価本体を起動 |
| `glass.py` | `GLASS` クラス。`trainer()` で `_train_discriminator()` を `meta_epochs` 回まわし、`tester()` で `ckpt_best_*.pth` をロードして評価 |
| `model.py` | 識別器（小さな MLP）、Projection（線形層）、PatchMaker（`Unfold` ベースのパッチ化） |
| `backbones.py` | `_BACKBONES` 辞書に 40 種以上の torchvision/timm バックボーン名を `eval()` で文字列実行（`pretrained=True` で常時ダウンロード）|
| `datasets/mvtec.py` | `MVTecDataset`。MVTec/MPDD/WFDD いずれもこのクラスを使用 |
| `datasets/visa.py` | `VisADataset`。マスクを `mode='F'` で読み二値化する点が MVTec 版と異なる |
| `perlin.py` | 学習時の擬似異常マスク生成（`imgaug` 依存）|
| `utils.py` | `distribution_judge()` で画像平均の FFT スペクトログラムから「Manifold / HyperSphere」を判別し PNG を出力 |

### 1.3 README の要点

- 推奨環境: **Python 3.9.15 / NVIDIA Tesla A800 (80GB)**。
- 学習データ: **MVTec AD / VisA / MPDD / DTD (補助テクスチャ)**。
- 自製データ: **WFDD / MAD-man / MAD-sys / Foreground Mask**（いずれも Google Drive リンク）。
- 学習済みモデル: **MVTec AD 用 GLASS-j の `results/` フォルダ**を配布（Google Drive）。
- 実行は `./shell/run-<dataset>.sh` を編集してから `bash run-<dataset>.sh`。
- `--test` を `ckpt`（学習）/ `test`（評価のみ）で切り替える。
- foreground mask 不要なデータには `--fg 0` を指定。

### 1.4 設定ファイル / 出力フォルダ

- **設定ファイル**: 専用 YAML/JSON は **無し**。すべての設定は `shell/run-*.sh` の CLI 引数として埋め込まれている。
- **出力フォルダ**（すべて `GLASS/` を CWD としたときの相対パス）:
  - `./results/models/backbone_<i>/<dataset>_<class>/` — `ckpt_best_<epoch>.pth`、`ckpt.pth`、`tb/` (TensorBoard)
  - `./results/training/<dataset>_<class>/` — エポック中の可視化（入力 / GT / ヒートマップ 3 連結 PNG）
  - `./results/eval/<dataset>_<class>/` — ベスト更新時に `training/` をコピー
  - `./results/judge/{avg,fft}/<flag>/<name>.png` — `--distribution 1` のときのみ
  - `./results/results.csv` — 集計指標
  - `./datasets/excel/<dataset>_distribution.xlsx` — distribution / foreground 判定結果（`main.py` が書き、`MVTecDataset` が `--fg 2` 時に読む）

### 1.5 shell スクリプト一覧

| スクリプト | データセット | `--fg` | `--test` 既定 |
|---|---|---|---|
| `run-mvtec.sh` | MVTec AD (15 class) | 1 | `ckpt` |
| `run-visa.sh` | VisA (12 class) | 1 | `ckpt` |
| `run-mpdd.sh` | MPDD | 1 想定 | `ckpt` |
| `run-wfdd.sh` | WFDD | 1 想定 | `ckpt` |
| `run-mad-man.sh` | MAD-man (MVTec 弱欠陥版) | — | — |
| `run-mad-sys.sh` | MAD-sys (β=0.1) | 1 | **`test`**（評価のみ） |
| `run-custom.sh` | ユーザ独自 | 0 | `ckpt`、`--distribution 2`（manifold 固定） |

すべての shell スクリプト冒頭は `cd ..` してから `python main.py` を呼ぶ前提（=`shell/` から実行する）。

---

## 2. 実行に必要な条件

### 2.1 Python / OS

| 項目 | 値 / 備考 |
|---|---|
| Python | **3.9.15**（README 明記）|
| OS | 元実装は Linux 想定。本ワークスペースは **Windows 11**。`bash` での `.sh` 実行は Git Bash / WSL を要するか PowerShell で書き直しが必要 |
| GPU | **CUDA 必須**。`utils.set_torch_device` は `gpu_ids` が空なら CPU にフォールバックするが、`requirements.txt` が `cuda-python==11.8.2` / `onnxruntime-gpu==1.18.1` / `torch==2.1.2`（CUDA 11.8 ホイール想定）を pin。CPU 実行は事実上非サポート |
| GPU メモリ | A800 80GB を使用。`batch_size=8`, `imagesize=288`, `wide_resnet50_2` の組み合わせは 8〜16GB 程度で動くはず（未検証）|

### 2.2 必要ライブラリ（`requirements.txt` のスナップショット）

```
click==8.1.7
cuda-python==11.8.2
imgaug==0.4.0
matplotlib==3.8.2
numpy==1.26.3
onnx==1.16.2
onnxruntime-gpu==1.18.1
onnxsim==0.4.36
opencv-python-headless==4.10.0.84
pandas==1.5.2
openpyxl==3.0.10
pillow==10.2.0
scikit-image==0.22.0
scikit-learn==1.4.0
scipy==1.11.4
tensorboard==2.15.1
timm==0.9.12
torch==2.1.2
torchvision==0.16.2
tqdm==4.66.1
```

注意点:
- `torch==2.1.2` は `pip install torch==2.1.2` だと CPU 版になる場合がある。CUDA 11.8 ホイールを明示するには `--index-url https://download.pytorch.org/whl/cu118` を使う。
- `onnx`, `onnxruntime-gpu`, `onnxsim` は ONNX 出力ワークフローのみで使用。学習・評価には不要。
- `imgaug==0.4.0` は `numpy>=1.20` で警告/エラーになることが多い。`numpy==1.26.3` 環境で動くかは要確認。

### 2.3 必要データセット

| 用途 | データセット | 入手 | 配置の必須要件 |
|---|---|---|---|
| 補助テクスチャ（必須） | **DTD** | https://www.robots.ox.ac.uk/~vgg/data/dtd/ | `<augpath>/<category>/*.jpg` 構造 |
| 評価 | **MVTec AD** | https://www.mvtec.com/company/research/datasets/mvtec-ad/ | `<class>/{train,test,ground_truth}/...` |
| 評価 | **VisA** | https://github.com/amazon-science/spot-diff/ | 〃（前処理が必要な場合あり）|
| 評価 | **MPDD** | https://github.com/stepanje/MPDD/ | 〃 |
| 評価 | **WFDD**（自製） | Google Drive | 〃 |
| 評価 | **MAD-man / MAD-sys**（自製） | Google Drive | MVTec 互換構造 |
| `--fg 1` 利用時 | **Foreground Mask** | Google Drive | `<datapath>/fg_mask/<class>/<file>.png`（`MVTecDataset.__getitem__` 参照）|

### 2.4 学習済みモデル / Checkpoint

- **MVTec AD 用**: README から Google Drive [リンク](https://drive.google.com/drive/folders/1Hjlr-CcXwnhWfrWUCJJCooBI_pMP4N1C?usp=sharing) で `results/` フォルダごと配布。
- 配置先: `GLASS/results/`（既存の `results/` を退避してから上書き）。
- 内部構造（`glass.py` から推定）: `results/models/backbone_<i>/<dataset>_<class>/ckpt_best_<epoch>.pth`。
- バックボーンの ImageNet 事前学習重みは `torchvision`/`timm` が `pretrained=True` で初回自動ダウンロード（`~/.cache/torch/hub/checkpoints/` に保存）。

### 2.5 外部依存関係

- HTTP ダウンロード: ImageNet 事前学習重み（pytorch.org / huggingface）。プロキシ環境では失敗し得る。
- ディスク容量目安: MVTec AD ≒ 5GB、VisA ≒ 10GB、DTD ≒ 600MB、配布 `results/` ≒ 数 GB（要確認）。
- TensorBoard: `tb/` ログ書き出しに `tensorboard==2.15.1` を使用。

---

## 3. 実行手順（具体的なコマンド付き）

> 想定: Windows 11 + Git Bash（または WSL/Anaconda Prompt）。Conda が前提だが venv でも代替可能。
> 作業ディレクトリは特記なき限り `01.GLASS/GLASS/`。
> 環境変更は本フェーズでは未実施。下記は**計画**であり、まだ実行していない。

### 3.1 仮想環境の作成

```bash
# Anaconda or Miniconda を前提
conda create -n glass_env python=3.9.15 -y
conda activate glass_env
```

> 代替案: `python -m venv .venv && source .venv/Scripts/activate` (Git Bash) / `.\.venv\Scripts\Activate.ps1` (PowerShell)。

### 3.2 依存関係のインストール

CUDA 11.8 環境を前提とし、PyTorch だけ別途インデックスを指定するのが安全:

```bash
cd "01.GLASS/GLASS"

# 1) CUDA 11.8 対応の torch / torchvision を先に入れる
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118

# 2) 残りを requirements.txt から
pip install -r requirements.txt
```

> **未確認事項**: `pip install -r requirements.txt` だけで `torch==2.1.2` が CUDA 11.8 ビルドになるかは環境依存。失敗時は上記手順で切り分ける。

GPU が利用できることを最初に確認:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
```

### 3.3 データセット準備

例: MVTec AD で動作確認する最小構成。

```bash
# 任意の場所、例えば D:\datasets に配置
# D:/datasets/
#   ├── mvtec_anomaly_detection/        ← MVTec AD 解凍ルート
#   │   ├── carpet/{train,test,ground_truth}/...
#   │   ├── ...
#   │   └── fg_mask/<class>/...           ← Foreground Mask zip を解凍
#   └── dtd/images/<category>/*.jpg       ← DTD 解凍
```

ポイント:
- `fg_mask/` は MVTec AD ルート直下（`<datapath>/fg_mask/<class>/<file>.png`）に置く必要がある（`mvtec.py:187` 周辺）。
- VisA は前処理（`split_csv.csv` から `train/test` に分けるスクリプト）が公式リポジトリで必要。配布 zip 構造のままでは `MVTecDataset.get_image_data()` は読めない（**未確認事項**: 公式の前処理手順に従って整形する必要あり）。

### 3.4 Checkpoint 準備（評価のみ実行する場合）

```bash
cd "01.GLASS/GLASS"

# 既存 results を退避
[ -d results ] && mv results results.bak.$(date +%s)

# Google Drive から results.zip をダウンロード（手動 or gdown）
pip install gdown
gdown --folder "https://drive.google.com/drive/folders/1Hjlr-CcXwnhWfrWUCJJCooBI_pMP4N1C" -O results
```

> **未確認事項**: 配布 `results/` 内の正確なディレクトリ構造（`models/backbone_0/mvtec_<class>/ckpt_best_*.pth` の命名）と、再ダウンロードが許可されているライセンス。

### 3.5 最小動作確認コマンド

#### (a) Smoke test：1 クラスだけで 1 エポック相当を回す

`shell/run-mvtec.sh` を写経して `meta_epochs=1`、`limit=8`、`-d carpet` のみに絞ると 5〜10 分程度で終わる。
（**まだコードを編集しない方針なので、ここでは案として提示**）

```bash
cd "01.GLASS/GLASS"
python main.py \
    --gpu 0 --seed 0 --test ckpt \
  net \
    -b wideresnet50 -le layer2 -le layer3 \
    --pretrain_embed_dimension 1536 --target_embed_dimension 1536 \
    --patchsize 3 \
    --meta_epochs 1 --eval_epochs 1 \
    --dsc_layers 2 --dsc_hidden 1024 \
    --pre_proj 1 --mining 1 --noise 0.015 --radius 0.75 --p 0.5 \
    --step 20 --limit 8 \
  dataset \
    --distribution 0 --mean 0.5 --std 0.1 --fg 1 --rand_aug 1 \
    --batch_size 8 --resize 288 --imagesize 288 \
    -d carpet \
    mvtec D:/datasets/mvtec_anomaly_detection D:/datasets/dtd/images
```

> 期待される挙動: ログに `Dataset CARPET ... train=N test=M`、tqdm の進捗、`results/models/backbone_0/mvtec_carpet/` に `ckpt.pth`、`tb/` が生成される。
> ただし `--distribution 0` は `./datasets/excel/mvtec_distribution.xlsx` を読みにいくため、初回は **`--distribution 1`** で 1 度回して xlsx を生成するのが正攻法。

#### (b) Distribution 判定ラン（初回のみ）

```bash
cd "01.GLASS/GLASS"
python main.py --gpu 0 --seed 0 --test ckpt \
  net -b wideresnet50 -le layer2 -le layer3 \
       --pretrain_embed_dimension 1536 --target_embed_dimension 1536 \
       --meta_epochs 1 --limit 1 \
  dataset --distribution 1 --fg 1 --batch_size 8 --resize 288 --imagesize 288 \
          -d carpet mvtec D:/datasets/mvtec_anomaly_detection D:/datasets/dtd/images
```

これで `./datasets/excel/mvtec_distribution.xlsx` と `./results/judge/...` が出力される（学習はスキップされる）。

### 3.6 本実行コマンド

#### MVTec AD 全 15 クラス学習

```bash
cd "01.GLASS/GLASS/shell"
# まず datapath / augpath を編集
# nano run-mvtec.sh    （Linux/Mac/Git Bash）
# notepad run-mvtec.sh （Windows）

bash run-mvtec.sh
```

スクリプト内の編集対象:
- `datapath=/root/cqy/dataset/MVTec` → ローカルの MVTec パス
- `augpath=/root/cqy/dataset/dtd/images` → ローカルの DTD パス
- 必要に応じて `--gpu`, `--meta_epochs`, `--batch_size`

#### 配布 checkpoint で評価のみ

```bash
# results/ を配布版で置換した後
cd "01.GLASS/GLASS/shell"
# run-mvtec.sh の --test を ckpt → test に変更してから
bash run-mvtec.sh
```

### 3.7 期待される出力

| ステージ | 期待ログ / 成果物 |
|---|---|
| データセット読み込み | `INFO:__main__:Dataset CARPET             : train=245 test=117` 等 |
| 学習 | `epoch:0 loss:1.23e+00 pt:.. pf:.. rt:.. rg:.. rf:.. svd:0 sample:392 IAUC:..` の tqdm |
| ベスト更新 | `results/models/backbone_0/<dataset>_<class>/ckpt_best_<epoch>.pth` が更新（古いものは削除）|
| 評価可視化 | `results/training/<dataset>_<class>/001.png` 〜（入力・GT・ヒートマップの 3 連結）|
| 集計 | `results/results.csv`（`Row Names, image_auroc, image_ap, pixel_auroc, pixel_ap, pixel_pro, best_epoch`、最後に Mean 行）|
| TensorBoard | `tensorboard --logdir results/models/backbone_0/<class>/tb` で曲線確認 |

論文値の目安（README より）:

| ベンチ | I-AUROC | P-AUROC |
|---|---|---|
| MVTec AD | 99.9% | 99.3% |
| VisA | 98.8% | 98.8% |
| MPDD | 99.6% | 99.4% |
| WFDD | 100% | 98.9% |

---

## 4. 実行前に注意すべきリスク

### 4.1 Hard-coded パス（要修正候補）

| ファイル | 箇所 | 内容 |
|---|---|---|
| `shell/run-*.sh` | `datapath=/root/cqy/dataset/...`, `augpath=/root/cqy/dataset/dtd/images` | 全スクリプトで Linux 絶対パス。Windows 環境では必ず書き換えが必要 |
| `datasets/mvtec.py:48`, `visa.py` | `anomaly_source_path='/root/dataset/dtd/images'` の既定値 | shell 経由なら CLI で上書きされるが、Python 単独呼び出し時に注意 |
| `onnx/pth2onnx.py` | `'/root/.cache/torch/hub/checkpoints/wide_resnet50_2-95faca4d.pth'` ほか | バックボーン重みとチェックポイントの絶対パス。Windows では `~/.cache/...` ですらないため要修正 |
| `glass.py` | `'./results/judge/...'`, `'./datasets/excel/...'`, `'./results/training/...'`, `'./results/eval/...'` | CWD 依存。必ず `GLASS/` から実行する必要あり |
| `main.py:344` | `os.makedirs('./datasets/excel', exist_ok=True)` | 同上 |

### 4.2 不足しているもの

- **配布 `results/`**: README 記載の Google Drive リンクは生きているが、社内 NW プロキシで弾かれる可能性。`gdown` が失敗するなら手動ダウンロード。
- **`fg_mask/` フォルダ**: `--fg 1` の場合に必須。同じ Google Drive リンクから別 zip。
- **VisA の前処理**: `MVTecDataset` 互換のフォルダ構造に整える必要あり（spot-diff 公式の前処理スクリプトが必要）。
- **`run-mad-man.sh` / `run-mpdd.sh` / `run-wfdd.sh`** の中身は今回未確認だが、いずれも `datapath` の書き換えが必要なことは確実。

### 4.3 バージョン競合・互換性

| 項目 | 懸念 |
|---|---|
| `torch==2.1.2 + cu118` ホイール | Windows + CUDA 12.x ドライバの場合、12.1/12.4 ホイール (`cu121`) のほうが安定する可能性。CUDA Toolkit と PyTorch ホイールの対応をドライバ側 `nvidia-smi` で確認 |
| `cuda-python==11.8.2` | PyTorch とは独立。CUDA 11.8 を前提にしているため、CUDA 12.x のみ入った環境では import で失敗する可能性 |
| `onnxruntime-gpu==1.18.1` | CUDA 11.8 + cuDNN 8.x が必要。学習だけなら不要なので、トラブル時はあえて入れない選択肢あり |
| `imgaug==0.4.0` | `numpy>=1.20` で `np.bool` 等の deprecated API 警告。`numpy==1.26.3` で動くかは未確認 |
| `pandas==1.5.2` + `numpy==1.26.3` | バージョン互換は概ね OK だが、新 numpy の `np.NaN` 廃止系の挙動に注意 |
| `openpyxl==3.0.10` | xlsx 出力時に `pandas` から要求される。requirements に含まれており通常問題なし |

### 4.4 README の説明不足・落とし穴

- shell スクリプトが `cd ..` する設計が README に明記されていない。`shell/` から実行しないと `./results/...` の相対パスが破綻する。
- `--distribution` の値の意味（0〜4）と `./datasets/excel/<dataset>_distribution.xlsx` の生成タイミングは README で説明されていない。**初回は `--distribution 1` を回す必要がある**ことに気づきにくい。
- `--fg 1` 時の `fg_mask/` 配置位置（`<datapath>/fg_mask/<class>/<file>.png`）の説明が薄い。
- 配布 `results/` を上書きする前に既存 `results/` を「クリアせよ」と書かれているが、実装上は `models/` 以下が分かれているので並存可能なはず（**未確認**）。

### 4.5 Windows 固有のリスク

- `bash` で `.sh` を実行する場合、Git Bash の `python` 解決順に注意（conda の python を確実に使うために `which python` を実行前に確認）。
- パス区切り `\` と `/` の混在に注意。`MVTecDataset.__getitem__` は `image_path.split(classname)[0] + 'fg_mask/'` のように **`/` で文字列結合**しているため、Windows でも問題ないが、`os.path.split` と混在しているのでデバッグ時は要注意。
- ファイル名長（OneDrive 配下の長いパス）+ Tensorboard ログで Windows の MAX_PATH に抵触する恐れ。`results/` を C ドライブ直下に出すなどの回避策を検討。
- OneDrive のリアルタイム同期と頻繁なチェックポイント書き込みは I/O 負荷を増やす。可能であれば `results/` をローカル外（`D:\` 等）にシンボリックリンクするのが望ましい。

### 4.6 修正が必要そうな箇所（優先度順）

1. **`shell/run-*.sh` の `datapath` / `augpath`** — 必須。
2. **`onnx/pth2onnx.py` のバックボーン pth パスとチェックポイント相対パス** — ONNX 化したい場合のみ。
3. **`utils.create_storage_folder`** — `log_project` / `log_group` / `run_name` を受け取りつつ無視している。複数実行を並列に走らせると `results/` を奪い合う可能性。
4. **`datasets/excel/` の事前生成有無** — `MVTecDataset` 側で `--fg 2` 時に xlsx を read するため、`--fg 1` で運用するなら影響なし。

---

## 5. 推奨ロードマップ

1. **環境構築 (0.5 日)**: conda 環境作成 → CUDA 11.8 対応 PyTorch → `requirements.txt` → `torch.cuda.is_available()` 確認。
2. **データ配置 (0.5〜1 日)**: MVTec AD と DTD と `fg_mask/` を D ドライブ等に配置 → `shell/run-mvtec.sh` のパスを書き換え。
3. **Smoke test (1 時間)**: `--meta_epochs 1 --limit 8 -d carpet` で疎通確認。エラー切り分け。
4. **Distribution 判定 (1〜2 時間)**: `--distribution 1` で `mvtec_distribution.xlsx` を生成。
5. **本学習 (数日 / GPU 性能依存)**: `bash shell/run-mvtec.sh`。論文値に近い AUROC/AP/PRO が出ることを確認。
6. **配布 ckpt での再現 (1 日)**: 配布 `results/` を取得 → `--test test` で評価のみ → 論文値と一致するか比較。
7. **ONNX 化（オプション）**: `pth2onnx.py` のパスを修正 → `python pth2onnx.py` → `ort.py` で推論サンプル。

---

## 6. 未確認事項一覧

実行前に確定させておきたい項目:

- [ ] ローカルの `nvidia-smi` で確認できる **CUDA ドライババージョン** と、それに合致する PyTorch ホイール（`cu118` / `cu121` / `cu124`）。
- [ ] **GPU メモリ容量**（A800 80GB 前提のハイパラがそのまま動くか。動かない場合 `--batch_size` を下げる）。
- [ ] 配布 `results/` の **正確なディレクトリ構造** とライセンス表記。
- [ ] **VisA 公式の前処理手順**（`MVTecDataset` 互換に変換するスクリプト）。
- [ ] **`run-mpdd.sh` / `run-wfdd.sh` / `run-mad-man.sh`** の細部（本レポートでは未読）。
- [ ] Windows + Git Bash で `bash shell/run-mvtec.sh` の `cd ..` がワークスペース内で意図通り動くか（`shell/` の親が `GLASS/` であることは確認済み）。
- [ ] 社内ネットワークから `download.pytorch.org`、HuggingFace、Google Drive、`pypi.org` に到達できるか（プロキシ設定の要否）。
- [ ] OneDrive 同期によるロック・遅延が `results/` 書き込みに影響しないか。

---

## 付録 A. 参考: コマンド単発呼び出しの構造

`main.py` は `click.group(chain=True)` で、3 つのサブコマンドを順に実行する設計:

```
python main.py [GLOBAL_OPTS]  net [NET_OPTS]  dataset [DATASET_OPTS] -d <class> [-d <class>...] <name> <data_path> <aug_path>
```

- `GLOBAL_OPTS`: `--results_path`, `--gpu`, `--seed`, `--log_group`, `--log_project`, `--run_name`, `--test`
- `NET_OPTS`: `-b/--backbone_names`, `-le/--layers_to_extract_from`, `--pretrain_embed_dimension`, `--target_embed_dimension`, `--patchsize`, `--meta_epochs`, `--eval_epochs`, `--dsc_layers`, `--dsc_hidden`, `--dsc_margin`, `--pre_proj`, `--mining`, `--noise`, `--radius`, `--p`, `--lr`, `--svd`, `--step`, `--limit`, `--train_backbone`
- `DATASET_OPTS`: `-d/--subdatasets`, `--batch_size`, `--num_workers`, `--resize`, `--imagesize`, augmentation 群, `--distribution`, `--mean`, `--std`, `--fg`, `--rand_aug`, `--downsampling`, `--augment`
- `<name>`: `mvtec` / `visa` / `mpdd` / `wfdd` のいずれか（`main.py:169` の `_DATASETS`）
- `<data_path>`, `<aug_path>`: `click.Path(exists=True, file_okay=False)` で存在チェックあり

`--gpu` は `multiple=True` なので複数指定可能だが、`utils.set_torch_device` は `gpu_ids[0]` のみ参照する（実質マルチ GPU 学習はできない）。

## 付録 B. 参考: backbone 選択肢

`backbones.py` は `wideresnet50` 以外にも `resnet18/50/101/200`, `vgg*`, `vit_*`, `efficientnet_*`, `densenet*`, `inception_v4` など 40 種以上を文字列 `eval()` でロード可能。すべて `pretrained=True` 固定なので、初回ロード時にネットワーク必須。

論文/shell スクリプトの推奨構成は **`-b wideresnet50 -le layer2 -le layer3 --pretrain_embed_dimension 1536 --target_embed_dimension 1536`**。

---

以上が本リポジトリの実行計画です。コード本体・環境とも未変更のため、本レポート確認後に「Step 3.1〜3.5 の順で進めてよいか」を判断してから次フェーズに移ることを推奨します。

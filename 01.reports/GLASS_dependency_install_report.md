# GLASS 依存関係インストールレポート

- **作成日**: 2026-05-01
- **対象 conda 環境**: `synthetic_data_py313` (`C:\Users\seong\anaconda3\envs\synthetic_data_py313`)
- **対象リポジトリ**: `01.GLASS/GLASS/`（commit `f788d567`）
- **元の固定**: `GLASS/requirements_original.txt`（バックアップ済み・未削除）
- **更新後**: `GLASS/requirements_updated_current_env.txt`

---

## 1. 現在の環境情報

### 1.1 ベース環境

| 項目 | 値 | 元 requirements との差 |
|---|---|---|
| OS | Windows 11 Home (10.0.26200) / MINGW64 (MSYS) | — |
| シェル | bash (Git for Windows) | — |
| Python | **3.13.13** | 元: 3.9.15 → **大幅に新しい** |
| pip | 26.0.1 | — |
| 仮想環境 | conda env `synthetic_data_py313` | アクティブ確認済み |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU (6 GB) | A800 80GB 想定より小容量 |
| GPU ドライバ | 595.97 | — |
| CUDA (PyTorch) | **13.0** | 元: 11.8 → 大幅に新しい |
| cuDNN | 91900 (`9.19.x`) | — |

### 1.2 既にインストール済みの GLASS 関連ライブラリ（調査時点）

| ライブラリ | 既存バージョン | 元 requirements 固定 | 判定 |
|---|---|---|---|
| `torch` | **2.11.0+cu130** | `==2.1.2` | 上書き禁止（指示） |
| `torchvision` | 0.26.0+cu130 | `==0.16.2` | 上書き禁止 |
| `numpy` | 2.4.3 | `==1.26.3` | numpy 2.x 系。imgaug と非互換 |
| `scipy` | 1.17.1 | `==1.11.4` | 既存維持 |
| `scikit-learn` | 1.8.0 | `==1.4.0` | 既存維持 |
| `scikit-image` | 0.26.0 | `==0.22.0` | 既存維持 |
| `Pillow` (PIL) | 12.1.1 | `==10.2.0` | 既存維持 |
| `opencv-python-headless` (cv2) | 4.13.0 | `==4.10.0.84` | 既存維持 |

### 1.3 インストール前に欠落していたライブラリ

`timm`, `pandas`, `click`, `tqdm`, `tensorboard`, `matplotlib`, `imgaug`, `openpyxl`, `onnx`, `onnxruntime`, `onnxsim`, `cuda-python` が未インストールだった。

---

## 2. 元 `requirements.txt` の問題点

### 2.1 Python 3.13 でビルド不可・ホイール不在のもの

`pip install` で失敗または旧ホイールが選ばれない:

- `pandas==1.5.2` — Python 3.13 対応は 2.2.3 以降。
- `tensorboard==2.15.1` — Python 3.13 対応は 2.18 以降。
- `matplotlib==3.8.2` — Python 3.13 対応は 3.9 以降。
- `numpy==1.26.3` — そのものは 3.13 でビルド可能だが既に 2.4.3 が入っており、ダウングレードすると ABI 不整合のリスク（後述）。

### 2.2 既に新しいバージョンが入っており触らない方が安全なもの

`torch`, `torchvision`, `numpy`, `scipy`, `scikit-learn`, `scikit-image`, `Pillow`, `opencv-python-headless`。
特に `torch / torchvision` はユーザ指示で **絶対にダウングレードしない**。

### 2.3 CUDA 11.8 前提で固定されていて CUDA 13 環境では妥当でないもの

- `cuda-python==11.8.2` — CUDA 11.8 系の Python バインディング。GLASS の Python ソースから `cuda` のような直接 import は確認できず、未使用と判断。
- `onnxruntime-gpu==1.18.1` — CUDA 11.8 ホイール前提。CUDA 13.0 用の公式 GPU ホイールは 2026-05 時点で確認できなかった。
- `onnx==1.16.2` / `onnxsim==0.4.36` — Python 3.13 では新しいバージョンが必要。

ただし `onnx*` および `cuda-python` は `pth2onnx.py` / `ort.py`（ONNX 書き出し・ONNX Runtime 推論サンプル）でのみ参照される。GLASS の **学習・評価本流（`main.py`）には不要**。今回は導入を見送り、必要時にコメントアウトを外す方針とした。

### 2.4 `imgaug==0.4.0` — 最大の互換性リスク

`imgaug` 0.4.0 (2020 年リリース) は内部で `np.sctypes`, `np.bool` 等の deprecated API を使用。NumPy 2.0 で `np.sctypes` は **完全に削除**された。新しいリリースは PyPI 上に存在せず、numpy 2.x 環境では即 import エラーとなる。
GLASS では `perlin.py` の以下 1 行でのみ使用:

```python
perlin_noise_np = iaa.Sequential([iaa.Affine(rotate=(-90, 90))])(image=perlin_noise_np)
```

`perlin.py` は `datasets/mvtec.py`, `datasets/visa.py` から import されるため、imgaug が import できないとデータセット側もロード不能になる（=学習・評価ともに着手不可）。詳細は §7。

---

## 3. 依存関係の互換性方針

| 区分 | 対象 | 対応 |
|---|---|---|
| そのまま入れる（最新 / 上限なし） | `click`, `tqdm`, `openpyxl`, `timm` | 最新版を許容 |
| 下限を引き上げる | `pandas>=2.2.3`, `tensorboard>=2.18`, `matplotlib>=3.9` | Python 3.13 ホイールが存在する版以降 |
| 既存維持（再インストール不要） | `numpy`, `scipy`, `scikit-learn`, `scikit-image`, `Pillow`, `opencv-python-headless` | requirements に書かない |
| 既存維持（特に保護） | `torch`, `torchvision` | requirements に書かない・pip からも触らせない |
| 元固定のまま入れる | `imgaug==0.4.0` | 唯一の利用可能版。numpy 2.x で import 失敗を承知の上 |
| 任意（コメントアウト） | `onnx`, `onnxruntime`, `onnxsim` | ONNX 書き出し用。学習・評価には不要 |
| 完全に除外 | `cuda-python` | GLASS 本体は未使用。CUDA 13 と無関係 |

`pip install` 実行時は `--upgrade-strategy only-if-needed` を指定し、既存パッケージを不必要に更新しない。

---

## 4. 作成した requirements ファイル

### 4.1 バックアップ（元のまま）

- パス: `GLASS/requirements_original.txt`
- 内容: 元 `requirements.txt` と完全一致（バイト同一）。

### 4.2 現在環境向け

- パス: `GLASS/requirements_updated_current_env.txt`
- 主要部分:

```text
click>=8.1
imgaug==0.4.0          # 唯一の利用可能版。numpy 2.x で import 失敗（後述）
matplotlib>=3.9
openpyxl>=3.1
pandas>=2.2.3
tensorboard>=2.18
timm>=1.0.11
tqdm>=4.66

# --- ONNX export workflow (uncomment only when needed) ---
# onnx>=1.17
# onnxsim>=0.4.36
# onnxruntime
```

`torch`, `torchvision`, `numpy`, `scipy`, `scikit-learn`, `scikit-image`, `Pillow`, `opencv-python-headless`, `cuda-python` は **意図的に省略**（コメントで明記）。

---

## 5. 実行したインストールコマンド

作業ディレクトリ: `01.GLASS/GLASS/`

```bash
# 1) バックアップ（破壊的書き込みなし）
cp requirements.txt requirements_original.txt

# 2) 新 requirements を編集（本ファイルとして作成済み）
#    requirements_updated_current_env.txt

# 3) ドライラン（torch / numpy が触られないことを事前確認）
python -m pip install -r requirements_updated_current_env.txt \
    --upgrade-strategy only-if-needed --dry-run

# 4) 本インストール
python -m pip install -r requirements_updated_current_env.txt \
    --upgrade-strategy only-if-needed
```

dry-run の結果、`Would install ...` リストに `torch` / `torchvision` / `numpy` / `scipy` / `scikit-learn` / `scikit-image` / `Pillow` / `opencv` のいずれも含まれず、PyTorch 環境を温存できることを実行前に確認した。

---

## 6. インストール結果

### 6.1 新規追加されたパッケージ（pip 実行ログ末尾の "Successfully installed" より）

```
Shapely-2.1.2          absl-py-2.4.0          annotated-doc-0.0.4    anyio-4.13.0
certifi-2026.4.22      click-8.3.3            colorama-0.4.6         contourpy-1.3.3
cycler-0.12.1          et-xmlfile-2.0.0       fonttools-4.62.1       grpcio-1.80.0
h11-0.16.0             hf-xet-1.4.3           httpcore-1.0.9         httpx-0.28.1
huggingface_hub-1.13.0 idna-3.13              imgaug-0.4.0           kiwisolver-1.5.0
markdown-3.10.2        markdown-it-py-4.0.0   matplotlib-3.10.9      mdurl-0.1.2
openpyxl-3.1.5         pandas-3.0.2           protobuf-7.34.1        pygments-2.20.0
pyparsing-3.3.2        python-dateutil-2.9.0.post0   pyyaml-6.0.3
rich-15.0.0            safetensors-0.7.0      shellingham-1.5.4      six-1.17.0
tensorboard-2.20.0     tensorboard-data-server-0.7.2   timm-1.0.26
tqdm-4.67.3            typer-0.25.1           tzdata-2026.2          werkzeug-3.1.8
```

### 6.2 GLASS が直接利用するライブラリのインストール後バージョン

| ライブラリ | バージョン | 元固定 | 状態 |
|---|---|---|---|
| `torch` | 2.11.0+cu130 | 2.1.2 | 維持（ダウングレードなし） |
| `torchvision` | 0.26.0+cu130 | 0.16.2 | 維持 |
| `numpy` | 2.4.3 | 1.26.3 | 維持（numpy 2.x 系） |
| `scipy` | 1.17.1 | 1.11.4 | 維持 |
| `scikit-learn` | 1.8.0 | 1.4.0 | 維持 |
| `scikit-image` | 0.26.0 | 0.22.0 | 維持 |
| `Pillow` | 12.1.1 | 10.2.0 | 維持 |
| `opencv-python-headless` (cv2) | 4.13.0 | 4.10.0.84 | 維持 |
| `pandas` | 3.0.2 | 1.5.2 | 新規 |
| `matplotlib` | 3.10.9 | 3.8.2 | 新規 |
| `tensorboard` | 2.20.0 | 2.15.1 | 新規 |
| `timm` | 1.0.26 | 0.9.12 | 新規 |
| `click` | 8.3.3 | 8.1.7 | 新規 |
| `tqdm` | 4.67.3 | 4.66.1 | 新規 |
| `openpyxl` | 3.1.5 | 3.0.10 | 新規 |
| `imgaug` | 0.4.0 | 0.4.0 | 新規（ただし import 不可） |
| `onnx` / `onnxruntime` / `onnxsim` / `cuda-python` | — | 各種 | 未導入（意図的） |

### 6.3 PyTorch / CUDA 動作確認

```text
torch         2.11.0+cu130
cuda?         True
cuda_v        13.0
torchvision   0.26.0+cu130
cuda tensor   cuda:0  torch.Size([2, 3])
```

`torch.randn(2, 3, device='cuda')` が成功し、CUDA テンソル割り当ては問題なし。**PyTorch 環境は今回の作業で一切変更されていない**。

---

## 7. import 確認結果

### 7.1 主要ライブラリ単体 import

| モジュール | 結果 | バージョン |
|---|---|---|
| `torch` | OK | 2.11.0+cu130 |
| `torchvision` | OK | 0.26.0+cu130 |
| `click` | OK | 8.3.3 |
| `tqdm` | OK | 4.67.3 |
| `pandas` | OK | 3.0.2 |
| `matplotlib` | OK | 3.10.9 |
| `tensorboard` | OK | 2.20.0 |
| `timm` | OK | 1.0.26 |
| `openpyxl` | OK | 3.1.5 |
| `PIL` | OK | 12.1.1 |
| `cv2` | OK | 4.13.0 |
| `numpy` | OK | 2.4.3 |
| `scipy` | OK | 1.17.1 |
| `sklearn` | OK | 1.8.0 |
| `skimage` | OK | 0.26.0 |
| **`imgaug`** | **NG** | 0.4.0（インストール済みだが import 不可） |

`imgaug` のエラー（抜粋）:

```
File ".../imgaug/imgaug.py", line 45, in <module>
    NP_FLOAT_TYPES = set(np.sctypes["float"])
AttributeError: `np.sctypes` was removed in the NumPy 2.0 release.
```

### 7.2 GLASS ソース直下の各モジュールの import

| モジュール | 結果 |
|---|---|
| `backbones` | OK |
| `model` | OK |
| `common` | OK |
| `loss` | OK |
| `metrics` | OK |
| `utils` | OK |
| `glass` | OK |
| `perlin` | **NG**（imgaug 経由で `np.sctypes` エラー） |
| `datasets.mvtec` | **NG**（同上、`from perlin import perlin_mask`） |
| `datasets.visa` | **NG**（同上） |

→ **学習・評価のいずれを起動しても、データセット読み込み時に必ず失敗する状態**。本格実行は本問題の解決後に行う必要がある。

---

## 8. 残っているリスク・未解決事項

### 8.1 BLOCKER: `imgaug` × NumPy 2.x

**事実**:
- `imgaug` は 2020-02 の 0.4.0 が最新。PyPI に新版なし。
- 内部で `np.sctypes`, `np.bool` 等の deprecated API を使用。
- NumPy 2.0 でこれらは削除されたため、現環境では import 不可。
- GLASS は `perlin.py` の 1 行でのみ `imgaug.augmenters.iaa.Affine` を使用。`MVTecDataset` / `VisADataset` 経由で全学習パスに乗る。

**選択肢（互いに排他）**:

| 案 | 内容 | コスト | リスク |
|---|---|---|---|
| **A. NumPy をダウングレード** | `pip install "numpy<2"`（実態 1.26.4） | 低 | scipy 1.17 / pandas 3.0 / scikit-image 0.26 は **numpy 2.x の C-ABI でビルドされている可能性**。pip メタデータ上は `numpy>=1.24` 等で許容されているが、実行時に `_ARRAY_API not found` 系の警告/エラーが発生する場合あり。発生時はそれら 3 つの再ビルド（`--force-reinstall --no-binary`）が必要 |
| **B. インストール済み `imgaug/imgaug.py` を patch** | `np.sctypes["float"]` → `[np.float16, np.float32, np.float64]` 等の明示列挙に書き換え（同様に `np.sctypes["int"]`, `np.sctypes["uint"]`） | 極小 | GLASS リポジトリは無修正。pip 再インストール時に再 patch が必要 |
| **C. 別 conda env を構築** | 例: `conda create -n glass_legacy python=3.9.15` で上流 README どおりに揃える | 中 | 学習用ストレージが二重化。CUDA 13.0 ドライバで CUDA 11.8 用 PyTorch ホイールは動作する（後方互換）が要動作確認 |
| **D. `perlin.py` を改修** | `imgaug.Affine` を `torchvision.transforms.functional.rotate` 等に置換 | 中 | **GLASS 本体修正にあたるため、今回の作業範囲外（ユーザ指示で禁止）** |

各パッケージの宣言上の numpy 制約は `pip install "numpy<2" --dry-run` で確認済み:
- `scipy 1.17.1`: `numpy<2.7,>=1.26.4` — 1.26.4 で OK
- `pandas 3.0.2`: `numpy>=1.26.0; python_version < "3.14"` — OK
- `scikit-image 0.26`: `numpy>=1.24` — OK
- `scikit-learn 1.8`: `numpy>=1.24.1` — OK
- `matplotlib 3.10`: `numpy>=1.23` — OK

メタデータ上は破綻しないが、**コンパイル済みバイナリ間の ABI 互換は別問題**である点に注意。

**推奨**: まず案 B（installed imgaug patch）で疎通確認し、安定運用が必要になった段階で案 C（別 env）への移行を検討。**いずれを選ぶかはユーザ判断とし、本作業では未着手**。

### 8.2 副次的リスク

- **GPU メモリ 6 GB**: 元論文は A800 80GB を前提。`shell/run-mvtec.sh` の `--batch_size 8` + `wide_resnet50_2` + `imagesize 288` は 6GB だと OOM の可能性が高い。`--batch_size 2〜4` への調整が必要かもしれない（GLASS_execution_plan.md §4.1 のリスクと符合）。
- **ONNX 書き出しは未準備**: `pth2onnx.py`, `ort.py` を試す段階で `onnx`, `onnxsim`, ONNX Runtime のインストールが追加で必要。CUDA 13 対応の `onnxruntime-gpu` ホイールは現時点で公式提供なし。CPU 版 `onnxruntime` を使う方針となる。
- **OneDrive 同期下のチェックポイント I/O**: `GLASS/results/` への頻繁な `ckpt.pth` 上書きが OneDrive と競合する可能性。学習開始前に `results/` を OneDrive 配下から逃がす（ジャンクション等）対応が望ましい。
- **`pandas 3.0.2` への大きなジャンプ**: GLASS は `pd.DataFrame`, `pd.read_excel`, `pd.concat` のみ使用しており API 互換問題は小さいと予想されるが、`distribution_judge` で xlsx を扱うため初回起動時に動作確認が必要。
- **`click 8.3.3` の Deprecation**: `click.__version__` 直接参照が将来削除予定（9.1）。GLASS のコード自体は影響なし。
- **`numpy 2.x` 全般**: `loss.py` などが `np.bool`, `np.int` 等を使っていないか念のため要確認（grep 上は未検出）。

### 8.3 未確認事項

- ローカルにインストール済みの **CUDA Toolkit / cuDNN のバージョン**（PyTorch は cu130 ホイールを内蔵しているため Toolkit は不要だが、ONNX Runtime を入れる場合に影響する）。
- 案 C を採用する場合の **CUDA 11.8 ホイールの PyTorch 2.1.2 が現ドライバ 595.97 で動くか**（後方互換的には動く想定だが未検証）。
- 上流の `imgaug` が抱える `np.bool` 系の他の deprecated API も同時に踏むか（`np.sctypes` 以外にも複数箇所ある可能性）。

---

## 9. 結論

- 元 `requirements.txt` は `requirements_original.txt` として保存。
- 現環境向け要件を `requirements_updated_current_env.txt` として作成し、`pip install -r ... --upgrade-strategy only-if-needed` でインストール完了。
- **PyTorch 2.11.0+cu130 / CUDA 13.0 / Python 3.13.13 環境は一切変更されていない**ことを確認済み。
- `imgaug` の NumPy 2.x 互換性問題により、`perlin.py` 経由で `datasets.{mvtec,visa}` がロード不能。**この 1 点が GLASS 起動の唯一のブロッカー**。
- 解決策は §8.1 の A〜D のいずれかをユーザが選択する必要があり、本作業では実施していない（GLASS 本体・PyTorch・Python のいずれにも触れない方針のため）。

次のアクション候補:
1. `imgaug` 対応方針の合意（推奨: 案 B）。
2. 合意後、case B なら installed `imgaug/imgaug.py` の最小パッチ（GLASS 本体無修正）。
3. パッチ後、計画書 §3.5(b) の `--distribution 1` Smoke test を 1 クラスで実行し、データ読み込み・FFT 判定の疎通を確認。

---

## 10. フォローアップ: `glass_env` への切り替え（2026-05-01 後続作業）

ユーザ判断により案 A をベースに、案 C（別 conda env）として上流 `requirements.txt` をそのまま再現する方針に転換した。numpy 1.26.x が Python 3.13 用 wheel を持たず、ソースビルドのリスクが高かったためである。

### 10.1 採用した方針

- **新規 conda env**: `glass_env`（上流 README 命名に準拠）
- **Python**: 3.9.15（上流指定どおり）
- **依存**: `requirements_original.txt` 完全準拠
- **PyTorch**: GPU 版を明示的に取得するため、専用インデックスから `torch==2.1.2+cu118` / `torchvision==0.16.2+cu118` を先行インストール
- **既存 env (`synthetic_data_py313`)**: 完全に温存。GLASS 用途には今後使わない

### 10.2 実行コマンド

```bash
# 1) 環境作成
"C:/Users/seong/anaconda3/Scripts/conda.exe" create -n glass_env python=3.9.15 -y

# 2) GPU 版 PyTorch を専用インデックスから先に入れる
GLASS_PY="C:/Users/seong/anaconda3/envs/glass_env/python.exe"
"$GLASS_PY" -m pip install torch==2.1.2 torchvision==0.16.2 \
    --index-url https://download.pytorch.org/whl/cu118

# 3) 残りの依存を元 requirements から
cd "01.GLASS/GLASS"
"$GLASS_PY" -m pip install -r requirements_original.txt
```

> Step 2 で transitive dep として numpy 2.0.2 が一旦入るが、Step 3 で `numpy==1.26.3` に正しくダウングレードされることを確認済み。

### 10.3 インストール結果（`glass_env`）

`requirements_original.txt` の全 20 パッケージが pin どおりに入った:

| パッケージ | 版 | パッケージ | 版 |
|---|---|---|---|
| torch | 2.1.2+cu118 | onnx | 1.16.2 |
| torchvision | 0.16.2+cu118 | onnxruntime-gpu | 1.18.1 |
| numpy | 1.26.3 | onnxsim | 0.4.36 |
| scipy | 1.11.4 | cuda-python | 11.8.2 |
| scikit-learn | 1.4.0 | timm | 0.9.12 |
| scikit-image | 0.22.0 | matplotlib | 3.8.2 |
| Pillow | 10.2.0 | tensorboard | 2.15.1 |
| opencv-python-headless | 4.10.0.84 | pandas | 1.5.2 |
| imgaug | 0.4.0 | openpyxl | 3.0.10 |
| click | 8.1.7 | tqdm | 4.66.1 |

### 10.4 動作確認結果（`glass_env`）

```text
python                 3.9.15
torch                  2.1.2+cu118  cuda? True  cuda_v 11.8
torchvision            0.16.2+cu118
device                 NVIDIA GeForce RTX 3060 Laptop GPU
cuda tensor            cuda:0  torch.Size([2, 3])

  OK numpy 1.26.3        OK scipy 1.11.4         OK sklearn 1.4.0
  OK skimage 0.22.0      OK PIL 10.2.0           OK cv2 4.11.0
  OK pandas 1.5.2        OK matplotlib 3.8.2     OK tensorboard 2.15.1
  OK timm 0.9.12         OK openpyxl 3.0.10      OK imgaug 0.4.0       ←　復活
  OK click 8.1.7         OK tqdm 4.66.1          OK onnx 1.16.2
  OK onnxruntime 1.18.1  OK onnxsim 0.4.36

--- GLASS modules ---
  OK backbones    OK model     OK common      OK loss        OK metrics
  OK utils        OK perlin    OK glass       OK datasets.mvtec   OK datasets.visa
```

- `imgaug` の `np.sctypes` エラーは消滅（numpy 1.26.3 環境では `np.sctypes` がまだ存在）。
- 旧環境で import 不可だった `perlin` / `datasets.mvtec` / `datasets.visa` がすべて成功。
- **PyTorch cu118 wheel が CUDA 13.0 ドライバ (595.97) 上で正常動作**することを確認（CUDA の forward driver compatibility による。§8.3 の未確認事項が解消）。

### 10.5 旧 env (`synthetic_data_py313`) と新 env (`glass_env`) の使い分け

| 項目 | `synthetic_data_py313` | `glass_env` |
|---|---|---|
| 用途 | GLASS 以外の既存作業を継続 | **GLASS の学習・評価専用** |
| Python | 3.13.13 | 3.9.15 |
| PyTorch | 2.11.0+cu130 | 2.1.2+cu118 |
| numpy | 2.4.3 | 1.26.3 |
| imgaug 動作 | NG | OK |
| GLASS 起動可否 | 不可 | 可（依存解決済み） |

GLASS を動かすコマンドは **必ず `glass_env` の Python から呼ぶ**こと:

```bash
# bash で直接呼ぶ場合
GLASS_PY="C:/Users/seong/anaconda3/envs/glass_env/python.exe"
cd "01.GLASS/GLASS"
"$GLASS_PY" main.py [GLOBAL_OPTS] net [...] dataset [...]

# あるいは conda activate で
conda activate glass_env
cd 01.GLASS/GLASS
python main.py ...
```

### 10.6 残存リスクの再整理（`glass_env` ベース）

§8.1 の `imgaug` 互換問題は **解消**。残るリスクは以下:

- **GPU メモリ 6 GB**: 変わらず。`shell/run-mvtec.sh` の `--batch_size 8` は OOM リスクあり。Smoke test 時に `--batch_size 2` 程度から試すことを推奨。
- **OneDrive 同期**: 変わらず。`results/` を OneDrive 配下から退避する設定が望ましい。
- **`requirements_updated_current_env.txt` は `synthetic_data_py313` 用の遺産**: GLASS 運用は `glass_env` + `requirements_original.txt` で行うため、本ファイルは現時点で実用的役割なし。削除はせず将来の Python 3.13 移行時の参考として残置。
- **未確認**: `MAD-man` / `MPDD` / `WFDD` 用 shell スクリプトの動作、配布 `results/` zip のディレクトリ構造（GLASS_execution_plan.md §6 の未確認事項は引き続き有効）。

### 10.7 結論

- GLASS の依存関係問題は **完全に解決**。
- 次の合理的なステップは GLASS_execution_plan.md §3.3〜3.5 の **データセット配置 → smoke test**。コードの修正・本格学習は依然として未着手。

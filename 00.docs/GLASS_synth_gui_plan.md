# GLASS 合成 NG データ生成 GUI アプリ ─ 実装プラン

作成日: 2026-05-02
対象環境: `glass_env` (Python 3.9.15 + cu118)、Windows 11、RTX 3060 Laptop 6 GB
作者: Claude Code (Opus 4.7)

---

## 0. ゴール

ユーザが手元に持っている **OK 画像 (正常品)** と **DTD のような外部テクスチャ集合** を入力に、
GLASS の **LAS (Local Anomaly Synthesis)** ロジックを使って **NG 画像 + 対応マスク** を量産する
**Tkinter ベースのデスクトップアプリ** を作る。出力は下流の AI 異常検知モデル (PatchCore / EfficientAD / 自社モデル等) の **学習データ** として直接使える形にする。

> 本プロジェクトのポイントは「**合成データがどれほど現実的に再現できるか**」をユーザが GUI で
> 即座に確認・調整できることであり、AUROC を競うことではない (memory: project_goal)。

---

## 1. スコープ

### in-scope
- LAS (画像空間合成: Perlin マスク × DTD ブレンド) を **学習なし** で実行
- OK 画像 1 枚から N 枚の NG 画像を生成し、画素単位の二値マスクを同時に出力
- 主要パラメータ (Perlin スケール、β 分布、回数、シード、リサイズ) を GUI で調整
- 1 サンプル即時プレビュー (左 Canvas に Original / Synthetic / Mask の 3 連)
- バッチ生成 (1 ボタンで `N × OK枚数` 出力 + ラベル CSV)

### out-of-scope (今回作らない)
- GAS (Global Anomaly Synthesis、特徴空間勾配上昇) ─ 画像書き出しに無関係
- Discriminator / 学習ループ ─ 合成のみ
- ONNX 出力、推論サービス化
- マルチ GPU、分散
- 自動ハイパラ探索

### 中期的に作る可能性 (今回は枠だけ用意)
- Foreground マスク自動推定 (現状 `--fg 0` 固定 → SAM2 / U^2-Net 等で OK 画像から fg を抽出)
- 合成画像の品質スコアリング (LPIPS / FID で「らしさ」を数値化)

---

## 2. 設計の前提 ─ 既存コードの再利用方針

| 既存資産 | 流用方法 |
|---|---|
| `GLASS/datasets/mvtec.py:172-212` (`__getitem__` の LAS 部分) | **コア関数として抽出** (`synthesizer_app/core/synthesis.py`) |
| `GLASS/perlin.py` (`perlin_mask`, `rand_perlin_2d_np`) | そのまま import |
| `GLASS/utils.py:torch_format_2_numpy_img` | そのまま import (denorm 用) |
| `GLASS/dump_synthetic.py` | 廃止せず、CLI バッチ用途として残し、内部で `core.synthesis` を呼ぶ形にリファクタ |
| `skills/tomomi-gui-style/templates/custom_styles_jp.py` | プロジェクトの `ui/` にコピー |

**重要な切り出し方針:** `MVTecDataset` は MVTec の `train/test` ディレクトリ構造を前提としているので
そのまま GUI からは使わない。LAS の純粋関数だけを抜き出して、入力 = 「画像 PIL.Image + テクスチャ PIL.Image + パラメータ」、
出力 = 「NG 画像 numpy + mask 画像 numpy」 の I/F に落とす。

---

## 3. アーキテクチャ

### 3.1 全体ディレクトリ構成 (新規)

```
GLASS/synthesizer_app/                   ← GLASS 配下に新規追加
├── gui_main.py                          ← ロジック層 (TR 規約: GuiXxx)
├── ui/
│   ├── __init__.py
│   ├── gui_main_ui.py                   ← UI 層 (TR 規約: GuiXxxUI)
│   ├── custom_styles_jp.py              ← skill から複製
│   └── TR_inc_logo.png                  ← skill assets から複製
├── core/
│   ├── __init__.py
│   ├── synthesis.py                     ← LAS 純関数 (MVTecDataset から抽出)
│   ├── exporter.py                      ← PNG + ラベル CSV 書き出し
│   └── io_utils.py                      ← OK 画像/テクスチャ列挙、検証
├── tests/
│   ├── test_synthesis.py                ← 同じ seed なら再現することの確認
│   └── test_exporter.py
├── README.md
└── run.bat                              ← `glass_env` の python.exe で起動するラッパ
```

`GLASS/dump_synthetic.py` は **GLASS 直下に残す** (既存ユーザを破壊しない)。
内部実装だけ `synthesizer_app.core.synthesis` を呼ぶ薄いラッパに置き換える。

### 3.2 レイヤ分離 (TOMOMI GUI 規約)

```
┌─────────────────────────────────────────┐
│ gui_main.py            GuiSynthApp      │  ロジック層
│   - イベントハンドラ                      │
│   - threading でバッチ実行                │
│   - core.synthesis / core.exporter 呼出   │
└──────────────┬──────────────────────────┘
               │ 継承
┌──────────────┴──────────────────────────┐
│ ui/gui_main_ui.py      GuiSynthAppUI    │  UI 層
│   - ウィジェット定義のみ                   │
│   - Tk 変数 _var_ui                       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ core/synthesis.py                       │  GUI 非依存の純関数
│   def synthesize(image, texture, params)│
│       -> (ng_image, mask)               │
└─────────────────────────────────────────┘
```

### 3.3 ウィンドウレイアウト

```
┌────────────────────────────────────────────────────────────────────┐
│ GLASS Synthesizer by TOMOMI RESEARCH, INC.            [_][□][×]   │
├────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────┬─────────────────────────┐  │
│ │ メインプレビュー (3 連 Canvas)      │ Notebook                │  │
│ │  ┌────────┬────────┬────────┐     │ ┌─ Control ───────────┐ │  │
│ │  │Original│Synth-  │Mask    │     │ │ [Logo]              │ │  │
│ │  │        │etic    │overlay │     │ │ Inputs              │ │  │
│ │  │        │        │        │     │ │  OK images: [...]   │ │  │
│ │  └────────┴────────┴────────┘     │ │  DTD path:  [...]   │ │  │
│ │                                    │ │  Output:    [...]   │ │  │
│ │ サムネイルストリップ (横スクロール)  │ │  N per OK:  [10]    │ │  │
│ │  [00][01][02][03]...[NN]           │ │ Run                  │ │  │
│ │                                    │ │  [Preview 1] (primary)│ │  │
│ │                                    │ │  [Generate batch] (primary)│ │
│ │                                    │ │  [Open output] (secondary)│ │
│ │                                    │ │  [Quit]              │ │  │
│ │                                    │ │ (C) 2026 TOMOMI...  │ │  │
│ │                                    │ ├─ Configure ─────────┤ │  │
│ │                                    │ │ Perlin min scale [0─4]│ │  │
│ │                                    │ │ Perlin max scale [0─6]│ │  │
│ │                                    │ │ β mean      [0.2─0.8]│ │  │
│ │                                    │ │ β std       [0.0─0.3]│ │  │
│ │                                    │ │ Image size  [256/288/512]│ │
│ │                                    │ │ Random aug  [☑]      │ │  │
│ │                                    │ │ Foreground  [None / Folder]│
│ │                                    │ │ Seed        [0]      │ │  │
│ │                                    │ └─────────────────────┘ │  │
│ └────────────────────────────────────┴─────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

すべて `custom.TLabelframe` / `primary.TButton` / `secondary.TButton` / `custom.TLabel` 等の TR 統一スタイルを使う (skill: tomomi-gui-style)。

---

## 4. コア合成 API 設計

### 4.1 関数シグネチャ (`core/synthesis.py`)

```python
@dataclass
class SynthParams:
    image_size: int = 288
    perlin_scale_min: int = 0     # 2**min が最小スケール
    perlin_scale_max: int = 6     # 2**max が最大スケール
    beta_mean: float = 0.5
    beta_std: float = 0.1
    rand_aug: bool = True
    seed: Optional[int] = None
    downsampling: int = 8         # 学習側に合わせると 8 (mask_s 用)
    use_foreground: bool = False  # True なら fg_mask を必ず適用

def synthesize_one(
    image: PIL.Image.Image,        # OK 画像 (RGB)
    texture: PIL.Image.Image,      # DTD 等の外部テクスチャ (RGB)
    params: SynthParams,
    fg_mask: Optional[PIL.Image.Image] = None,  # use_foreground=True のとき必須
) -> SynthResult:
    """
    Returns:
        SynthResult(
            ng_image_uint8: np.ndarray,   # H×W×3, 0-255 BGR (cv2 互換)
            mask_uint8: np.ndarray,       # H×W,   0/255 二値マスク
            mask_l_float: np.ndarray,     # H×W,   0-1 float (内部用、GUI overlay 用)
            beta_used: float,
            perlin_scale_used: tuple[int, int],
        )
    """
```

### 4.2 既存ロジックとの対応

| `MVTecDataset.__getitem__` (mvtec.py:172-212) | `synthesize_one` | 備考 |
|---|---|---|
| `transform_img(image)` | params で `image_size` だけ受けて Resize+CenterCrop+ToTensor+Normalize | Normalize は計算用、出力時に denorm |
| `transform_aug(aug)` | `rand_aug` フラグで分岐 | imgaug 経由は Perlin だけに残す |
| `perlin_mask(...)` | そのまま import | NumPy 1.26.x 必須 (CLAUDE.md) |
| `aug_image = image*(1-mask_l) + (1-β)*aug*mask_l + β*image*mask_l` | 同じ式 | β は `np.random.normal(beta_mean, beta_std)`、`[0.2, 0.8]` クリップ |
| `mask_s` (downsampling 後) | 内部用、GUI overlay にのみ使う | エクスポートは `mask_l` を二値化したものを優先 |

### 4.3 シード制御 (再現性)

`params.seed` が指定されたら **その時点でグローバル `np.random` / `torch` シードを固定**。
バッチ実行時は `seed_per_sample = seed_base + sample_idx` で per-sample シード。
`SynthResult.beta_used` / `perlin_scale_used` をログに残し、後で個別再現できるようにする。

---

## 5. 出力フォーマット

```
<output_dir>/
├── images/
│   ├── 0000_src000.png    ← NG 画像 (PNG, RGB, 8bit)
│   ├── 0001_src000.png
│   └── ...
├── masks/
│   ├── 0000_src000.png    ← 二値マスク (PNG, グレースケール 8bit, 0/255)
│   ├── 0001_src000.png
│   └── ...
├── originals/
│   └── src000.png         ← 元 OK 画像のスナップショット (リサイズ後)
├── panels/                 ← debug/QA 用 3 連結
│   ├── 0000_src000.png
│   └── ...
├── labels.csv             ← 1 行 = 1 NG サンプル
└── run.json               ← 全パラメータ + glass_env のバージョン情報
```

`labels.csv` 列:
```
sample_id, ng_image, mask, source_image, beta, perlin_scale_x, perlin_scale_y, seed, texture_path
```

下流の AI 異常検知側はこの CSV と `images/` `masks/` だけを読めば学習可能。
**MVTec ライクなディレクトリ構造** (`<class>/test/<defect_type>/*.png`, `<class>/ground_truth/<defect_type>/*.png`) で出すオプションも Configure に持たせる (PatchCore 等が直接食えるように)。

---

## 6. 実装フェーズ (incremental)

### Phase 0 ─ 準備 (1 セッション)
- [ ] `synthesizer_app/` 雛形作成、`custom_styles_jp.py` を skill から複製
- [ ] 空の `gui_main.py` / `gui_main_ui.py` で「タイトルバーが表示されるだけのアプリ」起動確認
- [ ] `run.bat` で `glass_env` の python から起動できることを確認

### Phase 1 ─ コア合成関数 (1 セッション、最重要)
- [ ] `core/synthesis.py` に `synthesize_one` 実装
- [ ] `dump_synthetic.py` を `core/synthesis` 経由に書き換え、carpet/leather/bottle で **以前と同じ panel が出ることを確認** (リグレッション防止)
- [ ] `tests/test_synthesis.py` で同一 seed → 同一出力の確認
- [ ] **GPU 不要**であることを実機で確認 (CPU-only で動く)

### Phase 2 ─ 最小 GUI (1 セッション)
- [ ] OK 画像フォルダ / DTD フォルダ / 出力フォルダの 3 つを `filedialog.askdirectory` で選ぶだけ
- [ ] [Preview 1] ボタンで 1 サンプル合成して左 Canvas に 3 連表示
- [ ] [Generate batch] ボタンで指定枚数を出力 (この時点ではブロッキングで OK)

### Phase 3 ─ Configure タブ + ライブプレビュー (1 セッション)
- [ ] Perlin / β / image_size / seed のスライダー & Entry
- [ ] スライダーが変わったら debounce 200ms で自動 [Preview 1] を再実行 (現在の OK + texture を流用)
- [ ] Foreground オプション: フォルダ選ばせる、無ければ disable

### Phase 4 ─ バックグラウンドワーカー化 (1 セッション)
- [ ] `threading.Thread(daemon=True)` でバッチ実行
- [ ] プログレスバー、進捗ラベル、キャンセルボタン
- [ ] `self._post(lambda: ...)` で UI 更新 (skill: tomomi-gui-style §13)
- [ ] エラーは `messagebox.showerror` + `traceback.format_exc()` を表示

### Phase 5 ─ 出力フォーマット拡張
- [ ] MVTec ライクな出力レイアウト切り替え
- [ ] `labels.csv` / `run.json`
- [ ] サムネイルストリップ表示 (生成済みサンプルの一覧、クリックで Canvas 拡大)

### Phase 6 ─ パッケージング (任意)
- [ ] PyInstaller spec (skill §15.2 の `collect_all` パターン)
- [ ] 依存 wheel 凍結

---

## 7. 主要なリスク

| リスク | 影響 | 対策 |
|---|---|---|
| `imgaug==0.4.0` × NumPy 2.x 不整合 | `np.sctypes` で起動不可 | `glass_env` (NumPy 1.26.3) で固定。requirements を変更しない (CLAUDE.md) |
| `MVTecDataset` を抽出するときに `transform_img`/`transform_mask` の Normalize/Resize の順序を取り違える | 出力が劣化 | Phase 1 で `dump_synthetic.py` の出力と pixel-level 同一を確認 (`np.allclose`) |
| Tk のメインスレッドにバッチ I/O が乗ると UI がフリーズ | UX 劣化 | Phase 4 で必ず `daemon=True` のスレッド + `root.after(0, ...)` パターン (skill §13) |
| OK 画像が極端に大 (4K 等) で合成が遅い | プレビューが固まる | プレビューは `image_size` (288) にリサイズしてから合成。バッチ時のみオリジナル解像度オプションを検討 (将来) |
| Foreground マスク無しで物体クラスを処理すると合成が背景に出る | 質が低下 | Configure に「Foreground 無し時の警告」表示。SAM2/U^2-Net 連携は Phase 7+ で別タスク化 |
| ImageTk.PhotoImage が GC される (skill §15.3) | プレビューが消える | `self._photo_*` でインスタンス属性に退避 |
| numpy 配列の truthiness (skill §15.1) | 起動時クラッシュ | `is None` + `len(...) == 0` の 2 段チェック厳守 |

---

## 8. 依存関係

`glass_env` 既存パッケージで足りるもの:
- numpy 1.26.3, torch 2.1.2, torchvision 0.16.2
- Pillow, opencv-python, imgaug 0.4.0, pandas, openpyxl
- tkinter (Python 標準)

**追加が必要:**
- `pygubu` (任意、UI ファイル管理が楽になる) — pure ttk でも書けるので Phase 1-3 は不要

`requirements.txt` (synthesizer_app 用):
```
# 既存 glass_env と同じピンに従う。差分のみここに記述。
# Phase 6 でパッケージするときに使用。
```

---

## 9. 受け入れ基準 (このプランの完了条件ではなく、最終アプリの DoD)

1. `run.bat` ダブルクリックでアプリが立ち上がる
2. OK 画像フォルダ + DTD フォルダ + 出力フォルダを選んで [Preview 1] を押すと 3 秒以内に Original / Synthetic / Mask が表示される
3. [Generate batch] で OK 画像 1 枚あたり N=10 枚を生成、UI はフリーズせずプログレスバーで進捗表示
4. 出力ディレクトリに `images/`, `masks/`, `originals/`, `panels/`, `labels.csv`, `run.json` が揃っている
5. `labels.csv` を pandas で読んで PatchCore のような既存ライブラリにそのまま食わせられる (MVTec 互換オプション ON のとき)
6. 同じ seed で再実行した時、生成画像が pixel-level で一致する
7. carpet / leather / bottle で生成した結果が、現状 `synthetic_dump/` にある panel と視覚的に区別できない (品質非劣化)

---

## 10. 確定事項 (2026-05-02 ユーザ回答)

| # | 質問 | 確定 | 設計への影響 |
|---|---|---|---|
| Q1 | GUI フレームワーク | **純 Tkinter + ttk** (Pygubu 不使用) | `ui/gui_main_ui.py` を手書き、Pygubu 関連設定は省略 |
| Q2 | 出力フォーマット | **MVTec 互換のみ** | `<output>/<class>/{train/good, test/synthetic, ground_truth/synthetic}` 構造に固定。独自 CSV や COCO マスクは出さない |
| Q3 | OK 画像の解像度 | **元解像度を保持** | 内部処理は `working_size=288` で固定 (perlin_mask が正方依存)、合成後に元解像度へ戻して保存 |
| Q4 | テクスチャ拡張性 | **DTD 以外も将来食わせる** | `core/io_utils.py` で「指定パス配下を再帰的に画像 (jpg/jpeg/png/bmp/tif) スキャン」する汎用ローダにする (DTD 固定の `*/*.jpg` を捨てる) |
| Q5 | クラス対応 | **1 クラス専用** | クラス切り替えタブは作らない。複数クラスは複数回起動 |
| Q6 | foreground マスク無し | **警告だけ出して続行** | Configure に「fg マスク未指定」インジケータと一行警告を表示 |
| Q7 | `dump_synthetic.py` リファクタ | **やる** (Phase 1 で実施) | `core.synthesis.synthesize_one` を呼ぶ薄いラッパに置換、視覚的非劣化を確認 |

---

## 11. 次の一手 (このプラン承認後に最初に着手)

1. ユーザに **Q1〜Q7 のうち重要な 2-3 個** だけ回答してもらう
2. **Phase 0 と Phase 1** を 1 セッションで実装し、
   - 雛形ディレクトリ
   - `core.synthesis.synthesize_one`
   - リファクタ後の `dump_synthetic.py` で carpet が以前と同じ出力を出すこと
   をエビデンスとして提示
3. その後 Phase 2 (最小 GUI) に進む

---

## 付録 A. 参考にするコード行

| ファイル | 行 | 内容 |
|---|---|---|
| `GLASS/datasets/mvtec.py` | 172-212 | `__getitem__`、LAS 合成本体 |
| `GLASS/perlin.py` | 全部 | Perlin マスク生成 |
| `GLASS/utils.py` | `torch_format_2_numpy_img` | denormalize → uint8 |
| `GLASS/dump_synthetic.py` | 全部 | 既存の CLI 版、リファクタ対象 |
| `skills/tomomi-gui-style/SKILL.md` | §1, §2, §11, §13, §15 | TR GUI 規約 |
| `skills/tomomi-gui-style/templates/custom_styles_jp.py` | 全部 | コピーして配置 |

## 付録 B. 用語

- **LAS**: Local Anomaly Synthesis ─ 画像空間で Perlin マスクを使ってテクスチャを合成。GUI が扱うのはここだけ。
- **GAS**: Global Anomaly Synthesis ─ 特徴空間で Gauss ノイズ + 勾配上昇。学習時のみ意味があり、画像出力に無関係 (今回 out-of-scope)。
- **mask_s**: feature 解像度 (288/8 = 36) の二値マスク、discriminator の教師信号
- **mask_l**: 画像解像度 (288×288) の二値マスク、合成画像の重み付け用
- **β**: 合成式 `(1-β) * texture + β * image` の混合比、`N(0.5, 0.1)` を `[0.2, 0.8]` でクリップ

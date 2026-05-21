# 489. Synthetic Data — 01. GLASS

GLASS（[A Unified Anomaly Synthesis Strategy with Gradient Ascent for Industrial Anomaly Detection and Localization](https://arxiv.org/abs/2407.09359), ECCV 2024）をローカル環境で再現し、その LAS（Local Anomaly Synthesis）部分を取り出して **NG (異常) 学習データを生成する GUI アプリ** を構築するためのワークスペース。

上流リポジトリ ([cqylunlun/GLASS](https://github.com/cqylunlun/GLASS), MIT License) を `GLASS/` に clone し、その周辺に論文 PDF・実行計画・依存インストール記録・合成データダンプ・GUI アプリ実装を配置している。

**最終ゴール**: 手元の OK 画像と任意のテクスチャ画像から、下流 AI 異常検知モデル (PatchCore / EfficientAD など) の学習に使える **NG 画像 + 二値マスク** を MVTec 互換レイアウトで生成する Tkinter デスクトップアプリ。

**📦 公開リポジトリ (standalone)**: https://github.com/kotai2003/glass-synthesizer-app
本ワークスペースの `synthesize_gui/`（vendored perlin 込みで clone 単体動作可）を公開していたもの。
**ただし 2026-05-17 に GUI アプリを `GLASS/synthesizer_app/` から `01.GLASS/synthesize_gui/` へ git 履歴なしで移動したため、従来の subtree-split 公開フローは無効**。公開リポは現状 stale。再開時は公開手段を再合意のこと（`00.docs/git_push_guide.md` / `CLAUDE.md` 参照）。

## ディレクトリ構成

```
01.GLASS/
├── 00.docs/
│   ├── 2407.09359v1.pdf                      論文
│   ├── GLASS_synth_gui_plan.md               GUI アプリ実装プラン (Phase 0〜6)
│   ├── GLASS_synthesizer_user_manual.md      GUI アプリのユーザーマニュアル（日本語、画面キャプチャ付き）
│   └── manual_screens/                       マニュアル用スクリーンショット (1600×900 PNG, 7 枚)
├── 01.reports/
│   ├── GLASS_execution_plan.md               実行計画（環境構築〜本実行まで）
│   └── GLASS_dependency_install_report.md    依存導入の試行錯誤と最終構成
├── GLASS/                                    上流 clone（.gitignore 済み）
│   ├── dump_synthetic.py                     合成データのみダンプする CLI（../synthesize_gui を import）
│   ├── requirements.txt                      上流の元 pinning（無修正）
│   ├── requirements_original.txt             requirements.txt のバックアップコピー
│   └── requirements_updated_current_env.txt  Py3.13 環境向けの試行（不採用、参考保管）
├── synthesize_gui/                           ★ NG データ合成 GUI アプリ（GLASS と並列、親 01.GLASS リポジトリで管理）
│   ├── core/                                 LAS 合成エンジン
│   │   ├── synthesis.py, exporter.py, io_utils.py    (synthesis は GPU 対応)
│   │   └── _vendored/perlin.py               上流 perlin.py を vendored (MIT 帰属)
│   ├── ui/                                   Tkinter UI 層 + custom_styles_jp.py
│   │   ├── TR_inc_logo.png                   ロゴ（読込時に背景を GUI 色へ合成）
│   │   ├── app_icon.ico / app_icon.png       ウィンドウ/タスクバー/EXE アイコン
│   │   └── _make_icon.py                     アイコン生成ユーティリティ
│   ├── tests/                                unittest
│   ├── LICENSE / LICENSE_GLASS               MIT (本体) + 上流 MIT (vendored 部分)
│   ├── README.md                             配布メタ
│   └── requirements.txt                      GLASS env 互換のピン
├── build_all.py                              ★ 保護付きビルド全体パイプライン
├── setup_cython.py                           Cython 化 (setup; ステージへコピーされ実行)
├── glass_app.py                              薄いランチャ（バンドル内で唯一の可読ソース）
├── glass_synthesizer.spec                    PyInstaller ONEDIR spec
├── glass_synthesizer_setup.iss               Inno Setup インストーラスクリプト
├── synthetic_dump/                           dump_synthetic.py の出力
│   └── <class>/{original,synthetic,mask,panel}/*.png
├── skills/                                   Claude Code 用ローカルスキル
│   ├── karphathy-guidelines/
│   └── tomomi-gui-style/                     TR 統一 GUI デザイン（synthesize_gui に適用）
├── CLAUDE.md                                 Claude Code 向けコードベースガイド
├── README.md                                 本ファイル
└── .gitignore
```

`GLASS/` は上流の独立した git repo であり、本ワークスペース側では追跡しない方針。

## はじめに読むもの

| 目的 | ドキュメント |
|---|---|
| **NG データ合成 GUI アプリのユーザーマニュアル**（各ウィジェットの操作方法・ワークフロー・出力構造、画面キャプチャ付き） | [`00.docs/GLASS_synthesizer_user_manual.md`](./00.docs/GLASS_synthesizer_user_manual.md) |
| **NG データ合成 GUI アプリの実装プラン** (Phase 構成・確定事項・受け入れ基準) | [`00.docs/GLASS_synth_gui_plan.md`](./00.docs/GLASS_synth_gui_plan.md) |
| 環境構築・実行手順・想定リスクをまとめて知りたい | [`01.reports/GLASS_execution_plan.md`](./01.reports/GLASS_execution_plan.md) |
| 実際に行った依存インストールの記録（どこで詰まり、どう解決したか） | [`01.reports/GLASS_dependency_install_report.md`](./01.reports/GLASS_dependency_install_report.md) |
| 上流コードのアーキテクチャと CLI の癖（`main.py` の click chain、`--distribution` / `--fg` の意味、出力先など） | [`CLAUDE.md`](./CLAUDE.md) |
| 上流の README・ライセンス | [`GLASS/README.md`](./GLASS/README.md) / [`GLASS/LICENSE`](./GLASS/LICENSE) |

## ローカル環境の現状

GLASS は **conda env `GLASS` から起動する**（旧ドキュメントの `glass_env` は誤り）。`requirements_original.txt` 完全準拠で構築済み。

| 項目 | 値 |
|---|---|
| Python 実行ファイル | `C:/Users/seong/anaconda3/envs/GLASS/python.exe` |
| Python | 3.9.15 |
| PyTorch | 2.1.2+cu118 / torchvision 0.16.2+cu118 |
| GPU | NVIDIA RTX 3060 Laptop, 6 GB VRAM (driver 595.97 / CUDA 13.0 capable, cu118 ホイールは forward 互換で動作確認済み) |
| MVTec AD | `C:/Datasets-rev002/01.MVTEC_Anomaly_Detection`（leather は junction で `leather_original` を参照）|
| DTD | `C:/Datasets-rev002/DTD/images`（47 カテゴリ × 5640 枚）|
| Foreground Mask | 未取得 → `--fg 0` 固定で運用 |

## 実行クイックスタート

### Smoke test（1 クラスで端から端まで疎通、~11 分）

```bash
GLASS_PY="C:/Users/seong/anaconda3/envs/GLASS/python.exe"
cd "GLASS"
"$GLASS_PY" main.py \
    --gpu 0 --seed 0 --test ckpt \
  net \
    -b wideresnet50 -le layer2 -le layer3 \
    --pretrain_embed_dimension 1536 --target_embed_dimension 1536 \
    --patchsize 3 --meta_epochs 1 --eval_epochs 1 \
    --dsc_layers 2 --dsc_hidden 1024 \
    --pre_proj 1 --mining 1 --noise 0.015 --radius 0.75 --p 0.5 \
    --step 20 --limit 8 \
  dataset \
    --distribution 2 --mean 0.5 --std 0.1 --fg 0 --rand_aug 1 \
    --batch_size 2 --resize 288 --imagesize 288 \
    -d carpet \
    mvtec C:/Datasets-rev002/01.MVTEC_Anomaly_Detection C:/Datasets-rev002/DTD/images
```

`--distribution 2` は `<dataset>_distribution.xlsx` の副作用を回避（manifold 強制）。`--fg 0` は fg_mask 不在に対応。`--batch_size 2` は 6 GB GPU 向け。

### 合成データだけ見る（学習・推論なし、数秒〜数分）

```bash
"$GLASS_PY" dump_synthetic.py \
    --datapath C:/Datasets-rev002/01.MVTEC_Anomaly_Detection \
    --augpath  C:/Datasets-rev002/DTD/images \
    -d carpet -d leather -d bottle \
    --num 30 \
    --outdir "../synthetic_dump"
```

各クラスについて `original/`, `synthetic/`, `mask/`, `panel/` の 4 フォルダに 30 枚ずつ書き出す。`panel/` の 1 枚が「正常 ｜ 合成異常 ｜ マスク」の横並び比較画像。

> 2026-05-02: 内部実装は `synthesize_gui.core.synthesis.synthesize_one` を呼ぶラッパに置換済み。
> CLI の出力フォーマットは互換維持。2026-05-17 に GUI アプリを `../synthesize_gui/` へ移動したため、
> `dump_synthetic.py` は親ディレクトリ（GLASS の 1 つ上）を `sys.path` に追加して import する。

### NG データ合成 GUI アプリ

実装プランは [`00.docs/GLASS_synth_gui_plan.md`](./00.docs/GLASS_synth_gui_plan.md)。
**Phase 0〜5 完了** (2026-05-02) — 基本機能・Configure タブ・スレッドワーカー・サムネイルストリップ全て実装済。
**2026-05-18: GPU 演算対応・ブランディング（ロゴ背景修正＋専用アプリアイコン）・配布パッケージ化（Cython 保護 exe ＋ Inno Setup インストーラ）完了。**
**2026-05-19: 合成をフル解像度・非正規化・ソフトマスク方式に刷新。** Perlin マスクのみ `working_size` で生成し、ブレンドは出力解像度で実行 → **マスク外の画素は元画像とビット完全一致**（全体の質感劣化＝旧 288px 縮小→拡大／正規化往復／マスクのジャギーを解消）。`working_size` は画質の天井ではなく異常マスクの粒度・速度つまみに。決定性契約は不変（テスト 5/5）。同方式を載せた保護 exe ＋インストーラを再ビルド・再検証 PASS。

```
synthesize_gui/                 （01.GLASS 直下、GLASS/ と並列）
├── core/
│   ├── synthesis.py            synthesize_one(image, texture, params) -> ng + mask（フル解像度・非正規化・ソフトマスク合成）
│   ├── exporter.py             MVTec 互換 writer
│   ├── io_utils.py             再帰的画像列挙
│   └── _vendored/perlin.py     上流 perlin.py を MIT vendoring (clone 単体で動作可)
├── ui/                         純 Tkinter + ttk + 統一スタイル
├── gui_main.py                 ロジック層 (threaded worker, queue-based main-thread dispatch)
├── tests/test_synthesis.py     5/5 passing
├── LICENSE / LICENSE_GLASS     MIT
└── requirements.txt
```

起動（`synthesize_gui/` を含むフォルダ＝`01.GLASS/` から）:

```bash
"$GLASS_PY" -m synthesize_gui.gui_main
```

ユニットテスト（同じく `01.GLASS/` から）:

```bash
"$GLASS_PY" -m unittest synthesize_gui.tests.test_synthesis -v
```

**確定事項** (プラン §10): 純 Tkinter / MVTec 互換出力 / 元解像度保持 / 1 クラス専用 / fg マスク無し時は警告のみ / `dump_synthetic.py` リファクタ済。

操作方法・各ウィジェットの説明・典型的なワークフローについては [`00.docs/GLASS_synthesizer_user_manual.md`](./00.docs/GLASS_synthesizer_user_manual.md) (画面キャプチャ付き、日本語) を参照。マニュアル用スクリーンショットを更新したい場合は、UI を変更後に
`"$GLASS_PY" synthesize_gui/tests/_capture_manual_screens.py` を実行すれば `00.docs/manual_screens/*.png` が再生成される。

#### 公開リポへの反映フロー（2026-05-17 時点で無効）

> 旧フロー（`GLASS` 内側リポジトリからの `git subtree split --prefix=synthesizer_app`）は
> 2026-05-17 の移動で**機能しなくなった**。`synthesize_gui/` は `GLASS` 内側リポジトリの外、
> 親 `01.GLASS` リポジトリ管理下に git 履歴なしで移動された。スタンドアロン公開を再開する場合は
> 公開手段をユーザーと再合意すること（詳細は `CLAUDE.md` の "Standalone publication" 参照）。

`syn_origin` は https://github.com/kotai2003/glass-synthesizer-app 。
**`origin` (cqylunlun/GLASS 上流) には絶対 push しない**。

### GPU 演算

合成の β ブレンド（画像 × テクスチャ × マスク）は CUDA があれば GPU で実行される。`SynthParams.device`：

- `"auto"`（既定）— GPU があれば CUDA、無ければ CPU
- `"cuda"` — GPU 強制（無ければエラー）
- `"cpu"` — CPU 強制

出力は CPU/GPU でビット完全一致を確認済み。プレビューのステータス行に `[GPU]`/`[CPU]` を表示。
※ vendored の `perlin.py`（MIT, 改変不可）は numpy/imgaug 実装で **CPU 固定**。GPU 化されるのはブレンド部のみ。

## 保護付き配布ビルド（Cython + PyInstaller + Inno Setup）

リバースエンジニアリング対策として、IP モジュール 7 本（synthesis/exporter/io_utils/perlin/gui_main/gui_main_ui/custom_styles_jp）を **Cython でネイティブ `.pyd` 化**し、ソースを除去した状態で PyInstaller ONEDIR 化、さらに **Inno Setup でインストーラ** を生成する。TOMOMI 標準（`../00.FORESIGHT_VIEWER_TR100` 準拠）。

```bash
# 01.GLASS/ から、GLASS env で。ステージ→Cython→PyInstaller→検証 を一括実行
"$GLASS_PY" build_all.py
```

- **ビルド出力は OneDrive 外**：`C:\TR_build\GLASS\{build_cython_stage,build,dist}\`（`GLASS_BUILD_ROOT` で変更可）。OneDrive 同期が巨大出力ツリーをロックし PyInstaller COLLECT が `WinError 5` で失敗するため。リポジトリへ戻るのは `build_all.log` のみ。
- 配布物：`C:\TR_build\GLASS\dist\GLASS_Synthesizer\GLASS_Synthesizer.exe`（約 5.7 GB。cu118 torch が CUDA 同梱のため）。
- インストーラ：`glass_synthesizer_setup.iss` を Inno Setup でコンパイル → `Output/` に `GLASS_Synthesizer_Setup.exe`。
- `build_all.py` の Step3 検証：保護ソース非混入・全 `.pyd` 同梱・`.pyd` import・起動時 stderr にクラッシュ痕跡が無いこと（windowed exe はエラーダイアログで生存し続けるため「生存」では判定しない）。詳細・既知の落とし穴（`tkinter.ttk` / `imageio` メタデータ）は [`CLAUDE.md`](./CLAUDE.md) の "Building the protected `.exe` distributable" を参照。

## 検証済みの動作

`mvtec_carpet` の smoke test (1 epoch / 10 サンプル / batch=2) で end-to-end 動作確認済み:

- I-AUROC 92.42 / P-AUROC 93.90 / P-PRO 78.03（10 サンプル学習なので論文値 99.9/99.3 には未到達。疎通確認の意味では十分）
- アーティファクト: `GLASS/results/models/backbone_0/mvtec_carpet/{ckpt.pth, ckpt_best_0.pth, tb/}`、`results/{training,eval}/mvtec_carpet/*.png` 117 枚、`results/results.csv`

## 既知の制約

- **GPU メモリ 6 GB**: 上流の `--batch_size 8` × `wide_resnet50_2` × `imagesize 288` は OOM の可能性が高い。`batch_size` は 2〜4 推奨。
- **`shell/run-*.sh` は未編集**: 上流ディレクトリを汚さないため、データパス書き換えではなく直接 CLI 実行で運用している。
- **配布チェックポイント未取得**: `--test test` で論文値再現するには Google Drive から `results/` 配下を別途取得し `GLASS/results/` に展開する必要あり（実行計画レポート §3.4 参照）。
- **`pth2onnx.py`/`ort.py`（ONNX 書き出し）は未検証**: ハードコードパスの修正と `onnxruntime-gpu` の動作確認が必要。

## 上流リポジトリ情報

- **Repo**: https://github.com/cqylunlun/GLASS
- **clone 時 commit**: `f788d567db552820d744ca2d93e989265aad8c45` (`update readme`, 2026-03-30)
- **License**: MIT（上流）
- **論文**: Chen et al., ECCV 2024, [arXiv:2407.09359](https://arxiv.org/abs/2407.09359)

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
│   │   ├── synthesis.py, exporter.py, io_utils.py
│   │   └── _vendored/perlin.py               上流 perlin.py を vendored (MIT 帰属)
│   ├── ui/                                   Tkinter UI 層 + custom_styles_jp.py + ロゴ
│   ├── tests/                                unittest
│   ├── LICENSE / LICENSE_GLASS               MIT (本体) + 上流 MIT (vendored 部分)
│   ├── README.md                             配布メタ
│   └── requirements.txt                      glass_env 互換のピン
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

GLASS は **conda env `glass_env` から起動する**。`requirements_original.txt` 完全準拠で構築済み。

| 項目 | 値 |
|---|---|
| Python 実行ファイル | `C:/Users/seong/anaconda3/envs/glass_env/python.exe` |
| Python | 3.9.15 |
| PyTorch | 2.1.2+cu118 / torchvision 0.16.2+cu118 |
| GPU | NVIDIA RTX 3060 Laptop, 6 GB VRAM (driver 595.97 / CUDA 13.0 capable, cu118 ホイールは forward 互換で動作確認済み) |
| MVTec AD | `C:/Datasets-rev002/01.MVTEC_Anomaly_Detection`（leather は junction で `leather_original` を参照）|
| DTD | `C:/Datasets-rev002/DTD/images`（47 カテゴリ × 5640 枚）|
| Foreground Mask | 未取得 → `--fg 0` 固定で運用 |

## 実行クイックスタート

### Smoke test（1 クラスで端から端まで疎通、~11 分）

```bash
GLASS_PY="C:/Users/seong/anaconda3/envs/glass_env/python.exe"
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

```
synthesize_gui/                 （01.GLASS 直下、GLASS/ と並列）
├── core/
│   ├── synthesis.py            synthesize_one(image, texture, params) -> ng + mask
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

# 489. Synthetic Data — 01. GLASS

GLASS（[A Unified Anomaly Synthesis Strategy with Gradient Ascent for Industrial Anomaly Detection and Localization](https://arxiv.org/abs/2407.09359), ECCV 2024）をローカル環境で再現・検証するためのワークスペース。

上流リポジトリ ([cqylunlun/GLASS](https://github.com/cqylunlun/GLASS), MIT License) を `GLASS/` に clone し、その周辺に論文 PDF・実行計画・社内向け補助スキルを配置している。

## ディレクトリ構成

```
01.GLASS/
├── 00.docs/                          論文 PDF (2407.09359v1.pdf)
├── 01.reports/                       検証レポート
│   └── GLASS_execution_plan.md       実行計画（環境構築〜本実行まで）
├── GLASS/                            上流 clone（.gitignore 済み）
├── skills/                           Claude Code 用ローカルスキル
│   ├── karphathy-guidelines/
│   └── tomomi-gui-style/
├── CLAUDE.md                         Claude Code 向けコードベースガイド
├── README.md                         本ファイル
└── .gitignore
```

`GLASS/` は上流の独立した git repo であり、本ワークスペース側では追跡しない方針。

## はじめに読むもの

| 目的 | ドキュメント |
|---|---|
| 環境構築・実行手順・想定リスクをまとめて知りたい | [`01.reports/GLASS_execution_plan.md`](./01.reports/GLASS_execution_plan.md) |
| 上流コードのアーキテクチャと CLI の癖（`main.py` の click chain、`--distribution` / `--fg` の意味、出力先など） | [`CLAUDE.md`](./CLAUDE.md) |
| 上流の README・ライセンス | [`GLASS/README.md`](./GLASS/README.md) / [`GLASS/LICENSE`](./GLASS/LICENSE) |

## 実行クイックスタート

詳細は実行計画レポートを参照。最短経路の概要のみ:

```bash
# 1. 環境
conda create -n glass_env python=3.9.15 -y
conda activate glass_env
cd GLASS
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# 2. データセット配置（例: D:/datasets/ に MVTec AD と DTD を展開）
#    fg_mask/ も <datapath>/fg_mask/<class>/<file>.png に配置

# 3. shell/run-mvtec.sh の datapath / augpath を書き換えてから
cd shell
bash run-mvtec.sh
```

> 初回はまず `--distribution 1` で `./datasets/excel/<dataset>_distribution.xlsx` を生成する必要がある。詳細は実行計画レポート §3.5 参照。

## 上流リポジトリ情報

- **Repo**: https://github.com/cqylunlun/GLASS
- **clone 時 commit**: `f788d567db552820d744ca2d93e989265aad8c45` (`update readme`, 2026-03-30)
- **License**: MIT（上流）
- **論文**: Chen et al., ECCV 2024, [arXiv:2407.09359](https://arxiv.org/abs/2407.09359)

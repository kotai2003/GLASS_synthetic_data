# Git Push 運用ガイド

このワークスペースは **3つの git リポジトリ / 4つのリモート** が絡む構造になっており、`git push` を打つ場所と引数を間違えると意図しないリポジトリに変更が飛んだり、上流 (`cqylunlun/GLASS`) を汚染するリスクがあります。本ドキュメントは安全な push 手順をまとめたものです。

---

> ⚠️ **2026-05-17 更新: スタンドアロン (`syn_origin` / subtree split) 関連の手順は無効です。**
> GUI アプリは `GLASS/synthesizer_app/` から `01.GLASS/synthesize_gui/` へ git 履歴なしで移動しました
> （`GLASS` 内側リポジトリの外、親 `01.GLASS` リポジトリ管理下）。
> `git subtree split --prefix=synthesizer_app` は対象が存在しないため失敗します。
> 現在 `synthesize_gui/` は **外側 `01.GLASS` リポジトリ (`origin`) で直接管理**されます。
> 以下の §2.2 / §3 のスタンドアロン手順・コミット履歴表は記録として残しますが、実行しないでください。
> スタンドアロン公開を再開する場合は公開手段をユーザーと再合意すること
> （`CLAUDE.md` の "Standalone publication" 参照）。

---

## 1. リポジトリとリモートの構成

```
01.GLASS/                              ← 外側ワークスペースリポ
├── .git/                              origin → kotai2003/GLASS_synthetic_data   (push OK)
│
└── GLASS/                             ← 内側 (上流 clone)
    └── .git/                          origin     → cqylunlun/GLASS                (push 禁止)
                                       syn_origin → kotai2003/glass-synthesizer-app (push OK, subtree split 経由)
```

| # | リポジトリ | リモート | 用途 | push してよいか |
|---|---|---|---|---|
| 1 | 外側ワークスペース | `origin` = `kotai2003/GLASS_synthetic_data` | docs / 計画書 / GLASS gitlink を保存 | ✅ |
| 2 | 内側 GLASS clone | `origin` = `cqylunlun/GLASS` | 上流ミラー | ❌ **絶対に push しない** |
| 3 | 内側 GLASS clone | `syn_origin` = `kotai2003/glass-synthesizer-app` | スタンドアロン配布用 (subtree 経由) | ✅ |

何を含むか:

- **外側** (`origin`): `00.docs/`, `01.reports/`, `README.md`, `CLAUDE.md`, `.gitignore`, GLASS の gitlink (submodule pointer) など。`GLASS/` 配下の実体は `.gitignore` 済みなので含まれない。
- **スタンドアロン** (`syn_origin`): `GLASS/synthesizer_app/` の中身だけを `git subtree split --prefix=synthesizer_app` で抽出した内容。配布用の単独で動く repo。

---

## 2. 基本コマンド

### 2.1 外側ワークスペースを push

```powershell
# 01.GLASS/ で実行
git push origin main
```

### 2.2 スタンドアロン (synthesizer_app/) を push

```powershell
# 必ず GLASS/ の中で実行
cd GLASS
git subtree split --prefix=synthesizer_app -b syn_split
git push syn_origin syn_split:main
```

### 2.3 上流への push 防止 (推奨設定)

万一 `cd GLASS && git push` (引数なし) を打っても上流に飛ばないよう、以下のいずれかを設定しておくと安全:

```powershell
# (a) origin の push URL を無効化 (fetch だけ残す)
git -C GLASS remote set-url --push origin no_push

# (b) origin の push を完全削除 (上流 fetch も不要なら)
git -C GLASS remote remove origin
```

(a) の状態だと、誤って `git push` した場合 `fatal: 'no_push' does not appear to be a git repository` で失敗するため安全側に倒れます。

---

## 3. 典型的なワークフロー

### A. ドキュメント / 設定だけ変更 (外側のみ更新)

例: `README.md`, `CLAUDE.md`, `00.docs/*` を編集した場合。

```powershell
# 01.GLASS/ で実行
git add README.md CLAUDE.md "00.docs/"
git commit -m "docs: ..."
git push origin main
```

### B. `GLASS/synthesizer_app/` を変更 (両方更新)

例: GUI のロジックや UI を変えた場合。

```powershell
# (1) 内側 GLASS repo に変更をコミット
cd GLASS
git add synthesizer_app/
git commit -m "synthesizer_app: ..."

# (2) スタンドアロンリポへ subtree split & push
git subtree split --prefix=synthesizer_app -b syn_split
git push syn_origin syn_split:main

# (3) 外側に戻り、gitlink を新 SHA に bump して push
cd ..
git add GLASS
git commit -m "GLASS: bump to <one-line summary>"
git push origin main
```

ステップ (3) は必須ではないが、外側 repo を clone した人が `GLASS/` の特定 SHA を再現する必要がある場合のみ実施。`.gitignore` に `GLASS/` が含まれている以上、省略しても他者の clone で困ることは少ない。

### C. GLASS 上流コードに修正を加えた (検証目的)

`GLASS/main.py` や `GLASS/datasets/mvtec.py` などをいじった場合は、外側 repo の `.gitignore` で追跡対象外なので、内側にコミットするしかない。`origin` (= 上流) には絶対 push しない。

```powershell
cd GLASS
git add main.py datasets/
git commit -m "local: <experiment description>"
# push しない (ローカル研究目的のため)
```

---

## 4. チェック用コマンド

### 現在のリモート構成を確認

```powershell
# 外側
git remote -v

# 内側
git -C GLASS remote -v
```

期待される出力:

```
# 外側
origin  https://github.com/kotai2003/GLASS_synthetic_data.git (fetch)
origin  https://github.com/kotai2003/GLASS_synthetic_data.git (push)

# 内側
origin      https://github.com/cqylunlun/GLASS.git (fetch)
origin      https://github.com/cqylunlun/GLASS.git (push)
syn_origin  https://github.com/kotai2003/glass-synthesizer-app.git (fetch)
syn_origin  https://github.com/kotai2003/glass-synthesizer-app.git (push)
```

### どこまで push 済みか確認

```powershell
# 外側で未 push のコミット一覧
git log origin/main..HEAD --oneline

# 内側 synthesizer_app/ のうち syn_origin に未反映のコミット
git -C GLASS log syn_origin/main..HEAD --oneline -- synthesizer_app/

# 外側が指している内側 gitlink の SHA
git ls-tree HEAD GLASS
```

### 内側 origin (上流) を fetch していないことを確認

```powershell
git -C GLASS log origin/main..HEAD --oneline
# このコマンドが多数のコミットを返すのは正常 (上流より先行している証)
# このリストに含まれるコミットは絶対に origin に push しない
```

---

## 5. やってはいけないこと

| 危険な操作 | 何が起きるか | 代わりに |
|---|---|---|
| `cd GLASS && git push` (引数なし) | 上流 `cqylunlun/GLASS` への push を試行 | `git push syn_origin syn_split:main` を明示 |
| `cd GLASS && git push --force` | 上記 + 履歴上書き | 同上 |
| `git push origin syn_split:main` (内側で) | 上流に subtree split を上書きしようとする | リモート名を `syn_origin` に |
| `cd GLASS && git pull` (引数なし) | 上流 main を merge し、ローカルの `synthesizer_app/` 追加が混ざる | 上流追従は通常不要。必要なら `git fetch origin` のみに留め、merge は手動 |
| 内側で `git rebase -i origin/main` | 上流コミット履歴を巻き戻す | 内側のローカルコミットは push 不要なので rebase 自体不要 |

---

## 6. 緊急時 (上流に push してしまった疑い)

1. `git -C GLASS log --oneline origin/main` を確認し、`9d23746 first commit` 以降のローカルコミット (例: `synthesizer_app: ...` など) が **上流リモートに到達していないこと** を確認。
2. もし到達してしまっていたら GitHub 上で revert PR を出すしかない (上流のメンテナ宛て)。
3. 再発防止として §2.3 の `remote set-url --push origin no_push` を設定しておく。

---

## 付録: 過去の主要コミット (参考)

| 日付 | リポ | SHA | 内容 |
|---|---|---|---|
| 2026-05-01 | 外側 | `9d23746` | first commit |
| 2026-05-02 | 外側 | `899ad5b` | add GUI app plan, install report, and reflect Phase 0-5 in docs |
| 2026-05-02 | 外側 | `62a8cc0` | docs: reflect standalone glass-synthesizer-app repo and vendored perlin |
| 2026-05-02 | 外側 | `9e96905` | docs: add GUI synthesizer user manual with screenshots |
| 2026-05-02 | 外側 | `bf64def` | GLASS: bump to include capture-script standalone-repo guard |
| 2026-05-02 | 内側 | `8cf7488` | synthesizer_app: vendor perlin.py for self-contained distribution |
| 2026-05-02 | 内側 | `b69c268` | synthesizer_app: add manual screenshot capture utility |
| 2026-05-02 | 内側 | `e7024fa` | synthesizer_app: guard capture script against standalone-repo run |

---

(C) 2026 TOMOMI RESEARCH, INC.

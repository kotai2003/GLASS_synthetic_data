# TOMOMI RESEARCH デザイントークン詳細仕様

## フォント定義

```python
jp_font = ("Meiryo", 12)           # 標準テキスト
jp_font_bold = ("Meiryo", 12, "bold")  # ボタン、見出し、LabelFrame
```

- Windows環境前提のため **Meiryo** を使用
- サイズ12は日本語の可読性とUIの密度のバランス
- macOSでテストする場合は "Hiragino Sans" にフォールバック可

---

## ttkスタイル一覧

### primary.TButton
```python
style.configure("primary.TButton",
    font=("Meiryo", 12, "bold"),
    padding=(12, 6),
    relief="flat"
)
```
用途: Live, Start, Quit, Save Config File など主要操作

### secondary.TButton
```python
style.configure("secondary.TButton",
    font=("Meiryo", 12, "bold"),
    padding=(12, 6),
    anchor="center",
    relief="flat",
    borderwidth=0
)
style.map("secondary.TButton",
    background=[('active', '#5A6268'), ('pressed', '#495057')],
    foreground=[('disabled', '#999999')]
)
```
用途: Repeat, Open Folder など補助操作

### custom.TCheckbutton
```python
style.configure("custom.TCheckbutton",
    font=("Meiryo", 12),
    padding=6,
    anchor="w"
)
```

### custom.TRadiobutton
```python
style.configure("custom.TRadiobutton",
    font=("Meiryo", 12),
    padding=6,
    anchor="w"
)
```

### custom.TLabel
```python
style.configure("custom.TLabel",
    font=("Meiryo", 12),
    anchor="w",
    padding=4
)
```

### custom.TLabelframe / custom.TLabelframe.Label
```python
style.configure("custom.TLabelframe",
    font=("Meiryo", 12, "bold"),
    relief="groove",
    borderwidth=0
)
style.configure("custom.TLabelframe.Label",
    font=("Meiryo", 12, "bold"),
    padding=(4, 0)
)
```

### custom.TFrame
```python
style.configure("custom.TFrame")
# 背景色はOSテーマに委ねる（明示指定なし）
```

### custom.TEntry
```python
style.configure("custom.TEntry",
    font=("Meiryo", 12),
    padding=4
)
```

---

## カラーポリシー

### 基本方針: OSテーマ追従

色は原則として **明示的に指定しない**。ttkのデフォルトテーマ（Windows: "vista", "winnative"）に任せる。

### コメントアウト準備パターン
将来的にカスタムテーマ対応が必要になった場合に備え、色指定はコメントアウトして残す：

```python
style.configure("primary.TButton",
    font=jp_font_bold,
    # foreground="blue",
    # background="red",
    padding=(12, 6),
    relief="flat"
)
```

### secondary.TButtonのみ例外
ホバー/押下/無効化の状態色は明示的に設定：
- active: `#5A6268`
- pressed: `#495057`
- disabled foreground: `#999999`

---

## 余白（Padding）ルール

### pack配置時の標準余白

```python
PACK_LAYOUT = {
    'expand': True,
    'fill': 'both',
    'side': 'top',
    'padx': 10,
    'pady': 5
}
```

### ウィジェット別の余白

| ウィジェット | padx | pady | side | fill | expand |
|-------------|------|------|------|------|--------|
| LabelFrame | 5 | 5 | top | both | True |
| ボタン (Control内) | 30 | 5 | top | both | True |
| Radiobutton (縦) | 10 | — | top | both | True |
| Checkbutton (横) | 10 | 5 | left | both | True |
| ロゴ Label | — | — | top | x | True |
| Canvas | — | — | top | both | True |

### grid配置時（Configureタブ）

| 要素 | column | padx | sticky |
|------|--------|------|--------|
| Label | 0 | 5 | ew |
| Scale/Entry | 1 | 5 | ew |
| col 1 weight | — | — | 1 |

---

## LabelFrame セクション命名規則

セクション名は **英語** で、機能を端的に表す：

- `Show Mode` — 表示モード切替
- `Enhance Mode` — 強調フィルタ
- `Preprocess Mode` — 前処理
- `Auto Object Alignment` — 自動位置合わせ
- `Image Save Mode` — 画像保存
- `Control` — 操作ボタン群
- `Camera Settings` — カメラ設定
- `Lighting Setting` — 照明設定
- `Photometric Stereo` — PS設定
- `Camera Show` — カメラ表示オプション
- `Crop (need to restart)` — クロップ設定
- `Image Rotate (need to restart)` — 回転設定

注意事項が必要な場合は `(need to restart)` のように括弧で補足。

---

## PanedWindow分割比

```
メインウィンドウ: horizontal PanedWindow
  ├── 左ペイン (weight=5) — 画像表示エリア
  │   └── vertical PanedWindow
  │       ├── 上ペイン (weight=10) — メインCanvas
  │       └── 下ペイン (weight=1)  — サブCanvas群（横並び）
  └── 右ペイン (weight=1) — コントロールパネル（Notebook）
```

左:右 = 5:1 の比率で画像表示を優先する設計。

---
name: tomomi-gui-style
description: >
  TOMOMI RESEARCH社のデスクトップGUIアプリケーション開発専用スキル。
  Tkinter/ttk + Pygubuベースのアプリを、会社の統一デザインシステムに準拠して生成・修正する。
  このスキルは以下のリクエストで必ず発動すること：
  「GUIアプリを作って」「Tkinterで画面を作りたい」「デスクトップアプリのUIを作成」
  「ttkのスタイルを設定」「Pygubuでデザイン」「ボタンやラベルの見た目を統一したい」
  「TOMOMI風のGUI」「TR-100/TR-300/E3 ENGINEのGUI」「検査アプリのUI」
  「カメラビューアのGUI」「設定画面を追加したい」など。
  Python GUI、tkinter、ttk、pygubu、デスクトップアプリ、Windows GUI、
  検査システムUI、産業用GUIなどのキーワードにも反応すること。
---

# TOMOMI RESEARCH GUI Design System

TOMOMI RESEARCH, Inc.の全GUIアプリケーションに適用する統一デザインルールとコード規約。
Claude Codeはこのスキルに従い、会社のブランドとUXパターンを一貫して再現する。

## クイックスタート

新規GUIアプリ作成時の手順：

1. このSKILL.mdを読む
2. `references/design_tokens.md` でカラー・フォント・余白の詳細を確認
3. `templates/custom_styles_jp.py` をプロジェクトの `ui/` にコピー
4. `templates/base_app.py` を雛形としてアプリを構築
5. ロゴは `assets/TR_inc_logo.png` を `ui/` に配置

---

## 1. アーキテクチャパターン

### ディレクトリ構成（必須）

```
my_app/
├── gui_main.py              ← メインアプリケーション（ビジネスロジック）
├── ui/
│   ├── gui_main_ui.py       ← Pygubu生成 or 手書きのUIクラス
│   ├── custom_styles_jp.py  ← ttk スタイル定義（共通モジュール）
│   ├── TR_inc_logo.png      ← 会社ロゴ
│   └── *.ui                 ← Pygubu UIファイル（使用する場合）
├── required_files/           ← ini, 設定テンプレート等
└── favicon_TR100.ico         ← ウィンドウアイコン（任意）
```

### クラス構成（2層分離パターン）

```python
# ui/gui_xxx_ui.py — UIレイヤー（ウィジェット定義のみ）
class GuiXxxUI:
    def __init__(self, master=None, ...):
        # ウィジェット生成、変数バインド、コールバック接続
        pass

# gui_xxx.py — ロジックレイヤー（UIを継承）
class GuiXxx(GuiXxxUI):
    def __init__(self, master=None):
        custom_styles_jp.setup_ttk_styles(master)  # ← 最初にスタイル設定
        super().__init__(master)
        # ハードウェア接続、ビジネスロジック初期化
```

**重要**: `custom_styles_jp.setup_ttk_styles()` は必ずウィジェット生成前に呼ぶ。

---

## 2. デザイントークン（サマリー）

詳細は `references/design_tokens.md` を参照。

### フォント
| 用途 | フォント | サイズ | ウェイト |
|------|----------|--------|----------|
| 標準テキスト | Meiryo | 12 | normal |
| ボタン・見出し | Meiryo | 12 | bold |
| コピーライト | Meiryo | 12 | bold |

### カラーポリシー
- **OS/ttkテーマに委ねる設計**（明示的な色指定は最小限）
- 背景色・前景色はコメントアウトして準備するが、デフォルトでは設定しない
- これによりWindows のライト/ダークテーマに自然に追従する

### 余白ルール
| コンテキスト | padx | pady |
|-------------|------|------|
| LabelFrame内ウィジェット | 10 | 5 |
| ボタン（Controlセクション） | 30 | 5 |
| Radiobutton / Checkbutton | 10 | 5（またはpady省略） |
| LabelFrame自体 | 5 | 5 |

---

## 3. ウィジェットスタイル規約

### ボタン

```
primary.TButton   → 主要アクション（Live, Start, Quit, Save Config）
                     padding=(12,6), relief="flat", font=Meiryo 12 bold
secondary.TButton → 補助アクション（Repeat, Open Folder）
                     padding=(12,6), relief="flat", borderwidth=0
```

- ボタンは `pack(expand=True, fill="both", padx=30, pady=5, side="top")`
- 「Control」LabelFrame内に縦積みで配置

### Checkbutton / Radiobutton

```
custom.TCheckbutton  → padding=6, anchor="w"
custom.TRadiobutton  → padding=6, anchor="w"
```

- 横並び時: `pack(side="left", padx=10, expand=True, fill="both")`
- 縦並び時: `pack(side="top", padx=10, expand=True, fill="both")`

### LabelFrame（セクション区切り）

```
custom.TLabelframe       → relief="groove", borderwidth=0, font=bold
custom.TLabelframe.Label → font=bold, padding=(4,0)
```

- 機能グループごとに1つのLabelFrameで囲む
- セクション例: "Show Mode", "Enhance Mode", "Control", "Camera Settings"

### Label / Entry

```
custom.TLabel → padding=4, anchor="w"
custom.TEntry → padding=4
```

### Notebook（タブ）

- 主要機能を「Control」タブ、詳細設定を「Configure」タブに分離
- タブ名は英語

---

## 4. レイアウトパターン

### 全体構成（メインウィンドウ）

```
┌─────────────────────────────────────────────────────┐
│ Toplevel (1920x1080)                                │
│ ┌──────────────────────────┬──────────────────────┐ │
│ │  PanedWindow (左: weight=5)│  PanedWindow (右: w=1)│ │
│ │  ┌──────────────────────┐│  ┌──────────────────┐│ │
│ │  │  メインCanvas (上)    ││  │  Notebook        ││ │
│ │  │  (画像表示エリア)     ││  │  ┌─ Control     ││ │
│ │  ├──────────────────────┤│  │  │  ロゴ         ││ │
│ │  │  サブCanvas群 (下)    ││  │  │  設定群       ││ │
│ │  │  [2D] [3D] [SN]      ││  │  │  ボタン群     ││ │
│ │  └──────────────────────┘│  │  │  (C) TOMOMI.. ││ │
│ │                          │  │  ├─ Configure   ││ │
│ │                          │  │  │  スライダー群  ││ │
│ └──────────────────────────┴──┴──┴──────────────┘│ │
└─────────────────────────────────────────────────────┘
```

### サイドパネル（Controlタブ）構成順序

1. **ロゴ** — 上部、`pack(expand=True, fill="x", side="top")`
2. **機能セクション群** — LabelFrameで区切り、上から順にpack
3. **Controlボタン群** — 最下部にLabelFrame "Control"
4. **コピーライト** — 最下端 `(C) {YEAR} TOMOMI RESEARCH, INC.`

### Configureタブ構成

- grid配置: Label(col=0) + LabeledScale/Entry/Combobox(col=1)
- col=1に `weight=1` でスライダーを伸縮可能に

---

## 5. ロゴ配置ルール

- ファイル: `TR_inc_logo.png`
- 配置: サイドパネル最上部（Notebookの最初のタブ内）
- レイアウト: `ttk.Label` に `image` プロパティで設定
- pack: `expand=True, fill="x", side="top"`
- ロゴの上下に余計なpaddingは入れない

---

## 6. コピーライト表記

```python
# フォーマット
"(C) {YEAR} TOMOMI RESEARCH, INC."

# スタイル: custom.TLabelframe.Label（bold）
# 配置: サイドパネル最下部
# pack: anchor="center", expand=True, fill="both", padx=5, side="top"
```

**YEARは現在の年を使用すること。**

---

## 7. ウィンドウ設定

```python
# タイトルフォーマット
"{アプリ名} by TOMOMI RESEARCH, INC."

# 例
"FORESIGHT STEREO Viewer by TOMOMI RESEARCH, INC."
"E3 ENGINE Trainer by TOMOMI RESEARCH, INC."

# デフォルトジオメトリ
geometry = "1920x1080"  # フルHD前提

# アイコン（利用可能な場合）
iconbitmap = "favicon_TR100.ico"
```

---

## 8. 画像表示パターン（Canvas）

```python
# OpenCV → Tkinter変換パターン
def display_on_canvas(canvas, cv_image, photo_dict, canvas_id):
    """cv2画像をCanvasに表示する共通パターン"""
    h, w = cv_image.shape[:2]
    canvas_w = canvas.winfo_width()
    canvas_h = canvas.winfo_height()
    
    # アスペクト比を保ってリサイズ
    scale = min(canvas_w / w, canvas_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(cv_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # BGR→RGB→PIL→ImageTk
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    photo = ImageTk.PhotoImage(pil_img)
    
    # 参照保持（GC防止）
    photo_dict[canvas_id] = photo
    canvas.delete("all")
    canvas.create_image(canvas_w // 2, canvas_h // 2, image=photo, anchor="center")
```

---

## 9. コーディング規約

### 命名規則
| 対象 | パターン | 例 |
|------|---------|-----|
| UIクラス | `Gui{Product}UI` | `GuiTr100UiUI` |
| ロジッククラス | `Gui{Product}` | `GuiTr100Ui` |
| UIファイル | `gui_{product}_ui.py` | `gui_fs_viewer_Tr100ui.py` |
| ロジックファイル | `gui_{product}.py` | `gui_fs_viewer_tr100.py` |
| Tk変数（UI層） | `{name}_var_ui` | `exptime_var_ui`, `save_var_ui` |
| Tk変数（ロジック層） | `var_{name}` | `var_exp_time`, `var_br_live` |
| ボタンID | `button_{action}` | `button_start`, `button_quit` |
| キャンバスID | `canvas_{purpose}` | `canvas_main`, `canvas_2d` |

### import順序
```python
# 1. 標準ライブラリ
import pathlib, tkinter, os, sys, threading, datetime

# 2. サードパーティ
import cv2, numpy, PIL, torch

# 3. TOMOMI RESEARCH 内部パッケージ
from ui.gui_xxx_ui import GuiXxxUI
import ui.custom_styles_jp as custom_styles_jp
from tr_foresight_stereo import ...
from tr_utils import ...
```

### PyInstaller対応パス解決
```python
if getattr(sys, 'frozen', False):
    _temp_path = pathlib.Path(sys._MEIPASS)
else:
    _temp_path = pathlib.Path(__file__).parent

PROJECT_PATH = _temp_path  # or fallback logic
```

### docstring
- クラス・メソッドには英語docstring
- printログ・コメントは日本語OK（絵文字使用可: ✅❌⚠️🛠️📁）

---

## 10. Pygubu統合ルール

Pygubuを使用する場合：

```python
# UIクラスのパターン
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "{app_name}.ui"
RESOURCE_PATHS = [PROJECT_PATH]

class GuiXxxUI:
    def __init__(self, master=None, translator=None, 
                 on_first_object_cb=None, data_pool=None):
        self.builder = pygubu.Builder(
            translator=translator,
            on_first_object=on_first_object_cb,
            data_pool=data_pool
        )
        self.builder.add_resource_paths(RESOURCE_PATHS)
        self.builder.add_from_file(PROJECT_UI)
        self.mainwindow = self.builder.get_object("toplevel1", master)
        
        # Tk変数のインポート
        self.xxx_var_ui: tk.StringVar = None
        self.builder.import_variables(self)
        self.builder.connect_callbacks(self)
```

### .uiファイルの設定
```xml
<setting id="use_ttk_styledefinition_file">True</setting>
<setting id="ttk_style_definition_file">custom_styles_jp.py</setting>
```

---

## 11. Pygubuなし（純粋Tkinter）の場合

Pygubuを使わずに手書きする場合も、同じデザイントークンとパターンを適用：

```python
import tkinter as tk
import tkinter.ttk as ttk
import ui.custom_styles_jp as custom_styles_jp

class MyApp:
    def __init__(self):
        self.root = tk.Tk()
        custom_styles_jp.setup_ttk_styles(self.root)
        
        self.root.title("My App by TOMOMI RESEARCH, INC.")
        self.root.geometry("1920x1080")
        
        self._build_ui()
    
    def _build_ui(self):
        # LabelFrameでセクションを区切る
        frame_mode = ttk.LabelFrame(
            self.root, text="Mode", style="custom.TLabelframe"
        )
        frame_mode.pack(expand=True, fill="both", padx=5, pady=5, side="top")
        
        # ボタンは primary.TButton / secondary.TButton
        btn = ttk.Button(
            frame_control, text="Start", style="primary.TButton"
        )
        btn.pack(expand=True, fill="both", padx=30, pady=5, side="top")
```

---

## 12. Toplevel サブパネル パターン

メインウィンドウに乗せるサブ機能（ヒストグラム分析、設定ダイアログ、ROI 設計など）は **独立 Toplevel** として実装する。Paddock の Phase 3b/3c/3d で確立：

```python
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class XxxPanel(tk.Toplevel):
    """独立 Toplevel 型のサブパネル。Apply は呼び出し元の callback へ。"""

    def __init__(self, master, *, <input_data>, on_apply=None, **kw):
        super().__init__(master)
        self.title(f"Xxx — <context>")
        self.geometry("1200x780")

        self._on_apply = on_apply  # 親ロジックへのコールバック
        # ... Tk変数初期化 ...

        self._build_layout()
        self._refresh()

    def _build_layout(self):
        # ヘッダ説明
        ttk.Label(self, text="...", wraplength=1160, justify="left",
                  style="custom.TLabel").pack(side="top", fill="x",
                                               padx=10, pady=(8, 4))

        # メイン領域（matplotlib / 画像 / table）
        chart = ttk.LabelFrame(self, text="Preview",
                                style="custom.TLabelframe")
        chart.pack(side="top", fill="both", expand=True, padx=10, pady=4)
        self._build_chart(chart)

        # コントロール群（LabelFrame で区切る）
        ctl = ttk.LabelFrame(self, text="Controls",
                              style="custom.TLabelframe")
        ctl.pack(side="top", fill="x", padx=10, pady=4)
        self._build_controls(ctl)

        # フッタ：Apply（primary）+ Close（secondary）を右寄せ
        footer = ttk.Frame(self, style="custom.TFrame")
        footer.pack(side="bottom", fill="x", padx=10, pady=8)
        ttk.Button(footer, text="Close", style="secondary.TButton",
                    command=self.destroy).pack(side="right", padx=4)
        ttk.Button(footer, text="Apply", style="primary.TButton",
                    command=self._do_apply).pack(side="right", padx=4)

    def _do_apply(self):
        payload = {...}  # パネルの state を収集
        try:
            if self._on_apply is not None:
                self._on_apply(payload)
        finally:
            self.destroy()


def open_xxx_panel(master, **kw):
    """シンプルな module-level エントリポイント。呼び出し元が直接 XxxPanel
    を import するより、この関数経由で開くと後日の実装差し替えが楽。"""
    return XxxPanel(master, **kw)
```

**ルール:**
- Toplevel は**親ウィンドウを触らない**。state 変更は `on_apply` 経由で親に戻すだけ。
- `matplotlib` を埋め込む場合は `FigureCanvasTkAgg` + `pack(fill="both", expand=True)`、Figure は `tight_layout()` してから `get_tk_widget()` を呼ぶ。
- Apply ボタンは `primary.TButton`、Close は `secondary.TButton`。右寄せフッタ。
- 閉じるルートが複数ある場合（× ボタン + Close ボタン）は `protocol("WM_DELETE_WINDOW", self._dismiss)` で 1 箇所に集約。

---

## 13. バックグラウンドワーカー + Tk 安全な post パターン

ML 学習・推論・ファイル I/O は**すべてバックグラウンド スレッドで走らせる**。ワーカーは Tk ウィジェットに**直接触らない** — メインスレッドに callback を回す：

```python
import threading

class GuiXxxLogic(GuiXxxUi):

    def on_click_heavy_action(self):
        """UI イベントハンドラ。ボタン即 disable → スレッド起動。"""
        self._lock_buttons()
        try:
            self.progressbar.start(12)
        except Exception:
            pass
        self.label_stage.configure(text="running...")
        threading.Thread(target=self._worker_heavy, daemon=True).start()

    def _worker_heavy(self):
        """バックグラウンド スレッド。Tk ウィジェットは直接触らない。
        進捗と完了はすべて self._post() でメインスレッドに回す。"""
        try:
            n = len(self.files)
            def _p(done, total):
                self._post(lambda d=done, t=total: self.label_stage.configure(
                    text=f"progress {d}/{t}"
                ))

            result = do_heavy_work(self.files, progress_cb=_p)
            self._post(lambda: self._on_heavy_done(result))
        except Exception as e:
            import traceback
            err = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            self._post(lambda: self._on_run_error("heavy_action", err))

    def _on_heavy_done(self, result):
        """メインスレッド callback。ここでのみウィジェットを触る。"""
        try:
            self.progressbar.stop()
        except Exception:
            pass
        self._refresh_button_states()
        # ... 結果を UI に反映 ...

    def _post(self, fn):
        """Tk メインスレッドへ callable を schedule。"""
        try:
            self.root.after(0, fn)
        except Exception:
            pass
```

**ルール:**
- ワーカーは必ず `daemon=True`（メインウィンドウが閉じても残らない）。
- progress callback も `_post` 経由。ワーカーから `label.configure()` を直接呼ぶと競合でクラッシュする。
- `try/except/traceback.format_exc()` でエラーを包み、`_on_run_error` 経由でダイアログ表示。ワーカー内で握り潰さない。
- ラムダで state をキャプチャするときは **デフォルト引数イディオム** (`lambda d=done: ...`) を使う — クロージャが後で評価されるので直接 `lambda: d` だと値が変わる。

---

## 14. Wizard ステージマシン + 任意ステージスキップ

チューニング／セットアップを複数ステップで案内するアプリ（Paddock 等）は、**StageMachine を独立モジュール化**して Logic 層から参照する：

```python
# src/xxx_state.py
STAGES = [
    "load_data",
    "required_step",
    "optional_step",       # ← 任意
    "next_required",
    "another_optional",    # ← 任意
    "export",
    "done",
]

STAGE_LABEL = {
    "load_data":        "[1/7] Load Data",
    "required_step":    "[2/7] Required",
    "optional_step":    "[3/7] Optional",
    ...
}


class StageMachine:
    def __init__(self):
        self.current = "load_data"
        self.best_run_id = None
        self.best_config = None
        self.stage_history = []

    def advance(self):
        idx = STAGES.index(self.current)
        if idx + 1 < len(STAGES):
            self.current = STAGES[idx + 1]

    def finalize_stage(self, stage, run_ids, decision):
        """stage を完了としてマーク。decision は advance/skip/redo 等。"""
        self.stage_history.append({
            "stage": stage, "run_ids": list(run_ids), "decision": decision,
        })

    def is_enabled(self, stage):
        """そのステージの主ボタンが live か。"""
        return stage == self.current
```

**任意ステージのスキップ有効化** — Logic 層側：

```python
def _refresh_button_states(self):
    sm = self.stage_machine

    def enable_for(btn, stage, also_stages=()):
        """stage が current、もしくは current が also_stages のどれかなら
        有効化。つまり任意ステージに居るときは次の必須ステージのボタンも
        live になる → ユーザーがスキップできる。"""
        allow = sm.is_enabled(stage) or any(sm.current == s for s in also_stages)
        btn.state(["!disabled"] if allow else ["disabled"])

    enable_for(self.button_required,       "required_step")
    enable_for(self.button_optional,       "optional_step")
    # optional_step に居るときも next_required ボタンを live に
    enable_for(self.button_next_required,  "next_required",
                also_stages=("optional_step",))
    enable_for(self.button_export,         "export",
                also_stages=("optional_step", "another_optional"))
```

スキップされたステージは、次の必須ステージの `on_click` で `finalize_stage(..., decision="skipped")` + `advance()` を呼ぶと正しい履歴が残る。

---

## 15. 既知の落とし穴

### 15.1 numpy 配列の truthiness（定番）

DatasetLoader など多くの TR 社内 API は file-path 配列を `numpy.ndarray` で返す。これを `if arr:` / `arr or []` のような**真偽値評価で使うと `ValueError: The truth value of an array with more than one element is ambiguous`** で落ちる。

```python
# ❌ ダメ
for p in (files_train or []):          # numpy.ndarray がここで bool 評価される
    ...
if files_test:                          # 同じエラー
    ...

# ✅ 明示的に長さチェック
if files_train is not None and len(files_train) > 0:
    for p in files_train:
        ...
if isinstance(files_test, dict):
    for cat, paths in files_test.items():
        if paths is None or len(paths) == 0:
            continue
        ...
```

Phase 3a と Phase 3d で**同じ人が 2 回踏んだ**。新規ヘルパを書くときは必ず `is None` + `len() == 0` の 2 段チェック。

### 15.2 Cython `.pyd` + PyInstaller spec の動的 import

`src/gui_xxx.py` を `.pyd` にコンパイルすると PyInstaller Analysis は import 連鎖を追えなくなる（Cython がバイトコードから import を消すため）。さらに内部パッケージ（`tr_e3engine` 等）自体が `.pyd` 群のとき、その中の動的 import は**ダブルで不可視**。

```python
# spec ファイル内 — 必ず collect_all を使う
from PyInstaller.utils.hooks import collect_all

# ❌ ダメ — submodule 名だけ登録され、実体 .py/.pyd はバンドルされない
_hiddenimports += collect_submodules("torchinfo")

# ✅ 正解 — datas + binaries + hiddenimports を一括収集
# 戻り値の順番は (datas, binaries, hiddenimports) — 間違えると Analysis が
# re.search で TypeError になる
for _pkg in ("tr_e3engine", "tr_utils", "torchinfo", "albumentations"):
    d, b, m = collect_all(_pkg)
    _datas += d
    _binaries += b
    _hiddenimports += m
```

新しい動的 dep で `.exe` 起動時に `ModuleNotFoundError` が出たら、**その dep を `_dyn_pkg` ループに追加して再ビルド**するのが定石。`collect_submodules` だけで解決しようとしない。

### 15.3 ImageTk.PhotoImage の GC

```python
# ❌ ダメ — ローカル変数はメソッド終了と同時に GC され、画像が消える
def _show_logo(self):
    img = Image.open("logo.png")
    photo = ImageTk.PhotoImage(img)
    ttk.Label(self.root, image=photo).pack()

# ✅ インスタンス属性で持つ
def _show_logo(self):
    img = Image.open("logo.png")
    self._logo_photo = ImageTk.PhotoImage(img)  # ← self.xxx に退避
    ttk.Label(self.root, image=self._logo_photo).pack()
```

matplotlib の Figure や cv2 の VideoCapture も同じ — **Tk メインループが参照を保持しない** オブジェクトはすべて `self.xxx` に退避する。

---

## テンプレート・リファレンスファイル

| ファイル | 用途 |
|---------|------|
| `templates/custom_styles_jp.py` | ttk スタイル定義モジュール（そのままコピーして使用） |
| `templates/base_app.py` | 新規アプリの雛形コード |
| `references/design_tokens.md` | カラー・フォント・余白の詳細仕様 |
| `assets/TR_inc_logo.png` | 会社ロゴ画像 |

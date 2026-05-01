#!/usr/bin/python3
"""TOMOMI RESEARCH GUI Application Template.

This module provides a base template for creating new Tkinter/ttk GUI
applications following the TOMOMI RESEARCH design system.

Usage:
    1. Copy this file and rename to gui_{your_app}.py
    2. Copy ui/ folder (custom_styles_jp.py, TR_inc_logo.png) into your project
    3. Customize _build_control_tab() and _build_configure_tab()
    4. Add business logic methods

Author: TOMOMI RESEARCH, INC.
"""

import pathlib
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from PIL import Image, ImageTk

# --- Path resolution (PyInstaller compatible) ---
if getattr(sys, 'frozen', False):
    _temp_path = pathlib.Path(sys._MEIPASS)
else:
    _temp_path = pathlib.Path(__file__).parent

PROJECT_PATH = _temp_path
UI_PATH = PROJECT_PATH / "ui"

# --- Import TOMOMI styles ---
sys.path.insert(0, str(PROJECT_PATH))
try:
    from ui import custom_styles_jp
except ImportError:
    import custom_styles_jp


# ============================================================
# UI Layer (widget definitions only)
# ============================================================
class BaseAppUI:
    """UI layer: creates widgets, binds variables, connects callbacks.

    Subclass this to add business logic. Do NOT put hardware or
    processing code here.
    """

    WINDOW_TITLE = "My App by TOMOMI RESEARCH, INC."
    WINDOW_GEOMETRY = "1200x800"
    COPYRIGHT_YEAR = 2025

    def __init__(self, master=None):
        # --- Root or Toplevel ---
        if master is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)

        # --- Apply TOMOMI styles FIRST ---
        self.pack_layout = custom_styles_jp.setup_ttk_styles(self.root)

        # --- Window settings ---
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_GEOMETRY)

        # Icon (optional)
        ico_path = PROJECT_PATH / "favicon_TR100.ico"
        if ico_path.exists():
            self.root.iconbitmap(str(ico_path))

        # --- Build UI ---
        self._build_main_layout()

    # ----------------------------------------------------------
    # Main layout
    # ----------------------------------------------------------
    def _build_main_layout(self):
        """Build the top-level paned layout."""

        # Horizontal PanedWindow: left=content, right=control
        self.paned_main = ttk.Panedwindow(self.root, orient="horizontal")
        self.paned_main.pack(expand=True, fill="both", side="top")

        # --- Left pane (content area) ---
        self.frame_content = ttk.Frame(self.paned_main)
        self.paned_main.add(self.frame_content, weight=5)
        self._build_content_area(self.frame_content)

        # --- Right pane (control panel) ---
        self.frame_sidebar = ttk.Frame(self.paned_main)
        self.paned_main.add(self.frame_sidebar, weight=1)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.frame_sidebar)
        self.notebook.pack(side="top", fill="both", expand=True)

        # Tab 1: Control
        self.tab_control = ttk.Frame(self.notebook, style="custom.TFrame")
        self.notebook.add(self.tab_control, text="Control")
        self._build_control_tab(self.tab_control)

        # Tab 2: Configure
        self.tab_configure = tk.Frame(self.notebook)
        self.notebook.add(self.tab_configure, text="Configure")
        self._build_configure_tab(self.tab_configure)

    # ----------------------------------------------------------
    # Content area (left pane) — Override in subclass
    # ----------------------------------------------------------
    def _build_content_area(self, parent):
        """Build the main content area (left pane).

        Override this method to add canvases, image displays, etc.
        """
        self.canvas_main = tk.Canvas(parent)
        self.canvas_main.pack(expand=True, fill="both", side="top")

    # ----------------------------------------------------------
    # Control tab (right pane)
    # ----------------------------------------------------------
    def _build_control_tab(self, parent):
        """Build the Control tab with logo, sections, buttons, copyright."""

        # --- Logo ---
        logo_frame = ttk.Frame(parent, style="custom.TFrame")
        logo_frame.pack(side="top", fill="x")
        self._place_logo(logo_frame)

        # --- Sections (customize these) ---
        self._build_mode_section(parent)

        # --- Control buttons ---
        frame_ctrl = ttk.LabelFrame(
            parent, text="Control", style="custom.TLabelframe"
        )
        frame_ctrl.pack(
            expand=True, fill="both", padx=5, pady=5, side="top"
        )

        btn_start = ttk.Button(
            frame_ctrl, text="Start", style="primary.TButton",
            command=self.on_start
        )
        btn_start.pack(
            expand=True, fill="both", padx=30, pady=5, side="top"
        )

        btn_quit = ttk.Button(
            frame_ctrl, text="Quit", style="primary.TButton",
            command=self.on_quit
        )
        btn_quit.pack(
            expand=True, fill="both", padx=30, pady=5, side="top"
        )

        # --- Copyright ---
        frame_copy = ttk.Frame(parent, style="custom.TFrame")
        frame_copy.pack(side="top", fill="x")
        lbl_copy = ttk.Label(
            frame_copy,
            text=f"(C) {self.COPYRIGHT_YEAR} TOMOMI RESEARCH, INC.",
            style="custom.TLabelframe.Label"
        )
        lbl_copy.pack(
            anchor="center", expand=True, fill="both", padx=5, side="top"
        )

    def _build_mode_section(self, parent):
        """Example: Mode selection section. Override to customize."""
        frame_mode = ttk.LabelFrame(
            parent, text="Mode", style="custom.TLabelframe"
        )
        frame_mode.pack(
            expand=True, fill="both", padx=5, pady=5, side="top"
        )

        self.mode_var = tk.StringVar(value="option1")
        for text, val in [("Option 1", "option1"), ("Option 2", "option2")]:
            rb = ttk.Radiobutton(
                frame_mode, text=text, value=val,
                variable=self.mode_var,
                style="custom.TRadiobutton"
            )
            rb.pack(
                expand=True, fill="both", padx=10, side="top"
            )

    # ----------------------------------------------------------
    # Configure tab — Override in subclass
    # ----------------------------------------------------------
    def _build_configure_tab(self, parent):
        """Build the Configure tab with sliders and entries.

        Uses grid layout: Label(col=0), Widget(col=1 weight=1).
        """
        parent.columnconfigure(1, weight=1)

        # Example: a slider setting
        ttk.Label(
            parent, text="Parameter [unit]", style="custom.TLabel"
        ).grid(row=0, column=0, padx=5, sticky="ew")

        self.param_var = tk.IntVar(value=100)
        ttk.LabeledScale(
            parent, variable=self.param_var, from_=0, to=1000
        ).grid(row=0, column=1, padx=5, sticky="ew")

    # ----------------------------------------------------------
    # Logo helper
    # ----------------------------------------------------------
    def _place_logo(self, parent):
        """Load and display the TOMOMI RESEARCH logo."""
        logo_path = UI_PATH / "TR_inc_logo.png"
        if logo_path.exists():
            img = Image.open(logo_path)
            self._logo_photo = ImageTk.PhotoImage(img)
            lbl = ttk.Label(
                parent, image=self._logo_photo, style="custom.TLabel"
            )
            lbl.pack(expand=True, fill="x", side="top")

    # ----------------------------------------------------------
    # Callbacks (override in subclass)
    # ----------------------------------------------------------
    def on_start(self):
        """Handle Start button click."""
        print("✅ Start clicked")

    def on_quit(self):
        """Handle Quit button click."""
        self.root.destroy()

    # ----------------------------------------------------------
    # Run
    # ----------------------------------------------------------
    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


# ============================================================
# Logic Layer (business logic)
# ============================================================
class BaseApp(BaseAppUI):
    """Logic layer: extends UI with business logic.

    Override on_start(), on_quit(), and add custom methods here.
    """

    WINDOW_TITLE = "My App by TOMOMI RESEARCH, INC."
    COPYRIGHT_YEAR = 2025

    def __init__(self, master=None):
        super().__init__(master)
        # Initialize hardware, processing pipelines, etc.

    def on_start(self):
        """Override: implement your start logic."""
        print("✅ BaseApp.on_start() — override me!")
        messagebox.showinfo("Info", "Start pressed")


# ============================================================
# Entry point
# ============================================================
if __name__ == "__main__":
    app = BaseApp()
    app.run()

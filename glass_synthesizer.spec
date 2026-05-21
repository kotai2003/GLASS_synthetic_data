# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec -- GLASS Synthesizer, Cython-protected ONEDIR build.

NOT --onefile (project requirement). Driven by build_all.py, which has
already produced a staging tree where every protected module is a compiled
`.pyd` and the original `.py` source has been deleted:

    build_cython_stage/
        glass_app.py                 <- thin launcher (only readable source)
        synthesize_gui/
            __init__.py              <- trivial glue, kept as source
            gui_main.cp39-*.pyd      <- compiled
            core/  ... *.pyd
            ui/    ... *.pyd + assets (png/ico)

Because the `.pyd` modules are opaque to PyInstaller's import scanner, this
spec collects the staged package explicitly (every .pyd as a binary at its
package-relative path, every remaining .py / asset as data) instead of
relying on modulegraph following imports into the compiled blobs.

Build (invoked by build_all.py):
    python -m PyInstaller glass_synthesizer.spec --noconfirm
"""
import os

from PyInstaller.utils.hooks import (
    collect_all, collect_submodules, copy_metadata,
)

SPEC_DIR = SPECPATH                                   # .../01.GLASS (OneDrive)
# build_all.py builds OUTSIDE OneDrive and passes the staging dir via env
# (OneDrive sync locks files in a multi-GB tree -> PyInstaller WinError 5).
STAGE = os.environ.get(
    "GLASS_STAGE_DIR", os.path.join(SPEC_DIR, "build_cython_stage"))
STAGE_PKG = os.path.join(STAGE, "synthesize_gui")
ENTRY = os.path.join(STAGE, "glass_app.py")
# EXE icon: take it from the repo (always present) not the stage.
EXE_ICON = os.path.join(SPEC_DIR, "synthesize_gui", "ui", "app_icon.ico")

if not os.path.isdir(STAGE_PKG):
    raise SystemExit(
        "Staging tree not found. Run build_all.py (it creates "
        "build_cython_stage/ and compiles the .pyd before PyInstaller)."
    )

# ---- Collect the staged, compiled package explicitly --------------------
binaries = []
datas = []
hiddenimports = []
ASSET_EXT = (".png", ".ico", ".jpg", ".jpeg", ".gif")

for root, _dirs, files in os.walk(STAGE_PKG):
    rel_dir = os.path.relpath(root, STAGE)            # e.g. synthesize_gui/ui
    for fn in files:
        src = os.path.join(root, fn)
        ext = os.path.splitext(fn)[1].lower()
        if ext == ".pyd":
            binaries.append((src, rel_dir))
            # Register the dotted module name so it is importable.
            mod = os.path.splitext(fn)[0].split(".")[0]
            dotted = rel_dir.replace(os.sep, ".")
            if fn != "__init__.pyd":
                dotted = f"{dotted}.{mod}"
            hiddenimports.append(dotted)
        elif ext == ".py" or ext in ASSET_EXT:
            datas.append((src, rel_dir))              # __init__.py + assets
        # .c / .pyc / build leftovers are intentionally NOT shipped.

hiddenimports += [
    "PIL.ImageTk", "PIL._tkinter_finder",
    # The protected UI .pyd modules import these; opaque to the scanner.
    "tkinter", "tkinter.ttk", "tkinter.filedialog",
    "tkinter.messagebox", "tkinter.font",
]

# ---- Heavy / hook-sensitive third-party deps, pulled in wholesale -------
for pkg in ("torch", "torchvision", "imgaug", "skimage", "scipy"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += collect_submodules("cv2")

# Several deps call importlib.metadata.version(...) at import time (imgaug ->
# imageio is the one that crashed: PackageNotFoundError: imageio). collect_all
# does NOT ship .dist-info metadata, so copy it explicitly (recursive picks up
# their dependency chains too).
for pkg in ("imageio", "imgaug", "scikit-image", "scipy", "numpy",
            "Pillow", "networkx", "tifffile", "lazy_loader",
            "PyWavelets"):
    try:
        datas += copy_metadata(pkg, recursive=True)
    except Exception:
        pass  # not all are present on every machine; skip cleanly

excludes = [
    "pytest", "IPython", "notebook", "pandas.tests",
    "synthesize_gui.tests", "synthesize_gui.ui._make_icon",
]

a = Analysis(
    [ENTRY],
    pathex=[STAGE],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,            # ONEDIR
    name="GLASS_Synthesizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                    # GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=EXE_ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GLASS_Synthesizer",
)

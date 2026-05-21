#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_all.py -- GLASS Synthesizer full build pipeline (TOMOMI standard).

Mirrors FORESIGHT VIEWER TR-100's build_all.py, adapted for a multi-module
package using an isolated staging tree.

  Step 1  Stage + Cython : copy synthesize_gui/ -> build_cython_stage/,
                            compile every protected .py -> .pyd, then delete
                            the .py source from the stage (repo is untouched).
  Step 2  PyInstaller     : freeze the staged (compiled) tree via
                            glass_synthesizer.spec  (ONEDIR, not --onefile).
  Step 3  Verification    : exe present; .pyd present in dist; NO protected
                            .py / readable source leaked into dist;
                            .pyd import smoke test; exe launches & stays
                            alive 5 s.

Run from 01.GLASS/ with the GLASS conda interpreter:

    "C:/Users/seong/anaconda3/envs/GLASS/python.exe" build_all.py
"""
import importlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # repo (under OneDrive)
SRC_PKG = BASE_DIR / "synthesize_gui"

SPEC_FILE = BASE_DIR / "glass_synthesizer.spec"
SETUP_CYTHON = BASE_DIR / "setup_cython.py"
STARTER = BASE_DIR / "glass_app.py"
ISS_FILE = BASE_DIR / "glass_synthesizer_setup.iss"
ISCC_CANDIDATES = (
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
)

APP_NAME = "GLASS_Synthesizer"

# All heavy build I/O goes OUTSIDE OneDrive. The repo lives under a synced
# OneDrive folder; OneDrive grabs transient handles on files in a multi-GB
# output tree, which intermittently breaks PyInstaller's COLLECT with
# `PermissionError: [WinError 5]`. Building to a plain local dir avoids it.
# Override with the GLASS_BUILD_ROOT env var if C:\ is not desired.
BUILD_ROOT = Path(os.environ.get("GLASS_BUILD_ROOT", r"C:\TR_build\GLASS"))
STAGE = BUILD_ROOT / "build_cython_stage"
STAGE_PKG = STAGE / "synthesize_gui"
WORK_DIR = BUILD_ROOT / "build"                     # PyInstaller --workpath
DIST_ROOT = BUILD_ROOT / "dist"                     # PyInstaller --distpath
DIST_DIR = DIST_ROOT / APP_NAME
INTERNAL = DIST_DIR / "_internal"
EXE_FILE = DIST_DIR / f"{APP_NAME}.exe"
INSTALLER_DIR = BUILD_ROOT / "installer"            # ISCC OutputDir (in .iss)

# Dev-only things never copied into the stage.
COPY_IGNORE = shutil.ignore_patterns(
    "tests", "_make_icon.py", "__pycache__", "*.pyc", "*.pyd", "*.c",
    "build", "*.so",
)
# Modules that MUST end up compiled (no .py for these anywhere in dist).
PROTECTED_BASENAMES = {
    "synthesis.py", "exporter.py", "io_utils.py", "perlin.py",
    "gui_main.py", "gui_main_ui.py", "custom_styles_jp.py",
}


def header(msg: str) -> None:
    print(f"\n{'=' * 64}\n  {msg}\n{'=' * 64}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


# ----------------------------------------------------------------------
# Step 1: Stage + Cython
# ----------------------------------------------------------------------
def step1_stage_and_cython() -> None:
    header("Step 1: Stage + Cython (.py -> .pyd)")

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    shutil.copytree(SRC_PKG, STAGE_PKG, ignore=COPY_IGNORE)
    shutil.copy2(STARTER, STAGE / STARTER.name)
    shutil.copy2(SETUP_CYTHON, STAGE / SETUP_CYTHON.name)
    print(f"[OK] staged -> {STAGE}")

    cmd = [sys.executable, SETUP_CYTHON.name, "build_ext", "--inplace"]
    if subprocess.run(cmd, cwd=str(STAGE)).returncode != 0:
        fail("Cython build failed")

    # Verify a .pyd exists for every protected module, then strip the source.
    stripped = []
    missing = []
    for py in list(STAGE_PKG.rglob("*.py")):
        if py.name == "__init__.py":
            continue
        pyd = next(iter(py.parent.glob(py.stem + ".*.pyd")), None)
        if pyd is None:
            missing.append(str(py.relative_to(STAGE)))
            continue
        py.unlink()
        stripped.append(py.name)
    # Also remove generated C sources from the stage.
    for c in STAGE_PKG.rglob("*.c"):
        c.unlink()

    if missing:
        fail("No .pyd produced for: " + ", ".join(missing))
    print(f"[OK] compiled & stripped {len(stripped)} modules: "
          f"{', '.join(sorted(stripped))}")


# ----------------------------------------------------------------------
# Step 2: PyInstaller
# ----------------------------------------------------------------------
def step2_pyinstaller() -> None:
    header("Step 2: PyInstaller (ONEDIR via glass_synthesizer.spec)")

    if not SPEC_FILE.exists():
        fail(f"spec not found: {SPEC_FILE}")

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC_FILE),
           "--noconfirm", "--clean",
           "--distpath", str(DIST_ROOT),
           "--workpath", str(WORK_DIR)]
    # Tell the spec where the (out-of-OneDrive) staging tree is.
    env = dict(os.environ, GLASS_STAGE_DIR=str(STAGE))
    if subprocess.run(cmd, cwd=str(BASE_DIR), env=env).returncode != 0:
        fail("PyInstaller build failed")
    if not EXE_FILE.exists():
        fail(f"EXE not produced: {EXE_FILE}")
    print(f"[OK] built {EXE_FILE}")


# ----------------------------------------------------------------------
# Step 3: Verification
# ----------------------------------------------------------------------
def step3_verify() -> None:
    header("Step 3: Post-build Verification")
    errors = []

    print("\n--- 3-1: artifact presence ---")
    if not EXE_FILE.exists():
        errors.append(f"EXE missing: {EXE_FILE}")
    else:
        print(f"[OK] {EXE_FILE.name}")
    dist_pkg = INTERNAL / "synthesize_gui"
    if not dist_pkg.is_dir():
        errors.append(f"package dir missing in dist: {dist_pkg}")
    else:
        print(f"[OK] {dist_pkg.relative_to(DIST_DIR)}/ present")

    print("\n--- 3-2: .pyd present for every protected module ---")
    pyds = {p.name.split(".")[0] for p in INTERNAL.rglob("*.pyd")
            if p.name.split(".")[0] + ".py" in PROTECTED_BASENAMES}
    expected = {b[:-3] for b in PROTECTED_BASENAMES}
    missing_pyd = sorted(expected - pyds)
    if missing_pyd:
        errors.append("protected modules with no .pyd in dist: "
                       + ", ".join(missing_pyd))
    else:
        print(f"[OK] all {len(expected)} protected modules shipped as .pyd")

    print("\n--- 3-3: NO protected source leaked into dist ---")
    # Scope strictly to OUR bundled package -- third-party deps (e.g.
    # torch/onnx/_internal/exporter.py) legitimately reuse these basenames
    # and must not be mistaken for a leak.
    leaks = []
    if dist_pkg.is_dir():
        for ext in ("*.py", "*.pyc", "*.c"):
            for f in dist_pkg.rglob(ext):
                stem = f.name.split(".")[0]
                if f.name == "__init__.py" or f.name.startswith("__init__."):
                    continue  # trivial glue, intentionally kept as source
                if stem + ".py" in PROTECTED_BASENAMES:
                    leaks.append(str(f.relative_to(DIST_DIR)))
    if leaks:
        errors.append("readable source for protected modules in dist: "
                       + ", ".join(leaks))
    else:
        print("[OK] no protected .py/.pyc/.c found in dist")

    print("\n--- 3-4: .pyd import smoke test ---")
    probe = INTERNAL / "synthesize_gui" / "core" / "synthesis.pyd"
    cand = list((INTERNAL / "synthesize_gui" / "core").glob("synthesis.*.pyd"))
    if not cand:
        errors.append("synthesis .pyd not found for import test")
    else:
        code = (
            "import sys; sys.path.insert(0, r'%s'); "
            "import synthesize_gui.core.synthesis as s; "
            "print('synthesize_one' , hasattr(s,'synthesize_one'))"
            % str(INTERNAL)
        )
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True)
        if r.returncode != 0 or "synthesize_one True" not in r.stdout:
            errors.append("synthesis.pyd import failed:\n"
                           + r.stdout + r.stderr)
        else:
            print("[OK] synthesis.pyd imports, synthesize_one present")

    print("\n--- 3-5: EXE launch (no crash within 8 s) ---")
    # NOTE: this is a windowed (console=False) build. If startup raises, the
    # PyInstaller bootloader pops an "Unhandled exception" dialog and the
    # process STAYS ALIVE -- so "still running" is NOT proof of success.
    # We must inspect stderr for crash markers regardless of liveness.
    err_path = BASE_DIR / "_exe_launch_stderr.txt"
    try:
        with open(err_path, "wb") as ferr:
            proc = subprocess.Popen([str(EXE_FILE)],
                                    stdout=subprocess.DEVNULL,
                                    stderr=ferr,
                                    cwd=str(DIST_DIR))
            time.sleep(8)
        early_exit = proc.poll() is not None
        rc = proc.returncode
        if proc.poll() is None:                       # app OR error dialog
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        try:
            stderr_txt = err_path.read_text("utf-8", errors="replace")
        except Exception:
            stderr_txt = ""
        CRASH_MARKERS = (
            "Traceback (most recent call last)", "ModuleNotFoundError",
            "ImportError", "PackageNotFoundError",
            "Failed to execute script", "Unhandled exception",
        )
        hit = next((m for m in CRASH_MARKERS if m in stderr_txt), None)
        if early_exit and rc not in (0, None):
            errors.append("EXE exited early (code %s). stderr:\n%s"
                          % (rc, stderr_txt[:1200]))
            print("[NG] EXE exited early")
        elif hit:
            errors.append("EXE crashed on launch (%s). stderr:\n%s"
                          % (hit, stderr_txt[:1200]))
            print(f"[NG] EXE crashed on launch ({hit})")
        else:
            print("[OK] EXE launched, no crash markers in stderr (8 s)")
    except Exception as e:
        errors.append(f"EXE launch failed: {e}")
    finally:
        try:
            err_path.unlink()
        except Exception:
            pass

    print(f"\n{'=' * 64}")
    if errors:
        print(f"  BUILD VERIFICATION FAILED ({len(errors)} error(s))")
        print('=' * 64)
        for e in errors:
            print(f"  [FAIL] {e}")
        sys.exit(1)
    print("  BUILD VERIFICATION PASSED -- ALL CHECKS OK")
    print('=' * 64)


# ----------------------------------------------------------------------
# Step 4: Inno Setup installer (optional -- skipped cleanly if ISCC absent)
# ----------------------------------------------------------------------
def step4_installer() -> None:
    header("Step 4: Inno Setup installer (ISCC)")

    iscc = next((p for p in ISCC_CANDIDATES if os.path.isfile(p)), None)
    if iscc is None:
        print("[SKIP] ISCC.exe not found (Inno Setup 6 not installed). "
              "Installer not built; the ONEDIR dist is still complete.")
        return
    if not ISS_FILE.exists():
        fail(f"iss script not found: {ISS_FILE}")

    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [iscc, str(ISS_FILE)]
    if subprocess.run(cmd, cwd=str(BASE_DIR)).returncode != 0:
        fail("Inno Setup compilation failed")

    setups = sorted(INSTALLER_DIR.glob("GLASS_Synthesizer_Setup*.exe"))
    if not setups:
        fail(f"installer .exe not produced in {INSTALLER_DIR}")
    total_mb = sum(f.stat().st_size for f in INSTALLER_DIR.glob("*")) / 1e6
    print(f"[OK] installer: {setups[0]}")
    print(f"[OK] installer set size: {total_mb:.0f} MB "
          f"({len(list(INSTALLER_DIR.glob('*')))} file(s) incl. .bin spans)")


def main() -> None:
    print("GLASS Synthesizer -- Cython-protected full build pipeline")
    print(f"Base: {BASE_DIR}")
    step1_stage_and_cython()
    step2_pyinstaller()
    step3_verify()
    step4_installer()
    print(f"\nDone. Distributable: {DIST_DIR}")
    print(f"Installer dir:   {INSTALLER_DIR}")


if __name__ == "__main__":
    main()

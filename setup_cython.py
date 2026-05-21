"""
Cython build for the GLASS Synthesizer (TOMOMI standard, FORESIGHT-style).

This file is COPIED into the staging tree by build_all.py and run there as:

    python setup_cython.py build_ext --inplace

It compiles every protected module of the `synthesize_gui` package
(everything except the package `__init__.py` glue) from `.py` into a native
`.pyd`, so the shipped product carries no readable Python source for the
synthesis algorithm or UI logic. Reverse-engineering is then as hard as
disassembling a C extension instead of trivially decompiling a `.pyc`.

`__init__.py` files are intentionally left as plain Python: they contain only
import wiring (no algorithm), and keeping them as source guarantees correct
package resolution while the siblings load from their `.pyd`.

Run location: the staging copy of the project (cwd == staging root, so the
glob below sees `synthesize_gui/...`). Never run against the repo working
tree -- build_all.py isolates this in build_cython_stage/.
"""
import glob
import os

from setuptools import setup
from Cython.Build import cythonize

PKG = "synthesize_gui"

# Every .py under the package except the __init__.py glue.
sources = [
    p for p in glob.glob(os.path.join(PKG, "**", "*.py"), recursive=True)
    if os.path.basename(p) != "__init__.py"
]
sources.sort()

print("[setup_cython] modules to compile:")
for s in sources:
    print(f"  - {s}")

setup(
    name="glass_synthesizer_protected",
    ext_modules=cythonize(
        sources,
        compiler_directives={
            "language_level": "3",
            # Drop docstrings from the compiled binary -- a little extra
            # opacity, and the end product has no use for them.
            "embedsignature": False,
        },
        # Keep each module its own extension (preserve package layout /
        # relative imports); do not merge into one blob.
        force=True,
        quiet=False,
    ),
)

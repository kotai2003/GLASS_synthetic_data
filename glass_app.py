"""
GLASS Synthesizer launcher (PyInstaller entry point) -- TOMOMI standard.

This is the ONLY first-party `.py` that ships as readable source, and it
contains no IP: it just (1) imports every third-party dependency and every
protected `synthesize_gui` submodule by name so PyInstaller's import scanner
bundles them -- the compiled `.pyd` modules are opaque to that scanner, so
their imports must be declared somewhere it can see -- and (2) hands off to
the real (compiled) entry point.

Mirrors FORESIGHT's gui_starter_fast.py role.
"""
# --- Stdlib GUI: the compiled .pyd UI modules import these, but PyInstaller
#     cannot scan inside a .pyd, so they must be declared here to be bundled.
import tkinter
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.font

# --- Third-party deps the compiled modules pull in at runtime -------------
import cv2
import imgaug
import imgaug.augmenters
import numpy as np
import PIL.Image
import PIL.ImageTk
import PIL._tkinter_finder
import torch
import torchvision
from torchvision import transforms
import skimage
import scipy

# --- Protected (Cython-compiled) submodules, named so they get bundled ----
import synthesize_gui
import synthesize_gui.core
import synthesize_gui.core.synthesis
import synthesize_gui.core.exporter
import synthesize_gui.core.io_utils
import synthesize_gui.core._vendored
import synthesize_gui.core._vendored.perlin
import synthesize_gui.ui
import synthesize_gui.ui.custom_styles_jp
import synthesize_gui.ui.gui_main_ui
import synthesize_gui.gui_main


def main() -> None:
    synthesize_gui.gui_main.main()


if __name__ == "__main__":
    main()

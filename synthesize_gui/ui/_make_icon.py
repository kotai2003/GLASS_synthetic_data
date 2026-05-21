"""
App-icon generator (asset utility, NOT a unit test — underscore-prefixed so
`unittest discover` skips it).

Produces the window / taskbar icon for the GLASS Synthesizer:

    synthesize_gui/ui/app_icon.ico   (multi-res 16..256, used by iconbitmap)
    synthesize_gui/ui/app_icon.png   (256px, iconphoto fallback)

Design language (matches the TOMOMI RESEARCH logo + ttk theme):
  - Rounded-square tile, diagonal navy -> cornflower-blue gradient
  - Bold white "G" monogram (GLASS), Segoe UI Black
  - A small glowing organic blob ringed by a thin outline in the lower-right:
    the product story in one mark -- a synthesized NG defect + its mask.

Re-run after changing the brand colors:
    python -m synthesize_gui.ui._make_icon
"""
from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_HERE = pathlib.Path(__file__).parent
ICO_PATH = _HERE / "app_icon.ico"
PNG_PATH = _HERE / "app_icon.png"

# Brand palette: deep navy -> vivid azure (keys off the TOMOMI cornflower
# blue but pushed richer/cooler for a sharper app-tile look).
NAVY = np.array([18, 30, 66], dtype=np.float32)         # #121E42  top-left
CORN = np.array([74, 138, 255], dtype=np.float32)       # #4A8AFF  bottom-right

SS = 4                      # supersampling factor for crisp anti-aliasing
SIZE = 256
S = SIZE * SS


def _gradient(s: int) -> Image.Image:
    """Smooth top-left -> bottom-right diagonal gradient."""
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    t = ((xx + yy) / (2.0 * (s - 1)))[..., None]        # 0..1 diagonal
    rgb = (NAVY * (1.0 - t) + CORN * t).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def _rounded_mask(s: int, radius: int) -> Image.Image:
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], radius, fill=255)
    return m


def _load_font(px: int) -> ImageFont.FreeTypeFont:
    for name in ("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", px)
        except OSError:
            continue
    return ImageFont.load_default()


def build() -> Image.Image:
    tile = _gradient(S).convert("RGBA")

    # Restrained top-left sheen for depth (kept subtle so the gradient
    # stays rich rather than washing out).
    hi = Image.new("L", (S, S), 0)
    ImageDraw.Draw(hi).ellipse([-S * 0.45, -S * 0.85, S * 0.95, S * 0.35],
                               fill=30)
    hi = hi.filter(ImageFilter.GaussianBlur(S * 0.07))
    tile = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)),
                           tile, hi)

    draw = ImageDraw.Draw(tile)

    # "G" monogram, optically centered.
    font = _load_font(int(S * 0.64))
    box = draw.textbbox((0, 0), "G", font=font)
    gw, gh = box[2] - box[0], box[3] - box[1]
    gx = (S - gw) / 2 - box[0]
    gy = (S - gh) / 2 - box[1] - S * 0.015
    # whisper-soft shadow (low alpha, tight offset -> no double edge)
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((gx, gy + S * 0.012), "G", font=font,
                            fill=(8, 16, 38, 110))
    tile = Image.alpha_composite(tile, sh.filter(
        ImageFilter.GaussianBlur(S * 0.012)))
    draw = ImageDraw.Draw(tile)
    draw.text((gx, gy), "G", font=font, fill=(255, 255, 255, 255))

    # Synthesized-defect mark: a bright cyan glow + organic blob ringed by a
    # thin "mask" outline -- the product story (synthetic NG + mask) in one
    # accent, tucked into the G's lower-right opening.
    cx, cy, r = S * 0.665, S * 0.695, S * 0.082
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse([cx - r * 2.6, cy - r * 2.6,
                                  cx + r * 2.6, cy + r * 2.6], fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.035))
    tile = Image.composite(Image.new("RGBA", (S, S), (120, 224, 255, 255)),
                           tile, glow)
    draw = ImageDraw.Draw(tile)
    # irregular blob with a faint cyan core->white look
    pts = [(cx + r * 1.05, cy - r * 0.55), (cx + r * 0.45, cy - r * 1.15),
           (cx - r * 0.65, cy - r * 0.85), (cx - r * 1.1, cy + r * 0.1),
           (cx - r * 0.45, cy + r * 1.05), (cx + r * 0.7, cy + r * 0.95),
           (cx + r * 1.15, cy + r * 0.25)]
    draw.polygon(pts, fill=(255, 255, 255, 255))
    # crisp thin mask ring
    draw.ellipse([cx - r * 1.85, cy - r * 1.85, cx + r * 1.85, cy + r * 1.85],
                 outline=(225, 246, 255, 255), width=max(2, int(S * 0.013)))

    # Round the corners.
    mask = _rounded_mask(S, int(S * 0.225))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(tile, (0, 0), mask)

    return out.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    icon = build()
    icon.save(PNG_PATH)
    icon.save(ICO_PATH, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                               (64, 64), (128, 128), (256, 256)])
    print(f"[make_icon] wrote {ICO_PATH}")
    print(f"[make_icon] wrote {PNG_PATH}")


if __name__ == "__main__":
    main()

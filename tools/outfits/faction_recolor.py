"""Recolours the Murim Robes' colour maps for the three Murim factions.

The robes' design, folds, embroidery and every other map (normal, roughness, metalness) stay exactly
as they are: only the colour maps are remapped, so a faction's robe is the same garment in its own
colours. Each pixel is split softly into four kinds, then each kind is put through its own colour ramp
by its brightness, so the folds, stitching and speckle of the original survive:

    cloth   the white robe, sleeves, cuffs and pearls
    coat    the gold brocade coat, belt band, embroidery and trims (including their brown shading)
    gem     the turquoise pendant
    dark    the black collar, trousers, boots and soles
    (pure black, the unused part of each sheet, is left as it is)

    blender -b --python tools/outfits/faction_recolor.py

Writes assets/outfits/factions/<Faction>/MurimOutfit_<Piece>_color.png and a contact sheet per faction
under renders/factions/ (local). Runs headless in Blender, which carries the numpy this needs.
"""
import os
import sys

import bpy
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "assets", "outfits")
OUT = os.path.join(ROOT, "assets", "outfits", "factions")
SHEETS = os.path.join(ROOT, "renders", "factions")

PIECES = ["Belt", "LeftBoot", "LeftCuff", "LeftShoe", "LeftSleeve", "LeftTrouser", "RightBoot",
          "RightCuff", "RightShoe", "RightSleeve", "RightTrouser", "Skirt", "Torso"]


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


# Each ramp: three stops, dark -> mid -> light, in display (sRGB-encoded) colour.
FACTIONS = {
    # Righteous, disciplined: white and azure with silver. Gold becomes sapphire, the gem ice.
    "Orthodox": {
        "cloth": ("#5f7497", "#c9d8ee", "#fbfdff"),
        "coat":  ("#0a1f4a", "#2a62bd", "#8cc4ff"),
        "gem":   ("#3a7fa6", "#9fe3ff", "#f2fdff"),
        "dark":  ("#05070d", "#141b2c", "#2b3752"),
    },
    # Independent, unconventional: linen and deep teal-green with copper. Gold becomes forest teal.
    "Unorthodox": {
        "cloth": ("#6b6a52", "#cbc6a4", "#f2eed6"),
        "coat":  ("#06241d", "#1b7058", "#62d1a0"),
        "gem":   ("#8a3a0c", "#ee8a2e", "#ffd9a0"),
        "dark":  ("#060907", "#171f1a", "#2c3a31"),
    },
    # Overwhelming, feared: ink-black cloth with crimson. Gold becomes blood red, the gem an ember.
    "Demonic": {
        "cloth": ("#040304", "#17131a", "#322a38"),
        "coat":  ("#1c0205", "#780b15", "#cc2c26"),
        "gem":   ("#7a1d04", "#ff6a1a", "#ffd27a"),
        "dark":  ("#020102", "#0c0809", "#1e1214"),
    },
}


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rc = np.where(nz, (mx - r) / np.where(nz, d, 1), 0)
    gc = np.where(nz, (mx - g) / np.where(nz, d, 1), 0)
    bc = np.where(nz, (mx - b) / np.where(nz, d, 1), 0)
    h = np.where(mx == r, bc - gc, np.where(mx == g, 2.0 + rc - bc, 4.0 + gc - rc))
    h = (h / 6.0) % 1.0
    h = np.where(nz, h, 0)
    s = np.where(mx > 1e-6, d / np.where(mx > 1e-6, mx, 1), 0)
    return h, s, mx


def smooth(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(stops, t):
    """Three-stop ramp over t in 0..1."""
    a, b, c = (hexc(s) for s in stops)
    t = np.clip(t, 0, 1)[..., None]
    lo = a + (b - a) * np.clip(t * 2, 0, 1)
    hi = b + (c - b) * np.clip(t * 2 - 1, 0, 1)
    return np.where(t < 0.5, lo, hi)


def classify(rgb):
    h, s, v = rgb_to_hsv(rgb)
    hue = h * 360.0
    gem = smooth(0.30, 0.45, s) * smooth(140, 160, hue) * (1 - smooth(205, 225, hue))
    coat = smooth(0.16, 0.32, s) * smooth(18, 30, hue) * (1 - smooth(62, 78, hue)) * (1 - gem)
    cloth = (1 - smooth(0.07, 0.16, s)) * smooth(0.55, 0.75, v) * (1 - gem) * (1 - coat)
    dark = np.clip(1 - gem - coat - cloth, 0, 1)
    total = gem + coat + cloth + dark
    return {"gem": gem / total, "coat": coat / total, "cloth": cloth / total, "dark": dark / total}, v


# The brightness range each kind spans in the original, so a ramp uses its whole length.
RANGE = {"cloth": (0.45, 0.96), "coat": (0.12, 0.86), "gem": (0.35, 0.95), "dark": (0.0, 0.34)}


def recolor(rgb, palette):
    weights, v = classify(rgb)
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    out = np.zeros_like(rgb)
    for kind, w in weights.items():
        lo, hi = RANGE[kind]
        t = (lum - lo) / (hi - lo)
        out += ramp(palette[kind], t) * w[..., None]
    # the sheets' unused black stays black, so seams bleed exactly as before
    keep = smooth(0.0, 0.05, v)[..., None]
    return rgb * (1 - keep) + out * keep


def load(path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3].copy(), w, h


def save(path, rgb, w, h):
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def contact_sheet(faction, sheet_path, shown=("Torso", "Skirt", "LeftSleeve", "Belt", "LeftTrouser", "LeftBoot")):
    """Original and recoloured, side by side, at 256 px: for the owner's approval before any upload."""
    cell = 256
    cols = len(shown)
    sheet = np.zeros((cell * 2, cell * cols, 3), dtype=np.float32)
    for i, piece in enumerate(shown):
        for row, folder in enumerate((SRC, os.path.join(OUT, faction))):
            rgb, w, h = load(os.path.join(folder, f"MurimOutfit_{piece}_color.png"))
            step = w // cell
            small = rgb.reshape(cell, step, cell, step, 3).mean(axis=(1, 3))
            sheet[(1 - row) * cell:(2 - row) * cell, i * cell:(i + 1) * cell] = small
    os.makedirs(os.path.dirname(sheet_path), exist_ok=True)
    save(sheet_path, sheet, cell * cols, cell * 2)


def main():
    only = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(FACTIONS)
    for faction in only:
        palette = {kind: stops for kind, stops in FACTIONS[faction].items()}
        os.makedirs(os.path.join(OUT, faction), exist_ok=True)
        for piece in PIECES:
            rgb, w, h = load(os.path.join(SRC, f"MurimOutfit_{piece}_color.png"))
            save(os.path.join(OUT, faction, f"MurimOutfit_{piece}_color.png"), recolor(rgb, palette), w, h)
        contact_sheet(faction, os.path.join(SHEETS, f"{faction}_colours.png"))
        print("done", faction)


main()

"""Reassembles the banner from title_pieces.py's images, the way the game places them, and checks the seams. Needs Pillow and numpy.

    python title_assemble.py <pieces folder> <out png> [--length 4.2] [--tier 4] [--tint 1.0 0.72 0.35]

length: the plate's length between its two ends, in units (the game: the title's words plus padding). The placing (all from pieces.json, nothing guessed):
  the mid strip, stretched sideways, spans the plate minus 0.4 units under each end stub (so the stubs cover its cut ends);
  each cap sits with its plate END at -length/2 or +length/2, offset by its recorded left/top; the crown sits at the middle; each light layer is tinted
  (white-hot where it is strongest, the tint round it) and drawn over its steel.
It then compares the metal's colour either side of each seam (where a cap's stub meets the mid strip), on the rim rows: the step must be under 8/255,
or the join would show in the game. Exit code 1 when it is not.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

folder, out = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
LENGTH = float(args[args.index("--length") + 1]) if "--length" in args else 4.2
TIER = int(args[args.index("--tier") + 1]) if "--tier" in args else 4
TINT = tuple(float(v) for v in args[args.index("--tint") + 1:args.index("--tint") + 4]) if "--tint" in args else (1.0, 0.72, 0.35)
meta = json.load(open(os.path.join(folder, "pieces.json")))
P, PX = meta["pieces"], meta["pxPerUnit"]
W, H = int(LENGTH * PX + 1800), 800
cx, cy = W // 2, H // 2
canvas = Image.new("RGBA", (W, H), (14, 16, 36, 255))
steel_only = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # the metal alone, for the seam check


def image(piece, layer, tinted=False, size=None):
    img = Image.open(os.path.join(folder, "title_tier%d_%s_%s.png" % (TIER, piece, layer))).convert("RGBA")
    if size:
        img = img.resize(size, Image.LANCZOS)
    if tinted:
        a = np.asarray(img, dtype=np.float32) / 255
        hot = np.clip((a[..., 3] - 0.55) / 0.45, 0, 1)[..., None]
        rgb = np.array(TINT)[None, None, :] * (1 - hot) + hot
        img = Image.fromarray((np.dstack((rgb, a[..., 3])) * 255).astype(np.uint8), "RGBA")
    return img


xe = {"capL": cx - LENGTH / 2 * PX, "capR": cx + LENGTH / 2 * PX}
mid_w = int(round(LENGTH * PX - 0.8 * PX))
placed = [("mid", cx - mid_w / 2, cy + P["mid"]["top"], (mid_w, P["mid"]["height"])),
          ("capL", xe["capL"] + P["capL"]["left"], cy + P["capL"]["top"], None),
          ("capR", xe["capR"] + P["capR"]["left"], cy + P["capR"]["top"], None),
          ("crown", cx + P["crown"]["left"], cy + P["crown"]["top"], None)]
for piece, x, y, size in placed:
    img = image(piece, "steel", size=size)
    canvas.alpha_composite(img, (int(round(x)), int(round(y))))
    steel_only.alpha_composite(img, (int(round(x)), int(round(y))))
for piece, x, y, size in placed:
    if P[piece]["light"]:
        canvas.alpha_composite(image(piece, "light", tinted=True), (int(round(x)), int(round(y))))
canvas.convert("RGB").save(out)

# the seams: on the rim rows (the gold rim's visible edge, 0.395 units from the middle), the metal just left of a cap's stub-end against just right of it,
# ten pixels each side; averaged over the opaque pixels
metal = np.asarray(steel_only, dtype=np.float32) / 255.0


def mean_colour(row, x0, x1):
    window = metal[row - 2:row + 3, x0:x1]
    weight = window[..., 3:4]
    return (window[..., :3] * weight).sum(axis=(0, 1)) / max(float(weight.sum()), 1e-6)


bad = 0
for side, name in ((1, "capL"), (-1, "capR")):
    boundary = int(round(xe[name] + side * 0.8 * PX))  # the stub's inner end
    for row_name, row in (("top rim", cy - int(0.395 * PX)), ("bottom rim", cy + int(0.395 * PX))):
        left, right = mean_colour(row, boundary - 12, boundary - 2), mean_colour(row, boundary + 2, boundary + 12)
        step = float(np.abs(left - right).max())
        ok = step < 8 / 255
        bad += 0 if ok else 1
        print("  %s  %s %-10s step %.1f/255" % ("PASS" if ok else "FAIL", name, row_name, step * 255))
print("%d seam check(s) failed" % bad)
sys.exit(1 if bad else 0)

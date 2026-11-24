"""Cuts title_banner.py's piece renders into the game's images. Needs Pillow and numpy.

    python title_pieces.py <render folder> <out folder> [--tier 4] [--cap-length 2.0]

For each of capL, capR, mid and crown (the renders title_tier<N>_<piece>_steel.png / _light.png): composes the light pass into the white, tintable glow
layer (title_compose.py), crops both layers to the piece's content, and writes <out>/title_tier<N>_<piece>_{steel,light}.png and <out>/pieces.json:
the size of each image and where it sits, in pixels (200 to a unit of the art; the plate is 0.7 units high) from the art's origin: the plate's middle
for the mid strip and the crown, the plate's END for a cap (its left end, -cap-length/2, or its right, +cap-length/2). The game places each piece from
these numbers, so none is guessed. A light layer with nothing in it (the mid strip's) is not written. Every image must be 1024 px or less on both sides:
that is what Roblox keeps of an upload.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

folder, out = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
TIER = int(args[args.index("--tier") + 1]) if "--tier" in args else 4
CAP_LENGTH = float(args[args.index("--cap-length") + 1]) if "--cap-length" in args else 2.0
PX = 200
LIMIT = 1024
os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))

pieces = {}
for piece in ("capL", "capR", "mid", "crown"):
    name = "title_tier%d_%s" % (TIER, piece)
    subprocess.run([sys.executable, "-I", os.path.join(here, "title_compose.py"), folder, name], check=True, stdout=subprocess.DEVNULL)
    steel = Image.open(os.path.join(folder, name + "_steel.png")).convert("RGBA")
    light = Image.open(os.path.join(folder, name + "_light.png")).convert("RGBA")
    alpha = np.maximum(np.asarray(steel)[..., 3], np.asarray(light)[..., 3])
    ys, xs = np.where(alpha > 2)
    left, right, top, bottom = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
    box = (left, top, right, bottom)
    width, height = right - left, bottom - top
    assert width <= LIMIT and height <= LIMIT, "%s is %dx%d: over Roblox's %d px" % (piece, width, height, LIMIT)
    W, H = steel.size
    origin_x = W / 2 + (-CAP_LENGTH / 2 * PX if piece == "capL" else CAP_LENGTH / 2 * PX if piece == "capR" else 0)
    steel.crop(box).save(os.path.join(out, name + "_steel.png"))
    has_light = bool(np.asarray(light)[..., 3].max() > 2)
    if has_light:
        light.crop(box).save(os.path.join(out, name + "_light.png"))
    pieces[piece] = {"width": width, "height": height, "left": round(left - origin_x, 1), "top": round(top - H / 2, 1), "light": has_light}
    print("%-6s %4d x %-4d  from the origin: x %+7.1f  y %+7.1f  light %s" % (piece, width, height, pieces[piece]["left"], pieces[piece]["top"], has_light))
with open(os.path.join(out, "pieces.json"), "w") as f:
    json.dump({"pxPerUnit": PX, "plateHeightUnits": 0.7, "capLengthUnits": CAP_LENGTH, "pieces": pieces}, f, indent=2)
print("wrote", os.path.join(out, "pieces.json"))

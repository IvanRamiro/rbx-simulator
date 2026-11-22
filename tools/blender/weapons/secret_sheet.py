"""A review sheet of the three faction secret weapons side by side, at one scale, each on its faction's colours (run headless
after the three have been exported):

    blender -b --factory-startup --python tools/blender/weapons/secret_sheet.py

Writes renders/faction_weapons/faction_weapons_sheet.png (local, never committed): the flat view the player sees on top, a
three-quarter view below.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402
import secret_lab as L  # noqa: E402
import secret_review as R  # noqa: E402

V = Vector
FACTIONS = (("SecretOrthodox", (0.04, 0.1, 0.24), (0.62, 0.78, 0.96)),
            ("SecretUnorthodox", (0.02, 0.09, 0.075), (0.16, 0.33, 0.27)),
            ("SecretDemonic", (0.02, 0.0, 0.008), (0.3, 0.03, 0.045)))


def backdrop(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    img = np.zeros((h, w, 4), dtype=np.float32)
    img[..., :3] = np.array(bottom) * (1 - t) + np.array(top) * t
    xs = np.linspace(-1, 1, w)[None, :, None]
    img[..., :3] *= 1.0 - 0.35 * xs ** 2          # a soft vignette
    img[..., 3] = 1.0
    return img


def run():
    rows = {"flat": [], "angle": []}
    for wid, top, bottom in FACTIONS:
        SK.fresh()
        body, glows = R.load_game(wid, SK.OUT_DIR)
        mine = [body] + glows
        L.lab()
        lo, hi = L.bounds(mine)
        centre = (lo + hi) / 2
        for key, view, ortho, size in (("flat", "top", True, (480, 960)), ("angle", "front34", False, (480, 960))):
            tile = L.shoot(mine, view, size=size, samples=64, ortho=ortho, centre=V((0, centre.y, 0.25)), span=12.0 if ortho else 12.5)
            bg = backdrop(size[0], size[1], top, bottom)
            a = tile[..., 3:4]
            bg[..., :3] = tile[..., :3] * a + bg[..., :3] * (1 - a)
            rows[key].append(bg)
    sheet = L.sheet(rows["flat"] + rows["angle"], 3, pad=6)
    out = os.path.join(SK.REVIEW, "faction_weapons_sheet.png")
    print("sheet:", L.save_png(sheet, out))


if __name__ == "__main__":
    run()

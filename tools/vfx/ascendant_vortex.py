"""Realm 5's golden vortex portal (the owner, 2026-11-03: "a vortex portal with a chain ... the chain
is inside the fast swirling golden portal"). Our own textures; each carries its own colour
(white-hot to the owner's gold 255,170,40 to amber), so its emitter's Color is white.

    python3 ascendant_vortex.py assets/aura/ascendant     (needs Pillow and numpy)

  GoldVortex.png      1024  seven spiral arms winding into the centre, brightest where they
                            converge, a ring of light at the rim, fading at the edge; a clear
                            hole at the very centre (a dark core particle sits there)
  GoldVortexArms.png  1024  three looser, broader arms, softer: the second layer turning the other way
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
N = 1024
yy, xx = np.mgrid[0:N, 0:N].astype(float)
X = (xx - N / 2) / (N * 0.46)
Y = (yy - N / 2) / (N * 0.46)
RAD = np.hypot(X, Y)
ANG = np.arctan2(Y, X)


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(img, r):
    return np.asarray(Image.fromarray(np.clip(img * 64, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), dtype=float) / 64


def colourise(i):
    white = np.array([255, 245, 215], dtype=float)
    gold = np.array([255, 170, 40], dtype=float)
    amber = np.array([200, 95, 15], dtype=float)
    lo = np.clip(i / 0.55, 0, 1)[..., None]
    hot = np.clip((i - 0.8) / 0.7, 0, 1)[..., None]
    rgb = amber * (1 - lo) + gold * lo
    rgb = rgb * (1 - hot) + white * hot
    return np.dstack([np.clip(rgb, 0, 255), np.clip(i, 0, 1) * 255]).astype(np.uint8)


def vortex(arms, wind, sharp, rim, hole):
    lr = np.log(np.maximum(RAD, 1e-3))
    phase = ANG * arms + wind * lr                        # logarithmic spiral arms
    band = (0.5 + 0.5 * np.cos(phase)) ** sharp
    radial = smooth(1.0, 0.55, RAD) * (0.35 + 0.9 * smooth(0.9, 0.15, RAD))
    i = band * radial
    i += rim * np.exp(-((RAD - 0.9) / 0.03) ** 2)        # a ring of light at the rim
    i *= smooth(hole * 0.6, hole, RAD)                    # the hole at the centre
    i = i + blur(i, 5) * 0.6 + blur(i, 18) * 0.35
    return i * smooth(1.02, 0.96, RAD)


Image.fromarray(colourise(vortex(7, 5.5, 6, 0.6, 0.14) * 1.1)).save(os.path.join(OUT, "GoldVortex.png"))
Image.fromarray(colourise(vortex(3, -3.5, 3, 0.0, 0.1) * 0.75)).save(os.path.join(OUT, "GoldVortexArms.png"))

# a preview of both on a dark ground
tiles = []
for n in ("GoldVortex.png", "GoldVortexArms.png"):
    a = np.asarray(Image.open(os.path.join(OUT, n)), dtype=float)
    al = a[..., 3:] / 255
    bg = np.array([12, 18, 40], dtype=float)
    tiles.append(np.clip(bg * (1 - al) + a[..., :3] * al * 1.2, 0, 255).astype(np.uint8))
Image.fromarray(np.hstack(tiles)).save(os.path.join(OUT, "GoldVortex_preview.png"))
print("written")

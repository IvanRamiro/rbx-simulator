"""Realm 5's golden chain (the owner, 2026-11-03: "a chain ... attached to both hands ... pulled
into the portal"; their picks 15938396604 and 9462760467 showed as a hairline on a beam, so this one
is ours). Drawn for a Beam: the length runs top to bottom (a Beam maps a texture's vertical along
its length), the links fill the full width, and the tile repeats seamlessly (TextureMode Wrap).

One tile holds a link seen face-on (an oval ring) and a link seen edge-on (a bar through it), as a
real chain alternates. Each is a metal tube: shaded across its section with a bright highlight and a
dark rim, warm gold to deep amber, so the Beam's Color is white.

    python3 ascendant_chain.py assets/aura/ascendant     (needs Pillow and numpy)

  GoldChain.png  256x512 RGBA
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SS = 4
W, H = 256 * SS, 512 * SS
yy, xx = np.mgrid[0:H, 0:W].astype(float)
cx = W / 2
TUBE = 22 * SS                # the tube's half thickness

GOLD_HI = np.array([255, 244, 200], dtype=float)
GOLD = np.array([245, 170, 50], dtype=float)
GOLD_LO = np.array([120, 60, 10], dtype=float)


def shade(d):
    """d: distance from the tube's centreline (0 at the centre, 1 at its edge) -> colour and alpha"""
    a = np.clip(1 - d, 0, 1)
    s = np.sqrt(np.clip(1 - d * d, 0, 1))                  # the round section
    light = np.clip(0.35 + 0.65 * s, 0, 1) ** 1.2
    hi = np.exp(-((d - 0.25) / 0.18) ** 2)                 # a highlight a little off centre
    col = GOLD_LO * (1 - light[..., None]) + GOLD * light[..., None]
    col = col * (1 - hi[..., None] * 0.8) + GOLD_HI * hi[..., None] * 0.8
    return col, (d < 1).astype(float) * np.clip((1 - d) * 6, 0, 1)


rgb = np.zeros((H, W, 3))
alpha = np.zeros((H, W))


def paint(col, al, over=True):
    global rgb, alpha
    m = al[..., None]
    rgb = rgb * (1 - m) + col * m
    alpha = np.maximum(alpha, al) if not over else alpha * (1 - al) + al


# the edge-on links: a vertical rounded bar centred at y = 3/4 of the tile, and its wrap at -1/4
for cy in (0.75 * H, -0.25 * H, 1.75 * H):
    half = 0.3 * H
    dy = np.clip(np.abs(yy - cy) - (half - TUBE), 0, None)
    d = np.hypot(xx - cx, dy) / TUBE
    col, al = shade(d)
    paint(col, al)

# the face-on link: an oval ring centred at y = 1/4 (drawn over the bars, which pass behind it)
for cy in (0.25 * H, 1.25 * H):
    rx, ry = 0.3 * W, 0.3 * H
    # distance to the ellipse's centreline, approximately, scaled to the tube
    q = np.hypot((xx - cx) / rx, (yy - cy) / ry)
    grad = np.hypot((xx - cx) / rx ** 2, (yy - cy) / ry ** 2) + 1e-6
    d = np.abs(q - 1) / grad / TUBE * np.maximum(q, 1e-6)
    col, al = shade(d)
    paint(col, al)

img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8)).resize((256, 512), Image.LANCZOS)
img.save(os.path.join(OUT, "GoldChain.png"))
# a preview: three tiles stacked on a dark ground, to check the seam
a = np.asarray(img, dtype=float)
tile = np.vstack([a, a, a])
al = tile[..., 3:] / 255
bg = np.array([12, 18, 40], dtype=float)
Image.fromarray(np.clip(bg * (1 - al) + tile[..., :3] * al, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "GoldChain_preview.png"))
print("written")

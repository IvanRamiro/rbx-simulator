"""Realm 5's golden lightning for the cloud above the head (the owner's spec, 2026-11-03: "sudden,
intermittent electrical strikes ... blinding electric gold-white"). Our own: four different
branching bolts in a 2x2 sheet (FlipbookStartRandom picks one per strike, so no two look alike),
each a jagged main channel from midpoint displacement with forks, a white-hot core and a soft glow,
inside a clear margin so neighbouring cells never bleed in. White on transparent: tinted in game.

    python3 ascendant_lightning.py assets/aura/ascendant     (needs Pillow and numpy)

  GoldLightning.png  1024x1024 (2x2 cells of 512)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
# review boards go to renders/aura (git-ignored), never beside the uploaded textures
PREVIEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "renders", "aura")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
SS = 2
CELL = 512 * SS
rng = np.random.default_rng(1105)


def bolt(p0, p1, rough, depth):
    """midpoint displacement: a jagged path from p0 to p1"""
    pts = [np.array(p0, float), np.array(p1, float)]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2
            d = b - a
            n = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-9)
            m = m + n * rng.normal(0, rough * np.hypot(*d))
            new += [m, b]
        pts = new
    return pts


def draw_cell(d, ox, oy):
    m = CELL * 0.12                                  # the clear margin
    span = CELL - 2 * m
    a = rng.uniform(0, math.tau)
    c = np.array([ox + CELL / 2, oy + CELL / 2])
    r = span / 2
    p0 = c + r * np.array([math.cos(a), math.sin(a)])
    p1 = c - r * np.array([math.cos(a + rng.uniform(-0.5, 0.5)), math.sin(a + rng.uniform(-0.5, 0.5))])
    main = bolt(p0, p1, 0.2, 5)            # few, sharp zigzags (7 levels read as a squiggle)
    d.line([tuple(p) for p in main], fill=255, width=7 * SS, joint="curve")
    # forks off the main channel, thinner, and a second order on some
    for _ in range(rng.integers(3, 6)):
        i = rng.integers(len(main) // 6, len(main) * 5 // 6)
        start = main[i]
        direction = main[min(i + 4, len(main) - 1)] - main[max(i - 4, 0)]
        ang = math.atan2(direction[1], direction[0]) + rng.choice([-1, 1]) * rng.uniform(0.4, 1.1)
        length = r * rng.uniform(0.3, 0.6)
        end = start + length * np.array([math.cos(ang), math.sin(ang)])
        end = np.clip(end, [ox + m, oy + m], [ox + CELL - m, oy + CELL - m])
        fork = bolt(start, end, 0.22, 4)
        d.line([tuple(p) for p in fork], fill=210, width=4 * SS, joint="curve")
        if rng.random() < 0.6:
            j = rng.integers(len(fork) // 3, len(fork))
            ang2 = ang + rng.choice([-1, 1]) * rng.uniform(0.4, 1.0)
            end2 = fork[j] + length * 0.45 * np.array([math.cos(ang2), math.sin(ang2)])
            end2 = np.clip(end2, [ox + m, oy + m], [ox + CELL - m, oy + CELL - m])
            d.line([tuple(p) for p in bolt(fork[j], end2, 0.28, 4)], fill=160, width=2 * SS, joint="curve")


L = Image.new("L", (CELL * 2, CELL * 2), 0)
d = ImageDraw.Draw(L)
for k in range(4):
    draw_cell(d, (k % 2) * CELL, (k // 2) * CELL)
core = np.asarray(L, dtype=float) / 255
glow = np.asarray(L.filter(ImageFilter.GaussianBlur(10 * SS)), dtype=float) / 255
wide = np.asarray(L.filter(ImageFilter.GaussianBlur(28 * SS)), dtype=float) / 255
a = np.clip(core + glow * 1.6 + wide * 0.9, 0, 1)
img = Image.fromarray((a * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
rgba = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
rgba.putalpha(img)
rgba.save(os.path.join(OUT, "GoldLightning.png"))
prev = np.asarray(img, dtype=float)[..., None] / 255
bg = np.array([12, 18, 40], dtype=float)
Image.fromarray(np.clip(bg * (1 - prev) + np.array([255, 245, 190]) * prev, 0, 255).astype(np.uint8)).save(os.path.join(PREVIEWS, "GoldLightning_preview.png"))
print("written")

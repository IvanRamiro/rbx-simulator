"""Realm 5's yin and yang (the owner, 2026-11-03: "Replace the heavenly seal behind with a yin and
yang"): a luminous taijitu standing behind the head, turning slowly. Our own drawing, in the realm's
style: the yang half glows gold (white-hot toward its heart), the yin half is a deep smoky dark with
a faint gold sheen, the S-curve and the outline burn as lines of light, and a double ring with
glowing nodes frames it. No text, no trigrams: only the symbol and rings.

The texture carries its own colours and alpha (the dark half is opaque enough to read against the
sky), so its ImageColor3 is white.

    python3 ascendant_taiji.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantTaiji.png          1024x1024 RGBA
  AscendantTaiji_preview.png  on a dark ground, and on a sky blue (how it is seen in the day)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
N = 2048
TAU = math.tau
yy, xx = np.mgrid[0:N, 0:N].astype(float)
X = (xx - N / 2) / (N * 0.47)
Y = -(yy - N / 2) / (N * 0.47)          # y up
RAD = np.hypot(X, Y)
ANG = np.arctan2(Y, X)

S = 0.78                                 # the symbol's radius (the rings sit outside it)
x, y = X / S, Y / S
r = np.hypot(x, y)


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(img, rad):
    return np.asarray(Image.fromarray(np.clip(img * 64, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad)), dtype=float) / 64


px = 1.0 / (N * 0.47 * S)               # one pixel in symbol units
inside = smooth(1 + px * 2, 1 - px * 2, r)
top = np.hypot(x, y - 0.5)               # the upper bulb
bot = np.hypot(x, y + 0.5)               # the lower bulb
# yang: the right half, plus the upper bulb, minus the lower bulb (soft edges)
right = smooth(-px * 2, px * 2, x)
up_b = smooth(0.5 + px * 2, 0.5 - px * 2, top)
lo_b = smooth(0.5 + px * 2, 0.5 - px * 2, bot)
yang = np.clip(right * (1 - lo_b) + up_b, 0, 1)
# the eyes: a yin dot in the yang bulb, a yang dot in the yin bulb
yin_eye = smooth(0.15 + px * 2, 0.15 - px * 2, top)
yang_eye = smooth(0.15 + px * 2, 0.15 - px * 2, bot)
yang = np.clip(yang * (1 - yin_eye) + yang_eye, 0, 1) * inside
yin = inside * (1 - yang)

# lines of light: the outline and the S-curve (where yang meets yin inside the symbol)
edge = np.abs(np.gradient(yang)[0]) + np.abs(np.gradient(yang)[1])
edge = np.clip(edge * 6, 0, 1) * inside
outline = np.exp(-((r - 1) / 0.012) ** 2)
lines = np.clip(blur(edge, 2) * 1.6 + outline, 0, 1)

# the frame: a double ring, 16 ticks, 8 glowing nodes
frame = (np.exp(-((RAD - 0.9) / 0.008) ** 2) + np.exp(-((RAD - 0.95) / 0.004) ** 2) * 0.7)
tick = (np.cos(ANG * 16) > 0.985) * smooth(0.905, 0.915, RAD) * smooth(0.945, 0.935, RAD)
frame = np.clip(frame + tick * 0.8, 0, 1)
nodes = np.zeros_like(RAD)
for k in range(8):
    a = k * TAU / 8 + TAU / 16
    nodes += np.exp(-(((X - 0.925 * math.cos(a)) ** 2 + (Y - 0.925 * math.sin(a)) ** 2) / 0.0009))
nodes = np.clip(nodes, 0, 1)

# light: the yang half glows, brightest toward the middle of its body; lines, frame and nodes burn
yang_glow = yang * (0.55 + 0.35 * smooth(1.0, 0.2, r) + 0.15 * (0.5 + 0.5 * np.cos(r * 18)))
light = yang_glow * 0.85 + lines * 1.3 + frame * 1.1 + nodes * 1.5
light = light + blur(light, 8) * 0.5 + blur(light, 28) * 0.35

white = np.array([255, 245, 215], dtype=float)
gold = np.array([255, 170, 40], dtype=float)
amber = np.array([210, 100, 15], dtype=float)
lo = np.clip(light / 0.55, 0, 1)[..., None]
hot = np.clip((light - 0.85) / 0.8, 0, 1)[..., None]
glow_rgb = amber * (1 - lo) + gold * lo
glow_rgb = glow_rgb * (1 - hot) + white * hot

# yin: a deep, smoky dark with a faint gold sheen near its edge and swirling through it
swirl = 0.5 + 0.5 * np.cos(ANG * 3 + r * 7)
yin_rgb = np.array([22, 13, 8], dtype=float) + np.array([60, 35, 8], dtype=float) * (smooth(0.6, 1.0, r) * 0.6 + swirl * 0.15)[..., None]

la = np.clip(light, 0, 1)[..., None]
yin_a = (yin * 0.9)[..., None]
rgb = yin_rgb * yin_a * (1 - la) + glow_rgb * la
alpha = np.clip(yin_a[..., 0] * (1 - la[..., 0]) + la[..., 0], 0, 1)
rgb = rgb / np.maximum(alpha[..., None], 1e-4)
alpha *= smooth(1.02, 0.99, RAD)

img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
img.save(os.path.join(OUT, "AscendantTaiji.png"))
a = np.asarray(img, dtype=float)
al = a[..., 3:] / 255
tiles = []
for bg in (np.array([12, 18, 40], dtype=float), np.array([110, 170, 230], dtype=float)):
    tiles.append(np.clip(bg * (1 - al) + a[..., :3] * al, 0, 255).astype(np.uint8))
Image.fromarray(np.hstack(tiles)).save(os.path.join(OUT, "AscendantTaiji_preview.png"))
print("written")

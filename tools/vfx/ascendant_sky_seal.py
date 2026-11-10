"""The Heaven Seal: Realm 5's huge magic circle high above the head (the owner, 2026-11-03: "create a
huge magic CIRCLE ABOVE THE HEAD, like VERY high"). Luminous energy like the ground circle, but its
own design, so the two don't repeat: the ground circle is concentric rings; this one is a gate of
heaven seen from below.
  outer      a broad double ring burning white-hot, with 36 short rays radiating outward
  band       a ring of 12 small circles, each with a point of light, linked by arcs
  star       a twelve-pointed star polygon (each point joined to the fifth one on), lines of light
  inner      three thin rings, a wheel of 24 spokes between them
  heart      a sun: a bright disc in a ring, eight long rays
No text (the game's fixed directive): only rings, lines and points. The texture carries its own
colour, white-hot to the owner's gold (255,170,40) to amber, so its Color is white.

    python3 ascendant_sky_seal.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantSkySeal.png          1024x1024 RGBA
  AscendantSkySeal_preview.png  (renders/aura) on a dark ground
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
N = 2048
C = N / 2
R = N * 0.47
TAU = math.tau

L = Image.new("L", (N, N), 0)
d = ImageDraw.Draw(L)


def P(r, a):
    return (C + R * r * math.cos(a), C + R * r * math.sin(a))


def ring(r, w, v=255):
    d.ellipse([C - R * r, C - R * r, C + R * r, C + R * r], outline=v, width=int(w))


def line(a, b, w, v=255):
    d.line([a, b], fill=v, width=int(w))


# outer: double ring, rays outward
ring(0.97, 9)
ring(0.925, 4)
for k in range(36):
    a = k * TAU / 36
    long = k % 3 == 0
    line(P(0.975, a), P(1.0 if long else 0.99, a), 6 if long else 3, 220)
    if long:
        line(P(0.93, a), P(0.965, a), 3, 180)
# band: 12 small circles linked by arcs
ring(0.84, 3, 170)
for k in range(12):
    a = k * TAU / 12 + TAU / 24
    cx, cy = P(0.84, a)
    rr = R * 0.045
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=255, width=6)
    d.ellipse([cx - rr * 0.35, cy - rr * 0.35, cx + rr * 0.35, cy + rr * 0.35], fill=255)
ring(0.79, 5)
# star: {12/5}
pts = [P(0.79, k * TAU / 12 - math.pi / 2) for k in range(12)]
for k in range(12):
    line(pts[k], pts[(k + 5) % 12], 5, 210)
# inner: rings and a wheel of spokes
ring(0.5, 6)
ring(0.44, 3, 190)
ring(0.3, 5)
for k in range(24):
    a = k * TAU / 24
    line(P(0.31, a), P(0.43, a), 3 if k % 2 else 5, 200 if k % 2 else 240)
# heart: a sun
ring(0.16, 6)
for k in range(8):
    a = k * TAU / 8 + TAU / 16
    tip, b0, b1 = P(0.28, a), P(0.17, a - 0.12), P(0.17, a + 0.12)
    d.polygon([b0, tip, b1], fill=220)
d.ellipse([C - R * 0.1, C - R * 0.1, C + R * 0.1, C + R * 0.1], fill=255)

base = np.asarray(L, dtype=float) / 255
yy, xx = np.mgrid[0:N, 0:N].astype(float)
rad = np.hypot(xx - C, yy - C) / R
ang = np.arctan2(yy - C, xx - C)
# flicker along every line, a faint glow filling the disc, two bloom passes
flicker = 0.7 + 0.3 * (0.5 + 0.5 * np.cos(ang * 7 + rad * 9) * np.cos(ang * 3 - 1.3))
I = base * flicker
I += 0.07 * np.clip(1 - rad, 0, 1) ** 0.5 * (rad < 1)


def blur(img, r):
    return np.asarray(Image.fromarray(np.clip(img * 64, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), dtype=float) / 64


I = I + blur(I, 6) * 0.6 + blur(I, 24) * 0.4
I *= np.clip((1.04 - rad) / 0.04, 0, 1)

white = np.array([255, 245, 215], dtype=float)
gold = np.array([255, 170, 40], dtype=float)
amber = np.array([215, 100, 15], dtype=float)
lo = np.clip(I / 0.5, 0, 1)[..., None]
hot = np.clip((I - 0.75) / 0.8, 0, 1)[..., None]
rgb = amber * (1 - lo) + gold * lo
rgb = rgb * (1 - hot) + white * hot
alpha = np.clip(I * 1.05, 0, 1)
img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
img.save(os.path.join(OUT, "AscendantSkySeal.png"))
a = np.asarray(img, dtype=float)
bg = np.array([12, 18, 40], dtype=float)
al = a[..., 3:] / 255
Image.fromarray(np.clip(bg * (1 - al) + a[..., :3] * al * 1.3, 0, 255).astype(np.uint8)).save(os.path.join(PREVIEWS, "AscendantSkySeal_preview.png"))
print("written")

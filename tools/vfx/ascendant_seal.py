"""The Ascendant Seal: Realm 5's ground circle (the owner asked for "a better circle", 2026-11-03).
Our own, drawn line by line. White on transparent: the game tints it (the owner's gold 255,170,40).
No text in any language (the game's fixed directive): only rings, ticks, clouds and wings.

From the rim inward:
  a double rim, fine ticks between, a small diamond every 30 degrees;
  eight auspicious clouds (ruyi scrolls), the clouds an Ascendant rises on;
  a ring with sixteen beads;
  eight swallow wings pointing outward, climbing (the realm's Skyrise swallow);
  a ring of short sun rays round an open centre (the body stands there).

    python3 ascendant_seal.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantSeal.png  1024x1024
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SS = 4                        # drawn at 4x and reduced, for clean lines
W = 1024 * SS
C = W / 2
R = W * 0.47                  # radius 1.0; the image keeps a clear margin past it
TAU = math.tau

layer = Image.new("L", (W, W), 0)
d = ImageDraw.Draw(layer)


def px(r, a):
    """a point at radius r (0-1) and angle a"""
    return (C + R * r * math.cos(a), C + R * r * math.sin(a))


LINE = 1.35                   # every line a third thicker: at 5 studs across, thin lines shimmer away


def ring(r, width):
    d.ellipse([C - R * r, C - R * r, C + R * r, C + R * r], outline=255, width=int(width * LINE * SS))


def line(points, width):
    d.line(points, fill=255, width=int(width * LINE * SS), joint="curve")


def dot(p, radius):
    rr = radius * SS
    d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=255)


# --- the rim: two rings, fine ticks between, a diamond every 30 degrees --------------------
ring(0.985, 3.2)
ring(0.935, 2.0)
for k in range(120):
    a = k * TAU / 120
    long = k % 10 == 0
    line([px(0.94, a), px(0.98 if long else 0.962, a)], 2.2 if long else 1.3)
for k in range(12):
    a = k * TAU / 12
    pts = [px(0.985 + 0.03, a), px(0.96, a + 0.012), px(0.985 - 0.06, a), px(0.96, a - 0.012)]
    d.polygon(pts, fill=255)

# --- the clouds: eight ruyi scrolls on the band, lobes outward ------------------------------


def cloud(theta, r0, s):
    """one auspicious cloud at angle theta, centred at radius r0, size s (in radius units).
    Local u runs along the ring, v outward; two scrolls curl inward under a three-lobed crown,
    with a wisp trailing behind (all of it in the direction the seal turns)"""
    t = (-math.sin(theta), math.cos(theta))      # along the ring
    n = (math.cos(theta), math.sin(theta))       # outward

    def P(u, v):
        x = r0 * n[0] + s * (u * t[0] + v * n[0])
        y = r0 * n[1] + s * (u * t[1] + v * n[1])
        return (C + R * x, C + R * y)

    def spiral(cu, side):
        # from the crown's foot, curling inward round (cu, 0): 1.3 turns, the radius shrinking
        pts = []
        for i in range(80):
            k = i / 79
            ang = math.pi / 2 + side * k * TAU * 1.3
            rad = 0.42 * (1 - 0.78 * k)
            pts.append(P(cu + side * rad * math.cos(ang) * -1, rad * math.sin(ang)))
        return pts

    line(spiral(-0.5, 1), 2.6)
    line(spiral(0.5, -1), 2.6)
    # the crown: a big middle lobe between two small ones, over the scrolls
    crown = []
    for i in range(61):
        k = i / 60
        u = -0.5 + k
        v = 0.42 + 0.30 * math.sin(math.pi * k) + 0.07 * math.sin(3 * math.pi * k)
        crown.append(P(u, v))
    line(crown, 2.6)
    # a wisp trailing behind, thinning
    wisp = [P(-0.5 - 0.42 - 1.15 * k, -0.05 + 0.16 * math.sin(k * math.pi * 1.6) - 0.35 * k * k) for k in np.linspace(0, 1, 40)]
    line(wisp, 1.8)


for k in range(8):
    cloud(k * TAU / 8 + TAU / 16, 0.795, 0.15)

# --- a beaded ring --------------------------------------------------------------------------
ring(0.655, 2.0)
for k in range(16):
    dot(px(0.655, k * TAU / 16), 5.5 if k % 2 == 0 else 3.5)

# --- eight swallow wings, pointing outward ---------------------------------------------------


def wing(theta):
    """two swept wings meeting at a point outward, a forked tail inward: a swallow climbing"""
    def P(r, da):
        return px(r, theta + da)
    for side in (1, -1):
        outer = [P(0.62 - 0.17 * k, side * (0.0 + 0.16 * k ** 0.8)) for k in np.linspace(0, 1, 30)]
        line(outer, 2.4)
        inner = [P(0.555 - 0.10 * k, side * (0.0 + 0.085 * k ** 0.8)) for k in np.linspace(0, 1, 20)]
        line(inner, 1.6)
        tail = [P(0.50 - 0.07 * k, side * 0.03 * k) for k in np.linspace(0, 1, 12)]
        line(tail, 1.6)
    dot(P(0.62, 0), 4.5)


for k in range(8):
    wing(k * TAU / 8)

# --- sun rays round the open centre ----------------------------------------------------------
ring(0.36, 2.4)
ring(0.335, 1.2)
for k in range(32):
    a = k * TAU / 32
    line([px(0.37, a), px(0.405 if k % 2 == 0 else 0.388, a)], 1.6)

# --- glow under every line, then reduce ------------------------------------------------------
glow = layer.filter(ImageFilter.GaussianBlur(9 * SS)).point(lambda v: int(min(255, v * 1.5)))
alpha = np.maximum(np.asarray(layer, dtype=float), np.asarray(glow, dtype=float) * 0.55)
alpha = Image.fromarray(alpha.astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
rgba = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
rgba.putalpha(alpha)
rgba.save(os.path.join(OUT, "AscendantSeal.png"))

# a preview on a dark ground, in the owner's gold
a = np.asarray(alpha, dtype=float)[:, :, None] / 255
gold = np.array([255, 170, 40], dtype=float)
bg = np.array([12, 18, 40], dtype=float)
Image.fromarray(np.clip(bg + a * gold * 1.2, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "AscendantSeal_preview.png"))
print("written:", sorted(os.listdir(OUT)))

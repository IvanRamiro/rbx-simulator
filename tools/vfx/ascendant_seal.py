"""The Ascendant Seal: Realm 5's ground circle. White on transparent: the game tints it (the owner's
gold 255,170,40). No text in any language (the game's fixed directive): birds, clouds and wind only.

Second design (2026-11-03). The owner called the first "too generic": eight repeated motifs in
rings with ticks is every magic circle. This one is a scene in motion, not a ring of symbols:
  three swallows chase each other round the circle (the realm's Skyrise swallow), flying clockwise;
  each one's long tail streamer sweeps back and swells outward into the border, flowing into the
  next bird, so the edge is three living strokes, not a drawn ring;
  inside, an updraft: wind lines spiral in toward the feet, and three large auspicious clouds ride
  the current between the birds;
  the centre stays open (the body stands there).
Rotational symmetry of three, curves only, nothing straight: it reads as climbing and turning even
when still.

    python3 ascendant_seal.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantSeal.png          1024x1024, the texture
  AscendantSeal_preview.png  in the owner's gold on a dark ground
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SS = 4                        # drawn at 4x and reduced, for clean edges
W = 1024 * SS
C = W / 2
R = W * 0.47                  # radius 1.0; a clear margin past it
TAU = math.tau
BIRDS = 3
FLIGHT = -1                   # clockwise on screen (y runs down): angles decrease as the birds fly

layer = Image.new("L", (W, W), 0)
d = ImageDraw.Draw(layer)


def to_px(x, y):
    return (C + R * x, C + R * y)


def polar(r, a):
    return (r * math.cos(a), r * math.sin(a))


def ribbon(centre, widths):
    """a filled stroke along a centre line with a width at every point (tapering ends, no caps)"""
    pts = np.asarray(centre)
    left, right = [], []
    for i, (p, w) in enumerate(zip(pts, widths)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = b - a
        t = t / (np.hypot(*t) or 1)
        n = np.array([-t[1], t[0]])
        left.append(to_px(*(p + n * w / 2)))
        right.append(to_px(*(p - n * w / 2)))
    d.polygon(left + right[::-1], fill=255)


def swallow(r, a, size):
    """a swallow at radius r, angle a, flying along the circle in FLIGHT's direction: a slim body,
    long swept wings, a deep forked tail. Local x points forward, y to the bird's left"""
    fwd = np.array([-math.sin(a), math.cos(a)]) * FLIGHT
    left = np.array([-fwd[1], fwd[0]])
    base = np.array(polar(r, a))

    def P(x, y):
        q = base + size * (x * fwd + y * left)
        return to_px(*q)

    body = [P(0.55, 0), P(0.42, 0.07), P(0.12, 0.1), P(-0.3, 0.06), P(-0.38, 0), P(-0.3, -0.06), P(0.12, -0.1), P(0.42, -0.07)]
    d.polygon(body, fill=255)
    for side in (1, -1):
        # the wing: a long crescent swept back, its leading edge curved, its trailing edge hollowed
        lead = [P(0.18 - 0.62 * k ** 1.15, side * (0.06 + 0.86 * k ** 0.85)) for k in np.linspace(0, 1, 24)]
        trail = [P(-0.44 + 0.46 * k ** 0.8, side * (0.92 - 0.86 * k ** 0.7)) for k in np.linspace(0, 1, 24)]
        d.polygon(lead + trail, fill=255)
        # the tail: a fork of two long streamers
        prong = [P(-0.3 - 0.62 * k, side * (0.03 + 0.2 * k ** 1.3)) for k in np.linspace(0, 1, 16)]
        ribbon([np.array([(c[0] - C) / R, (c[1] - C) / R]) for c in prong], np.linspace(0.05 * size * 1.4, 0.006, 16))


def streamer(a0):
    """the tail streamer behind a bird at angle a0: it sweeps back round the circle against the
    flight, swelling outward into the border and tapering away just behind the next bird"""
    span = TAU / BIRDS * 0.93
    k = np.linspace(0, 1, 160)
    ang = a0 - FLIGHT * (0.16 + span * k)
    rad = 0.74 + 0.22 * np.sin(np.minimum(k * 1.25, 1) * math.pi / 2) - 0.04 * k ** 3
    centre = [np.array(polar(r, t)) for r, t in zip(rad, ang)]
    width = 0.05 * np.sin(np.clip(k * 3.2, 0, 1) * math.pi / 2) * (1 - k) ** 0.8 + 0.004
    ribbon(centre, width)
    # a fine line riding outside it, offset a little, starting later and ending sooner
    k2 = np.linspace(0.18, 0.86, 120)
    ang2 = a0 - FLIGHT * (0.16 + span * k2)
    rad2 = 0.74 + 0.22 * np.sin(np.minimum(k2 * 1.25, 1) * math.pi / 2) - 0.04 * k2 ** 3 + 0.045
    ribbon([np.array(polar(r, t)) for r, t in zip(rad2, ang2)], 0.012 * np.sin((k2 - 0.18) / 0.68 * math.pi) + 0.002)


def cloud(r0, a, s):
    """a large auspicious cloud riding the current: two scrolls curling in under a lobed crown,
    its lobes facing outward"""
    t = np.array([-math.sin(a), math.cos(a)])
    n = np.array([math.cos(a), math.sin(a)])
    base = np.array(polar(r0, a))

    def Q(u, v):
        return base + s * (u * t + v * n)

    def spiral(cu, side):
        pts = []
        for i in range(90):
            k = i / 89
            ang = math.pi / 2 + side * k * TAU * 1.35
            rad = 0.42 * (1 - 0.8 * k)
            pts.append(Q(cu - side * rad * math.cos(ang), rad * math.sin(ang)))
        return pts

    for cu, side in ((-0.5, 1), (0.5, -1)):
        pts = spiral(cu, side)
        ribbon(pts, np.linspace(0.016, 0.009, len(pts)))
    crown = [Q(-0.5 + k, 0.42 + 0.32 * math.sin(math.pi * k) + 0.08 * math.sin(3 * math.pi * k)) for k in np.linspace(0, 1, 70)]
    ribbon(crown, np.full(70, 0.016))
    # its tail streams with the wind, along the flight
    tail = [Q(0.92 + 0.9 * k, -0.06 - 0.25 * k * k) for k in np.linspace(0, 1, 40)]
    ribbon(tail, np.linspace(0.013, 0.002, 40))


def updraft():
    """wind lines spiralling in toward the feet, turning the same way the birds fly"""
    arms = 9
    for j in range(arms):
        a0 = j * TAU / arms
        k = np.linspace(0, 1, 120)
        rad = 0.62 - 0.30 * k
        ang = a0 + FLIGHT * 1.6 * k
        centre = [np.array(polar(r, t)) for r, t in zip(rad, ang)]
        width = 0.011 * np.sin(k * math.pi) ** 0.8 + 0.0015
        ribbon(centre, width)


for b in range(BIRDS):
    a = -math.pi / 2 + b * TAU / BIRDS
    swallow(0.80, a, 0.21)
    streamer(a)
    cloud(0.50, a - FLIGHT * TAU / BIRDS / 2, 0.17)
updraft()
# the eye of the updraft: one soft ring round the open centre, broken where the wind enters
for j in range(9):
    a0 = j * TAU / 9 + 0.25
    arc = [np.array(polar(0.30, a0 + 0.5 * k)) for k in np.linspace(0, 1, 30)]
    ribbon(arc, 0.008 * np.sin(np.linspace(0, math.pi, 30)) + 0.002)

# glow under every stroke, then reduce
glow = layer.filter(ImageFilter.GaussianBlur(10 * SS)).point(lambda v: int(min(255, v * 1.6)))
alpha = np.maximum(np.asarray(layer, dtype=float), np.asarray(glow, dtype=float) * 0.5)
alpha = Image.fromarray(alpha.astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
rgba = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
rgba.putalpha(alpha)
rgba.save(os.path.join(OUT, "AscendantSeal.png"))

av = np.asarray(alpha, dtype=float)[:, :, None] / 255
gold = np.array([255, 170, 40], dtype=float)
bg = np.array([12, 18, 40], dtype=float)
Image.fromarray(np.clip(bg + av * gold * 1.2, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "AscendantSeal_preview.png"))
print("written:", sorted(os.listdir(OUT)))

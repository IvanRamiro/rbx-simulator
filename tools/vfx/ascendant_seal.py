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


def _arc(c, r, a0, a1, n):
    k = np.linspace(0, 1, n)
    ang = a0 + (a1 - a0) * k
    return np.stack([c[0] + r * np.cos(ang), c[1] + r * np.sin(ang)], 1)


def _coil(c, r0, r1, a0, turns, direction, n):
    """an even (Archimedean) coil from radius r0 at a0 down to r1"""
    k = np.linspace(0, 1, n)
    ang = a0 + direction * k * turns * TAU
    rad = r0 + (r1 - r0) * k
    return np.stack([c[0] + rad * np.cos(ang), c[1] + rad * np.sin(ang)], 1)


CLEAR = []  # (centre, radius): the space round each cloud the wind lines leave open


def cloud(r0, a, s):
    """an auspicious cloud riding the current, drawn as the classic scroll is: one continuous,
    calligraphic contour. Its tail rises straight into the back lobe, runs over the big lobe and
    coils inward inside it, thinning as it tightens; the back lobe coils too; a short inner line
    doubles the big lobe; a fine wisp runs under the tail. The owner found the first clouds ugly
    (little even-width curls): the strokes now swell and taper. The lobes lead in the birds'
    direction and face outward. Units: about 5 long and 2 tall, times s"""
    fwd = np.array([-math.sin(a), math.cos(a)]) * FLIGHT
    out = np.array([math.cos(a), math.sin(a)])
    base = np.array(polar(r0, a))
    D = math.radians
    CLEAR.append((base + s * (-1.3 * fwd + 0.05 * out), s * 2.9))

    def place(pts, widths):
        pts = np.asarray(pts)
        ribbon([base + s * (u * fwd + v * out) for u, v in pts], np.asarray(widths) * s)

    k = np.linspace(0, 1, 120)
    tail = np.stack([-4.0 + 2.5 * np.sin(k * math.pi / 2), -0.85 + 0.8 * (1 - np.cos(k * math.pi / 2))], 1)
    back = _arc((-0.85, -0.05), 0.65, D(180), D(62), 90)
    big = _arc((0.25, 0.15), 0.86, D(155), D(2), 110)
    coil = _coil((0.42, 0.06), 0.68, 0.1, D(0), 1.35, -1, 220)
    path = np.concatenate([tail, back[1:], big[1:], coil[1:]])
    nt, nb, ng = len(tail), len(back) - 1, len(big) - 1
    w = np.empty(len(path))
    w[:nt] = 0.008 + 0.15 * np.linspace(0, 1, nt) ** 1.6
    w[nt:nt + nb + ng] = 0.158
    w[nt + nb + ng:] = 0.158 - 0.12 * np.linspace(0, 1, len(path) - nt - nb - ng) ** 0.9
    place(path, w)
    place(_coil((-0.85, -0.05), 0.42, 0.07, D(250), 1.15, -1, 160), 0.11 - 0.08 * np.linspace(0, 1, 160))
    place(_arc((0.25, 0.15), 0.6, D(150), D(78), 60), 0.035 + 0.03 * np.sin(np.linspace(0, math.pi, 60)))
    k = np.linspace(0, 1, 120)
    place(np.stack([-1.6 - 2.2 * k, -0.42 - 0.21 * np.sin(k * math.pi) - 0.3 * k], 1), 0.045 * np.sin(k * math.pi) ** 0.8 + 0.005)


def updraft():
    """wind lines spiralling in toward the feet, turning the same way the birds fly; each breaks
    round the clouds, so the clouds sit in clear air with the wind flowing past"""
    arms = 9
    for j in range(arms):
        a0 = j * TAU / arms
        k = np.linspace(0, 1, 160)
        rad = 0.62 - 0.30 * k
        ang = a0 + FLIGHT * 1.6 * k
        pts = np.array([polar(r, q) for r, q in zip(rad, ang)])
        width = 0.011 * np.sin(k * math.pi) ** 0.8 + 0.0015
        free = np.array([all(np.hypot(*(p - c)) > r for c, r in CLEAR) for p in pts])
        i = 0
        while i < len(pts):
            if not free[i]:
                i += 1
                continue
            j2 = i
            while j2 < len(pts) and free[j2]:
                j2 += 1
            if j2 - i >= 8:
                run = np.arange(i, j2)
                ramp = np.sin(np.linspace(0, math.pi, len(run))) ** 0.35   # each piece tapers at both ends
                ribbon(list(pts[run]), width[run] * ramp + 0.0008)
            i = j2


for b in range(BIRDS):
    a = -math.pi / 2 + b * TAU / BIRDS
    swallow(0.80, a, 0.21)
    streamer(a)
    cloud(0.52, a - FLIGHT * TAU / BIRDS / 2, 0.125)
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

"""Realm 5's ground circle in the style of the owner's reference (2026-11-03): luminous energy, not
line art. Concentric rings burning white-hot in their cores and fading to gold and orange, flickering
along their length; a faint glow filling the disc; fine energy veins crackling between the rings;
four bright star nodes on the outer rings; swirling energy arcs whipping round the rim; sparkle dust;
a four-point star at the centre. No text in any language (the game's fixed directive): the marks
between the rings are abstract shapes only.

The texture carries its own colours, white-hot to the owner's gold (255,170,40) to deep orange, so the
emitter's Color is white: a tint alone can't make white-hot cores.

    python3 ascendant_energy_circle.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantCircle.png          1024x1024 RGBA
  AscendantCircle_preview.png  (renders/aura) on a dark ground
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
rng = np.random.default_rng(5)
N = 2048
R = N * 0.46
TAU = math.tau

yy, xx = np.mgrid[0:N, 0:N].astype(float)
X = (xx - N / 2) / R
Y = (yy - N / 2) / R
RAD = np.hypot(X, Y)
ANG = np.arctan2(Y, X)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def angular_noise(freq, seed):
    """smooth noise round the circle, 0..1"""
    r = np.random.default_rng(seed)
    k = np.arange(1, freq + 1)
    amp = 1 / k ** 1.2
    ph = r.random(freq) * TAU
    v = sum(a * np.cos(kk * ANG + p) for a, kk, p in zip(amp, k, ph))
    v = (v - v.min()) / (v.max() - v.min())
    return v


def blur(img, radius):
    return np.asarray(Image.fromarray(np.clip(img * 64, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius)), dtype=float) / 64


I = np.zeros((N, N))

# --- a faint glow filling the disc, banded a little ----------------------------------------------
I += 0.13 * smoothstep(0.95, 0.25, RAD) * (0.75 + 0.25 * np.cos(RAD * 34))

# --- the rings, each flickering along its length ------------------------------------------------
for i, (r0, w, s) in enumerate([(0.90, 0.010, 1.25), (0.855, 0.004, 0.7), (0.78, 0.006, 0.9), (0.64, 0.009, 1.05),
                                (0.60, 0.0035, 0.6), (0.44, 0.007, 0.9), (0.36, 0.004, 0.65), (0.20, 0.006, 0.8)]):
    flicker = 0.55 + 0.45 * angular_noise(14, 20 + i)
    I += s * np.exp(-((RAD - r0) / w) ** 2) * flicker

# --- strokes drawn as lines: marks, veins, arcs -----------------------------------------------
L = Image.new("L", (N, N), 0)
d = ImageDraw.Draw(L)


def P(r, a):
    return (N / 2 + R * r * math.cos(a), N / 2 + R * r * math.sin(a))


# abstract marks in the band between the outer rings: alternating short arcs, paired dots, chevrons
for k in range(40):
    a = k * TAU / 40 + 0.04
    kind = k % 4
    if kind == 0:
        d.arc([N / 2 - R * 0.715, N / 2 - R * 0.715, N / 2 + R * 0.715, N / 2 + R * 0.715],
              math.degrees(a - 0.035), math.degrees(a + 0.035), fill=210, width=6)
    elif kind == 1:
        for dr in (-0.025, 0.025):
            c = P(0.715 + dr, a)
            d.ellipse([c[0] - 6, c[1] - 6, c[0] + 6, c[1] + 6], fill=220)
    elif kind == 2:
        d.line([P(0.69, a - 0.02), P(0.715, a), P(0.74, a - 0.02)], fill=210, width=5)
    else:
        d.line([P(0.69, a), P(0.74, a)], fill=170, width=4)
# the same, smaller, in the inner band
for k in range(24):
    a = k * TAU / 24
    if k % 2 == 0:
        d.line([P(0.505, a - 0.03), P(0.52, a), P(0.535, a - 0.03)], fill=130, width=4)
    else:
        c = P(0.52, a)
        d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=140)

# energy veins: short jittering walks between the rings, like current running through the circle
for band, count in (((0.66, 0.77), 12), ((0.46, 0.58), 8), ((0.24, 0.33), 4)):
    for _ in range(count):
        r = rng.uniform(*band)
        a = rng.uniform(0, TAU)
        pts = [P(r, a)]
        for _ in range(rng.integers(5, 10)):
            a += rng.normal(0.035, 0.01)
            r = float(np.clip(r + rng.normal(0, 0.006), band[0], band[1]))
            pts.append(P(r, a))
        d.line(pts, fill=int(rng.uniform(60, 110)), width=3, joint="curve")

def diamond(r, a, length, width, fill, line):
    pts = [P(r + length, a), P(r, a + width), P(r - length, a), P(r, a - width), P(r + length, a)]
    d.line(pts, fill=fill, width=line, joint="curve")


for k in range(4):
    a = k * TAU / 4 - math.pi / 2
    diamond(0.90, a, 0.085, 0.07, 230, 6)
    diamond(0.90, a, 0.05, 0.04, 200, 4)
    diamond(0.64, a + TAU / 8, 0.055, 0.06, 210, 5)

I += np.asarray(L, dtype=float) / 255 * 0.9

# swirling energy arcs whipping round the rim: long tapering ribbons, spiralling outward
S = Image.new("L", (N, N), 0)
ds = ImageDraw.Draw(S)
for j in range(6):
    a0 = j * TAU / 6 + rng.uniform(-0.3, 0.3)
    span = rng.uniform(1.1, 2.0)
    r0 = rng.uniform(0.86, 0.9)
    r1 = rng.uniform(0.96, 1.02)
    k = np.linspace(0, 1, 120)
    ang = a0 + span * k
    rad = r0 + (r1 - r0) * k
    width = 16 * np.sin(k * math.pi) ** 0.7 + 1
    left, right = [], []
    for i in range(len(k)):
        n = (math.cos(ang[i]), math.sin(ang[i]))
        c = P(rad[i], ang[i])
        left.append((c[0] + n[0] * width[i] / 2, c[1] + n[1] * width[i] / 2))
        right.append((c[0] - n[0] * width[i] / 2, c[1] - n[1] * width[i] / 2))
    ds.polygon(left + right[::-1], fill=int(rng.uniform(170, 230)))
I += blur(np.asarray(S, dtype=float) / 255, 3) * 1.0


# --- star nodes: four bright on the outer ring, four smaller on the middle ring, one at the centre ---
def star4(cx, cy, size, s):
    dx, dy = (X - cx) / size, (Y - cy) / size
    arms = np.exp(-(dx ** 2 / 0.006 + dy ** 2)) + np.exp(-(dy ** 2 / 0.006 + dx ** 2))
    core = np.exp(-(dx ** 2 + dy ** 2) / 0.02)
    return s * (arms * 0.9 + core * 1.4)


for k in range(4):
    a = k * TAU / 4 - math.pi / 2
    I += star4(0.90 * math.cos(a), 0.90 * math.sin(a), 0.12, 1.3)
    a2 = a + TAU / 8
    I += star4(0.64 * math.cos(a2), 0.64 * math.sin(a2), 0.07, 0.9)
I += star4(0, 0, 0.16, 1.2)

# --- sparkle dust, thicker near the rings ------------------------------------------------------
dust = np.zeros((N, N))
for _ in range(900):
    r = float(np.clip(rng.choice([0.90, 0.78, 0.64, 0.44]) + rng.normal(0, 0.05), 0.1, 1.0))
    a = rng.uniform(0, TAU)
    x, y = P(r, a)
    xi, yi = int(x), int(y)
    if 0 <= xi < N and 0 <= yi < N:
        dust[yi, xi] = rng.uniform(0.4, 1.0)
I += blur(dust, 2.2) * 9

# --- bloom, edge fade -------------------------------------------------------------------------------
I = I + blur(I, 6) * 0.55 + blur(I, 22) * 0.35
I *= smoothstep(1.08, 1.0, RAD)

# white-hot cores, the owner's gold, deep orange at the faint edges
gold = np.array([255, 170, 40], dtype=float)
orange = np.array([230, 110, 20], dtype=float)
white = np.array([255, 245, 215], dtype=float)
t_low = np.clip(I / 0.5, 0, 1)[..., None]
t_hot = np.clip((I - 0.75) / 0.8, 0, 1)[..., None]
rgb = orange * (1 - t_low) + gold * t_low
rgb = rgb * (1 - t_hot) + white * t_hot
alpha = np.clip(I * 1.05, 0, 1)

img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
img.save(os.path.join(OUT, "AscendantCircle.png"))
a = np.asarray(img, dtype=float)
bg = np.array([12, 18, 40], dtype=float)
prev = bg * (1 - a[..., 3:] / 255) + a[..., :3] * (a[..., 3:] / 255) + a[..., :3] * (a[..., 3:] / 255) * 0.3
Image.fromarray(np.clip(prev, 0, 255).astype(np.uint8)).save(os.path.join(PREVIEWS, "AscendantCircle_preview.png"))
print("written:", sorted(os.listdir(OUT)))

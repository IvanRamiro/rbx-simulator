"""Realm 5's Taiji Seal: the circle behind the head (the owner, 2026-11-03: "something like this and
add the yin and yang on the center", their reference 129313199386118, a white line-art magic circle).
Our own drawing in that style, as lines of gold light:
  outer    a braided rim: two strands twisting round each other between two rings
  orbs     six orbs on a double band, each ringed by a toothed halo, a point of light in each
  web      lines from the rim to the orbs, a triangle round each orb
  inner    a hexagon whose corners touch the band's inner edge, a ring inside it, nodes at the corners
  heart    the yin and yang (as AscendantTaiji: gold yang, smoky dark yin, lines of light)
No text, no trigrams. The texture carries its own colour and alpha, so its ImageColor3 is white.

    python3 ascendant_taiji_seal.py assets/aura/ascendant     (needs Pillow and numpy)

  AscendantTaijiSeal.png          1024x1024 RGBA
  AscendantTaijiSeal_preview.png  (renders/aura) on a dark ground and on a sky blue
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


def ring(r, w, v=255, cx=0.0, cy=0.0):
    x, y = C + R * cx, C + R * cy
    d.ellipse([x - R * r, y - R * r, x + R * r, y + R * r], outline=v, width=int(w))


def poly(pts, w, v=255, closed=True):
    d.line(pts + ([pts[0]] if closed else []), fill=v, width=int(w), joint="curve")


def dot(p, rad, v=255):
    d.ellipse([p[0] - rad, p[1] - rad, p[0] + rad, p[1] + rad], fill=v)


# --- outer: the braided rim ----------------------------------------------------------
ring(0.985, 5)
ring(0.905, 5)
for phase in (0, math.pi):
    pts = []
    for i in range(721):
        a = i * TAU / 720
        r = 0.945 + 0.03 * math.sin(a * 48 + phase)
        pts.append(P(r, a))
    poly(pts, 4, 220, closed=False)

# --- orbs on a double band ---------------------------------------------------------------
BAND = 0.64
ORB = 0.115
ring(BAND + 0.03, 4, 230)
ring(BAND - 0.03, 4, 230)
orbs = []
for k in range(6):
    a = k * TAU / 6 - math.pi / 2
    cx, cy = BAND * math.cos(a), BAND * math.sin(a)
    orbs.append((cx, cy, a))
    # clear the band inside the orb, then draw the orb
    x, y = C + R * cx, C + R * cy
    d.ellipse([x - R * (ORB + 0.01), y - R * (ORB + 0.01), x + R * (ORB + 0.01), y + R * (ORB + 0.01)], fill=0)
    ring(ORB, 7, 255, cx, cy)
    ring(ORB - 0.025, 3, 170, cx, cy)
    # the toothed halo: short spikes round the orb
    for t in range(40):
        b = t * TAU / 40
        p0 = (x + R * (ORB + 0.012) * math.cos(b), y + R * (ORB + 0.012) * math.sin(b))
        p1 = (x + R * (ORB + (0.032 if t % 2 else 0.022)) * math.cos(b), y + R * (ORB + (0.032 if t % 2 else 0.022)) * math.sin(b))
        d.line([p0, p1], fill=200, width=3)
    dot((x, y), R * 0.022, 255)

# --- the web: from the rim to each orb, a triangle round it ----------------------------------
for cx, cy, a in orbs:
    for side in (-1, 1):
        rim = P(0.905, a + side * TAU / 12)
        tangent = (C + R * (cx + (ORB + 0.035) * math.cos(a + side * 1.25)), C + R * (cy + (ORB + 0.035) * math.sin(a + side * 1.25)))
        d.line([rim, tangent], fill=190, width=3)
    tip = P(0.905, a)
    d.line([tip, P(BAND + ORB + 0.035, a)], fill=190, width=3)
    dot(P(0.905, a + TAU / 12), R * 0.012, 255)

# --- inner: a hexagon, a ring inside it, nodes at the corners --------------------------------
HEX = BAND - 0.03
hexpts = [P(HEX, k * TAU / 6 - math.pi / 2 + TAU / 12) for k in range(6)]
poly(hexpts, 4, 220)
ring(0.5, 3, 190)
for p in hexpts:
    dot(p, R * 0.016, 255)
for k in range(6):                                   # spokes from the corners in to the heart's ring
    a = k * TAU / 6 - math.pi / 2 + TAU / 12
    d.line([P(0.5, a), P(0.4, a)], fill=170, width=3)

# bolder lines: thin ones vanished against the day sky
lines = np.asarray(L.filter(ImageFilter.MaxFilter(5)), dtype=float) / 255


# --- the heart: the yin and yang --------------------------------------------------------
yy, xx = np.mgrid[0:N, 0:N].astype(float)
X = (xx - C) / R
Y = -(yy - C) / R
RAD = np.hypot(X, Y)
ANG = np.arctan2(Y, X)
S = 0.38


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


x, y = X / S, Y / S
r = np.hypot(x, y)
px = 1.0 / (R * S)
inside = smooth(1 + px * 2, 1 - px * 2, r)
top, bot = np.hypot(x, y - 0.5), np.hypot(x, y + 0.5)
yang = np.clip(smooth(-px * 2, px * 2, x) * (1 - smooth(0.5 + px * 2, 0.5 - px * 2, bot)) + smooth(0.5 + px * 2, 0.5 - px * 2, top), 0, 1)
yang = np.clip(yang * (1 - smooth(0.15 + px * 2, 0.15 - px * 2, top)) + smooth(0.15 + px * 2, 0.15 - px * 2, bot), 0, 1) * inside
yin = inside * (1 - yang)
g0, g1 = np.gradient(yang)
edge = np.clip((np.abs(g0) + np.abs(g1)) * 6, 0, 1) * inside


def blur(img, rad):
    return np.asarray(Image.fromarray(np.clip(img * 64, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad)), dtype=float) / 64


outline = np.exp(-((r - 1) / 0.018) ** 2)
taiji_lines = np.clip(blur(edge, 2) * 1.6 + outline, 0, 1)
yang_glow = yang * (0.55 + 0.35 * smooth(1.0, 0.2, r) + 0.15 * (0.5 + 0.5 * np.cos(r * 18)))

# light: the line art flickers a little along its length; everything blooms
flicker = 0.75 + 0.25 * (0.5 + 0.5 * np.cos(ANG * 7 + RAD * 9) * np.cos(ANG * 3 - 1.3))
light = lines * flicker * 1.4 + yang_glow * 0.85 + taiji_lines * 1.3
light = light + blur(light, 6) * 0.55 + blur(light, 24) * 0.35
light += 0.05 * np.clip(1 - RAD, 0, 1) ** 0.5 * (RAD < 1) * (1 - inside)   # a faint glow filling the seal

white = np.array([255, 245, 215], dtype=float)
gold = np.array([255, 170, 40], dtype=float)
amber = np.array([210, 100, 15], dtype=float)
lo = np.clip(light / 0.55, 0, 1)[..., None]
hot = np.clip((light - 0.85) / 0.8, 0, 1)[..., None]
glow_rgb = amber * (1 - lo) + gold * lo
glow_rgb = glow_rgb * (1 - hot) + white * hot
swirl = 0.5 + 0.5 * np.cos(ANG * 3 + r * 7)
yin_rgb = np.array([22, 13, 8], dtype=float) + np.array([60, 35, 8], dtype=float) * (smooth(0.6, 1.0, r) * 0.6 + swirl * 0.15)[..., None]

la = np.clip(light, 0, 1)[..., None]
yin_a = (yin * 0.9)[..., None]
rgb = yin_rgb * yin_a * (1 - la) + glow_rgb * la
alpha = np.clip(yin_a[..., 0] * (1 - la[..., 0]) + la[..., 0], 0, 1)
rgb = rgb / np.maximum(alpha[..., None], 1e-4)
alpha *= smooth(1.03, 1.0, RAD)

img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
img.save(os.path.join(OUT, "AscendantTaijiSeal.png"))
a = np.asarray(img, dtype=float)
al = a[..., 3:] / 255
tiles = [np.clip(bg * (1 - al) + a[..., :3] * al, 0, 255).astype(np.uint8)
         for bg in (np.array([12, 18, 40], dtype=float), np.array([110, 170, 230], dtype=float))]
Image.fromarray(np.hstack(tiles)).save(os.path.join(PREVIEWS, "AscendantTaijiSeal_preview.png"))
print("written")

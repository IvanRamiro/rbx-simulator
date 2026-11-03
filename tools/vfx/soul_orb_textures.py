"""Realm 4's soul orbs (the owner's design, 2026-11-03): three spheres of black smoke with a star at
the centre and lightning on the edge. These are the star and the smoke; the lightning is built in
code from beams. White on transparent (true transparency, so the star works on a billboard, which
can't drop a black background); the game tints them.

    python3 soul_orb_textures.py assets/aura/soul_orbs     (needs Pillow and numpy)

  StarFlare.png  512x512    a thin cross flare: needle rays tapering to nothing, a hot core, a soft
                            halo and four faint shorter diagonal rays
  SmokePuff.png  1024x1024  4x4 flipbook (OneShot): a puff of smoke billows out, tears into wisps
                            and dissolves over its life; nothing touches a cell's edge
"""
import math
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20261105)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def save(alpha, name, size):
    img = Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    rgba = Image.new("RGBA", size, (255, 255, 255, 0))
    rgba.putalpha(img)
    rgba.save(os.path.join(OUT, name))


# ---------- the star: drawn at 2048 and reduced ----------
def star():
    S = 2048
    v = np.linspace(-1, 1, S)
    x, y = np.meshgrid(v, v)
    r = np.hypot(x, y)

    def ray(along, across, length, width, power):
        # a needle: thinnest at its tip, its brightness falling off steeply along its length
        t = np.clip(np.abs(along) / length, 0, 1)
        w = width * (1 - t) + 0.0015
        return np.exp(-(across / w) ** 2) * (1 - t) ** power

    cross = np.maximum(ray(x, y, 0.95, 0.018, 2.2), ray(y, x, 0.95, 0.018, 2.2))
    d1, d2 = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
    diag = np.maximum(ray(d1, d2, 0.42, 0.01, 2.6), ray(d2, d1, 0.42, 0.01, 2.6)) * 0.35
    core = np.exp(-(r / 0.035) ** 2)
    halo = np.exp(-r / 0.11) * 0.45
    a = np.maximum.reduce([cross, diag, core, halo])
    a *= 1 - smoothstep(0.92, 1.0, r)                     # nothing at the border
    save(a, "StarFlare.png", (512, 512))


# ---------- the smoke: value noise, warped and eroded over 16 frames ----------
def noise(n, size):
    grid = Image.fromarray((RNG.random((n, n)) * 255).astype(np.uint8))
    return np.asarray(grid.resize((size, size), Image.BICUBIC), dtype=float) / 255


def fbm(size, base, octaves=5):
    total, amp, weight = np.zeros((size, size)), 1.0, 0.0
    for o in range(octaves):
        total += noise(base * 2 ** o, size) * amp
        weight += amp
        amp *= 0.55
    return total / weight


def sample(field, x, y):
    """bilinear lookup of a square field at coordinates in -1..1 (wrapping)"""
    n = field.shape[0]
    fx = (x * 0.5 + 0.5) * (n - 1)
    fy = (y * 0.5 + 0.5) * (n - 1)
    x0, y0 = np.floor(fx).astype(int) % n, np.floor(fy).astype(int) % n
    x1, y1 = (x0 + 1) % n, (y0 + 1) % n
    tx, ty = fx - np.floor(fx), fy - np.floor(fy)
    top = field[y0, x0] * (1 - tx) + field[y0, x1] * tx
    bottom = field[y1, x0] * (1 - tx) + field[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def smoke():
    C = 256
    v = np.linspace(-1, 1, C)
    x, y = np.meshgrid(v, v)
    warp_a, warp_b = fbm(512, 4), fbm(512, 4)
    warp_a += 0.5 - warp_a.mean()                    # centred, so the puff stays mid-cell
    warp_b += 0.5 - warp_b.mean()
    body, tear = fbm(512, 6), fbm(512, 9)
    sheet = np.zeros((C * 4, C * 4))
    for f in range(16):
        t = f / 15
        swirl = 0.9 * t                                   # the puff turns as it billows
        cs, sn = math.cos(swirl), math.sin(swirl)
        rx, ry = x * cs - y * sn, x * sn + y * cs
        # domain warp: the outline boils outward and curls
        wx = rx + (sample(warp_a, rx * 0.6, ry * 0.6) - 0.5) * (0.5 + 0.6 * t)
        wy = ry + (sample(warp_b, rx * 0.6 + 0.3, ry * 0.6) - 0.5) * (0.5 + 0.6 * t)
        r = np.hypot(wx, wy)
        radius = 0.38 + 0.4 * t                           # it billows out
        shape = 1 - smoothstep(radius * 0.35, radius, r)
        density = shape * (0.55 + 0.45 * sample(body, wx * 0.8, wy * 0.8 + t * 0.3))
        # erosion: holes open and the edge tears into wisps as it ages
        erode = smoothstep(0.15 + 0.55 * t, 0.35 + 0.55 * t, sample(tear, wx, wy - t * 0.2) + (1 - shape) * 0.2)
        density *= 1 - (1 - erode) * min(1, t * 1.4)
        density *= (1 - t ** 1.6) * smoothstep(0, 0.12, t + 0.05)   # fades in fast, out slowly
        density *= 1 - smoothstep(0.82, 0.98, np.hypot(x, y))      # never touches the cell's edge
        row, col = divmod(f, 4)
        sheet[row * C:(row + 1) * C, col * C:(col + 1) * C] = np.clip(density * 1.25, 0, 1)
    save(sheet, "SmokePuff.png", (1024, 1024))


star()
smoke()
print("written:", sorted(os.listdir(OUT)))

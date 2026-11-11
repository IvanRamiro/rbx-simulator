"""Realm 4's soul orbs (the owner's design, 2026-11-03): three spheres of black smoke with a star at
the centre and lightning on the edge. These are the star and the smoke; the lightning is built in
code from beams. White on transparent (true transparency, so the star works on a billboard, which
can't drop a black background); the game tints them.

    python3 soul_orb_textures.py assets/aura/soul_orbs     (needs Pillow and numpy)

  StarFlare.png  512x512    a short cross flare: rays tapering to nothing well inside the image
                            (the owner: the first was "too long"), a hot core, a soft halo and
                            four faint diagonal glints
  SmokePuff.png  1024x1024  4x4 flipbook (OneShot): a puff of smoke billows out, tears into wisps
                            and dissolves over its life, inside the middle 78% of its cell
                            (a clear margin round every frame)
  SmokeRing.png  1024x1024  a ripple of smoke: wispy strands round a ring, broken and uneven,
                            sampled on the circle (no seam), exactly zero well inside the border
                            (a borrowed ring's faint border showed as a square at 19 studs)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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

    cross = np.maximum(ray(x, y, 0.45, 0.03, 1.7), ray(y, x, 0.45, 0.03, 1.7))
    d1, d2 = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
    diag = np.maximum(ray(d1, d2, 0.2, 0.016, 2), ray(d2, d1, 0.2, 0.016, 2)) * 0.3
    core = np.exp(-(r / 0.05) ** 2)
    halo = np.exp(-r / 0.09) * 0.4
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
    # the puff fills only the middle 78% of its cell: a clear margin round every frame, so the
    # texture's lower-resolution copies (used at a distance) never blend a neighbour's smoke in
    # and draw the cell's edge (a faint square on the ground mist, 2026-11-03)
    x, y = x / 0.78, y / 0.78
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
        density *= 1 - smoothstep(0.85, 1.0, np.hypot(x, y))       # zero from 78% of the cell out
        row, col = divmod(f, 4)
        sheet[row * C:(row + 1) * C, col * C:(col + 1) * C] = np.clip(density * 1.25, 0, 1)
    save(sheet, "SmokePuff.png", (1024, 1024))


# ---------- the Soul Seal: drawn at 4096 with Pillow, reduced ----------
def smoke_ring():
    S = 1024
    v = np.linspace(-1, 1, S)
    x, y = np.meshgrid(v, v)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    cx, cy = np.cos(th), np.sin(th)                  # noise sampled on the circle: no seam at 180 deg
    wobble, gaps = fbm(512, 4), fbm(512, 6)
    a = np.zeros_like(r)
    strands = ((0.72, 0.022, 1.0), (0.66, 0.016, 0.8), (0.78, 0.014, 0.7), (0.6, 0.012, 0.55), (0.75, 0.01, 0.6), (0.69, 0.009, 0.5))
    for k, (base, width, power) in enumerate(strands):
        # each strand wanders in and out round the ring, thins and breaks in places. Every lookup stays
        # inside the noise field (|coord| < 0.9): past its edge the field wraps and leaves a seam
        ox, oy = (k % 3 - 1) * 0.25, (k // 3 - 0.5) * 0.3
        rr = base + (sample(wobble, cx * 0.5 + ox, cy * 0.5 + oy) - 0.5) * 0.22
        strand = np.exp(-((r - rr) / width) ** 2)
        strand *= smoothstep(0.38, 0.68, sample(gaps, cx * 0.55 - oy, cy * 0.55 + ox))
        a = np.maximum(a, strand * power)
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), dtype=float) / 255
    a *= 1 - smoothstep(0.86, 0.93, r)                   # exactly zero from 0.93 out
    a *= smoothstep(0.4, 0.5, r)
    save(np.clip(a * 1.6, 0, 1), "SmokeRing.png", (1024, 1024))


star()
smoke()
smoke_ring()
print("written:", sorted(os.listdir(OUT)))

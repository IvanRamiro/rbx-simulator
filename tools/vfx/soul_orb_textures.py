"""Realm 4's soul orbs (the owner's design, 2026-11-03): three spheres of black smoke with a star at
the centre and lightning on the edge. These are the star and the smoke; the lightning is built in
code from beams. White on transparent (true transparency, so the star works on a billboard, which
can't drop a black background); the game tints them.

    python3 soul_orb_textures.py assets/aura/soul_orbs     (needs Pillow and numpy)

  StarFlare.png  512x512    a short cross flare: rays tapering to nothing well inside the image
                            (the owner: the first was "too long"), a hot core, a soft halo and
                            four faint diagonal glints
  SmokePuff.png  1024x1024  4x4 flipbook (OneShot): a puff of smoke billows out, tears into wisps
                            and dissolves over its life; nothing touches a cell's edge
  SoulSeal.png   1024x1024  the ground circle under the Spirit Soul aura: a double rim with ticks,
                            three soul nodes (one under each orb) joined by a fine triangle, a ring
                            of curling soul flames, an inner ring; the centre is left open
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


# ---------- the Soul Seal: drawn at 4096 with Pillow, reduced ----------
def soul_seal():
    S = 4096
    c = S / 2
    R = S * 0.48
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)

    def P(r, a):
        return c + math.cos(a) * r * R, c + math.sin(a) * r * R

    def ring(r, w):
        d.ellipse([c - r * R, c - r * R, c + r * R, c + r * R], outline=255, width=int(w))

    # the rim: two rings, fine ticks between, a longer tick every sixth
    ring(1.0, 20)
    ring(0.94, 10)
    for k in range(72):
        a = k / 72 * math.tau
        d.line([P(0.947, a), P(0.985 if k % 6 else 0.995, a)], fill=255, width=8 if k % 6 else 14)
    # the three soul nodes on the rim's inner edge (they sit under the three orbs), joined by a fine
    # triangle; the ring and tick marks break round each node
    nodes = [k * math.tau / 3 for k in range(3)]
    for a in nodes:
        x, y = P(0.86, a)
        rr = 0.075 * R
        d.ellipse([x - rr * 1.25, y - rr * 1.25, x + rr * 1.25, y + rr * 1.25], fill=0)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=255, width=14)
        d.ellipse([x - rr * 0.35, y - rr * 0.35, x + rr * 0.35, y + rr * 0.35], fill=255)
    for k in range(3):
        a0, a1 = nodes[k], nodes[(k + 1) % 3]
        # stop the side short of each node's circle
        x0, y0 = P(0.86, a0)
        x1, y1 = P(0.86, a1)
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        g = 0.075 * R * 1.5 / L
        d.line([(x0 + dx * g, y0 + dy * g), (x1 - dx * g, y1 - dy * g)], fill=255, width=7)
    # a ring of curling soul flames: a teardrop head trailing a tapering curl, all turning one way.
    # Each is traced densely (no dotted tail) and first cut out of what lies under it with a thin
    # dark gap, so the triangle's sides pass behind the flames instead of through them
    flames = []
    for k in range(12):
        a = k / 12 * math.tau + math.tau / 24
        pts = []
        for i in range(120):
            t = i / 119
            ang = a - 0.42 * t                        # the tail curls back round the circle
            rad = 0.66 + 0.07 * math.sin(t * math.pi)  # swelling out, then back in
            w = 0.036 * (1 - t) ** 1.3 + 0.003
            pts.append((P(rad, ang), w))
        flames.append(pts)
    for gap, fill in ((1.0, 0), (0, 255)):
        for pts in flames:
            for (x, y), w in pts:
                rr = w * R + gap * 0.012 * R
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)
    for pts in flames:                                # hollow the head so it reads as a flame
        (hx, hy), hw = pts[0]
        rr = hw * R * 0.45
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=0)
    # the inner ring, broken into three arcs between the triangle's sides
    for k in range(3):
        a = math.degrees(nodes[k]) + 60
        box = [c - 0.46 * R, c - 0.46 * R, c + 0.46 * R, c + 0.46 * R]
        d.arc(box, a - 45, a + 45, fill=255, width=12)
    ring(0.4, 6)
    # a soft glow under every line, so the seal reads as light
    glow = img.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(min(255, v * 1.4)))
    a = np.maximum(np.asarray(img, dtype=float) / 255, np.asarray(glow, dtype=float) / 255 * 0.55)
    yy, xx = np.mgrid[0:S, 0:S]
    a *= 1 - smoothstep(0.985, 1.0, np.hypot(xx - c, yy - c) / (S / 2))
    save(a, "SoulSeal.png", (1024, 1024))


star()
smoke()
soul_seal()
print("written:", sorted(os.listdir(OUT)))

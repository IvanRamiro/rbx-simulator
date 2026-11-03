"""The top two realms' aura textures (the owner's Tier 10 and Tier 12 brief, 2026-11-03). White
on transparent: the game tints them. Drawn at 4x and reduced for clean edges; 1024 at most, since
Roblox stores images no larger. No text in any language (the game's fixed directive): the "runes"
are original sacred geometry, trigram bars and abstract marks.

    python3 top_tier_aura_textures.py assets/aura/top_tier     (needs Pillow and numpy)

  DaoRunes.png     1024x1024  Heavenly Dao: concentric law circles for the turning ground disc
  LawStreak.png     256x1024  Heavenly Dao: razor-thin vertical threads, with breaks, for the law
                              beams shooting into the sky (VelocityParallel particles)
  NebulaMask.png   1024x1024  Eternal: fractal nebula and star clusters, fading to the edge, for
                              the cosmic core and the shockwaves
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20261103)


def save_alpha(mask, name, size):
    """mask: an 'L' image (white = opaque); saved as white RGBA at `size`."""
    mask = mask.resize(size, Image.LANCZOS)
    rgba = Image.new("RGBA", size, (255, 255, 255, 0))
    rgba.putalpha(mask)
    rgba.save(os.path.join(OUT, name))


# ---------- Dao Runes: concentric law circles ----------
def dao_runes():
    S = 4096
    c = S / 2
    R = S * 0.49
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)

    def ring(r, w):
        d.ellipse([c - r * R, c - r * R, c + r * R, c + r * R], outline=255, width=int(w))

    def polar(r, a):
        return c + math.cos(a) * r * R, c + math.sin(a) * r * R

    # the rim: a double ring with a tick band between
    ring(1.0, 22)
    ring(0.94, 12)
    for i in range(96):
        a = i / 96 * math.tau
        inner = 0.955 if i % 4 else 0.945
        d.line([polar(inner, a), polar(0.99, a)], fill=255, width=10 if i % 4 else 16)

    # eight trigram cartouches: three bars each, broken or whole (the eight patterns in turn)
    for k in range(8):
        a = k / 8 * math.tau - math.pi / 2
        for bar in range(3):
            whole = (k >> bar) & 1
            r = 0.835 + (bar - 1) * 0.035
            half = 0.1
            if whole:
                pts = [polar(r, a - half), polar(r, a + half)]
                d.line(pts, fill=255, width=34)
            else:
                d.line([polar(r, a - half), polar(r, a - 0.022)], fill=255, width=34)
                d.line([polar(r, a + 0.022), polar(r, a + half)], fill=255, width=34)
        # its frame: two arcs closed by ticks
        for r in (0.775, 0.895):
            box = [c - r * R, c - r * R, c + r * R, c + r * R]
            d.arc(box, math.degrees(a - 0.135), math.degrees(a + 0.135), fill=255, width=10)
        for side in (-1, 1):
            d.line([polar(0.775, a + side * 0.135), polar(0.895, a + side * 0.135)], fill=255, width=10)

    # between the cartouches: abstract marks (geometric symbols, never letters)
    def mark(kind, x, y, s, a):
        rot = lambda px, py: (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))
        if kind == 0:   # a ring with a dot
            d.ellipse([x - s, y - s, x + s, y + s], outline=255, width=10)
            d.ellipse([x - s * 0.25, y - s * 0.25, x + s * 0.25, y + s * 0.25], fill=255)
        elif kind == 1:  # a triangle
            d.polygon([rot(0, -s), rot(s * 0.87, s * 0.5), rot(-s * 0.87, s * 0.5)], outline=255, width=10)
        elif kind == 2:  # a diamond with a bar through it
            d.polygon([rot(0, -s), rot(s * 0.7, 0), rot(0, s), rot(-s * 0.7, 0)], outline=255, width=10)
            d.line([rot(-s, 0), rot(s, 0)], fill=255, width=10)
        else:            # three dots in a line
            for t in (-0.7, 0, 0.7):
                px, py = rot(t * s, 0)
                d.ellipse([px - s * 0.2, py - s * 0.2, px + s * 0.2, py + s * 0.2], fill=255)
    for k in range(8):
        for j in range(1, 3):
            a = (k + j / 3) / 8 * math.tau - math.pi / 2
            x, y = polar(0.835, a)
            mark((k + j) % 4, x, y, R * 0.035, a)

    # the inner law: a ring, an eight-pointed star, a ring of dots, sixteen petals, the centre
    ring(0.74, 14)
    for turn in (0, math.pi / 4):
        pts = [polar(0.7, turn + q * math.pi / 2) for q in range(4)]
        d.polygon(pts, outline=255, width=12)
    ring(0.5, 10)
    for i in range(32):
        x, y = polar(0.6, i / 32 * math.tau)
        rr = R * (0.014 if i % 2 else 0.022)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    for i in range(16):
        a = i / 16 * math.tau
        tip, base = polar(0.48, a), polar(0.3, a)
        left, right = polar(0.39, a - 0.13), polar(0.39, a + 0.13)
        d.polygon([base, left, tip, right], outline=255, width=9)
    ring(0.27, 12)
    ring(0.12, 26)
    d.ellipse([c - 0.05 * R, c - 0.05 * R, c + 0.05 * R, c + 0.05 * R], fill=255)

    # a faint glow under the lines, so the disc reads as light, not wire
    glow = img.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.55))
    out = Image.fromarray(np.maximum(np.asarray(img), np.asarray(glow)).astype(np.uint8))
    save_alpha(out, "DaoRunes.png", (1024, 1024))


# ---------- Law Streak: thin vertical threads with breaks ----------
def law_streak():
    W, H = 1024, 4096
    x = np.arange(W)[None, :]
    y = np.linspace(0, 1, H)[:, None]
    out = np.zeros((H, W))
    threads = [(0.5, 7, 1.0)] + [(0.5 + RNG.uniform(-0.32, 0.32), RNG.uniform(2.5, 5), RNG.uniform(0.3, 0.7)) for _ in range(9)]
    for cx, width, power in threads:
        across = np.exp(-((x - cx * W) ** 2) / (2 * width ** 2))
        # along it: lit segments with breaks of varied length, brighter in the middle of each
        along = np.zeros((H, 1))
        pos = RNG.uniform(0, 0.1)
        while pos < 1:
            length = RNG.uniform(0.08, 0.35)
            seg = (y >= pos) & (y < pos + length)
            mid = np.sin(np.clip((y - pos) / length, 0, 1) * math.pi)
            along = np.maximum(along, seg * (0.55 + 0.45 * mid) * RNG.uniform(0.6, 1))
            pos += length + RNG.uniform(0.02, 0.1)
        out = np.maximum(out, across * along * power)
    envelope = np.sin(np.clip(y, 0, 1) * math.pi) ** 0.6     # fades at both ends
    out = np.clip(out * envelope * 255, 0, 255).astype(np.uint8)
    save_alpha(Image.fromarray(out), "LawStreak.png", (256, 1024))


# ---------- Nebula Mask: fractal noise and star clusters ----------
def nebula():
    S = 1024
    total = np.zeros((S, S))
    amp, weight = 1.0, 0.0
    for octave in range(6):
        cells = 4 * 2 ** octave
        grid = Image.fromarray((RNG.random((cells, cells)) * 255).astype(np.uint8))
        layer = np.asarray(grid.resize((S, S), Image.BICUBIC), dtype=float) / 255
        total += layer * amp
        weight += amp
        amp *= 0.55
    total /= weight
    # ridged and thresholded: wisps of gas, not uniform fog
    gas = np.clip((1 - np.abs(total - 0.5) * 2.4) ** 2.2, 0, 1)
    gas *= np.clip((total - 0.35) * 3, 0, 1) + 0.25
    # star clusters: a few centres, stars gathered round them, and some scattered
    stars = np.zeros((S, S))
    yy, xx = np.mgrid[0:S, 0:S]
    centres = RNG.uniform(0.25, 0.75, (5, 2)) * S
    points = np.concatenate([c + RNG.normal(0, S * 0.07, (220, 2)) for c in centres] + [RNG.uniform(0, S, (500, 2))])
    for px, py in points:
        if 0 <= px < S and 0 <= py < S:
            r = RNG.uniform(0.8, 2.6)
            x0, x1 = int(max(0, px - 8)), int(min(S, px + 9))
            y0, y1 = int(max(0, py - 8)), int(min(S, py + 9))
            patch = np.exp(-((xx[y0:y1, x0:x1] - px) ** 2 + (yy[y0:y1, x0:x1] - py) ** 2) / (2 * r * r))
            stars[y0:y1, x0:x1] = np.maximum(stars[y0:y1, x0:x1], patch * RNG.uniform(0.5, 1))
    mask = np.maximum(gas * 0.85, stars)
    # a soft circular edge, so a particle never shows its square
    dist = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
    mask *= np.clip((1 - dist) / 0.35, 0, 1) ** 1.5
    save_alpha(Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8)), "NebulaMask.png", (1024, 1024))


dao_runes()
law_streak()
nebula()
print("written:", sorted(os.listdir(OUT)))

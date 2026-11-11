"""The top two realms' aura textures (the owner's Tier 10 and Tier 12 brief, 2026-11-03). White
on transparent: the game tints them. Drawn at 4x and reduced for clean edges; 1024 at most, since
Roblox stores images no larger. No text in any language (the game's fixed directive): the "runes"
are original sacred geometry, trigram bars and abstract marks.

    python3 top_tier_aura_textures.py assets/aura/top_tier     (needs Pillow and numpy)

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


law_streak()
nebula()
print("written:", sorted(os.listdir(OUT)))

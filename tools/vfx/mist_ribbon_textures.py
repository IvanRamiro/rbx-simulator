"""Mist ribbons for the auras (the owner's brief, 2026-11-03): two ribbons revolving round the body,
"smooth, no edge, not flat, mist or smoke, long length". White on transparent: the game tints them.
Drawn for a Trail or Beam in Stretch mode, so the length runs left to right and the whole image
spans the ribbon once: it fades out at both ends and across its width, so no edge ever shows.

    python3 mist_ribbon_textures.py assets/aura/ribbons     (needs Pillow and numpy)

  MistRibbon.png  1024x256  the ribbon: a soft body of smoke, denser along its middle, with wisps
                            streaming along its length and curling off its sides
  MistHaze.png    1024x256  a wider, fainter veil to lay under it, so the ribbon has depth
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20261103)
W, H = 1024, 256


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(cells_x, cells_y):
    """value noise on a cells_x by cells_y grid, smoothly resized to the image"""
    grid = Image.fromarray((RNG.random((cells_y, cells_x)) * 255).astype(np.uint8))
    return np.asarray(grid.resize((W, H), Image.BICUBIC), dtype=float) / 255


def fbm(cells_x, cells_y, octaves=5):
    """fractal noise; long thin features (few cells along the length) read as smoke streaming"""
    total, amp, weight = np.zeros((H, W)), 1.0, 0.0
    for o in range(octaves):
        total += noise(cells_x * 2 ** o, cells_y * 2 ** o) * amp
        weight += amp
        amp *= 0.55
    return total / weight


x = np.linspace(0, 1, W)[None, :]
y = np.linspace(-1, 1, H)[:, None]
ends = smoothstep(0, 0.18, x) * smoothstep(1, 0.6, x)   # fades in at the head, long fade to the tail


def ribbon():
    # the smoke weaves a little across its width as it runs, and wisps peel off its sides
    warp = fbm(3, 2, 3)
    yv = y + (warp - warp.mean()) * 0.45                  # centred, so the ribbon stays on its axis
    body = np.exp(-(yv / 0.42) ** 2)                      # soft across: densest along the middle
    streaks = fbm(4, 24)                                  # long streaks along the length
    wisps = smoothstep(0.45, 0.85, fbm(6, 10)) * np.exp(-(yv / 0.75) ** 2)
    a = body * (0.35 + 0.65 * streaks) + 0.35 * wisps
    a *= 1 - smoothstep(0.7, 0.98, np.abs(y))             # nothing at the top or bottom edge
    return np.clip(a * ends * 1.15, 0, 1)


def haze():
    yv = y + (fbm(2, 2, 3) - 0.5) * 0.5
    a = np.exp(-(yv / 0.6) ** 2) * (0.55 + 0.45 * fbm(3, 8, 4))
    a *= 1 - smoothstep(0.75, 0.99, np.abs(y))
    return np.clip(a * ends * 0.7, 0, 1)


def save(alpha, name):
    rgba = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    rgba.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    rgba.save(os.path.join(OUT, name))


save(ribbon(), "MistRibbon.png")
save(haze(), "MistHaze.png")
print("written:", sorted(os.listdir(OUT)))

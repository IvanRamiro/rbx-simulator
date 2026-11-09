"""The Ember Wyrm's Bonfire flame: a looping 4x4 flipbook of one cel-shaded tongue of fire, painted in the same bands as the flames
modelled on its back (a deep orange rim, its flame orange, a yellow heart, a cream-hot core), so the bonfire its special raises reads as
more of its own fire. Real colour with real alpha: the game draws it untinted.

    blender -b --factory-startup -P tools/vfx/wyrm_particles.py     writes assets/vfx/pets/bonfire_flame.png

1024x1024, 16 frames of 256 (Roblox reads a Grid4x4 flipbook left to right, top to bottom). It loops: the noise that licks its edges is
tileable and scrolls exactly one tile up over the 16 frames, and its sway turns a whole number of times.
"""
import math
import os
import struct
import zlib

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "vfx", "pets")
FRAMES, CELL, SUPER = 16, 256, 2

RIM = np.array((232, 74, 18.0))      # the deep orange edge
FLAME = np.array((255, 122, 30.0))   # its flames (ff7a1e)
HEART = np.array((255, 208, 74.0))   # their yellow hearts (ffd04a)
HOT = np.array((255, 244, 224.0))    # the hottest core (fff4e0)


def write_png(path, rgba):
    h, w = rgba.shape[:2]
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def tile_noise(rng, size, passes):
    """Blurred white noise; np.roll wraps, so it tiles both ways."""
    n = rng.random((size, size))
    for _ in range(passes):
        n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1)) / 5
    return (n - n.min()) / (n.max() - n.min())


def sample(noise, x, y):
    """Bilinear lookup of a tiling noise at fractional texel coordinates."""
    size = noise.shape[0]
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x0, y0 = x0 % size, y0 % size
    x1, y1 = (x0 + 1) % size, (y0 + 1) % size
    top = noise[y0, x0] * (1 - fx) + noise[y0, x1] * fx
    bottom = noise[y1, x0] * (1 - fx) + noise[y1, x1] * fx
    return top * (1 - fy) + bottom * fy


def frame(f, coarse, fine):
    size = CELL * SUPER
    y, x = np.mgrid[0:size, 0:size]
    u = (x + 0.5) / size * 2 - 1            # -1 left, +1 right
    v = 1 - (y + 0.5) / size                # 0 at the bottom, 1 at the top
    phase = 2 * math.pi * f / FRAMES

    # the tongue sways more toward its tip, twice round per loop, and a ripple runs up it
    sway = (0.08 * math.sin(phase * 2) + 0.06 * np.sin(v * 6 - phase * 3)) * v ** 1.3
    # a round base (clear of the cell's foot) swelling to its widest a quarter of the way up, then drawing to a point short of the top
    t = np.clip((v - 0.05) / 0.82, 0, 1)
    width = 0.46 * np.clip(np.sin(np.pi * t ** 0.55), 0, 1) ** 0.75

    # the licking: tiling noise scrolled up one whole tile (coarse) and two (fine) per loop; broad licks, ragged toward the tip, calm at the base
    scroll = f / FRAMES
    n = coarse.shape[0]
    lick = sample(coarse, (u * 0.5 + 0.5) * n * 0.35, (v * 0.55 + scroll) * n) - 0.5
    lick += 0.22 * (sample(fine, (u * 0.5 + 0.5) * n * 0.8, (v * 1.1 + 2 * scroll) * n) - 0.5)
    ragged = 0.1 + 1.0 * smooth(0.12, 0.9, v)

    body = 1 - np.abs(u - sway) / (width + 0.02) + lick * ragged * 1.7
    body = np.where(width > 0.004, body, np.minimum(body, -1))   # nothing past its tip or below its base

    # the heart sits low and fat in the tongue, flickering in height: the same field, shorter and calmer
    reach = 0.6 + 0.06 * math.sin(phase * 2 + 1.1) + 0.04 * math.sin(phase * 3)
    core = 1 - np.abs(u - sway * 0.8) / (width * 0.6 + 0.01) + lick * 0.8 * ragged - smooth(0.2, reach, v) * 1.1
    core -= (1 - smooth(0.06, 0.2, v)) * 0.9                         # (seated above the rim at its foot, not cut by it)

    aa = 0.035
    edge = smooth(0.0, 0.03, v) * (1 - smooth(0.96, 0.995, v)) * (1 - smooth(0.95, 0.995, np.abs(u)))   # (no texel at a cell's border)
    alpha = smooth(0.0, aa, body) * edge
    col = RIM[None, None] * np.ones((size, size, 1))
    for band, colour in ((smooth(0.3, 0.3 + aa, body), FLAME), (smooth(0.2, 0.2 + aa, core), HEART), (smooth(0.62, 0.62 + aa, core), HOT)):
        col = col * (1 - band[..., None]) + colour * band[..., None]

    rgba = np.dstack((col, alpha * 255))
    # down to the cell with a box filter (clean edges)
    # (the clear texels keep the rim's colour, not black, so no dark fringe shows once Roblox filters the edge)
    return rgba.reshape(CELL, SUPER, CELL, SUPER, 4).mean(axis=(1, 3))


def flipbook():
    rng = np.random.default_rng(20261110)
    coarse = tile_noise(rng, 64, 6)
    fine = tile_noise(rng, 64, 3)
    sheet = np.zeros((CELL * 4, CELL * 4, 4))
    for f in range(FRAMES):
        r, c = divmod(f, 4)
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = frame(f, coarse, fine)
    return np.clip(np.round(sheet), 0, 255).astype(np.uint8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write_png(os.path.join(OUT, "bonfire_flame.png"), flipbook())
    print("written", os.path.abspath(os.path.join(OUT, "bonfire_flame.png")))

"""The Jade Wyrm Turtle's two particle textures, painted: a plum petal and a chip of jade rock. White-free, with real alpha, lit by the world.

    blender -b --factory-startup -P tools/vfx/turtle_particles.py     writes assets/vfx/pets/plum_petal.png and jade_chip.png
"""
import math
import os
import struct
import zlib

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "vfx", "pets")


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


def blur_noise(rng, size, passes):
    n = rng.random((size, size))
    for _ in range(passes):
        n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1)) / 5
    return (n - n.min()) / (n.max() - n.min())


def petal(size=128):
    """A plum petal: broad and round with a small notch at the tip, narrowing to its base; deep pink at the base, pale at the edge, with faint veins."""
    y, x = np.mgrid[0:size, 0:size]
    u = (x + 0.5) / size * 2 - 1
    v = (y + 0.5) / size * 2 - 1      # -1 at the tip, +1 at the base
    along = (v + 1) / 2
    half_width = 0.82 * np.sqrt(np.clip(np.sin(np.pi * np.clip(along * 0.86 + 0.09, 0, 1)), 0, 1)) * (1 - 0.3 * along ** 3)
    inside = np.abs(u) / (half_width + 1e-6)
    notch = 0.12 * np.exp(-(u / 0.13) ** 2)
    alpha = (1 - smooth(0.9, 1.0, inside)) * smooth(-0.92 + notch, -0.84 + notch, v) * (1 - smooth(0.9, 0.98, v))
    pale, pink, deep = np.array((255, 236, 240.0)), np.array((250, 176, 200.0)), np.array((196, 74, 122.0))
    t = smooth(0.25, 1.0, along)[..., None]
    col = pale * (1 - t) + pink * t
    base = smooth(0.72, 1.0, along)[..., None]
    col = col * (1 - base) + deep * base
    veins = 0.5 + 0.5 * np.cos(np.arctan2(u, (1.4 - along)) * 34)
    col = col * (1 - 0.07 * veins[..., None] * (1 - smooth(0.0, 0.8, inside))[..., None])
    return np.dstack((np.clip(col, 0, 255), alpha * 255)).astype(np.uint8)


def chip(size=64):
    """An angular flake of rock, jade on one face and pale where it broke."""
    rng = np.random.default_rng(5)
    y, x = np.mgrid[0:size, 0:size]
    u = (x + 0.5) / size * 2 - 1
    v = (y + 0.5) / size * 2 - 1
    corners = [(0.75, -0.2), (0.25, -0.82), (-0.55, -0.6), (-0.85, 0.2), (-0.2, 0.8), (0.55, 0.55)]
    inside = np.ones_like(u)
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        inside = np.minimum(inside, ((bx - ax) * (v - ay) - (by - ay) * (u - ax)) * -8)
    alpha = smooth(0.0, 0.35, inside)
    n = blur_noise(rng, size, 3)
    light = np.clip(0.55 + 0.5 * (u * 0.6 - v * 0.7), 0, 1)
    col = (np.array((22, 92, 72.0)) * (1 - n[..., None] * 0.6) + np.array((126, 186, 150.0)) * n[..., None] * 0.6) * (0.6 + 0.6 * light[..., None])
    return np.dstack((np.clip(col, 0, 255), alpha * 255)).astype(np.uint8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write_png(os.path.join(OUT, "plum_petal.png"), petal())
    write_png(os.path.join(OUT, "jade_chip.png"), chip())
    print("written", os.path.abspath(OUT))

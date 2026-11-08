"""The Nebula Owl's new star, painted: a soft hot core in a violet halo with six fine, uneven rays, as a real star shows through a lens. White on black with real alpha; the game adds light with it.

    blender -b --factory-startup -P tools/vfx/owl_particles.py     writes assets/vfx/pets/new_star.png
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


def new_star(size=256):
    y, x = np.mgrid[0:size, 0:size]
    u = (x + 0.5) / size * 2 - 1
    v = (y + 0.5) / size * 2 - 1
    r = np.sqrt(u * u + v * v)
    core = np.exp(-(r / 0.055) ** 2)
    halo = np.exp(-(r / 0.26) ** 1.6) * 0.42
    rays = np.zeros_like(r)
    for th, length, width in ((0.35, 0.92, 0.012), (1.42, 0.60, 0.010), (2.46, 0.82, 0.012), (3.50, 0.66, 0.010), (4.53, 0.95, 0.012), (5.60, 0.56, 0.010)):
        along = u * math.cos(th) + v * math.sin(th)
        across = -u * math.sin(th) + v * math.cos(th)
        rays += np.exp(-(across / (width * (1 + 3.5 * np.maximum(along, 0)))) ** 2) * np.exp(-np.maximum(along, 0) / (length * 0.34)) * (along > 0)
    light = np.clip(core + halo + rays * 0.8, 0, 1) * (1 - np.clip((r - 0.86) / 0.14, 0, 1))
    # hot white at the core, violet in the halo; the Color property tints the rest
    t = np.clip(core * 1.4 + rays * 0.6, 0, 1)[..., None]
    col = np.array((205, 170, 255.0)) * (1 - t) + np.array((255, 250, 240.0)) * t
    return np.dstack((col, light * 255)).astype(np.uint8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write_png(os.path.join(OUT, "new_star.png"), new_star())
    print("written", os.path.abspath(OUT))

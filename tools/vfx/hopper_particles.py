"""The Lunar Hopper's particle sprite, painted: a little crescent moon of light, for the ring of moons its Moon Elixir runs out across the ground and
the motes that rise from it. Real colour with real alpha: the game draws it untinted (or tints it a shade).

    blender -b --factory-startup -P tools/vfx/hopper_particles.py     writes assets/vfx/pets/moon_crescent.png

256x256: a crescent opening up and to its right (as the one on its brow), a white-hot inner edge going to moonlight blue at its outer rim, and a soft
blue glow round it that fades to nothing before the edge of the image.
"""
import os
import struct
import zlib

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "vfx", "pets")
SIZE, SUPER = 256, 3

CORE = np.array((255, 255, 255.0))
MOON = np.array((214, 232, 255.0))
RIM = np.array((143, 188, 255.0))          # its crescent's own blue (8fbcff)
HALO = np.array((120, 170, 255.0))


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


def crescent():
    n = SIZE * SUPER
    y, x = np.mgrid[0:n, 0:n]
    u = (x + 0.5) / n * 2 - 1
    v = 1 - (y + 0.5) / n * 2                      # up is +v
    # the moon's disc, less a second disc offset up and to its right: a crescent opening that way
    r_moon = 0.56
    d_moon = np.hypot(u + 0.04, v + 0.02)
    cx, cy = 0.27, 0.2
    d_bite = np.hypot(u - cx, v - cy)
    r_bite = 0.47
    inside = np.minimum(r_moon - d_moon, d_bite - r_bite)       # > 0 within the crescent
    aa = 2.0 / n
    body = smooth(-aa, aa, inside)
    # colour: white-hot along the inner (bitten) edge, going to blue at its outer rim
    toward_rim = smooth(0.0, 0.1, r_moon - d_moon)                 # 0 at the outer rim
    toward_bite = smooth(0.0, 0.12, d_bite - r_bite)               # 0 at the inner edge
    hot = (1 - toward_bite) * 0.9
    col = RIM[None, None] + (MOON - RIM)[None, None] * toward_rim[..., None]
    col = col + (CORE - col) * hot[..., None]
    # its soft glow round it
    dist = np.maximum(-inside, 0)
    glow = np.exp(-(dist / 0.09) ** 2) * 0.55 * (1 - smooth(0.82, 0.98, np.hypot(u, v)))
    alpha = np.maximum(body, glow)
    col = col * body[..., None] + HALO[None, None] * (1 - body[..., None])
    rgba = np.dstack((col, alpha * 255))
    rgba = rgba.reshape(SIZE, SUPER, SIZE, SUPER, 4).mean(axis=(1, 3))
    return np.clip(np.round(rgba), 0, 255).astype(np.uint8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write_png(os.path.join(OUT, "moon_crescent.png"), crescent())
    print("written", os.path.abspath(os.path.join(OUT, "moon_crescent.png")))

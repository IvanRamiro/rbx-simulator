"""The Realm 6 (Immortal) celestial halos' textures, painted from scratch: the bands the halos' curved Beam segments are drawn
with, and the glint their particles show. Greyscale light with real alpha: the game tints them (Beam.Color, ParticleEmitter.Color).

    python3 tools/vfx/realm6_halo_textures.py        (numpy only; Blender's Python works too)
    writes assets/aura/realm6_halos/*.png

Beam textures are upright (a Beam lays a texture's vertical axis along its length) and symmetric end to end and side to side,
so a segment looks the same whichever way round it runs. Each tapers to a point at both ends with clear padding beyond (a
Beam's far end bleeds round to its near one): a ring of segments reads as one line pinched at its joints, not a stack of bars.

    CrownBand      64x512   a fine bright line with a soft glow either side: the crown halo
    GraduatedBand  128x512  a finer line crossed by evenly spaced ticks, every fourth one longer: the graduated ring
    OrbitBand      64x512   a faint thread strung with three round beads of light: the tilted orbit
    Glint          256x256  a four-point star with a small soft core and shorter diagonal rays, gone well inside its edge

No letters or symbols: lines, ticks, beads and a star only.
"""
import os
import struct
import zlib

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "aura", "realm6_halos")
SUPER = 3


def write_png(path, rgba):
    h, w = rgba.shape[:2]
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def save(name, lum, alpha, size):
    w, h = size
    lum = lum.reshape(h, SUPER, w, SUPER).mean(axis=(1, 3))
    alpha = alpha.reshape(h, SUPER, w, SUPER).mean(axis=(1, 3))
    rgba = np.zeros((h, w, 4), np.uint8)
    v = np.clip(lum * 255.0 + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 0] = v
    rgba[..., 1] = v
    rgba[..., 2] = v
    rgba[..., 3] = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    rgba[rgba[..., 3] == 0, :3] = 0
    write_png(os.path.join(OUT, name + ".png"), rgba)


def band_grid(size, pad):
    """x across (-1..1), s along (0..1 inside the padding), and the taper (0 at both tips, 1 along the middle)."""
    w, h = size
    W, H, P = w * SUPER, h * SUPER, pad * SUPER
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    x = (xs - W / 2.0) / (W / 2.0)
    s = (ys - P) / (H - 2 * P)
    inside = (s >= 0.0) & (s <= 1.0)
    taper = np.sqrt(smoothstep(0.0, 0.09, s) * smoothstep(1.0, 0.91, s)) * inside
    return x, s, taper, inside, h


def line(x, taper, core, glow, glow_share):
    """A line whose core and glow narrow to nothing at the tips."""
    t = np.maximum(taper, 1e-4)
    c = np.exp(-((x / (core * t)) ** 2)) * (taper > 0)
    g = np.exp(-((x / (glow * t)) ** 2)) * glow_share * (taper > 0)
    return c, g


def crown_band():
    x, s, taper, inside, h = band_grid((64, 512), 16)
    c, g = line(x, taper, 0.12, 0.5, 0.4)
    alpha = np.clip(c * 0.95 + g, 0, 1) * (1.0 - smoothstep(0.85, 1.0, np.abs(x)))
    lum = 0.8 + 0.2 * c
    save("CrownBand", lum, alpha, (64, 512))


def graduated_band():
    x, s, taper, inside, h = band_grid((128, 512), 16)
    c, g = line(x, taper, 0.05, 0.22, 0.3)
    # ticks: 16 along the segment, every fourth reaching farther, each a thin bar across the line
    n = 16
    phase = s * n
    k = np.round(phase)
    d = np.abs(phase - k) * (1.0 / n) * (512 * SUPER)  # distance to the nearest tick along the band, in pixels
    long_tick = (k % 4) == 0
    reach = np.where(long_tick, 0.78, 0.42) * np.maximum(taper, 0)
    tick_w = 1.3 * SUPER
    ticks = np.exp(-((d / tick_w) ** 2)) * (1.0 - smoothstep(reach - 0.08, reach, np.abs(x))) * ((k > 0) & (k < n))
    ticks = ticks * np.where(long_tick, 1.0, 0.7)
    alpha = np.clip(c * 0.95 + g + ticks * 0.85, 0, 1) * (1.0 - smoothstep(0.9, 1.0, np.abs(x)))
    lum = 0.8 + 0.2 * np.maximum(c, ticks)
    save("GraduatedBand", lum, alpha, (128, 512))


def orbit_band():
    x, s, taper, inside, h = band_grid((64, 512), 16)
    c, g = line(x, taper, 0.07, 0.3, 0.25)
    thread = c * 0.6 + g * 0.6
    # three beads, round on the beam (the beam is laid 8 times longer than it is wide: the texture's 64:512)
    beads = np.zeros_like(x)
    for at in (0.25, 0.5, 0.75):
        dy = (s - at) * 8.0  # in units of the band's half-width x 0.5... both axes in half-widths
        r = np.sqrt(x ** 2 + (dy * 2.0) ** 2)
        beads = np.maximum(beads, np.exp(-((r / 0.42) ** 2)) + np.exp(-((r / 0.9) ** 2)) * 0.3)
    alpha = np.clip(thread + beads, 0, 1) * inside * (1.0 - smoothstep(0.9, 1.0, np.abs(x)))
    lum = 0.8 + 0.2 * np.clip(beads, 0, 1)
    save("OrbitBand", lum, alpha, (64, 512))


def glint(size=256):
    S = size * SUPER
    ys, xs = (np.mgrid[0:S, 0:S].astype(np.float64) + 0.5) / S - 0.5
    r = np.sqrt(xs ** 2 + ys ** 2)

    def ray(u, v, length, thick):
        return np.exp(-((v / (thick * (1.0 - np.clip(np.abs(u) / length, 0, 1)) + 1e-4)) ** 2)) * (1.0 - smoothstep(0.0, length, np.abs(u)))

    main = np.maximum(ray(xs, ys, 0.42, 0.016), ray(ys, xs, 0.42, 0.016))
    d1, d2 = (xs + ys) / np.sqrt(2), (xs - ys) / np.sqrt(2)
    diag = np.maximum(ray(d1, d2, 0.16, 0.01), ray(d2, d1, 0.16, 0.01)) * 0.55
    core = np.exp(-((r / 0.035) ** 2))
    halo = np.exp(-((r / 0.11) ** 2)) * 0.28
    window = 1.0 - smoothstep(0.4, 0.48, r)
    alpha = np.clip(np.maximum(main, diag) + core + halo, 0, 1) * window
    lum = np.clip(0.85 + 0.15 * (core + main), 0, 1)
    save("Glint", lum, alpha, (size, size))


def main():
    os.makedirs(OUT, exist_ok=True)
    crown_band()
    graduated_band()
    orbit_band()
    glint()
    for name in sorted(os.listdir(OUT)):
        print(name, os.path.getsize(os.path.join(OUT, name)))


main()

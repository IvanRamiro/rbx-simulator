"""The Realm 6 (Immortal) wings' textures, painted from scratch: feathers for the Beams that build the wings, and the sprites for
their ParticleEmitters. Greyscale light with real alpha: the game tints every one (Beam.Color, ParticleEmitter.Color).

    python3 tools/vfx/realm6_wing_textures.py        (numpy only; Blender's Python works too: blender -b --factory-startup -P ...)
    writes assets/aura/realm6_wings/*.png

Beam textures are upright: a Beam lays a texture's vertical axis along its length. Each feather's quill is at the BOTTOM of
its image and its tip at the top, with clear padding at both ends (a Beam's far end bleeds round to its near one).

    PrimaryA, PrimaryB   256x1024  the long flight feathers of the hand: a narrow leading vane with a notch two thirds out,
                                   a broad trailing vane, a rounded tip, a few splits between the barbs (A and B differ)
    Secondary            256x768   the forearm's flight feathers: broad, both vanes nearly equal, a blunt round tip
    Covert               256x512   the short overlapping feathers over the wing's base: round, soft and downy at the root
    ShedFeather          256x256   a small loose feather, lying at an angle, for the feathers that drift off the wing
    LightPlume           256x256   a feather shape made of light, soft-edged, for the light streaming off the wingtips

Every feather has a lit rim (the vane's edge brighter and more solid than its middle): the "luminous" in luminous wings comes
from the edges, so feathers stacked on each other don't add up to a white sheet. No letters or symbols anywhere.
"""
import math
import os
import struct
import zlib

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "aura", "realm6_wings")
SUPER = 3  # drawn at 3x and averaged down: clean edges


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


def value_noise(shape, cells, seed):
    """Smooth noise in 0..1: a random grid of cells[0] x cells[1], bilinearly interpolated to shape."""
    rng = np.random.default_rng(seed)
    grid = rng.random((cells[0] + 1, cells[1] + 1))
    ys = np.linspace(0, cells[0], shape[0], endpoint=False)
    xs = np.linspace(0, cells[1], shape[1], endpoint=False)
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = grid[y0][:, x0]
    b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]
    d = grid[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def feather(xp, yp, spec, noise):
    """One feather's light and alpha at points (xp across, yp along from the quill's end), in pixels (supersampled).

    +x is the trailing (inner) vane, -x the leading (outer) one. Returns (lum, alpha)."""
    length = spec["length"]
    aa = 1.4 * SUPER
    s = yp / length
    rachis_x = spec["curve"] * s * s
    dx = xp - rachis_x
    ad = np.abs(dx)
    inner = dx >= 0
    quill = spec["quill"]
    t = (s - quill) / (1.0 - quill)

    # the vane's half-width along it: up fast from the quill, then held, then a round tip
    rise = smoothstep(0.0, spec["rise"], t) ** 0.6
    ts = spec["tip"]
    tip = np.where(t > ts, np.sqrt(np.clip(1.0 - ((t - ts) / (1.0 - ts)) ** 2, 0.0, 1.0)), 1.0)
    w = spec["width"] * rise * tip * (1.0 - spec["taper"] * np.clip(t, 0, 1))
    notch = spec["notch"]
    w_out = w * spec["outer"] * (1.0 - notch * smoothstep(0.5, 0.6, t))
    w_in = w * (1.0 - 0.45 * notch * smoothstep(0.55, 0.65, t))
    wside = np.where(inner, w_in, w_out)
    de = wside - ad  # how far inside the vane's edge (px)
    on_vane = (t > 0.0) & (t <= 1.0)
    vane = np.clip(de / aa, 0.0, 1.0) * on_vane
    rel = ad / np.maximum(wside, 1e-3)

    # barbs: fine lines from the rachis out and toward the tip
    phase = (yp - ad * spec["slant"] * (1.0 + 0.2 * rel)) / spec["barb"]
    stripes = 0.5 + 0.5 * np.cos(2.0 * math.pi * phase)
    rim_w = spec["rim"] * SUPER
    rim = np.exp(-np.maximum(de, 0.0) / rim_w)
    lum = 0.80 + 0.06 * stripes + 0.04 * (noise - 0.5) + 0.2 * rim
    alpha = vane * (0.84 + 0.16 * rim) * (0.95 + 0.05 * stripes)

    # splits: a few gaps running along the barbs from the edge inward
    for side, at, depth in spec["splits"]:
        side_mask = inner if side > 0 else ~inner
        p0 = at * length / spec["barb"]
        g = np.clip(np.abs(phase - p0) / (1.2 + 1.6 * np.clip(rel - (1.0 - depth), 0.0, 1.0)), 0.0, 1.0)
        reach = smoothstep(1.0 - depth, 1.0 - depth + 0.3, rel)
        alpha = alpha * np.where(side_mask, 1.0 - 0.85 * reach * (1.0 - g) ** 2, 1.0)

    # the downy root: thin, wispy barbs at the vane's start
    down = smoothstep(0.0, spec["down"], t)
    alpha = alpha * (0.25 + 0.75 * down) * np.clip(1.0 - (1.0 - down) * (0.3 + 0.5 * noise), 0.0, 1.0)

    # the rachis (shaft), tapering to the tip, and the bare quill below the vane
    rr = spec["shaft"] * SUPER * (1.0 - 0.75 * np.clip(s, 0, 1))
    shaft = np.clip((rr - ad) / aa, 0.0, 1.0) * (s >= 0.0) * (1.0 - smoothstep(0.9, 0.99, s))
    quill_w = spec["shaft"] * SUPER * 1.3
    calamus = np.clip((quill_w - ad) / aa, 0.0, 1.0) * (s >= 0.0) * (s < quill + 0.01) * smoothstep(0.0, 0.015, s)
    shaft = np.maximum(shaft, calamus * 0.8)
    lum = lum * (1.0 - shaft) + 1.0 * shaft
    alpha = np.maximum(alpha, shaft * 0.95)
    inside = (s >= 0.0) & (s <= 1.0)
    return np.clip(lum, 0, 1) * inside, np.clip(alpha, 0, 1) * inside


def to_rgba(lum, alpha, size):
    """Average the supersampled image down to size (w, h) and pack it as RGBA bytes (light premultiplied in nothing)."""
    h, w = size[1], size[0]
    lum = lum.reshape(h, SUPER, w, SUPER).mean(axis=(1, 3))
    alpha = alpha.reshape(h, SUPER, w, SUPER).mean(axis=(1, 3))
    rgba = np.zeros((h, w, 4), np.uint8)
    v = np.clip(lum * 255.0 + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 0] = v
    rgba[..., 1] = v
    rgba[..., 2] = v
    rgba[..., 3] = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    rgba[rgba[..., 3] == 0, :3] = 0
    return rgba


def beam_feather(name, size, pad, spec, seed):
    w, h = size
    W, H, P = w * SUPER, h * SUPER, pad * SUPER
    spec = dict(spec)
    spec["length"] = H - 2 * P
    # centre the whole feather (both vanes) across the image
    width = spec["width"] * SUPER
    spec["width"] = width
    centre = W / 2.0 - (width - width * spec["outer"]) / 2.0
    spec["curve"] = spec["curve"] * SUPER
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    yp = (H - P) - ys  # from the quill's end at the bottom
    xp = xs - centre
    noise = value_noise((H, W), (40, 8), seed)
    lum, alpha = feather(xp, yp, spec, noise)
    rgba = to_rgba(lum, alpha, size)
    write_png(os.path.join(OUT, name + ".png"), rgba)
    return rgba


def particle_feather(name, angle, spec, seed, size=256):
    """A whole small feather lying at an angle in a square sprite, its tip up and to the right."""
    S = size * SUPER
    ys, xs = np.mgrid[0:S, 0:S].astype(np.float64) + 0.5
    cx = cy = S / 2.0
    spec = dict(spec)
    spec["length"] = spec["length"] * SUPER
    spec["width"] = spec["width"] * SUPER
    spec["curve"] = spec["curve"] * SUPER
    a = math.radians(angle)
    # along the feather: from its root (bottom left) toward its tip (top right)
    ux, uy = math.sin(a), -math.cos(a)
    rx, ry = math.cos(a), math.sin(a)
    ox, oy = cx - ux * spec["length"] / 2.0, cy - uy * spec["length"] / 2.0
    yp = (xs - ox) * ux + (ys - oy) * uy
    xp = (xs - ox) * rx + (ys - oy) * ry
    noise = value_noise((S, S), (24, 24), seed)
    lum, alpha = feather(xp, yp, spec, noise)
    rgba = to_rgba(lum, alpha, (size, size))
    write_png(os.path.join(OUT, name + ".png"), rgba)
    return rgba


def light_plume(name, size=256):
    """A feather shape made of light: soft all round, a bright core along its shaft, a faint glow round it that is fully
    gone well inside the sprite's edge (no square)."""
    S = size * SUPER
    ys, xs = (np.mgrid[0:S, 0:S].astype(np.float64) + 0.5) / S - 0.5  # -0.5..0.5, y down
    a = math.radians(32.0)
    u = xs * math.sin(a) - ys * math.cos(a)   # along, toward the tip (up right)
    v = xs * math.cos(a) + ys * math.sin(a)   # across
    half = 0.36
    s = (u + half) / (2 * half)               # 0 root .. 1 tip
    width = 0.21 * np.sqrt(np.clip(np.sin(np.clip(s, 0, 1) * math.pi), 0, 1)) * (1.0 - 0.35 * s)
    width = width * (s >= 0) * (s <= 1)
    d = np.abs(v - 0.05 * (s - 0.5) ** 2) / np.maximum(width, 1e-4)
    body = np.where(width > 0, np.exp(-(d ** 2) * 2.2), 0.0)
    core = np.exp(-(v / 0.012) ** 2) * smoothstep(0.0, 0.15, s) * (1.0 - smoothstep(0.8, 1.0, s))
    r = np.sqrt(xs ** 2 + ys ** 2)
    glow = np.exp(-(r / 0.16) ** 2) * 0.22
    window = 1.0 - smoothstep(0.36, 0.47, r)
    alpha = np.clip(np.maximum(body * 0.8, glow) + core * 0.2, 0, 1) * window
    lum = np.clip(0.8 + 0.2 * core + 0.1 * body, 0, 1)
    rgba = to_rgba(lum, alpha, (size, size))
    write_png(os.path.join(OUT, name + ".png"), rgba)
    return rgba


PRIMARY = dict(width=104, outer=0.42, quill=0.07, rise=0.16, tip=0.74, taper=0.18, notch=0.38, curve=-10, slant=0.55,
               barb=7.5 * SUPER, rim=5.0, shaft=2.4, down=0.10)
SECONDARY = dict(width=100, outer=0.78, quill=0.06, rise=0.14, tip=0.66, taper=0.08, notch=0.0, curve=-6, slant=0.45,
                 barb=7.0 * SUPER, rim=5.0, shaft=2.2, down=0.12)
COVERT = dict(width=104, outer=0.86, quill=0.03, rise=0.12, tip=0.5, taper=0.05, notch=0.0, curve=-4, slant=0.4,
              barb=6.5 * SUPER, rim=5.5, shaft=2.0, down=0.3)
SHED = dict(length=196, width=34, outer=0.8, quill=0.07, rise=0.14, tip=0.58, taper=0.1, notch=0.0, curve=-10, slant=0.45,
            barb=4.0 * SUPER, rim=2.5, shaft=1.3, down=0.3)


def main():
    os.makedirs(OUT, exist_ok=True)
    beam_feather("PrimaryA", (256, 1024), 24, dict(PRIMARY, splits=[(1, 0.44, 0.45), (-1, 0.33, 0.5)]), 11)
    beam_feather("PrimaryB", (256, 1024), 24, dict(PRIMARY, curve=-14, splits=[(1, 0.56, 0.4)]), 12)
    beam_feather("Secondary", (256, 768), 22, dict(SECONDARY, splits=[(1, 0.52, 0.35)]), 13)
    beam_feather("Covert", (256, 512), 20, dict(COVERT, splits=[]), 14)
    particle_feather("ShedFeather", 32.0, dict(SHED, splits=[(1, 0.55, 0.4)]), 15)
    light_plume("LightPlume")
    for name in sorted(os.listdir(OUT)):
        print(name, os.path.getsize(os.path.join(OUT, name)))


main()

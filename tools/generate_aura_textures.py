"""Generates the optional aura textures in assets/aura (standard library only).

    python3 tools/generate_aura_textures.py [--preview DIR]

All three textures are original, white with transparency, so Roblox can tint
them with each pet's colours. Upload them in Studio (View > Asset Manager >
Import) and paste their asset IDs into AuraStyles.CustomTextures.

--preview DIR also writes tinted previews on a dark background, for checking
the textures before uploading.
"""

import math
import os
import random
import struct
import sys
import zlib

SEED = 2026
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "aura")


# PNG writing ------------------------------------------------------------------

def write_png(path, width, height, rows, channels=4):
    """rows: list of bytearrays, each width * channels bytes (RGBA or RGB)."""
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    color_type = 6 if channels == 4 else 2

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# Noise ------------------------------------------------------------------------

def smooth(t):
    return t * t * (3 - 2 * t)


def smoothstep(edge0, edge1, x):
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return smooth(t)


class PeriodicNoise:
    """Value noise that repeats every `period` lattice cells on each axis, so
    textures tile seamlessly and animations loop."""

    def __init__(self, rng, period_x, period_y, period_z=1):
        self.px, self.py, self.pz = period_x, period_y, period_z
        self.values = [rng.random() for _ in range(period_x * period_y * period_z)]

    def _value(self, x, y, z):
        return self.values[(x % self.px) + self.px * ((y % self.py) + self.py * (z % self.pz))]

    def at(self, x, y, z=0.0):
        x0, y0, z0 = math.floor(x), math.floor(y), math.floor(z)
        tx, ty, tz = smooth(x - x0), smooth(y - y0), smooth(z - z0)
        total = 0.0
        for dz in (0, 1):
            for dy in (0, 1):
                for dx in (0, 1):
                    weight = (tx if dx else 1 - tx) * (ty if dy else 1 - ty) * (tz if dz else 1 - tz)
                    total += weight * self._value(x0 + dx, y0 + dy, z0 + dz)
        return total


class Fractal:
    """A few octaves of PeriodicNoise, each twice as detailed and still periodic."""

    def __init__(self, rng, period_x, period_y, period_z=1, octaves=3):
        self.layers = [
            PeriodicNoise(rng, period_x * 2 ** o, period_y * 2 ** o, period_z * 2 ** o if period_z > 1 else 1)
            for o in range(octaves)
        ]

    def at(self, x, y, z=0.0):
        total, amplitude, norm = 0.0, 1.0, 0.0
        for octave, layer in enumerate(self.layers):
            scale = 2 ** octave
            total += layer.at(x * scale, y * scale, z * scale if layer.pz > 1 else 0) * amplitude
            norm += amplitude
            amplitude *= 0.5
        return total / norm


def white_pixel(alpha):
    return (255, 255, 255, max(0, min(255, int(alpha * 255 + 0.5))))


# Textures ---------------------------------------------------------------------

def energy_streak(rng):
    """512x128 horizontal streaks of energy with a bright core line, for Beams
    and Trails (the texture's width runs along the beam). Tiles left to right."""
    width, height = 512, 128
    streaks = Fractal(rng, 4, 64, octaves=3)
    clumps = Fractal(rng, 3, 1, octaves=2)
    rows = []
    for py in range(height):
        v = (py + 0.5) / height
        across = math.exp(-(((v - 0.5) / 0.22) ** 2))
        core = math.exp(-(((v - 0.5) / 0.045) ** 2))
        row = bytearray()
        for px in range(width):
            u = px / width
            n = streaks.at(u * 4, v * 16)
            c = clumps.at(u * 3, 0.5)
            alpha = across * (0.25 + 0.95 * n ** 1.5) * (0.3 + 1.1 * c * c) + core * 0.8 * (0.6 + 0.4 * c)
            row.extend(white_pixel(min(1.0, alpha)))
        rows.append(row)
    return width, height, rows


def flame_flipbook(rng):
    """512x512 sheet of 16 looping flame frames (4x4 grid of 128x128), read
    left to right, top to bottom. Brighter at the core so tinting gives a hot
    centre and deeper-coloured edges."""
    size, frame_size, frames = 512, 128, 16
    turbulence = Fractal(rng, 4, 4, 4, octaves=3)
    wobble = PeriodicNoise(rng, 4, 1, 4)
    rows = [bytearray(size * 4) for _ in range(size)]
    for frame in range(frames):
        t = frame / frames
        origin_x, origin_y = (frame % 4) * frame_size, (frame // 4) * frame_size
        for fy in range(frame_size):
            # 0 at the bottom of the frame, 1 near the top (leaving a margin)
            h = (1 - (fy + 0.5) / frame_size - 0.03) / 0.9
            if h < 0 or h > 1:
                continue
            sway = 0.07 * h ** 1.5 * math.sin(2 * math.pi * (t + h * 0.8))
            sway += (wobble.at(h * 3, 0, t * 4) - 0.5) * 0.16 * h
            # The outline swells and pinches as noise rises through it
            pinch = 0.7 + 0.6 * turbulence.at(0.5, (h * 2 - t * 4) % 4, t * 4)
            half_width = 0.3 * (1 - h) ** 0.7 * (0.55 + 0.45 * smoothstep(0, 0.18, h)) * pinch
            for fx in range(frame_size):
                x = (fx + 0.5) / frame_size
                if half_width <= 0.001:
                    continue
                distance = abs(x - 0.5 - sway) / half_width
                if distance >= 1.35:
                    continue
                shape = smoothstep(1.35, 0.3, distance) * smoothstep(0, 0.06, h)
                # Noise scrolls upward through the flame and loops every 16 frames.
                # It eats into the flame mostly at the edges and towards the top,
                # so the outline and tip break into ragged tongues while the
                # body of the flame stays solid.
                noise = turbulence.at(x * 9, (h * 6 - t * 4) % 4, t * 4)
                noise = min(1.0, max(0.0, (noise - 0.5) * 1.9 + 0.5))
                erosion = 1.7 * (1 - noise) * (0.25 + 0.75 * h) * (0.25 + 0.75 * distance)
                density = smoothstep(0.05, 0.35, shape - erosion)
                if density <= 0:
                    continue
                core = smoothstep(0.7, 0.0, distance) * (1 - h) ** 0.8
                brightness = 0.4 + 0.6 * core
                index = (origin_x + fx) * 4
                row = rows[origin_y + fy]
                row[index:index + 4] = bytes((int(255 * brightness),) * 3 + (int(density * 255),))
    return size, size, rows


def soft_glow(rng):
    """128x128 soft round glow with a small bright centre."""
    size = 128
    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            dx, dy = (px + 0.5) / size - 0.5, (py + 0.5) / size - 0.5
            r = math.hypot(dx, dy)
            halo = math.exp(-(r * r) / (2 * 0.2 ** 2))
            core = math.exp(-(r * r) / (2 * 0.055 ** 2))
            alpha = (0.6 * halo + 0.9 * core) * (1 - smoothstep(0.4, 0.5, r))
            row.extend(white_pixel(min(1.0, alpha)))
        rows.append(row)
    return size, size, rows


# Previews -----------------------------------------------------------------------

def write_preview(path, width, height, rows, tint, repeat_x=1):
    """The texture tinted and composited over a dark background (RGB)."""
    background = (18, 22, 34)
    out = []
    for row in rows:
        line = bytearray()
        for _ in range(repeat_x):
            for px in range(width):
                r, g, b, a = row[px * 4:px * 4 + 4]
                alpha = a / 255
                for channel, value in enumerate((r, g, b)):
                    colored = value / 255 * tint[channel]
                    line.append(int(background[channel] * (1 - alpha) + colored * alpha))
        out.append(line)
    write_png(path, width * repeat_x, height, out, channels=3)


def main():
    preview_dir = None
    if "--preview" in sys.argv:
        preview_dir = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(preview_dir, exist_ok=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rng = random.Random(SEED)
    textures = [
        ("aura_energy_streak.png", energy_streak, (90, 200, 255), 2),
        ("aura_flame_flipbook.png", flame_flipbook, (255, 150, 50), 1),
        ("aura_soft_glow.png", soft_glow, (120, 230, 170), 1),
    ]
    for name, build, tint, repeat_x in textures:
        width, height, rows = build(rng)
        path = os.path.join(OUTPUT_DIR, name)
        write_png(path, width, height, rows)
        print(f"wrote {os.path.relpath(path)} ({width}x{height})")
        if preview_dir:
            write_preview(os.path.join(preview_dir, "preview_" + name), width, height, rows, tint, repeat_x)


if __name__ == "__main__":
    main()

"""Realm 5's silver light (2026-11-03): the owner's silver rising light beside the gold one. Our gold
textures carry their colour in the pixels, so a silver Color on them still reads gold. This is the
LightPillar's shape (ascendant_textures.py) in white with a cool silver falloff, so the emitter's
Color sets the exact silver.

    python3 ascendant_silver.py assets/aura/ascendant     (needs Pillow and numpy)

  SilverPillar.png  512  a tall thin shaft of light, white-hot core, soft silver falloff, fading at
                         both ends (FacingCameraWorldUp, Squash for height)
  SoftLine.png      64x256  a glowing line that runs the full height without fading: a hot core
                         and a soft falloff across. For Beams that join end to end (the sphere's
                         rings), so no seam shows where they meet
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(56)

WHITE = np.array([255, 255, 255], dtype=float)
SILVER = np.array([205, 218, 245], dtype=float)
STEEL = np.array([120, 135, 170], dtype=float)


def silverise(i):
    """intensity (0..~2) to RGBA: steel when faint, silver, white-hot at the core"""
    lo = np.clip(i / 0.55, 0, 1)[..., None]
    hot = np.clip((i - 0.8) / 0.7, 0, 1)[..., None]
    rgb = STEEL * (1 - lo) + SILVER * lo
    rgb = rgb * (1 - hot) + WHITE * hot
    a = np.clip(i, 0, 1)
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


N = 512
py, px = np.mgrid[0:N, 0:N].astype(float)
u = (px - N / 2) / (N / 2)
v = (py - N / 2) / (N / 2)
along = smoothstep(1.0, 0.55, np.abs(v)) * (0.85 + 0.15 * np.cos(v * 9))
streak = 0.75 + 0.25 * np.asarray(Image.fromarray((rng.random((48, 1)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), dtype=float) / 255
core = np.exp(-(u / 0.02) ** 2) * 1.8 + np.exp(-(u / 0.08) ** 2) * 0.6 + np.exp(-(u / 0.25) ** 2) * 0.2
pillar = core * along * streak * (1 - smoothstep(0.9, 1.0, np.abs(u)))
Image.fromarray(silverise(pillar)).save(os.path.join(OUT, "SilverPillar.png"))

# the soft line: the same profile at every height, so beams can tile and join seamlessly
LW, LH = 64, 256
lu = (np.mgrid[0:LH, 0:LW][1].astype(float) - LW / 2 + 0.5) / (LW / 2)
line = (np.exp(-(lu / 0.12) ** 2) * 1.6 + np.exp(-(lu / 0.45) ** 2) * 0.45) * (1 - smoothstep(0.85, 1.0, np.abs(lu)))
Image.fromarray(silverise(line)).save(os.path.join(OUT, "SoftLine.png"))
print("saved SilverPillar.png and SoftLine.png in", OUT)

"""Realm 5's smoke stream: black smoke flowing along the chains as a steady Beam (the owner, 2026-11-03:
"the black smoke is unstable, think of it as a beam"; puffs popped in and out). Drawn for a Beam:
the length runs top to bottom and tiles seamlessly (TextureMode Wrap, scrolled by TextureSpeed), the
width fades softly to nothing at both edges, and the smoke is torn into wisps along its length.
White on transparent: the Beam's Color makes it black.

    python3 ascendant_smoke_stream.py assets/aura/ascendant     (needs Pillow and numpy)

  SmokeStream.png  256x1024
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
W, H = 256, 1024
rng = np.random.default_rng(77)


def periodic_noise(cx, cy):
    """value noise on a cx by cy grid that wraps vertically (and horizontally), resized smoothly"""
    g = rng.random((cy, cx))
    big = np.tile(g, (3, 3))
    img = Image.fromarray((big * 255).astype(np.uint8)).resize((W * 3, H * 3), Image.BICUBIC)
    a = np.asarray(img, dtype=float) / 255
    return a[H:2 * H, W:2 * W]


def fbm(cx, cy, octaves=5):
    tot, amp, w = np.zeros((H, W)), 1.0, 0.0
    for o in range(octaves):
        tot += periodic_noise(cx * 2 ** o, cy * 2 ** o) * amp
        w += amp
        amp *= 0.55
    return tot / w


x = np.linspace(-1, 1, W)[None, :]
# the stream weaves across its width as it runs, wisps torn along it
warp = (fbm(2, 3, 3) - 0.5) * 0.6
xs = x + warp
body = np.exp(-(xs / 0.42) ** 2)
streaks = fbm(6, 3)                       # long streaks along the length (few cells down, more across)
torn = np.clip((fbm(4, 6) - 0.32) * 2.2, 0, 1)
a = body * (0.35 + 0.75 * streaks) * (0.4 + 0.6 * torn)
a *= 1 - np.clip((np.abs(x) - 0.75) / 0.23, 0, 1)   # nothing at the side edges
a = np.clip(a * 1.35, 0, 1)

rgba = np.zeros((H, W, 4), dtype=np.uint8)
rgba[..., :3] = 255
rgba[..., 3] = (a * 255).astype(np.uint8)
Image.fromarray(rgba).save(os.path.join(OUT, "SmokeStream.png"))
# preview: tiled twice, dark smoke on a light ground (to check the seam and the shape)
t = np.vstack([a, a])
prev = (220 - t * 200).astype(np.uint8)
Image.fromarray(prev).save(os.path.join(OUT, "SmokeStream_preview.png"))
print("written")

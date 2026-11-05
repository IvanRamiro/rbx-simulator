"""The hoof spark texture: one hot streak, for particles turned along their velocity. Needs Pillow and numpy.

    python spark_texture.py <out folder>
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SIZE = 256

y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
u, v = x / (SIZE - 1) * 2 - 1, y / (SIZE - 1) * 2 - 1
alpha = np.clip(np.exp(-(u / 0.05) ** 2) * np.clip(1 - np.abs(v), 0, 1) ** 1.4, 0, 1)
one = np.ones_like(alpha)
os.makedirs(OUT, exist_ok=True)
Image.fromarray((np.dstack((one, one, one, alpha)) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "spark.png"))

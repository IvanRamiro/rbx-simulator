"""The Realm 6 magic circle's texture: the owner's chosen design, Creator Store decal 107338734690539 (Aogame12381), with its
white background cut away (the owner's choice, option B, 2026-11-11). On an additive Beam black adds no light and white
glows, so the decal's white outside would glow as a full square; cut to black and clear, only the seal shows.

    python3 tools/vfx/realm6_circle_cutout.py        (needs Pillow and numpy; downloads the decal's 700 px thumbnail)
    writes assets/aura/realm6_circle/MagicCircle.png  (1024 x 1024, the outside black and transparent)

The cut is a flood fill from the four corners through near-pure white only (luminance above 253), so it stops at the
seal's thin outer outline even where the thumbnail's antialiasing greys it; everything inside the seal is untouched.
"""
import json
import os
import urllib.request
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

DECAL = 107338734690539
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "aura", "realm6_circle")
THRESHOLD = 253


def main():
    url = "https://thumbnails.roblox.com/v1/assets?assetIds=%d&returnPolicy=PlaceHolder&size=700x700&format=Png" % DECAL
    image_url = json.load(urllib.request.urlopen(url, timeout=30))["data"][0]["imageUrl"]
    raw = urllib.request.urlopen(image_url, timeout=30).read()
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "decal_700.png")
    with open(src, "wb") as f:
        f.write(raw)
    a = np.asarray(Image.open(src).convert("RGBA")).astype(np.int32)
    h, w = a.shape[:2]
    light = a[..., :3].mean(axis=2) > THRESHOLD
    outside = np.zeros((h, w), bool)
    queue = deque([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    while queue:
        y, x = queue.popleft()
        if y < 0 or x < 0 or y >= h or x >= w or outside[y, x] or not light[y, x]:
            continue
        outside[y, x] = True
        queue.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    grown = np.asarray(Image.fromarray((outside * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    out = a.copy()
    out[grown, 0:3] = 0
    out[grown, 3] = 0
    Image.fromarray(out.astype(np.uint8), "RGBA").resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, "MagicCircle.png"))
    os.remove(src)
    print("outside share %.3f; wrote %s" % (outside.mean(), os.path.join(OUT, "MagicCircle.png")))


main()

"""The game icon (Steal a Spirit Egg): a square crop of a real Play screenshot with the same light grade as the thumbnail.

    python3 tools/ui/icon.py <out.png>      (needs numpy and Pillow)

The shot is assets/ui/thumbnail/icon_shot.jpg: a real Play capture (test save) of the player in the Murim Robes carrying
the Inferno Egg toward the camera, the enraged Ember Xuanwu behind, nothing painted in. No title: the icon is always shown
next to the game's name, and text is unreadable at icon sizes. Roblox wants a square image (1024x1024 is fine).
"""
import os
import sys
import numpy as np
from PIL import Image, ImageFilter

OUT = sys.argv[1]
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "ui", "thumbnail", "icon_shot.jpg")
S = 1024
CENTRE_X = 0.565  # the egg and the face, as a share of the shot's width

# ---------- the square: the full height of the shot, centred on the player ----------
shot = Image.open(SHOT).convert("RGB")
side = shot.height
left = round(min(max(shot.width * CENTRE_X - side / 2, 0), shot.width - side))
img = shot.crop((left, 0, left + side, side)).resize((S, S), Image.LANCZOS)

# ---------- the thumbnail's grade: a little contrast, cool shadows, warm highlights, a soft vignette ----------
a = np.asarray(img).astype(np.float32) / 255.0
lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
a = np.clip((a - 0.5) * 1.08 + 0.5, 0, 1)
shadow = np.clip(1 - lum * 1.8, 0, 1)[..., None]
light = np.clip((lum - 0.55) * 2.2, 0, 1)[..., None]
a = a + shadow * np.array([-0.012, 0.0, 0.025]) + light * np.array([0.03, 0.012, -0.02])
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt(((xx - S * 0.5) / (S * 0.6)) ** 2 + ((yy - S * 0.55) / (S * 0.62)) ** 2)
a *= (1 - 0.34 * np.clip(r - 0.5, 0, 1) ** 1.5)[..., None]
img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=50, threshold=2))
img.save(OUT)
print("saved", OUT, img.size)

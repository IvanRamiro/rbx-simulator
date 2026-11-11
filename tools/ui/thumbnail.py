"""The game thumbnail (Steal a Spirit Egg): a real Play screenshot, a light grade, and the title in the game's own fonts.

    python3 tools/ui/thumbnail.py <fonts dir> <out.jpg>      (needs numpy and Pillow)

The shot is assets/ui/thumbnail/egg_heist_shot.jpg: a real Play capture (test save) of the player carrying the Inferno Egg
away from the enraged Ember Xuanwu at Ember Peak, nothing painted in. The fonts are the UI's (UiTheme): Merriweather and
Montserrat from Google Fonts (OFL), saved in <fonts dir> as merri.ttf and mont.ttf (the variable fonts from
github.com/google/fonts, ofl/merriweather and ofl/montserrat). Roblox wants 1920x1080.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = sys.argv[1]
OUT = sys.argv[2]
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "ui", "thumbnail", "egg_heist_shot.jpg")
W, H = 1920, 1080

# ---------- the shot: scaled to fill 1080 tall, cropped so the runner sits right of centre ----------
shot = Image.open(SHOT).convert("RGB")
s = H / shot.height
shot = shot.resize((round(shot.width * s), H), Image.LANCZOS)
left = 60
img = shot.crop((left, 0, left + W, H))

# ---------- a light grade: a little contrast, cool shadows, warm highlights, a soft vignette ----------
a = np.asarray(img).astype(np.float32) / 255.0
lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
a = np.clip((a - 0.5) * 1.07 + 0.5, 0, 1)                      # contrast
shadow = np.clip(1 - lum * 1.8, 0, 1)[..., None]
light = np.clip((lum - 0.55) * 2.2, 0, 1)[..., None]
a = a + shadow * np.array([-0.012, 0.0, 0.025]) + light * np.array([0.03, 0.012, -0.02])
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W * 0.56) / (W * 0.62)) ** 2 + ((yy - H * 0.55) / (H * 0.68)) ** 2)
a *= (1 - 0.32 * np.clip(r - 0.55, 0, 1) ** 1.6)[..., None]     # vignette
img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))

# ---------- the title ----------
def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_name(weight)
    return f

small = font(f"{D}/mont.ttf", 64, "ExtraBold")
big = font(f"{D}/merri.ttf", 158, "Black")
CREAM = (255, 238, 196)
GOLD = (255, 196, 92)
INK = (28, 16, 12)

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
x0, y0 = 92, 74


def tracked(draw, xy, text, f, fill, track, stroke=0, stroke_fill=None):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += draw.textlength(ch, font=f) + track
    return x


for target, offset, fill, stroke_fill in ((shadow, (6, 9), (0, 0, 0, 150), (0, 0, 0, 150)), (layer, (0, 0), None, INK)):
    d = ImageDraw.Draw(target)
    ox, oy = offset
    tracked(d, (x0 + 6 + ox, y0 + oy), "STEAL A", small, fill or GOLD, 10, stroke=6, stroke_fill=stroke_fill)
    d.text((x0 + ox, y0 + 70 + oy), "SPIRIT", font=big, fill=fill or CREAM, stroke_width=9, stroke_fill=stroke_fill)
    d.text((x0 + ox, y0 + 70 + 168 + oy), "EGG", font=big, fill=fill or CREAM, stroke_width=9, stroke_fill=stroke_fill)
shadow = shadow.filter(ImageFilter.GaussianBlur(10))

out = img.convert("RGBA")
out.alpha_composite(shadow)
out.alpha_composite(layer)
out.convert("RGB").save(OUT, quality=95)
print("saved", OUT, out.size)

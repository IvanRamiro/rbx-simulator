"""The game thumbnail (Eggbound: Cultivation Realms): the key art with the title in the game's own fonts on top.

    python3 tools/ui/thumbnail.py <fonts dir> <out.jpg>      (needs numpy and Pillow)

The art is assets/ui/thumbnail/art_thumbnail.png (AI-generated, with the owner's permission; the file keeps its content-credential metadata): a blocky Roblox avatar in white and gold robes carrying a glowing lava egg, chased by an obsidian-and-gold phoenix-roc
(the owner, 2026-11-24: "use roblox character not a human figure"). It has no text in it, so the title is set here. It leaves the left third calm; a soft dark scrim behind the title
keeps it readable. The icon is assets/ui/thumbnail/Eggbound_icon_1024.png (no text on an icon). The fonts are the UI's (UiTheme): Merriweather and Montserrat from Google Fonts (OFL),
saved in <fonts dir> as merri.ttf and mont.ttf (the variable fonts from github.com/google/fonts, ofl/merriweather and ofl/montserrat). Roblox wants 1920x1080.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = sys.argv[1]
OUT = sys.argv[2]
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "ui", "thumbnail", "art_thumbnail.png")
W, H = 1920, 1080

# ---------- the shot: scaled to cover 1920x1080, cropped from the middle ----------
shot = Image.open(SHOT).convert("RGB")
s = max(W / shot.width, H / shot.height)
shot = shot.resize((round(shot.width * s), round(shot.height * s)), Image.LANCZOS)
left = (shot.width - W) // 2
top = (shot.height - H) // 2
img = shot.crop((left, top, left + W, top + H))

# ---------- a soft dark scrim behind the title (left, top to middle), so the letters read over any art ----------
a = np.asarray(img).astype(np.float32) / 255.0
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
scrim = np.clip(1 - np.sqrt(((xx - W * 0.12) / (W * 0.46)) ** 2 + ((yy - H * 0.33) / (H * 0.62)) ** 2), 0, 1) ** 1.3 * 0.5
a *= (1 - scrim)[..., None]
img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))  # (the art is 1536 wide: this keeps the upscale crisp)

# ---------- the title ----------
def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_name(weight)
    return f

small = font(f"{D}/mont.ttf", 50, "ExtraBold")
big = font(f"{D}/merri.ttf", 134, "Black")
CREAM = (255, 238, 196)
GOLD = (255, 196, 92)
INK = (28, 16, 12)

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
x0, y0 = 92, 96


def tracked(draw, xy, text, f, fill, track, stroke=0, stroke_fill=None):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += draw.textlength(ch, font=f) + track
    return x


# the name (the owner's pick, 2026-11-24, because the earlier title was too close to a big game's): EGGBOUND large, CULTIVATION REALMS under it
for target, offset, fill, stroke_fill in ((shadow, (6, 9), (0, 0, 0, 150), (0, 0, 0, 150)), (layer, (0, 0), None, INK)):
    d = ImageDraw.Draw(target)
    ox, oy = offset
    d.text((x0 + ox, y0 + oy), "EGGBOUND", font=big, fill=fill or CREAM, stroke_width=9, stroke_fill=stroke_fill)
    tracked(d, (x0 + 8 + ox, y0 + 160 + oy), "CULTIVATION REALMS", small, fill or GOLD, 7, stroke=6, stroke_fill=stroke_fill)
shadow = shadow.filter(ImageFilter.GaussianBlur(10))

out = img.convert("RGBA")
out.alpha_composite(shadow)
out.alpha_composite(layer)
out.convert("RGB").save(OUT, quality=95)
print("saved", OUT, out.size)

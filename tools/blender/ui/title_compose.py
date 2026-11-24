"""Turns title_banner.py's two renders into the game's layers, and a review image. Needs Pillow and numpy.

    python title_compose.py <render folder> <name, e.g. title_tier4_full> [--tint 0.62 0.45 1.0] [--out <folder for the layers>]

  <name>_steel.png   the metal and lacquer, RGBA as rendered
  <name>_light.png   the glow, as RGBA: its alpha is how bright it is, its colour white-hot to pale so the game can tint it (ImageColor3), plus a soft bloom
  <name>_review.png  both over a dark and a bright background, the light tinted, to judge the banner by (never shipped)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

folder, name = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
tint = tuple(float(v) for v in args[args.index("--tint") + 1:args.index("--tint") + 4]) if "--tint" in args else (0.62, 0.45, 1.0)
out = args[args.index("--out") + 1] if "--out" in args else folder
os.makedirs(out, exist_ok=True)

steel = Image.open(os.path.join(folder, name + "_steel.png")).convert("RGBA")
lit = np.asarray(Image.open(os.path.join(folder, name + "_light.png")).convert("RGBA"), dtype=np.float32) / 255.0
light = lit[..., :3] * lit[..., 3:4]


def blur(arr, radius):
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(img, dtype=np.float32) / 255.0


# the glow's strength: its brightest channel; its bloom: that, blurred at three radii, added
core = np.clip(light.max(axis=2) * 1.15, 0, 1)
bloom = np.clip(core + 0.55 * blur(core, 5) + 0.45 * blur(core, 16) + 0.35 * blur(core, 48), 0, 1)
# the layer's colour: white where it is hottest, so a tint (ImageColor3) gives a hot white core in the title's colour and a coloured halo
white = np.ones_like(core)
layer = np.dstack((white, white, white, bloom))
light_img = Image.fromarray((layer * 255).astype(np.uint8), "RGBA")
steel.save(os.path.join(out, name + "_steel.png"))
light_img.save(os.path.join(out, name + "_light.png"))


def over(bg, fg):
    return Image.alpha_composite(bg, fg)


def tinted_light():
    rgb = np.dstack([white * c for c in tint])
    hot = np.clip(core[..., None] * 1.0, 0, 1)
    colour = rgb * (1 - hot) + np.ones_like(rgb) * hot  # white-hot where the glow is strongest, the tint round it
    return Image.fromarray((np.dstack((colour, bloom)) * 255).astype(np.uint8), "RGBA")


def background(top, bottom):
    w, h = steel.size
    ramp = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top)[None, None, :] * (1 - ramp) + np.array(bottom)[None, None, :] * ramp
    arr = np.broadcast_to(arr, (h, w, 3))
    return Image.fromarray(np.dstack((arr, np.full((h, w), 255))).astype(np.uint8), "RGBA")


glow = tinted_light()
SAMPLE = args[args.index("--text") + 1] if "--text" in args else None
panels = []
for top, bottom in (((10, 12, 28), (24, 26, 56)), ((120, 170, 215), (170, 205, 150))):
    panel = over(background(top, bottom), steel)
    panel = over(panel, glow)
    if SAMPLE:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(panel)
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 118)
        box = draw.textbbox((0, 0), SAMPLE, font=font)
        pos = ((panel.width - (box[2] - box[0])) // 2, panel.height // 2 - (box[3] - box[1]) // 2 - box[1] - 6)
        draw.text((pos[0] + 4, pos[1] + 5), SAMPLE, font=font, fill=(40, 10, 20, 255))
        draw.text(pos, SAMPLE, font=font, fill=(255, 130, 110, 255), stroke_width=2, stroke_fill=(30, 8, 16, 255))
    panels.append(panel)
sheet = Image.new("RGBA", (steel.width, steel.height * 2), (0, 0, 0, 255))
for i, panel in enumerate(panels):
    sheet.paste(panel, (0, steel.height * i))
sheet.convert("RGB").save(os.path.join(out, name + "_review.png"))
print("wrote", name, "layers and review")

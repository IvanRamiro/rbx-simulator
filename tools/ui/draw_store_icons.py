"""Draws the Store's pictures (the owner's game pass shop, 2026-11-10), in the HUD icons' style (draw_icons.py): solid,
full-colour drawings with a dark outline, drawn at 1024 px and reduced for smooth edges. Original drawings, no text in any
language, except the VIP pass's own "VIP" lettering (the owner, 2026-11-10: in the style of Roblox's VIP pass icons). Each is
saved twice: <name>.png at 256 px for the game (UiTheme.Icons.Store, GameConfig.GamePasses[].Icon) and <name>_512.png, the
picture to give the pass on Roblox. Needs Pillow and numpy:

    python3 draw_store_icons.py assets/ui/store
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
OUT = sys.argv[1]
OUTLINE = (12, 18, 44, 255)


def rgb(hex_colour):
    return tuple(int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))


class Art:
    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    def _paint(self, mask, top, bottom):
        t = np.linspace(0, 1, S)[:, None, None]
        colours = (1 - t) * np.array(rgb(top))[None, None, :] + t * np.array(rgb(bottom))[None, None, :]
        colours = np.repeat(colours, S, axis=1)
        layer = np.dstack([colours, np.asarray(mask, dtype=float)]).astype(np.uint8)
        self.img.alpha_composite(Image.fromarray(layer, "RGBA"))

    def poly(self, pts, top, bottom=None):
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        self._paint(mask, top, bottom or top)

    def poly_within(self, pts, within, top, bottom=None, holes=()):
        """a polygon painted only where it overlaps another shape (`within`, less its `holes`)"""
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        clip = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(clip)
        d.polygon([(float(x), float(y)) for x, y in within], fill=255)
        for hole in holes:
            d.polygon([(float(x), float(y)) for x, y in hole], fill=0)
        self._paint(Image.fromarray(np.minimum(np.asarray(mask), np.asarray(clip))), top, bottom or top)

    def ellipse(self, cx, cy, rx, ry, top, bottom=None):
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        self._paint(mask, top, bottom or top)

    def line(self, pts, width, top, bottom=None):
        mask = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(mask)
        d.line([(float(x), float(y)) for x, y in pts], fill=255, width=int(width), joint="curve")
        for x, y in pts:
            d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=255)
        self._paint(mask, top, bottom or top)

    def cut(self, pts=None, ellipse=None):
        """makes a hole through everything drawn so far"""
        mask = Image.new("L", (S, S), 255)
        d = ImageDraw.Draw(mask)
        if pts:
            d.polygon(pts, fill=0)
        if ellipse:
            cx, cy, rx, ry = ellipse
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=0)
        r, g, b, a = self.img.split()
        self.img = Image.merge("RGBA", (r, g, b, Image.fromarray(np.minimum(np.asarray(a), np.asarray(mask)))))

    def save(self, name):
        # a dark line all round, so the picture stands out on any colour
        small = self.img.getchannel("A").resize((256, 256), Image.LANCZOS)
        grown = small.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(0.8)).resize((S, S), Image.BICUBIC)
        base = Image.new("RGBA", (S, S), OUTLINE)
        base.putalpha(grown)
        base.alpha_composite(self.img)
        base.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))
        # the pass's picture on Roblox: on a deep night-blue round plate with a gold rim (Roblox shows a pass's picture in a circle)
        plate = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(plate)
        d.ellipse([16, 16, S - 16, S - 16], fill=(226, 182, 92, 255))
        d.ellipse([44, 44, S - 44, S - 44], fill=(24, 25, 68, 255))
        glow = Image.new("L", (S, S), 0)
        ImageDraw.Draw(glow).ellipse([200, 200, S - 200, S - 200], fill=120)
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        light = Image.new("RGBA", (S, S), (90, 96, 190, 255))
        light.putalpha(glow)
        plate.alpha_composite(light)
        picture = base.resize((int(S * 0.74), int(S * 0.74)), Image.LANCZOS)
        plate.alpha_composite(picture, (int(S * 0.13), int(S * 0.13)))
        plate.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, name + "_512.png"))


def bez(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def mirror(pts):
    return [(S - x, y) for x, y in pts]


def sparkle(a, cx, cy, r, top="FFFFFF", bottom="FFF0A0"):
    a.poly([(cx, cy - r), (cx + r * 0.2, cy - r * 0.2), (cx + r, cy), (cx + r * 0.2, cy + r * 0.2),
            (cx, cy + r), (cx - r * 0.2, cy + r * 0.2), (cx - r, cy), (cx - r * 0.2, cy - r * 0.2)], top, bottom)


os.makedirs(OUT, exist_ok=True)

# Store: a gift box in crimson lacquer, tied with a gold ribbon and a bow, a glint
a = Art()
a.poly([(170, 470), (854, 470), (820, 940), (204, 940)], "F0433C", "8C1430")                  # the box
a.poly([(120, 340), (904, 340), (904, 500), (120, 500)], "FF6A5A", "C81E30")                  # its lid
a.poly([(452, 340), (572, 340), (572, 940), (452, 940)], "FFE27A", "D88A1C")                  # the ribbon down it
a.poly([(120, 400), (904, 400), (904, 448), (120, 448)], "FFF0A0", "E8A020")                  # and round the lid
for side in (1, -1):                                                                            # the bow's two loops
    loop = bez((512, 330), (512 - side * 120, 120), (512 - side * 360, 140), (512 - side * 300, 300)) \
        + bez((512 - side * 300, 300), (512 - side * 260, 360), (512 - side * 120, 360), (512, 330))[1:]
    a.poly(loop, "FFE27A", "D88A1C")
    a.poly(bez((512, 330), (512 - side * 110, 190), (512 - side * 260, 200), (512 - side * 250, 290))
           + bez((512 - side * 250, 290), (512 - side * 200, 320), (512 - side * 110, 320), (512, 330))[1:], "C8780C", "8A4E10")
a.ellipse(512, 330, 70, 60, "FFF4B8", "E8A020")                                                # its knot
sparkle(a, 830, 210, 90)
a.save("Store")

# Lucky Cultivator: a four-leaf jade clover on its stem, each leaf a heart with its own dark edge, round a gold coin with a
# square hole; two glints (leaves touching each other read as one green blob)
a = Art()
a.line(bez((560, 560), (640, 700), (700, 820), (820, 930)), 46, "2FB878", "17855C")             # the stem
for i in range(4):
    ang = math.radians(90 * i + 45)
    c, s_ = math.cos(ang), math.sin(ang)
    for grow, top, bottom in ((26, "0E5C40", "0A4A34"), (0, "8CF0A8", "1E9F68")):              # a dark rim, then the leaf
        tip = (512 + c * 40, 512 + s_ * 40)
        pts = []
        for side in (-1, 1):                                                                    # each leaf a heart: two lobes and a point toward the middle
            lx, ly = 512 + c * 270 - s_ * side * 82, 512 + s_ * 270 + c * side * 82
            a.ellipse(lx, ly, 118 + grow, 118 + grow, top, bottom)
        a.poly([(tip[0] - c * grow, tip[1] - s_ * grow), (512 + c * 250 - s_ * (190 + grow), 512 + s_ * 250 + c * (190 + grow)),
                (512 + c * 250 + s_ * (190 + grow), 512 + s_ * 250 - c * (190 + grow))], top, bottom)
    a.line([(512 + c * 110, 512 + s_ * 110), (512 + c * 330, 512 + s_ * 330)], 16, "2FB878", "17855C")   # its vein
a.ellipse(512, 512, 158, 158, "0E5C40", "0A4A34")
a.ellipse(512, 512, 138, 138, "FFE27A", "D88A1C")                                              # the coin
a.ellipse(512, 512, 108, 108, "FFF4B8", "F4B020")
a.cut(pts=[(472, 472), (552, 472), (552, 552), (472, 552)])
sparkle(a, 860, 150, 96)
sparkle(a, 150, 170, 64)
a.save("Luck")

# Qi Surge: two flames of Qi, a great one before a smaller, doubled, gold chevrons rising beside them
a = Art()
def flame(a, ox, oy, k, top, bottom, inner_top, inner_bottom):
    def P(x, y):
        return (ox + (x - 512) * k, oy + (y - 512) * k)
    outer = bez(P(512, 90), P(640, 300), P(860, 430), P(800, 660)) + bez(P(800, 660), P(760, 860), P(620, 930), P(500, 930))[1:] \
        + bez(P(500, 930), P(320, 930), P(190, 800), P(210, 620))[1:] + bez(P(210, 620), P(225, 500), P(320, 450), P(360, 340))[1:] \
        + bez(P(360, 340), P(400, 400), P(430, 430), P(460, 440))[1:] + bez(P(460, 440), P(440, 320), P(450, 200), P(512, 90))[1:]
    a.poly(outer, top, bottom)
    inner = bez(P(520, 400), P(600, 520), P(690, 590), P(650, 720)) + bez(P(650, 720), P(620, 830), P(440, 850), P(370, 740))[1:] \
        + bez(P(370, 740), P(330, 660), P(400, 590), P(440, 560))[1:] + bez(P(440, 560), P(470, 610), P(500, 600), P(510, 570))[1:] \
        + bez(P(510, 570), P(500, 510), P(500, 460), P(520, 400))[1:]
    a.poly(inner, inner_top, inner_bottom)
flame(a, 640, 470, 0.62, "B8A0FF", "5A3CE0", "F4F0FF", "C8B8FF")                               # behind: violet
flame(a, 440, 560, 0.86, "7FF4FF", "1466F0", "FFFFFF", "A8F0FF")                               # before: Qi blue
for k, (cx, cy) in enumerate(((830, 700), (830, 520), (830, 340))):
    a.poly([(cx - 110, cy + 60), (cx, cy - 50), (cx + 110, cy + 60), (cx + 110, cy + 130), (cx, cy + 20), (cx - 110, cy + 130)],
           "FFF0A0" if k == 2 else "FFE27A", "D88A1C")
a.save("QiSurge")

# +3 Pet Slots: three spirit paw prints climbing, a gold medallion with a plus
a = Art()
def paw(a, cx, cy, k, top, bottom):
    a.ellipse(cx, cy + 40 * k, 120 * k, 100 * k, top, bottom)
    for dx, dy, rx, ry in ((-120, -95, 46, 58), (-45, -150, 48, 62), (45, -150, 48, 62), (120, -95, 46, 58)):
        a.ellipse(cx + dx * k, cy + dy * k, rx * k, ry * k, top, bottom)
paw(a, 250, 790, 1.0, "FFB06A", "F06A18")
paw(a, 470, 500, 1.0, "7FF4E0", "2FB8A8")
paw(a, 230, 230, 0.9, "B494FF", "6A3CD8")
a.ellipse(770, 760, 200, 200, "FFE27A", "D88A1C")
a.ellipse(770, 760, 160, 160, "FFF4B8", "F4B020")
a.poly([(740, 650), (800, 650), (800, 730), (880, 730), (880, 790), (800, 790), (800, 870), (740, 870), (740, 790), (660, 790), (660, 730), (740, 730)],
       "FFFFFF", "FFE8A8")
a.save("PetSlots")

# VIP: in the style of Roblox's VIP pass icons (the owner, 2026-11-10): chunky gold "VIP" letters, a deeper gold underside
# giving them depth, a gold crown set with gems above, glints
a = Art()
V = [(90, 470), (232, 470), (262, 690), (292, 470), (434, 470), (338, 885), (186, 885)]
I = [(452, 470), (590, 470), (590, 885), (452, 885)]
P = [(608, 470), (800, 470)] + bez((800, 470), (915, 470), (950, 540), (950, 610))[1:] + bez((950, 610), (950, 680), (915, 750), (800, 750))[1:] \
    + [(746, 750), (746, 885), (608, 885)]
P_HOLE = [(746, 565), (795, 565)] + bez((795, 565), (825, 565), (838, 588), (838, 610))[1:] + bez((838, 610), (838, 632), (825, 655), (795, 655))[1:] + [(746, 655)]


def shifted(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


for letter in (V, I, P):                                                                     # the underside: depth
    a.poly(shifted(letter, 14, 22), "E8901C", "A8520C")
for letter in (V, I, P):
    a.poly(letter, "FFF6A0", "F4A818")
a.cut(pts=P_HOLE)
a.cut(pts=shifted(P_HOLE, 14, 22))
for letter, holes in ((V, ()), (I, ()), (P, (P_HOLE,))):                                     # a gloss along their tops, inside each letter
    a.poly_within([(60, 490), (980, 490), (980, 538), (60, 538)], letter, "FFFFFF", "FFF6C0", holes)
crown = [(300, 440), (270, 180), (395, 300), (512, 110), (629, 300), (754, 180), (724, 440)]
a.poly(crown, "FFE27A", "D88A1C")
a.poly([(290, 380), (734, 380), (734, 445), (290, 445)], "FFF0A0", "D88A1C")
for cx, cy, r in ((270, 180, 40), (512, 110, 48), (754, 180, 40)):
    a.ellipse(cx, cy, r, r, "FFFFFF", "D8E4FF")
a.ellipse(512, 412, 30, 26, "FF6A6A", "B81E30")
for cx in (390, 634):
    a.ellipse(cx, 412, 24, 22, "7FC8FF", "1E5AD8")
sparkle(a, 900, 150, 92)
sparkle(a, 120, 250, 64)
a.save("VIP")

# Exclusive Egg: a violet egg banded and starred with gold, glowing at a crack, glints round it
a = Art()
egg = bez((512, 80), (720, 80), (850, 410), (850, 615)) + bez((850, 615), (850, 835), (690, 960), (512, 960))[1:] \
    + bez((512, 960), (334, 960), (174, 835), (174, 615))[1:] + bez((174, 615), (174, 410), (304, 80), (512, 80))[1:]
a.poly(egg, "C8A8FF", "4A1C9C")
a.poly([(170, 560), (854, 560), (856, 640), (168, 640)], "FFE27A", "D88A1C")                  # its gold band
for cx in (300, 512, 724):
    a.ellipse(cx, 600, 30, 30, "FFFFFF", "FFE8A8")
crack = [(330, 330), (400, 280), (440, 360), (512, 300), (580, 380), (650, 320), (690, 360),
         (650, 360), (580, 420), (512, 340), (440, 400), (400, 320)]
a.poly(crack, "FFF6C8", "FFC838")
sparkle(a, 512, 780, 110, "FFFFFF", "FFE27A")
sparkle(a, 860, 200, 80)
sparkle(a, 150, 260, 60)
a.save("ExclusiveEgg")

print("drew 6 store pictures in", OUT)

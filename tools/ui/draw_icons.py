"""Draws the HUD's icon set (UiTheme.Icons): solid, full-colour pictures with a dark outline (the owner,
2026-11-04: the line icons were "too transparent and no life at all"). Drawn at 1024 px and reduced to
256 px for smooth edges. Original drawings, no text in any language. Needs Pillow and numpy:

    python3 draw_icons.py assets/ui/icons

then upload each PNG to Roblox and put its id in icons.json and UiTheme.Icons. The game shows them
untinted (UiKit.icon)."""
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


# Qi: a flame of energy curling on itself
a = Art()
flame = bez((512, 90), (640, 300), (860, 430), (800, 660)) + bez((800, 660), (760, 860), (620, 930), (500, 930))[1:] \
    + bez((500, 930), (320, 930), (190, 800), (210, 620))[1:] + bez((210, 620), (225, 500), (320, 450), (360, 340))[1:] \
    + bez((360, 340), (400, 400), (430, 430), (460, 440))[1:] + bez((460, 440), (440, 320), (450, 200), (512, 90))[1:]
a.poly(flame, "7FF4FF", "1466F0")
inner = bez((520, 400), (600, 520), (690, 590), (650, 720)) + bez((650, 720), (620, 830), (440, 850), (370, 740))[1:] \
    + bez((370, 740), (330, 660), (400, 590), (440, 560))[1:] + bez((440, 560), (470, 610), (500, 600), (510, 570))[1:] \
    + bez((510, 570), (500, 510), (500, 460), (520, 400))[1:]
a.poly(inner, "FFFFFF", "A8F0FF")
a.save("Qi")

# Spirit Stones: a cut crystal, each facet its own shade
a = Art()
a.poly([(290, 150), (734, 150), (900, 390), (124, 390)], "A5FFF0", "4FE0D0")
a.poly([(124, 390), (900, 390), (512, 930)], "1FC8C0", "0A7FA0")
a.poly([(290, 150), (400, 390), (124, 390)], "D8FFF8")
a.poly([(734, 150), (900, 390), (624, 390)], "3FD8D0")
a.poly([(400, 390), (624, 390), (512, 150)], "E8FFFC", "8FF8E8")
a.poly([(400, 390), (624, 390), (512, 930)], "6FF0E0", "18B0B8")
a.poly([(124, 390), (400, 390), (512, 930)], "38D8D0", "0C90A8")
a.save("Stones")

# Relics: a jade disc on a red cord, with a gold ring
a = Art()
a.line([(512, 60), (512, 260)], 46, "FF5A50", "C81E30")
a.ellipse(512, 590, 370, 370, "8CF0A8", "1E9F68")
a.ellipse(512, 590, 300, 300, "4FD088", "16855C")
a.ellipse(512, 590, 165, 165, "FFE27A", "E89A18")
a.cut(ellipse=(512, 590, 110, 110))
a.ellipse(512, 215, 66, 66, "FFE27A", "E89A18")
a.save("Relics")

# Pets: a spirit fox's face
a = Art()
ear_l = [(190, 90), (430, 340), (170, 500)]
a.poly(ear_l, "FF9A3C", "F06A18")
a.poly(mirror(ear_l), "FF9A3C", "F06A18")
a.poly([(205, 165), (370, 340), (195, 430)], "4A2030")
a.poly(mirror([(205, 165), (370, 340), (195, 430)]), "4A2030")
head = [(150, 400), (350, 300), (674, 300), (874, 400), (800, 650), (512, 950), (224, 650)]
a.poly(head, "FFAE50", "F26A18")
cheek = [(150, 480), (420, 620), (512, 950), (224, 680)]
a.poly(cheek, "FFFFFF", "FFE2C8")
a.poly(mirror(cheek), "FFFFFF", "FFE2C8")
eye = [(290, 500), (450, 540), (420, 610), (320, 580)]
a.poly(eye, "1C1430")
a.poly(mirror(eye), "1C1430")
a.ellipse(392, 555, 20, 20, "FFFFFF")
a.ellipse(S - 370, 555, 20, 20, "FFFFFF")
a.poly([(450, 830), (574, 830), (512, 910)], "1C1430")
a.save("Pets")

# Robes: a cultivator's robe: gold, wide sleeves, a crossed white collar, a red sash
a = Art()
sleeve_l = [(330, 170), (70, 400), (120, 640), (330, 520)]
a.poly(sleeve_l, "FFD866", "D88A1C")
a.poly(mirror(sleeve_l), "FFD866", "D88A1C")
a.poly([(320, 130), (704, 130), (780, 950), (244, 950)], "FFE48A", "E09A22")
a.poly([(400, 120), (512, 130), (624, 120), (512, 470)], "1C4FA8")
a.poly([(380, 110), (450, 110), (640, 500), (570, 560)], "FFFFFF", "D8E4FF")
a.poly([(644, 110), (574, 110), (440, 410), (484, 480)], "F4F8FF", "C8D8FF")
a.poly([(280, 560), (744, 560), (756, 680), (268, 680)], "F0433C", "B81E30")
a.ellipse(512, 620, 58, 58, "FFE27A", "E89A18")
a.save("Robes")

# Qinggong: a swallow diving, wings swept back
a = Art()
wing_l = bez((512, 420), (360, 260), (190, 130), (50, 120)) + bez((50, 120), (130, 330), (280, 520), (470, 590))[1:]
a.poly(wing_l, "2F7CFF", "7FE0FF")
a.poly(mirror(wing_l), "2F7CFF", "7FE0FF")
tail_l = [(470, 640), (512, 690), (400, 960)]
a.poly(tail_l, "2060E0", "0E3CA8")
a.poly(mirror(tail_l), "2060E0", "0E3CA8")
body = bez((512, 190), (620, 300), (610, 590), (512, 760)) + bez((512, 760), (414, 590), (404, 300), (512, 190))[1:]
a.poly(body, "FFFFFF", "BDEBFF")
a.poly(bez((512, 190), (570, 250), (580, 340), (560, 400)) + bez((560, 400), (530, 420), (494, 420), (464, 400))[1:]
       + bez((464, 400), (444, 340), (454, 250), (512, 190))[1:], "1E4FC8", "123490")
a.ellipse(512, 330, 24, 24, "FFD84A")
a.save("Qinggong")

# Guardian: a crimson shield, a gold rim, a beast's slit eye
a = Art()
shield = [(512, 60), (880, 180)] + bez((880, 180), (880, 560), (740, 820), (512, 970)) + bez((512, 970), (284, 820), (144, 560), (144, 180))[1:]
a.poly(shield, "FFE27A", "D88A1C")
inner = [(512, 150), (790, 240)] + bez((790, 240), (790, 540), (680, 740), (512, 860)) + bez((512, 860), (344, 740), (234, 540), (234, 240))[1:]
a.poly(inner, "F0433C", "8C1430")
eye = bez((240, 480), (380, 310), (644, 310), (784, 480)) + bez((784, 480), (644, 650), (380, 650), (240, 480))[1:]
a.poly(eye, "FFFFFF", "FFE8A8")
a.ellipse(512, 480, 118, 118, "FFC838", "E8780C")
a.poly(bez((512, 350), (560, 430), (560, 530), (512, 610)) + bez((512, 610), (464, 530), (464, 430), (512, 350))[1:], "1C1020")
a.save("Guardian")

# Hatch: a speckled egg splitting, gold light from the crack
a = Art()
egg = bez((512, 70), (720, 70), (850, 400), (850, 610)) + bez((850, 610), (850, 830), (690, 960), (512, 960))[1:] \
    + bez((512, 960), (334, 960), (174, 830), (174, 610))[1:] + bez((174, 610), (174, 400), (304, 70), (512, 70))[1:]
a.poly(egg, "FFFDF0", "F0D8A0")
for cx, cy, r in [(360, 300, 44), (650, 250, 34), (700, 780, 52), (300, 780, 38), (510, 850, 30)]:
    a.ellipse(cx, cy, r, r, "4FD088", "1E9F68")
crack = [(150, 520), (300, 440), (400, 560), (512, 420), (620, 560), (724, 440), (874, 520),
         (874, 620), (724, 540), (620, 660), (512, 520), (400, 660), (300, 540), (150, 620)]
a.poly(crack, "FFF29A", "FF9A1E")
a.save("Hatch")

# Shop: the Jade Scale: a gold balance, jade in one pan and stones in the other
a = Art()
a.poly([(482, 150), (542, 150), (560, 830), (464, 830)], "FFE27A", "D88A1C")
a.poly([(300, 830), (724, 830), (780, 940), (244, 940)], "FFD866", "C8780C")
a.line([(130, 240), (894, 240)], 56, "FFE27A", "E89A18")
a.ellipse(512, 180, 66, 66, "A8FFD0", "2FB878")
for side in (0, 1):
    cx = 190 if side == 0 else 834
    a.line([(cx, 250), (cx - 120, 560)], 18, "FFE27A")
    a.line([(cx, 250), (cx + 120, 560)], 18, "FFE27A")
    a.ellipse(cx, 470 if side else 490, 90, 80, "8CF0A8" if side == 0 else "7FF4FF", "1E9F68" if side == 0 else "1466F0")
    a.poly([(cx - 165, 560), (cx + 165, 560)] + bez((cx + 165, 560), (cx + 120, 680), (cx - 120, 680), (cx - 165, 560))[1:], "FFD866", "C8780C")
a.save("Shop")

# Forge: a hammer over an anvil, sparks flying
a = Art()
a.poly([(180, 620), (850, 620), (720, 740), (640, 760), (680, 900), (340, 900), (380, 760), (300, 740)], "B8C8E0", "4A5878")
a.poly([(180, 620), (850, 620), (800, 670), (230, 670)], "F4F8FF", "B8C8E0")
a.line([(620, 150), (390, 520)], 62, "B87A3C", "6A3C18")
a.poly([(360, 70), (660, 240), (560, 400), (260, 230)], "D8E4F4", "6A7898")
a.line([(700, 540), (800, 430)], 34, "FFE27A", "FF7A1E")
a.line([(780, 590), (930, 540)], 28, "FFE27A", "FF7A1E")
a.line([(640, 500), (660, 390)], 26, "FFE27A", "FF7A1E")
a.save("Forge")

# Quest: an open scroll with a red seal
a = Art()
a.poly([(230, 170), (794, 170), (794, 860), (230, 860)], "FFF6D8", "E8CC90")
for y in (300, 410, 520):
    a.line([(330, y), (694, y)], 30, "8A6A3C")
a.line([(330, 630), (560, 630)], 30, "8A6A3C")
a.ellipse(650, 720, 92, 92, "F0433C", "A81830")
a.ellipse(650, 720, 48, 48, "FF7A6A", "D8303A")
for y in (150, 880):
    a.line([(150, y), (874, y)], 92, "C88A3C", "8A5420")
    a.ellipse(130, y, 62, 62, "FFE27A", "E89A18")
    a.ellipse(894, y, 62, 62, "FFE27A", "E89A18")
a.save("Quest")

# Settings: a dial of eight lotus petals round a gold heart
a = Art()
for i in range(8):
    ang = math.radians(45 * i - 90)
    c, s_ = math.cos(ang), math.sin(ang)
    petal = []
    for t in np.linspace(0, 1, 40):
        length = 150 + 300 * t
        width = 118 * math.sin(math.pi * t) ** 0.8
        petal.append((512 + c * length - s_ * width, 512 + s_ * length + c * width))
    for t in np.linspace(1, 0, 40):
        length = 150 + 300 * t
        width = 118 * math.sin(math.pi * t) ** 0.8
        petal.append((512 + c * length + s_ * width, 512 + s_ * length - c * width))
    a.poly(petal, "D8E8FF", "6A9CF0")
a.ellipse(512, 512, 190, 190, "FFE27A", "E8901C")
a.cut(ellipse=(512, 512, 84, 84))
a.save("Settings")

# Rewards: a gold ingot, boat-shaped with a domed heart, and a glint
a = Art()
a.ellipse(512, 500, 220, 200, "FFF0A0", "F4B020")
boat = bez((60, 430), (180, 520), (300, 560), (512, 560)) + bez((512, 560), (724, 560), (844, 520), (964, 430))[1:] \
    + bez((964, 430), (920, 720), (780, 880), (512, 880))[1:] + bez((512, 880), (244, 880), (104, 720), (60, 430))[1:]
a.poly(boat, "FFD84A", "D87A0C")
a.line(bez((110, 500), (240, 590), (360, 620), (512, 620)) + bez((512, 620), (664, 620), (784, 590), (914, 500))[1:], 26, "FFF8C8")
for cx, cy, r in [(800, 170, 110), (250, 240, 60)]:
    a.poly([(cx, cy - r), (cx + r * 0.2, cy - r * 0.2), (cx + r, cy), (cx + r * 0.2, cy + r * 0.2),
            (cx, cy + r), (cx - r * 0.2, cy + r * 0.2), (cx - r, cy), (cx - r * 0.2, cy - r * 0.2)], "FFFFFF", "FFF0A0")
a.save("Rewards")

# Codex: an open book of beasts, a spirit's paw print glowing on its page
a = Art()
a.poly([(70, 250)] + bez((70, 250), (230, 170), (400, 190), (512, 280))[1:] + [(512, 920)] + bez((512, 920), (400, 830), (230, 810), (70, 890))[1:], "FFF8E0", "E8CFA0")
a.poly([(954, 250)] + bez((954, 250), (794, 170), (624, 190), (512, 280))[1:] + [(512, 920)] + bez((512, 920), (624, 830), (794, 810), (954, 890))[1:], "FFFDF0", "F0DAB0")
a.poly([(40, 300), (70, 250), (70, 890)] + bez((70, 890), (230, 810), (400, 830), (512, 920))[1:] + bez((512, 920), (624, 830), (794, 810), (954, 890))[1:] + [(954, 250), (984, 300), (984, 960)] + bez((984, 960), (800, 880), (620, 900), (512, 985))[1:] + bez((512, 985), (404, 900), (224, 880), (40, 960))[1:], "4FA8FF", "2A3C9C")
a.line([(512, 280), (512, 920)], 22, "B89868", "8C6C40")
a.ellipse(740, 590, 92, 78, "4FE0C8", "1E9F98")
for cx, cy, rx, ry in [(630, 465, 40, 54), (712, 410, 42, 58), (800, 418, 42, 58), (868, 480, 38, 52)]:
    a.ellipse(cx, cy, rx, ry, "7FF4E0", "2FB8A8")
for y in (380, 490, 600, 710):
    a.line([(150, y), (420, y + 18)], 24, "C8AC80")
a.save("Codex")

# Lock: a gold padlock with a keyhole
a = Art()
a.line(bez((300, 500), (300, 80), (724, 80), (724, 500)), 96, "E0E8F8", "7888A8")
a.poly([(170, 450), (854, 450), (894, 500), (894, 880), (830, 950), (194, 950), (130, 880), (130, 500)], "FFE27A", "D88A1C")
a.poly([(170, 450), (854, 450), (894, 500), (130, 500)], "FFF4B8", "FFE27A")
a.ellipse(512, 650, 76, 76, "3A2410", "1E1208")
a.poly([(476, 670), (548, 670), (580, 830), (444, 830)], "3A2410", "1E1208")
a.save("Lock")
print("drew 15 icons in", OUT)

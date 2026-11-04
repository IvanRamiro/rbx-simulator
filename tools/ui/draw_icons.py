"""Draws the HUD's icon set (UiTheme.Icons): white line icons on transparent, drawn at 1024 px
and reduced to 128 px for smooth edges; the game tints them (ImageColor3). Original drawings, no
text in any language. Needs Pillow:

    python3 draw_icons.py assets/ui/icons

then upload each PNG to Roblox and put its id in UiTheme.Icons."""
import math, os, sys
from PIL import Image, ImageDraw

S = 1024
W = 62            # line width
OUT = sys.argv[1]

def canvas():
    img = Image.new("L", (S, S), 0)
    return img, ImageDraw.Draw(img)

def path(d, pts, w=W, closed=False):
    if closed:
        pts = list(pts) + [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=int(w))
    for p in pts:
        r = w / 2
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)

def bez(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def arc(cx, cy, r, a0, a1, n=64):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def save(img, name):
    rgba = Image.new("RGBA", (S, S), (255, 255, 255, 0))
    rgba.putalpha(img)
    rgba.resize((128, 128), Image.LANCZOS).save(os.path.join(OUT, name + ".png"))

# Qi: a flame of energy rising, an inner flame within it
img, d = canvas()
outer = bez((512, 910), (190, 900), (150, 560), (330, 420)) + bez((330, 420), (380, 560), (450, 560), (450, 480))[1:] \
      + bez((450, 480), (420, 300), (520, 160), (640, 90))[1:] + bez((640, 90), (590, 260), (860, 380), (840, 640))[1:] \
      + bez((840, 640), (830, 820), (700, 910), (512, 910))[1:]
path(d, outer)
inner = bez((512, 800), (380, 790), (380, 640), (470, 560)) + bez((470, 560), (480, 640), (540, 640), (560, 560))[1:] \
      + bez((560, 560), (680, 640), (650, 790), (512, 800))[1:]
path(d, inner, W * 0.7)
save(img, "Qi")

# Spirit Stones: a faceted crystal
img, d = canvas()
top, l, r, bl, br, bottom = (512, 110), (230, 380), (794, 380), (330, 380), (694, 380), (512, 920)
outline = [(380, 110), (644, 110), (850, 360), (512, 920), (174, 360)]
path(d, outline, closed=True)
path(d, [(174, 360), (850, 360)], W * 0.7)
path(d, [(380, 110), (330, 360), (512, 920)], W * 0.7)
path(d, [(644, 110), (694, 360), (512, 920)], W * 0.7)
save(img, "Stones")

# Relics: an ancient jade disc on its cord
img, d = canvas()
path(d, arc(512, 580, 300, 0, 360), closed=False)
path(d, arc(512, 580, 110, 0, 360), W * 0.8)
path(d, [(512, 280), (512, 120)], W * 0.8)
path(d, [(512, 120), (420, 70)], W * 0.6)
path(d, [(512, 120), (604, 70)], W * 0.6)
for a in (45, 135, 225, 315):  # carved notches
    c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
    path(d, [(512 + 170 * c, 580 + 170 * s_), (512 + 240 * c, 580 + 240 * s_)], W * 0.55)
save(img, "Relics")

# Pets: a paw
img, d = canvas()
d.ellipse([300, 500, 724, 880], fill=255)
d.polygon([(330, 700), (512, 480), (694, 700)], fill=255)
for (x, y, rx, ry) in [(250, 420, 90, 120), (420, 260, 95, 130), (604, 260, 95, 130), (774, 420, 90, 120)]:
    d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=255)
save(img, "Pets")

# Robes: a cultivator's robe, crossed collar and wide sleeves
img, d = canvas()
robe = [(392, 140), (632, 140), (900, 420), (790, 520), (690, 440), (700, 920), (324, 920), (334, 440), (234, 520), (124, 420)]
path(d, robe, closed=True)
path(d, [(392, 140), (512, 330), (632, 140)], W * 0.75)   # collar
path(d, [(512, 330), (640, 560)], W * 0.75)              # the crossing fold
path(d, [(334, 600), (690, 600)], W * 0.6)                # sash
save(img, "Robes")

# Qinggong: a feather in flight
img, d = canvas()
spine = bez((230, 860), (380, 620), (560, 300), (820, 150))
path(d, spine)
vane_top = bez((300, 720), (330, 420), (560, 200), (820, 150))
vane_bot = bez((300, 720), (560, 700), (760, 440), (820, 150))
path(d, vane_top, W * 0.8)
path(d, vane_bot, W * 0.8)
for t in (0.35, 0.55, 0.75):  # barbs
    i = int(t * (len(spine) - 1))
    x, y = spine[i]
    path(d, [(x, y), (x + 110, y + 70)], W * 0.5)
save(img, "Qinggong")

# Guardian: a shield bearing a beast's slit eye
img, d = canvas()
shield = [(512, 100), (850, 220)] + bez((850, 220), (860, 560), (720, 800), (512, 930))[1:] \
         + bez((512, 930), (304, 800), (164, 560), (174, 220))[1:] + [(174, 220)]
path(d, shield, closed=True)
eye_top = bez((300, 520), (420, 400), (604, 400), (724, 520))
eye_bot = bez((724, 520), (604, 640), (420, 640), (300, 520))
path(d, eye_top + eye_bot[1:], W * 0.7)
d.ellipse([462, 430, 562, 610], fill=255)   # the slit pupil's iris
save(img, "Guardian")

# Hatch: an egg with a crack
img, d = canvas()
egg = []
for i in range(181):
    a = math.radians(i * 2)
    rx = 300
    ry = 400 if math.sin(a) < 0 else 350
    egg.append((512 + rx * math.cos(a) * (1 - 0.12 * max(0, -math.sin(a))), 560 + ry * math.sin(a)))
path(d, egg, closed=True)
path(d, [(250, 520), (360, 450), (430, 560), (520, 470), (600, 570), (680, 480), (770, 540)], W * 0.65)
save(img, "Hatch")

# Shop: a purse of spirit stones
img, d = canvas()
bag = bez((380, 330), (130, 520), (170, 900), (512, 900)) + bez((512, 900), (854, 900), (894, 520), (644, 330))[1:]
path(d, bag)
path(d, [(380, 330), (644, 330)], W * 0.8)
path(d, [(400, 330), (330, 170), (512, 230), (694, 170), (624, 330)], W * 0.7)
path(d, [(420, 640), (512, 540), (604, 640), (512, 740)], W * 0.6, closed=True)  # a stone on its side
save(img, "Shop")

# Forge: a hammer over an anvil
img, d = canvas()
anvil = [(200, 560), (824, 560), (824, 640), (700, 700), (700, 800), (800, 900), (224, 900), (324, 800), (324, 700), (200, 640)]
path(d, anvil, closed=True)
path(d, [(330, 420), (640, 140)], W)          # handle
path(d, [(560, 70), (760, 290), (690, 350), (490, 130)], W * 0.8, closed=True)  # head
save(img, "Forge")

# Settings: a gear
img, d = canvas()
cx, cy, teeth = 512, 512, 8
gear = []
for i in range(teeth):
    a = i * math.tau / teeth
    half = math.tau / teeth / 4.6
    for r, da in ((300, -half * 1.5), (400, -half * 0.8), (400, half * 0.8), (300, half * 1.5)):
        gear.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
path(d, gear, closed=True)
path(d, arc(cx, cy, 125, 0, 360), W)
save(img, "Settings")
print("drawn:", sorted(os.listdir(OUT)))

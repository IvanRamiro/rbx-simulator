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

# Qi: a spiral of energy rising into a flame's tip, not a generic fire
img, d = canvas()
spiral = []
for i in range(0, 121):
    t = i / 120
    a = math.tau * (1.55 * t) + 2.6
    r = 50 + 300 * t
    spiral.append((500 + r * math.cos(a), 600 + r * 0.9 * math.sin(a)))
path(d, spiral)
path(d, bez(spiral[-1], (880, 400), (760, 230), (640, 70)), W)
path(d, bez((640, 70), (620, 220), (500, 250), (450, 300)), W * 0.8)
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

# Pets: a spirit fox's head, tall ears and a narrow muzzle, its eyes slanted
img, d = canvas()
path(d, [(170, 90), (350, 390), (674, 390), (854, 90), (880, 500), (512, 930), (144, 500)], closed=True)
path(d, [(320, 560), (440, 620)], W * 1.1)
path(d, [(704, 560), (584, 620)], W * 1.1)
path(d, [(512, 930), (512, 800)], W * 0.8)
save(img, "Pets")

# Robes: a cultivator's robe: wide hanging sleeves, a crossed collar and a sash
img, d = canvas()
path(d, [(360, 130), (664, 130), (960, 430), (830, 620), (690, 470), (720, 920), (304, 920), (334, 470), (194, 620), (64, 430)], closed=True)
path(d, [(360, 130), (610, 480)], W * 0.85)
path(d, [(664, 130), (440, 400)], W * 0.85)
path(d, [(330, 560), (694, 560)], W * 0.9)
save(img, "Robes")

# Qinggong: a swallow diving, wings swept and its tail forked, as light as the art
img, d = canvas()
outline = [(512, 80)] + bez((590, 300), (720, 380), (860, 480), (960, 640)) + bez((960, 640), (820, 610), (700, 580), (600, 560))[1:] \
    + [(668, 950), (512, 770), (356, 950), (424, 560)] + bez((424, 560), (324, 580), (204, 610), (64, 640))[1:] \
    + bez((64, 640), (164, 480), (304, 380), (434, 300))[1:]
path(d, outline, W * 0.9, closed=True)
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

# Shop: the Jade Scale of Buy & Sell, a balance with two hanging pans
img, d = canvas()
path(d, [(512, 150), (512, 860)])
path(d, [(330, 890), (694, 890)])
path(d, [(150, 260), (874, 260)])
path(d, arc(512, 130, 55, 0, 360), W * 0.8)
for x in (170, 854):
    path(d, [(x, 260), (x - 120, 590)], W * 0.7)
    path(d, [(x, 260), (x + 120, 590)], W * 0.7)
    path(d, bez((x - 135, 590), (x - 100, 760), (x + 100, 760), (x + 135, 590)))
    path(d, [(x - 135, 590), (x + 135, 590)], W * 0.7)
save(img, "Shop")

# Forge: a hammer over an anvil
img, d = canvas()
anvil = [(200, 560), (824, 560), (824, 640), (700, 700), (700, 800), (800, 900), (224, 900), (324, 800), (324, 700), (200, 640)]
path(d, anvil, closed=True)
path(d, [(330, 420), (640, 140)], W)          # handle
path(d, [(560, 70), (760, 290), (690, 350), (490, 130)], W * 0.8, closed=True)  # head
save(img, "Forge")

# Settings: a dial of eight lotus petals round a ring
img, d = canvas()
cx, cy, petals = 512, 512, 8
outline = []
for i in range(petals):
    a0 = i * math.tau / petals
    half = math.tau / petals / 2
    p0 = (cx + 270 * math.cos(a0 - half), cy + 270 * math.sin(a0 - half))
    p1 = (cx + 490 * math.cos(a0 - half * 0.55), cy + 490 * math.sin(a0 - half * 0.55))
    p2 = (cx + 490 * math.cos(a0 + half * 0.55), cy + 490 * math.sin(a0 + half * 0.55))
    p3 = (cx + 270 * math.cos(a0 + half), cy + 270 * math.sin(a0 + half))
    outline += bez(p0, p1, p2, p3, 16)
path(d, outline, W * 0.85, closed=True)
path(d, arc(cx, cy, 130, 0, 360), W)
save(img, "Settings")

# Rewards: a gold ingot, boat-shaped with a domed heart, and a glint over it
img, d = canvas()
hull = bez((90, 470), (170, 900), (854, 900), (934, 470))
rim = bez((934, 470), (850, 600), (760, 620), (700, 600)) + bez((700, 600), (690, 340), (334, 340), (324, 600))[1:] \
    + bez((324, 600), (264, 620), (174, 600), (90, 470))[1:]
path(d, hull + rim[1:], W * 0.9)
path(d, [(760, 120), (760, 300)], W * 0.7)
path(d, [(670, 210), (850, 210)], W * 0.7)
save(img, "Rewards")

print("drawn:", sorted(os.listdir(OUT)))

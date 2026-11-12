"""The hub's people (the owner, 2026-11-12: NPCs for the Blacksmith, the Marketplace and Buy & Sell, a Beginner Guide and the
Wandering Merchant; custom characters; the hub is a celestial crystal city, NOT Chinese).

Each NPC is Roblox's default R15 body (Players:CreateHumanoidModelFromDescription) whose part colours are its base clothes
(a tunic, trousers), dressed in pieces made here, each riding one body part so the R15 animations carry it: an apron, a coat,
a cloak, boots, a beard, hair, a hammer. Like the hub (hub_finish.py), every piece is split by material and coloured in the
game with a real Roblox material (Fabric, Leather, Metal, Wood, Glass, Neon, SmoothPlastic for hair): no textures, nothing
to upload.

Authored in Roblox space relative to the HumanoidRootPart, the body at rest (BODY: measured in Studio, 2026-11-12), the NPC
facing -Z. Pieces are named <Npc>_<Piece>__<Material>; PIECES gives each piece's body part; COLOURS each material's colour
per NPC (written to src/worldbuild/Placements/HubNpcs.lua by write_placements()).

    import hub_npcs as N
    N.build("Forgemaster")      # one NPC's pieces (and the stand-in body, for renders)
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../world", "../eggs", "../outfits"):
    p = os.path.normpath(os.path.join(HERE, sub))
    if p not in sys.path:
        sys.path.insert(0, p)
import worldlib as W   # noqa: E402
import egg_hi as Hm    # noqa: E402
import murim_outfit as O   # noqa: E402  (its cloth shapes: se, fine, tube_shell, panel, ribbon, grid_faces)

V = Vector
TAU = 2 * math.pi

# Roblox's default R15 body at rest (centre and size of each part, HumanoidRootPart space), measured in Studio
BODY = {
    "Head": ((0.0, 1.674, 0.0), (1.159, 1.182, 1.161)),
    "UpperTorso": ((0.0, 0.25, 0.0), (1.943, 1.698, 1.004)),
    "LowerTorso": ((0.0, -0.8, 0.0), (1.991, 0.401, 1.004)),
    "LeftUpperArm": ((-1.472, 0.428, 0.0), (1.001, 1.242, 1.002)),
    "RightUpperArm": ((1.472, 0.428, 0.0), (1.001, 1.242, 1.002)),
    "LeftLowerArm": ((-1.472, -0.202, 0.0), (1.001, 1.118, 1.002)),
    "RightLowerArm": ((1.472, -0.202, 0.0), (1.001, 1.118, 1.002)),
    "LeftHand": ((-1.472, -0.865, 0.0), (0.984, 0.316, 1.028)),
    "RightHand": ((1.472, -0.865, 0.0), (0.984, 0.316, 1.028)),
    "LeftUpperLeg": ((-0.498, -1.471, 0.0), (0.993, 1.363, 0.973)),
    "RightUpperLeg": ((0.498, -1.471, 0.0), (0.993, 1.363, 0.973)),
    "LeftLowerLeg": ((-0.498, -2.334, 0.0), (0.993, 1.301, 0.973)),
    "RightLowerLeg": ((0.498, -2.334, 0.0), (0.993, 1.301, 0.973)),
    "LeftFoot": ((-0.498, -3.036, 0.0), (1.009, 0.312, 1.001)),
    "RightFoot": ((0.498, -3.036, 0.0), (1.009, 0.312, 1.001)),
}
FLOOR = -3.192

# the Roblox material each suffix takes in the game (and roughly what it reads as, for renders)
MATERIALS = {
    "Fabric": ("Fabric", 0.85, 0.0), "Leather": ("Leather", 0.55, 0.0), "Gold": ("Metal", 0.3, 1.0), "Steel": ("Metal", 0.32, 1.0),
    "Wood": ("Wood", 0.7, 0.0), "Hair": ("SmoothPlastic", 0.5, 0.0), "Glass": ("Glass", 0.05, 0.0), "Glow": ("Neon", 0.3, 0.0),
    "Cloth": ("Fabric", 0.85, 0.0), "Trim": ("Fabric", 0.7, 0.0), "Face": ("SmoothPlastic", 0.45, 0.0),
}

PIECES = {}    # "<Npc>_<Piece>" -> body part
COLOURS = {}   # npc -> {"<Piece>__<Material>": (r, g, b) 0..255}
BODY_COLOURS = {}   # npc -> {part group: (r, g, b)}: Head, Torso, Arms, Legs


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Kit:
    """One NPC's pieces under construction: a Hi mesh per (piece, material)."""

    def __init__(self, npc):
        self.npc = npc
        self.meshes = {}
        COLOURS[npc] = {}

    def hi(self, piece, material, part, colour):
        key = (piece, material)
        if key not in self.meshes:
            self.meshes[key] = Hm.Hi()
            PIECES[self.npc + "_" + piece] = part
            COLOURS[self.npc][piece + "__" + material] = hexrgb(colour) if isinstance(colour, str) else colour
        return self.meshes[key]

    def objects(self, coll):
        out = []
        for (piece, material), hi in self.meshes.items():
            o = hi.object("%s_%s__%s" % (self.npc, piece, material), coll, [], smooth=material not in ("Glow",))
            if material in ("Fabric", "Leather", "Cloth", "Trim", "Hair", "Wood", "Gold", "Steel"):
                o.data.set_sharp_from_angle(angle=math.radians(50))
                m = o.modifiers.new("Weighted", "WEIGHTED_NORMAL")
                m.mode = "FACE_AREA"
                m.keep_sharp = True
            out.append(o)
        return out


# ---------- shapes ----------
def box(hi, c, size, yaw=0.0, outward_all=True, bevel=0.0):
    """A box (Roblox space) turned about Y."""
    cx, cy, cz = c
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    cs, sn = math.cos(yaw), math.sin(yaw)

    def p(x, y, z):
        return V((cx + x * cs + z * sn, cy + y, cz - x * sn + z * cs))
    corners = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corners[(sx, sy, sz)] = hi.v(p(sx * hx, sy * hy, sz * hz))
    faces = [((1, 0, 0), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]), ((-1, 0, 0), [(-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)]),
             ((0, 1, 0), [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]), ((0, -1, 0), [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
             ((0, 0, 1), [(1, -1, 1), (1, 1, 1), (-1, 1, 1), (-1, -1, 1)]), ((0, 0, -1), [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)])]
    for n, quad in faces:
        nn = (n[0] * cs + n[2] * sn, n[1], -n[0] * sn + n[2] * cs)
        hi.facing([corners[q] for q in quad], [(0, 0), (1, 0), (1, 1), (0, 1)], nn, 0)


def lathe_y(hi, centre, profile, n=24, p=2.0, a_scale=1.0, b_scale=1.0, cap_top=True, cap_bottom=True):
    """A closed solid of revolution about a vertical axis: profile [(y, r)] top to bottom; p > 2 squares it off."""
    rows = O.tube_shell(hi, centre[::2] if len(centre) == 3 else centre,
                        [(y, r * a_scale, r * b_scale) for y, r in profile], 0, n=n, p=p)
    cx, cz = (centre[0], centre[2]) if len(centre) == 3 else centre
    if cap_top:
        y, r = profile[0]
        top = hi.v(V((cx, y, cz)))
        for i in range(n):
            hi.facing([rows[0][i], rows[0][(i + 1) % n], top], [(0, 0), (1, 0), (0.5, 1)], (0, 1, 0), 0)
    if cap_bottom:
        y, r = profile[-1]
        bot = hi.v(V((cx, y, cz)))
        for i in range(n):
            hi.facing([rows[-1][i], rows[-1][(i + 1) % n], bot], [(0, 0), (1, 0), (0.5, 1)], (0, -1, 0), 0)
    return rows


def tube(hi, pts, r, sides=10, tip=False):
    return Hm.htube(hi, pts, r if callable(r) else (lambda t: r), sides=sides, per=4, tip=tip, wobble=0.0)


def sheet(hi, rows, outward, thickness=0.06):
    """A cloth/leather sheet with thickness: rows[j][i] points (Roblox space); outward(j, i) the front side.
    Front, back and the edge strips."""
    nj, ni = len(rows), len(rows[0])
    front, back = [], []
    for j in range(nj):
        fr, bk = [], []
        for i in range(ni):
            n = V(outward(min(j, nj - 2), min(i, ni - 2))).normalized()
            fr.append(hi.v(rows[j][i]))
            bk.append(hi.v(rows[j][i] - n * thickness))
        front.append(fr)
        back.append(bk)
    uv = [[(i / (ni - 1), j / (nj - 1)) for i in range(ni)] for j in range(nj)]
    O.grid_faces(hi, front, uv, outward, 0)
    O.grid_faces(hi, back, uv, lambda j, i: tuple(-c for c in outward(j, i)), 0)
    # edges: top, bottom, left, right
    for a, b in ((front[0], back[0]), (front[-1], back[-1])):
        for i in range(ni - 1):
            hi.f([a[i], a[i + 1], b[i + 1], b[i]], [(0, 0), (1, 0), (1, 1), (0, 1)], 0)
    for col in (0, ni - 1):
        for j in range(nj - 1):
            hi.f([front[j][col], front[j + 1][col], back[j + 1][col], back[j][col]], [(0, 0), (1, 0), (1, 1), (0, 1)], 0)


# ---------- heads ----------
HEAD_C, HEAD_H = 1.674, 0.58          # the head's centre height and half size (a rounded cube)
HEAD_TOP = HEAD_C + 0.591


def hair_cap(hi, front, back, thick=0.05, p=8.0, fringe=None):
    """Hair close over the blocky head: from the crown down to a hairline at `front` (y) over the brow, sweeping lower round the
    sides to `back` behind; a squared shell `thick` off the head, its edge rolled under."""
    a = HEAD_H + thick
    levels = [(HEAD_TOP + thick * 0.6, a * 0.94, a * 0.94), (HEAD_TOP - 0.12, a, a), (front, a, a)]

    def droop(t):   # t from the front (0) round to the back (pi)
        return (front - back) * (0.5 - 0.5 * math.cos(t)) ** 1.3
    O.tube_shell(hi, (0, 0), levels, 0, n=48, p=p, droop=lambda t: droop(t) / 1.0 * (1.0), dome=0.06)


def beard(hi, top_front, top_side, bottom, depth=0.18, p=8.0):
    """A squared beard: a mass hugging the jaw from the sideburns (top_side, at the ears) round to under the mouth (top_front),
    hanging to `bottom` at the chin; `depth` thick off the face."""
    span = math.radians(100)
    rows = []
    for j in range(9):
        v = j / 8
        row = []
        for i in range(17):
            u = -1 + 2 * i / 16
            t = u * span
            top = top_front + (top_side - top_front) * abs(u) ** 1.6
            low = bottom + (top_side - 0.42 - bottom) * abs(u) ** 2.2      # shorter at the sides
            y = top + (low - top) * v
            a = HEAD_H + 0.03 + depth * math.sin(math.pi * min(1.0, v * 1.3 + 0.1)) * (1 - 0.5 * abs(u))
            x, z, nrm = O.se(t, a, a, p)
            row.append(V((x, y, z)) + nrm * 0.02 * math.sin(t * 11) * v)
        rows.append(row)
    sheet(hi, rows, lambda j, i: O.se(-span + 2 * span * (i + 0.5) / 16, 1, 1, p)[2], 0.12)


FACE_Z = -0.588      # the head's front, where a face's features sit


def spot(hi, x, y, rx, ry, z=FACE_Z, depth=0.03):
    """A flat oval on the face (an eye, a pupil, a highlight, a blush): rx wide, ry tall, standing `depth` off it."""
    prof = [(y + ry, 0.01)] + [(y + ry * math.cos(math.pi * k / 8), max(0.01, rx * math.sin(math.pi * k / 8))) for k in range(1, 8)] + [(y - ry, 0.01)]
    lathe_y(hi, (x, 0, z), prof, n=16, p=2.0, b_scale=depth / max(rx, 0.01))


def face(K, eyes, brows, mouth, eye_x=0.21, eye_y=1.77, eye_w=0.1, eye_h=0.13, brow_y=1.96, brow_tilt=(0.0, 0.0), brow_w=0.13, mouth_pts=None,
         mouth_w=0.035, lashes=False, nose=None, highlight=True, glow_eyes=False, blush=None):
    """A face of features standing on the blocky head: eye whites and pupils (or glowing eyes), brows (each tilted: + raises its
    outer end), a mouth along mouth_pts, an optional nose (a skin-coloured block), lashes, cheeks' blush."""
    if glow_eyes:
        ge = K.hi("Eyes", "Glow", "Head", eyes)
        for sgn in (-1, 1):
            spot(ge, sgn * eye_x, eye_y, eye_w * 1.1, eye_h * 0.7)
    else:
        wh = K.hi("EyeWhites", "Face", "Head", "fbfaf6")
        pu = K.hi("Pupils", "Face", "Head", eyes)
        hl = K.hi("EyeShine", "Face", "Head", "ffffff")
        for sgn in (-1, 1):
            spot(wh, sgn * eye_x, eye_y, eye_w, eye_h, depth=0.02)
            spot(pu, sgn * eye_x + sgn * 0.005, eye_y - 0.015, eye_w * 0.62, eye_h * 0.7, z=FACE_Z - 0.02, depth=0.02)
            if highlight:
                spot(hl, sgn * eye_x - 0.025, eye_y + 0.035, eye_w * 0.2, eye_h * 0.18, z=FACE_Z - 0.04, depth=0.01)
    if brows:
        br = K.hi("Brows", "Hair", "Head", brows)
        for k, sgn in enumerate((-1, 1)):
            tilt = brow_tilt[k]
            inner = (sgn * (eye_x - brow_w * 0.9), brow_y - tilt * 0.3, FACE_Z - 0.03)
            outer = (sgn * (eye_x + brow_w * 0.9), brow_y + tilt, FACE_Z - 0.03)
            mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 + 0.02, FACE_Z - 0.035)
            tube(br, [inner, mid, outer], lambda t: 0.045 - 0.015 * t, sides=6)
    if lashes:
        la = K.hi("Lashes", "Face", "Head", "1d1716")
        for sgn in (-1, 1):
            tube(la, [(sgn * (eye_x - eye_w), eye_y + eye_h * 0.5, FACE_Z - 0.03), (sgn * eye_x, eye_y + eye_h * 1.05, FACE_Z - 0.035),
                      (sgn * (eye_x + eye_w * 1.25), eye_y + eye_h * 0.75, FACE_Z - 0.03)], lambda t: 0.022, sides=5)
    if mouth and mouth_pts:
        mo = K.hi("Mouth", "Face", "Head", mouth)
        tube(mo, [(x, y, FACE_Z - 0.02) for x, y in mouth_pts], lambda t: mouth_w * (1 - 0.4 * abs(2 * t - 1)), sides=6)
    if nose:
        no = K.hi("Nose", "Face", "Head", nose)
        lathe_y(no, (0, 0, FACE_Z - 0.05), [(1.74, 0.02), (1.7, 0.06), (1.6, 0.085), (1.56, 0.02)], n=10, p=2.4, b_scale=0.9)
    if blush:
        bl = K.hi("Blush", "Face", "Head", blush)
        for sgn in (-1, 1):
            spot(bl, sgn * 0.34, 1.6, 0.08, 0.045, depth=0.01)


# ---------- the Forgemaster (the Blacksmith) ----------
# A broad, weathered smith: a slate tunic (his torso's colour), bare forearms in leather bracers banded with gold, a heavy
# leather apron from chest to knee with the forge's gold anvil sigil, a thick belt with tongs at the hip, a steel pauldron on
# his left shoulder (the hand that holds the work), heavy boots capped in gold, a short copper crop and a full braided beard;
# in his right hand a great forge hammer, its steel head banded in gold, hanging by his leg.
def forgemaster():
    K = Kit("Forgemaster")
    BODY_COLOURS["Forgemaster"] = {"Head": hexrgb("c98b62"), "Torso": hexrgb("3c4048"), "Arms": hexrgb("c98b62"), "Legs": hexrgb("4a3426")}
    LEATHER, DARK_LEATHER, GOLD, STEEL, HAIR = "6b4128", "3e2618", "e2b240", "a9b0ba", "b0562a"

    # the apron: a leather sheet from the chest to the knees, curving round the front, its bib narrower than its skirt
    ap = K.hi("Apron", "Leather", "UpperTorso", LEATHER)
    rows = []
    for j in range(15):
        v = j / 14
        y = 0.92 + (-2.05 - 0.92) * v
        half = 0.62 + (1.02 - 0.62) * min(1.0, max(0.0, (0.55 - y) / 1.1))          # the bib widens into the skirt at the waist
        bulge = 0.08 * math.sin(math.pi * min(1.0, v * 1.4))                          # over the belly
        row = []
        for i in range(9):
            u = -1 + 2 * i / 8
            x = u * half
            z = -0.53 - bulge - (0.05 if y < -0.75 else 0.0) * (1 - u * u) + 0.06 * u * u + (0.12 * (y + 0.75) if y < -0.75 else 0)
            row.append(V((x, y, z - 0.02)))
        rows.append(row)
    sheet(ap, rows, lambda j, i: (0, 0, -1), 0.05)
    # its neck strap and its waist ties, a gold rivet at each corner of the bib, the anvil sigil on the chest
    st = K.hi("Straps", "Leather", "UpperTorso", DARK_LEATHER)
    for s in (-1, 1):
        tube(st, [(s * 0.55, 0.9, -0.58), (s * 0.5, 1.1, -0.3), (s * 0.35, 1.16, 0.0), (0.0, 1.14, 0.4)], 0.05, sides=6)
    tube(st, [(-1.0, -0.62, -0.42), (-1.02, -0.62, 0.0), (-0.9, -0.62, 0.5), (0.0, -0.62, 0.55), (0.9, -0.62, 0.5), (1.02, -0.62, 0.0), (1.0, -0.62, -0.42)],
         0.06, sides=6)
    gold = K.hi("Studs", "Gold", "UpperTorso", GOLD)
    for x, y in ((-0.56, 0.86), (0.56, 0.86), (-0.95, -0.55), (0.95, -0.55)):
        O.sphere(gold, (x, y, -0.62), 0.06, 0, 8, 5)
    sig = K.hi("Sigil", "Gold", "UpperTorso", GOLD)
    box(sig, (0, 0.42, -0.66), (0.42, 0.1, 0.05))      # the anvil's face
    box(sig, (0, 0.3, -0.66), (0.16, 0.16, 0.05))      # its waist
    box(sig, (0, 0.18, -0.66), (0.34, 0.08, 0.05))     # its foot
    box(sig, (0.26, 0.44, -0.66), (0.14, 0.05, 0.05))  # its horn

    # the belt: thick leather round the waist over the apron, a square gold buckle, tongs hanging at the right hip
    belt = K.hi("Belt", "Leather", "LowerTorso", DARK_LEATHER)
    O.tube_shell(belt, (0, 0), [(-0.56, 1.05, 0.6), (-0.8, 1.06, 0.61)], 0, n=40, p=4.5)
    bk = K.hi("Buckle", "Gold", "LowerTorso", GOLD)
    box(bk, (0, -0.68, -0.66), (0.36, 0.3, 0.06))
    box(bk, (0, -0.68, -0.7), (0.2, 0.14, 0.04))
    tg = K.hi("Tongs", "Steel", "LowerTorso", STEEL)
    for dx in (-0.05, 0.05):
        tube(tg, [(1.12, -0.75, -0.2 + dx), (1.16, -1.3, -0.25 + dx * 1.5), (1.18, -1.7, -0.28 + dx * 2.5)], 0.035, sides=5)

    # bracers on both forearms, flaring a little at the elbow, two gold bands each
    for side, part in ((-1, "LeftLowerArm"), (1, "RightLowerArm")):
        x = side * 1.472
        br = K.hi(("L" if side < 0 else "R") + "Bracer", "Leather", part, LEATHER)
        O.tube_shell(br, (x, 0), [(0.08, 0.56, 0.56), (-0.3, 0.545, 0.545), (-0.66, 0.535, 0.535)], 0, n=32, p=7.0, cap_top=(0.08, 0.5, 0.5))
        bd = K.hi(("L" if side < 0 else "R") + "BracerBands", "Gold", part, GOLD)
        for y in (0.0, -0.58):
            O.tube_shell(bd, (x, 0), [(y + 0.04, 0.575, 0.575), (y - 0.04, 0.575, 0.575)], 0, n=32, p=7.0)

    # the pauldron on the left shoulder: three steel lames, each overlapping the next, edged in gold
    pa = K.hi("Pauldron", "Steel", "LeftUpperArm", STEEL)
    pe = K.hi("PauldronEdge", "Gold", "LeftUpperArm", GOLD)
    x = -1.472
    for k, (y, r) in enumerate(((1.12, 0.66), (0.88, 0.7), (0.64, 0.72))):
        rows = O.tube_shell(pa, (x, 0), [(y + 0.18, r * 0.82, r * 0.82), (y - 0.12, r, r)], 0, n=24, p=2.6, dome=0.18 if k == 0 else None)
        O.tube_shell(pe, (x, 0), [(y - 0.1, r + 0.02, r + 0.02), (y - 0.16, r + 0.02, r + 0.02)], 0, n=24, p=2.6)

    # boots: a heavy cuff, the shaft, the foot, a gold toe cap
    for side, part in ((-1, "LeftLowerLeg"), (1, "RightLowerLeg")):
        x = side * 0.498
        bo = K.hi(("L" if side < 0 else "R") + "Boot", "Leather", part, DARK_LEATHER)
        O.tube_shell(bo, (x, 0), [(-1.78, 0.58, 0.57), (-1.95, 0.56, 0.55), (-2.6, 0.535, 0.53), (-2.86, 0.54, 0.54)], 0, n=24, p=3.2)
        lathe_y(bo, (x, 0, -0.06), [(-2.8, 0.5), (-2.86, 0.54), (-3.19, 0.56)], n=24, p=3.2, b_scale=1.08)
        tc = K.hi(("L" if side < 0 else "R") + "ToeCap", "Gold", part, GOLD)
        box(tc, (x, -3.0, -0.58), (0.9, 0.34, 0.12))

    # hair: a short crop hugging the blocky head, the hairline above the brow, lower at the back
    hair_cap(K.hi("Hair", "Hair", "Head", HAIR), front=1.99, back=1.62, thick=0.05)
    # the beard: sideburns from the ears down round the jaw to a broad, squared mass under the mouth, braided at the chin
    bd = K.hi("Beard", "Hair", "Head", HAIR)
    beard(bd, top_front=1.43, top_side=1.86, bottom=1.02, depth=0.2)
    tube(bd, [(0, 1.06, -0.74), (0, 0.8, -0.76), (0, 0.56, -0.74)], lambda t: 0.12 - 0.05 * t, sides=8, tip=True)
    mo = K.hi("Moustache", "Hair", "Head", HAIR)
    for sgn in (-1, 1):
        tube(mo, [(sgn * 0.04, 1.52, -0.63), (sgn * 0.2, 1.5, -0.65), (sgn * 0.34, 1.43, -0.64), (sgn * 0.4, 1.34, -0.62)], lambda t: 0.065 - 0.03 * t, sides=6, tip=True)
    rg = K.hi("BeardRing", "Gold", "Head", GOLD)
    O.tube_shell(rg, (0, -0.75), [(0.86, 0.125, 0.125), (0.76, 0.125, 0.125)], 0, n=12, p=2.0)

    # the hammer in his right hand: a wrapped haft down by his leg, a steel head banded in gold
    hx, hz = 1.472, -0.08
    face(K, "2b1d16", HAIR, None, eye_w=0.085, eye_h=0.095, eye_y=1.76, brow_y=1.9, brow_tilt=(-0.04, -0.04), brow_w=0.15, nose=hexrgb("c07f57"))
    hm = K.hi("HammerHaft", "Wood", "RightHand", "5a3a22")
    tube(hm, [(hx, -0.55, hz), (hx, -1.3, hz), (hx, -2.25, hz)], 0.075, sides=8)
    hw = K.hi("HammerGrip", "Leather", "RightHand", DARK_LEATHER)
    O.tube_shell(hw, (hx, hz), [(-0.6, 0.095, 0.095), (-1.1, 0.095, 0.095)], 0, n=10, p=2.0)
    hh = K.hi("HammerHead", "Steel", "RightHand", STEEL)
    box(hh, (hx, -2.42, hz), (0.42, 0.42, 0.95))
    box(hh, (hx, -2.42, hz - 0.55), (0.34, 0.34, 0.16))
    hb = K.hi("HammerBands", "Gold", "RightHand", GOLD)
    for dz in (-0.3, 0.3):
        box(hb, (hx, -2.42, hz + dz), (0.46, 0.46, 0.08))
    return K


# ---------- shared dress ----------
def sleeve(K, side, piece, mat, colour, top=1.04, bottom=-0.66, a=0.55, cuff=None, cuff_colour=None):
    """A sleeve over a blocky arm: its upper part rides the upper arm, its lower the lower arm (they overlap at the elbow)."""
    sx = "L" if side < 0 else "R"
    x = side * 1.472
    up = K.hi(sx + piece + "Upper", mat, ("Left" if side < 0 else "Right") + "UpperArm", colour)
    O.tube_shell(up, (x, 0), [(top, a, a), (-0.1, a, a)], 0, n=32, p=7.0, dome=0.06)
    lo = K.hi(sx + piece + "Lower", mat, ("Left" if side < 0 else "Right") + "LowerArm", colour)
    O.tube_shell(lo, (x, 0), [(0.05, a - 0.008, a - 0.008), (bottom, a + 0.02, a + 0.02)], 0, n=32, p=7.0, cap_top=(0.05, 0.5, 0.5))
    if cuff:
        cf = K.hi(sx + piece + "Cuff", cuff, ("Left" if side < 0 else "Right") + "LowerArm", cuff_colour)
        O.tube_shell(cf, (x, 0), [(bottom + 0.12, a + 0.035, a + 0.035), (bottom - 0.01, a + 0.04, a + 0.04)], 0, n=32, p=7.0)


def boots(K, mat, colour, top=-1.85, a=0.53, toe=None, toe_colour=None, cuff=None, cuff_colour=None):
    for side in (-1, 1):
        sx = "L" if side < 0 else "R"
        x = side * 0.498
        part = ("Left" if side < 0 else "Right") + "LowerLeg"
        bo = K.hi(sx + "Boot", mat, part, colour)
        O.tube_shell(bo, (x, 0), [(top, a + 0.02, a + 0.02), (top - 0.2, a, a), (-2.86, a - 0.005, a - 0.005)], 0, n=32, p=7.0, cap_top=(top, 0.49, 0.48))
        lathe_y(bo, (x, 0, -0.05), [(-2.8, 0.5), (-2.86, 0.535), (-3.19, 0.55)], n=32, p=7.0, b_scale=1.08)
        if toe:
            tc = K.hi(sx + "ToeCap", toe, part, toe_colour)
            box(tc, (x, -3.02, -0.58), (0.86, 0.3, 0.1))
        if cuff:
            cf = K.hi(sx + "BootCuff", cuff, part, cuff_colour)
            O.tube_shell(cf, (x, 0), [(top + 0.06, a + 0.05, a + 0.05), (top - 0.12, a + 0.045, a + 0.045)], 0, n=32, p=7.0)


def egg(hi, c, r, n=16):
    cx, cy, cz = c
    prof = []
    for k in range(9):
        a = math.pi * k / 8
        rr = max(0.01, r * math.sin(a) * (0.82 + 0.18 * k / 8))
        prof.append((cy + r * 1.3 * math.cos(a) * (1.0 if a < math.pi / 2 else 0.85), rr))
    lathe_y(hi, (cx, 0, cz), prof, n=n, p=2.0)


def coat_torso(K, piece, mat, colour, top=1.1, bottom=-0.62, a=1.03, b=0.56, open_deg=0, p=6.0):
    """A coat or robe round the torso, closed over the shoulders; open_deg leaves a V open at the front."""
    hi = K.hi(piece, mat, "UpperTorso", colour)
    n = 64
    t0 = math.radians(open_deg)
    lv = O.fine([(top, a, b), (0.3, a, b), (bottom, a + 0.01, b + 0.01)], 0.15)
    rows = []
    for j, (y, aa, bb) in enumerate(lv):
        row = []
        # the opening narrows from the collar to nothing at the waist
        tj = t0 * max(0.0, (y - 0.0) / (top - 0.0)) if open_deg else 0.0
        for i in range(n + 1):
            t = tj + (TAU - 2 * tj) * i / n
            x, z, nrm = O.se(t, aa, bb, p)
            row.append(hi.v(V((x, y, z))))
        rows.append(row)
    uv = [[(i / n, j) for i in range(n + 1)] for j in range(len(lv))]
    O.grid_faces(hi, rows, uv, lambda j, i: O.se(t0 + (TAU - 2 * t0) * (i + 0.5) / n, 1, 1, p)[2], 0)
    yoke = [hi.v(V((O.se(t0 * 1.0 + (TAU - 2 * t0) * i / n, 0.62, 0.48, 3)[0], top + 0.02, O.se(t0 + (TAU - 2 * t0) * i / n, 0.62, 0.48, 3)[1])))
            for i in range(n + 1)]
    O.grid_faces(hi, [yoke, rows[0]], [[(i / n, -1) for i in range(n + 1)], uv[0]], lambda j, i: (0, 1, 0), 0)
    return hi


def skirt(K, piece, mat, colour, part="LowerTorso", top=-0.6, hem=-2.4, a0=1.04, b0=0.57, a1=1.22, b1=0.72, gaps=(("front", 8), ("back", 4)),
          folds=7, amp=0.05):
    """A skirt in two halves hanging from the waist, split at the front (and a little at the back), flaring to the hem."""
    hi = K.hi(piece, mat, part, colour)
    front = math.radians(dict(gaps).get("front", 0))
    back = math.radians(dict(gaps).get("back", 0))
    for sgn in (-1, 1):
        t0, t1 = (front, math.pi - back) if sgn > 0 else (-math.pi + back, -front)
        pts = []
        for j in range(19):
            v = j / 18
            f = v ** 1.2
            aa, bb = a0 + (a1 - a0) * f, b0 + (b1 - b0) * f
            row = []
            for i in range(25):
                t = t0 + (t1 - t0) * i / 24
                x, z, nrm = O.se(t, aa, bb, 5.0)
                d = O.folds(t, v, 7 + sgn, folds, lambda vv: amp * (0.2 + 0.8 * vv))
                row.append(V((x, top + (hem - top) * v, z)) + nrm * d)
            pts.append(row)
        sheet(hi, pts, lambda j, i, t0=t0, t1=t1: O.se(t0 + (t1 - t0) * (i + 0.5) / 24, 1, 1, 5.0)[2], 0.05)
    return hi


def strand(hi, pts, w0, w1, sides=8):
    """A tapered lock of hair through pts."""
    tube(hi, pts, lambda t: w0 + (w1 - w0) * t, sides=sides, tip=True)


# ---------- the Curator (the Marketplace) ----------
# A poised egg-keeper in a long lapis coat with a standing collar, two rows of gold buttons and gold piping, white gloves (her
# hands), tall dark boots, a satchel slung across her for the eggs she carries and a crystal egg held at her side; long silver
# hair in a low tail bound with gold.
def curator():
    K = Kit("Curator")
    BODY_COLOURS["Curator"] = {"Head": hexrgb("f1c9a5"), "Torso": hexrgb("ecebe6"), "Arms": hexrgb("f3f1ea"), "Legs": hexrgb("2b2c3a")}
    LAPIS, GOLD, HAIR, BOOT, STRAP = "2b4796", "e2b240", "cfd5e0", "2a1d18", "5b3a24"
    coat_torso(K, "Coat", "Fabric", LAPIS, open_deg=16)
    skirt(K, "CoatSkirt", "Fabric", LAPIS, hem=-2.45)
    col = K.hi("Collar", "Fabric", "UpperTorso", LAPIS)
    O.tube_shell(col, (0, 0.02), [(1.42, 0.62, 0.55), (1.12, 0.66, 0.58)], 0, n=40, p=5.0)
    g = K.hi("Piping", "Gold", "UpperTorso", GOLD)
    O.tube_shell(g, (0, 0.02), [(1.43, 0.635, 0.565), (1.38, 0.635, 0.565)], 0, n=40, p=5.0)
    for row_x in (-0.3, 0.3):
        for y in (0.75, 0.4, 0.05, -0.3):
            O.sphere(g, (row_x * (0.7 + 0.3 * (y + 0.3)), y, -0.58), 0.07, 0, 10, 6)
    gh = K.hi("Hem", "Gold", "LowerTorso", GOLD)
    for sgn in (-1, 1):
        pts = []
        for i in range(25):
            t = (math.radians(8) + (math.pi - math.radians(4) - math.radians(8)) * i / 24) * sgn
            x, z, _ = O.se(t, 1.235, 0.735, 5.0)
            pts.append((x, -2.42, z))
        tube(gh, pts, 0.04, sides=6)
    for side in (-1, 1):
        sleeve(K, side, "Sleeve", "Fabric", LAPIS, bottom=-0.6, cuff="Gold", cuff_colour=GOLD)
    boots(K, "Leather", BOOT, top=-1.75)
    # the satchel: a strap from her left shoulder to her right hip, a round leather case there, a crystal egg peeking out
    st = K.hi("SatchelStrap", "Leather", "UpperTorso", STRAP)
    tube(st, [(-0.7, 1.12, -0.2), (-0.55, 0.9, -0.6), (0.1, 0.2, -0.64), (0.8, -0.45, -0.6), (1.06, -0.6, -0.2)], 0.06, sides=6)
    tube(st, [(-0.7, 1.12, -0.2), (-0.6, 0.9, 0.58), (0.3, 0.1, 0.62), (1.06, -0.6, 0.2)], 0.06, sides=6)
    sc = K.hi("Satchel", "Leather", "LowerTorso", STRAP)
    lathe_y(sc, (1.12, 0, 0.0), [(-0.45, 0.32), (-0.55, 0.38), (-1.05, 0.4), (-1.15, 0.33)], n=20, p=3.0, b_scale=0.6)
    eg = K.hi("SatchelEgg", "Glass", "LowerTorso", "bfe4ff")
    egg(eg, (1.12, -0.38, 0.0), 0.2)
    he = K.hi("HeldEgg", "Glow", "LeftHand", "dff0ff")
    egg(he, (-1.472, -1.22, -0.3), 0.26)
    # hair: silver, the hairline high over the brow, long at the back, gathered low into a tail with a gold ring, two locks at the temples
    hr = K.hi("Hair", "Hair", "Head", HAIR)
    hair_cap(hr, front=2.02, back=1.25, thick=0.06)
    strand(hr, [(0, 1.5, 0.66), (0, 1.0, 0.72), (0, 0.4, 0.66), (0, -0.1, 0.62)], 0.2, 0.08)
    for sgn in (-1, 1):
        strand(hr, [(sgn * 0.6, 2.0, -0.4), (sgn * 0.64, 1.6, -0.45), (sgn * 0.6, 1.15, -0.42)], 0.1, 0.04)
    rg = K.hi("HairRing", "Gold", "Head", GOLD)
    O.tube_shell(rg, (0, 0.72), [(1.12, 0.17, 0.17), (1.0, 0.17, 0.17)], 0, n=14, p=2.0)
    face(K, "3a5fa8", "aeb6c4", "b5605a", eye_w=0.1, eye_h=0.12, brow_y=1.95, brow_tilt=(0.02, 0.02), brow_w=0.12, lashes=True,
         mouth_pts=[(-0.09, 1.5), (0.0, 1.475), (0.09, 1.5)], mouth_w=0.028, blush="f0a9a0")
    return K


# ---------- the Appraiser (Buy & Sell) ----------
# A dapper valuer: a gold brocade waistcoat over a white shirt with its sleeves rolled, a lapis bow tie, charcoal trousers,
# polished shoes, a gold monocle on a chain, a waxed moustache, slick black hair, the ledger of every trade under his arm.
def appraiser():
    K = Kit("Appraiser")
    BODY_COLOURS["Appraiser"] = {"Head": hexrgb("d9a07a"), "Torso": hexrgb("f2f1ec"), "Arms": hexrgb("f2f1ec"), "Legs": hexrgb("35353f")}
    BROCADE, GOLD, LAPIS, HAIR, SHOE, CREAM = "b98d34", "e8bc4a", "2b4796", "1e1a1a", "151214", "efe6cf"
    vest = K.hi("Waistcoat", "Fabric", "UpperTorso", BROCADE)
    n = 64
    rows = []
    lv = O.fine([(0.98, 1.0, 0.535), (0.3, 1.0, 0.535), (-0.72, 1.01, 0.545)], 0.12)
    for j, (y, a, b) in enumerate(lv):
        row = []
        t0 = math.radians(34) * max(0.0, (y - 0.15) / 0.83)     # the V of the neck, down to the top button
        for i in range(n + 1):
            t = t0 + (TAU - 2 * t0) * i / n
            x, z, _ = O.se(t, a, b, 6.0)
            yy = y - (0.14 * (1 - abs(math.sin(t * 0.5 + math.pi / 2))) if j == len(lv) - 1 else 0)   # points at the front hem
            row.append(vest.v(V((x, yy, z))))
        rows.append(row)
    O.grid_faces(vest, rows, [[(i / n, j) for i in range(n + 1)] for j in range(len(lv))],
                 lambda j, i: O.se(math.radians(34) + (TAU - 2 * math.radians(34)) * (i + 0.5) / n, 1, 1, 6.0)[2], 0)
    bt = K.hi("Buttons", "Gold", "UpperTorso", GOLD)
    for y in (0.08, -0.18, -0.44):
        O.sphere(bt, (0, y, -0.57), 0.055, 0, 10, 6)
    tube(bt, [(0, -0.18, -0.57), (0.25, -0.32, -0.6), (0.5, -0.3, -0.58)], 0.025, sides=5)      # the watch chain
    O.sphere(bt, (0.52, -0.33, -0.58), 0.09, 0, 12, 8)
    bow = K.hi("BowTie", "Fabric", "UpperTorso", LAPIS)
    for sgn in (-1, 1):
        lathe_y(bow, (sgn * 0.16, 0, -0.6), [(1.12, 0.05), (1.04, 0.12), (0.96, 0.05)], n=10, p=2.0, a_scale=1.6, b_scale=0.5)
    box(bow, (0, 1.04, -0.62), (0.1, 0.12, 0.08))
    cl = K.hi("ShirtCollar", "Cloth", "UpperTorso", "ffffff")
    for sgn in (-1, 1):
        box(cl, (sgn * 0.2, 1.08, -0.55), (0.28, 0.14, 0.06), yaw=sgn * 0.5)
    for side in (-1, 1):
        rc = K.hi(("L" if side < 0 else "R") + "RolledCuff", "Cloth", ("Left" if side < 0 else "Right") + "LowerArm", "ffffff")
        O.tube_shell(rc, (side * 1.472, 0), [(0.12, 0.56, 0.56), (-0.08, 0.565, 0.565)], 0, n=32, p=7.0, cap_top=(0.12, 0.5, 0.5))
    for side in (-1, 1):
        sh = K.hi(("L" if side < 0 else "R") + "Shoe", "Leather", ("Left" if side < 0 else "Right") + "Foot", SHOE)
        lathe_y(sh, (side * 0.498, 0, -0.06), [(-2.86, 0.5), (-2.9, 0.53), (-3.19, 0.545)], n=32, p=7.0, b_scale=1.1)
    hr = K.hi("Hair", "Hair", "Head", HAIR)
    hair_cap(hr, front=2.06, back=1.6, thick=0.05)
    box(hr, (-0.15, 2.3, -0.42), (0.7, 0.12, 0.3), yaw=0.1)     # the swept front
    mo = K.hi("Moustache", "Hair", "Head", HAIR)
    for sgn in (-1, 1):
        strand(mo, [(sgn * 0.03, 1.5, -0.62), (sgn * 0.22, 1.49, -0.64), (sgn * 0.38, 1.53, -0.63), (sgn * 0.44, 1.62, -0.6)], 0.055, 0.02, sides=6)
    # the monocle: a gold ring round his right eye, its lens, its chain down to the waistcoat
    mn = K.hi("Monocle", "Gold", "Head", GOLD)
    ring = [(0.24 + math.cos(TAU * k / 20) * 0.155, 1.74 + math.sin(TAU * k / 20) * 0.155, FACE_Z - 0.06) for k in range(21)]
    tube(mn, ring, 0.028, sides=6)
    tube(mn, [(0.39, 1.7, FACE_Z - 0.06), (0.45, 1.3, -0.64), (0.4, 0.95, -0.62), (0.3, 0.7, -0.6)], 0.016, sides=4)
    ln = K.hi("MonocleLens", "Glass", "Head", "d8eeff")
    spot(ln, 0.24, 1.74, 0.14, 0.14, z=FACE_Z - 0.06, depth=0.012)
    bk = K.hi("Ledger", "Leather", "LeftHand", "4a2a1c")
    box(bk, (-1.472, -1.05, -0.05), (0.18, 0.95, 0.72))
    pg = K.hi("LedgerPages", "Cloth", "LeftHand", CREAM)
    box(pg, (-1.472, -1.05, -0.07), (0.14, 0.88, 0.7))
    gc = K.hi("LedgerCorners", "Gold", "LeftHand", GOLD)
    for dy in (-0.44, 0.44):
        for dz in (-0.33, 0.33):
            box(gc, (-1.472, -1.05 + dy, -0.05 + dz), (0.2, 0.1, 0.1))
    # (his right eye sits behind the monocle, its brow raised in appraisal; a knowing half-smile under the moustache)
    face(K, "3b2a20", HAIR, "7a3d34", eye_x=0.24, eye_w=0.085, eye_h=0.1, eye_y=1.74, brow_y=1.9, brow_tilt=(-0.02, 0.09), brow_w=0.13,
         mouth_pts=[(-0.1, 1.43), (0.02, 1.42), (0.12, 1.45)], mouth_w=0.026, nose=hexrgb("c98d68"))
    return K


# ---------- the Guide (the Beginner Guide) ----------
# A warm, bright-eyed mentor in a sky-blue robe to the ankles under a white mantle (its hood down at her back) pinned with a gold
# clasp set with a crystal, a gold sash, soft white boots, shoulder-length golden hair, and a tall white staff crowned with a
# glowing crystal held in gold.
def guide():
    K = Kit("Guide")
    BODY_COLOURS["Guide"] = {"Head": hexrgb("ffd9b8"), "Torso": hexrgb("8fc4f0"), "Arms": hexrgb("8fc4f0"), "Legs": hexrgb("8fc4f0")}
    SKY, WHITE, GOLD, HAIR = "8fc4f0", "f4f3ee", "e2b240", "e8c25a"
    coat_torso(K, "Robe", "Fabric", SKY, a=1.02, b=0.55, p=6.0)
    skirt(K, "RobeSkirt", "Fabric", SKY, hem=-3.0, a1=1.12, b1=0.66, gaps=(("front", 0), ("back", 0)), folds=9, amp=0.04)
    # the mantle: a short white cape over the shoulders and down the back, the hood bunched at the neck behind
    mt = K.hi("Mantle", "Fabric", "UpperTorso", WHITE)
    rows = []
    for j in range(13):
        v = j / 12
        y = 1.14 - 1.0 * v - 0.45 * v * v
        row = []
        for i in range(33):
            t = math.radians(-150) + math.radians(300) * i / 32 + math.pi       # round the back, from shoulder to shoulder
            a, b = 1.06 + 0.12 * v, 0.6 + 0.12 * v
            x, z, nrm = O.se(t, a, b, 5.0)
            front_lift = 0.5 * max(0.0, math.cos(t)) ** 2                          # shorter at the front, over the arms
            row.append(V((x, y + front_lift * v, z)))
        rows.append(row)
    sheet(mt, rows, lambda j, i: O.se(math.radians(-150) + math.radians(300) * (i + 0.5) / 32 + math.pi, 1, 1, 5.0)[2], 0.05)
    hd = K.hi("Hood", "Fabric", "UpperTorso", WHITE)
    lathe_y(hd, (0, 0, 0.55), [(1.45, 0.15), (1.38, 0.42), (1.18, 0.5), (1.02, 0.3)], n=20, p=3.0, a_scale=1.3, b_scale=0.7)
    gs = K.hi("Sash", "Gold", "LowerTorso", GOLD)
    O.tube_shell(gs, (0, 0), [(-0.58, 1.05, 0.58), (-0.76, 1.055, 0.585)], 0, n=40, p=6.0)
    cl = K.hi("Clasp", "Gold", "UpperTorso", GOLD)
    O.tube_shell(cl, (0, -0.62), [(0.98, 0.16, 0.06), (0.78, 0.16, 0.06)], 0, n=16, p=2.0)
    cg = K.hi("ClaspGem", "Glow", "UpperTorso", "a8e2ff")
    O.sphere(cg, (0, 0.88, -0.69), 0.08, 0, 10, 6)
    for side in (-1, 1):
        sleeve(K, side, "Sleeve", "Fabric", SKY, bottom=-0.66, a=0.58, cuff="Gold", cuff_colour=GOLD)
    boots(K, "Leather", WHITE, top=-2.3)
    hr = K.hi("Hair", "Hair", "Head", HAIR)
    hair_cap(hr, front=2.04, back=1.15, thick=0.06)
    for sgn in (-1, 1):
        strand(hr, [(sgn * 0.6, 2.05, -0.38), (sgn * 0.66, 1.6, -0.42), (sgn * 0.68, 1.15, -0.35), (sgn * 0.7, 0.9, -0.2)], 0.15, 0.06)
        strand(hr, [(sgn * 0.45, 2.1, 0.55), (sgn * 0.5, 1.5, 0.68), (sgn * 0.48, 1.0, 0.66)], 0.2, 0.08)
    # the staff, held upright in her right hand: white, banded in gold, a crystal in a gold crown on top
    sx, sz = 1.472, -0.25
    sf = K.hi("Staff", "Wood", "RightHand", "efe9df")
    tube(sf, [(sx, FLOOR + 0.05, sz), (sx, 0.5, sz), (sx, 3.0, sz)], 0.08, sides=10)
    sb = K.hi("StaffGold", "Gold", "RightHand", GOLD)
    for y in (-0.5, -1.2, 2.2):
        O.tube_shell(sb, (sx, sz), [(y + 0.06, 0.105, 0.105), (y - 0.06, 0.105, 0.105)], 0, n=12, p=2.0)
    for k in range(4):
        a = TAU * k / 4
        tube(sb, [(sx + math.cos(a) * 0.08, 2.95, sz + math.sin(a) * 0.08), (sx + math.cos(a) * 0.28, 3.25, sz + math.sin(a) * 0.28),
                  (sx + math.cos(a) * 0.14, 3.6, sz + math.sin(a) * 0.14)], lambda t: 0.04 - 0.02 * t, sides=5)
    sc = K.hi("StaffCrystal", "Glow", "RightHand", "bfe8ff")
    lathe_y(sc, (sx, 0, sz), [(3.85, 0.02), (3.4, 0.2), (3.1, 0.02)], n=6, p=2.0)
    face(K, "2f7fc4", "c99a3a", "a8524a", eye_w=0.115, eye_h=0.14, eye_y=1.76, brow_y=1.97, brow_tilt=(0.03, 0.03), brow_w=0.12, lashes=True,
         mouth_pts=[(-0.14, 1.5), (-0.07, 1.45), (0.0, 1.44), (0.07, 1.45), (0.14, 1.5)], mouth_w=0.03, blush="f5b3a6")
    return K


# ---------- the Wandering Merchant ----------
# A traveller from beyond the islands: a plum hooded cloak to the shins, patched where the road wore it, a teal scarf over his
# mouth so only his eyes show under the hood, worn wrapped boots, a pouch-hung belt, a walking staff with a lantern swinging
# from its crook, and on his back a towering wooden pack frame laden with a crate, a rolled carpet, bundles, pots and two
# lanterns: the silhouette everyone learns to look for.
def merchant():
    K = Kit("Merchant")
    BODY_COLOURS["Merchant"] = {"Head": hexrgb("b98563"), "Torso": hexrgb("3b2a3f"), "Arms": hexrgb("5b2e5f"), "Legs": hexrgb("3a2a22")}
    PLUM, TEAL, GOLD, WOOD, LEATHER, LANTERN = "5b2e5f", "2f8a86", "d9a640", "7a5232", "4b3020", "ffc46a"
    coat_torso(K, "Cloak", "Fabric", PLUM, a=1.06, b=0.6, open_deg=10)
    skirt(K, "CloakSkirt", "Fabric", PLUM, hem=-2.65, a1=1.3, b1=0.8, folds=6, amp=0.07)
    pt = K.hi("Patches", "Fabric", "LowerTorso", "8a6a3a")
    box(pt, (0.92, -1.6, -0.62), (0.32, 0.36, 0.05), yaw=0.5)
    box(pt, (-0.7, -2.1, -0.78), (0.3, 0.28, 0.05), yaw=-0.3)
    # the hood up round the head, deep at the front so the face sits in its shade
    # (open at the front from brow to chin so the face shows, its edge rolled into a darker brim)
    hd = K.hi("Hood", "Fabric", "Head", PLUM)
    open_t = math.radians(38)
    rows = []
    for j in range(12):
        v = j / 11
        y = 2.56 - 1.46 * v
        r = 0.26 + 0.5 * math.sin(math.pi / 2 * min(1.0, v * 2.2)) + 0.05 * v
        row = []
        for i in range(29):
            t = open_t + (TAU - 2 * open_t) * i / 28
            x, z, nrm = O.se(t, r, r * 1.04, 4.0)
            row.append(V((x, y, z + 0.06 + 0.12 * v * v)))
        rows.append(row)
    sheet(hd, rows, lambda j, i: O.se(open_t + (TAU - 2 * open_t) * (i + 0.5) / 28, 1, 1, 4.0)[2], 0.06)
    fr = K.hi("HoodBrim", "Fabric", "Head", "4a2550")
    for sgn in (-1, 1):
        edge = [rows[j][0 if sgn < 0 else 28] for j in range(12)]
        tube(fr, [tuple(p_) for p_ in edge], 0.06, sides=6)
    sf = K.hi("Scarf", "Fabric", "Head", TEAL)
    O.tube_shell(sf, (0, -0.02), [(1.58, 0.62, 0.64), (1.3, 0.66, 0.68), (1.06, 0.7, 0.72)], 0, n=40, p=6.0)
    strand(sf, [(0.4, 1.2, -0.66), (0.5, 0.6, -0.7), (0.45, 0.1, -0.66)], 0.13, 0.08)
    for side in (-1, 1):
        sleeve(K, side, "Sleeve", "Fabric", PLUM, bottom=-0.62, a=0.58)
    boots(K, "Leather", LEATHER, top=-2.0, cuff="Fabric", cuff_colour="8a6a3a")
    bl = K.hi("Belt", "Leather", "LowerTorso", LEATHER)
    O.tube_shell(bl, (0, 0), [(-0.56, 1.08, 0.62), (-0.74, 1.085, 0.625)], 0, n=40, p=6.0)
    for x in (-0.75, 0.55):
        box(bl, (x, -0.9, -0.66), (0.34, 0.36, 0.2))
    # the pack: a wooden frame on his back rising over his head, its load lashed on
    pk = K.hi("PackFrame", "Wood", "UpperTorso", WOOD)
    for x in (-0.75, 0.75):
        box(pk, (x, 1.45, 0.82), (0.14, 4.3, 0.14))
    for y in (-0.5, 0.6, 1.9, 3.3):
        box(pk, (0, y, 0.82), (1.75, 0.12, 0.12))
    crate = K.hi("PackCrate", "Wood", "UpperTorso", "8a6038")
    box(crate, (0, 0.05, 1.25), (1.5, 1.0, 0.8))
    rug = K.hi("PackRug", "Fabric", "UpperTorso", "a3342e")
    tube(rug, [(-1.05, 1.0, 1.15), (1.05, 1.0, 1.15)], 0.3, sides=12)
    bd = K.hi("PackBundles", "Fabric", "UpperTorso", "c9b38a")
    lathe_y(bd, (-0.3, 0, 1.1), [(2.6, 0.2), (2.4, 0.42), (1.45, 0.45), (1.3, 0.3)], n=16, p=2.4)
    lathe_y(bd, (0.4, 0, 1.15), [(2.25, 0.15), (2.1, 0.35), (1.45, 0.38), (1.32, 0.25)], n=16, p=2.4)
    pot = K.hi("PackPots", "Steel", "UpperTorso", "9a6a42")
    lathe_y(pot, (0.1, 0, 1.0), [(3.25, 0.18), (3.15, 0.3), (2.8, 0.35), (2.65, 0.2)], n=14, p=2.0)
    lg = K.hi("PackLanterns", "Gold", "UpperTorso", GOLD)
    ll = K.hi("PackLanternLights", "Glow", "UpperTorso", LANTERN)
    for x, y in ((-1.0, 2.2), (1.0, 1.6)):
        tube(lg, [(x * 0.82, y + 0.55, 0.85), (x, y + 0.55, 0.85), (x, y + 0.35, 0.85)], 0.025, sides=4)
        box(lg, (x, y + 0.3, 0.85), (0.3, 0.06, 0.3))
        box(lg, (x, y - 0.3, 0.85), (0.3, 0.06, 0.3))
        box(ll, (x, y, 0.85), (0.22, 0.5, 0.22))
    # the walking staff in his right hand, a crook at the top with a lantern hanging from it
    sx, sz = 1.472, -0.25
    st = K.hi("Staff", "Wood", "RightHand", "5e3f26")
    tube(st, [(sx, FLOOR + 0.05, sz), (sx, 1.0, sz), (sx, 2.7, sz), (sx + 0.15, 3.05, sz - 0.05), (sx + 0.45, 3.05, sz - 0.1), (sx + 0.55, 2.85, sz - 0.1)],
         0.07, sides=8)
    lt = K.hi("StaffLantern", "Gold", "RightHand", GOLD)
    tube(lt, [(sx + 0.55, 2.85, sz - 0.1), (sx + 0.55, 2.55, sz - 0.1)], 0.02, sides=4)
    box(lt, (sx + 0.55, 2.5, sz - 0.1), (0.32, 0.06, 0.32))
    box(lt, (sx + 0.55, 1.95, sz - 0.1), (0.36, 0.08, 0.36))
    lw = K.hi("StaffLanternLight", "Glow", "RightHand", LANTERN)
    box(lw, (sx + 0.55, 2.22, sz - 0.1), (0.24, 0.48, 0.24))
    # only his eyes show between the hood and the scarf: amber, with a glint of something not quite of these islands
    face(K, "ffb347", "2a1a14", None, eye_w=0.1, eye_h=0.075, eye_y=1.8, brow_y=1.93, brow_tilt=(-0.05, -0.05), brow_w=0.13, glow_eyes=True)
    return K


# ---------- the Wandering Merchant's camp (around him, on the grass; its origin on the ground at his spot, +Z toward the tree) ----------
def camp():
    K = Kit("Camp")
    RUG, BORDER, WOOD, GOLD, LANTERN = "8e2f2a", "d9a640", "7a5232", "d9a640", "ffc46a"
    rug = K.hi("Rug", "Fabric", "Ground", RUG)
    box(rug, (0, 0.04, 2.2), (4.6, 0.08, 3.2))
    bd = K.hi("RugBorder", "Trim", "Ground", BORDER)
    for sx, sz, w, d in ((0, 0.65, 4.6, 0.2), (0, 3.75, 4.6, 0.2), (-2.2, 2.2, 0.2, 3.2), (2.2, 2.2, 0.2, 3.2)):
        box(bd, (sx, 0.09, sz), (w, 0.04, d))
    cr = K.hi("Crates", "Wood", "Ground", WOOD)
    box(cr, (2.9, 0.55, -0.4), (1.3, 1.1, 1.3), yaw=0.3)
    box(cr, (2.75, 1.45, -0.3), (0.9, 0.7, 0.9), yaw=-0.2)
    box(cr, (-3.0, 0.5, -0.6), (1.4, 1.0, 1.0), yaw=-0.25)
    ch = K.hi("Chest", "Wood", "Ground", "5e3f26")
    box(ch, (0, 0.35, 2.4), (1.5, 0.6, 0.9))
    cg = K.hi("ChestGold", "Gold", "Ground", GOLD)
    for dx in (-0.55, 0.55):
        box(cg, (dx, 0.36, 2.4), (0.12, 0.64, 0.94))
    box(cg, (0, 0.5, 1.93), (0.2, 0.2, 0.05))
    # three eggs on the rug and a jar of glowing stones: his goods
    eg = K.hi("RugEggs", "Glass", "Ground", "c9e6ff")
    for x, z in ((-1.4, 1.6), (-0.9, 3.0), (1.5, 3.1)):
        egg(eg, (x, 0.4, z), 0.24)
    st = K.hi("RugStones", "Glow", "Ground", "8ff0d8")
    for k, (x, z) in enumerate(((1.4, 1.4), (1.6, 1.6), (1.25, 1.65))):
        spot(st, x, 0.18, 0.12, 0.1, z=z, depth=0.12)
    # a lantern pole at the rug's corner
    lp = K.hi("LanternPole", "Wood", "Ground", WOOD)
    tube(lp, [(-2.6, 0.0, 3.6), (-2.6, 3.4, 3.6), (-2.2, 3.6, 3.6), (-1.9, 3.5, 3.6)], 0.08, sides=8)
    lg = K.hi("Lantern", "Gold", "Ground", GOLD)
    tube(lg, [(-1.9, 3.5, 3.6), (-1.9, 3.2, 3.6)], 0.02, sides=4)
    box(lg, (-1.9, 3.15, 3.6), (0.36, 0.06, 0.36))
    box(lg, (-1.9, 2.55, 3.6), (0.4, 0.08, 0.4))
    ll = K.hi("LanternLight", "Glow", "Ground", LANTERN)
    box(ll, (-1.9, 2.85, 3.6), (0.26, 0.52, 0.26))
    return K


NPCS = {"Forgemaster": forgemaster, "Curator": curator, "Appraiser": appraiser, "Guide": guide, "Merchant": merchant}
# what shows over each one's head
TITLES = {"Forgemaster": "Brann, Forgemaster", "Curator": "Lyra, Egg Curator", "Appraiser": "Corvin, Appraiser", "Guide": "Seren, Guide",
          "Merchant": "Wandering Merchant"}


def export():
    """assets/npcs/HubNpcs.fbx: every NPC's pieces round the HumanoidRootPart at the origin, the Merchant's camp round its spot;
    and src/worldbuild/Placements/HubNpcs.lua (each piece's body part, each NPC's colours). WB.storeKit("HubNpcs", <import>, "NPC_Anchor")."""
    coll = W.collection("NPC_Export")
    W.clear_collection(coll)
    PIECES.clear()
    objs = []
    for npc, fn in list(NPCS.items()) + [("Camp", camp)]:
        objs += fn().objects(coll)
    path = os.path.join(W.REPO, "assets", "npcs", "HubNpcs.fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    W.export_batch(objs, path, image=None, anchor_name="NPC_Anchor")
    write_placements()
    return path, objs


def write_placements(path=os.path.join(W.REPO, "src", "worldbuild", "Placements", "HubNpcs.lua")):
    c3 = lambda rgb: "Color3.fromRGB(%d, %d, %d)" % tuple(rgb)
    L = ["-- Generated by tools/blender/npcs/hub_npcs.py (the hub's people, 2026-11-12). Do not edit by hand.",
         "-- Pieces: each <Npc>_<Piece> and the body part it rides (\"Ground\": the Merchant's camp, anchored).",
         "-- Colours: per NPC, each <Piece>__<Material> part's colour. Body: each NPC's body part colours (its base clothes).",
         "-- Materials: the Roblox material of each suffix. Titles: the name over each one's head.", "return {", "    Pieces = {"]
    for name in sorted(PIECES):
        L.append('        %s = "%s",' % (name, PIECES[name]))
    L.append("    },")
    L.append("    Colours = {")
    for npc in sorted(COLOURS):
        L.append("        %s = {" % npc)
        for key in sorted(COLOURS[npc]):
            L.append('            ["%s"] = %s,' % (key, c3(COLOURS[npc][key])))
        L.append("        },")
    L.append("    },")
    L.append("    Body = {")
    for npc in sorted(BODY_COLOURS):
        b = BODY_COLOURS[npc]
        L.append("        %s = { Head = %s, Torso = %s, Arms = %s, Legs = %s }," % (npc, c3(b["Head"]), c3(b["Torso"]), c3(b["Arms"]), c3(b["Legs"])))
    L.append("    },")
    L.append("    Materials = {")
    for suffix, (mat, _, _) in sorted(MATERIALS.items()):
        L.append('        %s = Enum.Material.%s,' % (suffix, mat))
    L.append("    },")
    L.append("    Titles = {")
    for npc, title in sorted(TITLES.items()):
        L.append('        %s = "%s",' % (npc, title))
    L.append("    },")
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return path



# ---------- the stand-in body and preview ----------
def stand_in(coll, npc):
    import bmesh
    cols = BODY_COLOURS.get(npc, {})
    group = {"Head": "Head", "UpperTorso": "Torso", "LowerTorso": "Torso"}
    out = []
    for part, (c, s) in BODY.items():
        g = group.get(part, "Arms" if "Arm" in part or "Hand" in part else "Legs")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.12, segments=3, affect="EDGES")
        me = bpy.data.meshes.new("SI_" + part)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("SI_" + part, me)
        o.scale = (s[0], s[2], s[1])
        o.location = W.rb(*c)
        coll.objects.link(o)
        rgb = cols.get(g, (200, 200, 200))
        m = bpy.data.materials.new("si_" + part)
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (*(srgb(c_) for c_ in rgb), 1)
        b.inputs["Roughness"].default_value = 0.6
        me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
        out.append(o)
    return out


def srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def preview_materials(objs, npc):
    for o in objs:
        name = o.name[len(npc) + 1:]
        piece, _, material = name.partition("__")
        rgb = COLOURS[npc].get(name, (200, 200, 200))
        _, rough, metal = MATERIALS.get(material, ("", 0.6, 0.0))
        m = bpy.data.materials.new("pv_" + o.name)
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (*(srgb(c) for c in rgb), 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if material == "Glow":
            b.inputs["Emission Color"].default_value = (*(srgb(c) for c in rgb), 1)
            b.inputs["Emission Strength"].default_value = 3.0
        if material == "Glass":
            b.inputs["Alpha"].default_value = 0.5
        o.data.materials.clear()
        o.data.materials.append(m)


def build(npc, with_body=True):
    coll = W.collection("NPC_" + npc)
    W.clear_collection(coll)
    K = NPCS[npc]()
    objs = K.objects(coll)
    body = stand_in(coll, npc) if with_body else []
    return objs, body


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

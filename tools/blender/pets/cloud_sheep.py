"""The Cloud Sheep (Uncommon, Clouds; Spirit Breeze Egg): "A satin sheep under a mantle of scroll-curl clouds, always half asleep. It paddles its hooves on the air as if it were swimming."

A new creature. A fat little sheep whose fleece is a real cumulus: billowing lobes, sunlit on top, going blue-grey underneath, a silver lining along the edge. Out of it come a small slate-blue face,
drooping ears, little curled horns, and four thin legs that paddle at nothing. Its lids are always half down, and it nods off in mid air. Its lobes sit on their own bones, so it swells as it breathes.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/cloud_sheep.py -- [paint|all] [review dir]

Faces -Y, Z up. (Its hooves stand on z = GROUND, as it hovers anyway: the game centres it.) The maps go to assets/pets/SpiritBreezeEgg/.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "CloudSheep"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "SpiritBreezeEgg")

SUNLIT, WHITE, HAZE, RAIN = rgb(255, 253, 248), rgb(244, 247, 252), rgb(196, 210, 232), rgb(128, 146, 186)
SILVER, SLATE, DUSK, BLUSH = rgb(236, 240, 250), rgb(74, 88, 124), rgb(40, 48, 78), rgb(206, 150, 170)
HORN_A, HORN_B = rgb(236, 214, 170), rgb(160, 120, 88)

CENTRE = V(0, 0.12, 0.76)
RADII = (0.40, 0.58, 0.34)
EYE_R = 0.045
EYE_C = V(0.098, -0.672, 0.722)
EYE_AXIS = V(0.66, -0.73, 0.14).normalized()
LID_UP, LID_LOW = (9.0, 92.0, 0.0034), (-34.0, -125.0, 0.0028)     # the upper lid rests half down: always half asleep
BLINK_U, BLINK_L = 26.0, 14.0
HEADS = ((V(0, -0.60, 0.70), (0.135, 0.165, 0.122)), (V(0, -0.745, 0.635), (0.098, 0.105, 0.08)))
GROUND = 0.2
FRONT = [V(0.165, -0.20, 0.58), V(0.165, -0.225, 0.40), V(0.165, -0.20, 0.25)]
HIND = [V(0.175, 0.44, 0.58), V(0.175, 0.475, 0.40), V(0.175, 0.44, 0.25)]
LEGS = (("FL", 1, FRONT), ("FR", -1, FRONT), ("BL", 1, HIND), ("BR", -1, HIND))
LEG_R = (0.066, 0.05, 0.04)


def leg_radius(f):
    return float(np.interp(f, (0, 0.5, 1), LEG_R))


def leg_path(side, knots):
    return catmull([mir(p, side) for p in knots], 8)


def wool_lobes():
    """Hand-set, and not mirrored: a cloud is never symmetrical. (centre, radius)"""
    big = [((0.0, 0.10, 1.03), 0.235), ((0.20, -0.14, 0.98), 0.205), ((-0.19, 0.30, 1.0), 0.215), ((0.20, 0.36, 0.95), 0.205), ((-0.20, -0.20, 0.96), 0.19), ((0.03, -0.28, 1.01), 0.17), ((0.02, 0.50, 0.95), 0.2),
           ((0.34, 0.08, 0.80), 0.2), ((-0.35, 0.12, 0.82), 0.205), ((0.31, -0.22, 0.75), 0.175), ((-0.32, -0.20, 0.74), 0.17), ((0.32, 0.42, 0.74), 0.18), ((-0.31, 0.46, 0.76), 0.185), ((0.0, 0.66, 0.78), 0.165)]
    small = [((0.11, 0.0, 1.17), 0.1), ((-0.1, 0.2, 1.17), 0.105), ((0.11, 0.36, 1.1), 0.09), ((-0.09, -0.14, 1.1), 0.09), ((0.31, 0.14, 0.97), 0.095), ((-0.3, 0.02, 0.98), 0.095), ((-0.27, 0.42, 0.94), 0.09), ((0.28, -0.12, 0.92), 0.08),
             ((0.42, 0.26, 0.76), 0.09), ((-0.43, 0.3, 0.78), 0.085), ((0.4, -0.08, 0.72), 0.08), ((-0.42, -0.06, 0.7), 0.085)]
    under = [((0.2, 0.1, 0.58), 0.15), ((-0.2, 0.12, 0.58), 0.155), ((0.0, 0.28, 0.56), 0.16), ((0.0, -0.1, 0.57), 0.155), ((0.22, 0.34, 0.60), 0.13), ((-0.22, 0.36, 0.6), 0.13), ((0.26, -0.2, 0.6), 0.125), ((-0.26, -0.22, 0.6), 0.12)]
    # the bib under its chin, and the cap on its head
    head = [((0.0, -0.42, 0.68), 0.15), ((0.15, -0.34, 0.76), 0.115), ((-0.15, -0.34, 0.77), 0.115), ((0.0, -0.40, 0.87), 0.135),
            ((0.0, -0.56, 0.815), 0.09), ((0.05, -0.49, 0.84), 0.07), ((-0.05, -0.49, 0.845), 0.07), ((0.0, -0.635, 0.80), 0.056)]
    return [(V(*c), r) for c, r in big + small + under + head]


def curds(lobes, seed=5):
    """A cumulus is built like a cauliflower: small round heads crowding on the big ones. They have no regular spacing, so it never reads as balls."""
    rng = np.random.default_rng(seed)
    out = []
    for c, r in lobes:
        for _ in range(int(5 + r * 55)):
            d = rng.normal(size=3)
            d /= np.linalg.norm(d)
            d[2] = abs(d[2]) * 0.9 + d[2] * 0.1     # most of it on the upper side; the base of a cloud is flatter
            d /= np.linalg.norm(d)
            size = r * rng.uniform(0.2, 0.46)
            out.append((c + Vector(d) * r * 0.86, size))
    return out


LOBES = wool_lobes()
# keep the face clear, and a place for each horn
LOBES = LOBES + [(c, r) for c, r in curds(LOBES) if not (c.y < -0.5 and c.z < 0.78) and not (c.y < -0.62) and not (abs(c.x) > 0.07 and c.y < -0.38 and c.z < 0.96) and c.y > -0.52]     # (no curd may overhang the brow: the bake would pick it up)
TAIL_C = V(0.0, 0.83, 0.79)
TAIL_LOBES = [(TAIL_C, 0.085), (TAIL_C + V(0.05, 0.05, 0.05), 0.05), (TAIL_C + V(-0.04, 0.06, -0.02), 0.045)]


def build_skin():
    m = Mesh()
    m.ball(CENTRE, RADII)
    for c, r in LOBES + TAIL_LOBES:
        m.ball(c, (r, r, r), 20, 12)
    for c, r in HEADS:
        m.ball(c, r, 40, 26)
    m.tube([V(0, -0.34, 0.74), V(0, -0.46, 0.72), V(0, -0.58, 0.70)], lambda f: 0.11, sides=16)     # the neck, hidden by the bib
    for side in (1, -1):
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.012, (0.05, 0.05, 0.05), 20, 14)      # the socket
        m.ball(V(side * 0.102, -0.665, 0.778), (0.04, 0.06, 0.024), 18, 12)      # the heavy brow
    c = m.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.009, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 5})])
    # the body and head alone, for the game mesh: QuadriFlow can wreck anything as thin as a leg, so those get hand-built tubes
    body = bpy.data.objects.new(N + "BodyOnly", c.data.copy())
    HI.objects.link(body)
    body.hide_render = True
    thin = Mesh()
    for key, side, knots in LEGS:
        thin.tube(leg_path(side, knots), leg_radius, sides=18, flat=0.9)
        thin.ball(mir(knots[1], side), (0.046, 0.05, 0.05), 16, 12)
    th = thin.finish(N + "ThinHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0046, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c, body


def ball_field(P, balls):
    """Per point: how far outside the nearest of these balls, in units of its radius (under 0 is inside)."""
    best = np.full(len(P), 1e9)
    for c, r in balls:
        rr = np.array(r if isinstance(r, tuple) else (r, r, r))
        best = np.minimum(best, np.linalg.norm((P - np.array(tuple(c))) / rr, axis=1) - 1)
    return best


def wool_mask(P):
    """1 where the point is fleece, 0 where it is hide: whichever surface it lies nearer to."""
    face = list(HEADS)
    for side in (1, -1):
        face += [(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.012, (0.05, 0.05, 0.05)), (V(side * 0.102, -0.665, 0.778), (0.04, 0.06, 0.024))]
    hide = ball_field(P, face)
    for key, side, knots in LEGS:
        f, d = nearest_on(leg_path(side, knots), P)
        hide = np.minimum(hide, (d - np.interp(f, (0, 0.5, 1), LEG_R)) / 0.05)
    wool = ball_field(P, LOBES + TAIL_LOBES + [(CENTRE, RADII)])
    mask = smooth(0.03, -0.03, wool - hide)
    # nothing of the fleece on the brow, whatever curd lies near it
    edge = 0.05 + 1.1 * np.maximum(0.0, P[:, 2] - 0.80)      # a V of a hairline: it widens going up the forehead
    return mask * (1 - smooth(-0.575, -0.6, P[:, 1]) * smooth(edge, edge + 0.02, np.abs(P[:, 0])))


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    wool = wool_mask(P)
    up = Nn[:, 2]
    # the fleece's billows, then fine tufts: ridged noise, puffed outward
    billow = 1 - np.abs(2 * fbm(P, 6.0, 4, 7) - 1)
    tuft = 1 - np.abs(2 * fbm(P, 26.0, 3, 19) - 1)
    # lit from above like a real cumulus: warm at the crown, white, then haze, then rain-grey beneath
    col = mix(RAIN, HAZE, smooth(-0.85, -0.3, up))
    col = mix(col, WHITE, smooth(-0.3, 0.2, up))
    col = mix(col, SUNLIT, smooth(0.4, 0.95, up))
    col = mix(col, HAZE, smooth(0.55, 0.3, billow) * smooth(-0.3, 0.3, up) * 0.3)
    # the silver lining: where the fleece turns under, a bright, faintly metallic rim
    lining = (1 - smooth(0.0, 0.16, np.abs(up + 0.34))) * (1 - smooth(0.60, 0.68, z)) * smooth(0.45, 0.6, billow)
    col = mix(col, SILVER, lining * 0.9)
    # the hide
    hide = mix(SLATE, DUSK, smooth(0.1, 0.65, up))
    hide = mix(hide, DUSK, smooth(0.44, 0.3, z) * 0.9)
    hide = mix(hide, mix(SLATE, HAZE, 0.5), smooth(-0.76, -0.84, y) * smooth(0.4, -0.2, up) * (z > 0.45))      # the pale muzzle
    for side in (1, -1):
        cheek = np.exp(-(((x - side * 0.1) / 0.05) ** 2 + ((y + 0.72) / 0.05) ** 2 + ((z - 0.655) / 0.03) ** 2))
        hide = mix(hide, BLUSH, cheek * 0.5)
        nost = np.exp(-(((x - side * 0.03) / 0.011) ** 2 + ((z - 0.648) / 0.011) ** 2)) * (y < -0.78)
        hide = mix(hide, DUSK * 0.5, nost)
    col = mix(hide, col, wool)
    rough = 0.78 + (0.93 - 0.78) * wool - 0.25 * lining * wool
    disp = wool * (0.009 * (billow - 0.5) + 0.0035 * (tuft - 0.5))
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, rough, lining * wool * 0.6)


def eye_paint(o, fr):
    """A sheep's eye, in that blue face: pale gold, a soft wide pupil, half hidden by its lid."""
    px, py, a = eye_coords(o, fr)
    IRIS = 0.86
    r = np.where(a > 0, np.sqrt(px ** 2 + py ** 2) / IRIS, 3.0)
    iris = mix(rgb(250, 214, 140), rgb(190, 130, 70), smooth(0.45, 1.0, r))
    iris = iris * (1 - 0.5 * smooth(-0.1, 0.5, py / IRIS))[:, None]
    col = mix(rgb(30, 30, 44), iris, 1 - smooth(0.95, 1.0, r))
    pu = np.where(a > 0, np.sqrt((px / (IRIS * 0.62)) ** 2 + (py / (IRIS * 0.36)) ** 2), 3.0)
    col = mix(col, rgb(10, 10, 18), 1 - smooth(0.88, 1.0, pu))
    paint(o, col, np.full(len(px), 0.1))


def ear_point(side):
    root = V(side * 0.118, -0.555, 0.752)
    U = V(side * 0.86, 0.22, -0.46).normalized()
    Vv = (V(0, -0.9, -0.4) - U * V(0, -0.9, -0.4).dot(U)).normalized()
    Nn = U.cross(Vv) * side

    def point(u, v):
        width = 0.05 * math.sin(math.pi * u ** 0.7) ** 0.75 + 0.008
        w = 2 * v - 1
        return root + U * 0.2 * u + Vv * width * w + Nn * (0.016 * (1 - w * w) * math.sin(math.pi * u) - 0.03 * u * u)
    return point


def ear_colour(u, v):
    w = np.abs(2 * v - 1)
    return mix(mix(SLATE, DUSK, 0.3), BLUSH, (1 - smooth(0.2, 0.7, w)) * smooth(0.1, 0.3, u) * (1 - smooth(0.65, 0.92, u)) * 0.7)


def ear_thick(u, v):
    return 0.012 * (1 - u) + 0.005


def horn_path(side):
    """A small ram's curl: over the top, back, down, and round on itself beside the ear."""
    pts = []
    centre = V(side * 0.155, -0.545, 0.76)
    for k in range(29):
        f = k / 28
        a = -0.5 + 5.2 * f
        r = 0.092 * (1 - 0.72 * f)
        pts.append(centre + V(side * (-0.05 + 0.13 * min(1.0, f * 2.5) + 0.02 * f), r * math.sin(a), r * math.cos(a)))
    return pts


def horn_radius(f):
    return 0.006 + 0.021 * (1 - f) ** 0.8


def build_horns(name, coll, sides, step):
    m = Mesh()
    for side in (1, -1):
        m.tube(horn_path(side)[::step], horn_radius, sides=sides)
    return m.finish(name, coll)


def hoof_shape(m, key, side, knots, low):
    base = mir(knots[2], side)
    sides = 10 if low else 32
    levels = (0.0, 0.03, 0.062, 0.08) if low else (0.0, 0.003, 0.012, 0.03, 0.05, 0.065, 0.08)
    rings = []
    for z in levels:
        k = 1 - 0.3 * z / 0.08
        ring = []
        for j in range(sides):
            a = TAU * j / sides
            sn, cs = math.sin(a), math.cos(a)
            ry = 0.052 * k * (1 + 0.22 * max(0.0, -sn) ** 2)
            rx = 0.046 * k
            # the cleft at the front
            cleft = 0.012 * math.exp(-((cs / 0.16) ** 2)) * max(0.0, -sn)
            ring.append(m.bm.verts.new((base.x + rx * cs, base.y - 0.008 + (ry - cleft) * sn, GROUND + z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(sides):
            m.bm.faces.new((rings[i][j], rings[i][(j + 1) % sides], rings[i + 1][(j + 1) % sides], rings[i + 1][j]))
    m.bm.faces.new(list(reversed(rings[0])))
    m.bm.faces.new(rings[-1])


def build_hooves(name, coll, low=False):
    m = Mesh()
    which = []
    for index, (key, side, knots) in enumerate(LEGS):
        before = len(m.bm.verts)
        hoof_shape(m, key, side, knots, low)
        which += [index] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


def face_ray(tree, x, z, lift):
    return on_surface(tree, V(x, -0.75, z), V(0, 1, 0), lift)


def build_smile(tree, name, coll, per, lift=0.003):
    pts = [face_ray(tree, x, z, lift) for x, z in ((-0.058, 0.612), (-0.036, 0.6), (-0.012, 0.603), (0.0, 0.608), (0.012, 0.603), (0.036, 0.6), (0.058, 0.612))]
    m = Mesh()
    m.tube(catmull(pts, per), lambda f: 0.0018 + 0.0024 * math.sin(math.pi * f) ** 0.6, sides=8 if per > 2 else 5, plane=V(0, 1, 0))
    return m.finish(name, coll)


def build_mouth(tree, name, coll, seg, rings):
    c = face_ray(tree, 0.0, 0.592, -0.046)
    m = Mesh()
    m.ball(c, (0.04, 0.026, 0.024), seg, rings)
    return m.finish(name, coll), c


def build_hi():
    pieces, frames, marks = {}, {}, {}
    skin, body_only = build_skin()
    paint_skin(skin)
    pieces["Skin"] = skin
    pieces["Legs"] = skin      # (the game mesh's legs are their own tubes, baked from the same skin)
    marks["BodyOnly"] = body_only
    tree = tree_of(skin)
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=-6.0)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, mix(SLATE, DUSK, 0.25), rgb(14, 16, 32))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SLATE, rgb(14, 16, 32), lower_share=0.6)
        pieces["Ear" + tag] = sheet_hi(ear_point(side), ear_thick, 110, 60, N + "Ear" + tag + "Hi", ear_colour, lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    o = build_horns(N + "HornsHi", HI, 16, 1)
    P = verts(o)
    ridge = np.sin(P[:, 1] * 240 + P[:, 2] * 240) * 0.5 + 0.5
    paint(o, mix(HORN_A, HORN_B, ridge * 0.35), 0.42)
    pieces["Horns"] = o
    o, _ = build_hooves(N + "HoovesHi", HI)
    plain(o, DUSK * 0.8, 0.35)
    pieces["Hooves"] = o
    o = build_smile(tree, N + "SmileHi", HI, 5)
    plain(o, rgb(20, 18, 36), 0.5)
    pieces["Smile"] = o
    o, marks["Mouth"] = build_mouth(tree, N + "MouthHi", HI, 28, 16)
    B = verts(o)
    rim = np.sqrt(((B[:, 0] - marks["Mouth"].x) / 0.04) ** 2 + ((B[:, 2] - marks["Mouth"].z) / 0.024) ** 2)
    paint(o, mix(rgb(52, 22, 46), SLATE, smooth(0.8, 0.96, rim)), 0.5)
    pieces["Mouth"] = o
    glow = glints(frames, HI, "Glints_Glow_f0ead8", spots=((-16, 6, 0.008, 12),))
    return pieces, frames, marks, glow


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.45), (0, -0.05, 1), (0.25, -0.3, -0.9), (0.62, -0.76, 0.14, 1.5, (0.02, -0.62, 0.72)), (0, -1, 0.06, 1.3, (0, -0.65, 0.72)), (0.9, -0.3, 0.05, 1.8, (0.1, 0.1, 0.38))]
VIEW_AT = (0, 0.1, 0.68)


def show_glow(o):
    m = bpy.data.materials.new(o.name)
    g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0, 0, 0, 1)
    g.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    g.inputs["Emission Strength"].default_value = 1.2
    o.data.materials.append(m)
    o.visible_shadow = False



# ---------- the game mesh ----------
SKIN_QUADS = 2950
SCALES = {"EyeL": 5.0, "EyeR": 5.0, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5, "Smile": 3.0, "Mouth": 1.4, "EarL": 1.2, "EarR": 1.2, "Horns": 1.3}
META = {}


def build_low(pieces, frames, tree, marks_body):
    lows = {"Skin": retopo_skin(marks_body, N + "SkinLow", SKIN_QUADS)}
    m = Mesh()
    for key, side, knots in LEGS:
        m.tube(leg_path(side, knots)[::2], lambda f: leg_radius(f) + 0.002, sides=8, flat=0.9)
    lows["Legs"] = m.finish(N + "LegsLow", GAME)
    META["LegRows"] = len(leg_path(1, FRONT)[::2])
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 6, 3, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 16, 10)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Horns"] = build_horns(N + "HornsLow", GAME, 7, 2)
    lows["Hooves"], META["Hooves"] = build_hooves(N + "HoovesLow", GAME, low=True)
    lows["Smile"] = build_smile(tree_of(lows["Skin"]), N + "SmileLow", GAME, 2, lift=0.0015)     # on the game mesh itself: it re-meshes a little differently each build
    lows["Mouth"] = decimated(pieces["Mouth"], N + "MouthLow", 70)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
WOOL = {"WoolTop": V(0, 0.12, 1.08), "WoolBack": V(0, 0.55, 0.84), "WoolChest": V(0, -0.34, 0.86), "WoolL": V(0.36, 0.12, 0.8), "WoolR": V(-0.36, 0.12, 0.8)}
WOOL_REACH = 0.3


def skeleton(frames, marks):
    bones = [("Root", V(0, 0, 0), None), ("Body", CENTRE.copy(), "Root"), ("Head", V(0, -0.46, 0.72), "Body"), ("WoolCap", V(0, -0.53, 0.84), "Head"), ("Tail", V(0, 0.72, 0.79), "Body")]
    for name, at in WOOL.items():
        bones.append((name, at.copy(), "Body"))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, V(side * 0.118, -0.555, 0.752), "Head")]
    for key, side, knots in LEGS:
        bones.append(("Leg%s1" % key, mir(knots[0], side), "Body"))
        bones.append(("Leg%s2" % key, mir(knots[1], side), "Leg%s1" % key))
        bones.append(("Hoof" + key, mir(knots[2], side), "Leg%s2" % key))
    m = marks["Mouth"]
    bones += [("Smile", m.copy(), "Head"), ("Mouth", m.copy(), "Head")]
    return armature(bones)


def skin_weights(o):
    P = verts(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    wool_at = {name: np.exp(-(np.linalg.norm(P - np.array(tuple(at)), axis=1) / WOOL_REACH) ** 2) for name, at in WOOL.items()}
    head = smooth(-0.42, -0.5, y) * smooth(0.0, 0.0001, 1.0 - np.abs(x) * 0)
    cap = np.exp(-(np.linalg.norm(P - np.array((0, -0.53, 0.84)), axis=1) / 0.13) ** 2) * head
    tail = smooth(0.70, 0.76, y) * (z > 0.68)
    out = []
    for i in range(len(P)):
        w = {"Body": 1.0}
        for name, field in wool_at.items():
            v = float(field[i]) * 0.75
            if v > 0.02:
                w["Body"] -= v * w["Body"]
                w[name] = v
        h = float(head[i])
        if h > 0:
            w = {b: v * (1 - h) for b, v in w.items()}
            c = float(cap[i])
            w["Head"] = h * (1 - c)
            if c > 0.02:
                w["WoolCap"] = h * c
        t = float(tail[i])
        if t > 0:
            w = {b: v * (1 - t) for b, v in w.items()}
            w["Tail"] = t
        out.append(w)
    return out


def bind_all(lows, rig, glow):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    rows, leg_weights = META["LegRows"], []
    for key, side, knots in LEGS:
        for i in range(rows):
            f = i / (rows - 1)
            s, tip = float(smooth(0.36, 0.64, f)), float(smooth(0.9, 0.98, f))
            leg_weights += [{"Leg%s1" % key: 1 - s, "Leg%s2" % key: s * (1 - tip), "Hoof" + key: s * tip}] * 8
    weigh(lows["Legs"], leg_weights)
    keys = [key for key, *_ in LEGS]
    weigh(lows["Hooves"], [{"Hoof" + keys[int(i)]: 1.0} for i in META["Hooves"]])
    for key in ("EarL", "EarR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Smile", "Mouth"):
        rigid(lows[key], key)
    rigid(lows["Horns"], "Head")
    weigh(glow, [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glow)])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body, glow])
    return body


RX, RY = (-1, 0, 0), (0, 0, 1)


def pose_library(frames):
    def turn(axis, deg):
        return (axis, deg, (0, 0, 0))

    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out

    def leg(key, a, b, c):
        return {"Leg%s1" % key: turn(RX, a), "Leg%s2" % key: turn(RX, b), "Hoof" + key: turn(RX, c)}
    paddle = {**leg("FL", 40, -50, -30), **leg("FR", -30, -20, -10), **leg("BL", -36, 30, -20), **leg("BR", 32, 40, -30)}
    tuck = {**leg("FL", 62, -96, -40), **leg("FR", 62, -96, -40), **leg("BL", -60, 90, -30), **leg("BR", -60, 90, -30)}
    swell = {name: ((1, 0, 0), 0, tuple((at - CENTRE).normalized() * 0.075)) for name, at in WOOL.items()}
    swell["WoolCap"] = ((1, 0, 0), 0, (0, 0.012, 0.03))
    return {"Blink": lids(BLINK_U, BLINK_L), "Yawn": {"Smile": ((1, 0, 0), 0, (0, 0.03, 0)), "Mouth": ((1, 0, 0), 0, (0, -0.03, -0.006)), "Head": turn(RX, 16), **lids(BLINK_U, BLINK_L)}, "Paddle": paddle, "Tuck": tuck, "Swell": swell,
            "NodOff": {"Head": turn(RX, -26), **lids(BLINK_U, BLINK_L)}, "Look": {"Head": turn(RY, 32)}, "Tail": {"Tail": turn(RY, 28)}, "Ears": {"EarL": turn(RX, 26), "EarR": turn(RX, 26)}}


if __name__ == "__main__":
    pieces, frames, marks, glow = build_hi()
    mat = hi_material(ao_distance=0.12, ao_share=0.3)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glow(glow)
    stage_setup((0.3, 0.42, 0.58, 1))
    if STAGE == "paint":
        shots(os.path.join(REVIEW, "paint"), VIEWS, target=VIEW_AT, dist=5.2)
    else:
        lows = build_low(pieces, frames, tree_of(pieces["Skin"]), marks["BodyOnly"])
        gap = surface_gap(lows["Skin"], tree_of(marks["BodyOnly"]))
        print("SKIN GAP", round(gap, 4), flush=True)
        assert gap < 0.02, "the re-mesh strayed from the sculpt"
        unwrap(lows, [(lambda p: p.center.y < -0.5 and p.center.z < 0.84, 2.0), (None, 1.0)], SCALES, shape="CONVEX", angle=38)
        bake_all(lows, pieces, mat, size=1024, colour_size=1024, metal=True, fill=(0.8, 0.84, 0.9, 1), far=("Skin", "Legs"), far_reach=(0.016, 0.05))
        tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
        print("TRIS", sum(tris.values()), tris, flush=True)
        HI.objects.unlink(glow)
        GAME.objects.link(glow)
        rig = skeleton(frames, marks)
        body = bind_all(lows, rig, glow)
        for o in list(HI.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
        print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data), flush=True)
        for tag, fr in frames.items():
            print("EYE", tag, tuple(round(v, 4) for v in fr.centre), "hinge", tuple(round(v, 4) for v in fr.hinge), flush=True)
        pose(rig, {})
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS, target=VIEW_AT, dist=5.2)
        lib = pose_library(frames)
        for name, row in pet_kit.stress_report(rig, body, lib).items():
            print("STRESS", name, row, flush=True)
        close = (0.5, -0.86, 0.06, 1.4, (0.02, -0.64, 0.72))
        wide = (0.72, -0.62, 0.1, 5.0, VIEW_AT)
        for name, view in (("Blink", close), ("Yawn", close), ("NodOff", close), ("Look", (0.25, -0.95, 0.12, 2.2, (0, -0.55, 0.76))), ("Paddle", wide), ("Tuck", wide), ("Swell", wide), ("Tail", (0.5, 0.8, 0.2, 3.0, (0, 0.5, 0.8))), ("Ears", close)):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT)
        pose(rig, {})
        glow.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.2, 5.0, VIEW_AT))      # first: the export takes the glow piece's colour off
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, [glow]), flush=True)
    print("DONE", flush=True)

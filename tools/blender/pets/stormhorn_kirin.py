"""The Stormhorn Kirin (Legendary, Storms; Spirit Breeze Egg): "Its horn calls the rain and its hooves answer with thunder. Farmers and generals alike have prayed to it."

A new creature. A tall deer-dragon of storm-slate, scaled over neck, chest and shoulders, with a pale plated throat. Its one horn rises from a bronze sheath as a forked bolt of lightning.
Its mane and tail are torn by a wind only it feels, long streaming locks from night-blue to rain-grey, with lightning flickering in them. Veins of lightning run under its hide, and its cloven
bronze hooves throw sparks where they land. A noble animal's eye, gold in all that blue, under a heavy lid. It walks on the air, as the storm does.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/stormhorn_kirin.py -- [paint|all] [review dir]

paint: builds and paints the high-detail model and renders it. all: also makes the game mesh, bakes, rigs and writes the file and the FBX.
Faces -Y, Z up, hooves on z = 0. The maps go to assets/pets/SpiritBreezeEgg/.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "StormhornKirin"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "SpiritBreezeEgg")

# ---------- colours ----------
NIGHT, SLATE, STEEL, MIST, PEARL = rgb(22, 26, 58), rgb(48, 58, 106), rgb(86, 104, 154), rgb(164, 178, 212), rgb(228, 232, 244)
BRONZE, DEEP_BRONZE, GOLD = rgb(196, 136, 70), rgb(112, 70, 40), rgb(250, 190, 70)
MOUTH = rgb(70, 22, 44)

# ---------- the frame of it ----------
SPINE = [V(0, 0.72, 1.07), V(0, 0.32, 1.03), V(0, 0.05, 0.99), V(0, -0.22, 1.01), V(0, -0.44, 1.14), V(0, -0.60, 1.36), V(0, -0.80, 1.66), V(0, -1.30, 1.54)]
SPINE_SMOOTH = catmull(SPINE, 12)
NECK = catmull([V(0, -0.42, 1.04), V(0, -0.57, 1.26), V(0, -0.70, 1.46), V(0, -0.79, 1.62), V(0, -0.85, 1.72)], 8)
TAIL = catmull([V(0, 0.72, 1.11), V(0, 0.92, 1.20), V(0, 1.18, 1.20), V(0.03, 1.46, 1.09), V(-0.02, 1.74, 1.03), V(0, 2.02, 1.09), V(0, 2.20, 1.17)], 8)
TAIL_F = (0.03, 0.17, 0.33, 0.49, 0.65, 0.82)
FRONT = [V(0.15, -0.40, 0.96), V(0.15, -0.37, 0.72), V(0.135, -0.43, 0.46), V(0.13, -0.41, 0.16), V(0.13, -0.435, 0.08)]
HIND = [V(0.15, 0.50, 0.98), V(0.165, 0.37, 0.72), V(0.145, 0.59, 0.46), V(0.135, 0.53, 0.16), V(0.135, 0.505, 0.08)]
FRONT_R = [0.11, 0.072, 0.05, 0.042, 0.032]
HIND_R = [0.13, 0.098, 0.05, 0.042, 0.032]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.041
EYE_C = V(0.072, -0.985, 1.735)
EYE_AXIS = V(0.86, -0.48, 0.14).normalized()
LID_UP, LID_LOW = (17.0, 108.0, 0.0036), (-30.0, -125.0, 0.0028)
LID_TILT = 13.0
BLINK_U, BLINK_L = 36.0, 12.0


def leg_path(key, side, knots, radii, per=8):
    pts = catmull([mir(p, side) for p in knots], per)
    return pts


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    core.ball(V(0, -0.28, 0.93), (0.215, 0.30, 0.285))         # the deep chest
    core.ball(V(0, 0.06, 0.965), (0.195, 0.42, 0.225))         # the barrel, tucked up toward the flank
    core.ball(V(0, 0.46, 0.99), (0.205, 0.28, 0.23))           # the rump
    core.ball(V(0, 0.42, 1.09), (0.14, 0.24, 0.13))            # the croup
    core.ball(V(0, -0.36, 1.15), (0.115, 0.20, 0.115))         # the withers
    core.ball(V(0, -0.50, 0.95), (0.135, 0.13, 0.15))          # the breast
    for side in (1, -1):
        core.ball(V(side * 0.12, -0.38, 0.90), (0.10, 0.16, 0.235))    # the shoulder
        core.ball(V(side * 0.12, 0.48, 0.92), (0.105, 0.22, 0.24))     # the haunch
    core.tube(NECK, lambda f: 0.205 - 0.105 * f ** 0.8, sides=24, flat=0.74)
    # the head: heavy and dragon-deep, set on an arched neck
    core.ball(V(0, -0.90, 1.73), (0.098, 0.135, 0.098))        # the skull
    core.ball(V(0, -0.965, 1.785), (0.07, 0.11, 0.052))        # the dome of the forehead
    for side in (1, -1):
        core.ball(V(side * 0.062, -0.935, 1.655), (0.058, 0.105, 0.078))   # the strong cheek
        core.ball(V(side * 0.07, -1.0, 1.78), (0.044, 0.078, 0.024))       # the heavy brow, over the eye
        core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.008, (0.045, 0.045, 0.045))     # the socket
        core.ball(V(side * 0.056, -0.955, 1.762), (0.05, 0.09, 0.044))     # the bone behind the brow: the lid's hidden edge stays under it
        core.ball(V(side * 0.038, -1.27, 1.585), (0.026, 0.034, 0.024))    # the flared nostril
    muzzle = catmull([V(0, -0.98, 1.70), V(0, -1.12, 1.625), V(0, -1.25, 1.56)], 8)
    core.tube(muzzle, lambda f: 0.09 - 0.032 * f, sides=20, flat=0.88)
    core.ball(V(0, -1.28, 1.555), (0.056, 0.05, 0.05))         # the nose
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.011, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 22})])
    thin = Mesh()
    for key, side, knots, radii in LEGS:
        path = leg_path(key, side, knots, radii)
        thin.tube(path, lambda f, r=radii: leg_radius(r, f), sides=20, flat=0.84, plane=V(1, 0, 0))
        fetlock = mir(knots[3], side)
        thin.ball(fetlock + V(0, 0.012, 0), (0.038, 0.046, 0.042), 18, 12)     # the fetlock joint, round at the back
        thin.ball(mir(knots[2], side), (0.044, 0.05, 0.05), 18, 12)
    thin.tube(catmull([V(0, 0.60, 1.08), V(0, 0.74, 1.12), V(0, 0.90, 1.19)], 6), lambda f: 0.062 - 0.032 * f, sides=14)       # the dock of the tail
    th = thin.finish(N + "ThinHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0045, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


def spine_arc(P):
    """Per point: how far along the spine in metres, and its fraction along the path by knots."""
    f, d = nearest_on(SPINE, P)
    k = f * (len(SPINE) - 1)
    lengths = np.array([0.0] + [(SPINE[i + 1] - SPINE[i]).length for i in range(len(SPINE) - 1)])
    cum = np.cumsum(lengths)
    return np.interp(k, np.arange(len(SPINE)), cum), k, d


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    arc, k, d = spine_arc(P)
    leg = (1 - smooth(0.68, 0.82, z)) * smooth(0.04, 0.08, np.abs(x))
    head = smooth(-0.80, -0.88, y) * smooth(1.40, 1.46, z)
    # the coat: night along the spine, slate on the flanks, steel below, with the pale cloud-dapple of a storm's edge
    up = Nn[:, 2]
    col = mix(STEEL, SLATE, smooth(-0.2, 0.55, up))
    col = mix(col, NIGHT, smooth(0.72, 0.97, up) * (1 - smooth(0.05, 0.13, np.abs(x))) * 0.9)
    cloud = fbm(P, 3.6, 5, 5)
    col = mix(col, MIST, smooth(0.56, 0.74, cloud) * 0.3 * (1 - leg) * (1 - head) * smooth(-0.2, 0.05, y))
    col = mix(col, NIGHT, smooth(0.34, 0.2, cloud) * 0.5 * (1 - head))
    # the scales of its neck, chest and shoulders, fading out along the flank
    # measured along a smooth curve: on the polyline, a bend fans one knot across the withers, and the cells collapse into noise
    smooth_f, _ = nearest_on(SPINE_SMOOTH, P)
    index = smooth_f * (len(SPINE_SMOOTH) - 1)
    steps = np.array([0.0] + [(SPINE_SMOOTH[i + 1] - SPINE_SMOOTH[i]).length for i in range(len(SPINE_SMOOTH) - 1)])
    arc = np.interp(index, np.arange(len(SPINE_SMOOTH)), np.cumsum(steps))
    px = np.arctan2(x, z - np.interp(index, np.arange(len(SPINE_SMOOTH)), [p.z for p in SPINE_SMOOTH])) * 0.17
    w, h = 0.05, 0.034
    v = px / h
    row = np.floor(v)
    u = arc / w + 0.5 * (row % 2)
    fu, fv = u - np.floor(u) - 0.5, v - row - 0.5
    dome = np.clip(1 - (fu ** 2 + fv ** 2) * 3.0, 0, 1)
    # they lie on the neck's sides and over the shoulder, thinning out along the flank; none on the head or the legs
    scaled = (1 - smooth(-0.34, 0.06, y + 0.14 * (cloud - 0.5))) * (1 - leg) * (1 - head)
    plate = smooth(0.0, 0.5, dome)
    col = mix(col, mix(NIGHT, mix(SLATE, STEEL, 0.7), plate), scaled * 0.8)
    # the pale plates of its throat and breast, a clean band down the front
    narrow = 0.05 * (1 - smooth(-0.56, -0.26, y)) + 0.002      # it comes to a point on the breast
    throat = (1 - smooth(narrow, narrow + 0.02, np.abs(x))) * smooth(-0.1, -0.5, Nn[:, 1] + 0.75 * up) * smooth(0.66, 0.76, z) * (1 - smooth(-0.84, -0.92, y)) * (1 - smooth(-0.32, -0.2, y))
    band = arc / 0.045
    band_f = band - np.floor(band)
    col = mix(col, mix(MIST, PEARL, smooth(0.15, 0.85, band_f)), throat)
    # legs: darkening to night at the cannon, a pale rain-grey at the fetlock
    col = mix(col, NIGHT, smooth(0.58, 0.32, z) * leg * 0.92)
    col = mix(col, MIST, smooth(0.225, 0.14, z) * leg)
    # the head: slate above, steel on the cheek; pale only at the lip and under the jaw, a dark mask round the eye
    col = mix(col, STEEL, head * (1 - smooth(-0.15, 0.4, up)) * 0.8)
    col = mix(col, SLATE, head * smooth(0.05, 0.5, up))
    lip = smooth(-1.14, -1.24, y) * smooth(0.5, -0.1, up)
    col = mix(col, MIST, np.maximum(lip, smooth(0.12, -0.5, up) * smooth(-1.0, -1.1, y)) * head * 0.9)
    col = mix(col, mix(STEEL, MIST, 0.4), smooth(-1.2, -1.3, y) * head * 0.8)
    eye_d = np.minimum(np.linalg.norm(P - np.array(tuple(EYE_C)), axis=1), np.linalg.norm(P - np.array(tuple(mir(EYE_C, -1))), axis=1))
    col = mix(col, NIGHT, (1 - smooth(0.05, 0.09, eye_d)) * 0.92)
    # the ridge over the nose, dark, running up to the horn
    col = mix(col, NIGHT, head * (1 - smooth(0.012, 0.03, np.abs(x))) * smooth(0.3, 0.7, up) * 0.75)
    rough = 0.66 - 0.05 * plate * scaled - 0.12 * throat + 0.06 * (fbm(P, 24.0, 2, 9) - 0.5)
    # the underside of the muzzle is the roof of its mouth: the jaw covers it until it opens
    roof = (1 - smooth(0.02, 0.032, np.abs(x))) * smooth(-1.0, -1.04, y) * smooth(-0.35, -0.7, Nn[:, 2]) * (1 - smooth(-1.23, -1.25, y))
    col = mix(col, MOUTH, roof)
    # the nostrils
    nost = np.zeros_like(x)
    for side in (1, -1):
        nost = np.maximum(nost, 1 - smooth(0.008, 0.014, np.sqrt((x - side * 0.04) ** 2 + ((y + 1.29) * 0.8) ** 2 + (z - 1.585) ** 2)))
    col = mix(col, rgb(30, 22, 44), nost)
    disp = 0.002 * plate * scaled + 0.0012 * throat * smooth(0.0, 0.3, band_f) - 0.006 * nost + 0.0006 * cloud
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, rough)


# ---------- locks: mane, tail, fetlock tufts ----------
def resample(path, n):
    a = np.array([tuple(p) for p in path])
    t = np.linspace(0, len(a) - 1, n)
    out = []
    for f in t:
        i = min(int(f), len(a) - 2)
        out.append(Vector(a[i] + (a[i + 1] - a[i]) * (f - i)))
    return out


def lock_profile(width, tip=0.004):
    def r(f):
        return tip + width * math.sin(math.pi * min(1.0, f * 0.97 + 0.03) ** 0.62) ** 0.9
    return r


def locks_piece(locks, name, coll, rows, sides, flat):
    """A piece of many flat locks. locks: (path, width). Returns it and, per vertex: which lock, how far along, how far round."""
    m = Mesh()
    which, along, round_ = [], [], []
    for index, (path, width) in enumerate(locks):
        pts = resample(path, rows)
        m.tube(pts, lock_profile(width), sides=sides, flat=flat, plane=V(1, 0, 0))
        for i in range(rows):
            for j in range(sides):
                which.append(index)
                along.append(i / (rows - 1))
                round_.append(j / sides)
    o = m.finish(name, coll)
    return o, np.array(which), np.array(along), np.array(round_)


def paint_locks(o, which, along, round_, root, mid, tip, strand=1.0):
    P = verts(o)
    Nn = normals(o)
    seed = np.sin(which * 12.9) * 0.5 + 0.5
    col = mix(root, mid, smooth(0.08, 0.5, along + 0.08 * seed))
    col = mix(col, tip, smooth(0.5, 0.97, along + 0.06 * seed))
    # strands: fine grooves running the length of each lock
    lines = np.sin(round_ * TAU * 9 + seed * 9 + along * 3) * 0.5 + 0.5
    col = col * (1 - 0.24 * strand * smooth(0.6, 1.0, lines) * (1 - smooth(0.7, 1.0, along)))[:, None]
    set_verts(o, P - Nn * (0.0014 * strand * smooth(0.55, 1.0, lines))[:, None])
    paint(o, col, 0.58 + 0.1 * along)


def crest_root(tree, t):
    """A point on the crest of the neck, t from poll (0) to withers (1), just inside the skin."""
    i = int(round((1 - t) * (len(NECK) - 1) * 0.92)) + 2
    i = min(i, len(NECK) - 2)
    c = NECK[i]
    tan = (NECK[i + 1] - NECK[i - 1]).normalized()
    back = V(0, 1, 0) - tan * tan.y
    back = back.normalized()
    loc = tree.ray_cast(c + back * 0.5, -back, 1.0)[0]
    return (loc - back * 0.012) if loc else c


def flow(root, side_x, length, lift=1.0):
    """A lock streaming back on the wind from where it grows."""
    pts = [root, root + V(side_x * 0.18, 0.16 * length, 0.09 * length * lift), root + V(side_x * 0.48, 0.42 * length, 0.15 * length * lift), root + V(side_x * 0.76, 0.70 * length, 0.09 * length * lift),
           root + V(side_x, 1.0 * length, 0.15 * length * lift)]
    return catmull(pts, 6)


MANE_PLAN = (
    ("A", 0.03, 0.02, 0.50, 0.056), ("A", 0.12, -0.06, 0.60, 0.066), ("A", 0.22, 0.09, 0.52, 0.058),
    ("B", 0.33, -0.11, 0.60, 0.062), ("B", 0.44, 0.04, 0.68, 0.072), ("B", 0.54, 0.13, 0.54, 0.058), ("B", 0.60, -0.04, 0.50, 0.05),
    ("C", 0.68, -0.13, 0.52, 0.054), ("C", 0.76, 0.08, 0.54, 0.056), ("C", 0.86, -0.05, 0.44, 0.05), ("C", 0.95, 0.10, 0.36, 0.042),
)
MANE_CLUSTER = {"A": "Neck2", "B": "Neck2", "C": "Neck1"}


def mane_paths(tree):
    return [(flow(crest_root(tree, t), sx, length), w) for _, t, sx, length, w in MANE_PLAN]


TAIL_PLAN = ((0.0, 0.0, 1.0, 0.078), (0.05, 0.05, 0.93, 0.066), (-0.05, 0.04, 0.88, 0.066), (0.075, -0.02, 0.74, 0.058), (-0.075, -0.03, 0.8, 0.058), (0.03, -0.075, 0.66, 0.052), (-0.025, 0.09, 0.7, 0.05))


def tail_paths():
    out = []
    for ox, oz, reach, w in TAIL_PLAN:
        count = 5 + int(reach * 22)
        pts = []
        for k in range(count):
            f = k / (count - 1)
            p = TAIL[min(len(TAIL) - 1, int(f * reach * (len(TAIL) - 1)))]
            spread = math.sin(math.pi * min(1.0, f * 0.9)) ** 0.8
            pts.append(p + V(ox * (0.42 + 0.58 * spread), 0, oz * (0.42 + 0.58 * spread)))     # never quite together, even at the root
        out.append((pts, w))
    return out


def tuft_paths():
    out = []
    for key, side, knots, _ in LEGS:
        c = mir(knots[3], side) + V(0, 0.006, 0.0)
        for ox, oz, length in ((0.0, 0.012, 0.15), (0.018, -0.008, 0.11), (-0.018, -0.006, 0.12)):
            root = c + V(ox, 0, oz)
            pts = catmull([root, root + V(ox * 0.5, 0.45 * length, -0.05 * length), root + V(ox, 0.8 * length, 0.02 * length), root + V(ox * 1.2, length, 0.14 * length)], 4)
            out.append((pts, 0.018))
    return out


def frill_paths(side):
    """Short locks at the angle of the jaw, blown back."""
    out = []
    for dz, length, w in ((0.0, 0.3, 0.024), (-0.05, 0.25, 0.02)):
        root = V(side * 0.082, -0.88, 1.655 + dz)
        pts = catmull([root, root + V(side * 0.022, 0.24 * length, 0.012), root + V(side * 0.04, 0.56 * length, -0.004), root + V(side * 0.06, length, 0.03)], 5)
        out.append((pts, w))
    return out


# ---------- small pieces ----------
def hoof_toes(m, key, side, knots, low=False):
    """Two toes, a cloven hoof: each a wedge coming to a point in front, flat on the ground."""
    base = mir(knots[4], side)
    sides = 10 if low else 40
    levels = (0.0, 0.03, 0.07, 0.094) if low else (0.0, 0.003, 0.012, 0.03, 0.05, 0.07, 0.085, 0.094)
    for s in (1, -1):
        rings = []
        for z in levels:
            k = 1.0 - 0.34 * z / 0.094
            cy = base.y - 0.022 + 0.02 * z / 0.094
            ring = []
            for j in range(sides):
                a = TAU * j / sides
                sn, cs = math.sin(a), math.cos(a)
                # a teardrop, its point forward (-Y), its inner side flat against the other toe
                ry = 0.058 * k * (1 + 0.28 * max(0.0, -sn) ** 2)
                rx = 0.023 * k * (1 - 0.34 * max(0.0, -sn) ** 3)
                ring.append(m.bm.verts.new((base.x + s * 0.0245 * (0.75 + 0.25 * k) + rx * cs, cy + ry * sn, z)))
            rings.append(ring)
        for i in range(len(rings) - 1):
            for j in range(sides):
                m.bm.faces.new((rings[i][j], rings[i][(j + 1) % sides], rings[i + 1][(j + 1) % sides], rings[i + 1][j]))
        m.bm.faces.new(list(reversed(rings[0])))
        m.bm.faces.new(rings[-1])


def build_hooves(coll, name, low=False):
    m = Mesh()
    which = []
    for index, (key, side, knots, _) in enumerate(LEGS):
        before = len(m.bm.verts)
        hoof_toes(m, key, side, knots, low)
        which += [index] * (len(m.bm.verts) - before)
    o = m.finish(name, coll)
    return o, np.array(which)


def ear_point(side):
    root = V(side * 0.066, -0.83, 1.775)
    U = V(side * 0.46, 0.84, 0.28).normalized()
    Vv = (V(0, -0.35, 0.94) - U * V(0, -0.35, 0.94).dot(U)).normalized()
    Nn = U.cross(Vv) * side

    def point(u, v):
        width = 0.042 * math.sin(math.pi * u ** 0.62) ** 0.85 + 0.005
        w = (2 * v - 1)
        cup = 0.012 * (1 - w * w) * math.sin(math.pi * u)
        return root + U * 0.25 * u + Vv * width * w + Nn * cup * side
    return point


def ear_colour(u, v):
    w = np.abs(2 * v - 1)
    col = mix(SLATE, NIGHT, smooth(0.5, 1.0, u))
    return mix(col, mix(STEEL, MIST, 0.4), (1 - smooth(0.25, 0.7, w)) * smooth(0.1, 0.3, u) * (1 - smooth(0.6, 0.9, u)) * 0.55)


def build_horn(coll):
    """The sheath, bronze; the horn itself a forked bolt, a glow piece."""
    base = V(0, -0.965, 1.79)
    main = [base, V(0, -0.985, 1.90), V(0.024, -0.925, 2.01), V(-0.018, -0.995, 2.15), V(0.014, -0.945, 2.27), V(0, -1.005, 2.44)]
    fork1 = [main[2], V(0.05, -0.89, 2.11), V(0.038, -0.915, 2.15), V(0.085, -0.87, 2.25)]
    fork2 = [main[3], V(-0.05, -0.95, 2.25), V(-0.042, -0.97, 2.29), V(-0.09, -0.94, 2.37)]
    m = Mesh()
    m.tube(main, lambda f: 0.031 * (1 - f) ** 0.9 + 0.003, sides=5, flat=0.8, plane=V(1, 0, 0))
    m.tube(fork1, lambda f: 0.013 * (1 - f) + 0.0025, sides=4, flat=0.8, plane=V(1, 0, 0))
    m.tube(fork2, lambda f: 0.012 * (1 - f) + 0.0025, sides=4, flat=0.8, plane=V(1, 0, 0))
    glow = m.finish(N + "Horn_Glow_4fb4ff", coll, smooth_shade=False)
    sheath = catmull([base + V(0, 0.012, -0.018), base + V(0, 0.0, 0.02), base + V(0, -0.012, 0.06), base + V(0, -0.02, 0.105)], 6)
    return glow, sheath


def build_sheath(path, name, coll, sides):
    m = Mesh()
    m.tube(path, lambda f: 0.052 - 0.021 * f ** 0.8 + (0.0035 if 0.3 < f < 0.4 else 0.0), sides=sides, flat=0.9)
    return m.finish(name, coll)


def build_jaw(name, coll, sides, per):
    path = catmull([V(0, -0.96, 1.645), V(0, -1.10, 1.585), V(0, -1.215, 1.53), V(0, -1.255, 1.515)], per)
    m = Mesh()
    m.tube(path, lambda f: 0.038 - 0.014 * f, sides=sides, flat=1.3)
    return m.finish(name, coll)


def fin_list(tree):
    out = []
    for y in np.linspace(-0.24, 0.66, 9):
        hit = tree.ray_cast(V(0, y, 2.2), V(0, 0, -1), 2.0)[0]
        if hit:
            s = 0.018 + 0.016 * math.sin(math.pi * (y + 0.24) / 0.9)
            out.append((hit, s))
    return out


def build_fins(tree, name, coll):
    m = Mesh()
    for c, s in fin_list(tree):
        a, b = c + V(0, -s * 0.9, -0.016), c + V(0, s * 0.9, -0.016)
        tip = c + V(0, s * 1.05, s * 1.05)
        vs = [m.bm.verts.new(p) for p in (a + V(0.009, 0, 0), a - V(0.009, 0, 0), b + V(0.009, 0, 0), b - V(0.009, 0, 0), tip)]
        for f in ((0, 2, 4), (3, 1, 4), (1, 0, 4), (2, 3, 4), (1, 3, 2, 0)):
            m.bm.faces.new([vs[i] for i in f])
    return m.finish(name, coll, smooth_shade=False)


# ---------- glow: lightning ----------
def jagged(a, b, n, amount, rng):
    pts = []
    d = b - a
    side = d.cross(V(1, 0, 0))
    side = side.normalized() if side.length > 1e-6 else V(0, 0, 1)
    for i in range(n + 1):
        f = i / n
        off = 0.0 if i in (0, n) else rng.uniform(-amount, amount)
        pts.append(a + d * f + side * off)
    return pts


def on_flank(tree, side, y, z, lift):
    loc, nrm, _, _ = tree.ray_cast(V(side * 1.5, y, z), V(-side, 0, 0), 2.0)
    return (loc + nrm * lift) if loc else None


VEINS = (  # (y, z) from, to; pieces: its segments and how wide
    ((-0.78, 1.56), (-0.50, 1.10), 8, 0.0065),      # down the neck
    ((-0.44, 1.06), (0.60, 0.95), 14, 0.0075),      # the length of the flank
    ((-0.26, 1.02), (-0.30, 0.76), 5, 0.0045),      # a fork over the shoulder
    ((0.04, 0.99), (0.12, 0.84), 4, 0.004),
    ((0.40, 0.97), (0.46, 0.74), 5, 0.0045),        # and over the haunch
    ((-0.64, 1.33), (-0.53, 1.41), 3, 0.0035),      # and a branch off the neck, up toward the crest
)


def build_veins(tree, side, name, coll):
    rng = np.random.default_rng(23 if side > 0 else 41)
    m = Mesh()
    for index, ((y0, z0), (y1, z1), n, width) in enumerate(VEINS):
        lift = 0.0026 if index in (1, 5) else 0.0012      # where they cross, one stands a little prouder, so they do not fight
        knots = []
        for i in range(n + 1):
            f = i / n
            jy, jz = (0.0, 0.0) if i in (0, n) else (rng.uniform(-0.016, 0.016), rng.uniform(-0.028, 0.028))
            knots.append((y0 + (y1 - y0) * f + jy, z0 + (z1 - z0) * f + jz))
        pts = []
        for i in range(n):      # each straight run laid on the surface along its length, or it would sink under a curved flank
            for s in range(2):
                p = on_flank(tree, side, knots[i][0] + (knots[i + 1][0] - knots[i][0]) * s / 2, knots[i][1] + (knots[i + 1][1] - knots[i][1]) * s / 2, lift)
                if p:
                    pts.append(p)
        p = on_flank(tree, side, knots[n][0], knots[n][1], lift)
        if p:
            pts.append(p)
        m.tube(pts, lambda f, w=width: w * (1 - 0.7 * f) + 0.001, sides=3, flat=0.9, plane=V(1, 0, 0))
    return m.finish(name, coll, smooth_shade=False)


BOLT_LOCKS = (1, 4, 8)


def build_bolts(paths, name, coll):
    """Lightning threaded along three locks of the mane, one on each face: it flickers in the game."""
    rng = np.random.default_rng(7)
    m = Mesh()
    which, along = [], []
    for index in BOLT_LOCKS:
        path, width = paths[index]
        profile = lock_profile(width)
        for sign in (1, -1):
            pts = []
            fs = np.linspace(0.14, 0.92, 9)
            for i, f in enumerate(fs):
                p = resample(path, 41)[int(f * 40)]
                pts.append(p + V(sign * profile(float(f)) * 0.36 + sign * 0.0012, 0, rng.uniform(-0.55, 0.55) * profile(float(f))))
            before = len(m.bm.verts)
            m.tube(pts, lambda f: 0.0048 * (1 - 0.6 * f) + 0.001, sides=3, flat=0.6, plane=V(1, 0, 0))
            count = len(m.bm.verts) - before
            for i in range(count):
                which.append(index)
                along.append(float(fs[min(len(fs) - 1, i // 3)]))
    o = m.finish(name, coll, smooth_shade=False)
    return o, np.array(which), np.array(along)


def build_tail_bolt(paths, name, coll):
    tip = resample(paths[0][0], 41)[37]
    ahead = (resample(paths[0][0], 41)[40] - tip).normalized()
    main = [tip, tip + ahead * 0.09 + V(0.018, 0, 0.018), tip + ahead * 0.14 + V(-0.014, 0, 0.03), tip + ahead * 0.25 + V(0.012, 0, 0.075)]
    fork = [main[1], main[1] + ahead * 0.05 + V(-0.03, 0, -0.03), main[1] + ahead * 0.075 + V(-0.024, 0, -0.022), main[1] + ahead * 0.14 + V(-0.05, 0, -0.06)]
    m = Mesh()
    m.tube(main, lambda f: 0.014 * (1 - f) + 0.002, sides=4, flat=0.7, plane=V(1, 0, 0))
    m.tube(fork, lambda f: 0.0085 * (1 - f) + 0.0018, sides=3, flat=0.7, plane=V(1, 0, 0))
    return m.finish(name, coll, smooth_shade=False)


# ---------- eyes ----------
def eye_paint(o, fr):
    """A noble animal's eye: a wide dark pupil, its iris molten gold going to amber at the rim."""
    px, py, a = eye_coords(o, fr)
    IRIS = 0.84
    r = np.where(a > 0, np.sqrt(px ** 2 + py ** 2) / IRIS, 3.0)
    azi = np.arctan2(py, px)
    col = np.broadcast_to(rgb(214, 200, 176), (len(px), 3)).copy()
    iris = mix(rgb(255, 214, 96), rgb(196, 96, 22), smooth(0.45, 0.98, r))
    iris = mix(iris, rgb(255, 240, 170), (np.sin(azi * 30) * 0.5 + 0.5) * smooth(0.5, 0.9, r) * (1 - smooth(0.0, 0.5, py / IRIS)) * 0.4)
    iris = iris * (1 - 0.55 * smooth(-0.1, 0.7, py / IRIS))[:, None]
    col = mix(col, iris, 1 - smooth(0.96, 1.0, r))
    col = mix(col, rgb(16, 10, 16), smooth(0.86, 0.97, r) * (1 - smooth(0.985, 1.03, r)))
    pu = np.where(a > 0, np.sqrt((px / (IRIS * 0.5)) ** 2 + (py / (IRIS * 0.42)) ** 2), 3.0)
    col = mix(col, rgb(6, 6, 16), 1 - smooth(0.9, 1.0, pu))
    paint(o, col, np.full(len(px), 0.08))


# ---------- the whole, high-detail ----------
def build_hi():
    pieces, data = {}, {}
    skin = build_skin()
    paint_skin(skin)
    pieces["Skin"] = skin
    tree = tree_of(skin)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, mix(NIGHT, SLATE, 0.35), rgb(8, 8, 22))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, mix(NIGHT, SLATE, 0.3), rgb(10, 10, 26), lower_share=0.7)
        pieces["Ear" + tag] = sheet_hi(ear_point(side), lambda u, v: 0.009 * (1 - u) + 0.003, 110, 60, N + "Ear" + tag + "Hi", ear_colour, lambda u, v: np.full_like(u, 0.5), lambda u, v: np.zeros_like(u))
    mane = mane_paths(tree)
    data["mane"] = mane
    o, w, a, r = locks_piece(mane, N + "ManeHi", HI, 60, 26, 0.34)
    paint_locks(o, w, a, r, NIGHT, mix(SLATE, STEEL, 0.5), MIST)
    pieces["Mane"] = o
    tail = tail_paths()
    data["tail"] = tail
    o, w, a, r = locks_piece(tail, N + "TailHi", HI, 90, 26, 0.42)
    paint_locks(o, w, a, r, NIGHT, mix(SLATE, STEEL, 0.5), MIST)
    pieces["Tail"] = o
    o, w, a, r = locks_piece(tuft_paths(), N + "TuftsHi", HI, 16, 12, 0.5)
    paint_locks(o, w, a, r, NIGHT, STEEL, MIST, strand=0.6)
    pieces["Tufts"] = o
    o, w, a, r = locks_piece(frill_paths(1) + frill_paths(-1), N + "FrillsHi", HI, 22, 14, 0.4)
    paint_locks(o, w, a, r, NIGHT, STEEL, MIST, strand=0.7)
    pieces["Frills"] = o
    o, _ = build_hooves(HI, N + "HoovesHi")
    P = verts(o)
    plain_col = mix(BRONZE, DEEP_BRONZE, smooth(0.04, 0.0, P[:, 2]))
    paint(o, plain_col, 0.32, np.ones(len(P)))
    pieces["Hooves"] = o
    glow_horn, sheath_path = build_horn(HI)
    data["sheath"] = sheath_path
    o = build_sheath(sheath_path, N + "SheathHi", HI, 32)
    P = verts(o)
    paint(o, mix(DEEP_BRONZE, BRONZE, smooth(1.78, 1.86, P[:, 2])), 0.3, np.ones(len(P)))
    pieces["Sheath"] = o
    o = build_jaw(N + "JawHi", HI, 28, 16)
    P = verts(o)
    Nn = normals(o)
    jaw_col = mix(SLATE, STEEL, smooth(-1.0, -1.2, P[:, 1]))
    jaw_col = mix(jaw_col, MOUTH, smooth(0.3, 0.7, Nn[:, 2]) * (1 - smooth(-1.2, -1.24, P[:, 1])))
    paint(o, jaw_col, 0.5)
    pieces["Jaw"] = o
    o = build_fins(tree, N + "FinsHi", HI)
    P = verts(o)
    plain(o, SLATE, 0.4)
    pieces["Fins"] = o
    glows = {"Horn": glow_horn}
    glows["VeinsL"] = build_veins(tree, 1, N + "VeinsL_Glow_2a9dff", HI)
    glows["VeinsR"] = build_veins(tree, -1, N + "VeinsR_Glow_2a9dff", HI)
    glows["Bolts"], data["bolt_which"], data["bolt_along"] = build_bolts(mane, N + "Bolts_Glow_a8e0ff", HI)
    glows["TailBolt"] = build_tail_bolt(tail, N + "TailBolt_Glow_4fb4ff", HI)
    glows["Glints"] = glints(frames, HI, "Glints_Glow_f0ead8", spots=((-18, 14, 0.0085, 12),))
    return pieces, frames, glows, data, tree


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.45), (0, -0.05, 1), (0.25, -0.3, -0.9), (0.72, -0.62, 0.1, 2.3, (0.02, -1.02, 1.72)), (0, -1, 0.05, 2.0, (0, -1.0, 1.72)), (0.9, -0.3, 0.12, 2.0, (0.1, 0.5, 0.12))]
VIEW_AT = (0, 0.44, 1.1)


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 1.2
        o.data.materials.append(m)
        o.visible_shadow = False



# ---------- the game mesh ----------
SKIN_QUADS = 2400
META = {}
LOW_LOCKS = {"Mane": (9, 6, 0.34), "Tail": (15, 6, 0.42), "Tufts": (4, 4, 0.5), "Frills": (5, 4, 0.4)}
SCALES = {"EyeL": 4.5, "EyeR": 4.5, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5, "Jaw": 1.5, "Sheath": 1.5, "Hooves": 1.2, "EarL": 1.2, "EarR": 1.2}


def low_tube(path, rfn, rows, sides, name, **kw):
    m = Mesh()
    m.tube(resample(path, rows), rfn, sides=sides, **kw)
    return m.finish(name, GAME)


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    sources = {"Mane": data["mane"], "Tail": data["tail"], "Tufts": tuft_paths(), "Frills": frill_paths(1) + frill_paths(-1)}
    for key, (rows, sides, flat) in LOW_LOCKS.items():
        o, w, a, r = locks_piece(sources[key], N + key + "Low", GAME, rows, sides, flat)
        lows[key] = o
        META[key] = (w, a)
    lows["Hooves"], META["Hooves"] = build_hooves(GAME, N + "HoovesLow", low=True)
    lows["Sheath"] = low_tube(data["sheath"], lambda f: 0.052 - 0.021 * f ** 0.8 + (0.0035 if 0.3 < f < 0.4 else 0.0), 6, 10, N + "SheathLow", flat=0.9)
    lows["Jaw"] = build_jaw(N + "JawLow", GAME, 10, 3)
    lows["Fins"] = decimated(pieces["Fins"], N + "FinsLow", 100)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), lambda u, v: 0.009 * (1 - u) + 0.003, 6, 3, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 16, 10)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)] + ["TailTip"]
TAIL_KNOTS = TAIL_F + (0.95,)
LEG_JOINTS = ("%s1", "%s2", "%s3")


def cluster_at(paths, plan, cluster, f):
    pts = [resample(path, 41)[int(f * 40)] for (path, _), row in zip(paths, plan) if row[0] == cluster]
    return sum(pts, V(0, 0, 0)) / len(pts)


def skeleton(frames, data):
    bones = [("Root", V(0, 0, 0), None)]
    for i, name, parent in ((2, "Body", "Root"), (1, "Hips", "Body"), (3, "Chest", "Body"), (4, "Neck1", "Chest"), (5, "Neck2", "Neck1"), (6, "Head", "Neck2")):
        bones.append((name, SPINE[i].copy(), parent))
    bones += [("Jaw", V(0, -0.93, 1.655), "Head"), ("HornTip", V(0, -1.005, 2.44), "Head")]
    for cluster in ("A", "B", "C"):
        parent = MANE_CLUSTER[cluster]
        bones.append(("Mane%s1" % cluster, cluster_at(data["mane"], MANE_PLAN, cluster, 0.2), parent))
        bones.append(("Mane%s2" % cluster, cluster_at(data["mane"], MANE_PLAN, cluster, 0.55), "Mane%s1" % cluster))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_KNOTS):
        bones.append((name, TAIL[int(f * (len(TAIL) - 1))].copy(), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, V(side * 0.066, -0.83, 1.775), "Head"),
                  ("Frill" + tag, V(side * 0.10, -0.90, 1.66), "Head")]
    for key, side, knots, _ in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        for k in range(3):
            bones.append(("Leg%s%d" % (key, k + 1), mir(knots[k], side), parent))
            parent = "Leg%s%d" % (key, k + 1)
        bones.append(("Hoof" + key, mir(knots[3], side), parent))
    return armature(bones)


SEG_BONE = ["Hips", "Body", "Body", "Chest", "Neck1", "Neck2", "Head"]
SEG_BLEND = {1: 0.35, 3: 0.35, 4: 0.3, 5: 0.3, 6: 0.2}


def spine_weight(k):
    """k: position along the spine's knots. A joint's bone carries what lies beyond it; they blend across each joint."""
    i = min(int(k), len(SEG_BONE) - 1)
    near = round(k)
    if near in SEG_BLEND and abs(k - near) < SEG_BLEND[near]:
        s = float(smooth(near - SEG_BLEND[near], near + SEG_BLEND[near], k))
        return {SEG_BONE[near - 1]: 1 - s, SEG_BONE[near]: s}
    return {SEG_BONE[i]: 1.0}


LEG_F = (0.25, 0.5, 0.75)


def leg_weight(key, f):
    names = ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Hoof" + key]
    w = 0.07
    for j, knot in enumerate(LEG_F):
        if abs(f - knot) < w:
            s = float(smooth(knot - w, knot + w, f))
            return {names[j]: 1 - s, names[j + 1]: s}
    return {names[sum(1 for knot in LEG_F if f > knot)]: 1.0}


def body_weights(P):
    """The skin's weights at any points: spine, tail and legs."""
    _, k, _ = spine_arc(P)
    leg_data = {}
    for key, side, knots, radii in LEGS:
        f, d = nearest_on(leg_path(key, side, knots, radii), P)
        leg_data[key] = (side, knots, radii, f, d)
    tail_f, _ = nearest_on(TAIL, P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        w = dict(spine_weight(float(k[i])))
        share = float(smooth(0.66, 0.80, y)) * (1 - float(smooth(0.08, 0.14, abs(x))))
        if share > 0:
            w = {b: v * (1 - share) for b, v in w.items()}
            for b, v in chain_weight(TAIL_NAMES, TAIL_KNOTS, float(tail_f[i])).items():
                w[b] = w.get(b, 0) + v * share
        for key, (side, knots, radii, f, d) in leg_data.items():
            if x * side <= 0:
                continue
            reach = leg_radius(radii, float(f[i])) + 0.045
            m = float(smooth(knots[0].z, knots[0].z - 0.22, z)) * float(smooth(0.055, 0.105, abs(x))) * (1 - float(smooth(reach * 0.92, reach * 1.35, d[i])))
            if m > 0:
                w = {b: v * (1 - m) for b, v in w.items()}
                for b, v in leg_weight(key, float(f[i])).items():
                    w[b] = w.get(b, 0) + v * m
        out.append(w)
    return out


def lock_cluster_weight(index, f):
    cluster = MANE_PLAN[index][0]
    s1, s2 = float(smooth(0.03, 0.2, f)), float(smooth(0.38, 0.62, f))
    return {MANE_CLUSTER[cluster]: 1 - s1, "Mane%s1" % cluster: s1 * (1 - s2), "Mane%s2" % cluster: s1 * s2}


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    w, a = META["Mane"]
    weigh(lows["Mane"], [lock_cluster_weight(int(i), float(f)) for i, f in zip(w, a)])
    weigh(glows["Bolts"], [lock_cluster_weight(int(i), float(f)) for i, f in zip(data["bolt_which"], data["bolt_along"])])
    tf, _ = nearest_on(TAIL, verts(lows["Tail"]))
    w, a = META["Tail"]
    weigh(lows["Tail"], [chain_weight(["Hips"] + TAIL_NAMES, (0.0,) + TAIL_KNOTS, float(f)) for f in tf])
    # each fetlock tuft on its own leg's cannon; each hoof on its own bone
    keys = [key for key, *_ in LEGS]
    w, a = META["Tufts"]
    weigh(lows["Tufts"], [{"Leg%s3" % keys[int(i) // 3]: 1.0} for i in w])
    weigh(lows["Hooves"], [{"Hoof" + keys[int(i)]: 1.0} for i in META["Hooves"]])
    w, a = META["Frills"]
    weigh(lows["Frills"], [{"Head": float(1 - smooth(0.1, 0.5, f)), ("FrillL" if int(i) < 2 else "FrillR"): float(smooth(0.1, 0.5, f))} for i, f in zip(w, a)])
    weigh(lows["Fins"], body_weights(verts(lows["Fins"])))
    for key in ("EarL", "EarR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Jaw"):
        rigid(lows[key], key)
    rigid(lows["Sheath"], "Head")
    weigh(glows["VeinsL"], body_weights(verts(glows["VeinsL"])))
    weigh(glows["VeinsR"], body_weights(verts(glows["VeinsR"])))
    weigh(glows["Horn"], [{"HornTip" if p[2] > 2.3 else "Head": 1.0} for p in verts(glows["Horn"])])
    rigid(glows["TailBolt"], "TailTip")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes (+X turn: a limb's far end swings forward; +Y: turns to its left; +Z rolls): the same numbers its animation uses
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def pose_library(frames):
    def turn(axis, deg):
        return (axis, deg, (0, 0, 0))

    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out

    def fore(key, a, b, c, d):
        return {"Leg%s1" % key: turn(RX, a), "Leg%s2" % key: turn(RX, b), "Leg%s3" % key: turn(RX, c), "Hoof" + key: turn(RX, d)}
    stride = {**fore("FL", 34, 4, -6, -6), **fore("FR", -24, 2, -30, -30), **fore("BL", -30, 10, -10, -30), **fore("BR", 26, 30, -36, -8)}
    gather = {**fore("FL", 48, 12, -92, -40), **fore("FR", 40, 10, -84, -36), **fore("BL", 34, 44, -66, -28), **fore("BR", 28, 40, -60, -24)}
    rear = {"Body": turn(RX, 48), **fore("BL", -44, 6, -6, 8), **fore("BR", -40, 8, -10, 8), **fore("FL", 40, 10, -86, -34), **fore("FR", 18, 8, -60, -26), "Neck1": turn(RX, -14), "Neck2": turn(RX, -10), "Head": turn(RX, -6)}
    tail = {n: turn(RY, 12 * (-1) ** k) for k, n in enumerate(TAIL_NAMES)}
    tail.update({"Hips": turn(RY, 6)})
    mane = {}
    for c in "ABC":
        mane["Mane%s1" % c] = turn(RX, -18)
        mane["Mane%s2" % c] = turn(RX, -22)
    return {"Blink": lids(BLINK_U, BLINK_L), "Stern": lids(10, 5), "Jaw": {"Jaw": turn(RX, -16)}, "Stride": stride, "Gather": gather, "Rear": rear, "NeckDown": {"Neck1": turn(RX, -26), "Neck2": turn(RX, -20), "Head": turn(RX, 28)},
            "NeckUp": {"Neck1": turn(RX, 18), "Neck2": turn(RX, 16), "Head": turn(RX, -12)}, "HeadTurn": {"Neck1": turn(RY, 20), "Neck2": turn(RY, 24), "Head": turn(RY, 26), "Chest": turn(RZ, 6)}, "Tail": tail, "Mane": mane}


if __name__ == "__main__":
    pieces, frames, glows, data, tree = build_hi()
    mat = hi_material(ao_distance=0.08, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.3, 0.33, 0.38, 1))
    if STAGE == "paint":
        shots(os.path.join(REVIEW, "paint"), VIEWS, target=VIEW_AT, dist=9.0)
    else:
        lows = build_low(pieces, frames, data)
        unwrap(lows, [(lambda p: p.center.y < -0.8 and p.center.z > 1.4, 2.0), (None, 1.0)], SCALES)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.05, 0.06, 0.14, 1))
        tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
        print("TRIS", sum(tris.values()), tris, flush=True)
        for o in glows.values():
            HI.objects.unlink(o)
            GAME.objects.link(o)
        # the veins lie on the game mesh itself, so they fit it exactly
        low_tree = tree_of(lows["Skin"])
        for side, key in ((1, "VeinsL"), (-1, "VeinsR")):
            old = glows[key]
            name, material = old.name, old.data.materials[0]
            bpy.data.objects.remove(old, do_unlink=True)
            glows[key] = build_veins(low_tree, side, name, GAME)
            glows[key].data.materials.append(material)
            glows[key].visible_shadow = False
        triangulate(glows)
        rig = skeleton(frames, data)
        body = bind_all(lows, rig, glows, data)
        for o in list(HI.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
        for o in glows.values():
            print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", tuple(round(v, 2) for v in o.dimensions), flush=True)
        print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
        for tag, fr in frames.items():
            print("EYE", tag, tuple(round(v, 4) for v in fr.centre), "hinge", tuple(round(v, 4) for v in fr.hinge), flush=True)
        pose(rig, {})
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS, target=VIEW_AT, dist=9.0)
        lib = pose_library(frames)
        for name, row in pet_kit.stress_report(rig, body, lib).items():
            print("STRESS", name, row, flush=True)
        close = (0.5, -0.86, 0.06, 2.2, (0, -1.02, 1.74))
        wide = (0.72, -0.62, 0.1, 7.6, (0, 0.2, 1.05))
        for name, view in (("Blink", close), ("Stern", close), ("Jaw", close), ("Stride", wide), ("Gather", wide), ("Rear", wide), ("NeckDown", wide), ("NeckUp", wide), ("HeadTurn", (0.3, -0.94, 0.25, 4.2, (0, -0.6, 1.5))), ("Tail", (0, 0.1, 1, 7.6, (0, 0.8, 1.0))), ("Mane", (1, 0, 0.1, 4.2, (0, -0.2, 1.5)))):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT)
        # the joints that work hardest, close up
        for name, spec, view in (("xGatherHip", "Gather", (0.8, 0.5, -0.25, 2.2, (0.1, 0.45, 0.72))), ("xRearChest", "Rear", (0.9, -0.3, -0.1, 2.6, (0.1, -0.4, 1.0))), ("xStrideHip", "Stride", (0.85, 0.3, -0.2, 2.6, (0.1, 0.4, 0.75))), ("xBelly", "Gather", (0.15, -0.1, -1, 2.6, (0, -0.1, 0.7)))):
            pose(rig, lib[spec])
            shots(os.path.join(REVIEW, name), [view], target=VIEW_AT)
        pose(rig, {})
        for o in glows.values():
            o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.2, 8.0, VIEW_AT))      # first: the export takes the glow pieces' colours off
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

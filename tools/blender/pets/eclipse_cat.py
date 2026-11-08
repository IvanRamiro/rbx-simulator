"""The Eclipse Cat (Epic, Darkness and eclipses; Astral Sanctum Egg, also in the Heavenly Throne, Forbidden Origin and Void Rift Eggs): "It appears only when something
bright is being covered up. Its purr is the sound of the world going dark for a moment."

After the owner's concept sheet (2026-11-08), its aura and background left out. A stylized black cat with a big head on a compact, fluffy body: very large pointed ears,
purple inside with white-lavender tufts and gold-rimmed edges; fluffy cheek tufts; a glowing gold crescent on its forehead; big almond eyes, violet round a gold centre and
a slit pupil, under real lids. A fluffy chest ruff, and over it a dark collar with gold rims and studs, at its front a gold crescent framing a dark disc, the eclipse, with a
violet gem hanging below. Black fur with a violet sheen, a gold spiral on each haunch and shoulder, white-lavender socks and big round paws. Its tail is a huge crescent
sweeping up and curling over: deep violet to bright, faint stars, a gold rim and a glowing gold streak along its outer edge.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/eclipse_cat.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, paws on z = 0. +X is its left. The maps go to assets/pets/AstralSanctumEgg/.

What touches what: body, legs, neck, head and the tail's root are one fused skin; the tail rises out of the rump; fur tufts grow from inside the skin; the eyes sit in their
sockets under their lids, the iris lights, pupils and glints lie on the eyes in that order, all under the lids' reach; the collar lies on the ruff's roots, the pendant hangs
from it; the crest and the tail's streak lie on their surfaces.
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
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "EclipseCat"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AstralSanctumEgg")

# ---------- colours: black fur, violet light, gold ----------
FUR, SHEEN, VIOLET_TIP = rgb(16, 13, 26), rgb(58, 40, 112), rgb(124, 78, 226)
SOCK, SOCK_SHADE = rgb(232, 222, 250), rgb(176, 150, 230)
EAR_IN, TUFT_PALE = rgb(92, 44, 170), rgb(236, 226, 255)
GOLD = rgb(255, 196, 92)
NAVY, NOSE, NOSE_LIT, MOUTH = rgb(22, 20, 48), rgb(122, 72, 132), rgb(196, 140, 196), rgb(8, 6, 14)
NOSE_TOP, NOSE_BASE_Y = 0.619, -0.371        # the nose's top edge (z) and how far back its body sits (y): half of it set into the muzzle
TAIL_DEEP, TAIL_MID, TAIL_BRIGHT, STAR = rgb(34, 14, 92), rgb(96, 46, 214), rgb(186, 140, 255), rgb(246, 240, 255)
GLINT_HEX, CREST_HEX, GEM_HEX, STREAK_HEX = "ffffff", "ffd27a", "b07cff", "ffd27b"

# ---------- the frame of it ----------
SPINE = [V(0, 0.22, 0.34), V(0, 0.1, 0.36), V(0, -0.02, 0.37), V(0, -0.12, 0.39), V(0, -0.19, 0.46), V(0, -0.24, 0.56), V(0, -0.29, 0.64), V(0, -0.39, 0.6)]
HEAD = V(0, -0.27, 0.64)
TAIL = catmull([V(0, 0.2, 0.36), V(-0.01, 0.31, 0.43), V(-0.03, 0.42, 0.58), V(-0.06, 0.45, 0.76), V(-0.08, 0.4, 0.92), V(-0.08, 0.3, 1.0), V(-0.065, 0.17, 1.0), V(-0.05, 0.08, 0.95)], 10)
FRONT = [V(0.068, -0.13, 0.3), V(0.066, -0.11, 0.19), V(0.064, -0.14, 0.085), V(0.064, -0.15, 0.035), V(0.064, -0.16, 0.025)]
HIND = [V(0.078, 0.16, 0.28), V(0.086, 0.1, 0.17), V(0.08, 0.19, 0.085), V(0.078, 0.18, 0.035), V(0.078, 0.17, 0.025)]
FRONT_R = [0.046, 0.037, 0.029, 0.028, 0.027]
HIND_R = [0.06, 0.044, 0.03, 0.028, 0.027]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.042
EYE_C = V(0.062, -0.342, 0.654)       # set back into the face: the lids frame an almond, not a ball
EYE_AXIS = V(0.36, -0.93, 0.06).normalized()
LID_UP, LID_LOW = (30.0, 118.0, 0.0032), (-28.0, -128.0, 0.0026)      # an almond opening
LID_TILT = 18.0          # the outer corners raised, as the sheet draws them
BLINK_U, BLINK_L = 42.0, 18.0          # together more than the opening's 58 degrees: shut
IRIS, CORE, PUPIL_W, PUPIL_H = 0.9, 0.4, 0.1, 0.64       # on the eye's face (its front is 1): the violet iris, its gold centre, the slit
COLLAR_C, COLLAR_AXIS, COLLAR_R = V(0, -0.222, 0.518), V(0, -0.5, 0.866).normalized(), (0.104, 0.096)      # over the roots of the face's frame and the bib


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def tail_width(f):
    return float(np.interp(f, (0, 0.12, 0.35, 0.6, 0.82, 1), (0.042, 0.065, 0.14, 0.145, 0.095, 0.004)))


def tail_thick(f):
    return float(np.interp(f, (0, 0.12, 0.35, 0.6, 0.82, 1), (0.04, 0.034, 0.024, 0.02, 0.014, 0.002)))


def tail_frames(path):
    """Along the tail: its tangent, its flat side (the crescent lies in a plane nearly upright, tilted out to its right), and the direction across its width."""
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        flat = V(1, 0, 0) - tan * tan.x
        flat = flat.normalized() if flat.length > 1e-5 else V(1, 0, 0)
        across = tan.cross(flat).normalized()
        out.append((tan, flat, across))
    return out


def loft(m, path, wfn, tfn, sides, caps=True):
    """A lens round a path: wide across, thin through its flat side, drawn to edges."""
    fr = tail_frames(path)
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        f = i / (n - 1)
        tan, flat, across = fr[i]
        w, t = wfn(f), tfn(f)
        ring = []
        for k in range(sides):
            a = TAU * k / sides
            c, s = math.cos(a), math.sin(a)
            ring.append(m.bm.verts.new(p + across * (w * math.copysign(abs(c) ** 0.85, c)) + flat * (t * math.copysign(abs(s) ** 1.15, s))))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    if caps:
        m.bm.faces.new(rings[0])
        m.bm.faces.new(list(reversed(rings[-1])))


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    core.ball(V(0, -0.11, 0.33), (0.115, 0.13, 0.14))         # the chest, deep under the ruff
    core.ball(V(0, 0.03, 0.34), (0.108, 0.15, 0.115))         # the ribs
    core.ball(V(0, 0.16, 0.335), (0.115, 0.12, 0.122))        # the rump
    for side in (1, -1):
        core.ball(V(side * 0.07, -0.12, 0.28), (0.052, 0.08, 0.1))       # the shoulder
        core.ball(V(side * 0.078, 0.16, 0.27), (0.062, 0.105, 0.115))    # the haunch
    core.tube(catmull([V(0, -0.16, 0.42), V(0, -0.21, 0.5), V(0, -0.25, 0.58)], 8), lambda f: 0.085 - 0.012 * f, sides=24)
    # the head: big and round, full cheeks, a small muzzle, a high forehead under the ears
    core.ball(HEAD, (0.118, 0.105, 0.102))                    # the skull
    core.ball(V(0, -0.29, 0.69), (0.1, 0.085, 0.07))          # the forehead
    core.ball(V(0, -0.35, 0.594), (0.036, 0.032, 0.026))      # the muzzle, small
    core.ball(V(0, -0.352, 0.572), (0.02, 0.022, 0.015))      # the chin
    for side in (1, -1):
        core.ball(V(side * 0.07, -0.31, 0.6), (0.07, 0.07, 0.066))         # the cheek
        core.ball(V(side * 0.019, -0.365, 0.59), (0.02, 0.016, 0.016))     # the whisker pad
        core.ball(V(side * 0.058, -0.338, 0.708), (0.044, 0.026, 0.012))   # the brow, soft and high over the eye
        core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.007, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        core.ball(V(side * 0.055, -0.325, 0.684), (0.05, 0.05, 0.036))     # behind the brow: the lid's hidden edge stays under it
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 14})])
    thin = Mesh()
    for key, side, knots, radii in LEGS:
        thin.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=22, flat=0.9, plane=V(1, 0, 0))
        paw = mir(knots[4], side)
        thin.ball(paw + V(0, -0.012, 0.004), (0.041, 0.049, 0.028), 26, 16)       # the paw, round
        for k in range(4):        # four toes round its front
            a = (k - 1.5) * 0.45
            thin.ball(paw + V(math.sin(a) * 0.03, -0.05 - math.cos(a) * 0.008, 0.006), (0.0155, 0.017, 0.016), 14, 10)
    th = thin.finish(N + "ThinHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


def build_tail(name, coll, sides=96, rows=360):
    """Dense enough for its stars to be points, not squares."""
    m = Mesh()
    path = catmull([TAIL[int(i)] for i in np.linspace(0, len(TAIL) - 1, 15)], max(2, rows // 14)) if rows > len(TAIL) else TAIL
    loft(m, path, tail_width, tail_thick, sides)
    return m.finish(name, coll)


# ---------- fur tufts, ears ----------
def tuft(m, root, direction, length, width, normal, bend=V(0, 0, 0), sides=6, per=5, flat=0.36):
    """A stylized lock of fur: a flame, broad just below its middle, curving, drawn to a fine point; flat against the body (thin along the skin's normal)."""
    d = direction.normalized()
    pts = [root - d * 0.008, root + d * (length * 0.45) + bend * 0.35, root + d * length + bend]
    m.tube(catmull(pts, per), lambda f: width * math.sin(math.pi * (0.22 + 0.78 * f)) ** 0.55 * (1 - f) ** 0.35 + 0.0011, sides=sides, flat=flat, plane=normal)


def tuft_list(tree):
    """Every lock: root on the skin, direction, length, width, the skin's normal, bend, and the region it belongs to. Where they make the silhouette: a frame of
    fluff round the face, the bib, the nape, shoulders, elbows, the backs of the thighs and the tail's root."""
    out = []

    def cast(origin, toward):
        d = (toward - origin).normalized()
        hit = tree.ray_cast(origin, d, 1.0)
        return (hit[0], hit[1]) if hit[0] is not None else (None, None)

    def add(origin, target, direction, length, width, bend, region):
        loc, nrm = cast(origin, target)
        if loc is not None:
            d = direction(nrm) if callable(direction) else direction
            b = bend(nrm) if callable(bend) else bend
            out.append((loc, d.normalized(), length, width, nrm, b, region))
    rng = np.random.default_rng(7)
    # the face's frame: two layers of locks round the cheeks down to the jaw, flaring out and back, the back layer longer
    for side in (1, -1):
        for layer in (1, 0):
            for k in range(6):
                t = k / 5
                target = V(side * 0.03, -0.3 + 0.025 * layer, 0.625 - 0.075 * t)
                origin = target + V(side * 0.4, 0.07 + 0.06 * layer, -0.12 * t)
                length = (0.07 + 0.025 * math.sin(math.pi * t)) * (1.2 if layer else 1.0) * (0.92 + 0.16 * rng.random())
                lean = (rng.random() - 0.5) * 0.35          # each its own lean, so no two lie parallel
                add(origin, target, lambda n, side=side, t=t, layer=layer, lean=lean: n * (0.35 + lean) + V(side * 0.9, 0.45 + 0.25 * layer + lean, -0.25 - 0.9 * t),
                    length, 0.04 if layer else 0.034, lambda n: n * 0.012 + V(0, 0.012, 0.012), "Head")
    # the bib: rows of broad locks bulging forward off the chest and falling, their tips curling out
    for row, (z, n, length, width) in enumerate(((0.47, 10, 0.085, 0.042), (0.43, 12, 0.1, 0.046), (0.39, 13, 0.105, 0.046), (0.35, 12, 0.095, 0.044), (0.31, 10, 0.075, 0.038))):
        for k in range(n):
            a = math.radians(-112 + 224 * (k + 0.5 * (row % 2) + (rng.random() - 0.5) * 0.6) / n)
            centre = V(0, -0.15 + (z - 0.41) * -0.6, z + (rng.random() - 0.5) * 0.012)
            region = "Neck" if row < 2 else "Chest"
            sway = (rng.random() - 0.5) * 0.6            # each lock its own lean, so the rows never read as scales
            add(centre + V(math.sin(a) * 0.4, -math.cos(a) * 0.4, 0), centre, lambda nn, sw=sway: nn * (0.35 + 0.25 * rng.random()) + V(sw, 0, -1.0),
                length * (0.8 + 0.45 * rng.random()), width * (0.8 + 0.4 * rng.random()), lambda nn, sw=sway: nn * 0.02 + V(sw * 0.02, 0, 0), region)
    # the crown, the nape, the shoulders
    for x in (-0.022, 0.0, 0.024):
        add(V(x, -0.28, 1.1), V(x, -0.28, 0.6), lambda n, x=x: n + V(x * 8, 0.7, 0), 0.03, 0.018, V(0, 0.01, -0.008), "Head")
    for x in (-0.045, -0.015, 0.015, 0.045):
        add(V(x, -0.12, 0.62), V(x, -0.22, 0.52), lambda n, x=x: n * 0.4 + V(x * 4, 1.0, -0.35), 0.06, 0.034, lambda n: n * 0.01, "Neck")
    for side in (1, -1):
        for dz in (0.0, 0.04):
            add(V(side * 0.5, -0.1, 0.33 + dz), V(0, -0.1, 0.33 + dz), lambda n, side=side: n * 0.5 + V(side * 0.2, 0.8, -0.7), 0.05, 0.03, lambda n: n * 0.008, "Chest")
    # the elbows and the backs of the thighs: locks trailing back
    for side, tag in ((1, "L"), (-1, "R")):
        for dz in (0.03, 0.0, -0.03):
            t = V(side * 0.066, -0.1, 0.19 + dz)
            add(t + V(side * 0.15, 0.4, 0), t, lambda n, side=side: n * 0.4 + V(side * 0.2, 1.0, -0.55), 0.045, 0.024, lambda n: n * 0.006, "LegF" + tag)
        for dz in (0.06, 0.02, -0.02):
            t = V(side * 0.08, 0.2, 0.24 + dz)
            add(t + V(side * 0.2, 0.4, 0), t, lambda n, side=side: n * 0.45 + V(side * 0.25, 1.0, -0.6), 0.06, 0.03, lambda n: n * 0.008, "LegB" + tag)
    # the tail's root: locks lying along it as it leaves the rump
    for k in range(5):
        a = TAU * k / 5
        c = TAIL[3]
        add(c + V(math.cos(a) * 0.3, 0.05, math.sin(a) * 0.3 + 0.05), c, lambda n: n * 0.3 + (TAIL[9] - TAIL[3]).normalized(), 0.07, 0.03, lambda n: n * 0.01, "Hips")
    return out


def build_tufts(tree, name, coll, sides=6, per=5):
    m = Mesh()
    meta = []
    for loc, d, length, width, nrm, bend, region in tuft_list(tree):
        before = len(m.bm.verts)
        tuft(m, loc, d, length, width, nrm, bend, sides, per)
        count = len(m.bm.verts) - before
        meta += [(region, (i // sides) / max(1, count // sides - 1), tuple(loc)) for i in range(count)]
    return m.finish(name, coll), meta


EAR = {"front": V(0.034, -0.315, 0.724), "back": V(0.124, -0.214, 0.686), "tip": V(0.18, -0.262, 0.912)}


def ear_thick(u, v):
    return 0.013 * (1 - u) ** 0.7 + 0.0028


def ear_point(side):
    """A very large pointed ear, cupped toward the front and a little out; u from its root to its tip, v across."""
    A, B, T = mir(EAR["front"], side), mir(EAR["back"], side), mir(EAR["tip"], side)
    n = (B - A).cross(T - A).normalized()
    if n.y > 0:
        n = -n          # facing forward
    n = (n + V(side * 0.3, 0, 0)).normalized()

    across = (B - A).normalized()

    def point(u, v):
        p = A.lerp(B, v).lerp(T + across * ((v - 0.5) * 0.007), u ** 0.92)
        cup = 0.036 * math.sin(math.pi * v) ** 0.8 * (1 - u ** 1.4)
        return tuple(p - n * cup)
    return point


def ear_front(side):
    A, B, T = mir(EAR["front"], side), mir(EAR["back"], side), mir(EAR["tip"], side)
    n = (B - A).cross(T - A).normalized()
    return -n if n.y > 0 else n


def build_ear(side, name):
    """The ear as a shell with thickness: its hollow violet, deep at the root and rosier toward the edge, its back black, a thin gold rim all round its edge."""
    o = sheet_hi(ear_point(side), ear_thick, 120, 80, name, lambda u, v: np.broadcast_to(FUR, (len(u), 3)), lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    nu, nv = 120, 80
    uu, vv = np.zeros((nu + 1) * (nv + 1) * 2), np.zeros((nu + 1) * (nv + 1) * 2)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    Nn = normals(o)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(ear_front(side))))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.6)
    hollow = mix(rgb(70, 30, 140), rgb(170, 110, 220), smooth(0.45, 0.05, edge) * 0.6)      # rosier toward the edge
    hollow = mix(hollow, rgb(40, 18, 90), smooth(0.4, 0.0, uu) * smooth(0.12, 0.3, edge) * 0.6)       # deepest at the root
    col = mix(np.broadcast_to(FUR, (len(uu), 3)), hollow, inside * smooth(0.035, 0.07, edge))
    rim = 1 - smooth(0.018, 0.034, edge)
    col = mix(col, GOLD, rim)
    paint(o, col, 0.62 - 0.32 * rim, 0.6 * rim)
    return o


EAR_FUR = ((0.04, 0.22, 0.11, 0.024), (0.04, 0.4, 0.13, 0.026), (0.04, 0.58, 0.12, 0.026), (0.04, 0.76, 0.1, 0.024),
           (0.14, 0.3, 0.1, 0.022), (0.14, 0.5, 0.115, 0.024), (0.14, 0.7, 0.095, 0.022), (0.26, 0.4, 0.08, 0.019), (0.26, 0.6, 0.08, 0.019),
           (0.02, 0.1, 0.08, 0.02), (0.02, 0.9, 0.07, 0.02))


def ear_tufts(side, name, coll, sides=6, per=5):
    """Soft white-lavender fur filling the hollow of the ear: locks rooted in it, rising along it toward the tip and spilling a little out of its front."""
    point = ear_point(side)
    fwd = ear_front(side)
    m = Mesh()
    for k, (u, v, h, w) in enumerate(EAR_FUR):
        root = V(*point(u, v)) + fwd * (ear_thick(u, v) * 0.5 + (0.004 if k % 2 == 0 else 0.01))
        up = (V(*point(min(1.0, u + 0.6), 0.5 + (v - 0.5) * 0.4)) - root).normalized()
        d = (up + fwd * (0.22 + 0.1 * (k % 3)) + V(side * (v - 0.5) * 0.8, 0, 0)).normalized()
        roll = (k % 4 - 1.5) * 0.32          # each lock turned a little about its length: neighbours never share a face's plane
        flat_to = (fwd * math.cos(roll) + d.cross(fwd).normalized() * math.sin(roll)).normalized()
        tuft(m, root, d, h, w, flat_to, fwd * 0.02, sides, per, flat=0.7)
    return m.finish(name, coll)


# ---------- the nose ----------
def nose_point(sx, sy, sz):
    """A point of the nose from a point of the unit sphere: an inverted triangle seen from the front, two soft lobes over a point; its lower front
    drawn forward and down to that point; its back half set into the muzzle."""
    t = (1 - sz) / 2                                          # 0 at its top, 1 at its point
    w = 0.0158 * (1 - t) ** 0.78 + 0.0012
    front = 0.0055 + 0.0095 * t ** 1.25
    depth = front if sy < 0 else 0.007
    z = NOSE_TOP - 0.0215 * t - 0.0024 * math.exp(-(sx / 0.32) ** 2) * max(0.0, sz) ** 3      # the cleft between its lobes
    return V(sx * w, NOSE_BASE_Y + sy * depth, z)


def build_nose(name, coll, seg=40, rings=28):
    m = Mesh()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in m.bm.verts:
        v.co = nose_point(v.co.x, v.co.y, v.co.z)
    return m.finish(name, coll)


def paint_nose(o):
    """Dusky mauve leather, lit across its top, with two dark nostrils curving under its sides."""
    P = verts(o)
    Nn = normals(o)
    col = mix(NOSE, NOSE_LIT, smooth(-0.2, 0.9, Nn[:, 2]) * 0.65)
    col = mix(col, NOSE * 0.6, smooth(0.0, -0.8, Nn[:, 2]) * 0.5)
    nostril = np.zeros(len(P))
    for side in (1, -1):
        c = np.array((side * 0.0062, NOSE_BASE_Y - 0.0105, NOSE_TOP - 0.0165))
        nostril = np.maximum(nostril, 1 - smooth(0.0016, 0.003, np.linalg.norm((P - c) * np.array([1.0, 1.6, 0.8]), axis=1)))
    col = mix(col, MOUTH, nostril)
    paint(o, col, 0.32 + 0.4 * nostril, np.zeros(len(P)))


# ---------- the collar and pendant ----------
def collar_frame():
    up = COLLAR_AXIS
    side = V(1, 0, 0)
    fwd = up.cross(side).normalized()        # toward its front (-Y side)
    if fwd.y > 0:
        fwd = -fwd
    return up, side, fwd


def ring(m, centre, radii, axis_a, axis_b, axis_n, tube_w, tube_h, segs=48, sides=8):
    """A closed band round an ellipse, its section tube_w across the ring's plane and tube_h along its axis."""
    rings = []
    for i in range(segs):
        a = TAU * i / segs
        out = (axis_a * math.cos(a) * radii[0] + axis_b * math.sin(a) * radii[1])
        p = centre + out
        r_dir = out.normalized()
        rings.append([m.bm.verts.new(p + r_dir * (math.cos(TAU * k / sides) * tube_w) + axis_n * (math.sin(TAU * k / sides) * tube_h)) for k in range(sides)])
    for i in range(segs):
        i2 = (i + 1) % segs
        for k in range(sides):
            k2 = (k + 1) % sides
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i2][k2], rings[i2][k]))


def build_collar(name, coll, segs=64, sides=10):
    """The band (navy), its two gold rims and its gold studs. Returns (band, gold)."""
    up, side, fwd = collar_frame()
    band = Mesh()
    ring(band, COLLAR_C, COLLAR_R, side, -fwd, up, 0.011, 0.017, segs, sides)
    gold = Mesh()
    for h in (-0.016, 0.016):            # standing proud of the band's edges, clear of its face
        ring(gold, COLLAR_C + up * h, (COLLAR_R[0] + 0.012, COLLAR_R[1] + 0.012), side, -fwd, up, 0.004, 0.0032, segs, 6)
    for k in range(10):
        a = TAU * (k + 0.5) / 10
        out = side * math.cos(a) * (COLLAR_R[0] + 0.011) + (-fwd) * math.sin(a) * (COLLAR_R[1] + 0.011)
        if out.normalized().dot(fwd) > 0.92:
            continue        # the pendant's place
        gold.ball(COLLAR_C + out, (0.0085, 0.0085, 0.0085), 12, 8)
    return band.finish(name + "Band", coll), gold.finish(name + "Gold", coll)


def pendant_frame():
    up, side, fwd = collar_frame()
    top = COLLAR_C + fwd * (COLLAR_R[1] + 0.013) - up * 0.01
    face = V(0, -1, -0.1).normalized()      # hanging in front of the ruff, facing forward
    down = face.cross(side).normalized()
    if down.z > 0:
        down = -down
    return top, face, side, down


def build_pendant(name, coll, segs=40):
    """A gold crescent framing a dark disc, the eclipse, hanging from the collar's front; a violet gem below it. Returns (gold, disc, gem)."""
    top, face, side, down = pendant_frame()
    c = top + down * 0.032 + face * 0.034       # clear of the ruff's locks
    gold = Mesh()
    # the crescent: a thick ring, widest at the bottom and thinning to two points at the top
    rings = []
    for i in range(segs + 1):
        a = math.radians(-160 + 320 * i / segs)
        d = side * math.sin(a) + down * math.cos(a)
        w = 0.0085 * (0.25 + 0.75 * math.cos(a * 0.5) ** 2)
        rings.append([gold.bm.verts.new(c + d * (0.024 + w * math.cos(TAU * k / 8)) + face * (0.0045 * math.sin(TAU * k / 8))) for k in range(8)])
    for i in range(segs):
        for k in range(8):
            k2 = (k + 1) % 8
            gold.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    gold.bm.faces.new(rings[0])
    gold.bm.faces.new(list(reversed(rings[-1])))
    gold.tube([top - down * 0.004, top + face * 0.03 + down * 0.006, c - down * 0.022], lambda f: 0.0042, sides=10)       # the bail, over the ruff
    g = c + down * 0.048
    gold.tube([c + down * 0.026, g - down * 0.012], lambda f: 0.0022, sides=8)           # the link to the gem
    disc = Mesh()
    disc.tube([c - face * 0.0018, c + face * 0.0018], lambda f: 0.0185, sides=36)       # inside the crescent's inner edge
    gem = Mesh()
    pts = [g + down * 0.02, g - down * 0.014, g + side * 0.011, g - side * 0.011, g + face * 0.007, g - face * 0.007]
    verts_ = [gem.bm.verts.new(p) for p in pts]
    for e in ((2, 4), (4, 3), (3, 5), (5, 2)):
        gem.bm.faces.new((verts_[0], verts_[e[0]], verts_[e[1]]))
        gem.bm.faces.new((verts_[1], verts_[e[1]], verts_[e[0]]))
    return gold.finish(name + "Gold", coll), disc.finish(name + "Disc", coll), gem.finish(N + "Gem_Glow_" + GEM_HEX, coll, smooth_shade=False)


# ---------- the eyes ----------
def disc_on_ball(m, fr, lift, shape, segs=36, rings=6):
    """A patch lying on the eyeball, lift off it: shape(phi, t) gives the point at angle phi on ring t (0 inner, 1 outer), in the eye's face coordinates."""
    A, X, Y = fr.axis, fr.outer, fr.up
    R = fr.radius + lift

    def on_ball(x, y):
        rr = min(0.999, math.hypot(x, y))
        d = A * math.sqrt(1 - rr * rr) + X * x + Y * y
        return fr.centre + d.normalized() * R
    grid = []
    for j in range(rings + 1):
        row = [m.bm.verts.new(on_ball(*shape(TAU * i / segs, j / rings))) for i in range(segs)]
        grid.append(row)
    for j in range(rings):
        for i in range(segs):
            i2 = (i + 1) % segs
            q = [grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]]
            mid = (q[0].co + q[2].co) / 2
            nrm = (q[1].co - q[0].co).cross(q[3].co - q[0].co)
            if nrm.length < 1e-14:
                nrm = (q[2].co - q[1].co).cross(q[3].co - q[1].co)
            if nrm.dot(mid - fr.centre) < 0:
                q.reverse()
            m.bm.faces.new(q)


def eye_paint(o, fr):
    """The sheet's eye, painted on the ball: violet, deep at the top and lit below, a ring of gold round the slit pupil, fine fibres, a dark rim."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(22, 12, 44), (len(px), 3)).copy()          # beyond the iris, in the lids' shadow
    iris = mix(rgb(66, 30, 146), rgb(200, 156, 255), smooth(0.75, -0.65, py / IRIS))
    gold = mix(rgb(255, 222, 120), rgb(240, 150, 46), smooth(0.05, CORE, r))
    iris = mix(gold, iris, smooth(CORE * 0.78, CORE * 1.22, r))
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 38 + np.sin(azi * 7) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    col = mix(col, rgb(14, 6, 30), smooth(IRIS - 0.12, IRIS - 0.02, r) * (1 - smooth(IRIS, IRIS + 0.04, r)))      # the dark ring at its edge
    slit = np.where(front, np.hypot(px / PUPIL_W, py / PUPIL_H), 3.0)
    col = mix(col, rgb(4, 2, 8), 1 - smooth(0.9, 1.04, slit))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


# ---------- the crest and the tail's streak ----------
def build_crest(tree, coll):
    """A gold crescent on the forehead, lying on the skin: horns up."""
    m = Mesh()
    loc, nrm, _, _ = tree.ray_cast(V(0, -0.655, 0.755), V(0, 1, -0.17).normalized(), 1.0)
    up = (V(0, 0, 1) - nrm * nrm.z).normalized()
    right = up.cross(nrm).normalized()
    segs = 28
    top, bot = [], []
    for i in range(segs + 1):
        a = math.radians(-150 + 300 * i / segs)
        outer = right * (math.sin(a) * 0.024) + up * (-math.cos(a) * 0.024)
        thick = 0.0085 * math.cos(a * 0.5) ** 1.6 + 0.0006
        inner = outer * ((0.024 - thick) / 0.024)
        for p, row in ((outer, top), (inner, bot)):
            q = loc + p
            hit = tree.ray_cast(q + nrm * 0.03, -nrm, 0.08)
            row.append(m.bm.verts.new((hit[0] + hit[1] * 0.0016) if hit[0] is not None else q + nrm * 0.0016))
    for i in range(segs):
        q = [top[i], top[i + 1], bot[i + 1], bot[i]]
        nn = (q[1].co - q[0].co).cross(q[3].co - q[0].co)
        if nn.dot(nrm) < 0:
            q.reverse()
        m.bm.faces.new(q)
    m.bm.normal_update()
    return m.finish(N + "Crest_Glow_" + CREST_HEX, coll, smooth_shade=False, recalc=False)


def build_streak(coll, sides=8):
    """A thread of gold light along the tail's outer edge, from its broad middle to its tip."""
    fr = tail_frames(TAIL)
    n = len(TAIL)
    pts = []
    for i in range(int(n * 0.28), n - 2):
        f = i / (n - 1)
        tan, flat, across = fr[i]
        pts.append(TAIL[i] - across * (tail_width(f) + 0.0005))      # the outer edge (the crescent's convex side)
    m = Mesh()
    m.tube(pts, lambda f: 0.0042 * math.sin(math.pi * min(1.0, f * 1.05)) ** 0.5 + 0.0012, sides=sides)
    return m.finish(N + "Streak_Glow_" + STREAK_HEX, coll)


# ---------- paint ----------
def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # fine hair lying along the body, and violet light only where the fur faces up and out, as the sheet lights it
    fur = fbm(P * np.array([160.0, 60.0, 160.0]), 1.0, 3, 3)
    col = mix(FUR, FUR * 1.6, smooth(0.45, 0.8, fur) * 0.6)
    col = mix(col, SHEEN, smooth(0.15, 0.85, Nn[:, 2]) * 0.4 + smooth(0.6, 0.95, fur) * 0.15)
    # the socks: white-lavender from the wrist and hock down, shading to violet where they meet the black
    edge = 0.115 + 0.009 * np.sin(x * 170 + y * 60) + 0.006 * np.sin(y * 230 - x * 90)      # a ragged line of fur
    sock = smooth(edge + 0.008, edge - 0.008, z)
    col = mix(col, mix(SOCK_SHADE, SOCK, smooth(0.09, 0.035, z)), sock)
    # round the eyes: a violet glow on the fur, black liner close round the opening and a wing at each outer corner
    for side in (1, -1):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        rel = P - np.array(tuple(fr.centre))
        e = np.linalg.norm(rel, axis=1)
        front = (rel @ np.array(tuple(fr.axis))) > -0.004
        glow = smooth(EYE_R * 1.7, EYE_R * 1.15, e) * front
        col = mix(col, EAR_IN * 0.7, glow * 0.35)
        liner = smooth(EYE_R * 1.28, EYE_R * 1.1, e) * front
        ox = rel @ np.array(tuple(fr.outer))
        oy = rel @ np.array(tuple(fr.lid_up))
        reach = (ox - EYE_R * 0.9) / (EYE_R * 0.75)
        wing = (reach > 0) * (reach < 1) * (1 - smooth(0.0, 0.0045 * (1 - np.clip(reach, 0, 1)) + 0.0008, np.abs(oy - EYE_R * (0.05 + 0.5 * np.clip(reach, 0, 1) ** 1.3)))) * front
        col = mix(col, MOUTH, np.clip(liner + wing, 0, 1))
    muzzle = smooth(0.07, 0.03, np.linalg.norm((P - np.array((0, -0.36, 0.59))) * np.array([1.0, 1.2, 1.4]), axis=1)) * (y < -0.31)
    col = mix(col, rgb(52, 40, 86), muzzle * 0.5)
    # the face: nose leather and the mouth's line
    philtrum = (np.abs(x) < 0.0018) * (z < 0.599) * (z > 0.581) * (y < -0.36)        # from under the nose's point to the mouth
    lip = (1 - smooth(0.0014, 0.0034, np.abs(z - (0.582 + 9 * x ** 2)))) * (np.abs(x) < 0.022) * (y < -0.35)
    mouth = np.clip(philtrum + lip, 0, 1)
    col = mix(col, MOUTH, mouth * 0.9)
    # gold spirals: one on each haunch, a smaller one on each shoulder
    swirl = np.zeros(len(P))
    for side in (1, -1):
        for c, size, turns in ((V(side * 0.13, 0.17, 0.3), 0.06, 2.2), (V(side * 0.115, -0.12, 0.3), 0.04, 1.6)):
            on_side = (x * side > 0.06) & (Nn[:, 0] * side > 0.3)
            dy, dz = y - c.y, z - c.z
            r = np.hypot(dy, dz)
            th = np.arctan2(dz, dy * side) % TAU
            pitch = size / turns
            best = np.full(len(P), 9.0)
            for k in range(int(turns) + 2):
                arm = pitch * (th + TAU * k) / TAU
                best = np.minimum(best, np.abs(r - arm) + 9 * ((th + TAU * k) / TAU > turns))
            line = (1 - smooth(0.0022, 0.0042, best)) * on_side * (r < size + 0.004)
            swirl = np.maximum(swirl, line)
    col = mix(col, GOLD, swirl)
    rough = 0.68 - 0.1 * smooth(0.45, 0.8, fur) - 0.35 * swirl
    relief = (fur - 0.5) * 0.0005 - 0.001 * mouth + 0.0006 * swirl
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, rough, 0.6 * swirl)


def paint_tufts(o, along, pale=False):
    P = verts(o)
    if pale:
        col = mix(SOCK_SHADE, TUFT_PALE, smooth(0.0, 0.6, along))
    else:
        # black at the root, deepening to violet, the tip lit bright, as the sheet draws its fur; each lock a little different
        col = mix(FUR, FUR * 1.5, fbm(P, 60.0, 2, 4))
        col = mix(col, SHEEN, smooth(0.25, 0.7, along) * 0.8)
        col = mix(col, VIOLET_TIP, smooth(0.6, 1.0, along) * (0.65 + 0.3 * fbm(P, 12.0, 2, 9)))
    paint(o, col, np.full(len(P), 0.6), np.zeros(len(P)))


def tail_coords(P):
    """Per point of the tail: how far along it (0..1) and across it (-1 at its outer, convex edge, +1 at its inner)."""
    f, d = nearest_on(TAIL, P)
    fr = tail_frames(TAIL)
    idx = np.clip(np.round(f * (len(TAIL) - 1)).astype(int), 0, len(TAIL) - 1)
    across = np.array([tuple(fr[i][2]) for i in idx])
    centre = np.array([tuple(TAIL[i]) for i in idx])
    w = np.array([tail_width(float(t)) for t in f])
    return f, ((P - centre) * across).sum(1) / np.maximum(w, 1e-3)


def paint_tail(o):
    P = verts(o)
    f, a = tail_coords(P)
    # light flowing along it: bands that follow its length, gently wavering
    q = np.stack([f * 7.0, a * 1.6, np.zeros_like(f)], 1)
    flow = fbm(q, 1.0, 4, 8)
    band = 0.5 + 0.5 * np.sin(a * 5.0 + f * 6.0 + flow * 5.0)
    col = mix(TAIL_DEEP, TAIL_MID, smooth(0.2, 0.8, 0.6 * flow + 0.4 * band))
    col = mix(col, TAIL_BRIGHT, smooth(0.7, 0.95, band) * smooth(0.2, 0.7, f) * 0.6)
    col = mix(col, FUR, smooth(0.14, 0.04, f))                   # black where it leaves the body
    stars = (np.random.default_rng(23).random(len(P)) > 0.996) * smooth(0.15, 0.3, f) * (np.abs(a) < 0.8)
    col = mix(col, STAR, stars * 0.9)
    rim = smooth(0.84, 0.95, np.abs(a)) * smooth(0.18, 0.32, f)
    col = mix(col, GOLD, rim)
    paint(o, col, 0.45 - 0.2 * rim, 0.6 * rim)


def tuft_along(meta):
    return np.array([m[1] for m in meta])


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    tree = tree_of(skin)
    data["tree"] = tree
    pieces["Tail"] = build_tail(N + "TailHi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, FUR, rgb(2, 2, 6))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, FUR, rgb(4, 3, 8), lower_share=0.8)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
        pieces["EarTufts" + tag] = ear_tufts(side, N + "EarTufts" + tag + "Hi", HI, 10, 8)
    pieces["Nose"] = build_nose(N + "NoseHi", HI)
    pieces["Tufts"], data["tuft_meta"] = build_tufts(tree, N + "TuftsHi", HI, 10, 8)
    band, gold = build_collar(N + "Collar", HI)
    pgold, disc, gem = build_pendant(N + "Pendant", HI)
    pieces["CollarBand"], pieces["CollarGold"], pieces["PendantGold"], pieces["PendantDisc"] = band, gold, pgold, disc
    glows = {"Gem": gem, "Crest": build_crest(tree, HI), "Streak": build_streak(HI)}
    glows["Glints"] = glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0068, 12), (22, -18, 0.0032, 8)))
    if not clay:
        paint_skin(skin)
        paint_nose(pieces["Nose"])
        paint_tail(pieces["Tail"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
        paint_tufts(pieces["Tufts"], tuft_along(data["tuft_meta"]))
        for tag in ("L", "R"):
            o = pieces["EarTufts" + tag]
            rows = np.arange(len(o.data.vertices)) // 10
            paint_tufts(o, (rows % 21) / 20.0, pale=True)
        plain(band, NAVY, 0.45, 0.0)
        plain(gold, GOLD, 0.28, 0.6)
        plain(pgold, GOLD, 0.28, 0.6)
        plain(disc, rgb(10, 6, 26), 0.2, 0.0)
    return pieces, frames, glows, data


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.append(mat)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.02, 0.48)
FACE_AT = (0, -0.3, 0.64)
EXTRA = [(0, -1, 0.05, 1.1, FACE_AT), (0.62, -0.75, 0.2, 1.1, FACE_AT), (1, -0.12, 0.08, 1.1, FACE_AT), (0.3, -0.9, 0.2, 0.55, (0.056, -0.36, 0.648)),
         (0.2, -0.95, -0.15, 0.9, (0, -0.24, 0.48)), (-0.8, 0.5, 0.35, 1.6, (-0.05, 0.3, 0.75))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.45)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 2800
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5, "PendantGold": 2.0, "PendantDisc": 2.0, "Nose": 3.0, "CollarGold": 1.3,
          "EarL": 1.4, "EarR": 1.4, "Tail": 1.2}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    m = Mesh()
    loft(m, catmull([TAIL[int(i)] for i in np.linspace(0, len(TAIL) - 1, 15)], 2), tail_width, tail_thick, 14)
    lows["Tail"] = m.finish(N + "TailLow", GAME)
    lows["Tufts"], data["low_tuft_meta"] = build_tufts(data["tree"], N + "TuftsLow", GAME, 4, 2)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 9, 5, N + "Ear" + tag + "Low")
        lows["EarTufts" + tag] = ear_tufts(side, N + "EarTufts" + tag + "Low", GAME, 5, 2)
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 26, 18)       # round enough for the painted iris to stay round
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Nose"] = build_nose(N + "NoseLow", GAME, 14, 10)
    lows["CollarBand"], lows["CollarGold"] = build_collar(N + "CollarLow", GAME, 24, 6)
    lows["PendantGold"], lows["PendantDisc"], gem = build_pendant(N + "PendantLow", GAME, 14)
    bpy.data.objects.remove(gem, do_unlink=True)          # (the high gem is already game-ready)
    triangulate(lows)
    return lows


def game_glows(frames, data, glows):
    """The Neon pieces, at the game's density: glints and gem as built; the crest and the streak again with fewer faces."""
    out = {}
    out["Glints"] = glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0068, 10), (22, -18, 0.0032, 6)))
    out["Crest"] = build_crest(data["tree"], GAME)
    out["Streak"] = build_streak(GAME, sides=6)
    out["Gem"] = glows["Gem"]
    glows["Gem"].users_collection[0].objects.unlink(glows["Gem"])
    GAME.objects.link(glows["Gem"])
    return out


# ---------- the skeleton ----------
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.04, 0.2, 0.36, 0.52, 0.68, 0.84)
SEG_BONE = ["Hips", "Body", "Body", "Chest", "Neck", "Head", "Head"]
SEG_BLEND = {1: 0.35, 3: 0.35, 4: 0.3, 5: 0.3}
LEG_F = (0.25, 0.5, 0.75)


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def ear_root(side):
    return mir(EAR["front"].lerp(EAR["back"], 0.5), side) + V(0, 0, -0.01)


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", SPINE[2].copy(), "Root"), ("Hips", SPINE[1].copy(), "Body"), ("Chest", SPINE[3].copy(), "Body"),
             ("Neck", SPINE[4].copy(), "Chest"), ("Head", SPINE[5].copy(), "Neck")]
    top, face, side, down = pendant_frame()
    bones.append(("Pendant", top.copy(), "Neck"))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for s_, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, ear_root(s_), "Head")]
    for key, side_, knots, _ in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        for k in range(3):
            bones.append(("Leg%s%d" % (key, k + 1), mir(knots[k], side_), parent))
            parent = "Leg%s%d" % (key, k + 1)
        bones.append(("Paw" + key, mir(knots[3], side_), parent))
    return armature(bones)


def spine_weight(k):
    """k: position along the spine's knots. A joint's bone carries what lies beyond it; they blend across each joint."""
    i = min(int(k), len(SEG_BONE) - 1)
    near = round(k)
    if near in SEG_BLEND and abs(k - near) < SEG_BLEND[near]:
        s = float(smooth(near - SEG_BLEND[near], near + SEG_BLEND[near], k))
        return {SEG_BONE[near - 1]: 1 - s, SEG_BONE[near]: s}
    return {SEG_BONE[i]: 1.0}


def leg_weight(key, f):
    names = ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw" + key]
    w = 0.07
    for j, knot in enumerate(LEG_F):
        if abs(f - knot) < w:
            s = float(smooth(knot - w, knot + w, f))
            return {names[j]: 1 - s, names[j + 1]: s}
    return {names[sum(1 for knot in LEG_F if f > knot)]: 1.0}


def tail_weight(f):
    return chain_weight(["Hips"] + TAIL_NAMES, (0.0,) + TAIL_F, float(f))


def body_weights(P):
    """The skin's weights at any points: spine, neck and head, the tail's root, the legs."""
    f_sp, d_sp = nearest_on(SPINE, P)
    k = f_sp * (len(SPINE) - 1)
    head_d = np.linalg.norm((P - np.array(tuple(HEAD))) / np.array([0.13, 0.12, 0.115]), axis=1)
    legs = {}
    for key, side, knots, radii in LEGS:
        f, d = nearest_on(leg_path(knots, side), P)
        legs[key] = (side, knots, radii, f, d)
    tf, td = nearest_on(TAIL, P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        w = dict(spine_weight(float(k[i])))
        if head_d[i] < 1.0:          # inside the head's round: the head's, wherever the spine's knots fall
            h = float(smooth(1.0, 0.85, head_d[i]))
            w = blend(w, {"Head": 1.0}, h)
        share = (1 - float(smooth(tail_width(float(tf[i])) * 0.9 + 0.01, tail_width(float(tf[i])) * 0.9 + 0.03, td[i]))) * float(smooth(0.02, 0.1, tf[i]))
        if share > 0:
            w = blend(w, tail_weight(tf[i]), share)
        paw_key = None
        for key, (side, knots, radii, f, d) in legs.items():
            pc = mir(knots[4], side) + V(0, -0.03, 0.0)
            if (Vector(P[i]) - pc).length < 0.07 and z < 0.07:
                paw_key = key
        if paw_key is not None:          # a paw and its toes: wholly its paw's bone
            out.append({"Paw" + paw_key: 1.0})
            continue
        for key, (side, knots, radii, f, d) in legs.items():
            if x * side <= 0:
                continue
            reach = leg_radius(radii, float(f[i])) + 0.03
            mm = float(smooth(knots[0].z, knots[0].z - 0.12, z)) * float(smooth(0.012, 0.04, abs(x))) * (1 - float(smooth(reach * 0.95, reach * 1.4, d[i])))
            if mm > 0:
                w = blend(w, leg_weight(key, float(f[i])), mm)
        out.append(w)
    return out


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    tf, _ = nearest_on(TAIL, verts(lows["Tail"]))
    weigh(lows["Tail"], [tail_weight(f) for f in tf])
    roots = np.array([m[2] for m in data["low_tuft_meta"]])
    uniq, inverse = np.unique(roots, axis=0, return_inverse=True)
    root_w = body_weights(uniq)
    weigh(lows["Tufts"], [root_w[j] for j in inverse.ravel()])
    for tag in ("L", "R"):
        for key in ("Ear", "EarTufts"):
            rigid(lows[key + tag], "Ear" + tag)
        for key in ("Eye", "LidU", "LidL"):
            rigid(lows[key + tag], (key if key != "Eye" else "Eye") + tag)
    for key in ("CollarBand", "CollarGold"):
        weigh(lows[key], body_weights(verts(lows[key])))
    for key in ("PendantGold", "PendantDisc"):
        rigid(lows[key], "Pendant")
    rigid(glows["Gem"], "Pendant")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    rigid(glows["Crest"], "Head")
    rigid(lows["Nose"], "Head")
    sf, _ = nearest_on(TAIL, verts(glows["Streak"]))
    weigh(glows["Streak"], [tail_weight(f) for f in sf])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateEclipseCat uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


# the sit, found by a search over its joints (paws flat and on the ground, the seat down, front paws not sinking): paws 3 and 9 mm up, the seat 17 mm
SIT = {"Body": (0.38, 0, 0, (0, -0.045, 0.02)), "Hips": (0.7, 0, 0), "LegFL1": (-0.38, 0, 0), "LegFR1": (-0.38, 0, 0), "LegBL1": (-0.4, 0, 0), "LegBR1": (-0.4, 0, 0),
       "LegBL2": (-1.1, 0, 0), "LegBR2": (-1.1, 0, 0), "LegBL3": (0.42, 0, 0), "LegBR3": (0.42, 0, 0),
       "Tail1": (0.5, 1.1, 0), "Tail2": (0.2, 0.7, 0), "Tail3": (0.0, 0.6, 0), "Tail4": (-0.1, 0.5, 0), "Tail5": (0, 0.4, 0), "Tail6": (0, 0.3, 0)}


def spec(table):
    out = {}
    for bone, v in table.items():
        rx, ry, rz = v[:3]
        out[bone] = game_turn(rx, ry, rz, v[3] if len(v) > 3 else (0, 0, 0))
    return out


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    stride = spec({"LegFL1": (0.45, 0, 0), "LegFL2": (0.1, 0, 0), "LegFR1": (-0.35, 0, 0), "LegFR3": (-0.9, 0, 0), "LegBL1": (-0.4, 0, 0), "LegBL2": (0.5, 0, 0),
                   "LegBR1": (0.4, 0, 0), "LegBR2": (0.35, 0, 0), "LegBR3": (-0.6, 0, 0)})
    leap = spec({"Body": (0.1, 0, 0), "LegFL1": (1.1, 0, 0), "LegFR1": (1.0, 0, 0), "LegFL3": (-0.4, 0, 0), "LegFR3": (-0.4, 0, 0), "LegBL1": (-0.9, 0, 0), "LegBR1": (-0.95, 0, 0),
                 "LegBL2": (0.5, 0, 0), "LegBR2": (0.5, 0, 0), **{n: (-0.08, 0, 0) for n in TAIL_NAMES}})
    look = spec({"Neck": (0.3, 0.3, 0.1), "Head": (0.25, 0.4, 0.25)})
    tail = spec({n: (0, 0.18 * (1 if k % 2 else -1), 0) for k, n in enumerate(TAIL_NAMES)})
    sit = spec(SIT)
    return {"Blink": lids(BLINK_U, BLINK_L), "Content": lids(BLINK_U * 0.55, BLINK_L * 0.6), "Wide": lids(-8, -6), "Stride": stride, "Leap": leap, "Look": look,
            "Tail": tail, "Sit": sit, "Ears": spec({"EarL": (-0.4, 0.3, 0), "EarR": (-0.4, -0.3, 0)}), "SkyLook": {**sit, **spec({"Neck": (0.25, 0, 0), "Head": (0.55, 0, 0)})}}


def lowest_of(body, parts):
    """The lowest point of the posed mesh among the vertices each set of bones carries: where its paws and its seat are."""
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, bones in parts.items():
        idx = {groups[b] for b in bones}
        mine = [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)]
        out[name] = round(float(co[mine, 2].min()), 4)
    return out


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.45)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.3, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.2 and p.center.z > 0.5, 2.0), (None, 1.0)], SCALES, margin=0.011)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.3, 0.3, 0.3, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.008, 0.022))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key, o in list(glows.items()):
        if key != "Gem":          # first, so the game's pieces take their exact names (a name in use gets ".001")
            bpy.data.objects.remove(o, do_unlink=True)
    glows = game_glows(frames, data, glows)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Head", "Chest", "Pendant", "Tail6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Sit", "SkyLook"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, {"FrontPaws": ("PawFL", "PawFR"), "HindPaws": ("PawBL", "PawBR"), "Seat": ("Hips",)}), flush=True)
    wide = (0.62, -0.72, 0.25, 3.2, VIEW_AT)
    side = (1, -0.05, 0.08, 3.2, VIEW_AT)
    face = (0.25, -0.95, 0.1, 1.1, FACE_AT)
    for name, view in (("Blink", face), ("Content", face), ("Wide", face), ("Stride", side), ("Leap", side), ("Look", face), ("Tail", (0, 0.4, 1, 3.2, VIEW_AT)),
                       ("Sit", side), ("Sit", wide), ("Ears", face), ("SkyLook", wide)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name + ("W" if view is wide and name == "Sit" else "")), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 3.2, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

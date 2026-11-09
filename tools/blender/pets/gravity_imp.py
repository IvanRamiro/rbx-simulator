"""The Gravity Imp (Epic, Gravity; Elemental Core Egg): "A small, smug creature that decides which way is down. Loose objects tend to follow it around."

A pocket-planet imp (the owner's choice, 2026-11-09), in a design language of its own: a small, big-headed, pot-bellied violet imp who lives on a moonlet of
its own, about the size of its body, with a gravity of its own. Its feet stand on the moonlet wherever it likes: on top, round the side or underneath, and
whichever way that is, is down for it. Long leaf-shaped ears, heavy-lidded gold eyes, one brow that rises, a smirk with a single fang showing, a cowlick, a
long thin tail ending in a spade. The moonlet is pale moonstone, pocked with craters, with violet veins of gravity glowing in its cracks; three pebbles
circle it like little moons, always round the imp's own middle.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/gravity_imp.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It floats: the moonlet hangs a little above the ground. The maps go to assets/pets/ElementalCoreEgg/.

What touches what: the imp's skin (body, head, legs, arms) is one piece; its soles rest on the moonlet, sunk into it a hair so no sliver of light shows
under them; the ears, hands and tail are their own pieces, each rooted inside the skin; the eyes sit in the head with their lids round them; the tuft roots
in the crown, the fang in the upper lip; the veins lie in the moonlet's surface; the pebbles touch nothing (they orbit).
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (Matrix and Vector: the game stage)
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "GravityImp"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours ----------
SKIN, SKIN_DEEP, SKIN_PALE = rgb(122, 86, 168), rgb(70, 44, 112), rgb(186, 156, 220)
BLUSH, EAR_IN = rgb(196, 104, 170), rgb(214, 150, 196)
LIP = rgb(52, 26, 66)
FANG = rgb(246, 240, 228)
STONE, STONE_DEEP, STONE_PALE, MARE = rgb(190, 188, 204), rgb(132, 128, 150), rgb(222, 220, 232), rgb(118, 112, 140)
PEBBLE, PEBBLE_PALE = rgb(92, 86, 108), rgb(148, 142, 162)
VEIN_HEX = "d28cff"

# ---------- the frame of it (its left; mirrored) ----------
C, R = V(0, 0, 0.18), 0.15                 # the moonlet: its middle and radius
SOLE_SINK = 0.0015                         # how far a sole sinks into the moonlet
HIP = V(0.03, 0.005, 0.425)
KNEE = V(0.034, -0.009, 0.39)
ANKLE = V(0.03, 0.002, 0.356)
FOOT = [V(0.03, 0.02, 0.343), V(0.031, 0.0, 0.341), V(0.033, -0.026, 0.343), V(0.034, -0.046, 0.35), V(0.033, -0.058, 0.361)]     # heel to the curled toe
FOOT_R = ((0, 0.015), (0.25, 0.017), (0.6, 0.012), (0.85, 0.007), (1, 0.003))
PELVIS, PELVIS_R = V(0, 0.008, 0.43), (0.044, 0.04, 0.034)
BELLY, BELLY_R = V(0, -0.014, 0.46), (0.048, 0.047, 0.047)
TORSO = [V(0, 0.008, 0.41), V(0, 0.004, 0.45), V(0, -0.002, 0.49), V(0, -0.003, 0.525)]
TORSO_R = ((0, 0.036), (0.35, 0.043), (0.7, 0.036), (1, 0.027))
NECK = [V(0, 0.0, 0.525), V(0, -0.004, 0.548), V(0, -0.008, 0.562)]
HEAD_C, HEAD_R = V(0, -0.012, 0.6), (0.074, 0.066, 0.064)
SHOULDER = V(0.05, 0.0, 0.522)
ELBOW = V(0.078, 0.004, 0.462)
WRIST = V(0.1, -0.008, 0.39)
ARM_R = ((0, 0.0135), (0.45, 0.011), (0.55, 0.0115), (1, 0.009))
EYE_C, EYE_R = V(0.031, -0.058, 0.612), 0.021
EYE_AXIS = V(0.3, -0.95, 0.05).normalized()
LID_UP, LID_LOW = (14.0, 125.0, 0.0018), (-34.0, -125.0, 0.0018)      # the upper lid half down: heavy-lidded, a smug one's
EAR_ROOT = V(0.05, 0.004, 0.618)
EAR_PATH = [V(0.036, 0.002, 0.612), V(0.072, 0.007, 0.628), V(0.115, 0.014, 0.65), V(0.158, 0.024, 0.665), V(0.198, 0.034, 0.67)]
TAIL = [V(0, 0.035, 0.428), V(0, 0.085, 0.414), V(0, 0.13, 0.43), V(0, 0.155, 0.468), V(0, 0.15, 0.512), V(0, 0.126, 0.538)]
TUFT = [V(0, 0.006, 0.652), V(0, 0.002, 0.676), V(0, -0.012, 0.69), V(0, -0.027, 0.688), V(0, -0.031, 0.679)]
ORBIT = 0.275                               # the pebbles' orbit round the moonlet's middle
PEBBLES = ((math.radians(35), (0.036, 0.03, 0.027), 1), (math.radians(160), (0.027, 0.024, 0.021), 2), (math.radians(255), (0.031, 0.027, 0.025), 3))


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def make_tags(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new(bm, before, **values):
    for key, value in values.items():
        layer = bm.verts.layers.float[key] if isinstance(value, float) else bm.verts.layers.int[key]
        for v in bm.verts:
            if v not in before:
                v[layer] = value


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


def arm_path(side, per=6):
    return catmull([mir(p, side) for p in (SHOULDER + V(-0.032, 0, -0.012), SHOULDER, ELBOW, WRIST)], per)      # (it starts deep in the chest: begun at the shoulder, its end showed)


def leg_path(side, per=6):
    return catmull([mir(p, side) for p in (HIP + V(-0.008, 0, 0.012), HIP, KNEE, ANKLE)], per)


def foot_path(side, per=6):
    return catmull([mir(p, side) for p in FOOT], per)


def onto_moonlet(P, lift):
    """Every point inside the moonlet's sphere (radius R + lift) pushed out onto it."""
    c = np.array(tuple(C))
    d = P - c
    r = np.linalg.norm(d, axis=1)
    inside = r < R + lift
    P[inside] = c + d[inside] / r[inside, None] * (R + lift)
    return P


# ---------- the skin: body, head, legs, arms ----------
def build_skin():
    m = Mesh()
    m.tube(catmull(TORSO, 8), lambda f: prof(TORSO_R, f), sides=40, flat=1.12)      # one smooth trunk from the seat to the neck
    m.ball(BELLY, BELLY_R, 48, 28)                                     # a little pot belly: well fed, pleased with itself
    m.ball(PELVIS, PELVIS_R, 40, 24)
    m.tube(catmull(NECK, 6), lambda f: 0.027 - 0.003 * f, sides=28)
    m.ball(V(0, 0.004, 0.516), (0.05, 0.03, 0.02), 40, 20)            # the slope from the neck to the shoulders: no shelf
    m.ball(HEAD_C, HEAD_R, 56, 36)
    m.ball(V(0, 0.004, 0.608), (0.071, 0.062, 0.06), 48, 30)          # the back of the skull, full and round (blending into the crown: no shelf)
    for side in (1, -1):
        m.ball(mir(V(0.038, -0.047, 0.58), side), (0.03, 0.026, 0.025), 32, 18)      # the cheek: plump, smug; the two meet under the nose, where the mouth goes
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.16,) * 3, 28, 18)      # the eye's socket
        m.tube(catmull([mir(p, side) for p in (V(0.011, -0.072, 0.627), V(0.028, -0.07, 0.637), V(0.046, -0.062, 0.644), V(0.058, -0.051, 0.645))], 6),
               lambda f: 0.0062 * math.sin(math.pi * (0.1 + 0.8 * f)) ** 0.6 * (1 - 0.45 * f) + 0.0018, sides=16)      # the brow ridge, rising outward: a sly one's; it fades into the temple
        m.ball(mir(SHOULDER, side) + mir(V(-0.004, 0, -0.002), side), (0.0165, 0.016, 0.015), 24, 14)
        m.tube(arm_path(side), lambda f: prof(ARM_R, f), sides=24)
        m.ball(mir(ELBOW, side), (0.0118,) * 3, 20, 12)
        m.tube(leg_path(side), lambda f: prof(((0, 0.019), (0.3, 0.016), (0.55, 0.0125), (1, 0.0115)), f), sides=24)
        m.ball(mir(KNEE, side), (0.013,) * 3, 20, 12)
        m.tube(foot_path(side), lambda f: prof(FOOT_R, f), sides=24, flat=1.3, plane=V(1, 0, 0))     # a long imp's foot, its toe curling up
    m.tube(catmull([V(0, -0.05, 0.562), V(0, -0.057, 0.551), V(0, -0.061, 0.543)], 6), lambda f: 0.0105 - 0.0068 * f, sides=24, flat=1.25)     # a small pointed chin
    m.tube(catmull([V(0, -0.07, 0.607), V(0, -0.08, 0.602), V(0, -0.086, 0.6), V(0, -0.0885, 0.603)], 6), lambda f: 0.0098 - 0.0068 * f, sides=20, flat=1.15)     # a small pointed nose, its tip turned up
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0022, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 9})])
    apply_mods(o, [("SUBSURF", {"subdivision_type": "SIMPLE", "levels": 1, "render_levels": 1})])     # a vertex every millimetre: the smirk is a line a millimetre wide
    P = verts(o)
    set_verts(o, onto_moonlet(P, -SOLE_SINK))          # the soles resting on the moonlet
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- ears, hands, tail, tuft, fang ----------
def ear_frame(side):
    """Along the ear, its flat face's normal (forward and up a little), and across it."""
    path = catmull([mir(p, side) for p in EAR_PATH], 10)
    face = V(0, -0.94, 0.34).normalized()
    return path, face


def ear_half_width(u):
    """Narrow where it leaves the head (its root, buried, narrower still), broadest a third of the way out, then to a point."""
    grow = smooth(0.0, 0.3, u)
    return float(0.009 + 0.024 * grow) * math.sin(math.pi * min(1.0, 0.18 + 0.82 * u)) ** 0.6 * (1 - 0.3 * u) + 0.0012


def build_ears(name, coll, nu=40, nv=16):
    """Long leaf-shaped ears, out to its sides and a little up, cupped toward the front; their roots deep in the head."""
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        path, face = ear_frame(side)

        def point(u, v, path=path, face=face, side=side):
            p = path_at(path, u)
            d = (path_at(path, min(1.0, u + 0.02)) - path_at(path, max(0.0, u - 0.02))).normalized()
            across = d.cross(face).normalized() * (-side)          # up on both sides, the same way all along it (flipped by its sign, its drooping tip twisted)
            w = (2 * v - 1)
            hw = ear_half_width(u)
            cup = -0.009 * (1 - w * w) * math.sin(math.pi * min(1.0, u * 1.2))
            droop = -0.012 * u * u - 0.0072 * u * u * w * (hw / 0.033)          # its tip droops, its outer edge a little more: by its width (by w alone, the narrow tip stood on edge and twisted)
            return tuple(p + across * (w * hw) + face * cup + V(0, 0, droop))
        m.sheet(point, lambda u, v: 0.0072 * (1 - 0.55 * u) * (0.45 + 0.55 * math.sqrt(max(0.0, 1 - (2 * v - 1) ** 6))), nu, nv)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


def hand_frame(side):
    w = mir(WRIST, side)
    palm = w + mir(V(0.003, -0.003, -0.017), side)
    return w, palm


def digit_paths(side):
    """Three fingers hanging down from the palm, curling in a little, and a thumb to the front."""
    w, palm = hand_frame(side)
    down, fwd, out = V(0, 0, -1), V(0, -1, 0), mir(V(1, 0, 0), side)
    paths = []
    for a, length in ((-0.42, 0.021), (0.0, 0.024), (0.42, 0.02)):
        d = (down * math.cos(a) + fwd * math.sin(a)).normalized()
        base = palm + d * 0.008
        paths.append([base, base + d * length * 0.5 - out * 0.002, base + d * length - out * 0.006])
    tb = palm + fwd * 0.009 - out * 0.004
    td = (fwd * 0.8 + down * 0.5 - out * 0.3).normalized()
    paths.append([tb, tb + td * 0.01, tb + td * 0.018 - out * 0.002])
    return paths


def build_hands(name, coll, ball=(24, 16), sides=12, per=4, tip=(12, 8)):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        w, palm = hand_frame(side)
        m.ball(palm, (0.011, 0.013, 0.0145), *ball)
        m.tube([w + V(0, 0, 0.006), palm], lambda f: 0.0092, sides=sides)          # (the wrist runs into the palm: no gap)
        for k, path in enumerate(digit_paths(side)):
            r0 = 0.0052 if k < 3 else 0.0055
            m.tube(catmull(path, per), lambda f, r0=r0: r0 * (1 - 0.35 * f), sides=sides)
            m.ball(path[-1], (r0 * 0.66,) * 3, *tip)          # the rounded fingertip
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


def spade_outline(u):
    """The spade's half-width along it: broad lobes behind, a point in front."""
    return 0.019 * math.sin(math.pi * min(1.0, u * 1.05)) ** 0.8 * (1 - 0.55 * u) + 0.0008


def tail_end():
    p, q = TAIL[-1], TAIL[-2]
    d = (p - q).normalized()
    return p, d


def build_tail(name, coll, sides=16, per=8, spade=(22, 10)):
    m = Mesh()
    path = catmull(TAIL, per)
    m.tube(path, lambda f: 0.0085 * (1 - f) + 0.0042 * f, sides=sides)
    p, d = tail_end()
    across = d.cross(V(1, 0, 0)).normalized()
    side_v = V(1, 0, 0)

    def point(u, v):
        hw = spade_outline(u)
        w = 2 * v - 1
        return tuple(p - d * 0.008 + d * (0.044 * u) + side_v * (w * hw) + across * (0.004 * (1 - w * w)))
    m.sheet(point, lambda u, v: 0.0055 * (1 - 0.6 * u) * (0.45 + 0.55 * math.sqrt(max(0.0, 1 - (2 * v - 1) ** 6))), spade[0], spade[1])
    return m.finish(name, coll)


def build_tuft(name, coll, sides=14, per=6):
    m = Mesh()
    m.tube(catmull(TUFT, per), lambda f: 0.011 * (1 - f) ** 0.7 + 0.0016, sides=sides)
    return m.finish(name, coll)


def fused(o, voxel, tags=()):
    """One closed surface out of overlapping balls and tubes: baked from as they were, rays met the fingers' insides within the palm (their normals turned
    backward: black patches). A tag is carried over from the nearest original vertex."""
    keep = {}
    if tags:
        P0 = verts(o)
        for t in tags:
            keep[t] = (P0, read_tag(o, t))
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    if keep:
        P = verts(o)
        from mathutils.kdtree import KDTree
        for t, (P0, vals) in keep.items():
            kd = KDTree(len(P0))
            for i, q in enumerate(P0):
                kd.insert(q, i)
            kd.balance()
            a = o.data.attributes.new(t, "INT", "POINT")
            a.data.foreach_set("value", [int(vals[kd.find(q)[1]]) for q in P])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the face's lines, found on the face ----------
MOUTH = [V(-0.03, -0.03, 0.57), V(-0.015, -0.03, 0.566), V(0.002, -0.03, 0.5655), V(0.019, -0.03, 0.569), V(0.032, -0.03, 0.578)]      # its left corner up: the smirk


def on_face(tree, p, lift=0.0):
    loc, nrm, _, _ = tree.ray_cast(V(p.x, -0.2, p.z), V(0, 1, 0), 0.4)
    return (loc + nrm * lift) if loc else p


def mouth_path(tree, per=8):
    return catmull([on_face(tree, p) for p in MOUTH], per)


def fang_points(tree):
    """A single small fang, down over the lower lip under the smirk's raised corner."""
    root = on_face(tree, V(0.017, 0, 0.5705), -0.003)
    tip = on_face(tree, V(0.0172, 0, 0.5625), 0.0014)
    return root, tip


def build_fang(tree, name, coll, sides=12, per=4):
    root, tip = fang_points(tree)
    m = Mesh()
    m.tube([root.lerp(tip, k / per) for k in range(per + 1)], lambda f: 0.0036 * (1 - f) ** 1.1 + 0.0003, sides=sides, flat=1.35)      # a little triangle of a tooth, broad at its root
    return m.finish(name, coll)


# ---------- the moonlet ----------
CRATERS = ((V(0.4, -0.75, 0.52), 0.34, 0.006), (V(-0.8, 0.2, 0.2), 0.28, 0.005), (V(0.2, 0.6, -0.75), 0.4, 0.007), (V(-0.3, -0.5, -0.8), 0.22, 0.004),
           (V(0.85, 0.3, -0.2), 0.2, 0.004), (V(-0.2, 0.9, 0.35), 0.18, 0.0035), (V(0.1, -0.95, -0.25), 0.14, 0.003), (V(-0.75, -0.6, 0.1), 0.13, 0.003),
           (V(0.6, -0.1, 0.78), 0.12, 0.0028), (V(-0.55, 0.35, -0.75), 0.15, 0.0035), (V(0.75, 0.62, 0.15), 0.1, 0.0025), (V(-0.1, 0.25, 0.97), 0.09, 0.0022))


def crater_field(D):
    """Per direction from the moonlet's middle: how far the surface moves out (bowls in, rims up), and how deep in a bowl it lies (0..1)."""
    disp = np.zeros(len(D))
    bowl = np.zeros(len(D))
    rim = np.zeros(len(D))
    for c, size, depth in CRATERS:
        cd = np.array(tuple(c.normalized()))
        ang = np.arccos(np.clip(D @ cd, -1, 1))
        x = ang / size
        b = np.clip(1 - x * x, 0, 1)
        disp += -depth * b + 0.4 * depth * np.exp(-((x - 1.0) / 0.22) ** 2)
        bowl = np.maximum(bowl, b)
        rim = np.maximum(rim, np.exp(-((x - 1.0) / 0.18) ** 2))
    return disp, bowl, rim


def moonlet_radius(D):
    disp, _, _ = crater_field(D)
    return R + disp + 0.0012 * (fbm(D * R, 30.0, 4, 11) - 0.5)


def build_moonlet(name, coll, subdiv=7):
    m = Mesh()
    bmesh.ops.create_icosphere(m.bm, subdivisions=subdiv, radius=1.0)
    o = m.finish(name, coll)
    P = verts(o)
    D = P / np.linalg.norm(P, axis=1)[:, None]
    set_verts(o, np.array(tuple(C)) + D * moonlet_radius(D)[:, None])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


VEINS = ((V(0.2, 0.6, -0.75), ((0.0, 0.55), (0.9, 0.5), (1.9, 0.62), (2.8, 0.45))), (V(0.4, -0.75, 0.52), ((0.4, 0.55), (2.2, 0.5), (4.2, 0.4))),
         (V(-0.3, -0.5, -0.8), ((1.0, 0.5), (3.4, 0.45))), (V(-0.8, 0.2, 0.2), ((0.3, 0.5), (2.6, 0.55), (4.6, 0.38))))


def vein_paths():
    """Cracks of violet light running out from the big craters' rims across the stone, each wandering a little."""
    out = []
    for k, (start, arms) in enumerate(VEINS):
        c = start.normalized()
        a = c.orthogonal().normalized()
        b = c.cross(a).normalized()
        size = next(sz for cc, sz, _ in CRATERS if (cc.normalized() - c).length < 1e-6)
        for j, (heading, reach) in enumerate(arms):
            pts = []
            steps = 14
            for i in range(steps + 1):
                f = i / steps
                ang = size * (0.95 + reach / size * f)             # from the rim outward
                wob = 0.12 * math.sin(f * 9 + k * 2 + j) * f
                h = heading + wob
                d = (c * math.cos(ang) + (a * math.cos(h) + b * math.sin(h)) * math.sin(ang)).normalized()
                pts.append(d)
            out.append(pts)
    return out


def vein_radius(f):
    return 0.0042 * (1 - f) ** 0.6 + 0.0012


def build_veins(name, coll, sides=8, per=3, stride=1):
    m = Mesh()
    for dirs in vein_paths():
        dirs = dirs[::stride] if (len(dirs) - 1) % stride == 0 else dirs[::stride] + [dirs[-1]]
        D = np.array([tuple(d) for d in dirs])
        rad = moonlet_radius(D)
        pts = [C + d * (float(r) - 0.0012) for d, r in zip(dirs, rad)]
        m.tube(catmull(pts, per), vein_radius, sides=sides)
    return m.finish(name, coll)


def pebble_at(k):
    a, radii, seed = PEBBLES[k]
    return C + V(math.cos(a), math.sin(a), 0) * ORBIT, radii, seed


def build_pebbles(name, coll, seg=(28, 18)):
    m = Mesh()
    make_tags(m.bm, ints=("pebble",))
    for k in range(len(PEBBLES)):
        before = set(m.bm.verts)
        c, radii, seed = pebble_at(k)
        m.ball(c, radii, *seg)
        tag_new(m.bm, before, pebble=k)
    o = m.finish(name, coll)
    tags = read_tag(o, "pebble")
    P = verts(o)
    for k in range(len(PEBBLES)):
        c, radii, seed = pebble_at(k)
        sel = tags == k
        d = P[sel] - np.array(tuple(c))
        n = d / np.linalg.norm(d, axis=1)[:, None]
        lump = 0.008 * (fbm(n, 2.2, 3, seed * 7) - 0.5) + 0.003 * (fbm(n, 6.0, 2, seed * 7 + 3) - 0.5)
        P[sel] = np.array(tuple(c)) + d + n * lump[:, None]
    set_verts(o, P)
    return o


# ---------- the eyes ----------
def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=9.0) for side, tag in ((1, "L"), (-1, "R"))}      # the lids' outer ends raised: sly


def eye_paint(o, fr):
    """A gold eye: amber round a big round pupil, a darker ring at the iris's edge, a warm white."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(250, 206, 84), rgb(214, 128, 30), smooth(0.2, 0.5, r))
    col = mix(col, rgb(120, 60, 20), smooth(0.48, 0.56, r))
    col = mix(col, rgb(246, 240, 230), smooth(0.56, 0.6, r))
    col = mix(col, rgb(14, 8, 18), 1 - smooth(0.24, 0.28, r))
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.06), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.5
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_skin()
    tree = tree_of(pieces["Skin"])
    data["tree"] = tree
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SKIN, SKIN_DEEP * 0.45)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SKIN, SKIN_DEEP * 0.6, lower_share=0.6)
    pieces["Ears"] = build_ears(N + "EarsHi", HI)
    pieces["Hands"] = fused(build_hands(N + "HandsHi", HI), 0.0006, ("side",))
    pieces["Tail"] = fused(build_tail(N + "TailHi", HI), 0.0006)
    pieces["Tuft"] = build_tuft(N + "TuftHi", HI)
    pieces["Fang"] = build_fang(tree, N + "FangHi", HI)
    pieces["Moonlet"] = build_moonlet(N + "MoonletHi", HI)
    pieces["Pebbles"] = build_pebbles(N + "PebblesHi", HI)
    glows = {"Veins": build_veins(N + "Veins_Glow_" + VEIN_HEX, HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-22, 4, 0.0052, 10), (18, -18, 0.0024, 6)))}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


# ---------- painting ----------
def brow_path(side, per=6):
    return catmull([mir(p, side) for p in (V(0.011, -0.072, 0.627), V(0.028, -0.07, 0.637), V(0.046, -0.062, 0.644), V(0.058, -0.051, 0.645))], per)


def skin_fields(P, Nn, tree):
    """Per point of the skin: the smirk's line (and the dimple at its raised corner), how near the brows, the shadow round the eyes."""
    mp = mouth_path(tree)
    mf, md = nearest_on(mp, P)
    front = Nn[:, 1] < -0.2
    width = 0.0012 + 0.0005 * np.sin(np.pi * mf)
    line = (1 - smooth(width, width + 0.0008, md)) * front * (P[:, 1] < -0.04)
    corner = np.array(tuple(mp[-1]))
    dimple = (1 - smooth(0.0, 0.0045, np.linalg.norm(P - corner, axis=1))) * front
    brow = np.zeros(len(P))
    socket = np.zeros(len(P))
    for side in (1, -1):
        _, bd = nearest_on(brow_path(side), P)
        brow = np.maximum(brow, 1 - smooth(0.004, 0.0085, bd))
        e = np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1) / EYE_R
        socket = np.maximum(socket, smooth(1.0, 1.12, e) * (1 - smooth(1.25, 1.75, e)))
    return line, dimple, brow, socket, mf, md


def carve_skin(o, tree):
    P, Nn = verts(o), normals(o)
    line, dimple, brow, socket, _, _ = skin_fields(P, Nn, tree)
    navel = 1 - smooth(0.0, 0.0045, np.linalg.norm(P - np.array((0.0, -0.06, 0.452)), axis=1))
    d = -0.0013 * line - 0.0012 * dimple - 0.0016 * navel + 0.0006 * (fbm(P, 220.0, 2, 3) - 0.5)
    set_verts(o, P + Nn * d[:, None])


def paint_skin(o, tree):
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    line, dimple, brow, socket, mf, md = skin_fields(P, Nn, tree)
    n = len(P)
    col = np.broadcast_to(SKIN, (n, 3)).copy()
    # darker down its back and over its crown, as a cat's coat is; mottled a little
    back = smooth(-0.1, 0.7, Nn[:, 1] * 0.8 + Nn[:, 2] * 0.35)
    col = mix(col, SKIN_DEEP, back * 0.45)
    col = mix(col, SKIN_DEEP * 1.1, smooth(0.55, 0.8, fbm(P, 60.0, 3, 5)) * 0.18)
    col = mix(col, SKIN_PALE, smooth(0.6, 0.85, fbm(P, 25.0, 3, 8)) * 0.1)
    # its belly and chest, pale lilac; the muzzle round the mouth, too
    belly = (1 - smooth(0.75, 1.0, np.hypot(x / 0.038, (z - 0.462) / 0.05))) * smooth(-0.1, -0.5, Nn[:, 1])
    muzzle = (1 - smooth(0.7, 1.0, np.hypot(x / 0.038, (z - 0.566) / 0.02))) * smooth(-0.3, -0.7, Nn[:, 1])
    col = mix(col, SKIN_PALE, np.clip(belly * 0.85 + muzzle * 0.6, 0, 1))
    # the ends of its limbs darker: hands come darker still, on their own piece
    limbs = np.zeros(n)
    for side in (1, -1):
        f, d = nearest_on(foot_path(side), P)
        limbs = np.maximum(limbs, (d < 0.02) * smooth(0.2, 1.0, f))
        fa, da = nearest_on(arm_path(side), P)
        limbs = np.maximum(limbs, (da < 0.018) * smooth(0.6, 1.0, fa) * 0.6)
        fl, dl = nearest_on(leg_path(side), P)
        limbs = np.maximum(limbs, (dl < 0.02) * smooth(0.55, 1.0, fl) * 0.5)
    col = mix(col, SKIN_DEEP * 0.85, limbs * 0.7)
    col = mix(col, rgb(100, 70, 140), smooth(0.344, 0.338, z) * 0.6)          # its soles, worn
    # its face: a blush on the cheeks, a few freckles, the nose's tip pinker, a shadow round the eyes, darker brows, the smirk
    for side in (1, -1):
        cd = np.linalg.norm(P - np.array(tuple(mir(V(0.046, -0.06, 0.58), side))), axis=1)
        col = mix(col, BLUSH, (1 - smooth(0.006, 0.02, cd)) * 0.45)
    nose = 1 - smooth(0.0, 0.007, np.linalg.norm(P - np.array((0.0, -0.088, 0.602)), axis=1))
    col = mix(col, BLUSH * 0.95, nose * 0.5)
    d1, d2, own = cells_3d(P, 520.0, 13)
    spots = (own > 0.85) * (1 - smooth(0.12, 0.26, d1)) * (Nn[:, 1] < -0.35) * (z > 0.57) * (z < 0.61)
    col = mix(col, SKIN_DEEP * 0.8, spots * 0.55)
    col = mix(col, SKIN_DEEP * 0.75, socket * (0.35 + 0.25 * (z > 0.612)))
    col = mix(col, SKIN_DEEP * 0.6, brow * 0.85)
    col = mix(col, LIP, np.clip(line + dimple * 0.4, 0, 1))
    rough = 0.55 - 0.1 * nose - 0.08 * belly + 0.05 * back
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def cells_3d(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    own = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                off = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                d = np.linalg.norm(q - c - off, axis=1)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                d1 = np.where(nearer, d, d1)
    return d1, d2, own


def ear_coords(P, side):
    """Per point of an ear: how far along it (0 root, 1 tip), how far across from its middle line (0 middle, 1 its edge)."""
    path, face = ear_frame(side)
    f, d = nearest_on(path, P)
    hw = np.array([ear_half_width(float(u)) for u in f])
    return f, d / np.maximum(hw, 1e-4)


def paint_ears(o):
    P, Nn = verts(o), normals(o)
    tags = read_tag(o, "side")
    n = len(P)
    col = np.broadcast_to(SKIN, (n, 3)).copy()
    for side in (1, -1):
        sel = tags == side
        f, across = ear_coords(P[sel], side)
        _, face = ear_frame(side)
        front = (Nn[sel] @ np.array(tuple(face))) > 0.0
        inner = front * (1 - smooth(0.45, 0.75, across)) * smooth(0.12, 0.3, f) * (1 - smooth(0.75, 0.95, f))
        c = mix(np.broadcast_to(SKIN, (sel.sum(), 3)), SKIN_DEEP, (~front) * 0.35 + smooth(0.6, 1.0, f) * 0.4)
        c = mix(c, EAR_IN, inner * 0.85)
        c = mix(c, SKIN_DEEP * 0.8, smooth(0.85, 1.0, across) * 0.4)                  # its rim
        vein = (np.abs(np.sin(f * 30 + across * 3)) < 0.08) * inner * 0.25            # a few faint veins in its thin skin
        c = mix(c, BLUSH, vein)
        col[sel] = c
    paint(o, np.clip(col, 0, 1), np.full(n, 0.5), np.zeros(n))


def paint_hands(o):
    P = verts(o)
    tags = read_tag(o, "side")
    n = len(P)
    col = np.broadcast_to(SKIN, (n, 3)).copy()
    for side in (1, -1):
        sel = tags == side
        w, palm = hand_frame(side)
        down = np.clip((np.array(tuple(palm))[2] - P[sel, 2]) / 0.03, 0, 1)
        col[sel] = mix(np.broadcast_to(SKIN, (sel.sum(), 3)), SKIN_DEEP * 0.85, 0.3 + 0.5 * down)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.5), np.zeros(n))


def paint_tail(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    f, d = nearest_on(catmull(TAIL, 8), P)
    p, dd = tail_end()
    along = (P - np.array(tuple(p))) @ np.array(tuple(dd))
    spade = along > -0.008
    col = mix(np.broadcast_to(SKIN, (n, 3)), SKIN_DEEP, 0.25 + 0.4 * f)
    col = mix(col, SKIN_DEEP * 0.75, spade * 1.0)
    rim = spade * smooth(0.6, 0.95, np.abs((P[:, 0]) / 0.019))
    col = mix(col, SKIN * 1.1, rim * 0.5)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.48), np.zeros(n))


def paint_tuft(o):
    P = verts(o)
    n = len(P)
    col = mix(np.broadcast_to(SKIN_DEEP * 0.8, (n, 3)), SKIN_DEEP * 1.2, 0.5 + 0.5 * np.sin(P[:, 0] * 2400 + P[:, 2] * 300))
    paint(o, np.clip(col, 0, 1), np.full(n, 0.45), np.zeros(n))


def paint_fang(o):
    P = verts(o)
    n = len(P)
    zz = P[:, 2]
    col = mix(np.broadcast_to(FANG, (n, 3)), rgb(224, 210, 180), smooth(0.564, 0.57, zz) * 0.6)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.3), np.zeros(n))


def vein_distance(D):
    """Per direction from the moonlet's middle: the angle to the nearest vein."""
    best = np.full(len(D), 9.0)
    for dirs in vein_paths():
        pts = np.array([tuple(d) for d in dirs])
        _, dist = nearest_on([Vector(tuple(p)) for p in pts], D)
        best = np.minimum(best, dist)
    return best


def carve_moonlet(o):
    P, Nn = verts(o), normals(o)
    D = (P - np.array(tuple(C)))
    D /= np.linalg.norm(D, axis=1)[:, None]
    vd = vein_distance(D) * R
    groove = 1 - smooth(0.0035, 0.0065, vd)
    pits = cells_3d(D, 22.0, 31)
    pit = (pits[2] > 0.7) * (1 - smooth(0.0, 0.25, pits[0]))
    d = -0.0028 * groove - 0.0012 * pit + 0.0004 * (fbm(D, 70.0, 2, 4) - 0.5)
    set_verts(o, P + Nn * d[:, None])


def paint_moonlet(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    D = (P - np.array(tuple(C)))
    D /= np.linalg.norm(D, axis=1)[:, None]
    disp, bowl, rim = crater_field(D)
    col = np.broadcast_to(STONE, (n, 3)).copy()
    col = mix(col, MARE, smooth(0.5, 0.62, fbm(D, 1.6, 4, 21)) * 0.75)                  # dark seas of old stone
    col = mix(col, STONE_PALE, smooth(0.55, 0.8, fbm(D, 9.0, 3, 22)) * 0.3)
    col = mix(col, STONE_DEEP * 0.9, smooth(0.6, 0.85, fbm(D, 40.0, 3, 23)) * 0.25)     # fine dust and grit
    col = mix(col, STONE_DEEP, bowl * 0.55)
    col = mix(col, STONE_PALE * 1.04, rim * 0.6)
    pits = cells_3d(D, 22.0, 31)
    pit = (pits[2] > 0.7) * (1 - smooth(0.0, 0.25, pits[0]))
    col = mix(col, STONE_DEEP * 0.8, pit * 0.5)
    vd = vein_distance(D) * R
    col = mix(col, rgb(70, 40, 110), (1 - smooth(0.003, 0.008, vd)) * 0.9)             # scorched violet round the veins
    col = mix(col, rgb(150, 120, 190), (1 - smooth(0.008, 0.016, vd)) * 0.25)
    rough = 0.82 - 0.1 * bowl
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_pebbles(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    col = mix(np.broadcast_to(PEBBLE, (n, 3)), PEBBLE_PALE, smooth(0.45, 0.75, fbm(P, 90.0, 3, 41)) * 0.6)
    col = mix(col, rgb(70, 64, 86), smooth(0.6, 0.8, fbm(P, 220.0, 2, 42)) * 0.4)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.85), np.zeros(n))


def paint_all(pieces, frames, data):
    tree = data["tree"]
    carve_skin(pieces["Skin"], tree)
    paint_skin(pieces["Skin"], tree)
    paint_ears(pieces["Ears"])
    paint_hands(pieces["Hands"])
    paint_tail(pieces["Tail"])
    paint_tuft(pieces["Tuft"])
    paint_fang(pieces["Fang"])
    carve_moonlet(pieces["Moonlet"])
    paint_moonlet(pieces["Moonlet"])
    paint_pebbles(pieces["Pebbles"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)


VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0, 0.36)
FACE_AT = (0, -0.05, 0.6)
EXTRA = [(0, -1, 0.1, 0.5, FACE_AT), (0.62, -0.75, 0.2, 0.5, FACE_AT), (1, -0.15, 0.1, 0.5, FACE_AT), (0.3, 0.6, 0.6, 0.6, (0, 0.06, 0.55)),
         (0.5, -0.6, -0.1, 0.45, (0.06, -0.02, 0.38)), (0.55, 0.75, 0.4, 0.32, (0.06, 0.0, 0.62)), (0.1, -1, -0.05, 0.22, (0.01, -0.07, 0.57))]

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
        mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=1.8, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS, MOON_QUADS = 5000, 1500          # (at 3,400 its forearms got six strips round them, cutting inside the elbow: the bake read the skin's inside)
SCALES = {"Moonlet": 0.75, "EyeL": 2.0, "EyeR": 2.0, "LidUL": 1.0, "LidUR": 1.0, "LidLL": 1.0, "LidLR": 1.0, "Ears": 1.0, "Hands": 0.9, "Tail": 0.7,
          "Tuft": 0.6, "Fang": 0.6, "Pebbles": 0.6}


HEAD_LINE = 0.535          # the face and head above it get more of the atlas than the body below it


def imp_unwrap(lows, margin=0.006):
    """The atlas, each piece unwrapped on its own: the projection's charts become seams (and a seam round the neck, where the head's share of the
    map changes), then an angle-based unwrap, which can't fold a chart over itself (smart projection alone folded charts round its thin limbs over
    themselves: a thousand texels painted twice). Each piece is then scaled to its share and all are packed together."""
    for key, o in lows.items():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        select_only([o])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(40), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.seams_from_islands()
        bpy.ops.object.mode_set(mode="OBJECT")
        if key == "Skin":
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.normal_update()

            def face_region(f):
                c = f.calc_center_median()
                return c.z > HEAD_LINE + 0.006 and f.normal.y < -0.35 and abs(c.x) < 0.072
            for e in bm.edges:
                if len(e.link_faces) != 2:
                    continue
                zs = [f.calc_center_median().z > HEAD_LINE for f in e.link_faces]
                fr = [face_region(f) for f in e.link_faces]
                if zs[0] != zs[1] or fr[0] != fr[1]:
                    e.seam = True
                elif fr[0] and fr[1]:
                    e.seam = False          # the face is one piece: a seam across it shows as a line
            bm.to_mesh(o.data)
            bm.free()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.002)
        bpy.ops.object.mode_set(mode="OBJECT")
        # a small fragment the angle-based unwrap collapsed to nothing (it did, at a brow's end): its island projected again on its own
        uvd = o.data.uv_layers.active.data
        flat = []
        for p in o.data.polygons:
            a, b2, c = [uvd[l].uv for l in list(p.loop_indices)[:3]]
            if abs((b2.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b2.y - a.y)) < 1e-10:
                flat.append(p.index)
        if flat:
            print("UV REDO", key, len(flat), "collapsed faces", flush=True)
            o.data.polygons.foreach_set("select", [p.index in set(flat) for p in o.data.polygons])
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_linked(delimit={"SEAM"})
            bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
            bpy.ops.object.mode_set(mode="OBJECT")
        polys = list(o.data.polygons)
        if key == "Skin":
            scale_uv_to(o, [p for p in polys if p.center.z > HEAD_LINE], 1.7)
            scale_uv_to(o, [p for p in polys if p.center.z <= HEAD_LINE], 1.0)
        else:
            scale_uv_to(o, polys, SCALES.get(key, 1.0))
    objs = list(lows.values())
    select_only(objs)
    for o in objs:
        o.data.polygons.foreach_set("select", [True] * len(o.data.polygons))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def imp_retopo(hi, name, quads):
    """pet_kit's retopo_skin with a finer voxel: its wrists are 18 mm across, and the kit's 6.5 mm voxel would pinch them."""
    me = hi.data.copy()
    o = bpy.data.objects.new(name, me)
    GAME.objects.link(o)
    for a in ("paint", "rough", "metal"):
        if o.data.attributes.get(a):
            o.data.attributes.remove(o.data.attributes[a])
    base = o.data.copy()
    res = {"CANCELLED"}
    for size in (0.0028, 0.0026, 0.003, 0.0032, 0.0024):
        o.data = base.copy()
        apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": size, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
        bm.to_mesh(o.data)
        bm.free()
        select_only([o])
        res = bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False, use_preserve_sharp=False, use_preserve_boundary=False, preserve_attributes=False, smooth_normals=False, mode="FACES", target_faces=quads, seed=3)
        print("QUADRIFLOW", size, res, len(o.data.polygons), "faces", flush=True)
        if "FINISHED" in res:
            break
    assert "FINISHED" in res and len(o.data.polygons) < quads * 1.5, "the skin was not retopologised"
    apply_mods(o, [("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_low(pieces, frames, data):
    lows = {"Skin": imp_retopo(pieces["Skin"], N + "SkinLow", SKIN_QUADS), "Moonlet": retopo_skin(pieces["Moonlet"], N + "MoonletLow", MOON_QUADS)}
    P = onto_moonlet(verts(lows["Skin"]), -SOLE_SINK)         # the soles back on the moonlet: the re-mesh rounds them off
    for fr in frames.values():
        # the socket's skin lying level with the eyeball (within a millimetre): into the ball, where the eye hides it (level, they z-fought at the corners)
        c = np.array(tuple(fr.centre))
        d = np.linalg.norm(P - c, axis=1)
        band = np.abs(d - EYE_R) < 0.0012
        P[band] = c + (P[band] - c) / d[band, None] * (EYE_R - 0.0015)
        print("EYE SOCKET", int(band.sum()), "skin vertices tucked into the eye", flush=True)
    set_verts(lows["Skin"], P)
    tree = tree_of(pieces["Skin"])
    gaps = []
    for v in lows["Skin"].data.vertices:
        hit = tree.find_nearest(v.co)
        gaps.append((hit[3], tuple(round(c, 3) for c in v.co)))
    gaps.sort(reverse=True)
    print("SKIN GAP worst", [(round(g, 4), at) for g, at in gaps[:8]], flush=True)
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 20, 12)
        lows["LidU" + tag] = low_lid(fr, True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(fr, False, N + "LidL" + tag + "Low")
    lows["Ears"] = build_ears(N + "EarsLow", GAME, nu=16, nv=5)
    lows["Hands"] = decimated(pieces["Hands"], N + "HandsLow", 900)          # (the fused hands thinned: one closed surface, no faces hidden inside others to bake)
    lows["Tail"] = decimated(pieces["Tail"], N + "TailLow", 420)
    lows["Tuft"] = build_tuft(N + "TuftLow", GAME, sides=6, per=2)
    lows["Fang"] = build_fang(data["tree"], N + "FangLow", GAME, sides=5, per=1)
    lows["Pebbles"] = build_pebbles(N + "PebblesLow", GAME, seg=(10, 7))
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
HIPS_AT = V(0, 0.006, 0.43)
CHEST_AT = V(0, -0.002, 0.488)
HEAD_AT = V(0, -0.004, 0.548)
EAR_AT = V(0.06, 0.005, 0.622)
BROW_AT = V(0.034, -0.068, 0.638)
TAIL_F = (0.0, 0.28, 0.55, 0.8)
SIDES = (("L", 1), ("R", -1))


def tail_bones():
    path = catmull(TAIL, 8)
    return [("Tail%d" % (k + 1), path_at(path, f)) for k, f in enumerate(TAIL_F)]


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Core", C.copy(), "Root"), ("Planet", C.copy(), "Core"), ("Pivot", C.copy(), "Core"),
             ("Hips", HIPS_AT.copy(), "Pivot"), ("Chest", CHEST_AT.copy(), "Hips"), ("Head", HEAD_AT.copy(), "Chest")]
    for tag, side in SIDES:
        bones += [("Ear" + tag, mir(EAR_AT, side), "Head"), ("Brow" + tag, mir(BROW_AT, side), "Head")]
    for tag, fr in frames.items():
        bones += [("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    for tag, side in SIDES:
        bones += [("Arm%s1" % tag, mir(SHOULDER, side), "Chest"), ("Arm%s2" % tag, mir(ELBOW, side), "Arm%s1" % tag), ("Hand" + tag, mir(WRIST, side), "Arm%s2" % tag)]
        bones += [("Leg%s1" % tag, mir(HIP, side), "Hips"), ("Leg%s2" % tag, mir(KNEE, side), "Leg%s1" % tag), ("Foot" + tag, mir(ANKLE, side), "Leg%s2" % tag)]
    parent = "Hips"
    for name, at in tail_bones():
        bones.append((name, at, parent))
        parent = name
    for k in range(len(PEBBLES)):
        bones.append(("Pebble%d" % (k + 1), C.copy(), "Pivot"))         # each at the moonlet's middle: turning it carries its pebble round its orbit
    return armature(bones)


def ramp(f, bones, cuts, w):
    """Shares of a chain of bones at f: each takes over from the last across a window of +-w round its cut."""
    out = {}
    for i, b in enumerate(bones):
        lo = 1.0 if i == 0 else float(smooth(cuts[i - 1] - w, cuts[i - 1] + w, f))
        hi = 1.0 if i == len(bones) - 1 else 1 - float(smooth(cuts[i] - w, cuts[i] + w, f))
        v = lo * hi
        if v > 1e-4:
            out[b] = out.get(b, 0) + v
    return out


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def knot_fracs(path, pts):
    f, _ = nearest_on(path, np.array([tuple(p) for p in pts]))
    return f


def skin_weights(P):
    """The trunk from its seat to its head (hips, chest, head), each arm from the chest to the hand, each leg from the hips to the foot; the brows
    a soft share of the head round each brow ridge."""
    limbs = []
    for tag, side in SIDES:
        ap = arm_path(side)
        af, ad = nearest_on(ap, P)
        ak = knot_fracs(ap, [mir(SHOULDER, side), mir(ELBOW, side), mir(WRIST, side)])
        lp = leg_path(side)
        lf, ld = nearest_on(lp, P)
        lk = knot_fracs(lp, [mir(HIP, side), mir(KNEE, side), mir(ANKLE, side)])
        ff, fd = nearest_on(foot_path(side), P)
        _, bd = nearest_on(brow_path(side), P)
        limbs.append((tag, side, af, ad, ak, lf, ld, lk, ff, fd, bd))
    out = []
    for i, (x, y, z) in enumerate(P):
        w = None
        for tag, side, af, ad, ak, lf, ld, lk, ff, fd, bd in limbs:
            if x * side < 0.004:
                continue
            if ad[i] < 0.02 and af[i] > ak[0] - 0.02 and z > 0.37:
                w = ramp(float(af[i]), ["Chest", "Arm%s1" % tag, "Arm%s2" % tag, "Hand" + tag], (ak[0] + 0.07, ak[1], ak[2] - 0.01), 0.05)
                break
            if (fd[i] < 0.024 and z < 0.375) or (ld[i] < 0.024 and lf[i] > lk[2] - 0.05 and z < 0.375):
                w = {"Foot" + tag: 1.0}
                if z > 0.352:
                    w = blend({"Leg%s2" % tag: 1.0}, w, float(smooth(0.37, 0.352, z)))
                break
            if ld[i] < 0.026 and lf[i] > lk[0] - 0.04 and z < 0.432:
                w = ramp(float(lf[i]), ["Hips", "Leg%s1" % tag, "Leg%s2" % tag, "Foot" + tag], (lk[0] + 0.06, lk[1], lk[2] + 0.02), 0.06)
                # the crotch, near its middle line, stays with the hips: half on a thigh, it stretched six times over when a leg rose
                keep = 1 - float(smooth(0.006, 0.022, abs(x)))
                if keep > 0 and lf[i] < lk[1]:
                    w = blend(w, {"Hips": 1.0}, keep)
                break
        if w is None:
            w = ramp(float(z), ["Hips", "Chest", "Head"], (0.455, 0.543), 0.012)
            for tag, side, af, ad, ak, lf, ld, lk, ff, fd, bd in limbs:
                share = 0.85 * float(1 - smooth(0.004, 0.011, bd[i]))
                if share > 0:
                    w = blend(w, {"Brow" + tag: 1.0}, share)
        out.append(w)
    return out


def smooth_weights(o, weights, rounds=3, share=0.5, keep=("Brow",)):
    """Each vertex's shares averaged with its neighbours' a few rounds: a share that changes from one vertex to the next shows as a jagged crease when the
    joint bends (the crotch did). Shares of bones named in keep stay as they were (the brows' soft patches are drawn as they should be)."""
    nb = [[] for _ in weights]
    for e in o.data.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    w = [dict(x) for x in weights]
    for _ in range(rounds):
        new = []
        for i, mine in enumerate(w):
            if not nb[i]:
                new.append(mine)
                continue
            avg = {}
            for j in nb[i]:
                for k, v in w[j].items():
                    avg[k] = avg.get(k, 0) + v / len(nb[i])
            mixd = {k: v * (1 - share) for k, v in mine.items()}
            for k, v in avg.items():
                mixd[k] = mixd.get(k, 0) + v * share
            for k in list(mixd):
                if k.startswith(keep):
                    mixd[k] = mine.get(k, 0.0)
            total = sum(mixd.values()) or 1.0
            new.append({k: v / total for k, v in mixd.items() if v / total > 1e-3})
        w = new
    return w


def tail_weights(P):
    path = catmull(TAIL, 8)
    f, _ = nearest_on(path, P)
    p, d = tail_end()
    along = (P - np.array(tuple(p))) @ np.array(tuple(d))
    names = ["Hips"] + [n for n, _ in tail_bones()]
    out = []
    for i in range(len(P)):
        if along[i] > -0.008:
            out.append({"Tail4": 1.0})
        else:
            out.append(ramp(float(f[i]), names, (0.06,) + tuple(TAIL_F[1:]), 0.07))
    return out


PIECES = ("Skin", "Moonlet", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Ears", "Hands", "Tail", "Tuft", "Fang", "Pebbles")


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], smooth_weights(lows["Skin"], skin_weights(verts(lows["Skin"]))))
    rigid(lows["Moonlet"], "Planet")
    for tag in "LR":
        rigid(lows["Eye" + tag], "Head")
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    weigh(lows["Ears"], [{"EarL" if k == 1 else "EarR": 1.0} for k in read_tag(lows["Ears"], "side")])
    weigh(lows["Hands"], [{"HandL" if x > 0 else "HandR": 1.0} for x in verts(lows["Hands"])[:, 0]])
    weigh(lows["Tail"], tail_weights(verts(lows["Tail"])))
    rigid(lows["Tuft"], "Head")
    rigid(lows["Fang"], "Head")
    weigh(lows["Pebbles"], [{"Pebble%d" % (k + 1): 1.0} for k in read_tag(lows["Pebbles"], "pebble")])
    rigid(glows["Veins"], "Planet")
    weigh(glows["Glints"], [{"Head": 1.0} for _ in verts(glows["Glints"])])
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses: in the game's axes, the same numbers PetRig's animateGravityImp uses ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))       # Blender's axes to the game's (its own inverse)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def to_game(m3):
    """A turn in Blender's axes as the game's CFrame.Angles(x, y, z)."""
    e = (CM @ m3 @ CM).to_euler("ZYX")
    return (round(e.x, 4), round(e.y, 4), round(e.z, 4))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def mirror_table(table):
    """Its left side's turns onto its right: a mirror keeps a turn about X and flips those about Y and Z; a move flips along X."""
    out = dict(table)
    for bone, v in table.items():
        if bone.endswith("L") or bone[-2:-1] == "L" and bone[-1].isdigit():
            other = bone[:-1] + "R" if bone.endswith("L") else bone[:-2] + "R" + bone[-1]
            mv = v[3] if len(v) > 3 else (0, 0, 0)
            out[other] = (v[0], -v[1], -v[2], (-mv[0], mv[1], mv[2]))
    return out


def solve_arm(side, elbow_dir, wrist_dir, hand_fingers, hand_palm, parent=None):
    """The arm's three turns, in Blender's axes, that point its upper arm along elbow_dir, its forearm along wrist_dir, and its hand's fingers along
    hand_fingers with its palm facing hand_palm (all Blender axes, model space). parent: the trunk's own turn, if it has one: the directions are where
    the arm should end up, and its turns are taken back through the trunk's."""
    if parent is not None:
        pin = parent.inverted()
        elbow_dir, wrist_dir, hand_fingers, hand_palm = pin @ elbow_dir, pin @ wrist_dir, pin @ hand_fingers, pin @ hand_palm
    S, E, W = mir(SHOULDER, side), mir(ELBOW, side), mir(WRIST, side)
    u_rest, f_rest = E - S, W - E
    r1 = u_rest.rotation_difference(elbow_dir.normalized() * u_rest.length).to_matrix()
    r2 = f_rest.rotation_difference(r1.inverted() @ wrist_dir.normalized()).to_matrix()
    _, palm = hand_frame(side)
    rest_f = V(0, 0, -1)                         # at rest its fingers hang down, its palm faces its side (in)
    rest_p = mir(V(-1, 0, 0), side)
    fr_rest = Matrix((rest_f, rest_p, rest_f.cross(rest_p))).transposed()
    tf = hand_fingers.normalized()
    tp = (hand_palm - tf * hand_palm.dot(tf)).normalized()
    fr_want = Matrix((tf, tp, tf.cross(tp))).transposed()
    world = fr_want @ fr_rest.inverted()
    r3 = (r1 @ r2).inverted() @ world
    return r1, r2, r3


def arm_table(side_tag, r1, r2, r3):
    return {"Arm%s1" % side_tag: to_game(r1), "Arm%s2" % side_tag: to_game(r2), "Hand" + side_tag: to_game(r3)}


def akimbo():
    """Fists on its hips, elbows out: the smug stance."""
    r1, r2, r3 = solve_arm(1, V(0.62, 0.12, -0.5), V(-0.5, 0.02, -0.86), V(0.15, 0.55, -0.82), V(-1, 0.1, 0.0))
    return mirror_table(arm_table("L", r1, r2, r3))


WALK = {"swing": 0.36, "lift": 0.75, "tilt": 2.0, "dip": 0.004}       # (searched: planted soles within 1.4 mm of resting on the moonlet)       # tilt: how much more than the leg's swing the foot turns, to lie along the moonlet's curve


def walk(phi, swing=None, lift=None, tilt=None, dip=None):
    """On top of its moonlet, stepping it round under it as on a treadmill: its legs swing at the hips, a knee lifts a foot; a planted foot turns to lie
    along the moonlet's curve (kept level, its toe and heel dug in)."""
    swing = WALK["swing"] if swing is None else swing
    lift = WALK["lift"] if lift is None else lift
    tilt = WALK["tilt"] if tilt is None else tilt
    dip = WALK["dip"] if dip is None else dip
    t = {}
    for tag, lead in (("L", 0.0), ("R", math.pi)):
        sw = math.sin(phi + lead)
        lf = max(0.0, math.cos(phi + lead))
        t["Leg%s1" % tag] = (swing * sw, 0, 0)
        t["Leg%s2" % tag] = (-lift * lf, 0, 0)
        t["Foot" + tag] = (-tilt * swing * sw + lift * lf * 0.6, 0, 0)
        t["Arm%s1" % tag] = (-0.3 * sw, 0, 0)
    t["Hips"] = (0, 0, 0, (0, -dip * math.sin(phi) ** 2, 0))
    return t


SIT = {"down": 0.07, "back": 0.01, "lean": 0.22, "hip": 1.35, "knee": -0.1, "foot": -1.7, "reach": 0.8, "splay": -0.35}      # (searched: seated 2.4 mm in, palms 1 mm off the stone, legs 1 cm clear)


def lounge_arms(lean, reach):
    """Leaning back on its hands, palms flat on the moonlet behind it."""
    parent = Matrix.Rotation(lean, 3, V(1, 0, 0))          # the trunk leans back: (in Blender's axes, about +X tips its top back)
    r1, r2, r3 = solve_arm(1, V(0.3, reach, -0.88), V(0.12, reach * 0.6, -0.95), V(0.1, 1.0, -0.15), V(0, 0, -1), parent=parent)
    return arm_table("L", r1, r2, r3)


def sit(**kw):
    """Sitting on top of its moonlet as on a ball, its legs out in front of it in a V round its belly (its moonlet curves away under them), leaning
    back on its hands: how it rides when its owner flies. (Its legs hung over the front, its feet sank into the moonlet; its knees folded, they met its belly.)"""
    v = dict(SIT, **kw)
    t = lounge_arms(v["lean"], v["reach"])
    t["Hips"] = (v["lean"], 0, 0, (0, -v["down"], v["back"]))
    t["LegL1"] = (v["hip"], 0, v["splay"])          # (a negative turn about Z takes its left leg out to its left)
    t["LegL2"] = (v["knee"], 0, 0)
    t["FootL"] = (v["foot"], 0, 0)
    return mirror_table(t)


STOMP = {"tilt": 0.06, "shift": 0.0, "drop": 0.002}        # (searched: its left sole stays on the moonlet, its right rises 2.7 cm)


def balance_arms(up):
    """Arms out to its sides for balance, elbows bent up a little: ta-da."""
    return mirror_table({"ArmL1": (0.0, 0.0, -0.85 * up), "ArmL2": (0.0, 0.0, -0.55 * up), "HandL": (0.0, 0.0, -0.25 * up)})


def stomp(up, **kw):
    """Its special: a sumo's stamp. Its right leg rises out to its side (a forward knee would meet its belly), its weight over its left foot, its arms
    out for balance; then down."""
    v = dict(STOMP, **kw)
    t = balance_arms(up)
    t["Hips"] = (0, 0, -v["tilt"] * up, (-v["shift"] * up, -v["drop"] * up, 0))
    t["LegR1"] = (0.1 * up, 0, 1.25 * up)
    t["LegR2"] = (0, 0, -1.25 * up)
    t["FootR"] = (0, 0, 0.16 * up)
    t["LegL1"] = (0, 0, v["tilt"] * up)
    t["FootL"] = (0, 0, -v["tilt"] * up)
    return t


def search_stomp(rig, body, dom):
    best = None
    for tilt in (0.06, 0.1, 0.14, 0.18):
        for shift in (0.0, 0.006, 0.012):
            for drop in np.arange(-0.004, 0.0121, 0.002):
                pose(rig, spec(stomp(1.0, tilt=tilt, shift=shift, drop=float(drop))))
                q = quick(body, dom)
                err = abs(q["soleL"] + SOLE_SINK) + 4 * max(0.0, -q["legs"]) - 0.05 * q["soleR"]
                if best is None or err < best[0]:
                    best = (err, tilt, shift, round(float(drop), 4), {k: round(x, 4) for k, x in q.items()})
    return best


def look(yaw, pitch, roll):
    t = akimbo()
    t["Head"] = (pitch, yaw, roll)
    return t


def ears(droop, swing):
    return mirror_table({"EarL": (0, swing, droop)})


def tail(sway, rise):
    return {"Tail%d" % k: (rise, sway, 0) for k in range(1, 5)}


def pose_library(frames, extra):
    out = {name: spec(table) for name, table in extra.items()}
    for tag, fr in frames.items():
        out.setdefault("Blink", {})["LidU" + tag] = (tuple(fr.hinge), -40.0, (0, 0, 0))
        out["Blink"]["LidL" + tag] = (tuple(fr.hinge), 10.0, (0, 0, 0))
    return out


# ---------- checks on a posed mesh ----------
def piece_of_verts(body):
    me = body.data
    a = np.zeros(len(me.polygons), dtype=int)
    me.attributes["piece"].data.foreach_get("value", a)
    out = np.full(len(me.vertices), -1)
    for p in me.polygons:
        for v in p.vertices:
            out[v] = a[p.index]
    return out, a


def posed(body):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    tris = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return co.reshape(-1, 3), tris


def dominant(body):
    """Per vertex: its heaviest bone's name."""
    names = {g.index: g.name for g in body.vertex_groups}
    out = []
    for v in body.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        out.append(names[best.group] if best else "")
    return out


def tree_from(co, tris, faces):
    return BVHTree.FromPolygons([tuple(co[i]) for i in range(len(co))], [tris[f] for f in faces])


def check_pose(body, vpiece, fpiece, dom, centre=None):
    """What a pose can get wrong: a sole off its moonlet or sunk into it, anything else in the moonlet, an arm through the trunk, a hand deep in the hip,
    an ear or the tail through the body, a limb across the pebbles' orbits."""
    co, tris = posed(body)
    c = np.array(tuple(centre or C))
    rad = np.linalg.norm(co - c, axis=1)
    skin = vpiece == PIECES.index("Skin")
    feet = np.array([d.startswith("Foot") for d in dom])
    out = {}
    for tag in "LR":
        sel = skin & np.array([d == "Foot" + tag for d in dom])
        out["sole" + tag] = round(float(rad[sel].min() - R), 4)
    others = np.isin(vpiece, [PIECES.index(k) for k in ("Skin", "Ears", "Hands", "Tail", "Tuft", "Fang", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR")]) & ~feet
    out["in moonlet"] = round(float(min(0.0, (rad[others] - R).min())), 4)
    if out["in moonlet"] < -0.002:
        worst = np.where(others)[0][np.argmin(rad[others])]
        out["deepest"] = (PIECES[vpiece[worst]], dom[worst], tuple(round(float(v), 3) for v in co[worst]))
    skin_faces = [i for i, p in enumerate(fpiece) if p == PIECES.index("Skin")]

    def faces_of(test):
        return [i for i in skin_faces if all(test(dom[v]) for v in tris[i])]
    trunk = faces_of(lambda d: d in ("Hips", "Chest", "Head", "BrowL", "BrowR"))
    forearms = faces_of(lambda d: d.startswith("Arm") and d.endswith("2") or d.startswith("Hand"))
    legs = faces_of(lambda d: d.startswith("Leg") or d.startswith("Foot"))
    t_trunk = tree_from(co, tris, trunk)
    out["forearm x trunk"] = len(tree_from(co, tris, forearms).overlap(t_trunk))
    legL = faces_of(lambda d: d in ("LegL1", "LegL2", "FootL"))
    legR = faces_of(lambda d: d in ("LegR1", "LegR2", "FootR"))
    out["leg x leg"] = len(tree_from(co, tris, legL).overlap(tree_from(co, tris, legR)))
    upper = faces_of(lambda d: d in ("LegL2", "LegR2", "FootL", "FootR"))
    out["shin x trunk"] = len(tree_from(co, tris, upper).overlap(t_trunk))
    t_skin = tree_from(co, tris, skin_faces)
    # the hands: how deep any of it lies inside the skin (a closed surface: counted by rays)
    rig = body.parent
    wrists = [np.array(tuple(rig.pose.bones["Hand" + t].head)) for t in "LR"]
    hands = [i for i in np.where(vpiece == PIECES.index("Hands"))[0] if min(np.linalg.norm(co[i] - w) for w in wrists) > 0.016]      # (the wrist runs into the forearm on purpose)
    deep = 0.0
    for i in hands:
        p = Vector(tuple(co[i]))
        hits, q = 0, p
        for _ in range(40):
            loc, nrm, idx, dist = t_skin.ray_cast(q + V(0.0, 0.0, 1e-5), V(0.0003, 0.0002, 1.0))
            if loc is None:
                break
            hits += 1
            q = loc
        if hits % 2 == 1:
            near = t_skin.find_nearest(p)
            deep = max(deep, near[3])
    out["hand depth"] = round(deep, 4)
    # the ears and the tail: their roots are buried on purpose; count only where one crosses the skin away from its root
    head_c = co[np.array([d == "Head" for d in dom]) & skin].mean(0)
    tail_c = np.array(tuple(rig.pose.bones["Tail1"].head))
    for key, root, reach in (("Ears", head_c, 0.085), ("Tail", tail_c, 0.035)):
        faces = [i for i, p in enumerate(fpiece) if p == PIECES.index(key)]
        pairs = tree_from(co, tris, faces).overlap(t_skin)
        hits = [pr for pr in pairs if np.linalg.norm(co[list(tris[faces[pr[0]]])].mean(0) - root) > reach]
        out[key.lower() + " x skin"] = len(hits)
        out[key.lower() + " rooted"] = len(pairs) - len(hits)          # its root still crossing into the skin: no gap where it joins
    out["tail in moonlet"] = round(float(min(0.0, (rad[vpiece == PIECES.index("Tail")] - R).min())), 4)
    # the pebbles' orbits (round the imp's own middle): how close any of the imp comes to the path of a pebble's surface
    imp = np.isin(vpiece, [PIECES.index(k) for k in ("Skin", "Ears", "Hands", "Tail", "Tuft", "Fang")])
    clear = 9.0
    for k in range(len(PEBBLES)):
        n = orbit_normal(k)
        a = V(math.cos(PEBBLES[k][0]), math.sin(PEBBLES[k][0]), 0)
        b = n.cross(a).normalized()
        ring = np.array([tuple(C + (a * math.cos(t) + b * math.sin(t)) * ORBIT) for t in np.linspace(0, TAU, 96, endpoint=False)])
        pivot = pivot_matrix(body)
        ring = (np.array(pivot.to_3x3()) @ (ring - np.array(tuple(C))).T).T + np.array(tuple(C))
        d = np.min(np.linalg.norm(co[imp][:, None, :] - ring[None, :, :], axis=2))
        clear = min(clear, d - max(PEBBLES[k][1]) - 0.008)
    out["pebble clearance"] = round(float(clear), 4)
    return out


def pivot_matrix(body):
    rig = body.parent
    pb = rig.pose.bones["Pivot"]
    return pb.matrix @ pb.bone.matrix_local.inverted()


def orbit_normal(k):
    """Each pebble's orbit, tilted about the line from the moonlet's middle to where the pebble rests (so it rests on its orbit)."""
    tilt = (math.radians(14), math.radians(-20), math.radians(9))[k]
    a = V(math.cos(PEBBLES[k][0]), math.sin(PEBBLES[k][0]), 0)
    return Matrix.Rotation(tilt, 3, a) @ V(0, 0, 1)


def lowest_under_core(body, vpiece):
    co, _ = posed(body)
    return round(float(C.z - co[:, 2].min()), 4)


GLOW_HEXES = {"Veins": VEIN_HEX, "Glints": "ffffff"}


def game_glows(frames):
    return {"Veins": build_veins(N + "Veins_Glow_" + VEIN_HEX, GAME, sides=5, per=1, stride=2),
            "Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-22, 4, 0.0052, 8), (18, -18, 0.0024, 5)))}


def pose_tables():
    t = {"Rest": {}, "Akimbo": akimbo()}
    for k in range(4):
        t["Walk%d" % k] = walk(k * math.pi / 4)
    t["Sit"] = sit()
    t["StompUp"] = stomp(1.0)
    t["LookUp"] = look(0.7, 0.3, 0.2)
    t["LookDown"] = look(-0.7, -0.28, -0.2)
    t["EarsDroop"] = ears(0.45, 0.25)
    t["EarsPerk"] = ears(-0.3, -0.3)
    t["TailSway"] = tail(0.45, 0.0)
    t["TailOther"] = tail(-0.45, 0.25)
    t["TailDown"] = tail(0.0, -0.15)
    t["Brow"] = {"BrowL": (0, 0, 0, (0, 0.0045, 0)), "BrowR": (0, 0, 0, (0, -0.002, 0))}
    return t


def quick(body, dom, vpiece=None, fpiece=None):
    co, tris = posed(body)
    rad = np.linalg.norm(co - np.array(tuple(C)), axis=1) - R
    out = {}
    skin = np.ones(len(co), dtype=bool) if vpiece is None else vpiece == PIECES.index("Skin")
    for key, test in (("soleL", lambda d: d == "FootL"), ("soleR", lambda d: d == "FootR"), ("legs", lambda d: d.startswith("Leg")), ("seat", lambda d: d == "Hips")):
        sel = np.array([test(d) for d in dom]) & skin
        out[key] = float(rad[sel].min())
    if vpiece is not None:
        out["hands"] = float(rad[vpiece == PIECES.index("Hands")].min())
        skin_faces = [i for i, p in enumerate(fpiece) if p == PIECES.index("Skin")]
        trunk = [i for i in skin_faces if all(dom[v] in ("Hips", "Chest", "Head") for v in tris[i])]
        shins = [i for i in skin_faces if all(dom[v] in ("LegL2", "LegR2", "FootL", "FootR") for v in tris[i])]
        out["shin x trunk"] = len(tree_from(co, tris, shins).overlap(tree_from(co, tris, trunk)))
    return out


def search_walk(rig, body, dom):
    best = None
    for tilt in (1.0, 1.25, 1.5, 1.75, 2.0, 2.25):
        for dip in (0.0, 0.002, 0.004):
            err = 0.0
            for k in range(16):
                phi = k * math.pi / 8
                pose(rig, spec(walk(phi, tilt=tilt, dip=dip)))
                q = quick(body, dom)
                for tag, lead in (("L", 0.0), ("R", math.pi)):
                    g = q["sole" + tag]
                    if math.cos(phi + lead) <= 0:
                        err = max(err, abs(g + SOLE_SINK))
                    else:
                        err = max(err, max(0.0, -SOLE_SINK - g))
                err = max(err, max(0.0, -q["legs"]))
            if best is None or err < best[0]:
                best = (err, tilt, dip)
    return best


def search_sit(rig, body, dom, vpiece, fpiece):
    best = None
    for down in (0.0675, 0.07, 0.0725):
        for hip in (1.25, 1.35):
            for knee in (-0.1, -0.2):
                for foot in (-1.4, -1.7):
                    for arm in np.arange(0.6, 1.01, 0.05):
                        pose(rig, spec(sit(down=down, hip=hip, knee=knee, foot=foot, splay=-0.35, reach=float(arm))))
                        q = quick(body, dom, vpiece, fpiece)
                        pen = max(0.0, -q["legs"]) + max(0.0, -0.0025 - min(q["soleL"], q["soleR"]))
                        err = abs(q["seat"] + 0.002) + 4 * pen + abs(q["hands"] - 0.0) + 0.01 * q["shin x trunk"] - 0.0005 * (-foot)      # (palms on the stone)
                        if best is None or err < best[0]:
                            best = (err, down, hip, knee, foot, round(float(arm), 3), {k: round(v, 4) for k, v in q.items()})
    return best


def game_matrix(v):
    return Matrix.Rotation(v[0], 3, Vector(RX)) @ Matrix.Rotation(v[1], 3, Vector(RY)) @ Matrix.Rotation(v[2], 3, Vector(RZ))


LEG_BONES = ("LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR")


def staged(bone, w, into_sit):
    """Into the seat, staged as the game does it: its legs swing out ahead (done by 0.5), its hips lower after (from 0.4); straight, its feet swept
    through its moonlet on the way down."""
    if not into_sit:
        return w
    if bone in LEG_BONES:
        return min(1.0, w / 0.5)
    if bone == "Hips":
        return float(smooth(0.4, 1.0, w))
    return w


def slerp_tables(a, b, w, into_sit=False):
    """What the game's CFrame:Lerp makes between two stances: each bone's turn slerped (in the game's axes), its move lerped; as a pose spec."""
    out = {}
    for bone in set(a) | set(b):
        w_all = w
        w = staged(bone, w_all, into_sit)
        va = a.get(bone, (0, 0, 0))
        vb = b.get(bone, (0, 0, 0))
        qa = game_matrix(va).to_quaternion()
        qb = game_matrix(vb).to_quaternion()
        q = qa.slerp(qb, w)
        ma = Vector(va[3] if len(va) > 3 else (0, 0, 0))
        mb = Vector(vb[3] if len(vb) > 3 else (0, 0, 0))
        mv = ma.lerp(mb, w)
        axis, angle = q.to_axis_angle()
        out[bone] = (tuple(axis), math.degrees(angle), (-mv.x, mv.z, mv.y))
        w = w_all
    return out


TRANSITIONS = (("Akimbo", "Walk2"), ("Akimbo", "Sit"), ("Akimbo", "StompUp"), ("Walk2", "Sit"), ("Walk2", "StompUp"), ("Walk0", "Sit"), ("Walk1", "Sit"), ("Walk3", "Sit"))      # (it stands before it stamps: never the seat to the stamp)


def check_transitions(rig, body, vpiece, fpiece, dom):
    tables = pose_tables()
    for a, b in TRANSITIONS:
        worst = {}
        for k in range(11):
            w = k / 10
            pose(rig, slerp_tables(tables[a], tables[b], w, into_sit=(b == "Sit")))
            r = check_pose(body, vpiece, fpiece, dom)
            for key in ("in moonlet", "forearm x trunk", "leg x leg", "shin x trunk", "hand depth", "ears x skin", "tail x skin"):
                v = r[key]
                if key == "in moonlet":
                    worst[key] = min(worst.get(key, 0.0), v)
                else:
                    worst[key] = max(worst.get(key, 0), v)
            worst["soles"] = min(worst.get("soles", 9.0), r["soleL"], r["soleR"])
        print("TRANSITION", a, "->", b, worst, flush=True)


if __name__ == "__main__" and STAGE == "tables":
    # the numbers PetRig's animateGravityImp uses, in the game's axes (x, y, z turns; a move in metres)
    for name, table in (("AKIMBO", akimbo()), ("SIT", sit()), ("STOMP", stomp(1.0)), ("BALANCE", balance_arms(1.0))):
        print("TABLE", name, {k: tuple(round(float(x), 4) for x in v[:3]) + ((tuple(round(float(m), 4) for m in v[3]),) if len(v) > 3 else ()) for k, v in table.items()}, flush=True)
    for tag, fr in eye_frames().items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for k in range(len(PEBBLES)):
        n = orbit_normal(k)
        print("ORBIT", k + 1, "normal game axes", (round(-n.x, 4), round(n.z, 4), round(n.y, 4)), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    if STAGE == "all":
        imp_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.45, 0.34, 0.6, 1), far=("Skin", "Moonlet"), reach=(0.003, 0.008),
                 far_reach=(0.005, 0.014), reaches={"Moonlet": (0.008, 0.02), "Fang": (0.002, 0.005), "Tuft": (0.003, 0.007), "Hands": (0.001, 0.0025), "Ears": (0.001, 0.0025)})      # (fingertips and ear tips are 3 mm thick: a longer reach crossed to their other side)
    else:
        clay = bpy.data.materials.new("clay")
        g = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = game_glows(frames)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    vpiece, fpiece = piece_of_verts(body)
    dom = dominant(body)
    if "search" in ARGS:
        if "walk" in ARGS:
            print("SEARCH walk", search_walk(rig, body, dom), flush=True)
        print("SEARCH sit", search_sit(rig, body, dom, vpiece, fpiece), flush=True)
        if "stomp" in ARGS:
            print("SEARCH stomp", search_stomp(rig, body, dom), flush=True)
    tables = pose_tables()
    for name, table in tables.items():
        pose(rig, spec(table))
        print("POSE", name, check_pose(body, vpiece, fpiece, dom), flush=True)
        if name != "Rest":
            print("TABLE", name, {k: tuple(round(x, 4) for x in v[:3]) for k, v in table.items()}, flush=True)
        shots(os.path.join(REVIEW, "pose" + name), [(0.62, -0.72, 0.3, 1.6, VIEW_AT), (1, -0.05, 0.1, 1.6, VIEW_AT), (0, -1, 0.1, 1.6, VIEW_AT)], target=VIEW_AT, size=480)
        if name in ("Sit", "StompUp", "Walk2"):
            shots(os.path.join(REVIEW, "close" + name), [(0.3, -1, -0.25, 0.42, (0, -0.02, 0.37)), (1, -0.3, 0.0, 0.42, (0, -0.02, 0.37)), (-0.4, 0.9, -0.2, 0.42, (0, 0.0, 0.37))], size=480)
    if "transitions" in ARGS:
        check_transitions(rig, body, vpiece, fpiece, dom)
    for a in range(0, 181, 15):
        pose(rig, spec({"Pivot": (-math.radians(a), 0, 0)}))
        print("UNDER", a, lowest_under_core(body, vpiece), flush=True)
    pose(rig, spec({"Pivot": (-math.pi, math.pi, 0)}))
    print("POSE Upside", check_pose(body, vpiece, fpiece, dom), flush=True)
    shots(os.path.join(REVIEW, "poseUpside"), [(0.62, -0.72, 0.3, 2.0, (0, 0, 0.1))], size=480)
    lib = pose_library(frames, {k: v for k, v in tables.items() if k != "Rest"})
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    pose(rig, {})
    if STAGE == "all":
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 1.6, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

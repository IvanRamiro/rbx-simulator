"""The Comet Stag (Legendary, Comets; Celestial Egg, also in the Heavenly Throne Egg): "It crosses the sky once in a lifetime and leaves a trail people name
their children after."

A powerful stag whose antlers are comet tails (the owner's choice, 2026-11-09), in a design language of its own: speed, and light streaming back. A red deer's
build, a deep chest and a thick, shaggy neck ruff, carried high on long legs; a long, fine head with big dark eyes and large leaf-shaped ears. Its antlers do
not branch up: they sweep straight back from the crown like a comet's two tails, each a broad palm (the dust tail, white going to gold, streaked lengthwise)
with a straighter, finer tine above it (the ion tail, white going to vivid blue) and a short brow tine forward. A comet's nucleus glows on its brow between
them. Its hide is deep night-blue, with pale icy dapples drawn out backward along its back and flanks as if streaming in the wind of its own speed; a
shaggy blue-grey ruff, a pale muzzle and throat, a white rump patch round a short tail, icy silver hooves.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/comet_stag.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, hooves on z = 0. +X is its left. The maps go to assets/pets/CelestialEgg/.

What touches what: body, neck, head, legs, hooves and tail are one fused skin; the eyes sit in their sockets under their lids; the ears and the antlers are
their own pieces set into the head; the nucleus (a glow piece) is half sunk in the brow.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (Matrix and Vector: the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "CometStag"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- colours: night, ice and the comet's light ----------
HIDE, HIDE_DARK, HIDE_SHEEN = rgb(34, 44, 92), rgb(18, 22, 50), rgb(70, 90, 156)
BELLY, RUFF, RUFF_TIP = rgb(80, 92, 140), rgb(96, 110, 156), rgb(150, 166, 206)
PALE, RUMP = rgb(192, 204, 230), rgb(226, 232, 246)
DAPPLE = rgb(206, 228, 255)
HOOF, HOOF_LIT, NOSE_COL, MOUTH = rgb(150, 170, 200), rgb(222, 234, 250), rgb(30, 32, 48), rgb(14, 14, 24)
EAR_IN = rgb(156, 168, 206)
ICE_CORE, DUST, DUST_DEEP, ION, ION_DEEP = rgb(238, 246, 255), rgb(252, 226, 160), rgb(236, 176, 92), rgb(120, 196, 255), rgb(56, 120, 250)
GLINT_HEX = "ffffff"
NUCLEUS_HEX = "eaf6ff"

# ---------- the frame of it ----------
HEAD_SHIFT = V(0, -0.0, -0.15)          # the head lower and on a shorter neck than it was first laid out


def hv(x, y, z):
    """A point on the head, as laid out, moved with it."""
    return V(x, y, z) + HEAD_SHIFT


SPINE = [V(0, 0.3, 0.55), V(0, 0.18, 0.58), V(0, 0.06, 0.575), V(0, -0.06, 0.58), V(0, -0.16, 0.61), V(0, -0.24, 0.65)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.108), (0.15, 0.13), (0.4, 0.118), (0.65, 0.128), (0.85, 0.136), (1, 0.12))      # half-widths, rump to withers
BODY_H = ((0, 0.105), (0.15, 0.13), (0.4, 0.128), (0.65, 0.148), (0.85, 0.162), (1, 0.142))     # half-heights
BODY_DROP = ((0, 0.0), (0.15, 0.01), (0.4, 0.028), (0.65, 0.04), (0.85, 0.045), (1, 0.03))     # the loft's centre below the spine: a deep chest
NECK = catmull([V(0, -0.24, 0.65), V(0, -0.32, 0.74), V(0, -0.375, 0.83), V(0, -0.41, 0.9)], 10)
NECK_R = ((0, 0.13), (0.5, 0.1), (1, 0.074))
HEAD = hv(0, -0.42, 1.07)
HEAD_R = (0.066, 0.08, 0.064)
MUZZLE = [hv(0, -0.45, 1.06), hv(0, -0.52, 1.027), hv(0, -0.58, 0.995)]
JAW = [hv(0, -0.44, 1.03), hv(0, -0.5, 1.0), hv(0, -0.56, 0.972)]
TAIL = catmull([V(0, 0.35, 0.57), V(0, 0.385, 0.53), V(0, 0.4, 0.49)], 8)
FRONT = [V(0.078, -0.17, 0.53), V(0.09, -0.14, 0.37), V(0.08, -0.16, 0.21), V(0.076, -0.17, 0.08), V(0.076, -0.18, 0.033)]
HIND = [V(0.086, 0.2, 0.52), V(0.096, 0.12, 0.37), V(0.084, 0.25, 0.23), V(0.079, 0.23, 0.08), V(0.079, 0.22, 0.033)]
FRONT_R = [0.08, 0.056, 0.034, 0.03, 0.032]
HIND_R = [0.106, 0.068, 0.036, 0.03, 0.032]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.018
EYE_C = hv(0.046, -0.47, 1.078)
EYE_AXIS = V(0.78, -0.6, 0.12).normalized()       # a deer's eyes look out to the sides
LID_UP, LID_LOW = (40.0, 120.0, 0.0025), (-40.0, -128.0, 0.0021)      # wide, calm, watchful
LID_TILT = 6.0
BLINK_U, BLINK_L = 58.0, 26.0
IRIS = 0.95                              # on the eye's face: a deer's eye is nearly all iris
PUPIL_W, PUPIL_H = 0.4, 0.16             # a horizontal pupil
NUCLEUS_C, NUCLEUS_R = hv(0, -0.452, 1.116), (0.019, 0.025, 0.013)
# the antlers (its left; mirrored): the palm (the dust tail), the tine above it (the ion tail), the brow tine
PALM = [hv(0.036, -0.41, 1.118), hv(0.065, -0.4, 1.21), hv(0.115, -0.31, 1.31), hv(0.175, -0.13, 1.375), hv(0.235, 0.1, 1.39), hv(0.285, 0.33, 1.35)]
PALM_R = ((0, 0.019), (0.25, 0.03), (0.55, 0.052), (0.8, 0.038), (1, 0.006))
ION_TINE = [hv(0.08, -0.35, 1.27), hv(0.088, -0.19, 1.41), hv(0.1, 0.05, 1.5), hv(0.112, 0.27, 1.55)]
ION_TINE_R = ((0, 0.013), (0.5, 0.0095), (1, 0.0035))
BROW = [hv(0.054, -0.405, 1.17), hv(0.078, -0.465, 1.2), hv(0.09, -0.515, 1.24)]
BROW_R = ((0, 0.012), (1, 0.0035))


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def path_frames(path):
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0) - tan * tan.x
        side = side.normalized() if side.length > 1e-5 else V(1, 0, 0)
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def loft(m, path, w_fn, h_fn, drop_fn=None, nt=48):
    """Ellipses along a path: w across, h up; drop moves each ring's centre down."""
    fr = path_frames(path)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        w, h = w_fn(f), h_fn(f)
        c = p - V(0, 0, drop_fn(f) if drop_fn else 0.0)
        rings.append([m.bm.verts.new(c + side * (w * math.cos(TAU * k / nt)) + up * (h * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.005, -0.01), (0.1, 0.08, 0.1))                          # the rump
    core.ball(V(0, -0.33, 0.67), (0.105, 0.1, 0.13))                                       # the ruff: thick and shaggy, hanging under the neck
    core.ball(V(0, -0.36, 0.61), (0.07, 0.07, 0.07))                                       # the ruff's beard, its lowest point
    core.ball(V(0, -0.26, 0.55), (0.092, 0.075, 0.1))                                      # the breast
    for side in (1, -1):
        core.ball(V(side * 0.075, -0.17, 0.55), (0.062, 0.09, 0.098))                      # the shoulder
        core.ball(V(side * 0.085, 0.19, 0.51), (0.08, 0.11, 0.112))                        # the haunch
        core.ball(V(side * 0.05, -0.3, 0.72), (0.06, 0.08, 0.1))                          # the ruff over the sides of the neck
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 40, 28)                                                         # the cranium
    fine.tube(catmull(MUZZLE, 6), lambda f: 0.054 - 0.016 * f, sides=28, flat=0.9)         # the long face
    fine.ball(MUZZLE[-1] + V(0, -0.004, -0.002), (0.034, 0.024, 0.031))                     # the nose
    fine.tube(catmull(JAW, 6), lambda f: 0.038 - 0.011 * f, sides=24, flat=0.95)             # the lower jaw
    for side in (1, -1):
        fine.ball(hv(side * 0.034, -0.46, 1.058), (0.03, 0.044, 0.034))                      # the cheek
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(hv(side * 0.038, -0.465, 1.1), (0.024, 0.028, 0.015))                    # the brow: the lids' hidden edges stay under it
        fine.ball(mir(PALM[0], side) + V(0, 0, -0.006), (0.019, 0.019, 0.016), 20, 12)      # the pedicle the antler grows from
    for key, side, knots, radii in LEGS:
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.9)
        hoof = mir(knots[4], side)
        fine.ball(hoof + V(0, -0.006, -0.002), (0.034, 0.04, 0.031), 20, 14)               # the hoof, cloven in paint
    fine.tube(TAIL, lambda f: 0.034 - 0.008 * f, sides=20)                                   # the short tail
    fine.ball(TAIL[-1], (0.026, 0.026, 0.028), 16, 10)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0035, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- ears ----------
EAR = {"front": hv(0.044, -0.42, 1.102), "back": hv(0.066, -0.394, 1.086), "height": 0.094}


def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    want = V(side * 0.85, 0.3, 0.45)                       # a deer's ears stand out to the sides
    up = (want - along * want.dot(along)).normalized()
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n          # facing forward
    return A, B, C, along, up, n


def ear_point(side):
    """A large leaf-shaped ear: its base along the head, its rim a tall arc to a rounded tip; u from the base to the rim, v across. The rim reaches a little
    past the base at both ends, so no row of the sheet is drawn to a point."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        s = math.sin(math.pi * v)
        rim = C + along * (-math.cos(math.pi * v) * a * 1.25) + up * (s ** 0.8 * EAR["height"] + 0.008)
        p = base.lerp(rim, u)
        cup = 0.012 * s * math.sin(math.pi * min(1.0, u * 1.1))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return 0.007 * (1 - u) ** 0.7 + 0.0025


def sheet_uv(nu, nv):
    uu, vv = [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            uu += [i / nu, i / nu]
            vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def build_ear(side, name):
    """Night-blue behind, the hollow a pale blue-grey with fine hair, a dark rim."""
    nu, nv = 60, 60
    o = sheet_hi(ear_point(side), ear_thick, nu, nv, name, lambda u, v: np.broadcast_to(HIDE, (len(u), 3)), lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    uu, vv = sheet_uv(nu, nv)
    Nn = normals(o)
    _, _, _, _, _, n = ear_frame(side)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(n)))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.6)
    hair = 0.85 + 0.15 * np.sin(vv * 80.0 + uu * 6.0)
    hollow = mix(EAR_IN * 0.6, EAR_IN, smooth(0.04, 0.22, edge))[:, :] * hair[:, None]
    col = mix(np.broadcast_to(HIDE, (len(uu), 3)), hollow, inside * smooth(0.025, 0.06, edge))
    col = mix(col, HIDE_DARK, 1 - smooth(0.008, 0.03, edge))
    paint(o, col, np.full(len(uu), 0.62), np.zeros(len(uu)))
    return o


# ---------- the antlers: comet tails ----------
def antler_parts(side):
    """Each part: its knots, radius profile, how flat it is across (thin side to side), and its kind (0 palm, 1 ion tine, 2 brow tine)."""
    return [([mir(p, side) for p in PALM], PALM_R, 0.32, 0), ([mir(p, side) for p in ION_TINE], ION_TINE_R, 0.7, 1), ([mir(p, side) for p in BROW], BROW_R, 0.85, 2)]


def make_tags(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def build_antlers(name, coll, sides=28, per=12):
    """Each vertex carries its part ("kind"), how far along it ("along") and how far round it ("round": 0 at the top edge, 1 at the bottom)."""
    m = Mesh()
    bm = m.bm
    make_tags(bm, ints=("kind",), floats=("along", "round"))
    kl, al, rl = bm.verts.layers.int["kind"], bm.verts.layers.float["along"], bm.verts.layers.float["round"]
    for side in (1, -1):
        for knots, radii, flat, kind in antler_parts(side):
            path = catmull(knots, per if kind == 0 else max(4, per // 2))
            before = set(bm.verts)
            m.tube(path, lambda f, r=radii: prof(r, f), sides=sides, flat=flat, plane=V(1, 0, 0))
            new = [v for v in bm.verts if v not in before]
            f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
            for v, ff in zip(new, f):
                p = path_at(path, float(ff))
                v[kl], v[al] = kind, float(ff)
                v[rl] = float(0.5 - 0.5 * max(-1.0, min(1.0, (v.co - p).normalized().z if (v.co - p).length > 1e-6 else 0.0)))
    return m.finish(name, coll)


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


def paint_antlers(o):
    """The palm: icy white at the root (the comet's head) going to gold along it, streaked lengthwise; the ion tine white going to vivid blue; the brow tine
    white going to pale blue."""
    P = verts(o)
    kind, along, rnd = read_tag(o, "kind"), read_tag(o, "along"), read_tag(o, "round")
    streak = 0.5 + 0.5 * np.sin((rnd * 9.0 + along * 2.0) * math.pi)          # lengthwise striations across its face
    fine = fbm(P * np.array([30.0, 8.0, 30.0]), 1.0, 3, 7)
    palm = mix(np.broadcast_to(ICE_CORE, (len(P), 3)), DUST, smooth(0.08, 0.5, along))
    palm = mix(palm, DUST_DEEP, (smooth(0.5, 1.0, along) * (0.55 + 0.45 * rnd)))
    palm = palm * (0.8 + 0.2 * streak * smooth(0.12, 0.35, along) + 0.1 * (fine - 0.5))[:, None]
    ion = mix(np.broadcast_to(ICE_CORE, (len(P), 3)), ION, smooth(0.1, 0.55, along))
    ion = mix(ion, ION_DEEP, smooth(0.55, 1.0, along))
    brow = mix(np.broadcast_to(ICE_CORE, (len(P), 3)), ION * 1.1, smooth(0.3, 1.0, along))
    col = np.where((kind == 0)[:, None], palm, np.where((kind == 1)[:, None], ion, brow))
    paint(o, np.clip(col, 0, 1), np.full(len(P), 0.26), np.zeros(len(P)))


def build_nucleus(name, coll, seg=32, rings=20):
    m = Mesh()
    m.ball(NUCLEUS_C, NUCLEUS_R, seg, rings)
    return m.finish(name, coll)


# ---------- paint ----------
def cells(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point, and the nearest cell's own random number."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    own = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                d1 = np.where(nearer, d, d1)
    return d1, d2, own


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    head = 1 - smooth(0.08, 0.12, np.linalg.norm(P - np.array(tuple(HEAD + V(0, -0.06, -0.02))), axis=1))
    leg = smooth(0.4, 0.32, z) * (1 - head)
    # short sleek hair, lying back along the body and down the legs; a cool sheen where it faces up
    hair_body = fbm(P * np.array([170.0, 40.0, 170.0]), 1.0, 3, 3)
    hair_leg = fbm(P * np.array([170.0, 170.0, 40.0]), 1.0, 3, 5)
    fur = hair_body * (1 - leg) + hair_leg * leg
    col = mix(HIDE * 0.85, HIDE, smooth(0.3, 0.7, fur))
    col = mix(col, HIDE_SHEEN, smooth(0.3, 0.95, Nn[:, 2]) * 0.4)
    col = mix(col, HIDE_DARK, leg * smooth(0.3, 0.08, z) * 0.7)                       # darker down the legs
    under = smooth(-0.2, -0.7, Nn[:, 2]) * (1 - head) * (1 - leg)
    col = mix(col, BELLY, under * 0.85)
    # the ruff: shaggy, paler, round the lower neck and over the breast
    ruff_d = np.linalg.norm((P - np.array((0, -0.32, 0.68))) / np.array((0.15, 0.13, 0.17)), axis=1)
    ruff = (1 - smooth(0.8, 1.15, ruff_d)) * (1 - head)
    shag = fbm(P * np.array([60.0, 60.0, 22.0]), 1.0, 3, 9)
    col = mix(col, mix(RUFF, RUFF_TIP, smooth(0.45, 0.8, shag)), ruff * 0.9)
    # the face: a pale muzzle and chin, pale round the eyes
    muzzle_f, muzzle_d = nearest_on(catmull(MUZZLE, 6), P)
    face_pale = (1 - smooth(0.035, 0.05, muzzle_d)) * smooth(0.25, 0.75, muzzle_f) * smooth(0.4, -0.3, Nn[:, 2])
    col = mix(col, PALE, np.clip(face_pale, 0, 1) * 0.85)
    throat = smooth(0.55, 0.85, (Nn * np.array((0, -0.7, -0.7))).sum(1)) * smooth(-0.38, -0.46, y) * smooth(0.79, 0.87, z)
    col = mix(col, PALE, np.clip(throat, 0, 1) * 0.8)
    rings = np.zeros(len(P))
    for side in (1, -1):
        r = np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1)
        rings = np.maximum(rings, smooth(EYE_R * 1.7, EYE_R * 1.3, r) * (1 - smooth(EYE_R * 1.3, EYE_R * 1.1, r)))
    col = mix(col, PALE, rings * 0.7)
    # the rump patch: white round the short tail; the tail dark above
    rump = (1 - smooth(0.055, 0.09, np.linalg.norm((P - np.array((0, 0.365, 0.53))) / np.array((1.0, 0.8, 1.2)), axis=1)))
    tail_top = (1 - smooth(0.022, 0.038, np.linalg.norm(P - np.array((0, 0.38, 0.55)), axis=1))) * smooth(0.1, 0.6, Nn[:, 1] * 0.3 + Nn[:, 2])
    col = mix(col, RUMP, rump)
    col = mix(col, HIDE_DARK, tail_top * 0.9)
    # the dapples: pale icy spots along the back and flanks, drawn out backward as if streaming in the wind of its speed; thicker toward the rump
    Q = P * np.array([1.0, 0.32, 1.0])
    d1, d2, own = cells(Q, 34.0, 11)
    spot = 1 - smooth(0.2, 0.3, d1 + 0.1 * (own - 0.5))
    band = smooth(-0.05, 0.4, Nn[:, 2]) * smooth(0.4, 0.48, z) * smooth(-0.22, -0.12, y) * (1 - ruff) * (1 - head) * (1 - leg)
    density = (own > 0.35 - 0.35 * smooth(-0.15, 0.25, y)).astype(float)
    col = mix(col, DAPPLE, spot * band * density * 0.85)
    # the hooves: icy silver, cloven
    hooves = np.zeros(len(P))
    cleft = np.zeros(len(P))
    for key, side, knots, radii in LEGS:
        c = mir(knots[4], side)
        near = (np.linalg.norm(P[:, [0, 1]] - np.array((c.x, c.y)), axis=1) < 0.05) * (z < 0.05)
        hooves = np.maximum(hooves, near * smooth(0.052, 0.042, z))
        cleft = np.maximum(cleft, near * (1 - smooth(0.0015, 0.0035, np.abs(x - c.x))) * (y < c.y))
    col = mix(col, mix(HOOF, HOOF_LIT, smooth(0.0, 0.8, Nn[:, 2] * 0.3 + 0.5)), hooves)
    col = mix(col, HIDE_DARK * 0.5, cleft)
    # the nose and mouth
    nose = (1 - smooth(0.018, 0.026, np.linalg.norm((P - np.array(tuple(MUZZLE[-1] + V(0, -0.012, 0.006)))) / np.array((1.0, 0.7, 1.0)), axis=1)))
    col = mix(col, NOSE_COL, nose)
    nost = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(hv(side * 0.011, -0.6, 0.997)))
        nost = np.maximum(nost, 1 - smooth(0.0028, 0.0048, np.linalg.norm((P - c) * np.array([1.0, 0.6, 1.3]), axis=1)))
    fy, fz = y - HEAD_SHIFT.y, z - HEAD_SHIFT.z          # as laid out
    lip = (1 - smooth(0.0012, 0.003, np.abs(fz - (0.979 + 0.25 * (fy + 0.58))))) * (fy < -0.52) * (np.abs(x) < 0.034)
    mouth = np.clip(nost + lip, 0, 1)
    col = mix(col, MOUTH, mouth)
    relief = (fur - 0.5) * 0.0005 + (shag - 0.5) * 0.0025 * ruff - 0.0009 * mouth
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.58 - 0.12 * smooth(0.45, 0.8, fur) - 0.3 * hooves - 0.25 * nose, np.zeros(len(P)))


def eye_paint(o, fr):
    """A deer's eye, nearly all iris: deep blue-black with a ring of icy silver at its rim, a horizontal pupil, fine fibres."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(10, 12, 22), (len(px), 3)).copy()
    iris = mix(rgb(30, 42, 86), rgb(14, 18, 40), smooth(0.2, 0.7, r))
    iris = mix(iris, rgb(170, 206, 240), smooth(IRIS - 0.22, IRIS - 0.06, r) * (1 - smooth(IRIS - 0.04, IRIS, r)) * 0.85)
    azi = np.arctan2(py, px)
    iris = iris * (0.85 + 0.15 * np.sin(azi * 40 + np.sin(azi * 6) * 2))[:, None]
    iris = mix(iris, iris * 0.7, smooth(-0.2, 0.8, py / IRIS) * 0.4)
    col = mix(col, iris, 1 - smooth(IRIS - 0.02, IRIS + 0.01, r))
    pupil = np.where(front, (px / PUPIL_W) ** 2 + (py / PUPIL_H) ** 2, 9.0)
    col = mix(col, rgb(2, 2, 6), 1 - smooth(0.8, 1.1, pupil))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


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


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, HIDE, HIDE_DARK * 0.4)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, HIDE, HIDE_DARK * 0.5, lower_share=0.7)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Antlers"] = build_antlers(N + "AntlersHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0034, 12), (22, -18, 0.0016, 8))),
             "Nucleus": build_nucleus(N + "Nucleus_Glow_" + NUCLEUS_HEX, HI)}
    if not clay:
        paint_skin(skin)
        paint_antlers(pieces["Antlers"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.0, 0.6)
FACE_AT = tuple(hv(0, -0.5, 1.06))
EXTRA = [(0, -1, 0.05, 0.75, FACE_AT), (0.62, -0.75, 0.2, 0.75, FACE_AT), (1, -0.12, 0.08, 0.75, FACE_AT), (0.4, -0.9, 0.1, 0.35, tuple(EYE_C)),
         (0.8, 0.2, 0.5, 1.7, (0.1, -0.05, 1.2)), (1, -0.1, 0.05, 1.5, (0, -0.1, 0.35))]

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
        mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=4.0, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3800
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "EarL": 1.3, "EarR": 1.3, "Antlers": 1.4}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 9, 8, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Antlers"] = build_antlers(N + "AntlersLow", GAME, 10, 6)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[4], "Body"), ("Neck1", NECK[0], "Chest"),
               ("Neck2", path_at(NECK, 0.5), "Neck1"), ("Head", NECK[-1], "Neck2"))
TAIL_NAMES = ["Tail1", "Tail2"]
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Hoof" + key] for key, _, _, _ in LEGS}


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots):
    fs = [k / (len(knots) - 1) for k in range(len(knots))]
    return tuple((fs[k] + fs[k + 1]) / 2 for k in range(4))


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    bones += [("Tail1", TAIL[0].copy(), "Hips"), ("Tail2", path_at(TAIL, 0.5), "Tail1")]
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, C, along, up, n = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, C.copy(), "Head")]
    fs = [k / (len(FRONT) - 1) for k in range(len(FRONT))]
    for key, side, knots, _ in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        line = leg_line(knots, side)
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, path_at(line, fs[k]), parent))
            parent = name
    return armature(bones)


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.03,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (HEAD + V(0, -0.06, -0.02), (0.085, 0.13, 0.085))


def body_weights(P):
    """The skin's weights at any points: the trunk (hips to head), the head, the tail, the legs; a hoof wholly its hoof's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for key, side, knots_l, radii in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P)
        legs.append((key, side, knots_l, radii, f, d))
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        owner = None
        for key, side, knots_l, radii, f, d in legs:
            if (Vector(P[i]) - mir(knots_l[4], side)).length < 0.06 and z < 0.06:
                owner = "Hoof" + key
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
        share = (1 - float(smooth(0.045, 0.065, td[i]))) * float(smooth(0.0, 0.25, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, (0.0, 0.25, 0.75), float(tf[i])), share)
        for key, side, knots_l, radii, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.014
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            mm *= float(smooth(0.015, 0.08, x * side)) if z > knots_l[1].z - 0.02 else 1.0
            if mm > 0:
                w = blend(w, chain_weight(LEG_NAMES[key], leg_mids(knots_l), float(f[i])), mm)
        out.append(w)
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Antlers"], "Head")
    rigid(glows["Nucleus"], "Head")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateCometStag uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def legs4(f, b):
    out = {}
    for side in "LR":
        for k in range(3):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, 0)
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, 0)
    return out


# its stances, searched in Blender against the ground and for torn skin (see the vault): the same numbers as PetRig's STAG_* tables
REAR = {"Hips": (0, 0, 0, (0, -0.061, 0)), "Body": (0.573, 0, 0), "Neck1": (-0.15, 0, 0), "Head": (-0.038, 0, 0), **legs4((-0.067, -0.169, 0.906), (-0.249, -0.224, 0.02))}
LIE = {"Hips": (0, 0, 0, (0, -0.311, 0)), "Body": (-0.171, 0, 0), "Head": (0.27, 0, 0), **legs4((0.569, -2.153, -0.182), (-0.2, -1.438, 0.638))}
LEAP = {"Body": (-0.039, 0, 0), "Head": (0.2, 0, 0), "Tail1": (0.3, 0, 0), **legs4((0.679, -1.558, 0.307), (-0.39, 0.255, 0.091))}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    stride = {"LegFL1": (0.45, 0, 0), "LegFL2": (-0.7, 0, 0), "LegFR1": (-0.35, 0, 0), "LegBL1": (-0.4, 0, 0), "LegBR1": (0.35, 0, 0), "LegBR2": (0.5, 0, 0)}
    paw = {"LegFL1": (0.55, 0, 0), "LegFL2": (-1.1, 0, 0), "LegFL3": (0.3, 0, 0), "Neck1": (0.1, 0, 0), "Head": (0.3, 0, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-7, -5), "Stride": spec(stride), "Paw": spec(paw), "Rear": spec(REAR), "Lie": spec(LIE), "Leap": spec(LEAP),
            "Look": spec({"Neck2": (0.15, 0.35, 0), "Head": (0.2, 0.45, 0.15)}), "Toss": spec({"Neck1": (-0.25, 0, 0), "Neck2": (-0.2, 0, 0), "Head": (-0.35, 0, 0)}),
            "Ears": spec({"EarL": (-0.4, 0.3, 0), "EarR": (-0.4, -0.3, 0)})}


def lowest_of(body, parts):
    """The lowest point of the posed mesh among the vertices each set of bones carries."""
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, bones in parts.items():
        idx = {groups[b] for b in bones if b in groups}
        mine = [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)]
        out[name] = round(float(co[mine, 2].min()), 4) if mine else None
    return out


GROUND_PARTS = {"FrontHooves": ("HoofFL", "HoofFR"), "HindHooves": ("HoofBL", "HoofBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",), "Head": ("Head",)}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.38 and p.center.z > 0.82, 2.0), (None, 1.0)], SCALES, margin=0.009)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.2, 0.24, 0.4, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.01, 0.025))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in ("Glints", "Nucleus"):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0034, 10), (22, -18, 0.0016, 6))),
             "Nucleus": build_nucleus(N + "Nucleus_Glow_" + NUCLEUS_HEX, GAME, 16, 10)}
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
    for name in ("Hips", "Head", "Tail2"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    nc = sum((Vector(v.co) for v in glows["Nucleus"].data.vertices), Vector()) / len(glows["Nucleus"].data.vertices)
    print("NUCLEUS game axes", (round(-nc.x, 4), round(nc.z, 4), round(nc.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=4.0, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Rear", "Lie", "Leap", "Paw"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 4.0, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 4.0, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.8, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Stride", side), ("Paw", side), ("Rear", side), ("Lie", wide), ("Leap", side), ("Look", face), ("Toss", side), ("Ears", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 4.0, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

"""The Celestial Snow Leopard (Epic, Ice and celestial energy; Celestial Egg, also in the Heavenly Throne Egg): "It stalks the high snow where the sky begins.
Its pawprints stay frozen long after the mountain thaws."

A grown snow leopard, a majestic hunter (the owner's choice, 2026-11-09), in a design language of its own: the high snow under the night sky. A long, low
body with a deep chest and heavy shoulders; a small head carried low on a short, thick neck, a domed forehead, a short muzzle and a thick cheek ruff;
small rounded ears set wide; huge paws; a very long tail of even girth, thick with fur all the way, curling up at its tip. Smoky ice-white fur with a
faint blue frost sheen and a white belly; dark open rosettes with smoky centres over the body and tail, solid spots on the head and legs, a dark tail
tip; a few rosettes along its back hold faint ice-blue stars. Pale ice eyes going to aquamarine-silver round a round pupil, rimmed dark; a pink-grey
nose; frosted white whiskers; icy blue-grey paw pads.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/celestial_snow_leopard.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, paws on z = 0. +X is its left. The maps go to assets/pets/CelestialEgg/.

What touches what: body, neck, head, legs, paws and tail are one fused skin; the eyes sit in their sockets under their lids; the ears, the nose and the
whiskers are their own pieces set into the head.
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
PET = "CelestialSnowLeopard"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- colours: snow, smoke and starlight ----------
FUR, FUR_SHADE, BELLY = rgb(222, 226, 232), rgb(176, 182, 194), rgb(246, 247, 250)
FROST = rgb(206, 226, 246)
ROSETTE, ROSETTE_IN = rgb(46, 48, 58), rgb(148, 154, 168)
STAR = rgb(196, 232, 255)
NIGHT, NIGHT_GLOW = rgb(22, 34, 78), rgb(56, 82, 156)
PAD, NOSE_COL, NOSE_LIT, MOUTH = rgb(118, 136, 166), rgb(170, 132, 140), rgb(214, 176, 182), rgb(30, 26, 32)
EAR_BACK, EAR_IN = rgb(70, 72, 82), rgb(206, 208, 216)
WHISKER, WHISKER_TIP = rgb(236, 242, 250), rgb(250, 252, 255)
GLINT_HEX = "ffffff"

# ---------- the frame of it ----------
FACE_SHIFT = V(0, -0.03, -0.05)         # the head carried low and forward of where its features were first laid out


def hv(x, y, z):
    """A point on the head, as laid out, moved with it."""
    return V(x, y, z) + FACE_SHIFT


SPINE = [V(0, 0.33, 0.4), V(0, 0.22, 0.425), V(0, 0.1, 0.42), V(0, -0.02, 0.415), V(0, -0.13, 0.43), V(0, -0.22, 0.445)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.088), (0.15, 0.118), (0.4, 0.108), (0.65, 0.115), (0.85, 0.125), (1, 0.112))         # half-widths, rump to withers
BODY_H = ((0, 0.09), (0.15, 0.115), (0.4, 0.118), (0.65, 0.126), (0.85, 0.135), (1, 0.12))        # half-heights
BODY_DROP = ((0, 0.0), (0.15, 0.014), (0.4, 0.045), (0.65, 0.05), (0.85, 0.042), (1, 0.03))      # the loft's centre below the spine: a deep, furred belly
NECK = catmull([V(0, -0.22, 0.44), V(0, -0.31, 0.46), V(0, -0.38, 0.475), V(0, -0.44, 0.49)], 10)     # near level: the head carried low and forward
NECK_R = ((0, 0.1), (0.5, 0.088), (1, 0.076))
HEAD = hv(0, -0.44, 0.55)
HEAD_R = (0.082, 0.078, 0.07)
TAIL = catmull([V(0, 0.35, 0.39), V(0, 0.47, 0.33), V(0.02, 0.6, 0.25), V(0.06, 0.74, 0.19), V(0.12, 0.87, 0.165), V(0.19, 0.97, 0.195), V(0.23, 1.02, 0.285),
                V(0.22, 1.0, 0.375), V(0.17, 0.95, 0.415)], 10)
TAIL_PROFILE = ((0, 0.066), (0.15, 0.063), (0.5, 0.066), (0.85, 0.068), (0.95, 0.056), (1, 0.04))      # thick all the way: the snow leopard's tail
FRONT = [V(0.085, -0.19, 0.39), V(0.1, -0.14, 0.24), V(0.09, -0.21, 0.09), V(0.088, -0.232, 0.045), V(0.088, -0.255, 0.033)]     # the elbow tucked back under the chest
HIND = [V(0.09, 0.22, 0.39), V(0.108, 0.12, 0.24), V(0.096, 0.28, 0.115), V(0.09, 0.255, 0.045), V(0.09, 0.23, 0.033)]
FRONT_R = [0.076, 0.058, 0.046, 0.046, 0.044]
HIND_R = [0.096, 0.064, 0.04, 0.044, 0.042]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.019
EYE_C = hv(0.038, -0.497, 0.565)
EYE_AXIS = V(0.3, -0.95, 0.06).normalized()
LID_UP, LID_LOW = (27.0, 120.0, 0.0026), (-34.0, -128.0, 0.0022)       # level and steady: a hunter's look
LID_TILT = 9.0
BLINK_U, BLINK_L = 52.0, 24.0
IRIS, PUPIL = 0.92, 0.3                 # on the eye's face (its front is 1): a big cat's round pupil
NOSE_TOP, NOSE_BASE_Y = 0.538 + FACE_SHIFT.z, -0.538 + FACE_SHIFT.y   # the nose's top edge (z) and how far back its body sits (y)


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


def tail_radius(f):
    return prof(TAIL_PROFILE, f)


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.01, -0.005), (0.085, 0.075, 0.085))                       # the rump
    core.ball(V(0, -0.28, 0.4), (0.082, 0.072, 0.1))                                       # the chest, deep and round under the neck
    for side in (1, -1):
        core.ball(V(side * 0.072, -0.2, 0.41), (0.06, 0.085, 0.08))                        # the shoulder, under the fur
        core.ball(V(side * 0.08, 0.21, 0.38), (0.08, 0.11, 0.1))                           # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 48, 32)                                                         # the skull: small and broad
    fine.ball(hv(0, -0.468, 0.585), (0.058, 0.05, 0.04))                                    # the domed forehead
    fine.ball(hv(0, -0.51, 0.525), (0.045, 0.036, 0.034))                                   # the muzzle, short and broad
    fine.ball(hv(0, -0.5, 0.5), (0.026, 0.026, 0.018))                                      # the chin
    for side in (1, -1):
        fine.ball(hv(side * 0.05, -0.45, 0.515), (0.05, 0.05, 0.046))                       # the cheek ruff, thick with fur
        fine.ball(hv(side * 0.02, -0.533, 0.52), (0.022, 0.017, 0.018))                     # the whisker pad
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(hv(side * 0.036, -0.488, 0.582), (0.026, 0.026, 0.016))                   # the brow over the eye: its lids' hidden edges stay under it
    for key, side, knots, radii in LEGS:
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.92)
        paw = mir(knots[3], side)
        fine.ball(paw + V(0, -0.008, -0.012), (0.045, 0.055, 0.03), 28, 16)                # the paw: huge, a snowshoe
        for k in range(4):
            a = (k - 1.5) * 0.42
            fine.ball(paw + V(math.sin(a) * 0.03, -0.055 - math.cos(a) * 0.008, -0.016), (0.015, 0.017, 0.016), 14, 10)
    loft(fine, TAIL, lambda f: tail_radius(f), lambda f: tail_radius(f))
    fine.ball(TAIL[-1], (0.036, 0.036, 0.036), 20, 14)                                    # the tail's round, furred end
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


# ---------- ears, nose, whiskers ----------
EAR = {"front": hv(0.034, -0.45, 0.605), "back": hv(0.066, -0.415, 0.575), "height": 0.044}


def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    up = (V(side * 0.5, 0.15, 1) - along * V(side * 0.5, 0.15, 1).dot(along)).normalized()     # set wide: leaning out to its side
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n          # facing forward
    return A, B, C, along, up, n


def ear_point(side):
    """A small rounded ear: its base along the head, its rim a low arc over the top; u from the base to the rim, v across. The rim reaches a little past
    the base at both ends, so no row of the sheet is drawn to a point."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        rim = C + along * (-math.cos(math.pi * v) * a * 1.12) + up * (math.sin(math.pi * v) * EAR["height"] + 0.01)
        p = base.lerp(rim, u)
        cup = 0.011 * math.sin(math.pi * v) * math.sin(math.pi * min(1.0, u * 1.1))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return 0.009 * (1 - u) ** 0.7 + 0.0028


def build_ear(side, name):
    """Smoky grey-black behind with a pale spot, the hollow pale and furred, a dark rim."""
    nu, nv = 60, 60
    o = sheet_hi(ear_point(side), ear_thick, nu, nv, name, lambda u, v: np.broadcast_to(EAR_BACK, (len(u), 3)), lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    uu, vv = np.zeros((nu + 1) * (nv + 1) * 2), np.zeros((nu + 1) * (nv + 1) * 2)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    Nn = normals(o)
    _, _, _, _, _, n = ear_frame(side)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(n)))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.7)
    back = mix(np.broadcast_to(EAR_BACK, (len(uu), 3)), FUR, (1 - smooth(0.12, 0.2, np.hypot(uu - 0.45, (vv - 0.5) * 0.8))) * 0.85)     # the pale spot on the back
    hollow = mix(EAR_IN * 0.7, EAR_IN, smooth(0.05, 0.25, edge))
    col = mix(back, hollow, inside * smooth(0.03, 0.08, edge))
    col = mix(col, EAR_BACK * 0.7, 1 - smooth(0.01, 0.035, edge))
    paint(o, col, np.full(len(uu), 0.62), np.zeros(len(uu)))
    return o


def nose_point(sx, sy, sz):
    """A broad little nose from the unit sphere: wider at the top, narrowing to a soft point below, its front pushed forward, its back set into the muzzle."""
    t = (1 - sz) / 2
    w = 0.014 * (1 - t) ** 0.75 + 0.0018
    depth = (0.006 + 0.005 * t) if sy < 0 else 0.006
    return V(sx * w, NOSE_BASE_Y + sy * depth, NOSE_TOP - 0.016 * t - 0.0016 * math.exp(-(sx / 0.32) ** 2) * max(0.0, sz) ** 3)


def build_nose(name, coll, seg=36, rings=24):
    m = Mesh()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in m.bm.verts:
        v.co = nose_point(v.co.x, v.co.y, v.co.z)
    return m.finish(name, coll)


def paint_nose(o):
    P = verts(o)
    Nn = normals(o)
    col = mix(NOSE_COL, NOSE_LIT, smooth(-0.2, 0.9, Nn[:, 2]) * 0.6)
    nostril = np.zeros(len(P))
    for side in (1, -1):
        c = np.array((side * 0.0055, NOSE_BASE_Y - 0.008, NOSE_TOP - 0.012))
        nostril = np.maximum(nostril, 1 - smooth(0.0013, 0.0026, np.linalg.norm((P - c) * np.array([1.0, 1.6, 0.8]), axis=1)))
    col = mix(col, MOUTH, nostril)
    paint(o, col, 0.3 + 0.4 * nostril, np.zeros(len(P)))


def whisker_paths():
    """Five whiskers each side from the whisker pad, sweeping out and back, drooping a little toward their tips."""
    out = []
    for side in (1, -1):
        for k in range(5):
            root = hv(side * (0.024 + 0.003 * k), -0.536 + 0.004 * k, 0.53 - 0.0045 * k)
            d = V(side * 0.92, 0.28 + 0.05 * k, 0.14 - 0.11 * k).normalized()
            length = 0.085 - 0.006 * abs(k - 1.5)
            out.append([root - d * 0.004, root + d * length * 0.5 + V(0, 0, -0.003), root + d * length + V(0, 0, -0.011 - 0.002 * k)])
    return out


def build_whiskers(name, coll, sides=6, per=5):
    m = Mesh()
    for pts in whisker_paths():
        m.tube(catmull(pts, per), lambda f: 0.0016 * (1 - 0.7 * f) + 0.0005, sides=sides)
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


def tail_coords(P):
    f, d = nearest_on(TAIL, P)
    return f, d


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    head = 1 - smooth(0.085, 0.12, np.linalg.norm((P - np.array(tuple(HEAD + V(0, -0.03, 0)))), axis=1))
    leg = smooth(0.3, 0.2, z) * (1 - head)
    tf, td = tail_coords(P)
    on_tail = (1 - smooth(0.0, 0.025, td - np.array([tail_radius(float(f)) for f in tf]) * 1.1)) * smooth(0.04, 0.1, tf)
    leg = leg * (1 - on_tail)                                # (the tail is low, but it is no leg)
    # long thick fur lying back along the body, down the legs and along the tail; a cool frost sheen where it faces up
    hair_body = fbm(P * np.array([150.0, 38.0, 150.0]), 1.0, 3, 3)
    hair_leg = fbm(P * np.array([150.0, 150.0, 38.0]), 1.0, 3, 5)
    fur = hair_body * (1 - leg) + hair_leg * leg
    col = mix(FUR * 0.86, FUR, smooth(0.3, 0.7, fur))
    col = mix(col, FUR_SHADE, smooth(0.0, -0.6, Nn[:, 2]) * 0.35)
    col = mix(col, FROST, smooth(0.25, 0.9, Nn[:, 2]) * 0.35)
    under = smooth(-0.15, -0.65, Nn[:, 2]) * (1 - head) * (1 - on_tail * 0.6)
    col = mix(col, BELLY, under * 0.9)
    throat = smooth(0.55, 0.85, (Nn * np.array((0, -0.8, -0.6))).sum(1)) * smooth(-0.2, -0.32, y) * smooth(0.52, 0.46, z)
    col = mix(col, BELLY, np.clip(throat, 0, 1) * 0.85)
    # rosettes on the body and tail: rings of dark blotches, irregular and broken open, round smoky centres; small spots between them; solid spots on
    # the head and legs; the tail's dark end. The cells are warped, so no rosette is a circle.
    warp = np.stack([fbm(P, 9.0, 3, 31), fbm(P, 9.0, 3, 37), fbm(P, 9.0, 3, 41)], 1) - 0.5
    Q = P + warp * 0.05
    big = cells(Q, 17.0, 1)
    small = cells(P, 46.0, 7)
    ring_mid = 0.44 + 0.08 * (big[2] - 0.5)
    width = 0.1 + 0.05 * fbm(Q, 30.0, 2, 17)
    ring = 1 - smooth(width * 0.6, width, np.abs(big[0] - ring_mid))
    blotch = smooth(0.36, 0.5, fbm(Q, 34.0, 3, 11 + 0))           # the ring broken into three to five blotches
    ring *= blotch
    inner = (1 - smooth(ring_mid - 0.14, ring_mid - 0.05, big[0])) * (0.45 + 0.25 * fbm(Q, 60.0, 2, 19))
    flecks = (1 - smooth(0.16, 0.24, small[0])) * (small[2] > 0.6) * smooth(ring_mid + 0.08, ring_mid + 0.18, big[0])      # small spots between the rosettes
    spot = 1 - smooth(0.24, 0.34, small[0] + 0.12 * (small[2] - 0.5))
    plain = (1 - under) * (1 - np.clip(throat, 0, 1))
    solid = np.clip(head + leg, 0, 1)
    rose_w = (1 - solid) * plain
    col = mix(col, ROSETTE_IN, inner * rose_w)
    col = mix(col, ROSETTE, np.clip(ring + flecks, 0, 1) * rose_w)
    col = mix(col, ROSETTE, spot * solid * plain)
    tip = smooth(0.86, 0.94, tf) * on_tail
    col = mix(col, ROSETTE, tip)
    # the night sky: the rosettes along its back hold it, their centres deep night-blue speckled with ice-blue stars
    starry = (big[2] > 0.55) * smooth(0.15, 0.55, Nn[:, 2]) * rose_w
    inside = 1 - smooth(ring_mid - 0.13, ring_mid - 0.05, big[0])
    sky = mix(NIGHT, NIGHT_GLOW, smooth(0.3, 0.75, fbm(Q, 40.0, 3, 23)) * 0.6)
    col = mix(col, sky, inside * starry)
    pts = cells(P, 110.0, 21)
    star = ((1 - smooth(0.07, 0.15, pts[0])) + 0.4 * (1 - smooth(0.15, 0.32, pts[0]))) * (pts[2] > 0.45)
    col = mix(col, STAR, np.clip(star, 0, 1) * inside * starry)
    # the paw pads: icy blue-grey, under each paw
    pads = np.zeros(len(P))
    for key, side, knots, radii in LEGS:
        c = np.array(tuple(mir(knots[3], side) + V(0, -0.02, -0.04)))
        pads = np.maximum(pads, (1 - smooth(0.03, 0.045, np.linalg.norm((P - c) * np.array([1.0, 0.8, 2.0]), axis=1))) * smooth(-0.3, -0.7, Nn[:, 2]))
    col = mix(col, PAD, pads)
    # the face: dark rims round the eyes running a short tear line down, the mouth's line
    rims = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(EYE_C, side)))
        r = np.linalg.norm(P - c, axis=1)
        rims = np.maximum(rims, smooth(EYE_R * 1.45, EYE_R * 1.12, r))
        a = np.array(tuple(hv(side * 0.03, -0.52, 0.552)))
        b = np.array(tuple(hv(side * 0.024, -0.532, 0.534)))
        t = np.clip(((P - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        rims = np.maximum(rims, (1 - smooth(0.0016, 0.0032, np.linalg.norm(P - (a + t[:, None] * (b - a)), axis=1))) * 0.8)
    col = mix(col, ROSETTE, rims * 0.9)
    fy, fz = y - FACE_SHIFT.y, z - FACE_SHIFT.z          # as laid out
    philtrum = (np.abs(x) < 0.0018) * (fz < 0.523) * (fz > 0.508) * (fy < -0.535)
    lip = (1 - smooth(0.0013, 0.0032, np.abs(fz - (0.506 + 7 * x ** 2)))) * (np.abs(x) < 0.026) * (fy < -0.515)
    mouth = np.clip(philtrum + lip, 0, 1)
    col = mix(col, MOUTH, mouth * 0.9)
    relief = (fur - 0.5) * 0.0007 - 0.0008 * mouth
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.7 - 0.1 * smooth(0.45, 0.8, fur) - 0.25 * pads, np.zeros(len(P)))


def eye_paint(o, fr):
    """Pale ice going to aquamarine-silver at the rim, fine fibres, a round dark pupil, a dark rim."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(14, 18, 24), (len(px), 3)).copy()
    iris = mix(rgb(226, 240, 244), rgb(124, 184, 192), smooth(PUPIL * 1.1, IRIS, r))
    iris = mix(iris, iris * 0.72, smooth(-0.2, 0.8, py / IRIS) * 0.45)          # shadowed under the upper lid
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 36 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    col = mix(col, rgb(40, 70, 80), smooth(IRIS - 0.1, IRIS - 0.02, r) * (1 - smooth(IRIS, IRIS + 0.04, r)))
    col = mix(col, rgb(4, 4, 8), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def paint_whiskers(o):
    P = verts(o)
    d = np.linalg.norm(P[:, [0, 2]] - np.array((0.0, 0.52 + FACE_SHIFT.z)), axis=1)
    col = mix(np.broadcast_to(WHISKER, (len(P), 3)), WHISKER_TIP, smooth(0.04, 0.09, d))
    paint(o, col, np.full(len(P), 0.35), np.zeros(len(P)))


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
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, FUR, ROSETTE)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, FUR, ROSETTE, lower_share=0.9)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Nose"] = build_nose(N + "NoseHi", HI)
    pieces["Whiskers"] = build_whiskers(N + "WhiskersHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0036, 12), (22, -18, 0.0017, 8)))}
    if not clay:
        paint_skin(skin)
        paint_nose(pieces["Nose"])
        paint_whiskers(pieces["Whiskers"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.25, 0.32)
FACE_AT = tuple(hv(0, -0.48, 0.55))
EXTRA = [(0, -1, 0.05, 0.75, FACE_AT), (0.62, -0.75, 0.2, 0.75, FACE_AT), (1, -0.12, 0.08, 0.75, FACE_AT), (0.3, -0.9, 0.2, 0.35, tuple(EYE_C)),
         (0.7, 0.5, 0.4, 1.6, (0.1, 0.85, 0.3)), (1, -0.1, 0.05, 1.3, (0, -0.1, 0.2))]

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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3600
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Nose": 3.0, "EarL": 1.4, "EarR": 1.4, "Whiskers": 0.6}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 8, 8, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Nose"] = build_nose(N + "NoseLow", GAME, 14, 10)
    lows["Whiskers"] = build_whiskers(N + "WhiskersLow", GAME, 4, 2)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the hips are its base: everything ahead of them can crouch, stretch and lie off them
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Shoulders", SPINE[4], "Chest"),
               ("Neck", NECK[0], "Shoulders"), ("Head", NECK[-1], "Neck"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 8)]
TAIL_F = (0.03, 0.17, 0.31, 0.45, 0.6, 0.75, 0.88)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw" + key] for key, _, _, _ in LEGS}


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots):
    """Where each leg bone takes over along its leg: the middle of each bone, so the share passes across each joint."""
    fs = [k / (len(knots) - 1) for k in range(len(knots))]
    return tuple((fs[k] + fs[k + 1]) / 2 for k in range(4))


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, C, along, up, n = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, C.copy(), "Head")]
    fs = [k / (len(FRONT) - 1) for k in range(len(FRONT))]
    for key, side, knots, _ in LEGS:
        parent = "Shoulders" if key[0] == "F" else "Hips"
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


def body_weights(P):
    """The skin's weights at any points: the trunk (hips to head), the head, the tail, the legs; a paw and its toes wholly its paw's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    head_d = np.linalg.norm((P - np.array(tuple(HEAD + V(0, -0.03, -0.01)))) / np.array((0.1, 0.12, 0.1)), axis=1)
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
            if (Vector(P[i]) - (mir(knots_l[3], side) + V(0, -0.025, -0.01))).length < 0.075 and z < 0.07:
                owner = "Paw" + key
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if head_d[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, head_d[i])))
        reach = tail_radius(float(tf[i])) * 1.12 + 0.01
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.0, 0.05, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        for key, side, knots_l, radii, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.014
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            # the belly between the legs: the share falls away toward the midline over a hand's width, so a swing of the thigh or the upper arm pulls the
            # belly skin gently across that span instead of tearing it at a line (the knee sits close under the belly)
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
    rigid(lows["Nose"], "Head")
    rigid(lows["Whiskers"], "Head")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateSnowLeopard uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


# its stances, searched in Blender against the ground and for torn skin (see the vault): the same numbers as PetRig's LEOPARD_* tables
def legs4(f, b):
    """Both forelegs f = (upper, fore, wrist) and both hind legs b = (thigh, shin, hock), the same on each side."""
    out = {}
    for side in "LR":
        for k in range(3):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, 0)
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, 0)
    return out


CROUCH = {"Hips": (0, 0, 0, (0, -0.098, 0)), "Shoulders": (0.005, 0, 0), "Head": (0.228, 0, 0), **legs4((-0.2, -1.387, -0.2), (0.354, -0.419, 0.957))}
LIE = {"Hips": (-0.158, 0, 0, (0, -0.182, 0)), "Shoulders": (0.265, 0, 0), "Head": (0.16, 0, 0), **legs4((0.226, 1.261, -0.698), (0.23, -1.026, -0.306)),
       "Tail1": (0.0, 0.4, 0), "Tail2": (0.0, 0.4, 0), "Tail3": (0, 0.35, 0)}
LEAP = {"Hips": (-0.12, 0, 0), "Shoulders": (-0.2, 0, 0), "Head": (0.155, 0, 0), **legs4((0.756, -0.247, -0.29), (-0.511, 0.407, -0.106)),
        **{n: (-0.05, 0, 0) for n in TAIL_NAMES}}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    stride = {"LegFL1": (0.45, 0, 0), "LegFL2": (-0.5, 0, 0), "LegFR1": (-0.35, 0, 0), "LegBL1": (-0.45, 0, 0), "LegBR1": (0.4, 0, 0), "LegBR2": (-0.6, 0, 0),
              "Shoulders": (0, 0.06, 0), "Hips": (0, -0.05, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-7, -5), "Stride": spec(stride), "Crouch": spec(CROUCH), "Lie": spec(LIE), "Leap": spec(LEAP),
            "Look": spec({"Neck": (0.15, 0.4, 0), "Head": (0.2, 0.5, 0.15)}), "Tail": spec({n: (0.06, 0.15, 0) for n in TAIL_NAMES}),
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


GROUND_PARTS = {"FrontPaws": ("PawFL", "PawFR"), "HindPaws": ("PawBL", "PawBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",), "Tail": tuple(TAIL_NAMES)}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.4 and p.center.z > 0.42, 2.0), (None, 1.0)], SCALES, margin=0.009)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.85, 0.86, 0.88, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.01, 0.025),
             reaches={"Whiskers": (0.002, 0.006)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    bpy.data.objects.remove(glows["Glints"], do_unlink=True)          # first, so the game's piece takes its exact name
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0036, 10), (22, -18, 0.0017, 6)))}
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
    for name in ("Hips", "Head", "Tail7"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Crouch", "Lie", "Leap"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 3.4, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 3.4, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.8, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Stride", side), ("Crouch", side), ("Lie", wide), ("Leap", side), ("Look", face), ("Tail", wide), ("Ears", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 3.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

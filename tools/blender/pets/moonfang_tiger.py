"""The Moonfang Tiger (Rare, Moonlight; Ancient Grove Egg): "A tiger whose fangs catch moonlight and keep it. It hunts only when the moon can watch."

A new creature, in a design language of its own: a tiger out of a moonlit ink painting. A young tiger, chunky and bold: a big broad head, a deep chest,
thick legs and big paws, short white cheek ruffs. Its coat is moonlit silver, as rice paper is under the moon, washed darker along its back as a painter
washes in thinned ink, rice-white beneath and on its muzzle; its stripes are bold strokes of black ink laid on with a dry brush, tapering at both ends,
the bristles' streaks showing through; on its brow the tiger's 王 in ink; the backs of its ears ink-black, each with a white spot. A painter's seal in
vermilion on its haunch. Its tail is ringed in ink and ends in a calligraphy brush: a soft bulb of pale hairs drawn to a point dipped in ink. Moon-gold
eyes. Two long fangs of moonstone hang over its lower lip, glowing with the moonlight they keep.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/moonfang_tiger.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: the game mesh and skeleton, posed and checked. all: also the unwrap,
bake, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre, paws on z = 0. +X is its left. The maps go to assets/pets/AncientGroveEgg/.

What touches what: body, neck, head, legs, paws and tail (its brush tip too) are one fused skin; the eyes sit in their sockets under their lids; the
ears, nose and whiskers are their own pieces set into the head; the fangs (a glow piece) root in the upper lip, hanging over the lower.
"""
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401
from mathutils.bvhtree import BVHTree  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "MoonfangTiger"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AncientGroveEgg")

# ---------- colours: moonlit rice paper, ink, a vermilion seal, moonstone ----------
# (after the owner's reference photo, 2026-11-12: a Bengal tiger walking toward the camera)
SILVER, SILVER_COOL = rgb(222, 128, 44), rgb(236, 150, 62)          # its coat: deep orange, warmer in the light
WASH = rgb(176, 86, 28)                                             # darker along its spine
RICE = rgb(248, 242, 230)                                           # its belly, muzzle, chin, ruffs and brow patches: white
CREAM = rgb(240, 214, 170)                                          # where orange goes to white down its sides
INK, INK_WET = rgb(18, 14, 14), rgb(18, 14, 14)
SEAL = rgb(196, 42, 34)
EAR_IN = rgb(238, 232, 222)                                         # white fur inside its ears, as a tiger's
NOSE_COL, NOSE_LIT = rgb(184, 100, 90), rgb(206, 128, 112)       # a pink-orange nose, as in the reference
MOUTH = rgb(46, 30, 34)
PAD = rgb(70, 64, 72)
WHISKER, WHISKER_TIP = rgb(246, 246, 250), rgb(206, 212, 228)
FANG_HEX, GLINT_HEX = "8fd0ff", "ffffff"

# ---------- the frame of it ----------
BS = 1.15                                                         # its body against its head: a grown predator's build (the owner: "That's a predator pet, why are you making it looks cute?")
SPINE = [V(0, 0.22, 0.34) * BS, V(0, 0.14, 0.355) * BS, V(0, 0.05, 0.35) * BS, V(0, -0.03, 0.35) * BS, V(0, -0.11, 0.37) * BS, V(0, -0.17, 0.39) * BS]
BODY_PATH = catmull(SPINE, 10)
BODY_W = tuple((f, w * BS) for f, w in ((0, 0.088), (0.15, 0.118), (0.45, 0.114), (0.7, 0.13), (0.88, 0.142), (1, 0.126)))       # half-widths, rump to withers: heavy in the shoulder
BODY_H = tuple((f, h * BS) for f, h in ((0, 0.09), (0.15, 0.116), (0.45, 0.124), (0.7, 0.134), (0.88, 0.142), (1, 0.128)))     # deep: a tiger's belly hangs (shallow, it read as a greyhound)
BODY_DROP = tuple((f, d * BS) for f, d in ((0, 0.0), (0.15, 0.016), (0.45, 0.04), (0.7, 0.042), (0.88, 0.034), (1, 0.02)))
NECK = catmull([V(0, -0.19, 0.43), V(0, -0.225, 0.445), V(0, -0.26, 0.465)], 10)      # the head low between its shoulders: a hunter's carriage                     # barely any: the head sits on its shoulders
NECK_R = ((0, 0.12), (0.5, 0.108), (1, 0.096))
HEAD = V(0, -0.37, 0.5)
HEAD_R = (0.14, 0.14, 0.1)                                                                     # big and broad: a young tiger's
TAIL = catmull([V(0, 0.25, 0.33) * BS, V(0, 0.35, 0.28) * BS, V(0.01, 0.45, 0.21) * BS, V(0.03, 0.55, 0.15) * BS, V(0.06, 0.65, 0.12) * BS, V(0.09, 0.73, 0.13) * BS, V(0.11, 0.79, 0.17) * BS], 10)     # low and heavy, its end lifting
TAIL_PROFILE = ((0, 0.046), (0.2, 0.041), (0.6, 0.035), (0.85, 0.032), (0.95, 0.028), (1, 0.016))     # thick to a rounded black tip
FRONT = [V(0.078, -0.13, 0.33) * BS, V(0.092, -0.09, 0.2) * BS, V(0.086, -0.14, 0.08) * BS, V(0.084, -0.16, 0.042) * BS, V(0.084, -0.184, 0.032) * BS]
HIND = [V(0.084, 0.16, 0.33) * BS, V(0.1, 0.07, 0.21) * BS, V(0.09, 0.21, 0.1) * BS, V(0.086, 0.19, 0.042) * BS, V(0.086, 0.17, 0.032) * BS]
FRONT_R = [r * BS for r in (0.086, 0.07, 0.056, 0.054, 0.05)]           # thick forelegs: a tiger kills with them
HIND_R = [r * BS for r in (0.098, 0.07, 0.05, 0.05, 0.048)]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.024
EYE_C = V(0.054, -0.398, 0.552)                                   # big: a cub's eyes (smaller, they read beady)
EYE_AXIS = V(0.42, -0.89, 0.18).normalized()                  # forward under its brow
LID_UP, LID_LOW = (24.0, 120.0, 0.0024), (-17.0, -128.0, 0.002)       # a hard stare: heavy upper lids, the lower raised in a squint       # bold and open (lower, heavy upper lids read sad)
LID_TILT = 30.0                                          # its lids slanting down to its inner corners: a scowl (at 18, with the game lids buried, it looked worried; at 50, strange)
BLINK_U, BLINK_L = 31.0, 16.0                                            # (the two add past the 41 degrees between the edges)
IRIS, PUPIL = 0.92, 0.24                                 # a small pupil: intent
NOSE_TOP, NOSE_BASE_Y = 0.516, -0.486
MUZZLE_C = V(0, -0.47, 0.465)
FANG = [V(0.024, -0.474, 0.442), V(0.026, -0.483, 0.415), V(0.024, -0.486, 0.394)]     # long: a predator's   # (longer, they read as a walrus's tusks)   # (left) root in the upper lip, hanging over the lower
FANG_R = 0.0068


def ell_dist(P, c, r):
    return np.linalg.norm((P - np.array(tuple(c))) / np.array(r), axis=1)


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
    k = min(max(f, 0.0), 1.0) * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def loft(m, path, w_fn, h_fn, drop_fn=None, nt=48):
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
# Its head, lofted front to back like a sculptor's blocks: (y, half-width, top, bottom) of each section; each section a squared ellipse. A tiger's skull:
# a round back, the cheekbones widest, a heavy brow, then a long sloping bridge down to a deep square muzzle and a broad nose. (A sphere with a muzzle
# raised on it read as a mouse, the owner: "that's not a tiger, that's a mouse".)
HEAD_SECTIONS = [(-0.235, 0.05, 0.545, 0.47), (-0.255, 0.092, 0.588, 0.43), (-0.29, 0.118, 0.612, 0.41), (-0.33, 0.128, 0.616, 0.405),
                 (-0.37, 0.12, 0.605, 0.41), (-0.4, 0.1, 0.585, 0.415), (-0.425, 0.08, 0.555, 0.418), (-0.45, 0.07, 0.53, 0.42),
                 (-0.47, 0.064, 0.518, 0.426), (-0.485, 0.052, 0.512, 0.434), (-0.494, 0.03, 0.505, 0.448)]     # (2 cm longer, its muzzle read as a snout)
SWELLS = [(V(0.028, -0.475, 0.462), 0.011, (0.024, 0.02, 0.022)), (V(-0.028, -0.475, 0.462), 0.011, (0.024, 0.02, 0.022)),    # the whisker-pad lobes
          (V(0.13, -0.33, 0.445), 0.042, (0.05, 0.06, 0.05)), (V(-0.13, -0.33, 0.445), 0.042, (0.05, 0.06, 0.05)),         # the cheek ruffs, flaring out below the ears
          (V(0, -0.455, 0.425), 0.012, (0.04, 0.04, 0.02)),              # the chin
          (V(0.05, -0.395, 0.588), 0.017, (0.036, 0.026, 0.016)), (V(-0.05, -0.395, 0.588), 0.017, (0.036, 0.026, 0.016)),    # the heavy brow over each eye
          (V(0, -0.41, 0.582), 0.008, (0.014, 0.02, 0.025))]               # the ridge between its brows: a scowl


def head_with_face():
    m = Mesh()
    bm = m.bm
    nt, per = 96, 6
    secs = HEAD_SECTIONS
    # sections smoothed along its length
    # sections joined by a spline (eased one to the next, each joint showed as a ridge)
    pts = [V(q[0], q[1], q[2]) for q in secs]
    pts2 = [V(q[3], 0, 0) for q in secs]
    sp1, sp2 = catmull(pts, per), catmull(pts2, per)
    rows = [(p1.x, p1.y, p1.z, p2.x) for p1, p2 in zip(sp1, sp2)]
    rings = []
    for y, w, top, bot in rows:
        cz, hz = (top + bot) / 2, (top - bot) / 2
        ring = []
        for k in range(nt):
            a = TAU * k / nt
            c, sn = math.cos(a), math.sin(a)
            e = 2.6                                                      # squared: a square muzzle, a broad skull
            r = (abs(c) ** e + abs(sn) ** e) ** (-1 / e)
            ring.append(bm.verts.new(V(c * r * w, y, cz + sn * r * hz)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    back = bm.verts.new(V(0, rows[0][0] + 0.03, (rows[0][2] + rows[0][3]) / 2))
    front = bm.verts.new(V(0, rows[-1][0] - 0.008, (rows[-1][2] + rows[-1][3]) / 2))
    for k in range(nt):
        bm.faces.new((back, rings[0][(k + 1) % nt], rings[0][k]))
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % nt], front))
    o = m.finish(N + "HeadHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0025, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 16})])
    P, Nn = verts(o), normals(o)
    h = np.zeros(len(P))
    for c, amp, reach in SWELLS:
        h += amp * np.exp(-np.sum(((P - np.array(tuple(c))) / np.array(reach)) ** 2, axis=1))
    set_verts(o, P + Nn * h[:, None])
    return o


def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.01, -0.005), (0.085 * BS, 0.075 * BS, 0.085 * BS))      # the rump
    core.ball(V(0, -0.2, 0.34) * BS, (0.1 * BS, 0.085 * BS, 0.11 * BS))                   # the chest, deep and broad
    for side in (1, -1):
        core.ball(V(side * 0.075, -0.13, 0.35) * BS, (0.072 * BS, 0.09 * BS, 0.1 * BS))  # the shoulder: heavy and high, as in the reference
        core.ball(V(side * 0.078, 0.18, 0.33) * BS, (0.075 * BS, 0.1 * BS, 0.095 * BS))  # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    for side in (1, -1):
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
    for key, side, knots, radii in LEGS:
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.95)
        paw = mir(knots[3], side)
        fine.ball(paw + V(0, -0.016, -0.014), (0.064, 0.074, 0.038), 28, 16)             # the paw: huge, as a tiger's
        for k in range(4):
            a = (k - 1.5) * 0.42
            fine.ball(paw + V(math.sin(a) * 0.045, -0.08 - math.cos(a) * 0.008, -0.019), (0.021, 0.023, 0.02), 14, 10)
    loft(fine, TAIL, lambda f: tail_radius(f), lambda f: tail_radius(f))
    th = fine.finish(N + "FineHi", HI)
    for part in (th, head_with_face()):
        bm = bmesh.new()
        bm.from_mesh(c.data)
        bm.from_mesh(part.data)
        bm.to_mesh(c.data)
        bm.free()
        bpy.data.objects.remove(part, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0032, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    P = verts(c)
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- ears, nose, whiskers, fangs ----------
EAR = {"front": V(0.085, -0.31, 0.6), "back": V(0.122, -0.265, 0.565), "height": 0.042}     # set out at the sides of its skull (on top, round, they read as a mouse's)


def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    up = (V(side * 0.75, 0.15, 1) - along * V(side * 0.75, 0.15, 1).dot(along)).normalized()
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n
    return A, B, C, along, up, n


def ear_point(side):
    """A rounded ear: its base along the head, its rim a round arc over the top; u from the base to the rim, v across."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        rim = C + along * (-math.cos(math.pi * v) * a * 1.1) + up * (math.sin(math.pi * v) ** 0.8 * EAR["height"] + 0.008)
        p = base.lerp(rim, u)
        cup = 0.013 * math.sin(math.pi * v) * math.sin(math.pi * min(1.0, u * 1.1))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return 0.01 * (1 - u) ** 0.7 + 0.003


def ear_uv(nu, nv):
    uu, vv = np.zeros((nu + 1) * (nv + 1) * 2), np.zeros((nu + 1) * (nv + 1) * 2)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    return uu, vv


def build_ear(side, name):
    """Ink-black behind with a white spot (a tiger's), the hollow pale and furred, a dark rim."""
    nu, nv = 60, 60
    o = sheet_hi(ear_point(side), ear_thick, nu, nv, name, lambda u, v: np.broadcast_to(INK, (len(u), 3)), lambda u, v: np.full_like(u, 0.7), lambda u, v: np.zeros_like(u))
    uu, vv = ear_uv(nu, nv)
    Nn = normals(o)
    _, _, _, _, _, n = ear_frame(side)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(n)))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.7)
    spot = 1 - smooth(0.13, 0.19, np.hypot(uu - 0.5, (vv - 0.5) * 0.8))
    back = mix(np.broadcast_to(INK, (len(uu), 3)), RICE, spot)
    hollow = mix(EAR_IN * 0.75, mix(EAR_IN, RICE, 0.5), smooth(0.05, 0.25, edge))
    col = mix(back, hollow, inside * smooth(0.03, 0.08, edge))
    col = mix(col, INK, 1 - smooth(0.01, 0.035, edge))
    paint(o, col, np.full(len(uu), 0.7), np.zeros(len(uu)))
    return o


def nose_point(sx, sy, sz):
    """A broad tiger's nose: wide at the top, narrowing to a point below, its front pushed forward, its back set into the muzzle."""
    t = (1 - sz) / 2
    w = 0.027 * (1 - t) ** 0.75 + 0.003
    depth = (0.008 + 0.006 * t) if sy < 0 else 0.008
    return V(sx * w, NOSE_BASE_Y + sy * depth, NOSE_TOP - 0.024 * t - 0.002 * math.exp(-(sx / 0.32) ** 2) * max(0.0, sz) ** 3)


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
        c = np.array((side * 0.009, NOSE_BASE_Y - 0.012, NOSE_TOP - 0.019))
        nostril = np.maximum(nostril, 1 - smooth(0.0016, 0.003, np.linalg.norm((P - c) * np.array([1.0, 1.6, 0.8]), axis=1)))
    col = mix(col, MOUTH, nostril)
    rim = smooth(0.6, 1.0, np.abs(P[:, 0]) / 0.027)
    col = mix(col, INK, rim * 0.6)
    paint(o, col, 0.55 + 0.3 * nostril, np.zeros(len(P)))         # (at 0.3 it shone like a plastic tab)


def whisker_paths():
    out = []
    for side in (1, -1):
        for k in range(5):
            root = V(side * (0.04 + 0.004 * k), -0.478 + 0.005 * k, 0.462 - 0.005 * k)
            d = V(side * 0.92, 0.25 + 0.05 * k, 0.12 - 0.1 * k).normalized()
            length = 0.1 - 0.007 * abs(k - 1.5)
            out.append([root - d * 0.004, root + d * length * 0.5 + V(0, 0, -0.003), root + d * length + V(0, 0, -0.012 - 0.002 * k)])
    return out


def build_whiskers(name, coll, sides=6, per=5):
    m = Mesh()
    for pts in whisker_paths():
        m.tube(catmull(pts, per), lambda f: 0.0018 * (1 - 0.7 * f) + 0.0005, sides=sides)
    return m.finish(name, coll)


def paint_whiskers(o):
    P = verts(o)
    d = np.abs(P[:, 0])
    col = mix(np.broadcast_to(WHISKER, (len(P), 3)), WHISKER_TIP, smooth(0.04, 0.1, d))
    paint(o, col, np.full(len(P), 0.35), np.zeros(len(P)))


def build_fangs(coll, sides=14, per=8):
    """Its two moonstone fangs: long, curved a little back, from the upper lip down over the lower."""
    m = Mesh()
    for side in (1, -1):
        pts = catmull([mir(p, side) for p in FANG], per)
        m.tube(pts, lambda f: FANG_R * (1 - f) ** 0.8 + 0.0008, sides=sides)
    return m.finish(N + "Fangs_Glow_" + FANG_HEX, coll)


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


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
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SILVER, INK, line_w=7.0)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, rgb(46, 34, 28), INK, lower_share=0.9, line_w=5.0)     # black-rimmed below (pale, a white rim under its eye)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Nose"] = build_nose(N + "NoseHi", HI)
    pieces["Whiskers"] = build_whiskers(N + "WhiskersHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0046, 12), (22, -18, 0.0022, 8))), "Fangs": build_fangs(HI)}
    if not clay:
        paint_all(pieces, frames)
    return pieces, frames, glows, data


# ---------- painting: ink on moonlit paper ----------
SPINE_Z = 0.36 * BS


def brush_stroke(along, across, length, width, seed, dry=0.6):
    """Coverage of one dry-brush stroke laid along a line: along (0..length) and across it (metres); tapering at both ends, the bristles' streaks
    opening into gaps toward its tail (where the brush runs dry)."""
    t = np.clip(along / length, 0, 1)
    inside = (along > 0) & (along < length)
    w = width * np.sin(np.pi * np.clip(t * 0.92 + 0.04, 0, 1)) ** 0.55
    core = 1 - smooth(w * 0.75, w + 0.0012, np.abs(across))
    streak = np.sin((across / max(width, 1e-6)) * 11.0 + hash01(np.floor(across * 900).astype(np.int64), seed, 0, 5) * 3.0) * 0.5 + 0.5
    gap = smooth(0.35, 1.0, t) * dry * 0.2           # (fully dry, every stripe split into hatching: a real tiger's stripes are solid, the reference)
    keep = 1 - gap * smooth(0.45, 0.75, streak)
    return core * keep * inside


def trunk_stripes(P, Nn):
    """Its body's stripes: strokes from its spine down each flank, slanting back as they go, some joined over the spine; on its haunches they
    turn into arcs curving round each thigh, as a tiger's do. (Laid by height alone, strokes on the haunch, which faces back, ran level along
    it and crossed the flank's into a hatched patch.)"""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    theta = np.arctan2(np.abs(x), z - SPINE_Z)                 # 0 on its spine, ~pi/2 at its flank's middle
    side = np.sign(x)
    out = np.zeros(len(P))
    hip_y = HIND[1].y + 0.02                                    # behind this, its flank is its haunch
    flank = 1 - smooth(hip_y - 0.03, hip_y + 0.03, y) * smooth(0.35, 0.7, theta)          # (over the spine they run on to its tail)
    flank = flank * (1 - smooth(0.45, 0.7, np.abs(Nn[:, 1])))                              # never on a face turned fore or aft
    ys = np.arange(-0.13 * BS, 0.26 * BS, 0.05)
    for k, y0 in enumerate(ys):
        for sd in (1, -1):
            seed = k * 2 + (sd > 0)
            reach = 1.45 + 0.6 * hash01(k, sd, 1, 11)                           # how far down the flank it runs: most of the way to its belly
            start = 0.0 if hash01(k, 0, 2, 13) > 0.3 else 0.12
            centre = y0 + 0.024 * (theta - start) + 0.007 * np.sin(theta * 3.1 + k)    # slanting back, a little wavering
            along = (theta - start) * 0.11
            stroke = brush_stroke(along, y - centre, (reach - start) * 0.11, 0.014 + 0.007 * hash01(k, sd, 3, 17), seed, dry=0.25)
            out = np.maximum(out, stroke * (side == sd) * flank)
        # a short fork below some strokes, as a tiger's stripes branch
        if hash01(k, 7, 4, 19) > 0.5:
            for sd in (1, -1):
                centre = y0 + 0.016 + 0.05 * (theta - 0.95)
                along = (theta - 0.95) * 0.11
                out = np.maximum(out, brush_stroke(along, y - centre, 0.05, 0.007, k + 50, dry=0.2) * (side == sd) * flank)
    # the haunch: arcs round the thigh, opening backward, on its outer face
    for sd in (1, -1):
        X = x * sd
        on = smooth(0.04, 0.09, X) * smooth(-0.1, 0.35, Nn[:, 0] * sd) * smooth(hip_y - 0.05, hip_y + 0.01, y) * smooth(0.12, 0.17, z)
        cy, cz = HIND[0].y + 0.07, HIND[0].z - 0.1
        r = np.hypot(y - cy, (z - cz) * 0.9)
        phi = np.arctan2(z - cz, cy - y)                     # 0 forward, pi/2 up
        for k, r0 in enumerate((0.055, 0.088, 0.121, 0.154)):
            a0 = -1.1 + 0.35 * hash01(k, sd, 5, 31)
            a1 = 1.75 - 0.4 * hash01(k, sd, 6, 37) - 0.15 * k
            out = np.maximum(out, brush_stroke((phi - a0) * r0, r - r0, (a1 - a0) * r0, 0.012 + 0.004 * hash01(k, sd, 7, 41), 300 + k + 10 * (sd > 0), dry=0.25) * on)
    return out


def leg_bands(P, f_leg, d_leg, outer):
    """Ink bands across the outer face of each leg."""
    out = np.zeros(len(P))
    for k, f0 in enumerate((0.3, 0.42, 0.55)):
        along = (outer + 0.05) * 1.0
        out = np.maximum(out, brush_stroke(along, (f_leg - f0) * 0.3, 0.1, 0.007, 70 + k, dry=0.4))
    return out


def tail_marks(P, tf, td):
    """Rings of ink round its tail, a few strokes not quite closing; and its brush: pale hairs, the tip dipped in ink."""
    out = np.zeros(len(P))
    L = float(arc_len_tail)
    ang = np.arctan2(P[:, 0] - np.array([path_at(TAIL, float(f)).x for f in tf]), P[:, 2] - np.array([path_at(TAIL, float(f)).z for f in tf]))
    for k, f0 in enumerate((0.16, 0.27, 0.38, 0.49, 0.6, 0.7, 0.79)):
        a0 = hash01(k, 3, 3, 23) * TAU
        along = ((ang - a0) % TAU) * 0.035
        out = np.maximum(out, brush_stroke(along, (tf - f0) * L, 0.035 * (TAU - 0.5 - 0.6 * hash01(k, 1, 1, 29)), 0.0085, 90 + k, dry=0.5))
    tip = smooth(0.9, 0.93, tf)                                   # the black tip
    return out, tip


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n = len(P)
    head = 1 - smooth(1.0, 1.2, np.linalg.norm((P - np.array((0.0, -0.37, 0.51))) / np.array((0.18, 0.16, 0.14)), axis=1))
    tf, td = nearest_on(TAIL, P)
    on_tail = (1 - smooth(0.0, 0.02, td - np.array([tail_radius(float(f)) for f in tf]) * 1.1)) * smooth(0.03, 0.08, tf)
    legs = []
    for key, sd, knots, radii in LEGS:
        f, d = nearest_on(leg_path(knots, sd), P)
        legs.append((key, sd, f, d))
    leg = np.zeros(n)
    leg_f = np.zeros(n)
    for key, sd, f, d in legs:
        near = (1 - smooth(0.06, 0.08, d)) * smooth(0.15, 0.3, f) * (x * sd > 0.02)
        take = near > leg
        leg = np.where(take, near, leg)
        leg_f = np.where(take, f, leg_f)
    leg = leg * smooth(0.27, 0.2, z)
    # fur: fine strands lying back along its body and down its legs
    hair = fbm(P * np.array([160.0, 40.0, 160.0]), 1.0, 3, 3) * (1 - leg) + fbm(P * np.array([160.0, 160.0, 40.0]), 1.0, 3, 5) * leg
    col = mix(np.broadcast_to(SILVER, (n, 3)), SILVER_COOL, smooth(0.35, 0.8, hair) * 0.5)
    # the ink wash along its back, its edge bleeding as ink does into wet paper
    bleed = (fbm(P, 22.0, 4, 7) - 0.5) * 0.35
    top = smooth(0.15, 0.75, Nn[:, 2] + bleed) * (1 - head * 0.6) * (1 - leg * 0.7)
    col = mix(col, WASH, top * 0.35)
    # bare paper beneath: belly, chest, throat, inner legs; its muzzle, chin and ruffs
    under = smooth(-0.1, -0.6, Nn[:, 2] + bleed * 0.5) * (1 - on_tail * 0.5)
    inner = np.zeros(n)
    for key, sd, f, d in legs:
        inner = np.maximum(inner, (1 - smooth(0.06, 0.08, d)) * smooth(0.0, -0.6, (Nn[:, 0] * sd)) * smooth(0.3, 0.15, z))
    face_white = np.zeros(n)
    for c, r in ((V(0, -0.47, 0.462), (0.074, 0.05, 0.056)), (V(0, -0.45, 0.425), (0.05, 0.05, 0.035))):      # its muzzle's white rising up its sides (white patches under its eyes read as blobs)
        face_white = np.maximum(face_white, 1 - smooth(0.85, 1.1, ell_dist(P, c, r) + bleed * 0.4))
    for sd in (1, -1):
        face_white = np.maximum(face_white, 1 - smooth(0.85, 1.1, ell_dist(P, V(sd * 0.13, -0.34, 0.43), (0.065, 0.075, 0.05)) + bleed * 0.4))      # the ruffs
        face_white = np.maximum(face_white, (1 - smooth(0.7, 1.1, ell_dist(P, V(sd * 0.062, -0.388, 0.586), (0.027, 0.02, 0.007)) + bleed * 0.6)))          # a thin white crescent over each eye
    col = mix(col, CREAM, smooth(0.05, -0.35, Nn[:, 2] + bleed * 0.5) * (1 - head) * 0.7)
    col = mix(col, RICE, np.clip(np.maximum.reduce([under, inner, face_white]), 0, 1))
    # the stripes: dry-brush ink
    ink = trunk_stripes(P, Nn) * (1 - head) * (1 - leg) * (1 - on_tail) * (1 - 0.85 * under)      # (a filter on its normals wiped them off its back)
    for key, sd, f, d in legs:
        outer = (P - np.array(tuple(path_at(leg_path(dict((kk, kn) for kk, _, kn, _ in LEGS)[key], sd), 0.5)))) @ np.array((sd, 0.0, 0.0))
        ink = np.maximum(ink, leg_bands(P, f, d, outer) * (1 - smooth(0.06, 0.075, d)) * smooth(0.0, 0.5, Nn[:, 0] * sd) * (x * sd > 0.03) * smooth(0.27, 0.22, z))     # (higher, they ran along its flank as a line through every stripe)
    tail_ink, tip = tail_marks(P, tf, td)
    ink = np.maximum(ink, tail_ink * on_tail)
    ink = np.maximum(ink, face_marks(P, Nn) * head)          # (unmasked, its cheek strokes ran on down its whole body as level lines across every stripe)
    col = mix(col, INK, np.clip(ink, 0, 1) * 0.94)
    col = mix(col, INK, tip * on_tail)                         # its tail's black tip
    seal = np.zeros(n)
    # paw pads
    pads = np.zeros(n)
    for key, sd, knots, radii in LEGS:
        c = np.array(tuple(mir(knots[3], sd) + V(0, -0.025, -0.04)))
        pads = np.maximum(pads, (1 - smooth(0.03, 0.045, np.linalg.norm((P - c) * np.array([1.0, 0.8, 2.0]), axis=1))) * smooth(-0.3, -0.7, Nn[:, 2]))
    col = mix(col, PAD, pads)
    # the mouth: a dark lip line under the muzzle
    # a tiger's mouth: a fine line down from its nose, then its black lips parting from it, out and down (one broad arc read as a sulk)
    lip_z = 0.451 - 0.28 * np.abs(x) - 3 * x ** 2
    lip = (1 - smooth(0.0018, 0.0038, np.abs(z - lip_z))) * (1 - smooth(0.042, 0.05, np.abs(x))) * (y < -0.44)
    philtrum = (1 - smooth(0.0012, 0.0026, np.abs(x))) * smooth(0.449, 0.452, z) * (1 - smooth(0.488, 0.492, z)) * (y < -0.46)
    lip = np.maximum(lip, philtrum * 0.85)
    col = mix(col, MOUTH, lip * 0.9)
    relief = (hair - 0.5) * 0.0008 - 0.0008 * lip
    set_verts(o, P + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.72 - 0.1 * smooth(0.45, 0.8, hair) - 0.3 * pads - 0.15 * seal, np.zeros(n))


arc_len_tail = float(np.sum([(TAIL[i + 1] - TAIL[i]).length for i in range(len(TAIL) - 1)]))


def face_marks(P, Nn):
    """The tiger's face in ink: the king's mark (王) on its brow; strokes across its cheek ruffs; lines from the outer corners of its eyes; rows of
    whisker spots; its eyes rimmed."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n = len(P)
    front = smooth(0.1, 0.5, -Nn[:, 1] + 0.3 * Nn[:, 2])
    out = np.zeros(n)
    # 王: three level strokes and one upright through them, on its brow
    z0, h = 0.614, 0.036
    brow = (y < -0.33) * front
    for k, (zz, half) in enumerate(((z0, 0.024), (z0 - h / 2, 0.018), (z0 - h, 0.026))):
        out = np.maximum(out, brush_stroke(x + half, z - zz, 2 * half, 0.0062, 200 + k, dry=0.15) * brow)
    out = np.maximum(out, brush_stroke(z0 + 0.004 - z, x, h + 0.008, 0.006, 210, dry=0.1) * brow)
    for sd in (1, -1):                                             # strokes radiating up from over each eye into its crown
        for k in range(3):
            X = x * sd
            x0 = 0.045 + 0.02 * k
            along = z - 0.592
            out = np.maximum(out, brush_stroke(along, (X - x0) - 0.35 * (z - 0.592), 0.05 - 0.008 * k, 0.0055, 260 + k + (sd > 0) * 10, dry=0.2) * (y < -0.3))
    for sd in (1, -1):
        X = x * sd
        # three strokes across each cheek ruff, slanting down and back
        for k in range(4):
            zz = 0.485 - 0.017 * k
            along = (X - 0.065) * 1.0
            out = np.maximum(out, brush_stroke(along, (z - zz) + 0.3 * (X - 0.065), 0.09, 0.0058, 220 + k + (sd > 0) * 10, dry=0.2) * (y > -0.44) * (X > 0.05))
        # a line from each eye's outer corner, back toward its ear
        along = X - 0.08
        out = np.maximum(out, brush_stroke(along, (z - 0.548) - 0.4 * (X - 0.08), 0.05, 0.004, 240 + (sd > 0), dry=0.3) * (X > 0.07) * (y > -0.41))
        # (a second set of crown strokes, fanning back, crossed those rising from the brow into X's)
        # its brow: a heavy ink stroke over each eye, under its white patch, falling toward its nose: the frown of a hunter (without it the white
        # patches sat over its eyes like raised eyebrows, and it looked worried)
        bx0, bz0, bx1, bz1 = 0.094, 0.585, 0.03, 0.563
        dx, dz = bx1 - bx0, bz1 - bz0
        ln = math.hypot(dx, dz)
        along = ((X - bx0) * dx + (z - bz0) * dz) / ln
        across = (-(X - bx0) * dz + (z - bz0) * dx) / ln
        out = np.maximum(out, brush_stroke(along, across, ln, 0.0055, 280 + (sd > 0), dry=0.1) * (y < -0.36) * front)
        # rows of whisker spots on each pad
        for k in range(3):
            for j in range(4):
                c = np.array((sd * (0.024 + 0.008 * j), -0.48 + 0.006 * j, 0.47 - 0.007 * k))
                out = np.maximum(out, 1 - smooth(0.0014, 0.0026, np.linalg.norm(P - c, axis=1)))
        # a dark tear line from each eye's inner corner down beside its nose, as a tiger's
        along = 0.545 - z
        out = np.maximum(out, brush_stroke(along, (X - 0.035) - 0.25 * (0.545 - z), 0.04, 0.0035, 270 + (sd > 0), dry=0.15) * (y < -0.4) * (X > 0.015))
        # its eyes rimmed in ink
        r = np.linalg.norm(P - np.array(tuple(mir(EYE_C, sd))), axis=1)
        out = np.maximum(out, smooth(EYE_R * 1.2, EYE_R * 1.08, r))            # (wider, they read as bruises)
    return out


def seal_mark(P, Nn):
    """The painter's seal: a small vermilion square on its left haunch, its glyph cut out in the paper's white."""
    c = np.array((0.125, 0.19, 0.30))
    u = (P[:, 1] - c[1]) / 0.022
    v = (P[:, 2] - c[2]) / 0.022
    on = (P[:, 0] > 0.06) * smooth(0.2, 0.6, Nn[:, 0])
    sq = (1 - smooth(0.92, 1.0, np.maximum(np.abs(u), np.abs(v)))) * on
    border = smooth(0.78, 0.84, np.maximum(np.abs(u), np.abs(v)))
    glyph = np.zeros(len(P))
    for (a, b, d) in (((-0.55, 0.45), (0.55, 0.45), 0.12), ((-0.55, -0.1), (0.55, -0.1), 0.12), ((0.0, 0.6), (0.0, -0.6), 0.12), ((-0.5, -0.55), (0.3, -0.55), 0.1)):
        A, B = np.array(a), np.array(b)
        q = np.stack([u, v], 1)
        t = np.clip(((q - A) @ (B - A)) / ((B - A) @ (B - A)), 0, 1)
        glyph = np.maximum(glyph, 1 - smooth(d * 0.6, d, np.linalg.norm(q - (A + t[:, None] * (B - A)), axis=1)))
    glyph = np.maximum(glyph, 1 - border) * 0 + glyph * (1 - border)
    return sq, glyph


def eye_paint(o, fr):
    """Moon-gold: pale gold at the pupil going to deeper amber at the rim, fine fibres, a round pupil, an ink rim."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(14, 12, 10), (len(px), 3)).copy()
    iris = mix(rgb(246, 226, 150), rgb(206, 150, 58), smooth(PUPIL * 1.1, IRIS, r))
    iris = mix(iris, iris * 0.7, smooth(-0.2, 0.8, py / IRIS) * 0.45)
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 36 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    col = mix(col, rgb(70, 50, 30), smooth(IRIS - 0.1, IRIS - 0.02, r) * (1 - smooth(IRIS, IRIS + 0.04, r)))
    col = mix(col, rgb(6, 6, 8), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def paint_all(pieces, frames):
    paint_skin(pieces["Skin"])
    paint_nose(pieces["Nose"])
    paint_whiskers(pieces["Whiskers"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.12, 0.3)
FACE_AT = (0, -0.42, 0.5)
EXTRA = [(0, -1, 0.05, 0.7, FACE_AT), (0.62, -0.75, 0.2, 0.7, FACE_AT), (1, -0.12, 0.08, 0.7, FACE_AT), (0.3, -0.9, 0.2, 0.32, tuple(EYE_C)),
         (0.7, 0.5, 0.4, 1.2, (0.05, 0.7, 0.25)), (0.4, -0.9, -0.1, 0.4, (0, -0.47, 0.44))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.32, 0.34, 0.42, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.05, 0.04, 0.03, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    only = [int(k) for k in ARGS[ARGS.index("views") + 1].split(",")] if "views" in ARGS else None
    allv = VIEWS + EXTRA
    shots(os.path.join(REVIEW, STAGE), [allv[k] for k in only] if only else allv, target=VIEW_AT, dist=3.0, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3600
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 3.0, "LidUR": 3.0, "LidLL": 2.0, "LidLR": 2.0, "Nose": 3.0, "EarL": 1.4, "EarR": 1.4, "Whiskers": 0.6}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(lows["Skin"], P)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 8, 8, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low", lift=0.002)
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low", lift=0.002)
    lows["Nose"] = build_nose(N + "NoseLow", GAME, 14, 10)
    lows["Whiskers"] = build_whiskers(N + "WhiskersLow", GAME, 4, 2)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Shoulders", SPINE[4], "Chest"),
               ("Neck", NECK[0], "Shoulders"), ("Head", NECK[-1], "Neck"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 8)]
TAIL_F = (0.03, 0.17, 0.31, 0.45, 0.6, 0.75, 0.88)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw" + key] for key, _, _, _ in LEGS}
HEAD_ZONE = (V(0, -0.375, 0.5), (0.16, 0.16, 0.13))


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots):
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
    """The skin's weights: the trunk (hips to head), the head with its muzzle and ruffs, the tail, the legs; a paw and its toes wholly its paw's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    head_d = ell_dist(P, HEAD_ZONE[0], HEAD_ZONE[1])
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
            if (Vector(P[i]) - (mir(knots_l[3], side) + V(0, -0.03, -0.01))).length < 0.085 and z < 0.075:
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
            outer = lr * (1.15 + 0.3 * float(smooth(0.4, 0.1, f[i])))     # (reaching further, mid-belly skin took both a fore and a hind leg, and tore as they swung apart)
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            # at belly height (from just under the elbow or knee up) every leg share fades smoothly toward the midline, and along the body away from
            # the top of its leg: its deep belly hangs to its elbows and knees, and its short body put the fore and hind legs' zones side by side
            # mid-flank; skin given to a leg there, beside the trunk's or the other leg's, split as the legs swung apart (measured: 9 cm). Blended in
            # by height, not switched on, or the switch itself became the seam.
            bz = float(smooth(knots_l[1].z - 0.075, knots_l[1].z - 0.01, z))
            fade = float(smooth(0.0, 0.1, x * side)) * float(smooth(0.16, 0.06, abs(y - knots_l[0].y)))
            mm *= 1 - bz * (1 - fade)
            if mm > 0:
                w = blend(w, chain_weight(LEG_NAMES[key], leg_mids(knots_l), float(f[i])), mm)
        out.append(w)
    return out


def relax_weights(mesh, w, rounds=4, keep=0.5):
    """Each vertex's weights eased toward its neighbours' a few times: where two rules meet (the haunch behind the thigh, nearest now the thigh,
    now the shin) their shares jumped from one vertex to the next, and that step tore as the leg folded (measured: 7 cm lying down)."""
    nb = [[] for _ in w]
    for e in mesh.data.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    for _ in range(rounds):
        new = []
        for i, wi in enumerate(w):
            if not nb[i] or max(wi.values()) >= 0.999 and all(w[j] == wi for j in nb[i]):
                new.append(wi)
                continue
            out = {k: v * keep for k, v in wi.items()}
            share = (1 - keep) / len(nb[i])
            for j in nb[i]:
                for k, v in w[j].items():
                    out[k] = out.get(k, 0) + v * share
            new.append(out)
        w = new
    return w


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], relax_weights(lows["Skin"], body_weights(verts(lows["Skin"]))))
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Nose"], "Head")
    rigid(lows["Whiskers"], "Head")
    rigid(glows["Fangs"], "Head")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses, in the game's axes: +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def legs4(f, b):
    """Both forelegs f = (upper, fore, wrist) and both hind legs b = (thigh, shin, hock), the same on each side; each paw turned back level."""
    out = {}
    for side in "LR":
        for k in range(3):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, 0)
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, 0)
        out["PawF" + side] = (-sum(f), 0, 0)
        out["PawB" + side] = (-sum(b), 0, 0)
    return out


def paw_at(rig, key):
    pb = rig.pose.bones["Paw" + key]
    return rig.matrix_world @ pb.head


def solve_legs(rig, base, front_target, back_target, start_f=(0, 0, 0), start_b=(0, 0, 0)):
    """Leg turns (upper, middle, lower, the same each side) that put each paw where it should be with the trunk posed as base: a small simplex search on
    the bones (the skin follows them)."""
    def cost(xs, front):
        f = tuple(xs) if front else (0, 0, 0)
        b = (0, 0, 0) if front else tuple(xs)
        pose(rig, spec({**base, **legs4(f if front else start_f, b if not front else start_b)}))
        p = paw_at(rig, "FL" if front else "BL")
        t = front_target if front else back_target
        return (p.z - t[1]) ** 2 * 4 + (p.y - t[0]) ** 2 + 0.0004 * sum(x * x for x in xs)

    def simplex(fn, x0, steps=260):
        pts = [np.array(x0, dtype=float)] + [np.array(x0, dtype=float) + np.eye(3)[k] * 0.4 for k in range(3)]
        vals = [fn(p) for p in pts]
        for _ in range(steps):
            order = np.argsort(vals)
            pts = [pts[i] for i in order]
            vals = [vals[i] for i in order]
            c = sum(pts[:-1]) / 3
            r = c + (c - pts[-1])
            fr = fn(r)
            if fr < vals[0]:
                e = c + 2 * (c - pts[-1])
                fe = fn(e)
                pts[-1], vals[-1] = (e, fe) if fe < fr else (r, fr)
            elif fr < vals[-2]:
                pts[-1], vals[-1] = r, fr
            else:
                k = c + 0.5 * (pts[-1] - c)
                fk = fn(k)
                if fk < vals[-1]:
                    pts[-1], vals[-1] = k, fk
                else:
                    pts = [pts[0] + 0.5 * (p - pts[0]) for p in pts]
                    vals = [fn(p) for p in pts]
        i = int(np.argmin(vals))
        return pts[i], vals[i]
    f, cf = simplex(lambda xs: cost(xs, True), start_f)
    start_f = tuple(f)
    b, cb = simplex(lambda xs: cost(xs, False), start_b)
    return tuple(round(float(v), 3) for v in f), tuple(round(float(v), 3) for v in b), cf, cb


def lowest_of(body, parts):
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


GROUND_PARTS = {"FrontPaws": ("PawFL", "PawFR"), "HindPaws": ("PawBL", "PawBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",), "Tail": tuple(TAIL_NAMES),
                "Head": ("Head",)}

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames)
    if STAGE == "all":
        unwrap(lows, [(lambda p: p.center.y < -0.3 and p.center.z > 0.38, 2.0), (None, 1.0)], SCALES, margin=0.009)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.85, 0.5, 0.18, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.01, 0.025),
                 reaches={"Whiskers": (0.002, 0.006)})
    else:
        clay = bpy.data.materials.new("clay")
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    print("SKIN GAP (low from high, m)", round(surface_gap(lows["Skin"], data["tree"]), 4), flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0046, 10), (22, -18, 0.0022, 6))), "Fangs": build_fangs(GAME, 6, 3)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    bottom = min(lo, -0.025)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE (box middle with the RootPart, down to the paws)", round((hi + bottom) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Hips", "Head", "Tail7"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    vs = [v.co for v in glows["Fangs"].data.vertices]
    print("FANGS centre game axes", (0.0, round(sum(v.z for v in vs) / len(vs), 4), round(sum(v.y for v in vs) / len(vs), 4)), flush=True)
    RIG = {"body": body, "rig": rig, "frames": frames, "glows": glows}


# ---------- its stances: the legs found by the solver so the paws stay planted, then checked on the mesh ----------
CROUCH_DROP, LIE_DROP = 0.085, 0.105            # (at 0.17 its deep belly sank 6 cm into the ground)


def find_stances(rig):
    pose(rig, {})
    rest_f, rest_b = paw_at(rig, "FL"), paw_at(rig, "BL")
    out = {}
    # the stalk before a pounce: low, shoulders down, head level and forward, every paw where it stood
    base = {"Hips": (0, 0, 0, (0, -CROUCH_DROP, 0)), "Shoulders": (-0.04, 0, 0), "Head": (0.12, 0, 0)}
    f, b, cf, cb = solve_legs(rig, base, (rest_f.y, rest_f.z), (rest_b.y, rest_b.z), (-0.3, -0.8, 0.3), (0.3, -0.5, 0.6))
    out["CROUCH"] = ({**base, **legs4(f, b)}, cf, cb)
    # lying down: forepaws stretched out in front, hind legs folded under it
    base = {"Hips": (-0.05, 0, 0, (0, -LIE_DROP, 0)), "Shoulders": (0.08, 0, 0), "Head": (0.1, 0, 0), "Tail1": (-0.25, 0.35, 0), "Tail2": (0.05, 0.35, 0), "Tail3": (0.05, 0.3, 0)}
    f, b, cf, cb = solve_legs(rig, base, (rest_f.y - 0.1, rest_f.z - 0.004), (rest_b.y - 0.07, rest_b.z), (0.4, 0.6, -0.5), (0.4, -1.2, 0.2))
    out["LIE"] = ({**base, **legs4(f, b)}, cf, cb)
    return out


# ---------- its walk: a prowl, each paw sliding back flat on the ground, then lifted and swung forward; the leg turns found by the solver at each
# step of the cycle (the game reads them off this table, one leg after another: hind, fore, hind, fore, as a big cat walks) ----------
WALK_N, WALK_DUTY, WALK_REACH = 16, 0.62, 0.075      # steps in a cycle; its share of it on the ground; half a stride, metres
WALK_LIFT = {"F": 0.05, "B": 0.042}                 # how high each paw clears the ground at the top of its swing
WALK_LEAD = {"BL": 0.0, "FL": 0.25, "BR": 0.5, "FR": 0.75}


def walk_path(t):
    """Where a paw is, from where it stands, at t through the cycle: (along, metres, + back; up, as a share of its lift)."""
    if t < WALK_DUTY:
        return -WALK_REACH + 2 * WALK_REACH * t / WALK_DUTY, 0.0
    s = (t - WALK_DUTY) / (1 - WALK_DUTY)
    return WALK_REACH - 2 * WALK_REACH * (0.5 - 0.5 * math.cos(math.pi * s)), math.sin(math.pi * s)


def find_walk(rig):
    pose(rig, {})
    rf, rb = paw_at(rig, "FL"), paw_at(rig, "BL")
    rows, sf, sb = [], (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    for k in range(WALK_N + 1):                       # (the first step solved twice: warm-started from the last, so the cycle closes)
        dy, up = walk_path((k % WALK_N) / WALK_N)
        f, b, cf, cb = solve_legs(rig, {}, (rf.y + dy, rf.z + up * WALK_LIFT["F"]), (rb.y + dy, rb.z + up * WALK_LIFT["B"]), sf, sb)
        sf, sb = f, b
        if k < WALK_N:
            rows.append((f, b, cf, cb))
        else:
            rows[0] = (f, b, cf, cb)
    return rows


def walk_table(rows, g):
    """Every leg at g through the cycle (each at its own lead), its paw turned back level."""
    out = {}
    for key, lead in WALK_LEAD.items():
        t = ((g + lead) % 1.0) * WALK_N
        i, w = int(t) % WALK_N, t - int(t)
        a, c = rows[i][0 if key[0] == "F" else 1], rows[(i + 1) % WALK_N][0 if key[0] == "F" else 1]
        ang = [a[j] * (1 - w) + c[j] * w for j in range(3)]
        for j in range(3):
            out["Leg%s%d" % (key, j + 1)] = (ang[j], 0, 0)
        out["Paw" + key] = (-sum(ang), 0, 0)
    return out


POUNCE = {"Hips": (-0.1, 0, 0), "Shoulders": (-0.12, 0, 0), "Head": (0.1, 0, 0), **legs4((0.6, -0.2, -0.25), (-0.45, 0.32, -0.08)),
          **{n: (-0.06, 0, 0) for n in TAIL_NAMES}}
STALK_HEAD = {"Neck": (-0.12, 0, 0), "Head": (0.18, 0, 0)}
EARS_BACK = {"EarL": (-0.4, 0.3, 0), "EarR": (-0.4, -0.3, 0)}
# in the air (its owner flying): stretched out in a leap, forelegs reaching, hind legs thrown back, tail streaming
LEAP = {"Body": (0.05, 0, 0), "Head": (-0.05, 0, 0), **legs4((0.75, -0.35, -0.2), (-0.75, 0.25, 0.05)), **{n: (-0.05, 0, 0) for n in TAIL_NAMES}}
# its glare up at the moon after the strike: head high, ears back
MOON_GLARE = {"Shoulders": (0.06, 0, 0), "Neck": (0.28, 0, 0), "Head": (0.32, 0, 0), **EARS_BACK}
DOZE_HEAD = {"Neck": (-0.14, 0, 0), "Head": (-0.2, 0.15, 0.06)}             # lying, its head sunk on its paws


def pose_library(frames, stances):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    stride = {"LegFL1": (0.45, 0, 0), "LegFL2": (-0.5, 0, 0), "LegFR1": (-0.35, 0, 0), "LegBL1": (-0.45, 0, 0), "LegBR1": (0.4, 0, 0), "LegBR2": (-0.6, 0, 0),
              "Shoulders": (0, 0.06, 0), "Hips": (0, -0.05, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Stride": spec(stride), "Crouch": spec(stances["CROUCH"][0]), "Lie": spec(stances["LIE"][0]),
            "Pounce": spec(POUNCE), "Look": spec({"Neck": (0.1, 0.4, 0), "Head": (0.15, 0.5, 0.1)}), "Tail": spec({n: (0.06, 0.15, 0) for n in TAIL_NAMES}),
            "Ears": spec(EARS_BACK), "Snarl": spec({"Neck": (0.2, 0, 0), "Head": (0.35, 0, 0)}),
            "Leap": spec(LEAP), "Stalk": spec({**stances["CROUCH"][0], **STALK_HEAD, **EARS_BACK}), "Glare": spec(MOON_GLARE),
            "Doze": spec({**stances["LIE"][0], **DOZE_HEAD}), "LungeStalk": spec({**POUNCE, **STALK_HEAD, **EARS_BACK})}


POSE_VIEWS = [(1, -0.05, 0.08, 3.6, VIEW_AT), (0.62, -0.72, 0.25, 3.6, VIEW_AT)]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    body, rig, frames, glows = RIG["body"], RIG["rig"], RIG["frames"], RIG["glows"]
    stances = find_stances(rig)
    for name, (table, cf, cb) in stances.items():
        print("STANCE", name, "fit", round(cf, 6), round(cb, 6), "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in (v[:3] + (tuple(v[3]) if len(v) > 3 else ())))) for b, v in sorted(table.items())) + " }", flush=True)
    lib = pose_library(frames, stances)
    walk = find_walk(rig)
    print("WALK fit worst", max(r[2] for r in walk), max(r[3] for r in walk), flush=True)
    print("WALK_FRONT = { " + ", ".join("{ %g, %g, %g }" % r[0] for r in walk) + " }", flush=True)
    print("WALK_HIND = { " + ", ".join("{ %g, %g, %g }" % r[1] for r in walk) + " }", flush=True)
    for k in range(8):
        lib["Walk%d" % k] = spec(walk_table(walk, k / 8))
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    for name in ("Crouch", "Lie", "Pounce", "Stride", "Leap", "Stalk", "Glare", "Doze") + tuple("Walk%d" % k for k in range(8)):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
        if "shots" in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=420)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.0, size=560)
        for name in ("Crouch", "Lie", "Pounce", "Snarl", "Blink", "Leap", "Stalk", "Glare", "Doze"):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS, size=420)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.25, 3.2, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

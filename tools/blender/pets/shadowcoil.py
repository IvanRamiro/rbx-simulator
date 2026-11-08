"""The Shadowcoil (Rare, Shadow; Forbidden Origin Egg, also in the Void Rift Egg): "A loop of living shadow that hides under your own. You find out it is
there when it moves first."

A shadow stoat, in the stylized look the owner chose for the Eclipse Cat but in its own design language: S-curves, loops and smoke. A long, sinuous, low
body on short legs; a big round head with rounded ears, big eyes of pale mint-silver eyeshine with a round pupil under real lids, a small slate nose, two
pale brow spots. Ink-black fur, with soft wisps of smoke at its nape, cheeks, throat, elbows and hocks; its long tail is one bushy volume of swirling smoke,
soft ridges twisting along it, black at the root and drifting to dusky lavender-grey at the tip, coiling up into a spiral with smoke trailing off its point.
Pale mint-silver toe tips.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/shadowcoil.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, paws on z = 0. +X is its left. The maps go to assets/pets/ForbiddenOriginEgg/.

What touches what: body, legs, neck, head and tail are one fused skin; the wisps grow from inside it; the eyes sit in their sockets under their lids, the
glints on the eyes under the lids' reach; the ears and the nose are their own pieces set into the head.
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
PET = "Shadowcoil"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ForbiddenOriginEgg")

# ---------- colours: ink, smoke, eyeshine ----------
INK, INK_SHEEN, BELLY = rgb(14, 13, 20), rgb(44, 46, 64), rgb(36, 34, 48)
SMOKE_MID, SMOKE_TIP = rgb(52, 48, 70), rgb(150, 138, 178)
MINT, MINT_PALE = rgb(150, 214, 200), rgb(222, 246, 238)
NOSE_COL, NOSE_LIT, MOUTH = rgb(64, 62, 78), rgb(132, 130, 150), rgb(6, 5, 10)
EAR_IN, BROW = rgb(84, 76, 104), rgb(176, 168, 204)
GLINT_HEX = "ffffff"

# ---------- the frame of it ----------
SPINE = [V(0, 0.27, 0.19), V(0, 0.17, 0.205), V(0, 0.06, 0.212), V(0, -0.05, 0.212), V(0, -0.15, 0.22), V(0, -0.23, 0.25), V(0, -0.3, 0.31), V(0, -0.37, 0.37),
         V(0, -0.47, 0.35)]
BODY_PATH = catmull(SPINE[:8], 10)          # rump to inside the head: the neck flows into it
BODY_W = ((0, 0.075), (0.12, 0.09), (0.33, 0.08), (0.52, 0.088), (0.68, 0.082), (0.82, 0.066), (1, 0.06))
BODY_H = ((0, 0.076), (0.12, 0.088), (0.33, 0.078), (0.52, 0.092), (0.68, 0.084), (0.82, 0.066), (1, 0.06))
HEAD = V(0, -0.375, 0.375)
HEAD_R = (0.092, 0.084, 0.08)
TAIL = catmull([V(0, 0.29, 0.21), V(0, 0.39, 0.25), V(0.01, 0.48, 0.33), V(0.02, 0.52, 0.45), V(0.02, 0.47, 0.56), V(0.015, 0.38, 0.58), V(0.01, 0.32, 0.51),
                V(0.01, 0.35, 0.44)], 10)
TAIL_PROFILE = ((0, 0.042), (0.15, 0.06), (0.45, 0.08), (0.75, 0.062), (0.92, 0.032), (1, 0.004))     # the tail's radius along it: swelling, then a flame's point
TAIL_LOBES, TAIL_LOBE_DEPTH, TAIL_TWIST = 4, 0.2, 5 * math.pi     # soft ridges spiralling along it: swirling smoke
FRONT = [V(0.055, -0.16, 0.19), V(0.058, -0.15, 0.11), V(0.056, -0.17, 0.05), V(0.056, -0.18, 0.03), V(0.056, -0.19, 0.022)]
HIND = [V(0.062, 0.2, 0.18), V(0.068, 0.14, 0.11), V(0.064, 0.21, 0.06), V(0.062, 0.2, 0.03), V(0.062, 0.19, 0.022)]
FRONT_R = [0.044, 0.034, 0.029, 0.027, 0.026]
HIND_R = [0.056, 0.04, 0.03, 0.027, 0.026]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.031
EYE_C = V(0.05, -0.434, 0.392)
EYE_AXIS = V(0.42, -0.9, 0.1).normalized()
LID_UP, LID_LOW = (48.0, 120.0, 0.003), (-40.0, -128.0, 0.0024)      # wide and alert
LID_TILT = 10.0
BLINK_U, BLINK_L = 62.0, 28.0          # together more than the opening's 88 degrees: shut
IRIS, PUPIL = 0.9, 0.36                 # on the eye's face (its front is 1)
NOSE_TOP, NOSE_BASE_Y = 0.368, -0.47    # the nose's top edge (z) and how far back its body sits (y)


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


# ---------- the skin ----------
def loft_body(m, rows_per=1):
    """The long body: an ellipse lofted along the spine from the rump to the top of the neck, widest at the chest, a waist behind it."""
    path = BODY_PATH
    fr = path_frames(path)
    nt = 48
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        w, h = prof(BODY_W, f), prof(BODY_H, f)
        rings.append([m.bm.verts.new(p + side * (w * math.cos(TAU * k / nt)) + up * (h * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


def tail_radius(f):
    return prof(TAIL_PROFILE, f)


def tail_lobe(theta, f):
    """1 on a ridge of the swirl, -1 in a hollow."""
    return math.cos(TAIL_LOBES * theta + TAIL_TWIST * f)


def loft_tail(m, nt=48):
    """The tail: one bushy volume of swirling smoke, its soft ridges twisting along it, drawn to a curling point."""
    fr = path_frames(TAIL)
    rings = []
    for i, p in enumerate(TAIL):
        f = i / (len(TAIL) - 1)
        tan, side, up = fr[i]
        r = tail_radius(f)
        ring = []
        for k in range(nt):
            th = TAU * k / nt
            rr = r * (1 + TAIL_LOBE_DEPTH * tail_lobe(th, f))
            ring.append(m.bm.verts.new(p + side * (rr * math.cos(th)) + up * (rr * math.sin(th))))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


def tail_coords(P):
    """Per point: how far along the tail (0..1), how far from its line, and the swirl's value there (1 on a ridge)."""
    f, d = nearest_on(TAIL, P)
    fr = path_frames(TAIL)
    idx = np.clip(np.round(f * (len(TAIL) - 1)).astype(int), 0, len(TAIL) - 1)
    side = np.array([tuple(fr[i][1]) for i in idx])
    up = np.array([tuple(fr[i][2]) for i in idx])
    rel = P - np.array([tuple(TAIL[i]) for i in idx])
    theta = np.arctan2((rel * up).sum(1), (rel * side).sum(1))
    return f, d, np.cos(TAIL_LOBES * theta + TAIL_TWIST * f)


def build_skin():
    core = Mesh()
    loft_body(core)
    core.ball(SPINE[0] + V(0, 0.01, 0), (0.072, 0.07, 0.072))     # the round of the rump
    core.ball(HEAD, HEAD_R, 56, 36)                                # the skull: big and round
    core.ball(V(0, -0.395, 0.41), (0.075, 0.062, 0.056))          # the forehead
    core.ball(V(0, -0.45, 0.352), (0.028, 0.03, 0.022))           # the muzzle, short and neat
    core.ball(V(0, -0.447, 0.336), (0.017, 0.02, 0.013))          # the chin
    for side in (1, -1):
        core.ball(V(side * 0.052, -0.41, 0.355), (0.05, 0.052, 0.046))     # the cheek
        core.ball(V(side * 0.013, -0.459, 0.346), (0.015, 0.013, 0.011))   # the whisker pad
        core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        core.ball(V(side * 0.046, -0.41, 0.414), (0.038, 0.042, 0.03))     # behind the lids: their hidden edges stay under it
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.006, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    thin = Mesh()
    for key, side, knots, radii in LEGS:
        thin.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=20, flat=0.9, plane=V(1, 0, 0))
        paw = mir(knots[4], side)
        thin.ball(paw + V(0, -0.01, 0.002), (0.033, 0.042, 0.021), 24, 14)          # the paw, small and neat
        for k in range(4):
            a = (k - 1.5) * 0.45
            thin.ball(paw + V(math.sin(a) * 0.023, -0.042 - math.cos(a) * 0.006, 0.004), (0.012, 0.013, 0.012), 14, 10)
    loft_tail(thin)
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


# ---------- wisps of smoke ----------
def wisp_profile(width, round_tip):
    """A wisp's radius along it: a flame drawn to a fine point, or a soft clump ending in a dome."""
    if round_tip:
        return lambda f: width * (0.82 + 0.18 * min(1.0, f / 0.45)) * math.sqrt(max(0.0, 1 - max(0.0, (f - 0.45) / 0.55) ** 2)) + 0.0011
    return lambda f: width * math.sin(math.pi * (0.22 + 0.78 * f)) ** 0.55 * (1 - f) ** 0.35 + 0.0011


def wisp(m, root, direction, length, width, normal, bend=V(0, 0, 0), roll=0.0, sides=6, per=5, flat=0.42, round_tip=False):
    """A wisp of smoke (or a soft clump of it): curling, flat against the body, turned roll about its length."""
    d = direction.normalized()
    n = normal - d * normal.dot(d)
    n = n.normalized() if n.length > 1e-6 else d.orthogonal().normalized()
    plane = (n * math.cos(roll) + d.cross(n).normalized() * math.sin(roll)).normalized()
    pts = [root - d * 0.008, root + d * (length * 0.45) + bend * 0.35, root + d * length + bend]
    m.tube(catmull(pts, per), wisp_profile(width, round_tip), sides=sides, flat=flat, plane=plane)


def wisp_list(tree):
    """Every wisp: root, direction, length, width, the skin's normal there, bend, roll. The mane at the nape, the smoke off the tail's point, the cheeks,
    the bib, the elbows and hocks."""
    out = []
    rng = np.random.default_rng(11)

    def cast(origin, toward):
        hit = tree.ray_cast(origin, (toward - origin).normalized(), 1.0)
        return (hit[0], hit[1]) if hit[0] is not None else (None, None)

    def add(loc, nrm, d, length, width, bend, round_tip=False):
        out.append((loc, d.normalized(), length, width, nrm, bend, (rng.random() - 0.5) * 1.1, round_tip))
    # a soft mane of smoke at the nape, lying back along the neck
    for k in range(6):
        f = 0.74 + 0.16 * k / 5
        c = path_at(BODY_PATH, f)
        lean = 0.016 * (1 if k % 2 else -1)
        loc, nrm = cast(c + V(lean, 0, 0.4), c + V(lean, 0, 0))
        if loc is not None:
            back = (path_at(BODY_PATH, f - 0.03) - path_at(BODY_PATH, f + 0.03)).normalized()
            add(loc, nrm, nrm * 0.35 + back + V(lean * 5, 0, 0), 0.055 + 0.01 * rng.random(), 0.03, -nrm * 0.01)
    # smoke trailing off the tail's point
    tip, tan = TAIL[-1], (TAIL[-1] - TAIL[-3]).normalized()
    side_ax = tan.cross(V(0, 0, 1)).normalized() if abs(tan.z) < 0.95 else V(1, 0, 0)
    up_ax = side_ax.cross(tan).normalized()
    for j, (sx, sz) in enumerate(((0.35, 0.25), (-0.35, -0.2), (0.2, -0.35))):
        d = (tan + side_ax * sx + up_ax * sz).normalized()
        add(tip - tan * 0.03, up_ax, d, 0.085 - 0.012 * j, 0.016, up_ax * 0.016 + side_ax * (0.012 * (1 if j % 2 else -1)))
    # the cheeks: soft fluff flaring out and back
    for side in (1, -1):
        for k, (dz, ang) in enumerate(((0.015, 0.1), (-0.005, 0.35), (-0.025, 0.6), (0.0, -0.1))):
            target = V(side * 0.02, -0.4, 0.36 + dz)
            loc, nrm = cast(target + V(side * math.cos(ang) * 0.4, math.sin(ang) * 0.1 + 0.05, -0.04), target)
            if loc is not None:
                add(loc, nrm, nrm * 0.45 + V(side * 0.85, 0.45, -0.2 - 0.15 * k), 0.045 + 0.01 * rng.random(), 0.026, V(0, 0.01, 0.008))
    # the bib under the throat
    for k in range(4):
        a = math.radians(-45 + 90 * k / 3)
        c = V(0, -0.26, 0.255)
        loc, nrm = cast(c + V(math.sin(a) * 0.4, -math.cos(a) * 0.4, -0.05), c)
        if loc is not None:
            add(loc, nrm, nrm * 0.55 + V(0, -0.1, -1), 0.036, 0.026, nrm * 0.012)
    # the elbows and the hocks: a wisp trailing back from each
    for side in (1, -1):
        for knots, zf in ((FRONT, 1), (HIND, 2)):
            t = mir(knots[zf], side)
            loc, nrm = cast(t + V(side * 0.1, 0.4, 0.02), t)
            if loc is not None:
                add(loc, nrm, nrm * 0.4 + V(side * 0.2, 1.0, -0.3), 0.04, 0.018, nrm * 0.006)
    return out


def build_wisps(tree, name, coll, sides=6, per=5):
    m = Mesh()
    meta = []
    for loc, d, length, width, nrm, bend, roll, round_tip in wisp_list(tree):
        before = len(m.bm.verts)
        wisp(m, loc, d, length, width, nrm, bend, roll, sides, per, flat=0.62 if round_tip else 0.42, round_tip=round_tip)
        count = len(m.bm.verts) - before
        meta += [((i // sides) / max(1, count // sides - 1), tuple(loc)) for i in range(count)]
    return m.finish(name, coll), meta


# ---------- ears and nose ----------
EAR = {"front": V(0.046, -0.365, 0.437), "back": V(0.094, -0.322, 0.418), "height": 0.064}


def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    up = (V(side * 0.35, 0.1, 1) - along * V(side * 0.35, 0.1, 1).dot(along)).normalized()
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n          # facing forward
    return A, B, C, along, up, n


def ear_point(side):
    """A rounded ear: its base along the head, its rim an arc over the top; u from the base to the rim, v across. The rim reaches a little past the base
    at both ends, so no row of the sheet is drawn to a point."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        rim = C + along * (-math.cos(math.pi * v) * a * 1.15) + up * (math.sin(math.pi * v) * EAR["height"] + 0.012)
        p = base.lerp(rim, u)
        cup = 0.014 * math.sin(math.pi * v) * math.sin(math.pi * min(1.0, u * 1.1))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return 0.008 * (1 - u) ** 0.7 + 0.0026


def build_ear(side, name):
    """Black behind, the hollow a smoky lavender-grey, a faint pale rim."""
    o = sheet_hi(ear_point(side), ear_thick, 70, 70, name, lambda u, v: np.broadcast_to(INK, (len(u), 3)), lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    nu, nv = 70, 70
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
    col = mix(np.broadcast_to(INK, (len(uu), 3)), mix(EAR_IN * 0.5, EAR_IN, smooth(0.35, 0.08, edge)), inside * smooth(0.04, 0.09, edge))
    col = mix(col, MINT_PALE * 0.55, 1 - smooth(0.012, 0.03, edge))
    paint(o, col, np.full(len(uu), 0.6), np.zeros(len(uu)))
    return o


def nose_point(sx, sy, sz):
    """A small rounded nose from the unit sphere: wider at the top, narrowing to a soft point below, its front pushed forward, its back set into the muzzle."""
    t = (1 - sz) / 2
    w = 0.012 * (1 - t) ** 0.7 + 0.0016
    depth = (0.006 + 0.005 * t) if sy < 0 else 0.006
    return V(sx * w, NOSE_BASE_Y + sy * depth, NOSE_TOP - 0.015 * t - 0.0016 * math.exp(-(sx / 0.32) ** 2) * max(0.0, sz) ** 3)


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
        c = np.array((side * 0.0048, NOSE_BASE_Y - 0.008, NOSE_TOP - 0.011))
        nostril = np.maximum(nostril, 1 - smooth(0.0012, 0.0024, np.linalg.norm((P - c) * np.array([1.0, 1.6, 0.8]), axis=1)))
    col = mix(col, MOUTH, nostril)
    paint(o, col, 0.3 + 0.4 * nostril, np.zeros(len(P)))


# ---------- paint ----------
def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # short hair lying back along the body and down the legs, a cool sheen where it faces up
    hair_body = fbm(P * np.array([170.0, 45.0, 170.0]), 1.0, 3, 3)
    hair_leg = fbm(P * np.array([170.0, 170.0, 45.0]), 1.0, 3, 5)
    leg = smooth(0.16, 0.11, z)
    fur = hair_body * (1 - leg) + hair_leg * leg
    col = mix(INK, INK * 1.8, smooth(0.45, 0.8, fur) * 0.7)
    col = mix(col, INK_SHEEN, smooth(0.2, 0.9, Nn[:, 2]) * 0.4)
    # the tail: black where it leaves the body, smoke toward its point; the swirl's ridges lit, its hollows ink
    tf, td, lobe = tail_coords(P)
    on_tail = (1 - smooth(0.0, 0.03, td - np.array([tail_radius(float(f)) * (1 + TAIL_LOBE_DEPTH) for f in tf]))) * smooth(0.02, 0.1, tf)
    smoke = mix(mix(INK, SMOKE_MID, smooth(0.05, 0.6, tf)), SMOKE_TIP, smooth(0.55, 1.0, tf) * 0.8)
    smoke = mix(smoke, smoke * 0.45, smooth(0.2, -0.8, lobe) * 0.8)
    smoke = mix(smoke, SMOKE_TIP * 1.1, smooth(0.55, 0.95, lobe) * smooth(0.15, 0.6, tf) * 0.55)
    col = mix(col, smoke, on_tail)
    # smoke drifting over its back and flanks: faint lighter wreaths, drifting back toward the tail
    drift = fbm(np.stack([y * 6.0 + np.sin(z * 30.0) * 0.4, z * 9.0, x * 9.0], 1), 1.0, 4, 13)
    wreath = smooth(0.58, 0.74, drift) * smooth(0.15, 0.2, z) * smooth(-0.3, 0.3, y + 0.25) * (1 - on_tail)
    col = mix(col, SMOKE_MID * 1.2, wreath * 0.6)
    col = mix(col, BELLY, smooth(-0.3, -0.8, Nn[:, 2]) * smooth(0.12, 0.17, z) * 0.6)
    # the toe tips: pale mint-silver
    toes = np.zeros(len(P))
    for key, side, knots, radii in LEGS:
        paw = np.array(tuple(mir(knots[4], side) + V(0, -0.046, 0.004)))
        toes = np.maximum(toes, 1 - smooth(0.012, 0.024, np.linalg.norm(P - paw, axis=1)))
    col = mix(col, MINT, toes * 0.8)
    # the face: two pale brow spots over the eyes, the mouth's line
    brows = np.zeros(len(P))
    for side in (1, -1):
        c = np.array((side * 0.048, -0.43, 0.437))
        brows = np.maximum(brows, 1 - smooth(0.0055, 0.0085, np.linalg.norm((P - c) * np.array([1.0, 1.4, 1.3]), axis=1)))
    col = mix(col, BROW, brows)
    philtrum = (np.abs(x) < 0.0016) * (z < 0.355) * (z > 0.34) * (y < -0.462)
    lip = (1 - smooth(0.0012, 0.003, np.abs(z - (0.337 + 9 * x ** 2)))) * (np.abs(x) < 0.018) * (y < -0.45)
    mouth = np.clip(philtrum + lip, 0, 1)
    col = mix(col, MOUTH, mouth * 0.9)
    relief = (fur - 0.5) * 0.0004 - 0.0008 * mouth
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.66 - 0.1 * smooth(0.45, 0.8, fur) - 0.2 * toes, np.zeros(len(P)))


def paint_wisps(o, along):
    """Black at the root, drifting through smoke to a dusky lavender-grey at the tip."""
    P = verts(o)
    col = mix(INK, SMOKE_MID, smooth(0.15, 0.6, along))
    col = mix(col, SMOKE_TIP, smooth(0.55, 1.0, along) * (0.6 + 0.35 * fbm(P, 14.0, 2, 9)))
    paint(o, col, np.full(len(P), 0.62), np.zeros(len(P)))


def eye_paint(o, fr):
    """Eyeshine: pale mint-silver, brightest round the pupil, deepening to sea-green at the rim, fine fibres, a round dark pupil, a dark rim."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(16, 22, 26), (len(px), 3)).copy()
    iris = mix(MINT_PALE, rgb(70, 150, 140), smooth(PUPIL * 0.9, IRIS, r))
    iris = mix(iris, iris * 0.75, smooth(-0.2, 0.8, py / IRIS) * 0.5)          # shadowed under the upper lid
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 34 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    col = mix(col, rgb(10, 22, 24), smooth(IRIS - 0.12, IRIS - 0.02, r) * (1 - smooth(IRIS, IRIS + 0.04, r)))
    col = mix(col, rgb(3, 3, 6), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
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
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, INK, rgb(2, 2, 4))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, INK, rgb(4, 4, 6), lower_share=0.8)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Nose"] = build_nose(N + "NoseHi", HI)
    pieces["Wisps"], data["wisp_meta"] = build_wisps(data["tree"], N + "WispsHi", HI, 10, 8)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0058, 12), (22, -18, 0.0027, 8)))}
    if not clay:
        paint_skin(skin)
        paint_nose(pieces["Nose"])
        paint_wisps(pieces["Wisps"], np.array([m[0] for m in data["wisp_meta"]]))
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.05, 0.3)
FACE_AT = (0, -0.4, 0.38)
EXTRA = [(0, -1, 0.05, 0.85, FACE_AT), (0.62, -0.75, 0.2, 0.85, FACE_AT), (1, -0.12, 0.08, 0.85, FACE_AT), (0.3, -0.9, 0.2, 0.45, tuple(EYE_C)),
         (0.7, 0.5, 0.4, 1.3, (0, 0.42, 0.42)), (1, -0.1, 0.05, 1.6, (0, 0.0, 0.22))]


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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.0, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 2600
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5, "Nose": 3.0, "EarL": 1.4, "EarR": 1.4}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    lows["Wisps"], data["low_wisp_meta"] = build_wisps(data["tree"], N + "WispsLow", GAME, 5, 2)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 8, 8, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 26, 18)       # round enough for the painted iris to stay round
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Nose"] = build_nose(N + "NoseLow", GAME, 14, 10)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the hips are its base: everything ahead of them can rise off them, so it can stand up on its hind legs to look about
SPINE_BONES = (("Hips", 1, "Root"), ("Body", 2, "Hips"), ("Chest", 3, "Body"), ("Shoulders", 4, "Chest"), ("Neck", 5, "Shoulders"), ("Head", 6, "Neck"))
SEG_BONE = ["Hips", "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "Head"]
SEG_BLEND = {2: 0.35, 3: 0.35, 4: 0.3, 5: 0.3, 6: 0.3}
TAIL_NAMES = ["Tail%d" % k for k in range(1, 8)]
TAIL_F = (0.03, 0.17, 0.31, 0.45, 0.6, 0.75, 0.88)
LEG_F = (0.25, 0.5, 0.75)


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, k, parent in SPINE_BONES:
        bones.append((name, SPINE[k].copy(), parent))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, C, along, up, n = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, C.copy(), "Head")]
    for key, side, knots, _ in LEGS:
        parent = "Shoulders" if key[0] == "F" else "Hips"
        for k in range(3):
            bones.append(("Leg%s%d" % (key, k + 1), mir(knots[k], side), parent))
            parent = "Leg%s%d" % (key, k + 1)
        bones.append(("Paw" + key, mir(knots[3], side), parent))
    return armature(bones)


def spine_weight(k):
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


# a tail bone wholly owns the middle of its length, and the share passes to the next across the joint between them:
# skin on the near side of a pivot never follows the bone beyond it, which is what stretched the plume when it bent
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))


def tail_weight(f):
    return chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(f))


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def body_weights(P):
    """The skin's weights at any points: spine, neck and head, the tail, the legs; a paw and its toes wholly its paw's."""
    f_sp, _ = nearest_on(SPINE, P)
    k = f_sp * (len(SPINE) - 1)
    head_d = np.linalg.norm((P - np.array(tuple(HEAD))) / (np.array(HEAD_R) * 1.25), axis=1)
    legs = {}
    for key, side, knots, radii in LEGS:
        f, d = nearest_on(leg_path(knots, side), P)
        legs[key] = (side, knots, radii, f, d)
    tf, td, _ = tail_coords(P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        paw_key = None
        for key, (side, knots, radii, f, d) in legs.items():
            if (Vector(P[i]) - (mir(knots[4], side) + V(0, -0.025, 0))).length < 0.055 and z < 0.06:
                paw_key = key
        if paw_key is not None:
            out.append({"Paw" + paw_key: 1.0})
            continue
        w = dict(spine_weight(float(k[i])))
        if head_d[i] < 1.0:
            w = blend(w, {"Head": 1.0}, float(smooth(1.0, 0.85, head_d[i])))
        reach = tail_radius(float(tf[i])) * (1 + TAIL_LOBE_DEPTH) + 0.006
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.01, 0.06, tf[i]))
        if share > 0:
            w = blend(w, tail_weight(tf[i]), share)
        for key, (side, knots, radii, f, d) in legs.items():
            if x * side <= 0:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.025
            mm = float(smooth(knots[0].z, knots[0].z - 0.08, z)) * float(smooth(0.012, 0.035, abs(x))) * (1 - float(smooth(lr * 0.95, lr * 1.4, d[i])))
            if mm > 0:
                w = blend(w, leg_weight(key, float(f[i])), mm)
        out.append(w)
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    roots = np.array([m[1] for m in data["low_wisp_meta"]])
    uniq, inverse = np.unique(roots, axis=0, return_inverse=True)
    root_w = body_weights(uniq)
    weigh(lows["Wisps"], [root_w[j] for j in inverse.ravel()])
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Nose"], "Head")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateShadowcoil uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


# its stance poses, each found by a search against the ground (see the vault): the same numbers as PetRig's SHADOW_REAR and SHADOW_LIE
REAR = {"Body": (1.05, 0, 0), "Chest": (-0.15, 0, 0), "Neck": (-0.35, 0, 0), "Head": (-0.4, 0, 0), "LegFL1": (-0.9, 0, 0), "LegFR1": (-0.9, 0, 0), "LegFL2": (0.9, 0, 0),
        "LegFR2": (0.9, 0, 0), "LegFL3": (0.6, 0, 0), "LegFR3": (0.6, 0, 0)}
LIE = {"Hips": (0, 0, 0, (0, -0.097, 0)), "Body": (0, 0.25, 0), "Chest": (0, 0.3, 0), "Shoulders": (0, 0.3, 0), "Neck": (0.1, 0.35, 0), "Head": (0.05, 0.3, 0),
       "LegFL1": (-0.557, 0, 0), "LegFR1": (-0.557, 0, 0), "LegFL2": (-1.459, 0, 0), "LegFR2": (-1.459, 0, 0), "LegFL3": (-0.624, 0, 0), "LegFR3": (-0.624, 0, 0),
       "LegBL1": (0.646, 0, 0), "LegBR1": (0.646, 0, 0), "LegBL2": (-1.205, 0, 0), "LegBR2": (-1.205, 0, 0), "LegBL3": (0.865, 0, 0), "LegBR3": (0.865, 0, 0),
       "Tail1": (0, 0.03, 0), "Tail2": (0.14, 0.03, 0), "Tail3": (-0.55, 0, 0), "Tail4": (-0.27, 0, 0)}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    gather = spec({"Hips": (-0.25, 0, 0), "Body": (0.2, 0, 0), "Chest": (0.15, 0, 0), "LegFL1": (-0.6, 0, 0), "LegFR1": (-0.6, 0, 0), "LegBL1": (0.7, 0, 0), "LegBR1": (0.7, 0, 0),
                   "LegBL2": (-0.4, 0, 0), "LegBR2": (-0.4, 0, 0)})
    stretch = spec({"Hips": (0.15, 0, 0), "Body": (-0.1, 0, 0), "LegFL1": (0.75, 0, 0), "LegFR1": (0.75, 0, 0), "LegBL1": (-0.75, 0, 0), "LegBR1": (-0.75, 0, 0),
                    "LegBL2": (0.4, 0, 0), "LegBR2": (0.4, 0, 0)})
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-6, -5), "Gather": gather, "Stretch": stretch, "Rear": spec(REAR), "Lie": spec(LIE),
            "Look": spec({"Neck": (0.2, 0.4, 0.1), "Head": (0.2, 0.5, 0.3)}), "Tail": spec({n: (0.06, 0.15, 0) for n in TAIL_NAMES}),
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


GROUND_PARTS = {"FrontPaws": ("PawFL", "PawFR"), "HindPaws": ("PawBL", "PawBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",)}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.45)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.3 and p.center.z > 0.3, 2.0), (None, 1.0)], SCALES, margin=0.011)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.3, 0.3, 0.3, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.008, 0.022))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    bpy.data.objects.remove(glows["Glints"], do_unlink=True)          # first, so the game's piece takes its exact name
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0058, 10), (22, -18, 0.0027, 6)))}
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
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.0, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Rear", "Lie"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 2.6, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 2.6, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.9, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Gather", side), ("Stretch", side), ("Rear", side), ("Rear", wide), ("Lie", wide), ("Look", face),
                       ("Tail", (0.4, 0.8, 0.5, 2.0, (0, 0.4, 0.4))), ("Ears", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name + ("W" if view is wide and name == "Rear" else "")), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 2.6, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

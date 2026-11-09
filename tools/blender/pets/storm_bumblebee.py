"""The Storm Bumblebee (Uncommon, Electricity; Elemental Core Egg): "It drifts on charged air and hums before a storm. Its sting is a lesson most
people learn once."

A fat, fuzzy bumblebee charged with static (the owner's choice, 2026-11-09), in a design language of its own: static electricity in fur. A round,
plush body: an electric-gold collar and a storm-grey back on its thorax; a gold band, a storm-grey band and a snow-white tail on its abdomen, each
band's edge a jagged zigzag, the way charge runs. Its fur stands on end: a frizzed crest of tufts over its thorax and a cowlick on its crown, little
arcs crackling between their tips. Small smoky wings with dark veins, a blur when they beat. Big dark compound eyes, faceted, with a violet storm
sheen; fuzzy gold cheeks; short elbowed feelers, a spark at each tip. In the baskets of its hind legs, where a bee carries pollen, it carries balls
of stored lightning. Its sting is a needle of light, sheathed in its tail.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/storm_bumblebee.py -- [clay|paint|rig|all] [review dir]

Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It is modelled hovering, its legs hanging. The maps go to assets/pets/ElementalCoreEgg/.

What touches what: the skin (head, thorax, abdomen, the fur crest and cowlick, the collar ruff) is one piece; the eyes sit half sunk in its head;
the feelers root in its face; the legs root under its thorax; the wings root in the top of its thorax's sides; the mandibles root under its face;
the charge balls sit in the hollow of each hind leg's basket; the sting lies inside its tail, its point just showing; the arcs run between the tips
of its fur tufts.
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
PET = "StormBumblebee"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours: electric gold, storm grey, snow, and the light of a spark ----------
GOLD, GOLD_DEEP, GOLD_PALE = rgb(255, 206, 40), rgb(232, 146, 16), rgb(255, 234, 140)
STORM, STORM_DEEP, STORM_PALE = rgb(56, 60, 80), rgb(26, 28, 40), rgb(112, 118, 144)
SNOW, SNOW_TINT = rgb(244, 245, 252), rgb(200, 184, 255)
CHITIN, CHITIN_EDGE = rgb(24, 24, 34), rgb(70, 72, 96)
EYE_BASE, EYE_SHEEN, EYE_FACET = rgb(12, 12, 22), rgb(110, 84, 196), rgb(40, 40, 64)
WING, WING_VEIN = rgb(222, 226, 240), rgb(40, 38, 56)
TIP_HEX, CHARGE_HEX, STING_HEX, ARC_HEX = "fff2a0", "ffe066", "fff9dc", "eee4ff"

# ---------- the frame of it ----------
TH_C, TH_R = V(0, 0.0, 0.5), (0.125, 0.135, 0.12)                   # its thorax
HEAD_C, HEAD_R = V(0, -0.172, 0.462), (0.094, 0.074, 0.098)           # its head, a little low on the front of its thorax
ABD_PATH = [V(0, 0.08, 0.488), V(0, 0.17, 0.47), V(0, 0.27, 0.438), V(0, 0.36, 0.398), V(0, 0.445, 0.35)]    # waist to tail tip, down a little
ABD_RMAX, ABD_FMAX = 0.162, 0.4      # its girth, and where along it
ABD_WIDE = 1.07                     # its abdomen a little wider than deep
COLLAR = (V(0, -0.112, 0.484), (0.074, 0.036, 0.074))     # the ruff of fur filling the pinch between head and thorax
EYE_C = V(0.06, -0.212, 0.48)       # its compound eye (left), half sunk in its head
EYE_R = (0.034, 0.046, 0.07)        # out, forward, up
EYE_TILT = math.radians(12)         # their tops lean in, as a bee's do
EYE_YAW = math.radians(18)          # turned a little forward: it looks at you
CHEEK = (V(0.046, -0.222, 0.424), (0.031, 0.026, 0.028))
ANT = [V(0.016, -0.232, 0.503), V(0.03, -0.274, 0.582), V(0.066, -0.324, 0.632), V(0.096, -0.346, 0.628)]     # socket, elbow, bend, tip (left)
ANT_TIP_R = 0.0125
MANDIBLE = [V(0.03, -0.205, 0.39), V(0.022, -0.228, 0.382), V(0.007, -0.238, 0.378)]
# legs (left): hip, knee, ankle, toe, hanging as it hovers
LEGS = [[V(0.04, -0.07, 0.41), V(0.086, -0.104, 0.338), V(0.082, -0.07, 0.262), V(0.072, -0.05, 0.214)],
        [V(0.056, 0.0, 0.398), V(0.114, -0.004, 0.33), V(0.108, 0.046, 0.25), V(0.096, 0.076, 0.2)],
        [V(0.062, 0.048, 0.402), V(0.146, 0.088, 0.336), V(0.138, 0.172, 0.258), V(0.116, 0.222, 0.214)]]       # (its hip under its thorax, not its abdomen)
LEG_R = ((0.017, 0.0135), (0.0125, 0.0145), (0.0092, 0.0058))              # femur, tibia, tarsus: radius at each end
BASKET_W = 0.026                    # the hind tibia's basket: its half-width (flattened out to a paddle)
CHARGE_R = 0.021
# wings (left): root, the way the span runs, length, widest chord
FORE = (V(0.062, -0.03, 0.604), V(1.0, 0.36, 0.42), 0.27, 0.088)        # held up in a shallow V (lower, they met its abdomen as they beat)
HIND = (V(0.066, 0.034, 0.598), V(1.0, 0.8, 0.34), 0.17, 0.056)
# its fur: overlapping clumps, each a tongue lying back along its body, tip lifted (bristling with static on its back); a cowlick on its crown
FUR_ROW, FUR_COL = 0.026, 0.021      # a clump's length (along its body) and width (round it)
FUR_H = 0.0068                       # a clump's height at its tip, on its back (less on its sides, belly and face)
COWLICK = [(V(0.0, 0.3, 1.0), 0.056, V(0, -1, 0.3)), (V(0.32, 0.42, 1.0), 0.044, V(1, -0.6, 0)), (V(-0.32, 0.42, 1.0), 0.044, V(-1, -0.6, 0))]
# the arcs across its fur: pairs of points on it (a direction from the thorax's middle, or f along the abdomen and theta round it; the cowlick's tips)
ARCS = {"A": [("th", V(0.18, -0.35, 1.0), V(-0.05, -0.5, 1.0)), ("abd", (0.36, 0.5), (0.47, 0.12)), ("abd", (0.7, -0.62), (0.79, -0.22)), ("cow", 0, 1)],
        "B": [("th", V(-0.24, 0.05, 1.0), V(-0.04, -0.17, 1.0)), ("abd", (0.3, -0.42), (0.41, -0.8)), ("abd", (0.62, 0.58), (0.73, 0.9)), ("cow", 0, 2)]}
STING_LEN, STING_R = 0.064, 0.0095
STING_SHOW = 0.01                   # how far its point shows past the fur at rest


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def ell_point(c, r, d):
    """Where a direction from an ellipsoid's middle meets its surface."""
    d = d.normalized()
    k = 1 / math.sqrt((d.x / r[0]) ** 2 + (d.y / r[1]) ** 2 + (d.z / r[2]) ** 2)
    return c + d * k


def ell_normal(c, r, p):
    q = p - c
    return V(q.x / r[0] ** 2, q.y / r[1] ** 2, q.z / r[2] ** 2).normalized()


def arc_lengths(path):
    a = np.array([tuple(p) for p in path])
    return np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])


def rm_frames(path, first_side=None):
    """Frames along a path that never twist (each turned on from the last by the least rotation)."""
    out = []
    tan = (path[1] - path[0]).normalized()
    side = first_side or (V(1, 0, 0) - tan * tan.x)
    if side.length < 1e-4:
        side = tan.orthogonal()
    side = (side - tan * side.dot(tan)).normalized()
    for i in range(len(path)):
        t2 = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        if i > 0:
            side = tan.rotation_difference(t2) @ side
        side = (side - t2 * side.dot(t2)).normalized()
        tan = t2
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def loft(m, path, w_fn, h_fn, nt=24, first_side=None, caps=True):
    """A tube along path: w_fn(f) its half-width along its side, h_fn(f) its half-height. Returns its rings."""
    fr = rm_frames(path, first_side)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        w, h = w_fn(f), h_fn(f)
        rings.append([m.bm.verts.new(p + side * (w * math.cos(TAU * k / nt)) + up * (h * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    if caps:
        m.bm.faces.new(list(reversed(rings[0])))
        m.bm.faces.new(rings[-1])
    return rings


def oriented_ball(m, c, r, axes, seg=32, rings=20):
    """An ellipsoid with its radii along three axes (columns)."""
    M = Matrix.Translation(c) @ Matrix((axes[0] * r[0], axes[1] * r[1], axes[2] * r[2])).transposed().to_4x4()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=M)


# ---------- where things are ----------
ABD = catmull(ABD_PATH, 40)
ABD_S = arc_lengths(ABD)
ABD_F = ABD_S / ABD_S[-1]


def abd_at(f):
    s = f * ABD_S[-1]
    i = min(int(np.searchsorted(ABD_S, s, side="right")) - 1, len(ABD) - 2)
    t = (s - ABD_S[i]) / max(ABD_S[i + 1] - ABD_S[i], 1e-9)
    return ABD[i].lerp(ABD[i + 1], t)


def abd_radius(f):
    """Its abdomen's radius at f along it (0 its waist, 1 its tail's end): an egg, its front a little pinched, its end round (a radius profile
    through knots creased it in rings)."""
    if f < ABD_FMAX:
        return ABD_RMAX * math.sqrt(max(1 - ((ABD_FMAX - f) / ABD_FMAX * 0.86) ** 2, 0.0))
    return max(ABD_RMAX * math.sqrt(max(1 - ((f - ABD_FMAX) / (1 - ABD_FMAX)) ** 2, 0.0)), 0.003)


ABD_FRAMES = rm_frames(ABD, V(1, 0, 0))


def abd_surface(f, theta):
    """A point on its abdomen's surface at f along it and theta round it (0 its top, + toward its left), and the surface's normal there."""
    i = int(round(f * (len(ABD) - 1)))
    tan, side, up = ABD_FRAMES[i]
    if up.z < 0:
        up = -up
    if side.x < 0:
        side = -side
    r = abd_radius(float(ABD_F[i]))
    p = ABD[i] + side * (math.sin(theta) * r * ABD_WIDE) + up * (math.cos(theta) * r)
    n = (side * (math.sin(theta) / ABD_WIDE) + up * math.cos(theta)).normalized()
    return p, n


TAIL_DIR = (ABD[-1] - ABD[-3]).normalized()
TAIL_TIP = ABD[-1].copy()            # the end of its tail (the fur's mean surface)


def eye_axes(side):
    out = V(side, 0, 0)
    up = Matrix.Rotation(-side * EYE_TILT, 3, "Y") @ V(0, 0, 1)
    fwd = up.cross(out).normalized() * side
    if fwd.y > 0:
        fwd = -fwd
    out = fwd.cross(up).normalized()
    if out.x * side < 0:
        out = -out
    R = Matrix.Rotation(-side * EYE_YAW, 3, "Z")
    return R @ out, R @ fwd, up


def eye_centre(side):
    return mir(EYE_C, side)


def cowlick_paths():
    """The cowlick's tufts: each one's path from its root (inside the skin) to its tip, and its root's radius."""
    out = []
    for d, length, curl in COWLICK:
        base = ell_point(HEAD_C, HEAD_R, d)
        n = ell_normal(HEAD_C, HEAD_R, base)
        up = (n + V(d.x, 0, 0) * 0.8 + V(0, 0.15, 0.2)).normalized()
        tipward = (up + curl.normalized() * 0.9).normalized()
        pts = [base - n * 0.014, base + up * (length * 0.45), base + up * (length * 0.75) + tipward * (length * 0.18), base + up * (length * 0.8) + tipward * (length * 0.45)]
        out.append((catmull(pts, 6), 0.0135))
    return out


def resample(path, n):
    """n + 1 points evenly by arc length."""
    L = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    out = []
    for t in np.linspace(0, L[-1], n + 1):
        i = min(int(np.searchsorted(L, t, side="right")) - 1, len(a) - 2)
        f = (t - L[i]) / max(L[i + 1] - L[i], 1e-9)
        out.append(V(*(a[i] * (1 - f) + a[i + 1] * f)))
    return out


# the line down the middle of it, snout to tail tip: its fur's clumps are laid out along it and round it
CL = resample(catmull([V(0, -0.262, 0.462), V(0, -0.172, 0.462), V(0, -0.1, 0.482), V(0, 0.0, 0.5), V(0, 0.08, 0.49), V(0, 0.17, 0.47),
                       V(0, 0.27, 0.438), V(0, 0.36, 0.398), V(0, 0.445, 0.35)], 12), 200)
CL_L = float(arc_lengths(CL)[-1])
CL_FRAMES = rm_frames(CL, V(1, 0, 0))


def body_coords(P):
    """Per point: s (metres along its middle line, past its ends where its snout and tail turn), its distance off the line, and theta round it (0 along
    its back, +pi/2 its left, +-pi its belly)."""
    f, d = nearest_on(CL, P)
    k = np.clip(np.round(f * (len(CL) - 1)).astype(int), 0, len(CL) - 1)
    T = np.array([tuple(CL_FRAMES[i][0]) for i in k])
    S = np.array([tuple(CL_FRAMES[i][1]) for i in k])
    U = np.array([tuple(CL_FRAMES[i][2]) for i in k])
    U = U * np.sign(U[:, 2:3] + 1e-9)
    S = S * np.sign(S[:, 0:1] + 1e-9)
    rel = P - np.array([tuple(CL[i]) for i in k])
    along = (rel * T).sum(1)
    s = f * CL_L + np.where(f >= 0.999, np.maximum(along, 0), 0) + np.where(f <= 0.001, np.minimum(along, 0), 0)
    theta = np.arctan2((rel * S).sum(1), (rel * U).sum(1))
    return s, d, theta


def fur_field(P, Nn):
    """The fur's height at each point (metres, out along the skin), and how far each point is toward its clump's tip (0 root, 1 tip)."""
    s, d, theta = body_coords(P)
    # each row of clumps is laid round at its own width: its radius there (the skin's own, a high percentile of its distance off the line)
    bins = np.clip((s / CL_L * 60).astype(int), 0, 59)
    rad = np.array([np.percentile(d[bins == b], 80) if (bins == b).sum() > 20 else np.nan for b in range(60)])
    good = ~np.isnan(rad)
    rad = np.interp(np.arange(60), np.arange(60)[good], rad[good])
    rad = np.convolve(np.pad(rad, 3, mode="edge"), np.ones(7) / 7, mode="valid")
    c = theta * rad[bins]
    row = s / FUR_ROW
    best = np.zeros(len(P))
    tipness = np.zeros(len(P))
    i0 = np.floor(row).astype(int)
    for di in (-1, 0, 1):
        i = i0 + di
        shift = (i % 2) * 0.5
        col = c / FUR_COL - shift
        j0 = np.floor(col).astype(int)
        for dj in (-1, 0, 1):
            j = j0 + dj
            jx = hash01(i, j, 0, 31) - 0.5
            jy = hash01(i, j, 0, 37) - 0.5
            size = 0.82 + 0.36 * hash01(i, j, 0, 43)
            u = (row - (i + 0.5 + 0.4 * jy)) / size             # along it: -0.5 root .. +0.5 tip, and on
            w = (col - (j + 0.5 + 0.4 * jx)) / size
            along = np.clip((u + 0.75) / 1.6, 0, 1.2)           # 0 at its root, 1 at its tip
            half = 0.62 * (1 - np.clip(along, 0, 1) ** 2.4) + 0.04
            inside = (1 - smooth(half * 0.5, half, np.abs(w))) * (1 - smooth(0.9, 1.06, along))
            h = (np.clip(along, 0, 1) ** 0.85) * inside * (0.8 + 0.4 * hash01(i, j, 0, 41))
            take = h > best
            best = np.where(take, h, best)
            tipness = np.where(take, np.clip(along, 0, 1), tipness)
    back = smooth(-0.3, 0.9, np.cos(theta))                           # bristling most along its back
    face = smooth(-0.21, -0.17, P[:, 1]) * (1 - smooth(0.0, 1.0, -Nn[:, 1] - 0.2) * 0.0)
    amount = FUR_H * (0.45 + 0.55 * back) * (0.35 + 0.65 * face)
    return best * amount, tipness, s, theta


def tip_of(path):
    return path[-1]


# ---------- the skin ----------
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


def near_eyes(P, reach):
    """1 within reach of an eye's surface (its socket: no fur there, or it would poke through the eye), 0 beyond."""
    out = np.zeros(len(P))
    for side in (1, -1):
        ax = eye_axes(side)
        q = P - np.array(tuple(eye_centre(side)))
        loc = np.stack([(q * np.array(tuple(a))).sum(1) / r for a, r in zip(ax, EYE_R)], 1)
        d = (np.linalg.norm(loc, axis=1) - 1) * min(EYE_R)
        out = np.maximum(out, 1 - smooth(0.0, reach, d))
    return out


def build_skin():
    m = Mesh()
    m.ball(TH_C, TH_R, 128, 80)
    m.ball(HEAD_C, HEAD_R, 112, 72)
    rfn = lambda f: abd_radius(float(np.interp(f, np.linspace(0, 1, len(ABD_F)), ABD_F)))
    loft(m, ABD, lambda f: rfn(f) * ABD_WIDE, rfn, nt=128, first_side=V(1, 0, 0))
    m.ball(COLLAR[0], COLLAR[1], 64, 40)                 # the ruff round its neck
    for side in (1, -1):
        m.ball(mir(CHEEK[0], side), CHEEK[1], 48, 28)             # fuzzy cheeks under its eyes
        out, fwd, up = eye_axes(side)
        oriented_ball(m, eye_centre(side) - out * 0.004, (EYE_R[0] * 1.08, EYE_R[1] * 1.1, EYE_R[2] * 1.06), (out, fwd, up), 48, 32)   # the socket's rim
    for path, r0 in cowlick_paths():
        loft(m, path, lambda f, r0=r0: r0 * (1 - f) ** 0.85 + 0.0035, lambda f, r0=r0: r0 * (1 - f) ** 0.85 + 0.0035, nt=20)
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.7, "iterations": 4})])
    # its fur: clumps all over (none in its eye sockets, none on the cowlick: that is fur already)
    P, Nn = verts(o), normals(o)
    h, _, _, _ = fur_field(P, Nn)
    cow = np.zeros(len(P))
    for path, _ in cowlick_paths():
        _, dd = nearest_on(path[2:], P)
        cow = np.maximum(cow, 1 - smooth(0.012, 0.022, dd))
    h = h * (1 - near_eyes(P, 0.01)) * (1 - cow)
    set_verts(o, P + Nn * h[:, None])
    apply_mods(o, [("SMOOTH", {"factor": 0.3, "iterations": 1})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_eyes(coll, seg=64, rings=40, name="EyeHi"):
    out = {}
    for side, tag in ((1, "L"), (-1, "R")):
        m = Mesh()
        a = eye_axes(side)
        oriented_ball(m, eye_centre(side), EYE_R, a, seg, rings)
        out[tag] = m.finish(N + "Eye" + tag + ("Hi" if coll is HI else "Low"), coll)
    return out


def ant_segments(side):
    p = [mir(q, side) for q in ANT]
    return [p[0], p[1]], catmull([p[1], p[2], p[3]], 6)


def build_antennae(coll, nt=12, per=1):
    m = Mesh()
    make_tags_bm(m.bm, ints=("seg",))
    for side in (1, -1):
        scape, flag = ant_segments(side)
        before = set(m.bm.verts)
        loft(m, catmull([scape[0] - (scape[1] - scape[0]) * 0.15, scape[0], scape[1]], 4 * per), lambda f: 0.0088, lambda f: 0.0088, nt=nt)
        tag_new_bm(m.bm, before, seg=1 if side > 0 else 3)
        before = set(m.bm.verts)
        loft(m, [flag[0] - (flag[1] - flag[0]).normalized() * 0.008] + flag, lambda f: 0.0074 - 0.0012 * f, lambda f: 0.0074 - 0.0012 * f, nt=nt)
        m.ball(flag[0], (0.0118,) * 3, nt, max(6, nt // 2))          # the elbow, a knob (barely wider than the feeler, they lay level)
        tag_new_bm(m.bm, before, seg=2 if side > 0 else 4)
    return m.finish(N + "Antennae" + ("Hi" if coll is HI else "Low"), coll)


def build_mandibles(coll, nt=10):
    m = Mesh()
    for side in (1, -1):
        p = [mir(q, side) for q in MANDIBLE]
        loft(m, catmull(p, 5), lambda f: 0.0068 * (1 - 0.6 * f), lambda f: 0.0052 * (1 - 0.55 * f), nt=nt, first_side=V(0, 0, 1))
    return m.finish(N + "Mandibles" + ("Hi" if coll is HI else "Low"), coll)


def leg_points(side, k):
    return [mir(q, side) for q in LEGS[k]]


def build_legs(coll, nt=14, per=5):
    """Each leg one tube, hip to toe, the knee and ankle bent sharp; the hind legs' tibias flattened to a broad basket."""
    m = Mesh()
    make_tags_bm(m.bm, ints=("leg", "seg"))
    for side in (1, -1):
        for k in range(3):
            hip, knee, ankle, toe = leg_points(side, k)
            outward = V(side, 0, 0)
            for s, (a, b) in enumerate(((hip, knee), (knee, ankle), (ankle, toe))):
                before = set(m.bm.verts)
                d = (b - a).normalized()
                start = a - d * (0.006 if s else 0.02)           # the femur rooted well inside the thorax
                end = b + d * (0.004 if s < 2 else 0.0)
                pts = [start.lerp(end, t / per) for t in range(per + 1)]
                r0, r1 = LEG_R[s]
                if s == 1 and k == 2:
                    w_fn = lambda f, r0=r0, r1=r1: r0 + (BASKET_W - r0) * math.sin(math.pi * min(1, f * 1.15) / 2) ** 0.8 * (1 - 0.25 * f)
                    h_fn = lambda f, r0=r0: 0.0075
                else:
                    w_fn = lambda f, r0=r0, r1=r1: r0 + (r1 - r0) * f
                    h_fn = w_fn
                side_dir = (outward - d * d.dot(outward)).cross(d).normalized() if s == 1 and k == 2 else None
                loft(m, pts, w_fn, h_fn, nt=nt, first_side=side_dir)
                if s < 2:
                    m.ball(b, (LEG_R[s][1] * 1.3,) * 3, nt, max(6, nt // 2))      # the joint, a knob (barely wider than the leg, the two lay level)
                else:
                    claw = [b, b + d * 0.012 + V(0, -0.006, -0.004)]           # a small hooked claw
                    loft(m, catmull([b - d * 0.004] + claw, 3), lambda f: 0.0045 * (1 - 0.7 * f), lambda f: 0.0045 * (1 - 0.7 * f), nt=max(6, nt // 2))
                tag_new_bm(m.bm, before, leg=(0 if side > 0 else 3) + k, seg=s)
    return m.finish(N + "Legs" + ("Hi" if coll is HI else "Low"), coll)


def basket_frame(side):
    """The hind tibia's basket: its middle and the way its outer face looks."""
    hip, knee, ankle, toe = leg_points(side, 2)
    d = (ankle - knee).normalized()
    outward = V(side, 0, 0)
    n = (outward - d * d.dot(outward)).normalized()
    return knee.lerp(ankle, 0.5), n




# ---------- the wings ----------
WING_TMAX = 0.995                   # the tip's rounding stops just short of a point (no degenerate faces)


def wing_frame(spec, side):
    root, span, length, chord = spec
    S = mir(span, side).normalized()
    C = V(0, 1, 0.24)                   # its trailing edge a little raised: clear of the fur on its back
    C = (C - S * C.dot(S)).normalized()
    Nw = S.cross(C).normalized()
    if Nw.z < 0:
        Nw = -Nw
    return mir(root, side), S, C, Nw, length, chord


def wing_edges(u, chord):
    """Its leading and trailing edges (back along the chord from the span line) at u along it: narrow at its root, widest past the middle, then a
    rounded tip swept back."""
    if u < 0.62:
        c = chord * (0.2 + 0.8 * math.sin(math.pi / 2 * u / 0.62) ** 1.25)        # slender at its root, as a bee's is
        return -0.03 * chord * math.sin(math.pi * u / 0.62), c - 0.03 * chord * math.sin(math.pi * u / 0.62)
    t = min((u - 0.62) / 0.38, 1.0) * WING_TMAX
    centre = chord * (0.5 + 0.14 * t)
    half = chord * 0.5 * math.sqrt(max(1 - t * t, 0.0))
    return centre - half, centre + half


def wing_point(spec, side):
    root, S, C, Nw, length, chord = wing_frame(spec, side)

    def point(u, v):
        lead, trail = wing_edges(u, chord)
        s = (u * 1.08 - 0.08) * length                         # its root a little inside the thorax
        camber = 0.005 * math.sin(math.pi * v) * min(1, u * 3)
        return tuple(root + S * s + C * (lead + (trail - lead) * v) + Nw * (camber - 0.012 * (u ** 2)))     # its tip curved down a touch
    return point


WING_SPECS = (("Fore", FORE), ("Hind", HIND))


def wing_thick(u, v):
    return 0.0022


# the veins, as polylines in (u, v): a bee's forewing has a strong costa along its front, a long narrow marginal cell, three submarginal cells and
# the cells behind; its outer third is clear, only wrinkled
FORE_VEINS = [
    [(0.0, 0.04), (0.3, 0.035), (0.52, 0.04), (0.7, 0.07)],                 # the costa, along its front
    [(0.0, 0.17), (0.25, 0.18), (0.42, 0.2), (0.58, 0.19), (0.68, 0.13), (0.71, 0.07)],     # the radius, curving up to close the marginal cell
    [(0.04, 0.44), (0.24, 0.45), (0.42, 0.42)],                             # the media
    [(0.04, 0.72), (0.2, 0.72), (0.34, 0.66)],                              # the cubitus
    [(0.42, 0.2), (0.4, 0.31), (0.42, 0.42)], [(0.56, 0.19), (0.53, 0.32), (0.5, 0.42)],     # the submarginal cells' cross-veins, bowed
    [(0.24, 0.45), (0.22, 0.6), (0.2, 0.72)],                               # the discal cell's
]
HIND_VEINS = [
    [(0.0, 0.05), (0.4, 0.05), (0.62, 0.08)],
    [(0.04, 0.34), (0.3, 0.34), (0.46, 0.27)],
    [(0.3, 0.34), (0.24, 0.56)],
]
def vein_distance(uu, vv, veins, chord, length):
    """Per point, the distance in metres to the nearest vein."""
    best = np.full(len(uu), 1e9)
    P = np.stack([uu * length, vv * chord], 1)
    for line in veins:
        a = np.array([(q.x * length, q.y * chord) for q in catmull([V(u, v, 0) for u, v in line], 6)])
        for i in range(len(a) - 1):
            ab = a[i + 1] - a[i]
            t = np.clip(((P - a[i]) * ab).sum(1) / max((ab * ab).sum(), 1e-12), 0, 1)
            best = np.minimum(best, np.linalg.norm(P - (a[i] + ab * t[:, None]), axis=1))
    return best


def wing_paint_uv(uu, vv, kind):
    spec = FORE if kind == "Fore" else HIND
    veins = FORE_VEINS if kind == "Fore" else HIND_VEINS
    d = vein_distance(uu, vv, veins, spec[3], spec[2])
    vein = 1 - smooth(0.0006, 0.0016, d)
    edge = np.maximum(1 - smooth(0.0, 0.05, vv), 1 - smooth(0.92, 1.0, 1 - vv)) * 0.0
    smoke = smooth(0.0, 0.4, 1 - uu) * 0.25                                  # smokier toward its root
    col = mix(np.broadcast_to(WING, (len(uu), 3)), STORM_PALE, smoke)
    col = mix(col, WING_VEIN, np.clip(vein + edge, 0, 1))
    wrinkle = (1 - smooth(0.0, 0.0012, np.abs(np.sin(vv * 9 + uu * 22) * 0.004))) * smooth(0.7, 0.85, uu) * 0.35
    col = mix(col, STORM_PALE, wrinkle)
    return col, 0.1 + 0.15 * vein, vein


def wing_sheet(m, spec, side, nu, nv):
    """A wing as a thin closed plate, its two faces each offset along the wing's own plane (offset along the surface's normal from point to point,
    the normal twisted at its slender tip and folded the faces there: black notches). Its vertices in pairs (top, bottom), point by point."""
    point = wing_point(spec, side)
    _, S, C, Nw, _, _ = wing_frame(spec, side)
    bm = m.bm
    P = [[V(*point(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    sign = 1 if (P[nu // 2 + 1][nv // 2] - P[nu // 2][nv // 2]).cross(P[nu // 2][nv // 2 + 1] - P[nu // 2][nv // 2]).dot(Nw) > 0 else -1
    nrm = Nw * sign
    t = wing_thick(0, 0) / 2
    top, bot = [], []
    for i in range(nu + 1):
        rt, rb = [], []
        for j in range(nv + 1):
            rt.append(bm.verts.new(P[i][j] + nrm * t))
            rb.append(bm.verts.new(P[i][j] - nrm * t))
        top.append(rt)
        bot.append(rb)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j]))
    for i in range(nu):
        bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]))
        bm.faces.new((top[i + 1][nv], bot[i + 1][nv], bot[i][nv], top[i][nv]))
    for j in range(nv):
        bm.faces.new((top[0][j + 1], bot[0][j + 1], bot[0][j], top[0][j]))
        bm.faces.new((top[nu][j], bot[nu][j], bot[nu][j + 1], top[nu][j + 1]))


def build_wings_hi(nu=40, nv=16):
    m = Mesh()
    uu, vv, kinds = [], [], []
    for kind, spec in WING_SPECS:
        for side in (1, -1):
            wing_sheet(m, spec, side, nu, nv)
            for i in range(nu + 1):
                for j in range(nv + 1):
                    uu += [i / nu] * 2
                    vv += [j / nv] * 2
                    kinds += [kind] * 2
    o = m.finish(N + "WingsHi", HI, recalc=False)
    uu, vv, kinds = np.array(uu), np.array(vv), np.array(kinds)
    col = np.zeros((len(uu), 3))
    rough = np.zeros(len(uu))
    relief = np.zeros(len(uu))
    for kind in ("Fore", "Hind"):
        sel = kinds == kind
        c, r, v = wing_paint_uv(uu[sel], vv[sel], kind)
        col[sel], rough[sel], relief[sel] = c, r, 0.0004 * v
    P, Nn = verts(o), normals(o)
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, rough)
    return o


def build_wings_low(nu=8, nv=3):
    m = Mesh()
    make_tags_bm(m.bm, ints=("side", "hind"))
    for kind, spec in WING_SPECS:
        for side in (1, -1):
            before = set(m.bm.verts)
            wing_sheet(m, spec, side, nu if kind == "Fore" else nu - 2, nv)
            tag_new_bm(m.bm, before, side=side, hind=int(kind == "Hind"))
    return m.finish(N + "Wings", GAME, recalc=False)          # wound outward as it is made


# ---------- per-vertex tags ----------
def make_tags_bm(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new_bm(bm, before, **values):
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


# ---------- the glowing pieces ----------
def zigzag(p, q, outward, seed, kinks=6, bulge=0.014, jag=0.0065):
    """A little arc of static from one tuft's tip to another's: bowed out, kinked sharp."""
    d = q - p
    perp = d.cross(outward).normalized()
    pts = []
    for k in range(kinks + 1):
        t = k / kinks
        off = 0.0 if k in (0, kinks) else (1 if k % 2 else -1) * jag * (0.6 + 0.8 * hash01(seed, k, 3))
        pts.append(p + d * t + outward * (bulge * math.sin(math.pi * t)) + perp * off)
    return pts


def arc_ends(which):
    """Each arc of a set: its two ends (lifted onto the fur's clumps), the way out from the skin there, and its bone."""
    out = []
    cow = [path[-1] for path, _ in cowlick_paths()]
    for kind, a, b in ARCS[which]:
        if kind == "th":
            p, q = ell_point(TH_C, TH_R, a), ell_point(TH_C, TH_R, b)
            n = ell_normal(TH_C, TH_R, (p + q) / 2)
            p, q = p + ell_normal(TH_C, TH_R, p) * FUR_H, q + ell_normal(TH_C, TH_R, q) * FUR_H
            out.append((p, q, n, "Body"))
        elif kind == "abd":
            p, np_ = abd_surface(*a)
            q, nq = abd_surface(*b)
            out.append((p + np_ * FUR_H, q + nq * FUR_H, (np_ + nq).normalized(), "Abd1" if (a[0] + b[0]) / 2 < 0.45 else "Abd2"))
        else:
            p, q = cow[a], cow[b]
            out.append((p, q, ((p + q) / 2 - HEAD_C).normalized(), "Head"))
    return out


ARC_BONES = ("Body", "Head", "Abd1", "Abd2")


def build_crackle(which, coll, sides=5):
    m = Mesh()
    make_tags_bm(m.bm, ints=("bone",))
    for k, (p, q, outward, owner) in enumerate(arc_ends(which)):
        before = set(m.bm.verts)
        m.tube(zigzag(p, q, outward, 7 + k + (0 if which == "A" else 20), bulge=0.011 if owner != "Head" else 0.008), lambda f: 0.0042, sides=sides)
        tag_new_bm(m.bm, before, bone=ARC_BONES.index(owner))
    return m.finish(N + "Crackle%s_Glow_%s" % (which, ARC_HEX), coll)


def build_tips(coll, seg=14, rings=8):
    m = Mesh()
    for side in (1, -1):
        m.ball(mir(ANT[-1], side), (ANT_TIP_R,) * 3, seg, rings)
    return m.finish(N + "Tips_Glow_" + TIP_HEX, coll)


def build_charge(coll, seg=16, rings=10):
    m = Mesh()
    for side in (1, -1):
        c, n = basket_frame(side)
        m.ball(c + n * (CHARGE_R * 0.55), (CHARGE_R,) * 3, seg, rings)
    return m.finish(N + "Charge_Glow_" + CHARGE_HEX, coll)


STING_BASE = TAIL_TIP + TAIL_DIR * (STING_SHOW - STING_LEN)


def build_sting(coll, sides=10, per=6):
    m = Mesh()
    pts = [STING_BASE.lerp(TAIL_TIP + TAIL_DIR * STING_SHOW, t / per) for t in range(per + 1)]
    m.tube(pts, lambda f: STING_R * (1 - f) ** 0.7 + 0.0007, sides=sides)
    return m.finish(N + "Sting_Glow_" + STING_HEX, coll)


def build_glints(coll, sides=10):
    """A soft catch-light on each eye, high on its front: a disc lying on the ellipsoid."""
    m = Mesh()
    bm = m.bm
    for side in (1, -1):
        out, fwd, up = eye_axes(side)
        c = eye_centre(side)
        for dirn, r in (((fwd * 0.75 + up * 0.5 + out * 0.42), 0.0105), ((fwd * 0.9 - up * 0.25 + out * 0.36), 0.0052)):
            a = dirn.normalized()
            ax, ay = a.cross(up).normalized(), None
            ay = a.cross(ax).normalized()

            def on_eye(x, y, a=a, ax=ax, ay=ay):
                d = (a + ax * x + ay * y).normalized()
                local = V(d.dot(out), d.dot(fwd), d.dot(up))
                k = 1 / math.sqrt((local.x / EYE_R[0]) ** 2 + (local.y / EYE_R[1]) ** 2 + (local.z / EYE_R[2]) ** 2)
                p = d * k
                return c + p + (p.normalized() * 0.0024)        # clear of the game eye's facets
            centre = bm.verts.new(on_eye(0, 0))
            ring = [bm.verts.new(on_eye(math.cos(TAU * j / sides) * r / 0.05, math.sin(TAU * j / sides) * r * 1.5 / 0.05)) for j in range(sides)]
            for j in range(sides):
                bm.faces.new((centre, ring[j], ring[(j + 1) % sides]))
    bm.normal_update()
    o = m.finish(N + "Glints_Glow_ffffff", coll, smooth_shade=False, recalc=False)
    # each disc seen from outside: its normals away from the eye's middle
    for p in o.data.polygons:
        side = 1 if p.center.x > 0 else -1
        if p.normal.dot(p.center - eye_centre(side)) < 0:
            p.flip()
    return o


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


def build_glows(coll, low=False):
    return {"Tips": build_tips(coll, 10 if low else 16, 6 if low else 10), "Charge": build_charge(coll, 10 if low else 18, 6 if low else 12),
            "Sting": build_sting(coll, 6 if low else 12, 3 if low else 6), "CrackleA": build_crackle("A", coll, 4 if low else 6),
            "CrackleB": build_crackle("B", coll, 4 if low else 6), "Glints": build_glints(coll, 7 if low else 12)}


def build_hi(clay=False):
    pieces = {"Skin": build_skin()}
    eyes = build_eyes(HI)
    pieces["EyeL"], pieces["EyeR"] = eyes["L"], eyes["R"]
    pieces["Antennae"] = build_antennae(HI, 20, 3)
    pieces["Legs"] = build_legs(HI, 22, 12)
    pieces["Mandibles"] = build_mandibles(HI, 16)
    pieces["Wings"] = build_wings_hi()
    glows = build_glows(HI)
    if not clay:
        paint_all(pieces)
    return pieces, glows


# ---------- painting ----------
def s_at_y(y):
    """How far along its middle line (metres) a point level with y lies."""
    ys = np.array([p.y for p in CL])
    return float(np.interp(y, ys, arc_lengths(CL)))


S_NECK, S_THORAX = s_at_y(-0.112), s_at_y(-0.01)
S_GOLD_END, S_STORM_END = s_at_y(0.215), s_at_y(0.338)      # the abdomen's gold band ends, then its storm band, then the snow-white tail
TEETH, ZAG = 9, 0.011                # each band's edge: a zigzag of this many teeth round it, this deep


def zig(theta, phase=0.0):
    x = theta * TEETH / TAU + phase
    return (2 * np.abs(x - np.floor(x + 0.5)) - 0.5) * 2 * ZAG


def skin_fields(P, Nn):
    h, tip, s, theta = fur_field(P, Nn)
    back = np.cos(theta)
    head = s < S_NECK + zig(theta, 0.3) * 0.0
    face = head & (Nn[:, 1] < -0.35) & (P[:, 2] < 0.52)
    cheeks = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(CHEEK[0], side)))
        cheeks = np.maximum(cheeks, 1 - smooth(0.022, 0.04, np.linalg.norm(P - c, axis=1)))
    clypeus = (1 - smooth(0.7, 1.0, np.hypot(P[:, 0] / 0.019, (P[:, 2] - 0.425) / 0.026))) * smooth(-0.21, -0.235, P[:, 1])     # a small rounded plate
    cow = np.zeros(len(P))
    cow_tip = np.zeros(len(P))
    for path, _ in cowlick_paths():
        f, dd = nearest_on(path[2:], P)
        near = 1 - smooth(0.011, 0.02, dd)
        cow = np.maximum(cow, near * (P[:, 2] > HEAD_C.z + 0.06))
        cow_tip = np.maximum(cow_tip, near * smooth(0.4, 1.0, f) * (P[:, 2] > HEAD_C.z + 0.06))
    # the bands: gold collar, storm-grey back (thorax); gold, storm, snow (abdomen); each edge zigzag
    collar = (s < S_THORAX + zig(theta) + 0.03 * (1 - smooth(-0.6, 0.2, back))) & (s >= S_NECK - 0.012)
    gold2 = (s > s_at_y(0.09) + zig(theta, 0.5)) & (s < S_GOLD_END + zig(theta))
    tail = s > S_STORM_END + zig(theta, 0.5)
    belly = smooth(-0.35, -0.8, back)
    return dict(h=h, tip=tip, s=s, theta=theta, back=back, head=head.astype(float), face=face.astype(float), cheeks=cheeks, clypeus=clypeus, cow=cow,
                cow_tip=cow_tip, collar=collar.astype(float), gold2=gold2.astype(float), tail=tail.astype(float), belly=belly)


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    F = skin_fields(P, Nn)
    col = np.broadcast_to(STORM, (n, 3)).copy()
    col = mix(col, STORM_DEEP, F["head"] * 0.7)
    gold = mix(np.broadcast_to(GOLD, (n, 3)), GOLD_DEEP, smooth(0.2, -0.6, F["back"]) * 0.45)          # deeper gold down its sides
    col = mix(col, gold, np.maximum(F["collar"], F["gold2"]))
    snow = mix(np.broadcast_to(SNOW, (n, 3)), SNOW_TINT, smooth(0.3, -0.5, F["back"]) * 0.22 + smooth(0.9, 1.0, F["s"] / CL_L) * 0.15)
    col = mix(col, snow, F["tail"])
    face_gold = mix(np.broadcast_to(GOLD_PALE, (n, 3)), GOLD, 0.3 + 0.5 * smooth(0.02, 0.07, np.abs(P[:, 0])))
    col = mix(col, face_gold, np.clip(F["face"] * 0.9 + F["cheeks"], 0, 1))
    col = mix(col, GOLD_DEEP * 0.8, F["clypeus"] * 0.7)                # a small glossy plate (dark, it read as a gaping mouth)
    col = mix(col, STORM_DEEP * 0.8, F["belly"] * 0.35 * (1 - F["tail"]))
    # each clump: darker at its root, its tip catching the light
    col = col * (0.8 + 0.28 * F["tip"])[:, None]
    strands = np.sin(F["theta"] * 0.13 / 0.0032 * 6 + 3 * value_noise(P, 90.0, 71)) * 0.5 + 0.5       # fine hairs down each clump
    col = col * (0.95 + 0.08 * strands)[:, None]
    col = col * (0.94 + 0.12 * hash01(np.floor(F["s"] / FUR_ROW * 3).astype(int), np.floor(F["theta"] * 9).astype(int), 0, 53))[:, None]
    # the cowlick: storm-grey at its roots, its tips charged gold
    cow = mix(np.broadcast_to(STORM_DEEP, (n, 3)), GOLD_PALE, F["cow_tip"])
    col = mix(col, cow, F["cow"])
    rough = 0.72 - 0.12 * F["tip"] - 0.35 * F["clypeus"]
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def eye_local(o, side):
    ax = eye_axes(side)
    q = verts(o) - np.array(tuple(eye_centre(side)))
    return [(q * np.array(tuple(a))).sum(1) / r for a, r in zip(ax, EYE_R)]


def hex_cells(x, y, size):
    """Distance to the nearest hexagon edge (0 on an edge, about 0.5 at a middle), on a grid of this cell size."""
    q = np.stack([x, y], 1) / size
    best1 = np.full(len(x), 1e9)
    best2 = np.full(len(x), 1e9)
    for basis in (np.array([0.0, 0.0]), np.array([0.5, math.sqrt(3) / 2])):
        g = np.stack([np.round(q[:, 0] - basis[0]), np.round((q[:, 1] - basis[1]) / math.sqrt(3))], 1)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                c = np.stack([g[:, 0] + dx + basis[0], (g[:, 1] + dy) * math.sqrt(3) + basis[1]], 1)
                d = np.linalg.norm(q - c, axis=1)
                nearer = d < best1
                best2 = np.where(nearer, best1, np.minimum(best2, d))
                best1 = np.where(nearer, d, best1)
    return (best2 - best1) / 2


def carve_eye(o, side):
    ex, ef, eu = eye_local(o, side)
    edge = hex_cells(ef * 1.0, eu * 1.0, 0.075)
    P, Nn = verts(o), normals(o)
    set_verts(o, P + Nn * (0.00045 * smooth(0.0, 0.25, edge))[:, None])        # each facet a tiny dome


def paint_eye(o, side):
    ex, ef, eu = eye_local(o, side)
    edge = hex_cells(ef, eu, 0.075)
    col = mix(np.broadcast_to(EYE_BASE, (len(ex), 3)), EYE_FACET, (1 - smooth(0.0, 0.09, edge)) * 0.8)
    sheen = smooth(-0.2, 0.7, ef * 0.6 + eu * 0.8) * 0.55                # a violet sheen high on its front: the storm's light in it
    col = mix(col, EYE_SHEEN, sheen)
    col = mix(col, EYE_BASE * 0.6, smooth(0.1, -0.6, ex) * 0.5)
    paint(o, np.clip(col, 0, 1), 0.1 + 0.08 * (1 - smooth(0.0, 0.09, edge)), np.zeros(len(ex)))


def paint_antennae(o):
    P = verts(o)
    seg = read_tag(o, "seg")
    n = len(P)
    flag = (seg == 2) | (seg == 4)
    out = np.zeros(n)
    for side, sg in ((1, 2), (-1, 4)):
        sel = seg == sg
        f, _ = nearest_on(ant_segments(side)[1], P[sel])
        out[sel] = f
    col = mix(np.broadcast_to(CHITIN_EDGE, (n, 3)), CHITIN, flag.astype(float))
    col = mix(col, GOLD_DEEP * 0.7, smooth(0.75, 1.0, out) * flag * 0.6)         # warming toward the spark at its tip
    ring = (np.abs(np.sin(out * 34)) < 0.18) * flag * smooth(0.1, 0.2, out)
    col = mix(col, CHITIN_EDGE, ring * 0.5)                                       # its segments
    paint(o, np.clip(col, 0, 1), np.full(n, 0.35), np.zeros(n))


def paint_legs(o):
    P, Nn = verts(o), normals(o)
    leg = read_tag(o, "leg")
    seg = read_tag(o, "seg")
    n = len(P)
    col = np.broadcast_to(STORM_DEEP, (n, 3)).copy()
    hair = smooth(0.55, 0.85, value_noise(P * np.array([1, 1, 0.25]), 260.0, 61))      # a fringe of fine hairs down them
    col = mix(col, STORM_PALE, hair * 0.35 * (seg < 2))
    rough = np.full(n, 0.6)
    for side, k in ((1, 2), (-1, 5)):
        sel = (leg == k) & (seg == 1)
        c, nb = basket_frame(1 if k == 2 else -1)
        rel = P[sel] - np.array(tuple(c))
        outer = (rel * np.array(tuple(nb))).sum(1)
        hollow = smooth(-0.002, 0.004, outer)
        rim = 1 - smooth(0.0, 0.006, np.abs(np.linalg.norm(rel - np.outer(outer, np.array(tuple(nb))), axis=1) - BASKET_W * 0.85))
        col[sel] = mix(mix(col[sel], CHITIN * 0.7, hollow), GOLD, rim * 0.8)     # its basket: a glossy black hollow, rimmed with gold hairs
        rough[sel] = 0.6 - 0.4 * hollow
    tars = seg == 2
    col = mix(col, CHITIN_EDGE, tars * 0.5)
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_mandibles(o):
    P = verts(o)
    n = len(P)
    tipward = smooth(0.012, 0.03, np.abs(P[:, 0] - 0.03 * np.sign(P[:, 0])))
    col = mix(np.broadcast_to(CHITIN, (n, 3)), GOLD_DEEP * 0.6, tipward * 0.4)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.3), np.zeros(n))


def paint_all(pieces):
    paint_skin(pieces["Skin"])
    for side, tag in ((1, "L"), (-1, "R")):
        carve_eye(pieces["Eye" + tag], side)
        paint_eye(pieces["Eye" + tag], side)
    paint_antennae(pieces["Antennae"])
    paint_legs(pieces["Legs"])
    paint_mandibles(pieces["Mandibles"])


VIEWS = [(0, -1, 0.2), (0.62, -0.72, 0.3), (1, 0, 0.12), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.4, 0.5, 0.75)]
VIEW_AT = (0, 0.08, 0.44)
FACE_AT = (0, -0.2, 0.48)
EXTRA = [(0.15, -1, 0.15, 0.85, FACE_AT), (1, -0.6, 0.3, 0.85, FACE_AT), (0.2, -0.5, -0.8, 1.6, (0, 0.05, 0.36)), (0.3, 1, 0.3, 1.0, (0, 0.3, 0.42)),
         (0.3, -0.6, 0.9, 0.8, (0, -0.06, 0.6)), (1, 0.1, 0.5, 0.8, (0, -0.06, 0.6))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "tail tip", tuple(round(v, 3) for v in TAIL_TIP), flush=True)
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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 6000
PIECES = ("Skin", "EyeL", "EyeR", "Antennae", "Legs", "Mandibles")
SCALES = {"EyeL": 2.2, "EyeR": 2.2, "Antennae": 1.5, "Legs": 1.1, "Mandibles": 1.5, "Wings": 0.9}


def is_head(c):
    """Its head: it gets more of the atlas."""
    return c.y < -0.105


def eye_signed(P, side):
    """Per point: its distance out from an eye's surface (metres, roughly), and the point on the eye's surface in the same direction."""
    ax = eye_axes(side)
    c = np.array(tuple(eye_centre(side)))
    q = P - c
    loc = np.stack([(q * np.array(tuple(a))).sum(1) / r for a, r in zip(ax, EYE_R)], 1)
    rho = np.linalg.norm(loc, axis=1)
    return (rho - 1) * min(EYE_R), rho


def low_eye_piece(side, tag):
    m = Mesh()
    a = eye_axes(side)
    c = eye_centre(side)
    oriented_ball(m, c, EYE_R, a, 20, 12)
    # only what can ever show: the back of the eye, sunk in its head, goes
    dead = [f for f in m.bm.faces if all((v.co - c).dot(a[0]) / EYE_R[0] < -0.4 for v in f.verts)]
    bmesh.ops.delete(m.bm, geom=dead, context="FACES")
    return m.finish(N + "Eye" + tag + "Low", GAME)


def build_low(pieces):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    select_only([lows["Skin"]])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)          # every face outward
    bpy.ops.object.mode_set(mode="OBJECT")
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye_piece(side, tag)
    # QuadriFlow leaves a few lone vertices standing out of the surface (pimples a centimetre high): each back onto it
    P = verts(lows["Skin"])
    tree = tree_of(pieces["Skin"])
    snapped = 0
    for i in range(len(P)):
        loc, nrm, _, dist = tree.find_nearest(V(*P[i]))
        if loc is not None and dist > 0.003:
            P[i] = tuple(loc - nrm * 0.0005)
            snapped += 1
    print("SNAPPED", snapped, "skin vertices back onto the surface", flush=True)
    # the skin of its sockets level with an eye's facets (from 2 mm inside to 4 mm out) goes 3 mm behind them (level, they z-fight; measured in
    # the ellipsoid's own units, the band was too narrow along its long axis)
    sunk = 0
    for side, tag in ((1, "L"), (-1, "R")):
        eye = tree_of(lows["Eye" + tag])
        out_axis = eye_axes(side)[0]
        c = eye_centre(side)
        for i in range(len(P)):
            loc, nrm, _, dist = eye.find_nearest(V(*P[i]))
            if loc is None or dist > 0.006 or (loc - c).dot(out_axis) / EYE_R[0] < -0.3:
                continue
            signed = (V(*P[i]) - loc).dot(nrm)
            if -0.002 < signed < 0.004:
                P[i] = tuple(loc - nrm * 0.003)
                sunk += 1
    print("SOCKET", sunk, "skin vertices sunk behind the eyes", flush=True)
    set_verts(lows["Skin"], P)
    lows["Antennae"] = build_antennae(GAME, 7, 1)
    lows["Legs"] = build_legs(GAME, 7, 3)
    lows["Mandibles"] = build_mandibles(GAME, 6)
    lows["Wings"] = build_wings_low(8, 5)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


def bad_uv_faces(o):
    """Faces in UV islands that collapsed, folded (triangles facing both ways in the map) or lapped over themselves."""
    uvd = o.data.uv_layers.active.data
    out, signs = set(), {}
    for p in o.data.polygons:
        a, b2, c = [uvd[l].uv for l in list(p.loop_indices)[:3]]
        ar = (b2.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b2.y - a.y)
        if abs(ar) < 1e-10:
            out.add(p.index)
        signs[p.index] = ar > 0
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        island, stack = [], [f]
        while stack:
            g = stack.pop()
            if g.index in seen:
                continue
            seen.add(g.index)
            island.append(g.index)
            for e in g.edges:
                if not e.seam:
                    stack += [h for h in e.link_faces if h.index not in seen]
        up = sum(signs[i] for i in island)
        if 0 < up < len(island) or self_overlaps(o, island):
            out.update(island)
    bm.free()
    return out


def self_overlaps(o, faces, res=384):
    """Whether these faces' UVs cover any texel twice (at this resolution over their own bounds)."""
    uvd = o.data.uv_layers.active.data
    tris = [[np.array(uvd[l].uv) for l in o.data.polygons[i].loop_indices] for i in faces]
    pts = np.array([q for t in tris for q in t])
    lo, span = pts.min(0), np.maximum(pts.max(0) - pts.min(0), 1e-9)
    owner = np.zeros((res, res), dtype=bool)
    for t in tris:
        a, b, c = [(q - lo) / span * (res - 1) for q in t[:3]]
        mn = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        mx = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        ys, xs = np.mgrid[mn[1]:mx[1] + 1, mn[0]:mx[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 > 0.02) & (w1 > 0.02) & (w0 + w1 < 0.98) & (xs < res) & (ys < res)
        if owner[ys[inside], xs[inside]].any():
            return True
        owner[ys[inside], xs[inside]] = True
    return False


UV_ANGLE = {"Skin": 66, "Wings": 40, "Legs": 55, "Antennae": 55}     # the projection's angle per piece (wider: fewer, bigger charts, a fuller atlas)


def bee_unwrap(lows, margin=0.0035):
    """Each piece on its own: the projection's charts as seams (and one round its neck, where the head's share changes), an angle-based unwrap that
    can't fold a chart over itself, collapsed fragments projected again, each scaled to its share; all packed together."""
    for key, o in lows.items():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        select_only([o])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(UV_ANGLE.get(key, 66)), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.seams_from_islands()
        bpy.ops.object.mode_set(mode="OBJECT")
        if key == "Skin":
            bm = bmesh.new()
            bm.from_mesh(o.data)
            for e in bm.edges:
                hs = [is_head(f.calc_center_median()) for f in e.link_faces]
                if len(hs) == 2 and hs[0] != hs[1]:
                    e.seam = True
            bm.to_mesh(o.data)
            bm.free()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.002)
        bpy.ops.object.mode_set(mode="OBJECT")
        bad = bad_uv_faces(o)
        for angle, again in ((50, True), (30, False)):
            if not bad:
                break
            print("UV REDO", key, len(bad), "faces in islands collapsed, folded or lapped over themselves: at", angle, flush=True)
            o.data.polygons.foreach_set("select", [p.index in bad for p in o.data.polygons])
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_linked(delimit={"SEAM"})
            bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
            if again:
                bpy.ops.uv.seams_from_islands()
                bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.002)
            bpy.ops.object.mode_set(mode="OBJECT")
            bad = bad_uv_faces(o) if again else set()
        polys = list(o.data.polygons)
        if key == "Skin":
            scale_uv_to(o, [p for p in polys if is_head(p.center)], 1.6)
            scale_uv_to(o, [p for p in polys if not is_head(p.center)], 1.0)
        else:
            scale_uv_to(o, polys, SCALES.get(key, 1.0))
    objs = list(lows.values())
    select_only(objs)
    for o in objs:
        o.data.polygons.foreach_set("select", [True] * len(o.data.polygons))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, rotate_method="ANY", scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def flatten_normals(o, pad=4):
    """The wings' share of the normal map made flat: their relief is a fraction of a millimetre, and baked on their slender tips it came out
    turned away (black notches at the tips)."""
    img = bpy.data.images[PET + "_Normal"]
    if img.packed_file:                  # (edited while packed, the packed copy kept the old pixels: the .blend and the FBX disagreed with the PNG)
        img.unpack(method="REMOVE")
        img.reload()
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    mask = np.zeros((h, w), dtype=bool)
    uv = o.data.uv_layers.active.data
    for p in o.data.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * (w, h) for i in loops[:3]]
        lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - pad, 0, (w - 1, h - 1))
        hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + pad, 0, (w - 1, h - 1))
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        for p0, p1 in ((a, b), (b, c), (c, a)):             # and every texel within the padding of its edges (a sliver holds no texel centre)
            e = p1 - p0
            t = np.clip(((qx - p0[0]) * e[0] + (qy - p0[1]) * e[1]) / max(e @ e, 1e-12), 0, 1)
            inside |= np.hypot(qx - p0[0] - e[0] * t, qy - p0[1] - e[1] * t) <= pad
        mask[ys[inside], xs[inside]] = True
    px[mask] = (0.5, 0.5, 1.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.save()
    img.pack()
    return int(mask.sum())


# ---------- the skeleton ----------
NECK = V(0, -0.106, 0.478)
WAIST = V(0, 0.085, 0.488)
ABD2_AT = 0.45                       # where along its abdomen its second bone takes over
LEG_TAGS = ("L1", "L2", "L3", "R1", "R2", "R3")


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", TH_C.copy(), "Root"), ("Head", NECK.copy(), "Body"),
             ("Abd1", WAIST.copy(), "Body"), ("Abd2", abd_at(ABD2_AT), "Abd1"), ("Sting", STING_BASE.copy(), "Abd2")]
    for side, tag in ((1, "L"), (-1, "R")):
        a = [mir(q, side) for q in ANT]
        bones += [("Ant%s1" % tag, a[0], "Head"), ("Ant%s2" % tag, a[1], "Ant%s1" % tag), ("Wing" + tag, mir(FORE[0], side), "Body")]
        for k in range(3):
            hip, knee, ankle, toe = leg_points(side, k)
            bones += [("Leg%s%d" % (tag, k + 1), hip, "Body"), ("Shin%s%d" % (tag, k + 1), knee, "Leg%s%d" % (tag, k + 1))]
    return armature(bones)


def skin_weights(P):
    """Head, thorax, and the abdomen's two bones, each passing to the next over a short stretch (its neck, its waist, the middle of its abdomen)."""
    s, _, _ = body_coords(P)
    s_waist, s_abd2 = s_at_y(WAIST.y), s_at_y(abd_at(ABD2_AT).y)
    head = 1 - smooth(S_NECK - 0.022, S_NECK + 0.018, s)
    abd = smooth(s_waist - 0.02, s_waist + 0.035, s)
    abd2 = smooth(s_abd2 - 0.065, s_abd2 + 0.065, s)
    out = []
    for i in range(len(P)):
        w = {"Head": head[i], "Body": (1 - head[i]) * (1 - abd[i]), "Abd1": abd[i] * (1 - abd2[i]), "Abd2": abd[i] * abd2[i]}
        out.append({k: float(v) for k, v in w.items() if v > 1e-4})
    return out


def tag_weights(o, tags, names):
    """Each vertex rigid on the bone its tag names."""
    t = read_tag(o, tags) if isinstance(tags, str) else tags
    return [{names(int(k)): 1.0} for k in t]


def glow_side_weights(o, left, right):
    return [{left if v.co.x > 0 else right: 1.0} for v in o.data.vertices]


def game_glows(lows):
    g = build_glows(GAME, low=True)
    # the catch-lights laid onto the game eyes' own facets, 1.5 mm off them (laid on the true ellipsoid, one lay level with a facet and one stood
    # off it)
    trees = {1: tree_of(lows["EyeL"]), -1: tree_of(lows["EyeR"])}
    gl = g["Glints"]
    for v in gl.data.vertices:
        loc, nrm, _, _ = trees[1 if v.co.x > 0 else -1].find_nearest(v.co)
        v.co = loc + nrm * 0.0015
    gl.data.update()
    return g


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    for tag in "LR":
        rigid(lows["Eye" + tag], "Head")
    rigid(lows["Mandibles"], "Head")
    weigh(lows["Antennae"], tag_weights(lows["Antennae"], "seg", lambda k: ("AntL1", "AntL2", "AntR1", "AntR2")[k - 1]))
    leg, seg = read_tag(lows["Legs"], "leg"), read_tag(lows["Legs"], "seg")
    weigh(lows["Legs"], [{("Leg" if sg == 0 else "Shin") + LEG_TAGS[int(lg)]: 1.0} for lg, sg in zip(leg, seg)])
    wings = lows.pop("Wings")
    weigh(wings, [{"WingL" if sd > 0 else "WingR": 1.0} for sd in read_tag(wings, "side")])
    weigh(glows["Tips"], glow_side_weights(glows["Tips"], "AntL2", "AntR2"))
    weigh(glows["Charge"], glow_side_weights(glows["Charge"], "ShinL3", "ShinR3"))
    rigid(glows["Sting"], "Sting")
    for k in ("CrackleA", "CrackleB"):
        weigh(glows[k], [{ARC_BONES[int(b)]: 1.0} for b in read_tag(glows[k], "bone")])
    rigid(glows["Glints"], "Head")
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body, wings] + list(glows.values()))
    return body, wings


# ---------- poses, written as PetRig's tables (turns in the game's axes: x pitch, nose up +; y yaw; z roll) ----------
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))


def from_game(v):
    return CM @ (Matrix.Rotation(v[0], 3, "X") @ Matrix.Rotation(v[1], 3, "Y") @ Matrix.Rotation(v[2], 3, "Z")) @ CM


def to_game(R):
    e = (CM @ R @ CM).to_euler("ZYX")
    return (e.x, e.y, e.z)


def game_vec(b):
    return (-b.x, b.z, b.y)


def blender_vec(gv):
    return V(-gv[0], gv[2], gv[1])


def spec(table):
    out = {}
    for bone, v in table.items():
        q = from_game(v).to_quaternion()
        axis, angle = q.to_axis_angle()
        mv = blender_vec(v[3:6]) if len(v) > 3 else V(0, 0, 0)
        out[bone] = (tuple(axis), math.degrees(angle), tuple(mv))
    return out


def slerp_tables(a, b, w):
    out = {}
    for bone in set(a) | set(b):
        va, vb = a.get(bone, (0, 0, 0)), b.get(bone, (0, 0, 0))
        q = from_game(va).to_quaternion().slerp(from_game(vb).to_quaternion(), w)
        ma = Vector(va[3:6] if len(va) > 3 else (0, 0, 0))
        mb = Vector(vb[3:6] if len(vb) > 3 else (0, 0, 0))
        out[bone] = to_game(q.to_matrix()) + tuple(ma.lerp(mb, w))
    return out


def mirror_table(t):
    """Each left bone's turn copied to its right twin, mirrored (x kept, y and z flipped)."""
    out = dict(t)
    for b, v in t.items():
        m = re.match(r"^(Ant|Wing|Leg|Shin)L(\d?)$", b)
        if m and m.group(1) + "R" + m.group(2) not in t:
            out[m.group(1) + "R" + m.group(2)] = (v[0], -v[1], -v[2]) + ((-v[3], v[4], v[5]) if len(v) > 3 else ())
    return out


STING_OUT = 0.052                    # metres its sting slides out of its tail


def pose_tables():
    t = {}
    t["WingUp"] = mirror_table({"WingL": (0, 0, -0.6)})
    t["WingDown"] = mirror_table({"WingL": (0, 0, 0.24)})
    t["WingFwd"] = mirror_table({"WingL": (0, -0.4, 0)})
    t["WingBack"] = mirror_table({"WingL": (0, 0.14, 0)})
    for ud, roll in (("Up", -0.6), ("Down", 0.24)):           # the corners of its figure-eight beat: up or down while forward or back
        for fb, yaw in (("Fwd", -0.4), ("Back", 0.14)):
            t["Wing" + ud + fb] = mirror_table({"WingL": (0, yaw, roll)})
    out = -0.12                          # its legs rolled out a little (in, they met its abdomen)
    t["Zip"] = mirror_table({"Body": (-0.32, 0, 0), "Abd1": (0.06, 0, 0), "Head": (0.15, 0, 0), "AntL1": (-0.25, 0, 0),
                             "LegL1": (-0.2, 0, out), "ShinL1": (-0.15, 0, 0), "LegL2": (-0.25, 0, out), "ShinL2": (-0.15, 0, 0), "LegL3": (-0.28, 0, -0.22), "ShinL3": (-0.12, 0, 0)})
    t["Roll"] = {"Body": (0, 0, 1.6)}            # a quarter-plus of its barrel roll (the game spins it right round)
    t["Charge"] = mirror_table({"Body": (0.3, 0, 0), "Abd1": (-0.12, 0, 0), "Abd2": (-0.08, 0, 0), "Head": (-0.1, 0, 0), "AntL1": (0.25, 0, -0.2), "AntL2": (0.2, 0, 0)})
    sting = (0, 0, 0) + game_vec(TAIL_DIR * STING_OUT)
    # its sting aimed straight down: nose up, its abdomen curled under, its legs splayed out of the way (hanging, the curl swept into them)
    t["Sting"] = mirror_table({"Body": (0.2, 0, 0), "Abd1": (0.2, 0, 0), "Abd2": (0.52, 0, 0), "Sting": sting, "Head": (-0.12, 0, 0),
                               "LegL1": (0.5, 0, -0.25), "ShinL1": (0.4, 0, 0), "LegL2": (0.3, 0, -0.45), "LegL3": (0.55, 0, -0.5), "ShinL3": (0.15, 0, 0)})
    t["Look"] = mirror_table({"Head": (0.05, 0.3, 0.08), "AntL1": (0, 0.2, 0)})
    t["Antenna"] = {"AntL1": (0.2, 0.1, -0.2), "AntL2": (0.3, 0, 0)}
    return {k: {b: tuple(round(float(x), 4) for x in v) for b, v in tab.items()} for k, tab in t.items()}


# ---------- checks ----------
def posed(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    tris = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return co.reshape(-1, 3), tris


def dominant(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in o.data.vertices]


def pairs(co_a, tris_a, fa, co_b, tris_b, fb):
    if not fa or not fb:
        return 0
    ta = BVHTree.FromPolygons([tuple(c) for c in co_a], [tris_a[f] for f in fa])
    tb = BVHTree.FromPolygons([tuple(c) for c in co_b], [tris_b[f] for f in fb])
    return len(ta.overlap(tb))


class Checker:
    def __init__(self, body, wings, sting):
        self.body, self.wings, self.sting = body, wings, sting
        d = dominant(body)
        fp = np.zeros(len(body.data.polygons), dtype=int)
        body.data.attributes["piece"].data.foreach_get("value", fp)
        _, tris = posed(body)
        self.tris = tris

        def faces(test):
            return [i for i in range(len(tris)) if test(fp[i], d[tris[i][0]])]
        sk = PIECES.index("Skin")
        self.skin = faces(lambda p, b: p == sk)
        self.abdomen = faces(lambda p, b: p == sk and b in ("Abd1", "Abd2"))
        self.abd2 = faces(lambda p, b: p == sk and b == "Abd2")
        self.thorax = faces(lambda p, b: p == sk and b in ("Body", "Head"))
        self.front = faces(lambda p, b: p == sk and b in ("Head", "Body"))
        self.solid = faces(lambda p, b: p != PIECES.index("Legs") and p != PIECES.index("Antennae"))
        self.legs = {t: faces(lambda p, b, t=t: p == PIECES.index("Legs") and b.endswith(t)) for t in LEG_TAGS}
        self.shins = {t: faces(lambda p, b, t=t: p == PIECES.index("Legs") and b == "Shin" + t) for t in LEG_TAGS}
        self.flag = faces(lambda p, b: p == PIECES.index("Antennae") and b.endswith("2"))
        self.ant = faces(lambda p, b: p == PIECES.index("Antennae"))
        # the wings, away from their roots (rooted in the thorax by design)
        wco, wtris = posed(wings)
        self.wtris = wtris
        hind = read_tag(wings, "hind")
        self.wing_out, self.kind = {}, {}
        for side in (1, -1):
            out = []
            for i, t in enumerate(wtris):
                root = np.array(tuple(mir((HIND if hind[t[0]] else FORE)[0], side)))
                if np.sign(wco[t[0], 0]) == side and min(np.linalg.norm(wco[v] - root) for v in t) > 0.045:
                    out.append(i)
            self.wing_out[side] = out
            self.kind[side] = ([i for i in out if not hind[wtris[i][0]]], [i for i in out if hind[wtris[i][0]]])

    def run(self):
        co, tris = posed(self.body)
        wco, wtris = posed(self.wings)
        out = {}
        out["shins x skin"] = sum(pairs(co, tris, self.shins[t], co, tris, self.skin) for t in LEG_TAGS)
        per = {t: pairs(co, tris, self.legs[t], co, tris, self.abdomen) for t in LEG_TAGS}
        out["legs x abdomen"] = sum(per.values())
        self.which = {"legs x abdomen": {t: n for t, n in per.items() if n}}
        out["abd2 x thorax"] = pairs(co, tris, self.abd2, co, tris, self.thorax)
        out["fore x hind"] = sum(pairs(wco, wtris, self.kind[sd][0], wco, wtris, self.kind[sd][1]) for sd in (1, -1))
        out["legs x legs"] = sum(pairs(co, tris, self.legs[a], co, tris, self.legs[b]) for i, a in enumerate(LEG_TAGS) for b in LEG_TAGS[i + 1:])
        out["feelers x skin"] = pairs(co, tris, self.flag, co, tris, self.skin)
        allw = self.wing_out[1] + self.wing_out[-1]
        out["wings x body"] = pairs(wco, wtris, allw, co, tris, self.skin + self.ant + sum(self.legs.values(), []))
        self.which["wings x"] = {"fore x skin": pairs(wco, wtris, self.kind[1][0] + self.kind[-1][0], co, tris, self.skin),
                                 "hind x skin": pairs(wco, wtris, self.kind[1][1] + self.kind[-1][1], co, tris, self.skin)}
        if self.which["wings x"]["fore x skin"] + self.which["wings x"]["hind x skin"]:
            tb = BVHTree.FromPolygons([tuple(c) for c in co], [tris[f] for f in self.skin])
            ta = BVHTree.FromPolygons([tuple(c) for c in wco], [wtris[f] for f in allw])
            hits = ta.overlap(tb)
            self.which["wings x"]["at"] = sorted({tuple(np.round(wco[wtris[allw[a]][0]], 2)) for a, _ in hits})[:4]
        out["wing x wing"] = pairs(wco, wtris, self.wing_out[1], wco, wtris, self.wing_out[-1])
        sco, stris = posed(self.sting)
        out["sting x legs"] = pairs(sco, stris, list(range(len(stris))), co, tris, sum(self.legs.values(), []))
        out["low z"] = round(float(co[:, 2].min()), 4)
        return out


TRANSITIONS = [("Rest", "WingUp"), ("WingUp", "WingDown"), ("WingFwd", "WingBack"), ("WingUpFwd", "WingDownBack"), ("WingUpBack", "WingDownFwd"),
               ("WingUpFwd", "WingUpBack"), ("WingDownFwd", "WingDownBack"), ("Rest", "Zip"), ("Rest", "Roll"), ("Rest", "Charge"),
               ("Charge", "Sting"), ("Sting", "Rest"), ("Rest", "Look"), ("Rest", "Antenna")]
MINS = ("low z",)


def check_transitions(rig, chk, tables):
    tables = dict(tables, Rest={})
    for na, nb in TRANSITIONS:
        worst = {}
        for k in range(11):
            pose(rig, spec(slerp_tables(tables[na], tables[nb], k / 10)))
            for key, v in chk.run().items():
                worst[key] = min(worst.get(key, 9.0), v) if key in MINS else max(worst.get(key, 0), v)
        flag = {k: v for k, v in worst.items() if k not in MINS and v > 0}
        print("TRANSITION", na, "->", nb, flag if flag else "clean", flush=True)


POSE_VIEWS = [(0.62, -0.72, 0.3, 2.2, VIEW_AT), (1, 0.05, 0.1, 2.2, VIEW_AT), (0, -1, 0.15, 2.2, VIEW_AT), (-0.4, 0.8, 0.5, 2.2, VIEW_AT)]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, glows = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces)
    if STAGE == "all":
        bee_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.4, 0.38, 0.3, 1), far=("Skin",), reach=(0.003, 0.008),
                 far_reach=(0.009, 0.022), reaches={"Wings": (0.0015, 0.004), "Antennae": (0.002, 0.006), "Mandibles": (0.002, 0.005), "Legs": (0.003, 0.008)})
        print("WING NORMALS FLATTENED", flatten_normals(lows["Wings"]), "texels", flush=True)
    else:
        clay = bpy.data.materials.new("clay")
        gg = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        gg.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    # the wings flat-shaded: a plate 2 mm thick with a sharp tip, smooth-shaded, had its tip corners' normals averaged round onto its edges and
    # shaded black
    lows["Wings"].data.polygons.foreach_set("use_smooth", [False] * len(lows["Wings"].data.polygons))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    tree = tree_of(pieces["Skin"])
    print("SKIN GAP (low from high, m)", round(surface_gap(lows["Skin"], tree), 4), flush=True)
    gaps = sorted(((tree.find_nearest(v.co)[3], tuple(round(x, 3) for x in v.co)) for v in lows["Skin"].data.vertices), reverse=True)[:6]
    print("   worst at", gaps, flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)
    glows = game_glows(lows)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton()
    body, wings = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "WINGS tris", sum(len(p.vertices) - 2 for p in wings.data.polygons),
          "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), max(len(v.groups) for v in wings.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body, wings] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), "box middle", round((max(zs) + min(zs)) / 2, 4), flush=True)
    chk = Checker(body, wings, glows["Sting"])
    pose(rig, {})
    print("POSE Rest", chk.run(), chk.which, flush=True)
    tables = pose_tables()
    only = ARGS[ARGS.index("only") + 1].split(",") if "only" in ARGS else None
    for name, table in tables.items():
        if only and name not in only:
            continue
        pose(rig, spec(table))
        print("POSE", name, chk.run(), chk.which if "which" in ARGS else "", flush=True)
        if STAGE == "rig" and "noshots" not in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=420)
    if "transitions" in ARGS or STAGE == "all":
        check_transitions(rig, chk, tables)
    lib = {k: spec(v) for k, v in tables.items()}
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    if "tables" in ARGS or STAGE == "all":
        for name, table in tables.items():
            print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
        for name in ("Body", "Head", "Abd1", "Abd2", "Sting", "WingL", "AntL2", "ShinL3"):
            p = rig.data.bones[name].head_local
            print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=560)
        for name in ("WingUp", "Zip", "Roll", "Charge", "Sting"):
            pose(rig, spec(tables[name]))
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS[:2], size=420)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 2.4, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values()), extras=[wings]), flush=True)
    print("DONE", flush=True)

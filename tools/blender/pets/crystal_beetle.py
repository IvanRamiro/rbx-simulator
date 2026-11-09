"""The Crystal Beetle (Rare, Crystal; Elemental Core Egg): "Its shell grows a new crystal for every year it lives. Collectors have spent fortunes on the moults."

A crystal-horn rhinoceros beetle (the owner's choice, 2026-11-09), in a design language of its own: a living geode of glass and chitin. A stout, proud
rhinoceros beetle: a great rounded pronotum and head of glossy indigo chitin with an oil-slick sheen; its wing cases two smooth domes of clear cyan
crystal you can see into, layered inside with phantom growth layers, one a year, like a tree's rings; its great horn a single quartz crystal grown in
stacked hexagonal segments, one a year, its newest, the terminated tip, glowing. Amber hairs on its legs, amber lamellae on its clubbed antennae, spiny
toothed forelegs, hooked claws. Its hind wings, smoky membranes, lie folded under the domes until it flies.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/crystal_beetle.py -- [clay|paint|rig|all|tables] [review dir]

Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Stands on the ground (its feet at z = 0). The maps go to assets/pets/ElementalCoreEgg/.

What touches what: the body (pronotum, thorax, abdomen) is one piece; the head sits in under the pronotum's front; the horn roots in the head; the eyes
sit in the head's sides; the antennae root in the head below them; the wing cases' fronts tuck under the pronotum's back edge and rest over the
abdomen with a gap between, where the folded wings lie; each leg is three rigid segments joined on balls round their pivots (a joint turns in place:
no gap opens), its hip ball sunk into the body, its feet on the ground.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "CrystalBeetle"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours ----------
CHITIN, CHITIN_DEEP, SHEEN_V, SHEEN_T = rgb(38, 34, 82), rgb(16, 14, 36), rgb(120, 92, 200), rgb(60, 150, 170)
CRYSTAL, CRYSTAL_DEEP, CRYSTAL_PALE = rgb(110, 214, 236), rgb(22, 92, 122), rgb(214, 248, 255)
AMBER, AMBER_DEEP = rgb(214, 152, 64), rgb(120, 72, 30)
MEMBRANE, VEIN = rgb(176, 186, 206), rgb(52, 50, 74)
TIP_HEX = "9ff4ff"

# ---------- the frame of it (its left; mirrored) ----------
PRONOTUM_C, PRONOTUM_R = V(0, -0.078, 0.13), (0.125, 0.088, 0.08)
THORAX_C, THORAX_R = V(0, -0.03, 0.085), (0.085, 0.09, 0.045)
ABDOMEN_C, ABDOMEN_R = V(0, 0.13, 0.098), (0.114, 0.152, 0.054)
HEAD_C, HEAD_R = V(0, -0.18, 0.1), (0.058, 0.055, 0.045)
CLYPEUS_C, CLYPEUS_R = V(0, -0.222, 0.08), (0.046, 0.022, 0.018)      # a broad flat plate over its mouth
EYE_C, EYE_R = V(0.05, -0.205, 0.108), 0.016
EYE_AXIS = V(0.85, -0.45, 0.2).normalized()
HORN_BASE = V(0, -0.196, 0.112)
HORN_DIR = V(0, -0.56, 0.83).normalized()              # its first segment's way: forward and up; each later one turned further up, a rhinoceros beetle's hook
HORN_BEND = math.radians(-11)          # (negative: each segment turns up; positive, it curled forward and down)
HORN_SEGS = ((0.072, 0.058), (0.064, 0.05), (0.056, 0.042), (0.046, 0.034))      # length, across the flats at its base: a segment a year, each narrower
HORN_TAPER = 0.06          # each segment narrows this much along itself: the step to the next a small ledge of growth (big, they read as stacked nuts)
HORN_TIP = 0.05
ANT_BASE = V(0.036, -0.238, 0.078)
ANT_ELBOW = V(0.07, -0.262, 0.084)
# the wing cases
ELY_Y0, ELY_Y1, ELY_ZB, ELY_TH, ELY_THICK, SUTURE = -0.058, 0.29, 0.1, math.radians(72), 0.0065, 0.0015      # (its front under the pronotum; its edges well above its thighs: lower, a lifted thigh cut through them)
# legs: hip (in the body), knee, ankle, then the foot's end; front, middle, hind
LEGS = {
    1: (V(0.05, -0.11, 0.075), V(0.135, -0.16, 0.105), V(0.172, -0.222, 0.026), V(0.19, -0.268, 0.006)),
    2: (V(0.06, -0.01, 0.07), V(0.162, -0.02, 0.1), V(0.205, 0.004, 0.026), V(0.236, 0.034, 0.006)),
    3: (V(0.06, 0.07, 0.07), V(0.158, 0.12, 0.1), V(0.198, 0.196, 0.026), V(0.226, 0.244, 0.006)),
}
FEMUR_R, TIBIA_R = 0.021, 0.017
ELY_NU, ELY_NV = 150, 80          # the high wing cases' grid: a vertex every 2 mm, for growth rings 2 mm wide (at 60 x 32 they came out as jagged ripples)


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def make_tags(bm, ints=()):
    for key in ints:
        bm.verts.layers.int.new(key)


def tag_new(bm, before, **values):
    for key, value in values.items():
        layer = bm.verts.layers.int[key]
        for v in bm.verts:
            if v not in before:
                v[layer] = value


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=int)
    a.data.foreach_get("value", out)
    return out


def fused_tagged(o, voxel, tags):
    """One closed surface out of overlapping balls and tubes (baked from as they were, rays meet their insides: the Gravity Imp's black patches);
    each tag carried over from the nearest original vertex."""
    from mathutils.kdtree import KDTree
    P0 = verts(o)
    vals = {t: read_tag(o, t) for t in tags}
    fused(o, voxel, 1)
    kd = KDTree(len(P0))
    for i, q in enumerate(P0):
        kd.insert(q, i)
    kd.balance()
    near = [kd.find(q)[1] for q in verts(o)]
    for t in tags:
        a = o.data.attributes.new(t, "INT", "POINT")
        a.data.foreach_set("value", [int(vals[t][i]) for i in near])
    return o


def fused(o, voxel, smooth_iter=2):
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": smooth_iter})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the body: pronotum, thorax, abdomen ----------
def build_body(name, coll, voxel=0.0018):
    m = Mesh()
    m.ball(PRONOTUM_C, PRONOTUM_R, 64, 40)
    m.ball(THORAX_C, THORAX_R, 48, 28)
    m.ball(ABDOMEN_C, ABDOMEN_R, 64, 40)
    for k in (1, 2, 3):
        m.ball(LEGS[k][0], (0.026, 0.026, 0.024), 24, 14)
        m.ball(mir(LEGS[k][0], -1), (0.026, 0.026, 0.024), 24, 14)          # the sockets the legs sit in
    o = m.finish(name, coll)
    return fused(o, voxel, 3)


def build_head(name, coll, voxel=0.0012):
    m = Mesh()
    m.ball(HEAD_C, HEAD_R, 48, 30)
    m.ball(CLYPEUS_C, CLYPEUS_R, 40, 24)
    for side in (1, -1):
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.2,) * 3, 24, 16)      # the eye's rim
    o = m.finish(name, coll)
    return fused(o, voxel, 2)


def build_eyes(name, coll, seg=(40, 28)):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        m.ball(mir(EYE_C, side), (EYE_R,) * 3, *seg)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


# ---------- the horn: a quartz crystal grown in segments, one a year ----------
def horn_frame(k=0):
    """Segment k's axis (each turned further up than the last: the horn curves up as a rhinoceros beetle's does) and its cross axes."""
    d = (Matrix.Rotation(HORN_BEND * k, 3, V(1, 0, 0)) @ HORN_DIR).normalized()
    a = V(1, 0, 0)                       # a flat face toward its sides
    b = d.cross(a).normalized()
    return d, a, b


def hex_prism(m, base, length, flats, k=0, rings=2):
    """A hexagonal prism along segment k's axis, flat faces to its sides, narrowing a little along it; across its flats `flats` at its base. Its ends capped."""
    d, a, b = horn_frame(k)
    r0 = flats / math.sqrt(3)             # corner radius
    loops = []
    for i in range(rings + 1):
        c = base + d * (length * i / rings)
        r = r0 * (1 - HORN_TAPER * i / rings)
        loops.append([m.bm.verts.new(c + (a * math.cos(math.radians(30 + 60 * j)) + b * math.sin(math.radians(30 + 60 * j))) * r) for j in range(6)])
    for i in range(rings):
        for k in range(6):
            k2 = (k + 1) % 6
            m.bm.faces.new((loops[i][k], loops[i][k2], loops[i + 1][k2], loops[i + 1][k]))
    m.bm.faces.new(list(reversed(loops[0])))
    m.bm.faces.new(loops[-1])


def horn_segments():
    """Each segment: where it starts, its length and across its flats, and which way it runs. Each starts a little inside the last: a narrower
    ledge where it grew."""
    out = []
    at = HORN_BASE - HORN_DIR * 0.026     # (its root deep in the head)
    for k, (length, flats) in enumerate(HORN_SEGS):
        d, _, _ = horn_frame(k)
        out.append((at, length, flats, k))
        at = at + d * (length - 0.009)
    return out, at


def build_horn(name, coll, hi=True):
    m = Mesh()
    segs, end = horn_segments()
    for at, length, flats, k in segs:
        hex_prism(m, at, length, flats, k=k, rings=6 if hi else 1)
    o = m.finish(name, coll, smooth_shade=False)
    apply_mods(o, [("BEVEL", {"width": 0.0016 if hi else 0.0016, "segments": 3 if hi else 1, "limit_method": "ANGLE"})])      # (bevelled in the game's mesh too: smooth-shaded, it still reads as cut facets)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def tip_point():
    segs, end = horn_segments()
    d, _, _ = horn_frame(len(HORN_SEGS))
    return end + d * (HORN_TIP + 0.009)


def build_tip(name, coll):
    """The newest crystal: a pyramid of six faces, glowing, its base a little inside the last segment."""
    segs, end = horn_segments()
    d, a, b = horn_frame(len(HORN_SEGS))
    flats = HORN_SEGS[-1][1] * (1 - HORN_TAPER) * 0.97
    r = flats / math.sqrt(3)
    base = end - d * 0.002
    m = Mesh()
    ring = [m.bm.verts.new(base + (a * math.cos(math.radians(30 + 60 * k)) + b * math.sin(math.radians(30 + 60 * k))) * r) for k in range(6)]
    apex = m.bm.verts.new(tip_point())
    m.bm.faces.new(list(reversed(ring)))
    for k in range(6):
        m.bm.faces.new((ring[k], ring[(k + 1) % 6], apex))
    return m.finish(name, coll, smooth_shade=False)


# ---------- the wing cases: two domes of crystal ----------
def ely_w(u):
    """Its half-width seen from above, along it (0 its front, 1 its tip): an oval, broadest a third along."""
    if u < 0.33:
        return 0.12 + 0.012 * math.sin(math.pi / 2 * u / 0.33)
    return 0.132 * math.sqrt(max(0.0, 1 - ((u - 0.33) / 0.67) ** 2.2))


def ely_h(u):
    """Its height above its widest line, along it: a dome curving down to a rounded tail (falling as u squared, it was a flat-topped loaf); its
    front a little lower, tucked in under the pronotum's back edge (level with it, it left a gap: a dark crescent, and a case that floated)."""
    tuck = 0.925 + 0.075 * float(smooth(0.04, 0.16, u))
    return 0.112 * math.sqrt(max(0.0, 1 - u ** 2.6)) * tuck


def ely_point(u, v, side, lift=0.0):
    """A point of a wing case's middle surface: u along it, v from its seam (0) round its side to its edge (1)."""
    th = ELY_TH * v
    y = ELY_Y0 + (ELY_Y1 - ELY_Y0) * u
    x = SUTURE + ely_w(u) * math.sin(th)
    z = ELY_ZB + (ely_h(u) + lift) * math.cos(th)
    return V(x * side, y, z)


def build_elytra(name, coll, nu=ELY_NU, nv=ELY_NV):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        m.sheet(lambda u, v, side=side: tuple(ely_point(0.985 * u, v, side)), lambda u, v: ELY_THICK * (0.55 + 0.45 * math.sqrt(max(0.0, 1 - u ** 8))), nu, nv)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


# ---------- the hind wings: membranes folded under the wing cases ----------
def abdomen_top(x, y):
    q = 1 - (x / ABDOMEN_R[0]) ** 2 - ((y - ABDOMEN_C.y) / ABDOMEN_R[1]) ** 2
    return ABDOMEN_C.z + ABDOMEN_R[2] * math.sqrt(max(0.0, q))


def ely_inner(x, y):
    u = (y - ELY_Y0) / (ELY_Y1 - ELY_Y0)
    w = max(ely_w(u), 1e-4)
    s = min(1.0, max(0.0, (abs(x) - SUTURE) / w))
    return ELY_ZB + ely_h(u) * math.cos(math.asin(s)) - ELY_THICK / 2


WING_ROOT, WING_LEN, WING_W = V(0.045, 0.02, 0.0), 0.21, 0.05


def wing_point(u, v, side):
    """Folded: lengthwise under its wing case, midway between the abdomen and the case's inside."""
    y = WING_ROOT.y + WING_LEN * u
    x = WING_ROOT.x - 0.02 + (0.012 + 0.028 * math.sin(math.pi * min(1.0, 0.15 + u))) * (2 * v - 1) * 0.5 + 0.02 + 0.012 * u
    z = 0.5 * (abdomen_top(x, y) + ely_inner(x, y))
    return V(x * side, y, z)


def build_wings(name, coll, nu=30, nv=8):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        m.sheet(lambda u, v, side=side: tuple(wing_point(u, v, side)), lambda u, v: 0.0013, nu, nv)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


# ---------- legs ----------
LEG_KEYS = [(side, k) for side in (1, -1) for k in (1, 2, 3)]


def leg_index(side, k):
    return LEG_KEYS.index((side, k))


def leg_pts(side, k):
    return [mir(p, side) for p in LEGS[k]]


def tarsus_pts(side, k):
    hip, knee, ankle, end = leg_pts(side, k)
    out = []
    for i in range(6):
        f = i / 5
        p = ankle.lerp(end, f)
        p.z = 0.024 * (1 - f) ** 1.6 + 0.006 * (1 - (1 - f) ** 1.6) if i else ankle.z
        out.append(p)
    return out


def build_legs(name, coll, hi=True):
    """Each leg: the femur (hip ball to knee), the tibia (knee ball to ankle, toothed along its outer edge), the tarsus (ankle ball, five beads, two
    hooked claws). Tags: which leg, which segment."""
    sides = 18 if hi else 7
    ball = (20, 12) if hi else (8, 5)
    m = Mesh()
    make_tags(m.bm, ints=("leg", "seg"))
    for side, k in LEG_KEYS:
        hip, knee, ankle, end = leg_pts(side, k)
        li = leg_index(side, k)
        before = set(m.bm.verts)
        m.tube([hip.lerp(knee, f) for f in (0, 0.3, 0.7, 1.0)], lambda f: FEMUR_R * (0.85 + 0.25 * math.sin(math.pi * f)), sides=sides, flat=0.72, plane=V(0, 0, 1))      # flattened: wider than tall
        tag_new(m.bm, before, leg=li, seg=0)
        before = set(m.bm.verts)
        m.ball(knee, (FEMUR_R * 0.95,) * 3, *ball)
        m.tube([knee.lerp(ankle, f) for f in (0, 0.5, 1.0)], lambda f: TIBIA_R * (1 - 0.25 * f), sides=sides, flat=0.75, plane=V(0, 0, 1))
        out = (ankle - knee).cross(V(0, 0, 1)).normalized() * (1 if (ankle - knee).cross(V(0, 0, 1)).dot(mir(V(1, 0, 0), side)) > 0 else -1)
        for f in ((0.45, 0.62, 0.8) if k == 1 else (0.55, 0.8)):
            root = knee.lerp(ankle, f)
            tipp = root + out * (0.022 if k == 1 else 0.014) + (ankle - knee).normalized() * 0.008
            m.tube([root.lerp(tipp, s) for s in (0, 0.5, 1)], lambda s: 0.0065 * (1 - s) ** 0.8 + 0.0008, sides=max(5, sides // 2))      # a tooth
        tag_new(m.bm, before, leg=li, seg=1)
        before = set(m.bm.verts)
        m.ball(ankle, (TIBIA_R * 0.95,) * 3, *ball)          # (clearly bigger than the tibia's end: the same size, they z-fought)
        pts = tarsus_pts(side, k)
        # the tarsus: one tube whose width swells and narrows into five beads, then tapers into a hooked claw (as beads, a tip ball and two claw
        # tubes all overlapping, their surfaces lay level here and there and z-fought; two claws are a tenth of a stud at a pet's size anyway)
        d = (pts[-1] - pts[-2]).normalized()
        hook = [pts[-1] + d * 0.006 + V(0, 0, 0.0005), pts[-1] + d * 0.011 - V(0, 0, 0.002)]
        path = catmull(pts + hook, 6 if hi else 3)

        def tarsus_r(f):
            beads = 0.0038 + 0.0018 * abs(math.sin(5 * math.pi * min(1.0, f / 0.8))) ** 0.7
            return beads * (1 - float(smooth(0.8, 1.0, f))) + 0.0007
        m.tube(path, tarsus_r, sides=max(6, sides // 2))
        tag_new(m.bm, before, leg=li, seg=2)
    return m.finish(name, coll)


# ---------- antennae: an elbowed stalk and a club of three amber lamellae ----------
def build_antennae(name, coll, hi=True):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        b, e = mir(ANT_BASE, side), mir(ANT_ELBOW, side)
        m.tube(catmull([b - (e - b).normalized() * 0.01, b, e], 4 if hi else 1), lambda f: 0.0042, sides=12 if hi else 6)
        m.ball(e, (0.0055,) * 3, *((14, 9) if hi else (6, 4)))
        fwd = mir(V(0.4, -0.85, -0.2), side).normalized()
        # the club: its lamellae closed into one oval knob, as at rest (as three plates, it read as a little hand); their lines are painted on
        m.tube([e + fwd * (0.028 * f) for f in (0, 0.25, 0.5, 0.75, 1.0)], lambda f: 0.0035 + 0.0045 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * f)) ** 0.7, sides=14 if hi else 6, flat=1.6, plane=V(0, 0, 1))
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


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


def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, (40.0, 120.0, 0.0018), (-40.0, -120.0, 0.0018)) for side, tag in ((1, "L"), (-1, "R"))}


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Body"] = build_body(N + "BodyHi", HI)
    pieces["Head"] = build_head(N + "HeadHi", HI)
    pieces["Eyes"] = build_eyes(N + "EyesHi", HI)
    pieces["Horn"] = build_horn(N + "HornHi", HI)
    pieces["Elytra"] = build_elytra(N + "ElytraHi", HI)
    pieces["Wings"] = build_wings(N + "WingsHi", HI)
    pieces["Legs"] = fused_tagged(build_legs(N + "LegsHi", HI), 0.0009, ("leg", "seg"))
    pieces["Antennae"] = fused_tagged(build_antennae(N + "AntennaeHi", HI), 0.0006, ("side",))
    frames = eye_frames()
    glows = {"Tip": build_tip(N + "Tip_Glow_" + TIP_HEX, HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-20, 25, 0.0035, 10), (25, -15, 0.0018, 6)))}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


# ---------- painting ----------
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


def chitin(P, Nn, dark=0.0):
    """Glossy indigo chitin with an oil-slick sheen: violet where it faces up and forward, teal where it turns to its sides, fine pitting."""
    n = len(P)
    col = np.broadcast_to(CHITIN, (n, 3)).copy()
    side = np.abs(Nn[:, 0])
    col = mix(col, SHEEN_V, smooth(0.3, 0.95, Nn[:, 2]) * 0.35 * (1 - dark))
    col = mix(col, SHEEN_T, smooth(0.45, 0.95, side) * 0.3 * (1 - dark))
    col = mix(col, CHITIN_DEEP, smooth(-0.1, -0.7, Nn[:, 2]) * 0.6 + dark * 0.5)
    col = mix(col, SHEEN_V * 0.8, smooth(0.6, 0.85, fbm(P, 30.0, 3, 5)) * 0.15)
    return col


def pits(P, f=420.0, seed=7):
    d1, d2, own = cells_3d(P, f, seed)
    return (1 - smooth(0.0, 0.22, d1)) * (own > 0.35)


def carve_body(o):
    P, Nn = verts(o), normals(o)
    top = Nn[:, 2] > -0.2
    d = -0.0005 * pits(P) * top
    # the abdomen's underside: ribbed plates, one behind another
    under = (Nn[:, 2] < -0.3) & (P[:, 1] > 0.0)
    rib = 0.5 + 0.5 * np.cos((P[:, 1] - 0.02) * 2 * np.pi / 0.045)
    d += 0.0012 * smooth(0.8, 0.98, rib) * under
    set_verts(o, P + Nn * d[:, None])


def paint_body(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    col = chitin(P, Nn)
    # the pronotum's rim, a fine bead round its edge
    pr = np.linalg.norm((P - np.array(tuple(PRONOTUM_C))) / np.array(PRONOTUM_R), axis=1)
    lat = (P[:, 2] - PRONOTUM_C.z) / PRONOTUM_R[2]
    rim = (np.abs(lat + 0.05) < 0.06) * (pr > 0.97) * (P[:, 1] < 0.0)
    col = mix(col, CHITIN_DEEP, rim * 0.7)
    col = mix(col, CHITIN_DEEP * 0.8, pits(P) * 0.5 * (Nn[:, 2] > -0.2))
    # under it: ribbed plates fringed with amber hairs; a little amber fuzz on its chest
    under = smooth(-0.2, -0.6, Nn[:, 2])
    rib = 0.5 + 0.5 * np.cos((P[:, 1] - 0.02) * 2 * np.pi / 0.045)
    hairs = (0.5 + 0.5 * np.sin(P[:, 0] * 900)) * smooth(0.55, 0.8, rib)
    col = mix(col, AMBER_DEEP, under * hairs * 0.55 * (P[:, 1] > 0.0))
    chest = under * (P[:, 1] < 0.0) * (0.5 + 0.5 * np.sin(P[:, 0] * 1400 + np.sin(P[:, 1] * 300) * 2))
    col = mix(col, AMBER_DEEP * 1.1, chest * 0.22)                       # fine amber down on its chest (as noise, it read as blotches)
    rough = 0.28 + 0.25 * under + 0.15 * pits(P)
    metal = 0.35 * (1 - under)
    paint(o, np.clip(col, 0, 1), rough, metal)


def paint_head(o):
    P, Nn = verts(o), normals(o)
    col = chitin(P, Nn)
    cly = np.linalg.norm((P - np.array(tuple(CLYPEUS_C))) / np.array(CLYPEUS_R), axis=1)
    edge = (cly < 1.25) * (P[:, 1] < CLYPEUS_C.y - 0.01) * smooth(-0.2, -0.6, Nn[:, 1])
    col = mix(col, AMBER, edge * smooth(0.0, 0.004, -(P[:, 2] - CLYPEUS_C.z + 0.004)) * 0.6)       # a fringe of amber bristles under its face plate
    for side in (1, -1):
        e = np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1) / EYE_R
        col = mix(col, CHITIN_DEEP * 0.7, (1 - smooth(1.15, 1.5, e)) * 0.7)
    paint(o, np.clip(col, 0, 1), 0.3 + 0.1 * pits(P), np.full(len(P), 0.35))


def paint_eyes(o):
    """Compound eyes: black-blue, glossy, a fine honeycomb of facets, a teal shine across the top."""
    P, Nn = verts(o), normals(o)
    d1, d2, _ = cells_3d(P, 1100.0, 21)
    facet = smooth(0.0, 0.08, d2 - d1)
    col = mix(np.broadcast_to(rgb(10, 12, 26), (len(P), 3)), rgb(28, 40, 70), facet * 0.6)
    col = mix(col, rgb(70, 170, 190), smooth(0.4, 0.9, Nn[:, 2]) * 0.35)
    paint(o, np.clip(col, 0, 1), np.full(len(P), 0.08), np.zeros(len(P)))


def horn_local(P):
    """Per point of the horn: which segment (by which axis it lies nearest along), how far along that segment (0..1)."""
    segs, end = horn_segments()
    best = np.full(len(P), 9.0)
    seg = np.zeros(len(P), dtype=int)
    along = np.zeros(len(P))
    for at, length, flats, k in segs:
        d, _, _ = horn_frame(k)
        rel = P - np.array(tuple(at))
        t = rel @ np.array(tuple(d))
        radial = np.linalg.norm(rel - np.outer(t, np.array(tuple(d))), axis=1)
        inside = (t > -0.002) & (t < length + 0.002)
        score = np.where(inside, radial, 9.0)
        take = score < best
        best[take] = score[take]
        seg[take] = k
        along[take] = np.clip(t[take] / length, 0, 1)
    return seg, along


def paint_horn(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    seg, along = horn_local(P)
    # facet edges: where the bevel turns, its normal off every flat face's
    edge = np.zeros(n)
    for k in range(len(HORN_SEGS) + 1):
        d, a, b = horn_frame(min(k, len(HORN_SEGS) - 1))
        fn = [a * math.cos(math.radians(60 * j)) + b * math.sin(math.radians(60 * j)) for j in range(6)] + [d, -d]
        best = np.max(np.stack([Nn @ np.array(tuple(f)) for f in fn], 1), axis=1)
        edge = np.maximum(edge, 1 - smooth(0.9, 0.995, best))
    col = mix(np.broadcast_to(CRYSTAL_DEEP, (n, 3)), CRYSTAL, smooth(0.0, 0.6, along))           # deeper at each segment's root, clearer as it grows
    col = mix(col, CRYSTAL * 0.85, (seg % 2) * 0.25)                                             # each year's a slightly different tint
    phantom = np.zeros(n)
    for f in (0.3, 0.55, 0.8):
        phantom = np.maximum(phantom, 1 - smooth(0.012, 0.035, np.abs(along - f)))
    col = mix(col, CRYSTAL_PALE, phantom * 0.35)                                                 # phantom layers inside, where it paused growing
    col = mix(col, CRYSTAL_PALE, edge * 0.7)                                                     # frosted edges
    col = mix(col, CRYSTAL_PALE, smooth(0.7, 0.9, fbm(P, 160.0, 2, 3)) * 0.2)
    paint(o, np.clip(col, 0, 1), 0.07 + 0.25 * edge, np.zeros(n))


def sheet_uv(nu, nv, sides=2):
    """The u, v (0..1) and which face (0 top, 1 bottom) of each vertex of m.sheet's grid, in its order, for `sides` sheets one after another."""
    count = (nu + 1) * (nv + 1) * 2
    uu = np.zeros(count)
    vv = np.zeros(count)
    face = np.zeros(count, dtype=int)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for f in range(2):
                uu[idx], vv[idx], face[idx] = i / nu, j / nv, f
                idx += 1
    return np.tile(uu, sides), np.tile(vv, sides), np.tile(face, sides)


def paint_elytra(o, nu=ELY_NU, nv=ELY_NV):
    """Clear cyan crystal domes: deep teal at the rim where the crystal is thickest, a band of light caught inside it, phantom growth layers within,
    one a year, following its outline (measured in metres along its surface, so they follow the oval and close in at its tail), a darker core where the
    body shows through, frosted where the two meet."""
    P, Nn = verts(o), normals(o)
    n = len(P)
    uu, vv, face = sheet_uv(nu, nv)
    uu *= 0.985
    w = np.array([ely_w(float(u)) for u in uu])
    th = vv * ELY_TH
    span = ELY_Y1 - ELY_Y0
    ds = np.stack([w * th, w * (ELY_TH - th) * 0.9, uu * span * 1.4, (1 - uu) * span * 0.9], 1)       # metres to its seam, its side edge, its front, its tail
    k = 140.0
    inset = np.maximum(-np.log(np.exp(-ds * k).sum(1)) / k + np.log(4) / k, 0)
    col = mix(np.broadcast_to(CRYSTAL_DEEP, (n, 3)), CRYSTAL, smooth(0.0, 0.03, inset))
    light = np.exp(-((vv - 0.3) / 0.12) ** 2) * smooth(0.05, 0.25, uu) * (1 - smooth(0.7, 0.95, uu))
    col = mix(col, CRYSTAL_PALE, light * 0.45)                                                    # light caught inside it
    rings = np.zeros(n)
    shadow = np.zeros(n)
    for j, f in enumerate((0.01, 0.02, 0.03, 0.04)):
        rings = np.maximum(rings, 1 - smooth(0.0008, 0.0024, np.abs(inset - f)))
        shadow = np.maximum(shadow, (1 - smooth(0.0, 0.004, inset - f - 0.0016)) * (inset > f + 0.0012))
    col = mix(col, CRYSTAL_DEEP, shadow * 0.25)                                                   # each layer's depth, just inside it
    col = mix(col, CRYSTAL_PALE, rings * 0.6)                                                     # the phantom layers: one a year
    col = mix(col, CRYSTAL_DEEP * 0.85, smooth(0.048, 0.062, inset) * 0.45)                       # the body, seen through it
    col = mix(col, CRYSTAL_PALE, smooth(0.55, 0.95, Nn[:, 2]) * 0.18)
    col = mix(col, CRYSTAL_DEEP * 0.75, smooth(0.15, -0.45, Nn[:, 2]) * 0.45)                     # deeper where it turns away from the light
    col = mix(col, CRYSTAL_PALE, (1 - smooth(0.0, 0.03, vv)) * 0.6)                               # frosted along the seam
    col = mix(col, rgb(240, 255, 255), smooth(0.86, 0.94, fbm(P, 260.0, 2, 13)) * 0.5)            # glints in the crystal
    col = np.where(face[:, None] == 1, mix(col, CRYSTAL_DEEP, 0.45), col)                          # its inside, deeper
    paint(o, np.clip(col, 0, 1), np.full(n, 0.05) + 0.08 * rings, np.zeros(n))


def paint_wings(o, nu=30, nv=8):
    P = verts(o)
    n = len(P)
    uu, vv, face = sheet_uv(nu, nv)
    veins = np.maximum((1 - smooth(0.0, 0.05, np.abs(np.sin(vv * np.pi * 2 + uu * 1.2)))) * smooth(0.1, 0.3, uu), 1 - smooth(0.0, 0.06, np.abs(vv - 0.85)))
    col = mix(np.broadcast_to(MEMBRANE, (n, 3)), rgb(150, 160, 196), smooth(0.4, 1.0, uu) * 0.4)
    col = mix(col, VEIN, veins * 0.7)
    col = mix(col, rgb(196, 170, 120), (1 - smooth(0.0, 0.15, uu)) * 0.5)                       # amber at its root
    paint(o, np.clip(col, 0, 1), np.full(n, 0.35), np.zeros(n))


def paint_legs(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    seg = read_tag(o, "seg")
    col = chitin(P, Nn, dark=0.2)
    under = smooth(0.1, -0.6, Nn[:, 2])
    hairs = (0.5 + 0.5 * np.sin((P[:, 0] + P[:, 1]) * 1100)) * under
    col = mix(col, AMBER_DEEP, hairs * 0.45 * (seg < 2))                                        # amber hairs along their undersides
    col = np.where((seg == 2)[:, None], mix(col, AMBER_DEEP, 0.55), col)                         # the feet, amber-brown
    # the teeth's tips amber (each leg's own: tested against every leg, the others' tibiae all came out amber)
    legs = read_tag(o, "leg")
    for side, k in LEG_KEYS:
        hip, knee, ankle, end = leg_pts(side, k)
        f, d = nearest_on([knee, ankle], P)
        tooth = (seg == 1) * (legs == leg_index(side, k)) * smooth(TIBIA_R * 1.1, TIBIA_R * 1.9, d)
        col = mix(col, AMBER, tooth * 0.8)
    paint(o, np.clip(col, 0, 1), 0.3 + 0.2 * under, 0.3 * (seg < 2))


def paint_antennae(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    col = chitin(P, Nn, dark=0.2)
    for side in (1, -1):
        e = np.array(tuple(mir(ANT_ELBOW, side)))
        club = np.linalg.norm(P - e, axis=1) > 0.006
        fwd = np.array(tuple(mir(V(0.4, -0.85, -0.2), side).normalized()))
        t = (P - e) @ fwd
        lam = 0.5 + 0.5 * np.sin(P[:, 2] * 2600)                                                 # the lines between its closed lamellae
        sel = club & (t > 0.002) & (np.sign(P[:, 0]) == side)
        col[sel] = mix(np.broadcast_to(AMBER, (sel.sum(), 3)), AMBER_DEEP, smooth(0.6, 0.95, lam[sel]) * 0.6)
    paint(o, np.clip(col, 0, 1), np.full(n, 0.35), np.zeros(n))


def paint_all(pieces, frames, data):
    carve_body(pieces["Body"])
    paint_body(pieces["Body"])
    paint_head(pieces["Head"])
    paint_eyes(pieces["Eyes"])
    paint_horn(pieces["Horn"])
    paint_elytra(pieces["Elytra"])
    paint_wings(pieces["Wings"])
    paint_legs(pieces["Legs"])
    paint_antennae(pieces["Antennae"])


VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.25), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.03, 0.14)
FACE_AT = (0, -0.22, 0.13)
EXTRA = [(0.2, -1, 0.25, 0.55, FACE_AT), (0.9, -0.5, 0.2, 0.5, FACE_AT), (0.7, 0.2, 0.6, 0.6, (0, 0.12, 0.18)), (1, -0.2, -0.05, 0.55, (0.15, -0.05, 0.06))]

# ---------- the game mesh ----------
BODY_QUADS = 1600
SCALES = {"Body": 1.0, "Head": 1.5, "Eyes": 1.6, "Horn": 1.4, "Elytra": 1.5, "Wings": 0.5, "Legs": 0.8, "Antennae": 0.9}
PIECES = ("Body", "Head", "Eyes", "Horn", "Elytra", "Wings", "Legs", "Antennae")


def build_low(pieces):
    lows = {"Body": retopo_skin(pieces["Body"], N + "BodyLow", BODY_QUADS), "Head": decimated(pieces["Head"], N + "HeadLow", 700)}
    P = verts(lows["Head"])
    for side in (1, -1):
        # the rim's skin lying level with an eyeball (within a millimetre): into the ball, where the eye hides it (level, they z-fought)
        c = np.array(tuple(mir(EYE_C, side)))
        d = np.linalg.norm(P - c, axis=1)
        band = np.abs(d - EYE_R) < 0.0018
        P[band] = c + (P[band] - c) / d[band, None] * (EYE_R - 0.002)
    set_verts(lows["Head"], P)
    lows["Eyes"] = build_eyes(N + "EyesLow", GAME, seg=(12, 8))
    lows["Horn"] = build_horn(N + "HornLow", GAME, hi=False)
    lows["Elytra"] = build_elytra(N + "ElytraLow", GAME, nu=18, nv=10)
    lows["Wings"] = build_wings(N + "WingsLow", GAME, nu=8, nv=2)
    lows["Legs"] = build_legs(N + "LegsLow", GAME, hi=False)
    lows["Antennae"] = build_antennae(N + "AntennaeLow", GAME, hi=False)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


def beetle_unwrap(lows, margin=0.006):
    """Each piece unwrapped on its own (the projection's charts as seams, then angle-based: it can't fold a chart over itself), collapsed fragments
    projected again, each scaled to its share, all packed together (the Gravity Imp's way)."""
    for key, o in lows.items():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        select_only([o])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(40), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.seams_from_islands()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.002)
        bpy.ops.object.mode_set(mode="OBJECT")
        uvd = o.data.uv_layers.active.data
        flat = set()
        for p in o.data.polygons:
            a, b2, c = [uvd[l].uv for l in list(p.loop_indices)[:3]]
            if abs((b2.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b2.y - a.y)) < 1e-10:
                flat.add(p.index)
        if flat:
            print("UV REDO", key, len(flat), "collapsed faces", flush=True)
            o.data.polygons.foreach_set("select", [p.index in flat for p in o.data.polygons])
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_linked(delimit={"SEAM"})
            bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
            bpy.ops.object.mode_set(mode="OBJECT")
        scale_uv_to(o, list(o.data.polygons), SCALES.get(key, 1.0))
    objs = list(lows.values())
    select_only(objs)
    for o in objs:
        o.data.polygons.foreach_set("select", [True] * len(o.data.polygons))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


# ---------- the skeleton ----------
BODY_AT = V(0, -0.02, 0.11)
HEAD_AT = V(0, -0.165, 0.105)
ELY_AT = V(0.002, -0.058, 0.196)         # its hinge at its front edge, at the seam: all of it behind and outside it, so it lifts clear when it opens
WING_AT = V(0.045, 0.022, 0.165)
SIDES = (("L", 1), ("R", -1))


def leg_name(side, k):
    tag = "L" if side == 1 else "R"
    return "Leg%s%d" % (tag, k), "Shin%s%d" % (tag, k), "Foot%s%d" % (tag, k)


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", BODY_AT.copy(), "Root"), ("Head", HEAD_AT.copy(), "Body")]
    for tag, side in SIDES:
        bones += [("Ant" + tag, mir(ANT_BASE, side), "Head"), ("Ely" + tag, mir(ELY_AT, side), "Body"), ("Wing" + tag, mir(WING_AT, side), "Body")]
    for side, k in LEG_KEYS:
        a, b, c = leg_name(side, k)
        hip, knee, ankle, end = leg_pts(side, k)
        bones += [(a, hip, "Body"), (b, knee, a), (c, ankle, b)]
    return armature(bones)


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def bind_all(lows, rig, glows):
    rigid(lows["Body"], "Body")
    rigid(lows["Head"], "Head")
    rigid(lows["Eyes"], "Head")
    rigid(lows["Horn"], "Head")
    weigh(lows["Elytra"], [{"ElyL" if k == 1 else "ElyR": 1.0} for k in read_tag(lows["Elytra"], "side")])
    weigh(lows["Wings"], [{"WingL" if k == 1 else "WingR": 1.0} for k in read_tag(lows["Wings"], "side")])
    weigh(lows["Antennae"], [{"AntL" if k == 1 else "AntR": 1.0} for k in read_tag(lows["Antennae"], "side")])
    legs, segs = read_tag(lows["Legs"], "leg"), read_tag(lows["Legs"], "seg")
    weigh(lows["Legs"], [{leg_name(*LEG_KEYS[l])[g]: 1.0} for l, g in zip(legs, segs)])
    rigid(glows["Tip"], "Head")
    weigh(glows["Glints"], [{"Head": 1.0} for _ in verts(glows["Glints"])])
    tag_pieces(lows)
    objs = list(lows.values())
    body = lows["Body"]
    select_only(objs, body)
    bpy.ops.object.join()                    # (pet_kit's join_into looks for a piece named Skin)
    body.name = body.data.name = N + "Body"
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses, in the game's axes: the same numbers PetRig's animateCrystalBeetle uses ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))


def game_matrix(v):
    return Matrix.Rotation(v[0], 3, Vector(RX)) @ Matrix.Rotation(v[1], 3, Vector(RY)) @ Matrix.Rotation(v[2], 3, Vector(RZ))


def to_game(m3):
    e = (CM @ m3 @ CM).to_euler("ZYX")
    return (round(e.x, 4), round(e.y, 4), round(e.z, 4))


def spec(table):
    """A table of game turns (x, y, z[, move]) as pose specs; an entry may also be a 3x3 matrix in the game's axes (a turn built in another order)."""
    out = {}
    for bone, v in table.items():
        if isinstance(v, Matrix):
            q = v.to_quaternion()
            mv = (0, 0, 0)
        else:
            q = game_matrix(v).to_quaternion()
            mv = v[3] if len(v) > 3 else (0, 0, 0)
        axis, angle = q.to_axis_angle()
        out[bone] = (tuple(axis), math.degrees(angle), (-mv[0], mv[2], mv[1]))
    return out


def mirror_table(table):
    """Its left's turns onto its right: a mirror keeps a turn about X and flips those about Y and Z; a move flips along X."""
    out = dict(table)
    for bone, v in table.items():
        if "L" in bone[3:] or bone.endswith("L"):
            other = bone.replace("L", "R", 1) if not bone.startswith("L") else "L" + bone[1:].replace("L", "R", 1)
            if isinstance(v, Matrix):
                flip = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))
                out[other] = flip @ v @ flip
            else:
                mv = v[3] if len(v) > 3 else (0, 0, 0)
                out[other] = (v[0], -v[1], -v[2], (-mv[0], mv[1], mv[2]))
    return out


WALK = {"swing": 0.3, "lift": 0.22, "knee": 0.3}
GROUP_A = ((1, 1), (-1, 2), (1, 3))          # its tripods: front left, middle right, hind left; then the others


def walk(phi):
    """A tripod gait: three legs down while three swing forward, lifted. Each leg swings about the upright through its hip (a planted foot keeps
    exactly its height) and lifts at the hip and the knee."""
    t = {}
    for side, k in LEG_KEYS:
        lead = 0.0 if (side, k) in GROUP_A else math.pi
        sw = math.sin(phi + lead)
        lf = max(0.0, math.cos(phi + lead))
        a, b, c = leg_name(side, k)
        t[a] = (0, -WALK["swing"] * sw * side, -WALK["lift"] * lf * side)
        t[b] = (0, 0, WALK["knee"] * lf * side)
    return t      # (no roll of its body: rolled, its planted feet sank)


def fly_table(beat=0.0):
    """On the wing: tilted nose up, its wing cases up and out, its wings swung out from under them and beating (beat -1..1), its legs drawn in."""
    t = {"Body": (0.42, 0, 0, (0, 0.05, 0))}
    t["ElyL"] = (-0.4, 0, -1.1)                      # rolled up and out about its length, its tail lifted a little
    spread = Matrix.Rotation(-1.35, 3, Vector(RY))
    flap = Matrix.Rotation(-0.6 * max(beat, 0.0) + 0.25 * max(-beat, 0.0), 3, Vector(RZ))
    t["WingL"] = flap @ spread                       # spread out first, then beating about its body's long axis, mostly above level
    for k in (1, 2, 3):
        a, b, c = leg_name(1, k)
        t[a] = (0, 0.15 * (k - 2), 0.22)            # its legs hang (drawn up, they sat in its wings' down-beat)
        t[b] = (0, 0, -0.2)
    return mirror_table(t)


def rear_table():
    """Its special, wound up: reared on its hind legs, front legs up, its head back, the horn high."""
    t = {"Body": (0.38, 0, 0, (0, 0.094, 0.01)), "Head": (0.2, 0, 0)}          # (lifted by what turning about its middle drops its tail)
    a, b, c = leg_name(1, 1)
    t[a] = (0, 0, -0.55)
    t[b] = (0, 0, 0.45)
    return mirror_table(t)


def strike_table():
    """Its special, struck: it slams its front down, its head swung down, the horn level before it; front legs braced out. (Its horn curves up
    from the top of its head: pitched down far enough to bury the tip, its face went into the ground first.)"""
    t = {"Body": (-0.12, 0, 0, (0, 0.022, 0)), "Head": (-0.5, 0, 0)}
    a, b, c = leg_name(1, 1)
    t[a] = (0, -0.25, -0.12)
    return mirror_table(t)


def staged(bone, w, into_fly):
    """Onto the wing, staged as the game does it: its wing cases open first (done by 0.6), its wings swing out after (from 0.4): together, a wing
    crossed a half-open case."""
    if not into_fly:
        return w
    if bone.startswith("Ely"):
        return min(1.0, w / 0.6)
    if bone.startswith("Wing"):
        return float(smooth(0.4, 1.0, w))
    return w


def slerp_tables(a, b, w, into_fly=False):
    out = {}
    for bone in set(a) | set(b):
        wb = staged(bone, w, into_fly)
        qa = (a[bone] if isinstance(a.get(bone), Matrix) else game_matrix(a.get(bone, (0, 0, 0)))).to_quaternion()
        qb = (b[bone] if isinstance(b.get(bone), Matrix) else game_matrix(b.get(bone, (0, 0, 0)))).to_quaternion()
        q = qa.slerp(qb, wb)
        va, vb = a.get(bone, (0, 0, 0)), b.get(bone, (0, 0, 0))
        ma = Vector(va[3] if not isinstance(va, Matrix) and len(va) > 3 else (0, 0, 0))
        mb = Vector(vb[3] if not isinstance(vb, Matrix) and len(vb) > 3 else (0, 0, 0))
        mv = ma.lerp(mb, wb)
        axis, angle = q.to_axis_angle()
        out[bone] = (tuple(axis), math.degrees(angle), (-mv.x, mv.z, mv.y))
    return out


TRANSITIONS = (("Rest", "Fly"), ("Walk1", "Fly"), ("Walk3", "Fly"), ("Rest", "Rear"), ("Rear", "Strike"), ("Strike", "Rest"), ("Walk2", "Rear"), ("FlyUp", "FlyDown"))


def check_transitions(rig, body, vpiece, fpiece, dom):
    tables = pose_tables()
    for a, b in TRANSITIONS:
        worst = {}
        for k in range(11):
            pose(rig, slerp_tables(tables[a], tables[b], k / 10, into_fly=(b == "Fly")))
            r = check_pose(body, vpiece, fpiece, dom)
            for key, v in r.items():
                if v is None or key.startswith("foot ") or key == "horn lowest":
                    continue
                if key in ("feet z", "lowest else"):
                    worst[key] = min(worst.get(key, 9.0), v)
                else:
                    worst[key] = max(worst.get(key, 0), v - (23 if key == "horn x body" else 92 if key == "head x body" else 0))      # (less what it has at rest)
        print("TRANSITION", a, "->", b, {k: v for k, v in worst.items() if v != 0}, flush=True)


def look_table(yaw, pitch):
    return {"Head": (pitch, yaw, 0)}


def pose_tables():
    t = {"Rest": {}}
    for k in range(4):
        t["Walk%d" % k] = walk(k * math.pi / 4)
    t["Fly"] = fly_table(0.0)
    t["FlyUp"] = fly_table(1.0)
    t["FlyDown"] = fly_table(-1.0)
    t["Rear"] = rear_table()
    t["Strike"] = strike_table()
    t["LookL"] = look_table(0.38, 0.18)
    t["LookR"] = look_table(-0.38, -0.2)
    t["Shrug"] = mirror_table({"ElyL": (-0.18, 0, -0.08)})
    t["Antennae"] = mirror_table({"AntL": (0.35, -0.4, 0)})
    return t


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
    names = {g.index: g.name for g in body.vertex_groups}
    out = []
    for v in body.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        out.append(names[best.group] if best else "")
    return out


def tree_from(co, tris, faces):
    if not faces:
        return None
    return BVHTree.FromPolygons([tuple(co[i]) for i in range(len(co))], [tris[f] for f in faces])


def pairs(co, tris, fa, fb):
    ta, tb = tree_from(co, tris, fa), tree_from(co, tris, fb)
    if ta is None or tb is None:
        return 0
    return len(ta.overlap(tb))


def check_pose(body, vpiece, fpiece, dom):
    """What a pose can get wrong between rigid pieces: the horn into its body or legs, wings into anything, a wing case into a leg, one leg into
    another, a foot under the ground or off it, the body on the ground."""
    co, tris = posed(body)
    def faces(piece, test=None):
        return [i for i, p in enumerate(fpiece) if p == PIECES.index(piece) and (test is None or all(test(dom[v]) for v in tris[i]))]
    legs = {}
    for side, k in LEG_KEYS:
        names = leg_name(side, k)
        legs[(side, k)] = faces("Legs", lambda d, names=names: d in names)
    out = {}
    out["horn x body"] = pairs(co, tris, faces("Horn"), faces("Body"))
    out["horn x legs"] = pairs(co, tris, faces("Horn"), faces("Legs"))
    out["head x legs"] = pairs(co, tris, faces("Head"), faces("Legs"))
    out["wings x body"] = pairs(co, tris, faces("Wings"), faces("Body"))
    out["wings x elytra"] = pairs(co, tris, faces("Wings"), faces("Elytra"))
    out["wings x legs"] = pairs(co, tris, faces("Wings"), faces("Legs"))
    out["elytra x legs"] = pairs(co, tris, faces("Elytra"), faces("Legs"))
    out["elytra x head"] = pairs(co, tris, faces("Elytra"), faces("Head"))
    out["elytra x body"] = pairs(co, tris, faces("Elytra"), faces("Body"))
    out["head x body"] = pairs(co, tris, faces("Head") + faces("Eyes"), faces("Body"))
    out["antennae x"] = pairs(co, tris, faces("Antennae"), faces("Legs") + faces("Horn") + faces("Body"))
    cross = 0
    keys = list(legs)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            cross += pairs(co, tris, legs[keys[i]], legs[keys[j]])
    out["leg x leg"] = cross
    feet = np.array([d.startswith("Foot") for d in dom])
    out["feet z"] = round(float(co[feet, 2].min()), 4)
    for side, k in LEG_KEYS:
        sel = np.array([d == leg_name(side, k)[2] for d in dom])
        out["foot %s%d" % ("L" if side == 1 else "R", k)] = round(float(co[sel, 2].min()), 4)
    rest = ~feet & ~np.array([d.startswith("Shin") for d in dom])
    out["lowest else"] = round(float(co[rest, 2].min()), 4)
    tip = [i for i, d in enumerate(dom) if d == "Head" and vpiece[i] == PIECES.index("Horn")]
    out["horn lowest"] = round(float(co[tip, 2].min()), 4) if tip else None
    return out


def lowest_of(body, bones):
    co, _ = posed(body)
    dom = dominant(body)
    sel = np.array([d in bones for d in dom])
    return round(float(co[sel, 2].min()), 4)


VIEWS_GAME = [(0.62, -0.72, 0.3, 1.5, VIEW_AT), (1, -0.05, 0.1, 1.5, VIEW_AT), (0, -1, 0.15, 1.5, VIEW_AT)]


def game_glows(frames):
    return {"Tip": build_tip(N + "Tip_Glow_" + TIP_HEX, GAME),
            "Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-20, 25, 0.0035, 8), (25, -15, 0.0018, 5)))}


if __name__ == "__main__" and STAGE == "tables":
    for name, table in pose_tables().items():
        if name == "Rest":
            continue
        print("TABLE", name, {k: (to_game(v) if isinstance(v, Matrix) else tuple(round(float(x), 4) for x in v[:3]) + ((tuple(round(float(m), 4) for m in v[3]),) if len(v) > 3 else ())) for k, v in table.items()}, flush=True)
    for tag, fr in eye_frames().items():
        print("EYE", tag, fr.centre, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces)
    if STAGE == "all":
        beetle_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.15, 0.13, 0.3, 1), far=("Body",), reach=(0.003, 0.008),
                 far_reach=(0.006, 0.016), reaches={"Elytra": (0.002, 0.005), "Wings": (0.0008, 0.002), "Antennae": (0.002, 0.005), "Eyes": (0.002, 0.005), "Horn": (0.002, 0.006), "Legs": (0.0015, 0.004)})      # (legs: thin claws; a longer reach crossed them)
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
        bpy.data.objects.remove(glows[key], do_unlink=True)
    glows = game_glows(frames)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    vpiece, fpiece = piece_of_verts(body)
    dom = dominant(body)
    tables = pose_tables()
    for name, table in tables.items():
        pose(rig, spec(table))
        print("POSE", name, check_pose(body, vpiece, fpiece, dom), flush=True)
        shots(os.path.join(REVIEW, "pose" + name), VIEWS_GAME, target=VIEW_AT, size=480)
        if name in ("Rear", "Strike", "LookL", "Fly"):
            shots(os.path.join(REVIEW, "close" + name), [(1, -0.4, 0.5, 0.55, (0, -0.15, 0.17)), (0.3, -1, 0.6, 0.55, (0, -0.15, 0.17))], size=480)
    if "transitions" in ARGS:
        check_transitions(rig, body, vpiece, fpiece, dom)
    pose(rig, {})
    if STAGE == "all":
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 1.5, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.5
    else:
        mat = hi_material(ao_distance=0.04, ao_share=0.4)
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        attr = mat.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "metal"
        mat.node_tree.links.new(attr.outputs["Fac"], b.inputs["Metallic"])
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=1.7, size=640)
    print("DONE", flush=True)

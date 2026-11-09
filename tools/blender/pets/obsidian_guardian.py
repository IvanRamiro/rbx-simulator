"""The Obsidian Guardian (Rare, Darkness and crystal; Inferno Egg, also in the Magma Heart and Phoenix Ash Eggs): "A sentinel of black glass that
reflects you a little more honestly than you would like."

A black-glass gargoyle (the owner's choice, 2026-11-09), in a design language of its own: knapped stone. It perches as gargoyles do, crouched on its
haunches with its long arms down before it and its hands on the ledge, its head thrust out low between high shoulders, its tail curled round its feet.
All of it is volcanic glass worked like a stone blade: cut into flat facets with shallow flake scars and ripple rings in them, glassy black with thin
streaks of violet flow-banding. Only its face is polished: a dark violet mirror over its muzzle and between its eyes, cut in a few broad planes; its eyes
are two slits of violet light set deep under a heavy brow, under two brow shards that move; two tusks rise from its lower jaw; thick faceted horns sweep
back. Its wings are a bony arm and broad, jagged shards of glass with gaps between them, never feathers or membrane: folded, each wrist is a peak above
its shoulder and the shards hang round it like a cloak, their thin edges smoky violet. Its tail ends in a knapped spearhead.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/obsidian_guardian.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Built in its perch: the bind pose. The maps go to assets/pets/InfernoEgg/.

What touches what: trunk, neck, head, arms (running on into the palms), legs (into the foot pads) and the tail are one skin; each hand and foot is its
own piece, the limb ending inside its palm or pad, its talons on the ground; the eye slits lie half sunk in the face under the brow; the brow shards root in
the temples and lie along the brow; the horns and tusks root inside the head and jaw; each wing's arm roots inside the upper back, its shards inside the
wrist's hub or along its forearm; the elbow spurs root in the elbows; the tail's spearhead roots inside its tip.
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
PET = "ObsidianGuardian"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "InfernoEgg")

# ---------- colours: black glass ----------
OBS, OBS_DEEP, OBS_RIDGE = rgb(18, 15, 23), rgb(7, 6, 10), rgb(70, 64, 82)
SHEEN, SMOKE = rgb(70, 40, 112), rgb(96, 58, 128)          # violet flow-banding; the thin edges where light gets through
MIRROR = rgb(66, 60, 84)                                    # the face's mirror: polished black glass, a dark violet mirror (metal)
EYE_HEX = "9a50ff"

# ---------- the frame of it (its left; mirrored) ----------
# hunched far forward like a vulture on a ledge: the chest between its knees, the head thrust out low between high shoulders
HEAD0, HEAD_K, HEAD_SHIFT = V(0, -0.168, 0.602), 1.22, V(0, -0.077, -0.037)     # every head feature below is written where it was first drawn, and grown and moved by these (hv)


def hv(p):
    return HEAD0 + (p - HEAD0) * HEAD_K + HEAD_SHIFT


def head_local(P):
    """Points of the head back where the head's features were first drawn (the inverse of hv), for tests written there."""
    return (P - np.array(tuple(HEAD0 + HEAD_SHIFT))) / HEAD_K + np.array(tuple(HEAD0))


PELVIS = V(0, 0.1, 0.25)
CHEST = V(0, -0.075, 0.425)
SPINE = [V(0, 0.12, 0.24), V(0, 0.055, 0.33), V(0, -0.03, 0.405), V(0, -0.1, 0.455), V(0, -0.145, 0.48)]
NECK = [V(0, -0.1, 0.5), V(0, -0.165, 0.53), V(0, -0.215, 0.548)]
CRANIUM, CRANIUM_R = hv(V(0, -0.165, 0.6)), tuple(r * HEAD_K for r in (0.066, 0.076, 0.05))
MUZZLE = [hv(V(0, -0.2, 0.59)), hv(V(0, -0.245, 0.578)), hv(V(0, -0.285, 0.566))]
JAW = [hv(V(0, -0.14, 0.56)), hv(V(0, -0.21, 0.542)), hv(V(0, -0.272, 0.532))]
BROW = [hv(V(0.066, -0.2, 0.63)), hv(V(0.036, -0.226, 0.631)), hv(V(0.0, -0.236, 0.621))]     # the heavy brow ridge, its left half: low in the middle, a scowl
ARM = [V(0.135, -0.1, 0.465), V(0.21, -0.065, 0.39), V(0.272, -0.025, 0.305), V(0.252, -0.13, 0.19), V(0.22, -0.235, 0.078)]     # shoulder, mid, elbow, mid, wrist: elbows back and out, a crouching beast's
ARM_R = [0.06, 0.046, 0.044, 0.036, 0.019]
LEG = [V(0.092, 0.09, 0.25), V(0.155, -0.065, 0.275), V(0.128, 0.115, 0.135), V(0.118, -0.008, 0.032)]     # hip, knee, hock, ball of the foot
LEG_R = [0.078, 0.056, 0.035, 0.028]
TAIL = [V(0, 0.15, 0.235), V(0, 0.245, 0.135), V(0.05, 0.3, 0.055), V(0.15, 0.292, 0.036), V(0.24, 0.205, 0.033), V(0.282, 0.075, 0.031), V(0.272, -0.05, 0.026)]
TAIL_R = ((0, 0.056), (0.2, 0.045), (0.5, 0.032), (0.8, 0.02), (1, 0.0105))
# the face: polished smooth over the muzzle, the cheekbones and between the eyes, a dark violet mirror; every other surface knapped
SLIT = (hv(V(0.016, -0.248, 0.612)), hv(V(0.05, -0.224, 0.621)))     # each eye: a slit of light, inner end to outer end (where it lies on the face is found by a ray)
SLIT_R = 0.0036 * HEAD_K
# the wings, as built: folded up behind it as gargoyles hold them, each wrist a peak above its shoulder with a short spike, the shards hanging from it
# down behind and outside the body like a mantle; they open out for flight. A bony arm and broad knapped shards with gaps between them: never feathers
W_ROOT, W_ELBOW, W_WRIST = V(0.055, -0.02, 0.5), V(0.17, 0.14, 0.6), V(0.245, 0.04, 0.88)
W_NORMAL = V(0.95, -0.12, 0.25).normalized()       # the folded wing's face, out to its side
HUB_R = 0.032


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def tangent_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return (path[i + 1] - path[i]).normalized()


# ---------- per-vertex tags (Blender's sphere primitive reuses freed vertex slots: what a vertex must carry is written on it) ----------
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


# ---------- knapped blades: one maker for wing blades, horns, brow shards, spurs and the tail's point ----------
class Blade:
    """A leaf of knapped glass along a curved spine. across: the way its width lies. width: half-widths along it (knots). thick: at the midrib.
    flakes: how many pressure flakes run along each edge; serr: how deep the edge's teeth bite (a share of the width)."""

    def __init__(self, knots, across, width, thick, flakes=7, serr=0.04, cup=0.0, edge=0.0016, per=8, width_b=None):
        self.spine = catmull(knots, per)
        self.across, self.width, self.thick, self.flakes, self.serr, self.cup, self.edge = across, width, thick, flakes, serr, cup, edge
        self.width_b = width_b or width          # the other edge's half-widths (a knife: one edge straight, one bellied)

    def frame(self, u):
        t = tangent_at(self.spine, u)
        a = (self.across - t * t.dot(self.across)).normalized()
        return path_at(self.spine, u), t, a, t.cross(a).normalized()

    def flake(self, u, s):
        """Where a point sits in its edge's row of flakes: -0.5..0.5 across each flake."""
        k = u * self.flakes + (0.5 if s < 0 else 0.0)
        return k - math.floor(k) - 0.5

    def point(self, u, v, hi=True):
        s = 2 * v - 1
        p, t, a, n = self.frame(u)
        w = prof(self.width if s >= 0 else self.width_b, u)
        if hi:
            w *= 1 - self.serr * (2 * self.flake(u, s)) ** 2
        else:
            w *= 1 - self.serr          # the game mesh's outline never stands outside the teeth, so the bake never misses
        return p + a * (w * s) + n * (self.cup * w * (1 - s * s))

    def thickness(self, u, v, hi=True):
        s = 2 * v - 1
        body = self.thick * math.sqrt(max(0.0, 1 - s * s)) * (0.45 + 0.55 * math.sin(math.pi * min(1.0, 0.15 + u)) ** 0.5) * (1 - 0.7 * float(smooth(0.75, 1.0, u)))
        if hi:
            a = self.flake(u, s)
            dish = (1 - 4 * a * a) * float(smooth(0.08, 0.35, abs(s))) * float(smooth(1.0, 0.82, abs(s)))     # each flake a shallow groove, edge to midrib
            body *= 1 - 0.32 * dish
        return body + self.edge


def build_blades(blades, name, coll, res, hi=True):
    """blades: (Blade, tag). Each vertex carries its blade's tag and how far along it lies."""
    m = Mesh()
    make_tags(m.bm, ints=("blade",), floats=("along",))
    nu, nv = res
    for b, tag in blades:
        before = set(m.bm.verts)
        m.sheet(lambda u, v, b=b: tuple(b.point(u, v, hi)), lambda u, v, b=b: b.thickness(u, v, hi), nu, nv)
        tag_new(m.bm, before, blade=tag)
        al = m.bm.verts.layers.float["along"]
        new = [v for v in m.bm.verts if v not in before]
        f, _ = nearest_on(b.spine, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[al] = float(ff)
    return m.finish(name, coll)


# ---------- the wings ----------
def wing_frame(side):
    """The wing's joints, its forearm's line (out), the wing's face (normal) and, square to both in the wing's plane, the way toward its rear (back)."""
    root, elbow, wrist = mir(W_ROOT, side), mir(W_ELBOW, side), mir(W_WRIST, side)
    out = (wrist - elbow).normalized()
    normal = mir(W_NORMAL, side)
    normal = (normal - out * out.dot(normal)).normalized()
    back = normal.cross(out).normalized()
    if back.y < 0:
        back = -back
    return root, elbow, wrist, out, back, normal


def fan_dir(out, back, angle):
    """Round from the forearm's line toward the rear by this angle (radians), in the wing's plane."""
    return (out * math.cos(angle) + back * math.sin(angle)).normalized()


# each shard's outline: half-widths along it on its leading side, then on its trailing side; straight runs between knots, the trailing side notched
SHARDS = (
    (((0, 0.016), (0.5, 0.03), (0.85, 0.016), (1, 0.003)), ((0, 0.02), (0.2, 0.07), (0.34, 0.058), (0.5, 0.082), (0.74, 0.05), (0.86, 0.056), (1, 0.003))),
    (((0, 0.016), (0.4, 0.034), (0.8, 0.02), (1, 0.003)), ((0, 0.022), (0.24, 0.08), (0.42, 0.066), (0.6, 0.074), (0.8, 0.036), (1, 0.003))),
    (((0, 0.016), (0.45, 0.03), (0.86, 0.014), (1, 0.003)), ((0, 0.02), (0.18, 0.064), (0.38, 0.078), (0.55, 0.06), (0.72, 0.066), (0.9, 0.02), (1, 0.003))),
    (((0, 0.016), (0.5, 0.028), (1, 0.003)), ((0, 0.02), (0.3, 0.07), (0.5, 0.058), (0.7, 0.062), (0.88, 0.024), (1, 0.003))),
)
PRIMARIES = ((0.0, 0.16, 3), (2.25, 0.5, 0), (2.6, 0.56, 1), (2.9, 0.5, 2))     # (angle round from the forearm's line, length, outline): the spike, then the mantle
SECONDARIES = ((0.3, 0.38, 1, 3.0), (0.7, 0.46, 0, 3.05))                     # (along the forearm, length, outline, angle)


def wing_blades(side):
    """Every shard of one wing: (Blade, tag): the fan at the wrist 0..3, the forearm's two 10, 11. Each lies a little behind the one before, never level
    with it; broad, jagged, with gaps between them: never feathers."""
    root, elbow, wrist, out, back, normal = wing_frame(side)
    blades = []
    for k, (angle, length, shape) in enumerate(PRIMARIES):
        d = fan_dir(out, back, angle)
        r = wrist + d * (HUB_R * 0.1) - normal * (0.013 * k - 0.02)
        tip = r + d * length
        mid = r.lerp(tip, 0.5) + normal * 0.006
        lead, trail = SHARDS[shape]
        blades.append((Blade([r - d * 0.016, mid, tip], -normal.cross(d), lead, 0.02, flakes=5, serr=0.03, cup=0.03, width_b=trail), k))
    for k, (f, length, shape, angle) in enumerate(SECONDARIES):
        r = elbow.lerp(wrist, f) + normal * (0.009 - 0.024 * k)          # rooted inside the forearm, one each side of its middle
        d = fan_dir(out, back, angle)
        tip = r + d * length
        lead, trail = SHARDS[shape]
        blades.append((Blade([r - d * 0.024, r.lerp(tip, 0.5) + normal * 0.006, tip], -normal.cross(d), lead, 0.019, flakes=4, serr=0.03, cup=0.03, width_b=trail), 10 + k))
    return blades


def all_wing_blades():
    out = []
    for side in (1, -1):
        for b, tag in wing_blades(side):
            out.append((b, tag + (0 if side == 1 else 100)))
    return out


def wing_arm_path(side, per=8):
    root, elbow, wrist, out, back, normal = wing_frame(side)
    inner = root - (elbow - root).normalized() * 0.03
    return catmull([inner, root, root.lerp(elbow, 0.5) + V(0, 0, 0.012), elbow, elbow.lerp(wrist, 0.5) + normal * 0.004, wrist], per)


def wing_arm_radius(f):
    return prof(((0, 0.036), (0.15, 0.035), (0.4, 0.027), (0.58, 0.029), (0.8, 0.022), (1, 0.024)), f)


def build_wing_arms(name, coll, sides=24, per=8, hub=(24, 14)):
    """The bony arm of each wing, rooted in the upper back, a knuckle at the elbow, a hub at the wrist where the blades fan, and a hooked thumb-talon on it."""
    m = Mesh()
    make_tags(m.bm, ints=("side", "kind"), floats=("along",))
    for side in (1, -1):
        root, elbow, wrist, out, back, normal = wing_frame(side)
        path = wing_arm_path(side, per)
        before = set(m.bm.verts)
        m.tube(path, wing_arm_radius, sides=sides)
        al = m.bm.verts.layers.float["along"]
        new = [v for v in m.bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[al] = float(ff)
        tag_new(m.bm, before, side=side, kind=0)
        before = set(m.bm.verts)
        m.ball(elbow, (0.033, 0.033, 0.033), *hub)
        tag_new(m.bm, before, side=side, kind=1)
        before = set(m.bm.verts)
        m.ball(wrist, (HUB_R, HUB_R, HUB_R * 0.9), *hub)
        thumb = [wrist - back * 0.012, wrist - back * 0.035 + out * 0.012, wrist - back * 0.058 + out * 0.004 - V(0, 0, 0.012)]
        m.tube(catmull(thumb, per // 2 + 1), lambda f: 0.011 * (1 - f) ** 0.9 + 0.0015, sides=max(8, sides // 2))
        tag_new(m.bm, before, side=side, kind=2)
    o = m.finish(name, coll)
    return o


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    core.tube(catmull(SPINE, 8), lambda f: prof(((0, 0.08), (0.35, 0.074), (0.7, 0.088), (1, 0.08)), f), sides=40)
    core.ball(PELVIS, (0.09, 0.09, 0.076))
    core.ball(CHEST, (0.098, 0.11, 0.1))                                # a deep, narrow ribcage, a beast's, not a man's
    core.ball(V(0, -0.055, 0.5), (0.12, 0.085, 0.06))                  # the hunch: shoulders and back rise above the neck, so the head sits low between them
    core.ball(V(0, 0.01, 0.33), (0.074, 0.066, 0.07))                  # the belly
    for side in (1, -1):
        core.ball(V(side * 0.13, -0.095, 0.47), (0.058, 0.062, 0.062))  # the shoulder, heavy
        core.tube(catmull([mir(p, side) for p in (V(0.05, -0.06, 0.47), ARM[0], ARM[1], ARM[2])], 6), lambda f: prof(((0, 0.05), (0.33, 0.058), (0.66, 0.046), (1, 0.042)), f), sides=24)
        core.tube(catmull([mir(p, side) for p in (V(0.05, 0.09, 0.25), LEG[0], LEG[1])], 6), lambda f: prof(((0, 0.07), (0.5, 0.076), (1, 0.054)), f), sides=24)
        core.ball(V(side * 0.086, 0.07, 0.25), (0.074, 0.09, 0.074))   # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    fine = Mesh()
    fine.tube(catmull(NECK, 6), lambda f: 0.062 - 0.01 * f, sides=36)
    fine.ball(CRANIUM, CRANIUM_R, 40, 28)
    fine.tube(catmull(MUZZLE, 6), lambda f: (0.044 - 0.016 * f) * HEAD_K, sides=32, flat=1.12)
    fine.ball(MUZZLE[-1] + V(0, -0.002, -0.002) * HEAD_K, tuple(r * HEAD_K for r in (0.029, 0.014, 0.022)))      # the blunt end of the muzzle
    fine.tube(catmull(JAW, 6), lambda f: (0.04 - 0.012 * f) * HEAD_K, sides=28, flat=1.2)
    fine.ball(JAW[-1] + V(0, -0.003, 0.0) * HEAD_K, tuple(r * HEAD_K for r in (0.03, 0.016, 0.022)))          # the chin, broad
    for side in (1, -1):
        fine.tube(catmull([mir(p, side) for p in BROW], 6), lambda f: (0.0095 * (1 - 0.3 * f) * math.sin(math.pi * (0.15 + 0.85 * f)) ** 0.4 + 0.002) * HEAD_K, sides=20, flat=1.9)
        fine.ball(hv(V(side * 0.054, -0.205, 0.594)), tuple(r * HEAD_K for r in (0.02, 0.026, 0.017)))     # the cheekbone
        fine.ball(hv(V(side * 0.05, -0.152, 0.565)), tuple(r * HEAD_K for r in (0.03, 0.038, 0.028)))      # the jaw's muscle
        wrist, palm = hand_frame(side)
        fine.tube(catmull([mir(p, side) for p in ARM] + [palm], 6), lambda f: prof(list(zip(np.linspace(0, 1, len(ARM_R) + 1), ARM_R[:-1] + [0.022, 0.017])), f), sides=24)     # (on into the palm's middle)
        fine.ball(mir(ARM[2], side) + V(side * 0.004, 0.012, 0.0), (0.044, 0.044, 0.044))     # the elbow
        fine.tube(catmull([mir(p, side) for p in LEG], 8), lambda f: prof(list(zip(np.linspace(0, 1, len(LEG_R)), LEG_R)), f), sides=24)
        fine.ball(mir(LEG[2], side) + V(0, 0.008, 0.0), (0.03, 0.032, 0.032))      # the hock
    fine.tube(catmull(TAIL, 8), lambda f: prof(TAIL_R, f), sides=28)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    c.name = N + "SkinHi"
    facet(c)
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- hands and feet: their own pieces, so fingers and toes keep their shape in the game mesh ----------
def digits(base, dirs, knots, side):
    """Per digit: its path from inside the palm or foot out to the talon's root. dirs: angles from straight ahead (positive: outward)."""
    out = []
    for a, reach, rise in dirs:
        d = V(math.sin(a) * side, -math.cos(a), 0)
        out.append([base + d * (reach * k0) + V(0, 0, rise * k1) for k0, k1 in knots])
    return out


HAND_DIRS = ((-0.42, 0.074, 0.03), (0.0, 0.082, 0.032), (0.42, 0.072, 0.028))
HAND_KNOTS = ((0.0, 0.2), (0.4, 0.95), (0.72, 0.9), (1.0, 0.25))
FOOT_DIRS = ((-0.38, 0.066, 0.026), (0.0, 0.074, 0.028), (0.4, 0.064, 0.024))
FOOT_KNOTS = ((0.0, 0.3), (0.42, 1.0), (0.75, 0.8), (1.0, 0.2))


def hand_frame(side):
    wrist = mir(ARM[-1], side)
    palm = wrist + V(-0.004 * side, -0.035, -0.045)
    return wrist, palm


def foot_frame(side):
    ball = mir(LEG[-1], side)
    return ball, ball + V(0, -0.012, -0.008)


def talon(path):
    """A hooked talon from a digit's end down to the ground, knapped to a point."""
    a, b = path[-2], path[-1]
    d = b - a
    d = V(d.x, d.y, 0).normalized()
    return [b - d * 0.006, b + d * 0.012 + V(0, 0, 0.0), b + d * 0.024 + V(0, 0, -0.008), b + d * 0.028 + V(0, 0, -max(0.0, b.z - 0.004))]


def build_hands(name, coll, ball=(24, 14), sides=14, per=4):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        wrist, palm = hand_frame(side)
        m.ball(palm, (0.034, 0.036, 0.019), *ball)
        fingers = digits(palm + V(0, -0.012, 0.0), HAND_DIRS, HAND_KNOTS, side)
        thumb = digits(palm + V(-0.016 * side, 0.004, 0.0), ((-1.3, 0.05, 0.022),), HAND_KNOTS, side)
        for k, f in enumerate(fingers + thumb):
            m.tube(catmull(f, per), lambda t: 0.013 * (1 - 0.3 * t), sides=sides)
            m.ball(f[1], (0.0142, 0.0142, 0.0142), 16, 10)              # the knuckle
            m.tube(catmull(talon(f), per), lambda t: 0.009 * (1 - t) ** 0.85 + 0.0012, sides=sides - 2)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


def build_feet(name, coll, ball=(24, 14), sides=14, per=4):
    m = Mesh()
    make_tags(m.bm, ints=("side",))
    for side in (1, -1):
        before = set(m.bm.verts)
        b, pad = foot_frame(side)
        m.ball(pad, (0.03, 0.036, 0.02), *ball)
        toes = digits(pad + V(0, -0.014, 0.0), FOOT_DIRS, FOOT_KNOTS, side)
        dew = [pad + V(side * -0.012, 0.012, 0.004), pad + V(side * -0.02, 0.03, 0.012), pad + V(side * -0.024, 0.045, 0.008)]
        for f in toes + [dew]:
            m.tube(catmull(f, per), lambda t: 0.0125 * (1 - 0.3 * t), sides=sides)
            m.ball(f[1], (0.0135, 0.0135, 0.0135), 16, 10)
            m.tube(catmull(talon(f), per), lambda t: 0.0095 * (1 - t) ** 0.85 + 0.0012, sides=sides - 2)
        tag_new(m.bm, before, side=side)
    return m.finish(name, coll)


# ---------- the face ----------
def on_face(tree, p, toward=V(0, 1, 0), lift=0.0):
    """Where a point seen from in front lies on the face (a ray toward the head), lifted off it."""
    loc, nrm, _, _ = tree.ray_cast(p - toward * 0.12, toward, 0.3)
    return (loc + nrm * lift, nrm) if loc is not None else (p, -toward)


def slit_path(tree, side, per=6):
    a, b = (mir(q, side) for q in SLIT)
    pts = [on_face(tree, a.lerp(b, k / 4), V(0, 0.95, 0.3).normalized())[0] for k in range(5)]     # (from below: under the brow, never on it)
    return catmull(pts, per)


def build_slits(tree, name, coll, sides=16, per=6):
    """Two slits of violet light set deep under the brow, slanting up to the outside: its eyes. Half sunk in the face."""
    m = Mesh()
    for side in (1, -1):
        m.tube(slit_path(tree, side, per), lambda f: SLIT_R * (0.3 + 0.7 * math.sin(math.pi * f) ** 0.5), sides=sides, flat=1.0)
    return m.finish(name, coll)


def polished(P, Nn):
    """1 over the face's mirror: the muzzle, the cheekbones and between the eyes, facing forward; 0 where the glass is knapped."""
    H = head_local(P)
    x, y, z = np.abs(H[:, 0]), H[:, 1], H[:, 2]
    width = np.interp(z, [0.548, 0.565, 0.6, 0.618, 0.628], [0.02, 0.046, 0.066, 0.05, 0.016])
    inside = (1 - smooth(width - 0.004, width, x)) * smooth(0.551, 0.557, z) * (1 - smooth(0.623, 0.629, z + 0.25 * x))
    front = smooth(-0.17, -0.2, y) * smooth(-0.05, -0.35, Nn[:, 1] + 0.3 * np.maximum(Nn[:, 2], 0))
    return np.clip(inside * front, 0, 1)


def brow_blades(tree):
    """Each brow: a shard rooted in the temple, lying along the brow ridge over the eye and down toward the middle: a frown; its bone lowers or lifts it."""
    out = []
    for side in (1, -1):
        p0, n0 = on_face(tree, mir(hv(V(0.07, -0.19, 0.636)), side), V(-0.6 * side, 0.6, -0.5).normalized())
        p1, n1 = on_face(tree, mir(hv(V(0.012, -0.236, 0.628)), side), V(0, 0.8, -0.6).normalized())
        root = p0 - n0 * 0.008
        tip = p1 + n1 * 0.011
        mid = root.lerp(tip, 0.5) + (n0 + n1).normalized() * 0.016 * HEAD_K
        out.append((Blade([root, mid, tip], (n0 + n1).normalized().cross(tip - root).normalized(), tuple((u, w * HEAD_K) for u, w in ((0, 0.011), (0.3, 0.013), (0.75, 0.009), (1, 0.003))),
                          0.009 * HEAD_K, flakes=4, serr=0.05, cup=0.0, edge=0.0013, per=6), 0 if side == 1 else 1))
    return out


HORN_KNOTS = (V(0.034, -0.16, 0.636), V(0.058, -0.118, 0.676), V(0.084, -0.05, 0.702), V(0.104, 0.024, 0.712), V(0.114, 0.09, 0.704))


def horn_path(side, per=8):
    return catmull([mir(hv(p), side) for p in HORN_KNOTS], per)


def horn_radius(f):
    return (0.024 * (1 - f) ** 0.85 + 0.0016) * HEAD_K


def build_horns(name, coll, sides=7, per=8):
    """Swept back from the brow, thick at the root, knapped to a point: few sides, so its faces stay flat like struck glass."""
    m = Mesh()
    for side in (1, -1):
        m.tube(horn_path(side, per), horn_radius, sides=sides, flat=0.8)
    return m.finish(name, coll, smooth_shade=False)


def tusk_paths(side, per=6):
    return catmull([mir(hv(p), side) for p in (V(0.04, -0.236, 0.532), V(0.054, -0.244, 0.55), V(0.062, -0.25, 0.572), V(0.061, -0.248, 0.586))], per)


def build_tusks(name, coll, sides=14, per=6):
    m = Mesh()
    for side in (1, -1):
        m.tube(tusk_paths(side, per), lambda f: (0.0068 * (1 - f) ** 0.8 + 0.0012) * HEAD_K, sides=sides)
    return m.finish(name, coll)


def spur_blades():
    """A knapped spur at the back of each elbow."""
    out = []
    for side in (1, -1):
        e = mir(ARM[2], side)
        root = e + V(side * 0.004, 0.012, 0.004)
        out.append((Blade([root, root + V(side * 0.016, 0.04, 0.012), root + V(side * 0.026, 0.078, 0.03)], V(side, 0, 0.4),
                          ((0, 0.012), (0.35, 0.014), (0.7, 0.009), (1, 0.002)), 0.012, flakes=4, serr=0.05), 0 if side == 1 else 1))
    return out


def tail_point_path(per=8):
    end = TAIL[-1]
    d = (TAIL[-1] - TAIL[-2]).normalized()
    return catmull([end - d * 0.02, end + d * 0.03 + V(0, 0, -0.002), end + d * 0.075 + V(0, 0, -0.006), end + d * 0.11 + V(0, 0, -0.01)], per)


def tail_point_radius(f):
    return prof(((0, 0.0118), (0.2, 0.02), (0.42, 0.03), (0.7, 0.022), (0.92, 0.007), (1, 0.0015)), f)


def build_tail_point(name, coll, sides=6, per=8):
    """The tail's end: a knapped spearhead, wider than it is deep, its faces flat."""
    m = Mesh()
    m.tube(tail_point_path(per), tail_point_radius, sides=sides, flat=1.0, plane=V(0, 0, 1))
    o = m.finish(name, coll, smooth_shade=False)
    P = verts(o)
    c = np.array(tuple(TAIL[-1]))
    P[:, 2] = c[2] + (P[:, 2] - c[2]) * 0.5          # flattened: a blade lying on the ground, not a cone
    set_verts(o, P)
    return o


# ---------- knapped glass, painted: flake scars over the skin ----------
def cells(P, f, seed=0):
    """Flake cells: distance to the nearest and second-nearest cell point (in cell units), and the nearest cell's own random number."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    own = np.zeros(len(P))
    key = np.zeros(len(P), dtype=np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                key = np.where(nearer, ((c[:, 0] + 512) * 1024 + (c[:, 1] + 512)) * 1024 + (c[:, 2] + 512), key)
                d1 = np.where(nearer, d, d1)
    cells.key = key
    return d1, d2, own


def fine_zone(P):
    """1 where the flakes are small: the head, the hands and the feet; 0 over the body."""
    head = np.linalg.norm((head_local(P) - np.array((0, -0.2, 0.6))) / np.array((0.09, 0.11, 0.09)), axis=1)
    low = P[:, 2] < 0.1
    return np.maximum(1 - smooth(0.9, 1.2, head), low * 1.0)


def flake_field(P, Nn, scale=1.0):
    """Per point: how deep in its flake scar (0 at a ridge, 1 at the middle), the ripple rings in it, and the cell's own number."""
    zone = fine_zone(P)
    a1, a2, ao = cells(P, FACET_F[0] * scale, 3)
    b1, b2, bo = cells(P, FACET_F[1] * scale, 7)
    inner_a = smooth(0.0, 0.32, a2 - a1)
    inner_b = smooth(0.0, 0.32, b2 - b1)
    inner = inner_a * (1 - zone) + inner_b * zone
    ripple = np.sin((a1 * (1 - zone) + b1 * zone) * 26.0) * inner
    own = ao * (1 - zone) + bo * zone
    return inner, ripple, own


FACET_F = (17.0, 40.0)          # facets per metre over the body, and over the head, hands and feet


def facet(o, scale=1.0, strength=0.9):
    """Cuts the surface into flat facets, as a knapped stone is: each cell's points (each side of a thin part apart) pressed onto one plane. Not the face's mirror."""
    P, Nn = verts(o), normals(o)
    zone = fine_zone(P) > 0.5
    keys = np.zeros(len(P), dtype=np.int64)
    for fine, f, seed in ((False, FACET_F[0] * scale, 3), (True, FACET_F[1] * scale, 7)):
        cells(P, f, seed)
        keys = np.where(zone == fine, cells.key * 2 + int(fine), keys)
    side = np.argmax(np.abs(Nn), axis=1) * 2 + (Nn[np.arange(len(P)), np.argmax(np.abs(Nn), axis=1)] > 0)
    _, group = np.unique(keys * 8 + side, return_inverse=True)
    count = np.bincount(group).astype(float)
    centre = np.stack([np.bincount(group, P[:, k]) for k in range(3)], 1) / count[:, None]
    normal = np.stack([np.bincount(group, Nn[:, k]) for k in range(3)], 1)
    normal /= np.linalg.norm(normal, axis=1)[:, None] + 1e-9
    d = ((P - centre[group]) * normal[group]).sum(1)
    H = head_local(P)
    jaw = (1 - smooth(0.9, 1.15, np.linalg.norm((H - np.array((0, -0.22, 0.55))) / np.array((0.08, 0.09, 0.04)), axis=1)))     # the jaw and the mouth: left smooth
    mirror = polished(P, Nn)
    keep = strength * (1 - mirror) * (1 - jaw)
    P2 = P - normal[group] * (d * keep)[:, None]
    # the mirror: a few broad flat facets, polished, like a cut visor
    cells(P, 15.0, 17)
    side2 = side
    _, g2 = np.unique(cells.key * 8 + side2, return_inverse=True)
    c2 = np.stack([np.bincount(g2, P[:, k]) for k in range(3)], 1) / np.bincount(g2).astype(float)[:, None]
    n2 = np.stack([np.bincount(g2, Nn[:, k]) for k in range(3)], 1)
    n2 /= np.linalg.norm(n2, axis=1)[:, None] + 1e-9
    d2 = ((P - c2[g2]) * n2[g2]).sum(1)
    P2 = P2 - n2[g2] * (d2 * 0.85 * mirror)[:, None]
    set_verts(o, P2)


def knap(o, depth=0.0017, scale=1.0):
    """Dishes each flake scar into the surface, with fine ripple rings in it."""
    P, Nn = verts(o), normals(o)
    inner, ripple, _ = flake_field(P, Nn, scale)
    zone = fine_zone(P)
    d = depth * (1 - 0.4 * zone) * (1 - polished(P, Nn))
    set_verts(o, P - Nn * (d * inner + 0.00022 * ripple)[:, None])


def obsidian(P, Nn, inner, ripple, own, seed=0):
    """Glassy black: each flake a little its own shade, violet flow-banding running through the glass, the ridges between flakes catching the light."""
    col = mix(np.broadcast_to(OBS, (len(P), 3)), OBS_DEEP, 0.6 * own)
    band = np.sin(P[:, 2] * 70 + 10 * fbm(P, 3.0, 3, seed + 11) + P[:, 0] * 18)
    col = mix(col, SHEEN, smooth(0.8, 0.97, band) * 0.4 * smooth(0.2, 0.8, own))      # thin streaks of it, as flow-banded obsidian has
    col = mix(col, OBS_RIDGE, (1 - smooth(0.0, 0.2, inner)) * 0.22)
    col = mix(col, col * 1.2, (ripple * 0.5 + 0.5) * 0.12)
    rough = 0.08 + 0.14 * (1 - smooth(0.0, 0.35, inner))
    return col, rough


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    inner, ripple, own = flake_field(P, Nn)
    col, rough = obsidian(P, Nn, inner, ripple, own)
    mirror = polished(P, Nn)
    col = mix(col, MIRROR, mirror)
    rough = rough * (1 - mirror) + 0.03 * mirror
    rim = smooth(0.15, 0.45, mirror) * (1 - smooth(0.55, 0.85, mirror))          # the plate's edge, catching the light
    col = mix(col, OBS_RIDGE * 1.4, rim * 0.7)
    # the mouth: a dark seam where the muzzle meets the jaw
    H = head_local(P)
    hy, hz = H[:, 1], H[:, 2]
    mouth_z = np.interp(hy, [-0.29, -0.26, -0.2, -0.15], [0.548, 0.549, 0.554, 0.56])
    near_mouth = (hy < -0.14) & (hy > -0.298)
    seam = (1 - smooth(0.0016, 0.0035, np.abs(hz - mouth_z))) * near_mouth * (np.abs(H[:, 0]) < 0.058)
    col = mix(col, OBS_DEEP * 0.4, seam)
    paint(o, col, rough, mirror * (1 - seam))


def paint_glass_piece(o, scale=1.6, seed=0):
    """A hand, a foot or a wing's arm: the same knapped glass in smaller flakes."""
    P, Nn = verts(o), normals(o)
    inner, ripple, own = flake_field(P, Nn, scale)
    col, rough = obsidian(P, Nn, inner, ripple, own, seed)
    paint(o, col, rough, np.zeros(len(P)))


def paint_blades(o, blades, res):
    """Glossy black, the flake ridges catching the light, the thin edge smoky violet where light gets through, a fine violet seam down the midrib."""
    nu, nv = res
    per = (nu + 1) * (nv + 1) * 2
    uu, vv = [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            uu += [i / nu, i / nu]
            vv += [j / nv, j / nv]
    uu, vv = np.tile(np.array(uu), len(blades)), np.tile(np.array(vv), len(blades))
    assert len(uu) == len(o.data.vertices), (len(uu), len(o.data.vertices))
    s = 2 * vv - 1
    flakes = np.repeat(np.array([b.flakes for b, _ in blades]), per)
    k = uu * flakes + np.where(s < 0, 0.5, 0.0)
    a = k - np.floor(k) - 0.5
    groove = (1 - 4 * a * a) * smooth(0.08, 0.35, np.abs(s))
    ridge = 1 - smooth(0.0, 0.25, 1 - 4 * a * a)
    P = verts(o)
    own = hash01(np.floor(k).astype(np.int64), np.repeat(np.arange(len(blades)), per), (s < 0).astype(np.int64), 9)
    col = mix(np.broadcast_to(OBS, (len(uu), 3)), OBS_DEEP, 0.35 * own)
    edge = smooth(0.62, 0.98, np.abs(s))
    col = mix(col, SMOKE, edge * 0.75)
    col = mix(col, OBS_RIDGE, ridge * smooth(0.1, 0.4, np.abs(s)) * (1 - edge) * 0.6)
    col = mix(col, SHEEN, (1 - smooth(0.02, 0.07, np.abs(s))) * 0.35)
    band = np.sin(P[:, 2] * 60 + uu * 9)
    col = mix(col, SHEEN, smooth(0.6, 0.95, band) * 0.25 * (1 - edge))
    paint(o, col, 0.07 + 0.12 * ridge + 0.05 * groove * 0, np.zeros(len(uu)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 3.0
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
BLADE_RES = (60, 22)
SMALL_RES = (36, 16)


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    pieces["Hands"] = build_hands(N + "HandsHi", HI)
    pieces["Feet"] = build_feet(N + "FeetHi", HI)
    for key, o in (("Hands", pieces["Hands"]), ("Feet", pieces["Feet"])):
        apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0018, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 3})])
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    pieces["WingArms"] = build_wing_arms(N + "WingArmsHi", HI)
    data["wing"] = all_wing_blades()
    pieces["Wings"] = build_blades(data["wing"], N + "WingsHi", HI, BLADE_RES)
    pieces["Horns"] = build_horns(N + "HornsHi", HI, sides=7, per=10)
    data["brows"] = brow_blades(data["tree"])
    pieces["Brows"] = build_blades(data["brows"], N + "BrowsHi", HI, SMALL_RES)
    data["spurs"] = spur_blades()
    pieces["Spurs"] = build_blades(data["spurs"], N + "SpursHi", HI, SMALL_RES)
    pieces["TailPoint"] = build_tail_point(N + "TailPointHi", HI)
    pieces["Tusks"] = build_tusks(N + "TusksHi", HI)
    glows = {"Eyes": build_slits(data["tree"], N + "Eyes_Glow_" + EYE_HEX, HI)}
    if not clay:
        knap(skin)
        paint_skin(skin)
        for key in ("Hands", "Feet", "WingArms"):
            knap(pieces[key], 0.0012, 1.7)
            paint_glass_piece(pieces[key], 1.7)
        paint_blades(pieces["Wings"], data["wing"], BLADE_RES)
        paint_glass_piece(pieces["Horns"], 3.0, 5)
        paint_glass_piece(pieces["TailPoint"], 3.0, 6)
        for key in ("Brows", "Spurs"):
            paint_blades(pieces[key], data[key.lower()], SMALL_RES)
        paint_glass_piece(pieces["Tusks"], 3.0)
    return pieces, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.05, 0.55)
FACE_AT = (0, -0.3, 0.55)
EXTRA = [(0, -1, 0.08, 0.55, FACE_AT), (0.62, -0.75, 0.2, 0.55, FACE_AT), (1, -0.1, 0.08, 0.55, FACE_AT), (0.3, -0.9, 0.3, 0.6, (0.2, -0.2, 0.06)),
         (0.7, -0.3, 0.2, 0.6, (0.12, -0.02, 0.05)), (0.6, 0.6, 0.5, 1.6, (0.3, 0.2, 0.75))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.04, ao_share=0.35)
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        attr = mat.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "metal"
        mat.node_tree.links.new(attr.outputs["Fac"], b.inputs["Metallic"])      # (review only: the bake stage leaves the metal to its own pass)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3300
LOW_BLADE = (6, 4)
LOW_SMALL = (4, 4)
SCALES = {"Hands": 1.2, "Feet": 1.0, "WingArms": 0.8, "Wings": 0.85, "Horns": 1.2, "Brows": 1.6, "Spurs": 1.0, "TailPoint": 1.0, "Tusks": 1.6}


def build_low(pieces, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    lows["Hands"] = decimated(pieces["Hands"], N + "HandsLow", 1700)
    lows["Feet"] = decimated(pieces["Feet"], N + "FeetLow", 1500)
    lows["WingArms"] = build_wing_arms(N + "WingArmsLow", GAME, sides=8, per=3, hub=(10, 6))
    lows["Wings"] = build_blades(all_wing_blades(), N + "WingsLow", GAME, LOW_BLADE, hi=False)
    lows["Horns"] = build_horns(N + "HornsLow", GAME, sides=7, per=3)
    lows["Brows"] = build_blades(brow_blades(data["tree"]), N + "BrowsLow", GAME, LOW_SMALL, hi=False)
    lows["Spurs"] = build_blades(spur_blades(), N + "SpursLow", GAME, LOW_SMALL, hi=False)
    lows["TailPoint"] = build_tail_point(N + "TailPointLow", GAME, sides=6, per=3)
    lows["Tusks"] = build_tusks(N + "TusksLow", GAME, sides=6, per=2)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the hips are its base; the trunk runs hips, body, chest, neck, head
TRUNK = catmull(SPINE, 8) + catmull(NECK, 6)[1:] + [CRANIUM, MUZZLE[-1]]
TRUNK_HEADS = (("Hips", PELVIS.copy(), "Root"), ("Body", SPINE[2].copy(), "Hips"), ("Chest", SPINE[3].copy(), "Body"), ("Neck", NECK[0].copy(), "Chest"),
               ("Head", NECK[-1].copy(), "Neck"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 6)]
TAIL_F = (0.06, 0.24, 0.42, 0.6, 0.78)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
TAIL_LINE = catmull(TAIL, 8)
WING_BONES = ("Wing%s1", "Wing%s2", "Wing%s3")


def arm_line(side):
    wrist, palm = hand_frame(side)
    return catmull([mir(p, side) for p in ARM] + [palm], 6)


def leg_line(side):
    return catmull([mir(p, side) for p in LEG], 8)


def limbs():
    """Per limb: its key, side, line, its bones' names, where each bone's head sits along the line (0..1), and its parent."""
    out = []
    for side, tag in ((1, "L"), (-1, "R")):
        line = arm_line(side)
        f, _ = nearest_on(line, np.array([tuple(mir(ARM[k], side)) for k in (0, 2, 4)]))
        out.append(("A" + tag, side, line, ["Arm%s1" % tag, "Arm%s2" % tag, "Hand" + tag], tuple(f), "Chest"))
        line = leg_line(side)
        f, _ = nearest_on(line, np.array([tuple(mir(p, side)) for p in LEG]))
        out.append(("L" + tag, side, line, ["Leg%s1" % tag, "Leg%s2" % tag, "Leg%s3" % tag, "Foot" + tag], tuple(f), "Hips"))
    return out


def skeleton(data):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at, parent))
    for b, tag in data["brows"]:
        bones.append(("Brow" + ("L" if tag == 0 else "R"), b.spine[0].copy(), "Head"))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL_LINE, f), parent))
        parent = name
    for key, side, line, names, fs, parent in limbs():
        for name, f in zip(names, fs):
            bones.append((name, path_at(line, f), parent))
            parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        root, elbow, wrist, out, back, normal = wing_frame(side)
        n1, n2, n3 = (n % tag for n in WING_BONES)
        bones += [(n1, root, "Chest"), (n2, elbow, n1), (n3, wrist, n2)]
        bones += [("Wing%sF%d" % (tag, k), wrist.copy(), n3) for k in (1, 2, 3)]
        bones.append(("Wing%sS" % tag, elbow.copy(), n2))          # the forearm's two shards, so they fan open with the rest
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.03,)


def limb_mids(fs):
    """Where each bone of a limb takes over: the middle of each bone; the last past its head."""
    return tuple((fs[k] + fs[k + 1]) / 2 for k in range(len(fs) - 1)) + (min(1.0, fs[-1] + 0.02),)


def skin_weights(P):
    """The trunk from hips to head; the head wholly the head's; the tail; the arms and legs, each handing over to the body across a span near its root."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    H = head_local(P)
    hz = np.linalg.norm((H - np.array((0, -0.215, 0.583))) / np.array((0.085, 0.1, 0.072)), axis=1)
    tf, td = nearest_on(TAIL_LINE, P)
    lim = [(key, side, line, lnames, fs, *nearest_on(line, P)) for key, side, line, lnames, fs, _ in limbs()]
    out = []
    for i in range(len(P)):
        x = P[i][0]
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.2:
            w = blend(w, {"Head": 1.0}, float(smooth(1.2, 0.95, hz[i])))
        reach = prof(TAIL_R, float(tf[i])) * 1.15 + 0.012
        share = (1 - float(smooth(reach, reach + 0.025, td[i]))) * float(smooth(0.0, 0.06, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, (TAIL_MID[0],) + TAIL_MID[1:], float(tf[i])), share)
        for key, side, line, lnames, fs, f, d in lim:
            if x * side <= 0.01:
                continue
            radii = ARM_R[:-1] + [0.022, 0.017] if key[0] == "A" else LEG_R
            lr = prof(list(zip(np.linspace(0, 1, len(radii)), radii)), float(f[i])) + 0.014
            outer = lr * (1.25 + 0.7 * float(smooth(0.35, 0.05, f[i])))      # near the shoulder or hip the hand-over spreads wider
            mm = float(smooth(0.02, 0.2, f[i])) * (1 - float(smooth(lr * 0.85, outer, d[i])))
            if mm > 0:
                w = blend(w, chain_weight(lnames, limb_mids(fs), float(f[i])), mm)
        out.append(w)
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    weigh(lows["Hands"], [{"HandL" if p[0] > 0 else "HandR": 1.0} for p in verts(lows["Hands"])])
    weigh(lows["Feet"], [{"FootL" if p[0] > 0 else "FootR": 1.0} for p in verts(lows["Feet"])])
    wa = lows["WingArms"]
    kinds, along = read_tag(wa, "kind"), read_tag(wa, "along")
    ww = []
    for p, k, a in zip(verts(wa), kinds, along):
        tag = "L" if p[0] > 0 else "R"
        n1, n2, n3 = (n % tag for n in WING_BONES)
        if k == 2:
            ww.append({n3: 1.0})
        elif k == 1:
            ww.append({n2: 1.0})
        else:
            sd = 1 if tag == "L" else -1
            fe, fw = nearest_on(wing_arm_path(sd, 3), np.array([tuple(mir(W_ELBOW, sd)), tuple(mir(W_WRIST, sd))]))[0]
            # bone, not flesh: each segment rigid, the share passing only across its joint
            if a < fe + 0.03:
                ww.append(blend({n1: 1.0}, {n2: 1.0}, float(smooth(fe - 0.05, fe + 0.03, a))))
            else:
                ww.append(blend({n2: 1.0}, {n3: 1.0}, float(smooth(fw - 0.05, fw, a))))
    weigh(wa, ww)
    blade = read_tag(lows["Wings"], "blade")
    weigh(lows["Wings"], [{("Wing%s3" % t) if b % 100 == 0 else ("Wing%sF%d" % (t, b % 100)) if b % 100 < 10 else ("Wing%sS" % t): 1.0}
                          for b, t in zip(blade, ["L" if b < 100 else "R" for b in blade])])
    weigh(lows["Brows"], [{"BrowL" if b == 0 else "BrowR": 1.0} for b in read_tag(lows["Brows"], "blade")])
    weigh(lows["Spurs"], [{"ArmL2" if b == 0 else "ArmR2": 1.0} for b in read_tag(lows["Spurs"], "blade")])
    rigid(lows["Horns"], "Head")
    rigid(lows["Tusks"], "Head")
    rigid(lows["TailPoint"], "Tail5")
    rigid(glows["Eyes"], "Head")
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateObsidianGuardian uses. +X lifts what points forward; +Y turns to its left; +Z rolls its
# right side up (a left wing takes the opposite sign)
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


# its stances in the game's axes, left side (the right is its mirror: a turn about X kept, those about Y and Z flipped), as searched in Blender against the
# ground, for torn skin and for its wings cutting into it, at each pose and along the way to it: the same numbers as PetRig's GUARD_* tables
FLY_BODY = {"Hips": (-0.45, 0, 0), "Neck": (0.22, 0, 0), "Head": (0.25, 0, 0), "Tail1": (-0.175, 0.199, 0), "Tail2": (0.335, 1.314, 0), "Tail3": (-1.184, 0.181, 0),
            "Tail4": (-0.159, 0.399, 0), "Tail5": (-0.159, 0.714, 0), "ArmL1": (0.2, 0, -0.3), "ArmL2": (-1.4, 0, 0)}
GLIDE = {"WingL1": (0.376, -0.61, 0.253), "WingL2": (0.334, -2.985, -1.33), "WingLS": (0.887, 0.172, -0.13), "WingLF1": (1.14, 0.193, -0.189),
         "WingLF2": (0.988, 0.182, -0.153), "WingLF3": (0.786, 0.159, -0.109)}
UP = {"WingL1": (-0.169, -0.271, -0.288), "WingL2": (0.48, 3.093, -1.119), "WingLS": (0.988, 0.182, -0.153), "WingLF1": (1.038, 0.186, -0.165),
      "WingLF2": (0.887, 0.172, -0.13), "WingLF3": (0.686, 0.145, -0.088)}
DOWN = {"WingL1": (0.913, -0.676, 0.807), "WingL2": (0.277, -2.802, -1.621), "WingLS": (0.937, 0.177, -0.142), "WingLF1": (1.191, 0.195, -0.201),
        "WingLF2": (1.038, 0.186, -0.165), "WingLF3": (0.837, 0.166, -0.119)}
MANTLE = {"WingL1": (-0.437, -0.647, -0.035), "WingL2": (-1.119, 0.447, 0.609), "WingLS": (0.587, 0.128, -0.07), "WingLF1": (0.488, 0.11, -0.053),
          "WingLF2": (0.439, 0.1, -0.045), "WingLF3": (0.39, 0.09, -0.038)}
RISE = {"Body": (0.32, 0, 0), "Chest": (0.12, 0, 0), "Neck": (-0.2, 0, 0), "Head": (-0.12, 0, 0), "ArmL1": (0.25, 0, -0.2), "ArmL2": (-0.3, 0, 0),
        "WingL1": (-0.696, -0.464, 0.039), "WingL2": (-2.721, 0.026, 1.913), "WingLS": (0.988, 0.182, -0.153), "WingLF1": (1.242, 0.197, -0.214),
        "WingLF2": (1.089, 0.19, -0.177), "WingLF3": (0.887, 0.172, -0.13)}
SIDED = ("Wing", "Arm", "Leg", "Brow", "Hand", "Foot")


def sided(table):
    out = dict(table)
    for bone, (rx, ry, rz) in table.items():
        for prefix in SIDED:
            if bone.startswith(prefix + "L"):
                out[prefix + "R" + bone[len(prefix) + 1:]] = (rx, -ry, -rz)
    return out


POSES = {"Glide": sided({**FLY_BODY, **GLIDE}), "Up": sided({**FLY_BODY, **UP}), "Down": sided({**FLY_BODY, **DOWN}), "Mantle": sided(MANTLE), "Rise": sided(RISE),
         "Look": {"Neck": (0.4 * 0.35, 0.38, 0), "Head": (0.6 * 0.35, 0.62, 0.1)}, "Glare": sided({"BrowL": (0, 0, -0.3)}), "Flash": sided({"BrowL": (0.2, 0, 0.25)})}


def pose_library():
    return {name: spec(table) for name, table in POSES.items()}


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


GROUND_PARTS = {"Feet": ("FootL", "FootR"), "Hands": ("HandL", "HandR"), "Tail": tuple(TAIL_NAMES), "Belly": ("Hips", "Body"), "Wings": tuple("Wing%s%d" % (t, k) for t in "LR" for k in (1, 2, 3))}

if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    mat = hi_material(ao_distance=0.04, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, data)
    head_c = CRANIUM + V(0, -0.04, -0.01)
    unwrap(lows, [(lambda p: (p.center - head_c).length < 0.13, 2.2), (None, 1.0)], SCALES, margin=0.008)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.07, 0.06, 0.09, 1), far=("Skin",), reach=(0.005, 0.012), far_reach=(0.008, 0.02),
             reaches={"Wings": (0.004, 0.01), "Brows": (0.003, 0.008), "Spurs": (0.003, 0.008), "Horns": (0.003, 0.008), "TailPoint": (0.003, 0.008), "Tusks": (0.002, 0.006)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    bpy.data.objects.remove(glows["Eyes"], do_unlink=True)          # first, so the game's piece takes its exact name
    glows = {"Eyes": build_slits(data["tree"], N + "Eyes_Glow_" + EYE_HEX, GAME, sides=8, per=3)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(data)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    print("HIPS SOLE metres from the Hips bone down to the lowest point", round(rig.data.bones["Hips"].head_local.z - min(zs), 4), flush=True)
    for name in ("Hips", "Head", "Chest", "WingL3", "Tail5", "BrowL"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.6, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in lib:
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
        shots(os.path.join(REVIEW, "pose" + name), [(0.62, -0.72, 0.3, 2.8, VIEW_AT), (1, -0.05, 0.1, 2.8, VIEW_AT)], target=VIEW_AT, size=480)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.3, 2.6, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

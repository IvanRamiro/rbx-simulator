"""The Celestial Pearl Dragon (Mythical, Celestial energy; Celestial Egg, also in the Heavenly Throne Egg): "A dragon that carries one flawless pearl of
condensed heaven. Whole sects have fallen trying to take it."

A real dragon, and a fierce one (the owner, 2026-11-08: winged, on four legs, the pearl held in a forefoot; "make it even more fierce"). Its design language
is the shell that grows a pearl: nacre and moonlight, worn by a predator. A deep-chested, heavily muscled body on four strong legs with big hooked claws; a
thick neck in an S, thrusting a long wedge of a head forward and low; two great wings raised behind it, a hooked claw at each wrist. The head is all
angles: heavy brow ridges sloping down to the snout in a scowl over narrow glaring eyes, hard cheekbones, a strong jaw, fangs showing over the lip, flared
nostrils. Its horns twist like conch shells, a long pair sweeping back from the crown and a short pair from the jaw. A row of swept-back blade scales runs
from the crown down the neck, the back and the tail. Its wing membranes are ribbed like scallop shells, fanning from the wrist, their trailing edges cut in
deep scallops between the finger tips. Pearl-white nacre with a rainbow sheen, ivory belly plates, moon-silver horns, claws, teeth and wing-fingers;
sapphire eyes going to silver round a slit pupil. It stands on three legs and holds the flawless pearl to its chest in its right forefoot, the cupped hand
curled round it, the claws up its sides.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/celestial_pearl_dragon.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, feet on z = 0. +X is its left. The maps go to assets/pets/CelestialEgg/.

What touches what: body, neck, head, legs, feet, the pearl hand and the tail are one fused skin; the eyes sit in their sockets under their lids; the horns,
the blade scales, the teeth and the claws are their own pieces set into the skin; each wing (its arm, its fingers and its membrane) is set into the back;
the pearl lies in the right hand, the fingers and claws just clear of it.
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
PET = "CelestialPearlDragon"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- the frame of it ----------
# the spine from the rump to the withers; the body hangs below it, deepest at the chest
SPINE = [V(0, 0.31, 0.40), V(0, 0.22, 0.435), V(0, 0.10, 0.445), V(0, -0.02, 0.445), V(0, -0.14, 0.465), V(0, -0.24, 0.485)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.078), (0.15, 0.114), (0.38, 0.098), (0.62, 0.114), (0.82, 0.134), (1, 0.118))     # half-widths, rump to withers
BODY_H = ((0, 0.082), (0.15, 0.108), (0.38, 0.1), (0.62, 0.122), (0.82, 0.148), (1, 0.128))       # half-heights
BODY_DROP = ((0, 0.0), (0.15, 0.012), (0.38, 0.02), (0.62, 0.034), (0.82, 0.05), (1, 0.04))       # the loft's centre below the spine: the chest's keel
# the neck rises in an S and thrusts the head forward and a little low: poised
NECK = catmull([V(0, -0.24, 0.48), V(0, -0.33, 0.57), V(0, -0.395, 0.665), V(0, -0.43, 0.745), V(0, -0.47, 0.795), V(0, -0.525, 0.818)], 10)
NECK_R = ((0, 0.118), (0.3, 0.096), (0.65, 0.078), (1, 0.066))
HEAD = V(0, -0.545, 0.832)                 # the cranium
HEAD_R = (0.066, 0.078, 0.056)
SNOUT = [V(0, -0.585, 0.826), V(0, -0.69, 0.802), V(0, -0.782, 0.778)]
SNOUT_R = ((0, 0.05), (0.55, 0.038), (1, 0.025))
JAW = [V(0, -0.53, 0.785), V(0, -0.64, 0.77), V(0, -0.752, 0.755)]
JAW_R = ((0, 0.042), (0.55, 0.031), (1, 0.022))
TAIL = catmull([V(0, 0.3, 0.405), V(0, 0.42, 0.365), V(0, 0.55, 0.29), V(0.025, 0.67, 0.205), V(0.09, 0.77, 0.135), V(0.19, 0.825, 0.085),
                V(0.29, 0.815, 0.055), V(0.355, 0.75, 0.042)], 10)
TAIL_PROFILE = ((0, 0.082), (0.2, 0.068), (0.5, 0.045), (0.8, 0.026), (0.95, 0.015), (1, 0.01))
# the legs (its left side; mirrored for the right): joint centres from the shoulder or hip down to the toes, and their radii
FORE = [V(0.1, -0.2, 0.405), V(0.118, -0.15, 0.255), V(0.104, -0.205, 0.098), V(0.1, -0.224, 0.044), V(0.1, -0.252, 0.03)]
FORE_R = [0.072, 0.054, 0.043, 0.04, 0.036]
HIND = [V(0.104, 0.2, 0.39), V(0.128, 0.1, 0.25), V(0.114, 0.245, 0.128), V(0.108, 0.208, 0.044), V(0.108, 0.18, 0.03)]
HIND_R = [0.096, 0.062, 0.043, 0.04, 0.036]
# the right foreleg holds the pearl to its chest: the upper arm down and back, the forearm forward and up to a hand cupped under it
PEARL = V(-0.032, -0.445, 0.4)
PEARL_R = 0.048
ARM = [V(-0.1, -0.2, 0.405), V(-0.124, -0.17, 0.25), V(-0.078, -0.345, 0.262), V(-0.044, -0.418, 0.33)]
ARM_R = [0.072, 0.054, 0.043, 0.036]
EYE_R = 0.024
EYE_C = V(0.05, -0.616, 0.842)
EYE_AXIS = V(0.6, -0.78, 0.08).normalized()
LID_UP, LID_LOW = (13.0, 120.0, 0.0026), (-24.0, -128.0, 0.0022)     # narrow: the upper lid low over the eye, the lower one high
LID_TILT = 18.0                     # the opening's outer end raised, its inner end low by the snout: a glare
BLINK_U, BLINK_L = 40.0, 20.0
IRIS, PUPIL_W, PUPIL_H = 0.92, 0.16, 0.8     # on the eye's face (its front is 1): a vertical slit
# the wing (its left): the arm bent back at the elbow and up to the wrist, then four fingers fanning out
WING_ROOT = V(0.075, -0.12, 0.56)
WING_ELBOW = V(0.25, 0.04, 0.665)
WING_WRIST = V(0.38, -0.05, 0.97)
FINGERS = [V(0.56, 0.04, 1.14), V(0.7, 0.2, 0.98), V(0.68, 0.36, 0.76), V(0.48, 0.44, 0.58)]     # tips, leading to last
WING_BODY = V(0.078, 0.2, 0.475)         # where the membrane's trailing edge meets the flank
SCALLOP = 0.095                          # how deep the trailing edge cuts in between two tips
HORN = [V(0.042, -0.52, 0.872), V(0.064, -0.45, 0.918), V(0.086, -0.36, 0.944), V(0.098, -0.27, 0.95), V(0.094, -0.2, 0.978)]
HORN_R = ((0, 0.024), (0.35, 0.018), (0.75, 0.01), (1, 0.0045))
JAW_HORN = [V(0.062, -0.53, 0.8), V(0.094, -0.47, 0.79), V(0.12, -0.415, 0.8), V(0.13, -0.38, 0.818)]
JAW_HORN_R = ((0, 0.014), (0.5, 0.009), (1, 0.0035))


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


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


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def loft(m, path, w_fn, h_fn, drop_fn=None, nt=48, caps=True):
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
    if caps:
        m.bm.faces.new(rings[0])
        m.bm.faces.new(list(reversed(rings[-1])))


def twisted_tube(m, path, r_fn, side, lobes, twist, depth, sides=36):
    """A tube whose ridges spiral round it like a conch's whorl, smoothing out at both ends."""
    fr = path_frames(path)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, s, up = fr[i]
        r = r_fn(f)
        ring = []
        for k in range(sides):
            th = TAU * k / sides
            rr = r * (1 + depth * math.cos(lobes * th + side * twist * f) * smooth(0.0, 0.15, f) * (1 - smooth(0.85, 1.0, f)))
            ring.append(m.bm.verts.new(p + s * (rr * math.cos(th)) + up * (rr * math.sin(th))))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


# ---------- per-vertex tags ----------
# Blender's sphere primitive reuses the slots of vertices it frees, so the vertices of one piece are not in the order they were made: anything a vertex
# must carry (which blade, which finger) is written on it as a layer when it is made, and read back from the mesh's attribute of that name.
def make_tags(bm, ints=(), floats=()):
    """The layers, made before any geometry: adding a layer later frees every vertex reference held."""
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new(bm, before, **values):
    """Every vertex of bm not in `before` gets these layer values (the layers made by make_tags)."""
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


# ---------- feet ----------
def foot_toes(knots, side):
    """Per toe: its path from inside the foot to the claw's root. Three toes forward, spread, and one behind."""
    ball = mir(knots[3], side)
    out = []
    for a, reach in ((-0.46, 0.07), (0.0, 0.08), (0.46, 0.07)):
        d = V(math.sin(a) * side * 0.85, -math.cos(a), 0)
        root = ball + V(0, -0.006, -0.004)
        out.append([root, root + d * (reach * 0.5) + V(0, 0, 0.004), root + d * reach + V(0, 0, -0.012)])
    back = ball + V(side * 0.014, 0.02, -0.002)
    out.append([back, back + V(side * 0.007, 0.03, -0.006), back + V(side * 0.009, 0.046, -0.013)])
    return out


def toe_radius(f):
    return 0.02 * (1 - 0.35 * f)


def claw_path(toe):
    """A big hooked claw from the toe's end, down to the ground, its tip rounded off, never a point."""
    a, b = toe[-2], toe[-1]
    d = (b - a).normalized()
    d = (d - V(0, 0, d.z)).normalized()
    return [b - d * 0.01, b + d * 0.014 + V(0, 0, 0.002), b + d * 0.032 + V(0, 0, -0.005), b + d * 0.042 + V(0, 0, -0.016)]


def claw_radius(f):
    return 0.012 * (1 - f) ** 0.85 + 0.0018


# ---------- the pearl hand ----------
def hand_dirs():
    """The pearl hand's three fingers and its thumb: each a direction round the pearl, level, from its centre."""
    out = [V(math.sin(a), -math.cos(a), 0.0) for a in (-0.7, 0.0, 0.7)]
    out.append(V(1, 0.35, 0).normalized())          # the thumb, on the inner side, toward its chest's middle
    return out


def hand_fingers():
    """A hand cupped under the pearl: each finger from the palm under it, up the pearl's side to just below its middle; just clear of it."""
    up = V(0, 0, 1)
    reach = PEARL_R + 0.016
    out = []
    for k, d in enumerate(hand_dirs()):
        top = 0.12 if k < 3 else -0.1
        out.append([PEARL + (d * math.cos(t) + up * math.sin(t)) * reach for t in np.linspace(-1.5, top, 7)])
    return out


def finger_radius(f):
    return 0.0145 * (1 - 0.25 * f)


def hand_claw(finger):
    """The talon at a finger's end: born inside the fingertip, curling on over the top of the pearl toward its crown, hugging it, clear of it."""
    up = V(0, 0, 1)
    end = finger[-1]
    d = (end - PEARL - up * (end - PEARL).dot(up)).normalized()
    t0 = math.asin(max(-1.0, min(1.0, (end - PEARL).dot(up) / (end - PEARL).length)))
    return [PEARL + (d * math.cos(t) + up * math.sin(t)) * (PEARL_R + 0.0155 - 0.0055 * k / 5) for k, t in enumerate(np.linspace(t0 - 0.16, t0 + 0.72, 6))]


def hand_claw_radius(f):
    return 0.0085 * (1 - f) ** 0.9 + 0.0016


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.01, -0.005), (0.076, 0.07, 0.08))                       # the rump
    core.ball(V(0, -0.34, 0.47), (0.085, 0.065, 0.11))                                     # the breast, under the neck
    core.ball(V(0, -0.36, 0.63), (0.07, 0.07, 0.07))                                       # the neck's base, a heavy column of muscle
    for side in (1, -1):
        core.ball(V(side * 0.095, -0.2, 0.425), (0.078, 0.095, 0.1))                       # the shoulder
        core.ball(V(side * 0.094, 0.2, 0.405), (0.088, 0.115, 0.106))                      # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.008, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    # the head and the limbs, at a finer grain so their angles hold
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 40, 28)
    fine.tube(catmull(SNOUT, 6), lambda f: prof(SNOUT_R, f), sides=32, flat=1.22)
    fine.ball(SNOUT[-1] + V(0, -0.003, -0.002), (0.029, 0.017, 0.02))                       # the end of the snout, hard
    fine.tube(catmull(JAW, 6), lambda f: prof(JAW_R, f), sides=28, flat=1.2)
    fine.ball(JAW[-1] + V(0, -0.002, -0.002), (0.022, 0.016, 0.018))                       # the chin
    fine.tube(catmull([V(0, -0.6, 0.86), V(0, -0.7, 0.828), V(0, -0.77, 0.802)], 6), lambda f: 0.012 * (1 - 0.4 * f), sides=16, flat=1.8)     # the bridge of the nose
    for side in (1, -1):
        # the brow: a hard ridge over the eye, sloping down and in toward the snout: the scowl
        fine.tube(catmull([V(side * 0.062, -0.555, 0.872), V(side * 0.056, -0.605, 0.866), V(side * 0.036, -0.66, 0.846)], 6),
                  lambda f: (0.017 * (1 - 0.4 * f)) * math.sin(math.pi * (0.12 + 0.76 * f)) ** 0.6 + 0.002, sides=16, flat=1.3)
        fine.tube(catmull([V(side * 0.052, -0.65, 0.816), V(side * 0.064, -0.59, 0.81), V(side * 0.07, -0.53, 0.806)], 6),
                  lambda f: (0.012 + 0.006 * f) * math.sin(math.pi * (0.1 + 0.8 * f)) ** 0.6 + 0.002, sides=16)      # the cheekbone
        fine.ball(V(side * 0.056, -0.525, 0.79), (0.04, 0.046, 0.04))                     # the jaw's muscle
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
    for side, knots, radii in ((1, FORE, FORE_R), (1, HIND, HIND_R), (-1, HIND, HIND_R)):
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.92)
        fine.ball(mir(knots[3], side) + V(0, -0.006, -0.009), (0.044, 0.052, 0.026), 24, 14)       # the foot
        for toe in foot_toes(knots, side):
            fine.tube(catmull(toe, 4), toe_radius, sides=12)
    fine.tube(catmull(ARM, 8), lambda f: leg_radius(ARM_R, f), sides=24, flat=0.92)
    loft(fine, TAIL, lambda f: prof(TAIL_PROFILE, f), lambda f: prof(TAIL_PROFILE, f) * 0.92)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0035, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- the pearl hand: its own piece, so its fingers keep their shape in the game mesh ----------
PALM_C, PALM_R = PEARL + V(0.0, 0.008, -PEARL_R - 0.018), (0.042, 0.044, 0.02)


def build_hand(name, coll):
    """The palm cupped under the pearl, three fingers and a thumb up its sides, a knuckle at each joint, and a stub of wrist that plugs into the arm."""
    m = Mesh()
    m.ball(PALM_C, PALM_R, 24, 14)
    for finger in hand_fingers():
        m.tube(catmull(finger, 3), finger_radius, sides=12)
        for j, r in ((2, 0.0172), (4, 0.0152)):                   # the knuckles: a clawed hand, not a cage
            m.ball(finger[j] + (finger[j] - PEARL).normalized() * 0.003, (r, r, r), 16, 10)
    m.tube([ARM[2].lerp(ARM[3], 0.55), ARM[3], PALM_C.lerp(ARM[3], 0.3)], lambda f: 0.034 - 0.006 * f, sides=20)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0022, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 4})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def paint_hand(o):
    """The same nacre as the skin, in fine scales; the palm ivory."""
    P = verts(o)
    Nn = normals(o)
    d1, d2, own = cells(P, 140.0, 13)
    edge = 1 - smooth(0.0, 0.1, d2 - d1)
    col = nacre(P, Nn)
    col = mix(col, NACRE_DEEP, edge * 0.35)
    palm = (1 - smooth(0.9, 1.3, np.linalg.norm((P - np.array(tuple(PALM_C))) / np.array(PALM_R), axis=1))) * smooth(0.1, -0.5, Nn[:, 2])
    col = mix(col, IVORY, palm * 0.8)
    paint(o, col, 0.36 + 0.1 * edge, np.zeros(len(P)))


# ---------- the blade scales down its back ----------
def ridge_points():
    """Where the blades stand along the top line, and how big: from the crown down the neck, along the back and most of the tail."""
    out = [(HEAD + V(0, 0.03, 0.05), 0.03)]
    for k in range(8):
        out.append((path_at(NECK, 0.9 - 0.9 * k / 8), 0.04 + 0.012 * k / 8))
    for k in range(8):
        out.append((path_at(BODY_PATH, 1 - k / 8), 0.052 - 0.014 * k / 8))
    for k in range(9):
        out.append((path_at(TAIL, 0.04 + 0.66 * k / 9), 0.038 - 0.024 * k / 9))
    return out


def build_ridge(tree, name, coll, seg=16, rings=14, roots=None):
    """roots: a list that takes each blade's base, in the order of the blades; each vertex carries its blade's number as the "blade" layer."""
    """Blade scales: thin, hooked back like a fin, their bases sunk in the skin, each leaning over the next. Each is a ball reshaped: narrowing toward its
    tip and swept back as it rises, the tip a blunt edge, not a point."""
    m = Mesh()
    make_tags(m.bm, ints=("blade",))
    pts = ridge_points()
    for k, (p, size) in enumerate(pts):
        loc, nrm, _, _ = tree.ray_cast(p + V(0, 0, 0.3), V(0, 0, -1), 0.6)
        if loc is None:
            continue
        nxt = pts[min(k + 1, len(pts) - 1)][0] - pts[max(k - 1, 0)][0]
        back = (nxt - nrm * nxt.dot(nrm)).normalized()
        across = nrm.cross(back).normalized()
        before = set(m.bm.verts)
        made = bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0)["verts"]
        base = loc - nrm * (size * 0.35)
        if roots is not None:
            tag_new(m.bm, before, blade=len(roots))
            roots.append(tuple(loc))
        for v in made:
            x, y, z = v.co
            up = max(0.0, (z + 1) / 2)
            narrow = 1 - 0.72 * up ** 1.4
            a = x * 0.16 * size * narrow
            b = (y * 0.55 * narrow + 0.85 * up ** 2) * size
            h = (z + 1) / 2 * size * 1.25
            v.co = base + across * a + back * b + nrm * h
    return m.finish(name, coll)


# ---------- horns, teeth, claws ----------
HORN_KINDS = ((HORN, HORN_R, 3.4 * math.pi, 0.16, 36, 12), (JAW_HORN, JAW_HORN_R, 2.2 * math.pi, 0.14, 24, 8))


def build_horns(name, coll, scale=1.0):
    """Returns the object and, per vertex, how far along its horn (0 root, 1 tip) and the whorl's value there (1 on a ridge)."""
    m = Mesh()
    f_all, lobe_all = [], []
    for side in (1, -1):
        for knots, radii, twist, depth, sides, per in HORN_KINDS:
            sides = max(8, int(sides * scale))
            path = catmull([mir(p, side) for p in knots], max(3, int(per * scale)))
            twisted_tube(m, path, lambda f, r=radii: prof(r, f), side, 3, twist, depth, sides=sides)
            for i in range(len(path)):
                f = i / (len(path) - 1)
                for k in range(sides):
                    f_all.append(f)
                    lobe_all.append(math.cos(3 * TAU * k / sides + side * twist * f))
    return m.finish(name, coll), np.array(f_all), np.array(lobe_all)


def tooth_list():
    """Fangs over the lower lip: a long fang near the front each side and smaller teeth behind, hanging from inside the upper lip."""
    out = []
    for side in (1, -1):
        for y, length, r in ((-0.74, 0.03, 0.0062), (-0.715, 0.017, 0.0042), (-0.685, 0.02, 0.0046), (-0.655, 0.013, 0.0036), (-0.62, 0.012, 0.0034)):
            t = (y - SNOUT[0].y) / (SNOUT[-1].y - SNOUT[0].y)
            half = prof(SNOUT_R, min(max(t, 0), 1)) * 1.15
            x = side * (half - 0.006)
            z0 = SNOUT[0].z + (SNOUT[-1].z - SNOUT[0].z) * t - prof(SNOUT_R, min(max(t, 0), 1)) * 0.62
            out.append(([V(x, y, z0 + 0.008), V(x + side * 0.003, y, z0 - length * 0.5), V(x + side * 0.002, y - 0.003, z0 - length)], r))
    return out


def build_teeth(name, coll, sides=10, per=4):
    m = Mesh()
    f_all = []
    for pts, r in tooth_list():
        path = catmull(pts, per)
        m.tube(path, lambda f, r=r: r * (1 - f) ** 0.8 + 0.0011, sides=sides)
        f_all += [i / (len(path) - 1) for i in range(len(path)) for _ in range(sides)]
    return m.finish(name, coll), np.array(f_all)


def claw_list():
    """Every claw: its path, its radius along it, and the bone that carries it."""
    out = []
    for side, knots, bone in ((1, FORE, "PawFL"), (1, HIND, "PawBL"), (-1, HIND, "PawBR")):
        for toe in foot_toes(knots, side):
            out.append((claw_path(toe), claw_radius, bone))
    for finger in hand_fingers():
        out.append((hand_claw(finger), hand_claw_radius, "HandR"))
    return out


def build_claws(name, coll, sides=12, per=4):
    m = Mesh()
    f_all, owner = [], []
    for path, rfn, bone in claw_list():
        pts = catmull(path, per)
        m.tube(pts, rfn, sides=sides)
        f_all += [i / (len(pts) - 1) for i in range(len(pts)) for _ in range(sides)]
        owner += [bone] * (len(pts) * sides)
    return m.finish(name, coll), np.array(f_all), owner


# ---------- the wings ----------
def wing_frame(side):
    return mir(WING_ROOT, side), mir(WING_ELBOW, side), mir(WING_WRIST, side), [mir(p, side) for p in FINGERS], mir(WING_BODY, side)


def finger_curve(wrist, tip, side, bow=0.035, per=10):
    """A wing-finger, bowed a little against the wind, from the wrist to its tip."""
    mid = wrist.lerp(tip, 0.5)
    d = (tip - wrist).normalized()
    out = d.cross(V(0, 0, 1)).normalized() * side
    return catmull([wrist, mid + out * bow * 0.3 + V(0, 0, bow * 0.4), tip], per)


def arm_curve(side, per=10):
    root, elbow, wrist, _, _ = wing_frame(side)
    return catmull([root, elbow, wrist], per)


def scallop_edge(a, b, toward, depth):
    """The trailing edge between two tips, cut in toward `toward`, sharpest near the tips."""
    pts = []
    for t in np.linspace(0, 1, 13):
        p = a.lerp(b, t)
        pull = (toward - p).normalized() * depth * math.sin(math.pi * t) ** 0.7
        pts.append(p + pull)
    return pts


def sample(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def coons(c0, c1, d0, d1):
    """A surface from four edges: c0(u) and c1(u) along u at v = 0 and 1, d0(v) and d1(v) along v at u = 0 and 1."""
    P00, P10, P01, P11 = c0(0), c0(1), c1(0), c1(1)

    def point(u, v):
        return ((1 - v) * c0(u) + v * c1(u) + (1 - u) * d0(v) + u * d1(v)
                - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10 + (1 - u) * v * P01 + u * v * P11))
    return point


def membrane_point(side):
    """The membrane as one sheet in two panels. The hand (u < 0.6): between the four fingers, from a small arc round the wrist out to the scalloped
    edge. The arm (after it): from the arm down to the flank, out to the last finger. v runs from the wrist (or the arm) out to the trailing edge."""
    root, elbow, wrist, tips, body = wing_frame(side)
    fingers = [finger_curve(wrist, t, side) for t in tips]
    edges = [scallop_edge(tips[k], tips[k + 1], wrist, SCALLOP) for k in range(3)]

    def hand(u, v):
        k = min(int(u), 2)
        t = u - k
        a = sample(fingers[k], 0.05 + 0.95 * v)
        b = sample(fingers[k + 1], 0.05 + 0.95 * v)
        straight = a.lerp(b, t)
        edge = sample(edges[k], t)
        chord = tips[k].lerp(tips[k + 1], t)
        return straight + (edge - chord) * v ** 2.2
    arm = arm_curve(side)
    trailing = scallop_edge(tips[3], body, wrist.lerp(root, 0.5), SCALLOP * 1.3)
    flank = [root.lerp(body, t) + V(-side * 0.02 * math.sin(math.pi * t), 0, 0) for t in np.linspace(0, 1, 11)]
    last = fingers[3]
    arm_panel = coons(lambda u: sample(list(reversed(arm)), u), lambda u: sample(trailing, 1 - u), lambda v: sample(last, 0.05 + 0.95 * v), lambda v: sample(flank, v))
    split = 0.6

    def point(u, v):
        if u <= split:
            return tuple(hand(3 * u / split, v))
        return tuple(arm_panel((u - split) / (1 - split), v))
    return point


def membrane_thick(u, v):
    return 0.0042


def build_membranes(name, coll, nu=90, nv=40):
    m = Mesh()
    for side in (1, -1):
        m.sheet(membrane_point(side), membrane_thick, nu, nv)
    return m.finish(name, coll)


def wing_claw(side):
    """The hooked claw on the wing's wrist, pointing forward."""
    root, elbow, wrist, tips, body = wing_frame(side)
    fwd = (wrist - elbow).normalized()
    return [wrist + fwd * 0.012, wrist + fwd * 0.03 + V(side * 0.006, -0.012, 0.004), wrist + fwd * 0.05 + V(side * 0.01, -0.03, -0.006),
            wrist + fwd * 0.058 + V(side * 0.01, -0.04, -0.022)]


def build_wing_bones(name, coll, sides=16, scale=1.0):
    """The wings' arms and fingers: the arm skin-thick from its root in the back, the fingers fine, each with a knuckle at the wrist, a hooked claw at it.
    Each vertex carries its part ("kind": 0 arm, 1 knuckle, 2 finger, 3 claw), its finger ("finger", -1 if none) and how far along its part ("along")."""
    m = Mesh()
    bm = m.bm
    make_tags(bm, ints=("kind", "finger"), floats=("along",))

    def tube(path, rfn, n_sides, kind, which=-1):
        before = set(bm.verts)
        m.tube(path, rfn, sides=n_sides)
        tag_new(bm, before, kind=kind, finger=which)
        layer = bm.verts.layers.float["along"]
        new = [v for v in bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[layer] = float(ff)
    per = max(3, int(10 * scale))
    for side in (1, -1):
        root, elbow, wrist, tips, body = wing_frame(side)
        tube(arm_curve(side, per), lambda f: 0.032 * (1 - 0.42 * f), max(10, int((sides + 8) * scale)), 0)
        before = set(bm.verts)
        m.ball(wrist, (0.02, 0.022, 0.02), max(8, int(20 * scale)), max(5, int(12 * scale)))          # the wrist's knuckle, where the fingers spring from
        tag_new(bm, before, kind=1, finger=-1, along=0.0)
        for j, t in enumerate(tips):
            tube(finger_curve(wrist, t, side, per=per), lambda f: 0.012 * (1 - 0.55 * f) + 0.0022, max(6, int(sides * scale)), 2, j)
        tube(catmull(wing_claw(side), max(2, int(4 * scale))), lambda f: 0.01 * (1 - f) ** 0.85 + 0.0018, max(6, int(12 * scale)), 3)
    o = m.finish(name, coll)
    return o


def build_pearl(name, coll, seg=64, rings=40):
    m = Mesh()
    m.ball(PEARL, (PEARL_R,) * 3, seg, rings)
    return m.finish(name, coll)


# ---------- colours: nacre and moonlight ----------
NACRE, NACRE_DEEP = rgb(234, 231, 230), rgb(118, 126, 164)
PINK, AQUA, LILAC, GOLD = rgb(248, 204, 222), rgb(190, 236, 238), rgb(212, 200, 248), rgb(246, 228, 188)
IVORY, IVORY_LINE = rgb(246, 238, 218), rgb(196, 186, 168)
SILVER, PEWTER, SILVER_TIP = rgb(196, 204, 224), rgb(72, 80, 108), rgb(238, 242, 252)
TOOTH, TOOTH_ROOT = rgb(242, 238, 226), rgb(190, 184, 170)
MEMB, MEMB_DEEP = rgb(234, 228, 242), rgb(186, 178, 214)
KOHL, MOUTH = rgb(44, 46, 70), rgb(22, 18, 30)
SAPPHIRE, SAPPHIRE_DEEP, SILVER_EYE = rgb(40, 110, 236), rgb(14, 30, 100), rgb(214, 238, 255)


def iridescence(phase):
    """Nacre's play of colour: pink, gold, aqua, lilac round a cycle."""
    ph = np.mod(phase, 1.0)
    cols = [PINK, GOLD, AQUA, LILAC, PINK]
    out = np.zeros((len(ph), 3))
    for k in range(4):
        a, b = k / 4, (k + 1) / 4
        w = ((ph >= a) & (ph < b)).astype(float)
        t = ((ph - a) / 0.25)[:, None]
        out += w[:, None] * (cols[k] * (1 - t) + cols[k + 1] * t)
    return out


def cells(P, f, seed=0):
    """Scale cells: distance to the nearest and second-nearest cell point, and the nearest cell's own random number."""
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


def nacre(P, Nn, seed=0, sheen=0.34):
    """Pearl-white with a play of colour drifting over it: the hue moves with the way a surface faces and with a slow field through the body."""
    phase = 0.8 * (Nn @ np.array((0.3, -0.5, 0.8))) + 1.2 * fbm(P, 2.2, 3, seed + 5)
    return mix(np.broadcast_to(NACRE, (len(P), 3)), iridescence(phase), sheen)


DORSAL = [HEAD + V(0, 0.02, 0)] + list(reversed(NECK)) + list(reversed(BODY_PATH))[1:] + TAIL[1:]      # the crown, down the neck, the back and the tail


def scale_rows(P):
    """A dragon's overlapping scales in rows along the line of its body: each a rounded tile with its free edge toward the tail, lapping over the next
    row. Per point: the seam's darkness, the tile's lit rim, and the tile's own random number."""
    f, d = nearest_on(DORSAL, P)
    lengths = np.array([(DORSAL[i + 1] - DORSAL[i]).length for i in range(len(DORSAL) - 1)])
    s = f * lengths.sum()
    seg = np.clip((f * (len(DORSAL) - 1)).astype(int), 0, len(DORSAL) - 2)
    fr = path_frames(DORSAL)
    side = np.array([tuple(fr[i][1]) for i in seg])
    up = np.array([tuple(fr[i][2]) for i in seg])
    rel = P - np.array([tuple(DORSAL[i]) for i in seg])
    theta = np.arctan2((rel * side).sum(1), (rel * up).sum(1))       # 0 on the top line, growing round each side
    across = theta * np.maximum(d, 0.02)
    size = np.clip(d * 0.32, 0.009, 0.026)
    row = np.floor(s / (size * 0.82))
    t = s / (size * 0.82) - row
    u = across / size + 0.5 * (row % 2)
    x = u - np.floor(u) - 0.5
    rim = 0.45 + 0.55 * np.sqrt(np.clip(1 - (2 * x) ** 2, 0, 1))      # the tile's rounded free edge, toward the tail
    seam = (1 - smooth(0.0, 0.07, np.abs(t - rim))) + (1 - smooth(0.0, 0.05, 0.5 - np.abs(x))) * (t < rim) * 0.6
    lit = smooth(rim - 0.45, rim - 0.04, t) * (t < rim)
    own = hash01(row.astype(np.int64), np.floor(u).astype(np.int64), 0, 31)
    return np.clip(seam, 0, 1), lit, own


VENTRAL = list(reversed(NECK)) + list(reversed(BODY_PATH))[1:] + TAIL[1:]     # head end of the neck, down the throat, under the body, under the tail


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # scale cells: broad plates on the back and flanks, finer on the head, the legs and the hand
    head = 1 - smooth(0.1, 0.18, np.linalg.norm(P - np.array(tuple(HEAD + V(0, -0.08, 0))), axis=1))
    limb = smooth(0.28, 0.2, z) * (1 - head)
    small = cells(P, 74.0, 7)
    fine_w = np.clip(head + limb, 0, 1)
    rows_edge, rows_dome, rows_own = scale_rows(P)
    edge = rows_edge * (1 - fine_w) + (1 - smooth(0.0, 0.09, small[1] - small[0])) * fine_w * 0.45      # the seam between two scales
    dome = rows_dome * (1 - fine_w) + (1 - smooth(0.0, 0.6, small[0])) * fine_w                # each scale's raised, lit part
    own = rows_own * (1 - fine_w) + small[2] * fine_w
    col = nacre(P, Nn)
    col = mix(col, iridescence(0.35 * own + 0.9 * fbm(P, 2.5, 2, 3)), 0.12 * (1 - edge))      # each scale a little its own tint
    col = mix(col, NACRE_DEEP, edge * 0.7)
    col = mix(col, NACRE * 1.05, dome * 0.3)
    col = mix(col, NACRE_DEEP * 1.2, smooth(-0.1, -0.7, Nn[:, 2]) * 0.35)               # cooler where it faces down
    # the belly plates: ivory bands across the throat, the belly and under the tail
    s_frac, _ = nearest_on(VENTRAL, P)
    total = sum((VENTRAL[i + 1] - VENTRAL[i]).length for i in range(len(VENTRAL) - 1))
    s_len = s_frac * total
    # "down" at each point: straight down, square to the line the plates run along there
    seg = np.clip(s_frac * (len(VENTRAL) - 1), 0, len(VENTRAL) - 2).astype(int)
    tangents = np.array([tuple((VENTRAL[i + 1] - VENTRAL[i]).normalized()) for i in range(len(VENTRAL) - 1)])
    tan = tangents[seg]
    below = np.array((0, 0, -1.0)) + tan * tan[:, 2:3]
    below = below / np.maximum(np.linalg.norm(below, axis=1)[:, None], 1e-6)
    down = (Nn * below).sum(1)
    on_neck = s_len < sum((NECK[i + 1] - NECK[i]).length for i in range(len(NECK) - 1))
    face_front = (Nn * np.array((0, -0.75, -0.66))).sum(1)
    belly = np.where(on_neck, smooth(0.35, 0.6, face_front), smooth(0.38, 0.62, down)) * (1 - head) * smooth(0.06, 0.03, np.abs(x) - 0.04 * (1 - limb))
    belly *= 1 - limb
    band = np.mod(s_len / 0.018, 1.0)
    seam = 1 - smooth(0.0, 0.12, np.minimum(band, 1 - band))
    plates = mix(np.broadcast_to(IVORY, (len(P), 3)), IVORY_LINE, seam * 0.8)
    plates = mix(plates, iridescence(0.25 + 0.3 * band), 0.12)
    col = mix(col, plates, belly)
    # the face: a dark smoky rim round each eye, the line of the mouth, the nostrils
    kohl = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(EYE_C, side)))
        r = np.linalg.norm(P - c, axis=1)
        kohl = np.maximum(kohl, smooth(EYE_R * 1.55, EYE_R * 1.1, r))
    kohl *= smooth(EYE_C.z + 0.022, EYE_C.z + 0.008, z) * smooth(0.02, 0.035, np.abs(x))      # round the eye only: never over the brow or across the top
    col = mix(col, KOHL, kohl * 0.9)
    lip_z = np.interp(-y, [0.53, 0.66, 0.79], [0.786, 0.775, 0.762])
    lip = (1 - smooth(0.0014, 0.0034, np.abs(z - lip_z))) * (y < -0.54) * (np.abs(x) > 0.004)
    nost = np.zeros(len(P))
    for side in (1, -1):
        # a slit swept back and out along the top of the snout's end: flared, angry
        a = np.array((side * 0.012, -0.786, 0.79))
        b = np.array((side * 0.024, -0.772, 0.794))
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        nost = np.maximum(nost, (1 - smooth(0.0016, 0.0034, d)) * (y < -0.76))
    mouth = np.clip(lip + nost, 0, 1)
    col = mix(col, MOUTH, mouth * 0.92)
    relief = 0.00045 * dome - 0.0007 * edge - 0.0016 * mouth - 0.0004 * seam * belly
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.36 - 0.12 * dome * (1 - belly) + 0.12 * edge + 0.3 * mouth, np.zeros(len(P)))


def paint_ridge(o, tree):
    """Nacre blades, silver toward their edges and tips."""
    P = verts(o)
    Nn = normals(o)
    lift = np.array([(Vector(p) - tree.find_nearest(Vector(p))[0]).length for p in P])
    col = mix(nacre(P, Nn, 3, 0.5), SILVER_TIP, smooth(0.008, 0.03, lift) * 0.7)
    paint(o, col, np.full(len(P), 0.28), np.zeros(len(P)))


def paint_horns(o, f, lobe):
    """Moon-silver: the whorl's ridges bright, its grooves dark pewter, darker at the root, pale at the tips."""
    col = mix(np.broadcast_to(PEWTER, (len(f), 3)), SILVER, smooth(-0.6, 0.6, lobe))
    col = mix(col, PEWTER * 0.8, smooth(0.25, 0.0, f) * 0.6)
    col = mix(col, SILVER_TIP, smooth(0.65, 1.0, f) * 0.8)
    paint(o, col, 0.32 - 0.12 * smooth(-0.2, 0.8, lobe), np.full(len(f), 0.6))


def paint_claws(o, f):
    col = mix(np.broadcast_to(PEWTER, (len(f), 3)), SILVER_TIP, smooth(0.15, 0.9, f))
    paint(o, col, 0.3 - 0.12 * f, np.full(len(f), 0.55))


def paint_teeth(o, f):
    col = mix(np.broadcast_to(TOOTH_ROOT, (len(f), 3)), TOOTH, smooth(0.1, 0.5, f))
    paint(o, col, np.full(len(f), 0.3), np.zeros(len(f)))


def sheet_uv(nu, nv, sheets):
    """The u, v of every vertex of `sheets` closed sheets made by Mesh.sheet, in order."""
    uu, vv = [], []
    for _ in range(sheets):
        for i in range(nu + 1):
            for j in range(nv + 1):
                uu += [i / nu, i / nu]
                vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def membrane_pattern(uu, vv):
    """A scallop shell's pattern: ribs fanning out from the wrist (across u), growth bands round it (along v)."""
    hand = uu <= 0.6
    rib_u = np.where(hand, uu / 0.6 * 3 * 9, (uu - 0.6) / 0.4 * 8)
    rib = 0.5 + 0.5 * np.cos(rib_u * TAU)
    band = (0.5 + 0.5 * np.cos((vv + 0.015 * np.sin(rib_u * TAU * 0.5)) * TAU * 5.0)) * smooth(0.45, 0.9, vv)
    return rib, band


def paint_membranes(o, nu, nv):
    P = verts(o)
    Nn = normals(o)
    uu, vv = sheet_uv(nu, nv, 2)
    rib, band = membrane_pattern(uu, vv)
    col = mix(np.broadcast_to(MEMB_DEEP, (len(P), 3)), MEMB, smooth(0.05, 0.7, vv))
    col = mix(col, iridescence(0.15 + 0.9 * vv), 0.3)
    col = mix(col, col * 1.1, smooth(0.55, 1.0, rib) * 0.7)
    col = mix(col, MEMB_DEEP * 0.8, smooth(0.35, 0.0, rib) * 0.45)
    col = mix(col, NACRE_DEEP, smooth(0.8, 1.0, band) * 0.12)
    col = mix(col, SILVER_TIP, smooth(0.95, 1.0, vv) * 0.8)                 # a fine silver rim along the trailing edge
    relief = 0.0007 * (rib - 0.5) * smooth(0.04, 0.2, vv) * (1 - smooth(0.93, 1.0, vv))
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.4 - 0.1 * rib, np.zeros(len(P)))


def paint_wing_bones(o, kind, f):
    P = verts(o)
    Nn = normals(o)
    col = nacre(P, Nn, 11)
    silver = mix(np.broadcast_to(SILVER, (len(P), 3)), SILVER_TIP, smooth(0.5, 1.0, f))
    claw = mix(np.broadcast_to(PEWTER, (len(P), 3)), SILVER_TIP, smooth(0.15, 0.9, f))
    col = np.where((kind == 2)[:, None], silver, col)
    col = np.where((kind == 3)[:, None], claw, col)
    col = np.where((kind == 1)[:, None], mix(col, SILVER, 0.5), col)
    metal = np.where(kind >= 2, 0.55, 0.0)
    paint(o, col, np.where(kind >= 2, 0.3, 0.36), metal)


def eye_paint(o, fr):
    """Sapphire going to silver round a vertical slit, fine fibres, a dark rim."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(12, 14, 26), (len(px), 3)).copy()
    iris = mix(SILVER_EYE, SAPPHIRE, smooth(0.18, 0.62, r))
    iris = mix(iris, SAPPHIRE_DEEP, smooth(0.62, IRIS, r))
    iris = mix(iris, iris * 0.7, smooth(-0.2, 0.8, py / IRIS) * 0.45)          # shadowed under the upper lid
    azi = np.arctan2(py, px)
    iris = iris * (0.86 + 0.14 * np.sin(azi * 38 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    slit = np.where(front, (px / PUPIL_W) ** 2 + (py / PUPIL_H) ** 2, 9.0)
    col = mix(col, rgb(4, 4, 8), 1 - smooth(0.8, 1.1, slit))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


# ---------- the whole, high-detail ----------
MEMB_NU, MEMB_NV = 90, 40


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
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, KOHL * 1.6, KOHL * 0.3)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, KOHL * 1.8, KOHL * 0.4, lower_share=0.9)
    pieces["Hand"] = build_hand(N + "HandHi", HI)
    pieces["Ridge"] = build_ridge(data["tree"], N + "RidgeHi", HI)
    pieces["Horns"], data["horn_f"], data["horn_lobe"] = build_horns(N + "HornsHi", HI)
    pieces["Teeth"], data["tooth_f"] = build_teeth(N + "TeethHi", HI)
    pieces["Claws"], data["claw_f"], _ = build_claws(N + "ClawsHi", HI)
    pieces["Membranes"] = build_membranes(N + "MembranesHi", HI, MEMB_NU, MEMB_NV)
    pieces["WingBones"] = build_wing_bones(N + "WingBonesHi", HI)
    glows = {"Pearl": build_pearl(N + "Pearl_Glow_fff4e2", HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-24, 22, 0.0042, 12), (22, -18, 0.002, 8)))}
    if not clay:
        paint_skin(skin)
        paint_hand(pieces["Hand"])
        paint_ridge(pieces["Ridge"], data["tree"])
        paint_horns(pieces["Horns"], data["horn_f"], data["horn_lobe"])
        paint_teeth(pieces["Teeth"], data["tooth_f"])
        paint_claws(pieces["Claws"], data["claw_f"])
        paint_membranes(pieces["Membranes"], MEMB_NU, MEMB_NV)
        wb = pieces["WingBones"]
        paint_wing_bones(wb, read_tag(wb, "kind"), read_tag(wb, "along"))
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.05, 0.55)
FACE_AT = (0, -0.64, 0.82)
EXTRA = [(0, -1, 0.05, 0.9, FACE_AT), (0.62, -0.75, 0.2, 0.9, FACE_AT), (1, -0.12, 0.08, 0.9, FACE_AT), (0.3, -0.9, 0.2, 0.4, tuple(EYE_C)),
         (-0.5, -0.8, 0.2, 0.9, tuple(PEARL)), (0.7, 0.3, 0.5, 2.6, (0.35, 0.15, 0.8))]


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
        mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=4.2, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 4200
LOW_MEMB = (30, 9)
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Horns": 1.3, "Teeth": 1.5, "Claws": 1.3, "Membranes": 0.8,
          "WingBones": 1.0, "Ridge": 1.1, "Hand": 2.0}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Hand"] = decimated(pieces["Hand"], N + "HandLow", 1100)
    data["ridge_roots"] = []
    lows["Ridge"] = build_ridge(data["tree"], N + "RidgeLow", GAME, 6, 6, data["ridge_roots"])
    lows["Horns"], _, _ = build_horns(N + "HornsLow", GAME, scale=0.34)
    lows["Teeth"], _ = build_teeth(N + "TeethLow", GAME, 5, 2)
    lows["Claws"], _, data["claw_owner"] = build_claws(N + "ClawsLow", GAME, 6, 2)
    lows["Membranes"] = build_membranes(N + "MembranesLow", GAME, *LOW_MEMB)
    lows["WingBones"] = build_wing_bones(N + "WingBonesLow", GAME, 6, scale=0.4)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the hips are its base: everything ahead of them can rise off them, so it can rear up on its hind legs
TRUNK = BODY_PATH + NECK[1:] + [HEAD, SNOUT[-1]]       # rump to the end of the snout: the line every trunk weight is measured along
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[3], "Hips"), ("Chest", SPINE[4], "Body"), ("Neck1", NECK[0], "Chest"),
               ("Neck2", path_at(NECK, 0.38), "Neck1"), ("Neck3", path_at(NECK, 0.72), "Neck2"), ("Head", NECK[-1], "Neck3"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.04, 0.2, 0.36, 0.52, 0.68, 0.84)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
# each leg: its key, side, joint knots, radii, parent, and its bones' names (the bone heads sit on the knots)
LEGS = (("FL", 1, FORE, FORE_R, "Chest", ["LegFL1", "LegFL2", "LegFL3", "PawFL"]),
        ("BL", 1, HIND, HIND_R, "Hips", ["LegBL1", "LegBL2", "LegBL3", "PawBL"]),
        ("BR", -1, HIND, HIND_R, "Hips", ["LegBR1", "LegBR2", "LegBR3", "PawBR"]),
        ("AR", -1, ARM, ARM_R, "Chest", ["ArmR1", "ArmR2", "ArmR3", "HandR"]))
WING_NAMES = ("Wing%s1", "Wing%s2", "Wing%s3")       # root to elbow, elbow to wrist, the hand; a bone per finger after it


def leg_line(knots, side):
    """A leg's path, mirrored to its side: the right arm's knots are already on its side."""
    return catmull([mir(p, side) if knots is not ARM else p for p in knots], 8)


def leg_knot_f(knots):
    return [k / (len(knots) - 1) for k in range(len(knots))]


def leg_mids(knots, names):
    """Where each leg bone takes over: the middle of each bone (the last, if it ends the leg, just past the end)."""
    fs = leg_knot_f(knots)
    return tuple((fs[k] + fs[k + 1]) / 2 if k + 1 < len(fs) else 1.02 for k in range(len(names)))


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
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    for key, side, knots, radii, parent, names in LEGS:
        line = leg_line(knots, side)
        fs = leg_knot_f(knots)
        for k, name in enumerate(names):
            bones.append((name, path_at(line, fs[k]) if k < len(fs) else line[-1], parent))
            parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        root, elbow, wrist, tips, body = wing_frame(side)
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        bones += [(n1, root, "Chest"), (n2, elbow, n1), (n3, wrist, n2)]
        bones += [("Wing%sF%d" % (tag, j + 1), wrist.copy(), n3) for j in range(4)]
    return armature(bones)


def trunk_knots():
    """Where each trunk bone takes over along TRUNK: the middle of each bone, so the share passes across each joint, never at it."""
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.03,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (V(0, -0.655, 0.81), (0.085, 0.165, 0.085))     # the head, snout and jaw: wholly the head's


def body_weights(P):
    """The skin's weights at any points: the trunk (hips to head), the head, the tail, the legs and the pearl arm; a foot and its toes wholly its foot's,
    the hand round the pearl wholly the hand's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for key, side, knots_l, radii, parent, lnames in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P)
        legs.append((key, side, knots_l, radii, lnames, f, d))
    hand_d = np.full(len(P), 1e9)
    for finger in hand_fingers():
        _, d = nearest_on(catmull(finger, 3), P)
        hand_d = np.minimum(hand_d, d)
    palm = np.linalg.norm((P - np.array(tuple(PALM_C))) / np.array((0.055, 0.058, 0.032)), axis=1)
    arm_f, arm_d = nearest_on(leg_line(ARM, -1), P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        # a foot and its toes
        owner = None
        for key, side, knots_l, radii, lnames, f, d in legs:
            if key != "AR" and (Vector(P[i]) - mir(knots_l[3], side)).length < 0.1 and z < 0.065:
                owner = lnames[3]
        if owner is None and (hand_d[i] < 0.0145 + 0.009 or palm[i] < 1.0 or (arm_f[i] > 0.86 and arm_d[i] < 0.06)):
            owner = "HandR"
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
        reach = prof(TAIL_PROFILE, float(tf[i])) * 1.1 + 0.012
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.0, 0.05, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        for key, side, knots_l, radii, lnames, f, d in legs:
            if key != "AR" and x * side <= 0.012:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.014
            # near the shoulder or hip the hand-over to the body spreads wider, so a swing of the limb stretches the flank a little over a span, not at a line
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            if mm > 0:
                w = blend(w, chain_weight(lnames, leg_mids(knots_l, lnames), float(f[i])), mm)
        out.append(w)
    return out


def membrane_weights(nu, nv):
    """The membranes' weights from where each vertex lies on its sheet: the hand panel between the fingers' bones, the arm panel from the arm's bones
    out to the last finger and in to the flank (the chest and body carry that edge)."""
    uu, vv = sheet_uv(nu, nv, 2)
    tags = ["L"] * (len(uu) // 2) + ["R"] * (len(uu) // 2)
    out = []
    split = 0.6
    for u, v, tag in zip(uu, vv, tags):
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        fingers = ["Wing%sF%d" % (tag, j + 1) for j in range(4)]
        if u <= split:
            a = 3 * u / split
            k = min(int(a), 2)
            t = float(smooth(0, 1, a - k))
            w = {fingers[k]: 1 - t, fingers[k + 1]: t}
            near = float(smooth(0.12, 0.0, v))      # by the wrist, the hand itself
            w = blend(w, {n3: 1.0}, near)
        else:
            a = (u - split) / (1 - split)                   # 0 at the last finger, 1 at the flank
            arm = chain_weight([n1, n2, n3], (0.25, 0.75, 0.95), 1 - a)
            edge = blend({fingers[3]: 1.0}, {"Body": 0.6, "Chest": 0.4}, float(smooth(0.0, 1.0, a)))
            w = blend(arm, edge, float(smooth(0.0, 1.0, v)))
        out.append(w)
    return out


def wing_bone_weights(kind, f, finger, P):
    out = []
    for k, ff, j, p in zip(kind, f, finger, P):
        tag = "L" if p[0] > 0 else "R"
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        if k == 0:
            out.append(chain_weight([n1, n2, n3], (0.25, 0.75, 0.96), float(ff)))
        elif k == 2:
            out.append({"Wing%sF%d" % (tag, j + 1): 1.0})
        else:
            out.append({n3: 1.0})
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    root_w = [{max(w, key=w.get): 1.0} for w in body_weights(np.array(data["ridge_roots"]))]          # a blade is rigid: never sheared across a joint
    weigh(lows["Ridge"], [root_w[j] for j in read_tag(lows["Ridge"], "blade")])
    weigh(lows["Claws"], [{b: 1.0} for b in data["claw_owner"]])
    weigh(lows["Membranes"], membrane_weights(*LOW_MEMB))
    wb = lows["WingBones"]
    weigh(wb, wing_bone_weights(read_tag(wb, "kind"), read_tag(wb, "along"), read_tag(wb, "finger"), verts(wb)))
    for tag in ("L", "R"):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Hand"], "HandR")
    rigid(lows["Horns"], "Head")
    rigid(lows["Teeth"], "Head")
    rigid(glows["Pearl"], "HandR")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animatePearlDragon uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def wings(tag_sign_pairs=(("L", 1), ("R", -1)), lift=0.0, sweep=0.0, elbow=0.0, hand=0.0, fan=0.0):
    """Both wings: lift raises the whole wing (turns it about the body's length), sweep swings it back, elbow and hand fold it, fan closes the fingers."""
    out = {}
    for tag, sign in tag_sign_pairs:
        out["Wing%s1" % tag] = (0, sweep * sign, lift * -sign)
        out["Wing%s2" % tag] = (0, elbow * sign, 0)
        out["Wing%s3" % tag] = (0, hand * sign, 0)
        for j in range(4):
            out["Wing%sF%d" % (tag, j + 1)] = (0, fan * sign * (j / 3), 0)
    return out


# its stances, each searched in Blender against the ground and for torn skin: the same numbers as PetRig's PEARL_* tables
FLEX = wings(lift=-0.15, sweep=0.1, hand=-0.2, fan=0.3)                         # at rest its wings stay raised; now and then they flex and settle
BEAT_UP = wings(lift=0.45, sweep=-0.1)
BEAT_DOWN = wings(lift=-0.7, sweep=0.05, hand=0.15)
TUCK = {"LegFL1": (0.5, 0, 0), "LegFL2": (-1.0, 0, 0), "LegFL3": (0.5, 0, 0), "LegBL1": (-0.6, 0, 0), "LegBL2": (0.7, 0, 0), "LegBR1": (-0.6, 0, 0),
        "LegBR2": (0.7, 0, 0), **{n: (0.06, 0, 0) for n in TAIL_NAMES}}
REAR = {"Hips": (0, 0, 0, (0, -0.019, 0)), "Body": (0.611, 0, 0), "Chest": (0.15, 0, 0), "Neck1": (-0.2, 0, 0), "Neck2": (-0.15, 0, 0), "Head": (-0.25, 0, 0),
        "LegFL1": (-0.386, 0, 0), "LegFL2": (0.344, 0, 0), "LegFL3": (0.059, 0, 0), "ArmR2": (0.3, 0, 0),
        "LegBL1": (-0.295, 0, 0), "LegBR1": (-0.295, 0, 0), "LegBL2": (0.008, 0, 0), "LegBR2": (0.008, 0, 0), "LegBL3": (0.543, 0, 0), "LegBR3": (0.543, 0, 0),
        "Tail1": (-0.055, 0, 0), "Tail2": (-0.028, 0, 0), **wings(lift=0.5, sweep=-0.2)}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-8, -6), "Flex": spec(FLEX), "BeatUp": spec({**BEAT_UP, **TUCK}), "BeatDown": spec({**BEAT_DOWN, **TUCK}),
            "Rear": spec(REAR), "Look": spec({"Neck2": (0.1, 0.35, 0), "Neck3": (0.1, 0.3, 0), "Head": (0.1, 0.35, 0.15)}),
            "Tail": spec({n: (0.05, 0.12, 0) for n in TAIL_NAMES}), "Step": spec({"LegFL1": (0.5, 0, 0), "LegFL2": (-0.6, 0, 0), "LegBL1": (-0.4, 0, 0)})}


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


GROUND_PARTS = {"FrontFoot": ("PawFL",), "HindFeet": ("PawBL", "PawBR"), "Belly": ("Body", "Chest"), "Tail": tuple(TAIL_NAMES), "Hand": ("HandR",),
                "Wings": tuple("Wing%s%d" % (t, k) for t in "LR" for k in (1, 2, 3))}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.5 and p.center.z > 0.7, 2.2), (None, 1.0)], SCALES, margin=0.008)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.85, 0.85, 0.86, 1), far=("Skin",), reach=(0.006, 0.015), far_reach=(0.01, 0.025),
             reaches={"Membranes": (0.004, 0.01), "Ridge": (0.006, 0.014)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in ("Glints", "Pearl"):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-24, 22, 0.0042, 10), (22, -18, 0.002, 6))),
             "Pearl": build_pearl(N + "Pearl_Glow_fff4e2", GAME, 20, 14)}
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
    for name in ("Hips", "Head", "HandR", "WingL3", "Tail6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=4.2, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Flex", "Rear", "BeatDown"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 4.2, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 4.2, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.9, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Flex", wide), ("BeatUp", wide), ("BeatDown", wide), ("Rear", side), ("Look", face), ("Tail", wide), ("Step", side)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 4.2, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

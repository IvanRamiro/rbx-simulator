"""The Azure Sky Dragon (Epic, Wind and sky; Spirit Breeze Egg, also in the Inferno Egg).

A real dragon of the high sky (the owner, 2026-11-12: "A DRAGON", "Don't make it look skinny", and their reference: a great dragon gliding through an
aurora above the clouds, jaws open), recreated with nothing of its old lean wyvern. It lives in the air: its form is built in a glide, its wings spread
wide and broad, its legs drawn up under it, its long thick neck reaching forward and its jaws open. A heavy, muscular, deep-chested body; a long
wedge of a head with heavy brows over narrow glowing ice eyes, a ridged snout, rows of sharp teeth and a pale light in its throat (its breath of the
high wind); a crown of swept spikes fanning back round its skull and spikes from its cheeks; a shaggy mane of spines down its neck and a row of them
down its back and tail. Deep slate-teal scales lit with ice blue, a pale grey-blue belly; its wing membranes aurora-pale, lavender-white going to ice
cyan; dark claws. Nothing of the Celestial Pearl Dragon: no nacre, no scallop-ribbed wings or wrist claws, no conch horns, no pearl, never standing.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/azure_sky_dragon.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It never touches the ground: the game holds it in the air. The maps go to assets/pets/SpiritBreezeEgg/.

What touches what: body, neck, head, lower jaw, legs, feet and tail are one fused skin; the eyes sit in their sockets under their lids; the spikes,
the teeth, the tongue and the claws are their own pieces set into the skin; each wing (its arm, its fingers and its membrane) is set into the back;
the throat's light sits inside the mouth, behind the tongue.
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
PET = "AzureSkyDragon"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "SpiritBreezeEgg")

# ---------- the frame of it: gliding ----------
# the spine from the rump to the withers, level, a little arched: a heavy barrel, deepest at the chest
SPINE = [V(0, 0.3, 0.56), V(0, 0.19, 0.585), V(0, 0.07, 0.595), V(0, -0.05, 0.6), V(0, -0.14, 0.605), V(0, -0.22, 0.615)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.1), (0.2, 0.128), (0.45, 0.118), (0.7, 0.142), (0.88, 0.162), (1, 0.14))      # half-widths, rump to withers
BODY_H = ((0, 0.094), (0.2, 0.112), (0.45, 0.104), (0.7, 0.128), (0.88, 0.156), (1, 0.134))    # half-heights
BODY_DROP = ((0, 0.0), (0.2, 0.006), (0.45, 0.014), (0.7, 0.03), (0.88, 0.05), (1, 0.044))    # the loft's centre below the spine: the chest's keel
# a long, thick neck reaching forward, rising and then carrying the head a little down: a predator's reach
NECK = catmull([V(0, -0.22, 0.635), V(0, -0.33, 0.685), V(0, -0.45, 0.71), V(0, -0.56, 0.708), V(0, -0.645, 0.69)], 10)
NECK_R = ((0, 0.118), (0.35, 0.094), (0.7, 0.08), (1, 0.07))
# the head: a long wedge, its line pitched down toward the nose
HEAD_Y = (-0.645, -0.875)
HEAD_Z = (0.698, 0.622)
HEAD_W = ((0, 0.074), (0.15, 0.083), (0.33, 0.076), (0.55, 0.058), (0.78, 0.047), (0.92, 0.04), (0.98, 0.03), (1, 0.011))
HEAD_HT = ((0, 0.064), (0.18, 0.067), (0.36, 0.054), (0.6, 0.042), (0.85, 0.036), (0.96, 0.029), (1, 0.01))
HEAD_HB = ((0, 0.05), (0.3, 0.036), (0.6, 0.026), (0.88, 0.02), (1, 0.008))
# its lower jaw: its own loft along the head's pitch, hinged under the skull, opened wide: a roar on the wind
JAW_HINGE = V(0, -0.665, 0.66)
JAW_LEN = 0.195
JAW_DROP = 0.062                       # the jaw's line falls this much over its length, with the head's pitch
JAW_OPEN = math.radians(24)
JAW_W = ((0, 0.064), (0.4, 0.054), (0.75, 0.043), (0.94, 0.031), (1, 0.01))
JAW_HT = ((0, 0.012), (0.6, 0.009), (1, 0.005))
JAW_HB = ((0, 0.041), (0.45, 0.03), (0.85, 0.02), (1, 0.008))
JAW_M = Matrix.Translation(JAW_HINGE) @ Matrix.Rotation(JAW_OPEN, 4, V(1, 0, 0)) @ Matrix.Translation(-JAW_HINGE)
# the tail: long, trailing behind in a slow S, thick at its root
TAIL = catmull([V(0, 0.3, 0.565), V(0, 0.45, 0.55), V(0, 0.6, 0.515), V(0.03, 0.75, 0.49), V(0.075, 0.89, 0.48), V(0.095, 1.02, 0.49),
                V(0.085, 1.12, 0.505)], 10)
TAIL_PROFILE = ((0, 0.094), (0.2, 0.074), (0.5, 0.048), (0.8, 0.026), (0.95, 0.014), (1, 0.008))
# the legs (its left side; mirrored for the right): joint centres from the shoulder or hip to the toes, and their radii; drawn up in flight
FORE = [V(0.112, -0.165, 0.555), V(0.148, -0.085, 0.44), V(0.135, -0.19, 0.38), V(0.128, -0.245, 0.36), V(0.124, -0.29, 0.34)]
FORE_R = [0.074, 0.056, 0.043, 0.038, 0.034]
HIND = [V(0.118, 0.215, 0.535), V(0.152, 0.11, 0.42), V(0.142, 0.255, 0.36), V(0.136, 0.355, 0.335), V(0.13, 0.43, 0.315)]
HIND_R = [0.098, 0.068, 0.048, 0.042, 0.036]
# its eyes: narrow, under heavy brows, glowing ice
EYE_R = 0.0195
EYE_C = V(0.056, -0.708, 0.708)
EYE_AXIS = V(0.7, -0.66, 0.26).normalized()
LID_UP, LID_LOW = (16.0, 118.0, 0.0016), (-24.0, -126.0, 0.0014)
LID_TILT = 18.0                       # the outer end raised, the inner end low by the snout: a fierce glare
BLINK_U, BLINK_L = 40.0, 22.0
IRIS, PUPIL_W, PUPIL_H = 0.92, 0.17, 0.82       # on the eye's face (its front is 1): a vertical slit
# the wing (its left), spread in a glide: the arm out and up to the wrist, four long fingers fanning out and back
WING_ROOT = V(0.09, -0.12, 0.69)
WING_ELBOW = V(0.38, -0.02, 0.84)
WING_WRIST = V(0.62, -0.13, 0.98)
FINGERS = [V(1.13, -0.05, 1.05), V(1.14, 0.2, 0.92), V(0.98, 0.43, 0.79), V(0.7, 0.53, 0.68)]     # tips, leading to last
WING_BODY = V(0.11, 0.27, 0.6)            # where the membrane's trailing edge meets the flank
EDGE_CUT = 0.055                          # how far the trailing edge curves in between two finger tips (a gentle sweep, never a deep scallop)


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


def head_loft(m, centre, w, ht, hb, rings=48, sides=40, xform=None):
    """A closed loft along y: centre(f) the middle line, w/ht/hb (f) half-width, height above, depth below. xform: a matrix applied to every point."""
    bm = m.bm
    ring_verts = []
    for i in range(rings + 1):
        f = i / rings
        c = centre(f)
        ring = []
        for k in range(sides):
            t = TAU * k / sides
            sn, cs = math.sin(t), math.cos(t)
            p = c + V(prof(w, f) * math.copysign(abs(cs) ** 0.85, cs), 0, (prof(ht, f) if sn > 0 else prof(hb, f)) * math.copysign(abs(sn) ** 0.9, sn))
            ring.append(bm.verts.new(xform @ p if xform is not None else p))
        ring_verts.append(ring)
    for i in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((ring_verts[i][k], ring_verts[i][k2], ring_verts[i + 1][k2], ring_verts[i + 1][k]))
    bm.faces.new(list(reversed(ring_verts[0])))
    bm.faces.new(ring_verts[-1])


def head_centre(f):
    return V(0, HEAD_Y[0] + (HEAD_Y[1] - HEAD_Y[0]) * f, HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f)


def jaw_centre(f):
    return JAW_HINGE + V(0, -JAW_LEN * f, -0.004 - JAW_DROP * f)


def head_surface(x, y, top=True):
    """The head loft's surface height over (x, y): its top (or its underside)."""
    f = min(max((y - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0]), 0.0), 1.0)
    cz = HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f
    cs = min(1.0, abs(x) / prof(HEAD_W, f)) ** (1 / 0.85)
    sn = math.sqrt(max(0.0, 1 - cs * cs)) ** 0.9
    return cz + prof(HEAD_HT, f) * sn if top else cz - prof(HEAD_HB, f) * sn


# ---------- per-vertex tags ----------
# Blender's sphere primitive reuses the slots of vertices it frees, so the vertices of one piece are not in the order they were made: anything a vertex
# must carry (which spike, which finger) is written on it as a layer when it is made, and read back from the mesh's attribute of that name.
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


# ---------- feet: four long toes, drawn up in flight ----------
def foot_frame(knots, side):
    """A foot's forward (along its toes), across (out to its side) and its sole's down."""
    a, b = mir(knots[3], side), mir(knots[4], side)
    fwd = (b - a).normalized()
    across = V(side, 0, 0) - fwd * fwd.x * side
    across = across.normalized()
    down = fwd.cross(across) * side
    if down.z > 0.3:
        down = -down
    return a, fwd, across, down.normalized()


def foot_toes(knots, side):
    """Per toe: its path from inside the foot to the claw's root: three forward, spread, and one behind."""
    ball, fwd, across, down = foot_frame(knots, side)
    out = []
    for a, reach in ((-0.45, 0.05), (0.0, 0.058), (0.45, 0.05)):
        d = (fwd * math.cos(a) + across * math.sin(a)).normalized()
        root = ball + fwd * 0.004
        out.append([root, root + d * (reach * 0.5) - down * 0.004, root + d * reach + down * 0.012])
    back = ball - fwd * 0.018 + across * 0.012
    out.append([back, back - fwd * 0.02 + down * 0.006, back - fwd * 0.034 + down * 0.012])
    return out


def toe_radius(f):
    return 0.016 * (1 - 0.35 * f)


def claw_path(toe, down):
    """A long dark talon from the toe's end, hooking down under the foot."""
    a, b = toe[-2], toe[-1]
    d = (b - a).normalized()
    return [b - d * 0.008, b + d * 0.016 + down * 0.002, b + d * 0.03 + down * 0.012, b + d * 0.034 + down * 0.026]


def claw_radius(f):
    return 0.0085 * (1 - f) ** 0.9 + 0.0013


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.012, -0.004), (0.092, 0.08, 0.09))                         # the rump
    core.ball(V(0, -0.27, 0.56), (0.1, 0.09, 0.11))                                        # the breast under the neck: a great keel of muscle
    core.ball(V(0, -0.33, 0.66), (0.086, 0.082, 0.084))                                    # the neck's base, a heavy column
    for side in (1, -1):
        core.ball(V(side * 0.1, -0.16, 0.605), (0.086, 0.1, 0.1))                          # the shoulder, under the wing's root
        core.ball(V(side * 0.106, 0.21, 0.56), (0.094, 0.118, 0.108))                      # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.008, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    # the head, the jaw and the limbs, at a finer grain so their angles hold
    fine = Mesh()
    head_loft(fine, head_centre, HEAD_W, HEAD_HT, HEAD_HB)
    head_loft(fine, jaw_centre, JAW_W, JAW_HT, JAW_HB, rings=36, sides=32, xform=JAW_M)
    fine.ball(V(0, -0.65, 0.645), (0.054, 0.06, 0.05), 28, 18)                             # its throat under the skull, meeting the neck
    for side in (1, -1):
        # the corners of its mouth: the jaws joined near the hinge (its mouth opens where the gap holds)
        fine.tube([mir(V(0.042, -0.668, 0.664), side), mir(V(0.046, -0.69, 0.652), side), mir(V(0.043, -0.712, 0.64), side)],
                  lambda f: 0.016 * (1 - 0.5 * f), sides=16)
        # the brow: a heavy shelf over the eye, sloping down toward the snout (a glare), laid on the skull's own surface
        brow = [mir(V(x_, y_, head_surface(x_, y_) + lift), side) for x_, y_, lift in ((0.044, -0.75, -0.004), (0.054, -0.72, 0.004), (0.06, -0.69, 0.005),
                                                                                      (0.058, -0.66, 0.0), (0.05, -0.635, -0.006))]
        fine.tube(catmull(brow, 8), lambda f: 0.0105 * math.sin(math.pi * (0.02 + 0.96 * f)) ** 0.7 + 0.0004, sides=18, flat=1.3, caps=False)
        # the ridges of the snout: from the brow along the top of the muzzle to the nose, on its surface
        ridge = [mir(V(x_, y_, head_surface(x_, y_) - 0.002), side) for x_, y_ in ((0.036, -0.74), (0.031, -0.79), (0.022, -0.845))]
        fine.tube(catmull(ridge, 6), lambda f: 0.0062 * math.sin(math.pi * (0.03 + 0.94 * f)) ** 0.6 + 0.0005, sides=14, caps=False)
        # the cheekbone, under the eye back to the jaw's muscle, along the head's side
        cheek = []
        for y_ in (-0.745, -0.705, -0.665):
            f_ = (y_ - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0])
            cheek.append(mir(V(prof(HEAD_W, f_) * 0.9, y_, head_centre(f_).z - 0.008), side))
        fine.tube(catmull(cheek, 6), lambda f: 0.009 * math.sin(math.pi * (0.03 + 0.94 * f)) ** 0.6 + 0.0005, sides=14, caps=False)
        fine.ball(mir(V(0.057, -0.672, 0.672), side), (0.03, 0.038, 0.03), 24, 16)        # the jaw's muscle
        fine.ball(mir(V(0.018, -0.862, head_surface(0.018, -0.862) - 0.002), side), (0.0095, 0.012, 0.007), 18, 12)     # the flared rim of its nostril
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.12,) * 3, 28, 18)     # the socket
    for side, knots, radii in ((1, FORE, FORE_R), (-1, FORE, FORE_R), (1, HIND, HIND_R), (-1, HIND, HIND_R)):
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.95)
        ball, fwd, across, down = foot_frame(knots, side)
        fine.ball(ball + fwd * 0.006, (0.034, 0.036, 0.026), 24, 14)                       # the foot
        for toe in foot_toes(knots, side):
            fine.tube(catmull(toe, 4), toe_radius, sides=12)
    loft(fine, TAIL, lambda f: prof(TAIL_PROFILE, f), lambda f: prof(TAIL_PROFILE, f) * 0.92)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- spikes: the crown, the cheeks, the neck's mane, the back and the tail ----------
CROWN_C = V(0, -0.655, 0.7)            # the middle of the back of its skull: the crown fans round it


def spike_list():
    """Every spike: root (sunk in the skin), tip, base radius, its group ("head" rides the head; "trunk" its spine; "tail" the tail).
    Swept back with the wind, every one of them."""
    out = []
    # the crown: a fan of spikes round the back of the skull, longest on top, two great ones above the rest
    for side in (1, -1):
        for k, (ang, length) in enumerate(((14, 0.18), (34, 0.14), (54, 0.115), (74, 0.095), (94, 0.08), (114, 0.066))):
            a = math.radians(ang)
            out_dir = V(math.sin(a) * side, 0, math.cos(a))
            root = CROWN_C + out_dir * 0.044 + V(0, 0.004, 0)
            tip = root + (V(0, 1, 0) * 0.8 + out_dir * 0.55).normalized() * length + V(0, 0, 0.012 if k < 2 else 0)
            out.append((root - out_dir * 0.014, tip, 0.021 if k < 2 else 0.016, "head"))
        # its great horns: from behind the eyes, sweeping back and up past the crown; a smaller pair beneath them
        for (hx, hy, length, r0, rise, out_) in ((0.048, -0.684, 0.24, 0.024, 0.8, 0.38), (0.066, -0.664, 0.13, 0.016, 0.3, 0.45)):
            root = mir(V(hx, hy, head_surface(hx, hy) - 0.008), side)
            d = mir(V(out_, 0.9, rise), side).normalized()
            out.append((root, root + d * length, r0, "head"))
        # the cheeks: spikes swept back from behind the jaw's angle
        for k, (pos, length) in enumerate(((V(0.06, -0.69, 0.66), 0.075), (V(0.058, -0.674, 0.64), 0.06), (V(0.05, -0.66, 0.62), 0.045))):
            root = mir(pos, side)
            d = mir(V(0.55, 0.8, -0.15 - 0.15 * k), side).normalized()
            out.append((root - d * 0.01, root + d * length, 0.011 - 0.002 * k, "head"))
        # the jaw: a row of spikes along its lower edge, swept back
        for k in range(5):
            f_ = 0.18 + 0.6 * k / 4
            c_ = jaw_centre(f_)
            local = V(prof(JAW_W, f_) * 0.86, c_.y, c_.z - prof(JAW_HB, f_) * 0.55)
            root = JAW_M @ mir(local, side)
            d = (JAW_M.to_3x3() @ mir(V(0.45, 0.85, -0.3), side)).normalized()
            out.append((root - d * 0.006, root + d * (0.03 - 0.012 * k / 4), 0.0075 - 0.002 * k / 4, "jaw"))
        # the mane: two rows of spines down each side of the neck, swept back
        frames = path_frames(NECK)
        for row, (ang, base) in enumerate(((52, 0.05), (88, 0.04))):
            a = math.radians(ang)
            for k in range(8):
                f = 0.12 + 0.6 * k / 7            # (up to 0.72: further, the last ones were buried in the shoulders)
                p = path_at(NECK, 1 - f)
                tan, s_, up = frames[min(int((1 - f) * (len(NECK) - 1)), len(NECK) - 1)]
                r = prof(NECK_R, 1 - f)
                outward = (up * math.cos(a) + s_ * (math.sin(a) * side)).normalized()
                root = p + outward * (r * 0.85)
                length = base * (0.75 + 0.5 * f)
                tip = root + (outward * 0.55 - tan * 0.85).normalized() * length
                out.append((root - outward * 0.008, tip, 0.008 + 0.004 * f, "trunk"))
    # the dorsal row: from the back of the neck along the back and down the tail
    for k in range(9):
        f = 0.05 + 0.9 * k / 8
        p = path_at(NECK, 1 - f)
        tan = (path_at(NECK, max(0.0, 1 - f - 0.02)) - path_at(NECK, min(1.0, 1 - f + 0.02))).normalized()
        r = prof(NECK_R, 1 - f)
        root = p + V(0, 0, r * 0.9)
        out.append((root - V(0, 0, 0.01), root + (V(0, 0, 1) * 0.6 + tan * 0.8).normalized() * (0.06 + 0.025 * f), 0.012 + 0.004 * f, "trunk"))
    for k in range(7):
        f = 1 - k / 7
        p = path_at(BODY_PATH, f)
        h = prof(BODY_H, f)
        root = p + V(0, 0, h * 0.85 - prof(BODY_DROP, f))
        out.append((root - V(0, 0, 0.01), root + V(0, 0.75, 0.66).normalized() * (0.085 - 0.02 * k / 7), 0.016, "trunk"))
    for k in range(12):
        f = 0.03 + 0.92 * k / 11
        p = path_at(TAIL, f)
        r = prof(TAIL_PROFILE, f)
        tan = (path_at(TAIL, min(1.0, f + 0.02)) - path_at(TAIL, max(0.0, f - 0.02))).normalized()
        root = p + V(0, 0, r * 0.8)
        length = 0.06 * (1 - 0.7 * f) + 0.012 + (0.03 if k == 11 else 0)
        out.append((root - V(0, 0, 0.016),       # (sunk deep: where the tail meets the rump the first ones hovered)
                     root + (V(0, 0, 1) * 0.5 + tan * 0.86).normalized() * length, 0.014 * (1 - 0.6 * f) + 0.003, "tail"))
    return out


def seat(tree, root, tip, depth):
    """A spike set on the sculpted skin itself (a computed surface hovered where smoothing had pulled the skin in): its root moved to the skin's
    nearest point and sunk `depth` into it, its tip keeping its offset from there."""
    surface = tree.find_nearest(root)[0]
    out = tip - root
    return surface - out.normalized() * depth, surface + out


def build_spikes(tree, name, coll, sides=12, per=5, roots=None):
    """Each spike a curved horn, thick at its root, to a fine tip, bowed a little back, seated on the skin. Each vertex carries its spike's number
    ("spike") and how far along it ("along"). roots: a list that takes each spike's (root, group)."""
    m = Mesh()
    bm = m.bm
    make_tags(bm, ints=("spike",), floats=("along",))
    for j, (root, tip, r0, group) in enumerate(spike_list()):
        # sunk a little deeper than its neighbour: buried caps of spikes that meet in the skull never lie in one plane (z-fighting)
        root, tip = seat(tree, root, tip, 0.01 + 0.004 * (j % 3))
        d = tip - root
        bend = d.cross(V(1, 0, 0)).normalized() * ((0.14 if r0 >= 0.02 else 0.07) * d.length) if abs(d.normalized().x) < 0.95 else V(0, 0, 0)
        path = catmull([root, root.lerp(tip, 0.5) + bend, tip], per)
        before = set(bm.verts)
        m.tube(path, lambda f, r0=r0: r0 * (1 - f) ** 1.1 + 0.0009, sides=sides)
        tag_new(bm, before, spike=j)
        layer = bm.verts.layers.float["along"]
        new = [v for v in bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[layer] = float(ff)
        if roots is not None:
            roots.append((tuple(root.lerp(tip, 0.15)), group))
    return m.finish(name, coll)


# ---------- teeth, tongue, the throat's light, claws ----------
def tooth_list():
    """Teeth (left): root, direction, length, radius, on the lower jaw or not. A row of sharp teeth along each jaw and a great fang at the front."""
    out = []
    for y, length, r in ((-0.858, 0.03, 0.006), (-0.838, 0.016, 0.0038), (-0.816, 0.017, 0.0038), (-0.794, 0.015, 0.0036),
                         (-0.772, 0.014, 0.0034), (-0.75, 0.012, 0.0032), (-0.728, 0.011, 0.003), (-0.706, 0.009, 0.0028)):
        f = (y - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0])
        x = prof(HEAD_W, f) * 0.78
        z = head_surface(x, y, top=False) + 0.004
        out.append((V(x, y, z), V(0, -0.15, -1).normalized(), length, r, False))
    for y, length, r in ((-0.838, 0.022, 0.0048), (-0.815, 0.013, 0.0034), (-0.792, 0.012, 0.0032), (-0.77, 0.011, 0.003)):      # (none by the hinge: they hovered)
        f = (JAW_HINGE.y - y) / JAW_LEN
        c = jaw_centre(f)
        local = V(prof(JAW_W, f) * 0.72, y, c.z + prof(JAW_HT, f) * 0.3)
        out.append((JAW_M @ local, JAW_M.to_3x3() @ V(0, -0.12, 1).normalized(), length, r, True))
    return out


def build_teeth(name, coll, sides=10, per=4):
    """Every tooth set in its gum (the lower ones a little deeper; deeper still, they came out under the thin chin). (Seated on the skin's nearest
    point instead, the lower teeth near the hinge snapped up to the upper gum across the open mouth.)"""
    m = Mesh()
    f_all, jaw = [], []
    for side in (1, -1):
        for root, d, length, r, low in tooth_list():
            r0, dd = mir(root, side), mir(d, side)
            path = catmull([r0 - dd * (0.008 if low else 0.005), r0 + dd * length * 0.5, r0 + dd * length], per)
            m.tube(path, lambda f, r=r: r * (1 - f) ** 0.85 + 0.0006, sides=sides)
            f_all += [i / (len(path) - 1) for i in range(len(path)) for _ in range(sides)]
            jaw += [low] * (len(path) * sides)
    return m.finish(name, coll), np.array(f_all), np.array(jaw)


def build_tongue(name, coll, seg=24, rings=12):
    """A long tongue lying in the lower jaw."""
    m = Mesh()
    c = jaw_centre(0.5) + V(0, 0, 0.012)
    m.ball(c, (0.028, 0.075, 0.01), seg, rings)
    o = m.finish(name, coll)
    o.data.transform(JAW_M)
    return o


def build_breath(name, coll, seg=16, rings=10):
    """The pale light deep in its throat: its breath of the high wind, seen between its jaws."""
    m = Mesh()
    m.ball(V(0, -0.69, 0.655), (0.022, 0.03, 0.016), seg, rings)
    return m.finish(name, coll)


def claw_list():
    """Every claw: its path, its radius along it, and the bone that carries it."""
    out = []
    for side, knots, bone in ((1, FORE, "PawFL"), (-1, FORE, "PawFR"), (1, HIND, "PawBL"), (-1, HIND, "PawBR")):
        _, _, _, down = foot_frame(knots, side)
        for toe in foot_toes(knots, side):
            out.append((claw_path(toe, down), claw_radius, bone))
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


def finger_curve(wrist, tip, side, bow=0.04, per=10):
    """A wing-finger, bowed against the wind, from the wrist to its tip."""
    mid = wrist.lerp(tip, 0.5)
    d = (tip - wrist).normalized()
    out = d.cross(V(0, 0, 1)).normalized() * side
    return catmull([wrist, mid + out * bow * 0.3 + V(0, 0, bow * 0.5), tip], per)


def arm_curve(side, per=10):
    root, elbow, wrist, _, _ = wing_frame(side)
    return catmull([root, elbow, wrist], per)


def sample(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def swept_edge(a, b, toward, depth):
    """The trailing edge between two finger tips, curving in a little toward `toward`: a long, even sweep."""
    pts = []
    for t in np.linspace(0, 1, 13):
        p = a.lerp(b, t)
        pull = (toward - p).normalized() * depth * math.sin(math.pi * t)
        pts.append(p + pull)
    return pts


def coons(c0, c1, d0, d1):
    """A surface from four edges: c0(u) and c1(u) along u at v = 0 and 1, d0(v) and d1(v) along v at u = 0 and 1."""
    P00, P10, P01, P11 = c0(0), c0(1), c1(0), c1(1)

    def point(u, v):
        return ((1 - v) * c0(u) + v * c1(u) + (1 - u) * d0(v) + u * d1(v)
                - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10 + (1 - u) * v * P01 + u * v * P11))
    return point


HAND_SPLIT = 0.62       # the sheet's u: the hand panel (between the fingers) before it, the arm panel after


def membrane_point(side):
    """The membrane as one sheet in two panels. The hand (u < HAND_SPLIT): between the four fingers, from a small arc round the wrist out to the
    gently swept trailing edge. The arm (after it): from the arm down to the flank, out to the last finger. v runs from the wrist (or the arm) out."""
    root, elbow, wrist, tips, body = wing_frame(side)
    fingers = [finger_curve(wrist, t, side) for t in tips]
    edges = [swept_edge(tips[k], tips[k + 1], wrist, EDGE_CUT) for k in range(len(tips) - 1)]
    panels = len(tips) - 1

    def hand(u, v):
        k = min(int(u), panels - 1)
        t = u - k
        a = sample(fingers[k], 0.05 + 0.95 * v)
        b = sample(fingers[k + 1], 0.05 + 0.95 * v)
        straight = a.lerp(b, t)
        edge = sample(edges[k], t)
        chord = tips[k].lerp(tips[k + 1], t)
        return straight + (edge - chord) * v ** 2.2
    arm = arm_curve(side)
    trailing = swept_edge(tips[-1], body, wrist.lerp(root, 0.5), EDGE_CUT * 1.8)
    flank = [root.lerp(body, t) + V(-side * 0.02 * math.sin(math.pi * t), 0, 0) for t in np.linspace(0, 1, 11)]
    last = fingers[-1]
    arm_panel = coons(lambda u: sample(list(reversed(arm)), u), lambda u: sample(trailing, 1 - u),
                      lambda v: sample(last, 0.05 + 0.95 * v), lambda v: sample(flank, v))

    def point(u, v):
        if u <= HAND_SPLIT:
            return tuple(hand(panels * u / HAND_SPLIT, v))
        return tuple(arm_panel((u - HAND_SPLIT) / (1 - HAND_SPLIT), v))
    return point


def membrane_thick(u, v):
    return 0.0045


def build_membranes(name, coll, nu=110, nv=44):
    m = Mesh()
    for side in (1, -1):
        m.sheet(membrane_point(side), membrane_thick, nu, nv)
    return m.finish(name, coll)


def build_wing_bones(name, coll, sides=16, scale=1.0):
    """The wings' arms and fingers: the arm thick from its root in the back, the fingers long and fine, a knuckle at the wrist. Each vertex carries its
    part ("kind": 0 arm, 1 knuckle, 2 finger), its finger ("finger", -1 if none) and how far along its part ("along")."""
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
        tube(arm_curve(side, per), lambda f: 0.033 * (1 - 0.45 * f), max(10, int((sides + 8) * scale)), 0)
        before = set(bm.verts)
        m.ball(wrist, (0.024, 0.026, 0.024), max(8, int(20 * scale)), max(5, int(12 * scale)))          # the wrist's knuckle, where the fingers spring from
        tag_new(bm, before, kind=1, finger=-1, along=0.0)
        for j, t in enumerate(tips):
            tube(finger_curve(wrist, t, side, per=per), lambda f: 0.013 * (1 - 0.6 * f) + 0.0025, max(6, int(sides * scale)), 2, j)
    return m.finish(name, coll)


# ---------- colours: the high sky at night ----------
SLATE, TEAL, STEEL, ICE = rgb(22, 42, 62), rgb(32, 70, 94), rgb(58, 104, 140), rgb(138, 186, 222)
BELLY, BELLY_LINE = rgb(168, 190, 210), rgb(112, 132, 156)
SPIKE_ROOT, SPIKE_TIP = rgb(36, 70, 96), rgb(184, 218, 240)
CLAW, CLAW_TIP = rgb(20, 26, 38), rgb(96, 112, 136)
TOOTH, TOOTH_ROOT = rgb(236, 238, 232), rgb(178, 182, 176)
MOUTH, TONGUE = rgb(46, 16, 32), rgb(150, 66, 90)
MEMB_ROOT, MEMB_LAV, MEMB_ICE, MEMB_EDGE = rgb(54, 80, 112), rgb(196, 194, 236), rgb(176, 230, 246), rgb(236, 244, 255)
LINE = rgb(12, 20, 30)
EYE_IN, EYE_MID, EYE_RIM = rgb(236, 255, 255), rgb(120, 230, 255), rgb(20, 90, 140)


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


def night_scales(P, Nn):
    """Deep slate along the back, teal on the flanks, steel lower down, ice blue where the aurora catches the upper curves."""
    up = Nn[:, 2]
    col = mix(np.broadcast_to(STEEL, (len(P), 3)), TEAL, smooth(-0.4, 0.1, up))
    col = mix(col, SLATE, smooth(0.2, 0.8, up))
    sheen = smooth(0.35, 0.75, up) * smooth(0.15, 0.6, fbm(P, 3.0, 3, 41))
    return mix(col, ICE, sheen * 0.22)


DORSAL = [head_centre(0.1)] + list(reversed(NECK)) + list(reversed(BODY_PATH))[1:] + TAIL[1:]      # the crown, down the neck, the back and the tail
VENTRAL = list(reversed(NECK)) + list(reversed(BODY_PATH))[1:] + TAIL[1:]     # the head end of the neck, down the throat, under the body, under the tail


def scale_rows(P):
    """Overlapping scales in rows along the line of the body, their free edges toward the tail. Per point: the seam's darkness, the tile's lit rim,
    its own random number."""
    f, d = nearest_on(DORSAL, P)
    lengths = np.array([(DORSAL[i + 1] - DORSAL[i]).length for i in range(len(DORSAL) - 1)])
    s = f * lengths.sum()
    seg = np.clip((f * (len(DORSAL) - 1)).astype(int), 0, len(DORSAL) - 2)
    fr = path_frames(DORSAL)
    side = np.array([tuple(fr[i][1]) for i in seg])
    up = np.array([tuple(fr[i][2]) for i in seg])
    rel = P - np.array([tuple(DORSAL[i]) for i in seg])
    theta = np.arctan2((rel * side).sum(1), (rel * up).sum(1))
    across = theta * np.maximum(d, 0.02)
    size = np.clip(d * 0.26, 0.007, 0.018)
    row = np.floor(s / (size * 0.8))
    t = s / (size * 0.8) - row
    u = across / size + 0.5 * (row % 2)
    x = u - np.floor(u) - 0.5
    rim = 0.45 + 0.55 * np.sqrt(np.clip(1 - (2 * x) ** 2, 0, 1))
    seam = (1 - smooth(0.0, 0.08, np.abs(t - rim))) + (1 - smooth(0.0, 0.06, 0.5 - np.abs(x))) * (t < rim) * 0.6
    lit = smooth(rim - 0.45, rim - 0.04, t) * (t < rim)
    own = hash01(row.astype(np.int64), np.floor(u).astype(np.int64), 0, 31)
    return np.clip(seam, 0, 1), lit, own


def in_jaw(P_):
    """How much each point belongs to its lower jaw (in the jaw's own frame: below the mouth line, forward of the hinge), and the points in that frame."""
    jinv = JAW_M.inverted()
    loc = np.array([tuple(jinv @ Vector(p)) for p in P_])
    line = np.array([jaw_centre(float(np.clip((JAW_HINGE.y - y) / JAW_LEN, 0, 1))).z + 0.008 for y in loc[:, 1]])
    below = smooth(line + 0.004, line - 0.004, loc[:, 2])
    ahead = smooth(JAW_HINGE.y + 0.006, JAW_HINGE.y - 0.014, loc[:, 1])
    near = smooth(0.085, 0.06, np.abs(loc[:, 0]))
    return below * ahead * near, loc


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    head = smooth(-0.6, -0.64, y)
    small = cells(P, 150.0, 9)
    rows_edge, rows_dome, rows_own = scale_rows(P)
    limb = (np.abs(x) > 0.1) * smooth(0.48, 0.42, z) * (1 - head)
    fine_w = np.clip(head + limb, 0, 1)
    edge = rows_edge * (1 - fine_w) + (1 - smooth(0.0, 0.1, small[1] - small[0])) * fine_w * 0.6
    dome = rows_dome * (1 - fine_w) + (1 - smooth(0.0, 0.6, small[0])) * fine_w
    own = rows_own * (1 - fine_w) + small[2] * fine_w
    col = night_scales(P, Nn)
    col = col * (0.92 + 0.14 * own)[:, None]
    col = mix(col, col * 0.55, edge * 0.6)
    col = mix(col, mix(col, ICE, 0.3), dome * 0.3)
    # the belly plates: pale grey-blue bands across the throat, the belly and under the tail
    s_frac, _ = nearest_on(VENTRAL, P)
    total = sum((VENTRAL[i + 1] - VENTRAL[i]).length for i in range(len(VENTRAL) - 1))
    s_len = s_frac * total
    seg = np.clip(s_frac * (len(VENTRAL) - 1), 0, len(VENTRAL) - 2).astype(int)
    tangents = np.array([tuple((VENTRAL[i + 1] - VENTRAL[i]).normalized()) for i in range(len(VENTRAL) - 1)])
    tan = tangents[seg]
    below = np.array((0, 0, -1.0)) + tan * tan[:, 2:3]
    below = below / np.maximum(np.linalg.norm(below, axis=1)[:, None], 1e-6)
    down = (Nn * below).sum(1)
    belly = smooth(0.4, 0.62, down) * (1 - head) * (1 - limb) * smooth(0.075, 0.045, np.abs(x) - 0.02)
    band = np.mod(s_len / 0.02, 1.0)
    seam = 1 - smooth(0.0, 0.12, np.minimum(band, 1 - band))
    plates = mix(np.broadcast_to(BELLY, (len(P), 3)), BELLY_LINE, seam * 0.8)
    col = mix(col, plates, belly)
    # the head: darker round the eyes, inside the mouth, the nostrils
    rim = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(EYE_C, side)))
        rim = np.maximum(rim, smooth(EYE_R * 1.7, EYE_R * 1.12, np.linalg.norm(P - c, axis=1)))
    col = mix(col, LINE, rim * 0.8)
    jaw, loc = in_jaw(P)
    upper_under = (y < -0.67) & (np.abs(x) < 0.05) & (Nn[:, 2] < -0.55) & (jaw < 0.5) & (z < np.interp(-y, [0.67, 0.9], [0.668, 0.6]))
    line = np.array([jaw_centre(float(np.clip((JAW_HINGE.y - yy) / JAW_LEN, 0, 1))).z for yy in loc[:, 1]])
    jaw_top = (jaw > 0.5) & (Nn[:, 2] > 0.3) & (np.abs(x) < 0.04) & (loc[:, 2] > line + 0.004)
    inside = (upper_under | jaw_top).astype(float)
    col = mix(col, MOUTH, inside)
    nost = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(V(0.018, -0.866, head_surface(0.018, -0.866) + 0.003), side)))
        nost = np.maximum(nost, 1 - smooth(0.0035, 0.0065, np.linalg.norm((P - c) / np.array((1.0, 0.7, 1.0)), axis=1)))
    col = mix(col, LINE, nost * 0.9)
    relief = 0.0003 * dome - 0.0005 * edge - 0.0003 * seam * belly - 0.0012 * nost
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.56 - 0.14 * dome * (1 - belly) + 0.12 * edge + 0.2 * inside, np.zeros(len(P)))


def paint_spikes(o, along):
    col = mix(np.broadcast_to(SPIKE_ROOT, (len(along), 3)), SPIKE_TIP, smooth(0.15, 0.9, along))
    paint(o, col, 0.34 - 0.08 * along, np.zeros(len(along)))


def paint_claws(o, f):
    col = mix(np.broadcast_to(CLAW, (len(f), 3)), CLAW_TIP, smooth(0.4, 1.0, f))
    paint(o, col, np.full(len(f), 0.28), np.zeros(len(f)))


def paint_teeth(o, f):
    col = mix(np.broadcast_to(TOOTH_ROOT, (len(f), 3)), TOOTH, smooth(0.1, 0.5, f))
    paint(o, col, np.full(len(f), 0.3), np.zeros(len(f)))


def paint_tongue(o):
    P = verts(o)
    paint(o, np.broadcast_to(TONGUE, (len(P), 3)), np.full(len(P), 0.35), np.zeros(len(P)))


def sheet_uv(nu, nv, sheets):
    """The u, v of every vertex of `sheets` closed sheets made by Mesh.sheet, in order."""
    uu, vv = [], []
    for _ in range(sheets):
        for i in range(nu + 1):
            for j in range(nv + 1):
                uu += [i / nu, i / nu]
                vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def paint_membranes(o, nu, nv):
    """Aurora-lit: dark by the arm and the body, lavender-white through the middle, ice cyan toward the trailing edge, a faint vein network."""
    P = verts(o)
    uu, vv = sheet_uv(nu, nv, 2)
    col = mix(np.broadcast_to(MEMB_ROOT, (len(P), 3)), MEMB_LAV, smooth(0.02, 0.4, vv))
    col = mix(col, MEMB_ICE, smooth(0.45, 0.9, vv) * (0.5 + 0.5 * smooth(0.2, 0.7, uu)))
    col = mix(col, MEMB_EDGE, smooth(0.92, 1.0, vv) * 0.7)
    vein = 1 - smooth(0.0, 0.06, np.abs(fbm(P, 14.0, 3, 61) - 0.5))
    col = mix(col, col * 0.8, vein * 0.25 * smooth(0.05, 0.3, vv))
    paint(o, col, np.full(len(P), 0.45), np.zeros(len(P)))


def paint_wing_bones(o, kind, f):
    P = verts(o)
    Nn = normals(o)
    col = night_scales(P, Nn)
    finger = mix(np.broadcast_to(TEAL, (len(P), 3)), SPIKE_TIP, smooth(0.75, 1.0, f))
    col = np.where((kind == 2)[:, None], finger, col)
    paint(o, col, np.full(len(P), 0.55), np.zeros(len(P)))


def eye_paint(o, fr):
    """Glowing ice: near white round the slit, ice cyan, a deep blue rim; fine fibres."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(10, 14, 24), (len(px), 3)).copy()
    iris = mix(EYE_IN, EYE_MID, smooth(0.15, 0.6, r))
    iris = mix(iris, EYE_RIM, smooth(0.62, IRIS, r))
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 36 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    slit = np.where(front, (px / PUPIL_W) ** 2 + (py / PUPIL_H) ** 2, 9.0)
    col = mix(col, rgb(4, 6, 10), 1 - smooth(0.8, 1.1, slit))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


# ---------- the whole, high-detail ----------
MEMB_NU, MEMB_NV = 110, 44


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
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SLATE, LINE)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, TEAL, LINE, lower_share=0.9)
    pieces["Spikes"] = build_spikes(data["tree"], N + "SpikesHi", HI)
    pieces["Teeth"], data["tooth_f"], data["tooth_jaw"] = build_teeth(N + "TeethHi", HI)
    pieces["Tongue"] = build_tongue(N + "TongueHi", HI)
    pieces["Claws"], data["claw_f"], _ = build_claws(N + "ClawsHi", HI)
    pieces["Membranes"] = build_membranes(N + "MembranesHi", HI, MEMB_NU, MEMB_NV)
    pieces["WingBones"] = build_wing_bones(N + "WingBonesHi", HI)
    glows = {"Breath": build_breath(N + "Breath_Glow_bff4ff", HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-24, 22, 0.0038, 12), (22, -18, 0.0018, 8)))}
    if not clay:
        paint_skin(skin)
        sp = pieces["Spikes"]
        paint_spikes(sp, read_tag(sp, "along"))
        paint_teeth(pieces["Teeth"], data["tooth_f"])
        paint_tongue(pieces["Tongue"])
        paint_claws(pieces["Claws"], data["claw_f"])
        paint_membranes(pieces["Membranes"], MEMB_NU, MEMB_NV)
        wb = pieces["WingBones"]
        paint_wing_bones(wb, read_tag(wb, "kind"), read_tag(wb, "along"))
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.1, 0.68)
FACE_AT = (0, -0.76, 0.67)
EXTRA = [(0, -1, 0.05, 1.0, FACE_AT), (0.62, -0.75, 0.2, 1.0, FACE_AT), (1, -0.12, 0.08, 1.0, FACE_AT), (0.3, -0.9, 0.2, 0.32, tuple(EYE_C)),
         (0.7, 0.3, 0.5, 3.2, (0.55, 0.15, 0.9)), (0.8, -0.2, -0.4, 1.4, (0.13, 0.05, 0.38))]


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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=4.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 4600
LOW_MEMB = (34, 10)
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Spikes": 1.2, "Teeth": 1.5, "Tongue": 1.0, "Claws": 1.3,
          "Membranes": 0.8, "WingBones": 1.0}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    data["spike_roots"] = []
    lows["Spikes"] = build_spikes(tree_of(lows["Skin"]), N + "SpikesLow", GAME, 5, 2, data["spike_roots"])      # seated on the game skin it ships on
    lows["Teeth"], _, data["tooth_jaw_low"] = build_teeth(N + "TeethLow", GAME, 5, 2)
    lows["Tongue"] = build_tongue(N + "TongueLow", GAME, 10, 6)
    lows["Claws"], _, data["claw_owner"] = build_claws(N + "ClawsLow", GAME, 6, 2)
    lows["Membranes"] = build_membranes(N + "MembranesLow", GAME, *LOW_MEMB)
    lows["WingBones"] = build_wing_bones(N + "WingBonesLow", GAME, 6, scale=0.4)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the hips are its base: everything ahead of them turns off them, the tail trails behind them
TRUNK = BODY_PATH + NECK[1:] + [head_centre(0.0), head_centre(1.0)]       # rump to the end of the snout: the line every trunk weight is measured along
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[3], "Hips"), ("Chest", SPINE[4], "Body"), ("Neck1", NECK[0], "Chest"),
               ("Neck2", path_at(NECK, 0.38), "Neck1"), ("Neck3", path_at(NECK, 0.72), "Neck2"), ("Head", NECK[-1], "Neck3"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.04, 0.2, 0.36, 0.52, 0.68, 0.84)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
# each leg: its key, side, joint knots, radii, parent, and its bones' names (the bone heads sit on the knots)
LEGS = (("FL", 1, FORE, FORE_R, "Chest", ["LegFL1", "LegFL2", "LegFL3", "PawFL"]),
        ("FR", -1, FORE, FORE_R, "Chest", ["LegFR1", "LegFR2", "LegFR3", "PawFR"]),
        ("BL", 1, HIND, HIND_R, "Hips", ["LegBL1", "LegBL2", "LegBL3", "PawBL"]),
        ("BR", -1, HIND, HIND_R, "Hips", ["LegBR1", "LegBR2", "LegBR3", "PawBR"]))
WING_NAMES = ("Wing%s1", "Wing%s2", "Wing%s3")       # root to elbow, elbow to wrist, the hand; a bone per finger after it


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


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
    bones.append(("Jaw", JAW_HINGE.copy(), "Head"))
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
        bones += [("Wing%sF%d" % (tag, j + 1), wrist.copy(), n3) for j in range(len(FINGERS))]
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


HEAD_ZONE = (V(0, -0.765, 0.66), (0.11, 0.17, 0.11))     # the head, snout and jaw: wholly the head's (the jaw then the Jaw's)


def body_weights(P):
    """The skin's weights at any points: the trunk (hips to head), the head and its jaw, the tail and the legs; a foot and its toes wholly its foot's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    jaw, _ = in_jaw(P)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for key, side, knots_l, radii, parent, lnames in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P)
        legs.append((key, side, knots_l, radii, lnames, f, d))
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        owner = None
        for key, side, knots_l, radii, lnames, f, d in legs:
            if (Vector(P[i]) - mir(knots_l[3], side)).length < 0.075 and f[i] > 0.7:
                owner = lnames[3]
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
            if jaw[i] > 0:
                w = blend(w, {"Jaw": 1.0}, float(jaw[i]))
        reach = prof(TAIL_PROFILE, float(tf[i])) * 1.1 + 0.012
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.0, 0.05, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        for key, side, knots_l, radii, lnames, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.014
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
    panels = len(FINGERS) - 1
    out = []
    for u, v, tag in zip(uu, vv, tags):
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        fingers = ["Wing%sF%d" % (tag, j + 1) for j in range(len(FINGERS))]
        if u <= HAND_SPLIT:
            a = panels * u / HAND_SPLIT
            k = min(int(a), panels - 1)
            t = float(smooth(0, 1, a - k))
            w = {fingers[k]: 1 - t, fingers[k + 1]: t}
            w = blend(w, {n3: 1.0}, float(smooth(0.12, 0.0, v)))      # by the wrist, the hand itself
        else:
            a = (u - HAND_SPLIT) / (1 - HAND_SPLIT)                     # 0 at the last finger, 1 at the flank
            arm = chain_weight([n1, n2, n3], (0.25, 0.75, 0.95), 1 - a)
            edge = blend({fingers[-1]: 1.0}, {"Body": 0.6, "Chest": 0.4}, float(smooth(0.0, 1.0, a)))
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


def spike_weights(roots):
    """Each spike rigid on one bone (never sheared across a joint): the head's on the head, the jaw's on the jaw, the rest on the bone nearest its root."""
    pts = np.array([r for r, _ in roots])
    body_w = body_weights(pts)
    tf, _ = nearest_on(TAIL, pts)
    out = []
    for (root, group), bw, f in zip(roots, body_w, tf):
        if group == "head":
            out.append({"Head": 1.0})
        elif group == "jaw":
            out.append({"Jaw": 1.0})
        elif group == "tail":
            w = chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(f))
            out.append({max(w, key=w.get): 1.0})
        else:
            out.append({max(bw, key=bw.get): 1.0})
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    per_spike = spike_weights(data["spike_roots"])
    weigh(lows["Spikes"], [per_spike[j] for j in read_tag(lows["Spikes"], "spike")])
    weigh(lows["Claws"], [{b: 1.0} for b in data["claw_owner"]])
    weigh(lows["Membranes"], membrane_weights(*LOW_MEMB))
    wb = lows["WingBones"]
    weigh(wb, wing_bone_weights(read_tag(wb, "kind"), read_tag(wb, "along"), read_tag(wb, "finger"), verts(wb)))
    weigh(lows["Teeth"], [{"Jaw": 1.0} if j else {"Head": 1.0} for j in data["tooth_jaw_low"]])
    for tag in ("L", "R"):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Tongue"], "Jaw")
    rigid(glows["Breath"], "Head")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateAzureSkyDragon uses. +X lifts what points forward (and closes the jaw); +Y turns to
# its left; +Z rolls it
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def wings(tag_sign_pairs=(("L", 1), ("R", -1)), lift=0.0, sweep=0.0, elbow=0.0, hand=0.0, fan=0.0):
    """Both wings: lift raises the whole wing (turns it about the body's length), sweep swings it back, elbow and hand fold it, fan spreads the fingers."""
    out = {}
    for tag, sign in tag_sign_pairs:
        out["Wing%s1" % tag] = (0, sweep * sign, lift * -sign)
        out["Wing%s2" % tag] = (0, elbow * sign, 0)
        out["Wing%s3" % tag] = (0, hand * sign, 0)
        for j in range(len(FINGERS)):
            out["Wing%sF%d" % (tag, j + 1)] = (0, fan * sign * (j / (len(FINGERS) - 1)), 0)
    return out


# its moves, each checked in Blender for torn skin: the same numbers as PetRig's AZ tables
BEAT_UP = wings(lift=0.55, sweep=-0.08, hand=-0.1)
BEAT_DOWN = wings(lift=-0.6, sweep=0.06, hand=0.18)
FOLD = wings(sweep=0.35, elbow=0.55, hand=0.7, fan=-0.35)                       # wings drawn half in (a stoop)
ROAR = {"Jaw": (-0.22, 0, 0), "Head": (0.16, 0, 0), "Neck3": (0.08, 0, 0), "Neck2": (0.05, 0, 0)}     # the jaw wide for its breath (wider buckled its chin)
BANK = {"Body": (0, 0, 0.25), "Chest": (0, 0.1, 0.1), "Neck2": (0, 0.15, 0), "Head": (0, 0.15, 0), **wings(lift=0.0)}
REACH = {"LegFL1": (-0.5, 0, 0), "LegFL2": (0.6, 0, 0), "LegFR1": (-0.5, 0, 0), "LegFR2": (0.6, 0, 0), "PawFL": (0.4, 0, 0), "PawFR": (0.4, 0, 0)}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-8, -6), "BeatUp": spec(BEAT_UP), "BeatDown": spec(BEAT_DOWN), "Fold": spec(FOLD),
            "Roar": spec(ROAR), "Bank": spec(BANK), "Reach": spec(REACH),
            "Look": spec({"Neck2": (0.1, 0.35, 0), "Neck3": (0.1, 0.3, 0), "Head": (0.1, 0.35, 0.15)}),
            "Tail": spec({n: (0.05, 0.16, 0) for n in TAIL_NAMES})}


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.63, 2.2), (None, 1.0)], SCALES, margin=0.0105, shape="CONVEX")      # (concave packing interlocked two islands by a texel)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.14, 0.24, 0.32, 1), far=("Skin",), reach=(0.006, 0.015),
             far_reach=(0.01, 0.025), reaches={"Membranes": (0.004, 0.01), "Spikes": (0.016, 0.04)})      # (the game spikes sit on the game skin, up to 1.5 cm off their sculpt)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in ("Glints", "Breath"):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-24, 22, 0.0038, 10), (22, -18, 0.0018, 6))),
             "Breath": build_breath(N + "Breath_Glow_bff4ff", GAME, 12, 8)}
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
    print("Z range", round(lo, 4), round(hi, 4), "box middle", round((hi + lo) / 2, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Hips", "Head", "Jaw", "WingL3", "Tail6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=4.6, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    side = (1, -0.05, 0.08, 4.6, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 4.6, VIEW_AT)
    face = (0.4, -0.9, 0.12, 1.0, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Roar", face), ("BeatUp", wide), ("BeatDown", wide), ("Fold", wide), ("Bank", wide),
                       ("Reach", side), ("Look", face), ("Tail", wide)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 4.6, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

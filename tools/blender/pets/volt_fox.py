"""The Volt Fox (Epic, Lightning; Beginner Qi Egg): "A fox born from a thunderclap. Its fur remembers every storm it has run through, and it
crackles when it is pleased."

Recreated (November 10, 2026; the old model was a faceted yellow fox on black legs): the thundercloud fox (the owner's choice), after the raiju,
the thunder beast of Japanese folklore that runs through storm clouds, in a design language of its own: a kit that carries its own storm. A
young fox standing square on four legs, its big head on a small body: a short muzzle, full cheek fluff, tall upright ears whose tips split
into two prongs like a forked bolt, and big storm-blue eyes. Its fur is storm slate, pale as cloud on its chest, belly and muzzle, with
electric-blue bolt markings down its legs and across its cheeks. Its tail is a short furry stalk that carries a great thundercloud: dark
underneath, pale on top, lightning flickering inside it and two small bolts forking down from its underside.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/volt_fox.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: through the bake and the rig, with the limbs' signs measured.
all: also the poses, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre, its paws on the ground (z = 0). +X is its left.
The maps go to assets/pets/BeginnerQiEgg/.

What touches what: head, body, legs, paws and tail stalk are one fused skin; each ear is its own blade, its root buried in its crown; the eyes sit
in their sockets under their lids; the cloud (its own piece, see-through a little in the game) sits on the tail stalk's tip, the stalk buried in
it; the lightning (glow pieces) lies inside the cloud, two bolts forking out of its underside.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "VoltFox"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: storm slate, cloud and lightning ----------
# (storm grey with a cool hint: the first, bluer slates read royal blue under the game's sky light, measured in Play)
SLATE, SLATE_DEEP, SLATE_LIGHT = rgb(76, 82, 98), rgb(42, 46, 58), rgb(120, 126, 142)
CLOUD_FUR = rgb(222, 226, 234)                       # its chest, belly, muzzle and the insides of its ears
BOLT, BOLT_HOT = rgb(70, 206, 255), rgb(196, 246, 255)
NOSE = rgb(26, 26, 40)
MOUTH = rgb(40, 36, 60)
PAD = rgb(46, 48, 60)
LASH = rgb(18, 20, 34)
STORM_DARK, STORM_MID, STORM_TOP = rgb(54, 58, 72), rgb(124, 130, 148), rgb(222, 226, 236)
GLINT_HEX = "f6fbff"
LIGHTNING_HEX = "7fe8ff"

# ---------- the frame of it ----------
HEAD = V(0, -0.17, 0.305)
HEAD_R = (0.098, 0.088, 0.082)                       # big: a kit's
EYE_R = 0.027
EYE_C = V(0.05, -0.238, 0.322)
EYE_AXIS = V(0.5, -0.82, 0.22).normalized()          # set forward and a little out: bright, curious
LID_UP, LID_LOW = (48.0, 118.0, 0.0024), (-46.0, -126.0, 0.002)
LID_TILT = 10.0
BLINK_U, BLINK_L = 70.0, 30.0      # (they must add past the 94 degrees between the lids' edges, 48 and -46: at 62 + 22 a slit of iris showed, seen in Play)
IRIS, PUPIL = 0.9, 0.34
MUZZLE = (V(0, -0.215, 0.285), V(0, -0.292, 0.272))     # a tapered muzzle, from its cheeks to its nose (a ball read as a snout)
NOSE_C = V(0, -0.294, 0.282)
CHEST = (V(0, -0.07, 0.175), (0.076, 0.082, 0.08))
BELLY = (V(0, 0.01, 0.165), (0.07, 0.095, 0.07))
HIPS = (V(0, 0.082, 0.172), (0.07, 0.076, 0.072))
NECK = (V(0, -0.12, 0.232), (0.06, 0.056, 0.068))
# its legs (left): shoulder or hip, elbow or hock, wrist, the paw on the ground
FRONT = [V(0.05, -0.078, 0.145), V(0.054, -0.086, 0.086), V(0.053, -0.094, 0.038), V(0.053, -0.104, 0.017)]
HIND = [V(0.056, 0.095, 0.145), V(0.062, 0.122, 0.086), V(0.058, 0.112, 0.036), V(0.058, 0.102, 0.017)]
LEG_R = [0.031, 0.025, 0.021, 0.019]
HAUNCH = (V(0.055, 0.092, 0.15), (0.048, 0.066, 0.064))
LEGS = (("FL", 1, FRONT), ("FR", -1, FRONT), ("BL", 1, HIND), ("BR", -1, HIND))
# an ear (left): from its crown, straight up and a little out
EAR_BASE, EAR_TIP_C = V(0.046, -0.162, 0.362), V(0.09, -0.145, 0.51)
EAR_W = ((0, 0.046), (0.35, 0.047), (0.75, 0.034), (1, 0.024))       # half-widths, base to tip: broad, the tip wide enough to fork
EAR_FORK = 0.22                                       # how deep the notch between its tip's two prongs runs, of the ear's length
# the tail: a short furry stalk up and back, the cloud on its tip
TAIL = catmull([V(0, 0.125, 0.19), V(0, 0.18, 0.225), V(0, 0.215, 0.29)], 10)
TAIL_R = ((0, 0.03), (0.5, 0.026), (1, 0.024))
CLOUD_C = V(0, 0.245, 0.375)
# its puffs: (offset from CLOUD_C, radius): a cumulus, flat underneath, billowing on top
CLOUD = [(V(0, 0, 0), 0.1), (V(0.085, 0.01, -0.02), 0.075), (V(-0.085, 0.01, -0.02), 0.075), (V(0.03, -0.05, 0.055), 0.07),
         (V(-0.04, 0.04, 0.06), 0.074), (V(0.06, 0.06, 0.015), 0.065), (V(-0.065, -0.045, 0.005), 0.064), (V(0.0, 0.0, 0.1), 0.068),
         (V(0.14, 0.0, -0.04), 0.05), (V(-0.14, 0.005, -0.04), 0.05), (V(0.0, 0.095, -0.015), 0.06)]     # (half this, the tail read as a cauliflower)
CLOUD_FLOOR = -0.065                                 # its flat underside, below CLOUD_C


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(f):
    return float(np.interp(f, np.linspace(0, 1, len(LEG_R)), LEG_R))


# ---------- the ears ----------
def ear_frame(side):
    """Its ear: base, tip, along it (t), its front (f: the way its hollow faces, forward and a little out), across it (b)."""
    base, tip = mir(EAR_BASE, side), mir(EAR_TIP_C, side)
    t = (tip - base).normalized()
    want = mir(V(0.3, -1, 0), side)
    f = (want - t * t.dot(want)).normalized()
    b = t.cross(f).normalized()
    return base, tip, t, f, b


def ear_point(side):
    base, tip, t, f, b = ear_frame(side)
    length = (tip - base).length

    def point(u, v):
        s = v * 2 - 1
        # the tip forks: the middle stops short, two prongs run on at either side
        reach = 1 - EAR_FORK * math.exp(-(s / 0.3) ** 2) - 0.36 * max(0.0, abs(s) - 0.55) / 0.45     # (each prong a point: flat-topped, they stepped like a crown)
        along = u * reach
        w = prof(EAR_W, along)
        cup = 0.4 * w * s * s * (1 - 0.5 * along)        # its edges curl forward: a hollow facing the front
        return tuple(base + t * (along * length) + b * (s * w) + f * cup)
    return point


def ear_thick(u, v):
    s = v * 2 - 1
    return 0.014 * (1 - 0.5 * u) * math.sqrt(max(0.0, 1 - s * s)) ** 0.5 + 0.0045


def build_ear(side, name, coll, low=False):
    m = Mesh()
    nu, nv = (14, 8) if low else (44, 20)
    m.sheet(ear_point(side), ear_thick, nu, nv)
    return m.finish(name, coll)


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    for c, r in (CHEST, BELLY, HIPS, NECK):
        core.ball(c, r)
    for side in (1, -1):
        core.ball(mir(HAUNCH[0], side), HAUNCH[1])
        core.ball(mir(V(0.046, -0.08, 0.17), side), (0.04, 0.05, 0.05))        # the shoulder
    core.tube(TAIL, lambda f: prof(TAIL_R, f), sides=24)
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 20})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 48, 32)
    fine.tube(catmull([MUZZLE[0], MUZZLE[0].lerp(MUZZLE[1], 0.55) + V(0, 0, 0.002), MUZZLE[1]], 10),
              lambda f: 0.044 * (1 - f) ** 0.8 + 0.014, sides=28, flat=1.25)     # wider than tall, tapering to its nose
    fine.ball(NOSE_C, (0.011, 0.009, 0.009), 16, 10)
    fine.ball(V(0, -0.215, 0.258), (0.04, 0.045, 0.026))                      # a soft jaw under the muzzle
    fine.ball(V(0, -0.15, 0.25), (0.066, 0.06, 0.056))                        # its throat, bridging head and neck (without, the head's underside stood as a shelf)
    for side in (1, -1):
        fine.ball(mir(V(0.064, -0.2, 0.275), side), (0.04, 0.042, 0.036))     # its full cheek
        fine.tube([mir(V(0.07, -0.205, 0.272), side), mir(V(0.1, -0.175, 0.262), side), mir(V(0.128, -0.148, 0.252), side)],
                  lambda f: 0.032 * (1 - f) ** 0.9 + 0.006, sides=16)          # the cheek fluff, sweeping back to a soft point (balls read as jowls)
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.007, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(mir(EAR_BASE + V(0, 0.0, -0.012), side), (0.036, 0.024, 0.02), 20, 12)           # the soft base its ear springs from
    for key, side, knots in LEGS:
        fine.tube(leg_path(knots, side), leg_radius, sides=22)
        fine.ball(mir(knots[1], side), (0.024, 0.024, 0.024), 18, 12)        # the elbow or hock
        fine.ball(mir(knots[3], side) + V(0, -0.008, 0.0), (0.026, 0.032, 0.018), 22, 14)   # the round paw
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0026, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    P = verts(c)
    P[:, 2] = np.maximum(P[:, 2], 0.0)                                         # its paws flat on the ground
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- the cloud and its lightning ----------
def build_cloud(name, coll, voxel=0.004):
    m = Mesh()
    for off, r in CLOUD:
        m.ball(CLOUD_C + off, (r, r * 0.95, r * 0.86), 28, 18)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    P = verts(o)
    floor = CLOUD_C.z + CLOUD_FLOOR
    P[:, 2] = np.where(P[:, 2] < floor, floor + (P[:, 2] - floor) * 0.25, P[:, 2])     # flattened underneath, as a cumulus
    set_verts(o, P)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def bolt_path(points, jag, seed):
    """A forked zigzag between points: each segment kinked sideways a little."""
    rng = np.random.default_rng(seed)
    out = [points[0]]
    for a, b in zip(points, points[1:]):
        d = b - a
        side = d.cross(V(0, 0, 1))
        side = side.normalized() if side.length > 1e-6 else V(1, 0, 0)
        for k in (1, 2):
            p = a.lerp(b, k / 3) + side * (jag * (1 if k == 1 else -1) * (0.6 + 0.4 * rng.random()))
            out.append(p)
        out.append(b)
    return out


BOLTS = [   # (knots, thickness, seed): two flickering inside the cloud, two forking down out of its underside
    ([CLOUD_C + V(-0.1, 0.0, 0.01), CLOUD_C + V(0.0, -0.015, 0.0), CLOUD_C + V(0.1, 0.01, 0.02)], 0.005, 1),
    ([CLOUD_C + V(0.03, -0.07, 0.04), CLOUD_C + V(0.0, 0.01, -0.005), CLOUD_C + V(-0.03, 0.07, 0.04)], 0.0045, 2),
    ([CLOUD_C + V(0.05, -0.015, CLOUD_FLOOR + 0.015), CLOUD_C + V(0.07, -0.025, CLOUD_FLOOR - 0.03), CLOUD_C + V(0.088, -0.015, CLOUD_FLOOR - 0.07)], 0.0045, 3),
    ([CLOUD_C + V(-0.055, 0.025, CLOUD_FLOOR + 0.015), CLOUD_C + V(-0.075, 0.035, CLOUD_FLOOR - 0.025), CLOUD_C + V(-0.07, 0.05, CLOUD_FLOOR - 0.055)], 0.004, 4),
]


def build_lightning(name, coll, low=False):
    m = Mesh()
    for knots, r, seed in BOLTS:
        path = bolt_path(knots, 0.012, seed)
        m.tube(path, lambda f, r=r: r * 1.5 * (1 - 0.65 * f) + 0.0012, sides=6 if low else 10)
    return m.finish(name, coll)


# ---------- paint ----------
def zigzag(along, across, period, amp, width):
    """A bolt marking: a band that zigzags along a line. along, across: coordinates; returns 0..1."""
    tri = np.abs(((along / period) % 1.0) * 2 - 1) * 2 - 1           # -1..1 triangle wave
    centre = tri * amp
    return 1 - smooth(width * 0.6, width, np.abs(across - centre))


def paint_skin(o):
    """Storm-slate fur, darker on its back and the backs of its legs, pale as cloud on its chest, belly, muzzle and cheek fluff;
    electric-blue bolt markings zigzagging down the fronts of its legs and across its cheeks; dark paw pads and nose."""
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    n = len(Pv)
    strands = fbm(Pv * np.array([2.5, 2.5, 0.7]), 95.0, 3, 5)
    clumps = fbm(Pv, 34.0, 3, 6)
    col = mix(np.broadcast_to(SLATE, (n, 3)), SLATE_LIGHT, smooth(0.5, 0.8, clumps) * 0.3)      # (at 0.45 the clumps read as blotches in game)
    col = mix(col, SLATE_DEEP, smooth(0.3, 0.95, Nn[:, 2]) * smooth(0.1, 0.3, z) * 0.35)         # its back, darker
    col = col * (0.95 + 0.08 * strands)[:, None]
    # pale cloud fur: chest and belly (facing down or forward, low on the trunk), muzzle, jaw and cheek fluff
    head = np.linalg.norm((Pv - np.array(tuple(HEAD))) / np.array(HEAD_R), axis=1)
    trunk_under = smooth(0.1, -0.6, Nn[:, 2]) * smooth(0.24, 0.13, z) * smooth(0.07, 0.045, np.abs(x))      # (soft edges: hard, they cut lines up its shoulders)
    chest = smooth(0.2, -0.8, Nn[:, 1]) * smooth(0.27, 0.12, z) * smooth(0.0, -0.06, y) * smooth(0.075, 0.05, np.abs(x)) * smooth(1.0, 1.1, head)
    mf, md = nearest_on([MUZZLE[0], MUZZLE[1]], Pv)
    muzzle = (1 - smooth(0.045, 0.06, md)) * smooth(0.15, 0.4, mf) * smooth(-0.2, 0.2, -Nn[:, 2] + 0.3)     # its muzzle's lower half and sides
    jaw = 1 - smooth(0.035, 0.06, np.linalg.norm((Pv - np.array((0, -0.215, 0.258))) / np.array((1.4, 1.0, 1.0)), axis=1))
    fluff = np.zeros(n)
    for side in (1, -1):
        ff, fd = nearest_on([mir(V(0.07, -0.205, 0.272), side), mir(V(0.128, -0.148, 0.252), side)], Pv)
        fluff = np.maximum(fluff, (1 - smooth(0.03, 0.045, fd)) * smooth(0.1, 0.3, ff))
    pale = np.clip(np.maximum.reduce([trunk_under, chest, muzzle, jaw, fluff]), 0, 1)
    col = mix(col, CLOUD_FUR * (0.97 + 0.05 * strands[:, None]), pale)
    # bolt markings down the fronts of its legs, and one across each cheek
    marks = np.zeros(n)
    for key, side, knots in LEGS:
        f, d = nearest_on(leg_path(knots, side), Pv)
        on_leg = (d < leg_radius(0.5) + 0.012) * smooth(0.12, 0.25, f) * smooth(0.9, 0.78, f)
        front = smooth(0.0, 0.5, -Nn[:, 1])
        marks = np.maximum(marks, zigzag(z, x * side - knots[0].x, 0.03, 0.006, 0.0065) * on_leg * front)
    for side in (1, -1):
        cx, cz = side * 0.082, 0.302
        on_cheek = (np.abs(y + 0.19) < 0.028) * (x * side > 0.05) * smooth(0.3, 0.6, Nn[:, 0] * side) * (np.abs(z - cz) < 0.025)
        marks = np.maximum(marks, zigzag(-y, z - cz, 0.02, 0.006, 0.006) * on_cheek)
    col = mix(col, mix(BOLT, BOLT_HOT, 0.25), marks)
    # its nose, its mouth, its pads
    nose = 1 - smooth(0.014, 0.019, np.linalg.norm(Pv - np.array(tuple(NOSE_C)), axis=1))
    col = mix(col, NOSE, nose)
    lx, lz = x, z - (NOSE_C.z - 0.03)
    mouth = (1 - smooth(0.0011, 0.0024, np.abs(lz - 6.0 * lx * lx))) * (np.abs(lx) < 0.02) * (y < -0.255) * smooth(-0.2, 0.3, -Nn[:, 1])
    mouth = np.maximum(mouth, (1 - smooth(0.0011, 0.0024, np.abs(lx))) * (lz > 0.0) * (lz < 0.02) * (y < -0.27))
    col = mix(col, MOUTH, mouth * 0.9)
    pads = smooth(0.01, 0.0, z) * smooth(0.0, -0.4, Nn[:, 2] - 0.2)
    col = mix(col, PAD, smooth(0.008, 0.0, z) * 0.9)
    relief = (strands - 0.5) * 0.0006 + (clumps - 0.5) * 0.0007 - mouth * 0.0008
    set_verts(o, Pv + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.74 - 0.35 * nose - 0.1 * marks, np.zeros(n))


def paint_ear(o, side):
    """Slate on its back, pale cloud fur inside, the two prongs of its tip electric blue."""
    Pv = verts(o)
    base, tip, t, f, b = ear_frame(side)
    along = np.clip(((Pv - np.array(tuple(base))) @ np.array(tuple(t))) / (tip - base).length, 0, 1)
    rel = Pv - np.array(tuple(base))
    s2 = ((rel @ np.array(tuple(b))) / np.maximum(1e-4, np.interp(along, [k[0] for k in EAR_W], [k[1] for k in EAR_W]))) ** 2
    depth = rel @ np.array(tuple(f)) - 0.4 * np.interp(along, [k[0] for k in EAR_W], [k[1] for k in EAR_W]) * s2 * (1 - 0.5 * along)
    inner = smooth(-0.0005, -0.0035, -depth)                          # the front face of the blade: its hollow
    strands = fbm(Pv * np.array([1.0, 1.0, 3.0]), 90.0, 3, 9)
    # pale only in the hollow, a slate rim left round its edges (all pale, the ear read as a flat card); the hollow shadowed a little deeper in
    rim = smooth(0.7, 0.42, s2)
    hollow = mix(np.broadcast_to(CLOUD_FUR, (len(Pv), 3)), SLATE_LIGHT, (0.45 * smooth(0.2, 0.55, along) * (1 - s2) * smooth(0.9, 0.6, along)))
    col = mix(np.broadcast_to(SLATE, (len(Pv), 3)), hollow, inner * rim * smooth(0.05, 0.2, along) * smooth(0.95, 0.75, along) * 0.92)
    tips = smooth(0.72, 0.8, along)
    col = mix(col, mix(BOLT, BOLT_HOT, smooth(0.85, 1.0, along)), tips)
    col = col * (0.96 + 0.06 * strands)[:, None]
    paint(o, np.clip(col, 0, 1), 0.76 - 0.25 * tips, np.zeros(len(Pv)))


def paint_cloud(o):
    """A storm cloud: deep slate underneath, billowing to pale grey-white on top, a faint blue from the lightning inside."""
    Pv = verts(o)
    Nn = normals(o)
    h = np.clip((Pv[:, 2] - (CLOUD_C.z + CLOUD_FLOOR)) / 0.14, 0, 1)
    soft = fbm(Pv, 40.0, 4, 21)
    col = mix(np.broadcast_to(STORM_DARK * 0.8, (len(Pv), 3)), STORM_MID, smooth(0.15, 0.6, h))          # a dark storm underside (an even grey read soft)
    col = mix(col, STORM_TOP, smooth(0.5, 0.95, h) * smooth(0.1, 0.8, Nn[:, 2]))
    col = col * (0.92 + 0.14 * soft)[:, None]
    glow = np.exp(-(np.linalg.norm(Pv - np.array(tuple(CLOUD_C)), axis=1) / 0.06) ** 2)
    col = mix(col, BOLT, glow * 0.25)
    paint(o, np.clip(col, 0, 1), np.full(len(Pv), 0.9), np.zeros(len(Pv)))


def eye_paint(o, fr):
    """A storm-blue eye: deep blue going to electric cyan at its rim, a fine jagged ring like a spark, a big round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(20, 24, 46), (len(px), 3)).copy()
    iris = mix(rgb(40, 90, 200), rgb(110, 220, 255), smooth(0.3, 0.88, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 26 + np.sin(azi * 5) * 1.3))[:, None]     # soft fibres (a jagged spark ring read as a cog)
    iris = mix(iris, iris * 0.6, smooth(-0.1, 0.9, py / IRIS) * 0.45)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(20, 40, 90), smooth(IRIS - 0.12, IRIS - 0.02, r) * (1 - smooth(IRIS - 0.02, IRIS, r)))
    col = mix(col, rgb(8, 10, 24), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 3.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    pieces["Cloud"] = build_cloud(N + "CloudHi", HI)
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SLATE, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SLATE, LASH, lower_share=0.7)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0072, 12), (20, -18, 0.0032, 8))),
             "Lightning": build_lightning(N + "Lightning_Glow_" + LIGHTNING_HEX, HI)}
    if not clay:
        paint_skin(skin)
        paint_cloud(pieces["Cloud"])
        paint_ear(pieces["EarL"], 1)
        paint_ear(pieces["EarR"], -1)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.25), (0.62, -0.72, 0.35), (1, 0, 0.15), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.3), (0, -0.05, 1), (0.5, -0.5, -0.4)]
VIEW_AT = (0, 0.02, 0.24)
FACE_AT = (0, -0.2, 0.31)
EXTRA = [(0, -1, 0.1, 0.8, FACE_AT), (0.75, -0.6, 0.25, 0.8, FACE_AT), (1, -0.1, 0.1, 0.9, FACE_AT), (0.4, -0.85, 0.3, 0.3, tuple(EYE_C)),
         (0.7, 0.6, 0.4, 0.8, tuple(CLOUD_C)), (0.7, -0.6, 0.0, 0.7, (0, 0.0, 0.08))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "glow", {k: len(o.data.polygons) for k, o in glows.items()}, flush=True)
    stage_setup((0.3, 0.32, 0.42, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.05, 0.06, 0.12, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=1.9, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3400
CLOUD_QUADS = 900
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "EarL": 1.2, "EarR": 1.2, "Cloud": 0.85}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS), "Cloud": retopo_skin(pieces["Cloud"], N + "CloudLow", CLOUD_QUADS),
            "EarL": build_ear(1, N + "EarLLow", GAME, low=True), "EarR": build_ear(-1, N + "EarRLow", GAME, low=True)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)                    # its paws on the ground (the re-topology lays them a few millimetres under)
    set_verts(lows["Skin"], P)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK_HEADS = (("Hips", V(0, 0.08, 0.172), "Root"), ("Body", V(0, 0.01, 0.17), "Hips"), ("Chest", V(0, -0.062, 0.18), "Body"),
               ("Neck", V(0, -0.11, 0.222), "Chest"), ("Head", V(0, -0.148, 0.272), "Neck"))
TRUNK = catmull([V(0, 0.13, 0.17)] + [at for _, at, _ in TRUNK_HEADS] + [HEAD + V(0, -0.05, 0.03)], 8)
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Paw" + key] for key, _, _ in LEGS}
TAIL_NAMES = ["Tail1", "Tail2"]
TAIL_F = (0.0, 0.5)


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"),
                  ("Ear" + tag, mir(EAR_BASE, side), "Head")]
    for key, side, knots in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, mir(knots[k], side), parent))
            parent = name
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    bones.append(("Cloud", TAIL[-1].copy(), "Tail2"))
    return armature(bones)


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.05,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (HEAD + V(0, -0.035, -0.015), (0.145, 0.15, 0.1))         # its head with its cheeks, fluff and muzzle


def body_weights(P_):
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P_)
    hz = np.linalg.norm((P_ - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P_)
    legs = []
    for key, side, knots_l in LEGS:
        f, d = nearest_on(leg_path(knots_l, side), P_)
        legs.append((key, side, knots_l, f, d))
    out = []
    for i in range(len(P_)):
        x, y, z = P_[i]
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.12:
            w = blend(w, {"Head": 1.0}, float(smooth(1.12, 0.88, hz[i])))
        # the tail stalk: its root with the hips, then its two bones; its tip, buried in the cloud, with the cloud
        if td[i] < prof(TAIL_R, float(tf[i])) + 0.02 and y > 0.1 and z > 0.17:
            share = float(smooth(0.0, 0.25, tf[i]))
            t = blend(chain_weight(TAIL_NAMES, (0.5, 1.2), float(tf[i])), {"Cloud": 1.0}, float(smooth(0.8, 1.0, tf[i])))
            w = blend(w, t, share)
        for key, side, knots_l, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(float(f[i])) + 0.012
            on = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.95, lr * 1.6, d[i])))
            if key[0] == "B":                                   # the haunch goes with the hip
                hp = Vector(P_[i]) - mir(HAUNCH[0], side)
                hh = math.sqrt((hp.x / 0.06) ** 2 + (hp.y / 0.08) ** 2 + (hp.z / 0.075) ** 2)
                on = max(on, float(smooth(1.15, 0.8, hh)) * float(smooth(0.015, 0.04, x * side)))
            if on > 0:
                leg = chain_weight(LEG_NAMES[key], (0.36, 0.72, 1.2), float(f[i]))
                if z < 0.03:
                    leg = blend(leg, {"Paw" + key: 1.0}, float(smooth(0.03, 0.012, z)))
                w = blend(w, leg, on)
        out.append(w)
    return out


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for side, tag in ((1, "L"), (-1, "R")):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    cloud = lows.pop("Cloud")
    rigid(cloud, "Cloud")
    rigid(glows["Lightning"], "Cloud")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    cloud.name = cloud.data.name = N + "Cloud"
    pet_kit.bind(rig, [body, cloud] + list(glows.values()))
    return body, cloud


def part_flush(body, gap=0.0015, rounds=6):
    """Where an eye or a lid slides in under the brow, the skin can run within a millimetre of it and parallel: it would shimmer. Each such skin face is
    moved off the eye or lid, keeping its side of it, to a clean gap (after the bake: a millimetre or two does not move the paint). Looked for both
    ways, from the eye's or lid's faces and from the skin's, as QA looks. Returns how many skin vertices moved."""
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import intersect_point_tri
    me = body.data
    names = {g.index: g.name for g in body.vertex_groups}
    moved = set()
    for _ in range(rounds):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        dl = bm.verts.layers.deform.active

        def eye_part(f):
            best = {}
            for v in f.verts:
                for gi, w in v[dl].items():
                    best[names[gi]] = best.get(names[gi], 0) + w
            top = max(best, key=best.get)
            return top.startswith("Eye") or top.startswith("Lid")
        part = [eye_part(f) for f in bm.faces]
        tree = BVHTree.FromBMesh(bm)
        push = {}

        def check(src, dst, skin, eye):
            if abs(src.normal.dot(dst.normal)) < 0.99:
                return False
            n = eye.normal
            sdist = (skin.calc_center_median() - eye.calc_center_median()).dot(n)
            target = gap if sdist >= 0 else -gap
            if abs(sdist) >= gap:
                return False
            for v in skin.verts:
                step = n * (target - sdist)
                if v.index not in push or step.length > push[v.index].length:
                    push[v.index] = step
            return True
        for f in bm.faces:
            cen = f.calc_center_median()
            for p in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                for _, _, j, _ in tree.find_nearest_range(p, gap):
                    if j is None or j == f.index or part[j] == part[f.index] or set(f.verts) & set(bm.faces[j].verts):
                        continue
                    g = bm.faces[j]
                    q = p - g.normal * g.normal.dot(p - g.verts[0].co)
                    if intersect_point_tri(q, *[v.co for v in g.verts[:3]]):
                        skin, eye = (g, f) if part[f.index] else (f, g)
                        check(f, g, skin, eye)
        if not push:
            bm.free()
            break
        bm.verts.ensure_lookup_table()
        for i, dv in push.items():
            bm.verts[i].co += dv
        moved |= set(push)
        bm.to_mesh(me)
        bm.free()
    me.update()
    return len(moved)


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left); the same numbers as PetRig's VF tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def probe(rig, body, bones=("EarL", "LegFL1", "LegFL2", "PawFL", "LegBL1", "LegBL2", "PawBL", "Tail1", "Tail2", "Cloud", "Head")):
    """Each limb's signs, measured on the mesh: where the skin it carries goes (model axes, mm) under +0.4 rad about each game axis."""
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()

    def centre(idx):
        bpy.context.view_layer.update()
        dg2 = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg2).to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        body.evaluated_get(dg2).to_mesh_clear()
        return co.reshape(-1, 3)[idx].mean(axis=0)
    for bone in bones:
        gi = groups[bone]
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
        if not idx:
            print("PROBE", bone, "no skin", flush=True)
            continue
        pose(rig, {})
        c0 = centre(idx)
        row = []
        for k, axis in enumerate("xyz"):
            turn = [0.0, 0.0, 0.0]
            turn[k] = 0.4
            pose(rig, spec({bone: tuple(turn)}))
            d = (centre(idx) - c0) * 1000
            row.append("%s+ (%d,%d,%d)" % (axis, round(d[0]), round(d[1]), round(d[2])))
        print("PROBE", bone, len(idx), "verts", " ".join(row), flush=True)
    pose(rig, {})


def uv_clashes(body, size=1024):
    """Which faces share texels: per clash, the two faces' centres and their main bones."""
    me = body.data
    uv = me.uv_layers.active.data
    names = {g.index: g.name for g in body.vertex_groups}
    owner = np.full((size, size), -1, dtype=np.int32)
    pairs = {}
    for p in me.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        here = owner[ys[inside], xs[inside]]
        for o in set(here[here >= 0].tolist()):
            pairs[(o, p.index)] = pairs.get((o, p.index), 0) + int((here == o).sum())
        owner[ys[inside], xs[inside]] = p.index

    def bone_of(fi):
        best = {}
        for vi in me.polygons[fi].vertices:
            for g in me.vertices[vi].groups:
                best[names[g.group]] = best.get(names[g.group], 0) + g.weight
        return max(best, key=best.get)
    for (a, b), n in sorted(pairs.items(), key=lambda kv: -kv[1])[:8]:
        ca, cb = me.polygons[a].center, me.polygons[b].center
        print("UV CLASH", n, "texels", tuple(round(v, 3) for v in ca), bone_of(a), "|", tuple(round(v, 3) for v in cb), bone_of(b), flush=True)


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




def is_head(poly):
    c = np.array(tuple(poly.center))
    return bool(np.linalg.norm((c - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1])) < 1.0)


GROUND_PARTS = {"Paws": tuple("Paw" + k for k, _, _ in LEGS), "Belly": ("Body", "Hips", "Chest"), "Head": ("Head",)}

if __name__ == "__main__" and STAGE in ("all", "rig"):
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.42, 1))
    lows = build_low(pieces, frames)
    # its face given more of the atlas; its paws and lower legs apart (the creases at its toes fold in one chart)
    unwrap(lows, [(is_head, 1.8), (lambda p: p.center.z < 0.06, 1.0), (None, 1.0)], SCALES, margin=0.012, angle=42)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.25, 0.29, 0.4, 1), far=("Skin", "Cloud"), reach=(0.004, 0.01), far_reach=(0.008, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0072, 10), (20, -18, 0.0032, 6))),
             "Lightning": build_lightning(N + "Lightning_Glow_" + LIGHTNING_HEX, GAME, low=True)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body, cloud = bind_all(lows, rig, glows)
    print("SKIN MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "CLOUD tris", sum(len(p.vertices) - 2 for p in cloud.data.polygons),
          "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body, cloud] + list(glows.values()) for v in o.data.vertices), flush=True)
    for o in (body, cloud):
        print("UV OVERLAP TEXELS", o.name, uv_overlap_texels(o.data, 1024), flush=True)
    uv_clashes(body)
    zs = [(o.matrix_world @ v.co).z for o in [body, cloud] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    # (the game's box counts the RootPart, a 0.05 m cube at the origin: its bottom is 0.025 m under the paws, measured in Play)
    bottom = min(lo, -0.025)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE from the box middle (the RootPart counted) down to the ground", round((hi + bottom) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Head", "Hips", "Cloud", "Tail1"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    vs = [v.co for v in glows["Glints"].data.vertices]
    mid = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    print("GLINTS box centre game axes", (round(-mid.x, 4), round(mid.z, 4), round(mid.y, 4)), flush=True)
    probe(rig, body)
    if STAGE == "rig" and not os.environ.get("VF_TRY"):
        print("DONE", flush=True)
        raise SystemExit(0)


# its stances, in game axes, signs measured on the mesh (probe): +x swings a leg forward and up, tips its head back; -x raises its tail stalk
# (and the cloud on it); an ear folds back with +x, splays out with +z on the left. Left values; the right mirrors y and z.
def sym(table):
    out = {}
    for name, v in table.items():
        out[name] = v
        if name.startswith("Leg") and name[4] == "L" or name.startswith("Paw") and name[4] == "L":
            r = name[:4] + "R" + name[5:]
            out[r] = (v[0], -v[1], -v[2]) + tuple(v[3:])
        elif name == "EarL":
            out["EarR"] = (v[0], -v[1], -v[2]) + tuple(v[3:])
    return out


def legs(front, back):
    """front, back: (Leg1, Leg2, Paw) turns about x, on both sides."""
    out = {}
    for key, turns in (("FL", front), ("BL", back)):
        for k, name in enumerate(("Leg%s1", "Leg%s2", "Paw%s")):
            if turns[k]:
                out[name % key] = (turns[k], 0, 0)
    return out


# (each searched for every paw on the ground, to a millimetre: VF_TRY)
SIT = sym({"Hips": (0, 0, 0, (0, -0.042, 0)), "Body": (0.36, 0, 0), "Chest": (0.1, 0, 0), "Neck": (-0.12, 0, 0), "Head": (-0.14, 0, 0),
           "Tail1": (0.3, 0, 0), **legs((-0.5, 0, 0.45), (1.55, -2.45, 0.9))})
DOZE = sym({**SIT, "Neck": (-0.3, 0, 0), "Head": (-0.38, 0.12, 0.08), "EarL": (0.4, 0, 0.1), "Tail1": (0.42, 0, 0)})     # sat, nodding off (lying, its legs splayed)
BOW = sym({"Body": (-0.25, 0, 0), "Chest": (-0.1, 0, 0), "Neck": (0.22, 0, 0), "Head": (0.22, 0, 0), "Tail1": (-0.45, 0.25, 0),
           "EarL": (-0.15, 0, 0), **legs((0.9, -0.1, -0.6), (0.15, 0, -0.1))})
RAISE = sym({"Tail1": (-0.6, 0, 0), "Neck": (0.18, 0, 0), "Head": (0.32, 0, 0), "EarL": (-0.2, 0, -0.15), "Body": (0.08, 0, 0)})
FLY = sym({"Tail1": (0.25, 0, 0), "EarL": (0.45, 0, 0), **legs((0.5, -0.35, 0), (-0.5, 0.4, 0))})
# its trot (PetRig VF.TROT_FRONT, TROT_HIND): diagonal pairs together; per leg, swing = sin(phase), lift = max(0, cos(phase)) (lifted as it
# swings forward): Leg1 = a*swing + b*lift, Leg2 = c*lift, Paw = d*lift + e*max(0, swing). Searched with VF_TRY over the cycle: the lifted pair
# clears 1.8 to 3.3 cm, the planted pair within 5 mm of the ground. (A hind paw lifts by its shin reaching forward: the thigh slants back, so
# swinging it forward lowers the paw.)
TROT_FRONT, TROT_HIND = (0.26, 0.62, -1.2, 0.5, -0.6), (0.3, 0.0, 0.75, 0.1, -0.15)
TROT_LEAD = {"FL": 0.0, "BR": 0.0, "FR": math.pi, "BL": math.pi}


def trot(phase):
    out = {}
    for key, lead in TROT_LEAD.items():
        a, b, c, d, e = TROT_FRONT if key[0] == "F" else TROT_HIND
        swing, lift = math.sin(phase + lead), max(0.0, math.cos(phase + lead))
        out["Leg%s1" % key] = (a * swing + b * lift, 0, 0)
        out["Leg%s2" % key] = (c * lift, 0, 0)
        out["Paw%s" % key] = (d * lift + e * max(0.0, swing), 0, 0)
    return out


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-12, -6), "Walk": spec(trot(0.0)), "Reach": spec(trot(math.pi / 2)), "Sit": spec(SIT), "Doze": {**spec(DOZE), **lids(BLINK_U, BLINK_L)},
            "Bow": spec(BOW), "Raise": spec(RAISE), "Fly": spec(FLY), "Look": spec({"Neck": (0.05, 0.3, 0), "Head": (0.1, 0.4, 0.15)}),
            "EarFlick": spec({"EarL": (0.45, 0, 0.3)}), "Wag": spec({"Tail1": (0, 0.5, 0)})}


if __name__ == "__main__" and STAGE == "all":
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=1.9, size=640)
    lib = pose_library(frames)
    for o in (body, cloud):
        for name, row in pet_kit.stress_report(rig, o, lib).items():
            print("STRESS", o.name[-5:], name, row, flush=True)
    for name in ("Walk", "Reach", "Sit", "Doze", "Bow", "Raise"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.12, 1.9, VIEW_AT)
    face = (0.25, -0.95, 0.15, 0.8, FACE_AT)
    wide = (0.62, -0.72, 0.35, 1.9, VIEW_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Walk", wide), ("Sit", side), ("Doze", wide), ("Bow", side), ("Raise", side), ("Fly", side),
                       ("Look", face), ("EarFlick", wide), ("Wag", (0.6, 0.7, 0.3, 1.9, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.35, 1.9, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values()), extras=[cloud]), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__" and STAGE == "rig" and os.environ.get("VF_TRY"):
    # (tuning the stances: each paw's lowest point, and the belly's)
    import json
    each = {k: ("Paw" + k, "Leg%s2" % k) for k, _, _ in LEGS}
    each["Belly"] = ("Body", "Hips", "Chest")
    for name, table in json.loads(os.environ["VF_TRY"]).items():
        want = spec(sym({k: tuple(v[:3]) + ((tuple(v[3]),) if len(v) > 3 else ()) for k, v in table.items()}))
        pose(rig, want)
        print("TRY", name, lowest_of(body, each), flush=True)
        print("TRY STRESS", name, pet_kit.stress_report(rig, body, {name: want})[name], flush=True)
    pose(rig, {})
    print("DONE", flush=True)

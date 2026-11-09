"""The Thunderclaw Drake (Legendary, Lightning; Elemental Core Egg): "A drake that sharpens its claws on lightning. Mountain passes go quiet when it is
hunting nearby."

A storm wyvern (the owner, 2026-11-09: "I NEED A DRAGON NOT A CROCODILE", then "Storm wyvern"), in a design language of its own: a dragon that is a
living lightning conductor. Two powerful hind legs, bird-jointed, with great iron talons; its wings are its arms, and on the ground it prowls on their
wrists, each wrist armed with a big iron hook. A lean body pitched up from the hips; a slender neck rising in an S, the head carried high like a
sentinel's: a short angular wedge under a heavy brow, gold slit eyes, two fangs over the lip, small iron spikes swept back from the cheeks. Its horns are
lightning rods: two copper rods sweeping up and back, each threaded with white porcelain insulators and tipped with a glowing gold ball, an arc crackling
between them. Three long fingers to a wing, each ending in a copper spur with a glowing gold tip; the membranes are storm-cloud slate, veined with
branching lightning, their trailing edges cut jagged like a sail torn in a gale. A long tail ending in a copper blade in the shape of a lightning bolt;
a zig-zag bolt marking down each flank; storm-indigo hide with a pale banded belly.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/thunderclaw_drake.py -- [clay|paint|rig|all|tables] [review dir]

Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Stands on its hind feet (z = 0). Modelled with its wings half spread and raised (its display): the
game folds them to prowl and spreads them to fly. The maps go to assets/pets/ElementalCoreEgg/.

What touches what: the skin (body, neck, head, hind legs, tail) is one piece; the eyes sit in their sockets under their lids; the horns, fangs and cheek
spikes are set into the head; each talon roots in its toe; each wing (its arm, its fingers, the copper spurs and the wrist hook) is set into the
shoulder, its membrane's inner edge buried in the back; the tail blade roots in the tail's end; the glowing tips sit on the horn and spur ends.
"""
import math
import os
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
PET = "ThunderclawDrake"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours: a storm cloud with lightning in it ----------
HIDE, HIDE_DEEP, HIDE_PALE = rgb(72, 78, 110), rgb(36, 38, 60), rgb(116, 122, 158)
BELLY, BELLY_LINE = rgb(158, 160, 178), rgb(108, 110, 132)
BOLT = rgb(255, 216, 92)
COPPER, COPPER_DEEP, COPPER_BRIGHT = rgb(190, 104, 54), rgb(100, 46, 26), rgb(240, 166, 108)
PORCELAIN, PORCELAIN_DEEP = rgb(236, 232, 218), rgb(168, 162, 150)
IRON, IRON_PALE, EDGE = rgb(42, 42, 50), rgb(84, 84, 96), rgb(255, 236, 168)
TOOTH, TOOTH_ROOT = rgb(240, 234, 214), rgb(176, 168, 148)
MEMB, MEMB_DEEP, MEMB_CLOUD, VEIN = rgb(64, 70, 100), rgb(30, 32, 52), rgb(118, 126, 162), rgb(255, 244, 176)
TIP_HEX, ARC_HEX = "ffe864", "fffabe"

# ---------- the frame of it (its left; mirrored) ----------
SPINE = [V(0, 0.27, 0.46), V(0, 0.16, 0.49), V(0, 0.05, 0.52), V(0, -0.05, 0.56), V(0, -0.13, 0.6)]      # rump to withers: pitched up
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.066), (0.2, 0.094), (0.5, 0.08), (0.78, 0.098), (1, 0.09))          # half-widths
BODY_H = ((0, 0.07), (0.2, 0.092), (0.5, 0.088), (0.78, 0.11), (1, 0.104))           # half-heights
BODY_DROP = ((0, 0.0), (0.2, 0.008), (0.5, 0.016), (0.78, 0.032), (1, 0.03))         # the keel of its chest
NECK = catmull([V(0, -0.12, 0.6), V(0, -0.22, 0.668), V(0, -0.272, 0.75), V(0, -0.27, 0.83), V(0, -0.262, 0.9), V(0, -0.29, 0.958), V(0, -0.336, 0.99)], 10)     # an S: forward, back, forward into the head
NECK_R = ((0, 0.094), (0.3, 0.074), (0.7, 0.058), (1, 0.05))
HEAD = V(0, -0.36, 1.002)
HEAD_R = (0.056, 0.07, 0.05)
SNOUT = [V(0, -0.395, 1.0), V(0, -0.45, 0.988), V(0, -0.505, 0.97)]
SNOUT_R = ((0, 0.04), (0.5, 0.03), (1, 0.019))
JAW = [V(0, -0.345, 0.964), V(0, -0.43, 0.955), V(0, -0.494, 0.947)]
JAW_R = ((0, 0.034), (0.5, 0.024), (1, 0.015))
EYE_R = 0.0145
EYE_C = V(0.045, -0.404, 1.013)
EYE_AXIS = V(0.62, -0.76, 0.18).normalized()
LID_UP, LID_LOW = (-4, 118, 0.0016), (-36, -120, 0.0016)
LID_TILT = 16.0
HORN = [V(0.028, -0.33, 1.034), V(0.044, -0.302, 1.078), V(0.06, -0.262, 1.122), V(0.072, -0.214, 1.162), V(0.078, -0.164, 1.192)]
HORN_R = ((0, 0.0135), (0.3, 0.011), (0.8, 0.0075), (1, 0.0065))
INSULATORS = (0.42, 0.6)                 # where along each horn a porcelain insulator sits
CHEEK = ([V(0.048, -0.338, 0.978), V(0.07, -0.302, 0.984), V(0.094, -0.262, 0.996)], [V(0.046, -0.334, 0.956), V(0.064, -0.302, 0.946), V(0.082, -0.274, 0.94)])
HIND = [V(0.1, 0.15, 0.45), V(0.152, 0.03, 0.3), V(0.15, 0.17, 0.12), V(0.146, 0.1, 0.03)]      # hip, knee (forward), hock (back), the ball of the foot
HIND_R = [0.086, 0.056, 0.04, 0.034]
TAIL = catmull([V(0, 0.27, 0.46), V(0, 0.4, 0.42), V(0, 0.54, 0.352), V(0.03, 0.68, 0.284), V(0.1, 0.8, 0.226), V(0.2, 0.876, 0.188), V(0.3, 0.918, 0.168)], 8)
TAIL_PROFILE = ((0, 0.068), (0.2, 0.055), (0.5, 0.036), (0.8, 0.021), (1, 0.013))
# the wings, half spread and raised
WING_ROOT = V(0.07, -0.1, 0.635)
WING_ELBOW = V(0.25, 0.0, 0.73)
WING_WRIST = V(0.45, -0.15, 0.96)
FINGERS = [V(0.86, -0.06, 1.16), V(0.94, 0.2, 0.9), V(0.72, 0.44, 0.66)]            # tips, leading to last
WING_BODY = V(0.05, 0.07, 0.53)          # where the membrane's trailing edge meets the back (buried in it)
SPUR = 0.05                              # how far each copper spur runs on past its finger's tip
TIP_R = 0.0105
HORN_TIP_R = 0.0125
SPLIT = 0.6                              # the membrane's u: the hand's two panels below it, the arm's panel above
TEETH = (3, 3, 4)                        # the jagged cuts in each panel's trailing edge
MEMB_NU, MEMB_NV = 300, 120
LOW_MEMB = (40, 10)


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


def leg_path(side, per=8):
    return catmull([mir(p, side) for p in HIND], per)


def leg_radius(f):
    return float(np.interp(f, np.linspace(0, 1, len(HIND_R)), HIND_R))


# ---------- per-vertex tags (Blender's sphere primitive reuses freed vertex slots: what a vertex must carry is written on it when it is made) ----------
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


def tagged_tube(m, path, rfn, sides, measure=True, caps=True, **tags):
    """A tube whose new vertices carry these tags and, if measure, how far along the path each lies ("along")."""
    bm = m.bm
    before = set(bm.verts)
    m.tube(path, rfn, sides=sides, caps=caps)
    tag_new(bm, before, **tags)
    if measure:
        layer = bm.verts.layers.float["along"]
        new = [v for v in bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[layer] = float(ff)


def tagged_ball(m, c, radii, seg, rings, **tags):
    before = set(m.bm.verts)
    m.ball(c, radii, seg, rings)
    tag_new(m.bm, before, **tags)


# ---------- the hind feet ----------
def foot_toes(side):
    """Per toe: its path from inside the foot to the talon's root. Three toes forward, spread, and one behind."""
    ball = mir(HIND[3], side)
    out = []
    for a, reach in ((-0.5, 0.062), (0.0, 0.072), (0.5, 0.062)):
        d = V(math.sin(a) * side * 0.9, -math.cos(a), 0)
        root = ball + V(0, -0.006, -0.004)
        out.append([root, root + d * (reach * 0.5) + V(0, 0, 0.003), root + d * reach + V(0, 0, -0.01)])
    back = ball + V(side * 0.012, 0.018, -0.002)
    out.append([back, back + V(side * 0.006, 0.026, -0.004), back + V(side * 0.008, 0.042, -0.01)])
    return out


def toe_radius(f):
    return 0.017 * (1 - 0.3 * f)


def talon_path(toe):
    """A great hooked talon from the toe's end, curling down to the ground; rounded off at the tip, never a needle."""
    a, b = toe[-2], toe[-1]
    d = (b - a).normalized()
    d = (d - V(0, 0, d.z)).normalized()
    return [b - d * 0.008, b + d * 0.014 + V(0, 0, 0.004), b + d * 0.032 + V(0, 0, -0.002), b + d * 0.042 + V(0, 0, -0.014)]


def talon_radius(f):
    return 0.0115 * (1 - f) ** 0.85 + 0.0017


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, 0.0, -0.004), (0.064, 0.07, 0.07))                         # the rump
    core.ball(V(0, -0.15, 0.53), (0.075, 0.07, 0.09))                                      # the breast, under the neck: a deep keel
    core.ball(V(0, -0.17, 0.64), (0.07, 0.07, 0.075))                                      # the neck's base
    for side in (1, -1):
        core.ball(mir(WING_ROOT, side) + V(-side * 0.006, 0.0, -0.01), (0.056, 0.07, 0.06))      # the wing's shoulder: flight muscle
        core.ball(V(side * 0.112, 0.11, 0.41), (0.07, 0.096, 0.1))                          # the thigh's great muscle
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.008, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 40, 28)
    fine.tube(catmull(SNOUT, 6), lambda f: prof(SNOUT_R, f), sides=32, flat=1.18)
    fine.ball(SNOUT[-1] + V(0, -0.002, -0.001), (0.021, 0.012, 0.014))                     # the end of the snout, blunt and hard
    fine.tube(catmull(JAW, 6), lambda f: prof(JAW_R, f), sides=28, flat=1.15)
    fine.ball(JAW[-1] + V(0, -0.003, -0.002), (0.017, 0.012, 0.013))                       # the chin
    fine.tube(catmull([V(0, -0.375, 1.038), V(0, -0.44, 1.012), V(0, -0.498, 0.982)], 6), lambda f: 0.011 * (1 - 0.4 * f), sides=16, flat=2.0)     # the ridge of the nose
    for side in (1, -1):
        # the brow: a hard flat ridge over the eye, sloping down and in toward the snout: a glare, not an eyebrow
        fine.tube(catmull([V(side * 0.047, -0.355, 1.036), V(side * 0.046, -0.395, 1.03), V(side * 0.032, -0.442, 1.015)], 6),
                  lambda f: (0.0078 * (1 - 0.35 * f)) * math.sin(math.pi * (0.1 + 0.8 * f)) ** 0.5 + 0.0015, sides=16, flat=1.15)
        fine.tube(catmull([V(side * 0.042, -0.45, 0.982), V(side * 0.052, -0.4, 0.983), V(side * 0.06, -0.352, 0.985)], 6),
                  lambda f: (0.008 + 0.005 * f) * math.sin(math.pi * (0.1 + 0.8 * f)) ** 0.6 + 0.0015, sides=16)       # the cheekbone
        fine.ball(V(side * 0.044, -0.34, 0.968), (0.03, 0.036, 0.03))                      # the jaw's muscle
        fine.tube(catmull([V(side * 0.03, -0.35, 0.945), V(side * 0.03, -0.42, 0.944), V(side * 0.02, -0.49, 0.94)], 6),
                  lambda f: 0.007 * (1 - 0.5 * f), sides=12, flat=1.4)       # the jaw's lower edge: a hard line
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.1,) * 3, 28, 18)     # the socket
        fine.tube(leg_path(side), leg_radius, sides=24, flat=0.92)
        fine.ball(mir(HIND[1], side) + V(side * 0.004, -0.012, 0.0), (0.05, 0.05, 0.05), 24, 16)       # the knee
        fine.ball(mir(HIND[3], side) + V(0, -0.004, -0.008), (0.038, 0.046, 0.024), 24, 14)       # the foot
        for toe in foot_toes(side):
            fine.tube(catmull(toe, 4), toe_radius, sides=12)
    loft(fine, TAIL, lambda f: prof(TAIL_PROFILE, f), lambda f: prof(TAIL_PROFILE, f) * 0.95)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    P = verts(c)
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- the wings ----------
def wing_frame(side):
    return mir(WING_ROOT, side), mir(WING_ELBOW, side), mir(WING_WRIST, side), [mir(p, side) for p in FINGERS], mir(WING_BODY, side)


def finger_curve(wrist, tip, side, bow=0.03, per=10):
    """A wing-finger, bowed a little against the wind, from the wrist to its tip."""
    mid = wrist.lerp(tip, 0.5)
    d = (tip - wrist).normalized()
    out = d.cross(V(0, 0, 1)).normalized() * side
    return catmull([wrist, mid + out * bow * 0.3 + V(0, 0, bow * 0.4), tip], per)


def arm_curve(side, per=10):
    root, elbow, wrist, _, _ = wing_frame(side)
    return catmull([root, elbow, wrist], per)


def sample(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def jag_edge(a, b, toward, depth, teeth, n):
    """A trailing edge between two tips, cut in toward `toward`, torn into sharp teeth: a sail torn in a gale. n + 1 points, a tooth's point and its
    notch each on a point, so a coarser copy keeps them."""
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        ph = t * teeth
        tri = 1 - 2 * abs(ph - math.floor(ph) - 0.5)           # 0 at a notch, 1 at a tooth's point
        cut = depth * (0.75 * math.sin(math.pi * t) ** 0.8 + 0.5 * (1 - tri) * math.sin(math.pi * t) ** 0.3)
        pts.append(p + (toward - p).normalized() * cut)
    return pts


def coons(c0, c1, d0, d1):
    """A surface from four edges: c0(u) and c1(u) at v = 0 and 1, d0(v) and d1(v) at u = 0 and 1."""
    P00, P10, P01, P11 = c0(0), c0(1), c1(0), c1(1)

    def point(u, v):
        return ((1 - v) * c0(u) + v * c1(u) + (1 - u) * d0(v) + u * d1(v)
                - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10 + (1 - u) * v * P01 + u * v * P11))
    return point


def membrane_point(side, nu):
    """One sheet in three panels. The hand (u < SPLIT): two panels between the three fingers, from the wrist out to the torn edge. The arm (after it):
    from the arm (v = 0) out to the last finger and the torn edge back to the body (v = 1), the finger at its outer end, the back at its inner."""
    root, elbow, wrist, tips, body = wing_frame(side)
    fingers = [finger_curve(wrist, t, side) for t in tips]
    per_hand = round(nu * SPLIT / 2)
    per_arm = nu - 2 * per_hand
    edges = [jag_edge(tips[k], tips[k + 1], wrist, 0.075, TEETH[k], per_hand) for k in range(2)]

    def hand(u, v):
        k = min(int(u), 1)
        t = u - k
        a = sample(fingers[k], 0.05 + 0.95 * v)
        b = sample(fingers[k + 1], 0.05 + 0.95 * v)
        straight = a.lerp(b, t)
        edge = sample(edges[k], t)
        chord = tips[k].lerp(tips[k + 1], t)
        return straight + (edge - chord) * v ** 2.0
    arm = arm_curve(side)
    trailing = jag_edge(tips[2], body, elbow.lerp(root, 0.4), 0.085, TEETH[2], per_arm)
    flank = [root.lerp(body, t) + V(-side * 0.02 * math.sin(math.pi * t), 0, -0.01 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 11)]
    last = fingers[2]
    arm_panel = coons(lambda u: sample(list(reversed(arm)), u), lambda u: sample(trailing, u), lambda v: sample(last, 0.05 + 0.95 * v), lambda v: sample(flank, v))

    def point(u, v):
        if u <= SPLIT:
            return tuple(hand(2 * u / SPLIT, v))
        return tuple(arm_panel((u - SPLIT) / (1 - SPLIT), v))
    return point


def membrane_thick(u, v):
    return 0.004


def build_membranes(name, coll, nu, nv):
    m = Mesh()
    for side in (1, -1):
        m.sheet(membrane_point(side, nu), membrane_thick, nu, nv)
    return m.finish(name, coll)


def spur_path(side, k):
    """The copper spur running on past finger k's tip."""
    root, elbow, wrist, tips, body = wing_frame(side)
    path = finger_curve(wrist, tips[k], side)
    d = (path[-1] - path[-2]).normalized()
    return [path[-1] - d * 0.02, path[-1], path[-1] + d * SPUR]


def spur_tip(side, k):
    return spur_path(side, k)[-1]


def build_wing_bones(name, coll, sides=16, scale=1.0):
    """The wings' arms and fingers, each finger with a copper spur on its end. Each vertex carries its part ("kind": 0 arm, 1 knuckle, 2 finger,
    3 spur), its finger ("finger", -1 if none) and how far along its part ("along")."""
    m = Mesh()
    make_tags(m.bm, ints=("kind", "finger"), floats=("along",))
    per = max(3, int(10 * scale))
    for side in (1, -1):
        root, elbow, wrist, tips, body = wing_frame(side)
        tagged_tube(m, arm_curve(side, per), lambda f: 0.03 * (1 - 0.4 * f), max(10, int((sides + 8) * scale)), kind=0, finger=-1)
        tagged_ball(m, elbow, (0.024, 0.024, 0.024), max(8, int(20 * scale)), max(5, int(12 * scale)), kind=0, finger=-1, along=0.5)       # the elbow's point
        tagged_ball(m, wrist, (0.024, 0.026, 0.024), max(8, int(20 * scale)), max(5, int(12 * scale)), kind=1, finger=-1, along=0.0)     # the wrist's knuckle: what it walks on
        for j, t in enumerate(tips):
            tagged_tube(m, finger_curve(wrist, t, side, per=per), lambda f: 0.012 * (1 - 0.5 * f) + 0.002, max(6, int(sides * scale)), kind=2, finger=j)
            tagged_tube(m, catmull(spur_path(side, j), max(2, int(3 * scale))), lambda f: 0.0068 * (1 - 0.35 * f), max(6, int(12 * scale)), kind=3, finger=j)
    return m.finish(name, coll)


def wrist_hook(side):
    """The great iron hook on the wing's wrist, pointing forward and down: on the ground it walks on the knuckle behind it."""
    root, elbow, wrist, tips, body = wing_frame(side)
    fwd = (wrist - elbow).normalized()
    out = V(side, 0, 0)
    return [wrist + fwd * 0.01, wrist + fwd * 0.03 + out * 0.004 + V(0, -0.012, 0.004), wrist + fwd * 0.05 + out * 0.008 + V(0, -0.03, -0.006),
            wrist + fwd * 0.058 + out * 0.01 + V(0, -0.04, -0.024)]


# ---------- talons, hooks, horns, fangs, the tail's blade ----------
def claw_list():
    """Every talon and hook: its path, its radius along it, and its owner (0 left foot, 1 right foot, 2 left wrist, 3 right wrist)."""
    out = []
    for side, owner in ((1, 0), (-1, 1)):
        for toe in foot_toes(side):
            out.append((catmull(talon_path(toe), 4), talon_radius, owner))
    for side, owner in ((1, 2), (-1, 3)):
        out.append((catmull(wrist_hook(side), 4), lambda f: 0.0125 * (1 - f) ** 0.85 + 0.0018, owner))
    return out


def build_claws(name, coll, sides=12):
    m = Mesh()
    make_tags(m.bm, ints=("owner",), floats=("along",))
    for path, rfn, owner in claw_list():
        tagged_tube(m, path, rfn, sides, owner=owner)
    return m.finish(name, coll)


def horn_path(side):
    return catmull([mir(p, side) for p in HORN], 6)


def horn_tip(side):
    return horn_path(side)[-1]


def build_horns(name, coll, sides=20, scale=1.0):
    """Two copper lightning rods, each threaded with two porcelain insulators (ribbed discs); and two small iron spikes swept back from each cheek.
    kind: 0 copper, 1 porcelain, 2 iron."""
    m = Mesh()
    make_tags(m.bm, ints=("kind",), floats=("along",))
    for side in (1, -1):
        path = horn_path(side)
        tagged_tube(m, path, lambda f: prof(HORN_R, f), max(8, int(sides * scale)), kind=0)
        for f0 in INSULATORS:
            c = path_at(path, f0)
            d = (path_at(path, f0 + 0.02) - path_at(path, f0 - 0.02)).normalized()
            r = prof(HORN_R, f0)
            # an insulator: a stack of two discs on a collar, each disc wider than the rod by nearly its own radius
            pts = [c - d * 0.016, c - d * 0.01, c - d * 0.006, c - d * 0.002, c + d * 0.002, c + d * 0.006, c + d * 0.01, c + d * 0.016]
            radii = [r + 0.001, r + 0.004, r + 0.011, r + 0.004, r + 0.004, r + 0.011, r + 0.004, r + 0.001]
            tagged_tube(m, pts, lambda f, rr=radii: float(np.interp(f, np.linspace(0, 1, len(rr)), rr)), max(10, int(24 * scale)), measure=False, kind=1, along=f0)
        for k, spike in enumerate(CHEEK):
            r0 = 0.011 if k == 0 else 0.008
            tagged_tube(m, catmull([mir(p, side) for p in spike], 4), lambda f, r0=r0: r0 * (1 - f) ** 0.9 + 0.0015, max(6, int(14 * scale)), kind=2)
    return m.finish(name, coll)


def fang_list():
    """Two fangs a side, from inside the upper lip down over the lower jaw's outside."""
    out = []
    for side in (1, -1):
        for y, length in ((-0.476, 0.019), (-0.456, 0.013)):
            top = V(side * 0.028, y, 0.962)
            out.append([top + V(0, 0, 0.006), top, top + V(side * 0.002, -0.001, -length * 0.6), top + V(side * 0.001, -0.004, -length)])
    return out


def build_teeth(name, coll, sides=10, per=4):
    m = Mesh()
    make_tags(m.bm, floats=("along",))
    for path in fang_list():
        tagged_tube(m, catmull(path, per), lambda f: 0.0045 * (1 - f) ** 0.8 + 0.0008, sides)
    return m.finish(name, coll)


BOLT_SHAPE = [(0.0, -0.1), (0.55, -0.7), (0.55, -0.26), (1.0, -0.42), (0.42, 0.32), (0.42, -0.12), (0.0, 0.1)]      # a lightning-bolt glyph: along, across


def blade_frame():
    """Where the tail's blade sits: its root in the tail's end, laid along the tail's last stretch, standing up."""
    end = TAIL[-1]
    d = (TAIL[-1] - TAIL[-4]).normalized()
    up = (V(0, 0, 1) - d * d.z).normalized()
    return end - d * 0.03, d, up


def build_blade(name, coll, scale=1.0):
    """A flat copper blade in the shape of a lightning bolt, standing up off the tail's end, its edges bevelled."""
    root, d, up = blade_frame()
    L, W = 0.17, 0.11
    side = d.cross(up).normalized()
    m = Mesh()
    bm = m.bm
    outline = [root + d * (a * L) + up * (b * W) for a, b in BOLT_SHAPE]
    layers = []
    for off, inset in ((0.0045, 0.006), (0.0, 0.0), (-0.0045, 0.006)):
        ring = []
        for k, p in enumerate(outline):
            a, b = outline[k - 1], outline[(k + 1) % len(outline)]
            n1 = (p - a).cross(side).normalized()
            n2 = (b - p).cross(side).normalized()
            bis = (n1 + n2).normalized()
            q = p - bis * inset / max(0.35, bis.dot(n1))
            ring.append(bm.verts.new(q + side * off))
        layers.append(ring)
    n = len(outline)
    for i in range(2):
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((layers[i][k], layers[i][k2], layers[i + 1][k2], layers[i + 1][k]))
    top = bm.faces.new(layers[0])
    bot = bm.faces.new(list(reversed(layers[2])))
    bmesh.ops.triangulate(bm, faces=[top, bot])
    m.tube([root - d * 0.03, root, root + d * 0.022], lambda f: 0.014 - 0.004 * f, sides=max(8, int(16 * scale)))      # the socket gripping the tail
    return m.finish(name, coll, smooth_shade=False)


# ---------- the glows ----------
def build_tips(name, coll, hi=True):
    """A glowing gold ball on each horn and each copper spur."""
    m = Mesh()
    seg, rings = (24, 16) if hi else (10, 6)
    for side in (1, -1):
        m.ball(horn_tip(side), (HORN_TIP_R,) * 3, seg, rings)
        for k in range(3):
            m.ball(spur_tip(side, k), (TIP_R,) * 3, seg, rings)
    return m.finish(name, coll)


def arc_points(per=1):
    """The arc between its horn tips: a jagged line bowed up over its head."""
    a, b = horn_tip(1), horn_tip(-1)
    kinks = [(0.0, 0, 0), (0.14, 0.012, 0.006), (0.27, -0.004, 0.022), (0.4, 0.01, 0.03), (0.52, -0.008, 0.036), (0.63, 0.008, 0.032), (0.76, -0.01, 0.02),
             (0.88, 0.006, 0.01), (1.0, 0, 0)]
    pts = [a.lerp(b, t) + V(0, dy, dz) for t, dy, dz in kinks]
    out = []
    for i in range(len(pts) - 1):
        for s in range(per):
            out.append(pts[i].lerp(pts[i + 1], s / per))
    out.append(pts[-1])
    return out


def build_arc(name, coll, sides=6):
    m = Mesh()
    m.tube(arc_points(3), lambda f: 0.0032 * (0.6 + 0.4 * math.sin(math.pi * f)), sides=sides)
    return m.finish(name, coll, smooth_shade=False)


def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT) for side, tag in ((1, "L"), (-1, "R"))}


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


def write_tags(o, src_P, vals):
    """Each vertex of o takes the tags of the nearest of src_P."""
    from mathutils.kdtree import KDTree
    kd = KDTree(len(src_P))
    for i, q in enumerate(src_P):
        kd.insert(q, i)
    kd.balance()
    near = [kd.find(q)[1] for q in verts(o)]
    for key, arr in vals.items():
        kind = "FLOAT" if arr.dtype.kind == "f" else "INT"
        if o.data.attributes.get(key):
            o.data.attributes.remove(o.data.attributes[key])
        a = o.data.attributes.new(key, kind, "POINT")
        a.data.foreach_set("value", [float(arr[i]) if kind == "FLOAT" else int(arr[i]) for i in near])


def fused(o, voxel, tags=()):
    """One closed surface out of overlapping primitives (nothing inside for a bake to hit), its tags carried over."""
    P0 = verts(o)
    vals = {t: read_tag(o, t) for t in tags}
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 1})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    if vals:
        write_tags(o, P0, vals)
    return o


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_skin()
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, HIDE, HIDE_DEEP * 0.4)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, HIDE, HIDE_DEEP * 0.5, lower_share=0.7)
    pieces["Membranes"] = build_membranes(N + "MembranesHi", HI, MEMB_NU, MEMB_NV)
    pieces["WingBones"] = fused(build_wing_bones(N + "WingBonesHi", HI), 0.0008, ("kind", "finger", "along"))
    pieces["Claws"] = build_claws(N + "ClawsHi", HI)
    pieces["Horns"] = fused(build_horns(N + "HornsHi", HI), 0.0006, ("kind", "along"))
    pieces["Teeth"] = build_teeth(N + "TeethHi", HI)
    pieces["Blade"] = fused(build_blade(N + "BladeHi", HI), 0.0007)
    glows = {"Tips": build_tips(N + "Tips_Glow_" + TIP_HEX, HI), "Arc": build_arc(N + "Arc_Glow_" + ARC_HEX, HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-22, 20, 0.0032, 10), (20, -18, 0.0015, 6)))}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


# ---------- painting ----------
def cells_3d(P, f, seed=0):
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
                off = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                d = np.linalg.norm(q - c - off, axis=1)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                d1 = np.where(nearer, d, d1)
    return d1, d2, own


def tri_wave(x):
    """0 to 1 and back, once per unit."""
    return 1 - 2 * np.abs(x - np.floor(x) - 0.5)


TRUNK_LINE = [HEAD.copy()] + list(reversed(NECK)) + list(reversed(BODY_PATH))[1:] + TAIL[1:]      # the crown, down the neck, the back, the tail


def trunk_coords(P):
    """Per point: how far along the trunk line (metres from the crown), how far off it, and where round it (up: +1 on top, -1 underneath; out: to its side)."""
    A = np.array([tuple(p) for p in TRUNK_LINE])
    seg = np.linalg.norm(A[1:] - A[:-1], axis=1)
    arc = np.concatenate([[0], np.cumsum(seg)])
    f, d = nearest_on(TRUNK_LINE, P)
    k = f * (len(A) - 1)
    i = np.clip(k.astype(int), 0, len(A) - 2)
    t = k - i
    Q = A[i] * (1 - t)[:, None] + A[i + 1] * t[:, None]
    s = arc[i] * (1 - t) + arc[i + 1] * t
    tan = A[i + 1] - A[i]
    tan /= np.linalg.norm(tan, axis=1)[:, None]
    side = np.array([1.0, 0, 0]) - tan * tan[:, :1]
    side /= np.linalg.norm(side, axis=1)[:, None]
    up = np.cross(tan, side)
    rel = P - Q
    rn = rel / (np.linalg.norm(rel, axis=1)[:, None] + 1e-9)
    return s, d, (rn * up).sum(1), np.abs((rn * side).sum(1)), arc[-1]


def trunk_radius(s):
    """The trunk's rough radius at a distance s along TRUNK_LINE."""
    neck_len = sum((NECK[i + 1] - NECK[i]).length for i in range(len(NECK) - 1)) + (HEAD - NECK[-1]).length
    body_len = sum((BODY_PATH[i + 1] - BODY_PATH[i]).length for i in range(len(BODY_PATH) - 1))
    tail_len = sum((TAIL[i + 1] - TAIL[i]).length for i in range(len(TAIL) - 1))
    knots_s = [0, neck_len, neck_len + body_len * 0.5, neck_len + body_len, neck_len + body_len + tail_len]
    knots_r = [0.05, 0.094, 0.095, 0.07, 0.013]
    return np.interp(s, knots_s, knots_r), neck_len, body_len


def mouth_z(y):
    """The line of its mouth, where the snout meets the jaw."""
    return np.interp(y, [-0.52, -0.49, -0.44, -0.39, -0.36, -0.34], [0.958, 0.959, 0.961, 0.961, 0.958, 0.952])


def skin_fields(P, Nn):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    s, d, up, out, total = trunk_coords(P)
    r, neck_len, body_len = trunk_radius(s)
    on_trunk = d < r * 1.5 + 0.02
    legs = np.full(len(P), 1e9)
    for side in (1, -1):
        _, ld = nearest_on(leg_path(side), P)
        legs = np.minimum(legs, ld)
    leg = legs < np.interp(z, [0, 0.3, 0.45], [0.06, 0.075, 0.1])
    head = (y < -0.33) & (z > 0.9)
    belly = on_trunk * (~leg) * smooth(-0.45, -0.75, up) * (~head)
    band = 0.5 + 0.5 * np.cos(s * TAU / 0.024)
    # the bolt down each flank: a zig-zag band from the base of the neck to the tail's last third
    zig = 0.08 + 0.42 * tri_wave(s / 0.1)
    bolt = (1 - smooth(0.06, 0.1, np.abs(up - (zig - 0.25)))) * smooth(0.55, 0.75, out) * on_trunk * (~leg) * (~head)
    bolt *= smooth(neck_len * 0.55, neck_len * 0.75, s) * (1 - smooth(neck_len + body_len + 0.3, neck_len + body_len + 0.45, s))
    d1, d2, own = cells_3d(P, 150.0, 5)
    scale = smooth(0.0, 0.14, d2 - d1)
    D1, D2, own2 = cells_3d(P, 70.0, 9)
    plate = smooth(0.0, 0.1, D2 - D1)            # big plates on the crown, the brow and down the back
    back = smooth(0.35, 0.75, up) * on_trunk * (~leg) + head * smooth(0.2, 0.7, Nn[:, 2])
    mouth = (np.abs(z - mouth_z(y)) < 0.0024) * (y < -0.345) * (np.abs(x) > 0.008) * head
    nostril = np.zeros(len(P))
    for side in (1, -1):
        nostril = np.maximum(nostril, 1 - smooth(0.0035, 0.0065, np.linalg.norm(P - np.array((0.011 * side, -0.498, 0.982)), axis=1)))
    mask = np.zeros(len(P))
    for side in (1, -1):
        mask = np.maximum(mask, 1 - smooth(EYE_R * 1.3, EYE_R * 2.4, np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1)))
    return dict(belly=belly, band=band, bolt=bolt, scale=scale, own=own, plate=plate, own2=own2, back=back, mouth=mouth, nostril=nostril, mask=mask, leg=leg)


def carve_skin(o):
    P, Nn = verts(o), normals(o)
    F = skin_fields(P, Nn)
    plate_zone = F["back"]
    d = (0.0005 * F["scale"] * (1 - plate_zone) + 0.0012 * F["plate"] * plate_zone - 0.0011 * F["belly"] * smooth(0.82, 1.0, F["band"])
         - 0.0016 * F["mouth"] - 0.0035 * F["nostril"])
    set_verts(o, P + Nn * d[:, None])


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    F = skin_fields(P, Nn)
    col = np.broadcast_to(HIDE, (n, 3)).copy()
    col = mix(col, HIDE_DEEP, F["back"] * 0.55)                                              # dark along the top: a storm cloud's
    col = mix(col, HIDE_PALE, (F["own"] > 0.8) * F["scale"] * 0.3)
    col = mix(col, HIDE_DEEP * 0.7, (1 - F["scale"]) * 0.35)                                # the fine scales' edges
    col = mix(col, HIDE_DEEP * 0.6, F["back"] * (1 - F["plate"]) * 0.6)                     # the plates' edges
    col = mix(col, HIDE * 1.1, F["back"] * (F["own2"] > 0.7) * F["plate"] * 0.3)
    col = mix(col, BELLY, F["belly"] * 0.9)
    col = mix(col, BELLY_LINE, F["belly"] * smooth(0.82, 1.0, F["band"]) * 0.75)
    col = mix(col, BOLT, F["bolt"] * 0.92)
    col = mix(col, HIDE_DEEP * 0.45, F["mask"] * 0.75)                                      # a dark mask round the eyes: a glare
    col = mix(col, HIDE_DEEP * 0.25, np.clip(F["mouth"] + F["nostril"], 0, 1))
    col = mix(col, HIDE_DEEP * 0.7, smooth(0.04, 0.0, P[:, 2]) * 0.6)                       # soles
    rough = 0.5 - 0.12 * F["back"] * F["plate"] + 0.12 * F["belly"] - 0.15 * F["bolt"]
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def eye_paint(o, fr):
    """Molten gold, darker at the rim, a tall slit pupil."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(255, 226, 96), rgb(214, 128, 18), smooth(0.15, 0.6, r))
    col = mix(col, rgb(70, 34, 8), smooth(0.62, 0.74, r))
    azi = np.arctan2(py, px)
    col = col * (0.88 + 0.12 * np.sin(azi * 34 + np.sin(azi * 5) * 2))[:, None]
    slit = (np.abs(px) < 0.085 * np.sqrt(np.clip(1 - (py / 0.56) ** 2, 0, 1))) * (a > 0)
    col = mix(col, rgb(10, 6, 4), slit)
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.06), np.zeros(len(px)))


def sheet_uv(nu, nv, sheets):
    """The u, v of every vertex of `sheets` closed sheets made by Mesh.sheet, in order."""
    uu, vv = [], []
    for _ in range(sheets):
        for i in range(nu + 1):
            for j in range(nv + 1):
                uu += [i / nu, i / nu]
                vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def vein_paths(side, nu, seed):
    """Branching lightning through each panel of one wing, as 3D polylines with a width at their root and at their end."""
    rng = np.random.default_rng(seed)
    point = membrane_point(side, nu)
    out = []
    panels = ((0.0, 0.3, (0.5,)), (0.3, 0.6, (0.5,)), (0.6, 1.0, (0.22, 0.52, 0.8)))
    for u0, u1, centres in panels:
        w = u1 - u0
        for c in centres:
            uv = [(u0 + w * c, 0.04)]
            sign = 1 if rng.random() < 0.5 else -1
            for k in range(1, 8):
                sign = -sign
                uv.append((u0 + w * float(np.clip(c + sign * rng.uniform(0.04, 0.11) * (len(centres) == 1 and 1.4 or 0.7), 0.06, 0.94)), 0.04 + 0.9 * k / 7))
            out.append(([Vector(point(u, v)) for u, v in uv], 0.0062, 0.0024))
            for k in (2, 3, 5):
                u, v = uv[k]
                go = 1 if rng.random() < 0.5 else -1
                br = [(u, v)]
                for j in range(1, 4):
                    br.append((float(np.clip(u + go * w * (0.08 * j + rng.uniform(-0.02, 0.02)), u0 + 0.02, u1 - 0.02)), min(0.97, v + (0.95 - v) * j / 4 + rng.uniform(-0.02, 0.02))))
                out.append(([Vector(point(a, b)) for a, b in br], 0.0038, 0.0016))
    return out


def paint_membranes(o, nu, nv):
    P, Nn = verts(o), normals(o)
    n = len(P)
    uu, vv = sheet_uv(nu, nv, 2)
    left = np.arange(n) < n // 2
    vein = np.zeros(n)
    halo = np.zeros(n)
    for side, sel in ((1, left), (-1, ~left)):
        Ps = P[sel]
        best = np.zeros(len(Ps))
        glow = np.zeros(len(Ps))
        for path, w0, w1 in vein_paths(side, nu, 7):           # the same pattern on both wings, mirrored
            f, d = nearest_on(path, Ps)
            w = w0 + (w1 - w0) * f
            best = np.maximum(best, 1 - smooth(w * 0.5, w, d))
            glow = np.maximum(glow, (1 - smooth(w * 0.8, w * 5.0, d)) * 0.8)
        vein[sel] = best
        halo[sel] = glow
    cloud = fbm(P, 9.0, 4, 31)
    col = mix(np.broadcast_to(MEMB_DEEP, (n, 3)), MEMB, smooth(0.0, 0.5, vv))
    col = mix(col, MEMB_CLOUD, smooth(0.5, 0.75, cloud) * 0.45 * smooth(0.2, 0.8, vv))           # storm cloud, lighter toward the torn edge
    col = mix(col, MEMB_CLOUD * 1.15, smooth(0.93, 1.0, vv) * 0.6)
    col = mix(col, rgb(196, 172, 104), halo * 0.5)
    col = mix(col, VEIN, vein)
    set_verts(o, P + Nn * (0.0005 * vein)[:, None])
    paint(o, np.clip(col, 0, 1), 0.55 - 0.25 * vein, np.zeros(n))


def paint_wing_bones(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    kind, along = read_tag(o, "kind"), read_tag(o, "along")
    d1, d2, own = cells_3d(P, 160.0, 3)
    scale = smooth(0.0, 0.14, d2 - d1)
    hide = mix(np.broadcast_to(HIDE, (n, 3)), HIDE_DEEP, smooth(0.0, 0.8, Nn[:, 2]) * 0.4)
    hide = mix(hide, HIDE_DEEP * 0.7, (1 - scale) * 0.35)
    finger = mix(np.broadcast_to(HIDE_DEEP, (n, 3)), HIDE, smooth(0.2, 0.9, Nn[:, 2]) * 0.6)
    oxide = smooth(0.55, 0.8, fbm(P, 60.0, 3, 21))
    copper = mix(mix(np.broadcast_to(COPPER, (n, 3)), COPPER_DEEP, oxide * 0.55), COPPER_BRIGHT, smooth(0.6, 1.0, along) * 0.35)
    knuckle = mix(np.broadcast_to(HIDE_DEEP, (n, 3)), IRON_PALE, 0.3)
    col = np.where((kind == 0)[:, None], hide, finger)
    col = np.where((kind == 1)[:, None], knuckle, col)
    col = np.where((kind == 3)[:, None], copper, col)
    paint(o, np.clip(col, 0, 1), np.where(kind == 3, 0.28 + 0.2 * oxide, 0.5), np.where(kind == 3, 0.9, 0.0))


def paint_horns(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    kind, along = read_tag(o, "kind"), read_tag(o, "along")
    oxide = smooth(0.55, 0.8, fbm(P * np.array((1.0, 2.5, 2.5)), 60.0, 3, 21))
    copper = mix(np.broadcast_to(COPPER, (n, 3)), COPPER_DEEP, oxide * 0.6 + smooth(0.15, 0.0, along) * 0.4)
    copper = mix(copper, COPPER_BRIGHT, smooth(0.3, 0.9, Nn[:, 2]) * 0.3)
    porcelain = mix(np.broadcast_to(PORCELAIN, (n, 3)), PORCELAIN_DEEP, smooth(-0.1, -0.8, Nn[:, 2]) * 0.6)
    iron = mix(np.broadcast_to(IRON, (n, 3)), EDGE, smooth(0.7, 1.0, along) * 0.6)
    col = np.where((kind == 0)[:, None], copper, porcelain)
    col = np.where((kind == 2)[:, None], iron, col)
    rough = np.where(kind == 0, 0.28 + 0.25 * oxide, np.where(kind == 1, 0.15, 0.35))
    paint(o, np.clip(col, 0, 1), rough, np.where(kind == 1, 0.0, 0.85))


def paint_claws(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    along = read_tag(o, "along")
    edge = np.maximum(smooth(0.35, 0.9, along) * smooth(0.1, 0.6, Nn[:, 2]), smooth(0.8, 1.0, along))     # honed bright along their backs and to their points
    col = mix(np.broadcast_to(IRON, (n, 3)), EDGE, edge * 0.85)
    col = mix(col, IRON_PALE, smooth(0.6, 0.85, fbm(P, 140.0, 2, 9)) * 0.3 * (1 - edge))
    paint(o, np.clip(col, 0, 1), 0.35 - 0.2 * edge, np.full(n, 0.85))


def paint_teeth(o):
    along = read_tag(o, "along")
    n = len(along)
    paint(o, mix(np.broadcast_to(TOOTH_ROOT, (n, 3)), TOOTH, smooth(0.15, 0.5, along)), np.full(n, 0.3), np.zeros(n))


def paint_blade(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    root, d, up = blade_frame()
    side = np.array(tuple(d.cross(up).normalized()))
    rim = (np.abs((P - np.array(tuple(root))) @ side) < 0.001).astype(float)           # its edge: the middle ring of the bevel
    oxide = smooth(0.5, 0.8, fbm(P, 50.0, 3, 23))
    col = mix(np.broadcast_to(COPPER, (n, 3)), COPPER_DEEP, oxide * 0.5)
    col = mix(col, EDGE, rim * 0.9)
    paint(o, np.clip(col, 0, 1), 0.3 + 0.2 * oxide - 0.15 * rim, np.full(n, 0.9))


def paint_all(pieces, frames, data):
    carve_skin(pieces["Skin"])
    paint_skin(pieces["Skin"])
    paint_membranes(pieces["Membranes"], MEMB_NU, MEMB_NV)
    paint_wing_bones(pieces["WingBones"])
    paint_horns(pieces["Horns"])
    paint_claws(pieces["Claws"])
    paint_teeth(pieces["Teeth"])
    paint_blade(pieces["Blade"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)


VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.25), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.12, 0.62)
FACE_AT = (0, -0.41, 1.0)
EXTRA = [(0.2, -1, 0.15, 0.6, FACE_AT), (0.9, -0.5, 0.2, 0.6, FACE_AT), (1, 0.1, 0.1, 1.2, (0.13, 0.12, 0.2)), (0.7, 0.4, 0.6, 1.6, (0.5, 0.15, 0.9)),
         (0.6, 0.8, 0.3, 1.0, (0.2, 0.85, 0.2))]

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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=4.4, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 4400
PIECES = ("Skin", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Membranes", "WingBones", "Claws", "Horns", "Teeth", "Blade")
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "LidUL": 1.2, "LidUR": 1.2, "LidLL": 1.2, "LidLR": 1.2, "Membranes": 0.62, "WingBones": 1.0, "Claws": 1.3, "Horns": 1.7,
          "Teeth": 1.5, "Blade": 1.3}
HEAD_LINE = (-0.3, 0.86)          # in front of y and above z: its head, which gets more of the atlas


def is_head(c):
    return c.y < HEAD_LINE[0] and c.z > HEAD_LINE[1]


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)                 # the soles back on the ground
    for fr in frames.values():
        # the socket's skin lying level with an eyeball: into the ball, where the eye hides it (level, they z-fight)
        c = np.array(tuple(fr.centre))
        d = np.linalg.norm(P - c, axis=1)
        band = np.abs(d - EYE_R) < 0.0018
        P[band] = c + (P[band] - c) / d[band, None] * (EYE_R - 0.002)
    set_verts(lows["Skin"], P)
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 20, 12)
        lows["LidU" + tag] = low_lid(fr, True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(fr, False, N + "LidL" + tag + "Low")
    lows["Membranes"] = build_membranes(N + "MembranesLow", GAME, *LOW_MEMB)
    uu, vv = sheet_uv(*LOW_MEMB, 2)
    edge_a = np.where(uu > SPLIT, (uu - SPLIT) / (1 - SPLIT), -1.0)
    at = lows["Membranes"].data.attributes.new("memb_a", "FLOAT", "POINT")
    at.data.foreach_set("value", edge_a)
    lows["WingBones"] = build_wing_bones(N + "WingBonesLow", GAME, sides=7, scale=0.42)
    lows["Claws"] = build_claws(N + "ClawsLow", GAME, sides=6)
    lows["Horns"] = decimated(pieces["Horns"], N + "HornsLow", 900)
    lows["Teeth"] = build_teeth(N + "TeethLow", GAME, sides=5, per=2)
    lows["Blade"] = decimated(pieces["Blade"], N + "BladeLow", 160)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    data["wb_kind"], data["wb_finger"], data["wb_along"] = (read_tag(lows["WingBones"], k) for k in ("kind", "finger", "along"))
    data["claw_owner"] = read_tag(lows["Claws"], "owner")
    triangulate(lows)
    # (triangulating keeps the vertices and their order: the tags read above still match)
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


UV_ANGLE = {"Skin": 66, "Horns": 50, "Blade": 40}     # the projection's angle per piece (wider: fewer, bigger charts, a fuller atlas)


def drake_unwrap(lows, margin=0.0035):
    """Each piece on its own: the projection's charts as seams (and one round its neck, where the head's share changes), an angle-based unwrap that
    can't fold a chart over itself, collapsed fragments projected again, each scaled to its share; all packed together."""
    for key, o in lows.items():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        select_only([o])
        if key == "Membranes":
            # each sheet's upper layer and its rim one island, its lower layer another: cut only where the rim meets the lower layer (the
            # projection cut every rim off in a thin strip that wasted the atlas). Mesh.sheet makes each point's upper vertex, then its lower.
            bm = bmesh.new()
            bm.from_mesh(o.data)
            per = (LOW_MEMB[0] + 1) * (LOW_MEMB[1] + 1) * 2
            lower = lambda v: (v.index % per) % 2 == 1
            for e in bm.edges:
                e.seam = len(e.link_faces) == 2 and all(lower(v) for v in e.verts) and any(not all(lower(v) for v in f.verts) for f in e.link_faces)
            bm.to_mesh(o.data)
            bm.free()
        else:
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
            # those islands cut finer and unwrapped again; what still folds or overlaps, projected flat
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
            scale_uv_to(o, [p for p in polys if is_head(p.center)], 1.8)
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


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD, SNOUT[-1]]       # rump to the end of the snout: the line every trunk weight is measured along
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Neck1", NECK[0], "Chest"),
               ("Neck2", path_at(NECK, 0.34), "Neck1"), ("Neck3", path_at(NECK, 0.68), "Neck2"), ("Head", NECK[-1], "Neck3"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.04, 0.2, 0.36, 0.52, 0.68, 0.84)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
LEG_NAMES = ("Leg%s1", "Leg%s2", "Leg%s3", "Foot%s")       # thigh, shin, the long bone of the foot, the foot and its toes
WING_NAMES = ("Wing%s1", "Wing%s2", "Wing%s3")             # upper arm, forearm, the hand; a bone per finger after it
SIDES = (("L", 1), ("R", -1))


def leg_bones(tag):
    return [n % tag for n in LEG_NAMES]


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for tag, fr in frames.items():
        bones += [("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    for tag, side in SIDES:
        parent = "Hips"
        for name, at in zip(leg_bones(tag), HIND):
            bones.append((name, mir(at, side), parent))
            parent = name
        root, elbow, wrist, tips, body = wing_frame(side)
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        bones += [(n1, root, "Chest"), (n2, elbow, n1), (n3, wrist, n2)]
        bones += [("Wing%sF%d" % (tag, j + 1), wrist.copy(), n3) for j in range(3)]
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


HEAD_ZONE = (V(0, -0.42, 0.99), (0.075, 0.12, 0.075))     # the head, snout and jaw: wholly the head's
LEG_KNOT_F = (0.0, 1 / 3, 2 / 3, 1.0)
LEG_MIDS = (1 / 6, 0.5, 5 / 6, 1.02)


def body_weights(P):
    """The skin's weights at any points: the trunk (hips to head), the head, the tail and the hind legs; a foot and its toes wholly its foot's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for tag, side in SIDES:
        f, d = nearest_on(leg_path(side), P)
        legs.append((tag, side, f, d))
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        # the foot and its toes are the foot's, handed over to the leg smoothly up the ankle (a hard line there tore when the foot turned)
        foot, foot_share = None, 0.0
        for tag, side, f, d in legs:
            if x * side > 0.03 and (Vector(P[i]) - mir(HIND[3], side)).length < 0.11:
                foot, foot_share = "Foot" + tag, float(smooth(0.085, 0.045, z))
        if foot_share >= 0.999:
            out.append({foot: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
        reach = prof(TAIL_PROFILE, float(tf[i])) * 1.1 + 0.012
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.0, 0.05, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        for tag, side, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(float(f[i])) + 0.014
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))       # by the hip the hand-over spreads wider: a swing stretches the flank over a span
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            if mm > 0:
                w = blend(w, chain_weight(leg_bones(tag), LEG_MIDS, float(f[i])), mm)
        if foot_share > 0:
            w = blend(w, {foot: 1.0}, foot_share)
        out.append(w)
    return out


def membrane_weights(nu, nv):
    """From where each vertex lies on its sheet. The hand's panels between their fingers' bones (wholly: the fingers fold back on the hand, and a share
    of the hand would tear the membrane by the wrist). The arm's panel: along the arm (v = 0) the arm's bones, the forearm right to the wrist; along the
    last finger (u = 0) that finger; along the back (u = 1) the chest and body; the torn edge (v = 1) from the finger to the back."""
    uu, vv = sheet_uv(nu, nv, 2)
    tags = ["L"] * (len(uu) // 2) + ["R"] * (len(uu) // 2)
    out = []
    for u, v, tag in zip(uu, vv, tags):
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        fingers = ["Wing%sF%d" % (tag, j + 1) for j in range(3)]
        if u <= SPLIT:
            a = 2 * u / SPLIT
            k = min(int(a), 1)
            t = float(smooth(0, 1, a - k))
            w = {fingers[k]: 1 - t, fingers[k + 1]: t}
        else:
            # the upper arm carries the whole inner sail (so it drops with the arm when the wing folds: carried half by the back, it stood up in a
            # flap); only a strip along its edge in the back is the back's
            a = (u - SPLIT) / (1 - SPLIT)                   # 0 at the last finger, 1 at the back
            arm = chain_weight([n2, n1], (0.5, 0.64), a)    # the forearm from the wrist to the elbow, then the upper arm
            trail = chain_weight([fingers[2], n1], (0.15, 0.6), a)       # the torn edge: the finger's out at its tip, the upper arm's in toward the back
            w = blend(arm, trail, float(smooth(0.0, 1.0, v)))
            w = blend(w, {fingers[2]: 1.0}, (1 - float(smooth(0.0, 0.16, a))) * float(smooth(0.0, 0.1, v)))       # held along the finger
            w = blend(w, {"Chest": 0.6, "Body": 0.4}, float(smooth(0.9, 1.0, a)))                                    # its edge in the back
        out.append(w)
    return out


def wing_bone_weights(kind, along, finger, P):
    out = []
    for k, f, j, p in zip(kind, along, finger, P):
        tag = "L" if p[0] > 0 else "R"
        n1, n2, n3 = (n % tag for n in WING_NAMES)
        if k == 0:
            out.append(chain_weight([n1, n2, n3], (0.44, 0.56, 0.985), float(f)))
        elif k == 1:
            out.append({n3: 1.0})
        else:
            out.append({"Wing%sF%d" % (tag, j + 1): 1.0})
    return out


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def game_glows(frames):
    return {"Tips": build_tips(N + "Tips_Glow_" + TIP_HEX, GAME, hi=False), "Arc": build_arc(N + "Arc_Glow_" + ARC_HEX, GAME, sides=4),
            "Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-22, 20, 0.0032, 8), (20, -18, 0.0015, 5)))}


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    weigh(lows["Membranes"], membrane_weights(*LOW_MEMB))
    weigh(lows["WingBones"], wing_bone_weights(data["wb_kind"], data["wb_along"], data["wb_finger"], verts(lows["WingBones"])))
    owners = ("FootL", "FootR", "WingL3", "WingR3")
    weigh(lows["Claws"], [{owners[k]: 1.0} for k in data["claw_owner"]])
    for tag in "LR":
        rigid(lows["Eye" + tag], "Head")
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Horns"], "Head")
    rigid(lows["Teeth"], "Head")
    rigid(lows["Blade"], TAIL_NAMES[-1])
    ends = [(horn_tip(side), "Head") for tag, side in SIDES] + [(spur_tip(side, k), "Wing%sF%d" % (tag, k + 1)) for tag, side in SIDES for k in range(3)]
    E = np.array([tuple(p) for p, _ in ends])
    weigh(glows["Tips"], [{ends[int(np.argmin(np.linalg.norm(E - p, axis=1)))][1]: 1.0} for p in verts(glows["Tips"])])
    rigid(glows["Arc"], "Head")
    rigid(glows["Glints"], "Head")
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses: solved in the model's own space, written as PetRig's tables (turns in the game's axes) ----------
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
I3 = Matrix.Identity(3)


def from_game(v):
    return CM @ (Matrix.Rotation(v[0], 3, "X") @ Matrix.Rotation(v[1], 3, "Y") @ Matrix.Rotation(v[2], 3, "Z")) @ CM


def to_game(R):
    e = (CM @ R @ CM).to_euler("ZYX")
    return (e.x, e.y, e.z)


def frame_rot(a, n, a2, n2):
    """The turn taking direction a to a2 and the plane normal n to n2 (n2 squared up against a2)."""
    a, a2 = a.normalized(), a2.normalized()
    n = (n - a * n.dot(a)).normalized()
    n2 = (n2 - a2 * n2.dot(a2)).normalized()
    F0 = Matrix((a, n, a.cross(n))).transposed()
    F1 = Matrix((a2, n2, a2.cross(n2))).transposed()
    return F1 @ F0.transposed()


class Rig:
    """The rest skeleton's heads and parents, for solving poses without Blender's depsgraph."""

    def __init__(self, rig):
        self.head = {b.name: b.head_local.copy() for b in rig.data.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
        self.order = [b.name for b in rig.data.bones]

    def fk(self, local, moves=None):
        """local: bone -> 3x3 turn in the model's axes about its head (its parent's turn first). Returns world turns and heads."""
        moves = moves or {}
        W, H = {}, {}
        for b in self.order:
            p = self.parent[b]
            R = local.get(b, I3)
            mv = moves.get(b, V(0, 0, 0))
            if p is None:
                W[b], H[b] = R, self.head[b] + mv
            else:
                W[b] = W[p] @ R
                H[b] = H[p] + W[p] @ (self.head[b] - self.head[p]) + W[p] @ mv
        return W, H


def solve_leg(rig, W, H, tag, side, target, foot_turn=None):
    """A hind leg reaching `target` with the ball of its foot: the thigh's turn (pitch and splay) and the knee, the long bone of the foot kept parallel
    to the thigh (a bird's leg, folding as a pantograph). Returns the local turns of its four bones."""
    names = leg_bones(tag)
    J = [mir(p, side) for p in HIND]
    Rp = W["Hips"]
    hip = H[names[0]] if names[0] in H else H["Hips"] + Rp @ (J[0] - rig.head["Hips"])
    hip = H["Hips"] + Rp @ (J[0] - rig.head["Hips"])

    def reach(x):
        a0, b0, a1 = x
        R1 = Matrix.Rotation(b0, 3, "Y") @ Matrix.Rotation(a0, 3, "X")
        R2 = R1 @ Matrix.Rotation(a1, 3, "X")
        k = hip + R1 @ (J[1] - J[0])
        h = k + R2 @ (J[2] - J[1])
        return h + R1 @ (J[3] - J[2]), R1, R2
    x = np.zeros(3)
    tgt = np.array(tuple(target))
    for _ in range(40):
        f0 = np.array(tuple(reach(x)[0])) - tgt
        if np.linalg.norm(f0) < 1e-6:
            break
        Jm = np.zeros((3, 3))
        for i in range(3):
            dx = np.zeros(3)
            dx[i] = 1e-5
            Jm[:, i] = (np.array(tuple(reach(x + dx)[0])) - tgt - f0) / 1e-5
        x = x - np.linalg.lstsq(Jm.T @ Jm + 1e-6 * np.eye(3), Jm.T @ f0, rcond=None)[0]
    end, R1, R2 = reach(x)
    err = (end - target).length
    Rf = foot_turn if foot_turn is not None else I3
    return {names[0]: Rp.inverted() @ R1, names[1]: Matrix.Rotation(x[2], 3, "X"), names[2]: Matrix.Rotation(-x[2], 3, "X"), names[3]: R1.inverted() @ Rf}, err


def solve_wing(rig, W, H, tag, side, wrist_to, pole, hook_dir, hook_up, finger_dirs, fan_normal):
    """A wing's arm reaching `wrist_to` with its wrist (the elbow bowed toward `pole`); its hand turned so the wrist's hook points along `hook_dir`
    (the fingers' fan's normal toward `hook_up`); each finger k turned to point along finger_dirs[k], their fan's normal toward `fan_normal`."""
    n1, n2, n3 = (n % tag for n in WING_NAMES)
    S, E, Wr, tips, body = wing_frame(side)
    Rc = W["Chest"]
    S2 = H["Chest"] + Rc @ (S - rig.head["Chest"])
    l1, l2 = (E - S).length, (Wr - E).length
    e = wrist_to - S2
    d = min(e.length, l1 + l2 - 1e-4)
    eh = e.normalized()
    cos_t = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    pp = (pole - eh * pole.dot(eh)).normalized()
    E2 = S2 + eh * (l1 * cos_t) + pp * (l1 * math.sqrt(1 - cos_t * cos_t))
    W2 = S2 + eh * d
    a, b = E - S, Wr - E
    n = a.cross(b)
    a2, b2 = E2 - S2, W2 - E2
    n_2 = a2.cross(b2)          # the elbow's hinge keeps its sense: the arm bends the way it does at rest, the pole saying where the elbow goes
    R1 = frame_rot(a, n, a2, n_2)
    R2 = frame_rot(b, n, b2, n_2)
    hook = catmull(wrist_hook(side), 4)
    h_rest = (hook[-1] - hook[0]).normalized()
    nf = (tips[0] - Wr).cross(tips[2] - Wr).normalized()
    R3 = frame_rot(h_rest, nf, hook_dir, hook_up)
    out = {n1: Rc.inverted() @ R1, n2: R1.inverted() @ R2, n3: R2.inverted() @ R3}
    if callable(finger_dirs):
        finger_dirs, fan_normal = finger_dirs(E2, W2)
    for k in range(3):
        Rk = frame_rot((tips[k] - Wr).normalized(), nf, finger_dirs[k], fan_normal)
        out["Wing%sF%d" % (tag, k + 1)] = R3.inverted() @ Rk
    return out, (W2 - wrist_to).length, E2, W2


def g(*v):
    return v


def game_vec(b):
    """A position or move in the model's axes, in the game's."""
    return (-b.x, b.z, b.y)


def blender_vec(gv):
    return V(-gv[0], gv[2], gv[1])


PROWL_TRUNK = {"Hips": g(-0.55, 0, 0, (0, -0.03, 0)), "Chest": g(0.05, 0, 0), "Neck1": g(0.32, 0, 0), "Neck2": g(0.2, 0, 0), "Head": g(0.02, 0, 0),
               "Tail1": g(0.26, 0, 0), "Tail2": g(0.12, 0, 0), "Tail3": g(0.04, 0, 0)}


def prowl_fingers(side, spread=(0.0, 0.16, 0.34)):
    """The hand folded back off the planted wrist, a bat's: the last finger along the forearm, past the elbow, the others fanned a little above it."""
    def dirs(E2, W2):
        along = (E2 - W2).normalized()
        out = V(side, 0, 0)
        lift = (V(0, 0, 1) - along * along.z).normalized()
        d = [(along + lift * spread[2 - k] + out * 0.06).normalized() for k in range(3)]
        return d, d[0].cross(d[2]).normalized() if d[0].cross(d[2]).length > 1e-4 else out
    return dirs


def prowl_wing(side, wrist=(0.2, -0.3), pole=(0.7, 0.7, 0.5), lift=0.0, dy=0.0):
    return dict(wrist_to=V(side * wrist[0], wrist[1] + dy, 0.037 + lift), pole=V(side * pole[0], pole[1], pole[2]), hook_dir=V(side * 0.1, -1, -0.04).normalized(),
                hook_up=V(0, 0, 1), finger_dirs=prowl_fingers(side), fan_normal=None)


def build_pose(rig_info, trunk, feet=None, wings=None, extra=None):
    """trunk: bone -> game turns (and a move), set first; feet: tag -> where the ball of that foot goes (else where it stands at rest); wings: tag ->
    the arguments of solve_wing (else no wing turns). extra: game turns laid over the result last (on bones the solvers did not set). Returns the
    pose as a game table, rounded as PetRig has it, and how far each solved limb missed its mark."""
    local, moves = {}, {}
    for b, v in trunk.items():
        local[b] = from_game(v)
        if len(v) > 3:
            moves[b] = blender_vec(v[3])
    W, H = rig_info.fk(local, moves)
    miss = {}
    for tag, side in SIDES:
        target = (feet or {}).get(tag, mir(HIND[3], side))
        legs, err = solve_leg(rig_info, W, H, tag, side, target)
        local.update(legs)
        miss["foot" + tag] = round(err, 5)
    W, H = rig_info.fk(local, moves)
    for tag, side in SIDES:
        if wings and tag in wings:
            res, err, E2, W2 = solve_wing(rig_info, W, H, tag, side, **wings[tag])
            local.update(res)
            miss["wrist" + tag] = round(err, 5)
    for b, v in (extra or {}).items():
        local[b] = from_game(v)
    table = {}
    for b, R in local.items():
        e = tuple(round(float(x), 4) for x in to_game(R))
        mv = moves.get(b)
        if max(abs(x) for x in e) < 1e-4 and mv is None:
            continue
        table[b] = e + ((tuple(round(float(x), 4) for x in game_vec(mv)),) if mv is not None else ())
    return table, miss


def spec(table):
    out = {}
    for bone, v in table.items():
        q = from_game(v).to_quaternion()
        axis, angle = q.to_axis_angle()
        mv = blender_vec(v[3]) if len(v) > 3 else V(0, 0, 0)
        out[bone] = (tuple(axis), math.degrees(angle), tuple(mv))
    return out


def slerp_tables(a, b, w):
    out = {}
    for bone in set(a) | set(b):
        va, vb = a.get(bone, (0, 0, 0)), b.get(bone, (0, 0, 0))
        q = from_game(va).to_quaternion().slerp(from_game(vb).to_quaternion(), w)
        ma = Vector(va[3] if len(va) > 3 else (0, 0, 0))
        mb = Vector(vb[3] if len(vb) > 3 else (0, 0, 0))
        R = q.to_matrix()
        out[bone] = to_game(R) + (tuple(ma.lerp(mb, w)),)
    return out


# ---------- checks ----------
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
    names = {gg.index: gg.name for gg in body.vertex_groups}
    out = []
    for v in body.data.vertices:
        best = max(v.groups, key=lambda gg: gg.weight, default=None)
        out.append(names[best.group] if best else "")
    return out


def face_pieces(body):
    a = np.zeros(len(body.data.polygons), dtype=int)
    body.data.attributes["piece"].data.foreach_get("value", a)
    return a


def pairs(co, tris, fa, fb):
    if not fa or not fb:
        return 0
    verts_l = [tuple(c) for c in co]
    ta = BVHTree.FromPolygons(verts_l, [tris[f] for f in fa])
    tb = BVHTree.FromPolygons(verts_l, [tris[f] for f in fb])
    return len(ta.overlap(tb))


class Checker:
    def __init__(self, body):
        self.body = body
        self.dom = dominant(body)
        self.fp = face_pieces(body)
        _, tris = posed(body)
        self.tris = tris
        P = lambda k: [i for i, p in enumerate(self.fp) if p == PIECES.index(k)]
        self.skin, self.memb, self.wb, self.claws = P("Skin"), P("Membranes"), P("WingBones"), P("Claws")
        d = self.dom
        self.hooks = [i for i in self.claws if d[tris[i][0]].startswith("Wing")]
        self.legs = [i for i in self.skin if all(d[v].startswith(("Leg", "Foot")) for v in tris[i])]
        self.trunk = [i for i in self.skin if all(not d[v].startswith(("Leg", "Foot", "Tail")) for v in tris[i])]
        self.tail = [i for i in self.skin if all(d[v].startswith("Tail") for v in tris[i])]
        self.head = [i for i in self.skin if all(d[v] in ("Head", "Neck3") for v in tris[i])]
        # the membrane's faces away from its edge in the back (buried there by design)
        ma = np.zeros(len(body.data.vertices))
        body.data.attributes["memb_a"].data.foreach_get("value", ma)
        self.memb_free = [i for i in self.memb if all(ma[v] < 0.86 for v in tris[i])]
        self.wb_free = [i for i in self.wb if all(d[v] not in ("WingL1", "WingR1") for v in tris[i])]
        self.vpiece = np.full(len(body.data.vertices), -1)
        for i, t in enumerate(tris):
            for v in t:
                self.vpiece[v] = self.fp[i]
        self.side = np.array([1 if v.co.x > 0 else -1 for v in body.data.vertices])

    def run(self):
        co, tris = posed(self.body)
        d = self.dom
        out = {}
        out["membrane x trunk"] = pairs(co, tris, self.memb_free, self.trunk)
        out["membrane x legs"] = pairs(co, tris, self.memb, self.legs)
        out["membrane x tail"] = pairs(co, tris, self.memb, self.tail)
        out["membrane x head"] = pairs(co, tris, self.memb, self.head)
        out["wing x legs"] = pairs(co, tris, self.wb + self.hooks, self.legs)
        out["wing x trunk"] = pairs(co, tris, self.wb_free, self.trunk)
        L = [i for i in self.memb if self.side[tris[i][0]] > 0]
        R = [i for i in self.memb if self.side[tris[i][0]] < 0]
        out["membrane L x R"] = pairs(co, tris, L, R)
        out["leg x leg"] = pairs(co, tris, [i for i in self.legs if self.side[tris[i][0]] > 0], [i for i in self.legs if self.side[tris[i][0]] < 0])
        WL = [i for i in self.wb + self.memb if self.side[tris[i][0]] > 0]
        WR = [i for i in self.wb + self.memb if self.side[tris[i][0]] < 0]
        out["wing L x R"] = pairs(co, tris, WL, WR)
        out["tail x legs"] = pairs(co, tris, self.tail, self.legs)
        feet = np.array([x.startswith("Foot") for x in d]) & (self.vpiece == PIECES.index("Skin"))
        out["feet z"] = round(float(co[feet, 2].min()), 4)
        claws = self.vpiece == PIECES.index("Claws")
        out["claws z"] = round(float(co[claws, 2].min()), 4)
        wb = self.vpiece == PIECES.index("WingBones")
        out["wings z"] = round(float(co[wb, 2].min()), 4)
        memb = self.vpiece == PIECES.index("Membranes")
        out["membrane z"] = round(float(co[memb, 2].min()), 4)
        rest = (self.vpiece == PIECES.index("Skin")) & ~np.array([x.startswith(("Foot", "Leg")) for x in d])
        out["lowest else"] = round(float(co[rest, 2].min()), 4)
        return out


BASE_KEYS = ("membrane x trunk", "wing x trunk")       # buried at rest by design: judged against the rest pose's own count


def level_head(ri, trunk, pitch=0.0):
    """The head's own turn that leaves it pitched `pitch` (game turns about X) in the world, whatever the neck does."""
    local = {b: from_game(v) for b, v in trunk.items() if b != "Head"}
    W, _ = ri.fk(local)
    return to_game(W["Neck3"].inverted() @ from_game((pitch, 0, 0)))


WALK = {"foot": 0.11, "foot_lift": 0.05, "wrist": 0.13, "wrist_lift": 0.06, "bob": 0.012, "keys": 8}
LEADS = {"wristL": 0.0, "footR": 0.0, "wristR": math.pi, "footL": math.pi}       # diagonal pairs: a wrist with the opposite foot


def walk_pose(ri, phi):
    """The prowl, stepping: each foot and wrist goes back along the ground while it is down (the half where sin >= 0) and swings forward lifted (the
    other half); the hips bob twice a cycle and roll a little over the foot that is down; the tail swings against the step."""
    trunk = dict(PROWL_TRUNK)
    hips = list(trunk["Hips"])
    hips[2] = 0.03 * math.sin(phi)
    hips[3] = (0, -0.03 + WALK["bob"] * math.cos(2 * phi), 0)
    trunk["Hips"] = tuple(hips)
    for k in range(1, 5):
        trunk["Tail%d" % k] = (trunk.get("Tail%d" % k, (0, 0, 0))[0], 0.06 * math.sin(phi + 0.7 * k), 0)
    trunk["Head"] = (0.02, -0.03 * math.sin(phi), 0)
    feet, wings = {}, {}
    for tag, side in SIDES:
        p = phi + LEADS["foot" + tag]
        f = WALK["foot"] / 2 * math.cos(p)
        feet[tag] = mir(HIND[3], side) + V(0, -f, WALK["foot_lift"] * max(0.0, -math.sin(p)))
        p = phi + LEADS["wrist" + tag]
        f = WALK["wrist"] / 2 * math.cos(p)
        wings[tag] = prowl_wing(side, lift=WALK["wrist_lift"] * max(0.0, -math.sin(p)), dy=-f)
    return build_pose(ri, trunk, feet=feet, wings=wings)


def wing_turns(lift=0.0, sweep=0.0, elbow=0.0, hand=0.0, fan=0.0):
    """Both wings from their spread rest: lift raises the whole wing (a turn about the body's length), sweep swings it forward (+) or back, elbow and
    hand fold it, fan opens (+) or closes the fingers about the middle one."""
    out = {}
    for tag, sign in SIDES:
        out["Wing%s1" % tag] = (0, sweep * sign, -lift * sign)
        if elbow:
            out["Wing%s2" % tag] = (0, elbow * sign, 0)
        if hand:
            out["Wing%s3" % tag] = (0, hand * sign, 0)
        if fan:
            out["Wing%sF1" % tag] = (0, fan * sign, 0)
            out["Wing%sF3" % tag] = (0, -fan * sign, 0)
    return out


FLY_TRUNK = {"Hips": g(-0.32, 0, 0), "Neck1": g(-0.28, 0, 0), "Neck2": g(-0.08, 0, 0), "Neck3": g(0.12, 0, 0),
             "Tail1": g(-0.1, 0, 0), "Tail2": g(-0.04, 0, 0), "Tail3": g(0.02, 0, 0), "Tail4": g(0.03, 0, 0)}
TUCK = {"LegL1": g(-1.05, 0, 0), "LegL2": g(1.0, 0, 0), "LegL3": g(-0.55, 0, 0), "FootL": g(-0.55, 0, 0),
        "LegR1": g(-1.05, 0, 0), "LegR2": g(1.0, 0, 0), "LegR3": g(-0.55, 0, 0), "FootR": g(-0.55, 0, 0)}
REAR_TRUNK = {"Hips": g(0.12, 0, 0, (0, 0.02, 0)), "Body": g(0.08, 0, 0), "Chest": g(0.05, 0, 0), "Neck1": g(0.05, 0, 0), "Neck2": g(0.1, 0, 0),
              "Tail1": g(-0.12, 0, 0), "Tail2": g(-0.06, 0, 0)}


def slam_wing(side):
    """Slammed down onto its wrists, its hands flung open into a canopy over it: the fingers spread wide, up and out (a raptor mantling over its prey),
    their glowing tips raised to the sky."""
    def dirs(E2, W2):
        along = (E2 - W2).normalized()
        out = V(side, 0, 0)
        up = V(0, 0, 1)
        d3 = (along + out * 0.45 + V(0, 0.25, 0)).normalized()
        d2 = (along * 0.3 + out * 0.75 + up * 0.75).normalized()
        d1 = (out * 0.55 + up + V(0, -0.35, 0)).normalized()
        return [d1, d2, d3], d1.cross(d3).normalized()
    w = prowl_wing(side, wrist=(0.22, -0.34))
    w["finger_dirs"] = dirs
    return w


SLAM_TRUNK = {"Hips": g(-0.6, 0, 0, (0, -0.05, 0)), "Chest": g(0.0, 0, 0), "Neck1": g(0.2, 0, 0), "Neck2": g(0.16, 0, 0), "Neck3": g(0.04, 0, 0),
              "Tail1": g(0.3, 0, 0), "Tail2": g(0.16, 0, 0), "Tail3": g(0.06, 0, 0)}


def pose_tables(ri):
    t = {}
    misses = {}
    prowl = dict(PROWL_TRUNK)
    t["Prowl"], misses["Prowl"] = build_pose(ri, prowl, wings={tag: prowl_wing(side) for tag, side in SIDES})
    for k in range(WALK["keys"]):
        t["Walk%d" % k], misses["Walk%d" % k] = walk_pose(ri, 2 * math.pi * k / WALK["keys"])
    fly = dict(FLY_TRUNK)
    fly["Head"] = level_head(ri, fly, -0.12)
    base, misses["Fly"] = build_pose(ri, fly, extra=TUCK)
    for b in TUCK:
        base[b] = tuple(round(x, 4) for x in TUCK[b])
    t["Fly"] = dict(base)
    t["BeatUp"] = {**base, **{k: tuple(round(x, 4) for x in v) for k, v in wing_turns(lift=0.38, sweep=-0.08).items()}}
    t["BeatDown"] = {**base, **{k: tuple(round(x, 4) for x in v) for k, v in wing_turns(lift=-0.6, sweep=0.1, hand=0.25).items()}}
    rear = dict(REAR_TRUNK)
    rear["Neck3"] = g(0.12, 0, 0)
    rear["Head"] = level_head(ri, rear, 0.45)
    t["Rear"], misses["Rear"] = build_pose(ri, rear, extra={k: v for k, v in wing_turns(lift=0.32, sweep=0.12, fan=0.12).items()})
    slam = dict(SLAM_TRUNK)
    slam["Head"] = level_head(ri, slam, -0.12)
    t["Slam"], misses["Slam"] = build_pose(ri, slam, wings={tag: slam_wing(side) for tag, side in SIDES})
    mantle = {tag: dict(prowl_wing(side)) for tag, side in SIDES}
    for tag, side in SIDES:
        mantle[tag]["finger_dirs"] = prowl_fingers(side, spread=(0.0, 0.42, 0.85))
    t["Mantle"], misses["Mantle"] = build_pose(ri, prowl, wings=mantle)
    # waypoints, so a folded wing never swings through its body: it lifts clear folded first, then opens (and the other way about)
    lift = {"Hips": g(-0.3, 0, 0, (0, -0.01, 0)), "Chest": g(0.03, 0, 0), "Neck1": g(0.18, 0, 0), "Neck2": g(0.12, 0, 0), "Head": g(0.0, 0, 0),
            "Tail1": g(0.12, 0, 0), "Tail2": g(0.05, 0, 0)}
    def lift_fingers(side):
        def dirs(E2, W2):
            along = (E2 - W2).normalized()
            d = [V(side * 0.45, 0.55, 0.7), V(side * 0.42, 0.8, 0.36), (along * LIFT_F3 + V(side * 0.3, 0.9, 0.1).normalized() * (1 - LIFT_F3))]
            d = [x.normalized() for x in d]
            return d, d[0].cross(d[2]).normalized()
        return dirs
    wings = {}
    for tag, side in SIDES:
        w = prowl_wing(side)
        w["wrist_to"] = V(side * 0.4, -0.24, 0.42)
        w["pole"] = V(side * 0.6, 0.6, 0.9)
        w["hook_dir"] = V(side * 0.2, -1, 0.1).normalized()
        w["finger_dirs"] = lift_fingers(side)
        wings[tag] = w
    t["Lift"], misses["Lift"] = build_pose(ri, lift, wings=wings)
    look = dict(prowl)
    look.update({"Neck2": g(0.2, 0.3, 0), "Neck3": g(0.05, 0.3, 0), "Head": g(0.02, 0.35, 0.1)})
    t["Look"], misses["Look"] = build_pose(ri, look, wings={tag: prowl_wing(side) for tag, side in SIDES})
    for name, m in misses.items():
        bad = {k: v for k, v in m.items() if v > 1e-3}
        if bad:
            print("MISS", name, bad, flush=True)
    return t


TRANSITIONS = (("Prowl", "Walk0"), ("Walk0", "Walk1"), ("Walk1", "Walk2"), ("Walk2", "Walk3"), ("Walk3", "Walk4"), ("Walk4", "Walk5"), ("Walk5", "Walk6"),
               ("Walk6", "Walk7"), ("Walk7", "Walk0"), ("Prowl", "Mantle"), ("Prowl", "Look"), ("Mantle", "Look"),
               ("Prowl", "Lift"), ("Walk0", "Lift"), ("Walk2", "Lift"), ("Walk4", "Lift"), ("Walk6", "Lift"), ("Lift", "FlyUp"), ("Lift", "FlyDown"),
               ("Fly", "BeatUp"), ("Fly", "BeatDown"), ("BeatUp", "BeatDown"),
               ("Lift", "Rear"), ("Rear", "Lift"), ("Lift", "Slam"), ("Slam", "Prowl"), ("Slam", "Walk0"), ("Mantle", "Lift"))
WORST_MIN = ("feet z", "claws z", "wings z", "membrane z", "lowest else")


LIFT_F3 = 0.35              # the waypoint's last finger: this share of the way to lying along the forearm (spread wider, the membrane stretched 4x)
HOVER = 0.3                 # metres it rises off the ground on the wing (PetRig: TW.HOVER)
BEAT_IN = (0.85, 1.0)       # its wings start to beat only once they are open: over this stretch of its rise (PetRig: TW.BEAT_IN)


def hover_at(air):
    return HOVER * float(smooth(0.35, 0.9, air))


def staged(tables, na, nb, w):
    """The blend the game makes from stance na to nb at w, and how high it hovers then. Taking off: from the ground to the waypoint over the first half of
    its rise (air 0 to 0.5), on to the open wing over the second, beating once open (FlyUp, FlyDown: at the top and the bottom of the stroke)."""
    if nb in ("FlyUp", "FlyDown"):
        air = 0.5 + 0.5 * w
        beat = float(smooth(BEAT_IN[0], BEAT_IN[1], air))
        stroke = tables["BeatUp" if nb == "FlyUp" else "BeatDown"]
        return slerp_tables(tables[na], slerp_tables(tables["Fly"], stroke, beat), w), hover_at(air)
    if nb == "Lift" and na.startswith(("Prowl", "Walk")):
        return slerp_tables(tables[na], tables[nb], w), hover_at(0.5 * w)
    return slerp_tables(tables[na], tables[nb], w), 0.0


def check_transitions(rig, chk, tables, rest, which=None):
    for na, nb in which or TRANSITIONS:
        worst = {}
        for k in range(11):
            table, hover = staged(tables, na, nb, k / 10)
            pose(rig, spec(table))
            r = chk.run()
            for key in WORST_MIN:
                r[key] = round(r[key] + hover, 4)
            for key, v in r.items():
                worst[key] = min(worst.get(key, 9.0), v) if key in WORST_MIN else max(worst.get(key, 0), v)
        flag = {k: v for k, v in worst.items() if (k not in WORST_MIN and v > 0) or (k in ("claws z", "wings z") and v < -0.002)}
        print("TRANSITION", na, "->", nb, flag if flag else "clean", "| lows", {k: worst[k] for k in WORST_MIN}, flush=True)


CLOSE_VIEWS = [(0.3, 1, 0.9, 1.4, (0, 0.0, 0.5)), (1, 0.3, 0.4, 1.4, (0.15, 0.0, 0.4)), (0.8, -0.6, 0.6, 1.4, (0.15, -0.1, 0.45)),
               (1, 0.1, -0.1, 1.1, (0.13, 0.3, 0.32)), (0.6, 0.8, -0.3, 1.1, (0.13, 0.3, 0.32)), (1, -0.2, -0.3, 1.0, (0, -0.45, 0.85))]
POSE_VIEWS = [(0.62, -0.72, 0.3, 3.8, (0, 0.05, 0.5)), (1, -0.05, 0.08, 3.8, (0, 0.05, 0.5)), (-0.3, -1, 0.25, 3.8, (0, 0.05, 0.5)), (0.2, 0.9, 0.5, 3.8, (0, 0.05, 0.5))]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    if STAGE == "all":
        drake_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.3, 0.32, 0.42, 1), far=("Skin",), reach=(0.003, 0.008),
                 far_reach=(0.006, 0.016), reaches={"Claws": (0.0015, 0.004), "Horns": (0.0015, 0.004), "Teeth": (0.0012, 0.003), "Blade": (0.0015, 0.004),
                                                    "WingBones": (0.002, 0.006), "Membranes": (0.0025, 0.007)})
    else:
        clay = bpy.data.materials.new("clay")
        gg = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        gg.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
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
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    ri = Rig(rig)
    chk = Checker(body)
    pose(rig, {})
    rest = chk.run()
    print("POSE Rest", rest, flush=True)
    tables = pose_tables(ri)
    if "only" in ARGS:
        keep = ARGS[ARGS.index("only") + 1].split(",")
        tables = {k: v for k, v in tables.items() if k in keep}
    for name, table in tables.items():
        pose(rig, spec(table))
        r = chk.run()
        print("POSE", name, r, flush=True)
        co, _ = posed(body)
        wbv = np.where(chk.vpiece == PIECES.index("WingBones"))[0]
        low = wbv[np.argmin(co[wbv, 2])]
        print("  lowest wing vertex", chk.dom[low], tuple(round(float(x), 3) for x in co[low]), flush=True)
        if STAGE == "rig" and "noshots" not in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS + (CLOSE_VIEWS if "close" in ARGS else []), size=480)
    if "transitions" in ARGS or STAGE == "all":
        check_transitions(rig, chk, tables, rest)
    lib = {k: spec(v) for k, v in tables.items()}
    for tag, fr in frames.items():
        lib.setdefault("Blink", {})["LidU" + tag] = (tuple(fr.hinge), -40.0, (0, 0, 0))
        lib["Blink"]["LidL" + tag] = (tuple(fr.hinge), 16.0, (0, 0, 0))
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    if "tables" in ARGS or STAGE == "all":
        for name, table in tables.items():
            print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join(("%g" % x) if not isinstance(x, tuple) else ("%g, %g, %g" % x) for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
        for tag, fr in frames.items():
            h = fr.hinge
            print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
        for name in ("Hips", "Head", "WingL3", "WingLF1", "Tail6"):
            p = rig.data.bones[name].head_local
            print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=4.4, size=560)
        for name in ("Prowl", "Walk2", "Fly", "BeatDown", "Rear", "Slam", "Mantle", "Lift"):
            pose(rig, spec(tables[name]))
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS[:2], size=480)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 4.4, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

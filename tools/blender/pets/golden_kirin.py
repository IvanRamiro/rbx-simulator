"""The Golden Kirin (Legendary, Nature; Beginner Qi Egg): "A white-furred qilin that treads the air on clouds of its own making. Old stories say it never
steps on a living blade of grass."

Recreated (November 9, 2026; the old model was a low-poly white beast hung with teal curls): a radiant celestial kirin (the owner's choice, after a
gilded-scale guardian was turned down), in a design language of its own: sunlight and silk. A slender, graceful qilin with a pearl-white coat, its legs
dipped in gold from the knees down as if it had waded in sunlight, and gold scroll marks (the qilin's flame-scrolls, drawn as a calligrapher would) on its
shoulders and haunches. A fine qilin's head with big golden sun-eyes, two slender gold horns curving back like crescent moons, small leaf ears tipped in
gold, and two long golden barbels trailing from its lips like a dragon's. Its mane and tail are long silky ribbons of gold going to pale light at their
ends, rippling as if in a breeze that touches nothing else, and silky ribbons of the same trail from behind its fetlocks. A glowing sunburst arc stands
behind its head. Its gold hooves never touch the ground: under each one a lotus of light opens on the air.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/golden_kirin.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, the lotuses on the ground (z = 0), its hooves LIFT above them. +X is its left. The maps go to assets/pets/BeginnerQiEgg/.

What touches what: body, neck, head, legs, hooves and the shaft of the tail are one fused skin; the eyes sit in their sockets under their lids; the ears,
horns, barbels and the ribbons of the mane, tail and fetlocks root inside the skin and lie off it along their length; the sunburst (a glow piece) floats
behind its head on the head's bone; each lotus (a glow piece) floats under its hoof.
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
PET = "GoldenKirin"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: pearl, sunlight and silk ----------
COAT, COAT_SHADE, COAT_SHEEN = rgb(250, 246, 236), rgb(218, 206, 186), rgb(255, 252, 244)
GOLD, GOLD_DEEP, GOLD_PALE, GOLD_LIGHT = rgb(236, 180, 64), rgb(176, 112, 28), rgb(252, 220, 132), rgb(255, 244, 206)
NOSE_COL, MOUTH, LASH = rgb(206, 150, 84), rgb(110, 58, 36), rgb(150, 96, 30)
EAR_IN = rgb(250, 222, 200)
GLINT_HEX = "fffaf0"
HALO_HEX = "ffe7a0"
LOTUS_HEX = "ffd986"

# ---------- the frame of it ----------
LIFT = 0.06                              # its soles this high over the ground: a lotus of light under each


def P(x, y, z):
    return V(x, y, z + LIFT)


def U(x, y, z):
    """The body: set lower on its legs than first drawn (long-legged, it read as a gazelle)."""
    return V(x, y, z + LIFT - 0.19)


HEAD0 = V(0, -0.385, 0.995)              # the head's centre as its parts were laid out
HEAD_AT = V(0, -0.415, 0.995 + LIFT - 0.275)
HS = 1.18                                # and how much bigger it is than laid out: a young, big-headed face


def H(x, y, z):
    """A point on the head as laid out, set on its neck, lower and bigger."""
    return HEAD_AT + (V(x, y, z) - HEAD0) * HS


def laid(Pv):
    """Points back to the head as it was laid out (for painting its face)."""
    return np.array(tuple(HEAD0)) + (Pv - np.array(tuple(HEAD_AT))) / HS


SPINE = [U(0, 0.28, 0.56), U(0, 0.16, 0.585), U(0, 0.04, 0.578), U(0, -0.08, 0.585), U(0, -0.18, 0.62), U(0, -0.25, 0.665)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.108), (0.15, 0.128), (0.4, 0.114), (0.65, 0.122), (0.85, 0.13), (1, 0.114))      # half-widths, rump to withers: a slender waist
BODY_H = ((0, 0.104), (0.15, 0.126), (0.4, 0.118), (0.65, 0.138), (0.85, 0.152), (1, 0.132))     # half-heights
BODY_DROP = ((0, 0.0), (0.15, 0.01), (0.4, 0.026), (0.65, 0.04), (0.85, 0.046), (1, 0.03))     # the loft's centre below the spine: a deep chest
NECK = catmull([U(0, -0.25, 0.665), U(0, -0.315, 0.74), U(0, -0.36, 0.81), U(0, -0.385, 0.86)], 10)     # arched forward, the head carried out in front: upright, it read as a llama
NECK_R = ((0, 0.12), (0.5, 0.094), (1, 0.078))
HEAD = H(0, -0.385, 0.995)
HEAD_R = (0.078 * HS, 0.086 * HS, 0.075 * HS)           # big and round for its size: a young, kind face
MUZZLE = [H(0, -0.43, 0.982), H(0, -0.463, 0.972), H(0, -0.488, 0.966)]     # short, broad and full: a dragon cub's, not a beak
JAW = [H(0, -0.41, 0.958), H(0, -0.44, 0.948), H(0, -0.466, 0.944)]
TAIL = catmull([U(0, 0.31, 0.565), U(0, 0.365, 0.53), U(0, 0.41, 0.475), U(0, 0.46, 0.45), U(0, 0.51, 0.47)], 8)     # a lion's tail, its tuft silk
FRONT = [U(0.078, -0.18, 0.53), U(0.086, -0.158, 0.44), P(0.077, -0.17, 0.14), P(0.072, -0.175, 0.07), P(0.072, -0.183, 0.032)]
HIND = [U(0.084, 0.2, 0.52), U(0.094, 0.13, 0.43), P(0.081, 0.228, 0.15), P(0.076, 0.222, 0.07), P(0.076, 0.217, 0.032)]
FRONT_R = [0.08, 0.058, 0.04, 0.033, 0.035]
HIND_R = [0.104, 0.072, 0.041, 0.033, 0.035]
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
EYE_R = 0.026 * HS
EYE_C = H(0.048, -0.436, 1.01)
EYE_AXIS = V(0.6, -0.78, 0.12).normalized()        # set forward on the face more than a deer's: it looks at you
LID_UP, LID_LOW = (38.0, 118.0, 0.0026), (-44.0, -126.0, 0.0022)      # wide open, gentle
LID_TILT = 3.0
BLINK_U, BLINK_L = 56.0, 28.0
IRIS = 0.9
PUPIL = 0.36                             # round
# the horns (its left; mirrored): a dragon's, laid back flat along its head, the tips turning up (rising off the crown they read as a goat's)
HORN = [H(0.034, -0.415, 1.055), H(0.044, -0.385, 1.077), H(0.056, -0.34, 1.088), H(0.068, -0.29, 1.09), H(0.076, -0.248, 1.104)]
HORN_R = ((0, 0.015 * HS), (0.35, 0.012 * HS), (0.75, 0.0072 * HS), (1, 0.003 * HS))
BARBEL = [H(0.026, -0.482, 0.966), H(0.062, -0.478, 0.955), H(0.104, -0.462, 0.932), H(0.138, -0.432, 0.922), H(0.162, -0.398, 0.93), H(0.176, -0.366, 0.948)]     # well off the neck
BARBEL_R = ((0, 0.0052 * HS), (0.25, 0.0042 * HS), (1, 0.0016 * HS))
HALO_C, HALO_R, HALO_SPAN = H(0, -0.3, 1.08), 0.15 * HS, 128.0     # the sunburst behind its head: an arc, open below over its neck
EAR = {"front": H(0.058, -0.366, 1.036), "back": H(0.07, -0.344, 1.026), "height": 0.052 * HS}


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


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40, flat=0.9)
    core.ball(SPINE[0] + V(0, 0.004, -0.008), (0.092, 0.078, 0.094))                      # the rump
    core.ball(U(0, -0.27, 0.56), (0.084, 0.07, 0.095))                                     # the breast
    for side in (1, -1):
        core.ball(U(side * 0.07, -0.17, 0.55), (0.058, 0.086, 0.094))                      # the shoulder
        core.ball(U(side * 0.08, 0.19, 0.51), (0.074, 0.104, 0.106))                       # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.007, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 40, 28)                                                         # the cranium
    fine.ball(H(0, -0.415, 1.025), (0.06 * HS, 0.06 * HS, 0.05 * HS))                       # a high, round brow
    fine.tube(catmull(MUZZLE, 6), lambda f: (0.042 - 0.008 * f) * HS, sides=28, flat=1.1)    # a small button muzzle, as a young dragon's
    fine.ball(MUZZLE[-1], (0.037 * HS, 0.026 * HS, 0.034 * HS))                               # its end rounded (the tube's flat cap read as a pig's snout)
    fine.ball(H(0, -0.493, 0.982), (0.026 * HS, 0.017 * HS, 0.016 * HS))                     # the nose on top of it, turned up a little
    fine.tube(catmull(JAW, 6), lambda f: (0.03 - 0.008 * f) * HS, sides=24, flat=1.0)        # the lower jaw, tucked under
    fine.ball(JAW[-1], (0.022 * HS, 0.018 * HS, 0.02 * HS))                                    # the round chin
    # the seam between muzzle and jaw filled: left as a deep groove it baked as a jagged dark line; the mouth is painted, a soft smile
    fine.tube(catmull([H(-0.034, -0.418, 0.957), H(-0.03, -0.45, 0.952), H(0, -0.474, 0.948), H(0.03, -0.45, 0.952), H(0.034, -0.418, 0.957)], 8),
              lambda f: 0.013 * HS, sides=20)
    for side in (1, -1):
        fine.ball(H(side * 0.036, -0.43, 0.975), (0.034 * HS, 0.046 * HS, 0.034 * HS))                     # the cheek
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(H(side * 0.041, -0.431, 1.036), (0.026 * HS, 0.03 * HS, 0.014 * HS))                     # the brow: the lids' hidden edges stay under it
        fine.ball(mir(HORN[0], side) + V(0, 0, -0.006), (0.016 * HS, 0.016 * HS, 0.013 * HS), 20, 12)      # the knob the horn grows from
    for key, side, knots, radii in LEGS:
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=24, flat=0.9)
        fine.ball(mir(knots[3], side) + V(0, 0.004, 0), (0.03, 0.033, 0.03), 18, 12)        # the fetlock
        hoof = mir(knots[4], side)
        fine.ball(hoof + V(0, -0.005, -0.004), (0.032, 0.038, 0.034), 20, 14)              # the hoof, cloven in paint
    fine.tube(TAIL, lambda f: 0.026 - 0.012 * f, sides=20)                                   # the shaft of the tail
    fine.ball(TAIL[-1], (0.016, 0.016, 0.016), 16, 10)
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


# ---------- ears ----------
def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    want = V(side * 0.8, 0.6, 0.12)                        # out and back, under the horns: a dragon's leaf ear
    up = (want - along * want.dot(along)).normalized()
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n
    return A, B, C, along, up, n


def ear_point(side):
    """A small leaf ear: its base along the head, its rim an arc to a pointed tip; u from the base to the rim, v across."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        s = math.sin(math.pi * v)
        rim = C + along * (-math.cos(math.pi * v) * a * 1.3) + up * (s ** 1.2 * EAR["height"] + 0.006)
        p = base.lerp(rim, u)
        cup = 0.008 * s * math.sin(math.pi * min(1.0, u * 1.1))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return (0.006 * (1 - u) ** 0.7 + 0.0022) * HS


def sheet_uv(nu, nv):
    uu, vv = [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            uu += [i / nu, i / nu]
            vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def build_ear(side, name):
    """Pearl behind, a warm blush in the hollow, the tip dipped in gold."""
    nu, nv = 60, 60
    o = sheet_hi(ear_point(side), ear_thick, nu, nv, name, lambda u, v: np.broadcast_to(COAT, (len(u), 3)), lambda u, v: np.full_like(u, 0.6),
                 lambda u, v: np.zeros_like(u))
    uu, vv = sheet_uv(nu, nv)
    Nn = normals(o)
    _, _, _, _, _, n = ear_frame(side)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(n)))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.6)
    col = mix(np.broadcast_to(COAT, (len(uu), 3)), EAR_IN, inside * smooth(0.03, 0.08, edge) * 0.8)
    tip = smooth(0.55, 0.8, uu) * (1 - smooth(0.12, 0.3, np.abs(vv - 0.5)) * 0.4)
    col = mix(col, mix(GOLD, GOLD_PALE, smooth(0.8, 1.0, uu)), smooth(0.4, 0.9, tip))
    paint(o, col, np.full(len(uu), 0.55), np.where(tip > 0.5, 0.6, 0.0))
    return o


# ---------- horns, barbels ----------
def build_horns(name, coll, sides=24, per=10):
    """Each vertex carries how far along its horn it is ("along")."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.float.new("along")
    al = bm.verts.layers.float["along"]
    for side in (1, -1):
        for knots, radii, offset in ((HORN, HORN_R, 0.0),):
            path = catmull([mir(p, side) for p in knots], per)

            def r(f, radii=radii, main=knots is HORN):
                ring = 0.0011 * max(0.0, math.cos(math.pi * 2 * 3 * f)) ** 8 * (1 - smooth(0.0, 0.5, f)) if main else 0.0    # fine rings at its root
                return prof(radii, f) + ring
            before = set(bm.verts)
            m.tube(path, r, sides=sides)
            m.ball(path[-1], (radii[-1][1] * 1.3,) * 3, sides, max(6, sides // 2))     # a touch wider than the end: they don't lie level
            new = [v for v in bm.verts if v not in before]
            f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
            for v, ff in zip(new, f):
                v[al] = offset + (1 - offset) * float(ff)
    return m.finish(name, coll)


def build_barbels(name, coll, sides=12, per=8):
    m = Mesh()
    for side in (1, -1):
        m.tube(catmull([mir(p, side) for p in BARBEL], per), lambda f: prof(BARBEL_R, f), sides=sides)
        m.ball(mir(BARBEL[-1], side), (BARBEL_R[-1][1] * 1.3,) * 3, sides, max(6, sides // 2))
    return m.finish(name, coll)


# ---------- the ribbons: mane, tail, fetlocks ----------
def keep_out(tree, pts, gap, start=2):
    """Each point from start on lifted out of the skin to at least gap off it."""
    out = list(pts[:start])
    for p in pts[start:]:
        loc, nrm, _, d = tree.find_nearest(p)
        if loc is not None:
            off = (p - loc).dot(nrm)
            if off < gap:
                p = p + nrm * (gap - off)
        out.append(p)
    return out


def drape(tree, pts, gap_fn, start=2):
    """Each point from start on laid on the skin at gap_fn(f) off it, f how far along: hair lying on the neck, its ends lifting free."""
    out = list(pts[:start])
    n = len(pts)
    for i in range(start, n):
        loc, nrm, _, d = tree.find_nearest(pts[i])
        out.append(loc + nrm * gap_fn(i / (n - 1)) if loc is not None else pts[i])
    return out


def land(tree, point, dirn, lift=0.0):
    dirn = dirn.normalized()
    hit = tree.ray_cast(point - dirn * 0.3, dirn, 0.6)
    return (hit[0] + hit[1] * lift, hit[1]) if hit[0] is not None else None


def mane_paths(tree):
    """Silk ribbons from the crest of its neck, poll to withers, flowing back and down its sides in long waves, the last ones out over its back. Each:
    the path, its width, which side it falls to."""
    out = []
    count = 13
    for k in range(count):
        t = k / (count - 1)
        c = path_at(NECK, 0.96 - 0.88 * t)
        hit = land(tree, c + V(0, 0, 0.2), V(0, 0, -1))
        if not hit:
            continue
        side = 1 if k % 2 == 0 else -1
        root = hit[0] - V(0, 0, 0.006) + V(side * 0.007, 0, 0)        # parted at the crest: rooted together they lay back to back
        length = 0.19 + 0.1 * t
        back = V(0, 1, 0)
        fall = V(side * 0.8, 0.0, -0.6).normalized()
        pts = []
        for j in range(9):
            u = j / 8
            wave = math.sin(math.pi * 1.5 * u) * 0.012 * u         # in step: waves out of step crossed one ribbon over the next
            p = root + back * (length * 0.62 * u) + fall * (length * 0.62 * u ** 1.25) + V(0, 0, 0.022 * u * (1 - u)) + V(side * wave * 0.4, wave, wave * 0.5)
            pts.append(p)
        out.append((drape(tree, catmull(pts, 4), lambda f, t=t, k=k: 0.007 + 0.006 * ((k % 4) // 2) + 0.004 * t + 0.03 * f ** 2.2),
                    0.016 + 0.002 * t, side))     # narrower than the gap to the next on its side: wider, they lay over each other
    return out


def tail_paths():
    """Its tuft: five silk ribbons fanning from the end of the tail, streaming back and up in an S."""
    end = TAIL[-1]
    axis = (TAIL[-1] - TAIL[-3]).normalized()
    side = axis.cross(V(0, 0, 1)).normalized()
    up = side.cross(axis).normalized()
    out = []
    # set round the end of the tail like a brush (rooted together they lay level on each other)
    for k, (ang, length, width) in enumerate(((90, 0.29, 0.028), (18, 0.25, 0.026), (162, 0.25, 0.026), (-54, 0.2, 0.022), (-126, 0.2, 0.022))):
        a = math.radians(ang)
        off = side * math.cos(a) + up * math.sin(a)
        go = (V(0, 0.8, 0.6).normalized() + off * 0.3).normalized()
        pts = []
        for j in range(9):
            u = j / 8
            s = math.sin(math.pi * 1.6 * u) * 0.03 * u
            pts.append(end + off * 0.018 - go * 0.012 + go * (length * u) + V(0, -0.02 * u * u, s - 0.05 * u * u + 0.07 * u ** 3))
        out.append((catmull(pts, 4), width, 1 if math.cos(a) >= 0 else -1))
    return out


def fetlock_paths(tree):
    """Two short silk wisps trailing from behind each fetlock."""
    out = []
    for key, side, knots, radii in LEGS:
        c = mir(knots[3], side)
        for dz, length, width, dx in ((0.012, 0.075, 0.016, 0.006), (-0.006, 0.06, 0.013, -0.006)):
            hit = land(tree, c + V(dx * side, 0, dz), V(0, -1, 0))
            if not hit:
                continue
            root = hit[0] - V(0, 0.004, 0)
            pts = [root + V(dx * side * u, length * u, 0.022 * u - 0.026 * u * u) for u in np.linspace(0, 1, 7)]
            out.append((keep_out(tree, catmull(pts, 4), 0.004), width, key))
    return out


def ribbon_profile(width, tip=0.0018):
    def r(f):
        return tip + width * (math.sin(math.pi * min(1.0, 0.18 + f * 0.82)) ** 0.7) * (1 - 0.25 * f)
    return r


def resample(path, n):
    a = np.array([tuple(p) for p in path])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])
    out = []
    for t in np.linspace(0, s[-1], n):
        i = min(int(np.searchsorted(s, t, side="right")) - 1, len(a) - 2)
        f = (t - s[i]) / max(s[i + 1] - s[i], 1e-9)
        out.append(Vector(a[i] + (a[i + 1] - a[i]) * f))
    return out


def ribbons_piece(ribbons, name, coll, rows, sides, flat=0.16):
    """Flat ribbons along paths, thin across x (they lie along its sides). Each vertex carries which ribbon, how far along ("along") and how far round."""
    m = Mesh()
    bm = m.bm
    for key in ("along", "round"):
        bm.verts.layers.float.new(key)
    bm.verts.layers.int.new("which")
    al, rl, wl = bm.verts.layers.float["along"], bm.verts.layers.float["round"], bm.verts.layers.int["which"]
    for index, (path, width, _) in enumerate(ribbons):
        before = len(bm.verts)
        m.tube(resample(path, rows), ribbon_profile(width), sides=sides, flat=flat, plane=V(1, 0, 0))
        bm.verts.ensure_lookup_table()
        for k in range(before, len(bm.verts)):
            i, j = divmod(k - before, sides)
            v = bm.verts[k]
            v[al], v[rl], v[wl] = i / (rows - 1), j / sides, index
    return m.finish(name, coll)


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


# ---------- glow: the sunburst, the lotuses ----------
def build_halo(name, coll, sides=10, per=72):
    """An arc of light behind its head, open below, with rays standing out of it, long and short by turns."""
    m = Mesh()
    span = math.radians(HALO_SPAN)

    def at(a, r):
        return HALO_C + V(math.sin(a) * r, 0, math.cos(a) * r)
    arc = [at(a, HALO_R) for a in np.linspace(-span, span, per)]
    m.tube(arc, lambda f: 0.0065, sides=sides)
    for a in (-span, span):
        m.ball(at(a, HALO_R), (0.0085,) * 3, sides, max(4, sides // 2))
    inner = [at(a, HALO_R - 0.022) for a in np.linspace(-span * 0.86, span * 0.86, per)]
    m.tube(inner, lambda f: 0.0032, sides=max(6, sides - 2))
    for a in (-span * 0.86, span * 0.86):
        m.ball(at(a, HALO_R - 0.022), (0.0045,) * 3, max(6, sides - 2), max(3, sides // 2 - 1))
    rays = 11
    for k in range(rays):
        a = -span + 2 * span * (k + 0.5) / rays
        long = k % 2 == 0
        length = 0.034 if long else 0.02
        tip = 0.0048 if long else 0.0036
        m.tube([at(a, HALO_R - 0.004 + length * u) for u in np.linspace(0, 1, 6)], lambda f, t=tip: 0.0075 * (1 - f) + t * f, sides=max(6, sides - 2))
        m.ball(at(a, HALO_R - 0.004 + length), (tip,) * 3, max(6, sides - 2), max(3, sides // 2 - 1))     # a round drop of light at its end
    return m.finish(name, coll)


def torus(m, c, R, r, segs, sides):
    """A closed ring lying flat round c."""
    rings = []
    for i in range(segs):
        a = TAU * i / segs
        d = V(math.cos(a), math.sin(a), 0)
        rings.append([m.bm.verts.new(c + d * (R + r * math.cos(TAU * k / sides)) + V(0, 0, r * math.sin(TAU * k / sides))) for k in range(sides)])
    for i in range(segs):
        for k in range(sides):
            a, b = rings[i], rings[(i + 1) % segs]
            m.bm.faces.new((a[k], b[k], b[(k + 1) % sides], a[(k + 1) % sides]))


def lotus_at(key, side, knots):
    hoof = mir(knots[4], side)
    return V(hoof.x, hoof.y, 0.012)


def build_lotuses(name, coll, low=False):
    """Under each hoof a lotus of light: eight petals cupped round a ring. Returns it and which hoof each vertex is under."""
    m = Mesh()
    which = []
    seg = (6, 4) if low else (24, 14)
    for index, (key, side, knots, _) in enumerate(LEGS):
        before = len(m.bm.verts)
        c = lotus_at(key, side, knots)
        for k in range(8):
            a = TAU * (k + 0.5 * (index % 2)) / 8
            d = V(math.cos(a), math.sin(a), 0)
            tilt = Matrix.Rotation(math.radians(24), 4, d.cross(V(0, 0, 1)) * -1)
            rot = Matrix.Rotation(a, 4, "Z")
            mat = Matrix.Translation(c + d * 0.036 + V(0, 0, 0.006)) @ tilt @ rot
            bmesh.ops.create_uvsphere(m.bm, u_segments=seg[0], v_segments=seg[1], radius=1.0, matrix=mat @ Matrix.Diagonal((0.034, 0.016, 0.004, 1)))
        torus(m, c + V(0, 0, 0.004), 0.026, 0.004, 14 if low else 40, 5 if low else 10)
        which += [index] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


# ---------- paint ----------
def scroll_mark(Pv, Nn, centre, side, size, turns=1.7):
    """A gold flame-scroll on its flank: a spiral line winding in, as a brush draws it, thinning to its end."""
    u = Pv[:, 1] - centre.y
    v = Pv[:, 2] - centre.z
    r = np.hypot(u, v)
    a = np.arctan2(v, -u) % TAU
    best = np.full(len(Pv), 9.0)
    weight = np.zeros(len(Pv))
    for lap in range(int(turns) + 2):
        w = (a / TAU) + lap
        rr = size * (1 - w / (turns + 0.4))
        live = (w <= turns) & (rr > 0)
        d = np.where(live, np.abs(r - rr), 9.0)
        better = d < best
        best = np.where(better, d, best)
        weight = np.where(better, 1 - w / (turns + 0.6), weight)
    width = 0.0035 + 0.0045 * weight
    line = 1 - smooth(width * 0.7, width, best)
    facing = smooth(0.15, 0.45, Nn[:, 0] * side)
    return line * facing * (1 - smooth(size * 1.05, size * 1.2, r))


def paint_skin(o):
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    head = 1 - smooth(0.085 * HS, 0.13 * HS, np.linalg.norm(Pv - np.array(tuple(H(0, -0.435, 0.98))), axis=1))
    leg = smooth(LIFT + 0.4, LIFT + 0.32, z) * (1 - head)
    hair_body = fbm(Pv * np.array([170.0, 40.0, 170.0]), 1.0, 3, 3)
    hair_leg = fbm(Pv * np.array([170.0, 170.0, 40.0]), 1.0, 3, 5)
    fur = hair_body * (1 - leg) + hair_leg * leg
    col = mix(COAT * 0.96, COAT, smooth(0.3, 0.7, fur))
    col = mix(col, COAT_SHEEN, smooth(0.3, 0.95, Nn[:, 2]) * 0.5)
    under = smooth(-0.2, -0.75, Nn[:, 2]) * (1 - head)
    col = mix(col, COAT_SHADE, under * 0.45)
    # its legs dipped in sunlight: gold from the knees down, rising in soft licks
    gold = np.zeros(len(Pv))
    for key, side, knots, radii in LEGS:
        k2 = mir(knots[2], side)
        lick = 0.018 * np.sin(np.arctan2(y - k2.y, x - k2.x) * 3.0 + (1 if key[0] == "F" else 2))
        top = k2.z + 0.03 + lick
        near = (np.abs(x - k2.x) < 0.08) & (np.abs(y - k2.y) < 0.09)
        gold = np.maximum(gold, near * (1 - smooth(top - 0.025, top + 0.01, z)))
    gold_col = mix(GOLD, GOLD_PALE, smooth(LIFT + 0.08, LIFT + 0.2, z) * 0.6)
    gold_col = mix(gold_col, GOLD_DEEP, smooth(0.2, -0.6, Nn[:, 2]) * 0.4)
    col = mix(col, gold_col, gold)
    # the flame-scrolls on its shoulders and haunches
    scrolls = np.zeros(len(Pv))
    for side in (1, -1):
        scrolls = np.maximum(scrolls, scroll_mark(Pv, Nn, U(side * 0.09, -0.17, 0.56), side, 0.058))
        scrolls = np.maximum(scrolls, scroll_mark(Pv, Nn, U(side * 0.1, 0.18, 0.53), side, 0.066))
    col = mix(col, GOLD, scrolls * 0.95)
    # the face: a blush of gold on the muzzle
    muzzle_f, muzzle_d = nearest_on(catmull(MUZZLE, 6), Pv)
    blush = (1 - smooth(0.04 * HS, 0.056 * HS, muzzle_d)) * smooth(0.45, 0.95, muzzle_f)
    col = mix(col, GOLD_LIGHT, np.clip(blush, 0, 1) * 0.6)
    # the tail's shaft gold toward its tuft
    tf, td = nearest_on(TAIL, Pv)
    tail = (1 - smooth(0.03, 0.04, td)) * smooth(0.35, 0.9, tf)
    col = mix(col, GOLD, tail)
    # hooves: polished gold, cloven
    hooves = np.zeros(len(Pv))
    cleft = np.zeros(len(Pv))
    for key, side, knots, radii in LEGS:
        c = mir(knots[4], side)
        near = (np.linalg.norm(Pv[:, [0, 1]] - np.array((c.x, c.y)), axis=1) < 0.05) * (z < LIFT + 0.055)
        hooves = np.maximum(hooves, near * smooth(LIFT + 0.052, LIFT + 0.044, z))
        cleft = np.maximum(cleft, near * (1 - smooth(0.0015, 0.0035, np.abs(x - c.x))) * (y < c.y))
    col = mix(col, mix(GOLD_DEEP, GOLD_PALE, smooth(-0.4, 0.9, Nn[:, 2] * 0.5 - Nn[:, 1] * 0.5)), hooves)
    col = mix(col, GOLD_DEEP * 0.45, cleft)
    # the nose and mouth
    nose = 1 - smooth(0.013 * HS, 0.019 * HS, np.linalg.norm((Pv - np.array(tuple(H(0, -0.508, 0.986)))) / np.array((1.0, 0.7, 1.0)), axis=1))
    col = mix(col, mix(NOSE_COL, GOLD_PALE, smooth(0.3, 0.9, Nn[:, 2]) * 0.4), nose)
    nost = np.zeros(len(Pv))
    for side in (1, -1):
        c = np.array(tuple(H(side * 0.011, -0.513, 0.981)))
        nost = np.maximum(nost, 1 - smooth(0.003, 0.005, np.linalg.norm((Pv - c) * np.array([1.0, 0.6, 1.3]), axis=1)))
    L = laid(Pv)
    lx, fy, fz = L[:, 0], L[:, 1], L[:, 2]          # as the head was laid out
    lip = (1 - smooth(0.0006, 0.0016, np.abs(fz - (0.95 + 0.15 * (fy + 0.47) + 0.9 * lx ** 2)))) * smooth(-0.44, -0.455, fy) * (np.abs(lx) < 0.034) * (np.abs(fz - 0.95) < 0.03)
    mouth = np.clip(nost + lip, 0, 1)
    col = mix(col, MOUTH, mouth * 0.55)
    relief = (fur - 0.5) * 0.0005 - 0.0008 * mouth
    set_verts(o, Pv + Nn * relief[:, None])
    metal = np.clip(hooves * 0.9 + scrolls * 0.5 + gold * 0.25, 0, 1)
    paint(o, np.clip(col, 0, 1), 0.55 - 0.1 * smooth(0.45, 0.8, fur) - 0.3 * hooves - 0.2 * scrolls - 0.2 * nose, metal)


def paint_horns(o):
    Pv = verts(o)
    along = read_tag(o, "along")
    col = mix(np.broadcast_to(GOLD_DEEP, (len(Pv), 3)), GOLD, smooth(0.0, 0.4, along))
    col = mix(col, GOLD_LIGHT, smooth(0.6, 1.0, along))
    paint(o, col, np.full(len(Pv), 0.22), np.full(len(Pv), 0.85))


def paint_barbels(o):
    Pv = verts(o)
    f = np.zeros(len(Pv))
    for side in (1, -1):
        ff, dd = nearest_on(catmull([mir(p, side) for p in BARBEL], 8), Pv)
        f = np.where(Pv[:, 0] * side > 0, ff, f)
    col = mix(np.broadcast_to(GOLD, (len(Pv), 3)), GOLD_LIGHT, smooth(0.3, 1.0, f))
    paint(o, col, np.full(len(Pv), 0.3), np.full(len(Pv), 0.6))


def paint_ribbons(o):
    """Gold at the root going to pale light at the end, fine lengthwise sheen lines, the edges a touch deeper."""
    along, rnd, which = read_tag(o, "along"), read_tag(o, "round"), read_tag(o, "which")
    across = np.abs(np.cos(rnd * TAU))                  # 1 at the ribbon's edges, 0 on its faces
    streak = 0.5 + 0.5 * np.sin(np.sin(rnd * TAU) * 14.0 + which * 1.7)
    col = mix(np.broadcast_to(GOLD, (len(along), 3)), GOLD_PALE, smooth(0.15, 0.6, along))
    col = mix(col, GOLD_LIGHT, smooth(0.6, 1.0, along))
    col = col * (0.9 + 0.1 * streak)[:, None]
    col = mix(col, GOLD_DEEP, smooth(0.7, 1.0, across) * 0.35 * (1 - smooth(0.6, 1.0, along)))
    paint(o, np.clip(col, 0, 1), 0.3 - 0.08 * streak, np.full(len(along), 0.35))


def eye_paint(o, fr):
    """A golden sun-eye: amber deepening to its rim, bright rays of fibre from the pupil, a fine dark ring round the iris, a round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(40, 24, 10), (len(px), 3)).copy()
    iris = mix(rgb(255, 214, 96), rgb(214, 132, 28), smooth(0.35, 0.85, r / IRIS))
    azi = np.arctan2(py, px)
    rays = 0.5 + 0.5 * np.sin(azi * 26 + np.sin(azi * 5) * 1.5)
    iris = mix(iris, rgb(255, 240, 170), rays * smooth(PUPIL + 0.02, PUPIL + 0.2, r) * (1 - smooth(0.6, 0.85, r)) * 0.5)
    iris = mix(iris, iris * 0.7, smooth(-0.2, 0.8, py / IRIS) * 0.35)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(70, 36, 8), smooth(IRIS - 0.12, IRIS - 0.03, r) * (1 - smooth(IRIS - 0.03, IRIS, r)))
    col = mix(col, rgb(18, 10, 4), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
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
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    tree = tree_of(skin)
    data["tree"] = tree
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, COAT, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, COAT, LASH * 1.2, lower_share=0.7)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Horns"] = build_horns(N + "HornsHi", HI)
    pieces["Barbels"] = build_barbels(N + "BarbelsHi", HI)
    data["mane"] = mane_paths(tree)
    data["tail"] = tail_paths()
    data["fetlocks"] = fetlock_paths(tree)
    pieces["Mane"] = ribbons_piece(data["mane"], N + "ManeHi", HI, 80, 16, flat=0.1)
    pieces["Tuft"] = ribbons_piece(data["tail"], N + "TuftHi", HI, 80, 16)
    pieces["Feathers"] = ribbons_piece(data["fetlocks"], N + "FeathersHi", HI, 30, 12)
    lotus, data["lotus_which"] = build_lotuses(N + "Lotus_Glow_" + LOTUS_HEX, HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0058, 12), (20, -18, 0.0026, 8))),
             "Halo": build_halo(N + "Halo_Glow_" + HALO_HEX, HI), "Lotus": lotus}
    if not clay:
        paint_skin(skin)
        paint_horns(pieces["Horns"])
        paint_barbels(pieces["Barbels"])
        for key in ("Mane", "Tuft", "Feathers"):
            paint_ribbons(pieces[key])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.0, 0.52)
FACE_AT = tuple(HEAD + V(0, -0.06, -0.02))
EXTRA = [(0, -1, 0.05, 0.8, FACE_AT), (0.62, -0.75, 0.2, 0.8, FACE_AT), (1, -0.12, 0.08, 0.85, FACE_AT), (0.4, -0.9, 0.1, 0.35, tuple(EYE_C)),
         (0.8, 0.3, 0.5, 1.6, (0.0, -0.2, 0.72)), (1, -0.1, 0.05, 1.3, (0, 0.0, 0.18)), (0.5, 0.9, 0.3, 1.2, (0, 0.55, 0.45))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "ribbons", len(data["mane"]), len(data["tail"]), len(data["fetlocks"]), flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.1, 0.06, 0.02, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.15)       # a white coat shows every contact shadow: the mane's made grey smudges
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3800
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "EarL": 1.3, "EarR": 1.3, "Horns": 1.3, "Barbels": 1.0,
          "Mane": 1.0, "Tuft": 1.0, "Feathers": 1.2}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 8, 8, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Horns"] = build_horns(N + "HornsLow", GAME, 10, 5)
    lows["Barbels"] = build_barbels(N + "BarbelsLow", GAME, 5, 4)
    lows["Mane"] = ribbons_piece(data["mane"], N + "ManeLow", GAME, 12, 6, flat=0.1)
    lows["Tuft"] = ribbons_piece(data["tail"], N + "TuftLow", GAME, 12, 6)
    lows["Feathers"] = ribbons_piece(data["fetlocks"], N + "FeathersLow", GAME, 6, 5)
    triangulate(lows)
    return lows


def low_glows(frames):
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0058, 10), (20, -18, 0.0026, 6))),
             "Halo": build_halo(N + "Halo_Glow_" + HALO_HEX, GAME, 6, 30)}
    glows["Lotus"], which = build_lotuses(N + "Lotus_Glow_" + LOTUS_HEX, GAME, low=True)
    triangulate(glows)
    return glows, which


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[4], "Body"), ("Neck1", NECK[0], "Chest"),
               ("Neck2", path_at(NECK, 0.5), "Neck1"), ("Head", NECK[-1], "Neck2"))
TAIL_NAMES = ["Tail1", "Tail2", "Tail3"]
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Hoof" + key] for key, _, _, _ in LEGS}


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots):
    fs = [k / (len(knots) - 1) for k in range(len(knots))]
    return tuple((fs[k] + fs[k + 1]) / 2 for k in range(4))


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    bones += [("Tail1", TAIL[0].copy(), "Hips"), ("Tail2", path_at(TAIL, 0.45), "Tail1"), ("Tail3", TAIL[-1].copy(), "Tail2"), ("Halo", HALO_C.copy(), "Head")]
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, C, along, up, n = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, C.copy(), "Head")]
    fs = [k / (len(FRONT) - 1) for k in range(len(FRONT))]
    for key, side, knots, _ in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        line = leg_line(knots, side)
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, path_at(line, fs[k]), parent))
            parent = name
        bones.append(("Lotus" + key, lotus_at(key, side, knots), "Root"))
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


HEAD_ZONE = (H(0, -0.44, 0.985), (0.09 * HS, 0.12 * HS, 0.09 * HS))


def body_weights(P_):
    """The skin's weights at any points: the trunk (hips to head), the head, the tail, the legs; a hoof wholly its hoof's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P_)
    hz = np.linalg.norm((P_ - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P_)
    legs = []
    for key, side, knots_l, radii in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P_)
        legs.append((key, side, knots_l, radii, f, d))
    out = []
    for i in range(len(P_)):
        x, y, z = P_[i]
        owner = None
        for key, side, knots_l, radii, f, d in legs:
            if (Vector(P_[i]) - mir(knots_l[4], side)).length < 0.06 and z < LIFT + 0.062:
                owner = "Hoof" + key
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
        share = (1 - float(smooth(0.035, 0.05, td[i]))) * float(smooth(0.0, 0.2, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, (0.0, 0.2, 0.6, 0.95), float(tf[i])), share)
        for key, side, knots_l, radii, f, d in legs:
            if x * side <= 0.012:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.014
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            mm *= float(smooth(0.015, 0.08, x * side)) if z > knots_l[1].z - 0.02 else 1.0
            if mm > 0:
                w = blend(w, chain_weight(LEG_NAMES[key], leg_mids(knots_l), float(f[i])), mm)
        out.append(w)
    return out


def bind_all(lows, rig, glows, data, lotus_which):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Horns"], "Head")
    rigid(lows["Barbels"], "Head")
    # each mane ribbon goes with the neck where it grows; the tuft with the end of the tail; each wisp with its hoof
    roots = np.array([tuple(path[0]) for path, _, _ in data["mane"]])
    root_w = body_weights(roots)
    which = read_tag(lows["Mane"], "which")
    weigh(lows["Mane"], [root_w[k] for k in which])
    rigid(lows["Tuft"], "Tail3")
    keys = [key for _, _, key in data["fetlocks"]]
    weigh(lows["Feathers"], [{"Hoof" + keys[k]: 1.0} for k in read_tag(lows["Feathers"], "which")])
    rigid(glows["Halo"], "Halo")
    weigh(glows["Lotus"], [{"Lotus" + LEGS[k][0]: 1.0} for k in lotus_which])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateGoldenKirin uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def legs4(f, b):
    out = {}
    for side in "LR":
        for k in range(3):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, 0)
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, 0)
    return out


# its stances, searched in Blender against the ground and for torn skin: the same numbers as PetRig's KIRIN_* tables
REAR = {"Hips": (0, 0, 0, (0, -0.042, 0)), "Body": (0.5, 0, 0), "Neck1": (-0.15, 0, 0), "Head": (-0.05, 0, 0), **legs4((-0.1, -0.5, 1.2), (-0.25, -0.2, 0.05))}
LIE = {"Hips": (0, 0, 0, (0, -0.19, 0)), "Body": (-0.1, 0, 0), "Head": (0.25, 0, 0), **legs4((0.4, -2.1, 0.0), (-0.4, -0.65, 1.8))}     # hind legs folded at the hock (at the stifle the thigh tore)
LEAP = {"Body": (-0.04, 0, 0), "Head": (0.2, 0, 0), "Tail1": (0.3, 0, 0), **legs4((0.6, -1.4, 0.3), (-0.4, 0.25, 0.1))}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    # PetRig's prancing trot: a foreleg and the hind leg across from it lifted, the other pair swung back
    # (its worst: 30 degrees into the stride; every twelfth of the cycle checked in Blender, the most any edge gains is 4.5 cm)
    stride = {"LegFL1": (0.41, 0, 0), "LegFL2": (0.087, 0, 0), "LegFL3": (-1.04, 0, 0), "HoofFL": (-0.3, 0, 0), "LegBR1": (-0.15, 0, 0), "LegBR2": (-0.26, 0, 0),
              "LegBR3": (0.52, 0, 0), "LegFR1": (-0.15, 0, 0), "LegBL1": (0.15, 0, 0)}
    prance = {"LegFL1": (0.7, 0, 0), "LegFL2": (-1.3, 0, 0), "LegFL3": (0.6, 0, 0), "Neck1": (-0.12, 0, 0), "Head": (0.15, 0, 0), "Tail1": (0.35, 0, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-6, -5), "Stride": spec(stride), "Prance": spec(prance), "Rear": spec(REAR), "Lie": spec(LIE),
            "Leap": spec(LEAP), "Look": spec({"Neck2": (0.15, 0.35, 0), "Head": (0.2, 0.45, 0.15)}),
            "Bow": spec({"Neck1": (0.3, 0, 0), "Neck2": (0.25, 0, 0), "Head": (0.2, 0, 0)}),
            "Swish": spec({"Tail1": (0.3, 0.5, 0), "Tail2": (0.2, 0.6, 0), "Tail3": (0.1, 0.5, 0)}),
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


GROUND_PARTS = {"FrontHooves": ("HoofFL", "HoofFR"), "HindHooves": ("HoofBL", "HoofBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",), "Head": ("Head",),
                "Tail": ("Tail2", "Tail3")}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.15)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < HEAD_AT.y - 0.02 and p.center.z > HEAD_AT.z - 0.11, 2.0), (None, 1.0)], SCALES, margin=0.009, angle=38)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.9, 0.88, 0.82, 1), far=("Skin",), reach=(0.005, 0.012),
             far_reach=(0.01, 0.025))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    glows, lotus_which = low_glows(frames)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows, data, lotus_which)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones),
          "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres from the box middle down to the lotuses", round(hi / 2 - lo, 4), "(the box runs from the root at 0)", flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Hips", "Head", "Halo", "Tail3", "LotusFL", "LotusBR"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Rear", "Lie", "Leap", "Prance"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 3.4, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 3.4, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.8, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Stride", side), ("Prance", side), ("Rear", side), ("Lie", wide), ("Leap", side), ("Look", face),
                       ("Bow", side), ("Swish", wide), ("Ears", face)):
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

"""The Lotus Elephant (Epic, Serenity; Ancient Grove Egg), in place of the Thousand-Eyed Guardian (the owner's choice, 2026-11-12).

A new creature, in a design language of its own: a white elephant carrying a living lotus pond on its back. A young Asian elephant (references: its
twin-domed head the highest point of it, a rounded back, small angular ears, one finger at its trunk's tip, legs stacked straight under it on wide round
feet; short milk tusks), its skin the pale of white jade, freckled pink on its trunk and the edges of its ears as a white elephant's is. Over its back,
for a saddle cloth, a great lotus leaf, its veins running out from the middle, its rim wavy and lifting; set on it, a lotus in bloom, white petals
blushing pink to their tips round a seed-pod whose seeds glow gold with Qi (after the old "taiping youxiang", the elephant that carries peace on its
back). Little gold caps on its tusks, gold anklets with a bell on each. Calm amber eyes under heavy lids.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/lotus_elephant.py -- [clay|paint|rig|all] [review dir] [views i,j]

Faces -Y, Z up, 1 unit = 1 metre, feet on z = 0. +X is its left. The maps go to assets/pets/AncientGroveEgg/. The pet's id stays ThousandEyedGuardian
(saves and the egg table keep it); the files are named for it.

What touches what: body, head, trunk, legs, feet and tail are one fused skin; the eyes sit in their sockets under their lids; the ears are their own
sheets set into the sides of the head; the leaf lies 1 cm over its back; the lotus stands on the leaf; the tusks root in the lip, the anklets round the
lower legs.
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
PET = "ThousandEyedGuardian"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AncientGroveEgg")

# ---------- colours: white jade, lotus pink, leaf green, gold ----------
JADE, JADE_SHADE = rgb(218, 212, 200), rgb(178, 196, 188)        # its skin: white jade, cool and faintly green in its folds (whiter, it read as plastic)
JADE_TOP = rgb(232, 222, 206)                                    # warmer ivory where the light falls
FRECKLE = rgb(232, 176, 168)                                     # a white elephant's pink freckles
EAR_PINK = rgb(240, 188, 182)
LEAF, LEAF_DEEP, LEAF_VEIN = rgb(92, 150, 82), rgb(52, 104, 62), rgb(170, 204, 120)
PETAL_BASE, PETAL_TIP = rgb(255, 253, 250), rgb(236, 120, 150)      # (its base at 250 went grey in the cup's shade)
POD = rgb(214, 214, 120)
GOLD = rgb(226, 176, 70)
IVORY = rgb(244, 236, 214)
NAIL = rgb(232, 222, 200)
MOUTH = rgb(150, 92, 96)
SEED_HEX, GLINT_HEX = "ffc24a", "ffffff"

# ---------- the frame of it ----------
SPINE = [V(0, 0.34, 0.5), V(0, 0.25, 0.53), V(0, 0.12, 0.55), V(0, -0.02, 0.555), V(0, -0.14, 0.555), V(0, -0.22, 0.56)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.13), (0.15, 0.18), (0.45, 0.205), (0.7, 0.2), (0.88, 0.19), (1, 0.16))         # half-widths, rump to withers: a barrel
BODY_H = ((0, 0.14), (0.15, 0.19), (0.45, 0.215), (0.7, 0.215), (0.88, 0.205), (1, 0.18))
BODY_DROP = ((0, 0.0), (0.15, 0.01), (0.45, 0.02), (0.7, 0.018), (0.88, 0.01), (1, 0.0))      # its belly level, a little low in the middle
NECK = catmull([V(0, -0.21, 0.6), V(0, -0.26, 0.64), V(0, -0.3, 0.67)], 8)
NECK_R = ((0, 0.17), (0.5, 0.16), (1, 0.15))
HEAD = V(0, -0.4, 0.74)
# its head, lofted back to front: (y, half-width, top, bottom) of each section, squared ellipses; the forehead near upright, its top the highest
# point of it, the face narrowing down into the root of its trunk
HEAD_SECTIONS = [(-0.27, 0.14, 0.8, 0.54), (-0.3, 0.19, 0.875, 0.5), (-0.35, 0.215, 0.92, 0.49), (-0.41, 0.222, 0.935, 0.5), (-0.47, 0.208, 0.92, 0.53),
                 (-0.51, 0.178, 0.885, 0.56), (-0.535, 0.14, 0.83, 0.58), (-0.55, 0.1, 0.76, 0.6)]     # broad across the domes (narrower, it read as a bullet)
SWELLS = [(V(0.085, -0.43, 0.93), 0.024, (0.075, 0.075, 0.05)), (V(-0.085, -0.43, 0.93), 0.024, (0.075, 0.075, 0.05)),    # the twin domes
          (V(0, -0.44, 0.945), -0.016, (0.024, 0.09, 0.05)),                                                            # the groove between them
          (V(0.155, -0.49, 0.785), 0.018, (0.045, 0.04, 0.03)), (V(-0.155, -0.49, 0.785), 0.018, (0.045, 0.04, 0.03)),        # brows hooding its eyes
          (V(0, -0.53, 0.58), 0.016, (0.05, 0.04, 0.03))]                                                                # its lower lip
TRUNK_PATH = catmull([V(0, -0.49, 0.74), V(0, -0.545, 0.68), V(0, -0.585, 0.6), V(0, -0.615, 0.48), V(0, -0.625, 0.36), V(0, -0.615, 0.25), V(0, -0.6, 0.17),
                      V(0, -0.615, 0.115), V(0, -0.65, 0.1)], 8)                                                           # down, its end curling forward
TRUNK_PROFILE = ((0, 0.11), (0.08, 0.092), (0.18, 0.074), (0.45, 0.052), (0.75, 0.04), (0.92, 0.034), (1, 0.03))
FRONT = [V(0.095, -0.17, 0.48), V(0.105, -0.17, 0.31), V(0.11, -0.18, 0.15), V(0.11, -0.19, 0.06), V(0.11, -0.2, 0.035)]
HIND = [V(0.095, 0.25, 0.48), V(0.105, 0.2, 0.3), V(0.11, 0.24, 0.14), V(0.11, 0.24, 0.06), V(0.11, 0.23, 0.035)]      # under its body (wider, they stood out past its flanks)
FRONT_R = (0.1, 0.082, 0.072, 0.071, 0.075)                      # columns: little taper, as an elephant's
HIND_R = (0.108, 0.084, 0.07, 0.07, 0.074)
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))
FOOT_R = 0.08                                                  # its feet: wide and round
TAIL = catmull([V(0, 0.44, 0.58), V(0, 0.49, 0.5), V(0, 0.51, 0.4), V(0.01, 0.51, 0.32)], 8)
TAIL_PROFILE = ((0, 0.024), (0.6, 0.014), (1, 0.011))
EYE_R = 0.026
EYE_C = V(0.162, -0.5, 0.745)
EYE_AXIS = V(0.62, -0.76, 0.1).normalized()
LID_UP, LID_LOW = (24.0, 120.0, 0.0024), (-15.0, -126.0, 0.002)     # calm and a little heavy (the lower at -7 puffed up under each eye: sleepy)
LID_TILT = 0.0                                                       # level: serene (at -6 worried; at +8 the inner corners came down into a side-eye glare, seen in Play)
BLINK_U, BLINK_L = 30.0, 10.0                                         # (the two add past the 39 degrees between the edges)
IRIS, PUPIL = 0.86, 0.3
TUSK = [V(0.06, -0.545, 0.585), V(0.068, -0.585, 0.56), V(0.068, -0.61, 0.53)]      # short milk tusks, out of the lip either side of its trunk
TUSK_R = 0.013
EAR = {"root_top": V(0.2, -0.37, 0.87), "root_bot": V(0.19, -0.41, 0.62)}
LEAF_C = V(0, 0.05, 0.55)                                    # the leaf's middle, over its back (on the spine; its rays go out from here)
LEAF_SPAN = (0.3, 0.26)                                      # its half-length along the body, its reach round each flank (m, along the skin)
LOTUS_AT = V(0, 0.05, 0.0)                                   # set on the leaf's top (its z found on the leaf)
PETALS = ((8, 0.15, 0.062, 0.38, 0.0), (8, 0.19, 0.074, 0.82, math.pi / 8))     # big: the heart of it (smaller, a cake topper)     # rings: count, length, half-width, tilt out from upright, turn
ANKLET_Z = {"F": 0.13, "B": 0.12}


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


def fuse(target, parts):
    for part in parts:
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bm.from_mesh(part.data)
        bm.to_mesh(target.data)
        bm.free()
        bpy.data.objects.remove(part, do_unlink=True)


# ---------- the skin ----------
def head_mesh():
    m = Mesh()
    bm = m.bm
    nt, per = 96, 6
    sp1 = catmull([V(q[0], q[1], q[2]) for q in HEAD_SECTIONS], per)
    sp2 = catmull([V(q[3], 0, 0) for q in HEAD_SECTIONS], per)
    rows = [(p1.x, p1.y, p1.z, p2.x) for p1, p2 in zip(sp1, sp2)]
    rings = []
    for y, w, top, bot in rows:
        cz, hz = (top + bot) / 2, (top - bot) / 2
        ring = []
        for k in range(nt):
            a = TAU * k / nt
            c, sn = math.cos(a), math.sin(a)
            e = 2.3
            r = (abs(c) ** e + abs(sn) ** e) ** (-1 / e)
            ring.append(bm.verts.new(V(c * r * w, y, cz + sn * r * hz)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    back = bm.verts.new(V(0, rows[0][0] + 0.03, (rows[0][2] + rows[0][3]) / 2))
    front = bm.verts.new(V(0, rows[-1][0] - 0.01, (rows[-1][2] + rows[-1][3]) / 2))
    for k in range(nt):
        bm.faces.new((back, rings[0][(k + 1) % nt], rings[0][k]))
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % nt], front))
    return m.finish(N + "HeadHi", HI)


def smooth_region(o, spots, iterations=40):
    """Relaxes the skin only round each spot (centre, radius), fading out: where a tube meets the body the union leaves a crease that no global
    smoothing takes out without melting everything else."""
    P = verts(o)
    w = np.zeros(len(P))
    for c, r in spots:
        w = np.maximum(w, 1 - smooth(0.4 * r, r, np.linalg.norm(P - np.array(tuple(c)), axis=1)))
    g = o.vertex_groups.new(name="relax")
    for i in np.nonzero(w > 0.001)[0]:
        g.add([int(i)], float(w[i]), "REPLACE")
    apply_mods(o, [("SMOOTH", {"factor": 0.9, "iterations": iterations, "vertex_group": "relax"})])
    o.vertex_groups.clear()


def build_skin():
    """Body, head, trunk, legs, feet and tail in one fused pass (split in two, the trunk's and legs' roots shrank by different amounts in each and
    left a ledge round them), then the small things (sockets, the trunk's finger, the tail's tuft) in a finer one."""
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: prof(BODY_DROP, f))
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=40)
    core.ball(SPINE[0] + V(0, -0.01, 0.0), (0.15, 0.1, 0.15))                 # the rump, round
    core.tube(TRUNK_PATH, lambda f: prof(TRUNK_PROFILE, f) * 1.04, sides=32)
    for key, side, knots, radii in LEGS:
        core.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f) * 1.04, sides=28)
        foot = mir(knots[3], side)
        core.ball(foot + V(0, -0.012, -0.022), (FOOT_R, FOOT_R * 0.98, 0.042), 32, 16)                  # the foot: a wide round pad
    for side in (1, -1):
        core.ball(mir(FRONT[0], side) + V(-side * 0.03, 0, 0.02), (0.09, 0.12, 0.13))     # shoulders
        core.ball(mir(HIND[0], side) + V(-side * 0.03, 0, 0.02), (0.1, 0.13, 0.14))      # haunches
    loft(core, TAIL, lambda f: prof(TAIL_PROFILE, f) * 1.1, lambda f: prof(TAIL_PROFILE, f) * 1.1, nt=16)
    c = core.finish(N + "CoreHi", HI)
    fuse(c, [head_mesh()])
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 14})])
    fine = Mesh()
    for side in (1, -1):
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.007, (EYE_R * 1.1,) * 3, 28, 18)          # the socket
    fine.ball(TRUNK_PATH[-1] + V(0, -0.014, 0.014), (0.012, 0.012, 0.015), 12, 8)                      # the finger at its tip
    fine.ball(TAIL[-1] + V(0, 0, -0.02), (0.018, 0.016, 0.035), 16, 10)                                 # its tuft
    th = fine.finish(N + "FineHi", HI)
    spots = [(V(0, -0.53, 0.72), 0.14)]                                               # the trunk's root in its face
    for key, side, knots, radii in LEGS:
        spots.append((mir(knots[1], side) + V(0, 0, 0.06), 0.11))                         # each leg's top into the body
    smooth_region(c, spots)
    fuse(c, [th])
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0034, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    P, Nn = verts(c), normals(c)
    h = np.zeros(len(P))
    for cc, amp, reach in SWELLS:
        h += amp * np.exp(-np.sum(((P - np.array(tuple(cc))) / np.array(reach)) ** 2, axis=1))
    P = P + Nn * h[:, None]
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- ears ----------
def ear_frame(side):
    A, B = mir(EAR["root_top"], side), mir(EAR["root_bot"], side)
    down = (B - A).normalized()
    back = V(0, 1, 0) - down * down.y
    back = back.normalized()
    out = down.cross(back).normalized()
    if out.x * side < 0:
        out = -out
    return A, B, down, back, out


def ear_point(side):
    """An Asian elephant's ear: a rounded flap hung from a root down the side of its head, its top edge folded a little over, swept back and
    lying close against the neck; u from the root out to the rim, v from top to bottom."""
    A, B, down, back, out = ear_frame(side)

    def point(u, v):
        root = A.lerp(B, v)
        reach = 0.23 * math.sin(math.pi * (0.1 + 0.85 * v)) ** 0.6 + 0.03          # broadest a little below the middle, rounded
        lobe = 0.07 * smooth(0.55, 1.0, v) * math.sin(math.pi * u * 0.9)              # its lower lobe hangs down
        p = root + back * (u * reach) + down * (lobe * u)
        p += out * (0.018 * math.sin(math.pi * u) + 0.055 * u ** 1.5)                   # lying back along its neck, its rim standing off it
        p += out * (0.03 * math.sin(math.pi * v) * u * u) - back * (0.025 * math.sin(math.pi * v) * u ** 3)     # cupped: its rim curling forward (flat, a card)
        if v < 0.15:                                                                    # the top edge folded over
            p += out * (0.015 * (1 - v / 0.15) * u)
        return tuple(p)
    return point


def ear_thick(u, v):
    return 0.012 * (1 - u) ** 0.6 + 0.004


# ---------- tusks, the leaf, the lotus, anklets ----------
def build_tusks(name, coll, sides=16, per=8):
    m = Mesh()
    for side in (1, -1):
        m.tube(catmull([mir(p, side) for p in TUSK], per), lambda f: TUSK_R * (1 - 0.6 * f ** 1.5) + 0.002, sides=sides)
    return m.finish(name, coll)


def skin_hit(tree, origin, direction):
    loc, nrm, _, _ = tree.ray_cast(origin, direction, 2.0)
    return loc, nrm


def leaf_point(tree, u, v):
    """The leaf on its back: u out from the middle (0..1), v round it (0..1, starting forward). Laid on the skin round the body's axis: each point found
    by a ray out from the spine, then lifted off the skin, its rim wavy and curling up."""
    a = TAU * v
    rim = 1 + 0.035 * math.sin(a * 9) + 0.012 * math.sin(a * 23 + 1)          # (deeper, the rim read as rags)
    r = (0.06 + 0.94 * u) * rim
    along = -math.cos(a) * r * LEAF_SPAN[0]            # + back
    across = math.sin(a) * r * LEAF_SPAN[1]            # + its left, measured along the skin
    y = LEAF_C.y + along
    centre = path_at(BODY_PATH, float(np.clip(1 - (y - BODY_PATH[-1].y) / (BODY_PATH[0].y - BODY_PATH[-1].y), 0, 1)))
    centre = V(0, y, centre.z - 0.03)
    ang = across / 0.21                               # radians round its body (its half-width about 0.21 m)
    d = V(math.sin(ang), 0, math.cos(ang))
    loc, nrm = skin_hit(tree, centre + d * 0.6, -d)
    if loc is None:
        loc, nrm = centre + d * 0.22, d
    lift = 0.011 + 0.026 * u ** 5 + 0.005 * u ** 3 * math.sin(a * 9)
    return loc + nrm * lift


def build_leaf(tree, name, nu=40, nv=160, hi=True):
    m = Mesh()
    m.sheet(lambda u, v: tuple(leaf_point(tree, u, v)), lambda u, v: 0.004, nu, nv)
    return m.finish(name, HI if hi else GAME)


def leaf_top(tree):
    return leaf_point(tree, 0.0, 0.0)


def petal_point(base, out, up, length, half_w, tilt, cup=0.012, curl=0.02):
    """One petal: u from its base to its tip, v across it; pointed at the tip, cupped across, its tip curling out."""
    across = up.cross(out).normalized()
    d = (up * math.cos(tilt) + out * math.sin(tilt)).normalized()
    n = across.cross(d).normalized()
    if n.dot(out) < 0:
        n = -n

    def point(u, v):
        w = half_w * (math.sin(math.pi * min(1.0, 0.18 + u * 0.82)) ** 0.8) * (1 - u ** 4) + 0.0015     # (a zero-wide tip: its edges had no length)
        s = 2 * v - 1
        p = base + d * (u * length) + across * (s * w)
        p += n * (cup * (1 - s * s) * math.sin(math.pi * min(1.0, u * 1.1)) * -1)       # hollow toward the middle of the flower
        p += n * (curl * u ** 3)                                                          # the tip curling out
        return tuple(p)
    return point


def lotus_parts(at):
    """The lotus: (pieces, per petal ring) at its base point."""
    petals = []
    up = V(0, 0, 1)
    for ring, (count, length, half_w, tilt, turn) in enumerate(PETALS):
        for k in range(count):
            a = turn + TAU * k / count
            out = V(math.sin(a), -math.cos(a), 0)
            base = at + out * (0.022 + 0.012 * ring) + up * (0.012 - 0.006 * ring)
            petals.append((ring, k, petal_point(base, out, up, length, half_w, tilt * (1 + 0.04 * math.sin(k * 2.3)))))
    return petals


def petal_thick(u, v):
    return 0.0035 * (1 - u) + 0.0012


def build_lotus(at, name, nu=24, nv=16, coll=None):
    m = Mesh()
    for ring, k, point in lotus_parts(at):
        m.sheet(point, petal_thick, nu, nv)
    # the seed-pod: a flat-topped cone, wider at the top
    m.tube([at + V(0, 0, 0.0), at + V(0, 0, 0.035), at + V(0, 0, 0.06)], lambda f: 0.026 + 0.02 * f, sides=32)
    return m.finish(name, coll or HI)


def build_seeds(at, name, coll, seg=10, rings=6):
    m = Mesh()
    top = at + V(0, 0, 0.061)
    m.ball(top, (0.0065, 0.0065, 0.0045), seg, rings)
    for k in range(7):
        a = TAU * k / 7
        m.ball(top + V(math.sin(a) * 0.027, math.cos(a) * 0.027, -0.001), (0.0065, 0.0065, 0.0045), seg, rings)
    return m.finish(N + name, coll)


def anklet_path(knots, side, z):
    line = leg_path(knots, side)
    f, _ = nearest_on(line, np.array([[mir(knots[2], side).x, mir(knots[2], side).y, z]]))
    return path_at(line, float(f[0]))


def build_anklets(name, coll, sides=48, ring_sides=10, bells=True, bell_seg=(20, 12)):
    m = Mesh()
    for key, side, knots, radii in LEGS:
        c = anklet_path(knots, side, ANKLET_Z[key[0]])
        r = leg_radius(radii, 0.7) + 0.012
        bm = m.bm
        rings = []
        for i in range(sides):
            a = TAU * i / sides
            centre = c + V(math.cos(a) * r, math.sin(a) * r, 0)
            radial = V(math.cos(a), math.sin(a), 0)
            rings.append([bm.verts.new(centre + radial * math.cos(TAU * j / ring_sides) * 0.008 + V(0, 0, 1) * math.sin(TAU * j / ring_sides) * 0.012)
                          for j in range(ring_sides)])
        for i in range(sides):
            for j in range(ring_sides):
                i2, j2 = (i + 1) % sides, (j + 1) % ring_sides
                bm.faces.new((rings[i][j], rings[i2][j], rings[i2][j2], rings[i][j2]))
        if bells:
            front = c + V(0, -(r + 0.016), -0.012)
            m.ball(front, (0.016, 0.016, 0.017), *bell_seg)
    return m.finish(name, coll)


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
    tree = tree_of(skin)
    data["tree"] = tree
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, rgb(206, 194, 188), rgb(112, 88, 86), line_w=4.5)          # a little pinker than its skin, as lids are; a soft lash line (dark and wide, it glared)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, rgb(206, 190, 186), rgb(150, 116, 116), lower_share=0.6, line_w=4.0)
        pieces["Ear" + tag] = sheet_hi(ear_point(side), ear_thick, 48, 48, N + "Ear" + tag + "Hi", lambda u, v: np.broadcast_to(JADE, (len(u), 3)),
                                       lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    pieces["Tusks"] = build_tusks(N + "TusksHi", HI)
    pieces["Leaf"] = build_leaf(tree, N + "LeafHi")
    top = leaf_top(tree)
    data["lotus_at"] = V(0, top.y, top.z - 0.004)
    pieces["Lotus"] = build_lotus(data["lotus_at"], N + "LotusHi")
    pieces["Anklets"] = build_anklets(N + "AnkletsHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0046, 12), (22, -18, 0.0022, 8))),
             "Seeds": build_seeds(data["lotus_at"], "Seeds_Glow_" + SEED_HEX, HI)}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


# ---------- painting ----------
def sheet_uv(nu, nv, count=1):
    uu, vv = np.zeros((nu + 1) * (nv + 1) * 2), np.zeros((nu + 1) * (nv + 1) * 2)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    return np.tile(uu, count), np.tile(vv, count)


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n = len(P)
    # white jade: cool and faintly green where it turns away from the light (its folds, under its belly and chin)
    grain = fbm(P, 30.0, 4, 3)
    mottle = fbm(P, 6.0, 3, 12)
    col = mix(np.broadcast_to(JADE, (n, 3)), JADE_TOP, smooth(0.1, 0.8, Nn[:, 2]) * 0.8)
    col = mix(col, JADE_SHADE, np.clip(smooth(0.2, -0.7, Nn[:, 2]) * 0.7 + (mottle - 0.5) * 0.6, 0, 1))
    # an elephant's skin: a fine network of cracks all over it
    cells = value_noise(P, 55.0, 4) * 0.65 + value_noise(P, 130.0, 6) * 0.35
    crackle = 1 - smooth(0.0, 0.03, np.abs(cells - 0.5))
    # its trunk: rings all down it, deeper toward its tip; pink freckles over its lower half
    tf, td = nearest_on(TRUNK_PATH, P)
    on_trunk = (1 - smooth(0.0, 0.03, td - np.array([prof(TRUNK_PROFILE, float(f)) for f in tf]) * 1.05)) * smooth(0.12, 0.25, tf)
    L = float(np.sum([(TRUNK_PATH[i + 1] - TRUNK_PATH[i]).length for i in range(len(TRUNK_PATH) - 1)]))
    ring_phase = tf * L / 0.012 + (fbm(P, 25.0, 2, 9) - 0.5) * 0.5
    rings = smooth(0.9, 0.985, np.abs(np.sin(ring_phase * math.pi))) * on_trunk * smooth(-0.6, 0.2, -Nn[:, 1] * 0.5 - Nn[:, 2] * 0.5 + 0.3)     # thin creases, mostly on its front
    # the skin's fine crackle everywhere, a little deeper at its knees
    knees = np.zeros(n)
    for key, side, knots, radii in LEGS:
        for k in (1, 2):
            c = np.array(tuple(mir(knots[k], side)))
            near = 1 - smooth(0.06, 0.1, np.linalg.norm(P - c, axis=1))
            knees = np.maximum(knees, near * smooth(0.85, 0.98, np.abs(np.sin((z - c[2]) / 0.014 * math.pi + (grain - 0.5) * 1.5))))
    legs_z = np.zeros(n)
    for key, side, knots, radii in LEGS:
        f, d = nearest_on(leg_path(knots, side), P)
        on = (1 - smooth(0.0, 0.03, d - np.array([leg_radius(radii, float(q)) for q in f]) * 1.05)) * smooth(0.3, 0.45, f)
        legs_z = np.maximum(legs_z, on * smooth(0.88, 0.985, np.abs(np.sin(z / 0.022 * math.pi + (grain - 0.5) * 1.2))) * 0.6)     # loose bands round its legs
    knees = np.maximum(knees, legs_z)
    folds = np.maximum(rings, knees * 0.8)
    col = mix(col, col * np.array([0.8, 0.84, 0.83]), np.maximum(folds * 0.75, crackle * 0.22))
    freckle_noise = value_noise(P, 75.0, 11)
    freckles = smooth(0.62, 0.7, freckle_noise) * (on_trunk * smooth(0.4, 0.7, tf) + smooth(-0.5, -0.56, y) * smooth(0.68, 0.6, z) * (1 - on_trunk))
    col = mix(col, FRECKLE, np.clip(freckles, 0, 1) * 0.85)
    col = mix(col, FRECKLE, on_trunk * smooth(0.9, 1.0, tf) * 0.6)          # its trunk's tip, pink
    # round each eye a soft grey-pink
    for side in (1, -1):
        r = np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1)
        col = mix(col, rgb(200, 170, 170), (1 - smooth(EYE_R * 1.15, EYE_R * 1.9, r)) * 0.55)
    # its lip under the trunk
    lip = (1 - smooth(0.6, 1.0, ell_dist(P, V(0, -0.535, 0.575), (0.05, 0.03, 0.022)))) * smooth(0.0, 0.4, -Nn[:, 1])
    col = mix(col, MOUTH, lip * 0.8)
    # toenails: four ivory nails round the front of each front foot, three on each hind
    nails = np.zeros(n)
    for key, side, knots, radii in LEGS:
        foot = np.array(tuple(mir(knots[3], side) + V(0, -0.012, -0.022)))
        count = 4 if key[0] == "F" else 3
        for k in range(count):
            a = (k - (count - 1) / 2) * 0.55
            c = foot + np.array((math.sin(a) * FOOT_R * 0.95, -math.cos(a) * FOOT_R * 0.95, -0.006))
            nails = np.maximum(nails, 1 - smooth(0.6, 1.0, np.linalg.norm((P - c) / np.array((0.022, 0.022, 0.016)), axis=1)))
    col = mix(col, NAIL, nails)
    relief = (grain - 0.5) * 0.0012 - folds * 0.0018 - crackle * 0.0006 + nails * 0.002
    set_verts(o, P + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.66 - 0.25 * nails + 0.1 * folds + 0.08 * crackle, np.zeros(n))


def paint_ear(o, side):
    nu = nv = 48
    uu, vv = sheet_uv(nu, nv)
    Nn = normals(o)
    _, _, _, _, out = ear_frame(side)
    inside = smooth(0.1, -0.25, Nn @ np.array(tuple(out)))         # the side toward its head
    P = verts(o)
    edge = np.minimum(np.minimum(vv, 1 - vv), 1 - uu)
    col = mix(np.broadcast_to(JADE, (len(uu), 3)), EAR_PINK, inside * smooth(0.1, 0.5, uu) * 0.7)
    freck = smooth(0.6, 0.68, value_noise(P, 80.0, 21)) * (1 - smooth(0.04, 0.2, edge))
    col = mix(col, FRECKLE, freck * 0.9)
    veins = smooth(0.9, 0.98, np.abs(np.sin((vv * 7 + uu * 1.5 + (fbm(P, 40.0, 2, 4) - 0.5)) * math.pi))) * smooth(0.2, 0.7, uu) * inside
    col = mix(col, col * np.array([0.92, 0.8, 0.82]), veins * 0.5)
    paint(o, col, np.full(len(uu), 0.6), np.zeros(len(uu)))


def paint_tusks(o):
    P = verts(o)
    tf, _ = nearest_on(catmull([mir(p, 1) for p in TUSK], 8), np.column_stack([np.abs(P[:, 0]), P[:, 1], P[:, 2]]))
    cap = smooth(0.6, 0.63, tf)
    band = smooth(0.58, 0.6, tf) * (1 - smooth(0.66, 0.68, tf))
    col = mix(np.broadcast_to(IVORY, (len(P), 3)), GOLD, np.maximum(cap, band))
    paint(o, col, 0.4 - 0.15 * cap, cap)


def paint_leaf(o, nu=40, nv=160):
    uu, vv = sheet_uv(nu, nv)
    Nn = normals(o)
    P = verts(o)
    top = smooth(-0.2, 0.4, Nn[:, 2])
    rays = 18
    vein = 1 - smooth(0.012, 0.03, np.abs(((vv * rays + 0.5) % 1.0) - 0.5) / rays * TAU * (0.06 + 0.94 * uu))
    vein = vein * smooth(0.04, 0.12, uu) * (1 - smooth(0.85, 0.97, uu))
    fine = smooth(0.85, 0.95, np.abs(np.sin((uu * 22 + (fbm(P, 30.0, 2, 7) - 0.5) * 2) * math.pi))) * 0.35
    col = mix(np.broadcast_to(LEAF, (len(uu), 3)), LEAF_DEEP, smooth(0.0, 0.8, uu) * 0.5 + (fbm(P, 12.0, 3, 5) - 0.5) * 0.4)
    col = mix(col, LEAF_VEIN, np.clip(vein + fine * 0.4, 0, 1) * 0.8)
    col = mix(col, rgb(150, 170, 80), smooth(0.9, 1.0, uu) * 0.4)                # its rim catching the light, yellower
    centre = 1 - smooth(0.0, 0.08, uu)
    col = mix(col, LEAF_VEIN, centre * 0.6)
    paint(o, np.clip(col, 0, 1), 0.45 + 0.1 * (1 - top), np.zeros(len(uu)))


def paint_lotus(o, at):
    P = verts(o)
    nu, nv = 24, 16
    per = (nu + 1) * (nv + 1) * 2
    count = sum(c for c, *_ in PETALS)
    uu, vv = sheet_uv(nu, nv, count)
    n = len(P)
    on_petal = np.zeros(n, dtype=bool)
    on_petal[:per * count] = True
    u_full = np.zeros(n)
    u_full[:per * count] = uu
    v_full = np.full(n, 0.5)
    v_full[:per * count] = vv
    blush = smooth(0.35, 1.0, u_full) ** 1.3
    col = mix(np.broadcast_to(PETAL_BASE, (n, 3)), PETAL_TIP, blush)
    veins = smooth(0.92, 0.99, np.abs(np.sin(v_full * 9 * math.pi))) * smooth(0.1, 0.4, u_full) * 0.25
    col = mix(col, PETAL_TIP * 0.92, veins)
    col = mix(col, rgb(252, 244, 190), (1 - smooth(0.0, 0.16, u_full)) * 0.7)    # yellow-white at each petal's foot (grey inside the cup, it read dirty)
    pod = ~on_petal
    podz = np.clip((P[:, 2] - at.z) / 0.06, 0, 1)
    col[pod] = mix(np.broadcast_to(POD * 0.8, (int(pod.sum()), 3)), POD, podz[pod])
    paint(o, np.clip(col, 0, 1), np.where(on_petal, 0.35, 0.55), np.zeros(n))


def paint_all(pieces, frames, data):
    paint_skin(pieces["Skin"])
    for side, tag in ((1, "L"), (-1, "R")):
        paint_ear(pieces["Ear" + tag], side)
        eye_paint(pieces["Eye" + tag], frames[tag])
    paint_tusks(pieces["Tusks"])
    paint_leaf(pieces["Leaf"])
    paint_lotus(pieces["Lotus"], data["lotus_at"])
    plain(pieces["Anklets"], GOLD, 0.28, 1.0)


def eye_paint(o, fr):
    """Warm amber going to a deep brown rim, fine fibres, a round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(30, 22, 18), (len(px), 3)).copy()
    iris = mix(rgb(222, 160, 80), rgb(120, 66, 30), smooth(PUPIL * 1.05, IRIS, r))
    iris = mix(iris, iris * 0.72, smooth(-0.2, 0.8, py / IRIS) * 0.4)
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 30 + np.sin(azi * 5) * 2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS + 0.01, r))
    col = mix(col, rgb(8, 6, 6), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.05, 0.5)
FACE_AT = (0, -0.5, 0.72)
EXTRA = [(0, -1, 0.05, 1.0, FACE_AT), (0.62, -0.75, 0.2, 1.0, FACE_AT), (1, -0.12, 0.08, 1.0, FACE_AT), (0.4, -0.9, 0.2, 0.36, tuple(EYE_C)),
         (0.5, 0.4, 0.8, 1.0, (0, 0.05, 0.8))]

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
        mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    only = [int(k) for k in ARGS[ARGS.index("views") + 1].split(",")] if "views" in ARGS else None
    allv = VIEWS + EXTRA
    shots(os.path.join(REVIEW, STAGE), [allv[k] for k in only] if only else allv, target=VIEW_AT, dist=3.6, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 4200
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 3.0, "LidUR": 3.0, "LidLL": 2.0, "LidLR": 2.0, "EarL": 1.2, "EarR": 1.2, "Tusks": 2.0, "Leaf": 1.0,
          "Lotus": 2.4, "Anklets": 0.8}
LOW_LEAF, LOW_PETAL = (8, 48), (6, 4)


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(lows["Skin"], P)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 8, 10, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low", lift=0.002)
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low", lift=0.002)
    lows["Tusks"] = build_tusks(N + "TusksLow", GAME, 8, 3)
    m = Mesh()
    m.sheet(lambda u, v: tuple(leaf_point(data["tree"], u, v)), lambda u, v: 0.004, *LOW_LEAF)
    lows["Leaf"] = m.finish(N + "LeafLow", GAME)
    lows["Lotus"] = build_lotus(data["lotus_at"], N + "LotusLow", LOW_PETAL[0], LOW_PETAL[1], GAME)
    lows["Anklets"] = build_anklets(N + "AnkletsLow", GAME, 20, 5, bell_seg=(8, 5))
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Shoulders", SPINE[4], "Chest"),
               ("Neck", NECK[0], "Shoulders"), ("Head", NECK[-1], "Neck"))
NOSE_NAMES = ["Trunk%d" % k for k in range(1, 7)]
NOSE_F = (0.1, 0.25, 0.4, 0.55, 0.7, 0.84)
NOSE_MID = (0.0,) + tuple((a + b) / 2 for a, b in zip(NOSE_F, NOSE_F[1:] + (1.0,)))
TAIL_NAMES = ["Tail1", "Tail2", "Tail3"]
TAIL_F = (0.0, 0.35, 0.7)
TAIL_MID = (-0.1,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw" + key] for key, _, _, _ in LEGS}
HEAD_ZONE = (V(0, -0.42, 0.74), (0.25, 0.19, 0.25))
PETAL_NAMES = ["Petal%d" % k for k in range(1, PETALS[0][0] + 1)]


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots):
    fs = [k / (len(knots) - 1) for k in range(len(knots))]
    return tuple((fs[k] + fs[k + 1]) / 2 for k in range(4))


def petal_frames(at):
    """Each inner petal: its base, and the line it opens on (Blender axes): a positive turn tips it outward."""
    out = []
    count, length, half_w, tilt, turn = PETALS[0]
    for k in range(count):
        a = turn + TAU * k / count
        o = V(math.sin(a), -math.cos(a), 0)
        base = at + o * 0.022 + V(0, 0, 0.012)
        out.append((base, V(0, 0, 1).cross(o).normalized()))
    return out


def skeleton(frames, data):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    parent = "Head"
    for name, f in zip(NOSE_NAMES, NOSE_F):
        bones.append((name, path_at(TRUNK_PATH, f), parent))
        parent = name
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, down, back, outv = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"),
                  ("Ear" + tag, A.lerp(B, 0.35), "Head")]
    fs = [k / (len(FRONT) - 1) for k in range(len(FRONT))]
    for key, side, knots, _ in LEGS:
        parent = "Shoulders" if key[0] == "F" else "Hips"
        line = leg_line(knots, side)
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, path_at(line, fs[k]), parent))
            parent = name
    bones.append(("Lotus", data["lotus_at"].copy(), "Body"))
    for name, (base, hinge) in zip(PETAL_NAMES, petal_frames(data["lotus_at"])):
        bones.append((name, base, "Lotus"))
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


def body_weights(P, legs_too=True):
    """The skin's weights: the trunk of its body (hips to head), its head, its trunk, its tail, its legs; a foot wholly its foot's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    head_d = ell_dist(P, HEAD_ZONE[0], HEAD_ZONE[1])
    nf, nd = nearest_on(TRUNK_PATH, P)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for key, side, knots_l, radii in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P)
        legs.append((key, side, knots_l, radii, f, d))
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        owner = None
        if legs_too:
            for key, side, knots_l, radii, f, d in legs:
                if (Vector(P[i]) - (mir(knots_l[3], side) + V(0, -0.012, -0.02))).length < 0.11 and z < 0.085:
                    owner = "Paw" + key
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if head_d[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, head_d[i])))
        # its trunk, out of its face: the head's at the root, then each bone down it
        reach = prof(TRUNK_PROFILE, float(nf[i])) * 1.12 + 0.012
        share = (1 - float(smooth(reach, reach + 0.025, nd[i]))) * float(smooth(0.06, 0.16, nf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Head"] + NOSE_NAMES, NOSE_MID, float(nf[i])), share)
        reach = prof(TAIL_PROFILE, float(tf[i])) * 1.3 + 0.012
        share = (1 - float(smooth(reach, reach + 0.02, td[i]))) * float(smooth(0.0, 0.08, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        if legs_too:
            for key, side, knots_l, radii, f, d in legs:
                if x * side <= 0.01:
                    continue
                lr = leg_radius(radii, float(f[i])) + 0.016
                outer = lr * (1.15 + 0.3 * float(smooth(0.4, 0.1, f[i])))
                mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
                bz = float(smooth(knots_l[1].z - 0.075, knots_l[1].z - 0.01, z))
                fade = float(smooth(0.0, 0.08, x * side)) * float(smooth(0.18, 0.08, abs(y - knots_l[0].y)))
                mm *= 1 - bz * (1 - fade)
                if mm > 0:
                    w = blend(w, chain_weight(LEG_NAMES[key], leg_mids(knots_l), float(f[i])), mm)
        out.append(w)
    return out


def relax_weights(mesh, w, rounds=4, keep=0.5):
    """Each vertex's weights eased toward its neighbours' a few times: where two rules meet their shares jumped from one vertex to the next, and
    that step tears as a joint folds (the Moonfang Tiger's lesson)."""
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
    weigh(lows["Leaf"], relax_weights(lows["Leaf"], body_weights(verts(lows["Leaf"]), legs_too=False)))     # it lies on its back: the trunk's weights alone
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Tusks"], "Head")
    # the lotus: its inner petals each on their own bone (so they can open), the rest on the flower's
    nu, nv = LOW_PETAL
    per = (nu + 1) * (nv + 1) * 2
    count = PETALS[0][0]
    weigh(lows["Lotus"], [{PETAL_NAMES[i // per] if i < per * count else "Lotus": 1.0} for i in range(len(lows["Lotus"].data.vertices))])
    # each anklet on its own lower leg
    aw = []
    for p in verts(lows["Anklets"]):
        key = ("F" if p[1] < 0.03 else "B") + ("L" if p[0] > 0 else "R")
        aw.append({"Leg%s3" % key: 1.0})
    weigh(lows["Anklets"], aw)
    rigid(glows["Seeds"], "Lotus")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses, in the game's axes: +X lifts what points forward (and swings what hangs forward); +Y turns to its left ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
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
        out["PawF" + side] = (-sum(f), 0, 0)
        out["PawB" + side] = (-sum(b), 0, 0)
    return out


def paw_at(rig, key):
    pb = rig.pose.bones["Paw" + key]
    return rig.matrix_world @ pb.head


def solve_legs(rig, base, front_target, back_target, start_f=(0, 0, 0), start_b=(0, 0, 0)):
    """Leg turns (upper, middle, lower, the same each side) that put each foot where it should be with the body posed as base: a small simplex search."""
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


GROUND_PARTS = {"FrontFeet": ("PawFL", "PawFR"), "HindFeet": ("PawBL", "PawBR"), "Belly": ("Body", "Chest"), "Hips": ("Hips",), "Trunk": tuple(NOSE_NAMES),
                "Tail": tuple(TAIL_NAMES), "Head": ("Head",)}

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    if STAGE == "all":
        unwrap(lows, [(lambda p: p.center.y < -0.3 and p.center.z > 0.5, 2.0), (None, 1.0)], SCALES, margin=0.012)     # (at 0.009, 4 texels overlapped)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.85, 0.83, 0.79, 1), far=("Skin",), reach=(0.006, 0.015),
                 far_reach=(0.01, 0.025), reaches={"Leaf": (0.004, 0.01), "Lotus": (0.003, 0.008)})
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
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0046, 10), (22, -18, 0.0022, 6))),
             "Seeds": build_seeds(data["lotus_at"], "Seeds_Glow_" + SEED_HEX, GAME, 8, 4)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames, data)
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
    print("Z range", round(lo, 4), round(hi, 4), "SOLE (box middle with the RootPart, down to the feet)", round((hi + bottom) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name, (base, hinge) in zip(PETAL_NAMES, petal_frames(data["lotus_at"])):
        print("PETAL", name, "hinge game axes", (round(-hinge.x, 4), round(hinge.z, 4), round(hinge.y, 4)), flush=True)
    for name in ("Hips", "Head", "Lotus", "Trunk6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    RIG = {"body": body, "rig": rig, "frames": frames, "glows": glows, "data": data}


# ---------- its stances ----------
def find_stances(rig):
    """(Elephants rest standing: lying, its column legs folded like a broken table's, seen in Blender. Nothing here needs the solver.)"""
    return {}


# ---------- its walk: unhurried, one foot at a time (hind, fore, hind, fore), each set flat down and lifted a little; solved at each step ----------
WALK_N, WALK_DUTY, WALK_REACH = 16, 0.66, 0.06
WALK_LIFT = {"F": 0.04, "B": 0.035}
WALK_LEAD = {"BL": 0.0, "FL": 0.25, "BR": 0.5, "FR": 0.75}


def walk_path(t):
    if t < WALK_DUTY:
        return -WALK_REACH + 2 * WALK_REACH * t / WALK_DUTY, 0.0
    s = (t - WALK_DUTY) / (1 - WALK_DUTY)
    return WALK_REACH - 2 * WALK_REACH * (0.5 - 0.5 * math.cos(math.pi * s)), math.sin(math.pi * s)


def find_walk(rig):
    pose(rig, {})
    rf, rb = paw_at(rig, "FL"), paw_at(rig, "BL")
    rows, sf, sb = [], (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    for k in range(WALK_N + 1):
        dy, up = walk_path((k % WALK_N) / WALK_N)
        f, b, cf, cb = solve_legs(rig, {}, (rf.y + dy, rf.z + up * WALK_LIFT["F"]), (rb.y + dy, rb.z + up * WALK_LIFT["B"]), sf, sb)
        sf, sb = f, b
        if k < WALK_N:
            rows.append((f, b, cf, cb))
        else:
            rows[0] = (f, b, cf, cb)
    return rows


def walk_table(rows, g):
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


TRUMPET = {"Neck": (0.12, 0, 0), "Head": (0.22, 0, 0), "Trunk1": (0.55, 0, 0), "Trunk2": (0.6, 0, 0), "Trunk3": (0.55, 0, 0), "Trunk4": (0.45, 0, 0),
           "Trunk5": (0.4, 0, 0), "Trunk6": (0.35, 0, 0), "EarL": (0, -0.5, 0), "EarR": (0, 0.5, 0)}       # its trunk up and curling back (less, it pointed level)
# dozing on its feet, as elephants sleep: head a little low, trunk curled, one hind foot resting on its toe
DOZE = {"Neck": (-0.05, 0, 0), "Head": (-0.1, 0, 0), "Trunk3": (-0.1, 0, 0), "Trunk4": (-0.2, 0, 0), "Trunk5": (-0.3, 0, 0), "Trunk6": (-0.35, 0, 0),
        "LegBR1": (0.08, 0, 0), "LegBR2": (-0.22, 0, 0), "LegBR3": (0.22, 0, 0), "PawBR": (-0.1, 0, 0), "Hips": (0, 0, -0.03), "EarL": (0, 0.06, 0), "EarR": (0, -0.06, 0)}
# its greeting: trunk lifted and its tip waved, ears spread
GREET = {"Head": (0.08, 0, 0), "Trunk1": (0.3, 0, 0), "Trunk2": (0.35, 0, 0), "Trunk3": (0.35, 0, 0), "Trunk4": (0.45, 0, 0), "Trunk5": (0.55, 0, 0), "Trunk6": (0.6, 0, 0),
         "EarL": (0, -0.45, 0), "EarR": (0, 0.45, 0)}
CURL = {"Trunk3": (-0.2, 0, 0), "Trunk4": (-0.35, 0, 0), "Trunk5": (-0.45, 0, 0), "Trunk6": (-0.5, 0, 0)}           # its trunk curled in under it
SWING = {"Trunk1": (0, 0.15, 0), "Trunk2": (0, 0.2, 0), "Trunk3": (0, 0.2, 0), "Trunk4": (0, 0.2, 0), "Trunk5": (0, 0.15, 0), "Trunk6": (0, 0.1, 0)}
EARS_OUT = {"EarL": (0, -0.7, 0), "EarR": (0, 0.7, 0)}
# in the air (its owner flying): it swims, as elephants do, its trunk up like a snorkel, its legs paddling
SWIM = {"Head": (0.1, 0, 0), "Trunk1": (0.3, 0, 0), "Trunk2": (0.35, 0, 0), "Trunk3": (0.3, 0, 0), "Trunk4": (0.25, 0, 0), **legs4((0.35, -0.3, 0.1), (-0.35, 0.3, -0.1)),
        "EarL": (0, -0.3, 0), "EarR": (0, 0.3, 0)}


def pose_library(frames, stances, data):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    bloom = {name: (tuple(hinge), 30.0, (0, 0, 0)) for name, (base, hinge) in zip(PETAL_NAMES, petal_frames(data["lotus_at"]))}
    return {"Blink": lids(BLINK_U, BLINK_L), "Doze": spec(DOZE), "Greet": spec(GREET), "Trumpet": spec(TRUMPET), "Curl": spec(CURL),
            "Swing": spec(SWING), "Ears": spec(EARS_OUT), "Swim": spec(SWIM), "Look": spec({"Neck": (0.08, 0.35, 0), "Head": (0.12, 0.4, 0.08)}),
            "Tail": spec({n: (0.1, 0.3, 0) for n in TAIL_NAMES}), "Bloom": bloom}


POSE_VIEWS = [(1, -0.05, 0.08, 4.0, VIEW_AT), (0.62, -0.72, 0.25, 4.0, VIEW_AT)]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    body, rig, frames, glows, data = RIG["body"], RIG["rig"], RIG["frames"], RIG["glows"], RIG["data"]
    stances = find_stances(rig)
    for name, (table, cf, cb) in stances.items():
        print("STANCE", name, "fit", round(cf, 6), round(cb, 6), "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in (v[:3] + (tuple(v[3]) if len(v) > 3 else ())))) for b, v in sorted(table.items())) + " }", flush=True)
    lib = pose_library(frames, stances, data)
    walk = find_walk(rig)
    print("WALK fit worst", max(r[2] for r in walk), max(r[3] for r in walk), flush=True)
    print("WALK_FRONT = { " + ", ".join("{ %g, %g, %g }" % r[0] for r in walk) + " }", flush=True)
    print("WALK_HIND = { " + ", ".join("{ %g, %g, %g }" % r[1] for r in walk) + " }", flush=True)
    pose(rig, spec(TRUMPET))
    tip = rig.matrix_world @ rig.pose.bones["Trunk6"].head
    print("TRUMPET tip game axes", (round(-tip.x, 3), round(tip.z, 3), round(tip.y, 3)), flush=True)
    for k in range(8):
        lib["Walk%d" % k] = spec(walk_table(walk, k / 8))
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    for name in ("Doze", "Greet", "Trumpet", "Curl", "Swim") + tuple("Walk%d" % k for k in range(8)):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
        if "shots" in ARGS and not name.startswith("Walk"):
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=420)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=560)
        for name in ("Doze", "Greet", "Trumpet", "Curl", "Swim", "Blink", "Bloom", "Ears"):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS, size=420)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.25, 3.8, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

"""The Nebula Owl (Rare, Cosmic energy; Celestial Egg): "It sees by the light of stars that have not been born yet, which makes it very hard to surprise."

A new creature. The idea: an owl whose wings are a stellar nursery, and who already knows what you are about to do. A big wide head, a deep dished face with two huge round gold eyes, each iris a disc of dust winding in to
a dark centre, under lids that rest low: an unimpressed stare. Pale brow feathers run from the beak up into tall ear tufts. Every feather is its own feather, and the sky runs across all of them: indigo, violet and magenta gas with dark
lanes of dust, a few new stars burning in it. Its breast is pale, chevroned like a real owl's, going to dusk at the flanks; it flies without a sound.
Its signature: the head is its own piece, turning freely under a ruff of feathers, so it can look right round behind itself as a real owl does.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/nebula_owl.py -- [clay|paint|all|overwrite] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX,
into the PET_KIT_TRIAL folder. overwrite: "all" into assets/pets/CelestialEgg/ itself, which undoes the hand-painted colour map
there (see the NOTE by the bake). With no stage it does "paint". Faces -Y, Z up.

What touches what: the head's lower half is buried in a round collar, hidden by the ruff, so it can turn with no skin to twist; eyes sit in the dishes of the face under their lids; the beak, brows and tufts are sunk into the head;
every feather's root is sunk into the arm of its wing, whose shoulder is sunk into the body; tail feathers are sunk into the rump; legs into the thighs' feathers, talons into the feet.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
if STAGE == "all" and not os.environ.get("PET_KIT_TRIAL"):
    # a full build into assets/ would replace the hand-painted colour map: ask for it by name
    raise SystemExit("nebula_owl: \"all\" needs PET_KIT_TRIAL set to a trial folder; \"overwrite\" builds into assets/ itself")
if STAGE == "overwrite":
    STAGE = "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "NebulaOwl"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- the frame of it ----------
HEAD_C = V(0, -0.04, 1.30)
HEAD_R = (0.40, 0.34, 0.32)
NECK_AT = V(0, -0.02, 1.02)     # the head turns about this point, on the vertical
EYE_R = 0.122
EYE_C = V(0.158, -0.262, 1.338)
EYE_AXIS = V(0.20, -0.975, 0.04).normalized()
LID_UP, LID_LOW = (26.0, 150.0, 0.0055), (-52.0, -135.0, 0.0042)       # the upper lid rests low: an unimpressed stare
LID_TILT = 6.0
BLINK_U, BLINK_L = 64.0, 22.0
DISH_R = 0.205
ARM = [V(0.27, 0.03, 0.95), V(0.64, 0.13, 0.90), V(0.95, 0.05, 0.76), V(1.27, 0.10, 0.56)]      # a broad wing, held half down like a cloak: an owl's are rounded and wide, not a gull's
ARM_PATH = catmull(ARM, 10)
ARM_F = (0.0, 1 / 3, 2 / 3, 0.86)
TAIL_ROOT = V(0, 0.34, 0.54)
LEG = [V(0.16, -0.05, 0.36), V(0.17, -0.07, 0.25), V(0.17, -0.09, 0.17)]


def along(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def arm_radius(f):
    return 0.07 - 0.05 * f


# ---------- feathers ----------
class Feather:
    """One feather: where it grows, which way, how long and wide; lift raises it over its neighbour, tilt turns it like a slat of a blind, so they overlap as real ones do."""

    def __init__(self, root, direction, length, width, lift=0.0, tilt=0.14, cup=0.012, droop=0.05, tip=0.62, group=0, f=0.0, face=None):
        self.root, self.d, self.length, self.width = root.copy(), direction.normalized(), length, width
        self.lift, self.tilt, self.cup, self.droop, self.tip, self.group, self.f = lift, tilt, cup, droop, tip, group, f
        up = face if face is not None else V(0, 0, 1)
        up = up - self.d * self.d.dot(up)
        self.up = up.normalized()
        self.side = self.up.cross(self.d).normalized()

    def point(self, u, v):
        w = 2 * v - 1
        half = self.width * min(1.0, (math.sin(math.pi * min(1.0, 0.1 + 0.9 * u) ** self.tip) + 0.04)) ** 0.62 * (0.42 + 0.58 * min(1.0, u * 4.0))
        # the root is sunk into what it grows from; only further out does it rise over its neighbour
        rise = self.lift * (0.35 + 0.65 * min(1.0, u * 3.2) ** 0.8) - 0.012 * max(0.0, 1 - u * 5)      # (a little of its height even at the root, so no two lie in one plane there)
        return self.root + self.d * self.length * u + self.side * half * w + self.up * (rise + half * w * self.tilt + self.cup * (1 - w * w) - self.droop * u * u)


def feather_thick(u, v):
    return 0.009 * (1 - u) + 0.0035


def build_feathers(feathers, name, coll, nu, nv):
    """One mesh of many feathers. Returns it, and per vertex: which feather, how far along, across, and whether it's the upper face."""
    m = Mesh()
    idx, uu, vv, top = [], [], [], []
    for k, f in enumerate(feathers):
        m.sheet(f.point, feather_thick, nu, nv)
        for i in range(nu + 1):
            for j in range(nv + 1):
                for t in (1, 0):
                    idx.append(k)
                    uu.append(i / nu)
                    vv.append(j / nv)
                    top.append(t)
    o = m.finish(name, coll)
    return o, np.array(idx), np.array(uu), np.array(vv), np.array(top)


def build_low_feathers(feathers, name, coll, nu, nv):
    """The game mesh's feathers: an upper and a lower face, not joined at the edge. Joined, the shading rounds over that edge, which bends the bake's rays off the feather: black and white streaks along every one (seen)."""
    m = Mesh()
    bm = m.bm
    idx, uu, vv, top = [], [], [], []
    for k, f in enumerate(feathers):
        upper, lower = [], []
        for i in range(nu + 1):
            ru, rl = [], []
            for j in range(nv + 1):
                u, v = i / nu, j / nv
                p = Vector(f.point(u, v))
                du = Vector(f.point(min(u + 1 / nu, 1), v)) - Vector(f.point(max(u - 1 / nu, 0), v))
                dv = Vector(f.point(u, min(v + 1 / nv, 1))) - Vector(f.point(u, max(v - 1 / nv, 0)))
                nrm = du.cross(dv)
                nrm = nrm.normalized() if nrm.length > 1e-9 else V(0, 0, 1)
                t = feather_thick(u, v) / 2
                ru.append(bm.verts.new(p + nrm * t))
                rl.append(bm.verts.new(p - nrm * t))
                idx += [k, k]
                uu += [u, u]
                vv += [v, v]
                top += [1, 0]
            upper.append(ru)
            lower.append(rl)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((upper[i][j], upper[i + 1][j], upper[i + 1][j + 1], upper[i][j + 1]))
                bm.faces.new((lower[i][j + 1], lower[i + 1][j + 1], lower[i + 1][j], lower[i][j]))
    o = m.finish(name, coll, recalc=False)
    return o, np.array(idx), np.array(uu), np.array(vv), np.array(top)


def wing_feathers(side):
    out = []

    def d(th, z=-0.1):
        return V(side * math.cos(math.radians(th)), math.sin(math.radians(th)), z)

    def on_arm(f):
        return mir(along(ARM_PATH, f), side)
    # primaries, outermost first: a fan off the hand, each inner one lying over the one outside it
    for k in range(8):
        f = 0.965 - k * (0.965 - 0.67) / 7
        out.append(Feather(on_arm(f), d(16 + k * 8.2, -0.52 + k * 0.03), 0.68 - abs(k - 2.5) * 0.022, 0.102, lift=k * 0.0085, tilt=-side * (0.04 + 0.055 * (k % 3)), tip=0.5, group=0, f=f, face=V(side * 0.3, -0.25, 1)))
    # secondaries, from the wrist in to the elbow and on
    for k in range(9):
        f = 0.655 - k * (0.655 - 0.28) / 8
        out.append(Feather(on_arm(f), d(80 + k * 2.4, -0.42), 0.60 - k * 0.006, 0.098, lift=0.03 + k * 0.0062, tilt=-side * (0.04 + 0.055 * (k % 3)), tip=0.46, group=1, f=f, face=V(side * 0.2, -0.3, 1)))
    # tertials, on the inner arm, closing the gap to the body
    for k in range(3):
        f = 0.25 - k * 0.09
        out.append(Feather(on_arm(f), d(99 + k * 7, -0.38), 0.52 - k * 0.03, 0.098, lift=0.086 + k * 0.006, tilt=-side * (0.04 + 0.055 * (k % 3)), tip=0.46, group=2, f=f, face=V(0, -0.3, 1)))
    # the greater coverts, a shorter row laid over the roots
    for k in range(13):
        f = 0.90 - k * (0.90 - 0.1) / 12
        th = 40 + k * 5.2
        out.append(Feather(on_arm(f) + V(0, -arm_radius(f) * 0.7, 0.004), d(th, -0.36), 0.33 - abs(k - 6) * 0.004, 0.074, lift=0.088 + k * 0.0034, tilt=-side * (0.03 + 0.055 * (k % 3)), droop=0.02, tip=0.46, group=3, f=f, face=V(side * 0.2, -0.3, 1)))
    # the lesser coverts, small, lapping along the arm's leading edge, so it's a wing there and not a pipe
    for k in range(11):
        f = 0.86 - k * (0.86 - 0.08) / 10
        out.append(Feather(on_arm(f) + V(0, -arm_radius(f) * 1.05, 0.002), d(24, -0.26), 0.2, 0.06, lift=0.03 + k * 0.0028, tilt=-side * (0.02 + 0.05 * (k % 3)), cup=0.012, droop=0.008, tip=0.46, group=4, f=f, face=V(side * 0.1, -0.5, 1)))
    return out


def tail_feathers():
    out = []
    for k, x in enumerate((0.0, 0.1, -0.1, 0.2, -0.2, 0.29, -0.29)):
        # the outer ones first underneath; the middle pair on top
        rank = 3 - round(abs(x) / 0.098)
        out.append(Feather(TAIL_ROOT + V(x * 0.42, 0, 0), V(x * 1.25, 1, -0.62), 0.58 - abs(x) * 0.26, 0.112, lift=rank * 0.015, tilt=-0.08 * (1 if x >= 0 else -1), droop=0.03, tip=0.44, group=0, f=x, face=V(0, 0.55, 1)))
    return out


def tuft_feathers(side):
    root = V(side * 0.235, -0.03, 1.525)
    out = []
    for k, (dx, dy, dz, length, width) in enumerate(((0.40, 0.14, 0.90, 0.40, 0.074), (0.16, 0.22, 0.96, 0.29, 0.066), (0.68, 0.10, 0.72, 0.29, 0.064))):
        out.append(Feather(root + V(side * 0.022 * (k if k < 2 else -1.5), 0.012 * k, -0.018 * k), V(side * dx, dy, dz), length, width, lift=0.016 * (2 - k), tilt=0.0, cup=-0.014, droop=0.0, tip=0.62, f=k, face=V(side * 0.2, -1, 0.2)))
    return out


def brow_feathers(side, tree):
    """Pale feathers from the bridge of the beak out over each eye: its whole expression lives in these. Each is rooted on the head itself."""
    out = []
    for k, (x0, z0, dx, dz, length, width) in enumerate(((0.03, 1.452, 0.93, 0.30, 0.235, 0.042), (0.135, 1.492, 0.93, 0.30, 0.135, 0.032))):
        hit = tree.ray_cast(V(side * x0, -1.0, z0), V(0, 1, 0), 2.0)[0]
        out.append(Feather(V(side * x0, hit.y - 0.004, z0), V(side * dx, 0.44, dz), length, width, lift=0.012, tilt=0.0, cup=0.006, droop=0.016, tip=0.6, f=k))
    return out


def ruff_feathers():
    """A ring of short feathers hung from the head over the collar, so nothing shows where it turns."""
    out = []
    n = 34
    for k in range(n):
        a = TAU * k / n
        c, s = math.cos(a), math.sin(a)
        low = k % 2
        # two staggered rows: under the face in front, low on the nape behind
        # (the outer row starts higher, inside the head, and runs parallel to the inner one a little clear of it: rooted, and no ray of the bake reaches across)
        rad = 0.312 + 0.018 * low
        root = V(c * rad * 0.97, HEAD_C.y + s * rad * 0.86, 1.135 + 0.025 * low)      # (the head is narrower front to back: well inside it, all the way round)
        out.append(Feather(root, V(c * 0.30, s * 0.30, -1), 0.15 + 0.055 * low, 0.07, lift=0.0, tilt=0.0, cup=-0.003, droop=0.0, tip=1.25, f=k, face=V(c, s, 0.25)))      # short and round-ended: long, narrow points in a pale ring under the face read as a row of fangs
    return out


# ---------- the body ----------
def build_body():
    core = Mesh()
    core.ball(V(0, 0.03, 0.70), (0.40, 0.355, 0.42))        # the barrel
    core.ball(V(0, -0.09, 0.80), (0.365, 0.285, 0.30))      # the full chest
    core.ball(V(0, -0.055, 0.50), (0.335, 0.295, 0.24))     # the low belly
    core.ball(V(0, 0.23, 0.58), (0.23, 0.19, 0.20))         # the rump the tail grows from
    core.tube([V(0, -0.02, 0.92), V(0, -0.02, 1.02), V(0, -0.02, 1.13)], lambda f: 0.285 - 0.02 * f, sides=32)      # the round collar the head turns on
    for side in (1, -1):
        core.ball(V(side * 0.31, 0.04, 0.90), (0.125, 0.16, 0.13))     # the shoulder
        core.ball(V(side * 0.17, -0.05, 0.36), (0.135, 0.145, 0.135))  # the feathered thigh: trousers down to the foot
    c = core.finish(N + "BodyHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.012, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 20}), ("REMESH", {"mode": "VOXEL", "voxel_size": 0.0052, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    base = bpy.data.objects.new(N + "BodyBase", c.data.copy())
    HI.objects.link(base)
    base.hide_render = True
    return c, base


def dish_field(x, z, side):
    return np.sqrt((x - side * EYE_C.x) ** 2 + ((z - EYE_C.z) * 1.02) ** 2)


def build_head():
    """Wide and flat-faced. The two dishes of the face are pressed in after the first remesh, as a sculptor would: they are what shows the eyes."""
    m = Mesh()
    m.ball(HEAD_C, HEAD_R)
    m.ball(V(0, -0.02, 1.08), (0.235, 0.225, 0.16))         # the lower half, buried in the collar
    for side in (1, -1):
        m.ball(V(side * 0.235, -0.03, 1.51), (0.125, 0.12, 0.10))   # the base of each tuft
    o = m.finish(N + "HeadHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.009, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    P = verts(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    front = smooth(-0.05, -0.22, y)
    push = np.zeros_like(x)
    for side in (1, -1):
        d = dish_field(x, z, side)
        push += (0.062 * np.exp(-(d / (DISH_R * 0.72)) ** 2) - 0.018 * np.exp(-((d - DISH_R * 1.2) / 0.05) ** 2)) * (x * side > -0.02)
    # the ridge down the middle, between the dishes, comes forward to the beak
    push -= 0.03 * np.exp(-(x / 0.035) ** 2) * smooth(1.16, 1.3, z) * (1 - smooth(1.42, 1.52, z))
    P[:, 1] += push * front
    set_verts(o, P)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0048, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    base = bpy.data.objects.new(N + "HeadBase", o.data.copy())
    HI.objects.link(base)
    base.hide_render = True
    return o, base


def beak_paths():
    top = catmull([V(0, -0.325, 1.325), V(0, -0.395, 1.295), V(0, -0.425, 1.24), V(0, -0.412, 1.185)], 6)
    low = catmull([V(0, -0.33, 1.215), V(0, -0.375, 1.205), V(0, -0.395, 1.19)], 5)
    return top, low


def top_beak_radius(f):
    return 0.056 * (1 - f) ** 0.7 + 0.005


def low_beak_radius(f):
    return 0.038 * (1 - f) ** 0.8 + 0.006


def build_beak(name, coll, sides, step):
    top, _ = beak_paths()
    pts = top[::step]
    if pts[-1] != top[-1]:
        pts.append(top[-1])
    m = Mesh()
    m.tube(pts, top_beak_radius, sides=sides, flat=0.92, plane=V(1, 0, 0))
    return m.finish(name, coll)


def build_beak_low(name, coll, sides, step):
    _, low = beak_paths()
    pts = low[::step]
    if pts[-1] != low[-1]:
        pts.append(low[-1])
    m = Mesh()
    m.tube(pts, low_beak_radius, sides=sides, flat=1.1, plane=V(1, 0, 0))
    return m.finish(name, coll)


def build_arms(name, coll, sides, step):
    m = Mesh()
    which = []
    for side in (1, -1):
        path = [mir(p, side) for p in ARM_PATH]
        pts = path[::step]
        if pts[-1] != path[-1]:
            pts.append(path[-1])
        before = len(m.bm.verts)
        m.tube(pts, arm_radius, sides=sides, flat=1.55, plane=V(0, 1, 0.2).normalized())
        which += [side] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


def leg_path(side):
    return catmull([mir(p, side) for p in LEG], 4)


def build_legs(name, coll, sides, step):
    m = Mesh()
    which = []
    for side in (1, -1):
        path = leg_path(side)
        pts = path[::step]
        if pts[-1] != path[-1]:
            pts.append(path[-1])
        before = len(m.bm.verts)
        m.tube(pts, lambda f: 0.078 - 0.012 * f, sides=sides, flat=0.94)
        m.ball(mir(LEG[2], side) + V(0, -0.012, -0.012), (0.066, 0.076, 0.042), 14 if sides > 8 else 8, 8 if sides > 8 else 5)
        which += [side] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


def talon_paths(side):
    foot = mir(LEG[2], side) + V(0, -0.01, -0.012)
    out = []
    for a, l, r in ((-0.48, 0.14, 0.026), (0.0, 0.16, 0.028), (0.48, 0.14, 0.026), (math.pi, 0.105, 0.025)):
        d = V(math.sin(a) * side, -math.cos(a), 0)
        out.append((catmull([foot + d * 0.02, foot + d * l * 0.62 + V(0, 0, -0.006), foot + d * l - V(0, 0, 0.042), foot + d * l * 0.9 - V(0, 0, 0.082)], 4), r))
    return out


def build_talons(name, coll, sides, step):
    m = Mesh()
    which = []
    for side in (1, -1):
        before = len(m.bm.verts)
        for path, r in talon_paths(side):
            pts = path[::step]
            if pts[-1] != path[-1]:
                pts.append(path[-1])
            m.tube(pts, lambda f, r=r: r * (1 - f) ** 0.8 + 0.003, sides=sides)
        which += [side] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.1, 0.92)
CLOSE_FACE = (0.36, -0.9, 0.08, 2.4, (0, -0.2, 1.36))
FACE_ON = (0, -1, 0.03, 2.2, (0, -0.2, 1.38))
EXTRA = [CLOSE_FACE, FACE_ON, (0.1, 0.55, 0.85, 3.6, (0.62, 0.3, 0.8)), (0.3, 0.45, 0.85, 4.4, (1.0, 0.3, 0.8)), (0.7, -0.25, -0.5, 4.2, (0.9, 0.3, 0.7)), (0.45, -0.6, -0.15, 2.0, (0.15, -0.05, 0.25)), (0, 0.9, 0.35, 3.0, (0, 0.5, 0.6))]


# ---------- paint ----------
NIGHT, INDIGO, VIOLET, MAGENTA = rgb(12, 10, 40), rgb(38, 30, 104), rgb(112, 62, 188), rgb(204, 72, 158)
TEAL, PEARL, LAVENDER, DUSK = rgb(36, 150, 168), rgb(240, 232, 244), rgb(176, 160, 212), rgb(74, 60, 126)
GOLD, AMBER, HORN, DARK_HORN = rgb(255, 206, 92), rgb(214, 124, 34), rgb(206, 170, 104), rgb(70, 52, 44)


def worley(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2 + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                d1 = np.where(nearer, d, d1)
    return d1, d2


def nebula(P):
    """The sky: one field through all of it, so the gas runs on from feather to feather. Not a pattern laid on: billows of gas, lanes of dust across them, and stars, thick in some places and none in others."""
    Q = P * np.array((1.0, 1.0, 0.8))
    warp = (fbm(Q, 1.7, 3, 41) - 0.5)[:, None]
    gas = fbm(Q + warp * 1.1, 2.5, 5, 7)
    hot = fbm(Q + warp * 0.9 + 4.0, 2.2, 5, 19)
    cold = fbm(Q - warp + 9.0, 2.8, 4, 29)
    col = mix(NIGHT, INDIGO, smooth(0.34, 0.54, gas))
    col = mix(col, VIOLET, smooth(0.50, 0.70, gas))
    col = mix(col, TEAL, smooth(0.56, 0.72, cold) * (1 - smooth(0.5, 0.66, hot)) * 0.8)
    col = mix(col, MAGENTA, smooth(0.54, 0.70, hot) * smooth(0.42, 0.58, gas) * 0.85)
    col = mix(col, rgb(246, 200, 226), smooth(0.70, 0.84, hot) * smooth(0.56, 0.72, gas) * 0.75)
    lane = 1 - np.abs(2 * fbm(Q + warp * 0.6 + 2.0, 3.6, 4, 53) - 1)
    col = mix(col, NIGHT * 0.7, smooth(0.86, 0.985, lane) * 0.85)
    d1, _ = worley(P, 26.0, 61)
    d2, _ = worley(P, 62.0, 67)
    thick = smooth(0.42, 0.62, fbm(P, 3.2, 3, 71))
    stars = (1 - smooth(0.035, 0.085, d1)) * thick + (1 - smooth(0.05, 0.11, d2)) * thick * 0.45
    col = mix(col, rgb(240, 236, 255), np.clip(stars, 0, 1))
    return col, gas, stars


def paint_feathers(o, idx, uu, vv, top, kind="sky", hidden_under=None, flight=None):
    """Each feather's own bars, shaft and pale edge over the sky that runs across them all; pale below, as an owl's are.
    hidden_under: per feather, 1 where its underside lies over another feather, so nobody sees it from below.
    flight: a flight feather's underside goes dark toward its root, where it rises off the arm and faces forward: pale there read as white flecks along the wing in the game's poses (seen in Studio)."""
    P = verts(o)
    Nn = normals(o)
    sky, gas, stars = nebula(P)
    w = np.abs(2 * vv - 1)
    seed = np.sin(idx * 12.9898) * 0.5 + 0.5
    # the soft bars a real owl has, drawn with the gas instead of pigment
    bars = np.sin(uu * (15 + 3 * seed) + 2.2 * w + seed * 6) * 0.5 + 0.5
    bar_mask = smooth(0.62, 0.92, bars) * smooth(0.12, 0.3, uu)
    top_col = sky * (1 - 0.26 * bar_mask)[:, None]
    top_col = mix(top_col, LAVENDER, smooth(0.9, 0.995, np.maximum(uu ** 1.5, w * uu ** 0.2)) * 0.62)      # the pale edge that picks each feather out
    # beneath: pearl, barred in dusk
    under_bars = smooth(0.48, 0.74, np.sin(uu * (11 + 2 * seed) + seed * 5) * 0.5 + 0.5)
    under = mix(PEARL, mix(LAVENDER, DUSK, 0.4), under_bars * smooth(0.15, 0.35, uu) * 0.85)
    if hidden_under is not None:
        under = mix(under, sky * 0.55, hidden_under[idx])
    if flight is not None:
        under = mix(under, rgb(30, 24, 84), flight[idx] * (1 - smooth(0.4, 0.62, uu)))
    col = np.where(top[:, None] > 0, top_col, under)
    if kind == "tuft":      # dark gas at the root, going to pale gold-white at the tip, in front and behind
        col = mix(col, mix(LAVENDER, PEARL, smooth(0.45, 0.9, uu)), smooth(0.45, 0.95, uu) * 0.85)
    if kind == "ruff":      # pale under the face, the sky behind
        front = smooth(0.05, -0.2, P[:, 1])
        col = mix(sky * (1 - 0.2 * bar_mask)[:, None], mix(PEARL, LAVENDER, smooth(0.1, 0.9, uu)), front)
        col = mix(col, DUSK * 0.7, smooth(0.86, 1.0, uu) * front * 0.5)
    shaft = 1 - smooth(0.018, 0.05, w)
    col = mix(col, np.where(top[:, None] > 0, LAVENDER, DUSK), shaft * (0.55 - 0.3 * uu)[:, None][:, 0])
    barbs = np.sin((uu * 3 + w * 2.2) * 62 + seed * 9) * 0.5 + 0.5
    col = col * (1 - 0.1 * barbs * smooth(0.04, 0.14, w))[:, None]
    relief = 0.0016 * shaft + 0.0006 * barbs
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.68 - 0.14 * shaft)


def plain_feathers(o, idx, uu, vv, top):
    """The brows: pale, a dark line beneath, what its whole expression is drawn with."""
    col = mix(PEARL, LAVENDER, smooth(0.45, 1.0, uu) * 0.5)
    col = np.where(top[:, None] > 0, col, DUSK)
    paint(o, col, 0.7)


def scale_rows(theta, z, across, down):
    """Overlapping feather shapes on a rounded surface: per point, how far toward a feather's tip, how far off its middle."""
    row = np.floor(z / down)
    fz = z / down - row
    t = theta / across + 0.5 * (row % 2)
    fx = t - np.floor(t) - 0.5
    return fz, fx


def paint_body(o):
    """Back and shoulders are the sky; the breast is pale, chevroned, going to dusk at the flanks and pale again low down."""
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    sky, gas, stars = nebula(P)
    theta = np.arctan2(x, -(y + 0.02))
    fz, fx = scale_rows(theta, z, 0.34, 0.082)
    # one feather's outline: rounded at its lower end
    tip = fz - 0.82 * (1 - (2 * fx) ** 2)
    dome = smooth(0.0, -0.45, tip)
    edge = (1 - smooth(0.0, 0.09, np.abs(tip)))
    breast = smooth(1.5, 0.95, np.abs(theta))
    # not a net: only each feather's own small dark crescent, near its tip, broken up, some stronger than others (a net of lines read as quilting)
    crescent = (1 - smooth(0.0, 0.085, np.abs(tip + 0.2))) * (1 - smooth(0.2, 0.36, np.abs(fx)))
    tone = fbm(P, 6.5, 3, 83)
    pale = mix(PEARL, LAVENDER, smooth(0.25, 1.05, np.abs(theta)) * 0.75)
    pale = mix(pale, mix(DUSK, INDIGO, 0.25), crescent * smooth(0.36, 0.62, tone + 0.25 * np.abs(theta)) * 0.9)
    col = mix(sky * (0.84 + 0.2 * dome)[:, None], pale, breast)
    col = mix(col, DUSK * 0.8, edge * (1 - breast) * 0.45)
    # the fine stars carry on faintly over the pale breast
    col = mix(col, rgb(255, 250, 235), np.clip(stars, 0, 1) * breast * 0.6)
    # the wing's shadow on the flank and the head's on the collar: the bake's occlusion stays inside each piece
    col = col * (1 - 0.5 * smooth(1.04, 1.12, z))[:, None]
    disp = (0.0045 * dome - 0.0025 * edge * (1 - breast)) * smooth(0.0, 0.2, z)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, 0.78 - 0.1 * dome)


def paint_head(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    sky, gas, stars = nebula(P)
    front = smooth(-0.1, -0.24, y)
    d1, d2 = worley(P, 34.0, 13)
    fine = smooth(0.0, 0.3, d2 - d1)
    # the crown: fine feathers in the sky, a shade darker
    col = sky * (0.72 + 0.26 * fine)[:, None]
    # the face: two dishes of fine feathers raying out from each eye, pearl at the centre, lavender outward, with a dark rim
    disc = np.zeros_like(x)
    rim = np.zeros_like(x)
    face = np.broadcast_to(PEARL, (len(x), 3)).copy()
    for side in (1, -1):
        mine = x * side > -0.002
        d = dish_field(x, z, side)
        a = np.arctan2(z - EYE_C.z, x - side * EYE_C.x)
        rays = np.sin(a * 46 + 1.2 * np.sin(a * 5)) * 0.5 + 0.5
        tone = mix(PEARL, LAVENDER, smooth(0.1, DISH_R * 1.05, d))
        tone = tone * (1 - 0.24 * rays * smooth(0.11, 0.17, d))[:, None]
        tone = mix(tone, rgb(30, 20, 58), (1 - smooth(0.128, 0.152, d)) * 0.82)      # the dark ring round the eye
        face = np.where((mine)[:, None], tone, face)
        disc = np.where(mine, 1 - smooth(DISH_R * 1.04, DISH_R * 1.2, d), disc)
        rim = np.where(mine, np.maximum(rim, np.exp(-((d - DISH_R * 1.16) / 0.018) ** 2)), rim)
    disc = disc * front
    col = mix(col, face, disc)
    col = mix(col, rgb(22, 14, 46), rim * front * 0.9)
    # the bristled X down the middle of the face, pale, running up from the beak
    bridge = np.exp(-(x / 0.045) ** 2) * smooth(1.15, 1.28, z) * (1 - smooth(1.42, 1.5, z)) * front
    col = mix(col, rgb(250, 244, 236), bridge * 0.9)
    rough = 0.8 - 0.1 * disc
    a = np.arctan2(z - EYE_C.z, np.abs(x) - EYE_C.x)
    disp = 0.0025 * disc * (np.sin(a * 46) * 0.5 + 0.5) + (1 - disc) * 0.0035 * fine
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, rough)


def eye_paint(o, fr):
    """A disc of dust winding in to a dark centre, the way a new star gathers: old gold burning to white-gold near the middle, lanes of dark spiralling through it."""
    px, py, a = eye_coords(o, fr)
    IRIS = 0.88
    r = np.where(a > 0, np.sqrt(px ** 2 + py ** 2) / IRIS, 3.0)
    azi = np.arctan2(py, px) * (1 if fr.side > 0 else -1)
    iris = mix(rgb(255, 234, 150), GOLD, smooth(0.34, 0.6, r))
    iris = mix(iris, AMBER, smooth(0.62, 1.0, r))
    arms = np.sin(azi * 3 + np.log(np.maximum(r, 0.04)) * 8.5) * 0.5 + 0.5
    iris = iris * (1 - 0.46 * smooth(0.6, 0.95, arms) * smooth(0.36, 0.6, r))[:, None]
    fibres = np.sin(azi * 40 + r * 6) * 0.5 + 0.5
    iris = iris * (1 - 0.1 * fibres)[:, None]
    iris = iris * (1 - 0.42 * smooth(0.0, 0.8, py / IRIS))[:, None]        # the lid's shade
    col = mix(rgb(20, 12, 30), iris, 1 - smooth(0.965, 1.0, r))
    pu = np.where(a > 0, np.sqrt(px ** 2 + py ** 2) / (IRIS * 0.40), 3.0)
    col = mix(col, rgb(4, 3, 14), 1 - smooth(0.92, 1.0, pu))
    # a fleck of violet in the pupil: the star not born yet
    speck = np.where(a > 0, np.sqrt((px + 0.08) ** 2 + (py + 0.1) ** 2), 3.0)
    col = mix(col, rgb(130, 76, 220), (1 - smooth(0.02, 0.1, speck)) * 0.75)
    paint(o, col, np.full(len(px), 0.06))


def paint_arms(o):
    P = verts(o)
    Nn = normals(o)
    sky, _, _ = nebula(P)
    col = mix(sky, mix(PEARL, LAVENDER, 0.5), smooth(0.0, -0.7, Nn[:, 2]))
    paint(o, col, 0.75)


def paint_legs(o):
    P = verts(o)
    d1, d2 = worley(P, 46.0, 3)
    col = mix(mix(PEARL, LAVENDER, 0.4), mix(LAVENDER, DUSK, 0.4), smooth(0.3, 0.9, d2 - d1))
    paint(o, col, 0.82)


def paint_beak(o, lower):
    P = verts(o)
    Nn = normals(o)
    col = mix(HORN, rgb(244, 224, 170), smooth(0.05, 0.7, -Nn[:, 1]) * 0.8)
    col = mix(col, DARK_HORN, smooth(1.26, 1.32, P[:, 2]) * 0.8 if not lower else 0.0 * P[:, 2])
    paint(o, col, 0.32)


def paint_talons(o):
    P = verts(o)
    paint(o, mix(rgb(46, 36, 40), rgb(190, 150, 90), smooth(0.13, 0.18, P[:, 2])), 0.3)


# ---------- the new stars: a few, burning in the wing ----------
STAR_PICKS = ((0, 0.74, 0.34, 0.030), (2, 0.60, 0.30, 0.022), (5, 0.80, 0.36, 0.026), (9, 0.72, 0.30, 0.034), (12, 0.80, 0.36, 0.022), (15, 0.68, 0.30, 0.026), (22, 0.84, 0.32, 0.024))      # (u, v: each feather's other edge lies under its neighbour, so these keep to the open side)


def flat_star(m, c, nrm, size, points=8, waist=0.4):
    """A small burst lying on the feather. Eight unequal points, so it isn't read as any symbol."""
    a = nrm.orthogonal().normalized()
    b = nrm.cross(a).normalized()
    hub = m.bm.verts.new(c - nrm * 0.0115)      # its point rests on the feather; the rays stand just clear of it, where they can be seen
    ring = []
    for k in range(points * 2):
        th = TAU * k / (points * 2)
        r = size * (waist if k % 2 else (1.0 if k % 4 == 0 else 0.62))
        ring.append(m.bm.verts.new(c + a * math.cos(th) * r + b * math.sin(th) * r))
    for k in range(points * 2):
        m.bm.faces.new((hub, ring[k], ring[(k + 1) % (points * 2)]))


def low_face_point(f, u, v, nu=5, nv=1):
    """A point on the game mesh's flat face of a feather, which cuts the corners of the curved one."""
    x, y = u * nu, v * nv
    i, j = min(int(x), nu - 1), min(int(y), nv - 1)
    fx, fy = x - i, y - j
    a = Vector(f.point(i / nu, j / nv)).lerp(Vector(f.point((i + 1) / nu, j / nv)), fx)
    b = Vector(f.point(i / nu, (j + 1) / nv)).lerp(Vector(f.point((i + 1) / nu, (j + 1) / nv)), fx)
    return a.lerp(b, fy)


def build_stars(side, tag, feathers, low=False):
    m = Mesh()
    fs = []
    for index, u, v0, size in STAR_PICKS:
        f = feathers[index]
        v = v0 if side > 0 else 1 - v0
        p = low_face_point(f, u, v) if low else f.point(u, v)
        nrm = (low_face_point(f, min(u + 0.02, 1), v) - p).cross(low_face_point(f, u, min(v + 0.02, 1)) - p).normalized() if low else (f.point(min(u + 0.02, 1), v) - p).cross(f.point(u, min(v + 0.02, 1)) - p).normalized()
        if nrm.z < 0:
            nrm = -nrm
        # (nudged out over whatever lies on top of it: it is hung on the feather's own bones)
        flat_star(m, p + nrm * (0.012 + feather_thick(u, v) / 2), nrm, size)
        fs += [f.f] * (1 + 16)
    o = m.finish(N + "Stars" + tag + "_Glow_d6b4ff", HI, smooth_shade=False, recalc=False)
    return o, fs


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    frames = {}
    pieces["Skin"], data["BodyBase"] = build_body()
    pieces["Head"], data["HeadBase"] = build_head()
    head_tree = tree_of(data["HeadBase"])
    if not clay:
        paint_body(pieces["Skin"])
        paint_head(pieces["Head"])
    def feathers(key, flist, nu, nv, painter):
        o, idx, uu, vv, top = build_feathers(flist, N + key + "Hi", HI, nu, nv)
        pieces[key] = o
        data[key] = flist
        if not clay:
            painter(o, idx, uu, vv, top)
    glows = {}
    for side, tag in ((1, "L"), (-1, "R")):
        wing = wing_feathers(side)
        feathers("Wing" + tag, wing, 70, 26, lambda *a: paint_feathers(*a, hidden_under=np.array([1.0 if f.group >= 3 else 0.0 for f in wing]), flight=np.array([1.0 if f.group < 3 else 0.0 for f in wing])))
        feathers("Tuft" + tag, tuft_feathers(side), 60, 22, lambda *a: paint_feathers(*a, kind="tuft"))
        feathers("Brow" + tag, brow_feathers(side, head_tree), 40, 14, plain_feathers)
        glows["Stars" + tag], data["Stars" + tag] = build_stars(side, tag, wing)
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        if not clay:
            eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, mix(DUSK, LAVENDER, 0.45), rgb(14, 8, 30))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, mix(LAVENDER, PEARL, 0.4), rgb(20, 12, 38), lower_share=0.7)
    feathers("Tail", tail_feathers(), 70, 26, paint_feathers)
    feathers("Ruff", ruff_feathers(), 30, 14, lambda *a: paint_feathers(*a, kind="ruff"))
    pieces["Arms"], _ = build_arms(N + "ArmsHi", HI, 24, 1)
    pieces["Beak"] = build_beak(N + "BeakHi", HI, 28, 1)
    pieces["BeakLow"] = build_beak_low(N + "BeakLowHi", HI, 22, 1)
    pieces["Legs"], _ = build_legs(N + "LegsHi", HI, 18, 1)
    pieces["Talons"], _ = build_talons(N + "TalonsHi", HI, 12, 1)
    if not clay:
        paint_arms(pieces["Arms"])
        paint_beak(pieces["Beak"], False)
        paint_beak(pieces["BeakLow"], True)
        paint_legs(pieces["Legs"])
        paint_talons(pieces["Talons"])
    glows["Glints"] = glints(frames, HI, "Glints_Glow_f0ead8", spots=((-24, 24, 0.0185, 16), (18, -22, 0.0085, 10)))
    return pieces, frames, glows, data


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 1.4
        o.data.materials.append(m)
        o.visible_shadow = False


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.30, 0.33, 0.42, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.07, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=9.0, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = (900, 1000, 820, 1100, 760)
HEAD_QUADS = (1100, 1250, 1000, 1350, 900)
TEXELS = {"Head": 1.9, "WingL": 1.0, "WingR": 1.0, "Tail": 0.9, "TuftL": 1.2, "TuftR": 1.2, "BrowL": 1.3, "BrowR": 1.3, "Ruff": 1.0, "Arms": 0.7, "Beak": 1.6, "BeakLow": 1.3, "Legs": 0.8, "Talons": 0.9,
          "EyeL": 2.8, "EyeR": 2.8, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5}
META = {}


def truest(base, name, targets, limit=0.012):
    """QuadriFlow can wreck a small form and leave the mesh checks green: try several, measure each against the sculpt, keep the truest."""
    tree = tree_of(base)
    best, best_gap = None, 1e9
    for quads in targets:
        o = retopo_skin(base, N + "Try", quads)
        gap = surface_gap(o, tree)
        print("TRY", name, quads, len(o.data.polygons), "gap", round(gap, 4), flush=True)
        if gap < best_gap:
            if best:
                bpy.data.objects.remove(best, do_unlink=True)
            best, best_gap = o, gap
        else:
            bpy.data.objects.remove(o, do_unlink=True)
        if gap < 0.007:
            break
    assert best_gap < 0.014, name + ": every re-mesh strayed from the sculpt"
    best.name = N + name + "Low"
    for v in best.data.vertices:
        v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.8)
    return best


def cut_faces(o, test):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    dead = [f for f in bm.faces if test(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    # and any scrap the cut left
    seen, scraps = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        stack, group = [f], []
        seen.add(f)
        while stack:
            g = stack.pop()
            group.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        if len(group) < 60:
            scraps += group
    bmesh.ops.delete(bm, geom=scraps, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    print("CUT", o.name, len(dead), "scraps", len(scraps), flush=True)


def build_low(pieces, frames, data):
    skin = truest(data["BodyBase"], "Skin", SKIN_QUADS)
    head = truest(data["HeadBase"], "Head", HEAD_QUADS)
    # what is buried for good: the collar's top inside the head, the head's underside inside the collar
    cut_faces(skin, lambda c: c.z > 1.125)
    cut_faces(head, lambda c: c.z < 1.03)
    lows = {"Skin": skin, "Head": head}

    def feathers(key, nu, nv):
        lows[key], *META[key] = build_low_feathers(data[key], N + key + "Low", GAME, nu, nv)
    for tag in ("L", "R"):
        feathers("Wing" + tag, 5, 1)
        feathers("Tuft" + tag, 5, 1)
        feathers("Brow" + tag, 3, 1)
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 20, 12)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    feathers("Tail", 5, 1)
    feathers("Ruff", 3, 1)
    lows["Arms"], META["Arms"] = build_arms(N + "ArmsLow", GAME, 7, 4)
    lows["Beak"] = build_beak(N + "BeakLowPiece", GAME, 8, 3)
    lows["BeakLow"] = build_beak_low(N + "BeakUnderLow", GAME, 7, 3)
    lows["Legs"], META["Legs"] = build_legs(N + "LegsLow", GAME, 8, 3)
    lows["Talons"], META["Talons"] = build_talons(N + "TalonsLow", GAME, 5, 3)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
WING_NAMES = ("Wing%s1", "Wing%s2", "Wing%s3", "WingP%s")
TAIL_AT = {"L": V(0.13, 0.40, 0.52), "R": V(-0.13, 0.40, 0.52)}


def skeleton(frames, data):
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, 0.02, 0.72), "Root"), ("Chest", V(0, -0.14, 0.78), "Body"), ("Head", NECK_AT.copy(), "Body"), ("BeakLow", V(0, -0.33, 1.215), "Head"),
             ("Tail", TAIL_ROOT.copy(), "Body"), ("TailL", TAIL_AT["L"].copy(), "Tail"), ("TailR", TAIL_AT["R"].copy(), "Tail")]
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Brow" + tag, V(side * 0.03, -0.37, 1.45), "Head"), ("Tuft" + tag, V(side * 0.235, -0.03, 1.525), "Head")]
        parent = "Body"
        for name, f in zip(WING_NAMES, ARM_F):
            b = name % tag
            bones.append((b, mir(along(ARM_PATH, f), side), parent))
            parent = b
        bones += [("Leg" + tag, mir(LEG[0], side), "Body"), ("Foot" + tag, mir(LEG[2], side), "Leg" + tag)]
    return armature(bones)


def wing_weight(tag, f):
    names = [n % tag for n in WING_NAMES]
    return chain_weight(names, ARM_F, f)


def bind_all(lows, rig, glows, data):
    # the body: one piece, with a soft chest that breathes
    P = verts(lows["Skin"])
    chest = np.exp(-(np.linalg.norm((P - np.array((0, -0.2, 0.74))) / np.array((0.34, 0.26, 0.30)), axis=1)) ** 2) * 0.8
    weigh(lows["Skin"], [{"Body": 1 - float(c), "Chest": float(c)} if c > 0.02 else {"Body": 1.0} for c in chest])
    for tag in ("L", "R"):
        flist = data["Wing" + tag]
        idx = META["Wing" + tag][0]
        weigh(lows["Wing" + tag], [wing_weight(tag, flist[int(i)].f) for i in idx])
        rigid(lows["Tuft" + tag], "Tuft" + tag)
        rigid(lows["Brow" + tag], "Brow" + tag)
        for key in ("Eye", "LidU", "LidL"):
            rigid(lows[key + tag], key + tag)
        weigh(glows["Stars" + tag], [wing_weight(tag, f) for f in data["Stars" + tag]])
    for key in ("Head", "Ruff", "Beak"):
        rigid(lows[key], "Head")
    rigid(lows["BeakLow"], "BeakLow")
    # the arms along their own bones
    which = META["Arms"]
    arm_pts = verts(lows["Arms"])
    out = []
    for p, side in zip(arm_pts, which):
        path = [mir(q, int(side)) for q in ARM_PATH]
        f, _ = nearest_on(path, np.array([p]))
        out.append(wing_weight("L" if side > 0 else "R", float(f[0])))
    weigh(lows["Arms"], out)
    # the tail: the middle feathers on Tail, the outer ones fanning on TailL and TailR
    tlist = data["Tail"]
    weights = []
    for i in META["Tail"][0]:
        x = tlist[int(i)].f
        if abs(x) < 0.01:
            weights.append({"Tail": 1.0})
        else:
            share = min(1.0, abs(x) / 0.2)
            weights.append({"Tail": 1 - share, ("TailL" if x > 0 else "TailR"): share})
    weigh(lows["Tail"], weights)
    legs = verts(lows["Legs"])
    weigh(lows["Legs"], [{("Foot" if p[2] < LEG[2].z + 0.03 else "Leg") + ("L" if side > 0 else "R"): 1.0} for p, side in zip(legs, META["Legs"])])
    weigh(lows["Talons"], [{"Foot" + ("L" if side > 0 else "R"): 1.0} for side in META["Talons"]])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateNebulaOwl uses. +X turn: a limb's far end swings forward; +Y: turns to its left; +Z rolls
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def wings(lift, bend, hand, tip, sweep=0.0):
    """Both wings at once: lift raises the whole wing, bend and hand the outer parts (negative droops them), sweep brings it forward."""
    out = {}
    for tag, up in (("L", -1), ("R", 1)):
        out["Wing%s1" % tag] = game_turn(0, up * sweep, up * lift)
        out["Wing%s2" % tag] = game_turn(0, 0, up * bend)
        out["Wing%s3" % tag] = game_turn(0, 0, up * hand)
        out["WingP%s" % tag] = game_turn(0, 0, up * tip)
    return out


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    feet = {"LegL": game_turn(-0.5, 0, 0), "LegR": game_turn(-0.5, 0, 0), "FootL": game_turn(-0.6, 0, 0), "FootR": game_turn(-0.6, 0, 0)}
    hover_low = wings(-0.2, -0.12, -0.1, -0.06)      # the bottom of the slow hovering stroke
    up = {**wings(0.62, -0.26, 0.2, 0.28), "Body": game_turn(-0.22, 0, 0), **feet}
    down = {**wings(-0.42, -0.1, -0.34, -0.36), "Body": game_turn(-0.22, 0, 0), **feet}
    spread = {**wings(0.34, 0.14, 0.1, 0.2, -0.12), "Body": game_turn(0.12, 0, 0), **lids(-12, 0), "BrowL": game_turn(0.2, 0, 0), "BrowR": game_turn(0.2, 0, 0), "TailL": game_turn(0, -0.14, 0), "TailR": game_turn(0, 0.14, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "WinkL": {"LidUL": (tuple(frames["L"].hinge), -BLINK_U, (0, 0, 0)), "LidLL": (tuple(frames["L"].hinge), BLINK_L, (0, 0, 0))}, "Wide": lids(-14, 0), "Hover": hover_low, "Up": up, "Down": down, "Spread": spread,
            "BehindL": {"Head": game_turn(0, 2.7, 0), **hover_low}, "BehindR": {"Head": game_turn(0, -2.7, 0), **hover_low}, "Tilt": {"Head": game_turn(0, 0.35, 0.45), **hover_low}, "Beak": {"BeakLow": game_turn(-0.32, 0, 0)}}


CHECK_VIEW = (0.72, -0.62, 0.18, 8.2, VIEW_AT)

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.07, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(pieces, frames, data)
    print("SKIN GAP", round(surface_gap(lows["Skin"], tree_of(data["BodyBase"])), 4), "HEAD GAP", round(surface_gap(lows["Head"], tree_of(data["HeadBase"])), 4), flush=True)
    # the new stars are laid on the game mesh's own feathers, flat where the high ones curve
    for side, tag in ((1, "L"), (-1, "R")):
        material = glows["Stars" + tag].data.materials[0]
        bpy.data.objects.remove(glows["Stars" + tag], do_unlink=True)
        glows["Stars" + tag], data["Stars" + tag] = build_stars(side, tag, data["Wing" + tag], low=True)
        glows["Stars" + tag].data.materials.append(material)
        glows["Stars" + tag].visible_shadow = False
    unwrap(lows, [(None, 0.8)], {}, shape="CONCAVE", angle=52, texels=TEXELS, margin=0.006)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.05, 0.04, 0.16, 1), far=("Skin", "Head", "Legs"), reach=(0.012, 0.032), far_reach=(0.018, 0.05),
             reaches={**{k: (0.036, 0.09) for k in ("WingL", "WingR", "Tail", "TuftL", "TuftR", "BrowL", "BrowR")}, "Ruff": (0.009, 0.02)})
    # NOTE: a wing is one high piece, so these rays also reach the pale underside of the feather lying over each one: pale patches on the upper faces near the roots, shown in the game as white flecks. The colour map
    # in assets/ had them painted out by hand from the imported map (and a new build reorders the UVs), so rebuilding means re-importing and painting them out again, or baking each feather from itself.      # a feather is cupped above its flat low face: rays must start clear of it, or they start inside it (black slits along every shaft)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton(frames, data)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    for tag, fr in frames.items():
        print("EYE", tag, tuple(round(v, 4) for v in fr.centre), "hinge", tuple(round(v, 4) for v in fr.hinge), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=9.0, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.22, -0.95, 0.06, 2.4, (0, -0.2, 1.36))
    for name, view in (("Blink", close), ("WinkL", close), ("Wide", close), ("Hover", CHECK_VIEW), ("Up", CHECK_VIEW), ("Down", CHECK_VIEW), ("Spread", (0, -1, 0.15, 8.2, VIEW_AT)), ("BehindL", (0.5, 0.86, 0.3, 4.5, (0, 0, 1.2))), ("BehindR", (-0.5, -0.86, 0.3, 4.5, (0, 0, 1.2))), ("Tilt", close), ("Beak", (0.8, -0.6, 0.0, 2.2, (0, -0.25, 1.3)))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 8.2, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

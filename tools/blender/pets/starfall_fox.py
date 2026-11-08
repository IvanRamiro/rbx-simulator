"""The Starfall Fox (Common, Stars; Celestial Egg): "It chases falling stars and sometimes catches one. It keeps them buried somewhere nobody has found."

A new creature, and a face built like no other pet's. A young silver fox: black fur tipped with silver, which is already a night sky, a white bib and cheeks, a white brush to its tail, and gold star-dust on its forepaws and muzzle, which gives
away the digging. Its head is one long canine wedge, lofted from skull to nose. It has no eyeballs: each eye is a flat almond of amber set into the face in an ink rim, with a vertical slit pupil that slides across it and narrow lids that cut it to a sly stare.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/starfall_fox.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, paws on z = 0. The maps go to assets/pets/CelestialEgg/.

What touches what: the neck's top is buried in the head, its join hidden by the cheek ruff; ears, cheek locks, nose and jaw are sunk into the head; each almond sits in a dimple in the skin under its rim, its lids sliding under the skin out of sight;
bib locks are sunk into the chest, legs into the body, paws onto the legs, the tail's root into the rump.
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
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "StarfallFox"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- colours ----------
INK, NAVY, SLATE, SILVER, PEARL = rgb(13, 15, 32), rgb(26, 30, 60), rgb(60, 68, 106), rgb(172, 180, 206), rgb(240, 241, 248)
GOLD, AMBER, HOT, PAD = rgb(248, 192, 92), rgb(214, 120, 28), rgb(255, 226, 132), rgb(10, 9, 18)
MOUTH = rgb(92, 34, 50)

# ---------- the frame of it ----------
P0, NOSE = V(0, -0.40, 0.96), V(0, -0.86, 0.845)
HD = (NOSE - P0).normalized()
HUP = (V(0, 0, 1) - HD * HD.z).normalized()
S_KN = (0.0, 0.12, 0.3, 0.46, 0.6, 0.8, 1.0)
W_KN = (0.10, 0.19, 0.225, 0.15, 0.088, 0.068, 0.038)
T_KN = (0.07, 0.145, 0.165, 0.125, 0.074, 0.058, 0.038)
B_KN = (0.07, 0.13, 0.135, 0.09, 0.056, 0.046, 0.03)
TRUNK = catmull([V(0, 0.54, 0.585), V(0, 0.3, 0.605), V(0, 0.05, 0.585), V(0, -0.17, 0.595), V(0, -0.3, 0.68), V(0, -0.37, 0.82), V(0, -0.41, 0.92)], 8)
TRUNK_R = ((0, 0.06), (0.1, 0.13), (0.28, 0.135), (0.48, 0.113), (0.68, 0.15), (0.84, 0.128), (1, 0.1))
TAIL = catmull([V(0, 0.52, 0.6), V(0, 0.72, 0.53), V(0, 0.98, 0.56), V(0.04, 1.2, 0.73), V(-0.02, 1.3, 0.98), V(0.01, 1.3, 1.24)], 8)
FRONT = [V(0.095, -0.2, 0.52), V(0.1, -0.25, 0.3), V(0.09, -0.215, 0.135), V(0.09, -0.255, 0.04)]
HIND = [V(0.115, 0.4, 0.52), V(0.128, 0.29, 0.32), V(0.102, 0.45, 0.15), V(0.1, 0.41, 0.04)]
FRONT_R, HIND_R = (0.065, 0.046, 0.032, 0.03), (0.085, 0.062, 0.034, 0.03)
LEGS = (("FL", 1, FRONT, FRONT_R), ("FR", -1, FRONT, FRONT_R), ("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R))


def soft_profile(knots):
    """A head's profile with no kinks at its knots: the wedge's planes must flow into each other."""
    xs = np.linspace(0, 1, 401)
    ys = np.interp(xs, S_KN, knots)
    k = np.exp(-(np.arange(-40, 41) / 16.0) ** 2)
    k /= k.sum()
    pad = np.concatenate((np.full(40, ys[0]) + (ys[0] - ys[40:0:-1]), ys, np.full(40, ys[-1]) + (ys[-1] - ys[-2:-42:-1])))
    return xs, np.convolve(pad, k, mode="valid")


PROF_W, PROF_T, PROF_B = (soft_profile(k) for k in (W_KN, T_KN, B_KN))


def head_axis(s):
    return P0.lerp(NOSE, s)


def head_coords(P):
    d = P - np.array(tuple(P0))
    return d @ np.array(tuple(HD)) / (NOSE - P0).length, d @ np.array(tuple(HUP))


def tail_radius(f):
    return float(np.interp(f, (0, 0.08, 0.3, 0.55, 0.78, 0.93, 1), (0.07, 0.085, 0.15, 0.19, 0.155, 0.075, 0.012)))


def leg_path(side, knots, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def rings_mesh(name, coll, top, rings, bottom):
    m = Mesh()
    bm = m.bm
    a = bm.verts.new(top)
    grid = [[bm.verts.new(tuple(p)) for p in ring] for ring in rings]
    b = bm.verts.new(bottom)
    nt = len(rings[0])
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((a, grid[0][j], grid[0][j2]))
        for i in range(len(grid) - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]))
        bm.faces.new((grid[-1][j], b, grid[-1][j2]))
    return m.finish(name, coll)


def clump(m, root, d, length, width, bend=V(0, 0, 0), flat=1.0, plane=V(1, 0, 0), sides=12):
    """One soft point of fur: thick from its root, tapering to a blunt tip. Fused into what it grows from, so it is sculpted fur and not a leaf stuck on."""
    d = d.normalized()
    tip = root + d * length + bend
    mid = root + d * length * 0.5 + bend * 0.25
    m.tube(catmull([root - d * width * 0.5, mid, tip], 5), lambda f: width * (0.02 + (1 - f) ** 0.8 * min(1.0, 0.72 + f * 1.4)), sides=sides, flat=flat, plane=plane)


# ---------- the eye: a flat almond inlaid in the face, not a ball ----------
class FoxEye:
    R, A, B_UP, B_LOW, SOCKET = 0.15, 0.058, 0.03, 0.024, 0.009
    POW = 0.85

    def __init__(self, side, tree):
        self.side = side
        at = head_axis(0.405) + HUP * 0.06 + V(side * 0.098, 0, 0)
        out = V(side * 0.52, -0.82, 0.2).normalized()
        hit, nrm, _, _ = tree.ray_cast(at + out * 0.3, -out, 0.6)
        self.n = (nrm + out).normalized()
        self.c = hit - self.n * self.SOCKET
        u = V(side * 0.84, 0.16, 0.46)                   # along the eye, nose to temple: its outer corner high: the fox's slant
        self.u = (u - self.n * u.dot(self.n)).normalized()
        v = self.n.cross(self.u)
        self.v = v if v.z > 0 else -v
        self.p = self.c - self.n * self.R
        h = self.u
        if h.cross(self.n).dot(self.v) > 0:
            h = -h
        self.hinge = h                                   # a positive turn about this carries what's in front of the pivot downward

    def point(self, u, v, lift=0.0):
        d = (self.n + self.u * (u / self.R) + self.v * (v / self.R)).normalized()
        return self.p + d * (self.R + lift)

    def upper(self, t):
        """The almond's height over its long axis at t in -1..1 (nose to temple): pointed at both corners."""
        return self.B_UP * max(0.0, 1 - t * t) ** self.POW * (1 + 0.16 * t)

    def lower(self, t):
        return self.B_LOW * max(0.0, 1 - t * t) ** self.POW * (1 - 0.1 * t)

    def outline(self, th, r=1.0):
        t = math.cos(th)
        return (self.A * r * t, r * (self.upper(t) if math.sin(th) >= 0 else -self.lower(t)))

    def coords(self, P):
        """Per point: along the eye and up it (in almond units) and its radius in the almond: 1 on the outline."""
        d = P - np.array(tuple(self.p))
        n, u, v = np.array(tuple(self.n)), np.array(tuple(self.u)), np.array(tuple(self.v))
        dn = np.maximum((d * n).sum(1), 1e-4)
        uu = (d * u).sum(1) / dn * self.R / self.A
        vv = (d * v).sum(1) / dn * self.R
        vv = vv / np.where(vv >= 0, self.B_UP, self.B_LOW)
        r = np.sqrt(uu ** 2 + np.abs(vv) ** (1 / self.POW))
        front = (d * n).sum(1) > 0
        return uu, vv, np.where(front, r, 99.0)


def head_rings(nt, rows):
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    X, U_ = np.array((1.0, 0, 0)), np.array(tuple(HUP))
    cs, sn = np.cos(a), np.sin(a)
    out = []
    for i in range(rows):
        s = i / (rows - 1)
        w, t, b = (float(np.interp(s, *q)) for q in (PROF_W, PROF_T, PROF_B))
        c = np.array(tuple(head_axis(s)))
        x = w * np.sign(cs) * np.abs(cs) ** 0.9
        y = np.where(sn > 0, t, b) * np.sign(sn) * np.abs(sn) ** 0.9
        out.append(c + x[:, None] * X + y[:, None] * U_)
    return out


def cheek_clumps(m):
    """The ruff flaring from behind the jaw: broad and short, so the face is a wide triangle from the front. Nothing points forward: long pale points round a face read as fangs."""
    for side in (1, -1):
        for a, length, w, dy in ((-52, 0.15, 0.05, 0.0), (-30, 0.185, 0.056, 0.012), (-10, 0.2, 0.058, 0.02), (10, 0.17, 0.052, 0.03), (28, 0.13, 0.046, 0.044)):
            r = math.radians(a)
            root = V(side * (0.15 + 0.03 * math.cos(r)), -0.525 + dy, 0.905 + 0.078 * math.sin(r))
            d = V(side * math.cos(r), 0.62, math.sin(r) * 0.9)
            clump(m, root, d, length, w, bend=V(0, 0.01, -0.012), flat=1.0, plane=V(0, 1, 0.0))


def build_head_base(name, coll):
    rings = head_rings(96, 100)
    m = Mesh()
    bm = m.bm
    o = rings_mesh(name + "Loft", coll, tuple(P0 - HD * 0.02), rings, tuple(NOSE + HD * 0.014))
    bm.from_mesh(o.data)
    cheek_clumps(m)
    bpy.data.objects.remove(o, do_unlink=True)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0065, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    return o


def sculpt_face(o, eyes):
    """The socket each almond lies in, the brow over it, and the grin running back from the mouth."""
    P = verts(o)
    Nn = normals(o)
    s, up = head_coords(P)
    bottom = np.interp(s, *PROF_B)
    corner = smooth(0.62, 0.42, s)
    line = -0.42 * bottom + 0.02 * corner
    groove = np.exp(-((up - line) / 0.0062) ** 2) * smooth(0.40, 0.48, s) * (1 - smooth(0.97, 1.0, s)) * (np.abs(P[:, 0]) > 0.004) * smooth(0.0, -0.5, Nn @ np.array(tuple(HD)) * 0 - 1)
    brow = np.zeros(len(P))
    Q = P.copy()
    for e in eyes:
        uu, vv, r = e.coords(P)
        mine = ((P[:, 0] * e.side) > 0)
        d = P - np.array(tuple(e.p))
        L = np.linalg.norm(d, axis=1)
        floor = e.R - 0.0035                              # just under the lens
        w = (1 - smooth(1.02, 1.8, r)) * mine
        pull = np.where(L > floor, (floor - L) * w, 0.0)
        Q = Q + (d / L[:, None]) * pull[:, None]
        brow = np.maximum(brow, np.exp(-((vv - 2.5) / 0.85) ** 2) * np.exp(-((uu - 0.15) / 1.2) ** 2) * mine)
    Q = Q + Nn * (0.012 * brow - 0.006 * groove)[:, None]
    set_verts(o, Q)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0042, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the body ----------
def trunk_radius(f):
    a = np.array(TRUNK_R)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def body_clumps(m):
    # the ruff: its volume is one soft swell, broken only at the hem, where it falls in points over the chest
    for k, (x, length, w) in enumerate(((0.008, 0.16, 0.074), (-0.074, 0.105, 0.058), (0.086, 0.09, 0.056), (-0.135, 0.09, 0.056), (0.145, 0.105, 0.058))):      # (uneven on purpose: a matched pair of points on a chest reads as something else)
        back = abs(x) * 0.7
        z = 0.645 + abs(x) * 0.42
        clump(m, V(x, -0.44 + back, z), V(x * 1.6, -0.2 + back * 2.2, -1), length, w, bend=V(0, 0.02, 0), plane=V(1, 0, 0), flat=1.05)
    # its sides, sweeping back round the shoulder
    for side in (1, -1):
        for y, z, length, w in ((-0.3, 0.8, 0.14, 0.06), (-0.26, 0.69, 0.13, 0.058)):
            clump(m, V(side * 0.12, y, z), V(side * 0.34, 0.86, -0.42), length, w, plane=V(0, 1, 0))
    # the breeches on the back of each thigh, a little fringe under the belly
    for side in (1, -1):
        for y, z, length, w in ((0.5, 0.48, 0.12, 0.05), (0.49, 0.4, 0.11, 0.044)):
            clump(m, V(side * 0.11, y, z), V(side * 0.14, 0.6, -1), length, w, plane=V(0, 1, 0))
    # fur from the rump lying over the tail's root
    for x, z, length, w in ((0.0, 0.66, 0.15, 0.05), (0.052, 0.62, 0.14, 0.046), (-0.052, 0.62, 0.14, 0.046), (0.03, 0.555, 0.12, 0.044), (-0.03, 0.555, 0.12, 0.044)):
        clump(m, V(x, 0.5, z), V(x * 0.7, 1, -0.14), length, w, plane=V(1, 0, 0))
    for y, length, w in ((-0.08, 0.08, 0.04), (0.06, 0.07, 0.036)):
        for x in (-0.042, 0.042):
            clump(m, V(x, y, 0.5), V(x * 2, 0.8, -0.8), length, w, plane=V(1, 0, 0))


def build_body():
    core = Mesh()
    core.tube(TRUNK, trunk_radius, sides=28, flat=0.96)
    core.ball(V(0, -0.375, 0.75), (0.175, 0.15, 0.2))                  # the ruff's swell
    for side in (1, -1):
        core.ball(V(side * 0.082, -0.2, 0.565), (0.066, 0.1, 0.13))    # the shoulder
        core.ball(V(side * 0.102, 0.38, 0.52), (0.08, 0.15, 0.15))      # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.012, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 26})])
    fur = Mesh()
    bm = fur.bm
    bm.from_mesh(c.data)
    body_clumps(fur)
    base = fur.finish(N + "BodyBase", HI, recalc=False)
    apply_mods(base, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0065, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    base.hide_render = True
    thin = Mesh()
    thin.bm.from_mesh(c.data)
    body_clumps(thin)
    for key, side, knots, radii in LEGS:
        thin.tube(leg_path(side, knots), lambda f, r=radii: leg_radius(r, f), sides=18, flat=0.9, plane=V(1, 0, 0))
        thin.ball(mir(knots[2], side), (0.033, 0.036, 0.036), 16, 10)
    skin = thin.finish(N + "SkinHi", HI, recalc=False)
    bpy.data.objects.remove(c, do_unlink=True)
    apply_mods(skin, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0045, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    return skin, base


# ---------- the tail: a brush of soft points, every one lying toward the tip ----------
def build_tail_base(name, coll):
    m = Mesh()
    m.tube(TAIL, lambda f: tail_radius(f) * 0.9, sides=28)
    path = TAIL
    n = len(path)
    golden = 2.39996
    count = 64
    for k in range(count):
        f = 0.14 + 0.78 * k / (count - 1)
        i = min(n - 2, int(f * (n - 1)))
        p = path[i]
        tan = (path[i + 1] - p).normalized()
        side = (V(1, 0, 0) - tan * tan.x).normalized()
        up = tan.cross(side).normalized()
        a = k * golden
        rad = side * math.cos(a) + up * math.sin(a)
        r = tail_radius(f)
        d = tan + rad * 0.16
        fine = float(np.interp(f, (0.5, 0.85), (1.0, 0.8)))
        clump(m, p + rad * r * float(np.interp(f, (0.14, 0.4, 0.68, 0.9), (0.62, 0.8, 0.8, 0.66))), d, (0.12 + 0.07 * hash_of(k)) * fine, (0.046 + 0.016 * hash_of(k + 40)) * fine, plane=rad.cross(tan), flat=1.2, sides=10)
    tip = path[-1]
    tan = (path[-1] - path[-4]).normalized()
    clump(m, tip - tan * 0.12, tan, 0.2, 0.052, sides=14)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0065, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 7})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def hash_of(k):
    return math.sin(k * 12.9898) * 43758.5453 % 1.0


# ---------- ears, nose, jaw, paws ----------
def ear_point(side):
    root = V(side * 0.128, -0.545, 0.995)
    up = V(side * 0.3, 0.1, 0.95).normalized()
    face = V(side * 0.46, -0.88, 0.04)
    face = (face - up * face.dot(up)).normalized()
    across = up.cross(face).normalized()

    def point(u, v):
        w = 2 * v - 1
        half = 0.098 * (1 - u) ** 0.66 * (1 + 0.18 * math.sin(math.pi * min(1.0, u * 2.2))) + 0.002
        return root + up * 0.3 * u + across * half * w - face * (0.03 * (1 - w * w) * math.sin(math.pi * min(1.0, 0.3 + u * 0.7)) - 0.012)
    return point


def ear_thick(u, v):
    return 0.016 * (1 - u) + 0.004


def paint_ear(o, side):
    """Ink backs, a pale silver cup. The sheet's verts come in pairs: its cupped front, then its back."""
    P = verts(o)
    root = np.array(tuple(V(side * 0.128, -0.545, 0.995)))
    up = np.array(tuple(V(side * 0.3, 0.1, 0.95).normalized()))
    u = (P - root) @ up / 0.3
    Nn = normals(o)
    face = np.array(tuple(V(side * 0.46, -0.88, 0.04).normalized()))
    front = smooth(-0.05, 0.25, Nn @ face)
    across = np.array(tuple(up_cross(side)))
    w = np.abs((P - root) @ across) / np.maximum(0.098 * np.maximum(1 - u, 0.001) ** 0.66 + 0.002, 0.004)
    inner = (1 - smooth(0.46, 0.78, w)) * smooth(0.0, 0.2, u) * (1 - smooth(0.68, 0.86, u))
    hair = 0.72 + 0.28 * fbm(P * np.array((5.0, 5.0, 1.0)), 40.0, 2, 3)
    cup = mix(SLATE, mix(SILVER, PEARL, 0.35), smooth(0.04, 0.42, u))
    col = mix(INK, cup * hair[:, None], inner * front)
    paint(o, col, 0.82)


def up_cross(side):
    up = V(side * 0.3, 0.1, 0.95).normalized()
    face = V(side * 0.46, -0.88, 0.04)
    face = (face - up * face.dot(up)).normalized()
    return up.cross(face).normalized()


def build_jaw(name, coll, sides, per):
    a = head_axis(0.5) - HUP * 0.05
    b = head_axis(0.8) - HUP * 0.046
    c = head_axis(0.955) - HUP * 0.034
    m = Mesh()
    m.tube(catmull([a, a.lerp(b, 0.5), b, c], per), lambda f: (0.03 - 0.012 * f) * max(0.2, 1 - f ** 6), sides=sides, flat=2.0, plane=V(1, 0, 0))
    return m.finish(name, coll)


def build_nose(name, coll, seg, rings):
    m = Mesh()
    c = NOSE + HD * 0.004 + HUP * 0.008
    m.ball(c, (0.03, 0.024, 0.021), seg, rings)
    for side in (1, -1):
        m.ball(c + V(side * 0.013, -0.004, -0.003), (0.015, 0.018, 0.013), seg // 2, rings // 2)
    return m.finish(name, coll)


def build_paws(name, coll, low=False):
    m = Mesh()
    seg, rg = (8, 5) if low else (28, 16)
    for key, side, knots, _ in LEGS:
        c = mir(knots[3], side)
        m.ball(c + V(0, -0.016, -0.004), (0.04, 0.054, 0.036), seg, rg)
        if not low:
            for x in (-0.027, -0.009, 0.009, 0.027):
                m.ball(c + V(x, -0.058 + abs(x) * 0.45, -0.024), (0.014, 0.019, 0.016), 14, 10)
    return m.finish(name, coll)


# ---------- the eye's pieces ----------
def face_out(fs, e):
    for f in fs:
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - e.p) < 0:
            f.normal_flip()


def build_lens(e, name, coll, nth, radii):
    m = Mesh()
    bm = m.bm
    hub = bm.verts.new(e.point(0, 0))
    grid = [[bm.verts.new(e.point(*e.outline(TAU * j / nth, r))) for j in range(nth)] for r in radii]
    fs = []
    for j in range(nth):
        j2 = (j + 1) % nth
        fs.append(bm.faces.new((hub, grid[0][j], grid[0][j2])))
        for i in range(len(grid) - 1):
            fs.append(bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2])))
    face_out(fs, e)
    return m.finish(name, coll, recalc=False)


PUPIL_W, PUPIL_U, PUPIL_L = 0.0118, 0.022, 0.0175


def build_pupil(e, name, coll, nth):
    """A fox's pupil: a tall slit with soft ends, a little off the lens."""
    m = Mesh()
    bm = m.bm
    hub = bm.verts.new(e.point(0, 0, 0.0016))
    ring = []
    for j in range(nth):
        a = TAU * j / nth
        sn = math.sin(a)
        ring.append(bm.verts.new(e.point(PUPIL_W * math.cos(a) * (1 - 0.25 * sn * sn), (PUPIL_U if sn > 0 else PUPIL_L) * sn, 0.0016)))
    fs = [bm.faces.new((hub, ring[j], ring[(j + 1) % nth])) for j in range(nth)]
    face_out(fs, e)
    return m.finish(name, coll, recalc=False)


LID_REST_U, LID_REST_L = 0.56, 0.86


def lid_rows(e, upper, nu, nv):
    """A lid: a band fixed all along the rim, its free edge across the lens. It closes by stretching, so it never leaves the rim or shows behind the skin."""
    rows, shares = [], []
    for i in range(nu + 1):
        t = -1.08 + 2.16 * i / nu
        tc = max(-1.0, min(1.0, t))
        out = max(e.upper(tc), 0.0022) if upper else -max(e.lower(tc), 0.0022)      # (never quite nothing: the band keeps a width past the corner, under the rim)
        row, share = [], []
        for j in range(nv + 1):
            g = j / nv                     # 0 on the rim, 1 on the free edge
            k = 1.08 - (1.08 - (LID_REST_U if upper else LID_REST_L)) * g
            row.append(e.point(t * e.A, out * k, 0.0042 if upper else 0.0034))
            share.append(g * max(0.0, 1 - tc * tc) ** e.POW)
        rows.append(row)
        shares.append(share)
    return rows, shares


def build_lid(e, upper, name, coll, nu, nv):
    rows, shares = lid_rows(e, upper, nu, nv)
    m = Mesh()
    bm = m.bm
    grid = [[bm.verts.new(p) for p in row] for row in rows]
    fs = [bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])) for i in range(nu) for j in range(nv)]
    face_out(fs, e)
    o = m.finish(name, coll, recalc=False)
    return o, [s for row in shares for s in row]


def build_rim(e, name, coll, nth, sides, thick=0.0034):
    """A thin ink line round the almond, covering where the skin meets the lens: a closed ring."""
    pts = [e.point(*e.outline(TAU * j / nth), 0.003) for j in range(nth)]
    m = Mesh()
    bm = m.bm
    rings = []
    for j, q in enumerate(pts):
        tan = (pts[(j + 1) % nth] - pts[j - 1]).normalized()
        a = (e.n - tan * tan.dot(e.n)).normalized()
        b = tan.cross(a).normalized()
        rings.append([bm.verts.new(q + a * math.cos(TAU * k / sides) * thick + b * math.sin(TAU * k / sides) * thick) for k in range(sides)])
    for j in range(nth):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((rings[j][k], rings[j][k2], rings[(j + 1) % nth][k2], rings[(j + 1) % nth][k]))
    return m.finish(name, coll)


# ---------- paint ----------
def worley(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2 + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                d1 = np.minimum(d1, d)
    return d1


def night_coat(P, frost_share):
    """Black fur tipped with silver, in drifts, thickest over the shoulders and the back, with the odd hair-tip catching like a real star."""
    drift = fbm(P, 3.2, 3, 7)
    A = np.array(((0.62, 0.0, 0.78), (0.31, 0.92, -0.25), (-0.72, 0.39, 0.57)))      # (a second, turned sampling hides the noise's cube cells)
    fine = 0.5 * (fbm(P * np.array((1.0, 0.2, 1.0)), 92.0, 3, 19) + fbm(P * np.array((0.85, 0.16, 0.7)) @ A, 92.0, 3, 23))
    frost = smooth(0.34, 0.72, drift * 0.22 + fine * 0.78 + 0.05 * frost_share)
    col = mix(INK, NAVY, smooth(0.3, 0.62, drift))
    col = mix(col, mix(SLATE, SILVER, 0.14), frost * (0.26 + 0.34 * frost_share))
    small = (1 - smooth(0.06, 0.12, worley(P, 30.0, 41))) * smooth(0.42, 0.56, fbm(P, 8.0, 2, 53))
    big = (1 - smooth(0.05, 0.085, worley(P, 12.0, 61))) * smooth(0.45, 0.55, fbm(P, 5.0, 2, 71))
    stars = np.maximum(small, big)
    return mix(col, PEARL, stars), stars, fine


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    up = Nn[:, 2]
    col, stars, fine = night_coat(P, smooth(0.42, 0.74, z) * smooth(-0.3, 0.4, up))
    # the white bib: throat and chest, a narrow line along the belly
    d = np.linalg.norm((P - np.array((0, -0.47, 0.72))) / np.array((0.19, 0.26, 0.27)), axis=1)
    bib = 1 - smooth(0.86, 1.04, d + 0.16 * (fine - 0.5))
    belly = (1 - smooth(0.03, 0.06, np.abs(x))) * smooth(-0.45, -0.8, up) * (y < 0.28) * (z > 0.34)
    bib = np.maximum(bib, belly)
    col = mix(col, mix(PEARL, SILVER, fine * 0.4), bib)
    # ink stockings, gold dust on the forepaws from the digging
    leg = (1 - smooth(0.34, 0.48, z + 0.04 * (fine - 0.5))) * (1 - belly)
    col = mix(col, mix(INK, NAVY, fine * 0.5), leg)
    dust = (1 - smooth(0.14, 0.3, worley(P, 90.0, 3))) * (1 - smooth(0.06, 0.2, z)) * (y < 0.05)
    col = mix(col, GOLD, dust * leg * 0.9)
    set_verts(o, P + Nn * (0.0028 * (fine - 0.5))[:, None])
    paint(o, col, 0.84 - 0.2 * stars)


def paint_head(o, eyes):
    P = verts(o)
    Nn = normals(o)
    x = P[:, 0]
    s, up = head_coords(P)
    col, stars, fine = night_coat(P, 0.35)
    # white from the chin up the cheek and out along the ruff; its line runs from the nose's side, back under the eye, and sweeps up the cheek
    line = np.interp(s, (0.0, 0.2, 0.34, 0.5, 0.75, 1.0), (0.02, 0.012, -0.004, -0.024, -0.016, -0.012))
    white = 1 - smooth(-0.009, 0.009, up - line - 0.012 * (fine - 0.5))
    col = mix(col, mix(PEARL, SILVER, fine * 0.32), white)
    for e in eyes:
        uu, vv, r = e.coords(P)
        mine = (x * e.side) > 0
        # the ink tear line, from the inner corner down toward the mouth: every fox's mark
        tear = (1 - smooth(0.16, 0.38, np.abs(vv - (uu + 1.0) * 2.1))) * smooth(-0.85, -1.05, uu) * (1 - smooth(-2.7, -2.2, uu)) * mine
        col = mix(col, INK, tear)
        # ink round the almond, and a wing out past its outer corner
        col = mix(col, INK, (1 - smooth(1.04, 1.4, r)) * mine)
        wing = (1 - smooth(0.16, 0.36, np.abs(vv - (uu - 1.0) * 0.28))) * smooth(0.95, 1.1, uu) * (1 - smooth(1.45, 1.8, uu)) * mine
        col = mix(col, INK, wing)
    # the lip
    bottom = np.interp(s, *PROF_B)
    lip = np.exp(-((up - (-0.42 * bottom + 0.02 * smooth(0.62, 0.42, s))) / 0.0075) ** 2) * smooth(0.40, 0.48, s)
    col = mix(col, INK, lip)
    # gold dust on the bridge of the nose: it's been digging
    dust = (1 - smooth(0.13, 0.3, worley(P, 110.0, 5))) * smooth(0.68, 0.9, s) * smooth(0.0, 0.5, Nn @ np.array(tuple(HUP))) * smooth(0.42, 0.58, fbm(P, 20.0, 2, 13))
    col = mix(col, GOLD, dust)
    # the roof of the mouth, for when the jaw opens
    roof = smooth(-0.3, -0.75, Nn @ np.array(tuple(HUP))) * smooth(0.5, 0.56, s) * (1 - smooth(0.92, 0.97, s)) * (up < -0.42 * bottom) * (1 - smooth(0.028, 0.04, np.abs(x)))      # (narrow: the closed jaw must cover all of it)
    col = mix(col, MOUTH, roof)
    set_verts(o, P + Nn * (0.0016 * (fine - 0.5))[:, None])
    paint(o, col, 0.84 - 0.2 * stars)


def paint_lens(o, e):
    """Amber: pale at the heart, burning darker to the rim, shaded under the lid, with fine fibres raying out from the slit."""
    P = verts(o)
    uu, vv, r = e.coords(P)
    rad = np.sqrt(uu ** 2 + (vv * 0.8) ** 2)
    a = np.arctan2(vv, uu * 1.6)
    col = mix(HOT, AMBER, smooth(0.14, 0.82, rad))
    col = col * (1 - 0.16 * (np.sin(a * 30) * 0.5 + 0.5) * smooth(0.15, 0.4, rad))[:, None]
    col = col * (1 - 0.72 * smooth(-0.08, 0.5, vv))[:, None]
    paint(o, mix(col, rgb(40, 14, 8), smooth(0.8, 1.0, r)), np.full(len(P), 0.1))


def paint_lid(o, e, upper):
    """A lid is fur, the same dark as the face, so a closed eye reads as closed and not as a hole; only its free edge is ink."""
    P = verts(o)
    _, vv, _ = e.coords(P)
    edge = np.abs(vv - (LID_REST_U if upper else -LID_REST_L))
    col = mix(mix(NAVY, SLATE, 0.5), INK, 1 - smooth(0.03, 0.22, edge))
    col = col * (0.86 + 0.14 * fbm(P, 120.0, 2, 37))[:, None]
    paint(o, col, 0.8)


def paint_tail(o):
    P = verts(o)
    Nn = normals(o)
    f, _ = nearest_on(TAIL, P)
    col, stars, fine = night_coat(P, 0.7)
    strand = fbm(P * np.array((3.0, 0.6, 1.2)), 26.0, 3, 31)
    tip = smooth(0.66, 0.76, f + 0.07 * (strand - 0.5))
    col = mix(col, mix(PEARL, SILVER, strand * 0.36), tip)
    set_verts(o, P + Nn * (0.004 * (strand - 0.5))[:, None])
    paint(o, col, 0.84 - 0.2 * stars)


def paint_paws(o):
    P = verts(o)
    dust = (1 - smooth(0.16, 0.36, worley(P, 90.0, 9))) * (P[:, 1] < 0.05)
    paint(o, mix(mix(INK, NAVY, 0.3), GOLD, dust * 0.9), 0.74)


def build_glints(eyes, coll, sides, low=False):
    m = Mesh()
    bm = m.bm
    for e in eyes.values():
        u0, v0 = -0.012, 0.002
        lift = 0.003
        hub = bm.verts.new(e.point(u0, v0, lift))
        ring = [bm.verts.new(e.point(u0 + 0.0052 * math.cos(TAU * k / sides), v0 + 0.0062 * math.sin(TAU * k / sides), lift)) for k in range(sides)]
        face_out([bm.faces.new((hub, ring[k], ring[(k + 1) % sides])) for k in range(sides)], e)
    return m.finish(N + "Glints_Glow_f6ecd6", coll, smooth_shade=False, recalc=False)


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"], data["BodyBase"] = build_body()
    pieces["Legs"] = pieces["Skin"]
    head = build_head_base(N + "HeadHi", HI)
    tree0 = tree_of(head)
    eyes = {"L": FoxEye(1, tree0), "R": FoxEye(-1, tree0)}
    head = sculpt_face(head, list(eyes.values()))
    data["HeadBase"] = bpy.data.objects.new(N + "HeadBase", head.data.copy())
    HI.objects.link(data["HeadBase"])
    data["HeadBase"].hide_render = True
    pieces["Head"] = head
    data["eyes"] = eyes
    pieces["Tail"] = build_tail_base(N + "TailHi", HI)
    data["TailBase"] = bpy.data.objects.new(N + "TailBase", pieces["Tail"].data.copy())
    HI.objects.link(data["TailBase"])
    data["TailBase"].hide_render = True
    pieces["Jaw"] = build_jaw(N + "JawHi", HI, 26, 12)
    pieces["Nose"] = build_nose(N + "NoseHi", HI, 28, 16)
    pieces["Paws"] = build_paws(N + "PawsHi", HI)
    for side, tag in ((1, "L"), (-1, "R")):
        e = eyes[tag]
        pieces["Lens" + tag] = build_lens(e, N + "Lens" + tag + "Hi", HI, 120, [k / 26 * 1.08 for k in range(1, 27)])
        pieces["Pupil" + tag] = build_pupil(e, N + "Pupil" + tag + "Hi", HI, 40)
        pieces["LidU" + tag], _ = build_lid(e, True, N + "LidU" + tag + "Hi", HI, 40, 10)
        pieces["LidL" + tag], _ = build_lid(e, False, N + "LidL" + tag + "Hi", HI, 40, 10)
        pieces["Rim" + tag] = build_rim(e, N + "Rim" + tag + "Hi", HI, 100, 10)
        m = Mesh()
        m.sheet(ear_point(side), ear_thick, 80, 40)
        pieces["Ear" + tag] = m.finish(N + "Ear" + tag + "Hi", HI)
    if not clay:
        paint_skin(pieces["Skin"])
        paint_head(head, list(eyes.values()))
        paint_tail(pieces["Tail"])
        Nn = normals(pieces["Jaw"])
        P = verts(pieces["Jaw"])
        inside = mix(INK, MOUTH, 1 - smooth(0.012, 0.032, np.abs(P[:, 0])))
        paint(pieces["Jaw"], mix(np.tile(mix(PEARL, SILVER, 0.2), (len(P), 1)), inside, smooth(0.34, 0.66, Nn @ np.array(tuple(HUP)))), 0.5)
        plain(pieces["Nose"], PAD, 0.16)
        paint_paws(pieces["Paws"])
        for side, tag in ((1, "L"), (-1, "R")):
            e = eyes[tag]
            paint_lens(pieces["Lens" + tag], e)
            plain(pieces["Pupil" + tag], rgb(4, 3, 8), 0.05)
            paint_lid(pieces["LidU" + tag], e, True)
            paint_lid(pieces["LidL" + tag], e, False)
            plain(pieces["Rim" + tag], rgb(6, 6, 14), 0.5)
            paint_ear(pieces["Ear" + tag], side)
    return pieces, {"Glints": build_glints(eyes, HI, 14)}, data


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (1, 1, 1, 1)
        g.inputs["Emission Strength"].default_value = 1.4
        o.data.materials.append(m)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.25, 0.62)
FACE_AT = (0, -0.68, 0.95)
EXTRA = [(0, -1, 0.05, 1.7, FACE_AT), (0.62, -0.78, 0.1, 1.7, FACE_AT), (1, -0.05, 0.02, 1.7, FACE_AT), (0.32, -0.9, 0.42, 1.7, FACE_AT), (0.34, -0.92, 0.08, 0.62, (0.1, -0.74, 0.99)), (0.8, 0.4, 0.3, 2.6, (0, 1.0, 0.9)), (0.75, -0.55, -0.1, 2.0, (0.1, -0.1, 0.27))]


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
        mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=5.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = (1000, 1100, 900, 1200, 960, 1060, 860, 1150)
HEAD_QUADS = (1300, 1450, 1180, 1600, 1080)
TAIL_QUADS = (900, 1000, 820, 1100, 760)
TEXELS = {"Head": 1.9, "Tail": 0.85, "Legs": 0.9, "Paws": 1.0, "Jaw": 1.4, "Nose": 2.2, "EarL": 1.3, "EarR": 1.3, "LensL": 3.4, "LensR": 3.4, "PupilL": 1.6, "PupilR": 1.6, "LidUL": 1.2, "LidUR": 1.2, "LidLL": 1.2, "LidLR": 1.2, "RimL": 0.8, "RimR": 0.8}
BLINK_U, BLINK_L = 9.8, 5.0      # degrees: the lids' full travel
META = {}


def truest(base, name, targets):
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


def seat_eyes(head, eyes):
    """The game head must lie under each almond: the lens is what shows there. Whatever of it stands over the lens is drawn back, and what lies wholly under it is cut away: nothing there ever shows, and it would only z-fight."""
    P = verts(head)
    for e in eyes:
        uu, vv, r = e.coords(P)
        d = P - np.array(tuple(e.p))
        L = np.linalg.norm(d, axis=1)
        mine = (P[:, 0] * e.side) > 0
        floor = e.R - 0.003
        pull = np.where((L > floor) & (r < 1.16) & mine, floor - L, 0.0)
        P = P + (d / L[:, None]) * pull[:, None]
    set_verts(head, P)
    bm = bmesh.new()
    bm.from_mesh(head.data)
    bm.verts.ensure_lookup_table()
    pts = np.array([tuple(v.co) for v in bm.verts])
    dead = set()
    for e in eyes:
        _, _, r = e.coords(pts)
        inside = (r < 1.0) & ((pts[:, 0] * e.side) > 0)
        for f in bm.faces:
            if all(inside[v.index] for v in f.verts):
                dead.add(f)
    bmesh.ops.delete(bm, geom=list(dead), context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(head.data)
    bm.free()
    print("HEAD cut under the lenses", len(dead), flush=True)


def eye_check(head, eyes):
    """Rays out through each almond: nothing of the head may stand over it."""
    tree = tree_of(head)
    for e in eyes:
        over = 0
        for k in range(600):
            a, b = TAU * hash_of(k), hash_of(k + 700) ** 0.5 * 0.96
            u, v = e.outline(a, b)
            q = e.point(u, v)
            d = (q - e.p).normalized()
            hit = tree.ray_cast(q + d * 0.0005, d, 0.04)[0]
            over += hit is not None
        print("EYECHECK side", e.side, "skin over the lens:", over, "of 600", flush=True)
        assert over == 0, "the head stands over the eye"


def build_low_legs():
    m = Mesh()
    fs = []
    for key, side, knots, radii in LEGS:
        path = leg_path(side, knots, 3)
        n = len(path)
        m.tube(path, lambda f, r=radii: leg_radius(r, f), sides=8, flat=0.9, plane=V(1, 0, 0))
        for i in range(n):
            fs += [(key, i / (n - 1))] * 8
    return m.finish(N + "LegsLow", GAME), fs


def build_low(pieces, data):
    eyes = data["eyes"]
    lows = {"Skin": truest(data["BodyBase"], "Skin", SKIN_QUADS), "Head": truest(data["HeadBase"], "Head", HEAD_QUADS), "Tail": truest(data["TailBase"], "Tail", TAIL_QUADS)}
    lows["Legs"], META["Legs"] = build_low_legs()
    lows["Paws"] = build_paws(N + "PawsLow", GAME, low=True)
    lows["Jaw"] = build_jaw(N + "JawLow", GAME, 8, 3)
    m = Mesh()
    m.ball(NOSE + HD * 0.004 + HUP * 0.008, (0.033, 0.03, 0.024), 8, 5)
    lows["Nose"] = m.finish(N + "NoseLow", GAME)
    for side, tag in ((1, "L"), (-1, "R")):
        e = eyes[tag]
        lows["Lens" + tag] = build_lens(e, N + "Lens" + tag + "Low", GAME, 18, (0.36, 0.72, 1.08))
        lows["Pupil" + tag] = build_pupil(e, N + "Pupil" + tag + "Low", GAME, 10)
        lows["LidU" + tag], META["LidU" + tag] = build_lid(e, True, N + "LidU" + tag + "Low", GAME, 10, 2)
        lows["LidL" + tag], META["LidL" + tag] = build_lid(e, False, N + "LidL" + tag + "Low", GAME, 10, 2)
        lows["Rim" + tag] = build_rim(e, N + "Rim" + tag + "Low", GAME, 24, 5)
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 7, 4, N + "Ear" + tag + "Low")
    seat_eyes(lows["Head"], list(eyes.values()))
    eye_check(lows["Head"], list(eyes.values()))
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TAIL_F = (0.0, 0.17, 0.34, 0.51, 0.68, 0.84, 0.95)
TAIL_BONES = ("Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip")
TRUNK_F = (0.2, 0.42, 0.62, 0.82, 0.98)
TRUNK_BONES = ("Hips", "Body", "Chest", "Neck", "Head")
HEAD_PIVOT = V(0, -0.42, 0.9)
JAW_PIVOT = head_axis(0.46) - HUP * 0.05
MOUTH_AT = head_axis(0.88) - HUP * 0.03      # where it holds a star. PetRig puts it there, so this bone has the jaw's tip for its weights, or an export would drop it


def along(path, f):
    return path[min(len(path) - 1, int(round(f * (len(path) - 1))))].copy()


def skeleton(data):
    bones = [("Root", V(0, 0, 0), None), ("Body", along(TRUNK, TRUNK_F[1]), "Root"), ("Hips", along(TRUNK, TRUNK_F[0]), "Body"), ("Chest", along(TRUNK, TRUNK_F[2]), "Body"), ("Neck", along(TRUNK, TRUNK_F[3]), "Chest"), ("Head", HEAD_PIVOT.copy(), "Neck"), ("Jaw", JAW_PIVOT.copy(), "Head"), ("Mouth", MOUTH_AT.copy(), "Jaw")]
    for k, (name, f) in enumerate(zip(TAIL_BONES, TAIL_F)):
        bones.append((name, along(TAIL, f), TAIL_BONES[k - 1] if k else "Hips"))
    for side, tag in ((1, "L"), (-1, "R")):
        e = data["eyes"][tag]
        bones += [("Eye" + tag, e.p.copy(), "Head"), ("LidU" + tag, e.p.copy(), "Head"), ("LidL" + tag, e.p.copy(), "Head"), ("Ear" + tag, V(side * 0.128, -0.545, 1.03), "Head")]
    for key, side, knots, _ in LEGS:
        top = "Chest" if key[0] == "F" else "Hips"
        bones += [("Leg" + key + "1", mir(knots[0], side), top), ("Leg" + key + "2", mir(knots[1], side), "Leg" + key + "1"), ("Paw" + key, mir(knots[2], side), "Leg" + key + "2")]
    return armature(bones)


def leg_weight(key, f):
    if f < 0.28:
        return {"Leg" + key + "1": 1.0}
    if f < 0.38:
        t = float(smooth(0.28, 0.38, f))
        return {"Leg" + key + "1": 1 - t, "Leg" + key + "2": t}
    if f < 0.6:
        return {"Leg" + key + "2": 1.0}
    if f < 0.7:
        t = float(smooth(0.6, 0.7, f))
        return {"Leg" + key + "2": 1 - t, "Paw" + key: t}
    return {"Paw" + key: 1.0}


def bind_all(lows, rig, glows, data):
    f, _ = nearest_on(TRUNK, verts(lows["Skin"]))
    weigh(lows["Skin"], [chain_weight(TRUNK_BONES, TRUNK_F, float(x)) for x in f])
    f, _ = nearest_on(TAIL, verts(lows["Tail"]))
    weigh(lows["Tail"], [chain_weight(TAIL_BONES, TAIL_F, float(x)) for x in f])
    weigh(lows["Legs"], [leg_weight(key, f) for key, f in META["Legs"]])
    paws = verts(lows["Paws"])
    weigh(lows["Paws"], [{"Paw" + ("F" if p[1] < 0.1 else "B") + ("L" if p[0] > 0 else "R"): 1.0} for p in paws])
    for key in ("Head", "Nose"):
        rigid(lows[key], "Head")
    weigh(lows["Jaw"], [{"Mouth": 1.0} if p[1] < MOUTH_AT.y else {"Jaw": 1.0} for p in verts(lows["Jaw"])])
    for tag in ("L", "R"):
        rigid(lows["Lens" + tag], "Head")
        rigid(lows["Rim" + tag], "Head")
        rigid(lows["Pupil" + tag], "Eye" + tag)
        rigid(lows["Ear" + tag], "Ear" + tag)
        for key in ("LidU", "LidL"):
            weigh(lows[key + tag], [{"Head": 1.0} if s < 0.01 else ({key + tag: 1.0} if s > 0.99 else {"Head": 1 - s, key + tag: s}) for s in META[key + tag]])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateStarfallFox uses. +X turn: a limb's far end swings forward; +Y: turns to its left; +Z rolls
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def legs(fl, fr, bl, br, knee=0.5, paw=0.4):
    """Each leg's swing: positive forward. A leg folds as it comes through."""
    out = {}
    for key, a in (("FL", fl), ("FR", fr), ("BL", bl), ("BR", br)):
        lift = max(0.0, a) * knee
        sign = 1 if key[0] == "F" else -1
        out["Leg" + key + "1"] = game_turn(a, 0, 0)
        out["Leg" + key + "2"] = game_turn(sign * -lift, 0, 0)
        out["Paw" + key] = game_turn(sign * lift * paw, 0, 0)
    return out


def tail(a, b, c):
    return {"Tail1": game_turn(a, b, 0), "Tail2": game_turn(a * 0.5, b, 0), "Tail3": game_turn(0, b + c, 0), "Tail4": game_turn(0, c, 0), "Tail5": game_turn(0, c, 0), "Tail6": game_turn(0, c * 0.8, 0), "TailTip": game_turn(0, c * 0.6, 0)}


def pose_library(eyes):
    def lids(up, low):
        out = {}
        for tag, e in eyes.items():
            out["LidU" + tag] = (tuple(e.hinge), up, (0, 0, 0))
            out["LidL" + tag] = (tuple(e.hinge), -low, (0, 0, 0))
        return out

    def look(amount):
        out = {}
        for tag, e in eyes.items():
            out["Eye" + tag] = ((0, 0, 1), amount, (0, 0, 0))
        return out
    return {
        "Blink": lids(BLINK_U, BLINK_L),
        "WinkL": {"LidUL": (tuple(eyes["L"].hinge), BLINK_U, (0, 0, 0)), "LidLL": (tuple(eyes["L"].hinge), -BLINK_L, (0, 0, 0))},
        "LookLeft": look(3.5), "LookRight": look(-3.5),
        "Jaw": {"Jaw": game_turn(-0.42, 0, 0)},
        "EarsBack": {"EarL": game_turn(0.5, 0, -0.3), "EarR": game_turn(0.5, 0, 0.3)},
        "Trot1": {**legs(0.5, -0.5, -0.5, 0.5), **tail(-0.1, 0.3, 0.26)},
        "Trot2": {**legs(-0.5, 0.5, 0.5, -0.5), **tail(-0.1, -0.3, -0.26)},
        "Dig": {"Body": game_turn(-0.34, 0, 0, (0, 0, -0.12)), "Neck": game_turn(-0.4, 0, 0), "Head": game_turn(-0.3, 0, 0), **legs(0.9, 0.34, 0.34, 0.34), **tail(-0.5, 0.2, 0.2)},
        "Pounce": {"Body": game_turn(0.5, 0, 0, (0, 0, 0.4)), "Neck": game_turn(0.25, 0, 0), "Head": game_turn(0.3, 0, 0), **legs(1.0, 1.0, -1.0, -1.0, 0.0, 0.0), **tail(0.5, 0, 0)},
        "HeadUp": {"Neck": game_turn(0.4, 0, 0), "Head": game_turn(0.5, 0.2, 0.15), **lids(-2, 0)},
        "BehindL": {"Neck": game_turn(0, 0.45, 0), "Head": game_turn(0, 0.6, 0)}, "BehindR": {"Neck": game_turn(0, -0.45, 0), "Head": game_turn(0, -0.6, 0)},
    }


if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(pieces, data)
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=64, texels=TEXELS, margin=0.006)
    eye_reach = (0.004, 0.012)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.04, 0.05, 0.11, 1), far=("Skin", "Head", "Legs", "Tail"), reach=(0.012, 0.03), far_reach=(0.018, 0.05),
             reaches={k + t: eye_reach for k in ("Lens", "Pupil", "LidU", "LidL") for t in "LR"})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton(data)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    eyes = data["eyes"]
    for tag, e in eyes.items():
        print("EYE", tag, tuple(round(v, 4) for v in e.p), "hinge", tuple(round(v, 4) for v in e.hinge), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=5.6, size=640)
    lib = pose_library(eyes)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.26, -0.95, 0.06, 1.25, FACE_AT)
    whole = (0.72, -0.62, 0.18, 5.6, VIEW_AT)
    for name, view in (("Blink", close), ("WinkL", close), ("LookLeft", close), ("Jaw", (0.8, -0.6, 0.0, 1.5, FACE_AT)), ("EarsBack", close), ("Trot1", whole), ("Trot2", whole), ("Dig", whole), ("Pounce", whole), ("HeadUp", whole), ("BehindL", (0.4, 0.8, 0.3, 3.0, (0, -0.2, 0.9))), ("BehindR", (-0.4, -0.8, 0.3, 3.0, (0, -0.2, 0.9)))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 5.6, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

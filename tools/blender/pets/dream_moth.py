"""The Dream Moth (Common, Dreams; Bloomwood Egg): "It feeds on dreams you have already forgotten. Sleepers near one wake oddly rested."

A plump fluffy moth: a snow-white collar ruff, a banded lilac and rose body, feathery antennae like small fern leaves, a coiled tongue. Four broad dusty wings: a cream crescent moon on each forewing, and on each hindwing an eyespot drawn as a sleeping eye,
its lid closed and lashed. Its face is like no other pet's: two misty compound eyes, finely faceted, each with the dark pseudopupil a real insect's eye has, the spot that seems to follow you round the room. Here it does.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/dream_moth.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up. It never lands: its middle hovers at about z = 0.9. The maps go to assets/pets/BloomwoodEgg/.

What touches what: the head is sunk into the collar ruff; the eyes into the head; each pseudopupil lies on its eye; the antennae and the tongue's root are buried in the head; the wings' roots are buried in the thorax, forewing above hindwing with a gap between;
the legs' roots are buried in the thorax's underside.
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
PET = "DreamMoth"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BloomwoodEgg")

# ---------- colours ----------
CREAM, WHITE, LILAC, LILAC_D, ROSE, PEACH = rgb(250, 240, 230), rgb(252, 250, 255), rgb(196, 168, 230), rgb(150, 116, 196), rgb(240, 160, 196), rgb(252, 204, 178)
PLUM, PLUM_D, SILVER, GOLD_TAN, EYE_MIST = rgb(110, 62, 120), rgb(56, 28, 66), rgb(236, 236, 252), rgb(214, 178, 120), rgb(170, 158, 206)

# ---------- the frame of it ----------
THORAX = V(0, -0.12, 0.92)
HEAD = V(0, -0.33, 0.935)
ABDOMEN = catmull([V(0, -0.02, 0.91), V(0, 0.14, 0.885), V(0, 0.3, 0.83), V(0, 0.43, 0.77)], 10)
EYE_R = 0.054
EYES = {"L": V(0.07, -0.366, 0.952), "R": V(-0.07, -0.366, 0.952)}
MOUTH = V(0, -0.395, 0.9)      # (inside the head: the coil grows out of it)
ANTENNA = {s: [V(s * 0.03, -0.37, 1.01), V(s * 0.07, -0.43, 1.12), V(s * 0.15, -0.48, 1.21), V(s * 0.25, -0.49, 1.26)] for s in (1, -1)}
LEG_ROOTS = (("F", V(0.055, -0.2, 0.83), V(0.105, -0.1, -0.1), V(0.02, -0.06, -0.12)), ("M", V(0.065, -0.13, 0.82), V(0.125, -0.02, -0.12), V(0.02, 0.03, -0.13)), ("B", V(0.06, -0.08, 0.83), V(0.13, 0.08, -0.13), V(0.0, 0.08, -0.14)))      # (roots inside the thorax)
WING = {   # root (x, y, z), its angles from the leading edge to the trailing, the outline's reach at each angle, the lift over the span
    "Fore": (V(0.105, -0.17, 0.965), (-0.3, 1.22), ((-0.3, 0.6), (-0.16, 0.76), (0.0, 0.82), (0.2, 0.8), (0.45, 0.7), (0.72, 0.56), (0.98, 0.4), (1.22, 0.2))),
    "Hind": (V(0.095, -0.07, 0.935), (0.12, 1.85), ((0.12, 0.42), (0.38, 0.58), (0.68, 0.64), (1.0, 0.64), (1.3, 0.58), (1.58, 0.44), (1.85, 0.22))),
}
WING_LIFT = {"Fore": 0.2, "Hind": 0.13}
WING_THICK = 0.006


def puff(m, c, d, length, width, seg=14, rings=10):
    """A soft lobe of fluff: an egg lying along d, its round end out. Many of them fused make a cloud."""
    d = d.normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    M = Matrix.Translation(c + d * length * 0.5) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((width, width, length * 0.62, 1))
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=M)


def resample(path, n):
    a = [Vector(p) for p in path]
    out = []
    for k in range(n):
        f = k / (n - 1) * (len(a) - 1)
        i = min(int(f), len(a) - 2)
        out.append(a[i].lerp(a[i + 1], f - i))
    return out


def abdomen_radius(f):
    base = float(np.interp(f, (0, 0.15, 0.5, 0.82, 1), (0.11, 0.122, 0.112, 0.075, 0.03)))
    return base * (1 + 0.035 * math.cos(f * 7 * TAU) * (1 - f * 0.4))      # seven soft segments


# ---------- the body: thorax and abdomen, all fur ----------
RUFF_C, RUFF_R = V(0, -0.19, 0.93), (0.19, 0.13, 0.175)
RUFF_LOBES = 9


def build_ruff():
    """The collar: one big round pom-pom round the neck, soft lobes all round its rim."""
    m = Mesh()
    m.ball(RUFF_C, RUFF_R, 96, 64)
    o = m.finish(N + "Ruff", HI)
    P = verts(o)
    d = P - np.array(tuple(RUFF_C))
    a = np.arctan2(d[:, 0], d[:, 2])
    rim = 1 - smooth(0.25, 0.9, np.abs(d[:, 1]) / RUFF_R[1])
    lobe = 1 + 0.085 * np.cos(a * RUFF_LOBES) * rim + 0.03 * np.cos(a * RUFF_LOBES * 2 + 1.3) * rim
    set_verts(o, np.array(tuple(RUFF_C)) + d * lobe[:, None])
    return o


def body_clumps(m):
    ruff = build_ruff()
    m.bm.from_mesh(ruff.data)
    bpy.data.objects.remove(ruff, do_unlink=True)
    # a soft brush at the tip of the abdomen
    tip = ABDOMEN[-1]
    for k in range(6):
        a = TAU * k / 6
        puff(m, tip + V(math.sin(a) * 0.012, -0.01, math.cos(a) * 0.012), V(math.sin(a) * 0.4, 1, math.cos(a) * 0.4), 0.06, 0.026)


def build_body(name, coll, fur=True):
    m = Mesh()
    m.ball(THORAX, (0.135, 0.15, 0.135), 40, 28)
    m.tube(ABDOMEN, abdomen_radius, sides=32)
    if fur:
        body_clumps(m)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0045, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the head ----------
def build_head(name, coll):
    m = Mesh()
    m.ball(HEAD + V(0, -0.005, -0.004), (0.082, 0.082, 0.078), 32, 24)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0032, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def eye_normal(tag):
    """Where the pseudopupil rests: mostly forward, a little out. (In the game it turns to face whoever is looking.)"""
    side = 1 if tag == "L" else -1
    return V(side * 0.42, -1, 0.08).normalized()


def build_eyes(name, coll, seg, rings):
    m = Mesh()
    for tag in ("L", "R"):
        m.ball(EYES[tag], (EYE_R, EYE_R, EYE_R), seg, rings)
    return m.finish(name, coll)


PUPIL_ANGLE = 0.36      # radians: the pseudopupil's size on the eye


def build_pupils(name, coll, sides, rows):
    """A dark cap on each eye: the pseudopupil. It turns on the eye's centre, so it always lies on the eye."""
    m = Mesh()
    bm = m.bm
    for tag in ("L", "R"):
        c, n = EYES[tag], eye_normal(tag)
        u = n.orthogonal().normalized()
        v = n.cross(u).normalized()
        hub = bm.verts.new(c + n * (EYE_R + 0.0016))
        grid = []
        for i in range(1, rows + 1):
            th = PUPIL_ANGLE * i / rows
            ring = []
            for k in range(sides):
                a = TAU * k / sides
                d = (n * math.cos(th) + (u * math.cos(a) + v * math.sin(a)) * math.sin(th)).normalized()
                ring.append(bm.verts.new(c + d * (EYE_R + 0.0016)))
            grid.append(ring)
        fs = [bm.faces.new((hub, grid[0][k], grid[0][(k + 1) % sides])) for k in range(sides)]
        for i in range(rows - 1):
            for k in range(sides):
                k2 = (k + 1) % sides
                fs.append(bm.faces.new((grid[i][k], grid[i + 1][k], grid[i + 1][k2], grid[i][k2])))
        for f in fs:
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - c) < 0:
                f.normal_flip()
    return m.finish(name, coll, recalc=False)


# ---------- the tongue: a watch-spring coil under the head ----------
TONGUE_STEPS, TONGUE_STEP = 72, 0.0034
TONGUE_BONES = 12


def tongue_path():
    """From the mouth, heading down and a little forward, curling ever tighter: a spiral of about one and a half turns in the plane of its face."""
    p = MOUTH.copy()
    a = -math.pi / 2 - 0.35
    pts, turns = [p.copy()], [0.0]
    total = 0.0
    for i in range(TONGUE_STEPS):
        f = i / TONGUE_STEPS
        k = 14 + 70 * f ** 1.6           # curvature: tighter toward the tip
        a -= k * TONGUE_STEP
        total += k * TONGUE_STEP
        p = p + V(0, math.cos(a), math.sin(a)) * TONGUE_STEP
        pts.append(p.copy())
        turns.append(total)
    return pts, turns


def tongue_radius(f):
    return 0.0075 - 0.0035 * f


def tongue_bends():
    """How far each bone's stretch of the coil turns: unrolling the tongue is undoing these."""
    pts, turns = tongue_path()
    n = len(pts) - 1
    idx = [round(n * b / TONGUE_BONES) for b in range(TONGUE_BONES + 1)]
    return [turns[idx[b + 1]] - turns[idx[b]] for b in range(TONGUE_BONES)], [pts[i] for i in idx[:-1]]


def build_tongue(name, coll, sides, step=1):
    pts, _ = tongue_path()
    pts = pts[::step] + ([pts[-1]] if (len(pts) - 1) % step else [])
    m = Mesh()
    m.tube(pts, tongue_radius, sides=sides, plane=V(1, 0, 0))
    return m.finish(name, coll)


# ---------- antennae: fern-leaf plumes ----------
def antenna_path(side, per=10):
    return catmull(ANTENNA[side], per)


def plume_width(f):
    return 0.046 * math.sin(math.pi * min(1.0, 0.06 + f * 0.94)) ** 0.7 * (1 - 0.4 * f)


def antenna_frame(path, i):
    n = len(path)
    tan = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
    side = tan.cross(V(0, 0, 1))
    if side.length < 1e-4:
        side = V(1, 0, 0)
    side.normalize()
    up = side.cross(tan).normalized()
    return tan, side, up


def build_antennae_hi(name, coll):
    m = Mesh()
    for side in (1, -1):
        path = antenna_path(side, 24)
        n = len(path)
        m.tube(path, lambda f: 0.0055 - 0.0035 * f, sides=10)
        # a thin vane between the barbs, so the plume reads whole: and so the bake always finds something under the leaf
        m.tube(path, lambda f: plume_width(f) * 0.86 + 0.001, sides=16, flat=0.09, plane=V(0, 0, 1))
        for i in range(2, n - 1):
            f = i / (n - 1)
            tan, s_, up = antenna_frame(path, i)
            w = plume_width(f)
            for sgn in (1, -1):
                tip = path[i] + s_ * sgn * w + tan * w * 0.55 + up * 0.004
                m.tube([path[i], path[i].lerp(tip, 0.5) + up * 0.002, tip], lambda g: 0.0022 * (1 - 0.6 * g), sides=6)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0014, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.4, "iterations": 1})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_antennae_low():
    """Each a leaf with a toothed edge: the plume's outline, with the barbs baked in. Its upper and lower faces are separate sheets: one closed thin sheet bends the bake's rays at its edge (black rims)."""
    m = Mesh()
    bm = m.bm
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = antenna_path(side, 3)
        n = len(path)
        for lift in (1, -1):
            rows = []
            for i in range(n):
                f = i / (n - 1)
                tan, s_, up = antenna_frame(path, i)
                w = plume_width(f) * (0.92 if i % 2 else 0.74)
                row = [path[i] + s_ * w + tan * w * 0.5, path[i] + up * 0.003 * lift, path[i] - s_ * w + tan * w * 0.5]
                rows.append([bm.verts.new(p) for p in row])
                meta += [(tag, f)] * 3
            for i in range(n - 1):
                for k in range(2):
                    q = (rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k])
                    bm.faces.new(q if lift > 0 else tuple(reversed(q)))
    for f in bm.faces:
        f.normal_update()
    o = m.finish(N + "AntennaeLow", GAME, recalc=False)
    return o, meta


# ---------- legs: thin and furry, tucked a little ----------
def leg_path(key, side, per=6):
    _, root, a, b = next(l for l in LEG_ROOTS if l[0] == key)
    r = mir(root, side)
    k1 = r + V(a.x * side, a.y, a.z)
    k2 = k1 + V(b.x * side, b.y, b.z)
    k3 = k2 + V(0.006 * side, -0.035, -0.045)
    return catmull([r, k1, k2, k3], per)


def leg_radius(f):
    return float(np.interp(f, (0, 0.33, 0.66, 1), (0.016, 0.013, 0.009, 0.006)))


def build_legs_hi(name, coll):
    m = Mesh()
    for side in (1, -1):
        for key, *_ in LEG_ROOTS:
            path = leg_path(key, side, 10)
            m.tube(path, leg_radius, sides=12)
            n = len(path)
            i = int(0.42 * (n - 1))       # a fluffy cuff on each shin
            tan = (path[i + 1] - path[i]).normalized()
            puff(m, path[i], tan, 0.07, 0.022, 16, 10)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0022, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_legs_low():
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        for key, *_ in LEG_ROOTS:
            path = resample(leg_path(key, side, 6), 6)
            m.tube(path, lambda f: leg_radius(f) * 1.35, sides=5)
            meta += [(key + tag, i / 5) for i in range(6) for _ in range(5)]
    return m.finish(N + "LegsLow", GAME), meta


# ---------- wings ----------
def wing_reach(key, phi):
    knots = WING[key][2]
    base = float(np.interp(phi, [k[0] for k in knots], [k[1] for k in knots]))
    return base * (1 + 0.022 * math.sin(phi * (26 if key == "Fore" else 20)))      # scalloped between the veins


def wing_point(key, side, u, v, lift=0.0):
    """u: from the root out to the edge; v: across, from the leading edge to the trailing. Lies in the wing's plane, which rises a little toward the tip."""
    root, (p0, p1), _ = WING[key]
    phi = p0 + (p1 - p0) * v
    r = wing_reach(key, phi) * (0.06 + 0.94 * u)
    x, y = math.cos(phi) * r, math.sin(phi) * r
    z = WING_LIFT[key] * (r / 0.6) ** 1.3 - 0.018 * math.sin(math.pi * v) * u ** 2 + lift      # (raised in a shallow V, each wing a little cupped)
    return V(root.x * side + side * x, root.y + y, root.z + z)


def build_wing(key, side, name, coll, nu, nv):
    m = Mesh()
    m.sheet(lambda u, v: wing_point(key, side, u, v), lambda u, v: WING_THICK * (1 - 0.5 * u), nu, nv)
    return m.finish(name, coll)


def wing_coords(key, side, P):
    """Per point: how far out (0 at the root, 1 at the edge) and across (0 leading, 1 trailing) the wing it lies."""
    root, (p0, p1), _ = WING[key]
    x = (P[:, 0] - root.x * side) * side
    y = P[:, 1] - root.y
    phi = np.arctan2(y, x)
    v = (phi - p0) / (p1 - p0)
    reach = np.interp(phi, [k[0] for k in WING[key][2]], [k[1] for k in WING[key][2]]) * (1 + 0.022 * np.sin(phi * (26 if key == "Fore" else 20)))
    r = np.hypot(x, y)
    u = (r / reach - 0.06) / 0.94
    return np.clip(u, 0, 1.05), np.clip(v, -0.05, 1.05), r


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_body(N + "SkinHi", HI)
    pieces["Head"] = build_head(N + "HeadHi", HI)
    for key in ("Skin", "Head"):
        data[key + "Base"] = bpy.data.objects.new(N + key + "Base", pieces[key].data.copy())
        HI.objects.link(data[key + "Base"])
        data[key + "Base"].hide_render = True
    pieces["Eyes"] = build_eyes(N + "EyesHi", HI, 200, 140)
    pieces["Pupils"] = build_pupils(N + "PupilsHi", HI, 48, 10)
    pieces["Tongue"] = build_tongue(N + "TongueHi", HI, 14)
    pieces["Antennae"] = build_antennae_hi(N + "AntennaeHi", HI)
    pieces["Legs"] = build_legs_hi(N + "LegsHi", HI)
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            pieces[key + tag] = build_wing(key, side, N + key + tag + "Hi", HI, 120, 140)
    if not clay:
        paint_all(pieces)
    return pieces, data


def worley2(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point: their difference is the cell's edge."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt(sum((q[:, k] - c[:, k] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + k + 1)) ** 2 for k in range(3)))
                d2 = np.where(d < d1, d1, np.minimum(d2, d))
                d1 = np.minimum(d1, d)
    return d1, d2


def fur(P, centre, f, seed):
    """Fine strands lying outward from a centre: noise stretched along the way the fur grows."""
    d = P - np.array(tuple(centre))
    r = np.linalg.norm(d, axis=1)[:, None]
    n = d / np.maximum(r, 1e-6)
    Q = n * 0.18 + d * 0.0      # (by direction only: long strands)
    return fbm(Q * np.array((1.0, 1.0, 1.0)), f, 3, seed)


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    d = P - np.array(tuple(RUFF_C))
    in_ruff = np.linalg.norm(d / np.array(RUFF_R), axis=1) < 1.16
    strand = fur(P, RUFF_C, 160.0, 3)
    a = np.arctan2(d[:, 0], d[:, 2])
    rim = 1 - smooth(0.25, 0.9, np.abs(d[:, 1]) / RUFF_R[1])
    tips = smooth(0.4, 0.95, np.cos(a * RUFF_LOBES)) * rim
    ruff = mix(WHITE, mix(LILAC, ROSE, 0.3), tips * 0.55)
    ruff = mix(ruff, CREAM, smooth(0.45, 0.75, strand) * 0.5)
    # the abdomen: bands of rose and cream, lilac beneath
    f, dist = nearest_on(ABDOMEN, P)
    band = 0.5 + 0.5 * np.cos(f * 7 * TAU + 0.6)
    belly = smooth(0.1, -0.6, Nn[:, 2])
    strand2 = fbm(P * np.array((1.0, 0.2, 1.0)), 150.0, 3, 7)
    body = mix(CREAM, mix(ROSE, LILAC, 0.3), smooth(0.3, 0.8, band) * 0.7)
    body = mix(body, LILAC, belly * 0.7)
    body = mix(body, WHITE, smooth(0.86, 1.0, f) * 0.8)
    body = body * (0.88 + 0.12 * strand2)[:, None]
    col = np.where(in_ruff[:, None], ruff * (0.9 + 0.1 * strand)[:, None], body)
    set_verts(o, P + Nn * (np.where(in_ruff, 0.006 * (strand - 0.5), 0.003 * (strand2 - 0.5)))[:, None])
    paint(o, col, 0.92)


def paint_head(o):
    P = verts(o)
    Nn = normals(o)
    strand = fur(P, HEAD, 170.0, 9)
    col = mix(CREAM, WHITE, smooth(-0.4, 0.5, Nn[:, 2]))
    col = mix(col, ROSE, smooth(-0.2, -0.8, Nn[:, 2]) * 0.22)
    col = col * (0.88 + 0.12 * strand)[:, None]
    set_verts(o, P + Nn * (0.004 * (strand - 0.5))[:, None])
    paint(o, col, 0.92)


def paint_eyes(o):
    """Misty compound eyes: a fine honeycomb of facets, a sheen at the top, darker toward the head."""
    P = verts(o)
    Nn = normals(o)
    col = np.zeros((len(P), 3))
    disp = np.zeros(len(P))
    for tag in ("L", "R"):
        c = np.array(tuple(EYES[tag]))
        mine = np.linalg.norm(P - c, axis=1) < EYE_R * 1.2
        d1, d2 = worley2((P - c) / EYE_R, 13.0, 21)
        edge = 1 - smooth(0.0, 0.12, d2 - d1)
        out = (P - c) @ np.array(tuple(eye_normal(tag))) / EYE_R
        here = mix(mix(LILAC_D, EYE_MIST, smooth(-0.6, 0.6, out)), SILVER, smooth(0.5, 1.0, Nn[:, 2]) * 0.25)
        here = mix(here, PLUM, edge * 0.45)
        col = np.where(mine[:, None], here, col)
        disp = np.where(mine, -0.0012 * edge, disp)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, 0.22)


def paint_pupils(o):
    P = verts(o)
    col = np.zeros((len(P), 3))
    for tag in ("L", "R"):
        c, n = np.array(tuple(EYES[tag])), np.array(tuple(eye_normal(tag)))
        d = (P - c) / np.linalg.norm(P - c, axis=1)[:, None]
        th = np.arccos(np.clip(d @ n, -1, 1)) / PUPIL_ANGLE
        here = mix(PLUM_D, mix(PLUM, LILAC_D, 0.4), smooth(0.45, 1.0, th))
        col = np.where(((P - c) @ n > 0)[:, None] & (np.linalg.norm(P - c, axis=1) < EYE_R * 1.2)[:, None], here, col)
    paint(o, col, 0.2)


def paint_tongue(o):
    P = verts(o)
    col = mix(GOLD_TAN, rgb(170, 128, 82), smooth(0.4, 0.8, fbm(P, 400.0, 2, 3)))
    paint(o, col, 0.5)


def paint_antennae(o):
    P = verts(o)
    best = np.full(len(P), 9.0)
    for side in (1, -1):
        _, d = nearest_on(antenna_path(side, 24), P)
        best = np.minimum(best, d)
    vane = np.abs(normals(o)[:, 2]) > 0.8
    col = mix(rgb(150, 112, 70), GOLD_TAN, smooth(0.004, 0.02, best))
    col = mix(col, CREAM, smooth(0.018, 0.036, best) * 0.8)
    col = np.where((vane & (best > 0.006))[:, None], mix(rgb(120, 86, 60), PLUM, 0.25), col)      # the vane between the barbs: dark, so the barbs read
    paint(o, col, 0.7)


def paint_legs(o):
    P = verts(o)
    strand = fbm(P, 220.0, 2, 3)
    col = mix(mix(CREAM, LILAC, 0.35), WHITE, smooth(0.5, 0.8, strand))
    col = mix(col, PLUM, smooth(0.73, 0.69, P[:, 2]) * 0.5)
    paint(o, col, 0.9)


def wavy(u, v, at, waves, amp):
    return u - (at + amp * np.sin(v * waves * math.pi))


def paint_wing(o, key, side):
    """Dusty scales. The forewing: lilac going rose, two wavy lines across, a cream crescent moon between them, a pale band, a chequered fringe. The hindwing: peach going rose, with an eyespot that is a sleeping eye, its lid closed and lashed.
    Beneath, the same, paler and plainer."""
    P = verts(o)
    Nn = normals(o)
    u, v, r = wing_coords(key, side, P)
    under = Nn[:, 2] < 0
    scale = fbm(P * np.array((1.0, 1.0, 1.0)), 260.0, 2, 13)
    veins = np.zeros(len(P))
    root, (p0, p1), _ = WING[key]
    for k in range(1, 9):
        vk = k / 9
        veins = np.maximum(veins, np.exp(-((v - vk) * r / 0.0035) ** 2) * smooth(0.12, 0.3, u))
    fringe = smooth(0.95, 0.99, u)
    checks = smooth(-0.2, 0.2, np.sin(v * (40 if key == "Fore" else 34) * math.pi))
    def at(uc, vc):
        c = wing_point(key, side, uc, vc)
        return (P[:, 0] - c.x) * side, P[:, 1] - c.y
    if key == "Fore":
        col = mix(LILAC, mix(LILAC, ROSE, 0.55), smooth(0.2, 0.9, v))
        col = mix(col, mix(LILAC_D, PLUM, 0.3), np.exp(-(wavy(u, v, 0.36, 3, 0.03) / 0.012) ** 2))
        col = mix(col, mix(LILAC_D, PLUM, 0.3), np.exp(-(wavy(u, v, 0.72, 4, 0.025) / 0.012) ** 2))
        col = mix(col, mix(CREAM, LILAC, 0.25), smooth(0.76, 0.84, u) * (1 - smooth(0.88, 0.92, u)) * 0.7)
        # the moon: a crescent, lit from the trailing side
        dx, dy = at(0.55, 0.4)
        rr = np.hypot(dx, dy)
        dark = np.hypot(dx - 0.026, dy - 0.012)
        moon = (1 - smooth(0.05, 0.056, rr)) * smooth(0.042, 0.048, dark)
        ring = np.exp(-((rr - 0.056) / 0.0035) ** 2) * smooth(0.04, 0.05, dark)
        col = mix(col, mix(PLUM, PLUM_D, 0.3), ring * 0.8)
        col = mix(col, CREAM, moon)
        base = mix(CREAM, LILAC, 0.25)
    else:
        col = mix(PEACH, ROSE, smooth(0.15, 0.85, u))
        col = mix(col, mix(ROSE, LILAC, 0.4), smooth(0.6, 1.0, v) * 0.5)
        # the sleeping eye: an eyespot, rings of plum and lilac round a cream lid that is closed, its lashes hanging
        dx, dy = at(0.6, 0.5)
        # its long axis along the wing's span: x across the eye, y up it
        rr = np.hypot(dx / 1.25, dy)
        col = mix(col, PLUM, 1 - smooth(0.07, 0.076, rr))
        col = mix(col, mix(LILAC, ROSE, 0.2), 1 - smooth(0.058, 0.063, rr))
        col = mix(col, CREAM, 1 - smooth(0.046, 0.05, rr))
        # the lid, closed: a curve across the middle, bowed down, and its lashes hanging from it
        w = dx / 0.058
        lid_y = 0.006 - 0.014 * (1 - w * w)
        lidline = np.exp(-((dy - lid_y) / 0.0032) ** 2) * (np.abs(w) < 1)
        col = mix(col, PLUM_D, lidline)
        col = mix(col, mix(CREAM, ROSE, 0.35), smooth(0.0, 0.004, dy - lid_y) * (1 - smooth(0.046, 0.05, rr)) * 0.6)      # the lid itself, a little rosier
        lashes = np.zeros(len(P))
        for k in range(-3, 4):
            lx = k * 0.014
            ly = 0.006 - 0.014 * (1 - (lx / 0.058) ** 2)
            t = (ly - dy) / 0.016
            lashes = np.maximum(lashes, np.exp(-((dx - lx - t * 0.006 * k) / 0.0024) ** 2) * (t > 0) * (t < 1))
        col = mix(col, PLUM_D, lashes * 0.9)
        base = mix(PEACH, CREAM, 0.4)
    col = mix(col, col * 0.84, veins * 0.5)
    col = mix(col, mix(mix(PLUM, LILAC_D, 0.5), mix(CREAM, LILAC, 0.3), checks), fringe * 0.85)
    col = mix(col, WHITE, smooth(0.0, 0.14, 0.14 - u) * 0.75)       # the furry root
    col = col * (0.92 + 0.08 * scale)[:, None]
    sparkle = (1 - smooth(0.04, 0.08, worley2(P, 90.0, 5)[0])) * smooth(0.6, 0.7, fbm(P, 20.0, 2, 3))
    col = mix(col, SILVER, sparkle * 0.8)
    under_col = mix(base, col, 0.35)
    col = np.where(under[:, None], under_col, col)
    paint(o, col, 0.72 - 0.3 * sparkle)


def paint_all(pieces):
    paint_skin(pieces["Skin"])
    paint_head(pieces["Head"])
    paint_eyes(pieces["Eyes"])
    paint_pupils(pieces["Pupils"])
    paint_tongue(pieces["Tongue"])
    paint_antennae(pieces["Antennae"])
    paint_legs(pieces["Legs"])
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            paint_wing(pieces[key + tag], key, side)


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.0, 0.92)
FACE_AT = (0, -0.33, 0.95)
EXTRA = [(0, -1, 0.05, 0.9, FACE_AT), (0.62, -0.78, 0.12, 0.9, FACE_AT), (1, -0.1, 0.02, 1.0, FACE_AT), (0.25, -0.85, 0.48, 1.0, FACE_AT), (0.3, -0.95, 0.06, 0.42, (0.05, -0.36, 0.95)), (0.0, -0.05, 1.0, 2.6, (0.55, 0.05, 0.95)), (0.2, -0.3, -0.95, 2.4, (0.3, 0.05, 0.9))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=5.2, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Head": 2.0, "Eyes": 2.6, "Pupils": 2.0, "Tongue": 1.2, "Antennae": 1.4, "Legs": 0.8, "ForeL": 1.25, "ForeR": 1.25, "HindL": 1.25, "HindR": 1.25}
META = {}
PUPIL_TURN = 0.55      # radians the pseudopupils may turn either way to face whoever looks


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
        if gap < 0.006:
            break
    assert best_gap < 0.012, name + ": every re-mesh strayed from the sculpt"
    best.name = N + name + "Low"
    for v in best.data.vertices:
        v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.8)
    return best


def build_low(data):
    # the body by decimation, not QuadriFlow: QuadriFlow skates over the tight crease where the ruff meets the thorax (gaps of 1.5 to 3.8 cm in every try)
    skin = decimated(data["SkinBase"], N + "SkinLow", 2100)
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    print("SKIN decimated", len(skin.data.polygons), "gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), flush=True)
    lows = {"Skin": skin, "Head": truest(data["HeadBase"], "Head", (360, 420, 320, 480))}
    lows["Eyes"] = build_eyes(N + "EyesLow", GAME, 14, 9)
    lows["Pupils"] = build_pupils(N + "PupilsLow", GAME, 10, 2)
    lows["Tongue"] = build_tongue(N + "TongueLow", GAME, 6, 3)
    lows["Antennae"], META["Antennae"] = build_antennae_low()
    lows["Legs"], META["Legs"] = build_legs_low()
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            lows[key + tag] = build_wing(key, side, N + key + tag + "Low", GAME, 5, 15)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
ABD_F = (0.08, 0.32, 0.58, 0.84)
ABD_BONES = ("Body", "Abd1", "Abd2", "Abd3")
NECK = V(0, -0.265, 0.93)


def path_at(path, f):
    return path[min(len(path) - 1, int(round(f * (len(path) - 1))))].copy()


def tongue_names():
    return ["Tongue%d" % (k + 1) for k in range(TONGUE_BONES)]


def skeleton():
    bends, joints = tongue_bends()
    print("BENDS", [round(b, 4) for b in bends], flush=True)
    bones = [("Root", V(0, 0, 0), None), ("Body", THORAX.copy(), "Root"), ("Head", NECK.copy(), "Body")]
    parent = "Body"
    for name, f in zip(ABD_BONES[1:], ABD_F[1:]):
        bones.append((name, path_at(ABDOMEN, f), parent))
        parent = name
    for tag in ("L", "R"):
        bones.append(("Pupil" + tag, EYES[tag].copy(), "Head"))
    for side, tag in ((1, "L"), (-1, "R")):
        path = antenna_path(side, 10)
        bones += [("Ant" + tag + "1", ANTENNA[side][0].copy(), "Head"), ("Ant" + tag + "2", path_at(path, 0.4), "Ant" + tag + "1")]
        for key in ("Fore", "Hind"):
            root = WING[key][0]
            bones += [(key + tag + "1", V(root.x * side, root.y, root.z), "Body"), (key + tag + "2", wing_point(key, side, 0.45, 0.35 if key == "Fore" else 0.5), key + tag + "1")]
        for key, *_ in LEG_ROOTS:
            path = leg_path(key, side, 6)
            bones += [("Leg" + key + tag + "1", path[0].copy(), "Body"), ("Leg" + key + tag + "2", path_at(path, 0.36), "Leg" + key + tag + "1")]
    parent = "Head"
    for name, j in zip(tongue_names(), joints):
        bones.append((name, j.copy(), parent))
        parent = name
    return armature(bones)


def blend(names, cuts, f, width=0.06):
    for k, cut in enumerate(cuts):
        if f < cut - width:
            return {names[k]: 1.0}
        if f < cut + width:
            t = float(smooth(cut - width, cut + width, f))
            return {names[k]: 1 - t, names[k + 1]: t}
    return {names[-1]: 1.0}


def bind_all(lows, rig):
    f, _ = nearest_on(ABDOMEN, verts(lows["Skin"]))
    P = verts(lows["Skin"])
    weigh(lows["Skin"], [{"Body": 1.0} if p[1] < 0.0 else chain_weight(ABD_BONES, ABD_F, float(x)) for p, x in zip(P, f)])
    rigid(lows["Head"], "Head")
    rigid(lows["Eyes"], "Head")
    weigh(lows["Pupils"], [{"PupilL" if p[0] > 0 else "PupilR": 1.0} for p in verts(lows["Pupils"])])
    weigh(lows["Antennae"], [blend(("Ant%s1" % t, "Ant%s2" % t), (0.4,), f) for t, f in META["Antennae"]])
    weigh(lows["Legs"], [blend(("Leg%s1" % k, "Leg%s2" % k), (0.36,), f) for k, f in META["Legs"]])
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            u, v, r = wing_coords(key, side, verts(lows[key + tag]))
            weigh(lows[key + tag], [blend((key + tag + "1", key + tag + "2"), (0.45,), float(x), 0.12) for x in u])
    # the tongue: along its length, each stretch to its bone, shading into the next
    pts, _ = tongue_path()
    tv = verts(lows["Tongue"])
    f, _ = nearest_on(pts, tv)
    names = tongue_names()
    cuts = [(k + 1) / TONGUE_BONES for k in range(TONGUE_BONES - 1)]
    weigh(lows["Tongue"], [blend(names, cuts, float(x), 0.035) for x in f])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body])
    return body


# poses in the game's axes: the same numbers PetRig's animateDreamMoth uses. +X: a limb's far end swings forward, a head lifts; +Y: turns to its left; +Z rolls (a left wing's tip goes down)
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def wings(fore, hind, bend=0.0, sweep=0.0):
    """Raise (positive) or lower both pairs; bend: the outer half follows."""
    out = {}
    for tag, up in (("L", -1), ("R", 1)):
        out["Fore%s1" % tag] = game_turn(0, -up * sweep, up * fore)
        out["Fore%s2" % tag] = game_turn(0, 0, up * bend)
        out["Hind%s1" % tag] = game_turn(0, -up * sweep * 0.6, up * hind)
        out["Hind%s2" % tag] = game_turn(0, 0, up * bend * 0.8)
    return out


def pose_library():
    bends, _ = tongue_bends()
    names = tongue_names()
    sip = {names[k + 1]: game_turn(-bends[k] * 0.92, 0, 0) for k in range(TONGUE_BONES - 1)}
    sip[names[0]] = game_turn(0.3, 0, 0)
    half = {names[k + 1]: game_turn(-bends[k] * 0.5, 0, 0) for k in range(TONGUE_BONES - 1)}
    look = lambda yaw, pitch: {"PupilL": game_turn(pitch, yaw, 0), "PupilR": game_turn(pitch, yaw, 0)}
    return {
        "Up": {**wings(0.7, 0.55, 0.2), "Body": game_turn(0.1, 0, 0)},
        "Down": {**wings(-0.55, -0.45, -0.15), "Body": game_turn(-0.05, 0, 0)},
        "Closed": wings(1.35, 1.2, 0.1),
        "Sip": {**sip, "Head": game_turn(-0.15, 0, 0)},
        "Half": half,
        "LookL": look(PUPIL_TURN, 0), "LookUp": look(0, PUPIL_TURN),
        "Tilt": {"Head": game_turn(0.1, 0.3, 0.35), "AntL1": game_turn(0.3, 0, 0), "AntR1": game_turn(-0.2, 0, 0.2)},
        "Curl": {"Abd1": game_turn(-0.25, 0, 0), "Abd2": game_turn(-0.25, 0, 0), "Abd3": game_turn(-0.3, 0, 0)},
    }


if __name__ == "__main__" and STAGE == "all":
    pieces, data = build_hi()
    mat = hi_material(ao_distance=0.04, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(data)
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=62, texels=TEXELS, margin=0.006)
    wing_reach_ = {k + t: (0.005, 0.012) for k in ("Fore", "Hind") for t in "LR"}
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.8, 0.74, 0.88, 1), far=("Skin", "Head", "Legs"), reach=(0.008, 0.02), far_reach=(0.014, 0.04),
             reaches={**wing_reach_, "Pupils": (0.002, 0.005), "Eyes": (0.006, 0.014), "Antennae": (0.016, 0.05), "Tongue": (0.006, 0.014)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    rig = skeleton()
    body = bind_all(lows, rig)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    for tag in ("L", "R"):
        print("EYE", tag, tuple(round(v, 4) for v in EYES[tag]), "rest", tuple(round(v, 4) for v in eye_normal(tag)), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=5.2, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.25, -0.95, 0.1, 0.9, FACE_AT)
    whole = (0.62, -0.72, 0.28, 5.2, VIEW_AT)
    for name, view in (("Up", whole), ("Down", whole), ("Closed", whole), ("Sip", (0.9, -0.3, 0.0, 1.2, (0, -0.42, 0.8))), ("Half", (0.9, -0.3, 0.0, 1.0, (0, -0.42, 0.85))), ("LookL", close), ("LookUp", close), ("Tilt", close), ("Curl", (1, 0.2, 0, 2.2, (0, 0.15, 0.85)))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    path = save_all((0.62, -0.72, 0.28, 5.2, VIEW_AT))
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, []), flush=True)
    print("DONE", flush=True)

"""The Crystal Snail (Uncommon, Crystals; Bloomwood Egg): "It takes a hundred years to cross a valley and leaves a road of crystal behind it."

A glossy jade snail: a soft wet body pebbled with fine tubercles, its neck lifted, a pale gliding foot. On its back a coiled shell of pearly aquamarine, banded along its growth, with clusters of geode crystal growing out of it; the tallest crystal
in each cluster glows. Its face is like no other pet's: two eyes on long stalks, no lids at all. Like a real snail it blinks by drawing a stalk in, and what it feels shows in how it leans, droops and waves them; a small smile below.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/crystal_snail.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, the sole on z = 0. The maps go to assets/pets/BloomwoodEgg/.

What touches what: the shell's mouth is sunk into the body's back; the crystals are sunk into the shell; the stalks are sunk into the head, each eye onto its stalk's tip.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "CrystalSnail"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BloomwoodEgg")

# ---------- colours ----------
JADE, MINT, SEA, FOOT = rgb(104, 196, 164), rgb(176, 236, 210), rgb(56, 140, 126), rgb(222, 246, 236)
PEARL, AQUA, TEAL, DEEP = rgb(214, 246, 236), rgb(120, 222, 206), rgb(52, 162, 158), rgb(26, 92, 104)
ICE, BEAD, LIP = rgb(236, 255, 250), rgb(14, 22, 26), rgb(36, 96, 90)

# ---------- the frame of it ----------
SPINE = catmull([V(0, 0.5, 0.035), V(0, 0.32, 0.06), V(0, 0.1, 0.078), V(0, -0.12, 0.085), V(0, -0.27, 0.12), V(0, -0.37, 0.185), V(0, -0.42, 0.235)], 10)
P_W = ((0, 0.016), (0.12, 0.055), (0.35, 0.11), (0.55, 0.122), (0.72, 0.1), (0.86, 0.09), (1, 0.074))
P_T = ((0, 0.014), (0.12, 0.034), (0.35, 0.066), (0.55, 0.08), (0.72, 0.078), (0.86, 0.082), (1, 0.074))
P_B = ((0, 0.022), (0.12, 0.047), (0.35, 0.07), (0.55, 0.078), (0.72, 0.08), (0.86, 0.076), (1, 0.07))
SHELL_C = V(0, 0.1, 0.3)
SHELL_WIDE = 1.3          # the coil spread side to side, so from in front it is a round shell and not a disc
R_START, R_END, TURNS = 0.012, 0.122, 2.5
ALPHA_END = math.radians(-100)          # the shell's mouth faces down and a little forward, into the body's back
SPIRE = 0.1                            # how far the coil's early turns stand out to one side
STALKS = {s: [V(s * 0.03, -0.39, 0.245), V(s * 0.05, -0.43, 0.33), V(s * 0.07, -0.465, 0.42), V(s * 0.092, -0.495, 0.49)] for s in (1, -1)}      # (the first point is inside the head)
EYE_R = 0.027
HEAD_C, HEAD_R = V(0, -0.385, 0.205), (0.088, 0.085, 0.082)


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def hash_of(k):
    return math.sin(k * 12.9898) * 43758.5453 % 1.0


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


# ---------- the body: one loft, flat-soled, its front lifted ----------
def body_rings(nt, rows):
    out = []
    n = len(SPINE)
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    for i in range(rows):
        f = i / (rows - 1)
        k = f * (n - 1)
        j = min(int(k), n - 2)
        p = SPINE[j].lerp(SPINE[j + 1], k - j)
        tan = (SPINE[j + 1] - SPINE[j]).normalized()
        up = (V(0, 0, 1) - tan * tan.z).normalized()
        end = math.sqrt(max(0.0, 1 - ((f - 0.84) / 0.16) ** 2)) if f > 0.84 else 1.0
        w, t, b = prof(P_W, f) * end, prof(P_T, f) * end, prof(P_B, f) * end
        x = w * np.sign(cs) * np.abs(cs) ** 0.75
        y = np.where(sn > 0, t * np.abs(sn) ** 0.85, -b * np.abs(sn) ** 0.3)      # a flat sole
        out.append(np.array(tuple(p))[None, :] + x[:, None] * np.array((1.0, 0, 0)) + y[:, None] * np.array(tuple(up)))
    return out


def build_body(name, coll):
    rings = body_rings(72, 120)
    o = rings_mesh(name + "Loft", coll, tuple(SPINE[0] + V(0, 0.01, 0)), rings, tuple(SPINE[-1] + (SPINE[-1] - SPINE[-2]).normalized() * 0.004))
    # the head: a round dome on the front, so the face is soft and the stalks rise from its top
    m = Mesh()
    m.bm.from_mesh(o.data)
    bpy.data.objects.remove(o, do_unlink=True)
    m.ball(HEAD_C, HEAD_R, 40, 28)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.004, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    # the mouth: a small smile cut under the front of the head
    P = verts(o)
    Nn = normals(o)
    smile = mouth_field(P)
    set_verts(o, P - Nn * (0.0022 * smile)[:, None])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def mouth_field(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    line = 0.17 + 2.6 * x ** 2      # a small smile: its corners turn up
    return np.exp(-((z - line) / 0.0035) ** 2) * (np.abs(x) < 0.03) * (y < -0.44)


# ---------- the shell: a logarithmic coil, its turns overlapping into one shell ----------
def coil(samples):
    k = math.log(R_END / R_START) / (TURNS * TAU)
    th_max = TURNS * TAU
    out = []
    for i in range(samples + 1):
        th = th_max * i / samples
        R = R_START * math.exp(k * th)
        alpha = ALPHA_END - (th_max - th)
        x = SPIRE * (1 - th / th_max) ** 1.6 - 0.03      # a real snail's coil: its early turns rise into a spire on one side; the other side keeps only a small hollow
        out.append((V(x, SHELL_C.y + R * math.cos(alpha), SHELL_C.z + R * math.sin(alpha)), R, th / th_max, alpha))
    return out


def tube_radius(R):
    return 0.8 * R + 0.004


def build_shell(name, coll):
    pts = coil(420)
    m = Mesh()
    m.tube([p for p, *_ in pts], lambda f: tube_radius(pts[min(len(pts) - 1, int(round(f * (len(pts) - 1))))][1]), sides=40)
    m.ball(SHELL_C + V(0.012, 0, 0), (0.036, 0.05, 0.05), 24, 16)      # (the hollow on the flat side, made shallow: left deep it reads as a dark pit; filled out round, as an eye)
    o = m.finish(name, coll)
    P = verts(o)
    P[:, 0] = P[:, 0] * SHELL_WIDE
    set_verts(o, P)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0035, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def shell_coords(P):
    """Per point: how far along the coil (0 apex, 1 mouth) the nearest part of it is, and the angle round that part of the tube (0 straight out from the coil's centre, positive toward +X)."""
    pts = coil(420)
    path = [p for p, *_ in pts]
    Q = P.copy()
    Q[:, 0] = Q[:, 0] / SHELL_WIDE
    f, _ = nearest_on(path, Q)
    idx = np.clip(np.round(f * (len(pts) - 1)).astype(int), 0, len(pts) - 1)
    centres = np.array([tuple(pts[i][0]) for i in idx])
    alphas = np.array([pts[i][3] for i in idx])
    radial = np.column_stack((np.zeros(len(P)), np.cos(alphas), np.sin(alphas)))
    d = Q - centres
    phi = np.arctan2(d[:, 0], (d * radial).sum(1))
    return f, phi


SHELL_TREE = {}


def shell_surface(alpha, side=0.0):
    """A point on the shell's outside, found by a ray from inside it at an angle round the coil (0 points back, 90 up), leaning toward +X by side; and the surface's normal there."""
    if "tree" in SHELL_TREE:
        d = V(math.sin(side * 0.9), math.cos(alpha) * math.cos(side * 0.9), math.sin(alpha) * math.cos(side * 0.9)).normalized()
        hit, nrm, _, _ = SHELL_TREE["tree"].ray_cast(SHELL_C + d * 0.45, -d, 0.6)
        if hit is not None:
            return hit, (nrm + d).normalized()
    return old_shell_surface(alpha, side)


def old_shell_surface(alpha, side=0.0):
    """A point on the shell's outer turn at an angle round the coil (0 points back, 90 up), and the way out of it; side moves it across the tube toward +X (1 = all the way)."""
    pts = coil(420)
    best = min(pts[int(len(pts) * 0.55):], key=lambda q: abs(((q[3] - alpha) + math.pi) % TAU - math.pi))
    p, R, f, a = best
    rho = tube_radius(R)
    out = V(0, math.cos(a), math.sin(a))
    n = (out * math.cos(side * 1.2) + V(1, 0, 0) * math.sin(side * 1.2)).normalized()
    return p + n * rho, n


# ---------- crystals: hexagonal prisms with pointed tips, in clusters ----------
CLUSTERS = ((math.radians(72), 0.1, 6, 0), (math.radians(118), 0.35, 5, 1), (math.radians(28), -0.25, 5, 2), (math.radians(70), -0.95, 4, 3))


def cluster_crystals():
    """Each crystal: base point, axis, length, radius; the first in each cluster the tallest, the one that glows."""
    out = []
    for alpha, side, count, seed in CLUSTERS:
        base, n = shell_surface(alpha, side)
        t1 = n.orthogonal().normalized()
        t2 = n.cross(t1).normalized()
        for k in range(count):
            h = hash_of(seed * 31 + k * 7 + 1)
            g = hash_of(seed * 17 + k * 13 + 5)
            if k == 0:
                off, axis, length, radius = V(0, 0, 0), n, 0.15 if seed != 3 else 0.11, 0.024
            else:
                a = TAU * (k / (count - 1)) + seed
                off = (t1 * math.cos(a) + t2 * math.sin(a)) * (0.026 + 0.012 * h)
                axis = (n + (t1 * math.cos(a) + t2 * math.sin(a)) * (0.45 + 0.35 * g)).normalized()
                length, radius = 0.05 + 0.06 * h, 0.012 + 0.008 * g
            out.append((base + off - axis * 0.025, axis, length, radius, k == 0, seed * 10 + k))
    return out


def crystal(m, base, axis, length, radius, twist, rows=1):
    """A hex prism with a six-sided point. Built in rings, so paint can run along it."""
    bm = m.bm
    t1 = axis.orthogonal().normalized()
    t2 = axis.cross(t1).normalized()
    rings = []
    body = length * 0.72
    for i in range(rows + 1):
        g = i / rows
        c = base + axis * body * g
        rings.append([bm.verts.new(c + (t1 * math.cos(TAU * j / 6 + twist) + t2 * math.sin(TAU * j / 6 + twist)) * radius) for j in range(6)])
    tip = bm.verts.new(base + axis * length)
    bottom = bm.verts.new(base - axis * 0.002)
    for i in range(rows):
        for j in range(6):
            j2 = (j + 1) % 6
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    for j in range(6):
        j2 = (j + 1) % 6
        bm.faces.new((rings[-1][j], rings[-1][j2], tip))
        bm.faces.new((rings[0][j2], rings[0][j], bottom))


def build_crystals(name, coll, rows, glow=False):
    m = Mesh()
    which = []
    for base, axis, length, radius, tallest, k in cluster_crystals():
        if tallest != glow:
            continue
        before = len(m.bm.verts)
        crystal(m, base, axis, length, radius, hash_of(k) * 1.0, rows)
        which += [(k, base, axis, length)] * (len(m.bm.verts) - before)
    o = m.finish(name, coll, smooth_shade=False)
    return o, which


# ---------- eyes on stalks, and the feelers ----------
def stalk_path(side, per=8):
    return catmull(STALKS[side], per)


def stalk_radius(f):
    return 0.017 - 0.006 * f


def eye_at(side):
    return STALKS[side][-1] + (STALKS[side][-1] - STALKS[side][-2]).normalized() * 0.012


def build_tubes(name, coll, paths, rfn, sides, per):
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = catmull(paths[side], per)
        n = len(path)
        m.tube(path, rfn, sides=sides)
        meta += [(tag, i / (n - 1)) for i in range(n) for _ in range(sides)]
    o = m.finish(name, coll)
    return o, meta


def build_eyes(name, coll, seg, rings):
    m = Mesh()
    for side in (1, -1):
        m.ball(eye_at(side), (EYE_R, EYE_R, EYE_R), seg, rings)
    return m.finish(name, coll)


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_body(N + "SkinHi", HI)
    pieces["Shell"] = build_shell(N + "ShellHi", HI)
    SHELL_TREE["tree"] = tree_of(pieces["Shell"])
    for key in ("Skin", "Shell"):
        data[key + "Base"] = bpy.data.objects.new(N + key + "Base", pieces[key].data.copy())
        HI.objects.link(data[key + "Base"])
        data[key + "Base"].hide_render = True
    pieces["Crystals"], data["crystal_meta"] = build_crystals(N + "CrystalsHi", HI, 10)
    pieces["Stalks"], _ = build_tubes(N + "StalksHi", HI, STALKS, stalk_radius, 20, 10)
    pieces["Eyes"] = build_eyes(N + "EyesHi", HI, 48, 32)
    glow, _ = build_crystals(N + "Gems_Glow_8ff5dc", HI, 1, glow=True)
    if not clay:
        paint_all(pieces, data)
    return pieces, {"Gems": glow}, data


def worley2(P, f, seed=0):
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


def paint_skin(o):
    """Wet jade: darker along the back, paler down the sides, a pale sole; fine tubercles, their grooves darker; a darker keel down the neck; the smile."""
    P = verts(o)
    Nn = normals(o)
    f, d = nearest_on(SPINE, P)
    d1, d2 = worley2(P, 85.0, 3)
    groove = 1 - smooth(0.0, 0.12, d2 - d1)
    top = smooth(-0.1, 0.8, Nn[:, 2])
    col = mix(MINT, JADE, top * 0.8)
    col = mix(col, SEA, smooth(0.6, 0.95, Nn[:, 2]) * 0.45)
    col = mix(col, SEA * 0.8, groove * 0.4)
    sole = smooth(-0.3, -0.7, Nn[:, 2])
    col = mix(col, FOOT, sole)
    col = mix(col, FOOT * 0.9, sole * (0.5 + 0.5 * np.sin(P[:, 1] * 140)) * 0.2)      # the faint bands of its gliding foot
    keel = np.exp(-(P[:, 0] / 0.012) ** 2) * smooth(0.6, 0.85, f) * smooth(0.5, 0.9, Nn[:, 2])
    col = mix(col, SEA, keel * 0.6)
    col = mix(col, LIP, np.clip(mouth_field(P) * 1.3, 0, 1))
    # a soft blush on each cheek
    for side in (1, -1):
        b = np.exp(-(np.linalg.norm((P - np.array((side * 0.06, -0.445, 0.195))) / np.array((0.022, 0.02, 0.016)), axis=1)) ** 2)
        col = mix(col, rgb(244, 168, 170), b * 0.45)
    set_verts(o, P + Nn * (0.0014 * (1 - groove) - 0.0007)[:, None] * (1 - sole)[:, None])
    paint(o, col, 0.24 + 0.12 * groove + 0.3 * sole)


def paint_shell(o):
    """Pearly aquamarine, banded along its growth: deeper toward the coil's centre, two spiral bands round each turn, fine growth lines, a pale lip at the mouth."""
    P = verts(o)
    Nn = normals(o)
    f, phi = shell_coords(P)
    growth = 0.5 + 0.5 * np.sin(f * 260 + 2 * np.sin(f * 37))
    col = mix(mix(DEEP, TEAL, 0.55), TEAL, smooth(0.0, 0.45, f))
    col = mix(col, AQUA, smooth(0.35, 0.85, f))
    col = mix(col, PEARL, smooth(0.6, 0.98, f) * 0.45 * smooth(0.0, 0.8, np.cos(phi)))
    band = np.exp(-((np.abs(phi) - 0.62) / 0.1) ** 2)
    col = mix(col, DEEP, band * 0.55 * smooth(0.15, 0.4, f))
    col = col * (0.9 + 0.1 * growth)[:, None]
    lip = smooth(0.985, 1.0, f)
    col = mix(col, ICE, lip * 0.8)
    sheen = smooth(0.6, 1.0, (Nn @ np.array((0.4, -0.3, 0.86))))
    col = mix(col, ICE, sheen * 0.25)
    set_verts(o, P + Nn * (0.0012 * (growth - 0.5))[:, None])
    paint(o, col, 0.18 + 0.1 * (1 - growth))


def paint_crystals(o, meta):
    """Each crystal clouded deep teal at its root, clearing to ice at its point; each face its own brightness, so the facets read."""
    P = verts(o)
    Nn = normals(o)
    g = np.zeros(len(P))
    for i, (k, base, axis, length) in enumerate(meta):
        g[i] = (P[i] - np.array(tuple(base))) @ np.array(tuple(axis)) / length
    col = mix(TEAL, AQUA, smooth(0.0, 0.5, g))
    col = mix(col, ICE, smooth(0.45, 0.95, g))
    face = 0.5 + 0.5 * (Nn @ np.array((0.3, -0.5, 0.8)))
    col = col * (0.78 + 0.32 * face)[:, None]
    paint(o, col, 0.12)


def paint_all(pieces, data):
    paint_skin(pieces["Skin"])
    paint_shell(pieces["Shell"])
    paint_crystals(pieces["Crystals"], data["crystal_meta"])
    for key in ("Stalks",):
        P = verts(pieces[key])
        Nn = normals(pieces[key])
        fine = fbm(P, 160.0, 2, 3)
        tip = smooth(0.3, 0.52, P[:, 2])
        col = mix(mix(JADE, MINT, smooth(-0.3, 0.6, Nn[:, 2] * -1 + 0.3)), SEA, tip * 0.6)
        paint(pieces[key], col * (0.92 + 0.08 * fine)[:, None], 0.3)
    P = verts(pieces["Eyes"])
    Nn = normals(pieces["Eyes"])
    col = np.tile(BEAD, (len(P), 1))
    col = mix(col, rgb(40, 110, 104), smooth(0.2, 0.95, Nn @ np.array((0, 0.2, -0.6))) * 0.35)
    paint(pieces["Eyes"], col, 0.05)


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (0.4, 0.95, 0.85, 1)
        g.inputs["Emission Strength"].default_value = 1.6
        o.data.materials.append(m)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.0, 0.22)
FACE_AT = (0, -0.43, 0.3)
EXTRA = [(0, -1, 0.05, 0.85, FACE_AT), (0.62, -0.78, 0.12, 0.85, FACE_AT), (1, -0.05, 0.05, 0.95, FACE_AT), (0.3, -0.85, 0.45, 0.95, FACE_AT), (0.35, -0.92, 0.1, 0.4, (0.06, -0.47, 0.4)), (0.8, 0.3, 0.6, 1.4, (0, 0.1, 0.35)), (-0.9, 0.2, 0.3, 1.4, (0, 0.1, 0.3))]


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
        mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Shell": 1.25, "Crystals": 1.8, "Stalks": 1.4, "Eyes": 1.6}
META = {}


def build_low(data):
    skin = decimated(data["SkinBase"], N + "SkinLow", 2400)
    shell = decimated(data["ShellBase"], N + "ShellLow", 1700)
    for o in (skin, shell):
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    print("SKIN decimated gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), "SHELL gap", round(surface_gap(shell, tree_of(data["ShellBase"])), 4), flush=True)
    lows = {"Skin": skin, "Shell": shell}
    lows["Crystals"], _ = build_crystals(N + "CrystalsLow", GAME, 1)
    lows["Stalks"], META["Stalks"] = build_tubes(N + "StalksLow", GAME, STALKS, stalk_radius, 8, 2)
    lows["Eyes"] = build_eyes(N + "EyesLow", GAME, 12, 8)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
SPINE_BONES = ("TailTip", "Tail2", "Tail1", "Body", "Front", "Head")
SPINE_F = (0.03, 0.12, 0.27, 0.45, 0.68, 0.87)
STALK_F = (0.06, 0.55, 0.97)


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def stalk_axis(side):
    return (STALKS[side][-1] - STALKS[side][0]).normalized()


def stalk_length(side):
    path = stalk_path(side, 10)
    return sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", path_at(SPINE, SPINE_F[3]), "Root")]
    bones += [("Tail1", path_at(SPINE, SPINE_F[2]), "Body"), ("Tail2", path_at(SPINE, SPINE_F[1]), "Tail1"), ("TailTip", path_at(SPINE, SPINE_F[0]), "Tail2")]
    bones += [("Front", path_at(SPINE, SPINE_F[4]), "Body"), ("Head", HEAD_C.copy(), "Front"), ("Shell", SHELL_C.copy(), "Body")]
    for side, tag in ((1, "L"), (-1, "R")):
        path = stalk_path(side, 10)
        bones += [("Stalk" + tag + "1", path_at(path, STALK_F[0]), "Head"), ("Stalk" + tag + "2", path_at(path, STALK_F[1]), "Stalk" + tag + "1"), ("Stalk" + tag + "3", eye_at(side), "Stalk" + tag + "2")]
    return armature(bones)


def bind_all(lows, rig, glows):
    f, _ = nearest_on(SPINE, verts(lows["Skin"]))
    weigh(lows["Skin"], [chain_weight(SPINE_BONES, SPINE_F, float(x)) for x in f])
    for key in ("Shell", "Crystals"):
        rigid(lows[key], "Shell")
    rigid(glows["Gems"], "Shell")
    weigh(lows["Stalks"], [chain_weight(("Stalk%s1" % t, "Stalk%s2" % t, "Stalk%s3" % t), STALK_F, f) for t, f in META["Stalks"]])
    weigh(lows["Eyes"], [{"StalkL3" if p[0] > 0 else "StalkR3": 1.0} for p in verts(lows["Eyes"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateCrystalSnail uses. +X: what points forward lifts (a head), what points back drops (a tail)
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def retract(k, tags=("L", "R")):
    """Each stalk drawn in by k of its length's 55%: half at its middle, the rest at its tip, along the stalk."""
    out = {}
    for side, tag in ((1, "L"), (-1, "R")):
        if tag not in tags:
            continue
        a = stalk_axis(side) * (-k * 0.55 * stalk_length(side) * 0.5)
        out["Stalk%s2" % tag] = ((0, 0, 1), 0, tuple(a))
        out["Stalk%s3" % tag] = ((0, 0, 1), 0, tuple(a))
    return out


def pose_library():
    return {
        "Retract": retract(1.0), "BlinkL": retract(0.7, ("L",)),
        "Withdraw": {**retract(1.0), "Front": game_turn(-0.15, 0, 0, (0, 0.08, -0.025)), "Head": game_turn(-0.35, 0, 0)},
        "Stretch": {"Front": game_turn(0.06, 0, 0, (0, -0.045, 0.01)), "Head": game_turn(0.12, 0, 0), "Tail1": game_turn(0.04, 0, 0)},
        "StalksBack": {"StalkL1": game_turn(0.5, 0, 0), "StalkR1": game_turn(0.5, 0, 0)},
        "StalksForward": {"StalkL1": game_turn(-0.45, 0, 0), "StalkR1": game_turn(-0.45, 0, 0)},
        "Cross": {"StalkL1": game_turn(0, 0, 0.35), "StalkR1": game_turn(0, 0, -0.35), "StalkL2": game_turn(0, 0, 0.3), "StalkR2": game_turn(0, 0, -0.3)},
        "Fly": {"Tail1": game_turn(-0.35, 0, 0), "Tail2": game_turn(-0.45, 0, 0), "Front": game_turn(0.15, 0, 0), "StalkL1": game_turn(0.5, 0, 0), "StalkR1": game_turn(0.5, 0, 0)},
        "Turn": {"Front": game_turn(0, 0.35, 0), "Head": game_turn(0.05, 0.3, 0.15)},
    }


if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(data)
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=62, texels=TEXELS, margin=0.006)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.4, 0.75, 0.66, 1), far=("Skin", "Shell"), reach=(0.008, 0.02), far_reach=(0.012, 0.035),
             reaches={"Crystals": (0.004, 0.01), "Eyes": (0.005, 0.012), "Stalks": (0.006, 0.015)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [ (body.matrix_world @ v.co).z for v in body.data.vertices]
    print("SOLE metres from the box middle", round((max(zs) - min(zs)) / 2 - (0 - min(zs)) * 0 , 4), "min z", round(min(zs), 4), "max z", round(max(zs), 4), flush=True)
    for side, tag in ((1, "L"), (-1, "R")):
        a = stalk_axis(side)
        print("STALK", tag, "axis in the game's axes", (round(-a.x, 4), round(a.z, 4), round(a.y, 4)), "length", round(stalk_length(side), 4), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.6, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.3, -0.92, 0.2, 0.95, FACE_AT)
    side_v = (1, -0.15, 0.15, 1.6, (0, -0.1, 0.25))
    for name, view in (("Retract", close), ("BlinkL", close), ("Withdraw", side_v), ("Stretch", side_v), ("StalksBack", side_v), ("StalksForward", side_v), ("Cross", close), ("Fly", side_v), ("Turn", (0.5, -0.85, 0.3, 1.6, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 2.6, VIEW_AT))
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

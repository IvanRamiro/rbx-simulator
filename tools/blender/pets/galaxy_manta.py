"""The Galaxy Manta (Mythical, Cosmic energy; Astral Sanctum Egg): "It glides through open space with a slow spiral of stars turning under its wings."

A new creature. A great ray whose back is deep space: a nebula spiralling out from between its shoulders across both wings, gold constellations and gold edging
on it. Pale pearl beneath and along the lip. A true manta's head, flat and broad: small deep eyes on its sides, each with a thin ring of gold and violet, a wide calm mouth at the
very front, a star on its brow. Its horn fins curl into little spirals, its whip tail ends in a comet. Under its wings, as the lore says, a small galaxy really turns, its arms winding, and a ringed planet and a moon go round in it.
One smooth skin on bones: waves run out along the wings and back across them, and it can barrel-roll.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/galaxy_manta.py -- [paint|all] [review dir]

paint: builds and paints the high-detail model and renders it. all: also makes the game mesh, bakes, rigs and writes the file and the FBX.
Faces -Y, Z up. The maps go to assets/pets/AstralSanctumEgg/.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "GalaxyManta"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AstralSanctumEgg")

# ---------- colours ----------
VOID, INDIGO, VIOLET, MAGENTA, CYAN = rgb(13, 10, 44), rgb(36, 28, 108), rgb(96, 52, 196), rgb(216, 72, 178), rgb(52, 168, 214)
GOLD, PALE_GOLD, PEARL, LAVENDER, ROSE = rgb(240, 186, 92), rgb(255, 226, 160), rgb(236, 230, 250), rgb(176, 156, 232), rgb(176, 104, 176)
STAR = rgb(235, 232, 255)

# ---------- the shape in plan: half-span against the front and rear edges ----------
SPAN = 1.12
FRONT = catmull([V(0, -0.40, 0), V(0.16, -0.40, 0), V(0.26, -0.40, 0), V(0.345, -0.38, 0), V(0.50, -0.24, 0), V(0.72, -0.04, 0), V(0.92, 0.12, 0), V(1.05, 0.25, 0), V(SPAN, 0.345, 0)], 12)
REAR = catmull([V(0, 0.46, 0), V(0.10, 0.45, 0), V(0.22, 0.38, 0), V(0.40, 0.30, 0), V(0.62, 0.27, 0), V(0.84, 0.28, 0), V(1.0, 0.31, 0), V(SPAN, 0.355, 0)], 12)
_FX, _FY = np.array([p.x for p in FRONT]), np.array([p.y for p in FRONT])
_RX, _RY = np.array([p.x for p in REAR]), np.array([p.y for p in REAR])


def front_y(a):
    return np.interp(a, _FX, _FY)


def rear_y(a):
    return np.interp(a, _RX, _RY)


def mid_z(a, c):
    """The middle of the wing: a gull's curve, down then lifting to the tip, its rear edge drooping a little."""
    return -0.075 * smooth(0.18, 0.62, a) + 0.13 * smooth(0.55, SPAN, a) ** 1.6 - 0.03 * c * a / SPAN


def half_thick(a, c, top):
    edge = np.clip(4 * c * (1 - c), 0, 1) ** 0.55
    wing = (0.05 * np.clip(1 - a / SPAN, 0, 1) ** 0.85 + 0.011) * (1 - smooth(SPAN - 0.03, SPAN, a))
    bulge = np.exp(-(a / 0.27) ** 2) * np.sin(np.pi * np.clip(c, 0, 1) ** 0.85) ** 0.75
    return edge * (wing + bulge * (0.17 if top else 0.115))


def sheet_point(x, c, top):
    a = np.abs(x)
    y = front_y(a) + (rear_y(a) - front_y(a)) * c
    return x, y, mid_z(a, c) + (half_thick(a, c, True) if top else -half_thick(a, c, False))


def chord_of(x, y):
    a = np.abs(x)
    return a, np.clip((y - front_y(a)) / np.maximum(rear_y(a) - front_y(a), 1e-4), 0, 1)


# ---------- paths ----------
EYE_R = 0.046
EYE_C = V(0.322, -0.395, 0.02)
EYE_AXIS = V(0.86, -0.45, 0.24).normalized()
TAIL = catmull([V(0, 0.34, 0.0), V(0, 0.52, 0.015), V(0.0, 0.78, 0.05), V(0.035, 1.02, 0.09), V(-0.03, 1.24, 0.15), V(0.018, 1.42, 0.22), V(0.03, 1.56, 0.30)], 8)
SPIRAL_C = V(0, 0.04, -0.38)
SPIRAL_R = 1.30


def tail_radius(s):
    return 0.012 + 0.052 * (1 - s) ** 1.5


def ceph_path(side):
    """A horn fin: forward from beside the mouth, up, and round on itself in a little spiral."""
    return catmull([mir(p, side) for p in (V(0.225, -0.40, 0.0), V(0.28, -0.555, -0.012), V(0.325, -0.665, 0.015), V(0.348, -0.745, 0.075), V(0.322, -0.79, 0.14), V(0.272, -0.772, 0.168), V(0.248, -0.722, 0.145), V(0.272, -0.698, 0.118))], 7)


HORN_FLAT = 0.36      # flat paddles, as a real manta's are, not round tubes


def ceph_radius(f):
    return 0.008 + 0.074 * (1 - f) ** 1.15


DORSAL = catmull([V(0, 0.30, 0.09), V(0, 0.40, 0.10), V(0, 0.47, 0.135), V(0, 0.50, 0.17)], 5)


# ---------- the skin ----------
def build_sheet(name, coll, nu=520, nv=220):
    xs = np.linspace(-SPAN, SPAN, nu + 1)
    cs = (1 - np.cos(np.linspace(0, np.pi, nv + 1))) / 2      # closer together at the edges, where it turns over
    X, C = np.meshgrid(xs, cs, indexing="ij")
    pts = []
    for top in (True, False):
        x, y, z = sheet_point(X, C, top)
        pts.append(np.stack((x, y, z), -1).reshape(-1, 3))
    co = np.concatenate(pts)
    row = (nu + 1) * (nv + 1)
    idx = np.arange(row).reshape(nu + 1, nv + 1)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    faces = np.concatenate((np.stack((a, b, c, d), 1), np.stack((d, c, b, a), 1) + row))
    me = bpy.data.meshes.new(name)
    me.from_pydata(co.tolist(), [], faces.tolist())
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def build_core():
    core = Mesh()
    core.ball(V(0, -0.05, 0.02), (0.30, 0.50, 0.165))
    core.ball(V(0, -0.28, 0.025), (0.30, 0.24, 0.105))         # the head, low and flat
    core.ball(V(0, -0.445, -0.03), (0.262, 0.115, 0.058))      # the broad front of it, with the mouth
    core.ball(V(0, 0.36, 0.0), (0.085, 0.17, 0.06))            # the root of the tail
    for side in (1, -1):
        core.ball(V(side * 0.26, -0.02, -0.004), (0.2, 0.22, 0.042))     # the shoulder, sunk into the wing so no edge of it shows
        core.ball(V(side * 0.27, -0.30, 0.0), (0.095, 0.17, 0.066))   # the side of the head, carrying the eye
        core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.014 + V(0, 0, 0.006), (0.058, 0.058, 0.058))     # the small swell the eye sits in
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.014, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 40})])
    return c


def merged(objs, name):
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    HI.objects.link(o)
    return o


def build_skin():
    """Returns the skin, and the same without tail and horns: what the game mesh's wings settle onto."""
    core = build_core()
    sheet = build_sheet(N + "SheetHi", HI)
    body = merged((core, sheet), N + "BodyOnly")
    bpy.data.objects.remove(sheet, do_unlink=True)
    bpy.data.objects.remove(core, do_unlink=True)
    apply_mods(body, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0055, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    thin = Mesh()
    thin.tube(TAIL, tail_radius, sides=18, flat=1.0)
    for side in (1, -1):
        thin.tube(ceph_path(side), ceph_radius, sides=14, flat=HORN_FLAT, plane=V(0, 0, 1))
        thin.ball(ceph_path(side)[-1], (0.009, 0.009, 0.009), 12, 8)
    thin.tube(DORSAL, lambda f: 0.012 + 0.03 * (1 - f) ** 1.2, sides=10, flat=0.4)
    th = thin.finish(N + "ThinHi", HI)
    skin = merged((body, th), N + "SkinHi")
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(skin, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.004, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    return skin, body


# ---------- the constellations: (x, chord) on the back ----------
STAR_LINES = [
    ([(0.42, 0.30), (0.55, 0.44), (0.70, 0.40), (0.82, 0.56), (0.66, 0.68), (0.95, 0.52)], [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5)]),
    ([(0.30, 0.74), (0.42, 0.82), (0.56, 0.80)], [(0, 1), (1, 2)]),
    ([(-0.45, 0.55), (-0.58, 0.32), (-0.74, 0.44), (-0.90, 0.40), (-0.72, 0.72), (-0.58, 0.76)], [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5)]),
    ([(-0.36, 0.26), (-0.46, 0.16), (-0.33, 0.10)], [(0, 1), (1, 2)]),
    ([(-0.10, 0.70), (0.06, 0.60), (0.14, 0.74), (0.02, 0.82)], [(0, 1), (1, 2), (2, 3), (3, 0)]),
]


def star_xy(x, c):
    a = abs(x)
    y = front_y(a) + (rear_y(a) - front_y(a)) * c
    return float(x), float(y)


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    a, c = chord_of(x, y)
    top = smooth(-0.3, 0.25, Nn[:, 2])

    # the nebula, wound into a spiral about the middle of the back
    r = np.sqrt(x ** 2 + (y - 0.04) ** 2) + 1e-4
    th = np.arctan2(y - 0.04, x)
    wound = th + 1.45 * np.log(r + 0.12)
    Q = np.stack((r * np.cos(wound) * 1.6, r * np.sin(wound) * 1.6, z * 0.5), 1)
    cloud, wisp, far = fbm(Q, 5.0, 5, 3), fbm(Q + 3.1, 9.0, 5, 11), fbm(Q - 7.7, 3.0, 4, 23)
    arm = smooth(0.15, 0.95, 0.5 + 0.5 * np.cos(2 * wound + 1.2 * (cloud - 0.5) * 6))
    back = mix(VOID, INDIGO, smooth(0.32, 0.66, cloud))
    back = mix(back, VIOLET, smooth(0.36, 0.72, wisp) * (0.3 + 0.7 * arm))
    back = mix(back, MAGENTA, smooth(0.5, 0.74, wisp * (0.35 + 0.8 * arm)) * 0.9)
    back = mix(back, CYAN, smooth(0.54, 0.74, far) * smooth(0.45, 0.95, a) * 0.8)
    # the bright heart of it, between the shoulders
    heart = np.exp(-((r / 0.13) ** 2))
    back = mix(back, mix(MAGENTA, rgb(255, 176, 96), smooth(0.45, 1.0, heart)), np.clip(heart * 1.3, 0, 1) * 0.92)
    # a dust of faint stars, painted (the bright ones are glow pieces)
    cell = 0.03
    ix, iy = np.floor(x / cell).astype(np.int64), np.floor(y / cell).astype(np.int64)
    zero = np.zeros_like(ix)
    keep, jx, jy, bright = hash01(ix, iy, zero, 41), hash01(ix, iy, zero, 42), hash01(ix, iy, zero, 43), hash01(ix, iy, zero, 44)
    dx, dy = x - (ix + 0.2 + 0.6 * jx) * cell, y - (iy + 0.2 + 0.6 * jy) * cell
    dust = (keep > 0.74) * (1 - smooth(0.0026, 0.0048 + 0.0022 * bright ** 3, np.sqrt(dx ** 2 + dy ** 2)))
    back = mix(back, STAR, dust * (0.3 + 0.6 * bright))
    # the nebula thins to night over the head and toward the mouth
    calm = smooth(-0.2, -0.42, y) * (1 - smooth(0.36, 0.5, a))
    back = mix(back, mix(VOID, INDIGO, 0.5 + 0.5 * smooth(0.3, 0.7, cloud)), calm * 0.72)

    # beneath: pearl, going lavender and violet out to the tips, with its gill slits and a few dark freckles
    belly = mix(PEARL, LAVENDER, smooth(0.28, 0.85, a))
    belly = mix(belly, VIOLET, smooth(0.78, 1.1, a) * 0.8)
    for side in (1, -1):
        for k in range(5):
            gy = -0.10 + 0.062 * k
            d = np.abs(y - (gy + 0.5 * (np.abs(x) - 0.22) ** 2 * 1.2))
            slit = (1 - smooth(0.003, 0.0085, d)) * smooth(0.135, 0.15, side * x) * (1 - smooth(0.285, 0.30, side * x))
            belly = mix(belly, ROSE, slit * 0.85)
    fx = np.floor(x / 0.09).astype(np.int64)
    fy = np.floor(y / 0.09).astype(np.int64)
    fzero = np.zeros_like(fx)
    fk, fa, fb = hash01(fx, fy, fzero, 51), hash01(fx, fy, fzero, 52), hash01(fx, fy, fzero, 53)
    fd = np.sqrt((x - (fx + 0.3 + 0.4 * fa) * 0.09) ** 2 + (y - (fy + 0.3 + 0.4 * fb) * 0.09) ** 2)
    belly = mix(belly, mix(LAVENDER, INDIGO, 0.3), (fk > 0.8) * (1 - smooth(0.004, 0.009, fd)) * smooth(0.0, 0.2, y + 0.05) * 0.55)
    col = mix(belly, back, top)

    # the lip, pearl like the belly, a clean line across the front of the head
    lip_edge = -0.008 + 0.12 * np.abs(x) ** 2
    lip = smooth(0.009, -0.009, z - lip_edge) * smooth(-0.40, -0.47, y) * (1 - smooth(0.23, 0.29, a))
    col = mix(col, PEARL, lip)
    # the gold: along the front edge and fading out toward the head, a finer line behind it; the rear edge lit violet
    d_front = (y - front_y(a)) / 1.23      # roughly across the edge, not along Y: it runs at about 36 degrees
    outward = smooth(0.37, 0.47, a) * top * (d_front > -0.012)     # (nothing ahead of the wing's edge: the horns and cheeks aren't wing)
    edge_gold = (1 - smooth(0.013, 0.02, d_front)) * outward
    fine = (1 - smooth(0.0028, 0.0058, np.abs(d_front - 0.042))) * outward * (1 - smooth(0.9, 1.08, a))
    rim = (1 - smooth(0.012, 0.026, rear_y(a) - y)) * top
    col = mix(col, mix(LAVENDER, VIOLET, 0.3), rim * smooth(0.14, 0.3, a))
    # the constellations' lines
    lines = np.full_like(x, 1e9)
    for nodes, edges in STAR_LINES:
        pts = [star_xy(*n) for n in nodes]
        for i, j in edges:
            ax, ay = pts[i]
            bx, by = pts[j]
            abx, aby = bx - ax, by - ay
            t = np.clip(((x - ax) * abx + (y - ay) * aby) / (abx ** 2 + aby ** 2), 0, 1)
            lines = np.minimum(lines, np.sqrt((x - ax - abx * t) ** 2 + (y - ay - aby * t) ** 2))
    line_gold = (1 - smooth(0.0035, 0.0068, lines)) * top
    gold_mask = np.maximum(np.maximum(edge_gold, fine * 0.85), line_gold * 0.9)
    # the star on its brow
    bx, by = x, y + 0.33
    br = np.sqrt(bx ** 2 + by ** 2)
    reach = 0.007 + 0.03 * np.abs(np.cos(2 * np.arctan2(by, bx))) ** 7
    gold_mask = np.maximum(gold_mask, (1 - smooth(reach - 0.002, reach + 0.002, br)) * top)

    # tail and horn fins
    s_t, d_t = nearest_on(TAIL, P)
    tail = 1 - smooth(tail_radius(np.clip(s_t, 0, 1)) + 0.012, tail_radius(np.clip(s_t, 0, 1)) + 0.03, d_t)
    tail = tail * smooth(0.40, 0.5, y) * (1 - (a > 0.3))
    tail_col = mix(INDIGO, VIOLET, smooth(0.15, 0.8, s_t))
    tail_col = mix(tail_col, MAGENTA, smooth(0.45, 0.72, fbm(P, 11.0, 3, 61)) * 0.7)
    col = mix(col, tail_col, tail)
    bands = (np.sin(s_t * 44) > 0.86) * smooth(0.5, 0.62, s_t)
    gold_mask = np.maximum(gold_mask, bands * tail)
    horn = np.zeros_like(x)
    for side in (1, -1):
        f, d = nearest_on(ceph_path(side), P)
        here = (1 - smooth(0.085, 0.1, d)) * smooth(-0.36, -0.44, y)
        horn_col = mix(mix(VOID, INDIGO, 0.8), mix(VIOLET, MAGENTA, 0.6), smooth(0.3, 0.75, f))
        col = mix(col, horn_col, here)
        gold_mask = np.maximum(gold_mask, here * smooth(0.88, 0.97, f))
        horn = np.maximum(horn, here)

    col = mix(col, GOLD, gold_mask)
    col = mix(col, PALE_GOLD, gold_mask * smooth(0.0, 0.2, noise3(P, 40.0, 3.0)) * 0.5)
    rough = 0.62 + (0.4 - 0.62) * top
    rough = rough + (0.3 - rough) * gold_mask
    rough = rough + 0.05 * (fbm(P, 30.0, 2, 71) - 0.5)
    # fine folds running out along the wing, gold standing a hair proud
    folds = np.sin(c * 95 + a * 6) * 0.5 * smooth(0.3, 0.6, a) * (1 - smooth(0.9, 1.1, a))
    set_verts(o, P + Nn * (0.0011 * folds * top + 0.0013 * gold_mask)[:, None])
    paint(o, col, rough, gold_mask)


# ---------- eyes and face ----------
def eye_paint(o, fr):
    """A real animal's eye: almost all dark and deep, a thin ring of gold fading to violet round the pupil, an old thing looking at you."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.sqrt(px ** 2 + py ** 2), 3.0)
    col = np.broadcast_to(rgb(8, 6, 26), (len(px), 3)).copy()
    ring = mix(rgb(250, 196, 104), rgb(112, 62, 214), smooth(0.34, 0.6, r))
    col = mix(col, ring, smooth(0.28, 0.33, r) * (1 - smooth(0.58, 0.72, r)))
    col = mix(col, rgb(40, 28, 92), smooth(0.8, 0.98, r))      # it goes into the skin's colour at the edge
    paint(o, col, np.full(len(px), 0.08))


def face_ray(tree, x, z, lift):
    return on_surface(tree, V(x, -0.3, z), V(0, 1, 0), lift)


def build_lip_line(tree):
    """The mouth at rest: one long, calm line across the front of the head."""
    pts = [face_ray(tree, x, z, 0.003) for x, z in ((-0.205, -0.024), (-0.17, -0.031), (-0.11, -0.037), (-0.05, -0.04), (0.0, -0.041), (0.05, -0.04), (0.11, -0.037), (0.17, -0.031), (0.205, -0.024))]
    m = Mesh()
    m.tube(catmull(pts, 4), lambda f: 0.002 + 0.0036 * math.sin(math.pi * f) ** 0.5, sides=8, plane=V(0, 1, 0))
    o = m.finish(N + "SmileHi", HI)
    plain(o, rgb(24, 16, 62), 0.5)
    return o


def build_mouth(tree):
    """The open mouth, hidden in the head until it opens: a bone brings it forward."""
    c = face_ray(tree, 0.0, -0.05, -0.036)
    m = Mesh()
    m.ball(c, (0.17, 0.028, 0.032), 32, 14)
    o = m.finish(N + "MouthHi", HI)
    B = verts(o)
    rim = np.sqrt(((B[:, 0] - c.x) / 0.17) ** 2 + ((B[:, 2] - c.z) / 0.032) ** 2)
    paint(o, mix(rgb(16, 8, 46), rgb(214, 170, 226), smooth(0.74, 0.9, rim)), np.full(len(B), 0.45))
    return o, c


PLANET_AT = V(0.70, -0.42, 0.02)


def build_planets():
    """A little ringed planet and its moon, going round among the stars."""
    pc = SPIRAL_C + PLANET_AT
    m = Mesh()
    m.ball(pc, (0.058, 0.058, 0.056), 40, 24)
    planet = m.finish(N + "PlanetHi", HI)
    P = verts(planet) - np.array(tuple(pc))
    tilt = (P[:, 2] + P[:, 0] * 0.34) / 0.058
    bands = np.sin(tilt * 8 + np.sin(P[:, 1] * 30) * 0.5)
    paint(planet, mix(rgb(250, 176, 92), rgb(214, 80, 120), smooth(-0.6, 0.6, bands)), np.full(len(P), 0.45))
    m = Mesh()
    mc = SPIRAL_C + V(-0.50, 0.66, 0.05)
    m.ball(mc, (0.03, 0.03, 0.03), 24, 16)
    moon = m.finish(N + "MoonHi", HI)
    P = verts(moon)
    paint(moon, mix(rgb(220, 216, 240), rgb(150, 146, 186), smooth(0.35, 0.65, fbm(P, 60.0, 3, 91))), np.full(len(P), 0.7))
    return planet, moon, pc, mc


# ---------- the glow pieces ----------
RNG = np.random.default_rng(11)
BANDS = (0.56, 0.95)      # the galaxy's inner, middle and outer rings turn at slightly different speeds, so its arms wind and unwind
GALAXY = {"Violet": [], "Ember": [], "Stars": []}      # (centre, size, stretch angle, bone)


def spiral_stars():
    def band(r):
        return "SpiralInner" if r < BANDS[0] else ("SpiralMid" if r < BANDS[1] else "SpiralOuter")

    def add(colour, r, th, size, lift=0.0):
        GALAXY[colour].append((SPIRAL_C + V(r * math.cos(th), r * math.sin(th), lift), size, th, band(r)))
    for arm, count, spread, boost in ((0.0, 66, 0.11, 1.0), (math.pi, 66, 0.11, 1.0), (math.pi / 2, 26, 0.17, 0.75), (-math.pi / 2, 26, 0.17, 0.75)):
        for k in range(count):
            t = (k + RNG.random()) / count
            r = (0.2 + (SPIRAL_R - 0.2) * t ** 1.2) * (1 + RNG.normal(0, 0.025))
            r = min(r, SPIRAL_R)
            th = arm + math.log(r / 0.2) * 1.5 + RNG.normal(0, spread * (0.6 + 0.8 * t))
            size = boost * (0.024 - 0.011 * t) * RNG.uniform(0.6, 1.5) * (1.7 if RNG.random() > 0.93 else 1.0)
            roll = RNG.random()
            colour = "Ember" if t < 0.3 + 0.15 * roll or roll > 0.93 else ("Stars" if roll > 0.72 else "Violet")
            add(colour, r, th, size, RNG.normal(0, 0.014))
    for k in range(34):    # the bright bulge at its heart
        r = 0.21 * RNG.random() ** 0.7
        add("Ember", r, RNG.random() * TAU, RNG.uniform(0.01, 0.022), RNG.normal(0, 0.024))
    for k in range(26):    # and a thin scatter between the arms
        r = RNG.uniform(0.3, SPIRAL_R)
        add("Stars" if k % 3 == 0 else "Violet", r, RNG.random() * TAU, RNG.uniform(0.007, 0.012), RNG.normal(0, 0.02))


def octa(m, c, size, th):
    """A little solid star, longer along its orbit, so it reads from any side."""
    along = V(-math.sin(th), math.cos(th), 0)
    out = V(math.cos(th), math.sin(th), 0)
    up = V(0, 0, 1)
    pts = [c + along * size * 1.25, c - along * size * 1.25, c + out * size * 0.8, c - out * size * 0.8, c + up * size * 0.62, c - up * size * 0.62]
    vs = [m.bm.verts.new(p) for p in pts]
    for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
        m.bm.faces.new([vs[i] for i in f])


def flat_star(m, c, nrm, size, points=4, waist=0.3):
    """A star lying on the skin, facing out."""
    a = nrm.orthogonal().normalized()
    b = nrm.cross(a).normalized()
    centre = m.bm.verts.new(c + nrm * 0.0015)
    ring = []
    for k in range(points * 2):
        ang = TAU * k / (points * 2) + 0.4
        rr = size if k % 2 == 0 else size * waist
        ring.append(m.bm.verts.new(c + (a * math.cos(ang) + b * math.sin(ang)) * rr))
    for k in range(points * 2):
        m.bm.faces.new((centre, ring[k], ring[(k + 1) % (points * 2)]))


def wing_star_places(tree):
    """Where the stars on the back go: every constellation's nodes, big, and a fall of small ones."""
    big, small = [], []
    for nodes, _ in STAR_LINES:
        for x, c in nodes:
            big.append(star_xy(x, c))
    picks = 0
    while picks < 96:
        x = RNG.uniform(-1.04, 1.04)
        c = RNG.uniform(0.08, 0.92)
        px, py = star_xy(x, c)
        if abs(x) < 0.34 and py < -0.08:     # none on the face
            continue
        if RNG.random() > 0.35 + 0.65 * abs(x):     # thicker out on the wings
            continue
        small.append((px, py))
        picks += 1
    placed = []
    for place, size in [(p, RNG.uniform(0.024, 0.036)) for p in big] + [(p, RNG.uniform(0.0105, 0.017)) for p in small]:
        loc, nrm, _, _ = tree.ray_cast(V(place[0], place[1], 1.5), V(0, 0, -1), 3.0)
        if loc:
            placed.append((loc + nrm * 0.0055, nrm, size))
    return placed


def build_glows(tree, frames):
    """The Neon pieces, each one colour. Returns them, with each vertex's bone worked out at bind."""
    spiral_stars()
    glow = {}
    owners = {}

    def start_piece(key, hexa):
        m = Mesh()
        owners[key] = []
        glow[key] = (m, N + key + "_Glow_" + hexa)
        return m

    def note(key, m, before, bone):
        m.bm.verts.ensure_lookup_table()
        owners[key] += [bone] * (len(m.bm.verts) - before)

    for key, hexa in (("Violet", "8a6bff"), ("Ember", "ffc878"), ("Stars", "e6e0ff")):
        m = start_piece(key, hexa)
        for c, size, th, bone in GALAXY[key]:
            before = len(m.bm.verts)
            octa(m, c, size, th)
            note(key, m, before, bone)
    # the stars on its back ride the wing
    m = glow["Stars"][0]
    for loc, nrm, size in wing_star_places(tree):
        before = len(m.bm.verts)
        if size > 0.025:
            flat_star(m, loc, nrm, size, points=4, waist=0.26)
        else:
            flat_star(m, loc, nrm, size, points=2, waist=0.45)
        note("Stars", m, before, None)
    # the comet and the planet's ring each get a mesh of their own: Roblox's far-distance simplifying joins distant pieces of one mesh with long bars
    m = start_piece("Comet", "ffc878")
    before = 0
    tip = TAIL[-1]
    tan = (TAIL[-1] - TAIL[-3]).normalized()
    bmesh.ops.create_uvsphere(m.bm, u_segments=10, v_segments=6, radius=0.034, matrix=Matrix.Translation(tip))
    for ang in range(4):
        d = (V(0, 0, 1) * math.cos(ang * TAU / 4) + V(1, 0, 0) * math.sin(ang * TAU / 4)).normalized()
        octa_c = tip + d * 0.05
        vs = [m.bm.verts.new(octa_c + d * 0.04), m.bm.verts.new(octa_c - d * 0.03), m.bm.verts.new(octa_c + tan * 0.01), m.bm.verts.new(octa_c - tan * 0.01),
              m.bm.verts.new(octa_c + d.cross(tan) * 0.01), m.bm.verts.new(octa_c - d.cross(tan) * 0.01)]
        for f in ((0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2), (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)):
            m.bm.faces.new([vs[i] for i in f])
    note("Comet", m, before, "TailTip")
    # the planet's ring, a thread of gold
    m = start_piece("Ring", "ffc878")
    before = 0
    pc = SPIRAL_C + PLANET_AT
    q = Matrix.Rotation(math.radians(-19), 3, "Y") @ Matrix.Rotation(math.radians(12), 3, "X")
    ring = [pc + q @ V(math.cos(TAU * k / 28) * 0.098, math.sin(TAU * k / 28) * 0.098, 0) for k in range(29)]
    m.tube(ring, lambda f: 0.0115, sides=4, flat=0.3, plane=q @ V(0, 0, 1), caps=False)
    note("Ring", m, before, "Orbit")
    objs = {}
    for key, (mm, name) in glow.items():
        objs[key] = mm.finish(name, HI, smooth_shade=False)
    objs["Glints"] = glints(frames, HI, "Glints_Glow_d8d0f0", spots=((-24, 26, 0.0085, 10),))
    return objs, owners


# ---------- the whole, high-detail ----------
def build_hi():
    pieces = {}
    skin, body_only = build_skin()
    paint_skin(skin)
    pieces["Skin"] = skin
    tree = tree_of(skin)
    frames, marks = {}, {}
    no_lids = (0.0, 0.0, 0.0)
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, no_lids, no_lids, tilt=0.0)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
    pieces["Smile"] = build_lip_line(tree)
    pieces["Mouth"], marks["Mouth"] = build_mouth(tree)
    pieces["Planet"], pieces["Moon"], marks["Planet"], marks["Moon"] = build_planets()
    glows, owners = build_glows(tree_of(body_only), frames)
    return pieces, frames, marks, glows, owners, body_only


# ---------- review ----------
VIEWS = [(0, -1, 0.14), (0.62, -0.72, 0.36), (1, 0, 0.12), (0, 1, 0.25), (-0.5, 0.55, 0.7), (0, -0.02, 1), (0.25, -0.35, -0.9), (0, -1, 0.1, 2.4, (0, -0.45, 0.02)), (0.86, -0.46, 0.18, 1.5, (0.26, -0.42, 0.02)), (0.0, -0.05, 1, 3.6, (0, 0.02, 0))]
VIEW_AT = (0, 0.25, -0.06)



# ---------- the game mesh ----------
GRID_A = (0, 0.04, 0.08, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27, 0.30, 0.34, 0.38, 0.43, 0.49, 0.56, 0.64, 0.72, 0.80, 0.87, 0.94, 1.00, 1.05, 1.09, SPAN)
GRID_C = (0, 0.012, 0.03, 0.055, 0.085, 0.12, 0.16, 0.20, 0.25, 0.30, 0.36, 0.43, 0.5, 0.58, 0.66, 0.74, 0.82, 0.89, 0.95, 1.0)
PARTS = {}      # the skin's stretches of vertices, for its weights


def head_front(tree, x):
    """How far forward the head's own forms reach here: the game mesh's outline must take them in."""
    y = float(front_y(abs(x)))
    for z in (-0.06, -0.02, 0.03, 0.08, 0.13):
        hit = tree.ray_cast(V(x, -1.3, z), V(0, 1, 0), 2.0)[0]
        if hit:
            y = min(y, hit.y)
    return y


def low_skin(body_tree):
    """The wings and body as one clean grid, its rows running out along the wing so a wave bends it well, settled onto the high-detail form; tail and horns as tubes run into it."""
    m = Mesh()
    bm = m.bm
    xs = sorted({s * a for a in GRID_A for s in (1, -1)})
    nv = len(GRID_C)
    top, bot = {}, {}
    for i, x in enumerate(xs):
        a = abs(x)
        y0 = head_front(body_tree, x) if a < 0.5 else float(front_y(a))
        y1 = float(rear_y(a))
        for j, c in enumerate(GRID_C):
            y = y0 + (y1 - y0) * c
            edge = j in (0, nv - 1) or i in (0, len(xs) - 1)
            base = float(mid_z(a, c))
            if edge:
                z = base
                if j == 0 and a < 0.5:     # the head's nose: where the forward ray landed
                    best = None
                    for zz in (-0.06, -0.04, -0.02, 0.0):
                        hit = body_tree.ray_cast(V(x, -1.3, zz), V(0, 1, 0), 2.0)[0]
                        if hit and (best is None or hit.y < best.y):
                            best = hit
                    z = best.z if best else base
                v = bm.verts.new((x, y, z))
                top[i, j] = bot[i, j] = v
                continue
            hit_t = body_tree.ray_cast(V(x, y, 2.0), V(0, 0, -1), 4.0)[0]
            hit_b = body_tree.ray_cast(V(x, y, -2.0), V(0, 0, 1), 4.0)[0]
            top[i, j] = bm.verts.new((x, y, hit_t.z if hit_t else base + 0.004))
            bot[i, j] = bm.verts.new((x, y, hit_b.z if hit_b else base - 0.004))
    last_i, last_j = len(xs) - 2, nv - 2
    for i in range(len(xs) - 1):
        for j in range(nv - 1):
            for grid, flip in ((top, False), (bot, True)):
                q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
                faces = [q]
                if i in (0, last_i) and j in (0, last_j):
                    # the corner of a wing tip, where top and bottom share three of these four points: cut it across the point they don't, or the two sides fold into one
                    k = next(k for k in range(4) if top[(i, i + 1, i + 1, i)[k], (j, j, j + 1, j + 1)[k]] is not bot[(i, i + 1, i + 1, i)[k], (j, j, j + 1, j + 1)[k]])
                    a, b, c, d = q[k], q[(k + 1) % 4], q[(k + 2) % 4], q[(k + 3) % 4]
                    faces = [[a, b, c], [a, c, d]]
                for f in faces:
                    bm.faces.new(list(reversed(f)) if flip else f)
    n = len(bm.verts)
    PARTS["Grid"] = (0, n)

    def tube(key, pts, rfn, sides, **kw):
        nonlocal n
        m.tube(pts, rfn, sides=sides, **kw)
        PARTS[key] = (n, len(bm.verts))
        n = len(bm.verts)
    tube("Tail", TAIL[::2] if (len(TAIL) - 1) % 2 == 0 else TAIL, tail_radius, 8)
    tube("HornL", ceph_path(1)[::2], ceph_radius, 8, flat=HORN_FLAT, plane=V(0, 0, 1))
    tube("HornR", ceph_path(-1)[::2], ceph_radius, 8, flat=HORN_FLAT, plane=V(0, 0, 1))
    tube("Dorsal", DORSAL[::3], lambda f: 0.012 + 0.03 * (1 - f) ** 1.2, 6, flat=0.4)
    return m.finish(N + "SkinLow", GAME)


LOW_TRIS = {"Smile": 80, "Mouth": 70, "Planet": 90, "Moon": 40}
SCALES = {"EyeL": 6.0, "EyeR": 6.0, "Smile": 3.0, "Mouth": 1.4, "Planet": 1.4, "Moon": 1.0}


def build_low(pieces, frames, body_tree):
    lows = {"Skin": low_skin(body_tree)}
    for key, target in LOW_TRIS.items():
        lows[key] = decimated(pieces[key], N + key + "Low", target)
    for tag in ("L", "R"):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 14, 10)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
WING_A = (0.26, 0.50, 0.76, 1.0)
REAR_LINE = 0.56       # the chord along which the back of the wing folds
TAIL_F = (0.06, 0.18, 0.30, 0.42, 0.55, 0.68, 0.80, 0.90)
HORN_F = (0.08, 0.42, 0.72)


def at_path(path, f):
    return path[min(len(path) - 1, int(round(f * (len(path) - 1))))].copy()


def skeleton(frames, marks):
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, 0.02, 0.0), "Root"), ("Head", V(0, -0.20, 0.02), "Body")]
    for name in ("SpiralInner", "SpiralMid", "SpiralOuter", "Orbit"):
        bones.append((name, SPIRAL_C.copy(), "Root"))
    parent = "Body"
    for k, f in enumerate(TAIL_F):
        bones.append(("Tail%d" % (k + 1), at_path(TAIL, f), parent))
        parent = "Tail%d" % (k + 1)
    bones.append(("TailTip", TAIL[-1].copy(), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones.append(("Eye" + tag, fr.centre.copy(), "Head"))
        parent = "Head"
        path = ceph_path(side)
        for k, f in enumerate(HORN_F):
            bones.append(("Horn%s%d" % (tag, k + 1), at_path(path, f), parent))
            parent = "Horn%s%d" % (tag, k + 1)
        parent = "Body"
        for k, a in enumerate(WING_A):
            y0, y1 = float(front_y(a)), float(rear_y(a))
            name = "Wing%s%d" % (tag, k + 1)
            bones.append((name, V(side * a, y0 + (y1 - y0) * 0.4, float(mid_z(a, 0.4))), parent))
            bones.append(("WingRear%s%d" % (tag, k + 1), V(side * a, y0 + (y1 - y0) * REAR_LINE, float(mid_z(a, REAR_LINE))), name))
            parent = name
    m = marks["Mouth"]
    bones += [("Smile", m.copy(), "Head"), ("Mouth", m.copy(), "Head")]
    return armature(bones)


def wing_weight(x, y):
    """Bones and shares on the wing and body at a point seen from above."""
    a, c = chord_of(np.array([x]), np.array([y]))
    a, c = float(a[0]), float(c[0])
    tag = "L" if x > 0 else "R"
    knots = (0.14,) + WING_A
    w = {}
    if a <= knots[0]:
        spans = {0: 1.0}
    elif a >= knots[-1]:
        spans = {4: 1.0}
    else:
        spans = {}
        for k in range(4):
            if a <= knots[k + 1]:
                f = float(smooth(knots[k], knots[k + 1], a))
                spans = {k: 1 - f, k + 1: f}
                break
    rear = float(smooth(REAR_LINE - 0.08, REAR_LINE + 0.2, c))
    for k, share in spans.items():
        if k == 0:
            w["Body"] = w.get("Body", 0) + share
        else:
            w["Wing%s%d" % (tag, k)] = w.get("Wing%s%d" % (tag, k), 0) + share * (1 - rear)
            w["WingRear%s%d" % (tag, k)] = w.get("WingRear%s%d" % (tag, k), 0) + share * rear
    # the head takes over the front of the body, the tail its root
    head = float(smooth(-0.14, -0.27, y)) * (1 - float(smooth(0.30, 0.42, a)))
    if head > 0:
        w = {k: v * (1 - head) for k, v in w.items()}
        w["Head"] = head
    root = float(smooth(0.30, 0.44, y)) * (1 - float(smooth(0.05, 0.14, a)))
    if root > 0:
        w = {k: v * (1 - root) for k, v in w.items()}
        w["Tail1"] = w.get("Tail1", 0) + root
    return w


def skin_weights(o):
    P = verts(o)
    out = [None] * len(P)
    a, b = PARTS["Grid"]
    for i in range(a, b):
        out[i] = wing_weight(P[i, 0], P[i, 1])
    a, b = PARTS["Tail"]
    s, _ = nearest_on(TAIL, P[a:b])
    names = ["Tail%d" % (k + 1) for k in range(8)] + ["TailTip"]
    for k, i in enumerate(range(a, b)):
        out[i] = chain_weight(names, TAIL_F + (1.0,), float(s[k]))
    for key, side, tag in (("HornL", 1, "L"), ("HornR", -1, "R")):
        a, b = PARTS[key]
        s, _ = nearest_on(ceph_path(side), P[a:b])
        names = ["Head"] + ["Horn%s%d" % (tag, k + 1) for k in range(3)]
        for k, i in enumerate(range(a, b)):
            out[i] = chain_weight(names, (0.02,) + HORN_F, float(s[k]))
    a, b = PARTS["Dorsal"]
    for i in range(a, b):
        out[i] = {"Tail1": 0.5, "Body": 0.5}
    return out


def bind_all(lows, rig, glows, owners):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    for key, bone in (("EyeL", "EyeL"), ("EyeR", "EyeR"), ("Smile", "Smile"), ("Mouth", "Mouth"),
                      ("Planet", "Orbit"), ("Moon", "Orbit")):
        rigid(lows[key], bone)
    for key, o in glows.items():
        P = verts(o)
        if key == "Glints":
            weigh(o, [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in P])
        else:
            assert len(owners[key]) == len(P), (key, len(owners[key]), len(P))
            weigh(o, [{bone: 1.0} if bone else wing_weight(p[0], p[1]) for bone, p in zip(owners[key], P)])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


def pose_library(frames):
    def flap(deg):
        out = {}
        for k in range(1, 5):
            out["WingL%d" % k] = ((0, 1, 0), -deg, (0, 0, 0))
            out["WingR%d" % k] = ((0, 1, 0), deg, (0, 0, 0))
        return out
    wave = {"WingRearL%d" % k: ((1, 0, 0), 22, (0, 0, 0)) for k in range(1, 5)}
    wave.update({"WingRearR%d" % k: ((1, 0, 0), 22, (0, 0, 0)) for k in range(1, 5)})
    tail = {"Tail%d" % k: ((0, 0, 1), 14 * (-1) ** k, (0, 0, 0)) for k in range(1, 9)}
    tail.update({"Body": ((1, 0, 0), 0, (0, 0, 0))})
    return {"Open": {"Smile": ((1, 0, 0), 0, (0, 0.03, 0)), "Mouth": ((1, 0, 0), 0, (0, -0.036, 0))}, "Look": {"EyeL": ((0, 0, 1), 18, (0, 0, 0)), "EyeR": ((0, 0, 1), 18, (0, 0, 0))}, "Up": flap(15), "Down": flap(-15), "Rear": wave, "Tail": tail,
            "Roll": {"Body": ((0, 1, 0), 90, (0, 0, 0))}, "Rearing": {"Body": ((1, 0, 0), 62, (0, 0, 0))}, "Horns": {"HornL1": ((1, 0, 0), 25, (0, 0, 0)), "HornL2": ((1, 0, 0), 25, (0, 0, 0)), "HornR1": ((0, 0, 1), 25, (0, 0, 0))}}


if __name__ == "__main__":
    pieces, frames, marks, glows, owners, body_only = build_hi()
    mat = hi_material(ao_distance=0.08, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 1.0
        o.data.materials.append(m)
        o.visible_shadow = False       # they cast none in the game either
    body_only.hide_render = True
    stage_setup((0.17, 0.2, 0.26, 1))
    if STAGE == "paint":
        shots(os.path.join(REVIEW, "paint"), VIEWS, target=VIEW_AT, dist=7.0)
    else:
        body_tree = tree_of(body_only)
        bpy.data.objects.remove(body_only, do_unlink=True)
        lows = build_low(pieces, frames, body_tree)
        unwrap(lows, [(lambda p: p.center.y < -0.16 and abs(p.center.x) < 0.46, 1.8), (lambda p: p.normal.z > 0, 1.0), (None, 0.5)], SCALES)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.05, 0.04, 0.17, 1))
        tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
        print("TRIS", sum(tris.values()), tris, flush=True)
        for o in glows.values():
            HI.objects.unlink(o)
            GAME.objects.link(o)
        rig = skeleton(frames, marks)
        body = bind_all(lows, rig, glows, owners)
        for o in list(HI.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
        for o in glows.values():
            print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", tuple(round(v, 2) for v in o.dimensions), flush=True)
        print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
        for tag, fr in frames.items():
            print("EYE", tag, tuple(round(v, 4) for v in fr.centre), flush=True)
        pose(rig, {})
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS, target=VIEW_AT, dist=7.0)
        lib = pose_library(frames)
        close = (0, -1, 0.1, 2.4, (0, -0.45, 0.02))
        wide = (0.5, -0.75, 0.3, 6.0, VIEW_AT)
        for name, view in (("Open", close), ("Look", (0.86, -0.46, 0.18, 1.5, (0.26, -0.42, 0.02))), ("Up", wide), ("Down", wide), ("Rear", (1, -0.2, 0.25, 5.0, VIEW_AT)), ("Tail", (0, -0.1, 1, 6.5, (0, 0.5, 0))), ("Roll", wide), ("Rearing", wide), ("Horns", (0.5, -0.8, 0.3, 2.6, (0, -0.5, 0.05)))):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT)
        pose(rig, {})
        for o in glows.values():
            o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.42, 6.0, VIEW_AT))      # first: the export takes the glow pieces' colours off
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

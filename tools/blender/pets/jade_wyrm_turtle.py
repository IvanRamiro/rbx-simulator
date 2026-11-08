"""The Jade Wyrm Turtle (Legendary, Earth; Bloomwood Egg): "Half wyrm, half mountain, and in no hurry. Whole gardens have grown on its back between one step and the next."

A new creature. The idea: a mountain that took a step. Its shell starts at the rim as polished imperial jade, plates seamed in gold, and rises into a real crag: terraces of jade rock under moss, a spring
that runs down the cliff into a pool, one old plum tree in blossom leaning out over the rim (the Bloomwood's pink), a dark pine behind, and a tiny red-pillared pavilion, which is what tells you the size of it all.
Out of the front comes the wyrm: a long S of a neck with a low sail, a horned head with an old gold beak, pale stripes running back from a heavy-lidded amber eye. Behind, a long tail with a sail, curling up.
Four elephant-thick legs on three-clawed feet. It carries the whole garden and it is not in a hurry.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/jade_wyrm_turtle.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, feet on z = 0. The maps go to assets/pets/BloomwoodEgg/.

What touches what: feet flat on z = 0; legs leave the body below the shell's rim and never rise past it; the neck leaves under the raised front arch of the rim, the tail under the rear arch;
tree and pine roots are sunk into the terrain they stand on; the pavilion's base sits on a levelled terrace; the spring's ribbon lies on the rock and ends in the pool; horns are sunk into the skull, the claws into the feet.
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
PET = "JadeWyrmTurtle"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BloomwoodEgg")

# ---------- the frame of it ----------
CY, RA, RB = 0.12, 0.92, 1.12      # the shell's centre in y, and its half-width and half-length
SITES = {"pool": (-0.33, -0.33), "pavilion": (-0.07, -0.33), "plum": (0.36, -0.30), "pine": (-0.46, 0.44)}
LEVELS = {"pool": (1.03, 0.14, 0.25), "pavilion": (1.13, 0.15, 0.26)}      # the height each is levelled to, and the radii the levelling fades over
NECK_KNOTS = [V(0, -0.66, 0.50), V(0, -1.00, 0.63), V(0, -1.23, 0.85), V(0, -1.40, 1.09), V(0, -1.60, 1.26)]
NECK = catmull(NECK_KNOTS, 8)
TAIL_KNOTS = [V(0, 0.98, 0.50), V(0, 1.32, 0.42), V(0.09, 1.62, 0.37), V(0.22, 1.86, 0.44), V(0.20, 2.06, 0.63), V(0.04, 2.14, 0.79), V(-0.09, 2.05, 0.86)]
TAIL = catmull(TAIL_KNOTS, 8)
GROUND = 0.08      # the soles: the game centres the model, so only the proportion matters
FRONT = [V(0.50, -0.58, 0.42), V(0.69, -0.66, 0.325), V(0.75, -0.71, 0.20), V(0.75, -0.73, GROUND)]
HIND = [V(0.50, 0.82, 0.42), V(0.68, 0.92, 0.325), V(0.74, 0.96, 0.20), V(0.74, 0.98, GROUND)]
LEGS = (("FL", 1, FRONT), ("FR", -1, FRONT), ("BL", 1, HIND), ("BR", -1, HIND))
LEG_R = (0.215, 0.205, 0.19, 0.175, 0.185, 0.23, 0.24)
LEG_RF = (0.0, 0.3, 0.52, 0.74, 0.85, 0.96, 1.0)
EYE_R = 0.056
EYE_C = V(0.104, -1.855, 1.338)
EYE_AXIS = V(0.84, -0.53, 0.10).normalized()
LID_UP, LID_LOW = (20.0, 112.0, 0.0044), (-36.0, -125.0, 0.0034)     # the upper lid rests low: old, patient
LID_TILT = -5.0
BLINK_U, BLINK_L = 38.0, 16.0


def leg_radius(f):
    return float(np.interp(f, LEG_RF, LEG_R))


def leg_path(side, knots, per=8):
    return catmull([mir(p, side) for p in knots], per)


def neck_radius(f):
    return 0.225 - 0.10 * f ** 0.8


def tail_radius(f):
    return 0.012 + 0.185 * (1 - f) ** 1.25


# ---------- the shell and the mountain on it ----------
def rim_shape(t):
    """Per angle t round the shell (front is -pi/2): how far out, as a share of the ellipse, and how high its rim."""
    front = (t + math.pi / 2 + math.pi) % TAU - math.pi
    rear = (t - math.pi / 2 + math.pi) % TAU - math.pi
    reach = 1 - 0.10 * np.exp(-(front / 0.34) ** 2) - 0.06 * np.exp(-(rear / 0.24) ** 2) + 0.009 * np.cos(t * 18 + TAU * 0.25 * 18 / 18)
    high = 0.575 + 0.285 * np.exp(-(front / 0.50) ** 2) + 0.13 * np.exp(-(rear / 0.36) ** 2)
    return reach, high


def stair(h, step):
    q = h / step
    i = np.floor(q)
    return step * (i + smooth(0.58, 1.0, q - i))


def mountain(x, y, rho):
    """The crag's height above the dome: two peaks and a shoulder, in terraces, levelled where the pool and the pavilion sit. Off-centre on purpose: it is a mountain, not a hat."""
    def hill(cx, cy, sx, sy, a):
        return a * np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))
    p = np.stack((x, y, np.zeros_like(x)), axis=1)
    warp = fbm(p, 3.2, 3, 11) - 0.5
    h = hill(-0.16, 0.34, 0.34, 0.40, 0.66) + hill(0.32, 0.50, 0.27, 0.30, 0.36) + hill(-0.40, -0.06, 0.30, 0.32, 0.20) + hill(0.08, 0.04, 0.40, 0.34, 0.14)
    h = np.maximum(0, h + 0.20 * warp * smooth(0.02, 0.2, h))
    terraced = stair(h, 0.125)
    crag = 1 - np.abs(2 * fbm(p + 3.0, 7.0, 4, 23) - 1)
    steep = smooth(0.12, 0.36, h)
    out = mix(h, terraced, 0.72) + 0.06 * (crag - 0.6) * steep
    fade = 1 - smooth(0.58, 0.72, rho)
    return out * fade


def plate_cells(t, rho):
    """The plates of the lower shell: an outer ring of 18 and an inner ring of 10, offset. Returns distance to the nearest seam (in metres, roughly), the plate's id and how far up the ring."""
    outer = rho > 0.84
    n = np.where(outer, 18, 10)
    shift = np.where(outer, 0.25, 0.5)
    q = (t / TAU + 0.5) * n + shift + 0.12 * np.sin(t * 3) * ~outer
    cell = np.floor(q)
    fu = q - cell
    r0 = np.where(outer, 0.84, 0.60)
    r1 = np.where(outer, 1.02, 0.84)
    fv = (rho - r0) / (r1 - r0)
    around = np.minimum(fu, 1 - fu) * TAU / n * 0.95 * rho
    across = np.minimum(fv, 1 - fv) * (r1 - r0)
    return np.minimum(around, across), cell + 100 * outer, fv


def shell_height(t, rho, reach, high, plain=False):
    x = rho * reach * RA * np.cos(t)
    y = CY + rho * reach * RB * np.sin(t)
    dome = high + 0.46 * (1 - rho ** 2) ** 0.62
    seam, cell, fv = plate_cells(t, rho)
    plated = smooth(0.60, 0.67, rho)
    relief = 0.0 if plain else plated * (-0.016 * (1 - smooth(0.0, 0.016, seam)) + 0.010 * smooth(0.016, 0.07, seam))
    z = dome + relief + mountain(x, y, rho)
    for key, (level, r0, r1) in LEVELS.items():
        sx, sy = SITES[key]
        w = 1 - smooth(r0, r1, np.sqrt((x - sx) ** 2 + (y - sy) ** 2))
        z = z * (1 - w) + level * w
    return x, y, z


def terrain_at(x, y):
    """The top of the shell at a point: for setting things on it."""
    t = math.atan2((y - CY) / RB, x / RA)
    reach, high = rim_shape(np.array([t]))
    rho = math.sqrt((x / RA) ** 2 + ((y - CY) / RB) ** 2) / float(reach[0])
    _, _, z = shell_height(np.array([t]), np.array([rho]), reach, high)
    return float(z[0])


def build_shell():
    nt, nr = 1100, 420
    t = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    rows = np.linspace(0, 1, nr + 1)[1:] ** 0.8
    bm = bmesh.new()
    tt, rr = np.meshgrid(t, rows, indexing="xy")
    tt, rr = tt.ravel(), rr.ravel()
    reach, high = rim_shape(tt)
    x, y, z = shell_height(tt, rr, reach, high)
    P = np.stack((x, y, z), axis=1).reshape(nr, nt, 3)
    grid = [[bm.verts.new(P[i, j]) for j in range(nt)] for i in range(nr)]
    apex = bm.verts.new((0, CY, float(shell_height(np.array([0.0]), np.array([0.0]), *rim_shape(np.array([0.0])))[2][0])))
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((apex, grid[0][j], grid[0][j2]))
        for i in range(nr - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]))
    # the lip, turned under, and the underside
    reach1, high1 = rim_shape(t)
    under = []
    for rho, drop in ((1.012, 0.022), (1.0, 0.052), (0.93, 0.07), (0.72, 0.08)):
        under.append([bm.verts.new((rho * reach1[j] * RA * math.cos(t[j]), CY + rho * reach1[j] * RB * math.sin(t[j]), high1[j] - drop)) for j in range(nt)])
    last = grid[nr - 1]
    for ring in under:
        for j in range(nt):
            j2 = (j + 1) % nt
            bm.faces.new((last[j], ring[j], ring[j2], last[j2]))
        last = ring
    hub = bm.verts.new((0, CY, 0.60))
    for j in range(nt):
        bm.faces.new((last[j], hub, last[(j + 1) % nt]))
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(N + "ShellHi")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(N + "ShellHi", me)
    HI.objects.link(o)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0058, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    core.ball(V(0, CY, 0.52), (0.77, 0.99, 0.285))          # the body, under its shell: the plastron is its underside
    core.ball(V(0, -0.72, 0.56), (0.33, 0.28, 0.27))        # the loose skin at the root of the neck
    core.ball(V(0, 0.98, 0.50), (0.27, 0.27, 0.20))         # and of the tail
    core.tube(NECK, neck_radius, sides=28, flat=0.94)
    # the head: long, and old; a turtle's beak on a wyrm's skull
    core.ball(V(0, -1.70, 1.315), (0.165, 0.225, 0.135))    # the skull
    core.ball(V(0, -1.77, 1.345), (0.135, 0.205, 0.098))    # the dome of the forehead, blending into the skull: a smaller one left a plateau with a hard rim
    for side in (1, -1):
        core.ball(V(side * 0.098, -1.71, 1.245), (0.088, 0.16, 0.095))     # the heavy cheek
        core.ball(V(side * 0.100, -1.865, 1.392), (0.068, 0.115, 0.034))   # the brow
        core.ball(V(side * 0.082, -1.81, 1.365), (0.066, 0.12, 0.052))     # the bone behind the brow: the lid's hidden edge stays under it
        core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.012, (0.06, 0.06, 0.06))
        core.ball(V(side * 0.036, -2.045, 1.283), (0.026, 0.030, 0.018))   # the nostril's swell
    muzzle = catmull([V(0, -1.82, 1.30), V(0, -1.95, 1.265), V(0, -2.05, 1.235)], 8)
    core.tube(muzzle, lambda f: 0.118 - 0.036 * f, sides=22, flat=0.98)
    core.ball(V(0, -2.045, 1.232), (0.076, 0.056, 0.060))   # the end of the snout
    core.ball(V(0, -2.082, 1.198), (0.026, 0.022, 0.032))   # the beak: a turtle's, only just hooked
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.012, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 18})])
    body = bpy.data.objects.new(N + "BodyOnly", c.data.copy())       # for the game mesh: legs and tail get hand-built tubes, with loops where they bend
    HI.objects.link(body)
    body.hide_render = True
    thin = Mesh()
    for key, side, knots in LEGS:
        thin.tube(leg_path(side, knots), leg_radius, sides=26, flat=0.96, plane=V(1, 0, 0))
    thin.tube(TAIL, tail_radius, sides=22, flat=0.88, plane=V(1, 0, 0))
    th = thin.finish(N + "ThinHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0052, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c, body


# ---------- small pieces ----------
def claw_paths(side, knots):
    foot = mir(knots[3], side)
    out = []
    for a, length, r in ((-0.62, 0.135, 0.046), (0.0, 0.155, 0.052), (0.62, 0.135, 0.046)):
        d = V(math.sin(a) * side, -math.cos(a), 0)
        root = foot + d * 0.15 + V(0, 0, 0.078)
        out.append((catmull([root, root + d * length * 0.55 + V(0, 0, 0.012), root + d * length - V(0, 0, 0.066)], 5), r))
    return out


def build_claws(name, coll, sides, step):
    m = Mesh()
    which = []
    for index, (key, side, knots) in enumerate(LEGS):
        before = len(m.bm.verts)
        for path, r in claw_paths(side, knots):
            m.tube(path[::step] if path[::step][-1] == path[-1] else path[::step] + [path[-1]], lambda f, r=r: r * (1 - f) ** 0.75 + 0.004, sides=sides, flat=1.15, plane=V(1, 0, 0))
        which += [index] * (len(m.bm.verts) - before)
    return m.finish(name, coll), np.array(which)


def horn_path(side):
    return catmull([V(side * 0.075, -1.625, 1.385), V(side * 0.125, -1.47, 1.50), V(side * 0.145, -1.30, 1.555), V(side * 0.125, -1.13, 1.625), V(side * 0.095, -1.03, 1.72)], 8)


def horn_radius(f):
    return 0.052 * (1 - f) ** 0.8 + 0.006


def build_horns(name, coll, sides, step):
    m = Mesh()
    for side in (1, -1):
        m.tube(horn_path(side)[::step] + ([] if step == 1 else [horn_path(side)[-1]]), horn_radius, sides=sides, flat=0.9, plane=V(1, 0, 0))
    return m.finish(name, coll)


def build_jaw(name, coll, sides, per):
    path = catmull([V(0, -1.62, 1.205), V(0, -1.84, 1.172), V(0, -1.995, 1.166), V(0, -2.052, 1.176)], per)
    m = Mesh()
    m.tube(path, lambda f: 0.046 - 0.020 * f, sides=sides, flat=2.15, plane=V(1, 0, 0))
    return m.finish(name, coll)


def along(path, f):
    """A point on a sampled path at fraction f, and the path's direction there."""
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i), (path[i + 1] - path[i]).normalized()


def neck_sail_point(u, v):
    p, d = along(NECK, 0.26 + 0.70 * (1 - u))
    up = (V(0, 0, 1) - d * d.z).normalized()
    f = 0.26 + 0.70 * (1 - u)
    height = 0.085 * math.sin(math.pi * min(1.0, u * 1.02)) ** 0.7 * (0.93 + 0.07 * math.cos(u * math.pi * 14))
    return p + up * (neck_radius(f) * 0.9 + v * (height + 0.02))


def tail_sail_point(u, v):
    f = 0.13 + 0.80 * u
    p, d = along(TAIL, f)
    sideways = V(1, 0, 0)
    up = d.cross(sideways)
    if up.z < 0 and f < 0.75:
        up = -up
    up = up.normalized() if f < 0.75 else (V(0, 0, 1) * (1 - (f - 0.75) * 3) - d * 0.0 + V(0, 1, 0) * (f - 0.75) * 3).normalized()
    height = 0.095 * math.sin(math.pi * u ** 0.55) ** 0.8 * (0.93 + 0.07 * math.cos(u * math.pi * 16))
    return p + up * (tail_radius(f) * 0.8 + v * (height + 0.012))


def sail_thick(u, v):
    return 0.016 * (1 - v) + 0.005


def frill_point(side):
    root = V(side * 0.135, -1.60, 1.245)
    U = V(side * 0.62, 0.74, 0.16).normalized()
    Vv = (V(0, 0.2, 1) - U * V(0, 0.2, 1).dot(U)).normalized()

    def point(u, v):
        w = 2 * v - 1
        width = 0.085 * math.sin(math.pi * u ** 0.6) ** 0.8 + 0.012
        tip = 0.75 + 0.25 * math.cos(w * 3.2)
        return root + U * 0.30 * u * tip + Vv * width * w + U.cross(Vv) * side * 0.012 * math.sin(math.pi * u)
    return point


def frill_thick(u, v):
    return 0.012 * (1 - u) + 0.004


# ---------- the plum, the pine, the pavilion, the spring ----------
def site_z(key):
    return terrain_at(*SITES[key])


PLUM_PADS = (("PadA", 0, (0.20, -0.34, 0.60), (0.37, 0.33, 0.21)), ("PadB", 0, (-0.18, -0.10, 0.56), (0.29, 0.27, 0.17)), ("PadC", 0, (0.07, 0.04, 0.80), (0.29, 0.27, 0.19)))


def plum_paths():
    """The old trunk twists up and out toward the rim, with a bough to each mass of blossom. (path, radius at root, radius at tip)"""
    x, y = SITES["plum"]
    z = site_z("plum")
    b = V(x, y, z)
    trunk = catmull([b - V(0, 0, 0.06), b + V(0.05, -0.01, 0.12), b + V(0.00, -0.06, 0.25), b + V(0.07, -0.09, 0.38), b + V(0.07, -0.08, 0.56)], 7)
    fork = trunk[int(len(trunk) * 0.62)]
    top = trunk[-1]
    a = catmull([top, top + V(0.06, -0.09, 0.02), b + V(0.20, -0.32, 0.60)], 6)
    bough_b = catmull([fork, fork + V(-0.10, 0.0, 0.07), b + V(-0.18, -0.10, 0.54)], 6)
    c = catmull([top, top + V(-0.01, 0.06, 0.10), b + V(0.07, 0.04, 0.76)], 6)
    return b, [(trunk, 0.115, 0.058), (a, 0.056, 0.026), (bough_b, 0.048, 0.022), (c, 0.05, 0.024)]


def build_wood(paths, name, coll, sides, step=1):
    m = Mesh()
    for path, r0, r1 in paths:
        pts = path[::step]
        if pts[-1] != path[-1]:
            pts.append(path[-1])
        m.tube(pts, lambda f, a=r0, b=r1: a + (b - a) * f, sides=sides, flat=0.9, plane=V(1, 0.3, 0).normalized())
    return m.finish(name, coll)


def pad_lobes(c, r, seed):
    """A mass of blossom or needles is flat underneath and heaped above, like a cloud on a scroll: lobes of different sizes, never a ball."""
    rng = np.random.default_rng(seed)
    out = [(c, r)]
    for k in range(22):
        a = rng.uniform(0, TAU)
        d = math.sqrt(rng.uniform(0.15, 1.0))
        s = rng.uniform(0.26, 0.5)
        at = c + V(math.cos(a) * d * r[0] * 0.88, math.sin(a) * d * r[1] * 0.88, r[2] * rng.uniform(-0.55, 0.75) * (1.25 - d))
        q = max(r[0], r[1]) * s
        out.append((at, (q, q * rng.uniform(0.85, 1.1), q * rng.uniform(0.62, 0.85))))
    return out


def build_pads(specs, base, name, coll, voxel, seed_base):
    """One mesh of canopy. Returns it, its vertices telling apart by the nearest pad later."""
    m = Mesh()
    for k, (_, _, off, r) in enumerate(specs):
        for c, rr in pad_lobes(base + V(*off), r, seed_base + k):
            m.ball(c, rr, 24, 14)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel * 2.2, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6}), ("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


PINE_PADS = (("PineA", 0, (-0.03, 0.02, 0.62), (0.22, 0.21, 0.10)), ("PineB", 0, (-0.17, 0.02, 0.43), (0.21, 0.18, 0.09)), ("PineC", 0, (0.15, 0.05, 0.30), (0.18, 0.16, 0.08)))


def pine_paths():
    x, y = SITES["pine"]
    z = site_z("pine")
    b = V(x, y, z)
    trunk = catmull([b - V(0, 0, 0.06), b + V(0.03, 0, 0.15), b + V(-0.03, 0.01, 0.34), b + V(-0.03, 0.02, 0.62)], 6)
    low = catmull([trunk[7], b + V(0.09, 0.03, 0.25), b + V(0.15, 0.05, 0.29)], 5)
    mid = catmull([trunk[11], b + V(-0.11, 0.02, 0.38), b + V(-0.17, 0.02, 0.42)], 5)
    return b, [(trunk, 0.078, 0.022), (low, 0.03, 0.012), (mid, 0.032, 0.012)]


def pavilion(name, coll, low=False):
    """A tiny open pavilion: a stone base, four red pillars, one upswept roof with a gold finial. The thing that tells you how big the mountain is."""
    x, y = SITES["pavilion"]
    z = site_z("pavilion") - 0.012
    m = Mesh()
    B = V(x, y, z)
    W, H = 0.092, 0.135
    # the base: a low square plinth
    def box(c, sx, sy, sz, taper=1.0):
        vs = []
        for dz, k in ((0, 1.0), (sz, taper)):
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                vs.append(m.bm.verts.new(c + V(a * sx * k, b * sy * k, dz)))
        for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            m.bm.faces.new([vs[i] for i in f])
    box(B, W * 1.32, W * 1.32, 0.030, 0.94)
    floor = 0.030 + z
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = V(x + a * W, y + b * W, floor - 0.004)
        rows = 3 if low else 9
        m.tube([p + V(0, 0, (H + 0.008) * k / (rows - 1)) for k in range(rows)], lambda f: 0.012, sides=6 if low else 12)
    # the roof: a square hip, its eaves sweeping up at the corners
    roof_z = floor + H
    nu = 8 if low else 44

    def roof(u, v):
        a, b = 2 * u - 1, 2 * v - 1
        e = max(abs(a), abs(b))
        corner = (abs(a) * abs(b)) ** 2
        rise = 0.092 * (1 - e) ** 0.72
        lift = 0.030 * corner + 0.006
        return V(x + a * W * 1.72 * (1 + 0.1 * corner), y + b * W * 1.72 * (1 + 0.1 * corner), roof_z + rise + lift)
    m.sheet(roof, lambda u, v: 0.012, nu, nu)
    top = V(x, y, roof_z + 0.092 + 0.002)
    m.tube([top - V(0, 0, 0.012), top + V(0, 0, 0.018), top + V(0, 0, 0.036), top + V(0, 0, 0.052)], lambda f: 0.0115 * (1 - f) + 0.002 + 0.006 * math.sin(math.pi * f), sides=6 if low else 12)
    return m.finish(name, coll, smooth_shade=False), roof_z, floor


SPRING_XY = [V(x, y, 0) for x, y in ((-0.20, 0.13), (-0.25, 0.05), (-0.235, -0.04), (-0.30, -0.10), (-0.285, -0.17), (-0.31, -0.205), (-0.325, -0.25))]
SPRING_PATH = catmull(SPRING_XY, 8)


SPRING_BRANCH = catmull([V(x, y, 0) for x, y in ((-0.10, 0.03), (-0.155, -0.03), (-0.175, -0.09), (-0.235, -0.12), (-0.285, -0.17))], 6)


def spring_point(height, path=None, thin=1.0):
    """A thread of the spring, lying on the rock. height(x, y): the rock under it."""
    path = path or SPRING_PATH

    def point(u, v):
        p, d = along(path, u)
        side = V(-d.y, d.x, 0).normalized()
        width = (0.007 + 0.010 * u ** 1.5 + 0.002 * math.sin(u * 19)) * thin
        q = p + side * (v - 0.5) * width
        return V(q.x, q.y, height(q.x, q.y))
    return point


def pool_edge(a):
    """How far out the pool's shore lies at this angle: a pond's outline, and not a shape."""
    return 0.092 + 0.015 * math.sin(a * 3 + 0.7) + 0.010 * math.sin(a * 5 + 2.1) + 0.005 * math.sin(a * 8 + 4.0)


def build_pool(tree, name, coll, sides, rings):
    """A thin slab of still water and shore stones, flat, on whatever rock lies under it. Its rim is sunk into the rock."""
    cx, cy = SITES["pool"]
    top = 0.0
    for k in range(32):
        a = TAU * k / 32
        for f in (0.0, 0.5, 1.0):
            hit = tree.ray_cast(V(cx + math.cos(a) * pool_edge(a) * f, cy + math.sin(a) * pool_edge(a) * f, 3.0), V(0, 0, -1), 4.0)[0]
            if hit:
                top = max(top, hit.z)
    z = top + 0.004
    m = Mesh()
    bm = m.bm
    centre = bm.verts.new((cx, cy, z))
    grid = []
    for i in range(1, rings + 1):
        f = i / rings
        grid.append([bm.verts.new((cx + math.cos(TAU * k / sides) * pool_edge(TAU * k / sides) * f, cy + math.sin(TAU * k / sides) * pool_edge(TAU * k / sides) * f, z)) for k in range(sides)])
    skirt = [bm.verts.new((cx + math.cos(TAU * k / sides) * pool_edge(TAU * k / sides) * 1.02, cy + math.sin(TAU * k / sides) * pool_edge(TAU * k / sides) * 1.02, z - 0.05)) for k in range(sides)]
    for k in range(sides):
        k2 = (k + 1) % sides
        bm.faces.new((centre, grid[0][k], grid[0][k2]))
        for i in range(rings - 1):
            bm.faces.new((grid[i][k], grid[i + 1][k], grid[i + 1][k2], grid[i][k2]))
        bm.faces.new((grid[-1][k], skirt[k], skirt[k2], grid[-1][k2]))
    bm.faces.new(list(reversed(skirt)))
    return m.finish(name, coll, smooth_shade=False)


def paint_pool(o):
    P = verts(o)
    cx, cy = SITES["pool"]
    a = np.arctan2(P[:, 1] - cy, P[:, 0] - cx)
    edge = 0.092 + 0.015 * np.sin(a * 3 + 0.7) + 0.010 * np.sin(a * 5 + 2.1) + 0.005 * np.sin(a * 8 + 4.0)
    f = np.sqrt((P[:, 0] - cx) ** 2 + (P[:, 1] - cy) ** 2) / edge
    water = mix(rgb(8, 58, 66), rgb(34, 136, 126), smooth(0.25, 0.8, f))
    stones = smooth(0.84, 0.9, f + 0.06 * (fbm(P, 44.0, 2, 37) - 0.5))
    col = mix(water, mix(rgb(120, 126, 108), rgb(186, 186, 160), fbm(P, 70.0, 2, 3)), stones)
    paint(o, col, 0.05 + 0.75 * stones)


def ray_height(tree, lift):
    def height(x, y):
        hit = tree.ray_cast(V(x, y, 3.0), V(0, 0, -1), 4.0)[0]
        return (hit.z if hit else terrain_at(x, y)) + lift
    return height


def build_spring(tree, name, coll, nu, nv, ball):
    m = Mesh()
    m.sheet(spring_point(ray_height(tree, 0.006)), lambda u, v: 0.003, nu, nv)
    m.sheet(spring_point(ray_height(tree, 0.0105), SPRING_BRANCH, 0.8), lambda u, v: 0.003, nu // 2, nv)      # (a little prouder, so the two never fight where they join)
    return m.finish(name, coll, smooth_shade=False)


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-1, 0, 0.08), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.05, 0.92)


# ---------- paint ----------
DEEP, JADE, PALE, CELADON = rgb(10, 62, 50), rgb(24, 112, 84), rgb(112, 186, 148), rgb(176, 218, 186)
GOLD, OLD_GOLD, CREAM, IVORY = rgb(232, 176, 78), rgb(150, 104, 44), rgb(226, 208, 152), rgb(240, 230, 200)
ROCK_A, ROCK_B, MOSS_A, MOSS_B = rgb(50, 88, 72), rgb(108, 138, 110), rgb(58, 106, 42), rgb(136, 172, 66)
PINK, BLUSH, ROSE, BARK = rgb(250, 176, 200), rgb(255, 232, 238), rgb(176, 66, 112), rgb(58, 40, 36)
MOUTH = rgb(92, 34, 44)


def worley(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point, for scales and flowers."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                jx = hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)
                jy = hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)
                jz = hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)
                d = np.sqrt((q[:, 0] - c[:, 0] - jx) ** 2 + (q[:, 1] - c[:, 1] - jy) ** 2 + (q[:, 2] - c[:, 2] - jz) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                d1 = np.where(nearer, d, d1)
    return d1, d2


def shell_coords(P):
    t = np.arctan2((P[:, 1] - CY) / RB, P[:, 0] / RA)
    reach, high = rim_shape(t)
    rho = np.sqrt((P[:, 0] / RA) ** 2 + ((P[:, 1] - CY) / RB) ** 2) / reach
    return t, rho, high


def paint_shell(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    t, rho, high = shell_coords(P)
    seam, cell, fv = plate_cells(t, rho)
    plated = smooth(0.60, 0.67, rho)
    up = Nn[:, 2]
    veins = 1 - np.abs(2 * fbm(P, 5.5, 4, 3) - 1)
    # the polished plates: dark at the seam, lighter in the middle, each its own tone, clouded like real jade
    tone = hash01(cell.astype(np.int64), cell.astype(np.int64) * 3, np.zeros(len(P), dtype=np.int64), 9)
    plate = mix(DEEP, JADE, smooth(0.012, 0.10, seam) * (0.62 + 0.38 * tone))
    plate = mix(plate, PALE, smooth(0.45, 0.9, fbm(P, 3.4, 4, 13)) * smooth(0.02, 0.12, seam) * 0.55)
    plate = mix(plate, PALE, smooth(0.965, 1.0, veins) * 0.4)
    rings = np.sin(seam * 210) * 0.5 + 0.5
    plate = plate * (1 - 0.07 * rings * smooth(0.03, 0.05, seam))[:, None]
    gold_seam = (1 - smooth(0.005, 0.0125, seam)) * plated
    # the rock: strata that tilt and wander, pale veins, then moss wherever it lies flat enough to hold
    wander = 0.075 * (fbm(P, 2.6, 3, 21) - 0.5)
    strata = np.sin((z + wander + 0.05 * x) * 96) * 0.5 + 0.5
    strata2 = np.sin((z + wander) * 300 + fbm(P, 9.0, 2, 8) * 6) * 0.5 + 0.5
    blotch = fbm(P, 5.0, 4, 29)
    rock = mix(ROCK_A, ROCK_B, smooth(0.25, 0.85, strata * 0.45 + blotch * 0.55) * (0.72 + 0.28 * strata2))
    rock = mix(rock, CELADON, smooth(0.97, 1.0, veins) * 0.5)
    rock = mix(rock, DEEP, smooth(0.4, 0.05, up + 0.5) * 0.35)
    tuft = fbm(P, 38.0, 3, 41)
    patch = fbm(P, 8.0, 3, 17)
    moss = smooth(0.42, 0.68, up + 0.6 * (patch - 0.5))
    grass = mix(MOSS_A, MOSS_B, smooth(0.38, 0.68, tuft) * (0.55 + 0.45 * patch))
    top = mix(rock, grass, moss)
    # fallen petals under the plum, thick near the trunk and thinning out
    px, py = SITES["plum"]
    near = 1 - smooth(0.12, 0.55, np.sqrt((x - px - 0.02) ** 2 + (y - py + 0.1) ** 2))
    d1, _ = worley(P, 34.0, 77)
    petals = (1 - smooth(0.16, 0.26, d1)) * smooth(0.62, 0.42, hash01(np.floor(P[:, 0] * 34).astype(np.int64), np.floor(P[:, 1] * 34).astype(np.int64), np.floor(P[:, 2] * 34).astype(np.int64), 5) + 0.4 * (1 - near)) * near * moss
    top = mix(top, PINK, petals * 0.9)
    # what the canopies shade, since the bake's occlusion stays inside each piece
    shade = np.ones_like(x)
    bx, by = SITES["plum"]
    for _, _, off, r in PLUM_PADS:
        shade *= 1 - 0.34 * np.exp(-(((x - bx - off[0]) / (r[0] * 1.1)) ** 2 + ((y - by - off[1]) / (r[1] * 1.1)) ** 2))
    top = top * shade[:, None]
    col = mix(top, plate, plated)
    col = mix(col, GOLD, gold_seam)
    # under the rim: dark, nobody looks there
    under = smooth(-0.2, -0.6, up) * smooth(0.7, 0.95, rho)
    col = mix(col, DEEP * 0.5, under)
    rough = (0.82 - 0.25 * (1 - moss)) * (1 - plated) + (0.22 + 0.1 * (1 - smooth(0.0, 0.05, seam))) * plated      # (plain arrays: mix() would broadcast n by n)
    rough = rough * (1 - gold_seam) + 0.3 * gold_seam
    metal = gold_seam
    disp = (1 - plated) * (0.0035 * (strata - 0.5) * (1 - moss) + 0.006 * (tuft - 0.5) * moss + 0.0015 * petals)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, rough, metal)


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    up = Nn[:, 2]
    head = smooth(-1.56, -1.66, y) * smooth(1.0, 1.08, z)
    d1, d2 = worley(P, 21.0, 11)
    big = smooth(0.0, 0.26, d2 - d1)
    d3, d4 = worley(P, 44.0, 31)
    small = smooth(0.0, 0.3, d4 - d3)
    pattern = big * (1 - head) + small * head
    # the hide: deep jade above, celadon on the flank, cream below; the scales' centres lighter
    col = mix(mix(PALE, JADE, 0.55), DEEP, smooth(-0.25, 0.65, up))
    col = mix(col, mix(CELADON, CREAM, 0.6), smooth(-0.35, -0.85, up) * (1 - head * smooth(1.22, 1.30, z)))      # (not under the brow: that read as pale eyebrows)
    col = mix(col * 0.72, col * 1.12, pattern)
    # the neck: pale throat in overlapping bands, old-gold stripes running its length and on over the head, as a real turtle has them
    f, d = nearest_on(NECK, P)
    k = f * (len(NECK) - 1)
    pz = np.interp(k, np.arange(len(NECK)), [p.z for p in NECK])
    py = np.interp(k, np.arange(len(NECK)), [p.y for p in NECK])
    around = np.arctan2(np.abs(x), (z - pz) + (py - y) * 0.45)       # 0 on top of the neck, pi under the throat
    neck = (1 - head) * smooth(-0.82, -0.98, y) * (d < 0.3)
    stripe = np.zeros_like(x)
    for centre, width, wob in ((1.15, 0.13, 0.05), (1.78, 0.10, 0.06)):
        stripe = np.maximum(stripe, 1 - smooth(width * 0.7, width, np.abs(around - centre - wob * np.sin(f * 15))))
    col = mix(col, mix(GOLD, CREAM, 0.45), stripe * neck)
    throat = smooth(2.25, 2.6, around) * neck
    bands = (f * 34) % 1
    col = mix(col, mix(CREAM, IVORY, smooth(0.1, 0.9, bands)) * (0.82 + 0.18 * smooth(0.0, 0.2, bands))[:, None], throat)
    # the loose folds where the neck leaves the shell
    folds = np.sin(f * 62 + 2 * np.sin(around * 3)) * 0.5 + 0.5
    fold_zone = (1 - smooth(0.12, 0.3, f)) * neck
    col = mix(col, DEEP, smooth(0.65, 1.0, folds) * fold_zone * 0.55)
    # the head: darker crown; old gold down the cheek from the eye; a pale line under it
    col = mix(col, mix(DEEP, JADE, 0.5), head * smooth(0.0, 0.6, up))
    for side in (1, -1):
        d_eye = np.sqrt((x - side * 0.14) ** 2 + ((z - 1.285 - 0.20 * (y + 1.86))) ** 2 * 4)
        cheek = (1 - smooth(0.012, 0.03, d_eye)) * smooth(-1.86, -1.80, y) * (1 - smooth(-1.60, -1.52, y)) * (x * side > 0)
        col = mix(col, mix(GOLD, CREAM, 0.45), cheek)
    eye_d = np.minimum(np.linalg.norm(P - np.array(tuple(EYE_C)), axis=1), np.linalg.norm(P - np.array(tuple(mir(EYE_C, -1))), axis=1))
    col = mix(col, DEEP * 0.6, (1 - smooth(0.06, 0.095, eye_d)) * 0.55)
    # the beak: horn from old gold at its root to ivory at the edge
    lip = np.maximum(smooth(-2.045, -2.075, y), smooth(1.215, 1.19, z) * smooth(-1.86, -1.96, y))
    beak = lip * head
    col = mix(col, mix(OLD_GOLD, CREAM, smooth(-2.0, -2.09, y) * 0.75), beak)
    for side in (1, -1):
        nost = 1 - smooth(0.007, 0.013, np.sqrt((x - side * 0.038) ** 2 + (y + 2.066) ** 2 * 0.6 + (z - 1.292) ** 2))
        col = mix(col, rgb(16, 22, 18), nost)
    # the roof of the mouth, for when the jaw opens
    roof = (1 - smooth(0.075, 0.09, np.abs(x))) * smooth(-1.72, -1.78, y) * smooth(-0.45, -0.8, up) * (1 - smooth(-2.05, -2.09, y)) * head
    col = mix(col, MOUTH, roof)
    # the plastron: cream plates seamed in old gold, the underside of the body
    belly = smooth(0.34, 0.27, z) * (1 - smooth(0.60, 0.72, np.sqrt((x / 0.77) ** 2 + ((y - CY) / 0.99) ** 2))) * smooth(-0.3, -0.75, up)
    gx = np.abs(x)
    plate_seam = np.minimum(np.abs(gx - 0.012), np.abs(((y + 0.9) / 0.38) % 1 - 0.5) * 0.38 + 0.0)
    plast = mix(CREAM, IVORY, fbm(P, 6.0, 3, 5))
    plast = mix(plast, OLD_GOLD, 1 - smooth(0.006, 0.014, plate_seam))
    col = mix(col, plast, belly)
    # feet: paler soles, and shade under the shell's rim (the bake's occlusion stays inside each piece)
    t, rho, high = shell_coords(P)
    under_rim = (1 - smooth(0.85, 1.12, rho)) * smooth(high - 0.42, high - 0.08, z) * (1 - head)
    col = col * (1 - 0.72 * under_rim)[:, None]
    leg_band = smooth(0.18, GROUND + 0.02, z) * (1 - belly)
    col = mix(col, mix(PALE, CREAM, 0.4), leg_band * smooth(-0.2, 0.2, Nn[:, 2]) * 0.35)
    rough = 0.62 - 0.1 * pattern * (1 - head) - 0.22 * beak - 0.2 * belly + 0.05 * (fbm(P, 22.0, 2, 9) - 0.5)
    disp = (1 - belly) * (1 - beak) * ((1 - throat) * (0.0042 * (1 - head) * big + 0.002 * head * small) + 0.003 * throat * smooth(0.0, 0.3, bands)) - 0.009 * smooth(0.6, 1.0, folds) * fold_zone
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, rough)


def eye_paint(o, fr):
    """Old amber, gone to dark at the rim, with a tall soft pupil: half wyrm, and kind about it."""
    px, py, a = eye_coords(o, fr)
    IRIS = 0.86
    r = np.where(a > 0, np.sqrt(px ** 2 + py ** 2) / IRIS, 3.0)
    azi = np.arctan2(py, px)
    iris = mix(rgb(255, 210, 92), rgb(176, 88, 22), smooth(0.28, 0.98, r))
    iris = mix(iris, rgb(255, 238, 160), (np.sin(azi * 26) * 0.5 + 0.5) * smooth(0.35, 0.85, r) * 0.32)
    iris = iris * (1 - 0.5 * smooth(0.0, 0.75, py / IRIS))[:, None]
    col = mix(rgb(214, 196, 150), iris, 1 - smooth(0.97, 1.0, r))
    col = mix(col, rgb(18, 12, 10), smooth(0.86, 0.97, r) * (1 - smooth(0.985, 1.04, r)))
    pu = np.where(a > 0, np.sqrt((px / (IRIS * 0.26)) ** 2 + (py / (IRIS * 0.56)) ** 2), 3.0)
    col = mix(col, rgb(6, 6, 10), 1 - smooth(0.88, 1.0, pu))
    paint(o, col, np.full(len(px), 0.07))


def paint_horns(o):
    P = verts(o)
    Nn = normals(o)
    f = np.zeros(len(P))
    for side in (1, -1):
        mine = P[:, 0] * side > 0
        f[mine], _ = nearest_on(horn_path(side), P[mine])
    ridge = np.sin(f * 88) * 0.5 + 0.5
    col = mix(DEEP, PALE, smooth(0.0, 0.42, f))
    col = mix(col, IVORY, smooth(0.4, 1.0, f))
    col = col * (1 - 0.32 * smooth(0.65, 1.0, ridge) * (1 - smooth(0.7, 0.95, f)))[:, None]
    set_verts(o, P - Nn * (0.0045 * smooth(0.6, 1.0, ridge) * (1 - smooth(0.7, 0.95, f)))[:, None])
    paint(o, col, 0.36)


def sail_colour(u, v):
    ribs = np.abs(((u * 26) % 1) - 0.5) * 2
    col = mix(DEEP, JADE, smooth(0.0, 0.55, v))
    col = mix(col, PALE, smooth(0.45, 0.9, v) * 0.7)
    col = col * (1 - 0.35 * (1 - smooth(0.0, 0.22, ribs)))[:, None]
    return mix(col, GOLD, smooth(0.86, 0.98, v))


def sail_relief(u, v):
    ribs = np.abs(((u * 26) % 1) - 0.5) * 2
    return 0.0028 * (1 - smooth(0.0, 0.4, ribs))


def frill_colour(u, v):
    w = np.abs(2 * v - 1)
    ribs = np.abs(((v * 7) % 1) - 0.5) * 2
    col = mix(DEEP, JADE, smooth(0.0, 0.5, u))
    col = mix(col, PALE, smooth(0.45, 0.95, u) * 0.75)
    col = col * (1 - 0.32 * (1 - smooth(0.0, 0.26, ribs)))[:, None]
    return mix(col, GOLD, smooth(0.82, 0.98, np.maximum(u, w * 0.9)))


def paint_wood(o, seed):
    P = verts(o)
    Nn = normals(o)
    grain = fbm(P * np.array((1, 1, 0.3)), 34.0, 3, seed)
    col = mix(BARK * 0.7, BARK * 1.7, smooth(0.35, 0.72, grain))
    lichen = smooth(0.58, 0.72, fbm(P, 11.0, 3, seed + 9))
    col = mix(col, mix(MOSS_A, CELADON, 0.3), lichen * 0.55)
    set_verts(o, P + Nn * (0.006 * (grain - 0.5))[:, None])
    paint(o, col, 0.85)


def paint_blossom(o):
    P = verts(o)
    Nn = normals(o)
    up = Nn[:, 2]
    d1, d2 = worley(P, 30.0, 3)
    flower = 1 - smooth(0.14, 0.46, d1)
    heart = 1 - smooth(0.0, 0.12, d1)
    clump = fbm(P, 9.0, 4, 2)
    d5, _ = worley(P, 17.0, 23)
    # lit from above: pale on the crown, deep rose in the hollows and beneath
    col = mix(ROSE, PINK, smooth(-0.6, 0.15, up + 1.0 * (clump - 0.5)))
    col = mix(col, BLUSH, smooth(0.15, 0.8, up + 0.8 * (clump - 0.5)) * 0.8)
    col = col * (0.72 + 0.28 * smooth(0.0, 0.6, flower))[:, None]
    col = mix(col, BLUSH, flower * smooth(-0.2, 0.3, up) * 0.75)
    col = mix(col, rgb(226, 150, 60), heart * 0.8)
    col = col * (1 - 0.3 * smooth(0.25, 0.6, d5))[:, None]
    disp = 0.012 * (clump - 0.5) + 0.0075 * flower - 0.012 * smooth(0.25, 0.65, d5)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, 0.72)


def paint_needles(o):
    P = verts(o)
    Nn = normals(o)
    up = Nn[:, 2]
    d1, d2 = worley(P * np.array((1, 1, 2.4)), 58.0, 5)
    tuft = smooth(0.0, 0.28, d2 - d1)
    clump = fbm(P, 12.0, 3, 8)
    col = mix(rgb(10, 34, 30), rgb(28, 78, 54), smooth(-0.5, 0.35, up + clump - 0.5))
    col = mix(col, rgb(78, 132, 76), smooth(0.2, 0.9, up + 0.8 * (clump - 0.5)) * tuft)
    set_verts(o, P + Nn * (0.010 * (clump - 0.5) + 0.005 * tuft)[:, None])
    paint(o, col, 0.78)


def paint_pavilion(o, roof_z, floor):
    P = verts(o)
    z = P[:, 2]
    x, y = SITES["pavilion"]
    a = np.maximum(np.abs(P[:, 0] - x), np.abs(P[:, 1] - y))
    is_roof = z > roof_z + 0.0085
    finial = z > roof_z + 0.09
    dx, dy = np.abs(P[:, 0] - x), np.abs(P[:, 1] - y)
    along_eave = np.where(dx > dy, P[:, 1] - y, P[:, 0] - x)
    tiles = np.sin(along_eave * 250) * 0.5 + 0.5
    roof = mix(rgb(16, 72, 66), rgb(46, 138, 112), tiles)
    roof = mix(roof, GOLD, np.maximum(smooth(0.148, 0.156, a), 1 - smooth(0.003, 0.0075, np.abs(dx - dy))))
    col = np.broadcast_to(rgb(198, 192, 168), (len(P), 3)).copy()      # the plinth
    pillars = (z > floor - 0.0035) & (a < 0.108) & ~is_roof      # (the plinth's own corners are further out)
    col[pillars] = rgb(176, 44, 34)
    col[is_roof] = roof[is_roof]
    col[finial] = GOLD
    metal = finial * 1.0
    rough = np.full(len(P), 0.5)
    rough[finial] = 0.3
    paint(o, col, rough, metal)


# ---------- the whole, high-detail ----------
def build_hi():
    pieces, data, frames = {}, {}, {}
    pieces["Shell"] = build_shell()
    paint_shell(pieces["Shell"])
    skin, body_only = build_skin()
    paint_skin(skin)
    pieces["Skin"] = skin
    pieces["Legs"] = skin       # (the game mesh's legs and tail are their own tubes, baked from the same skin)
    pieces["Tail"] = skin
    data["BodyOnly"] = body_only
    o, _ = build_claws(N + "ClawsHi", HI, 16, 1)
    P = verts(o)
    paint(o, mix(OLD_GOLD, IVORY, smooth(GROUND + 0.09, GROUND + 0.01, P[:, 2])), 0.34)
    pieces["Claws"] = o
    o = build_horns(N + "HornsHi", HI, 18, 1)
    paint_horns(o)
    pieces["Horns"] = o
    o = build_jaw(N + "JawHi", HI, 26, 14)
    P = verts(o)
    Nn = normals(o)
    col = mix(mix(JADE, DEEP, 0.2), CREAM, smooth(-0.1, -0.7, Nn[:, 2]))
    col = mix(col, mix(OLD_GOLD, CREAM, 0.55), smooth(-1.9, -1.99, P[:, 1]))
    col = mix(col, MOUTH, smooth(0.4, 0.75, Nn[:, 2]) * (1 - smooth(-1.98, -2.03, P[:, 1])))
    paint(o, col, 0.45)
    pieces["Jaw"] = o
    rib_rough = lambda u, v: np.full_like(u, 0.42)
    pieces["NeckSail"] = sheet_hi(neck_sail_point, sail_thick, 120, 30, N + "NeckSailHi", sail_colour, rib_rough, sail_relief)
    pieces["TailSail"] = sheet_hi(tail_sail_point, sail_thick, 140, 30, N + "TailSailHi", sail_colour, rib_rough, sail_relief)
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Frill" + tag] = sheet_hi(frill_point(side), frill_thick, 70, 40, N + "Frill" + tag + "Hi", frill_colour, rib_rough, lambda u, v: np.zeros_like(u))
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, mix(DEEP, JADE, 0.55), rgb(8, 22, 18))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, mix(DEEP, JADE, 0.7), rgb(8, 22, 18), lower_share=0.6)
    base, wood = plum_paths()
    o = build_wood(wood, N + "PlumHi", HI, 16)
    paint_wood(o, 61)
    pieces["Plum"] = o
    o = build_pads(PLUM_PADS, base, N + "BlossomHi", HI, 0.0052, 31)
    paint_blossom(o)
    pieces["Blossom"] = o
    pbase, pwood = pine_paths()
    o = build_wood(pwood, N + "PineHi", HI, 12)
    paint_wood(o, 67)
    pieces["Pine"] = o
    o = build_pads(PINE_PADS, pbase, N + "NeedlesHi", HI, 0.0052, 57)
    paint_needles(o)
    pieces["Needles"] = o
    o, roof_z, floor = pavilion(N + "PavilionHi", HI)
    paint_pavilion(o, roof_z, floor)
    pieces["Pavilion"] = o
    data["base"], data["pbase"] = base, pbase
    o = build_pool(tree_of(pieces["Shell"]), N + "PoolHi", HI, 96, 24)
    paint_pool(o)
    pieces["Pool"] = o
    glows = {"Glints": glints(frames, HI, "Glints_Glow_f0ead8", spots=((-20, 15, 0.0115, 12),))}
    glows["Spring"] = build_spring(tree_of(pieces["Shell"]), N + "Spring_Glow_24c0a4", HI, 60, 3, None)
    return pieces, frames, glows, data


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 1.2
        o.data.materials.append(m)
        o.visible_shadow = False


CLOSE_HEAD = (0.62, -0.78, 0.05, 2.0, (0, -1.85, 1.28))
CLOSE_GARDEN = (-0.25, -0.5, 0.85, 5.0, (0, 0.05, 1.3))
CLOSE_GARDEN2 = (0.55, -0.7, 0.42, 4.2, (0, -0.1, 1.3))
EXTRA = [CLOSE_HEAD, (0, -1, 0.04, 1.8, (0, -1.9, 1.26)), CLOSE_GARDEN, CLOSE_GARDEN2, (0.75, -0.6, 0.12, 3.0, (0.2, -1.0, 0.7)), (0.12, -1, 0.15, 0.9, (0, -2.06, 1.24)), (-0.5, -0.6, 0.45, 2.2, (-0.15, -0.3, 1.2)), (0.9, -0.1, 0.0, 2.6, (0.7, -0.6, 0.45))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi()
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    print("SITES", {k: round(terrain_at(*v), 3) for k, v in SITES.items()}, flush=True)
    stage_setup((0.40, 0.46, 0.46, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.09, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=11.0, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = (3000, 2800, 2600, 3200, 2400, 2200, 2000)
BLOSSOM_TRIS, NEEDLE_TRIS = 1000, 380
SHELL_NT, SHELL_RHO = 84, np.array((0.07, 0.15, 0.22, 0.29, 0.35, 0.40, 0.45, 0.50, 0.54, 0.58, 0.62, 0.66, 0.71, 0.76, 0.81, 0.86, 0.91, 0.95, 0.98, 1.0))
SHELL_LIP = ((1.012, 0.022), (1.0, 0.052), (0.92, 0.07))
# how much of the map each part gets, per metre: the shell and the head are what a player looks at
TEXELS = {"Shell": 1.0, "Legs": 0.62, "Tail": 0.62, "Claws": 0.9, "Horns": 0.9, "Jaw": 1.3, "NeckSail": 0.8, "TailSail": 0.8, "Plum": 0.7, "Blossom": 1.0, "Pine": 0.7, "Needles": 0.65, "Pavilion": 2.6, "Pool": 3.0, "FrillL": 1.1, "FrillR": 1.1,
          "EyeL": 5.0, "EyeR": 5.0, "LidUL": 1.5, "LidUR": 1.5, "LidLL": 1.5, "LidLR": 1.5}
META = {}


def shell_low(name):
    """The game mesh of the shell: a regular polar grid, so its polished plates shade smoothly, sampling the same surface blurred a little (its detail lives in the normal map), with its rim's lobes in step with the plates."""
    t = np.linspace(-math.pi, math.pi, SHELL_NT, endpoint=False)
    m = Mesh()
    bm = m.bm
    rows = []
    for rho in SHELL_RHO:
        tt = np.full(SHELL_NT, 0.0) + t
        total = np.zeros(SHELL_NT)
        reach, high = rim_shape(tt)
        count = 0
        for dt, dr in ((0, 0), (0.03, 0), (-0.03, 0), (0, 0.02), (0, -0.02), (0.015, 0.01), (-0.015, -0.01)):
            # no blur toward the rim: the dome falls steeply there, and a blurred ring sits so far inside the real surface that the bake's rays start behind it (a speckled band, seen)
            r1 = np.clip(rho + dr * (1 - float(smooth(0.8, 0.92, rho))), 0, 1)
            reach1, high1 = rim_shape(tt + dt)
            _, _, z = shell_height(tt + dt, np.full(SHELL_NT, r1), reach1, high1, plain=True)
            total += z
            count += 1
        z = total / count
        x = rho * reach * RA * np.cos(t)
        y = CY + rho * reach * RB * np.sin(t)
        rows.append([bm.verts.new((float(x[j]), float(y[j]), float(z[j]))) for j in range(SHELL_NT)])
    apex = bm.verts.new((0, CY, float(np.mean([terrain_at(0.04 * math.cos(a), CY + 0.04 * math.sin(a)) for a in np.linspace(0, TAU, 8)]))))
    reach, high = rim_shape(t)
    for rho, drop in SHELL_LIP:
        rows.append([bm.verts.new((rho * reach[j] * RA * math.cos(t[j]), CY + rho * reach[j] * RB * math.sin(t[j]), high[j] - drop)) for j in range(SHELL_NT)])
    for j in range(SHELL_NT):
        j2 = (j + 1) % SHELL_NT
        bm.faces.new((apex, rows[0][j], rows[0][j2]))
        for i in range(len(rows) - 1):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j2], rows[i][j2]))
    hub = bm.verts.new((0, CY, 0.60))
    for j in range(SHELL_NT):
        bm.faces.new((rows[-1][j], hub, rows[-1][(j + 1) % SHELL_NT]))
    o = m.finish(name, GAME)
    META["ShellRows"] = len(rows)
    return o


def shell_uv(o, density):
    """One clean island: the whole top laid out flat from the summit, each ring at its true distance down the slope. The underside gets a corner of its own."""
    me = o.data
    uv = me.uv_layers.active.data
    k = density
    P = verts(o)
    t = np.arctan2((P[:, 1] - CY) / RB, P[:, 0] / RA)
    reach, high = rim_shape(t)
    # distance down the slope from the summit, ring by ring (rows go round the shell in order)
    nt, nrows = SHELL_NT, len(SHELL_RHO)
    arc = np.zeros(len(P))
    grid = P[:nt * nrows].reshape(nrows, nt, 3)
    apex = P[nt * nrows]
    run = np.linalg.norm(grid[0] - apex, axis=1)
    arcs = [run.copy()]
    for i in range(1, nrows):
        run = run + np.linalg.norm(grid[i] - grid[i - 1], axis=1)
        arcs.append(run.copy())
    arcs = np.array(arcs)
    arc[:nt * nrows] = arcs.ravel()
    sn, cs = np.sin(t), np.cos(t)
    flat_x = 0.5 + arc * cs * k
    flat_y = 0.5 + arc * sn * k
    apex_i = nt * nrows
    flat_x[apex_i], flat_y[apex_i] = 0.5, 0.5
    # the lip and underside: nobody looks, so a small flat ring off to one side, each ring of it further in (in plan the lip folds back on itself, which would overlap)
    ring = np.ones(len(P))
    for i, r in enumerate((0.97, 0.94, 0.88)):
        ring[apex_i + 1 + i * nt:apex_i + 1 + (i + 1) * nt] = r
    ring[-1] = 0.0
    for poly in me.polygons:
        vs = list(poly.vertices)
        under = any(v > apex_i for v in vs)
        for l, v in zip(poly.loop_indices, vs):
            if under:
                uv[l].uv = (9.0 + ring[v] * cs[v] * RA * k * 0.6, 0.5 + ring[v] * sn[v] * RB * k * 0.6)
            else:
                uv[l].uv = (flat_x[v], flat_y[v])


def canopy_uv(o, density):
    """A canopy is all lumps, and at the usual angle it shatters into hundreds of islands. A wider angle keeps it in a few, with far fewer split vertices."""
    select_only([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    pet_kit.scale_uv_to(o, list(o.data.polygons), density)


def build_low(pieces, frames, data):
    # QuadriFlow can wreck a small form and leave the mesh checks green (a gash down the snout, seen on one run): try several, measure each against the sculpt, keep the truest, then lay it on the sculpt
    tree = tree_of(data["BodyOnly"])
    best, best_gap = None, 1e9
    for quads in SKIN_QUADS:
        o = retopo_skin(data["BodyOnly"], N + "SkinTry", quads)
        gap = surface_gap(o, tree)
        print("SKIN TRY", quads, len(o.data.polygons), "gap", round(gap, 4), flush=True)
        if gap < best_gap:
            if best:
                bpy.data.objects.remove(best, do_unlink=True)
            best, best_gap = o, gap
        else:
            bpy.data.objects.remove(o, do_unlink=True)
        if gap < 0.009:
            break
    assert best_gap < 0.016, "every re-mesh strayed from the sculpt"
    best.name = N + "SkinLow"
    for v in best.data.vertices:
        v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.8)
    # the head is small against this mesh's even density: rounding it a little takes the corners off its outline
    bm = bmesh.new()
    bm.from_mesh(best.data)
    head = [v for v in bm.verts if v.co.y < -1.56 and v.co.z > 1.02]
    bmesh.ops.smooth_vert(bm, verts=head, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for v in head:      # (but never far from the sculpt: the point of a beak or a brow must not melt)
        near, _, _, dist = tree.find_nearest(v.co)
        if dist > 0.006:
            v.co = near + (v.co - near).normalized() * 0.006
    bm.to_mesh(best.data)
    bm.free()
    lows = {"Skin": best}
    # the top of the body lies wholly inside the shell, in every pose: no faces there
    bm = bmesh.new()
    bm.from_mesh(lows["Skin"].data)
    hidden = []
    for f in bm.faces:
        c = f.calc_center_median()
        t = math.atan2((c.y - CY) / RB, c.x / RA)
        reach, high = rim_shape(np.array([t]))
        rho = math.sqrt((c.x / RA) ** 2 + ((c.y - CY) / RB) ** 2) / float(reach[0])
        if rho < 0.74 and c.z > float(high[0]) - 0.03:
            hidden.append(f)
    bmesh.ops.delete(bm, geom=hidden, context="FACES")
    # and any scrap of a few faces the cut left floating inside
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
        if len(group) < 100:
            scraps += group
    bmesh.ops.delete(bm, geom=scraps, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    print("SCRAP FACES CUT", len(scraps), flush=True)
    bm.to_mesh(lows["Skin"].data)
    bm.free()
    print("HIDDEN FACES CUT", len(hidden), flush=True)
    m = Mesh()
    rows = len(leg_path(1, FRONT)[::2])
    for key, side, knots in LEGS:
        m.tube(leg_path(side, knots)[::2], lambda f: leg_radius(f) + 0.003, sides=10, flat=0.96, plane=V(1, 0, 0))
    lows["Legs"] = m.finish(N + "LegsLow", GAME)
    META["LegRows"], META["LegSides"] = rows, 10
    m = Mesh()
    tail = TAIL[::3]
    if tail[-1] != TAIL[-1]:
        tail.append(TAIL[-1])
    m.tube(tail, lambda f: tail_radius(f) + 0.002, sides=9, flat=0.88, plane=V(1, 0, 0))
    lows["Tail"] = m.finish(N + "TailLow", GAME)
    lows["Claws"], META["Claws"] = build_claws(N + "ClawsLow", GAME, 5, 3)
    lows["Horns"] = build_horns(N + "HornsLow", GAME, 7, 3)
    lows["Jaw"] = build_jaw(N + "JawLow", GAME, 10, 3)
    lows["NeckSail"] = low_sheet(neck_sail_point, sail_thick, 12, 2, N + "NeckSailLow")
    lows["TailSail"] = low_sheet(tail_sail_point, sail_thick, 16, 2, N + "TailSailLow")
    lows["Shell"] = shell_low(N + "ShellLow")
    lows["Plum"] = build_wood(plum_paths()[1], N + "PlumLow", GAME, 6, 3)
    lows["Blossom"] = decimated(pieces["Blossom"], N + "BlossomLow", BLOSSOM_TRIS)
    lows["Pine"] = build_wood(pine_paths()[1], N + "PineLow", GAME, 5, 3)
    lows["Needles"] = decimated(pieces["Needles"], N + "NeedlesLow", NEEDLE_TRIS)
    lows["Pavilion"], _, _ = pavilion(N + "PavilionLow", GAME, low=True)
    lows["Pool"] = build_pool(tree_of(lows["Shell"]), N + "PoolLow", GAME, 14, 2)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Frill" + tag] = low_sheet(frill_point(side), frill_thick, 5, 3, N + "Frill" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 16, 10)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
NECK_NAMES = ["Neck1", "Neck2", "Neck3", "Neck4"]
NECK_F = (0.10, 0.36, 0.60, 0.82)
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)] + ["TailTip"]
TAIL_F = (0.12, 0.27, 0.42, 0.56, 0.70, 0.83, 0.94)
HEAD_AT = V(0, -1.60, 1.27)


def skeleton(frames, data):
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, CY, 0.55), "Root"), ("Shell", V(0, CY, 0.92), "Body")]
    parent = "Body"
    for name, f in zip(NECK_NAMES, NECK_F):
        bones.append((name, along(NECK, f)[0], parent))
        parent = name
    bones += [("Head", HEAD_AT.copy(), parent), ("Jaw", V(0, -1.62, 1.215), "Head")]
    parent = "Body"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, along(TAIL, f)[0], parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Frill" + tag, V(side * 0.135, -1.60, 1.245), "Head")]
    for key, side, knots in LEGS:
        bones += [("Leg%s1" % key, mir(knots[0], side), "Body"), ("Leg%s2" % key, mir(knots[1], side), "Leg%s1" % key), ("Foot" + key, mir(knots[2], side), "Leg%s2" % key)]
    b, w = data["base"], plum_paths()[1]
    bones += [("Plum1", b + V(0, 0, 0.02), "Shell"), ("Plum2", w[0][0][int(len(w[0][0]) * 0.62)], "Plum1")]
    for name, _, off, _ in PLUM_PADS:
        bones.append((name, b + V(*off), "Plum2"))
    pb = data["pbase"]
    bones.append(("Pine1", pb + V(0, 0, 0.02), "Shell"))
    for name, _, off, _ in PINE_PADS:
        bones.append((name, pb + V(*off), "Pine1"))
    return armature(bones)


def neck_weight(f):
    return chain_weight(["Body"] + NECK_NAMES, (0.0,) + NECK_F, f)


def skin_weights(o):
    P = verts(o)
    y, z = P[:, 1], P[:, 2]
    f, d = nearest_on(NECK, P)
    neck_on = smooth(-0.70, -0.92, y)
    head_on = smooth(-1.50, -1.60, y) * smooth(0.98, 1.06, z)
    out = []
    for i in range(len(P)):
        w = {"Body": 1.0}
        n = float(neck_on[i])
        if n > 0:
            w = {"Body": 1 - n}
            for b, v in neck_weight(float(f[i])).items():
                w[b] = w.get(b, 0) + v * n
        h = float(head_on[i])
        if h > 0:
            w = {b: v * (1 - h) for b, v in w.items()}
            w["Head"] = w.get("Head", 0) + h
        out.append(w)
    return out


LEG_KNOTS = (1 / 3, 2 / 3)


def leg_weight(key, f):
    names = ["Leg%s1" % key, "Leg%s2" % key, "Foot" + key]
    width = 0.085
    for j, knot in enumerate(LEG_KNOTS):
        if abs(f - knot) < width:
            s = float(smooth(knot - width, knot + width, f))
            return {names[j]: 1 - s, names[j + 1]: s}
    return {names[sum(1 for knot in LEG_KNOTS if f > knot)]: 1.0}


def path_owner(P, paths):
    """Per point: which of these paths it lies on, and how far along."""
    best, which, along_it = np.full(len(P), 1e9), np.zeros(len(P), dtype=int), np.zeros(len(P))
    for k, (path, _, _) in enumerate(paths):
        f, d = nearest_on(path, P)
        take = d < best
        best[take], which[take], along_it[take] = d[take], k, f[take]
    return which, along_it


def wood_weights(o, paths, trunk, pads):
    which, f = path_owner(verts(o), paths)
    out = []
    for k, t in zip(which, f):
        if k == 0:
            out.append(chain_weight(trunk, (0.25, 0.75), float(t)) if len(trunk) > 1 else {trunk[0]: 1.0})
        else:
            s = float(smooth(0.25, 1.0, t))
            out.append({trunk[-1]: 1 - s, pads[k - 1]: s})
    return out


def pad_weights(o, base, specs, stem):
    P = verts(o)
    fields = []
    for name, _, off, r in specs:
        c = np.array(tuple(base + V(*off)))
        fields.append((name, np.exp(-(np.linalg.norm(P - c, axis=1) / (max(r) * 1.1)) ** 2)))
    total = sum(fl for _, fl in fields) + 1e-6
    out = []
    for i in range(len(P)):
        w = {stem: 0.12}
        for name, fl in fields:
            w[name] = 0.88 * float(fl[i] / total[i])
        out.append(w)
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    rows, sides = META["LegRows"], META["LegSides"]
    leg = []
    for key, _, _ in LEGS:
        for i in range(rows):
            leg += [leg_weight(key, i / (rows - 1))] * sides
    weigh(lows["Legs"], leg)
    tf, _ = nearest_on(TAIL, verts(lows["Tail"]))
    weigh(lows["Tail"], [chain_weight(["Body"] + TAIL_NAMES, (0.0,) + TAIL_F, float(f)) for f in tf])
    ns, _ = nearest_on(NECK, verts(lows["NeckSail"]))
    weigh(lows["NeckSail"], [neck_weight(float(f)) for f in ns])
    ts, _ = nearest_on(TAIL, verts(lows["TailSail"]))
    weigh(lows["TailSail"], [chain_weight(["Body"] + TAIL_NAMES, (0.0,) + TAIL_F, float(f)) for f in ts])
    keys = [key for key, *_ in LEGS]
    weigh(lows["Claws"], [{"Foot" + keys[int(i)]: 1.0} for i in META["Claws"]])
    for key in ("FrillL", "FrillR", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Jaw"):
        rigid(lows[key], key)
    rigid(lows["Horns"], "Head")
    for key in ("Shell", "Pavilion", "Pool"):
        rigid(lows[key], "Shell")
    weigh(lows["Plum"], wood_weights(lows["Plum"], plum_paths()[1], ["Plum1", "Plum2"], [p[0] for p in PLUM_PADS]))
    weigh(lows["Blossom"], pad_weights(lows["Blossom"], data["base"], PLUM_PADS, "Plum2"))
    pine = pine_paths()[1]
    # pine: its trunk on Pine1, and each lower bough to the pad it carries; the top pad sits on the trunk's end
    which, f = path_owner(verts(lows["Pine"]), pine)
    wood = []
    for k, t in zip(which, f):
        if k == 0:
            s = float(smooth(0.72, 1.0, t))
            wood.append({"Pine1": 1 - s, "PineA": s})
        else:
            s = float(smooth(0.25, 1.0, t))
            wood.append({"Pine1": 1 - s, ("PineC" if k == 1 else "PineB"): s})
    weigh(lows["Pine"], wood)
    weigh(lows["Needles"], pad_weights(lows["Needles"], data["pbase"], PINE_PADS, "Pine1"))
    rigid(glows["Spring"], "Shell")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes (+X turn: a limb's far end swings forward; +Y: turns to its left; +Z rolls), the same numbers its animation uses
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """CFrame.Angles(rx, ry, rz) in the game's axes, as this kit poses it."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


TREAD = {"FL": 0.0, "BR": 0.35, "FR": math.pi, "BL": math.pi + 0.35}


def tread(stride=0.0, moving=1.0, fly=0.0, stroke=0.0, raise_=0.0):
    """The same numbers PetRig's animateJadeWyrmTurtle gives its legs."""
    out = {}
    for key, lead in TREAD.items():
        phase = stride + lead
        a, lift = math.sin(phase), moving * max(0.0, math.cos(phase)) ** 1.4
        sign = -1 if key[1] == "L" else 1
        swing, out_z, bend, foot = moving * 0.3 * a, 0.26 * lift, -0.44 * lift, -moving * 0.3 * a * 0.9 - 0.14 * lift
        if key[0] == "F":
            swing += fly * (0.06 + 0.5 * stroke)
            out_z += fly * (0.34 + 0.12 * stroke)
            bend += fly * 0.26
            foot += fly * (0.16 * stroke - 0.62)
        else:
            swing += fly * (-0.52 + 0.14 * stroke)
            out_z += fly * 0.2
            bend += fly * 0.12
            foot += fly * -0.5
        if key == "FR":
            swing += 0.14 * raise_
            out_z += 0.62 * raise_
            bend -= 0.96 * raise_
            foot += 0.32 * raise_
        out["Leg%s1" % key] = game_turn(swing, 0, sign * out_z)
        out["Leg%s2" % key] = game_turn(0, 0, sign * bend)
        out["Foot" + key] = game_turn(foot, 0, 0)
    return out


def pose_library(frames):
    def turn(axis, deg):
        return (axis, deg, (0, 0, 0))

    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    # the special's two moments: all the numbers from the animation at raise = 1, and at plant = 1
    lift = 0.2
    raised = {**tread(moving=0.0, raise_=1.0), "Body": game_turn(0.1, 0, 0.1, (0, 0, 0.13)), "Neck1": game_turn(lift * 0.8, 0, -0.06), "Neck2": game_turn(lift, 0, -0.04), "Neck3": game_turn(lift * 0.7, 0, 0), "Neck4": game_turn(-lift * 0.3, 0, 0), "Head": game_turn(-lift * 0.55, 0, 0), "Jaw": game_turn(-0.14, 0, 0)}
    planted = {"Body": game_turn(-0.05, 0, 0, (0, 0, -0.025)), "Neck1": game_turn(-0.08, 0, 0), "Neck2": game_turn(-0.1, 0, 0), "Neck3": game_turn(-0.07, 0, 0), "Neck4": game_turn(0.03, 0, 0), "Head": game_turn(0.055, 0, 0), "Jaw": game_turn(-0.24, 0, 0), **lids(BLINK_U, BLINK_L), "PadA": ((0, 0, 1), 0, (0.03, -0.04, 0.012)), "PadB": ((0, 0, 1), 0, (-0.033, -0.015, 0.012)), "PadC": ((0, 0, 1), 0, (0, 0.012, 0.055))}
    swim_a = {**tread(moving=0.0, fly=1.0, stroke=1.0), "Body": game_turn(0.12, 0, 0, (0, 0, 0.05)), "Neck1": game_turn(-0.17, 0, 0), "Neck2": game_turn(-0.2, 0, 0), "Neck3": game_turn(-0.06, 0, 0), "Neck4": game_turn(0.14, 0, 0), "Head": game_turn(0.17, 0, 0)}
    swim_b = {**tread(moving=0.0, fly=1.0, stroke=-1.0), "Body": game_turn(0.06, 0, 0, (0, 0, 0.05))}
    look = {"Neck1": game_turn(0, 0.28, 0), "Neck2": game_turn(0, 0.42, 0), "Neck3": game_turn(0, 0.45, 0), "Neck4": game_turn(0, 0.31, 0), "Head": game_turn(0, 0.28, 0)}
    look_r = {"Neck1": game_turn(0, -0.28, 0), "Neck2": game_turn(0, -0.42, 0), "Neck3": game_turn(0, -0.45, 0), "Neck4": game_turn(0, -0.31, 0), "Head": game_turn(0, -0.28, 0)}
    tail = {("Tail%d" % k): game_turn(0, (0.035 + 0.04 * k / 6) * 1.7 * (-1) ** k * 1.0, 0) for k in range(1, 7)}
    plum = {"Plum1": game_turn(0.03, 0, 0.03), "Plum2": game_turn(0.04, 0.02, 0.05), "PadA": ((0, 0, 1), 0, (0.012, -0.02, 0.008)), "PineA": game_turn(0.03, 0, 0.03), "PineB": game_turn(0.03, 0, -0.03), "PineC": game_turn(-0.03, 0, 0.03)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Jaw": {"Jaw": game_turn(-0.24, 0, 0)}, "Step0": tread(0.0), "Step1": tread(0.9), "Step2": tread(1.9), "Raised": raised, "Planted": planted, "SwimA": swim_a, "SwimB": swim_b, "LookL": look, "LookR": look_r, "Tail": tail, "Plum": plum}


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.09, ao_share=0.5)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.40, 0.46, 0.46, 1))
    lows = build_low(pieces, frames, data)
    gap = surface_gap(lows["Skin"], tree_of(data["BodyOnly"]))
    print("SKIN GAP", round(gap, 4), flush=True)
    assert gap < 0.012, "the re-mesh strayed from the sculpt"
    print("SHELL GAP", round(surface_gap(lows["Shell"], tree_of(pieces["Shell"])), 4), "BLOSSOM GAP", round(surface_gap(lows["Blossom"], tree_of(pieces["Blossom"])), 4), flush=True)
    # the spring lies on the game mesh itself, so nothing of it sinks into a re-meshed rock
    material = glows["Spring"].data.materials[0]
    bpy.data.objects.remove(glows["Spring"], do_unlink=True)
    glows["Spring"] = build_spring(tree_of(lows["Shell"]), N + "Spring_Glow_24c0a4", HI, 26, 1, None)
    glows["Spring"].data.materials.append(material)
    glows["Spring"].visible_shadow = False
    unwrap(lows, [(lambda p: p.center.y < -1.5 and p.center.z > 1.0, 1.7), (None, 0.72)], {}, shape="CONCAVE", angle=52, own_uv={"Shell": shell_uv, "Blossom": canopy_uv, "Needles": canopy_uv}, texels=TEXELS, margin=0.006)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.04, 0.18, 0.14, 1), far=("Skin", "Legs", "Tail", "Shell", "Blossom", "Needles"), far_reach=(0.018, 0.055), reaches={"Shell": (0.05, 0.11), "Pool": (0.09, 0.2)})
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
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=11.0, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    wide = (0.72, -0.62, 0.18, 9.5, VIEW_AT)
    for name, view in (("Blink", CLOSE_HEAD), ("Jaw", CLOSE_HEAD), ("Step0", wide), ("Step1", wide), ("Raised", wide), ("Planted", wide), ("SwimA", wide), ("SwimB", wide), ("LookL", (0.5, -0.6, 0.7, 7.0, (0, -0.4, 1.1))), ("LookR", (-0.5, -0.6, 0.7, 7.0, (0, -0.4, 1.1))), ("Tail", (0, 0.1, 1, 9.0, (0, 0.8, 0.8))), ("Plum", (0.6, -0.7, 0.3, 5.0, (0.2, -0.3, 1.5)))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 9.0, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

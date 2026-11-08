"""The Nameless One (Secret, Unknown cosmic energy; Forbidden Origin Egg, also in the Void Rift and Primordial Abyss Eggs): "Every name it was given has been
forgotten by whoever gave it. This page keeps trying to write something down."

Not an animal. A tall, upright figure with no legs, floating: high square shoulders, a narrow waist, long thin arms hanging past it, and a hooded head that leans a
little forward. Its body is nothing: a matte indigo-black core with no light in it, wound in loose pale ribbons. Straps cross its chest and go over its shoulders, a band
circles the chest, spirals wind round the waist, and below the waist the ribbons leave it as six ragged streamers. Its arms are bandaged tight, and from each wrist two
loose ribbon ends hang where a hand would be; their tips glow, the ends that write. It has no face: the front of the hood is a deep oval hollow, and inside it one small
point of white light floats. Behind its head hangs a thin octagonal halo with one side missing. Every ribbon carries one line of large handwriting in faded violet ink,
some words struck through, some almost erased.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/the_nameless_one.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, the streamers' tips just above z = 0. +X is its left. The maps go to assets/pets/ForbiddenOriginEgg/.

What touches what: core, neck, head and arms are one fused skin. Each ribbon is its own closed sheet lying on the skin at its own height, so ribbons that cross never touch;
the streamers start under the waist's spirals, the wrist ribbons inside the wrists. The light floats in the hollow, the halo behind the head: both float on purpose.
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
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "TheNamelessOne"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ForbiddenOriginEgg")
STEP = 0.003 if STAGE == "clay" else 0.0012          # the high-detail ribbons' vertex spacing: fine enough to carry the handwriting
THICK = 0.0022                                       # every ribbon's thickness

# ---------- colours: nothing, paper and faded ink ----------
NOTHING, NOTHING_LIFT, HOLLOW = rgb(18, 14, 38), rgb(34, 26, 66), rgb(3, 2, 8)
PAPER, PAPER_SHADE, EDGE = rgb(230, 226, 240), rgb(198, 192, 220), rgb(200, 182, 255)
INK, INK_DARK = rgb(112, 98, 150), rgb(52, 40, 90)

# ---------- the frame of it ----------
# the core, bottom to top: height, half-width, half-depth, how far its middle sits back (+) or forward (-)
CORE = ((0.20, 0.02, 0.02, 0.0), (0.235, 0.068, 0.062, 0.0), (0.32, 0.097, 0.081, 0.0), (0.42, 0.094, 0.076, 0.0), (0.52, 0.083, 0.069, 0.0), (0.62, 0.1, 0.075, 0.0),
        (0.71, 0.134, 0.083, 0.004), (0.79, 0.164, 0.086, 0.006), (0.84, 0.178, 0.083, 0.006), (0.872, 0.156, 0.07, 0.004), (0.9, 0.082, 0.054, -0.004),
        (0.93, 0.048, 0.045, -0.012), (0.975, 0.045, 0.045, -0.022))
HEAD = V(0, -0.032, 1.05)
HEAD_R = (0.08, 0.09, 0.112)
HOLLOW_AT, HOLLOW_HALF, HOLLOW_DEPTH = 1.04, (0.05, 0.07), 0.056        # the hollow's middle height, its half-width and half-height, its depth
ARM = [V(0.162, 0.0, 0.818), V(0.205, -0.01, 0.73), V(0.222, -0.018, 0.63), V(0.225, -0.04, 0.53), V(0.22, -0.062, 0.44)]      # left arm: shoulder, elbow at [2], wrist
WRIST = V(0.22, -0.066, 0.418)
HALO_AT, HALO_R, HALO_GAP = V(0, 0.085, 1.075), 0.165, 1     # its middle, its corners' radius, the side that is missing


def prof(knots, f, k):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, k]))


def core_at(z):
    return prof(CORE, z, 1), prof(CORE, z, 2), prof(CORE, z, 3)


# ---------- the skin ----------
def loft_core(m):
    rows, nt = 150, 72
    z0, z1 = CORE[0][0], CORE[-1][0]
    grid = []
    for i in range(rows):
        z = z0 + (z1 - z0) * i / (rows - 1)
        W, D, yc = core_at(z)
        ring = []
        for j in range(nt):
            th = TAU * j / nt
            s, c = math.sin(th), math.cos(th)
            x = W * math.copysign(abs(s) ** 0.85, s)
            y = yc - D * math.copysign(abs(c) ** 0.85, c)
            ring.append(m.bm.verts.new((x, y, z)))
        grid.append(ring)
    bottom = m.bm.verts.new((0, 0, z0 - 0.004))
    top = m.bm.verts.new((0, core_at(z1)[2], z1 + 0.004))
    for j in range(nt):
        j2 = (j + 1) % nt
        m.bm.faces.new((bottom, grid[0][j2], grid[0][j]))
        for i in range(rows - 1):
            m.bm.faces.new((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
        m.bm.faces.new((grid[-1][j], grid[-1][j2], top))


def build_head(m):
    """A hood: the skull's egg, a fuller crown, the hood falling behind to the neck, and its point drooping back."""
    m.ball(HEAD, HEAD_R, 56, 36)
    m.ball(HEAD + V(0, 0.03, 0.065), (0.068, 0.082, 0.085), 48, 30)
    m.ball(HEAD + V(0, 0.055, -0.05), (0.074, 0.07, 0.078), 48, 30)
    tip = [HEAD + V(0, 0.02, 0.12), HEAD + V(0, 0.07, 0.15), HEAD + V(0, 0.12, 0.145), HEAD + V(0, 0.155, 0.12)]
    m.tube(catmull(tip, 10), lambda f: 0.042 * (1 - f) ** 1.2 + 0.006, sides=24)


def carve_hollow(o):
    """The face: an oval pushed deep into the front of the hood, steep-walled, its floor a bowl."""
    P = verts(o)
    hx, hz = HOLLOW_HALF
    e2 = (P[:, 0] / hx) ** 2 + ((P[:, 2] - HOLLOW_AT) / hz) ** 2
    front = P[:, 1] < HEAD.y - 0.03
    k = np.where(front & (e2 < 1), np.clip(1 - e2, 0, 1) ** 0.3, 0.0)
    P[:, 1] += HOLLOW_DEPTH * k
    set_verts(o, P)


def build_core(name, coll, head_only=False):
    """Core, neck and hooded head, without the arms: what the ribbons are laid on. head_only: the hood alone and uncut, for the head's ribbons, so a band
    passing the hollow's rim spans it rather than folding into it."""
    m = Mesh()
    if not head_only:
        loft_core(m)
    build_head(m)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    if not head_only:
        carve_hollow(o)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def arm_path(side, per=10):
    return catmull([mir(p, side) for p in ARM], per)


def build_skin(core, name, coll):
    """The core with both arms fused on: long, thin, bandaged, each ending in a small knot of wrist."""
    m = Mesh()
    m.bm.from_mesh(core.data)
    for side in (1, -1):
        m.tube(arm_path(side), lambda f: 0.031 - 0.012 * f + 0.004 * math.exp(-((f - 0.5) / 0.08) ** 2), sides=28)
        m.ball(mir(WRIST, side), (0.019, 0.02, 0.024), 32, 20)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 3})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the ribbons ----------
LAYER = {1: 0.0035, 2: 0.0075, 3: 0.0115, 4: 0.0155}      # how high a ribbon's middle lies off the skin: 4 mm a layer, so two never touch

# round the body: (height, degrees round from the front, + to its left)
WRAPS = {
    "StrapL": dict(knots=[(0.43, -40), (0.53, -14), (0.63, 8), (0.74, 30), (0.84, 46), (0.885, 70), (0.86, 112), (0.8, 150), (0.72, 178), (0.62, 205)], width=0.05),
    "StrapR": dict(knots=[(0.43, 40), (0.53, 14), (0.63, -8), (0.74, -30), (0.84, -46), (0.885, -70), (0.86, -112), (0.8, -150), (0.72, -178), (0.62, -205)], width=0.05),
    "Chest": dict(knots=[(0.66, 70), (0.69, 120), (0.715, 180), (0.725, 240), (0.71, 300), (0.69, 360), (0.675, 420), (0.665, 445)], width=0.056),
    "Waist": dict(knots=[(0.27, -20), (0.31, 40), (0.36, 100), (0.41, 160), (0.46, 220), (0.51, 280), (0.56, 340), (0.6, 380)], width=0.055),
    "Ribs": dict(knots=[(0.47, 200), (0.5, 250), (0.53, 300), (0.56, 350), (0.58, 400), (0.6, 450)], width=0.05),
    "Skirt": dict(knots=[(0.25, 150), (0.27, 90), (0.29, 30), (0.31, -30), (0.33, -90), (0.36, -150), (0.39, -210), (0.42, -250)], width=0.05),
}
# round the head: (degrees up from the hollow's level, degrees round from the front)
HEAD_WRAPS = {
    "Brow": dict(knots=[(28, 80), (40, 52), (47, 20), (48, 0), (47, -20), (40, -52), (28, -80), (20, -130), (16, -180), (20, -230), (26, -275), (30, -292)], width=0.042),
    "Chin": dict(knots=[(-18, 100), (-40, 66), (-58, 32), (-66, 0), (-58, -32), (-40, -66), (-18, -100), (-4, -150), (2, -200), (-6, -250), (-14, -268)], width=0.04),
    "Crown": dict(knots=[(4, 92), (34, 100), (62, 125), (78, 175), (66, 225), (40, 250), (14, 262)], width=0.04),
}
HEM_ANGLES = (22, 68, 112, 158, 202, 248, 292, 338)
HEM_DROP = (0.035, 0.07, 0.012, 0.05, 0.0, 0.06, 0.02, 0.075)       # how far above the ground each streamer's tip hangs: a ragged hem


def resample(C, Nr, step):
    """A polyline and its normals, at even spacing."""
    C = np.array([tuple(p) for p in C])
    Nr = np.array([tuple(n) for n in Nr])
    seg = np.linalg.norm(C[1:] - C[:-1], axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = float(s[-1])
    n = max(2, int(math.ceil(L / step)))
    t = np.linspace(0, L, n + 1)
    out = np.stack([np.interp(t, s, C[:, k]) for k in range(3)], 1)
    nr = np.stack([np.interp(t, s, Nr[:, k]) for k in range(3)], 1)
    nr /= np.linalg.norm(nr, axis=1)[:, None]
    return out, nr, t


def ribbon_grid(C, Nr, width, layer, tree, keep_off, step, hug=True, push=True, twist=None, across=None):
    """The middle surface of a ribbon: rows along it, columns across. width(f), layer(f): in metres at fraction f along. hug: laid onto the skin
    across its whole width (rays down its normal, onto tree); push: nothing sinks below its layer off keep_off (the whole skin). Returns the grid and each row's distance along it."""
    C, Nr, s = resample(C, Nr, step)
    L = s[-1]
    f = s / L
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    A = np.cross(Nr, T)
    A /= np.linalg.norm(A, axis=1)[:, None]
    if twist is not None:
        a = np.array([twist(x) for x in f])[:, None]
        A = A * np.cos(a) + np.cross(T, A) * np.sin(a)
    w = np.array([width(x) for x in f])
    nv = across or max(2, int(math.ceil(w.max() / step)))
    v = np.linspace(-0.5, 0.5, nv + 1)
    G = C[:, None, :] + A[:, None, :] * (w[:, None, None] * v[None, :, None])
    lay = np.array([layer(x) for x in f])
    if hug or push:
        for i in range(G.shape[0]):
            n = Vector(Nr[i])
            for j in range(G.shape[1]):
                p = Vector(G[i, j])
                if hug:
                    loc, nrm, _, _ = tree.ray_cast(p + n * 0.04, -n, 0.1)
                    if loc is not None:
                        p = loc + nrm * lay[i]
                if push:
                    loc, nrm, _, d = keep_off.find_nearest(p)
                    if loc is not None and (p - loc).dot(nrm) < lay[i]:
                        p = loc + nrm * lay[i]
                G[i, j] = tuple(p)
    return G, s, w


def sheet_mesh(G, thick, name, coll):
    """A closed blade round a grid of middle-surface points. Returns the object and, per vertex, its row and column."""
    nu, nv = G.shape[0] - 1, G.shape[1] - 1
    du = np.gradient(G, axis=0)
    dv = np.gradient(G, axis=1)
    nrm = np.cross(du, dv)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=2), 1e-12)[..., None]
    top = (G + nrm * (thick / 2)).reshape(-1, 3)
    bot = (G - nrm * (thick / 2)).reshape(-1, 3)
    P = np.concatenate([top, bot])
    K = (nu + 1) * (nv + 1)

    def t(i, j):
        return i * (nv + 1) + j

    def b(i, j):
        return K + i * (nv + 1) + j
    faces = []
    for i in range(nu):
        for j in range(nv):
            faces.append((t(i, j), t(i + 1, j), t(i + 1, j + 1), t(i, j + 1)))
            faces.append((b(i, j + 1), b(i + 1, j + 1), b(i + 1, j), b(i, j)))
    for i in range(nu):
        faces.append((t(i, 0), b(i, 0), b(i + 1, 0), t(i + 1, 0)))
        faces.append((t(i + 1, nv), b(i + 1, nv), b(i, nv), t(i, nv)))
    for j in range(nv):
        faces.append((t(0, j + 1), b(0, j + 1), b(0, j), t(0, j)))
        faces.append((t(nu, j), b(nu, j), b(nu, j + 1), t(nu, j + 1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(P.tolist(), [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    ii, jj = np.meshgrid(np.arange(nu + 1), np.arange(nv + 1), indexing="ij")
    rows = np.concatenate([ii.ravel(), ii.ravel()])
    cols = np.concatenate([jj.ravel(), jj.ravel()])
    return o, rows, cols


def wrap_path(knots, tree, per=24):
    """Round the core: each knot is cast onto it from outside, level with it."""
    C, Nr = [], []
    for q in catmull([V(z, math.radians(th), 0) for z, th in knots], per):
        z, th = q.x, q.y
        W, D, yc = core_at(z)
        d = V(math.sin(th), -math.cos(th), 0)
        loc, nrm, _, _ = tree.ray_cast(V(0, yc, z) + d * 0.5, -d, 0.6)
        C.append(loc)
        Nr.append(nrm)
    return C, Nr


def head_path(knots, tree, per=24):
    """Round the hood: each knot is cast onto it from outside, toward the head's middle."""
    C, Nr = [], []
    mid = V(0, HEAD.y, HOLLOW_AT)
    for q in catmull([V(math.radians(el), math.radians(az), 0) for el, az in knots], per):
        el, az = q.x, q.y
        d = V(math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el))
        loc, nrm, _, _ = tree.ray_cast(mid + d * 0.5, -d, 0.6)
        C.append(loc)
        Nr.append(nrm)
    return C, Nr


def hem_path(k, tree):
    """A streamer: laid down the core from under the waist's spirals, then hanging free, out and down, curling a little round."""
    th = math.radians(HEM_ANGLES[k])
    d = V(math.sin(th), -math.cos(th), 0)
    t = V(0, 0, 1).cross(d)
    C, Nr = [], []
    for z in (0.33, 0.295, 0.26):
        W, D, yc = core_at(z)
        loc, nrm, _, _ = tree.ray_cast(V(0, yc, z) + d * 0.5, -d, 0.6)
        C.append(loc)
        Nr.append(nrm)
    end = HEM_DROP[k]
    curl = 1 if k % 2 else -1
    for r, z, s in ((0.102, 0.215, 0.006), (0.136, 0.165, 0.02), (0.172, 0.1 + end * 0.6, 0.04), (0.205, 0.05 + end, 0.066), (0.225, 0.04 + end * 1.1, 0.085)):
        C.append(d * r + t * (s * curl) + V(0, 0, z))
        Nr.append(d)
    pts = catmull([Vector(p) for p in C], 12)
    nrs = catmull([Vector(n) for n in Nr], 12)
    return pts, nrs


def scarf_path(side, tree):
    """A loose end over each shoulder: lying on the back of the shoulder, then lifting off it, weightless, rising beside the halo and curling over."""
    C, Nr = [], []
    for z, th in ((0.8, 150), (0.845, 128)):
        W, D, yc = core_at(z)
        d = V(math.sin(math.radians(th)) * side, -math.cos(math.radians(th)), 0)
        loc, nrm, _, _ = tree.ray_cast(V(0, yc, z) + d * 0.5, -d, 0.6)
        C.append(loc + nrm * LAYER[1])
        Nr.append(nrm)
    for p, n in ((V(0.11, 0.115, 0.885), V(0.3, 1, 0.6)), (V(0.15, 0.17, 0.95), V(0.5, 1, 0.1)), (V(0.19, 0.22, 1.03), V(0.8, 0.8, -0.1)), (V(0.235, 0.255, 1.1), V(1, 0.5, -0.2)),
                 (V(0.29, 0.27, 1.15), V(0.9, 0.3, -0.5)), (V(0.345, 0.265, 1.17), V(0.5, 0.2, -1))):
        C.append(mir(p, side))
        Nr.append(mir(n.normalized(), side))
    return catmull([Vector(p) for p in C], 12), catmull([Vector(n) for n in Nr], 12)


TAIL_PATHS = {      # the left wrist's two loose ends, from inside the wrist
    "a": [V(0.226, -0.07, 0.418), V(0.234, -0.086, 0.36), V(0.248, -0.108, 0.29), V(0.258, -0.12, 0.22), V(0.256, -0.112, 0.15), V(0.246, -0.096, 0.11)],
    "b": [V(0.214, -0.064, 0.418), V(0.207, -0.076, 0.355), V(0.198, -0.09, 0.285), V(0.192, -0.094, 0.215), V(0.196, -0.086, 0.16)],
}
QUILL = 0.8          # where along a wrist ribbon its glowing tip begins


def tail_path(key, side):
    pts = catmull([mir(p, side) for p in TAIL_PATHS[key]], 12)
    out = []
    for i in range(len(pts)):
        tan = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        out.append((V(0, -1, 0) - tan * tan.y).normalized())       # its flat face turned forward
    return pts, out


UNDER = ["Chest", "Ribs", "Skirt", "Waist", "StrapL", "StrapR"]       # the order they were wound in, first underneath
HEAD_UNDER = ["Chin", "Brow", "Crown"]
LAYERS = {}


def assign_layers(trees):
    """Which layer each wound ribbon lies on: the lowest that no ribbon it crosses already takes, wound in the order above. The streamers' and scarves'
    roots lie on the skin first, under everything."""
    def overlap(a, b):
        A = np.array([tuple(p) for p in a[0]])
        Bp = np.array([tuple(p) for p in b[0]])
        d = np.linalg.norm(A[:, None, :] - Bp[None, :, :], axis=2).min()
        return d < (a[1] + b[1]) / 2 + 0.004
    placed = {}
    for k in range(len(HEM_ANGLES)):
        placed["Hem%d" % k] = ((hem_path(k, trees["core"])[0][:25], 0.06), 1)
    for side, tag in ((1, "L"), (-1, "R")):
        placed["Scarf" + tag] = ((scarf_path(side, trees["core"])[0][:16], 0.05), 1)
    for group, tree, paths in ((UNDER, trees["core"], lambda key: wrap_path(WRAPS[key]["knots"], tree, 8)[0]), (HEAD_UNDER, trees["head"], lambda key: head_path(HEAD_WRAPS[key]["knots"], trees["head"], 8)[0])):
        for key in group:
            me = (paths(key), (WRAPS.get(key) or HEAD_WRAPS[key])["width"])
            taken = {lay for (other, lay) in placed.values() if overlap(me, other)}
            free = [l for l in LAYER if l not in taken]
            assert free, "%s crosses a ribbon on every layer" % key
            LAYERS[key] = min(free)
            placed[key] = (me, LAYERS[key])
    print("LAYERS", LAYERS, flush=True)


def ribbon_specs(trees):
    """Every ribbon: (key, centre points, normals, width(f), layer(f), hug, push, twist, the tree it is laid on)."""
    specs = []
    tree, head_tree = trees["core"], trees["head"]
    if not LAYERS:
        assign_layers(trees)
    for key, r in WRAPS.items():
        C, Nr = wrap_path(r["knots"], tree)
        W, lay = r["width"], LAYER[LAYERS[key]]
        specs.append((key, C, Nr, lambda f, W=W: W * (0.6 + 0.4 * min(float(smooth(0, 0.05, f)), float(smooth(1, 0.95, f)))), lambda f, lay=lay: lay, True, True, None, tree))
    for key, r in HEAD_WRAPS.items():
        C, Nr = head_path(r["knots"], head_tree)
        W, lay = r["width"], LAYER[LAYERS[key]]
        specs.append((key, C, Nr, lambda f, W=W: W * (0.6 + 0.4 * min(float(smooth(0, 0.06, f)), float(smooth(1, 0.94, f)))), lambda f, lay=lay: lay, True, True, None, head_tree))
    for k in range(len(HEM_ANGLES)):
        C, Nr = hem_path(k, tree)
        twist = (0.6 if k % 2 else -0.6)
        specs.append(("Hem%d" % k, C, Nr, lambda f: 0.058 - 0.026 * f, lambda f: LAYER[1], False, True, lambda f, tw=twist: tw * float(smooth(0.3, 1, f)), tree))
    for side, tag in ((1, "L"), (-1, "R")):
        C, Nr = scarf_path(side, tree)
        specs.append(("Scarf" + tag, C, Nr, lambda f: 0.048 - 0.016 * f, lambda f: LAYER[1], False, True, lambda f, s=side: 0.35 * s * math.sin(math.pi * f), tree))
    for side, tag in ((1, "L"), (-1, "R")):
        for key in TAIL_PATHS:
            C, Nr = tail_path(key, side)
            specs.append(("Tail" + tag + key, C, Nr, lambda f: 0.025 - 0.01 * f, lambda f: 0.0, False, False, lambda f, s=side, a=(0.4 if key == "a" else -0.3): a * s * f, None))
    return specs


LOW_STEP = {"Tail": 0.018, "Hem": 0.022, "Scarf": 0.022}      # the game mesh's rows along a ribbon: closer where it bends with its bones; 2.8 cm on the body, 2.2 on the head


def low_step(key):
    return next((v for k, v in LOW_STEP.items() if key.startswith(k)), 0.022 if key in HEAD_WRAPS else 0.028)


def build_ribbons(trees, coll, step, low=False):
    """Every ribbon as its own closed sheet (low: the game's, two columns across). The wrist ribbons' tips are cut off into glow pieces.
    Returns {key: (object, rows, cols, grid, s, widths, laid on the skin)} and the tips' grids."""
    out, tips = {}, {}
    for key, C, Nr, width, layer, hug, push, twist, on in ribbon_specs(trees):
        G, s, w = ribbon_grid(C, Nr, width, layer, on, trees["skin"], low_step(key) if low else step, hug, push, twist, across=2 if low else None)
        if key.startswith("Tail"):
            cut = int(np.searchsorted(s / s[-1], QUILL))
            # the glowing tip starts 0.6 mm past the paper's last row: touching, never sharing a face with it
            k = 0.0006 / max(float(s[cut] - s[cut - 1]), 1e-6)
            tg, ts, tw = G[cut - 1:].copy(), s[cut - 1:].copy(), w[cut - 1:].copy()
            tg[0] = G[cut - 1] + (G[cut] - G[cut - 1]) * k
            ts[0] = s[cut - 1] + (s[cut] - s[cut - 1]) * k
            tw[0] = w[cut - 1] + (w[cut] - w[cut - 1]) * k
            tips[key] = (tg, ts, tw)
            G, s, w = G[:cut], s[:cut], w[:cut]
        o, rows, cols = sheet_mesh(G, THICK, N + key + ("Low" if low else "Hi"), coll)
        out[key] = (o, rows, cols, G, s, w, hug)
    return out, tips


# ---------- paint ----------
SCRIPT_RES = 0.00025       # the handwriting is drawn at a quarter of a millimetre a pixel


def script_canvas(length, height, seed):
    """One line of large flowing handwriting along a ribbon, in metres: ink (0..1, how dark), strike (the lines through some words). Words in a hand nobody
    can read: loops of a pen (a trochoid per letter, some tall, some dropping below the line), leaning; some words struck through, some faded, some almost gone."""
    rng = np.random.default_rng(seed)
    W, H = int(length / SCRIPT_RES) + 8, int(height / SCRIPT_RES) + 8
    ink = np.zeros((H, W), dtype=np.float32)
    strike = np.zeros((H, W), dtype=np.float32)
    smudge = np.zeros((H, W), dtype=np.float32)

    def stamp(canvas, xs, ys, r, value):
        xi = np.round(xs / SCRIPT_RES).astype(int) + 4
        yi = np.round(ys / SCRIPT_RES + H / 2).astype(int)
        value = np.broadcast_to(value, xs.shape)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy > r * r:
                    continue
                X, Y = xi + dx, yi + dy
                ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
                np.maximum.at(canvas, (Y[ok], X[ok]), value[ok])
    xh = 0.009                     # the x-height
    base = -xh * 0.45              # the baseline, below the ribbon's middle
    x = 0.012 + rng.random() * 0.02
    pen = 0.0011                   # the pen's half-width
    while x < length - 0.04:
        letters = int(rng.integers(2, 8))
        alpha = rng.choice([0.85, 0.85, 0.85, 0.4, 0.15], p=[0.3, 0.2, 0.15, 0.2, 0.15])
        start = x
        xs, ys = [], []
        for _ in range(letters):
            a = 0.008 + 0.004 * rng.random()
            kind = rng.random()
            h = xh * (2.0 if kind < 0.18 else (-1.1 if kind < 0.3 else 1.0)) * (0.85 + 0.3 * rng.random())
            loop = a * (0.22 + 0.2 * rng.random())
            t = np.linspace(0, TAU, 90)
            lx = x + a * t / TAU - loop * np.sin(t)
            ly = base + h * (1 - np.cos(t)) / 2
            xs.append(lx + 0.28 * (ly - base))       # leaning
            ys.append(ly)
            x += a
        X, Y = np.concatenate(xs), np.concatenate(ys)
        stamp(ink, X, Y, int(pen / SCRIPT_RES), np.float32(alpha))
        if alpha < 0.2:          # nearly erased: a grey smear where it was
            stamp(smudge, X, Y, int(pen * 3 / SCRIPT_RES), np.float32(0.25))
        if rng.random() < 0.24 and alpha > 0.3:      # struck through, hard, once
            sx = np.linspace(start - 0.003, x + 0.004, 400)
            sy = base + xh * 0.55 + (sx - start) * (rng.random() - 0.5) * 0.08 + 0.0006 * np.sin(sx * 900)
            stamp(strike, sx, sy, int(0.0009 / SCRIPT_RES), np.float32(1.0))
        x += 0.007 + 0.006 * rng.random()

    def blur(a, r):
        out = a.copy()
        for axis in (0, 1):
            acc = np.zeros_like(out)
            for d in range(-r, r + 1):
                acc += np.roll(out, d, axis)
            out = acc / (2 * r + 1)
        return out
    soft = int(STEP / SCRIPT_RES / 2)      # no finer than the mesh can carry
    return blur(ink, max(1, soft)), blur(strike, max(1, soft)), blur(smudge, 8)


def sample(canvas, u, v):
    H, W = canvas.shape
    X = np.clip(np.round(u / SCRIPT_RES).astype(int) + 4, 0, W - 1)
    Y = np.clip(np.round(v / SCRIPT_RES + H / 2).astype(int), 0, H - 1)
    return canvas[Y, X]


def paint_ribbon(key, o, rows, cols, s, w, seed):
    P = verts(o)
    nv = cols.max()
    u = s[rows]
    width = w[rows]
    v = (cols / nv - 0.5) * width
    paper = mix(PAPER, PAPER_SHADE, smooth(0.3, 0.8, fbm(P, 30.0, 4, seed)) * 0.55)
    paper = mix(paper, EDGE, smooth(0.0016, 0.0004, width / 2 - np.abs(v)) * 0.6)        # the edges catch a lavender light
    ink, strike, smudge = script_canvas(float(s[-1]) + 0.01, 0.07, seed)
    fade = 0.55 + 0.45 * smooth(0.25, 0.6, fbm(P, 3.0, 2, seed + 9))       # whole stretches of it fading
    a_ink = sample(ink, u, v) * fade
    a_strike = sample(strike, u, v)
    a_smudge = sample(smudge, u, v)
    col = mix(paper, PAPER_SHADE * 0.85, a_smudge)
    col = mix(col, INK, np.clip(a_ink, 0, 1))
    col = mix(col, INK_DARK, np.clip(a_strike * 0.9, 0, 1))
    rough = 0.8 - 0.18 * np.clip(a_ink + a_strike, 0, 1)
    if key.startswith("Tail"):          # the ends that write: soaked in ink toward the tip
        k = smooth(0.55, 1.0, u / s[-1])
        col = mix(col, INK_DARK, k * 0.85)
        rough = rough - 0.3 * k
    Nn = normals(o)
    crumple = (fbm(P, 45.0, 3, seed + 3) - 0.5) * 0.0007
    set_verts(o, P + Nn * crumple[:, None])
    paint(o, col, rough)


def paint_skin(o):
    """The core: nothing, matte, the faintest violet in it. The hollow darker still. The arms: bandaged tight, a sliver of nothing between the turns."""
    P = verts(o)
    Nn = normals(o)
    col = mix(NOTHING, NOTHING_LIFT, smooth(0.45, 0.85, fbm(P, 6.0, 4, 11)) * 0.6)
    rough = np.full(len(P), 0.92)
    hx, hz = HOLLOW_HALF
    e2 = (P[:, 0] / hx) ** 2 + ((P[:, 2] - HOLLOW_AT) / hz) ** 2
    deep = (1 - smooth(0.75, 1.05, e2)) * (P[:, 1] > HEAD.y - 0.1) * (P[:, 2] > 0.95)
    col = mix(col, HOLLOW, deep)
    rough = np.where(deep > 0.5, 1.0, rough)
    relief = np.zeros(len(P))
    for side in (1, -1):
        path = arm_path(side, 12)
        f, d = nearest_on(path, P)
        r = 0.031 - 0.012 * f + 0.004 * np.exp(-((f - 0.5) / 0.08) ** 2)
        wrist = np.linalg.norm(P - np.array(tuple(mir(WRIST, side))), axis=1) < 0.03
        on = ((d < r + 0.006) & (f > 0.05)) | wrist
        if not on.any():
            continue
        length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
        idx = np.clip(np.round(f * (len(path) - 1)).astype(int), 0, len(path) - 1)
        tan = np.array([tuple((path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()) for i in range(len(path))])
        side_ax = np.cross(tan, (0, 0, 1))
        side_ax /= np.maximum(np.linalg.norm(side_ax, axis=1), 1e-6)[:, None]
        up_ax = np.cross(side_ax, tan)
        rel = P - np.array([tuple(p) for p in path])[idx]
        phi = np.arctan2((rel * up_ax[idx]).sum(1), (rel * side_ax[idx]).sum(1)) / TAU
        # one turn of bandage every 2.6 cm, the two arms wound mirror-wise, each turn lying over the last: a step and a thin shadow at every edge,
        # and here and there the turns drawn apart, nothing showing between them
        q = (f * length / 0.026 + phi * side) % 1.0
        gap = 0.18 * smooth(0.68, 0.78, fbm(np.stack([f * length, np.zeros_like(f), np.full_like(f, side)], 1), 9.0, 2, 33 + side))
        band = smooth(gap, gap + 0.05, q)
        band = np.where(wrist & (d > r + 0.006), 1.0, band)
        paper = mix(PAPER, PAPER_SHADE, smooth(0.3, 0.8, fbm(P, 30.0, 4, 21)) * 0.55)
        paper = mix(PAPER_SHADE * 0.62, paper, smooth(gap, gap + 0.16, q))        # the shadow under the turn above
        bandage = mix(NOTHING, paper, band)
        col = np.where(on[:, None], bandage, col)
        rough = np.where(on, 0.8 * band + 0.92 * (1 - band), rough)
        relief = np.where(on, (0.0004 + 0.0011 * q) * band - 0.0006 * (1 - band), relief)
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, rough)


# ---------- the light: the point in the hollow, the broken halo, the wrist ribbons' tips ----------
CORE_HEX, HALO_HEX = "f4f0ff", "b89cff"
SPARK = V(0, HEAD.y - 0.05, HOLLOW_AT + 0.004)


def build_lights(tips, coll):
    out = {}
    m = Mesh()
    m.ball(SPARK, (0.018, 0.018, 0.018), 20, 12)
    out["Spark"] = m.finish(N + "Spark_Glow_" + CORE_HEX, coll)
    # the halo: seven sides of an octagon, standing behind the head, a flat top
    m = Mesh()
    corners = []
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        corners.append(HALO_AT + V(math.cos(a) * HALO_R, 0, math.sin(a) * HALO_R))
    order = [corners[(HALO_GAP + 1 + k) % 8] for k in range(8)]       # starts after the gap, ends before it
    pts = []
    for k in range(7):
        a, b = order[k], order[k + 1]
        for t in np.linspace(0, 1, 6, endpoint=(k == 6)):
            pts.append(a.lerp(b, float(t)))
    m.tube(pts, lambda f: 0.0075, sides=8)
    out["Halo"] = m.finish(N + "Halo_Glow_" + HALO_HEX, coll, smooth_shade=False)
    # the tips that write: each wrist ribbon's last fifth, a step past the paper's end
    for side, tag in (("L", "L"), ("R", "R")):
        bm = bmesh.new()
        for key in ("a", "b"):
            G, s, w = tips["Tail" + tag + key]
            o, _, _ = sheet_mesh(G, THICK * 1.15, "tmp", coll)
            bm.from_mesh(o.data)
            bpy.data.objects.remove(o, do_unlink=True)
        me = bpy.data.meshes.new(N + "Quill" + tag + "_Glow_" + HALO_HEX)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        out["Quill" + tag] = o
    return out


def show_glows(glows):
    for key, o in glows.items():
        h = CORE_HEX if key == "Spark" else HALO_HEX
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 3.0 if key == "Spark" else 2.0
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False, lights=True):
    pieces, data = {}, {}
    core = build_core(N + "CoreHi", HI)
    head = build_core(N + "HoodHi", HI, head_only=True)
    skin = build_skin(core, N + "SkinHi", HI)
    data["trees"] = {"core": tree_of(core), "head": tree_of(head), "skin": tree_of(skin)}
    for o in (core, head):
        bpy.data.objects.remove(o, do_unlink=True)
    data["SkinBase"] = bpy.data.objects.new(N + "SkinBase", skin.data.copy())
    HI.objects.link(data["SkinBase"])
    data["SkinBase"].hide_render = True
    pieces["Skin"] = skin
    ribbons, tips = build_ribbons(data["trees"], HI, STEP)
    data["ribbons"] = ribbons
    for key, r in ribbons.items():
        pieces[key] = r[0]
    glows = build_lights(tips, HI) if lights else {}
    if not clay:
        paint_skin(skin)
        for k, (key, r) in enumerate(ribbons.items()):
            paint_ribbon(key, r[0], r[1], r[2], r[4], r[5], 100 + 7 * k)
    return pieces, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.2), (-0.62, 0.62, 0.35), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0, 0.62)
FACE_AT = (0, -0.04, 1.05)
EXTRA = [(0, -1, 0.05, 1.0, FACE_AT), (0.6, -0.75, 0.25, 1.0, FACE_AT), (1, -0.1, 0.1, 1.2, (0.1, 0, 0.9)), (0.4, -0.9, -0.1, 1.4, (0.2, -0.06, 0.35)),
         (0.5, -0.8, 0.3, 1.6, (0, 0, 0.18)), (0, 1, 0.3, 1.2, (0, 0.08, 1.06))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    mat = bpy.data.materials.new("clay")
    g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
    g.inputs["Roughness"].default_value = 0.6
    dark = bpy.data.materials.new("clay_dark")
    g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0.05, 0.045, 0.08, 1)
    g.inputs["Roughness"].default_value = 0.8
    if STAGE == "paint":
        mat = dark = hi_material(ao_distance=0.03, ao_share=0.4)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if key == "Skin" else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
def remove_specks(o, smallest=20):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, stray = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        island, stack = [], [v]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            island.append(x)
            stack += [e.other_vert(x) for e in x.link_edges]
        if len(island) < smallest:
            stray += island
    bmesh.ops.delete(bm, geom=stray, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    return len(stray)


def build_low(data):
    skin = decimated(data["SkinBase"], N + "SkinLow", 3600)
    print("SKIN stray specks removed", remove_specks(skin), "verts", flush=True)
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    print("SKIN decimated gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), flush=True)
    ribbons, tips = build_ribbons(data["trees"], GAME, None, low=True)
    lows = {"Skin": skin}
    for key, r in ribbons.items():
        lows[key] = r[0]
    triangulate(lows)
    return lows, ribbons, tips


def strip_writer(r):
    """A ribbon's UVs, true to scale: its outer face one strip, its inner face a second strip beside it (shrunk for a ribbon lying on the skin, whose
    inside nobody sees), each thin side a sliver along the outer strip's edge."""
    o, rows, cols, G, s, w, hug = r

    def write(obj, density):
        me = obj.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uv = me.uv_layers.active.data
        K = len(rows) // 2
        nu, nv = int(rows.max()), int(cols.max())
        wmax, g = float(w.max()), 0.003
        um = s[rows] - s[0]
        vm = (cols / nv - 0.5) * w[rows]
        inner = 0.15 if hug else 1.0
        for p in me.polygons:
            vs = list(p.vertices)
            top, bot = all(v < K for v in vs), all(v >= K for v in vs)
            rr, cc = {int(rows[v]) for v in vs}, {int(cols[v]) for v in vs}
            for li, v in zip(p.loop_indices, vs):
                x, y = float(um[v]), float(vm[v])
                if top:
                    q = (x, y)
                elif bot:
                    q = (x * inner, wmax / 2 + 2 * g + inner * (wmax / 2 + y))
                elif v < K:
                    q = (x, y)
                elif len(rr) == 1:      # an end
                    q = (x + (g * 0.7 if rr == {nu} else -g * 0.7), y)
                else:                   # a long edge
                    q = (x, y + (g * 0.7 if cc == {nv} else -g * 0.7))
                uv[li].uv = (q[0] * density, q[1] * density)
    return write


def arm_share(P):
    """Per vertex, per side: how much it belongs to its arm (0 on the torso, 1 out on the arm), and where along the arm."""
    out = {}
    for side, tag in ((1, "L"), (-1, "R")):
        f, d = nearest_on(arm_path(side, 8), P)
        r = 0.031 - 0.012 * f + 0.004 * np.exp(-((f - 0.5) / 0.08) ** 2)
        W = np.array([core_at(z)[0] for z in P[:, 2]])
        near = 1 - smooth(r + 0.008, r + 0.02, d)
        outside = smooth(W - 0.012, W + 0.01, P[:, 0] * side)
        share = near * np.maximum(outside, smooth(0.1, 0.2, f))
        wrist = np.linalg.norm(P - np.array(tuple(mir(WRIST, side))), axis=1) < 0.032
        share = np.where(wrist, 1.0, share)
        f = np.where(wrist, 1.0, f)
        out[tag] = (share, f)
    return out


def arm_regions(skin):
    P = np.array([tuple(p.center) for p in skin.data.polygons])
    shares = arm_share(P)
    on = np.maximum(shares["L"][0], shares["R"][0]) > 0.5
    return {i for i in range(len(P)) if on[i]}


# ---------- the skeleton ----------
TORSO = ((0.3, "Hips"), (0.48, "Body"), (0.66, "Chest"), (0.88, "Chest"), (0.95, "Neck"), (1.0, "Head"))
ARM_F = (0.4, 0.58, 0.95)
HEM_F, SCARF_F, TAIL_F = (0.12, 0.42, 0.72), (0.1, 0.42, 0.72), (0.3, 0.66)


def torso_weight(z):
    if z <= TORSO[0][0]:
        return {TORSO[0][1]: 1.0}
    for (z0, a), (z1, b) in zip(TORSO, TORSO[1:]):
        if z <= z1:
            t = float(smooth(z0, z1, z))
            out = {a: 1 - t}
            out[b] = out.get(b, 0) + t
            return out
    return {TORSO[-1][1]: 1.0}


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def skeleton(trees):
    bones = [("Root", V(0, 0, 0), None), ("Hips", V(0, 0, 0.3), "Root"), ("Body", V(0, 0, 0.5), "Hips"), ("Chest", V(0, 0.004, 0.72), "Body"),
             ("Neck", V(0, -0.006, 0.89), "Chest"), ("Head", V(0, -0.022, 0.965), "Neck"), ("Spark", SPARK.copy(), "Head"), ("Halo", HALO_AT.copy(), "Head")]
    for side, tag in ((1, "L"), (-1, "R")):
        bones += [("Arm%s1" % tag, mir(ARM[0], side), "Chest"), ("Arm%s2" % tag, mir(ARM[2], side), "Arm%s1" % tag), ("Arm%s3" % tag, mir(ARM[4], side), "Arm%s2" % tag)]
        a, b = tail_path("a", side)[0], tail_path("b", side)[0]
        bones += [("Arm%s4" % tag, path_at(a, TAIL_F[0]).lerp(path_at(b, TAIL_F[0]), 0.5), "Arm%s3" % tag),
                  ("Arm%s5" % tag, path_at(a, TAIL_F[1]).lerp(path_at(b, TAIL_F[1]), 0.5), "Arm%s4" % tag)]
        sc = scarf_path(side, trees["core"])[0]
        parent = "Chest"
        for k, f in enumerate(SCARF_F):
            bones.append(("Scarf%s%d" % (tag, k + 1), path_at(sc, f), parent))
            parent = "Scarf%s%d" % (tag, k + 1)
    for k in range(len(HEM_ANGLES)):
        pts = hem_path(k, trees["core"])[0]
        parent = "Hips"
        for tag, f in zip("abc", HEM_F):
            bones.append(("Hem%d%s" % (k, tag), path_at(pts, f), parent))
            parent = "Hem%d%s" % (k, tag)
    return armature(bones)


def skin_like(P):
    """Weights for points on (or lying over) the skin: the torso by height, the arms along their length, the two handed over at each shoulder."""
    shares = arm_share(P)
    out = []
    for i in range(len(P)):
        w = torso_weight(float(P[i, 2]))
        for tag in ("L", "R"):
            share, f = shares[tag][0][i], shares[tag][1][i]
            if share > 1e-3:
                w = blend(w, chain_weight(["Arm%s1" % tag, "Arm%s2" % tag, "Arm%s3" % tag], ARM_F, float(f)), float(share))
        out.append(w)
    return out


def ribbon_weights(key, r, full=None):
    o, rows, cols, G, s, w, hug = r
    P = verts(o)
    if key in WRAPS or key in HEAD_WRAPS:
        return skin_like(P)
    f = s[rows] / (full or s[-1])
    if key.startswith("Hem"):
        k = key[3:]
        names = ["Hips"] + ["Hem%s%s" % (k, t) for t in "abc"]
        return [chain_weight(names, (0.06, 0.2, 0.5, 0.8), float(x)) for x in f]
    if key.startswith("Scarf"):
        tag = key[5:]
        names = ["Chest"] + ["Scarf%s%d" % (tag, n) for n in (1, 2, 3)]
        return [chain_weight(names, (0.05, 0.16, 0.48, 0.78), float(x)) for x in f]
    tag = key[4]
    return [chain_weight(["Arm%s3" % tag, "Arm%s4" % tag, "Arm%s5" % tag], (0.08, 0.32, 0.68), float(x)) for x in f]


def bind_all(lows, ribbons, tips, rig, glows):
    weigh(lows["Skin"], skin_like(verts(lows["Skin"])))
    for key, r in ribbons.items():
        full = None
        if key.startswith("Tail"):
            full = float(tips[key][1][-1])
        weigh(lows[key], ribbon_weights(key, r, full))
    rigid(glows["Spark"], "Spark")
    rigid(glows["Halo"], "Halo")
    rigid(glows["QuillL"], "ArmL5")
    rigid(glows["QuillR"], "ArmR5")
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateTheNamelessOne uses. +X lifts what points forward (and swings a hanging arm forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def pose_library():
    hem_back = {"Hem%d%s" % (k, t): game_turn(-0.25 * (1 + "abc".index(t) * 0.5), 0, 0) for k in range(len(HEM_ANGLES)) for t in "abc"}
    return {
        "Lean": {"Body": game_turn(-0.12, 0, 0), "Chest": game_turn(-0.08, 0, 0), **hem_back, "ScarfL2": game_turn(-0.3, 0, 0), "ScarfR2": game_turn(-0.3, 0, 0)},
        "Look": {"Neck": game_turn(0.12, 0.25, 0.1), "Head": game_turn(0.2, 0.35, 0.2)},
        "ArmsUp": {"ArmL1": game_turn(1.9, 0, -0.35), "ArmR1": game_turn(1.9, 0, 0.35), "ArmL2": game_turn(0.5, 0, 0), "ArmR2": game_turn(0.5, 0, 0), "Chest": game_turn(0.08, 0, 0),
                   "ArmL4": game_turn(0.5, 0, 0), "ArmR4": game_turn(0.5, 0, 0)},
        "Write": {"ArmL1": game_turn(1.0, 0, -0.15), "ArmL2": game_turn(0.7, 0, 0), "ArmL3": game_turn(0.4, 0.5, 0), "ArmL4": game_turn(0.6, 0, 0.3), "ArmL5": game_turn(0.4, 0, 0)},
        "Drift": {"ScarfL1": game_turn(0.2, 0.2, -0.2), "ScarfL2": game_turn(0.35, 0, -0.3), "ScarfL3": game_turn(0.4, 0, -0.3), "ScarfR1": game_turn(0.2, -0.2, 0.2),
                  "ScarfR2": game_turn(0.35, 0, 0.3), "ScarfR3": game_turn(0.4, 0, 0.3), **{"Hem%da" % k: game_turn(0.15 * math.sin(k * 1.7), 0, 0.2 * math.cos(k * 1.3)) for k in range(8)}},
    }


VIEW_GAME = (0, 0, 0.62)

if __name__ == "__main__" and STAGE == "all":
    pieces, _, data = build_hi(lights=False)
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows, ribbons, tips = build_low(data)
    arms = arm_regions(lows["Skin"])
    texels = {key: 1.0 for key in ribbons}
    own = {key: strip_writer(r) for key, r in ribbons.items()}
    unwrap(lows, [(lambda p: p.index in arms, 0.85), (None, 0.5)], {}, shape="CONCAVE", angle=50, margin=0.003, own_uv=own, texels=texels)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.3, 0.3, 0.3, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.007, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    glows = build_lights(tips, GAME)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(data["trees"])
    body = bind_all(lows, ribbons, tips, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    for name in ("Spark", "Halo", "Head", "ArmL5", "ArmR5", "Chest"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.6, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    wide = (0.6, -0.75, 0.3, 3.4, VIEW_AT)
    for name, view in (("Lean", (1, -0.1, 0.1, 3.4, VIEW_AT)), ("Look", (0.2, -1, 0.2, 1.4, FACE_AT)), ("ArmsUp", wide), ("Write", wide), ("Drift", (0.3, 0.9, 0.4, 3.4, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.3, 3.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

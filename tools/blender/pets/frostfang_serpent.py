"""The Frostfang Serpent (Mythical, Ice; Elemental Core Egg): "Its bite stops time for whatever it touches, at least for the moment that matters. It sheds
its skin as sheets of clear ice."

A frozen-hood king cobra (the owner's choice, 2026-11-09), in a design language of its own: frozen motion. A huge king cobra, its long tail coiled in a
flat spiral on the ground, its front rising in a tall column; at the top its great hood, the front of it frosted ice faceted into plates and veined with
frost, and round its rim a crown of clear ice blades that catch the light. A broad, flat head under heavy brow plates; lidless ice-white eyes that never
blink; a real jaw that opens on two long glowing crystal fangs and a forked tongue that flicks. Glacier-blue scales crossed by frost-white chevron bands,
a pale banded belly. Around it, things hang frozen in the air: time stopped.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/frostfang_serpent.py -- [clay|paint|rig|all] [review dir]

Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Its coil rests on the ground (z = 0). The maps go to assets/pets/ElementalCoreEgg/.

What touches what: the skin (the whole body from tail tip to the back of the head, the hood, the upper head) is one piece, its coil resting on the
ground; the lower jaw is its own shell, its top a few millimetres under the palate (the mouth line), its hinge tucked under the skull; the eyes sit in
their sockets (a snake has no lids); the fangs hang from the palate into the closed jaw; the tongue lies in the mouth's gap; the ice blades root inside
the hood's rim.
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
PET = "FrostfangSerpent"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours: glacier ice, frost, and the cold light in it ----------
GLACIER_DEEP, GLACIER, GLACIER_PALE = rgb(24, 46, 92), rgb(48, 92, 156), rgb(118, 168, 220)
FROST, FROST_EDGE = rgb(228, 244, 255), rgb(150, 214, 255)
BELLY, BELLY_LINE = rgb(214, 234, 250), rgb(146, 182, 220)
MOUTH, MOUTH_DEEP = rgb(150, 122, 176), rgb(70, 50, 100)
TONGUE = rgb(40, 34, 78)
ICE, ICE_VEIN = rgb(176, 226, 255), rgb(246, 252, 255)
FANG_HEX, TRAIL_HEX = "c8f2ff", "eafaff"

# ---------- the frame of it ----------
COIL_C = V(0, 0.1, 0)                # the middle of its coil, on the ground
R_OUT, R_IN = 0.345, 0.19            # the spiral's radius at the tail tip and where it rises
TURNS = 1.1
COLUMN = [V(0.115, -0.1, 0.16), V(0.1, -0.124, 0.3), V(0.042, -0.112, 0.43), V(0.0, -0.068, 0.55), V(0.0, -0.05, 0.66), V(0.0, -0.074, 0.752),
          V(0.0, -0.122, 0.8), V(0.0, -0.17, 0.81)]         # from the coil up its reared front, in an S, to the back of its head
RADIUS = ((0, 0.02), (0.1, 0.042), (0.35, 0.07), (0.64, 0.094), (0.76, 0.088), (0.88, 0.074), (1.0, 0.058))      # along it, tail tip (0) to head (1)
HOOD_Z = (0.43, 0.79)                # the hood's foot and top, heights up the column
HOOD_W = ((0, 0.08), (0.3, 0.19), (0.6, 0.245), (0.84, 0.2), (1, 0.09))         # its half-width up its height
HOOD_D = 0.03                        # its half-thickness
HOOD_CUP = 0.055                     # its edges curl forward this far: cupped round its head
HEAD_SHIFT = V(0, 0.01, -0.18)       # the head's numbers below are drawn at its first height and set down onto the column by this
CRANIUM = (V(0, -0.205, 0.99), (0.064, 0.076, 0.03))
SNOUT = [V(0, -0.215, 0.988), V(0, -0.26, 0.983), V(0, -0.302, 0.977)]
SNOUT_W = ((0, 0.05), (0.6, 0.038), (1, 0.025))
SNOUT_H = ((0, 0.026), (1, 0.018))
JAW = [V(0, -0.132, 0.942), V(0, -0.21, 0.946), V(0, -0.268, 0.949), V(0, -0.29, 0.95)]       # its chin a little behind the snout's end: tucked under it
JAW_W = ((0, 0.046), (0.5, 0.04), (0.85, 0.027), (1, 0.018))
JAW_H = ((0, 0.016), (0.7, 0.016), (1, 0.013))
MOUTH_GAP = 0.0012                   # half the mouth's gap: palate above, jaw below (a fine dark seam; wider, it read as a grin)
EYE_R = 0.0145
EYE_C = V(0.054, -0.224, 0.995)
EYE_AXIS = V(0.7, -0.6, 0.35).normalized()
FANGS_OPEN = [V(0.02, -0.266, 0.9665), V(0.0205, -0.271, 0.955), V(0.0195, -0.269, 0.943), V(0.018, -0.262, 0.935)]       # root (in the palate) to tip, struck down
FANG_FOLD = math.radians(88)         # at rest they fold back flat inside its palate, out of sight (a viper's trick: showing, they read as buck teeth)
TONGUE_PATH = [V(0, -0.17, 0.0), V(0, -0.24, 0.0), V(0, -0.272, 0.0)]       # (z: the mouth line) its root to the fork
# (the head drawn at its first height, set down onto the column)
CRANIUM = (CRANIUM[0] + HEAD_SHIFT, CRANIUM[1])
SNOUT = [p + HEAD_SHIFT for p in SNOUT]
JAW = [p + HEAD_SHIFT for p in JAW]
EYE_C = EYE_C + HEAD_SHIFT
FANGS_OPEN = [p + HEAD_SHIFT for p in FANGS_OPEN]
FANG_ROOT = V(0, FANGS_OPEN[0].y, FANGS_OPEN[0].z)          # the Fangs bone: their fold's hinge
FANGS = [FANG_ROOT + Matrix.Rotation(FANG_FOLD, 3, "X") @ (p - FANG_ROOT) for p in FANGS_OPEN]      # as modelled: folded
TONGUE_PATH = [p + V(0, HEAD_SHIFT.y, 0) for p in TONGUE_PATH]
FORK = 0.022
TONGUE_SINK = 0.0075                 # how far under the mouth line it lies, inside the jaw, until it flicks
ICE_BLADES = 6                       # a side, round the hood's rim


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def hd(v):
    return v + HEAD_SHIFT


def mouth_z(y):
    """The mouth line: the middle of the gap between palate and jaw, its corners turned down at the back (rising, it smiled)."""
    return float(np.interp(y - HEAD_SHIFT.y, [-0.31, -0.13], [0.957, 0.9505])) + HEAD_SHIFT.z


def mouth_zs(ys):
    return np.interp(ys - HEAD_SHIFT.y, [-0.31, -0.13], [0.957, 0.9505]) + HEAD_SHIFT.z


def path_frames(path):
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0) - tan * tan.x
        side = side.normalized() if side.length > 1e-5 else V(1, 0, 0)
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def arc_lengths(path):
    a = np.array([tuple(p) for p in path])
    return np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])


def resample(path, n):
    """n + 1 points evenly by arc length."""
    s = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    out = []
    for t in np.linspace(0, s[-1], n + 1):
        i = min(int(np.searchsorted(s, t, side="right")) - 1, len(a) - 2)
        f = (t - s[i]) / max(s[i + 1] - s[i], 1e-9)
        out.append(V(*(a[i] * (1 - f) + a[i + 1] * f)))
    return out


def centreline(per=6):
    """Its spine from the tail tip to the back of its head, evenly spaced: the spiral on the ground (each point its own radius up, so the coil rests on
    the ground), then up its reared front."""
    n = 64
    phi_end = -math.pi / 2
    flat = []
    for k in range(n + 1):
        t = k / n
        phi = phi_end - TURNS * TAU * (1 - t)
        r = R_OUT + (R_IN - R_OUT) * t
        flat.append(COIL_C + V(r * math.cos(phi), r * math.sin(phi), 0))
    # each spiral point lifted by its radius before the spline is drawn (lifted after, the spline between coil and column dipped into the ground)
    total = arc_lengths(flat)[-1] + arc_lengths(catmull([flat[-1]] + COLUMN, per))[-1]
    s_flat = arc_lengths(flat)
    pts = [V(p.x, p.y, prof(RADIUS, s_flat[k] / total)) for k, p in enumerate(flat)]
    path = catmull(pts + COLUMN, per)
    spiral = n * per            # the spiral's last point, in the spline
    f = arc_lengths(path)
    f = f / f[-1]
    path = [V(p.x, p.y, prof(RADIUS, f[i])) if i <= spiral else p for i, p in enumerate(path)]
    return resample(path, 360)


SPINE = centreline()
SPINE_S = arc_lengths(SPINE)
SPINE_F = SPINE_S / SPINE_S[-1]
COIL_END = int(np.argmin([(p - V(0, COIL_C.y - R_IN, prof(RADIUS, 0.64))).length for p in SPINE]))      # where it leaves the spiral, at the front


def radius_at(f):
    return prof(RADIUS, f)


def spine_at(f):
    k = f * (len(SPINE) - 1)
    i = min(int(k), len(SPINE) - 2)
    return SPINE[i].lerp(SPINE[i + 1], k - i)


def hood_f(z):
    """Where along its spine (0..1) its column reaches height z (above the coil)."""
    zs = np.array([p.z for p in SPINE])
    i0 = COIL_END + 5
    seg = zs[i0:]
    j = int(np.argmin(np.abs(seg - z)))
    return SPINE_F[i0 + j]


def hood_point(t, x01, side):
    """A point of the hood: t up its height (0 foot, 1 top), x01 out across it (0 the middle, 1 its rim), on side's half, on its middle surface."""
    f = hood_f(HOOD_Z[0] + (HOOD_Z[1] - HOOD_Z[0]) * t)
    c = spine_at(f)
    w = prof(HOOD_W, t)
    return c + V(side * w * x01, -HOOD_CUP * x01 ** 2, 0)


# ---------- the skin ----------
def rm_frames(path, first_side=None):
    """Frames along a path that never twist (each turned on from the last by the least rotation): the old frames flipped where the coil ran
    sideways and creased it."""
    out = []
    tan = (path[1] - path[0]).normalized()
    side = first_side or (V(1, 0, 0) - tan * tan.x)
    if side.length < 1e-4:
        side = tan.orthogonal()
    side = (side - tan * side.dot(tan)).normalized()
    for i in range(len(path)):
        t2 = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t2.rotation_difference(t2) @ side if i == 0 else tan.rotation_difference(t2) @ side
        side = (side - t2 * side.dot(t2)).normalized()
        tan = t2
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def tube_loft(m, path, r_fn, flat_fn=None, nt=40, frames=None):
    fr = frames or path_frames(path)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        r = r_fn(f)
        fl = flat_fn(f) if flat_fn else 1.0
        rings.append([m.bm.verts.new(p + side * (r * fl * math.cos(TAU * k / nt)) + up * (r * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


def build_skin():
    m = Mesh()
    body = SPINE[::2]
    fb = SPINE_F[::2]
    tube_loft(m, body, lambda f: radius_at(float(np.interp(f, np.linspace(0, 1, len(fb)), fb))), nt=36, frames=rm_frames(body, V(0, 0, 1)))
    m.ball(SPINE[0], (radius_at(0.0),) * 3, 20, 12)          # its tail's tip, rounded (no thinner than the game mesh's grain: thinner, it crumpled)
    # the hood: a broad thin plate grown out of the column, cupped forward
    rows, cols = 26, 30
    grid = []
    for i in range(rows + 1):
        t = i / rows
        row = []
        for j in range(cols + 1):
            a = TAU * j / cols
            x01 = math.cos(a)
            p = hood_point(t, abs(x01), 1 if x01 >= 0 else -1)
            depth = HOOD_D * math.sin(a) * (1 - 0.5 * abs(x01) ** 4)
            row.append(m.bm.verts.new(p + V(0, -depth, 0)))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            j2 = (j + 1) % cols
            m.bm.faces.new((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
    m.bm.faces.new(grid[0][:cols])
    m.bm.faces.new(list(reversed(grid[rows][:cols])))
    # the upper head
    m.ball(CRANIUM[0], CRANIUM[1], 40, 24)
    tube_loft(m, catmull(SNOUT, 8), lambda f: prof(SNOUT_H, f), lambda f: prof(SNOUT_W, f) / prof(SNOUT_H, f), nt=32)
    m.ball(SNOUT[-1] + V(0, 0.004, 0.0), (0.025, 0.014, 0.0175), 28, 16)                # the snout's end, rounded and blunt (cut flat, it read as a duck's bill)
    # its upper lip and jowls: down past the mouth line all along, so the palate is cut flat right on it (the head's own underside lay up to a
    # centimetre above it, and the mouth gaped)
    tube_loft(m, catmull([hd(V(0, -0.14, 0.956)), hd(V(0, -0.22, 0.954)), hd(V(0, -0.27, 0.956)), hd(V(0, -0.297, 0.958))], 8),
              lambda f: 0.012, lambda f: float(np.interp(f, [0, 0.5, 0.85, 1], [4.4, 4.3, 3.0, 1.9])), nt=32)
    for side in (1, -1):
        m.ball(hd(V(side * 0.052, -0.222, 1.0055)), (0.021, 0.034, 0.0045), 24, 12)      # the brow plate over the eye: a hard, flat stare (higher, it read as ears)
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.12,) * 3, 24, 16)      # the socket
        m.ball(hd(V(side * 0.05, -0.165, 0.975)), (0.024, 0.036, 0.018), 24, 14)       # the jaw's muscle behind the eye
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 5})])
    P = verts(o)
    # the palate flat over the mouth's gap; the coil's underside flat on the ground
    head = (P[:, 1] < -0.12) & (np.abs(P[:, 0]) < 0.075) & (P[:, 2] > 0.72)
    zm = mouth_zs(P[:, 1])
    P[head, 2] = np.maximum(P[head, 2], zm[head] + MOUTH_GAP)
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(o, P)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_jaw(name, coll, nt=32, per=8):
    """Its lower jaw: a D in section all along it, round beneath and dead flat on top just under the palate (the mouth's floor), its chin rounded.
    (Clamped flat after it was made, its sides folded onto its top and flickered.)"""
    m = Mesh()
    path = catmull(JAW, per)
    for _ in range(3):
        path.append(path[-1] + V(0, -0.003, 0))          # three more rings past its end, shrinking: a rounded chin
    nb = max(6, nt // 2)                 # points round the bottom
    nf = max(3, nt // 6)                 # points across the flat top
    rings = []
    n_main = len(catmull(JAW, per))
    for i, c in enumerate(path):
        f = min(1.0, i / (n_main - 1))
        shrink = 1.0 if i < n_main else (0.82, 0.55, 0.22)[i - n_main]
        w, h = prof(JAW_W, f) * shrink, prof(JAW_H, f) * 2 * shrink
        top = mouth_z(c.y) - MOUTH_GAP - (0 if i < n_main else 0.0006 * (i - n_main + 1))
        ring = []
        for a in np.linspace(math.pi, TAU, nb + 1):
            ring.append(m.bm.verts.new(V(c.x + w * math.cos(a), c.y, top + h * math.sin(a))))
        for b in np.linspace(1, -1, nf + 1)[1:-1]:
            ring.append(m.bm.verts.new(V(c.x + w * b, c.y, top)))
        rings.append(ring)
    n = len(rings[0])
    for i in range(len(rings) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(list(reversed(rings[0])))
    m.bm.faces.new(rings[-1])
    o = m.finish(name, coll)            # (the high one the same shape, only finer: voxel-smoothed, its chin parted from the game's and baked wrong)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_tongue(name, coll, sides=10):
    """A forked tongue: one flat closed piece (two tines made as tubes overlapped where they met, lying level, and flickered), lying inside its lower
    jaw: it rises into the mouth's gap and out only to flick."""
    y0, y1 = TONGUE_PATH[0].y, TONGUE_PATH[-1].y           # root, fork crotch
    tip = y1 - FORK
    half = lambda y: 0.0055 - 0.0015 * (y0 - y) / (y0 - y1)
    # its outline, round from the root up its left side, out to the left tine's point, back into the crotch, out to the right tine's, down its right side
    outline = [(-half(y0), y0), (-half(y1), y1), (-0.0095, tip), (-0.0062, tip + 0.0015), (0.0, y1 - 0.004),
               (0.0062, tip + 0.0015), (0.0095, tip), (half(y1), y1), (half(y0), y0)]
    dense = []
    for k in range(len(outline)):
        a, b = outline[k], outline[(k + 1) % len(outline)]
        n = 6 if k in (0, 7) else 3
        for t in range(n):
            dense.append((a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n))
    m = Mesh()
    bm = m.bm
    top = [bm.verts.new(V(x, y, mouth_z(y) - TONGUE_SINK + 0.001)) for x, y in dense]
    bot = [bm.verts.new(V(x, y, mouth_z(y) - TONGUE_SINK - 0.001)) for x, y in dense]
    n = len(dense)
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((top[k], bot[k], bot[k2], top[k2]))
    ft = bm.faces.new(list(reversed(top)))
    fb = bm.faces.new(bot)
    bmesh.ops.triangulate(bm, faces=[ft, fb])
    return m.finish(name, coll, smooth_shade=False)


def build_fangs(name, coll, sides=12, per=4):
    m = Mesh()
    for side in (1, -1):
        m.tube(catmull([mir(p, side) for p in FANGS], per), lambda f: 0.0042 * (1 - f) ** 0.8 + 0.0006, sides=sides)
    return m.finish(name, coll)


# ---------- the ice blades round the hood ----------
def blade_frames():
    """Per blade: its root (inside the hood's rim), the way it points (out from the rim, swept up), the plane it lies in, its length and its side.
    Broad plates fanned round the rim, each overlapping the next like scales, each a few millimetres behind the one below it (lying level, two that
    overlap would flicker)."""
    out = []
    for side in (1, -1):
        for k in range(ICE_BLADES):
            t = 0.1 + 0.8 * k / (ICE_BLADES - 1)
            rim = hood_point(t, 1.0, side)
            up = (hood_point(min(1, t + 0.02), 1.0, side) - hood_point(max(0, t - 0.02), 1.0, side)).normalized()
            inward = (hood_point(t, 0.8, side) - rim).normalized()
            normal = up.cross(inward).normalized()
            if normal.y > 0:
                normal = -normal                     # facing forward, as the hood does
            d = (-inward + up * (0.35 + 0.9 * t)).normalized()
            normal = Matrix.Rotation(math.radians(4 if k % 2 else -4), 3, d) @ normal      # twisted a little, alternately: never lying level with the hood
            length = 0.09 + 0.065 * math.sin(math.pi * min(1.0, 0.25 + t * 0.85))
            out.append((rim + inward * 0.06 + normal * (0.0016 * k - 0.004), d, normal, length + 0.018, side))      # rooted well inside the hood
    return out


def blade_width(u):
    """A blade's half-width along it: a crystal shard, straight-sided, widest a quarter of the way out, a long keen point (curved, they read as leaves)."""
    return max(0.0012, 0.028 * (0.55 + 0.45 * u / 0.25) if u < 0.25 else 0.028 * (1 - u) / 0.75)      # (its point never quite nothing: no degenerate faces)


def build_ice(name, coll, nu=8, nv=6):
    """Each blade a plate of clear ice: thickest down its middle, its edges keen, its point sharp."""
    m = Mesh()
    make_tags_bm(m.bm, ints=("blade",))
    for k, (root, d, normal, length, side) in enumerate(blade_frames()):
        across = d.cross(normal).normalized()
        before = set(m.bm.verts)

        def point(u, v, root=root, d=d, across=across, length=length, normal=normal):
            return tuple(root + d * (u * length) + across * ((v - 0.5) * 2 * blade_width(u)) + normal * (0.006 * u * u))
        m.sheet(point, lambda u, v: 0.0048 * (1 - abs(v - 0.5) * 1.7) * (1 - 0.75 * u) + 0.0007, nu, nv)
        tag_new_bm(m.bm, before, blade=k)
    return m.finish(name, coll, recalc=False)          # a sheet is wound outward as it is made (recalculated, thin blades turned inside out)


# ---------- per-vertex tags ----------
def make_tags_bm(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new_bm(bm, before, **values):
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


def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, (0, 1, 0.001), (0, -1, 0.001)) for side, tag in ((1, "L"), (-1, "R"))}


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_skin()
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
    pieces["Jaw"] = build_jaw(N + "JawHi", HI, nt=48, per=12)
    pieces["Tongue"] = build_tongue(N + "TongueHi", HI)
    pieces["Ice"] = build_ice(N + "IceHi", HI, 16, 10)
    glows = {"Fangs": build_fangs(N + "Fangs_Glow_" + FANG_HEX, HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-20, 22, 0.0032, 10), (18, -16, 0.0015, 6)))}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


# ---------- painting ----------
def cells_3d(P, f, seed=0):
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


F_RISE = float(SPINE_F[COIL_END])


def body_coords(P):
    """Per point: how far along its spine (metres from the tail tip), how far off it, and where round it (up: +1 along its back, -1 its belly; side)."""
    A = np.array([tuple(p) for p in SPINE])
    f, d = nearest_on(SPINE, P)
    k = f * (len(A) - 1)
    i = np.clip(k.astype(int), 0, len(A) - 2)
    t = k - i
    Q = A[i] * (1 - t)[:, None] + A[i + 1] * t[:, None]
    tan = A[i + 1] - A[i]
    tan /= np.linalg.norm(tan, axis=1)[:, None]
    # its back: up on the coil; on its reared front, behind it (its belly faces forward, under its hood)
    rise = smooth(F_RISE, F_RISE + 0.06, f)[:, None]
    back = np.array([0, 0, 1.0]) * (1 - rise) + np.array([0, 1.0, 0]) * rise
    back = back - tan * (back * tan).sum(1)[:, None]
    back /= np.linalg.norm(back, axis=1)[:, None] + 1e-9
    side = np.cross(tan, back)
    rel = P - Q
    rel /= np.linalg.norm(rel, axis=1)[:, None] + 1e-9
    return f * SPINE_S[-1], d, (rel * back).sum(1), (rel * side).sum(1), f


def hood_zone(P):
    """How much a point is the hood's broad plate (not the column inside it)."""
    zt = (P[:, 2] - HOOD_Z[0]) / (HOOD_Z[1] - HOOD_Z[0])
    inside = smooth(-0.02, 0.06, zt) * (1 - smooth(0.95, 1.05, zt))
    return inside * smooth(0.06, 0.09, np.abs(P[:, 0]))


def skin_fields(P, Nn):
    s, d, up, lat, f = body_coords(P)
    head = (P[:, 1] < -0.13) & (P[:, 2] > HOOD_Z[1] - 0.05) | (f > 0.985)
    belly = smooth(-0.35, -0.7, up) * (~head)
    # frost crossbands, chevrons pointing toward its head, bolder toward its tail
    c = s - 0.06 * (1 - up) + 0.025 * fbm(P, 6.0, 2, 3)          # a little uneven: even bands read as a toy's stripes
    period = 0.15
    ph = c / period
    dist = np.abs(ph - np.round(ph)) * period
    band = (1 - smooth(0.007, 0.017, dist)) * (0.4 + 0.6 * smooth(0.6, 0.1, f)) * (1 - belly) * (~head) * (1 - smooth(0.72, 0.86, f))
    core = (1 - smooth(0.0, 0.005, dist)) * band
    scute = 0.5 + 0.5 * np.cos(s * TAU / 0.022)
    d1, d2, own = cells_3d(P, 175.0, 5)
    scale = smooth(0.0, 0.14, d2 - d1)
    D1, D2, own2 = cells_3d(P, 60.0, 9)
    plate = smooth(0.0, 0.09, D2 - D1)
    hz = hood_zone(P)
    front = hz * smooth(-0.15, -0.5, Nn[:, 1])
    rear = hz * smooth(0.15, 0.5, Nn[:, 1])
    # the frost on its hood's front: veins radiating from the column, branching
    ang = np.arctan2(P[:, 2] - 0.62, np.abs(P[:, 0]))
    vein = 1 - smooth(0.03, 0.11, np.abs(np.sin(ang * 7 + fbm(P, 12.0, 3, 7) * 3.0)))
    vein *= smooth(0.07, 0.12, np.abs(P[:, 0])) * smooth(0.45, 0.6, fbm(P * 1.3, 9.0, 2, 13) + 0.2)
    C1, C2, _ = cells_3d(P, 26.0, 21)
    facet = smooth(0.0, 0.25, C2 - C1)
    crack = 1 - smooth(0.0, 0.035, C2 - C1)
    crescent = rear * (1 - smooth(0.012, 0.03, np.abs(np.hypot(P[:, 0] / 1.6, P[:, 2] - 0.56) - 0.11)))
    mouth = (P[:, 1] < -0.12) & (np.abs(P[:, 2] - mouth_zs(P[:, 1]) - MOUTH_GAP) < 0.0025) & (Nn[:, 2] < -0.6)
    lip = (P[:, 1] < -0.12) & (np.abs(P[:, 2] - mouth_zs(P[:, 1]) - MOUTH_GAP) < 0.007) & (~mouth) & head
    mask = np.zeros(len(P))
    for side in (1, -1):
        e = np.array(tuple(mir(EYE_C, side)))
        mask = np.maximum(mask, (1 - smooth(0.012, 0.026, np.abs(P[:, 2] - e[2] - 0.15 * (P[:, 1] - e[1])))) * (np.abs(P[:, 0]) > 0.035) * head)
    nostril = np.zeros(len(P))
    for side in (1, -1):
        nostril = np.maximum(nostril, 1 - smooth(0.003, 0.0055, np.linalg.norm(P - np.array(tuple(SNOUT[-1] + V(side * 0.011, 0.004, 0.012))), axis=1)))
    return dict(core=core, facet=facet, crack=crack, belly=belly, band=band, scute=scute, scale=scale, own=own, plate=plate, own2=own2, front=front, rear=rear, vein=vein, crescent=crescent,
                mouth=mouth.astype(float), lip=lip.astype(float), mask=mask, nostril=nostril, head=head.astype(float), up=up)


def carve_skin(o):
    P, Nn = verts(o), normals(o)
    F = skin_fields(P, Nn)
    d = (0.0006 * F["scale"] * (1 - F["head"]) + 0.0009 * F["plate"] * F["head"] - 0.0012 * F["belly"] * smooth(0.85, 1.0, F["scute"])
         + 0.0008 * F["front"] * F["vein"] - 0.003 * F["nostril"])
    set_verts(o, P + Nn * d[:, None])


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    F = skin_fields(P, Nn)
    col = mix(np.broadcast_to(GLACIER, (n, 3)), GLACIER_DEEP, smooth(0.0, 0.9, F["up"]) * 0.6)      # deepest along its back
    col = mix(col, GLACIER_PALE, smooth(0.1, -0.3, F["up"]) * 0.35 * (1 - F["belly"]))
    col = mix(col, GLACIER_PALE, (F["own"] > 0.82) * F["scale"] * 0.25)
    col = mix(col, GLACIER_DEEP * 0.75, (1 - F["scale"]) * 0.4 * (1 - F["head"]))                 # its scales' edges
    col = mix(col, FROST_EDGE * 0.92, F["band"])                     # frost crossbands: icy pale blue, a white line down their middle
    col = mix(col, FROST, F["core"] * 0.8)
    col = mix(col, BELLY, F["belly"] * 0.92)
    col = mix(col, BELLY_LINE, F["belly"] * smooth(0.82, 1.0, F["scute"]) * 0.7)
    # its hood: the front frosted ice in plates, veined with frost; the back deep, a frost crescent across it
    rim = smooth(0.08, 0.2, np.abs(P[:, 0]))
    ice = mix(np.broadcast_to(rgb(200, 232, 252), (n, 3)), GLACIER_PALE, rim * 0.7)          # pale ice, bluer toward its rim
    ice = mix(ice, ice * 1.08, smooth(0.3, 0.9, F["facet"]) * 0.6)                           # big facets catching the light
    ice = mix(ice, rgb(96, 150, 210), F["crack"] * 0.55)                                     # fine blue cracks between them
    ice = mix(ice, FROST, F["vein"])                                                         # frost veins, bold and white
    col = mix(col, ice, F["front"])
    col = mix(col, FROST, F["crescent"] * 0.9)
    # its head: plates outlined in frost, a dark mask through its eyes, a pale lip, its mouth
    head = F["head"]
    col = mix(col, FROST_EDGE * 0.8, head * (1 - F["plate"]) * 0.55 * smooth(-0.2, 0.4, Nn[:, 2]))
    col = mix(col, GLACIER_DEEP * 0.45, F["mask"] * 0.85)
    col = mix(col, GLACIER_PALE, F["lip"] * 0.5)
    col = mix(col, MOUTH, F["mouth"])
    col = mix(col, GLACIER_DEEP * 0.3, F["nostril"])
    rough = 0.32 - 0.1 * F["scale"] * (1 - F["belly"]) + 0.12 * F["belly"] - 0.12 * F["front"] + 0.2 * F["mouth"]
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_jaw(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    top = (Nn[:, 2] > 0.6).astype(float)
    d1, d2, own = cells_3d(P, 175.0, 5)
    col = mix(np.broadcast_to(BELLY, (n, 3)), GLACIER_PALE, smooth(-0.6, 0.2, Nn[:, 2]) * 0.4)
    col = mix(col, BELLY_LINE, (1 - smooth(0.0, 0.14, d2 - d1)) * 0.5)
    col = mix(col, GLACIER_PALE * 0.9, smooth(0.2, 0.55, Nn[:, 2]) * (1 - top) * 0.6)         # its lip (white, it drew a grin)
    mouth = mix(np.broadcast_to(MOUTH, (n, 3)), MOUTH_DEEP, (1 - smooth(0.01, 0.03, np.abs(P[:, 0]))) * 0.6)
    col = mix(col, mouth, top)
    paint(o, np.clip(col, 0, 1), 0.35 + 0.25 * top, np.zeros(n))


def paint_tongue(o):
    n = len(o.data.vertices)
    paint(o, np.broadcast_to(TONGUE, (n, 3)), np.full(n, 0.3), np.zeros(n))


def paint_ice(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    which = read_tag(o, "blade")
    frames = blade_frames()
    edge = np.zeros(n)
    spine = np.zeros(n)
    for k, (root, d, normal, length, side) in enumerate(frames):
        sel = which == k
        if not sel.any():
            continue
        rel = P[sel] - np.array(tuple(root))
        u = (rel @ np.array(tuple(d))) / length
        across = np.abs(rel @ np.array(tuple(d.cross(normal).normalized())))
        w = np.array([blade_width(float(np.clip(x, 0, 1))) for x in u]) + 1e-6
        edge[sel] = smooth(0.7, 1.0, across / w)
        spine[sel] = (1 - smooth(0.0, 0.25, across / w)) * smooth(0.05, 0.3, u)
    col = mix(np.broadcast_to(ICE, (n, 3)), ICE_VEIN, np.clip(edge * 0.8 + spine * 0.6, 0, 1))
    col = mix(col, FROST_EDGE, smooth(0.6, 0.85, fbm(P, 60.0, 3, 41)) * 0.25)
    paint(o, np.clip(col, 0, 1), 0.06 + 0.1 * edge, np.zeros(n))


def eye_paint(o, fr):
    """Ice-white, a cold cyan ring, a round black pupil: a cobra's, lidless and unblinking."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(214, 240, 255), rgb(120, 190, 240), smooth(0.2, 0.55, r))
    col = mix(col, rgb(36, 90, 170), smooth(0.55, 0.68, r))
    col = mix(col, rgb(10, 22, 52), smooth(0.68, 0.76, r))
    azi = np.arctan2(py, px)
    col = col * (0.88 + 0.12 * np.sin(azi * 30 + np.sin(azi * 4) * 2))[:, None]
    col = mix(col, rgb(4, 8, 18), 1 - smooth(0.17, 0.21, r))           # a pinpoint pupil: an intent stare
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.04), np.zeros(len(px)))


def paint_all(pieces, frames, data):
    carve_skin(pieces["Skin"])
    paint_skin(pieces["Skin"])
    paint_jaw(pieces["Jaw"])
    paint_tongue(pieces["Tongue"])
    paint_ice(pieces["Ice"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)


VIEWS = [(0, -1, 0.2), (0.62, -0.72, 0.3), (1, 0, 0.12), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.6, -0.3, 0.9)]
VIEW_AT = (0, 0.05, 0.4)
FACE_AT = (0, -0.23, 0.79)
EXTRA = [(0.15, -1, 0.15, 0.55, FACE_AT), (1, -0.5, 0.25, 0.55, FACE_AT), (0.3, -1, 0.05, 1.0, (0, -0.1, 0.62)), (0, 1, 0.2, 1.0, (0, -0.06, 0.62)),
         (0.7, -0.4, 0.5, 1.4, (0, 0.13, 0.08))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "spine len", round(float(SPINE_S[-1]), 3), "coil end", COIL_END, tuple(round(v, 3) for v in SPINE[COIL_END]), flush=True)
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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.4, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 5200
PIECES = ("Skin", "EyeL", "EyeR", "Jaw", "Tongue")
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "Jaw": 1.5, "Tongue": 1.0, "Ice": 1.2}


def is_head(c):
    """Its head and hood: they get more of the atlas."""
    return c.z > HOOD_Z[0] - 0.02


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    select_only([lows["Skin"]])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)          # every face outward
    bpy.ops.object.mode_set(mode="OBJECT")
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    for fr in frames.values():
        c = np.array(tuple(fr.centre))
        d = np.linalg.norm(P - c, axis=1)
        band = np.abs(d - EYE_R) < 0.0018
        P[band] = c + (P[band] - c) / d[band, None] * (EYE_R - 0.002)        # level with an eyeball, the socket's skin went into it (they z-fight)
    set_verts(lows["Skin"], P)
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 20, 12)
    lows["Jaw"] = build_jaw(N + "JawLow", GAME, nt=14, per=3)
    lows["Tongue"] = build_tongue(N + "TongueLow", GAME)
    lows["Ice"] = build_ice(N + "Ice", GAME, 4, 2)
    data["blade"] = read_tag(lows["Ice"], "blade")
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
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


UV_ANGLE = {"Skin": 66, "Ice": 40, "Jaw": 50}     # the projection's angle per piece (wider: fewer, bigger charts, a fuller atlas)


def serpent_unwrap(lows, margin=0.0035):
    """Each piece on its own: the projection's charts as seams (and one round its neck, where the head's share changes), an angle-based unwrap that
    can't fold a chart over itself, collapsed fragments projected again, each scaled to its share; all packed together."""
    for key, o in lows.items():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        select_only([o])
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




# ---------- the skeleton: a spine, from where it rises, forward up its front and back along its coil ----------
UP_N, COIL_N = 7, 12
LAST = len(SPINE) - 1
UP_AT = [COIL_END + round(k * (LAST - COIL_END) / UP_N) for k in range(UP_N)]       # Up1 where it rises (the base carries the coil's last stretch)
COIL_AT = [COIL_END - round(k * COIL_END / (COIL_N + 1)) for k in range(1, COIL_N + 1)]
CHAIN = [("Coil%d" % k, COIL_AT[k - 1]) for k in range(COIL_N, 0, -1)] + [("Base", COIL_END)] + [("Up%d" % k, UP_AT[k - 1]) for k in range(1, UP_N + 1)] + [("Head", LAST)]
CHAIN_NAMES = [n for n, _ in CHAIN]
HOOD_T = (0.3, 0.72)                 # the hood's two bones a side: their heights up it


def hood_bone_parent(t):
    z = HOOD_Z[0] + (HOOD_Z[1] - HOOD_Z[0]) * t
    i = int(np.argmin([abs(SPINE[k].z - z) + (9 if k < COIL_END else 0) for k in range(len(SPINE))]))
    owner = "Base"
    for name, at in CHAIN:
        if name.startswith("Up") and at <= i:
            owner = name
    return owner, i


def hood_bones():
    out = []
    for side, tag in ((1, "L"), (-1, "R")):
        for k, t in enumerate(HOOD_T):
            parent, i = hood_bone_parent(t)
            out.append(("Hood%s%d" % (tag, k + 1), SPINE[i] + V(side * 0.06, 0, 0), parent))
    return out


def jaw_hinge():
    return JAW[0].copy()


def tongue_root():
    return V(0, TONGUE_PATH[0].y, mouth_z(TONGUE_PATH[0].y))


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Base", SPINE[COIL_END].copy(), "Root")]
    parent = "Base"
    for k in range(1, UP_N + 1):
        bones.append(("Up%d" % k, SPINE[UP_AT[k - 1]].copy(), parent))
        parent = "Up%d" % k
    bones.append(("Head", SPINE[LAST].copy(), parent))
    bones += [("Jaw", jaw_hinge(), "Head"), ("Tongue", tongue_root(), "Jaw"), ("Fangs", FANG_ROOT.copy(), "Head")]      # its tongue in its jaw's floor
    parent = "Base"
    for k in range(1, COIL_N + 1):
        bones.append(("Coil%d" % k, SPINE[COIL_AT[k - 1]].copy(), parent))
        parent = "Coil%d" % k
    bones += hood_bones()
    return armature(bones)


def chain_mids():
    """Where each spine bone takes over, along the spine (0 tail tip, 1 head): the middle of the stretch it carries (a coil bone carries the stretch
    tailward of it, an up bone the stretch headward), so its share passes across each joint, never at it."""
    fs = [float(SPINE_F[at]) for _, at in CHAIN]
    mids = []
    for k, (name, at) in enumerate(CHAIN):
        if name.startswith("Coil"):
            lo = fs[k - 1] if k > 0 else 0.0
            mids.append((lo + fs[k]) / 2)
        elif name == "Base":
            mids.append((fs[k - 1] + fs[k]) / 2)
        elif name == "Head":
            mids.append(1.01)
        else:
            mids.append((fs[k] + fs[k + 1]) / 2)
    return mids


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def body_weights(P):
    mids = chain_mids()
    f, _ = nearest_on(SPINE, P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        w = chain_weight(CHAIN_NAMES, mids, float(f[i]))
        head_like = y < -0.12 and z > HOOD_Z[1] - 0.06 and abs(x) < 0.08
        if head_like:
            w = blend(w, {"Head": 1.0}, float(smooth(-0.12, -0.16, y)))
        # the hood's broad halves: on its own bones, out from the column
        t = (z - HOOD_Z[0]) / (HOOD_Z[1] - HOOD_Z[0])
        share = float(smooth(0.065, 0.11, abs(x))) * float(smooth(-0.05, 0.05, t)) * (1 - float(smooth(0.95, 1.05, t))) * (not head_like)
        if share > 0:
            tag = "L" if x > 0 else "R"
            w = blend(w, chain_weight(["Hood%s1" % tag, "Hood%s2" % tag], HOOD_T, float(np.clip(t, 0, 1))), share)
        out.append(w)
    return out


def ice_weights(blade):
    frames = blade_frames()
    out = []
    for k in blade:
        root, d, normal, length, side = frames[int(k)]
        t = (root.z - HOOD_Z[0]) / (HOOD_Z[1] - HOOD_Z[0])
        tag = "L" if side > 0 else "R"
        out.append({"Hood%s%d" % (tag, 1 if t < 0.5 else 2): 1.0})          # each blade rigid: glass never bends
    return out


def game_glows(frames):
    return {"Fangs": build_fangs(N + "Fangs_Glow_" + FANG_HEX, GAME, sides=6, per=2),
            "Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-20, 22, 0.0032, 8), (18, -16, 0.0015, 5)))}


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in "LR":
        rigid(lows["Eye" + tag], "Head")
    rigid(lows["Jaw"], "Jaw")
    rigid(lows["Tongue"], "Tongue")
    ice = lows.pop("Ice")
    weigh(ice, ice_weights(data["blade"]))
    rigid(glows["Fangs"], "Fangs")
    rigid(glows["Glints"], "Head")
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body, ice] + list(glows.values()))
    return body, ice


# ---------- poses: the spine fitted to a curve, written as PetRig's tables (turns in the game's axes) ----------
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
I3 = Matrix.Identity(3)


def from_game(v):
    return CM @ (Matrix.Rotation(v[0], 3, "X") @ Matrix.Rotation(v[1], 3, "Y") @ Matrix.Rotation(v[2], 3, "Z")) @ CM


def to_game(R):
    e = (CM @ R @ CM).to_euler("ZYX")
    return (e.x, e.y, e.z)


def game_vec(b):
    return (-b.x, b.z, b.y)


def blender_vec(gv):
    return V(-gv[0], gv[2], gv[1])


def frame_rot(a, n, a2, n2):
    a, a2 = a.normalized(), a2.normalized()
    n = (n - a * n.dot(a)).normalized()
    n2 = (n2 - a2 * n2.dot(a2)).normalized()
    F0 = Matrix((a, n, a.cross(n))).transposed()
    F1 = Matrix((a2, n2, a2.cross(n2))).transposed()
    return F1 @ F0.transposed()


SNOUT_TIP = SNOUT[-1]


def segment(points, name, at):
    """A spine bone's own stretch in `points` (the spine, rest or posed): its head and where its stretch ends."""
    i = CHAIN_NAMES.index(name)
    if name.startswith("Coil") or name == "Base":
        end = CHAIN[i - 1][1] if i > 0 else 0
    elif name == "Head":
        return points[at], None
    else:
        end = CHAIN[i + 1][1]
    return points[at], points[end]


def transported_backs(points):
    """Its back's direction at every point of a spine, carried from the tail tip (up, lying on the ground) along it by the least turn at each step:
    never twisting. (A rule from the direction alone flipped half a turn where the column leaned from forward to back, and the bones twisted.)"""
    out = []
    tan = (points[1] - points[0]).normalized()
    back = (V(0, 0, 1) - tan * tan.z).normalized()
    for i in range(len(points)):
        t2 = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        back = tan.rotation_difference(t2) @ back
        back = (back - t2 * back.dot(t2)).normalized()
        tan = t2
        out.append(back)
    return out


REST_BACKS = transported_backs(SPINE)


def fit_spine(target, head_dir=None, head_back=None):
    """World turns for every spine bone so the spine lies along `target` (a point per rest spine point, the same spacing), and the move of its base."""
    W = {}
    tb = transported_backs(target)
    for name, at in CHAIN:
        if name == "Head":
            continue
        h0, e0 = segment(SPINE, name, at)
        h1, e1 = segment(target, name, at)
        d0, d1 = e0 - h0, e1 - h1
        W[name] = frame_rot(d0, REST_BACKS[at], d1, tb[at])
    rest_head = (SNOUT_TIP - SPINE[LAST]).normalized()
    hd_dir = (head_dir or (target[LAST] - target[LAST - 6])).normalized()
    W["Head"] = frame_rot(rest_head, V(0, 0, 1), hd_dir, head_back or V(0, 0, 1))
    return W, target[COIL_END] - SPINE[COIL_END]


def locals_from_world(W):
    parent = {"Base": None}
    for k in range(1, UP_N + 1):
        parent["Up%d" % k] = "Base" if k == 1 else "Up%d" % (k - 1)
    parent["Head"] = "Up%d" % UP_N
    for k in range(1, COIL_N + 1):
        parent["Coil%d" % k] = "Base" if k == 1 else "Coil%d" % (k - 1)
    out = {}
    for name, R in W.items():
        p = parent[name]
        out[name] = R if p is None else W[p].inverted() @ R
    return out


def table_of(local, base_move=None, extra=None):
    table = {}
    for b, R in local.items():
        e = tuple(round(float(x), 4) for x in to_game(R))
        if b == "Base" and base_move is not None and base_move.length > 1e-5:
            table[b] = e + (tuple(round(float(x), 4) for x in game_vec(base_move)),)
        elif max(abs(x) for x in e) >= 1e-4:
            table[b] = e
    for b, v in (extra or {}).items():
        table[b] = tuple(round(float(x), 4) if not isinstance(x, tuple) else tuple(round(float(y), 4) for y in x) for x in v)
    return table


def along(path, s):
    """The point at arc length s along a polyline (clamped)."""
    L = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    s = float(np.clip(s, 0, L[-1]))
    i = min(int(np.searchsorted(L, s, side="right")) - 1, len(a) - 2)
    f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
    return V(*(a[i] * (1 - f) + a[i + 1] * f))


def column_curve(ctrl):
    """Its reared front along a curve that leaves the coil as it does at rest (out to the side, then up: its first stretch kept) and goes on through
    ctrl, the rest of it stretched or shrunk to its length; the coil as it rests. (Leaving it straight up, every pose wrenched the column's base.)"""
    base = SPINE[COIL_END]
    need = SPINE_S[LAST] - SPINE_S[COIL_END]
    fixed = [base, COLUMN[0], COLUMN[1]]
    pivot = COLUMN[1]
    pts = fixed + ctrl
    for _ in range(4):
        path = catmull(pts, 12)
        have = arc_lengths(path)[-1]
        k = 1 + (need - have) / max(arc_lengths(catmull([pivot] + pts[3:], 12))[-1], 1e-6)
        pts = fixed + [pivot + (p - pivot) * k for p in pts[3:]]
    path = catmull(pts, 12)
    L = arc_lengths(path)[-1]
    out = list(SPINE[:COIL_END + 1])
    for i in range(COIL_END + 1, len(SPINE)):
        out.append(along(path, (SPINE_S[i] - SPINE_S[COIL_END]) / need * L))
    return out


def jaw_open(a):
    return to_game(Matrix.Rotation(a, 3, "X"))


def fangs_out(w=1.0):
    return to_game(Matrix.Rotation(-FANG_FOLD * w, 3, "X"))


def hood_turns(spread):
    """Both hood halves swung back (spread < 0: folded against the neck) or forward wider (> 0), about the column's upright."""
    out = {}
    for tag, sign in (("L", 1), ("R", -1)):
        for k in (1, 2):
            out["Hood%s%d" % (tag, k)] = (0, -spread * sign * (1.0 if k == 1 else 0.85), 0)
    return out


RIPPLE = 0.07                        # radians: each coil bone's sway as a ripple runs round its coil while it glides
RIPPLE_STEP = 0.9                    # radians of the ripple's phase from one coil bone to the next


def ripple(phase, amount=1.0):
    """A ripple running back round its coil: each coil bone swayed in turn about the upright (the coil stays flat on the ground). Each bone's own
    turn is the difference from the one before, so each lies at most RIPPLE off its rest (as plain turns they added up down the chain)."""
    world = [0.0] + [RIPPLE * amount * math.sin(phase - RIPPLE_STEP * k) for k in range(1, COIL_N + 1)]
    return {"Coil%d" % k: (0, world[k] - world[k - 1], 0) for k in range(1, COIL_N + 1)}


def pose_tables():
    t = {}
    # gliding: it does not uncoil (laid out, its waves folded its thick body over itself, and it stretched to many times its coil): it leans forward,
    # head low and level, its hood half folded, and slides on its coil while a ripple runs round it
    W, move = fit_spine(column_curve([V(0.03, -0.2, 0.42), V(0.0, -0.3, 0.54), V(0, -0.38, 0.58)]), V(0, -1, -0.12))
    t["Glide"] = table_of(locals_from_world(W), move, hood_turns(-0.45))
    for k in range(4):
        t["Glide%d" % k] = dict(t["Glide"], **{n: tuple(round(x, 4) for x in v) for n, v in ripple(TAU * k / 4).items()})
    # on the wing: coiled as it rests, hovering, its hood half folded
    t["Hover"] = {n: tuple(round(x, 4) for x in v) for n, v in hood_turns(-0.2).items()}       # (its tail hung down, it tore from the coil it lies by)
    W, move = fit_spine(column_curve([V(0.04, -0.11, 0.48), V(0.0, -0.08, 0.7), V(0, -0.12, 0.86), V(0, -0.15, 0.91)]), V(0, -1, 0.35))
    t["Rear"] = table_of(locals_from_world(W), move, {**hood_turns(0.25), "Jaw": jaw_open(0.62), "Fangs": fangs_out()})
    W, move = fit_spine(column_curve([V(0.04, -0.24, 0.4), V(0.0, -0.44, 0.44), V(0, -0.6, 0.38), V(0, -0.7, 0.32)]), V(0, -1, -0.3))
    t["Strike"] = table_of(locals_from_world(W), move, {**hood_turns(0.3), "Jaw": jaw_open(0.7), "Fangs": fangs_out()})
    hiss = {"Up6": (0.12, 0, 0), "Up7": (0.12, 0, 0), "Head": (-0.1, 0, 0), "Jaw": jaw_open(0.42), "Fangs": fangs_out(), **hood_turns(0.22)}
    t["Hiss"] = {k: tuple(round(float(x), 4) for x in v) for k, v in hiss.items()}
    t["Fold"] = {k: tuple(round(x, 4) for x in v) for k, v in hood_turns(-0.55).items()}
    t["Look"] = {"Up5": (0, 0.25, 0), "Up6": (0, 0.25, 0), "Up7": (0, 0.25, 0), "Head": (0.0, 0.3, 0.08)}
    rise = TONGUE_SINK + (mouth_z(TONGUE_PATH[0].y - 0.07) - mouth_z(TONGUE_PATH[0].y))     # into the gap, and up the mouth line's slope as it slides
    t["TongueUp"] = {"Tongue": (0, 0, 0, (0, round(TONGUE_SINK, 4), 0))}           # first up into the gap, inside its shut mouth (rising and sliding at
    t["Tongue"] = {"Tongue": (0, 0, 0, (0, round(rise, 4), -0.07))}                 # once, its tip came out through its chin); then out between its lips
    return t


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
        out[bone] = to_game(q.to_matrix()) + (tuple(ma.lerp(mb, w)),)
    return out


# ---------- checks ----------
def posed(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    tris = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return co.reshape(-1, 3), tris


def dominant(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in o.data.vertices]


def pairs(co_a, tris_a, fa, co_b, tris_b, fb):
    if not fa or not fb:
        return 0
    ta = BVHTree.FromPolygons([tuple(c) for c in co_a], [tris_a[f] for f in fa])
    tb = BVHTree.FromPolygons([tuple(c) for c in co_b], [tris_b[f] for f in fb])
    return len(ta.overlap(tb))


class Checker:
    def __init__(self, body, ice, fangs):
        self.body, self.ice, self.fangs = body, ice, fangs
        self.dom = dominant(body)
        fp = np.zeros(len(body.data.polygons), dtype=int)
        body.data.attributes["piece"].data.foreach_get("value", fp)
        _, tris = posed(body)
        self.tris = tris
        d = self.dom
        skin = [i for i, p in enumerate(fp) if p == PIECES.index("Skin")]
        rank = {n: k for k, n in enumerate(CHAIN_NAMES)}
        # every skin face on one spine bone (by its first corner): a face meets only its own bone's and its neighbours' near the joints
        self.by_rank = {}
        for i in skin:
            r = rank.get(d[tris[i][0]])
            if r is not None:
                self.by_rank.setdefault(r, []).append(i)
        self.jaw = [i for i, p in enumerate(fp) if p == PIECES.index("Jaw")]
        self.tongue = [i for i, p in enumerate(fp) if p == PIECES.index("Tongue")]
        self.head = [i for i in skin if d[tris[i][0]] == "Head"]
        self.not_hood = [i for i in skin if not d[tris[i][0]].startswith(("Hood", "Up", "Head"))]
        self.skin_v = np.zeros(len(body.data.vertices), dtype=bool)
        for i in skin:
            for v in tris[i]:
                self.skin_v[v] = True

    def run(self):
        co, tris = posed(self.body)
        out = {}
        ranks = sorted(self.by_rank)
        hits = 0
        self.which = {}
        for a in ranks:
            for b in ranks:
                if b >= a + 3:
                    n = pairs(co, tris, self.by_rank[a], co, tris, self.by_rank[b])
                    if n:
                        self.which[(CHAIN_NAMES[a], CHAIN_NAMES[b])] = n
                        hits += n
        out["body x body"] = hits
        ico, itris = posed(self.ice)
        out["ice x body"] = pairs(ico, itris, list(range(len(itris))), co, tris, self.not_hood)
        fco, ftris = posed(self.fangs)
        out["fangs x jaw"] = pairs(fco, ftris, list(range(len(ftris))), co, tris, self.jaw)
        out["tongue x jaw"] = pairs(co, tris, self.tongue, co, tris, self.jaw)
        out["skin z"] = round(float(co[self.skin_v, 2].min()), 4)
        out["ice z"] = round(float(ico[:, 2].min()), 4)
        return out


def fangs_hidden(fangs, body):
    """With its mouth shut, whether every vertex of its fangs is inside its head (a ray up from each meets its skin an odd number of times)."""
    co, tris = posed(body)
    tree = BVHTree.FromPolygons([tuple(c) for c in co], tris)
    fco, _ = posed(fangs)
    outside = 0
    for p in fco:
        hits, o = 0, Vector(p)
        d = V(0, 0, 1)
        while True:
            loc, nrm, idx, dist = tree.ray_cast(o, d, 1.0)
            if loc is None:
                break
            hits += 1
            o = loc + d * 1e-5
        outside += hits % 2 == 0
    return outside


TRANSITIONS = [("Rest", "Glide"), ("Glide0", "Glide1"), ("Glide1", "Glide2"), ("Glide2", "Glide3"), ("Glide3", "Glide0"), ("Rest", "Hover"),
               ("Glide", "Hover"), ("Rest", "Rear"), ("Rear", "Strike"), ("Strike", "Rest"), ("Rest", "Hiss"), ("Rest", "Fold"), ("Glide", "Rear"),
               ("Rest", "Look"), ("TongueUp", "Tongue")]
MINS = ("skin z", "ice z")


def check_transitions(rig, chk, tables):
    tables = dict(tables, Rest={})
    for na, nb in TRANSITIONS:
        worst = {}
        for k in range(11):
            pose(rig, spec(slerp_tables(tables[na], tables[nb], k / 10)))
            for key, v in chk.run().items():
                worst[key] = min(worst.get(key, 9.0), v) if key in MINS else max(worst.get(key, 0), v)
        flag = {k: v for k, v in worst.items() if (k not in MINS and v > 0) or (k in MINS and v < -0.004)}
        print("TRANSITION", na, "->", nb, flag if flag else "clean", "| lows", {k: worst[k] for k in MINS}, flush=True)


POSE_VIEWS = [(0.62, -0.72, 0.4, 3.6, (0, 0.1, 0.3)), (1, -0.05, 0.15, 3.6, (0, 0.1, 0.3)), (0, -0.05, 1, 3.6, (0, 0.1, 0.0)), (-0.4, 1, 0.5, 3.6, (0, 0.1, 0.3))]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    if STAGE == "all":
        serpent_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.3, 0.4, 0.6, 1), far=("Skin",), reach=(0.003, 0.008),
                 far_reach=(0.006, 0.016), reaches={"Ice": (0.0015, 0.004), "Tongue": (0.0012, 0.003), "Jaw": (0.002, 0.006)})
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
    rig = skeleton()
    body, ice = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "ICE tris", sum(len(p.vertices) - 2 for p in ice.data.polygons),
          "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), max(len(v.groups) for v in ice.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body, ice] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    chk = Checker(body, ice, glows["Fangs"])
    pose(rig, {})
    print("POSE Rest", chk.run(), "fang verts outside the head (mouth shut)", fangs_hidden(glows["Fangs"], body), flush=True)
    if "which" in ARGS:
        print("   where", chk.which, flush=True)
    tables = pose_tables()
    only = ARGS[ARGS.index("only") + 1].split(",") if "only" in ARGS else None
    for name, table in tables.items():
        if only and name not in only:
            continue
        pose(rig, spec(table))
        print("POSE", name, chk.run(), flush=True)
        if "which" in ARGS:
            print("   where", chk.which, flush=True)
        if STAGE == "rig" and "noshots" not in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=480)
    if "transitions" in ARGS or STAGE == "all":
        check_transitions(rig, chk, tables)
    lib = {k: spec(v) for k, v in tables.items()}
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    if "tables" in ARGS or STAGE == "all":
        for name, table in tables.items():
            print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join(("%g" % x) if not isinstance(x, tuple) else ("%g, %g, %g" % x) for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
        for name in ("Base", "Head", "Jaw", "Fangs", "Tongue", "Up4"):
            p = rig.data.bones[name].head_local
            print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.4, size=560)
        for name in ("Glide1", "Hover", "Rear", "Strike", "Hiss", "Look"):
            pose(rig, spec(tables[name]))
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS[:2], size=480)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 3.4, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values()), extras=[ice]), flush=True)
    print("DONE", flush=True)

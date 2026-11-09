"""The Glacier Puff (Common, Ice; Elemental Core Egg): "A round little ball of old ice that has never once melted, not even in the mouth of a volcano."

An ice pufferfish (the owner's choice, 2026-11-09), in a design language of its own: polished glacier ice. A round little fish that swims through the air:
deep blue at its heart, frosted pale with rime on top, white-blue beneath, banded through with the layers of old glacier ice, with air bubbles caught in
it. A blunt face; big domed eyes in raised rims and no lids (a fish), their irises sapphire round a big black pupil, each eye swivelling on its own; a
small round puckered mouth with a beak of white teeth. Stubby fluttering pectoral fins, small dorsal and anal fins, a rounded tail fan, all pale and fine-
rayed. Calm, it is smooth; startled, it puffs: its body balloons round its middle (eight puff bones, its face and tail keeping their size) and spines of
hoarfrost, hidden just under the ice, slide out of it.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/glacier_puff.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It floats: its middle about half a metre up. The maps go to assets/pets/ElementalCoreEgg/.

What touches what: body, face, cheeks, eye rims and tail stem are one skin; each eye is its own sphere set in its rim, a little over half of it showing; the
lips are two half rings round the mouth (the lower on the jaw), a dark mouth inside them and a beak plate behind each lip; each fin roots inside the skin;
every spine lies wholly inside the body at rest, its tip under the surface, and slides out along its puff bone when it puffs.
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
PET = "GlacierPuff"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ElementalCoreEgg")

# ---------- colours: glacier ice ----------
ICE_DEEP, ICE, ICE_PALE, RIME, BELLY = rgb(28, 92, 168), rgb(84, 162, 222), rgb(178, 222, 246), rgb(236, 248, 255), rgb(214, 236, 250)
BAND = rgb(46, 118, 196)
FIN, FIN_RAY = rgb(214, 238, 252), rgb(120, 182, 228)
LIP, MOUTH_IN, TOOTH = rgb(196, 226, 246), rgb(18, 34, 70), rgb(246, 250, 252)
FROST = rgb(240, 250, 255)
GLINT_HEX = "ffffff"

# ---------- the frame of it ----------
ZC = 0.45                     # its middle's height
BODY_PATH = catmull([V(0, -0.186, ZC - 0.004), V(0, -0.12, ZC), V(0, -0.02, ZC), V(0, 0.08, ZC + 0.002), V(0, 0.172, ZC + 0.008)], 12)
BODY_W = ((0, 0.022), (0.05, 0.072), (0.14, 0.112), (0.3, 0.142), (0.48, 0.15), (0.68, 0.13), (0.85, 0.088), (1, 0.042))     # half-widths, front to the tail stem
BODY_H = ((0, 0.024), (0.05, 0.076), (0.14, 0.118), (0.3, 0.146), (0.48, 0.15), (0.68, 0.132), (0.85, 0.09), (1, 0.046))     # half-heights
STEM = [V(0, 0.13, ZC + 0.006), V(0, 0.17, ZC + 0.008), V(0, 0.198, ZC + 0.01), V(0, 0.222, ZC + 0.012)]
EYE_AXIS = V(0.76, -0.55, 0.34).normalized()
EYE_C, EYE_R = V(0.088, -0.098, ZC + 0.078) + EYE_AXIS * 0.011, 0.04          # (out of its rim far enough that a little over half of it shows)
MOUTH_C = V(0, -0.184, ZC - 0.026)
MOUTH_RX, MOUTH_RZ, LIP_R = 0.018, 0.012, 0.0072
JAW_HINGE = V(0, -0.162, ZC - 0.048)          # below and behind the lower lip, so it swings down and out of the chin, never into it
# the fins: root line (two ends, its left), and how far and which way each fan reaches
PEC_ROOT = (V(0.126, -0.032, ZC + 0.024), V(0.13, -0.014, ZC - 0.016))
DORSAL_ROOT = (V(0, 0.07, ZC + 0.135), V(0, 0.128, ZC + 0.112))
ANAL_ROOT = (V(0, 0.07, ZC - 0.133), V(0, 0.128, ZC - 0.11))
CAUDAL_ROOT = (V(0, 0.214, ZC + 0.042), V(0, 0.214, ZC - 0.022))
# the puff: eight bones round its length, each pushing out the ice on its side; the face and tail keep their size
ZONES = 8
PUFF_Y = 0.035                # where along it the puff bones sit
PUFF_T, SPIKE_S = 0.06, 0.054  # metres a puff bone moves out at full puff, and how much further its spines slide out of the ice
SPINE_L, SPINE_DEPTH = 0.07, 0.007      # a spine's length, and how far under the surface its tip lies at rest: puffed, 2 cm of it stays in the ice


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


_SMOOTH = {}


def sprof(knots, f):
    """A profile through its knots with no corners at them (a straight-line profile creases the skin at every knot)."""
    if knots not in _SMOOTH:
        pts = catmull([V(u, w, 0) for u, w in knots], 24)
        _SMOOTH[knots] = (np.array([p.x for p in pts]), np.array([p.y for p in pts]))
    xs, ys = _SMOOTH[knots]
    return float(np.interp(f, xs, ys))


def path_frames(path):
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0) - tan * tan.x
        side = side.normalized() if side.length > 1e-5 else V(1, 0, 0)
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def loft(m, path, w_fn, h_fn, nt=48):
    fr = path_frames(path)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        w, h = w_fn(f), h_fn(f)
        rings.append([m.bm.verts.new(p + side * (w * math.cos(TAU * k / nt)) + up * (h * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


def make_tags(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new(bm, before, **values):
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


def zone_dir(k):
    """Puff bone k's way out: round its length, 0 its left (+X), then up, its right, down."""
    a = TAU * k / ZONES
    return V(math.cos(a), 0, math.sin(a))


def puff_reach(y, x=0.0, z=ZC + 0.1):
    """How much of the puff a point takes: all of it round its middle, none on its face or its tail. Its belly and chin balloon further forward than its
    upper face, where its eyes are; the ramps are long and smooth, so it swells round, never boxy."""
    below = float(smooth(0.0, -0.6, (z - ZC) / max(1e-6, math.hypot(x, z - ZC))))
    front = -0.02 - 0.07 * below
    return float(smooth(front - 0.095, front, y) * (1 - smooth(0.11, 0.19, y)))


# ---------- the skin ----------
def build_skin():
    m = Mesh()
    loft(m, BODY_PATH, lambda f: sprof(BODY_W, f), lambda f: sprof(BODY_H, f))
    m.tube(catmull(STEM, 6), lambda f: sprof(((0, 0.07), (0.45, 0.044), (1, 0.03)), f), sides=32)     # the tail stem, running out of the body
    for side in (1, -1):
        m.ball(V(side * 0.062, -0.118, ZC - 0.022), (0.042, 0.045, 0.042), 32, 20)     # the cheek
        e = mir(EYE_C, side)
        a = mir(EYE_AXIS, side)
        u = a.orthogonal().normalized()
        w = a.cross(u).normalized()
        rim = [e - a * 0.004 + (u * math.cos(TAU * k / 32) + w * math.sin(TAU * k / 32)) * (EYE_R * 1.02) for k in range(33)]
        m.tube(rim, lambda f: 0.0095, sides=16, plane=a, caps=False)                    # the eye's raised rim (framed on its axis: no twist)
    m.ball(MOUTH_C + V(0, 0.014, 0.002), (0.028, 0.02, 0.024), 32, 20)                # the pursed muzzle round the mouth
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0024, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the eyes ----------
def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, (40.0, 120.0, 0.002), (-40.0, -128.0, 0.002)) for side, tag in ((1, "L"), (-1, "R"))}


def eye_paint(o, fr):
    """A fish's eye: a big black pupil, a sapphire iris shading to turquoise and streaked out from it, a dark ring at its edge; glossy all over."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    ang = np.arctan2(py, px)
    col = mix(rgb(70, 196, 230), rgb(24, 70, 160), smooth(0.45, 0.85, r))
    col = col * (0.85 + 0.25 * (0.5 + 0.5 * np.sin(ang * 23 + r * 9)))[:, None] ** 1
    col = mix(col, rgb(8, 18, 40), 1 - smooth(0.4, 0.46, r))           # the pupil
    col = mix(col, rgb(10, 26, 60), smooth(0.86, 0.95, r))              # the dark ring round the iris
    col = mix(col, rgb(196, 230, 248), smooth(1.15, 1.3, r))            # (the back of the ball, hidden in the rim)
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.04), np.zeros(len(px)))


# ---------- the mouth ----------
def lip_ring(upper, per=24):
    """Half of the ring of lip round the mouth: the upper half or the lower; each end tucked a little back into the muzzle."""
    gap = 0.12          # (the halves stop short of each other at the corners, their ends tucked in: two ends meeting level z-fight)
    a0, a1 = (gap, math.pi - gap) if upper else (math.pi + gap, TAU - gap)
    pts = []
    for k in range(per + 1):
        a = a0 + (a1 - a0) * k / per
        p = MOUTH_C + V(math.cos(a) * MOUTH_RX, 0, math.sin(a) * MOUTH_RZ)
        end = 1 - min(k, per - k) / (per * 0.12) if min(k, per - k) < per * 0.12 else 0.0
        pts.append(p + V(0, 0.006 * end, 0))
    return pts


def build_lips(name, coll, sides=16, per=24):
    m = Mesh()
    make_tags(m.bm, ints=("lower",))
    for upper in (True, False):
        before = set(m.bm.verts)
        m.tube(lip_ring(upper, per), lambda f: LIP_R * (0.75 + 0.25 * math.sin(math.pi * f)), sides=sides, plane=V(0, 1, 0))     # (framed on the ring's axis: no twist)
        tag_new(m.bm, before, lower=0 if upper else 1)
    return m.finish(name, coll)


def build_mouth_inside(name, coll, seg=24, rings=14):
    """The dark of the mouth, set just behind the lips, and a beak plate of white teeth behind each lip."""
    m = Mesh()
    make_tags(m.bm, ints=("lower",))
    before = set(m.bm.verts)
    m.ball(MOUTH_C + V(0, 0.012, 0), (MOUTH_RX * 0.95, 0.012, MOUTH_RZ * 0.95), seg, rings)
    tag_new(m.bm, before, lower=0)
    for upper in (True, False):
        before = set(m.bm.verts)
        z = MOUTH_RZ * (0.45 if upper else -0.45)
        m.ball(MOUTH_C + V(0, 0.002, z), (MOUTH_RX * 0.62, 0.0045, MOUTH_RZ * 0.32), seg, rings)
        tag_new(m.bm, before, lower=0 if upper else 1)
    return m.finish(name, coll)


# ---------- the fins ----------
def fin_point(root, reach, spread, flat_axis, u, v, rounder=0.35):
    """A fan: u from the root out, v across it. reach: (direction at v=0, direction at v=1, length). flat_axis: the fan's face."""
    a, b = root
    p0 = a.lerp(b, v)
    d0, d1, length = reach
    d = d0.slerp(d1, v) if d0.angle(d1) > 1e-4 else d0
    edge = 1 - rounder * (2 * v - 1) ** 2                 # a rounded edge
    wave = 1 + 0.06 * math.cos(v * math.pi * spread)       # scalloped between its rays
    return p0 + d.normalized() * (length * u * edge * (wave if u > 0.85 else 1))


FIN_KINDS = {
    "PecL": (PEC_ROOT, (V(0.85, 0.5, 0.42), V(0.85, 0.55, -0.34), 0.088), 8),
    "Dorsal": (DORSAL_ROOT, (V(0, 0.4, 0.92), V(0, 0.95, 0.3), 0.062), 7),
    "Anal": (ANAL_ROOT, (V(0, 0.4, -0.92), V(0, 0.95, -0.3), 0.056), 7),
    "Caudal": (CAUDAL_ROOT, (V(0, 0.85, 0.6), V(0, 0.85, -0.6), 0.1), 10),
}


FIN_TREE = []          # the skin's tree, once it is built: every fin's root is set on its surface


def on_skin(p, outward):
    """Where a point lies on the skin, seen from outside along `outward`; the point itself before the skin exists."""
    if not FIN_TREE:
        return p
    hit, _, _, _ = FIN_TREE[0].ray_cast(p + outward * 0.3, -outward, 0.6)
    return hit if hit is not None else p


def fin_outward(key, p):
    return V(p.x, 0, p.z - ZC).normalized() if key.startswith("Pec") else (V(0, 0, 1) if key == "Dorsal" else V(0, 0, -1) if key == "Anal" else V(0, 1, 0))


def fin_list():
    """Each fin: its key, its root line ON the skin, its reach, its rays (a hand-placed root stood clear of the body: the dorsal fin floated)."""
    out = []
    for key, (root, reach, rays) in FIN_KINDS.items():
        if key != "Caudal":
            root = tuple(on_skin(p, fin_outward(key, p)) for p in root)
        out.append((key, root, reach, rays))
        if key == "PecL":
            out.append(("PecR", tuple(mir(p, -1) for p in root), (mir(reach[0], -1), mir(reach[1], -1), reach[2]), rays))
    return out


FIN_TAG = {"PecL": 0, "PecR": 1, "Dorsal": 2, "Anal": 3, "Caudal": 4}


def build_fins(name, coll, nu, nv):
    m = Mesh()
    make_tags(m.bm, ints=("fin",))
    for key, root, reach, rays in fin_list():
        before = set(m.bm.verts)
        a, b = root
        root_in = tuple(q - fin_outward(key, q) * 0.006 for q in root) if key != "Caudal" else root      # (rooted a little inside the skin)
        m.sheet(lambda u, v, r=root_in, re=reach, n=rays: tuple(fin_point(r, re, n, None, u, v)), lambda u, v: 0.0042 * (1 - 0.55 * u) + 0.0008, nu, nv)
        tag_new(m.bm, before, fin=FIN_TAG[key])
    return m.finish(name, coll)


def paint_fins(o, nu, nv):
    fins = fin_list()
    per = (nu + 1) * (nv + 1) * 2
    uu, vv, rays = [], [], []
    for key, root, reach, n in fins:
        for i in range(nu + 1):
            for j in range(nv + 1):
                uu += [i / nu] * 2
                vv += [j / nv] * 2
                rays += [n] * 2
    uu, vv, rays = np.array(uu), np.array(vv), np.array(rays)
    assert len(uu) == len(o.data.vertices)
    ray = 1 - smooth(0.0, 0.18, np.abs(np.sin(vv * np.pi * (rays - 1))))      # fine rays fanning out, one at each v = k / (rays - 1)
    col = mix(np.broadcast_to(FIN, (len(uu), 3)), FIN_RAY, ray * smooth(0.05, 0.3, uu) * 0.7)
    col = mix(col, ICE, (1 - smooth(0.0, 0.25, uu)) * 0.6)              # its root, the body's ice
    col = mix(col, RIME, smooth(0.8, 0.98, uu) * 0.6)                   # a frosted edge
    paint(o, col, 0.2 + 0.1 * uu, np.zeros(len(uu)))


# ---------- the spines: hoarfrost, hidden under the ice until it puffs ----------
def spine_sites(tree, spacing=0.036, seed=7):
    """Where the spines lie: round its middle (where it puffs fully), clear of its fins; spaced a little apart. Each: surface point, normal, zone."""
    rng = np.random.default_rng(seed)
    pts = []
    tries = 0
    while tries < 6000:
        tries += 1
        y = rng.uniform(-0.12, 0.115)
        a = rng.uniform(0, TAU)
        o = V(0, y, ZC) + V(math.cos(a), 0, math.sin(a)) * 0.4
        hit, nrm, _, _ = tree.ray_cast(o, (V(0, y, ZC) - o).normalized(), 0.5)
        if hit is None:
            continue
        clear = all((hit - q).length > spacing for q, _, _ in pts)
        near_fin = any(min((hit - r[0]).length, (hit - r[1]).length, (hit - r[0].lerp(r[1], 0.5)).length) < 0.035 for _, r, _, _ in fin_list())
        d = spine_axis(nrm)
        ends = (hit - d * SPINE_DEPTH, hit - d * (SPINE_DEPTH + SPINE_L))
        full = all(puff_reach(q.y, q.x, q.z) > 0.99 for q in (hit,) + ends)      # the whole spine, base to tip, where the ice swells all the way          # (only where it swells all the way: a spine where the ice swells less would slide right out of it)
        if clear and not near_fin and full:
            zone = int(round(math.atan2(hit.z - ZC, hit.x) / (TAU / ZONES))) % ZONES
            pts.append((hit, nrm, zone))
    return pts


def spine_axis(nrm):
    return (nrm + V(0, 0.4, 0)).normalized()                  # leaning back a little, as a fish's do


def build_spines(sites, name, coll, sides=5, rings=3):
    """Faceted cones of hoarfrost, wholly under the surface at rest: their tips SPINE_DEPTH inside it."""
    m = Mesh()
    make_tags(m.bm, ints=("zone",))
    for p, nrm, zone in sites:
        d = spine_axis(nrm)
        tip = p - d * SPINE_DEPTH / max(0.3, d.dot(nrm))
        base = tip - d * SPINE_L
        before = set(m.bm.verts)
        m.tube([base.lerp(tip, k / rings) for k in range(rings + 1)], lambda f: 0.0092 * (1 - f) ** 0.9 + 0.0009, sides=sides)
        tag_new(m.bm, before, zone=zone)
    return m.finish(name, coll, smooth_shade=False)


# ---------- painting the ice ----------
def bubbles(P, f, seed):
    """Air caught in the ice: small round bubbles (1 at a bubble's middle), from a scatter of points."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    best = np.full(len(P), 9.0)
    size = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                h = hash01(c[:, 0], c[:, 1], c[:, 2], seed)
                off = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                d = np.linalg.norm(q - c - off, axis=1)
                keep = h > 0.62
                r = 0.08 + 0.16 * hash01(c[:, 0], c[:, 1], c[:, 2], seed + 9)
                nd = np.where(keep, d / r, 9.0)
                take = nd < best
                best = np.where(take, nd, best)
    return best


def cells_flat(P, f, seed=0):
    """Distance to the nearest and second-nearest scatter point (cell units): where the two are near equal, a cell's edge."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                off = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                d = np.linalg.norm(q - c - off, axis=1)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                d1 = np.where(nearer, d, d1)
    return d1, d2, None


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    up = Nn[:, 2]
    # deep blue at its heart, shading paler toward its back and white-blue beneath
    col = mix(np.broadcast_to(ICE, (len(P), 3)), ICE_DEEP, np.clip(smooth(0.2, -0.6, up) * 0.4 + 0.3 * (1 - smooth(0.02, 0.14, np.abs(x))) * smooth(-0.3, 0.3, up) + 0.25 * (fbm(P, 5.0, 3, 9) - 0.5), 0, 1))
    col = mix(col, BELLY, smooth(-0.35, -0.85, up))
    col = mix(col, ICE_PALE, smooth(0.35, 0.85, up) * 0.6)
    # the layers of old glacier ice: thin, uneven, tilted back along it, some fainter than others; deeper blue, never a pattern
    warp = 0.03 * (fbm(P, 9.0, 3, 5) - 0.5) + 0.01 * np.sin(x * 25 + y * 14)
    phase = (z + 0.3 * y + warp) * 70
    band = np.sin(phase)
    strength = smooth(0.3, 0.7, fbm(np.stack([np.floor(phase / np.pi), np.zeros(len(P)), np.zeros(len(P))], 1), 0.37, 2, 8))
    col = mix(col, BAND, smooth(0.72, 0.97, band) * 0.55 * strength * smooth(-0.7, 0.2, up))
    # fractures caught in the ice: a few faint pale planes seen edge-on as fine lines
    cell_a, cell_b, _ = cells_flat(P, 9.0, 13)
    crack = (1 - smooth(0.0, 0.03, cell_b - cell_a)) * smooth(0.64, 0.74, fbm(P, 4.0, 2, 17))     # only here and there: a few planes, never a net
    col = mix(col, ICE_PALE, crack * 0.35)
    # rime: frost settled on top, in a fine speckle
    rime = smooth(0.5, 0.9, up) * smooth(0.45, 0.75, fbm(P, 60.0, 3, 3))
    col = mix(col, RIME, rime * 0.75)
    # air bubbles: a white highlight in each, its edge a little darker
    b = bubbles(P, 55.0, 21)
    col = mix(col, ICE_DEEP * 0.8, (1 - smooth(0.85, 1.0, b)) * smooth(0.55, 0.8, b) * 0.5)
    col = mix(col, RIME, 1 - smooth(0.3, 0.6, b))
    b2 = bubbles(P, 120.0, 41)
    col = mix(col, RIME, (1 - smooth(0.25, 0.5, b2)) * 0.7)
    # the lips' surround a little paler; the eye rims frosted
    for side in (1, -1):
        e = np.array(tuple(mir(EYE_C, side)))
        de = np.linalg.norm(P - e, axis=1)
        col = mix(col, RIME, (1 - smooth(EYE_R * 1.1, EYE_R * 1.5, de)) * 0.55)
    dm = np.linalg.norm((P - np.array(tuple(MOUTH_C))) / np.array((1.0, 1.4, 1.2)), axis=1)
    col = mix(col, ICE_PALE, (1 - smooth(0.03, 0.05, dm)) * 0.5)
    rough = 0.07 + 0.3 * rime
    paint(o, np.clip(col, 0, 1), rough, np.zeros(len(P)))


def paint_lips(o):
    n = len(o.data.vertices)
    paint(o, np.broadcast_to(LIP, (n, 3)).copy(), np.full(n, 0.15), np.zeros(n))


def paint_mouth(o):
    """The dark inside; the beak plates white."""
    P = verts(o)
    plate = np.abs(P[:, 2] - MOUTH_C.z) > MOUTH_RZ * 0.25
    front = P[:, 1] < MOUTH_C.y + 0.006
    col = np.where((plate & front)[:, None], TOOTH, MOUTH_IN)
    paint(o, col, np.where(plate & front, 0.2, 0.5), np.zeros(len(P)))


def paint_spines(o):
    P = verts(o)
    n = len(P)
    col = mix(np.broadcast_to(FROST, (n, 3)), ICE_PALE, 0.25 * (0.5 + 0.5 * np.sin(P[:, 0] * 300 + P[:, 2] * 200)))
    paint(o, col, np.full(n, 0.28), np.zeros(n))


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


# ---------- the whole, high-detail ----------
FIN_RES = (24, 40)


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    FIN_TREE[:] = [data["tree"]]
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
    pieces["Lips"] = build_lips(N + "LipsHi", HI)
    pieces["Mouth"] = build_mouth_inside(N + "MouthHi", HI)
    pieces["Fins"] = build_fins(N + "FinsHi", HI, *FIN_RES)
    data["sites"] = spine_sites(data["tree"])
    pieces["Spines"] = build_spines(data["sites"], N + "SpinesHi", HI, sides=6, rings=6)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 26, 0.009, 14), (20, -18, 0.0042, 10)))}
    if not clay:
        paint_skin(skin)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
        paint_lips(pieces["Lips"])
        paint_mouth(pieces["Mouth"])
        paint_fins(pieces["Fins"], *FIN_RES)
        paint_spines(pieces["Spines"])
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.03, ZC)
FACE_AT = (0, -0.16, ZC + 0.02)
EXTRA = [(0, -1, 0.08, 0.5, FACE_AT), (0.62, -0.75, 0.2, 0.5, FACE_AT), (1, -0.15, 0.1, 0.5, FACE_AT), (0.3, -0.9, 0.2, 0.25, tuple(MOUTH_C)),
         (0.6, -0.7, 0.4, 0.3, tuple(EYE_C)), (0.7, 0.4, 0.3, 0.6, (0.05, 0.12, ZC))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "spines", len(data["sites"]), flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.3)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    if STAGE == "clay":
        pieces["Spines"].hide_render = False
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=1.5, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 2400
LOW_FIN = (4, 6)
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "Lips": 1.6, "Mouth": 1.0, "Fins": 1.0, "Spines": 0.6}


def low_ball(fr, name, seg=20, rings=14):
    """The whole ball, its back too: an eye that turns shows what a cut-away one would hide."""
    m = Mesh()
    q = fr.axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=fr.radius, matrix=Matrix.Translation(fr.centre) @ q)
    return m.finish(name, GAME)


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_ball(fr, N + "Eye" + tag + "Low")
    lows["Lips"] = build_lips(N + "LipsLow", GAME, sides=8, per=10)
    lows["Mouth"] = build_mouth_inside(N + "MouthLow", GAME, seg=12, rings=8)
    lows["Fins"] = build_fins(N + "FinsLow", GAME, *LOW_FIN)
    lows["Spines"] = build_spines(data["sites"], N + "SpinesLow", GAME, sides=5, rings=1)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
BODY_AT, HEAD_AT, TAIL1_AT, TAIL2_AT = V(0, 0.02, ZC), V(0, -0.07, ZC + 0.02), V(0, 0.15, ZC + 0.006), V(0, 0.215, ZC + 0.012)
FIN_BONES = {"PecL": ("FinL", 0), "PecR": ("FinR", 4), "Dorsal": ("Dorsal", 2), "Anal": ("Anal", 6)}     # each fin's bone, and the puff bone it rides on


def puff_at(k):
    return V(0, PUFF_Y, ZC) + zone_dir(k) * 0.1


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", BODY_AT.copy(), "Root"), ("Head", HEAD_AT.copy(), "Body"), ("Jaw", JAW_HINGE.copy(), "Head")]
    for tag, fr in frames.items():
        bones.append(("Eye" + tag, fr.centre.copy(), "Head"))
    bones += [("Tail1", TAIL1_AT.copy(), "Body"), ("Tail2", TAIL2_AT.copy(), "Tail1")]
    for k in range(ZONES):
        bones += [("Puff%d" % (k + 1), puff_at(k), "Body"), ("Spike%d" % (k + 1), puff_at(k), "Puff%d" % (k + 1))]
    for key, root, reach, rays in fin_list():
        if key in FIN_BONES:
            name, zone = FIN_BONES[key]
            bones.append((name, root[0].lerp(root[1], 0.5), "Puff%d" % (zone + 1)))
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def base_weight(y):
    """Along it: the head in front, the body through its middle, the tail stem, the tail fan; each handing over across a span."""
    if y < -0.04:
        return blend({"Head": 1.0}, {"Body": 1.0}, float(smooth(-0.1, -0.04, y)))
    if y < 0.16:
        return blend({"Body": 1.0}, {"Tail1": 1.0}, float(smooth(0.1, 0.16, y)))
    return blend({"Tail1": 1.0}, {"Tail2": 1.0}, float(smooth(0.19, 0.215, y)))


def zone_weight(x, z):
    """The two puff bones either side of a point round its length, shared by how near it lies to each."""
    a = math.atan2(z - ZC, x) % TAU
    s = a / (TAU / ZONES)
    k = int(math.floor(s)) % ZONES
    t = s - math.floor(s)
    return blend({"Puff%d" % (k + 1): 1.0}, {"Puff%d" % ((k + 1) % ZONES + 1): 1.0}, t)


def skin_weights(P):
    out = []
    for x, y, z in P:
        w = base_weight(y)
        r = puff_reach(y, x, z)
        if r > 0:
            w = blend(w, zone_weight(x, z), r)
        out.append(w)
    return out


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    rigid(lows["EyeL"], "EyeL")
    rigid(lows["EyeR"], "EyeR")
    weigh(lows["Lips"], [{"Jaw" if low else "Head": 1.0} for low in read_tag(lows["Lips"], "lower")])
    weigh(lows["Mouth"], [{"Jaw" if low else "Head": 1.0} for low in read_tag(lows["Mouth"], "lower")])
    names = {v: k for k, v in FIN_TAG.items()}
    weigh(lows["Fins"], [{FIN_BONES[names[f]][0] if names[f] in FIN_BONES else "Tail2": 1.0} for f in read_tag(lows["Fins"], "fin")])
    weigh(lows["Spines"], [{"Spike%d" % (z + 1): 1.0} for z in read_tag(lows["Spines"], "zone")])
    weigh(glows["Glints"], [{"Head": 1.0} for _ in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateGlacierPuff uses. +X lifts what points forward; +Y turns to its left; moves in metres
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def puffed(share=1.0):
    """Each puff bone out along its own way by PUFF_T, its spines a further SPIKE_S (in the game's axes: a way out (cos, 0, sin) in Blender is (-cos, sin, 0))."""
    out = {}
    for k in range(ZONES):
        d = zone_dir(k)
        g = (-d.x, d.z, d.y)
        out["Puff%d" % (k + 1)] = (0, 0, 0, tuple(c * PUFF_T * share for c in g))
        out["Spike%d" % (k + 1)] = (0, 0, 0, tuple(c * SPIKE_S * share for c in g))
    return out


POSES = {"Puffed": puffed(1.0), "Half": puffed(0.5), "Gulp": {"Jaw": (-0.35, 0, 0)},
         "Flutter": {"FinL": (0, 0.22, 0), "FinR": (0, -0.22, 0)}, "FlutterBack": {"FinL": (0, -0.5, 0), "FinR": (0, 0.5, 0)},
         "Tail": {"Tail1": (0, 0.28, 0), "Tail2": (0, 0.4, 0)}, "Look": {"EyeL": (0.3, 0.45, 0), "EyeR": (0.3, -0.45, 0)},
         "FinsUp": {"Dorsal": (0, 0, 0.35), "Anal": (0, 0, -0.35)}}


def pose_library():
    return {name: spec(table) for name, table in POSES.items()}


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.3)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.08, 2.0), (None, 1.0)], SCALES, margin=0.008)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.33, 0.6, 0.85, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.006, 0.015),
             reaches={"Fins": (0.003, 0.008), "Spines": (0.002, 0.006), "Lips": (0.003, 0.008), "Mouth": (0.002, 0.006)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    bpy.data.objects.remove(glows["Glints"], do_unlink=True)          # first, so the game's piece takes its exact name
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 26, 0.009, 10), (20, -18, 0.0042, 6)))}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for name in ("Body", "Head", "Puff1", "FinL", "Tail2"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=1.5, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Puffed", "Half", "Gulp", "Flutter", "Look"):
        pose(rig, lib[name])
        view = (0.62, -0.72, 0.28, 1.5, VIEW_AT) if name != "Gulp" else (0.3, -0.95, 0.1, 0.5, FACE_AT)
        shots(os.path.join(REVIEW, "pose" + name), [view, (1, -0.05, 0.1, 1.5, VIEW_AT)], target=VIEW_AT, size=480)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 1.5, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

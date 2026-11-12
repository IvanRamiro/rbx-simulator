"""The Ninefold Spirit Serpent (Legendary, Spiritual energy; Ancient Grove Egg): "Nine coils, one for each meridian. Cultivators meditate beside it to
feel their own Qi move."

The idea: Qi you can see moving. A slender pearl-white serpent, loosely coiled on the ground, its front rising in a tall, unhurried S like a swan's
neck; nine rings of jade light ride its body, one at each turn of it, one for each meridian, and in the game the light climbs from ring to ring,
tail to crown, as Qi climbs a cultivator's channels. Its head is serene, not a hunter's: a rounded snout, calm half-lidded eyes of jade, a small jade
gem on its brow (where the light arrives); a fan of thin jade fins spreads behind its head like a halo. Its scales are pearl, a jade line runs down
its spine, its belly is warm ivory. No hood, no fangs, no antlers: it is not the Frostfang's cobra nor the Origin Serpent's dragon.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/ninefold_serpent.py -- [clay|paint|rig|all] [review dir]

Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Its coil rests on the ground (z = 0). The maps go to assets/pets/AncientGroveEgg/.

What touches what: the skin (tail tip to snout, the coil resting on the ground) is one piece; the fins grow out of the back of its head; the eyes sit
in their sockets under lids; the nine rings float a little off the body (glow); the brow gem lies on the brow (glow).
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "NinefoldSpiritSerpent"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AncientGroveEgg")

# ---------- colours: pearl, jade, ivory, and the jade light ----------
PEARL, PEARL_SHADE = rgb(236, 238, 240), rgb(196, 206, 214)
JADE, JADE_DEEP = rgb(70, 196, 150), rgb(24, 110, 86)
IVORY = rgb(242, 228, 196)
RING_HEX, GEM_HEX = "35f5b8", "35f5b8"       # saturated: Neon blooms a paler mint to white

# ---------- the frame of it ----------
COIL_C = V(0, 0.09, 0)               # the middle of its coil, on the ground
R_OUT, R_IN = 0.3, 0.16              # the spiral's radius at the tail tip and where it rises
TURNS = 1.35
COLUMN = [V(0.1, -0.08, 0.1), V(0.085, -0.13, 0.24), V(0.02, -0.12, 0.38), V(-0.025, -0.06, 0.5), V(-0.01, -0.02, 0.61), V(0.0, -0.05, 0.71),
          V(0.0, -0.11, 0.77), V(0.0, -0.165, 0.79)]      # from the coil up its front in a slow S (back, then forward like a swan's neck) to its nape
RADIUS = ((0, 0.012), (0.08, 0.022), (0.3, 0.04), (0.58, 0.05), (0.72, 0.046), (0.86, 0.036), (0.95, 0.033), (1.0, 0.034))   # tail tip (0) to nape (1)
RINGS = 9
RING_F = (0.56, 0.95)                # the first and last ring, along it: up the rising body, a ladder of light toward its head (spread over the coil, they crowded into clutter)
CRANIUM = (V(0, -0.196, 0.802), (0.057, 0.058, 0.03))
SNOUT = [V(0, -0.22, 0.8), V(0, -0.252, 0.796), V(0, -0.278, 0.79)]
SNOUT_W = ((0, 0.04), (0.6, 0.031), (1, 0.021))
SNOUT_H = ((0, 0.025), (1, 0.016))
EYE_R = 0.0138
EYE_C = V(0.038, -0.228, 0.81)
EYE_AXIS = V(0.62, -0.72, 0.3).normalized()
LID_UP, LID_LOW = (30.0, 120.0, 0.0018), (-24.0, -126.0, 0.0016)      # calm and a little lowered: at 14 it read asleep and sullen
LID_TILT = 0.0
GEM_C = V(0, -0.234, 0.834)          # on its brow, between and above the eyes
FINS = 5                             # the fan behind its head
FIN_ROOT = V(0, -0.17, 0.808)


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def arc_lengths(path):
    a = np.array([tuple(p) for p in path])
    return np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])


def resample(path, n):
    s = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    out = []
    for t in np.linspace(0, s[-1], n + 1):
        i = min(int(np.searchsorted(s, t, side="right")) - 1, len(a) - 2)
        f = (t - s[i]) / max(s[i + 1] - s[i], 1e-9)
        out.append(V(*(a[i] * (1 - f) + a[i + 1] * f)))
    return out


def centreline(per=6):
    """Its spine from tail tip to nape, evenly spaced: the spiral on the ground (each point lifted by its own radius), then up its front."""
    n = 72
    phi_end = -math.pi / 2
    flat = []
    for k in range(n + 1):
        t = k / n
        phi = phi_end - TURNS * TAU * (1 - t)
        r = R_OUT + (R_IN - R_OUT) * t
        flat.append(COIL_C + V(r * math.cos(phi), r * math.sin(phi), 0))
    total = arc_lengths(flat)[-1] + arc_lengths(catmull([flat[-1]] + COLUMN, per))[-1]
    s_flat = arc_lengths(flat)
    pts = [V(p.x, p.y, prof(RADIUS, s_flat[k] / total)) for k, p in enumerate(flat)]
    path = catmull(pts + COLUMN, per)
    spiral = n * per
    f = arc_lengths(path)
    f = f / f[-1]
    path = [V(p.x, p.y, prof(RADIUS, f[i])) if i <= spiral else p for i, p in enumerate(path)]
    return resample(path, 400)


SPINE = centreline()
SPINE_S = arc_lengths(SPINE)
SPINE_F = SPINE_S / SPINE_S[-1]


def radius_at(f):
    return prof(RADIUS, f)


def spine_at(f):
    k = f * (len(SPINE) - 1)
    i = min(int(k), len(SPINE) - 2)
    return SPINE[i].lerp(SPINE[i + 1], k - i)


def tangent_at(f):
    return (spine_at(min(1.0, f + 0.004)) - spine_at(max(0.0, f - 0.004))).normalized()


def rm_frames(path, first_side=None):
    """Frames along a path that never twist."""
    out = []
    tan = (path[1] - path[0]).normalized()
    side = first_side or (V(1, 0, 0) - tan * tan.x)
    if side.length < 1e-4:
        side = tan.orthogonal()
    side = (side - tan * side.dot(tan)).normalized()
    for i in range(len(path)):
        t2 = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = tan.rotation_difference(t2) @ side if i else side
        side = (side - t2 * side.dot(t2)).normalized()
        tan = t2
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def tube_loft(m, path, r_fn, flat_fn=None, nt=40, frames=None):
    fr = frames or rm_frames(path)
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


# ---------- the skin ----------
def build_skin():
    m = Mesh()
    body = SPINE[::2]
    fb = SPINE_F[::2]
    tube_loft(m, body, lambda f: radius_at(float(np.interp(f, np.linspace(0, 1, len(fb)), fb))), nt=36, frames=rm_frames(body, V(0, 0, 1)))
    m.ball(SPINE[0], (radius_at(0.0),) * 3, 20, 12)
    # the head: a rounded cranium, a soft snout, a blunt rounded nose, full cheeks under the eyes
    m.ball(CRANIUM[0], CRANIUM[1], 40, 24)
    tube_loft(m, catmull(SNOUT, 8), lambda f: prof(SNOUT_H, f), lambda f: prof(SNOUT_W, f) / prof(SNOUT_H, f), nt=32,
              frames=rm_frames(catmull(SNOUT, 8), V(1, 0, 0)))
    m.ball(SNOUT[-1] + V(0, 0.003, 0.0), (0.0215, 0.016, 0.0155), 28, 16)
    for side in (1, -1):
        m.ball(V(side * 0.035, -0.222, 0.797), (0.017, 0.026, 0.015), 24, 14)    # the cheek under each eye (fuller, it read as a duck's)
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.04,) * 3, 24, 16)     # the socket (fuller and further out, the eyes bulged like a frog's)
    m.ball(V(0, -0.215, 0.826), (0.028, 0.034, 0.01), 28, 14)                      # the brow, where the gem sits
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 6})])
    P = verts(o)
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(o, P)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def fin_frame(k):
    """Fin k (0 at its left cheek, FINS - 1 at its right): its angle round the head, the way it points, its length and width."""
    a = math.radians(-84 + 168 * k / (FINS - 1))               # fanned round behind the head, from beside its left cheek over the top to its right: a halo
    out = V(math.sin(a), 0.3, math.cos(a)).normalized()        # out round it, a little back (more back, they bunched into a crest)
    length = 0.1 + 0.035 * math.cos(a) ** 2                    # the middle ones longest
    return a, out, length, 0.03


def build_fins(name=N + "FinsHi", coll=HI, nu=24, nv=8, recalc=True):
    """The halo: thin jade fins fanned out behind its head, each a long leaf swept back and up, ribbed, its edge scalloped a little."""
    m = Mesh()
    for k in range(FINS):
        a, out, length, width = fin_frame(k)

        def point(u, v, out=out, length=length, width=width, a=a):
            across = V(math.cos(a), 0, -math.sin(a))           # across the fin
            p = FIN_ROOT + out * (length * u) + across * (width * (v - 0.5) * 2 * math.sin(math.pi * (0.08 + 0.84 * u)))     # a rounded tip (to nothing, it drew a needle)
            return p + V(0, 0.02 * u * u, 0.015 * u * u)        # curling back at the tip

        m.sheet(point, lambda u, v: 0.004 * (1 - 0.6 * u), nu, nv)
    o = m.finish(name, coll, recalc=recalc)
    return o


def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT) for side, tag in ((1, "L"), (-1, "R"))}


def ring_frame(k):
    """Ring k (0 the lowest): its centre on the spine, the two directions across the body there, and its radius."""
    f = RING_F[0] + (RING_F[1] - RING_F[0]) * k / (RINGS - 1)
    c, t = spine_at(f), tangent_at(f)
    side = (V(0, 0, 1).cross(t)).normalized() if abs(t.z) < 0.95 else V(1, 0, 0)
    up = t.cross(side).normalized()
    return c, side, up, radius_at(f) + 0.016


def ring_mesh(m, k, seg=40, sides=8, bead=(12, 8), clear=None):
    """clear(point, distance): the point moved out of the skin to that distance off it (the game rings); None leaves it (the high ones)."""
    c, side, up, r = ring_frame(k)
    pts = [c + (side * math.cos(TAU * i / seg) + up * math.sin(TAU * i / seg)) * r for i in range(seg + 1)]
    if clear:
        pts = [clear(p, RING_CLEAR[0]) for p in pts]
    m.tube(pts, lambda u: 0.0042, sides=sides, caps=False)
    for b in range(4):
        q = c + (side * math.cos(TAU * b / 4 + 0.4) + up * math.sin(TAU * b / 4 + 0.4)) * r
        m.ball(clear(q, RING_CLEAR[1]) if clear else q, (0.0075,) * 3, *bead)


def build_rings(name):
    """The nine meridian rings: a thin band of light round its body at each turn, a little off it, each with four small beads (the acupoints)."""
    m = Mesh()
    for k in range(RINGS):
        ring_mesh(m, k)
    return m.finish(name, HI)


def build_gem(name):
    m = Mesh()
    m.ball(GEM_C, (0.011, 0.013, 0.0055), 16, 10)
    return m.finish(name, HI)


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


COIL_END = int(np.argmin([(p - V(0, COIL_C.y - R_IN, prof(RADIUS, 0.6))).length for p in SPINE]))
F_RISE = float(SPINE_F[COIL_END])
RING_FS = [RING_F[0] + (RING_F[1] - RING_F[0]) * k / (RINGS - 1) for k in range(RINGS)]


def body_coords(P):
    """Per point: metres along its spine, distance off it, where round it (up +1 its back, -1 its belly; side), and f 0..1."""
    A = np.array([tuple(p) for p in SPINE])
    f, d = nearest_on(SPINE, P)
    k = f * (len(A) - 1)
    i = np.clip(k.astype(int), 0, len(A) - 2)
    t = k - i
    Q = A[i] * (1 - t)[:, None] + A[i + 1] * t[:, None]
    tan = A[i + 1] - A[i]
    tan /= np.linalg.norm(tan, axis=1)[:, None]
    rise = smooth(F_RISE, F_RISE + 0.06, f)[:, None]
    back = np.array([0, 0, 1.0]) * (1 - rise) + np.array([0, 1.0, 0]) * rise      # up on the coil; behind it on its risen front
    back = back - tan * (back * tan).sum(1)[:, None]
    back /= np.linalg.norm(back, axis=1)[:, None] + 1e-9
    side = np.cross(tan, back)
    rel = P - Q
    rel /= np.linalg.norm(rel, axis=1)[:, None] + 1e-9
    return f * SPINE_S[-1], d, (rel * back).sum(1), (rel * side).sum(1), f


def skin_fields(P, Nn):
    s, d, up, lat, f = body_coords(P)
    head = (P[:, 1] < -0.15) & (P[:, 2] > 0.74) | (f > 0.99)
    belly = smooth(-0.35, -0.7, up) * (~head)
    dorsal = (1 - smooth(0.0, 0.16, np.abs(lat) + 0.6 * (1 - up))) * smooth(0.0, 0.5, up) * (~head)      # a jade line down its spine
    # round each ring, the scales lit pale jade: the meridian point showing through
    near = np.zeros(len(P))
    for rf in RING_FS:
        near = np.maximum(near, 1 - smooth(0.012, 0.05, np.abs(s - rf * SPINE_S[-1])))
    d1, d2, own = cells_3d(P, 190.0, 5)
    scale = smooth(0.0, 0.14, d2 - d1)
    scute = 0.5 + 0.5 * np.cos(s * TAU / 0.02)
    # the head: a jade sweep back from each eye, the mouth line, the nostrils
    sweep = np.zeros(len(P))
    for side in (1, -1):
        e = np.array(tuple(mir(EYE_C, side)))
        back_of = smooth(0.0, 0.05, P[:, 1] - e[1])
        sweep = np.maximum(sweep, (1 - smooth(0.004, 0.012, np.abs(P[:, 2] - e[2] + 0.004 + 0.12 * (P[:, 1] - e[1])))) * back_of
                           * (1 - smooth(0.04, 0.07, P[:, 1] - e[1])) * (np.abs(P[:, 0]) > 0.03) * head)
    mouth_z = 0.785 + 0.12 * np.maximum(0, P[:, 1] + 0.27)
    mouth = (1 - smooth(0.0012, 0.0032, np.abs(P[:, 2] - mouth_z))) * smooth(-0.2, -0.215, P[:, 1]) * smooth(0.004, 0.012, np.abs(P[:, 0])) * head
    # (a hard-edged 1.8 mm band stitched across the painted vertices: a soft one draws a clean line)
    nostril = np.zeros(len(P))
    for side in (1, -1):
        nostril = np.maximum(nostril, 1 - smooth(0.0025, 0.0045, np.linalg.norm(P - np.array(tuple(SNOUT[-1] + V(side * 0.01, 0.0, 0.012))), axis=1)))
    return dict(belly=belly, dorsal=dorsal, near=near, scale=scale, own=own, scute=scute, sweep=sweep, mouth=mouth, nostril=nostril,
                head=head.astype(float), up=up)


def carve_skin(o):
    P, Nn = verts(o), normals(o)
    F = skin_fields(P, Nn)
    d = 0.0005 * F["scale"] * (1 - F["head"]) - 0.0009 * F["belly"] * smooth(0.85, 1.0, F["scute"]) - 0.0025 * F["nostril"] - 0.0008 * F["mouth"]
    set_verts(o, P + Nn * d[:, None])


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    n = len(P)
    F = skin_fields(P, Nn)
    col = mix(np.broadcast_to(PEARL, (n, 3)), PEARL_SHADE, (1 - F["scale"]) * 0.45 * (1 - F["head"]))      # pearl scales, their edges a cool grey
    col = mix(col, PEARL * 1.03, (F["own"] > 0.8) * F["scale"] * 0.4)                                    # a few catching the light
    col = mix(col, rgb(214, 236, 230), smooth(0.2, 0.9, F["up"]) * 0.25)                                 # a faint jade cast along its back
    col = mix(col, JADE, F["dorsal"] * 0.85)
    col = mix(col, rgb(150, 232, 200), F["near"] * F["scale"] * 0.55 * (1 - F["belly"]))                 # the meridian points' pale jade glow
    col = mix(col, IVORY, F["belly"] * 0.9)
    col = mix(col, rgb(214, 196, 160), F["belly"] * smooth(0.82, 1.0, F["scute"]) * 0.6)
    col = mix(col, JADE, F["sweep"] * 0.9)
    col = mix(col, rgb(132, 112, 116), F["mouth"] * 0.75)
    col = mix(col, rgb(70, 80, 84), F["nostril"])
    rough = 0.34 - 0.12 * F["scale"] * (1 - F["belly"]) + 0.1 * F["belly"]
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_fins(o):
    P = verts(o)
    n = len(P)
    rel = P - np.array(tuple(FIN_ROOT))
    t = np.clip(np.linalg.norm(rel, axis=1) / 0.13, 0, 1)                   # root (0) to tip (1)
    col = mix(np.broadcast_to(JADE_DEEP, (n, 3)), rgb(150, 236, 205), smooth(0.05, 0.85, t))
    ang = np.arctan2(rel[:, 0], rel[:, 2])
    rib = 1 - smooth(0.02, 0.07, np.abs(np.sin(ang * 26)))                     # fine ribs fanning out
    col = mix(col, rgb(220, 255, 240), rib * 0.35 * smooth(0.15, 0.6, t))
    col = mix(col, rgb(236, 255, 248), smooth(0.85, 1.0, t) * 0.6)            # pale tips
    paint(o, np.clip(col, 0, 1), np.full(n, 0.28), np.zeros(n))


def eye_paint(o, fr):
    """Calm jade eyes: a pale jade iris deepening at its rim, a round dark pupil, a fine gold fleck ring: wise, not a hunter's slit."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(170, 245, 214), rgb(52, 176, 132), smooth(0.15, 0.55, r))
    col = mix(col, rgb(18, 70, 56), smooth(0.55, 0.7, r))
    col = mix(col, rgb(236, 210, 130), (1 - smooth(0.0, 0.03, np.abs(r - 0.36))) * 0.5)
    azi = np.arctan2(py, px)
    col = col * (0.9 + 0.1 * np.sin(azi * 28 + np.sin(azi * 4) * 2))[:, None]
    col = mix(col, rgb(8, 18, 16), 1 - smooth(0.24, 0.29, r))
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.04), np.zeros(len(px)))


def paint_all(pieces, frames, data):
    carve_skin(pieces["Skin"])
    paint_skin(pieces["Skin"])
    paint_fins(pieces["Fins"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_skin()
    pieces["Fins"] = build_fins()
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, PEARL, rgb(60, 110, 96), line_w=3.5)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, PEARL, rgb(90, 130, 118), lower_share=0.5, line_w=3.0)
    glows = {"Rings": build_rings(N + "Rings_Glow_" + RING_HEX), "Gem": build_gem(N + "Gem_Glow_" + GEM_HEX)}
    if not clay:
        paint_all(pieces, frames, data)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.2), (-0.6, 0.6, 0.4), (0, -0.05, 1)]
VIEW_AT = (0, 0.02, 0.42)
FACE_AT = (0, -0.23, 0.81)
EXTRA = [(0, -1, 0.1, 0.45, FACE_AT), (0.7, -0.6, 0.2, 0.45, FACE_AT), (1, 0, 0.15, 0.5, FACE_AT)]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "spine len", round(float(SPINE_S[-1]), 3), flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.66, 0.64, 0.6, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.04, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
from mathutils.bvhtree import BVHTree  # noqa: E402

SKIN_QUADS = 5200
SKIN_SEEDS = (7, 5, 13, 3)           # QuadriFlow's seeds tried: the one whose skin keeps closest to the high one is kept (seed 3 left a 1.5 cm fold where
                                     # the column lies on the outer coil)
PIECES = ("Skin", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "Fins")
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 3.0, "LidUR": 3.0, "LidLL": 2.0, "LidLR": 2.0, "Fins": 1.4}
FIN_LOW = (10, 2)                    # a fin's grid along and across it in the game mesh
RING_LOW = (24, 5, (6, 4))           # a ring's segments round, its band's sides, its beads' grid
RING_FLOOR = 0.0015                  # the three rings on the coil pass under it: their lowest stretch is laid flat just over the ground, under the coil
RING_CLEAR = (0.0062, 0.0095)        # the band's and a bead's middle at least this far off the skin: where the body bends (the fourth, where it rises off
                                     # its coil) a ring otherwise cut into it
BLINK_U, BLINK_L = 38.0, 18.0        # degrees each lid turns to close (the two add past the 54 between its lids' edges)


def is_head(c):
    """Its head: it gets more of the atlas."""
    return c.y < -0.13 and c.z > 0.72


def best_retopo(hi, tree):
    best = None
    for seed in SKIN_SEEDS:
        o = retopo_skin(hi, N + "SkinLow", SKIN_QUADS, seed=seed)
        gap = surface_gap(o, tree)
        print("SKIN seed", seed, "gap", round(gap, 4), flush=True)
        if best is None or gap < best[0]:
            if best:
                bpy.data.objects.remove(best[1], do_unlink=True)
            best = (gap, o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    best[1].name = N + "SkinLow"
    return best[1]


def build_low(pieces, frames, data):
    data["tree"] = tree_of(pieces["Skin"])
    lows = {"Skin": best_retopo(pieces["Skin"], data["tree"])}
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
        P[band] = c + (P[band] - c) / d[band, None] * (EYE_R - 0.002)        # level with an eyeball, the socket's skin z-fights it
    set_verts(lows["Skin"], P)
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 20, 12)
        lows["LidU" + tag] = low_lid(fr, True, N + "LidU" + tag + "Low", lift=0.002)
        lows["LidL" + tag] = low_lid(fr, False, N + "LidL" + tag + "Low", lift=0.002)
    lows["Fins"] = build_fins(N + "FinsLow", GAME, *FIN_LOW, recalc=False)      # (a sheet is wound outward as it is made)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    sharpen(lows["Fins"])
    triangulate(lows)
    return lows


def sharpen(o, angle=60):
    """A fin's thin rim kept apart from its faces: shaded smooth across the turn, each short stretch of the rim drew a dark tooth (seen baked)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(angle):
            e.smooth = False
    bm.to_mesh(o.data)
    bm.free()


def game_glows(tree):
    """The nine rings, each its own piece (the game lights them one at a time, ring 1 the lowest), and the brow gem."""
    def clear(p, dist):
        if p.z < 0.012:              # (the stretch under the coil: laid on the ground below)
            return p
        for _ in range(8):           # pushed off the nearest surface, again and again: in a crotch it settles between the two
            loc, nrm, _, d = tree.find_nearest(p)
            if loc is None:
                break
            off = (p - loc).dot(nrm)
            if off >= dist - 1e-5:
                break
            p = p + nrm * (dist - off)
        return p
    out = {}
    seg, sides, bead = RING_LOW
    for k in range(RINGS):
        m = Mesh()
        ring_mesh(m, k, seg, sides, bead, clear)
        bmesh.ops.remove_doubles(m.bm, verts=m.bm.verts, dist=1e-6)        # the band's closing seam welded
        o = m.finish(N + "Ring%d_Glow_%s" % (k + 1, RING_HEX), GAME)
        P = verts(o)
        P[:, 2] = np.maximum(P[:, 2], RING_FLOOR)
        set_verts(o, P)
        out["Ring%d" % (k + 1)] = o
    m = Mesh()
    m.ball(GEM_C, (0.011, 0.013, 0.0055), 12, 7)
    out["Gem"] = m.finish(N + "Gem_Glow_" + GEM_HEX, GAME)
    return out


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


UV_ANGLE = {"Skin": 66, "Fins": 50}


def serpent_unwrap(lows, margin=0.0045):
    """Each piece on its own: the projection's charts as seams (and one round its neck, where the head's share changes), an angle-based unwrap that
    can't fold a chart over itself, collapsed fragments projected again, each scaled to its share; all packed together (frostfang_serpent.py's)."""
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
            scale_uv_to(o, [p for p in polys if is_head(p.center)], 2.2)
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


def flat_normals_under(o, img, grow=2):
    """Sets a baked normal map flat (no relief) under one piece's UV islands, a few texels past their edges. The fins are smooth leaves: baked,
    their thin rims bent the normals near each edge into a row of dark teeth (the colour alone baked clean)."""
    w, h = img.size
    mask = np.zeros((h, w), dtype=bool)
    uv = o.data.uv_layers.active.data
    for p in o.data.polygons:
        loops = list(p.loop_indices)
        a = np.array(uv[loops[0]].uv) * (w, h)
        for i in range(1, len(loops) - 1):
            b, c = np.array(uv[loops[i]].uv) * (w, h), np.array(uv[loops[i + 1]].uv) * (w, h)
            lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - 1, 0, (w - 1, h - 1))
            hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1, 0, (w - 1, h - 1))
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
            qx, qy = xs + 0.5, ys + 0.5
            w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
            w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
            inside = (w0 >= -0.02) & (w1 >= -0.02) & (w0 + w1 <= 1.02)
            mask[ys[inside], xs[inside]] = True
    for _ in range(grow):
        mask = mask | np.roll(mask, 1, 0) | np.roll(mask, -1, 0) | np.roll(mask, 1, 1) | np.roll(mask, -1, 1)
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    px[mask] = (0.5, 0.5, 1.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.save()
    img.pack()
    return int(mask.sum())


# ---------- the skeleton: a spine, from where it rises, forward up its front and back along its coil; the fins, the eyes and their lids ----------
UP_N, COIL_N = 8, 12
LAST = len(SPINE) - 1
UP_AT = [COIL_END + round(k * (LAST - COIL_END) / UP_N) for k in range(UP_N)]       # Up1 where it rises (the base carries the coil's last stretch)
COIL_AT = [COIL_END - round(k * COIL_END / (COIL_N + 1)) for k in range(1, COIL_N + 1)]
CHAIN = [("Coil%d" % k, COIL_AT[k - 1]) for k in range(COIL_N, 0, -1)] + [("Base", COIL_END)] + [("Up%d" % k, UP_AT[k - 1]) for k in range(1, UP_N + 1)] + [("Head", LAST)]
CHAIN_NAMES = [n for n, _ in CHAIN]
FIN_NAMES = ["Fin%d" % (k + 1) for k in range(FINS)]       # Fin1 by its left cheek, Fin5 by its right


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Base", SPINE[COIL_END].copy(), "Root")]
    parent = "Base"
    for k in range(1, UP_N + 1):
        bones.append(("Up%d" % k, SPINE[UP_AT[k - 1]].copy(), parent))
        parent = "Up%d" % k
    bones.append(("Head", SPINE[LAST].copy(), parent))
    for name in FIN_NAMES:
        bones.append((name, FIN_ROOT.copy(), "Head"))
    for tag, fr in frames.items():
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    parent = "Base"
    for k in range(1, COIL_N + 1):
        bones.append(("Coil%d" % k, SPINE[COIL_AT[k - 1]].copy(), parent))
        parent = "Coil%d" % k
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


HEAD_FROM = (-0.135, -0.165)         # y: where the neck hands over to the head (its nape, the Head bone, at -0.165)


def body_weights(P):
    mids = chain_mids()
    f, _ = nearest_on(SPINE, P)
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        w = chain_weight(CHAIN_NAMES, mids, float(f[i]))
        if y < HEAD_FROM[0] and z > 0.735 and abs(x) < 0.075:
            w = blend(w, {"Head": 1.0}, float(smooth(HEAD_FROM[0], HEAD_FROM[1], y)))
        out.append(w)
    return out


def fin_weights(o):
    per = (FIN_LOW[0] + 1) * (FIN_LOW[1] + 1) * 2
    return [{FIN_NAMES[min(i // per, FINS - 1)]: 1.0} for i in range(len(o.data.vertices))]


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in "LR":
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    weigh(lows["Fins"], fin_weights(lows["Fins"]))
    for k in range(RINGS):
        o = glows["Ring%d" % (k + 1)]
        weigh(o, body_weights(verts(o)))        # each ring weighted as the skin under it is: it rides the body where it sits
    rigid(glows["Gem"], "Head")
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# ---------- poses: the spine fitted to a curve, written as PetRig's tables (turns in the game's axes; frostfang_serpent.py's method) ----------
CM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))


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
    i = CHAIN_NAMES.index(name)
    if name.startswith("Coil") or name == "Base":
        end = CHAIN[i - 1][1] if i > 0 else 0
    elif name == "Head":
        return points[at], None
    else:
        end = CHAIN[i + 1][1]
    return points[at], points[end]


def transported_backs(points):
    """Its back's direction at every point of a spine, carried from the tail tip along it by the least turn at each step: never twisting."""
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
        W[name] = frame_rot(e0 - h0, REST_BACKS[at], e1 - h1, tb[at])
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
        table[b] = tuple(round(float(x), 4) for x in v)
    return table


def along(path, s):
    L = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    s = float(np.clip(s, 0, L[-1]))
    i = min(int(np.searchsorted(L, s, side="right")) - 1, len(a) - 2)
    f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
    return V(*(a[i] * (1 - f) + a[i + 1] * f))


def column_curve(ctrl):
    """Its risen front along a curve that leaves the coil as it does at rest (its first stretch kept) and goes on through ctrl, the rest of it
    stretched or shrunk to its length; the coil as it rests."""
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


def fin_axes():
    """Per fin, in the game's axes: the line it fans out on (a positive turn takes it further from the middle of the fan) and the line it lifts
    on (a positive turn raises it up and forward, out of its swept-back rest; negative folds it back along the neck)."""
    out = []
    for k in range(FINS):
        a, fout, length, width = fin_frame(k)
        fan = V(0, 1, 0) if a >= 0 else V(0, -1, 0)            # a turn about +Y increases a (out toward its right cheek)
        if abs(a) < 1e-6:
            fan = V(0, 0, 0)
        lift = fout.cross(V(0, 1, 0)).normalized()          # a turn about this takes its tip away from the back (+Y)
        tip = Matrix.Rotation(0.2, 3, lift) @ fout
        if tip.y > fout.y:
            lift = -lift
        out.append((game_vec(fan), game_vec(lift), abs(a) / math.radians(84)))
    return out


def fins_turn(spread, lift):
    """Every fin's turn: fanned wider by spread (radians at the outermost; the middle one does not fan) and lifted by lift."""
    out = {}
    for name, (fan, lf, share) in zip(FIN_NAMES, fin_axes()):
        R = Matrix.Rotation(lift, 3, blender_vec(lf))
        if share > 0:
            R = Matrix.Rotation(spread * share, 3, blender_vec(fan)) @ R
        out[name] = to_game(R)
    return out


RIPPLE = 0.015                       # radians: each coil bone's sway as a ripple runs round its coil while it glides (its turns and its rings lie close:
RIPPLE_TAIL = 0.04                   # at 0.025 they swayed into each other); rising to this at its tail's tip, which has room
RIPPLE_STEP = 0.9


def ripple_amp(k, base=RIPPLE, tail=RIPPLE_TAIL):
    return base + (tail - base) * float(smooth(COIL_N - 3.5, COIL_N, k))


def ripple(phase, base=RIPPLE, tail=RIPPLE_TAIL):
    """A ripple running back round its coil: each coil bone swayed in turn about the upright (the coil stays flat on the ground). Each bone's own
    turn is the difference from the one before, so each lies at most its amplitude off its rest."""
    world = [0.0] + [ripple_amp(k, base, tail) * math.sin(phase - RIPPLE_STEP * k) for k in range(1, COIL_N + 1)]
    return {"Coil%d" % k: (0, world[k] - world[k - 1], 0) for k in range(1, COIL_N + 1)}


def pose_tables():
    t = {}
    # gliding: it never uncoils; it leans its column forward like a swan's neck, head level, fins folded back, and slides on its coil while a ripple
    # runs round it
    W, move = fit_spine(column_curve([V(0.04, -0.2, 0.36), V(0.0, -0.27, 0.49), V(0, -0.35, 0.56), V(0, -0.42, 0.57)]), V(0, -1, -0.05))
    t["Glide"] = table_of(locals_from_world(W), move, fins_turn(-0.06, -0.05))
    for k in range(4):
        t["Glide%d" % k] = dict(t["Glide"], **{n: tuple(round(x, 4) for x in v) for n, v in ripple(TAU * k / 4).items()})
    t["Hover"] = table_of({}, None, fins_turn(0.08, 0.05))
    # rising: it draws itself up tall and straight, head lifted, its fins spread wide and raised: its meditation, and its special
    W, move = fit_spine(column_curve([V(0.04, -0.11, 0.38), V(0.0, -0.07, 0.55), V(0, -0.07, 0.71), V(0, -0.1, 0.84), V(0, -0.15, 0.9)]), V(0, -1, 0.3))
    t["Rise"] = table_of(locals_from_world(W), move, fins_turn(0.3, 0.3))
    t["Look"] = {"Up6": (0, 0.2, 0), "Up7": (0, 0.25, 0), "Up8": (0, 0.25, 0), "Head": (0.0, 0.3, 0.06)}
    t["Bow"] = {"Up7": (-0.08, 0, 0), "Up8": (-0.14, 0, 0), "Head": (-0.28, 0, 0), **{k: tuple(round(x, 4) for x in v) for k, v in fins_turn(0.0, 0.1).items()}}
    t["FinsOpen"] = {k: tuple(round(x, 4) for x in v) for k, v in fins_turn(0.3, 0.3).items()}
    t["FinsFold"] = {k: tuple(round(x, 4) for x in v) for k, v in fins_turn(-0.06, -0.05).items()}      # (folded further, they lay into its neck)
    return t


def spec(table):
    out = {}
    for bone, v in table.items():
        q = from_game(v).to_quaternion()
        axis, angle = q.to_axis_angle()
        mv = blender_vec(v[3]) if len(v) > 3 else V(0, 0, 0)
        out[bone] = (tuple(axis), math.degrees(angle), tuple(mv))
    return out


def lids_spec(frames, up, low):
    out = {}
    for tag, fr in frames.items():
        out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
        out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
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
    """Per pose: skin against itself (faces three or more spine bones apart), each ring against the skin, the fins against its neck and column,
    and how low the skin, the rings and the fins go."""

    def __init__(self, body, glows):
        self.body, self.glows = body, glows
        self.dom = dominant(body)
        fp = np.zeros(len(body.data.polygons), dtype=int)
        body.data.attributes["piece"].data.foreach_get("value", fp)
        _, tris = posed(body)
        self.tris = tris
        d = self.dom
        skin = [i for i, p in enumerate(fp) if p == PIECES.index("Skin")]
        rank = {n: k for k, n in enumerate(CHAIN_NAMES)}
        self.by_rank = {}
        for i in skin:
            r = rank.get(d[tris[i][0]])
            if r is not None:
                self.by_rank.setdefault(r, []).append(i)
        self.skin = skin
        self.fins = [i for i, p in enumerate(fp) if p == PIECES.index("Fins")]
        self.not_head = [i for i in skin if d[tris[i][0]] != "Head"]
        self.skin_v = np.zeros(len(body.data.vertices), dtype=bool)
        for i in skin:
            for v in tris[i]:
                self.skin_v[v] = True
        self.ring_faces = {}
        for k in range(RINGS):
            o = glows["Ring%d" % (k + 1)]
            z = verts(o)[:, 2]
            self.ring_faces[k] = [p.index for p in o.data.polygons if min(z[v] for v in p.vertices) > 0.012]      # (not the stretch laid under the coil)
        self.fin_v = np.zeros(len(body.data.vertices), dtype=bool)
        for i in self.fins:
            for v in tris[i]:
                self.fin_v[v] = True

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
        ring_hits, ring_low = 0, 9.0
        for k in range(RINGS):
            rco, rtris = posed(self.glows["Ring%d" % (k + 1)])
            n = pairs(rco, rtris, self.ring_faces[k], co, tris, self.skin)
            if n:
                self.which["Ring%d" % (k + 1)] = n
            ring_hits += n
            ring_low = min(ring_low, float(rco[:, 2].min()))
        out["rings x skin"] = ring_hits
        out["fins x neck"] = pairs(co, tris, self.fins, co, tris, self.not_head)
        out["skin z"] = round(float(co[self.skin_v, 2].min()), 4)
        out["ring z"] = round(ring_low, 4)
        out["fin z"] = round(float(co[self.fin_v, 2].min()), 4)
        return out


TRANSITIONS = [("Rest", "Glide"), ("Glide0", "Glide1"), ("Glide1", "Glide2"), ("Glide2", "Glide3"), ("Glide3", "Glide0"), ("Rest", "Hover"),
               ("Glide", "Hover"), ("Rest", "Rise"), ("Glide", "Rise"), ("Hover", "Rise"), ("Rise", "Look"), ("Rest", "Look"), ("Rest", "Bow"),
               ("Look", "Bow"), ("FinsFold", "FinsOpen"), ("Glide", "Look")]
MINS = ("skin z", "ring z", "fin z")


def check_transitions(rig, chk, tables):
    tables = dict(tables, Rest={})
    for na, nb in TRANSITIONS:
        worst = {}
        for k in range(11):
            pose(rig, spec(slerp_tables(tables[na], tables[nb], k / 10)))
            for key, v in chk.run().items():
                worst[key] = min(worst.get(key, 9.0), v) if key in MINS else max(worst.get(key, 0), v)
        flag = {k: v for k, v in worst.items() if (k not in MINS and v > 0) or (k in MINS and v < -0.002)}
        print("TRANSITION", na, "->", nb, flag if flag else "clean", "| lows", {k: worst[k] for k in MINS}, flush=True)


GAME_VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.1), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-1, 0, 0.1), (0, -0.05, 1)]
BASE_VIEWS = [(0.62, -0.72, 0.5, 0.75, (0.0, -0.04, 0.1)), (-0.7, -0.6, 0.35, 0.75, (0.0, -0.04, 0.1)), (0.9, 0.3, 0.3, 0.75, (0.0, -0.04, 0.1)),
              (0, -1, 0.15, 0.75, (0.0, -0.04, 0.1)), (0, 0, 1, 0.9, (0.0, 0.06, 0.0))]
POSE_VIEWS = [(0.62, -0.72, 0.3, 2.6, (0, -0.05, 0.42)), (1, -0.05, 0.12, 2.6, (0, -0.05, 0.42))]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.04, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    tree = data["tree"]
    print("SKIN GAP (low from high, m)", round(surface_gap(lows["Skin"], tree), 4), flush=True)
    if STAGE == "all":
        serpent_unwrap(lows)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.8, 0.82, 0.83, 1), far=("Skin",), reach=(0.003, 0.008),
                 far_reach=(0.005, 0.014), reaches={"Fins": (0.002, 0.006), "EyeL": (0.002, 0.005), "EyeR": (0.002, 0.005)})
        print("FIN NORMALS flattened, texels", flat_normals_under(lows["Fins"], bpy.data.images[PET + "_Normal"]), flush=True)
    else:
        clay = bpy.data.materials.new("clay")
        gg = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        gg.inputs["Base Color"].default_value = (0.66, 0.64, 0.6, 1)
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)
    glows = game_glows(tree_of(lows["Skin"]))           # (clear of the game skin, which fills the crotch where its column lies on its coil)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    glow_tris = {o.name[len(N):]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in glows.values()}
    body_tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    print("BODY tris", body_tris, "GLOW tris", sum(glow_tris.values()), glow_tris, "ALL tris", body_tris + sum(glow_tris.values()), flush=True)
    print("dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name, (fan, lift, share) in zip(FIN_NAMES, fin_axes()):
        print("FIN", name, "fan", tuple(round(x, 4) for x in fan), "lift", tuple(round(x, 4) for x in lift), "share", round(share, 3), flush=True)
    chk = Checker(body, glows)
    pose(rig, {})
    print("POSE Rest", chk.run(), flush=True)
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
        if STAGE == "rig" and "poseshots" in ARGS and (not name.startswith("Glide") or name == "Glide1"):
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=480)
    pose(rig, lids_spec(frames, BLINK_U, BLINK_L))
    print("POSE Blink", chk.run(), flush=True)
    if "ripples" in ARGS:          # (a design aid: the ripple's size against what it does to the coil)
        for amp in ((0.02, 0.02), (0.015, 0.04), (0.015, 0.03), (0.01, 0.04), (0.012, 0.05)):
            worst = {}
            for k in range(8):
                pose(rig, spec(dict(tables["Glide"], **{n: tuple(round(x, 4) for x in v) for n, v in ripple(TAU * k / 8, *amp).items()})))
                for key, v in chk.run().items():
                    worst[key] = min(worst.get(key, 9.0), v) if key in MINS else max(worst.get(key, 0), v)
            print("RIPPLE", amp, worst, flush=True)
    if "fins" in ARGS:
        for lift in (-0.3, -0.2, -0.15, -0.1, -0.05):
            for base_name in ("Rest", "Glide", "Rise", "Bow", "Look"):
                base_t = {} if base_name == "Rest" else {k: v for k, v in tables[base_name].items() if not k.startswith("Fin")}
                pose(rig, spec(dict(base_t, **{k: tuple(round(x, 4) for x in v) for k, v in fins_turn(-0.05, lift).items()})))
                print("FINS", lift, base_name, chk.run()["fins x neck"], flush=True)
    if "base" in ARGS:
        pose(rig, {})
        shots(os.path.join(REVIEW, "base"), BASE_VIEWS, size=520)
    if "transitions" in ARGS or STAGE == "all":
        check_transitions(rig, chk, tables)
    lib = {k: spec(v) for k, v in tables.items()}
    lib["Blink"] = lids_spec(frames, BLINK_U, BLINK_L)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    if "tables" in ARGS or STAGE == "all":
        for name, table in tables.items():
            print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join(("%g" % x) if not isinstance(x, tuple) else ("%g, %g, %g" % x) for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
        for name in ("Base", "Head", "Up8", "Fin3", "EyeL"):
            p = rig.data.bones[name].head_local
            print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
        for k in range(RINGS):
            c = ring_frame(k)[0]
            print("RING", k + 1, "centre game axes", (round(-c.x, 4), round(c.z, 4), round(c.y, 4)), flush=True)
    pose(rig, {})
    if STAGE == "all" or "shots" in ARGS:
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), GAME_VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=560)
        for name in ("Glide1", "Hover", "Rise", "Look", "Bow"):
            pose(rig, spec(tables[name]))
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS, size=480)
        pose(rig, lids_spec(frames, BLINK_U, BLINK_L))
        shots(os.path.join(REVIEW, "gameposeBlink"), EXTRA[:2], size=480)
        pose(rig, {})
    if STAGE == "all":
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 2.4, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

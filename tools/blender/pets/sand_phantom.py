"""The Sand Phantom (Common, Sand; Magma Heart Egg, also in the Phoenix Ash Egg): "A shape in the blowing sand that is gone when you look straight at it.
Caravans leave it water, just in case."

A desert jerboa spirit (the owner's choice, 2026-11-09), in a design language of its own: the dunes, and a creature too quick to be sure you saw. It
sits up on long kangaroo hind legs and huge flat feet, its body a tilted egg, its tiny forepaws held to its chest; a big round head with enormous ears and
enormous dark eyes, a short muzzle with a pink nose and very long whiskers; a very long thin tail held out behind for balance, ending in a flat brush,
a dark band and a cream tip. Sand-gold fur with dune ripples across its back and flanks, light on their crests and shadowed behind them, a cream belly,
a pale stripe across each haunch, cream feet. Its eyes are near-black, rimmed in amber gold, flecked with gold like sand in the light.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/sand_phantom.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, feet on z = 0. +X is its left. The maps go to assets/pets/MagmaHeartEgg/.

What touches what: body, head, legs, feet and tail are one fused skin; the eyes sit in their sockets under their lids; the ears, the nose, the whiskers and
the tail's brush are their own pieces set into the skin.
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
PET = "SandPhantom"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "MagmaHeartEgg")

# ---------- colours: the dunes ----------
SAND, SAND_DEEP, SAND_CREST = rgb(212, 164, 98), rgb(156, 104, 54), rgb(242, 210, 150)
CREAM, CREAM_SHADE = rgb(248, 238, 214), rgb(214, 196, 166)
BAND, TIP = rgb(58, 40, 30), rgb(252, 246, 232)
EAR_IN, EAR_RIM = rgb(234, 178, 152), rgb(126, 82, 46)
NOSE_COL, NOSE_LIT, MOUTH = rgb(214, 128, 128), rgb(244, 180, 176), rgb(70, 36, 34)
WHISKER, WHISKER_TIP = rgb(70, 52, 40), rgb(236, 226, 206)
GLINT_HEX = "ffffff"

# ---------- the frame of it ----------
HEAD0, HEAD_K = V(0, -0.125, 0.42), 1.15        # the head as first laid out, and how much bigger it became
HEAD = V(0, -0.118, 0.392)                      # where it is now: lower, sitting almost straight on the body


def hv(x, y, z):
    """A point on the head, as laid out, moved and grown with it."""
    return HEAD + (V(x, y, z) - HEAD0) * HEAD_K


SPINE = [V(0, 0.12, 0.16), V(0, 0.07, 0.195), V(0, 0.015, 0.235), V(0, -0.035, 0.275), V(0, -0.065, 0.31)]     # the body tilted up: rump low behind
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.076), (0.2, 0.095), (0.5, 0.092), (0.8, 0.076), (1, 0.062))
BODY_H = ((0, 0.078), (0.2, 0.097), (0.5, 0.095), (0.8, 0.08), (1, 0.066))
NECK = catmull([V(0, -0.065, 0.31), V(0, -0.088, 0.34), V(0, -0.105, 0.37)], 8)
HEAD_R = (0.08, 0.083, 0.075)
EYE_R = 0.028 * HEAD_K
EYE_C = hv(0.047, -0.165, 0.432)
EYE_AXIS = V(0.62, -0.76, 0.18).normalized()
LID_UP, LID_LOW = (44.0, 120.0, 0.0024), (-44.0, -128.0, 0.002)       # wide open: always watching
LID_TILT = 4.0
BLINK_U, BLINK_L = 62.0, 28.0
IRIS, PUPIL = 0.96, 0.62                 # on the eye's face: nearly all dark, a big round pupil
NOSE_TOP, NOSE_BASE_Y = 0.399, -0.217     # on the tip of the muzzle (its front is at y -0.2226): set in front of it, not inside
# its legs (its left; mirrored): the hind from the hip to the toes, the fore from the shoulder to the paw held at its chest
HIND = [V(0.064, 0.085, 0.18), V(0.072, 0.015, 0.125), V(0.064, 0.11, 0.04), V(0.06, 0.0, 0.016), V(0.06, -0.045, 0.013)]
HIND_R = [0.064, 0.032, 0.017, 0.015, 0.013]
FORE = [V(0.04, -0.045, 0.275), V(0.047, -0.07, 0.23), V(0.033, -0.102, 0.245), V(0.025, -0.115, 0.26)]
FORE_R = [0.02, 0.012, 0.0105, 0.0095]
LEGS = (("BL", 1, HIND, HIND_R), ("BR", -1, HIND, HIND_R), ("FL", 1, FORE, FORE_R), ("FR", -1, FORE, FORE_R))
TAIL = catmull([V(0, 0.15, 0.17), V(0, 0.3, 0.15), V(0, 0.48, 0.16), V(0.015, 0.66, 0.2), V(0.04, 0.82, 0.26), V(0.06, 0.94, 0.33)], 10)
TAIL_R = ((0, 0.026), (0.15, 0.016), (0.6, 0.011), (1, 0.008))
TUFT_F = 0.74                             # where along the tail its brush starts


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def path_frames(path):
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0) - tan * tan.x
        side = side.normalized() if side.length > 1e-5 else V(1, 0, 0)
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


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


def toe_paths(side):
    """Three long toes forward from the ball of each hind foot, spread a little."""
    ball = mir(HIND[3], side)
    out = []
    for a in (-0.32, 0.0, 0.32):
        d = V(math.sin(a) * side, -math.cos(a), 0)
        out.append([ball + V(0, 0.004, 0.0), ball + d * 0.03 + V(0, 0, -0.002), ball + d * 0.058 + V(0, 0, -0.003)])
    return out


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f))
    core.tube(NECK, lambda f: 0.06 - 0.006 * f, sides=32)
    core.ball(SPINE[0] + V(0, 0.01, -0.01), (0.075, 0.065, 0.066))                         # the rump, low
    core.ball(V(0, -0.055, 0.24), (0.058, 0.05, 0.065))                                    # the chest
    for side in (1, -1):
        core.ball(V(side * 0.05, 0.065, 0.165), (0.052, 0.072, 0.072))                     # the haunch: big, for the spring, under the fur
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 48, 32)                                                         # the head: big and round
    fine.ball(hv(0, -0.182, 0.41), (0.046, 0.039, 0.038))                                  # the muzzle, short
    fine.ball(hv(0, -0.17, 0.384), (0.025, 0.027, 0.018))                                  # the chin
    for side in (1, -1):
        fine.ball(hv(side * 0.04, -0.15, 0.405), (0.046, 0.048, 0.044))                    # the cheek: round and full
        fine.ball(hv(side * 0.016, -0.2, 0.405), (0.02, 0.018, 0.018))                     # the whisker pad
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.005, (EYE_R * 1.08,) * 3, 32, 20)     # the socket
        fine.ball(hv(side * 0.04, -0.152, 0.458), (0.03, 0.03, 0.014))                     # the brow, soft: the lids' hidden edges stay under it
    for key, side, knots, radii in LEGS:
        fine.tube(leg_path(knots, side), lambda f, r=radii: leg_radius(r, f), sides=22, flat=0.92)
        if key[0] == "B":
            fine.ball(mir(knots[3], side) + V(0, 0.01, -0.002), (0.017, 0.03, 0.012), 18, 12)       # the sole of the long foot
            for toe in toe_paths(side):
                fine.tube(catmull(toe, 4), lambda f: 0.0085 - 0.002 * f, sides=12)
        else:
            fine.ball(mir(knots[3], side), (0.012, 0.011, 0.011), 14, 10)                    # the little hand
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0026, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- ears ----------
EAR = {"front": hv(0.026, -0.124, 0.476), "back": hv(0.07, -0.084, 0.462), "height": 0.145}


def ear_frame(side):
    A, B = mir(EAR["front"], side), mir(EAR["back"], side)
    C = A.lerp(B, 0.5)
    along = (B - A).normalized()
    want = V(side * 0.6, 0.3, 1)                           # broad, leaning out and a little back
    up = (want - along * want.dot(along)).normalized()
    n = along.cross(up).normalized()
    if n.y > 0:
        n = -n          # facing forward
    return A, B, C, along, up, n


def ear_point(side):
    """A huge, broad, rounded ear: its base along the head, its rim a tall round arc; u from the base to the rim, v across. Wider than its base in the
    middle, and the rim reaches a little past the base at both ends, so no row of the sheet is drawn to a point."""
    A, B, C, along, up, n = ear_frame(side)
    a = (B - A).length / 2

    def point(u, v):
        base = A.lerp(B, v)
        s = math.sin(math.pi * v)
        rim = C + along * (-math.cos(math.pi * v) * a * (1.3 + 0.75 * s)) + up * (s ** 0.5 * EAR["height"] + 0.008)
        p = base.lerp(rim, u)
        cup = 0.02 * s * math.sin(math.pi * min(1.0, u * 1.05))
        return tuple(p - n * cup)
    return point


def ear_thick(u, v):
    return 0.0055 * (1 - u) ** 0.7 + 0.0022


def sheet_uv(nu, nv):
    uu, vv = [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            uu += [i / nu, i / nu]
            vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


def build_ear(side, name):
    """Sand behind with a darker rim, the hollow a warm pink-sand, fine hair at its edge."""
    nu, nv = 64, 64
    o = sheet_hi(ear_point(side), ear_thick, nu, nv, name, lambda u, v: np.broadcast_to(SAND, (len(u), 3)), lambda u, v: np.full_like(u, 0.6), lambda u, v: np.zeros_like(u))
    uu, vv = sheet_uv(nu, nv)
    Nn = normals(o)
    _, _, _, _, _, n = ear_frame(side)
    inside = smooth(-0.1, 0.25, Nn @ np.array(tuple(n)))
    edge = np.minimum(np.minimum(vv, 1 - vv), (1 - uu) * 0.6)
    veins = 0.92 + 0.08 * np.sin(vv * 14.0 + uu * 3.0)
    hollow = mix(EAR_IN * 0.85, EAR_IN, smooth(0.05, 0.25, edge)) * veins[:, None]
    back = mix(np.broadcast_to(SAND, (len(uu), 3)), SAND_DEEP, smooth(0.6, 1.0, uu) * 0.5)
    col = mix(back, hollow, inside * smooth(0.02, 0.06, edge))
    col = mix(col, EAR_RIM, 1 - smooth(0.006, 0.022, edge))
    paint(o, col, np.full(len(uu), 0.62), np.zeros(len(uu)))
    return o


# ---------- nose, whiskers, the tail's brush ----------
def nose_point(sx, sy, sz):
    t = (1 - sz) / 2
    w = 0.0125 * (1 - t) ** 0.7 + 0.0018
    depth = (0.006 + 0.004 * t) if sy < 0 else 0.006
    return V(sx * w, NOSE_BASE_Y + sy * depth, NOSE_TOP - 0.012 * t)


def build_nose(name, coll, seg=32, rings=20):
    m = Mesh()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in m.bm.verts:
        v.co = nose_point(v.co.x, v.co.y, v.co.z)
    return m.finish(name, coll)


def paint_nose(o):
    P = verts(o)
    Nn = normals(o)
    col = mix(NOSE_COL, NOSE_LIT, smooth(-0.2, 0.9, Nn[:, 2]) * 0.6)
    nostril = np.zeros(len(P))
    for side in (1, -1):
        c = np.array((side * 0.0045, NOSE_BASE_Y - 0.008, NOSE_TOP - 0.009))
        nostril = np.maximum(nostril, 1 - smooth(0.0011, 0.0022, np.linalg.norm((P - c) * np.array([1.0, 1.6, 0.8]), axis=1)))
    col = mix(col, MOUTH, nostril)
    paint(o, col, 0.3 + 0.4 * nostril, np.zeros(len(P)))


def whisker_paths():
    """Six very long whiskers each side, sweeping out and back, drooping a little."""
    out = []
    for side in (1, -1):
        for k in range(6):
            root = hv(side * (0.02 + 0.002 * k), -0.204 + 0.003 * k, 0.41 - 0.004 * k)
            d = V(side * 0.9, 0.3 + 0.06 * k, 0.2 - 0.09 * k).normalized()
            length = 0.13 - 0.01 * abs(k - 2.5)
            out.append([root - d * 0.004, root + d * length * 0.5 + V(0, 0, -0.004), root + d * length + V(0, 0, -0.015 - 0.003 * k)])
    return out


def build_whiskers(name, coll, sides=6, per=5):
    m = Mesh()
    for pts in whisker_paths():
        m.tube(catmull(pts, per), lambda f: 0.0011 * (1 - 0.6 * f) + 0.0004, sides=sides)
    return m.finish(name, coll)


def paint_whiskers(o):
    P = verts(o)
    d = np.abs(P[:, 0])
    paint(o, mix(np.broadcast_to(WHISKER, (len(P), 3)), WHISKER_TIP, smooth(0.04, 0.12, d)), np.full(len(P), 0.4), np.zeros(len(P)))


def build_tail(name, coll, sides=18, per=10):
    """The long thin tail, its own piece: a skinned tube would come out too coarse in the game mesh. It starts inside the rump; each vertex carries how
    far along it is ("along")."""
    m = Mesh()
    m.bm.verts.layers.float.new("along")
    al = m.bm.verts.layers.float["along"]
    # it ends a little inside the brush, where the brush is already thicker than it, so its sides never run along the brush's flat faces
    end = TUFT_F + 0.1
    knots = [TAIL[0] + (TAIL[0] - TAIL[3]).normalized() * 0.03] + [path_at(TAIL, f) for f in np.linspace(0, end, 9)]
    path = catmull(knots, per)
    m.tube(path, lambda f: prof(TAIL_R, f * end) * (1 - 0.5 * smooth(0.93, 1.0, f)), sides=sides)
    f, _ = nearest_on(TAIL, np.array([tuple(v.co) for v in m.bm.verts]))
    for v, ff in zip(m.bm.verts, f):
        v[al] = float(ff)
    return m.finish(name, coll)


def paint_tail(o):
    """Sand at the root fading paler along it, fine hairs lying back."""
    P = verts(o)
    f = read_tag(o, "along")
    hair = 0.9 + 0.1 * np.sin(P[:, 1] * 400.0 + np.arctan2(P[:, 2] - 0.2, P[:, 0]) * 6)
    col = mix(np.broadcast_to(SAND, (len(P), 3)), CREAM_SHADE, smooth(0.25, 0.9, f))
    paint(o, col * hair[:, None], np.full(len(P), 0.66), np.zeros(len(P)))


def tuft_path():
    return [path_at(TAIL, TUFT_F + (1 - TUFT_F) * t) for t in np.linspace(0, 1, 9)] + [TAIL[-1] + (TAIL[-1] - TAIL[-2]).normalized() * 0.035]


def tuft_radius(f):
    """The brush: swelling from the tail, broadest past its middle, rounded off at its end."""
    body = 0.012 + 0.03 * math.sin(math.pi * min(1.0, f * 0.85)) ** 0.8
    return body * math.sqrt(max(0.0, 1 - float(smooth(0.72, 1.0, f)) ** 2)) + 0.002       # a rounded end, never a flat cut, never a point


def build_tuft(name, coll, sides=24, per=6):
    """Flat side to side, like the brush of a jerboa's tail; each vertex carries how far along it is ("along")."""
    m = Mesh()
    m.bm.verts.layers.float.new("along")
    al = m.bm.verts.layers.float["along"]
    path = catmull(tuft_path(), per)
    # flat side to side, except where the tail enters it: there it is as thick as the tail and a little more, so the tail stays inside
    loft(m, path, lambda f: max(tuft_radius(f) * 0.38, 0.0125 * (1 - smooth(0.3, 0.45, f))), tuft_radius, nt=sides)
    f, _ = nearest_on(path, np.array([tuple(v.co) for v in m.bm.verts]))
    for v, ff in zip(m.bm.verts, f):
        v[al] = float(ff)
    return m.finish(name, coll)


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices))
    a.data.foreach_get("value", out)
    return out


def paint_tuft(o):
    """Sand where it leaves the tail, then a dark band, then a cream tip; fine hairs along it."""
    P = verts(o)
    f = read_tag(o, "along")
    hair = 0.88 + 0.12 * np.sin(P[:, 2] * 900.0 + P[:, 1] * 120.0)
    col = mix(np.broadcast_to(SAND, (len(P), 3)), BAND, smooth(0.1, 0.25, f))
    col = mix(col, TIP, smooth(0.55, 0.7, f))
    paint(o, col * hair[:, None], np.full(len(P), 0.66), np.zeros(len(P)))


# ---------- paint ----------
def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    head = 1 - smooth(0.08, 0.115, np.linalg.norm(P - np.array(tuple(HEAD + V(0, -0.03, -0.01))), axis=1))
    tf, td = nearest_on(TAIL, P)
    on_tail = (1 - smooth(0.0, 0.012, td - np.array([prof(TAIL_R, float(f)) for f in tf]))) * smooth(0.02, 0.08, tf)
    feet = smooth(0.06, 0.03, z) * (1 - on_tail)
    fur = fbm(P * np.array([200.0, 60.0, 200.0]), 1.0, 3, 3)
    col = mix(SAND * 0.9, SAND, smooth(0.3, 0.7, fur))
    # the dunes: ripples across its back and flanks, each a gentle slope lit on its crest and a steep, shadowed lee
    warp = fbm(P, 9.0, 3, 17) - 0.5
    phase = (y * 1.0 - z * 0.55) * 95.0 + warp * 14.0 + np.sin(x * 60.0) * 1.6        # wavy, as wind lays them, never straight bands
    saw = np.mod(phase / TAU, 1.0)
    crest = smooth(0.7, 0.86, saw) * (1 - smooth(0.86, 0.92, saw))                         # a thin lit crest
    lee = smooth(0.86, 0.92, saw) * (1 - smooth(0.95, 1.0, saw))                           # and a narrow shadow just behind it
    back = smooth(-0.35, 0.3, Nn[:, 2] + 0.25 * np.abs(Nn[:, 0])) * (1 - head) * (1 - feet)
    col = mix(col, SAND_CREST, crest * back * 0.7)
    col = mix(col, SAND_DEEP, lee * back * 0.3)
    col = mix(col, SAND_DEEP * 1.1, smooth(0.4, 0.95, Nn[:, 2]) * (1 - head) * 0.25)              # darker along the spine
    # the cream underside, throat and muzzle; the feet cream; a pale stripe across each haunch
    under = smooth(-0.1, -0.6, Nn[:, 2] + 0.35 * Nn[:, 1]) * (1 - on_tail)
    col = mix(col, CREAM, under * 0.9)
    stripe = np.zeros(len(P))
    for side in (1, -1):
        c = np.array((side * 0.1, 0.06, 0.17))
        d = np.linalg.norm((P - c) * np.array([0.6, 1.0, 1.0]), axis=1)
        stripe = np.maximum(stripe, (1 - smooth(0.004, 0.009, np.abs(d - 0.052))) * (x * side > 0.06) * (P[:, 1] > 0.02))
    col = mix(col, CREAM, stripe * 0.85)
    col = mix(col, CREAM, feet * 0.9)
    muzzle = (1 - smooth(0.03, 0.046, np.linalg.norm((P - np.array(tuple(hv(0, -0.19, 0.4)))) * np.array([1.0, 1.0, 1.2]), axis=1)))
    col = mix(col, CREAM, muzzle * 0.85)
    rings = np.zeros(len(P))
    for side in (1, -1):
        r = np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1)
        rings = np.maximum(rings, smooth(EYE_R * 1.55, EYE_R * 1.2, r))
    col = mix(col, CREAM, rings * 0.8)
    # the mouth
    fy, fz = HEAD0.y + (y - HEAD.y) / HEAD_K, HEAD0.z + (z - HEAD.z) / HEAD_K          # as laid out
    lip = (1 - smooth(0.0009, 0.0023, np.abs(fz - (0.392 + 6 * x ** 2)))) * (np.abs(x) < 0.023) * (fy < -0.185)
    philtrum = (np.abs(x) < 0.0014) * (fz < 0.404) * (fz > 0.392) * (fy < -0.2)
    mouth = np.clip(lip + philtrum, 0, 1)
    col = mix(col, MOUTH, mouth * 0.85)
    relief = (fur - 0.5) * 0.00035 + 0.0006 * crest * back - 0.0005 * lee * back - 0.0006 * mouth
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, 0.68 - 0.1 * smooth(0.45, 0.8, fur), np.zeros(len(P)))


def eye_paint(o, fr):
    """Near-black and huge, a ring of amber gold at its rim, flecks of gold in the dark like sand in the light, a big round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(10, 8, 6), (len(px), 3)).copy()
    iris = mix(rgb(52, 32, 18), rgb(24, 14, 8), smooth(PUPIL, IRIS, r))
    iris = mix(iris, rgb(214, 150, 60), smooth(IRIS - 0.14, IRIS - 0.05, r) * (1 - smooth(IRIS - 0.03, IRIS, r)))
    flecks = (fbm(np.stack([px * 9, py * 9, np.zeros_like(px)], 1), 1.0, 2, 5) > 0.64) * smooth(PUPIL + 0.02, PUPIL + 0.1, r) * (1 - smooth(IRIS - 0.16, IRIS - 0.1, r))
    iris = mix(iris, rgb(196, 140, 58), flecks * 0.7)
    col = mix(col, iris, 1 - smooth(IRIS - 0.02, IRIS + 0.01, r))
    col = mix(col, rgb(2, 2, 2), 1 - smooth(PUPIL - 0.03, PUPIL + 0.01, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


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
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SAND, BAND)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, CREAM, BAND * 1.4, lower_share=0.8)
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi")
    pieces["Nose"] = build_nose(N + "NoseHi", HI)
    pieces["Whiskers"] = build_whiskers(N + "WhiskersHi", HI)
    pieces["Tail"] = build_tail(N + "TailHi", HI)
    pieces["Tuft"] = build_tuft(N + "TuftHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0062, 14), (24, -18, 0.0028, 8)))}
    if not clay:
        paint_skin(skin)
        paint_nose(pieces["Nose"])
        paint_whiskers(pieces["Whiskers"])
        paint_tuft(pieces["Tuft"])
        paint_tail(pieces["Tail"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.3, 0.28)
FACE_AT = tuple(hv(0, -0.15, 0.45))
EXTRA = [(0, -1, 0.05, 0.6, FACE_AT), (0.62, -0.75, 0.2, 0.6, FACE_AT), (1, -0.12, 0.08, 0.6, FACE_AT), (0.35, -0.9, 0.15, 0.3, tuple(EYE_C)),
         (1, -0.1, 0.1, 0.9, (0, 0.0, 0.25)), (0.8, 0.4, 0.3, 0.6, (0.04, 0.88, 0.3))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.025, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3200
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Nose": 3.0, "EarL": 1.3, "EarR": 1.3, "Whiskers": 0.6, "Tuft": 1.2, "Tail": 1.0}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 10, 9, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 26, 18)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Nose"] = build_nose(N + "NoseLow", GAME, 14, 10)
    lows["Whiskers"] = build_whiskers(N + "WhiskersLow", GAME, 4, 2)
    lows["Tuft"] = build_tuft(N + "TuftLow", GAME, 10, 3)
    lows["Tail"] = build_tail(N + "TailLow", GAME, 8, 3)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK = BODY_PATH + NECK[1:] + [HEAD]
TRUNK_HEADS = (("Hips", SPINE[0], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Neck", NECK[0], "Chest"), ("Head", NECK[-1], "Neck"))
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.02, 0.18, 0.36, 0.54, 0.72, 0.88)
TAIL_MID = (2 * TAIL_F[0] - (TAIL_F[0] + TAIL_F[1]) / 2,) + tuple((a + b) / 2 for a, b in zip(TAIL_F, TAIL_F[1:] + (1.0,)))
LEG_NAMES = {"BL": ["LegBL1", "LegBL2", "LegBL3", "FootBL"], "BR": ["LegBR1", "LegBR2", "LegBR3", "FootBR"], "FL": ["ArmL1", "ArmL2", "HandL"], "FR": ["ArmR1", "ArmR2", "HandR"]}


def leg_line(knots, side):
    return catmull([mir(p, side) for p in knots], 8)


def leg_mids(knots, names):
    fs = [k / (len(knots) - 1) for k in range(len(knots))]
    return tuple((fs[k] + fs[k + 1]) / 2 if k + 1 < len(fs) else 1.02 for k in range(len(names)))


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        A, B, C, along, up, n = ear_frame(side)
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"), ("Ear" + tag, C.copy(), "Head")]
    for key, side, knots, _ in LEGS:
        parent = "Hips" if key[0] == "B" else "Chest"
        line = leg_line(knots, side)
        fs = [k / (len(knots) - 1) for k in range(len(knots))]
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, path_at(line, fs[k]), parent))
            parent = name
    return armature(bones)


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.03,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def body_weights(P):
    """The skin's weights at any points: the trunk, the head, the tail, the legs and arms; a foot and its toes wholly its foot's."""
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P)
    hz = np.linalg.norm((P - np.array(tuple(HEAD + V(0, -0.03, 0.0)))) / np.array((0.095, 0.11, 0.095)), axis=1)
    tf, td = nearest_on(TAIL, P)
    legs = []
    for key, side, knots_l, radii in LEGS:
        f, d = nearest_on(leg_line(knots_l, side), P)
        legs.append((key, side, knots_l, radii, f, d))
    out = []
    for i in range(len(P)):
        x, y, z = P[i]
        owner = None
        for key, side, knots_l, radii, f, d in legs:
            if key[0] == "B" and (Vector(P[i]) - mir(knots_l[3], side)).length < 0.075 and z < 0.03:
                owner = "Foot" + key
        if owner:
            out.append({owner: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.9, hz[i])))
        reach = prof(TAIL_R, float(tf[i])) * 1.3 + 0.008
        share = (1 - float(smooth(reach, reach + 0.015, td[i]))) * float(smooth(0.0, 0.06, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(tf[i])), share)
        for key, side, knots_l, radii, f, d in legs:
            if x * side <= 0.008:
                continue
            lr = leg_radius(radii, float(f[i])) + 0.01
            outer = lr * (1.2 + 0.6 * float(smooth(0.4, 0.1, f[i])))
            mm = float(smooth(0.05, 0.22, f[i])) * (1 - float(smooth(lr * 0.8, outer, d[i])))
            mm *= float(smooth(0.01, 0.05, x * side)) if z > knots_l[1].z - 0.015 else 1.0
            if mm > 0:
                w = blend(w, chain_weight(LEG_NAMES[key], leg_mids(knots_l, LEG_NAMES[key]), float(f[i])), mm)
        out.append(w)
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Nose"], "Head")
    rigid(lows["Whiskers"], "Head")
    weigh(lows["Tuft"], [chain_weight(TAIL_NAMES[-2:], (0.0, 0.3), float(f)) for f in read_tag(lows["Tuft"], "along")])
    weigh(lows["Tail"], [chain_weight(["Hips"] + TAIL_NAMES, TAIL_MID, float(f)) for f in read_tag(lows["Tail"], "along")])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateSandPhantom uses. +X lifts what points forward (and swings a hanging leg forward); +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def hind(t, s, h, f):
    out = {}
    for side in "LR":
        out["LegB%s1" % side], out["LegB%s2" % side], out["LegB%s3" % side], out["FootB%s" % side] = (t, 0, 0), (s, 0, 0), (h, 0, 0), (f, 0, 0)
    return out


# its stances, searched in Blender against the ground and for torn skin (see the vault): the same numbers as PetRig's SAND_* tables
CROUCH = {"Hips": (0, 0, 0, (0, -0.025, 0)), "Body": (-0.064, 0, 0), **hind(0.308, -0.47, 0.062, 0.3)}            # gathered for the hop, feet planted
SPRING = {"Body": (0.1, 0, 0), **hind(-0.6, 0.6, -0.4, -0.5), **{n: (0.05, 0, 0) for n in TAIL_NAMES}}        # legs flung back, mid-air (lifted by the hop)
UPRIGHT = {"Hips": (0, 0, 0, (0, 0.046, 0)), "Body": (0.261, 0, 0), "Chest": (0.1, 0, 0), "Head": (-0.2, 0, 0), **hind(0.208, -0.117, -0.496, 0.019)}    # up tall, feet planted


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-6, -5), "Crouch": spec(CROUCH), "Spring": spec(SPRING), "Upright": spec(UPRIGHT),
            "Look": spec({"Neck": (0.15, 0.4, 0), "Head": (0.2, 0.5, 0.2)}), "Tail": spec({n: (0.06, 0.12, 0) for n in TAIL_NAMES}),
            "Ears": spec({"EarL": (-0.5, 0.3, 0), "EarR": (-0.5, -0.3, 0)}), "Groom": spec({"ArmL1": (0.6, 0, 0), "ArmL2": (-0.6, 0, 0), "ArmR1": (0.6, 0, 0), "ArmR2": (-0.6, 0, 0)})}


def lowest_of(body, parts):
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, bones in parts.items():
        idx = {groups[b] for b in bones if b in groups}
        mine = [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)]
        out[name] = round(float(co[mine, 2].min()), 4) if mine else None
    return out


GROUND_PARTS = {"Feet": ("FootBL", "FootBR"), "Hips": ("Hips",), "Tail": tuple(TAIL_NAMES), "Belly": ("Body", "Chest")}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.025, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.y < -0.08 and p.center.z > 0.33, 2.2), (None, 1.0)], SCALES, margin=0.009)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.8, 0.6, 0.38, 1), far=("Skin",), reach=(0.005, 0.012), far_reach=(0.008, 0.02),
             reaches={"Whiskers": (0.0015, 0.004)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    bpy.data.objects.remove(glows["Glints"], do_unlink=True)          # first, so the game's piece takes its exact name
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0062, 10), (24, -18, 0.0028, 6)))}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows, data)
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
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Hips", "Head", "Tail6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Crouch", "Spring", "Upright"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.08, 2.0, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.55, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Crouch", side), ("Spring", side), ("Upright", side), ("Look", face), ("Tail", side), ("Ears", face), ("Groom", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 2.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

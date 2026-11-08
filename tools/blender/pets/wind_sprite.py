"""The Wind Sprite (Common, Wind; Spirit Breeze Egg): "A curl of breeze that decided to stay. It tugs at sleeves when it wants attention."

A new creature, not based on anything before it. A baby wind spirit: its body runs out into one great scroll-curl of wind, it flies on a
pair of maple-seed wings, has little robe-sleeve arms to tug with and a jade bead on a coral cord. One smooth skin on bones, so the tail really
curls and streams, the eyes look about and blink under real lids, and it puffs its cheeks and blows.

Colours: pearl and mint, deepening to teal in the wind's ribbons; coral and gold as the one warm accent.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/wind_sprite.py -- [paint|all] [review dir]

paint: builds and paints the high-detail model and renders it. all: also makes the game mesh, bakes, rigs and writes the file and the FBX.
Faces -Y, Z up. The maps go to assets/pets/SpiritBreezeEgg/.
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
PET = "WindSprite"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "SpiritBreezeEgg")


PEARL, MINT, JADE, TEAL, DEEP = rgb(226, 246, 238), rgb(182, 238, 222), rgb(98, 208, 182), rgb(44, 156, 150), rgb(22, 96, 106)
CORAL, GOLD, BLUSH, HAND = rgb(240, 104, 84), rgb(244, 190, 92), rgb(250, 150, 138), rgb(250, 232, 220)


# ---------- the design, as numbers ----------
HEAD = V(0, -0.02, 0.86)
HEAD_R = (0.36, 0.32, 0.30)
CURL_C = V(0.0, 0.485, 0.30)
CURL_R = 0.33
CURL_FROM, CURL_TO = math.radians(205), math.radians(650)
ARM_ROOT = V(0.135, -0.03, 0.495)
ARM_TIP = V(0.255, -0.185, 0.345)
WING_ROOT = V(0.105, 0.125, 0.535)
WING_U = V(0.76, 0.42, 0.50).normalized()
WING_V = (V(0.0, 0.42, -1.0) - WING_U * V(0.0, 0.42, -1.0).dot(WING_U)).normalized()   # the blade faces front and back, so it reads from both
WING_L = 0.68
EAR_ROOT = V(0.285, 0.03, 1.0)
EAR_U = V(0.70, 0.42, 0.58).normalized()
EAR_L = 0.37
EYE_R = 0.152
EYE_AXIS = V(0.26, -0.96, 0.02).normalized()
LID_TILT = 7.0
LID_U, LID_U_FAR, LID_U_GAP = 38.0, 150.0, 0.0055       # upper lid: edge, how far back it runs, how far off the ball, in degrees and metres
LID_L, LID_L_FAR, LID_L_GAP = -56.0, -135.0, 0.0042     # the lower one rests in the cheek and rises only to meet the upper
BLINK_U, BLINK_L = 72.0, 22.0
EYE_C = V(0.1413, -0.1969, 0.8479)     # the ball's centre


def curl_point(s):
    th = CURL_FROM + (CURL_TO - CURL_FROM) * s
    r = CURL_R * (1 - s) ** 0.92 + 0.028
    x = 0.055 * math.sin(s * math.pi * 1.25)
    return CURL_C + V(x, math.cos(th) * r, math.sin(th) * r)


def curl_radius(s):
    return 0.03 + 0.104 * (1 - s) ** 0.72 * min(1.0, 0.72 + s * 2.2)


# the hair: one big lock swept up and back off the crown, leaning a little to its left, its tip curling over like a wave; two lower locks
# lie along the head and flick out over the ears
CREST_MAIN = catmull([HEAD + V(0.0, -0.13, 0.245), HEAD + V(0.02, -0.05, 0.325), HEAD + V(0.06, 0.05, 0.395), HEAD + V(0.115, 0.155, 0.45),
                      HEAD + V(0.175, 0.235, 0.535), HEAD + V(0.215, 0.225, 0.64), HEAD + V(0.215, 0.125, 0.672), HEAD + V(0.18, 0.06, 0.61),
                      HEAD + V(0.16, 0.095, 0.55)], 10)
# and a little forelock that has escaped down the forehead
CREST_FORE = catmull([HEAD + V(0.0, -0.12, 0.272), HEAD + V(0.014, -0.2, 0.238), HEAD + V(0.024, -0.262, 0.185), HEAD + V(0.006, -0.298, 0.128)], 8)


def crest_side(side):
    return catmull([HEAD + V(side * 0.05, -0.10, 0.262), HEAD + V(side * 0.13, -0.03, 0.272), HEAD + V(side * 0.205, 0.06, 0.25),
                    HEAD + V(side * 0.235, 0.115, 0.222), HEAD + V(side * 0.19, 0.11, 0.15)], 8)




def ear_point(side):
    U = mir(EAR_U, side)
    V_ = (V(0, 0.5, -1) - U * V(0, 0.5, -1).dot(U)).normalized()
    N_ = U.cross(V_) * side
    root = mir(EAR_ROOT, side)

    def point(u, v):
        half = 0.088 * math.sin(math.pi * min(1.0, u ** 0.70)) ** 0.82 + 0.002
        w = (v - 0.5) * 2
        return root + U * EAR_L * u + V_ * half * w + N_ * (0.055 * (1 - w * w) * math.sin(math.pi * u) - 0.09 * u * u) + V(0, 0.06, 0.05) * u * u
    return point


def wing_point(side):
    U, V_ = mir(WING_U, side), mir(WING_V, side)
    Nn = U.cross(V_) * side
    root = mir(WING_ROOT, side)

    def point(u, v):
        lead = 0.024 * math.sin(math.pi * min(1.0, u * 1.05))
        trail = 0.205 * math.sin(math.pi * u ** 0.62) ** 0.78 + 0.018
        y = -lead + (lead + trail) * v
        twist = 0.30 * u * (y - 0.08)
        return root + U * WING_L * u + V_ * y + Nn * (twist + 0.05 * math.sin(math.pi * u))
    return point


def ear_thick(u, v):
    return 0.024 * (1 - 0.6 * u)


def wing_thick(u, v):
    return (0.034 - 0.016 * v) * (1 - 0.4 * u)


def build_skin():
    core = Mesh()
    core.ball(HEAD, HEAD_R, 64, 40)
    for side in (1, -1):
        core.ball(HEAD + V(side * 0.165, -0.125, -0.105), (0.145, 0.145, 0.118))    # full cheeks, low on the face
        # the socket: a swell of the head just under the ball at the front, rising past the lid's shell at a shallow angle, so lid and face melt together
        socket = mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.03
        core.ball(socket, (0.168, 0.168, 0.168))
        core.ball(mir(ARM_ROOT, side) + V(-side * 0.035, 0, 0), (0.07, 0.07, 0.07))     # shoulders
        core.ball(mir(WING_ROOT, side) - mir(WING_U, side) * 0.035, (0.065, 0.06, 0.06))     # where a wing seats
    core.ball(HEAD + V(0, 0.05, 0.075), (0.28, 0.255, 0.215))    # a rounder crown
    core.ball(V(0, -0.04, 0.385), (0.17, 0.152, 0.162))         # the little round belly
    spine = catmull([V(0, 0.0, 0.62), V(0, 0.0, 0.53), V(0, 0.02, 0.43), V(0, 0.06, 0.33), V(0, 0.12, 0.23), curl_point(0.03)], 8)
    core.tube(spine, lambda f: 0.112 + 0.09 * math.sin(math.pi * min(1.0, f + 0.14)) ** 1.1 - 0.02 * f, sides=24, flat=1.04)
    # the root of the curl belongs to the body's mass, so the big smooth makes a fillet of the join
    core.tube([curl_point(0.22 * k / 16) for k in range(17)], lambda f: curl_radius(0.22 * f) * (0.98 - 0.3 * smooth(0.5, 1.0, f)) * min(1.0, 0.5 + f * 5), sides=20, flat=0.88)
    # the sleeves: narrow at the shoulder, belling to a rolled cuff with a little mitt past it
    for side in (1, -1):
        a, b = mir(ARM_ROOT, side), mir(ARM_TIP, side)
        mid = a.lerp(b, 0.5) + V(side * 0.035, 0, 0.02)
        core.tube(catmull([a, mid, b], 8), lambda f: 0.054 + 0.056 * f ** 1.6, sides=16)
        d = (b - mid).normalized()
        core.ball(b + d * 0.02, (0.098, 0.098, 0.098), 24, 16)
        core.ball(b + d * 0.078, (0.064, 0.064, 0.064), 20, 14)
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.016, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 45})])
    thin = Mesh()
    # the great curl
    thin.tube([curl_point(0.07 + 0.93 * k / 150) for k in range(151)], lambda f: curl_radius(0.07 + 0.93 * f), sides=20, flat=0.88)
    thin.ball(curl_point(1.0), (0.03 * 0.88, 0.03, 0.03), 16, 10)
    # the cowlick and its two smaller licks
    thin.tube(CREST_MAIN, lambda f: 0.018 + 0.074 * (1 - f) ** 0.85 * min(1.0, 0.55 + f * 3.2), sides=14, flat=1.45)
    for side in (1, -1):
        thin.tube(crest_side(side), lambda f: 0.007 + 0.05 * (1 - f) ** 0.9 * min(1.0, 0.6 + f * 3), sides=12, plane=V(0, 0, 1), flat=0.8)
    th = thin.finish(N + "ThinHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    # one surface now, dense enough to carry the detail
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0052, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 12})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- painting ----------


CURL_S = [curl_point(k / 90) for k in range(91)]


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    s, d = nearest_on(CURL_S, P)
    # how much of the tail each point is
    tail = (d < np.interp(s, [0, 1], [0.19, 0.05])) * smooth(0.02, 0.1, s) * (z < 0.60) * (y > 0.06)
    tail = np.where((s < 0.1) & (y < 0.2) & (z > 0.42), 0, tail)
    head = smooth(0.565, 0.625, z)
    fm, dm = nearest_on(CREST_MAIN, P)
    fl, dl = nearest_on(crest_side(1), P)
    fr, dr = nearest_on(crest_side(-1), P)
    hair_d = np.minimum(dm, np.minimum(dl, dr))
    hair_f = np.where(dm <= hair_d, fm, np.where(dl < dr, fl, fr))
    hair = (1 - smooth(0.055, 0.09, dm)) * smooth(0.0, 0.06, z - 1.03)
    side_f = np.where(dl < dr, fl, fr)
    hair = np.maximum(hair, (1 - smooth(0.05, 0.075, np.minimum(dl, dr))) * smooth(0.0, 0.06, z - 1.03) * (1 - smooth(0.62, 0.92, side_f)))

    # the ground colour: pearl front, mint back, deeper low down
    front = smooth(0.15, -0.55, Nn[:, 1])
    for side in (1, -1):        # round each eye the face stays pearl, the colour of the lid
        front = np.maximum(front, 1 - smooth(0.19, 0.24, np.linalg.norm(P - np.array(tuple(mir(EYE_C, side))), axis=1)))
    col = mix(MINT, PEARL, front * 0.9 + 0.1 * noise3(P, 7.0))
    col = mix(col, mix(MINT, JADE, 0.45), smooth(0.5, 0.26, z) * (1 - front) * (1 - tail))

    # the wind's ribbons, wound round the body and on along the curl
    theta = np.arctan2(x, y - 0.03)
    body_rib = np.cos(2 * theta + z * 15.0 + 0.6)
    body_band = smooth(0.62, 0.86, body_rib) * smooth(0.56, 0.5, z) * (1 - tail) * smooth(-0.2, 0.25, Nn[:, 1])
    # round the tail: the angle round its tube
    ii = np.clip((s * 90).astype(int), 0, 89)
    samples = np.array([tuple(p) for p in CURL_S])
    tang = samples[ii + 1] - samples[ii]
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    near = samples[ii] + (samples[ii + 1] - samples[ii]) * ((s * 90 - ii)[:, None])
    rad = P - near
    rad -= tang * (rad * tang).sum(1)[:, None]
    ang = np.arctan2(rad[:, 0], (rad * np.stack((np.zeros_like(x), tang[:, 2], -tang[:, 1]), 1)).sum(1))
    rib = np.cos(2 * ang + s * 26.0)
    band = smooth(0.42, 0.72, rib) * (1 - smooth(0.82, 0.93, s))     # the tip stays one clean colour
    tail_col = mix(mix(JADE, MINT, smooth(0.05, 0.5, s)), PEARL, smooth(0.5, 0.98, s))
    tail_col = mix(tail_col, mix(TEAL, JADE, smooth(0.35, 0.95, s)), band * (1 - smooth(0.82, 1.0, s) * 0.7))
    tail_col = mix(tail_col, DEEP, smooth(0.86, 0.97, rib) * (1 - smooth(0.6, 0.95, s)) * 0.55)
    col = mix(col, tail_col, tail)
    col = mix(col, TEAL, body_band * 0.8)

    # the face: pearl, the blush on the cheeks
    col = mix(col, PEARL, head * front * 0.85)
    for side in (1, -1):
        cheek = np.exp(-(((x - side * 0.245) / 0.07) ** 2 + ((z - 0.72) / 0.05) ** 2)) * (y < 0)
        col = mix(col, BLUSH, cheek * 0.62)
    # the back of the head and the hair: mint to jade at the root, pearl at the tips, a thin dark line along each lick
    crown = head * smooth(-0.2, 0.5, Nn[:, 2]) * (1 - front)
    col = mix(col, mix(MINT, JADE, 0.3), crown * 0.8)
    tip = np.where((dm <= hair_d)[:, None], PEARL, mix(MINT, JADE, 0.2))
    hair_col = mix(mix(JADE, TEAL, 0.25), tip, smooth(0.25, 0.92, hair_f))
    col = mix(col, hair_col, hair)
    # strands
    strand = np.sin(hair_d * 210) * 0.5 + 0.5      # lines running along each lock
    col = mix(col, DEEP, hair * smooth(0.8, 1.0, strand) * 0.14 * (1 - smooth(0.22, 0.5, hair_f)))

    # a whorl of wind on the back of the head
    bx, bz = x, z - 0.875
    br = np.sqrt(bx ** 2 + bz ** 2)
    whorl = np.cos(2 * np.arctan2(bz, bx) + br * 19.0)
    whorl_band = smooth(0.55, 0.85, whorl) * smooth(0.1, 0.4, Nn[:, 1]) * head * (1 - hair) * (1 - smooth(0.2, 0.31, br))
    col = mix(col, mix(TEAL, JADE, 0.3), whorl_band * 0.85)

    # the sleeves
    rough = np.full(len(P), 0.55)
    disp = -0.0035 * smooth(0.5, 0.8, rib) * tail - 0.0028 * body_band - 0.0028 * whorl_band
    for side in (1, -1):
        a, b = mir(ARM_ROOT, side), mir(ARM_TIP, side)
        dirn = (b - a)
        L = dirn.length
        dirn = dirn / L
        A, Dv = np.array(tuple(a)), np.array(tuple(dirn))
        t = ((P - A) * Dv).sum(1) / L
        perp = np.linalg.norm((P - A) - Dv[None, :] * (t * L)[:, None], axis=1)
        arm = ((perp < 0.145) & (t > -0.1) & (t < 1.62)) * smooth(0.0, 0.18, t)
        sleeve = mix(PEARL, MINT, smooth(0.0, 0.85, t) * 0.35)
        sleeve = mix(sleeve, CORAL, smooth(0.86, 0.92, t) * (1 - smooth(1.11, 1.16, t)))
        sleeve = mix(sleeve, GOLD, smooth(0.8, 0.84, t) * (1 - smooth(0.86, 0.89, t)))
        sleeve = mix(sleeve, HAND, smooth(1.13, 1.2, t))
        col = mix(col, sleeve, arm)
        folds = np.sin(t * 22 + np.arctan2(P[:, 2] - a.z, P[:, 0] - a.x) * 2) * smooth(0.1, 0.5, t) * (1 - smooth(0.78, 0.86, t))
        disp = disp + 0.0032 * folds * arm
    P2 = P + Nn * disp[:, None]
    set_verts(o, P2)
    paint(o, col, rough)


def wing_veins(u, v):
    """Fan veins from the seed to the trailing edge, as in a real maple key."""
    fan = np.arctan2(v * 0.22 + 0.001, u * 0.68 + 0.02)
    lines = np.abs(np.sin(fan * 12.5))
    main = 1 - smooth(0.02, 0.24, lines)
    return main * smooth(0.04, 0.14, u) * smooth(0.0, 0.06, 1 - v + 0.02)


def wing_colour(u, v):
    base = mix(PEARL, MINT, smooth(0.0, 0.8, v) * 0.75)
    base = mix(base, mix(JADE, MINT, 0.3), (1 - smooth(0.0, 0.09, v)))          # the thick leading edge
    base = mix(base, rgb(246, 170, 140), smooth(0.68, 1.0, u) * smooth(0.25, 1.0, v) * 0.75)  # a warm blush at the tip, as the seed's wing ripens
    base = mix(base, JADE, smooth(0.32, 0.0, u) * 0.75)                        # greening toward the seed
    base = mix(base, TEAL, wing_veins(u, v) * 0.8)
    return base


def build_wing(side, name):
    o = sheet_hi(wing_point(side), wing_thick, 200, 240, N + name + "Hi", wing_colour, lambda u, v: np.full_like(u, 0.32),
                 lambda u, v: 0.0028 * wing_veins(u, v))
    return o


def build_nut(side, name):
    m = Mesh()
    c = mir(WING_ROOT, side) + mir(WING_U, side) * 0.015
    q = mir(WING_U, side).to_track_quat("Z", "Y").to_matrix().to_4x4()
    mat = Matrix.Translation(c) @ q @ Matrix.Diagonal((0.066, 0.066, 0.088, 1))
    bmesh.ops.create_uvsphere(m.bm, u_segments=96, v_segments=64, radius=1.0, matrix=mat)
    o = m.finish(N + name + "NutHi", HI)
    P = verts(o)
    Nn = normals(o)
    loc = (P - np.array(tuple(c))) @ np.array(q.to_3x3())   # local coordinates
    az = np.arctan2(loc[:, 1], loc[:, 0])
    ribs = np.abs(np.sin(az * 3.5))
    set_verts(o, P + Nn * (0.006 * (ribs - 0.5))[:, None])
    col = mix(mix(TEAL, DEEP, 0.4), GOLD, smooth(0.0, 0.08, 0.1 - ribs) * 0.85)
    col = mix(col, JADE, smooth(0.02, 0.09, loc[:, 2] + 0.03) * 0.3)
    paint(o, col, np.full(len(P), 0.3))
    return o


def ear_colour(u, v):
    w = np.abs(v - 0.5) * 2
    mid = 1 - smooth(0.0, 0.07, w)
    side = np.abs(np.sin((u * 6 - w * 1.6) * math.pi))
    lines = (1 - smooth(0.04, 0.3, side)) * smooth(0.08, 0.2, u) * (1 - smooth(0.82, 0.97, w))
    base = mix(mix(JADE, MINT, 0.3), PEARL, smooth(0.45, 1.0, u))
    base = mix(base, rgb(244, 170, 150), smooth(0.2, 0.9, 1 - w) * smooth(0.05, 0.5, u) * (1 - smooth(0.55, 0.9, u)) * 0.45)
    base = mix(base, TEAL, np.maximum(mid * smooth(0.0, 0.1, 1 - u), lines * 0.8) * 0.85)
    return base


def build_ear(side, name):
    def relief(u, v):
        w = np.abs(v - 0.5) * 2
        return -0.002 * (1 - smooth(0.0, 0.07, w))
    return sheet_hi(ear_point(side), ear_thick, 220, 140, N + name + "Hi", ear_colour, lambda u, v: np.full_like(u, 0.45), relief)


def eye_paint(o, fr):
    P = verts(o) - np.array(tuple(fr.centre))
    d = P / np.linalg.norm(P, axis=1)[:, None]
    A, X, Y = np.array(tuple(fr.axis)), np.array(tuple(fr.outer)), np.array(tuple(fr.up))
    a = (d * A).sum(1)
    px, py = (d * X).sum(1), (d * Y).sum(1)
    IRIS = 0.76   # sine of the iris's half angle: a big iris, nearly filling the opening
    r = np.sqrt(px ** 2 + py ** 2) / IRIS
    r = np.where(a > 0, r, 3.0)
    azi = np.arctan2(py, px)
    # the white, shadowed under the upper lid
    col = mix(PEARL, rgb(190, 225, 225), smooth(0.1, 0.65, py))
    # the iris: dark at the top, lit from below, the anime way, with fine fibres
    top_dark = smooth(-0.7, 0.8, py / IRIS)
    iris = mix(rgb(44, 226, 180), rgb(4, 82, 104), top_dark)
    fib = np.sin(azi * 34) * 0.5 + 0.5
    iris = mix(iris, rgb(150, 255, 225), fib * smooth(0.45, 0.95, r) * (1 - smooth(0.0, 0.3, top_dark)) * 0.4)
    # a warm ring round the pupil: the spark in its eye
    iris = mix(iris, rgb(255, 196, 96), (1 - smooth(0.6, 0.74, r)) * smooth(0.25, -0.5, py / IRIS) * 0.85)
    col = mix(col, iris, 1 - smooth(0.965, 1.0, r))
    col = mix(col, rgb(2, 34, 50), smooth(0.86, 0.97, r) * (1 - smooth(0.985, 1.03, r)))   # the dark outer ring
    # the pupil, a tall rounded lozenge
    pu = np.sqrt((px / (IRIS * 0.47)) ** 2 + (py / (IRIS * 0.56)) ** 2)
    pu = np.where(a > 0, pu, 3.0)
    col = mix(col, rgb(5, 22, 34), 1 - smooth(0.9, 1.0, pu))
    paint(o, col, np.full(len(P), 0.1))




def build_brow(tree, side, name, fr):
    # a short, tapered tuft above the eye, raised at the outer end; asymmetry belongs to the pose
    pts = []
    for k in range(13):
        t = k / 12
        c = HEAD + V(side * (0.09 + 0.135 * t), 0, 0.205 + 0.016 * t - 0.022 * (2 * t - 1) ** 2)
        pts.append(on_surface(tree, c, V(0, 1, 0), 0.008))
    m = Mesh()
    m.tube(catmull(pts, 4), lambda f: 0.003 + 0.0078 * math.sin(math.pi * min(1.0, f * 0.92 + 0.08)) ** 0.8, sides=10, flat=1.0, plane=V(0, 1, 0))
    o = m.finish(N + name + "Hi", HI)
    paint(o, np.broadcast_to(mix(JADE, TEAL, 0.6), (len(o.data.vertices), 3)), np.full(len(o.data.vertices), 0.5))
    return o


def build_fore(tree):
    """A little forelock that has escaped down the forehead. Its own piece: too thin to survive in the skin."""
    ctrl = [HEAD + V(0.0, -0.06, 0.20)] + [on_surface(tree, HEAD + V(x, 0, z), V(0, 1, 0), 0.006) for x, z in ((0.006, 0.268), (0.02, 0.228), (0.028, 0.178), (0.004, 0.122))]
    path = catmull(ctrl, 8)
    m = Mesh()
    m.tube(path, lambda f: 0.0045 + 0.019 * (1 - f) ** 0.9, sides=10, plane=V(1, 0, 0), flat=1.3)
    o = m.finish(N + "ForeHi", HI)
    P = verts(o)
    f, _ = nearest_on(path, P)
    paint(o, mix(mix(JADE, TEAL, 0.25), mix(MINT, JADE, 0.2), smooth(0.2, 0.95, f)), np.full(len(P), 0.5))
    return o


def face_point(tree, x, z, lift=0.0):
    return on_surface(tree, V(x, 0, z), V(0, 1, 0), lift)


def build_mouth(tree):
    """A sly one-sided smile with one small fang, and hidden in the head, the round mouth it blows through."""
    pts = [face_point(tree, x, z, 0.003) for x, z in ((-0.05, 0.668), (-0.03, 0.657), (-0.004, 0.651), (0.024, 0.654), (0.05, 0.667), (0.068, 0.684), (0.074, 0.697))]
    m = Mesh()
    m.tube(catmull(pts, 5), lambda f: 0.0022 + 0.0038 * math.sin(math.pi * f) ** 0.6, sides=8, plane=V(0, 1, 0))
    smile = m.finish(N + "SmileHi", HI)
    paint(smile, np.broadcast_to(rgb(58, 30, 50), (len(smile.data.vertices), 3)), np.full(len(smile.data.vertices), 0.5))
    # the fang, under the smile's rising end
    a = face_point(tree, 0.036, 0.657, 0.002)
    m = Mesh()
    tip = a + V(0, -0.008, -0.024)
    m.bm.verts.ensure_lookup_table()
    base = [m.bm.verts.new(a + V(math.cos(TAU * k / 8) * 0.009, math.sin(TAU * k / 8) * 0.005, 0)) for k in range(8)]
    t = m.bm.verts.new(tip)
    for k in range(8):
        m.bm.faces.new((base[k], base[(k + 1) % 8], t))
    m.bm.faces.new(list(reversed(base)))
    fang = m.finish(N + "FangHi", HI, smooth_shade=False)
    paint(fang, np.broadcast_to(PEARL, (len(fang.data.vertices), 3)), np.full(len(fang.data.vertices), 0.3))
    # the blowing mouth
    c = face_point(tree, 0.0, 0.672, -0.034)
    m = Mesh()
    ring = [c + V(math.cos(TAU * k / 48) * 0.036, 0, math.sin(TAU * k / 48) * 0.036) for k in range(49)]
    m.tube(ring, lambda f: 0.0135, sides=12, plane=V(0, 1, 0), caps=False)
    bmesh.ops.create_uvsphere(m.bm, u_segments=20, v_segments=12, radius=1.0, matrix=Matrix.Translation(c + V(0, 0.004, 0)) @ Matrix.Diagonal((0.032, 0.008, 0.032, 1)))
    blow = m.finish(N + "BlowHi", HI)
    B = verts(blow)
    inner = np.linalg.norm((B - np.array(tuple(c)))[:, [0, 2]], axis=1) < 0.033
    col = np.where(inner[:, None], rgb(28, 12, 30)[None, :], BLUSH[None, :])
    paint(blow, col, np.full(len(B), 0.45))
    return smile, fang, blow, c


def neck_ring(tree, z=0.552, lift=0.007):
    pts = []
    for k in range(40):
        a = TAU * k / 40
        d = V(math.cos(a), math.sin(a), 0)
        loc, nrm, _, _ = tree.ray_cast(V(0, 0.01, z), d, 0.6)      # from inside: from outside, the back's rays land on the tail
        pts.append((loc + d * lift) if loc else V(0, 0.01, z) + d * 0.16)
    return pts + [pts[0]]


def build_trim(tree):
    """A coral cord round its neck, a jade bead on it with a gold cap, and a little tassel."""
    m = Mesh()
    ring = neck_ring(tree)
    front = min(ring, key=lambda p: p.y)
    m.tube(catmull(ring, 3), lambda f: 0.013, sides=8, plane=V(0, 0, 1), caps=False)
    cord = m.finish(N + "CordHi", HI)
    B = verts(cord)
    braid = np.sin(np.arctan2(B[:, 1] - 0.01, B[:, 0]) * 44) * 0.5 + 0.5
    paint(cord, mix(CORAL, rgb(180, 64, 58), braid * 0.5), np.full(len(B), 0.6))

    bead_c = front + V(0, -0.018, -0.028)
    m = Mesh()
    m.ball(bead_c, (0.042, 0.042, 0.042), 64, 40)
    bead = m.finish(N + "BeadHi", HI)
    B = verts(bead)
    d = (B - np.array(tuple(bead_c))) / 0.042
    col = mix(rgb(30, 190, 150), rgb(8, 92, 92), smooth(-0.8, 0.8, d[:, 2]))
    col = mix(col, rgb(180, 255, 230), np.exp(-(((d[:, 0] + 0.3) / 0.34) ** 2 + ((d[:, 2] - 0.45) / 0.34) ** 2)) * (d[:, 1] < 0) * 0.85)
    paint(bead, col, np.full(len(B), 0.14))

    m = Mesh()
    cap_c = bead_c + V(0, 0, 0.034)
    m.ball(cap_c, (0.024, 0.024, 0.013), 24, 12)
    m.ball(bead_c + V(0, 0, -0.04), (0.018, 0.018, 0.011), 20, 10)
    cap = m.finish(N + "BeadCapHi", HI)
    paint(cap, np.broadcast_to(GOLD, (len(cap.data.vertices), 3)), np.full(len(cap.data.vertices), 0.28))

    # the tassel: three strands, hanging free
    m = Mesh()
    root = bead_c + V(0, 0, -0.045)
    for k, dx in enumerate((-0.012, 0.0, 0.012)):
        pts = catmull([root + V(dx * 0.4, 0, 0), root + V(dx, -0.002, -0.05), root + V(dx * 1.4, 0.004, -0.105)], 6)
        m.tube(pts, lambda f: 0.0085 * (1 - 0.5 * f), sides=6, plane=V(1, 0, 0))
    tassel = m.finish(N + "TasselHi", HI)
    paint(tassel, np.broadcast_to(CORAL, (len(tassel.data.vertices), 3)), np.full(len(tassel.data.vertices), 0.65))
    return cord, bead, cap, tassel, root


def tail_channel(sign):
    """A thin thread of qi running along the curl, on its surface between the ribbons (a glow piece)."""
    pts = []
    samples = 44
    for k in range(samples + 1):
        s = 0.26 + 0.62 * k / samples
        c = curl_point(s)
        tan = (curl_point(min(1.0, s + 0.005)) - curl_point(max(0.0, s - 0.005))).normalized()
        up = (V(1, 0, 0).cross(tan)).normalized()
        side = tan.cross(up).normalized()
        a = (2 * math.pi - s * 26.0 / 2.0) * 1.0 + sign * math.pi / 2 + 1.1
        r = curl_radius(s) * 1.035
        pts.append(c + side * math.cos(a) * r * 0.885 + up * math.sin(a) * r)
    return pts


# ---------- the whole, high-detail ----------


def build_hi():
    pieces = {}
    skin = build_skin()
    paint_skin(skin)
    pieces["Skin"] = skin
    tree = tree_of(skin)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Wing" + tag] = build_wing(side, "Wing" + tag)
        pieces["Nut" + tag] = build_nut(side, "Wing" + tag)
        pieces["Ear" + tag] = build_ear(side, "Ear" + tag)
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, (LID_U, LID_U_FAR, LID_U_GAP), (LID_L, LID_L_FAR, LID_L_GAP), tilt=LID_TILT)
        frames[tag] = fr
        eye = build_eye(fr, tag)
        eye_paint(eye, fr)
        pieces["Eye" + tag] = eye
        lid_skin = mix(MINT, PEARL, 0.95) * 0.92
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, lid_skin, rgb(10, 48, 60))
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, lid_skin, rgb(40, 110, 112))
        pieces["Brow" + tag] = build_brow(tree, side, "Brow" + tag, fr)
    smile, fang, blow, blow_c = build_mouth(tree)
    pieces["Smile"], pieces["Fang"], pieces["Blow"] = smile, fang, blow
    pieces["Fore"] = build_fore(tree)
    cord, bead, cap, tassel, tassel_root = build_trim(tree)
    pieces["Cord"], pieces["Bead"], pieces["Cap"], pieces["Tassel"] = cord, bead, cap, tassel
    return pieces, frames, dict(blow=blow_c, tassel=tassel_root)


def channels(coll):
    m = Mesh()
    for sign in (1, -1):
        m.tube(tail_channel(sign), lambda f: 0.0046 * (1 - 0.4 * f), sides=3, plane=V(1, 0, 0))
    return m.finish(N + "Channels_Glow_1eebb4", coll, smooth_shade=False)


# ---------- review ----------


VIEWS = [(0, -1, 0.08), (0.6, -0.8, 0.2), (1, 0, 0.1), (0, 1, 0.15), (-0.6, 0.75, 0.45), (0, -0.25, 1), (0, -1, 0.02, 2.0, (0, -0.1, 0.8)), (0.75, -0.7, 0.12, 2.0, (0, -0.1, 0.8))]


# ---------- the game mesh ----------
TARGET = {"NutL": 120, "NutR": 120, "BrowL": 56, "BrowR": 56, "Smile": 100, "Fang": 9, "Blow": 110, "Cord": 150, "Bead": 190, "Cap": 44, "Tassel": 66, "Fore": 90}
SKIN_QUADS = 2350
SCALES = {"EyeL": 3.0, "EyeR": 3.0, "LidUL": 1.6, "LidUR": 1.6, "LidLL": 1.6, "LidLR": 1.6, "Blow": 1.6, "Bead": 1.6, "Smile": 3.0, "Fang": 3.0, "WingL": 1.6, "WingR": 1.6, "EarL": 1.6, "EarR": 1.6}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for key, target in TARGET.items():
        lows[key] = decimated(pieces[key], N + key + "Low", target)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Wing" + tag] = low_sheet(wing_point(side), wing_thick, 13, 5, N + "Wing" + tag + "Low")
        lows["Ear" + tag] = low_sheet(ear_point(side), ear_thick, 9, 4, N + "Ear" + tag + "Low")
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low")
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    for o in lows.values():
        apply_mods(o, [("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
    return lows


# ---------- the skeleton ----------
TAIL_S = (0.02, 0.15, 0.29, 0.43, 0.57, 0.71, 0.85)


def skeleton(frames, marks):
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, 0.02, 0.50), "Root"), ("Head", V(0, 0.01, 0.585), "Body")]
    crest = CREST_MAIN
    bones += [("Crest1", crest[int(len(crest) * 0.12)], "Head"), ("Crest2", crest[int(len(crest) * 0.55)], "Crest1")]
    parent = "Body"
    for k, s in enumerate(TAIL_S):
        bones.append(("Tail%d" % (k + 1), curl_point(s), parent))
        parent = "Tail%d" % (k + 1)
    bones.append(("TailTip", curl_point(1.0), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Ear" + tag, mir(EAR_ROOT, side) - V(side * 0.03, 0, 0.02), "Head"), ("Eye" + tag, fr.centre.copy(), "Head"),
                  ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"),
                  ("Brow" + tag, HEAD + V(side * 0.15, -0.28, 0.21), "Head"), ("Cheek" + tag, HEAD + V(side * 0.21, -0.2, -0.12), "Head")]
        a, b = mir(ARM_ROOT, side), mir(ARM_TIP, side)
        bones += [("Arm" + tag + "1", a, "Body"), ("Arm" + tag + "2", a.lerp(b, 0.55), "Arm" + tag + "1")]
        wp = wing_point(side)
        bones += [("Wing" + tag, mir(WING_ROOT, side), "Body"), ("WingMid" + tag, Vector(wp(0.42, 0.25)), "Wing" + tag), ("WingTip" + tag, Vector(wp(0.985, 0.25)), "WingMid" + tag)]
    bones += [("Smile", marks["blow"].copy(), "Head"), ("Blow", marks["blow"].copy(), "Head"), ("Tassel", marks["tassel"].copy(), "Body")]
    return armature(bones)


def tail_weights(s):
    """Bones and shares along the curl at s."""
    knots = TAIL_S
    if s <= knots[0]:
        return {"Tail1": 1.0}
    if s >= knots[-1]:
        f = float(smooth(knots[-1], 1.0, s))
        return {"Tail%d" % len(knots): 1 - f, "TailTip": f}
    for k in range(len(knots) - 1):
        if s <= knots[k + 1]:
            f = float(smooth(knots[k], knots[k + 1], s))
            return {"Tail%d" % (k + 1): 1 - f, "Tail%d" % (k + 2): f}


def skin_weights(o):
    P = verts(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    s, d = nearest_on(CURL_S, P)
    tail = np.where(d < np.interp(s, [0, 1], [0.21, 0.06]), 1.0, 0.0) * smooth(0.0, 0.1, s) * (z < 0.60) * (y > 0.05)
    tail = np.where((s < 0.1) & (y < 0.2) & (z > 0.40), 0, tail)
    head = smooth(0.545, 0.60, z)
    fm, dm = nearest_on(CREST_MAIN, P)
    crest = (1 - smooth(0.05, 0.095, dm)) * smooth(0.0, 0.06, z - 1.07)
    arm = {}
    for side, tag in ((1, "L"), (-1, "R")):
        a, b = mir(ARM_ROOT, side), mir(ARM_TIP, side)
        A = np.array(tuple(a))
        Dv = np.array(tuple((b - a).normalized()))
        L = (b - a).length
        t = ((P - A) * Dv).sum(1) / L
        perp = np.linalg.norm((P - A) - Dv[None, :] * (t * L)[:, None], axis=1)
        arm[tag] = (t, ((perp < 0.15) & (t > -0.1) & (t < 1.7) & (z < 0.56)) * smooth(0.0, 0.2, t))
    weights = []
    for i in range(len(P)):
        w = {}
        rest = 1.0
        for tag in ("L", "R"):
            t, m = arm[tag][0][i], arm[tag][1][i]
            if m > 0:
                f = float(smooth(0.3, 0.7, t))
                w["Arm" + tag + "1"] = m * (1 - f)
                w["Arm" + tag + "2"] = m * f
                rest -= m
        if tail[i] > 0 and rest > 0:
            for bone, v in tail_weights(float(s[i])).items():
                w[bone] = w.get(bone, 0) + v * tail[i] * rest
            rest -= tail[i] * rest
        if rest > 0.001:
            h = float(head[i]) * rest
            if h > 0:
                c = float(crest[i])
                if c > 0:
                    f = float(smooth(0.35, 0.6, fm[i]))
                    w["Crest1"] = c * (1 - f) * h
                    w["Crest2"] = c * f * h
                    h *= 1 - c
                for side, tag in ((1, "L"), (-1, "R")):
                    ch = math.exp(-(((x[i] - side * 0.21) / 0.1) ** 2 + ((z[i] - 0.74) / 0.075) ** 2 + ((y[i] + 0.22) / 0.13) ** 2)) * 0.8
                    if ch > 0.02:
                        w["Cheek" + tag] = ch * h
                        h *= 1 - ch
                w["Head"] = w.get("Head", 0) + h
            b = rest * (1 - float(head[i]))
            if b > 0:
                w["Body"] = w.get("Body", 0) + b
        weights.append(w)
    return weights


def bind_all(lows, rig, glint, chan, frames):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    for side, tag in ((1, "L"), (-1, "R")):
        P = verts(lows["Wing" + tag])
        u = (P - np.array(tuple(mir(WING_ROOT, side)))).dot(np.array(tuple(mir(WING_U, side)))) / WING_L
        flex, tip = smooth(0.3, 0.6, u), smooth(0.86, 1.0, u)
        weigh(lows["Wing" + tag], [{"Wing" + tag: float(1 - f), "WingMid" + tag: float(f * (1 - g)), "WingTip" + tag: float(f * g)} for f, g in zip(flex, tip)])
    for key, bone in (("NutL", "WingL"), ("NutR", "WingR"), ("EarL", "EarL"), ("EarR", "EarR"), ("EyeL", "EyeL"), ("EyeR", "EyeR"),
                      ("LidUL", "LidUL"), ("LidUR", "LidUR"), ("LidLL", "LidLL"), ("LidLR", "LidLR"), ("BrowL", "BrowL"), ("BrowR", "BrowR"), ("Smile", "Smile"), ("Fang", "Smile"),
                      ("Blow", "Blow"), ("Fore", "Head"), ("Cord", "Body"), ("Bead", "Body"), ("Cap", "Body"), ("Tassel", "Tassel")):
        rigid(lows[key], bone)
    # the glints: each on its own eye
    P = verts(glint)
    g_l, g_r = glint.vertex_groups.new(name="EyeL"), glint.vertex_groups.new(name="EyeR")
    for i, p in enumerate(P):
        (g_l if p[0] > 0 else g_r).add([i], 1.0, "REPLACE")
    P = verts(chan)
    s, _ = nearest_on(CURL_S, P)
    weigh(chan, [tail_weights(float(v)) for v in s])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, (body, glint, chan))
    return body


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    blow = {"Smile": ((1, 0, 0), 0, (0, 0.03, 0)), "Blow": ((1, 0, 0), 0, (0, -0.036, 0)), "CheekL": ((1, 0, 0), 0, (0.03, -0.024, 0)), "CheekR": ((1, 0, 0), 0, (-0.03, -0.024, 0))}
    tail = {"Tail%d" % k: ((1, 0, 0), -24, (0, 0, 0)) for k in range(1, 8)}      # the curl opening out
    tug = {"ArmL1": ((1, 0, 0), -62, (0, 0, 0)), "ArmL2": ((1, 0, 0), -30, (0, 0, 0))}
    wings = {"WingL": ((0, 1, 0), 34, (0, 0, 0)), "WingR": ((0, 1, 0), -34, (0, 0, 0))}
    look = {"EyeL": ((0, 0, 1), 16, (0, 0, 0)), "EyeR": ((0, 0, 1), 16, (0, 0, 0))}
    return {"Blink": lids(BLINK_U, BLINK_L), "Sly": lids(16, 7), "Blow": blow, "Look": look, "TailOpen": tail, "Tug": tug, "WingsUp": wings}


if __name__ == "__main__":
    pieces, frames, marks = build_hi()
    mat = hi_material()
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    glow_mat = glow_material()
    gl = glints(frames, HI, "Glints_Glow_ffffff")
    ch = channels(HI)
    gl.data.materials.append(glow_mat)
    ch.data.materials.append(glow_mat)
    stage_setup()
    if STAGE == "paint":
        shots(os.path.join(REVIEW, "paint"), VIEWS)
    else:
        lows = build_low(pieces, frames)
        unwrap(lows, [(lambda p: p.center.z > 0.58 and p.center.y < 0.1, 1.5), (None, 1.0)], SCALES)
        bake_all(lows, pieces, mat, fill=(0.6, 0.85, 0.78, 1))
        tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
        print("TRIS", sum(tris.values()), tris, flush=True)
        # the glow pieces move to the game collection
        for o in (gl, ch):
            HI.objects.unlink(o)
            GAME.objects.link(o)
        rig = skeleton(frames, marks)
        body = bind_all(lows, rig, gl, ch, frames)
        # only the game mesh renders from here on
        for o in list(HI.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
        mw = 0
        for v in body.data.vertices:
            mw = max(mw, len(v.groups))
        print("MAX INFLUENCES", mw, flush=True)
        for tag, fr in frames.items():
            print("EYE", tag, "centre", tuple(round(v, 4) for v in fr.centre), "hinge", tuple(round(v, 4) for v in fr.hinge), flush=True)
        # the curl must stand clear of the body
        print("CURL GAP", round(min((curl_point(k / 100) - V(0, y0, z0)).length - curl_radius(k / 100) for k in range(35, 101) for y0, z0 in ((0.03, 0.40), (0.06, 0.32))) - 0.17, 3), flush=True)
        scene.cycles.samples = 28
        pose(rig, {})
        shots(os.path.join(REVIEW, "game"), VIEWS)
        lib = pose_library(frames)
        pose_views = []
        close = (0, -1, 0.02, 2.0, (0, -0.1, 0.8))
        for name, view in (("Blink", close), ("Sly", close), ("Blow", close), ("Look", close), ("TailOpen", (1, 0, 0.1)), ("Tug", (0.75, -0.65, 0.1)), ("WingsUp", (0, 1, 0.15))):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "pose" + name), [view])
        pose(rig, {})
        path = save_all((0.6, -0.8, 0.2))      # first: the export takes the glow pieces' colours off
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, (gl, ch)), flush=True)
    print("DONE", flush=True)

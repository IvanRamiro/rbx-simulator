"""The Echo Bat (Common, Sound; Ancient Grove Egg): "It speaks only in sounds it has already heard. Ask it a question and you may hear a voice from a
hundred years ago."

A new creature, in a design language of its own: rings that keep sound. The growth rings of the grove's oldest trees and the grooves of a record are the
same idea, a year or a voice kept as a ring, and this bat is made of them. A small, plush fruit bat, round in head and body: warm cocoa fur, a fawn face
and a pale chest, the chest's round patch ringed twice like a ripple. Its ears are its own: two big calla-lily trumpets rising from its crown, each a
funnel flaring to a wide mouth that faces forward and out, its rim drawn up behind into a soft point like a bat's ear. Outside they are velvet plum;
inside, ivory, cut with fine concentric grooves, and in three of the grooves glow the sounds it has kept, sea-glass teal. Big glossy dark eyes with a
teal ring of eyeshine; a short soft muzzle, a round button nose, a small open mouth (it is always halfway through repeating something). Plum wings held
half open, each a membrane on three long fingers and a thumb claw, its trailing edge scalloped between them, faint ripples of an echo spreading out across
it from the wrist. Small dark legs tucked under, toes hooked for hanging.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/echo_bat.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: the game mesh and skeleton, posed and checked, in clay. all: also the
unwrap, bake, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It hovers: its middle about 0.45 m up. The maps go to
assets/pets/AncientGroveEgg/.

What touches what: head, body, muzzle, cheeks, nose and the shoulder mounds are one fused skin; the eyes sit in their sockets under their lids; each ear
is its own piece, its root buried in its crown; each wing (upper arm, forearm, wrist, thumb and three fingers, and the membrane between them) is set into
its shoulder mound, the membrane's root edge buried in its flank and its trailing corner meeting the knee; the legs root under its belly; the glowing
rings lie in the grooves inside the ears, half sunk; the catch-lights lie on the eyes.
"""
import math
import os
import re
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
PET = "EchoBat"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AncientGroveEgg")

# ---------- colours: cocoa fur, fawn and cream, plum velvet, ivory, and the teal of a kept sound ----------
COCOA, COCOA_DEEP, COCOA_WARM = rgb(98, 66, 58), rgb(58, 38, 36), rgb(136, 92, 70)
FAWN, CREAM = rgb(218, 174, 136), rgb(242, 222, 188)
PLUM, PLUM_DEEP, MAUVE = rgb(120, 70, 94), rgb(74, 42, 60), rgb(178, 124, 152)
IVORY, GROOVE = rgb(246, 234, 214), rgb(178, 138, 128)
NOSE, MOUTH, TONGUE = rgb(86, 50, 56), rgb(64, 28, 38), rgb(226, 128, 142)
BLUSH, LASH, CLAW = rgb(232, 148, 138), rgb(40, 26, 26), rgb(238, 228, 208)
ECHO_HEX, GLINT_HEX = "1fe0c6", "ffffff"

# ---------- the frame of it ----------
BODY = (V(0, 0.028, 0.41), (0.118, 0.11, 0.14))
PEAR = 0.16                                          # its body fuller low than high (two balls for it read as a snowman)
HEAD, HEAD_R = V(0, -0.04, 0.6), (0.142, 0.13, 0.124)            # bigger than its body: a round, plush head
MUZZLE = (V(0, -0.15, 0.565), (0.05, 0.036, 0.034))      # short and soft (fuller, it read as a snout)
CHEEK = (V(0.066, -0.122, 0.556), (0.052, 0.046, 0.042))
NOSE_C = (V(0, -0.183, 0.58), (0.013, 0.008, 0.009))             # a small round button
EYE_R = 0.042
EYE_C = V(0.062, -0.138, 0.622)
EYE_AXIS = V(0.4, -0.9, 0.16).normalized()           # big and set forward
LID_UP, LID_LOW = (56.0, 118.0, 0.0026), (-46.0, -126.0, 0.0022)     # wide open: it is listening
LID_TILT = -7.0                                      # their outer ends a little low: a soft, sweet look (raised, it read as a scowl)
BLINK_U, BLINK_L = 76.0, 32.0                       # (the two add past the 102 degrees between the lids' edges: at 64 + 22 a band of eye showed)
IRIS, PUPIL, SHINE = 0.9, 0.5, (0.7, 0.8)            # (on the eye's face, 1 its rim): the iris, its pupil, the teal ring of eyeshine
MOUTH_C = V(0, -0.176, 0.539)                        # its small open mouth, under its nose
# an ear (left): from deep in its crown, up and out, flaring into a trumpet whose mouth faces forward, out and up
EAR = [V(0.05, -0.03, 0.63), V(0.075, -0.04, 0.71), V(0.11, -0.062, 0.785), V(0.15, -0.1, 0.83)]      # its root deep: the ear a funnel out of its crown     # (longer, on a thin stem, it read as a stalk)
EAR_STEM, EAR_BELL = 0.034, 0.088                   # the stem's radius and the mouth's
EAR_FLARE = 0.16                                    # where along it the trumpet starts to flare
EAR_CAVE = 0.42                                     # where its hollow begins
EAR_HOOD = 0.45                                      # how much further its rim runs on the side of its point (a share of its length)
EAR_TIP_DIR = V(0.35, 0.55, 1.0)                    # (left) the way its rim's point lies: up and back
EAR_WALL = (0.009, 0.0055)                          # its wall's thickness deep in it, and at its lip
GROOVES = (0.52, 0.62, 0.72, 0.82, 0.91)             # the rings cut inside its trumpet (along it)
GLOW_GROOVES = (0.62, 0.76, 0.9)                    # the three that glow
# a wing (left): shoulder, elbow, wrist; a thumb; three fingers from the wrist, each wrist, knuckle, tip; the membrane's corner at its knee
SHOULDER, ELBOW, WRIST = V(0.098, 0.05, 0.47), V(0.185, 0.115, 0.545), V(0.275, 0.05, 0.615)
THUMB = [V(0.275, 0.05, 0.615), V(0.281, 0.03, 0.633), V(0.279, 0.016, 0.637)]
FINGERS = [[V(0.275, 0.05, 0.615), V(0.36, 0.075, 0.64), V(0.445, 0.11, 0.6)],
           [V(0.275, 0.05, 0.615), V(0.345, 0.12, 0.55), V(0.405, 0.185, 0.47)],
           [V(0.275, 0.05, 0.615), V(0.31, 0.135, 0.5), V(0.33, 0.19, 0.39)]]
SCALLOP = (0.2, 0.2, 0.16)                          # how deep the trailing edge dips between finger tips (and from the last to its knee)
MEMBRANE = 0.0032
# a leg (left): hip (inside its belly), knee, ankle; three hooked toes
LEG = [V(0.052, 0.07, 0.3), V(0.088, 0.112, 0.252), V(0.078, 0.094, 0.204)]
KNEE = LEG[1]


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def arc_lengths(path):
    a = np.array([tuple(p) for p in path])
    return np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])


def resample(path, n):
    """n + 1 points evenly by arc length."""
    L = arc_lengths(path)
    a = np.array([tuple(p) for p in path])
    out = []
    for t in np.linspace(0, L[-1], n + 1):
        i = min(int(np.searchsorted(L, t, side="right")) - 1, len(a) - 2)
        f = (t - L[i]) / max(L[i + 1] - L[i], 1e-9)
        out.append(V(*(a[i] * (1 - f) + a[i + 1] * f)))
    return out


def rm_frames(path, first_side=None):
    """Frames along a path that never twist (each turned on from the last by the least rotation)."""
    out = []
    tan = (path[1] - path[0]).normalized()
    side = first_side or (V(1, 0, 0) - tan * tan.x)
    if side.length < 1e-4:
        side = tan.orthogonal()
    side = (side - tan * side.dot(tan)).normalized()
    for i in range(len(path)):
        t2 = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        if i > 0:
            side = tan.rotation_difference(t2) @ side
        side = (side - t2 * side.dot(t2)).normalized()
        tan = t2
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def ell_dist(P, c, r):
    """Per point: its distance from an ellipsoid's middle in the ellipsoid's own units (1 on its surface)."""
    return np.linalg.norm((P - np.array(tuple(c))) / np.array(r), axis=1)


# ---------- the ears: a trumpet turned on its own curved line ----------
EAR_PTS = resample(catmull(EAR, 16), 240)
EAR_LEN = float(arc_lengths(EAR_PTS)[-1])
EAR_FR = rm_frames(EAR_PTS, V(0, 0, 1))


def ear_line(side, f):
    """Where along its ear's middle line f lies (past 1 it runs straight on), and the frame there (tangent, side, up), for the left ear mirrored."""
    k = f * (len(EAR_PTS) - 1)
    if k >= len(EAR_PTS) - 1:
        tan, sd, up = EAR_FR[-1]
        c = EAR_PTS[-1] + tan * ((f - 1) * EAR_LEN)
    else:
        i = max(0, int(k))
        c = EAR_PTS[i].lerp(EAR_PTS[i + 1], k - i)
        tan, sd, up = EAR_FR[i]
    if side < 0:
        return mir(c, -1), mir(tan, -1), mir(sd, -1), mir(up, -1)
    return c, tan, sd, up


def ear_radius(f):
    """The trumpet's outer radius: a stem rising out of its crown, then flaring wide (and past its mouth, on its point's side, widening a little more)."""
    if f < EAR_FLARE:
        return EAR_STEM + 0.016 * (1 - f / EAR_FLARE) ** 2          # wide where it springs from its crown
    if f <= 1:
        return EAR_STEM + (EAR_BELL - EAR_STEM) * ((f - EAR_FLARE) / (1 - EAR_FLARE)) ** 1.6
    return EAR_BELL + 0.06 * (f - 1)


def ear_wall(f):
    return EAR_WALL[0] + (EAR_WALL[1] - EAR_WALL[0]) * smooth(EAR_CAVE, 1.0, f)


def tip_angle():
    """Round its ear's mouth, the angle (in its frame) its rim's point lies at."""
    c, tan, sd, up = ear_line(1, 1.0)
    d = EAR_TIP_DIR.normalized()
    return math.atan2(d.dot(up), d.dot(sd))


TIP_A = tip_angle()


def ear_end(theta):
    """How far along it its rim reaches at theta round it: drawn out to a soft point on one side."""
    return 1.0 + EAR_HOOD * max(0.0, math.cos(theta - TIP_A)) ** 2.5


def ear_profile(n_out, n_lip, n_in, n_cap):
    """The trumpet's section, as (s, rho, inner, depth) from its root's pole round to its hollow's floor: s 0..1 along the stretch of it that bends with
    theta (past EAR_FLARE it is stretched to each theta's own rim), rho its radius, inner whether it is on the hollow's side, depth the groove depth to
    apply. Returned as rows (f(theta), rho(theta)) callables."""
    rows = []
    # its root, a rounded end deep in its crown
    for k in range(1, n_cap + 1):
        a = math.pi / 2 * k / n_cap
        rows.append(("out", -0.04 * math.cos(a), math.sin(a)))
    for k in range(1, n_out + 1):
        rows.append(("out", k / n_out, 1.0))
    for k in range(1, n_lip):
        rows.append(("lip", k / n_lip, 0))
    for k in range(n_in, -1, -1):
        rows.append(("in", k / n_in, 0))
    for k in range(1, n_cap):
        rows.append(("floor", k / n_cap, 0))
    return rows


def ear_f(s, theta):
    """Along its ear for s in 0..1 at theta: unstretched up to where it flares, then out to that theta's rim."""
    if s <= EAR_FLARE:
        return s
    return EAR_FLARE + (s - EAR_FLARE) / (1 - EAR_FLARE) * (ear_end(theta) - EAR_FLARE)


def ear_section(kind, a, b, theta):
    """(f, rho) of one row of its section at theta."""
    if kind == "out":
        if a < 0:
            return a, ear_radius(0.0) * b
        f = ear_f(a, theta)
        lip_flare = 0.004 * smooth(0.9, 1.0, a)                      # its lip rolls out a little
        return f, ear_radius(f) + lip_flare
    if kind == "lip":
        f1 = ear_f(1.0, theta)
        w = ear_wall(f1)
        r_out, r_in = ear_radius(f1) + 0.004, ear_radius(f1) - w
        half, mid = (r_out - r_in) / 2, (r_out + r_in) / 2
        ang = math.pi * a                                              # a round lip, from the outer face over to the inner
        return f1 + math.sin(ang) * half * 0.8 / EAR_LEN, mid + math.cos(ang) * half
    if kind == "in":
        s = EAR_CAVE + (1.0 - EAR_CAVE) * a
        f = ear_f(s, theta) if s > EAR_FLARE else s
        return f, max(ear_radius(f) - ear_wall(f), 0.002)
    # the hollow's floor: a shallow dish closing to its middle
    f0 = EAR_CAVE
    r0 = ear_radius(f0) - ear_wall(f0)
    return f0 - 0.02 * math.sin(math.pi / 2 * a), r0 * math.cos(math.pi / 2 * a)


def build_ear(side, name, coll, nt=64, res=(40, 6, 40, 8), grooves=True):
    """One ear: its section turned round its middle line. Tagged per vertex: inner (1 on the hollow's side), f (along it)."""
    rows = ear_profile(*res)
    m = Mesh()
    bm = m.bm
    lay_in = bm.verts.layers.float.new("inner")
    lay_f = bm.verts.layers.float.new("ef")
    thetas = [TAU * k / nt for k in range(nt)]
    c0, tan0, _, _ = ear_line(side, 0.0)
    root = bm.verts.new(c0 + tan0 * (-0.04 * EAR_LEN))
    root[lay_in], root[lay_f] = 0.0, -0.04
    rings = []
    for kind, a, b in rows:
        ring = []
        for th in thetas:
            f, rho = ear_section(kind, a, b, th)
            if kind == "in" and grooves:
                for g in GROOVES:
                    rho += 0.0016 * math.exp(-((f - g) / 0.007) ** 2)          # a groove: a fine ring cut into the wall
            c, tan, sd, up = ear_line(side, f)
            v = bm.verts.new(c + (sd * math.cos(th) + up * math.sin(th)) * rho)      # (the right ear's frame is mirrored: so is it)
            v[lay_in] = 1.0 if kind in ("in", "floor") else (0.5 if kind == "lip" else 0.0)
            v[lay_f] = f
            ring.append(v)
        rings.append(ring)
    floor_c, ftan, _, _ = ear_line(side, EAR_CAVE - 0.02)
    floor = bm.verts.new(floor_c)
    floor[lay_in], floor[lay_f] = 1.0, EAR_CAVE - 0.02
    for k in range(nt):
        bm.faces.new((root, rings[0][(k + 1) % nt], rings[0][k]))
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    for k in range(nt):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % nt], floor))
    return m.finish(name, coll)


def build_echo_rings(coll, sides=10, nt=72, lift=0.0012):
    """The sounds it keeps: a glowing ring lying in each of three grooves inside each ear, half sunk in its groove."""
    m = Mesh()
    for side in (1, -1):
        for g in GLOW_GROOVES:
            rho = ear_radius(g) - ear_wall(g) + lift          # + into its groove
            c, tan, sd, up = ear_line(side, g)
            pts = [c + (sd * math.cos(TAU * k / nt) + up * math.sin(TAU * k / nt)) * rho for k in range(nt)]
            ring_tube(m, pts, 0.0022, sides)
    return m.finish(N + "Echo_Glow_" + ECHO_HEX, coll)


def ring_tube(m, pts, r, sides):
    """A closed tube round a loop of points."""
    n = len(pts)
    rings = []
    for i, p in enumerate(pts):
        tan = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        out = (p - sum(pts, V(0, 0, 0)) / n)
        out = (out - tan * out.dot(tan)).normalized()
        up = tan.cross(out).normalized()
        rings.append([m.bm.verts.new(p + (out * math.cos(TAU * k / sides) + up * math.sin(TAU * k / sides)) * r) for k in range(sides)])
    for i in range(n):
        for k in range(sides):
            k2 = (k + 1) % sides
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[(i + 1) % n][k2], rings[(i + 1) % n][k]))


# ---------- the wings: a membrane on a fan of spokes from the wrist ----------
def wing_spokes(side):
    """The spokes the membrane hangs on, from its wrist: the three fingers, the line to its knee, and back along the arm to the shoulder."""
    fingers = [resample(catmull([mir(p, side) for p in f], 12), 60) for f in FINGERS]
    w, k = mir(WRIST, side), mir(KNEE, side)
    to_knee = resample(catmull([w, w.lerp(k, 0.5) + V(0, 0.035, 0), k], 12), 60)
    arm = resample(catmull([w, w.lerp(mir(ELBOW, side), 0.5), mir(ELBOW, side), mir(ELBOW, side).lerp(mir(SHOULDER, side), 0.5), mir(SHOULDER, side)], 6), 60)
    return fingers + [to_knee, arm]


def path_at(path, f):
    k = min(max(f, 0.0), 1.0) * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def wing_edge(side, seg, t, spokes):
    """The membrane's outer edge between spoke seg and the next, at t across: scalloped toward the wrist between finger tips; buried in its flank
    from its knee to its shoulder."""
    a, b = spokes[seg][-1], spokes[seg + 1][-1]
    lin = a.lerp(b, t)
    if seg < 3:
        return lin + (mir(WRIST, side) - lin) * (SCALLOP[seg] * math.sin(math.pi * t))
    inward = V(lin.x * 0.82, lin.y, lin.z)                # the root edge sunk into its flank
    return lin.lerp(inward, math.sin(math.pi * t))


V0 = 0.05                                             # the membrane starts this far out along its spokes (the wrist's knuckle covers the rest)


def wing_uvt(u, v):
    seg = min(int(u * 4), 3)
    return seg, u * 4 - seg, V0 + (1 - V0) * v


def wing_point(side, spokes, nrm):
    def point(u, v):
        seg, t, vv = wing_uvt(u, v)
        sa, sb = path_at(spokes[seg], vv), path_at(spokes[seg + 1], vv)
        lin = sa.lerp(sb, t)
        end = spokes[seg][-1].lerp(spokes[seg + 1][-1], t)
        p = lin + (wing_edge(side, seg, t, spokes) - end) * (vv * vv)
        billow = (0.012 if seg < 3 else 0.006) * math.sin(math.pi * t) * math.sin(math.pi * min(1.0, vv * 1.1))
        return tuple(p + nrm * billow)
    return point


def wing_normal(side):
    """The way the membrane's back faces (back and a little up)."""
    w = mir(WRIST, side)
    n = (mir(FINGERS[0][-1], side) - w).cross(mir(KNEE, side) - w).normalized()
    return n if n.y > 0 else -n


def build_membrane(side, nu_per, nv, coll, name):
    """One membrane, as a thin closed plate. Its vertices in pairs (top, bottom), point by point; returns the object and each pair's (seg, t, v)."""
    spokes = wing_spokes(side)
    m = Mesh()
    m.sheet(wing_point(side, spokes, wing_normal(side)), lambda u, v: MEMBRANE, nu_per * 4, nv)
    o = m.finish(name, coll)
    nu = nu_per * 4
    tags = []
    for i in range(nu + 1):
        for j in range(nv + 1):
            tags += [wing_uvt(i / nu, j / nv)] * 2
    return o, tags


def bone_pts(side):
    """Each of a wing's bones as a path: upper arm, forearm, thumb, three fingers."""
    s, e, w = mir(SHOULDER, side), mir(ELBOW, side), mir(WRIST, side)
    inner = s + (s - e).normalized() * 0.02               # rooted deep in its shoulder mound
    return {"Upper": [inner.lerp(e, k / 10) for k in range(11)], "Fore": [e.lerp(w, k / 10) for k in range(11)],
            "Thumb": catmull([mir(p, side) for p in THUMB], 6), "F1": catmull([mir(p, side) for p in FINGERS[0]], 10),
            "F2": catmull([mir(p, side) for p in FINGERS[1]], 10), "F3": catmull([mir(p, side) for p in FINGERS[2]], 10)}


BONE_R = {"Upper": (0.022, 0.0135), "Fore": (0.011, 0.0085), "Thumb": (0.0062, 0.0012), "F1": (0.0068, 0.0034), "F2": (0.0064, 0.0032), "F3": (0.006, 0.003)}


def build_arms(coll, sides=16, low=False):
    """Both wings' bones: tubes, a knob at the elbow and the wrist and each knuckle. Tagged per vertex: side (+1, -1) and part (index in BONE_R)."""
    m = Mesh()
    bm = m.bm
    lay_side = bm.verts.layers.int.new("side")
    lay_part = bm.verts.layers.int.new("part")
    keys = list(BONE_R)
    for side in (1, -1):
        paths = bone_pts(side)
        for key, pts in paths.items():
            before = set(bm.verts)
            r0, r1 = BONE_R[key]
            if low:
                pts = resample(pts, 4 if key in ("Upper", "Fore") else 3)
            m.tube(pts, lambda f, r0=r0, r1=r1: r0 + (r1 - r0) * f, sides=sides)
            if key == "Upper":
                m.ball(mir(ELBOW, side), (0.0135,) * 3, sides, max(6, sides // 2))
            if key == "Fore":
                m.ball(mir(WRIST, side), (0.0128,) * 3, sides, max(6, sides // 2))
            if key in ("F1", "F2", "F3"):
                m.ball(mir(FINGERS[int(key[1]) - 1][1], side), (r0 * 0.95,) * 3, max(8, sides // 2), max(6, sides // 3))
            for v in bm.verts:
                if v not in before:
                    v[lay_side] = side
                    v[lay_part] = keys.index(key)
    return m.finish(N + "Arms" + ("Low" if low else "Hi"), coll)


def build_legs(coll, sides=14, low=False):
    """Small dark legs tucked under its belly, three hooked toes each. Tagged: side."""
    m = Mesh()
    bm = m.bm
    lay = bm.verts.layers.int.new("side")
    for side in (1, -1):
        before = set(bm.verts)
        p = [mir(q, side) for q in LEG]
        path = catmull(p, 3 if low else 10)
        m.tube(path, lambda f: 0.0115 - 0.003 * f, sides=sides)
        m.ball(p[-1], (0.0125, 0.0135, 0.009), sides, max(6, sides // 2))      # its little foot
        for k in (-1, 0, 1):
            root = p[-1] + V(side * 0.006 * k, -0.006, -0.004)
            toe = [root, root + V(side * 0.003 * k, -0.01, -0.006), root + V(side * 0.004 * k, -0.012, 0.002)]     # hooked forward and up
            m.tube(catmull(toe, 2 if low else 5), lambda f: 0.0042 * (1 - 0.75 * f), sides=max(6, sides // 2))
        for v in bm.verts:
            if v not in before:
                v[lay] = side
    return m.finish(N + "Legs" + ("Low" if low else "Hi"), coll)


# ---------- the skin ----------
SWELLS = [(V(0, -0.168, 0.562), 0.017, (0.04, 0.03, 0.03)),            # its muzzle: centre (on the head's surface), height, reach (x, y, z)
          (V(0.078, -0.112, 0.548), 0.016, (0.045, 0.045, 0.036)), (V(-0.078, -0.112, 0.548), 0.016, (0.045, 0.045, 0.036)),     # its cheeks
          (V(0, -0.168, 0.505), 0.008, (0.04, 0.04, 0.026))]          # its chin, soft under its mouth


def head_with_face():
    """Its head, the muzzle, cheeks and chin raised out of it as smooth swells, and the nose a small round button on the muzzle (balls fused onto a
    head creased into a pug's face)."""
    m = Mesh()
    m.ball(HEAD, HEAD_R, 192, 128)
    o = m.finish(N + "HeadHi", HI)
    P, Nn = verts(o), normals(o)
    h = np.zeros(len(P))
    for c, amp, reach in SWELLS:
        h += amp * np.exp(-np.sum(((P - np.array(tuple(c))) / np.array(reach)) ** 2, axis=1))
    P = P + Nn * h[:, None]
    nose = 1 - smooth(0.0, 1.0, ell_dist(P, NOSE_C[0], (NOSE_C[1][0] * 1.6, NOSE_C[1][1] * 3, NOSE_C[1][2] * 1.6)))
    P = P + Nn * (0.0075 * np.sqrt(np.clip(nose * (2 - nose), 0, 1)))[:, None]
    set_verts(o, P)
    return o


def pear_body():
    m = Mesh()
    m.ball(BODY[0], BODY[1], 128, 96)
    o = m.finish(N + "BodyHi", HI)
    P = verts(o)
    c = np.array(tuple(BODY[0]))
    k = 1 - PEAR * (P[:, 2] - c[2]) / BODY[1][2]
    P[:, :2] = c[:2] + (P[:, :2] - c[:2]) * k[:, None]
    set_verts(o, P)
    return o


def build_skin():
    m = Mesh()
    for side in (1, -1):
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.012, (EYE_R * 1.06,) * 3, 40, 28)      # the socket's rim (further out, it read as goggles)
        m.ball(mir(SHOULDER + V(0.004, 0.008, 0.006), side), (0.032, 0.034, 0.036), 32, 20)      # the shoulder its wing springs from
        c, tan, _, _ = ear_line(side, 0.2)
        m.ball(c - tan * 0.012, (0.034, 0.03, 0.026), 32, 20)          # the soft base its ear springs from
    o = m.finish(N + "SkinHi", HI)
    for part in (head_with_face(), pear_body()):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.from_mesh(part.data)
        bm.to_mesh(o.data)
        bm.free()
        bpy.data.objects.remove(part, do_unlink=True)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    fill_creases(o)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def fill_creases(o, rounds=4, reach=40):
    """Where two of its swells meet, a crease: the skin is smoothed hard (a copy, reach iterations), and wherever the smoothed skin stands out past the
    real one (a dip: concave) the real skin is drawn out to it. Head runs into body, belly into chest and shoulder into flank as one plush shape.
    Not round its eyes (their sockets hold them)."""
    me = o.data
    E = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    n = len(me.vertices)
    cnt = np.zeros(n)
    np.add.at(cnt, E[:, 0], 1)
    np.add.at(cnt, E[:, 1], 1)

    def avg(Q):
        acc = np.zeros((n, 3))
        np.add.at(acc, E[:, 0], Q[E[:, 1]])
        np.add.at(acc, E[:, 1], Q[E[:, 0]])
        return acc / np.maximum(cnt, 1)[:, None]
    P0 = verts(o)
    keep = np.ones(n)
    for side in (1, -1):
        keep = keep * smooth(1.3, 1.55, ell_dist(P0, mir(EYE_C, side), (EYE_R,) * 3))
    keep = keep * smooth(0.8, 1.2, ell_dist(P0, NOSE_C[0], (0.02, 0.02, 0.02)))
    for _ in range(rounds):
        P, Nn = verts(o), normals(o)
        Q = P.copy()
        for _ in range(reach):
            Q = avg(Q)
        dip = ((Q - P) * Nn).sum(1)
        w = smooth(0.0002, 0.0016, dip) * keep
        set_verts(o, P + (Q - P) * w[:, None] * 0.6)
    apply_mods(o, [("SMOOTH", {"factor": 0.5, "iterations": 2})])


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces = {"Skin": build_skin()}
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, FAWN, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, FAWN, LASH, lower_share=0.6)
    tags = {}
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Wing" + tag], tags["Wing" + tag] = build_membrane(side, 12, 36, HI, N + "Wing" + tag + "Hi")
    pieces["Arms"] = build_arms(HI, 20)
    pieces["Legs"] = build_legs(HI, 18)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 26, 0.0105, 14), (20, -20, 0.0048, 8))),
             "Echo": build_echo_rings(HI)}
    if not clay:
        paint_all(pieces, frames, tags)
    return pieces, frames, glows, tags


# ---------- painting ----------
def read_attr(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


def chest_coords(P):
    """Its chest, flattened onto the front of its body: x across, z up, from the middle of its pale bib."""
    return P[:, 0], P[:, 2] - CHEST_C


CHEST_C = 0.44                                      # the middle of its bib (height)
BIB = (0.062, 0.07)                                 # its half-width and half-height
RIPPLES = (0.012, 0.024)                            # the two rings round its lower edge: how far out from it


def paint_skin(o):
    """Cocoa fur, a deeper cap down its crown and back; a fawn mask over its eyes and muzzle; a cream bib on its chest, ringed below twice like a
    ripple; blush on its cheeks; a dark button nose; a small open mouth, a pink tongue in it."""
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n = len(P)
    # fine strands lying down and back over it, gathered into soft locks (a blotchy noise read as dirt)
    warp = fbm(P, 40.0, 2, 8)[:, None] * 0.012
    strands = fur_strands(P + warp, Nn)
    clumps = fbm(P, 26.0, 3, 6)
    col = mix(np.broadcast_to(COCOA, (n, 3)), COCOA_WARM, smooth(0.45, 0.75, clumps) * 0.3)
    # a deeper cap: its crown between the ears, running down its back
    cap = smooth(0.2, 0.75, Nn[:, 2]) * smooth(-0.11, -0.03, y) * (z > 0.6)
    back = smooth(0.2, 0.8, Nn[:, 1]) * smooth(0.6, 0.35, z)
    col = mix(col, COCOA_DEEP, np.clip(cap * 0.55 + back * 0.4, 0, 1))
    # the fawn mask: a broad round shape over its eyes and muzzle, its edge furred
    edge_noise = (fbm(P, 70.0, 3, 21) - 0.5) * 0.22
    mr = np.hypot(x / 0.118, (z - 0.582) / np.where(z > 0.582, 0.085, 0.09))
    mask = (1 - smooth(0.82, 1.0, mr + edge_noise)) * smooth(-0.07, -0.115, y)
    col = mix(col, mix(np.broadcast_to(FAWN, (n, 3)), CREAM, smooth(0.5, 0.0, mr) * 0.35), mask)
    # the bib, and its two ripples below
    bx, bz = chest_coords(P)
    front = smooth(-0.2, -0.55, Nn[:, 1]) * (z < 0.53) * (y < 0.0)
    br = np.hypot(bx / BIB[0], bz / BIB[1])
    bib = (1 - smooth(0.88, 1.0, br + edge_noise * 0.6)) * front
    col = mix(col, CREAM, bib)
    out = (br - 1.0) * min(BIB)
    lower = smooth(0.35, -0.2, bz / BIB[1])                                       # arcs round its lower half, fading up its sides
    ring = sum(1 - smooth(0.0022, 0.0042, np.abs(out - r)) for r in RIPPLES) * lower * front
    col = mix(col, COCOA_DEEP * 0.85, np.clip(ring, 0, 1) * 0.9)
    # blush; the nose; nostrils; the mouth and tongue
    blush = np.zeros(n)
    for side in (1, -1):
        blush = np.maximum(blush, 1 - smooth(0.004, 0.024, np.linalg.norm(P - np.array((side * 0.084, -0.142, 0.548)), axis=1)))
    col = mix(col, BLUSH, blush * 0.5 * smooth(-0.1, -0.13, y))
    nose = 1 - smooth(0.85, 1.25, ell_dist(P, NOSE_C[0] + V(0, -0.006, 0.0), (NOSE_C[1][0] * 1.5, 0.02, NOSE_C[1][2] * 1.5)))
    col = mix(col, NOSE, nose * smooth(-0.17, -0.185, y))
    nostril = np.zeros(n)
    for side in (1, -1):
        nostril = np.maximum(nostril, 1 - smooth(0.0022, 0.0036, np.hypot(x - side * 0.0062, (z - 0.5775) * 1.3)))
    nostril = nostril * smooth(-0.184, -0.19, y)
    col = mix(col, MOUTH, nostril * 0.85)
    mouth, down, _ = mouth_field(P)
    col = mix(col, mix(np.broadcast_to(MOUTH, (n, 3)), TONGUE, smooth(0.55, 0.85, down) * 0.85), mouth)
    col = col * (0.9 + 0.16 * strands)[:, None]                                  # each strand's tip catching the light
    relief = (strands - 0.5) * 0.0006 + (clumps - 0.5) * 0.0012 - mouth * 0.0026 - nostril * 0.0008
    relief = relief * (1 - nose) + nose * 0.0
    set_verts(o, P + Nn * relief[:, None])
    rough = 0.8 - 0.42 * nose - 0.4 * mouth - 0.1 * bib
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def fur_strands(P, Nn, size=0.0024):
    """Fine fur, 0 between strands and 1 along one: lines running down its body and back over its head (the way fur lies), broken into short strands."""
    flow = np.stack([np.zeros(len(P)), np.full(len(P), 0.55), -np.ones(len(P))], 1)
    flow = flow - Nn * (flow * Nn).sum(1)[:, None]
    flow = flow / np.maximum(np.linalg.norm(flow, axis=1), 1e-6)[:, None]
    across = np.cross(Nn, flow)
    a = (P * across).sum(1) / size
    b = (P * flow).sum(1) / (size * 5)
    cell = hash01(np.floor(a).astype(np.int64), np.floor(b).astype(np.int64), 0, 19)
    line = 1 - np.abs(np.sin(np.pi * (a + cell * 0.6)))
    return np.clip(line ** 2 * (0.55 + 0.45 * cell), 0, 1)


def mouth_field(P):
    """Its small open mouth, under its nose: 1 inside it (the edge soft), how far down it each point lies (0 its upper lip, 1 its lower), and the front."""
    q = P - np.array(tuple(MOUTH_C))
    hx, hz = 0.0145, 0.0105
    x, zz = q[:, 0] / hx, q[:, 2] / hz
    top = 0.3 + 0.25 * x * x                                                     # its upper lip, the corners turned up: a smile
    bot = -np.sqrt(np.clip(1 - x * x, 0, 1))                                     # its lower lip a round U
    d = np.minimum(np.minimum(top - zz, zz - bot), 1 - np.abs(x)) * hz
    inside = smooth(0.0, 0.0009, d) * (q[:, 1] < 0.02) * (P[:, 1] < -0.14)
    return inside, np.clip((top - zz) / np.maximum(top - bot, 1e-6), 0, 1), d


def paint_ear(o):
    """Velvet plum outside (cocoa where it springs from its crown); ivory inside, cut with darker grooves, going warm and deep into its hollow; a plum
    lip."""
    P, Nn = verts(o), normals(o)
    n = len(P)
    inner = read_attr(o, "inner")
    f = read_attr(o, "ef")
    velvet = fbm(P * np.array([2.0, 2.0, 2.0]), 140.0, 3, 31)
    outside = mix(np.broadcast_to(COCOA, (n, 3)), PLUM, smooth(0.12, 0.42, f))
    outside = mix(outside, PLUM_DEEP, smooth(0.6, 1.2, f) * 0.25)
    outside = outside * (0.94 + 0.1 * velvet)[:, None]
    groove = np.zeros(n)
    for g in GROOVES:
        groove = np.maximum(groove, np.exp(-((f - g) / 0.006) ** 2))
    inside = mix(np.broadcast_to(IVORY, (n, 3)), MAUVE, smooth(0.62, EAR_CAVE, f) * 0.55)       # warmer and deeper toward its hollow
    inside = mix(inside, PLUM_DEEP, smooth(EAR_CAVE + 0.06, EAR_CAVE - 0.02, f) * 0.8)
    inside = mix(inside, GROOVE, groove * 0.75)
    col = mix(outside, inside, smooth(0.25, 0.75, inner))
    col = mix(col, PLUM_DEEP, (np.abs(inner - 0.5) < 0.01) * 0.6)                 # its lip
    rough = 0.72 - 0.3 * smooth(0.25, 0.75, inner)
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_membrane(o, side, tags):
    """Plum, deepest by its body and wrist and lightening toward its trailing edge (thinner there); faint ripples of an echo spreading out from its
    wrist; a darker hem along its free edge."""
    P = verts(o)
    n = len(P)
    seg = np.array([t[0] for t in tags])
    tt = np.array([t[1] for t in tags])
    vv = np.array([t[2] for t in tags])
    d = np.linalg.norm(P - np.array(tuple(mir(WRIST, side))), axis=1)
    thin = np.sin(np.pi * tt) * smooth(0.35, 0.95, vv) * (seg < 3)
    col = mix(np.broadcast_to(PLUM_DEEP, (n, 3)), PLUM, smooth(0.05, 0.6, vv) * 0.85)
    col = mix(col, MAUVE, thin * 0.45)
    ripple = sum(np.exp(-((d - r) / 0.0035) ** 2) * (1 - k * 0.18) for k, r in enumerate((0.055, 0.092, 0.13, 0.168)))
    col = mix(col, MAUVE * 1.08, np.clip(ripple, 0, 1) * smooth(0.02, 0.12, vv) * (1 - smooth(0.85, 1.0, vv)) * 0.55)
    hem = smooth(0.95, 1.0, vv) * (seg < 3)
    col = mix(col, PLUM_DEEP * 0.8, hem * 0.7)
    tex = fbm(P, 220.0, 2, 77)
    col = col * (0.95 + 0.08 * tex)[:, None]
    paint(o, np.clip(col, 0, 1), 0.55 + 0.1 * tex, np.zeros(n))


def paint_arms(o):
    """Its upper arms furred cocoa by its shoulders; forearms, wrists and fingers bare plum-dark; ivory thumb claws."""
    P = verts(o)
    n = len(P)
    part = read_attr(o, "part")
    sd = read_attr(o, "side")
    keys = list(BONE_R)
    col = np.broadcast_to(PLUM_DEEP, (n, 3)).copy()
    upper = part == keys.index("Upper")
    fur = np.zeros(n)
    for side in (1, -1):
        sel = upper & (sd == side)
        dd = np.linalg.norm(P[sel] - np.array(tuple(mir(SHOULDER, side))), axis=1)
        fur[sel] = 1 - smooth(0.04, 0.08, dd)
    col = mix(col, COCOA, fur)
    thumb = part == keys.index("Thumb")
    for side in (1, -1):
        sel = thumb & (sd == side)
        dd = np.linalg.norm(P[sel] - np.array(tuple(mir(WRIST, side))), axis=1)
        col[sel] = mix(col[sel], CLAW, smooth(0.012, 0.02, dd))
    knuckle = fbm(P, 300.0, 2, 3)
    col = col * (0.94 + 0.08 * knuckle)[:, None]
    paint(o, np.clip(col, 0, 1), 0.6 - 0.25 * thumb, np.zeros(n))


def paint_legs(o):
    P = verts(o)
    n = len(P)
    col = np.broadcast_to(PLUM_DEEP, (n, 3)).copy()
    sd = read_attr(o, "side")
    claw = np.zeros(n)
    for side in (1, -1):
        foot = mir(LEG[-1], side)
        sel = sd == side
        claw[sel] = smooth(-0.008, -0.014, P[sel, 1] - foot.y)
    col = mix(col, CLAW, claw)
    col = mix(col, COCOA, smooth(0.25, 0.29, P[:, 2]))
    paint(o, np.clip(col, 0, 1), 0.6 - 0.25 * claw, np.zeros(n))


def eye_paint(o, fr):
    """A big glossy eye: deep espresso going warm amber toward its lower rim (the light through it), a ring of teal eyeshine, a big round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(20, 14, 14), (len(px), 3)).copy()
    iris = mix(rgb(52, 32, 28), rgb(176, 108, 56), smooth(0.0, -0.85, py / IRIS) * smooth(0.3, 0.85, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 26 + np.sin(azi * 5) * 1.3))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    shine = np.exp(-((r / IRIS - (SHINE[0] + SHINE[1]) / 2) / ((SHINE[1] - SHINE[0]) / 2)) ** 2) * front
    col = mix(col, rgb(40, 196, 178), shine * 0.6)
    col = mix(col, rgb(10, 8, 10), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    col = mix(col, rgb(12, 8, 8), smooth(IRIS - 0.04, IRIS + 0.02, r) * (1 - smooth(IRIS + 0.02, IRIS + 0.12, r)) * 0.7)      # a dark limbal ring
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def paint_all(pieces, frames, tags):
    paint_skin(pieces["Skin"])
    for tag in "LR":
        paint_ear(pieces["Ear" + tag])
        eye_paint(pieces["Eye" + tag], frames[tag])
    for side, tag in ((1, "L"), (-1, "R")):
        paint_membrane(pieces["Wing" + tag], side, tags["Wing" + tag])
    paint_arms(pieces["Arms"])
    paint_legs(pieces["Legs"])


VIEWS = [(0, -1, 0.2), (0.62, -0.72, 0.3), (1, 0, 0.12), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.4, -0.5, -0.6)]
VIEW_AT = (0, 0.04, 0.58)
FACE_AT = (0, -0.12, 0.6)
EXTRA = [(0.1, -1, 0.12, 0.9, FACE_AT), (0.8, -0.6, 0.25, 0.9, FACE_AT), (0.35, -0.85, 0.5, 0.8, (0.19, -0.09, 0.86)), (1, 0.2, 0.4, 0.9, (0.19, -0.09, 0.84)),
         (0.4, -0.85, 0.2, 0.36, tuple(EYE_C)), (0.6, -0.2, -0.75, 1.2, (0, 0.06, 0.34))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, tags = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "glow", {k: len(o.data.polygons) for k, o in glows.items()}, flush=True)
    stage_setup((0.3, 0.32, 0.36, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.05, 0.04, 0.05, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    only = [int(k) for k in ARGS[ARGS.index("views") + 1].split(",")] if "views" in ARGS else None
    allv = VIEWS + EXTRA
    shots(os.path.join(REVIEW, STAGE), [allv[k] for k in only] if only else allv, target=VIEW_AT, dist=2.3, size=560)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3000                  # (about 6k tris: a Common pet, its ears and wings carrying its silhouette)
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "LidUL": 1.3, "LidUR": 1.3, "LidLL": 1.3, "LidLR": 1.3, "EarL": 1.5, "EarR": 1.5, "WingL": 0.75, "WingR": 0.75,
          "Arms": 0.9, "Legs": 0.9}
HEAD_ZONE = (HEAD + V(0, -0.015, -0.01), (0.165, 0.16, 0.14))     # its head with its cheeks and muzzle


def is_head(poly):
    c = np.array(tuple(poly.center))
    return bool(np.linalg.norm((c - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1])) < 1.0)


def split_rims(o, angle=50):
    """A thin plate's rims kept apart from its faces in the shading (smoothed together, the corners at its finger tips shaded black)."""
    md = o.modifiers.new("Rims", "EDGE_SPLIT")
    md.split_angle = math.radians(angle)
    md.use_edge_sharp = False
    apply_mods(o, [])


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    select_only([lows["Skin"]])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    # QuadriFlow can leave a lone vertex standing out of the surface: each back onto it
    P = verts(lows["Skin"])
    tree = tree_of(pieces["Skin"])
    snapped = 0
    for i in range(len(P)):
        loc, nrm, _, dist = tree.find_nearest(V(*P[i]))
        if loc is not None and dist > 0.003:
            P[i] = tuple(loc - nrm * 0.0005)
            snapped += 1
    set_verts(lows["Skin"], P)
    print("SNAPPED", snapped, "skin vertices back onto the surface", flush=True)
    tags = {}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
        lows["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Low", GAME, nt=24, res=(9, 3, 9, 3), grooves=False)
        lows["Wing" + tag], tags["Wing" + tag] = build_membrane(side, 3, 6, GAME, N + "Wing" + tag + "Low")
    lows["Arms"] = build_arms(GAME, 6, low=True)
    lows["Legs"] = build_legs(GAME, 6, low=True)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    for tag in "LR":
        split_rims(lows["Wing" + tag])
    return lows, tags


def flatten_normals(objs, pad=4):
    """The membranes' share of the normal map made flat: their relief is a fraction of a millimetre, and baked on a thin plate's tips it comes out
    turned away (black notches)."""
    img = bpy.data.images[PET + "_Normal"]
    if img.packed_file:
        img.unpack(method="REMOVE")
        img.reload()
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    mask = np.zeros((h, w), dtype=bool)
    for o in objs:
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            loops = list(p.loop_indices)
            a, b, c = [np.array(uv[i].uv) * (w, h) for i in loops[:3]]
            lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - pad, 0, (w - 1, h - 1))
            hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + pad, 0, (w - 1, h - 1))
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-12:
                continue
            ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
            qx, qy = xs + 0.5, ys + 0.5
            w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
            w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
            inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
            for p0, p1 in ((a, b), (b, c), (c, a)):
                e = p1 - p0
                t = np.clip(((qx - p0[0]) * e[0] + (qy - p0[1]) * e[1]) / max(e @ e, 1e-12), 0, 1)
                inside |= np.hypot(qx - p0[0] - e[0] * t, qy - p0[1] - e[1] * t) <= pad
            mask[ys[inside], xs[inside]] = True
    px[mask] = (0.5, 0.5, 1.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.save()
    img.pack()
    return int(mask.sum())


# ---------- the skeleton ----------
NECK = V(0, -0.02, 0.5)
EAR_BONE_F = 0.12                                    # where each ear turns, along it (inside its crown)
WING_BONES = ("Arm", "Fore", "Hand", "Fing1", "Fing2", "Fing3")


def wb(name, tag):
    return name + tag


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", BODY[0].copy(), "Root"), ("Head", NECK.copy(), "Body")]
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
        bones.append(("Ear" + tag, ear_line(side, EAR_BONE_F)[0], "Head"))
        bones += [(wb("Arm", tag), mir(SHOULDER, side), "Body"), (wb("Fore", tag), mir(ELBOW, side), wb("Arm", tag)), (wb("Hand", tag), mir(WRIST, side), wb("Fore", tag))]
        for k in range(3):
            bones.append((wb("Fing%d" % (k + 1), tag), mir(WRIST, side), wb("Hand", tag)))
        bones.append(("Leg" + tag, mir(LEG[0], side), "Body"))
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def skin_weights(P_):
    """Head and body, passing over at its neck; the skin of its shoulder mound partly with its upper arm (so the arm's root never shows)."""
    hz = np.linalg.norm((P_ - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    out = []
    for i in range(len(P_)):
        w = blend({"Body": 1.0}, {"Head": 1.0}, float(smooth(1.1, 0.88, hz[i])))
        side = 1 if P_[i][0] > 0 else -1
        tag = "L" if side > 0 else "R"
        d = (Vector(P_[i]) - mir(SHOULDER, side)).length
        if d < 0.05:
            w = blend(w, {wb("Arm", tag): 1.0}, float(1 - smooth(0.022, 0.05, d)) * 0.6)
        out.append(w)
    return out


def membrane_weights(tags, side):
    """Each spoke's bones along it, and the membrane between two spokes a blend of theirs; its root edge (buried in its flank) with its body."""
    tag = "L" if side > 0 else "R"
    arm = wing_spokes(side)[4]
    L = arc_lengths(arm)
    v_elbow = float(L[int(np.argmin([(q - mir(ELBOW, side)).length for q in arm]))] / L[-1])

    def spoke(k, v):
        if k < 3:
            return blend({wb("Hand", tag): 1.0}, {wb("Fing%d" % (k + 1), tag): 1.0}, float(smooth(0.06, 0.3, v)))
        if k == 3:                                    # wrist to knee
            hand = 1 - float(smooth(0.05, 0.45, v))
            leg = float(smooth(0.6, 1.0, v))
            return {kk: vv for kk, vv in ((wb("Hand", tag), hand), (wb("Fore", tag), max(0.0, 1 - hand - leg)), ("Leg" + tag, leg)) if vv > 1e-4}
        return chain_weight([wb("Hand", tag), wb("Fore", tag), wb("Arm", tag)], (0.06, 0.3, v_elbow + 0.1), v)
    out = []
    for seg, t, v in tags:
        w = blend(spoke(seg, v), spoke(seg + 1, v), t)
        if seg == 3:
            w = blend(w, {"Body": 1.0}, float(smooth(0.72, 1.0, v)) * math.sin(math.pi * t) ** 0.7)
        out.append(w)
    return out


def arm_weights(o):
    part = read_attr(o, "part")
    sd = read_attr(o, "side")
    keys = list(BONE_R)
    names = {"Upper": "Arm", "Fore": "Fore", "Thumb": "Hand", "F1": "Fing1", "F2": "Fing2", "F3": "Fing3"}
    P = verts(o)
    out = []
    for i in range(len(P)):
        side = int(sd[i])
        tag = "L" if side > 0 else "R"
        w = {wb(names[keys[int(part[i])]], tag): 1.0}
        if (Vector(P[i]) - mir(WRIST, side)).length < 0.016:
            w = {wb("Hand", tag): 1.0}
        elif (Vector(P[i]) - mir(ELBOW, side)).length < 0.017:
            w = {wb("Arm", tag): 0.5, wb("Fore", tag): 0.5}
        out.append(w)
    return out


def bind_all(lows, rig, glows, tags):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    for side, tag in ((1, "L"), (-1, "R")):
        rigid(lows["Ear" + tag], "Ear" + tag)
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    weigh(lows["Arms"], arm_weights(lows["Arms"]))
    weigh(lows["Legs"], [{"LegL" if s > 0 else "LegR": 1.0} for s in read_attr(lows["Legs"], "side")])
    wings = {}
    for side, tag in ((1, "L"), (-1, "R")):
        w = lows.pop("Wing" + tag)
        # (the rims were split apart for the shading: each split copy keeps its original's place, so match by place)
        src = build_membrane(side, 3, 6, GAME, "tmp")
        sp = verts(src[0])
        mw = membrane_weights(src[1], side)
        bpy.data.objects.remove(src[0], do_unlink=True)
        tree = BVHTree.FromPolygons([tuple(q) for q in sp], [[k] for k in range(len(sp))]) if False else None
        idx = [int(np.argmin(np.linalg.norm(sp - q, axis=1))) for q in verts(w)]
        weigh(w, [mw[k] for k in idx])
        wings[tag] = w
    weigh(glows["Echo"], [{"EarL" if q[0] > 0 else "EarR": 1.0} for q in verts(glows["Echo"])])
    weigh(glows["Glints"], [{"EyeL" if q[0] > 0 else "EyeR": 1.0} for q in verts(glows["Glints"])])
    tag_pieces(lows)
    body = join_into(lows, "Body")
    select_only([wings["L"], wings["R"]], wings["L"])
    bpy.ops.object.join()
    wing = wings["L"]
    wing.name = wing.data.name = N + "Wings"
    pet_kit.bind(rig, [body, wing] + list(glows.values()))
    return body, wing


PIECES = ("Skin", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR", "EarL", "EarR", "Arms", "Legs")


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def part_flush(body, gap=0.0015, rounds=6):
    """Where an eye or a lid slides in under the brow, the skin can run within a millimetre of it and parallel: it would shimmer. Each such skin face is
    moved off the eye or lid, keeping its side of it, to a clean gap. Returns how many skin vertices moved."""
    from mathutils.geometry import intersect_point_tri
    me = body.data
    names = {g.index: g.name for g in body.vertex_groups}
    moved = set()
    for _ in range(rounds):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        dl = bm.verts.layers.deform.active

        def eye_part(f):
            best = {}
            for v in f.verts:
                for gi, w in v[dl].items():
                    best[names[gi]] = best.get(names[gi], 0) + w
            top = max(best, key=best.get)
            return top.startswith("Eye") or top.startswith("Lid")
        part = [eye_part(f) for f in bm.faces]
        tree = BVHTree.FromBMesh(bm)
        push = {}
        for f in bm.faces:
            cen = f.calc_center_median()
            for p in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                for _, _, j, _ in tree.find_nearest_range(p, gap):
                    if j is None or j == f.index or part[j] == part[f.index] or set(f.verts) & set(bm.faces[j].verts):
                        continue
                    g = bm.faces[j]
                    q = p - g.normal * g.normal.dot(p - g.verts[0].co)
                    if not intersect_point_tri(q, *[v.co for v in g.verts[:3]]):
                        continue
                    skin, eye = (g, f) if part[f.index] else (f, g)
                    if abs(skin.normal.dot(eye.normal)) < 0.99:
                        continue
                    n = eye.normal
                    sdist = (skin.calc_center_median() - eye.calc_center_median()).dot(n)
                    if abs(sdist) >= gap:
                        continue
                    target = gap if sdist >= 0 else -gap
                    for v in skin.verts:
                        step = n * (target - sdist)
                        if v.index not in push or step.length > push[v.index].length:
                            push[v.index] = step
        if not push:
            bm.free()
            break
        bm.verts.ensure_lookup_table()
        for i, dv in push.items():
            bm.verts[i].co += dv
        moved |= set(push)
        bm.to_mesh(me)
        bm.free()
    me.update()
    return len(moved)


# ---------- poses, in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left), as PetRig's tables ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def sym(table):
    """Left values; each right twin mirrored (x kept, y and z flipped)."""
    out = dict(table)
    for name, v in table.items():
        m = re.match(r"^(Arm|Fore|Hand|Fing\d|Ear|Eye|Leg)L$", name)
        if m and m.group(1) + "R" not in table:
            out[m.group(1) + "R"] = (v[0], -v[1], -v[2]) + tuple(v[3:])
    return out


def probe(rig, body, wing, bones=("Head", "EarL", "ArmL", "ForeL", "HandL", "Fing1L", "Fing3L", "LegL")):
    """Each bone's signs, measured on the mesh: where what it carries goes (model axes, mm) under +0.4 rad about each game axis."""
    for o in (body, wing):
        groups = {g.name: g.index for g in o.vertex_groups}

        def centre(idx, o=o):
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            me = o.evaluated_get(dg).to_mesh()
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            o.evaluated_get(dg).to_mesh_clear()
            return co.reshape(-1, 3)[idx].mean(axis=0)
        for bone in bones:
            if bone not in groups:
                continue
            gi = groups[bone]
            idx = [v.index for v in o.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
            if not idx:
                continue
            pose(rig, {})
            c0 = centre(idx)
            row = []
            for k, axis in enumerate("xyz"):
                turn = [0.0, 0.0, 0.0]
                turn[k] = 0.4
                pose(rig, spec({bone: tuple(turn)}))
                d = (centre(idx) - c0) * 1000
                row.append("%s+ (%d,%d,%d)" % (axis, round(d[0]), round(d[1]), round(d[2])))
            print("PROBE", o.name[len(N):], bone, len(idx), "verts", " ".join(row), flush=True)
    pose(rig, {})


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
    """What must never pass through what, in any pose: the membranes through its body, head or ears; one wing through the other; its ears through
    its wings; its legs through its belly."""

    def __init__(self, body, wing):
        self.body, self.wing = body, wing
        d = dominant(body)
        fp = np.zeros(len(body.data.polygons), dtype=int)
        body.data.attributes["piece"].data.foreach_get("value", fp)
        _, tris = posed(body)

        def faces(test):
            return [i for i in range(len(tris)) if test(fp[i], d[tris[i][0]])]
        sk = PIECES.index("Skin")
        self.head = faces(lambda p, b: p == sk and b == "Head")
        self.trunk = faces(lambda p, b: p == sk and b == "Body")
        self.ears = faces(lambda p, b: p in (PIECES.index("EarL"), PIECES.index("EarR")))
        self.legs = faces(lambda p, b: p == PIECES.index("Legs"))
        self.arms = {t: faces(lambda p, b, t=t: p == PIECES.index("Arms") and b.endswith(t)) for t in "LR"}
        wd = dominant(wing)
        wco, wtris = posed(wing)
        self.wtris = wtris
        # the membranes away from their buried root edge (by its flank and shoulder): what is free to swing
        self.free = {t: [i for i, tr in enumerate(wtris) if wd[tr[0]].endswith(t) and wd[tr[0]] != "Body" and not wd[tr[0]].startswith("Leg")
                         and not wd[tr[0]].startswith("Arm")] for t in "LR"}

    def run(self):
        co, tris = posed(self.body)
        wco, wtris = posed(self.wing)
        out = {}
        allw = self.free["L"] + self.free["R"]
        out["wings x head"] = pairs(wco, wtris, allw, co, tris, self.head)
        out["wings x ears"] = pairs(wco, wtris, allw, co, tris, self.ears)
        out["wings x trunk"] = pairs(wco, wtris, allw, co, tris, self.trunk)
        out["wing x wing"] = pairs(wco, wtris, self.free["L"], wco, wtris, self.free["R"])
        out["arms x head"] = pairs(co, tris, self.arms["L"] + self.arms["R"], co, tris, self.head + self.ears)
        out["legs x wings"] = 0
        out["low z"] = round(float(co[:, 2].min()), 4)
        return out


VIEWS_GAME = VIEWS + EXTRA

if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows, hitags = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.03, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.36, 1))
    lows, tags = build_low(pieces, frames)
    if STAGE == "all":
        unwrap(lows, [(is_head, 1.8), (None, 1.0)], SCALES, margin=0.01, angle=42)
        bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.38, 0.26, 0.23, 1), far=("Skin",), reach=(0.003, 0.008),
                 far_reach=(0.008, 0.02), reaches={"WingL": (0.002, 0.005), "WingR": (0.002, 0.005), "Arms": (0.003, 0.008), "Legs": (0.003, 0.008),
                                                   "EarL": (0.004, 0.01), "EarR": (0.004, 0.01)})
        print("WING NORMALS FLATTENED", flatten_normals([lows["WingL"], lows["WingR"]]), "texels", flush=True)
    else:
        clay = bpy.data.materials.new("clay")
        gg = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        gg.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    tree = tree_of(pieces["Skin"])
    print("SKIN GAP (low from high, m)", round(surface_gap(lows["Skin"], tree), 4), flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 26, 0.0105, 10), (20, -20, 0.0048, 6))),
             "Echo": build_echo_rings(GAME, sides=4, nt=24, lift=-0.0006)}      # (the game ear has no grooves: sunk in its faceted wall, they showed as dashes)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body, wing = bind_all(lows, rig, glows, tags)
    print("SKIN MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "WINGS tris", sum(len(p.vertices) - 2 for p in wing.data.polygons),
          "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body, wing] + list(glows.values()) for v in o.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), uv_overlap_texels(wing.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body, wing] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), "box middle", round((max(zs) + min(zs)) / 2, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Body", "Head", "EarL", "ArmL", "HandL", "LegL"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    for side in (1, -1):
        c, tan, _, _ = ear_line(side, 1.0)
        print("EAR MOUTH", side, "game axes", (round(-c.x, 4), round(c.z, 4), round(c.y, 4)), "facing", (round(-tan.x, 3), round(tan.z, 3), round(tan.y, 3)), flush=True)
    probe(rig, body, wing)
    chk = Checker(body, wing)
    pose(rig, {})
    print("POSE Rest", chk.run(), flush=True)
    RIG = {"body": body, "wing": wing, "rig": rig, "glows": glows, "frames": frames, "chk": chk}


# its poses (signs measured on the mesh, probe): +x tips its head back; +y turns it to its left; +z rolls it to its left. A left wing: z+ swings it
# down, y+ sweeps it back and in; its forearm folds in with z+; a finger folds back with y+, curls down with z+. An ear: +x tips it back, z+ out and
# down. Left values; the right mirrors y and z.
FLAP_UP = sym({"ArmL": (0, 0.1, -0.75), "ForeL": (0, 0, -0.12), "Fing1L": (0, -0.05, -0.1), "Fing2L": (0, -0.08, -0.08), "Fing3L": (0, -0.1, 0), "Body": (0.06, 0, 0),
               "EarL": (0.1, 0, 0.05)})
FLAP_DOWN = sym({"ArmL": (0, -0.12, 0.6), "ForeL": (0, 0, 0.12), "Fing1L": (0, 0.06, 0.22), "Fing2L": (0, 0.08, 0.22), "Fing3L": (0, 0.1, 0.18), "Body": (-0.05, 0, 0),
                 "EarL": (-0.08, 0, -0.04)})
# (no folded pose: folded, its membrane bunched into its flanks; it hovers on slow, lazy beats instead)
GLIDE = sym({"ArmL": (0, -0.05, 0.28), "ForeL": (0, 0, -0.1), "Fing1L": (0, -0.12, 0), "Fing2L": (0, -0.08, 0.05), "Fing3L": (0, -0.04, 0.1), "Body": (-0.18, 0, 0),
             "Head": (0.12, 0, 0), "EarL": (-0.2, 0, -0.05)})
LISTEN = sym({"Head": (0.08, 0.22, 0.28), "EarL": (-0.15, -0.2, 0.1)})
LISTEN["EarR"] = (-0.05, 0.25, -0.05)
ECHO = sym({"Head": (0.32, 0, 0), "Body": (0.12, 0, 0), "EarL": (-0.2, -0.15, 0.2), "ArmL": (0, -0.1, -0.35), "ForeL": (0, 0, -0.15),
            "Fing1L": (0, -0.1, -0.1), "Fing2L": (0, -0.12, 0), "Fing3L": (0, -0.12, 0.05)})
EAR_FLICK = {"EarL": (0.3, 0.15, 0.25)}
LEGS_TUCK = sym({"LegL": (-0.4, 0, 0.1)})


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-10, -6), "FlapUp": spec(FLAP_UP), "FlapDown": spec(FLAP_DOWN), "Glide": spec(GLIDE),
            "Listen": spec(LISTEN), "Echo": spec(ECHO), "EarFlick": spec(EAR_FLICK), "Legs": spec(LEGS_TUCK),
            "Look": spec({"Head": (0.05, 0.4, 0.05)}), "EyesL": spec(sym({"EyeL": (0, 0.25, 0)}))}


GAME_TABLES = {"FLAP_UP": FLAP_UP, "FLAP_DOWN": FLAP_DOWN, "GLIDE": GLIDE, "LISTEN": LISTEN, "ECHO": ECHO, "EAR_FLICK": EAR_FLICK, "LEGS_TUCK": LEGS_TUCK}
TRANSITIONS = [("Rest", "FlapUp"), ("FlapUp", "FlapDown"), ("FlapDown", "Rest"), ("Rest", "Glide"), ("Glide", "FlapUp"), ("Glide", "FlapDown"), ("Rest", "Echo"), ("Echo", "FlapDown"),
               ("Rest", "Listen")]


def check_transitions(rig, chk, lib):
    lib = dict(lib, Rest={})
    for na, nb in TRANSITIONS:
        worst = {}
        for k in range(11):
            spec_a, spec_b = lib[na], lib[nb]
            mixed = {}
            for bone in set(spec_a) | set(spec_b):
                qa = Matrix.Rotation(math.radians(spec_a[bone][1]), 3, Vector(spec_a[bone][0])).to_quaternion() if bone in spec_a else Matrix.Identity(3).to_quaternion()
                qb = Matrix.Rotation(math.radians(spec_b[bone][1]), 3, Vector(spec_b[bone][0])).to_quaternion() if bone in spec_b else Matrix.Identity(3).to_quaternion()
                q = qa.slerp(qb, k / 10)
                axis, angle = q.to_axis_angle()
                mixed[bone] = (tuple(axis), math.degrees(angle), (0, 0, 0))
            pose(rig, mixed)
            for key, v in chk.run().items():
                worst[key] = min(worst.get(key, 9.0), v) if key == "low z" else max(worst.get(key, 0), v)
        flag = {k: v for k, v in worst.items() if k != "low z" and v > 0}
        print("TRANSITION", na, "->", nb, flag if flag else "clean", flush=True)


POSE_VIEWS = [(0, -1, 0.15, 2.3, VIEW_AT), (0.62, -0.72, 0.3, 2.3, VIEW_AT), (1, 0.05, 0.1, 2.3, VIEW_AT), (-0.4, 0.8, 0.5, 2.3, VIEW_AT)]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    body, wing, rig, glows, frames, chk = RIG["body"], RIG["wing"], RIG["rig"], RIG["glows"], RIG["frames"], RIG["chk"]
    lib = pose_library(frames)
    only = ARGS[ARGS.index("only") + 1].split(",") if "only" in ARGS else None
    for name, sp in lib.items():
        if only and name not in only:
            continue
        pose(rig, sp)
        print("POSE", name, chk.run(), flush=True)
        if STAGE == "rig" and "noshots" not in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=420)
    check_transitions(rig, chk, lib)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS body", name, row, flush=True)
    for name, row in pet_kit.stress_report(rig, wing, lib).items():
        print("STRESS wing", name, row, flush=True)
    for name, table in GAME_TABLES.items():
        print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.3, size=560)
        for name in ("FlapUp", "FlapDown", "Glide", "Echo", "Listen", "Blink"):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS[:2], size=420)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 2.3, VIEW_AT))      # first: the export takes the glow pieces' colours off
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values()), extras=[wing]), flush=True)
    print("DONE", flush=True)

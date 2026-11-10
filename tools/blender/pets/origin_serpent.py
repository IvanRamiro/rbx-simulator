"""The Origin Serpent (Secret, Primordial; Beginner Qi Egg): "The first coil of the first spirit vein. The world's oldest Qi still flows along the path
it carved."

Recreated (November 10, 2026; the old model, which the owner liked, was a faceted dragon-serpent rising in an S from a coil, cyan seams between its
scales, a horned head with fangs and cyan barbels, two Qi rings spiralling round it): the same creature, rebuilt (the owner's choices: a floating
helix; its two rings kept and made to orbit), in a design language of its own: the first spirit vein, a living current of the world's oldest Qi.
A loong, after the old texts' nine resemblances (a stag's horns, a camel's long head, a demon's eyes, a snake's neck, a clam's belly, a carp's
scales): its long body corkscrews up through the air round an invisible axis, its tail trailing below like a root of light, its neck leaving the
helix to carry its head forward over the top. Its scales are faceted carp scales of dark primordial slate edged in silver, the world's first Qi
glowing cyan in the seams between them; a vein of light runs down each flank; its belly is plated pale. Its head: a long muzzle with flared
nostrils, a heavy brow over fierce cyan slit eyes, a jaw a little open on four bone fangs, branching stag antlers tipped in cyan, two long glowing
barbels; a scalloped fin ridge runs down its back. Two Qi rings, magenta and cyan, spiral round it.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/origin_serpent.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: through the bake and the rig, with the bones' signs measured.
all: also the poses, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre. It floats: the tip of its trailing tail is its lowest point, at about
z = 0.04. +X is its left. The maps go to assets/pets/BeginnerQiEgg/.

What touches what: body, head, jaw, brow and nostrils are one fused skin; the antlers root in its crown and the fin ridge in its back (their own
pieces); the eyes sit in their sockets under their lids; the barbels root in its muzzle, the veins lie on its flanks and the rings float round it
(glow pieces).
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "OriginSerpent"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: primordial slate, silver, the first Qi ----------
SLATE, SLATE_DEEP, SLATE_LIGHT = rgb(52, 58, 92), rgb(26, 28, 52), rgb(96, 108, 150)
SILVER = rgb(206, 216, 232)
BELLY = rgb(176, 188, 214)
QI = rgb(64, 226, 255)
MOUTH = rgb(70, 22, 48)
BONE = rgb(226, 222, 206)
LASH = rgb(10, 12, 26)
QI_HEX = "38e0ff"          # its veins, barbels and the cyan ring (Neon: saturated, a pale cyan blooms white)
RING_HEX = "ff4fd8"        # the magenta ring
GLINT_HEX = "f2fbff"

# ---------- its path: a dangling tail, a helix rising round an invisible axis, a neck carrying its head forward over the top ----------
AXIS = V(0, 0.06, 0)
TURNS = 2.25
HELIX_Z = (0.11, 0.5)


def helix_point(t):
    a = math.pi - TURNS * TAU * (1 - t)                 # it ends at the left of the axis, heading forward (-Y)
    r = 0.12 + 0.05 * math.sin(math.pi * t)
    return AXIS + V(r * math.cos(a), r * math.sin(a), HELIX_Z[0] + (HELIX_Z[1] - HELIX_Z[0]) * t)


TAIL_TIP = V(0.03, 0.235, 0.045)                       # its tail trailing below the helix, a root of light
HEAD_C = V(0.0, -0.2, 0.705)                           # the middle of its cranium (before its head's scaling, below)
KNOTS = [TAIL_TIP, V(0.015, 0.205, 0.08)] + [helix_point(t) for t in np.linspace(0.0, 1.0, 37)] + [
    V(-0.085, -0.075, 0.57), V(-0.045, -0.115, 0.645), V(-0.012, -0.145, 0.69), V(0.0, -0.165, 0.705)]
PATH = catmull(KNOTS, 6)
# its body's radius along the path (0 at its tail tip, 1 where its neck meets its head)
# (its tail tip no thinner than the game mesh's 6.5 mm re-mesh can keep: its frond tuft finishes it)
BODY_R = ((0, 0.009), (0.04, 0.014), (0.15, 0.024), (0.35, 0.04), (0.55, 0.05), (0.72, 0.052), (0.86, 0.047), (0.94, 0.04), (1, 0.038))


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def path_frames(path):
    """Along the path: its tangent, its back (dorsal: outward from the axis and up along the helix, up along its neck) and its left side."""
    out = []
    n = len(path)
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        f = i / (n - 1)
        radial = V(p.x - AXIS.x, p.y - AXIS.y, 0)
        radial = radial.normalized() if radial.length > 1e-4 else V(0, 1, 0)
        want = (radial * 0.75 + V(0, 0, 1) * 0.66).lerp(V(0, 0, 1), float(smooth(0.86, 0.96, f)))
        d = (want - t * t.dot(want)).normalized()
        out.append((t, d, t.cross(d).normalized()))
    return out


FRAMES = path_frames(PATH)


def frame_at(f):
    k = min(int(round(f * (len(PATH) - 1))), len(PATH) - 1)
    return FRAMES[k]


# ---------- the head ----------
# its head, 1.35 times its first size about its neck joint (the owner: "the face more bigger and fiercer"): every point of it through hp(), every
# length through K
HEAD_PIVOT = V(0, -0.15, 0.705)
K = 1.35


def hp(x, y, z):
    return HEAD_PIVOT + (V(x, y, z) - HEAD_PIVOT) * K


def hk(knots):
    return tuple((a, b * K) for a, b in knots)


# its head: a loft from the back of its skull to its nose (wide at its cheeks, a scowling brow, a long flat-topped muzzle narrowing to its nose;
# balls and tubes read first as a deer's head, then as a box with a pig's snout); its lower jaw its own loft, hinged and open on its fangs
HEAD_Y = (hp(0, -0.15, 0).y, hp(0, -0.326, 0).y)
HEAD_Z = (hp(0, 0, 0.705).z, hp(0, 0, 0.69).z)
HEAD_W = hk(((0, 0.034), (0.12, 0.046), (0.3, 0.045), (0.5, 0.034), (0.75, 0.026), (0.9, 0.021), (0.97, 0.014), (1, 0.006)))
HEAD_HT = hk(((0, 0.028), (0.18, 0.034), (0.33, 0.031), (0.52, 0.019), (0.8, 0.016), (0.93, 0.016), (0.98, 0.011), (1, 0.004)))
HEAD_HB = hk(((0, 0.03), (0.3, 0.022), (0.6, 0.012), (0.9, 0.01), (1, 0.005)))
JAW_HINGE = hp(0, -0.188, 0.676)
JAW_LEN = 0.118 * K
JAW_OPEN = math.radians(30)                              # (wide on its fangs: fiercer)
JAW_W = hk(((0, 0.032), (0.4, 0.028), (0.75, 0.022), (0.95, 0.015), (1, 0.005)))
JAW_HT = hk(((0, 0.01), (0.6, 0.008), (1, 0.004)))
JAW_HB = hk(((0, 0.022), (0.5, 0.015), (0.9, 0.009), (1, 0.004)))
EYE_R = 0.0135 * K
EYE_C = hp(0.03, -0.212, 0.721)
EYE_AXIS = V(0.78, -0.5, 0.36).normalized()
LID_UP, LID_LOW = (24.0, 118.0, 0.0018 * K), (-44.0, -126.0, 0.0016 * K)      # (its upper lid low over a narrowed eye: fierce)
LID_TILT = 22.0                                          # (its outer corner up under its scowling brow: tilted down, it looked sad)
BLINK_U, BLINK_L = 46.0, 28.0                            # (they add past the 68 degrees between the lids' edges: the lids meet)
IRIS, PUPIL = 0.92, 0.2
# its antlers (left): from its crown, back, out and up; a main beam and two tines
# (swept back along its head, a dragon's: upright, they read as a stag's)
ANTLER = [hp(0.024, -0.17, 0.73), hp(0.04, -0.146, 0.76), hp(0.06, -0.106, 0.782), hp(0.08, -0.052, 0.792), hp(0.094, -0.004, 0.788)]
TINES = [(0.33, V(0.004, 0.008, 0.036) * K), (0.66, V(0.012, 0.016, 0.03) * K)]       # (along the beam, its tip's offset from there)
# its barbels (left): from the sides of its muzzle, sweeping back, out and down, the tips curling
BARBEL = [hp(0.017, -0.304, 0.684), hp(0.04, -0.29, 0.674), hp(0.072, -0.256, 0.652), hp(0.098, -0.206, 0.636), hp(0.118, -0.152, 0.634),
          hp(0.128, -0.104, 0.646), hp(0.122, -0.066, 0.664)]      # (an S: drooping, then curling back up along its neck; set straight, they read as wires)
# (left: root, direction, length): two great fangs and a row of teeth up top, a fang and teeth below (longer and more of them: fiercer)
FANGS = [(hp(0.017, -0.298, 0.68), V(0, -0.15, -1), 0.024 * K), (hp(0.02, -0.276, 0.676), V(0, 0, -1), 0.015 * K),
         (hp(0.021, -0.258, 0.675), V(0, 0, -1), 0.008 * K), (hp(0.021, -0.243, 0.675), V(0, 0, -1), 0.007 * K), (hp(0.01, -0.318, 0.682), V(0, -0.3, -1), 0.007 * K),
         (hp(0.013, -0.288, 0.0), V(0.0, -0.3, 1), 0.016 * K), (hp(0.017, -0.268, 0.0), V(0, 0, 1), 0.008 * K), (hp(0.018, -0.25, 0.0), V(0, 0, 1), 0.007 * K)]
LOWER_TEETH = 3                         # the last few, set on its open lower jaw
JAW_M = Matrix.Translation(JAW_HINGE) @ Matrix.Rotation(JAW_OPEN, 4, V(1, 0, 0)) @ Matrix.Translation(-JAW_HINGE)


def fang_list():
    """Every fang and tooth (left): root, direction, length, radius. The last LOWER_TEETH sit on the open lower jaw's top line, set in the jaw's frame."""
    out = []
    for k, (root, d, length) in enumerate(FANGS):
        r = (0.0042 if length > 0.014 * K else 0.0027) * K
        if k < len(FANGS) - LOWER_TEETH:
            # seated on its upper jaw's underside, from the same profile the head is lofted with, its root sunk 4 mm into the gum (placed by hand,
            # the small teeth hung below the gum once its head was scaled: QA found them floating)
            f = (root.y - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0])
            cz = HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f
            cs = min(1.0, abs(root.x) / prof(HEAD_W, f)) ** (1 / 0.85)
            sn = math.sqrt(max(0.0, 1 - cs * cs))
            root = V(root.x, root.y, cz - prof(HEAD_HB, f) * sn ** 0.9 + 0.004)
        if k >= len(FANGS) - LOWER_TEETH:
            f = (JAW_HINGE.y - root.y) / JAW_LEN
            local = V(root.x, root.y, JAW_HINGE.z - 0.004 + prof(JAW_HT, f) * 0.5)
            root, d = JAW_M @ local, JAW_M.to_3x3() @ d
        out.append((root, d.normalized(), length, r))
    return out


BROW = [hp(0.023, -0.184, 0.738), hp(0.031, -0.205, 0.732), hp(0.035, -0.236, 0.716)]
NOSTRIL = hp(0.011, -0.31, 0.703)
# its cheek frills (left): spines fanning back from behind its jaw
FRILLS = [(hp(0.04, -0.176, 0.7), V(0.6, 0.75, 0.15), 0.066 * K), (hp(0.042, -0.17, 0.688), V(0.65, 0.7, -0.2), 0.058 * K),
          (hp(0.038, -0.172, 0.713), V(0.45, 0.8, 0.5), 0.054 * K), (hp(0.036, -0.166, 0.678), V(0.55, 0.7, -0.55), 0.046 * K)]   # (bigger, spikier: fiercer)


def loft(m, centre, w, ht, hb, rings=48, sides=40, xform=None):
    """A closed loft: centre(f) the middle line, w/ht/hb (f) half-width, height above, depth below. xform: a matrix applied to every point."""
    bm = m.bm
    ring_verts = []
    for i in range(rings + 1):
        f = i / rings
        c = centre(f)
        ring = []
        for k in range(sides):
            t = TAU * k / sides
            sn, cs = math.sin(t), math.cos(t)
            p = c + V(prof(w, f) * math.copysign(abs(cs) ** 0.85, cs), 0, (prof(ht, f) if sn > 0 else prof(hb, f)) * math.copysign(abs(sn) ** 0.9, sn))
            ring.append(bm.verts.new(xform @ p if xform is not None else p))
        ring_verts.append(ring)
    for i in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((ring_verts[i][k], ring_verts[i][k2], ring_verts[i + 1][k2], ring_verts[i + 1][k]))
    bm.faces.new(list(reversed(ring_verts[0])))
    bm.faces.new(ring_verts[-1])


def build_skin():
    m = Mesh()
    m.tube(PATH, lambda f: prof(BODY_R, f), sides=36, plane=V(0, 0, 1))
    loft(m, lambda f: V(0, HEAD_Y[0] + (HEAD_Y[1] - HEAD_Y[0]) * f, HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f), HEAD_W, HEAD_HT, HEAD_HB)
    jaw = JAW_M
    loft(m, lambda f: JAW_HINGE + V(0, -JAW_LEN * f, -0.004), JAW_W, JAW_HT, JAW_HB, rings=32, sides=32, xform=jaw)
    m.ball(hp(0, -0.166, 0.67), (0.034 * K, 0.036 * K, 0.03 * K), 28, 18)                   # its throat under its skull (fuller and lower: smaller, it met its neck in a crease that folded)
    # the corners of its mouth: the jaws joined near the hinge, so its mouth opens where the gap is wide enough to hold (a slit narrower than the
    # game mesh's re-mesh folded its lips into each other)
    for side in (1, -1):
        m.tube([mir(hp(0.02, -0.188, 0.674), side), mir(hp(0.022, -0.206, 0.664), side), mir(hp(0.02, -0.222, 0.655), side)], lambda f: 0.012 * K * (1 - 0.55 * f), sides=16)
    m.tube([hp(0, -0.19, 0.672), hp(0, -0.208, 0.664)], lambda f: 0.011 * K * (1 - 0.4 * f), sides=16, flat=1.6)
    # a ridge down the middle of its snout, brow to nose (fiercer)
    m.tube([hp(0, -0.19, 0.737), hp(0, -0.245, 0.722), hp(0, -0.296, 0.707)], lambda f: (0.0065 * (1 - 0.5 * f)) * K, sides=14)
    for side in (1, -1):
        m.tube([mir(BROW[0], side), mir(BROW[1], side), mir(BROW[2], side)],
               lambda f: 0.0105 * K * (0.12 + 0.88 * math.sin(math.pi * (0.03 + 0.8 * f))) * (1 - 0.35 * f), sides=16)
        # (the brow ridge over its eye, angled steeply down to its muzzle: a scowl; tapered at both ends: blunt, its back end read as a block)
        # (sunk into its skull: thicker and higher it sat on its head as two logs)
        m.ball(mir(NOSTRIL, side), (0.0085 * K, 0.012 * K, 0.0062 * K), 18, 12)            # the flared rim of its nostril
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.12,) * 3, 24, 16)     # the socket
    o = m.finish(N + "SkinRaw", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0024, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    o.name = N + "SkinHi"
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def antler_paths(side):
    beam = catmull([mir(p, side) for p in ANTLER], 8)
    tines = []
    for f, off in TINES:
        base = path_at(beam, f)
        tines.append(catmull([base, base + mir(off, side) * 0.55 + mir(V(0, -0.004, 0.006), side), base + mir(off, side)], 6))
    return beam, tines


def build_antlers(name, coll, low=False):
    m = Mesh()
    sides = 8 if low else 16
    for side in (1, -1):
        beam, tines = antler_paths(side)
        m.tube(beam, lambda f: 0.0085 * (1 - 0.65 * f) + 0.0018, sides=sides)
        for tine in tines:
            m.tube(tine, lambda f: 0.005 * (1 - 0.7 * f) + 0.0012, sides=max(6, sides - 4))
    return m.finish(name, coll)


def build_frills(m, low=False):
    for side in (1, -1):
        for root, d, length in FRILLS:
            r0 = mir(root, side)
            d = mir(d, side).normalized()
            m.tube([r0 - d * 0.006, r0 + d * length * 0.5 + V(0, 0, 0.003), r0 + d * length], lambda f: 0.0072 * (1 - f) ** 1.1 + 0.0006, sides=6 if low else 12)


def build_fangs(m, low=False):
    for side in (1, -1):
        for root, d, length, r in fang_list():
            r0, d = mir(root, side), mir(d, side)
            m.tube([r0 - d * 0.005, r0 + d * length * 0.5, r0 + d * length], lambda f, r=r: r * (1 - f) + 0.0004, sides=6 if low else 10)


# ---------- its spines: a row down its back, a tuft at its tail tip ----------
# (single swept spines: a continuous fin read as a ribbon, the coils as a flat band)
SPINE_F = (0.1, 0.93)
SPINE_COUNT = 46


def spine_list():
    """Each spine: root (sunk in its back), tip, base radius."""
    out = []
    for k in range(SPINE_COUNT):
        u = k / (SPINE_COUNT - 1)
        f = SPINE_F[0] + (SPINE_F[1] - SPINE_F[0]) * u
        p = path_at(PATH, f)
        t, d, sd = frame_at(f)
        r = prof(BODY_R, f)
        h = 0.012 + 0.03 * math.sin(math.pi * min(1.0, 0.15 + u * 0.95)) ** 0.7       # small near its tail, tallest along its middle, smaller at its neck
        root = p + d * (r * 0.7)
        tip = root + (d * 0.82 - t * 0.57).normalized() * (h + r * 0.3)                  # swept back along its body
        out.append((root, tip, 0.0055 + 0.07 * h))
    # the tuft at its tail tip: a few fronds fanning back along it (its tail is a root of light)
    t0 = (PATH[0] - PATH[3]).normalized()
    up = V(0, 0, 1)
    side = t0.cross(up).normalized()
    for k, (a, b, h) in enumerate(((0.0, 0.0, 0.05), (0.5, 0.25, 0.04), (-0.5, 0.25, 0.04), (0.25, -0.45, 0.034), (-0.25, -0.45, 0.034))):
        root = PATH[2]
        tip = root + (t0 + side * a + up * b).normalized() * h
        out.append((root, tip, 0.006))
    return out


def build_spines(name, coll, low=False):
    m = Mesh()
    for root, tip, r in spine_list():
        mid = root.lerp(tip, 0.5)
        m.tube([root, mid, tip], lambda f, r=r: r * (1 - f) ** 1.1 + 0.0005, sides=5 if low else 10, plane=V(0, 0, 1), caps=True)
    return m.finish(name, coll)


# ---------- its glow pieces ----------
VEIN_F = (0.06, 0.9)
VEIN_SEGMENTS = 4                        # its veins lit in four lengths: the game runs a pulse along them


def vein_path(side, f0, f1, lift=0.0012):
    pts = []
    for f in np.linspace(f0, f1, max(8, int((f1 - f0) * 260))):
        p = path_at(PATH, f)
        t, d, sd = frame_at(f)
        r = prof(BODY_R, f)
        pts.append(p + (sd * side * 0.94 + d * 0.34).normalized() * (r + lift))
    return pts


def build_veins(coll, low=False, tree=None):
    out = {}
    for k in range(VEIN_SEGMENTS):
        f0 = VEIN_F[0] + (VEIN_F[1] - VEIN_F[0]) * k / VEIN_SEGMENTS
        f1 = VEIN_F[0] + (VEIN_F[1] - VEIN_F[0]) * (k + 1) / VEIN_SEGMENTS
        m = Mesh()
        for side in (1, -1):
            pts = vein_path(side, f0, f1)
            if tree is not None:                   # set on the game skin's own surface: its nearest point (a ray could miss, or strike the next coil, and
                # the vein jumped across the air in a straight line, seen in the game renders)
                seated = []
                for p in pts:
                    loc, nrm, _, _ = tree.find_nearest(p)
                    seated.append(loc + nrm * 0.0012 if loc is not None else p)
                pts = seated
            m.tube(pts, lambda f: 0.0021, sides=5 if low else 8, plane=V(0, 0, 1))
        out["Vein" + "ABCD"[k]] = m.finish(N + "Vein" + "ABCD"[k] + "_Glow_" + QI_HEX, coll)
    return out


def build_barbels(name, coll, low=False):
    m = Mesh()
    for side in (1, -1):
        m.tube(catmull([mir(p, side) for p in BARBEL], 8), lambda f: 0.0034 * (1 - 0.75 * f) + 0.0008, sides=6 if low else 10, plane=V(0, 0, 1))
    return m.finish(name, coll)


RING_C = V(0, 0.06, 0.32)


def ring_path(phase, radius, rise, tilt, turns=1.15):
    pts = []
    for s in np.linspace(0.0, 1.0, 90):
        a = phase + turns * TAU * s
        p = V(radius * math.cos(a), radius * math.sin(a), rise * (s - 0.5))
        p = Matrix.Rotation(tilt, 3, V(1, 0, 0)) @ p
        pts.append(RING_C + p)
    return pts


RINGS = {"RingA": (RING_HEX, 0.4, 0.27, 0.34, 0.22), "RingB": (QI_HEX, 3.4, 0.24, 0.3, -0.26)}      # (hex, phase, radius, rise, tilt)


def build_ring(key, coll, low=False):
    hexc, phase, radius, rise, tilt = RINGS[key]
    m = Mesh()
    m.tube(ring_path(phase, radius, rise, tilt), lambda f: 0.0036 * math.sin(math.pi * f) ** 0.6 + 0.0012, sides=6 if low else 10, plane=V(0, 0, 1),
           caps=False)          # (its tips no thinner than 2.4 mm: thinner, their two sides read as back-to-back faces)
    return m.finish(N + key + "_Glow_" + hexc, coll)


# ---------- paint ----------
def body_coords(P):
    """Per point near its body: the fraction along its path, the angle round it (0 along its back, +-pi under its belly), the distance from it."""
    f, d = nearest_on(PATH, P)
    T = np.zeros((len(P), 3)); D = np.zeros((len(P), 3)); S = np.zeros((len(P), 3)); C = np.zeros((len(P), 3))
    idx = np.clip(np.round(f * (len(PATH) - 1)).astype(int), 0, len(PATH) - 1)
    arr_p = np.array([tuple(p) for p in PATH])
    for k in np.unique(idx):
        t, dd, sd = FRAMES[k]
        sel = idx == k
        T[sel], D[sel], S[sel] = tuple(t), tuple(dd), tuple(sd)
    # the nearest point on the path itself (between samples)
    seg = np.clip(f * (len(PATH) - 1), 0, len(PATH) - 1.0001)
    i0 = np.floor(seg).astype(int)
    C = arr_p[i0] + (arr_p[np.minimum(i0 + 1, len(PATH) - 1)] - arr_p[i0]) * (seg - i0)[:, None]
    v = P - C
    ang = np.arctan2((v * S).sum(1), (v * D).sum(1))
    return f, ang, d


# arc length along the path, divided by its local radius: scales sized to the body, smaller toward its tail
_arc = np.concatenate([[0.0], np.cumsum([(PATH[i + 1] - PATH[i]).length / max(0.012, prof(BODY_R, (i + 0.5) / (len(PATH) - 1))) for i in range(len(PATH) - 1)])])


def scale_lattice(f, ang, around=14, along=0.55):
    """Faceted carp scales: the nearest of a staggered lattice of scale centres (each set toward its scale's free, tail-ward edge), so each scale is
    rounded and the seams follow their curves (a square lattice read as tiles with cyan grout). Per point: its scale's id, how high on the scale it
    is (a cone: 1 at its middle, a cut gem's ridge) and how near a seam (1 on it)."""
    u = np.interp(f * (len(PATH) - 1), np.arange(len(PATH)), _arc) / along
    w = (ang / TAU + 0.5) * around
    r0 = np.floor(u)
    best = np.full(len(u), 9.0)
    second = np.full(len(u), 9.0)
    ident = np.zeros(len(u))
    for dr in (-1, 0, 1):
        row = r0 + dr
        off = 0.5 * (row % 2)
        c0 = np.floor(w - off)
        for dc in (-1, 0, 1):
            col = c0 + dc
            cu, cw = row + 0.62, col + off + 0.5            # (toward the tail end of its cell: carp scales overlap from the head down)
            du = (u - cu) * np.where(u > cu, 1.25, 0.85)       # (rounder at its free edge)
            dw = (w - cw) * 0.95
            d = np.hypot(du, dw)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d))
            ident = np.where(closer, row * 131 + np.mod(col, around), ident)
            best = np.where(closer, d, best)
    h = np.clip(1 - best / 0.62, 0, 1)
    seam = 1 - smooth(0.035, 0.09, second - best)
    return ident, h, seam


def paint_skin(o):
    Pv = verts(o)
    Nn = normals(o)
    n = len(Pv)
    f, ang, dist = body_coords(Pv)
    head = (Pv[:, 1] < -0.145) & (Pv[:, 2] > 0.5)                # its head (its open jaw reaches down to 0.56): smooth plates, not body scales
    sid, h, seam = scale_lattice(f, ang)
    rnd = hash01(sid.astype(np.int64), 7, 3, 11)
    belly = smooth(0.62 * math.pi, 0.78 * math.pi, np.abs(ang))
    # its back: faceted slate scales, each a little its own shade, a silver rim, the first Qi in the seams
    col = mix(np.broadcast_to(SLATE_DEEP, (n, 3)), SLATE, smooth(0.05, 0.6, h))
    col = col * (0.85 + 0.3 * rnd)[:, None]
    col = mix(col, SLATE_LIGHT, smooth(0.55, 0.95, h) * 0.35)
    rim = (1 - smooth(0.09, 0.2, 1 - seam + 0.0)) * 0 + smooth(0.0, 0.2, 1 - seam) * (1 - smooth(0.2, 0.55, 1 - seam))
    col = mix(col, SILVER, rim * 0.45)
    col = mix(col, QI, seam * 0.85)
    # its belly: wide pale plates across it
    plate = np.interp(f * (len(PATH) - 1), np.arange(len(PATH)), _arc) / 0.42
    pa = plate - np.floor(plate)
    plate_col = mix(np.broadcast_to(BELLY, (n, 3)) * 0.82, BELLY, smooth(0.05, 0.4, pa))
    plate_col = mix(plate_col, SLATE_DEEP, 1 - smooth(0.0, 0.07, pa))
    col = mix(col, plate_col, belly)
    # a soft cyan halo along each flank under its vein
    for side in (1, -1):
        col = mix(col, QI, np.exp(-((ang - side * 1.22) / 0.16) ** 2) * 0.35 * (1 - belly) * smooth(0.04, 0.08, f) * (1 - smooth(0.88, 0.92, f)))
    relief = np.where(belly > 0.5, -0.0006 * (1 - smooth(0.0, 0.07, pa)), 0.0013 * h - 0.0007 * seam) * (1 - head)
    # its head: smooth slate, silver along its brow and lips, pale under its jaw, its mouth deep crimson inside, dark nostrils
    hc = np.broadcast_to(SLATE, (n, 3)) * (0.92 + 0.12 * fbm(Pv, 60.0, 3, 5))[:, None]
    under = smooth(0.0, -0.6, Nn[:, 2]) * (Pv[:, 2] < 0.69)
    hc = mix(hc, BELLY, under * 0.9)
    jaw = JAW_M
    # (inside its mouth: between the upper head's underside and the jaw's top)
    upper_under = (Pv[:, 2] < HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * np.clip((Pv[:, 1] - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0]), 0, 1) - 0.004 * K) & (Nn[:, 2] < -0.2)
    jaw_top = np.zeros(n, dtype=bool)
    jinv = jaw.inverted()
    loc = (np.array(jinv)[:3, :3] @ Pv.T).T + np.array(jinv)[:3, 3]
    # (its jaw's own top surface, in the jaw's frame: the first test, any surface above the hinge, caught its upper muzzle too)
    jaw_top = (loc[:, 2] > JAW_HINGE.z - 0.008 * K) & (loc[:, 2] < JAW_HINGE.z + 0.008 * K) & (loc[:, 1] < JAW_HINGE.y - 0.01 * K) & (Nn[:, 2] > 0.2) & (Pv[:, 1] < hp(0, -0.2, 0).y)
    inside = (upper_under | jaw_top) & (Pv[:, 1] < hp(0, -0.2, 0).y) & (np.abs(Pv[:, 0]) < 0.03 * K)
    hc = mix(hc, MOUTH, inside.astype(float))
    brow = np.zeros(n)
    for side in (1, -1):
        bf, bd = nearest_on([mir(p, side) for p in BROW], Pv)
        brow = np.maximum(brow, 1 - smooth(0.006 * K, 0.011 * K, bd))
    hc = mix(hc, SILVER, brow * 0.55)
    nostril = np.zeros(n)
    for side in (1, -1):
        nostril = np.maximum(nostril, 1 - smooth(0.0035 * K, 0.006 * K, np.linalg.norm(Pv - np.array(tuple(mir(NOSTRIL + V(0, -0.008 * K, 0.001), side))), axis=1)))
    hc = mix(hc, LASH, nostril)
    col = np.where(head[:, None], hc, col)
    set_verts(o, Pv + Nn * relief[:, None])
    rough = np.where(head, 0.55, np.where(belly > 0.5, 0.5, 0.34 + 0.25 * seam)) - 0.0 * h
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def paint_tipped(o, roots_tips, base, tip, start=0.45):
    """Each vertex by how far it is from its piece's root toward its tip: base colour, glowing toward the tip."""
    Pv = verts(o)
    best = np.full(len(Pv), 9.0)
    frac = np.zeros(len(Pv))
    for root, tp in roots_tips:
        r, t = np.array(tuple(root)), np.array(tuple(tp))
        ab = t - r
        k = np.clip(((Pv - r) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        d = np.linalg.norm(Pv - (r + ab * k[:, None]), axis=1)
        take = d < best
        best[take], frac[take] = d[take], k[take]
    col = mix(np.broadcast_to(base, (len(Pv), 3)), tip, smooth(start, 1.0, frac))
    paint(o, np.clip(col, 0, 1), 0.4 - 0.15 * frac, np.zeros(len(Pv)))


def antler_segments():
    out = []
    for side in (1, -1):
        beam, tines = antler_paths(side)
        out.append((beam[0], beam[-1]))
        for tine in tines:
            out.append((tine[0], tine[-1]))
    return out


def eye_paint(o, fr):
    """A fierce cyan eye: the first Qi bright round a dark slit pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(10, 14, 30), (len(px), 3)).copy()
    iris = mix(rgb(20, 120, 170), rgb(140, 250, 255), smooth(0.05, 0.75, 1 - r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 30 + np.sin(azi * 6) * 1.2))[:, None]
    col = mix(col, iris, 1 - smooth(IRIS - 0.04, IRIS, r))
    col = mix(col, rgb(8, 30, 50), smooth(IRIS - 0.14, IRIS - 0.02, r) * (1 - smooth(IRIS - 0.02, IRIS, r)))
    slit = ((px / 0.1) ** 2 + (py / 0.74) ** 2) < 1.0           # (thin: fiercer)
    col = mix(col, rgb(4, 6, 14), (slit & front).astype(float))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 3.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    pieces["Antlers"] = build_antlers(N + "AntlersHi", HI)
    fm = Mesh()
    build_fangs(fm)
    pieces["Fangs"] = fm.finish(N + "FangsHi", HI)
    pieces["Spines"] = build_spines(N + "SpinesHi", HI)
    frm = Mesh()
    build_frills(frm)
    pieces["Frills"] = frm.finish(N + "FrillsHi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SLATE, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SLATE, LASH, lower_share=0.7)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-22, 22, 0.0032, 10), (18, -16, 0.0015, 8))),
             "Barbels": build_barbels(N + "Barbels_Glow_" + QI_HEX, HI), "RingA": build_ring("RingA", HI), "RingB": build_ring("RingB", HI)}
    glows.update(build_veins(HI))
    if not clay:
        paint_skin(skin)
        paint_tipped(pieces["Antlers"], antler_segments(), BONE, QI, start=0.55)
        paint_tipped(pieces["Fangs"], [(mir(r, sd), mir(r + d * l, sd)) for sd in (1, -1) for r, d, l, _ in fang_list()], BONE * 0.85, BONE)
        paint_tipped(pieces["Spines"], [(a, b) for a, b, _ in spine_list()], SLATE_DEEP, QI, start=0.35)
        paint_tipped(pieces["Frills"], [(mir(r, sd), mir(r + d.normalized() * l, sd)) for sd in (1, -1) for r, d, l in FRILLS], SLATE, QI, start=0.4)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data



# ---------- the game mesh ----------
SKIN_QUADS = 4200
SCALES = {"EyeL": 2.2, "EyeR": 2.2, "LidUL": 1.3, "LidUR": 1.3, "LidLL": 1.3, "LidLR": 1.3, "Antlers": 1.0, "Spines": 0.8, "Frills": 1.0, "Fangs": 0.8}


def fold_edges(bm, limit):
    return [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal) > limit]


def unfold(low, tree, limit=math.radians(100), rounds=12):
    """Where the re-topology left faces folded over one another (seen at its brow and its fin's base: the folds overlapped in the UV map), relax the
    vertices round each fold and set them back on the high skin, until none is left. Returns the folds found at first and at the end."""
    bm = bmesh.new()
    bm.from_mesh(low.data)
    first = len(fold_edges(bm, limit))
    for _ in range(rounds):
        bm.normal_update()
        bad = fold_edges(bm, limit)
        if not bad:
            break
        near = set()
        for e in bad:
            for v in e.verts:
                near.add(v)
                for e2 in v.link_edges:
                    near.add(e2.other_vert(v))
        near = list(near)
        bmesh.ops.smooth_vert(bm, verts=near, factor=0.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        for v in near:
            hit = tree.find_nearest(v.co)
            if hit[0] is not None:
                v.co = hit[0]
    bm.normal_update()
    last = len(fold_edges(bm, limit))
    for e in fold_edges(bm, limit)[:12]:
        c = (e.verts[0].co + e.verts[1].co) / 2
        print("FOLD AT", tuple(round(v, 3) for v in c), round(math.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))), flush=True)
    bm.to_mesh(low.data)
    bm.free()
    low.data.update()
    return first, last


def best_skin(hi):
    """QuadriFlow is chaotic: a small change to the high skin can leave folds anywhere (seen at its mouth's corner, then on its lowest coil). Try a
    few face counts, unfold each, and keep the first with no fold left (or the best): fewest folds, then the smallest gap from the high skin."""
    tree = tree_of(hi)
    best = None
    # (decimation first: it collapses the high skin's own edges, so it cannot fold over as a fresh quad layout can; QuadriFlow folded on every try
    # over its long helix, and its face counts strayed far from the target)
    tries = [("decimate", 9000), ("decimate", 10500)] + [("quadriflow", q) for q in (SKIN_QUADS, SKIN_QUADS + 600)]
    for how, amount in tries:
        quads = amount
        if how == "decimate":
            low = decimated(hi, N + "SkinTry", amount)
            apply_mods(low, [("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
            low.data.polygons.foreach_set("use_smooth", [True] * len(low.data.polygons))
        else:
            low = retopo_skin(hi, N + "SkinTry", quads)
        first, last = unfold(low, tree)
        gap = surface_gap(low, tree)
        print("SKIN TRY", how, quads, "faces", len(low.data.polygons), "folds", first, "->", last, "gap", round(gap, 4), flush=True)
        score = (last, gap)
        if best is None or score < best[0]:
            if best is not None:
                bpy.data.objects.remove(best[1], do_unlink=True)
            best = (score, low)
        else:
            bpy.data.objects.remove(low, do_unlink=True)
        if last == 0 and gap < 0.006:
            break
    best[1].name = N + "SkinLow"
    print("SKIN KEPT", best[0], flush=True)
    return best[1]


def build_low(pieces, frames):
    lows = {"Skin": best_skin(pieces["Skin"])}
    lows["Antlers"] = build_antlers(N + "AntlersLow", GAME, low=True)
    lows["Spines"] = build_spines(N + "SpinesLow", GAME, low=True)
    m = Mesh()
    build_frills(m, low=True)
    lows["Frills"] = m.finish(N + "FrillsLow", GAME)
    m = Mesh()
    build_fangs(m, low=True)
    lows["Fangs"] = m.finish(N + "FangsLow", GAME)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 18, 12)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton: a chain rooted mid-coil, down to its tail and up to its head ----------
CHAIN = ["Tail1", "Tail2", "Tail3", "Tail4", "Core", "Body1", "Body2", "Body3", "Body4", "Neck", "Head"]
CHAIN_F = (0.09, 0.18, 0.28, 0.38, 0.48, 0.58, 0.68, 0.77, 0.85, 0.92, 0.985)
HEAD_AT = V(0, -0.15, 0.705)


def bone_at(name):
    k = CHAIN.index(name)
    return HEAD_AT.copy() if name == "Head" else path_at(PATH, CHAIN_F[k])


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Core", bone_at("Core"), "Root")]
    up = CHAIN[CHAIN.index("Core") + 1:]
    parent = "Core"
    for name in up:
        bones.append((name, bone_at(name), parent))
        parent = name
    parent = "Core"
    for name in reversed(CHAIN[:CHAIN.index("Core")]):
        bones.append((name, bone_at(name), parent))
        parent = name
    bones.append(("Jaw", JAW_HINGE.copy(), "Head"))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"),
                  ("Barbel" + tag, mir(BARBEL[0], side), "Head")]
    bones += [("RingA", RING_C.copy(), "Root"), ("RingB", RING_C.copy(), "Root")]
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def in_jaw(P_):
    """How much each point belongs to its lower jaw: in the jaw's own frame, below the mouth line and forward of the hinge."""
    jinv = JAW_M.inverted()
    loc = (np.array(jinv)[:3, :3] @ P_.T).T + np.array(jinv)[:3, 3]
    below = smooth(JAW_HINGE.z + 0.008, JAW_HINGE.z + 0.001, loc[:, 2])
    ahead = smooth(JAW_HINGE.y + 0.004, JAW_HINGE.y - 0.012, loc[:, 1])
    return below * ahead * (P_[:, 1] < -0.17) * (P_[:, 2] > 0.5)


def body_weights(P_):
    f, d = nearest_on(PATH, P_)
    head = smooth(-0.13, -0.155, P_[:, 1]) * (P_[:, 2] > 0.5)
    jaw = in_jaw(P_)
    out = []
    for i in range(len(P_)):
        w = chain_weight(CHAIN, CHAIN_F, float(f[i]))
        if head[i] > 0:
            w = blend(w, {"Head": 1.0}, float(head[i]))
        if jaw[i] > 0:
            w = blend(w, {"Jaw": 1.0}, float(jaw[i]))
        out.append(w)
    return out


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for key in ("Antlers", "Frills"):
        rigid(lows[key], "Head")
    fp = verts(lows["Fangs"])
    weigh(lows["Fangs"], [{"Jaw": 1.0} if j > 0.5 else {"Head": 1.0} for j in in_jaw(fp)])
    weigh(lows["Spines"], body_weights(verts(lows["Spines"])))
    for side, tag in ((1, "L"), (-1, "R")):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    for k in "ABCD":
        weigh(glows["Vein" + k], body_weights(verts(glows["Vein" + k])))
    weigh(glows["Barbels"], [{"BarbelL" if p[0] > 0 else "BarbelR": 1.0} for p in verts(glows["Barbels"])])
    rigid(glows["RingA"], "RingA")
    rigid(glows["RingB"], "RingB")
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


def part_flush(body, gap=0.0015, rounds=6):
    """Where an eye or a lid slides in under the brow, the skin can run within a millimetre of it and parallel: it would shimmer. Each such skin face is
    moved off the eye or lid, keeping its side of it, to a clean gap (after the bake: a millimetre or two does not move the paint). Looked for both
    ways, from the eye's or lid's faces and from the skin's, as QA looks. Returns how many skin vertices moved."""
    from mathutils.bvhtree import BVHTree
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

        def check(src, dst, skin, eye):
            if abs(src.normal.dot(dst.normal)) < 0.99:
                return False
            n = eye.normal
            sdist = (skin.calc_center_median() - eye.calc_center_median()).dot(n)
            target = gap if sdist >= 0 else -gap
            if abs(sdist) >= gap:
                return False
            for v in skin.verts:
                step = n * (target - sdist)
                if v.index not in push or step.length > push[v.index].length:
                    push[v.index] = step
            return True
        for f in bm.faces:
            cen = f.calc_center_median()
            for p in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                for _, _, j, _ in tree.find_nearest_range(p, gap):
                    if j is None or j == f.index or part[j] == part[f.index] or set(f.verts) & set(bm.faces[j].verts):
                        continue
                    g = bm.faces[j]
                    q = p - g.normal * g.normal.dot(p - g.verts[0].co)
                    if intersect_point_tri(q, *[v.co for v in g.verts[:3]]):
                        skin, eye = (g, f) if part[f.index] else (f, g)
                        check(f, g, skin, eye)
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


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left); the same numbers as PetRig's OS tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def probe(rig, body, bones=("Head", "Jaw", "Neck", "Body2", "Core", "Tail3", "Tail1")):
    """Each limb's signs, measured on the mesh: where the skin it carries goes (model axes, mm) under +0.4 rad about each game axis."""
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()

    def centre(idx):
        bpy.context.view_layer.update()
        dg2 = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg2).to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        body.evaluated_get(dg2).to_mesh_clear()
        return co.reshape(-1, 3)[idx].mean(axis=0)
    for bone in bones:
        gi = groups[bone]
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
        if not idx:
            print("PROBE", bone, "no skin", flush=True)
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
        print("PROBE", bone, len(idx), "verts", " ".join(row), flush=True)
    pose(rig, {})


def uv_clashes(body, size=1024):
    """Which faces share texels: per clash, the two faces' centres and their main bones."""
    me = body.data
    uv = me.uv_layers.active.data
    names = {g.index: g.name for g in body.vertex_groups}
    owner = np.full((size, size), -1, dtype=np.int32)
    pairs = {}
    for p in me.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        here = owner[ys[inside], xs[inside]]
        for o in set(here[here >= 0].tolist()):
            pairs[(o, p.index)] = pairs.get((o, p.index), 0) + int((here == o).sum())
        owner[ys[inside], xs[inside]] = p.index

    def bone_of(fi):
        best = {}
        for vi in me.polygons[fi].vertices:
            for g in me.vertices[vi].groups:
                best[names[g.group]] = best.get(names[g.group], 0) + g.weight
        return max(best, key=best.get)
    for (a, b), n in sorted(pairs.items(), key=lambda kv: -kv[1])[:8]:
        ca, cb = me.polygons[a].center, me.polygons[b].center
        print("UV CLASH", n, "texels", tuple(round(v, 3) for v in ca), bone_of(a), "|", tuple(round(v, 3) for v in cb), bone_of(b), flush=True)



VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.3), (1, 0, 0.12), (0, 1, 0.25), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.5, -0.5, -0.45)]
VIEW_AT = (0, 0.02, 0.38)
FACE_AT = (0.0, -0.27, 0.7)
EXTRA = [(0.75, -0.6, 0.2, 0.75, FACE_AT), (0.1, -1, 0.1, 0.7, FACE_AT), (1, -0.15, 0.15, 0.7, FACE_AT), (0.7, -0.4, 0.6, 0.75, FACE_AT),
         (0.8, 0.4, 0.2, 0.9, (0, 0.1, 0.25))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "glow", {k: len(o.data.polygons) for k, o in glows.items()}, flush=True)
    stage_setup((0.3, 0.32, 0.42, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.05, 0.06, 0.12, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.1, size=640)
    print("DONE", flush=True)


def is_head(poly):
    return poly.center.y < -0.14 and poly.center.z > 0.5


_arc_m = np.concatenate([[0.0], np.cumsum([(PATH[i + 1] - PATH[i]).length for i in range(len(PATH) - 1)])])


def clashing_faces(me, size=1024):
    """The faces that share texels with another face (rasterised as uv_overlap_texels does)."""
    uv = me.uv_layers.active.data
    owner = np.full((size, size), -1, dtype=np.int32)
    out = set()
    for p in me.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        here = owner[ys[inside], xs[inside]]
        hit = set(here[here >= 0].tolist())
        if hit:
            out |= hit
            out.add(p.index)
        owner[ys[inside], xs[inside]] = p.index
    return out


def unwrap_serpent(lows, head_density=1.7, strip=0.5, margin=0.006, extra=frozenset(), depth=0):
    """Its body unrolled as strips along its path (round it from the seam under its belly, along it in metres, cut every half metre): a stacked
    helix projected by angle laid its coils' faces over each other in the map. Its head and every other piece projected as usual. All at their true
    texel density, then packed together."""
    objs = list(lows.values())
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    skin = lows["Skin"]
    me = skin.data
    P = verts(skin)
    f, ang, _ = body_coords(P)
    along = np.interp(f * (len(PATH) - 1), np.arange(len(PATH)), _arc_m)
    # past either end of its path, carried on along the end's tangent (clamped, every point there took the same value and its faces flattened over
    # each other behind its head)
    for end, k, sign in ((f >= 0.999, len(PATH) - 1, 1.0), (f <= 0.001, 0, -1.0)):
        t = FRAMES[k][0]
        beyond = (P - np.array(tuple(PATH[k]))) @ np.array(tuple(t))
        along = np.where(end, _arc_m[k] + np.maximum(0.0, beyond * sign) * sign, along)
    rad = np.interp(f, [k[0] for k in BODY_R], [k[1] for k in BODY_R])
    uv = me.uv_layers.active.data
    head_polys, body_polys = [], []
    for poly in me.polygons:
        (head_polys if is_head(poly) else body_polys).append(poly)
    for poly in body_polys:
        vids = list(poly.vertices)
        a = ang[vids].copy()
        if a.max() - a.min() > math.pi:                 # (it straddles the seam under its belly)
            a = np.where(a < 0, a + TAU, a)
        seg = math.floor(float(np.mean(along[vids])) / strip)
        for li, vi, ai in zip(poly.loop_indices, vids, a):
            uv[li].uv = (float(ai * rad[vi]) + seg * 1.0, float(along[vi] - seg * strip))
    # a few thin faces turn over as they unroll (at its neck's bend, on its coil): those go to the projection, each its own little island
    def signed(poly):
        q = [uv[li].uv for li in poly.loop_indices]
        return sum((q[i].x * q[(i + 1) % len(q)].y - q[(i + 1) % len(q)].x * q[i].y) for i in range(len(q))) / 2
    areas = np.array([signed(poly) for poly in body_polys])
    usual = np.sign(np.median(areas))
    # turned over, or squashed or stretched far from the usual (a squashed face overlapped its neighbour at its neck's bend)
    ratio = np.array([ar * usual / max(poly.area, 1e-12) for poly, ar in zip(body_polys, areas)])
    typical = float(np.median(ratio))
    turned = {poly.index for poly, r in zip(body_polys, ratio) if r <= typical * 0.35 or r >= typical * 2.8} | set(extra)
    print("UNROLLED FACES TURNED OVER", len(turned), "of", len(body_polys), flush=True)
    body_polys = [poly for poly in body_polys if poly.index not in turned]
    # its head, those faces and the other pieces: projected
    select_only(objs)
    for o in objs:
        sel = [o is not skin or is_head(poly) or poly.index in turned for poly in o.data.polygons]
        o.data.polygons.foreach_set("select", sel)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.uv.smart_project(angle_limit=math.radians(42), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    scale_uv_to(skin, body_polys, 1.0)
    scale_uv_to(skin, head_polys, head_density)
    if turned:
        scale_uv_to(skin, [me.polygons[i] for i in turned], 1.0)
    for key, o in lows.items():
        if key != "Skin":
            scale_uv_to(o, list(o.data.polygons), SCALES.get(key, 1.0))
    select_only(objs)
    for o in objs:
        o.data.polygons.foreach_set("select", [True] * len(o.data.polygons))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    # any faces of its body still sharing texels (where its neck bends tighter than its own thickness the unrolling folds over a ridge): those and
    # their neighbours go to the projection too, and it unwraps again
    clash = {i for i in clashing_faces(me) if not is_head(me.polygons[i])} - set(extra)
    print("UNWRAP PASS", depth, "body faces still clashing", len(clash), flush=True)
    if clash and depth < 3:
        grow = set(clash)
        verts_in = {v for i in clash for v in me.polygons[i].vertices}
        grow |= {poly.index for poly in me.polygons if any(v in verts_in for v in poly.vertices)}
        unwrap_serpent(lows, head_density, strip, margin, frozenset(set(extra) | grow), depth + 1)


if __name__ == "__main__" and STAGE in ("all", "rig"):
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.42, 1))
    lows = build_low(pieces, frames)
    print("SURFACE GAP skin", round(surface_gap(lows["Skin"], data["tree"]), 4), flush=True)
    worst = sorted(((data["tree"].find_nearest(v.co)[3], tuple(round(c, 3) for c in v.co)) for v in lows["Skin"].data.vertices), reverse=True)[:6]
    print("GAP AT", worst, flush=True)
    unwrap_serpent(lows)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.12, 0.13, 0.22, 1), far=("Skin",), reach=(0.003, 0.008), far_reach=(0.006, 0.016))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)
    low_tree = tree_of(lows["Skin"])
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-22, 22, 0.0032, 8), (18, -16, 0.0015, 6))),
             "Barbels": build_barbels(N + "Barbels_Glow_" + QI_HEX, GAME, low=True), "RingA": build_ring("RingA", GAME, low=True),
             "RingB": build_ring("RingB", GAME, low=True)}
    glows.update(build_veins(GAME, low=True, tree=low_tree))
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    print("SKIN MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", body.name, uv_overlap_texels(body.data, 1024), flush=True)
    uv_clashes(body)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Root", "Core", "Head", "Jaw", "Neck", "RingA", "BarbelL"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    vs = [v.co for v in glows["Glints"].data.vertices]
    mid = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    print("GLINTS box centre game axes", (round(-mid.x, 4), round(mid.z, 4), round(mid.y, 4)), flush=True)
    probe(rig, body)
    if STAGE == "rig":
        print("DONE", flush=True)
        raise SystemExit(0)


# its stances, in game axes, signs measured on the mesh (probe): +x lifts its nose and closes its jaw (so -x opens it); +y turns to its left
ROAR = {"Jaw": (-0.32, 0, 0), "Head": (0.22, 0, 0), "Neck": (0.1, 0, 0)}
SNAP = {"Jaw": (0.22, 0, 0)}                          # (its jaw near closed: further, its fangs would meet its lower jaw)
LOOK = {"Head": (0.08, 0.35, 0.12), "Neck": (0.0, 0.2, 0.0)}
SWAY_A = {"Tail3": (0, -0.12, 0), "Tail4": (0, 0.1, 0), "Body1": (0, 0.12, 0), "Body2": (0, -0.1, 0), "Body3": (0, 0.12, 0), "Body4": (0, -0.1, 0)}
SWAY_B = {k: (v[0], -v[1], v[2]) for k, v in SWAY_A.items()}
RISE = {"Core": (0.1, 0, 0), "Body1": (0.06, 0, 0), "Body2": (0.06, 0, 0), "Neck": (-0.1, 0, 0), "Head": (0.1, 0, 0)}
FLICK = {"Tail1": (0.4, 0.35, 0), "Tail2": (0.22, 0.15, 0)}
RINGS_TURN = {"RingA": (0, 1.2, 0), "RingB": (0, -1.0, 0)}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-10, -5), "Roar": {**spec(ROAR), **lids(-10, -5)}, "Snap": spec(SNAP), "Look": spec(LOOK),
            "SwayA": spec(SWAY_A), "SwayB": spec(SWAY_B), "Rise": spec(RISE), "Flick": spec(FLICK), "Rings": spec(RINGS_TURN)}


if __name__ == "__main__" and STAGE == "all":
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.1, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    face = (0.75, -0.6, 0.2, 0.8, FACE_AT)
    wide = (0.62, -0.72, 0.3, 2.1, VIEW_AT)
    for name, view in (("Blink", face), ("Roar", face), ("Snap", face), ("Look", wide), ("SwayA", wide), ("SwayB", wide), ("Rise", wide),
                       ("Flick", (0.6, 0.7, 0.2, 1.6, (0, 0.15, 0.15))), ("Rings", wide)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.3, 2.1, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

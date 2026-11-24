"""Tiangou v3's forms (run inside Blender): the hound's body, head, jaw, ears, paws and claws as fused ellipsoids (a voxel remesh of lobes laid
along the skeleton's bones, then smoothed), the white fire (ruff, collar, chest tuft, tail plume, feathers, ear flickers, the stalk) as tapered
tongues, the eclipse (a black disc, a ring of gold and a corona of streamers) and the eyes. Everything is authored in Roblox studs through
worldlib's rb (x right, y up, the hound's front toward -Z).

Every part reads its numbers from a parameter dict `P` (default: the final design, which is also what tiangou_v3_bones.py holds), so the
silhouette study (tiangou_v3_study.py) builds its eight candidates from the same code with other numbers.
"""
import math
import random

import bpy
from mathutils import Euler, Vector

import egg_hi as Hm
import egg_kit as K
import guardian_kit as G
from tiangou_v3_bones import BONES, ECLIPSE, ECLIPSE_R, STREAMS, stream_dir

W = K.W
V = Vector
TAU = 2 * math.pi


def default_params():
    return {
        "cw": 1.12, "cd": 1.05,                       # chest width and depth
        "withers": 0.7, "croup": 0.0,               # lift of the shoulder hump and of the haunch (studs)
        "neck": [(0, 12.5, -6.8), (0, 14.3, -9.1), (0, 15.5, -11.6), (0, 16.5, -14.0)], "neck_r": (3.0, 2.1),
        "head_at": (0, 16.5, -14.0), "nose": (0, 15.0, -21.5), "hs": 1.0,
        "ruff": 1.0, "tail": [BONES["Tail1"][1]] + [BONES["Tail%d" % i][2] for i in range(1, 7)], "tail_r": (1.3, 0.55),
        "legs": 1.0, "front_r": 1.25, "back_r": 1.2, "ears": 1.0, "plume": 1.0,
    }


def lobe_along(a, b, r0, r1, n=6, fx=1.0, fz=1.0, stretch=1.15):
    """Ellipsoid lobes from a to b whose radius goes r0 to r1: each long axis lies along the segment, `fx` thins its width, `fz` its height (for a
    segment that runs along the body)."""
    a, b = V(a), V(b)
    d = b - a
    rot = V((0, 1, 0)).rotation_difference(d.normalized()).to_euler()
    deg = tuple(math.degrees(c) for c in rot)
    out = []
    for i in range(n):
        t = i / (n - 1)
        r = r0 + (r1 - r0) * t
        out.append((tuple(a.lerp(b, t)), (r * fx, max(d.length / (n - 1) * stretch, r), r * fz), deg))
    return out


def leg_lobes(P, s, front):
    """The lobes of one leg (s = -1 left, +1 right)."""
    t = "Left" if s < 0 else "Right"
    q = lambda n: (BONES[n][1], BONES[n][2])
    out = []
    if front:
        k = P["front_r"]
        a, b = q("Front%sScapula" % t)
        out += lobe_along(a, b, 2.0 * k, 1.75 * k, 5, 0.85)
        a, b = q("Front%sUpper" % t)
        out += lobe_along(a, b, 1.85 * k, 1.35 * k, 6, 0.95)
        a, b = q("Front%sLower" % t)
        out += lobe_along(a, b, 1.45 * k, 0.95 * k, 7, 0.95)
        a, b = q("Front%sPaw" % t)
        out += lobe_along(a, b, 0.78 * k, 0.6 * k, 3)
        a, b = q("Front%sToes" % t)
        out += paw_lobes(a, b, s, k)
        out.append(((s * 2.6, 7.0, -7.0), (1.5 * k, 1.5 * k, 1.5 * k), None))                 # the elbow
    else:
        k = P["back_r"]
        a, b = q("Back%sThigh" % t)
        out += lobe_along(a, b, 1.75 * k, 1.45 * k, 7, 1.0)
        a, b = q("Back%sShin" % t)
        out += lobe_along(a, b, 1.7 * k, 1.1 * k, 7, 0.9)
        a, b = q("Back%sMeta" % t)
        out += lobe_along(a, b, 0.8 * k, 0.62 * k, 4)
        out.append((tuple(q("Back%sMeta" % t)[0]), (0.95 * k, 0.95 * k, 1.05 * k), None))      # the hock
        a, b = q("Back%sToes" % t)
        out += paw_lobes(a, b, s, k)
    return out


def paw_lobes(knuckle, tip, s, k):
    """A paw: a pad under the knuckle and four toes that splay a little."""
    kn, tp = V(knuckle) + V((0, 0.3, 0)), V(tip) + V((0, 0.3, 0))
    out = [(tuple(kn.lerp(tp, 0.22)), (0.95 * k, 0.62, 1.05 * k), None)]
    for dx in (-0.62, -0.21, 0.21, 0.62):
        end = V((tp.x + dx * 1.25, tp.y - 0.05, tp.z + (0.15 if abs(dx) > 0.5 else -0.2)))
        out += lobe_along(kn + V((dx * 0.85, 0.0, -0.1)), end, 0.36 * k, 0.3 * k, 4, 1.0, 0.9, 1.05)
    return out


def body_lobes(P):
    cw, cd, wi, cr = P["cw"], P["cd"], P["withers"], P["croup"]
    L = [
        ((0, 9.7, -6.4), (3.1 * cw, 4.0 * cd, 5.0), None),               # the deep chest
        ((0, 10.1, -2.0), (3.0 * cw, 3.5 * cd, 4.2), None),              # the barrel
        ((0, 10.9, 2.0), (2.5, 2.6, 3.0), None),                         # the loin, tucked
        ((0, 10.9 + cr, 5.0), (2.5, 3.1, 3.0), None),                    # the haunch
        ((0, 8.9, -10.0), (2.3 * cw, 2.7, 2.2), None),                   # the breastbone, forward
        ((0, 12.9 + wi, -6.5), (2.5, 1.9, 3.2), None),                   # the withers
    ]
    for s in (-1, 1):
        L.append(((s * 1.5, 11.6 + wi, -7.0), (1.8, 2.4, 2.8), None))   # the shoulder muscle
        L.append(((s * 2.0, 10.6 + cr, 4.4), (0.9, 2.0, 2.0), None))     # the hip muscle
        L.append(((s * 2.7, 8.4, -9.0), (1.5, 2.1, 1.9), None))         # the point of the chest over the foreleg
    n = P["neck"]
    for a, b, f in ((n[0], n[1], 0.0), (n[1], n[2], 0.5), (n[2], n[3], 1.0)):
        r0 = P["neck_r"][0] + (P["neck_r"][1] - P["neck_r"][0]) * f
        r1 = P["neck_r"][0] + (P["neck_r"][1] - P["neck_r"][0]) * (f + 0.5 if f < 1 else 1.0)
        L += lobe_along(a, b, r0, min(r1, P["neck_r"][1] if f >= 0.5 else r1), 4, 1.0, 1.0)
    L += lobe_along(P["neck"][-1], P["head_at"], 2.0, 2.0, 2)
    tl = P["tail"]
    for i in range(len(tl) - 1):
        f = i / (len(tl) - 2)
        L += lobe_along(tl[i], tl[i + 1], P["tail_r"][0] + (P["tail_r"][1] - P["tail_r"][0]) * f, P["tail_r"][0] + (P["tail_r"][1] - P["tail_r"][0]) * (f + 1 / (len(tl) - 1)), 3)
    for s in (-1, 1):
        for front in (True, False):
            ls = leg_lobes(P, s, front)
            if P["legs"] != 1.0:                       # the study only: the legs shortened or lengthened about the hip line
                ls = [((c[0], 12.0 - (12.0 - c[1]) * P["legs"], c[2]), r, rot) for c, r, rot in ls]
            L += ls
    return L


def head_axis(P):
    """(base, nose) of the head scaled by P['hs'] about its base."""
    base, nose = V(P["head_at"]), V(P["nose"])
    return base, base + (nose - base) * P["hs"]


def skull_lobes(P):
    base, nose = head_axis(P)
    d = (nose - base)
    ln = d.length
    u = d / ln
    side = V((1, 0, 0))
    up = V((0, 1, 0)) - u * u.y
    up.normalize()
    hs = P["hs"]
    at = lambda f, h=0.0, w=0.0: base + u * (ln * f) + up * (h * hs) + side * (w * hs)
    L = [(tuple(at(0.24, 0.8)), (2.15 * hs, 1.75 * hs, 2.9 * hs), None)]             # the cranium
    L += lobe_along(at(0.45, 0.3), at(0.95, 0.15), 1.5 * hs, 0.62 * hs, 6, 1.0, 0.86)    # the muzzle
    L.append((tuple(at(0.99, 0.12)), (0.68 * hs, 0.52 * hs, 0.58 * hs), None))          # the nose
    shift = V(P["head_at"]) - V(BONES["Head"][1])
    for s in (-1, 1):
        L.append((tuple(at(0.36, 1.35, s * 0.9)), (0.95 * hs, 0.5 * hs, 1.05 * hs), None))    # the brow ridge
        L.append((tuple(at(0.34, 0.2, s * 1.4)), (0.6 * hs, 0.9 * hs, 1.4 * hs), None))     # the cheek
        L.append((tuple(at(0.72, 0.0, s * 0.8)), (0.5 * hs, 0.42 * hs, 1.6 * hs), None))     # the upper lip's jowl
        a, b = (V(x) + shift for x in BONES[("Left" if s < 0 else "Right") + "EarA"][1:3])
        e = V(BONES[("Left" if s < 0 else "Right") + "EarB"][2]) + shift
        k = P["ears"]
        L += lobe_along(a, b, 0.85 * k, 0.75 * k, 4, 0.30, 1.0, 1.1)
        L += lobe_along(b, e, 0.75 * k, 0.14 * k, 5, 0.30, 1.0, 1.1)
    return L


def jaw_lobes(P):
    base, nose = head_axis(P)
    u = (nose - base).normalized()
    hs = P["hs"]
    hinge = V(BONES["Jaw"][1])
    tip = V(BONES["Jaw"][2])
    L = lobe_along(hinge + V((0, 0.15, 0)), tip + V((0, 0.6, 0)), 0.95 * hs, 0.5 * hs, 6, 1.0, 0.8)
    L.append(((0, hinge.y - 0.1, hinge.z - 0.3), (1.25 * hs, 0.85 * hs, 1.2 * hs), None))
    L.append(((0, tip.y + 0.45, tip.z + 0.1), (0.52 * hs, 0.42 * hs, 0.52 * hs), None))
    L.append(((0, tip.y + 1.25, tip.z + 2.3), (0.42 * hs, 0.22, 1.5 * hs), None))        # the tongue, lying on the floor of the mouth
    return L


def hi_blob(name, coll, mat, lobes, voxel, smooth=0.85, rough=0.025, iterations=6):
    return G.blob(name, coll, mat, lobes, voxel=voxel, smooth=smooth, rough=rough, chisel="TG3Chisel")


# ---------------------------------------------------------------- small hard parts
def teeth(P, hi_up, hi_low):
    """Canines and a row of smaller teeth, up and down."""
    hs = P["hs"]
    for s in (-1, 1):
        G.cone(hi_up, (s * 0.7, 16.0, -20.2), (s * 0.72, 14.4, -20.35), 0.24 * hs, 6)
        G.cone(hi_low, (s * 0.52, 14.15, -20.6), (s * 0.55, 15.55, -20.7), 0.2 * hs, 6)
        for i, z in enumerate((-19.0, -18.2, -17.4)):
            G.cone(hi_up, (s * 0.7, 15.95, z), (s * 0.7, 15.1, z), 0.16 * hs, 5)
            G.cone(hi_low, (s * 0.55, 14.25, z - 0.3), (s * 0.55, 15.05, z - 0.3), 0.14 * hs, 5)
        for z in (-20.9,):
            G.cone(hi_up, (s * 0.28, 15.95, z), (s * 0.28, 14.95, z), 0.14 * hs, 5)
            G.cone(hi_low, (s * 0.3, 14.25, z + 0.1), (s * 0.3, 15.0, z + 0.1), 0.13 * hs, 5)


def claws(hi):
    """A dark-ivory claw on each toe tip."""
    for name in ("FrontLeftToes", "FrontRightToes", "BackLeftToes", "BackRightToes"):
        kn, tp = V(BONES[name][1]) + V((0, 0.3, 0)), V(BONES[name][2]) + V((0, 0.3, 0))
        for dx in (-0.62, -0.21, 0.21, 0.62):
            end = V((tp.x + dx * 1.25, tp.y - 0.05, tp.z + (0.15 if abs(dx) > 0.5 else -0.2)))
            base = end + V((0, 0.12, 0))
            front = -1 if name.startswith("Front") else -1
            G.cone(hi, base, end + V((0, -0.35, -0.55)), 0.2, 6)


def nose_pad(hi, P):
    base, nose = head_axis(P)
    c = V(nose) + V((0, 0.38 * P["hs"], 0.3 * P["hs"]))
    G.sphere(hi, c, 0.5, nu=12, nv=8, radii=(0.58 * P["hs"], 0.4 * P["hs"], 0.36 * P["hs"]))


def eyes(P, skull):
    """Almond gold eyes under a scowling brow, set on the skull's surface by a ray: (iris Hi, pupil Hi, lids Hi). Round black pupils."""
    iris, pupil, lids = Hm.Hi(), Hm.Hi(), Hm.Hi()
    hs = P["hs"]
    for s in (-1, 1):
        n = V((s * 0.8, 0.12, -0.58)).normalized()
        near = V((s * 1.0, 17.15, -16.7))
        c = G.surface_along(skull, near, n, 4.0) - n * 0.1
        G.eye(iris, pupil, lids, c, n, V((s * 0.0, -0.35, -1.0)), 0.74 * hs, 0.56 * hs, tilt=0.30, bulge=0.14, lid=0.34, droop=0.55, lower=0.17, slit=0.55, pupil_height=0.8)
    return iris, pupil, lids


# ---------------------------------------------------------------- fire
def flame(hi, base, direction, width_axis, length, width, rnd, lean=(0, 0, 0), thick=0.34, rings=8):
    """A flat tongue of fire: a lens-section tube along a swaying curve that leaves `base` along `direction`, broad along `width_axis`, wide a
    quarter of the way up and pointed at its tip, leaning toward `lean` as it rises. UV u round it, v 0 at the root to 0.8 at the tip."""
    d = V(direction).normalized()
    wa = V(width_axis) - d * V(width_axis).dot(d)
    wa = wa.normalized() if wa.length > 1e-4 else G.frame(d)[1]
    nr = d.cross(wa).normalized()
    sway = rnd.uniform(-1, 1)
    base, lean = V(base), V(lean)
    ctr, rows = [], []
    for i in range(rings + 1):
        t = i / rings
        c = base + d * (length * t) + wa * (length * 0.09 * sway * math.sin(math.pi * t) + length * 0.05 * sway * t * t) + lean * (length * t * t)
        w = width * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.18 + t * 0.62))) * max(0.04, (1.0 - t * 0.96) ** 0.8)
        ctr.append((c, w))
    for i, (c, w) in enumerate(ctr):
        rows.append([hi.v(c + wa * w), hi.v(c + nr * w * thick), hi.v(c - wa * w), hi.v(c - nr * w * thick)])
    for i in range(rings):
        for k in range(4):
            k2 = (k + 1) % 4
            mid = (V(hi.verts[rows[i][k]]) + V(hi.verts[rows[i + 1][k2]])) / 2
            out = K.rb_inv(*(mid - V(W.rb(*ctr[i][0]))))
            hi.facing([rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]], [(k / 4, i / rings * 0.8), ((k + 1) / 4, i / rings * 0.8), ((k + 1) / 4, (i + 1) / rings * 0.8), (k / 4, (i + 1) / rings * 0.8)], out)
    tip = hi.v(ctr[-1][0] + d * (length * 0.06))
    for k in range(4):
        k2 = (k + 1) % 4
        out = K.rb_inv(*(V(hi.verts[rows[-1][k]]) - V(W.rb(*ctr[-1][0]))))
        hi.facing([rows[-1][k], rows[-1][k2], tip], [(k / 4, 0.8), ((k + 1) / 4, 0.8), ((k + 0.5) / 4, 0.84)], out)


class Fire:
    """White fire tongues in one Hi, remembering which vertices belong to which bones (so each tongue follows its own chain)."""

    def __init__(self, seed=3):
        self.hi = Hm.Hi()
        self.rnd = random.Random(seed)
        self.spans = []                                # (first vertex, last vertex, [bones])

    def tongue(self, base, direction, up, length, radius, bones, sides=5):
        n0 = len(self.hi.verts)
        flame(self.hi, base, direction, up, length, radius * 2.6, self.rnd, lean=(0, 0.16, 0), thick=0.36)
        self.spans.append((n0, len(self.hi.verts), list(bones)))

    def count(self):
        return len(self.spans)


def build_fire(P):
    f = Fire()
    R = f.rnd
    k = P["ruff"]
    up = (0, 1, 0)
    # the mane down the neck's top, running back over the shoulders
    n = P["neck"]
    for i in range(16):
        t = i / 15
        seg = min(2, int(t * 3))
        a, b = V(n[seg]), V(n[seg + 1])
        c = a.lerp(b, (t * 3) - seg) + V((R.uniform(-0.6, 0.6), 2.0, 0.0))
        d = V((R.uniform(-0.25, 0.25), 0.28, 1.0)).normalized()
        f.tongue(c, d, up, (3.4 + 2.0 * math.sin(math.pi * t)) * k, 0.46, ["Neck3", "Neck2", "Neck1", "RuffTopA", "RuffTopB"])
    # the collar behind each cheek, falling over the shoulder
    for s in (-1, 1):
        t = "Left" if s < 0 else "Right"
        for i in range(10):
            u = i / 9
            c = V((s * (1.9 + 0.5 * u), 15.4 - 2.2 * u, -11.6 + 1.8 * u))
            d = V((s * (0.18 + 0.1 * u), -0.35 - 0.3 * u, 0.8)).normalized()
            f.tongue(c, d, up, (3.0 + 1.6 * math.sin(math.pi * u)) * k, 0.44, ["Neck2", t + "Ruff1", t + "Ruff2", "Chest"])
    # the chest tuft
    for i in range(10):
        s = -1 if i % 2 == 0 else 1
        u = i / 9
        c = V((s * R.uniform(0.0, 1.8), 10.6 - 2.6 * u, -11.3 + 0.4 * u))
        d = V((s * R.uniform(0.0, 0.3), -0.9, 0.1 + 0.3 * u)).normalized()
        f.tongue(c, d, (1, 0, 0), (2.6 + 1.2 * u) * k, 0.45, ["Chest", "ChestTuftA", "ChestTuftB"])
    # the plume of the tail: tongues along its length, longest at its end
    tl = P["tail"]
    for i in range(30):
        t = i / 29
        seg = min(len(tl) - 2, int(t * (len(tl) - 1)))
        a, b = V(tl[seg]), V(tl[seg + 1])
        c = a.lerp(b, t * (len(tl) - 1) - seg) + V((R.uniform(-0.5, 0.5), R.uniform(0.0, 0.5), 0.0))
        along = (b - a).normalized()
        d = (along * 1.0 + V((R.uniform(-0.3, 0.3), R.uniform(0.1, 0.5), 0.0))).normalized()
        f.tongue(c, d, up, (3.0 + 6.5 * t ** 1.4) * P["plume"], 0.5 * (1.0 - 0.25 * t), ["Tail%d" % (1 + min(5, int(t * 6.0)))] + ["Tail%d" % (j + 1) for j in range(6) if abs(j - t * 6.0) < 1.6])
    # feathers: the back of each forearm and each thigh and hock hang with fire
    for s in (-1, 1):
        t = "Left" if s < 0 else "Right"
        for i in range(8):
            u = i / 7
            c = V((s * R.uniform(2.1, 3.1), 7.0 - 3.9 * u, -7.1 - 0.15 * u))
            f.tongue(c, V((s * 0.05, -0.55, 0.85)).normalized(), up, 2.4 + 1.6 * math.sin(math.pi * u), 0.34, ["Front%sFeather" % t, "Front%sLower" % t])
        for i in range(10):
            u = i / 9
            c = V((s * R.uniform(2.3, 3.4), 9.0 - 5.2 * u, 3.2 + 2.6 * u))
            f.tongue(c, V((s * 0.05, -0.65, 0.75)).normalized(), up, 2.8 + 1.8 * math.sin(math.pi * u), 0.36, ["Back%sFeather" % t, "Back%sThigh" % t, "Back%sShin" % t])
    # a flicker inside each ear, and a lick of fire at its tip
    for s in (-1, 1):
        t = "Left" if s < 0 else "Right"
        a, b, e = BONES[t + "EarA"][1], BONES[t + "EarA"][2], BONES[t + "EarB"][2]
        for i in range(3):
            c = V(a) + V((s * (-0.15), 0.4 + 0.5 * i, -0.45 - 0.15 * i))
            f.tongue(c, (V(e) - V(a)).normalized() * 1.0 + V((0, 0, -0.2)), up, (2.4 + 0.8 * i) * P["ears"], 0.2, [t + "EarA", t + "EarB"], 4)
    # the stalk that holds the eclipse: fire rising from the withers to the ring
    s1, s2 = V(BONES["Stalk1"][1]), V(BONES["Stalk2"][2])
    for i in range(14):
        t = i / 13
        c = s1.lerp(s2, t) + V((R.uniform(-0.8, 0.8), 0.0, R.uniform(-0.6, 0.6)))
        f.tongue(c, (s2 - s1).normalized() * 0.7 + V((R.uniform(-0.45, 0.45), 0.1, R.uniform(-0.3, 0.4))), (1, 0, 0) if i % 2 else (0, 0, 1), 2.6 + 1.2 * t, 0.62, ["Stalk1", "Stalk2"])
    return f


# ---------------------------------------------------------------- the eclipse
def torus(hi, centre, R, r, nu=64, nv=8, mat=0):
    """A ring in the plane x-y (its axis along z) at `centre`: outer radius R, tube radius r."""
    c = V(centre)
    ring = []
    for i in range(nu):
        a = TAU * i / nu
        row = []
        for j in range(nv):
            b = TAU * j / nv
            rr = R + r * math.cos(b)
            row.append(hi.v(c + V((rr * math.sin(a), rr * math.cos(a), r * math.sin(b)))))
        ring.append(row)
    for i in range(nu):
        for j in range(nv):
            i2, j2 = (i + 1) % nu, (j + 1) % nv
            a = TAU * (i + 0.5) / nu
            b = TAU * (j + 0.5) / nv
            out = (math.cos(b) * math.sin(a), math.cos(b) * math.cos(a), math.sin(b))
            hi.facing([ring[i][j], ring[i2][j], ring[i2][j2], ring[i][j2]], [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)], out, mat)


def eclipse_disc():
    """The black disc: a flattened UV sphere (consistent winding, single poles), its face toward -Z."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=44, v_segments=16, radius=1.0)
    hi = Hm.Hi()
    idx = {}
    c = V(ECLIPSE)
    uvs = {}
    for v in bm.verts:
        # the sphere's poles lie on Blender's z: take that as Roblox's z (the disc's thin axis)
        idx[v.index] = hi.v(c + V((v.co.x * (ECLIPSE_R - 0.1), v.co.y * (ECLIPSE_R - 0.1), v.co.z * 0.6)))
        uvs[v.index] = (0.5 + math.atan2(v.co.y, v.co.x) / TAU, 0.5 + v.co.z * 0.5)
    for f in bm.faces:
        hi.f([idx[v.index] for v in f.verts], [uvs[v.index] for v in f.verts])
    bm.free()
    return hi


def corona(P):
    """(the outer ring and its streamers [Hi], a list of (first vertex, last vertex, nearest stream index or None) spans), (the core: a gold ring and its short rays)."""
    outer = Hm.Hi()
    spans = []
    n0 = len(outer.verts)
    torus(outer, ECLIPSE, ECLIPSE_R + 0.75, 0.42, 72, 8)
    spans.append((n0, len(outer.verts), None))
    rnd = random.Random(11)
    for k in range(16):
        a = TAU * (k + 0.5 * (k % 2)) / 16
        dx, dy = math.sin(a), math.cos(a)
        root = V(ECLIPSE) + V((dx * (ECLIPSE_R + 1.0), dy * (ECLIPSE_R + 1.0), 0))
        length = (8.5 + 4.5 * (0.5 + 0.5 * math.cos(a * 2)) + rnd.uniform(-1, 1)) if k % 2 == 0 else (5.5 + rnd.uniform(-0.8, 1.0))
        n1 = len(outer.verts)
        flame(outer, root, V((dx, dy, 0.1)), V((-dy, dx, 0)), length, 1.15 if k % 2 == 0 else 0.85, rnd, lean=(0, 0, 0.09), thick=0.3, rings=9)
        spans.append((n1, len(outer.verts), a))
    core = Hm.Hi()
    torus(core, ECLIPSE, ECLIPSE_R + 0.05, 0.26, 72, 6)
    for k in range(40):
        a = TAU * k / 40
        dx, dy = math.sin(a), math.cos(a)
        base = V(ECLIPSE) + V((dx * (ECLIPSE_R + 0.2), dy * (ECLIPSE_R + 0.2), 0))
        G.cone(core, base, base + V((dx, dy, 0.1)) * (1.0 + 0.7 * (k % 2)), 0.2, 4)
    return outer, spans, core

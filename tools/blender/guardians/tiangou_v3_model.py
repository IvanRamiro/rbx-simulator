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
        "cw": 1.2, "cd": 1.08,                       # chest width and depth
        "withers": 0.25, "croup": 0.0,               # lift of the shoulder hump and of the haunch (studs)
        "neck": [(0, 12.9, -7.4), (0, 14.4, -9.4), (0, 15.6, -11.7), (0, 16.5, -14.0)], "neck_r": (3.0, 2.2),
        "head_at": (0, 16.5, -14.0), "nose": (0, 15.0, -21.5), "hs": 1.0,
        "ruff": 1.0, "tail": [BONES["Tail1"][1]] + [BONES["Tail%d" % i][2] for i in range(1, 7)], "tail_r": (1.3, 0.55),
        "legs": 1.0, "front_r": 1.15, "back_r": 1.08, "ears": 1.0, "plume": 1.0,
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
        out += lobe_along(a, b, 1.5 * k, 1.35 * k, 5, 0.8)
        a, b = q("Front%sUpper" % t)
        out += lobe_along(a, b, 1.45 * k, 1.15 * k, 6, 0.9)
        a, b = q("Front%sLower" % t)
        out += lobe_along(a, b, 1.45 * k, 0.95 * k, 7, 0.95)
        a, b = q("Front%sPaw" % t)
        out += lobe_along(a, b, 0.78 * k, 0.6 * k, 3)
        a, b = q("Front%sToes" % t)
        out += paw_lobes(a, b, s, k)
        out.append(((s * 2.6, 7.0, -7.0), (1.15 * k, 1.15 * k, 1.15 * k), None))                 # the elbow
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
    """The torso, neck and tail, tail and legs: smooth, deep and plain (no separate muscle bulges): a barrel chest, a tucked loin, a sloping croup, and a neck that grows out of the
    chest (it starts inside it, widest at the shoulders) so there is no step where they meet."""
    cw, cd, wi, cr = P["cw"], P["cd"], P["withers"], P["croup"]
    L = [
        ((0, 9.7, -6.6), (3.3 * cw, 3.9 * cd, 5.9), None),               # the deep chest
        ((0, 10.2, -2.2), (3.1 * cw, 3.6 * cd, 4.4), None),              # the barrel
        ((0, 10.9, 1.8), (2.6, 2.7, 3.1), None),                         # the loin, tucked
        ((0, 10.9 + cr, 5.0), (2.8, 3.2, 3.1), None),                    # the haunch
        ((0, 12.3 + wi, -6.6), (2.4, 1.7, 3.2), None),                   # the withers
            ]
    L += lobe_along((0, 13.2, -5.2), (0, 14.1, -8.0), 2.5, 2.2, 4, 1.0, 1.0, 1.2)           # the shoulders slope into the neck
    L.append(((0, 12.6, -9.4), (2.9, 2.8, 2.8), None))                                         # fills the valley between the chest's front and the neck
    L.append(((0, 10.8, -10.4), (2.6, 3.0, 2.4), None))                                        # and the chest's front below it
    n = [V(p) for p in P["neck"]]
    pts = [V((0, 11.2, -5.6))] + n
    rad = [3.0, 2.9, 2.6, 2.35, 2.2] if len(n) == 4 else [3.4] * len(pts)
    rad = (rad + [P["neck_r"][1]] * len(pts))[:len(pts)]
    for i in range(len(pts) - 1):
        L += lobe_along(pts[i], pts[i + 1], rad[i], rad[i + 1], 5, 1.0, 1.0, 1.25)
    tl = P["tail"]
    for i in range(len(tl) - 1):
        f = i / (len(tl) - 2)
        L += lobe_along(tl[i], tl[i + 1], P["tail_r"][0] + (P["tail_r"][1] - P["tail_r"][0]) * f, P["tail_r"][0] + (P["tail_r"][1] - P["tail_r"][0]) * (f + 1 / (len(tl) - 1)), 3, 1.0, 1.0, 1.3)
    for s in (-1, 1):
        for front in (True, False):
            ls = leg_lobes(P, s, front)
            if P["legs"] != 1.0:
                ls = [((c[0], 12.0 - (12.0 - c[1]) * P["legs"], c[2]), r, rot) for c, r, rot in ls]
            L += ls
    return L


def head_axis(P):
    """(base, nose) of the head scaled by P['hs'] about its base."""
    base, nose = V(P["head_at"]), V(P["nose"])
    return base, base + (nose - base) * P["hs"]


def head_frame(P):
    """at(f, h, w): the point f along the head (0 at the neck, 1 at the nose), h above its axis and w to the right, in studs (scaled by hs)."""
    base, nose = head_axis(P)
    d = nose - base
    ln = d.length
    u = d / ln
    side = V((1, 0, 0))
    up = V((0, 1, 0)) - u * u.y
    up.normalize()
    hs = P["hs"]
    return (lambda f, h=0.0, w=0.0: base + u * (ln * f) + up * (h * hs) + side * (w * hs)), hs


def skull_lobes(P):
    """A canine skull: a domed cranium with brow ridges, a definite stop where the forehead drops to a tapered, bridged muzzle, flews that hang over the lower jaw,
    full cheeks, tall pointed ears."""
    at, hs = head_frame(P)
    L = [(tuple(at(0.16, 0.85)), (2.1 * hs, 1.8 * hs, 2.3 * hs), None),                  # the cranium
         (tuple(at(0.38, 1.0)), (1.85 * hs, 1.45 * hs, 1.8 * hs), None)]                   # the forehead
    L += lobe_along(at(0.56, 0.22), at(0.95, 0.04), 1.55 * hs, 0.7 * hs, 7, 0.82, 0.95)   # the muzzle, tapering
    L += lobe_along(at(0.58, 0.72), at(0.9, 0.42), 0.62 * hs, 0.34 * hs, 5, 0.8, 0.7)      # the bridge
    shift = V(P["head_at"]) - V(BONES["Head"][1])
    for s in (-1, 1):
        L.append((tuple(at(0.36, 1.62, s * 0.92)), (0.85 * hs, 0.4 * hs, 0.85 * hs), None))   # the brow ridge
        L.append((tuple(at(0.30, -0.12, s * 1.45)), (0.62 * hs, 0.92 * hs, 1.35 * hs), None))  # the cheek
        L += lobe_along(at(0.56, -0.36, s * 1.0), at(0.9, -0.5, s * 0.62), 0.55 * hs, 0.4 * hs, 6, 0.8, 1.0)   # the flew: the jowl line
        tag = "Left" if s < 0 else "Right"
        a, b = (V(x) + shift for x in BONES[tag + "EarA"][1:3])
        e = V(BONES[tag + "EarB"][2]) + shift
        k = P["ears"]
        L += lobe_along(a, b, 0.95 * k, 0.82 * k, 4, 0.28, 1.0, 1.1)
        L += lobe_along(b, e, 0.82 * k, 0.12 * k, 5, 0.28, 1.0, 1.1)
    return L


def jaw_lobes(P):
    """The lower jaw: narrower than the muzzle so the flews overhang it, a rounded chin, a tongue lying on the floor of the mouth."""
    at, hs = head_frame(P)
    L = lobe_along(at(0.34, -0.78), at(0.9, -0.82), 0.95 * hs, 0.55 * hs, 7, 0.9, 0.8)
    L.append((tuple(at(0.28, -0.8)), (1.1 * hs, 0.9 * hs, 0.95 * hs), None))
    L.append((tuple(at(0.9, -0.86)), (0.42 * hs, 0.36 * hs, 0.38 * hs), None))
    L += lobe_along(at(0.42, -0.56), at(0.74, -0.6), 0.4 * hs, 0.28 * hs, 4, 1.0, 0.45)
    return L


def hi_blob(name, coll, mat, lobes, voxel, smooth=0.85, rough=0.015, iterations=6):
    o = G.blob(name, coll, mat, lobes, voxel=voxel, smooth=smooth, rough=rough, chisel="TG3Chisel")
    return o


# ---------------------------------------------------------------- small hard parts
def teeth(P, hi_up, hi_low):
    """A real row: six incisors across the front, a canine each side, three premolars and a carnassial behind it, up and down, set along the muzzle's lip line."""
    at, hs = head_frame(P)
    for s in (-1, 1):
        # upper: embedded in the gum above the lip line, hanging below it
        G.cone(hi_up, at(0.90, -0.28, s * 0.80), at(0.90, -1.38, s * 0.80), 0.25 * hs, 6)
        for j, (f, x) in enumerate(((0.84, 0.96), (0.78, 1.02), (0.72, 1.07))):
            G.cone(hi_up, at(f, -0.28, s * x), at(f, -0.86, s * x), 0.15 * hs, 5)
        G.cone(hi_up, at(0.65, -0.28, s * 1.1), at(0.65, -0.98, s * 1.1), 0.21 * hs, 5)
        # lower: rising from the jaw, tips between the upper ones
        G.cone(hi_low, at(0.915, -1.05, s * 0.60), at(0.915, -0.42, s * 0.60), 0.22 * hs, 6)
        for f, x in ((0.83, 0.86), (0.77, 0.92), (0.71, 0.97)):
            G.cone(hi_low, at(f, -1.05, s * x), at(f, -0.55, s * x), 0.14 * hs, 5)
        G.cone(hi_low, at(0.64, -1.05, s * 0.98), at(0.64, -0.6, s * 0.98), 0.19 * hs, 5)
    for k, x in enumerate((-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)):
        f = 0.965 - 0.05 * (x / 0.5) ** 2
        G.cone(hi_up, at(f, -0.28, x), at(f, -0.80, x), 0.115 * hs, 5)
        G.cone(hi_low, at(f - 0.01, -1.05, x * 0.9), at(f - 0.01, -0.5, x * 0.9), 0.1 * hs, 5)


def claws(hi):
    """A dark-ivory claw on each toe tip."""
    for name in ("FrontLeftToes", "FrontRightToes", "BackLeftToes", "BackRightToes"):
        kn, tp = V(BONES[name][1]) + V((0, 0.3, 0)), V(BONES[name][2]) + V((0, 0.3, 0))
        for dx in (-0.62, -0.21, 0.21, 0.62):
            end = V((tp.x + dx * 1.25, tp.y - 0.05, tp.z + (0.15 if abs(dx) > 0.5 else -0.2)))
            base = end + V((0, 0.12, 0))
            G.cone(hi, base, end + V((0, -0.35, -0.55)), 0.2, 6)


def nose_pad(hi, P):
    """A defined black nose: a broad pad, two wings either side of a groove, a nostril in each (material 1 is the nostril's)."""
    at, hs = head_frame(P)
    G.sphere(hi, at(0.99, 0.26), 0.5, nu=14, nv=9, radii=(0.62 * hs, 0.32 * hs, 0.34 * hs))
    for s in (-1, 1):
        G.sphere(hi, at(1.015, 0.16, s * 0.28), 0.3, nu=10, nv=7, radii=(0.24 * hs, 0.28 * hs, 0.26 * hs))
        G.sphere(hi, at(1.055, 0.14, s * 0.27), 0.2, nu=8, nv=6, radii=(0.12 * hs, 0.16 * hs, 0.09 * hs), mat=1)


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
def flame(hi, base, direction, width_axis, length, width, sway, lean=(0, 0, 0), thick=0.3, rings=5):
    """A soft tongue of fire: a lens-section tube along an S-shaped curve that leaves `base` along `direction`, broad along `width_axis`, wide near its root and
    tapering to a point, swaying by `sway` (-1..1) and leaning toward `lean` as it rises. UV u round it (the broad faces at 0.25 and 0.75, the edges at 0 and 0.5),
    v 0 at the root to 0.8 at the tip."""
    d = V(direction).normalized()
    wa = V(width_axis) - d * V(width_axis).dot(d)
    wa = wa.normalized() if wa.length > 1e-4 else G.frame(d)[1]
    nr = d.cross(wa).normalized()
    base, lean = V(base), V(lean)
    ctr, rows = [], []
    for i in range(rings + 1):
        t = i / rings
        c = base + d * (length * t) + wa * (length * (0.2 * sway * math.sin(math.pi * t * 1.5) + 0.12 * sway * t * t)) + lean * (length * t * t * 1.4)
        w = width * (0.62 + 0.38 * math.sin(math.pi * min(1.0, 0.1 + t * 0.7))) * max(0.06, (1.0 - t * 0.95) ** 0.6)
        ctr.append((c, w))
    for c, w in ctr:
        rows.append([hi.v(c + wa * w), hi.v(c + nr * w * thick), hi.v(c - wa * w), hi.v(c - nr * w * thick)])
    for i in range(rings):
        for k in range(4):
            k2 = (k + 1) % 4
            mid = (V(hi.verts[rows[i][k]]) + V(hi.verts[rows[i + 1][k2]])) / 2
            out = K.rb_inv(*(mid - V(W.rb(*ctr[i][0]))))
            hi.facing([rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]], [(k / 4, i / rings * 0.8), ((k + 1) / 4, i / rings * 0.8), ((k + 1) / 4, (i + 1) / rings * 0.8), (k / 4, (i + 1) / rings * 0.8)], out)
    tip = hi.v(ctr[-1][0] + d * (length * 0.05))
    for k in range(4):
        k2 = (k + 1) % 4
        out = K.rb_inv(*(V(hi.verts[rows[-1][k]]) - V(W.rb(*ctr[-1][0]))))
        hi.facing([rows[-1][k], rows[-1][k2], tip], [(k / 4, 0.8), ((k + 1) / 4, 0.8), ((k + 0.5) / 4, 0.84)], out)


class Fire:
    """White fire tongues in one Hi, remembering which vertices belong to which bones (so each tongue follows its own chain). The tongues come from one seeded
    generator, and a left-hand cluster is the mirror of the right-hand one (the same numbers with x flipped)."""

    def __init__(self, seed=3):
        self.hi = Hm.Hi()
        self.rnd = random.Random(seed)
        self.spans = []

    def tongue(self, base, direction, width_axis, length, width, bones, sway=0.0, lean=(0, 0.14, 0), thick=0.4):
        n0 = len(self.hi.verts)
        flame(self.hi, base, direction, width_axis, length, width, sway, lean, thick)
        self.spans.append((n0, len(self.hi.verts), list(bones)))

    def cluster(self, base, direction, width_axis, length, width, bones, count=3, fan=0.5, mirror=False, lean=(0, 0.14, 0), spread=0.5):
        """`count` tongues from about one place: each its own length, width, sway and a turn of its direction within `fan`; mirror=True flips x, the same numbers."""
        R = self.rnd
        sx = -1 if mirror else 1
        flip = lambda v: V((sx * v[0], v[1], v[2]))
        for i in range(count):
            a, b = R.uniform(-1, 1), R.uniform(-1, 1)
            d = V(direction) + V((fan * a, fan * b * 0.6, fan * R.uniform(-0.3, 0.3)))
            off = V((spread * R.uniform(-1, 1), spread * R.uniform(-0.5, 0.5), spread * R.uniform(-1, 1)))
            L = length * R.uniform(0.7, 1.05)
            w = width * R.uniform(0.8, 1.15)
            sw = R.uniform(-1, 1)
            self.tongue(flip(V(base) + off), flip(d), flip(width_axis), L, w, bones, sw, flip(lean))


def build_fire(P):
    f = Fire()
    k, pk = P["ruff"], P["plume"]
    up = (0, 1, 0)
    n = [V(p) for p in P["neck"]]
    # the mane down the neck's top, running back over the shoulders: layered, a long outer row and a short broad inner one
    for i in range(10):
        t = i / 9
        seg = min(2, int(t * 3))
        c = n[seg].lerp(n[seg + 1], t * 3 - seg) + V((0, 1.9, 0))
        ln = (3.0 + 1.8 * math.sin(math.pi * t)) * k
        f.cluster(c, V((0, 0.25, 1.0)), (0, 1, 0), ln * 1.0, 0.8, ["Neck3", "Neck2", "Neck1", "RuffTopA", "RuffTopB"], 3, 0.5, False, (0, 0.14, 0), 0.8)
        f.cluster(c + V((0, -0.5, 0.4)), V((0, 0.1, 1.0)), (0, 1, 0), ln * 0.6, 0.75, ["Neck3", "Neck2", "Neck1", "RuffTopA", "RuffTopB"], 2, 0.55, False, (0, 0.08, 0), 0.7)
    # the collar behind each cheek, falling over the shoulder (the right side first, the left its mirror)
    for mirror in (False, True):
        t = "Left" if mirror else "Right"
        for i in range(6):
            u = i / 5
            c = V((1.5 + 0.4 * u, 15.2 - 2.2 * u, -11.4 + 1.8 * u))
            f.cluster(c, V((0.2, -0.38 - 0.3 * u, 0.8)), (0, 1, 0), (2.5 + 1.2 * math.sin(math.pi * u)) * k, 0.65, ["Neck2", t + "Ruff1", t + "Ruff2", "Chest"], 3, 0.45, mirror, (0, -0.04, 0), 0.6)
    # the chest tuft: soft, hanging
    for i in range(5):
        u = i / 4
        f.cluster(V((0.0, 10.4 - 2.4 * u, -10.2 + 0.4 * u)), V((0, -0.9, 0.15 + 0.3 * u)), (1, 0, 0), (2.2 + 0.9 * u) * k, 0.7, ["Chest", "ChestTuftA", "ChestTuftB"], 3, 0.55, False, (0, -0.05, 0.05), 0.7)
    # the plume of the tail: a bottle-brush, tongues all round the tail from its root to beyond its tip, longest at the end
    tl = [V(p) for p in P["tail"]]
    for i in range(11):
        t = i / 10
        seg = min(len(tl) - 2, int(t * (len(tl) - 1)))
        a, b = tl[seg], tl[seg + 1]
        c = a.lerp(b, t * (len(tl) - 1) - seg)
        along = (b - a).normalized()
        names = ["Tail%d" % (1 + min(5, int(t * 6.0)))] + ["Tail%d" % (j + 1) for j in range(6) if abs(j - t * 6.0) < 1.6]
        for q in range(4):
            ang = 2 * math.pi * (q + 0.5 * (i % 2)) / 4
            side = V((math.cos(ang), math.sin(ang) * 0.8, 0))
            f.tongue(c + side * 0.4, (along + side * 0.45 + V((0, 0.1, 0))).normalized(), side, (2.6 + 5.6 * t ** 1.3) * pk, 0.8 * (1 - 0.2 * t), names, f.rnd.uniform(-1, 1), (0, 0.1, 0), 0.5)
    # feathers: the back of each foreleg and of each thigh and hock hang with fire
    for mirror in (False, True):
        t = "Left" if mirror else "Right"
        for i in range(5):
            u = i / 4
            f.cluster(V((2.2, 6.8 - 3.5 * u, -7.0 - 0.15 * u)), V((0.05, -0.5, 0.85)), (0, 0, 1), 2.2 + 1.2 * math.sin(math.pi * u), 0.7, ["Front%sFeather" % t, "Front%sLower" % t], 3, 0.4, mirror, (0, -0.06, 0), 0.5)
        for i in range(6):
            u = i / 5
            f.cluster(V((2.2, 9.0 - 5.0 * u, 3.2 + 2.4 * u)), V((0.05, -0.6, 0.75)), (0, 0, 1), 2.4 + 1.4 * math.sin(math.pi * u), 0.72, ["Back%sFeather" % t, "Back%sThigh" % t, "Back%sShin" % t], 3, 0.4, mirror, (0, -0.06, 0), 0.5)
    # a flicker inside each ear: the same two tongues in both
    for mirror in (False, True):
        t = "Left" if mirror else "Right"
        a, b, e = V(BONES[t + "EarA"][1]), V(BONES[t + "EarA"][2]), V(BONES[t + "EarB"][2])
        sx = -1 if mirror else 1
        for q, (hh, ln) in enumerate(((0.35, 2.6), (0.9, 1.9))):
            base = a.lerp(b, hh) + V((sx * -0.1, 0, -0.5))
            f.tongue(base, (e - a).normalized() + V((0, 0, -0.15)), (sx, 0, 0), ln * P["ears"], 0.55, [t + "EarA", t + "EarB"], 0.0, (0, 0.05, -0.05))
    # the stalk that holds the eclipse: a column of fire from the withers to the ring
    s1, s2 = V(BONES["Stalk1"][1]), V(BONES["Stalk2"][2])
    for i in range(5):
        t = i / 4
        f.cluster(s1.lerp(s2, t), (s2 - s1).normalized() * 0.7 + V((0, 0.1, 0.1)), (1, 0, 0) if i % 2 else (0, 0, 1), 2.8 + 1.2 * t, 0.75, ["Stalk1", "Stalk2"], 4, 0.45, False, (0, 0.1, 0), 0.7)
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
        flame(outer, root, V((dx, dy, 0.1)), V((-dy, dx, 0)), length, 1.15 if k % 2 == 0 else 0.85, rnd.uniform(-1, 1), lean=(0, 0, 0.09), thick=0.3, rings=9)
        spans.append((n1, len(outer.verts), a))
    core = Hm.Hi()
    torus(core, ECLIPSE, ECLIPSE_R + 0.05, 0.26, 72, 6)
    for k in range(40):
        a = TAU * k / 40
        dx, dy = math.sin(a), math.cos(a)
        base = V(ECLIPSE) + V((dx * (ECLIPSE_R + 0.2), dy * (ECLIPSE_R + 0.2), 0))
        G.cone(core, base, base + V((dx, dy, 0.1)) * (1.0 + 0.7 * (k % 2)), 0.2, 4)
    return outer, spans, core

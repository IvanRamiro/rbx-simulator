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
        ((0, 9.6, -6.4), (3.1 * cw, 4.5 * cd, 5.9), None),               # the deep chest: an oval, deeper than wide
        ((0, 10.2, -2.0), (2.95 * cw, 3.7 * cd, 4.4), None),              # the barrel
        ((0, 10.9, 1.8), (2.6, 2.7, 3.1), None),                         # the loin, tucked
        ((0, 10.9 + cr, 5.0), (2.8, 3.2, 3.1), None),                    # the haunch
        ((0, 12.3 + wi, -6.6), (2.4, 1.7, 3.2), None),                   # the withers
            ]
    # the neck is thick at its base and tapers to the head; a trapezius slope runs from the withers up the nape; the chest's front is filled so nothing steps
    L += lobe_along((0, 13.4, -5.2), (0, 15.3, -10.6), 2.4, 1.85, 6, 1.0, 1.0, 1.25)           # the trapezius slope along the top of the neck
    L.append(((0, 12.2, -9.6), (2.7, 2.9, 2.6), None))                                         # fills the valley between the chest's front and the neck
    L.append(((0, 10.6, -10.8), (2.3, 3.1, 2.3), None))                                        # the chest's front below it
    n = [V(p) for p in P["neck"]]
    pts = [V((0, 10.8, -5.0)), V((0, 12.0, -6.4))] + n
    rad = [3.5, 3.45, 3.2, 2.8, 2.45, 2.2]
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
    L = [(tuple(at(0.15, 0.9)), (1.68 * hs, 1.75 * hs, 2.0 * hs), None),                   # the cranium: narrow and domed
         (tuple(at(0.36, 1.1)), (1.5 * hs, 1.35 * hs, 1.7 * hs), None)]                   # the forehead rising gently from the stop
    # the muzzle as a lean wedge: a narrow nasal ridge on top, the sides sloping down and out to the flews, everything narrowing steadily to the nose
    L += lobe_along(at(0.42, 0.75), at(0.96, 0.3), 0.58 * hs, 0.32 * hs, 7, 0.85, 1.0)
    shift = V(P["head_at"]) - V(BONES["Head"][1])
    for s in (-1, 1):
        L += lobe_along(at(0.44, 0.2, s * 0.55), at(0.95, 0.0, s * 0.3), 0.55 * hs, 0.3 * hs, 7, 0.85, 0.9)       # the muzzle's sides
        L += lobe_along(at(0.44, -0.35, s * 0.6), at(0.9, -0.5, s * 0.36), 0.45 * hs, 0.3 * hs, 7, 0.8, 1.0)     # the flews: the jowl line
        L.append((tuple(at(0.40, 1.5, s * 0.75)), (0.55 * hs, 0.25 * hs, 0.6 * hs), None))                      # a soft supraorbital ridge (the scowl)
        L.append((tuple(at(0.28, 0.0, s * 1.05)), (0.45 * hs, 0.75 * hs, 1.0 * hs), None))                    # a subtle cheek
        tag = "Left" if s < 0 else "Right"
        a_, b_ = (V(x) + shift + V((s * 0.25, 0.25, 0)) for x in BONES[tag + "EarA"][1:3])      # the ears set a little higher and wider on the skull
        e = V(BONES[tag + "EarB"][2]) + shift + V((s * 0.25, 0.25, 0))
        k = P["ears"]
        L += lobe_along(a_, b_, 0.95 * k, 0.82 * k, 4, 0.28, 1.0, 1.1)
        L += lobe_along(b_, e, 0.82 * k, 0.12 * k, 5, 0.28, 1.0, 1.1)
    return L


def jaw_lobes(P):
    """The lower jaw: narrower than the muzzle so the flews overhang it, a rounded chin, a tongue lying on the floor of the mouth."""
    at, hs = head_frame(P)
    L = lobe_along(at(0.34, -0.78), at(0.9, -0.82), 0.85 * hs, 0.4 * hs, 7, 0.82, 0.8)
    L.append((tuple(at(0.28, -0.8)), (0.95 * hs, 0.9 * hs, 0.95 * hs), None))
    L.append((tuple(at(0.88, -0.86)), (0.3 * hs, 0.3 * hs, 0.32 * hs), None))
    return L


def hi_blob(name, coll, mat, lobes, voxel, smooth=0.85, rough=0.015, iterations=6):
    o = G.blob(name, coll, mat, lobes, voxel=voxel, smooth=smooth, rough=rough, chisel="TG3Chisel")
    return o


# ---------------------------------------------------------------- small hard parts
def teeth(P, hi_up, hi_low):
    """Canines and a carnassial show at the lip line; the incisors and premolars sit behind the flews (their tips stop above the lip's edge); every tooth a
    little different in length and curved back a touch, none a regular rivet."""
    at, hs = head_frame(P)
    R = random.Random(21)
    curve = lambda f, h0, h1, x, c: (at(f, h0, x), at(f + c, h1, x))
    for s in (-1, 1):
        # upper canine (long, curved back), premolars (hidden), carnassial (shows a little)
        a, b = curve(0.90, -0.28, -1.0, s * 0.62, 0.025)
        G.cone(hi_up, a, b, 0.17 * hs, 6)
        for f, x in ((0.84, 0.56), (0.78, 0.6), (0.72, 0.64)):
            k = R.uniform(0.85, 1.15)
            a, b = curve(f, -0.28, -0.58 * k, s * x, 0.01)
            G.cone(hi_up, a, b, 0.1 * hs, 5)
        a, b = curve(0.65, -0.28, -0.8, s * 0.7, 0.03)
        G.cone(hi_up, a, b, 0.15 * hs, 5)
        # lower canine (shows beside the upper one), premolars hidden, carnassial
        a, b = curve(0.915, -1.05, -0.45, s * 0.3, -0.02)
        G.cone(hi_low, a, b, 0.15 * hs, 6)
        for f, x in ((0.83, 0.34), (0.77, 0.37), (0.71, 0.4)):
            k = R.uniform(0.85, 1.15)
            a, b = curve(f, -1.05, -0.72 * k, s * x, -0.01)
            G.cone(hi_low, a, b, 0.1 * hs, 5)
        a, b = curve(0.64, -1.05, -0.68, s * 0.42, -0.02)
        G.cone(hi_low, a, b, 0.12 * hs, 5)
    for k, x in enumerate((-0.3, -0.18, -0.06, 0.06, 0.18, 0.3)):
        f = 0.965 - 0.05 * (x / 0.3) ** 2
        ln = R.uniform(0.2, 0.3)
        G.cone(hi_up, at(f, -0.28, x), at(f + 0.008, -0.28 - ln, x), R.uniform(0.09, 0.13) * hs, 5)
        ln = R.uniform(0.3, 0.4)
        G.cone(hi_low, at(f - 0.01, -1.05, x * 0.8), at(f - 0.018, -1.05 + ln, x * 0.8), R.uniform(0.08, 0.12) * hs, 5)


def claws(hi):
    """A dark-ivory claw on each toe tip."""
    for name in ("FrontLeftToes", "FrontRightToes", "BackLeftToes", "BackRightToes"):
        kn, tp = V(BONES[name][1]) + V((0, 0.3, 0)), V(BONES[name][2]) + V((0, 0.3, 0))
        for dx in (-0.62, -0.21, 0.21, 0.62):
            end = V((tp.x + dx * 1.25, tp.y - 0.05, tp.z + (0.15 if abs(dx) > 0.5 else -0.2)))
            base = end + V((0, 0.12, 0))
            G.cone(hi, base, end + V((0, -0.35, -0.55)), 0.2, 6)


def nose_pad(hi, P):
    """A small matte rhinarium: a narrow pad, two nostril wings, a nostril in each (material 1) and a vertical philtrum groove running down to the lip."""
    at, hs = head_frame(P)
    G.sphere(hi, at(0.985, 0.3), 0.5, nu=14, nv=9, radii=(0.42 * hs, 0.28 * hs, 0.3 * hs))
    for s in (-1, 1):
        G.sphere(hi, at(1.01, 0.24, s * 0.2), 0.3, nu=10, nv=7, radii=(0.16 * hs, 0.22 * hs, 0.2 * hs))
        G.sphere(hi, at(1.04, 0.22, s * 0.19), 0.2, nu=8, nv=6, radii=(0.08 * hs, 0.13 * hs, 0.07 * hs), mat=1)
    G.sphere(hi, at(0.995, 0.0), 0.2, nu=8, nv=6, radii=(0.03 * hs, 0.1 * hs, 0.3 * hs), mat=1)   # the philtrum


def eyes(P, skull):
    """Almond gold eyes under a scowling brow, set on the skull's surface by a ray: (iris Hi, pupil Hi, lids Hi). Round black pupils."""
    iris, pupil, lids = Hm.Hi(), Hm.Hi(), Hm.Hi()
    hs = P["hs"]
    for s in (-1, 1):
        n = V((s * 0.42, 0.14, -0.88)).normalized()
        c = G.surface_along(skull, V((s * 1.0, 17.15, -17.0)), V((0, 0.08, -1.0)), 5.0) - n * 0.12
        G.eye(iris, pupil, lids, c, n, V((s * 0.0, -0.35, -1.0)), 0.5 * hs, 0.37 * hs, tilt=0.62, bulge=0.12, lid=0.34, droop=0.55, lower=0.17, slit=0.55, pupil_height=0.8)
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
    n = [V(p) for p in P["neck"]]
    axis_pts = [V((0, 10.8, -5.0)), V((0, 12.0, -6.4))] + n
    rads = [3.4, 3.35, 3.1, 2.75, 2.4, 2.2]
    ring_bones = ["Neck1", "Neck2", "Neck3", "RuffTopA", "RuffTopB", "LeftRuff1", "LeftRuff2", "RightRuff1", "RightRuff2", "ChestTuftA", "ChestTuftB", "Chest"]

    def axis_at(t):
        """Point, direction and radius on the neck's axis, t 0 at the chest's front to 1 under the head."""
        x = t * (len(axis_pts) - 1)
        i = min(len(axis_pts) - 2, int(x))
        c = axis_pts[i].lerp(axis_pts[i + 1], x - i)
        d = (axis_pts[i + 1] - axis_pts[i]).normalized()
        return c, d, rads[i] + (rads[i + 1] - rads[i]) * (x - i)

    # ONE flame ruff round the neck: rings of tongues from the chest's front to the head, each pointing back down the neck and a little outward; the ones underneath
    # make the forechest tuft, the ones on top the mane, the ones either side the collar: the same tongues, so it reads as one mass of fire
    stations, around = 8, 9
    for si in range(stations):
        t = si / (stations - 1) * 0.86
        c, d, r = axis_at(t)
        e1 = V((1, 0, 0))
        e2 = d.cross(e1).normalized()
        for q in range(around):
            a = 2 * math.pi * q / around + (math.pi / around if si % 2 else 0.0)
            # a tongue and its mirror image share their numbers: the random generator is keyed by station and the angle's distance from straight up
            R = random.Random(1000 * si + int(round(abs(math.sin(a / 2) * 100))))
            out = e1 * math.cos(a) + e2 * math.sin(a)
            tang = e1 * -math.sin(a) + e2 * math.cos(a)
            base = c + out * (r * 0.72)
            direction = (-d * 1.0 + out * 0.55 + V((0, -0.1, 0))).normalized()
            length = (2.4 + 1.6 * math.sin(math.pi * min(1.0, t * 1.1))) * k * R.uniform(0.85, 1.15) * (1.2 if abs(math.cos(a / 2)) < 0.4 else 1.0)
            f.tongue(base, direction, tang, length, R.uniform(0.95, 1.25), ring_bones, R.uniform(-1, 1) * (1 if math.sin(a) >= 0 else -1), (0, 0.06, 0))
    # the plume of the tail: a bottle-brush of wide overlapping tongues all round the tail, longest at its end
    tl = [V(p) for p in P["tail"]]
    for i in range(14):
        t = i / 13
        seg = min(len(tl) - 2, int(t * (len(tl) - 1)))
        a, b = tl[seg], tl[seg + 1]
        c = a.lerp(b, t * (len(tl) - 1) - seg)
        along = (b - a).normalized()
        names = ["Tail%d" % (1 + min(5, int(t * 6.0)))] + ["Tail%d" % (j + 1) for j in range(6) if abs(j - t * 6.0) < 1.6]
        for q in range(4):
            ang = 2 * math.pi * (q + 0.5 * (i % 2)) / 4
            side = V((math.cos(ang), math.sin(ang) * 0.8, 0))
            tang = along.cross(side).normalized()
            R = random.Random(5000 + 10 * i + int(round(abs(math.sin(ang / 2) * 100))))
            f.tongue(c + side * 0.4, (along + side * 0.4 + V((0, 0.08, 0))).normalized(), tang, (2.5 + 5.5 * t ** 1.3) * pk * R.uniform(0.9, 1.1), 1.05 * (1 - 0.2 * t), names, R.uniform(-1, 1), (0, 0.1, 0))
    # feathers: the back of each foreleg and of each thigh and hock hang with fire (right side first, the left its mirror)
    for mirror in (False, True):
        t = "Left" if mirror else "Right"
        for i in range(5):
            u = i / 4
            f.cluster(V((1.9, 6.8 - 3.5 * u, -6.8 - 0.15 * u)), V((0.05, -0.5, 0.85)), (0, 0, 1), 2.2 + 1.2 * math.sin(math.pi * u), 0.85, ["Front%sFeather" % t, "Front%sLower" % t], 3, 0.35, mirror, (0, -0.06, 0), 0.5)
        for i in range(6):
            u = i / 5
            f.cluster(V((2.2, 9.0 - 5.0 * u, 3.2 + 2.4 * u)), V((0.05, -0.6, 0.75)), (0, 0, 1), 2.4 + 1.4 * math.sin(math.pi * u), 0.9, ["Back%sFeather" % t, "Back%sThigh" % t, "Back%sShin" % t], 3, 0.35, mirror, (0, -0.06, 0), 0.5)
    # a flicker inside each ear: the same two tongues in both
    for mirror in (False, True):
        t = "Left" if mirror else "Right"
        a, b, e = V(BONES[t + "EarA"][1]), V(BONES[t + "EarA"][2]), V(BONES[t + "EarB"][2])
        sx = -1 if mirror else 1
        for q, (hh, ln) in enumerate(((0.35, 2.6), (0.9, 1.9))):
            base = a.lerp(b, hh) + V((sx * -0.1, 0, -0.5))
            f.tongue(base, (e - a).normalized() + V((0, 0, -0.15)), (sx, 0, 0), ln * P["ears"], 0.6, [t + "EarA", t + "EarB"], 0.0, (0, 0.05, -0.05))
    # the stalk that holds the eclipse: a column of fire from the withers to the ring
    s1, s2 = V(BONES["Stalk1"][1]), V(BONES["Stalk2"][2])
    for i in range(5):
        t = i / 4
        f.cluster(s1.lerp(s2, t), (s2 - s1).normalized() * 0.7 + V((0, 0.1, 0.1)), (1, 0, 0) if i % 2 else (0, 0, 1), 2.8 + 1.2 * t, 0.9, ["Stalk1", "Stalk2"], 4, 0.45, False, (0, 0.1, 0), 0.7)
    return f


# ---------------------------------------------------------------- constellations (high-detail only: baked into the colour map)
FIGURES = [   # (z, y) of each star in a flank's side view, joined in order; the left flank is the mirror image
    [(-3.6, 11.4), (-2.3, 12.5), (-0.8, 11.7), (0.4, 12.8), (1.8, 12.0), (3.2, 12.7), (4.2, 11.3)],            # a W along the back's flank
    [(-4.2, 9.2), (-2.9, 10.0), (-1.6, 9.5), (-0.3, 10.3), (0.2, 8.8), (-1.2, 8.3), (-2.4, 8.6)],              # a ladle low on the ribs
    [(-8.6, 11.4), (-7.4, 12.3), (-6.2, 11.7), (-6.0, 10.3), (-7.3, 10.0)],                                      # a small ring over the shoulder
    [(3.4, 10.6), (4.6, 11.5), (5.9, 10.9), (6.3, 9.4), (5.1, 8.8), (3.8, 9.2), (3.0, 9.9)],                    # a ring on the haunch
    [(1.0, 7.8), (2.4, 8.4), (3.8, 7.9), (4.9, 8.5)],                                                            # a short line on the thigh
]


def constellations(body):
    """Dots of varied size and thin lines joining them, laid on the body's flanks (a ray from outside onto the surface), in one Hi."""
    hi = Hm.Hi()
    rnd = random.Random(77)
    sizes = {}

    def on_surface(sx, z, y):
        return G.surface_along(body, (sx * 8.0, y, z), (sx, 0, 0), 6.0)

    for sx in (1, -1):
        for fig, pts in enumerate(FIGURES):
            proj = []
            for (z, y) in pts:
                try:
                    proj.append(on_surface(sx, z, y))
                except AssertionError:
                    proj.append(None)
            for i, p in enumerate(proj):
                if p is None:
                    continue
                key = (fig, i)
                if key not in sizes:
                    sizes[key] = rnd.uniform(0.17, 0.36)
                r = sizes[key]
                G.sphere(hi, V(p) + V((sx * 0.03, 0, 0)), r, nu=10, nv=6, radii=(0.05, r, r))
            for i in range(len(pts) - 1):
                if proj[i] is None or proj[i + 1] is None:
                    continue
                path = []
                for j in range(7):
                    u = j / 6
                    z = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u
                    y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u
                    try:
                        path.append(V(on_surface(sx, z, y)) + V((sx * 0.02, 0, 0)))
                    except AssertionError:
                        path = []
                        break
                if len(path) == 7:
                    Hm.htube(hi, [tuple(q) for q in path], lambda t_: 0.05, sides=4, per=1, uv_scale=1.0, tip=False, wobble=0.0)
    return hi


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

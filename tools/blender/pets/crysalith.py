"""Crysalith, "The Eternal Frost" (Divine, Exclusive Egg): an ancient crystalline guardian, modelled by hand piece by piece in bmesh.

The idea: a glacier that learned to walk. A heavy frost-draconic quadruped whose crystal is grown bone, not ornament: it pushes up out of
the body where the skeleton is closest to the skin (the withers, the shoulder blades, the spine, the hip points, the brow, the antler
pedicles, the end of the tail) and every formation has a root, a collar where it breaks the skin, a body and a faceted termination.
A deep chest and heavy shoulders under an elevated, armoured neck; a long draconic skull with a broad muzzle, a nasal bridge, brow ridges
over deep sockets and calm, narrow arctic-cyan eyes; two great branching crystal antlers; split cloven hooves; a long armoured tail that
ends in a plume of crystal. The body is solid deep glacial blue under layered frosted armour plates; only the crystals are pale and glassy.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/blender/pets/crysalith.py -- <stage> [--review DIR]

Stages, each building everything before it: blockout | anatomy | antlers | crystals | materials | bake | export | review ("all" = review).
Each stage renders front, side, back, top and three-quarter views (and a head close-up) into the review folder; blockout, anatomy and
crystals also write their stage .blend (Crysalith_Blockout / _Anatomy / _Crystals), and the last stage writes Crysalith_Final.blend.

Faces -Y, Z up, ground at z = 0, 1 unit = 1 metre. The game animates it as a jointed pet (PetRig.Profiles.Crysalith, animateCrysalith):
one mesh per joint, Crysalith_{Body,Head,Antlers,LegFL,LegFR,LegBL,LegBR,Tail}, each with one baked set (colour, normal, roughness), a
2 cm cube Crysalith_Pivot_<Joint> at each joint's centre of rotation, and Crysalith_Point_Antlers_TipL / _TipR at the antlers' highest tips.

What touches what: each leg's top is a rounded mass centred on its pivot inside the shoulder or hip, so a swing turns it in place under the
body's skin; the head's skull base and throat latch sit over the top of the neck, round the head's pivot; the antlers' beams are sunk in
bony pedicles on the skull, ringed by a crystal coronet; the tail's root mass is centred on its pivot inside the rump; every plate and
crystal is sunk into what carries it.
"""
import math
import os
import random
import subprocess
import sys
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit as K  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGES = ["blockout", "anatomy", "antlers", "crystals", "materials", "bake", "export", "review"]
STAGE = ARGS[0] if ARGS else "anatomy"
if STAGE == "all":
    STAGE = "review"
LEVEL = STAGES.index(STAGE)
REVIEW = ARGS[ARGS.index("--review") + 1] if "--review" in ARGS else os.path.join(K.ROOT, "renders", "pets", "ExclusiveEgg", "Crysalith_stages")
os.makedirs(REVIEW, exist_ok=True)

PET = "Crysalith"
N = PET + "_"
TAU = 2 * math.pi
X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))
Z = Vector((0, 0, 1))


def V(*a):
    return Vector(a)


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def spow(x, p):
    return math.copysign(abs(x) ** p, x)


def turn(v, axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis.normalized()) @ v


def rng_for(*key):
    return random.Random(zlib.crc32("|".join(str(k) for k in key).encode()))


def mirror(v, side):
    return Vector((v.x * side, v.y, v.z))


# ======================================================================================================================================
# the frame of it (metres; ground at z = 0; it faces -Y; +X is its left)
# ======================================================================================================================================
PIVOT = {
    "Body": V(0, 0.0, 0.95),
    "Head": V(0, -1.000, 1.700),     # the top of the neck, inside the skull base
    "LegFL": V(0.165, -0.470, 1.000),  # inside the shoulder: the top of the upper arm
    "LegFR": V(-0.165, -0.470, 1.000),
    "LegBL": V(0.160, 0.430, 1.020),  # inside the hip: the head of the thigh
    "LegBR": V(-0.160, 0.430, 1.020),
    "Tail": V(0, 0.690, 1.065),      # the root of the tail, inside the rump
}

# The body, rump to skull: each knot is a section between its top point and its bottom point (y, z), with a half-width, a bias that
# lifts (+) or drops (-) its widest level, the squareness of its upper and lower halves, and a dorsal ridge. Rings tilt progressively from
# upright (the trunk) to leaning back (the neck), so the chest front and the crest of the neck come out of one surface.
BODY = [
    # (top), (bottom), half-width, bias, p top, p bottom, ridge
    ((0.792, 1.100), (0.792, 0.995), 0.080, 0.00, 2.2, 2.0, 0.00),   # 0  round the tail's root
    ((0.748, 1.172), (0.738, 0.840), 0.178, 0.05, 2.3, 2.0, 0.00),   # 1  the buttocks
    ((0.650, 1.225), (0.642, 0.672), 0.262, -0.06, 2.5, 2.1, 0.02),  # 2  hamstrings, down over the thighs
    ((0.505, 1.246), (0.505, 0.676), 0.306, 0.00, 2.7, 2.2, 0.03),   # 3  the hips
    ((0.350, 1.226), (0.350, 0.762), 0.276, 0.10, 2.7, 2.2, 0.03),   # 4  loin: the belly tucked up before the stifle
    ((0.195, 1.206), (0.195, 0.722), 0.270, 0.00, 2.6, 2.3, 0.03),   # 5  flank
    ((0.030, 1.206), (0.030, 0.640), 0.310, -0.08, 2.6, 2.3, 0.03),  # 6  belly barrel
    ((-0.140, 1.226), (-0.140, 0.560), 0.335, -0.08, 2.6, 2.3, 0.03),  # 7  ribcage
    ((-0.290, 1.262), (-0.290, 0.525), 0.350, 0.00, 2.6, 2.4, 0.03),  # 8  girth: the deep chest
    ((-0.420, 1.300), (-0.425, 0.525), 0.350, 0.10, 2.6, 2.4, 0.03),  # 9  withers and shoulders
    ((-0.515, 1.335), (-0.585, 0.545), 0.335, 0.12, 2.6, 2.4, 0.02),  # 10 the shoulders' front
    ((-0.585, 1.400), (-0.750, 0.640), 0.305, 0.08, 2.5, 2.4, 0.02),  # 11 point of the shoulder, chest front
    ((-0.645, 1.475), (-0.870, 0.770), 0.270, 0.00, 2.4, 2.4, 0.02),  # 12 pectorals' front
    ((-0.700, 1.555), (-0.950, 0.990), 0.225, 0.00, 2.3, 2.3, 0.02),  # 13 base of the neck: the breast's front
    ((-0.752, 1.625), (-0.960, 1.170), 0.190, 0.00, 2.3, 2.2, 0.02),  # 14 neck: the throat set back over the breast
    ((-0.800, 1.690), (-0.985, 1.340), 0.170, 0.00, 2.3, 2.2, 0.02),  # 15 neck
    ((-0.845, 1.745), (-1.015, 1.490), 0.155, 0.00, 2.3, 2.2, 0.02),  # 16 throat
    ((-0.885, 1.790), (-1.050, 1.615), 0.140, 0.00, 2.3, 2.2, 0.01),  # 17 under the skull
]
BODY_REAR_CAP = V(0, 0.825, 1.048)
BODY_TOP_CAP = V(0, -1.005, 1.720)

# muscle masses, sculpted into the trunk after lofting (proportional editing along the normals): centre (left side), radii, amount
MUSCLES = [
    ("scapula", V(0.250, -0.450, 1.150), (0.15, 0.22, 0.22), 0.060),
    ("triceps", V(0.290, -0.355, 0.760), (0.12, 0.14, 0.16), 0.045),
    ("pectoral", V(0.130, -0.810, 0.740), (0.14, 0.13, 0.19), 0.050),
    ("ribcage", V(0.300, -0.150, 0.940), (0.08, 0.24, 0.22), 0.022),
    ("abdomen", V(0.260, 0.120, 0.760), (0.10, 0.20, 0.08), -0.014),
    ("deltoid", V(0.230, -0.600, 0.960), (0.10, 0.11, 0.13), 0.020),
    ("girth", V(0.290, -0.200, 0.700), (0.10, 0.16, 0.10), -0.012),
    ("flankfold", V(0.270, 0.230, 0.700), (0.08, 0.10, 0.08), -0.014),
    ("hippoint", V(0.236, 0.360, 1.150), (0.08, 0.08, 0.08), 0.022),
    ("glute", V(0.215, 0.565, 1.040), (0.14, 0.17, 0.19), 0.040),
    ("quadriceps", V(0.250, 0.360, 0.860), (0.11, 0.17, 0.17), 0.042),
    ("hamstring", V(0.190, 0.680, 0.880), (0.10, 0.10, 0.14), 0.020),
    ("neckband", V(0.125, -0.860, 1.200), (0.06, 0.12, 0.20), 0.014),
]
MIDLINE = [
    ("sternum", V(0, -0.845, 0.800), (0.035, 0.10, 0.16), -0.014),
    ("spinegroove", V(0, 0.150, 1.210), (0.025, 0.40, 0.04), -0.006),
]

# legs (the left ones; the right ones mirror them): the joints from the pivot down, and (side, front-back) half-sizes along the limb
LEGS = {
    "fore": {"pts": [V(0.165, -0.470, 1.000), V(0.250, -0.402, 0.600), V(0.262, -0.470, 0.300), V(0.262, -0.462, 0.165),
                     V(0.262, -0.508, 0.100)],
             # dome, under pivot, pivot, upper arm, elbow, forearm muscle, forearm low, wrist, cannon, fetlock, pastern, coronet, end
             "rad": [(0.060, 0.068), (0.094, 0.115), (0.112, 0.148), (0.118, 0.152), (0.106, 0.130), (0.102, 0.122), (0.074, 0.084),
                     (0.080, 0.088), (0.064, 0.071), (0.075, 0.082), (0.062, 0.066), (0.066, 0.070), (0.056, 0.060)]},
    "hind": {"pts": [V(0.160, 0.430, 1.020), V(0.262, 0.255, 0.660), V(0.262, 0.525, 0.360), V(0.260, 0.485, 0.165),
                     V(0.260, 0.433, 0.100)],
             # dome, under pivot, pivot, thigh, stifle, gaskin, gaskin low, hock, cannon, fetlock, pastern, coronet, end
             "rad": [(0.062, 0.070), (0.100, 0.132), (0.126, 0.188), (0.136, 0.192), (0.114, 0.138), (0.100, 0.128), (0.072, 0.090),
                     (0.076, 0.096), (0.062, 0.069), (0.073, 0.080), (0.060, 0.064), (0.064, 0.068), (0.054, 0.058)]},
}
# sturdier legs: everything below the elbow and the stifle thickened (no thin legs under a heavy body)
for _k in LEGS:
    _m = {4: 1.30, 5: 1.55, 6: 1.42, 7: 1.25}                    # the forearm and the gaskin: heavy, a guardian's legs
    LEGS[_k]["rad"] = [(a * (1.05 if i < 5 else 1.17) * _m.get(i, 1.0 if i < 4 else 1.10), b * (1.05 if i < 5 else 1.14) * _m.get(i, 1.0 if i < 4 else 1.10))
                       for i, (a, b) in enumerate(LEGS[_k]["rad"])]
    LEGS[_k]["pts"][4] = LEGS[_k]["pts"][4] + Z * 0.012
# the tops of the legs (the dome on the pivot, the upper arm, the thigh) slimmer: they turn in place under the skin of the shoulder and the
# hip, and must stay under it through the game's whole swing
for _k, _top in (("fore", (0.64, 0.80)), ("hind", (0.54, 0.74))):
    LEGS[_k]["rad"] = [((a * _top[0], b * _top[1]) if i < 4 else (a, b)) for i, (a, b) in enumerate(LEGS[_k]["rad"])]
HOOF_K = 1.28                     # the hooves' size
STANCE = {"LegFL": -3.0, "LegFR": 2.0, "LegBL": 2.5, "LegBR": -2.0}     # degrees about X through the pivot (negative: the hoof forward)

TAIL_PATH = [V(0, 0.690, 1.065), V(0, 0.865, 1.030), V(0, 1.060, 0.955), V(0, 1.265, 0.905), V(0, 1.460, 0.915), V(0, 1.625, 0.985),
             V(0, 1.745, 1.090)]
TAIL_R = [0.225, 0.192, 0.152, 0.118, 0.092, 0.073, 0.060]



def _trunk(v, k=0.86, y0=-0.42):
    """the trunk's length, set once: everything behind the shoulders drawn in toward them"""
    return V(v.x, y0 + (v.y - y0) * k, v.z) if v.y > y0 else v.copy()


BODY = [((_trunk(V(0, *t)).y, t[1]), (_trunk(V(0, *b)).y, b[1])) + tuple(rest) for t, b, *rest in BODY]
BODY_REAR_CAP = _trunk(BODY_REAR_CAP)
PIVOT = {k: _trunk(v) for k, v in PIVOT.items()}
MUSCLES = [(n, _trunk(c), r, a) for n, c, r, a in MUSCLES]
MIDLINE = [(n, _trunk(c), r, a) for n, c, r, a in MIDLINE]
LEGS["hind"]["pts"] = [_trunk(p) for p in LEGS["hind"]["pts"]]
TAIL_PATH = [_trunk(TAIL_PATH[0])] + [p + (_trunk(TAIL_PATH[0]) - TAIL_PATH[0]) for p in TAIL_PATH[1:]]
LIFT = 0.05                       # the body stands this much higher than it is drawn: longer legs under it
BODY = [((t[0], t[1] + LIFT), (b[0], b[1] + LIFT)) + tuple(rest) for t, b, *rest in BODY]
NECK_UP = 0.04                    # the neck carries the head this much higher (the upper rings rise most)
_w = {12: 0.10, 13: 0.28, 14: 0.48, 15: 0.68, 16: 0.86, 17: 1.0}
NECK_FWD = 0.13                   # and carries it forward of the chest: a forward-raised neck, not a column
BODY = [((t[0] - NECK_FWD * _w.get(i, 0.0), t[1] + NECK_UP * _w.get(i, 0.0)),
         (b[0] - NECK_FWD * 0.8 * _w.get(i, 0.0), b[1] + NECK_UP * _w.get(i, 0.0) * 0.85)) + tuple(rest)
        for i, (t, b, *rest) in enumerate(BODY)]
BODY_REAR_CAP, BODY_TOP_CAP = BODY_REAR_CAP + Z * LIFT, BODY_TOP_CAP + Z * (LIFT + NECK_UP) - Y * NECK_FWD
PIVOT = {k: v + Z * (LIFT + (NECK_UP if k == 'Head' else 0.0)) - Y * (NECK_FWD if k == 'Head' else 0.0) for k, v in PIVOT.items()}
MUSCLES = [(n, c + Z * LIFT, r, a) for n, c, r, a in MUSCLES]
MIDLINE = [(n, c + Z * LIFT, r, a) for n, c, r, a in MIDLINE]
TAIL_PATH = [p + Z * LIFT for p in TAIL_PATH]
for _k in LEGS:
    _p = LEGS[_k]["pts"]
    LEGS[_k]["pts"] = [_p[0] + Z * LIFT, _p[1] + Z * LIFT, _p[2] + Z * LIFT * 0.6, _p[3] + Z * LIFT * 0.2, _p[4]]

# materials: ten identities in the .blend, baked into one colour map per game piece
MATS = ["Body", "NeckChestArmor", "Face", "Antler", "CrystalArmor", "Hoof", "Toe", "Tail", "Eye", "Detail"]
M = {name: i for i, name in enumerate(MATS)}
SMOOTH = {M["Body"], M["Face"], M["Tail"], M["Eye"]}     # skin is smooth; whatever is built as a hard part keeps its facets      # skin is smooth; plates, crystals, antlers and hooves keep hard facets


# ======================================================================================================================================
# a mesh under construction
# ======================================================================================================================================
class Geo:
    """A bmesh with the per-vertex values the materials read: fu (0 at a part's root, 1 at its tip), fv (-1..1 across it), seed (per part),
    shade and under (per-material flags), and a per-face random 'facet' (each crystal face catches the light differently)."""
    ATTRS = ("fu", "fv", "seed", "shade", "under")

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.L = {a: self.bm.verts.layers.float.new(a) for a in self.ATTRS}
        self.F = self.bm.faces.layers.float.new("facet")
        self.HD = self.bm.faces.layers.int.new("hard")
        self.rng = rng_for(name, "facets")
        self.count = 0
        self.hard = 0          # while > 0, new faces are hard (plates, crystals, fins, antlers keep flat facets on smooth materials)

    def vert(self, co, **a):
        v = self.bm.verts.new(co)
        for k, x in a.items():
            v[self.L[k]] = x
        return v

    def face(self, vs, mat):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = mat
        f[self.F] = self.rng.random()
        f[self.HD] = 1 if self.hard else 0
        return f

    def tree(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.normal_update()
        return BVHTree.FromBMesh(self.bm)

    def separate(self, passes=12):
        """Where two separate parts overlap in one plane (within 1.3 mm, facing the same way), the engine would flicker between them:
        turn the smaller about its own root (its least-fu vertices, sunk in what carries it) by 3 degrees until no such pair is left."""
        bm = self.bm
        bm.verts.ensure_lookup_table()
        island, size, k = {}, {}, 0
        for v in bm.verts:
            if v.index in island:
                continue
            stack = [v]
            island[v.index] = k
            while stack:
                x = stack.pop()
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y.index not in island:
                        island[y.index] = k
                        stack.append(y)
            k += 1
        members = {}
        for v in bm.verts:
            members.setdefault(island[v.index], []).append(v)
        fu = self.L["fu"]
        moved = 0
        turns = {}
        bm.faces.ensure_lookup_table()
        hardisl = {island[f.verts[0].index] for f in bm.faces if f[self.HD]}
        for _ in range(passes):
            bm.faces.ensure_lookup_table()
            bm.normal_update()
            tree = BVHTree.FromBMesh(bm)
            moves = {}
            for f in bm.faces:
                n = f.normal
                cen = f.calc_center_median()
                for q in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                    for _, _, j, _ in tree.find_nearest_range(q, 0.0013):
                        if j is None or j == f.index:
                            continue
                        g2 = bm.faces[j]
                        if n.dot(g2.normal) < 0.995:      # facing the same way: what the engine would flicker between
                            continue
                        a, b = island[f.verts[0].index], island[g2.verts[0].index]
                        if a == b:
                            continue
                        mine = a if (len(members[a]), a) <= (len(members[b]), b) else b
                        if mine not in hardisl:          # only hard parts (plates, crystals) may be turned; skin, eyes, lids never
                            continue
                        if mine not in moves:
                            moves[mine] = (q.copy(), n.orthogonal().normalized())
            if not moves:
                break
            moves = {i: m for i, m in moves.items() if turns.get(i, 0) < 3}       # never more than 9 degrees for any part
            if not moves:
                break
            for i, (pivot, axis) in moves.items():
                turns[i] = turns.get(i, 0) + 1
                low = min(v[fu] for v in members[i])
                roots = [v.co for v in members[i] if v[fu] <= low + 1e-4]
                if roots and len(roots) < len(members[i]):
                    pivot = sum(roots, Vector()) / len(roots)
                rot_ = Matrix.Rotation(math.radians(3.0), 3, axis)
                for v in members[i]:
                    v.co = pivot + rot_ @ (v.co - pivot)
            moved += len(moves)
        return moved

    def finish(self, coll, flat=False):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        n = self.separate()
        if n:
            print("SEPARATED", self.name, n, flush=True)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
        for v in bm.verts:                       # hooves rest on the ground, never through it
            if v.co.z < 0.0:
                v.co.z = 0.0
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        idx = [0] * len(me.polygons)
        me.polygons.foreach_get("material_index", idx)
        hard = [0] * len(me.polygons)
        me.attributes["hard"].data.foreach_get("value", hard)
        me.polygons.foreach_set("use_smooth", [(not flat) and i in SMOOTH and not h for i, h in zip(idx, hard)])
        me.attributes.remove(me.attributes["hard"])
        o = bpy.data.objects.new(self.name, me)
        coll.objects.link(o)
        return o


def loft(g, rings, mat, cap0=True, cap1=True, attrs=None, loop=False, cap_attrs=None):
    """Bridges rings of equal count. A cap is True (a fan to the ring's middle), a Vector (a fan to that point) or False."""
    R = []
    for i, ring in enumerate(rings):
        a = attrs(i) if attrs else {}
        R.append([g.vert(p, **a) for p in ring])
    m, n = len(rings[0]), len(R)
    for i in range(n if loop else n - 1):
        A, B = R[i], R[(i + 1) % n]
        for k in range(m):
            k2 = (k + 1) % m
            g.face((A[k], A[k2], B[k2], B[k]), mat)
    if not loop:
        for e, (cap, ring) in enumerate(((cap0, R[0]), (cap1, R[-1]))):
            if cap is False:
                continue
            c = (sum((v.co for v in ring), Vector()) / m) if cap is True else cap
            a = cap_attrs[e] if cap_attrs else (attrs(0 if e == 0 else n - 1) if attrs else {})
            cv = g.vert(c, **a)
            for k in range(m):
                g.face((ring[k], ring[(k + 1) % m], cv), mat)
    return R


def sculpt(g, verts, centre, radii, amount, frame=None, along=None):
    """Proportional editing: moves the verts inside an ellipsoid (radii along world X, Y, Z, or along a frame's three axes) along their
    normals (or along a given direction) with a smooth falloff."""
    g.bm.normal_update()
    moves = []
    for v in verts:
        d = v.co - centre
        if frame:
            d = V(d.dot(frame[0]), d.dot(frame[1]), d.dot(frame[2]))
        q = (d.x / radii[0]) ** 2 + (d.y / radii[1]) ** 2 + (d.z / radii[2]) ** 2
        if q < 1.0:
            w = (1.0 - q) ** 2
            moves.append((v, (along if along is not None else v.normal) * (amount * w)))
    for v, mv in moves:
        v.co += mv


def catmull(pts, per=4):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-2].copy())
    return out


def frames(pts, side=X):
    """Per point: tangent t, a across (toward `side`), b = t x a."""
    out = []
    n = len(pts)
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        a = side - t * t.dot(side)
        a = a.normalized() if a.length > 1e-6 else t.orthogonal().normalized()
        out.append((t, a, t.cross(a).normalized()))
    return out


def oval(c, A, B, ra, rb, n, p=2.0, phase=0.0, jitter=None):
    out = []
    for k in range(n):
        th = phase + TAU * k / n
        j = jitter[k] if jitter else 1.0
        out.append(c + A * (ra * j * spow(math.cos(th), 2 / p)) + B * (rb * j * spow(math.sin(th), 2 / p)))
    return out


def cast(tree, p, d, reach=1.2):
    """The outermost surface point seen from outside along -d, aiming at p."""
    d = d.normalized()
    hit = tree.ray_cast(p + d * reach, -d, reach * 2)
    if hit[0] is None:
        loc, n = tree.find_nearest(p)[:2]
        return loc, n
    return hit[0], hit[1]


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
    return total


# ======================================================================================================================================
# crystal: a grown formation with a sunk root, a collar where it breaks the skin, a body and a faceted termination
# ======================================================================================================================================
CRYSTAL_PROFILES = {
    # (t along the length, section scale); the first ring is sunk below the surface, the second is the collar at the surface
    "prism": [(0.00, 1.16), (0.09, 1.00), (0.50, 0.95), (0.76, 0.84)],             # an elongated prism with a pointed termination
    "blade": [(0.00, 1.14), (0.12, 1.00), (0.54, 0.90), (0.80, 0.62)],             # broad and flattened, a chisel termination
    "stub": [(0.00, 1.14), (0.22, 1.00), (0.62, 0.84)],                             # a short, thick cluster element
    "spur": [(0.00, 1.10), (0.35, 0.80)],                                          # a small secondary shard
}


def _crystal(g, root, axis, L, r, mat, key, kind="prism", sides=6, flat=1.0, wide=None, sink=None, bend=0.0, fu0=0.0, shade=0.0,
            under=0.0):
    rnd = rng_for(*key) if isinstance(key, tuple) else rng_for(key)
    a = axis.normalized()
    w = wide if wide is not None else a.orthogonal()
    w = w - a * a.dot(w)
    w = w.normalized() if w.length > 1e-6 else a.orthogonal().normalized()
    b = a.cross(w).normalized()
    ph = rnd.uniform(0, TAU)
    sec = []
    for k in range(sides):
        th = ph + TAU * k / sides + rnd.uniform(-0.16, 0.16) * TAU / sides
        rho = rnd.uniform(0.86, 1.12)
        sec.append((math.cos(th) * rho, math.sin(th) * rho * flat))
    sink = r * 0.9 if sink is None else sink
    prof = [(-sink / L, 0.80)] + CRYSTAL_PROFILES[kind]
    bendv = (w * rnd.uniform(-1, 1) * 0.4 + b * rnd.uniform(-1, 1) * 0.4 + w * bend) * L
    lean = rnd.uniform(-12, 12)          # the termination's facets turn a little against the body
    rings, ts = [], []
    for i, (t, s) in enumerate(prof):
        c = root + a * (L * t) + bendv * (max(t, 0.0) ** 2)
        sc = s * (0.6 if (kind == "blade" and i == len(prof) - 1) else 1.0)
        tw = math.radians(lean * max(t, 0.0))
        cw, sw = math.cos(tw), math.sin(tw)
        ring = []
        for x, y in sec:
            xx, yy = x * cw - y * sw, x * sw + y * cw
            if kind == "blade" and i == len(prof) - 1:
                yy *= 0.45
            ring.append(c + (w * xx + b * yy) * (r * sc))
        rings.append(ring)
        ts.append(max(t, 0.0))
    apex = root + a * L + bendv + (w * rnd.uniform(-0.25, 0.25) + b * rnd.uniform(-0.25, 0.25) * flat) * r
    seed = rnd.random()
    loft(g, rings, mat, cap0=True, cap1=apex,
         attrs=lambda i: {"fu": fu0 + (1 - fu0) * ts[i], "fv": 0.0, "seed": seed, "shade": shade, "under": under},
         cap_attrs=({"fu": fu0, "seed": seed, "shade": shade, "under": under}, {"fu": 1.0, "seed": seed, "shade": shade, "under": under}))
    return apex



def crystal(g, *a, **k):
    g.hard += 1
    try:
        return _crystal(g, *a, **k)
    finally:
        g.hard -= 1

def cluster(g, tree, loc, n, axis, L, r, mat, key, kind="blade", flat=0.6, wide=None, sides=6, sats=(), shade=0.0):
    """A main crystal and its satellites. A satellite: (angle round the root in degrees from the main's lean, distance in radii, tilt
    away from the main in degrees, scale, kind)."""
    crystal(g, loc, axis, L, r, mat, key + ("main",), kind=kind, flat=flat, wide=wide, sides=sides, shade=shade)
    lean = axis - n * n.dot(axis)
    lean = lean.normalized() if lean.length > 1e-4 else n.orthogonal().normalized()
    for k, (ang, dist, tilt, sc, kind2) in enumerate(sats):
        d = turn(lean, n, ang)
        p, nn = cast(tree, loc + d * (dist * r), n, 0.4)
        away = (d - nn * nn.dot(d)).normalized()
        ax = turn(axis, nn.cross(away), -tilt) if away.length > 1e-4 else axis
        crystal(g, p, ax, L * sc, r * (0.45 + 0.55 * sc), mat, key + ("sat", k), kind=kind2, flat=min(1.0, flat + 0.25),
                wide=wide, sides=6 if sc > 0.5 else 5, shade=shade)


# ======================================================================================================================================
# armour plate: a thick slab laid on a surface, its root sunk under the skin and its free edge lifted (layered, like scales)
# ======================================================================================================================================
OUTLINES = {
    "shield": [(-0.04, 0.0), (0.0, -0.40), (0.30, -0.50), (0.62, -0.44), (0.88, -0.22), (1.0, 0.0), (0.88, 0.22), (0.62, 0.44),
               (0.30, 0.50), (0.0, 0.40)],
    # frost plates: the edges chipped in two steps, like broken ice
    "frost": [(-0.04, 0.0), (0.0, -0.40), (0.34, -0.50), (0.52, -0.36), (0.72, -0.42), (1.0, 0.0), (0.72, 0.42), (0.52, 0.36),
              (0.34, 0.50), (0.0, 0.40)],
    "chevron": [(-0.03, 0.0), (0.0, -0.50), (0.50, -0.44), (1.0, 0.0), (0.50, 0.44), (0.0, 0.50)],
    "scale": [(-0.03, 0.0), (0.0, -0.36), (0.40, -0.50), (0.80, -0.34), (1.0, 0.0), (0.80, 0.34), (0.40, 0.50), (0.0, 0.36)],
    # an angular shard plate: a broad root, cut corners, a point
    "shard": [(-0.03, 0.0), (0.0, -0.42), (0.40, -0.50), (0.74, -0.30), (1.0, 0.0), (0.74, 0.30), (0.40, 0.50), (0.0, 0.42)],
    # a keel plate: straight-sided, long, for the crest and the breastbone
    "keel": [(-0.03, 0.0), (0.0, -0.34), (0.58, -0.40), (0.90, -0.20), (1.0, 0.0), (0.90, 0.20), (0.58, 0.40), (0.0, 0.34)],
    # a long keel scute: narrow, straight-sided
    "scute": [(-0.03, 0.0), (0.0, -0.34), (0.55, -0.40), (0.88, -0.24), (1.0, 0.0), (0.88, 0.24), (0.55, 0.40), (0.0, 0.34)],
}


def _plate(g, tree, at, along, L, W, mat, outline="shard", thick=0.016, lift=0.026, ridge=0.012, seed=0.0, shade=0.0, under=0.0,
          normal=None, skew=0.0):
    """A plate laid on the surface under it: its outline follows the skin, its root sunk below it, its free end lifted over what lies
    behind (the layering of scales); its top is gabled, two planes meeting along a ridge down its middle, so it reads as hard, cut armour."""
    hit = tree.find_nearest(at)
    base, n = hit[0], (normal if normal is not None else hit[1])
    d = (along - n * n.dot(along)).normalized()
    s = n.cross(d).normalized()
    g.count += 1
    stack = 0.0026 * (g.count % 4)            # neighbours that overlap are stacked a little apart, so they never share a plane
    ol = OUTLINES[outline]

    def lay(u, v):
        p = base + d * (u * L) + s * (v * W + skew * u * W)
        q = tree.find_nearest(p)
        return q[0], q[1]

    def hgt(u):
        u = max(0.0, u)
        return -0.011 + stack + 0.011 * min(1.0, u / 0.22) + lift * u ** 1.3

    a = {"seed": seed, "shade": shade, "under": under}
    top, bot = [], []
    for u, v in ol:
        q, nq = lay(u, v)
        h = hgt(u)
        top.append(g.vert(q + nq * (h + thick * 0.5), fu=max(0.0, u), fv=2 * v, **a))
        bot.append(g.vert(q + nq * (h - thick * 0.5), fu=max(0.0, u), fv=2 * v, **a))
    RU = (0.05, 0.42, 0.80)
    R = []
    for j, ru in enumerate(RU):
        q, nq = lay(ru, 0.0)
        R.append(g.vert(q + nq * (hgt(ru) + thick * 0.5 + ridge * (0.45 if j == 0 else 1.0)), fu=ru, fv=0.0, **a))
    m = len(ol)

    def near(k):
        um = (ol[k][0] + ol[(k + 1) % m][0]) / 2
        return min(range(3), key=lambda j: abs(RU[j] - um))
    prev = near(m - 1)
    for k in range(m):
        k2 = (k + 1) % m
        j = near(k)
        if j != prev:
            step = 1 if j > prev else -1
            for jj in range(prev, j, step):
                g.face((top[k], R[jj], R[jj + step]), mat)
        g.face((top[k], top[k2], R[j]), mat)
        prev = j
    qc, nc = lay(0.42, 0.0)
    cb = g.vert(qc + nc * (hgt(0.42) - thick * 0.5 - 0.003), fu=0.42, fv=0.0, **a)
    for k in range(m):
        k2 = (k + 1) % m
        g.face((bot[k2], bot[k], cb), mat)
        g.face((top[k2], top[k], bot[k], bot[k2]), mat)



def plate(g, *a, **k):
    g.hard += 1
    try:
        return _plate(g, *a, **k)
    finally:
        g.hard -= 1

def _leaf(g, root, d, n, L, W, thick, mat, outline, cup=0.0, attrs=None, sink=0.02):
    """A free-standing armoured blade (the ears, the skull's frill): an outline in the plane (d, n x d), thick, its front cupped."""
    d = d.normalized()
    s = n.cross(d).normalized()
    n = d.cross(s).normalized()
    a = attrs or {}
    ol = OUTLINES[outline]
    top, bot = [], []
    for u, v in ol:
        c = root + d * (u * L - sink * (1 - min(1, u * 4))) + s * (v * W)
        k = thick * (1.0 - 0.6 * max(0.0, u))
        cupv = -n * cup * (1 - (2 * v) ** 2) * math.sin(math.pi * min(1.0, max(0.0, u)))
        top.append(g.vert(c + n * (k * 0.5) + cupv, fu=max(0.0, u), fv=2 * v, under=1.0, **a))
        bot.append(g.vert(c - n * (k * 0.5) + cupv * 0.4, fu=max(0.0, u), fv=2 * v, under=0.0, **a))
    ct = g.vert(root + d * (0.42 * L) + n * (thick * 0.3) - n * cup * 1.1, fu=0.42, fv=0.0, under=1.0, **a)
    cb = g.vert(root + d * (0.42 * L) - n * (thick * 0.7) - n * cup * 0.3, fu=0.42, fv=0.0, under=0.0, **a)
    m = len(ol)
    for k in range(m):
        k2 = (k + 1) % m
        g.face((top[k], top[k2], ct), mat)
        g.face((bot[k2], bot[k], cb), mat)
        g.face((top[k2], top[k], bot[k], bot[k2]), mat)


# ======================================================================================================================================
# the body
# ======================================================================================================================================

def leaf(g, *a, **k):
    g.hard += 1
    try:
        return _leaf(g, *a, **k)
    finally:
        g.hard -= 1

def body_knot(i):
    t, b, w, bias, pt, pb, ridge = BODY[i]
    return V(0, *t), V(0, *b), w, bias, pt, pb, ridge


def body_section(u):
    """centre, D (bottom to top), half-height, half-width at a fractional knot index"""
    u = min(max(u, 0.0), len(BODY) - 1.0)
    i = min(int(math.floor(u)), len(BODY) - 2)
    t = u - i
    t0, b0, w0, *_ = body_knot(i)
    t1, b1, w1, *_ = body_knot(i + 1)
    top, bot = lerp(t0, t1, t), lerp(b0, b1, t)
    return (top + bot) / 2, (top - bot).normalized(), (top - bot).length / 2, lerp(w0, w1, t)


def section(top, bot, w, bias, pt, pb, ridge, n):
    D = top - bot
    h = D.length / 2
    D.normalize()
    c = (top + bot) / 2
    pts = []
    for k in range(n):
        th = TAU * k / n
        s, co = math.sin(th), math.cos(th)
        p = pt if co >= 0 else pb
        x = w * spow(s, 2 / p)
        y = h * spow(co, 2 / p) + bias * h * s * s
        if co > 0:
            y += ridge * h * co ** 16
        pts.append(c + X * x + D * y)
    return pts


def body_rings(n, sub):
    tops = catmull([body_knot(i)[0] for i in range(len(BODY))], per=sub)
    bots = catmull([body_knot(i)[1] for i in range(len(BODY))], per=sub)
    idx = np.linspace(0, len(BODY) - 1, len(tops))
    cols = list(zip(*[BODY[i][2:] for i in range(len(BODY))]))
    rings = []
    for k, (t, b) in enumerate(zip(tops, bots)):
        vals = [float(np.interp(idx[k], range(len(BODY)), c)) for c in cols]
        rings.append(section(t, b, *vals, n))
    return rings, idx


def build_body_skin(g, level):
    n, sub = (12, 1) if level == 0 else (20, 2)
    rings, idx = body_rings(n, sub)
    R = loft(g, rings, M["Body"], cap0=BODY_REAR_CAP, cap1=BODY_TOP_CAP, attrs=lambda i: {"fu": idx[i] / (len(BODY) - 1)})
    verts = [v for ring in R for v in ring]
    if level >= 1:
        for name, c, r, amt in MUSCLES:
            for side in (1, -1):
                sculpt(g, verts, mirror(c, side), r, amt)
        for name, c, r, amt in MIDLINE:
            sculpt(g, verts, c, r, amt)
    return verts


def on_body(tree, u, phi, side=1):
    c, D, h, w = body_section(u)
    ph = math.radians(phi)
    return cast(tree, c, D * math.cos(ph) + X * (side * math.sin(ph)), 1.0)


def aft(u):
    """the direction toward the rear along the body at u (down the neck, on the neck)"""
    return (body_section(u - 0.3)[0] - body_section(u + 0.3)[0]).normalized()


def body_armor(g, tree):
    """Layered armour that follows the anatomy:
    - the chest: a keel of plates down the breastbone and, each side, plates sweeping back and out over the pectorals (NeckChestArmor:
      silver-blue, cold white only at their edges);
    - the neck: long keel scutes along the crest and bands of overlapping slate scales round its sides and throat;
    - the trunk: scutes flanking the spine, two staggered rows of plates down each flank over the ribs, a pauldron over each shoulder
      blade and plates over the hip points and the thighs (frosted slate, Body shade 1)."""
    rnd = rng_for("armor")
    arm, body = M["NeckChestArmor"], M["Body"]
    # the breastbone keel
    for k, u in enumerate((14.15, 13.35, 12.55, 11.75, 10.95)):
        loc, nn = on_body(tree, u, 180)
        plate(g, tree, loc, aft(u), 0.205 - 0.006 * k, 0.170, arm, outline="keel" if k % 2 == 0 else "shard", thick=0.022, lift=0.034,
              ridge=0.022, seed=rnd.random())
    # plates sweeping back over the pectorals
    for side in (1, -1):
        for k, (u, ph, L, W) in enumerate(((13.95, 162, 0.200, 0.150), (13.05, 160, 0.215, 0.160), (12.15, 158, 0.215, 0.160),
                                           (13.55, 142, 0.220, 0.165), (12.75, 138, 0.240, 0.175), (11.95, 134, 0.240, 0.175),
                                           (13.15, 118, 0.200, 0.150), (12.35, 112, 0.215, 0.160), (11.55, 110, 0.200, 0.150))):
            loc, nn = on_body(tree, u, ph, side)
            plate(g, tree, loc, aft(u) * 0.55 + X * (side * 0.75) - Z * 0.15, L, W, arm, outline="shard" if k % 2 else "frost",
                  thick=0.020, lift=0.030, ridge=0.016, seed=rnd.random())
    # the crest of the neck: long keel scutes, overlapping down toward the withers
    for k, u in enumerate((15.95, 15.25, 14.55, 13.85, 13.15, 12.45)):
        loc, nn = on_body(tree, u, 0)
        plate(g, tree, loc, aft(u), 0.150 + 0.008 * k, 0.098 + 0.004 * k, arm, outline="keel", thick=0.020, lift=0.032, ridge=0.018,
              seed=rnd.random())
    # bands of slate scales round the neck's sides and throat
    for j, u in enumerate((16.55, 15.75, 14.95)):
        for side in (1, -1):
            for k, ph in enumerate((58, 98, 140) if j < 2 else (78,)):
                loc, nn = on_body(tree, u + (0.35 if k % 2 else 0.0), ph, side)
                plate(g, tree, loc, aft(u) - Z * 0.25, 0.125, 0.112, body, outline="chevron", thick=0.015, lift=0.020, ridge=0.010,
                      seed=rnd.random(), shade=1.0)
    # the trunk: scutes flanking the spine, longest over the shoulders, shrinking toward the hips
    for k, u in enumerate((10.6, 9.8, 9.0, 8.2, 7.4, 6.6, 5.8, 5.0, 4.2, 3.4)):
        for side in (1, -1):
            loc, nn = on_body(tree, u + (0.15 if side < 0 else 0.0), 19, side)
            sc = 1.0 - 0.045 * k
            plate(g, tree, loc, aft(u) + X * (side * 0.30), 0.200 * sc, 0.135 * sc, body, outline="keel" if k % 2 else "shard",
                  thick=0.020, lift=0.028, ridge=0.015, seed=rnd.random(), shade=1.0)
    for side in (1, -1):
        # two staggered rows of plates down each flank, over the ribs
        for row, (ph, us) in enumerate(((50, (9.2, 8.3, 7.4, 6.5, 5.6, 4.7)), (80, (8.75, 7.65, 6.55, 5.45)))):
            for k, u in enumerate(us):
                loc, nn = on_body(tree, u, ph + rnd.uniform(-4, 4), side)
                plate(g, tree, loc, aft(u) * 0.75 - Z * 0.55, 0.185 - 0.01 * row, 0.165, body, outline="shard" if (k + row) % 2 else "frost",
                      thick=0.018, lift=0.026, ridge=0.014, seed=rnd.random(), shade=1.0)
        # a pauldron over each shoulder blade
        for k, (u, ph, L, W) in enumerate(((9.95, 46, 0.270, 0.200), (9.45, 62, 0.250, 0.185), (8.95, 76, 0.215, 0.165), (10.2, 76, 0.200, 0.150))):
            loc, nn = on_body(tree, u, ph, side)
            plate(g, tree, loc, aft(u) * 0.55 - Z * 0.85 + X * (side * 0.2), L, W, body, outline="frost" if k == 1 else "shard",
                  thick=0.024, lift=0.034, ridge=0.020, seed=rnd.random(), shade=1.0)
        # the hip points and the thighs
        for k, (u, ph, L, W) in enumerate(((3.30, 44, 0.190, 0.145), (2.70, 62, 0.170, 0.130), (3.0, 90, 0.200, 0.160), (2.2, 96, 0.190, 0.150))):
            loc, nn = on_body(tree, u, ph, side)
            plate(g, tree, loc, aft(u) * 0.7 - Z * 0.6, L, W, body, outline="shard" if k % 2 else "frost", thick=0.020, lift=0.026, ridge=0.015,
                  seed=rnd.random(), shade=1.0)


def body_crystals(g, tree):
    """The crystal ridge along the spine (largest over the upper back, smaller toward the hips, every one leaning back: the direction the
    beast's growth flows), a cluster from each shoulder blade, small formations at the hip points and two at the base of the neck."""
    cr = M["CrystalArmor"]
    ridge = [  # u, length, radius, kind, flat, satellites: largest over the withers, stepping down to the hips
        (12.30, 0.150, 0.042, "prism", 0.78, ()),
        (11.40, 0.300, 0.078, "blade", 0.62, ((200, 1.3, 18, 0.45, "spur"),)),
        (10.50, 0.560, 0.125, "blade", 0.55, ((30, 1.3, 18, 0.55, "prism"), (205, 1.25, 22, 0.42, "stub"))),
        (9.60, 0.500, 0.115, "blade", 0.58, ((160, 1.25, 20, 0.48, "prism"), (20, 1.2, 16, 0.32, "stub"))),
        (8.70, 0.420, 0.100, "prism", 0.68, ((200, 1.25, 20, 0.42, "prism"),)),
        (7.80, 0.340, 0.085, "blade", 0.60, ((20, 1.2, 16, 0.40, "stub"),)),
        (6.90, 0.275, 0.072, "prism", 0.72, ()),
        (6.00, 0.220, 0.060, "blade", 0.60, ((200, 1.2, 18, 0.42, "spur"),)),
        (5.10, 0.172, 0.050, "prism", 0.75, ()),
        (4.20, 0.132, 0.040, "stub", 0.80, ()),
        (3.30, 0.100, 0.032, "prism", 0.80, ()),
        (2.45, 0.072, 0.024, "spur", 0.85, ()),
    ]
    for k, (u, L, r, kind, flat, sats) in enumerate(ridge):
        side = 1 if k % 2 else -1
        loc, nn = on_body(tree, u, 3 * side)
        back = aft(u)
        lean = 40 if u < 11 else 50
        axis = (nn * math.cos(math.radians(lean)) + back * math.sin(math.radians(lean))).normalized()
        axis = turn(axis, nn, 6 * side)
        cluster(g, tree, loc, nn, axis, L, r, cr, ("ridge", k), kind=kind, flat=flat, wide=back, sats=sats)
    for side in (1, -1):
        # the shoulder cluster: a great broad crystal from the top of the blade, up, out and back, with four of its kin round it
        loc, nn = on_body(tree, 9.80, 44, side)
        axis = (nn * 0.40 + Z * 0.70 + aft(9.8) * 0.55).normalized()
        cluster(g, tree, loc, nn, axis, 0.560, 0.125, cr, ("shoulder", side), kind="blade", flat=0.55, wide=aft(9.8),
                sats=((15 * side, 1.30, 16, 0.66, "prism"), (165 * side, 1.25, 20, 0.58, "blade"), (-70 * side, 1.35, 26, 0.42, "stub"),
                      (95 * side, 1.25, 30, 0.36, "prism"), (-130 * side, 1.3, 24, 0.30, "spur")))
        # the hip point: one small pair
        loc, nn = on_body(tree, 3.25, 30, side)
        axis = (nn * 0.6 + aft(3.25) * 0.8 + Z * 0.2).normalized()
        cluster(g, tree, loc, nn, axis, 0.120, 0.032, cr, ("hip", side), kind="prism", flat=0.8,
                sats=((150, 1.3, 18, 0.55, "spur"),))
        # small crystals in the frost mane's lower edge, growing down and back with its plates
        for k, (u, ph, L) in enumerate(((12.9, 118, 0.085), (12.1, 104, 0.070))):
            loc, nn = on_body(tree, u, ph, side)
            axis = (nn * 0.55 + aft(u) * 0.70 - Z * 0.30).normalized()
            crystal(g, loc, axis, L, L * 0.26, cr, ("mane", side, k), kind="prism", flat=0.75, sides=5)
        # the base of the neck, where the frost mane meets the shoulder: a short spur pair
        loc, nn = on_body(tree, 12.3, 88, side)
        axis = (nn * 0.6 + aft(12.3) * 0.75 + Z * 0.1).normalized()
        cluster(g, tree, loc, nn, axis, 0.100, 0.027, cr, ("neckbase", side), kind="prism", flat=0.8,
                sats=((140, 1.3, 16, 0.5, "spur"),))


# ======================================================================================================================================
# the head (local axes: s across, f forward, u up; leaned into place)
# ======================================================================================================================================
HEAD_O = V(0, -1.100 - 0.13, 1.825 + 0.04)          # the middle of the cranium
HS = 1.50                             # the head's scale: its tables are written at 1/1.2
HEAD_PITCH = 16.0                     # the muzzle points forward and a little down: a watchful carriage


def head_axes():
    p = math.radians(HEAD_PITCH)
    return V(0, -math.cos(p), -math.sin(p)), V(0, -math.sin(p), math.cos(p))


MUZZLE_K = 0.76                       # the muzzle's length, set once: everything in front of the eyes drawn back toward them


def H(s, f, u):
    F, U = head_axes()
    if f > 0.112:
        f = 0.112 + (f - 0.112) * MUZZLE_K
    return HEAD_O + (X * s + F * f + U * u) * HS


def head_frame():
    F, U = head_axes()
    return (X, F, U)


# The skull with the upper jaw, as edge loops back to front: (f, half-section from the crown down one side to the palate, as (s, u)).
# The points of each loop, top to bottom: crown, upper skull, temple, the brow shelf's edge, the socket (sunk), the socket's floor, the
# cheekbone, the cheek's widest, the jaw muscle, the lower side, the underside, the middle. In front of the eyes the same points become the
# muzzle's planes: a nasal bridge, flat sides, a raised nasal boss over the nostrils, a blunt front.
SKULL = [
    (-0.175, [(0, .040), (.025, .038), (.045, .030), (.055, .018), (.058, .005), (.058, -.010), (.058, -.025), (.056, -.040), (.050, -.052),
              (.040, -.060), (.022, -.066), (0, -.068)]),
    (-0.135, [(0, .086), (.040, .083), (.074, .070), (.092, .050), (.100, .025), (.104, .000), (.106, -.030), (.104, -.065), (.096, -.100),
              (.080, -.128), (.045, -.145), (0, -.150)]),                     # skull base and throat latch: it covers the top of the neck
    (-0.070, [(0, .108), (.050, .105), (.090, .092), (.114, .070), (.122, .045), (.126, .015), (.134, -.020), (.136, -.055), (.126, -.095),
              (.104, -.128), (.060, -.150), (0, -.156)]),                     # behind the eye: the temple, the jaw's hinge
    (-0.010, [(0, .116), (.052, .113), (.094, .100), (.120, .080), (.124, .054), (.126, .024), (.140, -.012), (.143, -.046), (.131, -.086),
              (.108, -.116), (.064, -.134), (0, -.140)]),                     # the cheekbones at their widest
    (0.050, [(0, .113), (.050, .112), (.094, .104), (.138, .088), (.104, .060), (.098, .030), (.127, .000), (.137, -.032), (.124, -.070),
             (.102, -.098), (.060, -.114), (0, -.118)]),                      # the eye: the brow shelf over a sunk socket
    (0.100, [(0, .103), (.046, .102), (.086, .096), (.128, .082), (.098, .058), (.095, .028), (.116, .000), (.121, -.030), (.110, -.062),
             (.094, -.080), (.055, -.090), (0, -.093)]),
    (0.150, [(0, .090), (.040, .084), (.076, .080), (.100, .068), (.104, .045), (.106, .020), (.106, -.008), (.104, -.035), (.098, -.052),
             (.088, -.062), (.050, -.068), (0, -.070)]),                      # the stop; the corner of the mouth below it
    (0.220, [(0, .082), (.032, .073), (.068, .069), (.090, .060), (.095, .040), (.096, .018), (.096, -.006), (.095, -.030), (.091, -.052),
             (.082, -.068), (.046, -.074), (0, -.076)]),                      # the muzzle: a nasal bridge, flat sides
    (0.290, [(0, .077), (.030, .068), (.064, .064), (.084, .055), (.089, .034), (.090, .012), (.090, -.010), (.089, -.032), (.085, -.054),
             (.070, -.068), (.040, -.074), (0, -.076)]),
    (0.340, [(0, .077), (.032, .070), (.064, .066), (.082, .055), (.086, .032), (.086, .010), (.085, -.012), (.083, -.034), (.079, -.054),
             (.063, -.068), (.036, -.073), (0, -.075)]),                      # the nasal boss over the nostrils
    (0.378, [(0, .064), (.028, .060), (.054, .055), (.072, .044), (.077, .022), (.078, .004), (.077, -.016), (.075, -.036), (.071, -.054),
             (.053, -.066), (.030, -.071), (0, -.073)]),
    (0.400, [(0, .042), (.024, .041), (.042, .036), (.053, .026), (.057, .010), (.058, -.006), (.057, -.022), (.055, -.040), (.051, -.055),
             (.044, -.065), (.025, -.070), (0, -.072)]),                      # the blunt front of the nose
]
SKULL_TIP = (0.413, -0.012)
# the lower jaw: (f, top u, bottom u, half-width); deep under the cheeks, a squared chin, shorter than the upper jaw (a slight overbite)
JAW = [(-0.040, -0.064, -0.165, 0.100), (0.040, -0.060, -0.165, 0.095), (0.120, -0.060, -0.152, 0.088), (0.200, -0.066, -0.138, 0.080),
       (0.270, -0.070, -0.130, 0.072), (0.320, -0.072, -0.124, 0.065), (0.352, -0.073, -0.116, 0.057), (0.368, -0.074, -0.106, 0.047)]
JAW_TIP = (0.377, -0.092)
HEAD_SCULPT = [  # local centre (s, f, u), radii (s, f, u), amount; mirrored when s != 0
    ((0.0, -0.130, 0.070), (0.030, 0.060, 0.040), 0.006),      # the occipital crest
]
EYE_LOCAL = (0.084, 0.068, 0.044)
EYE_R = 0.038 * HS
EYE_AXIS_LOCAL = (0.68, 0.72, 0.12)


def skull_rings(sub):
    """The loops, with sub - 1 more between each pair (each point carried along its own spline), mirrored to a full ring."""
    n = len(SKULL[0][1])
    fs = [f for f, _ in SKULL]
    tracks = [catmull([V(sec[i][0], f, sec[i][1]) for f, sec in SKULL], per=sub) for i in range(n)]
    rings, fus = [], []
    for k in range(len(tracks[0])):
        half = [tracks[i][k] for i in range(n)]
        full = half + [V(-p.x, p.y, p.z) for p in reversed(half[1:-1])]
        rings.append([H(p.x, p.y, p.z) for p in full])
        fus.append(half[0].y)
    return rings, fus


def build_skull(g, level):
    sub = 1 if level == 0 else 2
    rings, fus = skull_rings(sub)
    if level == 0:
        rings = [r[::2] for r in rings]
    R = loft(g, rings, M["Face"], cap0=H(0, -0.186, -0.012), cap1=H(0, *SKULL_TIP), attrs=lambda i: {"fu": (fus[i] + 0.17) / 0.58})
    verts = [v for r in R for v in r]
    jaw = []
    nj = 10 if level == 0 else 14
    for f, ut, ub, w in JAW:
        uc, h = (ut + ub) / 2, (ut - ub) / 2
        jaw.append([H(w * spow(math.sin(TAU * k / nj), 2 / 2.8), f, uc + h * spow(math.cos(TAU * k / nj), 2 / 2.6)) for k in range(nj)])
    RJ = loft(g, jaw, M["Face"], cap0=True, cap1=H(0, *JAW_TIP), attrs=lambda i: {"fu": 0.5 + 0.5 * i / (len(JAW) - 1)})
    if level >= 1:
        fr = head_frame()
        for (s, f, u), r, amt in HEAD_SCULPT:
            for side in ((1, -1) if s else (1,)):
                sculpt(g, verts, H(s * side, f, u), tuple(x * HS for x in r), amt * HS, frame=fr)
    return verts, [v for r in RJ for v in r]


def eye_frame(side):
    F, U = head_axes()
    s, f, u = EYE_LOCAL
    c = H(s * side, f, u)
    a = EYE_AXIS_LOCAL
    axis = (X * (a[0] * side) + F * a[1] + U * a[2]).normalized()
    up = (U - axis * axis.dot(U)).normalized()
    fwd = (F - axis * axis.dot(F) - up * up.dot(F)).normalized()       # across the eye, toward the nose
    return c, axis, up, fwd


def sph(c, axis, up, fwd, r, alpha, beta):
    """a point on the eye's sphere: alpha round toward the nose, beta up (degrees)"""
    al, be = math.radians(alpha), math.radians(beta)
    return c + (axis * (math.cos(be) * math.cos(al)) + fwd * (math.cos(be) * math.sin(al)) + up * math.sin(be)) * r


def build_eye(g, side, seg=14, rings=6):
    """The eyeball: the front of a sphere, set into the socket (what the socket buries is not built). Its paint: a deep blue-black ball,
    the arctic-cyan iris, a narrow upright pupil and a catch-light (fu: toward the front; fv: up; shade: toward the nose)."""
    c, axis, up, fwd = eye_frame(side)
    r = EYE_R
    # the pupil: a dark upright lens seated in the glowing iris's opening (painted as pupil: fu 1, at the eye's middle)
    def pup(th):
        return 1.0 / math.sqrt((math.cos(th) / 15.0) ** 2 + (math.sin(th) / 6.5) ** 2) * 0.90
    lens = []
    for rad in (0.985, 1.026):
        ring = []
        for k in range(12):
            th = TAU * k / 12
            el = math.radians(pup(th))
            d = axis * math.cos(el) + (up * math.cos(th) + fwd * math.sin(th)) * math.sin(el)
            ring.append(c + d * (r * rad))
        lens.append(ring)
    pa = {"fu": 1.0, "fv": 0.0, "shade": 0.0, "under": 1.0}
    loft(g, lens, M["Eye"], cap0=c + axis * (r * 0.985), cap1=c + axis * (r * 1.030), attrs=lambda i: pa, cap_attrs=(pa, pa))
    pole = g.vert(c + axis * r, fu=1.0, fv=0.0, shade=0.0)
    rows = []
    for i in range(1, rings + 1):
        el = math.radians(112.0 * i / rings)
        row = []
        for k in range(seg):
            az = TAU * k / seg
            d = axis * math.cos(el) + (up * math.cos(az) + fwd * math.sin(az)) * math.sin(el)
            row.append(g.vert(c + d * r, fu=d.dot(axis), fv=d.dot(up), shade=d.dot(fwd)))
        rows.append(row)
    for k in range(seg):
        g.face((pole, rows[0][k], rows[0][(k + 1) % seg]), M["Eye"])
    for i in range(len(rows) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            g.face((rows[i][k], rows[i + 1][k], rows[i + 1][k2], rows[i][k2]), M["Eye"])
    bv = g.vert(c - axis * r * 0.25, fu=-1.0)
    for k in range(seg):
        g.face((rows[-1][k], bv, rows[-1][(k + 1) % seg]), M["Eye"])


def build_lid(g, side, upper):
    """A lid: a thick shell over the eyeball. The upper one comes down over the top of the iris (a calm, slightly narrow look, its line
    level, peaking a little toward the nose); the lower one rises to meet it at the corners: an almond opening."""
    c, axis, up, fwd = eye_frame(side)
    r = EYE_R
    alphas = [-96, -70, -45, -20, 4, 28, 52, 74, 98] if upper else [-88, -66, -43, -19, 4, 27, 50, 70, 90]   # their corner caps apart
    ro, ri = (1.14, 0.92) if upper else (1.06, 0.80)

    def edge(al):
        x = max(-1.0, min(1.0, (al - 6) / 74.0))
        k = math.cos(x * math.pi / 2)
        return (-7 + 28 * k) if upper else (-3 - 25 * k)

    rows_o, rows_i = [], []
    for al in alphas:
        e = edge(al)
        be = [e, e + (86 - e) * 0.4, 86] if upper else [e, e + (-84 - e) * 0.45, -84]
        rk = (ro * 0.985, ro, 0.84 if upper else 0.76)   # its back row dives steeply into the socket: it never runs alongside the ball
        rows_o.append([g.vert(sph(c, axis, up, fwd, r * rk[j], al, b), fu=j / 2, fv=0.0, shade=1.0) for j, b in enumerate(be)])
        rows_i.append([g.vert(sph(c, axis, up, fwd, r * ri, al, b), fu=j / 2, fv=0.0, shade=1.0) for j, b in enumerate(be)])
    mat = M["Face"]
    for i in range(len(alphas) - 1):
        for j in range(2):
            g.face((rows_o[i][j], rows_o[i + 1][j], rows_o[i + 1][j + 1], rows_o[i][j + 1]), mat)
            g.face((rows_i[i][j + 1], rows_i[i + 1][j + 1], rows_i[i + 1][j], rows_i[i][j]), mat)
        g.face((rows_i[i][0], rows_i[i + 1][0], rows_o[i + 1][0], rows_o[i][0]), mat)       # the lid's edge
        g.face((rows_o[i][2], rows_o[i + 1][2], rows_i[i + 1][2], rows_i[i][2]), mat)
    for i in (0, len(alphas) - 1):
        g.face((rows_o[i][0], rows_o[i][1], rows_o[i][2], rows_i[i][2], rows_i[i][1], rows_i[i][0]), mat)


def build_eye_glow(gl, gw, side, seg=14):
    """The glowing iris (Neon in the game): an annulus standing just off the eyeball round the narrow upright pupil, which stays the
    eyeball's own dark paint; and a small icy-white catch-light above the pupil (a second, white glow)."""
    c, axis, up, fwd = eye_frame(side)
    r = EYE_R

    def pupil(th):     # the pupil's outline: 6.5 degrees across, 15 tall
        return 1.0 / math.sqrt((math.cos(th) / 15.0) ** 2 + (math.sin(th) / 6.5) ** 2)

    rings = []
    for el_of, rad in ((lambda th: pupil(th), 1.034), (lambda th: 33.0, 1.034), (lambda th: 33.0, 0.975), (lambda th: pupil(th), 0.975)):
        ring = []
        for k in range(seg):
            th = TAU * k / seg
            el = math.radians(el_of(th))
            d = axis * math.cos(el) + (up * math.cos(th) + fwd * math.sin(th)) * math.sin(el)
            ring.append(c + d * (r * rad))
        rings.append(ring)
    loft(gl, rings, 0, cap0=False, cap1=False, loop=True)
    # the catch-light: a small dome up and toward the nose of the pupil
    cc = sph(c, axis, up, fwd, 1.0, 13, 17) - c
    a2 = cc.normalized()
    u2 = (up - a2 * a2.dot(up)).normalized()
    f2 = a2.cross(u2)
    out, inn = [], []
    for k in range(6):
        th = TAU * k / 6
        el = math.radians(4.2)
        d = a2 * math.cos(el) + (u2 * math.cos(th) + f2 * math.sin(th)) * math.sin(el)
        out.append(c + d * (r * 1.06))
        inn.append(c + d * (r * 0.99))
    loft(gw, [inn, out], 0, cap0=c + a2 * (r * 0.99), cap1=c + a2 * (r * 1.072))


def ridge_tube(g, pts_local, sizes, mat, sec, side, attrs=None, per=2):
    pts = [H(s * side, f, u) for s, f, u in pts_local]
    path = catmull(pts, per=per)
    sz = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(sizes)), sizes)
    fr = frames(path, side=X * side)
    F, U = head_axes()
    rings = []
    for p, (t, A, B), k in zip(path, fr, sz):
        up = B if B.dot(U) > 0 else -B
        rings.append([p + A * (x * k * HS) + up * (y * k * HS) for x, y in sec])
    if side < 0:
        rings = [list(reversed(r)) for r in rings]
    loft(g, rings, mat, cap0=True, cap1=True, attrs=attrs)


def build_nostril(g, side):
    """A shaped nostril: a dark slit sunk in the dented side of the nose, under a raised rim of hide."""
    F, U = head_axes()
    c = H(0.074 * side, 0.352, 0.026)
    out = (X * side * 0.70 + F * 0.62 + U * 0.25).normalized()
    along = (U * 0.45 - F * 0.9).normalized()            # the slit runs back and a little up
    s = out.cross(along).normalized()
    rim = [c + along * (0.021 * HS * math.cos(TAU * k / 8)) + s * (0.0075 * HS * math.sin(TAU * k / 8)) for k in range(8)]
    inner = [c - out * 0.010 * HS + (p - c) * 0.55 for p in rim]
    loft(g, [[p + out * 0.0018 * HS for p in rim], inner], M["Detail"], cap0=True, cap1=True, attrs=lambda i: {"shade": 1.0})
    # the rim above it: a short hide fold
    ridge_tube(g, [(0.060, 0.322, 0.046), (0.079, 0.350, 0.044), (0.072, 0.380, 0.034)], [0.004, 0.0075, 0.004], M["Face"],
               [(-0.6, 0.6), (0.6, 0.8), (1.0, -0.2), (0.0, -0.8)], side, attrs=lambda i: {"fu": 0.95, "fv": 1.0}, per=1)


def head_plates(g, tree):
    """Reptilian scutes over the skull: two long plates down the nasal bridge, and a small one on the brow shelf over each eye."""
    F, U = head_axes()
    rnd = rng_for("headplates")
    loc, nn = cast(tree, H(0, 0.180, 0.0), U, 0.4)
    plate(g, tree, loc, -F, 0.110 * HS, 0.074 * HS, M["Face"], outline="keel", thick=0.010, lift=0.010, ridge=0.007, seed=rnd.random())
    for side in (1, -1):
        for k, (f, L, W) in enumerate(((0.120, 0.064, 0.042),)):
            loc, nn = cast(tree, H(0.112 * side, f, 0.090), U * 0.7 + X * side * 0.7, 0.4)
            plate(g, tree, loc, -F + X * side * 0.15, L * HS, W * HS, M["Face"], outline="shard", thick=0.013, lift=0.016, ridge=0.009,
                  seed=rnd.random())


def build_ears(g, tree, side):
    """No mammal's ears: a pair of swept-back fins at the back of each cheek, the upper long, the lower short, crystal-edged in their paint;
    they lie back along the skull toward the neck, under the antlers and clear of them."""
    F, U = head_axes()
    for k, (root, d, L, W) in enumerate(((H(0.116 * side, -0.070, 0.012), X * side * 0.34 - F * 0.92 - U * 0.18, 0.320, 0.088),
                                         (H(0.120 * side, -0.050, -0.050), X * side * 0.32 - F * 0.92 - U * 0.40, 0.220, 0.066))):
        nrm = X * side * 0.90 + U * 0.30
        leaf(g, root, d, nrm, L * HS, W * HS, 0.014 * HS, M["Detail"], "keel", cup=0.006 * HS, attrs={"seed": 0.3 + 0.1 * k},
             sink=0.035 * HS)


def build_frill(g):
    """The skull's frill: three plates from the occiput back over the crest of the neck (the skull runs into the neck's armour)."""
    F, U = head_axes()
    for k, (s, L, W, tilt) in enumerate(((0.0, 0.135, 0.080, 0.0), (0.048, 0.110, 0.066, 0.35), (-0.048, 0.110, 0.066, -0.35))):
        root = H(s, -0.118, 0.090 if s == 0 else 0.078)
        d = (-F * 0.80 - U * 0.42 + X * tilt * 0.6).normalized()
        nrm = (U * 0.8 - F * 0.4 + X * tilt)
        leaf(g, root, d, nrm, L * HS, W * HS, 0.014 * HS, M["Face"], "scute", cup=-0.004 * HS, attrs={"seed": 0.2 * k, "shade": 0.0}, sink=0.04 * HS)


def build_pedicle(g, side):
    """The bony pedicle the antler grows from: a short angular boss on the skull, behind the brow."""
    p0, axis = pedicle_frame(side)
    path = [p0 - axis * 0.040 * HS, p0 - axis * 0.010 * HS, p0 + axis * 0.014 * HS, p0 + axis * 0.030 * HS]
    radii = [0.040 * HS, 0.045 * HS, 0.043 * HS, 0.040 * HS]
    fr = frames(path, side=X * side)
    rnd = rng_for("pedicle", side)
    jit = [rnd.uniform(0.92, 1.08) for _ in range(8)]
    rings = [oval(p, A, B, r, r * 0.92, 8, p=2.0, jitter=jit) for p, (t, A, B), r in zip(path, fr, radii)]
    loft(g, rings, M["Detail"], cap0=True, cap1=True, attrs=lambda i: {"fu": i / 3, "shade": 0.0, "under": 0.0, "seed": 0.8})


def pedicle_frame(side):
    F, U = head_axes()
    base = H(0.066 * side, -0.022, 0.082)
    axis = (X * side * 0.38 - F * 0.30 + U * 0.875).normalized()
    return base, axis


def antler_base(side):
    p0, axis = pedicle_frame(side)
    return p0 + axis * 0.030 * HS, axis


def head_crystals(g, tree):
    """Only a few: one on the forehead between the antlers, and on each side one along the upper cheek and one behind the eye, all lying
    back along the skull, clear of the eyes and the muzzle."""
    F, U = head_axes()
    cr = M["CrystalArmor"]
    for k, f in enumerate((0.235, 0.290, 0.340)):        # small crystal nubs along the nasal ridge, lying back along it
        loc, nn = cast(tree, H(0, f, 0.04), U, 0.4)
        crystal(g, loc, (nn * 0.55 - F * 0.85).normalized(), (0.040 - 0.006 * k) * HS, (0.011 - 0.0015 * k) * HS, cr, ("nasal", k),
                kind="stub", flat=0.6, wide=X, sides=5)
    loc, nn = cast(tree, H(0, -0.030, 0.10), U, 0.4)
    cluster(g, tree, loc, nn, (U * 0.62 - F * 0.78).normalized(), 0.090 * HS, 0.020 * HS, cr, ("forehead",), kind="blade", flat=0.55, wide=X,
            sats=((150, 1.2, 14, 0.5, "spur"),))
    for side in (1, -1):
        loc, nn = cast(tree, H(0.110 * side, -0.006, -0.018), X * side, 0.4)
        crystal(g, loc, (-F * 0.85 + X * side * 0.30 + U * 0.25).normalized(), 0.062 * HS, 0.013 * HS, cr, ("cheek", side), kind="prism", flat=0.7,
                sides=5)
        loc, nn = cast(tree, H(0.104 * side, -0.044, 0.060), X * side, 0.4)
        crystal(g, loc, (-F * 0.80 + X * side * 0.32 + U * 0.42).normalized(), 0.058 * HS, 0.012 * HS, cr, ("behindeye", side), kind="prism",
                flat=0.75, sides=5)


def head_attrs(g):
    """Paint values: shade darkens round the eyes; under pales the throat and the jaw's underside."""
    c1, c2 = eye_frame(1)[0], eye_frame(-1)[0]
    F, U = head_axes()
    sh, un = g.L["shade"], g.L["under"]
    for v in g.bm.verts:
        if v[sh] > 0.0 or v[un] > 0.0:
            continue
        d = min((v.co - c1).length, (v.co - c2).length)
        v[sh] = 1.0 - sstep(0.030 * HS, 0.075 * HS, d)
        u = (v.co - HEAD_O).dot(U) / HS
        v[un] = sstep(-0.125, -0.170, u) * 0.80


# ======================================================================================================================================
# the antlers
# ======================================================================================================================================
# The left antler, as nodes offset from the top of its pedicle in world axes (x out, y back, z up). Crystal grows straight between nodes:
# the beam is a run of hexagonal segments, each turned against the last and swelling into a faceted knuckle at its node, where the tines
# branch. It sweeps back and out, then rises (back and up from the side); the tines go forward and up (a crown from the front); its end
# forks outward.
BEAM = [V(0.000, 0.000, 0.000), V(0.060, 0.060, 0.090), V(0.170, 0.150, 0.180), V(0.310, 0.220, 0.270), V(0.450, 0.250, 0.370),
        V(0.570, 0.230, 0.480), V(0.650, 0.180, 0.600), V(0.690, 0.130, 0.690)]
BEAM_R = [0.068, 0.062, 0.055, 0.048, 0.041, 0.033, 0.025]
TINES = [  # node, direction, length, radius, secondaries (direction, length, radius) from the tine's middle node
    ("brow", 1, V(0.30, -0.85, 0.43), 0.200, 0.033, []),
    ("bez", 2, V(0.10, -0.52, 0.85), 0.265, 0.031, [(V(0.60, -0.25, 0.76), 0.105, 0.016)]),
    ("back", 3, V(0.25, 0.75, 0.62), 0.150, 0.023, []),
    ("trez", 4, V(0.30, -0.30, 0.90), 0.285, 0.027, [(V(0.82, 0.05, 0.57), 0.115, 0.015)]),
    ("royal", 5, V(0.85, 0.05, 0.52), 0.185, 0.021, []),
]
ANTLER_R_VARY = {"brow": (1.0, -6), "bez": (0.93, 7), "back": (1.10, -5), "trez": (1.05, -5), "royal": (0.90, 8)}   # the right antler


def beam_nodes(side):
    base, axis = antler_base(side)
    k = 1.0 if side > 0 else 0.97                       # the right antler: a touch smaller and lower at its end
    pts = [base - axis * 0.030] + [base + mirror(p, side) * k + V(0, 0.010, -0.012) * (i / 7) * (side < 0) for i, p in enumerate(BEAM)]
    rad = [BEAM_R[0] * 0.92] + BEAM_R + [0.0]
    return pts, rad


def _antler_prism(g, nodes, radii, fu, mat, key, sides=6, flat=0.80, knuckle=1.13, glow=None):
    """A crystal shaft through its nodes: at each inner node a faceted knuckle (wider, its section turned 30 degrees against the segment
    before), just after it a neck (narrower), so every segment reads as its own prism; the last segment ends in a two-stage faceted
    termination (a narrowed, turned ring and an off-centre point). nodes[-1] is the point."""
    rnd = rng_for(*key)
    ph = rnd.uniform(0, TAU)
    sec = []
    for k in range(sides):
        th = ph + TAU * k / sides + rnd.uniform(-0.12, 0.12) * TAU / sides
        sec.append((math.cos(th) * rnd.uniform(0.9, 1.1), math.sin(th) * rnd.uniform(0.92, 1.08) * flat))
    ref = Z if abs((nodes[-1] - nodes[0]).normalized().dot(Z)) < 0.9 else X
    pts, sc, rot = [], [], []
    last = len(nodes) - 2                       # the last node before the point
    for i in range(last + 1):
        r = radii[i]
        if 0 < i < last:
            pts.append(nodes[i])
            sc.append(r * knuckle)
            rot.append(30.0 * i)
        else:
            pts.append(nodes[i])
            sc.append(r)
            rot.append(30.0 * i)
        if i < last:
            pts.append(nodes[i].lerp(nodes[i + 1], 0.22))
            sc.append(lerp(r, radii[i + 1], 0.22) * 0.90)
            rot.append(30.0 * i + 12.0)
    # the termination: a narrowed ring turned against the last, then the point
    tip = nodes[-1]
    pts.append(nodes[last].lerp(tip, 0.55))
    sc.append(radii[last] * 0.62)
    rot.append(30.0 * last + 30.0)
    fr = frames(pts + [tip], side=ref)
    rings = []
    for p, (t, A, B), r, rd in zip(pts, fr, sc, rot):
        c, s_ = math.cos(math.radians(rd)), math.sin(math.radians(rd))
        rings.append([p + (A * (x * c - y * s_) + B * (x * s_ + y * c)) * r for x, y in sec])
    t, A, B = fr[-1]
    apex = tip + (A * rnd.uniform(-0.3, 0.3) + B * rnd.uniform(-0.3, 0.3)) * radii[last] * 0.6
    n = len(rings)
    seed = rnd.random()
    loft(g, rings, mat, cap0=True, cap1=apex, attrs=lambda i: {"fu": fu[0] + (fu[1] - fu[0]) * (i / n) ** 0.85, "seed": seed},
         cap_attrs=({"fu": fu[0], "seed": seed}, {"fu": fu[1], "seed": seed}))
    if glow is not None:
        # the frozen light over the termination: a thin shell standing 3 mm off its facets, closed inside the crystal
        def off(ring, c, k):
            return [p + (p - c).normalized() * k for p in ring]
        c0, c1 = pts[-2], pts[-1]
        ax = (apex - c1).normalized()
        loft(glow, [off(rings[-2], c0, -0.005), off(rings[-2], c0, 0.004), off(rings[-1], c1, 0.004)], 0,
             cap0=c0 + ax * 0.002, cap1=apex + ax * 0.006)
    return apex


def antler_prism(g, *a, **k):
    g.hard += 1
    try:
        return _antler_prism(g, *a, **k)
    finally:
        g.hard -= 1


def build_antler(g, side, level, tips, glow=None):
    mat = M["Antler"]
    nodes, radii = beam_nodes(side)
    beam_tip = antler_prism(g, nodes, radii, (0.0, 1.0), mat, ("beam", side), sides=6 if level else 5, glow=glow)
    tips.append(beam_tip)
    tines = [t for t in TINES if t[0] in ("brow", "bez", "trez")] if level == 0 else TINES
    for name, ni, d, length, r, subs in tines:
        k, rot = (1.0, 0.0) if side > 0 else ANTLER_R_VARY[name]
        p0 = nodes[ni + 1]
        r0 = radii[ni + 1]
        dd = turn(mirror(d, side).normalized(), Z, rot * side)
        Ln = length * k
        mid = p0 + dd * (Ln * 0.50) + Z * (Ln * 0.06)
        end = p0 + dd * Ln + Z * (Ln * 0.16)
        tn = [p0 - dd * (r0 * 0.4), p0 + dd * (r0 * 1.05), mid, end]
        tp = antler_prism(g, tn, [r * 0.95, r * 1.02, r * 0.80, 0.0], (0.25 + 0.6 * ni / 7, 1.0), mat, ("tine", name, side),
                          sides=6 if level else 5, flat=0.86, glow=glow if name in ("bez", "trez") else None)
        tips.append(tp)
        for (sd, sl, sr) in (subs if level else []):
            sdd = turn(mirror(sd, side).normalized(), Z, rot * side)
            q0 = mid
            sn = [q0 - sdd * (sr * 0.5), q0 + sdd * (sr * 1.2), q0 + sdd * sl + Z * (sl * 0.10)]
            antler_prism(g, sn, [sr * 0.95, sr, 0.0], (0.85, 1.0), mat, ("sub", name, side), sides=5, flat=0.85)
    if level >= 1:
        build_coronet(g, side)


def build_coronet(g, side):
    """The coronet: a ring of short, broad crystal plates round the beam's root where it meets the pedicle: the antler's substantial base."""
    base, axis = antler_base(side)
    w = axis.orthogonal().normalized()
    rnd = rng_for("coronet", side)
    for k in range(7):
        ang = 360 * k / 7 + rnd.uniform(-10, 10)
        out = turn(w, axis, ang)
        root = base + axis * 0.004 + out * 0.058
        ax = (out * 0.70 + axis * 0.70).normalized()
        crystal(g, root, ax, rnd.uniform(0.048, 0.066), 0.020, M["Antler"], ("coronet", side, k), kind="stub", sides=5, flat=0.55,
                wide=turn(out, axis, 90), sink=0.010, fu0=0.0)


# ======================================================================================================================================
# the legs
# ======================================================================================================================================
def leg_path(kind, side):
    P = [mirror(p, side) for p in LEGS[kind]["pts"]]
    P0, P1, P2, P3, P4 = P
    if kind == "fore":
        mids = [lerp(P0, P1, 0.42), P1, lerp(P1, P2, 0.36), lerp(P1, P2, 0.78)]
    else:
        mids = [lerp(P0, P1, 0.48), P1, lerp(P1, P2, 0.36), lerp(P1, P2, 0.78)]
    return [P0 + Z * 0.115, P0 + Z * 0.068, P0] + mids + [P2, lerp(P2, P3, 0.5), P3, lerp(P3, P4, 0.55), P4, P4 - Z * 0.030]


def leg_sculpts(kind, side):
    P0, P1, P2, P3, P4 = [mirror(p, side) for p in LEGS[kind]["pts"]]
    out = X * side
    if kind == "fore":
        return [
            (P1 + V(0, 0.072, 0.010), (0.05, 0.05, 0.06), 0.030),                    # the point of the elbow
            (lerp(P1, P2, 0.28) + V(0, -0.055, 0), (0.06, 0.05, 0.10), 0.016),       # forearm extensor
            (lerp(P1, P2, 0.30) + V(0, 0.048, 0), (0.05, 0.05, 0.10), 0.012),        # flexor
            (lerp(P1, P2, 0.25) + out * 0.06, (0.05, 0.08, 0.10), 0.010),            # the forearm's outer mass
            (P2 + V(0, -0.050, 0.005), (0.05, 0.04, 0.04), 0.010),                   # the wrist's front
            (P3 + V(0, 0.052, 0.0), (0.05, 0.05, 0.05), 0.012),                      # fetlock
            (lerp(P2, P3, 0.5) + V(0, 0.050, 0), (0.03, 0.03, 0.08), -0.006),        # tendon groove
        ]
    return [
        (P1 + V(0, -0.080, 0.006), (0.06, 0.05, 0.06), 0.016),                      # the stifle
        (lerp(P1, P2, 0.30) + V(0, 0.060, 0.0), (0.06, 0.06, 0.10), 0.020),         # gaskin
        (P2 + V(0, 0.062, 0.030), (0.04, 0.05, 0.05), 0.030),                       # the point of the hock
        (P3 + V(0, 0.050, 0.0), (0.05, 0.05, 0.05), 0.012),                         # fetlock
        (lerp(P2, P3, 0.5) + V(0, 0.048, 0), (0.03, 0.03, 0.08), -0.006),           # tendon groove
    ]


def build_leg_skin(g, kind, side, level):
    path = leg_path(kind, side)
    rad = LEGS[kind]["rad"]
    if level >= 1:
        fine = catmull(path, per=2)
        r = [tuple(np.interp(np.linspace(0, 1, len(fine)), np.linspace(0, 1, len(rad)), [x[j] for x in rad])) for j in range(2)]
        rad2 = list(zip(*r))
        path = fine
    else:
        rad2 = rad
    n = 7 if level == 0 else 10
    fr = frames(path, side=X * side)
    rings = []
    for i, (p, (t, A, B), (rs, rf)) in enumerate(zip(path, fr, rad2)):
        rings.append(oval(p, A, B, rs, rf, n, p=2.25))
    R = loft(g, rings, M["Body"], cap0=True, cap1=True, attrs=lambda i: {"fu": i / (len(rings) - 1)})
    verts = [v for ring in R for v in ring]
    if level >= 1:
        for c, r, amt in leg_sculpts(kind, side):
            sculpt(g, verts, c, r, amt)
    return verts


TOE_BOTTOM = [(0.000, -0.108), (0.000, -0.040), (0.000, 0.030), (0.016, 0.050), (0.046, 0.046), (0.066, 0.010), (0.067, -0.036),
              (0.052, -0.076), (0.026, -0.103)]


def build_hoof(g, kind, side, level):
    """Split cloven hooves: two toes with real thickness, each flat on its inner face along the cleft and curved outside, a defined front
    edge sloping up from the toe's point, the underside darker in its paint. A frost band rings the coronet; two crystal dewclaw spurs
    point down and back from the fetlock."""
    P3, P4 = [mirror(p, side) for p in LEGS[kind]["pts"][3:]]
    C = V(P4.x, P4.y, 0.0)
    hk = HOOF_K
    for toe in (-1, 1):
        sx = toe * side              # +: outward from the cleft on this toe
        x0 = C.x + sx * 0.0060
        levels = [(0.000, 1.00, 1.00), (0.012 * hk, 1.01, 1.00), (0.050 * hk, 0.90, 0.80), (0.088 * hk, 0.78, 0.56), (0.104 * hk, 0.66, 0.42)]
        rings = []
        for z, ws, fs in levels:
            ring = []
            for x, y in (TOE_BOTTOM if level else TOE_BOTTOM[::2]):
                yy = (y * fs) if y < 0 else y * (0.6 + 0.4 * ws)
                ring.append(V(x0 + sx * x * ws * hk, C.y + (yy + 0.004 * (1 - ws)) * hk, z))
            if sx < 0:
                ring.reverse()
            rings.append(ring)
        loft(g, rings, M["Hoof"], cap0=True, cap1=V(x0 + sx * 0.03, C.y - 0.01, 0.15), attrs=lambda i: {"fu": i / 4, "seed": 0.5 + 0.2 * toe})
    if level == 0:
        return
    # the coronet band: an angular ring of frost over the top of the hoof
    rnd = rng_for("band", kind, side)
    seg = 10
    jit = [rnd.uniform(0.94, 1.06) for _ in range(seg)]
    ringA = [C + V(0, -0.012, z) for z in (0.090, 0.124)]
    rings = []
    for (zc, rr, ins) in ((0.100, 1.10, 0.0), (0.138, 0.98, 0.0), (0.138, 0.78, 1.0), (0.100, 0.86, 1.0)):
        rings.append([C + V(math.sin(TAU * k / seg) * 0.084 * rr * jit[k], -0.014 + math.cos(TAU * k / seg) * 0.086 * rr * jit[k],
                            zc + (0.006 if k % 2 else 0.0)) for k in range(seg)])
    loft(g, rings, M["Toe"], loop=True, attrs=lambda i: {"fu": 0.2 + 0.2 * i, "seed": 0.4})
    for k, dx in enumerate((0.030, -0.030)):
        root = P3 + V(dx, 0.050, -0.012)
        crystal(g, root, V(dx * 4, 0.55, -0.80).normalized(), 0.058, 0.013, M["Toe"], ("dewclaw", kind, side, k), kind="prism", sides=5,
                flat=0.7, sink=0.016)


def leg_armor(g, tree, kind, side):
    """Slate greaves down the front of the cannon, and a cap over the knee (fore: the wrist's front; hind: the stifle)."""
    P = [mirror(p, side) for p in LEGS[kind]["pts"]]
    P0, P1, P2, P3, P4 = P
    rnd = rng_for("legplates", kind, side)
    fwd = V(0, -1, 0)
    runs = [(lerp(P2, P3, f), 0.120 - 0.020 * k, 0.095 - 0.012 * k) for k, f in enumerate((0.12, 0.55))]
    if kind == "hind":
        runs.append((P1 + V(0, -0.02, 0.05), 0.160, 0.130))
    for k, (c, L, W) in enumerate(runs):
        loc, nn = cast(tree, c, fwd + X * side * 0.15, 0.4)
        plate(g, tree, loc, -Z, L, W, M["Body"], outline="keel" if k % 2 else "shard", thick=0.018, lift=0.018, ridge=0.014,
              seed=rnd.random(), shade=1.0)


def leg_crystals(g, tree, kind, side):
    """Crystal greaves: a run of formations down the outer front of the forearm (fore) or the outer back of the gaskin (hind), growing up
    and back from the limb like frost from a branch, the largest highest; all between the joints."""
    P0, P1, P2, P3, P4 = [mirror(p, side) for p in LEGS[kind]["pts"]]
    out = X * side
    cr = M["CrystalArmor"]
    if kind == "fore":
        spec = [(0.22, 0.230, 0.056, "blade"), (0.50, 0.185, 0.046, "prism"), (0.76, 0.135, 0.036, "blade")]
        face = out * 0.75 - Y * 0.65
    else:
        spec = [(0.25, 0.200, 0.050, "blade"), (0.55, 0.160, 0.040, "prism"), (0.80, 0.115, 0.032, "stub")]
        face = out * 0.80 + Y * 0.60
    for k, (f, L, r, kind2) in enumerate(spec):
        at = lerp(P1, P2, f)
        loc, nn = cast(tree, at, face, 0.4)
        axis = (nn * 0.55 + Z * 0.55 + Y * 0.45).normalized()
        cluster(g, tree, loc, nn, axis, L, r, cr, ("greave", kind, side, k), kind=kind2, flat=0.62, wide=Z,
                sats=((150, 1.25, 18, 0.45, "spur"),) if k == 0 else ())


# ======================================================================================================================================
# the tail
# ======================================================================================================================================
def tail_path(per):
    root = TAIL_PATH[0] - (TAIL_PATH[1] - TAIL_PATH[0]).normalized() * 0.105
    pts = catmull([root] + TAIL_PATH, per=per)
    rad = [TAIL_R[0] * 0.55] + TAIL_R
    radii = list(np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(rad)), rad))
    return pts, radii


def build_tail_skin(g, level):
    per = 1 if level == 0 else 3
    pts, radii = tail_path(per)
    n = 8 if level == 0 else 12
    fr = frames(pts)
    rings = []
    for i, (p, (t, A, B), r) in enumerate(zip(pts, fr, radii)):
        seg = 1.0 + (0.035 if (i % 2 == 0 and i > 2 and level) else 0.0)        # armoured segments
        up = B if B.z > 0 else -B
        rings.append(oval(p, A, up, r * seg, r * 0.94 * seg, n, p=2.3))
    end = pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.035
    loft(g, rings, M["Tail"], cap0=True, cap1=end, attrs=lambda i: {"fu": i / (len(rings) - 1)})
    return pts, radii


def tail_point(pts, radii, f):
    i = f * (len(pts) - 1)
    i0 = min(int(i), len(pts) - 2)
    return pts[i0].lerp(pts[i0 + 1], i - i0), (pts[i0 + 1] - pts[i0]).normalized(), float(np.interp(i, range(len(radii)), radii))


def tail_armor(g, tree, pts, radii):
    """Overlapping keel scutes down the top of the tail and a row of slate plates down each flank: banded armour, smaller toward its end."""
    rnd = rng_for("tailplates")
    for k, f in enumerate((0.08, 0.17, 0.26, 0.35, 0.44, 0.53, 0.62, 0.71)):
        p, t, r = tail_point(pts, radii, f)
        loc, nn = cast(tree, p, Z - t * t.dot(Z), 0.5)
        sc = 1.0 - 0.06 * k
        plate(g, tree, loc, t, 0.200 * sc, 0.160 * sc, M["Tail"], outline="keel" if k % 2 else "shard", thick=0.020, lift=0.026,
              ridge=0.016, seed=rnd.random(), shade=1.0)
    for k, f in enumerate((0.10, 0.26, 0.42, 0.58)):
        p, t, r = tail_point(pts, radii, f)
        for side in (1, -1):
            loc, nn = cast(tree, p + t * 0.04, (X * side + Z * 0.35), 0.5)
            sc = 1.0 - 0.10 * k
            plate(g, tree, loc, t - Z * 0.25, 0.170 * sc, 0.140 * sc, M["Tail"], outline="chevron", thick=0.017, lift=0.020, ridge=0.012,
                  seed=rnd.random(), shade=1.0)


def tail_crystals(g, tree, pts, radii):
    """A crystal ridge along the top of its second half, growing toward the end and flowing into the plume: a calyx of short crystals
    round the tail's end and a fan of long shards spread back from it, up and down and a little to each side (their roots in the end)."""
    cr = M["CrystalArmor"]
    for k, (f, L, r) in enumerate(((0.40, 0.090, 0.026), (0.50, 0.115, 0.031), (0.60, 0.145, 0.037), (0.70, 0.180, 0.044),
                                   (0.79, 0.220, 0.052), (0.88, 0.260, 0.060))):
        p, t, rr = tail_point(pts, radii, f)
        loc, nn = cast(tree, p, Z - t * t.dot(Z), 0.5)
        side = 1 if k % 2 else -1
        axis = (nn * 0.60 + t * 0.80 + X * side * 0.10).normalized()
        crystal(g, loc, axis, L, r, cr, ("tailridge", k), kind="blade" if k % 2 else "prism", flat=0.60, wide=t, sides=6)
    for k, f in enumerate((0.78, 0.89)):                 # pairs on the flanks of its last length, leading into the plume
        p, t, rr = tail_point(pts, radii, f)
        for side in (1, -1):
            loc, nn = cast(tree, p, X * side + Z * 0.25, 0.5)
            axis = (nn * 0.55 + t * 0.85).normalized()
            crystal(g, loc, axis, 0.14 + 0.05 * k, 0.034 + 0.008 * k, cr, ("tailside", k, side), kind="prism", flat=0.7, sides=5)
    end, t, r = tail_point(pts, radii, 1.0)
    end = end + t * 0.012
    up = (Z - t * t.dot(Z)).normalized()
    sd = t.cross(up).normalized()
    for k in range(4):                                   # the knot: a calyx of short crystals
        ang = 360 * k / 4 + 45
        o = turn(up, t, ang)
        loc, nn = cast(tree, end - t * 0.03 + o * 0.02, o, 0.3)
        crystal(g, loc, (o * 0.55 + t * 0.85).normalized(), 0.150, 0.040, cr, ("knot", k), kind="stub", flat=0.6, wide=t, sides=5)
    plume = [(0, 0, 0.660, 0.082, "blade"), (24, 8, 0.540, 0.068, "prism"), (-20, -7, 0.470, 0.062, "blade"), (46, -10, 0.420, 0.056, "prism"),
             (-40, 12, 0.360, 0.050, "prism"), (12, 26, 0.430, 0.056, "blade"), (8, -27, 0.400, 0.054, "blade"), (66, 4, 0.270, 0.042, "stub"),
             (-58, -4, 0.250, 0.040, "prism"), (34, -24, 0.320, 0.046, "blade")]
    for k, (pitch, yaw, L, rr, kind) in enumerate(plume):
        d = turn(turn(t, sd, -pitch), up, yaw)
        root = end + d * 0.01
        crystal(g, root, d, L, rr, cr, ("plume", k), kind=kind, flat=0.55, wide=up if kind == "blade" else None, sides=6, sink=0.09)


# ======================================================================================================================================
# assembling the pieces
# ======================================================================================================================================
JOINTS = ["Body", "Head", "Antlers", "LegFL", "LegFR", "LegBL", "LegBR", "Tail"]
LEG_KEYS = {"LegFL": ("fore", 1), "LegFR": ("fore", -1), "LegBL": ("hind", 1), "LegBR": ("hind", -1)}
GLOW_EYE = "48d8ff"       # the iris (Neon in the game; PetRig names it Head_Glow_<hex> and welds it to the head)
GLOW_GLINT = "ffffff"     # the catch-lights
GLOW_ANTLER = "5fe3ff"    # the frozen light over the antlers' highest terminations (PetRig draws it 70% see-through and pulses it)
GLOWS = {"HeadGlow": GLOW_EYE, "HeadGlint": GLOW_GLINT, "AntlersGlow": GLOW_ANTLER}


def build_model(level, coll, suffix=""):
    pieces = {}
    tips = {}
    # the body
    g = Geo(N + "Source_Body" + suffix)
    build_body_skin(g, level)
    if level >= 1:
        tree = g.tree()
        body_armor(g, tree)
        if level >= 3:
            body_crystals(g, tree)
    pieces["Body"] = g
    # the head
    g = Geo(N + "Source_Head" + suffix)
    build_skull(g, level)
    if level >= 1:
        tree = g.tree()
        gl, gw = Geo(N + "Source_HeadGlow" + suffix), Geo(N + "Source_HeadGlint" + suffix)
        for side in (1, -1):
            build_eye(g, side)
            build_lid(g, side, True)
            build_lid(g, side, False)
            build_nostril(g, side)
            build_ears(g, tree, side)
            build_pedicle(g, side)
            build_eye_glow(gl, gw, side)
        build_frill(g)
        head_plates(g, tree)
        if level >= 3:
            head_crystals(g, tree)
        head_attrs(g)
        pieces["HeadGlow"] = gl
        pieces["HeadGlint"] = gw
    pieces["Head"] = g
    # the antlers
    if level == 0 or level >= 2:
        g = Geo(N + "Source_Antlers" + suffix)
        ag = Geo(N + "Source_AntlersGlow" + suffix) if level >= 1 else None
        for side, tag in ((1, "L"), (-1, "R")):
            t = []
            build_antler(g, side, level, t, glow=ag)
            tips[tag] = max(t, key=lambda p: p.z)
        pieces["Antlers"] = g
        if ag is not None:
            pieces["AntlersGlow"] = ag
    # the legs
    for j, (kind, side) in LEG_KEYS.items():
        g = Geo(N + "Source_" + j + suffix)
        build_leg_skin(g, kind, side, level)
        build_hoof(g, kind, side, level)
        if level >= 1:
            tree = g.tree()
            leg_armor(g, tree, kind, side)
            if level >= 3:
                leg_crystals(g, tree, kind, side)
        # the stance: each leg turned a few degrees about its pivot
        bmesh.ops.rotate(g.bm, verts=g.bm.verts[:], cent=PIVOT[j], matrix=Matrix.Rotation(math.radians(STANCE[j]), 3, "X"))
        pieces[j] = g
    # the tail
    g = Geo(N + "Source_Tail" + suffix)
    pts, radii = build_tail_skin(g, level)
    if level >= 1:
        tree = g.tree()
        tail_armor(g, tree, pts, radii)
        if level >= 3:
            tail_crystals(g, tree, pts, radii)
    pieces["Tail"] = g
    objs = {k: g.finish(coll) for k, g in pieces.items()}
    return objs, tips


def antler_pivot():
    return (antler_base(1)[0] + antler_base(-1)[0]) / 2


def pivot_points():
    p = dict(PIVOT)
    p["Antlers"] = antler_pivot()
    return p


def cube(coll, name, at):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.02, matrix=Matrix.Translation(at))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.hide_render = True             # markers for the game's joints and effects, never part of the look
    return o


def markers(coll, tips):
    out = [cube(coll, N + "Pivot_" + j, p) for j, p in pivot_points().items()]
    for tag in ("L", "R"):
        if tag in tips:
            out.append(cube(coll, N + "Point_Antlers_Tip" + tag, tips[tag]))
    return out


# ======================================================================================================================================
# materials: ten identities, each reading the per-vertex values the pieces carry
# ======================================================================================================================================
def srgb(r, g, b):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


PAL = {
    # body: deep glacial blue, muted blue-grey, frosted slate, pale icy blue
    "glacial": srgb(26, 52, 104), "glacialdeep": srgb(16, 32, 70), "bluegrey": srgb(56, 80, 120), "slate": srgb(86, 106, 140),
    "icy": srgb(168, 196, 224), "frostslate": srgb(122, 140, 168),
    # secondaries: silver-blue, cold white, desaturated cyan, dark crystalline blue
    "silver": srgb(148, 172, 204), "cold": srgb(226, 236, 246), "dcyan": srgb(112, 170, 190), "darkcrys": srgb(20, 30, 56),
    # crystals: translucent pale cyan, bright glacial blue, clear icy white, deep sapphire
    "pcyan": srgb(150, 224, 246), "gblue": srgb(58, 148, 232), "white": srgb(236, 249, 255), "sapphire": srgb(22, 50, 132),
    "sapphire2": srgb(36, 82, 178),
    # eyes
    "iris": srgb(64, 214, 255), "irislite": srgb(190, 244, 255), "sclera": srgb(14, 26, 58), "pupil": srgb(4, 8, 22),
}


class NT:
    """A small helper for writing a material's node graph as expressions."""

    def __init__(self, mat):
        self.t = mat.node_tree
        self.bsdf = next(n for n in self.t.nodes if n.type == "BSDF_PRINCIPLED")
        self.cache = {}

    def node(self, kind, **props):
        n = self.t.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def attr(self, name):
        if name not in self.cache:
            self.cache[name] = self.node("ShaderNodeAttribute", attribute_name=name).outputs["Fac"]
        return self.cache[name]

    def geo(self, out):
        if "geo" not in self.cache:
            self.cache["geo"] = self.node("ShaderNodeNewGeometry")
        return self.cache["geo"].outputs[out]

    def obj(self):
        if "obj" not in self.cache:
            self.cache["obj"] = self.node("ShaderNodeTexCoord").outputs["Object"]
        return self.cache["obj"]

    def xyz(self, vec, i):
        if ("sep", vec) not in self.cache:
            n = self.node("ShaderNodeSeparateXYZ")
            self.t.links.new(vec, n.inputs[0])
            self.cache[("sep", vec)] = n
        return self.cache[("sep", vec)].outputs[i]

    def _in(self, sock, v):
        if isinstance(v, (int, float, tuple)):
            sock.default_value = v
        else:
            self.t.links.new(v, sock)

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        return n.outputs[0]

    def ramp(self, x, a, b):
        n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        self._in(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = a
        n.inputs["From Max"].default_value = b
        return n.outputs["Result"]

    def mix(self, a, b, f, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self._in(n.inputs[0], f)
        self._in(n.inputs[6], a)
        self._in(n.inputs[7], b)
        return n.outputs[2]

    def noise(self, scale, detail=3.0):
        n = self.node("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        self.t.links.new(self.obj(), n.inputs["Vector"])
        return n.outputs["Fac"]

    def cells(self, scale, feature="DISTANCE_TO_EDGE"):
        n = self.node("ShaderNodeTexVoronoi", feature=feature)
        n.inputs["Scale"].default_value = scale
        self.t.links.new(self.obj(), n.inputs["Vector"])
        return n.outputs["Distance"]

    def cell_tone(self, scale):
        """a random value per scale (the same cells as cells(scale))"""
        n = self.node("ShaderNodeTexVoronoi", feature="F1")
        n.inputs["Scale"].default_value = scale
        self.t.links.new(self.obj(), n.inputs["Vector"])
        return self.xyz(n.outputs["Color"], 0)

    def bevel(self, radius):
        n = self.node("ShaderNodeBevel")
        n.samples = 8
        n.inputs["Radius"].default_value = radius
        return n.outputs["Normal"]

    def edge(self, radius):
        """1 along the facets' edges, 0 on their faces: how far the rounded (bevel) normal leans from the true one"""
        d = self.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        self.t.links.new(self.bevel(radius), d.inputs[0])
        self.t.links.new(self.geo("Normal"), d.inputs[1])
        return self.ramp(self.math("SUBTRACT", 1.0, d.outputs["Value"]), 0.004, 0.06)

    def out(self, colour, rough, height=None, strength=0.25, dist=0.003, normal=None):
        self._in(self.bsdf.inputs["Base Color"], colour)
        self._in(self.bsdf.inputs["Emission Color"], colour)
        self.bsdf.inputs["Emission Strength"].default_value = 0.0
        self._in(self.bsdf.inputs["Roughness"], rough)
        self.bsdf.inputs["Metallic"].default_value = 0.0
        nrm = normal
        if height is not None:
            bump = self.node("ShaderNodeBump")
            bump.inputs["Strength"].default_value = strength
            bump.inputs["Distance"].default_value = dist
            self._in(bump.inputs["Height"], height)
            if normal is not None:
                self.t.links.new(normal, bump.inputs["Normal"])
            nrm = bump.outputs["Normal"]
        if nrm is not None:
            self.t.links.new(nrm, self.bsdf.inputs["Normal"])


def crystal_graph(nt, root, mid, high, tip, rough=0.10, edge_k=0.75, facet_k=0.28):
    """Solid crystal painted as glass: dark at its root where it leaves the body, clearing through its body to an icy-white termination;
    each facet a slightly different depth of colour, the edges bright, the edges rounded in the normal map (controlled bevels)."""
    fu, seed, facet = nt.attr("fu"), nt.attr("seed"), nt.attr("facet")
    col = nt.mix(root, mid, nt.ramp(fu, 0.03, 0.30))
    col = nt.mix(col, high, nt.ramp(fu, 0.32, 0.78))
    col = nt.mix(col, tip, nt.ramp(fu, 0.80, 1.0))
    col = nt.mix(col, PAL["white"], nt.math("MULTIPLY", nt.math("SUBTRACT", facet, 0.45), facet_k, clamp=True))
    col = nt.mix(col, PAL["sapphire"], nt.math("MULTIPLY", nt.math("SUBTRACT", 0.40, facet), facet_k * 1.4, clamp=True))
    band = nt.ramp(nt.noise(26.0, 2.0), 0.55, 0.70)              # frozen fractures inside it
    col = nt.mix(col, PAL["white"], nt.math("MULTIPLY", band, 0.18))
    edge = nt.edge(0.005)
    col = nt.mix(col, PAL["white"], nt.math("MULTIPLY", edge, edge_k))
    col = nt.mix(col, (0, 0, 0, 1), nt.math("MULTIPLY", seed, 0.10))
    r = nt.math("ADD", rough, nt.math("MULTIPLY", facet, 0.08))
    nt.out(col, r, nt.math("MULTIPLY", band, 0.4), strength=0.08, dist=0.002, normal=nt.bevel(0.005))


def make_materials():
    mats = []
    for name in MATS:
        m = bpy.data.materials.new(N + name)
        nt = NT(m)
        fu, fv, seed, shade, under = (nt.attr(k) for k in ("fu", "fv", "seed", "shade", "under"))
        if name in ("Body", "Tail"):
            # a deep glacial-blue back, blue-grey flanks, a frosted-slate belly; hide of fine scales, each its own tone, their edges
            # catching frosted slate; frost dusting where it would settle; the armour plates (shade 1) frosted slate with pale chipped edges
            z = nt.xyz(nt.obj(), 2)
            nz = nt.xyz(nt.geo("Normal"), 2)
            col = nt.mix(PAL["bluegrey"], PAL["glacial"], nt.ramp(nz, -0.05, 0.55))
            col = nt.mix(col, PAL["glacialdeep"], nt.math("MULTIPLY", nt.ramp(nz, 0.45, 0.95), 0.75))
            col = nt.mix(col, PAL["frostslate"], nt.math("MULTIPLY", nt.ramp(nz, -0.30, -0.85), 0.85))
            col = nt.mix(col, PAL["silver"], nt.math("MULTIPLY", nt.ramp(z, 0.40, 0.14), 0.45))           # frost gathers on the lower legs
            if name == "Tail":
                col = nt.mix(col, PAL["glacialdeep"], nt.math("MULTIPLY", nt.ramp(fu, 0.3, 1.0), 0.35))
            mott = nt.noise(5.0, 4.0)
            col = nt.mix(col, PAL["slate"], nt.math("MULTIPLY", nt.ramp(mott, 0.50, 0.80), 0.25))
            sc = nt.cells(95.0)
            tone = nt.cell_tone(95.0)
            col = nt.mix(col, (0, 0, 0, 1), nt.math("MULTIPLY", tone, 0.16))
            edge = nt.math("SUBTRACT", 1.0, nt.ramp(sc, 0.0, 0.11))
            col = nt.mix(col, PAL["slate"], nt.math("MULTIPLY", edge, 0.30))
            band = nt.math("ABSOLUTE", nt.math("SUBTRACT", nt.math("FRACT", nt.math("MULTIPLY", nt.noise(1.6, 1.0), 9.0)), 0.5))
            col = nt.mix(col, PAL["glacialdeep"], nt.math("MULTIPLY", nt.ramp(band, 0.40, 0.50), 0.18))   # faint darker scale bands
            dust = nt.math("MULTIPLY", nt.ramp(nt.noise(22.0, 3.0), 0.60, 0.72), nt.ramp(nz, 0.35, 0.85))
            col = nt.mix(col, PAL["icy"], nt.math("MULTIPLY", dust, 0.40))                                # frost dusting
            # the plates
            pl = nt.math("MULTIPLY", shade, 1.0)
            pc = nt.mix(PAL["glacial"], PAL["bluegrey"], nt.math("ADD", nt.math("MULTIPLY", seed, 0.45), nt.math("MULTIPLY", fu, 0.35)))
            pc = nt.mix(pc, PAL["glacialdeep"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.30)), 0.65))
            pe = nt.edge(0.006)
            pc = nt.mix(pc, PAL["silver"], nt.math("MULTIPLY", pe, 0.85))
            pc = nt.mix(pc, PAL["icy"], nt.math("MULTIPLY", nt.ramp(fu, 0.80, 1.0), 0.50))
            col = nt.mix(col, pc, pl)
            height = nt.math("ADD", nt.math("MULTIPLY", nt.ramp(sc, 0.0, 0.14), nt.math("SUBTRACT", 1.0, pl)),
                             nt.math("MULTIPLY", nt.noise(30.0, 3.0), pl))
            rough = nt.math("ADD", 0.60, nt.math("MULTIPLY", pl, -0.18))
            nt.out(col, rough, height, strength=0.34, dist=0.004, normal=nt.bevel(0.006))
        elif name == "NeckChestArmor":
            # frost armour: silver-blue, darker at the root where it leaves the hide, cold white only along its edges and free tip
            col = nt.mix(srgb(70, 96, 140), srgb(118, 144, 182), nt.ramp(fu, 0.10, 0.75))
            col = nt.mix(col, PAL["dcyan"], nt.math("MULTIPLY", nt.ramp(seed, 0.3, 1.0), 0.30))
            col = nt.mix(col, PAL["glacial"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.25)), 0.60))
            grain = nt.noise(60.0, 4.0)
            col = nt.mix(col, PAL["glacial"], nt.math("MULTIPLY", nt.ramp(grain, 0.55, 0.80), 0.20))
            col = nt.mix(col, PAL["cold"], nt.math("MULTIPLY", nt.ramp(fu, 0.90, 1.0), 0.55))
            col = nt.mix(col, PAL["cold"], nt.math("MULTIPLY", nt.edge(0.005), 0.85))
            ridge = nt.math("SUBTRACT", 1.0, nt.ramp(nt.math("ABSOLUTE", fv), 0.0, 0.35))
            nt.out(col, nt.math("ADD", 0.38, nt.math("MULTIPLY", grain, 0.12)), nt.math("ADD", nt.math("MULTIPLY", grain, 0.5), ridge),
                   strength=0.2, dist=0.003, normal=nt.bevel(0.006))
        elif name == "Face":
            # blue-grey hide, darker deep glacial round the eyes (shade), paler under the jaw and throat (under), the nasal bridge lighter
            col = nt.mix(PAL["bluegrey"], PAL["glacial"], nt.math("MULTIPLY", nt.ramp(nt.xyz(nt.geo("Normal"), 2), 0.2, 0.95), 0.55))
            col = nt.mix(col, PAL["glacialdeep"], nt.math("MULTIPLY", shade, 0.85))
            col = nt.mix(col, PAL["icy"], nt.math("MULTIPLY", under, 0.75))
            col = nt.mix(col, PAL["slate"], nt.math("MULTIPLY", nt.ramp(fu, 0.55, 0.95), nt.math("MULTIPLY", fv, -1.0)))
            sc = nt.cells(115.0)
            col = nt.mix(col, PAL["slate"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(sc, 0.0, 0.1)), 0.15))
            col = nt.mix(col, PAL["silver"], nt.math("MULTIPLY", nt.edge(0.004), 0.45))
            nt.out(col, 0.52, nt.ramp(sc, 0.0, 0.12), strength=0.10, dist=0.002, normal=nt.bevel(0.004))
        elif name == "Antler":
            crystal_graph(nt, PAL["sapphire"], PAL["gblue"], PAL["pcyan"], PAL["white"], rough=0.12, edge_k=0.7, facet_k=0.32)
        elif name == "CrystalArmor":
            crystal_graph(nt, PAL["sapphire2"], PAL["pcyan"], srgb(196, 238, 252), PAL["white"], rough=0.08, edge_k=0.6, facet_k=0.26)
        elif name == "Hoof":
            # dark crystalline blue, its edges catching silver, its underside darker still, fine growth lines
            col = nt.mix(PAL["darkcrys"], srgb(44, 62, 104), nt.ramp(fu, 0.0, 1.0))
            col = nt.mix(col, PAL["silver"], nt.math("MULTIPLY", nt.edge(0.005), 0.55))
            col = nt.mix(col, srgb(8, 12, 22), nt.ramp(nt.xyz(nt.geo("Normal"), 2), -0.6, -0.95))
            lines = nt.math("FRACT", nt.math("MULTIPLY", nt.xyz(nt.obj(), 2), 140.0))
            nt.out(col, 0.28, nt.math("MULTIPLY", lines, 0.4), strength=0.1, dist=0.001, normal=nt.bevel(0.004))
        elif name == "Toe":
            col = nt.mix(PAL["silver"], srgb(206, 226, 244), nt.ramp(fu, 0.2, 1.0))
            col = nt.mix(col, PAL["glacial"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.2)), 0.5))
            col = nt.mix(col, PAL["white"], nt.math("MULTIPLY", nt.edge(0.004), 0.5))
            nt.out(col, 0.30, nt.noise(50.0), strength=0.15, dist=0.002, normal=nt.bevel(0.004))
        elif name == "Eye":
            # the ball deep blue-black; the iris arctic cyan, paler at its inner ring; a narrow upright pupil; one icy-white catch-light
            ang = fu
            iris = nt.ramp(ang, 0.80, 0.86)
            col = nt.mix(PAL["sclera"], nt.mix(PAL["iris"], PAL["irislite"], nt.ramp(ang, 0.94, 0.985)), iris)
            px = nt.math("DIVIDE", shade, 0.115)
            py = nt.math("DIVIDE", fv, 0.26)
            pr = nt.math("ADD", nt.math("MULTIPLY", px, px), nt.math("MULTIPLY", py, py))
            col = nt.mix(col, PAL["pupil"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(pr, 0.85, 1.05)), nt.ramp(ang, 0.9, 0.95)))
            dx = nt.math("SUBTRACT", shade, 0.22)
            dy = nt.math("SUBTRACT", fv, 0.29)
            spot = nt.math("ADD", nt.math("MULTIPLY", dx, dx), nt.math("MULTIPLY", dy, dy))
            col = nt.mix(col, PAL["white"], nt.math("SUBTRACT", 1.0, nt.ramp(spot, 0.002, 0.006)))
            col = nt.mix(col, PAL["pupil"], under)                  # the pupil lens: dark, and matte, so it never mirrors the light
            nt.out(col, nt.math("ADD", 0.06, nt.math("MULTIPLY", under, 0.55)))
        elif name == "Detail":
            # ears (cupped front darker), the pedicles (silver-blue bone), the nostrils (shade 1: dark)
            col = nt.mix(PAL["bluegrey"], PAL["silver"], nt.ramp(fu, 0.3, 1.0))
            col = nt.mix(col, PAL["glacialdeep"], nt.math("MULTIPLY", under, 0.65))
            col = nt.mix(col, PAL["silver"], nt.math("MULTIPLY", nt.ramp(seed, 0.7, 0.9), 0.6))
            col = nt.mix(col, srgb(10, 16, 32), shade)
            col = nt.mix(col, PAL["cold"], nt.math("MULTIPLY", nt.edge(0.004), 0.45))
            nt.out(col, 0.45, nt.noise(40.0), strength=0.15, dist=0.002, normal=nt.bevel(0.004))
        mats.append(m)
    return mats


def assign(objs, mats):
    """Gives every piece the ten material slots, keeping each face's identity (clearing the slots would reset every face to the first)."""
    for o in objs:
        idx = [0] * len(o.data.polygons)
        o.data.polygons.foreach_get("material_index", idx)
        o.data.materials.clear()
        for m in mats:
            o.data.materials.append(m)
        o.data.polygons.foreach_set("material_index", idx)
        o.data.update()


def glow_material(hexv):
    name = N + "Glow_" + hexv
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    c = srgb(int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16))
    b.inputs["Base Color"].default_value = c
    b.inputs["Emission Color"].default_value = c
    b.inputs["Emission Strength"].default_value = 2.5
    return m


# ======================================================================================================================================
# review renders
# ======================================================================================================================================
def world_setup():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Studio")
    sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.10, 0.10, 0.105, 1)
    bg.inputs[1].default_value = 1.0
    cam = bpy.data.cameras.new("ReviewCam")
    co = bpy.data.objects.new("ReviewCam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"


def lights_setup():
    """Neutral studio light: a soft key, a fill, a rim and a low back light, all white; a dark grey floor."""
    sc = bpy.context.scene
    for name, energy, loc, size in (("Key", 520, (-2.6, -3.4, 3.8), 3.0), ("Fill", 220, (3.4, -2.4, 1.8), 3.5), ("Rim", 420, (1.2, 3.8, 3.4), 2.5),
                                    ("Back", 140, (-3.0, 3.0, 1.4), 3.0)):
        L = bpy.data.lights.new(name, "AREA")
        L.energy = energy
        L.size = size
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (V(0, 0, 1.0) - V(*loc)).to_track_quat("-Z", "Y").to_euler()
    me = bpy.data.meshes.new("Floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=14)
    bm.to_mesh(me)
    bm.free()
    fl = bpy.data.objects.new("Floor", me)
    sc.collection.objects.link(fl)
    m = bpy.data.materials.new("FloorGrey")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.06, 0.06, 0.065, 1)
    b.inputs["Roughness"].default_value = 0.85
    me.materials.append(m)
    return fl


def engine(kind, samples=48):
    sc = bpy.context.scene
    if kind == "clay":
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light = "STUDIO"
        sh.color_type = "SINGLE"
        sh.single_color = (0.52, 0.53, 0.56)
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.cavity_ridge_factor = 1.0
        sh.cavity_valley_factor = 1.0
        sh.show_object_outline = True
        sh.object_outline_color = (0.0, 0.0, 0.0)
        sh.show_specular_highlight = True
        sh.background_type = "VIEWPORT"
        sh.background_color = (0.11, 0.11, 0.115)
        sc.display.render_aa = "8"
    else:
        sc.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except TypeError:
            sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True


VIEWS = {
    "front": (V(0, -1, 0), True), "side": (V(1, 0, 0), True), "back": (V(0, 1, 0), True), "top": (V(0.0001, 0.0, 1), True),
    "threeq": (V(0.95, -1.0, 0.42), False), "beauty": (V(-1.05, -1.15, 0.28), False), "rearq": (V(-0.9, 1.0, 0.45), False),
    "head": (V(0.8, -1.0, 0.22), False), "headside": (V(1, -0.05, 0.02), True), "headfront": (V(0.0, -1, 0.12), True),
    "low": (V(0.6, -1.0, -0.12), False),
}


def bbox(objs):
    pts = [o.matrix_world @ V(*c) for o in objs for c in o.bound_box]
    lo = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))
    hi = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    return lo, hi


def shoot(path, view, objs, size=720, target=None, extent=None, lens=55, transparent=False, wide=1.0):
    sc = bpy.context.scene
    cam = sc.camera
    d, ortho = VIEWS[view] if isinstance(view, str) else view
    d = d.normalized()
    lo, hi = bbox(objs)
    c = target if target is not None else (lo + hi) / 2
    radius = extent if extent is not None else (hi - lo).length / 2
    up = Z if abs(d.z) < 0.95 else -Y
    cam.data.clip_start, cam.data.clip_end = 0.01, 100
    if ortho:
        cam.data.type = "ORTHO"
        right = up.cross(-d).normalized()
        upv = (-d).cross(right).normalized()
        corners = [V(x, y, z) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        e1 = max(abs((p - c).dot(right)) for p in corners)
        e2 = max(abs((p - c).dot(upv)) for p in corners)
        cam.data.ortho_scale = (extent * 2) if extent is not None else max(e1 / wide, e2) * 2 * 1.08 * wide
        cam.location = c + d * 10
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
        fov = 2 * math.atan(18 / lens)
        cam.location = c + d * (radius / math.sin(fov / 2) * 1.02)
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = int(size * wide), size
    sc.render.film_transparent = transparent
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_px(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def save_px(path, px):
    h, w = px.shape[:2]
    img = bpy.data.images.new("sheet_out", w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def resize(px, size):
    h, w = px.shape[:2]
    ys = (np.arange(size[0]) * h / size[0]).astype(int)
    xs = (np.arange(size[1]) * w / size[1]).astype(int)
    return px[np.ix_(ys, xs)]


# a 5 x 7 pixel font for the labels on the review sheets
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "-": "00000 00000 00000 11111 00000 00000 00000", ".": "00000 00000 00000 00000 00000 01100 01100",
    ":": "00000 01100 01100 00000 01100 01100 00000", "+": "00000 00100 00100 11111 00100 00100 00000",
    "(": "00010 00100 01000 01000 01000 00100 00010", ")": "01000 00100 00010 00010 00010 00100 01000",
    "/": "00001 00010 00010 00100 01000 01000 10000", " ": "00000 00000 00000 00000 00000 00000 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011",
}


def label(canvas, text, x, y_top, scale=3):
    """Writes text (upper case) on a canvas whose rows run bottom-up, with a dark bar behind it."""
    H_ = canvas.shape[0]
    w = (len(text) * 6 + 2) * scale
    y0 = H_ - y_top - 9 * scale
    canvas[max(0, y0):H_ - y_top, x:x + w, :3] = canvas[max(0, y0):H_ - y_top, x:x + w, :3] * 0.25
    for i, ch in enumerate(text.upper()):
        rows = FONT.get(ch, FONT[" "]).split()
        for r, bits in enumerate(rows):
            for c, b in enumerate(bits):
                if b == "1":
                    yy = H_ - y_top - (r + 1) * scale - scale
                    xx = x + (i * 6 + c + 1) * scale
                    canvas[yy:yy + scale, xx:xx + scale, :3] = 0.92


def sheet(tiles, out, cols, tile=600, bg=(0.10, 0.10, 0.105)):
    """tiles: rows of (path, span, label); a span-2 tile is twice as wide."""
    Ht = len(tiles) * tile
    canvas = np.zeros((Ht, cols * tile, 4), dtype=np.float32)
    canvas[..., :3] = bg
    canvas[..., 3] = 1
    for r, row in enumerate(tiles):
        c = 0
        for path, span, text in row:
            im = resize(load_px(path), (tile, tile * span))
            y0 = Ht - (r + 1) * tile
            canvas[y0:y0 + tile, c * tile:(c + span) * tile] = im
            canvas[y0:y0 + tile, c * tile:c * tile + 2, :3] = 0.25
            canvas[y0:y0 + 2, c * tile:(c + span) * tile, :3] = 0.25
            if text:
                label(canvas, text, c * tile + 8, r * tile + 8, scale=3)
            c += span
    save_px(out, canvas)
    return out


CONCEPT_SIDE = os.path.join(K.ROOT, "assets", "concepts", "crops", "Crysalith_side.png")
# how the concept's side view maps to the model: metres per pixel, and the pixels of the ground line and of the nose's tip
CONCEPT_K, CONCEPT_GROUND, CONCEPT_NOSE_X, CONCEPT_TOP = 0.00300, 843, 126, 80


def concept_pair(objs, out, nose_y):
    """The model's side view (from its left, like the painting) at the painting's scale, beside it."""
    lo, hi = bbox([o for o in objs if not o.hide_render])
    k = hi.z / (CONCEPT_GROUND - CONCEPT_TOP)          # the painting scaled to the model: ground to the antlers' tips
    across = nose_y + (512 - CONCEPT_NOSE_X) * k
    target = V(0, across, (CONCEPT_GROUND - 512) * k)
    sc = bpy.context.scene
    keep = VIEWS["side"]
    VIEWS["side_l"] = (V(1, 0, 0), True)
    tmp = shoot(os.path.join(REVIEW, "_concept_side.png"), "side_l", objs, size=1024, target=target, extent=512 * k, transparent=True)
    a = load_px(tmp)                                # seen from its left, its nose points left, like the painting's
    con = load_px(CONCEPT_SIDE)
    m = a[..., 3:4]
    model = a[..., :3] * m + np.array(sc.world.node_tree.nodes["Background"].inputs[0].default_value[:3]) * (1 - m)
    both = np.concatenate([con, np.dstack([model, np.ones_like(m)])], axis=1)
    edge = (m[..., 0] > 0.5)
    rim = edge & ~(np.roll(edge, 2, 0) & np.roll(edge, -2, 0) & np.roll(edge, 2, 1) & np.roll(edge, -2, 1))
    ov = con.copy()
    ov[rim, :3] = (0.3, 1.0, 0.6)
    save_px(out, both)
    save_px(out.replace(".png", "_overlay.png"), ov)
    VIEWS["side"] = keep
    return out


def set_visible(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_viewport = not on


def stage_renders(stage, model, kind):
    engine(kind)
    parts = list(model.values())
    if os.environ.get("CRY_BEAUTY"):          # a quick look: two large views only
        shoot(os.path.join(REVIEW, stage + "_beauty.png"), "beauty", parts, size=900, lens=50, wide=1.5, target=V(0, -0.15, 1.35), extent=1.75)
        shoot(os.path.join(REVIEW, stage + "_beauty2.png"), (V(1.0, -0.55, 0.30), False), parts, size=900, lens=50, wide=1.5,
              target=V(0, -0.15, 1.35), extent=1.75)
        return
    head = [o for k, o in model.items() if k.startswith("Head") or k == "Antlers"]
    tag = os.path.join(REVIEW, stage)
    shots_ = {}
    for v in ("front", "side", "back", "top", "threeq", "rearq"):
        shots_[v] = shoot("%s_%s.png" % (tag, v), v, parts, size=640)
    hc = H(0.0, 0.10, 0.0)
    hs = [shoot("%s_head_%s.png" % (tag, v), v, head if v != "headside" else [model["Head"]], target=hc if v != "head" else None,
                extent=0.50 if v != "head" else None, lens=60, size=640) for v in ("head", "headside", "headfront")]
    sheet([[(shots_["front"], 1, "FRONT"), (shots_["side"], 1, "SIDE"), (shots_["back"], 1, "REAR")],
           [(shots_["threeq"], 1, "THREE-QUARTER"), (shots_["rearq"], 1, "REAR THREE-QUARTER"), (shots_["top"], 1, "TOP")],
           [(hs[0], 1, "HEAD"), (hs[1], 1, "HEAD SIDE"), (hs[2], 1, "HEAD FRONT")]],
          tag + "_sheet.png", 3, tile=520)


def report(model):
    total = 0
    for k, o in model.items():
        n = tri_count([o])
        total += n
        print("TRIS %-10s %6d" % (k, n))
    print("TRIS TOTAL", total)
    lo, hi = bbox(list(model.values()))
    print("BOX", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
    return total


# ======================================================================================================================================
# the game pieces: one per joint, unwrapped and baked
# ======================================================================================================================================
EMPTY = (1.0, 0.0, 1.0, 1.0)      # the colour map's fill, so its gutters can be found and bled
MAP_SIZE = {"Body": 2048, "Head": 2048, "Antlers": 2048, "Tail": 2048, "LegFL": 1024, "LegFR": 1024, "LegBL": 1024, "LegBR": 1024}


def select_only(objs, active=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def game_name(j):
    if j in GLOWS:
        return N + j.replace("Glow", "").replace("Glint", "") + "_Glow_" + GLOWS[j]
    return N + j


def make_game(model, coll):
    game = {}
    for j, o in model.items():
        me = o.data.copy()
        me.name = game_name(j)
        g = bpy.data.objects.new(game_name(j), me)
        coll.objects.link(g)
        game[j] = g
    return game


def unwrap(o, joint):
    """Smart projection at the facets' own angle (every hard edge a seam), the eyes and the face given more of the map, packed tight."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    select_only([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    boost = {M["Eye"]: 4.0, M["Face"]: 1.25} if joint == "Head" else {}
    uv = me.uv_layers.active.data
    for mat, k in boost.items():
        loops = [l for p in me.polygons if p.material_index == mat for l in p.loop_indices]
        if not loops:
            continue
        # scale each face's loops about its own island centre: approximated per face (smart projection islands of these are small)
        for p in me.polygons:
            if p.material_index != mat:
                continue
            c = sum((uv[l].uv for l in p.loop_indices), Vector((0, 0))) / len(p.loop_indices)
            for l in p.loop_indices:
                uv[l].uv = c + (uv[l].uv - c) * k
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=0.004, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def px_of(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def bake_piece(o, joint, mats, hide):
    sc = bpy.context.scene
    size = MAP_SIZE[joint]
    imgs = {}
    for kind in ("color", "normal", "roughness", "ao"):
        img = bpy.data.images.new(N + joint + "_" + kind, size, size, alpha=False)
        img.generated_color = EMPTY if kind == "color" else ((0.5, 0.5, 1, 1) if kind == "normal" else (0.5, 0.5, 0.5, 1))
        if kind != "color":
            img.colorspace_settings.name = "Non-Color"
        imgs[kind] = img
    for o2 in hide:
        o2.hide_render = True
    select_only([o])

    def target(img):
        for m in mats:
            t = m.node_tree
            n = t.nodes.get("BakeTarget") or t.nodes.new("ShaderNodeTexImage")
            n.name = "BakeTarget"
            n.image = img
            t.nodes.active = n
    bsdfs = [next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED") for m in mats]
    margin = 12 if size <= 1024 else 16
    sc.cycles.samples = 24
    target(imgs["color"])
    for b in bsdfs:
        b.inputs["Emission Strength"].default_value = 1.0
    bpy.ops.object.bake(type="EMIT", margin=margin, use_clear=True, target="IMAGE_TEXTURES")
    for b in bsdfs:
        b.inputs["Emission Strength"].default_value = 0.0
    target(imgs["roughness"])
    bpy.ops.object.bake(type="ROUGHNESS", margin=margin, use_clear=True, target="IMAGE_TEXTURES")
    sc.cycles.samples = 24
    target(imgs["normal"])
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=margin, use_clear=True, target="IMAGE_TEXTURES")
    sc.world.light_settings.distance = 0.10
    sc.cycles.samples = 64
    target(imgs["ao"])
    bpy.ops.object.bake(type="AO", margin=margin, use_clear=True, target="IMAGE_TEXTURES")
    for o2 in hide:
        o2.hide_render = False
    col, ao = px_of(imgs["color"]), px_of(imgs["ao"])
    empty = (np.abs(col[..., 0] - 1) < 1e-3) & (col[..., 1] < 1e-3) & (np.abs(col[..., 2] - 1) < 1e-3)
    shade = (0.45 + 0.55 * ao[..., :1])
    col[..., :3] = np.where(empty[..., None], col[..., :3], col[..., :3] * shade)
    imgs["color"].pixels.foreach_set(col.ravel())
    imgs["color"].update()
    K.bleed_gutters([imgs["color"], imgs["normal"], imgs["roughness"]])
    os.makedirs(K.OUT, exist_ok=True)
    for kind in ("color", "normal", "roughness"):
        img = imgs[kind]
        img.filepath_raw = os.path.join(K.OUT, N + joint + "_" + kind + ".png")
        img.file_format = "PNG"
        img.save()
        img.pack()
    bpy.data.images.remove(imgs["ao"])
    for m in mats:
        n = m.node_tree.nodes.get("BakeTarget")
        if n:
            m.node_tree.nodes.remove(n)
    m = bpy.data.materials.new(N + joint + "_Baked")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    ci = t.nodes.new("ShaderNodeTexImage")
    ci.image = imgs["color"]
    ni = t.nodes.new("ShaderNodeTexImage")
    ni.image = imgs["normal"]
    ri = t.nodes.new("ShaderNodeTexImage")
    ri.image = imgs["roughness"]
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(ci.outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(ni.outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    t.links.new(ri.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.0
    o.data.materials.clear()
    o.data.materials.append(m)
    return m


def export_fbx(game, mk):
    os.makedirs(K.OUT, exist_ok=True)
    path = os.path.join(K.OUT, PET + ".fbx")
    objs = list(game.values()) + list(mk)
    select_only(objs)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE",
                             add_leaf_bones=False, bake_anim=False)
    raw = open(path, "rb").read()
    fixed = raw.replace(b"/Users/ivan/", b"/Users/user/")
    if fixed != raw:
        open(path, "wb").write(fixed)
    return path


def verify_fbx(path):
    before = set(bpy.data.objects)
    sc = bpy.data.scenes.new("FbxCheck")
    with bpy.context.temp_override(scene=sc):
        bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    out = {}
    for o in new:
        if o.type != "MESH":
            continue
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        out[o.name] = (tuple(round(v, 4) for v in o.scale), tris, tuple(round(v, 3) for v in o.dimensions), len(o.data.materials))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(sc)
    bpy.data.orphans_purge(do_recursive=True)
    return out


def turn_about(o, pivot, axis, deg):
    o.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-pivot) @ o.matrix_world


def save_blend(name):
    """The .blend, written from the scene alone (not the window manager, which remembers this machine's folders), every path relative."""
    os.makedirs(K.TOOLS, exist_ok=True)
    path = os.path.join(K.TOOLS, name)
    render = bpy.context.scene.render
    render.filepath = "//" + "_" * 1020
    render.filepath = "//"
    for img in bpy.data.images:
        rel = img.filepath_raw
        if rel and not rel.startswith("//"):
            rel = "//" + os.path.basename(rel)          # the maps are packed; only their names are kept
        if img.filepath_raw:
            img.filepath_raw = "//" + "_" * 1020        # a path field keeps its old bytes after a shorter path: fill it first
            img.filepath_raw = rel
        for packed in img.packed_files:
            packed.filepath = "//" + "_" * 1020
            packed.filepath = rel
    if os.path.exists(path):
        os.remove(path)
    bpy.data.libraries.write(path, {bpy.context.scene}, path_remap="RELATIVE_ALL", compress=True)
    return path


def scan_file(path):
    raw = open(path, "rb").read()
    if raw[:4] == b"\x28\xb5\x2f\xfd":
        raw = subprocess.run(["zstd", "-dc", path], capture_output=True).stdout
    hits = {}
    for pat in (b"/Users/", b"/private/", b"/tmp/", b"/var/", b"/home/", b"scratchpad"):
        if pat in raw:
            hits[pat.decode()] = raw.count(pat)
    return hits


def stage_blend(name, keep):
    """A stage's .blend: its model alone (no review camera, lights or floor)."""
    gone = []
    for o in list(bpy.context.scene.collection.objects):
        if o.type in ("CAMERA", "LIGHT") or o.name == "Floor":
            gone.append(o)
    for o in gone:
        bpy.context.scene.collection.objects.unlink(o)
    path = save_blend(name)
    for o in gone:
        bpy.context.scene.collection.objects.link(o)
    print("BLEND", path, "SCAN", scan_file(path))


def final_review(game, model, mk):
    """The QA renders and the review sheet: front, side, rear and top (orthographic), three-quarter and rear three-quarter, the beauty
    shot, head close-ups, clay, the concept's side view beside the model, and the joints swung to the game's limits."""
    tag = os.path.join(REVIEW, "final")
    parts = list(game.values())
    engine("cycles", 96)
    R = {}
    for v in ("front", "side", "back", "top", "threeq", "rearq", "low"):
        R[v] = shoot("%s_%s.png" % (tag, v), v, parts, size=900)
    heads = [game["Head"], game["HeadGlow"], game["HeadGlint"], game["Antlers"], game["AntlersGlow"]]
    hc = H(0.0, 0.12, 0.02)
    R["head"] = shoot(tag + "_head.png", (V(0.85, -1.0, 0.20), False), heads[:3], target=hc, extent=0.46, lens=70, size=900)
    R["headside"] = shoot(tag + "_headside.png", "headside", heads[:3], target=hc, extent=0.44, size=900)
    R["headfront"] = shoot(tag + "_headfront.png", "headfront", heads, target=hc + V(0, 0, 0.18), extent=0.62, size=900)
    R["eye"] = shoot(tag + "_eye.png", (V(1.0, -0.55, 0.12), False), heads[:3], target=eye_frame(1)[0], extent=0.11, lens=80, size=900)
    R["beauty"] = shoot(tag + "_beauty.png", "beauty", parts, size=800, lens=50, wide=2.0, target=V(0, 0.15, 1.30), extent=2.15)
    # the joints at the game's limits: legs swung 25 degrees each way, head raised as in the special, antlers swayed, tail turned
    keep = {k: o.matrix_world.copy() for k, o in game.items()}
    piv = pivot_points()
    for j, sgn in (("LegFL", 1), ("LegBR", 1), ("LegFR", -1), ("LegBL", -1)):
        turn_about(game[j], piv[j], X, 25 * sgn)
    for k in ("Head", "HeadGlow", "HeadGlint", "Antlers", "AntlersGlow"):
        turn_about(game[k], piv["Head"], X, 26)
        turn_about(game[k], piv["Head"], Z, 12)
    for k in ("Antlers", "AntlersGlow"):
        turn_about(game[k], turn_about_point(piv["Antlers"], piv["Head"], 26, 12), Z, 7)
    turn_about(game["Tail"], piv["Tail"], Z, 9)
    turn_about(game["Tail"], piv["Tail"], X, -17)
    R["joints"] = shoot(tag + "_joints.png", (V(1.0, -0.35, 0.10), True), parts, size=900)
    R["joints_q"] = shoot(tag + "_joints_q.png", (V(-0.9, -0.9, 0.25), False), parts, size=900)
    # close-ups of the leg joints at +25 (left legs) and -25 (right legs), where a gap would open
    R["jfore"] = shoot(tag + "_jfore.png", (V(1.0, -0.15, 0.05), True), parts, size=900, target=piv["LegFL"] + V(0, -0.05, -0.20), extent=0.42)
    R["jhind"] = shoot(tag + "_jhind.png", (V(-1.0, 0.15, 0.05), True), parts, size=900, target=piv["LegBR"] + V(0, -0.05, -0.20), extent=0.42)
    for k, o in game.items():
        o.matrix_world = keep[k]
    for j, sgn in (("LegFL", -1), ("LegBR", -1), ("LegFR", 1), ("LegBL", 1)):
        turn_about(game[j], piv[j], X, 25 * sgn)
    R["joints2"] = shoot(tag + "_joints2.png", (V(-1.0, -0.2, 0.05), True), parts, size=900)
    R["jfore2"] = shoot(tag + "_jfore2.png", (V(1.0, -0.15, 0.05), True), parts, size=900, target=piv["LegFL"] + V(0, 0.05, -0.20), extent=0.42)
    R["jhind2"] = shoot(tag + "_jhind2.png", (V(-1.0, 0.15, 0.05), True), parts, size=900, target=piv["LegBR"] + V(0, 0.05, -0.20), extent=0.42)
    floor = bpy.data.objects.get("Floor")
    if floor:
        floor.hide_render = True
    R["joints_under"] = shoot(tag + "_joints_under.png", (V(0.55, -0.6, -0.30), False), parts, size=900)
    if floor:
        floor.hide_render = False
    for k, o in game.items():
        o.matrix_world = keep[k]
    engine("clay")
    R["clay"] = shoot(tag + "_clay.png", "threeq", parts, size=900)
    R["clay_side"] = shoot(tag + "_clay_side.png", "side", parts, size=900)
    R["clay_front"] = shoot(tag + "_clay_front.png", "front", parts, size=900)
    R["clay_rear"] = shoot(tag + "_clay_rear.png", "rearq", parts, size=900)
    engine("cycles", 96)
    nose = H(0, *SKULL_TIP).y
    R["pair"] = concept_pair(parts, tag + "_concept_side.png", nose)
    out = os.path.join(K.ROOT, "renders", "pets", "ExclusiveEgg", PET + "_review.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet([
        [(R["front"], 1, "FRONT ORTHO"), (R["side"], 1, "SIDE ORTHO"), (R["back"], 1, "REAR ORTHO"), (R["top"], 1, "TOP ORTHO")],
        [(R["threeq"], 1, "THREE-QUARTER"), (R["rearq"], 1, "REAR THREE-QUARTER"), (R["head"], 1, "HEAD"), (R["headside"], 1, "HEAD SIDE")],
        [(R["beauty"], 2, "BEAUTY - NEUTRAL STUDIO LIGHT"), (R["headfront"], 1, "HEAD FRONT"), (R["eye"], 1, "EYE")],
        [(R["pair"], 2, "CONCEPT SIDE / MODEL SIDE"), (R["joints"], 1, "JOINTS +25 / HEAD UP"), (R["joints2"], 1, "JOINTS -25")],
        [(R["jfore"], 1, "SHOULDER LEG +25"), (R["jfore2"], 1, "SHOULDER LEG -25"), (R["jhind"], 1, "HIP LEG +25"), (R["jhind2"], 1, "HIP LEG -25")],
        [(R["joints_q"], 1, "JOINT SWING 3/4"), (R["joints_under"], 1, "JOINTS FROM BELOW"), (R["clay"], 1, "CLAY"),
         (R["clay_side"], 1, "CLAY SIDE")],
    ], out, 4, tile=600)
    print("REVIEW", out)
    return R


def turn_about_point(p, pivot, pitch, yaw):
    q = Matrix.Rotation(math.radians(yaw), 3, Z) @ Matrix.Rotation(math.radians(pitch), 3, X)
    return pivot + q @ (p - pivot)


if __name__ == "__main__":
    K.start(PET, "ExclusiveEgg")
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)
    world_setup()
    model_coll = K.get_coll(PET + "_Source")
    lvl = min(LEVEL, 3)
    model, tips = build_model(lvl, model_coll)
    report(model)
    marker_coll = K.get_coll(PET + "_Markers")
    if LEVEL <= 3:
        stage_renders(STAGE, model, "clay")
        names = {0: "Crysalith_Blockout.blend", 1: "Crysalith_Anatomy.blend", 3: "Crysalith_Crystals.blend"}
        if LEVEL in names:
            markers(marker_coll, tips)
            stage_blend(names[LEVEL], model)
    if LEVEL >= 4:
        mats = make_materials()
        assign([o for k, o in model.items() if k not in GLOWS], mats)
        for k, hx in GLOWS.items():
            if k in model:
                model[k].data.materials.append(glow_material(hx))
        floor = lights_setup()
    if LEVEL == 4:
        stage_renders(STAGE, model, "cycles")
    if LEVEL >= 5:
        engine("cycles")
        game_coll = K.get_coll(PET)
        game = make_game(model, game_coll)
        for j, o in game.items():
            unwrap(o, j)          # the glows too: Neon ignores it, but every piece leaves with a UV map
        hide = list(model.values()) + [floor]
        for j, o in game.items():
            if j in GLOWS:
                o.data.materials.clear()
                o.data.materials.append(glow_material(GLOWS[j]))
                continue
            bake_piece(o, j, mats, hide)
            print("BAKED", j, flush=True)
        set_visible(list(model.values()), False)
        mk = markers(game_coll, tips)
        print("GAME TRIS", {j: tri_count([o]) for j, o in game.items()}, "TOTAL", tri_count(list(game.values())))
        if LEVEL == 5:
            stage_renders(STAGE, game, "cycles")
    if LEVEL >= 6:
        path = export_fbx(game, mk)
        check = verify_fbx(path)
        for k, v in sorted(check.items()):
            print("FBX", k, "scale", v[0], "tris", v[1], "size", v[2], "materials", v[3])
        print("FBX TOTAL TRIS", sum(v[1] for k, v in check.items() if "_Pivot_" not in k and "_Point_" not in k))
        print("FBX SCAN", scan_file(path))
    if LEVEL == 7:
        final_review(game, model, mk)
    if LEVEL >= 6:
        for name in ("Floor", "ReviewCam", "Key", "Fill", "Rim", "Back"):
            o = bpy.data.objects.get(name)
            if o:
                bpy.data.objects.remove(o, do_unlink=True)
        set_visible(list(model.values()), True)
        bpy.data.orphans_purge(do_recursive=True)
        blend = stage_blend("Crysalith_Final.blend", None)

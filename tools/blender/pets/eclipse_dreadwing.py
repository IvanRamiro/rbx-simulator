"""Eclipse Dreadwing, "Devourer of Stars" (Mythical, Exclusive Egg): a raven-drake modelled by hand, piece by piece, in bmesh.

The idea: an ancient predator built of blades. A raven's hooked beak and long-necked carriage on a drake's armoured frame, every feather a hard,
faceted obsidian blade; two crimson crown horns sweep back off a heavy skull, deep-set crimson eyes watch from under a scowling brow ridge,
and two enormous layered wings carry the only bright colour (violet and crimson at a few feather tips). Pale lavender chevron armour runs down
its breast. Scaled plum-armoured legs end in big hooked talons; a long tapering tail ends in a fan of blades.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/blender/pets/eclipse_dreadwing.py -- <stage> [--review DIR]

Stages, each building everything before it: blockout | anatomy | wings | detail | materials | bake | export | review | all ("all" = review).
Each stage renders its own front, side, back and three-quarter views (and close-ups) into the review folder.

Faces -Y, Z up, 1 unit = 1 metre. The game animates it as a jointed pet (PetRig.Profiles.EclipseDreadwing, animateWinged): one mesh per joint,
EclipseDreadwing_{Body,Head,WingL,WingR,Tail}, each with one baked 2048 material (colour, normal, roughness), and a tiny cube
EclipseDreadwing_Pivot_<Joint> at each joint's centre of rotation. The wings rest extended and flap about the shoulder.

What touches what: the head's neck socket sits over the top of the neck (the head turns about the joint at the top of the neck, its collar
overlapping the neck); each wing's shoulder knuckle is a rounded mass centred on its pivot, buried in the shoulder of the body, so a flap turns
it in place; the tail's root mass is centred on its pivot inside the rump; every feather's root is sunk into what carries it; the toes are
sunk into the foot, the claws into the toes, the horns into the skull, the eyes into their sockets.
"""
import collections
import math
import os
import random
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
STAGES = ["blockout", "anatomy", "wings", "detail", "materials", "bake", "export", "review"]
STAGE = ARGS[0] if ARGS else "anatomy"
if STAGE == "all":
    STAGE = "review"
LEVEL = STAGES.index(STAGE)
REVIEW = ARGS[ARGS.index("--review") + 1] if "--review" in ARGS else os.path.join(K.ROOT, "renders", "pets", "ExclusiveEgg", "stages")
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
os.makedirs(REVIEW, exist_ok=True)

PET = "EclipseDreadwing"
N = PET + "_"
TAU = 2 * math.pi
X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))
Z = Vector((0, 0, 1))


def V(*a):
    return Vector(a)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def mirror(v, side):
    return Vector((v.x * side, v.y, v.z))


# ---------- the frame of it (metres; ground at z = 0; it faces -Y) ----------
# A four-legged raven-drake: a horizontal, low-slung body with a deep chest and broad shoulders, the neck rising out of a heavy ruff in an S
# up to the head, which sits above the chest; heavy armoured forelegs under the chest, drake hind legs under the hips, a long feathered tail
# trailing back almost to the ground, and the wings raised high over the back in a V.
PIVOT = {
    "Body": V(0, 0.0, 0.80),
    "Head": V(0, -0.372, 1.262),     # the joint at the top of the neck, where the skull sits on it
    "WingL": V(0.190, 0.010, 0.990),  # the shoulder, on top of the shoulder mass
    "WingR": V(-0.190, 0.010, 0.990),
    "Tail": V(0, 0.520, 0.790),      # the root of the tail, inside the rump
}
HEAD_O = V(0, -0.425, 1.330)          # the middle of the cranium
HEAD_PITCH = 9.0                      # the head leans forward and down a little: a predator's carriage

# body spine, from the tail root up to the head; (centre, half-width, dorsal, ventral, squareness)
SPINE = [
    (V(0, 0.560, 0.800), 0.085, 0.075, 0.075, 2.3),
    (V(0, 0.450, 0.800), 0.170, 0.150, 0.150, 2.4),
    (V(0, 0.300, 0.790), 0.240, 0.190, 0.195, 2.5),
    (V(0, 0.130, 0.795), 0.262, 0.200, 0.215, 2.5),
    (V(0, -0.040, 0.825), 0.292, 0.212, 0.250, 2.5),
    (V(0, -0.180, 0.875), 0.310, 0.212, 0.288, 2.4),
    (V(0, -0.290, 0.960), 0.255, 0.178, 0.270, 2.3),
    (V(0, -0.345, 1.065), 0.180, 0.135, 0.170, 2.2),
    (V(0, -0.360, 1.150), 0.135, 0.108, 0.118, 2.1),
    (V(0, -0.360, 1.220), 0.102, 0.086, 0.090, 2.1),
    (V(0, -0.372, 1.285), 0.076, 0.062, 0.068, 2.1),
]

# the left legs (+X): (joint chain, radii along it); the right ones mirror them, with a walking stagger
LEGS = {
    # forelegs: the elbow folded back under the chest, the forearm reaching down and forward to a bent wrist, the foot reaching forward
    "fore": {"top": V(0.170, -0.190, 0.820), "mid": V(0.250, -0.060, 0.570), "low": V(0.240, -0.215, 0.300), "foot": V(0.228, -0.330, 0.068)},
    # hind legs, digitigrade: a muscular thigh down and forward to the knee, the shin back to a high backward-bent hock, the foot forward
    "hind": {"top": V(0.190, 0.300, 0.770), "mid": V(0.255, 0.120, 0.560), "low": V(0.248, 0.470, 0.300), "foot": V(0.234, 0.335, 0.068)},
}
STRIDE = {("fore", 1): -0.055, ("hind", 1): 0.045, ("fore", -1): 0.030, ("hind", -1): -0.030}

TAIL_PATH = [V(0, 0.470, 0.790), V(0, 0.680, 0.680), V(0, 0.920, 0.500), V(0, 1.160, 0.320), V(0, 1.390, 0.170), V(0, 1.580, 0.080)]
TAIL_R = [0.088, 0.066, 0.046, 0.030, 0.018, 0.010]
DROP = 0.0

# materials: separate identities in the .blend, baked into one colour map per game piece
MATS = ["BodyFeather", "UnderArmor", "HeadBeak", "WingFeather", "Horn", "Talon", "TailFeather", "Eye", "Accent", "LegScale"]
M = {name: i for i, name in enumerate(MATS)}


# ---------- a mesh under construction ----------
class Geo:
    """A bmesh with the per-vertex values the materials read: fu (0 at a feather's root, 1 at its tip, or along a part), fv (-1..1 across
    it), seed (per feather), tint (crimson), violet, shade (0 dark .. 1 pale)."""
    ATTRS = ("fu", "fv", "seed", "tint", "violet", "shade", "under")

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.L = {a: self.bm.verts.layers.float.new(a) for a in self.ATTRS}
        self.cur = {"fv": 0.5}
        self.count = 0

    def vert(self, co, **a):
        v = self.bm.verts.new(co)
        for k, x in self.cur.items():
            v[self.L[k]] = x
        for k, x in a.items():
            v[self.L[k]] = x
        return v

    def face(self, vs, mat):
        f = self.bm.faces.new(vs)
        f.material_index = mat
        return f

    def separate(self, passes=16):
        """Where two feathers overlap in one plane (within a millimetre, facing the same way) the engine would flicker between them: turn the
        smaller of the two a few degrees about the spot until no such pair is left."""
        bm = self.bm
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        island, size = {}, collections.Counter()
        k = 0
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
        for i in island.values():
            size[i] += 1
        members = collections.defaultdict(list)
        for v in bm.verts:
            members[island[v.index]].append(v)
        moved_total = 0
        for _ in range(passes):
            tb = bm.copy()                       # judged as the engine draws it: in triangles (a triangulation adds no vertices)
            bmesh.ops.triangulate(tb, faces=tb.faces[:])
            tb.faces.ensure_lookup_table()
            tb.normal_update()
            tree = BVHTree.FromBMesh(tb)
            moves = {}
            for f in tb.faces:
                n = f.normal
                cen = f.calc_center_median()
                for q in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                    for _, _, j, _ in tree.find_nearest_range(q, 0.0013):
                        if j is None or j == f.index:
                            continue
                        g = tb.faces[j]
                        if abs(n.dot(g.normal)) < 0.998:
                            continue
                        a, b = island[f.verts[0].index], island[g.verts[0].index]
                        if a == b:
                            continue
                        mine = a if (size[a], a) <= (size[b], b) else b
                        if mine not in moves:
                            moves[mine] = (q.copy(), n.orthogonal().normalized())
            tb.free()
            if not moves:
                break
            fu = bm.verts.layers.float.get("fu")
            for i, (pivot, axis) in moves.items():
                roots = [v.co for v in members[i] if v[fu] < 1e-4]
                if roots and len(roots) < len(members[i]):
                    pivot = sum(roots, Vector()) / len(roots)      # a feather turns about its own root, which stays sunk in what carries it
                turn = Matrix.Rotation(math.radians(4.0), 3, axis)
                for v in members[i]:
                    v.co = pivot + turn @ (v.co - pivot)
            moved_total += len(moves)
            if os.environ.get("DW_DEBUG"):
                print("SEPARATE", self.name, len(moves), flush=True)
        return moved_total

    def finish(self, coll, flat=True):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")   # as the engine will draw it
        self.separate()
        for v in self.bm.verts:                  # talon points rest on the ground, never through it
            if v.co.z < 0.0:
                v.co.z = 0.0
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        idx = [0] * len(me.polygons)
        me.polygons.foreach_get("material_index", idx)
        # hard facets everywhere; only the eyes are smooth, so their gloss is a small round glint and not a whole facet lit up
        me.polygons.foreach_set("use_smooth", [(not flat) or i == M["Eye"] for i in idx])
        o = bpy.data.objects.new(self.name, me)
        coll.objects.link(o)
        return o


def loft(g, rings, mat, cap0=True, cap1=True, ring_attrs=None):
    """Bridges rings of equal count; a cap is True (a fan to the ring's middle), a Vector (a fan to that point: a tip) or False."""
    R = []
    for i, ring in enumerate(rings):
        a = ring_attrs(i) if ring_attrs else {}
        R.append([g.vert(p, **a) for p in ring])
    m = len(rings[0])
    for i in range(len(R) - 1):
        for k in range(m):
            k2 = (k + 1) % m
            g.face((R[i][k], R[i][k2], R[i + 1][k2], R[i + 1][k]), mat)
    for cap, ring, first in ((cap0, R[0], True), (cap1, R[-1], False)):
        if cap is False:
            continue
        c = (sum((v.co for v in ring), Vector()) / m) if cap is True else cap
        a = ring_attrs(0 if first else len(rings) - 1) if ring_attrs else {}
        cv = g.vert(c, **a)
        for k in range(m):
            g.face((ring[k], ring[(k + 1) % m], cv), mat)
    return R


def frame_ring(c, A, B, pts):
    return [c + A * x + B * y for x, y in pts]


def super_ring(w, hd, hv, n=16, p=2.4, keel=0.0, flat_top=0.0):
    """A section: half-width w, dorsal hd, ventral hv; p > 2 squares it off; keel sharpens the underside to a ridge. Starts at the top."""
    out = []
    for k in range(n):
        a = TAU * k / n
        s, c = math.sin(a), math.cos(a)
        x = w * math.copysign(abs(s) ** (2 / p), s)
        y = (hd if c > 0 else hv) * math.copysign(abs(c) ** (2 / p), c)
        if c < 0:
            y -= keel * abs(c) ** 6 * hv
        if c > 0:
            y -= flat_top * c ** 4 * hd
        out.append((x, y))
    return out


def path_frames(pts, side=X):
    """Per point: tangent, and a frame (A across, B 'up' = tangent x A)."""
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        a = side - t * t.dot(side)
        a = a.normalized() if a.length > 1e-6 else t.orthogonal().normalized()
        b = t.cross(a).normalized()
        out.append((t, a, b))
    return out


def catmull(pts, per=6):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-2].copy())
    return out


# ---------- the feather: a hard faceted blade ----------
FEATHER_SHAPES = {
    # (width at t) knots: a broad root, the widest part early, a long straight taper, a sharp point
    "flight": ((0.0, 0.42), (0.18, 0.92), (0.42, 1.0), (0.70, 0.78), (0.88, 0.42), (1.0, 0.0)),
    "covert": ((0.0, 0.55), (0.30, 1.0), (0.62, 0.86), (0.84, 0.48), (1.0, 0.0)),
    "contour": ((0.0, 0.60), (0.35, 1.0), (0.70, 0.70), (1.0, 0.0)),
    "plate": ((0.0, 0.80), (0.40, 1.0), (0.75, 0.80), (1.0, 0.0)),
    "spike": ((0.0, 1.0), (0.35, 0.80), (0.75, 0.40), (1.0, 0.0)),
    # crystalline shards: the same blade with chips knocked out of its edges, two steps down its length, like knapped obsidian
    "shard": ((0.0, 0.40), (0.14, 0.92), (0.32, 1.0), (0.46, 0.94), (0.48, 0.78), (0.66, 0.70), (0.68, 0.54), (0.84, 0.38), (1.0, 0.0)),
    "shardc": ((0.0, 0.55), (0.28, 1.0), (0.48, 0.90), (0.50, 0.72), (0.76, 0.50), (1.0, 0.0)),
    # a chevron plate of the breast: broad at the root, straight sides to a point
    "chev": ((0.0, 1.0), (0.45, 0.96), (1.0, 0.0)),
}


def width_at(shape, t):
    ks = FEATHER_SHAPES[shape]
    for (t0, w0), (t1, w1) in zip(ks, ks[1:]):
        if t <= t1:
            return w0 + (w1 - w0) * (t - t0) / (t1 - t0)
    return 0.0


def blade(g, root, d, n, length, width, mat, shape="covert", thick=0.16, under=0.07, lead=0.42, bend=0.0, droop=0.0, twist=0.0,
          segs=None, seed=0.0, tint=0.0, violet=0.0, shade=0.0, notch=False):
    """One feather blade from its root along d, upper side toward n. Its cross-section is a shallow diamond (a ridge along the shaft, the
    two vanes falling away from it to sharp edges), so it reads as hard and faceted. bend: sideways curve (toward +side) as a share of length;
    droop: curve toward -n (onto what it lies on); twist: degrees about its shaft by the tip; lead: the leading vane's share of the width."""
    d = d.normalized()
    s = d.cross(n).normalized()            # the side
    n = s.cross(d).normalized()
    # every blade in a mesh is stacked a little apart from the last and turned a few degrees from it, so neighbours that overlap never
    # share a plane (they would flicker against each other in the engine)
    g.count += 1
    root = root + n * (0.0012 * (g.count % 5))
    roll = 0.9 * ((g.count * 4) % 11 - 5)
    ks = [k[0] for k in FEATHER_SHAPES[shape]]
    ts = sorted(set(ks + ([0.55] if shape == "flight" else [])))
    if segs:
        ts = [i / segs for i in range(segs + 1)]
    rings = []
    for t in ts[:-1]:
        c = root + d * (length * t) + s * (bend * length * t * t) - n * (droop * length * t * t)
        tw = math.radians(twist * t + roll)
        ss = s * math.cos(tw) + n * math.sin(tw)
        nn = n * math.cos(tw) - s * math.sin(tw)
        w = width * width_at(shape, t)
        wl, wt = w * lead, w * (1 - lead)
        if notch and 0.5 < t < 0.9:
            wt *= 0.86
        ridge = (wt - wl) * 0.18                  # the shaft sits a little toward the leading edge
        rings.append(([c - ss * wl, c + nn * (thick * w) + ss * ridge * -1, c + ss * wt, c - nn * (under * w) + ss * ridge * -1], t))
    tip = root + d * length + s * (bend * length) - n * (droop * length)
    vs = []
    for ring, t in rings:
        vs.append([g.vert(p, fu=t, fv=fv, seed=seed, tint=tint, violet=violet, shade=shade, under=u)
                   for p, fv, u in zip(ring, (-1.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))])
    tv = g.vert(tip, fu=1.0, fv=0.0, seed=seed, tint=tint, violet=violet, shade=shade)
    for i in range(len(vs) - 1):
        for k in range(4):
            k2 = (k + 1) % 4
            g.face((vs[i][k], vs[i][k2], vs[i + 1][k2], vs[i + 1][k]), mat)
    for k in range(4):
        g.face((vs[-1][k], vs[-1][(k + 1) % 4], tv), mat)
    g.face(list(reversed(vs[0])), mat)
    return tip


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
    return total


# ---------- the head (local axes: s across, f forward, u up; scaled and leaned into place) ----------
HEAD_SCALE = 1.12


def head_axes():
    p = math.radians(HEAD_PITCH)
    return V(0, -math.cos(p), -math.sin(p)), V(0, -math.sin(p), math.cos(p))


def H(s, f, u):
    F, U = head_axes()
    k = HEAD_SCALE
    return HEAD_O + X * (s * k) + F * (f * k) + U * (u * k)


# the skull, back to front: (f, half section from the crown down one side to the throat: (s, u)). A pronounced forehead, brow ridges
# standing out over sunken eye sockets, cheekbones under them, a heavy rear skull, tapering to the beak.
SKULL = [
    (-0.138, [(0, .030), (.018, .028), (.026, .022), (.030, .012), (.032, .002), (.032, -.008), (.030, -.018), (.024, -.026), (.014, -.032), (0, -.034)]),
    (-0.118, [(0, .066), (.032, .062), (.050, .050), (.058, .034), (.060, .016), (.060, -.002), (.058, -.020), (.050, -.036), (.030, -.048), (0, -.052)]),
    (-0.080, [(0, .100), (.046, .095), (.072, .078), (.084, .054), (.087, .030), (.086, .006), (.081, -.018), (.068, -.042), (.042, -.058), (0, -.064)]),
    (-0.035, [(0, .122), (.054, .116), (.086, .095), (.096, .068), (.096, .040), (.094, .012), (.088, -.014), (.072, -.040), (.045, -.058), (0, -.064)]),
    (0.005, [(0, .128), (.056, .122), (.090, .100), (.096, .074), (.088, .050), (.086, .026), (.090, .006), (.072, -.030), (.046, -.050), (0, -.058)]),
    (0.040, [(0, .125), (.053, .119), (.086, .098), (.090, .076), (.074, .058), (.072, .032), (.086, .010), (.066, -.026), (.042, -.046), (0, -.054)]),
    (0.075, [(0, .116), (.046, .110), (.076, .090), (.080, .070), (.072, .054), (.070, .032), (.074, .012), (.058, -.020), (.036, -.040), (0, -.048)]),
    (0.105, [(0, .100), (.038, .096), (.058, .080), (.064, .064), (.063, .048), (.062, .030), (.060, .014), (.050, -.012), (.032, -.030), (0, -.036)]),
    (0.130, [(0, .086), (.030, .082), (.044, .070), (.048, .056), (.046, .042), (.046, .026), (.048, .010), (.042, -.012), (.028, -.026), (0, -.030)]),
]
# the brow ridge: a bony bar from the horn's root forward over the eye down to the beak's root, its hard edge overhanging the eye (the scowl
# drops toward the beak); the cheekbone under the eye closes the opening into a narrow almond. (s, f, u, size)
BROW = [(0.072, -0.040, 0.104, 0.75), (0.090, -0.004, 0.096, 1.25), (0.097, 0.034, 0.084, 1.45), (0.090, 0.070, 0.070, 1.30),
        (0.066, 0.104, 0.058, 0.70), (0.050, 0.126, 0.056, 0.40)]
CHEEK = [(0.074, -0.050, 0.030, 0.55), (0.090, -0.012, 0.018, 0.95), (0.092, 0.030, 0.012, 1.0), (0.082, 0.068, 0.016, 0.85),
         (0.062, 0.100, 0.020, 0.55)]
EYE_LOCAL = (0.060, 0.040, 0.044)      # s, f, u of the eyeball's centre: sunk between the brow ridge and the cheekbone
EYE_R = 0.024
EYE_AXIS_LOCAL = (0.70, 0.70, 0.02)   # out, forward, up: a predator's forward-set eye
# the beak: the upper's ridge (f, u), its depth below the ridge and half-width; the lower's top edge, depth and half-width
BEAK_UP = [(0.100, .090, .088, .057), (0.140, .084, .080, .052), (0.178, .068, .067, .043), (0.208, .044, .054, .031),
           (0.228, .012, .040, .021), (0.236, -.024, .024, .012), (0.228, -.056, 0.0, 0.0)]
BEAK_LO = [(0.098, .010, .056, .045), (0.140, .004, .048, .038), (0.176, -.006, .037, .029), (0.203, -.018, .025, .019),
           (0.218, -.030, 0.0, 0.0)]
# the crown horns: path (s, f, u) from inside the skull, and radius; the right one bends a little differently
HORN = [((0.062, 0.020, 0.092), .034), ((0.092, -0.045, 0.118), .031), ((0.122, -0.120, 0.140), .026), ((0.150, -0.200, 0.165), .019),
        ((0.170, -0.270, 0.196), .012), ((0.182, -0.318, 0.228), .006), ((0.186, -0.336, 0.250), 0.0)]
HORN_R_BEND = (0.92, 1.04, 0.97)       # the right horn: a touch narrower and longer, its tip lower


def skull_rings(blockout=False):
    rings = []
    for f, half in SKULL:
        if blockout:
            half = [half[0], half[2], half[3], half[6], half[7], half[9]]
        full = half + [(-s, u) for s, u in reversed(half[1:-1])]
        rings.append([H(s, f, u) for s, u in full])
    return rings


def build_skull(g, blockout=False):
    rings = skull_rings(blockout)
    loft(g, rings, M["HeadBeak"], cap0=H(0, -0.146, -0.002), cap1=True, ring_attrs=lambda i: {"fu": i / (len(rings) - 1), "shade": 0.0})


def build_brow(g, side):
    """The brow ridge and the cheekbone round the eye: angular bars whose sharp edges frame a narrow, deep-set opening."""
    for spec, sec, mat in ((BROW, [(-0.55, 0.85), (0.35, 1.05), (1.25, -0.25), (0.45, -0.80), (-0.45, -0.55)], M["HeadBeak"]),
                           (CHEEK, [(-0.5, 0.55), (0.6, 0.85), (1.0, 0.0), (0.4, -0.85), (-0.5, -0.6)], M["HeadBeak"])):
        pts = [H(s_ * side, f, u) for s_, f, u, _ in spec]
        sizes = [k for *_, k in spec]
        path = catmull(pts, per=2)
        sz = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(sizes)), sizes)
        frames = path_frames(path, side=X * side)
        rings = []
        r0 = 0.020 * HEAD_SCALE
        for p, (t, A, B), k in zip(path, frames, sz):
            up = B if B.z > 0 else -B
            rings.append([p + A * (x * r0 * k) + up * (y * r0 * k * 0.8) for x, y in sec])
        if side < 0:
            rings = [list(reversed(r)) for r in rings]
        loft(g, rings, mat, cap0=True, cap1=True, ring_attrs=lambda i: {"fu": i / (len(rings) - 1), "shade": 0.6})


def beak_ring(c, A, B, d, w, upper):
    if upper:
        pts = [(0, 0.004), (0.62 * w, -0.22 * d), (w, -0.80 * d), (0.62 * w, -0.97 * d), (0, -0.90 * d)]
    else:
        pts = [(0, -0.12 * d), (0.86 * w, 0.0), (w, -0.45 * d), (0.55 * w, -0.88 * d), (0, -d)]
    full = pts + [(-x, y) for x, y in reversed(pts[1:-1])]
    return frame_ring(c, A, B, full)


def build_beak(g, which):
    spec = BEAK_UP if which == "upper" else BEAK_LO
    pts = [H(0, f, u) for f, u, _, _ in spec]
    frames = path_frames(pts)
    k = HEAD_SCALE
    rings = []
    for (f, u, d, w), p, (t, A, B) in zip(spec[:-1], pts[:-1], frames[:-1]):
        rings.append(beak_ring(p, A, B, d * k, w * k, which == "upper"))
    loft(g, rings, M["HeadBeak"], cap0=True, cap1=pts[-1], ring_attrs=lambda i: {"fu": i / max(1, len(rings) - 1), "shade": 1.0, "tint": 0.0})


def eye_frame(side):
    F, U = head_axes()
    s, f, u = EYE_LOCAL
    c = H(s * side, f, u)
    a = EYE_AXIS_LOCAL
    axis = (X * (a[0] * side) + F * a[1] + U * a[2]).normalized()
    return c, axis


def build_eye(g, side, seg=14, rings=9):
    c, axis = eye_frame(side)
    r = EYE_R * HEAD_SCALE
    up = (Z - axis * axis.dot(Z)).normalized()
    across = up.cross(axis).normalized()
    pole = c + axis * r
    prev = None
    rows = []
    for i in range(1, rings):
        el = math.pi * i / rings                     # from the front pole round toward the back
        if el > math.radians(118):                  # what is buried in the socket is not built
            break
        rr = []
        for k in range(seg):
            az = TAU * k / seg
            d = axis * math.cos(el) + (up * math.cos(az) + across * math.sin(az)) * math.sin(el)
            p = c + d * r
            rr.append(g.vert(p, fu=d.dot(axis), fv=d.dot(up), shade=d.dot(across) * side, seed=0.0))
        rows.append(rr)
    pv = g.vert(pole, fu=1.0, fv=0.0, shade=0.0)
    for k in range(seg):
        g.face((pv, rows[0][k], rows[0][(k + 1) % seg]), M["Eye"])
    for i in range(len(rows) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            g.face((rows[i][k], rows[i + 1][k], rows[i + 1][k2], rows[i][k2]), M["Eye"])
    back = c - axis * r * 0.2
    bv = g.vert(back, fu=-1.0)
    for k in range(seg):
        g.face((rows[-1][k], bv, rows[-1][(k + 1) % seg]), M["Eye"])


def build_eye_glow(g, pupils, side, seg=12):
    """The pale glowing iris: a thin lens standing just off the front of the eyeball (a Neon piece in the game, so the eye reads from
    across a field), with a dark slit pupil just in front of it, on the head itself."""
    c, axis = eye_frame(side)
    r = EYE_R * HEAD_SCALE
    up = (Z - axis * axis.dot(Z)).normalized()
    across = up.cross(axis).normalized()
    ri, t0, t1 = r * 0.64, r + 0.0013, r + 0.0025
    back = [g.vert(c + axis * t0 + (up * math.cos(TAU * k / seg) + across * math.sin(TAU * k / seg)) * ri) for k in range(seg)]
    front = [g.vert(c + axis * t1 + (up * math.cos(TAU * k / seg) + across * math.sin(TAU * k / seg)) * ri) for k in range(seg)]
    cb, cf = g.vert(c + axis * t0), g.vert(c + axis * t1)
    for k in range(seg):
        k2 = (k + 1) % seg
        g.face((cf, front[k], front[k2]), 0)
        g.face((cb, back[k2], back[k]), 0)
        g.face((back[k], back[k2], front[k2], front[k]), 0)
    # the slit: two dark points, up and down, from the middle of the lens
    mid = c + axis * (t1 + 0.0014)
    for d in (up, -up):
        blade(pupils, mid - d * 0.001, d, axis, ri * 0.92, r * 0.22, M["HeadBeak"], shape="spike", thick=0.08, under=0.08, seed=0.0, shade=0.0)


def horn_points(side):
    out = []
    for (s, f, u), r in HORN:
        if side < 0:
            s, f, u = s * HORN_R_BEND[0], f * HORN_R_BEND[1], u * HORN_R_BEND[2]
        out.append((H(s * side, f, u), r * HEAD_SCALE))
    return out


def build_horn(g, side, blockout=False):
    pts = horn_points(side)
    path = catmull([p for p, _ in pts], per=1 if blockout else 2)
    radii = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(pts)), [r for _, r in pts])
    frames = path_frames(path, side=Z)
    sec = [(0, 0.80), (0.55, 0.50), (1.0, -0.05), (0.62, -0.58), (0, -0.70), (-0.62, -0.58), (-1.0, -0.05), (-0.55, 0.50)]
    rings = []
    for i, (p, (t, A, B), r) in enumerate(zip(path[:-1], frames[:-1], radii[:-1])):
        ridge = 1.0 + (0.08 if i % 2 else -0.03)        # growth ridges, felt as facets along it
        rings.append(frame_ring(p, B * side, A, [(x * r * ridge, y * r * ridge) for x, y in sec]))
    loft(g, rings, M["Horn"], cap0=True, cap1=path[-1], ring_attrs=lambda i: {"fu": i / (len(rings) - 1), "seed": side})


# ---------- the body ----------
def body_rings(n=16):
    pts = [c for c, *_ in SPINE]
    frames = path_frames(pts)
    rings = []
    for (c, w, hd, hv, p), (t, A, B) in zip(SPINE, frames):
        keel = 0.10 if c.y < -0.05 and c.z < 1.0 else 0.0
        rings.append(frame_ring(c, A, B, super_ring(w, hd, hv, n=n, p=p, keel=keel)))
    return rings, frames


def build_body(g, n=16):
    rings, _ = body_rings(n)
    loft(g, rings, M["BodyFeather"], cap0=True, cap1=True, ring_attrs=lambda i: {"fu": i / (len(rings) - 1)})


def leg_points(kind, side):
    L, off = LEGS[kind], STRIDE[(kind, side)]
    top = mirror(L["top"], side)
    mid = mirror(L["mid"], side) + V(0, off * 0.5, 0)
    low = mirror(L["low"], side) + V(0, off, 0)
    foot = mirror(L["foot"], side) + V(0, off, 0)
    return top, mid, low, foot


def tube(g, path, radii, mat, n=8, flat=1.0, side=X, cap0=True, cap1=True, sec=None, attrs=None):
    frames = path_frames(path, side=side)
    rings = []
    for p, (t, A, B), r in zip(path, frames, radii):
        if sec:
            pts = [(x * r, y * r) for x, y in sec]
        else:
            pts = [(math.sin(TAU * k / n) * r * flat, math.cos(TAU * k / n) * r) for k in range(n)]
        rings.append(frame_ring(p, A, B, pts))
    return loft(g, rings, mat, cap0=cap0, cap1=cap1, ring_attrs=attrs)


LIMB = {   # radii along the upper limb, the middle limb and the lowest (scaled) segment
    "fore": ([0.110, 0.138, 0.124, 0.088], [0.084, 0.074, 0.056, 0.046], [0.044, 0.047, 0.037, 0.044]),
    "hind": ([0.120, 0.158, 0.158, 0.128, 0.086], [0.084, 0.076, 0.056, 0.044], [0.042, 0.045, 0.035, 0.042]),
}


def build_leg(g, kind, side, blockout=False):
    """A leg: a heavy feathered upper limb sunk into the body, an armoured middle limb, a scaled lowest limb with a crimson-violet scale band
    at the joint above the foot, and a four-toed taloned foot."""
    top, mid, low, foot = leg_points(kind, side)
    n = 6 if blockout else 10
    up_r, mid_r, low_r = LIMB[kind]
    inside = top + V(-0.08 * side, 0.0, 0.04)
    upper = [inside, top, lerp(top, mid, 0.45), lerp(top, mid, 0.8), mid][-len(up_r):]
    tube(g, upper, up_r, M["BodyFeather"], n=n, flat=0.86, attrs=lambda i: {"fu": i / 4})
    middle = [lerp(top, mid, 0.8), mid, lerp(mid, low, 0.45), low]
    tube(g, middle, mid_r, M["LegScale"], n=n - 2, flat=0.88, attrs=lambda i: {"fu": i / 3})
    lowest = [lerp(mid, low, 0.85), low, lerp(low, foot, 0.5), foot + V(0, 0, 0.012)]
    tube(g, lowest, low_r, M["LegScale"], n=n - 2, flat=0.84, attrs=lambda i: {"fu": i / 3})
    if not blockout:
        axis = (foot - low).normalized()
        r = low_r[1] * 1.05
        band = [low - axis * 0.002, low + axis * 0.008, low + axis * 0.017]
        tube(g, band, [r * 0.94, r, r * 0.90], M["Accent"], n=7, flat=0.86, attrs=lambda i: {"fu": 0.6 + 0.2 * i, "fv": 0.75 - 0.3 * i})
    build_foot(g, side, foot, blockout)


TOES = [  # (degrees off forward, toward the body's middle is +; length; thickness) — three forward, one big rear talon
    (0.0, 0.165, 0.034), (30.0, 0.138, 0.031), (-30.0, 0.138, 0.031), (180.0 - 14.0, 0.098, 0.036)]


def build_foot(g, side, foot, blockout=False):
    for k, (ang, length, r) in enumerate(TOES):
        a = math.radians(ang) * side
        d = V(math.sin(a) * -1, -math.cos(a), 0).normalized()        # forward is -Y; +ang turns toward the middle (-X on the left)
        start = foot + V(0, 0, -0.006)
        pts = [start - d * 0.012, start + d * 0.02 + V(0, 0, -0.010), start + d * (length * 0.45) + V(0, 0, -0.020),
               start + d * (length * 0.75) + V(0, 0, -0.022), start + d * length + V(0, 0, -0.024)]
        radii = [r * 1.2, r * 1.05, r * 1.08, r * 0.86, r * 0.80]          # knuckles stand out
        sec = [(0, 0.9), (0.95, 0.15), (0.55, -0.80), (-0.55, -0.80), (-0.95, 0.15)]
        side_ref = d.cross(Z).normalized()
        tube(g, pts, radii, M["LegScale"], side=side_ref, sec=None if blockout else sec, n=5, cap0=True, cap1=True,
             attrs=lambda i: {"fu": i / 4})
        build_claw(g, pts[-1] - d * 0.012, d, r * (1.35 if k == 3 else 1.15), blockout)


def build_claw(g, base, d, r, blockout=False):
    """A hooked talon: thick at the toe, curving down to a needle point, a sharp ridge along its back."""
    L = r * 3.4
    drop = min(L * 0.60, base.z - 0.002)        # the point just touches the ground
    pts = [base, base + d * (L * 0.38) + Z * (L * 0.12), base + d * (L * 0.74) + Z * (L * 0.04), base + d * (L * 0.93) - Z * (drop * 0.5),
           base + d * (L * 0.88) - Z * drop]
    radii = [r * 0.92, r * 0.78, r * 0.55, r * 0.30, 0.0]
    side_ref = d.cross(Z).normalized()
    sec = [(0, 1.15), (0.78, 0.25), (0.55, -0.75), (-0.55, -0.75), (-0.78, 0.25)]
    frames = path_frames(pts, side=side_ref)
    rings = [frame_ring(p, A, B, [(x * rr, y * rr) for x, y in sec]) for p, (t, A, B), rr in zip(pts[:-1], frames[:-1], radii[:-1])]
    loft(g, rings, M["Talon"], cap0=True, cap1=pts[-1], ring_attrs=lambda i: {"fu": i / 3})


# ---------- the tail ----------
def build_tail_base(g, n=10):
    full = catmull(TAIL_PATH, per=2)
    radii = np.interp(np.linspace(0, 1, len(full)), np.linspace(0, 1, len(TAIL_R)), TAIL_R)
    path, radii = full[:9], radii[:9]           # it ends inside the root of the closing shards, which carry it to its point
    tube(g, path, radii, M["TailFeather"], n=8, flat=1.0, cap0=True, cap1=path[-1] + (path[-1] - path[-2]).normalized() * 0.03,
         attrs=lambda i: {"fu": i / (len(path) - 1)})


# ---------- the wings ----------
# The left wing's skeleton in each pose: shoulder, elbow, wrist, hand tip; at each joint the chord (the way its flight feathers trail) and,
# for the folded pose, the upper side. Extended: the arm rises out to a high wrist, the hand reaches on out, the feathers rake back and down.
# Folded: the humerus runs back along the body, the forearm forward again to the wrist at the shoulder, the hand back along the flank.
WING_POSES = {
    # the rest pose the game flaps from: raised high over the back and swept back, a V framing the head from the front. The arm climbs from
    # the shoulder to a high wrist, the hand reaches back, and the feathers hang back and down behind and above the body like a sail.
    "raised": {
        "J": [V(0.190, 0.010, 0.990), V(0.330, 0.130, 1.300), V(0.540, 0.120, 1.640), V(0.700, 0.520, 1.660)],
        "C": [V(0.05, 0.75, -0.66), V(0.12, 0.74, -0.66), V(0.30, 0.52, -0.80), V(0.42, 0.50, -0.76)],
        "N": None, "fan": 1.0,
    },
    # fully extended, as in flight: only used to measure the wingspan
    "extended": {
        "J": [V(0.190, 0.010, 0.990), V(0.430, 0.110, 1.120), V(0.730, 0.040, 1.320), V(1.030, 0.140, 1.440)],
        "C": [V(0.0, 0.70, -0.71), V(0.05, 0.71, -0.70), V(0.24, 0.64, -0.73), V(0.62, 0.40, -0.67)],
        "N": None, "fan": 1.0,
    },
    "folded": {
        "J": [V(0.190, 0.010, 0.990), V(0.300, 0.300, 0.930), V(0.320, -0.060, 0.990), V(0.345, 0.340, 0.950)],
        "C": [V(0.10, 0.62, -0.78), V(0.10, 0.80, -0.59), V(0.10, 0.86, -0.50), V(0.06, 0.95, -0.30)],
        "N": V(1.0, -0.05, 0.35), "fan": 0.12,
    },
}
REST_POSE = "raised"
REST_LOWER = 11.0      # degrees the raised pose is lowered about the shoulder, so a full upward wingbeat in the game keeps the wings apart


def nlerp(a, b, t):
    return (a * (1 - t) + b * t).normalized()


class WingFrame:
    def __init__(self, pose, side):
        spec = WING_POSES[pose]
        self.side = side
        J, C = list(spec["J"]), list(spec["C"])
        if pose == "raised":
            turn = Matrix.Rotation(math.radians(REST_LOWER), 3, Y)      # about the forward axis through the shoulder: the left wing comes down
            J = [J[0] + turn @ (j - J[0]) for j in J]
            C = [turn @ c for c in C]
        self.J = [mirror(j, side) - Z * DROP for j in J]
        self.C = [mirror(c, side).normalized() for c in C]
        self.fan = spec["fan"]
        self.Nfix = mirror(spec["N"], side).normalized() if spec["N"] else None

    def at(self, seg, a):
        """Position, chord, span (along the bone, outward), upper side, at a along bone seg (0 humerus, 1 forearm, 2 hand)."""
        p = lerp(self.J[seg], self.J[seg + 1], a)
        c = nlerp(self.C[seg], self.C[seg + 1], a)
        span = (self.J[seg + 1] - self.J[seg]).normalized()
        if self.Nfix:
            n = self.Nfix
        else:
            n = span.cross(c) * self.side
            n = n.normalized()
        n = (n - c * c.dot(n)).normalized()
        return p, c, span, n

    def direction(self, seg, a, theta):
        p, c, span, n = self.at(seg, a)
        th = math.radians(theta * self.fan)
        out = span - c * c.dot(span)
        out = out.normalized() if out.length > 1e-6 else n.cross(c).normalized()
        return (c * math.cos(th) + out * math.sin(th)).normalized()


def rng_for(*key):
    """A repeatable random stream per feather (Python's own hash of a string changes from run to run)."""
    return random.Random(zlib.crc32(repr(key).encode()))


def wing_feathers(side):
    """The feather list: (layer, seg, a, theta, length, width, shape, lift, shift, tint, violet, shade). lift: off the bone along the upper
    side (positive = above, a later layer lies over an earlier); shift: toward the leading edge. Few, big, chipped shards in clear tiers:
    coverts over secondaries over primaries, each blade overlapping the next."""
    F = []
    P_LEN = [0.60, 0.66, 0.72, 0.78, 0.82, 0.82, 0.76]
    for i in range(7):
        f = i / 6
        F.append(("primary", 2, 0.06 + 0.94 * f ** 0.9, 2 + 22 * f ** 1.2, P_LEN[i], 0.200 - 0.030 * f, "shard", -0.014 + 0.0065 * i, 0.0,
                  0.85 + 0.15 * f, 0.0, 0.30))
    for j in range(8):
        f = j / 7
        F.append(("secondary", 1, 0.02 + 0.97 * f, -4 + 8 * f, 0.58 + 0.04 * math.sin(j * 2.1) + 0.02 * f, 0.200, "shard",
                  -0.014 + 0.0060 * (7 - j), 0.0, 0.0, 0.0, 0.40))
    for j in range(2):
        F.append(("tertial", 0, 0.70 + 0.26 * j, -20 + 8 * j, 0.48 + 0.03 * j, 0.190, "shard", -0.002 + 0.006 * (1 - j), 0.0, 0.0, 0.0, 0.25))
    for i in range(5):
        f = i / 4
        F.append(("gcovert", 2, 0.05 + 0.82 * f, 4 + 20 * f, 0.34 + 0.03 * f, 0.180, "shardc", 0.024 + 0.006 * i, 0.014, 0.0, 0.0, 0.15))
    for j in range(7):
        f = j / 6
        F.append(("gcovert", 1, 0.03 + 0.94 * f, -3 + 8 * f, 0.33 + 0.02 * math.sin(j * 1.9), 0.180, "shardc", 0.026 + 0.0055 * (6 - j), 0.014,
                  0.0, 0.0, 0.10))
    for j in range(8):
        f = j / 7
        seg, a = (0, 0.30 + 0.70 * f / 0.30) if f < 0.30 else ((1, (f - 0.30) / 0.45) if f < 0.75 else (2, (f - 0.75) / 0.25 * 0.85))
        F.append(("mcovert", seg, min(a, 1.0), -10 + 26 * f, 0.23 + 0.02 * f, 0.160, "shardc", 0.050 + 0.003 * j, 0.050, 0.0, 0.0, 0.0))
    for row in range(2):
        for j in range(6):
            f = (j + 0.5 * row) / 6
            seg, a = (0, 0.18 + 0.82 * f / 0.4) if f < 0.4 else (1, (f - 0.4) / 0.6)
            F.append(("lcovert", seg, min(a, 1.0), -6 + 14 * f, 0.15 - 0.02 * row, 0.120, "contour", 0.064 + 0.008 * row, 0.075 - 0.028 * row,
                      0.0, 0.0, 0.0))
    for j in range(4):
        f = j / 3
        F.append(("marginal", 2, 0.05 + 0.80 * f, 20 + 22 * f, 0.15 - 0.03 * f, 0.100, "contour", 0.040, 0.045, 0.0, 0.0, 0.0))
    for row in range(2):
        for j in range(6):
            f = (j + 0.5 * row) / 6
            seg, a = (0, 0.30 + 0.70 * f / 0.35) if f < 0.35 else (1, (f - 0.35) / 0.65)
            F.append(("under", seg, min(a, 1.0), -4 + 10 * f, 0.27 - 0.07 * row, 0.15, "shardc", -0.040 - 0.008 * row, 0.024 + 0.03 * row,
                      0.0, 0.0, 0.0))
    return F


def build_wing(g, side, pose, blockout=False):
    wf = WingFrame(pose, side)
    J = wf.J
    if blockout:
        lead = [J[0], J[1], J[2], J[3]]
        trail = [J[0] + wf.C[0] * 0.38, J[1] + wf.C[1] * 0.44, J[2] + wf.C[2] * 0.55, J[3] + wf.C[3] * 0.62]
        rings = []
        for p, q in zip(lead, trail):
            n = (q - p).cross(Z).normalized() * 0.01
            rings.append([p + n, q + n, q - n, p - n])
        loft(g, rings, M["WingFeather"])
        return
    # the arm: a faceted bone-and-muscle limb, thick at the shoulder, knuckled at elbow and wrist
    path = catmull(J, per=3)
    radii = np.interp(np.linspace(0, 1, len(path)), [0, 0.33, 0.66, 1.0], [0.074, 0.050, 0.042, 0.016])
    sec = [(0, 1.0), (0.80, 0.55), (1.0, -0.25), (0.45, -0.85), (-0.45, -0.85), (-1.0, -0.25), (-0.80, 0.55)]
    frames = []
    for i, p in enumerate(path):
        seg = min(2, int(i / 3))
        a = (i - seg * 3) / 3
        _, c, span, n = wf.at(seg, min(a, 1.0))
        frames.append((c, n))
    rings = []
    for p, (c, n), r in zip(path, frames, radii):
        rings.append(frame_ring(p, -c, n, [(x * r * 1.25, y * r * 0.8) for x, y in sec]))   # wider along the chord than deep
    loft(g, rings, M["BodyFeather"], cap0=True, cap1=path[-1] + (path[-1] - path[-2]).normalized() * 0.05, ring_attrs=lambda i: {"fu": i / len(rings)})
    # the shoulder knuckle: a rounded faceted mass centred on the joint, buried in the body's shoulder so a flap turns it in place
    knuckle(g, J[0], 0.095, M["BodyFeather"])
    # the patagium: the leading-edge web from shoulder to wrist that the coverts lie on
    p0, c0, s0, n0 = wf.at(0, 0.0)
    p2, c2, s2, n2 = wf.at(1, 1.0)
    pe, ce, se, ne = wf.at(1, 0.0)
    web = [[p0 - c0 * 0.02 + n0 * 0.02, lerp(p0, p2, 0.5) - lerp(c0, c2, 0.5) * 0.03 + n0 * 0.012, p2 - c2 * 0.02 + n2 * 0.01],
           [pe + ne * 0.015, lerp(pe, p2, 0.4) + ne * 0.012, p2 + c2 * 0.02 + n2 * 0.01]]
    web_sheet(g, web, n0, 0.012, M["BodyFeather"])
    # the wrist claw: a hooked spur off the wrist's leading edge, the drake in it
    pw, cw, sw, nw = wf.at(2, 0.0)
    fwd = (-cw + nw * 0.6).normalized()
    claw_path = [pw - fwd * 0.01, pw + fwd * 0.045 + sw * 0.01, pw + fwd * 0.085 + nw * 0.015, pw + fwd * 0.105 + nw * 0.045 - cw * 0.0]
    tube(g, claw_path[:-1], [0.020, 0.016, 0.010], M["Talon"], side=sw, sec=[(0, 1.1), (0.75, 0.2), (0.5, -0.8), (-0.5, -0.8), (-0.75, 0.2)],
         cap0=True, cap1=claw_path[-1], attrs=lambda i: {"fu": i / 3})
    for spec in wing_feathers(side):
        layer, seg, a, theta, length, width, shape, lift, shift, tint, violet, shade = spec
        r = rng_for(side, layer, round(a, 3), seg)
        p, c, span, n = wf.at(seg, a)
        jitter = r.uniform(-1.5, 1.5)
        d = wf.direction(seg, a, theta + jitter)
        root = p + n * lift - c * shift
        if layer in ("primary", "secondary", "tertial", "under"):
            root = root - d * 0.04
        L = length * r.uniform(0.96, 1.04)
        if pose == "folded" and layer in ("primary",):
            L *= 1.0
        nn = n if layer != "under" else n
        blade(g, root, d, nn, L, width * r.uniform(0.95, 1.05), M["WingFeather"], shape=shape,
              thick=0.17 if layer in ("primary", "secondary", "tertial") else 0.21, under=0.07,
              bend=r.uniform(-0.03, 0.01) * (1 if layer != "under" else -1), droop=(0.05 if layer in ("primary", "secondary") else 0.03) * (1 if layer != "under" else -1),
              twist=r.uniform(-5, 5), seed=r.random(), tint=tint, violet=violet, shade=shade, notch=False)


def knuckle(g, c, r, mat, seg=8, rings=6):
    rows = []
    for i in range(1, rings):
        el = math.pi * i / rings
        rows.append([g.vert(c + V(math.cos(TAU * k / seg) * math.sin(el), math.sin(TAU * k / seg) * math.sin(el), math.cos(el)) * r, fu=0.0) for k in range(seg)])
    top, bot = g.vert(c + Z * r), g.vert(c - Z * r)
    for k in range(seg):
        k2 = (k + 1) % seg
        g.face((top, rows[0][k], rows[0][k2]), mat)
        g.face((bot, rows[-1][k2], rows[-1][k]), mat)
    for i in range(len(rows) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            g.face((rows[i][k], rows[i + 1][k], rows[i + 1][k2], rows[i][k2]), mat)


def web_sheet(g, grid, n, thick, mat):
    """A thick sheet over a grid of points (rows x cols), closed round its edge."""
    top = [[g.vert(p + n * thick) for p in row] for row in grid]
    bot = [[g.vert(p - n * thick) for p in row] for row in grid]
    R, C = len(grid), len(grid[0])
    for i in range(R - 1):
        for j in range(C - 1):
            g.face((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]), mat)
            g.face((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]), mat)
    ring_t = [top[0][j] for j in range(C)] + [top[i][C - 1] for i in range(1, R)] + [top[R - 1][j] for j in range(C - 2, -1, -1)] + [top[i][0] for i in range(R - 2, 0, -1)]
    ring_b = [bot[0][j] for j in range(C)] + [bot[i][C - 1] for i in range(1, R)] + [bot[R - 1][j] for j in range(C - 2, -1, -1)] + [bot[i][0] for i in range(R - 2, 0, -1)]
    for k in range(len(ring_t)):
        k2 = (k + 1) % len(ring_t)
        g.face((ring_t[k], ring_b[k], ring_b[k2], ring_t[k2]), mat)


# ---------- feathers over the body, the head and the tail ----------
def spine_eval(sf):
    """The body's section at a fractional index along SPINE: centre, tangent (toward the head), across, up, w, hd, hv, p."""
    n = len(SPINE)
    sf = min(max(sf, 0.0), n - 1.0001)
    i = int(sf)
    t = sf - i
    cs = [c for c, *_ in SPINE]
    c = lerp(cs[i], cs[i + 1], t)
    tan = (cs[min(i + 1, n - 1)] - cs[max(i, 0)]).normalized()
    prev = (cs[min(i + 1, n - 1)] - cs[max(i - 1, 0)]).normalized()
    nxt = (cs[min(i + 2, n - 1)] - cs[i]).normalized()
    tan = nlerp(prev, nxt, t)
    A = X
    B = tan.cross(A).normalized()
    w, hd, hv, p = [lerp(SPINE[i][k], SPINE[i + 1][k], t) for k in (1, 2, 3, 4)]
    return c, tan, A, B, w, hd, hv, p


def body_point(sf, phi):
    """A point on the body at sf along it, phi round it (0 = top of the back, pi = the belly), with its outward normal and the way toward the tail."""
    def at(sf_, phi_):
        c, tan, A, B, w, hd, hv, p = spine_eval(sf_)
        s, co = math.sin(phi_), math.cos(phi_)
        x = w * math.copysign(abs(s) ** (2 / p), s)
        y = (hd if co > 0 else hv) * math.copysign(abs(co) ** (2 / p), co)
        return c + A * x + B * y, tan
    p0, tan = at(sf, phi)
    pa, _ = at(sf + 0.05, phi)
    pb, _ = at(sf, phi + 0.05)
    nrm = (pa - p0).cross(pb - p0).normalized()
    c, *_ = spine_eval(sf)
    if nrm.dot(p0 - c) < 0:
        nrm = -nrm
    back = -(pa - p0).normalized()
    return p0, nrm, back


def lay(g, p, nrm, toward, length, width, mat, shape="contour", lift_deg=10.0, sink=0.012, **kw):
    """A feather lying on a surface at p, pointing along it toward `toward`, raised lift_deg off it, its root sunk."""
    d = (toward - nrm * nrm.dot(toward)).normalized()
    d = (d * math.cos(math.radians(lift_deg)) + nrm * math.sin(math.radians(lift_deg))).normalized()
    return blade(g, p - nrm * sink - d * length * 0.08, d, nrm, length, width, mat, shape=shape, **kw)


def body_feathers(g):
    r = random.Random(7)
    ns = len(SPINE) - 1
    # the neck: a heavy ruff of shards from the skull down to the shoulders, standing off the neck, pale down the throat, dark behind
    rows = [(ns - 0.40, 8, 0.17), (ns - 1.15, 9, 0.21), (ns - 1.90, 10, 0.25), (ns - 2.65, 10, 0.28)]
    for k, (sf, count, L) in enumerate(rows):
        for j in range(count):
            phi = TAU * (j + 0.5 * (k % 2)) / count
            ventral = math.cos(phi) < -0.80
            if ventral and sf < ns - 1.4:
                continue                          # the breast armour takes over below the throat
            p, nrm, back = body_point(sf, phi)
            lay(g, p, nrm, back, L * r.uniform(0.92, 1.08), L * 0.6, M["UnderArmor"] if ventral else M["BodyFeather"],
                shape="contour" if ventral else "shardc", lift_deg=20 if not ventral else 12, seed=r.random(), shade=1.0 if ventral else 0.0,
                twist=r.uniform(-6, 6), violet=0.0 if ventral else 0.25)
    # the breast: layered chevron plates pointing down, pale lavender-grey, the side plates set higher and angled in, so each row is a V
    for k, (sf, half, L, W) in enumerate([(7.35, 1, 0.13, 0.13), (6.80, 1, 0.14, 0.14), (6.25, 1, 0.14, 0.14), (5.70, 1, 0.13, 0.12)]):
        for j in range(-half, half + 1):
            phi = math.pi + j * 0.27
            p, nrm, back = body_point(sf + 0.25 * abs(j), phi)
            inward = (X * (-math.copysign(1, j) if j else 0.0)) * 0.35
            lay(g, p, nrm, (back + inward).normalized(), L, W, M["UnderArmor"], shape="chev", lift_deg=10, sink=0.012, seed=r.random(),
                shade=1.0 - 0.15 * abs(j), thick=0.14, under=0.08)
    # the chest's sides: dark indigo shards closing in round the pale band, so the front reads dark with a narrow chevron down its middle
    for k, sf in enumerate((6.85, 6.05)):
        for side in (1, -1):
            for j, dphi in enumerate((0.46, 0.80, 1.15)):
                phi = math.pi - side * (dphi + 0.12 * (k % 2))
                p, nrm, back = body_point(sf, phi)
                L = (0.22 + 0.02 * j) * r.uniform(0.92, 1.08)
                lay(g, p, nrm, back, L, L * 0.6, M["BodyFeather"], shape="shardc", lift_deg=14, seed=r.random(), shade=0.15, violet=0.3)
    # the scapular mantle: big shards over the shoulders and the roots of the wings
    for side in (1, -1):
        for k, (sf, phi, L) in enumerate([(4.55, 0.60, 0.28), (4.10, 0.95, 0.30), (4.00, 0.35, 0.30), (3.45, 0.75, 0.31), (3.35, 0.15, 0.27),
                                          (2.85, 0.50, 0.29)]):
            p, nrm, back = body_point(sf, phi * side)
            lay(g, p, nrm, back, L * r.uniform(0.95, 1.05), L * 0.55, M["BodyFeather"], shape="shardc", lift_deg=14, seed=r.random(), shade=0.1,
                violet=0.4)
    # the back, flanks and belly: shard contours from the shoulders to the rump
    for k, sf in enumerate([5.35, 4.30, 3.25, 2.20, 1.20]):
        count = 7
        for j in range(count):
            phi = TAU * (j + 0.5 * (k % 2)) / count
            if math.cos(phi) < -0.90 and sf > 5.5:
                continue                           # the breast band
            p, nrm, back = body_point(sf, phi)
            under = math.cos(phi) < -0.3
            L = (0.34 if not under else 0.26) * r.uniform(0.9, 1.1)
            lay(g, p, nrm, back, L, L * 0.6, M["BodyFeather"], shape="shardc", lift_deg=13, seed=r.random(), shade=0.2 if under else 0.0,
                violet=0.6 if under else 0.15)


def scute(g, c, axis, front, r, length, arc=150.0, thick=0.012, flare=1.10, segs=3):
    """A curved armour scute wrapping the front of a limb: a shell over an arc round it, flaring a little at its lower edge so the next one
    down tucks under it."""
    side = axis.cross(front).normalized()
    front = side.cross(axis).normalized()
    rows = []
    for k, (t, rr) in enumerate(((0.0, 1.0), (1.0, flare))):
        ring_o, ring_i = [], []
        for j in range(segs + 1):
            a = math.radians(-arc / 2 + arc * j / segs)
            d = front * math.cos(a) + side * math.sin(a)
            p = c + axis * (length * t)
            ring_o.append(g.vert(p + d * (r * rr + thick), fu=0.3 + 0.6 * t, fv=(j / segs) * 2 - 1, shade=0.5))
            ring_i.append(g.vert(p + d * (r * rr - thick * 0.5), fu=0.3 + 0.6 * t, fv=(j / segs) * 2 - 1, shade=0.5))
        rows.append((ring_o, ring_i))
    (o0, i0), (o1, i1) = rows
    mat = M["LegScale"]
    for j in range(segs):
        g.face((o0[j], o0[j + 1], o1[j + 1], o1[j]), mat)
        g.face((i0[j + 1], i0[j], i1[j], i1[j + 1]), mat)
        g.face((o0[j + 1], o0[j], i0[j], i0[j + 1]), mat)
        g.face((o1[j], o1[j + 1], i1[j + 1], i1[j]), mat)
    g.face((o0[0], o1[0], i1[0], i0[0]), mat)
    g.face((o1[segs], o0[segs], i0[segs], i1[segs]), mat)


def radius_at(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def leg_feathers(g, kind, side):
    r = random.Random(11 + side + (7 if kind == "hind" else 0))
    top, mid, low, foot = leg_points(kind, side)
    # the upper limb: a mantle of shards pointing down to the joint
    axis = (mid - top).normalized()
    u = (axis.cross(X)).normalized()
    w_ = axis.cross(u).normalized()
    rad0 = LIMB[kind][0]
    for k, f in enumerate([0.22, 0.66]):
        c = lerp(top, mid, f)
        rad = rad0[min(k + 1, len(rad0) - 1)]
        for j in range(6):
            a = TAU * (j + 0.5 * (k % 2)) / 6
            nrm = (u * math.cos(a) + w_ * math.sin(a)).normalized()
            if nrm.x * side < -0.55:
                continue                           # its inside, against the body
            p = c + nrm * rad * 0.76               # (the limb is flattened across: 0.86 of its radius at the sides)
            L = (0.24 + 0.04 * k) * r.uniform(0.92, 1.08)
            lay(g, p, nrm, axis, L, L * 0.55, M["BodyFeather"], shape="shardc", lift_deg=14, seed=r.random(), violet=0.35)
    # the middle limb: curved scutes wrapping its leading face, each tucked under the one above, and a violet tuft of shards off its back
    seg = (low - mid).normalized()
    lead = V(0, -1, 0) if kind == "fore" else V(0, 1, 0)       # the forearm's front faces forward; the hind shin's faces back
    front = (lead - seg * seg.dot(lead)).normalized()
    mid_r = LIMB[kind][1]
    L_seg = (low - mid).length
    for k in range(3):
        f = 0.10 + 0.27 * k
        scute(g, lerp(mid, low, f), seg, front, radius_at(mid_r, 0.33 + f * 0.67) * 0.95, L_seg * 0.30, arc=170, thick=0.010)
    back = -front
    for k in range(2):
        c = lerp(mid, low, 0.35 + 0.30 * k)
        nrm = (back + X * side * (0.4 if k % 2 else -0.3)).normalized()
        lay(g, c + nrm * 0.03, nrm, (seg - front * 0.4).normalized(), 0.16 + 0.03 * k, 0.07, M["BodyFeather"], shape="shardc", lift_deg=24,
            seed=r.random(), violet=1.0)
    # the lowest limb: scutes down its front, down to the toes
    low_seg = (foot - low).normalized()
    fwd = (V(0, -1, 0) - low_seg * low_seg.dot(V(0, -1, 0))).normalized()
    low_r = LIMB[kind][2]
    L_low = (foot - low).length
    for k in range(2):
        f = 0.25 + 0.32 * k
        scute(g, lerp(low, foot, f), low_seg, fwd, radius_at(low_r, 0.33 + f * 0.67) * 0.95, L_low * 0.30, arc=160, thick=0.008)


def tail_feathers(g):
    """A long whip of a tail: narrow shards lying close along it in tiers from the rump to the tip, shorter toward the end as it tapers, a
    row of armoured plates down its spine, and three long thin shards closing it to a point; violet on the undersides."""
    r = random.Random(5)
    path = catmull(TAIL_PATH, per=4)
    frames = path_frames(path)
    n = len(path)
    radii = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(TAIL_R)), TAIL_R)
    tiers = 8
    for k in range(tiers):
        f = k / (tiers - 1)
        i = int(1 + f * (n - 7))
        p, (t, A, B), rad = path[i], frames[i], radii[i]
        angs = (-100, -35, 30, 95, 180) if k % 2 else (-70, 0, 65, 140, 220)
        for ang in angs:
            a = math.radians(ang)
            nrm = (B * math.cos(a) + A * math.sin(a)).normalized()
            below = math.cos(a) < -0.3
            L = (0.32 - 0.15 * f) * r.uniform(0.92, 1.08) * (0.85 if below else 1.0)
            lay(g, p + nrm * rad * 0.8, nrm, -t, L, L * (0.34 - 0.06 * f), M["TailFeather"], shape="shardc", lift_deg=9, seed=r.random(),
                violet=0.0, thick=0.2)
    # the point: three long thin shards closing the end of the whip
    end_t, end_A, end_B = frames[-4]
    base = path[-5]
    for j, ang in enumerate((-9, 0, 9)):
        a = math.radians(ang)
        d = (-end_t * math.cos(a) + end_A * math.sin(a)).normalized()
        L = 0.34 if ang == 0 else 0.24
        blade(g, base + end_B * (0.006 if ang == 0 else 0.0) - d * 0.03, d, end_B, L, 0.050 if ang == 0 else 0.040, M["TailFeather"], shape="shard",
              thick=0.2, under=0.08, seed=r.random(), violet=0.0, tint=0.0)
    # armoured plates down the top of the tail
    for k in range(5):
        i = int(1 + k * (n - 9) / 4)
        p, (t, A, B), rad = path[i], frames[i], radii[i]
        lay(g, p + B * rad * 1.02, B, -t, 0.11 - 0.014 * k, 0.05, M["Accent"], shape="spike", lift_deg=22, sink=0.010, seed=r.random(), thick=0.35)


def head_feathers(g):
    r = random.Random(3)
    F, U = head_axes()
    k = HEAD_SCALE
    # the crest: a ridge of violet-edged blades from the forehead back over the crown, between the horns, rising as they go back
    for j, (f, L, ang) in enumerate([(0.085, 0.10, 18), (0.050, 0.15, 28), (0.012, 0.26, 52), (-0.028, 0.22, 38), (-0.066, 0.19, 30)]):
        root = H(0, f, 0.112 + 0.012 * (j > 0))
        d = (-F * math.cos(math.radians(ang)) + U * math.sin(math.radians(ang))).normalized()
        nrm = X
        blade(g, root, d, nrm, L * k, (0.075 if j == 2 else 0.058) * k, M["BodyFeather"], shape="shard" if j == 2 else "shardc", thick=0.22,
              under=0.22, seed=r.random(), violet=1.0 if j in (1, 2, 3) else 0.6, droop=0.0, bend=0.0, lead=0.5)
    for side in (1, -1):
        # side crest blades flanking the ridge
        for j, (s_, f, L, ang) in enumerate([(0.030, 0.030, 0.13, 26), (0.042, -0.020, 0.16, 30), (0.046, -0.068, 0.15, 26)]):
            root = H(s_ * side, f, 0.094)
            d = (-F * math.cos(math.radians(ang)) + U * math.sin(math.radians(ang)) + X * side * 0.25).normalized()
            nrm = (U * 0.6 + X * side).normalized()
            blade(g, root, d, nrm, L * k, 0.05 * k, M["BodyFeather"], shape="contour", thick=0.24, seed=r.random(), violet=0.35, droop=-0.04)
        # the jaw: short blades lying back along the jawline under the cheekbone, and paler ones under the throat
        for j, (f, u, L) in enumerate([(0.095, -0.006, 0.060), (0.060, -0.018, 0.075), (0.022, -0.026, 0.085), (-0.018, -0.030, 0.090),
                                       (-0.058, -0.028, 0.090)]):
            p = H(0.068 * side, f, u)
            nrm = (X * side - U * 0.35).normalized()
            lay(g, p, nrm, -F - U * 0.15, L * k, 0.040 * k, M["BodyFeather"], shape="contour", lift_deg=8, sink=0.006, seed=r.random())
        for j, (f, L) in enumerate([(0.07, 0.07), (0.025, 0.085), (-0.02, 0.095)]):
            p = H(0.030 * side, f, -0.050)
            nrm = (-U + X * side * 0.5).normalized()
            lay(g, p, nrm, -F - U * 0.4, L * k, 0.045 * k, M["UnderArmor"], shape="contour", lift_deg=8, sink=0.006, seed=r.random(), shade=1.0)
        # the nasal bristles of a raven: blades lying forward over the root of the beak
        for j, (s_, u) in enumerate([(0.020, 0.088), (0.040, 0.070)]):
            p = H(s_ * side, 0.090, u)
            nrm = (U + X * side * (0.4 + j)).normalized()
            lay(g, p, nrm, F, 0.065 * k, 0.030 * k, M["BodyFeather"], shape="contour", lift_deg=6, sink=0.008, seed=r.random())
        # the nape: a mane of blades off the back of the skull, hanging back down over the top of the neck (it covers the joint as the head
        # turns), in two tiers, the outer ones fanning to the sides
        for tier, (f, us, L) in enumerate([(-0.095, (0.090, 0.045, 0.000, -0.040), 0.20), (-0.120, (0.060, 0.020, -0.020), 0.24)]):
            for j, u in enumerate(us):
                s_ = (0.035 + 0.022 * j) if tier == 0 else (0.020 + 0.03 * j)
                p = H(s_ * side, f, u)
                out = (X * side * (0.35 + 0.25 * j)).normalized() * (0.35 + 0.25 * j)
                nrm = (-F * 0.6 + U * 0.5 + out).normalized()
                down = (-F * 0.80 - U * 0.45 + X * side * 0.12 * j).normalized()
                lay(g, p, nrm, down, (L - 0.02 * j) * k * r.uniform(0.92, 1.06), 0.060 * k, M["BodyFeather"], shape="contour", lift_deg=8 + 4 * tier,
                    sink=0.008, seed=r.random(), violet=0.25 if tier == 1 else 0.0)
    for j, u in enumerate((0.07, 0.02)):
        p = H(0, -0.125, u)
        lay(g, p, (-F + U * 0.4).normalized(), (-F * 0.8 - U * 0.5).normalized(), (0.24 - 0.02 * j) * k, 0.065 * k, M["BodyFeather"], shape="contour",
            lift_deg=10, sink=0.008, seed=r.random(), violet=0.3)


# ---------- materials: ten identities, each reading the per-vertex values the pieces carry ----------
def srgb(r, g, b):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


PAL = {
    "ink": srgb(26, 20, 56), "indigo": srgb(44, 34, 86), "violet": srgb(122, 60, 255), "violetdeep": srgb(84, 42, 190),
    "obsidian": srgb(30, 26, 54), "blueblack": srgb(26, 22, 58), "graphite": srgb(62, 56, 96),
    "crimson": srgb(172, 26, 62), "magenta": srgb(184, 36, 112), "lavender": srgb(143, 134, 176), "lavdark": srgb(82, 74, 116),
    "horn0": srgb(72, 12, 36), "horn1": srgb(152, 24, 58), "horn2": srgb(204, 54, 100),
    "talon0": srgb(38, 28, 50), "talon1": srgb(8, 6, 12), "beak": srgb(46, 40, 66), "beaktip": srgb(14, 12, 22),
    "iris": srgb(238, 230, 255), "irisdark": srgb(132, 84, 240), "sclera": srgb(14, 10, 24),
    "accent": srgb(128, 30, 96), "plum": srgb(96, 40, 104), "scale": srgb(62, 48, 108), "scaledark": srgb(24, 18, 44),
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
            n = self.node("ShaderNodeAttribute", attribute_name=name)
            self.cache[name] = n.outputs["Fac"]
        return self.cache[name]

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            self.t.links.new(v, sock)

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        return n.outputs[0]

    def ramp(self, x, a, b):
        """smoothstep(a, b, x)"""
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

    def out(self, colour, rough, height=None, strength=0.25, dist=0.003):
        self._in(self.bsdf.inputs["Base Color"], colour)
        self._in(self.bsdf.inputs["Emission Color"], colour)
        self.bsdf.inputs["Emission Strength"].default_value = 0.0
        self._in(self.bsdf.inputs["Roughness"], rough)
        self.bsdf.inputs["Metallic"].default_value = 0.0
        if height is not None:
            bump = self.node("ShaderNodeBump")
            bump.inputs["Strength"].default_value = strength
            bump.inputs["Distance"].default_value = dist
            self._in(bump.inputs["Height"], height)
            self.t.links.new(bump.outputs["Normal"], self.bsdf.inputs["Normal"])


def feather_graph(nt, base_a, base_b, edge_violet=0.7, under_violet=0.75, rough=0.36):
    """A hard feather: dark indigo, saturated violet along its edges and over its underside, violet or crimson-magenta at the tip, a darker
    shaft, barbs in the normal map."""
    fu, fv, seed, tint, violet, shade, under = (nt.attr(k) for k in ("fu", "fv", "seed", "tint", "violet", "shade", "under"))
    afv = nt.math("ABSOLUTE", fv)
    col = nt.mix(PAL[base_a], PAL[base_b], nt.math("ADD", nt.math("MULTIPLY", shade, 0.6), nt.math("MULTIPLY", seed, 0.45), clamp=True))
    col = nt.mix(col, PAL["violet"], nt.math("MULTIPLY", nt.ramp(afv, 0.70, 1.0), edge_violet))
    col = nt.mix(col, nt.mix(PAL["violetdeep"], PAL["violet"], nt.ramp(fu, 0.2, 0.9)), nt.math("MULTIPLY", nt.ramp(under, 0.05, 0.6), under_violet))
    col = nt.mix(col, PAL["violet"], nt.math("MULTIPLY", nt.ramp(fu, 0.45, 1.0), violet))
    tipc = nt.math("MULTIPLY", nt.ramp(fu, 0.74, 0.97), tint)
    col = nt.mix(col, nt.mix(PAL["crimson"], PAL["magenta"], nt.ramp(fu, 0.88, 1.0)), tipc)
    rach = nt.math("SUBTRACT", 1.0, nt.ramp(afv, 0.04, 0.13))
    col = nt.mix(col, PAL["ink"], nt.math("MULTIPLY", rach, 0.35))
    col = nt.mix(col, PAL["blueblack"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.22)), 0.45))
    value = nt.math("ADD", 0.88, nt.math("MULTIPLY", seed, 0.24))
    col = nt.mix(col, (0, 0, 0, 1), nt.math("SUBTRACT", 1.0, value))
    barbs = nt.math("FRACT", nt.math("ADD", nt.math("MULTIPLY", fu, 30.0), nt.math("MULTIPLY", afv, 6.0)))
    barbs = nt.math("ABSOLUTE", nt.math("SUBTRACT", barbs, 0.5))
    height = nt.math("ADD", nt.math("MULTIPLY", barbs, 0.6), nt.math("MULTIPLY", rach, 0.8))
    r = nt.math("ADD", rough, nt.math("MULTIPLY", seed, 0.12))
    r = nt.math("SUBTRACT", r, nt.math("MULTIPLY", rach, 0.12))
    nt.out(col, r, height, strength=0.18, dist=0.002)


def make_materials():
    mats = []
    for name in MATS:
        m = bpy.data.materials.new(N + name)
        nt = NT(m)
        fu, fv, seed, tint, violet, shade = (nt.attr(k) for k in ("fu", "fv", "seed", "tint", "violet", "shade"))
        if name == "BodyFeather":
            feather_graph(nt, "ink", "indigo", edge_violet=0.38, under_violet=0.45, rough=0.42)
        elif name == "WingFeather":
            feather_graph(nt, "ink", "indigo", edge_violet=0.55, under_violet=0.60, rough=0.34)
        elif name == "TailFeather":
            feather_graph(nt, "ink", "indigo", edge_violet=0.45, under_violet=0.55, rough=0.36)
        elif name == "UnderArmor":
            afv = nt.math("ABSOLUTE", fv)
            col = nt.mix(PAL["lavdark"], PAL["lavender"], nt.math("MULTIPLY", shade, nt.math("ADD", 0.75, nt.math("MULTIPLY", seed, 0.3))))
            rim = nt.math("MAXIMUM", nt.ramp(afv, 0.80, 1.0), nt.ramp(fu, 0.84, 1.0))
            col = nt.mix(col, PAL["lavdark"], nt.math("MULTIPLY", rim, 0.8))
            col = nt.mix(col, PAL["lavdark"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.3)), 0.6))
            ridge = nt.math("SUBTRACT", 1.0, nt.ramp(afv, 0.03, 0.2))
            nt.out(col, nt.math("ADD", 0.48, nt.math("MULTIPLY", rim, -0.1)), nt.math("ADD", ridge, nt.math("MULTIPLY", rim, -0.5)), strength=0.2)
        elif name == "HeadBeak":
            # the skull and brow: dark graphite; the beak (shade 1): a glossy dark keratin, darkest at the hook
            col = nt.mix(PAL["obsidian"], PAL["graphite"], nt.math("MULTIPLY", shade, 0.5))
            beak = nt.ramp(shade, 0.9, 1.0)
            bk = nt.mix(PAL["beak"], PAL["beaktip"], nt.ramp(fu, 0.45, 1.0))
            col = nt.mix(col, bk, beak)
            grain = nt.math("FRACT", nt.math("MULTIPLY", fu, 18.0))
            nt.out(col, nt.math("SUBTRACT", 0.55, nt.math("MULTIPLY", beak, 0.33)), nt.math("MULTIPLY", grain, 0.3), strength=0.1)
        elif name == "Horn":
            col = nt.mix(nt.mix(PAL["horn0"], PAL["horn1"], nt.ramp(fu, 0.0, 0.45)), PAL["horn2"], nt.ramp(fu, 0.55, 1.0))
            rings = nt.math("ABSOLUTE", nt.math("SUBTRACT", nt.math("FRACT", nt.math("MULTIPLY", fu, 9.0)), 0.5))
            col = nt.mix(col, PAL["horn0"], nt.math("MULTIPLY", nt.math("SUBTRACT", 0.5, rings), 0.6))
            nt.out(col, nt.math("ADD", 0.42, nt.math("MULTIPLY", rings, 0.2)), rings, strength=0.35)
        elif name == "Talon":
            col = nt.mix(PAL["talon0"], PAL["talon1"], nt.ramp(fu, 0.15, 0.75))
            nt.out(col, 0.22, nt.math("FRACT", nt.math("MULTIPLY", fu, 6.0)), strength=0.08)
        elif name == "Eye":
            # fu: toward the front of the eye (1 at its pole); fv: up; shade: across (outward). A crimson iris with a slit pupil and one catch-light.
            iris = nt.ramp(fu, 0.50, 0.62)
            col = nt.mix(PAL["sclera"], nt.mix(PAL["irisdark"], PAL["iris"], nt.ramp(fu, 0.66, 0.9)), iris)
            ash = nt.math("ABSOLUTE", shade)
            slit = nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(ash, 0.07, 0.12)), nt.ramp(fu, 0.70, 0.8))
            col = nt.mix(col, (0.005, 0.002, 0.004, 1), slit)
            dx = nt.math("SUBTRACT", shade, -0.26)
            dy = nt.math("SUBTRACT", fv, 0.30)
            spot = nt.math("ADD", nt.math("MULTIPLY", dx, dx), nt.math("MULTIPLY", dy, dy))
            glint = nt.math("SUBTRACT", 1.0, nt.ramp(spot, 0.0015, 0.0045))
            col = nt.mix(col, (0.95, 0.80, 0.84, 1), nt.math("MULTIPLY", glint, 0.85))
            nt.out(col, 0.14)
        elif name == "Accent":
            afv = nt.math("ABSOLUTE", fv)
            col = nt.mix(PAL["accent"], PAL["crimson"], nt.math("MULTIPLY", nt.math("MAXIMUM", nt.ramp(afv, 0.7, 1.0), nt.ramp(fu, 0.75, 1.0)), 0.7))
            col = nt.mix(col, PAL["plum"], nt.math("MULTIPLY", nt.math("SUBTRACT", 1.0, nt.ramp(fu, 0.0, 0.3)), 0.6))
            nt.out(col, 0.3, nt.math("SUBTRACT", 1.0, nt.ramp(afv, 0.02, 0.25)), strength=0.25)
        elif name == "LegScale":
            vor = nt.node("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
            vor.inputs["Scale"].default_value = 70.0
            tc = nt.node("ShaderNodeTexCoord")
            nt.t.links.new(tc.outputs["Object"], vor.inputs["Vector"])
            edge = nt.ramp(vor.outputs["Distance"], 0.0, 0.08)
            col = nt.mix(PAL["scaledark"], PAL["scale"], edge)
            col = nt.mix(col, PAL["plum"], nt.math("MULTIPLY", seed, 0.0))
            nt.out(col, nt.math("ADD", 0.5, nt.math("MULTIPLY", edge, 0.15)), edge, strength=0.45, dist=0.004)
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


# ---------- assembling the pieces ----------
JOINTS = ["Body", "Head", "WingL", "WingR", "Tail"]


def build_model(level, coll, wing_pose=REST_POSE, suffix=""):
    blockout = level == 0
    pieces = {}
    g = Geo(N + "Source_Body" + suffix)
    build_body(g, n=8 if blockout else 16)
    for side in (1, -1):
        for kind in ("fore", "hind"):
            build_leg(g, kind, side, blockout)
            if level >= 3:
                leg_feathers(g, kind, side)
    if level >= 3:
        body_feathers(g)
    pieces["Body"] = g
    g = Geo(N + "Source_Head" + suffix)
    build_skull(g, blockout)
    build_beak(g, "upper")
    if not blockout:
        build_beak(g, "lower")
        glow = Geo(N + "Source_HeadGlow" + suffix)
        for side in (1, -1):
            build_eye(g, side)
            build_brow(g, side)
            build_eye_glow(glow, g, side)
        pieces["HeadGlow"] = glow
    for side in (1, -1):
        build_horn(g, side, blockout)
    if level >= 3:
        head_feathers(g)
    pieces["Head"] = g
    for side, tag in ((1, "WingL"), (-1, "WingR")):
        g = Geo(N + "Source_" + tag + suffix)
        build_wing(g, side, wing_pose, blockout=level < 2)
        pieces[tag] = g
    g = Geo(N + "Source_Tail" + suffix)
    build_tail_base(g, n=6 if blockout else 10)
    if level >= 2:
        tail_feathers(g)
    pieces["Tail"] = g
    return {k: g.finish(coll) for k, g in pieces.items()}


def pivots(coll):
    out = {}
    for j, p in PIVOT.items():
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=0.02, matrix=Matrix.Translation(p))
        me = bpy.data.meshes.new(N + "Pivot_" + j)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(N + "Pivot_" + j, me)
        coll.objects.link(o)
        out[j] = o
    return out


# ---------- review renders ----------
def world_setup():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Studio")
    sc.world = w
    w.color = (0.055, 0.055, 0.06)
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    bg.inputs[1].default_value = 1.0
    cam = bpy.data.cameras.new("ReviewCam")
    co = bpy.data.objects.new("ReviewCam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"


def lights_setup():
    sc = bpy.context.scene
    k = float(os.environ.get("DW_LIGHT", "0.18"))
    for name, energy, loc, size in (("Key", 900, (-2.2, -3.0, 3.4), 2.5), ("Fill", 320, (3.2, -2.0, 1.6), 3.0), ("Rim", 700, (1.0, 3.4, 3.2), 2.0),
                                    ("Back", 240, (-2.6, 2.6, 1.2), 2.5)):
        L = bpy.data.lights.new(name, "AREA")
        L.energy = energy * k
        L.size = size
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (V(0, 0, 0.9) - V(*loc)).to_track_quat("-Z", "Y").to_euler()
    me = bpy.data.meshes.new("Floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12)
    bm.to_mesh(me)
    bm.free()
    fl = bpy.data.objects.new("Floor", me)
    sc.collection.objects.link(fl)
    m = bpy.data.materials.new("FloorGrey")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    return fl


def engine(kind):
    sc = bpy.context.scene
    if kind == "clay":
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading
        sh.light = "STUDIO"
        sh.color_type = "SINGLE"
        sh.single_color = (0.50, 0.50, 0.54)
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.cavity_ridge_factor = 1.0
        sh.cavity_valley_factor = 1.0
        sh.show_object_outline = True
        sh.object_outline_color = (0.0, 0.0, 0.0)
        sh.show_specular_highlight = True
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
        sc.cycles.samples = 48
        sc.cycles.use_denoising = True


VIEWS = {
    "front": (V(0, -1, 0), True), "side": (V(1, 0, 0), True), "back": (V(0, 1, 0), True), "threeq": (V(0.85, -1.0, 0.42), False),
    "beauty": (V(-0.95, -1.15, 0.30), False), "head": (V(0.75, -1.0, 0.18), False), "headside": (V(1, -0.08, 0.02), True),
    "headfront": (V(0.0, -1, 0.10), True), "top": (V(0.001, 0.0, 1), True), "low": (V(0.5, -1.0, -0.18), False), "feet": (V(0.7, -1.0, 0.25), False),
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
    up = Z if abs(d.z) < 0.95 else Y * -1
    cam.data.clip_start, cam.data.clip_end = 0.01, 100
    if ortho:
        cam.data.type = "ORTHO"
        right = up.cross(-d).normalized() if abs(d.z) < 0.95 else X
        upv = (-d).cross(right).normalized()
        ext = max(abs((p - c).dot(right)) for p in (V(lo.x, lo.y, lo.z), V(hi.x, hi.y, hi.z), V(lo.x, hi.y, hi.z), V(hi.x, lo.y, lo.z),
                                                    V(lo.x, lo.y, hi.z), V(hi.x, hi.y, lo.z), V(lo.x, hi.y, lo.z), V(hi.x, lo.y, hi.z)))
        ext2 = max(abs((p - c).dot(upv)) for p in (lo, hi, V(lo.x, hi.y, lo.z), V(hi.x, lo.y, hi.z), V(lo.x, lo.y, hi.z), V(hi.x, hi.y, lo.z)))
        cam.data.ortho_scale = (extent * 2) if extent is not None else max(ext, ext2) * 2 * 1.08
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


def sheet(paths, out, cols, tile=640, bg=(0.05, 0.05, 0.055)):
    rows = (len(paths) + cols - 1) // cols
    canvas = np.zeros((rows * tile, cols * tile, 4), dtype=np.float32)
    canvas[..., :3] = bg
    canvas[..., 3] = 1
    for k, p in enumerate(paths):
        im = resize(load_px(p), (tile, tile))
        r, c = rows - 1 - k // cols, k % cols           # (pixels run bottom-up)
        canvas[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile] = im
        canvas[r * tile:(r + 1) * tile, c * tile:c * tile + 2, :3] = 0.25
        canvas[r * tile:r * tile + 2, c * tile:(c + 1) * tile, :3] = 0.25
    save_px(out, canvas)
    return out


CONCEPT = os.path.join(K.ROOT, "assets", "concepts", "views", "Dreadwing")
# how the concept's side view maps to the model: metres per pixel, the pixel at y = 0 and the ground line
CONCEPT_SIDE = (0.0025, 420, 800)
CONCEPT_FRONT = (0.00232, 495, 825)


def overlay(view, objs, out):
    """The model rendered over the concept at the same scale (side or front), and the two side by side."""
    k, x0, g0 = CONCEPT_SIDE if view == "side" else CONCEPT_FRONT
    src = os.path.join(CONCEPT, "1_side.png" if view == "side" else "2_front.png")
    across = (512 - x0) * k
    target = V(0, across, (g0 - 512) * k) if view == "side" else V(across, 0, (g0 - 512) * k)
    tmp = shoot(os.path.join(REVIEW, "_ov.png"), view, objs, size=1024, target=target, extent=512 * k, transparent=True)
    a = load_px(tmp)
    con = load_px(src)
    alpha = a[..., 3:4] * 0.62
    mixed = con.copy()
    mixed[..., :3] = con[..., :3] * (1 - alpha) + a[..., :3] * alpha
    # an outline of the model's silhouette, so its edge reads against the painting
    m = a[..., 3] > 0.5
    edge = m & ~(np.roll(m, 2, 0) & np.roll(m, -2, 0) & np.roll(m, 2, 1) & np.roll(m, -2, 1))
    mixed[edge, :3] = (0.2, 1.0, 0.6)
    both = np.concatenate([con, np.dstack([a[..., :3] * a[..., 3:4] + 0.05 * (1 - a[..., 3:4]), np.ones_like(a[..., :1])])], axis=1)
    save_px(out, mixed)
    save_px(out.replace(".png", "_pair.png"), both)
    return out


def set_visible(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_viewport = not on


def stage_renders(stage, model, folded, kind):
    """The stage's own review: front, side, back and three-quarter, wings extended and folded, head close-ups, and the concept overlays."""
    engine(kind)
    parts = list(model.values())
    head = [o for k, o in model.items() if k.startswith("Head")]
    shots_ = []
    tag = os.path.join(REVIEW, stage)
    if ONLY is None or "ext" in ONLY:
        for v in ("front", "side", "back", "threeq"):
            shots_.append(shoot("%s_ext_%s.png" % (tag, v), v, parts))
        sheet(shots_[-4:], tag + "_sheet_ext.png", 2)
    if folded and (ONLY is None or "fold" in ONLY):
        set_visible([model["WingL"], model["WingR"]], False)
        set_visible(folded, True)
        fparts = [model["Body"], model["Head"], model["HeadGlow"], model["Tail"]] + folded
        fs = [shoot("%s_fold_%s.png" % (tag, v), v, fparts) for v in ("front", "side", "back", "threeq")]
        sheet(fs, tag + "_sheet_fold.png", 2)
        set_visible(folded, False)
        set_visible([model["WingL"], model["WingR"]], True)
    if ONLY is None or "head" in ONLY:
        hc = HEAD_O + V(0, -0.02, 0.06)
        hs = [shoot("%s_head_%s.png" % (tag, v), v, head, target=hc, extent=0.36, lens=70) for v in ("head", "headside", "headfront")]
        hs.append(shoot("%s_head_top.png" % tag, (V(-0.6, -1, 0.9), False), head, target=hc, extent=0.36, lens=70))
        sheet(hs, tag + "_sheet_head.png", 2)
    if ONLY is not None and "wing" in ONLY:
        w = [model["WingL"]]
        ws = [shoot("%s_wing_%s.png" % (tag, v), (d, False), w, lens=50) for v, d in
              (("top", V(0.2, 0.5, 1.0)), ("under", V(0.3, -0.6, -0.8)), ("front", V(0.3, -1, 0.15)), ("back", V(0.2, 1, 0.3)))]
        sheet(ws, tag + "_sheet_wing.png", 2)
    if ONLY is None or "ov" in ONLY:
        overlay("side", parts, tag + "_overlay_side.png")
        overlay("front", parts, tag + "_overlay_front.png")


def report(model, extra=None):
    total = 0
    for k, o in model.items():
        n = tri_count([o])
        total += n
        print("TRIS %-6s %6d" % (k, n))
    print("TRIS TOTAL", total)
    lo, hi = bbox(list(model.values()))
    print("BOX", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
    beak = H(0, BEAK_UP[-2][0], BEAK_UP[-2][1])
    length = TAIL_PATH[1].y - beak.y
    # the wingspan the directive measures is with the wings fully extended, as in flight (the rest pose holds them raised)
    span = 0.0
    if "WingL" in model and len(model["WingL"].data.polygons) > 100:
        g = Geo("SpanCheck")
        build_wing(g, 1, "extended")
        o = g.finish(bpy.context.scene.collection)
        span = 2 * max(v.co.x for v in o.data.vertices)
        bpy.data.objects.remove(o, do_unlink=True)
    print("NOSE->TAILBASE %.3f  REST WIDTH %.3f  EXTENDED WINGSPAN %.3f  RATIO %.2f" % (length, hi.x - lo.x, span, span / length))
    return total


# ---------- the game pieces: one per joint, unwrapped and baked to one 2048 set each ----------
MAP = 2048
EMPTY = (1.0, 0.0, 1.0, 1.0)      # the colour map's fill, so its gutters can be found and bled


def select_only(objs, active=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


GLOW_HEX = "d8ccff"      # the iris glow: Neon in the game (PetRig names it Head_Glow_<hex> and welds it to the head)


def game_name(j):
    return N + ("Head_Glow_" + GLOW_HEX if j == "HeadGlow" else j)


def glow_material():
    m = bpy.data.materials.get(N + "IrisGlow") or bpy.data.materials.new(N + "IrisGlow")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(216, 204, 255)
    b.inputs["Emission Color"].default_value = srgb(216, 204, 255)
    b.inputs["Emission Strength"].default_value = 3.0
    return m


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
    boost = {M["Eye"]: 6.0, M["HeadBeak"]: 1.5, M["Horn"]: 1.3} if joint == "Head" else {}
    uv = me.uv_layers.active.data
    for mat, k in boost.items():
        loops = [l for p in me.polygons if p.material_index == mat for l in p.loop_indices]
        if not loops:
            continue
        c = sum((uv[l].uv for l in loops), Vector((0, 0))) / len(loops)
        for l in loops:
            uv[l].uv = c + (uv[l].uv - c) * k
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=0.006, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def px_of(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def bake_piece(o, joint, mats, hide):
    sc = bpy.context.scene
    imgs = {}
    for kind in ("color", "normal", "roughness", "ao"):
        img = bpy.data.images.new(N + joint + "_" + kind, MAP, MAP, alpha=False)
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
    sc.cycles.samples = 16
    target(imgs["color"])
    for b in bsdfs:
        b.inputs["Emission Strength"].default_value = 1.0
    bpy.ops.object.bake(type="EMIT", margin=16, use_clear=True, target="IMAGE_TEXTURES")
    for b in bsdfs:
        b.inputs["Emission Strength"].default_value = 0.0
    target(imgs["roughness"])
    bpy.ops.object.bake(type="ROUGHNESS", margin=16, use_clear=True, target="IMAGE_TEXTURES")
    target(imgs["normal"])
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=16, use_clear=True, target="IMAGE_TEXTURES")
    sc.world.light_settings.distance = 0.12
    sc.cycles.samples = 64
    target(imgs["ao"])
    bpy.ops.object.bake(type="AO", margin=16, use_clear=True, target="IMAGE_TEXTURES")
    for o2 in hide:
        o2.hide_render = False
    # the layers shade each other: ambient occlusion goes into the colour map, gently, where the map has paint
    col, ao = px_of(imgs["color"]), px_of(imgs["ao"])
    empty = (np.abs(col[..., 0] - 1) < 1e-3) & (col[..., 1] < 1e-3) & (np.abs(col[..., 2] - 1) < 1e-3)
    shade = (0.42 + 0.58 * ao[..., :1])
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
    # the game piece's one material: the three maps
    m = bpy.data.materials.new(N + joint + "_Baked")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    ci = t.nodes.new("ShaderNodeTexImage"); ci.image = imgs["color"]; ci.name = "ColorMap"
    ni = t.nodes.new("ShaderNodeTexImage"); ni.image = imgs["normal"]; ni.name = "NormalMap"
    ri = t.nodes.new("ShaderNodeTexImage"); ri.image = imgs["roughness"]; ri.name = "RoughMap"
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(ci.outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(ni.outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    t.links.new(ri.outputs["Color"], bsdf.inputs["Roughness"])
    o.data.materials.clear()
    o.data.materials.append(m)
    return m


def export_fbx(game, markers):
    os.makedirs(K.OUT, exist_ok=True)
    path = os.path.join(K.OUT, PET + ".fbx")
    objs = list(game.values()) + list(markers)
    select_only(objs)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False)
    return path


def verify_fbx(path):
    """Imports the FBX into a scratch scene: names, scale, size and triangles."""
    before = set(bpy.data.objects)
    sc = bpy.data.scenes.new("FbxCheck")
    win_scene = bpy.context.window.scene if bpy.context.window else None
    with bpy.context.temp_override(scene=sc):
        bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    out = {}
    dg = bpy.context.evaluated_depsgraph_get()
    for o in new:
        if o.type != "MESH":
            continue
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        out[o.name] = (tuple(round(v, 4) for v in o.scale), tris, tuple(round(v, 3) for v in o.dimensions), len(o.data.materials))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(sc)
    return out


def markers(coll):
    out = list(pivots(coll).values())
    c, axis = eye_frame(1)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.02, matrix=Matrix.Translation(c + axis * EYE_R * HEAD_SCALE))
    me = bpy.data.meshes.new(N + "Point_Head_Eye")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(N + "Point_Head_Eye", me)
    coll.objects.link(o)
    for m in out + [o]:
        m.hide_render = True             # markers for the game's joints and effects, never part of the look
    return out + [o]


def turn_about(o, pivot, axis, deg):
    o.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-pivot) @ o.matrix_world


def save_blend():
    """The .blend, written from the scene alone (not the window manager, which remembers this machine's folders), every path relative."""
    os.makedirs(K.TOOLS, exist_ok=True)
    path = os.path.join(K.TOOLS, PET + ".blend")
    render = bpy.context.scene.render
    render.filepath = "//" + "_" * 1020
    render.filepath = "//"
    for img in bpy.data.images:
        if img.filepath_raw and not img.filepath_raw.startswith("//"):
            img.filepath_raw = bpy.path.relpath(img.filepath_raw, start=K.TOOLS)
        for packed in img.packed_files:
            packed.filepath = img.filepath_raw
    if os.path.exists(path):
        os.remove(path)
    bpy.data.libraries.write(path, {bpy.context.scene}, path_remap="RELATIVE_ALL", compress=True)
    return path


def scan_blend(path):
    import subprocess
    raw = open(path, "rb").read()
    if raw[:4] == b"\x28\xb5\x2f\xfd":
        raw = subprocess.run(["zstd", "-dc", path], capture_output=True).stdout
    hits = {}
    for pat in (b"/Users/", b"/private/", b"/tmp/", b"/var/", b"/home/", b"scratchpad"):
        if pat in raw:
            hits[pat.decode()] = raw.count(pat)
    return hits


def sheet_spans(tiles, out, cols, tile=600, bg=(0.05, 0.05, 0.055)):
    """tiles: rows of (path, span); a span-2 tile is twice as wide."""
    H = len(tiles) * tile
    canvas = np.zeros((H, cols * tile, 4), dtype=np.float32)
    canvas[..., :3] = bg
    canvas[..., 3] = 1
    for r, row in enumerate(tiles):
        c = 0
        for path, span in row:
            im = resize(load_px(path), (tile, tile * span))
            y0 = H - (r + 1) * tile
            canvas[y0:y0 + tile, c * tile:(c + span) * tile] = im
            canvas[y0:y0 + tile, c * tile:c * tile + 2, :3] = 0.22
            canvas[y0:y0 + 2, c * tile:(c + span) * tile, :3] = 0.22
            c += span
    save_px(out, canvas)
    return out


def final_review(game, folded, model):
    """The section-12 renders and the review sheet: folded (front, side, rear, three-quarter), extended (front, rear, side, three-quarter),
    the beauty shot, head close-ups, clay, a joint-motion check, and the model beside the concept's side view."""
    tag = os.path.join(REVIEW, "final")
    parts = list(game.values())
    wings = [game["WingL"], game["WingR"]]
    engine("cycles")
    bpy.context.scene.cycles.samples = 64
    R = {}
    set_visible(wings, False)
    set_visible(folded, True)
    fparts = [game["Body"], game["Head"], game["HeadGlow"], game["Tail"]] + folded
    for v in ("front", "side", "back", "threeq"):
        R["fold_" + v] = shoot("%s_fold_%s.png" % (tag, v), v, fparts, size=900)
    set_visible(folded, False)
    set_visible(wings, True)
    for v in ("front", "back", "side", "threeq", "low"):
        R["ext_" + v] = shoot("%s_ext_%s.png" % (tag, v), v, parts, size=900)
    hc = HEAD_O + V(0, -0.02, 0.06)
    heads = [game["Head"], game["HeadGlow"]]
    R["head"] = shoot(tag + "_head.png", "head", heads, target=hc, extent=0.36, lens=70, size=900)
    R["headside"] = shoot(tag + "_headside.png", "headside", heads, target=hc, extent=0.36, size=900)
    R["headfront"] = shoot(tag + "_headfront.png", "headfront", heads, target=hc, extent=0.36, size=900)
    # the beauty shot: wings raised about the shoulders, as the game raises them
    turn_about(game["WingL"], PIVOT["WingL"], Y, -24)
    turn_about(game["WingR"], PIVOT["WingR"], Y, 24)
    R["beauty"] = shoot(tag + "_beauty.png", "beauty", parts, size=800, lens=50, wide=2.0, target=V(0, -0.05, 0.92), extent=1.75)
    turn_about(game["WingL"], PIVOT["WingL"], Y, 24)
    turn_about(game["WingR"], PIVOT["WingR"], Y, -24)
    # the joints at their limits in the game's flap (wings down, head up, tail turned): nothing may open at a joint
    keep = {k: o.matrix_world.copy() for k, o in game.items()}
    turn_about(game["WingL"], PIVOT["WingL"], Y, 34)
    turn_about(game["WingR"], PIVOT["WingR"], Y, -34)
    turn_about(game["Head"], PIVOT["Head"], X, 23)
    turn_about(game["HeadGlow"], PIVOT["Head"], X, 23)
    turn_about(game["Tail"], PIVOT["Tail"], Z, 10)
    turn_about(game["Tail"], PIVOT["Tail"], X, -14)
    R["joints"] = shoot(tag + "_joints.png", (V(0.9, -0.7, 0.25), False), parts, size=900)
    R["joints_back"] = shoot(tag + "_joints_back.png", (V(0.5, 1.0, 0.7), False), [game["Body"]] + wings, size=900, target=PIVOT["Body"] + V(0, 0, 0.25),
                             extent=0.55)
    for k, o in game.items():
        o.matrix_world = keep[k]
    # clay: the geometry without its paint
    engine("clay")
    R["clay"] = shoot(tag + "_clay.png", "threeq", parts, size=900)
    engine("cycles")
    bpy.context.scene.cycles.samples = 64
    overlay("side", parts, tag + "_concept_side.png")
    R["pair"] = tag + "_concept_side_pair.png"
    out = os.path.join(K.ROOT, "renders", "pets", "ExclusiveEgg", PET + "_review.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet_spans([
        [(R["fold_front"], 1), (R["fold_side"], 1), (R["fold_back"], 1), (R["fold_threeq"], 1)],
        [(R["ext_front"], 1), (R["ext_back"], 1), (R["ext_side"], 1), (R["ext_threeq"], 1)],
        [(R["beauty"], 2), (R["head"], 1), (R["headside"], 1)],
        [(R["pair"], 2), (R["joints"], 1), (R["clay"], 1)],
    ], out, 4)
    print("REVIEW", out)
    return R


if __name__ == "__main__":
    K.start(PET, "ExclusiveEgg")
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    world_setup()
    model_coll = K.get_coll(PET + "_Model")
    fold_coll = K.get_coll(PET + "_FoldedWings")
    model = build_model(LEVEL, model_coll)
    folded = []
    if LEVEL >= 2:
        for side, tag in ((1, "WingL"), (-1, "WingR")):
            g = Geo(N + "Source_" + tag + "_Folded")
            build_wing(g, side, "folded")
            folded.append(g.finish(fold_coll))
        set_visible(folded, False)
    report(model)
    if LEVEL <= 3:
        stage_renders(STAGE, model, folded, "clay")
    if LEVEL >= 4:
        mats = make_materials()
        assign([o for k, o in model.items() if k != "HeadGlow"] + folded, mats)
        if "HeadGlow" in model:
            model["HeadGlow"].data.materials.append(glow_material())
        lights_setup()
    if LEVEL == 4 and "--albedo" in ARGS:
        for m in mats:
            next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Emission Strength"].default_value = 1.0
        for o in bpy.data.objects:
            if o.type == "LIGHT":
                o.data.energy = 0.0
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    if LEVEL == 4:
        stage_renders(STAGE + ("_albedo" if "--albedo" in ARGS else ""), model, folded, "cycles")
    if LEVEL >= 5:
        floor = bpy.data.objects["Floor"]
        engine("cycles")
        game_coll = K.get_coll(PET)
        game = make_game(model, game_coll)
        for j, o in game.items():
            unwrap(o, j)
        hide = list(model.values()) + folded + [floor]
        for j, o in game.items():
            if j == "HeadGlow":
                o.data.materials.clear()
                o.data.materials.append(glow_material())
                continue
            bake_piece(o, j, mats, hide)
            print("BAKED", j, flush=True)
        set_visible(list(model.values()), False)
        mk = markers(game_coll)
        print("GAME TRIS", {j: tri_count([o]) for j, o in game.items()}, "TOTAL", tri_count(list(game.values())))
        if LEVEL == 5:
            stage_renders(STAGE, game, folded, "cycles")
    if LEVEL >= 6:
        path = export_fbx(game, mk)
        check = verify_fbx(path)
        for k, v in sorted(check.items()):
            print("FBX", k, "scale", v[0], "tris", v[1], "size", v[2], "materials", v[3])
        print("FBX TOTAL TRIS", sum(v[1] for k, v in check.items() if "_Pivot_" not in k and "_Point_" not in k))
    if LEVEL == 7:
        final_review(game, folded, model)
    if LEVEL >= 6:
        # the file: the source pieces with their ten materials, the folded wings, the game pieces and markers; no review rig
        for name in ("Floor", "ReviewCam", "Key", "Fill", "Rim", "Back"):
            o = bpy.data.objects.get(name)
            if o:
                bpy.data.objects.remove(o, do_unlink=True)
        set_visible(list(model.values()), True)
        set_visible(folded, False)
        for o in folded:
            o.hide_viewport = False
        for c in list(bpy.data.collections):
            if c.name == PET + "_Hi":
                bpy.data.collections.remove(c)
        bpy.data.orphans_purge(do_recursive=True)
        blend = save_blend()
        print("BLEND", blend, "SCAN", scan_blend(blend))

"""Eclipse Dreadwing, "Devourer of Stars" (Divine, Exclusive Egg), rigged: the model exactly as it was modelled and baked, given a skeleton.

Written by the project's pet pipeline. The look is kept as it is: the same game pieces (EclipseDreadwing_Body, _Head, _Head_Glow_d8ccff, _Tail,
_WingL, _WingR), the same UVs, the same baked colour, normal and roughness maps (assets/pets/ExclusiveEgg/EclipseDreadwing_*.png are never
written here). Only how it moves changes. It was a jointed pet (five rigid pieces turning on pivots: wings that were each one stiff slab, a
body that had no neck, no legs and no spine); it becomes a skinned one on a skeleton of 45 bones:

    Root; Hips, Spine, Chest (the trunk); Neck1-3, Head, Jaw (the neck's S-curve, the head, the lower beak);
    Tail1-4 (the whip of a tail); per side Wing1-3 (shoulder, elbow, wrist), Prim1-3 (three fans of primary feathers), Sec1-2 (two banks
    of secondaries); LegF*/LegB* 1-3 and Foot* (a drake's four legs: hip, knee, hock or wrist, and the foot with its toes and talons).

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/eclipse_dreadwing_rig.py -- <stage> [limits] [--review dir]

stages: probe (builds the rig and prints its numbers), rig (also every pose, the safe ranges and the review renders, the range sheets with
`limits`; writes nothing into the project), all (also the .blend, the FBX, and the temporary preview data module for Studio). It reads the Dreadwing's own .blend
(tools/blender/pets/ExclusiveEgg/EclipseDreadwing.blend): its game pieces (collection EclipseDreadwing) are copied, never changed, so the
file can be rebuilt any number of times; the bake sources stay in it untouched. Faces -Y, Z up, 1 unit = 1 metre, +X is its left.

How the skin is weighted (no feather ever shears):
    - the trunk, neck, wing arms, tail loft and the leg tubes take smooth weights from where each point lies along its bone chain, with a
      short blend at every joint, so the neck bends in an S and the knees fold without a crease; pieces that overlap there take the same weights;
    - every feather, scute and plate is one island and takes ONE weight vector: the one at its root, so it rides its bone as a rigid blade;
    - the wing's flight feathers are split by where they sit along the span into Prim1-3 (the hand) and Sec1-2 (the forearm); the coverts and
      the shorter feathers stay on the arm bones, so the roots of the flight feathers stay covered as the fans spread;
    - the head and its horns and eyes are rigid on Head; the lower beak (its own island) is rigid on Jaw; the eye glow is rigid on Head.
Where the build order of the old model's islands is relied on (the wing's feathers, the legs' and the tail's), the script asserts it.
"""
import base64
import collections
import math
import os
import struct
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit  # noqa: E402
from pet_kit import V, smooth  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "probe"
ROOT = pet_kit.ROOT
PET, EGG = "EclipseDreadwing", "ExclusiveEgg"
N = PET + "_"
REVIEW = ARGS[ARGS.index("--review") + 1] if "--review" in ARGS else os.path.join(ROOT, "renders", "exclusive_pets", "dreadwing_rig")
SOURCE = os.path.join(ROOT, "tools/blender/pets", EGG, PET + ".blend")
ASSETS = os.path.join(ROOT, "assets/pets", EGG)
PREVIEW = os.path.join(ROOT, "src/client/Pets/_Preview", PET + "Data.lua")
GLOW_HEX = "d8ccff"
TAU = 2 * math.pi
os.makedirs(REVIEW, exist_ok=True)

# ---------- the file: the Dreadwing's own .blend, its game pieces copied into a collection of their own ----------
bpy.ops.wm.open_mainfile(filepath=SOURCE, load_ui=False)
scene = bpy.context.scene
pet_kit.scene = scene
pet_kit.PET, pet_kit.N = PET, N
pet_kit.OUT, pet_kit.TOOLS = ASSETS, os.path.join(ROOT, "tools/blender/pets", EGG)
for old in [c for c in bpy.data.collections if c.name == N + "Game"]:       # a previous build: rebuilt from the pieces each time
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
bpy.context.view_layer.update()                      # (the view layer still lists the removed objects until it is updated)
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)
for arm in [a for a in bpy.data.armatures if a.users == 0]:
    bpy.data.armatures.remove(arm)
GAME = bpy.data.collections.new(N + "Game")
scene.collection.children.link(GAME)
pet_kit.GAME = GAME
pet_kit.HI = GAME

PARTS = ("Body", "Head", "Tail", "WingL", "WingR")
GLOW_NAME = N + "Head_Glow_" + GLOW_HEX
RIGGED = N + "Rigged_"


def copy_piece(src, name):
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    o.data.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    GAME.objects.link(o)
    o.data.transform(src.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    o.parent = None
    for k in list(o.keys()):
        del o[k]
    return o


def gather():
    """Copies of the game pieces (the originals, in collection EclipseDreadwing, stay as they are)."""
    pieces = {part: copy_piece(bpy.data.objects[N + part], RIGGED + part) for part in PARTS}
    pieces["Glow"] = copy_piece(bpy.data.objects[GLOW_NAME], RIGGED + "Glow")
    return pieces


# ---------- the skeleton (Blender axes: faces -Y, +X its left, Z up) ----------
def mir(v, side):
    return Vector((v.x * side, v.y, v.z))


# the left wing: shoulder, elbow, wrist, hand tip: the old model's raised pose, lowered 11 degrees about the shoulder as the model was built
WING_RAW = [V(0.190, 0.010, 0.990), V(0.330, 0.130, 1.300), V(0.540, 0.120, 1.640), V(0.700, 0.520, 1.660)]
_turn = Matrix.Rotation(math.radians(11.0), 3, V(0, 1, 0))
WING = [WING_RAW[0] + _turn @ (j - WING_RAW[0]) for j in WING_RAW]

SPINE = [("Hips", V(0, 0.30, 0.790)), ("Spine", V(0, 0.12, 0.800)), ("Chest", V(0, -0.08, 0.845)), ("Neck1", V(0, -0.28, 0.955)),
         ("Neck2", V(0, -0.345, 1.065)), ("Neck3", V(0, -0.36, 1.155)), ("Head", V(0, -0.372, 1.262))]
JAW = V(0, -0.535, 1.285)          # the lower beak's hinge (checked against the beak's island)
HEAD_TIP = V(0, -0.48, 1.33)
TAIL = [("Tail1", V(0, 0.52, 0.790)), ("Tail2", V(0, 0.68, 0.680)), ("Tail3", V(0, 0.92, 0.500)), ("Tail4", V(0, 1.16, 0.320))]
TAIL_END = V(0, 1.42, 0.160)

LEGS = {
    "fore": {"top": V(0.170, -0.190, 0.820), "mid": V(0.250, -0.060, 0.570), "low": V(0.240, -0.215, 0.300), "foot": V(0.228, -0.330, 0.068)},
    "hind": {"top": V(0.190, 0.300, 0.770), "mid": V(0.255, 0.120, 0.560), "low": V(0.248, 0.470, 0.300), "foot": V(0.234, 0.335, 0.068)},
}
STRIDE = {("fore", 1): -0.055, ("hind", 1): 0.045, ("fore", -1): 0.030, ("hind", -1): -0.030}     # (the old model's walking stagger)
TOE_REACH = V(0, -0.19, -0.03)     # the foot bone points along the toes: forward, the talons reaching the ground


def leg_points(kind, side):
    L, off = LEGS[kind], STRIDE[(kind, side)]
    return (mir(L["top"], side), mir(L["mid"], side) + V(0, off * 0.5, 0), mir(L["low"], side) + V(0, off, 0), mir(L["foot"], side) + V(0, off, 0))


def leg_names(kind, side):
    tag = ("F" if kind == "fore" else "B") + ("L" if side == 1 else "R")
    return ["Leg%s1" % tag, "Leg%s2" % tag, "Leg%s3" % tag, "Foot%s" % tag]


def leg_chain(kind, side):
    top, mid, low, foot = leg_points(kind, side)
    return [top, mid, low, foot, foot + mir(TOE_REACH, 1)]


WING_GROUPS = {}       # filled from the wing's feathers (wing_groups): the roots and directions of Prim1-3 and Sec1-2


def bones_spec():
    """(name, head, tail, parent), parents before children."""
    out = [("Root", V(0, 0, 0), V(0, 0, 0.12), None)]
    heads = [h for _, h in SPINE]
    for k, (name, h) in enumerate(SPINE):
        parent = "Root" if k == 0 else SPINE[k - 1][0]
        tail = heads[k + 1] if k + 1 < len(heads) else HEAD_TIP
        out.append((name, h, tail, parent))
    out.append(("Jaw", JAW, JAW + V(0, -0.13, -0.02), "Head"))
    ph = [h for _, h in TAIL] + [TAIL_END]
    for k, (name, h) in enumerate(TAIL):
        out.append((name, h, ph[k + 1], "Hips" if k == 0 else TAIL[k - 1][0]))
    for side, tag in ((1, "L"), (-1, "R")):
        J = [mir(j, side) for j in WING]
        out.append(("Wing%s1" % tag, J[0], J[1], "Chest"))
        out.append(("Wing%s2" % tag, J[1], J[2], "Wing%s1" % tag))
        out.append(("Wing%s3" % tag, J[2], J[3], "Wing%s2" % tag))
        for k in (1, 2, 3):
            h, t = WING_GROUPS[("Prim", k, side)]
            out.append(("Prim%s%d" % (tag, k), h, t, "Wing%s3" % tag))
        for k in (1, 2):
            h, t = WING_GROUPS[("Sec", k, side)]
            out.append(("Sec%s%d" % (tag, k), h, t, "Wing%s2" % tag))
    for side in (1, -1):
        for kind in ("fore", "hind"):
            names, chain = leg_names(kind, side), leg_chain(kind, side)
            parent = "Chest" if kind == "fore" else "Hips"
            for k, name in enumerate(names):
                out.append((name, chain[k], chain[k + 1], parent))
                parent = name
    return out


def skeleton():
    bones = bones_spec()
    rig = pet_kit.armature([(n, h, p) for n, h, t, p in bones])
    pet_kit.select_only([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for n, h, t, p in bones:
        eb[n].tail = t
        eb[n].roll = 0.0
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# ---------- weights ----------
def nearest_on_polyline(P, pts):
    """Per point: the arc length along the polyline at its nearest point, and that distance."""
    P = np.asarray(P, dtype=np.float64)
    pts = np.asarray([tuple(p) for p in pts], dtype=np.float64)
    seg = pts[1:] - pts[:-1]
    ln = np.linalg.norm(seg, axis=1)
    start = np.concatenate([[0.0], np.cumsum(ln)[:-1]])
    best_d = np.full(len(P), 1e9)
    best_f = np.zeros(len(P))
    for k in range(len(seg)):
        a = pts[k]
        t = np.clip(((P - a) @ seg[k]) / (ln[k] ** 2), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * seg[k]), axis=1)
        better = d < best_d
        best_d[better] = d[better]
        best_f[better] = (start[k] + t * ln[k])[better]
    return best_f, best_d, start, ln


def chain_weights(P, pts, names, half):
    """Smooth weights along a chain of bones. pts: the polyline (the joints' heads, then the end), names: one bone per segment, half: the half
    width of the blend at each joint after the first bone. Returns one {bone: w} per point."""
    f, d, start, ln = nearest_on_polyline(P, pts)
    knots = list(start[1:len(names)])
    out = []
    for fi in f:
        w = {}
        for k, name in enumerate(names):
            lo = -1e9 if k == 0 else float(smooth(knots[k - 1] - half[k - 1], knots[k - 1] + half[k - 1], fi))
            hi = 1.0 if k == len(names) - 1 else 1.0 - float(smooth(knots[k] - half[k], knots[k] + half[k], fi))
            share = (1.0 if k == 0 else lo) * hi
            if share > 1e-4:
                w[name] = share
        out.append(w)
    return out


SPINE_PTS = [h for _, h in SPINE] + [SPINE[-1][1] + V(0, 0, 0.35)]
SPINE_NAMES = [n for n, _ in SPINE]
SPINE_HALF = [0.09, 0.09, 0.07, 0.05, 0.045, 0.04]


def spine_w(P):
    return chain_weights(P, SPINE_PTS, SPINE_NAMES, SPINE_HALF)


def tail_w(P):
    pts = [SPINE[0][1]] + [h for _, h in TAIL] + [TAIL_END]
    return chain_weights(P, pts, ["Hips"] + [n for n, _ in TAIL], [0.08, 0.10, 0.10, 0.10])


def arm_w(P, side):
    pts = [mir(j, side) for j in WING]
    tag = "L" if side == 1 else "R"
    return chain_weights(P, pts, ["Wing%s%d" % (tag, k) for k in (1, 2, 3)], [0.07, 0.06])


def leg_w(P, kind, side):
    return chain_weights(P, leg_chain(kind, side), leg_names(kind, side), [0.055, 0.05, 0.035])


def snap(w, level=0.85):
    """A rigid island's single weight vector: the one bone when it dominates, else the blend as it is."""
    top = max(w.values())
    if top >= level:
        return {max(w, key=w.get): 1.0}
    return dict(w)


def islands_of(o):
    """Connected pieces of the mesh, in the order they were built (by their lowest vertex)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a.index)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        out.append(sorted(comp))
    bm.free()
    out.sort(key=lambda c: c[0])
    return out


def root_point(P, ids, pts, share=0.25):
    """Where a feather or a plate sits on its carrier: the mean of the island's vertices nearest the carrier's polyline."""
    q = P[ids]
    _, d, _, _ = nearest_on_polyline(q, pts)
    k = max(3, int(len(ids) * share))
    near = np.argsort(d)[:k]
    return q[near].mean(0)


def wing_groups(wing):
    """The wing's islands by build order: arm loft, shoulder knuckle, web, claw, then 7 primaries, 8 secondaries, 2 tertials, 5 + 7 greater
    coverts, 8 median coverts, 12 lesser coverts, 4 marginal coverts, 12 under-coverts (the old script's wing_feathers). Returns the island
    ids in groups, each with its vertices' indices."""
    isl = islands_of(wing)
    assert len(isl) == 69, "the wing is no longer 69 islands: %d" % len(isl)
    assert [len(c) for c in isl[:4]] == [72, 42, 12, 17], [len(c) for c in isl[:4]]
    sizes = [len(c) for c in isl[4:]]
    assert sizes == [33] * 7 + [33] * 8 + [33] * 2 + [21] * 12 + [21] * 8 + [13] * 16 + [21] * 12, sizes
    return isl


# the flight feathers' groups: primary index 0-6 inner to outer, secondary 0-7 elbow to wrist (by the feathers' own roots along the bones)
PRIM_OF = [1, 1, 1, 2, 2, 3, 3]
SEC_OF = [1, 1, 1, 1, 2, 2, 2, 2]
# the other feathers' carrier (0 humerus, 1 forearm, 2 hand), by the old script's own build order and rules (wing_feathers): tertials 2 (humerus),
# greater coverts 5 (hand) + 7 (forearm), median coverts 8 (segments by their place: f < 0.30 humerus, < 0.75 forearm, else hand), lesser coverts
# 12 (f < 0.4 humerus), marginal coverts 4 (hand), under-coverts 12 (f < 0.35 humerus)
COVERT_SEG = ([0, 0] + [2] * 5 + [1] * 7 + [0, 0, 0, 1, 1, 1, 2, 2] + [0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1] + [2] * 4 + [0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1])
assert len(COVERT_SEG) == 50


def group_geometry(P, island_ids, arm_pts):
    """(head, tail) of a bone carrying these feathers: their mean root, and along their mean direction."""
    roots, dirs = [], []
    for ids in island_ids:
        r = root_point(P, ids, arm_pts, 0.2)
        roots.append(r)
        c = P[ids].mean(0)
        dirs.append(Vector(c - r).normalized())
    head = Vector(np.mean(roots, axis=0))
    d = sum(dirs, Vector((0, 0, 0))).normalized()
    return head, head + d * 0.22


def prepare_wing_groups():
    """The Prim/Sec bones' heads and tails come from the feathers themselves (both wings, mirrored from the left one so the rig is symmetric)."""
    left = bpy.data.objects[N + "WingL"]
    P = pet_kit.verts(left)
    isl = wing_groups(left)
    arm_pts = list(WING)
    prims = isl[4:11]
    secs = isl[11:19]
    for k in (1, 2, 3):
        ids = [prims[i] for i in range(7) if PRIM_OF[i] == k]
        h, t = group_geometry(P, ids, arm_pts)
        WING_GROUPS[("Prim", k, 1)] = (h, t)
        WING_GROUPS[("Prim", k, -1)] = (mir(h, -1), mir(t, -1))
    for k in (1, 2):
        ids = [secs[i] for i in range(8) if SEC_OF[i] == k]
        h, t = group_geometry(P, ids, arm_pts)
        WING_GROUPS[("Sec", k, 1)] = (h, t)
        WING_GROUPS[("Sec", k, -1)] = (mir(h, -1), mir(t, -1))


def weights_wing(piece, side):
    """Per vertex {bone: w} for a wing piece."""
    tag = "L" if side == 1 else "R"
    P = pet_kit.verts(piece)
    isl = wing_groups(piece)
    arm = [mir(j, side) for j in WING]
    W = [None] * len(P)
    names = ["Wing%s%d" % (tag, k) for k in (1, 2, 3)]
    # arm loft and web: smooth along the arm; knuckle: rigid on the shoulder; claw: rigid on the hand
    smooth_w = arm_w(P, side)
    for i in isl[0] + isl[2]:
        W[i] = smooth_w[i]
    for i in isl[1]:
        W[i] = {names[0]: 1.0}
    for i in isl[3]:
        W[i] = {names[2]: 1.0}
    feathers = isl[4:]
    for n, ids in enumerate(feathers):
        if n < 7:
            w = {"Prim%s%d" % (tag, PRIM_OF[n]): 1.0}
        elif n < 15:
            w = {"Sec%s%d" % (tag, SEC_OF[n - 7]): 1.0}
        else:
            seg = COVERT_SEG[n - 15]
            w = {names[seg]: 1.0}
        for i in ids:
            W[i] = w
    return W


def weights_body(piece):
    P = pet_kit.verts(piece)
    isl = islands_of(piece)
    W = [None] * len(P)
    assert len(isl[0]) == 178, "the trunk is no longer the first island"
    for i, w in zip(isl[0], spine_w(P[isl[0]])):         # the trunk and neck loft: smooth along the spine
        W[i] = w
    starts = [i for i, c in enumerate(isl) if i > 0 and len(c) in (42, 52)]
    assert [len(isl[i]) for i in starts] == [42, 52, 42, 52], [len(isl[i]) for i in starts]
    last = max(i for i, c in enumerate(isl) if len(c) == 16)           # the lowest scute of the last leg ends the legs' islands
    ends = starts[1:] + [last + 1]
    legs = [(1, "fore"), (1, "hind"), (-1, "fore"), (-1, "hind")]
    for (side, kind), a, b in zip(legs, starts, ends):
        chunk = isl[a:b]
        assert [len(c) for c in chunk[:12]] == [len(isl[a]), 34, 34, 23] + [27, 22] * 4, [len(c) for c in chunk[:12]]
        names, chain = leg_names(kind, side), leg_chain(kind, side)
        for c in chunk:
            d = np.linalg.norm(P[c].mean(0) - np.array(tuple(chain[1])))
            assert nearest_on_polyline(P[c].mean(0)[None], chain)[1][0] < 0.22, ("an island far from its leg", side, kind)
        for c in chunk[:4]:                              # the leg's tubes and its scale band: smooth along the leg
            for i, w in zip(c, leg_w(P[c], kind, side)):
                W[i] = w
        for c in chunk[4:12]:                            # toes and talons: the foot
            for i in c:
                W[i] = {names[3]: 1.0}
        for c in chunk[12:]:                             # scutes and the thigh's shards: rigid on the leg bone they sit on
            r = root_point(P, c, chain, 0.3)
            w = snap(leg_w(r[None], kind, side)[0], 0.7)
            for i in c:
                W[i] = w
    for c in isl[last + 1:]:                             # the body's own feathers and plates: rigid on the spine bone at their root
        r = root_point(P, c, SPINE_PTS[:-1], 0.3)
        w = snap(spine_w(r[None])[0], 0.7)
        for i in c:
            W[i] = w
    assert all(w is not None for w in W)
    return W


def weights_head(piece):
    P = pet_kit.verts(piece)
    isl = islands_of(piece)
    assert len(isl) == 62 and [len(c) for c in isl[:3]] == [164, 50, 34], [len(c) for c in isl[:3]]
    W = [None] * len(P)
    for i, w in zip(isl[0], spine_w(P[isl[0]])):         # the skull: its collar rides the neck's top as the trunk's does there
        W[i] = w
    for i in isl[1]:
        W[i] = {"Head": 1.0}
    for i in isl[2]:                                     # the lower beak: its own island, on the jaw
        W[i] = {"Jaw": 1.0}
    for c in isl[3:]:
        r = root_point(P, c, SPINE_PTS[:-1], 0.3)
        w = snap(spine_w(r[None])[0], 0.7)
        for i in c:
            W[i] = w
    assert all(w is not None for w in W)
    return W


def weights_tail(piece):
    P = pet_kit.verts(piece)
    isl = islands_of(piece)
    assert len(isl) == 49 and len(isl[0]) == 74, (len(isl), len(isl[0]))
    pts = [SPINE[0][1]] + [h for _, h in TAIL] + [TAIL_END]
    W = [None] * len(P)
    for i, w in zip(isl[0], tail_w(P[isl[0]])):
        W[i] = w
    for c in isl[1:]:
        r = root_point(P, c, pts, 0.3)
        w = snap(tail_w(r[None])[0], 0.7)
        for i in c:
            W[i] = w
    assert all(w is not None for w in W)
    return W


def bind_all(pieces, rig):
    weigh = pet_kit.weigh
    weigh(pieces["Body"], weights_body(pieces["Body"]))
    weigh(pieces["Head"], weights_head(pieces["Head"]))
    weigh(pieces["Tail"], weights_tail(pieces["Tail"]))
    weigh(pieces["WingL"], weights_wing(pieces["WingL"], 1))
    weigh(pieces["WingR"], weights_wing(pieces["WingR"], -1))
    pet_kit.rigid(pieces["Glow"], "Head")
    pet_kit.bind(rig, list(pieces.values()))


def tris_of(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def report_weights(pieces, rig):
    total = 0
    used = collections.Counter()
    for key, o in pieces.items():
        counts = [len(v.groups) for v in o.data.vertices]
        unweighted = sum(1 for v in o.data.vertices if not v.groups or sum(g.weight for g in v.groups) < 0.99)
        names = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight > 0.5:
                    used[names[g.group]] += 1
        total += tris_of(o)
        print("PIECE", key, "verts", len(o.data.vertices), "tris", tris_of(o), "groups", len(o.vertex_groups), "max influences", max(counts), "unweighted", unweighted, flush=True)
    print("TRIS total", total, flush=True)
    unused = [b.name for b in rig.data.bones if b.name != "Root" and used[b.name] == 0]
    print("BONES", len(rig.data.bones), "bones with no vertex over half weight:", unused, flush=True)
    print("VERTS per bone (weight > 0.5):", dict(sorted(used.items())), flush=True)



# ---------- poses: in the game's axes (x pitch about its right, y yaw about up, z roll about its long axis), degrees ----------
# The game maps Blender's (x, y, z) to its own (-x, z, y), a proper rotation, so a turn of t about a game axis is the turn of t about the same
# axis seen from Blender: game X = Blender -X, game Y = Blender Z, game Z = Blender Y. Positive x lifts the nose and lowers the tail.
MAP = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))


def game_rotation(rx, ry, rz):
    rg = Matrix.Rotation(rx, 3, "X") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rz, 3, "Z")
    return MAP @ rg @ MAP


def pose_reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)


def apply(rig, spec):
    """spec: bone: (rx, ry, rz) degrees in game axes (optionally a fourth item, a move (x, y, z) in game metres)."""
    pose_reset(rig)
    for name, v in spec.items():
        pb = rig.pose.bones[name]
        B = pb.bone.matrix_local.to_3x3()
        R = game_rotation(*(math.radians(a) for a in v[:3]))
        pb.rotation_quaternion = (B.inverted() @ R @ B).to_quaternion()
        if len(v) > 3:
            pb.location = B.inverted() @ Vector((-v[3][0], v[3][2], v[3][1]))
    bpy.context.view_layer.update()


def twin(name):
    """The other side's bone: the L in WingL1, LegFL1, FootFL becomes an R."""
    for k in (-1, -2):
        i = len(name) + k
        if name[i] == "L" and (k == -1 or name[-1].isdigit()):
            return name[:i] + "R" + name[i + 1:]
    return name


def mirror_spec(spec):
    """The right side's twin of a left-side spec (yaw and roll change sign)."""
    return {twin(name): (v[0], -v[1], -v[2]) + tuple(v[3:]) for name, v in spec.items()}


def both(spec):
    return {**spec, **mirror_spec(spec)}


def aim(rig, name, target):
    """Turns the bone about its head so it points along `target` (Blender axes), whatever its parents have done."""
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(target).normalized())
    m = pb.matrix.copy()
    new = Matrix.Translation(pb.head) @ (q.to_matrix() @ m.to_3x3()).to_4x4()
    pb.matrix = new
    bpy.context.view_layer.update()


def posed(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


class Checker:
    """A pose against the rest pose: how far any edge stretches (a tear), how many collapse (a crush), and how much more of one piece cuts
    through another than at rest (a feather through the body or the other wing, a leg through another leg, a head into the trunk)."""
    PAIRS = (("WingL", "WingR"), ("WingL", "Tail"), ("WingR", "Tail"), ("WingL", "Head"), ("WingR", "Head"), ("Tail", "LegBL"), ("Tail", "LegBR"),
             ("LegFL", "LegFR"), ("LegBL", "LegBR"), ("LegFL", "LegBL"), ("LegFR", "LegBR"), ("LegFL", "Tail"), ("LegBL", "WingL"), ("LegBR", "WingR"))

    def __init__(self, pieces, rig):
        self.pieces, self.rig = pieces, rig
        self.edges, self.len0, self.tris = {}, {}, {}
        apply(self.rig, {})
        for key, o in pieces.items():
            me = o.data
            e = np.empty(len(me.edges) * 2, dtype=np.int64)
            me.edges.foreach_get("vertices", e)
            e = e.reshape(-1, 2)
            co = posed(o)
            self.edges[key] = e
            self.len0[key] = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1) + 1e-9
            me.calc_loop_triangles()
            self.tris[key] = [tuple(lt.vertices) for lt in me.loop_triangles]
        isl = islands_of(pieces["Body"])
        trunk = set(isl[0])
        self.trunk_tris = [t for t in self.tris["Body"] if all(i in trunk for i in t)]
        starts = [i for i, c in enumerate(isl) if i > 0 and len(c) in (42, 52)]
        self.leg_ids = {}
        for (side, kind), a in zip([(1, "fore"), (1, "hind"), (-1, "fore"), (-1, "hind")], starts):
            tag = ("F" if kind == "fore" else "B") + ("L" if side == 1 else "R")
            self.leg_ids[tag] = set(i for c in isl[a:a + 12] for i in c)
        self.leg_tris = {tag: [t for t in self.tris["Body"] if all(i in ids for i in t)] for tag, ids in self.leg_ids.items()}
        self.rest = self.measure()

    def measure(self):
        co = {k: posed(o) for k, o in self.pieces.items() if k != "Glow"}
        out = {"tear": 0.0, "n_tear": 0, "crush": 0}
        where = ""
        for k, c in co.items():
            e = self.edges[k]
            now = np.linalg.norm(c[e[:, 0]] - c[e[:, 1]], axis=1)
            gain = now - self.len0[k]
            j = int(np.argmax(gain))
            if gain[j] > out["tear"]:
                out["tear"], where = float(gain[j]), k
            out["n_tear"] += int((gain > 0.06).sum())
            out["crush"] += int((now / self.len0[k] < 0.25).sum())
        out["tear_in"] = where
        trees = {k: BVHTree.FromPolygons([tuple(p) for p in c], self.tris[k], epsilon=0.0) for k, c in co.items() if k != "Body"}
        for tag, t in self.leg_tris.items():
            trees["Leg" + tag] = BVHTree.FromPolygons([tuple(p) for p in co["Body"]], t, epsilon=0.0)
        for a, b in self.PAIRS:
            out["x_" + a + "_" + b] = len(trees[a].overlap(trees[b]))
        trunk = BVHTree.FromPolygons([tuple(p) for p in co["Body"]], self.trunk_tris, epsilon=0.0)
        subjects = {"WingL": co["WingL"], "WingR": co["WingR"], "Head": co["Head"], "Tail": co["Tail"]}
        for tag, ids in self.leg_ids.items():
            subjects["Leg" + tag] = co["Body"][sorted(ids)]
        for k, pts in subjects.items():                          # vertices deeper than 3 cm inside the trunk's own skin
            n = 0
            for p in pts:
                loc, nrm, _, dist = trunk.find_nearest(Vector(p))
                if loc is not None and dist > 0.03 and (Vector(p) - loc).dot(nrm) < 0:
                    n += 1
            out["in_" + k] = n
        return out

    def run(self):
        return self.measure()

    def worse(self, r, only=None):
        """What got clearly worse than at rest, as {key: amount}; empty if it is clean. (Layered feathers always cut into each other a little:
        only what grows a lot counts here, and the limits are then looked at in renders.) only: the piece names a bone's turn is judged by."""
        bad = {}
        if only:
            bad = {k: v for k, v in self.worse(r).items() if k == "tear cm" or k == "crush" or any(t in k for t in only)}
            return bad
        if r["tear"] > self.rest["tear"] + 0.07:
            bad["tear cm"] = round(r["tear"] * 100, 1)
        if r["crush"] > self.rest["crush"]:
            bad["crush"] = r["crush"] - self.rest["crush"]
        for a, b in self.PAIRS:
            k = "x_" + a + "_" + b
            if r[k] > self.rest[k] + 40:
                bad[k[2:]] = r[k] - self.rest[k]
        for k in r:
            if k.startswith("in_"):
                slack = 30 if k.startswith("in_Leg") or k in ("in_Tail", "in_Head") else 25
                if r[k] > self.rest[k] + slack:
                    bad[k] = r[k] - self.rest[k]
        return bad


# ---------- review renders (Workbench, the baked maps as colour) ----------
VIEWS = {"front": (V(0, -1, 0.08), V(0, 0.2, 0.85)), "side": (V(1, 0, 0.06), V(0, 0.3, 0.85)), "back": (V(0, 1, 0.12), V(0, 0.2, 0.85)),
         "three": (V(0.72, -0.62, 0.30), V(0, 0.2, 0.85)), "top": (V(0, 0.02, 1), V(0, 0.3, 0.8)), "threeR": (V(-0.72, -0.62, 0.30), V(0, 0.2, 0.85))}
REVIEW_OBJS = []


def review_setup(size=560):
    sc = bpy.context.scene
    for lc in bpy.context.view_layer.layer_collection.children:      # only the rigged Dreadwing is seen and rendered
        lc.exclude = lc.name != GAME.name
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type, sh.show_cavity, sh.show_shadows = "STUDIO", "TEXTURE", False, False
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("RigReview")
    w.color = (0.35, 0.35, 0.38)
    sc.world = w
    cam = bpy.data.objects.new("RigCam", bpy.data.cameras.new("RigCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.clip_start, cam.data.clip_end = 0.01, 100
    REVIEW_OBJS.extend([cam, w])
    return cam


def shoot(cam, path, view, scale=2.5, target=None):
    d, t = VIEWS[view]
    t = target if target is not None else t
    cam.location = t + d.normalized() * 10
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_px(path):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"            # (no conversion: the sheet carries the renders' own values)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def save_px(path, px):
    h, w = px.shape[:2]
    img = bpy.data.images.new("sheet_out", w, h, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.ascontiguousarray(px, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def sheet(paths, out, cols, tile=420):
    rows = (len(paths) + cols - 1) // cols
    canvas = np.zeros((rows * tile, cols * tile, 4), dtype=np.float32)
    canvas[..., :3], canvas[..., 3] = 0.30, 1
    for k, p in enumerate(paths):
        px = load_px(p)
        h, w = px.shape[:2]
        ys, xs = (np.arange(tile) * h / tile).astype(int), (np.arange(tile) * w / tile).astype(int)
        r, c = rows - 1 - k // cols, k % cols
        t = px[np.ix_(ys, xs)].copy()
        a = t[..., 3:4]
        t[..., :3] = t[..., :3] * a + 0.30 * (1 - a)          # (the render's film is transparent: laid over the sheet's grey)
        t[..., 3] = 1
        canvas[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile] = t
        canvas[r * tile:(r + 1) * tile, c * tile:c * tile + 2, :3] = 0.1
        canvas[r * tile:r * tile + 2, c * tile:(c + 1) * tile, :3] = 0.1
    save_px(out, canvas)
    return out


TMP = os.path.join(REVIEW, "_tmp")


def multi_sheet(cam, rig, name, specs, views=("front", "side", "three"), scale=2.6, tile=360):
    """One row per pose, one column per view."""
    os.makedirs(TMP, exist_ok=True)
    paths = []
    for k, (label, spec) in enumerate(specs):
        spec(rig) if callable(spec) else apply(rig, spec)
        for v in views:
            paths.append(shoot(cam, os.path.join(TMP, "%s_%d_%s.png" % (name, k, v)), v, scale))
    out = sheet(paths, os.path.join(REVIEW, name + ".png"), len(views), tile)
    for p in paths:
        os.remove(p)
    apply(rig, {})
    return out


def pose_sheet(cam, rig, name, spec, views=("front", "side", "three", "top"), scale=2.6, tile=420, size=None):
    os.makedirs(TMP, exist_ok=True)
    apply(rig, spec) if not callable(spec) else spec(rig)
    paths = [shoot(cam, os.path.join(TMP, "%s_%s.png" % (name, v)), v, scale) for v in views]
    out = sheet(paths, os.path.join(REVIEW, name + ".png"), len(views), tile)
    for p in paths:
        os.remove(p)
    return out


def judged_by(name):
    """The pieces a bone's turn is judged against (the others are driven by other bones: a spine bending drags the feet round, and that is
    the animation's to avoid, not the skin's)."""
    if name.startswith("Leg") or name.startswith("Foot"):
        return ("Leg" + name[3:5] if name.startswith("Leg") else "Leg" + name[4:6],)
    if name.startswith(("Wing", "Prim", "Sec")):
        return ("Wing" + name[-2] if name[-2] in "LR" else "Wing" + name[4:5],)
    if name.startswith("Tail"):
        return ("Tail",)
    if name in ("Head", "Jaw"):
        return ("Head",)
    return ("Wing", "Head")        # the trunk and neck carry the wings and the head


def sweep(chk, rig, bones, step=6.0, top=96.0):
    """For each bone and each axis, both ways: the largest turn (to `top`, in `step`s) that stays clean. {bone: {axis: (neg, pos)}} in degrees."""
    out = {}
    why = sweep.why = {}
    for name in bones:
        out[name] = {}
        for ax in range(3):
            lim = []
            for sign in (-1, 1):
                good = 0.0
                a = step
                while a <= top:
                    v = [0.0, 0.0, 0.0]
                    v[ax] = sign * a
                    apply(rig, {name: tuple(v)})
                    bad = chk.worse(chk.run(), judged_by(name))
                    if bad:
                        why[(name, "xyz"[ax], sign)] = bad
                        break
                    good = a
                    a += step
                lim.append(sign * good)
            out[name]["xyz"[ax]] = tuple(lim)
        print("LIMITS", name, {k: v for k, v in out[name].items()}, flush=True)
    apply(rig, {})
    return out



# ---------- the pose library (every one checked against the rest pose; the renders are the proof) ----------
def neck(p=0.0, y=0.0, r=0.0, k=(0.15, 0.25, 0.25, 0.35)):
    return {n: (p * w, y * w, r * w) for n, w in zip(("Neck1", "Neck2", "Neck3", "Head"), k)}


def tail(y=0.0, p=0.0, k=(0.15, 0.25, 0.3, 0.3)):
    return {n: (p * w, y * w, 0) for n, w in zip(("Tail1", "Tail2", "Tail3", "Tail4"), k)}


FORE_TUCK = {"LegFL1": (-28, 0, 0), "LegFL2": (-25, 0, 0), "LegFL3": (-60, 0, 0), "FootFL": (30, 0, 0)}
HIND_TUCK = {"LegBL1": (-60, 0, 0), "LegBL2": (-25, 0, 0), "LegBL3": (30, 0, 0), "FootBL": (30, 0, 0)}
FORE_FWD = {"LegFL1": (50, 0, 0), "LegFL2": (30, 0, 0), "LegFL3": (30, 0, 0), "FootFL": (-30, 0, 0)}
HIND_FWD = {"LegBL1": (28, 0, 0), "LegBL2": (15, 0, 0), "LegBL3": (-40, 0, 0), "FootBL": (-30, 0, 0)}

POSES = {
    "WingsUp": both({"WingL1": (0, 0, -35)}),
    "WingsMid": both({"WingL1": (0, 0, 30)}),
    "WingsDown70": both({"WingL1": (0, 0, 70)}),
    "WingsDownFlex": both({"WingL1": (0, 0, 72), "WingL2": (0, 20, 0), "WingL3": (0, 14, 0)}),
    "WingsFolded": both({"WingL1": (-10, 25, 92), "WingL2": (-30, 12, 0), "WingL3": (-30, 8, 0)}),
    "ElbowWristFold": both({"WingL1": (0, 0, 22), "WingL2": (0, 34, 0), "WingL3": (0, 20, 0)}),
    "WingsSpread": both({"WingL1": (0, 0, 28), "WingL2": (0, -38, 0), "WingL3": (0, -22, 0)}),
    "PrimariesFanned": both({"WingL1": (0, 0, 28), "WingL2": (0, -30, 0), "WingL3": (0, -15, 0), "PrimL1": (0, 12, 0), "PrimL2": (0, -4, 0),
                             "PrimL3": (0, -22, 0), "SecL1": (0, 8, 0), "SecL2": (0, -12, 0)}),
    "PrimariesClosed": both({"WingL1": (0, 0, 28), "PrimL1": (0, -10, 0), "PrimL2": (0, 2, 0), "PrimL3": (0, 14, 0), "SecL1": (0, -6, 0), "SecL2": (0, 8, 0)}),
    "NeckUp": neck(60), "NeckDown": neck(-55), "NeckLeft": neck(0, 70), "NeckRight": neck(0, -70), "NeckTilt": neck(0, 0, 40),
    "NeckLunge": {"Neck1": (-22, 0, 0), "Neck2": (-14, 0, 0), "Neck3": (24, 0, 0), "Head": (38, 0, 0), "Spine": (-10, 0, 0)},
    "NeckHigh": {"Neck1": (12, 0, 0), "Neck2": (-18, 0, 0), "Neck3": (-12, 0, 0), "Head": (30, 0, 0)},
    "TailLeft": tail(y=80), "TailRight": tail(y=-80), "TailUp": tail(p=-50), "TailDown": tail(p=50),
    "TailCurl": {"Tail1": (0, 40, 0), "Tail2": (0, 45, 0), "Tail3": (0, 50, 0), "Tail4": (0, 55, 0)},
    "JawOpen": {"Jaw": (-40, 0, 0)},
    "LegsTuckedBack": {**FORE_TUCK, **mirror_spec(FORE_TUCK), **HIND_TUCK, **mirror_spec(HIND_TUCK)},
    "LegsForward": {**FORE_FWD, **mirror_spec(FORE_FWD), **HIND_FWD, **mirror_spec(HIND_FWD)},
    "LegsDangle": {**{"LegFL1": (22, 0, 0), "LegFL2": (12, 0, 0), "LegFL3": (-10, 0, 0), "LegBL1": (-18, 0, 0), "LegBL2": (8, 0, 0), "LegBL3": (14, 0, 0)},
                   **mirror_spec({"LegFL1": (22, 0, 0), "LegFL2": (12, 0, 0), "LegFL3": (-10, 0, 0), "LegBL1": (-18, 0, 0), "LegBL2": (8, 0, 0), "LegBL3": (14, 0, 0)})},
    "Hover": {**both({"WingL1": (0, 0, 34), "WingL2": (0, 10, 0)}), **neck(8), **tail(p=-10), **both({"LegFL1": (20, 0, 0), "LegFL2": (20, 0, 0), "LegBL1": (-20, 0, 0)}),
              "Hips": (-6, 0, 0, (0, 0.25, 0))},
    "Glide": {**both({"WingL1": (0, 0, 18), "WingL2": (0, -38, 0), "WingL3": (0, -22, 0), "PrimL3": (0, -12, 0), "LegFL1": (-28, 0, 0), "LegFL2": (-25, 0, 0),
                      "LegFL3": (-60, 0, 0), "FootFL": (30, 0, 0), "LegBL1": (-60, 0, 0), "LegBL2": (-25, 0, 0), "LegBL3": (30, 0, 0), "FootBL": (30, 0, 0)}),
              **neck(-12), **tail(p=-8)},
    "Roar": {**both({"WingL1": (0, 0, -10), "WingL2": (0, -20, 0)}), **neck(40), "Jaw": (-45, 0, 0), "Spine": (14, 0, 0), "Chest": (12, 0, 0), **tail(p=15)},
}


def run_poses(chk, rig):
    out = {}
    for name, spec in POSES.items():
        spec(rig) if callable(spec) else apply(rig, spec)
        r = chk.run()
        out[name] = chk.worse(r)
        print("POSE", name, out[name] or "clean", "tear cm", round(r["tear"] * 100, 1), flush=True)
    apply(rig, {})
    return out


# ---------- the safe ranges ----------
def design_caps(name):
    """What the moving parts can be asked for (degrees, game axes): the Checker sees tears and crushes, not what looks absurd, so the rigid-island
    chains (feathers, tail, jaw, foot) are capped by what their renders held up to."""
    full = {"x": (-90, 90), "y": (-90, 90), "z": (-90, 90)}
    if name == "Hips":
        return {"x": (-45, 45), "y": (-60, 60), "z": (-35, 35)}
    if name == "Jaw":
        return {"x": (-50, 6), "y": (-10, 10), "z": (-10, 10)}
    if name.startswith("Tail") and name != "Tail1":
        return {"x": (-60, 60), "y": (-60, 60), "z": (-45, 45)}
    if name.startswith(("Prim", "Sec")):
        return {"x": (-30, 30), "y": (-40, 40), "z": (-30, 30)}
    if name.startswith("Wing") and name[-1] in "23":
        return {"x": (-60, 60), "y": (-60, 75), "z": (-60, 60)}
    if name.startswith("Foot"):
        return {"x": (-45, 45), "y": (-30, 30), "z": (-30, 30)}
    if name.startswith("Leg") and name[-1] == "3":              # (the lowest shin spins freely without a tear: kept to what a leg does)
        return {"x": (-66, 66), "y": (-60, 60), "z": (-60, 60)}
    return full


def final_limits(raw):
    out = {}
    for name, ax in raw.items():
        cap = design_caps(name)
        out[name] = {a: (max(ax[a][0], cap[a][0]), min(ax[a][1], cap[a][1])) for a in "xyz"}
    return out


def limit_sheets(cam, rig, limits):
    """Each bone at the edge of its range, both ways on each axis (the left side's: the right's are their mirror images): a row a bone, a column
    an end (x-, x+, y-, y+, z-, z+)."""
    groups = {"torso_neck": ["Hips", "Spine", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw"], "wing": ["WingL1", "WingL2", "WingL3", "PrimL1", "PrimL3", "SecL1", "SecL2"],
              "legs": ["LegFL1", "LegFL2", "LegFL3", "FootFL", "LegBL1", "LegBL2", "LegBL3", "FootBL"], "tail": ["Tail1", "Tail2", "Tail3", "Tail4"]}
    view = {"wing": "three", "tail": "three", "legs": "side", "torso_neck": "side"}
    os.makedirs(TMP, exist_ok=True)
    for gname, bones in groups.items():
        paths = []
        for b in bones:
            for ax in "xyz":
                for v in limits[b][ax]:
                    spec = [0.0, 0.0, 0.0]
                    spec["xyz".index(ax)] = v
                    apply(rig, {b: tuple(spec)})
                    paths.append(shoot(cam, os.path.join(TMP, "lim_%s_%s_%s%+d.png" % (gname, b, ax, v)), view[gname], 2.6))
        sheet(paths, os.path.join(REVIEW, "limits_%s.png" % gname), 6, 250)
        for p in paths:
            os.remove(p)
    apply(rig, {})


def rest_match(cam, pieces):
    """The rigged pieces at rest against the old model's, pixel for pixel, from four views."""
    old = bpy.data.collections[PET]
    hidden = []
    for o in old.objects:
        if "Pivot_" in o.name or "Point_" in o.name:
            hidden.append((o, o.hide_render))
            o.hide_render = True
    lc = bpy.context.view_layer.layer_collection.children
    worst = 0.0
    pairs = {"old": [], "new": []}
    for view in ("front", "side", "three", "top", "back"):
        imgs = []
        for which in ("old", "new"):
            for c in lc:
                c.exclude = c.name != (PET if which == "old" else GAME.name)
            shoot(cam, os.path.join(TMP, "m_%s_%s.png" % (which, view)), view, 2.6)
            imgs.append(load_px(os.path.join(TMP, "m_%s_%s.png" % (which, view))))
            pairs[which].append(os.path.join(TMP, "m_%s_%s.png" % (which, view)))
        d = np.abs(imgs[0][..., :3] - imgs[1][..., :3]).max(axis=2)
        n = int((d > 0.02).sum())
        print("REST MATCH", view, "pixels differing more than 2%:", n, "of", d.size, "max", round(float(d.max()), 3), flush=True)
        worst = max(worst, n)
    sheet(pairs["old"] + pairs["new"], os.path.join(REVIEW, "01_rest_old_over_new.png"), 5, 330)
    for c in lc:
        c.exclude = c.name != GAME.name
    for o, h in hidden:
        o.hide_render = h
    return worst


def weight_views(cam, rig, pieces):
    """Each chosen bone's weights painted on the pieces (blue none, red all), from the three-quarter view: one tile a bone."""
    bones = ["Spine", "Chest", "Neck2", "Head", "Jaw", "WingL1", "WingL2", "WingL3", "PrimL3", "SecL1", "Tail2", "LegFL2", "LegBL1", "LegBL2", "FootBL", "Hips"]
    sh = bpy.context.scene.display.shading
    sh.color_type = "VERTEX"
    apply(rig, {})
    paths = []
    for b in bones:
        for o in pieces.values():
            me = o.data
            att = me.color_attributes.get("wv") or me.color_attributes.new("wv", "FLOAT_COLOR", "POINT")
            gi = {g.name: g.index for g in o.vertex_groups}
            w = np.zeros(len(me.vertices))
            if b in gi:
                for v in me.vertices:
                    for g in v.groups:
                        if g.group == gi[b]:
                            w[v.index] = g.weight
            t = w[:, None]
            col = np.concatenate([t, 0.15 * (1 - np.abs(2 * t - 1)), 1 - t, np.ones_like(t)], axis=1)
            att.data.foreach_set("color", col.ravel())
            me.color_attributes.active_color = att
        paths.append(shoot(cam, os.path.join(TMP, "w_%s.png" % b), "three", 2.6))
    sheet(paths, os.path.join(REVIEW, "70_weights.png"), 4, 330)
    for p in paths:
        os.remove(p)
    sh.color_type = "TEXTURE"


# ---------- the game's files: FBX, preview data, .blend ----------
def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii")


def sample_colours(o, part):
    """The baked colour map at each vertex's UV (the average over its corners), as 8-bit sRGB: the map's own values, never converted."""
    img = bpy.data.images.load(os.path.join(ASSETS, "%s_%s_color.png" % (PET, part)), check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    bpy.data.images.remove(img)
    me = o.data
    loops = len(me.loops)
    uv = np.empty(loops * 2, dtype=np.float32)
    me.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    vi = np.empty(loops, dtype=np.int64)
    me.loops.foreach_get("vertex_index", vi)
    ix = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    iy = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)
    c = px[iy, ix, :3]
    acc = np.zeros((len(me.vertices), 3))
    cnt = np.zeros(len(me.vertices))
    np.add.at(acc, vi, c)
    np.add.at(cnt, vi, 1)
    return np.clip(np.round(acc / np.maximum(cnt, 1)[:, None] * 255), 0, 255).astype(np.uint8)


def piece_data(o, bones, colour):
    me = o.data
    me.calc_loop_triangles()
    P = pet_kit.verts(o)
    G = np.stack([-P[:, 0], P[:, 2], P[:, 1]], axis=1).astype("<f4")             # Blender (x, y, z) -> the game's (-x, z, y)
    T = np.array([lt.vertices[:] for lt in me.loop_triangles], dtype="<u4")
    names = {g.index: g.name for g in o.vertex_groups}
    index = {b: k for k, b in enumerate(bones)}
    bi = np.zeros((len(P), 4), dtype=np.uint8)
    wt = np.zeros((len(P), 4), dtype=np.float64)
    for v in me.vertices:
        gs = sorted(((g.weight, index[names[g.group]]) for g in v.groups), reverse=True)[:4]
        tot = sum(w for w, _ in gs)
        for j, (w, b) in enumerate(gs):
            bi[v.index, j] = b
            wt[v.index, j] = w / tot
    q = np.round(wt * 255).astype(int)
    for k in range(len(P)):                                                      # the remainder to the largest share, so each vertex sums to 255
        q[k, 0] += 255 - q[k].sum()
    assert q.min() >= 0 and (q.sum(axis=1) == 255).all()
    col = colour if isinstance(colour, np.ndarray) else np.tile(np.array(colour, dtype=np.uint8), (len(P), 1))
    # (the mapping is a proper rotation, so a triangle wound outward in Blender is wound outward in the game's right-handed space)
    vol = float(np.einsum("ij,ij->i", G[T[:, 0]].astype(float), np.cross(G[T[:, 1]].astype(float) - G[T[:, 0]], G[T[:, 2]].astype(float) - G[T[:, 0]])).sum() / 6)
    return {"Verts": G, "Tris": T, "Cols": col, "BoneIdx": bi, "Wts": q.astype(np.uint8), "volume": vol}


def write_preview(pieces, rig):
    bones = [b[0] for b in bones_spec()]
    heads = {n: h for n, h, t, p in bones_spec()}
    parents = {n: p for n, h, t, p in bones_spec()}
    lines = ["-- Written by tools/blender/pets/eclipse_dreadwing_rig.py. Temporary, for looking at the skinned Dreadwing in Studio before it is imported: never committed.",
             "-- Bones: { name, parent, x, y, z } rest head positions in the game's axes (metres, ground at y = 0); pieces: float32 xyz, uint32 triples, uint8 rgb per",
             "-- vertex, four uint8 bone indices and four uint8 weights per vertex (sum 255), all little-endian, base64. Triangles are wound outward in the game's space.",
             "return {", '    Pet = "%s",' % PET, "    Bones = {"]
    for n in bones:
        h = heads[n]
        lines.append('        { "%s", "%s", %.5f, %.5f, %.5f },' % (n, parents[n] or "", -h.x, h.z, h.y))
    lines.append("    },")
    lines.append("    Pieces = {")
    check = {}
    for key in ("Body", "Head", "Tail", "WingL", "WingR", "Glow"):
        o = pieces[key]
        colour = (216, 204, 255) if key == "Glow" else sample_colours(o, key)
        d = piece_data(o, bones, colour)
        name = GLOW_NAME if key == "Glow" else N + key
        check[name] = (len(o.data.vertices), len(d["Tris"]), d)
        lines.append("        {")
        lines.append('            Name = "%s",' % name)
        if key == "Glow":
            lines.append('            Glow = "%s",' % GLOW_HEX)
        for field in ("Verts", "Tris", "Cols", "BoneIdx", "Wts"):
            lines.append("            %s = [==[%s]==]," % (field, b64(d[field])))
        lines.append("        },")
    lines.append("    },")
    lines.append("}")
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    with open(PREVIEW, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # the check: decode what was written and compare counts
    text = open(PREVIEW).read()
    for name, (nv, nt, d) in check.items():
        i = text.index('Name = "%s"' % name)
        seg = text[i:]
        def field(f):
            j = seg.index(f + " = [==[") + len(f) + 6
            return base64.b64decode(seg[j:seg.index("]==]", j)])
        assert len(field("Verts")) == nv * 12, name
        assert len(field("Tris")) == nt * 12, name
        assert len(field("Cols")) == nv * 3, name
        assert len(field("BoneIdx")) == nv * 4 and len(field("Wts")) == nv * 4, name
        assert np.array_equal(np.frombuffer(field("Verts"), dtype="<f4").reshape(-1, 3), d["Verts"])
        print("PREVIEW", name, "verts", nv, "tris", nt, "signed volume (positive = wound outward)", round(d["volume"], 3), flush=True)
    assert text.count('{ "') == len(bones), "bone count"
    print("PREVIEW file", PREVIEW, os.path.getsize(PREVIEW) // 1024, "KB; bones", len(bones), flush=True)


def export_fbx(pieces, rig):
    """The FBX, as File > Import 3D wants it: the pieces under their game names, and the skeleton."""
    pet_kit.OUT = ASSETS
    apply(rig, {})
    names = {"Body": N + "Body", "Head": N + "Head", "Tail": N + "Tail", "WingL": N + "WingL", "WingR": N + "WingR", "Glow": GLOW_NAME}
    aside = []
    for block in (bpy.data.objects, bpy.data.meshes):          # the bake sources' own pieces step aside: the game reads its pieces by name
        for nm in names.values():
            other = block.get(nm)
            if other is not None:
                other.name = nm + "_Aside"
                aside.append((other, nm))
    for key, nm in names.items():
        pieces[key].name = pieces[key].data.name = nm
    pet_kit.select_only(list(pieces.values()) + [rig], rig)
    path = os.path.join(ASSETS, PET + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                             primary_bone_axis="Y", secondary_bone_axis="X")
    raw = open(path, "rb").read()
    home = os.path.expanduser("~").encode()
    if home.startswith(b"/Users/") and len(home) > 7:
        pad = b"user"[:len(home) - 7].ljust(len(home) - 7, b"_")
        fixed = raw.replace(home + b"/", b"/Users/" + pad + b"/")
        if fixed != raw:
            open(path, "wb").write(fixed)
    for key in pieces:
        pieces[key].name = pieces[key].data.name = RIGGED + key
    for other, nm in aside:
        other.name = nm
    return path


def save_clean_blend():
    """The .blend, written from the scene alone (the window manager's remembered paths stay out of it, which save_as_mainfile leaves behind)."""
    path = os.path.join(pet_kit.TOOLS, PET + ".blend")
    render = bpy.context.scene.render
    render.filepath = "//" + "_" * 1020            # (the render output field keeps old bytes after a shorter path: fill it to its end, then clear it)
    render.filepath = "//"
    for img in bpy.data.images:
        if img.filepath_raw and not img.filepath_raw.startswith("//"):
            img.filepath_raw = bpy.path.relpath(img.filepath_raw, start=pet_kit.TOOLS)
    bpy.data.libraries.write(path, {bpy.context.scene}, path_remap="RELATIVE_ALL", compress=True)
    return path


VERIFY_CODE = """
import bpy, json
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=%r)
out = {"meshes": {}, "armatures": 0, "bones": 0, "bone_names": []}
for o in bpy.data.objects:
    if o.type == "MESH":
        me = o.data
        names = {g.index: g.name for g in o.vertex_groups}
        out["meshes"][o.name] = [len(me.vertices), sum(len(p.vertices) - 2 for p in me.polygons), len(o.vertex_groups), [m.name for m in me.materials], bool(me.uv_layers),
                                 max(len(v.groups) for v in me.vertices), sum(1 for v in me.vertices if not v.groups), o.parent.name if o.parent else None]
    elif o.type == "ARMATURE":
        out["armatures"] += 1
        out["bones"] += len(o.data.bones)
        out["bone_names"] = sorted(b.name for b in o.data.bones)
out["images"] = sorted(set(i.filepath for i in bpy.data.images if i.filepath))
print("VFJSON" + json.dumps(out))
"""


def verify_fbx(path):
    """Imports the FBX in a fresh Blender: meshes, bones, vertices, groups, materials and the maps they point at."""
    import json
    import subprocess
    res = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", "--python-expr", VERIFY_CODE % path], capture_output=True, text=True)
    line = next(l for l in res.stdout.splitlines() if l.startswith("VFJSON"))
    return json.loads(line[6:])


def flap_range(chk, rig, step=4.0):
    """Both wings turned together about the shoulder (roll: down is positive on the left, negative on the right): how far each way before the
    Checker finds the wings in each other, in the legs or in the trunk (the stroke the game flaps through)."""
    out = {}
    for sign, label in ((-1, "up"), (1, "down")):
        a, last = step, 0.0
        while a <= 120:
            apply(rig, both({"WingL1": (0, 0, sign * a)}))
            r = chk.run()
            bad = chk.worse(r, ("Wing",))
            if bad:
                out[label + "_first_flag"] = (a, bad)
                break
            last = a
            a += step
        out[label] = last
    apply(rig, {})
    return out


def mirror_check(raw):
    """The right side's limits against the left's (a bone's twin: yaw and roll swap their ends): the worst difference in degrees."""
    worst = 0.0
    for name, ax in raw.items():
        t = twin(name)
        if t == name or name[-2:-1] != "L" and name[-1] != "L":
            continue
        if t not in raw:
            continue
        for a in "xyz":
            lo, hi = ax[a]
            tl, th = raw[t][a]
            exp = (lo, hi) if a == "x" else (-hi, -lo)
            worst = max(worst, abs(tl - exp[0]), abs(th - exp[1]))
    return worst


if __name__ == "__main__":
    engine_before = scene.render.engine
    prepare_wing_groups()
    pieces = gather()
    rig = skeleton()
    bind_all(pieces, rig)
    report_weights(pieces, rig)
    chk = Checker(pieces, rig)
    print("REST", {k: v for k, v in chk.rest.items() if k[:2] in ("x_", "in") or k in ("tear", "crush")}, flush=True)
    for b in rig.data.bones:
        h, t = b.head_local, b.tail_local
        print("BONE", b.name, "parent", b.parent.name if b.parent else None, "head", tuple(round(x, 3) for x in (-h.x, h.z, h.y)), "tail",
              tuple(round(x, 3) for x in (-t.x, t.z, t.y)), flush=True)
    if STAGE == "probe":
        raise SystemExit(0)
    print("FLAP both wings together:", flap_range(chk, rig), flush=True)
    results = run_poses(chk, rig)
    raw = sweep(chk, rig, [b.name for b in rig.data.bones if b.name != "Root"], step=6.0, top=96.0)
    for k, v in sweep.why.items():
        print("WHY", k, v, flush=True)
    print("MIRROR worst difference between the left and right limits (degrees):", mirror_check(raw), flush=True)
    limits = final_limits(raw)
    for name, ax in limits.items():
        print("SAFE", name, {a: tuple(int(x) for x in v) for a, v in ax.items()}, flush=True)
    cam = review_setup()
    worst = rest_match(cam, pieces)
    weight_views(cam, rig, pieces)
    pose_sheet(cam, rig, "00_rest", {}, ("front", "side", "back", "three", "top"), tile=360)
    groups = [("10_wings", ["WingsUp", "WingsMid", "WingsDown70", "WingsDownFlex", "WingsSpread", "PrimariesFanned"], ("front", "three", "top")),
              ("11_wings_fold", ["WingsFolded", "ElbowWristFold", "PrimariesClosed", "WingsDown70"], ("front", "side", "top")),
              ("20_neck", ["NeckUp", "NeckDown", "NeckLeft", "NeckRight", "NeckTilt", "NeckLunge", "NeckHigh"], ("front", "side", "three")),
              ("30_tail", ["TailLeft", "TailRight", "TailUp", "TailDown", "TailCurl"], ("side", "top", "back")),
              ("40_legs", ["LegsTuckedBack", "LegsForward", "LegsDangle"], ("side", "three", "front")),
              ("50_poses", ["Hover", "Glide", "Roar"], ("front", "side", "three"))]
    for name, poses, views in groups:
        multi_sheet(cam, rig, name, [(p, POSES[p]) for p in poses], views, scale=2.6, tile=330)
    for v in ("h_side", "h_three", "h_front"):
        VIEWS[v] = (VIEWS[v[2:]][0], V(0, -0.50, 1.32))
    paths = []
    for ang in (0, -15, -30, -45):
        apply(rig, {"Jaw": (ang, 0, 0)})
        for v in ("h_side", "h_three", "h_front"):
            paths.append(shoot(cam, os.path.join(TMP, "j_%d_%s.png" % (ang, v)), v, 0.75))
    sheet(paths, os.path.join(REVIEW, "60_jaw.png"), 3, 330)
    for p in paths:
        os.remove(p)
    apply(rig, {})
    if "limits" in ARGS or STAGE == "all":
        limit_sheets(cam, rig, limits)
    if STAGE == "all":
        for o in REVIEW_OBJS:                                   # (the review's camera and world leave the file)
            if isinstance(o, bpy.types.Object):
                bpy.data.objects.remove(o, do_unlink=True)
            else:
                bpy.data.worlds.remove(o)
        scene.render.engine = engine_before
        write_preview(pieces, rig)
        fbx = export_fbx(pieces, rig)
        print("FBX", fbx, os.path.getsize(fbx) // 1024, "KB", flush=True)
        info = verify_fbx(fbx)
        print("FBX CHECK armatures", info["armatures"], "bones", info["bones"], "meshes", len(info["meshes"]), flush=True)
        for name, row in sorted(info["meshes"].items()):
            print("FBX MESH", name, "verts", row[0], "tris", row[1], "groups", row[2], "materials", row[3], "uv", row[4], "max influences", row[5], "unweighted", row[6], "parent", row[7], flush=True)
        print("FBX bones", info["bone_names"], flush=True)
        print("FBX images", info["images"], flush=True)
        path = save_clean_blend()
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("DONE stage", STAGE, flush=True)

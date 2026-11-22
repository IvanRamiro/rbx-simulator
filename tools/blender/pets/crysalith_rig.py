"""Crysalith, "The Eternal Frost" (Secret, Exclusive Egg), rigged: the existing model, exactly as it was modelled and baked, given one skeleton.

Written by the project's pet pipeline. Crysalith's look is kept as it is: the same game pieces, the same UVs, the same baked colour, normal and
roughness maps (assets/pets/ExclusiveEgg/Crysalith_*_{color,normal,roughness}.png are read, never written), the same glow pieces, the same
names. Only how it moves changes. It was a jointed pet (eight rigid parts turning on pivots); it becomes a skinned one, as the pipeline's
recent pets are: every piece skinned to ONE armature (each piece is a MeshPart in the game, and they all share the bones):

    Root > Hips > Spine1 > Spine2 > Chest > Neck1 > Neck2 > Head > AntlerL1 > AntlerL2, AntlerR1 > AntlerR2
    Hips > Tail1 > Tail2 > Tail3 > Tail4
    Chest > LegFL1 > LegFL2 > LegFL3 > FootFL (and FR);  Hips > LegBL1 > LegBL2 > LegBL3 > FootBL (and BR)

so the trunk can breathe, roll and bend, the neck can carry the head, the legs can be driven by a three-segment IK gait with a foot, the tail
can swing from its root, and the two crowns of crystal antlers can resonate on their own. The head has no Jaw: its lower jaw is part of the
skull's one loft, closed along a painted mouth line, and a hinge there would tear the lip (see JAW_NOTE).

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/crysalith_rig.py -- [rig|all] [review dir]

rig: build and check the skeleton, the weights, every pose and the safe ranges, with renders (nothing is written into the project).
all: also the .blend (the rigged collection is added to tools/blender/pets/ExclusiveEgg/Crysalith_Final.blend, the old collections untouched),
the FBX (assets/pets/ExclusiveEgg/Crysalith.fbx) and the preview data module (src/client/Pets/_Preview/CrysalithData.lua, temporary,
never committed). It reads Crysalith_Final.blend's own game pieces (collection Crysalith): they are copied, never changed, so the file can be
rebuilt any number of times. Faces -Y, Z up, 1 unit = 1 metre; +X is its left. The game maps Blender (x, y, z) to its own (-x, z, y).

What touches what (unchanged from the jointed model): each leg's top is a rounded mass centred on its pivot inside the shoulder or hip; the
head's skull base and throat latch sit over the top of the neck; the antlers' beams are sunk in bony pedicles on the skull, ringed by a crystal
coronet; the tail's root mass is inside the rump. Where two pieces overlap, both take the same weights there, so they move as one and no seam
can open. Every plate and crystal is its own island and takes one set of weights (those of the skin where it grows), so it is never sheared.
"""
import base64
import collections
import json
import math
import os
import struct
import subprocess
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "rig"
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REVIEW = ARGS[1] if len(ARGS) > 1 and ARGS[1] else os.path.join(ROOT, "renders", "exclusive_pets", "crysalith_rig")
os.makedirs(REVIEW, exist_ok=True)
PET, EGG = "Crysalith", "ExclusiveEgg"
N = PET + "_"
SOURCE = os.path.join(ROOT, "tools", "blender", "pets", EGG, "Crysalith_Final.blend")
FBX_OUT = os.path.join(ROOT, "assets", "pets", EGG, "Crysalith.fbx")
PREVIEW_OUT = os.path.join(ROOT, "src", "client", "Pets", "_Preview", "CrysalithData.lua")


def V(*a):
    return Vector(a)


TAU = 2 * math.pi
JAW_NOTE = "no Jaw bone: the lower jaw is part of the skull's single loft (one island with the upper jaw); a hinge there would tear the lip line"


def smooth(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def machine_patterns():
    """What must not be in a file that is committed: this machine's home folder and its temporary folders (built here, not written out)."""
    home = os.path.expanduser("~").encode()
    return [home, b"/" + b"pri" + b"vate/", b"/" + b"tm" + b"p/", b"/" + b"var/", b"/" + b"home/", b"scratch" + b"pad"]


def verify_fbx(path=None):
    """Imports the exported FBX into an empty scene (a fresh Blender: --factory-startup) and reports what the game will get."""
    path = path or FBX_OUT
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    out = {"armatures": [a.name for a in arm], "bones": sorted(b.name for a in arm for b in a.data.bones), "meshes": {}}
    for o in meshes:
        me = o.data
        tris = sum(len(q.vertices) - 2 for q in me.polygons)
        infl = max((len(v.groups) for v in me.vertices), default=0)
        unw = sum(1 for v in me.vertices if not v.groups)
        used = {o.vertex_groups[g.group].name for v in me.vertices for g in v.groups}
        imgs = sorted({n.image.name for m in me.materials if m and m.node_tree for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image})
        out["meshes"][o.name] = {"tris": tris, "verts": len(me.vertices), "max_infl": infl, "unweighted": unw, "bones_used": len(used), "images": imgs, "scale": tuple(round(x, 4) for x in o.scale),
                                 "parent": o.parent.name if o.parent else None, "modifiers": [m.type for m in o.modifiers]}
    weighted = set()
    for o in meshes:
        weighted |= {o.vertex_groups[g.group].name for v in o.data.vertices for g in v.groups}
    out["bones_without_weights"] = sorted(set(out["bones"]) - weighted)
    out["total_tris"] = sum(m["tris"] for m in out["meshes"].values())
    raw = open(path, "rb").read()
    out["fbx_bytes"] = len(raw)
    out["machine_paths"] = {pat.decode(): raw.count(pat) for pat in machine_patterns() if pat in raw}
    out["neutral_paths"] = raw.count(b"/Users/" + b"user/")
    print("VERIFY", json.dumps(out, indent=1, default=str), flush=True)
    return out


if STAGE == "verify":
    verify_fbx()
    sys.exit(0)


# ======================================================================================================================================
# the file: Crysalith_Final.blend's own game pieces, copied into a collection of their own
# ======================================================================================================================================
bpy.ops.wm.open_mainfile(filepath=SOURCE, load_ui=False)
scene = bpy.context.scene
OLD = bpy.data.collections[PET]
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = True
for old in [c for c in bpy.data.collections if c.name == PET + "_Game"]:        # a previous build: rebuilt from the pieces each time
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)
for arm in [a for a in bpy.data.armatures if a.users == 0]:
    bpy.data.armatures.remove(arm)
GAME = bpy.data.collections.new(PET + "_Game")
scene.collection.children.link(GAME)
SOLIDS = ["Body", "Head", "Antlers", "Tail", "LegFL", "LegFR", "LegBL", "LegBR"]
GLOWS = ["Head_Glow_48d8ff", "Head_Glow_ffffff", "Antlers_Glow_5fe3ff"]
PIECES = SOLIDS + GLOWS
GAME_NAME = {p: "%sGame_%s" % (N, p) for p in PIECES}      # in the .blend; the FBX gets the real names (export_names)


def copy_piece(name):
    src = bpy.data.objects[N + name]
    o = src.copy()
    o.data = src.data.copy()
    o.name = GAME_NAME[name]
    o.data.name = GAME_NAME[name]
    for c in list(o.users_collection):
        c.objects.unlink(o)
    GAME.objects.link(o)
    o.data.transform(src.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    for k in list(o.keys()):
        del o[k]
    return o


PIECE = {p: copy_piece(p) for p in PIECES}
REST_TRIS = {p: sum(len(q.vertices) - 2 for q in o.data.polygons) for p, o in PIECE.items()}


def verts(o):
    a = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


# ======================================================================================================================================
# the skeleton (Blender axes; the left side, +X, then mirrored)
# ======================================================================================================================================
# The spine runs through the middle of the trunk; the neck rises from the withers to the head's pivot (the marker the jointed model turned its
# head on); the legs' joints are the generator's own leg points (crysalith.py LEGS) after its stance turn, which the meshes were built on.
HIPS, SPINE1, SPINE2, CHEST = V(0, 0.34, 1.04), V(0, 0.08, 1.02), V(0, -0.17, 1.00), V(0, -0.42, 1.02)
NECK1, NECK2, HEAD, HEAD_TIP = V(0, -0.72, 1.12), V(0, -0.92, 1.47), V(0, -1.13, 1.79), V(0, -1.52, 1.80)
JAW_HINGE, JAW_TIP = V(0, -1.16, 1.70), V(0, -1.66, 1.60)       # the lower jaw's hinge under the skull's back, and the chin
TAILP = [V(0, 0.535, 1.115), V(0, 0.905, 1.005), V(0, 1.305, 0.965), V(0, 1.50, 1.045), V(0, 1.95, 1.55)]
ANT_BASE, ANT_MID, ANT_TIP = V(0.087, -1.23, 2.00), V(0.397, -1.01, 2.27), V(0.78, -1.10, 2.70)
LEG = {   # left; shoulder/hip, elbow/stifle, wrist/hock, fetlock, the ground under the hoof
    "F": [V(0.165, -0.470, 1.050), V(0.250, -0.423, 0.647), V(0.262, -0.508, 0.331), V(0.262, -0.508, 0.176), V(0.262, -0.557, 0.0)],
    "B": [V(0.160, 0.311, 1.070), V(0.262, 0.176, 0.704), V(0.262, 0.422, 0.394), V(0.260, 0.397, 0.178), V(0.260, 0.355, 0.0)],
}


def mirror(v):
    return V(-v.x, v.y, v.z)


def build_bones():
    """[(name, head, tail, parent)]: each bone's tail is its first child's head (the last bone of a chain ends where its piece ends)."""
    b = [("Root", V(0, 0, 0), V(0, 0, 0.12), None),
         ("Hips", HIPS, SPINE1, "Root"), ("Spine1", SPINE1, SPINE2, "Hips"), ("Spine2", SPINE2, CHEST, "Spine1"), ("Chest", CHEST, NECK1, "Spine2"),
         ("Neck1", NECK1, NECK2, "Chest"), ("Neck2", NECK2, HEAD, "Neck1"), ("Head", HEAD, HEAD_TIP, "Neck2"), ("Jaw", JAW_HINGE, JAW_TIP, "Head")]
    for side, tag in ((1, "L"), (-1, "R")):
        m = (lambda v: v) if side > 0 else mirror
        b += [("Antler%s1" % tag, m(ANT_BASE), m(ANT_MID), "Head"), ("Antler%s2" % tag, m(ANT_MID), m(ANT_TIP), "Antler%s1" % tag)]
    for k in range(4):
        b.append(("Tail%d" % (k + 1), TAILP[k], TAILP[k + 1], "Hips" if k == 0 else "Tail%d" % k))
    for end, parent in (("F", "Chest"), ("B", "Hips")):
        for side, tag in ((1, "L"), (-1, "R")):
            m = (lambda v: v) if side > 0 else mirror
            P = [m(p) for p in LEG[end]]
            names = ["Leg%s%s%d" % (end, tag, k + 1) for k in range(3)] + ["Foot%s%s" % (end, tag)]
            for k in range(4):
                b.append((names[k], P[k], P[k + 1], parent if k == 0 else names[k - 1]))
    return b


BONES = build_bones()
BONE_NAMES = [x[0] for x in BONES]
BI = {n: i for i, n in enumerate(BONE_NAMES)}
NB = len(BONES)


def skeleton():
    arm = bpy.data.armatures.new(PET + "_Rig")
    rig = bpy.data.objects.new(PET + "_Rig", arm)
    GAME.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in BONES:
        eb = arm.edit_bones.new(name)
        eb.head, eb.tail = head, tail
        eb.use_deform = True
    for name, head, tail, parent in BONES:
        eb = arm.edit_bones[name]
        if parent:
            eb.parent = arm.edit_bones[parent]
            eb.use_connect = False
        y = (eb.tail - eb.head).normalized()
        eb.align_roll(V(1, 0, 0).cross(y) if abs(y.x) < 0.95 else V(0, 0, 1))     # local X = the pet's lateral axis, so a turn about it is a pitch
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# ======================================================================================================================================
# weights: one rule per region, by where a point is, so overlapping pieces take the same weights
# ======================================================================================================================================
def islands_of(o):
    n = len(o.data.vertices)
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for e in o.data.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            par[a] = b
    d = collections.defaultdict(list)
    for i in range(n):
        d[find(i)].append(i)
    return sorted(d.values(), key=lambda g: -len(g))


def polyline(pts):
    A = np.array([tuple(p) for p in pts])
    seg = A[1:] - A[:-1]
    L = np.linalg.norm(seg, axis=1)
    return A, seg, L, np.concatenate([[0.0], np.cumsum(L)])


def project(P, pts):
    """For each point of P (n, 3): its arc-length position s along the polyline (the ends extended straight on) and its distance d from it."""
    A, seg, L, cum = polyline(pts)
    best = np.full(len(P), np.inf)
    s_out = np.zeros(len(P))
    for k in range(len(seg)):
        t = ((P - A[k]) @ seg[k]) / (L[k] ** 2)
        lo = -np.inf if k == 0 else 0.0
        hi = np.inf if k == len(seg) - 1 else 1.0
        t = np.clip(t, lo, hi)
        d = np.linalg.norm(P - (A[k] + np.outer(t, seg[k])), axis=1)
        better = d < best
        best[better] = d[better]
        s_out[better] = cum[k] + t[better] * L[k]
    return s_out, best


def chain(s, names, joints):
    """A chain of bones along a polyline: joints = [(arc position of the joint after bone k, half-width of its blend)]. Returns {bone: weights}."""
    t = [np.ones_like(s)] + [smooth(j - h, j + h, s) for j, h in joints] + [np.zeros_like(s)]
    return {names[k]: t[k] - t[k + 1] for k in range(len(names))}


def to_matrix(parts, n):
    W = np.zeros((n, NB))
    for name, w in parts.items():
        W[:, BI[name]] += w
    return W


def soft(P, segs, names, sigma):
    """Soft nearest-bone weights: each bone is a segment (A, B); a point takes a share of every bone exp(-(d^2 - dmin^2) / 2 sigma^2) of it (d: the
    distance to the segment), so the weights change smoothly and a joint blends over about 1.5 sigma on each side, however the polyline bends.
    segs[0] extends backward and segs[-1] forward without end, so the ends of a chain hold. Returns a matrix (n, NB)."""
    D = np.zeros((len(P), len(segs)))
    for k, (a, b) in enumerate(segs):
        A, B = np.array(tuple(a)), np.array(tuple(b))
        ab = B - A
        t = ((P - A) @ ab) / (ab @ ab)
        t = np.clip(t, -np.inf if k == 0 else 0.0, np.inf if k == len(segs) - 1 else 1.0)
        D[:, k] = np.linalg.norm(P - (A + np.outer(t, ab)), axis=1)
    sig = np.broadcast_to(np.asarray(sigma, dtype=float), (len(segs),))
    e = np.exp(-(D ** 2 - (D.min(axis=1, keepdims=True)) ** 2) / (2 * sig * sig))
    e /= e.sum(axis=1, keepdims=True)
    W = np.zeros((len(P), NB))
    for k, n in enumerate(names):
        W[:, BI[n]] += e[:, k]
    return W


TRUNK_NAMES = ["Hips", "Spine1", "Spine2", "Chest", "Neck1", "Neck2", "Head"]
TRUNK_SIGMA = [0.09, 0.10, 0.10, 0.11, 0.11, 0.09, 0.07]      # per bone: how far its weight reaches into its neighbours


def trunk_segs():
    pts = [HIPS, SPINE1, SPINE2, CHEST, NECK1, NECK2, HEAD, HEAD + (HEAD_TIP - HEAD).normalized() * 0.3]
    return [(pts[k], pts[k + 1]) for k in range(7)]


def trunk_weights(P):
    return soft(P, trunk_segs(), TRUNK_NAMES, TRUNK_SIGMA)


def limb_pull(W, P, pivot, side_sign, bone, reach=0.26, hold=0.10, share=0.30):
    """Skin near a leg's pivot follows the leg a little (the shoulder's and the hip's muscle masses ride with the limb)."""
    d = np.linalg.norm(P - np.array(tuple(pivot)), axis=1)
    g = (1.0 - smooth(hold, reach, d)) * (P[:, 0] * side_sign > 0)
    pull = share * g
    W *= (1 - pull)[:, None]
    W[:, BI[bone]] += pull
    return W


def body_weights(P):
    W = trunk_weights(P)
    for tag, sg in (("L", 1), ("R", -1)):
        m = (lambda v: v) if sg > 0 else mirror
        W = limb_pull(W, P, m(LEG["F"][0]), sg, "LegF%s1" % tag)
        W = limb_pull(W, P, m(LEG["B"][0]), sg, "LegB%s1" % tag)
    return W


def head_weights(P):
    """The head rigid, as the jointed model turned it: its skull base and throat latch are a collar over the top of the neck, and the head turns on the
    pivot inside it (the body's neck tube, which takes the Head's share near its top, runs up into the collar)."""
    W = np.zeros((len(P), NB))
    W[:, BI["Head"]] = 1.0
    return W


def jaw_island(o):
    """The head piece's lower jaw: the lowest of its larger islands (a loft of its own under the skull's upper jaw)."""
    P = verts(o)
    isl = [g for g in islands_of(o) if len(g) >= 80]
    return min(isl, key=lambda g: P[g][:, 2].mean())


def spine_line():
    return [HIPS, SPINE1, SPINE2, CHEST, NECK1, NECK2, HEAD]


LEG_JOINT = {"F": (0.10, 0.07, 0.045), "B": (0.12, 0.09, 0.045)}      # the blend at the elbow/stifle, the wrist/hock, the fetlock (m, about 1.5 sigma each side)


def leg_weights(P, end, tag):
    sg = 1 if tag == "L" else -1
    m = (lambda v: v) if sg > 0 else mirror
    pts = [m(p) for p in LEG[end]]
    names = ["Leg%s%s%d" % (end, tag, k + 1) for k in range(3)] + ["Foot%s%s" % (end, tag)]
    segs = [(pts[k], pts[k + 1]) for k in range(4)]
    J = LEG_JOINT[end]
    W = soft(P, segs, names, [J[0], max(J[0], J[1]), max(J[1], J[2]), J[2]])
    parent = "Chest" if end == "F" else "Hips"
    up = 0.75 * smooth(pts[0].z - 0.04, pts[0].z + 0.11, P[:, 2])
    W *= (1 - up)[:, None]
    W[:, BI[parent]] += up
    return W


def tail_weights(P):
    A, seg, L, cum = polyline(TAILP)
    s, d = project(P, TAILP)
    segs = [(TAILP[k], TAILP[k + 1]) for k in range(4)]
    W = soft(P, segs, ["Tail1", "Tail2", "Tail3", "Tail4"], 0.11)
    root = 1.0 - smooth(0.0, 0.26, s)           # the root mass sits inside the rump: it follows the hips
    W *= (1 - root)[:, None]
    W[:, BI["Hips"]] += root
    return W


def antler_line(side):
    m = (lambda v: v) if side > 0 else mirror
    return [m(ANT_BASE), m(ANT_MID), m(ANT_TIP)]


def antler_weights(P, side):
    tag = "L" if side > 0 else "R"
    base, mid, tip = antler_line(side)
    up = (mid - base).normalized()
    segs = [(base - up * 0.30, base + up * 0.10), (base + up * 0.10, mid), (mid, tip)]
    return soft(P, segs, ["Head", "Antler%s1" % tag, "Antler%s2" % tag], 0.045)


def rigid_by_island(o, rule, big):
    """Weights for a piece: the biggest islands (the skin: `big` of them) per vertex by `rule`; every other island one set of weights, the rule's at
    the island's root (its point nearest the skin: its centroid for a plate or a crystal, which is sunk into what carries it)."""
    P = verts(o)
    W = np.zeros((len(P), NB))
    isl = islands_of(o)
    for k, ids in enumerate(isl):
        ids = np.array(ids)
        if k < big:
            W[ids] = rule(P[ids])
        else:
            c = P[ids].mean(axis=0)
            w = rule(c[None, :])[0]
            W[ids] = np.eye(NB)[int(np.argmax(w))]          # a plate or crystal rides one bone, the one that carries the skin under it
    return W, isl


def finish(W):
    """Normalized, at most four influences, each above a hundredth."""
    out = np.zeros_like(W)
    for i in range(len(W)):
        top = np.argsort(-W[i])[:4]
        w = W[i, top]
        keep = w >= 0.01
        if not keep.any():
            keep[0] = True
        top, w = top[keep], w[keep]
        out[i, top] = w / w.sum()
    return out


def assign(o, W):
    o.vertex_groups.clear()
    groups = {}
    for b in range(NB):
        col = W[:, b]
        ids = np.nonzero(col > 0)[0]
        if len(ids) == 0:
            continue
        g = o.vertex_groups.new(name=BONE_NAMES[b])
        for i in ids:
            g.add([int(i)], float(col[i]), "REPLACE")
        groups[BONE_NAMES[b]] = len(ids)
    return groups


def bind_all(rig):
    """Weights for every piece, then every piece parented to the rig with an Armature modifier."""
    allW = {}
    for part in SOLIDS + GLOWS:
        o = PIECE[part]
        if part == "Body":
            W, isl = rigid_by_island(o, body_weights, 1)
        elif part == "Head":
            W, isl = rigid_by_island(o, head_weights, 1)
            jaw = np.array(jaw_island(o))
            d = np.linalg.norm(verts(o)[jaw] - np.array(tuple(JAW_HINGE)), axis=1)
            share = 0.6 * (1.0 - smooth(0.03, 0.12, d))                     # near the hinge the jaw's skin follows the skull a little: no hard corner as it opens
            W[jaw] = 0
            W[jaw, BI["Jaw"]] = 1.0 - share
            W[jaw, BI["Head"]] = share
        elif part == "Tail":
            W, isl = rigid_by_island(o, tail_weights, 1)
        elif part.startswith("Leg"):
            W, isl = rigid_by_island(o, lambda P, e=part[3], t=part[4]: leg_weights(P, e, t), 1)
        elif part == "Antlers":
            def rule(P):
                return np.where((P[:, 0:1] >= 0), antler_weights(P, 1), antler_weights(P, -1))
            W, isl = rigid_by_island(o, rule, 2)
        elif part == "Antlers_Glow_5fe3ff":
            def rule(P):
                return np.where((P[:, 0:1] >= 0), antler_weights(P, 1), antler_weights(P, -1))
            W, isl = rigid_by_island(o, rule, 0)
        else:                                                               # the head's glow pieces: the eyes' rings and glints
            W = np.zeros((len(o.data.vertices), NB))
            W[:, BI["Head"]] = 1.0
            isl = []
        W = finish(W)
        allW[part] = W
        assign(o, W)
        md = o.modifiers.new("Rig", "ARMATURE")
        md.object = rig
        o.parent = rig
    return allW


# ======================================================================================================================================
# poses: in the game's own axes (x pitch about its right axis, y yaw about up, z roll about its long axis; Roblox CFrame.Angles)
# ======================================================================================================================================
GAME_TO_BLENDER = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))        # its own inverse


def game_rot(rx, ry, rz):
    return (Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X"))


def pose(rig, spec, move=None):
    """spec: bone: (rx, ry, rz) in the game's axes; move: bone: (x, y, z) game axes (the hips). Quaternion channels, the bone's own frame."""
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    for name, (rx, ry, rz) in spec.items():
        pb = rig.pose.bones[name]
        B = pb.bone.matrix_local.to_3x3()
        C = GAME_TO_BLENDER @ game_rot(rx, ry, rz) @ GAME_TO_BLENDER
        pb.rotation_quaternion = (B.inverted() @ C @ B).to_quaternion()
    for name, (x, y, z) in (move or {}).items():
        pb = rig.pose.bones[name]
        B = pb.bone.matrix_local.to_3x3()
        pb.location = B.inverted() @ (GAME_TO_BLENDER @ Vector((x, y, z)))
    bpy.context.view_layer.update()


class Skin:
    """Linear blend skinning of every piece in numpy (what the engine does), for the safe-range search: fast, and independent of the depsgraph."""

    def __init__(self, rig, allW):
        self.rig = rig
        self.pieces = {}
        for part, o in PIECE.items():
            P = verts(o)
            W = allW[part]
            idx = np.argsort(-W, axis=1)[:, :4]
            wts = np.take_along_axis(W, idx, axis=1)
            edges = np.empty(len(o.data.edges) * 2, dtype=np.int64)
            o.data.edges.foreach_get("vertices", edges)
            self.pieces[part] = (P, idx, wts, edges.reshape(-1, 2), islands_of(o))
        pose(rig, {})
        self.rest_mats = [np.array(rig.pose.bones[n].bone.matrix_local) for n in BONE_NAMES]

    def bone_mats(self):
        return np.array([np.array(self.rig.pose.bones[n].matrix) @ np.linalg.inv(self.rest_mats[i]) for i, n in enumerate(BONE_NAMES)])

    def deform(self, part, mats=None):
        P, idx, wts, edges, isl = self.pieces[part]
        mats = self.bone_mats() if mats is None else mats
        H = np.concatenate([P, np.ones((len(P), 1))], axis=1)
        out = np.zeros((len(P), 3))
        for k in range(4):
            M = mats[idx[:, k]]
            out += wts[:, k:k + 1] * np.einsum("nij,nj->ni", M[:, :3, :], H)
        return out

    def stretch(self, parts=None, mats=None):
        """Worst edge of the skin islands: the length it gained (m) and its ratio, and the most crushed ratio among edges of real length."""
        mats = self.bone_mats() if mats is None else mats
        worst = {"gain": 0.0, "ratio": 1.0, "crush": 1.0, "part": "", "at": None}
        for part in (parts or SOLIDS):
            P, idx, wts, edges, isl = self.pieces[part]
            Q = self.deform(part, mats)
            l0 = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1)
            l1 = np.linalg.norm(Q[edges[:, 0]] - Q[edges[:, 1]], axis=1)
            gain = l1 - l0
            k = int(np.argmax(gain))
            if gain[k] > worst["gain"]:
                worst.update(gain=float(gain[k]), ratio=float(l1[k] / max(l0[k], 1e-9)), part=part, at=tuple(np.round(P[edges[k, 0]], 2)))
            real = l0 > 0.02
            if real.any():
                worst["crush"] = min(worst["crush"], float((l1[real] / l0[real]).min()))
        return worst


class FK:
    """Bone matrices from a pose in numpy (the same maths as pose() and the engine): used to scan every bone's range without the depsgraph."""

    def __init__(self, rig):
        pose(rig, {})
        self.rest = np.array([np.array(rig.pose.bones[n].bone.matrix_local) for n in BONE_NAMES])
        self.inv = np.linalg.inv(self.rest)
        self.parent = [BI[x[3]] if x[3] else -1 for x in BONES]
        self.B = self.rest[:, :3, :3]
        self.g2b = np.array(GAME_TO_BLENDER)

    def local(self, i, rot=None, move=None):
        T = np.eye(4)
        if rot is not None:
            C = self.g2b @ np.array(game_rot(*rot)) @ self.g2b
            T[:3, :3] = self.B[i].T @ C @ self.B[i]
        if move is not None:
            T[:3, 3] = self.B[i].T @ (self.g2b @ np.array(move))
        return T

    def skin(self, spec, move=None):
        move = move or {}
        posed = [None] * NB
        for i, name in enumerate(BONE_NAMES):
            T = self.local(i, spec.get(name), move.get(name))
            p = self.parent[i]
            base = self.rest[i] if p < 0 else posed[p] @ self.inv[p] @ self.rest[i]
            posed[i] = base @ T
        return np.array([posed[i] @ self.inv[i] for i in range(NB)])


TEAR_GAIN = 0.05       # m: an edge that grows more than this has torn
TEAR_RATIO = 1.5
CRUSH = 0.40           # an edge of real length (> 2 cm) shorter than this share of itself has collapsed


def safe_limits(rig, skin, fk, step=0.025, top=1.8):
    """For each bone and axis, how far each way it can turn (alone) before the skin tears (an edge gaining more than TEAR_GAIN and TEAR_RATIO) or
    collapses (an edge crushed below CRUSH). Reported in the game's axes."""
    out = {}
    for name in BONE_NAMES[1:]:
        out[name] = {}
        for ax in range(3):
            for sign in (1, -1):
                lim, why = top, ""
                a = step
                while a <= top + 1e-9:
                    rot = [0.0, 0.0, 0.0]
                    rot[ax] = sign * a
                    w = skin.stretch(mats=fk.skin({name: tuple(rot)}))
                    if (w["gain"] > TEAR_GAIN and w["ratio"] > TEAR_RATIO) or w["crush"] < CRUSH:
                        lim = a - step
                        why = "tear %.3f m (x%.2f) %s at %s" % (w["gain"], w["ratio"], w["part"], w["at"]) if w["gain"] > TEAR_GAIN else "collapse %.2f" % w["crush"]
                        break
                    a += step
                out[name]["xyz"[ax] + ("+" if sign > 0 else "-")] = (round(lim, 3), why)
    return out


# ======================================================================================================================================
# review: Workbench renders (the baked maps as they are), a contact sheet per set of poses
# ======================================================================================================================================
def review_setup():
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity, sh.show_shadows = "STUDIO", "TEXTURE", False, False
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = scene.world or bpy.data.worlds.new("w")
    scene.world = world
    world.color = (0.80, 0.83, 0.86)
    cam = bpy.data.objects.get("RevCam") or bpy.data.objects.new("RevCam", bpy.data.cameras.new("RevCam"))
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    cam.data.lens = 60
    scene.camera = cam
    for o in list(GAME.objects) + list(OLD.objects):
        if o.type == "MESH" and "_Glow_" in o.name:
            h = o.name.split("_Glow_")[1][:6]
            m = bpy.data.materials.get("Rev" + h) or bpy.data.materials.new("Rev" + h)
            m.diffuse_color = (int(h[:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:], 16) / 255, 1.0)
            o.data.materials.clear()
            o.data.materials.append(m)
    return cam


def only_game(on=True):
    for lc in bpy.context.view_layer.layer_collection.children:
        lc.exclude = (lc.name != GAME.name) if on else (lc.name == GAME.name)


def shoot(path, view, size=640, target=(0, 0.1, 1.2), dist=8.0, xray=False, scale=4.6):
    """An orthographic tile (size wide, three quarters of it high): the same scale in every view, so poses compare."""
    cam = scene.camera
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = scale
    t = Vector(target)
    cam.location = t + Vector(view).normalized() * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = size, size * 3 // 4
    scene.display.shading.show_xray = xray
    scene.display.shading.xray_alpha = 0.55
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_px(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def sheet(paths, out, cols):
    tiles = [load_px(p) for p in paths]
    h, w = tiles[0].shape[:2]
    rows = (len(tiles) + cols - 1) // cols
    big = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for k, t in enumerate(tiles):
        r, c = divmod(k, cols)
        big[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = t
    img = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    img.pixels.foreach_set(big.ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    for p in paths:
        os.remove(p)


def debug_bones(rig, on=True):
    coll = bpy.data.collections.get("Dbg") or bpy.data.collections.new("Dbg")
    if coll.name not in [c.name for c in scene.collection.children]:
        scene.collection.children.link(coll)
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    if not on:
        return
    mat = bpy.data.materials.get("DbgRed") or bpy.data.materials.new("DbgRed")
    mat.diffuse_color = (1.0, 0.1, 0.1, 1.0)
    for b in rig.pose.bones:
        h, t = rig.matrix_world @ b.head, rig.matrix_world @ b.tail
        cu = bpy.data.curves.new("d", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.014
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (*h, 1)
        sp.points[1].co = (*t, 1)
        o = bpy.data.objects.new("dbg_" + b.name, cu)
        o.data.materials.append(mat)
        coll.objects.link(o)
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == "Dbg":
            lc.exclude = False


VIEWS4 = [(0, -1, 0.12), (1, 0, 0.08), (0.75, -0.65, 0.3), (0, 1, 0.15)]


def tiles(prefix, spec, views, move=None, size=420, **kw):
    pose(RIG, spec, move)
    out = []
    for k, v in enumerate(views):
        p = "%s_%d.png" % (prefix, k)
        shoot(p, v, size, **kw)
        out.append(p)
    return out



PALETTE = {}


def bone_colour(name):
    """One distinct colour per bone (hue by its index), so a blend of two bones reads as a mix of two colours."""
    import colorsys
    k = BI[name]
    r, g, b = colorsys.hsv_to_rgb((k * 0.381966) % 1.0, 0.85, 0.95)
    return np.array((r, g, b))


def weight_view(on):
    """Colour every vertex by its weights (a mix of the bones' colours) and show that instead of the maps."""
    sh = scene.display.shading
    if not on:
        sh.color_type = "TEXTURE"
        return
    cols = np.array([bone_colour(n) for n in BONE_NAMES])
    for part, o in PIECE.items():
        W = ALLW[part]
        rgb = W @ cols
        a = o.data.color_attributes.get("wcol") or o.data.color_attributes.new("wcol", "FLOAT_COLOR", "POINT")
        a.data.foreach_set("color", np.concatenate([rgb, np.ones((len(rgb), 1))], axis=1).ravel())
        o.data.color_attributes.active_color = a
    sh.color_type = "VERTEX"


def deg(*a):
    return tuple(math.radians(x) for x in a)


def sym(spec):
    """A left-side spec mirrored onto the right: x pitch stays, y and z flip."""
    out = dict(spec)
    for k, (x, y, z) in spec.items():
        if k.endswith("L") or "L" in k[-2:]:
            out[k[:-2] + "R" + k[-1] if k[-1].isdigit() else k[:-1] + "R"] = (x, -y, -z)
    return out


def legs(front_l, front_r, back_l, back_r):
    """Each leg: (swing hip, bend knee, wrist/hock, foot) as pitches; returns a spec."""
    spec = {}
    for tag, a in (("FL", front_l), ("FR", front_r), ("BL", back_l), ("BR", back_r)):
        for k, name in enumerate(("Leg%s1", "Leg%s2", "Leg%s3", "Foot%s")):
            spec[name % tag] = (a[k], 0, 0)
    return spec


def pose_library():
    P = {}
    P["rest"] = ({}, None)
    # walking: the hip swings, the knee bends as the foot lifts (positive pitch swings a hanging leg forward, a negative knee folds it back)
    fwd = (0.38, -0.14, 0.06, -0.20)
    back = (-0.34, 0.10, -0.02, 0.2)
    lift = (0.55, -1.00, 0.55, 0.25)
    P["GAIT lift fore: hip +0.55 elbow -1.0 wrist +0.55 foot +0.25"] = (legs(lift, (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)), None)
    P["GAIT lift hind: hip +0.5 stifle -0.9 hock +0.9 foot +0.3"] = (legs((0, 0, 0, 0), (0, 0, 0, 0), (0.5, -0.9, 0.9, 0.3), (0, 0, 0, 0)), None)
    P["GAIT reach fore +0.6 / hind -0.6 (swing ends)"] = ({"LegFL1": (0.6, 0, 0), "LegFR1": (0.6, 0, 0), "LegBL1": (-0.6, 0, 0), "LegBR1": (-0.6, 0, 0)}, None)
    P["GAIT reach fore -0.5 / hind +0.7 (swing ends)"] = ({"LegFL1": (-0.5, 0, 0), "LegFR1": (-0.5, 0, 0), "LegBL1": (0.7, 0, 0), "LegBR1": (0.7, 0, 0)}, None)
    P["trot A (FL BR forward, FR BL back)"] = (legs(fwd, back, back, fwd), None)
    P["trot B (FR BL forward, FL BR back)"] = (legs(back, fwd, fwd, back), None)
    P["lifted paws FL + BR"] = (legs(lift, (0, 0, 0, 0), (0, 0, 0, 0), lift), {"Hips": (0, 0.0, 0)})
    P["knees 60 deg (all legs)"] = (legs((0.3, -1.05, 0.7, 0.2), (0.3, -1.05, 0.7, 0.2), (-0.1, -1.05, 1.0, 0.3), (-0.1, -1.05, 1.0, 0.3)), {"Hips": (0, -0.35, 0)})
    P["knees 90 deg (all legs)"] = (legs((0.4, -1.57, 1.0, 0.3), (0.4, -1.57, 1.0, 0.3), (-0.2, -1.57, 1.3, 0.4), (-0.2, -1.57, 1.3, 0.4)), {"Hips": (0, -0.55, 0)})
    P["planted crouch (heavy plant)"] = (legs((0.18, -0.30, 0.16, 0.0), (0.18, -0.30, 0.16, 0.0), (-0.08, -0.32, 0.34, -0.1), (-0.08, -0.32, 0.34, -0.1)), {"Hips": (0, -0.14, 0)})
    # the trunk
    P["spine arch (back up)"] = ({"Spine1": (-0.12, 0, 0), "Spine2": (-0.14, 0, 0), "Chest": (-0.10, 0, 0)}, None)
    P["spine sag (back down)"] = ({"Spine1": (0.12, 0, 0), "Spine2": (0.14, 0, 0), "Chest": (0.10, 0, 0)}, None)
    P["spine bend left"] = ({"Spine1": (0, 0.14, 0), "Spine2": (0, 0.16, 0), "Chest": (0, 0.12, 0)}, None)
    P["spine twist (roll)"] = ({"Spine1": (0, 0, 0.10), "Spine2": (0, 0, 0.12), "Chest": (0, 0, 0.10)}, None)
    P["breath in (chest up)"] = ({"Spine2": (-0.03, 0, 0), "Chest": (-0.05, 0, 0), "Neck1": (0.04, 0, 0)}, {"Chest": (0, 0.01, 0)})
    # neck and head
    P["neck up"] = ({"Neck1": (0.30, 0, 0), "Neck2": (0.25, 0, 0), "Head": (0.15, 0, 0)}, None)
    P["neck down (grazing)"] = ({"Neck1": (-0.40, 0, 0), "Neck2": (-0.35, 0, 0), "Head": (-0.25, 0, 0)}, None)
    P["neck and head left"] = ({"Neck1": (0, 0.25, 0), "Neck2": (0, 0.30, 0), "Head": (0, 0.35, 0.10)}, None)
    P["head nod down"] = ({"Head": (-0.45, 0, 0)}, None)
    P["head nod up"] = ({"Head": (0.45, 0, 0)}, None)
    P["jaw open 6 deg"] = ({"Jaw": (-0.105, 0, 0)}, None)
    P["jaw open 12 deg"] = ({"Jaw": (-0.21, 0, 0)}, None)
    P["jaw open 20 deg"] = ({"Jaw": (-0.35, 0, 0)}, None)
    P["EXTREME head nod down 0.6"] = ({"Head": (-0.6, 0, 0)}, None)
    P["EXTREME head nod up 0.6"] = ({"Head": (0.6, 0, 0)}, None)
    P["EXTREME head yaw 0.7 + roll 0.4"] = ({"Head": (0, 0.7, 0.4)}, None)
    P["EXTREME antlers out 0.5 / aft 0.5"] = ({"AntlerL1": (0.5, 0, 0.5), "AntlerL2": (0.3, 0, 0.3), "AntlerR1": (0.5, 0, -0.5), "AntlerR2": (0.3, 0, -0.3)}, None)
    P["EXTREME antlers in 0.5 / fore 0.5"] = ({"AntlerL1": (-0.5, 0, -0.5), "AntlerL2": (-0.3, 0, -0.3), "AntlerR1": (-0.5, 0, 0.5), "AntlerR2": (-0.3, 0, 0.3)}, None)
    P["EXTREME tail curl up (0.45 each)"] = ({"Tail1": (-0.35, 0, 0), "Tail2": (-0.45, 0, 0), "Tail3": (-0.55, 0, 0), "Tail4": (-0.6, 0, 0)}, None)
    P["EXTREME tail S (yaw +-0.5)"] = ({"Tail1": (0, 0.35, 0), "Tail2": (0, -0.5, 0), "Tail3": (0, 0.6, 0), "Tail4": (0, -0.6, 0)}, None)
    P["EXTREME neck all up (0.35,0.6,0.5)"] = ({"Neck1": (0.35, 0, 0), "Neck2": (0.6, 0, 0), "Head": (0.5, 0, 0)}, None)
    P["EXTREME neck all down (-0.6,-0.8,-0.5)"] = ({"Neck1": (-0.6, 0, 0), "Neck2": (-0.8, 0, 0), "Head": (-0.5, 0, 0)}, None)
    P["head tilt (roll)"] = ({"Head": (0, 0, 0.30)}, None)
    # antlers
    P["antlers sway out (L out, R out)"] = ({"AntlerL1": (0, 0, 0.12), "AntlerL2": (0, 0, 0.10), "AntlerR1": (0, 0, -0.12), "AntlerR2": (0, 0, -0.10)}, None)
    P["antlers sway in"] = ({"AntlerL1": (0, 0, -0.12), "AntlerL2": (0, 0, -0.10), "AntlerR1": (0, 0, 0.12), "AntlerR2": (0, 0, 0.10)}, None)
    P["antlers fore"] = ({"AntlerL1": (-0.14, 0, 0), "AntlerL2": (-0.12, 0, 0), "AntlerR1": (-0.14, 0, 0), "AntlerR2": (-0.12, 0, 0)}, None)
    P["antlers aft"] = ({"AntlerL1": (0.14, 0, 0), "AntlerL2": (0.12, 0, 0), "AntlerR1": (0.14, 0, 0), "AntlerR2": (0.12, 0, 0)}, None)
    # tail
    P["tail swish left"] = ({"Tail1": (0, 0.20, 0), "Tail2": (0, 0.25, 0), "Tail3": (0, 0.30, 0), "Tail4": (0, 0.30, 0)}, None)
    P["tail swish right"] = ({"Tail1": (0, -0.20, 0), "Tail2": (0, -0.25, 0), "Tail3": (0, -0.30, 0), "Tail4": (0, -0.30, 0)}, None)
    P["tail up"] = ({"Tail1": (-0.15, 0, 0), "Tail2": (-0.25, 0, 0), "Tail3": (-0.30, 0, 0), "Tail4": (-0.30, 0, 0)}, None)
    P["tail down"] = ({"Tail1": (0.15, 0, 0), "Tail2": (0.20, 0, 0), "Tail3": (0.20, 0, 0), "Tail4": (0.20, 0, 0)}, None)
    # whole-body poses
    P["bow (front down)"] = ({**legs((0.35, -1.2, 0.8, 0.2), (0.35, -1.2, 0.8, 0.2), (0, 0, 0, 0), (0, 0, 0, 0)), "Spine2": (0.10, 0, 0), "Chest": (0.15, 0, 0),
                              "Neck1": (-0.25, 0, 0), "Neck2": (-0.25, 0, 0), "Head": (-0.15, 0, 0)}, {"Chest": (0, -0.25, 0)})
    P["roar (head up)"] = ({"Spine1": (-0.04, 0, 0), "Spine2": (-0.06, 0, 0), "Chest": (-0.08, 0, 0), "Neck1": (0.36, 0, 0), "Neck2": (0.32, 0, 0), "Head": (0.30, 0, 0),
                            "AntlerL1": (-0.08, 0, -0.06), "AntlerR1": (-0.08, 0, 0.06), "Tail1": (-0.15, 0, 0), "Tail2": (-0.2, 0, 0)}, None)
    return P


CAM_FULL = dict(target=(0, 0.1, 1.25), scale=4.5)
CAM_HEAD = dict(target=(0, -0.95, 1.95), scale=2.5)
CAM_ANT = dict(target=(0, -1.0, 2.2), scale=2.2)
CAM_TAIL = dict(target=(0, 1.1, 1.1), scale=2.8)
V3 = [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1)]
POSE_GROUPS = [
    ("legs1", ["rest", "trot A (FL BR forward, FR BL back)", "trot B (FR BL forward, FL BR back)"], CAM_FULL, V3),
    ("legs2", ["lifted paws FL + BR", "knees 60 deg (all legs)", "knees 90 deg (all legs)"], CAM_FULL, V3),
    ("legs3", ["planted crouch (heavy plant)", "bow (front down)", "roar (head up)"], CAM_FULL, V3),
    ("trunk1", ["spine arch (back up)", "spine sag (back down)", "spine bend left"], CAM_FULL, [(1, 0, 0.06), (0, 0, 1), (0, -1, 0.1)]),
    ("trunk2", ["spine twist (roll)", "breath in (chest up)", "rest"], CAM_FULL, [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1)]),
    ("neck1", ["neck up", "neck down (grazing)", "neck and head left"], CAM_HEAD, [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, 0, 1)]),
    ("neck2", ["head nod down", "head nod up", "head tilt (roll)"], CAM_HEAD, [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1)]),
    ("ext_head", ["EXTREME head nod down 0.6", "EXTREME head nod up 0.6", "EXTREME head yaw 0.7 + roll 0.4"], CAM_HEAD, [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1)]),
    ("ext_antlers", ["EXTREME antlers out 0.5 / aft 0.5", "EXTREME antlers in 0.5 / fore 0.5", "rest"], CAM_ANT, [(1, 0, 0.06), (0, -1, 0.1), (0, 0, 1)]),
    ("ext_tail", ["EXTREME tail curl up (0.45 each)", "EXTREME tail S (yaw +-0.5)", "rest"], CAM_TAIL, [(1, 0, 0.06), (0, 0, 1), (0.65, 0.75, 0.3)]),
    ("ext_neck", ["EXTREME neck all up (0.35,0.6,0.5)", "EXTREME neck all down (-0.6,-0.8,-0.5)", "rest"], CAM_HEAD, [(1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1)]),
    ("jaw", ["jaw open 6 deg", "jaw open 12 deg", "jaw open 20 deg"], dict(target=(0, -1.35, 1.8), scale=1.3), [(1, 0, 0.0), (0.65, -0.75, 0.2), (0, -1, 0.0)]),
    ("antlers1", ["antlers sway out (L out, R out)", "antlers sway in", "rest"], CAM_ANT, [(1, 0, 0.06), (0, -1, 0.1), (0, 0, 1)]),
    ("antlers2", ["antlers fore", "antlers aft", "roar (head up)"], CAM_ANT, [(1, 0, 0.06), (0, -1, 0.1), (0, 0, 1)]),
    ("tail1", ["tail swish left", "tail swish right", "tail up"], CAM_TAIL, [(1, 0, 0.06), (0, 0, 1), (0.65, 0.75, 0.3)]),
    ("tail2", ["tail down", "rest", "tail up"], CAM_TAIL, [(1, 0, 0.06), (0, 0, 1), (0.65, 0.75, 0.3)]),
]


def run_pose_sheets(P):
    for gname, names, cam, views in POSE_GROUPS:
        paths = []
        for pn in names:
            spec, move = P[pn]
            for k, v in enumerate(views):
                pose(RIG, spec, move)
                p = os.path.join(REVIEW, "tmp_%s_%d_%d.png" % (gname, len(paths), k))
                shoot(p, v, 640, **cam)
                paths.append(p)
        sheet(paths, os.path.join(REVIEW, "poses_%s.png" % gname), len(views))
        print("SHEET poses_%s.png rows top to bottom:" % gname, names, flush=True)
    pose(RIG, {})


def run_closeups():
    """Joints close up at the poses a gait uses and the extremes: the elbow, the stifle and hock, the shoulder, the hip, the foot."""
    cases = [
        ("FL lifted (hip +0.55, elbow -1.0, wrist +0.55, foot +0.25)", {"LegFL1": (0.55, 0, 0), "LegFL2": (-1.0, 0, 0), "LegFL3": (0.55, 0, 0), "FootFL": (0.25, 0, 0)}, None, dict(target=(0.2, -0.5, 0.75), scale=1.7)),
        ("BL lifted (hip +0.5, stifle -0.9, hock +0.9, foot +0.3)", {"LegBL1": (0.5, 0, 0), "LegBL2": (-0.9, 0, 0), "LegBL3": (0.9, 0, 0), "FootBL": (0.3, 0, 0)}, None, dict(target=(0.2, 0.3, 0.75), scale=1.7)),
        ("FL swung forward 0.6 / BL swung back 0.6 (shoulder and hip)", {"LegFL1": (0.6, 0, 0), "LegBL1": (-0.6, 0, 0)}, None, dict(target=(0.2, -0.1, 0.9), scale=2.8)),
        ("FL swung back 0.5 / BL swung forward 0.7", {"LegFL1": (-0.5, 0, 0), "LegBL1": (0.7, 0, 0)}, None, dict(target=(0.2, -0.1, 0.9), scale=2.8)),
    ]
    for k, (title, spec, move, cam) in enumerate(cases):
        paths = []
        for j, v in enumerate(((1, 0, 0.05), (0.7, -0.7, 0.25), (-0.7, -0.7, 0.25))):
            pose(RIG, spec, move)
            p = os.path.join(REVIEW, "tmp_c_%d_%d.png" % (k, j))
            shoot(p, v, 640, **cam)
            paths.append(p)
        sheet(paths, os.path.join(REVIEW, "closeup_%d.png" % (k + 1)), 3)
        print("CLOSEUP %d: %s" % (k + 1, title), flush=True)
    pose(RIG, {})


def run_rest_compare():
    """The old jointed model and the rigged one, at rest, in the same three views: they must match."""
    if OLD.name not in [c.name for c in scene.collection.children]:
        scene.collection.children.link(OLD)
    for o in OLD.objects:
        if "_Pivot_" in o.name or "_Point_" in o.name:
            o.hide_render = o.hide_viewport = True
    pose(RIG, {})
    paths = []
    for which in ("old", "rigged"):
        for lc in bpy.context.view_layer.layer_collection.children:
            lc.exclude = (lc.name != (OLD.name if which == "old" else GAME.name))
        for j, v in enumerate(((1, 0, 0.06), (0.65, -0.75, 0.3), (0, -1, 0.1))):
            p = os.path.join(REVIEW, "tmp_rc_%s_%d.png" % (which, j))
            shoot(p, v, 640, **CAM_FULL)
            paths.append(p)
    sheet(paths, os.path.join(REVIEW, "rest_old_vs_rigged.png"), 3)
    only_game(True)


def run_weight_sheets():
    weight_view(True)
    pose(RIG, {})
    paths = []
    for k, (v, cam) in enumerate((((1, 0, 0.06), CAM_FULL), ((0, -1, 0.1), CAM_FULL), ((0.65, -0.75, 0.3), CAM_FULL), ((1, 0, 0.1), CAM_HEAD), ((0.65, -0.75, 0.3), CAM_HEAD), ((0, 1, 0.12), CAM_FULL))):
        p = os.path.join(REVIEW, "tmp_w_%d.png" % k)
        shoot(p, v, 640, **cam)
        paths.append(p)
    sheet(paths, os.path.join(REVIEW, "weights.png"), 3)
    weight_view(False)


# ======================================================================================================================================
# the files: the .blend (the rigged collection added), the FBX, the preview data
# ======================================================================================================================================
def read_png(path):
    """8-bit RGB or RGBA PNG (non-interlaced) -> (h, w, 3) uint8: the baked colour maps, read from the files in assets/ themselves."""
    import zlib
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w = 8, b"", 0
    while pos < len(raw):
        n = struct.unpack(">I", raw[pos:pos + 4])[0]
        kind = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and inter == 0, (depth, ctype, inter)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    ch = 3 if ctype == 2 else 4
    data = np.frombuffer(zlib.decompress(idat), dtype=np.uint8).reshape(h, 1 + w * ch)
    rows = np.zeros((h, w * ch), dtype=np.int32)
    prev = np.zeros(w * ch, dtype=np.int32)
    for y in range(h):
        f, line = data[y, 0], data[y, 1:].astype(np.int32)
        if f == 0:
            cur = line
        elif f == 1:
            cur = line.copy()
            for x in range(ch, w * ch):
                cur[x] = (cur[x] + cur[x - ch]) & 255
        elif f == 2:
            cur = (line + prev) & 255
        elif f == 3:
            cur = line.copy()
            for x in range(w * ch):
                left = cur[x - ch] if x >= ch else 0
                cur[x] = (cur[x] + ((left + prev[x]) >> 1)) & 255
        else:
            cur = line.copy()
            for x in range(w * ch):
                a = cur[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (cur[x] + pr) & 255
        rows[y] = cur
        prev = cur
    return rows.reshape(h, w, ch)[:, :, :3].astype(np.uint8)


def scan_file(path):
    raw = open(path, "rb").read()
    if raw[:4] == b"\x28\xb5\x2f\xfd":
        raw = subprocess.run(["zstd", "-dc", path], capture_output=True).stdout
    return {pat.decode(): raw.count(pat) for pat in machine_patterns() if pat in raw}


def write_blend():
    """The rigged collection joins the old ones in Crysalith_Final.blend (written from the datablocks alone, not the window manager, which remembers
    this machine's folders). Every path is relative, and the path fields are filled to their end before they are cleared."""
    keep = {OLD, bpy.data.collections["Crysalith_Markers"], bpy.data.collections["Crysalith_Source"], GAME}
    for img in bpy.data.images:
        rel = img.filepath_raw
        if rel and not rel.startswith("//"):
            rel = "//" + os.path.basename(rel)
        if img.filepath_raw:
            img.filepath_raw = "//" + "_" * 1020
            img.filepath_raw = rel
        for packed in img.packed_files:
            packed.filepath = "//" + "_" * 1020
            packed.filepath = rel
    tmp = SOURCE + ".new"
    if os.path.exists(tmp):
        os.remove(tmp)
    bpy.data.libraries.write(tmp, keep, path_remap="RELATIVE_ALL", compress=True)
    os.replace(tmp, SOURCE)
    return scan_file(SOURCE)


def export_fbx(rig):
    """The FBX: the rigged pieces under the game's own names (the old pieces step aside for the export only), the armature, the maps embedded."""
    pose(rig, {})
    moved = []
    for part in PIECES:
        old = bpy.data.objects[N + part]
        old.name = N + part + "__old"
        moved.append(old)
        g = PIECE[part]
        g.name = N + part
        g.data.name = N + part
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in list(PIECE.values()) + [rig]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    os.makedirs(os.path.dirname(FBX_OUT), exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=FBX_OUT, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False,
                             use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X")
    for part in PIECES:
        g = PIECE[part]
        g.name = GAME_NAME[part]
        g.data.name = GAME_NAME[part]
    for old in moved:
        old.name = old.name[:-len("__old")]
    raw = open(FBX_OUT, "rb").read()
    home = os.path.expanduser("~").encode() + b"/"
    neutral = b"/Users/" + (b"user" * 8)[:len(home) - len(b"/Users/") - 1] + b"/"      # the same length: the earlier FBX files carry /Users/user/, nothing of this machine's
    fixed = raw.replace(home, neutral) if len(neutral) == len(home) else raw
    if fixed != raw:
        open(FBX_OUT, "wb").write(fixed)
    return os.path.getsize(FBX_OUT)


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def to_game(P):
    """Blender (x, y, z) -> the game's (-x, z, y): a proper rotation (determinant +1), so every triangle keeps its winding."""
    return np.stack([-P[:, 0], P[:, 2], P[:, 1]], axis=1).astype(np.float32)


def vertex_colours(o, part):
    """The baked colour map's colour at each vertex (the average over the vertex's corners), sRGB bytes: a glow piece is one flat colour."""
    n = len(o.data.vertices)
    if "_Glow_" in part:
        h = part.split("_Glow_")[1][:6]
        return np.tile(np.array([int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)], dtype=np.uint8), (n, 1))
    tex = read_png(os.path.join(ROOT, "assets", "pets", EGG, "Crysalith_%s_color.png" % part))
    h, w = tex.shape[:2]
    uv = np.empty(len(o.data.loops) * 2)
    o.data.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    px = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    py = np.clip(((1.0 - uv[:, 1]) * h).astype(int), 0, h - 1)           # (a PNG's first row is the top; the UV's v runs up)
    col = tex[py, px].astype(np.float64)
    vi = np.empty(len(o.data.loops), dtype=np.int64)
    o.data.loops.foreach_get("vertex_index", vi)
    acc = np.zeros((n, 3))
    cnt = np.zeros(n)
    np.add.at(acc, vi, col)
    np.add.at(cnt, vi, 1)
    return np.round(acc / np.maximum(cnt, 1)[:, None]).astype(np.uint8)


def quantise(W):
    """The top four bones per vertex as bytes (indices and weights summing to exactly 255)."""
    idx = np.argsort(-W, axis=1)[:, :4]
    w = np.take_along_axis(W, idx, axis=1)
    q = np.floor(w / w.sum(axis=1, keepdims=True) * 255 + 1e-6).astype(np.int32)
    q[:, 0] += 255 - q.sum(axis=1)
    return idx.astype(np.uint8), q.astype(np.uint8)


def write_preview(allW):
    pieces = []
    for part in PIECES:
        o = PIECE[part]
        P = verts(o)
        tris = np.empty(len(o.data.polygons) * 3, dtype=np.uint32)
        o.data.polygons.foreach_get("vertices", tris)
        idx, wq = quantise(allW[part])
        cols = vertex_colours(o, part)
        G = to_game(P)
        # the triangles as Blender winds them, outward; the mapping keeps that, checked against the piece's own middle
        T = tris.reshape(-1, 3)
        nrm = np.cross(G[T[:, 1]] - G[T[:, 0]], G[T[:, 2]] - G[T[:, 0]])
        nb = np.empty(len(o.data.polygons) * 3)
        o.data.polygons.foreach_get("normal", nb)                      # Blender's own face normals (outward), turned into the game's axes
        want = to_game(nb.reshape(-1, 3))
        out = ((nrm * want).sum(axis=1) > 0).mean()
        glow = part.split("_Glow_")[1][:6] if "_Glow_" in part else None
        pieces.append((N + part, glow, G, T.astype(np.uint32), cols, idx, wq, float(out)))
    for k, (name, glow, G, T, cols, idx, wq, out) in enumerate(pieces):       # the pure-Python decode check
        for tag, arr, dt in (("Verts", G, "<f4"), ("Tris", T, "<u4"), ("Cols", cols, "u1"), ("BoneIdx", idx, "u1"), ("Wts", wq, "u1")):
            raw = base64.b64decode(b64(arr))
            back = struct.unpack("<%d%s" % (arr.size, {"<f4": "f", "<u4": "I", "u1": "B"}[dt]), raw)
            assert np.array_equal(np.array(back, dtype=arr.dtype).reshape(arr.shape), arr), (name, tag)
        assert (wq.astype(int).sum(axis=1) == 255).all(), name
    lines = ["-- Written by tools/blender/pets/crysalith_rig.py: a PREVIEW of the rigged Crysalith for loading in Studio (temporary, never committed).",
             "-- Game axes (x = -blender x, y = blender z, z = blender y), metres, ground at y = 0. Winding as Blender wrote it (counter-clockwise from outside).",
             "return {", '    Pet = "Crysalith",', "    Bones = {"]
    for name, head, tail, parent in BONES:
        lines.append('        { "%s", "%s", %.5f, %.5f, %.5f },' % (name, parent or "", -head.x, head.z, head.y))
    lines += ["    },", "    Pieces = {"]
    for name, glow, G, T, cols, idx, wq, out in pieces:
        lines += ["        {", '            Name = "%s",' % name, '            Glow = %s,' % ('"%s"' % glow if glow else "nil"), "            VertexCount = %d, TriangleCount = %d," % (len(G), len(T)),
                  '            Verts = "%s",' % b64(G), '            Tris = "%s",' % b64(T), '            Cols = "%s",' % b64(cols), '            BoneIdx = "%s",' % b64(idx), '            Wts = "%s",' % b64(wq), "        },"]
    lines += ["    },", "}", ""]
    os.makedirs(os.path.dirname(PREVIEW_OUT), exist_ok=True)
    open(PREVIEW_OUT, "w").write("\n".join(lines))
    return {p[0]: round(p[7], 3) for p in pieces}, os.path.getsize(PREVIEW_OUT)


def rest_check(allW):
    """The rigged pieces at rest equal the old ones, vertex for vertex."""
    pose(RIG, {})
    dg = bpy.context.evaluated_depsgraph_get()
    worst = 0.0
    for part, o in PIECE.items():
        ev = o.evaluated_get(dg).to_mesh()
        a = np.empty(len(ev.vertices) * 3)
        ev.vertices.foreach_get("co", a)
        o.evaluated_get(dg).to_mesh_clear()
        worst = max(worst, float(np.abs(a.reshape(-1, 3) - verts(bpy.data.objects[N + part])).max()))
    return worst


if __name__ == "__main__":
    RIG = skeleton()
    ALLW = bind_all(RIG)
    for o in GAME.objects:
        if o.type == "MESH":
            o.select_set(False)
    if STAGE == "all":
        print("REST vs old pieces: max vertex difference %.2e m" % rest_check(ALLW), flush=True)
        maps_same = True
        for img in bpy.data.images:
            f = os.path.join(ROOT, "assets", "pets", EGG, img.name + ".png")
            if img.packed_file is not None and os.path.exists(f):
                maps_same &= (bytes(img.packed_file.data) == open(f, "rb").read())
        print("MAPS packed in the .blend identical to assets/pets/ExclusiveEgg files:", maps_same, flush=True)
        qa_before = None
        print("WRITE .blend scan:", write_blend(), flush=True)
        print("WRITE FBX bytes:", export_fbx(RIG), "scan:", scan_file(FBX_OUT), flush=True)
        print("WRITE preview module (outward share per piece, bytes):", write_preview(ALLW), flush=True)
    review_setup()
    only_game(True)
    infl = max(len(o.data.vertices[i].groups) for o in PIECE.values() for i in range(len(o.data.vertices)))
    unw = sum(1 for o in PIECE.values() for v in o.data.vertices if not v.groups)
    print("BONES", NB, "TRIS", REST_TRIS, "TOTAL", sum(REST_TRIS.values()), "MAX INFL", infl, "UNWEIGHTED", unw, flush=True)
    todo = ARGS[2:] if len(ARGS) > 2 else ["bones", "weights", "poses"]
    if "table" in todo:
        for name, head, tail, parent in BONES:
            rigid = sum(int((W[:, BI[name]] > 0.999).sum()) for W in ALLW.values())
            blended = sum(int(((W[:, BI[name]] > 0) & (W[:, BI[name]] < 0.999)).sum()) for W in ALLW.values())
            pcs = [k for k, W in ALLW.items() if (W[:, BI[name]] > 0).any()]
            g = lambda v: (round(-v.x, 3), round(v.z, 3), round(v.y, 3))
            print("BONE %-9s %-8s head %s tail %s len %.3f rigid %d blended %d pieces %s" % (name, parent or "-", g(head), g(tail), (tail - head).length, rigid, blended, ",".join(p.replace("_Glow_", "G") for p in pcs)), flush=True)
    if "bones" in todo:
        debug_bones(RIG)
        pose(RIG, {})
        paths = []
        for k, (v, cam) in enumerate((((1, 0, 0.06), CAM_FULL), ((0, -1, 0.1), CAM_FULL), ((1, 0, 0.06), dict(target=(0, -0.1, 0.65), scale=1.9)),
                                      ((1, 0, 0.06), dict(target=(0, 0.75, 0.9), scale=1.9)), ((1, 0, 0.06), CAM_HEAD), ((1, 0, 0.06), dict(target=(0, 1.2, 1.2), scale=1.9)))):
            p = os.path.join(REVIEW, "tmp_rest_%d.png" % k)
            shoot(p, v, 640, xray=True, **cam)
            paths.append(p)
        sheet(paths, os.path.join(REVIEW, "bones_over_mesh.png"), 3)
        debug_bones(RIG, False)
    if "weights" in todo:
        run_weight_sheets()
    if "closeups" in todo:
        run_closeups()
    if "compare" in todo:
        run_rest_compare()
    if "poses" in todo:
        run_pose_sheets(pose_library())
    if "qa" in todo:
        skills = os.environ["BLENDER_SKILLS_DIR"]            # the folder holding blender-asset-qa/ and blender-character-rigging/ (their scripts)
        sys.path.insert(0, os.path.join(skills, "blender-asset-qa", "scripts"))
        sys.path.insert(0, os.path.join(skills, "blender-character-rigging", "scripts"))
        import qa_check
        import rig_check
        pose(RIG, {})
        for o in bpy.data.objects:
            o.select_set(False)
        res = qa_check.run(objects=[o.name for o in PIECE.values()], profile="roblox")
        print("QA pass:", res["pass"], "errors:", len(res["errors"]), "warnings:", len(res["warnings"]), flush=True)
        for e in res["errors"]:
            print("QA ERROR", str(e)[:300], flush=True)
        for w in res["warnings"]:
            print("QA WARN", str(w)[:300], flush=True)
        rc = rig_check.run(armature=RIG.name, meshes=[o.name for o in PIECE.values()], profile="roblox")
        print("RIG_CHECK", json.dumps(rc, default=str)[:3000], flush=True)
    if "diag" in todo:
        SK = Skin(RIG, ALLW)
        FKR = FK(RIG)
        for pn, spec in (("Head x -0.5", {"Head": (-0.5, 0, 0)}), ("Head x +0.5", {"Head": (0.5, 0, 0)}), ("Neck1 x +0.5", {"Neck1": (0.5, 0, 0)}), ("Chest x 0.6", {"Chest": (0.6, 0, 0)}), ("LegFL2 x 1.0", {"LegFL2": (1.0, 0, 0)}), ("LegBL2 x 0.8", {"LegBL2": (0.8, 0, 0)})):
            mats = FKR.skin(spec)
            for part in SOLIDS:
                P, idx, wts, edges, isl = SK.pieces[part]
                Q = SK.deform(part, mats)
                l0 = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1)
                l1 = np.linalg.norm(Q[edges[:, 0]] - Q[edges[:, 1]], axis=1)
                r = l1 / np.maximum(l0, 1e-9)
                bad = np.nonzero(((l1 - l0 > 0.05) & (r > 1.5)) | ((l0 > 0.02) & (r < 0.4)))[0]
                if len(bad):
                    k = bad[np.argmax(np.abs(np.log(r[bad])))]
                    a, b = edges[k]
                    print("DIAG %s %s: %d bad edges; worst l0 %.3f -> %.3f at %s; w(a)=%s w(b)=%s" % (pn, part, len(bad), l0[k], l1[k], tuple(np.round(P[a], 2)),
                          [(BONE_NAMES[i], round(float(w), 2)) for i, w in zip(idx[a], wts[a]) if w > 0.001], [(BONE_NAMES[i], round(float(w), 2)) for i, w in zip(idx[b], wts[b]) if w > 0.001]), flush=True)
    if "limits" in todo or "check" in todo:
        SK = Skin(RIG, ALLW)
        FKR = FK(RIG)
        # the numpy skinning must equal Blender's: one awkward pose, every bone's matrix and a few vertices
        spec = {"LegFL1": (0.3, 0.1, 0.05), "Neck1": (0.2, -0.3, 0.1), "Tail2": (0.1, 0.4, 0.2), "AntlerL1": (0.1, 0.1, -0.2), "Spine2": (0.05, 0.2, 0.1)}
        mv = {"Hips": (0.02, -0.1, 0.03)}
        pose(RIG, spec, mv)
        mats_blender = SK.bone_mats()
        mats_np = FKR.skin(spec, mv)
        print("FK vs Blender: max matrix difference %.2e" % float(np.abs(mats_blender - mats_np).max()), flush=True)
        dev = o_dev = 0.0
        dg = bpy.context.evaluated_depsgraph_get()
        for part in ("Body", "LegFL", "Antlers", "Tail", "Head"):
            ev = PIECE[part].evaluated_get(dg).to_mesh()
            a = np.empty(len(ev.vertices) * 3)
            ev.vertices.foreach_get("co", a)
            o_dev = max(o_dev, float(np.abs(a.reshape(-1, 3) - SK.deform(part, mats_np)).max()))
            PIECE[part].evaluated_get(dg).to_mesh_clear()
        print("numpy skin vs Blender mesh: max vertex difference %.2e m" % o_dev, flush=True)
        pose(RIG, {})
        if "limits" in todo:
            lim = safe_limits(RIG, SK, FKR)
            json.dump(lim, open(os.path.join(REVIEW, "safe_limits.json"), "w"), indent=1)
            for name, d in lim.items():
                print("LIMIT %-9s %s" % (name, "  ".join("%s %.3f" % (k, v[0]) for k, v in d.items())), flush=True)
        P = pose_library()
        print("POSE STRETCH (worst edge gain m / ratio / most crushed ratio):", flush=True)
        for pn, (spec, move) in P.items():
            w = SK.stretch(mats=FKR.skin(spec, move))
            print("  %-40s gain %.3f x%.2f crush %.2f %s" % (pn, w["gain"], w["ratio"], w["crush"], w["part"]), flush=True)

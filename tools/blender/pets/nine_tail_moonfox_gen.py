"""The Nine-Tail Moonfox (Secret; Exclusive Egg), built from the owner's high-detail sculpt of their concept
(assets/concepts/generated/Moonfox_shape.glb; the concept sheet is assets/concepts/ExclusivePets.png, top row, and its views are in
assets/concepts/views/Moonfox/).

A fox spirit, large and grand: pale lavender-white, shaded in soft lavender to violet; a tall spiky mane and ruff, slim legs with small dark
claws, blue eyes, a dark nose and lips, and nine thick brush tails fanned wide like a peacock's. Its coat is soft, layered fur: a fluffy ruff, clumped fur on its
chest and legs, the clumps' relief carried by the normal map, violet gathering in the crevices between them and on the undersides of its tails,
the tails darker toward their roots.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/nine_tail_moonfox_gen.py -- [rig|all] [review dir]

rig: the game mesh and skeleton, posed and checked, in clay. all: also the paint, the unwrap, the bake, the review renders, the .blend and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, paws on z = 0. +X is its left. The maps and the FBX go to assets/pets/ExclusiveEgg/.

How the sculpt is turned into the pet:
- the sculpt is turned to face -Y, centred between its paws and stood on z = 0; its two loose specks are dropped, and its surface is smoothed
  just enough to take out the fine stair-steps of the grid it was made on, which would print into the normal map as a woven texture;
- its eyes were closed slits: each is opened into an almond, the groove filled, a low eyeball dome and a lid crease sculpted in (the normal
  map takes them), and painted per texel: blue iris, dark pupil, liner and a catch-light;
- the game mesh is a 4 mm voxel copy (which unions whatever passes through itself and drops the inside specks it finds) collapsed to the
  budget: it kept the tails, ears and mane spikes far better than QuadriFlow, which cut whole tail edges and spikes off at this budget;
- the tails: the sculpt's own (thin petal sheets, nine with four stubs at the root) are cut away and the rump closed and smoothed over their
  place. Nine brush tails are built in their stead, as plumes: each leaves the rump heading back and turns steadily up and over in a
  crescent, its tip hooking forward and curling up like a flame (the outer tails shorter and more curled); slim at the root, fullest two
  thirds out. Each is a soft core and ten overlapping fur locks (tubes along it): most run along its edges, their ends flaring off toward the
  tip so the outline is layered fur; two round out its faces; two part off beside the tip, so it ends in three flames. One bundle leaves the
  rump, fanned evenly (Tail1 its left to Tail9 its right, seen from behind; Tail5, the centre, highest), the even tails a layer behind the
  odd ones so that past the bundle no tail touches another, at rest or posed. Three bones per tail and a bone at each tip.
"""
import heapq
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "rig"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "NineTailMoonfox"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "ExclusiveEgg")
SCULPT = os.path.join(pet_kit.ROOT, "assets", "concepts", "generated", "Moonfox_shape.glb")
CONCEPT_SIDE = os.path.join(pet_kit.ROOT, "assets", "concepts", "views", "Moonfox", "1_side.png")
TARGET_TRIS = 19600
VOXEL = 0.004

# ---------- colours (sRGB 0-255, after the concept sheet) ----------
FUR_LIGHT = rgb(248, 247, 255)        # its lit coat: white with a breath of lavender
FUR = rgb(232, 230, 252)
FUR_SHADE = rgb(204, 199, 244)        # the coat turned away from the light
CREASE = rgb(156, 140, 228)           # violet between the fur clumps
DEEP = rgb(134, 118, 214)              # deep violet in the deepest folds and under the tails
TAIL_TOP = rgb(222, 222, 255)
TAIL_UNDER = rgb(180, 174, 240)
TAIL_ROOT = rgb(166, 154, 232)
TAIL_TIP = rgb(244, 244, 255)
EAR_IN = rgb(184, 172, 240)
NOSE = rgb(52, 44, 80)
NOSE_LIT = rgb(84, 76, 116)
LIP = rgb(58, 46, 92)
CLAW = rgb(50, 44, 74)
IRIS_DEEP, IRIS, IRIS_LIT = rgb(34, 52, 168), rgb(62, 108, 236), rgb(140, 196, 255)
PUPIL = rgb(16, 16, 40)
LINER = rgb(44, 34, 92)
GLINT = rgb(255, 255, 255)

# ---------- where things are on the sculpt (metres, after it is turned and centred; measured from it) ----------
# each eye's groove: its middle, the line it runs along (front-low to back-high: a fox's slant), and the way it faces
EYE_CENTRE, EYE_ALONG, EYE_FACING = Vector((0.0625, -0.873, 1.081)), Vector((0.40, 0.82, 0.40)), Vector((0.80, -0.45, 0.12))
EYE_HALF, EYE_UP, EYE_LOW = 0.029, 0.0115, 0.0068     # half its length; how far its upper and lower lids reach from its line
MUZZLE = Vector((0.0, -0.935, 1.02))                   # the middle of its muzzle (nose and lips are painted from the sculpt's own shapes there)
LIP_ZONE = ((-0.935, -0.858), (0.982, 1.016), (0.022, 0.058))     # y, z, |x|: the mouth's corner groove on each side
TAIL_START_Y = -0.12                                   # its tails leave the rump about here
# its bones' heads (the left side; the right mirrors it). Measured on orthographic views of the sculpt.
TRUNK = (("Hips", (0, -0.17, 0.60), "Root"), ("Spine", (0, -0.33, 0.63), "Hips"), ("Chest", (0, -0.50, 0.66), "Spine"),
         ("Neck", (0, -0.62, 0.80), "Chest"), ("Head", (0, -0.72, 1.06), "Neck"))
HEAD_END = (0, -0.93, 1.08)
LEGS = {"F": ((0.095, -0.64, 0.64), (0.105, -0.62, 0.42), (0.106, -0.715, 0.11), (0.11, -0.765, 0.045), (0.11, -0.84, 0.02)),
        "B": ((0.075, -0.17, 0.58), (0.065, -0.25, 0.42), (0.055, -0.155, 0.27), (0.066, -0.215, 0.05), (0.066, -0.30, 0.02))}
EAR_BASE = (0.072, -0.715, 1.20)


def mirror_x(p, side):
    return Vector((p[0] * side, p[1], p[2]))


# ---------- the sculpt ----------
def load_sculpt():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SCULPT)
    new = [o for o in bpy.data.objects if o not in before]
    hi = next(o for o in new if o.type == "MESH")
    hi.data.transform(hi.matrix_world)
    hi.parent = None
    hi.matrix_world = Matrix.Identity(4)
    for o in new:
        if o is not hi:
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(hi.users_collection):
        c.objects.unlink(hi)
    HI.objects.link(hi)
    hi.name = hi.data.name = N + "Sculpt"
    for m in list(hi.data.materials):
        hi.data.materials.clear()
    hi.data.transform(Matrix.Rotation(math.radians(90), 4, "Z"))      # it faced -X
    dropped = keep_largest(hi)
    P = verts(hi)
    x0 = P[int(np.argmin(P[:, 1])), 0]          # its midline: through the tip of its nose (its eyes and paws agree within 3 mm; a stray low tuft skews the paws)
    hi.data.transform(Matrix.Translation((-x0, 0, 0)))
    apply_mods(hi, [("SMOOTH", {"factor": 0.5, "iterations": 12})])    # the grid's stair-steps out, the fur clumps kept
    P = verts(hi)
    hi.data.transform(Matrix.Translation((0, 0, -P[:, 2].min())))
    print("SCULPT faces", len(hi.data.polygons), "loose pieces dropped", dropped, "midline shift", round(x0, 4), "dims", tuple(round(v, 3) for v in hi.dimensions), flush=True)
    return hi


def keep_largest(o):
    """Drops every loose piece but the largest. Returns the dropped pieces' vertex counts."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen = np.zeros(len(bm.verts), dtype=bool)
    bm.verts.ensure_lookup_table()
    groups = []
    for v in bm.verts:
        if seen[v.index]:
            continue
        stack, group = [v], []
        seen[v.index] = True
        while stack:
            u = stack.pop()
            group.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if not seen[w.index]:
                    seen[w.index] = True
                    stack.append(w)
        groups.append(group)
    groups.sort(key=len, reverse=True)
    bmesh.ops.delete(bm, geom=[v for g in groups[1:] for v in g], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    return [len(g) for g in groups[1:]]


def edge_array(me):
    e = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", e)
    return e.reshape(-1, 2)


def neighbour_mean(X, E, deg):
    s = np.zeros_like(X)
    np.add.at(s, E[:, 0], X[E[:, 1]])
    np.add.at(s, E[:, 1], X[E[:, 0]])
    return s / np.maximum(deg, 1)[:, None]


class EyeFrame:
    """An eye's frame on the surface: a along its slit (front to back), b up across it, w out of the head."""

    def __init__(self, side, tree):
        self.side = side
        c = mirror_x(EYE_CENTRE, side)
        w = mirror_x(EYE_FACING, side).normalized()
        loc, nrm, _, _ = tree.ray_cast(c + w * 0.05, -w, 0.12)
        self.c = loc if loc else c
        a = mirror_x(EYE_ALONG, side)
        a = (a - w * a.dot(w)).normalized()
        b = w.cross(a).normalized()
        if b.z < 0:
            b = -b
        self.a, self.b, self.w = a, b, w

    def local(self, P):
        d = P - np.array(self.c)
        return d @ np.array(self.a), d @ np.array(self.b), d @ np.array(self.w)


def almond(u, v):
    """Inside > 0, in metres to the lids' edge (negative outside): the eye's open shape, its upper lid flatter and higher, its outer corner lifted."""
    s = np.clip(u / EYE_HALF, -1, 1)
    top = EYE_UP * (1 - s * s) ** 0.55 + 0.0025 * s           # (the outer corner lifted a little more: a fox's slant, not a frown)
    bot = -EYE_LOW * (1 - s * s) ** 0.85 + 0.0018 * s
    inside = np.minimum(top - v, v - bot)
    ends = (EYE_HALF - np.abs(u)) * 0.45
    return np.minimum(inside, ends)


def shape_face(hi):
    """Opens the sculpt's closed eye slits: the region is made finer (so the bake can hold a crisp eye), the groove filled, an eyeball dome and a
    lid crease sculpted in. The muzzle is made finer too, so its nose and lip paint are sharp."""
    tree = BVHTree.FromObject(hi, bpy.context.evaluated_depsgraph_get())
    frames = {"L": EyeFrame(1, tree), "R": EyeFrame(-1, tree)}
    zones = [(fr.c, 0.05) for fr in frames.values()] + [(MUZZLE, 0.085)]
    bm = bmesh.new()
    bm.from_mesh(hi.data)
    for _ in range(2):
        edges = [e for e in bm.edges if any((e.verts[0].co - c).length < r and (e.verts[1].co - c).length < r for c, r in zones)]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(hi.data)
    bm.free()
    me = hi.data
    P = verts(hi)
    E = edge_array(me)
    deg = np.bincount(E.ravel(), minlength=len(P)).astype(float)
    move = np.zeros(len(P))
    for fr in frames.values():
        d = np.linalg.norm(P - np.array(fr.c), axis=1)
        move = np.maximum(move, smooth(0.042, 0.026, d))
    for _ in range(30):                                       # fill the slits
        P = P + (neighbour_mean(P, E, deg) - P) * (0.5 * move)[:, None]
    for fr in frames.values():
        u, v, d = fr.local(P)
        near = (np.abs(u) < 0.05) & (np.abs(v) < 0.04) & (np.abs(d) < 0.02)
        e = almond(u[near], v[near])
        out = np.maximum(-e, 0)
        dome = np.where(e > 0, -0.0007 + 0.0021 * smooth(0.0, 0.007, e), 0.0)          # the eyeball, sunk under its lids at the edge
        rim = 0.0009 * np.exp(-((out - 0.0011) / 0.0011) ** 2) * (e <= 0)             # the lids' rims
        crease = -0.0011 * np.exp(-((out - 0.0042) / 0.0016) ** 2) * (v[near] > 0)     # the fold over the upper lid
        P[near] += np.outer(dome + rim + crease, np.array(fr.w))
    set_verts(hi, P)
    print("FACE shaped: sculpt now", len(me.polygons), "faces", flush=True)
    return frames


# ---------- the sculpt's own tails come off ----------
STRIP_SHARE = 0.35      # a point of the sculpt goes when its tail bones carry more than this of it


def strip_tails(hi):
    """The sculpt's tails are thin petal sheets, thirteen of them counting the stubs at the root: all come off, to be replaced by nine brush
    tails built here. A first rig is made only to tell tail from body: its bones' weights are carried onto the sculpt, everything the tail
    bones carry is deleted, scraps left loose are dropped, and the hole in the rump is closed (the new tails' root mound covers it)."""
    body = game_mesh(hi)
    chains = tail_chains(body)
    rig = skeleton(chains)
    bind_heat(rig, body)
    dt = hi.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = body
    dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"
    dt.layers_vgroup_select_dst = "NAME"
    select_only([hi])
    bpy.ops.object.datalayout_transfer(modifier=dt.name)
    bpy.ops.object.modifier_apply(modifier=dt.name)
    tail_groups = {g.index for g in hi.vertex_groups if g.name.startswith("Tail") and g.name != "TailRoot"}
    share = np.zeros(len(hi.data.vertices))
    for v in hi.data.vertices:
        share[v.index] = sum(g.weight for g in v.groups if g.group in tail_groups)
    bm = bmesh.new()
    bm.from_mesh(hi.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(share > STRIP_SHARE)[0]], context="VERTS")
    bm.to_mesh(hi.data)
    bm.free()
    hi.vertex_groups.clear()
    scraps = keep_largest(hi)
    bm = bmesh.new()
    bm.from_mesh(hi.data)
    edges = [e for e in bm.edges if e.is_boundary]
    hole = np.array([tuple(v.co) for e in edges for v in e.verts]) if edges else np.zeros((1, 3))
    for _ in range(4):           # closed and manifold before the voxel copy (an open or pinched edge there and the copy comes back in scraps)
        bad = [e for e in bm.edges if len(e.link_faces) > 2]
        if bad:
            bmesh.ops.delete(bm, geom=list({f for e in bad for f in e.link_faces}), context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        edges = [e for e in bm.edges if e.is_boundary]
        if not edges and not bad:
            break
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)     # (holes_fill left this ragged rim open)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    open_edges = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(hi.data)
    bm.free()
    assert open_edges == 0, "the rump would not close: %d open or pinched edges" % open_edges
    for o in (body, rig):
        bpy.data.objects.remove(o, do_unlink=True)
    # an even 3 mm skin, then the rump round the old hole smoothed out: the flat patch over the hole and the scraps of petal round it go
    closed = hi.data.copy()
    for size in (0.003, 0.0032, 0.0028, 0.0035):
        hi.data = closed.copy()
        apply_mods(hi, [("REMESH", {"mode": "VOXEL", "voxel_size": size, "adaptivity": 0.0})])
        keep_largest(hi)
        if len(hi.data.polygons) > 200000:
            break
        print("STRIP voxel copy at %.4f came back in pieces (%d faces): again" % (size, len(hi.data.polygons)), flush=True)
    assert len(hi.data.polygons) > 200000, "the stripped body's voxel copy failed"
    bpy.data.meshes.remove(closed)
    P = verts(hi)
    kd = KDTree(len(hole))
    for i, q in enumerate(hole):
        kd.insert(q, i)
    kd.balance()
    near = np.array([kd.find(p)[2] for p in P])
    w = smooth(0.09, 0.03, near) * (P[:, 1] > -0.32) * (P[:, 2] > 0.36)
    E = edge_array(hi.data)
    deg = np.bincount(E.ravel(), minlength=len(P)).astype(float)
    for _ in range(60):
        P = P + (neighbour_mean(P, E, deg) - P) * (0.6 * w)[:, None]
    set_verts(hi, P)
    print("STRIP old tail chains found", len(chains), "points removed", int((share > STRIP_SHARE).sum()), "scraps dropped", len(scraps),
          "hole rim points", len(hole), "hole spans", tuple(np.round(hole.min(0), 3)), tuple(np.round(hole.max(0), 3)), flush=True)
    return hole


# ---------- nine brush tails ----------
FAN_ROOT = Vector((0.0, -0.26, 0.58))      # where all nine start, sunk in the rump, leaving it as one bundle
TAIL_SPREAD = [116.0]                      # degrees either side of straight up, seen from behind: where the outermost tails head
TAIL_LAYER = [0.42]                        # the even tails (2, 4, 6, 8) run this far behind the odd ones (1, 3, 5, 7, 9), a layer back, so neighbours never touch
# each tail by its place from the centre (0, the centre, to 4, the outermost pair; mirrored either side):
TAIL_LENGTH = [1.46, 1.42, 1.36, 1.27, 1.16]          # metres: the outer tails shorter
TAIL_TURN = [(18, 168), (18, 160), (16, 146), (14, 132), (12, 122)]     # its heading, in degrees from straight back toward its place in the fan,
#                                                       at the root and at the tip: past 90 it hooks forward; a crescent
TAIL_CURL = [0.3, 0.45, 0.62, 0.82, 1.05]             # how much its last third lifts its tip up, like a flame: the outer tails curl most
TAIL_FAT = [0.181, 0.178, 0.174, 0.166, 0.158]        # its greatest half-width, about two thirds of the way out
TAIL_FLAT = [0.9]                                      # thickness across the fan against width
ROOT_ZONE = 0.4                                        # the first part of each tail is the bundle they share at the root; past it no tail may touch another


def tail_angle(k):
    return math.radians(TAIL_SPREAD[0] * (5 - k) / 4)                # Tail1 to its left (+X), Tail5 straight up, Tail9 to its right


def tail_radius(k, t):
    """A brush: slim at the root, fattest about two thirds of the way out, then a quick soft point."""
    rmax = TAIL_FAT[abs(k - 5)]
    t = np.asarray(t, dtype=float)
    rise = 0.24 + 0.76 * np.sin(np.pi / 2 * np.clip(t / 0.62, 0, 1)) ** 2.6     # slim through the bundle, then filling out
    fall = np.cos(np.pi / 2 * np.clip((t - 0.62) / 0.38, 0, 1)) ** 0.85
    return rmax * np.where(t <= 0.62, rise, fall)


def tail_path(k, n=200):
    """Tail k's middle line from the root to its tip, a crescent: it leaves the rump heading back, turns steadily (more and more toward its tip)
    out to its place in the fan and over, so that its tip hooks forward, and its last third curls up like a flame. (points, unit tangents, the
    normal of the plane it bends in, at each point), evenly spaced along its length."""
    side = abs(k - 5)
    L = TAIL_LENGTH[side]
    t0, t1 = (math.radians(a) for a in TAIL_TURN[side])
    phi = tail_angle(k)
    back, up = np.array((0.0, 1.0, 0.0)), np.array((0.0, 0.0, 1.0))
    rad = np.array((math.sin(phi), 0.0, math.cos(phi)))
    m = 1200
    u = (np.arange(m) + 0.5) / m
    theta = t0 + (t1 - t0) * u ** 1.5
    lift = TAIL_CURL[side] * smooth(0.55, 1.0, u)
    out = rad[None] + up[None] * lift[:, None]
    out /= np.linalg.norm(out, axis=1)[:, None]
    d = np.cos(theta)[:, None] * back[None] + np.sin(theta)[:, None] * out
    B = np.vstack([np.array(FAN_ROOT)[None], np.array(FAN_ROOT) + np.cumsum(d * (L / m), axis=0)])
    seg = np.linalg.norm(np.diff(B, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    fs = np.linspace(0, cum[-1], n)
    pts = np.array([np.interp(fs, cum, B[:, j]) for j in range(3)]).T
    if k % 2 == 0:
        pts = pts + np.outer(smooth(0.02, 0.32, fs / cum[-1]), back) * TAIL_LAYER[0]
    tan = np.gradient(pts, axis=0)
    tan /= np.linalg.norm(tan, axis=1)[:, None]
    face = np.cross(rad, back)
    face /= np.linalg.norm(face)
    return pts, tan, np.tile(face, (n, 1))


def lock_hash(*a):
    h = 0
    for v in a:
        h = (h * 1000003 + int(v) * 9176 + 12345) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFFFF) / 0xFFFFFF


# the locks a tail is made of, besides its core: (angle round it from its outer curve, where it starts and ends along the tail, size, how far
# its end flares out). Most run along its two edges (its outer and inner curves) so the outline shows them; two smaller ones round out its
# faces; the last two part off beside the tip and curl with it, so the tip ends in three flames.
LOCKS = [(0.0, 0.16, 0.58, 1.0, 0.55), (0.38, 0.3, 0.76, 0.9, 0.7), (-0.36, 0.44, 0.9, 0.85, 0.8),
         (math.pi, 0.18, 0.62, 0.95, 0.5), (math.pi - 0.4, 0.34, 0.8, 0.9, 0.7), (math.pi + 0.38, 0.5, 0.88, 0.8, 0.75),
         (math.pi / 2, 0.3, 0.72, 0.7, 0.2), (-math.pi / 2, 0.4, 0.8, 0.7, 0.2),
         (math.pi / 2 + 0.35, 0.64, 0.99, 0.4, 1.05), (-math.pi / 2 - 0.35, 0.66, 0.97, 0.38, 1.05)]


def tail_shape(k, rings, around, grooves):
    """Tail k as a soft core and its locks, each a closed swept tube: [(grid of rings x around points, tip, root, places along the tail)].
    grooves (the bake's version): soft strands along each."""
    pts, tan, face = tail_path(k, rings)
    t = np.linspace(0, 1, rings)
    r = tail_radius(k, t)
    frames = []
    for i in range(rings):
        T = tan[i]
        F = face[i] - T * np.dot(face[i], T)
        F /= np.linalg.norm(F)
        frames.append((T, F, np.cross(T, F)))
    bend = np.gradient(tan, axis=0)
    out = []

    def tube(centres, radii, tt, ar, flat_dir=None):
        n = len(centres)
        tg = np.gradient(centres, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        grid = np.zeros((n - 1, ar, 3))
        ang = np.linspace(0, 2 * np.pi, ar, endpoint=False)
        for q in range(n - 1):
            F = frames[min(int(tt[q] * (rings - 1)), rings - 1)][1]
            a1 = np.cross(tg[q], F)
            a1 /= np.linalg.norm(a1) + 1e-12
            a2 = np.cross(tg[q], a1)
            rr = np.full(ar, radii[q])
            if grooves:
                env = np.sin(np.pi * np.clip(q / (n - 1), 0, 1)) ** 0.6
                rr = rr * (1 - 0.06 * env * (1 - np.abs(np.sin(2.5 * ang + 3 * tt[q] + k)) ** 0.4)) - 0.0012 * env * (0.5 + 0.5 * np.sin(13 * ang + 5 * tt[q]))
            grid[q] = centres[q] + (np.outer(np.cos(ang), a1) + np.outer(np.sin(ang), a2) * TAIL_FLAT[0]) * rr[:, None]
        out.append((grid, centres[-1], centres[0] - tg[0] * 0.005, tt[:-1]))

    # the core, a little slimmer than the whole tail
    tube(pts, r * 0.8, t, around)
    for theta, ts, te, size, flare in LOCKS:
        m = max(8, int((te - ts) * rings))
        lt = np.linspace(ts, te, m)
        idx = np.clip((lt * (rings - 1)).astype(int), 0, rings - 1)
        rl = tail_radius(k, lt)
        centres = np.zeros((m, 3))
        for q, i in enumerate(idx):
            T, F, W = frames[i]
            d = math.cos(theta) * W + math.sin(theta) * F * TAIL_FLAT[0]
            reach = (lt[q] - ts) / (te - ts)
            centres[q] = pts[i] + d * rl[q] * (0.5 + flare * smooth(0.55, 1.0, reach))
            if abs(math.sin(theta)) > 0.8 and ts > 0.6:          # the tip's flames curl with the tail
                cb = bend[i] / (np.linalg.norm(bend[i]) + 1e-12)
                centres[q] += cb * rl[q] * 0.4 * smooth(0.35, 1.0, reach)
        reach = (lt - ts) / (te - ts)
        sharp = 1.2 if ts > 0.6 else 0.8                       # the tip's flames end in finer points
        rad = size * 0.55 * rl * np.sin(np.pi / 2 * np.clip(reach / 0.3, 0, 1)) * np.cos(np.pi / 2 * np.clip((reach - 0.4) / 0.6, 0, 1)) ** sharp
        rad = np.maximum(rad, 0.002)
        tube(centres, rad, lt, max(10, around // 2))
    return out


def grid_to_mesh(bm, grid, tip, root):
    rows = [[bm.verts.new(Vector(p)) for p in ring] for ring in grid]
    n = len(rows[0])
    tv, rv = bm.verts.new(Vector(tip)), bm.verts.new(Vector(root))
    for i in range(len(rows) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((rows[-1][j], rows[-1][j2], tv))
        bm.faces.new((rows[0][j2], rows[0][j], rv))


def tail_mesh(k, rings, around, grooves):
    """A soft core and its locks, each a closed tube (fused later)."""
    m = Mesh()
    for grid, tip, root, _ in tail_shape(k, rings, around, grooves):
        grid_to_mesh(m.bm, grid, tip, root)
    bmesh.ops.recalc_face_normals(m.bm, faces=m.bm.faces)
    return m


def build_tails(grooved, name, coll):
    """The nine tails, as one object of nine closed pieces, each tail's core and locks fused (a voxel copy). grooved: the bake's version
    (3 mm, soft strands cut in); else the game mesh's (4 mm)."""
    pieces = []
    for k in range(1, 10):
        piece = tail_mesh(k, 260 if grooved else 110, 96 if grooved else 44, grooved)
        o = piece.finish(name + "_%d" % k, coll, recalc=False)
        # core and locks fused into one closed surface: for the bake as well (left overlapping, its rays caught the locks' insides along
        # every seam and printed them as dark zigzags)
        apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003 if grooved else VOXEL, "adaptivity": 0.0})])
        keep_largest(o)
        pieces.append(o)
    return join(pieces, name)


def tail_chains9():
    return [tail_path(k, 25)[0] for k in range(1, 10)]


CLOUD = {}


def tail_cloud(k):
    """Points on tail k's surface (its core and every lock, as the game mesh has them) with their outward normals, places along the tail and
    the bone (A, B, C) that carries them."""
    if k in CLOUD:
        return CLOUD[k]
    parts = [(g, gt) for g, _, _, gt in tail_shape(k, 70, 30, False)]
    pts, nrm, tt = [], [], []
    for G, gt in parts:
        d1 = np.gradient(G, axis=0)
        d2 = np.roll(G, -1, axis=1) - np.roll(G, 1, axis=1)
        n = np.cross(d1, d2)
        n /= np.linalg.norm(n, axis=2, keepdims=True) + 1e-12
        cen = G.mean(axis=1, keepdims=True)
        n[((G - cen) * n).sum(-1) < 0] *= -1
        pts.append(G.reshape(-1, 3))
        nrm.append(n.reshape(-1, 3))
        tt.append(np.repeat(gt, G.shape[1]))
    pts, nrm, tt = np.vstack(pts), np.vstack(nrm), np.concatenate(tt)
    seg = np.where(tt < TAIL_JOINTS[1], 0, np.where(tt < TAIL_JOINTS[2], 1, 2))
    CLOUD[k] = (pts, nrm, tt, seg)
    return CLOUD[k]


def tail_clearance(rig=None, bodytree=None):
    """Surface to surface: how close any tail comes to another past its share of the root bundle (negative: one passes into the other), and
    to the body. With a rig, the tails as posed (each stretch moved by the bone that carries it)."""
    clouds = {}
    for k in range(1, 10):
        pts, nrm, tt, seg = tail_cloud(k)
        if rig is not None:
            P, Nn = pts.copy(), nrm.copy()
            for j, name in enumerate(tail_bone_names(k)):
                pb = rig.pose.bones[name]
                M = np.array(rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ rig.matrix_world.inverted())
                sel = seg == j
                P[sel] = pts[sel] @ M[:3, :3].T + M[:3, 3]
                Nn[sel] = nrm[sel] @ M[:3, :3].T
            pts, nrm = P, Nn
        clouds[k] = (pts, nrm, tt)
    worst, where = 1e9, None
    for a in range(1, 10):
        Pa, _, ta = clouds[a]
        A = Pa[ta >= ROOT_ZONE]
        tA = ta[ta >= ROOT_ZONE]
        for b in range(1, 10):
            if a == b:
                continue
            Pb, Nb, tb = clouds[b]
            keep = tb >= ROOT_ZONE                          # both surfaces past the bundle (inside it, all nine share one volume)
            Pb, Nb, tb = Pb[keep], Nb[keep], tb[keep]
            if (np.maximum(A.min(0) - Pb.max(0), Pb.min(0) - A.max(0)) > 0.05).any():
                continue
            kd = KDTree(len(Pb))
            for i, q in enumerate(Pb):
                kd.insert(q, i)
            kd.balance()
            for qi, q in enumerate(A):
                co, i, d = kd.find(q)
                if d > 0.06:
                    continue
                sd = float(np.dot(q - Pb[i], Nb[i]))
                if sd < worst:
                    worst, where = sd, (a, b, round(float(tA[qi]), 2), round(float(tb[i]), 2), tuple(np.round(q, 2)))
    body = None
    if bodytree is not None:
        body = 1e9
        for a in range(1, 10):
            Pa, _, ta = clouds[a]
            for q in Pa[ta >= ROOT_ZONE][::2]:
                loc, n, _, d = bodytree.find_nearest(Vector(q))
                if loc is not None:
                    # the side it is on counts only close to the body: further off, the nearest face may be a cut rim or the far side of a spike
                    body = min(body, float(np.dot(np.array(q) - np.array(loc), np.array(n))) if d < 0.03 else d)
    return round(worst if where else 0.06, 4), where, (round(body, 4) if body is not None else None)


# ---------- the game mesh ----------
BODY_SPEND = [0.98]     # the body's weight for thinning against the tails' 1 (it keeps more: the head, mane and eyes keep their detail)


def game_mesh(hi, tails=None, body=None):
    """The voxel copy collapsed to the budget. With the tails' and the body's own surfaces given, every point nearer the tails is weighted for
    thinning (the body keeps more), and the ratio is searched until the whole lands on the budget."""
    me = hi.data.copy()
    o = bpy.data.objects.new(N + "Body", me)
    GAME.objects.link(o)
    for a in ("paint", "rough", "metal"):
        if me.attributes.get(a):
            me.attributes.remove(me.attributes[a])
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": VOXEL, "adaptivity": 0.0})])
    specks = keep_largest(o)
    assert not specks or max(specks) < 2000, "the voxel copy fell apart: pieces of %s vertices dropped" % sorted(specks)[-3:]
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tails is None:
        apply_mods(o, [("DECIMATE", {"decimate_type": "COLLAPSE", "ratio": TARGET_TRIS / tris}), ("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
    else:
        dg = bpy.context.evaluated_depsgraph_get()
        tt, bt = BVHTree.FromObject(tails, dg), BVHTree.FromObject(body, dg)
        g = o.vertex_groups.new(name="Spend")
        tail_v, body_v = [], []
        for v in o.data.vertices:
            (tail_v if tt.find_nearest(v.co)[3] < bt.find_nearest(v.co)[3] else body_v).append(v.index)
        g.add(tail_v, 1.0, "REPLACE")
        g.add(body_v, BODY_SPEND[0], "REPLACE")
        ratio, base = TARGET_TRIS / tris, o.data.copy()
        for _ in range(6):
            o.data = base.copy()
            apply_mods(o, [("DECIMATE", {"decimate_type": "COLLAPSE", "ratio": ratio, "vertex_group": "Spend", "vertex_group_factor": 1.0}),
                           ("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
            got = sum(len(p.vertices) - 2 for p in o.data.polygons)
            if abs(got - TARGET_TRIS) < 250:
                break
            ratio *= TARGET_TRIS / max(got, 1)
        o.vertex_groups.clear()
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    P = verts(o)
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(o, P)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    print("GAME MESH: inside specks dropped by the voxel copy", len(specks), "tris", sum(len(p.vertices) - 2 for p in o.data.polygons), flush=True)
    return o


def gaps(low, hi, n=80000):
    """How far the game mesh strays from the sculpt (low to high), and what of the sculpt it misses (high to low: a lost spike shows here)."""
    dg = bpy.context.evaluated_depsgraph_get()
    th, tl = BVHTree.FromObject(hi, dg), BVHTree.FromObject(low, dg)
    a = np.array([th.find_nearest(v.co)[3] for v in low.data.vertices])
    idx = np.random.default_rng(1).choice(len(hi.data.vertices), min(n, len(hi.data.vertices)), replace=False)
    b = np.array([tl.find_nearest(hi.data.vertices[int(i)].co)[3] for i in idx])
    return {"low to sculpt max m": round(float(a.max()), 4), "sculpt to low p99 m": round(float(np.percentile(b, 99)), 4),
            "p99.9": round(float(np.percentile(b, 99.9)), 4), "max": round(float(b.max()), 4)}


# ---------- its tails, found on the game mesh ----------
def graph(o):
    P = verts(o)
    E = edge_array(o.data)
    L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    adj = [[] for _ in range(len(P))]
    for (a, b), l in zip(E.tolist(), L.tolist()):
        adj[a].append((b, l))
        adj[b].append((a, l))
    return P, adj


def dijkstra(adj, sources):
    n = len(adj)
    d = np.full(n, np.inf)
    prev = np.full(n, -1)
    label = np.full(n, -1)
    h = []
    for k, s in enumerate(sources):
        d[s] = 0.0
        label[s] = k
        h.append((0.0, s))
    heapq.heapify(h)
    while h:
        dd, u = heapq.heappop(h)
        if dd > d[u]:
            continue
        for v, l in adj[u]:
            nd = dd + l
            if nd < d[v]:
                d[v], prev[v], label[v] = nd, u, label[u]
                heapq.heappush(h, (nd, v))
    return d, prev, label


def tail_chains(low):
    """One chain per tail: (points from the rump to the tip). Tips are the far points of the surface (from the nose) behind the hind legs, at least
    14 cm apart over the surface. Ordered round the fan, as seen from behind: from its right to its left."""
    P, adj = graph(low)
    nose = int(np.argmin(P[:, 1]))
    dn, prev, _ = dijkstra(adj, [nose])
    order = np.argsort(-dn)
    taken = np.zeros(len(P), dtype=bool)
    tips = []
    for i in order:
        if taken[i] or not np.isfinite(dn[i]) or P[i, 1] < 0.0 or dn[i] < 1.5:
            continue
        local = {int(i): 0.0}
        h = [(0.0, int(i))]
        while h:
            dd, u = heapq.heappop(h)
            if dd > local.get(u, 1e9):
                continue
            for v, l in adj[u]:
                nd = dd + l
                if nd < 0.14 and nd < local.get(v, 1e9):
                    local[v] = nd
                    heapq.heappush(h, (nd, v))
        fresh = not any(taken[v] for v in local)
        for v in local:
            taken[v] = True
        if fresh:
            tips.append(int(i))
    _, _, label = dijkstra(adj, tips)
    chains = []
    for k, t in enumerate(tips):
        path = [t]
        while prev[path[-1]] >= 0 and P[path[-1], 1] > TAIL_START_Y:
            path.append(int(prev[path[-1]]))
        pts = P[path[::-1]]
        mine = P[label == k]
        cen = []
        for i in range(len(pts)):
            tng = pts[min(len(pts) - 1, i + 2)] - pts[max(0, i - 2)]
            tng = tng / (np.linalg.norm(tng) + 1e-9)
            rel = mine - pts[i]
            sel = mine[(np.abs(rel @ tng) < 0.02) & (np.linalg.norm(rel, axis=1) < 0.16)]
            cen.append(sel.mean(0) if len(sel) > 4 else pts[i])
        cen = np.array(cen)
        cen[-1] = pts[-1]
        for _ in range(4):                                      # ease the jitter of the centring out of the line
            cen[1:-1] = (cen[:-2] + 2 * cen[1:-1] + cen[2:]) / 4
        seg = np.linalg.norm(np.diff(cen, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        fs = np.linspace(0, 1, 25)
        line = np.array([np.interp(fs * s[-1], s, cen[:, j]) for j in range(3)]).T
        chains.append(line)
    chains.sort(key=lambda c: math.atan2(c[-1][0], c[-1][2] - 0.55))
    for k, c in enumerate(chains):
        print("TAIL", k + 1, "root", tuple(np.round(c[0], 3)), "tip", tuple(np.round(c[-1], 3)), "length %.2f" % np.linalg.norm(np.diff(c, axis=0), axis=1).sum(), flush=True)
    return chains


# ---------- the skeleton ----------
TAIL_JOINTS = (0.0, 0.34, 0.67, 0.97)
SEGS = "ABC"


def tail_bone_names(k):
    return ["Tail%d%s" % (k, s) for s in SEGS]


def leg_names(key):
    return ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw" + key]


def skeleton(chains, tips=False):
    """Root, Hips, Spine, Chest, Neck, Head; ears; four legs (upper, elbow or knee, wrist or hock, paw); TailRoot and three bones per tail.
    Each bone points at its child, so heat weighting sees the real limb."""
    spec = [("Root", V(0, 0, 0), V(0, 0, 0.12), None)]
    heads = {n: V(*h) for n, h, _ in TRUNK}
    order = [n for n, _, _ in TRUNK]
    for i, (name, head, parent) in enumerate(TRUNK):
        tail = heads[order[i + 1]] if i + 1 < len(order) else V(*HEAD_END)
        spec.append((name, V(*head), tail, parent))
    P = verts(GAME.objects[N + "Body"])
    for side, tag in ((1, "L"), (-1, "R")):
        base = mirror_x(EAR_BASE, side)
        cand = P[(P[:, 0] * side > 0.03) & (P[:, 1] < -0.5)]
        tip = Vector(cand[np.argmax(cand[:, 2])])            # the ear's tip: the highest point on its side of the head
        spec.append(("Ear" + tag, base, base + (tip - base) * 0.85, "Head"))
        for key, joints in LEGS.items():
            names = leg_names(key + tag)
            parent = "Chest" if key == "F" else "Hips"
            for j, name in enumerate(names):
                spec.append((name, mirror_x(joints[j], side), mirror_x(joints[j + 1], side), parent))
                parent = name
    root_at = V(0, TAIL_START_Y - 0.01, 0.6)
    spec.append(("TailRoot", V(0, -0.2, 0.6), root_at, "Hips"))
    for k, c in enumerate(chains, 1):
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))])

        def at(f):
            return V(*[float(np.interp(f * s[-1], s, c[:, j])) for j in range(3)])
        parent = "TailRoot"
        for j, name in enumerate(tail_bone_names(k)):
            spec.append((name, at(TAIL_JOINTS[j]), at(TAIL_JOINTS[j + 1]), parent))
            parent = name
        if tips:          # each tail's tip, for effects to leave from (carries no skin)
            spec.append(("Tail%d_Tip" % k, at(TAIL_JOINTS[-1]), at(1.0) + (at(1.0) - at(TAIL_JOINTS[-1])).normalized() * 0.02, parent))
    rig = armature([(n, h, p) for n, h, t, p in spec])
    select_only([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    for n, h, t, p in spec:
        rig.data.edit_bones[n].tail = t
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def bind_heat(rig, body):
    """Bone heat weights, then at most four a vertex, none under a hundredth, normalized. The Root bone carries the rest; the tail tips nothing."""
    carry_none = [b for b in rig.data.bones if b.name == "Root" or b.name.endswith("_Tip")]
    for b in carry_none:
        b.use_deform = False
    select_only([body, rig], rig)
    res = bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for b in carry_none:
        b.use_deform = True                   # (kept as deforming bones so the FBX keeps them; they hold no skin)
    select_only([body])
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01, keep_single=True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    unweighted = sum(1 for v in body.data.vertices if not any(g.weight > 1e-4 for g in v.groups))
    print("HEAT", res, "unweighted vertices", unweighted, "max influences", max(len(v.groups) for v in body.data.vertices), flush=True)
    return unweighted


def weights_of(body):
    names = [g.name for g in body.vertex_groups]
    W = np.zeros((len(body.data.vertices), len(names)))
    for v in body.data.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    return names, W


def tail_info(body, chains):
    """Per vertex of the game mesh: how much of it its tails carry, which tail most, and how far along that tail it lies (0 root, 1 tip)."""
    names, W = weights_of(body)
    P = verts(body)
    tail_cols = {k: [i for i, n in enumerate(names) if n.startswith("Tail%d" % k) and n[len("Tail%d" % k):] in SEGS] for k in range(1, len(chains) + 1)}
    per = np.stack([W[:, cols].sum(1) for k, cols in sorted(tail_cols.items())], 1)
    share = per.sum(1)
    which = per.argmax(1)
    along = np.zeros(len(P))
    for k, c in enumerate(chains):
        sel = which == k
        if sel.any():
            along[sel], _ = nearest_on([Vector(p) for p in c], P[sel])
    return share, which, along


def cavity(P, Nn, cell):
    """How deep each point lies under the surface round it, in metres: the surface's Gaussian-blurred mean position near the point, against the
    point, along its normal (positive in a crevice). Measured in space, not over the mesh's edges, so the finer-meshed eyes and muzzle read like
    the rest. The blurred means are found at the centres of a grid of cells and blended to each point trilinearly (a point taking its own
    cell's mean printed the grid as stripes)."""
    key = np.floor(P / cell).astype(np.int64)
    lo = key.min(0) - 2
    key -= lo
    dims = key.max(0) + 4

    def flat(k):
        return (k[..., 0] * dims[1] + k[..., 1]) * dims[2] + k[..., 2]
    cells, inv = np.unique(flat(key), return_inverse=True)
    sums = np.zeros((len(cells), 3))
    np.add.at(sums, inv, P)
    counts = np.bincount(inv, minlength=len(cells)).astype(float)
    ck = np.stack([cells // (dims[1] * dims[2]), (cells // dims[2]) % dims[1], cells % dims[2]], 1)
    acc = np.zeros((len(cells), 3))
    wsum = np.zeros(len(cells))
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                w = math.exp(-(dx * dx + dy * dy + dz * dz) / 2.5)
                if w < 0.05:
                    continue
                other = flat(ck + np.array([dx, dy, dz]))
                at = np.clip(np.searchsorted(cells, other), 0, len(cells) - 1)
                hit = cells[at] == other
                acc[hit] += w * sums[at[hit]]
                wsum[hit] += w * counts[at[hit]]
    mean_c = acc / np.maximum(wsum, 1e-9)[:, None]
    f = P / cell - 0.5 - lo
    base = np.floor(f).astype(np.int64)
    t = f - base
    vm = np.zeros((len(P), 3))
    vw = np.zeros(len(P))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                other = flat(base + np.array([dx, dy, dz]))
                at = np.clip(np.searchsorted(cells, other), 0, len(cells) - 1)
                hit = cells[at] == other
                vm[hit] += w[hit, None] * mean_c[at[hit]]
                vw[hit] += w[hit]
    mean = vm / np.maximum(vw, 1e-9)[:, None]
    return ((mean - P) * Nn).sum(1)


# ---------- the unwrap: each part cut into near-flat patches ----------
def region_of(name):
    if name in ("Head", "EarL", "EarR"):
        return "Head"
    if name.startswith("Leg"):
        return "Leg" + name[-3:-1]
    if name.startswith("Paw"):
        return "Leg" + name[3:]
    if name.startswith("Tail") and name != "TailRoot":
        return name[:-1]
    if name in ("Chest", "Neck"):
        return "Ruff"
    return "Trunk"


def face_regions(body, bm):
    """Each face's part, from the bones that carry its corners; ragged edges between parts straightened, and scraps of a part cut off from it
    (too small to be islands) given to what surrounds them."""
    names = [g.name for g in body.vertex_groups]
    vreg = []
    for v in body.data.vertices:
        acc = {}
        for g in v.groups:
            r = region_of(names[g.group])
            acc[r] = acc.get(r, 0) + g.weight
        vreg.append(max(acc, key=acc.get))
    freg = []
    for f in bm.faces:
        acc = {}
        for v in f.verts:
            acc[vreg[v.index]] = acc.get(vreg[v.index], 0) + 1
        freg.append(max(acc, key=acc.get))
    for _ in range(3):
        new = list(freg)
        for f in bm.faces:
            acc = {freg[f.index]: 1.5}
            for e in f.edges:
                for g in e.link_faces:
                    if g is not f:
                        acc[freg[g.index]] = acc.get(freg[g.index], 0) + 1
            new[f.index] = max(acc, key=acc.get)
        freg = new
    for _ in range(4):
        seen = np.zeros(len(bm.faces), dtype=bool)
        changed = False
        for f in bm.faces:
            if seen[f.index]:
                continue
            comp, stack = [], [f]
            seen[f.index] = True
            while stack:
                g = stack.pop()
                comp.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if not seen[h.index] and freg[h.index] == freg[f.index]:
                            seen[h.index] = True
                            stack.append(h)
            if len(comp) < 40:
                acc = {}
                for g in comp:
                    for e in g.edges:
                        for h in e.link_faces:
                            if freg[h.index] != freg[f.index]:
                                acc[freg[h.index]] = acc.get(freg[h.index], 0) + 1
                if acc:
                    other = max(acc, key=acc.get)
                    for g in comp:
                        freg[g.index] = other
                    changed = True
        if not changed:
            break
    return freg


def uv_islands(me):
    """UV islands: faces joined where they share both corners of an edge in UV too."""
    uv = me.uv_layers.active.data
    corner = {}
    for p in me.polygons:
        for li in p.loop_indices:
            corner[(p.index, me.loops[li].vertex_index)] = tuple(np.round(uv[li].uv, 6))
    edge_faces = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    parent = list(range(len(me.polygons)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for (a, b), fs in edge_faces.items():
        if len(fs) == 2 and corner[(fs[0], a)] == corner[(fs[1], a)] and corner[(fs[0], b)] == corner[(fs[1], b)]:
            parent[find(fs[0])] = find(fs[1])
    return len({find(i) for i in range(len(me.polygons))})


def uv_fill(me):
    uv = me.uv_layers.active.data
    total = 0.0
    for p in me.polygons:
        a, b, c = [uv[i].uv for i in list(p.loop_indices)[:3]]
        total += abs((b - a).cross(c - a)) / 2
    return round(total, 3)


PATCH_FACES = 170      # about this many faces to a UV island: small enough to flatten with little stretch, few enough for few seams


def patch_labels(me, freg):
    """Each part cut into compact patches that lie near flat (k-means over the faces' places and facings, within each part), each patch one
    connected piece; scraps joined to a neighbour."""
    centres = np.array([tuple(p.center) for p in me.polygons])
    facing = np.array([tuple(p.normal) for p in me.polygons])
    feats = np.hstack([centres / 0.07, facing * 1.4])
    labels = np.full(len(me.polygons), -1)
    nxt = 0
    rng = np.random.default_rng(7)
    for region in sorted(set(freg)):
        idx = np.array([i for i, r in enumerate(freg) if r == region])
        k = max(1, int(round(len(idx) / PATCH_FACES)))
        X = feats[idx]
        seeds = [int(rng.integers(len(idx)))]
        d = np.linalg.norm(X - X[seeds[0]], axis=1)
        for _ in range(k - 1):
            seeds.append(int(np.argmax(d)))
            d = np.minimum(d, np.linalg.norm(X - X[seeds[-1]], axis=1))
        C = X[seeds]
        for _ in range(20):
            lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), 1)
            for j in range(k):
                if (lab == j).any():
                    C[j] = X[lab == j].mean(0)
        labels[idx] = lab + nxt
        nxt += k
    # one connected piece per patch
    adj = [[] for _ in range(len(me.polygons))]
    edge_faces = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    for fs in edge_faces.values():
        if len(fs) == 2:
            adj[fs[0]].append(fs[1])
            adj[fs[1]].append(fs[0])
    comp = np.full(len(me.polygons), -1)
    c = 0
    for i in range(len(me.polygons)):
        if comp[i] >= 0:
            continue
        stack = [i]
        comp[i] = c
        while stack:
            u = stack.pop()
            for w in adj[u]:
                if comp[w] < 0 and labels[w] == labels[u]:
                    comp[w] = c
                    stack.append(w)
        c += 1
    for _ in range(6):
        sizes = np.bincount(comp)
        small = np.nonzero(sizes < 12)[0]
        if not len(small):
            break
        for sc in small:
            members = np.nonzero(comp == sc)[0]
            votes = {}
            for u in members:
                for w in adj[u]:
                    if comp[w] != sc:
                        votes[comp[w]] = votes.get(comp[w], 0) + 1
            if votes:
                comp[members] = max(votes, key=votes.get)
    return comp


def unwrap_regions(body, densities):
    """The atlas: each part (head, ruff, trunk, each leg, each tail) cut into compact near-flat patches, each flattened (angle based, then
    relaxed); faces still turned over or crushed flat are projected on their own; each part sized to its density (the face most), and all
    packed. (Smart projection of this fur gave over a thousand islands filling a quarter of the map; whole parts flattened as one island
    stretched their spikes to nothing.)"""
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    freg = face_regions(body, bm)
    bm.free()
    patch = patch_labels(me, freg)
    for e in me.edges:
        e.use_seam = False
    edge_faces = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    seam_keys = {ek for ek, fs in edge_faces.items() if len(fs) == 2 and patch[fs[0]] != patch[fs[1]]}
    for e in me.edges:
        e.use_seam = e.key in seam_keys
    seams = len(seam_keys)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    select_only([body])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", fill_holes=True, correct_aspect=True, margin=0.002)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.minimize_stretch(iterations=40)
    bpy.ops.object.mode_set(mode="OBJECT")
    print("UV fill after flattening", uv_fill(me), "islands", uv_islands(me), flush=True)
    uv = me.uv_layers.active.data
    ratio, sign = np.zeros(len(me.polygons)), np.zeros(len(me.polygons))
    for p in me.polygons:
        a, b, c = [uv[i].uv for i in list(p.loop_indices)[:3]]
        su = (b - a).cross(c - a) / 2
        sign[p.index] = np.sign(su)
        ratio[p.index] = abs(su) / max(p.area, 1e-12)
    # judged island by island (one part can flatten into islands facing either way)
    parent = list(range(len(me.polygons)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    edge_faces = {}
    for poly in me.polygons:
        for ek in poly.edge_keys:
            edge_faces.setdefault(ek, []).append(poly.index)
    seam = {e.key for e in me.edges if e.use_seam}
    for ek, fs in edge_faces.items():
        if len(fs) == 2 and ek not in seam:
            parent[find(fs[0])] = find(fs[1])
    island = np.array([find(i) for i in range(len(me.polygons))])
    bad = np.zeros(len(me.polygons), dtype=bool)
    for isl in np.unique(island):
        idx = np.nonzero(island == isl)[0]
        med = np.median(ratio[idx])
        major = 1.0 if (sign[idx] > 0).sum() >= (sign[idx] < 0).sum() else -1.0
        bad[idx] = (sign[idx] != major) | (ratio[idx] < 0.05 * med)       # faces turned over, or crushed nearly flat (a spike folded down)
    sizes = np.bincount(np.unique(island, return_inverse=True)[1])
    print("UNWRAP seam islands", len(sizes), "under 20 faces", int((sizes < 20).sum()), "faces in them", int(sizes[sizes < 20].sum()), flush=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")              # (a selection set outside edit mode was lost, and the whole mesh was re-projected)
    ebm = bmesh.from_edit_mesh(me)
    ebm.faces.ensure_lookup_table()
    for f in ebm.faces:
        f.select_set(False)
    for f in ebm.faces:
        if bad[f.index]:
            f.select_set(True)
    ebm.select_flush_mode()
    bmesh.update_edit_mesh(me)
    if bad.any():
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    polys = {}
    for p in me.polygons:
        polys.setdefault(freg[p.index], []).append(p)
    print("UV fill after re-projection", uv_fill(me), flush=True)
    for region, ps in polys.items():
        scale_uv_to(body, ps, densities(region))
    uvs = np.empty(len(me.loops) * 2)
    me.uv_layers.active.data.foreach_get("uv", uvs)
    uvs = uvs.reshape(-1, 2)
    uvs = (uvs - uvs.min(0)) / (uvs.max(0) - uvs.min(0)).max()      # back into the unit square before packing (spread over many units, it packed to a fifth)
    me.uv_layers.active.data.foreach_set("uv", uvs.ravel())
    print("UV fill after sizing", uv_fill(me), flush=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=0.004, rotate=True, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    print("UV fill after packing", uv_fill(me), "islands", uv_islands(me), flush=True)
    print("UNWRAP parts", len(polys), "seam edges", seams, "faces projected on their own", int(bad.sum()), flush=True)
    return freg


# ---------- the paint: per vertex of the sculpt, baked to the colour map; eyes and claws are painted per texel after ----------
def paint_sculpt(hi, body, tinfo, body_points=None):
    me = hi.data
    P = verts(hi)
    Nn = normals(hi)
    fine, broad = cavity(P, Nn, 0.004), cavity(P, Nn, 0.014)       # two scales: the fur clumps, and the folds between them
    for name, c in (("fine", fine), ("broad", broad)):
        print("CAVITY", name, "percentiles 1 10 50 90 99", np.round(np.percentile(c, [1, 10, 50, 90, 99]), 5), flush=True)
    # its tails' share, tail and place along it, from the nearest point of the game mesh
    share, which, along = tinfo
    BP = verts(body)
    kd = KDTree(len(BP))
    for i, p in enumerate(BP):
        kd.insert(p, i)
    kd.balance()
    near = np.array([kd.find(p)[1] for p in P])
    t_share, t_along = share[near], along[near]
    if body_points:
        t_share[:body_points] = 0.0          # the tails' colour on the tails only (it stained the haunch where the tail bones' weights reach)
    up = np.clip(Nn[:, 2], -1, 1)
    lit = smooth(-0.6, 0.85, up)
    col = mix(FUR_SHADE, FUR_LIGHT, lit ** 0.9)
    col = mix(col, FUR, 0.25)
    # the tails: lavender, deeper toward the roots and on their undersides, near white at the tips
    tail_col = mix(TAIL_ROOT, TAIL_TOP, smooth(0.02, 0.5, t_along))
    tail_col = mix(tail_col, TAIL_TIP, smooth(0.72, 0.97, t_along))
    tail_col = mix(tail_col, TAIL_UNDER, smooth(0.1, -0.55, up) * smooth(0.12, 0.4, t_along) * 0.85)
    col = mix(col, tail_col, smooth(0.25, 0.75, t_share))
    # inside its ears
    for side in (1, -1):
        ear = (P[:, 2] > 1.24) & (P[:, 0] * side > 0.03) & (P[:, 1] < -0.55)
        inner = smooth(0.1, 0.55, -Nn[:, 1]) * smooth(1.24, 1.3, P[:, 2]) * ear
        col = mix(col, EAR_IN, inner * 0.6)
    # violet in the crevices between the fur clumps and in the deep folds; the clumps' crests catch the light
    col = mix(col, CREASE, smooth(0.00012, 0.0012, fine) * 0.7)
    col = mix(col, DEEP, smooth(0.0015, 0.007, broad) * 0.4)
    col = mix(col, FUR_LIGHT, smooth(-0.00015, -0.0012, fine) * 0.45 * (1 - smooth(0.3, 0.8, t_share)))
    col = mix(col, TAIL_TIP, smooth(-0.0005, -0.004, fine) * 0.55 * smooth(0.3, 0.8, t_share))      # a soft sheen on the tails' lock crests
    rough = np.full(len(P), 0.82)
    # nose: the bulb at the front of its muzzle
    tipi = int(np.argmin(P[:, 1]))
    tip = P[tipi]
    dn = np.linalg.norm((P - (tip + np.array([0, 0.008, -0.005]))) / np.array([1.0, 1.25, 1.2]), axis=1)
    nose = smooth(0.0145, 0.0108, dn) * smooth(0.0, 0.35, -Nn[:, 1] - 0.3 * Nn[:, 2] + 0.2)
    sheen = smooth(0.4, 0.95, Nn[:, 2]) * nose
    col = mix(col, NOSE, nose)
    col = mix(col, NOSE_LIT, sheen * 0.45)
    rough = rough * (1 - nose) + 0.42 * nose
    # lips: the groove at each corner of its mouth, from under the nose back
    (y0, y1), (z0, z1), (x0, x1) = LIP_ZONE
    zone = (P[:, 1] > y0) & (P[:, 1] < y1) & (P[:, 2] > z0) & (P[:, 2] < z1) & (np.abs(P[:, 0]) > x0) & (np.abs(P[:, 0]) < x1)
    lip = zone * smooth(0.00007, 0.0002, fine) * smooth(y1, y1 - 0.012, P[:, 1])
    col = mix(col, LIP, np.clip(lip * 1.2, 0, 1))
    rough = rough * (1 - lip) + 0.55 * lip
    paint(hi, col, rough)
    print("PAINT sculpt", len(P), "verts; nose verts", int((nose > 0.5).sum()), "lip verts", int((lip > 0.5).sum()), flush=True)


def sculpt_material():
    """Paint, with violet gathered where the sculpt shades itself: a close one for the clumps, a wide one for the folds between tails and under it."""
    m = bpy.data.materials.new(PET + "_Hi")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    paint_in = t.nodes.new("ShaderNodeAttribute")
    paint_in.attribute_name = "paint"
    rough_in = t.nodes.new("ShaderNodeAttribute")
    rough_in.attribute_name = "rough"
    last = paint_in.outputs["Color"]
    for dist, share, colour in ((0.025, 0.45, CREASE), (0.14, 0.3, DEEP)):
        ao = t.nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = dist
        ao.only_local = True
        ao.samples = 16
        f = t.nodes.new("ShaderNodeMath")
        f.operation = "MULTIPLY_ADD"
        f.inputs[1].default_value = -share
        f.inputs[2].default_value = share
        t.links.new(ao.outputs["AO"], f.inputs[0])
        mx = t.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs[7].default_value = (*colour, 1)
        t.links.new(f.outputs[0], mx.inputs[0])
        t.links.new(last, mx.inputs[6])
        last = mx.outputs[2]
    t.links.new(last, bsdf.inputs["Base Color"])
    t.links.new(rough_in.outputs["Fac"], bsdf.inputs["Roughness"])
    return m


# ---------- per-texel paint: eyes and claws ----------
def rasterize(o, size):
    """Each texel of the map: the point of the game mesh it shows, and that point's normal. Returns (positions, normals, covered)."""
    me = o.data
    uv = me.uv_layers.active.data
    P = verts(o)
    Nn = normals(o)
    pos = np.zeros((size, size, 3), dtype=np.float32)
    nrm = np.zeros((size, size, 3), dtype=np.float32)
    cov = np.zeros((size, size), dtype=bool)
    for p in me.polygons:
        loops = list(p.loop_indices)
        vi = list(p.vertices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not inside.any():
            continue
        W = np.stack([w0[inside], w1[inside], w2[inside]], 1)
        pos[ys[inside], xs[inside]] = W @ P[vi[:3]]
        nrm[ys[inside], xs[inside]] = W @ Nn[vi[:3]]
        cov[ys[inside], xs[inside]] = True
    return pos, nrm, cov


def read_px(img):
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(h, w, 4)


def write_px(img, px):
    img.pixels.foreach_set(px.ravel())
    img.update()


def to_linear(c):
    """The colour map holds sRGB bytes: its paint is mixed in linear light."""
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def paint_texels(body, frames, size):
    """Eyes (in the frames the sculpt's eyes were opened in) and claws, painted onto the baked maps at full resolution."""
    pos, nrm, cov = rasterize(body, size)
    colour_img, rough_img = bpy.data.images[PET + "_Color"], bpy.data.images[PET + "_Roughness"]
    C, R = read_px(colour_img), read_px(rough_img)
    ys, xs = np.nonzero(cov)
    Pt, Nt = pos[ys, xs].astype(np.float64), nrm[ys, xs].astype(np.float64)
    col, rgh = to_linear(C[ys, xs, :3]), R[ys, xs, 0].copy()
    painted = 0
    for fr in frames.values():
        u, v, d = fr.local(Pt)
        mine = (np.abs(u) < 0.05) & (np.abs(v) < 0.035) & (np.abs(d) < 0.015) & ((Nt @ np.array(fr.w)) > 0.25)
        if not mine.any():
            continue
        uu, vv = u[mine], v[mine]
        e = almond(uu, vv)
        s = np.clip(uu / EYE_HALF, -1, 1)
        inside = smooth(-0.0003, 0.0004, e)
        # the iris: blue, deep under the upper lid, lit low; a round dark pupil; a catch-light up and forward
        ic = np.array([-0.0025, 0.0012])
        ri = np.hypot(uu - ic[0], (vv - ic[1]) * 1.05)
        iris = mix(IRIS_DEEP, IRIS, smooth(0.0085, -0.002, vv))
        iris = mix(iris, IRIS_LIT, smooth(-0.001, -0.0075, vv) * smooth(0.0105, 0.004, ri))
        iris = mix(iris, IRIS_DEEP, smooth(0.0085, 0.0105, ri))           # a dark ring round the iris
        iris = mix(iris, PUPIL, smooth(0.0044, 0.0036, np.hypot(uu - ic[0], (vv - ic[1]) * 0.9)))
        glint = smooth(0.0021, 0.0014, np.hypot(uu - ic[0] + 0.0038, vv - ic[1] - 0.0036))
        glint2 = smooth(0.0011, 0.0006, np.hypot(uu - ic[0] - 0.0035, vv - ic[1] + 0.0035))
        iris = mix(iris, GLINT, np.maximum(glint, glint2 * 0.8))
        shade = smooth(0.0, 0.006, EYE_UP * (1 - s * s) ** 0.55 - vv)     # the upper lid's shadow on the eye
        iris = iris * (0.55 + 0.45 * shade)[:, None]
        # the liner: all round, heavier along the upper lid, and a short wing out past the outer corner
        out = np.maximum(-e, 0)
        width = np.where(vv > 0, 0.0021, 0.0012) + 0.0008 * smooth(0.3, 1.0, s)
        liner = smooth(width, width * 0.55, out) * (e < 0.0004)
        wu = (uu - EYE_HALF) / 0.008
        wing_line = 0.003 + 0.0045 * np.clip(wu, 0, 1)
        wing = smooth(0.0016, 0.0008, np.abs(vv - wing_line)) * smooth(-0.15, 0.1, wu) * smooth(1.0, 0.7, wu)
        liner = np.maximum(liner, wing)
        c0 = col[mine]
        c0 = mix(c0, iris, inside)
        c0 = mix(c0, LINER, np.clip(liner * (1 - inside), 0, 1))
        col[mine] = c0
        r0 = rgh[mine]
        rgh[mine] = r0 * (1 - inside) + 0.12 * inside
        painted += int((inside > 0.5).sum())
    # claws: the front of each toe, down at the ground
    toe = smooth(0.036, 0.02, Pt[:, 2]) * smooth(0.2, 0.5, -Nt[:, 1]) * (Pt[:, 2] < 0.04)
    col = mix(col, CLAW, toe)
    rgh = rgh * (1 - toe) + 0.38 * toe
    C[ys, xs, :3] = to_srgb(col)
    R[ys, xs, 0] = R[ys, xs, 1] = R[ys, xs, 2] = rgh
    for img, px in ((colour_img, C), (rough_img, R)):
        fill_gutters(px, cov)
        if img.packed_file:                       # (packing an image that is already packed keeps the old bytes: the FBX and .blend lost the eyes)
            img.unpack(method="REMOVE")
        write_px(img, px)
        img.save()
        img.pack()
    print("TEXELS eye texels", painted, "claw texels", int((toe > 0.5).sum()), flush=True)



def fill_gutters(px, cov):
    """Every texel no face shows takes its nearest face's colour, so nothing bleeds in at the seams when the engine shrinks the map."""
    hole = ~cov
    known = cov.astype(np.float32)
    px[hole] = 0
    for _ in range(4096):
        if not hole.any():
            break
        weight = np.zeros_like(known)
        total = np.zeros_like(px)
        for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
            k = np.roll(known, shift, axis)
            weight += k
            total += np.roll(px, shift, axis) * k[..., None]
        grow = hole & (weight > 0)
        px[grow] = total[grow] / weight[grow][..., None]
        hole[grow] = False
        known[grow] = 1.0
    px[..., 3] = 1.0


# ---------- poses, in the game's axes: +X lifts what points forward; +Y turns to its left ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def legs4(f, b):
    """Both forelegs f = (upper, fore, wrist) and both hind legs b = (thigh, shin, hock), the same each side; each paw turned back level."""
    out = {}
    for side in "LR":
        for k in range(3):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, 0)
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, 0)
        out["PawF" + side] = (-sum(f), 0, 0)
        out["PawB" + side] = (-sum(b), 0, 0)
    return out


def paw_at(rig, key):
    return rig.matrix_world @ rig.pose.bones["Paw" + key].head


def simplex(fn, x0, steps=260):
    dim = len(x0)
    pts = [np.array(x0, dtype=float)] + [np.array(x0, dtype=float) + np.eye(dim)[k] * 0.4 for k in range(dim)]
    vals = [fn(p) for p in pts]
    for _ in range(steps):
        order = np.argsort(vals)
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        c = sum(pts[:-1]) / dim
        r = c + (c - pts[-1])
        fr = fn(r)
        if fr < vals[0]:
            e = c + 2 * (c - pts[-1])
            fe = fn(e)
            pts[-1], vals[-1] = (e, fe) if fe < fr else (r, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = r, fr
        else:
            k = c + 0.5 * (pts[-1] - c)
            fk = fn(k)
            if fk < vals[-1]:
                pts[-1], vals[-1] = k, fk
            else:
                pts = [pts[0] + 0.5 * (p - pts[0]) for p in pts]
                vals = [fn(p) for p in pts]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def solve_legs(rig, base, front_target, back_target, start_f=(0, 0, 0), start_b=(0, 0, 0)):
    """Leg turns (upper, middle, lower; the same each side) that put each paw at its target (along, up) with the trunk posed as base."""
    def cost(xs, front):
        f = tuple(xs) if front else start_f
        b = start_b if front else tuple(xs)
        pose(rig, spec({**base, **legs4(f, b)}))
        p = paw_at(rig, "FL" if front else "BL")
        t = front_target if front else back_target
        return (p.z - t[1]) ** 2 * 4 + (p.y - t[0]) ** 2 + 0.0004 * sum(x * x for x in xs)
    f, cf = simplex(lambda xs: cost(xs, True), start_f)
    start_f = tuple(f)
    b, cb = simplex(lambda xs: cost(xs, False), start_b)
    return tuple(round(float(v), 3) for v in f), tuple(round(float(v), 3) for v in b), cf, cb


# its trot: diagonal pairs together (fore-left with hind-right), each paw sliding back flat on the ground, then lifted and swung forward
WALK_N, WALK_DUTY, WALK_REACH = 16, 0.55, 0.1
WALK_LIFT = {"F": 0.075, "B": 0.065}
WALK_LEAD = {"FL": 0.0, "BR": 0.0, "FR": 0.5, "BL": 0.5}


def walk_path(t):
    if t < WALK_DUTY:
        return -WALK_REACH + 2 * WALK_REACH * t / WALK_DUTY, 0.0
    s = (t - WALK_DUTY) / (1 - WALK_DUTY)
    return WALK_REACH - 2 * WALK_REACH * (0.5 - 0.5 * math.cos(math.pi * s)), math.sin(math.pi * s)


def find_walk(rig):
    pose(rig, {})
    rf, rb = paw_at(rig, "FL"), paw_at(rig, "BL")
    rows, sf, sb = [], (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    for k in range(WALK_N + 1):
        dy, up = walk_path((k % WALK_N) / WALK_N)
        f, b, cf, cb = solve_legs(rig, {}, (rf.y + dy, rf.z + up * WALK_LIFT["F"]), (rb.y + dy, rb.z + up * WALK_LIFT["B"]), sf, sb)
        sf, sb = f, b
        if k < WALK_N:
            rows.append((f, b, cf, cb))
        else:
            rows[0] = (f, b, cf, cb)
    return rows


def walk_table(rows, g):
    out = {}
    for key, lead in WALK_LEAD.items():
        t = ((g + lead) % 1.0) * WALK_N
        i, w = int(t) % WALK_N, t - int(t)
        a, c = rows[i][0 if key[0] == "F" else 1], rows[(i + 1) % WALK_N][0 if key[0] == "F" else 1]
        ang = [a[j] * (1 - w) + c[j] * w for j in range(3)]
        for j in range(3):
            out["Leg%s%d" % (key, j + 1)] = (ang[j], 0, 0)
        out["Paw" + key] = (-sum(ang), 0, 0)
    return out


SIT_TILT, SIT_DROP = 0.5, 0.2                     # its trunk tips up this much (radians) and its hips come down this far (metres) as it sits


def find_sit(rig, n_tails, body=None):
    """Sitting: the trunk tipped up on its haunches, forepaws where they stood, hind paws a little forward of where they stood; its tails lifted
    off the ground just enough to clear it (tipping the hips swings the hanging tails down)."""
    pose(rig, {})
    rest_f, rest_b = paw_at(rig, "FL"), paw_at(rig, "BL")
    lift = 0.0
    for _ in range(12):
        base = {"Hips": (SIT_TILT, 0, 0, (0, -SIT_DROP, 0.02)), "Neck": (-0.18, 0, 0), "Head": (-0.15, 0, 0), "TailRoot": (-0.45 - lift, 0, 0)}
        for k in range(1, n_tails + 1):
            base[tail_bone_names(k)[0]] = (-lift * 0.6, 0, 0)
        f, b, cf, cb = solve_legs(rig, base, (rest_f.y + 0.02, rest_f.z), (rest_b.y - 0.06, rest_b.z), (-0.4, 0.2, 0.2), (0.9, -1.4, 0.4))
        if body is None:
            break
        pose(rig, spec({**base, **legs4(f, b)}))
        low = lowest_of(body, {"Tails": tuple(n for k in range(1, n_tails + 1) for n in tail_bone_names(k))})["Tails"]
        if low is None or low > 0.01:
            break
        lift += 0.08
    return {**base, **legs4(f, b)}, cf, cb


SWAY_SEGMENT = (0.3, 0.65, 1.0)       # each tail's sway grows toward its tip: the bundle at the root barely moves (swung there, neighbours met)


def tail_sway(n_tails, phase, amp=0.28):
    """A wave running across the fan (neighbours a quarter radian apart) and down each tail."""
    out = {}
    for k in range(1, n_tails + 1):
        for j, name in enumerate(tail_bone_names(k)):
            w = math.sin(phase - k * 0.25 - j * 0.6)
            out[name] = (0.04 * w * SWAY_SEGMENT[j], amp * SWAY_SEGMENT[j] * w, 0)
    return out


def sway_worst(n_tails, amp):
    """The worst the game's sway can do: tails side by side in a layer (k and k + 2) swung fully against each other."""
    out = {}
    for k in range(1, n_tails + 1):
        sign = 1 if ((k - 1) // 2) % 2 == 0 else -1
        for j, name in enumerate(tail_bone_names(k)):
            out[name] = (0, sign * amp * SWAY_SEGMENT[j], 0)
    return out


def fly_tuck(n_tails):
    """In the air: forelegs folded back under its chest, hind legs drawn up under it, tails streaming behind. (Folded harder, the forelegs
    tore the skin under its chest: 23 cm.)"""
    table = legs4((0.45, -1.35, 0.45), (0.6, -1.2, 0.5))
    table.update({"Hips": (0.06, 0, 0), "Neck": (-0.08, 0, 0), "Head": (0.12, 0, 0), "TailRoot": (-0.2, 0, 0)})
    for k in range(1, n_tails + 1):
        for j, name in enumerate(tail_bone_names(k)):
            table[name] = (-0.06, 0, 0)
    return table


def lowest_of(body, parts):
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, bones in parts.items():
        idx = {groups[b] for b in bones if b in groups}
        mine = [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)]
        out[name] = round(float(co[mine, 2].min()), 4) if mine else None
    return out


def posed_chains(rig, chains):
    """The tails' middle lines as posed: each point carried by the bone that holds that stretch of its tail."""
    out = []
    t = np.linspace(0, 1, len(chains[0]))
    for k, c in enumerate(chains, 1):
        names = tail_bone_names(k)
        pts = []
        for i, p in enumerate(c):
            j = 0 if t[i] < TAIL_JOINTS[1] else 1 if t[i] < TAIL_JOINTS[2] else 2
            pb = rig.pose.bones[names[j]]
            M = rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ rig.matrix_world.inverted()
            pts.append(tuple(M @ Vector(p)))
        out.append(np.array(pts))
    return out


def posed_body_tree(body):
    """The posed skin less its tails, for testing tails against the body."""
    names = [g.name for g in body.vertex_groups]
    tail_idx = {i for i, n in enumerate(names) if n.startswith("Tail") and n != "TailRoot"}
    share = np.zeros(len(body.data.vertices))
    for v in body.data.vertices:
        share[v.index] = sum(g.weight for g in v.groups if g.group in tail_idx)
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = [tuple(v.co) for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if max(share[list(p.vertices)]) < 0.5]
    body.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(co, polys)


def fan_out(n_tails, spread=0.32, lift=0.15):
    """The special: every tail swung out round its long axis (the outer ones most) and lifted."""
    return {tail_bone_names(k)[0]: (-lift, 0, spread * (5 - k) / 4) for k in range(1, n_tails + 1)}


def numbered_views(prefix, chains, names, size=720):
    """The straight back and top views with each tail's number by its tip, to count them by."""
    cam = bpy.data.objects["ShowCam"]
    labels = []
    mat = bpy.data.materials.new("Numbers")
    t = mat.node_tree
    t.nodes.clear()
    out = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.82, 0.25, 1)
    em.inputs["Strength"].default_value = 6.0
    t.links.new(em.outputs[0], out.inputs[0])
    paths = []
    for view in names:
        d = Vector(VIEWS[view]).normalized()
        cam.location = Vector(VIEW_AT) + d * 5.2
        cam.rotation_euler = (Vector(VIEW_AT) - cam.location).to_track_quat("-Z", "Y").to_euler()
        for k, c in enumerate(chains, 1):
            tip = Vector(c[-1])
            out_dir = (tip - FAN_ROOT)
            out_dir.y = 0 if view == "backflat" else out_dir.y
            cu = bpy.data.curves.new("n%d" % k, "FONT")
            cu.body = str(k)
            cu.size = 0.12
            cu.align_x = "CENTER"
            cu.align_y = "CENTER"
            cu.materials.append(mat)
            o = bpy.data.objects.new("n%d" % k, cu)
            o.location = tip + out_dir.normalized() * 0.1 + d * 0.3
            o.rotation_euler = cam.rotation_euler
            scene.collection.objects.link(o)
            labels.append(o)
        scene.render.resolution_x = scene.render.resolution_y = size
        path = os.path.join(REVIEW, "%s_%s.png" % (prefix, view))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
        for o in labels:
            bpy.data.objects.remove(o, do_unlink=True)
        labels = []
    bpy.data.materials.remove(mat)
    return paths


# ---------- the review stage ----------
VIEW_AT = (0.0, -0.05, 0.72)
VIEWS = {"front": (0, -1, 0.1), "side": (1, 0, 0.02), "back": (0, 1, 0.12), "q34": (0.72, -0.68, 0.22), "game": (-0.5, 0.78, 0.75),
         "backflat": (0, 1, 0.0), "top": (0, 0.03, 1)}


def clay_material(normal_img):
    m = bpy.data.materials.new(PET + "_Clay")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    if normal_img:
        ni = t.nodes.new("ShaderNodeTexImage")
        ni.image = normal_img
        nm = t.nodes.new("ShaderNodeNormalMap")
        t.links.new(ni.outputs["Color"], nm.inputs["Color"])
        t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def review_stage():
    if "ShowCam" not in bpy.data.objects:
        stage_setup()
    world = scene.world
    t = world.node_tree
    bg = t.nodes["Background"]
    bg.inputs[0].default_value = (0.5, 0.5, 0.62, 1)          # a soft lavender sky lights it, as in the concept
    bg.inputs[1].default_value = 0.9
    dark = t.nodes.new("ShaderNodeBackground")
    dark.inputs[0].default_value = (0.03, 0.028, 0.042, 1)    # while the camera sees the concept's dark backdrop
    path = t.nodes.new("ShaderNodeLightPath")
    mixer = t.nodes.new("ShaderNodeMixShader")
    out = next(n for n in t.nodes if n.type == "OUTPUT_WORLD")
    t.links.new(path.outputs["Is Camera Ray"], mixer.inputs[0])
    t.links.new(bg.outputs[0], mixer.inputs[1])
    t.links.new(dark.outputs[0], mixer.inputs[2])
    t.links.new(mixer.outputs[0], out.inputs[0])
    for name, energy in (("Key", 3.0), ("Fill", 1.4), ("Rim", 2.6)):
        bpy.data.objects[name].data.energy = energy
    bpy.data.objects["Key"].data.color = (1.0, 0.98, 1.0)
    bpy.data.objects["Fill"].data.color = (0.82, 0.84, 1.0)
    bpy.data.objects["Rim"].data.color = (0.88, 0.86, 1.0)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.cycles.samples = 48
    try:
        scene.cycles.use_denoising = True
    except AttributeError:
        pass
    if "Ground" not in bpy.data.objects:
        bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
        g = bpy.context.object
        g.name = "Ground"
        gm = bpy.data.materials.new("GroundShadow")
        gm.node_tree.nodes.clear()
        out = gm.node_tree.nodes.new("ShaderNodeOutputMaterial")
        sc = gm.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
        sc.inputs["Color"].default_value = (0.035, 0.033, 0.048, 1)
        gm.node_tree.links.new(sc.outputs[0], out.inputs[0])
        g.data.materials.append(gm)


def render_views(prefix, names, dist=5.2, size=720, target=VIEW_AT):
    cam = bpy.data.objects["ShowCam"]
    cam.data.lens = 70
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    T = Vector(target)
    out = []
    for name in names:
        d = Vector(VIEWS[name]).normalized()
        cam.location = T + d * dist
        cam.rotation_euler = (T - cam.location).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(REVIEW, "%s_%s.png" % (prefix, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out.append(path)
    return out


def review_sheet(tiles, rows, path, labels, tile=720):
    """Lays the renders out on one sheet, each with its caption, rendered as a plain image (no compositing tools needed)."""
    sheet = bpy.data.scenes.new("ReviewSheet")
    loaded = []
    cols = max(len(r) for r in rows)
    w, h = cols * tile, len(rows) * (tile + 60) + 20
    cam = bpy.data.objects.new("SheetCam", bpy.data.cameras.new("SheetCam"))
    sheet.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h) / 100
    cam.location = (w / 200, -h / 200, 10)
    sheet.camera = cam
    sheet.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_WORKBENCH"
    sheet.render.resolution_x, sheet.render.resolution_y = w, h
    sheet.view_settings.view_transform = "Standard"
    sheet.world = bpy.data.worlds.new("SheetWorld")
    sheet.world.use_nodes = True
    sheet.world.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.04, 0.05, 1)
    for r, row in enumerate(rows):
        for c, key in enumerate(row):
            img = bpy.data.images.load(tiles[key])
            loaded.append(img)
            iw, ih = img.size
            sx = tile / 100
            sy = sx * ih / iw
            me = bpy.data.meshes.new("tile")
            me.from_pydata([(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0)], [], [(0, 1, 2, 3)])
            me.uv_layers.new().data.foreach_set("uv", [0, 0, 1, 0, 1, 1, 0, 1])
            o = bpy.data.objects.new("tile", me)
            o.location = (c * tile / 100, -(r * (tile + 60) + 60 + tile) / 100 + (tile / 100 - sy) / 2, 0)
            sheet.collection.objects.link(o)
            m = bpy.data.materials.new("tile")
            t = m.node_tree
            t.nodes.clear()
            outn = t.nodes.new("ShaderNodeOutputMaterial")
            em = t.nodes.new("ShaderNodeEmission")
            tex = t.nodes.new("ShaderNodeTexImage")
            tex.image = img
            t.links.new(tex.outputs["Color"], em.inputs["Color"])
            t.links.new(em.outputs[0], outn.inputs[0])
            me.materials.append(m)
            cu = bpy.data.curves.new("label", "FONT")
            cu.body = labels.get(key, key)
            cu.size = 0.3
            to = bpy.data.objects.new("label", cu)
            to.location = (c * tile / 100 + 0.15, -(r * (tile + 60) + 45) / 100, 0.01)
            tm = bpy.data.materials.new("label")
            tt = tm.node_tree
            tt.nodes.clear()
            o2 = tt.nodes.new("ShaderNodeOutputMaterial")
            e2 = tt.nodes.new("ShaderNodeEmission")
            e2.inputs["Color"].default_value = (0.85, 0.85, 0.9, 1)
            tt.links.new(e2.outputs[0], o2.inputs[0])
            cu.materials.append(tm)
            sheet.collection.objects.link(to)
    sheet.render.filepath = path
    with bpy.context.temp_override(scene=sheet):
        bpy.ops.render.render(write_still=True, scene=sheet.name)
    for o in list(sheet.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(sheet)
    for img in loaded:                          # (left in, the tiles' file paths would be saved in the .blend)
        bpy.data.images.remove(img)
    return path


GROUND_PARTS = {"FrontPaws": ("PawFL", "PawFR"), "HindPaws": ("PawBL", "PawBR"), "Hocks": ("LegBL3", "LegBR3"), "Hips": ("Hips",), "Chest": ("Chest", "Spine")}


def islands_of(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, count = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        count += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            u = stack.pop()
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
    bm.free()
    return count


def join(objs, name):
    select_only(objs, objs[0])
    bpy.ops.object.join()
    objs[0].name = objs[0].data.name = name
    return objs[0]


def part_tris(body):
    """Triangles per part of the game mesh: each face to the bone that carries most of its corners."""
    names = [g.name for g in body.vertex_groups]
    dom = []
    for v in body.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        dom.append(names[g.group])
    out = {}
    for p in body.data.polygons:
        acc = {}
        for i in p.vertices:
            n = dom[i]
            key = n[:-1] if n.startswith("Tail") and n != "TailRoot" else "Body (head, trunk, legs, tail root)"
            acc[key] = acc.get(key, 0) + 1
        k = max(acc, key=acc.get)
        out[k] = out.get(k, 0) + len(p.vertices) - 2
    return dict(sorted(out.items()))


if __name__ == "__main__":
    hi = load_sculpt()
    hole = strip_tails(hi)
    frames = shape_face(hi)
    body_tree = BVHTree.FromObject(hi, bpy.context.evaluated_depsgraph_get())
    tails_hi = build_tails(True, N + "TailsHi", HI)
    tails_lo = build_tails(False, N + "TailsLo", HI)
    print("PIECES before fusing: sculpt body", islands_of(hi), "island(s); new tails", islands_of(tails_hi), "islands (bake version),", islands_of(tails_lo),
          "(game-mesh version)", flush=True)
    chains = tail_chains9()
    n_tails = len(chains)
    for k, c in enumerate(chains, 1):
        print("TAIL %d tip %s length %.2f" % (k, tuple(np.round(c[-1], 3)), np.linalg.norm(np.diff(c, axis=0), axis=1).sum()), flush=True)
    print("CLEARANCE rest (tail surface to tail surface past the shared root, worst pair; tail to body), m", tail_clearance(None, body_tree), flush=True)
    source = hi.copy()
    source.data = hi.data.copy()
    HI.objects.link(source)
    tails_lo_copy = tails_lo.copy()
    tails_lo_copy.data = tails_lo.data.copy()
    HI.objects.link(tails_lo_copy)
    source = join([source, tails_lo], N + "GameSource")
    body = game_mesh(source, tails_lo_copy, hi)
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.objects.remove(tails_lo_copy, do_unlink=True)
    body_points = len(hi.data.vertices)
    hi = join([hi, tails_hi], N + "Sculpt")                 # the bake's source: the sculpt's body and the nine fur-cut tails
    print("FUSED game mesh islands", islands_of(body), flush=True)
    print("GAPS", gaps(body, hi), flush=True)
    rig = skeleton(chains, tips=True)
    unweighted = bind_heat(rig, body)
    GROUND_PARTS["Tails"] = tuple(n for k in range(1, n_tails + 1) for n in tail_bone_names(k))
    tinfo = tail_info(body, chains)
    print("BONES", len(rig.data.bones), [b.name for b in rig.data.bones], flush=True)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    print("BODY tris", tris, "verts", len(body.data.vertices), "dims", tuple(round(v, 3) for v in body.dimensions), flush=True)
    print("TRIS by part", part_tris(body), flush=True)

    if STAGE == "all":
        unwrap_regions(body, lambda r: {"Head": 2.3, "Ruff": 1.1, "Trunk": 1.0}.get(r, 0.8 if r.startswith("Tail") else 1.0))
        paint_sculpt(hi, body, tinfo, body_points)
        mat = sculpt_material()
        hi.data.materials.clear()
        hi.data.materials.append(mat)
        stage_setup()
        bake_all({"Skin": body}, {"Skin": hi}, mat, size=2048, colour_size=2048, far=("Skin",), far_reach=(0.008, 0.024), fill=(0.9, 0.9, 1.0, 1))
        paint_texels(body, frames, 2048)
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)

    # the rest numbers the game needs
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
    lo, top = min(zs), max(zs)
    print("Z range", round(lo, 4), round(top, 4), "SOLE (box middle with the RootPart, down to the paws)", round((top + min(lo, -0.025)) / 2 - lo, 4), flush=True)
    for name in ("Hips", "Head", "TailRoot"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)

    # stances and the walk, solved on the bones and checked on the skin
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    sit, cf, cb = find_sit(rig, n_tails, body)
    print("SIT fit", round(cf, 6), round(cb, 6), "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in (v[:3] + (tuple(v[3]) if len(v) > 3 else ())))) for b, v in sorted(sit.items())) + " }", flush=True)
    walk = find_walk(rig)
    print("WALK fit worst", max(r[2] for r in walk), max(r[3] for r in walk), flush=True)
    print("WALK_FRONT = { " + ", ".join("{ %g, %g, %g }" % r[0] for r in walk) + " }", flush=True)
    print("WALK_HIND = { " + ", ".join("{ %g, %g, %g }" % r[1] for r in walk) + " }", flush=True)
    fly = fly_tuck(n_tails)
    print("FLY { " + ", ".join("%s = { %g, %g, %g }" % (b, *v[:3]) for b, v in sorted(fly.items())) + " }", flush=True)
    lib = {"Sit": spec(sit), "Fly": spec(fly), "TailSway": spec(tail_sway(n_tails, 0.0)), "TailSway2": spec(tail_sway(n_tails, math.pi)),
           "FanOut": spec(fan_out(n_tails)), "SwayGame": spec(tail_sway(n_tails, 1.3, 0.08)), "SwayWorst": spec(sway_worst(n_tails, 0.08)),
           "Glance": spec({"Neck": (0.08, 0.35, 0), "Head": (0.12, 0.45, 0.1)}), "Ears": spec({"EarL": (-0.35, 0.3, 0), "EarR": (-0.35, -0.3, 0)}),
           "Breath": spec({"Chest": (0.03, 0, 0), "Spine": (0.02, 0, 0)})}
    for k in range(8):
        lib["Walk%d" % k] = spec({**walk_table(walk, k / 8), **tail_sway(n_tails, k / 8 * 2 * math.pi, 0.12)})
    for name in ("Sit", "Fly", "TailSway", "Walk2"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Sit", "Fly", "TailSway", "TailSway2", "SwayGame", "SwayWorst", "FanOut") + tuple("Walk%d" % k for k in range(8)):
        pose(rig, lib[name])
        print("CLEARANCE", name, tail_clearance(rig, posed_body_tree(body)), flush=True)
    pose(rig, {})

    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    if STAGE == "all":
        review_stage()
        tiles = {}
        MAIN = ["front", "side", "back", "q34", "game"]
        for k, p in zip(MAIN, render_views("paint", MAIN)):
            tiles["paint_" + k] = p
        for k, p in zip(("backflat", "top"), numbered_views("count", chains, ["backflat", "top"])):
            tiles["count_" + k] = p
        pose(rig, lib["FanOut"])
        tiles["fanout"] = render_views("fanout", ["back"])[0]
        pose(rig, lib["Walk2"])
        tiles["walk"] = render_views("walk", ["q34"])[0]
        pose(rig, lib["Sit"])
        tiles["sit"] = render_views("sit", ["q34"])[0]
        pose(rig, {})
        baked = body.data.materials[0]
        clay = clay_material(bpy.data.images[PET + "_Normal"])
        body.data.materials[0] = clay
        for k, p in zip(MAIN, render_views("clay", MAIN)):
            tiles["clay_" + k] = p
        body.data.materials[0] = baked
        # beside the concept's side view, framed alike
        cam = bpy.data.objects["ShowCam"]
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 2.62
        cam.location = Vector((6, 0.02, 0.72))
        cam.rotation_euler = (Vector((0, 0.02, 0.72)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x = scene.render.resolution_y = 720
        scene.render.filepath = os.path.join(REVIEW, "concept_match.png")
        bpy.ops.render.render(write_still=True)
        cam.data.type = "PERSP"
        tiles["match"] = scene.render.filepath
        tiles["concept"] = CONCEPT_SIDE
        labels = {"paint_front": "front", "paint_side": "side", "paint_back": "back", "paint_q34": "3/4", "paint_game": "high 3/4 back (game camera)",
                  "clay_front": "clay + normal map: front", "clay_side": "clay + normal: side", "clay_back": "clay + normal: back", "clay_q34": "clay + normal: 3/4",
                  "clay_game": "clay + normal: game camera", "concept": "concept: side", "match": "game mesh: side", "walk": "mid-trot", "sit": "sitting",
                  "count_backflat": "straight back: tails numbered", "count_top": "top: tails numbered", "fanout": "special: tails fanned out"}
        rows = [["paint_front", "paint_side", "paint_back", "paint_q34", "paint_game"], ["clay_front", "clay_side", "clay_back", "clay_q34", "clay_game"],
                ["concept", "match", "walk", "sit"], ["count_backflat", "count_top", "fanout"]]
        sheet_path = os.path.join(pet_kit.ROOT, "renders", "pets", "ExclusiveEgg", PET + "_gen_review.png")
        os.makedirs(os.path.dirname(sheet_path), exist_ok=True)
        print("SHEET", review_sheet(tiles, rows, sheet_path, labels), flush=True)
        scene.render.resolution_x = scene.render.resolution_y = 540
        path = save_all((0.62, -0.72, 0.25, 5.0, VIEW_AT))
        # written again with only the scene and what it uses: a full save keeps the window manager's stale bytes, a path from this machine
        # among them (seen in this .blend and the Moonfang Tiger's); the egg's .blend is written this way too
        bpy.data.libraries.write(path, {scene}, path_remap="RELATIVE_ALL", compress=True)
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, []), flush=True)
    print("DONE", flush=True)

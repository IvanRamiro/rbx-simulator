"""The Bonefire Dragon (Legendary, Spectral fire; Magma Heart Egg and Phoenix Ash Egg): "The bones of a dragon that refused to finish dying, with a blue
soul flame still burning in its ribs."

Recreated from its name and lore, with nothing of its old block skeleton (the owner, 2026-11-11: "Now proceed with bonefire dragon / Another dragon but
different style"). Its reference is the dracolich of dark fantasy: a horned skull with fire in its sockets and jaws, a great ribcage lit from inside, a
row of spines down its back. Its own design language: a hulking dragon of bare bone that the soul fire in its chest holds together and up off the
ground. It hangs in the air in a predator's crouch, head low and forward, forefeet reaching, hind feet drawn under it; a broad barrel of a ribcage with
the soul fire burning inside it like a bonfire in a cage, the bones round it scorched black where the flames lick them; tall blades of spine along its
back, highest over its shoulders; a long heavy skull with deep sockets that hold two blue flames under heavy bony brows, open holes behind and before
the eyes, rows of fangs and the fire showing in its throat; two great ram horns curled round the sides of its head; the bare bones of its wings, raised
and half folded behind its shoulders like the branches of a burnt tree, every membrane long since burnt away; thick knotted limb bones and black bone
talons; a long tail of vertebrae ending in a spiked knot of fused bone. Old ivory bone, yellowed and cracked; horns of dark weathered horn.

Unlike every other dragon here: no skin or scales (the Azure Sky, the Sunscale, the Pearl), no wings for arms or torn membranes (the Thunderclaw), no
hide split by glowing cracks (the Dreadfang Cerberus); its great ram horns are no other pet's (the Cloud Sheep's are a lamb's small curls); the
fire is only in its chest, eyes and throat.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/bonefire_dragon.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It never touches the ground: the game holds it in the air. The maps go to assets/pets/MagmaHeartEgg/.

What touches what: the skull and its lower jaw meet at the hinge; the horns root in the skull; the brows sit over the sockets; each eye's flame sits in
its socket; the vertebrae touch their neighbours from the skull to the tail's knot; every rib springs from its vertebra and the front ribs meet the
breastbone; the shoulder blades lie on the front ribs and the hip bones on the hips' vertebrae; each leg springs from its shoulder or hip socket; each
wing's bones spring from the top of its shoulder blade; the teeth sit in the jaws; the talons on the toes; the soul fire fills the chest and licks up to
the spine.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (Matrix and Vector: the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "BonefireDragon"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "MagmaHeartEgg")


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


# ---------- the frame of it: crouched in the air ----------
# the spine from the hips to the withers, rising a little toward the shoulders
SPINE = catmull([V(0, 0.3, 0.64), V(0, 0.17, 0.665), V(0, 0.04, 0.685), V(0, -0.09, 0.7), V(0, -0.2, 0.71)], 10)
# the neck: short and massive, up from the withers, then forward and down: the head carried low, a predator's
NECK = catmull([V(0, -0.2, 0.718), V(0, -0.29, 0.79), V(0, -0.38, 0.82), V(0, -0.455, 0.812), V(0, -0.51, 0.786)], 10)
# the tail: back from the hips, sinking, then rising a little to its knot
TAIL = catmull([V(0, 0.3, 0.64), V(0, 0.43, 0.6), V(0.02, 0.56, 0.55), V(0.06, 0.68, 0.515), V(0.085, 0.8, 0.505), V(0.085, 0.9, 0.525),
                V(0.07, 0.97, 0.56)], 10)
# the skull: big and heavy, a broad wedge pitched down to a blunt snout, broadest over the brows and behind them
HEAD_Y = (-0.505, -0.835)
HEAD_Z = (0.805, 0.705)
HEAD_W = ((0, 0.066), (0.08, 0.096), (0.22, 0.11), (0.36, 0.106), (0.52, 0.084), (0.72, 0.068), (0.88, 0.061), (0.96, 0.05), (1, 0.02))
HEAD_HT = ((0, 0.066), (0.1, 0.084), (0.28, 0.088), (0.44, 0.07), (0.68, 0.056), (0.88, 0.05), (0.96, 0.04), (1, 0.016))
HEAD_HB = ((0, 0.06), (0.25, 0.055), (0.5, 0.04), (0.8, 0.03), (0.95, 0.024), (1, 0.01))
# the lower jaw: a heavy U of bone hinged under the back of the skull, hanging a little open
JAW_HINGE = V(0, -0.55, 0.735)
JAW_LEN = 0.278
JAW_DROP = 0.07
JAW_OPEN = math.radians(15)
JAW_W = ((0, 0.084), (0.25, 0.076), (0.6, 0.062), (0.88, 0.054), (0.97, 0.042), (1, 0.014))
JAW_HT = ((0, 0.02), (0.5, 0.014), (1, 0.008))
JAW_HB = ((0, 0.056), (0.2, 0.046), (0.55, 0.036), (0.9, 0.03), (1, 0.012))
JAW_M = Matrix.Translation(JAW_HINGE) @ Matrix.Rotation(JAW_OPEN, 4, V(1, 0, 0)) @ Matrix.Translation(-JAW_HINGE)
# the eye sockets: deep, under the brows, looking out and forward
EYE_C = V(0.076, -0.638, 0.806)
EYE_AXIS = V(0.72, -0.62, 0.3).normalized()
SOCKET_R = 0.04          # the socket's reach from its centre, at most
SOCKET_W, SOCKET_H = 0.044, 0.03     # its half-length (along) and half-height: an oval
SOCKET_TILT = 16.0                # degrees: its front end lower
# the ribs: six pairs, broad round a barrel chest; the front four meet the breastbone, the back two end free
RIB_Y = (-0.158, -0.094, -0.03, 0.034, 0.098, 0.158)
RIB_W = (0.15, 0.178, 0.192, 0.19, 0.175, 0.152)        # half-width at its widest
RIB_DEPTH = (0.262, 0.282, 0.282, 0.27, 0.22, 0.175)    # how far below the spine it reaches
RIB_FREE = (False, False, False, False, True, True)
STERNUM = catmull([V(0, -0.215, 0.462), V(0, -0.15, 0.425), V(0, -0.08, 0.41), V(0, 0.0, 0.418), V(0, 0.045, 0.432)], 8)
SOUL_C = V(0, -0.03, 0.565)        # the heart of the fire
# the shoulder blades and hip bones (left), each from its top edge to its socket
SCAPULA = (V(0.11, -0.24, 0.76), V(0.19, -0.165, 0.555))
ILIUM = (V(0.07, 0.24, 0.715), V(0.145, 0.31, 0.59))
# the legs (left): socket, elbow or knee, wrist or ankle, the ball of the foot
FORE = [V(0.19, -0.165, 0.555), V(0.205, -0.1, 0.44), V(0.19, -0.225, 0.36), V(0.182, -0.275, 0.33)]
FORE_R = (0.05, 0.04, 0.031)          # upper bone, lower bone, the foot's bones
HIND = [V(0.145, 0.31, 0.59), V(0.19, 0.205, 0.475), V(0.178, 0.33, 0.38), V(0.168, 0.29, 0.3)]
HIND_R = (0.058, 0.044, 0.033)
# the wings (left): the bare bones, raised and half folded behind the shoulder, gnarled like the branches of a burnt tree
WING_ROOT = V(0.11, -0.22, 0.77)
WING_ELBOW = V(0.27, -0.05, 0.93)
WING_WRIST = V(0.31, -0.2, 1.08)
FINGERS = [V(0.39, -0.06, 1.2), V(0.455, 0.1, 1.09), V(0.42, 0.25, 0.96)]
# the ram horns: from the top of the skull behind the brows, up and back, down round the coil and forward beside the cheek, the tip turning out
HORN_ROOT = V(0.062, -0.555, 0.862)
HORN_C = V(0.15, -0.5, 0.775)          # the coil's centre (left)
HORN_TURNS = 0.9


# ---------- shapes ----------
def frame_of(tan, hint=V(0, 0, 1)):
    """A frame round a direction: (tan, side, up), up as near `hint` as it can be."""
    tan = tan.normalized()
    side = tan.cross(hint)
    side = side.normalized() if side.length > 1e-5 else tan.orthogonal().normalized()
    return tan, side, side.cross(tan).normalized()


def ellipsoid(m, c, axes, radii, seg=32, rings=20):
    """A ball stretched along three axes (unit vectors)."""
    a, b, d = (ax.normalized() * r for ax, r in zip(axes, radii))
    if a.cross(b).dot(d) < 0:
        d = -d           # a mirrored frame: keep it right-handed, so the ball's faces still point out
    mat = Matrix(((a.x, b.x, d.x, c.x), (a.y, b.y, d.y, c.y), (a.z, b.z, d.z, c.z), (0, 0, 0, 1)))
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=mat)


def line(a, b, n=6):
    return [a.lerp(b, t) for t in np.linspace(0, 1, n)]


def path_at(path, f):
    k = min(max(f, 0.0), 1.0) * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def tangent_at(path, f):
    return (path_at(path, min(1.0, f + 0.01)) - path_at(path, max(0.0, f - 0.01))).normalized()


def long_bone(m, a, b, r, sides, rings=None, knob=0.5, bow=0.0, condyles=True, ring_scale=1.0):
    """A limb bone from a to b: a waisted shaft, its ends swelling into knobs; two condyles at its far end."""
    d = b - a
    t, s, u = frame_of(d)
    mid = a.lerp(b, 0.5) + u * bow * d.length
    rings = rings or (8 if ring_scale >= 1 else 4)
    pts = catmull([a, mid, b], max(2, rings // 2))

    def rfn(f):
        e = max(0.0, 1 - min(f, 1 - f) / 0.22)
        return r * (0.78 + knob * e * e)
    m.tube(pts, rfn, sides=sides)
    if condyles:
        for k in (1, -1):
            ellipsoid(m, b - t * r * 0.2 + s * (k * r * 0.48), (t, s, u), (r * 0.62, r * 0.55, r * 0.66), max(6, int(16 * ring_scale)), max(4, int(10 * ring_scale)))


def tapered(m, pts, r0, r1, sides, power=1.0, flat=1.0, plane=V(1, 0, 0)):
    m.tube(pts, lambda f: r0 + (r1 - r0) * f ** power, sides=sides, flat=flat, plane=plane)


# ---------- the skull ----------
def head_centre(f):
    return V(0, HEAD_Y[0] + (HEAD_Y[1] - HEAD_Y[0]) * f, HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f)


def jaw_centre(f):
    return JAW_HINGE + V(0, -JAW_LEN * f, -0.006 - JAW_DROP * f)


def head_loft(m, centre, w, ht, hb, rings=48, sides=40, xform=None):
    """A closed loft along y: centre(f) the middle line, w/ht/hb (f) half-width, height above, depth below. xform: a matrix applied to every point."""
    bm = m.bm
    ring_verts = []
    for i in range(rings + 1):
        f = i / rings
        c = centre(f)
        ring = []
        for k in range(sides):
            a = TAU * k / sides
            sn, cs = math.sin(a), math.cos(a)
            p = c + V(prof(w, f) * math.copysign(abs(cs) ** 0.8, cs), 0, (prof(ht, f) if sn > 0 else prof(hb, f)) * math.copysign(abs(sn) ** 0.85, sn))
            ring.append(bm.verts.new(xform @ p if xform is not None else p))
        ring_verts.append(ring)
    for i in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((ring_verts[i][k], ring_verts[i][k2], ring_verts[i + 1][k2], ring_verts[i + 1][k]))
    bm.faces.new(list(reversed(ring_verts[0])))
    bm.faces.new(ring_verts[-1])


def head_surface(x, y, top=True):
    f = min(max((y - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0]), 0.0), 1.0)
    cz = HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f
    cs = min(1.0, abs(x) / prof(HEAD_W, f)) ** (1 / 0.8)
    sn = math.sqrt(max(0.0, 1 - cs * cs)) ** 0.85
    return cz + prof(HEAD_HT, f) * sn if top else cz - prof(HEAD_HB, f) * sn


def head_x(y, z):
    """The skull's half-width at (y, z): how far out its side lies there."""
    f = min(max((y - HEAD_Y[0]) / (HEAD_Y[1] - HEAD_Y[0]), 0.0), 1.0)
    cz = HEAD_Z[0] + (HEAD_Z[1] - HEAD_Z[0]) * f
    h = prof(HEAD_HT, f) if z > cz else prof(HEAD_HB, f)
    sn = min(1.0, abs(z - cz) / h) ** (1 / 0.85)
    return prof(HEAD_W, f) * math.sqrt(max(0.0, 1 - sn * sn)) ** 0.8


def socket_frame():
    """The socket's own frame: out along its axis, s along its long side (forward), u across it; tilted so its front end sits lower (a glare)."""
    t, s, u = frame_of(EYE_AXIS)
    if (EYE_C + s).y > EYE_C.y:
        s = -s
        u = -u if u.z < 0 else u
    a = math.radians(SOCKET_TILT)
    s2 = s * math.cos(a) - u * math.sin(a)
    u2 = u * math.cos(a) + s * math.sin(a)
    return t, s2.normalized(), u2.normalized()


# the openings of the skull: the sockets, the holes behind them and before them, the nostrils (left; each a cutter: centre, axes, radii)
def skull_holes():
    out = []
    t, s, u = socket_frame()
    out.append((EYE_C + EYE_AXIS * 0.012, (EYE_AXIS, s, u), (0.05, SOCKET_W, SOCKET_H)))
    # behind the eye, high on the side of the skull: a long oval opening
    c = V(head_x(-0.575, 0.818) + 0.006, -0.575, 0.818)
    out.append((c, (V(1, 0, 0), V(0, 1, 0.25), V(0, -0.25, 1)), (0.036, 0.03, 0.02)))
    # before the eye: a long teardrop-shaped opening down the snout's side
    c = V(head_x(-0.725, 0.768) + 0.008, -0.725, 0.768)
    out.append((c, (V(1, 0, 0), V(0, 1, 0.22), V(0, -0.22, 1)), (0.03, 0.036, 0.015)))
    # the nostril, near the tip of the snout, on top
    c = V(0.026, -0.828, head_surface(0.026, -0.828) + 0.004)
    out.append((c, (V(0, 0, 1), V(0, 1, 0), V(1, 0, 0)), (0.028, 0.018, 0.011)))
    return out


def cut(o, cutters_mesh_fn, name):
    """Boolean difference of o with the cutters a Mesh-filling function makes."""
    m = Mesh()
    cutters_mesh_fn(m)
    k = m.finish(name, HI)
    md = o.modifiers.new("cut", "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.object = k
    md.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data
    o.modifiers.clear()
    o.data = me
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(k, do_unlink=True)


def build_skull(fine=0.0022):
    m = Mesh()
    head_loft(m, head_centre, HEAD_W, HEAD_HT, HEAD_HB)
    for side in (1, -1):
        # the cheekbone: an arch from under the eye back to the hinge, standing a little off the side of the skull
        arch = [mir(V(head_x(y_, z_) + off, y_, z_), side) for y_, z_, off in ((-0.71, 0.765, -0.006), (-0.66, 0.762, 0.008), (-0.605, 0.758, 0.012),
                                                                                 (-0.56, 0.75, 0.004))]
        m.tube(catmull(arch, 8), lambda f: 0.016 * (0.85 + 0.3 * math.sin(math.pi * f)), sides=18, flat=1.25, plane=V(0, 0, 1))
        # the back of the skull: a heavy crest over the neck, where the horns spring
        ellipsoid(m, mir(V(0.044, -0.545, 0.842), side), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.052, 0.056, 0.044), 28, 18)
        # the ridge along the top of the snout, from the brow to the nostril
        ridge = [mir(V(x_, y_, head_surface(x_, y_) - 0.003), side) for x_, y_ in ((0.044, -0.7), (0.04, -0.76), (0.032, -0.81))]
        m.tube(catmull(ridge, 6), lambda f: 0.0095 * math.sin(math.pi * (0.04 + 0.92 * f)) ** 0.6 + 0.0006, sides=14, caps=False)
        # the jaw's hinge knob, under the back of the skull, where the jaw meets it
        ellipsoid(m, mir(V(0.074, -0.553, 0.742), side), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.028, 0.03, 0.026), 20, 12)
    # the condyle where the neck meets the skull
    ellipsoid(m, V(0, -0.505, 0.79), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.04, 0.04, 0.04), 24, 16)
    o = m.finish(N + "SkullHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.004, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])

    def cutters(c):
        for side in (1, -1):
            for centre, axes, radii in skull_holes():
                ax = tuple(mir(a, side) if side < 0 else a for a in axes)
                ellipsoid(c, mir(centre, side), ax, radii, 32, 20)
    cut(o, cutters, N + "SkullCut")
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": fine, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 3})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_jaw(fine=0.0022):
    m = Mesh()
    head_loft(m, jaw_centre, JAW_W, JAW_HT, JAW_HB, rings=40, sides=32, xform=JAW_M)
    for side in (1, -1):
        # the back of the jaw rising to the hinge, under the skull's knob
        ellipsoid(m, mir(V(0.074, -0.556, 0.728), side), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.024, 0.032, 0.026), 20, 12)
    o = m.finish(N + "JawHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.004, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 3})])

    def cutters(c):
        for side in (1, -1):
            # an opening in the side of the jaw, toward its back
            f = 0.3
            jc = jaw_centre(f)
            p = JAW_M @ V(side * (prof(JAW_W, f) + 0.004), jc.y, jc.z - 0.01)
            ellipsoid(c, p, (V(1, 0, 0), JAW_M.to_3x3() @ V(0, 1, 0), JAW_M.to_3x3() @ V(0, 0, 1)), (0.03, 0.04, 0.014), 28, 16)
    cut(o, cutters, N + "JawCut")
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": fine, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.8, "iterations": 3})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the backbone: neck, back and tail ----------
NECK_UNITS = 6
BACK_UNITS = 7
TAIL_UNITS = 14


def vertebra_list():
    """Every vertebra: centre, along (its path's direction), up, radius, length, spine height, its region and its fraction along that region."""
    out = []
    # the neck: thick, close-set, each with a short blade and wings of bone to the sides
    for k in range(NECK_UNITS):
        f = (k + 0.5) / NECK_UNITS
        c = path_at(NECK, 1 - f)
        tan = -tangent_at(NECK, 1 - f)            # toward the head
        _, _, up = frame_of(tan)
        out.append((c, tan, up, 0.05 + 0.01 * f, 0.07, 0.055 + 0.07 * f, "neck", f))
    # the back: the tallest blades over the shoulders, falling toward the hips
    for k in range(BACK_UNITS):
        f = (k + 0.5) / BACK_UNITS
        c = path_at(SPINE, 1 - f)
        tan = -tangent_at(SPINE, 1 - f)
        _, _, up = frame_of(tan)
        out.append((c, tan, up, 0.054, 0.076, 0.17 - 0.08 * f, "back", f))
    # the tail: shrinking toward the knot
    for k in range(TAIL_UNITS):
        f = (k + 0.5) / TAIL_UNITS
        c = path_at(TAIL, f * 0.96)
        tan = -tangent_at(TAIL, f * 0.96)
        _, _, up = frame_of(tan)
        r = 0.05 * (1 - 0.6 * f)
        out.append((c, tan, up, r, 0.074 * (1 - 0.3 * f), 0.08 * (1 - 0.8 * f) + 0.01, "tail", f))
    return out


def spool_halves(units, clear=0.003):
    """Each vertebra's spool half-length: overlapping its neighbours so the column is unbroken, but never with an end in the plane of a neighbour's end
    (two caps there z-fight): a spool whose cap lands within `clear` of a near spool's parallel cap is shortened until it doesn't. The first, by the
    skull, reaches deeper into the skull's condyle."""
    halves = [length * 0.56 * (1.3 if j == 0 else 1.0) for j, (c, tan, up, r, length, *_rest) in enumerate(units)]
    for _ in range(40):
        moved = False
        for j, (cj, tj, *_a) in enumerate(units):
            for k, (ck, tk, *_b) in enumerate(units):
                if k <= j or (cj - ck).length > 0.2 or abs(tj.normalized().dot(tk.normalized())) < 0.995:
                    continue
                n = tj.normalized()
                for sj in (1, -1):
                    for sk in (1, -1):
                        pj = cj + tj.normalized() * (sj * halves[j])
                        pk = ck + tk.normalized() * (sk * halves[k])
                        if abs((pj - pk).dot(n)) < clear:
                            halves[j] -= 0.004
                            moved = True
        if not moved:
            break
    return halves


def build_vertebrae(name, coll, res=1.0):
    """Each vertebra a spool of bone (its ends flared), a blade standing up from it, leaning back, wings of bone to the sides, and under the tail a
    small chevron. Each vertex carries its vertebra's number ("unit")."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("unit")
    sides = max(6, int(18 * res))
    units = vertebra_list()
    halves = spool_halves(units)
    for j, (c, tan, up, r, length, spine_h, region, f) in enumerate(units):
        before = set(bm.verts)
        t, s, u = frame_of(tan, up)
        # the spool, its two ends flared a little: overlapping its neighbours so the column is unbroken
        half = halves[j]
        m.tube(line(c - t * half, c + t * half, 5 if res >= 1 else 3), lambda f_, r=r: r * (0.78 + 0.28 * abs(2 * f_ - 1) ** 2), sides=sides)
        # the blade: flattened along the column, leaning back (toward the tail)
        base = c + u * r * 0.5
        tip = c + u * (r + spine_h) + t * (-spine_h * (0.45 if region != "neck" else 0.6))
        blade_sides = max(6, int(12 * res))
        blade_sides += blade_sides % 2      # (even: an odd count puts a face square to the column, in the plane of the spool's end)
        tapered(m, catmull([base, base.lerp(tip, 0.5) + t * (-0.004), tip], max(2, int(4 * res))), r * 0.5, 0.005, blade_sides,
                power=0.8, flat=2.4, plane=t)
        # the side wings of bone
        if region != "tail" or f < 0.7:
            for k in (1, -1):
                a = c + s * (k * r * 0.6)
                b = c + s * (k * (r + 0.034 * (1.25 if region == "back" else 1.0))) - u * 0.01 + t * (-0.008)
                tapered(m, line(a, b, 3 if res >= 1 else 2), r * 0.38, r * 0.18, max(4, int(10 * res)))
        if region == "tail" and f < 0.8:
            a = c - u * r * 0.6
            b = c - u * (r + 0.04 * (1 - f)) + t * (-0.014)
            tapered(m, line(a, b, 3 if res >= 1 else 2), r * 0.32, 0.003, max(4, int(10 * res)))
        layer = bm.verts.layers.int["unit"]
        for v in bm.verts:
            if v not in before:
                v[layer] = j
    return m.finish(name, coll)


# ---------- the tail's knot: fused bone, bristling ----------
KNOT_C = TAIL[-1] + (TAIL[-1] - TAIL[-2]).normalized() * 0.02


def knot_spikes():
    out = []
    tan = tangent_at(TAIL, 1.0)
    t, s, u = frame_of(tan)
    for k in range(7):
        a = TAU * k / 7 + 0.3
        d = (s * math.cos(a) + u * math.sin(a)) * 0.85 + t * 0.55
        out.append((KNOT_C + d.normalized() * 0.03, KNOT_C + d.normalized() * (0.11 + 0.025 * (k % 2))))
    out.append((KNOT_C + t * 0.04, KNOT_C + t * 0.14))
    return out


def build_knot(name, coll, res=1.0):
    m = Mesh()
    tan = tangent_at(TAIL, 1.0)
    t, s, u = frame_of(tan)
    ellipsoid(m, KNOT_C, (s, t, u), (0.05, 0.06, 0.047), max(10, int(28 * res)), max(6, int(18 * res)))
    for a, b in knot_spikes():
        tapered(m, catmull([a - (b - a).normalized() * 0.016, a.lerp(b, 0.5), b], max(2, int(4 * res))), 0.02, 0.003, max(5, int(12 * res)), power=1.1)
    return m.finish(name, coll)


# ---------- the ribs and the breastbone ----------
def rib_path(k, side, n=14):
    """A rib (left or right): from beside its vertebra, out round the barrel, in to the breastbone (or ending free), swept back as it falls."""
    y = RIB_Y[k]
    z0 = path_at(SPINE, (y - SPINE[0].y) / (SPINE[-1].y - SPINE[0].y)).z
    w, depth = RIB_W[k], RIB_DEPTH[k]
    pts = []
    for i in range(n + 1):
        f = i / n
        a = math.pi * 0.5 - math.pi * 0.98 * f            # from the top (90 degrees) round the side to the bottom
        x = 0.03 + (w - 0.03) * max(0.0, math.cos(a)) ** 0.8
        z = z0 - depth * (1 - math.sin(a)) * 0.5
        pts.append(V(side * x, y + 0.045 * f ** 1.4, z))
    if RIB_FREE[k]:
        pts = pts[:int(n * 0.72) + 1]
    else:
        end = path_at(STERNUM, min(1.0, (y + 0.215 + 0.045) / 0.26))
        pts[-1] = V(side * 0.016, end.y, end.z + 0.012)
    return catmull(pts, 3)


def build_ribs(name, coll, res=1.0):
    """Each rib a flat band of bone; the breastbone a deep keel under the chest. Each vertex carries its rib ("rib", -1 for the breastbone)."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("rib")
    sides = max(6, int(14 * res))
    for k in range(len(RIB_Y)):
        for side in (1, -1):
            before = set(bm.verts)
            pts = rib_path(k, side)
            if res < 1:
                pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
            free = RIB_FREE[k]
            m.tube(pts, lambda f, free=free: 0.019 * (1.15 - 0.3 * f) * (1 - 0.6 * smooth(0.8, 1.0, f) if free else 1), sides=sides, flat=1.38,
                   plane=V(0, 1, 0))
            layer = bm.verts.layers.int["rib"]
            for v in bm.verts:
                if v not in before:
                    v[layer] = k
    before = set(bm.verts)
    # (every other point at game resolution, keeping the last once: repeated, it collapsed a ring and its faces to nothing)
    m.tube(STERNUM if res >= 1 else STERNUM[::2] + ([STERNUM[-1]] if (len(STERNUM) - 1) % 2 else []), lambda f: 0.028 * (1 - 0.3 * f), sides=max(8, int(18 * res)), flat=0.55)
    for v in bm.verts:
        if v not in before:
            v[bm.verts.layers.int["rib"]] = -1
    return m.finish(name, coll)


# ---------- shoulders, hips, legs, feet ----------
def build_girdles(name, coll, res=1.0):
    """The shoulder blades, lying on the front ribs, and the hip bones each side of the hips' vertebrae, with their sockets."""
    m = Mesh()
    seg, rings = max(10, int(32 * res)), max(6, int(18 * res))
    for side in (1, -1):
        for (top, sock), width in ((SCAPULA, 0.078), (ILIUM, 0.07)):
            a, b = mir(top, side), mir(sock, side)
            along = (b - a).normalized()
            out = V(side, 0, 0)
            normal = (out - along * along.dot(out)).normalized()
            across = along.cross(normal).normalized()
            ellipsoid(m, a.lerp(b, 0.45), (along, across, normal), ((b - a).length * 0.62, width, 0.017), seg, rings)
            ellipsoid(m, b, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.046, 0.048, 0.046), max(8, int(20 * res)), max(5, int(12 * res)))
        # the bars of the hip below its socket, back toward the tail
        long_bone(m, mir(ILIUM[1], side) + V(0, 0.004, -0.01), mir(V(0.05, 0.38, 0.53), side), 0.022, max(6, int(14 * res)), knob=0.4, condyles=False)
    return m.finish(name, coll)


def foot_frame(knots, side):
    a, b = mir(knots[2], side), mir(knots[3], side)
    fwd = V(0, -1, 0)
    down = (b - a).normalized()
    across = V(side, 0, 0)
    return b, fwd, across, down


def toe_list(knots, side, fore):
    """Per toe: its knuckles from the ball of the foot out, and the last's direction for its talon. Three forward and spread, one behind."""
    ball, fwd, across, down = foot_frame(knots, side)
    out = []
    reach = 0.07 if fore else 0.076
    for a in (-0.42, 0.0, 0.42):
        d = (fwd * math.cos(a) + across * math.sin(a) * side).normalized()
        k0 = ball + d * 0.008
        k1 = k0 + d * reach * 0.5 + V(0, 0, -0.008)
        k2 = k1 + d * reach * 0.5 + V(0, 0, -0.01)
        out.append([k0, k1, k2])
    back = ball - fwd * 0.014 + across * 0.008 + V(0, 0, -0.004)
    out.append([back, back - fwd * 0.022 + V(0, 0, -0.008), back - fwd * 0.04 + V(0, 0, -0.012)])
    return out


def talon_path(toe):
    a, b = toe[-2], toe[-1]
    d = (b - a).normalized()
    return [b - d * 0.008, b + d * 0.02 + V(0, 0, -0.004), b + d * 0.038 + V(0, 0, -0.018), b + d * 0.042 + V(0, 0, -0.036)]


LEG_SET = (("FL", 1, FORE, FORE_R, True), ("FR", -1, FORE, FORE_R, True), ("BL", 1, HIND, HIND_R, False), ("BR", -1, HIND, HIND_R, False))


def build_legs(name, coll, res=1.0):
    """Each leg's bones: the upper, the lower (with its twin, as in a real forearm or shin), the foot's long bones, and three toes forward and one
    behind, each of knuckled bones. Each vertex carries its leg ("leg") and segment ("seg": 0 upper, 1 lower, 2 foot, 3 toes)."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("leg")
    bm.verts.layers.int.new("seg")
    sides = max(6, int(18 * res))

    def tag(before, leg, seg):
        for v in bm.verts:
            if v not in before:
                v[bm.verts.layers.int["leg"]] = leg
                v[bm.verts.layers.int["seg"]] = seg
    for j, (key, side, knots, radii, fore) in enumerate(LEG_SET):
        p = [mir(k, side) for k in knots]
        before = set(bm.verts)
        long_bone(m, p[0], p[1], radii[0], sides, knob=0.55, bow=0.05 if fore else -0.05, ring_scale=res)
        tag(before, j, 0)
        before = set(bm.verts)
        long_bone(m, p[1], p[2], radii[1], sides, knob=0.5, ring_scale=res)
        # its twin bone, thinner, beside it
        off = V(side * radii[1] * 0.9, 0, 0)
        long_bone(m, p[1] + off * 0.7, p[2] + off, radii[1] * 0.55, max(5, sides // 2), knob=0.45, condyles=False, ring_scale=res)
        tag(before, j, 1)
        before = set(bm.verts)
        long_bone(m, p[2], p[3], radii[2], sides, knob=0.45, ring_scale=res)
        ellipsoid(m, p[3], (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (radii[2] * 1.25, radii[2] * 1.2, radii[2] * 1.05), max(6, int(20 * res)), max(4, int(12 * res)))
        tag(before, j, 2)
        before = set(bm.verts)
        for toe in toe_list(knots, side, fore):
            for k, (a, b, r) in enumerate(((toe[0], toe[1], 0.016), (toe[1], toe[2], 0.0135))):
                if k:          # sunk into the bone before it: two caps in one plane z-fight
                    a = a - (b - a).normalized() * r * 0.7
                long_bone(m, a, b, r, max(5, int(12 * res)), knob=0.5, condyles=False, ring_scale=res)
                if res >= 1:          # (the game mesh's knobbed bone ends carry the knuckle)
                    ellipsoid(m, b, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (r * 1.15,) * 3, 12, 8)
        tag(before, j, 3)
    return m.finish(name, coll)


def build_talons(name, coll, res=1.0):
    """Black bone talons, thick and hooked, on every toe. Each vertex carries its leg ("leg") and how far along its talon ("along")."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("leg")
    bm.verts.layers.float.new("along")
    sides = max(4, int(12 * res)) if res < 1 else 12
    for j, (key, side, knots, radii, fore) in enumerate(LEG_SET):
        for toe in toe_list(knots, side, fore):
            pts = catmull(talon_path(toe), max(2, int(4 * res)))
            before = set(bm.verts)
            m.tube(pts, lambda f: 0.0145 * (1 - f) ** 0.95 + 0.0016, sides=sides)
            for i, v in enumerate([v for v in bm.verts if v not in before]):
                v[bm.verts.layers.int["leg"]] = j
                v[bm.verts.layers.float["along"]] = (i // sides) / (len(pts) - 1) if i // sides < len(pts) else 1.0
    return m.finish(name, coll)


# ---------- the wings: bare bones ----------
def wing_frame(side):
    return mir(WING_ROOT, side), mir(WING_ELBOW, side), mir(WING_WRIST, side), [mir(p, side) for p in FINGERS]


def finger_pts(wrist, tip, side, k):
    """A wing finger, crooked like a dead branch: two knuckles, a little bend at each."""
    d = tip - wrist
    t, s, u = frame_of(d)
    a = wrist.lerp(tip, 0.36) + s * (side * 0.016) + u * 0.02
    b = wrist.lerp(tip, 0.7) - s * (side * 0.012) + u * 0.008
    return [wrist, a, b, tip]


def build_wing_bones(name, coll, res=1.0):
    """The arm (upper and lower bone), the wrist's knuckle with a hooked thumb claw, three long jointed fingers, each ending in a hooked point. Each
    vertex carries its part ("kind": 0 upper arm, 1 forearm, 2 wrist and thumb, 3 finger), its finger ("finger") and how far along ("along")."""
    m = Mesh()
    bm = m.bm
    for key in ("kind", "finger"):
        bm.verts.layers.int.new(key)
    bm.verts.layers.float.new("along")
    sides = max(6, int(16 * res))

    def tag(before, kind, finger=-1, a0=0.0, a1=1.0, pts=None):
        new = [v for v in bm.verts if v not in before]
        if pts is not None:
            f, _ = nearest_on(pts, np.array([tuple(v.co) for v in new]))
        for i, v in enumerate(new):
            v[bm.verts.layers.int["kind"]] = kind
            v[bm.verts.layers.int["finger"]] = finger
            v[bm.verts.layers.float["along"]] = float(a0 + (a1 - a0) * f[i]) if pts is not None else a0
    for side in (1, -1):
        root, elbow, wrist, tips = wing_frame(side)
        before = set(bm.verts)
        long_bone(m, root, elbow, 0.04, sides, knob=0.55, bow=0.06, ring_scale=res)
        tag(before, 0, pts=[root, elbow])
        before = set(bm.verts)
        long_bone(m, elbow, wrist, 0.032, sides, knob=0.5, bow=-0.05, ring_scale=res)
        tag(before, 1, pts=[elbow, wrist])
        before = set(bm.verts)
        ellipsoid(m, wrist, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.042, 0.044, 0.042), max(8, int(22 * res)), max(6, int(14 * res)))
        # the thumb: a short bone forward, and its hooked claw
        th = [wrist, wrist + V(side * 0.014, -0.055, 0.016), wrist + V(side * 0.02, -0.092, -0.004), wrist + V(side * 0.018, -0.1, -0.034)]
        tapered(m, catmull(th, max(2, int(4 * res))), 0.02, 0.0025, max(5, int(12 * res)), power=1.2)
        tag(before, 2)
        for j, tip in enumerate(tips):
            pts = finger_pts(wrist, tip, side, j)
            before = set(bm.verts)
            r0 = 0.031 - 0.0025 * j
            for k, (a, b, r) in enumerate(((pts[0], pts[1], r0), (pts[1], pts[2], r0 * 0.85))):
                if k:
                    a = a - (b - a).normalized() * r * 0.7
                long_bone(m, a, b, r, max(6, int(14 * res)), knob=0.55, condyles=False, ring_scale=res)
                ellipsoid(m, b, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (r * 1.2,) * 3, max(6, int(14 * res)), max(4, int(9 * res)))
            # the last bone tapering to a hooked point
            d = (pts[3] - pts[2]).normalized()
            _, s_, u_ = frame_of(d)
            hook = [pts[2] - d * r0 * 0.6, pts[2].lerp(pts[3], 0.6), pts[3], pts[3] + d * 0.016 - u_ * 0.028]
            tapered(m, catmull(hook, max(2, int(4 * res))), r0 * 0.75, 0.0015, max(5, int(12 * res)), power=1.1)
            tag(before, 3, j, pts=pts)
    return m.finish(name, coll)


# ---------- the ram horns ----------
def horn_path(side, n=48):
    """From its root on the skull, up and back over the coil, down behind it, forward beside the cheek and up, the tip turning out: a ram's."""
    root = mir(HORN_ROOT, side)
    c = mir(HORN_C, side)
    ax = mir(V(1, -0.12, 0.08), side).normalized()        # the coil faces out from the head
    start = root - c
    start = start - ax * start.dot(ax)
    r0 = start.length
    e1 = start.normalized()
    e2 = ax.cross(e1).normalized()
    if e2.y < 0:          # the first turn goes back over the neck
        e2 = -e2
    pts = []
    for i in range(n + 1):
        f = i / n
        a = TAU * HORN_TURNS * f
        r = r0 * (1 - 0.56 * f)
        pts.append(c + (e1 * math.cos(a) + e2 * math.sin(a)) * r + ax * (0.085 * f ** 1.2))
    pts.insert(0, root + (root - pts[1]).normalized() * 0.02 - mir(V(0.01, 0, 0.008), side))      # its root sunk in the skull
    return pts


def horn_radius(f):
    return 0.044 * (1 - f) ** 0.8 + 0.004


def build_horns(name, coll, res=1.0):
    """Ridged ram horns; each vertex carries how far along its horn ("along")."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.float.new("along")
    sides = max(8, int(26 * res)) if res >= 1 else 11
    for side in (1, -1):
        pts = horn_path(side, max(30, int(72 * res)))
        before = set(bm.verts)
        if res >= 1:
            rfn = lambda f: horn_radius(f) * (1 + 0.09 * max(0.0, math.sin(f * 80)) ** 3 * (1 - 0.7 * f))     # the growth ridges round it
        else:
            rfn = horn_radius
        m.tube(pts, rfn, sides=sides, flat=1.2, plane=mir(V(1, 0, 0), side))
        new = [v for v in bm.verts if v not in before]
        f, _ = nearest_on(pts, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[bm.verts.layers.float["along"]] = float(ff)
    return m.finish(name, coll)


# ---------- the brows: heavy ridges of bone over the sockets (they hinge, to glare) ----------
def brow_path(side, n=12):
    """Over the upper rim of the socket, from before it to behind it, standing a little proud of the rim."""
    t, s, u = socket_frame()
    out = []
    for k in range(n + 1):
        a = math.radians(-74 + 148 * k / n)
        p = EYE_C + t * 0.004 + u * (math.cos(a) * SOCKET_H * 1.02) + s * (math.sin(a) * SOCKET_W * 1.05)
        out.append(p)
    if out[0].y > out[-1].y:
        out.reverse()          # from front (snout) to back
    back = out[-1]
    out.append(back + V(0.01, 0.03, 0.012))          # the spur, swept back
    return [mir(p, side) for p in out]


def brow_radius(f):
    return 0.0145 * (math.sin(math.pi * min(1.0, 0.08 + f * 1.15)) ** 0.5 if f < 0.75 else (1 - f) / 0.25 * 0.8) + 0.002


def build_brows(name, coll, res=1.0):
    m = Mesh()
    for side in (1, -1):
        m.tube(catmull(brow_path(side, max(6, int(12 * res))), max(2, int(3 * res))), brow_radius, sides=max(8, int(18 * res)), flat=1.25,
               plane=V(0, 0, 1))
    return m.finish(name, coll)


# ---------- teeth ----------
def tooth_list():
    """Teeth (left): root, direction, length, radius, on the lower jaw or not. Fangs at the front, top and bottom, crossing past each other, and a
    second pair a little behind them; set by where they fall along the skull or the jaw."""
    out = []
    for f, length, r in ((0.935, 0.05, 0.0088), (0.87, 0.026, 0.0058), (0.805, 0.028, 0.006), (0.735, 0.04, 0.0076), (0.665, 0.026, 0.0058),
                         (0.595, 0.023, 0.0054), (0.525, 0.02, 0.005), (0.455, 0.017, 0.0046)):
        y = HEAD_Y[0] + (HEAD_Y[1] - HEAD_Y[0]) * f
        x = prof(HEAD_W, f) * 0.8
        z = head_surface(x, y, top=False) + 0.007
        out.append((V(x, y, z), V(0.06, -0.1, -1).normalized(), length, r, False))
    for f, length, r in ((0.9, 0.044, 0.0082), (0.83, 0.024, 0.0056), (0.76, 0.026, 0.0058), (0.69, 0.034, 0.007), (0.62, 0.022, 0.0052),
                         (0.55, 0.019, 0.0048), (0.48, 0.016, 0.0044)):
        y = JAW_HINGE.y - JAW_LEN * f
        c = jaw_centre(f)
        local = V(prof(JAW_W, f) * 0.76, y, c.z + prof(JAW_HT, f) * 0.4)
        out.append((JAW_M @ local, JAW_M.to_3x3() @ V(0.06, -0.08, 1).normalized(), length, r, True))
    return out


def build_teeth(name, coll, res=1.0):
    m = Mesh()
    f_all, jaw = [], []
    sides, per = max(4, int(10 * res)), max(1, int(4 * res))
    for side in (1, -1):
        for root, d, length, r, low in tooth_list():
            r0, dd = mir(root, side), mir(d, side)
            path = catmull([r0 - dd * 0.009, r0 + dd * length * 0.5 + mir(V(0, -0.003, 0), side), r0 + dd * length], per)
            m.tube(path, lambda f, r=r: r * (1 - f) ** 0.8 + 0.0006, sides=sides)
            f_all += [i / (len(path) - 1) for i in range(len(path)) for _ in range(sides)]
            jaw += [low] * (len(path) * sides)
    return m.finish(name, coll), np.array(f_all), np.array(jaw)


# ---------- the soul fire, the eyes' flames, the throat's ----------
def build_soul(name, coll, res=1.0):
    """The fire in its chest: a burning heart, its flames licking up between the ribs to the spine."""
    m = Mesh()
    ellipsoid(m, SOUL_C, (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.092, 0.12, 0.085), max(12, int(32 * res)), max(8, int(20 * res)))
    for k, (x, y, h, lean) in enumerate(((0.0, -0.11, 0.16, -0.02), (0.058, -0.05, 0.14, 0.01), (-0.058, -0.05, 0.14, 0.01), (0.0, 0.02, 0.16, 0.03),
                                         (0.052, 0.075, 0.12, 0.03), (-0.052, 0.075, 0.12, 0.03), (0.0, 0.11, 0.11, 0.04))):
        base = SOUL_C + V(x, y, 0.02)
        top_ = base + V(x * 0.4, lean, h)
        mid = base.lerp(top_, 0.55) + V(-x * 0.3 + 0.012 * math.sin(k * 2.1), 0, 0)
        tapered(m, catmull([base, mid, top_], max(3, int(6 * res))), 0.048, 0.005, max(6, int(14 * res)), power=0.8)
    o = m.finish(name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.006 if res >= 1 else 0.011, "adaptivity": 0.0}),
                   ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    if res < 1:
        apply_mods(o, [("DECIMATE", {"decimate_type": "COLLAPSE", "ratio": 0.16})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def eye_flame_paths(side):
    """Each socket's fire: a bright point of light deep in the dark socket, and two flames streaming from the socket's back corner, up and back
    over the brow."""
    t, s, u = frame_of(EYE_AXIS)
    pupil = mir(EYE_C - EYE_AXIS * 0.012, side)
    corner = EYE_C + t * 0.004 + (u * 0.55 - s * 0.84).normalized() * SOCKET_R * 0.72      # the socket's back upper corner (s points forward: away from it)
    if (EYE_C + s).y < EYE_C.y:
        corner = EYE_C + t * 0.004 + (u * 0.55 + s * 0.84).normalized() * SOCKET_R * 0.72
    flames = []
    for k, (lift, back, out, r) in enumerate(((0.045, 0.1, 0.016, 0.0145), (0.018, 0.075, 0.03, 0.0105))):
        a = corner + V(0, 0, 0.002)
        tip = corner + V(out, back, lift)
        mid = a.lerp(tip, 0.45) + V(0.006, -0.004, 0.012)
        flames.append(([mir(a - EYE_AXIS * 0.012, side), mir(a, side), mir(mid, side), mir(tip, side)], r))
    return pupil, flames


def build_eye_flames(name, coll, res=1.0):
    m = Mesh()
    t, s, u = frame_of(EYE_AXIS)
    for side in (1, -1):
        pupil, _ = eye_flame_paths(side)
        # from the socket's floor out toward its mouth: a point of light seen deep in it, rooted in the bone
        ellipsoid(m, pupil - mir(EYE_AXIS, side) * 0.012, (mir(EYE_AXIS, side), mir(s, side), mir(u, side)), (0.021, 0.0095, 0.011), max(8, int(18 * res)),
                  max(6, int(12 * res)))
    return m.finish(name, coll)


def build_maw(name, coll, res=1.0):
    """The fire showing in its throat, between the jaws."""
    m = Mesh()
    ellipsoid(m, V(0, -0.62, 0.726), (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)), (0.04, 0.062, 0.02), max(8, int(20 * res)), max(5, int(12 * res)))
    return m.finish(name, coll)


# ---------- colours: old bone, black where the fire licks ----------
BONE, BONE_OLD, BONE_DARK = rgb(226, 214, 188), rgb(196, 178, 142), rgb(150, 132, 104)
GRIME, SOOT, SOOT_BLUE = rgb(86, 72, 58), rgb(26, 26, 34), rgb(40, 52, 90)
HORN, HORN_RIDGE, HORN_TIP = rgb(64, 54, 46), rgb(122, 106, 88), rgb(206, 192, 164)
TOOTH, TOOTH_ROOT = rgb(232, 224, 198), rgb(150, 128, 96)
TALON, TALON_TIP = rgb(22, 20, 22), rgb(84, 80, 84)
INSIDE = rgb(30, 26, 30)


def bone_colour(P, Nn, seed=0):
    """Old bone: ivory, yellowed in patches, fine pores and hairline cracks, darker in its hollows."""
    yellow = smooth(0.3, 0.75, fbm(P, 5.0, 4, 3 + seed))
    col = mix(np.broadcast_to(BONE, (len(P), 3)), BONE_OLD, yellow * 0.9)
    stain = smooth(0.55, 0.8, fbm(P, 2.2, 3, 29 + seed))
    col = mix(col, BONE_DARK, stain * 0.45)
    pores = 1 - smooth(0.0, 0.22, cells_d(P, 300.0, 7 + seed))
    col = mix(col, BONE_DARK, pores * 0.45)
    d1, d2 = cells2(P, 22.0, 11 + seed)
    crack = (1 - smooth(0.0, 0.045, d2 - d1)) * smooth(0.68, 0.8, fbm(P, 2.4, 2, 17 + seed))
    col = mix(col, GRIME, crack * 0.75)
    under = smooth(0.1, -0.8, Nn[:, 2])
    col = mix(col, col * 0.7, under * 0.55)
    top = smooth(0.4, 0.95, Nn[:, 2])
    col = mix(col, col * 1.06, top * 0.4)
    return col, crack, pores


def cells_d(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                d1 = np.minimum(d1, d)
    return d1


def cells2(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point: their difference is small along the cells' edges (a crack network)."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                d2 = np.where(d < d1, d1, np.minimum(d2, d))
                d1 = np.minimum(d1, d)
    return d1, d2


def scorch(P, Nn):
    """Black soot where the soul fire licks: near it, on faces turned toward it; a blue cast at its edge."""
    d = P - np.array(tuple(SOUL_C))
    dist = np.linalg.norm(d / np.array((1.0, 0.85, 0.75)), axis=1)
    facing = smooth(0.25, -0.35, (Nn * d).sum(1) / np.maximum(np.linalg.norm(d, axis=1), 1e-6))
    near = smooth(0.24, 0.1, dist)
    return np.clip(near * (0.35 + 0.65 * facing), 0, 1), smooth(0.3, 0.16, dist)


def paint_bones(o, seed=0, burn=True):
    P = verts(o)
    Nn = normals(o)
    col, crack, pores = bone_colour(P, Nn, seed)
    rough = 0.62 + 0.1 * crack
    if burn:
        s, edge = scorch(P, Nn)
        col = mix(col, mix(np.broadcast_to(SOOT_BLUE, (len(P), 3)), SOOT, smooth(0.3, 0.8, s)), np.clip(s * 1.1, 0, 0.95))
        col = mix(col, col * np.array((0.85, 0.92, 1.12)), edge * (1 - s) * 0.5)
        rough = rough + 0.12 * s
    relief = -0.0006 * crack - 0.0002 * pores
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, rough, np.zeros(len(P)))


def paint_skull(o, jaw=False):
    P = verts(o)
    Nn = normals(o)
    col, crack, pores = bone_colour(P, Nn, 5 if jaw else 1)
    # soot round the sockets (the eyes' fire) and inside the mouth and the holes
    rim = np.zeros(len(P))
    deep = np.zeros(len(P))
    for side in (1, -1):
        c = np.array(tuple(mir(EYE_C, side)))
        d = np.linalg.norm(P - c, axis=1)
        rim = np.maximum(rim, smooth(SOCKET_R * 1.9, SOCKET_R * 1.15, d))
        deep = np.maximum(deep, smooth(SOCKET_R * 1.2, SOCKET_R * 1.02, d))
    col = mix(col, mix(np.broadcast_to(SOOT_BLUE, (len(P), 3)), SOOT, 0.5), rim * 0.7)
    col = mix(col, INSIDE * 0.5, deep)
    if not jaw:
        mouth = (Nn[:, 2] < -0.5) & (np.abs(P[:, 0]) < 0.048) & (P[:, 1] < -0.6)
    else:
        loc = np.array([tuple(JAW_M.inverted() @ Vector(p)) for p in P])
        mouth = (Nn @ np.array(tuple(JAW_M.to_3x3() @ V(0, 0, 1))) > 0.5) & (np.abs(loc[:, 0]) < 0.042) & (loc[:, 1] < -0.6)
    col = mix(col, INSIDE, mouth.astype(float) * 0.85)
    relief = -0.0007 * crack - 0.0002 * pores
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, np.clip(0.6 + 0.12 * crack + 0.15 * rim + 0.4 * deep, 0, 0.97), np.zeros(len(P)))


def paint_horns(o, along):
    P = verts(o)
    ridge = np.maximum(0.0, np.sin(along * 80)) ** 3 * (1 - along * 0.7)
    col = mix(np.broadcast_to(HORN, (len(P), 3)), HORN_RIDGE, ridge * 0.9)
    col = mix(col, HORN_TIP, smooth(0.55, 1.0, along))
    streak = smooth(0.4, 0.7, fbm(P * np.array((4.0, 4.0, 1.0)), 18.0, 3, 23))
    col = col * (0.88 + 0.2 * streak)[:, None]
    paint(o, col, 0.48 - 0.12 * along, np.zeros(len(P)))


def paint_teeth(o, f):
    col = mix(np.broadcast_to(TOOTH_ROOT, (len(f), 3)), TOOTH, smooth(0.15, 0.55, f))
    paint(o, col, np.full(len(f), 0.36), np.zeros(len(f)))


def paint_talons(o, f):
    col = mix(np.broadcast_to(TALON, (len(f), 3)), TALON_TIP, smooth(0.45, 1.0, f))
    paint(o, col, np.full(len(f), 0.3), np.zeros(len(f)))


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


# ---------- the whole, high-detail ----------
GLOW_SOUL, GLOW_EYES = "3d7bff", "4aa6ff"


def build_hi(clay=False):
    pieces = {}
    pieces["Skin"] = build_skull()
    pieces["Jaw"] = build_jaw()
    pieces["Brows"] = build_brows(N + "BrowsHi", HI)
    pieces["Horns"] = build_horns(N + "HornsHi", HI)
    pieces["Teeth"], tooth_f, _ = build_teeth(N + "TeethHi", HI)
    pieces["Spine"] = build_vertebrae(N + "SpineHi", HI)
    pieces["Knot"] = build_knot(N + "KnotHi", HI)
    pieces["Ribs"] = build_ribs(N + "RibsHi", HI)
    pieces["Girdles"] = build_girdles(N + "GirdlesHi", HI)
    pieces["Legs"] = build_legs(N + "LegsHi", HI)
    pieces["Talons"] = build_talons(N + "TalonsHi", HI)
    pieces["Wings"] = build_wing_bones(N + "WingsHi", HI)
    glows = {"Soul": build_soul(N + "Soul_Glow_" + GLOW_SOUL, HI), "Eyes": build_eye_flames(N + "Eyes_Glow_" + GLOW_EYES, HI),
             "Maw": build_maw(N + "Maw_Glow_" + GLOW_SOUL, HI)}
    if not clay:
        paint_skull(pieces["Skin"])
        paint_skull(pieces["Jaw"], jaw=True)
        for key, seed in (("Brows", 2), ("Spine", 3), ("Knot", 4), ("Ribs", 6), ("Girdles", 7), ("Legs", 8), ("Wings", 9)):
            paint_bones(pieces[key], seed)
        paint_horns(pieces["Horns"], read_tag(pieces["Horns"], "along"))
        paint_teeth(pieces["Teeth"], tooth_f)
        paint_talons(pieces["Talons"], read_tag(pieces["Talons"], "along"))
    return pieces, glows


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.1, 0.7)
FACE_AT = (0, -0.68, 0.77)
EXTRA = [(0, -1, 0.05, 1.0, FACE_AT), (0.62, -0.75, 0.2, 1.0, FACE_AT), (1, -0.12, 0.08, 1.0, FACE_AT), (0.4, -0.85, 0.3, 0.5, tuple(EYE_C)),
         (0.8, -0.3, 0.2, 1.4, (0.0, -0.02, 0.56)), (0.8, -0.2, -0.4, 1.4, (0.13, 0.05, 0.38))]


def show_glows(glows, strength=3.0):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = strength
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def soul_light():
    """A blue light in its chest, as the game gives it (a PointLight): only for review renders."""
    lt = bpy.data.lights.new("SoulLight", "POINT")
    lt.energy = 18
    lt.color = (0.35, 0.6, 1.0)
    lt.shadow_soft_size = 0.05
    ob = bpy.data.objects.new("SoulLight", lt)
    scene.collection.objects.link(ob)
    ob.location = SOUL_C + V(0, 0, 0.02)
    return ob


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.36, 0.38, 0.44, 1))
    show_glows(glows)
    soul_light()
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.04, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=4.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKULL_QUADS, JAW_QUADS = 1350, 540
LOW_RES = {"Brows": 0.4, "Horns": 0.3, "Teeth": 0.4, "Spine": 0.34, "Knot": 0.36, "Ribs": 0.42, "Girdles": 0.32, "Legs": 0.3, "Talons": 0.4,
           "Wings": 0.36}
SCALES = {"Jaw": 1.3, "Brows": 1.4, "Horns": 1.0, "Teeth": 1.2, "Spine": 0.85, "Knot": 0.9, "Ribs": 0.85, "Girdles": 0.8, "Legs": 0.8, "Talons": 0.9,
          "Wings": 0.75}
BUILDERS = {"Brows": build_brows, "Horns": build_horns, "Spine": build_vertebrae, "Knot": build_knot, "Ribs": build_ribs, "Girdles": build_girdles,
            "Legs": build_legs, "Talons": build_talons, "Wings": build_wing_bones}


def build_low(pieces):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKULL_QUADS), "Jaw": retopo_skin(pieces["Jaw"], N + "JawLow", JAW_QUADS)}
    for key, fn in BUILDERS.items():
        lows[key] = fn(N + key + "Low", GAME, LOW_RES[key])
    lows["Teeth"], _, jaw_flags = build_teeth(N + "TeethLow", GAME, LOW_RES["Teeth"])
    triangulate(lows)
    return lows, jaw_flags


def horn_uv(o, density):
    """The horns' own UVs: each horn one strip, around it by its girth and along it by its length (a single projection of the coil folds over
    itself). Mesh.tube lays its rings down in order, so a vertex's ring and its place round the ring come from its index."""
    res = LOW_RES["Horns"]
    pts = horn_path(1, max(30, int(72 * res)))
    sides = 11
    per = len(pts) * sides
    me = o.data
    assert len(me.vertices) == 2 * per, ("horn vertices", len(me.vertices), 2 * per)
    seg = [0.0] + [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    along = np.cumsum(seg)
    girth = [TAU * horn_radius(a / along[-1]) * 1.1 for a in along]
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        rings = {divmod(vi % per, sides)[0] for vi in poly.vertices}
        if len(rings) == 1:
            # an end cap: its own little disc just past that end of the strip (laid along the strip, its faces would have no area)
            ring = rings.pop()
            h = poly.vertices[0] // per
            rad = girth[ring] / TAU
            centre_v = along[ring] - rad - 0.02 if ring == 0 else along[ring] + rad + 0.02
            for li, vi in zip(poly.loop_indices, poly.vertices):
                k = (vi % per) % sides
                a = TAU * k / sides
                uv[li].uv = (h * 0.35 + 0.2 + rad * math.cos(a), centre_v + rad * math.sin(a))
            continue
        ks = [(vi % per) % sides for vi in poly.vertices]
        wrap = (sides - 1) in ks and 0 in ks
        for li, vi in zip(poly.loop_indices, poly.vertices):
            h, local = divmod(vi, per)
            ring, k = divmod(local, sides)
            if wrap and k == 0:
                k = sides
            uv[li].uv = (h * 0.35 + girth[ring] * (k / sides - 0.5) + 0.2, along[ring])
    scale_uv_to(o, list(me.polygons), density)


def fit_uvs(lows, margin=0.006):
    """The packer can lay the atlas out over several tiles (here it spread over two by two): scale the whole layout, every piece alike, back into the
    one tile the bake and the game read. A uniform scale keeps every island apart."""
    arrays = []
    for o in lows.values():
        uv = o.data.uv_layers.active.data
        a = np.empty(len(uv) * 2)
        uv.foreach_get("uv", a)
        arrays.append(a.reshape(-1, 2))
    allp = np.concatenate(arrays)
    lo, hi_ = allp.min(0), allp.max(0)
    k = (1 - 2 * margin) / float((hi_ - lo).max())
    for o, a in zip(lows.values(), arrays):
        o.data.uv_layers.active.data.foreach_set("uv", ((a - lo) * k + margin).ravel())
    return lo, hi_, k


def build_glows(coll, res):
    return {"Soul": build_soul(N + "Soul_Glow_" + GLOW_SOUL, coll, res), "Eyes": build_eye_flames(N + "Eyes_Glow_" + GLOW_EYES, coll, res),
            "Maw": build_maw(N + "Maw_Glow_" + GLOW_SOUL, coll, res)}


# ---------- the skeleton ----------
# the hips are its base: the back, the neck and the head turn off them forward, the tail behind
HIPS_AT, BODY_AT, CHEST_AT = path_at(SPINE, 0.08), path_at(SPINE, 0.5), path_at(SPINE, 0.92)
NECK1_AT, NECK2_AT, HEAD_AT = NECK[0], path_at(NECK, 0.55), V(0, -0.505, 0.79)
TAIL_NAMES = ["Tail%d" % k for k in range(1, 7)]
TAIL_F = (0.02, 0.18, 0.34, 0.5, 0.66, 0.82)
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Leg%s3" % key, "Paw%s" % key] for key, *_ in LEG_SET}


def brow_centre(side):
    pts = brow_path(side, 12)
    return pts[6]


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Hips", HIPS_AT, "Root"), ("Body", BODY_AT, "Hips"), ("Chest", CHEST_AT, "Body"),
             ("Neck1", NECK1_AT, "Chest"), ("Neck2", NECK2_AT, "Neck1"), ("Head", HEAD_AT, "Neck2"), ("Jaw", JAW_HINGE.copy(), "Head"),
             ("Soul", SOUL_C.copy(), "Body")]
    for side, tag in ((1, "L"), (-1, "R")):
        bones += [("Eye" + tag, mir(EYE_C, side), "Head"), ("Brow" + tag, brow_centre(side), "Head")]
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for key, side, knots, radii, fore in LEG_SET:
        parent = "Chest" if fore else "Hips"
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, mir(knots[k], side), parent))
            parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        root, elbow, wrist, tips = wing_frame(side)
        bones += [("Wing%s1" % tag, root, "Chest"), ("Wing%s2" % tag, elbow, "Wing%s1" % tag), ("Wing%s3" % tag, wrist, "Wing%s2" % tag)]
        bones += [("Wing%sF%d" % (tag, j + 1), wrist.copy(), "Wing%s3" % tag) for j in range(len(FINGERS))]
    return armature(bones)


def trunk_bone(p):
    """The trunk bone a point of the back or neck rides on."""
    if p[1] < NECK2_AT.y + 0.02:
        return "Neck2"
    if p[1] < NECK1_AT.y - 0.005:
        return "Neck1"
    if p[1] < -0.06:
        return "Chest"
    if p[1] < 0.17:
        return "Body"
    return "Hips"


def tail_bone(f):
    k = max(i for i, tf in enumerate(TAIL_F) if f >= tf - 1e-6) if f >= TAIL_F[0] else 0
    return TAIL_NAMES[k]


def bind_all(lows, rig, glows, jaw_flags):
    """A skeleton's bones are rigid: every piece rides wholly on one bone (one influence everywhere, nothing stretches)."""
    rigid(lows["Skin"], "Head")
    rigid(lows["Jaw"], "Jaw")
    rigid(lows["Horns"], "Head")
    weigh(lows["Teeth"], [{"Jaw": 1.0} if j else {"Head": 1.0} for j in jaw_flags])
    weigh(lows["Brows"], [{"BrowL" if p[0] > 0 else "BrowR": 1.0} for p in verts(lows["Brows"])])
    units = vertebra_list()
    unit = read_tag(lows["Spine"], "unit")
    per_unit = []
    for c, tan, up, r, length, spine_h, region, f in units:
        per_unit.append(tail_bone(f * 0.96) if region == "tail" else trunk_bone(tuple(c)))
    weigh(lows["Spine"], [{per_unit[j]: 1.0} for j in unit])
    rigid(lows["Knot"], TAIL_NAMES[-1])
    rib = read_tag(lows["Ribs"], "rib")
    weigh(lows["Ribs"], [{"Chest" if (k < 0 or RIB_Y[k] < -0.06) else "Body": 1.0} for k in rib])
    weigh(lows["Girdles"], [{"Chest" if p[1] < 0 else "Hips": 1.0} for p in verts(lows["Girdles"])])
    leg, seg = read_tag(lows["Legs"], "leg"), read_tag(lows["Legs"], "seg")
    weigh(lows["Legs"], [{LEG_NAMES[LEG_SET[l][0]][g]: 1.0} for l, g in zip(leg, seg)])
    weigh(lows["Talons"], [{LEG_NAMES[LEG_SET[l][0]][3]: 1.0} for l in read_tag(lows["Talons"], "leg")])
    wb = lows["Wings"]
    kind, finger = read_tag(wb, "kind"), read_tag(wb, "finger")
    out = []
    for k, j, p in zip(kind, finger, verts(wb)):
        tag = "L" if p[0] > 0 else "R"
        out.append({("Wing%s1" % tag, "Wing%s2" % tag, "Wing%s3" % tag)[k] if k < 3 else "Wing%sF%d" % (tag, j + 1): 1.0})
    weigh(wb, out)
    rigid(glows["Soul"], "Soul")
    rigid(glows["Maw"], "Head")
    weigh(glows["Eyes"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Eyes"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateBonefireDragon uses. +X lifts what points forward (and closes the jaw); +Y turns to
# its left; +Z rolls it
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    """move: in the game's axes, metres."""
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def wings(lift=0.0, sweep=0.0, elbow=0.0, hand=0.0, fan=0.0):
    """Both wings: lift raises the whole wing (about the body's length), sweep swings it back, elbow and hand fold or open it, fan spreads the fingers."""
    out = {}
    for tag, sign in (("L", 1), ("R", -1)):
        out["Wing%s1" % tag] = (0, sweep * sign, lift * -sign)
        out["Wing%s2" % tag] = (0, elbow * sign, 0)
        out["Wing%s3" % tag] = (0, hand * sign, 0)
        for j in range(len(FINGERS)):
            out["Wing%sF%d" % (tag, j + 1)] = (0, fan * sign * (j / (len(FINGERS) - 1) - 0.5), 0)
    return out


# its moves, each checked here: the same numbers as PetRig's BF tables
BEAT_UP = wings(lift=0.5, sweep=-0.1, elbow=-0.25, hand=-0.2, fan=0.3)
BEAT_DOWN = wings(lift=-0.55, sweep=0.12, elbow=-0.35, hand=-0.3, fan=0.4)
ROAR = {"Jaw": (-0.42, 0, 0), "Head": (0.22, 0, 0), "Neck2": (0.1, 0, 0), "Neck1": (0.06, 0, 0)}
RISE = {"Body": (0.2, 0, 0), "Chest": (0.16, 0, 0), "Neck1": (-0.1, 0, 0), "Head": (-0.12, 0, 0), "LegFL1": (0.5, 0, 0), "LegFR1": (0.5, 0, 0),
        "LegFL2": (-0.6, 0, 0), "LegFR2": (-0.6, 0, 0), **wings(lift=0.35, sweep=-0.05, elbow=-0.45, hand=-0.4, fan=0.5)}
SWIPE = {"LegFL1": (-0.55, 0.1, 0), "LegFL2": (0.7, 0, 0), "LegFL3": (0.4, 0, 0), "PawFL": (0.3, 0, 0)}
LOOK = {"Neck1": (0.04, 0.22, 0), "Neck2": (0.04, 0.25, 0.08), "Head": (0.06, 0.3, 0.12), "EyeL": (0, 0.25, 0), "EyeR": (0, 0.25, 0)}
TAIL_SWAY = {n: (0.04, 0.18, 0) for n in TAIL_NAMES}


def brow_spec(deg):
    """Both brows turned about their own length: positive lowers their fronts (a glare)."""
    out = {}
    for side, tag in ((1, "L"), (-1, "R")):
        t, s, u = socket_frame()
        out["Brow" + tag] = (tuple(mir(t, side)), deg * side, (0, 0, 0))
    return out


def pose_library():
    return {"BeatUp": spec(BEAT_UP), "BeatDown": spec(BEAT_DOWN), "Roar": spec(ROAR), "Rise": spec(RISE), "Swipe": spec(SWIPE), "Look": spec(LOOK),
            "Tail": spec(TAIL_SWAY), "Glare": brow_spec(14), "Wonder": brow_spec(-14)}


if __name__ == "__main__" and STAGE == "all":
    pieces, glows = build_hi()
    mat = hi_material(ao_distance=0.04, ao_share=0.5)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows, jaw_flags = build_low(pieces)
    # true densities (each projection run is scaled apart otherwise: the skull came out hundreds of times denser than the bones) and a thin margin:
    # a skeleton is some two thousand islands, and a margin of a hundredth per island shrank every one of them to nothing. The horns lay out their
    # own strips (projected, their coils folded over themselves)
    unwrap(lows, [(lambda p: True, 1.6), (None, 1.0)], SCALES, margin=0.0028, angle=45, shape="CONVEX", texels=SCALES,
           own_uv={"Horns": horn_uv})
    print("UV FIT", fit_uvs(lows), flush=True)
    for key, o in lows.items():
        print("UV DENSITY", key, round(uv_density([o]), 3), flush=True)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.62, 0.56, 0.45, 1), far=("Skin", "Jaw"), reach=(0.008, 0.02),
             far_reach=(0.01, 0.025))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    glows = build_glows(GAME, 0.45)
    triangulate(glows)
    show_glows(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows, jaw_flags)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), "UNWEIGHTED", sum(1 for v in body.data.vertices if not v.groups), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "box middle", round((hi + lo) / 2, 4), flush=True)
    for name in ("Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "Jaw", "Soul", "EyeL", "BrowL", "WingL1", "WingL3", "Tail1", "Tail6", "LegFL1", "LegBL1"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    t_, s_, u_ = socket_frame()
    print("BROW AXIS L game axes", (round(-t_.x, 4), round(t_.z, 4), round(t_.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=4.4, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    side = (1, -0.05, 0.08, 4.4, VIEW_AT)
    wide = (0.62, -0.72, 0.25, 4.4, VIEW_AT)
    face = (0.45, -0.85, 0.15, 1.0, FACE_AT)
    for name, view in (("BeatUp", wide), ("BeatDown", wide), ("Roar", face), ("Rise", side), ("Swipe", side), ("Look", face), ("Tail", wide),
                       ("Glare", face), ("Wonder", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 4.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

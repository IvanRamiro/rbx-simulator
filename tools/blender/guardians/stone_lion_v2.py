"""The Awakened Stone Lion, rebuilt from nothing (the owner, 2026-11-05: "like a total change", "Make a more realistic animation").

A real lion in carved granite, not a temple dog: a deep chest, a tucked waist, heavy haunches, a level back and a low head, under
a heavy mane of chiselled locks. It sits as a temple statue until it wakes. It holds no egg: no guardian does, the three stands are
behind it. What it keeps from the game: its name, a gold collar with a jade orb that tells its state, Qi-blue eyes, the Slam, the
Roar, the Pounce and their ranges.

The realism starts in the skeleton. A lion's legs have one more joint than a two-piece limb can show, so each foreleg is a shoulder
blade that rolls over the ribs, an upper arm, a forearm, a pastern and toes, and each hind leg a thigh, a shin, a hock and toes.

Authored in Roblox studs: standing, facing -Z, its paws on the ground at y = 0, its origin under the chest, its left toward -X.

    import stone_lion_v2 as L
    L.build_form(); L.bind()        # the clay
    L.build_final() ...             # see build_all
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import egg_hi as Hm
import egg_kit as K
import guardian_kit as G
import pangu_v2 as P
import tiangou_v2 as T

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "StoneLion"
RIG = "StoneLionRig"
COLLECTION = "StoneLionV2"
OUT = G.OUT_DIR
EYE_HEX, PUPIL_HEX, ORB_HEX = "006eff", "06101c", "00a05f"


# ---------- the skeleton: (parent, head, tail) ----------
_B = {
    "Root": (None, (0, 0, 0), (0, 2, 0)),
    "Hips": ("Root", (0, 16.9, 14.5), (0, 18.0, 8.0)),
    "Spine": ("Hips", (0, 18.0, 8.0), (0, 18.2, 1.0)),
    "Chest": ("Spine", (0, 18.2, 1.0), (0, 19.2, -7.5)),
    "Neck1": ("Chest", (0, 19.2, -7.5), (0, 21.2, -11.6)),
    "Neck2": ("Neck1", (0, 21.2, -11.6), (0, 22.4, -14.0)),
    "Head": ("Neck2", (0, 22.4, -14.0), (0, 21.2, -22.5)),
    "Jaw": ("Head", (0, 20.2, -15.8), (0, 18.6, -22.4)),
    "Eyes": ("Head", (0, 23.0, -19.3), (0, 23.0, -20.3)),
    "ManeTop": ("Neck2", (0, 25.0, -12.5), (0, 24.6, -3.8)),
    "ManeChest": ("Neck1", (0, 16.2, -11.0), (0, 8.8, -9.8)),
    "Tail1": ("Hips", (0, 17.2, 18.0), (0, 14.8, 21.2)),
    "Tail2": ("Tail1", (0, 14.8, 21.2), (0, 11.4, 23.2)),
    "Tail3": ("Tail2", (0, 11.4, 23.2), (0, 8.0, 24.2)),
    "Tail4": ("Tail3", (0, 8.0, 24.2), (0, 5.2, 25.0)),
    "Tail5": ("Tail4", (0, 5.2, 25.0), (0, 3.4, 26.4)),
    "Tail6": ("Tail5", (0, 3.4, 26.4), (0, 2.9, 28.6)),
}


def _side(sign, tag):
    x = lambda v: v * sign
    b = {
        "Ear": ("Head", (x(3.1), 24.6, -15.0), (x(3.55), 26.2, -14.7)),
        "Mane": ("Neck2", (x(4.6), 22.0, -12.6), (x(7.2), 14.6, -6.0)),
    }
    out = {tag + "Ear": b["Ear"], tag + "Mane": b["Mane"]}
    front = {
        "Scapula": ("Chest", (x(3.0), 19.6, -2.2), (x(5.2), 13.4, -8.2)),
        "Upper": ("Scapula", (x(5.2), 13.4, -8.2), (x(5.2), 8.2, -4.0)),
        "Lower": ("Upper", (x(5.2), 8.2, -4.0), (x(5.2), 2.9, -5.2)),
        "Paw": ("Lower", (x(5.2), 2.9, -5.2), (x(5.2), 1.0, -7.0)),
        "Toes": ("Paw", (x(5.2), 1.0, -7.0), (x(5.2), 0.8, -9.6)),
    }
    back = {
        "Thigh": ("Hips", (x(4.6), 15.4, 13.2), (x(5.4), 9.2, 8.0)),
        "Shin": ("Thigh", (x(5.4), 9.2, 8.0), (x(5.4), 6.0, 15.6)),
        "Meta": ("Shin", (x(5.4), 6.0, 15.6), (x(5.4), 1.0, 13.3)),
        "Toes": ("Meta", (x(5.4), 1.0, 13.3), (x(5.4), 0.8, 10.6)),
    }
    for n, (parent, head, tail) in front.items():
        full = "Front" + tag + n
        out[full] = ("Front" + tag + parent if parent in front else parent, head, tail)
    for n, (parent, head, tail) in back.items():
        full = "Back" + tag + n
        out[full] = ("Back" + tag + parent if parent in back else parent, head, tail)
    return out


_B.update(_side(-1, "Left"))
_B.update(_side(1, "Right"))
BONES = _B


# ---------- the forms ----------
limb = T._limb


def _paw(x, z, sign, wide=1.0):
    """A lion's great paw: a broad pad and four thick separate toes, the middle two longest, the knuckles standing proud."""
    lobes = [((x, 1.2, z + 0.5), (2.05 * wide, 1.2, 1.9), None)]
    for dx, length in ((-1.72, 1.85), (-0.6, 2.5), (0.6, 2.5), (1.72, 1.85)):
        tx = x + dx * sign * wide
        lobes += limb([(tx, 1.55, z - 0.2), (tx, 1.25, z - length * 0.55), (tx, 0.78, z - length)], [(0.74, 0.68, 0.8), (0.72, 0.82, 0.85), (0.62, 0.72, 0.62)])
    return lobes


def _groups():
    """The body as groups of soft forms: (how softly the group's forms melt together, its forms)."""
    groups = []
    # the torso: a deep keeled ribcage, a tucked waist, heavy hindquarters falling to the tail. A level back, no sway
    groups.append((1.7, [
        ((0, 13.9, -2.8), (6.4, 6.1, 8.4), (-5, 0, 0)),            # the ribcage, reaching down to the elbows
        ((0, 11.9, -8.6), (4.5, 3.8, 3.7), None),                  # the breast
        ((0, 18.0, -4.4), (4.8, 2.2, 4.8), None),                  # the withers
    ] + limb([(0, 15.1, 3.2), (0, 15.1, 8.0), (0, 15.2, 12.0)], [(5.6, 4.5, 3.6), (4.9, 3.8, 3.4), (5.6, 4.3, 3.6)]) + [
        ((0, 15.2, 14.1), (5.9, 4.5, 4.9), None),                  # the rump
        ((0, 16.8, 15.4), (4.2, 2.2, 3.4), (10, 0, 0)),            # the croup
    ]))
    # the neck, thick into the shoulders (the mane lies over it)
    groups.append((2.0, limb([(0, 17.2, -6.2), (0, 20.1, -10.2), (0, 22.3, -13.6)], [(4.7, 5.2, 4.6), (4.1, 4.0, 3.8), (3.6, 3.2, 3.2)])))
    # the head: a broad skull, a slanted brow over deep eyes, a long flat nose, cheek planes, whisker pads parted down the middle, a strong chin
    groups.append((0.6, [
        ((0, 22.75, -15.7), (3.55, 2.6, 3.4), None),               # the skull
        ((-1.85, 24.05, -18.2), (1.6, 0.6, 1.25), (0, 0, 18)), ((1.85, 24.05, -18.2), (1.6, 0.6, 1.25), (0, 0, -18)),         # the brow, in a frown
        ((-2.75, 21.75, -17.2), (0.95, 1.45, 2.1), None), ((2.75, 21.75, -17.2), (0.95, 1.45, 2.1), None),                     # the cheekbones
        ((-2.3, 21.75, -19.3), (0.8, 0.95, 1.5), (12, 0, 0)), ((2.3, 21.75, -19.3), (0.8, 0.95, 1.5), (12, 0, 0)),             # the planes under the eyes
    ] + limb([(0, 22.0, -18.0), (0, 21.5, -20.2), (0, 21.2, -22.0)], [(1.95, 1.75, 2.0), (1.7, 1.45, 1.5), (1.55, 1.15, 0.75)])
      + limb([(0, 23.75, -18.0), (0, 23.05, -20.6), (0, 22.4, -22.9)], [(1.3, 0.55, 1.0), (1.2, 0.56, 0.9), (1.1, 0.46, 0.42)])
      + [((-1.2, 20.9, -22.0), (1.22, 1.08, 1.05), None), ((1.2, 20.9, -22.0), (1.22, 1.08, 1.05), None)]                     # the whisker pads
      + [((-2.6, 20.0, -16.8), (1.25, 1.8, 2.4), None), ((2.6, 20.0, -16.8), (1.25, 1.8, 2.4), None),                          # the jowls, wrapped over the jaw's hinge
         ((0, 18.9, -15.4), (2.7, 1.8, 2.5), None)]))                                                                          # the throat under them
    for sign in (-1, 1):
        x = lambda v: v * sign
        # a small round ear, set wide, half lost in the mane
        groups.append((0.25, limb([(x(3.2), 24.6, -15.0), (x(3.5), 25.5, -14.85), (x(3.65), 26.0, -14.75)], [(0.92, 0.8, 0.42), (0.86, 0.72, 0.38), (0.6, 0.46, 0.28)])))
        # the foreleg: a shoulder lying on the ribs, a massive upper arm back to the elbow, a thick straight forearm
        groups.append((1.05, [((x(4.95), 15.8, -5.6), (1.7, 3.9, 3.4), (24, 0, x(-6)))]
                       + limb([(x(5.3), 13.2, -8.0), (x(5.35), 8.4, -4.2)], [(2.25, 3.0, 2.85), (1.95, 2.1, 2.25)])
                       + [((x(5.35), 8.5, -3.2), (1.25, 1.3, 1.1), None)]                                        # the point of the elbow
                       + limb([(x(5.35), 8.0, -4.3), (x(5.3), 5.2, -4.8), (x(5.25), 2.9, -5.2)], [(2.1, 2.1, 2.35), (1.85, 1.9, 1.95), (1.7, 1.2, 1.7)])))
        # the pastern and the paw, each toe its own form
        groups.append((0.42, limb([(x(5.25), 3.2, -5.2), (x(5.25), 1.7, -6.1)], [(1.72, 1.1, 1.7), (1.95, 1.05, 1.75)]) + _paw(x(5.25), -7.0, sign)))
        # the hind leg: a great flat thigh, a calf high behind, the hock's sharp point
        groups.append((1.15, [((x(4.65), 13.0, 12.2), (2.3, 4.8, 4.7), (-14, 0, 0))]
                       + limb([(x(4.95), 11.8, 10.0), (x(5.4), 9.2, 8.2)], [(2.3, 3.3, 3.1), (1.9, 2.0, 1.95)])
                       + limb([(x(5.4), 9.2, 8.2), (x(5.4), 7.6, 11.8), (x(5.4), 6.25, 15.3)], [(1.9, 2.3, 2.1), (1.5, 1.7, 1.75), (1.15, 1.0, 0.9)])
                       + [((x(5.38), 8.9, 11.2), (1.35, 1.75, 2.3), (-22, 0, 0))]))                              # the calf
        # the hock's point, the long straight metatarsus and the paw
        groups.append((0.42, [((x(5.4), 6.2, 15.9), (0.92, 0.95, 0.78), None)]
                       + limb([(x(5.4), 6.1, 15.4), (x(5.4), 3.3, 14.35), (x(5.4), 1.6, 13.6)], [(1.15, 1.05, 1.0), (1.15, 1.1, 1.05), (1.45, 0.95, 1.3)])
                       + _paw(x(5.4), 13.3, sign, wide=0.95)))
    # the tail: thick at its root, tapering, carried low in a long curve, a heavy tuft drawn to a point
    names = ["Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6"]
    pts = [BONES[n][1] for n in names] + [BONES["Tail6"][2]]
    rad = [(1.55, 1.6, 1.6), (1.18, 1.2, 1.2), (0.98, 1.0, 1.0), (0.84, 0.86, 0.86), (0.76, 0.78, 0.78), (0.74, 0.76, 0.76), (0.72, 0.72, 0.72)]
    groups.append((0.4, limb(pts, rad) + limb([(0, 3.05, 27.0), (0, 2.75, 28.8), (0, 2.65, 31.0)], [(1.0, 0.95, 1.0), (1.5, 1.4, 1.6), (0.14, 0.14, 0.14)])))
    return groups


def _mouth_line(z):
    """The height of the line between the upper and lower jaw, along the muzzle."""
    return 20.3 - 0.42 * ((z + 17.4) / -5.0)


def _mouth_cut(points, d):
    """The skin stops at the mouth: everything below the line, ahead of its corner, belongs to the jaw."""
    import numpy as np
    w = np.maximum(points[:, 1] - _mouth_line(points[:, 2]), points[:, 2] + 18.6)   # negative inside the wedge: the cheek hides the jaw's back, the corner of the mouth is here
    d = np.maximum(d, -w)
    # deep-set eye sockets under the heavy brow
    for side in (-1, 1):
        q = (points - np.array((side * 1.82, 22.92, -19.5))) / np.array((1.0, 0.62, 1.05))
        sock = (np.linalg.norm(q, axis=1) - 1.0) * 0.62
        h = np.maximum(0.3 - np.abs(d + sock), 0.0) / 0.3
        d = np.maximum(d, -sock) + h * h * 0.3 * 0.25
    return d


def _jaw_cut(points, d):
    import numpy as np
    return np.maximum(d, points[:, 1] - (_mouth_line(points[:, 2]) + 0.42))     # tucked up behind the upper lip, so no gap shows when it's shut


JAW_GROUPS = [(0.42, limb([(0, 20.15, -16.4), (0, 19.9, -19.4), (0, 19.7, -21.3)], [(2.35, 1.1, 1.9), (2.3, 0.95, 1.7), (2.05, 0.82, 0.75)])
               + [((-1.05, 19.42, -21.65), (1.05, 0.72, 0.72), None), ((1.05, 19.42, -21.65), (1.05, 0.72, 0.72), None), ((0, 19.1, -21.0), (1.65, 0.62, 1.2), None)])]


def _lock(hi, root, direction, up, length, radius, rnd, sides=8, mat=0):
    """A lock of the mane: a thick carved strand lying along `direction`, close to the mass, its tip lifting a little toward `up`."""
    d = V(direction).normalized()
    u = V(up) - d * V(up).dot(d)
    u = u.normalized() if u.length > 1e-4 else V((0, 1, 0))
    s = d.cross(u)
    sway = rnd.uniform(-1, 1)
    pts = [V(root), V(root) + d * length * 0.3 + s * length * 0.1 * sway + u * radius * 0.3, V(root) + d * length * 0.66 - s * length * 0.08 * sway + u * radius * 0.2,
           V(root) + d * length + u * length * 0.06 + s * length * 0.08 * sway]
    Hm.htube(hi, pts, lambda q: radius * (0.82 + 0.38 * math.sin(math.pi * min(1.0, q * 1.7))) * (1 - q ** 2.2) ** 0.7, sides=sides, per=4, mat=mat, uv_scale=1.0 / length, tip=True, wobble=0.0)


def _mane_mass():
    """The mass under the locks: over the crown, round the cheeks, down the neck and melting into the shoulders, full at the chest."""
    return [(2.0, limb([(0, 23.6, -14.0), (0, 24.0, -10.8), (0, 22.3, -6.8), (0, 19.8, -2.6)], [(4.2, 2.1, 2.4), (5.2, 2.9, 3.6), (5.5, 2.9, 3.8), (3.8, 1.5, 3.2)])
             + limb([(-4.2, 21.0, -14.2), (-5.7, 18.4, -11.0), (-6.5, 15.0, -6.8)], [(1.6, 3.2, 2.2), (2.5, 4.4, 3.6), (1.3, 3.2, 3.2)])
             + limb([(4.2, 21.0, -14.2), (5.7, 18.4, -11.0), (6.5, 15.0, -6.8)], [(1.6, 3.2, 2.2), (2.5, 4.4, 3.6), (1.3, 3.2, 3.2)])
             + limb([(0, 17.6, -13.4), (0, 14.4, -12.9), (0, 11.2, -11.4)], [(3.9, 3.8, 2.3), (4.0, 3.6, 2.5), (2.4, 2.2, 1.6)]))]


def _mane_locks(hi, mass, rnd, count=1.0):
    """Heavy overlapping locks over the mass, each laid as a real mane falls: back from the face, down the sides, down the chest."""
    def lay(centre, spread_x, spread_y, spread_z, number, flow, length, radius, normal):
        for _ in range(int(number * count)):
            c = V(centre) + V((rnd.uniform(-spread_x, spread_x), rnd.uniform(-spread_y, spread_y), rnd.uniform(-spread_z, spread_z)))
            out = (c - V((0, 18.0, -9.0))) if normal is None else V(normal)
            out = V((out.x, out.y * 0.9, out.z * 0.3)).normalized() if abs(out.y) > 0.1 or abs(out.x) > 0.1 else out.normalized()
            cast = V((0, 1, 0)) if out.y < -0.1 else out
            try:
                root = G.surface_along(mass, c, cast, reach=10.0) - cast * 0.25
            except AssertionError:
                continue
            d = (V(flow) + cast * 0.1 + V((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08)))).normalized()
            _lock(hi, root, d, cast if out.y >= -0.1 else out, length * rnd.uniform(0.85, 1.2), radius * rnd.uniform(0.9, 1.12), rnd)

    # short round the face, then long down the neck and sides; every lock overlaps the ones below, like thatch
    lay((0, 25.6, -14.2), 3.4, 0.4, 0.5, 22, (0, -0.1, 1), 5.0, 0.62, (0, 1, 0))
    for s in (-1, 1):
        lay((s * 4.6, 21.0, -14.4), 0.5, 2.6, 0.9, 20, (s * 0.15, -0.4, 1), 5.4, 0.64, (s, 0, 0))
        lay((s * 6.0, 18.6, -11.8), 0.9, 3.8, 2.0, 30, (s * 0.06, -0.78, 0.72), 7.4, 0.72, (s, 0, 0))
        lay((s * 6.6, 14.6, -7.6), 0.8, 2.8, 2.0, 18, (s * 0.04, -0.96, 0.34), 6.6, 0.66, (s, 0, 0))
    lay((0, 27.0, -11.0), 4.8, 0.5, 3.0, 32, (0, -0.48, 1), 6.4, 0.72, (0, -0.6, 1))
    lay((0, 24.6, -6.2), 4.6, 0.5, 2.4, 24, (0, -0.95, 1), 5.2, 0.68, (0, -1, 0.5))
    # the chest: heavy, hanging between the forelegs, ending above the knees
    lay((0, 17.4, -15.6), 3.6, 2.2, 0.4, 24, (0, -1, 0.14), 6.4, 0.72, (0, 0, -1))
    lay((0, 13.8, -15.0), 3.2, 2.0, 0.5, 16, (0, -1, 0.12), 5.4, 0.62, (0, 0, -1))


def _fuse(name, coll, mat, objects, voxel):
    """Locks and mass become one solid carving: only one surface to reduce and to bake, so a lock can't tear away from what it grows from."""
    import bmesh
    bm = bmesh.new()
    for o in objects:
        bm.from_mesh(o.data)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    fused = bpy.data.objects.new(name, me)
    coll.objects.link(fused)
    Hm.apply_modifiers(fused, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel}), ("SMOOTH", {"factor": 0.6, "iterations": 2})])
    # a lock's tip the remesh cut loose would float: only the one carving stays
    bm = bmesh.new()
    bm.from_mesh(fused.data)
    seen, islands = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        seen.add(v)
        stack, island = [v], []
        while stack:
            q = stack.pop()
            island.append(q)
            for e in q.link_edges:
                w = e.other_vert(q)
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        islands.append(island)
    biggest = max(islands, key=len)
    bmesh.ops.delete(bm, geom=[q for island in islands if island is not biggest for q in island], context="VERTS")
    bm.to_mesh(fused.data)
    bm.free()
    for p in fused.data.polygons:
        p.use_smooth = True
    for o in objects:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(data)
    return fused


# ---------- the clay ----------
def _clay(name="LionClay", rgb=(0.42, 0.41, 0.4)):
    return P._clay(name, rgb)


def build_skeleton(coll):
    data = bpy.data.armatures.new(RIG)
    arm = bpy.data.objects.new(RIG, data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for name, (parent, head, tail) in BONES.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = W.rb(*head), W.rb(*tail)
        made[name] = b
    for name, (parent, head, tail) in BONES.items():
        if parent:
            made[name].parent = made[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in data.bones:
        b.use_deform = b.name != "Root"
    return arm


def _blob(name, coll, mat, groups, voxel, cut=None, soften=6, chisel="LionV2Chisel"):
    o = G.blob(name, coll, mat, P._rough_lobes(groups), voxel=voxel, smooth=0.75, rough=0.0, chisel=chisel)
    T._settle(o, groups, cut=cut)
    G.soften(o, soften)
    T._settle(o, groups, passes=2, cut=cut)
    return o


def build_form(voxel=0.17, tris=18500):
    T.clear()
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    skin = _blob("LN2_Skin", coll, _clay(), _groups(), voxel, cut=_mouth_cut)
    jaw = _blob("LN2_Jaw", coll, _clay(), JAW_GROUPS, 0.1, cut=_jaw_cut, soften=4)
    mass = _blob("LN2_ManeMass", coll, _clay("LionClayMane", (0.36, 0.34, 0.33)), _mane_mass(), 0.2, soften=4)
    hi = Hm.Hi()
    _mane_locks(hi, mass, random.Random(7))
    locks = hi.object("LN2_Locks", coll, [_clay("LionClayMane", (0.36, 0.34, 0.33))])
    mane = _fuse("LN2_Mane", coll, _clay("LionClayMane", (0.36, 0.34, 0.33)), [mass, locks], 0.11)
    counts = {"skin": P._reduce(skin, tris), "jaw": P._reduce(jaw, 2000), "mane": P._reduce(mane, 12000)}
    P._clean(skin)
    P._clean(jaw)
    P._clean(mane)
    build_skeleton(coll)
    return {**counts, "bones": len(BONES)}


# ---------- the weights ----------
def _points(obj):
    return P._points(obj)


def _distances(pts, names):
    import numpy as np
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    return np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)


def _attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


def _write_weights(obj, names, d, falloff, influences=4):
    import numpy as np
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[d >= 1e5] = 0
    order = np.argsort(-w, axis=1)[:, :influences]
    keep = np.zeros_like(w)
    rows = np.arange(len(w))[:, None]
    keep[rows, order] = w[rows, order]
    keep[keep < 0.02] = 0
    keep /= np.maximum(keep.sum(axis=1, keepdims=True), 1e-9)
    obj.vertex_groups.clear()
    for j, nm in enumerate(names):
        idx = np.nonzero(keep[:, j])[0]
        if len(idx):
            vg = obj.vertex_groups.new(name=nm)
            for i in idx.tolist():
                vg.add([i], float(keep[i, j]), "REPLACE")
    _attach(obj)
    return {"verts": len(w), "max influences": int((keep > 0).sum(axis=1).max()), "unweighted": int((keep.sum(axis=1) < 0.99).sum())}


def bind_rigid(obj, bone):
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    _attach(obj)


def bind_skin(skin, falloff=2.7):
    """Each bone gives way gradually outside its region, never at a hard edge (a hard edge creases the flank as a leg swings): the back and
    belly stay with the spine, the top of the rump never rises with a thigh, and the shoulder blade owns the hump over the withers, so it
    rolls under the skin."""
    import numpy as np
    pts = _points(skin)
    names = [n for n in BONES if n not in ("Root", "Eyes", "Jaw", "ManeTop", "ManeChest", "LeftMane", "RightMane")]
    d = _distances(pts, names)
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    ax = np.abs(x)
    over = lambda v, a, width: np.clip((v - a) / width, 0.0, 1.0) ** 2        # 0 up to a, then rising to 1 over width
    far = 9.0
    regions = {
        "Hips": over(5.0 - z, 0, 7.0) * far,
        "Spine": (over(z, 12.0, 5.0) + over(-z, 1.0, 5.0)) * far,
        "Chest": over(z, 3.5, 6.0) * far,
        "Neck1": over(z, -6.0, 3.5) * far,
        "Neck2": (over(z, -10.5, 2.5) + over(15.5 - y, 0, 2.5)) * far,
        "Head": (over(z, -13.2, 1.6) + over(17.5 - y, 0, 1.5)) * far,
        "Scapula": (over(1.8 - ax, 0, 1.2) + over(9.5 - y, 0, 2.5) + over(z, 2.0, 3.0) + over(-z, 12.5, 2.0)) * far,
        "Upper": (over(3.6 - ax, 0, 1.6) + over(y, 15.0, 3.0) + over(z, 0.0, 3.0)) * far,
        "Lower": (over(3.3 - ax, 0, 1.0) + over(y, 8.8, 2.0) + over(z, 0.5, 2.0)) * far,
        "Paw": over(y, 3.2, 1.2) * far,
        "Thigh": over(4.2 - ax, 0, 1.6) * far + np.maximum(0.0, 11.5 + (y - 8.0) * 0.2 - z) * 0.9 + np.maximum(0.0, y - 9.0) * 0.95,
        "Shin": (over(3.6 - ax, 0, 1.2) + over(y, 10.6, 1.6) + over(6.0 - z, 0, 1.5)) * far,
        "Meta": (over(y, 6.4, 1.2) + over(10.5 - z, 0, 1.5)) * far,
    }
    for j, nm in enumerate(names):
        if nm.startswith(("FrontLeft", "BackLeft", "LeftEar")):
            d[x > 0.1, j] = 1e6
        elif nm.startswith(("FrontRight", "BackRight", "RightEar")):
            d[x < -0.1, j] = 1e6
        base = nm.replace("FrontLeft", "").replace("FrontRight", "").replace("BackLeft", "").replace("BackRight", "")
        if nm in regions:
            d[:, j] += regions[nm]
        elif base in regions:
            d[:, j] += regions[base]
        elif base == "Toes":
            front = nm.startswith("Front")
            d[:, j] += (over(y, 2.0, 0.8) + over(z, -6.8 if front else 13.6, 0.8)) * far
        elif nm.endswith("Ear"):
            d[:, j] += over(24.8 - y, 0, 0.6) * far
        elif nm.startswith("Tail"):
            k = int(nm[4:])
            d[:, j] += (over(ax, 3.0, 1.0) + over(16.5 + (k - 1) * 1.2 - z, 0, 1.5)) * far
    result = _write_weights(skin, names, d, falloff)
    T.smooth_weights(skin, factor=0.5, repeat=12)
    # the flank is a wide sheet of skin: the thigh hands over to the body across a broad band, so a leg swinging forward stretches all of it
    # gently instead of tearing one strip
    _blur_weights(skin, ("Hips", "Spine", "BackLeftThigh", "BackRightThigh"), (y > 7.6) & (z > 0.0) & (z < 16.5), 12)
    return result


def _blur_weights(obj, names, region, repeat):
    """Spreads the named bones' weights among themselves inside a region, keeping each vertex's total and at most four bones."""
    import numpy as np
    me = obj.data
    n = len(me.vertices)
    groups = {g.name: g.index for g in obj.vertex_groups}
    everything = list(groups)
    w = np.zeros((n, len(everything)))
    at = {g: i for i, g in enumerate(everything)}
    for v in me.vertices:
        for g in v.groups:
            w[v.index, at[obj.vertex_groups[g.group].name]] = g.weight
    edges = np.zeros(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", edges)
    a, b = edges[0::2], edges[1::2]
    cols = [at[k] for k in names if k in at]
    part = w[:, cols]
    share = part.sum(axis=1, keepdims=True)
    # the rim of the region holds still, so what's outside it isn't disturbed
    for _ in range(repeat):
        total = np.zeros_like(part)
        count = np.zeros((n, 1))
        np.add.at(total, a, part[b])
        np.add.at(total, b, part[a])
        np.add.at(count, a, 1)
        np.add.at(count, b, 1)
        mean = total / np.maximum(count, 1)
        part[region] = part[region] * 0.4 + mean[region] * 0.6
    part *= share / np.maximum(part.sum(axis=1, keepdims=True), 1e-9)
    w[:, cols] = part
    order = np.argsort(-w, axis=1)[:, :4]
    keep = np.zeros_like(w)
    rows = np.arange(n)[:, None]
    keep[rows, order] = w[rows, order]
    keep[keep < 0.015] = 0
    keep /= np.maximum(keep.sum(axis=1, keepdims=True), 1e-9)
    for name, j in at.items():
        vg = obj.vertex_groups[name]
        vg.remove(list(range(n)))
        idx = np.nonzero(keep[:, j])[0]
        for i in idx.tolist():
            vg.add([i], float(keep[i, j]), "REPLACE")


def _bind_mane(obj):
    """The mane rides the neck and head, and its heavy sides and chest hang from their own bones, so they lag and swing."""
    import numpy as np
    pts = _points(obj)
    names = ["Head", "Neck1", "Neck2", "Chest", "ManeTop", "ManeChest", "LeftMane", "RightMane"]
    d = _distances(pts, names)
    z = pts[:, 2]
    d[:, 0] += np.clip((z + 14.5) / 1.5, 0, 1) * 6
    return _write_weights(obj, names, d, 2.6)


def bind():
    O = bpy.data.objects
    out = {"skin": bind_skin(O["LN2_Skin"])}
    bind_rigid(O["LN2_Jaw"], "Jaw")
    out["mane"] = _bind_mane(O["LN2_Mane"])
    return out


# ---------- posing: rotations in Roblox axes, each on top of its parent, as the game's joints work ----------
_euler, _mat, _frame = P._euler, P._mat, P._frame


def _children():
    kids = {}
    for name, (parent, _, _) in BONES.items():
        kids.setdefault(parent, []).append(name)
    return kids


_KIDS = _children()


def fk(pose, shift=(0, 0, 0)):
    """Where each bone is under a pose: {bone: (world rotation, world head)}, Roblox axes."""
    out = {}

    def walk(name, parent):
        pa, head, tail = BONES[name]
        r = _mat(pose.get(name, (0, 0, 0)))
        if parent is None:
            world, at = r, V(head)
        else:
            pr, pp = out[parent]
            world = pr @ r
            at = pp + pr @ (V(head) - V(BONES[parent][1]))
            if name == "Hips":
                at = at + V(shift)
        out[name] = (world, at)
        for child in _KIDS.get(name, ()):
            walk(child, name)

    walk("Root", None)
    return out


def tail_of(state, name):
    r, at = state[name]
    return at + r @ (V(BONES[name][2]) - V(BONES[name][1]))


def set_pose(pose, shift=(0, 0, 0)):
    arm = bpy.data.objects[RIG]
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        rest = pb.bone.matrix_local.to_3x3()
        t = T.rb_rot(*pose.get(pb.name, (0, 0, 0)))
        pb.rotation_quaternion = (rest.inverted() @ t @ rest).to_quaternion()
        pb.location = (0, 0, 0)
    hips = arm.pose.bones["Hips"]
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips.location = hips.bone.matrix_local.to_3x3().inverted() @ (C @ V(shift))
    bpy.context.view_layer.update()


def _hide_rig():
    bpy.data.objects[RIG].hide_render = True


VIEWS = {"front": (0, 6), "three": (-38, 10), "left": (-90, 4), "back": (180, 8), "right": (90, 4), "top": (-90, 70)}


def review_form(path, pose=None, shift=(0, 0, 0), views=("front", "three", "left", "back", "right", "top"), size=560, columns=3, distance=112, centre=(0, 14, 2)):
    scene, cam = T._review_scene(size)
    _hide_rig()
    set_pose(pose or {}, shift)
    tmp = path + ".tile.png"
    tiles = []
    for v in views:
        yaw, pitch = VIEWS[v]
        tiles.append(T._shot(scene, cam, yaw, pitch, distance, W.rb(*centre), size, tmp))
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


# ---------- the legs, solved: the paws go where they're told and the limbs reach for them ----------
FRONT, BACK = ("FrontLeft", "FrontRight"), ("BackLeft", "BackRight")
LEGS = FRONT + BACK
_REST = {n: V(BONES[n][2]) - V(BONES[n][1]) for n in BONES}
_X = V((1, 0, 0))
_rx = lambda deg: Matrix.Rotation(math.radians(deg), 3, "X")


def _hinged(rest, want):
    """The turn taking a rest direction to a wanted one with no twist about the limb: a leg swings on its hinge."""
    return _frame(want, _X) @ _frame(rest, _X).inverted()


def _set_world(pose, state, bone, world):
    pose[bone] = _euler(state[BONES[bone][0]][0].inverted() @ world)


def _two_bone(root, target, l1, l2, pole):
    to = target - root
    dist = max(min(to.length, (l1 + l2) * 0.995), abs(l1 - l2) + 0.05)
    d = to.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    side = (pole - d * pole.dot(d)).normalized()
    return root + d * a + side * h, root + d * dist, to.length / (l1 + l2)


REACH = {}


def solve_leg(pose, shift, leg, foot=(0, 0, 0, 0, 0), scapula=0.0):
    """foot = (dx, dy, dz, ankle, toe): where the toes' knuckle goes from where it stands, the turn of the pastern or hock (negative: the
    heel lifts over the knuckle) and of the toes, in the world. A foreleg's shoulder blade rolls by `scapula` first."""
    dx, dy, dz, ankle, toe = foot
    state = fk(pose, shift)
    knuckle = V(BONES[leg + "Toes"][1]) + V((dx, dy, dz))
    if leg in FRONT:
        pose[leg + "Scapula"] = (scapula, 0, 0)
        state = fk(pose, shift)
        names = (leg + "Upper", leg + "Lower", leg + "Paw")
        pole = V((0, -0.2, 1))
    else:
        names = (leg + "Thigh", leg + "Shin", leg + "Meta")
        pole = V((0, 0.1, -1))
    root = state[names[0]][1]
    ankle_world = _rx(ankle)
    wrist = knuckle - ankle_world @ _REST[names[2]]
    elbow, reached, stretch = _two_bone(root, wrist, _REST[names[0]].length, _REST[names[1]].length, pole)
    REACH[leg] = max(REACH.get(leg, 0), stretch)
    upper = _hinged(_REST[names[0]], elbow - root)
    lower = _hinged(_REST[names[1]], reached - elbow)
    pose[names[0]] = _euler(state[BONES[names[0]][0]][0].inverted() @ upper)
    pose[names[1]] = _euler(upper.inverted() @ lower)
    pose[names[2]] = _euler(lower.inverted() @ ankle_world)
    pose[leg + "Toes"] = _euler(ankle_world.inverted() @ _rx(toe))


def _level_head(pose, shift, pitch=0.0, yaw=0.0):
    """The head holds its own line in the world while the body rolls under it, as a stalking cat's does."""
    state = fk(pose, shift)
    _set_world(pose, state, "Head", _rx(pitch) @ Matrix.Rotation(math.radians(yaw), 3, "Y"))


def _hangings(pose, shift):
    """The heavy mane hangs from the neck: what the neck does, it mostly doesn't, so sitting up or lowering the head never swings it out."""
    for bone, keep in (("ManeChest", 0.5), ("LeftMane", 0.35), ("RightMane", 0.35)):
        state = fk(pose, shift)
        own = _mat(pose.get(bone, (0, 0, 0)))
        parent = state[BONES[bone][0]][0]
        q = parent.inverted().to_quaternion().slerp(Matrix.Identity(3).to_quaternion(), 1 - keep)
        pose[bone] = _euler(q.to_matrix() @ own)


TAIL_FLOOR = 2.0


def _tail_low(pose, shift):
    state = fk(pose, shift)
    points = [tail_of(state, "Tail%d" % k) for k in range(2, 7)]
    r, _ = state["Tail6"]
    points.append(tail_of(state, "Tail6") + r @ (_REST["Tail6"].normalized() * 2.4))
    return min(q.y for q in points)


def _tail_clear(pose, shift):
    """Wherever the body goes, the tail stays above the ground. Each joint turns the way that actually lifts its lowest point, which depends on
    where the tail is lying, and in proportion to how much it helps, so it curves instead of kinking. A tail already clear isn't touched."""
    joints = ["Tail%d" % k for k in range(1, 6)]
    for _ in range(8):
        low = _tail_low(pose, shift)
        need = TAIL_FLOOR - low
        if need < 0.02:
            return
        gains = []
        for n in joints:
            p = pose.get(n, (0, 0, 0))
            pose[n] = (p[0] + 1.0, p[1], p[2])
            gains.append(_tail_low(pose, shift) - low)
            pose[n] = p
        total = sum(g * g for g in gains)
        if total < 1e-6:
            return
        for n, g in zip(joints, gains):
            p = pose.get(n, (0, 0, 0))
            pose[n] = (p[0] + max(-18.0, min(18.0, g * need / total)), p[1], p[2])


STAND_SHIFT = (0, -0.5, 0)
STAND_BODY = {"Neck1": (-2, 0, 0), "Neck2": (1, 0, 0), "Tail1": (6, 0, 0), "Tail2": (2, 0, 0), "Tail5": (-6, 0, 0), "Tail6": (-10, 0, 0)}


def standing(body=None, shift=STAND_SHIFT, feet=None):
    pose = dict(STAND_BODY)
    pose.update(body or {})
    feet = feet or {}
    for leg in LEGS:
        solve_leg(pose, shift, leg, feet.get(leg, (0, 0, 0, 0, 0)), feet.get(leg + "Scapula", 0.0))
    return pose


# ---------- the gaits ----------
# A walk is a lateral sequence: hind, fore on the same side, the other hind, the other fore, never fewer than two paws down. Its run is a
# rotary gallop: the two hinds land close together, then the two fores, the same way round, with a gathered flight between them.
# Each paw's stride is measured: stride = what a planted paw travels back under him, per share of the cycle it stays down.
GAITS = {
    "walk": {
        "reach": {"Front": 5.1, "Back": 5.1}, "centre": {"Front": -0.3, "Back": 1.0}, "duty": 0.64, "lift": {"Front": 2.5, "Back": 1.5},
        "phase": {"BackLeft": 0.0, "FrontLeft": 0.24, "BackRight": 0.5, "FrontRight": 0.74},
        "hips": -1.45, "bob": 0.24, "yaw": 6.0, "roll": 2.8, "chest_yaw": 7.0, "chest_roll": 3.2, "pitch": 1.2, "flex": 0.0,
        "scapula": 15.0, "heel": {"Front": -36, "Back": -32}, "swing": {"Front": -74, "Back": -38}, "neck": -5.0, "head": -3.0, "nod": 1.4, "tail": (10, -2), "speed": 12,
    },
    "run": {
        "reach": {"Front": 5.0, "Back": 5.0}, "centre": {"Front": -0.8, "Back": 1.3}, "duty": 0.36, "lift": {"Front": 4.2, "Back": 2.2},
        "phase": {"BackLeft": 0.0, "BackRight": 0.11, "FrontRight": 0.47, "FrontLeft": 0.6},
        "hips": -1.8, "bob": 0.7, "yaw": 3.0, "roll": 2.2, "chest_yaw": 3.0, "chest_roll": 2.4, "pitch": 2.5, "flex": 7.5,
        "scapula": 21.0, "heel": {"Front": -46, "Back": -38}, "swing": {"Front": -88, "Back": -36}, "neck": -9.0, "head": -6.0, "nod": 2.6, "tail": (-24, 6), "speed": 21,
    },
}


def stride_of(g):
    return 2 * g["reach"]["Back"] / g["duty"]


def _ease(u):
    return u * u * (3 - 2 * u)


def _step(g, end, p):
    """A paw through its cycle, p from touching down: (dz, dy, ankle, toe, reach share forward 1 .. back -1)."""
    reach, duty, lift = g["reach"][end], g["duty"], g["lift"][end]
    centre = g["centre"][end]
    heel, swing = g["heel"][end], g["swing"][end]
    if p < duty:
        u = p / duty
        dz = centre - reach + 2 * reach * u
        # it rolls: pads flat through the stance, then the heel rises over the knuckle while the knuckle stays down
        roll = max(0.0, (u - 0.58) / 0.42)
        land = max(0.0, 1 - u / 0.12)
        ankle = heel * roll ** 1.6 + 7 * land
        return dz, 0.0, ankle, -4 * land, 1 - 2 * u
    w = (p - duty) / (1 - duty)
    dz = centre + reach - 2 * reach * _ease(w)
    # it leaves toe last and swings tucked, then reaches out and opens just before it lands
    height = lift * math.sin(math.pi * w ** 0.8) ** 1.1
    tuck = math.sin(math.pi * min(1.0, w * 1.15)) ** 0.9
    ankle = heel + (swing - heel) * min(1.0, w / 0.32) if w < 0.32 else swing + (7 - swing) * _ease((w - 0.32) / 0.68)
    toe = -30 * math.sin(math.pi * min(1.0, w * 1.5)) * (1 if w < 0.67 else 0) - 4 * max(0, w - 0.67) / 0.33
    return dz, height + 0.0 * tuck, ankle, toe, -1 + 2 * _ease(w)


def gait_body(g, phase):
    """The body over its paws: pelvis and shoulders each turn with their own legs and roll away from the leg in the air, so the spine bends
    between them; in the run the back gathers and stretches once a stride."""
    ph = g["phase"]
    duty = g["duty"]
    mid = duty + (1 - duty) / 2
    hip_yaw = -g["yaw"] * math.cos(TAU * (phase - ph["BackLeft"]))
    hip_roll = g["roll"] * math.cos(TAU * (phase - ph["BackLeft"] - mid))
    fore_yaw = -g["chest_yaw"] * math.cos(TAU * (phase - ph["FrontLeft"]))
    fore_roll = g["chest_roll"] * math.cos(TAU * (phase - ph["FrontLeft"] - mid))
    # two dips a stride: the body sinks as each hind takes the weight
    bob = g["bob"] * math.cos(2 * TAU * (phase - ph["BackLeft"] - 0.12))
    flex = g["flex"] * math.cos(TAU * (phase - 0.2))       # + gathered, the back rounded: hinds reaching under, fores about to leave
    pitch = g["pitch"] * math.sin(TAU * (phase - 0.2))
    if g["flex"]:
        bob = g["bob"] * math.cos(TAU * (phase - 0.32))    # the run rises once, into the flight
    body = {
        "Hips": (pitch + flex * 0.6, hip_yaw, hip_roll),
        "Spine": (-flex * 0.55, (fore_yaw - hip_yaw) * 0.45, (fore_roll - hip_roll) * 0.45),
        "Chest": (-flex * 0.65 - (2.5 if g["flex"] else 1.0), (fore_yaw - hip_yaw) * 0.55, (fore_roll - hip_roll) * 0.55),
        "Neck1": (g["neck"], -fore_yaw * 0.55, -fore_roll * 0.5),
        "Neck2": (-flex * 0.2 + 1, -fore_yaw * 0.35, -fore_roll * 0.3),
    }
    return body, (0, g["hips"] + bob, 0.32 * math.sin(2 * TAU * phase) if not g["flex"] else -0.7 * math.sin(TAU * (phase - 0.2)))


def gait_pose(name, phase):
    g = GAITS[name]
    body, shift = gait_body(g, phase)
    pose = dict(STAND_BODY)
    pose.update(body)
    for leg in LEGS:
        end = "Front" if leg in FRONT else "Back"
        p = (phase - g["phase"][leg]) % 1
        dz, dy, ankle, toe, share = _step(g, end, p)
        scapula = g["scapula"] * share if end == "Front" else 0.0
        solve_leg(pose, shift, leg, (0, dy, dz, ankle, toe), scapula)
    # the head rides level, nodding a beat late; the tail swings across behind it, each joint later than the last
    nod = g["nod"] * math.sin(2 * TAU * (phase - 0.2))
    if g["flex"]:
        nod = g["nod"] * math.sin(TAU * (phase - 0.42))
    _level_head(pose, shift, g["head"] + nod)
    base, curl = g["tail"]
    for k in range(1, 7):
        lag = TAU * (phase - 0.09 * k)
        sway = (2.2 + 1.3 * k) * math.sin(lag) * (0.5 if g["flex"] else 1.0)
        pose["Tail%d" % k] = (STAND_BODY.get("Tail%d" % k, (0, 0, 0))[0] + (base if k == 1 else curl) + (1.6 * k * math.sin(2 * lag) if g["flex"] else 0), sway, 0)
    _hangings(pose, shift)
    _tail_clear(pose, shift)
    return pose, shift


# ---------- the poses it holds ----------
def _tail_lying(sign=1):
    """The tail curled forward on the ground along the hind paw, as a seated cat keeps it."""
    return {"Tail1": (72, sign * 18, 0), "Tail2": (24, sign * 22, 0), "Tail3": (10, sign * 26, 0), "Tail4": (0, sign * 26, 0), "Tail5": (-4, sign * 22, 0), "Tail6": (-2, sign * 16, 0)}


SIT_SHIFT = (0, -9.4, 2.2)
SIT_BODY = dict({"Hips": (22, 0, 0), "Spine": (7, 0, 0), "Chest": (8, 0, 0), "Neck1": (-17, 0, 0), "Neck2": (20, 0, 0)}, **_tail_lying())     # the neck bends in two, so the collar lies on the chest
SIT_FEET = {"BackLeft": (0, 0.0, -3.2, 54, 0), "BackRight": (0, 0.0, -3.2, 54, 0), "FrontLeft": (0.2, 0, 0.6, -6, 0), "FrontRight": (-0.2, 0, 0.6, -6, 0)}


def sit_pose(head=-2.0):
    pose = dict(SIT_BODY)
    for leg in LEGS:
        solve_leg(pose, SIT_SHIFT, leg, SIT_FEET[leg], -8.0 if leg in FRONT else 0.0)
    _level_head(pose, SIT_SHIFT, head)
    _hangings(pose, SIT_SHIFT)
    _tail_clear(pose, SIT_SHIFT)
    return pose, SIT_SHIFT


def state_poses():
    stand = standing()
    _level_head(stand, STAND_SHIFT, 0.0)
    _hangings(stand, STAND_SHIFT)
    _tail_clear(stand, STAND_SHIFT)
    s0 = STAND_SHIFT
    states = {"Guardian": (dict(stand), s0)}
    p = dict(stand)
    _level_head(p, s0, -5.0)
    _hangings(p, s0)
    _tail_clear(p, s0)
    states["Returning"] = (p, s0)
    sit, sit_shift = sit_pose()
    states["Dormant"] = (sit, sit_shift)
    states["Resting"] = (dict(sit), sit_shift)
    # hurt: the left paw held off the ground, the weight on the other three, the head hanging, the tail limp
    s = (0, -1.5, 0.5)
    p = standing({"Hips": (-2, 0, 2), "Spine": (0, 0, 1), "Chest": (-3, 0, 3), "Neck1": (-14, 0, -2), "Neck2": (-6, 0, 0), "Jaw": (-16, 0, 0), "Tail1": (20, 0, 0), "Tail2": (8, 0, 0), "LeftEar": (20, 0, 0), "RightEar": (20, 0, 0)},
                 s, {"FrontLeft": (0.3, 5.0, 0.8, -82, -30), "FrontLeftScapula": 8.0, "FrontRight": (-1.0, 0, -0.5, 0, 0), "BackLeft": (0.4, 0, -0.4, 0, 0)})
    _level_head(p, s, -26.0)
    _hangings(p, s)
    _tail_clear(p, s)
    states["Weakened"] = (p, s)
    # enraged: low on its legs, shoulders high, head low and forward, lips back, the tail up and lashing
    s = (0, -2.9, -0.6)
    p = standing({"Hips": (1, 0, 0), "Chest": (-5, 0, 0), "Neck1": (-10, 0, 0), "Neck2": (-2, 0, 0), "Jaw": (-14, 0, 0), "Tail1": (-22, 0, 0), "Tail2": (-10, 0, 0), "Tail3": (-6, 0, 0), "Tail5": (-22, 0, 0), "Tail6": (-30, 0, 0), "LeftEar": (34, 0, 0), "RightEar": (34, 0, 0)},
                 s, {"FrontLeft": (-0.4, 0, -1.4, -6, 0), "FrontRight": (0.4, 0, 0.8, -4, 0), "FrontLeftScapula": 7.0, "FrontRightScapula": 2.0})
    _level_head(p, s, -9.0)
    _hangings(p, s)
    _tail_clear(p, s)
    states["Enraged"] = (p, s)
    return stand, s0, states


# ---------- the moves: each a list of keys, solved every frame so a planted paw never leaves its spot ----------
def _key(at, ease="smooth", body=None, shift=STAND_SHIFT, feet=None, head=None, scap=None, air=False):
    return {"at": at, "ease": ease, "body": body or {}, "shift": shift, "feet": feet or {}, "head": head, "scap": scap or {}, "air": air}


def _mix_angles(a, b, u):
    qa, qb = _mat(a).to_quaternion(), _mat(b).to_quaternion()
    return _euler(qa.slerp(qb, u).to_matrix())


def clip_pose(t, keys):
    """The pose at time t. The body's turns slerp between keys; the paws' targets move between keys in straight lines (an arc needs a key)
    and the legs are solved afresh, so a paw that doesn't move stays exactly on its spot."""
    if t >= keys[-1]["at"]:
        a = b = keys[-1]
        u = 0.0
    else:
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if t <= b["at"]:
                u = (t - a["at"]) / (b["at"] - a["at"])
                u = {"in": u * u * u, "out": 1 - (1 - u) ** 3, "smooth": _ease(u), "linear": u, "in2": u * u}[b["ease"]]
                break
    pose = dict(STAND_BODY)
    names = (set(a["body"]) | set(b["body"]))
    for n in names:
        pose[n] = _mix_angles(a["body"].get(n, STAND_BODY.get(n, (0, 0, 0))), b["body"].get(n, STAND_BODY.get(n, (0, 0, 0))), u)
    shift = tuple(a["shift"][k] + (b["shift"][k] - a["shift"][k]) * u for k in range(3))
    for leg in LEGS:
        fa, fb = a["feet"].get(leg, (0, 0, 0, 0, 0)), b["feet"].get(leg, (0, 0, 0, 0, 0))
        foot = tuple(fa[k] + (fb[k] - fa[k]) * u for k in range(5))
        scap = a["scap"].get(leg, 0.0) + (b["scap"].get(leg, 0.0) - a["scap"].get(leg, 0.0)) * u
        solve_leg(pose, shift, leg, foot, scap)
    ha = a["head"] if a["head"] is not None else 0.0
    hb = b["head"] if b["head"] is not None else 0.0
    _level_head(pose, shift, ha + (hb - ha) * u)
    _hangings(pose, shift)
    _tail_clear(pose, shift)
    return pose, shift


SIT_KEY_BODY = dict(SIT_BODY)
_JAW = lambda deg: (deg, 0, 0)


def clips():
    out = {}
    L, R = "FrontLeft", "FrontRight"
    # the slam: the weight rocks back and onto the right, the left paw rises high and hangs, then the whole forequarter drives it down
    w = 0.75
    out["Slam"] = [
        _key(0.0, head=0.0),
        _key(0.26, "smooth", {"Hips": (1, 0, 2), "Chest": (-4, -5, 4), "Neck1": (-6, -4, 0), "Tail1": (-4, 0, 0), "Jaw": _JAW(-6)}, (0.7, -1.7, 1.5), {L: (0, 0.9, 0.5, -30, 0)}, -6.0),
        _key(w - 0.13, "smooth", {"Hips": (3, 0, 4), "Spine": (2, 0, 1), "Chest": (4, 5, 5), "Neck1": (8, 6, 0), "Neck2": (6, 0, 0), "Tail1": (-22, 0, 0), "Tail2": (-8, 0, 0), "Jaw": _JAW(-22)}, (1.1, -1.7, 2.0),
             {L: (-0.4, 12.5, -7.0, 30, 24), R: (0.2, 0, 0.4, -8, 0)}, 8.0, {L: 26.0, R: -6.0}),
        _key(w, "in", {"Hips": (-3, 0, -3), "Spine": (-3, 0, -1), "Chest": (-6, -6, -5), "Neck1": (-3, -8, 0), "Neck2": (-2, 0, 0), "Tail1": (-30, 0, 0), "Tail2": (-16, 0, 0), "Jaw": _JAW(-40), "ManeChest": (10, 0, 0)}, (-0.6, -2.6, -2.6),
             {L: (0.8, 0, -10.0, 8, 0)}, -16.0, {L: 18.0}),
        _key(w + 0.28, "out", {"Hips": (-2, 0, -2), "Spine": (-2, 0, -1), "Chest": (-6, -4, -4), "Neck1": (-6, -6, 0), "Tail1": (-18, 0, 0), "Jaw": _JAW(-30)}, (-0.4, -2.7, -2.1), {L: (0.8, 0, -10.0, 4, 0)}, -11.0, {L: 16.0}),
        _key(w + 0.56, "smooth", {"Hips": (-1, 0, 0), "Chest": (-3, -2, -1), "Jaw": _JAW(-10)}, (0, -1.5, -1.0), {L: (0.4, 3.2, -5.0, -52, -12)}, -4.0, {L: 8.0}),
        _key(w + 0.85, "smooth", head=0.0),
    ]
    # the roar: it coils, head low and haunches sinking, draws the breath in with its chest swelling, then thrusts its head out and up with
    # its jaws wide and its whole body behind it, holds it shuddering, and lets it go
    w = 1.1
    tail_up = {"Tail1": (-26, 0, 0), "Tail2": (-12, 0, 0), "Tail3": (-8, 0, 0), "Tail5": (-22, 0, 0), "Tail6": (-26, 0, 0)}
    out["Roar"] = [
        _key(0.0, head=0.0),
        _key(0.34, "smooth", {"Hips": (-3, 0, 0), "Chest": (-5, 0, 0), "Neck1": (-16, 0, 0), "Neck2": (-6, 0, 0), "Tail1": (20, 0, 0), "LeftEar": (20, 0, 0), "RightEar": (20, 0, 0)}, (0, -2.4, 1.8), None, -24.0),
        _key(w - 0.16, "smooth", {"Hips": (1, 0, 0), "Spine": (1, 0, 0), "Chest": (3, 0, 0), "Neck1": (8, 0, 0), "Neck2": (2, 0, 0), "Jaw": _JAW(-12), "Tail1": (0, 0, 0)}, (0, -1.3, 2.1), None, 4.0),
        _key(w + 0.03, "in", dict(tail_up, Hips=(-1, 0, 0), Spine=(1, 0, 0), Chest=(1, 0, 0), Neck1=(4, 0, 0), Neck2=(4, 0, 0), Jaw=_JAW(-48), LeftEar=(40, 0, 0), RightEar=(40, 0, 0), ManeTop=(-14, 0, 0), LeftMane=(-16, 0, 0), RightMane=(-16, 0, 0)), (0, -2.4, -2.0), None, 22.0),
        _key(w + 0.75, "linear", dict(tail_up, Hips=(-1, 0, 0), Spine=(1, 0, 0), Chest=(0, 0, 0), Neck1=(2, 0, 0), Neck2=(3, 0, 0), Jaw=_JAW(-44), LeftEar=(36, 0, 0), RightEar=(36, 0, 0)), (0, -2.3, -1.6), None, 18.0),
        _key(w + 1.4, "smooth", head=0.0),
    ]
    # the pounce: a deep crouch with the haunches loaded; the hinds drive, the fores reach, stretched out long; then the nose comes down
    crouch = {"Hips": (6, 0, 0), "Spine": (-3, 0, 0), "Chest": (-6, 0, 0), "Neck1": (-6, 0, 0), "Tail1": (-14, 0, 0), "LeftEar": (28, 0, 0), "RightEar": (28, 0, 0)}
    out["Pounce"] = [
        _key(0.0, head=0.0),
        _key(0.42, "smooth", crouch, (0, -6.0, 2.0), {"FrontLeft": (0, 0, 0.6, -8, 0), "FrontRight": (0, 0, 0.6, -8, 0), "BackLeft": (0, 0, -0.6, -14, 0), "BackRight": (0, 0, -0.3, -14, 0)}, -10.0),
        _key(0.60, "in2", {"Hips": (12, 0, 0), "Spine": (2, 0, 0), "Chest": (6, 0, 0), "Neck1": (0, 0, 0), "Jaw": _JAW(-14), "Tail1": (-6, 0, 0)}, (0, -0.2, -2.2),
             {"FrontLeft": (0, 6.0, -5.0, -46, -18), "FrontRight": (0, 6.6, -6.0, -44, -18), "BackLeft": (0, 0, 2.6, -46, 8), "BackRight": (0, 0, 2.9, -46, 8)}, 2.0, {"FrontLeft": 18.0, "FrontRight": 20.0}),
        _key(0.92, "out", {"Hips": (6, 0, 0), "Spine": (-2, 0, 0), "Chest": (-3, 0, 0), "Neck1": (2, 0, 0), "Jaw": _JAW(-34), "Tail1": (-18, 0, 0), "Tail2": (-6, 0, 0), "LeftEar": (30, 0, 0), "RightEar": (30, 0, 0), "ManeTop": (-10, 0, 0), "LeftMane": (-14, 0, 0), "RightMane": (-14, 0, 0)}, (0, 0, -0.5),
             {"FrontLeft": (0, 8.0, -9.0, 8, 22), "FrontRight": (0, 8.4, -9.4, 8, 22), "BackLeft": (0, 4.4, 9.0, -64, -20), "BackRight": (0, 4.2, 9.6, -64, -20)}, 2.0, {"FrontLeft": 26.0, "FrontRight": 26.0}),
        _key(1.35, "smooth", {"Hips": (-7, 0, 0), "Spine": (-1, 0, 0), "Chest": (-2, 0, 0), "Neck1": (6, 0, 0), "Jaw": _JAW(-34), "Tail1": (-34, 0, 0), "Tail2": (-10, 0, 0), "ManeTop": (10, 0, 0)}, (0, 0, -0.5),
             {"FrontLeft": (0, 0.2, -8.6, 12, 14), "FrontRight": (0, 0.4, -9.2, 12, 14), "BackLeft": (0, 3.0, -2.0, -34, -18), "BackRight": (0, 2.8, -1.4, -34, -18)}, -6.0, {"FrontLeft": 24.0, "FrontRight": 24.0}),
        _key(1.55, "smooth", {"Hips": (-9, 0, 0), "Chest": (-2, 0, 0), "Neck1": (4, 0, 0), "Jaw": _JAW(-24), "Tail1": (-30, 0, 0)}, (0, -0.4, -0.6),
             {"FrontLeft": (0, 0, -7.6, 10, 2), "FrontRight": (0, 0, -8.2, 10, 2), "BackLeft": (0, 2.2, -4.0, -18, -8), "BackRight": (0, 2.0, -3.4, -18, -8)}, -8.0, {"FrontLeft": 20.0, "FrontRight": 20.0}),
    ]
    # the landing: the forelegs take it and fold, the chest nearly to the ground; the hinds come through and land; it rises out of it
    out["Land"] = [
        _key(0.0, "smooth", {"Hips": (-9, 0, 0), "Chest": (-2, 0, 0), "Neck1": (4, 0, 0), "Jaw": _JAW(-24), "Tail1": (-30, 0, 0)}, (0, -0.4, -0.6),
             {"FrontLeft": (0, 0, -7.6, 10, 0), "FrontRight": (0, 0, -8.2, 10, 0), "BackLeft": (0, 2.2, -4.0, -18, -8), "BackRight": (0, 2.0, -3.4, -18, -8)}, -8.0, {"FrontLeft": 20.0, "FrontRight": 20.0}),
        _key(0.14, "out", {"Hips": (-7, 0, 0), "Spine": (3, 0, 0), "Chest": (-3, 0, 0), "Neck1": (0, 0, 0), "Jaw": _JAW(-30), "Tail1": (-26, 0, 0), "ManeTop": (14, 0, 0), "LeftMane": (8, 0, 0), "RightMane": (8, 0, 0), "ManeChest": (0, 0, 0)}, (0, -3.5, -2.2),
             {"FrontLeft": (0, 0, -7.6, 22, 0), "FrontRight": (0, 0, -8.2, 22, 0), "BackLeft": (0, 0.0, -3.2, -6, 0), "BackRight": (0, 0.0, -2.8, -6, 0)}, -14.0, {"FrontLeft": 6.0, "FrontRight": 6.0}),
        _key(0.42, "smooth", {"Hips": (-3, 0, 0), "Chest": (-2, 0, 0), "Neck1": (-3, 0, 0), "Jaw": _JAW(-12)}, (0, -2.6, -1.2),
             {"FrontLeft": (0, 0, -7.6, 6, 0), "FrontRight": (0, 0, -8.2, 6, 0), "BackLeft": (0, 0, -3.2, 0, 0), "BackRight": (0, 0, -2.8, 0, 0)}, -6.0, {"FrontLeft": 10.0, "FrontRight": 10.0}),
        _key(0.68, "smooth", {"Neck1": (-2, 0, 0)}, (0, -1.0, -0.4),
             {"FrontLeft": (0, 2.2, -3.6, -44, -14), "FrontRight": (0, 0, -8.2, 2, 0), "BackLeft": (0, 0, -3.2, 0, 0), "BackRight": (0, 1.8, -1.4, -30, -8)}, -2.0, {"FrontRight": 12.0}),
        _key(0.95, "smooth", None, STAND_SHIFT, {"FrontRight": (0, 1.6, -3.0, -36, -10), "BackLeft": (0, 1.6, -1.6, -28, -8)}, 0.0),
        _key(1.2, "smooth", head=0.0),
    ]
    # waking: the stone shudders, the head comes up, the chest fills; it gathers its hinds under it, rises, shakes the dust from its mane
    sit_feet = dict(SIT_FEET)
    sit_scap = {"FrontLeft": -8.0, "FrontRight": -8.0}
    out["Awaken"] = [
        _key(0.0, "smooth", SIT_BODY, SIT_SHIFT, sit_feet, -2.0, sit_scap),
        _key(0.45, "out", dict(SIT_BODY, Neck1=(-20, 0, 0), Chest=(6, 0, 0)), (0, -9.6, 2.2), sit_feet, -14.0, sit_scap),
        _key(1.05, "smooth", dict(SIT_BODY, Chest=(8, 0, 0), Neck1=(-10, 0, 0), Neck2=(16, 0, 0), Jaw=_JAW(-12)), (0, -9.4, 2.2), sit_feet, 12.0, sit_scap),
        _key(1.5, "smooth", dict(_tail_lying(), Hips=(8, 0, 0), Spine=(2, 0, 0), Chest=(2, 0, 0), Neck1=(4, 0, 0)), (0, -4.2, 0.8),
             {"BackLeft": (0, 0.0, -3.0, 22, 0), "BackRight": (0, 0.0, -3.0, 22, 0), "FrontLeft": (0, 0, 0.3, -2, 0), "FrontRight": (0, 0, 0.3, -2, 0)}, -4.0),
        _key(1.85, "smooth", {"Hips": (1, 0, 0), "Neck1": (-3, 0, 0), "Tail1": (40, 6, 0), "Tail2": (10, 6, 0), "Tail3": (-6, 6, 0), "Tail4": (-10, 0, 0), "Tail5": (-14, 0, 0)}, (0, -0.9, 0.1),
             {"BackLeft": (0, 1.3, -1.6, -24, -8), "BackRight": (0, 0.0, -1.0, 0, 0)}, -4.0),
        _key(2.15, "smooth", {"Neck1": (-3, 12, 0), "Neck2": (2, 10, 0), "ManeTop": (0, -8, 0), "LeftMane": (0, -14, 0), "RightMane": (0, -14, 0)}, STAND_SHIFT, {"BackRight": (0, 1.0, -0.6, -18, -6)}, -3.0),
        _key(2.4, "smooth", {"Neck1": (-3, -12, 0), "Neck2": (2, -10, 0), "ManeTop": (0, 8, 0), "LeftMane": (0, 14, 0), "RightMane": (0, 14, 0)}, STAND_SHIFT, None, -3.0),
        _key(2.8, "smooth", head=0.0),
    ]
    # settling down to sit: the hinds step forward, the rump lowers, the chest stays up
    out["SitDown"] = [
        _key(0.0, head=0.0),
        _key(0.32, "smooth", {"Hips": (3, 0, 0), "Neck1": (-1, 0, 0), "Tail1": (40, 6, 0), "Tail2": (10, 6, 0), "Tail3": (-6, 6, 0), "Tail4": (-10, 0, 0), "Tail5": (-14, 0, 0)}, (0, -1.3, 0.3),
             {"BackLeft": (0, 0.8, -1.0, -12, -4), "BackRight": (0, 0.0, -0.8, 0, 0)}, -1.0),
        _key(0.6, "smooth", dict(_tail_lying(), Hips=(5, 0, 0), Neck1=(0, 0, 0)), (0, -2.2, 0.6), {"BackLeft": (0, 1.4, -1.8, -22, -8), "BackRight": (0, 0.0, -1.4, 0, 0)}, -2.0),
        _key(0.95, "smooth", dict(_tail_lying(), Hips=(13, 0, 0), Spine=(3, 0, 0), Chest=(4, 0, 0), Neck1=(-8, 0, 0), Neck2=(10, 0, 0)), (0, -5.6, 1.4),
             {"BackLeft": (0, 0, -2.8, 30, 0), "BackRight": (0, 0, -2.8, 30, 0), "FrontLeft": (0, 0, 0.3, -3, 0), "FrontRight": (0, 0, 0.3, -3, 0)}, -2.0),
        _key(1.5, "smooth", SIT_BODY, SIT_SHIFT, sit_feet, -2.0, sit_scap),
    ]
    # faltering: a blow it can't take: the head whips aside, the left foreleg gives, it catches itself and draws the paw up
    stand_w, s_w = state_poses()[2]["Weakened"]
    out["Weaken"] = [
        _key(0.0, head=0.0),
        _key(0.2, "out", {"Hips": (-2, 0, -2), "Chest": (-5, 8, -5), "Neck1": (-6, 18, 0), "Neck2": (2, 10, 0), "Jaw": _JAW(-34), "LeftMane": (0, 14, 0), "RightMane": (0, 14, 0), "Tail1": (-16, 0, 0)}, (0.6, -1.6, 0.8), None, 6.0),
        _key(0.62, "smooth", {"Hips": (-3, 0, 3), "Spine": (-2, 0, 0), "Chest": (-7, -3, 8), "Neck1": (-8, -6, 0), "Neck2": (-6, -4, 0), "Jaw": _JAW(-24), "Tail1": (22, 0, 0)}, (-0.4, -3.2, -0.6),
             {"FrontLeft": (0, 0, -1.0, 22, 0), "FrontRight": (0, 0, -1.2, 10, 0)}, -24.0),
        _key(1.05, "smooth", {"Hips": (-3, 0, 2), "Chest": (-6, 0, 5), "Neck1": (-18, 0, -2), "Neck2": (-8, 0, 0), "Jaw": _JAW(-18), "Tail1": (22, 0, 0)}, (0, -2.6, 0.4),
             {"FrontLeft": (0.2, 1.6, 0.0, -60, -18), "FrontRight": (-1.0, 0, -0.5, 0, 0), "BackLeft": (0.4, 0, -0.4, 0, 0)}, -28.0, {"FrontLeft": 4.0}),
        _key(1.7, "smooth", {"Hips": (-2, 0, 2), "Spine": (0, 0, 1), "Chest": (-3, 0, 3), "Neck1": (-14, 0, -2), "Neck2": (-6, 0, 0), "Jaw": _JAW(-16), "Tail1": (20, 0, 0), "Tail2": (8, 0, 0), "LeftEar": (20, 0, 0), "RightEar": (20, 0, 0)}, (0, -1.5, 0.5),
             {"FrontLeft": (0.3, 5.0, 0.8, -82, -30), "FrontRight": (-1.0, 0, -0.5, 0, 0), "BackLeft": (0.4, 0, -0.4, 0, 0)}, -26.0, {"FrontLeft": 8.0}),
    ]
    return out


# ---------- reviewing the motion ----------
def filmstrip(path, frames, yaw=-90, pitch=4, size=360, columns=6, distance=108, centre=(0, 13, 2)):
    """frames: [(pose, shift)]. A strip of stills from one side, on the ground line."""
    scene, cam = T._review_scene(size)
    _hide_rig()
    floor = bpy.data.objects.get("LN2_Floor")
    if not floor:
        me = bpy.data.meshes.new("LN2_Floor")
        me.from_pydata([W.rb(-60, 0, -60), W.rb(60, 0, -60), W.rb(60, 0, 60), W.rb(-60, 0, 60)], [], [(0, 1, 2, 3)])
        floor = bpy.data.objects.new("LN2_Floor", me)
        floor.data.materials.append(_clay("LionClayFloor", (0.55, 0.58, 0.6)))
        bpy.context.scene.collection.objects.link(floor)
    tmp = path + ".tile.png"
    tiles = []
    for pose, shift in frames:
        set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, yaw, pitch, distance, W.rb(*centre), size, tmp))
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


# ---------- the stone, and everything on it ----------
def mat_granite(name="LionV2Granite"):
    """Weathered granite: warm grey flecked dark and light, split by old cracks, darkest in the hollows, moss on the upward faces."""
    g = Hm._Graph(name)
    co = g.coords()
    big = g.n("ShaderNodeTexNoise", **{"Scale": 0.32, "Detail": 5.0, "Roughness": 0.58})
    g.link(co, big.inputs["Vector"])
    col = g.ramp(big.outputs["Fac"], [(0.3, (0.1, 0.095, 0.085)), (0.52, (0.185, 0.175, 0.155)), (0.74, (0.31, 0.295, 0.26))])
    fleck = g.n("ShaderNodeTexNoise", **{"Scale": 13.0, "Detail": 2.0})
    g.link(co, fleck.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("GREATER_THAN", fleck.outputs["Fac"], 0.64), 0.65), col, (0.035, 0.033, 0.03))
    col = g.mix(g.math("MULTIPLY", g.math("LESS_THAN", fleck.outputs["Fac"], 0.3), 0.35), col, (0.46, 0.44, 0.4))
    # old cracks: long broken lines, only here and there
    cell = g.n("ShaderNodeTexVoronoi", **{"Scale": 0.2})
    cell.feature = "DISTANCE_TO_EDGE"
    g.link(co, cell.inputs["Vector"])
    patch = g.n("ShaderNodeTexNoise", **{"Scale": 0.16, "Detail": 3.0})
    g.link(co, patch.inputs["Vector"])
    crack = g.math("MULTIPLY", g.math("LESS_THAN", cell.outputs["Distance"], 0.016), g.math("GREATER_THAN", patch.outputs["Fac"], 0.56))
    crack = g.math("MULTIPLY", crack, g.math("LESS_THAN", g.sep(co)[1], 12.5))     # never across the face: Blender's +Y is ahead of him
    col = g.mix(g.math("MULTIPLY", crack, 0.8), col, (0.018, 0.018, 0.016))
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    mossn = g.n("ShaderNodeTexNoise", **{"Scale": 0.5, "Detail": 7.0})
    g.link(co, mossn.inputs["Vector"])
    moss = g.math("MULTIPLY", g.math("SUBTRACT", up, 0.32, clamp=True), g.math("SUBTRACT", g.math("MULTIPLY", mossn.outputs["Fac"], 2.2), 0.98, clamp=True))
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", moss, 3.4), 0.9), col, (0.075, 0.14, 0.035))
    col = g.ao(col, 0.8, 0.34)
    height = g.math("SUBTRACT", g.math("ADD", big.outputs["Fac"], g.math("MULTIPLY", fleck.outputs["Fac"], 0.35)), g.math("MULTIPLY", crack, 0.7))
    return g.finish(col, 0.86, 0.0, g.bump(height, 0.75, 0.09))


def materials():
    return {
        "granite": mat_granite(), "gold": Hm.mat_gold(), "ivory": T.mat_plain("LionV2Ivory", (0.62, 0.58, 0.47), 0.55),
        "mouth": T.mat_plain("LionV2Mouth", (0.11, 0.035, 0.035), 0.6), "tongue": T.mat_plain("LionV2Tongue", (0.27, 0.075, 0.08), 0.5),
        "nose": T.mat_plain("LionV2Nose", (0.035, 0.03, 0.03), 0.45), "claw": T.mat_plain("LionV2Claw", (0.075, 0.07, 0.065), 0.5),
    }


PIECES = {"Skin": 19400, "Jaw": 2600, "Mane": 16000, "Collar": 4000}
BAKES = {"Skin": dict(size=2048, small=1024, ray=0.3, extrusion=0.14), "Jaw": dict(size=512, small=256, ray=0.15, extrusion=0.06), "Mane": dict(size=2048, small=512, ray=0.4, extrusion=0.16), "Collar": dict(size=512, small=256, ray=0.1, extrusion=0.04)}
PREFIX = "StoneLionV2_"


def build_final(voxel=0.12):
    """The high-detail pieces, ready to bake: {piece: [objects]}, and the glow pieces {name: (object, hex)}."""
    T.clear()
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    M = materials()
    skin = _blob("LN2_SkinHi", coll, M["granite"], _groups(), voxel, cut=_mouth_cut, chisel="LionV2Chisel")
    # chisel-hewn planes across the stone, without moving its forms
    tex = bpy.data.textures.get("LionV2Hewn") or bpy.data.textures.new("LionV2Hewn", "VORONOI")
    tex.noise_scale = 1.9
    Hm.apply_modifiers(skin, [("DISPLACE", {"texture": tex, "strength": 0.075, "mid_level": 0.5, "texture_coords": "GLOBAL"})])
    for p in skin.data.polygons:
        p.use_smooth = True

    eyes, pupils, lids, nose, teeth, claws, tuft = (Hm.Hi() for _ in range(7))
    for side in (-1, 1):
        normal = V((side * 0.5, 0.08, -0.86)).normalized()
        seat = G.surface_along(skin, V((side * 1.82, 22.9, -19.0)), normal, reach=4.0) + normal * 0.06
        G.eye(eyes, pupils, lids, seat, normal, (-side * 0.62, -0.06, -1), 0.92, 0.42, tilt=0.42, bulge=0.1, lid=0.55, droop=0.62, lower=0.22, slit=0.3, pupil_height=0.66)
        for z, x, length, radius in ((-21.15, 1.32, 1.7, 0.38), (-20.0, 1.55, 0.62, 0.22), (-19.2, 1.62, 0.55, 0.2)):
            line = _mouth_line(z)
            G.cone(teeth, (side * x, line + 0.14, z), (side * (x - 0.06), line - length, z - 0.1), radius, sides=7)
        for k, x in enumerate((0.27, 0.8)):
            z = -21.75 + 0.1 * k
            G.cone(teeth, (side * x, _mouth_line(z) + 0.14, z), (side * x, _mouth_line(z) - 0.55, z - 0.04), 0.2, sides=6)
        for (x, z, wide) in ((5.25, -7.0, 1.0), (5.4, 13.3, 0.95)):
            for dx, length in ((-1.72, 1.85), (-0.6, 2.5), (0.6, 2.5), (1.72, 1.85)):
                tx = side * x + dx * side * wide
                tip = z - length
                G.cone(claws, (tx, 1.05, tip + 0.3), (tx, 0.12, tip - 0.85), 0.36, sides=7)
    nose_at = G.surface_along(skin, V((0, 22.05, -22.0)), V((0, 0.3, -1)).normalized(), reach=4.0)
    G.sphere(nose, nose_at + V((0, 0.02, 0.12)), 0.6, nu=14, nv=10, radii=(0.86, 0.46, 0.3))
    lines = Hm.Hi()
    top = G.surface_along(skin, nose_at + V((0, -0.42, 0)), V((0, 0, -1)), reach=3.0)
    bottom = G.surface_along(skin, V((0, _mouth_line(-22.8) + 0.16, -22.2)), V((0, 0, -1)), reach=3.0)
    Hm.htube(lines, [top, top.lerp(bottom, 0.5) + V((0, 0, 0.08)), bottom], lambda q: 0.075, sides=6, per=3, uv_scale=1.0, tip=True, wobble=0.0)
    rnd = random.Random(19)
    for k in range(24):
        a = TAU * k / 24
        root = V((0, 2.8, 28.4)) + V((math.cos(a) * 0.9, math.sin(a) * 0.8, rnd.uniform(-0.8, 0.8)))
        _lock(tuft, root, V((math.cos(a) * 0.22, math.sin(a) * 0.18, 1)), V((math.cos(a), math.sin(a), 0)), rnd.uniform(1.9, 3.0), 0.42, rnd)

    def kept(hi, name, mat):
        o = hi.object(name, coll, mat if isinstance(mat, list) else [mat])
        o["keep"] = True
        return o

    palate = G.blob("LN2_Palate", coll, M["mouth"], [((0, _mouth_line(-19.6) + 0.02, -19.6), (1.62, 0.26, 2.15), None), ((0, 19.75, -18.5), (1.8, 1.3, 0.5), None)], voxel=0.1, smooth=0.6, rough=0.0, chisel="LionV2Chisel3")
    palate["keep"] = False

    # the jaw: its own piece, a dark floor of the mouth, a tongue and the lower teeth
    jaw = _blob("LN2_JawHi", coll, M["granite"], JAW_GROUPS, 0.08, cut=_jaw_cut, soften=4)
    gum = G.blob("LN2_Gum", coll, M["mouth"], [((0, _mouth_line(-19.2) + 0.46, -19.2), (1.85, 0.16, 2.3), None)], voxel=0.07, smooth=0.6, rough=0.0, chisel="LionV2Chisel3")
    gum["keep"] = False
    tongue, jaw_teeth = Hm.Hi(), Hm.Hi()
    Hm.htube(tongue, [(0, _mouth_line(-16.9) + 0.42, -16.9), (0, _mouth_line(-19.0) + 0.6, -19.0), (0, _mouth_line(-20.6) + 0.5, -20.6)], lambda q: 0.72 * (1 - 0.3 * q), sides=9, per=4, uv_scale=1.0, tip=True, wobble=0.0)
    for side in (-1, 1):
        z = -20.9
        G.cone(jaw_teeth, (side * 1.02, _mouth_line(z) + 0.3, z), (side * 0.98, _mouth_line(z) + 1.65, z - 0.08), 0.34, sides=7)
        for x in (0.26, 0.62):
            G.cone(jaw_teeth, (side * x, _mouth_line(-21.2) + 0.3, -21.2), (side * x, _mouth_line(-21.2) + 0.92, -21.22), 0.17, sides=6)

    # the mane: one carving of mass and locks, with the gold collar lying over it and the jade orb on its chest
    mass = _blob("LN2_ManeMass", coll, M["granite"], _mane_mass(), 0.14, soften=4, chisel="LionV2Chisel2")
    hi = Hm.Hi()
    _mane_locks(hi, mass, random.Random(7))
    locks = hi.object("LN2_LocksHi", coll, [M["granite"]])
    mane = _fuse("LN2_ManeHi", coll, M["granite"], [mass, locks], 0.13)
    Hm.apply_modifiers(mane, [("DISPLACE", {"texture": tex, "strength": 0.05, "mid_level": 0.5, "texture_coords": "GLOBAL"})])
    for p in mane.data.polygons:
        p.use_smooth = True
    gold, orb = Hm.Hi(), Hm.Hi()
    centre, axis = V((0, 18.0, -9.2)), V((0, 0.8, -0.6)).normalized()
    _, s, u = G.frame(axis)
    ring = []
    for i in range(56):
        a = TAU * i / 56
        out = (s * math.cos(a) + u * math.sin(a)).normalized()
        ring.append(G.surface_along(mane, centre, out, reach=14.0) + out * 0.5)
    # smoothed, so it lies over the locks as one hoop instead of following each of them
    for _ in range(16):
        ring = [(ring[i - 1] + ring[i] * 2 + ring[(i + 1) % len(ring)]) / 4 for i in range(len(ring))]
    P._ring(gold, ring, 0.42, sides=8)
    forward = V((0, -0.08, -1)).normalized()
    low_front = min(ring, key=lambda q: q.y)
    front = low_front + V((0, -1.25, -0.25))
    G.sphere(orb, front, 0.82, nu=18, nv=12)
    P._band(gold, front + V((0, 0, 0.08)), forward, 0.9, 0.17)
    for side in (-1, 1):
        top = front + V((side * 0.8, -0.42, 0.06))
        Hm.htube(gold, [top, top + V((side * 0.15, -0.8, -0.1)), top + V((side * 0.2, -1.45, -0.08))], lambda q: 0.2 * (1 - 0.2 * q), sides=7, per=3, uv_scale=1.0, tip=False, wobble=0.0)
        G.sphere(gold, top + V((side * 0.2, -1.6, -0.08)), 0.33, nu=10, nv=8)
        for k in range(5):
            b = top + V((side * 0.2, -1.72, -0.08))
            a = TAU * k / 5
            Hm.htube(gold, [b, b + V((0.17 * math.cos(a), -1.05, 0.17 * math.sin(a)))], lambda q: 0.13 * (1 - 0.45 * q), sides=5, per=2, uv_scale=1.0, tip=True, wobble=0.0)

    pieces = {
        "Skin": [skin, tuft.object("LN2_TuftHi", coll, [M["granite"]]), palate, kept(lids, "LN2_Lids", M["nose"]), kept(lines, "LN2_Lines", M["nose"]), kept(nose, "LN2_Nose", M["nose"]), kept(teeth, "LN2_Teeth", M["ivory"]), kept(claws, "LN2_Claws", M["claw"])],
        "Jaw": [jaw, gum, kept(tongue, "LN2_Tongue", M["tongue"]), kept(jaw_teeth, "LN2_JawTeeth", M["ivory"])],
        "Mane": [mane],
        "Collar": [kept(gold, "LN2_Gold", M["gold"])],     # its own piece: a rigid hoop on the neck, and its gold can't bake onto the mane under it
    }
    glows = {
        "Eyes": (eyes.object("LN2_Eyes", coll, [K.glow_material(EYE_HEX)], smooth=True), EYE_HEX),
        "Pupils": (pupils.object("LN2_Pupils", coll, [K.glow_material(PUPIL_HEX)], smooth=True), PUPIL_HEX),
        "Orb": (orb.object("LN2_Orb", coll, [K.glow_material(ORB_HEX)], smooth=True), ORB_HEX),
    }
    for o, _ in glows.values():
        P._clean(o, triangulate=True)
        P._fit_uv(o)
    build_skeleton(coll)
    return pieces, glows


def make_lows(pieces):
    import egg_bake as B
    coll = bpy.data.collections[COLLECTION]
    lows = {}
    for name, hi in pieces.items():
        low = B.make_low(PREFIX + name, hi, coll, PIECES[name])
        low.name = PREFIX + name
        if name == "Mane":
            # the reduction leaves slivers along the locks, which shade and bake as dark torn patches: a little smoothing lays them down
            Hm.apply_modifiers(low, [("SMOOTH", {"factor": 0.5, "iterations": 2})])
        P._clean(low)
        lows[name] = low
    return lows


def bake_piece(name, hi, low):
    import egg_bake as B
    bpy.context.scene.cycles.device = "GPU"
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    try:
        B.bake(PREFIX + name, hi, low, samples=12, **BAKES[name])
    finally:
        B.EGG_DIR = saved


GAME_NAMES = {PREFIX + "Skin": "Skin", PREFIX + "Jaw": "Jaw", PREFIX + "Mane": "Mane", PREFIX + "Collar": "Collar", "LN2_Eyes": "Eyes", "LN2_Pupils": "Pupils", "LN2_Orb": "Orb"}


def rig_all():
    O = bpy.data.objects
    out = {"skin": bind_skin(O[PREFIX + "Skin"]), "mane": _bind_mane(O[PREFIX + "Mane"])}
    bind_rigid(O[PREFIX + "Jaw"], "Jaw")
    bind_rigid(O["LN2_Eyes"], "Eyes")
    bind_rigid(O["LN2_Pupils"], "Eyes")
    bind_rigid(O[PREFIX + "Collar"], "Neck1")
    bind_rigid(O["LN2_Orb"], "Neck1")
    game = set(GAME_NAMES) | {RIG}
    for o in O:
        if o.type == "MESH" and o.name not in game:
            o.hide_render = True
            o.hide_viewport = True
    return out


def tally():
    return {GAME_NAMES[o.name]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.name in GAME_NAMES}


def export():
    """assets/guardians/StoneLionV2.fbx: every game piece, skinned, and the skeleton, bound as modelled, the maps inside."""
    O = bpy.data.objects
    set_pose({})
    arm = O[RIG]
    arm.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    for src in GAME_NAMES:
        O[src].hide_viewport = False
        O[src].select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    for src, name in list(GAME_NAMES.items()):
        O[src].name = name
    path = os.path.join(OUT, "StoneLionV2.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X")
    return path, os.path.getsize(path) // 1024


# ---------- what the game plays: generated, never edited by hand ----------
_near = P._near
_continuous = P._continuous
_lua = P._lua


def _joints():
    return [n for n in BONES if n not in ("Root", "Eyes")]


def _vals(pose, shift, base):
    out = {}
    for n in _joints():
        out[n] = list(_continuous(pose.get(n, (0, 0, 0)), base.get(n, (0, 0, 0))[:3]))
    out["Hips"] = out["Hips"] + [shift[1], shift[2]]
    return out


STEPS = 32
MOVES_FPS = 30


def _planted(keys):
    """For each frame of a move, which paws are on the ground: a leg lets go of the ground only when its key lifts it."""
    length = keys[-1]["at"]
    rows = {leg: [] for leg in LEGS}
    for f in range(int(length * MOVES_FPS) + 1):
        t = min(f / MOVES_FPS, length)
        if t >= keys[-1]["at"]:
            a = b = keys[-1]
        else:
            for i in range(len(keys) - 1):
                a, b = keys[i], keys[i + 1]
                if t <= b["at"]:
                    break
        for leg in LEGS:
            ya = a["feet"].get(leg, (0, 0, 0, 0, 0))[1]
            yb = b["feet"].get(leg, (0, 0, 0, 0, 0))[1]
            rows[leg].append(0 if max(ya, yb) > 0.05 else 1)
    return rows


def anchors():
    cl = clips()
    out = {}
    pose, shift = clip_pose(0.75, cl["Slam"])
    st = fk(pose, shift)
    p = st["FrontLeftToes"][1]
    out["Slam"] = (round(p.x, 1), 0.3, round(p.z - 1.0, 1))
    pose, shift = clip_pose(1.13, cl["Roar"])
    st = fk(pose, shift)
    r, a = st["Head"]
    p = a + r @ (V((0, 20.1, -23.2)) - V(BONES["Head"][1]))
    out["Roar"] = (round(p.x, 1), round(p.y, 1), round(p.z, 1))
    return out


def write_clips(path=None):
    path = path or os.path.join(W.REPO, "src", "client", "Guardians", "GuardianRigs", "StoneLionClips.lua")
    stand, s0, states = state_poses()
    base = {n: stand.get(n, (0, 0, 0)) for n in _joints()}
    lines = ["-- Generated by tools/blender/guardians/stone_lion_v2.py (write_clips): do not edit by hand. Angles in degrees, [pitch, yaw, roll];",
             "-- the hips also carry [lift, slide]. Poses and Moves are whole poses; Gaits are changes from how it stands.", "local Clips = {}",
             "Clips.Fps = %d" % MOVES_FPS, "Clips.Steps = %d" % STEPS, "Clips.Anchors = " + _lua({k: list(v) for k, v in anchors().items()}),
             "Clips.Strides = " + _lua({n: stride_of(g) for n, g in GAITS.items()}), "Clips.Duty = " + _lua({n: g["duty"] for n, g in GAITS.items()}),
             "Clips.Phase = " + _lua({n: dict(g["phase"]) for n, g in GAITS.items()})]
    lines.append("Clips.Poses = {")
    for name, (pose, shift) in states.items():
        lines.append(name + "=" + _lua(_vals(pose, shift, base)) + ",")
    lines.append("}")
    standv = _vals(stand, s0, base)
    # (not written: the game never reads the standing pose; it is the Guardian pose, and the gaits are measured from it)
    lines.append("Clips.Gaits = {")
    for name in GAITS:
        table = {n: [] for n in _joints()}
        prev = base
        for f in range(STEPS):
            pose, shift = gait_pose(name, f / STEPS)
            v = _vals(pose, shift, prev)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            for n in _joints():
                table[n].append([v[n][k] - standv[n][k] for k in range(len(v[n]))])
        keep = {n: t for n, t in table.items() if any(abs(x) > 0.3 for row in t for x in row)}
        lines.append(name + "=" + _lua(keep) + ",")
    lines.append("}")
    cl = clips()
    lines.append("Clips.Moves = {")
    worst = {}
    for name, keys in cl.items():
        frames, prev = [], base
        length = keys[-1]["at"]
        for f in range(int(length * MOVES_FPS) + 1):
            pose, shift = clip_pose(min(f / MOVES_FPS, length), keys)
            v = _vals(pose, shift, prev)
            for n in _joints():
                d = max(abs(v[n][k] - prev[n][k]) for k in range(3))
                if f and d > worst.get(name, (0, ""))[0]:
                    worst[name] = (round(d, 1), n, f)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            frames.append(v)
        moved = [n for n in _joints() if any(abs(fr[n][k] - frames[0][n][k]) > 0.2 for fr in frames for k in range(3)) or abs(frames[0][n][0] - standv[n][0]) > 0.2]
        lines.append(name + "=" + _lua([{n: fr[n] for n in moved} for fr in frames]) + ",")
    lines.append("}")
    lines.append("Clips.Plants = {")
    for name, keys in cl.items():
        lines.append(name + "=" + _lua(_planted(keys)) + ",")
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    return {"bytes": os.path.getsize(path), "biggest step": worst, "anchors": anchors()}


def write_placement(path=None):
    """Placements/StoneLionSkinned.lua: how the store step fits the import, and the bones the importer drops, from the rest pose."""
    path = path or os.path.join(W.REPO, "src", "worldbuild", "Placements", "StoneLionSkinned.lua")
    fit = {"Hips": BONES["Hips"][1], "Head": BONES["Head"][1], "BackLeftThigh": BONES["BackLeftThigh"][1], "FrontRightLower": BONES["FrontRightLower"][1]}
    data = bpy.data.armatures[RIG] if RIG in bpy.data.armatures else bpy.data.objects[RIG].data
    D = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, -1)))
    add = []
    for name in ("Jaw", "Eyes"):
        bone = data.bones[name]
        local = bone.parent.matrix_local.inverted() @ bone.matrix_local
        r = D @ local.to_3x3() @ D
        p_ = D @ local.to_translation()
        numbers = [p_.x, p_.y, p_.z] + [r[i][j] for i in range(3) for j in range(3)]
        add.append("        %s = { Parent = \"%s\", CFrame = CFrame.new(%s) }," % (name, bone.parent.name, ", ".join("%.6g" % n for n in numbers)))
    vec = lambda v: "Vector3.new(%s)" % ", ".join("%.4g" % c for c in v)
    text = ["-- The Awakened Stone Lion with a skeleton (tools/blender/guardians/stone_lion_v2.py writes this file, assets/guardians/StoneLionV2.fbx). Used by",
            "-- GuardianBuilder.storeSkinned. The importer drops a bone that only single-bone pieces use: these go back on the same bind.", "return {", "    Rig = \"StoneLionSkinned\",", "    Fit = {"]
    for k, v in fit.items():
        text.append("        %s = %s," % (k, vec(v)))
    text += ["    },", "    AddBones = {"] + add + ["    },", "    Glow = {", "        Eyes = Color3.fromRGB(0, 110, 255),", "        Pupils = Color3.fromRGB(6, 16, 28),", "        Orb = Color3.fromRGB(0, 160, 95),", "    },", "}", ""]
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(text))
    return path

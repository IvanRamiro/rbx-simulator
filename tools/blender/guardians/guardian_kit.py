"""Shared building blocks for the guardians (run inside Blender): shapes authored in Roblox studs
(x right, y up, the guardian's front toward -Z, its feet on the ground at y = 0), the bake of each
segment onto its own game mesh, and the FBX with its pieces report.

A guardian is built from rigid segments that the game turns with Motor6D joints; each segment's
high-detail objects are baked onto one game mesh (egg_bake.py), its glowing parts are separate
Neon pieces named <Guardian>_<Segment>_Glow_<hex>.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(W.REPO, "assets", "guardians")


# ---------- shapes ----------
def blob(name, coll, mat, lobes, voxel=0.12, smooth=0.6, rough=0.05, chisel="LionChisel"):
    """A solid mass: ellipsoid lobes [(centre, radii, rotation degrees or None)], merged by a voxel
    remesh, smoothed, and roughened by a Voronoi displacement (`chisel` names its texture)."""
    bm = bmesh.new()
    for centre, radii, rot in lobes:
        made = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        r = Euler([math.radians(a) for a in (rot or (0, 0, 0))]).to_matrix()
        for v in made["verts"]:
            p = V((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
            p = r @ p
            v.co = W.rb(centre[0] + p.x, centre[1] + p.y, centre[2] + p.z)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    tex = bpy.data.textures.get(chisel) or bpy.data.textures.new(chisel, "VORONOI")
    tex.noise_scale = 0.9
    Hm.apply_modifiers(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel}),
                           ("SMOOTH", {"factor": smooth, "iterations": 6}),
                           ("DISPLACE", {"texture": tex, "strength": rough, "mid_level": 0.5, "texture_coords": "GLOBAL"})])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def capsule_lobes(a, b, r0, r1, n=5):
    """Ellipsoid lobes along a limb from a to b, its radius going from r0 to r1."""
    a, b = V(a), V(b)
    out = []
    for i in range(n):
        t = i / (n - 1)
        c = a.lerp(b, t)
        r = r0 + (r1 - r0) * t
        out.append((tuple(c), (r, r * 1.25, r), None))
    return out


def surface_down(obj, x, z, from_y=40.0):
    """Where a ray straight down at (x, z) meets obj, and the surface normal there (Roblox space)."""
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    hit, normal, _, _ = tree.ray_cast(W.rb(x, from_y, z), V((0, 0, -1)))
    if hit is None:
        return None, None
    return V(K.rb_inv(*hit)), V(K.rb_inv(*normal))


def frame(normal):
    n = V(normal).normalized()
    ref = V((0, 1, 0)) if abs(n.y) < 0.9 else V((1, 0, 0))
    s = n.cross(ref).normalized()
    return n, s, n.cross(s).normalized()


def curl(hi, centre, normal, radius, turns=1.6, thick=0.22, spin=1, phase=0.0):
    """A carved spiral curl lying on a surface: a tube winding in from `radius`, standing proud."""
    n, s, t = frame(normal)
    c = V(centre)
    pts = []
    steps = 28
    for i in range(steps + 1):
        k = i / steps
        a = phase + spin * TAU * turns * k
        r = radius * (1 - 0.82 * k)
        pts.append(c + (s * math.cos(a) + t * math.sin(a)) * r + n * thick * 0.6 * (1 - 0.4 * k))
    Hm.htube(hi, pts, lambda k: thick * (1 - 0.55 * k), sides=7, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def on_ellipsoid(centre, radii, u, v):
    """A point on an ellipsoid (u round from the front -Z, v from the bottom 0 to the top 1) and its
    outward normal."""
    a, th = TAU * u, math.pi * v
    d = V((math.sin(th) * math.sin(a), -math.cos(th), -math.sin(th) * math.cos(a)))
    p = V(centre) + V((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
    n = V((d.x / radii[0], d.y / radii[1], d.z / radii[2])).normalized()
    return p, n


def cone(hi, base, tip, r, sides=8):
    base, tip = V(base), V(tip)
    n, s, t = frame(tip - base)
    ring = [hi.v(base + (s * math.cos(TAU * i / sides) + t * math.sin(TAU * i / sides)) * r) for i in range(sides)]
    top = hi.v(tip)
    for i in range(sides):
        out = (s * math.cos(TAU * (i + 0.5) / sides) + t * math.sin(TAU * (i + 0.5) / sides))
        hi.facing([ring[i], ring[(i + 1) % sides], top], [(0, 0), (1, 0), (0.5, 1)], tuple(out), 0)


def sphere(hi, centre, r, nu=16, nv=10, radii=None, mat=0):
    """A sphere (or an ellipsoid with `radii`) with UVs round (u) and up (v)."""
    c = V(centre)
    rx, ry, rz = radii or (r, r, r)
    dirs = [[V((math.sin(math.pi * j / nv) * math.cos(TAU * i / nu), -math.cos(math.pi * j / nv), math.sin(math.pi * j / nv) * math.sin(TAU * i / nu)))
             for i in range(nu + 1)] for j in range(nv + 1)]
    rows = [[hi.v(c + V((d.x * rx, d.y * ry, d.z * rz))) for d in row] for row in dirs]
    for j in range(nv):
        for i in range(nu):
            out = dirs[j][i] + dirs[j][i + 1] + dirs[j + 1][i + 1] + dirs[j + 1][i]
            hi.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]],
                      [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)], tuple(out), mat)


# ---------- bake and export ----------
def bake_piece(guardian, piece, hi, coll, budget):
    """Bakes a piece's high-detail objects onto its game mesh <guardian>_<piece>, with its maps in
    assets/guardians/."""
    name = guardian + "_" + piece
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(name, hi, coll, budget)
    low.name = name
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        B.bake(name, hi, low, size=1024, small=256)
    finally:
        B.EGG_DIR = saved
    return low


def centre_of(obj):
    pts = [V(K.rb_inv(*(obj.matrix_world @ v.co))) for v in obj.data.vertices]
    lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
    hi = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
    return [round(c, 4) for c in (lo + hi) / 2]


def write_fbx(guardian, parts, report):
    """One FBX of every segment's game mesh and glow piece, and the pieces' centres and pivots."""
    path = os.path.join(OUT_DIR, guardian + ".fbx")
    W.export_batch(parts, path)
    with open(os.path.join(OUT_DIR, guardian + "_pieces.json"), "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    return path


def export(guardian, pivots, parts_map):
    """The FBX and its report from parts_map {piece: (segment, low object name)} and the guardian's
    glow pieces (<guardian>_<Segment>_Glow_<hex>)."""
    parts, report = [], {"Pieces": {}, "Pivots": {}}
    for piece, (segment, low) in sorted(parts_map.items()):
        obj = bpy.data.objects[low]
        parts.append(obj)
        report["Pieces"][piece] = {"Segment": segment, "Centre": centre_of(obj)}
    for o in bpy.data.objects:
        if o.name.startswith(guardian + "_") and "_Glow_" in o.name:
            parts.append(o)
            segment = o.name[len(guardian) + 1:].split("_Glow_")[0]
            report["Pieces"][o.name[len(guardian) + 1:]] = {"Segment": segment, "Centre": centre_of(o), "Hex": o.name.rsplit("_", 1)[1]}
    for segment, (parent, pos) in pivots.items():
        report["Pivots"][segment] = {"Parent": parent, "Position": list(pos)}
    return write_fbx(guardian, parts, report), report

"""Floating magma fragments for the Inferno Egg's aura (run inside Blender), built like the eggs:
high-detail volcanic rock baked (egg_bake) onto one game mesh, then split back into one mesh per
fragment, all wearing the same baked maps.

Each fragment is an irregular rock with its own silhouette (a slab, a shard, a wedge, a chunk, a
splinter, a cinder), roughened with noise and cut into plates: the faces nearest each of a few
sites on its surface. Every plate is shrunk toward its middle and given thickness, so seams open
between them, and a core of lava inside shows through the seams. The plates wear the eggs'
obsidian shader (its own dark tone per plate, molten veins, red-hot crevices); the core becomes a
Neon part in the game, so the cracks really glow.

    import inferno_fragments as F
    F.export()   # assets/eggs/InfernoFragments.fbx (+ _color, _normal, _roughness, _metalness):
                 # Fragment1..6 and Fragment<k>_Glow_ff5a14

Sizes are studs (1 Blender unit = 1 stud).
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eggs"))
import egg_bake as B  # noqa: E402
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402

W = K.W
NAME = "InfernoFragments"
LAVA = "ff5a14"
SPACING = 3.0          # fragments are built apart along X, then split by nearest centre

# size (studs), stretch (Roblox x, y, z), plates, seed: each its own silhouette
FRAGMENTS = [
    (0.50, (1.35, 0.55, 1.0), 4, 11),   # slab
    (0.42, (0.6, 1.55, 0.55), 3, 12),   # shard
    (0.55, (1.25, 0.9, 0.7), 4, 13),    # wedge
    (0.66, (1.0, 0.9, 1.05), 5, 14),    # chunk, the largest
    (0.36, (0.5, 1.35, 0.45), 3, 15),   # splinter
    (0.30, (0.95, 0.8, 0.9), 3, 16),    # cinder
]


def _hull(centre, size, stretch, seed, n=20):
    """Jittered points round a sphere, stretched, wrapped in their convex hull (Blender space)."""
    rnd = random.Random(seed)
    golden = math.pi * (3 - math.sqrt(5))
    bm = bmesh.new()
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        a = golden * i + rnd.uniform(-0.35, 0.35)
        d = Vector((math.cos(a) * r * stretch[0], y * stretch[1], math.sin(a) * r * stretch[2])) * size * rnd.uniform(0.72, 1.15)
        bm.verts.new(W.rb(centre.x + d.x, centre.y + d.y, centre.z + d.z))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    return bm


def _object(bm, name, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def _apply(o):
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data
    o.modifiers.clear()
    o.data = me
    bpy.data.meshes.remove(old)


def _rough(o, size, seed):
    """Subdivide the hull and push it about with noise: a broken, pitted rock surface."""
    sub = o.modifiers.new("Sub", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 2
    tex = bpy.data.textures.get("FragNoise%d" % seed) or bpy.data.textures.new("FragNoise%d" % seed, "VORONOI")
    tex.noise_scale = 0.14 * size + 0.03
    tex.distance_metric = "DISTANCE"
    disp = o.modifiers.new("Disp", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = "GLOBAL"
    disp.strength = 0.16 * size
    disp.mid_level = 0.6
    _apply(o)


def fragment(k, coll, mat_rock, mat_lava):
    size, stretch, n_plates, seed = FRAGMENTS[k]
    centre = Vector((k * SPACING, 0, 0))
    rock = _object(_hull(centre, size, stretch, seed), "Frag%d_Rock" % (k + 1), coll)
    _rough(rock, size, seed)
    # plate sites: spread over the surface (farthest-point picks from the face centres)
    me = rock.data
    centres = [p.center.copy() for p in me.polygons]
    rnd = random.Random(seed + 100)
    sites = [centres[rnd.randrange(len(centres))]]
    while len(sites) < n_plates:
        sites.append(max(centres, key=lambda c: min((c - s).length for s in sites)))
    owner = [min(range(len(sites)), key=lambda i: (c - sites[i]).length) for c in centres]
    plates = []
    for i in range(len(sites)):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if owner[f.index] != i], context="FACES")
        mid = sum((v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
        for v in bm.verts:             # shrunk toward its middle: a seam opens round it
            v.co = mid + (v.co - mid) * 0.87
        p = _object(bm, "Frag%d_Plate%d" % (k + 1, i + 1), coll)
        bm.free()
        sol = p.modifiers.new("Thick", "SOLIDIFY")
        sol.thickness = 0.22 * size
        sol.offset = -1
        _apply(p)
        p.data.materials.append(mat_rock)
        for poly in p.data.polygons:
            poly.use_smooth = True
        plates.append(p)
    me = rock.data
    bpy.data.objects.remove(rock, do_unlink=True)
    bpy.data.meshes.remove(me)
    # the lava core: the hull itself, smaller, unroughened
    core = _object(_hull(centre, size * 0.8, stretch, seed), "Fragment%d_Glow_%s" % (k + 1, LAVA), coll)
    core.data.materials.append(mat_lava)
    for poly in core.data.polygons:
        poly.use_smooth = False
    return plates, core


def build():
    coll = W.collection(NAME + "Hi")
    W.clear_collection(coll)
    mat_rock = Hm.mat_obsidian("FragmentObsidian", vein=(1.0, 0.3, 0.02), vein_hot=(1.0, 0.7, 0.15), heat=(0.55, 0.05, 0.01),
                                heat_reach=0.035)   # the egg's reach would heat every face of a rock this small
    mat_lava = K.glow_material(LAVA)
    plates, cores = [], []
    for k in range(len(FRAGMENTS)):
        p, c = fragment(k, coll, mat_rock, mat_lava)
        plates += p
        cores.append(c)
    return plates, cores, coll


def split(low, coll):
    """One game mesh per fragment, by nearest fragment centre; all keep the baked material."""
    out = []
    for k in range(len(FRAGMENTS)):
        bm = bmesh.new()
        bm.from_mesh(low.data)
        bm.faces.ensure_lookup_table()
        far = [f for f in bm.faces if round(f.calc_center_median().x / SPACING) != k]
        bmesh.ops.delete(bm, geom=far, context="FACES")
        me = bpy.data.meshes.new("Fragment%d" % (k + 1))
        bm.to_mesh(me)
        bm.free()
        me.materials.append(low.data.materials[0])
        o = bpy.data.objects.new("Fragment%d" % (k + 1), me)
        coll.objects.link(o)
        out.append(o)
    return out


def export(budget=4200, size=1024):
    plates, cores, coll = build()
    old = bpy.data.objects.get(NAME + "_Body")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(NAME, plates, coll, budget)
    B.bake(NAME, plates, low, size=size, extrusion=0.02, ray=0.06)
    bodies = split(low, coll)
    W.export_batch(bodies + cores, os.path.join(K.EGG_DIR, NAME + ".fbx"))
    return {o.name: B.tris(o) for o in bodies + cores}

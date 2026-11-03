"""The Skyrise Coronet: Realm 5's crown (the owner, 2026-11-03: "create an asset to blender for
crown"; it floats above the head, not on it, with bloom and a PointLight round it in the game).

Design (the modelling directive: idea first, then primary, secondary, tertiary forms):
  idea      the Ascendant rises like a swallow climbing the sky (the realm's Skyrise swallow, its
            ground seal of swallows and clouds): a coronet of swept swallow wings spiralling up.
  primary   six wing blades rising from a slim floating band, alternating tall and short, leaning
            outward and sweeping round in one direction: a turning, climbing silhouette. The tall
            blades end in a swallow's forked tail; the short ones in a single point.
  secondary each blade has a raised central vane; a small bead sits where each blade meets the
            band; the band is a lens in section, flared, with a ridge round its middle.
  tertiary  shallow chevron feather grooves on each blade.
Units are studs (1 Blender unit = 1 stud), Z up in Blender; the OBJ is written Y up for Studio.
One mesh, one material (the game makes it Neon gold).

    run inside Blender:  exec(open(".../tools/blender/auras/ascendant_crown.py").read())
    writes assets/aura/ascendant/AscendantCrown.obj
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = "/Users/ivan/qi-aura-simulator"
OUT = os.path.join(ROOT, "assets/aura/ascendant/AscendantCrown.obj")
COLL = "AscendantCrown"
TAU = math.tau

BAND_R = 0.72          # the band sits round, not on, a 1.2-stud head
BAND_H = 0.16
BLADES = 6
SWEEP = 1              # every blade sweeps the same way round: the crown reads as turning


def collection():
    old = bpy.data.collections.get(COLL)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    c = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(c)
    return c


def obj_from_bmesh(bm, name, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


# ---------------------------------------------------------------- the band ----------------
def band(coll):
    """a lens-section ring, flared a little at the top, with a ridge round its middle"""
    bm = bmesh.new()
    seg, prof = 72, 12
    rows = []
    for i in range(seg):
        a = i * TAU / seg
        ring = []
        for j in range(prof):
            t = j * TAU / prof
            # the section: height BAND_H, depth 0.07, a ridge on the outer face at mid height
            z = math.sin(t) * BAND_H / 2
            out = math.cos(t) * 0.035
            if math.cos(t) > 0:
                out += 0.018 * math.exp(-(math.sin(t) / 0.25) ** 2)       # the ridge
            r = BAND_R + out + 0.03 * (z / (BAND_H / 2))                    # flared to the top
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rows.append(ring)
    for i in range(seg):
        for j in range(prof):
            a, b = rows[i][j], rows[i][(j + 1) % prof]
            c, d = rows[(i + 1) % seg][(j + 1) % prof], rows[(i + 1) % seg][j]
            bm.faces.new((a, b, c, d))
    return obj_from_bmesh(bm, "Band", coll)


# ---------------------------------------------------------------- the blades --------------
def blade(coll, k, tall):
    """a swept swallow wing, built as a grid (u across, v along) and bent onto its path. Its outline
    is a wing's, not a leaf's: a smooth curved leading edge, a trailing edge scalloped into feather
    tips, a raised arm along the leading edge, sweeping back to a point"""
    H = 1.15 if tall else 0.75
    W = 0.30 if tall else 0.24
    base_a = k * TAU / BLADES
    nu, nv = 12, 36
    feathers = 5 if tall else 4

    def lead(v):
        # the leading edge: swells early, then sweeps smoothly to the tip
        return W * 0.42 * math.sin(math.pi * min(0.985, 0.16 + 0.84 * v ** 0.75)) ** 0.8 + 0.004

    def trail(v):
        # the trailing edge: broad, cut into feather tips, narrowing to the point
        body = math.sin(math.pi * min(0.985, 0.14 + 0.86 * v ** 1.05)) ** 0.6
        scallop = 0.72 + 0.28 * abs(math.cos(v * feathers * math.pi)) ** 0.6
        return W * 0.58 * body * scallop + 0.004

    def path(v):
        """the centreline: rising nearly upright, leaning out a little, sweeping round"""
        r = BAND_R + 0.02 + 0.2 * v ** 1.5
        a = base_a + SWEEP * 0.55 * v ** 1.8
        z = -0.03 + (BAND_H / 2 + H) * v
        return Vector((r * math.cos(a), r * math.sin(a), z)), a

    def point(u, v):
        p, a = path(v)
        e = 1e-3
        p2, _ = path(min(1, v + e))
        p1, _ = path(max(0, v - e))
        along = (p2 - p1).normalized()
        across = Vector((-math.sin(a), math.cos(a), 0)) * SWEEP          # + is the leading side
        normal = along.cross(across).normalized()
        if normal.dot(Vector((math.cos(a), math.sin(a), 0))) < 0:
            normal = -normal
        x = u * lead(v) if u >= 0 else u * trail(v)
        # the arm: a raised ridge along the leading side; feather lines raking back from it
        arm_x = lead(v) * 0.35
        arm = 0.032 * math.exp(-((x - arm_x) / 0.03) ** 2) * (1 - v ** 2.5)
        rake = 0.0
        if x < arm_x:
            f = (v * feathers * 2 + (arm_x - x) / max(W, 1e-3) * 1.6) % 1.0
            rake = -0.005 * math.exp(-((f - 0.5) / 0.12) ** 2)
        return p + across * x + normal * (arm + rake)

    bm = bmesh.new()
    grid = []
    for j in range(nv + 1):
        v = j / nv
        grid.append([bm.verts.new(point(-1 + 2 * i / nu, v)) for i in range(nu + 1)])
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    o = obj_from_bmesh(bm, f"Blade{k}", coll)
    sol = o.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.035
    sol.offset = 0
    sol.use_even_offset = False
    return o


def bead(coll, k):
    """a small faceted bead where each blade meets the band"""
    a = k * TAU / BLADES
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.045)
    o = obj_from_bmesh(bm, f"Bead{k}", coll)
    o.location = ((BAND_R + 0.05) * math.cos(a), (BAND_R + 0.05) * math.sin(a), 0.0)
    o.scale = (1, 1, 1.3)
    return o


def build():
    coll = collection()
    parts = [band(coll)]
    for k in range(BLADES):
        parts.append(blade(coll, k, tall=(k % 2 == 0)))
        parts.append(bead(coll, k))
    # one mesh: apply modifiers and transforms, join
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    for o in parts:
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    crown = bpy.context.view_layer.objects.active
    crown.name = "AscendantCrown"
    bpy.ops.object.shade_smooth()
    # a neutral clay material for the form review
    mat = bpy.data.materials.get("CrownClay") or bpy.data.materials.new("CrownClay")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    crown.data.materials.clear()
    crown.data.materials.append(mat)
    tris = sum(len(p.vertices) - 2 for p in crown.data.polygons)
    dims = crown.dimensions
    print(f"AscendantCrown: {tris} triangles, {len(crown.data.vertices)} vertices, size {dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} studs")
    return crown


def export(crown):
    bpy.ops.object.select_all(action="DESELECT")
    crown.select_set(True)
    bpy.context.view_layer.objects.active = crown
    bpy.ops.wm.obj_export(filepath=OUT, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                          export_materials=False, export_uv=True, export_normals=True, apply_modifiers=True)
    print("written", OUT)


crown = build()

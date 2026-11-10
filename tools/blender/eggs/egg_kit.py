"""The few helpers the egg, guardian, weapon, outfit and bridge scripts share (run inside Blender):
the egg's size (H, R), rb_inv, the Neon glow materials (glow_material: an object wearing one becomes
a Neon part named by its colour) and join. The eggs themselves are built by egg_forge.py into
assets/eggs/.
"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "world"))
import worldlib as W  # noqa: E402

TAU = 2 * math.pi
REPO = W.REPO


def rb_inv(x, y, z):
    """Blender space -> Roblox space (the inverse of worldlib.rb)."""
    return (x, z, -y)


H = 2.7    # egg height
R = 1.02   # egg radius at its widest


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------- export ----------
def glow_material(hexstr):
    """A flat emissive material named by its colour; objects using it become the egg's Neon parts."""
    name = "EggGlow_" + hexstr
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    for nd in list(t.nodes):
        t.nodes.remove(nd)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*[c ** 2.2 for c in rgb(hexstr)], 1)
    em.inputs["Strength"].default_value = 3.0
    t.links.new(em.outputs[0], out.inputs[0])
    m["glow"] = hexstr
    return m


def join(objects, name, coll):
    """Merge objects into one mesh object called name."""
    bm = bmesh.new()
    mats = []
    for o in objects:
        me = o.data.copy()
        me.transform(o.matrix_world)
        offset = len(mats)
        mats.extend(me.materials)
        for p in me.polygons:
            p.material_index += offset
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)   # zero-area faces at points and poles
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats[:1]:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o

"""The hub's finish pass (2026-11-12, the owner's quality brief: "I just want to make it feel realistic").

The hub's generators paint every face from one flat colour atlas, which read as plastic. Here each piece is split by the
atlas strip its faces use into one mesh per material (HB_Market__Marble, HB_Market__Gold, ...); in the game each takes a real
Roblox material (WorldBuilder.MaterialLooks: Marble, Metal gold, blue Marble lapis, Slate, Glass, Neon), so no texture is
uploaded. Each split mesh is welded, its square edges given a small chamfer that catches the light, curved surfaces smoothed
(weighted normals keep big flat faces flat).
"""
import math

import bpy
import bmesh

import hub_celestial as H

# atlas strip -> the material suffix the game reads (Shade: the darker marble of grout lines and undersides)
SUFFIX = {H.MARBLE: "Marble", H.SHADE: "Shade", H.MARBLE2: "Marble", H.LAPIS: "Lapis", H.GOLD: "Gold",
          H.CRYSTAL: "Crystal", H.GLOW: "Glow", H.SLATE: "Slate", H.STEEL: "Steel"}
SMOOTH_ANGLE = math.radians(62)   # a 6-sided tube's edges (60 degrees) smooth out; a box's (90) stay crisp
BEVEL_ANGLE = math.radians(75)
BEVEL = 0.05                      # studs


def _band_of(v, bands):
    for k, (v0, v1) in bands.items():
        lo, hi = min(v0, v1), max(v0, v1)
        if lo - 1e-4 <= v <= hi + 1e-4:
            return k
    raise ValueError("uv v %.4f in no band" % v)


def split(obj, bands, coll):
    """obj -> [new objects], one per material suffix, named <obj>__<Suffix>. obj is removed."""
    me = obj.data
    uv = me.uv_layers.active.data
    groups = {}
    for p in me.polygons:
        k = _band_of(uv[p.loop_indices[0]].uv[1], bands)
        groups.setdefault(SUFFIX[k], []).append(p.index)
    out = []
    for suffix, polys in sorted(groups.items()):
        bm = bmesh.new()
        bm.from_mesh(me)
        keep = set(polys)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
        if suffix not in ("Glow", "Crystal"):    # (glow is Neon: no shading to catch; crystals keep their facets)
            bm.edges.ensure_lookup_table()
            sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) >= BEVEL_ANGLE]
            if sharp:
                bmesh.ops.bevel(bm, geom=sharp, offset=BEVEL, segments=1, profile=0.5, affect="EDGES", clamp_overlap=True)
        new = bpy.data.meshes.new(obj.name + "__" + suffix)
        bm.to_mesh(new)
        bm.free()
        for p in new.polygons:
            p.use_smooth = suffix != "Crystal"
        if suffix != "Crystal":
            new.set_sharp_from_angle(angle=SMOOTH_ANGLE)
        o = bpy.data.objects.new(new.name, new)
        coll.objects.link(o)
        if suffix not in ("Glow", "Crystal"):
            m = o.modifiers.new("Weighted", "WEIGHTED_NORMAL")
            m.mode = "FACE_AREA"
            m.keep_sharp = True
        out.append(o)
    bpy.data.objects.remove(obj, do_unlink=True)
    return out


def finish(objs, bands, coll):
    out = []
    for o in objs:
        out += split(o, bands, coll)
    return out


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# ---------- preview look (renders only: roughly what each Roblox material reads as) ----------
def _mat(name, base, rough, metal=0.0, veins=None, emit=None, alpha=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if veins:
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.inputs["Scale"].default_value = veins[0]
        tex.inputs["Distortion"].default_value = 9.0
        tex.inputs["Detail"].default_value = 6.0
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.55
        ramp.color_ramp.elements[0].color = base
        ramp.color_ramp.elements[1].color = veins[1]
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = base
    if emit:
        b.inputs["Emission Color"].default_value = emit[0]
        b.inputs["Emission Strength"].default_value = emit[1]
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


def preview_materials(objs, core=("HB_BlacksmithCore",)):
    looks = {
        "Marble": _mat("pv_marble", (0.86, 0.85, 0.83, 1), 0.3, veins=(1.1, (0.74, 0.75, 0.77, 1))),
        "Shade": _mat("pv_shade", (0.62, 0.62, 0.62, 1), 0.4, veins=(1.1, (0.52, 0.53, 0.55, 1))),
        "Lapis": _mat("pv_lapis", (0.03, 0.06, 0.26, 1), 0.3, veins=(1.4, (0.1, 0.17, 0.45, 1))),
        "Gold": _mat("pv_gold", (0.85, 0.6, 0.2, 1), 0.32, metal=1.0),
        "Slate": _mat("pv_slate", (0.06, 0.065, 0.08, 1), 0.7),
        "Steel": _mat("pv_steel", (0.62, 0.64, 0.68, 1), 0.3, metal=1.0),
        "Crystal": _mat("pv_crystal", (0.6, 0.82, 1.0, 1), 0.05, alpha=0.55),
        "Glow": _mat("pv_glow", (0.75, 0.84, 0.95, 1), 0.2, emit=((0.8, 0.9, 1.0, 1), 0.6)),
        "Core": _mat("pv_core", (1.0, 0.45, 0.1, 1), 0.2, emit=((1.0, 0.45, 0.1, 1), 4.0)),
    }
    for o in objs:
        base, _, suffix = o.name.partition("__")
        look = looks["Core"] if base in core else looks.get(suffix)
        if look:
            o.data.materials.clear()
            o.data.materials.append(look)

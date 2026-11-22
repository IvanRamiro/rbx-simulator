"""hq_blender: Blender-side helpers for the headquarters kit (headless only; never the open Blender window).

Turns hq_kit Pieces into Blender objects (named <Piece>__<Material>, authored in Roblox studs through worldlib.rb, one box-projected UV chart set per
mesh, smooth with a sharp-angle split), builds the whole compound from the placements (linked copies share their mesh), and offers the review
tools: clay and material renders from any side, a black silhouette, a night render, the QA call, the FBX export (anchor cube, machine path scrub).
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import worldlib as W  # noqa: E402

TILE = 8.0

# preview colours (sRGB 0-255, roughness, metallic, emission): roughly what the game's material will read as
PREVIEW = {
    "Marble": ((238, 236, 232), 0.28, 0.0, None, None), "Granite": ((176, 176, 184), 0.55, 0.0, None, None),
    "Tile": ((26, 46, 118), 0.3, 0.0, None, None), "Gold": ((255, 172, 48), 0.32, 1.0, None, None),
    "GoldFlat": ((226, 176, 70), 0.45, 0.0, None, None), "Azure": ((38, 104, 204), 0.4, 0.0, None, None),
    "Plaster": ((236, 230, 220), 0.7, 0.0, None, None), "Stone": ((196, 186, 170), 0.8, 0.0, None, None),
    "SilkBlue": ((28, 62, 170), 0.8, 0.0, None, None), "SilkWhite": ((240, 242, 250), 0.8, 0.0, None, None),
    "Crystal": ((130, 195, 255), 0.05, 0.0, None, 0.55), "AzureGlow": ((40, 150, 255), 0.2, 0.0, ((40, 150, 255), 6.0), None),
    "Pool": ((110, 190, 230), 0.05, 0.0, None, 0.6),
}


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def preview_material(suffix, glow=True):
    key = "hq_" + suffix + ("" if glow else "_off")
    m = bpy.data.materials.get(key)
    if m:
        return m
    (r, g, b), rough, metal, emit, alpha = PREVIEW[suffix]
    m = bpy.data.materials.new(key)
    col = (lin(r), lin(g), lin(b), 1.0)
    m.diffuse_color = col
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit and glow:
        bsdf.inputs["Emission Color"].default_value = (lin(emit[0][0]), lin(emit[0][1]), lin(emit[0][2]), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    if alpha is not None:
        bsdf.inputs["Alpha"].default_value = alpha
    return m


def clay_material():
    m = bpy.data.materials.get("hq_clay")
    if m:
        return m
    m = bpy.data.materials.new("hq_clay")
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.60, 0.57, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


def black_material():
    m = bpy.data.materials.get("hq_black")
    if m:
        return m
    m = bpy.data.materials.new("hq_black")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def uv_charts(bm):
    """Box-projected UVs, one tile per TILE studs: faces grouped into charts by projection axis and adjacency, each chart no larger than a tile and
    placed at the tile's origin (every UV inside 0-1)."""
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    axis = {}
    for f in bm.faces:
        n = f.normal
        axis[f.index] = max(range(3), key=lambda i: abs(n[i]))
    done = set()
    for f0 in bm.faces:
        if f0.index in done:
            continue
        ax = axis[f0.index]
        a, b = [i for i in range(3) if i != ax]
        chart, stack = [], [f0]
        lo = [min(v.co[a] for v in f0.verts), min(v.co[b] for v in f0.verts)]
        hi = [max(v.co[a] for v in f0.verts), max(v.co[b] for v in f0.verts)]
        done.add(f0.index)
        while stack:
            f = stack.pop()
            chart.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index in done or axis[g.index] != ax:
                        continue
                    nlo = [min(lo[0], min(v.co[a] for v in g.verts)), min(lo[1], min(v.co[b] for v in g.verts))]
                    nhi = [max(hi[0], max(v.co[a] for v in g.verts)), max(hi[1], max(v.co[b] for v in g.verts))]
                    if nhi[0] - nlo[0] > TILE or nhi[1] - nlo[1] > TILE:
                        continue
                    lo, hi = nlo, nhi
                    done.add(g.index)
                    stack.append(g)
        scale = max(TILE, hi[0] - lo[0], hi[1] - lo[1])
        for f in chart:
            for l in f.loops:
                l[uv].uv = ((l.vert.co[a] - lo[0]) / scale, (l.vert.co[b] - lo[1]) / scale)


def mesh_from_geo(name, geo, suffix, smooth_angle=40.0):
    bm = bmesh.new()
    vs = [bm.verts.new(W.rb(*p)) for p in geo.v]
    for f in geo.f:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    uv_charts(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    me.materials.append(preview_material(suffix))
    return me


def piece_objects(name, piece, coll, smooth_angle=40.0):
    """One object per material, named <name>__<suffix>, at the origin."""
    out = []
    for suffix, geo in sorted(piece.g.items()):
        if not geo.f:
            continue
        me = mesh_from_geo("%s__%s" % (name, suffix), geo, suffix, smooth_angle)
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        out.append(o)
    return out


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


# ----------------------------------------------------------------------------------------------------------------------
# the whole compound
# ----------------------------------------------------------------------------------------------------------------------
def build_compound(data, coll):
    """Every placement as an object (linked copies share their mesh), in the pad frame (Roblox -> Blender by rb). Returns {piece name: [objects of the
    first copy]} and the list of all objects."""
    first = {}
    objs = []
    meshes = {}
    for p in data["placements"]:
        piece = data["pieces"][p["piece"]]
        for suffix, geo in sorted(piece.g.items()):
            key = (p["piece"], suffix)
            if key not in meshes:
                meshes[key] = mesh_from_geo("%s__%s" % key, geo, suffix)
            o = bpy.data.objects.new("%s__%s" % key, meshes[key])
            o.location = W.rb(p["x"], p["y"], p["z"])
            o.rotation_euler = (0.0, 0.0, p["yaw"])
            if p["scale"] != 1.0:
                o.scale = (p["scale"],) * 3
            coll.objects.link(o)
            objs.append(o)
            first.setdefault(p["piece"], []).append(o)
    return first, objs


def set_material_mode(objs, mode, glow=True):
    """mode: clay (one neutral material), paint (the preview colours) or black (a flat black silhouette)."""
    for o in objs:
        suffix = o.name.partition("__")[2].split(".")[0]
        o.data.materials.clear()
        if mode == "clay":
            o.data.materials.append(clay_material())
        elif mode == "black":
            o.data.materials.append(black_material())
        else:
            o.data.materials.append(preview_material(suffix, glow))


# ----------------------------------------------------------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------------------------------------------------------
def setup_render(res=(1280, 800), samples=24):
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    try:
        scene.eevee.taa_render_samples = samples
    except AttributeError:
        pass
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    return scene


def set_world(color=(0.42, 0.43, 0.46), strength=0.9):
    scene = bpy.context.scene
    world = bpy.data.worlds.get("HQWorld") or bpy.data.worlds.new("HQWorld")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (color[0], color[1], color[2], 1)
    bg.inputs["Strength"].default_value = strength


def set_sun(energy=3.4, rot=(50, 0, 35), color=(1, 1, 1)):
    sun = bpy.data.objects.get("HQSun")
    if not sun:
        sun = bpy.data.objects.new("HQSun", bpy.data.lights.new("HQSun", "SUN"))
        bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = energy
    sun.data.color = color
    sun.data.angle = math.radians(6)
    sun.rotation_euler = tuple(math.radians(a) for a in rot)


def add_camera(name, loc, target, lens=40.0, ortho=None):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    cam.data.clip_end = 2000
    cam.data.clip_start = 0.5
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def shoot(cam, path):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def rbv(x, y, z):
    return W.rb(x, y, z)


def clear_lights():
    for o in list(bpy.data.objects):
        if o.type == "LIGHT" and o.name != "HQSun":
            bpy.data.objects.remove(o, do_unlink=True)


# ----------------------------------------------------------------------------------------------------------------------
# QA and export
# ----------------------------------------------------------------------------------------------------------------------
def qa_module():
    path = os.environ.get("HQ_QA_SCRIPT")
    if not path:
        raise SystemExit("HQ_QA_SCRIPT must name the asset QA's qa_check.py")
    sys.path.insert(0, os.path.dirname(path))
    import qa_check
    return qa_check


def bbox_roblox(objs):
    pts = []
    for o in objs:
        pts += [o.matrix_world @ v.co for v in o.data.vertices]
    rb = [Vector((p.x, p.z, -p.y)) for p in pts]
    lo = [min(p[i] for p in rb) for i in range(3)]
    hi = [max(p[i] for p in rb) for i in range(3)]
    return [round(x, 3) for x in lo], [round(x, 3) for x in hi]


def scrub(path):
    """Machine paths in an exported file read /Users/user (same length: binary-safe); stale bytes after a shorter path are zeroed."""
    b = bytearray(open(path, "rb").read())
    home = os.path.expanduser("~").encode()
    if len(home) != len(b"/Users/user"):
        raise SystemExit("scrub: the home path is not the same length as /Users/user: fix by hand")
    i = b.find(home)
    while i != -1:
        b[i:i + len(home)] = b"/Users/user"
        j = i + len(home)
        while j < len(b) and b[j] != 0:
            j += 1
        k = j
        while k < len(b) and k - j < 1024 and b[k:k + 16] != b"\x00" * 16:
            b[k] = 0
            k += 1
        i = b.find(home, i + 1)
    open(path, "wb").write(bytes(b))

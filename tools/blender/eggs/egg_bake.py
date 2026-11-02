"""From a high-detail egg (egg_hi.py) to the game mesh (run inside Blender), as the sculpted pets
are made:

1. make_low: every high-detail piece decimated to share a triangle budget (thin sheets such as
   leaves and petals keep more of theirs), joined into one game mesh, unwrapped.
2. bake: colour (with the shaders' ambient occlusion), tangent-space normal, roughness and
   metalness, from the high-detail pieces onto the game mesh (Cycles, selected to active).
3. export: assets/eggs/<EggId>.fbx holding "<EggId>_Body" (the game mesh wearing the colour and
   normal maps, which Studio's importer turns into a SurfaceAppearance) and one
   "<EggId>_Glow_<rrggbb>" piece per glow colour (Neon in the game), plus <EggId>_color.png,
   _normal.png, _roughness.png and _metalness.png next to it (the last two are set on the
   SurfaceAppearance in Studio: the importer does not read them).
"""
import math
import os

import bpy

import egg_kit as K

W = K.W
EGG_DIR = K.EGG_DIR


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _copy(obj, name):
    me = obj.data.copy()
    me.transform(obj.matrix_world)
    o = bpy.data.objects.new(name, me)
    return o


def make_low(egg_id, hi_objects, coll, budget, sheet_ratio=0.55):
    """The game mesh: each piece decimated (pieces marked obj["keep"] are left whole; sheets,
    marked obj["sheet"], go to sheet_ratio; the rest share what is left of `budget`), joined and
    unwrapped."""
    kept = [o for o in hi_objects if o.get("keep")]
    sheets = [o for o in hi_objects if o.get("sheet") and not o.get("keep")]
    solids = [o for o in hi_objects if not o.get("sheet") and not o.get("keep")]
    fixed = sum(tris(o) for o in sheets) * sheet_ratio + sum(tris(o) for o in kept)
    solid_total = max(1, sum(tris(o) for o in solids))
    ratio = max(0.02, min(1.0, (budget - fixed) / solid_total))
    pieces = []
    for o in hi_objects:
        c = _copy(o, o.name + "_low")
        coll.objects.link(c)
        r = 1.0 if o.get("keep") else sheet_ratio if o.get("sheet") else ratio
        if r < 0.999:
            md = c.modifiers.new("Decimate", "DECIMATE")
            md.decimate_type = "COLLAPSE"
            md.ratio = r
            md.use_collapse_triangulate = True
            me = bpy.data.meshes.new_from_object(c.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            old = c.data
            c.modifiers.clear()
            c.data = me
            bpy.data.meshes.remove(old)
        pieces.append(c)
    low = K.join(pieces, egg_id + "_Body", coll)
    for c in pieces:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    me = low.data
    me.materials.clear()
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        p.use_smooth = True
    _unwrap(low)
    return low


def _ui_override(obj):
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=win, area=area, region=region, active_object=obj,
                                     selected_objects=[obj], selected_editable_objects=[obj], object=obj)


def _unwrap(obj):
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    view_layer.objects.active = obj
    with _ui_override(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002)
        try:
            bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
        except (RuntimeError, TypeError):
            bpy.ops.uv.pack_islands(margin=0.003)
        bpy.ops.object.mode_set(mode="OBJECT")


def _image(name, size, color):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, size, size, alpha=False)
    if not color:
        img.colorspace_settings.name = "Non-Color"
    return img


def _baked_material(egg_id, images):
    """The game mesh's material: its maps' image nodes, left unconnected while they are baked into
    (connected, they would read the images being written); wire_baked connects them."""
    m = bpy.data.materials.get(egg_id + "_Baked") or bpy.data.materials.new(egg_id + "_Baked")
    m.use_nodes = True
    t = m.node_tree
    for nd in list(t.nodes):
        t.nodes.remove(nd)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
    t.links.new(bsdf.outputs[0], out.inputs["Surface"])
    for key, img in images.items():
        nd = t.nodes.new("ShaderNodeTexImage")
        nd.image = img
        nd.name = key
    return m


def wire_baked(m):
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    t.links.new(t.nodes["color"].outputs["Color"], bsdf.inputs["Base Color"])
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(t.nodes["normal"].outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    t.links.new(t.nodes["roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    t.links.new(t.nodes["metalness"].outputs["Color"], bsdf.inputs["Metallic"])


def _route_value(materials, node_name):
    """Every material shows the value of its node `node_name` as emission (to bake it). Returns
    a function that puts the materials back."""
    undo = []
    for m in materials:
        t = m.node_tree
        out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
        old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        em = t.nodes.new("ShaderNodeEmission")
        src = t.nodes.get(node_name)
        if src is not None:
            t.links.new(src.outputs[0], em.inputs["Color"])
        else:
            em.inputs["Color"].default_value = (0, 0, 0, 1)
        t.links.new(em.outputs[0], out.inputs["Surface"])
        undo.append((t, out, old, em))

    def restore():
        for t, out, old, em in undo:
            t.nodes.remove(em)
            if old is not None:
                t.links.new(old, out.inputs["Surface"])
    return restore


def bake(egg_id, hi_objects, low, size=1024, small=512, samples=12, extrusion=0.035, ray=0.12):
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    images = {"color": _image(egg_id + "_Color", size, True), "normal": _image(egg_id + "_Normal", size, False),
              "roughness": _image(egg_id + "_Roughness", small, False), "metalness": _image(egg_id + "_Metalness", small, False)}
    mat = _baked_material(egg_id, images)
    low.data.materials.clear()
    low.data.materials.append(mat)
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    hi_mats = {m for o in hi_objects for m in o.data.materials if m}
    # the game mesh sits on the high-detail surface: hidden from rays while baking (the shaders'
    # ambient occlusion is local to each piece for the same reason, see egg_hi)
    rays = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow")
    saved_rays = {r: getattr(low, r) for r in rays}
    for r in rays:
        setattr(low, r, False)
    passes = [("color", "DIFFUSE", None), ("normal", "NORMAL", None), ("roughness", "EMIT", "BAKE_ROUGH"), ("metalness", "EMIT", "BAKE_METAL")]
    try:
        for key, kind, route in passes:
            mat.node_tree.nodes.active = mat.node_tree.nodes[key]
            restore = _route_value(hi_mats, route) if route else None
            bpy.ops.object.select_all(action="DESELECT")
            for o in hi_objects:
                o.select_set(True)
            low.select_set(True)
            view_layer.objects.active = low
            kw = dict(type=kind, use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=ray, margin=8,
                      use_clear=True, target="IMAGE_TEXTURES")
            if kind == "DIFFUSE":
                kw["pass_filter"] = {"COLOR"}
            if kind == "NORMAL":
                kw["normal_space"] = "TANGENT"
            try:
                bpy.ops.object.bake(**kw)
            finally:
                if restore:
                    restore()
    finally:
        scene.render.engine = engine
        for r, v in saved_rays.items():
            setattr(low, r, v)
    wire_baked(mat)
    os.makedirs(EGG_DIR, exist_ok=True)
    for key, img in images.items():
        img.filepath_raw = os.path.join(EGG_DIR, egg_id + "_" + key + ".png")
        img.file_format = "PNG"
        img.save()
    return images


def export(egg_id, low, glow_objects, coll):
    """assets/eggs/<EggId>.fbx: the baked body and one Neon piece per glow colour."""
    parts = [low]
    for hexstr, objs in glow_objects.items():
        if objs:
            g = K.join(objs, egg_id + "_Glow_" + hexstr, coll)
            for p in g.data.polygons:
                p.use_smooth = False
            parts.append(g)
    W.export_batch(parts, os.path.join(EGG_DIR, egg_id + ".fbx"))
    return parts

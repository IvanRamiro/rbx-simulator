"""Baking an Eclipse Exorcist item (run inside Blender): its high-detail pieces (and the motifs lying
on them) onto its game mesh, one texture set per item.

- unwrap: every game-mesh piece of the item into one shared UV layout (smart project), the lining's
  islands (the inner faces, which barely show) given a third of the texel density, then packed.
- bake: each game-mesh piece from its own high-detail piece and the motifs on it only (baking all at
  once, overlapping layers such as the stole over the torso would bleed into each other), into the
  item's colour (with the shaders' ambient occlusion), tangent normal, roughness and metalness maps,
  written to assets/ugc/EclipseExorcist/<Item>_<map>.png.
"""
import math
import os

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

import ee_kit as K

EB = K.EB

LINING_SCALE = 0.35


def _islands(bm, uvl):
    """UV islands of a bmesh: lists of faces connected through edges whose UVs agree on both sides."""
    parent = {f.index: f.index for f in bm.faces}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) != 2:
            continue
        f0, f1 = lf

        def uv_at(f, v):
            for lp in f.loops:
                if lp.vert == v:
                    return lp[uvl].uv
        ok = all((uv_at(f0, v) - uv_at(f1, v)).length < 1e-5 for v in e.verts)
        if ok:
            parent[find(f0.index)] = find(f1.index)
    groups = {}
    for f in bm.faces:
        groups.setdefault(find(f.index), []).append(f)
    return list(groups.values())


def unwrap(lows, lining_names=("EE_CrimsonLining",)):
    """One UV layout over all the item's game-mesh pieces."""
    for o in lows:
        me = o.data
        while me.uv_layers:
            me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    for o in lows:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lows[0]
    with K.override(lows, lows[0]):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    # the lining's islands at a third of the density
    for o in lows:
        slots = [i for i, m in enumerate(o.data.materials) if m and m.name in lining_names]
        if not slots:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        uvl = bm.loops.layers.uv.active
        for isl in _islands(bm, uvl):
            if not all(f.material_index in slots for f in isl):
                continue
            uvs = [lp[uvl].uv for f in isl for lp in f.loops]
            cx = sum(u.x for u in uvs) / len(uvs)
            cy = sum(u.y for u in uvs) / len(uvs)
            for f in isl:
                for lp in f.loops:
                    u = lp[uvl].uv
                    lp[uvl].uv = (cx + (u.x - cx) * LINING_SCALE, cy + (u.y - cy) * LINING_SCALE)
        bm.to_mesh(o.data)
        bm.free()
    with K.override(lows, lows[0]):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(margin=0.004, rotate=True, scale=True)
        bpy.ops.object.mode_set(mode="OBJECT")


def pairs_by_name(lows, his, decals):
    """[(low piece, [its high-detail piece and the motifs lying on it])]: pieces pair by name (the
    _low and _hi suffixes); each motif goes with the high-detail piece it lies closest to."""
    by = {o.name.rsplit("_", 1)[0]: o for o in his}
    trees = {}
    for o in his:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm = bmesh.new()
        bm.from_mesh(me)
        trees[o.name] = BVHTree.FromBMesh(bm)
        bm.free()
        bpy.data.meshes.remove(me)
    owner = {}
    for d in decals:
        verts = [d.matrix_world @ v.co for v in list(d.data.vertices)[:: max(1, len(d.data.vertices) // 40)]]
        best, best_d = None, 1e9
        for o in his:
            dists = (trees[o.name].find_nearest(p)[3] for p in verts)
            tot = sum(d if d is not None else 1e9 for d in dists)
            if tot < best_d:
                best, best_d = o, tot
        owner.setdefault(best.name, []).append(d)
    out = []
    for lo in lows:
        hi = by[lo.name.rsplit("_", 1)[0]]
        out.append((lo, [hi] + owner.get(hi.name, [])))
    return out


def bake(item, pairs, size=2048, small=1024, samples=12, extrusion=0.06, ray=0.16):
    """Bakes every pair into the item's maps (written to OUT_DIR); returns the images."""
    scene = bpy.context.scene
    vl = bpy.context.view_layer
    images = {"color": EB._image(item + "_Color", size, True), "normal": EB._image(item + "_Normal", size, False),
              "roughness": EB._image(item + "_Roughness", small, False), "metalness": EB._image(item + "_Metalness", small, False)}
    mat = EB._baked_material(item, images)
    for lo, _ in pairs:
        lo.data.materials.clear()
        lo.data.materials.append(mat)
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    rays = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow")
    passes = [("color", "DIFFUSE", None), ("normal", "NORMAL", None), ("roughness", "EMIT", "BAKE_ROUGH"), ("metalness", "EMIT", "BAKE_METAL")]
    hidden = []
    all_hi = {o for _, his in pairs for o in his}
    all_lo = [lo for lo, _ in pairs]
    try:
        for key, kind, route in passes:
            mat.node_tree.nodes.active = mat.node_tree.nodes[key]
            hi_mats = {m for o in all_hi for m in o.data.materials if m}
            restore = EB._route_value(hi_mats, route) if route else None
            try:
                for n, (lo, his) in enumerate(pairs):
                    # only this pair takes part: the other pieces are hidden from the rays
                    hidden = [o for o in list(all_hi) + all_lo if o not in his and o is not lo]
                    saved = {(o.name, r): getattr(o, r) for o in hidden + [lo] for r in rays}
                    for o in hidden + [lo]:
                        for r in rays:
                            setattr(o, r, False)
                    bpy.ops.object.select_all(action="DESELECT")
                    for o in his:
                        o.select_set(True)
                    lo.select_set(True)
                    vl.objects.active = lo
                    kw = dict(type=kind, use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=ray, margin=6,
                              use_clear=(n == 0), target="IMAGE_TEXTURES")
                    if kind == "DIFFUSE":
                        kw["pass_filter"] = {"COLOR"}
                    if kind == "NORMAL":
                        kw["normal_space"] = "TANGENT"
                    try:
                        bpy.ops.object.bake(**kw)
                    finally:
                        for (name, r), v in saved.items():
                            setattr(bpy.data.objects[name], r, v)
            finally:
                if restore:
                    restore()
    finally:
        scene.render.engine = engine
    EB.wire_baked(mat)
    os.makedirs(K.OUT_DIR, exist_ok=True)
    for key, img in images.items():
        img.filepath_raw = os.path.join(K.OUT_DIR, item + "_" + key + ".png")
        img.file_format = "PNG"
        img.save()
    return images

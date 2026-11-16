"""Stages for hub_district_run.py beyond build and qa: the z-fight locator, the paving, the review sheet and the export."""
import math
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import hub_district as D

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def _tris(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris, owner = [], [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            tris.append(tuple(base + i for i in t.vertices))
            owner.append(o.name)
        ev.to_mesh_clear()
    return verts, tris, owner


def zf(names):
    """Prints where coplanar overlapping faces are (Roblox studs: x, y up, z), per asset."""
    groups, _ = D.build(names)
    for asset, objs in groups.items():
        verts, tris, owner = _tris(objs)
        bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
        seen = set()
        for ti, t in enumerate(tris):
            a, b, c = (verts[i] for i in t)
            n = (b - a).cross(c - a)
            if n.length < 1e-9:
                continue
            n.normalize()
            cen = (a + b + c) / 3
            for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
                for _, _, tj, _ in bvh.find_nearest_range(p, 0.001):
                    if tj is None or tj == ti or set(tris[tj]) & set(t):
                        continue
                    a2, b2, c2 = (verts[i] for i in tris[tj])
                    n2 = (b2 - a2).cross(c2 - a2)
                    if n2.length < 1e-9:
                        continue
                    n2.normalize()
                    if n.dot(n2) < 0.999:
                        continue
                    key = (min(ti, tj), max(ti, tj))
                    if key in seen:
                        continue
                    seen.add(key)
                    print("ZF %s %s<->%s at roblox (%.2f, %.2f, %.2f) normal (%.2f, %.2f, %.2f)" % (
                        asset, owner[ti], owner[tj], cen.x, cen.z, -cen.y, n.x, n.z, -n.y))


# ---------- look-dev renders ----------
def _engine(scene):
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = name
            return name
        except TypeError:
            continue
    return scene.render.engine


def stage_scene(res=(1280, 800)):
    """A sunlit scene: a soft blue sky, a warm sun, a lawn under everything (the ground at Roblox y 0)."""
    scene = bpy.context.scene
    _engine(scene)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    world = bpy.data.worlds.get("HubSky") or bpy.data.worlds.new("HubSky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(coord.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.78, 0.86, 0.95, 1)
    ramp.color_ramp.elements[1].color = (0.32, 0.52, 0.86, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.75
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.objects.get("HubSun")
    if not sun:
        ld = bpy.data.lights.new("HubSun", "SUN")
        sun = bpy.data.objects.new("HubSun", ld)
        scene.collection.objects.link(sun)
    sun.data.energy = 2.7
    sun.data.color = (1.0, 0.95, 0.86)
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
    ground = bpy.data.objects.get("HubLawn")
    if not ground:
        me = bpy.data.meshes.new("HubLawn")
        s = 900
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        ground = bpy.data.objects.new("HubLawn", me)
        scene.collection.objects.link(ground)
        m = bpy.data.materials.new("pv_lawn")
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.16, 0.32, 0.12, 1)
        b.inputs["Roughness"].default_value = 0.9
        me.materials.append(m)
    return scene


def camera(name, loc_rb, look_rb, lens=35.0, ortho=None):
    """A camera at a Roblox-space point looking at another."""
    from mathutils import Vector
    import worldlib as W
    cam = bpy.data.objects.get(name)
    if not cam:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    loc, look = W.rb(*loc_rb), W.rb(*look_rb)
    cam.location = loc
    cam.rotation_euler = (look - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 5000
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
    return cam


def render_to(cam, path):
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path


def show_only(objs):
    keep = set(o.name for o in objs) | {"HubSun", "HubLawn"}
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in keep


# where each asset's views are taken from: (three-quarter eye, look at), (player's eye, look at), Roblox studs in its own frame
VIEWS = {
    "Market": (((34, 26, 58), (0, 10, -2)), ((9, 5.5, 34), (0, 9, 0))),
    "Blacksmith": (((36, 28, 58), (0, 13, -4)), ((10, 5.5, 36), (0, 11, 0))),
    "BuySell": (((32, 24, 52), (0, 12, -2)), ((8, 5.5, 33), (0, 10, 0))),
    "MerchantDais": (((16, 14, 26), (0, 2, -2)), ((4, 5.5, 22), (0, 3, -4))),
    "SpawnPad": (((8, 7, 12), (0, 0.5, 0)), ((2, 5.5, 13), (0, 0.6, 0))),
    "SanctumPlinth": (((30, 18, 34), (0, 0, 0)), ((6, 5.5, 32), (0, 0.5, 0))),
    "SquareCompass": (((8, 7, 12), (0, 3.5, 0)), ((2, 5.5, 13), (0, 4, 0))),
}


def look(names):
    """Each asset alone: three-quarter and eye height, into $HUB_LOOK_DIR."""
    out = os.environ.get("HUB_LOOK_DIR", "/tmp")
    groups, _ = D.build(names)
    stage_scene()
    for asset, objs in groups.items():
        show_only(objs)
        (a, b), (c, d) = VIEWS[asset]
        render_to(camera("Cam34", a, b, 32), os.path.join(out, asset + "_34.png"))
        render_to(camera("CamEye", c, d, 24), os.path.join(out, asset + "_eye.png"))
        print("LOOK", asset)


def paving(names):
    """Builds the paving and QA's it (the paving is one asset: its pieces touch each other)."""
    import hub_district_run as R
    groups = D.build_paving()
    flat = {"Paving": [o for objs in groups.values() for o in objs]}
    for name, objs in groups.items():
        print(name, sum(D.tris(o) for o in objs), "tris", [(o.name, D.tris(o)) for o in objs])
    R.run_qa(flat, eps=0.001, tol=0.002)


def underside(names):
    """Builds Yggdrasil's island meshes (ygg_meshes: the strata on the new rim, the re-routed grip roots, the tree), QA's the
    underside, and checks the roots: none above the ground inside the Ring Road's outer edge (236), on a bridge's deck or in a shop."""
    import ygg_meshes as M
    import ygg_island as Y
    import hub_ground as G
    import hub_district_run as R
    objs, img, report = M.build()
    print("UNDERSIDE clearance", report)
    under = [o for o in objs if o.name in M.CHANGED_BY_REDESIGN]
    M.roblox_ready(under)
    R.run_qa({"Underside": under}, eps=0.001, tol=0.05)
    shop_rects = G.shops()
    for o in objs:
        if not o.name.startswith("YG_GripRoot"):
            continue
        worst_in, worst_shop, worst_deck, high = 0.0, 1e9, 1e9, -1e9
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            x, y, z = p.x, p.z, -p.y            # Roblox studs
            r = math.hypot(x, z)
            g = G.ground(x, z) if r < Y.rim(math.atan2(z, x)) else -99
            above = y - g
            if r < 238.0:
                worst_in = max(worst_in, above)
            if above > -1.0:
                for name, (cx, cz, w, d, yaw) in shop_rects.items():
                    worst_shop = min(worst_shop, G._rect(x, z, cx, cz, w + 2, d + 2, yaw))
                for rx, rz, b in G.bridges().values():
                    ux, uz = math.cos(math.radians(b)), math.sin(math.radians(b))
                    t = x * ux + z * uz
                    if t > 230:
                        worst_deck = min(worst_deck, abs(-x * uz + z * ux) - 20.0)
            high = max(high, above)
        print("ROOT %s: highest above the ground inside r 238: %.2f; nearest shop footprint (+1): %.1f; nearest deck edge: %.1f; top over ground %.1f"
              % (o.name, worst_in, worst_shop, worst_deck, high))
    lowest = min((o.matrix_world @ v.co).z for o in under for v in o.data.vertices)
    print("UNDERSIDE lowest (Roblox y) %.1f (must stay above -124)" % lowest)


# ---------- the district assembled in island coordinates ----------
def _place(o, x, y, z, yaw=0.0):
    import worldlib as W
    o.location = W.rb(x, y, z)
    o.rotation_euler = (0.0, 0.0, yaw)


def assemble():
    """Every new piece where the layout puts it (island-local studs), the moved Sanctum on its plinth, the paving,
    and a preview of the ground (the terrain's heights and the new rim). Returns {group: [objects]}."""
    import hub_ground as G
    import hub_celestial as H
    import hub_finish as F
    groups, spots = D.build()
    paving = D.build_paving()
    for name, (x, z, w, d, yaw) in G.shops().items():
        asset = {"Marketplace": "Market"}.get(name, name)
        for o in groups[asset]:
            _place(o, x, G.ground(x, z), z, yaw)
    for o in groups["MerchantDais"]:
        _place(o, G.MERCHANT[0], 0.0, G.MERCHANT[1], math.pi)
    for o in groups["SquareCompass"]:
        _place(o, G.SQUARE[0], 0.0, G.SQUARE[1])
    for o in groups["SanctumPlinth"]:
        _place(o, G.SANCTUM[0], G.LIFT, G.SANCTUM[1])
    pads = list(groups["SpawnPad"])
    copies = []
    for i, b, _, _, (sx, sz) in G.pens():
        for o in pads:
            c = o if i == 1 else o.copy()
            if c is not o:
                bpy.context.scene.collection.objects.link(c)
                copies.append(c)
            _place(c, sx, 0.0, sz, G.face_yaw(math.cos(math.radians(b)), math.sin(math.radians(b))))
    groups["SpawnPad"] += copies
    # the Sanctum as it is (hub_celestial), for context
    img, bands = H.W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS) if hasattr(H, "W") else (None, None)
    import worldlib as W
    img, bands = W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS)
    H.MARBLE_BAND, H.GOLD_BAND = bands[H.MARBLE], bands[H.GOLD]
    ctx = W.collection("HD_Context")
    W.clear_collection(ctx)
    old = [fn(ctx, None, bands) for fn in (H.sanctum, H.sanctum_glass, H.sanctum_crystal, H.sanctum_runes,
                                         H.crystal_lamp, H.crystal_lamp_glow)]
    old = F.finish(old, bands, ctx)
    F.preview_materials(old)
    lamps = [o for o in old if o.name.startswith("HB_CrystalLamp")]
    for o in old:
        if o.name.startswith(("HB_Hatch", "HB_Sanctum")):
            _place(o, G.SANCTUM[0], G.LIFT, G.SANCTUM[1])
    lamp_objs = []
    for k, (x, z, yaw) in enumerate(G.lamp_layout()):
        for o in lamps:
            c = o.copy()
            bpy.context.scene.collection.objects.link(c)
            _place(c, x, G._y(x, z), z, yaw)
            lamp_objs.append(c)
    for o in lamps:
        o.hide_render = True
    groups["Context"] = [o for o in old if o not in lamps] + lamp_objs
    groups["Paving"] = [o for objs in paving.values() for o in objs]
    groups["Ground"] = [ground_preview()]
    return groups, spots


def ground_preview(cell=4.0):
    """The island's top as a mesh (the terrain's heights, out to the new rim), for the renders."""
    import ygg_island as Y
    import hub_ground as G
    import worldlib as W
    n = int(396 / cell)
    verts, faces, index = [], [], {}
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, z = i * cell, j * cell
            h, _ = G.height(x, z)
            if h is None:
                continue
            index[(i, j)] = len(verts)
            verts.append(W.rb(x, h - 0.05, z))
    for i in range(-n, n):
        for j in range(-n, n):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in index for k in q):
                faces.append([index[k] for k in q][::-1])
    o = W.mesh_object("HD_GroundPreview", verts, faces, W.collection("HD_Ground"), smooth=True)
    m = bpy.data.materials.get("pv_lawn2") or bpy.data.materials.new("pv_lawn2")
    b = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.2, 0.36, 0.14, 1)
    b.inputs["Roughness"].default_value = 0.9
    o.data.materials.append(m)
    return o


# ---------- the phase-1 blockout's outline, from its own numbers (the approved phase-1 blockout), for the top-down proof ----------
BLOCKOUT = {
    "TreeRing": (80, 104), "RingRoad": (216, 236), "PenRadius": 168, "PenBearings": (60, 120, 180, -120, -60, 0), "PenPlot": (62, 84),
    "Discs": [(0, 118, 13), (0, -120, 15), (0, -178, 22), (-147.2, 85, 24), (0, 176, 24), (226.5, -110.5, 28)],
    "Shops": [(235.3, -194.0, 40, 44), (304.4, -141.9, 48, 40), (288.9, -54.3, 40, 40)],
    "Square": (226.5, -110.5),
}


def outline_mesh():
    """Thin red strips along the blockout's outlines (and the new ground's rim, by its own algorithm), floating over everything."""
    import worldlib as W
    import ygg_island as Y
    mb = W.MeshBuilder()
    Y_TOP = 60.0
    band = (0.0, 1.0)

    def seg(a, b, w=2.2):
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L * w / 2, dx / L * w / 2
        mb.face([(a[0] + nx, Y_TOP, a[1] + nz), (b[0] + nx, Y_TOP, b[1] + nz), (b[0] - nx, Y_TOP, b[1] - nz), (a[0] - nx, Y_TOP, a[1] - nz)][::-1],
                [(0.5, 0.5)] * 4)

    def circle(cx, cz, r, n=96):
        pts = [(cx + math.cos(TAU * k / n) * r, cz + math.sin(TAU * k / n) * r) for k in range(n + 1)]
        for a, b in zip(pts, pts[1:]):
            seg(a, b)

    def rect(cx, cz, w, d, yaw):
        c, s = math.cos(yaw), math.sin(yaw)
        P = [(cx + x * c + z * s, cz - x * s + z * c) for x, z in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        for k in range(4):
            seg(P[k], P[(k + 1) % 4])
    TAU = 2 * math.pi
    for r in BLOCKOUT["TreeRing"] + BLOCKOUT["RingRoad"]:
        circle(0, 0, r, 160)
    for b in BLOCKOUT["PenBearings"]:
        cx, cz = math.cos(math.radians(b)) * BLOCKOUT["PenRadius"], math.sin(math.radians(b)) * BLOCKOUT["PenRadius"]
        rect(cx, cz, BLOCKOUT["PenPlot"][0], BLOCKOUT["PenPlot"][1], math.radians(90 - b))
        sx, sz = math.cos(math.radians(b)) * 120, math.sin(math.radians(b)) * 120
        circle(sx, sz, 6, 24)
    for cx, cz, r in BLOCKOUT["Discs"]:
        circle(cx, cz, r)
    sqx, sqz = BLOCKOUT["Square"]
    for cx, cz, w, d in BLOCKOUT["Shops"]:
        rect(cx, cz, w, d, math.atan2(sqx - cx, sqz - cz))
    # the new ground's rim, as the blockout drew it (bearing steps of 2 degrees)
    rim = [(b, Y.rim(math.radians(b))) for b in range(-60, 16, 2)]
    pts = [(math.cos(math.radians(b)) * r, math.sin(math.radians(b)) * r) for b, r in rim]
    for a, b in zip(pts, pts[1:]):
        seg(a, b, 2.6)
    o = mb.object("HD_BlockoutOutline", W.collection("HD_Ground"), None)
    m = bpy.data.materials.get("pv_outline") or bpy.data.materials.new("pv_outline")
    nt = m.node_tree
    b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (1.0, 0.1, 0.05, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
    b.inputs["Emission Strength"].default_value = 6.0
    o.data.materials.append(m)
    return o


def clay(objs, on=True):
    m = bpy.data.materials.get("pv_clay") or bpy.data.materials.new("pv_clay")
    b = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.42, 0.42, 0.41, 1)
    b.inputs["Roughness"].default_value = 0.8
    for o in objs:
        if on:
            o["_mats"] = [s.material.name if s.material else "" for s in o.material_slots]
            for s in o.material_slots:
                s.material = m
        elif "_mats" in o:
            for s, name in zip(o.material_slots, o["_mats"]):
                s.material = bpy.data.materials.get(name)


def wire(objs, on=True):
    m = bpy.data.materials.get("pv_wire") or bpy.data.materials.new("pv_wire")
    b = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.05, 0.08, 0.16, 1)
    out = []
    for o in objs:
        if on:
            c = o.copy()
            c.data = o.data.copy()
            c.data.materials.clear()
            c.data.materials.append(m)
            bpy.context.scene.collection.objects.link(c)
            md = c.modifiers.new("Wire", "WIREFRAME")
            md.thickness = 0.07
            md.use_replace = True
            out.append(c)
    return out


def caption(text, path, w, h=44):
    """A caption strip: white text on the sheet's dark band."""
    scene = bpy.data.scenes.get("Caption") or bpy.data.scenes.new("Caption")
    for o in list(scene.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    _engine(scene)
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.get("CapBg") or bpy.data.worlds.new("CapBg")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.04, 0.06, 1)
    scene.world = world
    cu = bpy.data.curves.new("cap", "FONT")
    cu.body = text
    cu.size = 0.42
    cu.align_x = "LEFT"
    cu.align_y = "CENTER"
    t = bpy.data.objects.new("cap", cu)
    scene.collection.objects.link(t)
    mat = bpy.data.materials.get("pv_captext") or bpy.data.materials.new("pv_captext")
    bb = next(nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    bb.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    bb.inputs["Emission Strength"].default_value = 1.0
    bb.inputs["Base Color"].default_value = (1, 1, 1, 1)
    cu.materials.append(mat)
    cam = bpy.data.objects.new("capcam", bpy.data.cameras.new("capcam"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = w / h
    cam.location = (w / h / 2 - 0.25, 0, 5)
    t.location = (0, 0, 0)
    scene.camera = cam
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True, scene=scene.name)
    return path


def compose(panels, cols, out, pw, ph, cap_h=44, gap=8):
    """panels: [(png, caption)] -> one sheet."""
    import numpy as np
    rows = (len(panels) + cols - 1) // cols
    W_, H_ = cols * pw + (cols + 1) * gap, rows * (ph + cap_h) + (rows + 1) * gap
    sheet = np.zeros((H_, W_, 4), dtype=np.float32)
    sheet[..., :3] = (0.035, 0.04, 0.06)
    sheet[..., 3] = 1.0
    tmp = os.environ.get("HUB_LOOK_DIR", "/tmp")
    for k, (png, text) in enumerate(panels):
        r, c = divmod(k, cols)
        x0 = gap + c * (pw + gap)
        y_top = gap + r * (ph + cap_h + gap)
        img = bpy.data.images.load(png)
        a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
        if a.shape[0] != ph or a.shape[1] != pw:
            ys = (np.arange(ph) * a.shape[0] / ph).astype(int)
            xs = (np.arange(pw) * a.shape[1] / pw).astype(int)
            a = a[ys][:, xs]
        y0 = H_ - (y_top + cap_h + ph)        # (Blender images run bottom-up)
        sheet[y0:y0 + ph, x0:x0 + pw] = a
        cp = caption(text, os.path.join(tmp, "cap_%02d.png" % k), pw, cap_h)
        ci = bpy.data.images.load(cp)
        ca = np.array(ci.pixels[:], dtype=np.float32).reshape(ci.size[1], ci.size[0], 4)
        sheet[y0 + ph:y0 + ph + cap_h, x0:x0 + pw] = ca
    out_img = bpy.data.images.new("Sheet", W_, H_, alpha=False)
    out_img.pixels[:] = sheet.ravel()
    out_img.filepath_raw = out
    out_img.file_format = "PNG"
    out_img.save()
    return out


def review(names):
    """renders/hub_redesign/phase2_review.png."""
    import hub_ground as G
    tmp = os.environ.get("HUB_LOOK_DIR", "/tmp")
    groups, spots = assemble()
    scene = stage_scene((960, 600))
    lawn = bpy.data.objects.get("HubLawn")
    lawn.hide_render = True
    every = [o for objs in groups.values() for o in objs]
    panels = []

    def shot(name, loc, look, lens, text, ortho=None):
        p = os.path.join(tmp, "rv_%s.png" % name)
        render_to(camera("RvCam", loc, look, lens, ortho), p)
        panels.append((p, text))

    def local(asset, p):
        """An asset-frame point in island coordinates."""
        if asset in ("Market", "Blacksmith", "BuySell"):
            key = {"Market": "Marketplace"}.get(asset, asset)
            x, z, w, d, yaw = G.shops()[key]
        else:
            (x, z), yaw = G.MERCHANT, math.pi
        lx, ly, lz = p
        return (x + lx * math.cos(yaw) + lz * math.sin(yaw), ly + G.ground(x, z), z - lx * math.sin(yaw) + lz * math.cos(yaw))
    titles = {"Market": "Market (the Crystal Market)", "Blacksmith": "Blacksmith (the Celestial Forge)", "BuySell": "Buy & Sell (the Gilded Vault)"}
    for asset in ("Market", "Blacksmith", "BuySell"):
        (a, b), (c, d) = VIEWS[asset]
        shot(asset + "34", local(asset, a), local(asset, b), 30, titles[asset] + ": front three-quarter")
        shot(asset + "eye", local(asset, c), local(asset, d), 24, titles[asset] + ": player's eye height")
    sq = G.SQUARE
    shot("district", (175, 95, -30), (272, 8, -130), 30, "The Merchants' Terrace: the district as a whole, from over the Ring Road")
    shot("square", (200, 6.5, -96), (300, 14, -140), 26, "The Market Square at eye height: Market ahead, Blacksmith left, Buy & Sell right")
    shot("merchant", (14, 13, -150), (0, 2, -120), 30, "The Hidden Merchant's dais (empty: it still reads as a place)")
    shot("pad", (64, 7, 116), (60, 0.5, 104), 30, "Spawn pad (facing its pen), the Arrival side")
    shot("sanctum", (40, 30, -120), (0, 6, -178), 30, "The Hatching Sanctum moves as it is, on its new plinth")
    shot("compass", (238, 7, -96), (226.5, 4, -110.5), 30, "The Market Square's centrepiece (restrained)")
    # clay and wireframe
    district = groups["Market"] + groups["Blacksmith"] + groups["BuySell"] + groups["SquareCompass"] + groups["Paving"]
    built = [o for o in every if o not in groups["Ground"]]
    clay(built)
    shot("clay", (175, 95, -30), (272, 8, -130), 30, "Clay: the district (forms only)")
    wires = wire(groups["Blacksmith"] + groups["Market"])
    shot("wire", local("Blacksmith", (40, 30, 60)), local("Blacksmith", (0, 12, -4)), 30, "Clay and wireframe: the Blacksmith (%d triangles)" %
         sum(D.tris(o) for o in groups["Blacksmith"]))
    shot("wire2", local("Market", (34, 26, 58)), local("Market", (0, 10, -2)), 30, "Clay and wireframe: the Market (%d triangles)" %
         sum(D.tris(o) for o in groups["Market"]))
    for o in wires:
        bpy.data.objects.remove(o, do_unlink=True)
    clay(built, on=False)
    # the top-down proof: the new ground and the built footprints with the blockout's outline over them
    outline = outline_mesh()
    cam = camera("TopCam", (40, 900, -40), (40, 0, -40.5), 50, ortho=820)
    import worldlib as W
    cam.location = W.rb(40, 900, -40)
    cam.rotation_euler = (0.0, 0.0, 0.0)      # straight down, north (Roblox -Z, Blender +Y) up, east right
    p = os.path.join(tmp, "rv_topdown.png")
    render_to(cam, p)
    panels.append((p, "Top-down (north up): the new ground and every built footprint, the approved blockout's outlines in red"))
    out = os.path.join(REPO, "renders", "hub_redesign", "phase2_review.png")
    compose(panels, 4, out, 960, 600)
    print("REVIEW", out)


# ---------- the export ----------
def _scrub(path):
    """Machine paths in an exported file read /Users/user (same length: binary-safe); a fixed-size path field's stale bytes after
    its end are zeroed (a shorter path leaves the old one's tail behind)."""
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


def export(names):
    """assets/world/Yggdrasil/Yggdrasil_District.fbx (every new piece and the paving; anchor HB_Anchor at the island's centre),
    Yggdrasil_Underside.fbx (the strata and the grip roots the redesign changed; anchor YG_Anchor), the staged data
    (src/worldbuild/Terrain and Placements), tools/blender/world/HubDistrict.blend and renders/hub_redesign/phase2_qa.txt."""
    import json
    import hub_ground as G
    import ygg_meshes as M
    import worldlib as W
    import hub_district_run as R
    groups, spots = D.build()
    paving = D.build_paving()
    report = R.run_qa(groups)
    report.update(R.run_qa({"Paving": [o for objs in paving.values() for o in objs]}))
    kit = [o for objs in groups.values() for o in objs] + [o for objs in paving.values() for o in objs]
    for o in kit:      # the weighted normals into the meshes (FBX takes the evaluated mesh anyway; this keeps the .blend honest)
        bpy.context.view_layer.objects.active = o
    fbx = os.path.join(REPO, "assets", "world", "Yggdrasil", "Yggdrasil_District.fbx")
    W.export_batch(kit, fbx, image=None, anchor_name="HB_Anchor")
    _scrub(fbx)
    objs, img, rep = M.build()
    upath, under = M.export_underside(objs)
    _scrub(upath)
    report.update(R.run_qa({"Underside": under}, eps=0.001, tol=0.05))
    staged = [G.export_terrain(), G.write_placements(spots), G.write_pastures()]
    with open(os.path.join(REPO, "renders", "hub_redesign", "phase2_qa.txt"), "w") as f:
        f.write("Asset QA (blender-asset-qa, profile roblox) of every phase-2 export, %s\n\n" % "2026-11-15")
        for asset, r in report.items():
            f.write("%s: %s, %d triangles, %d errors\n" % (asset, "PASS" if r["pass"] else "FAIL", sum(r["tris"].values()), len(r["errors"])))
            for name, t in sorted(r["tris"].items()):
                f.write("    %-34s %6d\n" % (name, t))
            for e in r["errors"]:
                f.write("    ERROR %s\n" % e)
            for w in r["warnings"]:
                f.write("    warning: %s\n" % w)
        f.write("\nSpots (each piece's own frame, Roblox studs):\n%s\n" % json.dumps(spots, indent=1, default=list))
    blend = os.path.join(HERE, "HubDistrict.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=False)
    _scrub(blend)
    print("EXPORTED", fbx, upath, staged, blend, "kit pieces", len(kit), "underside pieces", len(under))
    print("TRIS kit", sum(D.tris(o) for o in kit), "underside", sum(D.tris(o) for o in under))


def export_pieces(names):
    """Re-exports one building (or a few) for a re-import: assets/world/Yggdrasil/Yggdrasil_<Asset>.fbx, anchor HB_Anchor, after
    the QA. names: hub_district.ASSETS keys."""
    import worldlib as W
    import hub_district_run as R
    groups, spots = D.build(names)
    rep = R.run_qa(groups)
    assert all(r["pass"] for r in rep.values()), "QA failed"
    for asset, objs in groups.items():
        path = os.path.join(REPO, "assets", "world", "Yggdrasil", "Yggdrasil_%s.fbx" % asset)
        W.export_batch(objs, path, image=None, anchor_name="HB_Anchor")
        _scrub(path)
        print("EXPORTED", path, len(objs), "pieces", sum(D.tris(o) for o in objs), "tris", spots[asset])

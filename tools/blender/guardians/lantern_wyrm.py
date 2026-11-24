"""The Abyssal Lantern Wyrm, the boss of the Origin Abyss: model, skeleton, weights, maps, export (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/lantern_wyrm.py -- <stage> [--out DIR]

A colossal limbless serpent-dragon of the deep dark, about 76 studs long and 5 thick at the girth, tapering over its last third to a finned
tail: the long (a deep horned head with antlers and barbels, a mane-like frill) crossed with a deep-sea anglerfish (a stalk from the brow
carrying a faceted lantern of warm gold, the lure that draws the eye; cold cyan photophores along the flanks). Scales of near-black
blue-violet with an oil-slick sheen, pale cream ventral scutes. The brief (2026-11-24) and the silhouette study (lantern_wyrm_study.py)
decided the shape. It replaces Pangu in the game, which keeps its id.

Authored in Roblox studs, facing -Z, the belly on the ground (the spine at y = 2.6), left is -X, bound in a straight line along Z: every
pose is a curve the spine is laid along (lantern_wyrm_motion.py). It holds no egg: no guardian does.

Stages: form | look | final | strip | checks | clips | ... (see main at the bottom). The motion is lantern_wyrm_motion.py.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../eggs", "../world", "."):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, sub)))
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402
import guardian_kit as G  # noqa: E402
import tiangou_v2 as T  # noqa: E402
import lantern_wyrm_body as LB  # noqa: E402
import lantern_wyrm_head as LH  # noqa: E402
import lantern_wyrm_materials as Mt  # noqa: E402
import lantern_wyrm_bones as Bn  # noqa: E402
import lantern_wyrm_bones as B  # noqa: E402
from lantern_wyrm_bones import BONES, joints  # noqa: E402

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "LanternWyrm"
RIG = "LanternWyrmRig"
OUT = G.OUT_DIR
REPO = W.REPO

CLAY = {"body": (0.16, 0.17, 0.30), "head": (0.18, 0.20, 0.34), "horn": (0.42, 0.32, 0.20), "whisker": (0.5, 0.45, 0.4), "cup": (0.8, 0.55, 0.1), "tooth": (0.8, 0.76, 0.62),
        "frill": (0.38, 0.18, 0.55), "lamp": (1.0, 0.7, 0.1), "eyes": (1.0, 0.85, 0.4), "rings": (0.2, 0.85, 1.0)}
REAL = {}
WANT_REAL = False


def _clay(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


def use_real_materials():
    REAL.clear()
    REAL.update(Mt.all_materials())


def _mat(kind):
    if kind in REAL:
        return REAL[kind]
    return _clay("LWClay_" + kind, CLAY[kind])


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------------------------------------------------------------- skeleton
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


# ---------------------------------------------------------------- weights
def _points(obj):
    """The vertices of obj in Roblox space."""
    import numpy as np
    n = len(obj.data.vertices)
    co = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)


def _write_groups(obj, per_vertex):
    """per_vertex: a list (one per vertex) of {bone: weight}; at most four, normalised."""
    obj.vertex_groups.clear()
    groups = {}
    for i, w in enumerate(per_vertex):
        top = sorted(((v, k) for k, v in w.items() if v > 0.02), reverse=True)[:4]
        tot = sum(v for v, _ in top) or 1.0
        for v, k in top:
            if k not in groups:
                groups[k] = obj.vertex_groups.new(name=k)
            groups[k].add([i], v / tot, "REPLACE")


def bind_function(obj, fn):
    """Weights by position along the bind axis: fn(z) -> {bone: weight}."""
    pts = _points(obj)
    _write_groups(obj, [fn(float(p[2])) for p in pts])


def bind_rigid(obj, bone):
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def bind_distance(obj, names, falloff=0.6):
    """Weights from each vertex's distance to the bones in `names` (segments head to tail): the nearest leads, the rest share by a Gaussian."""
    import numpy as np
    pts = _points(obj)
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    d = np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    _write_groups(obj, [{names[j]: float(w[i, j]) for j in range(len(names))} for i in range(len(pts))])


def bind_table(obj, table):
    """Weights from a {vertex index: {bone: weight}} table."""
    _write_groups(obj, [table[i] for i in range(len(obj.data.vertices))])


def attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


# ---------------------------------------------------------------- the high-detail parts
def _hi(hi, name, coll, kinds, keep=True, smooth=True):
    o = hi.object(name, coll, [_mat(k) for k in kinds], smooth=smooth, weld=0)
    o["keep"] = keep
    return o


def build_hi(coll, voxel=0.085):
    """Every high-detail part: {piece: {key: object}}. The body is one finely ringed tube; the head a fused blob with its horns and fittings."""
    parts = {}
    bh, n = LB.body_hi(0.125, 48, grooves=True)
    body = _hi(bh, "LW_BodyHi", coll, ["body"])
    LB.body_attributes(body, n, 48, 0.125)
    parts["Body"] = {"body": body}
    skull = LH.build_skull(coll, _mat("head"), voxel)
    jaw = LH.build_jaw(coll, _mat("head"), voxel * 0.85)
    iris, lids = LH.eyes(skull)
    cut = LH.cut_slits(iris)
    head = {"skull": skull, "jaw": jaw, "lids": _hi(lids, "LW_Lids", coll, ["head"]), "horns": _hi(LH.horns(), "LW_Horns", coll, ["horn"]),
            "fangs_up": _hi(LH.fangs(True), "LW_FangsUp", coll, ["tooth"]), "fangs_low": _hi(LH.fangs(False), "LW_FangsLow", coll, ["tooth"]), "stalk": _hi(LH.stalk_and_cup(), "LW_Stalk", coll, ["horn"]), "barbels": _hi(LH.barbels(), "LW_Barbels", coll, ["whisker"])}
    for o in (skull, jaw):
        o["keep"] = False
    parts["Head"] = head
    parts["Eyes"] = {"iris": _hi(iris, "LW_Eyes", coll, ["eyes"])}
    parts["Lantern"] = {"lamp": _hi(LH.lamp(), "LW_Lamp", coll, ["lamp"])}
    for g in "ABCD":
        parts["Rings" + g] = {"rings": _hi(LB.rings_hi(g), "LW_Rings" + g, coll, ["rings"])}
    fh, fw = LB.frill_hi(rows=12, across=8)
    LB.fin_hi(fh, fw)
    frill = _hi(fh, "LW_FrillHi", coll, ["frill", "frill"], smooth=True)
    LB.frill_attributes(frill, None)
    parts["Frill"] = {"frill": frill}
    return parts, {"slit faces cut": cut, "body hi tris": tris(body), "skull hi tris": tris(skull), "frill hi tris": tris(frill)}


# ---------------------------------------------------------------- the game meshes
def _reduce(obj, target):
    now = tris(obj)
    if target and now > target:
        m = obj.modifiers.new("Reduce", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = max(0.02, target / now)
        m.use_collapse_triangulate = True
        me = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        old = obj.data
        obj.modifiers.clear()
        obj.data = me
        bpy.data.meshes.remove(old)
    for p in obj.data.polygons:
        p.use_smooth = True


def _copy(obj, name, coll):
    me = obj.data.copy()
    me.transform(obj.matrix_world)
    c = bpy.data.objects.new(name, me)
    coll.objects.link(c)
    return c


def _clean(obj):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for c in objs:
        c.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    low = bpy.context.view_layer.objects.active
    low.name = low.data.name = name
    for p in low.data.polygons:
        p.use_smooth = True
    return low


LOW_BODY = dict(du=0.3, sides=24)
HEAD_PLAN = [("skull", 8500, ("rigid", "Head")), ("jaw", 2200, ("rigid", "Jaw")), ("lids", 700, ("rigid", "Head")), ("horns", None, ("rigid", "Head")),
             ("fangs_up", None, ("rigid", "Head")), ("fangs_low", None, ("rigid", "Jaw")), ("stalk", None, ("dist", ["Head", "Lure1", "Lure2", "Lure3"], 0.35)), ("barbels", None, ("barbels",))]


def make_lows(parts, coll):
    lows = {}
    # the body: the tube again, coarser, with the same unrolling, weighted by position
    bh, n = LB.body_hi(LOW_BODY["du"], LOW_BODY["sides"], grooves=False)
    body = _hi(bh, "LW_BodyLow", coll, ["body"])
    bind_function(body, LB.body_weights)
    lows["Body"] = body
    made = []
    for key, target, how in HEAD_PLAN:
        c = _copy(parts["Head"][key], "low_head_" + key, coll)
        _reduce(c, target)
        _clean(c)
        if how[0] == "rigid":
            bind_rigid(c, how[1])
        elif how[0] == "dist":
            bind_distance(c, how[1], how[2])
        elif how[0] == "barbels":
            bind_distance(c, Bn.BARBELS["Left"] + Bn.BARBELS["Right"], 0.5)
        made.append(c)
    lows["Head"] = _join(made, "LW_HeadLow")
    # the frill and the fin
    fh, fw = LB.frill_hi(rows=5, across=3)
    _, fw2 = LB.fin_hi(fh, fw)
    frill = _hi(fh, "LW_FrillLow", coll, ["frill", "frill"])
    LB.frill_attributes(frill, None)
    bind_table(frill, fw2)
    lows["Frill"] = frill
    # the neon pieces
    for key in ("Eyes", "Lantern") + tuple("Rings" + g for g in "ABCD"):
        src = list(parts[key].values())[0]
        c = _copy(src, "low_" + key, coll)
        if key == "Eyes":
            bind_rigid(c, "Eyes")
        elif key == "Lantern":
            bind_rigid(c, "Lure3")
        else:
            bind_function(c, LB.body_weights)
        lows[key] = c
    return lows


GAME_NAMES = {"Body": "Body", "Head": "Head", "Frill": "Frill", "Eyes": "Eyes", "Lantern": "Lantern", "RingsA": "RingsA", "RingsB": "RingsB", "RingsC": "RingsC", "RingsD": "RingsD"}


def drop_zfighting(lows, eps=0.001):
    """Where two triangles of the asset lie on one plane (within eps) facing the same way and overlap, one of them is hidden under the other
    and z-fights with it: the later one is removed (the same test blender-asset-qa makes). Every piece is triangulated first."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    objs = list(lows.values())
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    verts, tris, meta = [], [], []
    for oi, o in enumerate(objs):
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            tris.append(tuple(base + i for i in p.vertices))
            meta.append((oi, p.index, p.normal.copy()))
    bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    tri_sets = [set(t) for t in tris]
    drop = set()
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = meta[ti][2]
        if n.length < 0.5:
            continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or tri_sets[ti] & tri_sets[tj]:
                    continue
                n2 = meta[tj][2]
                if n.dot(n2) < 0.999:
                    continue
                a2, b2, c2 = (verts[i] for i in tris[tj])
                q = p - n2 * n2.dot(p - a2)
                v0, v1, v2 = c2 - a2, b2 - a2, q - a2
                d00, d01, d02, d11, d12 = v0.dot(v0), v0.dot(v1), v0.dot(v2), v1.dot(v1), v1.dot(v2)
                inv = d00 * d11 - d01 * d01
                if abs(inv) < 1e-12:
                    continue
                u, w = (d11 * d02 - d01 * d12) / inv, (d00 * d12 - d01 * d02) / inv
                if u >= -1e-6 and w >= -1e-6 and u + w <= 1 + 1e-6:
                    drop.add(max(ti, tj))
    per = {}
    for ti in drop:
        per.setdefault(meta[ti][0], set()).add(meta[ti][1])
    for oi, faces in per.items():
        bm = bmesh.new()
        bm.from_mesh(objs[oi].data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in faces], context="FACES")
        bm.to_mesh(objs[oi].data)
        bm.free()
    return len(drop)




def build_lows(real=False, voxel=0.085):
    global WANT_REAL
    from tiangou_v2 import clear
    clear()
    coll = bpy.data.collections.new("LanternWyrm")
    bpy.context.scene.collection.children.link(coll)
    if real:
        use_real_materials()
    build_skeleton(coll)
    parts, info = build_hi(coll, voxel)
    lows = make_lows(parts, coll)
    print("hidden coplanar triangles removed:", drop_zfighting(lows))
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o not in lows.values():
            o.hide_render = True
            o.hide_viewport = True
    for name, o in lows.items():
        attach(o)
    return info, parts, lows


def count(lows):
    out, infl = {}, 0
    for k, o in lows.items():
        out[k] = tris(o)
        infl = max(infl, max((len(v.groups) for v in o.data.vertices), default=0))
    out["total"] = sum(out.values())
    out["max influences"] = infl
    return out


def review(path, views, size=520, columns=3, hide=(RIG,)):
    scene, cam = T._review_scene(size)
    for h in hide:
        if bpy.data.objects.get(h):
            bpy.data.objects[h].hide_render = True
    tmp = path + ".tile.png"
    tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in views]
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


# ---------------------------------------------------------------- looks, maps, the FBX
def setup_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type != "CPU" for d in prefs.devices):
                for d in prefs.devices:
                    d.use = True
                bpy.context.scene.cycles.device = "GPU"
                return kind
        except (TypeError, RuntimeError):
            continue
    return "CPU"


def look(path, shots, size=640, samples=48, columns=3, hide=(RIG,)):
    """Colour renders of the high-detail model with its real shaders, in a dim cold light with a warm key (the lantern's)."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    kind = setup_gpu()
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    world = bpy.data.worlds.get("LWWorld") or bpy.data.worlds.new("LWWorld")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.30, 0.34, 0.46, 1)
    bg.inputs[1].default_value = 0.9
    scene.world = world
    for name, energy, rot, col in (("LWKey", 4.0, (50, 0, 35), (1.0, 0.88, 0.72)), ("LWRim", 3.0, (65, 0, 215), (0.55, 0.7, 1.0))):
        if not bpy.data.objects.get(name):
            d = bpy.data.lights.new(name, "SUN")
            d.energy = energy
            d.color = col
            o = bpy.data.objects.new(name, d)
            o.rotation_euler = tuple(math.radians(a) for a in rot)
            scene.collection.objects.link(o)
    cam = bpy.data.objects.get("LWCam")
    if not cam:
        data = bpy.data.cameras.new("LWCam")
        data.lens = 60
        cam = bpy.data.objects.new("LWCam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    for h in hide:
        if bpy.data.objects.get(h):
            bpy.data.objects[h].hide_render = True
    tmp = path + ".tile.png"
    tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in shots]
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return kind


def show_hi(parts, on=True):
    """Shows the high-detail parts (and hides the game meshes), for the look renders."""
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = True
    for piece in parts.values():
        for o in piece.values():
            o.hide_render = not on


BAKES = {"Body": dict(size=2048, small=1024, ray=0.30, extrusion=0.12), "Head": dict(size=2048, small=1024, ray=0.20, extrusion=0.08), "Frill": dict(size=1024, small=512, ray=0.10, extrusion=0.03)}
NEON = {"Eyes": Mt.EYE_HEX, "Lantern": Mt.LAMP_HEX, "RingsA": Mt.RING_HEX, "RingsB": Mt.RING_HEX, "RingsC": Mt.RING_HEX, "RingsD": Mt.RING_HEX}


def _fit_uv(obj):
    """A Neon piece wears no map, but Roblox wants its UVs inside the square."""
    uv = obj.data.uv_layers.active
    if not uv:
        obj.data.uv_layers.new(name="UVMap")
        return
    us = [d.uv.x for d in uv.data]
    vs = [d.uv.y for d in uv.data]
    su, sv = max(max(us) - min(us), 1e-6), max(max(vs) - min(vs), 1e-6)
    u0, v0 = min(us), min(vs)
    for d in uv.data:
        d.uv = ((d.uv.x - u0) / su, (d.uv.y - v0) / sv)


def bake_all(parts, lows, only=None):
    import egg_bake as Bk
    saved = Bk.EGG_DIR
    Bk.EGG_DIR = OUT
    os.makedirs(OUT, exist_ok=True)
    setup_gpu()
    try:
        for piece, spec in BAKES.items():
            if only and piece not in only:
                continue
            if piece == "Head":
                hi = list(parts["Head"].values())
            else:
                hi = list(parts[piece].values())
            for o in hi + [lows[piece]]:
                o.hide_viewport = False
                o.hide_render = False
            if piece != "Body":
                Bk._unwrap(lows[piece])
            Bk.bake("LanternWyrm_" + piece, hi, lows[piece], samples=12, **spec)
            for o in hi:
                o.hide_viewport = True
                o.hide_render = True
    finally:
        Bk.EGG_DIR = saved
    for piece in NEON:
        _fit_uv(lows[piece])
        for p in lows[piece].data.polygons:
            p.use_smooth = False


def scrub_fbx(path):
    """The FBX remembers the absolute folder its maps were copied from. Done to the bytes, in place, each machine path becomes filler of the same
    length (so the file's length-prefixed strings stay valid): nothing of this machine is left in it."""
    data = open(path, "rb").read()
    for what in sorted({REPO, os.path.expanduser("~")}, key=len, reverse=True):
        data = data.replace(what.encode(), b"x" * len(what))
    open(path, "wb").write(data)
    return sum(data.lower().count(w) for w in (os.path.basename(os.path.expanduser("~")).lower().encode(), b"/users/"))


def glow_material_for_neon(lows):
    """One shared glow material for every Neon piece (the game colours each by name), so the FBX holds four materials in all."""
    mat = K.glow_material(Mt.LAMP_HEX)
    for piece in NEON:
        o = lows[piece]
        o.data.materials.clear()
        o.data.materials.append(mat)


def export_fbx(lows):
    """assets/guardians/LanternWyrm.fbx: every game piece, skinned, and the skeleton, bound as modelled. The maps go in with it."""
    import lantern_wyrm_motion as M
    M.set_pose({})
    arm = bpy.data.objects[RIG]
    arm.hide_render = False
    arm.hide_viewport = False
    bpy.ops.object.select_all(action="DESELECT")
    for piece, name in GAME_NAMES.items():
        o = lows[piece]
        o.name = name
        o.hide_viewport = False
        o.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT, NAME + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                             primary_bone_axis="Y", secondary_bone_axis="X")
    left = scrub_fbx(path)
    return path, os.path.getsize(path) // 1024, "machine path hits left: %d" % left


from mathutils import Matrix  # noqa: E402
ADD_BONE_FLIP = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, -1)))


def addbone_cframe(parent, bone):
    """A bone's place under its parent as Roblox's importer gives it: Blender's bone-local value with X and Z flipped, in position and rotation alike."""
    arm = bpy.data.objects[RIG]
    rel = arm.data.bones[parent].matrix_local.inverted() @ arm.data.bones[bone].matrix_local
    pos = ADD_BONE_FLIP @ rel.to_translation()
    rot = ADD_BONE_FLIP @ rel.to_3x3() @ ADD_BONE_FLIP
    return [round(x, 5) for x in (*pos, *[rot[i][j] for i in range(3) for j in range(3)])]


def bone_use(lows):
    use = {}
    for piece, o in lows.items():
        weighted = set()
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight > 0:
                    weighted.add(o.vertex_groups[g.group].name)
        for n in weighted:
            use.setdefault(n, []).append((piece, len(weighted)))
    return use


def write_placements(path, lows):
    use = bone_use(lows)
    need = [n for n in BONES if n != "Root" and not any(count > 1 for _, count in use.get(n, []))]
    glow = {"Lantern": Mt.LAMP_HEX, "Eyes": Mt.EYE_HEX, "RingsA": Mt.RING_HEX, "RingsB": Mt.RING_HEX, "RingsC": Mt.RING_HEX, "RingsD": Mt.RING_HEX}
    rgb = lambda h: "Color3.fromRGB(%d, %d, %d)" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda v: "Vector3.new(%s)" % ", ".join(("%.4f" % c).rstrip("0").rstrip(".") for c in v)
    lines = ["-- The Abyssal Lantern Wyrm, the Origin Abyss's guardian, with a skeleton (tools/blender/guardians/lantern_wyrm.py, assets/guardians/LanternWyrm.fbx).",
             "-- Used by GuardianBuilder.storeSkinned for the guardian Pangu (the id stays: saves, records and quests key off it).",
             "return {", '    Rig = "LanternWyrmSkinned",', "    Fit = {"]
    for name in ("Hips", "Head", "Tail6", "RightFrill5"):
        lines.append("        %s = %s," % (name, f(BONES[name][1])))
    lines += ["    },",
              "    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, from Blender's rest pose. The",
              "    -- import is a half turn about Y: a bone-local value is Blender's with X and Z flipped, in position and rotation alike.",
              "    AddBones = {"]
    for n in need:
        parent = BONES[n][0]
        c = addbone_cframe(parent, n)
        lines.append('        %s = { Parent = "%s", CFrame = CFrame.new(%s) },' % (n, parent, ", ".join(("%g" % x) for x in c)))
    lines += ["    },", "    Glow = {"]
    for k, h in glow.items():
        lines.append("        %s = %s," % (k, rgb(h)))
    lines += ["    },", "}"]
    with open(path, "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    return need


def write_report(path, lows):
    import json
    use = bone_use(lows)
    rep = {"Pieces": {}, "Bones": len([n for n in BONES if n != "Root"]), "Joints": len(joints())}
    lo, hi = V((1e9, 1e9, 1e9)), V((-1e9, -1e9, -1e9))
    for piece, o in lows.items():
        pts = _points(o)
        rep["Pieces"][GAME_NAMES[piece]] = {"Triangles": tris(o), "Vertices": len(o.data.vertices), "BonesUsed": len({n for n, lst in use.items() if any(p == piece for p, _ in lst)}),
                                            "Glow": ("#" + NEON[piece]) if piece in NEON else None, "Size": [round(float(x), 2) for x in (pts.max(axis=0) - pts.min(axis=0))]}
        lo = V(map(min, lo, pts.min(axis=0)))
        hi = V(map(max, hi, pts.max(axis=0)))
    rep["Bounds"] = {"Min": [round(x, 2) for x in lo], "Max": [round(x, 2) for x in hi]}
    rep["Triangles"] = sum(p["Triangles"] for p in rep["Pieces"].values())
    rep["MeshParts"] = len(rep["Pieces"])
    with open(path, "w", encoding="utf8") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    return rep


def run_qa(lows, profile="roblox"):
    """blender-asset-qa on each game piece (the folder of its qa_check.py in $LANTERN_QA_DIR)."""
    qa_dir = os.environ.get("LANTERN_QA_DIR") or os.environ.get("CINDER_QA_DIR")
    if not qa_dir:
        return "skipped: set LANTERN_QA_DIR to the folder holding qa_check.py"
    sys.path.insert(0, qa_dir)
    import qa_check
    names = [GAME_NAMES[p] for p in lows]
    r = qa_check.run(objects=names, profile=profile)
    return {"pass": r["pass"], "errors": r["errors"], "warnings": r["warnings"][:24], "zfighting": str(r.get("zfighting"))[:1800], "floating": str(r.get("floating"))[:600]}


def build_final(out_blend=None, placements=None, report=None):
    info, parts, lows = build_lows(real=True)
    bake_all(parts, lows)
    glow_material_for_neon(lows)
    path = export_fbx(lows)
    notes = {}
    if placements:
        notes["AddBones"] = write_placements(placements, lows)
    if report:
        notes["report"] = write_report(report, lows)
    notes["qa"] = run_qa(lows)
    if out_blend:
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    return info, count(lows), path, notes


# ---------------------------------------------------------------- numeric checks
def skin_arrays(lows):
    """Per piece: the bind vertices (Roblox space), each vertex's four bones and weights."""
    import numpy as np
    names = list(BONES)
    index = {n: i for i, n in enumerate(names)}
    out = {}
    for piece, o in lows.items():
        n = len(o.data.vertices)
        bi = np.zeros((n, 4), dtype=np.int64)
        w = np.zeros((n, 4))
        gname = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            for k, g in enumerate(sorted(v.groups, key=lambda x: -x.weight)[:4]):
                bi[v.index, k] = index[gname[g.group]]
                w[v.index, k] = g.weight
        out[piece] = (_points(o), bi, w)
    return out, names


def skinned(arrs, names, pose, shift):
    """Every piece's vertices under a pose: linear blend skinning about each bone's head, as the game's bones do."""
    import numpy as np
    import lantern_wyrm_motion as M
    st = M.fk(pose, shift)
    R = np.array([np.array(st[n][0]) for n in names])
    H = np.array([list(st[n][1]) for n in names])
    H0 = np.array([BONES[n][1] for n in names])
    out = {}
    for piece, (v, bi, w) in arrs.items():
        p = np.zeros_like(v)
        for k in range(4):
            b = bi[:, k]
            p += w[:, k:k + 1] * (H[b] + np.einsum("nij,nj->ni", R[b], v - H0[b]))
        out[piece] = p
    return out


def rot_angle(a, b):
    import lantern_wyrm_motion as M
    return math.degrees((M.mat(a).inverted() @ M.mat(b)).to_quaternion().angle)


def twist_about(e, axis):
    import lantern_wyrm_motion as M
    q = M.mat(e).to_quaternion()
    deg = math.degrees(2 * math.atan2(V((q.x, q.y, q.z)).dot(axis), q.w))
    return (deg + 180) % 360 - 180


def _seg_dist(p, a, b):
    """Distance in the ground plane from p to the segment a-b."""
    ab = V((b.x - a.x, 0, b.z - a.z))
    ap = V((p.x - a.x, 0, p.z - a.z))
    t = max(0.0, min(1.0, ap.dot(ab) / max(ab.dot(ab), 1e-9)))
    c = a + ab * t
    return math.hypot(p.x - c.x, p.z - c.z)


def run_checks(only=None):
    import numpy as np
    import lantern_wyrm_motion as M
    info, parts, lows = build_lows()
    arrs, names = skin_arrays(lows)
    report = {"tris": count(lows)}
    report["bones"] = Bn.checks()
    # the bind symmetric about the long axis: the bones (exact) and the body's and frill's vertices (mirrored, nearest)
    body = _points(lows["Body"])
    mirror = body * np.array([-1, 1, 1])
    from mathutils.kdtree import KDTree
    kd = KDTree(len(body))
    for i, p in enumerate(body):
        kd.insert(V(p), i)
    kd.balance()
    report["body mesh mirror error (max studs)"] = round(max(kd.find(V(p))[2] for p in mirror[::7]), 5)
    fr = _points(lows["Frill"])
    kd2 = KDTree(len(fr))
    for i, p in enumerate(fr):
        kd2.insert(V(p), i)
    kd2.balance()
    report["frill mesh mirror error (max studs)"] = round(max(kd2.find(V(p))[2] for p in (fr * np.array([-1, 1, 1]))[::5]), 4)
    base = {n: (0, 0, 0) for n in M.JOINTS}
    sts = M.state_tables()
    guardian = M.full(*sts["Guardian"], base)
    mv = M.moves()
    ends = M.MOVE_LENGTH
    start_state = {n: "Guardian" for n in mv}
    start_state["Awaken"] = "Dormant"
    end_state = {"CoilLash": "Guardian", "LanternGaze": "Guardian", "VoidSurge": "Guardian", "SerpentLeap": None, "Land": "Guardian", "Awaken": "Guardian", "Enrage": "Enraged", "Weaken": "Weakened"}
    twist_axes = {n: M.rest_dir(n) for n in B.NECK + ["Head"]}
    moves_report = {}
    for name, keys in mv.items():
        if only and name not in only:
            continue
        length = keys[-1]["t"]
        n_frames = int(round(length * 30)) + 1
        res = {"frames": n_frames, "length s": length}
        poses = [M.pose_at(keys, min(f / 30.0, length)) for f in range(n_frames)]
        low_y, low_who = 9e9, ""
        tips_prev = None
        step_max, step_who = 0.0, ""
        head_speed, head_drop, lamp_speed = [], [], []
        tw = {n: 0.0 for n in twist_axes}
        trunk_x = []
        prev_head = None
        for f, (pose, shift) in enumerate(poses):
            t = f / 30.0
            airborne = name == "SerpentLeap" and t > 0.82
            sk = skinned(arrs, names, pose, shift)
            if not airborne:
                for piece, p in sk.items():
                    if piece in ("Eyes",):
                        continue
                    mi = int(np.argmin(p[:, 1]))
                    if p[mi, 1] < low_y:
                        low_y, low_who = float(p[mi, 1]), "%s (%s)" % (piece, names[int(arrs[piece][1][mi, int(np.argmax(arrs[piece][2][mi]))])])
            st = M.fk(pose, shift)
            tips = {n: M.tip(st, n) for n in BONES if n != "Root"}
            if tips_prev:
                for n, v in tips.items():
                    d = (v - tips_prev[n]).length
                    if d > step_max:
                        step_max, step_who = d, "%s frame %d" % (n, f)
            head_speed.append(0.0 if tips_prev is None else (tips["Head"] - tips_prev["Head"]).length * 30)
            head_drop.append(0.0 if tips_prev is None else (tips_prev["Head"].y - tips["Head"].y) * 30)
            tips_prev = tips
            for n, ax in twist_axes.items():
                tw[n] = max(tw[n], abs(twist_about(pose[n], ax)))
            trunk_x.append([st[n][1].x for n in B.SPINE_BACK])
        res["lowest vertex y (studs, ground frames)"] = round(low_y, 2)
        res["lowest vertex belongs to"] = low_who
        res["biggest bone-end step (studs per frame)"] = (round(step_max, 2), step_who)
        res["max twist (deg) neck and head"] = {k: round(v, 1) for k, v in tw.items() if v > 20}
        res["start pose vs %s (max deg, bone)" % start_state[name]] = max((round(rot_angle(M.full(*sts[start_state[name]], base)[n][:3], M.full(*poses[0], guardian)[n][:3]), 1), n) for n in M.JOINTS)
        if end_state[name]:
            tgt = M.full(*sts[end_state[name]], base)
            fl = M.full(*poses[-1], tgt)
            res["end pose vs %s (max deg, bone)" % end_state[name]] = max((round(rot_angle(tgt[n][:3], fl[n][:3]), 1), n) for n in M.JOINTS)
        if name in M.CONTACT:
            at = int(round(M.CONTACT[name] * 30))
            if name == "CoilLash":
                res["head-tip speed peak frame / contact frame"] = (int(np.argmax(head_speed)), at, round(max(head_speed), 0))
            elif name == "LanternGaze":
                res["head thrust: hips slide peak frame / contact frame"] = (int(np.argmin([p[1][1] for p in poses])), at)
            elif name == "VoidSurge":
                res["head downstroke peak frame / contact frame"] = (int(np.argmax(head_drop)), at, round(max(head_drop), 0))
            elif name == "SerpentLeap":
                res["air blend crosses 0.5 (frame) / leave-ground frame"] = (next(f for f in range(n_frames) if M.spec_at(keys, f / 30.0)[0]["air"] >= 0.2), at)
            elif name == "Land":
                res["head lowest frame / contact frame"] = (int(np.argmin([M.tip(M.fk(*p), "Head").y for p in poses])), at)
            elif name in ("Weaken",):
                hy = [M.tip(M.fk(*p), "Head").y for p in poses]
                res["head fastest drop frame / contact frame"] = (int(np.argmax([hy[i] - hy[i + 1] for i in range(len(hy) - 1)])) + 1, at)
            elif name == "Enrage":
                res["head-tip speed peak frame (the rear-up) / slam frame"] = (int(np.argmax(head_speed)), at)
        if name == "CoilLash":
            # the lash's wave down the length: when each trunk bone's sideways swing peaks after the blow
            first = []
            for j, n in enumerate(B.SPINE_BACK):
                ref = poses[at][0][n]
                first.append(next((f for f in range(at, n_frames) if rot_angle(poses[f][0][n], ref) > 3.0), None))
            res["lash wave: first frame after the blow at which a trunk bone has turned 3 degrees (Body1, Body6, Body11, Tail6, Tail11)"] = [first[0], first[5], first[10], first[15], first[21]]
        moves_report[name] = res
    report["moves"] = moves_report
    # the states: lowest vertex
    states_report = {}
    for name, (pose, shift) in sts.items():
        sk = skinned(arrs, names, pose, shift)
        states_report[name] = round(min(float(p[:, 1].min()) for k, p in sk.items() if k != "Eyes"), 2)
    report["lowest vertex y per state pose"] = states_report
    # the walk and the run on a straight path, a circle and an S, each at its speed
    gaits = {}
    up = V((0, 1, 0))
    paths = {"straight": lambda t, v: V((0, 0, -v * t)),
             "circle (radius 7)": lambda t, v: V((7.0 - 7.0 * math.cos(v * t / 7.0), 0, -7.0 * math.sin(v * t / 7.0))),
             "S (6 studs each way)": lambda t, v: V((6.0 * math.sin(v * t / 14.0), 0, -v * t))}
    guardian_pose = M.state_pose("Guardian")[0]
    for gname, speed in (("walk", 12.0), ("run", 28.0)):
        res = {}
        for pname, path in paths.items():
            tr = M.Trail()
            worst_follow, worst_fk, worst_amp, lowy = 0.0, 0.0, 0.0, 9e9
            dt = 1.0 / 30.0
            for f in range(int(9 / dt)):
                t = f * dt
                pos = path(t, speed)
                fwd = (path(t + 1e-3, speed) - pos).normalized()
                right = fwd.cross(up)
                tr.push(pos)
                if tr.s_now < 70.0:
                    continue
                to_local = lambda p, pos=pos, fwd=fwd, right=right: V(((p - pos).dot(right), 0.0, -(p - pos).dot(fwd)))
                for wave in (False, True):
                    pts = M.chain_points(tr, speed, to_local, wave=wave)
                    pose = M.chain_pose(pts)
                    st = M.fk({**pose, "Hips": (0, 0, 0)}, (0.0, 0.0))
                    fk_pts = [st["Body1"][1]] + [M.tip(st, n) for n in B.SPINE_BACK]
                    dev = 0.0
                    path_local = [to_local(q) for q in tr.pts[-260:]] + [to_local(tr.now)]
                    for j in range(len(pts)):
                        dev = max(dev, min(_seg_dist(fk_pts[j], a_, b_) for a_, b_ in zip(path_local, path_local[1:])))
                    if not wave:
                        worst_follow = max(worst_follow, dev)
                    else:
                        worst_amp = max(worst_amp, dev)
                        worst_fk = max(worst_fk, max((fk_pts[j] - pts[j]).length for j in range(len(pts))))
                        sk = skinned({"Body": arrs["Body"]}, names, {**guardian_pose, **pose}, (0.0, 0.0))
                        lowy = min(lowy, float(sk["Body"][:, 1].min()))
            res[pname] = {"follow-the-leader deviation, wave off (max studs)": round(worst_follow, 3), "wave on: biggest sideways offset from the leader's path (studs)": round(worst_amp, 2),
                          "FK reproduces the laid joints (max studs)": round(worst_fk, 3), "lowest body vertex y": round(lowy, 2)}
        a_, lam = M.wave_params(speed)
        # a wave is world-fixed and cyclic: the pose at s and at s + wavelength is the same
        tr1, tr2 = M.Trail(), M.Trail()
        for k in range(300):
            tr1.push(V((0, 0, -k * 0.5)))
            tr2.push(V((0, 0, -(k * 0.5 + lam))))
        loc = lambda tr: (lambda p: V((p.x, 0.0, p.z - tr.now.z)))
        p1 = M.chain_pose(M.chain_points(tr1, speed, loc(tr1)))
        p2 = M.chain_pose(M.chain_points(tr2, speed, loc(tr2)))
        res["wave amplitude (studs) / wavelength (studs)"] = (round(a_, 2), round(lam, 1))
        res["cycle closes: pose at s vs s + wavelength (max deg)"] = round(max(rot_angle(p1[n], p2[n]) for n in p1), 4)
        gaits[gname] = res
    report["gaits"] = gaits
    return report


def pose_sheet(path, specs, size=420, views=None):
    """The wyrm in clay in each given spec, from the side and from above."""
    import lantern_wyrm_motion as M
    info, parts, lows = build_lows()
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    views = views or ((-90, 4, 120, (0, 10, 4)), (-40, 22, 110, (0, 8, 4)), (0, 89, 120, (0, 0, 4)))
    for name, spec in specs:
        pose, shift = M.solve(spec)
        M.set_pose(pose, shift)
        for yaw, pitch, dist, c in views:
            tiles.append(T._shot(scene, cam, yaw, pitch, dist, W.rb(*c), size, tmp))
    T._sheet(tiles, len(views), path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def _frame_of(keys_or_poses, times, axes):
    """A camera centre and distance that hold every joint of the wyrm over `times` (axes: the two world axes the view shows)."""
    import lantern_wyrm_motion as M
    lo, hi = [1e9] * 3, [-1e9] * 3
    for t in times:
        pose, shift = keys_or_poses(t)
        st = M.fk(pose, shift)
        for n, (r, p) in st.items():
            q = M.tip(st, n) if n in ("Head", "Tail11", "Lure3") else p
            for pt in (p, q):
                for i in range(3):
                    lo[i], hi[i] = min(lo[i], pt[i]), max(hi[i], pt[i])
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = max(hi[i] - lo[i] for i in axes) / 2 + 5.0
    return c, ext / 0.257 * 1.06


def strips(names, out_dir, size=360, side_only=False):
    """A strip of frames of each move from three-quarter, side and above (the lows in clay), for judging the motion by eye."""
    import lantern_wyrm_motion as M
    info, parts, lows = build_lows()
    scene, cam = T._review_scene(size)
    allm = M.moves()
    for name in names:
        keys = allm[name]
        times = M.STRIP_TIMES[name]
        fn = lambda t: M.pose_at(keys, t)
        c_side, d_side = _frame_of(fn, [i * keys[-1]["t"] / 30 for i in range(31)], (1, 2))
        c_top, d_top = _frame_of(fn, [i * keys[-1]["t"] / 30 for i in range(31)], (0, 2))
        views = ((-38, 16, max(d_side, d_top) * 0.95, c_side), (-90, 3, d_side, c_side), (0, 89, d_top, c_top))
        if side_only:
            views = views[:2]
        tiles = []
        for yaw, pitch, dist, c in views:
            for t in times:
                pose, shift = M.pose_at(keys, t)
                M.set_pose(pose, shift)
                tiles.append(T._shot(scene, cam, yaw, pitch, dist, W.rb(*c), size, os.path.join(out_dir, "_t.png")))
        T._sheet(tiles, len(times), os.path.join(out_dir, "strip_%s.png" % name), size)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    stage = argv[0] if argv else "form"
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(REPO, "renders", "lantern_wyrm")
    os.makedirs(out_dir, exist_ok=True)
    if stage == "form":
        info, parts, lows = build_lows()
        print("INFO", info, count(lows))
        review(os.path.join(out_dir, "form.png"), [(-90, 5, 100, (0, 3, 8)), (-35, 14, 34, (0, 4, -24)), (-60, 20, 50, (0, 3, 30)), (0, 90, 100, (0, 3, 8)), (0, 6, 30, (0, 4, -27)),
                                                    (-60, 50, 30, (0, 4, -27))])
    if stage == "states":
        import lantern_wyrm_motion as M
        names = argv[1].split(",") if len(argv) > 1 and not argv[1].startswith("--") else list(M.state_specs())
        pose_sheet(os.path.join(out_dir, "states.png"), [(n, M.state_spec(n)) for n in names])
    if stage == "strip":
        strips(argv[1].split(","), out_dir, side_only="--side" in argv)
    if stage == "look":
        WANT = True
        info, parts, lows = build_lows(real=True)
        show_hi(parts)
        print(info)
        shots = [(-90, 4, 100, (0, 5, 10)), (-35, 10, 36, (0, 4, -24)), (-60, 20, 56, (0, 4, 30)), (0, 6, 24, (0, 4, -26)), (-70, 10, 24, (0, 4, -26)), (-120, 25, 26, (0, 4, -10))]
        print(look(os.path.join(out_dir, "look.png"), shots, size=560, samples=40))
    if stage == "final":
        blend = os.path.join(out_dir, "LanternWyrm_final.blend")
        pl = argv[argv.index("--placements") + 1] if "--placements" in argv else None
        rp = argv[argv.index("--report") + 1] if "--report" in argv else None
        import json
        print("FINAL " + json.dumps(build_final(blend, pl, rp), default=str))
    if stage == "scrub":
        print("scrubbed, hits left:", scrub_fbx(os.path.join(OUT, NAME + ".fbx")))
    if stage == "checks":
        import json
        only = argv[1].split(",") if len(argv) > 1 and not argv[1].startswith("--") else None
        rep = run_checks(only)
        print("CHECKS " + json.dumps(rep, indent=1, default=str))
    if stage == "clips":
        import lantern_wyrm_motion as M
        path = argv[1] if len(argv) > 1 else os.path.join(out_dir, "LanternWyrmClips.lua")
        print(M.write_clips(path))

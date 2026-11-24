"""Tiangou the Moon-Eater, rebuilt (v3): model, skeleton, weights, maps, export (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/tiangou_v3.py -- <stage> [--out DIR]

A powerful heavenly hound, about 14 studs at the shoulder, 22 studs from its origin to its nose when it stands: a deep barrel chest and a heavy
shoulder and neck, a strong loin, long digitigrade legs with big paws, a long head with a strong muzzle and a jaw that really opens, ears that
stand tall, a coat that is the midnight sky (deep blue, faint constellations, silvered where the moon falls) with white fire for a ruff, a plume
and feathered legs; and above its shoulders the eclipse it made: a black disc ringed by a corona of fire, floating on a stalk of fire.

Authored in Roblox studs, facing -Z, feet on y = 0, left is -X. The skeleton is tiangou_v3_bones.py, the motion tiangou_v3_motion.py.
Stages: study (tiangou_v3_study.py) | form | cache | states | strip | checks | final | clips | gait | scrub (see main at the bottom).
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
import tiangou_v3_materials as Mt  # noqa: E402
import tiangou_v3_model as Md  # noqa: E402
from tiangou_v3_bones import BONES, ECLIPSE, STREAMS, joints  # noqa: E402

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "TiangouV3"
RIG = "TiangouV3Rig"
OUT = G.OUT_DIR
REPO = W.REPO
CACHE = os.path.join(REPO, "renders", "tiangou_v3", "lows.blend")

CLAY = {"coat": (0.10, 0.13, 0.30), "fire": (0.85, 0.9, 1.0), "tooth": (0.8, 0.76, 0.62), "star": (0.9, 0.95, 1.0), "nose": (0.02, 0.02, 0.03), "nostril": (0.0, 0.0, 0.0), "eyes": (1.0, 0.7, 0.1), "pupils": (0.02, 0.0, 0.0),
        "eclipse": (0.03, 0.03, 0.06), "corona": (0.8, 0.9, 1.0), "core": (1.0, 0.85, 0.5)}
REAL = {}


def _clay(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


def _mat(kind):
    return REAL[kind] if kind in REAL else _clay("TG3Clay_" + kind, CLAY[kind])


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
    import numpy as np
    n = len(obj.data.vertices)
    co = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)


def _write_groups(obj, per_vertex):
    obj.vertex_groups.clear()
    groups = {}
    for i, w in enumerate(per_vertex):
        top = sorted(((v, k) for k, v in w.items() if v > 0.02), reverse=True)[:4]
        tot = sum(v for v, _ in top) or 1.0
        for v, k in top:
            if k not in groups:
                groups[k] = obj.vertex_groups.new(name=k)
            groups[k].add([i], v / tot, "REPLACE")


def bind_rigid(obj, bone):
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


# how far a bone's own influence reaches round it (studs): the distance to it is judged against this, so a fat thigh and a thin shin share the
# vertices between them in proportion
REACH = {"Hips": 3.6, "SpineA": 3.5, "SpineB": 3.6, "Chest": 4.4, "Neck1": 2.9, "Neck2": 2.5, "Neck3": 2.2, "Scapula": 2.2, "Upper": 1.7, "Lower": 1.2, "Paw": 0.9,
         "Thigh": 2.6, "Shin": 1.4, "Meta": 0.85, "Toes": 1.0, "Head": 2.2, "Jaw": 1.0, "Ear": 0.8, "Tail": 1.2}


def reach_of(name):
    for key in ("Scapula", "Upper", "Lower", "Paw", "Thigh", "Shin", "Meta", "Toes", "Ear", "Tail", "Neck1", "Neck2", "Neck3", "Hips", "SpineA", "SpineB", "Chest", "Head", "Jaw"):
        if key in name:
            return REACH[key]
    return 1.0


def weights_by(pts, names, falloff=0.45, normalise=True):
    """{bone: weight} per point (as a list of dicts): the nearest bone (distance over its reach) leads, the others share by a Gaussian of how much
    farther they are."""
    import numpy as np
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    d = np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)
    if normalise:
        d = d / np.array([reach_of(n) for n in names])[None, :]
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.0)
    w /= w.sum(axis=1, keepdims=True)
    return w


def smooth_weights(obj, w, names, rounds=3, amount=0.55):
    """Averages each vertex's weights with its neighbours' (a few rounds): the hand-over at a joint spreads over several studs."""
    import numpy as np
    n = len(obj.data.vertices)
    e = np.zeros(len(obj.data.edges) * 2, dtype=np.int64)
    obj.data.edges.foreach_get("vertices", e)
    e = e.reshape(-1, 2)
    for _ in range(rounds):
        acc = np.zeros_like(w)
        cnt = np.zeros((n, 1))
        np.add.at(acc, e[:, 0], w[e[:, 1]])
        np.add.at(acc, e[:, 1], w[e[:, 0]])
        np.add.at(cnt, e[:, 0], 1)
        np.add.at(cnt, e[:, 1], 1)
        w = (1 - amount) * w + amount * acc / np.maximum(cnt, 1)
    return w


def bind_smooth(obj, names, falloff=0.45, rounds=3, amount=0.55, spans=None):
    pts = _points(obj)
    w = weights_by(pts, names, falloff)
    w = smooth_weights(obj, w, names, rounds, amount)
    _write_groups(obj, [{names[j]: float(w[i, j]) for j in range(len(names))} for i in range(len(pts))])


def bind_table(obj, table):
    _write_groups(obj, [table[i] for i in range(len(obj.data.vertices))])


def attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


BODY_BONES = ["Hips", "SpineA", "SpineB", "Chest", "Neck1", "Neck2", "Neck3"] + ["Tail%d" % i for i in range(1, 7)] + \
    ["Front%s%s" % (t, p) for t in ("Left", "Right") for p in ("Scapula", "Upper", "Lower", "Paw", "Toes")] + \
    ["Back%s%s" % (t, p) for t in ("Left", "Right") for p in ("Thigh", "Shin", "Meta", "Toes")]
HEAD_BONES = ["Head", "Neck3", "LeftEarA", "LeftEarB", "RightEarA", "RightEarB"]


def _toes_of(point):
    """The toes bone nearest a claw's point."""
    best, who = 1e9, None
    for n in ("FrontLeftToes", "FrontRightToes", "BackLeftToes", "BackRightToes"):
        h = V(BONES[n][1])
        d = (h - V(point)).length
        if d < best:
            best, who = d, n
    return who


# ---------------------------------------------------------------- the high-detail parts
def _hi(hi, name, coll, kinds, smooth=True):
    return hi.object(name, coll, [_mat(k) for k in kinds], smooth=smooth, weld=0)


def build_hi(coll, P=None, voxel=0.15):
    P = P or Md.default_params()
    parts = {}
    body = Md.hi_blob("TG3_Body", coll, _mat("coat"), Md.body_lobes(P), voxel)
    G.soften(body, 28)
    skull = Md.hi_blob("TG3_Skull", coll, _mat("coat"), Md.skull_lobes(P), voxel * 0.4, 0.9, 0.006)
    G.soften(skull, 4)
    jaw = Md.hi_blob("TG3_Jaw", coll, _mat("coat"), Md.jaw_lobes(P), voxel * 0.4, 0.9, 0.006)
    G.soften(jaw, 3)
    iris, pupil, lids = Md.eyes(P, skull)
    up, low = Hm.Hi(), Hm.Hi()
    Md.teeth(P, up, low)
    claw = Hm.Hi()
    Md.claws(claw)
    nose = Hm.Hi()
    Md.nose_pad(nose, P)
    parts["Pelt"] = {"body": body, "claws": _hi(claw, "TG3_Claws", coll, ["tooth"]), "stars": _hi(Md.constellations(body), "TG3_Stars", coll, ["star"])}
    parts["Skull"] = {"skull": skull, "jaw": jaw, "lids": _hi(lids, "TG3_Lids", coll, ["coat"]), "teeth_up": _hi(up, "TG3_TeethUp", coll, ["tooth"]),
                      "teeth_low": _hi(low, "TG3_TeethLow", coll, ["tooth"]), "nose": _hi(nose, "TG3_Nose", coll, ["nose", "nostril"])}
    fire = Md.build_fire(P)
    parts["Fire"] = {"fire": _hi(fire.hi, "TG3_Fire", coll, ["fire"])}
    parts["Fire"]["fire"]["spans"] = repr(fire.spans)
    parts["Eclipse"] = {"disc": _hi(Md.eclipse_disc(), "TG3_Disc", coll, ["eclipse"])}
    outer, spans, core = Md.corona(P)
    parts["Corona"] = {"corona": _hi(outer, "TG3_Corona", coll, ["corona"])}
    parts["Corona"]["corona"]["spans"] = repr(spans)
    parts["CoronaCore"] = {"core": _hi(core, "TG3_Core", coll, ["core"])}
    parts["Eyes"] = {"iris": _hi(iris, "TG3_Iris", coll, ["eyes"])}
    parts["Pupils"] = {"pupil": _hi(pupil, "TG3_Pupil", coll, ["pupils"])}
    for o in (body, skull, jaw):
        o["keep"] = False
    return parts


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


def _clean(obj, fix_winding=False):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    if fix_winding:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # loose vertices and tiny islands (a voxel remesh leaves a few at thin tips) are removed
    bm.verts.ensure_lookup_table()
    seen, drop = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        comp, stack = [], [v]
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        if len(comp) < 12 and len(bm.verts) > 200:
            drop += comp
    if drop:
        bmesh.ops.delete(bm, geom=drop, context="VERTS")
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


PLANS = {"Pelt": [("body", 17000), ("claws", None)], "Skull": [("skull", 6800), ("jaw", 1900), ("lids", 500), ("teeth_up", None), ("teeth_low", None), ("nose", None)]}


def _fire_weights(obj, spans):
    import numpy as np
    pts = _points(obj)
    table = [None] * len(pts)
    names_all = [n for n in BONES if n != "Root"]
    for a, b, bones in spans:
        bones = [n for n in dict.fromkeys(bones)]
        w = weights_by(pts[a:b], bones, 0.9, normalise=False)
        for i in range(a, b):
            table[i] = {bones[j]: float(w[i - a, j]) for j in range(len(bones))}
    for i in range(len(table)):
        if table[i] is None:
            table[i] = {"Chest": 1.0}
    bind_table(obj, table)


def _corona_weights(obj, spans):
    pts = _points(obj)
    table = [None] * len(pts)
    for a, b, ang in spans:
        for i in range(a, b):
            if ang is None:
                table[i] = {"EclipseRing": 1.0}
        if ang is not None:
            k = int(round(ang / (TAU / STREAMS))) % STREAMS + 1
            names = ["EclipseRing", "Stream%dA" % k, "Stream%dB" % k]
            # a streamer lies between two bones' angles: share by the nearest two
            kk = ang / (TAU / STREAMS)
            lo, hi = int(math.floor(kk)) % STREAMS + 1, int(math.ceil(kk)) % STREAMS + 1
            names = ["EclipseRing"] + sum([["Stream%dA" % j, "Stream%dB" % j] for j in dict.fromkeys((lo, hi))], [])
            w = weights_by(pts[a:b], names, 0.9, normalise=False)
            for i in range(a, b):
                table[i] = {names[j]: float(w[i - a, j]) for j in range(len(names))}
    bind_table(obj, table)


def make_lows(parts, coll):
    lows = {}
    for piece, plan in PLANS.items():
        made = []
        for key, target in plan:
            c = _copy(parts[piece][key], "low_%s_%s" % (piece.lower(), key), coll)
            _reduce(c, target)
            _clean(c, fix_winding=key in ("lids", "nose", "teeth_up", "teeth_low"))
            if key == "body":
                bind_smooth(c, BODY_BONES, 0.5, 3, 0.5)
            elif key == "skull":
                bind_smooth(c, HEAD_BONES, 0.28, 1, 0.35)
            elif key in ("jaw", "teeth_low"):
                bind_rigid(c, "Jaw")
            elif key in ("lids", "teeth_up", "nose"):
                bind_rigid(c, "Head")
            elif key == "claws":
                pts = _points(c)
                bind_table(c, [{_toes_of(p): 1.0} for p in pts])
            made.append(c)
        lows[piece] = _join(made, "TG3_%sLow" % piece)
    import ast
    fire = _copy(parts["Fire"]["fire"], "low_fire", coll)
    _fire_weights(fire, ast.literal_eval(parts["Fire"]["fire"]["spans"]))
    lows["Fire"] = fire
    cor = _copy(parts["Corona"]["corona"], "low_corona", coll)
    _corona_weights(cor, ast.literal_eval(parts["Corona"]["corona"]["spans"]))
    lows["Corona"] = cor
    for key, bone, src in (("Eclipse", "EclipseRing", "Eclipse"), ("CoronaCore", "EclipseRing", "CoronaCore"), ("Eyes", "Eyes", "Eyes"), ("Pupils", "Eyes", "Pupils")):
        c = _copy(list(parts[src].values())[0], "low_" + key, coll)
        bind_rigid(c, bone)
        lows[key] = c
    return lows


GAME_NAMES = {k: k for k in ("Pelt", "Skull", "Fire", "Eclipse", "Corona", "CoronaCore", "Eyes", "Pupils")}


def build_lows(real=False, voxel=0.15, params=None):
    from tiangou_v2 import clear
    clear()
    coll = bpy.data.collections.new("TiangouV3")
    bpy.context.scene.collection.children.link(coll)
    if real:
        REAL.clear()
        REAL.update(Mt.all_materials())
    build_skeleton(coll)
    parts = build_hi(coll, params, voxel)
    lows = make_lows(parts, coll)
    from lantern_wyrm import drop_zfighting
    print("hidden coplanar triangles removed:", drop_zfighting(lows))
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o not in lows.values():
            o.hide_render = True
            o.hide_viewport = True
    for o in lows.values():
        attach(o)
    return parts, lows


def cache():
    parts, lows = build_lows()
    for k, o in lows.items():
        o.name = o.data.name = "LOW_" + k
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=CACHE)
    return {k: tris(o) for k, o in lows.items()}


def load_cache():
    bpy.ops.wm.open_mainfile(filepath=CACHE)
    return {k: bpy.data.objects["LOW_" + k] for k in GAME_NAMES}


def count(lows):
    out, infl = {}, 0
    for k, o in lows.items():
        out[k] = tris(o)
        infl = max(infl, max((len(v.groups) for v in o.data.vertices), default=0))
    out["total"] = sum(v for v in out.values())
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
    """Colour renders with the real shaders in a cold moonlit dusk with a faint warm rim."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    kind = setup_gpu()
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    world = bpy.data.worlds.get("TG3World") or bpy.data.worlds.new("TG3World")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.20, 0.25, 0.40, 1)
    bg.inputs[1].default_value = 0.9
    scene.world = world
    for name, energy, rot, col in (("TG3Key", 5.0, (55, 0, 30), (0.78, 0.86, 1.0)), ("TG3Rim", 3.0, (65, 0, 215), (1.0, 0.82, 0.6))):
        if not bpy.data.objects.get(name):
            d = bpy.data.lights.new(name, "SUN")
            d.energy = energy
            d.color = col
            o = bpy.data.objects.new(name, d)
            o.rotation_euler = tuple(math.radians(a) for a in rot)
            scene.collection.objects.link(o)
    cam = bpy.data.objects.get("TG3Cam")
    if not cam:
        data = bpy.data.cameras.new("TG3Cam")
        data.lens = 60
        cam = bpy.data.objects.new("TG3Cam", data)
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
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = True
    for piece in parts.values():
        for o in piece.values():
            o.hide_render = not on


def closeups(path, hi=True, flat=False, size=520):
    """Head from the front, the side and three-quarters, the chest and neck join, the ruff and the plume (the high-detail model with the real shaders, or with
    flat=True the baked game meshes in Roblox-like flat lighting)."""
    shots = [(-8, 4, 17, (0, 16, -18.5)), (-90, 3, 17, (0, 16, -18)), (-40, 8, 18, (0, 16, -17.5)), (-62, 8, 24, (0, 11.5, -8.5)), (-50, 14, 26, (0, 15, -10)), (150, 12, 42, (0, 10, 12))]
    if flat:
        flat_scene(size)
        scene, cam = bpy.context.scene, bpy.data.objects["TG3Cam"]
        tmp = path + ".tile.png"
        tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in shots]
        T._sheet(tiles, 3, path, size)
        flat_restore()
        if os.path.exists(tmp):
            os.remove(tmp)
    else:
        look(path, shots, size=size, samples=40, columns=3)


def flat_scene(size):
    """Roblox-like flat lighting: every baked piece shows its colour map unlit (an emission of it), every Neon piece its own colour; no shadows, no specular."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    setup_gpu()
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    world = bpy.data.worlds.get("TG3Flat") or bpy.data.worlds.new("TG3Flat")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.2, 0.3, 0.5, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    cam = bpy.data.objects.get("TG3Cam")
    if not cam:
        data = bpy.data.cameras.new("TG3Cam")
        data.lens = 60
        cam = bpy.data.objects.new("TG3Cam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in GAME_NAMES:
            o.hide_render = False
            if o.name in NEON:
                # a Neon piece of its own colour (the pieces share one glow material in the FBX)
                hx = NEON[o.name]
                tmp = bpy.data.materials.new("FlatNeon_" + o.name)
                tmp.use_nodes = True
                tn = tmp.node_tree
                for nd in list(tn.nodes):
                    tn.nodes.remove(nd)
                out = tn.nodes.new("ShaderNodeOutputMaterial")
                em = tn.nodes.new("ShaderNodeEmission")
                em.inputs["Color"].default_value = (*[(int(hx[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)], 1)
                tn.links.new(em.outputs[0], out.inputs["Surface"])
                FLAT_UNDO.append(("swap", o, list(o.data.materials)))
                o.data.materials.clear()
                o.data.materials.append(tmp)
                continue
            mats = []
            for m in o.data.materials:
                t = m.node_tree
                out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
                img = t.nodes.get("color")
                em = t.nodes.new("ShaderNodeEmission")
                if img is not None:
                    t.links.new(img.outputs["Color"], em.inputs["Color"])
                old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
                t.links.new(em.outputs[0], out.inputs["Surface"])
                mats.append((t, out, old, em))
            FLAT_UNDO.append(mats)


FLAT_UNDO = []


def flat_restore():
    for mats in FLAT_UNDO:
        if isinstance(mats, tuple):
            _, o, old = mats
            o.data.materials.clear()
            for m in old:
                o.data.materials.append(m)
            continue
        for t, out, old, em in mats:
            t.nodes.remove(em)
            if old is not None:
                t.links.new(old, out.inputs["Surface"])
    FLAT_UNDO.clear()


def posed_heads(path, size=420):
    """The deformed head and neck (the cached lows in clay, skinned by the real weights) at the Bite's contact, the Howl's peak and the Awaken's yawn, from the
    side and from three-quarters: for judging the jaw's and the neck's skinning."""
    import tiangou_v3_motion as M
    load_cache()
    scene, cam = T._review_scene(size)
    mv = M.moves()
    tmp = path + ".tile.png"
    tiles = []
    for name, t in (("Bite", 0.47), ("Bite", 0.50), ("EclipseHowl", 1.0), ("Awaken", 2.3)):
        pose, shift, _ = M.sample(mv[name], t)
        M.set_pose(pose, shift)
        st = M.fk(pose, shift)
        head = M.tip(st, "Head")
        c = (st["Neck2"][1] + head) / 2
        for yaw, pitch in ((-90, 4), (-40, 12)):
            tiles.append(T._shot(scene, cam, yaw, pitch, 46, W.rb(c.x, c.y, c.z), size, tmp))
    T._sheet(tiles, 4, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def head_turntable(path, size=420):
    """Four angles of the head (front, three-quarter, side, back three-quarter) from the baked game meshes."""
    shots = [(-4, 6, 15, (0, 16, -18.5)), (-45, 8, 16, (0, 16, -18)), (-90, 4, 16, (0, 16, -18)), (-140, 12, 18, (0, 16.5, -16))]
    look(path, shots, size=size, samples=36, columns=4)


# ---------------------------------------------------------------- maps, the FBX, the placements
BAKES = {"Pelt": dict(size=2048, small=1024, ray=0.25, extrusion=0.10), "Skull": dict(size=2048, small=1024, ray=0.18, extrusion=0.06)}
NEON = {"Eclipse": Mt.ECLIPSE_HEX, "Corona": Mt.CORONA_HEX, "CoronaCore": Mt.CORE_HEX, "Eyes": Mt.EYE_HEX, "Pupils": Mt.PUPIL_HEX}


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


def fire_maps(lows):
    """The fire's four maps are drawn, not baked: every tongue shares one gradient on its v (0 at the root to 0.84 at the tip): a warm cream core,
    pale blue-white, a cool blue tip, with a soft flicker across it. The Fire's own UVs (u round the tongue, v along it) overlap on purpose."""
    import numpy as np
    import egg_bake as Bk
    size = 256
    v = (np.arange(size)[:, None] / (size - 1)) / 0.84
    u = np.arange(size)[None, :] / (size - 1)
    t = np.clip(v, 0, 1) * np.ones((1, size))
    stops = [(0.0, Mt.FIRE_ROOT), (0.25, (1.0, 0.96, 0.9)), (0.65, (0.82, 0.9, 1.0)), (1.0, Mt.FIRE_MID)]
    base = np.zeros((size, size, 3))
    for c in range(3):
        base[:, :, c] = np.interp(t[:, 0], [a for a, _ in stops], [b[c] for _, b in stops])[:, None] * np.ones((1, size))
    core = np.sin(u * 6.28318) ** 2 * np.ones((size, 1))
    edge = np.array(Mt.FIRE_TIP)[None, None, :]
    w = ((1.0 - core) * 0.85)[..., None]
    col = np.clip(base * (1 - w) + edge * w, 0, 1) ** (1 / 2.2)
    images = {"color": col, "normal": np.dstack([np.full((size, size), 0.5), np.full((size, size), 0.5), np.ones((size, size))]), "roughness": np.full((size, size, 3), 0.9),
              "metalness": np.zeros((size, size, 3))}
    made = {}
    for key, arr in images.items():
        img = Bk._image("TiangouV3_Fire_" + key, size, key == "color")
        rgba = np.dstack([arr, np.ones((size, size))]).astype(np.float32)
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = os.path.join(OUT, "TiangouV3_Fire_%s.png" % key)
        img.file_format = "PNG"
        img.save()
        made[key] = img
    mat = Bk._baked_material("TiangouV3_Fire", made)
    Bk.wire_baked(mat)
    o = lows["Fire"]
    o.data.materials.clear()
    o.data.materials.append(mat)
    uv = o.data.uv_layers.active
    for d in uv.data:
        d.uv = (min(max(d.uv.x, 0.0), 1.0), min(max(d.uv.y, 0.0), 0.99))


def bake_all(parts, lows):
    import egg_bake as Bk
    saved = Bk.EGG_DIR
    Bk.EGG_DIR = OUT
    os.makedirs(OUT, exist_ok=True)
    setup_gpu()
    try:
        for piece, spec in BAKES.items():
            hi = list(parts[piece].values())
            for o in hi + [lows[piece]]:
                o.hide_viewport = False
                o.hide_render = False
            Bk._unwrap(lows[piece])
            Bk.bake("TiangouV3_" + piece, hi, lows[piece], samples=12, **spec)
            for o in hi:
                o.hide_viewport = True
                o.hide_render = True
    finally:
        Bk.EGG_DIR = saved
    fire_maps(lows)
    for piece in NEON:
        _fit_uv(lows[piece])
        for p in lows[piece].data.polygons:
            p.use_smooth = False


def scrub_fbx(path):
    """The FBX remembers the absolute folder its maps were copied from: done to the bytes, each machine path becomes filler of the same length."""
    data = open(path, "rb").read()
    for what in sorted({REPO, os.path.expanduser("~")}, key=len, reverse=True):
        data = data.replace(what.encode(), b"x" * len(what))
    open(path, "wb").write(data)
    return sum(data.lower().count(w) for w in (os.path.basename(os.path.expanduser("~")).lower().encode(), b"/users/"))


def glow_material_for_neon(lows):
    mat = K.glow_material(Mt.EYE_HEX)
    for piece in NEON:
        o = lows[piece]
        o.data.materials.clear()
        o.data.materials.append(mat)


def export_fbx(lows):
    import tiangou_v3_motion as M
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
    left = -1
    for compression in (15, 24, 33, 42, 51, 60):
        # the maps are embedded as their PNG bytes: by chance a stream can spell a letter run of the checks' pattern, so the compression is stepped until none does
        bpy.context.scene.render.image_settings.compression = compression
        for img in bpy.data.images:
            if img.name.startswith("TiangouV3_") and img.filepath_raw:
                img.save()
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                                 path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                                 primary_bone_axis="Y", secondary_bone_axis="X")
        left = scrub_fbx(path)
        if left == 0:
            break
    return path, os.path.getsize(path) // 1024, "machine path hits left: %d" % left


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
    glow = {k: v for k, v in NEON.items()}
    rgb = lambda h: "Color3.fromRGB(%d, %d, %d)" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda v: "Vector3.new(%s)" % ", ".join(("%.4f" % c).rstrip("0").rstrip(".") for c in v)
    lines = ["-- Tiangou the Moon-Eater, rebuilt, with a skeleton (tools/blender/guardians/tiangou_v3.py, assets/guardians/TiangouV3.fbx).",
             "-- Used by GuardianBuilder.storeSkinned for the guardian Tiangou once it is wired (the live Tiangou keeps Placements/TiangouSkinned.lua until then).",
             "return {", '    Rig = "TiangouV3Skinned",', "    Fit = {"]
    for name in ("Hips", "Head", "BackLeftThigh", "FrontRightLower"):
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
    """blender-asset-qa on each game piece (the folder of its qa_check.py in $TIANGOU_QA_DIR)."""
    qa_dir = os.environ.get("TIANGOU_QA_DIR") or os.environ.get("LANTERN_QA_DIR") or os.environ.get("CINDER_QA_DIR")
    if not qa_dir:
        return "skipped: set TIANGOU_QA_DIR to the folder holding qa_check.py"
    sys.path.insert(0, qa_dir)
    import qa_check
    names = [GAME_NAMES[p] for p in lows]
    r = qa_check.run(objects=names, profile=profile)
    return {"pass": r["pass"], "errors": r["errors"], "warnings": r["warnings"][:24], "zfighting": str(r.get("zfighting"))[:1800], "floating": str(r.get("floating"))[:600]}


def baked_looks(lows, out_dir):
    """Renders of the game meshes as imported (the baked maps and the Neon pieces' flat colours) in the awake pose: a turntable of six views, and the
    head, the ruff and the eclipse close up."""
    import tiangou_v3_motion as M
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in lows.values()
            o.hide_viewport = o.hide_render
    pose, shift, _ = M.build_pose(M.states()["Guardian"])
    M.set_pose(pose, shift)
    turn = [(yaw, 12, 80, (0, 13, -1)) for yaw in (0, 60, 120, 180, 240, 300)]
    look(os.path.join(out_dir, "turntable.png"), turn, size=520, samples=40, columns=3)
    close = [(-35, 10, 22, (0, 16.2, -17.5)), (-90, 4, 22, (0, 16.2, -17.5)), (20, 8, 24, (0, 15.5, -17.0)), (-70, 24, 30, (0, 15, -9)), (150, 16, 34, (0, 13, 10)), (-30, 6, 40, (0, 21, -2))]
    look(os.path.join(out_dir, "closeups.png"), close, size=520, samples=48, columns=3)


def build_final(out_blend=None, placements=None, report=None):
    parts, lows = build_lows(real=True)
    bake_all(parts, lows)
    baked_looks(lows, os.path.join(REPO, "renders", "tiangou_v3"))
    head_turntable(os.path.join(REPO, "renders", "tiangou_v3", "head_turntable.png"))
    glow_material_for_neon(lows)
    path = export_fbx(lows)
    closeups(os.path.join(REPO, "renders", "tiangou_v3", "closeups_flat.png"), flat=True)
    flat_scene(420)
    head_flat = os.path.join(REPO, "renders", "tiangou_v3", "head_turntable_flat.png")
    scene, cam = bpy.context.scene, bpy.data.objects["TG3Cam"]
    tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), 420, head_flat + ".t.png") for y, p, d, c in [(-4, 6, 15, (0, 16, -18.5)), (-45, 8, 16, (0, 16, -18)), (-90, 4, 16, (0, 16, -18)), (-140, 12, 18, (0, 16.5, -16))]]
    T._sheet(tiles, 4, head_flat, 420)
    flat_restore()
    notes = {}
    if placements:
        notes["AddBones"] = write_placements(placements, lows)
    if report:
        notes["report"] = write_report(report, lows)
    notes["qa"] = run_qa(lows)
    if out_blend:
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    return count(lows), path, notes


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
    import tiangou_v3_motion as M
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
    import tiangou_v3_motion as M
    return math.degrees((M.mat(a).inverted() @ M.mat(b)).to_quaternion().angle)


def twist_about(e, axis):
    import tiangou_v3_motion as M
    q = M.mat(e).to_quaternion()
    deg = math.degrees(2 * math.atan2(V((q.x, q.y, q.z)).dot(axis), q.w))
    return (deg + 180) % 360 - 180


def run_checks(only=None):
    import numpy as np
    import tiangou_v3_motion as M
    import tiangou_v3_bones as Bn
    lows = load_cache()
    arrs, names = skin_arrays(lows)
    arrs["Coat"] = tuple(np.concatenate([arrs["Pelt"][i], arrs["Skull"][i]]) for i in range(3))     # the Pelt and the Skull together, for the floor checks
    report = {"tris": count(lows), "bones": Bn.checks()}
    coat = _points(lows["Pelt"])
    mirror = coat * np.array([-1, 1, 1])
    from mathutils.kdtree import KDTree
    kd = KDTree(len(coat))
    for i, p in enumerate(coat):
        kd.insert(V(p), i)
    kd.balance()
    report["coat mesh mirror error (max studs; the voxel remesh is not exactly symmetric)"] = round(max(kd.find(V(p))[2] for p in mirror[::9]), 4)
    solid = {piece: np.ones(len(arrs[piece][0]), dtype=bool) for piece in arrs}
    ground_pieces = ("Coat",)
    guardian = M.full(*M.state_tables()["Guardian"], {n: (0, 0, 0) for n in M.JOINTS})
    sts = M.state_tables()
    mv = M.moves()
    start_state = {n: "Guardian" for n in mv}
    start_state["Awaken"] = "Dormant"
    end_state = {"Bite": "Guardian", "EclipseHowl": "Guardian", "MoonLeap": None, "Land": "Guardian", "Awaken": "Guardian", "Enrage": "Enraged", "Weaken": "Weakened"}
    twist_axes = {n: M.rest_dir(n) for n in Bn.NECK + ["Head", "SpineA", "SpineB", "Chest"] + [l + p for l in M.LEGS for p in ("Upper", "Lower", "Thigh", "Shin") if l + p in BONES]}
    moves_report = {}
    for name, keys in mv.items():
        if only and name not in only:
            continue
        length = keys[-1]["t"]
        nf = int(round(length * 30)) + 1
        poses = [M.sample(keys, min(f / 30.0, length)) for f in range(nf)]
        res = {"frames": nf, "length s": length}
        low_y, low_who = 9e9, ""
        tips_prev, step_max, step_who = None, 0.0, ""
        tw = {n: 0.0 for n in twist_axes}
        head_speed, jaw, nose_z = [], [], []
        ik_err, planted_slide = 0.0, 0.0
        for f, (pose, shift, pl) in enumerate(poses):
            t = f / 30.0
            airborne = name == "MoonLeap" and t > 0.57
            if not airborne:
                sk = skinned({"Coat": arrs["Coat"]}, names, pose, shift)
                ys = sk["Coat"][:, 1]
                mi = int(np.argmin(ys))
                if ys[mi] < low_y:
                    low_y, low_who = float(ys[mi]), names[int(arrs["Coat"][1][mi, int(np.argmax(arrs["Coat"][2][mi]))])]
            st = M.fk(pose, shift)
            tips = {n: M.tip(st, n) for n in BONES if n != "Root"}
            if tips_prev:
                for n, v in tips.items():
                    d = (v - tips_prev[n]).length
                    if d > step_max:
                        step_max, step_who = d, "%s frame %d" % (n, f)
            head_speed.append(0.0 if tips_prev is None else (tips["Head"] - tips_prev["Head"]).length * 30)
            jaw.append(pose.get("Jaw", (0, 0, 0))[0])
            nose_z.append(tips["Head"].z)
            tips_prev = tips
            for n, ax in twist_axes.items():
                tw[n] = max(tw[n], abs(twist_about(pose[n], ax)))
        res["lowest coat vertex y (studs, ground frames)"] = round(low_y, 2)
        res["lowest vertex belongs to"] = low_who
        res["biggest bone-end step (studs per frame)"] = (round(step_max, 2), step_who)
        res["largest twist about its own length (deg)"] = max((round(v, 1), k) for k, v in tw.items())
        base = {n: (0, 0, 0) for n in M.JOINTS}
        s0 = M.full(*sts[start_state[name]], base)
        res["start pose vs %s (max deg, bone)" % start_state[name]] = max((round(rot_angle(s0[n][:3], M.full(poses[0][0], poses[0][1], guardian)[n][:3]), 1), n) for n in M.JOINTS)
        if end_state[name]:
            tgt = M.full(*sts[end_state[name]], base)
            fl = M.full(poses[-1][0], poses[-1][1], tgt)
            res["end pose vs %s (max deg, bone)" % end_state[name]] = max((round(rot_angle(tgt[n][:3], fl[n][:3]), 1), n) for n in M.JOINTS)
        at = int(round(M.CONTACT.get(name, 0) * 30))
        if name == "Bite":
            res["head-tip speed peak frame / jaw shut for good (frame) / contact frame"] = (int(np.argmax(head_speed)), next(f for f in range(10, nf) if jaw[f] > -2.0), at)
            res["nose reach at contact (studs ahead of the origin), height"] = (round(-nose_z[at], 1), round(M.tip(M.fk(*poses[at][:2]), "Head").y, 1))
        elif name == "EclipseHowl":
            hy = [M.tip(M.fk(*p[:2]), "Head").y for p in poses]
            res["head height peak frame / contact frame"] = (int(np.argmax(hy)), at)
            res["front feet leave the ground (frame) / drop back (frame)"] = (next(f for f in range(nf) if not poses[f][2]["FrontLeft"]), next(f for f in range(20, nf) if poses[f][2]["FrontLeft"]))
        elif name == "MoonLeap":
            res["every foot off the ground (first frame) / leave-ground frame"] = (next(f for f in range(nf) if not any(poses[f][2].values())), at)
        elif name == "Land":
            res["forefeet planted on frame 0"] = bool(poses[0][2]["FrontLeft"] and poses[0][2]["FrontRight"])
            res["hind feet down (first frame)"] = next(f for f in range(nf) if poses[f][2]["BackLeft"] and poses[f][2]["BackRight"])
        elif name == "Weaken":
            hh = [p[1][0] for p in poses]
            res["hips first within 0.3 of their final height (frame) / contact frame"] = (next(f for f in range(nf) if all(abs(hh[g] - hh[-1]) < 0.3 for g in range(f, nf))), at)
        moves_report[name] = res
    report["moves"] = moves_report
    st_report = {}
    for name, (pose, shift) in sts.items():
        sk = skinned({"Coat": arrs["Coat"]}, names, pose, shift)
        st_report[name] = round(float(sk["Coat"][:, 1].min()), 2)
    report["lowest coat vertex y per state pose"] = st_report
    gaits = {}
    for gname, g in M.GAITS.items():
        res = {}
        frames = [M.gait_key(gname, i / 96.0) for i in range(97)]
        worst_ik, lowy, step = 0.0, 9e9, 0.0
        slide = {l: 0.0 for l in M.LEGS}
        prev_ball, prev_tips = {}, None
        loop = max(rot_angle(frames[0][0].get(n, (0, 0, 0)), frames[96][0].get(n, (0, 0, 0))) for n in M.JOINTS)
        for i, (pose, shift, pl) in enumerate(frames):
            st = M.fk(pose, shift)
            phase = i / 96.0
            for l in M.LEGS:
                target = M.foot_at(g, l, phase)[0]
                got = st[M.LEG[l]["F"]][1]
                worst_ik = max(worst_ik, (got - target).length)
                q = (phase - g["phase"][l]) % 1.0
                if q < g["duty"] * 0.95 and l in prev_ball and q >= 1.5 / 96:
                    # a planted foot's world spot moves by (body-frame change) - (body travel): the speed times the time between frames
                    dz = got.z - prev_ball[l].z
                    slide[l] = max(slide[l], abs(dz - g["stride"] / 96.0))
                prev_ball[l] = got
            sk = skinned({"Coat": arrs["Coat"]}, names, pose, shift)
            lowy = min(lowy, float(sk["Coat"][:, 1].min()))
            tips = {n: M.tip(st, n) for n in BONES if n != "Root"}
            if prev_tips:
                step = max(step, max((tips[n] - prev_tips[n]).length for n in tips))
            prev_tips = tips
        res["IK reaches every foot target (max error, studs)"] = round(worst_ik, 4)
        res["planted-foot slide per 1/96 cycle step (max studs; 0 = still on its spot)"] = {l: round(v, 4) for l, v in slide.items()}
        res["lowest coat vertex y"] = round(lowy, 2)
        res["cycle closes (max deg, frame 0 vs 1)"] = round(loop, 4)
        res["stride (studs) at speed (studs/s): feet cycle every (s)"] = (g["stride"], g["speed"], round(g["stride"] / g["speed"], 3))
        res["biggest bone-end step per 1/96 cycle"] = round(step, 3)
        gaits[gname] = res
    report["gaits"] = gaits
    return report


def gait_strip(path, size=330):
    """The walk and the gallop from the side: eight frames of a cycle."""
    import tiangou_v3_motion as M
    load_cache()
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    for name in ("walk", "run"):
        for i in range(8):
            pose, shift, _ = M.gait_key(name, i / 8)
            M.set_pose(pose, shift)
            tiles.append(T._shot(scene, cam, -90, 3, 105, W.rb(0, 11, -1), size, tmp))
    T._sheet(tiles, 8, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


# ---------------------------------------------------------------- pose and move renders (the cached lows in clay)
def _extent(poses, axes):
    import tiangou_v3_motion as M
    lo, hi = [1e9] * 3, [-1e9] * 3
    for pose, shift in poses:
        st = M.fk(pose, shift)
        for n in BONES:
            if n == "Root":
                continue
            for pt in (st[n][1], M.tip(st, n)):
                for i in range(3):
                    lo[i], hi[i] = min(lo[i], pt[i]), max(hi[i], pt[i])
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = max(hi[i] - lo[i] for i in axes) / 2 + 4.0
    return c, ext / 0.257 * 1.0


def pose_sheet(path, specs, size=420):
    import tiangou_v3_motion as M
    load_cache()
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    for name, spec in specs:
        pose, shift, _ = M.build_pose(spec)
        M.set_pose(pose, shift)
        c, d = _extent([(pose, shift)], (1, 2))
        for yaw, pitch, dist, cc in ((-90, 4, max(d, 60), c), (-40, 16, max(d, 60) * 1.05, c), (0, 6, max(d, 60) * 0.9, (c[0], c[1], c[2] + 4))):
            tiles.append(T._shot(scene, cam, yaw, pitch, dist, W.rb(*cc), size, tmp))
    T._sheet(tiles, 3, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def strips(names, out_dir, size=360, side_only=False, times=None):
    import tiangou_v3_motion as M
    load_cache()
    scene, cam = T._review_scene(size)
    allm = M.moves()
    for name in names:
        keys = allm[name]
        ts = times or M.STRIP_TIMES[name]
        every = [M.sample(keys, i * keys[-1]["t"] / 30)[:2] for i in range(31)]
        c, d = _extent(every, (1, 2))
        ct, dt = _extent(every, (0, 2))
        views = ((-38, 16, max(d, dt) * 0.95, c), (-90, 3, d, c), (0, 89, dt, ct))
        if side_only:
            views = views[:2]
        tiles = []
        for yaw, pitch, dist, cc in views:
            for t in ts:
                pose, shift, _ = M.sample(keys, t)
                M.set_pose(pose, shift)
                tiles.append(T._shot(scene, cam, yaw, pitch, dist, W.rb(*cc), size, os.path.join(out_dir, "_t.png")))
        T._sheet(tiles, len(ts), os.path.join(out_dir, "strip_%s.png" % name), size)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    stage = argv[0] if argv else "form"
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(REPO, "renders", "tiangou_v3")
    os.makedirs(out_dir, exist_ok=True)
    if stage == "form":
        parts, lows = build_lows()
        print("INFO", count(lows))
        review(os.path.join(out_dir, "form.png"), [(-90, 4, 85, (0, 13, -1)), (-38, 14, 85, (0, 13, -1)), (0, 6, 80, (0, 14, 0)), (90, 4, 85, (0, 13, -1)), (-150, 20, 85, (0, 13, -1)), (-75, 8, 26, (0, 16, -17.5))])
    if stage == "cache":
        print("CACHE", cache())
    if stage == "look":
        parts, lows = build_lows(real=True)
        show_hi(parts)
        shots = [(-90, 4, 85, (0, 13, -1)), (-38, 12, 80, (0, 14, -1)), (0, 5, 75, (0, 15, -2)), (-65, 8, 26, (0, 16, -17.5)), (150, 14, 80, (0, 13, 0)), (-20, 40, 60, (0, 8, -2))]
        print(look(os.path.join(out_dir, "look.png"), shots, size=560, samples=40))

    if stage == "test":
        import tiangou_v3_motion as M
        pose, shift, plants = M.build_pose(M.GUARDIAN)
        print("REST max deg", max(max(abs(x) for x in v) for k, v in pose.items() if k in sum([[M.LEG[l][n] for n in "ULPF"] for l in M.LEGS], [])))
        for l in M.LEGS:
            print(l, {n: tuple(round(x, 2) for x in pose[M.LEG[l][n]]) for n in "ULPF"})
        for name, k in M.states().items():
            pose, shift, plants = M.build_pose(k)
            print(name, plants)
    if stage == "states":
        import tiangou_v3_motion as M
        sts = M.states()
        names = argv[1].split(",") if len(argv) > 1 and not argv[1].startswith("--") else list(sts)
        pose_sheet(os.path.join(out_dir, "states.png"), [(n, sts[n]) for n in names])
    if stage == "strip":
        strips(argv[1].split(","), out_dir, side_only="--side" in argv)
    if stage == "clips":
        import tiangou_v3_motion as M
        path = argv[1] if len(argv) > 1 else os.path.join(out_dir, "TiangouV3Clips.lua")
        print("CLIPS", M.write_clips(path))
    if stage == "gait":
        gait_strip(os.path.join(out_dir, "gait.png"))
    if stage == "checks":
        import json
        only = argv[1].split(",") if len(argv) > 1 and not argv[1].startswith("--") else None
        print("CHECKS " + json.dumps(run_checks(only), indent=1, default=str))
    if stage == "final":
        import json
        blend = os.path.join(out_dir, "TiangouV3_final.blend")
        pl = argv[argv.index("--placements") + 1] if "--placements" in argv else None
        rp = argv[argv.index("--report") + 1] if "--report" in argv else None
        print("FINAL " + json.dumps(build_final(blend, pl, rp), default=str))
    if stage == "scrub":
        print("scrubbed, hits left:", scrub_fbx(os.path.join(OUT, NAME + ".fbx")))
    if stage == "closeups":
        parts, lows = build_lows(real=True)
        show_hi(parts)
        closeups(os.path.join(out_dir, "closeups_hi.png"))
    if stage == "posed":
        posed_heads(os.path.join(out_dir, "posed_heads.png"))

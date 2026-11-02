"""Turning the Eclipse Exorcist's baked game meshes into Roblox items (run inside Blender).

Layered clothing (the robe, the hakama), per item:
- the game-mesh pieces joined into one mesh named after the item;
- skinned to Roblox's blocky R15 skeleton (the 17 body bones of BlockyCharacter.fbx's armature, kept
  as Roblox exported them), at most four bones a vertex;
- <Item>_InnerCage: Roblox's clothing cage template (its topology and UVs untouched) with every
  vertex moved onto the blocky body's own cage, matched by UV (see setup_reference);
- <Item>_OuterCage: the same cage pushed out along its normals past every layer of the item, then
  pushed further wherever any vertex of the item still lies outside it, and smoothed;
- the attachment marker (<Name>_Att) from the blocky character;
- written to assets/ugc/EclipseExorcist/<Item>.fbx in the layout of Roblox's own caged examples.

The seal cord is layered too, worn over the robe: its inner cage is the robe's outer cage (the
surface it was modelled on), so it sits on the robe on any body, and tightens onto the body when
worn alone. (As a rigid accessory it scaled with the body while the robe kept its real thickness,
and on a narrow body the robe swallowed it.) rigid() is kept for a rigid version.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

import ee_kit as K

V = Vector
R15 = ["Root", "HumanoidRootNode", "LowerTorso", "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand",
       "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg",
       "RightLowerLeg", "RightFoot"]
ELBOW, KNEE, ANKLE = 1.031, -0.81, -1.763     # the blocky body's joints (z)
ss = K.smoothstep


def _claim(name):
    """Frees `name` for a new object: Roblox reads the cages and markers by their exact names, so a
    leftover from an earlier run must not push the new one to "name.001"."""
    old = bpy.data.objects.get(name)
    if old is not None:
        data = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Armature):
                bpy.data.armatures.remove(data)


def _copy(src, name):
    _claim(name)
    o = src.copy()
    o.data = src.data.copy()
    o.name = o.data.name = name
    for key in list(o.keys()):
        del o[key]
    bpy.context.scene.collection.objects.link(o)
    return o


# ---------- the reference (once per Blender session) ----------
def setup_reference(ref_dir):
    """Imports Roblox's reference files from `ref_dir` and prepares what the export needs:
    - ref_dir/blocky/BlockyCharacter.fbx: the blocky body (its armature "Armature.001"... renamed
      "Blocky_Armature", its part cages, its attachment markers);
    - ref_dir/cages/Clothing_Cage_Templates/Clothing_Cage_Template.fbx: the clothing cage template;
    - EE_InnerCage_Blocky: the template with every vertex moved onto the blocky body's cage, matched
      by UV (the two layouts are identical: every corner matches);
    - Blocky_BodyFront_Att and Blocky_WaistCenter_Att: the markers the items' attachments copy.
    Downloads (create.roblox.com/docs/avatar/resources): Clothing_Cage_Templates.zip and
    BlockyCharacter.fbx. Import their FBX files only: never open their .blend files (scripts)."""
    from mathutils import kdtree

    def imp(path, tag):
        before = set(bpy.data.objects.keys())
        bpy.ops.import_scene.fbx(filepath=path)
        new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
        for o in new:
            o["src"] = tag
        return new
    blocky = imp(os.path.join(ref_dir, "blocky", "BlockyCharacter.fbx"), "blocky")
    tpl = imp(os.path.join(ref_dir, "cages", "Clothing_Cage_Templates", "Clothing_Cage_Template.fbx"), "cagetpl")
    arm = next(o for o in blocky if o.type == "ARMATURE")
    arm.name = "Blocky_Armature"
    template = next(o for o in tpl if o.name.endswith("_InnerCage"))
    parts = [o for o in blocky if o.name.endswith("_OuterCage")]
    pts = []
    for o in parts:
        me = o.data
        uv = me.uv_layers.active.data
        for poly in me.polygons:
            for li in poly.loop_indices:
                pts.append((uv[li].uv.copy(), o.matrix_world @ me.vertices[me.loops[li].vertex_index].co))
    kd = kdtree.KDTree(len(pts))
    for i, (u, _) in enumerate(pts):
        kd.insert((u.x, u.y, 0), i)
    kd.balance()
    me = template.data.copy()
    me.name = "EE_InnerCage_Blocky"
    uvl = me.uv_layers.active.data
    targets, worst = {}, 0.0
    for poly in me.polygons:
        for li in poly.loop_indices:
            u = uvl[li].uv
            _, idx, d = kd.find((u.x, u.y, 0))
            worst = max(worst, d)
            targets.setdefault(me.loops[li].vertex_index, []).append(pts[idx][1])
    for vi, ps in targets.items():
        me.vertices[vi].co = sum(ps, Vector()) / len(ps)
    _claim("EE_InnerCage_Blocky")
    cage = bpy.data.objects.new("EE_InnerCage_Blocky", me)
    bpy.context.scene.collection.objects.link(cage)
    # the markers the items' attachments copy (the body's own, under names of their own)
    front = next(o for o in blocky if o.name.startswith("BodyFront_Att"))
    front.name = "Blocky_BodyFront_Att"
    waist = next(o for o in blocky if o.name.startswith("WaistCenter_Att"))
    waist.name = "Blocky_WaistCenter_Att"
    return {"uv_worst": worst, "moved": len(targets), "of": len(me.vertices)}


# ---------- the skeleton ----------
def skeleton(name, source="Blocky_Armature"):
    """A copy of the blocky character's armature (setup_reference) keeping only the 17 R15 body bones."""
    arm = _copy(bpy.data.objects[source], name)
    vl = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    vl.objects.active = arm
    with _override([arm], arm):
        bpy.ops.object.mode_set(mode="EDIT")
        for eb in list(arm.data.edit_bones):
            if eb.name not in R15:
                arm.data.edit_bones.remove(eb)
        bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _override(objs, active):
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=win, area=area, region=region, active_object=active,
                                     selected_objects=objs, selected_editable_objects=objs, object=active)


# ---------- weights ----------
def _limit(w, n=4):
    w = {k: v for k, v in w.items() if v > 1e-4}
    top = dict(sorted(w.items(), key=lambda kv: -kv[1])[:n])
    s = sum(top.values()) or 1.0
    return {k: v / s for k, v in top.items()}


def _legs(x, z, top=0.25):
    """Hanging cloth below the waist: from the hips into the leg it hangs over."""
    leg = ss(top, top - 0.7, z)
    share_l = ss(-0.3, 0.3, x)
    low = ss(-0.95, -1.45, z) * 0.45
    w = {"LowerTorso": 1 - leg}
    for sd, share in (("Left", share_l), ("Right", 1 - share_l)):
        w[sd + "UpperLeg"] = leg * share * (1 - low)
        w[sd + "LowerLeg"] = leg * share * low
    return w


def _arm(x, z, side):
    """A sleeve: the upper arm above the elbow, the lower arm below; into the torso at the shoulder."""
    arm = ss(0.95, 1.22, abs(x))
    lower = ss(ELBOW + 0.18, ELBOW - 0.18, z)
    return {side + "UpperArm": arm * (1 - lower), side + "LowerArm": arm * lower, "UpperTorso": 1 - arm}


def _torso(x, z):
    head = ss(2.12, 2.42, z) if abs(x) < 0.8 else 0.0
    pelvis = ss(0.6, 0.3, z)
    return {"Head": head, "UpperTorso": (1 - head) * (1 - pelvis), "LowerTorso": (1 - head) * pelvis}


def robe_weights(p, piece):
    """Bones and weights for a point of the robe's piece `piece` (world space, on the blocky body)."""
    x, y, z = p
    if "Sleeve" in piece:
        return _limit(_arm(x, z, "Left" if "Left" in piece else "Right"))
    if "Mantle" in piece:
        w = _arm(x, z, "Right")
        w["RightLowerArm"] = 0.0          # a shoulder cape: it rides the upper arm only
        return _limit(w)
    if "Skirt" in piece or "Underskirt" in piece:
        return _limit(_legs(x, z))
    if "Stole" in piece and z < 0.3:
        return _limit(_legs(x, z))
    return _limit(_torso(x, z))


def pants_weights(p, piece):
    """Bones and weights for a point of the hakama's piece `piece` (the hip, or a leg's piece)."""
    x, y, z = p
    side = "Left" if "Left" in piece else "Right" if "Right" in piece else None
    if side is None:
        leg = ss(0.0, -0.35, z)
        share_l = ss(-0.3, 0.3, x)
        return _limit({"LowerTorso": 1 - leg, "LeftUpperLeg": leg * share_l, "RightUpperLeg": leg * (1 - share_l)})
    top = ss(-0.05, 0.2, z)
    knee = ss(KNEE + 0.15, KNEE - 0.15, z)
    foot = ss(ANKLE + 0.1, ANKLE - 0.1, z)
    w = {"LowerTorso": top, side + "UpperLeg": (1 - top) * (1 - knee), side + "LowerLeg": (1 - top) * knee * (1 - foot),
         side + "Foot": (1 - top) * knee * foot}
    return _limit(w)


def weigh(obj, weight_fn):
    """Vertex groups on one piece from weight_fn(world point, piece name)."""
    obj.vertex_groups.clear()
    groups = {b: obj.vertex_groups.new(name=b) for b in R15 if b not in ("Root", "HumanoidRootNode")}
    mw = obj.matrix_world
    for v in obj.data.vertices:
        for b, wt in weight_fn(mw @ v.co, obj.name).items():
            groups[b].add([v.index], wt, "REPLACE")


def bind(obj, arm):
    """An Armature modifier, parented to the armature (keeping its place)."""
    mod = obj.modifiers.get("Armature") or obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    world = obj.matrix_world.copy()
    obj.parent = arm
    obj.matrix_world = world


# ---------- joining ----------
def join(objects, name):
    """The pieces joined into one mesh object named `name` (transforms applied: world space)."""
    for o in objects:
        o.data = o.data.copy()
        o.data.transform(o.matrix_world)
        o.matrix_world = o.matrix_world.Identity(4)
    vl = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.hide_set(False)
        o.select_set(True)
    vl.objects.active = objects[0]
    with _override(objects, objects[0]):
        bpy.ops.object.join()
    o = objects[0]
    if o.name != name:
        _claim(name)
    o.name = o.data.name = name
    return o


# ---------- cages ----------
def inner_cage(name, source="EE_InnerCage_Blocky"):
    """A copy of a cage with the template's topology and UVs, named for the item: the blocky-fitted
    body cage, or (for something worn over another item) that item's outer cage."""
    o = _copy(bpy.data.objects[source], name)
    o.location = (0, 0, 0)
    return o


def _bvh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def outside_points(cage, render, tol=0.008, faces=False):
    """The item's vertices not at least `tol` inside the cage (by the nearest cage face's side); with
    faces, (point, nearest face index, normal, signed distance) for each."""
    tree = _bvh(cage)
    out = []
    for v in render.data.vertices:
        r = render.matrix_world @ v.co
        loc, nrm, idx, _ = tree.find_nearest(r)
        if loc is None:
            continue
        sd = (r - loc).dot(nrm)
        if sd > -tol:
            out.append((r, idx, nrm, sd) if faces else r)
    return out


# the blocky body's boxes (x0, x1, y0, y1, z0, z1), from BlockyCharacter.fbx's body cages
BLOCKY_BOXES = [(-1.0, 1.0, -0.513, 0.501, 0.02, 2.008), (-0.615, 0.615, -0.605, 0.614, 2.008, 3.145),
                (1.0, 2.0, -0.513, 0.5, -0.004, 2.0), (-2.0, -1.0, -0.513, 0.5, -0.004, 2.0),
                (0.0, 1.0, -0.513, 0.5, -2.006, 0.057), (-1.0, 0.0, -0.513, 0.5, -2.006, 0.057)]


def blocky_internal(p, eps=0.025):
    """Whether a point of the blocky-fitted cage is hidden inside the body: on a seam where two boxes
    meet (head and torso, torso and arm, torso and leg, the two legs) or within a box."""
    x, y, z = p
    inside = [b for b in BLOCKY_BOXES if b[0] - eps <= x <= b[1] + eps and b[2] - eps <= y <= b[3] + eps and b[4] - eps <= z <= b[5] + eps]
    if len(inside) >= 2:
        return True
    for b in inside:
        if b[0] + eps < x < b[1] - eps and b[2] + eps < y < b[3] - eps and b[4] + eps < z < b[5] - eps:
            return True
    return False


def outer_cage(inner, render, name, reach=0.55, margin=0.035, passes=12, max_offset=0.8, k=10):
    """The outer cage: the inner cage pushed out along its normals past the item.

    Coverage is judged per cage vertex, not by the nearest cage face: where the blocky body's boxes
    meet (torso and legs, torso and arms) the template folds flat inside the body, and the nearest
    face there can be an inner fold. A point of the item is covered when the nearest cage vertex that
    faces it (the point lies on its outward side) has been pushed out past it."""
    o = _copy(inner, name)
    me = o.data
    me.update()
    base = [v.co.copy() for v in me.vertices]
    normals = [v.normal.copy() for v in me.vertices]
    tree = _bvh(render)
    offset = [0.0] * len(base)
    # the cage's hidden seams: where the template is squeezed between the blocky body's boxes (head
    # and torso, torso and arms and legs, the legs) a vertex's normal points straight into another
    # part's cage. Those vertices are inside the body: they are never pushed.
    itree = _bvh(inner)
    internal = set()
    for i, (p, n) in enumerate(zip(base, normals)):
        if blocky_internal(p) or itree.ray_cast(p + n * 0.004, n, 0.09)[0] is not None:
            internal.add(i)
    # 1: past every layer met along the normal within reach
    for i, (p, n) in enumerate(zip(base, normals)):
        if i in internal:
            continue
        start = p + n * 0.001
        far = None
        travelled = 0.0
        while travelled < reach:
            hit, _, _, d = tree.ray_cast(start, n, reach - travelled)
            if hit is None:
                break
            travelled += d + 1e-4
            far = travelled
            start = hit + n * 1e-4
        if far is not None:
            offset[i] = min(max_offset, far + margin)
    nbr = [[] for _ in base]
    for e in me.edges:
        a, b = e.vertices
        nbr[a].append(b)
        nbr[b].append(a)
    kd = KDTree(len(base))
    for i, p in enumerate(base):
        kd.insert(p, i)
    kd.balance()
    rverts = [render.matrix_world @ v.co for v in render.data.vertices]

    def facing(r):
        """The cage vertex the point lies most squarely in front of (among the nearest few), and how far
        out it lies: the collar beside the head is covered by the head's sides, not by the shoulder
        tops below it."""
        best, best_score, best_along = None, 0.0, 0.0
        first = None
        for co, j, dist in kd.find_n(r, k):
            if j in internal:
                continue
            along = (r - base[j]).dot(normals[j])
            if along <= 0:
                continue
            if first is None:
                first = (j, along)
            c = along / max(dist, 1e-6)
            score = c / (dist + 0.08)          # squarely in front of it, and near it
            if c > 0.35 and score > best_score:
                best, best_score, best_along = j, score, along
        if best is not None:
            return best, best_along
        return first if first else (None, 0.0)

    def smooth():
        for _ in range(2):
            offset[:] = [offset[i] if (i in internal or not nbr[i]) else
                         min(max_offset, max(offset[i], 0.8 * sum(offset[j] for j in nbr[i] if j not in internal) / max(1, sum(1 for j in nbr[i] if j not in internal))))
                         for i in range(len(base))]

    smooth()
    uncovered = []
    for _ in range(passes):
        uncovered = []
        for r in rverts:
            j, along = facing(r)
            if j is None:
                continue
            if along + 0.008 > offset[j]:
                uncovered.append(along + 0.008 - offset[j])
                offset[j] = min(max_offset, along + margin)
        if not uncovered:
            break
        smooth()
    for i, v in enumerate(me.vertices):
        v.co = base[i] + normals[i] * offset[i]
    me.update()
    capped = sum(1 for x in offset if x >= max_offset - 1e-6)
    return o, {"uncovered": len(uncovered), "of": len(rverts), "max_offset": round(max(offset), 3), "capped": capped,
               "internal": len(internal),
               "face_test_outside": len(outside_points(o, render))}


def attachment(source, name, arm):
    """The attachment marker: a copy of the blocky character's marker mesh, parented to the armature."""
    src = bpy.data.objects[source]
    o = _copy(src, name)
    world = src.matrix_world.copy()
    o.parent = arm
    o.matrix_world = world
    return o


def write_fbx(objects, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    vl = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.hide_set(False)
        o.select_set(True)
    vl.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH", "EMPTY"},
                             axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             add_leaf_bones=False, bake_anim=False, use_armature_deform_only=False,
                             mesh_smooth_type="FACE", path_mode="STRIP")


def seal_weights(p, piece):
    """The seal cord rides the hips whole, as a rigid piece would."""
    return {"LowerTorso": 1.0}


def layered(item, pieces, weight_fn, att_source, att_name, inner_source="EE_InnerCage_Blocky"):
    """Builds and writes one layered item; returns its report. inner_source: the cage the item was
    modelled on (the body, or the outer cage of the item it is worn over)."""
    arm = skeleton(item + "_Armature")
    for o in pieces:
        weigh(o, weight_fn)
    mesh = join(pieces, item)
    bind(mesh, arm)
    att = attachment(att_source, att_name, arm)
    inner = inner_cage(item + "_InnerCage", inner_source)
    outer, rep = outer_cage(inner, mesh, item + "_OuterCage")
    _claim(item + "_Cage")
    cage_root = bpy.data.objects.new(item + "_Cage", None)
    bpy.context.scene.collection.objects.link(cage_root)
    for c in (inner, outer):
        c.parent = cage_root
    path = os.path.join(K.OUT_DIR, item + ".fbx")
    exported = [arm, mesh, att, cage_root, inner, outer]
    expected = [item + "_Armature", item, att_name, item + "_Cage", item + "_InnerCage", item + "_OuterCage"]
    assert [o.name for o in exported] == expected, [o.name for o in exported]
    write_fbx(exported, path)
    rep.update({"tris": K.tris(mesh), "fbx": path,
                "max_influences": max((len([g for g in v.groups if g.weight > 1e-4]) for v in mesh.data.vertices), default=0)})
    return rep


def rigid(item, pieces):
    """Writes the rigid accessory (one mesh) and its bounds (world space) for Studio."""
    mesh = join(pieces, item)
    path = os.path.join(K.OUT_DIR, item + ".fbx")
    write_fbx([mesh], path)
    bb = [mesh.matrix_world @ V(c) for c in mesh.bound_box]
    lo = [min(v[i] for v in bb) for i in range(3)]
    hi = [max(v[i] for v in bb) for i in range(3)]
    info = {"tris": K.tris(mesh), "fbx": path, "min": lo, "max": hi}
    with open(os.path.join(K.OUT_DIR, item + "_bounds.json"), "w") as f:
        json.dump(info, f, indent=1)
    return info

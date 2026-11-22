"""The Unorthodox faction's secret weapon (run inside Blender, headless): the Crosscurrent Saber, id SecretUnorthodox (a sword).

    blender -b --factory-startup --python tools/blender/weapons/sword_unorthodox.py -- clay|export|review|study|all

THE IDEA (one, and nothing else): the counter-curve. The blade bows out to one side, swells into a heavy forward belly, and turns
back in a recurve to a clipped, hooked point (the blade's last third turns toward the edge side). The guard answers it: one swept
bronze arm on the edge side only, leaving the plate, sweeping out and forward, and turning back toward the blade (a catch for a
foe's blade, as the jitte's hook is). They turn opposite ways, so the silhouette is a figure that nobody would take for a school sword.
Everything else is craft: a patinated, grain-forged blade with a honed edge and a wandering temper line, a pierced bronze plate with
a raised face in a flat rim, a copper blade collar, brass fuchi and cap, grips lashed in bone-coloured linen over black leather in
three separate lashings, and a heavy pommel of two interlocked bronze links (an upright link through a flat one through the cap's
eye), the Korean ring pommel made a chain.

Authored in studs from the grip (the realm weapons' convention: point toward -Z, flats +-Y, edges +-X, the curve in the X-Z plane, the
curve bowing to +X, the edge on the -X side). Hilt = where the blade leaves the collar, Tip = the point (off the axis).

  tools/blender/weapons/sword_unorthodox.py          this (the build, the game mesh, the export)
  sword_unorthodox_blade.py / _fit.py / _mat.py      the blade, the fittings, the materials
  sword_unorthodox_review.py                         the review renders (renders/faction_weapons_v2/Unorthodox/, local)
  sword_unorthodox_study.py / _draw.py               the research board and the silhouette study
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402
import sword_unorthodox_blade as BL  # noqa: E402
import sword_unorthodox_fit as FT  # noqa: E402
import sword_unorthodox_mat as MT  # noqa: E402

WK, Hm, W, B = SK.WK, SK.Hm, SK.W, SK.B
V = Vector
TAU = math.tau
WEAPON_ID = "SecretUnorthodox"
NAME = "Crosscurrent Saber"
COMPARE = ("Sword6", 2.6)
REVIEW = os.path.join(SK.REPO, "renders", "faction_weapons_v2", "Unorthodox")
BUDGET = 5600

_LOW = []        # the game mesh's parts, filled by build(): (name, low object)
_BLADE = None


def blade():
    global _BLADE
    if _BLADE is None:
        _BLADE = BL.Blade()
    return _BLADE


# ---------- the build ----------
def mark_sharp(obj, angle=18.0):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    lim = math.radians(angle)
    for e in bm.edges:
        if e.is_manifold and e.calc_face_angle(0.0) > lim:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    for p in obj.data.polygons:
        p.use_smooth = True


def low_blade(b, coll):
    hi = Hm.Hi()
    BL.build_low(hi, b, 92)
    o = hi.object("UL_Blade", coll, [], smooth=True, weld=1e-6)
    mark_sharp(o, 14.0)
    o["uv_keep"] = True
    return o


def low_grip(coll):
    """The game mesh's grip: a swollen round core with the three lashings as raised, chamfered bands (the cord's twist is in the normal map)."""
    hi = Hm.Hi()
    r0 = FT.GRIP_R

    def core(z):
        t = (z - FT.GRIP0) / (FT.GRIP1 - FT.GRIP0)
        return r0 * (1 + 0.10 * math.sin(math.pi * t) ** 1.2)
    poly = [(0.0, FT.GRIP0), (core(FT.GRIP0), FT.GRIP0)]
    for z0, z1 in FT.BANDS:
        c = 0.012
        poly += [(core(z0 - c), z0 - c), (core(z0) + 0.042, z0 + 0.004), (core(z1) + 0.042, z1 - 0.004), (core(z1 + c), z1 + c)]
    poly += [(core(FT.GRIP1), FT.GRIP1), (0.0, FT.GRIP1)]
    SK.revolve(hi, poly, n=14, mat=0, uv_scale=1.0)
    o = hi.object("UL_Grip", coll, [], smooth=True, weld=1e-6)
    mark_sharp(o, 40.0)
    # the two end discs are inside the fuchi and the cap: removed
    bm = bmesh.new()
    bm.from_mesh(o.data)
    dead = [f for f in bm.faces if all(math.hypot(v.co.x, v.co.y) > -1 and abs(v.co.y) > -1 for v in f.verts) and f.normal.length > 0 and abs(f.normal.y) > 0.99]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    FT.cylinder_uv(o)
    return o


def decimate(o, coll, target, planar=None):
    """A low copy of a high-detail piece: planar dissolve first (hard-surface pieces keep their facets) then collapse to about `target`."""
    c = B._copy(o, o.name.replace("UG_", "UL_") + "_low")
    coll.objects.link(c)
    if planar:
        md = c.modifiers.new("Dissolve", "DECIMATE")
        md.decimate_type = "DISSOLVE"
        md.angle_limit = math.radians(planar)
        md.use_dissolve_boundaries = False
        tr = c.modifiers.new("Tri", "TRIANGULATE")
        tr.min_vertices = 4
        SK._evaluated_copy(c)
    tris = SK._tris(c)
    if tris > target * 1.1:
        md = c.modifiers.new("Decimate", "DECIMATE")
        md.decimate_type = "COLLAPSE"
        md.ratio = max(0.02, target / tris)
        md.use_collapse_triangulate = True
        SK._evaluated_copy(c)
    if planar:
        mark_sharp(c, 35.0)           # hard-surface pieces keep crisp edges (smooth shading would smear them)
    return c


def build():
    """The high-detail pieces (bake sources) in a collection; the game mesh's parts are registered for make_low. Returns (objs, glow, root)."""
    global _LOW
    SK.fresh()
    root = W.collection("UnorthodoxHi")
    W.clear_collection(root)
    b = blade()
    M = dict(hira=MT.mat_hira(), edge=MT.mat_edge(), shinogi=MT.mat_shinogi(), fuller=MT.mat_fuller(), inlay=MT.mat_inlay(),
             bronze=MT.mat_bronze(), bronze_dark=MT.mat_bronze("UgBronzeDark", dark=True), copper=MT.mat_copper(), brass=MT.mat_brass(),
             leather=MT.mat_leather(), linen=MT.mat_linen(), bone=MT.mat_bone(), steel=MT.mat_steel_obj())
    objs = []
    # the blade
    hi = Hm.Hi()
    BL.build_hi(hi, b, 300)
    ob = hi.object("UG_Blade", root, [M["hira"], M["edge"], M["shinogi"], M["fuller"], M["inlay"]], smooth=True, weld=1e-6)
    objs.append(ob)
    objs.append(FT.habaki(b, root, M["copper"]))
    objs.append(FT.guard_plate(root, M["bronze"]))
    objs.append(FT.guard_arm(root, M["steel"]))
    objs.append(FT.arm_lashing(root, M["linen"]))
    objs.append(FT.arm_sleeves(root, M["brass"]))
    objs.append(FT.arm_inlay(root, M["inlay"]))
    objs.append(FT.plate_wire(root, M["inlay"]))
    objs.append(FT.fuchi(root, M["brass"]))
    objs.append(FT.grip_core(root, M["leather"]))
    objs.append(FT.grip_cord(root, M["linen"]))
    objs.append(FT.grip_stitches(root, M["linen"]))
    objs.append(FT.kashira(root, M["brass"]))
    objs.append(FT.eye_lug(root, M["brass"]))
    objs.append(FT.ring_pommel(root, M["bronze"]))
    # the game mesh's parts
    lc = bpy.data.collections.get("UnorthodoxLow") or bpy.data.collections.new("UnorthodoxLow")
    if lc.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(lc)
    W.clear_collection(lc)
    lc.hide_viewport = lc.hide_render = False
    _LOW = [("blade", low_blade(b, lc)), ("grip", low_grip(lc))]
    _LOW.append(("lashing", FT.lashing_low(lc, "UL_Lashing")))
    _LOW.append(("plate", FT.low_plate(lc)))
    _LOW.append(("ring", FT.low_ring(lc)))
    _LOW.append(("eye", FT.low_eye(lc)))
    _LOW.append(("bands", FT.bands_low(lc)))
    plan = [("UG_Arm", 380, None), ("UG_Habaki", 150, 3.0), ("UG_Fuchi", 150, 3.0), ("UG_Kashira", 170, None)]
    tube_like = ("UG_Habaki", "UG_Fuchi", "UG_Kashira")
    byname = {o.name: o for o in objs}
    ends = {"UG_Fuchi": (-0.835, -0.63), "UG_Kashira": (0.60,), "UG_Habaki": (-1.0,)}
    for name, target, planar in plan:
        low = decimate(byname[name], lc, target, planar)
        if name in ends:
            FT.drop_end_faces(low, ends[name])
        if name in tube_like:
            FT.cylinder_uv(low, axis_x=(0.03 if name == "UG_Habaki" else 0.0))
        _LOW.append((name, low))
    for o in lc.objects:
        o.hide_render = True
    return objs, {}, root


def hilt_tip():
    b = blade()
    z = -1.31
    u = float(np.interp(z, b.z[::-1], b.u[::-1]))
    x = float(b.at(b.x, u))
    tx, tz = b.tip()
    return (round(x, 3), 0.0, z), (tx, 0.0, tz)


# ---------- the game mesh ----------
def make_low(weapon_id, hi_objects, coll, budget, sheet_ratio=0.55):
    """Joins the parts registered by build() into the game mesh, one material, unwrapped (islands packed as boxes)."""
    bm = bmesh.new()
    keep = bm.faces.layers.int.new("keepuv")
    for name, o in _LOW:
        me = o.data.copy()
        me.transform(o.matrix_world)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bm.faces.ensure_lookup_table()
        if o.get("uv_keep"):
            for f in bm.faces[n0:]:
                f[keep] = 1
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    me = bpy.data.meshes.new(weapon_id + "_Body")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.material_index = 0
        p.use_smooth = True
    low = bpy.data.objects.new(weapon_id + "_Body", me)
    coll.objects.link(low)
    unwrap(low)
    me.attributes.remove(me.attributes["keepuv"])
    return low


def unwrap(obj):
    """Smart project the faces that have no UVs of their own, put those that do (the ring: a strip) through untouched, bring every island to
    one texel density, and pack them as boxes (so no island nests inside the hole of another, which could read as a shape)."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    view_layer.objects.active = obj
    with B._ui_override(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(me)
        layer = bm.faces.layers.int.get("keepuv")
        for f in bm.faces:
            f.select_set(not f[layer])
        bmesh.update_edit_mesh(me)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002)
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(margin=0.006, rotate=True, shape_method="AABB")
        bpy.ops.object.mode_set(mode="OBJECT")


def export():
    """Bakes the maps and writes the FBX and the placements file (assets/weapons, src/worldbuild/Placements/Weapons)."""
    objs, glow, root = build()
    hilt, tip = hilt_tip()
    saved = (B.make_low, B.bake, B.K.join, B._unwrap)
    real_join = B.K.join
    B.make_low, B.bake, B._unwrap = make_low, SK.bake, SK.unwrap
    try:
        report = WK.export(WEAPON_ID, "Sword", "sword_unorthodox.py", objs, glow, root, hilt, tip, budget=BUDGET)
    finally:
        B.make_low, B.bake, B.K.join, B._unwrap = saved
    SK.scrub_paths(os.path.join(SK.OUT_DIR, WEAPON_ID + ".fbx"))
    lua = os.path.join(SK.PLACEMENTS_DIR, WEAPON_ID + ".lua")
    import re
    text = re.sub(r"^-- \w+ by ", "-- Built by ", open(lua).read(), count=1)
    open(lua, "w").write(text)
    return objs, glow, root, report


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    import sword_unorthodox_review as R
    R.run(sys.modules[__name__], stage)

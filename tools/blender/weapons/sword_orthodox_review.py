"""The review lab for the Orthodox sword (run inside Blender, headless; stages called by sword_orthodox.py). Everything goes to
renders/faction_weapons_v2/Orthodox/ (local, never committed). Uses secret_lab.py read-only (its REVIEW folder is redirected here).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

import secret_kit as SK
import secret_lab as L
import sword_orthodox_board as BD
import sword_orthodox_parts as P

V = Vector
W = SK.W
REVIEW = os.path.join(W.REPO, "renders", "faction_weapons_v2", "Orthodox")
L.REVIEW = SK.REVIEW = REVIEW


def rv(name):
    os.makedirs(REVIEW, exist_ok=True)
    return os.path.join(REVIEW, name)


def tris(objs):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)


def c3(x, y, z):
    """A Roblox point as the lab's centre (Blender axes)."""
    return V((x, -z, y))


# the close-ups: (view, Roblox centre, span in studs)
CLOSE = (("front34", (0, 0, -1.1), 2.6), ("back34", (0, 0, -0.9), 2.6), ("top", (0, 0, 0.5), 2.8), ("front34", (0, 0, 1.9), 2.6),
         ("top", (0, 0, 3.0), 2.2), ("front34", (0, 0, -5.2), 1.7), ("back34", (0, 0, -0.75), 1.5), ("pommel", (0, 0, -1.0), 2.4), ("edge_r", (0, 0, 2.6), 2.4),
         ("top", (0, 0, -2.5), 1.0), ("front34", (0, 0, -3.4), 1.1), ("top", (0, 0, 3.3), 1.0))


def six_views(objs, path, samples=36, size=(300, 760)):
    tiles = []
    mid = c3(0, 0, -1.05)
    for v in ("top", "bottom", "edge_r", "edge_l", "front34", "back34"):
        tiles.append(L.shoot(objs, v, size=size, samples=samples, ortho=v in ("top", "bottom", "edge_r", "edge_l"), centre=mid, span=10.4))
    return L.save_png(L.sheet(tiles, len(tiles)), path)


def close_ups(objs, path, samples=40, size=(440, 440)):
    tiles = []
    for v, c, span in CLOSE:
        tiles.append(L.shoot(objs, v, size=size, samples=samples, ortho=False, centre=c3(*c), span=span))
    return L.save_png(L.sheet(tiles, 3), path)


def clay(mod, tag="clay", samples=36):
    SK.fresh()
    objs, root = mod.build_hi()
    L.lab()
    with L.clay(objs):
        p1 = six_views(objs, rv("%s_six.png" % tag), samples)
        p2 = close_ups(objs, rv("%s_close.png" % tag), samples)
    print("clay:", p1, p2)
    print("hi triangles:", {o.name: P_tris(o) for o in objs}, "total", tris(objs))
    return objs, root


def look_hi(mod, tag="hi_look", samples=48):
    """The HIGH-detail source in its own shaders (before any bake): a quick look at what the maps will carry."""
    SK.fresh()
    objs, root = mod.build_hi()
    L.lab()
    tiles = []
    for v, c, span, sz in (("top", (0, 0, -1.3), 3.6, (420, 760)), ("front34", (0, 0, -1.2), 2.6, (420, 760)), ("edge_r", (0, 0, -1.2), 3.6, (420, 760)),
                           ("top", (0, 0, 0.4), 3.0, (420, 760))):
        tiles.append(L.shoot(objs, v, size=sz, samples=samples, ortho=False, centre=c3(*c), span=span))
    p = L.save_png(L.sheet(tiles, 4), rv(tag + ".png"))
    tiles = []
    for v, c, span in (("top", (0, 0, -3.6), 1.9), ("front34", (0, 0, -5.3), 1.5), ("top", (0, 0, 2.9), 2.6), ("front34", (0, 0, 1.7), 2.2)):
        tiles.append(L.shoot(objs, v, size=(520, 520), samples=samples, ortho=False, centre=c3(*c), span=span))
    p2 = L.save_png(L.sheet(tiles, 4), rv(tag + "_2.png"))
    print("hi look:", p, p2)
    return objs


def look_blade(mod, tag="blade_look", samples=64):
    SK.fresh()
    objs, root = mod.build_hi()
    blade = [o for o in objs if o.name == "OR_Blade"]
    L.lab()
    tiles = []
    for v, c, span in (("top", (0, 0, -2.6), 1.1), ("front34", (0, 0, -3.2), 1.2), ("top", (0, 0, -4.7), 1.1), ("edge_r", (0, 0, -4.2), 2.2)):
        tiles.append(L.shoot(blade, v, size=(430, 700), samples=samples, ortho=False, centre=c3(*c), span=span))
    return L.save_png(L.sheet(tiles, 4), rv(tag + ".png"))


def export(mod):
    SK.fresh()
    objs, root, report = mod.export()
    print("export report (centre, size, tris):", json.dumps(report))
    return objs, root, report


# ---------- what was written ----------
import secret_review as R  # noqa: E402

R.REVIEW = REVIEW


def box_mesh(name, coll, pts_a, rot_x_deg, color, alpha=1.0):
    """A box given by (centre, size) in the hand's own frame (x across, y toward the fingers' back = 'up' when the arm is raised, z toward
    the elbow) turned into weapon space by the grip's turn (CombatFx.GRIP_TURN: 80 degrees about X for a sword): the R15 hand and forearm
    as the game puts them round the weapon."""
    (cx, cy, cz), (sx, sy, sz) = pts_a
    t = math.radians(rot_x_deg)
    verts = []
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                x, y, z = cx + dx * sx / 2, cy + dy * sy / 2, cz + dz * sz / 2
                # weapon = Rx(-turn) * attach
                yw = y * math.cos(t) + z * math.sin(t)
                zw = -y * math.sin(t) + z * math.cos(t)
                verts.append(W.rb(x, yw, zw))
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    m = bpy.data.materials.get("SK_Hand_" + name) or bpy.data.materials.new("SK_Hand_" + name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Alpha"].default_value = alpha
    o.data.materials.append(m)
    return o


def r15_arm(coll, scale=1.0):
    """The R15 right hand and lower arm at true size (default proportions: hand 1.0 x 0.32 x 1.0, lower arm 1.0 x 1.08 x 1.0; the owner's
    avatar is 0.81-0.91 of this), placed as the grip attachment sits in the hand (0.1 toward the fingers from the hand's middle)."""
    k = scale
    hand = box_mesh("SK_R15Hand", coll, ((0, 0, 0.1 * k), (1.0 * k, 1.0 * k, 0.32 * k)), 80.0, (0.8, 0.55, 0.42), 0.55)
    arm = box_mesh("SK_R15Forearm", coll, ((0, 0, (0.1 + 0.16 + 0.54) * k), (1.0 * k, 1.0 * k, 1.08 * k)), 80.0, (0.82, 0.58, 0.45), 0.55)
    return [hand, arm]


def _arm_axes():
    """The hand block in the hand's frame as (x across, y toward the elbow... ) is easier to read in weapon space: print its extents."""
    return None


def dark_light(scene):
    """A dramatic light: a near-black world, a hard rim light behind, a weak warm key from the front."""
    w = bpy.data.worlds.get("SK_Dark") or bpy.data.worlds.new("SK_Dark")
    w.use_nodes = True
    t = w.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputWorld")
    bg = t.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.006, 0.008, 0.014, 1)
    bg.inputs["Strength"].default_value = 1.0
    t.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w
    lights = []
    for nm, loc, energy, color, size in (("SK_Rim", (-3.0, 2.0, 2.5), 900, (0.75, 0.85, 1.0), 2.0), ("SK_Key", (2.5, -4.5, 1.8), 260, (1.0, 0.86, 0.7), 2.5),
                                         ("SK_Under", (0.0, 3.0, -2.0), 120, (0.5, 0.6, 0.9), 3.0)):
        ld = bpy.data.lights.new(nm, "AREA")
        ld.energy, ld.size, ld.color = energy, size, color
        lo = bpy.data.objects.new(nm, ld)
        scene.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (V(loc) * -1).to_track_quat("-Z", "Y").to_euler()
        lights.append(lo)
    return lights


def remove_lights(lights):
    for lo in lights:
        bpy.data.objects.remove(lo, do_unlink=True)


def review(mod):
    """Everything the owner and the gate look at, from what was WRITTEN (the FBX and its four PNGs), not from the build."""
    SK.fresh()
    wid = mod.WEAPON_ID
    folder = SK.OUT_DIR
    body, glows = R.load_game(wid, folder)
    mine = [body] + glows
    scene = L.lab()
    coll = scene.collection
    mid = c3(0, 0, -1.05)
    # six views, neutral studio light
    tiles = [L.shoot(mine, v, size=(300, 760), samples=48, ortho=v in ("top", "bottom", "edge_r", "edge_l"), centre=mid, span=10.4)
             for v in ("top", "bottom", "edge_r", "edge_l", "front34", "back34")]
    p1 = L.save_png(L.sheet(tiles, 6), rv("game6_neutral.png"))
    # the VFX-off test: the same, in a dark dramatic light
    lights = dark_light(scene)
    saved_world = L._world
    L._world = lambda scene, sky=True, exposure=1.0: None          # shoot() would put the studio dome back every time
    tiles = [L.shoot(mine, v, size=(300, 760), samples=64, ortho=False, centre=mid, span=10.4) for v in ("top", "edge_r", "front34", "back34")]
    p2 = L.save_png(L.sheet(tiles, 4), rv("game_dark.png"))
    big = [L.shoot(mine, "front34", size=(560, 760), samples=80, ortho=False, centre=c3(0, 0, -1.9), span=5.6),
           L.shoot(mine, "top", size=(560, 760), samples=80, ortho=False, centre=c3(0, 0, 0.9), span=5.6)]
    p2b = L.save_png(L.sheet(big, 2), rv("game_dark_big.png"))
    remove_lights(lights)
    L._world = saved_world
    L.lab()
    # close-ups: bell, the other side of the bell, grip, ring and cord, tassel, point
    close = []
    for v, c, span in CLOSE:
        close.append(L.shoot(mine, v, size=(520, 520), samples=64, ortho=False, centre=c3(*c), span=span))
    p3 = L.save_png(L.sheet(close, 3), rv("game_closeups.png"))
    # the real R15 hand and forearm
    arm = r15_arm(coll)
    held = [L.shoot(mine + arm, v, size=(520, 600), samples=40, centre=c3(0, 0, 0.55), span=4.8, ortho=True) for v in ("top", "edge_r")]
    held.append(L.shoot(mine + arm, "front34", size=(520, 600), samples=40, centre=c3(0, 0, 0.55), span=4.8, ortho=False))
    p4 = L.save_png(L.sheet(held, 3), rv("hand_test.png"))
    L.set_visible(arm, False)
    # beside Sword6 (the Immortal sword), same scale
    other_id, dx = mod.COMPARE
    obody, oglows = R.load_game(other_id, os.path.join(SK.REPO, "assets", "weapons"), (dx, 0, 0))
    both = mine + [obody] + oglows
    arm2 = r15_arm(coll)
    for o in arm2:
        o2 = o.copy()
        o2.data = o.data
        coll.objects.link(o2)
        o2.location = o2.location + V((dx, 0, 0))
        both.append(o2)
    both += arm2
    views = [L.shoot(both, "top", size=(620, 760), samples=40, ortho=True, centre=c3(dx / 2, 0, -1.0), span=11.0),
             L.shoot(both, "front34", size=(620, 760), samples=40, ortho=False, centre=c3(dx / 2, 0, -1.0), span=11.0)]
    p5 = L.save_png(L.sheet(views, 2), rv("vs_Sword6.png"))
    L.set_visible(both, False)
    L.set_visible(mine, True)
    # black silhouettes at thumbnail size: the flat the player sees, the edge, three-quarter
    sil = R.silhouette_tiles(mine, ("top", "edge_r", "front34"), size=(160, 420), ortho=False)
    sil += R.silhouette_tiles(mine, ("top", "edge_r", "front34"), size=(80, 210), ortho=False)
    p6 = L.save_png(L.sheet(sil, len(sil), bg=(0.5, 0.5, 0.5, 1)), rv("silhouette_final.png"))
    p7 = R.maps_sheet(wid, folder, rv("maps.png"))
    # the gate, on the game mesh as it is written (imported back from the FBX), and the maps read back raw
    stats = R.map_stats(wid, folder)
    res = R.qa([body] + glows)
    obj_info = dict(tris=sum(len(p.vertices) - 2 for p in body.data.polygons), verts=len(body.data.vertices), dims=[round(x, 3) for x in body.dimensions],
                    uv_layers=len(body.data.uv_layers), materials=len(body.data.materials))
    with open(rv(wid + "_qa.json"), "w") as f:
        json.dump(dict(mesh=obj_info, maps=stats, qa={k: res[k] for k in ("pass", "errors", "warnings")}), f, indent=1, default=str)
    print("QA pass:", res["pass"], "| mesh:", obj_info, "| maps:", json.dumps(stats))
    print("review images:", p1, p2, p2b, p3, p4, p5, p6, p7, sep="\n  ")


def qa_only(mod):
    """The gate on the FBX as written, nothing rendered."""
    SK.fresh()
    wid = mod.WEAPON_ID
    body, glows = R.load_game(wid, SK.OUT_DIR)
    res = R.qa([body] + glows)
    print("QA pass:", res["pass"], "tris", sum(len(p.vertices) - 2 for p in body.data.polygons))
    return res


def P_tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def run(mod, stage):
    if stage in ("clay", "all"):
        clay(mod)
    if stage == "look":
        look_hi(mod)
    if stage in ("export", "all"):
        export(mod)
    if stage in ("review", "all"):
        review(mod)
    if stage == "qa":
        qa_only(mod)
    if stage == "blade":
        print(look_blade(mod))

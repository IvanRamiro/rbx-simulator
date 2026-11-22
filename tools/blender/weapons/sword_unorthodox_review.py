"""The review renders for the Unorthodox sword (run inside Blender, headless): everything goes to renders/faction_weapons_v2/Unorthodox/
(local, never committed). Built on secret_lab's lab (studio dome, camera, silhouettes) and secret_review's helpers, pointed at this folder.

    study     the research board and the silhouette study (sword_unorthodox_study.py)
    clay      the hi-detail model in neutral grey from eight views, and close-ups
    export    bake and write the FBX/maps/placements, run the QA gate, check the maps
    review    the written game mesh dressed from its own four PNGs: material views in neutral light and in a dark dramatic light (the
              weapon has no glow piece: both are the VFX-off view), close-ups, the blade's cross-sections, a hand test with a real R15
              forearm and hand at true size, Sword6 at the same scale, black silhouettes at thumbnail size, the maps at thumbnail size
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import secret_kit as SK  # noqa: E402
import secret_lab as L  # noqa: E402
import secret_review as SR  # noqa: E402
import sword_unorthodox_draw as D  # noqa: E402

V = Vector
REVIEW = os.path.join(SK.REPO, "renders", "faction_weapons_v2", "Unorthodox")
SK.REVIEW = L.REVIEW = SR.REVIEW = REVIEW

CLAY_VIEWS = ("top", "bottom", "edge_r", "edge_l", "front34", "back34", "pommel", "tip")
MAT_VIEWS = ("top", "bottom", "edge_r", "edge_l", "front34", "back34")
# close-ups: (view, centre in Roblox axes, span)
CLOSE = (("top", (-0.2, 0.0, -1.5), 3.2), ("front34", (-0.3, 0.0, -1.3), 3.2), ("back34", (0.0, 0.0, 0.3), 3.6), ("edge_r", (0.0, 0.0, 1.0), 3.0))


def bpos(c):
    return V((c[0], -c[2], c[1]))


def tris_of(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# ---------- light ----------
def dark_world(scene, sky=True, exposure=1.0):
    w = bpy.data.worlds.get("UG_Dark") or bpy.data.worlds.new("UG_Dark")
    w.use_nodes = True
    t = w.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputWorld")
    bg = t.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.012, 0.016, 0.024, 1)
    bg.inputs["Strength"].default_value = 1.0
    t.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w


def _light(name, loc, energy, color, size, target=(0, 2.4, 0)):
    o = bpy.data.objects.get(name)
    if o is None:
        ld = bpy.data.lights.new(name, "AREA")
        o = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(o)
    o.data.energy, o.data.color, o.data.size = energy, color, size
    o.location = V(loc)
    o.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


class Dark:
    """A dark dramatic light: a near-black world, a warm key from the front left, a cold rim from behind, a faint kicker below."""

    def __enter__(self):
        self.saved = L._world
        L._world = dark_world
        self.lights = [_light("SKL_Key", (-5, -3, 5), 700, (1.0, 0.86, 0.7), 2.5), _light("SKL_Rim", (5, 7, 3), 1500, (0.5, 0.85, 1.0), 2.0),
                       _light("SKL_Low", (0, 1, -4), 120, (1.0, 0.7, 0.5), 3.0)]
        return self

    def __exit__(self, *a):
        L._world = self.saved
        for o in self.lights:
            bpy.data.objects.remove(o, do_unlink=True)


# ---------- the R15 stand-in ----------
HAND = ((0.984, 0.316, 1.028), (0.0, 0.0, 0.0))             # true size, Roblox axes (x, y, z): centre
FOREARM = ((1.001, 1.118, 1.002), (0.0, 0.663, 0.0))       # its centre above the hand's (RightLowerArm -0.202, RightHand -0.865)
GRIP_IN_HAND = (0.0, -0.137, 0.0)
GRIP_TURN_DEG = -10.0                                      # RightGripAttachment (-90 about X) times CombatFx's GRIP_TURN Sword (+80 about X)


def box(coll, name, size, centre, color=(0.78, 0.55, 0.42), alpha=1.0):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[2]   # Blender y = -Roblox z
        v.co.z *= size[1]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location = bpos(centre)
    m = bpy.data.materials.new("SK_" + name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Alpha"].default_value = alpha
    o.data.materials.append(m)
    return o


def r15(coll, alpha=1.0):
    return [box(coll, "SK_Hand", *HAND, alpha=alpha), box(coll, "SK_Forearm", *FOREARM, color=(0.7, 0.5, 0.4), alpha=alpha)]


def hold(objs, dx=0.0):
    """Moves a weapon's objects (authored from the grip, in Blender axes) into the hand's space: the grip attachment, turned -10 degrees."""
    m = Matrix.Translation(bpos((GRIP_IN_HAND[0] + dx, GRIP_IN_HAND[1], GRIP_IN_HAND[2]))) @ Matrix.Rotation(math.radians(GRIP_TURN_DEG), 4, "X")
    for o in objs:
        o.matrix_world = m @ o.matrix_world


def clearance(body):
    """Hand space, Roblox axes. For the part of the game mesh behind the grip's cap (weapon z beyond 0.62: the pommel ring) the nearest
    distance to the forearm box and to the hand box (outside distance, 0 when touching or inside), and how many vertices of the whole
    mesh lie inside the forearm box (the grip is meant to sit inside the hand, nothing may sit inside the forearm)."""
    m = Matrix.Translation(bpos(GRIP_IN_HAND)) @ Matrix.Rotation(math.radians(GRIP_TURN_DEG), 4, "X")
    boxes = {"forearm": (V(FOREARM[1]), V(FOREARM[0]) / 2), "hand": (V(HAND[1]), V(HAND[0]) / 2)}
    nearest = {k: 9.0 for k in boxes}
    inside = 0
    for v in body.data.vertices:
        p = m @ v.co
        r = V((p.x, p.z, -p.y))          # Blender -> Roblox
        wz = -(v.co.y)                   # weapon z in Roblox axes (the weapon's own frame)
        for k, (c, h) in boxes.items():
            d = V((abs(r.x - c.x) - h.x, abs(r.y - c.y) - h.y, abs(r.z - c.z) - h.z))
            out = V((max(d.x, 0), max(d.y, 0), max(d.z, 0))).length
            if k == "forearm" and max(d.x, d.y, d.z) < 0:
                inside += 1
            if wz > 0.62:
                nearest[k] = min(nearest[k], out)
    return nearest, inside


# ---------- stages ----------
def clay(mod, samples=36):
    objs, glow, root = mod.build()
    for o in bpy.data.collections["UnorthodoxLow"].objects:
        o.hide_render = True
    L.lab()
    tiles = []
    with L.clay(objs):
        for v in CLAY_VIEWS:
            tiles.append(L.shoot(objs, v, size=(380, 700), samples=samples, ortho=v in ("top", "bottom", "edge_r", "edge_l", "pommel", "tip")))
    print("clay sheet:", L.save_png(L.sheet(tiles, 4), os.path.join(REVIEW, "03_clay_eight_views.png")))
    close = []
    with L.clay(objs):
        for v, c, span in CLOSE:
            close.append(L.shoot(objs, v, size=(520, 520), samples=samples, ortho=False, centre=bpos(c), span=span))
    print("clay close-ups:", L.save_png(L.sheet(close, 4), os.path.join(REVIEW, "04_clay_closeups.png")))
    tri = {o.name: tris_of(o) for o in objs}
    print("hi triangles per piece:", tri, "total", sum(tri.values()))
    low = {n: tris_of(o) for n, o in mod._LOW}
    print("low triangles per part:", low, "total", sum(low.values()))
    return objs, glow, root


def export(mod):
    objs, glow, root, rep, parts, res = None, None, None, None, None, None
    objs, glow, root, rep = mod.export()
    print("export report (centre, size, tris):", json.dumps(rep))
    stats = SR.map_stats(mod.WEAPON_ID, SK.OUT_DIR)
    print("maps:", json.dumps(stats))
    parts = [bpy.data.objects[mod.WEAPON_ID + "_Body"]] + [o for o in bpy.data.objects if o.name.startswith(mod.WEAPON_ID + "_Glow_")]
    res = SR.qa(parts)
    os.makedirs(REVIEW, exist_ok=True)
    with open(os.path.join(REVIEW, "SecretUnorthodox_qa.json"), "w") as f:
        json.dump(dict(report=rep, maps=stats, qa={k: res[k] for k in ("pass", "errors", "warnings")}), f, indent=1, default=str)
    return objs, glow, root, parts


def section_sheet(mod, path):
    """The blade's cross-section at four stations, true scale (x4 across: the blade is thin), drawn from the numbers the mesh is built from."""
    import sword_unorthodox_blade as BL
    b = mod.blade()
    cv = D.canvas(1200, 560, (0.07, 0.075, 0.09))
    D.text(cv, 12, 8, "BLADE CROSS-SECTIONS (EDGE LEFT, BACK RIGHT). TOP ROW TRUE SHAPE, BOTTOM ROW THICKNESS X3", (0.92, 0.93, 0.95), 2)
    names = {1: "EDGE BEVEL", 0: "HIRA", 2: "SHINOGI-JI + BACK", 3: "FULLER", 4: "DRIFT LINE"}
    cols = {1: (0.95, 0.95, 0.9), 0: (0.5, 0.62, 0.64), 2: (0.34, 0.42, 0.43), 3: (0.3, 0.7, 0.62), 4: (0.9, 0.55, 0.3)}
    for i, u in enumerate((0.08, 0.35, 0.62, 0.84)):
        loop, w = BL.section_loop(b, u, True)
        for row, ky in ((0, 1.0), (1, 3.0)):
            sc = 470 if row == 0 else 400
            ox, oy = 150 + i * 290, (150 if row == 0 else 410)
            # mirror x so the edge is at the left (a is toward the edge)
            pts = [(ox - a * sc, oy - y * sc * ky) for a, y, d, k, t in loop]
            D.fill(cv, pts, (0.45, 0.5, 0.52))
            for j in range(len(loop)):
                k = loop[j][3]
                if k in (1, 3, 4):
                    q = loop[(j + 1) % len(loop)]
                    D.line(cv, [pts[j], (ox - q[0] * sc, oy - q[1] * sc * ky)], cols[k], 1.6)
        D.text(cv, 60 + i * 290, 250, "STATION %.2f  WIDTH %.2f  THICKNESS %.3f" % (u, w, 2 * b.at(b.h, u)), (0.8, 0.82, 0.86), 1)
    x = 12
    for k in (1, 3, 4):
        D.text(cv, x, 535, names[k], cols[k], 1)
        x += 220
    return D.save(cv, path)


def review(mod, looks_only=False):
    SK.fresh()
    wid = mod.WEAPON_ID
    folder = SK.OUT_DIR
    body, glows = SR.load_game(wid, folder)
    mine = [body] + glows
    L.lab()
    coll = bpy.context.scene.collection
    # neutral light: six views, then close-ups
    tiles = [L.shoot(mine, v, size=(300, 680), samples=64, ortho=v in ("top", "bottom", "edge_r", "edge_l")) for v in MAT_VIEWS]
    print(L.save_png(L.sheet(tiles, 6), os.path.join(REVIEW, "05_material_neutral.png")))
    close = [L.shoot(mine, v, size=(560, 560), samples=72, ortho=False, centre=bpos(c), span=span) for v, c, span in CLOSE]
    print(L.save_png(L.sheet(close, 4), os.path.join(REVIEW, "06_closeups_guard_grip_pommel.png")))
    detail = [L.shoot(mine, "top", size=(640, 640), samples=72, ortho=True, centre=bpos((0.1, 0.0, -4.0)), span=2.6, tag="d1"),
              L.shoot(mine, "front34", size=(640, 640), samples=72, ortho=False, centre=bpos((0.0, 0.0, -1.2)), span=1.9, tag="d2"),
              L.shoot(mine, "top", size=(640, 640), samples=72, ortho=True, centre=bpos((-0.35, 0.0, -1.5)), span=2.0, tag="d3"),
              L.shoot(mine, "back34", size=(640, 640), samples=72, ortho=False, centre=bpos((0.0, 0.0, 0.1)), span=1.7, tag="d4")]
    print(L.save_png(L.sheet(detail, 4), os.path.join(REVIEW, "07_ornament_blade_guard_grip.png")))
    # dark dramatic light (no glow, no aura: the VFX-off view)
    with Dark():
        tiles = [L.shoot(mine, v, size=(300, 680), samples=96, ortho=False, transparent=False) for v in ("front34", "back34", "top", "edge_r")]
        tiles += [L.shoot(mine, "front34", size=(560, 680), samples=96, ortho=False, centre=bpos((0.0, 0.0, -1.5)), span=3.4, transparent=False)]
        print(L.save_png(L.sheet(tiles, 5, bg=(0.02, 0.02, 0.03, 1)), os.path.join(REVIEW, "08_vfx_off_dark_light.png")))
    if looks_only:
        return
    # the hand: a real R15 right hand and forearm at true size, the weapon in the grip as CombatFx holds it (arm hanging)
    hand = r15(coll, 0.55)
    hold(mine)
    nearest, inside = clearance(body)
    print("clearance (pommel ring and cap, behind z 0.62): nearest the forearm box %.3f studs, nearest the hand box %.3f; vertices inside the forearm box: %d" % (nearest["forearm"], nearest["hand"], inside))
    held = [L.shoot(mine + hand, "edge_r", size=(900, 560), samples=48, ortho=True, centre=bpos((0.0, 0.0, 0.2)), span=4.2, roll_up=(0, 0, 1), tag="h1"),
            L.shoot(mine + hand, "top", size=(900, 560), samples=48, ortho=True, centre=bpos((0.0, 0.0, 0.2)), span=4.2, roll_up=(1, 0, 0), tag="h2"),
            L.shoot(mine + hand, V((0.8, 0.5, 0.9)), size=(900, 560), samples=48, ortho=False, centre=bpos((0.0, 0.0, 0.5)), span=3.6, roll_up=(0, 0, 1), tag="h3"),
            L.shoot(mine + hand, "pommel", size=(900, 560), samples=48, ortho=False, centre=bpos((0.0, 0.0, 0.0)), span=3.4, roll_up=(0, 0, 1), tag="h4")]
    print(L.save_png(L.sheet(held, 2), os.path.join(REVIEW, "09_hand_test_r15.png")))
    # next to Sword6 at the same scale, each in a true hand
    cmp_id, dx = mod.COMPARE
    obody, oglows = SR.load_game(cmp_id, os.path.join(SK.REPO, "assets", "weapons"), (0, 0, 0))
    hold([obody] + oglows)
    others = [obody] + oglows
    for o in hand:
        o.hide_render = True
    # place Sword6's hand and the new one side by side: shift Sword6 by dx along +X
    for o in others:
        o.location = o.location + V((dx, 0, 0))
    hand2 = r15(coll, 0.55)
    for o in hand2:
        o.location = o.location + V((dx, 0, 0))
    for o in hand:
        o.hide_render = False
    both = mine + others + hand + hand2
    views = [L.shoot(both, "top", size=(760, 700), samples=48, ortho=True, centre=bpos((dx / 2, 0.0, -2.2)), span=7.8, roll_up=(0, 1, 0), tag="c1"),
             L.shoot(both, V((0.6, 0.5, 0.7)), size=(760, 700), samples=48, ortho=False, centre=bpos((dx / 2, 0.0, -2.2)), span=8.2, roll_up=(0, 0, 1), tag="c2")]
    print(L.save_png(L.sheet(views, 2), os.path.join(REVIEW, "10_vs_Sword6_same_scale.png")))
    L.set_visible(others + hand + hand2, False)
    # black silhouettes at thumbnail size
    # (the weapon back in its authored frame)
    SK.fresh()
    body, glows = SR.load_game(wid, folder)
    mine = [body] + glows
    sil = SR.silhouette_tiles(mine, ("top", "edge_r", "front34", "pommel"), size=(180, 380), ortho=False)
    sil += SR.silhouette_tiles(mine, ("top", "front34"), size=(90, 190), ortho=False)
    sil += SR.silhouette_tiles(mine, ("top", "front34"), size=(48, 100), ortho=False)
    print(L.save_png(L.sheet(sil, len(sil), bg=(0.5, 0.5, 0.5, 1)), os.path.join(REVIEW, "11_silhouette_black.png")))
    print(SR.maps_sheet(wid, folder, os.path.join(REVIEW, "12_maps_thumbnail.png")))
    print(section_sheet(mod, os.path.join(REVIEW, "13_blade_cross_sections.png")))


def verify(mod):
    """Re-imports the written FBX into an empty scene and checks what Roblox will get: one mesh, one material, one UV set inside 0..1, the
    triangle count, the size, the maps beside it, no machine path left in the file; runs the QA gate on the imported mesh."""
    import re
    SK.fresh()
    fbx = os.path.join(SK.OUT_DIR, mod.WEAPON_ID + ".fbx")
    objs = L.import_game(fbx)
    meshes = [o for o in objs if o.type == "MESH"]
    out = {"objects": [o.name for o in objs]}
    body = next(o for o in meshes if o.name.startswith(mod.WEAPON_ID + "_Body"))
    me = body.data
    uvs = np.array([l.uv[:] for l in me.uv_layers.active.data])
    out.update(meshes=len(meshes), materials=len(me.materials), uv_layers=len(me.uv_layers), tris=tris_of(body),
               uv_min=[float(x) for x in uvs.min(0)], uv_max=[float(x) for x in uvs.max(0)], scale=[round(x, 4) for x in body.scale],
               dimensions_studs=[round(x, 3) for x in body.dimensions], vertices=len(me.vertices))
    raw = open(fbx, "rb").read()
    out["fbx_bytes"] = len(raw)
    out["machine_path_left"] = len(re.findall(rb"/Users/(?!user)[A-Za-z0-9_.-]+", raw))
    out["fake_path_present"] = b"/Users/user" in raw
    res = SR.qa(meshes)
    out["qa"] = {k: res[k] for k in ("pass", "errors", "warnings")}
    for key in ("color", "normal", "roughness", "metalness"):
        out["map_" + key] = os.path.exists(os.path.join(SK.OUT_DIR, "%s_%s.png" % (mod.WEAPON_ID, key)))
    with open(os.path.join(REVIEW, "SecretUnorthodox_qa_fbx_reimport.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("verify:", json.dumps(out, default=str))
    return out


def run(mod, stage):
    if stage in ("study", "all"):
        import sword_unorthodox_study as S
        S.board()
        S.silhouettes()
        S.round2()
    if stage in ("clay", "all"):
        clay(mod)
    if stage in ("export", "all"):
        export(mod)
    if stage == "verify":
        verify(mod)
    if stage == "look":
        review(mod, looks_only=True)
    if stage in ("review", "all"):
        review(mod)

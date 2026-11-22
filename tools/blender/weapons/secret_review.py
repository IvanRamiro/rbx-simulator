"""The stages every faction weapon script runs (headless):

    clay      build the hi-detail weapon, render it in neutral grey from the sides (shape alone, no paint);
    export    build, bake, write assets/weapons/<Id>.fbx, its four maps and the placements file, run the QA gate,
              check the maps (not blank, metal where metal should be);
    review    import what was written (the game mesh, the maps, the Neon pieces), rebuild its material from the four
              PNGs, and render material views, the hand test, the Sword6/Spear6 comparison, black silhouettes at
              thumbnail size, and the maps on a dark ground at thumbnail size;
    all       the three, in this order (clay and export in one process, review in the same).

Everything goes to renders/faction_weapons/ (local, never committed).
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

V = Vector
REVIEW = SK.REVIEW
def _qa_dir():
    """The asset QA gate's scripts (qa_check.py): QA_CHECK_DIR, or the installed Blender skill pack's copy."""
    import glob
    if os.environ.get("QA_CHECK_DIR"):
        return os.environ["QA_CHECK_DIR"]
    found = sorted(glob.glob(os.path.expanduser("~/.*/plugins/cache/blender-agent-skills/*/*/skills/blender-asset-qa/scripts")))
    return found[-1] if found else ""


SKILL = _qa_dir()

DEFAULT_CLOSE = (("front34", (0, 0, -1.0), 3.0), ("top", (0, 0, -0.5), 3.0), ("back34", (0, 0, 0.4), 3.0), ("edge_r", (0, 0, 0.2), 3.0))
CLAY_VIEWS = ("top", "bottom", "edge_r", "edge_l", "front34", "back34")


def _glow_objs(glow):
    return [o for _, (_, objs) in glow.items() for o in objs]


def clay(mod, tag="clay", samples=36):
    objs, glow, root = mod.build()
    everything = objs + _glow_objs(glow)
    L.lab()
    L.glow_strength(_glow_objs(glow), 5.0)
    tiles = []
    with L.clay(everything):
        for v in CLAY_VIEWS:
            tiles.append(L.shoot(everything, v, size=(300, 620), samples=samples, ortho=v in ("top", "bottom", "edge_r", "edge_l")))
    path = L.save_png(L.sheet(tiles, len(tiles)), os.path.join(REVIEW, "%s_%s.png" % (mod.WEAPON_ID, tag)))
    print("clay sheet:", path)
    close = []
    with L.clay(everything):
        for v, c, span in getattr(mod, "CLOSE", DEFAULT_CLOSE):
            close.append(L.shoot(everything, v, size=(520, 520), samples=samples, ortho=False, centre=V((c[0], -c[2], c[1])), span=span))
    print("clay close-ups:", L.save_png(L.sheet(close, len(close)), os.path.join(REVIEW, "%s_%s_close.png" % (mod.WEAPON_ID, tag))))
    tri = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in everything}
    print("hi triangles per piece:", tri, "total", sum(tri.values()))
    return objs, glow, root


def map_stats(weapon_id, folder):
    """Reads the four PNGs raw (Non-Color) and reports what they hold."""
    out = {}
    for key in ("color", "normal", "roughness", "metalness"):
        path = os.path.join(folder, "%s_%s.png" % (weapon_id, key))
        img = bpy.data.images.load(path, check_existing=False)
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
        out[key] = dict(size=(w, h), mean=[round(float(x), 3) for x in a.mean((0, 1))], lo=round(float(a.min()), 3), hi=round(float(a.max()), 3),
                        std=round(float(a.std()), 3))
        bpy.data.images.remove(img)
    return out


def qa(parts, profile="roblox"):
    sys.path.insert(0, SKILL)
    import qa_check
    res = qa_check.run(objects=[o.name for o in parts], profile=profile)
    print("QA pass:", res["pass"])
    for e in res["errors"]:
        print("  ERROR", e)
    for w in res["warnings"]:
        print("  warn ", w)
    return res


def export(mod, report=True):
    objs, glow, root, rep = mod.export()
    print("export report (centre, size, tris):", json.dumps(rep))
    stats = map_stats(mod.WEAPON_ID, SK.OUT_DIR)
    print("maps:", json.dumps(stats))
    parts = [bpy.data.objects[mod.WEAPON_ID + "_Body"]] + [o for o in bpy.data.objects if o.name.startswith(mod.WEAPON_ID + "_Glow_")]
    res = qa(parts)
    os.makedirs(REVIEW, exist_ok=True)
    with open(os.path.join(REVIEW, mod.WEAPON_ID + "_qa.json"), "w") as f:
        json.dump(dict(report=rep, maps=stats, qa={k: res[k] for k in ("pass", "errors", "warnings")}), f, indent=1, default=str)
    return objs, glow, root, parts


# ---------- reviewing what was written ----------
def game_material(name, prefix):
    """What SurfaceAppearance will do with the four maps: colour (sRGB), the others as data, normal in tangent space."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
    t.links.new(bsdf.outputs[0], out.inputs[0])
    for key, socket in (("color", "Base Color"), ("roughness", "Roughness"), ("metalness", "Metallic")):
        img = bpy.data.images.load(prefix + "_%s.png" % key, check_existing=True)
        img.colorspace_settings.name = "sRGB" if key == "color" else "Non-Color"
        nd = t.nodes.new("ShaderNodeTexImage")
        nd.image = img
        t.links.new(nd.outputs["Color"], bsdf.inputs[socket])
    nimg = bpy.data.images.load(prefix + "_normal.png", check_existing=True)
    nimg.colorspace_settings.name = "Non-Color"
    nd = t.nodes.new("ShaderNodeTexImage")
    nd.image = nimg
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(nd.outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def glow_material(hexstr, strength=4.0):
    m = K_glow(hexstr)
    em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
    em.inputs["Strength"].default_value = strength
    return m


def K_glow(hexstr):
    return SK.K.glow_material(hexstr)


def load_game(weapon_id, folder, offset=(0, 0, 0)):
    """Imports the FBX and dresses it from the PNGs. Returns (body, glow pieces)."""
    objs = L.import_game(os.path.join(folder, weapon_id + ".fbx"), offset)
    body = next(o for o in objs if o.name.startswith(weapon_id + "_Body"))
    glows = [o for o in objs if "_Glow_" in o.name]
    mat = game_material(weapon_id + "_Game", os.path.join(folder, weapon_id))
    body.data.materials.clear()
    body.data.materials.append(mat)
    for o in glows:
        hexstr = o.name.split("_Glow_")[1].split(".")[0]
        o.data.materials.clear()
        o.data.materials.append(glow_material(hexstr))
    return body, glows


def silhouette_tiles(objs, views, size=(170, 340), ortho=True):
    L.SKY = False
    scene = L.lab()
    scene.render.film_transparent = False
    tiles = []
    try:
        with L.black(objs):
            for v in views:
                tiles.append(L.shoot(objs, v, size=size, samples=8, ortho=ortho, transparent=False))
    finally:
        L.SKY = True
        L.lab()
    return tiles


def maps_sheet(weapon_id, folder, path):
    """The maps on a dark ground, large and at 64 px, the way a stranger would see them."""
    tiles = []
    for key in ("color", "normal", "roughness", "metalness"):
        img = bpy.data.images.load(os.path.join(folder, "%s_%s.png" % (weapon_id, key)), check_existing=False)
        img.colorspace_settings.name = "sRGB"
        w, h = img.size
        a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
        bpy.data.images.remove(img)
        step = max(1, w // 384)
        big = a[::step, ::step]
        small = a[::max(1, w // 64), ::max(1, w // 64)]
        tiles.append((big, small))
    th = tiles[0][0].shape[0]
    canvas = np.zeros((th + 90, sum(t[0].shape[1] for t in tiles) + 10 * len(tiles), 4), dtype=np.float32)
    canvas[:] = (0.05, 0.05, 0.06, 1)
    x = 5
    for big, small in tiles:
        canvas[5:5 + big.shape[0], x:x + big.shape[1]] = big
        canvas[th + 15:th + 15 + small.shape[0], x:x + small.shape[1]] = small
        x += big.shape[1] + 10
    canvas[..., 3] = 1
    return L.save_png(canvas, path)


def review(mod, compare=None):
    """compare: ("Sword6", offset) — a realm weapon to stand next to it, held at the same scale."""
    SK.fresh()
    wid = mod.WEAPON_ID
    folder = SK.OUT_DIR
    body, glows = load_game(wid, folder)
    mine = [body] + glows
    scene = L.lab()
    coll = scene.collection
    # six views of the game result
    tiles = [L.shoot(mine, v, size=(300, 640), samples=48, ortho=v in ("top", "bottom", "edge_r", "edge_l")) for v in ("top", "bottom", "edge_r", "edge_l", "front34", "back34")]
    p1 = L.save_png(L.sheet(tiles, 6), os.path.join(REVIEW, wid + "_game6.png"))
    # close-ups of the working end: guard, grip, pommel
    lo, hi = L.bounds(mine)
    close = []
    hilt = mod.hilt_tip()[0]
    for v, c, span in (("front34", (0, 0, hilt[2] + 0.3), 3.2), ("top", (0, 0, 0.0), 3.4), ("back34", (0, 0, 0.5), 3.2), ("edge_r", (0, 0, 0.3), 3.4)):
        close.append(L.shoot(mine, v, size=(520, 520), samples=56, ortho=False, centre=V((c[0], -c[2], c[1])), span=span))
    p2 = L.save_png(L.sheet(close, 4), os.path.join(REVIEW, wid + "_closeups.png"))
    # the hand
    hand = L.hand_proxy(coll)
    for o in hand:
        for m in o.data.materials:
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Alpha"].default_value = 0.35
    held = [L.shoot(mine + hand, v, size=(460, 520), samples=40, centre=V((0, 0, 0)), span=3.4, ortho=True) for v in ("top", "edge_r")]
    p3 = L.save_png(L.sheet(held, 2), os.path.join(REVIEW, wid + "_hand.png"))
    L.set_visible(hand, False)
    # next to a realm weapon, same scale, same hands
    p4 = None
    if compare:
        other_id, dx = compare
        obody, oglows = load_game(other_id, os.path.join(SK.REPO, "assets", "weapons"), (dx, 0, 0))
        others = [obody] + oglows
        for o in hand:
            h2 = o.copy()
            coll.objects.link(h2)
            h2.location = h2.location + V((dx, 0, 0))
            others.append(h2)
        L.set_visible(hand, True)
        both = mine + others + hand
        views = [L.shoot(both, v, size=(560, 700), samples=40, ortho=True) for v in ("top",)] + [L.shoot(both, "front34", size=(560, 700), samples=40, ortho=False)]
        p4 = L.save_png(L.sheet(views, 2), os.path.join(REVIEW, "%s_vs_%s.png" % (wid, other_id)))
        L.set_visible(hand, False)
        L.set_visible(others, False)
    # silhouettes at thumbnail size, black on white: the sides the player sees
    sil = silhouette_tiles(mine, ("top", "edge_r", "front34"), size=(180, 360), ortho=False)
    sil += silhouette_tiles(mine, ("top", "edge_r"), size=(90, 180), ortho=False)
    p5 = L.save_png(L.sheet(sil, len(sil), bg=(0.5, 0.5, 0.5, 1)), os.path.join(REVIEW, wid + "_silhouette.png"))
    p6 = maps_sheet(wid, folder, os.path.join(REVIEW, wid + "_maps.png"))
    print("review images:", p1, p2, p3, p4, p5, p6, sep="\n  ")


def run(mod, stage):
    if stage in ("clay", "all"):
        clay(mod)
    if stage in ("export", "all"):
        export(mod)
    if stage in ("review", "all"):
        review(mod, getattr(mod, "COMPARE", None))

"""Headless runner for Nightfall Citadel's vegetation, rocks and paths (nightfall_veg.py). Never the open Blender window.

    HQ_QA_SCRIPT=<blender-asset-qa>/scripts/qa_check.py \
    blender -b --factory-startup -P tools/blender/world/nightfall_veg_run.py -- <stage> [piece names]
      contract    (plain python is enough) veg_pieces.json from the pieces alone: names, triangles, bounds, colliders, looks: the EARLY contract for the placer
      look        a quick paint contact sheet of the named pieces (default: every tree) into renders/nightfall/veg/look_*.png
      sheets      six-side clay and paint sheets of every piece, and the paint contact sheet per family
      silhouette  black silhouettes (two views) of every Nightfall tree and rock and of every other map's (Windrift's included), and the overlap numbers
      qa          qa_check.py (profile roblox) on every piece
      export      QA, then the three FBX files, veg_pieces.json and the verification re-import
      verify      numeric checks (budgets, flat bases, paths, the planned mix, FBX re-import), written to renders/nightfall/veg/verify.txt
    python3 tools/blender/world/nightfall_veg_run.py sheet     the uniqueness sheet (headless Chrome) from the silhouette stage's pictures
Evidence goes to renders/nightfall/veg/ (local, never committed). Every piece stands upright: in the side views +X runs to the right of the picture.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "nightfall", "veg")
OUT = os.path.join(REPO, "assets", "world", "MurimCrossing", "Nightfall")
UNIQ = os.path.join(RENDERS, "uniq")
FILES = {"Trees": "Nightfall_Trees.fbx", "Plants": "Nightfall_Plants.fbx", "Rocks": "Nightfall_Rocks.fbx"}
ANCHOR = "NF_Anchor"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
STAGE = ARGS[0] if ARGS else "look"
NAMES = ARGS[1:]

try:
    import bpy  # noqa: E402
    import bmesh  # noqa: E402
    from mathutils import Vector  # noqa: E402
    import hq_blender as B  # noqa: E402
    import worldlib as W  # noqa: E402
    HAVE_BPY = True
except ImportError:
    HAVE_BPY = False

import nightfall_veg as V  # noqa: E402

os.makedirs(RENDERS, exist_ok=True)

if HAVE_BPY:
    # the preview colours of the suffixes: derived from the looks (always: the shared kit has its own "Stone", "Gold"... names)
    for suffix, look in V.LOOKS.items():
        c = tuple(look["Color"])
        mat = look["Material"]
        metal = {"Metal": 0.55, "CorrodedMetal": 0.3}.get(mat, 0.0)
        rough = {"Metal": 0.35, "CorrodedMetal": 0.6, "Glass": 0.05, "SmoothPlastic": 0.5, "Slate": 0.8, "Basalt": 0.8, "Fabric": 0.9, "Concrete": 0.9, "Sand": 0.95}.get(mat, 0.75)
        emit = ((c[0], c[1], c[2]), 3.0) if mat in ("CrackedLava", "Neon") else None
        B.PREVIEW[suffix] = (c, rough, metal, emit, None)

SMOOTH = {}
SMOOTH_DEFAULT = 18.0          # angular: only near-flat neighbours share a normal, every real facet stays hard


def zf_pairs(geo):
    """The shell pairs of one Geo that the asset QA's z-fighting test flags, found the way the QA finds them (Blender's own triangulation, BVH, four sample
    points per triangle, normals within 2.5 degrees, plane distance under 0.001), plus the count of flagged pairs inside one shell."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    vs = [bm.verts.new(W.rb(*p)) for p in geo.v]
    for f in geo.f:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    verts = [v.co.copy() for v in bm.verts]
    tris = [tuple(v.index for v in f.verts) for f in bm.faces]
    norms = [f.normal.copy() for f in bm.faces]
    bm.free()
    bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    sets = [set(t) for t in tris]
    shell, _ = V._shells(geo)
    cross, inside = set(), 0
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = norms[ti]
        if n.length < 0.5:
            continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, 0.001):
                if tj is None or tj == ti or sets[ti] & sets[tj]:
                    continue
                n2 = norms[tj]
                if n.dot(n2) < 0.999:
                    continue
                a2, b2, c2 = (verts[i] for i in tris[tj])
                q = p - n2 * n2.dot(p - a2)
                v0, v1, v2 = c2 - a2, b2 - a2, q - a2
                d00, d01, d02, d11, d12 = v0.dot(v0), v0.dot(v1), v0.dot(v2), v1.dot(v1), v1.dot(v2)
                den = d00 * d11 - d01 * d01
                if abs(den) < 1e-12:
                    continue
                u = (d11 * d02 - d01 * d12) / den
                v = (d00 * d12 - d01 * d02) / den
                if u >= -1e-6 and v >= -1e-6 and u + v <= 1 + 1e-6:
                    sa, sb = shell[t[0]], shell[tris[tj][0]]
                    if sa == sb:
                        inside += 1
                    else:
                        cross.add((min(sa, sb), max(sa, sb)))
    return cross, inside


def decollide(geo, tries=10):
    """Rolls one shell of each flagged pair a few degrees about its own long axis until the QA's z-fighting test finds nothing (blades from one root can
    land on near-parallel faces by chance). Deterministic. Returns (shells turned, flagged pairs left)."""
    turned = 0
    cross, inside = zf_pairs(geo)
    for it in range(tries):
        if not cross:
            break
        shell, n = V._shells(geo)
        members = {}
        for i, sh in enumerate(shell):
            members.setdefault(sh, []).append(i)
        done = set()
        for a, b in sorted(cross):
            sh = max(a, b) if (it % 2 == 0) else min(a, b)
            if sh in done:
                continue
            done.add(sh)
            vs = members[sh]
            p0 = geo.v[vs[0]]
            far = geo.v[vs[-1]]
            axis = V.vnorm(V.vsub(far, p0)) if V.vlen(V.vsub(far, p0)) > 1e-6 else (1.0, 0.0, 0.0)
            ang = (0.06 + 0.035 * it) * (1 if (sh + it) % 2 else -1)
            for i in vs:
                geo.v[i] = V.vadd(p0, V._rot(V.vsub(geo.v[i], p0), axis, ang))
            turned += 1
        cross, inside = zf_pairs(geo)
    return turned, len(cross) + inside


_BUILT = {}


def build(names=None):
    key = tuple(names) if names else None
    if key in _BUILT:
        return _BUILT[key]
    data = V.build_all(names)
    for n, piece in data["pieces"].items():
        if "_Rocks_" in n:          # convex stone and the walkable paths are never rolled: their faces are exact
            continue
        for suffix, geo in piece.g.items():
            V.decollide(geo)        # the plain-python mirror of the QA's z-fighting test (so the contract and the FBX agree)
            if HAVE_BPY:
                t, left = decollide(geo)
                if left:
                    print("z-fight pairs left in", n, suffix, left)
    V.finish_meta(data)
    _BUILT[key] = data
    return data


def piece_objs(name, piece, coll, mode="paint"):
    out = []
    for suffix, geo in sorted(piece.g.items()):
        if not geo.f:
            continue
        me = B.mesh_from_geo("%s__%s" % (name, suffix), geo, suffix, SMOOTH.get(suffix, SMOOTH_DEFAULT))
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        out.append(o)
    if mode != "paint":
        B.set_material_mode(out, mode)
    return out


def new_scene():
    B.clear_scene()
    coll = bpy.data.collections.new("v")
    bpy.context.scene.collection.children.link(coll)
    return coll


# ---------------------------------------------------------------------------------------------------------------------------------
# image helpers (numpy ships with Blender)
# ---------------------------------------------------------------------------------------------------------------------------------
def load_pixels(path):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def save_pixels(px, path):
    h, w = px.shape[0], px.shape[1]
    img = bpy.data.images.new("out", w, h, alpha=False)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def resize(px, h, w):
    import numpy as np
    ys = np.linspace(0, px.shape[0] - 1, h).astype(int)
    xs = np.linspace(0, px.shape[1] - 1, w).astype(int)
    return px[ys][:, xs]


def bounds_of(objs):
    return B.bbox_roblox(objs)


def ortho_cam(name, view, lo, hi, pad=1.18):
    """front: camera at -Z (+X is on the LEFT); back: camera at +Z (+X on the RIGHT: the usual view); left: from -X (looking downwind); right: from +X
    (looking into the wind); top: from above, +X right, the front (-Z) up; q3: a perspective from the +Z side, a little windward and above."""
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = [hi[i] - lo[i] for i in range(3)]
    D = 300.0
    if view == "front":
        loc, size = (c[0], c[1], c[2] - D), max(ext[0], ext[1])
    elif view == "back":
        loc, size = (c[0], c[1], c[2] + D), max(ext[0], ext[1])
    elif view == "left":
        loc, size = (c[0] - D, c[1], c[2]), max(ext[2], ext[1])
    elif view == "right":
        loc, size = (c[0] + D, c[1], c[2]), max(ext[2], ext[1])
    elif view == "top":
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = max(ext[0], ext[2]) * pad
        cam.data.clip_end = 2000
        cam.location = B.rbv(c[0], c[1] + D, c[2])
        cam.rotation_euler = (0.0, 0.0, 0.0)
        return cam
    else:
        size = max(ext)
        loc = (c[0] - size * 0.55, c[1] + ext[1] * 0.2 + size * 0.5, c[2] + size * 1.45)
        return B.add_camera(name, B.rbv(*loc), B.rbv(*c), lens=36.0)
    return B.add_camera(name, B.rbv(*loc), B.rbv(*c), ortho=size * pad)


def lighting(strength=2.8, azimuth=-35.0):
    B.set_world((0.62, 0.66, 0.74), 1.0)
    B.set_sun(strength, (-50.0, 0.0, azimuth), (1.0, 0.97, 0.92))


def mosaic(images, cols, tile=300, bg=0.93):
    import numpy as np
    rows = (len(images) + cols - 1) // cols
    sheet = np.ones((rows * tile, cols * tile, 4), np.float32) * bg
    sheet[:, :, 3] = 1.0
    for i, px in enumerate(images):
        r, c = divmod(i, cols)
        h, w = px.shape[0], px.shape[1]
        k = tile / max(h, w)
        t = resize(px, max(1, int(h * k)), max(1, int(w * k)))
        y0 = (r + 1) * tile - t.shape[0]
        x0 = c * tile + (tile - t.shape[1]) // 2
        sheet[rows * tile - y0 - t.shape[0]: rows * tile - y0, x0:x0 + t.shape[1]] = t
    return sheet


def ground_and_peg(coll, lo, hi, peg=True):
    """A flat dark ground disc at y = 0 and a 2 x 5 x 1 stud peg (a player's size) beside the piece, for scale."""
    ext = max(hi[0] - lo[0], hi[2] - lo[2])
    R = max(ext * 0.7, 4.0)
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    objs = []
    me = bpy.data.meshes.new("ground")
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=R, segments=40)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("ground", me)
    coll.objects.link(g)
    g.location = B.rbv(cx, -0.02, cz)
    m = bpy.data.materials.get("wr_ground") or bpy.data.materials.new("wr_ground")
    m.diffuse_color = (0.12, 0.14, 0.11, 1.0)
    nodes = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
    if nodes:
        nodes[0].inputs["Base Color"].default_value = (0.09, 0.11, 0.08, 1.0)
        nodes[0].inputs["Roughness"].default_value = 0.95
    me.materials.append(m)
    objs.append(g)
    if peg:
        me2 = bpy.data.meshes.new("peg")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(2.0, 1.0, 5.0), verts=bm.verts)     # blender frame: x 2, y 1, z (up) 5
        bm.to_mesh(me2)
        bm.free()
        p = bpy.data.objects.new("peg", me2)
        coll.objects.link(p)
        p.location = B.rbv(lo[0] - 2.2, 2.5, cz + 0.0)
        m2 = bpy.data.materials.get("wr_peg") or bpy.data.materials.new("wr_peg")
        nodes = [n for n in m2.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        if nodes:
            nodes[0].inputs["Base Color"].default_value = (0.8, 0.25, 0.2, 1.0)
        me2.materials.append(m2)
        objs.append(p)
    return objs


def render_views(name, piece, views, mode, res=(480, 480), peg=True, ground=True):
    coll = new_scene()
    objs = piece_objs(name, piece, coll, mode)
    B.setup_render(res, samples=10)
    bpy.context.scene.render.film_transparent = False
    lighting()
    if mode == "clay":
        B.set_world((0.55, 0.55, 0.55), 1.0)
    lo, hi = bounds_of(objs)
    if ground:
        extra = ground_and_peg(coll, lo, hi, peg)
        lo2, hi2 = bounds_of(objs + [o for o in extra if o.name.startswith("peg")]) if peg else (lo, hi)
        lo, hi = [min(a, b) for a, b in zip(lo, lo2)], [max(a, b) for a, b in zip(hi, hi2)]
    imgs = []
    for v in views:
        cam = ortho_cam("cam_" + v, v, lo, hi)
        path = os.path.join(RENDERS, "_tmp_%s.png" % v)
        B.shoot(cam, path)
        imgs.append(load_pixels(path))
    return imgs


# ---------------------------------------------------------------------------------------------------------------------------------
def look():
    data = build(NAMES or None)
    names = NAMES or [n for n in data["pieces"] if "_Trees_" in n]
    imgs = []
    for n in names:
        imgs += render_views(n, data["pieces"][n], ("back", "q3", "top"), "paint", res=(420, 420))
    sheet = mosaic(imgs, 3, tile=380)
    tag = "_".join(x.split("_")[-1] for x in names[:3]) if len(names) <= 3 else names[0].split("_")[-1] + "_set"
    save_pixels(sheet, os.path.join(RENDERS, "look_%s.png" % tag))
    print("looked", names, "->", "look_%s.png" % tag)
    for n in names:
        lo, hi = data["pieces"][n].bounds()
        print("  %-36s %5d tris  %s  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (n, data["pieces"][n].tris(), data["pieces"][n].stats(), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))


def overview():
    """One paint sheet per family: for each piece the side view and the quarter view, four pictures to a row (renders/nightfall/veg/over_<Family>.png)."""
    data = build(NAMES or None)
    for fam in ("Trees", "Rocks", "Plants"):
        names = [n for n in data["pieces"] if "_%s_" % fam in n]
        if not names:
            continue
        imgs = []
        for n in names:
            imgs += render_views(n, data["pieces"][n], ("back", "q3"), "paint", res=(360, 360))
        save_pixels(mosaic(imgs, 4, tile=300), os.path.join(RENDERS, "over_%s.png" % fam))
        print("overview", fam, len(names), "pieces:", ", ".join(x.split("_")[-1] for x in names))


def sheets():
    """Six-side clay and paint sheets (wind right, from the other side, from upwind, from downwind, top, quarter) of every piece, then one paint
    sheet per family."""
    data = build(NAMES or None)
    fams = ("Trees", "Rocks", "Plants")
    for n, piece in data["pieces"].items():
        views = ("back", "front", "left", "right", "top", "q3")
        imgs = render_views(n, piece, views, "clay", res=(360, 360))
        save_pixels(mosaic(imgs, 3, tile=330, bg=0.9), os.path.join(RENDERS, "six_%s_clay.png" % n.replace("Nightfall_", "")))
        imgs = render_views(n, piece, views, "paint", res=(360, 360))
        save_pixels(mosaic(imgs, 3, tile=330, bg=0.9), os.path.join(RENDERS, "six_%s_paint.png" % n.replace("Nightfall_", "")))
    if not NAMES:
        for fam in fams:
            names = [n for n in data["pieces"] if "_%s_" % fam in n]
            imgs = []
            for n in names:
                imgs += render_views(n, data["pieces"][n], ("q3",), "paint", res=(380, 380))
            save_pixels(mosaic(imgs, 5, tile=300), os.path.join(RENDERS, "paint_%s.png" % fam))
    print("sheets done")


# ---------------------------------------------------------------------------------------------------------------------------------
# silhouettes and the numeric comparison with every other map's trees and rocks
# ---------------------------------------------------------------------------------------------------------------------------------
# label, FBX (relative to assets/world), object-name prefixes (an asset = the objects sharing one name before "__"; None = every asset of the file),
# kind (tree or rock), and an optional filter on names (the file may hold buildings too)
OTHERS = [
    ("Windrift", "MurimCrossing/Windrift/Windrift_Trees.fbx", None, "tree"),
    ("Windrift", "MurimCrossing/Windrift/Windrift_Rocks.fbx", None, "rock"),
    ("Jade Grove (new)", "JadeGrove/Library/JadeGrove_Trees.fbx", None, "tree"),
    ("Jade Grove (new)", "JadeGrove/Library/JadeGrove_Bamboo.fbx", None, "tree"),
    ("Jade Grove (new)", "JadeGrove/Library/JadeGrove_Rocks.fbx", None, "rock"),
    ("Dawnspire", "MurimCrossing/Dawnspire/Dawnspire_Trees.fbx", None, "tree"),
    ("Dawnspire", "MurimCrossing/Dawnspire/Dawnspire_Rocks.fbx", None, "rock"),
    ("Jade (old, replaced)", "JadeGrove/JadeGrove_Props.fbx", ["JG_AncientTreeA", "JG_AncientTreeB", "JG_BambooClump"], "tree"),
    ("Jade (old, replaced)", "JadeGrove/JadeGrove_Props.fbx", ["JG_JadeOutcrop", "JG_StandingStone"], "rock"),
    ("Jade (old, replaced)", "JadeGrove/JadeGrove_Island.fbx", ["JG_ElderTrunk"], "tree"),
    ("Blossom Sanctuary", "BlossomSanctuary/BlossomSanctuary_Trees.fbx", ["BS_TreeElder", "BS_TreeWeeping", "BS_TreeLeaning", "BS_TreeTwin", "BS_TreeYoung", "BS_TreeGnarled"], "tree"),
    ("Blossom Sanctuary", "BlossomSanctuary/BlossomSanctuary_Stones.fbx", ["BS_EdgeRockA", "BS_EdgeRockB", "BS_EdgeRockC", "BS_SteppingStoneA"], "rock"),
    ("Ember Peak", "EmberPeak/EmberPeak_Props.fbx", ["EP_PetrifiedTreeA", "EP_PetrifiedTreeB"], "tree"),
    ("Ember Peak", "EmberPeak/EmberPeak_Props.fbx", ["EP_BasaltClusterA", "EP_BasaltClusterB", "EP_ObsidianShard"], "rock"),
    ("Moonlit Isle", "MoonlitIsle/MoonlitIsle_Props.fbx", ["MI_LunarRock", "MI_MoonstoneShards"], "rock"),
    ("Moonlit Isle", "MoonlitIsle/MoonlitIsle_Kit.fbx", ["MI_MoonstoneSpire"], "rock"),
    ("Origin Abyss", "OriginAbyss/OriginAbyss_Props.fbx", ["OA_ThornCrown"], "tree"),
    ("Origin Abyss", "OriginAbyss/OriginAbyss_Props.fbx", ["OA_SlateRock", "OA_VoidCrystals", "OA_RuinPillar"], "rock"),
]
SIZE = 150


def mask_from(px):
    import numpy as np
    m = px[:, :, 0] < 0.4
    ys, xs = np.where(m)
    if len(ys) == 0:
        return m
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def sil_setup(res=420):
    B.setup_render((res, res), samples=4)
    B.set_world((1.0, 1.0, 1.0), 1.0)
    B.set_sun(0.0, (-50, 0, 0))
    bpy.context.scene.render.film_transparent = False


def shoot_mask(objs, view, res=420):
    lo, hi = bounds_of(objs)
    cam = ortho_cam("cam_sil_" + view, view, lo, hi, pad=1.08)
    path = os.path.join(RENDERS, "_tmp_sil.png")
    B.shoot(cam, path)
    return mask_from(load_pixels(path))


def save_mask_png(mask, path, size=SIZE):
    import numpy as np
    h, w = mask.shape
    k = (size - 8) / max(h, w)
    th, tw = max(1, int(round(h * k))), max(1, int(round(w * k)))
    m = resize(mask.astype(np.float32), th, tw) > 0.5
    px = np.ones((size, size, 4), np.float32)
    y0 = size - 4 - th
    x0 = (size - tw) // 2
    sub = px[size - 4 - th: size - 4, x0:x0 + tw]
    sub[m] = (0.0, 0.0, 0.0, 1.0)
    save_pixels(px, path)


def fit(mask, h):
    import numpy as np
    w = max(1, int(round(mask.shape[1] * h / mask.shape[0])))
    ys = np.linspace(0, mask.shape[0] - 1, h).astype(int)
    xs = np.linspace(0, mask.shape[1] - 1, w).astype(int)
    return mask[ys][:, xs]


def iou_height_fit(a, b, h=96):
    """IoU after fitting both to the same height (aspect kept), centred, best of a few shifts and of the mirrored second mask."""
    import numpy as np
    A, Bm = fit(a, h), fit(b, h)
    Wd = max(A.shape[1], Bm.shape[1]) + 16

    def place(m, dx):
        c = np.zeros((h, Wd), bool)
        x0 = (Wd - m.shape[1]) // 2 + dx
        c[:, max(0, x0):max(0, x0) + m.shape[1] - (max(0, x0) - x0)] = m[:, max(0, -x0):][:, :Wd - max(0, x0)]
        return c
    best = 0.0
    for flip in (False, True):
        bb = Bm[:, ::-1] if flip else Bm
        for dx in range(-6, 7, 2):
            pa, pb = place(A, 0), place(bb, dx)
            u = (pa | pb).sum()
            if u:
                best = max(best, (pa & pb).sum() / u)
    return best


def import_assets(path, prefixes):
    """Imports an FBX and keeps only the objects whose base name (before '__') is in prefixes (None: all but the anchor). Returns {asset: [objects]}."""
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    groups = {}
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            continue
        base = o.name.split(".")[0].split("__")[0]
        if base.endswith("_Anchor") or base.endswith("Anchor") and "__" not in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if prefixes is not None and base not in prefixes:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        groups.setdefault(base, []).append(o)
    return groups


def silhouette():
    """Stage 1 (in Blender): the black masks of every Nightfall tree and rock and every other map's, as pictures in uniq/ and the numbers in
    uniqueness.txt / uniqueness.json. The sheet itself comes from `python3 nightfall_veg_run.py sheet`."""
    import numpy as np
    os.makedirs(UNIQ, exist_ok=True)
    for f in os.listdir(UNIQ):
        os.remove(os.path.join(UNIQ, f))
    views = ("back", "right")
    masks = {}     # key -> {view: mask}
    meta = {}      # key -> (label, kind, w, h)
    data = build(None)
    for n, piece in data["pieces"].items():
        fam = n.split("_")[1]
        if fam == "Plants":
            continue
        if fam == "Rocks" and any(k in n for k in ("_BasaltPave", "_HexSteps")):
            continue
        coll = new_scene()
        objs = piece_objs(n, piece, coll, "black")
        sil_setup()
        key = "Nightfall@" + n.replace("Nightfall_", "")
        masks[key] = {v: shoot_mask(objs, v) for v in views}
        lo, hi = bounds_of(objs)
        meta[key] = ("Nightfall", "tree" if fam == "Trees" else "rock", hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    for label, rel, prefixes, kind in OTHERS:
        path = os.path.join(REPO, "assets", "world", rel)
        if not os.path.exists(path):
            print("MISSING FILE", path)
            continue
        groups = import_assets(path, prefixes)
        if prefixes:
            for p in prefixes:
                if p not in groups:
                    print("MISSING", p)
        for base, objs in groups.items():
            if label == "Windrift" and any(k in base for k in ("_Steps", "_Cobble", "_PlankWalk")):
                continue                    # Windrift's walkable path slabs are not rocks to compare with
            key = "%s@%s" % (label, base)
            if key in masks:
                continue
            if label.startswith("Jade Grove") and ("Guardian" in base and "Crown" in base):
                continue
            if label.startswith("Jade Grove") and base == "JG_Tree_Guardian":
                objs = objs + [o for b2, os2 in groups.items() if "GuardianCrown" in b2 for o in os2]
            for o in bpy.data.objects:
                o.hide_render = True
            for o in objs:
                o.data.materials.clear()
                o.data.materials.append(B.black_material())
                o.hide_render = False
            sil_setup()
            masks[key] = {v: shoot_mask(objs, v) for v in views}
            lo, hi = bounds_of(objs)
            meta[key] = (label, kind, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        print("masks:", label, os.path.basename(path), len(groups))
    # the Jade guardian: the crown is a second asset: merge the two for one mask would need a re-import; the trunk piece alone is used (reported)
    # pictures
    for key, mm in masks.items():
        for v in views:
            save_mask_png(mm[v], os.path.join(UNIQ, "%s__%s.png" % (key.replace("/", "_"), "front" if v == "back" else "side")))
        label, kind, w_, h_, d_ = meta[key]
        with open(os.path.join(UNIQ, key.replace("/", "_") + ".txt"), "w") as fh:
            fh.write("%.1f %.1f %.1f %s\n" % (w_, h_, d_, kind))
    # numbers: each Nightfall tree/rock against every other map's assets: the same kind first (trees and bamboo against trees, rocks against rocks), then all kinds
    mine = [k for k in masks if k.startswith("Nightfall@")]
    others = [k for k in masks if not k.startswith("Nightfall@")]
    kind = {k: meta[k][1] for k in masks}

    def pair(a, b):
        same = max(iou_height_fit(masks[a][v], masks[b][v]) for v in views)
        anyv = max(iou_height_fit(masks[a][v], masks[b][w]) for v in views for w in views)
        return same, anyv

    def profile(a, b):
        """A Nightfall piece's 'back' view against either view of the other piece (a view-free reading)."""
        return max(iou_height_fit(masks[a]["back"], masks[b][w]) for w in views)
    lines = ["Nightfall trees and rocks: silhouette overlap against every other map's trees and rocks",
             "IoU = intersection over union of black masks fitted to the same height (aspect kept), centred, best of a few shifts and of mirroring the second mask,",
             "orthographic views: 'back' (camera at +Z) and 'right' (camera at +X). SAME-VIEW = the best of the two same-view pairs (the method of Dawnspire's note);",
             "ANY-VIEW = the best of all four view pairs (stricter: a long rock's end view against a boulder's side view).",
             "SAME KIND = trees and bamboo against trees, rocks against rocks (the comparison that matters); ALL KINDS = against every other map's piece of any kind.", ""]
    res_kind, res_all = {}, {}
    for a in mine:
        rk, ra = [], []
        for b in others:
            same, anyv = pair(a, b)
            ra.append((same, anyv, b))
            if kind[b] == kind[a]:
                rk.append((same, anyv, b))
        rk.sort(reverse=True)
        ra.sort(reverse=True)
        res_kind[a], res_all[a] = rk, ra
    # the reference: how alike the OTHER maps' pieces already are to each other (different maps, same kind)
    ref = {"tree": (0.0, None), "rock": (0.0, None)}
    ref_all = []
    labels = {k: meta[k][0] for k in others}
    for i, a in enumerate(others):
        for b in others[i + 1:]:
            if labels[a] == labels[b] or kind[a] != kind[b]:
                continue
            if labels[a].startswith("Jade") and labels[b].startswith("Jade"):
                continue
            v = max(iou_height_fit(masks[a][w], masks[b][w]) for w in views)
            ref_all.append((v, a, b))
            if v > ref[kind[a]][0]:
                ref[kind[a]] = (v, (a, b))
    ref_all.sort(reverse=True)
    lines.append("reference (the other maps against each other, same kind, different maps; same-view IoU): highest tree pair %.3f %s, highest rock pair %.3f %s" % (
        ref["tree"][0], ref["tree"][1], ref["rock"][0], ref["rock"][1]))
    for kd in ("tree", "rock"):
        vals = sorted([v for (v, a, b) in ref_all if kind[a] == kd])
        if vals:
            lines.append("   %s pairs: %d pairs, median %.3f, 90th percentile %.3f" % (kd, len(vals), vals[len(vals) // 2], vals[int(len(vals) * 0.9)]))
    own = {}
    for i, a in enumerate(mine):
        for b in mine[i + 1:]:
            own[(a, b)] = max(iou_height_fit(masks[a][v], masks[b][v]) for v in views)
    lines.append("")
    summary = {}
    for a in mine:
        lines.append("%s  (%s)" % (a.replace("Nightfall@", ""), kind[a]))
        for same, anyv, b in res_kind[a][:3]:
            lines.append("    same kind %.3f / %.3f   %s" % (same, anyv, b))
        for same, anyv, b in res_all[a][:1]:
            lines.append("    all kinds %.3f / %.3f   %s" % (same, anyv, b))
        s0 = res_kind[a][0]
        prof = sorted(((profile(a, b), b) for b in others if kind[b] == kind[a]), reverse=True)[0]
        lines.append("    back view against either view of any other %s: %.3f   %s" % (kind[a], prof[0], prof[1]))
        summary[a] = (s0[0], s0[2], max(r[1] for r in res_kind[a]), res_all[a][0][0], res_all[a][0][2], prof[0], prof[1])
    lines += ["", "summary (highest SAME-KIND same-view IoU against any other map, the piece it is, the highest any-view IoU of the same kind, then the highest of any kind):"]
    for a in mine:
        s_ = summary[a]
        lines.append("  %-26s %.3f  %-42s any-view %.3f   all kinds %.3f %s   profile %.3f %s" % (a.replace("Nightfall@", ""), s_[0], s_[1], s_[2], s_[3], s_[4], s_[5], s_[6]))
    worst = max(summary.values(), key=lambda s_: s_[0])
    lines += ["", "highest of all (same kind, same view): %.3f (%s)" % (worst[0], worst[1]), "", "between two Nightfall pieces (same-view IoU, the pairs above 0.60, trees against trees and rocks against rocks only):"]
    for (a, b), v in sorted(own.items(), key=lambda kv: -kv[1]):
        if v > 0.60 and kind[a] == kind[b]:
            lines.append("  %.3f  %s | %s" % (v, a.replace("Nightfall@", ""), b.replace("Nightfall@", "")))
    with open(os.path.join(RENDERS, "uniqueness.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(RENDERS, "uniqueness.json"), "w") as fh:
        json.dump({"summary": {k: {"iou": v[0], "closest": v[1], "any_view": v[2], "all_kinds": v[3], "all_kinds_closest": v[4], "profile": v[5], "profile_closest": v[6]} for k, v in summary.items()},
                   "reference": {k: [ref[k][0], list(ref[k][1]) if ref[k][1] else None] for k in ref},
                   "closest": {a: [(r[0], r[1], r[2]) for r in res_kind[a][:6]] for a in mine}}, fh, indent=1)
    print("\n".join(lines[6:9]))
    print("\n".join(l for l in lines if l.startswith("  ") and "profile" in l))
    return summary


def sheet():
    """The uniqueness sheet (plain Python + headless Chrome): black front silhouettes of every Nightfall tree and rock beside every other map's."""
    import base64
    import glob
    import subprocess
    import tempfile
    files = sorted(glob.glob(os.path.join(UNIQ, "*__front.png")))
    groups = {}
    for f in files:
        name = os.path.basename(f)[:-len("__front.png")]
        label, _, asset = name.partition("@")
        dims = open(f.replace("__front.png", ".txt")).read().split()
        groups.setdefault(label, []).append((asset, f, dims))
    order = ["Nightfall", "Windrift", "Jade Grove (new)", "Dawnspire", "Jade (old, replaced)", "Blossom Sanctuary", "Ember Peak", "Moonlit Isle", "Origin Abyss"]
    summ = {}
    jp = os.path.join(RENDERS, "uniqueness.json")
    if os.path.exists(jp):
        summ = json.load(open(jp))["summary"]
    cell, gap = SIZE + 10, 6
    cols = 10
    parts = []
    y = 70
    Wd = cols * (cell + gap) + 40

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;")
    for label in order:
        items = groups.get(label, [])
        if not items:
            continue
        for kind, title in (("tree", "trees and bamboo"), ("rock", "rocks and stones")):
            lst = [it for it in items if it[2][3] == kind]
            if not lst:
                continue
            parts.append('<text x="20" y="%d" font-size="15" font-weight="800" fill="#222">%s: %s</text>' % (y, esc(label.upper()), title))
            y += 8
            for k, (asset, f, dims) in enumerate(lst):
                r, c = divmod(k, cols)
                x, yy = 20 + c * (cell + gap), y + r * (cell + 34 + gap)
                data = base64.b64encode(open(f, "rb").read()).decode()
                parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#999"/>' % (x, yy, cell, cell + 30))
                parts.append('<image x="%d" y="%d" width="%d" height="%d" href="data:image/png;base64,%s"/>' % (x + 5, yy + 2, SIZE, SIZE, data))
                short = asset.replace("JG_", "").replace("EP_", "").replace("BS_", "").replace("MI_", "").replace("OA_", "")
                parts.append('<text x="%d" y="%d" font-size="9.5" fill="#111">%s  %sx%s</text>' % (x + 4, yy + SIZE + 12, esc(short), dims[0], dims[1]))
                key = "Nightfall@" + asset
                if label == "Nightfall" and key in summ:
                    s = summ[key]
                    parts.append('<text x="%d" y="%d" font-size="8.5" fill="#a02020">max IoU %.2f</text>' % (x + 4, yy + SIZE + 24, s["iou"]))
                    parts.append('<text x="%d" y="%d" font-size="7.5" fill="#a02020">%s</text>' % (x + 4, yy + SIZE + 33, esc(s["closest"].split("@")[1][:26])))
            rows = (len(lst) + cols - 1) // cols
            y += rows * (cell + 34 + gap) + 26
    H = y + 20
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica Neue, Arial, sans-serif"><rect width="%d" height="%d" fill="#f3f1ea"/>'
           '<text x="20" y="34" font-size="17" font-weight="800" fill="#111">UNIQUENESS SHEET: Nightfall Citadel\'s trees and rocks beside every other map\'s (Windrift\'s too). Black side silhouettes, each on its own scale, width x height in studs; red = highest overlap</text>%s</svg>'
           % (Wd, H, Wd, H, Wd, H, "".join(parts)))
    work = tempfile.mkdtemp()
    sp = os.path.join(work, "sheet.svg")
    with open(sp, "w", encoding="utf8") as f:
        f.write(svg)
    outp = os.path.join(RENDERS, "uniqueness_sheet.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--user-data-dir=" + os.path.join(work, "profile"),
                    "--window-size=%d,%d" % (Wd, H), "--force-device-scale-factor=1", "--screenshot=" + outp, "file://" + sp], check=True, capture_output=True, timeout=240)
    print("wrote", outp, "(%d x %d)" % (Wd, H))


# ---------------------------------------------------------------------------------------------------------------------------------
# QA, export, verification
# ---------------------------------------------------------------------------------------------------------------------------------
ACCEPT = (
    ("UV overlap", "no texture is ever applied: the UV set exists so the mesh imports (box-projected charts that overlap by design)"),
    ("open boundary", "flat ground patches, path slabs' hidden undersides and the one-sided closing faces of blades sunk into ground or limbs"),
    ("non-manifold", "solids that meet along an edge or a corner (a blade or a root leaving a limb, a stone on a stone)"),
    ("duplicate verts", "the corners of two solids that touch share a position"),
    ("hidden back-to-back", "faces of two solids resting on each other (a few per stack)"),
    ("fully enclosed", "a blade base, a root end or a vein sunk inside the mass it grows from, on purpose"),
    ("lowest point", "the pieces' feet are buried below y = 0 on purpose (they stand in the ground)"),
)


def accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def run_qa(write=True):
    data = build(NAMES or None)
    coll = new_scene()
    qa = B.qa_module()
    lines = ["Nightfall vegetation: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece", ""]
    all_pass = True
    n_err = 0
    for name in sorted(data["pieces"]):
        objs = piece_objs(name, data["pieces"][name], coll)
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
        t = {o.name: B.tris(o) for o in objs}
        all_pass &= r["pass"]
        n_err += len(r["errors"])
        lines.append("%s: %s, %d triangles, %d errors" % (name, "PASS" if r["pass"] else "FAIL", sum(t.values()), len(r["errors"])))
        for k, v in sorted(t.items()):
            lines.append("    %-50s %6d" % (k, v))
        for e in r["errors"]:
            lines.append("    ERROR %s" % e)
        seen = set()
        for w in r["warnings"]:
            why = accepted(w)
            if why:
                if why not in seen:
                    lines.append("    accepted warning(s): %s" % why)
                    seen.add(why)
            else:
                lines.append("    WARNING %s" % w)
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    lines.insert(1, "Overall: %s (%d errors in %d pieces)" % ("PASS" if all_pass else "FAIL", n_err, len(data["pieces"])))
    if write and not NAMES:
        with open(os.path.join(RENDERS, "qa.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if l.endswith("errors") or l.startswith("Overall") or "ERROR" in l or "WARNING" in l))
    return all_pass


def verify_fbx(path, expect):
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if ANCHOR not in got:
        problems.append("no " + ANCHOR)
    for name, (tr, lo, hi) in expect.items():
        o = got.get(name)
        if o is None:
            problems.append("missing " + name)
            continue
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
        l2, h2 = B.bbox_roblox([o])
        if t != tr:
            problems.append("%s tris %d != %d" % (name, t, tr))
        if max(abs(a - b) for a, b in zip(lo + hi, l2 + h2)) > 0.02:
            problems.append("%s box %s %s != %s %s" % (name, l2, h2, lo, hi))
    extra = sorted(set(got) - set(expect) - {ANCHOR})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems


FRAME = ("each piece at its own origin, y = 0 the ground it stands on (feet sink below), front is -Z, Roblox studs; every piece stands UPRIGHT on a vertical axis "
         "(nothing leans to a wind: place at any yaw); anchor cube NF_Anchor (1 stud) at the origin; Roblox material and colour per material suffix in `looks`; "
         "collision boxes are invisible Plastic colliders in the piece frame (none for crowns, plants, ground patches and walkable path pieces)")


def write_contract(files):
    data = build(None)
    os.makedirs(OUT, exist_ok=True)
    pieces = {}
    for n, m in data["meta"].items():
        d = dict(m)
        d["fbx"] = FILES[m["family"]]
        d["objects"] = ["%s__%s" % (n, s) for s in m["materials"]]
        pieces[n] = d
    with open(os.path.join(OUT, "veg_pieces.json"), "w") as f:
        json.dump({"frame": FRAME, "looks": data["looks"], "files": files, "pieces": pieces}, f, indent=1)
    return data


def contract():
    """The EARLY contract: veg_pieces.json from the pieces alone (no Blender, no FBX yet), so the placer can plan counts and keep-outs."""
    data = build(None)
    files = {}
    for fam, fname in FILES.items():
        ms = [m for m in data["meta"].values() if m["family"] == fam]
        files[fam] = {"fbx": os.path.relpath(os.path.join(OUT, fname), REPO), "objects": sum(len(m["materials"]) for m in ms), "tris": sum(m["tris"] for m in ms),
                      "verify": "pending: the FBX is not exported yet, this JSON is the early contract (names, triangles, bounds and colliders may move by a few hundredths)"}
    write_contract(files)
    tot = sum(m["tris"] for m in data["meta"].values())
    print("contract written:", len(data["meta"]), "pieces,", tot, "triangles in one of each")


def export():
    if not run_qa():
        raise SystemExit("QA failed: nothing exported")
    data = build(None)
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for fam, fname in FILES.items():
        coll = new_scene()
        objs_all, expect = [], {}
        for n, piece in sorted(data["pieces"].items()):
            if "_%s_" % fam not in n:
                continue
            objs = piece_objs(n, piece, coll)
            for o in objs:
                lo, hi = B.bbox_roblox([o])
                expect[o.name] = (B.tris(o), lo, hi)
            objs_all += objs
        path = os.path.join(OUT, fname)
        W.export_batch(objs_all, path, image=None, anchor_name=ANCHOR)
        B.scrub(path)
        problems = verify_fbx(path, expect)
        report[fam] = {"fbx": os.path.relpath(path, REPO), "objects": len(expect), "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok"}
        print("EXPORTED", path, len(expect), "objects", "verify:", problems or "ok")
    write_contract(report)
    print("EXPORT_DONE")


def verify():
    data = build(None)
    pieces, meta = data["pieces"], data["meta"]
    L = ["Nightfall vegetation: numeric checks (Roblox studs, y = 0 the ground, every piece upright)", ""]
    bad = []

    def chk(name, ok, detail=""):
        L.append("%-96s %s %s" % (name, "ok" if ok else "FAIL", detail))
        if not ok:
            bad.append(name)
    short = lambda n: n.replace("Nightfall_", "")
    # 1. budgets
    L.append("1. Budgets per piece (trees 400-2,400 and the giant up to 6,000; rocks 70-900; path pieces 150-700; plants 60-450; at most 2 material suffixes, the giant 3;")
    L.append("   largest single mesh 3,000; nothing under y = -1.5)")
    for n, m in sorted(meta.items()):
        base, fam = m["piece"], m["family"]
        walk = m["walkable"]
        if fam == "Trees":
            lim = (1500, 6000) if base == "GiantBlackthorn" else (150, 2400)
        elif fam == "Plants":
            lim = (60, 450)
        else:
            lim = (150, 700) if walk else (70, 900)
        nm = len(m["materials"])
        max_mat = 3 if base == "GiantBlackthorn" else 2
        chk("   %-30s %5d tris (range %d-%d), %d materials (max %d)" % (short(n), m["tris"], lim[0], lim[1], nm, max_mat), lim[0] <= m["tris"] <= lim[1] and nm <= max_mat)
        mx = max(m["materials"].values())
        chk("   %-30s largest mesh %d (max 3,000)" % (short(n), mx), mx <= 3000)
        chk("   %-30s lowest point %.2f (not under -1.5)" % (short(n), m["bounds_min"][1]), m["bounds_min"][1] > -1.5)
    L.append("")
    # 2. the planned mix
    L.append("2. The planned mix (16 trees with the one giant, 24 rocks and path pieces, 60 plants): counts, triangles, MeshParts (one per material per placed piece)")
    tot = {"Trees": [0, 0, 0], "Rocks": [0, 0, 0], "Plants": [0, 0, 0]}
    rows = []
    for n, m in sorted(meta.items(), key=lambda kv: (["Trees", "Rocks", "Plants"].index(kv[1]["family"]), kv[0])):
        k = m["plan_count"]
        parts = len(m["materials"])
        rows.append("   %-8s %-18s %5d tris  %d materials  place %2d  = %6d tris, %3d parts" % (m["family"], m["piece"], m["tris"], parts, k, k * m["tris"], k * parts))
        t = tot[m["family"]]
        t[0] += k
        t[1] += k * m["tris"]
        t[2] += k * parts
    L += rows
    gt = [sum(t[i] for t in tot.values()) for i in range(3)]
    for fam, t in tot.items():
        L.append("   %-8s %2d pieces placed, %6d triangles, %3d MeshParts" % (fam, t[0], t[1], t[2]))
    L.append("   TOTAL    %2d pieces placed, %6d triangles, %3d MeshParts" % (gt[0], gt[1], gt[2]))
    chk("   16 trees (one of them the giant), 24 rocks and path pieces, 60 plants", tot["Trees"][0] == 16 and tot["Rocks"][0] == 24 and tot["Plants"][0] == 60, "%d / %d / %d" % (tot["Trees"][0], tot["Rocks"][0], tot["Plants"][0]))
    chk("   at most 45,000 triangles as placed", gt[1] <= 45000, str(gt[1]))
    chk("   at most 160 MeshParts", gt[2] <= 160, str(gt[2]))
    chk("   one giant only", meta["Nightfall_Trees_GiantBlackthorn"]["plan_count"] == 1)
    chk("   at least 5 tree designs in 3 families (plus the giant)", len([n for n in meta if "_Trees_" in n]) - 1 >= 5 and len({m["piece"][:-2] for n, m in meta.items() if m["family"] == "Trees" and m["variant"]}) >= 3)
    chk("   at least 5 rocks (columns and shards among them), 8 plants", len([m for m in meta.values() if m["family"] == "Rocks" and not m["walkable"]]) >= 5 and len([m for m in meta.values() if m["family"] == "Plants"]) >= 8)
    L.append("")
    # 3. bases, paths and the upright rule
    L.append("3. Bases, paths and the upright rule")
    for n in sorted(pieces):
        m = meta[n]
        if m["family"] != "Trees":
            continue
        lo_y = min(p[1] for g in pieces[n].g.values() for p in g.v)
        chk("   %-30s feet sunk under the ground: lowest point %.2f (0.2 to 1.2 under)" % (short(n), lo_y), -1.2 <= lo_y <= -0.2)
    for n in ("Nightfall_Rocks_HexStepsA", "Nightfall_Rocks_HexStepsB"):
        g = pieces[n].g["Basalt"]
        tops = [p[1] for p in g.v if p[1] > 0.0]
        chk("   %-30s every walking top within 0.05 of one level: %.3f to %.3f (y 0 to 0.25)" % (short(n), min(tops), max(tops)), max(tops) - min(tops) <= 0.05 and 0.0 <= min(tops) and max(tops) <= 0.25)
    tops = [p[1] for p in pieces["Nightfall_Rocks_BasaltPave"].g["Basalt"].v if p[1] > 0.0]
    chk("   %-30s every paver top within 0.05 of one level: %.3f to %.3f" % ("Rocks_BasaltPave", min(tops), max(tops)), max(tops) - min(tops) <= 0.05 and max(tops) <= 0.25)
    eg = [p[1] for p in pieces["Nightfall_Rocks_BasaltPave"].g["Ember"].v]
    chk("   %-30s the ember grout lies under the paver tops (its top %.2f, the pavers' lowest top %.3f)" % ("Rocks_BasaltPave", max(eg), min(tops)), max(eg) < min(tops) - 0.05)
    for n in sorted(pieces):
        if meta[n]["family"] == "Rocks" and meta[n]["walkable"]:
            chk("   %-30s no collision boxes (the walkable mesh itself carries the foot)" % short(n), not meta[n]["collision"])
    L.append("   upright: the horizontal middle of everything above 40 percent of the piece's height lies within 18 percent of that height (plus 1.5 studs) of its foot's middle")
    for n in sorted(pieces):
        m = meta[n]
        if m["family"] == "Plants" and m["piece"] in ("EmberCrust", "AshDrift"):
            continue
        if m["walkable"]:
            continue
        vs = [v for g in pieces[n].g.values() for v in g.v]
        H = m["height"]
        up = [v for v in vs if v[1] > 0.4 * H]
        low = [v for v in vs if v[1] < 0.2 * H + 0.3]
        if not up or not low:
            continue
        ux, uz = sum(v[0] for v in up) / len(up), sum(v[2] for v in up) / len(up)
        lx, lz = sum(v[0] for v in low) / len(low), sum(v[2] for v in low) / len(low)
        off = math.hypot(ux - lx, uz - lz)
        chk("   %-30s upper mass %.2f from the foot's middle (limit %.2f)" % (short(n), off, 0.18 * H + 1.5), off <= 0.18 * H + 1.5)
    L.append("")
    # 4. colliders
    L.append("4. Colliders (invisible boxes in the piece frame)")
    for n in sorted(pieces):
        m = meta[n]
        boxes = m["collision"]
        lo, hi = m["bounds_min"], m["bounds_max"]
        within = all(b["x0"] >= lo[0] - 0.05 and b["x1"] <= hi[0] + 0.05 and b["z0"] >= lo[2] - 0.05 and b["z1"] <= hi[2] + 0.05 and b["y0"] >= -0.01 and b["y1"] <= hi[1] + 0.05 for b in boxes)
        need = m["family"] == "Trees" or m["piece"] == "Thornbrake" or (m["family"] == "Rocks" and not m["walkable"] and not m["piece"].startswith("ShardScatter"))
        chk("   %-30s %2d boxes (%s), inside the bounds" % (short(n), len(boxes), "needed" if need else "none wanted"), within and (bool(boxes) == need))
    g_boxes = meta["Nightfall_Trees_GiantBlackthorn"]["collision"]
    chk("   Trees_GiantBlackthorn: no collider over y 24 (the crown is decoration)", max(b["y1"] for b in g_boxes) <= 24.5, "%d boxes" % len(g_boxes))
    for n in ("Nightfall_Trees_CinderstumpD1",):
        bx = meta[n]["collision"]
        chk("   Trees_CinderstumpD1: the staves are boxed, the hollow centre (radius 1) is free of every box", not any(b["x0"] < 1.0 and b["x1"] > -1.0 and b["z0"] < 1.0 and b["z1"] > -1.0 for b in bx), "%d boxes" % len(bx))
    L.append("")
    # 5. the exported files
    L.append("5. The exported files (re-imported)")
    for fam, fname in FILES.items():
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            chk("   %s exists" % fname, False)
            continue
        expect = {}
        coll = new_scene()
        for n, piece in sorted(pieces.items()):
            if "_%s_" % fam in n:
                for o in piece_objs(n, piece, coll):
                    lo, hi = B.bbox_roblox([o])
                    expect[o.name] = (B.tris(o), lo, hi)
        problems = verify_fbx(path, expect)
        chk("   %s re-imports with %d objects, the same triangles and boxes, and its %s" % (fname, len(expect), ANCHOR), not problems, str(problems[:3]))
        raw = open(path, "rb").read()
        home = os.path.expanduser("~").encode()
        chk("   %s holds neither this machine's home path nor its user name" % fname, home not in raw and os.path.basename(home) not in raw and b"/Users/" not in raw, "size %d bytes" % len(raw))
    jp = os.path.join(OUT, "veg_pieces.json")
    raw = open(jp, "rb").read()
    chk("   veg_pieces.json holds no machine path", os.path.expanduser("~").encode() not in raw and b"/Users/" not in raw)
    chk("   veg_pieces.json lists every piece and every FBX as verified ok", len(json.load(open(jp))["pieces"]) == len(pieces) and all(v["verify"] == "ok" for v in json.load(open(jp))["files"].values()))
    L.append("")
    L.append("6. Uniqueness (from uniqueness.json, the silhouette stage)")
    ju = os.path.join(RENDERS, "uniqueness.json")
    if os.path.exists(ju):
        u = json.load(open(ju))
        worst_t = max((v["iou"] for k, v in u["summary"].items() if k.startswith("Nightfall@Trees")), default=0)
        worst_r = max((v["iou"] for k, v in u["summary"].items() if k.startswith("Nightfall@Rocks")), default=0)
        L.append("   trees: highest same-kind IoU against any other map %.3f (reference: the other maps against each other, highest tree pair %.3f)" % (worst_t, u["reference"]["tree"][0]))
        L.append("   rocks: highest same-kind IoU against any other map %.3f (reference: the other maps against each other, highest rock pair %.3f)" % (worst_r, u["reference"]["rock"][0]))
    else:
        L.append("   (run the silhouette stage first)")
    L.append("")
    L.append("RESULT: %s" % ("ALL OK" if not bad else "FAILED: " + "; ".join(bad)))
    with open(os.path.join(RENDERS, "verify.txt"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(l for l in L if "FAIL" in l or l.startswith("RESULT") or l.startswith("   TOTAL") or l.startswith("   Trees ") or l.startswith("   Rocks ") or l.startswith("   Plants ")))


def main():
    {"contract": contract, "look": look, "overview": overview, "sheets": sheets, "silhouette": silhouette, "qa": run_qa, "export": export, "verify": verify, "sheet": sheet}[STAGE]()


if __name__ == "__main__":
    main()

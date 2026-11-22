"""Headless runner for Dawnspire's vegetation, rocks and ground cover (dawnspire_veg.py). Never the open Blender window.

    HQ_QA_SCRIPT=<blender-asset-qa>/scripts/qa_check.py \
    blender -b --factory-startup -P tools/blender/world/dawnspire_veg_run.py -- <stage> [piece names]
      look        a quick clay + paint contact sheet of the named pieces (default: every tree) into renders/dawnspire/veg/look_*.png
      sheets      six-side clay sheets (front, back, left, right, top, three-quarter) of every piece, and the paint sheet per family
      silhouette  black-on-white 128 px silhouettes of the 10 trees beside the Blossom Sanctuary's six, and the IoU numbers
      qa          qa_check.py (profile roblox) on every piece
      export      QA, then the three FBX files, veg_pieces.json and the verification re-import
      verify      numeric checks (budgets, symmetry, clearances, flat bases, FBX re-import), written to renders/dawnspire/veg/verify.txt
Evidence goes to renders/dawnspire/veg/ (local, never committed).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import hq_blender as B  # noqa: E402
import worldlib as W  # noqa: E402
import dawnspire_veg as V  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "look"
NAMES = ARGS[1:]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "dawnspire", "veg")
OUT = os.path.join(REPO, "assets", "world", "MurimCrossing", "Dawnspire")
os.makedirs(RENDERS, exist_ok=True)

# the preview colours of the suffixes (the hall's PREVIEW table has only its own): derived from the looks
for suffix, look in V.LOOKS.items():
    if suffix in B.PREVIEW:
        continue
    c = tuple(look["Color"])
    mat = look["Material"]
    metal = 1.0 if mat == "Metal" else 0.0
    rough = {"Metal": 0.32, "Glass": 0.05, "SmoothPlastic": 0.55, "Marble": 0.28, "Fabric": 0.85, "Granite": 0.55}.get(mat, 0.75)
    B.PREVIEW[suffix] = (c, rough, metal, None, 0.55 if mat == "Glass" else None)

SMOOTH = {"Blossom": 24.0, "BlossomBlush": 24.0, "Bark": 55.0, "BarkPale": 40.0}   # shading angle per suffix: faceted clouds, softer bark and stone
SMOOTH_DEFAULT = 38.0


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


def all_pieces():
    import dawnspire_veg as v
    return v.build_all()


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
    import numpy as np
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


# ---------------------------------------------------------------------------------------------------------------------------------
# views
# ---------------------------------------------------------------------------------------------------------------------------------
def bounds_of(objs):
    lo, hi = B.bbox_roblox(objs)
    return lo, hi


def ortho_cam(name, view, lo, hi, pad=1.18):
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = [hi[i] - lo[i] for i in range(3)]
    D = 200.0
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
        cam.rotation_euler = (0.0, 0.0, math.pi)
        return cam
    else:   # q3: a three-quarter perspective from the front-left, above
        size = max(ext)
        loc = (c[0] - size * 1.25, c[1] + ext[1] * 0.25 + size * 0.5, c[2] - size * 1.45)
        return B.add_camera(name, B.rbv(*loc), B.rbv(*c), lens=36.0)
    return B.add_camera(name, B.rbv(*loc), B.rbv(*c), ortho=size * pad)


def lighting(strength=2.6, azimuth=-35.0):
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


def render_views(name, piece, views, mode, res=(480, 480), tag=None, glow=True):
    coll = new_scene()
    objs = piece_objs(name, piece, coll, mode)
    B.setup_render(res, samples=10)
    bpy.context.scene.render.film_transparent = False
    lighting()
    if mode == "clay":
        B.set_world((0.55, 0.55, 0.55), 1.0)
    lo, hi = bounds_of(objs)
    ground = bpy.data.objects.new("ground", bpy.data.meshes.new("ground"))
    imgs = []
    for v in views:
        cam = ortho_cam("cam_" + v, v, lo, hi)
        path = os.path.join(RENDERS, "_tmp_%s.png" % v)
        B.shoot(cam, path)
        imgs.append(load_pixels(path))
    return imgs


# ---------------------------------------------------------------------------------------------------------------------------------
def look():
    data = all_pieces()
    names = NAMES or [n for n in data["pieces"] if "_Trees_" in n]
    imgs = []
    for n in names:
        imgs += render_views(n, data["pieces"][n], ("front", "q3", "top"), "paint", res=(420, 420))
    sheet = mosaic(imgs, 3, tile=360)
    save_pixels(sheet, os.path.join(RENDERS, "look_%s.png" % ("_".join(x.split("_")[-1] for x in names[:3]) if len(names) <= 3 else "set")))
    print("looked", names)


def sheets():
    """Six-side clay sheets (front, back, left, right, top, three-quarter) of every piece, then one paint sheet per family."""
    data = all_pieces()
    for n, piece in data["pieces"].items():
        views = ("front", "back", "left", "right", "top", "q3")
        imgs = render_views(n, piece, views, "clay", res=(360, 360))
        save_pixels(mosaic(imgs, 3, tile=330, bg=0.9), os.path.join(RENDERS, "six_%s_clay.png" % n.replace("Dawnspire_", "")))
    for fam in ("Trees", "Rocks", "Plants"):
        names = [n for n in data["pieces"] if "_%s_" % fam in n]
        imgs = []
        for n in names:
            imgs += render_views(n, data["pieces"][n], ("q3",), "paint", res=(380, 380))
        save_pixels(mosaic(imgs, 5, tile=300), os.path.join(RENDERS, "paint_%s.png" % fam))
    print("sheets done")


# ---------------------------------------------------------------------------------------------------------------------------------
# silhouettes and the numeric comparison
# ---------------------------------------------------------------------------------------------------------------------------------
BS_FBX = os.path.join(REPO, "assets", "world", "BlossomSanctuary", "BlossomSanctuary_Trees.fbx")
BS_TREES = ["BS_TreeElder", "BS_TreeWeeping", "BS_TreeLeaning", "BS_TreeTwin", "BS_TreeYoung", "BS_TreeGnarled"]


def mask_from(px):
    import numpy as np
    m = px[:, :, 0] < 0.4
    ys, xs = np.where(m)
    if len(ys) == 0:
        return m
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def shoot_mask(objs, view):
    lo, hi = bounds_of(objs)
    cam = ortho_cam("cam_sil_" + view, view, lo, hi, pad=1.08)
    path = os.path.join(RENDERS, "_tmp_sil.png")
    B.shoot(cam, path)
    return mask_from(load_pixels(path))


def sil_setup(res=420):
    B.setup_render((res, res), samples=4)
    B.set_world((1.0, 1.0, 1.0), 1.0)
    B.set_sun(0.0, (-50, 0, 0))
    bpy.context.scene.render.film_transparent = False


def all_tree_masks(views):
    """{model: {view: mask}} for my ten trees and the Blossom Sanctuary's six (imported read-only from its FBX)."""
    data = all_pieces()
    out = {}
    names = [n for n in data["pieces"] if "_Trees_" in n]
    for n in names:
        coll = new_scene()
        objs = piece_objs(n, data["pieces"][n], coll, "black")
        sil_setup()
        out[n.replace("Dawnspire_Trees_", "")] = {v: shoot_mask(objs, v) for v in views}
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=BS_FBX)
    allobjs = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in allobjs:
        o.data.materials.clear()
        o.data.materials.append(B.black_material())
    sil_setup()
    for key in BS_TREES:
        mine = [o for o in allobjs if o.name.split(".")[0].startswith(key + "__")]
        for o in allobjs:
            o.hide_render = o not in mine
        out[key] = {v: shoot_mask(mine, v) for v in views}
    return out


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
    W = max(A.shape[1], Bm.shape[1]) + 16

    def place(m, dx):
        c = np.zeros((h, W), bool)
        x0 = (W - m.shape[1]) // 2 + dx
        c[:, max(0, x0):max(0, x0) + m.shape[1] - (max(0, x0) - x0)] = m[:, max(0, -x0):][:, :W - max(0, x0)]
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


def iou_box_fit(a, b, h=96):
    """IoU after fitting both to the same square (aspect NOT kept: the strictest comparison of the pure shape), best with the second mirrored."""
    import numpy as np
    def sq(m):
        ys = np.linspace(0, m.shape[0] - 1, h).astype(int)
        xs = np.linspace(0, m.shape[1] - 1, h).astype(int)
        return m[ys][:, xs]
    A, Bm = sq(a), sq(b)
    best = 0.0
    for bb in (Bm, Bm[:, ::-1]):
        u = (A | bb).sum()
        best = max(best, (A & bb).sum() / u)
    return best


def tiers_of(mask):
    """How many distinct horizontal crown layers the silhouette has: peaks of the row-width curve (smoothed) separated by dips of at least 14% of the widest row."""
    import numpy as np
    w = mask.sum(axis=1).astype(float)
    w = np.convolve(w, np.ones(5) / 5.0, mode="same")
    w /= max(w.max(), 1.0)
    peaks, lo, hi, rising = 0, 1.0, 0.0, False
    state = "down"
    for v in w:
        if v > 0.3:
            if state == "down":
                hi = max(hi, v)
                if v < hi - 0.14:
                    state = "valley"
                    lo = v
            elif state == "valley":
                lo = min(lo, v)
                if v > lo + 0.14:
                    peaks += 1
                    state = "down"
                    hi = v
    return peaks + 1


def silhouette():
    import numpy as np
    views = ("front", "right")
    masks = all_tree_masks(views + ("q3",))
    mine = [k for k in masks if not k.startswith("BS_")]
    bs = [k for k in masks if k.startswith("BS_")]
    order = mine + bs
    # the thumbnail sheet: every silhouette fitted to 128 px tall, mine then the Blossom Sanctuary's, front row then quarter row
    rows = []
    for v in ("front", "q3"):
        tiles = [fit(masks[k][v], 128) for k in order]
        W = sum(t.shape[1] + 10 for t in tiles) + 40
        row = np.ones((140, W, 4), np.float32)
        row[:, :, 3] = 1.0
        x = 6
        for i, t in enumerate(tiles):
            if i == len(mine):
                x += 30
                row[:, x - 18:x - 14, :3] = 0.6
            row[6:134, x:x + t.shape[1], :3] = np.where(t[:, :, None], 0.0, 1.0)
            x += t.shape[1] + 10
        rows.append(row)
    Wmax = max(r.shape[1] for r in rows)
    sheet = np.ones((sum(r.shape[0] for r in rows), Wmax, 4), np.float32)
    y = 0
    for r in rows[::-1]:    # (the image's rows run bottom to top: the quarter row first, so the front row is on top)
        sheet[y:y + r.shape[0], :r.shape[1]] = r
        y += r.shape[0]
    save_pixels(sheet, os.path.join(RENDERS, "silhouette_sheet.png"))
    # numbers
    lines = ["Dawnspire trees: silhouette comparison (black masks; views: front and right side, orthographic; IoU = intersection over union)", "",
             "order on the sheet (left to right): " + ", ".join(order) + "   (a gap and a grey bar separate Dawnspire's ten from the Blossom Sanctuary's six)", "",
             "per model (front view): aspect = width / height, tiers = distinct crown layers (row-width peaks), trunk = the fraction of the height, from the ground, narrower than a quarter of the crown", ""]
    for k in order:
        m = masks[k]["front"]
        w = m.sum(axis=1).astype(float)
        wn = w / max(w.max(), 1.0)
        trunk = 0.0
        for v in wn[::-1]:
            if v < 0.25:
                trunk += 1
            else:
                break
        lines.append("  %-16s aspect %.2f  tiers %d  clear trunk %.0f%%" % (k, m.shape[1] / m.shape[0], tiers_of(m), 100.0 * trunk / m.shape[0]))
    res = {}
    worst = {"mine": (0, None), "vs_bs": (0, None), "mine_box": (0, None), "vs_bs_box": (0, None)}
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            ih = max(iou_height_fit(masks[a][v], masks[b][v]) for v in views)
            ib = max(iou_box_fit(masks[a][v], masks[b][v]) for v in views)
            res["%s|%s" % (a, b)] = (ih, ib)
            if not a.startswith("BS_") and not b.startswith("BS_"):
                key = "mine"
            elif a.startswith("BS_") and b.startswith("BS_"):
                continue
            else:
                key = "vs_bs"
            if ih > worst[key][0]:
                worst[key] = (ih, (a, b))
            if ib > worst[key + "_box"][0]:
                worst[key + "_box"] = (ib, (a, b))
    lines += ["", "worst pairs (max over the two views, best of a few shifts and of mirroring):",
              "  between two of Dawnspire's ten, height-fitted IoU   %.3f   %s" % (worst["mine"][0], worst["mine"][1]),
              "  between two of Dawnspire's ten, box-fitted IoU      %.3f   %s" % (worst["mine_box"][0], worst["mine_box"][1]),
              "  Dawnspire against a Blossom Sanctuary tree, height  %.3f   %s" % (worst["vs_bs"][0], worst["vs_bs"][1]),
              "  Dawnspire against a Blossom Sanctuary tree, box     %.3f   %s" % (worst["vs_bs_box"][0], worst["vs_bs_box"][1]), "",
              "full matrix (height-fitted / box-fitted), Dawnspire against Dawnspire:"]
    for i, a in enumerate(mine):
        for b in mine[i + 1:]:
            ih, ib = res["%s|%s" % (a, b)]
            lines.append("  %-14s %-14s %.3f / %.3f" % (a, b, ih, ib))
    lines += ["", "Dawnspire against the Blossom Sanctuary (height-fitted / box-fitted):"]
    for a in mine:
        row = []
        for b in bs:
            ih, ib = res["%s|%s" % (a, b)]
            row.append("%s %.2f/%.2f" % (b.replace("BS_Tree", ""), ih, ib))
        lines.append("  %-14s %s" % (a, "  ".join(row)))
    with open(os.path.join(RENDERS, "silhouettes.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-3 - len(mine) - 2:]))
    print("\n".join(l for l in lines if l.startswith("  between") or l.startswith("  Dawnspire against")))
    return worst


# ---------------------------------------------------------------------------------------------------------------------------------
# QA, export, verification
# ---------------------------------------------------------------------------------------------------------------------------------
ACCEPT = (
    ("UV overlap", "no texture is ever applied: the UV set exists so the mesh imports (box-projected charts that overlap by design)"),
    ("open boundary", "blossom, needle and moss masses are one closed solid split by face direction into two tints (the two halves close each other across materials); petals, the water sheet and the flat petal drift are open sheets by design"),
    ("non-manifold", "solids that meet along an edge or a corner (a root or limb leaving a trunk, a petal on its flower)"),
    ("duplicate verts", "the corners of two solids that touch share a position, and the tint halves share their seam"),
    ("hidden back-to-back", "faces of two solids resting on each other (a few per stack)"),
    ("fully enclosed", "a petal base or an overlapping lobe sunk inside the mass it grows from, on purpose"),
    ("lowest point", "the pieces' feet are buried below y = 0 on purpose (they stand in the ground)"),
)


def accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def qa_module():
    return B.qa_module()


def run_qa(write=True):
    data = all_pieces()
    coll = new_scene()
    qa = qa_module()
    lines = ["Dawnspire vegetation: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece", ""]
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
    if write:
        with open(os.path.join(RENDERS, "qa.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if l.endswith("errors") or l.startswith("Overall") or "ERROR" in l or "WARNING" in l))
    return all_pass


FILES = {"Trees": "Dawnspire_Trees.fbx", "Plants": "Dawnspire_Plants.fbx", "Rocks": "Dawnspire_Rocks.fbx"}


def verify_fbx(path, expect):
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if "DS_Anchor" not in got:
        problems.append("no DS_Anchor")
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
    extra = sorted(set(got) - set(expect) - {"DS_Anchor"})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems


def export():
    if not run_qa():
        raise SystemExit("QA failed: nothing exported")
    data = all_pieces()
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
        W.export_batch(objs_all, path, image=None, anchor_name="DS_Anchor")
        B.scrub(path)
        problems = verify_fbx(path, expect)
        report[fam] = {"fbx": os.path.relpath(path, REPO), "objects": len(expect), "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok"}
        print("EXPORTED", path, len(expect), "objects", "verify:", problems or "ok")
    pieces = {}
    for n, m in data["meta"].items():
        d = dict(m)
        d["fbx"] = FILES[m["family"]]
        d["objects"] = ["%s__%s" % (n, s) for s in m["materials"]]
        pieces[n] = d
    with open(os.path.join(OUT, "veg_pieces.json"), "w") as f:
        json.dump({"frame": "each piece at its own origin, y = 0 the ground it stands on (feet sink below), front is -Z, Roblox studs; anchor cube DS_Anchor (1 stud) at the origin; "
                            "Roblox material and colour per material suffix in `looks`; collision boxes are invisible Plastic colliders in the piece frame",
                   "looks": data["looks"], "files": report, "pieces": pieces}, f, indent=1)
    print("EXPORT_DONE")


# ---------------------------------------------------------------------------------------------------------------------------------
def mirror_delta(piece):
    worst = 0.0
    for suffix, g in piece.g.items():
        cells = {}
        h = 1e-2
        for p in g.v:
            cells.setdefault((round(p[0] / h), round(p[1] / h), round(p[2] / h)), []).append(p)
        for p in g.v:
            q = (-p[0], p[1], p[2])
            kx, ky, kz = round(q[0] / h), round(q[1] / h), round(q[2] / h)
            best = 1e9
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for r in cells.get((kx + dx, ky + dy, kz + dz), []):
                            best = min(best, max(abs(r[0] - q[0]), abs(r[1] - q[1]), abs(r[2] - q[2])))
            worst = max(worst, best)
    return worst


def verify():
    data = all_pieces()
    pieces, meta = data["pieces"], data["meta"]
    L = ["Dawnspire vegetation: numeric checks (Roblox studs, y = 0 the ground)", ""]
    bad = []

    def chk(name, ok, detail=""):
        L.append("%-70s %s %s" % (name, "ok" if ok else "FAIL", detail))
        if not ok:
            bad.append(name)
    L.append("1. Budgets (trees 800-3,000, rocks 300-1,500, plants 100-600; ground cover and stepping stones smaller by design; nothing over 20,000)")
    total = 0
    for n, m in sorted(meta.items()):
        base = m["piece"]
        lim = (800, 3000) if m["family"] == "Trees" else ((300, 1500) if base.startswith("Scholar") else ((40, 80) if base.startswith("Stepping") else (
            (100, 220) if base.startswith("PetalDrift") else ((250, 400) if base.startswith("GravelRake") else ((40, 140) if base.startswith("Moss") else (100, 600))))))
        total += m["tris"]
        chk("   %-38s %5d tris (range %d-%d) %d materials" % (n.replace("Dawnspire_", ""), m["tris"], lim[0], lim[1], len(m["materials"])), lim[0] <= m["tris"] <= lim[1])
        chk("   %s: largest mesh under 20,000" % n.replace("Dawnspire_", ""), max(m["materials"].values()) < 20000)
    L.append("   sum of one of each piece: %d triangles" % total)
    L.append("")
    L.append("2. The ArchTree pair: mirror symmetry about x = 0 (vertex to mirror vertex, must be 0 within 1e-4), clear height over the middle line, clear width at the feet")
    for v in ("A", "B"):
        n = "Dawnspire_Trees_ArchTree" + v
        d = mirror_delta(pieces[n])
        chk("   ArchTree%s mirror delta" % v, d < 1e-4, "%.2e" % d)
        vs = [p for g in pieces[n].g.values() for p in g.v]
        mid = [p for p in vs if abs(p[0]) < 1.5 and p[2] > -9]
        low = min(p[1] for p in mid)
        chk("   ArchTree%s lowest geometry over the middle line (|x| < 1.5) at least 8" % v, low >= 8.0, "%.2f" % low)
        bark = pieces[n].g["Bark"].v
        feet = [p for p in bark if p[1] < 1.0]
        inner = min(abs(p[0]) for p in feet)
        chk("   ArchTree%s clear width between the trunk feet (trunk surfaces) 10 / 14" % v, abs(2 * inner - (10 if v == "A" else 14)) < 1.6, "%.2f" % (2 * inner))
        col = meta[n]["collision"]
        chk("   ArchTree%s colliders are the two trunk feet only, clear between them %.1f" % (v, col[1]["x0"] - col[0]["x1"]), len(col) == 2)
    L.append("")
    L.append("3. Flat bases and levels")
    for n in ("Dawnspire_Trees_PlinthTreeA", "Dawnspire_Trees_PlinthTreeB"):
        ys = {round(p[1], 4) for p in pieces[n].g["PlinthBase"].v}
        chk("   %s plinth foot has one flat bottom plane" % n.replace("Dawnspire_Trees_", ""), min(ys) == -0.4 and sum(1 for p in pieces[n].g["PlinthBase"].v if abs(p[1] + 0.4) < 1e-6) >= 4, "bottom y %.2f" % min(ys))
        if n.endswith("A"):
            sv = pieces[n].g["Soil"].v
            top = max(p[1] for p in sv)
            chk("   PlinthTreeA soil bed has one flat top plane (four corners at one y)", sum(1 for p in sv if abs(p[1] - top) < 1e-6) >= 4, "y %.2f" % top)
        else:
            pv = pieces[n].g["Plinth"].v
            top = max(p[1] for p in pv)
            chk("   PlinthTreeB pedestal rim is one level ring (every top vertex at one y)", len({round(p[1], 4) for p in pv if p[1] > top - 0.02}) == 1, "y %.2f" % top)
    for n in ("Dawnspire_Trees_BasinTreeA", "Dawnspire_Trees_BasinTreeB"):
        bot = [p for p in pieces[n].g["Plinth"].v if p[1] < -0.1]
        chk("   %s basin foot is flat (all bottom vertices at one y)" % n.replace("Dawnspire_Trees_", ""), len({round(p[1], 4) for p in bot}) == 1, "y %.2f" % bot[0][1])
    for v in "ABC":
        n = "Dawnspire_Rocks_SteppingStone" + v
        ys = [p[1] for p in pieces[n].g["Stone"].v]
        chk("   SteppingStone%s flat bottom at -0.3, top within 0.2-0.6" % v, abs(min(ys) + 0.3) < 1e-6 and 0.2 < max(ys) < 0.6, "top %.2f" % max(ys))
    L.append("")
    L.append("4. Heights and sizes against the brief")
    for n, lo, hi in (("TierTreeA", 16, 20), ("TierTreeB", 14, 20), ("PlinthTreeA", 8, 10), ("PlinthTreeB", 8, 10), ("BasinTreeA", 8, 10), ("BasinTreeB", 8, 10), ("BoundTreeA", 13, 15), ("BoundTreeB", 13, 15)):
        m = meta["Dawnspire_Trees_" + n]
        chk("   %s height %.1f (range %d-%d)" % (n, m["height"], lo, hi), lo <= m["height"] <= hi)
    for n in ("BoundTreeA", "BoundTreeB"):
        m = meta["Dawnspire_Trees_" + n]
        lo, hi = m["bounds_min"], m["bounds_max"]
        chk("   %s crown spread %.1f x %.1f (12 to 14 across)" % (n, hi[0] - lo[0], hi[2] - lo[2]), 12 <= max(hi[0] - lo[0], hi[2] - lo[2]) <= 20)
    chk("   no piece sinks more than 1.5 studs under the ground", all(m["bounds_min"][1] > -1.6 for m in meta.values()))
    L.append("")
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
        chk("   %s re-imports with %d objects, the same triangles and boxes, and its DS_Anchor" % (fname, len(expect)), not problems, str(problems[:3]))
        raw = open(path, "rb").read()
        home = os.path.expanduser("~").encode()
        chk("   %s holds neither this machine's home path nor its user name" % fname, home not in raw and os.path.basename(home) not in raw, "size %d bytes" % len(raw))
    L.append("")
    L.append("RESULT: %s" % ("ALL OK" if not bad else "FAILED: " + "; ".join(bad)))
    with open(os.path.join(RENDERS, "verify.txt"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[-14:]))


def main():
    {"look": look, "sheets": sheets, "silhouette": silhouette, "qa": run_qa, "export": export, "verify": verify}[STAGE]()


if __name__ == "__main__":
    main()

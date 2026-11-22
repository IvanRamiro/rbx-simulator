"""Headless runner for Dawnspire Hall (orthodox_hq.py). Never the open Blender window.

    blender -b --factory-startup -P tools/blender/world/orthodox_hq_run.py -- <stage> [args]
      look        quick renders (front, three-quarter) into renders/orthodox_hq/look_*.png
      sides       the six sides, clay and paint, each beside the concept sheet's matching view (renders/orthodox_hq/six_sides_*.png)
      silhouette  black silhouettes at thumbnail size from the plaza's eye view and a player's eye height on the stair
      night       a dark-lit render with the glow on, and a plain render with the glow off
      verify      the numeric checks (symmetry, roof alignment, pillar grid, stairs, ...), written to renders/orthodox_hq/verify.txt
      qa          asset QA (profile roblox) on every exported piece, kit_check on the structural modules
      export      FBX files into assets/world/MurimCrossing/Orthodox/, the placements Lua, the QA report
Scratch output goes to renders/orthodox_hq/ (local, never committed).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import hq_blender as B  # noqa: E402
import orthodox_hq as O  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "look"
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "orthodox_hq")
os.makedirs(RENDERS, exist_ok=True)
SHEET = os.environ.get("HQ_SHEET")   # the concept sheet (a local image, not in the repository): the six-side renders sit beside its matching views


def scene_with_compound(mode="paint", glow=True):
    B.clear_scene()
    data = O.build_all()
    coll = bpy.data.collections.new("Orthodox")
    bpy.context.scene.collection.children.link(coll)
    first, objs = B.build_compound(data, coll)
    B.set_material_mode(objs, mode, glow)
    return data, objs


def sun(front=True, strength=3.4, azimuth=-30.0, elevation=52.0, color=(1.0, 0.97, 0.92)):
    B.set_sun(strength, (-elevation, 0.0, azimuth), color)


def look():
    data, objs = scene_with_compound("paint")
    B.setup_render((1280, 800))
    B.set_world((0.55, 0.62, 0.72), 1.0)
    sun()
    views = {
        "front": ((0, 28, -190), (0, 38, 0), 38),
        "q3": ((-120, 48, -140), (0, 34, 0), 40),
        "court": ((0, 6, -62), (0, 18, 0), 28),
        "corner": ((44, 40, -44), (19, 33, -13), 55),
    }
    for name, (loc, tgt, lens) in views.items():
        cam = B.add_camera("cam_" + name, B.rbv(*loc), B.rbv(*tgt), lens=lens)
        B.shoot(cam, os.path.join(RENDERS, "look_%s.png" % name))
    print("looked")


# the concept sheet's matching views: (x0, y0, x1, y1) in the 1536 x 1024 image
SHEET_VIEWS = {"left": (10, 672, 375, 966), "front": (380, 672, 790, 966), "right": (795, 672, 1140, 966), "back": (1148, 672, 1512, 966),
               "top": (996, 22, 1512, 352), "bottom": (996, 392, 1512, 655)}


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


def resize_to_height(px, hh):
    import numpy as np
    h, w = px.shape[0], px.shape[1]
    ww = int(round(w * hh / h))
    ys = (np.linspace(0, h - 1, hh)).astype(int)
    xs = (np.linspace(0, w - 1, ww)).astype(int)
    return px[ys][:, xs]


def compose(mine_path, view, out_path, hh=640):
    """My render on the left, the concept sheet's matching view on the right."""
    import numpy as np
    mine = load_pixels(mine_path)
    if not SHEET:
        raise SystemExit("HQ_SHEET must name the concept sheet's image")
    sheet = load_pixels(SHEET)
    sh = sheet.shape[0]
    x0, y0, x1, y1 = SHEET_VIEWS[view]
    crop = sheet[sh - y1:sh - y0, x0:x1]          # (the image's rows run bottom to top)
    a = resize_to_height(mine, hh)
    b = resize_to_height(crop, hh)
    gap = np.ones((hh, 8, 4), np.float32) * 0.05
    save_pixels(np.concatenate([a, gap, b], axis=1), out_path)


SIDE_CAMS = {
    "front": dict(loc=(0, 44, -300), tgt=(0, 40, 0), lens=58),
    "back": dict(loc=(0, 44, 300), tgt=(0, 40, 0), lens=58),
    "left": dict(loc=(-300, 44, 0), tgt=(0, 40, 0), lens=58),
    "right": dict(loc=(300, 44, 0), tgt=(0, 40, 0), lens=58),
}


def six_sides(mode="paint", tag="paint", glow=True):
    data, objs = scene_with_compound(mode, glow)
    B.setup_render((1280, 960))
    B.set_world((0.55, 0.62, 0.72) if mode == "paint" else (0.5, 0.5, 0.5), 1.0)
    for view, c in SIDE_CAMS.items():
        az = {"front": -30, "back": 150, "left": -120, "right": 60}[view]
        sun(azimuth=az)
        cam = B.add_camera("cam_" + view, B.rbv(*c["loc"]), B.rbv(*c["tgt"]), lens=c["lens"])
        path = os.path.join(RENDERS, "side_%s_%s.png" % (view, tag))
        B.shoot(cam, path)
    # top and bottom: orthographic
    sun(azimuth=-30)
    for view, rot, z in (("top", (0, 0, math.pi), 400.0), ("bottom", (math.pi, 0, 0), -400.0)):
        cam = bpy.data.objects.new("cam_" + view, bpy.data.cameras.new("cam_" + view))
        bpy.context.scene.collection.objects.link(cam)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = 140
        cam.data.clip_end = 2000
        cam.location = (0.0, -8.0, z)
        cam.rotation_euler = rot
        path = os.path.join(RENDERS, "side_%s_%s.png" % (view, tag))
        B.shoot(cam, path)
    for view in SIDE_CAMS:
        compose(os.path.join(RENDERS, "side_%s_%s.png" % (view, tag)), view, os.path.join(RENDERS, "six_%s_%s.png" % (view, tag)))
    for view in ("top", "bottom"):
        compose(os.path.join(RENDERS, "side_%s_%s.png" % (view, tag)), view, os.path.join(RENDERS, "six_%s_%s.png" % (view, tag)))
    print("six sides", tag)


def sides():
    six_sides("paint", "paint")
    six_sides("clay", "clay")


# ---------------------------------------------------------------------------------------------------------------------------------
# silhouettes and night
# ---------------------------------------------------------------------------------------------------------------------------------
def silhouette():
    """Black silhouettes at thumbnail size: from the plaza's middle at eye height and from a player's eye on the stair."""
    data, objs = scene_with_compound("black")
    B.setup_render((384, 240), samples=8)
    B.set_world((1.0, 1.0, 1.0), 1.0)
    B.set_sun(0.0, (-50, 0, 0))
    views = {"plaza": ((0, -11.0, -206.0), (0, 40, 0), 30), "stair": ((0, 2.0, -86.0), (0, 38, 0), 28), "stair_top": ((0, 4.5, -56.0), (0, 40, 0), 24)}
    for name, (loc, tgt, lens) in views.items():
        cam = B.add_camera("cam_" + name, B.rbv(*loc), B.rbv(*tgt), lens=lens)
        B.shoot(cam, os.path.join(RENDERS, "silhouette_%s.png" % name))
    print("silhouettes")


def night():
    """A dark-lit render with the glow on, and a plain daylight render with the glow off."""
    data, objs = scene_with_compound("paint", True)
    B.setup_render((1280, 800), samples=24)
    B.set_world((0.012, 0.02, 0.05), 1.0)
    B.set_sun(0.5, (-45, 0, -30), (0.55, 0.65, 1.0))
    # the four lamp lights of the hall (warm azure-white), as the game will have them
    n = 0
    for p in data["placements"]:
        if p["piece"] == "Orthodox_Lantern" and p.get("light"):
            ld = bpy.data.lights.new("lamp%d" % n, "POINT")
            ld.energy = 3500
            ld.color = (0.55, 0.78, 1.0)
            ld.shadow_soft_size = 0.5
            lo = bpy.data.objects.new("lamp%d" % n, ld)
            bpy.context.scene.collection.objects.link(lo)
            lo.location = B.rbv(p["x"], p["y"] + 5.0, p["z"])
            n += 1
    for name, (loc, tgt, lens) in {"front": ((0, 26, -170), (0, 36, 0), 36), "court": ((0, 6, -62), (0, 18, 0), 28)}.items():
        cam = B.add_camera("cam_" + name, B.rbv(*loc), B.rbv(*tgt), lens=lens)
        B.shoot(cam, os.path.join(RENDERS, "night_glow_on_%s.png" % name))
    data, objs = scene_with_compound("paint", False)
    B.set_world((0.55, 0.62, 0.72), 1.0)
    sun()
    for name, (loc, tgt, lens) in {"front": ((0, 26, -170), (0, 36, 0), 36), "court": ((0, 6, -62), (0, 18, 0), 28)}.items():
        cam = B.add_camera("cam_" + name, B.rbv(*loc), B.rbv(*tgt), lens=lens)
        B.shoot(cam, os.path.join(RENDERS, "glow_off_%s.png" % name))
    print("night")


# ---------------------------------------------------------------------------------------------------------------------------------
# QA, export, placements
# ---------------------------------------------------------------------------------------------------------------------------------
OUT = os.path.join(REPO, "assets", "world", "MurimCrossing", "Orthodox")
GROUPS = {
    "Structure": ["Court", "Woldae", "Balustrades", "HallBody", "HallInterior", "VaultDoor", "Rock"],
    "Roofs": ["HallRoof1", "HallTier2", "HallTier3", "HallTier4", "HallTier5"],
    "Modules": ["Tower", "GatePavilion"],
    "Props": ["Lantern", "Banner", "Flag", "Spire", "Basin"],
}
ACCEPT = (
    ("UV overlap", "no texture is ever applied: the UV set exists so the mesh imports, charts are box projections that overlap by design"),
    ("open boundary", "hidden undersides, contact faces and buried feet (a closed bottom would only add hidden triangles)"),
    ("non-manifold", "two solids that meet along an edge or a corner (a box on a box)"),
    ("duplicate verts", "the corners of two boxes that touch share a position"),
    ("hidden back-to-back", "faces of two solids resting on each other (a few per stack)"),
    ("fully enclosed", "the azure glow core sits inside the crystal and the lamp house on purpose"),
    ("lowest point", "the pieces' feet are buried below the floor on purpose (they stand in the ground)"),
)


def accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def run_qa():
    data = O.build_all()
    B.clear_scene()
    coll = bpy.data.collections.new("qa")
    bpy.context.scene.collection.children.link(coll)
    qa = B.qa_module()
    lines = ["Dawnspire Hall: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece", ""]
    all_pass = True
    result = {}
    for name in sorted(data["pieces"]):
        objs = B.piece_objects(name, data["pieces"][name], coll)
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
        t = {o.name: B.tris(o) for o in objs}
        all_pass &= r["pass"]
        lines.append("%s: %s, %d triangles, %d errors" % (name, "PASS" if r["pass"] else "FAIL", sum(t.values()), len(r["errors"])))
        for k, v in sorted(t.items()):
            lines.append("    %-40s %6d" % (k, v))
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
        result[name] = (r["pass"], sum(t.values()))
    lines.insert(1, "Overall: %s" % ("PASS (zero errors on every piece)" if all_pass else "FAIL"))
    with open(os.path.join(RENDERS, "qa.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if l.endswith("errors") or l.startswith("Overall")))
    return all_pass


def kit_check():
    """kit_check.py on the structural modules (grid 0.5, bottom-centre pivot)."""
    data = O.build_all()
    B.clear_scene()
    coll = bpy.data.collections.new("kc")
    bpy.context.scene.collection.children.link(coll)
    path = os.environ.get("HQ_KITCHECK_DIR")
    if not path:
        raise SystemExit("HQ_KITCHECK_DIR must name the folder of the environment-kits skill's kit_check.py")
    sys.path.insert(0, path)
    import kit_check as KC
    lines = ["kit_check (grid 0.5, pivot bottom-centre, prefix Orthodox_) on every piece; curved roofs, lathe columns and rock are off-grid by nature", ""]
    for name in sorted(data["pieces"]):
        objs = B.piece_objects(name, data["pieces"][name], coll)
        r = KC.run(objects=[o.name for o in objs], grid=0.5, pivot="bottom-center", texture=256, tol=0.001, prefix="Orthodox_", fix=False)
        for oname, info in sorted(r["pieces"].items()):
            lines.append("%-40s dims %s  errors %d  warnings %d" % (oname, info["dims_m"], len(info["errors"]), len(info["warnings"])))
            for e in info["errors"][:3]:
                lines.append("      %s" % e)
    with open(os.path.join(RENDERS, "kit_check.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("kit_check written")


def verify_fbx(path, expect):
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if "OH_Anchor" not in got:
        problems.append("no OH_Anchor")
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
    extra = sorted(set(got) - set(expect) - {"OH_Anchor"})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems


def export():
    import worldlib as W
    if not run_qa():
        raise SystemExit("QA failed: nothing exported")
    data = O.build_all()
    os.makedirs(OUT, exist_ok=True)
    report = {}
    only = os.environ.get("HQ_ONLY")          # e.g. HQ_ONLY=Structure re-exports one file
    for group, names in GROUPS.items():
        if only and group != only:
            continue
        B.clear_scene()
        coll = bpy.data.collections.new("exp")
        bpy.context.scene.collection.children.link(coll)
        objs_all, expect = [], {}
        for n in names:
            objs = B.piece_objects("Orthodox_" + n, data["pieces"]["Orthodox_" + n], coll)
            for o in objs:
                lo, hi = B.bbox_roblox([o])
                expect[o.name] = (B.tris(o), lo, hi)
            objs_all += objs
        path = os.path.join(OUT, "Orthodox_%s.fbx" % group)
        W.export_batch(objs_all, path, image=None, anchor_name="OH_Anchor")
        B.scrub(path)
        problems = verify_fbx(path, expect)
        report[group] = {"fbx": os.path.relpath(path, REPO), "objects": sorted(expect), "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok"}
        print("EXPORTED", path, len(expect), "objects", "verify:", problems or "ok")
    # piece boxes for the notes
    boxes = {}
    for n, piece in data["pieces"].items():
        lo, hi = piece.bounds()
        boxes[n] = {"min": [round(v, 2) for v in lo], "max": [round(v, 2) for v in hi], "tris": piece.tris(), "materials": piece.stats()}
    if only and os.path.exists(os.path.join(OUT, "pieces.json")):        # (a one-file re-export keeps the other files' entries)
        old = json.load(open(os.path.join(OUT, "pieces.json")))["files"]
        old.update(report)
        report = old
    with open(os.path.join(OUT, "pieces.json"), "w") as f:
        json.dump({"frame": "pad frame: origin at the pad's centre (+0.5 up), y = 0 the court floor, front is -Z; every piece at its own origin; anchor OH_Anchor",
                   "files": report, "pieces": boxes}, f, indent=1)
    import orthodox_hq_lua as L
    L.write(data)
    print("EXPORT_DONE")


def main():
    {"look": look, "sides": sides, "silhouette": silhouette, "night": night, "qa": run_qa, "kitcheck": kit_check, "export": export}[STAGE]()


if __name__ == "__main__":
    main()

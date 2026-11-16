"""Headless runner for the Blossom Sanctuary's meshes (blossom_assets.py). Never the open Blender window.

    blender -b --factory-startup -P tools/blender/world/blossom_assets_run.py -- <stage> [pieces...]
      build     build each piece (one at a time, the scene cleared between) and print its triangles
      qa        build, then the asset QA (blender-asset-qa, profile roblox) on each piece: BS_QA_SCRIPT names its qa_check.py
      render    build each piece and render renders/blossom_sanctuary/assets/<Piece>.png (front, side, top, three-quarter)
      lineup    the six trees side by side (trees_lineup.png) and their black silhouettes (trees_silhouettes.png)
      sheet     every other piece on one sheet (others_sheet.png)
      export    build, QA, export the four FBX files (anchor BS_Anchor), scrub them, write qa.txt and pieces.json
Scratch images go to $BS_TMP (default: the system temp folder).
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import blossom_assets as A  # noqa: E402
import worldlib as W  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "build"
NAMES = ARGS[1:] or None
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "blossom_sanctuary", "assets")
OUT = os.path.join(REPO, "assets", "world", "BlossomSanctuary")
TMP = os.environ.get("BS_TMP") or tempfile.gettempdir()

GROUPS = {
    "Trees": ["BS_TreeElder", "BS_TreeWeeping", "BS_TreeLeaning", "BS_TreeTwin", "BS_TreeYoung", "BS_TreeGnarled"],
    "Stones": ["BS_Bridge", "BS_SteppingStoneA", "BS_SteppingStoneB", "BS_SteppingStoneC", "BS_EdgeRockA", "BS_EdgeRockB",
               "BS_EdgeRockC", "BS_KerbStone", "BS_SeatStone"],
    "Water": ["BS_LilyPadA", "BS_LilyPadB", "BS_LilyPadCluster", "BS_LilyFlower", "BS_Reeds", "BS_WaterPlantain", "BS_PetalDrift"],
    "Koi": ["BS_KoiKohaku", "BS_KoiKohakuTail", "BS_KoiShowa", "BS_KoiShowaTail", "BS_KoiOgon", "BS_KoiOgonTail", "BS_Ripple"],
}


def names():
    if NAMES:
        return NAMES
    return [p for g in GROUPS.values() for p in g if p in A.PIECES]


def qa_module():
    path = os.environ.get("BS_QA_SCRIPT")
    if not path:
        raise SystemExit("BS_QA_SCRIPT must name the asset QA's qa_check.py")
    sys.path.insert(0, os.path.dirname(path))
    import qa_check
    return qa_check


def run_qa(piece, objs, meta=None):
    qa = qa_module()
    # (a koi's body and tail are checked together: the tail is meant to sit in the body's socket)
    r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
    t = {o.name: A.tris(o) for o in objs}
    print("QA", piece, "PASS" if r["pass"] else "FAIL", sum(t.values()), "tris", t)
    for e in r["errors"]:
        print("   ERROR", e)
    for w in r["warnings"]:
        print("   warn ", w)
    if meta:
        print("   meta ", json.dumps(meta))
    return r


# ---------- renders ----------
def setup_scene(res=(720, 540)):
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.use_stamp = False
    for attr in dir(scene.render):
        if attr.startswith("use_stamp_"):
            try:
                setattr(scene.render, attr, False)
            except (AttributeError, TypeError):
                pass
    try:
        scene.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.get("BSBackdrop") or bpy.data.worlds.new("BSBackdrop")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.42, 0.43, 0.45, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.objects.get("BSSun")
    if not sun:
        sun = bpy.data.objects.new("BSSun", bpy.data.lights.new("BSSun", "SUN"))
        scene.collection.objects.link(sun)
    sun.data.energy = 3.2
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(50), 0, math.radians(40))
    return scene


def ref_bar(x, y0, z):
    """The 5-stud human-height reference bar."""
    g = A.Geo()
    for dy in (0.0, 5.0):
        for dx, dz in ((-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)):
            g.vert((x + dx, y0 + dy, z + dz))
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        g.face(*f)
    m = bpy.data.materials.get("BS_RefBar") or bpy.data.materials.new("BS_RefBar")
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.03, 0.05, 0.09, 1)
    me = bpy.data.meshes.new("BSRefBar")
    me.from_pydata([tuple(W.rb(*p)) for p in g.v], [], g.f)
    me.materials.append(m)
    o = bpy.data.objects.new("BSRefBar", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def cam(name, loc, look, ortho=None, lens=40.0, up=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(c)
    lo, lk = W.rb(*loc), W.rb(*look)
    c.location = lo
    c.rotation_euler = (lk - lo).to_track_quat("-Z", up or "Y").to_euler()
    c.data.clip_start, c.data.clip_end = 0.05, 2000
    if ortho:
        c.data.type, c.data.ortho_scale = "ORTHO", ortho
    else:
        c.data.type, c.data.lens = "PERSP", lens
    return c


def shoot(c, path):
    scene = bpy.context.scene
    scene.camera = c
    scene.render.filepath = path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return path


def piece_views(piece, objs, out_png, res=(720, 540)):
    setup_scene(res)
    lo, hi = A.bbox_roblox(objs)
    lo, hi = Vector(lo), Vector(hi)
    base = 0.0 if lo.y > -1.0 and piece.find("Koi") < 0 and piece != "BS_Ripple" else lo.y
    if piece.find("Koi") >= 0 or piece == "BS_Ripple":
        base = lo.y
    bar = ref_bar(hi.x + 1.2, base, lo.z - 1.2)
    lo2 = Vector((lo.x, min(lo.y, base), lo.z - 1.5))
    hi2 = Vector((hi.x + 1.5, max(hi.y, base + 5), hi.z))
    cen = (lo2 + hi2) / 2
    size = hi2 - lo2
    asp = res[0] / res[1]
    d = max(size) * 3 + 20
    panels = []
    s_front = max(size.x, size.y * asp) * 1.12
    panels.append((shoot(cam("BSCamF", (cen.x, cen.y, cen.z + d), cen, ortho=s_front), os.path.join(TMP, piece + "_f.png")),
                   "%s  front (from +Z)" % piece))
    s_side = max(size.z, size.y * asp) * 1.12
    panels.append((shoot(cam("BSCamS", (cen.x + d, cen.y, cen.z), cen, ortho=s_side), os.path.join(TMP, piece + "_s.png")),
                   "side (from +X)"))
    s_top = max(size.x, size.z * asp) * 1.12
    ct = cam("BSCamT", (cen.x, cen.y + d, cen.z), cen, ortho=s_top)
    ct.rotation_euler = (0, 0, 0)
    panels.append((shoot(ct, os.path.join(TMP, piece + "_t.png")), "top (front +Z down)"))
    dist = size.length * 1.2 + 2
    eye = cen + Vector((0.62, 0.42, 0.66)).normalized() * dist
    panels.append((shoot(cam("BSCam34", tuple(eye), tuple(cen), lens=40), os.path.join(TMP, piece + "_q.png")),
                   "three-quarter; bar = 5 studs"))
    import hub_district_stages as S
    os.environ["HUB_LOOK_DIR"] = TMP
    S.compose(panels, 2, out_png, res[0], res[1])
    bpy.data.objects.remove(bar, do_unlink=True)
    bpy.context.scene.render.engine = bpy.context.scene.render.engine
    return out_png


def render(pieces):
    os.makedirs(RENDERS, exist_ok=True)
    for p in pieces:
        A.clear_scene()
        objs, meta = A.build_piece(p)
        print("BUILT", p, sum(A.tris(o) for o in objs), {o.name: A.tris(o) for o in objs}, json.dumps(meta))
        out = piece_views(p, objs, os.path.join(RENDERS, p + ".png"))
        print("RENDER", out)
        A.clear_scene()


def _row(pieces, turn, gap=5.0):
    """Builds the pieces in a row along X (each turned `turn` radians about the vertical), returns the objects and the extents."""
    objs_all, x = [], 0.0
    for p in pieces:
        objs, meta = A.build_piece(p)
        for o in objs:
            o.rotation_euler = (0, 0, turn)
        bpy.context.view_layer.update()
        lo, hi = A.bbox_roblox(objs)
        dx = x - lo[0]
        for o in objs:
            o.location.x += dx
        x += (hi[0] - lo[0]) + gap
        objs_all += objs
    bpy.context.view_layer.update()
    return objs_all, x - gap


def _row_shot(objs, width, path, res, silhouette=False):
    lo, hi = A.bbox_roblox(objs)
    bar = ref_bar(width + 2.0, 0.0, 0.0)
    w = width + 4.0
    h = max(hi[1], 5.0) + 2.0
    s = max(w, h * res[0] / res[1]) * 1.04
    c = cam("BSCamRow", (w / 2 - 0.5, h / 2 - 1.0, 300.0), (w / 2 - 0.5, h / 2 - 1.0, 0.0), ortho=s)
    shoot(c, path)
    bpy.data.objects.remove(bar, do_unlink=True)
    return path


def lineup(pieces):
    """trees_lineup.png (colour) and trees_silhouettes.png (black on white): the six trees at one scale, front row and side row."""
    import hub_district_stages as S
    os.environ["HUB_LOOK_DIR"] = TMP
    os.makedirs(RENDERS, exist_ok=True)
    trees = [p for p in GROUPS["Trees"] if p in A.PIECES]
    res = (2400, 620)
    for mode in ("colour", "silhouette"):
        panels = []
        for turn, label in ((0.0, "front (from +Z)"), (math.pi / 2, "side (each turned 90 degrees, from +X)")):
            A.clear_scene()
            scene = setup_scene(res)
            if mode == "silhouette":
                scene.render.engine = "BLENDER_WORKBENCH"
                sh = scene.display.shading
                sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (0.0, 0.0, 0.0)
                scene.world.color = (1.0, 1.0, 1.0)
                sh.background_type = "WORLD" if hasattr(sh, "background_type") else None
            objs, width = _row(trees, turn)
            path = os.path.join(TMP, "row_%s_%d.png" % (mode, int(turn * 10)))
            _row_shot(objs, width, path, res)
            panels.append((path, "%s, left to right: %s; bar = 5 studs" % (label, ", ".join(t.replace("BS_Tree", "") for t in trees))))
        out = os.path.join(RENDERS, "trees_lineup.png" if mode == "colour" else "trees_silhouettes.png")
        S.compose(panels, 1, out, res[0], res[1])
        print("LINEUP", out)
    A.clear_scene()


def sheet(pieces):
    """others_sheet.png: every piece but the trees, each in a three-quarter view with its 5-stud bar."""
    import hub_district_stages as S
    os.environ["HUB_LOOK_DIR"] = TMP
    others = [p for p in pieces if not p.startswith("BS_Tree")]
    panels, res = [], (560, 420)
    for p in others:
        A.clear_scene()
        objs, meta = A.build_piece(p)
        setup_scene(res)
        lo, hi = A.bbox_roblox(objs)
        lo, hi = Vector(lo), Vector(hi)
        small = "Koi" in p or p == "BS_Ripple"
        base = lo.y if small else 0.0
        bar = ref_bar(hi.x + 0.9, base, lo.z - 0.9)
        lo2 = Vector((lo.x, min(lo.y, base), lo.z - 1.2))
        hi2 = Vector((hi.x + 1.2, max(hi.y, base + 5.0), hi.z))
        cen = (lo2 + hi2) / 2
        dist = (hi2 - lo2).length * 1.15 + 1.0
        eye = cen + Vector((0.62, 0.5, 0.62)).normalized() * dist
        path = os.path.join(TMP, "sheet_%s.png" % p)
        shoot(cam("BSCamSheet", tuple(eye), tuple(cen), lens=40), path)
        panels.append((path, "%s  %d tris" % (p, sum(A.tris(o) for o in objs))))
    out = os.path.join(RENDERS, "others_sheet.png")
    S.compose(panels, 4, out, res[0], res[1])
    print("SHEET", out)
    A.clear_scene()


ACCEPT = (
    ("UV overlap", "UV charts are stacked on purpose: box-projected tiling UVs for a Roblox material, one tile per 8 studs; no baked texture"),
    ("lowest point", "by design: bedded below the ground or the water line (roots, footings, stone bodies), or a centre-origin piece"),
    ("open boundary", "by design: koi colour patches are cut out of one continuous body surface (the assembled fish is closed); "
                      "fallen petals are single-sided cards seen only from above"),
)


def _accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def _verify_fbx(path, expect):
    """Re-imports an exported FBX into an empty scene: the object names, triangle counts and Roblox-space boxes must match."""
    A.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if "BS_Anchor" not in got:
        problems.append("no BS_Anchor")
    else:
        lo, hi = A.bbox_roblox([got["BS_Anchor"]])
        if max(abs(x) for x in lo + hi) > 0.51:
            problems.append("BS_Anchor not at the origin %s %s" % (lo, hi))
    for name, (tris, lo, hi) in expect.items():
        o = got.get(name)
        if o is None:
            problems.append("missing " + name)
            continue
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
        l2, h2 = A.bbox_roblox([o])
        if t != tris:
            problems.append("%s tris %d != %d" % (name, t, tris))
        if max(abs(a - b) for a, b in zip(lo + hi, l2 + h2)) > 0.02:
            problems.append("%s box %s %s != %s %s" % (name, l2, h2, lo, hi))
    extra = sorted(set(got) - set(expect) - {"BS_Anchor"})
    if extra:
        problems.append("unexpected objects %s" % extra)
    A.clear_scene()
    return problems


def export(pieces):
    """assets/world/BlossomSanctuary/BlossomSanctuary_<Group>.fbx (anchor BS_Anchor at the origin, every piece at the origin as
    authored), scrubbed and verified by re-import; renders/blossom_sanctuary/assets/qa.txt; assets/world/BlossomSanctuary/pieces.json."""
    import hub_district_stages as S
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    qa_lines, data, files = [], {}, {}
    all_pass = True
    for group, plist in GROUPS.items():
        A.clear_scene()
        objs_all, expect = [], {}
        for p in plist:
            # one piece at a time: built, checked, then the next (they share the scene only for the batch export)
            objs, meta = A.build_piece(p)
            r = run_qa(p, objs, meta)
            all_pass &= r["pass"]
            tris = {o.name: A.tris(o) for o in objs}
            lo, hi = A.bbox_roblox(objs)
            for o in objs:
                l1, h1 = A.bbox_roblox([o])
                expect[o.name] = (tris[o.name], l1, h1)
            entry = {"group": group, "objects": tris, "tris": sum(tris.values()), "bbox_min": lo, "bbox_max": hi}
            if "canopy_centre" in meta:
                entry.update({"canopy_centre": meta["canopy_centre"], "canopy_lowest": meta["canopy_lowest"],
                              "branch_lowest": meta["branch_lowest"], "canopy_size": meta["canopy_size"]})
            if "tail_hinge" in meta:
                entry["tail_hinge"] = meta["tail_hinge"]
                entry["tail_piece" if not p.endswith("Tail") else "body_piece"] = p + "Tail" if not p.endswith("Tail") else p[:-4]
            data[p] = entry
            qa_lines.append("%s: %s, %d triangles" % (p, "PASS" if r["pass"] else "FAIL", entry["tris"]))
            for name, t in sorted(tris.items()):
                qa_lines.append("    %-34s %6d" % (name, t))
            qa_lines.append("    bbox (Roblox studs) min %s max %s" % (lo, hi))
            for k in ("canopy_centre", "canopy_lowest", "branch_lowest", "tail_hinge"):
                if k in entry:
                    qa_lines.append("    %s: %s" % (k, entry[k]))
            for e in r["errors"]:
                qa_lines.append("    ERROR %s" % e)
            seen = set()
            for w in r["warnings"]:
                why = _accepted(w)
                if why:
                    if why not in seen:
                        qa_lines.append("    accepted warning(s): %s" % why)
                        seen.add(why)
                else:
                    qa_lines.append("    WARNING %s" % w)
            objs_all += objs
        path = os.path.join(OUT, "BlossomSanctuary_%s.fbx" % group)
        W.export_batch(objs_all, path, image=None, anchor_name="BS_Anchor")
        S._scrub(path)
        problems = _verify_fbx(path, expect)
        files[group] = {"fbx": os.path.relpath(path, REPO), "pieces": plist, "objects": len(expect) + 1, "verify": problems or "ok"}
        print("EXPORTED", path, len(expect), "objects", "verify:", problems or "ok")
    head = ["Blossom Sanctuary meshes: asset QA (blender-asset-qa qa_check.py, profile roblox) per piece",
            "Overall: %s" % ("PASS (zero errors on every piece)" if all_pass else "FAIL"), "",
            "Export verification (each FBX re-imported into an empty scene: names, triangles and boxes compared):"]
    for g, f in files.items():
        head.append("    %s: %s" % (f["fbx"], f["verify"]))
    head.append("")
    with open(os.path.join(RENDERS, "qa.txt"), "w") as fh:
        fh.write("\n".join(head + qa_lines) + "\n")
    with open(os.path.join(OUT, "pieces.json"), "w") as fh:
        json.dump({"units": "Roblox studs; Y up; each piece's front is +Z; origin at the ground contact under the base centre "
                            "(koi and ripple: their centre)", "anchor": "BS_Anchor (1-stud cube at the origin)", "files": files,
                   "pieces": data}, fh, indent=1)
    print("QA_ALL", all_pass)


def bridge_views(pieces):
    """BS_Bridge_elevation.png: a true side elevation (orthographic from +X) and an end view (orthographic from +Z), the
    5-stud bar beside each."""
    import hub_district_stages as S
    os.environ["HUB_LOOK_DIR"] = TMP
    A.clear_scene()
    objs, meta = A.build_piece("BS_Bridge")
    res = (1600, 560)
    setup_scene(res)
    bar = ref_bar(0.0, 0.0, 17.2)
    side = cam("BSCamElev", (60.0, 0.6, 0.0), (0.0, 0.6, 0.0), ortho=36.5)
    p1 = shoot(side, os.path.join(TMP, "bridge_elev.png"))
    bpy.data.objects.remove(bar, do_unlink=True)
    bar = ref_bar(6.0, 0.0, 0.0)
    end = cam("BSCamEnd", (0.0, 0.6, 60.0), (0.0, 0.6, 0.0), ortho=36.5)
    p2 = shoot(end, os.path.join(TMP, "bridge_end.png"))
    bpy.data.objects.remove(bar, do_unlink=True)
    out = os.path.join(RENDERS, "BS_Bridge_elevation.png")
    S.compose([(p1, "BS_Bridge: true side elevation (orthographic from +X): deck 0 at the ends, 3.2 at the middle; the arch "
                    "opening springs at -1.6 from z = +-9; bar = 5 studs"),
               (p2, "BS_Bridge: end view (orthographic from +Z, at the same scale): curbs, end posts with rosettes, footings")],
              1, out, res[0], res[1])
    print("ELEVATION", out)
    A.clear_scene()


def main():
    if STAGE == "build":
        for p in names():
            A.clear_scene()
            objs, meta = A.build_piece(p)
            print("BUILT", p, sum(A.tris(o) for o in objs), {o.name: A.tris(o) for o in objs}, A.bbox_roblox(objs), json.dumps(meta))
    elif STAGE == "qa":
        for p in names():
            A.clear_scene()
            objs, meta = A.build_piece(p)
            run_qa(p, objs, meta)
    elif STAGE == "render":
        render(names())
    elif STAGE == "lineup":
        lineup(names())
    elif STAGE == "sheet":
        sheet(names())
    elif STAGE == "elevation":
        bridge_views(names())
    elif STAGE == "export":
        export(names())
    else:
        raise SystemExit("unknown stage " + STAGE)


if __name__ == "__main__":
    main()

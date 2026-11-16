"""Headless runner for the Hall of Records (hall_records.py, hall_layout.py, hub_ground.py). Never the open Blender window.

    blender -b --factory-startup -P tools/blender/world/hall_records_run.py -- <stage> [pieces...]
      build    build each piece (one at a time, the scene cleared between) and print its triangles
      qa       build, then the asset QA (blender-asset-qa, profile roblox) on each piece: HR_QA_SCRIPT names its qa_check.py
      render   each piece's sheet: renders/hall_of_records/assets/<Piece>.png (front, side, top, three-quarter, 5-stud bar)
      set      the hall assembled as placed (hall_layout.stations and its flags): set_eye.png, set_top.png, set_board.png
      ground   the hub's terrain and placements (src/worldbuild/Terrain/Yggdrasil.lua, Placements/Yggdrasil.lua)
      export   build, QA, export assets/world/HallOfRecords/HallOfRecords.fbx (anchor HR_Anchor) and the hub's changed paving,
               assets/world/Yggdrasil/Yggdrasil_Paving.fbx (anchor HB_Anchor); scrub both, verify by re-import, write qa.txt
               and assets/world/HallOfRecords/pieces.json
Scratch images go to $HR_TMP (default: the system temp folder).
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

import hall_layout as L  # noqa: E402
import hall_records as R  # noqa: E402
import worldlib as W  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "build"
NAMES = ARGS[1:] or None
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "hall_of_records", "assets")
OUT = os.path.join(REPO, "assets", "world", "HallOfRecords")
TMP = os.environ.get("HR_TMP") or tempfile.gettempdir()
PAVING = ("HB_Avenues", "HB_Plazas", "HB_PavingRunes")   # the hub's paving pieces the hall changed


def names():
    return NAMES or list(R.PIECES)


def qa_module():
    path = os.environ.get("HR_QA_SCRIPT")
    if not path:
        raise SystemExit("HR_QA_SCRIPT must name the asset QA's qa_check.py")
    sys.path.insert(0, os.path.dirname(path))
    import qa_check
    return qa_check


def run_qa(piece, objs):
    qa = qa_module()
    r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
    t = {o.name: R.tris(o) for o in objs}
    print("QA", piece, "PASS" if r["pass"] else "FAIL", sum(t.values()), "tris", t)
    for e in r["errors"]:
        print("   ERROR", e)
    for w in r["warnings"]:
        print("   warn ", w)
    return r


def build(pieces):
    for p in pieces:
        R.clear_scene()
        objs, meta = R.build_piece(p)
        print("BUILT", p, sum(R.tris(o) for o in objs), {o.name: R.tris(o) for o in objs})


def qa(pieces):
    ok = True
    for p in pieces:
        R.clear_scene()
        objs, meta = R.build_piece(p)
        ok &= run_qa(p, objs)["pass"]
    print("QA_ALL", ok)


def render(pieces):
    import blossom_assets_run as BR
    os.makedirs(RENDERS, exist_ok=True)
    for p in pieces:
        R.clear_scene()
        objs, meta = R.build_piece(p)
        out = BR.piece_views(p, objs, os.path.join(RENDERS, p + ".png"))
        print("RENDER", out)
        R.clear_scene()


def _assemble():
    """Every piece built once and copied to its stations (hall frame: Roblox x, z; a station's yaw), plus the flags. Returns objects."""
    R.clear_scene()
    built = {}
    placed = []
    coll = W.collection("HR_Set")
    for piece, x, z, yaw in L.stations() + [("HR_PathFlag", fx, fz, fy) for fx, fz, fy in L.flag_path()]:
        if piece not in built:
            built[piece], _ = R.build_piece(piece)
            for o in built[piece]:
                o.hide_render = True
                o.hide_viewport = True
        for src in built[piece]:
            o = src.copy()
            o.hide_render = False
            o.hide_viewport = False
            coll.objects.link(o)
            # Roblox (x, y, z) -> Blender (x, -z, y); a Roblox yaw about +Y is a Blender turn about +Z
            o.location = W.rb(x, 0.0, z)
            o.rotation_euler = (0.0, 0.0, yaw)
            placed.append(o)
    bpy.context.view_layer.update()
    return placed


def set_views(_pieces):
    import blossom_assets_run as BR
    import hub_district_stages as S
    os.environ["HUB_LOOK_DIR"] = TMP
    os.makedirs(os.path.dirname(RENDERS), exist_ok=True)
    out_dir = os.path.dirname(RENDERS)
    placed = _assemble()
    res = (1600, 1000)
    BR.setup_scene(res)
    BR.ref_bar(6.0, 0.0, 34.0)
    shots = [("set_eye", (0.0, 7.0, 62.0), (0.0, 7.0, 0.0), 30.0, None, "From the flag path at eye height (7 studs), the entrance ahead"),
             ("set_inside", (0.0, 6.5, 14.0), (0.0, 8.0, -19.0), 26.0, None, "Inside, from beside the Chronicle toward the Highest Cultivation stele"),
             ("set_side", (-22.0, 6.5, 22.0), (14.0, 7.0, -4.0), 26.0, None, "Inside, toward the Hall of Firsts and the hourglass"),
             ("set_side2", (22.0, 6.5, 22.0), (-14.0, 7.0, -4.0), 26.0, None, "Inside, toward the Rarest Beasts showcase and the notice board"),
             ("set_top", (0.0, 150.0, 0.01), (0.0, 0.0, 0.0), None, 80.0, "From above: the court, the six boards, the entrance (+Z, toward the tree, at the bottom), the flags"),
             ("set_high", (40.0, 38.0, 56.0), (0.0, 4.0, -2.0), 34.0, None, "Three-quarter from above")]
    panels = []
    for name, eye, look, lens, ortho, caption in shots:
        c = BR.cam("HRCam_" + name, eye, look, ortho=ortho, lens=lens or 35.0)
        if name == "set_top":
            c.rotation_euler = (0.0, 0.0, 0.0)
        path = os.path.join(out_dir, name + ".png")
        BR.shoot(c, path)
        panels.append((path, caption))
        print("SHOT", path)
    S.compose(panels, 2, os.path.join(out_dir, "set_review.png"), res[0] // 2, res[1] // 2)
    print("REVIEW", os.path.join(out_dir, "set_review.png"), "objects", len(placed))


def ground(_pieces):
    import hub_ground as G
    print("WROTE", G.export_terrain(), G.write_placements(None))


def _verify(path, anchor, expect):
    """Re-imports an FBX into an empty scene: the anchor at the origin and every object with its triangles and box."""
    R.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if anchor not in got:
        problems.append("no " + anchor)
    else:
        lo, hi = R.bbox_roblox([got[anchor]])
        if max(abs(x) for x in lo + hi) > 0.51:
            problems.append("%s not at the origin" % anchor)
    for name, (t, lo, hi) in expect.items():
        o = got.get(name)
        if o is None:
            problems.append("missing " + name)
            continue
        if R.tris(o) != t:
            problems.append("%s tris %d != %d" % (name, R.tris(o), t))
        l2, h2 = R.bbox_roblox([o])
        if max(abs(a - b) for a, b in zip(lo + hi, l2 + h2)) > 0.02:
            problems.append("%s box moved" % name)
    extra = sorted(set(got) - set(expect) - {anchor})
    if extra:
        problems.append("unexpected %s" % extra)
    R.clear_scene()
    return problems


ACCEPT = (
    ("UV overlap", "box-projected tiling UVs for a Roblox material, one tile per 8 studs; no baked texture"),
    ("lowest point", "by design: every block is bedded 0.3 under the ground so the terrain never shows a gap"),
)


def export(pieces):
    import hub_district as D
    import hub_district_stages as S
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(RENDERS), exist_ok=True)
    lines, data, all_ok = [], {}, True
    R.clear_scene()
    kit, expect = [], {}
    for p in R.PIECES:
        objs, meta = R.build_piece(p)
        r = run_qa(p, objs)
        all_ok &= r["pass"]
        t = {o.name: R.tris(o) for o in objs}
        lo, hi = R.bbox_roblox(objs)
        data[p] = {"objects": t, "tris": sum(t.values()), "bbox_min": lo, "bbox_max": hi}
        lines.append("%s: %s, %d triangles, bbox min %s max %s" % (p, "PASS" if r["pass"] else "FAIL", sum(t.values()), lo, hi))
        for n_, tt in sorted(t.items()):
            lines.append("    %-28s %6d" % (n_, tt))
        for e in r["errors"]:
            lines.append("    ERROR %s" % e)
        seen = set()
        for w in r["warnings"]:
            why = next((y for k, y in ACCEPT if k in w), None)
            if why and why not in seen:
                lines.append("    accepted warning(s): %s" % why)
                seen.add(why)
            elif not why:
                lines.append("    WARNING %s" % w)
        for o in objs:
            l1, h1 = R.bbox_roblox([o])
            expect[o.name] = (t[o.name], l1, h1)
        kit += objs
    hall = os.path.join(OUT, "HallOfRecords.fbx")
    W.export_batch(kit, hall, image=None, anchor_name="HR_Anchor")
    S._scrub(hall)
    v1 = _verify(hall, "HR_Anchor", expect)
    print("EXPORTED", hall, len(expect), "objects", "verify:", v1 or "ok")
    # the hub's paving the hall changed (the south-west avenue, the garden court and the old leaderboard's disc gone)
    R.clear_scene()
    paving = D.build_paving()
    objs = [o for base in PAVING for o in paving[base]]
    import hub_district_run as HR
    os.environ.setdefault("HUB_QA_SCRIPT", os.environ.get("HR_QA_SCRIPT", ""))
    # (checked with all of the hub's paving, as it lies: the runes sit in the Tree Ring's and the Ring Road's lapis too)
    prep = HR.run_qa({"Paving": [o for group in paving.values() for o in group]})
    all_ok &= prep["Paving"]["pass"]
    pexpect = {}
    for o in objs:
        l1, h1 = R.bbox_roblox([o])
        pexpect[o.name] = (R.tris(o), l1, h1)
    pav = os.path.join(REPO, "assets", "world", "Yggdrasil", "Yggdrasil_Paving.fbx")
    W.export_batch(objs, pav, image=None, anchor_name="HB_Anchor")
    S._scrub(pav)
    v2 = _verify(pav, "HB_Anchor", pexpect)
    print("EXPORTED", pav, len(objs), "objects", "verify:", v2 or "ok")
    head = ["Hall of Records meshes: asset QA (blender-asset-qa qa_check.py, profile roblox) per piece",
            "Overall: %s" % ("PASS (zero errors)" if all_ok else "FAIL"), "",
            "Export verification (re-imported into an empty scene: names, triangles, boxes):",
            "    %s: %s" % (os.path.relpath(hall, REPO), v1 or "ok"),
            "    %s: %s (%s)" % (os.path.relpath(pav, REPO), v2 or "ok", ", ".join(sorted(pexpect))),
            "    paving QA (all of the hub's paving together): %s, %d triangles, errors %s; exported: %d triangles"
            % ("PASS" if prep["Paving"]["pass"] else "FAIL", sum(prep["Paving"]["tris"].values()), prep["Paving"]["errors"],
               sum(t for t, _, _ in pexpect.values())), ""]
    with open(os.path.join(os.path.dirname(RENDERS), "qa.txt"), "w") as fh:
        fh.write("\n".join(head + lines) + "\n")
    with open(os.path.join(OUT, "pieces.json"), "w") as fh:
        json.dump({"units": "Roblox studs; Y up; each piece's front is +Z; origin on the ground under its base centre",
                   "anchor": "HR_Anchor (1-stud cube at the origin)", "file": os.path.relpath(hall, REPO), "pieces": data,
                   "paving": {"file": os.path.relpath(pav, REPO), "anchor": "HB_Anchor (the hub's centre)", "objects": sorted(pexpect)}},
                  fh, indent=1)
    print("QA_ALL", all_ok)


def main():
    {"build": build, "qa": qa, "render": render, "set": set_views, "ground": ground, "export": export}[STAGE](names())


if __name__ == "__main__":
    main()

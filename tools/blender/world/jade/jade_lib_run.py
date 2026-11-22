"""Headless runner for Jade Grove's library (never the open Blender window):

    blender -b --factory-startup -P tools/blender/world/jade/jade_lib_run.py -- <stage> <family|all> [piece ...]

stages
  review <family> [pieces]   six-view sheets (front, back, left, right, top, three-quarter), clay and paint, into renders/jade_grove_library/<family>/
  qa <family>                blender-asset-qa (profile roblox) on every piece: zero errors required; report in renders/jade_grove_library/qa_<family>.txt
  numbers <family>           triangle, material and size table (no Blender work)
  export <family|all>        FBX into assets/world/JadeGrove/Library/ (anchor JL_Anchor), the re-import check, the machine-path scrub
Families: trees, bamboo, rocks, plants, structures, bridges, cliffs, island (see FAMILIES). Evidence is local, never committed.
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import jade_lib_blender as B  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "review"
WHAT = ARGS[1] if len(ARGS) > 1 else "trees"
ONLY = ARGS[2:]
REPO = B.REPO
RENDERS = os.path.join(REPO, "renders", "jade_grove_library")
OUT = os.path.join(REPO, "assets", "world", "JadeGrove", "Library")

# family -> (module, FBX file name stem)
FAMILIES = {
    "trees": ("jade_lib_trees", "Trees"),
    "guardian": ("jade_lib_guardian", "Guardian"),
    "bamboo": ("jade_lib_bamboo", "Bamboo"),
    "rocks": ("jade_lib_rocks", "Rocks"),
    "plants": ("jade_lib_plants", "Plants"),
    "structures": ("jade_lib_structures", "Structures"),
    "bridges": ("jade_lib_bridges", "Bridges"),
    "cliffs": ("jade_lib_cliffs", "Cliffs"),
    "island": ("jade_lib_island_mesh", "Island"),
}
# FBX files and the families they hold, in the owner's import order
FILES = {
    "Trees": ["trees", "guardian"],
    "Bamboo": ["bamboo"],
    "Rocks": ["rocks"],
    "Plants": ["plants"],
    "Structures": ["structures"],
    "Bridges": ["bridges"],
    "Cliffs": ["cliffs", "island"],
}


def pieces_of(family):
    mod = importlib.import_module(FAMILIES[family][0])
    built = mod.build_all()
    if ONLY and STAGE not in ("export", "contact"):
        built = {k: v for k, v in built.items() if any(o in k for o in ONLY)}
    return built


def review(family):
    outdir = os.path.join(RENDERS, family)
    os.makedirs(outdir, exist_ok=True)
    for name, piece in pieces_of(family).items():
        for mode in ("clay", "paint"):
            B.clear_scene()
            coll = B.new_collection("rv")
            objs = B.piece_objects(piece, coll)
            B.set_mode(objs, mode)
            B.six_views(objs, os.path.join(outdir, name), mode=mode)
        print("reviewed", name, piece.tris())


def contact(family, view="q3", cols=4):
    outdir = os.path.join(RENDERS, family)
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for name, piece in pieces_of(family).items():
        B.clear_scene()
        coll = B.new_collection("ct")
        objs = B.piece_objects(piece, coll)
        p = os.path.join(outdir, "ct_%s.png" % name)
        B.contact_view(objs, p, view=view)
        paths.append(p)
    B.stitch(paths, cols, os.path.join(RENDERS, "contact_%s_%s.png" % (family, view)))
    for p in paths:
        os.remove(p)
    print("contact sheet", family, view, len(paths))


def scene(family):
    """The family's assembled scene (module.scene()) in six views, clay and paint."""
    mod = importlib.import_module(FAMILIES[family][0])
    outdir = os.path.join(RENDERS, family)
    os.makedirs(outdir, exist_ok=True)
    for mode in ("clay", "paint"):
        B.clear_scene()
        coll = B.new_collection("sc")
        objs = B.place_scene(mod.scene(), coll)
        B.set_mode(objs, mode)
        B.six_views(objs, os.path.join(outdir, "scene_" + family), mode=mode, res=(520, 520))
    print("scene", family)


def qa(family):
    built = pieces_of(family)
    ok, lines, result = B.run_qa(list(built.values()))
    lines.insert(0, "Overall: %s" % ("PASS (zero errors on every piece)" if ok else "FAIL"))
    lines.insert(0, "Jade Grove library: %s: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece" % family)
    os.makedirs(RENDERS, exist_ok=True)
    with open(os.path.join(RENDERS, "qa_%s.txt" % family), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if l.endswith("errors") or l.startswith("Overall")))
    return ok


def numbers(family):
    for name, p in pieces_of(family).items():
        lo, hi = p.bounds()
        print("%-30s %6d tris  size %5.1f x %5.1f x %5.1f  %s" % (name, p.tris(), hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], p.stats()))


def export_file(stem):
    """All families of one FBX file into one FBX."""
    families = FILES[stem]
    allp = []
    for fam in families:
        allp += list(importlib.import_module(FAMILIES[fam][0]).build_all().values())
    ok, lines, _ = B.run_qa(allp)
    if not ok:
        raise SystemExit("QA failed: nothing exported for %s\n%s" % (stem, "\n".join(l for l in lines if "ERROR" in l)))
    B.clear_scene()
    coll = B.new_collection("exp")
    objs_all, expect, ok_all = [], {}, True
    for fam in families:
        mod = importlib.import_module(FAMILIES[fam][0])
        for name, piece in mod.build_all().items():
            objs = B.piece_objects(piece, coll)
            for o in objs:
                lo, hi = B.bbox_roblox([o])
                expect[o.name] = (B.tris(o), lo, hi)
            objs_all += objs
    path = os.path.join(OUT, "JadeGrove_%s.fbx" % stem)
    B.export_fbx(objs_all, path)
    clean = B.scrub(path)
    problems = B.verify_fbx(path, expect)
    info = {"fbx": os.path.relpath(path, REPO), "objects": len(expect), "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok", "paths_clean": clean,
            "bytes": os.path.getsize(path)}
    print("EXPORTED", json.dumps(info))
    return info


def main():
    if STAGE == "review":
        review(WHAT)
    elif STAGE == "scene":
        scene(WHAT)
    elif STAGE == "contact":
        contact(WHAT, view=ONLY[0] if ONLY else "q3")
    elif STAGE == "qa":
        qa(WHAT)
    elif STAGE == "numbers":
        numbers(WHAT)
    elif STAGE == "export":
        stems = list(FILES) if WHAT == "all" else [WHAT]
        for s in stems:
            export_file(s)
    else:
        raise SystemExit("unknown stage " + STAGE)


if __name__ == "__main__":
    main()

"""Headless runner for the hub's redesign (hub_district.py, hub_ground.py, ygg_meshes.py). Never the open Blender window.

    blender -b --factory-startup -P tools/blender/world/hub_district_run.py -- <stage> [assets...]
      build    build and finish every asset; save tools/blender/world/HubDistrict.blend
      qa       build, then the asset QA (blender-asset-qa, profile roblox) on each asset: HUB_QA_SCRIPT names its qa_check.py
      paving   build the paving (hub_ground) and QA it
      review   build everything and render renders/hub_redesign/phase2_review.png
      export   build, QA, export the FBX files and the staged data (assets/world/Yggdrasil/)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import hub_district as D  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "build"
NAMES = ARGS[1:] or None
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def qa_module():
    path = os.environ.get("HUB_QA_SCRIPT")
    if not path:
        raise SystemExit("HUB_QA_SCRIPT must name the asset QA's qa_check.py")
    sys.path.insert(0, os.path.dirname(path))
    import qa_check
    return qa_check


def run_qa(groups, eps=0.001, tol=0.002):
    qa = qa_module()
    report = {}
    for asset, objs in groups.items():
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=eps, tol=tol)
        report[asset] = {"pass": r["pass"], "errors": r["errors"], "warnings": r["warnings"],
                         "tris": {o.name: D.tris(o) for o in objs}}
        print("QA", asset, "PASS" if r["pass"] else "FAIL", sum(D.tris(o) for o in objs), "tris")
        for e in r["errors"]:
            print("   ERROR", e)
        for w in r["warnings"]:
            print("   warn ", w)
    return report


def main():
    if STAGE == "build":
        groups, spots = D.build(NAMES)
        for a, objs in groups.items():
            print(a, sum(D.tris(o) for o in objs), "tris", [o.name for o in objs])
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "HubDistrict.blend"))
    elif STAGE == "qa":
        groups, spots = D.build(NAMES)
        rep = run_qa(groups)
        out = os.environ.get("HUB_QA_OUT")
        if out:
            with open(out, "w") as f:
                json.dump(rep, f, indent=1)
    else:
        import hub_district_stages as S
        getattr(S, STAGE)(NAMES)


if __name__ == "__main__":
    main()

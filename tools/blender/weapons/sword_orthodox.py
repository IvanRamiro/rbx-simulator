"""The Orthodox faction's secret weapon (run inside Blender, headless), id SecretOrthodox, Kind Sword:

    blender -b --factory-startup --python tools/blender/weapons/sword_orthodox.py -- clay|export|review|qa|all

A long straight double-edged blade of folded steel, risen out of a hollow, faceted gilt-and-silver bell (the pavilion guard, eight
arched windows through its wall, eaves swept up at the corners), a long two-handed grip of white ray-skin under a diamond wrap of
deep azure silk, a silver kashira and a gilt ring (the Korean hwan), and from the ring a silk cord with a knot, a jade pendant and a
tassel. The vault note "Faction Sword Orthodox 2026-11-22" holds the research, the silhouette study and the design in full.

Stages:
  clay    the HIGH-detail source in one grey clay, six views and close-ups (shape alone, no paint);
  export  build the game mesh (hand-built, at most 6,000 triangles), bake the four maps from the source, write assets/weapons/SecretOrthodox.fbx,
          its maps and the Placements file, scrub the machine path from the FBX;
  review  everything the owner and the QA gate look at (sword_orthodox_review.py), all in renders/faction_weapons_v2/Orthodox/;
  qa      the asset QA gate on the exported game mesh.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402
import sword_orthodox_mat as M  # noqa: E402
import sword_orthodox_parts as P  # noqa: E402
import weapon_kit as WK  # noqa: E402

B, Hm, W = SK.B, SK.Hm, SK.W
V = Vector
WEAPON_ID = "SecretOrthodox"
REVIEW = os.path.join(W.REPO, "renders", "faction_weapons_v2", "Orthodox")
SK.REVIEW = REVIEW
COMPARE = ("Sword6", 2.6)
BUDGET = 6000
GLOW = {}                      # no Neon: the design must not need it
HILT = (0.0, 0.0, P.Z_HILT)
TIP = (0.0, 0.0, P.Z_TIP)

# (name, builder, materials, smoothing angle or None, texel weight of its UV islands, the low mesh has it)
def materials():
    steel, silver = M.mat_steel(), M.mat_silver()
    gilt, deep = M.mat_gilt("OrGilt"), M.mat_gilt("OrGiltDeep", deep=True, scale=70.0)
    skin, silk = M.mat_rayskin(), M.mat_silk()
    azure = M.mat_cord("OrAzureCord", SK.srgb(8, 38, 108), SK.srgb(36, 92, 190))
    white = M.mat_cord("OrWhiteCord", SK.srgb(190, 196, 208), SK.srgb(244, 246, 250))
    gold_thread = M.mat_cord("OrGoldThread", SK.srgb(176, 124, 42), SK.srgb(246, 204, 108))
    jade = M.mat_jade()
    return dict(steel=steel, silver=silver, gilt=gilt, deep=deep, skin=skin, silk=silk, azure=azure, white=white, gold=gold_thread, jade=jade)


def pieces(m):
    return [
        ("Blade", P.blade, [m["steel"]], 14.0, 1.45, True),
        ("Collar", P.collar, [m["gilt"]], 40.0, 1.1, True),
        ("Shell", P.shell, [m["silver"], m["deep"]], 30.0, 1.0, True),
        ("Ribs", P.ribs, [m["gilt"]], 60.0, 1.0, False),
        ("Core", P.grip_core, [m["skin"]], 35.0, 1.2, True),
        ("Wrap", P.wrap, [m["silk"]], 50.0, 1.0, False),
        ("Fuchi", P.fuchi, [m["silver"], m["gilt"]], 40.0, 1.0, True),
        ("Kashira", P.kashira, [m["silver"], m["gilt"]], 40.0, 1.0, True),
        ("Ring", P.ring_pommel, [m["gilt"]], 40.0, 0.9, True),
        ("Cord", P.cord, [m["azure"], m["white"]], 60.0, 0.9, True),
        ("Knot", P.knot, [m["azure"], m["gilt"]], 60.0, 0.8, True),
        ("Pendant", P.pendant, [m["jade"], m["gilt"]], 40.0, 0.9, True),
        ("Tassel", P.tassel, [m["azure"], m["white"], m["gold"], m["gilt"]], 60.0, 0.9, True),
    ]


# ---------- the HIGH-detail source ----------
def build_hi(root=None):
    """Every part at full detail, as objects in one collection. Returns the list."""
    root = root or W.collection("OrthodoxHi")
    W.clear_collection(root)
    m = materials()
    out = []
    for name, fn, mats, ang, _, _ in pieces(m):
        hi = fn("hi")
        o = P.make_object(hi, "OR_" + name, root, mats, smooth_angle=ang)
        if name == "Shell":
            cut = P.make_object(P.window_cutters("hi"), "OR_Cut", root, mats[:1], smooth_angle=None)
            P.boolean_cut(o, cut)
            bpy.data.objects.remove(cut, do_unlink=True)
            P.smooth_by_angle(o, ang)
        out.append(o)
    return out, root


# ---------- the LOW game mesh ----------
def _tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


SMOOTH = dict(Blade=14.0, Collar=40.0, Shell=30.0, Core=35.0, Fuchi=40.0, Kashira=40.0, Ring=40.0, Cord=60.0, Knot=60.0, Pendant=40.0, Tassel=60.0)


def build_low_mesh(root):
    """The game mesh: every low part (hand-built, its UV laid in true proportion), joined and packed (sword_orthodox_low.py). Returns the
    joined object named SecretOrthodox_Body."""
    import sword_orthodox_low as LW
    pcs = []
    for name, fn in LW.LOW:
        o = P.make_object(fn(), "OL_" + name, root, [], smooth_angle=SMOOTH[name])
        if name == "Shell":
            cut = P.make_object(LW.window_cutters_low(), "OL_Cut", root, [], smooth_angle=None)
            P.boolean_cut(o, cut)
            bpy.data.objects.remove(cut, do_unlink=True)
            P.smooth_by_angle(o, SMOOTH[name])
        pcs.append(o)
    with bpy.context.temp_override(active_object=pcs[0], object=pcs[0], selected_objects=pcs, selected_editable_objects=pcs):
        bpy.ops.object.join()
    low = pcs[0]
    low.name = low.data.name = WEAPON_ID + "_Body"
    for c in list(low.users_collection):
        c.objects.unlink(low)
    root.objects.link(low)
    low.data.materials.clear()
    bm = bmesh.new()
    bm.from_mesh(low.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")      # the booleans leave n-gons; the bake and the export see triangles
    bm.to_mesh(low.data)
    bm.free()
    LW.pack_uv(low)
    return low


def export():
    """Bakes and writes the weapon. Returns (hi objects, root, report)."""
    root = W.collection("OrthodoxHi")
    objs, root = build_hi(root)
    saved = (B.make_low, B.bake, B.K.join, B._unwrap)
    B.make_low = lambda wid, hi, r, budget: build_low_mesh(r)
    B.bake = lambda wid, hi, low, size=1024, small=512: SK.bake(wid, hi, low, size, small, samples=16, extrusion=0.05, ray=0.14)
    try:
        report = WK.export(WEAPON_ID, "Sword", "sword_orthodox.py", objs, GLOW, root, HILT, TIP, budget=BUDGET, size=1024, small=512)
    finally:
        B.make_low, B.bake, B.K.join, B._unwrap = saved
    SK.scrub_paths(os.path.join(SK.OUT_DIR, WEAPON_ID + ".fbx"))
    import re
    lua = os.path.join(SK.PLACEMENTS_DIR, WEAPON_ID + ".lua")
    text = re.sub(r"^-- \w+ by ", "-- Built by ", open(lua).read(), count=1)
    open(lua, "w").write(text)
    return objs, root, report


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    import sword_orthodox_review as R
    R.run(sys.modules[__name__], stage)

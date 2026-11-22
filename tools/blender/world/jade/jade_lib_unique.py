"""jade_lib_unique: the uniqueness sheet (2026-11-22): black silhouettes at thumbnail size of ALL of Jade Grove's trees and rocks beside the other maps' existing trees and
rocks (extracted by name from the FBX files in assets/world/<Island>/), so that no two read alike.

    blender -b --factory-startup -P tools/blender/world/jade/jade_lib_unique.py -- silhouettes     (renders renders/jade_grove_library/uniq/*.png, front and side)
    python3 tools/blender/world/jade/jade_lib_unique.py sheet                                       (the sheet, via headless Chrome)
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUTDIR = os.path.join(REPO, "renders", "jade_grove_library", "uniq")
SIZE = 150

# label, FBX (relative to assets/world), object-name prefixes (an asset = the objects sharing one name before "__")
OTHERS = [
    ("Jade (old, replaced)", "JadeGrove/JadeGrove_Props.fbx", ["JG_AncientTreeA", "JG_AncientTreeB", "JG_JadeOutcrop", "JG_StandingStone", "JG_BambooClump"]),
    ("Jade (old, replaced)", "JadeGrove/JadeGrove_Island.fbx", ["JG_ElderTrunk"]),
    ("Blossom Sanctuary", "BlossomSanctuary/BlossomSanctuary_Trees.fbx", ["BS_TreeElder", "BS_TreeWeeping", "BS_TreeLeaning", "BS_TreeTwin", "BS_TreeYoung", "BS_TreeGnarled"]),
    ("Blossom Sanctuary", "BlossomSanctuary/BlossomSanctuary_Stones.fbx", ["BS_EdgeRockA", "BS_EdgeRockB", "BS_EdgeRockC", "BS_SteppingStoneA"]),
    ("Ember Peak", "EmberPeak/EmberPeak_Props.fbx", ["EP_PetrifiedTreeA", "EP_PetrifiedTreeB", "EP_BasaltClusterA", "EP_BasaltClusterB", "EP_ObsidianShard"]),
    ("Moonlit Isle", "MoonlitIsle/MoonlitIsle_Props.fbx", ["MI_LunarRock", "MI_MoonstoneShards"]),
    ("Moonlit Isle", "MoonlitIsle/MoonlitIsle_Kit.fbx", ["MI_MoonstoneSpire"]),
    ("Origin Abyss", "OriginAbyss/OriginAbyss_Props.fbx", ["OA_SlateRock", "OA_ThornCrown", "OA_VoidCrystals", "OA_RuinPillar"]),
]


def silhouettes():
    import bpy
    import jade_lib_blender as B
    import jade_lib_trees, jade_lib_guardian, jade_lib_rocks, jade_lib_bamboo
    os.makedirs(OUTDIR, exist_ok=True)
    for f in glob.glob(os.path.join(OUTDIR, "*.png")):
        os.remove(f)

    def shoot_scene(name):
        for view in ("front", "side"):
            p = os.path.join(OUTDIR, "%s__%s.png" % (name, view))
            objs = [o for o in bpy.data.objects if o.type == "MESH"]
            B.silhouette_image([objs], p, SIZE, view)
        lo, hi = B.bbox_roblox([o for o in bpy.data.objects if o.type == "MESH"])
        with open(os.path.join(OUTDIR, name + ".txt"), "w") as fh:
            fh.write("%.1f %.1f %.1f\n" % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    # Jade's own
    mine = {}
    mine.update(jade_lib_trees.build_all())
    g = jade_lib_guardian.build_all()
    for k in ("JG_Tree_Guardian", "JG_Tree_GuardianCrown"):
        mine[k] = g[k]
    mine.update({k: v for k, v in jade_lib_rocks.build_all().items()})
    for k, v in jade_lib_bamboo.build_all().items():
        if "Grove" in k or "Clump" in k:
            mine[k] = v
    for k, piece in mine.items():
        if k == "JG_Tree_GuardianCrown":
            continue
        B.clear_scene()
        coll = B.new_collection("u")
        items = [(piece, (0, 0, 0), 0.0, 1.0)]
        if k == "JG_Tree_Guardian":
            items.append((mine["JG_Tree_GuardianCrown"], (0, 0, 0), 0.0, 1.0))
        B.place_scene(items, coll)
        shoot_scene("Jade Grove (new)@" + k)
    # the others
    for label, rel, prefixes in OTHERS:
        path = os.path.join(REPO, "assets", "world", rel)
        for pre in prefixes:
            B.clear_scene()
            bpy.ops.import_scene.fbx(filepath=path)
            for o in list(bpy.data.objects):
                base = o.name.split(".")[0].split("__")[0]
                if o.type != "MESH" or base != pre:
                    bpy.data.objects.remove(o, do_unlink=True)
            if not [o for o in bpy.data.objects if o.type == "MESH"]:
                print("MISSING", pre)
                continue
            shoot_scene("%s@%s" % (label, pre))
    print("silhouettes done")


def sheet():
    sys.path.insert(0, os.path.join(REPO, "tools", "blender", "world", "jade"))
    import base64
    import jade_lib_plan as PL
    files = sorted(glob.glob(os.path.join(OUTDIR, "*__front.png")))
    groups = {}
    for f in files:
        name = os.path.basename(f)[:-len("__front.png")]
        label, _, asset = name.partition("@")
        groups.setdefault(label, []).append((asset, f))
    order = ["Jade Grove (new)", "Jade (old, replaced)", "Blossom Sanctuary", "Ember Peak", "Moonlit Isle", "Origin Abyss"]
    cell, gap = SIZE + 10, 6
    cols = 10
    parts = []
    y = 70
    W = cols * (cell + gap) + 40
    for label in order:
        items = groups.get(label, [])
        if not items:
            continue
        trees = [it for it in items if any(k in it[0] for k in ("Tree", "Elder", "Ancient", "Bamboo", "Thorn"))]
        rocks = [it for it in items if it not in trees]
        for kind, lst in (("trees and bamboo", trees), ("rocks and stones", rocks)):
            if not lst:
                continue
            parts.append(PL.label(20, y, "%s: %s" % (label.upper(), kind), 15, "#222", "800", "start", 1.0).replace('fill="#222"', 'fill="#222"').replace('stroke="#0a0f1e"', 'stroke="none"'))
            y += 8
            for k, (asset, f) in enumerate(lst):
                r, c = divmod(k, cols)
                x, yy = 20 + c * (cell + gap), y + r * (cell + 22 + gap)
                data = base64.b64encode(open(f, "rb").read()).decode()
                side = f.replace("__front.png", "__side.png")
                parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#999"/>' % (x, yy, cell, cell + 18))
                parts.append('<image x="%d" y="%d" width="%d" height="%d" href="data:image/png;base64,%s"/>' % (x + 5, yy + 2, SIZE, SIZE, data))
                dims = open(f.replace("__front.png", ".txt")).read().split()
                short = asset.replace("JG_", "").replace("EP_", "").replace("BS_", "").replace("MI_", "").replace("OA_", "")
                parts.append('<text x="%d" y="%d" font-size="9.5" fill="#111">%s</text>' % (x + 4, yy + SIZE + 12, "%s  %sx%s" % (short, dims[0], dims[1])))
            rows = (len(lst) + cols - 1) // cols
            y += rows * (cell + 22 + gap) + 26
    H = y + 20
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica Neue, Arial, sans-serif"><rect width="%d" height="%d" fill="#f3f1ea"/>'
           '<text x="20" y="34" font-size="20" font-weight="800" fill="#111">UNIQUENESS SHEET: Jade Grove\'s trees and rocks beside every other map\'s (black front silhouettes, each framed on its own size; width x height in studs)</text>%s</svg>' % (W, H, W, H, W, H, "".join(parts)))
    PL.render_svg(os.path.join(REPO, "renders", "jade_grove_library", "uniqueness_sheet.png"), svg, W, H, W)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args and args[0] == "silhouettes":
        silhouettes()
    else:
        sheet()

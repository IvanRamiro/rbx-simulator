"""jade_lib_swatch: before and after sheets for the polish pass's colour grade (2026-11-23). Evidence only, written to renders/jade_grove_library/polish/ (never committed).

    python3 jade_lib_swatch.py swatch                  swatches of every changed look, phase A beside the new one, with the value change
    blender -b --factory-startup -P jade_lib_swatch.py -- pieces     six pieces rendered with phase A's colours (top row) and the new ones (bottom row)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_looks as LK  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "jade_grove_library", "polish")

GROUPS = [
    ("Leaves", ["LeafDeep", "LeafMid", "LeafTeal", "LeafPale"]),
    ("Ferns, moss, grass", ["Fern", "FernBright", "Moss", "MossDeep", "Grass", "GrassPale"]),
    ("Bamboo", ["Culm", "CulmNode", "CulmPale"]),
    ("Jade, flowers, caps, bark", ["Jade", "JadeGlass", "BloomGold", "BloomWhite", "BloomRose", "BloomViolet", "CapPale", "Trunk", "TrunkPale", "Root"]),
]


def swatch():
    import jade_lib_plan as P
    W, H = 1500, 1040
    parts = ['<rect width="%d" height="%d" fill="#10161f"/>' % (W, H),
             P.label(30, 44, "JADE GROVE: the colour grade (before: phase A, after: the polish pass)", 22, "#ffffff", "800", "start"),
             P.label(30, 72, "value (the brightest channel) lifted 13 to 25 percent on leaves, ferns, moss and grass; the pale growth tones get a warm gold-green edge; Neon only on GlowTeal and GlowAmber (unchanged)", 13, "#9fb0d6", "500", "start")]
    y = 120
    for title, names in GROUPS:
        parts.append(P.label(30, y, title, 16, "#f4efe2", "700", "start"))
        y += 14
        x = 30
        for n in names:
            a, b = LK.LOOKS_PHASE_A[n][1], LK.LOOKS[n][1]
            va, vb = max(a) / 255.0, max(b) / 255.0
            parts.append('<rect x="%d" y="%d" width="64" height="86" fill="rgb%s"/><rect x="%d" y="%d" width="64" height="86" fill="rgb%s"/>' % (x, y, a, x + 64, y, b))
            parts.append(P.label(x + 64, y + 106, n, 12, "#ffffff", "700"))
            parts.append(P.label(x + 64, y + 122, "%+.0f%%" % (100 * (vb - va) / va), 12, "#ffd76a", "700"))
            x += 142
            if x > W - 160:
                x = 30
                y += 140
        y += 150
    # a strip of a sample forest ground: the leaf ramp as a gradient, old over new
    parts.append(P.label(30, y, "Leaf ramp (deep, mid, pale), phase A above, now below", 14, "#f4efe2", "700", "start"))
    y += 12
    for row, table in enumerate((LK.LOOKS_PHASE_A, LK.LOOKS)):
        x = 30
        for n in ("LeafDeep", "LeafTeal", "LeafMid", "Fern", "Moss", "FernBright", "Grass", "GrassPale", "LeafPale"):
            parts.append('<rect x="%d" y="%d" width="150" height="40" fill="rgb%s"/>' % (x, y + row * 44, table[n][1]))
            x += 150
    P.render_svg(os.path.join(OUT, "colour_swatches.png"), '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="Helvetica Neue, Arial, sans-serif">%s</svg>' % (W, H, "\n".join(parts)), W, H, W)


def pieces():
    import bpy  # noqa: F401
    import jade_lib_blender as B
    import jade_lib_run  # noqa: F401  (for the family modules)
    import importlib
    picks = [("jade_lib_trees", "JG_Tree_Aspire_A1"), ("jade_lib_trees", "JG_Tree_Buttress_B1"), ("jade_lib_trees", "JG_Tree_Mistbough_D1"),
             ("jade_lib_plants", "JG_Plant_Fern_Fountain_F1"), ("jade_lib_plants", "JG_Plant_FlowerBush_C1"), ("jade_lib_bamboo", "JG_Bamboo_Clump_K2")]
    built = {n: importlib.import_module(m).build_all()[n] for m, n in picks}
    rows = []
    for label, table in (("before", LK.LOOKS_PHASE_A), ("after", dict(LK.LOOKS))):
        paths = []
        saved = dict(LK.LOOKS)
        LK.LOOKS.clear()
        LK.LOOKS.update(table)
        for mat in list(B.bpy.data.materials):
            B.bpy.data.materials.remove(mat)
        for m, n in picks:
            B.clear_scene()
            coll = B.new_collection("sw")
            objs = B.piece_objects(built[n], coll)
            B.set_mode(objs, "paint")
            p = os.path.join(OUT, "sw_%s_%s.png" % (label, n))
            B.contact_view(objs, p, res=(420, 420), view="q3")
            paths.append(p)
        LK.LOOKS.clear()
        LK.LOOKS.update(saved)
        rows += paths
    B.stitch(rows, len(picks), os.path.join(OUT, "colour_before_after.png"))
    for p in rows:
        os.remove(p)
    print("wrote", os.path.join(OUT, "colour_before_after.png"))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    if args and args[0] == "swatch":
        swatch()
    else:
        pieces()

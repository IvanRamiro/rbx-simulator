"""jade_lib_lua: writes Jade Grove's Lua data (2026-11-22): the expanded terrain (src/worldbuild/Terrain/JadeGrove.lua) and the library's placements
(src/worldbuild/Placements/JadeGroveLibrary.lua). Plain Python. Run after jade_lib_forest.build() (which sets the terrain pads and trails).

    python3 jade_lib_lua.py            # writes both files, prints the numbers
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_forest as F  # noqa: E402
import jade_lib_island as I  # noqa: E402
import jade_lib_looks as LK  # noqa: E402
import jade_lib_oldmap as O  # noqa: E402
import jade_lib_sites as S  # noqa: E402

REPO = O.REPO
TERRAIN = os.path.join(REPO, "src", "worldbuild", "Terrain", "JadeGrove.lua")
PLACEMENTS = os.path.join(REPO, "src", "worldbuild", "Placements", "JadeGroveLibrary.lua")


def rle(values, off):
    """The terrain modules' run-length strings: values joined by commas, "~N" for N entries of `off`."""
    out, run = [], 0
    for v in values:
        if v == off:
            run += 1
            continue
        if run:
            out.append("~%d" % run if run > 1 else str(off if off is not None else "false"))
            run = 0
        out.append(v)
    if run:
        out.append("~%d" % run if run > 1 else str(off if off is not None else "false"))
    return ",".join(str(x) for x in out)


def write_terrain(path=TERRAIN, grid=None):
    ox, oz, n, heights, mats = grid or I.grid()
    h_tokens = ["false" if h is None else ("%.2f" % h) for h in heights]
    # run-length on the literal token "false"
    out, run = [], 0
    for t in h_tokens:
        if t == "false":
            run += 1
            continue
        if run:
            out.append("~%d" % run)
            run = 0
        out.append(t)
    if run:
        out.append("~%d" % run)
    heights_s = ",".join(out)
    out, run = [], 0
    for m in mats:
        if m == 0:
            run += 1
            continue
        if run:
            out.append("~%d" % run)
            run = 0
        out.append(str(m))
    if run:
        out.append("~%d" % run)
    mats_s = ",".join(out)
    c = I.CENTRE
    text = "\n".join([
        "-- Written by tools/blender/world/jade (jade_lib_lua.py): Jade Grove's expanded ground (2026-11-22). Do not edit by hand.",
        "-- Run-length strings (WorldBuilder expands them): values joined by commas, \"~N\" = N entries of false (heights) or 0 (material indices).",
        "-- The grid is the island's centre +- %d studs on the engine's 4-stud voxel grid; JadeGroveBuilder.buildTerrain writes only the columns that have a height," % I.HALF,
        "-- one by one, so the neighbours' columns in this square (Ember Peak's corner) are never rewritten.",
        "return {",
        '    Island = "JadeGrove",',
        "    Centre = Vector3.new(%g, %g, %g)," % tuple(c),
        "    Turns = 0, -- quarter turns about the centre, each adding 90 degrees of bearing",
        "    Origin = Vector2.new(%g, %g), -- world X/Z of the grid's first corner" % (ox, oz),
        "    Cell = %d," % I.CELL,
        "    Size = %d," % n,
        '    Materials = { %s },' % ", ".join('"%s"' % m for m in I.MATERIALS),
        '    Heights = "%s",' % heights_s,
        '    MaterialIndex = "%s",' % mats_s,
        "}",
        ""])
    with open(path, "w", encoding="utf8") as f:
        f.write(text)
    return len(text), n


def v3(x, y, z):
    return "Vector3.new(%.2f, %.2f, %.2f)" % (x, y, z)


# what stays of the first foundation's kit (arena floor, glade floor, grove gate, hermitage, hollow rim and water, egg pedestals and glow rings: their functions are kept);
# every other template and placement of Placements/JadeGrove.lua is old dress and is replaced (replace means delete)
KEEP = ["JG_ArenaFloor", "JG_GladeFloor", "JG_GroveGate", "JG_Hermitage", "JG_HollowRim", "JG_HollowWater", "JG_EggPedestal", "JG_EggGlowRing"]
REMOVE_TEMPLATES = sorted(k for k in S.read_old_kit() if k not in KEEP)
BORROWED = ["JG_AncientTreeA", "JG_AncientTreeB", "JG_BambooClump", "JG_Fern"]   # CrossingBuilder's JADE list: kept until the Murim track stops borrowing them
REMOVE_ISLAND_PIECES = ["JG_Underside", "JG_UnderCrystals", "JG_MossCurtains", "JG_Vines", "JG_ElderTrunk", "JG_ElderBranches", "JG_ElderPads", "JG_ElderCanopy"]


def write_placements(pl, path=PLACEMENTS):
    L = []
    A = L.append
    A("-- Written by tools/blender/world/jade (jade_lib_lua.py): Jade Grove's library placements (2026-11-22). Do not edit by hand; change the plan in jade_lib_sites.py / jade_lib_forest.py.")
    A("-- Read by JadeGroveBuilder. Island-local studs (x east, z south, y up, the arena's centre at the origin; WorldBuilder.islandFrame carries them into the world).")
    A("-- The kit is the seven FBX files in assets/world/JadeGrove/Library (JG_<Family>_<Name>__<Material>, anchor JL_Anchor) stored by WorldBuilder.storeKit(\"JadeGrove\", import, \"JL_Anchor\").")
    A("-- Every visual piece is CanCollide/CanQuery/CanTouch false with Box fidelity: all walking and bumping is Colliders (invisible Plastic boxes and cylinders, one material).")
    A("return {")
    A('    Island = "JadeGrove",')
    A('    Kit = "JadeGrove",')
    A("    Folders = { \"Terrain\", \"Buildings\", \"Vegetation\", \"Rocks\", \"Props\", \"Paths\" }, -- under Workspace.FloatingIslands.JadeGrove")
    A("    Reach = %d, -- how far the ground runs from the island's centre (WorldConfig.Islands.JadeGrove.Reach should be this or more)" % math.ceil(REACH + 4))
    A("    Place = {")
    for piece in sorted(pl.place):
        A("        %s = { -- %s" % (piece, folder := S.folder_of(piece)))
        for e in pl.place[piece]:
            sc = "" if abs(e["scale"] - 1.0) < 1e-6 else ", Scale = %.3f" % e["scale"]
            A("            { Position = %s, Yaw = %.4f%s, Seed = %d }," % (v3(e["x"], e["y"], e["z"]), e["yaw"], sc, e["seed"]))
        A("        },")
    A("    },")
    A("    Folder = { -- the sub-folder each piece goes to")
    for piece in sorted(pl.place):
        A("        %s = \"%s\"," % (piece, S.folder_of(piece)))
    A("    },")
    A("    Looks = { -- by material suffix: Roblox material, colour and extras (no texture anywhere)")
    for suffix, (mat, col, extra) in LK.LOOKS.items():
        ex = ""
        for k, v in extra.items():
            ex += ", %s = %s" % (k, ("true" if v else "false") if isinstance(v, bool) else v)
        A("        %s = { Material = \"%s\", Color = { %d, %d, %d }%s }," % (suffix, mat, col[0], col[1], col[2], ex))
    A("    },")
    A("    Glow = { \"GlowTeal\", \"GlowAmber\" }, -- the only Neon parts (small accents, never lights)")
    A("    Colliders = { -- invisible Plastic parts: Block, or Cylinder (an upright round post: Size = height, diameter, diameter before the quarter turn)")
    for c in pl.colliders:
        if c["kind"] == "cyl":
            A("        { Folder = \"%s\", Shape = \"Cylinder\", Position = %s, Size = %s, Yaw = %.4f }," % (c["folder"], v3(c["x"], c["y"], c["z"]), v3(c["sy"], c["sx"], c["sz"]), c["yaw"]))
        else:
            A("        { Folder = \"%s\", Shape = \"Block\", Position = %s, Size = %s, Yaw = %.4f }," % (c["folder"], v3(c["x"], c["y"], c["z"]), v3(c["sx"], c["sy"], c["sz"]), c["yaw"]))
    A("    },")
    A("    Lights = { -- at most eight PointLights on the whole island")
    for l in pl.lights:
        A("        { Name = \"%s\", Position = %s, Range = %d, Brightness = %.1f }," % (l["name"], v3(l["x"], l["y"], l["z"]), l["range"], l["brightness"]))
    A("    },")
    A("    LightColor = { 255, 196, 128 }, -- warm, so the forest is not washed green")
    A("    Falls = { -- WorldBuilder.buildWaterfall(parent, lip, from): Drop = how far the water falls (a short fall is shortened after it is built)")
    for f in pl.falls:
        A("        { Name = \"%s\", Lip = %s, From = %s, Drop = %.1f }," % (f["name"], v3(*f["lip"]), v3(*f["frm"]), f["drop"]))
    A("    },")
    A("    Water = {")
    A("        Streams = { -- ribbons of Glass parts between the points (x, y, z of the surface), Width across")
    for s_ in pl.water["streams"]:
        A("            { Name = \"%s\", Width = %.1f, Points = {" % (s_["name"], s_["width"]))
        for p in s_["pts"]:
            A("                %s," % v3(p[0], p[2] if len(p) > 2 else 0.0, p[1]))
        A("            } },")
    A("        },")
    A("        Discs = { -- round pools: a flat Glass cylinder at the surface")
    for d in pl.water["discs"]:
        A("            { Name = \"%s\", Position = %s, Radius = %.1f }," % (d["name"], v3(d["x"], d["y"], d["z"]), d["r"]))
    A("        },")
    A("    },")
    A("    Spots = { -- the hidden places and other marked spots (not signposted in the world)")
    for name, (x, y, z, note) in sorted(pl.spots.items()):
        A("        %s = { Position = %s, Note = \"%s\" }," % (name, v3(x, y, z), note))
    A("    },")
    A("    Bridges = { -- the three forest bridges: both ends of the deck and its level (the terrain is levelled to it at both ends)")
    for name, b in sorted(pl.bridges.items()):
        A("        %s = { A = %s, B = %s, Level = %.2f, Span = %.1f }," % (name, v3(b["A"][0], b["level"], b["A"][1]), v3(b["B"][0], b["level"], b["B"][1]), b["level"], b["span"]))
    A("    },")
    A("    Remove = { -- what the library replaces (replace means delete): the old dress, its templates, the old island meshes")
    A("        Keep = { %s }, -- what stays of the first foundation's kit (Placements/JadeGrove.lua); every other name in its Kit is old dress: its placed copies and templates go" % ", ".join('"%s"' % n for n in KEEP))
    A("        Borrowed = { %s }, -- templates Murim Crossing's first-foundation dress still borrows (CrossingBuilder JADE): kept until that track stops using them" % ", ".join('"%s"' % n for n in BORROWED))
    A("        IslandPieces = { %s }," % ", ".join('"%s"' % n for n in REMOVE_ISLAND_PIECES))
    A("    },")
    A("}")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(L) + "\n")
    return len("\n".join(L))


REACH = 0.0


def main():
    global REACH
    pl = F.build()
    S.I.USE_PADS[0] = True
    grid = I.grid()
    ox, oz, n, heights, mats = grid
    REACH = 0.0
    for j in range(n):
        for i in range(n):
            if heights[j * n + i] is not None:
                x = ox + (i + 0.5) * I.CELL - I.CENTRE[0]
                z = oz + (j + 0.5) * I.CELL - I.CENTRE[2]
                REACH = max(REACH, math.hypot(x, z))
    t = write_terrain(grid=grid)
    p = write_placements(pl)
    cells = sum(1 for h in heights if h is not None)
    print("terrain file bytes", t[0], "grid", t[1], "cells", cells, "area", cells * 16, "ratio", round(cells * 16 / 73664.0, 3), "reach", round(REACH, 1))
    print("placements file chars", p, "placements", sum(len(v) for v in pl.place.values()), "colliders", len(pl.colliders))
    return grid, pl


if __name__ == "__main__":
    main()

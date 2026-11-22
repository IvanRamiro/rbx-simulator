"""Writes src/worldbuild/Placements/MurimDawnspire.lua from dawnspire.build_all() (Dawnspire's territory, 2026-11-22). Plain Python."""
import math
import os

import dawnspire as D
import murim_dawnspire_terrain as T

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PATH = os.path.join(REPO, "src", "worldbuild", "Placements", "MurimDawnspire.lua")

# the Roblox look of each architecture material suffix (no texture anywhere): Material enum name, colour, extras
ARCH_LOOKS = [
    ("Marble", "Marble", (238, 236, 232), ""), ("Granite", "Granite", (176, 176, 184), ""), ("Tile", "Marble", (28, 50, 120), ""),
    ("Gold", "Metal", (255, 172, 48), ""), ("GoldFlat", "SmoothPlastic", (226, 176, 70), ""), ("Azure", "SmoothPlastic", (38, 104, 204), ""),
    ("Plaster", "Plaster", (236, 230, 220), ""), ("Timber", "Wood", (196, 176, 148), ""),
    ("SilkBlue", "Fabric", (28, 62, 170), ", CastShadow = false"), ("SilkWhite", "Fabric", (240, 242, 250), ", CastShadow = false"),
    ("AzureGlow", "Neon", (40, 150, 255), ", CastShadow = false"), ("Pool", "Glass", (110, 190, 230), ", Transparency = 0.5, CastShadow = false"),
    ("Case", "Glass", (225, 240, 250), ", Transparency = 0.72, CastShadow = false"),
]
FOLDER_OF = {   # which of the owner's fixed sub-folders each piece goes in
    "Buildings": "Buildings", "Props": "Props",
}
PATH_COURTS = ("Floor", "Stair", "Bridge", "Landing", "Causeway", "Rail", "RearStair")
GROUND_COVER = ("PetalDrift", "GravelRake", "MossTuft", "SteppingStone")
LIGHT_OFFSET = {"LanternPillar": (0.0, 5.2, 0.0), "LanternLow": (0.0, 2.1, 0.0), "TeaPavilion": (0.0, 5.5, 0.0)}


def v3(p):
    return "Vector3.new(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2])


def folder_for(entry):
    fam, name = entry["family"], entry["name"]
    if fam == "Courts":
        return "Paths" if name.startswith(PATH_COURTS) else "Buildings"
    return FOLDER_OF[fam]


def veg_folder(piece):
    base = piece.split("_", 2)[2]
    if piece.startswith("Dawnspire_Rocks"):
        return "Paths" if base.startswith("SteppingStone") else "Rocks"
    if piece.startswith("Dawnspire_Plants"):
        return "Paths" if base.startswith(GROUND_COVER) else "Vegetation"
    return "Vegetation"


def zones(P):
    """Route zones and checks: pad-frame rectangles (Centre = x, level, z; Size = x, z; Low/High = the ground's levels at the two ends for a slope)."""
    routes, checks = [], []
    for name, t in T.TERRACES.items():
        routes.append(dict(name=name, c=((t["x0"] + t["x1"]) / 2, D.G(t["y"]), (t["z0"] + t["z1"]) / 2), size=(t["x1"] - t["x0"] + 4.0, t["z1"] - t["z0"] + 4.0), low=0.0, high=0.0, yaw=0.0))
    for sname, st in T.STAIRS.items():
        for run in T.stair_runs(sname):
            (ax, az), (bx, bz) = run["a"], run["b"]
            lo, hi = min(run["y0"], run["y1"]), max(run["y0"], run["y1"])
            hw = (T.GORGE if sname == "Rear" else run["half"]) + 4.0
            routes.append(dict(name="%s stair" % sname, c=((ax + bx) / 2, D.G(lo), (az + bz) / 2), size=(2 * hw, run["L"] + 2.0), low=0.0, high=hi - lo, yaw=0.0))
    for bname, b in T.BRIDGES.items():
        (ax, az), (bx, bz) = b["a"], b["b"]
        routes.append(dict(name="Bridge %s" % bname, c=((ax + bx) / 2, D.G(b["y"]), (az + bz) / 2), size=(abs(bx - ax) + 4.0, 12.0), low=0.0, high=b["rise"] + 3.0, yaw=0.0))
    spots = {"Garden": (0.0, 66.0), "Residence": (0.0, 150.0), "Tea": (84.0, -34.0), "Yard": (94.0, 6.0), "Exhibit": (92.0, 62.0)}
    for name, (x, z) in spots.items():
        t = T.TERRACES[name]
        checks.append(dict(name=name, c=((t["x0"] + t["x1"]) / 2, D.G(t["y"]), (t["z0"] + t["z1"]) / 2), size=(t["x1"] - t["x0"] - 8.0, t["z1"] - t["z0"] - 8.0),
                           ret=(x, D.G(t["y"]) + 0.3, z), yaw=math.atan2(-(0.0 - x), -(0.0 - z)) if False else 0.0))
    return routes, checks


def write(P):
    L = []
    A = L.append
    A("-- Written by tools/blender/world/dawnspire_lua.py (Dawnspire's territory, the Orthodox side's extension, 2026-11-22). Do not edit by hand.")
    A("-- Read by DawnspireBuilder. Every position is in the PAD'S FRAME (as MurimOrthodox's): origin at the Orthodox pad's centre (Placements/MurimCrossing.lua")
    A("-- Pads.Orthodox.Centre) lifted by FloorLift, turned by the pad's FrontYaw, so y is the height over the plaza minus 16.5 (the garden's floor mesh is y 9, the")
    A("-- residence's 27, the tea terrace's 0, the yard's 4, the exhibition terrace's 9). Yaw: CFrame.Angles(0, Yaw, 0) in that frame. The architecture is the FBX files")
    A("-- Dawnspire_Buildings / _Courts / _Props (pieces Dawnspire_<Family>_<Piece>__<Material>, anchor DS_Anchor), the vegetation Dawnspire_Trees / _Plants / _Rocks,")
    A("-- all stored by WorldBuilder.storeKit(\"Dawnspire\", import, \"DS_Anchor\"). Every visual piece is CanCollide/CanQuery/CanTouch false with Box fidelity: all walking")
    A("-- and bumping is the Colliders (invisible Plastic boxes, one material so they cost one batch).")
    A("return {")
    A("    Pad = \"Orthodox\",")
    A("    FloorLift = 0.5,")
    A("    Folders = { \"Buildings\", \"Vegetation\", \"Rocks\", \"Props\", \"Paths\" }, -- the owner's fixed sub-folders of Territory")
    by = {}
    for p in P.placements:
        by.setdefault(p["piece"], []).append(p)
    A("    Kit = { -- architecture: piece = { { Position, Yaw, Scale, Role, Folder, Light } }")
    for name in sorted(by):
        A("        %s = {" % name)
        for p in by[name]:
            sc = ""
            if "scale_x" in p:
                sc = ", Scale = Vector3.new(%.4f, 1, 1)" % p["scale_x"]
            extra = (", Light = true" if p.get("light") else "")
            A("            { Position = %s, Yaw = %.4f%s, Role = \"%s\", Folder = \"%s\"%s }," % (v3((p["x"], p["y"], p["z"])), p["yaw"], sc, p["role"], folder_for(p), extra))
        A("        },")
    A("    },")
    A("    Vegetation = { -- the library's own trees, plants and rocks, each at its terrace's ground: piece, position, yaw, scale, folder")
    for v in P.veg:
        A("        { Piece = \"%s\", Position = %s, Yaw = %.3f, Scale = %.2f, Folder = \"%s\" }," % (v["piece"], v3((v["x"], v["y"], v["z"])), v["yaw"], v["scale"], veg_folder(v["piece"])))
    A("    },")
    A("    Looks = { -- by material suffix; Arch for the architecture, Veg for the library (the same name can mean two looks)")
    A("        Arch = {")
    for suffix, material, c, extra in ARCH_LOOKS:
        A("            %s = { Material = \"%s\", Color = { %d, %d, %d }%s }," % (suffix, material, c[0], c[1], c[2], extra))
    A("        },")
    A("        Veg = {")
    for suffix, look in D.veg()["looks"].items():
        ex = ""
        if "Transparency" in look:
            ex += ", Transparency = %g" % look["Transparency"]
        if look.get("CastShadow") is False:
            ex += ", CastShadow = false"
        c = look["Color"]
        A("            %s = { Material = \"%s\", Color = { %d, %d, %d }%s }," % (suffix, look["Material"], c[0], c[1], c[2], ex))
    A("        },")
    A("    },")
    A("    Colliders = { -- invisible boxes: centre, size (and a yaw for a rotated one: the library's trunks and rocks)")
    for c in P.colliders:
        if c.get("rotated"):
            A("        { Name = \"%s\", Position = %s, Size = %s, Yaw = %.4f }," % (c["name"], v3((c["cx"], (c["y0"] + c["y1"]) / 2, c["cz"])), v3((c["sx"], c["y1"] - c["y0"], c["sz"])), c["yaw"]))
        else:
            A("        { Name = \"%s\", Position = %s, Size = %s }," % (c["name"], v3(((c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2, (c["z0"] + c["z1"]) / 2)),
                                                                  v3((c["x1"] - c["x0"], c["y1"] - c["y0"], c["z1"] - c["z0"]))))
    A("    },")
    A("    Spots = { -- marked places: the Master, the Regent's display, the exhibition door, the NPC places (names starting Npc), the garden, the yard")
    for name, m in sorted(P.spots.items()):
        A("        %s = { Position = %s, Yaw = %.4f }, -- %s" % (name, v3(m["pos"]), m["yaw"], m["note"]))
    A("    },")
    A("    Lights = { -- at most six PointLights in the whole territory: position, colour, range, brightness")
    for lt in P.lights:
        A("        { Position = %s, Color = { %d, %d, %d }, Range = %d, Brightness = %.2f, Note = \"%s\" }," % (v3(lt["pos"]), lt["color"][0], lt["color"][1], lt["color"][2], lt["range"], lt["brightness"], lt["note"]))
    A("    },")
    A("    Falls = { -- WorldBuilder.buildWaterfall(parent, lip, from): the lip and the point behind it")
    for f in P.falls:
        A("        { Zone = \"%s\", Lip = %s, From = %s }, -- %s" % (f["zone"], v3(f["lip"]), v3(f["frm"]), f["note"]))
    A("    },")
    routes, checks = zones(P)
    A("    Zones = { -- for Approach.Zones (WorldService's fall return): Route boxes over every walkable terrace, stair and bridge (they reach 100 under the ground), Check boxes with a ReturnTo")
    A("        Routes = {")
    for r in routes:
        A("            { Name = \"%s\", Centre = %s, Size = Vector2.new(%.1f, %.1f), High = %.1f }," % (r["name"], v3(r["c"]), r["size"][0], r["size"][1], r["high"]))
    A("        },")
    A("        Checks = {")
    for c in checks:
        A("            { Name = \"%s\", Centre = %s, Size = Vector2.new(%.1f, %.1f), ReturnTo = %s }," % (c["name"], v3(c["c"]), c["size"][0], c["size"][1], v3(c["ret"])))
    A("        },")
    A("    },")
    A("    Remove = { -- what the first foundation made on the Orthodox side that this territory replaces (replace means delete)")
    A("        Dress = { \"Blossom\" }, -- Workspace.FloatingIslands.MurimCrossing.Dress.Blossom: the Blossom Sanctuary's trees on the Orthodox mountains")
    A("        Hall = { \"Trees\" },    -- OrthodoxPad.Hall.Trees: the Blossom Sanctuary's trees the hall placed")
    A("        Waterfalls = 2,         -- the first two of Dress.Waterfalls (the Orthodox mesas' falls): the Dawnspire falls take their place")
    A("    },")
    A("}")
    with open(PATH, "w") as f:
        f.write("\n".join(L) + "\n")
    return PATH

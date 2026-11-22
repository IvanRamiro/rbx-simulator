"""Writes src/worldbuild/Placements/MurimOrthodox.lua from orthodox_hq.build_all() (Dawnspire Hall, 2026-11-22). Plain Python."""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PATH = os.path.join(REPO, "src", "worldbuild", "Placements", "MurimOrthodox.lua")

# the Roblox look of each material suffix (no texture anywhere): Material enum name, colour, extras
LOOKS = [
    ("Marble", "Marble", (238, 236, 232), ""),
    ("Granite", "Granite", (176, 176, 184), ""),
    ("Tile", "Marble", (28, 50, 120), ""),
    ("Gold", "Metal", (255, 172, 48), ""),
    ("GoldFlat", "SmoothPlastic", (226, 176, 70), ""),
    ("Azure", "SmoothPlastic", (38, 104, 204), ""),
    ("Plaster", "Plaster", (236, 230, 220), ""),
    ("Stone", "Limestone", (196, 186, 170), ""),
    ("SilkBlue", "Fabric", (28, 62, 170), ", CastShadow = false"),
    ("SilkWhite", "Fabric", (240, 242, 250), ", CastShadow = false"),
    ("Crystal", "Glass", (130, 195, 255), ", Transparency = 0.35, CastShadow = false"),
    ("AzureGlow", "Neon", (40, 150, 255), ", CastShadow = false"),
    ("Pool", "Glass", (110, 190, 230), ", Transparency = 0.5, CastShadow = false"),
]


def v3(p):
    return "Vector3.new(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2])


def write(data):
    L = []
    A = L.append
    A("-- Written by tools/blender/world/orthodox_hq_lua.py (Dawnspire Hall, the Orthodox headquarters, 2026-11-22). Do not edit by hand.")
    A("-- Read by OrthodoxBuilder. Every position is in the PAD'S FRAME: origin at the Orthodox pad's centre (Placements/MurimCrossing.lua Pads.Orthodox.Centre)")
    A("-- lifted by FloorLift (the court's floor is 0.5 over the pad's ground), turned by the pad's FrontYaw, so y = 0 is the court's floor and the front (-Z) faces")
    A("-- the plaza. Yaw: CFrame.Angles(0, Yaw, 0) in that frame. The kit is the FBX files in assets/world/MurimCrossing/Orthodox (Orthodox_<Piece>__<Material>,")
    A("-- anchor OH_Anchor), stored by WorldBuilder.storeKit(\"Dawnspire\", import, \"OH_Anchor\"). Every visual piece is CanCollide/CanQuery/CanTouch false with Box")
    A("-- fidelity: all walking and bumping is the Colliders (invisible Plastic boxes, one material so they cost one batch).")
    A("return {")
    A("    Pad = \"Orthodox\",")
    A("    FloorLift = 0.5,")
    A("    Footprint = { XHalf = 58.0, ZFrom = -56.0, ZTo = 42.0 }, -- the trees of the first foundation inside this rectangle are removed")
    A("    Remove = { Stairs = { \"Gate_Orthodox\", \"Flags_Orthodox\" } }, -- parts of the first foundation this hall replaces (CrossingBuilder.buildStairs)")
    A("    Kit = {")
    by = {}
    for p in data["placements"]:
        by.setdefault(p["piece"], []).append(p)
    for name in sorted(by):
        A("        %s = {" % name)
        for p in by[name]:
            extra = ""
            if p.get("light"):
                extra += ", Light = true"
            if p.get("rear"):
                extra += ", Rear = true"
            sc = "" if abs(p["scale"] - 1.0) < 1e-9 else ", Scale = %.3f" % p["scale"]
            A("            { Position = %s, Yaw = %.4f%s, Role = \"%s\"%s }," % (v3((p["x"], p["y"], p["z"])), p["yaw"], sc, p["role"], extra))
        A("        },")
    A("    },")
    A("    Looks = { -- by material suffix")
    for suffix, material, c, extra in LOOKS:
        A("        %s = { Material = \"%s\", Color = { %d, %d, %d }%s }," % (suffix, material, c[0], c[1], c[2], extra))
    A("    },")
    A("    Colliders = { -- invisible boxes: centre and size")
    for c in data["colliders"]:
        cx, cy, cz = (c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2, (c["z0"] + c["z1"]) / 2
        A("        { Name = \"%s\", Position = %s, Size = %s }," % (c["name"], v3((cx, cy, cz)), v3((c["x1"] - c["x0"], c["y1"] - c["y0"], c["z1"] - c["z0"]))))
    A("    },")
    A("    Spots = { -- marked places (later phases read them)")
    for name, m in sorted(data["marks"].items()):
        A("        %s = { Position = %s, Yaw = %.4f }, -- %s" % (name, v3(m["pos"]), m["yaw"], m["note"]))
    A("    },")
    A("    Lights = { Color = { 120, 200, 255 }, Range = 22, Brightness = 0.9 }, -- the lanterns marked Light = true carry one PointLight each (4 in the whole hall)")
    A("    Falls = { -- WorldBuilder.buildWaterfall(parent, lip, from): the lip and the point behind it")
    for f in data["falls"]:
        A("        { Zone = \"%s\", Lip = %s, From = %s }," % (f["zone"], v3(f["lip"]), v3(f["frm"])))
    A("    },")
    A("    Trees = { -- the Blossom Sanctuary's trees (WorldAssets.BlossomSanctuaryAssets), position and yaw")
    for i, t in enumerate(data["trees"]):
        A("        { Position = %s, Yaw = %.3f, Scale = %.2f }," % (v3(t), (i * 1.9) % 6.28, 1.15 + 0.1 * (i % 3)))
    A("    },")
    A("    Glow = { Spire = \"Orthodox_Spire__AzureGlow\", Lantern = \"Orthodox_Lantern__AzureGlow\" }, -- the only Neon pieces")
    A("}")
    with open(PATH, "w") as f:
        f.write("\n".join(L) + "\n")
    return PATH

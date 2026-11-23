"""Writes src/worldbuild/Placements/MurimNightfall.lua from nightfall.build_all() (Nightfall Citadel, the Demonic territory, 2026-11-23). Plain Python.

    python3 tools/blender/world/nightfall_lua.py [out-path]      # without a path: renders/nightfall/scratch/MurimNightfall.lua (a scratch copy; the tree's file is copied in one step by hand)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import nightfall as D  # noqa: E402
import murim_nightfall_terrain as T  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRATCH = os.path.join(REPO, "renders", "nightfall", "scratch", "MurimNightfall.lua")
TREE = os.path.join(REPO, "src", "worldbuild", "Placements", "MurimNightfall.lua")

PATH_COURTS = ("Flight", "Landing", "Top", "Bridge", "Chain", "Parapet", "Curtain")
GROUND_COVER = ("Ash", "Moss", "Lichen", "Drift", "Litter")
WALKABLE = ("Rocks_Steps", "Rocks_Slab", "Rocks_Path", "Rocks_Cobble")


def v3(p):
    return "Vector3.new(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2])


def folder_for(entry):
    fam, name = entry["family"], entry["name"]
    if fam == "Courts":
        return "Paths" if name.startswith(PATH_COURTS) else "Buildings"
    if entry["name"] == "UpperGate":
        return "Paths"
    return {"Buildings": "Buildings", "Props": "Props"}[fam]


def veg_folder(piece, given):
    base = piece.split("_", 2)[2]
    if piece.startswith("Nightfall_Rocks"):
        return "Paths" if base.startswith(("Steps", "Slab", "Path", "Cobble")) else "Rocks"
    if piece.startswith("Nightfall_Plants"):
        return "Paths" if base.startswith(GROUND_COVER) else "Vegetation"
    return "Vegetation"


def zones(P):
    """Route zones and checks: pad-frame rectangles (Centre = x, level, z; Size = x, z; High = the rise above Centre's level for a slope; Yaw for a turned one). The foundation's own pad
    squares already cover the lower ward up to 8 over the pad's ground; everything higher is here, and every Route reaches 100 studs under its ground (Approach.Zones)."""
    routes, checks = [], []
    for name, t in T.TERRACES.items():
        routes.append(dict(name=name, c=((t["x0"] + t["x1"]) / 2, D.G(t["y"]), (t["z0"] + t["z1"]) / 2), size=(t["x1"] - t["x0"] + 7.0, t["z1"] - t["z0"] + 7.0), high=0.0, yaw=0.0))
    stairs = (("Great", D.STAIR_X, 14.0 + 4.0, ((11.0, 29.0, D.GR, 12.0), (29.0, 35.0, D.G(28.0), 0.0), (35.0, 53.0, D.G(28.0), 12.0))),
              ("Postern", D.POSTERN_X, 5.0 + 2.2, ((13.0, 31.0, D.GR, 12.0), (31.0, 35.0, D.G(28.0), 0.0), (35.0, 53.0, D.G(28.0), 12.0))),
              ("Bridgehead", D.BH_X, 6.0 + 2.0, ((75.0, 87.0, D.GU, 8.0),)))
    for nm, x, w, runs in stairs:
        for (z0, z1, y, hi) in runs:
            routes.append(dict(name="%s stair" % nm, c=(x, y, (z0 + z1) / 2), size=(w + 8.0, z1 - z0 + 2.0), high=hi, yaw=0.0))
    routes.append(dict(name="Upper Gate", c=(D.STAIR_X, D.GU, 55.0), size=(22.0, 8.0), high=0.0, yaw=0.0))
    routes.append(dict(name="Postern top", c=(D.POSTERN_X, D.GU, 55.0), size=(10.0, 8.0), high=0.0, yaw=0.0))
    for p in P.placements:
        if p["name"] == "ChainBridge":
            pc = P.pieces[p["piece"]]
            (lx, ly, lz), (hx, hy, hz) = pc.bounds()
            routes.append(dict(name="Chain bridge", c=(p["x"], p["y"] - 3.0, p["z"]), size=(hx - lx + 4.0, 12.0), high=6.0, yaw=0.0))
    checks.append(dict(name="Lower Ward", c=(0.0, D.GR, -20.0), size=(30.0, 24.0), ret=(0.0, -0.2, -22.0)))
    checks.append(dict(name="Upper Ward", c=(-2.0, D.GU, 70.0), size=(34.0, 24.0), ret=(-4.0, D.GU + 0.3, 70.0)))
    checks.append(dict(name="Bridgehead", c=(18.0, D.GB, 99.0), size=(10.0, 12.0), ret=(18.0, D.GB + 0.3, 98.0)))
    checks.append(dict(name="Residence", c=(52.0, D.GB, 101.0), size=(12.0, 12.0), ret=(48.0, D.GB + 0.3, 101.0)))
    return routes, checks


def write(P, path=None):
    path = path or SCRATCH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L = []
    A = L.append
    A("-- Written by tools/blender/world/nightfall_lua.py (Nightfall Citadel, the Demonic territory, 2026-11-23). Do not edit by hand.")
    A("-- Read by NightfallBuilder. Every position is in the PAD'S FRAME (as MurimDawnspire's and MurimWindrift's, for the Demonic pad): origin at the pad's centre (Placements/MurimCrossing.lua")
    A("-- Pads.Demonic.Centre, island-local x -126.83, z 162.33) lifted by FloorLift, turned by the pad's FrontYaw (-0.6632: +z up the mountain, +x across the stairway), so y is the height over the")
    A("-- plaza minus 16.5 (the pad's own ground is y -0.5, the Upper Ward's 23.5, the bridgehead's and the Residence ledge's 29.5; a floor mesh lies 0.5 over its ground). Yaw: CFrame.Angles(0, Yaw, 0)")
    A("-- in that frame. The architecture is the FBX files Nightfall_Buildings / _Courts / _Props (pieces Nightfall_<Family>_<Piece>__<Material>, anchor NF_Anchor), the vegetation Nightfall_Trees /")
    A("-- _Plants / _Rocks, all stored by WorldBuilder.storeKit(\"Nightfall\", import, \"NF_Anchor\"). Every visual piece is CanCollide/CanQuery/CanTouch false with Box fidelity except the Walkable")
    A("-- ones (flat path slabs, which collide as boxes): all other walking and bumping is the Colliders (invisible Plastic boxes, one material so they cost one batch).")
    A("return {")
    A("    Pad = \"Demonic\",")
    A("    FloorLift = 0.5,")
    A("    Folders = { \"Buildings\", \"Vegetation\", \"Rocks\", \"Props\", \"Paths\" }, -- the owner's fixed sub-folders of Territory")
    by = {}
    for p in P.placements:
        by.setdefault(p["piece"], []).append(p)
    A("    Kit = { -- architecture: piece = { { Position, Yaw, Scale, Role, Folder, Light } }")
    for name in sorted(by):
        A("        %s = {" % name)
        for p in by[name]:
            extra = (", Light = true" if p.get("light") else "")
            A("            { Position = %s, Yaw = %.4f, Scale = 1, Role = \"%s\", Folder = \"%s\"%s }," % (v3((p["x"], p["y"], p["z"])), p["yaw"], p["role"], folder_for(p), extra))
        A("        },")
    A("    },")
    A("    Vegetation = { -- the library's own trees, plants and rocks, each at its ground: piece, position, yaw, scale, folder (Walkable: the mesh itself collides)")
    for v in P.veg:
        walk = ", Walkable = true" if v["piece"].startswith(WALKABLE) else ""
        A("        { Piece = \"%s\", Position = %s, Yaw = %.3f, Scale = %.2f, Folder = \"%s\"%s }," % (v["piece"], v3((v["x"], v["y"], v["z"])), v["yaw"], v["scale"], veg_folder(v["piece"], v["folder"]), walk))
    A("    },")
    A("    Looks = { -- by material suffix; Arch for the architecture, Veg for the library (the same name can mean two looks)")
    A("        Arch = {")
    for suffix, look in D.ARCH_LOOKS.items():
        ex = ""
        if "Transparency" in look:
            ex += ", Transparency = %g" % look["Transparency"]
        if look.get("CastShadow") is False:
            ex += ", CastShadow = false"
        c = look["Color"]
        A("            %s = { Material = \"%s\", Color = { %d, %d, %d }%s }," % (suffix, look["Material"], c[0], c[1], c[2], ex))
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
    A("    Colliders = { -- invisible boxes: centre, size (and a yaw for a turned one)")
    for c in P.colliders:
        if c.get("rotated"):
            A("        { Name = \"%s\", Position = %s, Size = %s, Yaw = %.4f }," % (c["name"], v3((c["cx"], (c["y0"] + c["y1"]) / 2, c["cz"])), v3((c["sx"], c["y1"] - c["y0"], c["sz"])), c["yaw"]))
        else:
            A("        { Name = \"%s\", Position = %s, Size = %s }," % (c["name"], v3(((c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2, (c["z0"] + c["z1"]) / 2)),
                                                                  v3((c["x1"] - c["x0"], c["y1"] - c["y0"], c["z1"] - c["z0"]))))
    A("    },")
    A("    Spots = { -- marked places: TalonDisplay (the Nightfall Talon), Vault, LordSpot, HqDoor, HqInside, GateCourt, ArenaCentre, ArenaDummy1..8, TrainingRing, Npc1..10 and the stairs' and bridge's ends")
    for name, m in sorted(P.spots.items()):
        A("        %s = { Position = %s, Yaw = %.4f }, -- %s" % (name, v3(m["pos"]), m["yaw"], m["note"]))
    A("    },")
    A("    Lights = { -- at most eight PointLights in the whole territory: position, colour, range, brightness")
    for lt in P.lights:
        A("        { Position = %s, Color = { %d, %d, %d }, Range = %d, Brightness = %.2f, Note = \"%s\" }," % (v3(lt["pos"]), lt["color"][0], lt["color"][1], lt["color"][2], lt["range"], lt["brightness"], lt["note"]))
    A("    },")
    A("    Effects = { -- at most twelve ParticleEmitters in the whole territory, each Rate at most 6, no scripts (NightfallBuilder.buildEffects): Kind = Flame | Embers | Ash; Rate; Position")
    for e in P.effects:
        A("        { Kind = \"%s\", Rate = %d, Position = %s, Note = \"%s\" }," % (e["kind"], e.get("rate", 5), v3(e["pos"]), e["note"]))
    A("    },")
    routes, checks = zones(P)
    A("    Zones = { -- for Approach.Zones (WorldService's fall return): Route boxes over every walkable ledge, stair and bridge (they reach 100 under the ground), Check boxes with a ReturnTo")
    A("        Routes = {")
    for r in routes:
        A("            { Name = \"%s\", Centre = %s, Size = Vector2.new(%.1f, %.1f), High = %.1f, Yaw = %.4f }," % (r["name"], v3(r["c"]), r["size"][0], r["size"][1], r["high"], r["yaw"]))
    A("        },")
    A("        Checks = {")
    for c in checks:
        A("            { Name = \"%s\", Centre = %s, Size = Vector2.new(%.1f, %.1f), ReturnTo = %s }," % (c["name"], v3(c["c"]), c["size"][0], c["size"][1], v3(c["ret"])))
    A("        },")
    A("    },")
    A("    Remove = { -- what the first foundation made on the Demonic side that this territory replaces (replace means delete)")
    A("        Dress = { \"Basalt\" }, -- Workspace.FloatingIslands.MurimCrossing.Dress.Basalt: the Ember Peak's basalt clusters and shards on the Demonic mountains")
    A("    },")
    A("}")
    tmp = path + ".part"
    with open(tmp, "w") as f:
        f.write("\n".join(L) + "\n")
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    print(write(D.build_all(), sys.argv[1] if len(sys.argv) > 1 else None))

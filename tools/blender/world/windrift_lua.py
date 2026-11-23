"""Writes src/worldbuild/Placements/MurimWindrift.lua from windrift.build_all() (Windrift Hold, the Unorthodox territory, 2026-11-23). Plain Python."""
import math
import os

import windrift as D
import murim_windrift_terrain as T

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PATH = os.path.join(REPO, "src", "worldbuild", "Placements", "MurimWindrift.lua")

PATH_COURTS = ("Bridge", "Gorge", "Great", "Stair", "Cleft", "Flight", "Landing", "RimRail")
GROUND_COVER = ("LichenA", "LichenB", "Stonecrop")
WALKABLE = ("Rocks_StepsA", "Rocks_StepsB", "Rocks_Cobble", "Rocks_PlankWalk")


def v3(p):
    return "Vector3.new(%.3f, %.3f, %.3f)" % (p[0], p[1], p[2])


def folder_for(entry):
    fam, name = entry["family"], entry["name"]
    if fam == "Courts":
        return "Paths" if name.startswith(PATH_COURTS) else "Buildings"
    return {"Buildings": "Buildings", "Props": "Props"}[fam]


def veg_folder(piece, given):
    base = piece.split("_", 2)[2]
    if piece.startswith("Windrift_Rocks"):
        return "Paths" if base.startswith(("Steps", "Cobble", "PlankWalk")) else "Rocks"
    if piece.startswith("Windrift_Plants"):
        return "Paths" if base.startswith(GROUND_COVER) else "Vegetation"
    return "Vegetation"


def zones(P):
    """Route zones and checks: pad-frame rectangles (Centre = x, level, z; Size = x, z; High = the rise above Centre's level for a slope; Yaw for a diagonal flight)."""
    routes, checks = [], []
    for name, t in T.TERRACES.items():
        routes.append(dict(name=name, c=((t["x0"] + t["x1"]) / 2, D.G(t["y"]), (t["z0"] + t["z1"]) / 2), size=(t["x1"] - t["x0"] + 7.0, t["z1"] - t["z0"] + 7.0), high=0.0, yaw=0.0))
    for sname, st in T.STAIRS.items():
        for run in T.stair_runs(sname):
            (ax, az), (bx, bz) = run["a"], run["b"]
            lo, hi = min(run["y0"], run["y1"]), max(run["y0"], run["y1"])
            routes.append(dict(name="%s stair" % sname, c=((ax + bx) / 2, D.G(lo), (az + bz) / 2), size=(2 * (run["half"] + 4.0), run["L"] + 2.0), high=hi - lo,
                               yaw=D.run_yaw(run["a"], run["b"])))
    for p in P.placements:
        if p["name"] in ("GorgeBridge", "GreatSpan"):
            pc = P.pieces[p["piece"]]
            (lx, ly, lz), (hx, hy, hz) = pc.bounds()
            L = hx - lx
            drop = 6.0 if p["name"] == "GreatSpan" else 0.0
            routes.append(dict(name=p["name"], c=(p["x"], p["y"] - drop - 3.0, p["z"]), size=(L + 4.0, 12.0), high=drop + 6.0, yaw=0.0))
    # the Cleft stair, hanging in the gorge (axis-aligned: along +z from x 3, z 27, down 12)
    routes.append(dict(name="Cleft stair", c=(4.8, D.G(T.Y_DRIP), 36.5), size=(8.0, 22.0), high=12.0, yaw=0.0))
    checks.append(dict(name="Forecourt", c=(0.0, 0.0, -20.0), size=(30.0, 24.0), ret=(0.0, -0.2, -18.0)))
    checks.append(dict(name="Eyrie", c=((T.TERRACES["Eyrie"]["x0"] + T.TERRACES["Eyrie"]["x1"]) / 2, D.G(T.Y_EYRIE), 69.0), size=(14.0, 8.0), ret=(-27.5, D.Fl(T.Y_EYRIE) + 0.3, 66.0)))
    checks.append(dict(name="Perch", c=(27.5, D.G(T.Y_PERCH), 68.5), size=(8.0, 8.0), ret=(27.5, D.Fl(T.Y_PERCH) + 0.3, 68.5)))
    checks.append(dict(name="Drip ledge", c=(7.0, D.G(T.Y_DRIP), 49.0), size=(5.0, 6.0), ret=(7.2, D.G(T.Y_DRIP) + 0.3, 47.2)))
    checks.append(dict(name="Rain Hall", c=(9.5, 1.5, 52.0), size=(24.0, 10.0), ret=(1.0, -0.2, 41.5)))
    return routes, checks


def write(P):
    L = []
    A = L.append
    A("-- Written by tools/blender/world/windrift_lua.py (Windrift Hold, the Unorthodox territory, 2026-11-23). Do not edit by hand.")
    A("-- Read by WindriftBuilder. Every position is in the PAD'S FRAME (as MurimDawnspire's, for the Unorthodox pad): origin at the pad's centre (Placements/MurimCrossing.lua")
    A("-- Pads.Unorthodox.Centre, island-local x 0, z 250) lifted by FloorLift, turned by the pad's FrontYaw (0), so y is the height over the plaza minus 36.5 (the pad's own")
    A("-- floor mesh level is y 0, the Eyrie's 21.5, the Perch's 15.5, the Drip ledge's -12.5). Yaw: CFrame.Angles(0, Yaw, 0) in that frame. The architecture is the FBX files")
    A("-- Windrift_Buildings / _Courts / _Props (pieces Windrift_<Family>_<Piece>__<Material>, anchor WR_Anchor), the vegetation Windrift_Trees / _Plants / _Rocks, all stored by")
    A("-- WorldBuilder.storeKit(\"Windrift\", import, \"WR_Anchor\"). Every visual piece is CanCollide/CanQuery/CanTouch false with Box fidelity except the Walkable ones (the path")
    A("-- slabs, which are flat and collide as boxes): all other walking and bumping is the Colliders (invisible Plastic boxes, one material so they cost one batch).")
    A("return {")
    A("    Pad = \"Unorthodox\",")
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
    A("    Spots = { -- marked places: SaberDisplay (the Crosscurrent Saber), ElderSpot, the NPC places (names starting Npc), the doors, the ledges")
    for name, m in sorted(P.spots.items()):
        A("        %s = { Position = %s, Yaw = %.4f }, -- %s" % (name, v3(m["pos"]), m["yaw"], m["note"]))
    A("    },")
    A("    Lights = { -- at most eight PointLights in the whole territory: position, colour, range, brightness")
    for lt in P.lights:
        A("        { Position = %s, Color = { %d, %d, %d }, Range = %d, Brightness = %.2f, Note = \"%s\" }," % (v3(lt["pos"]), lt["color"][0], lt["color"][1], lt["color"][2], lt["range"], lt["brightness"], lt["note"]))
    A("    },")
    A("    Falls = { -- WorldBuilder.buildWaterfall(parent, lip, from, look, { Drop, Scale, Curtains, Splash })")
    for f in P.falls:
        A("        { Zone = \"%s\", Lip = %s, From = %s, Drop = %g, Scale = %g, Curtains = %d, Splash = %s }, -- %s" % (f["zone"], v3(f["lip"]), v3(f["frm"]), f["drop"], f["scale"], f["curtains"], "true" if f["splash"] else "false", f["note"]))
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
    A("    Remove = { -- what the first foundation made on the Unorthodox side that this territory replaces (replace means delete)")
    A("        Dress = { \"Forest\" }, -- Workspace.FloatingIslands.MurimCrossing.Dress.Forest: the Jade Grove's trees on the Unorthodox mountains")
    A("        Waterfalls = true,      -- the Dress.Waterfalls holder behind the Unorthodox pad (the old mesa fall): the Great Falls take its place")
    A("    },")
    A("}")
    with open(PATH, "w") as f:
        f.write("\n".join(L) + "\n")
    return PATH


if __name__ == "__main__":
    print(write(D.build_all()))

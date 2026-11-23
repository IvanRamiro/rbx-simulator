"""jade_lib_forest: the finished plan (2026-11-22): sites from jade_lib_sites, then the replacements at the old dress's positions, the stepping-slab ways to the hidden places,
the lanterns and their eight lights, and the forest, bamboo, rocks and ground life scattered with exclusions (nothing on a path, in the water, on a steep bank, in a
structure's footprint, in the arena, near the rim). Deterministic. `build()` returns the Plan with the terrain pads applied (jade_lib_island.PADS)."""
import math
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_island as I  # noqa: E402
import jade_lib_sites as S  # noqa: E402

TAU = 2 * math.pi
OLD = I.OLD
PHASE_A = "484e202"      # the commit that holds phase A's placements: the polish pass keeps every scatter piece that is still valid on the new ground where it was (the forest the owner liked), and only tops up


def phase_a_scatter():
    """{piece: [(x, z, yaw, scale, seed)]} read from phase A's Placements/JadeGroveLibrary.lua (git), in its own order."""
    try:
        text = subprocess.run(["git", "-C", I.O.REPO, "show", "%s:src/worldbuild/Placements/JadeGroveLibrary.lua" % PHASE_A], capture_output=True, text=True, check=True).stdout
    except Exception:
        return {}
    out = {}
    head = text.index("    Place = {")
    tail = text.index("    Folder = {")
    for m in re.finditer(r"        (JG_\w+) = \{ -- \w+\n(.*?)\n        \},", text[head:tail], re.S):
        lst = []
        for e in re.finditer(r"Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), Yaw = ([-\d.]+)(?:, Scale = ([-\d.]+))?, Seed = (\d+)", m.group(2)):
            x, y, z, yaw, sc, seed = e.groups()
            lst.append((float(x), float(z), float(yaw), float(sc) if sc else 1.0, int(seed)))
        out[m.group(1)] = lst
    return out

COUNTS = {   # piece -> how many (the scatter's budget, see the note's table)
    "JG_Tree_Aspire_A1": 4, "JG_Tree_Aspire_A2": 3, "JG_Tree_Buttress_B1": 3, "JG_Tree_Buttress_B2": 2, "JG_Tree_Spiral_C1": 4, "JG_Tree_Spiral_C2": 3,
    "JG_Tree_Mistbough_D1": 5, "JG_Tree_Mistbough_D2": 4, "JG_Tree_Veil_F1": 3,
    "JG_Bamboo_Grove_G1": 4, "JG_Bamboo_Grove_G2": 4, "JG_Bamboo_Clump_K1": 4, "JG_Bamboo_Clump_K2": 5, "JG_Bamboo_Shoots_S1": 4,
    "JG_Rock_MossBoulders_B1": 5, "JG_Rock_MossBoulders_B2": 5, "JG_Rock_LeaningSlab_L1": 3, "JG_Rock_LeaningSlab_L2": 3, "JG_Rock_SplitStone_S1": 3, "JG_Rock_TerraceStep_T1": 2,
    "JG_Rock_JadeVein_J1": 3,
    "JG_Plant_Fern_Fountain_F1": 10, "JG_Plant_Fern_Crown_F2": 7, "JG_Plant_BroadLeaf_L1": 9, "JG_Plant_FlowerBush_C1": 5, "JG_Plant_Orchid_O1": 5,
    "JG_Plant_Grass_G1": 9, "JG_Plant_Grass_G2": 5, "JG_Mush_Parasol_M1": 6, "JG_Mush_Shelf_M2": 3, "JG_Mush_Cluster_M3": 6, "JG_Mush_Funnel_M4": 4,
    "JG_Moss_Mat_M1": 10, "JG_Moss_Mat_M2": 8, "JG_Log_Fallen_L1": 5, "JG_Log_Stump_S1": 5,
}
BIG = {"JG_Tree_Aspire_A1", "JG_Tree_Aspire_A2", "JG_Tree_Buttress_B1", "JG_Tree_Buttress_B2", "JG_Tree_Spiral_C1", "JG_Tree_Spiral_C2", "JG_Tree_Mistbough_D1",
       "JG_Tree_Mistbough_D2", "JG_Tree_Veil_F1", "JG_Bamboo_Grove_G1", "JG_Bamboo_Grove_G2", "JG_Bamboo_Clump_K1", "JG_Bamboo_Clump_K2"}
RADIUS = {"Tree_Aspire": 6.0, "Tree_Buttress": 11.0, "Tree_Spiral": 5.0, "Tree_Mistbough": 4.5, "Tree_Veil": 7.5, "Bamboo_Grove": 6.0, "Bamboo_Clump": 4.0, "Bamboo_Shoots": 3.0,
          "Rock_MossBoulders": 5.0, "Rock_LeaningSlab": 5.0, "Rock_SplitStone": 6.0, "Rock_TerraceStep": 9.0, "Rock_JadeVein": 4.5, "Log_Fallen": 4.5, "Log_Stump": 2.2}


def radius_of(piece):
    key = "_".join(piece.split("_")[1:3])
    return RADIUS.get(key, 1.6)


def tidy(pl):
    pl.paths = {}


def build():
    pl, pads, root_west, rope_ends = S.plan()
    rnd = random.Random(77)
    P = S.pieces()
    # ---------------------------------------------------------------- visible trails and hidden ways
    pool = I.POND
    shore_e = (I.POND[0] + 0.82 * (I.POND[2] + 1.0), I.POND[1] + 0.58 * (I.POND[2] + 1.0))      # the pond's east-south-east shore: where the visible trail ends
    trails = {
        "FallsTrail": [(-58.0, -76.0), (-63.0, -84.0), (shore_e[0] + 1.0, shore_e[1] - 2.0)],
        "GorgeTrail": [(-118.0, 56.0), (-136.0, 44.0), (-150.0, 28.0)],
        "RampTrail": list(I.RAMP),       # the long ramp up Mistfall Heights is a visible worn trail (the way is not hidden: it is the road up to the lookout)
    }
    tot = I.poly_nearest(0, 0, I.STREAM)[2]
    logc, _ = I.point_at(I.STREAM, 0.52 * tot)
    I.TRAILS[:] = list(trails.values())
    hidden = {
        "Glen": [(0.0, -80.0), (-4.0, -108.0), (-12.0, -138.0), (-14.0, -166.0)],
        "Grotto": [(-60.0, -80.0), (shore_e[0], shore_e[1] - 3.0), (I.POND[0] + 4.0, I.POND[1] + 4.0), (I.POND[0] - 8.0, I.POND[1] - 3.0), (I.FALLS_FOOT[0] + 4.0, I.FALLS_FOOT[1] + 2.0)],
        "Circle": [(root_west[0], root_west[1]), (root_west[0] - 12.0, root_west[1] + 4.0), (I.STONE_CIRCLE[0] + 14.0, I.STONE_CIRCLE[1] + 6.0), (I.STONE_CIRCLE[0] + 13.0, I.STONE_CIRCLE[1] + 2.0)],
        "Pavilion": [(-48.0, 114.0), (-70.0, 118.0), (rope_ends[0][0], rope_ends[0][1]), ],
    }
    pl.paths.update({"Trails": trails, "Hidden": hidden})
    # beyond the rope bridge's far end, the slabs go on to the pavilion
    hidden["PavilionFar"] = [(rope_ends[1][0], rope_ends[1][1]), (-92.0, 158.0)]

    # ---------------------------------------------------------------- terrain pads and trails become final: from here ground() includes them
    I.PADS[:] = [(x, z, r, lv, 7.0) for (x, z, r, lv) in pads]
    I.USE_PADS[0] = True

    # re-seat the placements that were put on the unpadded ground
    for piece, lst in pl.place.items():
        for e in lst:
            pass

    # ---------------------------------------------------------------- replacements at the old dress's positions
    old = S.read_old_kit()
    for k, (x, y, z, yaw) in enumerate(old["JG_StandingStone"]):
        pl.add("JG_Rock_StandingSlab_L3", x, z, yaw + math.pi / 2, 1.0)
    for k, (x, y, z, yaw) in enumerate(old["JG_RuinPillar"]):
        pl.add("JG_Ruin_Column_C2" if k % 5 == 3 else "JG_Ruin_Column_C1", x, z, yaw, 1.0)
    hollow_stones = sorted(k for k in old if k.endswith("Stone") and k != "JG_StandingStone")   # the three carved stones round the Hollow
    for (x, y, z, yaw) in old[hollow_stones[0]]:
        pl.add("JG_Waymarker_W2", x, z, yaw, 1.0)
    for k, (x, y, z, yaw) in enumerate(old["JG_JadeOutcrop"]):
        pl.add(["JG_Rock_MossBoulders_B1", "JG_Rock_MossBoulders_B2", "JG_Rock_JadeVein_J1"][k % 3], x, z, yaw, 0.9)
    lanterns = old["JG_JadeLantern"]
    for k, (x, y, z, yaw) in enumerate(lanterns):
        tall = k >= 13
        pl.add("JG_Lantern_Sprout_L1" if tall else "JG_Lantern_Sprout_L2", x, z, yaw, 1.0)
    # at most eight PointLights on the island: the gate pair, one each at the glade, the hermitage, the guardian tree's hollow, the grotto, the east shrine, the pavilion
    gate_l = [lanterns[13], lanterns[14]]
    for k, (x, y, z, yaw) in enumerate(gate_l):
        pl.lights.append({"name": "GateLantern%d" % (k + 1), "x": x, "y": I.ground(x, z) + 3.6, "z": z, "range": 18, "brightness": 1.0})
    glade_l = lanterns[5]
    pl.lights.append({"name": "GladeLantern", "x": glade_l[0], "y": I.ground(glade_l[0], glade_l[2]) + 2.6, "z": glade_l[2], "range": 16, "brightness": 0.9})
    herm_l = lanterns[7]
    pl.lights.append({"name": "HermitageLantern", "x": herm_l[0], "y": I.ground(herm_l[0], herm_l[2]) + 2.6, "z": herm_l[2], "range": 16, "brightness": 0.9})
    ox, oy, oz = S.jade_lib_guardian.ORIGIN
    pl.lights.append({"name": "GuardianHollow", "x": ox - 3.0, "y": oy + 2.4, "z": oz, "range": 14, "brightness": 0.8})
    gl = pl.spots["SpiritGrotto"]
    pl.lights.append({"name": "GrottoGlow", "x": gl[0], "y": gl[1] + 3.2, "z": gl[2], "range": 20, "brightness": 0.9})
    es = pl.spots["EastShrine"]
    pl.lights.append({"name": "EastShrine", "x": es[0], "y": es[1] + 3.6, "z": es[2], "range": 16, "brightness": 0.9})
    pv = pl.spots["PavilionRuin"]
    pl.lights.append({"name": "PavilionRuin", "x": pv[0], "y": pv[1] + 4.0, "z": pv[2], "range": 16, "brightness": 0.8})
    # new lanterns that only mark something: the east shrine and the old grove hall (a pair each), the grotto ledge, the valley gate
    for name, (x, z, f) in (("East", (es[0], es[2], S.yaw_front(-es[0], -es[2]))),):
        for sx in (-1, 1):
            lx = x + math.cos(f) * sx * 5.2 - math.sin(f) * (-5.0)
            lz = z - math.sin(f) * sx * 5.2 + math.cos(f) * (-5.0)
            pl.add("JG_Lantern_Sprout_L2", lx, lz, f, 1.0)
    # offering tables, gates, waymarkers
    pl.add("JG_Offering_Table_O1", es[0] + math.cos(S.yaw_front(-es[0], -es[2])) * 0 + 0.0, es[2] - 9.0 * 0 + 8.0, S.yaw_front(-es[0], -es[2]), 1.0)
    gx, gz = root_west[0] - 6.0, root_west[1] + 2.0
    pl.add("JG_Gate_Branch_G1", I.STONE_CIRCLE[0] + 26.0, I.STONE_CIRCLE[1] + 10.0, math.atan2(1.0, 0.5), 1.0)
    for (x, z) in ((-70.0, -74.0), (I.POND[0] + 25.0, I.POND[1] + 4.0), (-122.0, 52.0), (root_west[0] + 22.0, root_west[1] + 3.0)):
        pl.add("JG_Waymarker_W1" if (x, z) != (-122.0, 52.0) else "JG_Waymarker_W3", x, z, rnd.uniform(0, TAU), 1.0)
    # ---------------------------------------------------------------- stepping slabs along the hidden ways
    for name, line in hidden.items():
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line, line[1:]))
        s_ = 2.0
        k = 0
        while s_ < total - 1.5:
            p, d = I.point_at(line, s_)
            side = rnd.uniform(-0.9, 0.9)
            x, z = p[0] - d[1] * side, p[1] + d[0] * side
            g = I.ground(x, z)
            if g is not None and g > -2.0:
                in_pond = math.hypot(x - I.POND[0], z - I.POND[1]) < I.POND[2]
                pl.add("JG_Path_Slab_P%d" % (1 + k % 3), x, z, math.atan2(d[0], d[1]) + rnd.uniform(-0.5, 0.5), 1.0, y=(I.POND_WATER + 0.03) if in_pond else g - 0.05)
            s_ += rnd.uniform(3.6, 5.2)
            k += 1
    # two bamboo arches over hidden ways, a natural stone arch at the glen's way in
    ap, ad = I.point_at(hidden["Glen"], 48.0)
    pl.add("JG_Rock_Arch_A1", ap[0], ap[1], math.atan2(ad[0], ad[1]) + math.pi / 2, 1.0)
    ap, ad = I.point_at(hidden["Circle"], 9.0)
    pl.add("JG_Bamboo_Arch_H1", ap[0], ap[1], math.atan2(ad[0], ad[1]), 1.0)
    ap, ad = I.point_at(hidden["Pavilion"], 40.0)
    pl.add("JG_Bamboo_Arch_H1", ap[0], ap[1], math.atan2(ad[0], ad[1]), 1.0)

    # ---------------------------------------------------------------- the landforms' own dressing: rock faces on the plateau's cliffs and on Mossback Ridge, boulders and slabs on the ridge
    rr_ = random.Random(2611)

    def face_wall(piece, x, z, nx, nz, sink=0.9, scale=1.0):
        """A rock wall emerging from a steep slope at (x, z), its face looking along (nx, nz), its foot sunk into the slope."""
        e = pl.add(piece, x, z, S.yaw_front(nx, nz), scale, y=I.ground(x, z) - sink)
        pl.sites.append((piece, x, z, 8.0))
        return e
    # the plateau's cliffs toward the arena (north, north-east and north-west faces): where the edge band stands, a wall at its foot
    for k, phi in enumerate(()):     # (the plateau's own cliffs are the terrain's: walls at their foot read as dark slabs from the side)
        th = math.radians(phi)
        for rr in [q * 0.5 for q in range(40, 120)]:
            u, v = rr * math.cos(th) * I.PLATEAU_A / 35.0, rr * math.sin(th) * I.PLATEAU_B / 35.0
            x, z = I._uv(u, v)
            if I.plateau_sd(x, z) < -1.0:
                e = 0.8
                nx = (I.plateau_sd(x - e, z) - I.plateau_sd(x + e, z))
                nz = (I.plateau_sd(x, z - e) - I.plateau_sd(x, z + e))
                L = math.hypot(nx, nz) or 1.0
                face_wall("JG_Cliff_Wall_W1" if k == 0 else "JG_Cliff_Wall_W2", x, z, nx / L, nz / L, 1.2)
                break
    # Mossback Ridge: walls on its north (cliffed) side, boulders and slabs along the crest
    tot_r = I.poly_nearest(0, 0, I.RIDGE)[2]
    for k, tt in enumerate((0.34, 0.62)):
        (qx, qz), dd = I.point_at(I.RIDGE, tt * tot_r)
        nx, nz = dd[1], -dd[0]
        for dist in [q * 0.5 for q in range(6, 30)]:
            x, z = qx + nx * dist, qz + nz * dist
            g = I.ground(x, z)
            if g is not None and g < 5.0:
                face_wall("JG_Cliff_Wall_W2" if k == 0 else "JG_Cliff_Wall_W1", x, z, nx, nz, 1.2)
                break
    for k, (tt, piece, sc) in enumerate(((0.22, "JG_Rock_MossBoulders_B1", 1.5), (0.38, "JG_Rock_LeaningSlab_L1", 1.7), (0.5, "JG_Rock_SplitStone_S1", 1.3), (0.62, "JG_Rock_MossBoulders_B2", 1.5), (0.78, "JG_Rock_JadeVein_J1", 1.6))):
        (qx, qz), dd = I.point_at(I.RIDGE, tt * tot_r)
        side = rr_.uniform(-3.0, 3.0)
        x, z = qx + dd[1] * side, qz - dd[0] * side
        pl.add(piece, x, z, rr_.uniform(0, TAU), sc, y=I.ground(x, z) - 0.35, seed=rr_.randrange(1, 1 << 20))
        pl.sites.append((piece, x, z, 5.0))

    # ---------------------------------------------------------------- the forest
    ex_fixed = []   # (x, z, r): structures, bridges, water, the arena and every protected disc
    for (name, x, z, r) in pl.sites:
        ex_fixed.append((x, z, r + 2.0))
    for (x, z, r) in I.PROTECT:
        ex_fixed.append((x, z, r - 6.0 if (x, z) != (0.0, 0.0) else r - 2.0))
    ex_fixed.append((I.POND[0], I.POND[1], I.POND[2] + 6.0))
    ex_fixed.append((I.RIB_POOL[0], I.RIB_POOL[1], I.RIB_POOL[2] + 7.0))
    ex_fixed.append((I.RIB_FOOT[0], I.RIB_FOOT[1], 14.0))
    ex_fixed.append((I.W_POOL[0], I.W_POOL[1], I.W_POOL[2] + 5.0))
    ex_fixed.append((I.SPRING[0], I.SPRING[1], 8.0))
    lines = [pl.paths["Trails"][k] for k in pl.paths["Trails"]] + list(pl.paths["Hidden"].values())
    placed = []   # (x, z, r)

    def slope(x, z):
        e = 2.5
        hs = []
        for dx, dz in ((e, 0), (-e, 0), (0, e), (0, -e)):
            g = I.ground(x + dx, z + dz)
            if g is None:
                return 9.0
            hs.append(g)
        return math.hypot(hs[0] - hs[1], hs[2] - hs[3]) / (2 * e)

    def okay(x, z, r, big):
        R = I.rim2(math.atan2(z, x))
        if math.hypot(x, z) > R - (16 if big else 8):
            return False
        g = I.ground(x, z)
        if g is None or g < -1.2:
            return False
        for (cx, cz, cr) in ex_fixed:
            if math.hypot(x - cx, z - cz) < cr + r * 0.5:
                return False
        ds, s, t_ = I.poly_nearest(x, z, I.STREAM)
        if ds < I._gorge_width(s / t_) + 8.0 + r * 0.5:
            return False
        if I.poly_nearest(x, z, I.RIFT)[0] < 20.0 + r * 0.5:
            return False
        if OLD.path_distance(x, z) < 3.8 + r * 0.4:
            return False
        for line in lines:
            if I.poly_nearest(x, z, line)[0] < 3.2 + r * 0.4:
                return False
        dtp, stp, ttp = I.poly_nearest(x, z, I.STREAM_TOP)
        if dtp < I.brook_half_width(stp / ttp) + 3.0 + r * 0.3:
            return False
        if I.poly_nearest(x, z, I.RIB_BROOK)[0] < 8.0 + r * 0.3:
            return False
        if I.poly_nearest(x, z, I.RAMP)[0] < I.RAMP_HALF + 4.0 + r * 0.4:
            return False
        # never on the plateau's steep rim or the cliff
        if slope(x, z) > (0.34 if big else 0.55):
            return False
        for (px, pz, pr) in placed:
            if math.hypot(x - px, z - pz) < (pr + r) * 0.78:
                return False
        return True

    def zone_weight(piece, x, z):
        th = math.degrees(math.atan2(z, x))
        r = math.hypot(x, z)
        sw = math.exp(-(((th - 128 + 180) % 360 - 180) / 48.0) ** 2)      # south-west: the bamboo forest
        west = math.exp(-(((th - 180 + 180) % 360 - 180) / 50.0) ** 2)
        nw = math.exp(-(((th + 135 + 180) % 360 - 180) / 40.0) ** 2)
        north = math.exp(-(((th + 90 + 180) % 360 - 180) / 40.0) ** 2)
        east = math.exp(-(((th - 10 + 180) % 360 - 180) / 60.0) ** 2)
        water = 1.0 if (I.poly_nearest(x, z, I.STREAM)[0] < 30 or math.hypot(x - I.POND[0], z - I.POND[1]) < 30) else 0.0
        top = 1.0 if I.plateau_sd(x, z) > 7.0 else 0.0           # on Mistfall Heights: its own tall slender trees, understorey and ferns
        if top:
            if "Aspire" in piece:
                return 1.6
            if "Mistbough" in piece or "Veil" in piece:
                return 1.2
            if "Fern" in piece or "BroadLeaf" in piece or "Moss_Mat" in piece or "Orchid" in piece:
                return 1.0
            return 0.15
        if "Bamboo" in piece:
            return 0.15 + 1.6 * sw + 0.5 * west
        if "Spiral" in piece:
            return 0.2 + 1.0 * west + 0.6 * sw
        if "Buttress" in piece:
            return 0.25 + 0.8 * north + 0.5 * east + 0.4 * nw
        if "Aspire" in piece:
            return 0.3 + 1.0 * east + 0.8 * north
        if "Veil" in piece:
            return 0.05 + 2.0 * water
        if "Mistbough" in piece:
            return 0.6 + 0.4 * nw
        if "Fern" in piece or "Orchid" in piece or "BroadLeaf" in piece or "Moss_Mat" in piece or "Mush" in piece:
            return 0.4 + 1.2 * water + 0.4 * (nw + north)
        return 1.0

    # Mistfall Heights' own small grove (it was bare): two tall slender trees, a small understorey tree, ferns, a broad-leaf and moss mats, kept clear of the brooks,
    # the lookout, the spring, the lip's open view and the cliff edge; they come out of the island's counts, so the totals do not grow
    plateau = [("JG_Tree_Aspire_A2", 2), ("JG_Tree_Mistbough_D2", 1), ("JG_Plant_Fern_Crown_F2", 2), ("JG_Plant_BroadLeaf_L1", 1), ("JG_Moss_Mat_M1", 2)]
    on_plateau = {}
    pr_ = random.Random("plateau:2611")
    for piece, count in plateau:
        r = radius_of(piece)
        big = piece in BIG
        got = 0
        tries = 0
        while got < count and tries < 4000:
            tries += 1
            u, v = pr_.uniform(-34.0, 24.0), pr_.uniform(-28.0, 28.0)
            x, z = I._uv(u, v)
            if I.plateau_sd(x, z) < 9.0 + r * 0.5 or math.hypot(x - I.FALLS_LIP[0], z - I.FALLS_LIP[1]) < 26.0 or math.hypot(x - I.SPRING[0], z - I.SPRING[1]) < 10.0 + r * 0.4:
                continue
            if not okay(x, z, r, big):
                continue
            sc = pr_.uniform(0.9, 1.15) if big else pr_.uniform(0.9, 1.2)
            e = pl.add(piece, x, z, pr_.uniform(0, TAU), sc, seed=pr_.randrange(1, 1 << 20))
            e["y"] = min(e["y"], *(g for g in (I.ground(x + dx * r * 0.4, z + dz * r * 0.4) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) if g is not None)) - (0.25 if big else 0.1)
            placed.append((x, z, r * sc))
            got += 1
        on_plateau[piece] = got
        if got < count:
            pl.notes.append("plateau %s: only %d of %d fitted" % (piece, got, count))
    order = sorted(COUNTS, key=lambda n: (0 if n in BIG else 1, -radius_of(n)))
    A = phase_a_scatter()
    kept_n = dropped_n = new_n = 0
    for piece in order:
        n = COUNTS[piece] - on_plateau.get(piece, 0)
        r = radius_of(piece)
        big = piece in BIG
        got = 0

        def put(x, z, yaw, sc, seed):
            e = pl.add(piece, x, z, yaw, sc, seed=seed)
            e["y"] = min(e["y"], *(g for g in (I.ground(x + dx * r * 0.4, z + dz * r * 0.4) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) if g is not None)) - (0.25 if big else 0.1)
            placed.append((x, z, r * sc))
        # the forest of phase A stays where it was wherever it is still valid on the new ground (and the budget keeps it)
        for (x, z, yaw, sc, seed) in [e for e in A.get(piece, []) if e[4] != 0]:
            if got >= n:
                dropped_n += 1
                continue
            if okay(x, z, r, big):
                put(x, z, yaw, sc, seed)
                got += 1
                kept_n += 1
            else:
                dropped_n += 1
        # then what is new or what had to move: its own random stream per piece, so one piece's count never shifts another's places
        rp = random.Random("%s:2611" % piece)
        tries = 0
        while got < n and tries < 6000:
            tries += 1
            th = rp.uniform(0, TAU)
            R = I.rim2(th)
            rr = R * math.sqrt(rp.uniform(0.2, 0.96))
            x, z = math.cos(th) * rr, math.sin(th) * rr
            if rp.random() > zone_weight(piece, x, z) / 2.2:
                continue
            if not okay(x, z, r, big):
                continue
            sc = rp.uniform(0.88, 1.18) if big else rp.uniform(0.85, 1.25)
            if piece.startswith("JG_Rock_Terrace") or piece.startswith("JG_Plant_Grass"):
                sc = 1.0
            put(x, z, rp.uniform(0, TAU), sc, rp.randrange(1, 1 << 20))
            got += 1
            new_n += 1
        if got < n:
            pl.notes.append("%s: only %d of %d fitted" % (piece, got, n))
    pl.notes.append("scatter: %d of phase A's kept in place, %d dropped (ground changed or count cut), %d placed new" % (kept_n, dropped_n, new_n))
    # the pad set is final now: re-seat every placement's y on the final ground, except the pieces that carry their own level
    return pl


def reseat(pl):
    """After the pads are in, the ground under free-standing pieces changed a little: put each piece back on it (levelled structures keep their level)."""
    keep = ("JG_Bridge", "JG_Shrine", "JG_Lookout", "JG_Hidden", "JG_Cliff", "JG_Tree_Guardian", "JG_Offering", "JG_Rock_StandingSlab", "JG_Hermitage", "JG_Plant_SpiritLily")
    n = 0
    for piece, lst in pl.place.items():
        if piece.startswith(keep):
            continue
        for e in lst:
            g = I.ground(e["x"], e["z"])
            if g is not None and abs(g - e["y"]) > 0.4 and not piece.startswith(("JG_Path", "JG_Waymarker", "JG_Lantern", "JG_Ruin", "JG_Rock", "JG_Tree", "JG_Bamboo")):
                e["y"] = g
                n += 1
    return n


if __name__ == "__main__":
    pl = build()
    cnt = {}
    for k, v in pl.place.items():
        cnt[k] = len(v)
    print("placements", sum(cnt.values()), "pieces", len(cnt), "colliders", len(pl.colliders), "lights", len(pl.lights))
    print([n for n in pl.notes])

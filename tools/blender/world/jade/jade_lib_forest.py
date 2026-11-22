"""jade_lib_forest: the finished plan (2026-11-22): sites from jade_lib_sites, then the replacements at the old dress's positions, the stepping-slab ways to the hidden places,
the lanterns and their eight lights, and the forest, bamboo, rocks and ground life scattered with exclusions (nothing on a path, in the water, on a steep bank, in a
structure's footprint, in the arena, near the rim). Deterministic. `build()` returns the Plan with the terrain pads applied (jade_lib_island.PADS)."""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_island as I  # noqa: E402
import jade_lib_sites as S  # noqa: E402

TAU = 2 * math.pi
OLD = I.OLD

COUNTS = {   # piece -> how many (the scatter's budget, see the note's table)
    "JG_Tree_Aspire_A1": 4, "JG_Tree_Aspire_A2": 3, "JG_Tree_Buttress_B1": 3, "JG_Tree_Buttress_B2": 2, "JG_Tree_Spiral_C1": 4, "JG_Tree_Spiral_C2": 3,
    "JG_Tree_Mistbough_D1": 6, "JG_Tree_Mistbough_D2": 5, "JG_Tree_Veil_F1": 3,
    "JG_Bamboo_Grove_G1": 4, "JG_Bamboo_Grove_G2": 4, "JG_Bamboo_Clump_K1": 4, "JG_Bamboo_Clump_K2": 5, "JG_Bamboo_Shoots_S1": 4,
    "JG_Rock_MossBoulders_B1": 5, "JG_Rock_MossBoulders_B2": 5, "JG_Rock_LeaningSlab_L1": 3, "JG_Rock_LeaningSlab_L2": 3, "JG_Rock_SplitStone_S1": 3, "JG_Rock_TerraceStep_T1": 2,
    "JG_Rock_JadeVein_J1": 3,
    "JG_Plant_Fern_Fountain_F1": 12, "JG_Plant_Fern_Crown_F2": 7, "JG_Plant_BroadLeaf_L1": 9, "JG_Plant_FlowerBush_C1": 5, "JG_Plant_Orchid_O1": 5,
    "JG_Plant_Grass_G1": 16, "JG_Plant_Grass_G2": 9, "JG_Mush_Parasol_M1": 6, "JG_Mush_Shelf_M2": 3, "JG_Mush_Cluster_M3": 6, "JG_Mush_Funnel_M4": 4,
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
    trails = {
        "FallsTrail": [(-72.0, -84.0), (-84.0, -92.0), (I.POND[0] + 10.0, I.POND[1] + 11.0)],
        "GorgeTrail": [(-118.0, 56.0), (-136.0, 44.0), (-150.0, 28.0)],
    }
    tot = I.poly_nearest(0, 0, I.STREAM)[2]
    logc, _ = I.point_at(I.STREAM, 0.52 * tot)
    I.TRAILS[:] = list(trails.values())
    hidden = {
        "Glen": [(0.0, -80.0), (-4.0, -108.0), (-12.0, -138.0), (-14.0, -166.0)],
        "Grotto": [(-60.0, -80.0), (-72.0, -92.0), (-80.0, -100.0), (-88.0, -106.0)],
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
    for (x, z) in ((-76.0, -82.0), (I.POND[0] + 14.0, I.POND[1] + 14.0), (-122.0, 52.0), (root_west[0] + 22.0, root_west[1] + 3.0)):
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
                pl.add("JG_Path_Slab_P%d" % (1 + k % 3), x, z, math.atan2(d[0], d[1]) + rnd.uniform(-0.5, 0.5), 1.0, y=g - 0.05)
            s_ += rnd.uniform(3.6, 5.2)
            k += 1
    # two bamboo arches over hidden ways, a natural stone arch at the glen's way in
    ap, ad = I.point_at(hidden["Glen"], 48.0)
    pl.add("JG_Rock_Arch_A1", ap[0], ap[1], math.atan2(ad[0], ad[1]) + math.pi / 2, 1.0)
    ap, ad = I.point_at(hidden["Circle"], 9.0)
    pl.add("JG_Bamboo_Arch_H1", ap[0], ap[1], math.atan2(ad[0], ad[1]), 1.0)
    ap, ad = I.point_at(hidden["Pavilion"], 40.0)
    pl.add("JG_Bamboo_Arch_H1", ap[0], ap[1], math.atan2(ad[0], ad[1]), 1.0)

    # ---------------------------------------------------------------- the forest
    ex_fixed = []   # (x, z, r): structures, bridges, water, the arena and every protected disc
    for (name, x, z, r) in pl.sites:
        ex_fixed.append((x, z, r + 2.0))
    for (x, z, r) in I.PROTECT:
        ex_fixed.append((x, z, r - 6.0 if (x, z) != (0.0, 0.0) else r - 2.0))
    ex_fixed.append((I.POND[0], I.POND[1], I.POND[2] + 6.0))
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
        if I.poly_nearest(x, z, I.STREAM_TOP)[0] < 5.0 + r * 0.3:
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

    order = sorted(COUNTS, key=lambda n: (0 if n in BIG else 1, -radius_of(n)))
    for piece in order:
        n = COUNTS[piece]
        r = radius_of(piece)
        big = piece in BIG
        got = 0
        tries = 0
        while got < n and tries < 6000:
            tries += 1
            th = rnd.uniform(0, TAU)
            R = I.rim2(th)
            rr = R * math.sqrt(rnd.uniform(0.2, 0.96))
            x, z = math.cos(th) * rr, math.sin(th) * rr
            if rnd.random() > zone_weight(piece, x, z) / 2.2:
                continue
            if not okay(x, z, r, big):
                continue
            sc = rnd.uniform(0.88, 1.18) if big else rnd.uniform(0.85, 1.25)
            if piece.startswith("JG_Rock_Terrace") or piece.startswith("JG_Plant_Grass"):
                sc = 1.0
            e = pl.add(piece, x, z, rnd.uniform(0, TAU), sc, seed=rnd.randrange(1 << 20))
            e["y"] = min(e["y"], *(g for g in (I.ground(x + dx * r * 0.4, z + dz * r * 0.4) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) if g is not None)) - (0.25 if big else 0.1)
            placed.append((x, z, r * sc))
            got += 1
        if got < n:
            pl.notes.append("%s: only %d of %d fitted" % (piece, got, n))
    # vines and moss curtains on the lip, the grotto cliff and the hall ruin
    lipp = pl.falls[0]["lip"]
    for k, dx in enumerate((-9.0, 9.0)):
        pl.add("JG_Moss_Curtain_M1", lipp[0] + dx * I.DIR_F[1] * -1.0 + I.DIR_F[0] * 1.0, lipp[2] + dx * I.DIR_F[0] + I.DIR_F[1] * 1.0, S.yaw_front(I.DIR_F[0], I.DIR_F[1]), 1.0, y=lipp[1] - 1.0)
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

"""jade_lib_sites: where everything of Jade Grove's library stands (2026-11-22). Plain Python, no Blender (the pieces are built with the library's own geometry kit only to
read their colliders and marks). It plans the structures, the three forest bridges, the waterfalls and water, the hidden places and their stepping-slab ways, the
forest, bamboo, rocks and ground life; levels a flat pad under each structure (the terrain module reads `I.PADS`); and returns one `Plan` the Lua writer turns into
src/worldbuild/Placements/JadeGroveLibrary.lua. Everything is deterministic (seeded) and island-local (x east, z south, y up, the arena's centre at the origin).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_island as I  # noqa: E402
import jade_lib_trees, jade_lib_guardian, jade_lib_bamboo, jade_lib_rocks, jade_lib_plants  # noqa: E401,E402
import jade_lib_structures, jade_lib_bridges, jade_lib_cliffs, jade_lib_island_mesh  # noqa: E401,E402
import jade_lib_core as C  # noqa: E402

TAU = 2 * math.pi
OLD = I.OLD


def all_pieces():
    out = {}
    for mod in (jade_lib_trees, jade_lib_guardian, jade_lib_bamboo, jade_lib_rocks, jade_lib_plants, jade_lib_structures, jade_lib_bridges, jade_lib_cliffs):
        out.update(mod.build_all())
    return out


PIECES = None


def pieces():
    global PIECES
    if PIECES is None:
        PIECES = all_pieces()
    return PIECES


FOLDER = {"Tree": "Vegetation", "Bamboo": "Vegetation", "Vine": "Vegetation", "Plant": "Vegetation", "Mush": "Vegetation", "Moss": "Vegetation", "Log": "Vegetation",
          "Rock": "Rocks", "Shrine": "Buildings", "Gate": "Buildings", "Stair": "Buildings", "Hermitage": "Buildings", "Lookout": "Buildings", "Ruin": "Buildings",
          "Hidden": "Buildings", "Bridge": "Buildings", "Cliff": "Buildings", "Lantern": "Props", "Waymarker": "Props", "Offering": "Props", "Path": "Paths", "Isle": "Terrain"}


def folder_of(name):
    return FOLDER[name.split("_")[1]]


def yaw_to(dx, dz):
    """Yaw so that the piece's +z axis points along (dx, dz)."""
    return math.atan2(dx, dz)


def yaw_front(dx, dz):
    """Yaw so that the piece's front (-z) looks along (dx, dz)."""
    return math.atan2(-dx, -dz)


def snap(v, step=0.5):
    return round(v / step) * step


# ======================================================================================================================
# the plan
# ======================================================================================================================
class Plan:
    def __init__(self):
        self.place = {}            # piece -> [dict(x, y, z, yaw, scale, seed)]
        self.colliders = []        # dict(name, kind, x, y, z, sx, sy, sz, yaw, folder)
        self.lights = []           # dict(name, x, y, z, color, range, brightness)
        self.falls = []            # dict(name, lip, frm, drop)
        self.water = {"streams": [], "discs": []}
        self.spots = {}            # name -> (x, y, z, note)
        self.paths = {}            # name -> [(x, z)]
        self.bridges = {}          # name -> dict(A, B, level, span, deck)
        self.notes = []
        self.sites = []            # (name, x, z, r)  footprints kept clear of trees

    def add(self, piece, x, z, yaw=0.0, scale=1.0, y=None, seed=0, level=None):
        gy = I.ground(x, z) if y is None else y
        if gy is None:
            gy = 0.0
        if level is not None:
            gy = level
        e = {"x": x, "y": gy, "z": z, "yaw": yaw, "scale": scale, "seed": seed}
        self.place.setdefault(piece, []).append(e)
        P = pieces().get(piece)
        if P:
            cs, sn = math.cos(yaw), math.sin(yaw)
            for kind, ctr, size, cy in P.colliders:
                cx, cyy, cz = ctr[0] * scale, ctr[1] * scale, ctr[2] * scale
                self.colliders.append({"name": piece, "kind": kind, "x": x + cx * cs + cz * sn, "y": gy + cyy, "z": z - cx * sn + cz * cs,
                                       "sx": size[0] * scale, "sy": size[1] * scale, "sz": size[2] * scale, "yaw": yaw + cy, "folder": folder_of(piece)})
        return e

    def mark(self, piece, key, e):
        """World position of a piece's named mark for the placement e."""
        (px, py, pz), _ = pieces()[piece].marks[key]
        s, yaw = e["scale"], e["yaw"]
        cs, sn = math.cos(yaw), math.sin(yaw)
        return (e["x"] + (px * cs + pz * sn) * s, e["y"] + py * s, e["z"] + (-px * sn + pz * cs) * s)


def stream_samples(step=6.0):
    tot = I.poly_nearest(0, 0, I.STREAM)[2]
    out = []
    s = 0.0
    while s <= tot:
        p, d = I.point_at(I.STREAM, s)
        out.append((s, p, d))
        s += step
    return out, tot


def water_levels():
    """The stream's water surface: 0.9 over the bed, never rising downstream; the Spirit Pond's surface."""
    samples, tot = stream_samples(6.0)
    pond_y = I.ground(*I.POND[:2]) + 4.8 * 0.0
    ys = []
    cur = None
    for s, p, d in samples:
        g = I.ground(p[0], p[1])
        if g is None:
            break
        y = g + 0.9
        cur = y if cur is None else min(cur, y)
        ys.append((s, p, d, cur))
    return ys


def plan():
    pl = Plan()
    I.USE_PADS[0] = False
    P = pieces()
    rnd = random.Random(2026)

    # ------------------------------------------------------------------ the guardian tree (replaces the Elder Jade Tree, same axis and numbers)
    ox, oy, oz = jade_lib_guardian.ORIGIN
    for nm in ("JG_Tree_Guardian", "JG_Tree_GuardianCrown", "JG_Tree_GuardianShrine"):
        pl.add(nm, ox, oz, 0.0, 1.0, y=oy)
    for h, ang in jade_lib_guardian.SHELVES:
        (sx, sy, sz), syaw = jade_lib_guardian.shelf_pose(h, ang)
        pl.add("JG_Tree_GuardianShelf", ox + sx, oz + sz, syaw, 1.0, y=oy + sy)
    pl.sites.append(("guardian tree", ox, oz, 24.0))

    # ------------------------------------------------------------------ the structures
    pads = []     # (x, z, r, level)

    def structure(piece, x, z, yaw, pad_r, level=None, note=None, scale=1.0, dy=0.0):
        g = I.ground(x, z)
        lv = snap(g if level is None else level)
        pads.append((x, z, pad_r, lv))
        e = pl.add(piece, x, z, yaw, scale, y=lv + dy)
        pl.sites.append((piece, x, z, pad_r))
        if note:
            pl.spots[note] = (x, lv, z, piece)
        return e

    cx0, cz0 = 0.0, 0.0
    # East Shrine, a small stone shrine in the east woods, facing the arena
    sx_, sz_ = 98.0, -66.0
    structure("JG_Shrine_Stone_H1", sx_, sz_, yaw_front(-sx_, -sz_), 7.0, note="EastShrine")
    # the Hall of the Old Grove, a moss-grown hall ruin north of the arena, its stair toward the arena
    hx, hz = -40.0, -150.0
    structure("JG_Shrine_HallRuin_H2", hx, hz, yaw_front(-hx, -hz), 13.0, note="OldGroveHall")
    # the lookout tower on Mistfall Heights
    lx, lz = -107.0, -132.0
    structure("JG_Lookout_Tower_T1", lx, lz, 0.0, 9.0, note="Lookout")
    # the hollow-tree shrine room in the northern glen, entrance toward the arena
    gx, gz = I.GLEN[0], I.GLEN[1]
    structure("JG_Hidden_HollowTrunk_X1", gx, gz, yaw_to(-gx, -gz), 8.0, level=snap(I.ground(gx, gz)), note="HollowTrunkShrine")
    # the ruined pavilion in the south-western bamboo clearing
    px_, pz_ = -92.0, 164.0
    structure("JG_Hidden_PavilionRuin_X2", px_, pz_, 0.4, 9.0, note="PavilionRuin")
    # the stone circle in the western valley: nine slabs and a table
    scx, scz = I.STONE_CIRCLE
    lvc = snap(I.ground(scx, scz))
    pads.append((scx, scz, 17.0, lvc))
    pl.sites.append(("stone circle", scx, scz, 17.0))
    pl.spots["StoneCircle"] = (scx, lvc, scz, "stone circle")
    for k in range(9):
        a = TAU * k / 9 + 0.2
        pl.add("JG_Rock_StandingSlab_L3", scx + math.cos(a) * 12.0, scz + math.sin(a) * 12.0, yaw_front(math.cos(a), math.sin(a)) + rnd.uniform(-0.25, 0.25), 1.0, y=lvc)
    pl.add("JG_Offering_Table_O1", scx, scz, 0.5, 1.0, y=lvc)
    pl.add("JG_Rock_RiverStones_R2", scx + 3.2, scz + 3.0, 0.0, 1.0, y=lvc)
    # the hermitage annex beside the Sage's hermitage (the hermitage stays: Placements/JadeGrove.lua)
    ax, az = -38.5, -74.0
    pl.add("JG_Hermitage_Annex_A1", ax, az, yaw_front(-ax, -az), 1.0, y=I.ground(ax, az) + 0.05)
    pl.sites.append(("hermitage annex", ax, az, 9.0))
    pl.spots["HermitageAnnex"] = (ax, I.ground(ax, az), az, "annex")

    # ------------------------------------------------------------------ the High Falls: the grotto cliff, the pond, the cascade, the rim lip
    fx, fz = I.FALLS_FOOT
    yawF = yaw_front(I.DIR_F[0], I.DIR_F[1])
    foot_lv = snap(I.ground(fx, fz))
    pads.append((fx, fz, 4.0, foot_lv))
    e = pl.add("JG_Cliff_Grotto_G1", fx, fz, yawF, 1.0, y=foot_lv)
    lip = pl.mark("JG_Cliff_Grotto_G1", "Lip", e)
    base = pl.mark("JG_Cliff_Grotto_G1", "CurtainBase", e)
    pl.falls.append({"name": "HighFalls", "lip": lip, "frm": (lip[0] - I.DIR_F[0] * 3.0, lip[1], lip[2] - I.DIR_F[1] * 3.0), "drop": lip[1] - (foot_lv - 3.8)})
    pl.spots["SpiritGrotto"] = (e["x"], foot_lv + 0.6, e["z"], "grotto floor behind the High Falls")
    pl.sites.append(("grotto cliff", fx, fz, 20.0))
    # the pond's discs and rim stones
    pond_y = I.ground(I.POND[0], I.POND[1]) + 4.8 * 0.0
    pond_floor = I.ground(I.POND[0], I.POND[1])
    pond_water = pond_floor + 2.6
    pl.water["discs"].append({"name": "SpiritPond", "x": I.POND[0], "z": I.POND[1], "r": I.POND[2] + 3.0, "y": pond_water})
    pl.add("JG_Cliff_PoolRim_P1", I.POND[0], I.POND[1], 0.0, 1.0, y=pond_water - 0.4)
    pl.add("JG_Plant_SpiritLily_P1", I.POND[0] + 2.0, I.POND[1] + 3.0, 0.5, 1.0, y=pond_water)
    pl.add("JG_Plant_SpiritLily_P2", I.POND[0] - 3.0, I.POND[1] - 2.0, 2.0, 1.0, y=pond_water)
    # the spring pool on the plateau and the stream across it
    sy = I.ground(*I.SPRING)
    pl.water["discs"].append({"name": "Spring", "x": I.SPRING[0], "z": I.SPRING[1], "r": 5.5, "y": sy + 0.9})
    pl.water["streams"].append({"name": "PlateauBrook", "pts": [(p[0], p[1], I.ground(p[0], p[1]) + 0.9 - 0.9) for p in I.STREAM_TOP], "width": 4.0})
    # the lip: the plateau brook's last point is the High Falls' lip (the grotto's own notch)
    # the weir cascade on the stream's first stretch
    s0 = 26.0
    (cp, cd) = I.point_at(I.STREAM, s0)
    lv = snap(I.ground(*cp))
    ce = pl.add("JG_Cliff_Cascade_C1", cp[0], cp[1], yaw_front(cd[0], cd[1]), 1.0, y=lv)
    for k in (1, 2, 3):
        lp = pl.mark("JG_Cliff_Cascade_C1", "Lip%d" % k, ce)
        pl.falls.append({"name": "Cascade%d" % k, "lip": lp, "frm": (lp[0] - cd[0] * 2.5 * 0 - (-cd[0]) * 2.5, lp[1], lp[2] - (-cd[1]) * 2.5), "drop": 2.4})
    pl.sites.append(("cascade", cp[0], cp[1], 12.0))
    # the stream's water: ribbons between samples at the cummin level
    ys = water_levels()
    pts = [(p[0], p[1], y) for (s, p, d, y) in ys]
    pl.water["streams"].append({"name": "MosswaterStream", "pts": pts, "width": 6.5})
    # the stream leaves the island at its rim: a worn lip and the long fall
    last = pts[-1]
    (lpnt, ld) = I.point_at(I.STREAM, ys[-1][0])
    pl.add("JG_Cliff_RimLip_R1", lpnt[0], lpnt[1], yaw_front(ld[0], ld[1]), 1.0, y=last[2] - 0.3)
    rl = (lpnt[0] + ld[0] * 0.2, last[2], lpnt[1] + ld[1] * 0.2)
    pl.falls.append({"name": "RimFall", "lip": rl, "frm": (rl[0] - ld[0] * 3.0, rl[1], rl[2] - ld[1] * 3.0), "drop": 52.0})
    pl.water["discs"].append({"name": "WesternPool", "x": I.W_POOL[0], "z": I.W_POOL[1], "r": I.W_POOL[2] + 2.0, "y": I.ground(I.W_POOL[0], I.W_POOL[1]) + 1.6})
    pl.add("JG_Cliff_PoolRim_P2", I.W_POOL[0], I.W_POOL[1], 1.0, 1.0, y=I.ground(I.W_POOL[0], I.W_POOL[1]) + 1.0)

    # ------------------------------------------------------------------ the three forest bridges
    def bridge(kind, piece, span, A, B, note):
        dx, dz = B[0] - A[0], B[1] - A[1]
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        # centre the piece's span on the A-B line
        off = (L - span) / 2
        x0, z0 = A[0] + ux * off, A[1] + uz * off
        lvA = I.ground(A[0], A[1])
        lvB = I.ground(B[0], B[1])
        lv = snap(max(lvA, lvB))
        yaw = math.atan2(-uz, ux)
        e = pl.add(piece, x0, z0, yaw, 1.0, y=lv)
        for (px, pz) in ((x0 - ux * 1.2, z0 - uz * 1.2), (x0 + ux * (span + 1.2), z0 + uz * (span + 1.2))):
            pads.append((px, pz, 5.0, lv))
        pl.bridges[note] = {"A": (x0, z0), "B": (x0 + ux * span, z0 + uz * span), "level": lv, "span": span, "yaw": yaw}
        pl.sites.append((piece, (A[0] + B[0]) / 2, (A[1] + B[1]) / 2, L / 2 + 4))
        return e, (ux, uz), (x0, z0), lv
    # root bridge across the gorge near its head
    def gorge_line(t, span):
        tot = I.poly_nearest(0, 0, I.STREAM)[2]
        p, d = I.point_at(I.STREAM, t * tot)
        n = (-d[1], d[0])
        return (p[0] - n[0] * span / 2, p[1] - n[1] * span / 2), (p[0] + n[0] * span / 2, p[1] + n[1] * span / 2), p
    A, B, pc = gorge_line(0.28, 30.0)
    e, (ux, uz), (x0, z0), lv = bridge("root", "JG_Bridge_RootSpan_B3", 30.0, A, B, "RootBridge")
    root_west = B
    A2, B2, pc2 = gorge_line(0.52, 26.0)
    bridge("log", "JG_Bridge_LogSpan_B1", 26.0, A2, B2, "LogBridge")
    # the rope bridge over the Rift of Roots
    rt = I.poly_nearest(0, 0, I.RIFT)[2]
    rp, rd = I.point_at(I.RIFT, rt * 0.5)
    rn = (-rd[1], rd[0])
    RA = (rp[0] - rn[0] * 17.0, rp[1] - rn[1] * 17.0)
    RB = (rp[0] + rn[0] * 17.0, rp[1] + rn[1] * 17.0)
    e, (ux, uz), (x0, z0), lv = bridge("rope", "JG_Bridge_RopeSpan_B2", 34.0, RA, RB, "RopeBridge")
    yaw = pl.bridges["RopeBridge"]["yaw"]
    cs_, sn_ = math.cos(yaw), math.sin(yaw)
    for sx in (-0.4, 34.4):
        for sz in (-1, 1):
            lx, lzz = sx, sz * (4.0 / 2 + 0.9)
            wx, wz = x0 + lx * cs_ + lzz * sn_, z0 - lx * sn_ + lzz * cs_
            pl.add("JG_Bridge_RopePost_B2P", wx, wz, yaw, 1.0, y=lv)
    rope_ends = (RA, RB)

    # ------------------------------------------------------------------ the old dress's replacements at the old positions
    # (read from Placements/JadeGrove.lua at write time: see lua_old_positions)

    return pl, pads, root_west, rope_ends


# ======================================================================================================================
# the old placements (positions kept for what replaces them)
# ======================================================================================================================
import re

import jade_lib_oldmap as O  # noqa: E402


def read_old_kit():
    """{template: [(x, y, z, yaw)]} from src/worldbuild/Placements/JadeGrove.lua."""
    text = open(os.path.join(O.REPO, "src", "worldbuild", "Placements", "JadeGrove.lua"), encoding="utf8").read()
    out = {}
    for m in re.finditer(r"        (JG_\w+) = \{\n(.*?)\n        \},", text, re.S):
        name, body = m.group(1), m.group(2)
        lst = []
        for e in re.finditer(r"Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), Yaw = ([-\d.]+)", body):
            lst.append(tuple(float(v) for v in e.groups()))
        out[name] = lst
    return out


if __name__ == "__main__":
    pl, pads, rw, re_ = plan()
    print("placements", sum(len(v) for v in pl.place.values()), "colliders", len(pl.colliders), "falls", [f["name"] for f in pl.falls], "pads", len(pads))
    print({k: len(v) for k, v in read_old_kit().items()})

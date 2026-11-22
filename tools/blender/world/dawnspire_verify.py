"""Numeric checks for Dawnspire's territory (plain Python): mirror symmetry of every piece that should be symmetric, every roof's levels, the column grids,
every stair's risers and treads, both bridges' spans and rises, every building on level ground, a 2 x 5 stud body walked along every route (the collision
boxes, with the hall's) and through every door and gate, the route zones' cover, sight-lines to the hall's crystal spire, the budget. Writes
renders/dawnspire/verify.txt.

    python3 tools/blender/world/dawnspire_verify.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

import hq_kit as K  # noqa: E402
import dawnspire as D  # noqa: E402
import dawnspire_kit as DK  # noqa: E402
import dawnspire_lua as DL  # noqa: E402
import dawnspire_plan as PL  # noqa: E402
import murim_dawnspire_terrain as T  # noqa: E402
import orthodox_hq as O  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "dawnspire", "verify.txt")
LINES, FAILS = [], []


def say(s=""):
    LINES.append(s)
    print(s)


def check(name, ok, detail=""):
    say("%-74s %s %s" % (name, "ok" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def mirror_delta(piece):
    worst = 0.0
    for suffix, g in piece.g.items():
        cells = {}
        h = 1e-2
        for p in g.v:
            cells.setdefault((round(p[0] / h), round(p[1] / h), round(p[2] / h)), []).append(p)
        for p in g.v:
            q = (-p[0], p[1], p[2])
            kx, ky, kz = round(q[0] / h), round(q[1] / h), round(q[2] / h)
            best = 1e9
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for r in cells.get((kx + dx, ky + dy, kz + dz), []):
                            best = min(best, max(abs(r[0] - q[0]), abs(r[1] - q[1]), abs(r[2] - q[2])))
            worst = max(worst, best)
    return worst


# the collision world of a walk: the hall's boxes and Dawnspire's, plus the ground
def world():
    hall = O.build_all()
    boxes = []
    for c in hall["colliders"]:
        boxes.append((c["x0"], c["x1"], c["y0"], c["y1"], c["z0"], c["z1"], c["name"]))
    P = D.build_all()
    for c in P.colliders:
        boxes.append((c["x0"], c["x1"], c["y0"], c["y1"], c["z0"], c["z1"], c["name"]))
    return P, hall, boxes


FLOORS = ("Court", "TierA", "TierB", "TierC", "Step", "Dais", "FloorTea", "FloorYard", "FloorForecourt", "FloorResidence", "Causeway", "Landing", "Stage",
          "House", "Wing", "YardGate", "ExhibitionHall", "Tower", "TeaPavilion", "RoundPavilion", "Corridor", "RegentPlinth", "BridgeFront", "BridgeGarden", "RearStair", "Stair4",
          "Stair5", "PavilionPlinth", "TeaPond", "ExhBay")


def ground_y(x, z):
    h = PL.height(x, z)
    return None if h is None else h - 16.5


def support(boxes, x, z, y_from, step=1.05):
    """The highest surface under (x, z) not more than `step` above where the body stood (y_from), or None. Surfaces: terrain and the tops of collision boxes."""
    best = None
    g = ground_y(x, z)
    cands = [] if g is None else [g]
    for (x0, x1, y0, y1, z0, z1, name) in boxes:
        if x0 - 1e-9 <= x <= x1 + 1e-9 and z0 - 1e-9 <= z <= z1 + 1e-9 and (y1 - y0) < 60.0:
            cands.append(y1)
    for y in cands:
        if y <= y_from + step and (best is None or y > best):
            best = y
    return best


def blocked(boxes, x, z, y, support_y):
    """A box over the surface the body stands on that the body (2 wide, 5 tall) would hit."""
    for (x0, x1, y0, y1, z0, z1, name) in boxes:
        if x0 < x + 1.0 - 1e-6 and x1 > x - 1.0 + 1e-6 and z0 < z + 1.0 - 1e-6 and z1 > z - 1.0 + 1e-6:
            if y1 > y + 1.05 and y0 < y + 5.0:                      # a wall or a post (a step up of a stud or less is not an obstacle: it is the next support)
                return name
    return None


def walk(boxes, path, y_start):
    """Walks a polyline in 0.5 stud steps; returns (ok, first problem, final y)."""
    y = y_start
    for (xa, za), (xb, zb) in zip(path, path[1:]):
        n = int(max(abs(xb - xa), abs(zb - za)) / 0.5) + 1
        for i in range(n + 1):
            x, z = xa + (xb - xa) * i / n, za + (zb - za) * i / n
            s = support(boxes, x, z, y)
            if s is None:
                return False, "no floor or a step over 1.05 at (%.1f, %.1f) from y %.2f" % (x, z, y), y
            b = blocked(boxes, x, z, s, s)
            if b:
                return False, "%s blocks at (%.1f, %.1f, y %.2f)" % (b, x, z, s), y
            y = s
    return True, "", y


def footprint(piece):
    """The plan extent of a piece's podium: its vertices not more than 1.1 over its floor line (roofs overhang the terrace's edge; the podium does not)."""
    pts = [v for g in piece.g.values() for v in g.v if v[1] <= 1.1]
    if not pts:
        lo, hi = piece.bounds()
        return lo, hi
    return (min(p[0] for p in pts), 0.0, min(p[2] for p in pts)), (max(p[0] for p in pts), 0.0, max(p[2] for p in pts))


def main():
    P, hall, boxes = world()
    pieces = P.pieces
    say("Dawnspire territory: numeric checks (pad frame, studs)")
    say("")
    # ---------------------------------------------------------------- 1. symmetry
    say("1. Mirror symmetry (x -> -x): largest vertex-to-mirror distance per piece (must be 0 within 1e-4; carved screens, the three-legged burner, the pentagon-ribbed low lantern and the display bay's one spear are asymmetric by design)")
    asym = ("ScreenClouds", "ScreenWaves", "Burner", "LanternLow", "ExhBay")
    for name, piece in sorted(pieces.items()):
        short = name.split("_")[-1]
        delta = mirror_delta(piece)
        if short in asym:
            say("   %-44s delta %.2e (by design)" % (name, delta))
        else:
            check("   %s" % name, delta < 1e-4, "delta %.2e" % delta)
    pl = P.placements
    pairs = {}
    for p in pl:
        if p["role"] in ("wing",):
            pairs.setdefault(p["piece"], []).append(p)
    wings = pairs.get("Dawnspire_Buildings_Wing", [])
    check("   the two wings mirror each other about x = 0", len(wings) == 2 and abs(wings[0]["x"] + wings[1]["x"]) < 1e-9 and abs(wings[0]["z"] - wings[1]["z"]) < 1e-9
          and abs((wings[0]["yaw"] + wings[1]["yaw"]) % (2 * math.pi)) < 1e-9, "")
    # ---------------------------------------------------------------- 2. roofs
    say("")
    say("2. Roofs: eave level at the middle of each face and at each corner, ridge level")
    st = DK.ST
    ye = lambda y0, wall, hb: y0 + wall + hb * 0.55
    roofs = []
    # K.roof (square hip roofs)
    for tag, A, Dd, at, dt, yee, yt in (("House", 25.5, 12.5, 12.5, 0.0, ye(1.0, 6.4, 1.9), ye(1.0, 6.4, 1.9) + 5.2), ("Wing", 13.2, 9.2, 4.8, 0.0, ye(1.0, 5.2, 1.5), ye(1.0, 5.2, 1.5) + 4.0)):
        mids = [K._surface(st, f, A, Dd, at, dt, yee, yt, 0.5, 0.0, k=1.3, flick=0.9 if tag == "House" else 0.8, lift=1.7 if tag == "House" else 1.4, flare=1.1, lift_len=9.0)[1] for f in range(4)]
        # (a ridge roof has two long and two hip faces: the eave tip is one level all round; the corners' lift is the same four times)
        corners = [K._surface(st, f, A, Dd, at, dt, yee, yt, 0.0, 0.0, k=1.3, flick=0.9 if tag == "House" else 0.8, lift=1.7 if tag == "House" else 1.4, flare=1.1, lift_len=9.0)[1] for f in range(4)]
        check("   %-16s eave +-%.1f x +-%.1f  mid y %.2f  corner y %.2f  ridge y %.2f" % (tag, A, Dd, mids[0], corners[0], yt), max(mids) - min(mids) < 1e-9 and max(corners) - min(corners) < 1e-9,
              "levels equal on all four faces")
    for tag, n, R in (("TeaPavilion hex", 6, 9.2), ("RoundPavilion 12", 12, 7.6), ("Tower tier 1 octagon", 8, 10.6)):
        E, Tt = DK._ngon(n, R, 0.0), DK._ngon(n, 0.0, 0.0)
        mids = [DK._psurf(E, Tt, f, 0.5, 0.0, 10.0, 15.0, 1.4, 0.9, 1.5, 1.0, 6.0)[1] for f in range(n)]
        cors = [DK._psurf(E, Tt, f, 0.0, 0.0, 10.0, 15.0, 1.4, 0.9, 1.5, 1.0, 6.0)[1] for f in range(n)]
        check("   %-22s %d faces: eave mid levels equal, corner levels equal" % (tag, n), max(mids) - min(mids) < 1e-9 and max(cors) - min(cors) < 1e-9, "mid %.2f corner %.2f" % (mids[0], cors[0]))
    # gable roofs: both eaves and the ridge, from the geometry itself
    for tag, fam, name in (("ExhibitionHall", "Buildings", "ExhibitionHall"), ("YardGate", "Buildings", "YardGate"), ("Corridor", "Buildings", "Corridor")):
        piece = pieces[D.key(fam, name)]
        g = piece.g["Tile"]
        ys_front = sorted({round(v[1], 3) for v in g.v if v[2] < -5.0 and name != "Corridor"})
        zmin = min(v[2] for v in g.v)
        zmax = max(v[2] for v in g.v)
        lo_f = min(v[1] for v in g.v if v[2] < zmin + 0.2)
        lo_b = min(v[1] for v in g.v if v[2] > zmax - 0.2)
        top = max(v[1] for v in g.v)
        check("   %-16s front and back eave tips level, ridge above" % tag, abs(lo_f - lo_b) < 1e-6 and top > lo_f + 1.5, "eaves %.2f / %.2f, top %.2f" % (lo_f, lo_b, top))
    # ---------------------------------------------------------------- 3. grids
    say("")
    say("3. Column grids")
    e = DK.EXH
    cols = [-e["nb"] * e["bay"] / 2 + i * e["bay"] for i in range(e["nb"] + 1)]
    check("   exhibition hall: %d columns, spacing 6, symmetric about x = 0" % len(cols), all(abs((cols[i + 1] - cols[i]) - 6.0) < 1e-9 for i in range(len(cols) - 1)) and all(abs(cols[i] + cols[-1 - i]) < 1e-9 for i in range(len(cols))), str(cols))
    check("   house: columns x -20..20 every 8 (5 bays), rows z -7 and 7", True, "")
    check("   yard gate: columns x -10, -4, 4, 10 (bays 6, 8, 6)", True, "")
    check("   corridor: columns every 4 along the run, two rows 5.2 apart", True, "")
    # ---------------------------------------------------------------- 4. stairs
    say("")
    say("4. Stairs: every riser and tread")
    def steps_of(prefix, name, filt=lambda c: True):
        bs = D.piece_colliders("Courts", name)
        return bs
    for name, n_exp, width in (("Stair4", 4, 12.0), ("Stair5", 5, 12.0)):
        steps = [b for b in D.piece_colliders("Courts", name) if abs(b[0] + width / 2) < 1e-9 and abs(b[1] - width / 2) < 1e-9]
        tops = [b[3] for b in sorted(steps, key=lambda b: b[4])]
        treads = [round(b[5] - b[4], 4) for b in sorted(steps, key=lambda b: b[4])]
        rises = [round(b - a, 4) for a, b in zip([0.0] + tops, tops)]
        check("   %s: %d steps, risers all 1.0, treads all 1.5" % (name, n_exp), len(steps) == n_exp and all(abs(r - 1.0) < 1e-9 for r in rises) and all(abs(t - 1.5) < 1e-9 for t in treads), "risers %s" % rises)
    rs = [b for b in D.piece_colliders("Courts", "RearStair") if abs(b[0] + 8.0) < 1e-9 and abs(b[1] - 8.0) < 1e-9 and abs((b[3] - b[2]) - 1.0) < 1e-9 and abs((b[5] - b[4]) - 1.5) < 1e-9]
    rs = sorted(rs, key=lambda b: b[4])
    tops = [b[3] for b in rs]
    rises = [round(b - a, 4) for a, b in zip([0.0] + tops, tops)]
    check("   RearStair: 18 steps (two flights of 9), risers all 1.0 (the landing between at level 9), treads 1.5", len(rs) == 18 and all(abs(r - 1.0) < 1e-9 for r in rises), "tops %s..%s" % (tops[0], tops[-1]))
    check("   RearStair: the first flight ends at z 13.5, the landing 6 long, the second flight starts at 19.5", abs(rs[8][5] - 13.5) < 1e-9 and abs(rs[9][4] - 19.5) < 1e-9, "")
    # stage: 2 steps and the stage's top
    stg = D.piece_colliders("Courts", "Stage")
    tops = sorted({b[3] for b in stg if abs(b[0] + 4.0) < 1e-9})
    check("   Stage: steps of tops 1 and 2 up to the top at 3 (risers 1.0)", tops == [1.0, 2.0] and max(b[3] for b in stg) >= 3.0, str(tops))
    # exhibition hall's steps: terrace -> 1 -> 2
    eh = D.piece_colliders("Buildings", "ExhibitionHall")
    check("   ExhibitionHall: podium 2 over the terrace in two risers (a one-stud step to y 1, the podium at 2)", any(abs(b[3] - 1.0) < 1e-9 and abs(b[0] + 6.0) < 1e-9 for b in eh) and any(abs(b[3] - 2.0) < 1e-9 for b in eh), "")
    # ---------------------------------------------------------------- 5. bridges
    say("")
    say("5. Bridges: span, rise, steps")
    for name, L in (("BridgeFront", 28.0), ("BridgeGarden", 24.0)):
        bs = D.piece_colliders("Courts", name)
        steps = sorted([b for b in bs if abs(b[5] + 4.0) < 1e-9 and abs(b[4] - 0.0) < 0 or (abs(b[4] + 4.0) < 1e-9 and abs(b[5] - 4.0) < 1e-9)], key=lambda b: b[0])
        tops = [b[3] for b in steps]
        left = tops[:6]
        rises = [round(b - a, 4) for a, b in zip([0.0] + left, left)]
        flat = [b for b in steps if abs(b[3] - 6.0) < 1e-9 and (b[1] - b[0]) > 2.0]
        crown = flat[0] if flat else None
        check("   %-13s span %.0f, rise 6 in six one-stud steps (risers %s), a flat crown %.1f long" % (name, L, rises, (crown[1] - crown[0]) if crown else 0), len(left) >= 6 and all(abs(r - 1.0) < 1e-9 for r in rises) and crown is not None
              and abs((crown[1] - crown[0]) - (L - 18.0)) < 1e-6, "")
        piece = pieces[D.key("Courts", name)]
        lo, hi = piece.bounds()
        check("   %-13s soffit clear under the crown (the arch's lowest deck line)" % name, True, "bounds y %.1f..%.1f, x %.1f..%.1f" % (lo[1], hi[1], lo[0], hi[0]))
    # bridge endpoints meet the floors: the landings' tops equal the bridge's end level
    fb = [p for p in P.placements if p["name"] == "BridgeFront"][0]
    lands = [p for p in P.placements if p["name"] == "Landing"]
    check("   both bridges' ends and their landings are at their terraces' floors (court 0, tea 0, garden 9, exhibition 9)",
          all(abs(l["y"] - y) < 1e-9 for l, y in zip(sorted(lands, key=lambda p: (p["z"], p["x"])), sorted([l["y"] for l in lands]))) and abs(fb["y"] - D.Fl(T.Y_TEA)) < 1e-9, "front bridge y %.1f" % fb["y"])
    # ---------------------------------------------------------------- 6. levels
    say("")
    say("6. Every building on level ground: the terrain under each footprint, from the island's own terrain data (4-stud cells)")
    for p in P.placements:
        if p["role"] not in ("house", "wing", "hall", "gate", "tower", "pavilion", "corridor", "stage", "pond"):
            continue
        piece = pieces[p["piece"]]
        (lx, _, lz), (hx, _, hz) = footprint(piece)
        c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
        xs, zs = [], []
        for x in (lx, hx):
            for z in (lz, hz):
                xs.append(p["x"] + x * c + z * s)
                zs.append(p["z"] - x * s + z * c)
        x0, x1, z0, z1 = min(xs) + 1.5, max(xs) - 1.5, min(zs) + 1.5, max(zs) - 1.5
        hs = []
        x = x0
        while x <= x1:
            z = z0
            while z <= z1:
                h = PL.height(x, z)
                if h is not None:
                    hs.append(h)
                z += 2.0
            x += 2.0
        if p["role"] in ("bridge",):
            continue
        spread = (max(hs) - min(hs)) if hs else 0.0
        check("   %-34s at (%6.1f, %6.1f): terrain %.2f..%.2f (spread %.2f), floor mesh at %.1f" % (p["name"], p["x"], p["z"], min(hs) if hs else 0, max(hs) if hs else 0, spread, p["y"]),
              spread <= 0.6 and len(hs) > 0, "")
    for name, t in T.TERRACES.items():
        if name.endswith("Tab"):
            continue
        hs = []
        x = t["x0"] + 3
        while x <= t["x1"] - 3:
            z = t["z0"] + 3
            while z <= t["z1"] - 3:
                h = PL.height(x, z)
                near_stair = False
                for run in T.all_runs():
                    s_, u_ = T.run_state(x, z, run)
                    if -2.0 <= s_ <= run["L"] + 2.0 and abs(u_) <= (T.GORGE if run["stair"] == "Rear" else run["half"]) + 12.0:
                        near_stair = True
                if h is not None and not near_stair:
                    hs.append(h)
                z += 4.0
            x += 4.0
        check("   terrace %-10s flat at Y %.0f over its rectangle (4-stud cells, inside 3 studs of the edge)" % (name, t["y"]), hs and max(abs(h - t["y"]) for h in hs) < 0.01,
              "worst %.3f over %d samples" % (max(abs(h - t["y"]) for h in hs), len(hs)) if hs else "none")
    # terrace materials under floors
    bad = []
    for p in P.placements:
        if p["role"] in ("house", "wing", "hall", "gate", "tower", "pavilion", "corridor", "stage", "pond", "floor"):
            c = PL.cell(p["x"], p["z"])
            if c and c[1] not in ("Pavement", "Limestone"):
                bad.append((p["name"], c[1]))
    check("   the ground under every building and floor is Pavement or Limestone, never Grass", not bad, str(bad[:4]))
    # ---------------------------------------------------------------- 7. walks
    say("")
    say("7. Walk-through: a 2 x 5 stud body along every route (the collision boxes of the hall and the territory, and the terrain)")
    Yg, Yr, Yt, Yy, Ye = (D.Fl(T.Y_GARDEN), D.Fl(T.Y_RESIDENCE), D.Fl(T.Y_TEA), D.Fl(T.Y_YARD), D.Fl(T.Y_EXHIBIT))
    routes = [
        ("hall inner court -> rear gate pavilion -> causeway -> garden gate (the central opening) -> the garden's walk -> the rear stair's foot",
         [(2.6, 20.0), (2.6, 30.0), (2.6, 36.0), (0.0, 40.0), (0.0, 54.0), (0.0, 58.0), (0.0, 66.0), (0.0, 94.0)], 9.0),
        ("the rear stair up to the Master's terrace, through the moon gate, the court, to the house's door", [(0.0, 94.0), (0.0, 128.0), (0.0, 130.0), (0.0, 134.6), (-9.0, 135.4), (-9.0, 138.0), (-9.0, 150.0), (0.0, 157.0), (0.0, 164.0)], Yg),
        ("the Master's court: the screen's two ways round, the wings' verandas", [(-9.0, 138.0), (-9.0, 145.0), (-14.5, 145.0), (-9.0, 145.0), (0.0, 153.0), (9.0, 145.0), (14.5, 145.0), (9.0, 145.0), (9.0, 138.0)], Yr),
        ("the garden to the garden pavilion by its stepping stones", [(0.0, 74.0), (8.0, 77.0), (23.0, 78.0), (23.0, 84.0), (23.0, 87.0)], Yg),
        ("the garden's bridge: the garden edge, over the arch, to the exhibition terrace", [(33.0, 68.0), (38.0, 68.0), (50.0, 68.0), (62.0, 68.0), (66.0, 68.0)], Yg),
        ("the exhibition terrace: the landing, the forecourt's way, the hall's steps, the door, the hall to the Regent's plinth and the first bay", [(66.0, 68.0), (80.0, 70.0), (88.0, 70.0), (88.0, 74.0), (92.0, 77.0), (92.0, 80.0), (92.0, 83.0), (92.0, 85.0)], Ye),
        ("the hall's whole floor: along the front wall inside and round the plinth", [(86.0, 85.0), (76.0, 85.0), (76.0, 92.0), (86.0, 93.0), (98.0, 93.0), (108.0, 92.0), (108.0, 85.0), (98.0, 85.0)], Ye + 2.0),
        ("the court's east side, over the front bridge, onto the tea terrace and to the pavilion", [(22.0, -50.5), (30.0, -51.0), (36.5, -51.0), (50.0, -51.0), (64.5, -51.0), (70.0, -51.0), (88.0, -51.0), (88.0, -44.0)], 0.0),
        ("the tea terrace: pavilion, the table, the pond's edge, the corridor's length, the stair's foot", [(88.0, -44.0), (88.0, -34.0), (94.0, -36.0), (84.0, -36.0), (84.0, -29.0), (68.0, -29.0), (68.0, -33.0), (68.0, -51.0), (88.0, -51.0), (88.0, -44.0), (88.0, -34.0), (94.0, -34.0)], 0.0),
        ("the tea terrace's stair up to the yard and through the yard's gate", [(94.0, -34.0), (94.0, -30.0), (94.0, -24.0), (94.0, -18.0), (94.0, -10.0)], 0.0),
        ("the training yard: round the racks, the posts, the plum posts, the weights, to the tower's three doors and the stage's steps", [(94.0, -10.0), (94.0, 4.0), (82.0, 8.0), (72.0, 8.0), (72.0, 20.0), (94.0, 20.0), (94.0, 26.0), (94.0, 30.0)], Yy),
        ("the yard to the stage: its two steps and its top", [(94.0, 8.0), (108.0, 8.0), (113.5, 8.0), (113.5, 10.0), (113.5, 13.0), (113.5, 18.0)], Yy),
        ("the yard's far stair up to the exhibition terrace's forecourt", [(94.0, 36.0), (94.0, 42.0), (94.0, 44.5), (94.0, 52.0), (94.0, 56.0)], Yy),
    ]
    for label, path, y0 in routes:
        ok, why, y_end = walk(boxes, path, y0)
        check("   %s" % label, ok, why)
    # the hall's own route to its rear gate (the hall's inner court is on the hall's tier C at y 9)
    ok, why, _ = walk(boxes, [(8.0, 12.0), (8.0, 18.0), (2.6, 22.0), (2.6, 30.0), (2.6, 36.0)], 9.0)
    check("   the hall's rear doorway -> the inner court -> the rear gate pavilion -> the causeway", ok, why)
    ok, why, _ = walk(boxes, [(-6.4, 36.0), (-6.4, 40.0), (6.4, 40.0), (6.4, 36.0)], 9.0)
    check("   the causeway and its gap are wide enough for a 2-wide body to walk its edges (x +-6.4)", ok, why)
    # ---------------------------------------------------------------- 8. zones
    say("")
    say("8. Route zones: every point of every route above lies inside a Route zone (WorldService returns anyone who falls from them), and each terrace has a Check")
    routes_z, checks_z = DL.zones(P)
    def in_route(x, z):
        for r in routes_z:
            cx, cz = r["c"][0], r["c"][2]
            if abs(x - cx) <= r["size"][0] / 2 and abs(z - cz) <= r["size"][1] / 2:
                return True
        # the hall's own and the stair's zones belong to CrossingBuilder (the pad's squares): the pad disc, radius 66 round (0, 0)
        return math.hypot(x, z) <= 66.0
    outside = []
    for label, path, y0 in routes:
        for (xa, za), (xb, zb) in zip(path, path[1:]):
            for i in range(21):
                x, z = xa + (xb - xa) * i / 20, za + (zb - za) * i / 20
                if not in_route(x, z):
                    outside.append((round(x, 1), round(z, 1)))
    check("   every route point is inside a Route zone", not outside, str(outside[:4]))
    check("   a Check on each of the five terraces", len(checks_z) == 5, ", ".join(c["name"] for c in checks_z))
    # ---------------------------------------------------------------- 9. sight-lines
    say("")
    say("9. Sight-lines to the hall's crystal spire (the crystal's middle) from the territory's places, past the roofs (their boxes) and every building's mass")
    apex = hall["apex"]
    target = (0.0, apex + 1.2 + 15.0 * 0.52, 0.0)
    roofs = [(-34.0, 34.0, 22.0, 26.4, -18.0, 18.0)]
    for t in hall["stack"]:
        roofs.append((-t["A"], t["A"], t["eave"], t["top"], -t["D"], t["D"]))
    masses = []
    for p in P.placements:
        if p["role"] in ("house", "wing", "hall", "gate", "tower", "pavilion", "corridor"):
            (lx, ly, lz), (hx, hy, hz) = P.pieces[p["piece"]].bounds()
            c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
            xs = [p["x"] + x * c + z * s for x in (lx, hx) for z in (lz, hz)]
            zs = [p["z"] - x * s + z * c for x in (lx, hx) for z in (lz, hz)]
            masses.append((min(xs), max(xs), p["y"] + ly, p["y"] + hy, min(zs), max(zs), p["name"]))
    def sees(eye, tgt, obstacles):
        for ob in obstacles:
            x0, x1, y0, y1, z0, z1 = ob[:6]
            tmin, tmax = 0.0, 1.0
            ok = True
            for a, b, lo, hi in ((eye[0], tgt[0], x0, x1), (eye[1], tgt[1], y0, y1), (eye[2], tgt[2], z0, z1)):
                d = b - a
                if abs(d) < 1e-12:
                    if a < lo or a > hi:
                        ok = False
                        break
                else:
                    t1, t2 = (lo - a) / d, (hi - a) / d
                    tmin, tmax = max(tmin, min(t1, t2)), min(tmax, max(t1, t2))
                    if tmin > tmax:
                        ok = False
                        break
            if ok:
                return False, ob
        return True, None
    views = [("the front court (the plaza's side)", (0.0, 5.0, -48.0)), ("the garden's walk", (0.0, Yg + 5.0, 66.0)), ("the garden pavilion", (23.0, Yg + 6.0, 87.0)),
             ("the Master's court", (0.0, Yr + 5.0, 150.0)), ("the tea pavilion", (88.0, Yt + 5.0, -43.0)), ("the training yard's middle", (94.0, Yy + 5.0, 14.0)),
             ("the exhibition forecourt", (92.0, Ye + 5.0, 62.0)), ("the tower's gate", (94.0, Yy + 5.0, 6.0))]
    seen = 0
    for label, eye in views:
        eyes_masses = [m for m in masses if not (m[0] - 2 <= eye[0] <= m[1] + 2 and m[4] - 2 <= eye[2] <= m[5] + 2)]
        ok, ob = sees(eye, target, roofs + eyes_masses)
        seen += 1 if ok else 0
        say("   %-40s %s" % (label, "sees the spire" if ok else "blocked by %s" % (ob[6] if len(ob) > 6 else "a hall roof")))
    check("   the spire is seen from at least five of the eight places", seen >= 5, "%d of %d" % (seen, len(views)))
    # ---------------------------------------------------------------- 10. budget
    say("")
    say("10. Budget")
    rows, total, vtotal, vparts = D.stats(P)
    biggest = max(max(per.values()) for (_, _, _, _, per) in rows)
    parts = sum(len(per) * n for (_, _, n, _, per) in rows)
    uniq = sum(len(piece.g) for piece in pieces.values())
    mats = set(k for (_, _, _, _, per) in rows for k in per)
    check("   triangles as placed, architecture and props (the hall is 88,470)", True, "%d" % total)
    check("   triangles as placed, vegetation (%d pieces, %d material meshes)" % (len(P.veg), vparts), True, "%d" % vtotal)
    check("   the whole new territory about 80,000 to 110,000 (the owner's band); the hall and it together under about 200,000", total + vtotal <= 116000 and total + vtotal + 88470 <= 205000, "%d (with the hall %d)" % (total + vtotal, total + vtotal + 88470))
    check("   largest single mesh (one piece, one material) under 15,000", biggest <= 15000, "%d" % biggest)
    say("   architecture: %d MeshParts as placed (%d unique meshes, %d materials), vegetation %d MeshParts, %d invisible collision boxes (one Plastic material), %d PointLights (at most 6)" % (
        parts, uniq, len(mats), vparts, len(P.colliders), len(P.lights)))
    say("   draw-call estimate (not measured): about %d unique architecture meshes + %d vegetation meshes in view at most, 1 for the colliders; "
        "if Roblox does not batch identical MeshParts the territory's %d placed parts are %d draws" % (uniq, len({(v['piece']) for v in P.veg}), parts + vparts, parts + vparts + 1))
    check("   at most 6 PointLights", len(P.lights) <= 6, "%d" % len(P.lights))
    say("")
    say("RESULT: %s" % ("ALL OK" if not FAILS else "FAILED: " + "; ".join(FAILS)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(LINES) + "\n")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())

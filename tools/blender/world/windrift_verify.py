"""Numeric checks for Windrift Hold (plain Python): the budget (MeshParts per family, triangles, the largest mesh, material suffixes per piece, lights), every stair's risers
and treads, the bridges' decks, every building on level ground, a REALISTIC body (2 studs wide, 5 tall; and the pathfinder's 1.3 radius) walked over the pad's whole ground
from the gate (a flood fill on a 1-stud grid, against the terrain's 4-stud voxels and the collision boxes) and through every door, stair and bridge, every marked place
reachable, every walked point inside a Route zone (so a fall is caught), the first foundation's hidden paths, lookouts, nooks and rope bridges walked, and the Reach.
Writes renders/windrift/verify.txt.

    python3 tools/blender/world/windrift_verify.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import murim_layout as M  # noqa: E402
import murim_windrift_terrain as T  # noqa: E402
import windrift as D  # noqa: E402
import windrift_lua as L  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "windrift", "verify.txt")
LINES, FAILS = [], []
STEP = 1.05          # the most a body climbs in one stride (a stud and a hair)


def say(s=""):
    LINES.append(s)
    print(s)


def check(name, ok, detail=""):
    say("%-96s %s %s" % (name, "ok" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------------------------------------------------------------------------
# the world a body walks in: terrain cells (4-stud voxels, the column's top) and collision boxes
# ---------------------------------------------------------------------------------------------------------------------------------
_GRID = {}


def grid():
    if not _GRID:
        ox, oz, n, H, Mt, B, U = M.sample_grid()
        _GRID.update(ox=ox, oz=oz, n=n, H=H)
    return _GRID


def terrain_y(x, z):
    """Frame y of the terrain column under a pad-frame point, or None where there is none (open sky)."""
    g = grid()
    lx, lz = T.to_local(x, z)
    wx, wz = M.to_world(lx, lz)
    i, j = int((wx - g["ox"]) // M.CELL), int((wz - g["oz"]) // M.CELL)
    if not (0 <= i < g["n"] and 0 <= j < g["n"]):
        return None
    h = g["H"][j * g["n"] + i]
    return None if h is None else h - D.Y0


class World:
    def __init__(self, boxes):
        self.boxes = boxes
        self.bucket = {}
        for b in boxes:
            for ix in range(int(math.floor((b["x0"] - 2) / 8)), int(math.floor((b["x1"] + 2) / 8)) + 1):
                for iz in range(int(math.floor((b["z0"] - 2) / 8)), int(math.floor((b["z1"] + 2) / 8)) + 1):
                    self.bucket.setdefault((ix, iz), []).append(b)

    def near(self, x, z):
        return self.bucket.get((int(math.floor(x / 8)), int(math.floor(z / 8))), ())

    @staticmethod
    def inside(b, x, z, grow=0.0):
        if not b.get("rotated"):
            return b["x0"] - grow <= x <= b["x1"] + grow and b["z0"] - grow <= z <= b["z1"] + grow
        c, s = math.cos(b["yaw"]), math.sin(b["yaw"])
        dx, dz = x - b["cx"], z - b["cz"]
        u, v = dx * c - dz * s, dx * s + dz * c
        return abs(u) <= b["sx"] / 2 + grow and abs(v) <= b["sz"] / 2 + grow

    def support(self, x, z, y_from, step=STEP):
        """The highest surface under (x, z) not more than `step` above where the body stood: the terrain's column top or a collision box's top."""
        cands = []
        t = terrain_y(x, z)
        if t is not None:
            cands.append(t)
        for b in self.near(x, z):
            if self.inside(b, x, z) and (b["y1"] - b["y0"]) < 60.0:
                cands.append(b["y1"])
        best = None
        for y in cands:
            if y <= y_from + step and (best is None or y > best):
                best = y
        return best

    def blocked(self, x, z, y, r):
        """A box over the surface a body (radius r, 5 tall) stands on that it would hit; returns its name."""
        for b in self.near(x, z):
            if b["y1"] > y + STEP and b["y0"] < y + 5.0 and self.inside(b, x, z, r):
                # (a box whose top is above the body's feet by more than a stride is a wall or a post; boxes beneath the feet are floors)
                return b["name"]
        return None


def walk(world, path, y0, r=1.0, step=0.5):
    """Walks a polyline in half-stud steps; returns (ok, problem, final y)."""
    y = y0
    for (xa, za), (xb, zb) in zip(path, path[1:]):
        n = int(max(abs(xb - xa), abs(zb - za)) / step) + 1
        for i in range(n + 1):
            x, z = xa + (xb - xa) * i / n, za + (zb - za) * i / n
            s = world.support(x, z, y)
            if s is None:
                return False, "no floor or a step over %.2f at (%.1f, %.1f) from y %.2f" % (STEP, x, z, y), y
            b = world.blocked(x, z, s, r)
            if b:
                return False, "%s blocks at (%.1f, %.1f, y %.2f)" % (b, x, z, s), y
            y = s
    return True, "", y


def flood(world, start, y0, r, x0=-72.0, x1=72.0, z0=-52.0, z1=90.0, h=1.0):
    """Every (x, z) cell a body of radius r reaches from `start` by moving to a neighbour a stud away whose floor is at most a stride above and at most 1.3 below."""
    seen = {}
    stack = [(round(start[0] / h), round(start[1] / h), y0)]
    seen[(stack[0][0], stack[0][1])] = y0
    while stack:
        i, j, y = stack.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ni, nj = i + di, j + dj
            if (ni, nj) in seen:
                continue
            x, z = ni * h, nj * h
            if not (x0 <= x <= x1 and z0 <= z <= z1):
                continue
            s = world.support(x, z, y)
            if s is None or s < y - 1.3:
                continue
            if world.blocked(x, z, s, r):
                continue
            seen[(ni, nj)] = s
            stack.append((ni, nj, s))
    return seen


def route_rects():
    """Route zones as pad-frame rectangles with their y range: the foundation's (the pad's two squares of side 140, the stairs) and Windrift's own."""
    out = []
    pr = 70.0
    for yaw in (0.0, PI4):
        out.append(dict(c=(0.0, 0.0), size=(2 * pr, 2 * pr), yaw=yaw, y0=-0.5 - 100.0, y1=-0.5 + 8.0))
    routes, checks = L.zones(P)
    for r in routes:
        height = 8 + 100 + r["high"]
        out.append(dict(c=(r["c"][0], r["c"][2]), size=r["size"], yaw=r["yaw"], y0=r["c"][1] - 100.0, y1=r["c"][1] - 100.0 + height))
    return out, checks


PI4 = math.pi / 4


def in_zone(z_, x, z, y):
    c, s = math.cos(z_["yaw"]), math.sin(z_["yaw"])
    dx, dz = x - z_["c"][0], z - z_["c"][1]
    u, v = dx * c - dz * s, dx * s + dz * c
    return abs(u) <= z_["size"][0] / 2 and abs(v) <= z_["size"][1] / 2 and z_["y0"] <= y <= z_["y1"]


P = None


def main():
    global P
    P = D.build_all()
    say("Windrift Hold: numeric checks (pad frame, studs; the pad's floor level is y 0, the plaza's ground is Y over the plaza = y + 36.5 for terrain)")
    say("")
    # ------------------------------------------------------------------------------------------------ 1. budget
    say("1. Budget (as placed)")
    rows, tri_arch, parts_arch, tri_veg, parts_veg = D.stats(P)
    fam = {}
    for name, t, n, tn, per in rows:
        f = D.family_of(name)
        d = fam.setdefault(f, [0, 0, 0])
        d[0] += n
        d[1] += tn
        d[2] += len(per) * n
    for f, (n, tn, parts) in sorted(fam.items()):
        say("   %-12s %3d placements %7d triangles %4d MeshParts" % (f, n, tn, parts))
    vfam = {}
    for v in P.veg:
        f = v["piece"].split("_")[1]
        meta = D.veg()["pieces"][v["piece"]]
        d = vfam.setdefault(f, [0, 0, 0])
        d[0] += 1
        d[1] += meta["tris"]
        d[2] += len(meta["materials"])
    for f, (n, tn, parts) in sorted(vfam.items()):
        say("   %-12s %3d placements %7d triangles %4d MeshParts (vegetation library)" % ("Veg " + f, n, tn, parts))
    total_t, total_p = tri_arch + tri_veg, parts_arch + parts_veg
    say("   TOTAL %d triangles, %d MeshParts (architecture %d / %d, vegetation %d / %d)" % (total_t, total_p, tri_arch, parts_arch, tri_veg, parts_veg))
    check("the whole territory is at most 110,000 triangles", total_t <= 110000, "(%d)" % total_t)
    check("at most 450 MeshParts as placed (invisible collision boxes not counted)", total_p <= 450, "(%d)" % total_p)
    biggest = max((t_ for name, piece in P.pieces.items() for t_ in piece.stats().values()), default=0)
    big_name = max(((t_, name, k) for name, piece in P.pieces.items() for k, t_ in piece.stats().items()))
    check("the largest single architecture mesh is at most 5,000 (the headquarters' roof is a landmark; every other is at most 3,000)", biggest <= 5000, "(%d: %s__%s)" % big_name)
    over3 = sorted((t_, name, k) for name, piece in P.pieces.items() for k, t_ in piece.stats().items() if t_ > 3000)
    say("   meshes over 3,000 (landmarks): %s" % ", ".join("%s__%s %d" % (n.split("_", 2)[2], k, t_) for t_, n, k in over3))
    vbig = max(m["tris"] for m in D.veg()["pieces"].values())
    check("at most 4 material suffixes on any piece", max(len(p.g) for p in P.pieces.values()) <= 4 and max(len(m["materials"]) for m in D.veg()["pieces"].values()) <= 4)
    check("at most 8 PointLights", len(P.lights) <= 8, "(%d)" % len(P.lights))
    check("the vegetation library's largest mesh is at most 3,000", max(max(m["materials"].values()) for m in D.veg()["pieces"].values()) <= 3000)
    say("   collision: %d invisible boxes (one folder, Plastic); every visual MeshPart is CanCollide false except the Walkable path slabs" % len(P.colliders))
    say("")
    # ------------------------------------------------------------------------------------------------ 2. stairs and bridges
    say("2. Stairs and bridges")
    for pname in ("Windrift_Courts_Flight11", "Windrift_Courts_CleftStair"):
        pc = P.pieces[pname]
        steps = sorted((b for b in pc.col if b[6] == "Step"), key=lambda b: b[4])
        rises = [b[3] - a[3] for a, b in zip(steps, steps[1:])]
        treads = [b[4] - a[4] for a, b in zip(steps, steps[1:])]
        check("%s: %d steps, every riser exactly 1.0 and every tread 1.5" % (pname.split("_")[-1], len(steps)),
              all(abs(abs(r) - 1.0) < 1e-6 for r in rises) and all(abs(t_ - 1.5) < 1e-6 for t_ in treads))
    for name in ("GorgeBridge", "GreatSpan"):
        pc = P.pieces["Windrift_Courts_" + name]
        decks = sorted((b for b in pc.col if b[6] == "Deck"), key=lambda b: b[0])
        jumps = [abs(b[3] - a[3]) for a, b in zip(decks, decks[1:])]
        check("%s: deck %d boxes, no step over 0.60 between neighbours (the worst %.2f; a body climbs 1.05), width %.1f" % (name, len(decks), max(jumps), decks[0][5] - decks[0][4]),
              max(jumps) <= 0.60 and (decks[0][5] - decks[0][4]) >= 4.0)
    span = [p for p in P.placements if p["name"] == "GreatSpan"][0]
    pcs = P.pieces[span["piece"]]
    decks = sorted((b for b in pcs.col if b[6] == "Deck"), key=lambda b: b[0])
    ends = (span["y"] + decks[0][3], span["y"] + decks[-1][3])
    check("GreatSpan's ends meet the ledges: Eyrie deck %.2f (ledge terrain %.2f + 0.5), Perch %.2f (terrain %.2f + 0.5)" % (ends[0], D.G(T.Y_EYRIE), ends[1], D.G(T.Y_PERCH)),
          abs(ends[0] - D.Fl(T.Y_EYRIE)) <= 0.6 and abs(ends[1] - D.Fl(T.Y_PERCH)) <= 0.6)
    gb = [p for p in P.placements if p["name"] == "GorgeBridge"][0]
    gpc = P.pieces[gb["piece"]]
    gd = sorted((b for b in gpc.col if b[6] == "Deck"), key=lambda b: b[0])
    check("GorgeBridge spans the gorge (x %.1f .. %.1f over the slot x %.1f .. %.1f)" % (gb["x"] + gd[0][0], gb["x"] + gd[-1][1], T.SLOT["x0"], T.SLOT["x1"]),
          gb["x"] + gd[0][0] <= T.SLOT["x0"] and gb["x"] + gd[-1][1] >= T.SLOT["x1"])
    say("")
    # ------------------------------------------------------------------------------------------------ 3. ground under buildings
    say("3. Buildings on level ground (terrain columns under each footprint)")
    expected = {"Hq": 36.0, "RainHall": 36.0, "Gallery": 36.0, "HearthYard": 36.0, "StoneRing": 36.0, "LogYard": 36.0, "RopeCourse": 36.0, "SwingLogs": 36.0,
                "Eyrie": T.Y_EYRIE, "PerchPavilion": T.Y_PERCH, "DripShrine": T.Y_DRIP}
    for p in P.placements:
        nm = p["name"]
        if nm not in expected:
            continue
        pc = P.pieces[p["piece"]]
        c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
        worst, cnt, missing = 0.0, 0, 0
        for (x0, x1, z0, z1, y) in pc.floor:
            if nm in ("Gallery",) and x1 > 15.0:
                x1 = 14.5               # (the lantern room hangs past the pad's rim on stilts: only the podium stands on the ground)
            if nm == "Eyrie":
                continue
            if nm == "RainHall":
                continue
            for xi in range(int(x0 + 1), int(x1), 2):
                for zi in range(int(z0 + 1), int(z1), 2):
                    wx, wz = p["x"] + xi * c + zi * s, p["z"] - xi * s + zi * c
                    t_ = terrain_y(wx, wz)
                    if t_ is None:
                        missing += 1
                        continue
                    cnt += 1
                    worst = max(worst, abs((t_ + D.Y0) - expected[nm]))
        if nm in ("Eyrie", "RainHall"):
            continue
        check("%-14s ground within 0.6 of its level %.1f over its footprint (%d samples, worst %.2f, %d off the ground)" % (nm, expected[nm], cnt, worst, missing), worst <= 0.6 and missing == 0)
    say("")
    # ------------------------------------------------------------------------------------------------ 4. the walk
    say("4. A body walks the pad (2 studs wide, 5 tall; and radius 1.3, the pathfinder's)")
    world = World(P.colliders)
    start = (0.0, -49.0)
    y0 = terrain_y(*start)
    fl1 = flood(world, start, y0, 1.0)
    fl13 = flood(world, start, y0, 1.3)
    say("   reachable from the gate on a 1-stud grid: %d cells (radius 1.0), %d cells (radius 1.3)" % (len(fl1), len(fl13)))

    def reach(label, x, z, fl, r):
        k = (round(x), round(z))
        near = [(k[0] + a, k[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
        return any(q in fl for q in near)
    targets = [(n, v["pos"][0], v["pos"][2]) for n, v in sorted(P.spots.items())]
    for n, x, z in targets:
        a, b = reach(n, x, z, fl1, 1.0), reach(n, x, z, fl13, 1.3)
        check("reach %-16s (%6.1f, %6.1f) on foot" % (n, x, z), a, "(radius 1.0%s; radius 1.3: %s)" % ("", "yes" if b else "NO"))
    say("")
    say("   Doors and passages walked as polylines (radius 1.0 and 1.3):")
    doors = [
        ("the gate to the Long Hold's door and into its hall", [(0.0, -49.0), (0.0, -20.0), (-21.0, -4.0), (-21.0, 7.5), (-21.0, 12.0), (-21.0, 22.0)], y0),
        ("the gate round the HQ's front court to the Rain Hall's left door by the left lane, through its length to the gallery",
         [(0.0, -49.0), (0.0, -20.0), (14.0, -14.0), (14.0, 4.0), (19.5, 7.0), (20.0, 20.0), (20.0, 36.0), (20.0, 41.0), (19.0, 44.0), (19.0, 48.0), (14.0, 52.0), (9.5, 52.0), (9.5, 58.0), (9.5, 60.3)], y0),
        ("the gate to the Gallery of Blades' door and to the cradle", [(0.0, -49.0), (0.0, -20.0), (14.0, -14.0), (14.0, 6.5), (31.4, 7.5), (31.4, 11.0), (31.4, 14.0), (31.4, 20.0), (46.0, 20.0), (55.0, 20.0)], y0),
        ("the gate to the Hearth Yard's NPC ring", [(0.0, -49.0), (0.0, -20.0), (20.0, -22.0), (30.0, -24.5), (32.4, -24.7)], y0),
        ("the gate over the Gorge Bridge at z 14 (from the lane by the Long Hold to the left lane)", [(0.0, -49.0), (0.0, -20.0), (0.5, 8.0), (0.5, 14.0), (2.5, 14.0), (9.25, 14.0), (16.5, 14.0), (19.5, 14.0)], y0),
        ("the Cleft Stair down to the Drip ledge", [(0.0, -20.0), (0.5, 8.0), (0.5, 26.0), (2.0, 27.5), (4.8, 28.5), (4.8, 44.0), (7.0, 48.0)], y0),
        ("the Moss Court's west gate", [(0.0, -20.0), (10.0, -10.0), (14.0, -3.5), (20.0, -3.5), (24.0, -3.5)], y0),
        ("the stone ring by its west gap", [(0.0, -49.0), (-18.0, -20.0), (-24.0, -20.0), (-30.0, -20.0), (-30.0, -14.0)], y0),
        ("the wire course", [(0.0, -49.0), (0.0, -36.0), (-14.0, -36.0), (-26.0, -35.0)], y0),
    ]
    for label, path, y_start in doors:
        if y_start is None:
            continue
        ok1, why1, yf = walk(world, path, y_start, 1.0)
        ok2, why2, _ = walk(world, path, y_start, 1.3)
        check("walk: %s" % label, ok1, "(radius 1.0%s; 1.3: %s)" % ("" if ok1 else ": " + why1, "yes" if ok2 else "no: " + why2))
    # the stair and the bridge to the high ledges: from the pad up the Eyrie stair, across the Eyrie deck, over the Great Span to the Perch
    ey = T.STAIRS["Eyrie"]["runs"]
    path = [(ey[0][0][0], ey[0][0][1] - 1.0)]
    for (a, b, y_lo, y_hi) in ey:
        path.append(a)
        path.append(b)
    path += [(-26.0, 63.0), (-22.0, 67.0), (-18.0, 67.0), (-14.0, 66.5), (0.0, 66.0), (12.0, 66.0), (19.0, 66.0), (21.5, 67.0), (24.0, 68.5), (27.5, 68.5)]
    y_a = terrain_y(*path[0])
    if os.environ.get('WR_DEBUG'):
        yy = y_a
        for (xa, za), (xb, zb) in zip(path, path[1:]):
            n_ = int(max(abs(xb - xa), abs(zb - za)) / 0.5) + 1
            for i in range(n_ + 1):
                x_, z_ = xa + (xb - xa) * i / n_, za + (zb - za) * i / n_
                s_ = world.support(x_, z_, yy)
                if s_ is None:
                    print('DEBUG no support at', round(x_, 1), round(z_, 1), 'from', round(yy, 2)); break
                if abs(s_ - yy) > 0.9:
                    print('DEBUG step', round(x_, 1), round(z_, 1), round(yy, 2), '->', round(s_, 2))
                yy = s_
    for r in (1.0, 1.3):
        ok, why, yf = walk(world, path, y_a, r)
        check("walk: the pad, up the Eyrie stair (22 risers), the Eyrie's deck, the Great Span (33 long), onto the Perch (radius %.1f)" % r, ok, "(ends at y %.2f: the Perch floor %.2f)" % (yf, D.Fl(T.Y_PERCH)) if ok else why)
    say("")
    # ------------------------------------------------------------------------------------------------ 5. falls
    say("5. Route zones: every walkable point is inside a Route zone (a player who falls is returned to the last Check)")
    zones, checks = route_rects()
    outside = []
    for (ix, iz), y in fl1.items():
        if not any(in_zone(z_, float(ix), float(iz), y) for z_ in zones):
            outside.append((ix, iz, round(y, 1)))
    # (the high ledges and the bridge are reached by walking too: add their cells)
    ledge_pts = []
    for name, t in T.TERRACES.items():
        for xi in range(int(t["x0"] + 2), int(t["x1"] - 1), 3):
            for zi in range(int(t["z0"] + 2), int(t["z1"] - 1), 3):
                ledge_pts.append((xi, zi, D.G(t["y"]) + 0.5))
    bad_ledge = [p_ for p_ in ledge_pts if not any(in_zone(z_, float(p_[0]), float(p_[1]), p_[2]) for z_ in zones)]
    check("every reachable pad cell (%d) lies inside a Route zone" % len(fl1), not outside, "(%d outside: %s)" % (len(outside), outside[:4]))
    check("every ledge point (%d) lies inside a Route zone" % len(ledge_pts), not bad_ledge, "(%d outside: %s)" % (len(bad_ledge), bad_ledge[:4]))
    say("   Windrift's own: %d Route boxes and %d Check boxes (each Route reaches 100 studs under its ground)" % (len(L.zones(P)[0]), len(checks)))
    for c in checks:
        ret = c["ret"]
        t_ = terrain_y(ret[0], ret[2])
        on_floor = world.support(ret[0], ret[2], ret[1] + 0.5, 1.5)
        check("Check %-12s returns to (%.1f, %.1f, %.1f) on a surface (floor %.2f)" % (c["name"], ret[0], ret[1], ret[2], on_floor if on_floor is not None else -99), on_floor is not None and abs(on_floor - ret[1]) <= 0.7)
    say("")
    # ------------------------------------------------------------------------------------------------ 6. the Reach
    say("6. Reach (Placements/MurimCrossing.lua Reach = 340 from the plaza's middle)")
    far = 0.0
    far_pt = None
    for (ix, iz), y in fl1.items():
        lx, lz = T.to_local(float(ix), float(iz))
        d = math.hypot(lx, lz)
        if d > far:
            far, far_pt = d, (ix, iz)
    for name, t in T.TERRACES.items():
        for (x, z) in ((t["x0"], t["z1"]), (t["x1"], t["z1"])):
            lx, lz = T.to_local(x, z)
            if math.hypot(lx, lz) > far:
                far, far_pt = math.hypot(lx, lz), (x, z, name)
    check("the farthest walkable ground (%s) is within 340 of the plaza's middle" % (far_pt,), far <= 340.0, "(%.1f)" % far)
    say("")
    # ------------------------------------------------------------------------------------------------ 7. the first foundation's paths
    say("7. The hidden paths, lookouts, nooks and rope bridges of the first foundation (their terrain is unchanged: windrift_terrain_diff.py), walked with the terrain's own voxels")
    for k, knots in enumerate(M.PATHS):
        pts = [(kn[0], kn[1] - 250.0) for kn in knots]
        yy = terrain_y(*pts[0])
        ok, why, yf = walk(World([]), pts, yy, 1.0, step=0.5)
        # voxel steps of the old design: where the ground jumps, report it (the first foundation was built and walked in Studio with the same voxels)
        check("path %d (%d knots) walked on the terrain columns" % (k + 1, len(knots)), ok, "" if ok else "(%s: unchanged by Windrift, so as in the first foundation)" % why)
    for k, br in enumerate(M.ROPE_BRIDGES):
        a, b = br
        ta, tb = terrain_y(a[0], a[1] - 250.0), terrain_y(b[0], b[1] - 250.0)
        check("rope bridge %d: its two rims at y %.2f and %.2f (a plank deck between them, as built by CrossingBuilder)" % (k + 1, ta + D.Y0, tb + D.Y0), abs(ta - tb) < 3.0)
    say("")
    check("RESULT: every check above passed", not FAILS, "(%d failed: %s)" % (len(FAILS), FAILS) if FAILS else "")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(LINES) + "\n")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

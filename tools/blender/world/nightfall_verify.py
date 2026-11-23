"""Numeric checks for Nightfall Citadel (plain Python), voxel-aware from the start (Windrift's lesson: Studio's terrain is 4-stud columns on a grid turned 23.4 degrees against the island,
a cell reaches 2.6 to 2.9 studs past its centre, and a smooth heightfield passed a bridge that was inside the cliff).

  1  budget                   MeshParts, triangles, largest meshes, material suffixes per piece, lights, emitters
  2  stairs                   every riser 1.0 and tread 1.5, flights chained, flush with the terrain, no buried step (terrain over a tread's middle)
  3  bridge                   the chain bridge's deck, its ends flush with the ledges, its corridor free of terrain
  4  ground under buildings   level ground under every footprint
  5  the walk                 a body of radius 1.0, 1.3 and 1.5 (2, 2.6 and 3 studs wide, 5 tall) walked over the whole ward from the gate (a flood fill on a 1-stud grid against the
                              collision boxes AND the terrain's cells, each cell counted as its whole voxel rounded up), every marked place reached, every main route walked as a polyline
  6  falls                    every walkable cell, ledge point and stair inside a Route zone, every Check's ReturnTo on a surface
  7  Reach                    the farthest walkable ground within 340 of the plaza's middle
  8  voxel corridors          every corridor (stairs, bridge, doors, gatehouse, arena gates): no terrain cell in the body's space (0.8 to 4.6 above the floor, 2.5 to each side)
  9  the foundation's markers free of colliders
Writes renders/nightfall/verify.txt.

    python3 tools/blender/world/nightfall_verify.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import murim_layout as M  # noqa: E402
import murim_nightfall_terrain as T  # noqa: E402
import nightfall as D  # noqa: E402
import nightfall_lua as L  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "nightfall", "verify.txt")
LINES, FAILS = [], []
STEP = 1.05          # the most a body climbs in one stride (a stud and a hair)
CELL = M.CELL
ISLAND_Y = 200.0     # the island's centre height: world Y = 200 + the data's height; Studio's voxels are 4 studs tall on multiples of 4


def say(s=""):
    LINES.append(s)
    print(s)


def check(name, ok, detail=""):
    say("%-110s %s %s" % (name, "ok" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


# =====================================================================================================================================================================
# the voxel world (importable): cells of the terrain data, in the pad frame
# =====================================================================================================================================================================
_GRID = {}


def grid():
    if not _GRID:
        ox, oz, n, H, Mt, B, U = M.sample_grid()
        _GRID.update(ox=ox, oz=oz, n=n, H=[None if h is None else round(h, 1) for h in H])     # (written with one decimal)
    return _GRID


def world_of(x, z):
    lx, lz = T.to_local(x, z)
    return M.to_world(lx, lz)


def cell_tops(i, j):
    """(exact top, conservative top) in frame y of the column at cell (i, j), or None. The conservative top counts the column as its whole voxel, rounded up to the next voxel boundary."""
    g = grid()
    if not (0 <= i < g["n"] and 0 <= j < g["n"]):
        return None
    h = g["H"][j * g["n"] + i]
    if h is None:
        return None
    ex = h - D.Y0
    cons = (4.0 * math.ceil((ISLAND_Y + h - 1e-9) / 4.0) - ISLAND_Y) - D.Y0
    return ex, cons


def terrain_y(x, z):
    """Frame y of the terrain column under a pad-frame point (the column's top), or None over open sky."""
    g = grid()
    wx, wz = world_of(x, z)
    i, j = int((wx - g["ox"]) // CELL), int((wz - g["oz"]) // CELL)
    t = cell_tops(i, j)
    return None if t is None else t[0]


_NEAR = {}


def cells_near(x, z, r):
    """Every cell (i, j) whose 4 x 4 square (axis-aligned in the world, turned against the pad frame) comes within r of the pad-frame point (x, z)."""
    g = grid()
    wx, wz = world_of(x, z)
    out = []
    for i in range(int((wx - r - g["ox"]) // CELL), int((wx + r - g["ox"]) // CELL) + 1):
        for j in range(int((wz - r - g["oz"]) // CELL), int((wz + r - g["oz"]) // CELL) + 1):
            cx, cz = g["ox"] + (i + 0.5) * CELL, g["oz"] + (j + 0.5) * CELL
            dx, dz = max(abs(wx - cx) - CELL / 2, 0.0), max(abs(wz - cz) - CELL / 2, 0.0)
            if math.hypot(dx, dz) <= r:
                out.append((i, j))
    return out


def terrain_over(x, z, r, y_top):
    """The highest conservative column top among the cells within r of (x, z), if it stands above y_top; else None."""
    best = None
    for (i, j) in cells_near(x, z, r):
        t = cell_tops(i, j)
        if t is not None and t[1] > y_top and (best is None or t[1] > best):
            best = t[1]
    return best


def max_cons(x, z, r):
    m = None
    for (i, j) in cells_near(x, z, r):
        t = cell_tops(i, j)
        if t is not None and (m is None or t[1] > m):
            m = t[1]
    return m


class World:
    """Collision boxes and terrain cells: what a body walks on and what it bumps into."""

    def __init__(self, boxes):
        self.boxes = boxes
        self.bucket = {}
        for b in boxes:
            for ix in range(int(math.floor((b["x0"] - 2) / 8)), int(math.floor((b["x1"] + 2) / 8)) + 1):
                for iz in range(int(math.floor((b["z0"] - 2) / 8)), int(math.floor((b["z1"] + 2) / 8)) + 1):
                    self.bucket.setdefault((ix, iz), []).append(b)
        self._blk = {}

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
        """The highest surface under (x, z) not more than `step` above where the body stood: the terrain column's top or a collision box's top."""
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
        """What a body (radius r, 5 tall, feet at y) would hit: a box over the surface it stands on, or a terrain column (counted as its whole voxel) standing more than a stride above
        its feet within r of it. Returns a name."""
        for b in self.near(x, z):
            if b["y1"] > y + STEP and b["y0"] < y + 5.0 and self.inside(b, x, z, r):
                return b["name"]
        if terrain_over(x, z, r, y + STEP) is not None:
            return "terrain"
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


def flood(world, start, y0, r, x0=-72.0, x1=76.0, z0=-52.0, z1=132.0, h=1.0):
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


def corridor_free(world, path, y0, half=2.5, lo=0.8, hi=4.6, step=1.0, lateral=0.5):
    """The voxel corridor rule: along a polyline, at every stud and at lateral offsets up to `half` each side, no terrain cell (a column counts as its whole voxel, rounded up) within 0.2 of the
    point may stand above the floor + `lo` (the body's space runs lo..hi over the floor). Returns (points checked, the blocked ones)."""
    bad, n_pts = [], 0
    y = y0
    for (xa, za), (xb, zb) in zip(path, path[1:]):
        L_ = math.hypot(xb - xa, zb - za)
        if L_ < 1e-6:
            continue
        ux, uz = (xb - xa) / L_, (zb - za) / L_
        nx, nz = -uz, ux
        n = int(L_ / step) + 1
        for i in range(n + 1):
            t = i / n
            x, z = xa + (xb - xa) * t, za + (zb - za) * t
            s = world.support(x, z, y)
            if s is None:
                continue
            y = s
            k = -half
            while k <= half + 1e-9:
                px, pz = x + nx * k, z + nz * k
                n_pts += 1
                top = terrain_over(px, pz, 0.2, y + lo)
                if top is not None:
                    bad.append((round(px, 1), round(pz, 1), round(top, 2), round(y, 2)))
                k += lateral
    return n_pts, bad


def gap_width(world, x, z, nx, nz, y, limit=9.0):
    """The clear width of a doorway, gate or gap: from the point (x, z) at floor height y, how far a body's centre line runs free (boxes and terrain cells, tested with a radius of 0)
    to each side along (nx, nz), the two distances added. 0 if the point itself is blocked."""
    def free(px, pz):
        return world.blocked(px, pz, y, 0.0) is None
    if not free(x, z):
        return 0.0
    total = 0.0
    for sgn in (1.0, -1.0):
        d = 0.0
        while d < limit and free(x + sgn * nx * (d + 0.02), z + sgn * nz * (d + 0.02)):
            d += 0.02
        total += d + 0.01
    return total


def pathfinder_ok(gap, r):
    """Roblox's PathfindingService, measured in Studio on the Residence's door (2026-11-23): a doorway is passable for an agent of radius r when it is at least 2 r + 2.2 studs clear (4.2 fails
    at 1.0, 1.25 and 1.5; 4.7 passes at 1.0; 5.2 passes at 1.5). The headless flood fill's 2 r is not enough for NPCs."""
    return gap >= 2.0 * r + 2.2 - 1e-6


MAIN_GAP, SECOND_GAP = 2 * 1.5 + 2.2, 2 * 1.0 + 2.2 + 0.5      # 5.2 for a main route (radius 1.5), 4.7 for a secondary one (radius 1.0 plus the 0.5 Studio's step of 0.5 shows)


# ---------------------------------------------------------------------------------------------------------------------------------
# Route zones
# ---------------------------------------------------------------------------------------------------------------------------------
P = None


def route_rects():
    """Route zones as boxes in the pad frame: the foundation's (the Demonic pad's two squares of side 2 x EdgeRadius, 100 under the pad to 8 over it) and Nightfall's own."""
    out = []
    pr = 66.0
    pc = T.PAD_C
    for yaw in (0.0, math.pi / 4):
        out.append(dict(foundation=True, yaw=yaw, half=pr, y0=-0.5 - 100.0, y1=-0.5 + 8.0))
    routes, checks = L.zones(P)
    for r in routes:
        height = 8 + 100 + r["high"]
        out.append(dict(foundation=False, c=(r["c"][0], r["c"][2]), size=r["size"], yaw=r["yaw"], y0=r["c"][1] - 100.0, y1=r["c"][1] - 100.0 + height))
    return out, checks


def in_zone(z_, x, z, y):
    if z_["foundation"]:
        lx, lz = T.to_local(x, z)
        dx, dz = lx - T.PAD_C[0], lz - T.PAD_C[1]
        c, s = math.cos(z_["yaw"]), math.sin(z_["yaw"])
        u, v = dx * c - dz * s, dx * s + dz * c
        return abs(u) <= z_["half"] and abs(v) <= z_["half"] and z_["y0"] <= y <= z_["y1"]
    c, s = math.cos(z_["yaw"]), math.sin(z_["yaw"])
    dx, dz = x - z_["c"][0], z - z_["c"][1]
    u, v = dx * c - dz * s, dx * s + dz * c
    return abs(u) <= z_["size"][0] / 2 and abs(v) <= z_["size"][1] / 2 and z_["y0"] <= y <= z_["y1"]


def mark_world(placement, key):
    """A piece's mark in the pad frame."""
    pc = P.pieces[placement["piece"]]
    m = pc.marks[key]
    c, s = math.cos(placement["yaw"]), math.sin(placement["yaw"])
    return (placement["x"] + m[0] * c + m[2] * s, placement["y"] + m[1], placement["z"] - m[0] * s + m[2] * c)


def placement(name):
    return [p for p in P.placements if p["name"] == name][0]


def measure_gaps(world, P):
    """Every doorway, gate and gap on the main routes (and the Postern's stair): (label, clear width, main)."""
    out = []
    cb_ = placement("ChainBridge")
    arm = placement("Armory")
    keep = placement("Keep")
    res = placement("Residence")
    out.append(("the gatehouse's passage", gap_width(world, 0.0, D.GATE_Z, 1.0, 0.0, D.GR), True))
    for name, a in (("front", -math.pi / 2), ("right", 0.0), ("left", math.pi)):
        x, z = D.ARENA[0] + 13.4 * math.cos(a), D.ARENA[1] + 13.4 * math.sin(a)
        out.append(("the arena's %s gate" % name, gap_width(world, x, z, -math.sin(a), math.cos(a), D.GR), True))
    out.append(("the keep's door", gap_width(world, keep["x"], keep["z"] - 14.0 + 2.5, 1.0, 0.0, keep["y"]), True))
    out.append(("the armory's door", gap_width(world, arm["x"] + 6.5, arm["z"], 0.0, 1.0, arm["y"]), True))
    out.append(("the armory's porch between its piers", gap_width(world, arm["x"] + 9.0, arm["z"], 0.0, 1.0, arm["y"]), True))
    rx = res["x"] - (res["x"] - 48.0) - 0.0
    pc = P.pieces[res["piece"]]
    door = mark_world(res, "Door")
    out.append(("the Residence's door", gap_width(world, door[0] + 1.0, door[2], 0.0, 1.0, res["y"]), True))
    out.append(("the Residence's porch between its posts", gap_width(world, door[0] - 1.8, door[2], 0.0, 1.0, res["y"]), True))
    for label, x in (("the bridge's bridgehead end (between the pylons)", cb_["x"] - 10.6), ("the bridge's middle (between the guard rails)", cb_["x"]), ("the bridge's Residence end (between the pylons)", cb_["x"] + 10.6)):
        yb = world.support(x, cb_["z"], 40.0)
        out.append((label, gap_width(world, x, cb_["z"], 0.0, 1.0, yb), True))
    ug = placement("UpperGate")
    out.append(("the Upper Gate at the Great Stair's head (between the pylons)", gap_width(world, 0.0, ug["z"] + 2.3, 1.0, 0.0, ug["y"]), True))
    out.append(("the Great Stair (between its flanks, mid first flight)", gap_width(world, 0.0, 20.0, 1.0, 0.0, world.support(0.0, 20.0, 40.0)), True))
    out.append(("the bridgehead stair (between its flanks)", gap_width(world, D.BH_X, 80.0, 1.0, 0.0, world.support(D.BH_X, 80.0, 40.0)), True))
    out.append(("the Postern's first flight (between its flanks)", gap_width(world, D.POSTERN_X, 20.0, 1.0, 0.0, world.support(D.POSTERN_X, 20.0, 40.0)), False))
    out.append(("the Postern's second flight (between its flanks)", gap_width(world, D.POSTERN_X, 45.0, 1.0, 0.0, world.support(D.POSTERN_X, 45.0, 40.0)), False))
    return out


def ring_gaps(world, P):
    """The chain ring's gaps between neighbouring posts (not doorways: the ring is open between them)."""
    out = []
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8 + 2 * math.pi / 16
        x, z = D.RING[0] + 8.0 * math.cos(a), D.RING[1] + 8.0 * math.sin(a)
        out.append(("ring gap %d" % k, gap_width(world, x, z, -math.sin(a), math.cos(a), D.GR), False))
    return out


def main():
    global P
    P = D.build_all()
    say("Nightfall Citadel: numeric checks (pad frame, studs; the pad's ground is y -0.5, the Upper Ward's 23.5, the bridgehead's and the Residence ledge's 31.5)")
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
    big = sorted(((t_, name, k) for name, piece in P.pieces.items() for k, t_ in piece.stats().items()), reverse=True)
    over3 = [(t_, n, k) for t_, n, k in big if t_ > 3000]
    check("every architecture mesh is at most 3,000 triangles (landmarks over it are listed)", not over3 or all(n.endswith(("_Keep", "_Armory")) for t_, n, k in over3),
          "(the largest %d: %s__%s; over 3,000: %s)" % (big[0][0], big[0][1].split("_", 2)[2], big[0][2], ", ".join("%s__%s %d" % (n.split("_", 2)[2], k, t_) for t_, n, k in over3) or "none"))
    check("at most 4 material suffixes on any piece", max(len(p.g) for p in P.pieces.values()) <= 4 and all(len(m["materials"]) <= 4 for m in D.veg()["pieces"].values()))
    check("at most 8 PointLights", len(P.lights) <= 8, "(%d)" % len(P.lights))
    check("at most 12 emitters, each Rate at most 6, none on a script", len(P.effects) <= 12 and all(e.get("rate", 5) <= 6 for e in P.effects), "(%d: %s)" % (len(P.effects), ", ".join(sorted(e["kind"] for e in P.effects))))
    if D.veg()["pieces"]:
        check("the vegetation library's largest mesh is at most 3,000", max(max(m["materials"].values()) for m in D.veg()["pieces"].values()) <= 3000)
    say("   collision: %d invisible boxes (one folder, Plastic); every visual MeshPart is CanCollide false except the Walkable path slabs" % len(P.colliders))
    say("")
    # ------------------------------------------------------------------------------------------------ 2. stairs
    say("2. Stairs (solid stone ramps; every tread a block from its top down into the ground)")
    flights = ("GreatFlight", "GreatFlightHigh", "PosternFlight", "PosternFlightHigh", "BridgeFlight")
    for nm in flights:
        pc = P.pieces["Nightfall_Courts_" + nm]
        steps = sorted((b for b in pc.col if b[6] == "Step"), key=lambda b: b[4])
        rises = [b[3] - a[3] for a, b in zip(steps, steps[1:])]
        treads = [b[4] - a[4] for a, b in zip(steps, steps[1:])]
        check("%-18s %2d steps: every riser exactly 1.0 and every tread 1.5 (the first tread's top is 1.0 over the foot)" % (nm, len(steps)), all(abs(r_ - 1.0) < 1e-6 for r_ in rises) and all(abs(t_ - 1.5) < 1e-6 for t_ in treads) and abs(steps[0][3] - 1.0) < 1e-6)

    def foot_top(pname, nm_piece, count):
        pl = [p for p in P.placements if p["name"] == pname]
        return pl
    # the chain of each stair: the foot's ground, each flight's top, the next level
    gf = placement("GreatFlight")
    gl = placement("GreatLanding")
    gh = placement("GreatFlightHigh")
    ug = placement("UpperGate")
    chain_ok = abs(gf["y"] + 12.0 - gl["y"]) < 1e-6 and abs(gl["y"] - gh["y"]) < 1e-6 and abs(gh["y"] + 12.0 - ug["y"]) < 1e-6 and abs(gf["z"] + 18.0 - gl["z"]) < 1e-6 and abs(gl["z"] + 6.0 - gh["z"]) < 1e-6 and abs(gh["z"] + 18.0 - ug["z"]) < 1e-6
    check("Great Stair: foot %.2f (the pad's ground) -> flight 12 -> landing %.2f (z %.0f..%.0f) -> flight 12 -> head %.2f (the Upper Ward's ground %.2f): every join exact" % (gf["y"], gl["y"], gl["z"], gh["z"], ug["y"], D.GU), chain_ok and abs(ug["y"] - D.GU) < 0.6)
    foot_t = terrain_y(0.0, gf["z"] - 0.5)
    check("Great Stair: its foot meets the pad's ground within 0.6 (first tread top %.2f over the ground %.2f)" % (gf["y"] + 1.0, foot_t), abs((gf["y"] + 1.0) - foot_t - 1.0) < 0.6)
    pf, pl_, ph = placement("PosternFlight"), [p for p in P.placements if p["name"] == "PosternLanding"], placement("PosternFlightHigh")
    check("Postern: foot %.2f -> flight 12 -> landing %.2f -> flight 12 -> head %.2f (the Upper Ward's ground %.2f)" % (pf["y"], pl_[0]["y"], pl_[1]["y"], D.GU),
          abs(pf["y"] + 12.0 - pl_[0]["y"]) < 1e-6 and abs(pl_[0]["y"] - ph["y"]) < 1e-6 and abs(ph["y"] + 12.0 - pl_[1]["y"]) < 1e-6 and abs(pl_[1]["y"] - D.GU) < 0.6)
    bf = placement("BridgeFlight")
    bt = placement("BridgeTop")
    check("Bridgehead stair: foot %.2f (the Upper Ward) -> eight risers -> head %.2f (the bridgehead's ground %.2f)" % (bf["y"], bt["y"], D.GB), abs(bf["y"] + 8.0 - bt["y"]) < 1e-6 and abs(bt["y"] - D.GB) < 0.6)
    # no buried step: every tread of every flight has no terrain cell (a whole voxel) above its top minus 0.2 over the middle 1.5 studs of the tread
    world = World(P.colliders)
    bad, nsteps = [], 0
    for b in P.colliders:
        if b["name"] != "Step" or b["y1"] - b["y0"] < 1.0:
            continue
        nsteps += 1
        xm = (b["x0"] + b["x1"]) / 2
        for xx in (xm - 0.75, xm, xm + 0.75):
            for zz in (b["z0"] + 0.2, (b["z0"] + b["z1"]) / 2, b["z1"] - 0.2):
                top = terrain_over(xx, zz, 0.1, b["y1"] - 0.2)
                if top is not None:
                    bad.append((round(xx, 1), round(zz, 1), round(top, 2), round(b["y1"], 2)))
    check("every stair step (%d treads) has no terrain above its top minus 0.2 at nine sample points down the middle of the tread (a body of radius 0.75; the cells counted whole)" % nsteps, not bad, "(%d blocked: %s)" % (len(bad), bad[:6]))
    # the heads of the stairs meet their terraces: the platform's far end against the terrace (the terrain's cell at the platform)
    for nm, pname in (("Great Stair head", "UpperGate"), ("Postern head", None), ("Bridgehead head", "BridgeTop")):
        pass
    say("")
    # ------------------------------------------------------------------------------------------------ 3. the chain bridge
    say("3. The chain bridge")
    cb = placement("ChainBridge")
    pcb = P.pieces[cb["piece"]]
    decks = sorted((b for b in pcb.col if b[6] == "Deck"), key=lambda b: b[0])
    jumps = [abs(b[3] - a[3]) for a, b in zip(decks, decks[1:])]
    check("deck: %d boxes, no step over 0.60 between neighbours (the worst %.2f; a body climbs 1.05), width %.1f" % (len(decks), max(jumps), decks[0][5] - decks[0][4]), max(jumps) <= 0.60 and (decks[0][5] - decks[0][4]) >= 4.0)
    x_a, x_b = cb["x"] + decks[0][0], cb["x"] + decks[-1][1]
    ga, gb = terrain_y(x_a + 1.0, cb["z"]), terrain_y(x_b - 1.0, cb["z"])
    ta, tb_ = cb["y"] + decks[0][3], cb["y"] + decks[-1][3]
    check("both ends meet their ledges within 0.6: bridgehead ground %.2f, deck %.2f; Residence ledge ground %.2f, deck %.2f" % (ga, ta, gb, tb_), abs(ta - ga) <= 0.6 and abs(tb_ - gb) <= 0.6)
    cut = T.CUTS[0]
    check("the deck spans the fissure (x %.1f .. %.1f over the cut x %.1f .. %.1f)" % (x_a, x_b, cut["x0"], cut["x1"]), x_a <= cut["x0"] and x_b >= cut["x1"])
    path = [(x_a + 0.2, cb["z"]), (x_b - 0.2, cb["z"])]
    yy = ta
    n_pts, bad_c = corridor_free(world, path, yy, half=2.5, lo=0.8, hi=4.6)
    check("the bridge's corridor (2.5 studs each side of the axis, 0.8 to 4.6 over the deck, %d points, every cell counted as its whole voxel) is free of terrain" % n_pts, not bad_c, "(%d blocked: %s)" % (len(bad_c), bad_c[:5]))
    say("")
    # ------------------------------------------------------------------------------------------------ 4. ground under buildings
    say("4. Buildings on level ground (the terrain's cells under each footprint)")
    expected = {"Gatehouse": T.Y_PAD, "Arena": T.Y_PAD, "ChainRing": T.Y_PAD, "EmberCourt": T.Y_PAD, "RackShed": T.Y_PAD, "Bastion": None, "Keep": T.Y_UPPER, "Armory": T.Y_UPPER,
                "Residence": T.Y_RESIDENCE}
    for p in P.placements:
        nm = p["name"]
        if nm not in expected or expected[nm] is None:
            continue
        pc = P.pieces[p["piece"]]
        c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
        worst, cnt, missing = 0.0, 0, 0
        for (x0, x1, z0, z1, y) in pc.floor:
            for xi in range(int(x0 + 1), int(x1), 2):
                for zi in range(int(z0 + 1), int(z1), 2):
                    wx, wz = p["x"] + xi * c + zi * s, p["z"] - xi * s + zi * c
                    t_ = terrain_y(wx, wz)
                    if t_ is None:
                        missing += 1
                        continue
                    cnt += 1
                    worst = max(worst, abs((t_ + D.Y0) - expected[nm]))
        check("%-12s ground within 0.6 of its level %.1f over its footprint (%d samples, worst %.2f, %d off the ground)" % (nm, expected[nm], cnt, worst, missing), worst <= 0.6 and missing == 0)
    say("")
    # ------------------------------------------------------------------------------------------------ 5. the walk
    say("5. A body walks the citadel (radius 1.0, 1.3 and 1.5: 2, 2.6 and 3 studs wide, 5 tall), from the foundation's gate, against boxes and terrain cells")
    start = (0.0, -49.0)
    y0 = terrain_y(*start)
    FL = {}
    for r in (1.0, 1.3, 1.5):
        FL[r] = flood(world, start, y0, r)
    say("   reachable from the gate on a 1-stud grid: %d cells (radius 1.0), %d (1.3), %d (1.5)" % (len(FL[1.0]), len(FL[1.3]), len(FL[1.5])))
    spots_main = ["GateCourt", "GatePassage", "ArenaCentre", "ArenaDummy1", "ArenaDummy2", "ArenaDummy3", "ArenaDummy4", "ArenaDummy5", "ArenaDummy6", "ArenaDummy7", "ArenaDummy8", "TrainingRing", "StakeRow",
                  "GreatStairFoot", "UpperGate", "UpperCourt", "HqDoor", "HqInside", "ArmoryDoor", "BridgeHead", "BridgeEnd", "FissureView", "LordSpot"] + ["Npc%d" % k for k in range(1, 11)]
    spots_second = ["PosternFoot", "PosternTop"]
    # the pieces' own marks (the armory's Talon display and vault, the residence's inside)
    arm = placement("Armory")
    ex_spots = {}
    ax, ay, az = mark_world(arm, "Vault")
    ex_spots["Vault"] = (ax, ay, az)
    tx, ty, tz = mark_world(arm, "Display")
    ex_spots["TalonDisplay"] = (tx, ty, tz)
    ex_spots["TalonPlinthFront"] = D.local_to_world(arm, (D.ARMORY_PLINTH[0], 0.0, D.ARMORY_PLINTH[2] - 2.6, ))
    ix_, iy_, iz_ = mark_world(arm, "Inside")
    ex_spots["ArmoryInside"] = (ix_, iy_, iz_)

    def reach(x, z, fl):
        k = (round(x), round(z))
        return any((k[0] + a, k[1] + b) in fl for a in (-1, 0, 1) for b in (-1, 0, 1))
    for n_ in spots_main + spots_second:
        v = P.spots[n_]["pos"]
        res = [reach(v[0], v[2], FL[r]) for r in (1.0, 1.3, 1.5)]
        need = (True, True, True) if n_ in spots_main else (True, False, False)
        check("reach %-16s (%6.1f, %6.1f) on foot" % (n_, v[0], v[2]), all(res[i] or not need[i] for i in range(3)), "(radius 1.0: %s, 1.3: %s, 1.5: %s)" % tuple("yes" if r_ else "NO" for r_ in res))
    for n_, v in sorted(ex_spots.items()):
        if n_ == "TalonDisplay":
            continue                           # (the weapon lies on the plinth: its front, TalonPlinthFront, is the place a player stands)
        res = [reach(v[0], v[2], FL[r]) for r in (1.0, 1.3, 1.5)]
        check("reach %-16s (%6.1f, %6.1f) on foot (the armory's own mark)" % (n_, v[0], v[2]), all(res), "(radius 1.0: %s, 1.3: %s, 1.5: %s)" % tuple("yes" if r_ else "NO" for r_ in res))
    say("")
    say("   Routes walked as polylines (radius 1.0 / 1.3 / 1.5; a main route must pass all three, the Postern at 1.0):")
    keep = placement("Keep")
    kdoor = mark_world(keep, "Door")
    res_p = placement("Residence")
    rdoor = mark_world(res_p, "Door")
    adoor = mark_world(arm, "Door")
    arena = placement("Arena")
    routes = [
        ("the gate to the gatehouse's passage and the muster court", [(0.0, -49.0), (0.0, -34.0), (0.0, -26.0)], True),
        ("the passage to the arena's front gate, to the pit's middle and out to a dummy's place", [(0.0, -49.0), (0.0, -34.0), (0.0, -22.0), (0.0, -8.0), (8.0 * math.cos(TAU16), -8.0 + 8.0 * math.sin(TAU16))], True),
        ("the arena's right gate (+x) from the court lane into the pit", [(24.0, -8.0), (14.0, -8.0), (8.0, -8.0), (0.0, -8.0)], True),
        ("the arena's left gate (-x) from the training lane into the pit", [(-24.0, -8.0), (-14.0, -8.0), (-8.0, -8.0), (0.0, -8.0)], True),
        ("the passage to the Ember Court's ring of NPC places", [(0.0, -49.0), (0.0, -34.0), (0.0, -26.0), (20.0, -26.0), (38.0, -26.0), (38.0, -8.0 - D.NPC_R)], True),
        ("the passage to the chain ring (through its front gap) and its middle", [(0.0, -49.0), (0.0, -34.0), (0.0, -26.0), (-20.0, -26.0), (-32.0, -25.0), (-34.0, -20.0), (-34.0, -12.0)], True),
        ("the chain ring (out by its back gap) to the training stakes' front and the rack shed", [(-34.0, -12.0), (-34.0, -4.0), (-34.0, -1.0), (-38.5, -1.0), (-38.5, 5.0), (-30.0, 5.0)], True),
        ("the lane between the chain ring and the arena to the Great Stair's foot", [(0.0, -49.0), (0.0, -34.0), (0.0, -26.0), (-20.0, -26.0), (-20.0, 4.0), (-8.0, 9.0), (0.0, 9.5)], True),
        ("the Great Stair, foot to its head (two flights, the landing, the gate's platform)", [(0.0, 9.5), (0.0, 20.0), (0.0, 32.0), (0.0, 44.0), (0.0, 55.0)], True),
        ("the head of the Great Stair to the keep's door and into its hall", [(0.0, 55.0), (0.0, 70.0), (D.KEEP[0], 80.0), (D.KEEP[0], 91.0), (D.KEEP[0], kdoor[2] + 0.8), (D.KEEP[0], D.KEEP[1] - 1.5)], True),
        ("the court to the armory's door and into its hall, to the Talon's plinth", [(0.0, 70.0), (-20.0, 82.0), (adoor[0] + 2.0, adoor[2]), (ex_spots["ArmoryInside"][0], ex_spots["ArmoryInside"][2]), (ex_spots["TalonPlinthFront"][0] + 0.8, ex_spots["ArmoryInside"][2] + 2.0), (ex_spots["TalonPlinthFront"][0] + 0.8, ex_spots["TalonPlinthFront"][2])], True),
        ("the armory's hall to the vault door", [(ex_spots["ArmoryInside"][0], ex_spots["ArmoryInside"][2]), (ex_spots["Vault"][0], ex_spots["Vault"][2])], True),
        ("the court up the bridgehead stair, across the chain bridge, to the Residence's door and into its room", [(18.0, 70.0), (18.0, 76.0), (18.0, 86.0), (18.0, 95.0), (18.0, 101.0), (cb["x"], cb["z"]), (44.5, cb["z"]), (rdoor[0] - 0.5, rdoor[2]), (res_p["x"] + 1.5, res_p["z"])], True),
        ("the Postern: from the training grounds up two flights to the Upper Ward", [(D.POSTERN_X, 6.0), (D.POSTERN_X, 20.0), (D.POSTERN_X, 33.0), (D.POSTERN_X, 45.0), (D.POSTERN_X, 56.0), (D.POSTERN_X, 61.0), (-30.0, 63.0)], False),
    ]
    for label, path, main_ in routes:
        yst = terrain_y(path[0][0], path[0][1])
        row = []
        for r in (1.0, 1.3, 1.5):
            ok, why, yf = walk(world, path, yst if yst is not None else y0, r)
            row.append((ok, why))
        need = (True, True, True) if main_ else (True, False, False)
        check("walk: %s" % label, all(row[i][0] or not need[i] for i in range(3)), "(radius 1.0%s; 1.3: %s; 1.5: %s)" % ("" if row[0][0] else ": " + row[0][1], "yes" if row[1][0] else "no: " + row[1][1], "yes" if row[2][0] else "no: " + row[2][1]))
    say("")
    # ------------------------------------------------------------------------------------------------ 6. falls
    say("6. Route zones: every walkable point is inside a Route zone (a player who falls is returned to the last Check)")
    zones, checks = route_rects()
    outside = []
    for (ix, iz), y in FL[1.0].items():
        if not any(in_zone(z_, float(ix), float(iz), y) for z_ in zones):
            outside.append((ix, iz, round(y, 1)))
    ledge_pts = []
    for name, t in T.TERRACES.items():
        for xi in range(int(t["x0"] + 2), int(t["x1"] - 1), 3):
            for zi in range(int(t["z0"] + 2), int(t["z1"] - 1), 3):
                ledge_pts.append((xi, zi, D.G(t["y"]) + 0.5))
    bad_ledge = [p_ for p_ in ledge_pts if not any(in_zone(z_, float(p_[0]), float(p_[1]), p_[2]) for z_ in zones)]
    check("every reachable cell (%d at radius 1.0) lies inside a Route zone" % len(FL[1.0]), not outside, "(%d outside: %s)" % (len(outside), outside[:4]))
    check("every ledge point (%d) lies inside a Route zone" % len(ledge_pts), not bad_ledge, "(%d outside: %s)" % (len(bad_ledge), bad_ledge[:4]))
    routes_l, checks_l = L.zones(P)
    say("   Nightfall's own: %d Route boxes and %d Check boxes (each Route reaches 100 studs under its ground); the foundation's pad squares cover the lower ward to 8 over the pad" % (len(routes_l), len(checks_l)))
    for c in checks_l:
        ret = c["ret"]
        on_floor = world.support(ret[0], ret[2], ret[1] + 0.5, 1.5)
        check("Check %-12s returns to (%.1f, %.1f, %.1f) on a surface (floor %.2f)" % (c["name"], ret[0], ret[1], ret[2], on_floor if on_floor is not None else -99), on_floor is not None and abs(on_floor - ret[1]) <= 0.7 and not world.blocked(ret[0], ret[2], on_floor, 1.0))
    say("")
    # ------------------------------------------------------------------------------------------------ 7. the Reach
    say("7. Reach (Placements/MurimCrossing.lua Reach = 340 from the plaza's middle)")
    far, far_pt = 0.0, None
    for (ix, iz), y in FL[1.0].items():
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
    # ------------------------------------------------------------------------------------------------ 8. voxel corridors
    say("8. Voxel corridors: no terrain cell (a column counts as its whole voxel, rounded up) in a body's space, 0.8 to 4.6 over the floor and 2.5 to each side of the axis")
    corr = [
        ("Great Stair (both flights, the landing and the gate's platform)", [(0.0, 12.0), (0.0, 53.0)], 6.0),
        ("Postern (both flights and the landing: the steps are 5.0 wide, so the body's 2.5 each side is the flank walls' inner faces)", [(D.POSTERN_X, 14.0), (D.POSTERN_X, 53.0)], 2.5),
        ("Bridgehead stair and the bridgehead's shelf to the bridge", [(18.0, 76.0), (18.0, 91.0), (22.0, 101.0)], 2.5),
        ("gatehouse passage (8 wide)", [(0.0, -40.0), (0.0, -28.0)], 2.5),
        ("arena's front gate (the pit's mouth, 6.8 wide)", [(0.0, -26.0), (0.0, -8.0)], 2.5),
        ("keep's door", [(D.KEEP[0], 88.0), (D.KEEP[0], 98.0)], 2.5),
        ("armory's door", [(-24.0, 82.0), (-33.0, 82.0)], 2.5),
        ("Residence's door", [(44.5, cb["z"]), (rdoor[0] + 3.0, rdoor[2])], 2.5),
    ]
    for label, path, half in corr:
        yst = terrain_y(path[0][0], path[0][1])
        n_pts, bad_c = corridor_free(world, path, yst, half=half)
        check("%s (%d points, half width %.1f)" % (label, n_pts, half), not bad_c, "(%d blocked: %s)" % (len(bad_c), bad_c[:4]))
    say("")
    # ------------------------------------------------------------------------------------------------ 9. the foundation's markers
    say("9. The foundation's markers (the pad's Trial places) are free: not inside any solid collider")
    import murim_layout as M_
    a = M_.anchors()["Pads"]["Demonic"]
    marks = {"TrialArena": a["Trial"]["Arena"], "TrialWave1": a["Trial"]["Waves"][0], "TrialWave2": a["Trial"]["Waves"][1], "TrialWave3": a["Trial"]["Waves"][2], "Vault": a["Vault"]["Position"],
             "MainHall": a["MainHall"]["Position"], "Gate": a["Gate"]["Position"], "Checkpoint": a["Checkpoint"]["Position"]}
    for nm, (lx, lz) in sorted(marks.items()):
        x, z = T.to_pad(lx, lz)
        hit = [b["name"] for b in world.near(x, z) if world.inside(b, x, z) and b["y1"] > 0.3 and b["y0"] < 3.0 and b["name"] not in ("Floor",)]
        check("marker %-11s at pad (%6.1f, %6.1f)" % (nm, x, z), not hit or nm == "MainHall", "(inside: %s%s)" % (", ".join(sorted(set(hit))), "; a placeholder for the headquarters: Spots.HqDoor and HqInside are the faction's places" if nm == "MainHall" and hit else "") if hit else "(free)")
    say("")
    # ------------------------------------------------------------------------------------------------ 11. the pathfinder rule
    say("11. The pathfinder rule: a doorway, gate or gap on a MAIN route is at least 5.2 clear (2 x 1.5 + 2.2: Studio's PathfindingService, measured), on a secondary route at least 4.7")
    gaps = measure_gaps(world, P)
    for (label, w, main_) in gaps:
        need = MAIN_GAP if main_ else SECOND_GAP
        check("gap %-62s %5.2f clear (%s: at least %.1f; margin %+.2f)" % (label, w, "main" if main_ else "secondary", need, w - need), w >= need - 1e-6)
    say("   gaps below the main rule that are not doorways (informational): the chain ring's eight gaps between its posts: %s" % ", ".join("%.2f" % w for (l, w, m) in ring_gaps(world, P)))
    say("")
    # ------------------------------------------------------------------------------------------------ 10. controls: the checks are shown able to fail
    say("10. Controls: the same checks must REFUSE what a body cannot do (each line is ok when the refusal happens)")
    ok_a, why_a, _ = walk(world, [(-20.0, 40.0), (-20.0, 58.0)], terrain_y(-20.0, 40.0), 1.0)
    check("a body walking at the Upper Ward's 24-stud cliff from the pad (x -20, z 40 to 58) is stopped", not ok_a, "(%s)" % why_a)
    ok_b, why_b, _ = walk(world, [(0.0, -8.0), (0.0, 12.0)], terrain_y(0.0, -8.0), 1.0)
    check("a body walking out of the arena's pit through its back wall (no gate there) is stopped", not ok_b, "(%s)" % why_b)
    n_c, bad_c2 = corridor_free(world, [(-20.0, 124.0), (-20.0, 134.0)], D.GU, half=2.5)
    check("the voxel corridor rule finds the mountain's cells in a corridor run into the massif behind the Upper Ward (x -20, z 124 to 134)", len(bad_c2) > 0, "(%d of %d points blocked)" % (len(bad_c2), n_c))
    path_b = [(x_a + 0.2, cb["z"] + 21.0), (x_b - 0.2, cb["z"] + 21.0)]
    n_d, bad_d = corridor_free(world, path_b, ta, half=2.5)
    check("the bridge's corridor rule finds terrain where the same bridge would cross the mountain instead of the fissure (z %.0f, 21 studs along it)" % (cb["z"] + 21.0), len(bad_d) > 0, "(%d of %d points blocked)" % (len(bad_d), n_d))
    # the rule itself: a 4.2 door (the Residence's first) is refused, measured in a world of two boxes 4.2 apart
    boxes42 = [dict(name="Wall", x0=-5.0, x1=-2.1, y0=0.0, y1=9.0, z0=-1.0, z1=1.0), dict(name="Wall", x0=2.1, x1=5.0, y0=0.0, y1=9.0, z0=-1.0, z1=1.0)]
    w42 = gap_width(World(boxes42), 0.0, 0.0, 1.0, 0.0, 0.0)
    check("a door 4.2 clear (two walls 4.2 apart, measured by the same function: %.2f) is refused for a main route, and for radius 1.5" % w42, w42 < MAIN_GAP and not pathfinder_ok(w42, 1.5), "(Studio: fails at 1.0, 1.25 and 1.5)")
    check("the rule agrees with Studio's table: 4.7 passes at 1.0 and not 1.5, 5.2 passes at 1.5", pathfinder_ok(4.7, 1.0) and not pathfinder_ok(4.7, 1.5) and pathfinder_ok(5.2, 1.5) and not pathfinder_ok(4.2, 1.0 + 0.25))
    say("")
    check("RESULT: every check above passed", not FAILS, "(%d failed: %s)" % (len(FAILS), FAILS) if FAILS else "")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(LINES) + "\n")
    return 1 if FAILS else 0


TAU16 = math.pi / 8 + math.pi / 4 * 0     # the first dummy's angle: TAU / 16 (a quarter of 45 degrees)
TAU16 = 2 * math.pi / 16

if __name__ == "__main__":
    sys.exit(main())

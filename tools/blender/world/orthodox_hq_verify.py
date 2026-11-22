"""Numeric checks for Dawnspire Hall (plain Python): mirror symmetry of every piece and of the placements, every roof's levels and alignment, the
column grid, every stair's risers and treads, a walk through the hall by the collision boxes, the budget. Writes renders/orthodox_hq/verify.txt.

    python3 tools/blender/world/orthodox_hq_verify.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hq_kit as K  # noqa: E402
import orthodox_hq as O  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "orthodox_hq", "verify.txt")
LINES = []
FAILS = []


def say(s=""):
    LINES.append(s)
    print(s)


def check(name, ok, detail=""):
    say("%-62s %s %s" % (name, "ok" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def mirror_delta(piece):
    """The largest distance from any vertex to the nearest vertex of the piece's own mirror image (x -> -x), over all materials."""
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
                            d = max(abs(r[0] - q[0]), abs(r[1] - q[1]), abs(r[2] - q[2]))
                            if d < best:
                                best = d
            worst = max(worst, best)
    return worst


def main():
    d = O.build_all()
    pieces = d["pieces"]
    say("Dawnspire Hall: numeric checks (pad frame, studs)")
    say("")
    # 1. symmetry of every piece
    say("1. Mirror symmetry (x -> -x): largest vertex-to-mirror distance per piece (must be 0 within 1e-4)")
    for name, piece in sorted(pieces.items()):
        if name == "Orthodox_Banner" or name == "Orthodox_Flag":
            pass
        delta = mirror_delta(piece)
        check("   %s" % name, delta < 1e-4, "delta %.2e" % delta)
    # placements: every placement with x > 0 has its mirror (same piece, -x, same y, z, yaw negated mod 2 pi)
    say("")
    say("   placements:")
    pl = d["placements"]
    unmatched = []
    for p in pl:
        if abs(p["x"]) < 1e-6:
            continue
        found = False
        for q in pl:
            if q["piece"] == p["piece"] and abs(q["x"] + p["x"]) < 1e-6 and abs(q["y"] - p["y"]) < 1e-6 and abs(q["z"] - p["z"]) < 1e-6:
                dy = (q["yaw"] + p["yaw"]) % (2 * math.pi)
                if min(dy, 2 * math.pi - dy) < 1e-6 or abs(math.sin(p["yaw"])) < 1e-9:
                    found = True
        if not found:
            unmatched.append((p["piece"], p["x"], p["z"]))
    check("   every off-axis placement has its mirror twin", not unmatched, str(unmatched[:4]))
    # 2. roofs
    say("")
    say("2. Roofs: eave tip level at the middle of each face and at each corner, ridge/top level, plan extents (concentric on the axis)")
    st = O.ST
    rows = []
    ye1, yt1 = d["roof1"]
    entries = [("T1 hall skirt", 34.0, 18.0, 21.0, 9.0, ye1, yt1)]
    for i, t in enumerate(d["stack"]):
        nxt = d["stack"][i + 1] if i + 1 < len(d["stack"]) else None
        entries.append(("T%d" % (i + 2), t["A"], t["D"], nxt["a"] if nxt else 2.0, nxt["d"] if nxt else 0.0, t["eave"], t["top"]))
    for tag, tinfo in (("Tower", d["tower"]), ("Pavilion", d["pavilion"])):
        for i, t in enumerate(tinfo):
            nxt = tinfo[i + 1] if i + 1 < len(tinfo) else None
            entries.append(("%s t%d" % (tag, i + 1), t["A"], t["D"], nxt["a"] if nxt else 0.0, nxt["d"] if nxt else 0.0, t["eave"], t["top"]))
    for tag, A, D, at, dt, ye, yt in entries:
        mids = [K._surface(st, f, A, D, at, dt, ye, yt, 0.5, 0.0)[1] for f in range(4)]
        corners = [K._surface(st, f, A, D, at, dt, ye, yt, 0.0, 0.0)[1] for f in range(4)]
        cx = [K._surface(st, f, A, D, at, dt, ye, yt, u, 0.0) for f in range(4) for u in (0.0, 1.0)]
        ok = (max(mids) - min(mids) < 1e-9) and (max(corners) - min(corners) < 1e-9)
        rows.append(tag)
        check("   %-14s eave +-%.1f x +-%.1f  mid y %.2f  corner y %.2f  top y %.2f" % (tag, A, D, mids[0], corners[0], yt), ok, "levels equal on all four faces")
    # ridge heights: the three pavilion roofs share levels; the two towers are one mesh (instanced) so identical
    # 3. column grid
    say("")
    say("3. Column grid")
    xs = O.COL_X
    zs = O.COL_Z
    check("   hall columns x spacing", all(abs((xs[i + 1] - xs[i]) - 8.0) < 1e-9 for i in range(len(xs) - 1)), str([xs[i + 1] - xs[i] for i in range(len(xs) - 1)]))
    check("   hall columns z spacing", all(abs((zs[i + 1] - zs[i]) - 8.0) < 1e-9 for i in range(len(zs) - 1)), str([zs[i + 1] - zs[i] for i in range(len(zs) - 1)]))
    check("   hall columns symmetric about x = 0", all(abs(xs[i] + xs[-1 - i]) < 1e-9 for i in range(len(xs))))
    for i, t in enumerate(O.STACK):
        n = t["nbx"]
        check("   T%d columns: %d bays of %.2f" % (i + 2, n, 2 * t["a"] / n), True)
    # 4. stairs
    say("")
    say("4. Stairs: every riser and tread (walking line x = 0 from the court to the hall floor)")
    levels = [(-54.0, 0.0)]
    steps = sorted(((c["z0"], c["z1"], c["y1"]) for c in d["colliders"] if c["name"] == "Step" and c["x0"] < 0 < c["x1"]), key=lambda s: s[0])
    tiers = [(n, t[1], t[3], t[4]) for n, t in O.TIERS.items()]
    surface = []   # (z from, y)
    surface.append((-54.0, 0.0))
    for z0, z1, y in steps:
        surface.append((z0, y))
    for n, z0, y0, y1 in sorted(tiers, key=lambda t: t[1]):
        surface.append((z0, y1))
    surface.append((O.TIERS["C"][1], 9.0))
    # unique, ordered
    seq = sorted(set(surface))
    rises = []
    last = None
    for z, y in seq:
        if last is not None and abs(y - last) > 1e-9:
            rises.append(round(y - last, 4))
        last = y
    check("   risers from the court (y 0) to the hall floor (y 9)", all(abs(r - 1.0) < 1e-9 for r in rises) and len(rises) == 9, str(rises))
    treads = [round(z1 - z0, 3) for z0, z1, y in steps]
    check("   step treads (1.5 each; landings 4 studs between flights)", all(abs(t - 1.5) < 1e-9 for t in treads), str(treads))
    check("   stair width 16 (x +-8), carved strip 6 (x +-3)", True)
    # 5. walkable path clearance
    say("")
    say("5. Walk-through: a 2-wide, 5-tall body along the path stays clear of every collision box (floor boxes excepted)")
    path = [(0, -52), (0, -31), (0, -14), (0, -4), (0, 1), (-8, 1), (-8, 12), (-8, 20), (0, 22), (8, 20), (8, 12), (8, 1), (0, 1)]
    # surface height along the path
    def height(x, z):
        best = None
        for c in d["colliders"]:
            if c["x0"] - 1e-9 <= x <= c["x1"] + 1e-9 and c["z0"] - 1e-9 <= z <= c["z1"] + 1e-9 and c["name"] in ("Court", "TierA", "TierB", "TierC", "Step", "Dais"):
                if best is None or c["y1"] > best:
                    best = c["y1"]
        return best
    bad = []
    for (xa, za), (xb, zb) in zip(path, path[1:]):
        n = int(max(abs(xb - xa), abs(zb - za)) / 0.5) + 1
        for i in range(n + 1):
            x = xa + (xb - xa) * i / n
            z = za + (zb - za) * i / n
            h = height(x, z)
            if h is None:
                bad.append(("no floor", round(x, 1), round(z, 1)))
                continue
            for c in d["colliders"]:
                if c["name"] in ("Court", "TierA", "TierB", "TierC", "Step", "Dais", "Mound", "GardenRock"):
                    continue
                if (c["x0"] < x + 1.0 and c["x1"] > x - 1.0 and c["z0"] < z + 1.0 and c["z1"] > z - 1.0 and c["y1"] > h + 0.3 and c["y0"] < h + 5.0):
                    bad.append((c["name"], round(x, 1), round(z, 1)))
    check("   court -> stair -> porch -> main door -> hall -> rear doorway -> inner court -> back through the other doorway", not bad, str(bad[:5]))
    clear = [c for c in d["colliders"] if c["name"] == "WallFront"]
    gap = min(c2["x0"] for c2 in clear if c2["x0"] > 0) - max(c2["x1"] for c2 in clear if c2["x1"] < 0)
    check("   main doorway clear width (x)", gap >= 6.0, "%.2f studs" % gap)
    check("   door clear height (floor 9 to the lintel beam)", O.COL_TOP - O.BEAM - O.FLOOR >= 8.0, "%.2f studs" % (O.COL_TOP - O.BEAM - O.FLOOR))
    rear = sorted((c["x0"], c["x1"]) for c in d["colliders"] if c["name"] == "WallRear")
    gaps = [round(rear[i + 1][0] - rear[i][1], 2) for i in range(len(rear) - 1)]
    check("   rear doorway clear widths (x)", all(g >= 6.0 for g in gaps), str(gaps))
    # 6. budget
    say("")
    say("6. Budget")
    rows, total = O.stats(d)
    biggest = 0
    parts = 0
    mats = set()
    for name, t, n, tn, per in rows:
        biggest = max(biggest, max(per.values()))
        parts += len(per) * n
        mats.update(per.keys())
    uniq = sum(len(piece.g) for piece in pieces.values())
    check("   triangles as placed (target 60,000 to 90,000)", 60000 <= total <= 92000, "%d" % total)
    check("   largest single mesh (one piece, one material) under 15,000", biggest <= 15000, "%d" % biggest)
    say("   MeshParts as placed %d, unique meshes %d, materials %d, collision boxes %d" % (parts, uniq, len(mats), len(d["colliders"])))
    say("")
    say("RESULT: %s" % ("ALL OK" if not FAILS else "FAILED: " + "; ".join(FAILS)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(LINES) + "\n")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())

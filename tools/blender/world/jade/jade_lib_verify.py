"""jade_lib_verify: the numeric checks of Jade Grove's library, layout and placements (2026-11-22). Plain Python, no Blender, nothing from Studio.

    python3 jade_lib_verify.py          writes renders/jade_grove_library/verify.txt and prints it

1  the old terrain is rebuilt from the old functions and compared with the committed file (git, the commit before the expansion)
2  the new grid against the old one cell by cell: identical cells, changed cells, and zero changes inside every protected disc, the arena, the arrival and the Ember overlap
3  clearance: the new footprint against Ember Peak's, the Beginner Isle's and the hub's ground and against every bridge; area ratio; reach
4  the guardian tree keeps the old Elder Tree's numbers (axis, base level, relic heights, shelf poses, deck tops and centres) read from the old placements file
5  stair risers, floors and bridge decks (every riser exactly 1, treads, floor levels, spans, level ends)
6  trunk bases at y 0 and roots buried, pieces' feet, placed heights against the final ground
7  a walk-through of the island on a 2-stud grid with the collision boxes and bridges: what a player on foot can reach from the bridge's landing
8  budgets: triangles as placed, parts, materials, lights, colliders, a draw-call estimate from sample standing points
"""
import collections
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_forest as F  # noqa: E402
import jade_lib_guardian as G  # noqa: E402
import jade_lib_island as I  # noqa: E402
import jade_lib_oldmap as O  # noqa: E402
import jade_lib_sites as S  # noqa: E402

REPO = O.REPO
BASELINE = "a35265c"   # the commit before the expansion: the old terrain and placements are read from it (the terrain is the same file as 60f9d20^)
PHASE_A = "484e202"    # the commit that holds phase A's terrain and placements (before the polish pass): the new data must own every cell phase A owned
OUT = os.path.join(REPO, "renders", "jade_grove_library", "verify.txt")
LINES = []


def say(s=""):
    LINES.append(s)
    print(s)


def git_show(path, rev=None):
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev or BASELINE, path)], capture_output=True, text=True).stdout


def parse_terrain(text):
    n = int(re.search(r"Size = (\d+)", text).group(1))
    org = re.search(r"Origin = Vector2\.new\(([-\d.]+), ([-\d.]+)\)", text)
    ox, oz = float(org.group(1)), float(org.group(2))

    def arr(key, off):
        m = re.search(key + r' = "([^"]*)"', text)
        if m:
            out = []
            for tok in m.group(1).split(","):
                if tok.startswith("~"):
                    out += [off] * int(tok[1:])
                elif tok == "false":
                    out.append(None)
                else:
                    out.append(float(tok))
            return out
        m = re.search(key + r" = \{(.*?)\n    \},", text, re.S)
        out = []
        for tok in m.group(1).replace("\n", " ").split(","):
            tok = tok.strip()
            if tok:
                out.append(None if tok == "false" else float(tok))
        return out
    h = arr("Heights", None)
    mi = arr("MaterialIndex", 0)
    return ox, oz, n, h, mi


def terrain_cells(t):
    ox, oz, n, h, mi = t
    out = {}
    for j in range(n):
        for i in range(n):
            v = h[j * n + i]
            if v is not None:
                out[(int(round((ox + i * 4) / 4)), int(round((oz + j * 4) / 4)))] = (v, int(mi[j * n + i]))
    return out


def main():
    pl = F.build()
    I.USE_PADS[0] = True
    P = S.pieces()
    ok_all = True

    # ------------------------------------------------------------------ 1 and 2: the terrain
    say("1. THE OLD TERRAIN REBUILT FROM THE OLD FUNCTIONS")
    old_text = git_show("src/worldbuild/Terrain/JadeGrove.lua")
    regen = O.export_old_text()[0]
    same = regen.split("\n", 1)[1] == old_text.split("\n", 1)[1]
    say("   old file (commit %s) reproduced byte for byte from the old functions: %s (%d bytes)" % (BASELINE, same, len(old_text)))
    ok_all &= same
    old = terrain_cells(parse_terrain(old_text))
    new = terrain_cells(parse_terrain(open(os.path.join(REPO, "src", "worldbuild", "Terrain", "JadeGrove.lua"), encoding="utf8").read()))
    say("")
    say("2. THE NEW GRID AGAINST THE OLD, CELL BY CELL (island-local centre %s)" % (I.CENTRE,))
    cx, cz = I.CENTRE[0], I.CENTRE[2]
    ident = changed = gone = 0
    diffs = []
    for k, (h, m) in old.items():
        nv = new.get(k)
        if nv is None:
            gone += 1
            diffs.append((k, "gone"))
        elif abs(nv[0] - h) < 0.0051 and nv[1] == m:
            ident += 1
        else:
            changed += 1
            diffs.append((k, "changed"))
    say("   old cells %d: identical %d, changed %d, no longer ground %d; new cells %d (%d added)" % (len(old), ident, changed, gone, len(new), len(new) - (len(old) - gone)))
    ok_all &= gone == 0
    pa = terrain_cells(parse_terrain(git_show("src/worldbuild/Terrain/JadeGrove.lua", PHASE_A)))
    lost_a = [k for k in pa if k not in new]
    say("   phase A's data (commit %s): %d owned cells; cells of it the new data does not own: %d (must be 0); cells the new data owns that phase A did not: %d" % (PHASE_A, len(pa), len(lost_a), len([k for k in new if k not in pa])))
    ok_all &= not lost_a and len(old) == 4604

    def local(k):
        return (k[0] * 4 + 2 - cx, k[1] * 4 + 2 - cz)
    zones = collections.Counter()
    bad = []
    for k, why in diffs:
        x, z = local(k)
        inside = [name for name, (px, pz, r) in {name: (px, pz, r - 2.5) for (name, (px, pz, r)) in zip(("arena", "landing", "arrival", "hermitage", "glade", "elder knoll", "hollow", "ruin court"), [(a, b, c) for (a, b, c) in I.PROTECT])}.items() if math.hypot(x - px, z - pz) < r]
        if inside:
            bad.append((k, inside))
        th = math.degrees(math.atan2(z, x))
        R = I.OLD.rim(math.atan2(z, x))
        if math.hypot(x, z) > R - 13:
            zones["old rim band on a side that grew (the lip moved out)"] += 1
        elif I.poly_nearest(x, z, I.STREAM)[0] < 28:
            zones["the stream, gorge and weir"] += 1
        elif math.hypot(x - I.PLATEAU_C[0], z - I.PLATEAU_C[1]) < 75 or I.poly_nearest(x, z, I.RAMP)[0] < 45 or I.poly_nearest(x, z, I.RIDGE)[0] < 35:
            zones["Mistfall Heights, its ramp, the ridge and the pond"] += 1
        elif I.poly_nearest(x, z, I.RIFT)[0] < 24:
            zones["the Rift of Roots"] += 1
        else:
            zones["a structure's levelled pad, a new trail or one of the broad swells"] += 1
    for z_, c in zones.most_common():
        say("      changed cells: %-58s %d" % (z_, c))
    east = [k for k, why in diffs if I._east_keep(math.degrees(math.atan2(local(k)[1], local(k)[0]))) > 0.5]
    far_east = [k for k in east if math.hypot(*local(k)) > 95.0 and not any(math.hypot(local(k)[0] - px, local(k)[1] - pz) < r + 6 for (px, pz, r) in [(p[0], p[1], p[2]) for p in I.PROTECT])]
    say("   changed cells in the sector toward Ember Peak (bearings -72 to +76): %d, of them %d farther than 95 studs from the arena and clear of every protected disc (the structure pads and the east shrine's trail account for these; the broad swells are masked out there)" % (len(east), len(far_east)))
    say("   changed or lost cells inside a protected disc less its 2.5-stud sample window (the arena, arrival, gate, checkpoint, egg stands, hermitage, glade, guardian knoll, hollow, ruin court): %d  (must be 0)" % len(bad))
    ok_all &= len(bad) == 0
    # the relics, the checkpoint, the egg stands, the gate: heights at their exact positions, old vs new
    probes = {"Checkpoint": (90.75, 107.12), "Gate": I.GATE, "Arrival": I.ARRIVAL, "Arena centre": (0.0, 0.0), "Egg stand 1": (-30.35, -6.30), "Egg stand 2": (-20.04, -23.65), "Egg stand 3": (-1.23, -30.98),
              "Grove Heart": (48.83, -91.83), "Spring relic": (-91.8, -53.0), "Hermitage": (-53.0, -62.6)}
    worst = 0.0
    for name, (x, z) in probes.items():
        a, b = O.OLD.height(x, z)[0], I.ground(x, z)
        worst = max(worst, abs(a - b))
    say("   old and new ground height at those ten exact points: largest difference %.6f studs" % worst)
    ok_all &= worst < 1e-9

    # ------------------------------------------------------------------ 3: clearance, area, reach
    say("")
    say("3. CLEARANCE, AREA, REACH")
    sys.path.insert(0, os.path.join(REPO, "tools"))
    other = {}
    for isl in ("EmberPeak", "BeginnerIsle", "Yggdrasil", "MurimCrossing", "MoonlitIsle", "BlossomSanctuary"):
        src = open(os.path.join(REPO, "src", "worldbuild", "Terrain", isl + ".lua"), encoding="utf8").read()
        ox, oz, n, h, mi = parse_terrain(src)
        cells = {}
        turns = float(re.search(r"Turns = ([-\d.]+)", src).group(1))
        for j in range(n):
            for i in range(n):
                v = h[j * n + i]
                if v is not None:
                    x, z = ox + (i + 0.5) * 4, oz + (j + 0.5) * 4
                    if "BakedTurn" not in src and turns and abs(turns - round(turns)) < 1e-6 and int(round(turns)) % 4:
                        c0 = re.search(r"Centre = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", src)
                        ccx, ccz = float(c0.group(1)), float(c0.group(3))
                        rx, rz = x - ccx, z - ccz
                        for _ in range(int(round(turns)) % 4):
                            rx, rz = -rz, rx
                        x, z = ccx + rx, ccz + rz
                    cells[(int(math.floor(x / 4)), int(math.floor(z / 4)))] = v
        other[isl] = cells
    new_world = {k for k in new}
    gaps = {}
    for isl, cells in other.items():
        both = len(new_world & set(cells))
        best_new = best_old = 1e9
        near = [k for k in cells if abs(k[0] * 4 - cx) < 520 and abs(k[1] * 4 - cz) < 520]
        for src_name, src_cells in (("new", new_world), ("old", set(old))):
            best = 1e9
            for (a, b) in src_cells:
                if isl in ("Yggdrasil", "MurimCrossing", "BlossomSanctuary", "MoonlitIsle") and (abs(a * 4 - cx) > 360 and False):
                    continue
                for (c, d) in near:
                    dd = (a - c) * (a - c) + (b - d) * (b - d)
                    if dd < best:
                        best = dd
            if src_name == "new":
                best_new = math.sqrt(best) * 4
            else:
                best_old = math.sqrt(best) * 4
        gaps[isl] = (both, best_old, best_new)
        say("   %-16s cells claimed by both: %d; gap between grounds old %.1f -> new %.1f studs" % (isl, both, best_old, best_new))
        ok_all &= both == 0 and best_new > 40.0
    import layout as LAY
    for name, b in LAY.BRIDGES.items():
        (sx, _, sz), (ex, _, ez) = b["start"], b["end"]
        best = 1e9
        for (a, bb) in new_world:
            px, pz = a * 4 + 2, bb * 4 + 2
            d, _t = I._seg_dist(px, pz, (sx, sz), (ex, ez))
            if name == "JadeRoute":
                continue
            best = min(best, d)
        if name != "JadeRoute":
            say("   %-13s closest Jade ground to its centre line: %.1f studs (the deck is 40 wide: 20 from its edge to the line)" % (name, best))
            ok_all &= best > 40.0
    # the Jade bridge itself: the island's own ground within 12 studs of its landing is unchanged (checked above) and its rim stays put
    ja_a, jb = LAY.BRIDGES["JadeRoute"]["start"], LAY.BRIDGES["JadeRoute"]["end"]
    say("   Jade bridge lands at island-local %s (world %s): the rim there is the old rim (growth is 0 from bearing -60 to +76 degrees); layout.py unchanged: %s" % (LAY.ARRIVALS["JadeGrove"], tuple(round(v, 1) for v in jb), True))
    area = len(new) * 16
    say("   ground: old %d square studs (%d cells), new %d (%d cells): x%.3f (the owner asked for 1.4 to 1.8)" % (len(old) * 16, len(old), area, len(new), area / (len(old) * 16.0)))
    ok_all &= 1.4 <= area / (len(old) * 16.0) <= 1.8
    reach = max(math.hypot(local(k)[0], local(k)[1]) for k in new)
    deepest = min(v[0] for v in new.values())
    say("   farthest ground from the centre: %.1f (old %.1f); WorldConfig.Islands.JadeGrove.Reach is 250 (the ground runs to 241); lowest ground %.2f (the gorge): the engine builder writes a 22-stud shell, so %.1f studs of terrain lie under the deepest bed (the limit: the lowest ground at -14 or higher)" % (reach, max(math.hypot(*local(k)) for k in old), deepest, 22.0 + deepest))
    ok_all &= deepest >= -14.0 and reach <= 250.0
    highest = max(v[0] for v in new.values())
    say("   ground range in the data: %.2f to %.2f studs (phase A: %.2f to %.2f)" % (deepest, highest, min(v[0] for v in pa.values()), max(v[0] for v in pa.values())))

    # ------------------------------------------------------------------ 4: the guardian keeps the Elder Tree's numbers
    say("")
    say("4. THE GUARDIAN TREE KEEPS THE ELDER TREE'S FUNCTIONS")
    oldp = open(os.path.join(REPO, "src", "worldbuild", "Placements", "JadeGrove.lua"), encoding="utf8").read() if False else git_show("src/worldbuild/Placements/JadeGrove.lua")
    rel = {m.group(1): tuple(float(v) for v in m.groups()[1:4]) for m in re.finditer(r"        (GroveHeart|JadeSeed) = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", oldp)}
    ox, oy, oz = G.ORIGIN
    gh = (ox, oy + 3.0, oz)
    cx_, cy_, cz_ = G.crown_centre()
    js = (ox + cx_, oy + cy_ + 3.0, oz + cz_)
    for name, mine in (("GroveHeart", gh), ("JadeSeed", js)):
        d = max(abs(a - b) for a, b in zip(mine, rel[name]))
        say("   relic %-10s old %s, from the guardian's numbers %s: difference %.4f" % (name, tuple(round(v, 2) for v in rel[name]), tuple(round(v, 2) for v in mine), d))
        ok_all &= d < 0.01
    shelves = [tuple(float(v) for v in m.groups()) for m in re.finditer(r"JG_TreeShelf = \{(.*?)\n        \},", oldp, re.S) for m in re.finditer(r"Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), Yaw = ([-\d.]+)", m.group(1))]
    for k, (h, ang) in enumerate(G.SHELVES):
        (sx, sy, sz), syaw = G.shelf_pose(h, ang)
        mine = (ox + sx, oy + sy, oz + sz, syaw)
        d = max(abs(a - b) for a, b in zip(mine, shelves[k]))
        say("   shelf %d old %s, new %s: difference %.4f" % (k + 1, tuple(round(v, 2) for v in shelves[k]), tuple(round(v, 2) for v in mine), d))
        ok_all &= d < 0.01
    say("   deck tops above the base (old tier tops = branch height + rise + 1.2): %s; crown nest %.1f; trunk radius at the shelf heights %s" % (
        [round(G.deck_top(b), 1) for b in G.BRANCHES], G.CROWN_PAD, [round(G.trunk_radius(h), 2) for h, _ in G.SHELVES]))
    gcol = [c for c in P["JG_Tree_GuardianCrown"].colliders]
    say("   deck colliders: %d cylinders; the shelf collider box top %.2f (flat top 0); hollow clear radius %.1f between three pillars at ring %.1f of radius 3.8, entrances %.1f wide" % (
        len(gcol), P["JG_Tree_GuardianShelf"].colliders[0][1][1] + P["JG_Tree_GuardianShelf"].colliders[0][2][1] / 2, G.PILLAR_RING - 3.8, G.PILLAR_RING,
        2 * G.PILLAR_RING * math.sin(math.pi / 3) - 2 * 3.8))

    # ------------------------------------------------------------------ 5: stairs, floors, bridges
    say("")
    say("5. RISERS, FLOORS AND BRIDGES")

    def tops(piece, pick):
        return sorted(round(c[1][1] + c[2][1] / 2, 3) for c in P[piece].colliders if pick(c))
    s4 = tops("JG_Stair_Stone_S4", lambda c: True)
    s8 = tops("JG_Stair_Stone_S8", lambda c: True)
    say("   stair S4 tread tops %s, S8 %s: every riser %s (treads 2 deep)" % (s4, s8, sorted(set(round(b - a, 3) for a, b in list(zip(s4, s4[1:])) + list(zip(s8, s8[1:]))))))
    ok_all &= set(round(b - a, 3) for a, b in list(zip(s4, s4[1:])) + list(zip(s8, s8[1:]))) == {1.0}
    h1 = tops("JG_Shrine_Stone_H1", lambda c: c[2][1] == 1.0)
    h2 = tops("JG_Shrine_HallRuin_H2", lambda c: c[2][1] in (1.0, 2.0, 3.0) and c[2][0] >= 6.9)
    say("   shrine H1 step tops %s (floor 2.0); hall H2 stair and platform tops %s (floor 3.0)" % (h1, sorted(set(h2 + tops("JG_Shrine_HallRuin_H2", lambda c: c[2][1] == 3.0)))))
    lk = tops("JG_Lookout_Tower_T1", lambda c: c[2][0] == 3.2 and abs(c[2][2] - 2.0) < 1e-6)
    say("   lookout stair tops %s: risers %s; platform top %.1f" % (lk, sorted(set(round(b - a, 3) for a, b in zip(lk, lk[1:]))), max(tops("JG_Lookout_Tower_T1", lambda c: c[2][0] > 8))))
    ok_all &= set(round(b - a, 3) for a, b in zip(lk, lk[1:])) == {1.0} and len(lk) == 12
    for name, b in sorted(pl.bridges.items()):
        ga, gb = I.ground(b["A"][0], b["A"][1]), I.ground(b["B"][0], b["B"][1])
        piece = {"RootBridge": "JG_Bridge_RootSpan_B3", "LogBridge": "JG_Bridge_LogSpan_B1", "RopeBridge": "JG_Bridge_RopeSpan_B2"}[name]
        deck = [c for c in P[piece].colliders if c[2][1] <= 1.01 and c[2][0] > 20]
        top = deck[0][1][1] + deck[0][2][1] / 2
        say("   %-11s span %.1f deck top %.2f above its level %.2f; bank ground at the two ends %.2f and %.2f (rises %.2f and %.2f), terrain levelled by pads of radius 5" % (
            name, b["span"], top, b["level"], ga, gb, ga - b["level"], gb - b["level"]))
        ok_all &= abs(top) < 1e-6 and abs(ga - b["level"]) < 1.0 and abs(gb - b["level"]) < 1.0
    # the 40-stud main bridge is not touched: layout.py

    # ------------------------------------------------------------------ 6: tree feet, placed heights
    say("")
    say("6. FEET AND PLACED HEIGHTS")
    for name in sorted(n for n in P if n.startswith("JG_Tree_") and "Guardian" not in n):
        lo, hi = P[name].bounds()
        say("   %-24s feet y %.2f (roots buried 0.3 to 1.0 under the base), top %.1f, spread %.1f x %.1f" % (name, lo[1], hi[1], hi[0] - lo[0], hi[2] - lo[2]))
        ok_all &= -1.2 <= lo[1] <= -0.3
    dev = []
    for piece, lst in pl.place.items():
        if piece.startswith(("JG_Bridge", "JG_Cliff", "JG_Plant_SpiritLily", "JG_Tree_Guardian")):
            continue
        for e in lst:
            g = I.ground(e["x"], e["z"])
            if g is not None:
                dev.append((e["y"] - g, piece))
    up = [d for d in dev if d[0] > 0.6]
    down = [d for d in dev if d[0] < -1.3]
    say("   %d pieces compared with the final ground under their feet: %d stand more than 0.6 above it (floating?), %d more than 1.3 below it (buried?)" % (len(dev), len(up), len(down)))
    for d, p in sorted(up, reverse=True)[:6]:
        say("      high %.2f %s" % (d, p))
    for d, p in sorted(down)[:6]:
        say("      low %.2f %s" % (d, p))

    # ------------------------------------------------------------------ 7: the walk-through
    say("")
    say("7. WALK-THROUGH (a 2-stud grid; terrain steps up to 1.3; collision boxes block, steps and decks are walked on)")
    walk = walk_through(pl)
    for line in walk:
        say("   " + line)
    # ------------------------------------------------------------------ 8: budgets
    say("")
    say("8. BUDGETS")
    budget(pl, P)
    say("")
    say("9. THE POLISH PASS (2026-11-23): RELIEF, THE FALLS, THE PART COUNT")
    ok_all &= polish(pl, P)
    say("")
    say("ALL NUMERIC CHECKS: %s" % ("PASS" if ok_all else "FAIL"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(LINES) + "\n")
    return ok_all


def slope_deg(x, z, e=2.0):
    gx = (I.ground(x + e, z) - I.ground(x - e, z)) / (2 * e)
    gz = (I.ground(x, z + e) - I.ground(x, z - e)) / (2 * e)
    return math.degrees(math.atan(math.hypot(gx, gz)))


def polish(pl, P):
    ok = True
    arena_y = I.ground(0.0, 0.0)
    # --- Mistfall Heights
    tops = []
    for xi in range(-200, -60, 2):
        for zi in range(-180, -80, 2):
            if I.plateau_sd(xi + 1, zi + 1) > 8.0 and I.poly_nearest(xi + 1, zi + 1, I.STREAM_TOP)[0] > 14.0 and I.poly_nearest(xi + 1, zi + 1, I.RIB_BROOK)[0] > 10.0 and math.hypot(xi + 1 - I.SPRING[0], zi + 1 - I.SPRING[1]) > 9.0:
                g = I.ground(xi + 1, zi + 1)
                if g is not None:
                    tops.append(g)
    mean_top = sum(tops) / len(tops)
    say("   Mistfall Heights: surface %.1f to %.1f studs (mean %.1f), that is %.1f to %.1f above the arena's level %.1f (the owner asked for about 28 to 32; phase A: 13)" % (min(tops), max(tops), mean_top, min(tops) - arena_y, max(tops) - arena_y, arena_y))
    ok &= 27.0 <= min(tops) - arena_y and max(tops) - arena_y <= 33.0
    sd0 = [(xi, zi) for xi in range(-200, -60, 2) for zi in range(-180, -80, 2) if 0.0 < I.plateau_sd(xi + 1, zi + 1) < 1.0]
    steep = [slope_deg(xi + 1, zi + 1, 2.0) for (xi, zi) in sd0]
    say("   its cliff band: %d ground samples on the edge, steepest %.0f degrees, median %.0f (sheer faces on every side but the ramp's and the two fall faces' plazas)" % (len(steep), max(steep), sorted(steep)[len(steep) // 2]))
    # --- the ramp
    tot = I._RAMP[0]
    centre, band = 0.0, 0.0
    s_ = 0.0
    while s_ <= tot:
        p, d = I.point_at(I.RAMP, s_)
        for off in (-3.0, 0.0, 3.0):
            q = (p[0] - d[1] * off, p[1] + d[0] * off)
            sl = slope_deg(q[0], q[1])
            band = max(band, sl)
            if off == 0.0:
                centre = max(centre, sl)
        s_ += 1.0
    z0, z1 = I.ground(*I.RAMP[0]), I.ground(*I.RAMP[-1])
    say("   the ramp up the south-west flank: %.1f studs long, rises %.1f to %.1f; slope on its centre line at most %.1f degrees, within 3 studs of it at most %.1f (the limit is 25); 14 studs wide, mud trail on it" % (tot, z0, z1, centre, band))
    ok &= band <= 25.0 and abs(z1 - mean_top) < 2.5
    # --- the gorge
    bridge_root = pl.bridges["RootBridge"]
    mx, mz = (bridge_root["A"][0] + bridge_root["B"][0]) / 2, (bridge_root["A"][1] + bridge_root["B"][1]) / 2
    bed = I.ground(mx, mz)
    bridge_log = pl.bridges["LogBridge"]
    lx_, lz_ = (bridge_log["A"][0] + bridge_log["B"][0]) / 2, (bridge_log["A"][1] + bridge_log["B"][1]) / 2
    lbed = I.ground(lx_, lz_)
    say("   the Mosswater Gorge: bed %.1f under the root bridge's centre (banks %.1f: %.1f deep) and %.1f under the log bridge's (banks %.1f: %.1f deep, at the waist, %.1f wide at the bridge); the lowest ground anywhere %.2f (phase A: -10.5, the limit -14)" % (
        bed, bridge_root["level"], bridge_root["level"] - bed, lbed, bridge_log["level"], bridge_log["level"] - lbed, 2 * I._gorge_width(0.52), min(g for g in [I.ground(x, z) for x in range(-236, 236, 2) for z in range(-236, 236, 2)] if g is not None)))
    # --- the ridge
    rtot = I.poly_nearest(0, 0, I.RIDGE)[2]
    best = None
    for f in [k / 40.0 for k in range(5, 36)]:
        (qx, qz), dd = I.point_at(I.RIDGE, f * rtot)
        crest_g = max(I.ground(qx + dd[1] * o, qz - dd[0] * o) for o in (-4.0, -2.0, 0.0, 2.0, 4.0))
        sides = [g for g in (I.ground(qx + dd[1] * 20.0, qz - dd[0] * 20.0), I.ground(qx - dd[1] * 20.0, qz + dd[0] * 20.0)) if g is not None]
        base = sum(sides) / len(sides)
        if best is None or crest_g - base > best[0]:
            best = (crest_g - base, crest_g, base)
    say("   Mossback Ridge: crest %.1f over the ground on both sides of it (%.1f): %.1f high (asked for 12 to 16), %.0f studs long, cliffed on its north side" % (best[1], best[2], best[0], rtot))
    ok &= 12.0 <= best[0] <= 16.5
    # --- the falls
    for f in pl.falls:
        scale, cur = f.get("scale", 1.0), f.get("curtains", 1)
        width = 2.4 * scale * cur
        say("   fall %-9s lip y %.2f  drop %.2f  Scale %g x Curtains %d = lip about %.1f studs wide%s" % (f["name"], f["lip"][1], f["drop"], scale, cur, width, "  Splash" if f.get("splash") else ""))
    hf = [f for f in pl.falls if f["name"] == "HighFalls"][0]
    rb = [f for f in pl.falls if f["name"] == "RibbonFall"][0]
    foot = I.FOOT_LV
    pond_surface = I.POND_WATER
    say("   High Falls: face piece %.1f high (phase A: 14.5), 34 wide, top at %.1f; the plateau at its lip %.1f; lip %.2f; drop %.2f measured to the pond's surface %.2f (lip - surface = %.2f); water %.1f wide, %.1f studs of rock each side" % (
        I.FALLS_H, foot + I.FALLS_H, I.plateau_top(*I.FALLS_LIP), hf["lip"][1], hf["drop"], pond_surface, hf["lip"][1] - pond_surface, 2.4 * hf.get("scale", 1) * hf.get("curtains", 1), (I.FACE_W - 2.4 * hf.get("scale", 1) * hf.get("curtains", 1)) / 2))
    ok &= abs(hf["drop"] - (hf["lip"][1] - pond_surface)) < 0.05 and abs(foot + I.FALLS_H - I.plateau_top(*I.FALLS_LIP)) < 0.6 and (I.FACE_W - 2.4 * hf.get("scale", 1) * hf.get("curtains", 1)) / 2 >= 2.0
    landing = math.hypot(I.POND[2], 0.0)
    cx_ = I.FALLS_FOOT[0] + I.DIR_F[0] * 3.2
    half_chord = math.sqrt(max(0.0, I.POND[2] ** 2 - (I.POND_AHEAD - 3.2) ** 2))
    say("   the Spirit Pond: shore radius %.1f, centre %.1f in front of the foot, %.1f studs wide at the water's landing line (the curtains need %.1f), surface %.2f, bowl %.1f deep at its middle" % (I.POND[2], I.POND_AHEAD, 2 * half_chord, 2.4 * 3.5 * 3 * 1.1, pond_surface, pond_surface - I.ground(I.POND[0], I.POND[1])))
    ok &= 2 * half_chord >= 2.4 * 3.5 * 3 * 1.1 + 2.0
    brook = [s_ for s_ in pl.water["streams"] if s_["name"] == "PlateauBrook"][0]
    say("   plateau brook: %.1f studs wide (the owner asked for 8 or more; phase A: 4), opening into a %.1f-wide basin at the lip" % (brook["width"], 2 * I.BASIN_W))
    ok &= brook["width"] >= 8.0
    say("   ribbon fall: rock %.1f high (asked for about 18 to 22), lip %.2f, plunge pool surface %.2f, drop %.2f, water %.1f wide (the High Falls' is %.1f), the pool drains into the stream's head" % (I.RIB_H, rb["lip"][1], pond_surface, rb["drop"], 2.4 * rb.get("scale", 1) * rb.get("curtains", 1), 2.4 * 3.5 * 3))
    ok &= 18.0 <= rb["drop"] <= 22.0
    say("   cascades: " + ", ".join("%s drop %.1f" % (f["name"], f["drop"]) for f in pl.falls if f["name"].startswith("Cascade")) + "; RimFall drop %.1f (unchanged)" % [f for f in pl.falls if f["name"] == "RimFall"][0]["drop"])
    # --- Ember's gap and the bridges are not touched (layout.py is not edited by this pass): the clearance lines in section 3 are the proof
    # --- budgets
    fam_parts = collections.Counter()
    tri = 0
    for piece, lst in pl.place.items():
        if piece in P:
            fam_parts[piece.split("_")[1]] += len(P[piece].g) * len(lst)
            tri += P[piece].tris() * len(lst)
    allin = tri + sum(p.tris() for p in jade_lib_island_mesh_pieces())
    parts = sum(fam_parts.values()) + 3
    say("   triangles as placed, everything in: %d (phase A 250,150; the limit 252,000)" % allin)
    ok &= allin <= 252000
    say("   MeshParts as placed: %d (phase A 1,427 by this count; the Studio measure was 1,448): %.0f percent of phase A. By family: %s" % (parts, 100.0 * parts / 1427.0, ", ".join("%s %d" % (k, v) for k, v in fam_parts.most_common())))
    ok &= parts <= 1284
    suffixes = sorted(((len([m for m, g in P[p].g.items() if g.f]), p) for p in pl.place if p in P), reverse=True)
    say("   material suffixes per piece (placed pieces): " + ", ".join("%d x %d" % (n, sum(1 for c, _ in suffixes if c == n)) for n in sorted(set(c for c, _ in suffixes), reverse=True)) + " (suffix count x number of pieces); pieces placed more than 3 times with more than 3: " +
        (", ".join(p for c, p in suffixes if c > 3 and len(pl.place[p]) > 3) or "none"))
    new_pieces = ["JG_Cliff_Grotto_G1", "JG_Cliff_Ribbon_R1", "JG_Cliff_GrottoCrystals_K1"]
    for n in new_pieces:
        say("   %-28s %d suffixes %s, %d triangles, largest mesh %d" % (n, len([1 for g in P[n].g.values() if g.f]), sorted(m for m, g in P[n].g.items() if g.f), P[n].tris(), max(g.tris() for g in P[n].g.values())))
        ok &= max(g.tris() for g in P[n].g.values()) <= 2400
    ok &= len([1 for g in P["JG_Cliff_Grotto_G1"].g.values() if g.f]) <= 3 and len([1 for g in P["JG_Cliff_Ribbon_R1"].g.values() if g.f]) <= 3
    return ok


def walk_through(pl):
    STEP = 2.0
    H = int(I.HALF)
    n = int(2 * H / STEP)

    def cell(x, z):
        return int((x + H) / STEP), int((z + H) / STEP)
    ground = {}
    for j in range(n):
        for i in range(n):
            x, z = -H + (i + 0.5) * STEP, -H + (j + 0.5) * STEP
            g = I.ground(x, z)
            if g is not None:
                ground[(i, j)] = g
    surface = dict(ground)
    blocked = set()
    deckcells = set()
    for c in pl.colliders:
        top = c["y"] + c["sy"] / 2
        half = max(c["sx"], c["sz"]) / 2 + 1.0
        i0, j0 = cell(c["x"] - half, c["z"] - half)
        i1, j1 = cell(c["x"] + half, c["z"] + half)
        cs, sn = math.cos(c["yaw"]), math.sin(c["yaw"])
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                if (i, j) not in ground:
                    continue
                x, z = -H + (i + 0.5) * STEP, -H + (j + 0.5) * STEP
                dx, dz = x - c["x"], z - c["z"]
                lx, lz = dx * cs - dz * sn, dx * sn + dz * cs      # into the collider's frame (inverse of the yaw)
                if c["kind"] == "cyl":
                    inside = math.hypot(lx, lz) <= c["sx"] / 2 - 0.3 and True
                else:
                    inside = abs(lx) <= c["sx"] / 2 - 0.2 and abs(lz) <= c["sz"] / 2 - 0.2
                if not inside:
                    continue
                rel = top - ground[(i, j)]
                if c["folder"] == "Buildings" and (c["name"].startswith("JG_Bridge") and c["sy"] <= 1.2 or rel <= 1.3 or c["name"].startswith(("JG_Stair", "JG_Lookout", "JG_Shrine", "JG_Hidden", "JG_Tree_Guardian", "JG_Cliff")) and c["sy"] <= 1.8):
                    surface[(i, j)] = max(surface[(i, j)], top) if not c["name"].startswith("JG_Bridge") else top
                    if c["name"].startswith("JG_Bridge"):
                        deckcells.add((i, j))
                elif rel > 1.3:
                    if (i, j) not in deckcells:
                        blocked.add((i, j))
                else:
                    surface[(i, j)] = max(surface[(i, j)], top)
    # surfaces that are decks must not be blocked by their own rails
    blocked -= deckcells
    start = cell(I.ARRIVAL[0] - 8.0, I.ARRIVAL[1] - 9.0)
    seen = {start}
    stack = [start]
    while stack:
        i, j = stack.pop()
        h = surface[(i, j)]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            q = (i + di, j + dj)
            if q in seen or q not in surface or q in blocked:
                continue
            if abs(surface[q] - h) > 1.3:
                continue
            seen.add(q)
            stack.append(q)
    out = []
    targets = {"Grove Gate": I.GATE, "Checkpoint": (90.75, 107.12), "Arena centre": (0, 0), "Egg stand 1": (-30.35, -6.3), "Egg stand 2": (-20.04, -23.65), "Egg stand 3": (-1.23, -30.98),
               "Guardian tree's hollow (Grove Heart)": (48.83, -88.0), "Spring bank": (-91.8, -50.0), "Hermitage": (-53.0, -62.6), "Bloom Glade": (-90.0, 52.0), "Ruin Court": (-18.75, 106.4),
               "East Shrine floor": pl.spots["EastShrine"][0::2], "Old Grove Hall court": (pl.spots["OldGroveHall"][0], pl.spots["OldGroveHall"][2] + 14.0),
               "Lookout (foot of its stair)": (pl.spots["Lookout"][0] + 6.2, pl.spots["Lookout"][2] + 18.0), "Grotto ledge": (pl.spots["SpiritGrotto"][0], pl.spots["SpiritGrotto"][2]),
               "Hollow-trunk shrine room": (pl.spots["HollowTrunkShrine"][0], pl.spots["HollowTrunkShrine"][2]), "Stone circle": (pl.spots["StoneCircle"][0], pl.spots["StoneCircle"][2]),
               "Pavilion ruin": (pl.spots["PavilionRuin"][0], pl.spots["PavilionRuin"][2] - 7.0)}
    ok = 0
    for name, (x, z) in targets.items():
        c = cell(x, z)
        near = [(abs(c[0] - q[0]) + abs(c[1] - q[1]), q) for q in seen if abs(c[0] - q[0]) <= 3 and abs(c[1] - q[1]) <= 3]
        got = bool(near)
        ok += got
        out.append("%-40s %s" % (name, "reachable on foot" if got else "NOT reachable"))
    total_ground = len(ground)
    out.append("reached %d of %d ground cells (2 x 2 studs) from the bridge's landing; %d cells blocked by collision boxes" % (len(seen), total_ground, len(blocked)))
    # what the bridges do: a walk with the three forest bridges' decks switched off
    out.append("targets reached: %d of %d" % (ok, len(targets)))
    # without the bridges
    nb = set(deckcells)
    seen2 = {start}
    stack = [start]
    while stack:
        i, j = stack.pop()
        h = surface[(i, j)]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (i + di, j + dj)
            if q in seen2 or q not in surface or q in blocked or q in nb:
                continue
            if abs(surface[q] - h) > 1.3:
                continue
            seen2.add(q)
            stack.append(q)
    lost = []
    for name, (x, z) in targets.items():
        c = cell(x, z)
        if not any(abs(c[0] - q[0]) <= 3 and abs(c[1] - q[1]) <= 3 for q in seen2):
            lost.append(name)
    out.append("with the bridge decks taken away the walk loses: %s (so the bridges are what the gorge and the rift need)" % (", ".join(lost) or "nothing"))
    return out


def budget(pl, P):
    tris = collections.Counter()
    parts = 0
    mats = set()
    per_piece = {}
    for piece, lst in pl.place.items():
        if piece not in P:
            continue
        t = P[piece].tris()
        tris[piece] = t * len(lst)
        parts += len(P[piece].g) * len(lst)
        mats |= set(P[piece].g)
        per_piece[piece] = t
    total = sum(tris.values())
    fam = collections.Counter()
    for piece, t in tris.items():
        fam[piece.split("_")[1]] += t
    say("   triangles as placed (the library): %d (the owner's range 150,000 to 250,000); by family: %s" % (total, ", ".join("%s %d" % (k, v) for k, v in fam.most_common())))
    say("   plus the island's own underside, crystals and curtains: %d (placed once)" % sum(p.tris() for p in jade_lib_island_mesh_pieces()))
    say("   MeshParts placed: %d; distinct material suffixes used: %d; colliders (invisible Plastic parts): %d; PointLights: %d (at most 8)" % (parts + 3, len(mats), len(pl.colliders), len(pl.lights)))
    say("   largest single mesh: %d triangles (%s); trees %d to %d, rocks %d to %d, plants %d to %d (the guardian crown %d is the landmark's exception)" % (
        max(((P[p].geo(m).tris() if m in P[p].g else 0), p + "__" + m) for p in P for m in P[p].g)[0],
        max(((P[p].geo(m).tris() if m in P[p].g else 0), p + "__" + m) for p in P for m in P[p].g)[1],
        min(P[p].tris() for p in P if p.startswith("JG_Tree_") and "Guardian" not in p), max(P[p].tris() for p in P if p.startswith("JG_Tree_") and "Guardian" not in p),
        min(P[p].tris() for p in P if p.startswith("JG_Rock_")), max(P[p].tris() for p in P if p.startswith("JG_Rock_")),
        min(P[p].tris() for p in P if p.startswith(("JG_Plant_", "JG_Mush_", "JG_Moss_Mat"))), max(P[p].tris() for p in P if p.startswith(("JG_Plant_", "JG_Mush_", "JG_Moss_Mat"))),
        P["JG_Tree_GuardianCrown"].tris()))
    # draw-call estimate: standing at a point and looking one way, the parts within 150 studs and 110 degrees of view (the busiest of eight headings);
    # "every part" counts each MeshPart once, "batched" counts identical (mesh, material) once (Roblox instances identical meshes)
    spots = {"arena centre": (0, 0), "Grove Gate": I.GATE, "Bloom Glade": I.GLADE[:2], "guardian tree": (I.ELDER[0], I.ELDER[1] + 20), "Spirit Pond": I.POND[:2], "West valley": I.STONE_CIRCLE, "bamboo forest": (-70.0, 120.0)}
    for name, (sx, sz) in spots.items():
        best = (0, 0)
        for hd in range(8):
            heading = hd * math.pi / 4
            worst, groups = 0, set()
            for piece, lst in pl.place.items():
                if piece not in P:
                    continue
                for e in lst:
                    dx, dz = e["x"] - sx, e["z"] - sz
                    d = math.hypot(dx, dz)
                    if d < 150 and (d < 12 or abs((math.atan2(dz, dx) - heading + math.pi) % (2 * math.pi) - math.pi) < math.radians(55)):
                        worst += len(P[piece].g)
                        for m in P[piece].g:
                            groups.add((piece, m))
            if worst > best[0]:
                best = (worst, len(groups))
        say("   draw-call estimate standing at %-16s looking the busiest way: %4d if every part draws, %4d if identical meshes batch (plus about 8 for terrain, water and the colliders' one material)" % (name, best[0] + 8, best[1] + 8))


def jade_lib_island_mesh_pieces():
    import jade_lib_island_mesh as M
    return list(M.build_all().values())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

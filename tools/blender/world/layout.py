"""World layout for the five floating islands: one source of truth for island placement and the
routes between them. Coordinates are Roblox studs (X east, Y up, Z south; north is -Z).

Since 2026-11-01 every route is a bridge (the owner's decision: the stepping stones made the
islands too hard to reach). Players run, use Qinggong, or ride the sword along it; a Qi barrier
at its start lets through only players of the destination's unlock rank. The stepping-stone data
below (gap, leaps) is kept for reference; `route_stones` returns no stones for a bridged route.

    python3 tools/blender/world/layout.py            # print the layout, check the bridges
    python3 tools/blender/world/layout.py --write    # also write src/worldbuild/Placements/Bridges.lua
"""
import math

# Measured in Studio (QinggongController rules, Roblox gravity): air leaps -> (flat reach, peak height).
REACH = {1: (31, 14), 2: (50, 21), 3: (71, 28), 4: (97, 34), 5: (124, 41), 6: (153, 48), 7: (187, 55)}
LANDING_CLEARANCE = 3  # studs of peak height left over when landing on a raised stone

ISLANDS = {
    "StartingIsland": {"centre": (0, 200, 0), "radius": 95},
    "JadeGrove": {"centre": (330, 206, -70), "radius": 80},
    "EmberPeak": {"centre": (-318, 222, 262), "radius": 75},
    "MoonlitIsle": {"centre": (80, 392, -330), "radius": 60},
    "OriginAbyss": {"centre": (-560, 95, -540), "radius": 85},
}

# Each route leaves one island's rim and lands on another's. `leaps` is the air-leap count of
# the rank that unlocks the destination; every gap must be reachable with it and out of reach
# with one leap fewer. `gap` is the planned horizontal spacing between stones.
ROUTES = {
    "JadeRoute": {"from": (100, 200, -12), "to": (252, 206, -52), "leaps": 2, "gap": 40},
    "EmberRoute": {"from": (-72, 200, 72), "to": (-262, 224, 214), "leaps": 3, "gap": 57},
    "MoonlitRoute": {"from": (8, 204, -96), "to": (66, 392, -272), "leaps": 4, "climb": 27},
    "OriginRoute": {"from": (-78, 200, -70), "to": (-470, 200, -430), "leaps": 6, "gap": 132},
}


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def flat(a, b):
    return math.hypot(b[0] - a[0], b[2] - a[2])


def route_stones(name):
    """Stone positions (top centres) between a route's ends, evenly spaced. A bridged route has
    none (the island scripts then place no stones)."""
    r = ROUTES[name]
    if name in BRIDGES:
        return [], 1
    a, b = r["from"], r["to"]
    if "climb" in r:
        steps = math.ceil((b[1] - a[1]) / r["climb"])
    else:
        steps = max(1, round(flat(a, b) / r["gap"]))
    return [lerp(a, b, i / steps) for i in range(1, steps)], steps


def check():
    ok = True
    for name, r in ROUTES.items():
        if name in BRIDGES:
            continue
        stones, steps = route_stones(name)
        pts = [r["from"]] + stones + [r["to"]]
        n = r["leaps"]
        for p, q in zip(pts, pts[1:]):
            d, dy = flat(p, q), q[1] - p[1]
            reach, peak = REACH[n]
            lower_reach, lower_peak = REACH[n - 1]
            can = d <= reach and dy <= peak - LANDING_CLEARANCE
            blocked = d > lower_reach or dy > lower_peak - LANDING_CLEARANCE
            if not (can and blocked):
                ok = False
            print(f"  {name}: gap {d:6.1f} rise {dy:+6.1f}  rank-ok={can}  lower-rank-blocked={blocked}")
        print(f"{name}: {steps} gaps, {len(stones)} stones")
    return ok


# ---------- bridges ----------
# Ends measured in Studio on 2026-11-01: `start` is on the Starting Island's ground 6 studs past
# the route's waystone and 14 to its side (so the waystone stands beside the gate, not on the deck;
# Moonlit's goes to the other side, clear of a spirit pine),
# `end` on the destination's ground just inside its arrival (the Grove Gate,
# the Ember Gate, the Crescent Arch, the Origin Route's Descent Ledge). Heights are the ground's.
# `rise` lifts the middle of a level bridge into a gentle arch. Moonlit Isle is 192 studs higher
# than the rim it leaves, so its bridge is a stairway of three flights zigzagging `swing` studs to
# each side, with a landing at each turn.
DECK_WIDTH = 20          # studs (doubled at the owner's request): room to pass, and to ride the sword along it
MAX_SLOPE = 34           # degrees; Roblox characters walk up far steeper, but stairs past this read as a wall
SEGMENT = 12             # studs per deck piece along a span

BRIDGES = {
    "JadeRoute": {"theme": "Jade", "rank": "QiGatherer", "start": (93.6, 198.4, -20.6), "end": (250.2, 206.0, -52.2), "rise": 7},
    "EmberRoute": {"theme": "Ember", "rank": "QiAwakener", "start": (-65.3, 198.4, 76.7), "end": (-261.4, 222.0, 213.4), "rise": 9},
    "MoonlitRoute": {"theme": "Moon", "rank": "FoundationInitiate", "start": (26.6, 199.0, -88.6), "end": (65.0, 392.0, -273.8),
                     "swing": 78, "landing": 15, "approach": (0.2425, -0.9701), "approach_len": 18},
    "OriginRoute": {"theme": "Origin", "rank": "DivineInitiate", "start": (-81.4, 198.4, -61.7), "end": (-468.0, 200.3, -428.0), "rise": 14},
}


def bridge_nodes(name):
    """The deck's centre line as nodes (x, y, z, landing): consecutive nodes are joined by deck
    pieces; a landing node gets a round platform."""
    b = BRIDGES[name]
    s, e = b["start"], b["end"]
    if "swing" in b:
        fx, fz = e[0] - s[0], e[2] - s[2]
        length = math.hypot(fx, fz)
        ux, uz = fx / length, fz / length
        lx, lz = -uz, ux                                   # to the side
        w = b["swing"]
        corners = [(s[0] + fx / 3 + lx * w, s[2] + fz / 3 + lz * w), (s[0] + 2 * fx / 3 - lx * w, s[2] + 2 * fz / 3 - lz * w)]
        pts = [(s[0], s[2])] + corners + [(e[0], e[2])]
        landing = [False, True, True, False]
        if "approach" in b:   # the last stretch runs straight in, square to the arrival (the Crescent Arch)
            ax, az = b["approach"]
            pts.insert(-1, (e[0] - ax * b["approach_len"], e[2] - az * b["approach_len"]))
            landing.insert(-1, False)
        r = b["landing"]
        # the flights climb between the landings' rims; each landing is level (rim in, centre, rim out)
        flights = []
        for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
            dx, dz = p1[0] - p0[0], p1[1] - p0[1]
            d = math.hypot(dx, dz)
            ux, uz = dx / d, dz / d
            a0 = r if landing[i] else 0
            a1 = r if landing[i + 1] else 0
            flights.append(((p0[0] + ux * a0, p0[1] + uz * a0), (p1[0] - ux * a1, p1[1] - uz * a1)))
        climb = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in flights)
        y = s[1]
        nodes = [(s[0], y, s[2], False)]
        for i, (p, q) in enumerate(flights):
            y += (e[1] - s[1]) * math.hypot(q[0] - p[0], q[1] - p[1]) / climb
            nodes.append((q[0], y, q[1], False))
            if landing[i + 1]:
                cx, cz = pts[i + 1]
                nxt = flights[i + 1][0]
                nodes.append((cx, y, cz, True))
                nodes.append((nxt[0], y, nxt[1], False))
        return nodes
    n = max(2, round(flat(s, e) / SEGMENT))
    nodes = []
    for i in range(n + 1):
        t = i / n
        x, y, z = lerp(s, e, t)
        nodes.append((x, y + b["rise"] * 4 * t * (1 - t), z, False))   # a parabolic arch
    return nodes


def check_bridges():
    ok = True
    for name in BRIDGES:
        nodes = bridge_nodes(name)
        steep, length = 0, 0
        for a, b in zip(nodes, nodes[1:]):
            d = math.hypot(b[0] - a[0], b[2] - a[2])
            length += math.hypot(d, b[1] - a[1])
            steep = max(steep, math.degrees(math.atan2(abs(b[1] - a[1]), d)))
        good = steep <= MAX_SLOPE
        ok = ok and good
        print(f"{name}: {len(nodes) - 1} spans, {length:.0f} studs long, steepest {steep:.1f} deg {'OK' if good else 'TOO STEEP'}")
    return ok


def write_bridges(path=None):
    import os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "worldbuild", "Placements", "Bridges.lua")
    lines = ["-- Generated by tools/blender/world/layout.py (--write): the bridges between the islands. Don't edit",
             "-- by hand: change BRIDGES there and run it again. Positions are world studs; Nodes trace the deck's",
             "-- centre line (its top surface), Landing marks a round platform (LandingRadius) at a turn.",
             "return {", f"    DeckWidth = {DECK_WIDTH},", "    Bridges = {"]
    for name, b in BRIDGES.items():
        lines.append(f'        {name} = {{ Theme = "{b["theme"]}", RankId = "{b["rank"]}", LandingRadius = {b.get("landing", 0)}, Nodes = {{')
        for x, y, z, landing in bridge_nodes(name):
            lines.append(f"            {{ Position = Vector3.new({x:.2f}, {y:.2f}, {z:.2f}), Landing = {'true' if landing else 'false'} }},")
        lines.append("        } },")
    lines += ["    },", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    import sys
    for n, isl in ISLANDS.items():
        print(n, isl)
    print("ALL BRIDGES WALKABLE" if check_bridges() else "SOME BRIDGES TOO STEEP")
    if "--write" in sys.argv:
        print("wrote", write_bridges())

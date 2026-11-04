"""World layout: one source of truth for island placement and the bridges between them.
Coordinates are Roblox studs (X east, Y up, Z south; north is -Z).

Since 2026-11-01 (the owner's map) Yggdrasil is the hub at the centre, about 500 studs across, and
the four outer islands stand in a row north of it, west to east in unlock order (Jade Grove, Ember
Peak, Moonlit Isle, Origin Abyss), every island's ground at Y 200. Each outer island keeps the shape
it was authored with and is placed by its centre and `turns`: quarter turns, each adding 90 degrees
of bearing ((x, z) -> (-z, x)), chosen so its gate faces Yggdrasil and its bridge runs straight.
Quarter turns keep its terrain grid exact; every move is a whole number of 4-stud voxels.

Since 2026-11-02 the harder an island, the farther it stands (the owner's rule): each bridge takes
about four seconds longer to run than the last at its unlock rank's run speed (GameConfig.Qinggong):
Jade ~200 studs (Qi Gatherer, 24 studs/s), Ember ~320 (Qi Awakener, 26), Moonlit ~460 (Foundation
Initiate, 28; the sword flies it in ~10 s), Origin ~650 (Divine Initiate, 32). The islands sit on
their old bearings from Yggdrasil, moved out until their bridges measure that.

    python3 tools/blender/world/layout.py            # print the layout, check the bridges
    python3 tools/blender/world/layout.py --write    # also write src/worldbuild/Placements/Bridges.lua
"""
import math

ISLANDS = {
    "Yggdrasil": {"centre": (0, 200, 0), "radius": 250, "turns": 0},
    "JadeGrove": {"centre": (-384, 200, -448), "radius": 160, "turns": 0},
    "EmberPeak": {"centre": (-128, 200, -696), "radius": 150, "turns": 0},
    "MoonlitIsle": {"centre": (192, 200, -804), "radius": 125, "turns": 0},
    "OriginAbyss": {"centre": (596, 200, -856), "radius": 165, "turns": 0},
    # east of the hub, the first island a player crosses to (the owner, 2026-11-04): open from the
    # start, its bridge about five seconds' run at a beginner's speed
    "BeginnerIsle": {"centre": (468, 200, -124), "radius": 140, "turns": 0},
}

# Each island's arrival, where its bridge lands (island-local, before turning): just inside its gate
# (the Grove Gate, the Ember Gate, the Crescent Arch, and on Origin Abyss the Gate of Descent).
ARRIVALS = {
    "JadeGrove": (99.8, 0.0, 117.8),    # since the island doubled (2026-11-02): its old bridge end
    "EmberPeak": (26.6, 0.0, 146.6),    # since the island doubled (2026-11-02): its old bridge end
    "MoonlitIsle": (-27.0, 0.0, 118.2),    # since the island doubled (2026-11-02): its old bridge end
    "OriginAbyss": (-85.8, 0.0, 122.8),    # since the island doubled (2026-11-02): its old bridge end
    "BeginnerIsle": (-114.1, 0.0, 30.2),   # on the line from the hub to the island's centre
}
HUB_EXIT_RADIUS = 245    # bridges leave Yggdrasil's ground this far from its centre


def turn(v, turns):
    """Island-local (x, y, z) turned by quarter turns, each adding 90 degrees of bearing."""
    x, y, z = v
    for _ in range(turns % 4):
        x, z = -z, x
    return (x, y, z)


def to_world(island, local):
    c = ISLANDS[island]["centre"]
    x, y, z = turn(local, ISLANDS[island]["turns"])
    return (c[0] + x, c[1] + y, c[2] + z)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def flat(a, b):
    return math.hypot(b[0] - a[0], b[2] - a[2])


# ---------- bridges ----------
# The bridges fan out from Yggdrasil as on the owner's map, each straight from Yggdrasil's ground
# (HUB_EXIT_RADIUS out, facing its island) to just inside its island's gate (ARRIVALS). Level at
# Y 200, arching gently: the middle rises RISE of the length (so the ends never climb more than
# about 6 degrees). No landings: the owner wants each bridge one straight span.
DECK_WIDTH = 40          # studs (doubled twice at the owner's request): room to pass, and to ride the sword along it
MAX_SLOPE = 34           # degrees; Roblox characters walk up far steeper, but stairs past this read as a wall
SEGMENT = 12             # studs per deck piece along a span
RISE = 0.025

ROUTES = {
    "JadeRoute": {"island": "JadeGrove", "theme": "Jade", "rank": "QiGatherer"},
    "EmberRoute": {"island": "EmberPeak", "theme": "Ember", "rank": "QiAwakener"},
    "MoonlitRoute": {"island": "MoonlitIsle", "theme": "Moon", "rank": "SoulAwakening"},
    "OriginRoute": {"island": "OriginAbyss", "theme": "Origin", "rank": "DivineInitiate"},
    "BeginnerRoute": {"island": "BeginnerIsle", "theme": "Lion", "rank": "QiInitiate"},
}


def bridge_path(name):
    """(start on Yggdrasil, end at the island's arrival), world studs."""
    end = to_world(ROUTES[name]["island"], ARRIVALS[ROUTES[name]["island"]])
    hub = ISLANDS["Yggdrasil"]["centre"]
    ux, uz = end[0] - hub[0], end[2] - hub[2]
    u = math.hypot(ux, uz)
    start = (hub[0] + ux / u * HUB_EXIT_RADIUS, hub[1], hub[2] + uz / u * HUB_EXIT_RADIUS)
    return start, end


BRIDGES = {}
for _name, _route in ROUTES.items():
    _start, _end = bridge_path(_name)
    BRIDGES[_name] = {"theme": _route["theme"], "rank": _route["rank"],
                      "start": tuple(round(v, 1) for v in _start), "end": tuple(round(v, 1) for v in _end)}


def bridge_nodes(name):
    """The deck's centre line as nodes (x, y, z), SEGMENT studs or so apart, arching."""
    a, b = BRIDGES[name]["start"], BRIDGES[name]["end"]
    rise = RISE * flat(a, b)
    n = max(1, round(flat(a, b) / SEGMENT))
    out = []
    for i in range(n + 1):
        t = i / n
        x, y, z = lerp(a, b, t)
        out.append((x, y + rise * 4 * t * (1 - t), z))
    return out


def check_bridges():
    ok = True
    names = list(BRIDGES)
    for name in names:
        nodes = bridge_nodes(name)
        steep, length = 0, 0
        for a, b in zip(nodes, nodes[1:]):
            d = math.hypot(b[0] - a[0], b[2] - a[2])
            length += math.hypot(d, b[1] - a[1])
            steep = max(steep, math.degrees(math.atan2(abs(b[1] - a[1]), d)))
        good = steep <= MAX_SLOPE
        ok = ok and good
        print(f"{name}: {len(nodes) - 1} spans, {length:.0f} studs long, steepest {steep:.1f} deg {'OK' if good else 'TOO STEEP'}")
    # no two bridges come within a deck's width of each other, and none passes another's island
    legs = {name: [(p, q) for p, q in zip(_corners(name), _corners(name)[1:])] for name in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            gap = min(_segment_gap(p, q) for p in legs[a] for q in legs[b])
            if gap < DECK_WIDTH * 1.5:
                ok = False
                print(f"{a} and {b} come within {gap:.0f} studs")
    for name in names:
        for island, info in ISLANDS.items():
            if island in ("Yggdrasil", ROUTES[name]["island"]):
                continue
            if min(_distance_to_segment(info["centre"], s, e) for s, e in legs[name]) < info["radius"] + DECK_WIDTH:
                ok = False
                print(f"{name} passes too close to {island}")
    return ok


def _corners(name):
    b = BRIDGES[name]
    return [b["start"], b["end"]]


def _segment_gap(a, b):
    (p1, p2), (q1, q2) = a, b
    def o(p, q, r):
        return (q[0] - p[0]) * (r[2] - p[2]) - (q[2] - p[2]) * (r[0] - p[0])
    if o(p1, p2, q1) * o(p1, p2, q2) < 0 and o(q1, q2, p1) * o(q1, q2, p2) < 0:
        return 0.0
    return min(_distance_to_segment(q1, p1, p2), _distance_to_segment(q2, p1, p2),
               _distance_to_segment(p1, q1, q2), _distance_to_segment(p2, q1, q2))


def _distance_to_segment(c, s, e):
    vx, vz = e[0] - s[0], e[2] - s[2]
    t = max(0.0, min(1.0, ((c[0] - s[0]) * vx + (c[2] - s[2]) * vz) / (vx * vx + vz * vz)))
    return math.hypot(c[0] - (s[0] + vx * t), c[2] - (s[2] + vz * t))


def write_bridges(path=None):
    import os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "worldbuild", "Placements", "Bridges.lua")
    lines = ["-- Generated by tools/blender/world/layout.py (--write): the bridges between the islands. Don't edit",
             "-- by hand: change ROUTES there and run it again. Positions are world studs; Nodes trace the deck's",
             "-- centre line (its top surface).",
             "return {", f"    DeckWidth = {DECK_WIDTH},", "    Bridges = {"]
    for name, b in BRIDGES.items():
        lines.append(f'        {name} = {{ Theme = "{b["theme"]}", RankId = "{b["rank"]}", Nodes = {{')
        for x, y, z in bridge_nodes(name):
            lines.append(f"            {{ Position = Vector3.new({x:.2f}, {y:.2f}, {z:.2f}) }},")
        lines.append("        } },")
    lines += ["    },", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    import sys
    for n, isl in ISLANDS.items():
        print(n, isl)
    for n, b in BRIDGES.items():
        print(n, b["start"], "->", b["end"])
    print("ALL BRIDGES GOOD" if check_bridges() else "SOME BRIDGES BAD")
    if "--write" in sys.argv:
        print("wrote", write_bridges())

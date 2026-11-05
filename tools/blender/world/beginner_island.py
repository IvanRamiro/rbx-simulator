"""The Beginner Isle: the outer court of a cultivation sect, the first island a player crosses to.

East of Yggdrasil, its bridge open from the start. Authored in island-local Roblox studs (x east,
z south, y up; ground ~0 = world Y 200), unturned (TURNS 0: local axes are the world's).

The idea: a place you come to learn. Everything looks used and looked after, a working training
ground and not a ruin, a forest or a volcano. The other islands are places you dare to enter; this
one has a front gate.

- The Lion Gate on the west rim, where the bridge lands: a three-bay lacquered archway.
- The Lion Court in the middle: a level round of flagstones where the Awakened Stone Lion sits on
  its paw-print medallion, facing the gate. The three egg stands stand in an arc behind it, just
  past its engage radius. Nothing else stands in the court.
- The Hall of First Breath behind them, closing the view from the gate.
- The training yard to the south: packed earth, wooden dummies, weapon racks and lifting stones.
- The meditation pavilion on a low knoll to the north.
- The great bell on the north-east side of the court.
- Round the rest, spirit pines, plum blossom and mossy rocks, on Yggdrasil's own meadow palette.
"""
import math

import layout as L

NAME = "BeginnerIsle"
CENTRE = L.ISLANDS[NAME]["centre"]
TURNS = L.ISLANDS[NAME]["turns"]

ARRIVAL = (L.ARRIVALS[NAME][0], L.ARRIVALS[NAME][2])
ARRIVAL_BEARING = math.degrees(math.atan2(ARRIVAL[1], ARRIVAL[0]))
BACK_BEARING = ARRIVAL_BEARING + 180
_IN = (-ARRIVAL[0] / math.hypot(*ARRIVAL), -ARRIVAL[1] / math.hypot(*ARRIVAL))


def polar(bearing, r):
    a = math.radians(bearing)
    return (math.cos(a) * r, math.sin(a) * r)


GATE = (ARRIVAL[0] + _IN[0] * 15, ARRIVAL[1] + _IN[1] * 15)     # the Lion Gate, on the path in
ARENA_R, ARENA_EDGE = 52, 56                                     # the paving, then cobbles to the edge
RING_R = 62                                                      # the path round the court
LAIR = (0.0, 0.0)
EGG_RING = 31
EGG_BEARINGS = [BACK_BEARING + d for d in (-38, 0, 38)]
EGG_SPOTS = [polar(b, EGG_RING) for b in EGG_BEARINGS]
HALL = polar(BACK_BEARING, 96)
YARD = polar(ARRIVAL_BEARING - 95, 90)                          # z positive: south
YARD_R = 24
PAVILION = polar(ARRIVAL_BEARING + 95, 92)                      # z negative: north
PAVILION_R = 11
BELL = polar(BACK_BEARING - 58, 84)

BASE_R = 130.0
LOBES = [(ARRIVAL_BEARING, 8, 22), (BACK_BEARING, 10, 34), (ARRIVAL_BEARING - 95, 6, 30), (ARRIVAL_BEARING + 95, 5, 26)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = BASE_R
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    return r + 7.0 * fbm(math.cos(theta) * 2.4 + 21, math.sin(theta) * 2.4 - 13, seed=411, octaves=3)


def _ring(b):
    return polar(b, RING_R)


def _bearing(p):
    return math.degrees(math.atan2(p[1], p[0]))


PATHS = [
    [ARRIVAL, GATE, _ring(ARRIVAL_BEARING)],
    [_ring(b) for b in range(0, 361, 15)],
    [_ring(BACK_BEARING), polar(BACK_BEARING, 80)],
    [_ring(_bearing(YARD)), polar(_bearing(YARD), 90 - YARD_R + 4)],
    [_ring(_bearing(PAVILION)), polar(_bearing(PAVILION), 92 - PAVILION_R)],
    [_ring(_bearing(BELL)), polar(_bearing(BELL), 84 - 8)],
]


def _seg(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def _flatten(h, x, z, c, rad, soft, lift):
    from worldlib import smoothstep
    w = 1 - smoothstep(rad, rad + soft, math.hypot(x - c[0], z - c[1]))
    return h * (1 - w) + lift * w


def _spoke_distance(x, z):
    """To the ways off the court, leaving out its ring (the apron paves that)."""
    return min(_seg(x, z, a, b) for k, line in enumerate(PATHS) if k != 1 for a, b in zip(line, line[1:]))


DIG = 0.8   # the most the ground is let down under paving on a slope
ROAD_BED = 0.35   # and at least this under a road, off the court's level ground


def edge_distance(x, z):
    return rim(math.atan2(z, x)) - math.hypot(x, z)


def _base(x, z):
    from worldlib import fbm, smoothstep
    e = edge_distance(x, z)
    if e <= 0:
        return None
    h = 1.3 * fbm(x / 34 + 7, z / 34 - 3, seed=421, octaves=3) + 0.25 * fbm(x / 9, z / 9, seed=422, octaves=2)
    h = _flatten(h, x, z, GATE, 16, 8, 0.0)
    h = _flatten(h, x, z, LAIR, RING_R + 2, 10, 0.0)
    h = _flatten(h, x, z, HALL, 26, 8, 0.0)
    h = _flatten(h, x, z, YARD, YARD_R, 8, 0.0)
    h = _flatten(h, x, z, PAVILION, PAVILION_R, 11, 3.0)       # the knoll
    h = _flatten(h, x, z, BELL, 9, 6, 0.0)
    h = _flatten(h, x, z, ARRIVAL, 14, 6, 0.0)
    h -= 3.0 * (1 - smoothstep(1, 8, e)) ** 1.5
    # the bridge comes in over the rim: the ground stays under its deck, from the arrival out
    ux, uz = -_IN[0], -_IN[1]
    along = x * ux + z * uz
    across = abs(x * uz - z * ux)
    r0 = math.hypot(*ARRIVAL) - 9       # the abutment starts 8 studs in from the arrival
    if across < 25:
        h = min(h, 0.0 - 0.6 * smoothstep(r0 - 5, r0, along) - 0.2 * max(0, along - r0))
    return h


def height(x, z):
    from worldlib import fbm
    h = _base(x, z)
    if h is None:
        return None, None
    a = math.hypot(x, z)
    # the court's flat cobbles; earth under all the other paving (island_upgrades.py), because terrain grass grows up through a mesh
    if a < ARENA_EDGE:
        return h, "Cobblestone"
    if a < 68 or _spoke_distance(x, z) < 5.5:
        return h, "Ground"
    # no grass under the bridge: blades would grow up through the abutment
    ux, uz = -_IN[0], -_IN[1]
    if x * ux + z * uz > math.hypot(*ARRIVAL) - 14 and abs(x * uz - z * ux) < 25:
        return h, "Ground"
    if math.hypot(x - YARD[0], z - YARD[1]) < YARD_R + 3.5:
        return h, "Ground"
    if edge_distance(x, z) < 3.0 + 2.0 * fbm(x / 11, z / 11, seed=432, octaves=2):
        return h, "Rock"
    return h, "Grass"


MATERIALS = ["Grass", "Ground", "Rock", "Cobblestone"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    # the island is turned by a fraction of a quarter turn: each world cell asks for the height at its
    # place on the unturned island
    a = math.radians(TURNS * 90)
    ca, sa = math.cos(a), math.sin(a)

    def under_paving(x, z):
        """The terrain, not the paving: where the land rises (the pavilion's knoll) the 4-stud voxels round up over the meshes laid on
        height(), so the ground under and beside them is let down a little (island_upgrades.py, the apron and the roads)."""
        from worldlib import smoothstep
        h, mat = height(x, z)
        if h is None:
            return h, mat
        a_ = math.hypot(x, z)
        road = 1 - smoothstep(7.5, 11.0, _spoke_distance(x, z))
        rise = min(max(h + 0.05, 0.0), DIG) * max(road, 1 - smoothstep(69.0, 73.0, a_))
        return h - max(rise, ROAD_BED * road if a_ > 66 else 0.0), mat

    def turned(x, z):
        return under_paving(x * ca + z * sa, -x * sa + z * ca)
    return W.export_heightfield(NAME, CENTRE, 4, 160, turned, MATERIALS, path, priority=[("Cobblestone", 2)], turns=TURNS, baked_turn=True)

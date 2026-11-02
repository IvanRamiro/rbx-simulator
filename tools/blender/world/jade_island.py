"""Jade Grove: the ancient forest island, first in the row north of Yggdrasil.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200), unturned
(TURNS 0: local axes are the world's).

Since 2026-11-02 (the owner's upgrade) the island is twice as wide (about 300 studs across) and
built round an open middle: the **Mantis Arena**, a level ring of grass bordered in jade
flagstones, where the Bamboo Mantis Sage keeps its lair at the centre and the three egg stands
stand in an arc behind it, away from the bridge. Nothing stands in the arena; the forest, the
landmarks and their relics ring it:
- the arrival terrace and the Grove Gate on the south-east rim, where the Jade bridge lands
  (the island moved out along its bridge, which didn't change);
- the Elder Jade Tree on its knoll to the north-east (Grove Heart in its hollow, Jade Seed in its
  crown);
- the Whispering Hollow to the north-west (a spring pool and the Whispering Spring relic);
- the Bloom Glade to the south-west: a flagstone sanctuary ringed by standing stones, the Mantis
  Sage's safe zone, where a stolen egg is secured;
- the Ruin Court to the south, broken pillars round a clearing.
A path rings the arena; spokes run from it to each landmark and to the gate.
"""
import math

import layout as L

NAME = "JadeGrove"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

ARRIVAL = (L.ARRIVALS[NAME][0], L.ARRIVALS[NAME][2])   # where the Jade bridge lands
_IN = (-ARRIVAL[0] / math.hypot(*ARRIVAL), -ARRIVAL[1] / math.hypot(*ARRIVAL))   # from the arrival toward the centre


def _toward_centre(d):
    return (ARRIVAL[0] + _IN[0] * d, ARRIVAL[1] + _IN[1] * d)


LANDING = (*_toward_centre(14), 13)        # the arrival terrace: centre x, z, radius
GATE = _toward_centre(28)                  # the Grove Gate, facing the arrival

ARENA = (0.0, 0.0)                         # the Mantis Arena's centre
ARENA_R = 44                               # its level grass; flagstones to ARENA_EDGE
ARENA_EDGE = 50
ARENA_Y = 0.6
RING_R = 57                                # the path round it
LAIR = ARENA                               # the Mantis Sage's lair, facing the gate
EGG_RING = 31                              # the egg stands' arc behind the lair, just outside its EngageRadius (26)


def _polar(bearing, r):
    a = math.radians(bearing)
    return (math.cos(a) * r, math.sin(a) * r)


ARRIVAL_BEARING = math.degrees(math.atan2(ARRIVAL[1], ARRIVAL[0]))
EGG_BEARINGS = [ARRIVAL_BEARING + 180 + d for d in (-38, 0, 38)]

GLADE = (*_polar(150, 104), 17)            # Bloom Glade: the safe zone; flat at +1
ELDER = (*_polar(-62, 104), 24)            # Elder Jade Tree knoll: top +7
HOLLOW = (*_polar(-148, 100), 15)          # Whispering Hollow: floor -7
HOLLOW_POOL = (HOLLOW[0] + 2, HOLLOW[1] - 2, 6.5)
POOL_BED, POOL_WATER = -8.6, -7.2
RUINS = (*_polar(100, 108), 16)            # the Ruin Court

# Rim radius by bearing (theta = atan2(z, x); east 0, south +90, north -90): lobes and bays, pulled
# in toward Ember Peak (north-east) and out at the arrival.
LOBES = [(ARRIVAL_BEARING, 6, 20), (0, -8, 26), (-45, -10, 22), (-100, 10, 30), (-160, 12, 26), (150, 8, 28), (100, -6, 22)]
BASE_R = 150.0


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = BASE_R
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    r += 5.0 * fbm(math.cos(theta) * 2.6 + 21, math.sin(theta) * 2.6 + 9, seed=43, octaves=3)
    return r


def _ring_point(bearing):
    return _polar(bearing, RING_R)


def _spoke(bearing, end, steps=3):
    """A path from the ring at `bearing` out to `end`, bending gently."""
    a = _ring_point(bearing)
    mid = ((a[0] + end[0]) / 2 + (end[1] - a[1]) * 0.08, (a[1] + end[1]) / 2 - (end[0] - a[0]) * 0.08)
    return [a, mid, end]


def _edge_of(feature, bearing_from_centre, margin=2):
    """A point on a round feature's edge facing the arena."""
    fx, fz, fr = feature
    d = math.hypot(fx, fz)
    return (fx - fx / d * (fr - margin), fz - fz / d * (fr - margin))


PATHS = [
    [ARRIVAL, LANDING[:2], GATE, _ring_point(ARRIVAL_BEARING)],                             # arrival -> gate -> the ring
    [_polar(b, RING_R) for b in range(0, 361, 15)],                                        # the ring round the arena
    _spoke(150, _edge_of(GLADE, 150)),                                                     # -> Bloom Glade
    _spoke(-62, _edge_of(ELDER, -62)),                                                     # -> Elder Tree
    _spoke(-148, _edge_of(HOLLOW, -148, -2)),                                              # -> Whispering Hollow (descends)
    _spoke(100, _edge_of(RUINS, 100)),                                                     # -> Ruin Court
]


def _seg_dist(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg_dist(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def arena_distance(x, z):
    """How far (x, z) is from the arena's centre."""
    return math.hypot(x - ARENA[0], z - ARENA[1])


def _base(x, z):
    """Ground height before material choice (None outside the rim)."""
    from worldlib import fbm, smoothstep, gauss
    r = math.hypot(x, z)
    R = rim(math.atan2(z, x))
    if r > R:
        return None
    # rolling forest floor, a ridge along the north-west and a rise in the south-east
    h = 3.0 * fbm(x / 42 + 11, z / 42 - 3, seed=51, octaves=4)
    h += 5.0 * gauss((x + 70) * 0.5, z + 110, 26) * (1 + 0.4 * fbm(x / 14, z / 14, seed=52, octaves=2))
    h += 3.0 * gauss(x - 112, (z - 20) * 0.6, 18)
    # the Elder Tree knoll
    ex, ez, er = ELDER
    h += 7.0 * (1 - smoothstep(er * 0.35, er, math.hypot(x - ex, z - ez)))
    # the Whispering Hollow: a steep-sided bowl
    hx, hz, hr = HOLLOW
    d = math.hypot(x - hx, z - hz)
    bowl = 1 - smoothstep(hr * 0.55, hr, d)
    h = h * (1 - bowl) - 7.0 * bowl
    px, pz, pr = HOLLOW_POOL
    dp = math.hypot(x - px, z - pz) - pr
    if dp < 1.0:
        w = 1 - smoothstep(-2.0, 0.8, dp)
        h = h * (1 - w) + POOL_BED * w
    # flat terraces: the arrival, the glade, the ruin court and the arena (wide and dead level)
    for (cx, cz, rad), lift, soft in ((LANDING, 0.4, 7), (GLADE, 1.0, 8), (RUINS, 0.5, 8), ((*ARENA, RING_R + 2), ARENA_Y, 12)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    # paths worn in (not in the arena, which stays level)
    if arena_distance(x, z) > ARENA_EDGE:
        h -= 0.4 * (1 - smoothstep(2.4, 4.4, path_distance(x, z)))
    # rounded lip at the rim
    h -= 3.4 * (1 - smoothstep(R - 1, R - 12, r)) ** 1.6
    return h


def pool_distance(x, z):
    px, pz, pr = HOLLOW_POOL
    return math.hypot(x - px, z - pz) - pr


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    a = arena_distance(x, z)
    if a < ARENA_EDGE:   # the arena: grass inside a border of jade flagstones
        return h, "Sandstone" if a > ARENA_R else "LeafyGrass"
    # slope from finite differences: steep ground shows jade stone
    e = 1.5
    hs = [_base(x + dx, z + dz) for dx, dz in ((e, 0), (-e, 0), (0, e), (0, -e))]
    hs = [v if v is not None else h for v in hs]
    slope = math.hypot(hs[0] - hs[1], hs[2] - hs[3]) / (2 * e)
    if path_distance(x, z) < 3.8:
        mat = "Mud"
    elif slope > 0.75 or pool_distance(x, z) < 1.0:
        mat = "Sandstone"
    else:
        mat = "LeafyGrass"
    return h, mat


MATERIALS = ["LeafyGrass", "Mud", "Sandstone"]


def export_terrain(path=None):
    """Write src/worldbuild/Terrain/JadeGrove.lua for WorldBuilder.buildTerrain."""
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 176, height, MATERIALS, path, priority=[("Mud", 2)], turns=TURNS)

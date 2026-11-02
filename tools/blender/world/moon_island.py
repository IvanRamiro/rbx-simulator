"""Moonlit Isle: the highest island, pale and celestial, shaped like a crescent moon.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200).

Since 2026-11-02 (the owner's upgrade) the island is twice as wide (a moon disc about 250 studs
across), and moved out along its unchanged bridge. It keeps its crescent: a disc with a deep bay of
sky cut out of its north, its horns curling round it. The band is now broad enough to hold an open
middle, the **Lunar Court**: a level ring of moon paving bordered in salt-white stone, kept for
Moonlit Isle's guardian (still to come), its three egg pedestals in an arc at its back, looking out
over the bay. Nothing stands in it; round it, on the band:
- the arrival and the Crescent Arch on the south rim, where the Moonlit bridge lands;
- the Moon Mirror to the west: a round reflecting pool on a terrace, a crescent bridge out to the
  lotus dais and its relic;
- the Star Well on the west horn: a stone-ringed well brimming with starlight, its relic above it;
- the Celestial Pavilion on the east horn: eight porcelain pillars under a floating armillary.
A path rings the court; spokes run from it to each landmark and to the gate.
- Ground: pale limestone, moon-frost drifts, salt-white paths, paving on the terraces and the court.
"""
import math

import layout as L

NAME = "MoonlitIsle"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

BODY = (0.0, 0.0, 125.0)       # the full moon disc: centre x, z and radius
BITE = (0.0, -145.0, 85.0)     # the disc cut away to the north; its edge is the crescent's inner curve


def band_point(bearing_deg, frac):
    """A point across the crescent's band at a bearing from the body's centre: frac 0 on the
    inner (bay) shore, 1 on the outer shore. Bearings: 90 is south, 180 west, 0 east. Where the
    ray misses the bite (the south half), frac 0 is the body's centre."""
    bx, bz, br = BODY
    cx, cz, cr = BITE
    a = math.radians(bearing_deg)
    dx, dz = math.cos(a), math.sin(a)
    # where the ray from the body's centre leaves the bitten-away disc
    ox, oz = bx - cx, bz - cz
    b_ = ox * dx + oz * dz
    c_ = ox * ox + oz * oz - cr * cr
    disc = b_ * b_ - c_
    r_in = max(0.0, -b_ + math.sqrt(disc)) if disc > 0 else 0.0
    r = r_in + (br - r_in) * frac
    return (round(bx + dx * r, 1), round(bz + dz * r, 1))


def _polar(bearing, r):
    a = math.radians(bearing)
    return (BODY[0] + math.cos(a) * r, BODY[1] + math.sin(a) * r)


ARRIVAL = (L.ARRIVALS[NAME][0], L.ARRIVALS[NAME][2])   # where the Moonlit bridge lands
ARRIVAL_BEARING = math.degrees(math.atan2(ARRIVAL[1], ARRIVAL[0]))
_IN = (-ARRIVAL[0] / math.hypot(*ARRIVAL), -ARRIVAL[1] / math.hypot(*ARRIVAL))
LANDING = (ARRIVAL[0] + _IN[0] * 12, ARRIVAL[1] + _IN[1] * 12, 9)   # x, z, radius; flat at +0.4

ARENA = (0.0, 14.0)            # the Lunar Court, a little south of the disc's centre (the bay bites the north)
ARENA_R, ARENA_EDGE, ARENA_Y = 44, 50, 1.0
RING_R = 57
LAIR = ARENA                   # the guardian to come stands here, facing the gate
EGG_RING = 31
_LAIR_FACING = math.degrees(math.atan2(ARRIVAL[1] - ARENA[1], ARRIVAL[0] - ARENA[0]))
EGG_BEARINGS = [_LAIR_FACING + 180 + d for d in (-38, 0, 38)]   # about the court's centre


def court_point(bearing, r):
    a = math.radians(bearing)
    return (ARENA[0] + math.cos(a) * r, ARENA[1] + math.sin(a) * r)


MIRROR = _polar(172, 96) + (13,)         # Moon Mirror terrace (west): centre, radius; flat at +1.2
MIRROR_POOL_R = 10.0
WELL = _polar(-148, 98) + (6,)           # Star Well (west horn): centre, ring radius
WELL_SHAFT_R, WELL_FLOOR = 3.2, -4.0     # a shallow bowl under the starlight surface (voxels can't hold a narrow open shaft)
PAVILION = _polar(-30, 98) + (10,)       # Celestial Pavilion terrace (east horn): centre, radius; flat at +2.6


def _court_spoke(target, inset):
    """A path from the court's ring out to a feature's arena-facing side."""
    tx, tz = target[0], target[1]
    b = math.degrees(math.atan2(tz - ARENA[1], tx - ARENA[0]))
    a = court_point(b, RING_R)
    d = math.hypot(tx - ARENA[0], tz - ARENA[1])
    end = (ARENA[0] + (tx - ARENA[0]) * (d - inset) / d, ARENA[1] + (tz - ARENA[1]) * (d - inset) / d)
    return [a, ((a[0] + end[0]) / 2, (a[1] + end[1]) / 2), end]


JUNCTION = _court_spoke(MIRROR, MIRROR[2])[-1]   # the Moon Mirror's bank facing the court: its crescent bridge starts here

PATHS = [
    [ARRIVAL, LANDING[:2], court_point(_LAIR_FACING, RING_R)],        # arrival -> landing (the Crescent Arch) -> the ring
    [court_point(b, RING_R) for b in range(0, 361, 15)],              # the ring round the court
    _court_spoke(PAVILION, PAVILION[2] + 1),                          # -> the pavilion
    _court_spoke(MIRROR, MIRROR[2]),                                  # -> the Moon Mirror's bank
    _court_spoke(WELL, WELL[2] + 3),                                  # -> the Star Well
]


def edge_distance(x, z):
    """Distance from (x, z) to the crescent's edge: positive inside the island, negative outside.
    A little noise keeps the coast from being a perfect arc."""
    from worldlib import fbm, smoothstep
    bx, bz, br = BODY
    cx, cz, cr = BITE
    inside_body = br - math.hypot(x - bx, z - bz)
    outside_bite = math.hypot(x - cx, z - cz) - cr
    base = min(inside_body, outside_bite)
    # the wobble only roughens the coast from the inside, so it never raises slivers of land in
    # the bay beyond the horn tips
    wobble = 2.6 * fbm(x / 24 + 41, z / 24 + 3, seed=121, octaves=3) * smoothstep(-0.5, 3.0, base)
    return base + wobble


def inside(x, z):
    return edge_distance(x, z) > 0


def _seg(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def arena_distance(x, z):
    return math.hypot(x - ARENA[0], z - ARENA[1])


def _base(x, z):
    from worldlib import fbm, smoothstep
    e = edge_distance(x, z)
    if e <= 0:
        return None
    # soft, wind-carved swells of moon frost
    h = 1.8 * fbm(x / 30 + 9, z / 30 - 4, seed=131, octaves=4) + 0.8
    for (cx, cz, rad), lift, soft in ((LANDING, 0.4, 6), (MIRROR, 1.2, 6), (PAVILION, 2.6, 5), ((*ARENA, RING_R + 2), ARENA_Y, 10)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    # the Star Well: a shaft straight down inside a small raised apron
    wx, wz, wr = WELL
    dw = math.hypot(x - wx, z - wz)
    h += 0.8 * (1 - smoothstep(wr, wr + 5, dw))
    if dw < WELL_SHAFT_R + 1.0:
        h = WELL_FLOOR + (h - WELL_FLOOR) * smoothstep(WELL_SHAFT_R - 0.5, WELL_SHAFT_R + 1.0, dw)
    if arena_distance(x, z) > ARENA_EDGE:
        h -= 0.3 * (1 - smoothstep(2.2, 3.8, path_distance(x, z)))
    h -= 3.0 * (1 - smoothstep(1, 10, e)) ** 1.6
    return h


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    from worldlib import fbm
    a = arena_distance(x, z)
    if a < ARENA_EDGE:   # the court: moon paving inside a salt-white border
        return h, "Salt" if a > ARENA_R else "Pavement"
    if path_distance(x, z) < 3.4:
        mat = "Salt"
    elif any(math.hypot(x - cx, z - cz) < rad + 1 for cx, cz, rad in (MIRROR, PAVILION)) or \
            math.hypot(x - WELL[0], z - WELL[1]) < WELL[2] + 2:
        mat = "Pavement"
    elif fbm(x / 20 - 5, z / 20 + 2, seed=132, octaves=3) > 0.15:
        mat = "Snow"      # moon-frost drifts
    else:
        mat = "Limestone"
    return h, mat


MATERIALS = ["Limestone", "Snow", "Salt", "Pavement"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 140, height, MATERIALS, path, priority=[("Salt", 2)], turns=TURNS)

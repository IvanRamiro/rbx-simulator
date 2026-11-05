"""Origin Abyss: the hidden endgame island, the last and farthest north-east of Yggdrasil.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200), unturned
(TURNS 0: local axes are the world's).

Since 2026-11-02 (the owner's upgrade) the island is twice as wide (about 320 studs across), moved
out along its unchanged bridge, and built round an open middle: the **Void Court**, a level court of
worn temple stone bordered by void-crystal crust, kept for Origin Abyss's guardian (still to come).
Its three obsidian egg plinths stand in an arc at its back, under the Thorn Crown, whose great
bronze branches rise from the court's rim behind them. Nothing stands in the court; round it:
- the Gate of Descent on the south-west rim, where the Origin bridge lands, and the ruined avenue,
  lined with snapped columns and fallen drums, running from it to the court;
- the fallen colossus, a giant carved head sunk in the ground to one side;
- the Rift: a void rift tearing a chord across the island's far side, behind the eggs, pinching
  and gaping as it goes; open sky shows through it. An ancient broken bridge crosses it where it
  narrows, its middle fallen away but for one hanging block;
- beyond the rift, the raised shelf, tilting up toward its far edge: the Origin Altar inside its
  ring of obsidian monoliths, and the Void Shard hanging 150 studs above it, reached by floating ruin
  fragments that each rise 49 studs (seven air leaps clear that, six do not).
- Ground: dark slate, worn avenue stone, void-crystal crust along the rift's lips and round the
  court; the temple terraces are paved with hewn slabs (meshes, in origin_meshes.py).
"""
import math

import layout as L

NAME = "OriginAbyss"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

ARRIVAL = (L.ARRIVALS[NAME][0], L.ARRIVALS[NAME][2])   # where the Origin bridge lands
ARRIVAL_BEARING = math.degrees(math.atan2(ARRIVAL[1], ARRIVAL[0]))
BACK_BEARING = ARRIVAL_BEARING + 180     # behind the court: the eggs, the rift, the altar
_IN = (-ARRIVAL[0] / math.hypot(*ARRIVAL), -ARRIVAL[1] / math.hypot(*ARRIVAL))


def _polar(bearing, r):
    a = math.radians(bearing)
    return (math.cos(a) * r, math.sin(a) * r)


GATE = (ARRIVAL[0] + _IN[0] * 16, ARRIVAL[1] + _IN[1] * 16, 10)   # Gate of Descent terrace: centre, radius; flat at +0.5

ARENA = (0.0, 0.0)                         # the Void Court: worn temple stone to ARENA_R, void crust to ARENA_EDGE
ARENA_R, ARENA_EDGE, ARENA_Y = 44, 50, 0.8
RING_R = 57
LAIR = ARENA                               # the guardian to come stands here, facing the gate
EGG_RING = 31
EGG_BEARINGS = [BACK_BEARING + d for d in (-38, 0, 38)]
EGG_SPOTS = [_polar(b, EGG_RING) for b in EGG_BEARINGS]
EGG_PAD_R = 5.0                            # the paved pad under each egg plinth

COLOSSUS = _polar(ARRIVAL_BEARING + 95, 104)   # the fallen colossus's head, off to the side

# the rift: a chord across the far side, RIFT_OFF from the centre, running along RIFT_DIR. The normal
# (-RIFT_DIR[1], RIFT_DIR[0]) points from the rift back toward the court and the gate.
RIFT_OFF = 96.0
_A = math.radians(ARRIVAL_BEARING)
RIFT_DIR = (math.sin(_A), -math.cos(_A))
RIFT_HALF = 7.0
BRIDGE_HALF = 7.6          # the rift is pinched to about this half-width where the bridge crosses

ALTAR = (*_polar(BACK_BEARING, 132), 16)   # Origin Altar terrace (on the shelf beyond the rift): centre, radius; flat at +7

BASE_R = 152.0
LOBES = [(ARRIVAL_BEARING, 6, 20), (BACK_BEARING, 14, 32), (ARRIVAL_BEARING + 95, 8, 30), (ARRIVAL_BEARING - 95, -6, 24),
         (BACK_BEARING + 55, 6, 18), (BACK_BEARING - 60, -8, 16)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = BASE_R
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    # a torn, shattered coast: sharper noise than the other islands
    r += 9.0 * W_abs(fbm(math.cos(theta) * 4 + 11, math.sin(theta) * 4 - 7, seed=161, octaves=4)) - 4.5
    return r


def W_abs(v):
    return abs(v) * 2


def _along(x, z):
    return x * RIFT_DIR[0] + z * RIFT_DIR[1]


def side(x, z):
    """Signed distance across the rift's centreline: positive on the court's side, negative on the
    shelf. The centreline meanders, so the rift reads as torn rather than cut."""
    from worldlib import fbm
    nx, nz = -RIFT_DIR[1], RIFT_DIR[0]
    along = _along(x, z)
    return x * nx + z * nz + RIFT_OFF + 14.0 * fbm(along / 38 + 5, 0.3, seed=172, octaves=2) + 4.0 * fbm(along / 9 + 9, 4.1, seed=174, octaves=2)


def rift_half(x, z):
    """Half the rift's width: pinched to about 4 studs in places and gaping to about 12 in others,
    with a jagged edge; held near BRIDGE_HALF where the bridge crosses (along 0, behind the court)."""
    from worldlib import fbm
    along = _along(x, z)
    free = RIFT_HALF + 5.0 * fbm(along / 18 + 3, 1.7, seed=171, octaves=2) + 1.4 * fbm(along / 4, 2.9, seed=173, octaves=2)
    pinch = math.exp(-(along / 12) ** 2)
    return free * (1 - pinch) + BRIDGE_HALF * pinch


def edge_distance(x, z):
    """Distance to the nearest edge (the coast or the rift's lip): positive on land."""
    coast = rim(math.atan2(z, x)) - math.hypot(x, z)
    lip = abs(side(x, z)) - rift_half(x, z)
    return min(coast, lip)


def _lip_toward(sign):
    """Where the bridge line (from the court toward the altar) meets the rift's lip on the court's
    side (sign 1) or the shelf's (-1)."""
    ux, uz = math.cos(math.radians(BACK_BEARING)), math.sin(math.radians(BACK_BEARING))
    lo, hi = 40.0, 160.0
    for _ in range(60):   # the first point along the line where the side drops to the lip
        mid = (lo + hi) / 2
        x, z = ux * mid, uz * mid
        if side(x, z) > rift_half(x, z):
            lo = mid
        else:
            hi = mid
    near = lo
    if sign > 0:
        return (round(ux * near, 2), round(uz * near, 2))
    lo, hi = near, 200.0
    for _ in range(60):   # then where it rises out of the rift on the far side
        mid = (lo + hi) / 2
        x, z = ux * mid, uz * mid
        if side(x, z) > -rift_half(x, z):
            lo = mid
        else:
            hi = mid
    return (round(ux * hi, 2), round(uz * hi, 2))


BRIDGE_SE, BRIDGE_NW = _lip_toward(1), _lip_toward(-1)   # where the broken bridge meets each lip (court side, shelf side)

# Landings at each bridge head that even out the ground the deck rests on. Both put the surface
# half-way up a voxel (world Y a multiple of 4), where Studio renders flat ground truest. Measured
# before the upgrade: the shelf landing renders flat at +5.1; the court-side one sits close to the
# lower lip (it renders from about +0.5 down to -0.6), so the deck reaches further inland there
# (origin_meshes.BRIDGE_INLAND / DECK_ENDS).
BRIDGE_PAD_LIFT = (1.0, 5.0)


def bridge_pads():
    """Centres (3.5 studs inland of each bridge head, along the bridge) and heights of the landings."""
    (ax, az), (bx, bz) = BRIDGE_SE, BRIDGE_NW
    d = math.hypot(bx - ax, bz - az)
    ux, uz = (bx - ax) / d, (bz - az) / d
    return [((ax - ux * 3.5, az - uz * 3.5), BRIDGE_PAD_LIFT[0]), ((bx + ux * 3.5, bz + uz * 3.5), BRIDGE_PAD_LIFT[1])]


def _ring_point(bearing):
    return _polar(bearing, RING_R)


def _bearing_of(p):
    return math.degrees(math.atan2(p[1], p[0]))


PATHS = [
    [ARRIVAL, GATE[:2], _ring_point(ARRIVAL_BEARING)],                                    # arrival -> gate -> the avenue to the court
    [_ring_point(b) for b in range(0, 361, 15)],                                           # the ring round the court
    [_ring_point(_bearing_of(COLOSSUS)), _polar(_bearing_of(COLOSSUS), 92)],               # the court -> the colossus head
    [_ring_point(BACK_BEARING), BRIDGE_SE],                                                # the court -> the rift bridge
    [BRIDGE_NW, (ALTAR[0] - math.cos(math.radians(BACK_BEARING)) * (ALTAR[2] - 2),
                 ALTAR[1] - math.sin(math.radians(BACK_BEARING)) * (ALTAR[2] - 2))],      # the far lip -> the Origin Altar
]


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
    s = side(x, z)
    # rubble-strewn ground; the shelf beyond the rift is raised and tilts up toward its far edge
    h = 2.0 * fbm(x / 28 + 3, z / 28 - 8, seed=181, octaves=4) + 1.2 * abs(fbm(x / 7, z / 7, seed=182, octaves=2))
    if s < 0:
        h += 5.0 + 0.09 * (-s)
    for (cx, cz, rad), lift, soft in ((GATE, 0.5, 6), (ALTAR, 7.0, 7), ((*ARENA, RING_R + 2), ARENA_Y, 10)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    if arena_distance(x, z) > ARENA_EDGE:
        h -= 0.35 * (1 - smoothstep(2.2, 3.8, path_distance(x, z)))
    # broken lips: the ground falls away at the coast and at the rift
    h -= 3.4 * (1 - smoothstep(1, 9, e)) ** 1.5
    for (px, pz), lift in bridge_pads():
        w = 1 - smoothstep(3.0, 6.0, math.hypot(x - px, z - pz))
        h = h * (1 - w) + lift * w
    return h


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    a = arena_distance(x, z)
    if a < ARENA_EDGE + 0.5:   # under the court's floor (r52): Sand, which renders level at its height, kept well inside the kerb because its colour is wrong for this island. Glacier's bumps came through the floor, and Concrete snaps to the voxel grid, a stud under it
        return h, "Sand"
    if a < ARENA_EDGE + 4:
        return h, "Concrete"
    lip = abs(side(x, z)) - rift_half(x, z)
    if path_distance(x, z) < 3.4:
        mat = "Concrete"
    elif 1.8 < lip < 5.0:
        mat = "Glacier"     # void-crystal crust set back from the rift's lip (the lip column itself
                            # forms the rift wall, which should stay dark slate)
    else:
        mat = "Slate"       # also under the temple terraces, which are paved with meshes (Brick
                            # terrain would snap their height to the 4-stud voxel grid)
    return h, mat


MATERIALS = ["Slate", "Concrete", "Glacier", "Sand"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 182, height, MATERIALS, path, priority=[("Concrete", 2)], turns=TURNS)

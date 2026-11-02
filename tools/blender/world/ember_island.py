"""Ember Peak: the volcanic island, second in the row north of Yggdrasil.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200), unturned
(TURNS 0: local axes are the world's).

Since 2026-11-02 (the owner's upgrade) the island is twice as wide (about 300 studs across) and
built round an open middle: the **Cinder Arena**, a dead-level ring of basalt bordered by cracked,
glowing lava rock, kept for Ember Peak's guardian (still to come). Its three egg pedestals stand
in an arc at its back, under the volcano. Nothing stands in the arena; round it:
- the arrival terrace and the Ember Gate on the south rim, where the Ember bridge lands (the
  island moved out along its bridge, which didn't change);
- the volcano to the north, looming behind the eggs: its caldera holds a lava lake with the
  Caldera Crown on a basalt pillar; basalt steps climb its arena-facing flank; a lava river runs
  from a notch in its rim to the north-west edge and pours off as a lavafall;
- the Ember Forge ruins to the east (Ember Heart);
- the Ash Plain to the west, its petrified grove and the Ashen Sigil monolith.
A path rings the arena; spokes run from it to each landmark and to the gate.
- Ground: black basalt with drifts of ash; cracked lava along the river, in the caldera and round
  the arena.
"""
import math

import layout as L

NAME = "EmberPeak"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

ARRIVAL = (L.ARRIVALS[NAME][0], L.ARRIVALS[NAME][2])   # where the Ember bridge lands
ARRIVAL_BEARING = math.degrees(math.atan2(ARRIVAL[1], ARRIVAL[0]))
_IN = (-ARRIVAL[0] / math.hypot(*ARRIVAL), -ARRIVAL[1] / math.hypot(*ARRIVAL))


def _toward_centre(d):
    return (ARRIVAL[0] + _IN[0] * d, ARRIVAL[1] + _IN[1] * d)


def _polar(bearing, r):
    a = math.radians(bearing)
    return (math.cos(a) * r, math.sin(a) * r)


LANDING = (*_toward_centre(14), 11)        # x, z, radius; flat at +0.5
GATE = _toward_centre(26)                  # the Ember Gate, across the path

ARENA = (0.0, 0.0)                         # the Cinder Arena: level basalt to ARENA_R, glowing border to ARENA_EDGE
ARENA_R, ARENA_EDGE, ARENA_Y = 44, 50, 0.5
RING_R = 57                                # the path round it
LAIR = ARENA                               # the guardian to come stands here, facing the gate
EGG_RING = 31                              # the egg pedestals' arc at the arena's back
EGG_BEARINGS = [ARRIVAL_BEARING + 180 + d for d in (-38, 0, 38)]

VOLCANO_BEARING = ARRIVAL_BEARING + 180    # straight behind the eggs
VOLCANO = (*_polar(VOLCANO_BEARING, 100), 36)   # centre, base radius
RIM_H, RIM_R, CRATER_FLOOR = 40.0, 14.0, 27.0   # crater rim height and radius, caldera floor
LAVA_LAKE = 29.0               # lava surface inside the caldera (about 9 studs across)
FORGE = (*_polar(ARRIVAL_BEARING - 110, 100), 14)   # Ember Forge terrace (east): centre, radius; flat at +2
ASH = (*_polar(ARRIVAL_BEARING + 95, 100), 17)      # Ash Plain (west): centre, radius; flat at +0.5

# the lava river: from the crater's notch away from the arena, to the north-west edge (the last point
# is moved onto the rim below, where the lavafall starts)
_RIVER_DIR = math.radians(VOLCANO_BEARING - 45)
RIVER = [(VOLCANO[0] + math.cos(_RIVER_DIR + w) * d, VOLCANO[1] + math.sin(_RIVER_DIR + w) * d)
         for d, w in ((13.5, 0.0), (27, 0.06), (44, 0.02), (60, -0.05), (78, -0.03))]
RIVER_HALF = 3.4

BASE_R = 145.0
LOBES = [(ARRIVAL_BEARING, 6, 20), (VOLCANO_BEARING, 8, 34), (VOLCANO_BEARING - 45, 4, 20), (ARRIVAL_BEARING - 110, 5, 24),
         (ARRIVAL_BEARING + 95, 6, 26), (ARRIVAL_BEARING + 140, -7, 18), (ARRIVAL_BEARING - 150, -6, 18)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = BASE_R
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    r += 5.0 * fbm(math.cos(theta) * 2.6 + 31, math.sin(theta) * 2.6 + 17, seed=71, octaves=3)
    return r


def _ring_point(bearing):
    return _polar(bearing, RING_R)


def _toward(feature, inset):
    """The point on a round feature's arena-facing side, `inset` in from its centre."""
    fx, fz = feature[0], feature[1]
    d = math.hypot(fx, fz)
    return (fx - fx / d * inset, fz - fz / d * inset)


def _bearing_of(point):
    return math.degrees(math.atan2(point[1], point[0]))


def _spoke(target):
    a = _ring_point(_bearing_of(target))
    return [a, ((a[0] + target[0]) / 2, (a[1] + target[1]) / 2), target]


PATHS = [
    [ARRIVAL, LANDING[:2], GATE, _ring_point(ARRIVAL_BEARING)],      # arrival -> gate -> the ring
    [_ring_point(b) for b in range(0, 361, 15)],                      # the ring round the arena
    _spoke(_toward(FORGE, FORGE[2] - 2)),                             # -> Ember Forge (its opening is this path's end)
    _spoke(_toward(ASH, ASH[2] - 4)),                                 # -> Ash Plain
    _spoke(_toward(VOLCANO, 27)),                                     # -> the volcano's flank, where the basalt steps start
]


def _seg(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def river_distance(x, z):
    return min(_seg(x, z, a, b) for a, b in zip(RIVER, RIVER[1:]))


def arena_distance(x, z):
    return math.hypot(x - ARENA[0], z - ARENA[1])


def notch_weight(x, z):
    """How much of the rim notch over the river applies at this bearing (0..1)."""
    vx, vz, _ = VOLCANO
    a = math.atan2(z - vz, x - vx)
    b = math.atan2(RIVER[0][1] - vz, RIVER[0][0] - vx)
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return math.exp(-(diff / 0.32) ** 2)


def volcano_height(x, z):
    """Concave flanks up to a rim at RIM_R, a caldera bowl inside it, and a notch in the rim
    where the lava lake overflows into the river."""
    from worldlib import smoothstep
    vx, vz, vr = VOLCANO
    d = math.hypot(x - vx, z - vz)
    if d >= vr:
        return 0.0
    rim_h = RIM_H - (RIM_H - LAVA_LAKE + 0.6) * notch_weight(x, z)
    if d >= RIM_R:
        return rim_h * ((vr - d) / (vr - RIM_R)) ** 1.35
    return CRATER_FLOOR + (rim_h - CRATER_FLOOR) * smoothstep(RIM_R - 7, RIM_R, d)


def _base(x, z):
    from worldlib import fbm, smoothstep
    r = math.hypot(x, z)
    R = rim(math.atan2(z, x))
    if r > R:
        return None
    h = 2.2 * fbm(x / 36 + 5, z / 36 - 9, seed=81, octaves=4)
    h += 1.6 * abs(fbm(x / 9, z / 9, seed=82, octaves=3))   # broken lava-rock ground
    # flat terraces (the volcano rises after, so the arena's flattening never cuts its toe)
    for (cx, cz, rad), lift, soft in ((LANDING, 0.5, 6), (FORGE, 2.0, 7), (ASH, 0.5, 8), ((*ARENA, RING_R + 2), ARENA_Y, 10)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    h += volcano_height(x, z) * (1 + 0.05 * fbm(x / 7, z / 7, seed=83, octaves=2))
    # the lava river's channel, cut into the flank and the plain
    rd = river_distance(x, z)
    if rd < RIVER_HALF + 3:
        cut = 1 - smoothstep(RIVER_HALF - 0.5, RIVER_HALF + 3, rd)
        h -= 2.6 * cut
    if arena_distance(x, z) > ARENA_EDGE:
        h -= 0.4 * (1 - smoothstep(2.2, 4.2, path_distance(x, z)))
    h -= 3.6 * (1 - smoothstep(R - 1, R - 12, r)) ** 1.6
    return h


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    from worldlib import fbm
    a = arena_distance(x, z)
    if a < ARENA_EDGE:   # the arena: level basalt inside a glowing border of cracked lava rock
        return h, "CrackedLava" if a > ARENA_R else "Basalt"
    vx, vz, vr = VOLCANO
    dv = math.hypot(x - vx, z - vz)
    if path_distance(x, z) < 3.6:
        mat = "Sand"
    elif river_distance(x, z) < RIVER_HALF + 2.2 or dv < RIM_R - 2:
        mat = "CrackedLava"
    elif math.hypot(x - ASH[0], z - ASH[1]) < ASH[2] + 4 or fbm(x / 22 + 3, z / 22, seed=84, octaves=2) > 0.32:
        mat = "Asphalt"   # ash drifts
    else:
        mat = "Basalt"
    return h, mat


MATERIALS = ["Basalt", "CrackedLava", "Asphalt", "Sand"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 172, height, MATERIALS, path, priority=[("Sand", 2)], turns=TURNS)


def _clip_river_to_rim():
    """Cut the river where it first reaches the island edge (where the lavafall begins)."""
    def inside(x, z):
        return math.hypot(x, z) < rim(math.atan2(z, x)) - 1.0
    for k in range(1, len(RIVER)):
        a, b = RIVER[k - 1], RIVER[k]
        if not inside(*b):
            lo, hi = 0.0, 1.0
            for _ in range(40):
                t = (lo + hi) / 2
                if inside(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t):
                    lo = t
                else:
                    hi = t
            end = (round(a[0] + (b[0] - a[0]) * lo, 2), round(a[1] + (b[1] - a[1]) * lo, 2))
            del RIVER[k:]
            RIVER.append(end)
            return
    raise ValueError("the lava river never reaches the rim: lengthen it")


_clip_river_to_rim()

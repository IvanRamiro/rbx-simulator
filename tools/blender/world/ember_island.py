"""Ember Peak: the volcanic island, second in the row north of Yggdrasil.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200).
Features:
- Arrival: the Ember Route lands on the north-east rim at a landing guarded by the Ember Gate.
- The volcano rises in the middle; its caldera holds a lava lake with the Caldera Crown on a
  basalt pillar in the centre.
- A lava river runs from a notch in the crater rim down a carved channel to the south-west
  edge, where it pours off the island as a lavafall.
- Around the volcano:
  - the Ember Forge ruins (south-east, Ember Heart);
  - the Ash Plain with its petrified grove and the Ashen Sigil monolith (west);
  - the Phoenix Altar egg shrine (north-west).
- Ground: black basalt with drifts of ash; cracked lava along the river and in the caldera.
"""
import math

import layout as L

NAME = "EmberPeak"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

ARRIVAL = (56, -48)            # where the Ember bridge lands (about layout.ARRIVALS["EmberPeak"])
LANDING = (48, -40, 10)        # x, z, radius; flat at +0.5
VOLCANO = (-6, 8, 36)          # centre, base radius
RIM_H, RIM_R, CRATER_FLOOR = 40.0, 14.0, 27.0   # crater rim height and radius, caldera floor
LAVA_LAKE = 29.0               # lava surface inside the caldera (about 9 studs across)
FORGE = (34, 30, 14)           # Ember Forge terrace: centre, radius; flat at +2
ASH = (-50, -12, 17)           # Ash Plain: centre, radius; flat at +0.5
ALTAR = (-24, -44, 13)         # Phoenix Altar: centre, radius; flat at +1
RIVER = [(-15, 18), (-24, 28), (-36, 40), (-47, 52), (-58, 63)]  # crater notch -> south-west edge
                               # (the last point is moved onto the rim below, where the lavafall starts)
RIVER_HALF = 3.4

LOBES = [(0, 6, 20), (-40, 12, 18), (50, 8, 22), (130, -5, 16), (-130, 9, 20), (175, 7, 18), (95, -4, 12)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = 74.0
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    r += 4.0 * fbm(math.cos(theta) * 2.6 + 31, math.sin(theta) * 2.6 + 17, seed=71, octaves=3)
    return r


JUNCTION = (22, -22)
PATHS = [
    [ARRIVAL, (48, -40), (36, -32), JUNCTION],                      # arrival -> gate -> junction
    [JUNCTION, (2, -38), (-14, -42)],                               # junction -> Phoenix Altar
    [JUNCTION, (34, -6), (38, 12), (36, 20)],                       # junction -> Ember Forge (east of the volcano)
    [(2, -38), (-20, -28), (-38, -18)],                             # altar path -> Ash Plain
    [(30, -10), (20, -6)],                                          # spur to the foot of the basalt steps
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
    vx, vz, vr = VOLCANO
    dv = math.hypot(x - vx, z - vz)
    h = 1.8 * fbm(x / 26 + 5, z / 26 - 9, seed=81, octaves=4)
    rough = 1.6 * abs(fbm(x / 9, z / 9, seed=82, octaves=3))   # broken lava-rock ground
    h += rough
    h += volcano_height(x, z) * (1 + 0.05 * fbm(x / 7, z / 7, seed=83, octaves=2))
    # the lava river's channel, cut into the flank and the plain
    rd = river_distance(x, z)
    if rd < RIVER_HALF + 3:
        cut = 1 - smoothstep(RIVER_HALF - 0.5, RIVER_HALF + 3, rd)
        h -= 2.6 * cut
    # flat terraces
    for (cx, cz, rad), lift, soft in ((LANDING, 0.5, 6), (FORGE, 2.0, 7), (ASH, 0.5, 8), (ALTAR, 1.0, 7)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    h -= 0.4 * (1 - smoothstep(2.0, 3.8, path_distance(x, z)))
    h -= 3.6 * (1 - smoothstep(R - 1, R - 10, r)) ** 1.6
    return h


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    from worldlib import fbm
    vx, vz, vr = VOLCANO
    dv = math.hypot(x - vx, z - vz)
    if path_distance(x, z) < 3.4:
        mat = "Sand"
    elif river_distance(x, z) < RIVER_HALF + 2.2 or dv < RIM_R - 2:
        mat = "CrackedLava"
    elif math.hypot(x - ASH[0], z - ASH[1]) < ASH[2] + 4 or fbm(x / 18 + 3, z / 18, seed=84, octaves=2) > 0.32:
        mat = "Asphalt"   # ash drifts
    else:
        mat = "Basalt"
    return h, mat


MATERIALS = ["Basalt", "CrackedLava", "Asphalt", "Sand"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 98, height, MATERIALS, path, priority=[("Sand", 2)], turns=TURNS)


def _clip_river_to_rim():
    """Cut the river where it first reaches the island edge (where the lavafall begins)."""
    inside = lambda x, z: math.hypot(x, z) < rim(math.atan2(z, x)) - 1.0
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


_clip_river_to_rim()

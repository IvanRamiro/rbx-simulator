"""Jade Grove: the ancient forest island east of the Starting Island.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 206).
Features: the Jade Route lands on the west rim at a small terrace with the Grove Gate; paths wind
east to a junction, then to the Bloom Glade egg shrine (south-west), the Elder Jade Tree on its
knoll (centre-east; Grove Heart in its hollow, Jade Seed in its crown) and down into the
Whispering Hollow (north; a spring pool and the Whispering Spring relic). Rolling forest floor
with jade-stone outcrops on the steeper ground.
"""
import math

NAME = "JadeGrove"
CENTRE = (330, 206, -70)

ARRIVAL = (-78, 18)            # where the Jade Route's last leap lands (layout.ROUTES["JadeRoute"]["to"])
LANDING = (-68, 15, 11)        # terrace inside the rim: centre x, z, radius
GATE = (-58, 12)               # the Grove Gate, facing the arrival
JUNCTION = (-36, 6)
GLADE = (-30, 36, 17)          # Bloom Glade egg shrine: centre, radius; flat at +1
ELDER = (16, -4, 24)           # Elder Jade Tree knoll: centre, radius; top +7
HOLLOW = (-12, -48, 15)        # Whispering Hollow: centre, radius; floor -7
HOLLOW_POOL = (-10, -50, 6.5)  # spring pool in the hollow floor: centre, radius
POOL_BED, POOL_WATER = -8.6, -7.2

# Rim radius by bearing (theta = atan2(z, x); east 0, south +90, north -90).
LOBES = [(0, 8, 22), (60, -6, 18), (115, 9, 20), (167, 10, 16), (-120, 7, 24), (-60, -5, 16), (-150, -4, 10)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = 78.0
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    r += 3.6 * fbm(math.cos(theta) * 2.4 + 21, math.sin(theta) * 2.4 + 9, seed=43, octaves=3)
    return r


PATHS = [
    [(-76, 17), (-68, 15), GATE, (-48, 9), JUNCTION],               # arrival -> gate -> junction
    [JUNCTION, (-36, 18), (-32, 26)],                                # junction -> Bloom Glade
    [JUNCTION, (-22, 0), (-8, 2), (2, 4)],                           # junction -> Elder Tree (west root arch)
    [JUNCTION, (-34, -12), (-26, -26), (-18, -36)],                  # junction -> Whispering Hollow (descends)
    [(30, 10), (44, 16), (58, 14)],                                  # Elder Tree -> east overlook
]


def _seg_dist(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg_dist(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def _base(x, z):
    """Ground height before material choice (None outside the rim)."""
    from worldlib import fbm, smoothstep, gauss
    r = math.hypot(x, z)
    R = rim(math.atan2(z, x))
    if r > R:
        return None
    # rolling forest floor with a low ridge along the east
    h = 2.6 * fbm(x / 30 + 11, z / 30 - 3, seed=51, octaves=4)
    h += 4.0 * gauss(x - 50, (z + 6) * 0.45, 16) * (1 + 0.4 * fbm(x / 12, z / 12, seed=52, octaves=2))
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
    # flat terraces
    for (cx, cz, rad), lift, soft in ((LANDING, 0.4, 7), (GLADE, 1.0, 8)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    # paths worn in
    h -= 0.4 * (1 - smoothstep(2.2, 4.0, path_distance(x, z)))
    # rounded lip at the rim
    h -= 3.4 * (1 - smoothstep(R - 1, R - 11, r)) ** 1.6
    return h


def pool_distance(x, z):
    px, pz, pr = HOLLOW_POOL
    return math.hypot(x - px, z - pz) - pr


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    # slope from finite differences: steep ground shows jade stone
    e = 1.5
    hs = [_base(x + dx, z + dz) for dx, dz in ((e, 0), (-e, 0), (0, e), (0, -e))]
    hs = [v if v is not None else h for v in hs]
    slope = math.hypot(hs[0] - hs[1], hs[2] - hs[3]) / (2 * e)
    if path_distance(x, z) < 3.6:
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
    return W.export_heightfield(NAME, CENTRE, 4, 102, height, MATERIALS, path, priority=[("Mud", 2)])

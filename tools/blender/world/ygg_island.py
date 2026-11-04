"""Yggdrasil: the hub island at the centre of the world, where every player arrives.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200), about 500
studs across: three times the outer islands. The World Tree stands at the centre on its root mound,
ringed by the Root Court path. South of it: the leaderboard plot, the Qi Compass and the Spawn Walk
with the six spawn daises. West: the Market Terrace (blacksmith, marketplace, buy & sell plots).
East: the Egg Garden, the Stone Lion's lair north of it, and the Qi Spring on the rim. North: a
paved bridgehead for each of the four bridges. The great root down to the Root of the Island
leaves the south rim.

The Qi Spring is the Starting Island's (its meshes are reused): SPRING_OFFSET and SPRING_YAW
(from_start) carry its pieces, authored in that island's coordinates, onto this rim.
"""
import math

import layout as L
import start_island as S

NAME = "Yggdrasil"
CENTRE = L.ISLANDS[NAME]["centre"]
TURNS = L.ISLANDS[NAME]["turns"]

RIM = 250.0
MOUND = (40.0, 76.0, 5.0)       # the World Tree's root mound: flat top radius, foot radius, height
COURT_R = 82.0                  # the Root Court, the ring path round the mound
COMPASS = (0.0, 132.0, 18.0)    # the Qi Compass plaza: centre, radius (the default spawn)
SLOT_R = 162.0                  # the Spawn Walk's radius; a dais every 20 degrees on it
SLOT_BEARINGS = (40, 60, 80, 100, 120, 140)
SLOT_PAD = 12.0
EGG_GARDEN = (170.0, 6.0, 22.0)  # sunk 1.5
LION_LAIR = (128.0, -62.0, 16.0)
ROOT_EXIT = (0.0, 246.0)         # where the great root leaves the rim (RootPath)
LANE_R = 140.0                   # the Market Terrace's lane

# Plots kept for buildings that come later: centre x, z, width (along the facing side), depth, and
# the bearing their front faces. The leaderboard faces the Qi Compass; the others face the lane.
PLOTS = {
    "Leaderboard": (0.0, 102.0, 28.0, 12.0, 90.0),
    "Blacksmith": (-173.9, 46.6, 36.0, 30.0, -15.0),
    "Marketplace": (-168.3, -29.7, 40.0, 32.0, 10.0),
    "BuySell": (-132.6, -101.6, 30.0, 26.0, 37.0),
}


def polar(bearing, r):
    a = math.radians(bearing)
    return (math.cos(a) * r, math.sin(a) * r)


SLOTS = [polar(b, SLOT_R) for b in SLOT_BEARINGS]
EXITS = {name: (b["start"][0], b["start"][2]) for name, b in L.BRIDGES.items()}

# ---------- the Qi Spring, carried over ----------
# Turned so its spillway points straight out from the island centre, and moved so the spill's end
# sits just past this rim, as it did on the Starting Island's.
SPRING_BEARING = 22.0
_old_out = math.atan2(S.SPILL_END[1] - S.SPRING[1], S.SPILL_END[0] - S.SPRING[0])
SPRING_YAW = -(math.radians(SPRING_BEARING) - _old_out)   # Roblox yaw: a positive yaw lowers the bearing
_spill_reach = math.hypot(S.SPILL_END[0] - S.SPRING[0], S.SPILL_END[1] - S.SPRING[1])
SPRING_CENTRE = polar(SPRING_BEARING, 244.0 - _spill_reach)


def spring_rotate(x, z, yaw=SPRING_YAW):
    c, s = math.cos(yaw), math.sin(yaw)
    return (x * c + z * s, -x * s + z * c)


_rx, _rz = spring_rotate(S.SPRING[0], S.SPRING[1])
SPRING_OFFSET = (SPRING_CENTRE[0] - _rx, SPRING_CENTRE[1] - _rz)   # new = offset + rotate(old)


def from_start(x, z):
    """A Starting Island point (the spring's frame) on Yggdrasil."""
    rx, rz = spring_rotate(x, z)
    return (SPRING_OFFSET[0] + rx, SPRING_OFFSET[1] + rz)


def to_start(x, z):
    rx, rz = spring_rotate(x - SPRING_OFFSET[0], z - SPRING_OFFSET[1], -SPRING_YAW)
    return rx, rz


SPILL = from_start(*S.SPILL_END)
SPRING_PATH_END = from_start(31.0, -27.0)   # where the Starting Island's path met the terrace

# ---------- the rim ----------
LOBES = [(10, 9, 13), (64, -8, 16), (118, 11, 15), (165, -9, 11), (205, 10, 16), (250, -7, 9), (-30, 9, 14), (-110, -6, 7)]


def _bulge(d, bearing, amount, width):
    diff = (d - bearing + 180) % 360 - 180
    return amount * math.exp(-(diff / width) ** 2)


def rim(theta):
    """Rim radius by bearing (theta = atan2(z, x); east 0, south +90, north -90)."""
    from worldlib import fbm
    d = math.degrees(theta)
    r = RIM
    for bearing, amount, width in LOBES:
        r += _bulge(d, bearing, amount, width)
    r += 6.0 * fbm(math.cos(theta) * 2.6 + 4, math.sin(theta) * 2.6 - 9, seed=71, octaves=3)
    # each bridgehead and the root's exit stand on a broad headland: their ground runs past where
    # the bridge (layout.HUB_EXIT_RADIUS) or the root leaves it
    for (x, z), reach, width in [(e, 16, 9.5) for e in EXITS.values()] + [(ROOT_EXIT, 14, 6.5)]:
        want = math.hypot(x, z) + reach - r
        if want > 0:
            r += want * math.exp(-(((d - math.degrees(math.atan2(z, x)) + 180) % 360 - 180) / width) ** 2)
    # the spring's cove: the rim passes just inside the spill's end
    spill_r = math.hypot(*SPILL)
    cove = r - (spill_r - 0.8)
    if cove > 0:
        arc = math.radians((d - math.degrees(math.atan2(SPILL[1], SPILL[0])) + 180) % 360 - 180) * spill_r
        r -= cove * math.exp(-(arc / 8.7) ** 2)
    return r


# ---------- paths ----------
def _arc(bearing0, bearing1, r, step=6):
    n = max(1, int(abs(bearing1 - bearing0) / step))
    return [polar(bearing0 + (bearing1 - bearing0) * i / n, r) for i in range(n + 1)]


def _spokes():
    out = []
    for x, z in EXITS.values():
        b = math.degrees(math.atan2(z, x))
        r = math.hypot(x, z)
        out.append([polar(b, COURT_R), polar(b, r - 4)])
    return out


PATHS = [
    _arc(0, 360, COURT_R),                                           # the Root Court
    _arc(12, 156, SLOT_R),                                           # the Spawn Walk
    [(0.0, COMPASS[1] + COMPASS[2]), (0.0, SLOT_R)],                 # Compass -> Spawn Walk
    [(-11.0, COMPASS[1] - 13.0), (-24.0, 102.0), polar(106, COURT_R)],   # Compass -> Root Court, either side of the leaderboard
    [(11.0, COMPASS[1] - 13.0), (24.0, 102.0), polar(74, COURT_R)],
    [(0.0, SLOT_R), (0.0, ROOT_EXIT[1] - 6)],                        # Spawn Walk -> the great root
    [polar(0, COURT_R), (EGG_GARDEN[0] - EGG_GARDEN[2], EGG_GARDEN[1])],   # Root Court -> the old Egg Garden
    [(EGG_GARDEN[0] - EGG_GARDEN[2], EGG_GARDEN[1]), EXITS["BeginnerRoute"]],   # ... and on to the Beginner Isle's bridge
    [polar(12, SLOT_R), (150.0, 26.0), (EGG_GARDEN[0] - 8, EGG_GARDEN[1] + 16)],   # Spawn Walk -> Egg Garden
    [polar(24, SLOT_R), SPRING_PATH_END],                            # Spawn Walk -> Qi Spring
    [polar(192, COURT_R), polar(192, LANE_R)],                       # Root Court -> Market Terrace
    _arc(168, 227, LANE_R),                                          # the Market lane
    [polar(156, SLOT_R), polar(168, LANE_R)],
] + _spokes()


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    best = 1e9
    for line in PATHS:
        for a, b in zip(line, line[1:]):
            best = min(best, _seg_dist(x, z, a, b))
    return best


def plot_distance(x, z, plot):
    """Signed distance outside a plot's rectangle (negative inside)."""
    cx, cz, w, d, facing = plot
    a = math.radians(facing)
    fx, fz = math.cos(a), math.sin(a)          # out of its front
    u = (x - cx) * -fz + (z - cz) * fx         # along the front
    v = (x - cx) * fx + (z - cz) * fz
    qx, qz = abs(u) - w / 2, abs(v) - d / 2
    return math.hypot(max(qx, 0), max(qz, 0)) + min(max(qx, qz), 0)


# Low knolls near the rim, for a skyline: centre x, z, radius, height
KNOLLS = [(-118, 200, 26, 6.0), (122, 196, 24, 5.0), (-216, -66, 22, 5.5), (-78, -176, 28, 7.0), (172, -120, 24, 6.0)]
BRIDGEHEAD_R = 26.0             # paved round each bridge's start: the decks are 40 studs wide


def flats():
    """(x, z, radius, height, soft, material) discs the ground is levelled to."""
    out = [(COMPASS[0], COMPASS[1], COMPASS[2], 0.3, 7, "Cobblestone"),
           (EGG_GARDEN[0], EGG_GARDEN[1], EGG_GARDEN[2], -1.5, 9, None),
           (LION_LAIR[0], LION_LAIR[1], LION_LAIR[2], 0.0, 10, None)]
    out += [(x, z, SLOT_PAD, 0.2, 6, "Ground") for x, z in SLOTS]   # bare earth: grass would grow through the dais
    for x, z in EXITS.values():
        r = math.hypot(x, z)
        out.append((x * (r - 10) / r, z * (r - 10) / r, BRIDGEHEAD_R, 0.0, 8, "Cobblestone"))
    return out


def height(x, z):
    """Ground height (y offset) or None outside the rim, plus the terrain material."""
    from worldlib import fbm, smoothstep, gauss
    r = math.hypot(x, z)
    R = rim(math.atan2(z, x))
    if r > R:
        return None, None

    h = 1.2 * fbm(x / 70 + 2, z / 70 - 6, seed=81, octaves=4) + 0.5 * fbm(x / 21, z / 21, seed=83, octaves=3)
    rocky = False
    for kx, kz, kr, kh in KNOLLS:
        dome = gauss(x - kx, z - kz, kr * 0.5)
        h += kh * dome + 1.6 * dome * fbm(x / 8, z / 8, seed=85, octaves=3)
        rocky = rocky or dome > 0.5 and fbm(x / 11 + 5, z / 11, seed=87, octaves=3) > -0.05 + 0.4 * (1 - dome)

    # the root mound under the World Tree
    w = 1 - smoothstep(MOUND[0], MOUND[1], r)
    h = h * (1 - w) + MOUND[2] * w ** 0.8

    mat = None
    for fx, fz, fr, fh, soft, fmat in flats():
        d = math.hypot(x - fx, z - fz)
        w = 1 - smoothstep(fr, fr + soft, d)
        h = h * (1 - w) + fh * w
        if fmat and d < fr + 1.0:
            mat = fmat
    for plot in PLOTS.values():
        d = plot_distance(x, z, plot)
        w = 1 - smoothstep(0.0, 6.0, d)
        h = h * (1 - w) + 0.3 * w
        if d < 0.5:
            mat = "Cobblestone"

    # the Qi Spring's terrace and pool, as on the Starting Island
    sx, sz = to_start(x, z)
    d_spring = math.hypot(sx - S.SPRING[0], sz - S.SPRING[1])
    w = 1 - smoothstep(S.SPRING[2], S.SPRING[2] + 8, d_spring)
    h = h * (1 - w) + 6.0 * w
    pd_pool = S.pool_distance(sx, sz)
    if pd_pool < 1.0:
        wp = 1 - smoothstep(-2.0, 0.8, pd_pool)
        h = h * (1 - wp) + S.POOL_BED * wp

    pd = path_distance(x, z)
    h -= 0.35 * (1 - smoothstep(2.4, 4.4, pd))

    # rounded grass lip at the rim
    h -= 3.2 * (1 - smoothstep(R - 1, R - 11, r)) ** 1.6

    spring_edge = S.SPRING[2] - 1 < d_spring < S.SPRING[2] + 6
    if pd_pool < 1.0:
        mat = "Rock"
    elif mat:
        pass
    elif pd < 4.2:
        mat = "Ground"
    elif rocky or spring_edge:
        mat = "Rock"
    else:
        mat = "Grass"
    return h, mat


MATERIALS = ["Grass", "Ground", "Rock", "Cobblestone"]


def export_terrain(path=None):
    """Write src/worldbuild/Terrain/Yggdrasil.lua for WorldBuilder.buildTerrain."""
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 276, height, MATERIALS, path,
                                priority=[("Cobblestone", 4), ("Ground", 2)], turns=TURNS)

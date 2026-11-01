"""Moonlit Isle: the highest island, pale and celestial, shaped like a crescent moon.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 200).
Features:
- Outline: a large disc with a big offset disc cut away to the north, so seen from above the
  island is a crescent whose tapering horns curl around an open bay of sky (the layout centre
  lies in that bay; every landmark sits on the crescent's band).
- Arrival: the Moonlit Route's last climb lands on the south rim at a small landing.
- The Moon Mirror (south-west): a round reflecting pool on a flat terrace, with a crescent
  bridge out to the lotus dais and the relic at its centre.
- The Star Well (west horn): a stone-ringed well brimming with glowing starlight, with
  starlight rising off it and the relic above its mouth.
- The Celestial Pavilion (south-east): the egg shrine on a raised terrace.
- Ground: pale limestone, moon-frost drifts, salt-white paths, paving on the terraces.
"""
import math

import layout as L

NAME = "MoonlitIsle"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

BODY = (0.0, 8.0, 60.0)        # the full moon disc: centre x, z and radius
BITE = (0.0, -28.0, 52.0)      # the disc cut away to the north; its edge is the crescent's inner curve


def band_point(bearing_deg, frac):
    """A point across the crescent's band at a bearing from the body's centre: frac 0 on the
    inner (bay) shore, 1 on the outer shore. Bearings: 90 is south, 180 west, 0 east."""
    bx, bz, br = BODY
    cx, cz, cr = BITE
    a = math.radians(bearing_deg)
    dx, dz = math.cos(a), math.sin(a)
    # where the ray from the body's centre leaves the bitten-away disc
    ox, oz = bx - cx, bz - cz
    b_ = ox * dx + oz * dz
    c_ = ox * ox + oz * oz - cr * cr
    r_in = -b_ + math.sqrt(b_ * b_ - c_)
    r = r_in + (br - r_in) * frac
    return (round(bx + dx * r, 1), round(bz + dz * r, 1))


ARRIVAL = (-14, 58)             # where the Moonlit bridge lands (about layout.ARRIVALS["MoonlitIsle"])
LANDING = (-12, 50, 7)          # x, z, radius; flat at +0.4
MIRROR = band_point(150, 0.5) + (13,)    # Moon Mirror terrace (south-west): centre, radius; flat at +1.2
MIRROR_POOL_R = 10.0
WELL = band_point(180, 0.55) + (6,)      # Star Well (west horn, where it is still broad): centre, ring radius
WELL_SHAFT_R, WELL_FLOOR = 3.2, -4.0   # a shallow bowl under the starlight surface (voxels can't hold a narrow open shaft)
PAVILION = band_point(35, 0.5) + (10,)   # Celestial Pavilion terrace (south-east): centre, radius; flat at +2.6
JUNCTION = band_point(95, 0.42)


def edge_distance(x, z):
    """Distance from (x, z) to the crescent's edge: positive inside the island, negative outside.
    A little noise keeps the coast from being a perfect arc."""
    from worldlib import fbm
    bx, bz, br = BODY
    cx, cz, cr = BITE
    from worldlib import smoothstep
    inside_body = br - math.hypot(x - bx, z - bz)
    outside_bite = math.hypot(x - cx, z - cz) - cr
    base = min(inside_body, outside_bite)
    # the wobble only roughens the coast from the inside, so it never raises slivers of land in
    # the bay beyond the horn tips
    wobble = 1.8 * fbm(x / 16 + 41, z / 16 + 3, seed=121, octaves=3) * smoothstep(-0.5, 3.0, base)
    return base + wobble


def inside(x, z):
    return edge_distance(x, z) > 0


PATHS = [
    [ARRIVAL, LANDING[:2], JUNCTION],                                          # arrival -> landing -> junction
    [JUNCTION, band_point(118, 0.45), band_point(132, 0.45)],                  # junction -> the Moon Mirror's east bank
    [JUNCTION, band_point(70, 0.45), band_point(48, 0.48)],                    # junction -> the pavilion
    [band_point(166, 0.5), band_point(171, 0.53)],                             # the mirror's west bank -> the Star Well
]


def _seg(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    return min(_seg(x, z, a, b) for line in PATHS for a, b in zip(line, line[1:]))


def _base(x, z):
    from worldlib import fbm, smoothstep
    e = edge_distance(x, z)
    if e <= 0:
        return None
    # soft, wind-carved swells of moon frost
    h = 1.4 * fbm(x / 22 + 9, z / 22 - 4, seed=131, octaves=4) + 0.8
    for (cx, cz, rad), lift, soft in ((LANDING, 0.4, 6), (MIRROR, 1.2, 6), (PAVILION, 2.6, 5)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    # the Star Well: a shaft straight down inside a small raised apron
    wx, wz, wr = WELL
    dw = math.hypot(x - wx, z - wz)
    h += 0.8 * (1 - smoothstep(wr, wr + 5, dw))
    if dw < WELL_SHAFT_R + 1.0:
        h = WELL_FLOOR + (h - WELL_FLOOR) * smoothstep(WELL_SHAFT_R - 0.5, WELL_SHAFT_R + 1.0, dw)
    h -= 0.3 * (1 - smoothstep(2.0, 3.6, path_distance(x, z)))
    h -= 3.0 * (1 - smoothstep(1, 9, e)) ** 1.6
    return h


def height(x, z):
    h = _base(x, z)
    if h is None:
        return None, None
    from worldlib import fbm
    if path_distance(x, z) < 3.2:
        mat = "Salt"
    elif any(math.hypot(x - cx, z - cz) < rad + 1 for cx, cz, rad in (MIRROR, PAVILION)) or \
            math.hypot(x - WELL[0], z - WELL[1]) < WELL[2] + 2:
        mat = "Pavement"
    elif fbm(x / 14 - 5, z / 14 + 2, seed=132, octaves=3) > 0.15:
        mat = "Snow"      # moon-frost drifts
    else:
        mat = "Limestone"
    return h, mat


MATERIALS = ["Limestone", "Snow", "Salt", "Pavement"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 80, height, MATERIALS, path, priority=[("Salt", 2)], turns=TURNS)

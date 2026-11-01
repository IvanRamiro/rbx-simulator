"""Origin Abyss: the hidden endgame island, far north-west and below the others.

Authored in island-local Roblox studs (x east, z south, y up; ground ~0 = world Y 95).
Features:
- The Rift: a void rift splits the island from north-east to south-west. Open sky shows
  through it, and a broken bridge and floating rubble cross it.
- The south-east half (where the glide from the Origin Route lands):
  - the broken Gate of Descent;
  - a ruined avenue to the rift bridge;
  - the half-buried head of a fallen stone colossus;
  - the shrine of thorny bronze egg pedestals.
- The north-west half, raised and tilted up toward its far edge:
  - the Origin Altar inside a ring of obsidian monoliths;
  - the Void Shard hanging 150 studs above it, reached by floating ruin fragments that each
    rise 49 studs (seven air leaps clear that, six do not).
- Ground: dark slate, worn avenue stone, and void-crystal crust along the rift's lips; the
  temple terraces are paved with hewn slabs (meshes, in origin_meshes.py).
"""
import math

import layout as L

NAME = "OriginAbyss"
CENTRE = L.ISLANDS[NAME]["centre"]   # its place in the world, and its quarter turns (layout.py)
TURNS = L.ISLANDS[NAME]["turns"]

RIFT_DIR = (1 / math.sqrt(2), -1 / math.sqrt(2))   # the rift runs north-east to south-west
RIFT_HALF = 7.0
GATE = (40, 44, 10)          # Gate of Descent terrace (south-east): centre, radius; flat at +0.5
SHRINE = (8, 52, 9)          # egg shrine terrace: centre, radius; flat at +0.8
COLOSSUS = (54, -4)          # where the fallen colossus head lies
ALTAR = (-34, -30, 16)       # Origin Altar terrace (north-west): centre, radius; flat at +7
BRIDGE_SE, BRIDGE_NW = (-0.3, 16.7), (-13.5, 3.5)   # where the broken bridge meets each lip (the rift's narrowest point)

# Landings at each bridge head (SE, NW) that even out the ground the deck rests on. Both put the
# surface half-way up a voxel (world Y a multiple of 4), where Studio renders flat ground truest.
# Measured: the NW landing renders flat at +5.1; the SE one is too close to the lower lip to stay
# flat (it renders from about +0.5 down to -0.6), so the deck reaches further inland there
# (origin_meshes.BRIDGE_INLAND / DECK_ENDS).
BRIDGE_PAD_LIFT = (1.0, 5.0)


def bridge_pads():
    """Centres (3.5 studs inland of each bridge head, along the bridge) and heights of the landings."""
    (ax, az), (bx, bz) = BRIDGE_SE, BRIDGE_NW
    d = math.hypot(bx - ax, bz - az)
    ux, uz = (bx - ax) / d, (bz - az) / d
    return [((ax - ux * 3.5, az - uz * 3.5), BRIDGE_PAD_LIFT[0]), ((bx + ux * 3.5, bz + uz * 3.5), BRIDGE_PAD_LIFT[1])]


LOBES = [(45, 8, 30), (-135, 10, 28), (-30, -6, 16), (160, -7, 14), (100, 5, 20), (-80, 6, 22)]


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = 78.0
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    # a torn, shattered coast: sharper noise than the other islands
    r += 6.0 * W_abs(fbm(math.cos(theta) * 4 + 11, math.sin(theta) * 4 - 7, seed=161, octaves=4)) - 3.0
    return r


def W_abs(v):
    return abs(v) * 2


def side(x, z):
    """Signed distance across the rift's centreline: positive on the south-east half. The
    centreline meanders, so the rift reads as torn rather than cut."""
    from worldlib import fbm
    nx, nz = -RIFT_DIR[1], RIFT_DIR[0]
    along = x * RIFT_DIR[0] + z * RIFT_DIR[1]
    return x * nx + z * nz + 24.0 * fbm(along / 38 + 5, 0.3, seed=172, octaves=2) + 5.0 * fbm(along / 9 + 9, 4.1, seed=174, octaves=2)


def rift_half(x, z):
    """Half the rift's width: pinched to about 4 studs in places and gaping to about 11 in others,
    with a jagged edge."""
    from worldlib import fbm
    along = x * RIFT_DIR[0] + z * RIFT_DIR[1]
    return RIFT_HALF + 5.0 * fbm(along / 18 + 3, 1.7, seed=171, octaves=2) + 1.4 * fbm(along / 4, 2.9, seed=173, octaves=2)


def edge_distance(x, z):
    """Distance to the nearest edge (the coast or the rift's lip): positive on land."""
    coast = rim(math.atan2(z, x)) - math.hypot(x, z)
    lip = abs(side(x, z)) - rift_half(x, z)
    return min(coast, lip)


def inside(x, z):
    return edge_distance(x, z) > 0


PATHS = [
    [(GATE[0] - 4, GATE[1] - 4), (28, 26), (12, 22), BRIDGE_SE],          # gate -> avenue -> the rift bridge
    [(28, 26), (16, 40), (SHRINE[0] + 2, SHRINE[1] - 6)],                  # avenue -> egg shrine
    [(30, 14), (44, 2)],                                                   # avenue -> the colossus head
    [BRIDGE_NW, (-18, -8), (ALTAR[0] + 12, ALTAR[1] + 10)],                # the far lip -> the Origin Altar
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
    s = side(x, z)
    # rubble-strewn ground; the north-west half is raised and tilts up toward its far edge
    h = 1.6 * fbm(x / 20 + 3, z / 20 - 8, seed=181, octaves=4) + 1.2 * abs(fbm(x / 7, z / 7, seed=182, octaves=2))
    if s < 0:
        h += 5.0 + 0.09 * (-s)
    for (cx, cz, rad), lift, soft in ((GATE, 0.5, 6), (SHRINE, 0.8, 5), (ALTAR, 7.0, 7)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    h -= 0.35 * (1 - smoothstep(2.0, 3.6, path_distance(x, z)))
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
    lip = abs(side(x, z)) - rift_half(x, z)
    if path_distance(x, z) < 3.2:
        mat = "Concrete"
    elif 1.8 < lip < 5.0:
        mat = "Glacier"     # void-crystal crust set back from the rift's lip (the lip column itself
                            # forms the rift wall, which should stay dark slate)
    else:
        mat = "Slate"       # also under the temple terraces, which are paved with meshes (Brick
                            # terrain would snap their height to the 4-stud voxel grid)
    return h, mat


MATERIALS = ["Slate", "Concrete", "Glacier"]


def export_terrain(path=None):
    import worldlib as W
    path = path or W.REPO + "/src/worldbuild/Terrain/%s.lua" % NAME
    return W.export_heightfield(NAME, CENTRE, 4, 100, height, MATERIALS, path, priority=[("Concrete", 2)], turns=TURNS)

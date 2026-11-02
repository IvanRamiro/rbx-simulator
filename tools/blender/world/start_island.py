"""Starting Island: the welcoming grassy cultivation island that was the hub until Yggdrasil
replaced it (2026-11-01). Kept as the ground and the Qi Spring that the Starting Island's kit
(start_props, start_nature, start_meshes) was authored on: Yggdrasil places that kit, and carries
the spring over whole (ygg_island.SPRING_OFFSET, SPRING_YAW, from_start).

Authored in island-local Roblox studs (x east, z south, y up, ground ~0 = world Y 200).
Features: central spawn plaza, Qi Spring terrace (north-east) whose overflow falls through a
cove in the rim, rocky lookout hill (west), sunken egg garden (south-west), worn paths to every
landmark and Qinggong route exit, and the Root of the Island grotto beneath.
"""
import math

PLAZA = (0, 0, 24)            # x, z, radius
SPRING = (46, -42, 19)        # terrace centre and radius; ground lifted +6
HILL = (-50, 16, 22)          # lookout hill: centre, radius; peak +15
EGG_GARDEN = (-38, 50, 22)    # sunken terrace at -1.5
# Qi Spring pool: a capsule on the spring terrace that runs out to the waterfall cove.
POOL_A, POOL_B, POOL_R = (40, -37), (49.7, -44.0), 6.0
SPILL_END = (64.6, -54.8)        # where the spillway leaves the rim and the waterfall begins
POOL_BED, POOL_WATER = 3.2, 5.6  # wading depth; the water is a mesh surface (too narrow for terrain water)

# Rim radius by bearing (theta = atan2(z, x); east 0, south +90, north -90).
LOBES = [(-7, 13, 16), (135, 15, 20), (-86, 9, 14), (-138, 16, 15), (100, 7, 22), (40, 4, 18)]
COVE = (-38, -7, 6)           # waterfall cove: bearing, depth, half-width (deg)


def rim(theta):
    from worldlib import fbm
    d = math.degrees(theta)
    r = 90.0
    for bearing, amount, width in LOBES:
        diff = (d - bearing + 180) % 360 - 180
        r += amount * math.exp(-(diff / width) ** 2)
    diff = (d - COVE[0] + 180) % 360 - 180
    r += COVE[1] * math.exp(-(diff / COVE[2]) ** 2)
    r += 3.2 * fbm(math.cos(theta) * 2.2 + 7, math.sin(theta) * 2.2 + 3, seed=11, octaves=3)
    return r


PATHS = [
    [(0, 0), (18, -16), (31, -27)],                       # plaza -> spring (west bank)
    [(0, 0), (-16, 22), (-32, 42)],                       # plaza -> egg garden
    [(0, 0), (40, -6), (72, -10), (100, -12)],            # plaza -> Jade exit
    [(-32, 42), (-54, 58), (-72, 72)],                    # egg garden -> Ember exit
    [(0, 0), (2, -40), (6, -72), (8, -96)],               # plaza -> Moonlit exit
    [(0, 0), (-26, -24), (-54, -48), (-78, -70)],         # plaza -> Origin exit
    [(-16, -6), (-30, 4), (-44, 12)],                     # plaza -> hill top
    [(40, -6), (62, 12), (88, 34)],                       # Jade path -> root path
]


def _seg_dist(px, pz, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t))


def path_distance(x, z):
    best = 1e9
    for line in PATHS:
        for a, b in zip(line, line[1:]):
            best = min(best, _seg_dist(x, z, a, b))
    return best


def pool_distance(x, z):
    """Signed distance outside the spring pool (negative inside), with a lobed outline."""
    return _seg_dist(x, z, POOL_A, POOL_B) - POOL_R * (1 + 0.12 * math.sin(math.atan2(z - POOL_A[1], x - POOL_A[0]) * 3 + 1.3))


def height(x, z):
    """Ground height (y offset) or None outside the rim, plus the terrain material."""
    from worldlib import fbm, smoothstep, gauss
    r = math.hypot(x, z)
    theta = math.atan2(z, x)
    R = rim(theta)
    if r > R:
        return None, None

    h = 1.1 * fbm(x / 38 + 3, z / 38 - 5, seed=3, octaves=4)
    # gentle rise toward the north meadow and the Moonlit exit
    h += 2.4 * smoothstep(10, 80, -z) * (1 - smoothstep(30, 70, abs(x)))

    # lookout hill: a rocky dome with a craggy cap
    hx, hz, hr = HILL
    dome = gauss(x - hx, z - hz, hr * 0.55)
    h += 15 * dome + 2.2 * dome * fbm(x / 9, z / 9, seed=21, octaves=3)

    # flat terraces blended in
    for (cx, cz, rad), lift, soft in ((PLAZA, 0.3, 8), (SPRING, 6.0, 8), (EGG_GARDEN, -1.5, 9)):
        d = math.hypot(x - cx, z - cz)
        w = 1 - smoothstep(rad, rad + soft, d)
        h = h * (1 - w) + lift * w

    # the spring pool is carved into the terrace, with a soft bank
    pd_pool = pool_distance(x, z)
    if pd_pool < 1.0:
        w = 1 - smoothstep(-2.0, 0.8, pd_pool)
        h = h * (1 - w) + POOL_BED * w

    # paths are worn slightly into the ground
    pd = path_distance(x, z)
    h -= 0.35 * (1 - smoothstep(2.0, 3.8, pd))

    # rounded grass lip at the rim
    h -= 3.2 * (1 - smoothstep(R - 1, R - 11, r)) ** 1.6

    # material
    slope_rock = dome > 0.45
    spring_edge = SPRING[2] - 1 < math.hypot(x - SPRING[0], z - SPRING[1]) < SPRING[2] + 6
    if pd_pool < 1.0:
        mat = "Rock"
    elif math.hypot(x - PLAZA[0], z - PLAZA[1]) < PLAZA[2] + 1.5:
        mat = "Cobblestone"
    elif pd < 3.6:
        mat = "Ground"
    elif slope_rock or spring_edge:
        mat = "Rock"
    else:
        mat = "Grass"
    return h, mat


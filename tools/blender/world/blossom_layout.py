"""The Blossom Sanctuary (the owner's directive, 2026-11-16): one source for the island's shape, its terrain, everything placed on
it, the stepping-stone climb from the hub and the top-down plan sketch. Plain Python (no Blender needed).

    python3 tools/blender/world/blossom_layout.py            # check the layout, print its numbers
    python3 tools/blender/world/blossom_layout.py --write    # also write src/worldbuild/Terrain/BlossomSanctuary.lua,
                                                             # src/worldbuild/Placements/BlossomSanctuary.lua and
                                                             # renders/blossom_sanctuary/plan_topdown.png

Coordinates are Roblox studs. The island's own frame ("local") has its origin at CENTRE, local -Z pointing back at the hub (the
side the stepping stones arrive on) and local +X toward the north-east. WorldBuilder.islandFrame turns local into world by the
island's Turns (not a whole number of quarter turns, so the terrain grid is written already turned: BakedTurn).

The island sits south-east of Yggdrasil, out along the hub's south-east avenue (bearing 30 in hub_ground's polar terms), in the open
sky: no island or bridge is within 300 studs of it. Its ground is about as big as the hub's playable area (a lobed, coved shape,
not a circle): the Grove (west lobe), the Spirit Fish Pond with its bridge, the Training Ground lawn by the pond (the +50% Qi zone,
GameConfig.TrainingStation), a far meadow and the raised Lookout with its cliff edge (east lobe).
"""
import json
import math
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ISLAND = "BlossomSanctuary"

CENTRE = (452.0, 200.0, 380.0)
YAW = math.atan2(CENTRE[0], CENTRE[2])          # turns local -Z toward the hub's centre
TURNS = -YAW / (math.pi / 2)                    # WorldBuilder.islandFrame: CFrame.Angles(0, -Turns * pi / 2, 0)
CELL = 4

WATER = 4.5          # the pond's surface over the island's base (Y 200)
LAWN = 6.0           # the Training Ground's level, the arrival's and most of the ground's
PLATEAU = 18.0       # the Lookout


def to_world(x, z):
    c, s = math.cos(YAW), math.sin(YAW)
    return CENTRE[0] + x * c + z * s, CENTRE[2] - x * s + z * c


def to_local(wx, wz):
    dx, dz = wx - CENTRE[0], wz - CENTRE[2]
    c, s = math.cos(YAW), math.sin(YAW)
    return dx * c - dz * s, dx * s + dz * c


# ---------- noise ----------
def _hash(i, j, seed):
    h = (i * 374761393 + j * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, seed=0):
    i, j = math.floor(x), math.floor(z)
    fx, fz = x - i, z - j
    ux, uz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash(i, j, seed), _hash(i + 1, j, seed)
    c, d = _hash(i, j + 1, seed), _hash(i + 1, j + 1, seed)
    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uz


def fbm(x, z, seed=0, octaves=3):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * vnoise(x * (2 ** o), z * (2 ** o), seed + o * 17)
        norm += amp
        amp *= 0.5
    return total / norm   # 0..1


def smoothstep(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------- shapes: an approximate distance inside (studs, > 0 inside) ----------
def ellipse(x, z, cx, cz, a, b, rot=0.0):
    dx, dz = x - cx, z - cz
    if rot:
        c, s = math.cos(rot), math.sin(rot)
        dx, dz = dx * c - dz * s, dx * s + dz * c
    return (1.0 - math.hypot(dx / a, dz / b)) * min(a, b)


def soft_union(values, k=6.0):
    m = max(values)
    return m + math.log(sum(math.exp((v - m) / k) for v in values)) * k


LOBES = [  # the island's ground: (cx, cz, a, b)
    (0, 0, 192, 165),        # the body: the pond, the lawn, the far meadow
    (-215, 25, 140, 122),    # the Grove (west)
    (212, -15, 122, 108),    # the Lookout (east, raised, its outer side a cliff)
    (-30, 150, 132, 82),     # the far meadow's bulge
    (40, -150, 52, 46),      # the arrival's tongue, reaching toward the hub
]
COVES = [  # bites out of the outline: (cx, cz, r)
    (122, -168, 46),         # the cove right of the arrival (seen from the last stones)
    (-92, -166, 52),         # the cove left of it
    (108, 156, 50),          # the far cove
    (-336, -46, 42),         # a notch in the Grove's tip
]


def island_field(x, z):
    f = max(ellipse(x, z, *l) for l in LOBES)
    for cx, cz, r in COVES:
        f = min(f, math.hypot(x - cx, z - cz) - r)
    return f + 9.0 * (fbm(x / 55.0, z / 55.0, 3) - 0.5)


POND = [  # the Spirit Fish Pond: a long kidney, a small pool off its west end, and the neck between them the bridge crosses
    (-52, -40, 56, 32, 0.22),
    (-132, -20, 27, 21, -0.5),
    (-104, -31, 17, 10, 0.27),
]
POND_LOBES = [(-52, -40), (-132, -20)]


def pond_field(x, z):
    return soft_union([ellipse(x, z, *p) for p in POND], 3.0) + 3.2 * (fbm(x / 20.0, z / 20.0, 11) - 0.5)


BRIDGE = {"Position": (-104.0, -31.0), "Yaw": 0.27, "Half": 15.0}   # BS_Bridge spans its local Z (ends at +-15), across the neck


def bridge_end(sign):
    bx, bz = BRIDGE["Position"]
    return bx + sign * BRIDGE["Half"] * math.sin(BRIDGE["Yaw"]), bz + sign * BRIDGE["Half"] * math.cos(BRIDGE["Yaw"])


# the Training Ground: the +50% Qi zone (GameConfig.TrainingStation), a bean-shaped lawn by the pond; QiService reads its outline
ZONE = [(66, -22, 56, 35, 0.32), (98, 2, 24, 20, 0.0)]   # a long lens turned toward the pond, a soft swell at its far end
ZONE_CENTRE = (70, -18)
ZONE_HEIGHT = 12       # studs above or below the lawn that still count (QiService)


def zone_field(x, z):
    return soft_union([ellipse(x, z, *e) for e in ZONE], 14.0)


ARRIVAL = (40.0, -180.0)
PLATEAU_AT = (205.0, -20.0)

# paths: Catmull-Rom through these points, Cobblestone, half width
PATHS = [
    ([(40, -186), (42, -150), (46, -112), (51, -84), (54, -58)], 3.5),             # arrival -> the Training Ground's kerb
    ([(44, -132), (10, -110), (-30, -96), (-75, -86), (-104, -66), (-108, -50)], 3.0),   # along the pond's near bank -> the bridge
    ([(-100, -16), (-98, 6), (-104, 30), (-140, 46), (-185, 30), (-228, -6), (-262, 18), (-245, 70), (-200, 92), (-150, 70), (-104, 30)], 3.0),  # the Grove's loop
    ([(-100, 30), (-70, 70), (-25, 92), (30, 78), (50, 44), (53, 22)], 3.0),      # the far meadow -> the lawn's back
    ([(130, -21), (150, -22), (166, -24), (176, -25)], 3.5),                      # the lawn -> up to the Lookout's torii
]


def catmull(points, step=2.0):
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        seg = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(tuple(points[-1]))
    return out


PATH_PTS = [(catmull(p), hw) for p, hw in PATHS]


def path_dist(x, z):
    best = 1e9
    for pts, hw in PATH_PTS:
        for px, pz in pts:
            d = math.hypot(x - px, z - pz) - hw
            if d < best:
                best = d
    return best


# ---------- what stands on it ----------
# trees: (piece, x, z, yaw, scale). Six different trees (BS_Tree*), each placed for a reason: the Elder over the pond's far bank
# framing the bridge from the arrival, a Weeping tree at the bridge's far end, Leaning trees reaching over the water, the Twins
# and the Gnarled ones in the Grove and on the Lookout's cliff, Young trees opening the lawn's edges. None inside the lawn.
TREES = [
    # the pond and the bridge (scaled up 2026-11-16 after the import: at 1.0 they read as small tufts on a 600-stud island)
    ("BS_TreeElder", -128, 18, 0.4, 1.5),        # the hero: over the small pool's far bank, framing the bridge from the landing
    ("BS_TreeWeeping", -84, 4, 2.0, 1.3),        # at the bridge's far end
    ("BS_TreeLeaning", -26, -82, -0.31, 1.3),    # reaching over the kidney from its near bank
    ("BS_TreeLeaning", -154, -60, 0.95, 1.15),   # over the small pool
    ("BS_TreeTwin", -40, -116, 3.9, 1.15),       # framing the landing's view
    ("BS_TreeYoung", -6, -142, 4.0, 1.2),
    ("BS_TreeGnarled", -100, -100, 0.6, 1.1),
    # the Grove: a stand inside its path's loop and round it
    ("BS_TreeElder", -262, 70, 2.4, 1.3),
    ("BS_TreeTwin", -208, 62, 1.2, 1.35),
    ("BS_TreeGnarled", -215, 25, 0.9, 1.2),
    ("BS_TreeYoung", -232, 42, 4.4, 1.15),
    ("BS_TreeTwin", -252, -22, 2.6, 1.25),
    ("BS_TreeWeeping", -190, -42, 4.0, 1.2),
    ("BS_TreeYoung", -170, 98, 0.3, 1.3),
    ("BS_TreeYoung", -300, 15, 3.0, 1.2),
    ("BS_TreeTwin", -232, -78, 5.6, 1.1),
    ("BS_TreeElder", -300, 75, 1.0, 1.1),
    ("BS_TreeLeaning", -175, -70, 2.8, 1.1),
    ("BS_TreeYoung", -128, -90, 1.1, 1.2),
    # the far meadow (open in the middle: the island's open ground)
    ("BS_TreeTwin", 8, 112, 5.0, 1.3),
    ("BS_TreeYoung", -112, 76, 1.7, 1.15),
    ("BS_TreeElder", -70, 128, 3.3, 1.25),
    ("BS_TreeYoung", 40, 140, 2.6, 1.2),
    ("BS_TreeGnarled", -10, 170, 0.2, 1.15),
    # round the Training Ground (never on it)
    ("BS_TreeYoung", 96, 76, 2.2, 1.2),
    ("BS_TreeYoung", 140, -88, 0.8, 1.15),
    ("BS_TreeGnarled", 78, -128, 3.5, 1.1),
    ("BS_TreeTwin", 150, -55, 1.9, 1.15),
    ("BS_TreeLeaning", 40, 52, 2.76, 1.1),       # leaning toward the lawn
    # the Lookout, and the hub-facing edge's silhouette
    ("BS_TreeGnarled", 248, -58, 2.1, 1.3),
    ("BS_TreeGnarled", 200, 32, 1.0, 1.15),
    ("BS_TreeElder", 205, 12, 4.0, 1.2),         # shading the Lookout's seats
    ("BS_TreeYoung", 275, 10, 1.4, 1.1),
    ("BS_TreeElder", 175, -95, 2.2, 1.15),
    # a few more (the owner, 2026-11-16: "I love the new are, but add some few more blossom trees"), each for a reason:
    ("BS_TreeTwin", 10, -168, 0.9, 1.05),        # either side of the stepping stones' landing
    ("BS_TreeYoung", 68, -170, 4.3, 1.1),
    ("BS_TreeLeaning", 116, -112, 3.6, 1.05),    # the hub-facing edge, seen on the approach
    ("BS_TreeYoung", -30, 12, 2.0, 1.15),        # the pond's far bank, off the landing's line to the bridge
    ("BS_TreeLeaning", -55, 14, 3.09, 1.1),      # leaning out over the kidney
    ("BS_TreeTwin", 70, 110, 3.0, 1.2),          # the meadow's edge
    ("BS_TreeGnarled", -150, 140, 1.6, 1.1),
    ("BS_TreeTwin", 272, -62, 2.4, 1.2),         # framing the Lookout (the shrine's site) from behind
    ("BS_TreeLeaning", 262, 32, -2.46, 1.1),
]
# The shrine on the Lookout (the owner, 2026-11-16: "Also add japanese shrine on that area", then "Yes, build the Japanese
# shrine on the Blossom Sanctuary (torii, hall, lanterns), modelled in Blender"; "JAPANESE is good to me, but not chinese design"):
# its pieces (blossom_assets.py) in the hall's own frame, the hall at the origin facing +Z and the approach coming in along +Z
# (blossom_assets_run.SHRINE_SET is the same list): the torii where the path tops the plateau, twelve paving slabs, a pair of
# toro lanterns halfway, the chozuya beside the approach facing it. The hall faces west, back down the path to the lawn.
SHRINE_AT = (232.0, -25.0)
SHRINE_YAW = -math.pi / 2          # turns the hall's +Z (its front) toward local -X
SHRINE_PIECES = [("BS_ShrineHall", 0.0, 0.0, 0.0), ("BS_Torii", 0.0, 54.0, 0.0),
                 ("BS_ShrineLantern", -6.0, 32.0, 0.0), ("BS_ShrineLantern", 6.0, 32.0, 0.0), ("BS_Chozuya", 11.0, 37.0, -math.pi / 2)] + \
                [("BS_ShrinePathSlab", 0.0, 9.0 + 3.2 * k, 0.0) for k in range(12)]
SHRINE_COURT = (-15.0, 15.0, -11.0, 58.0)   # the gravel court under it (the hall's frame: x from, x to, z from, z to)


def shrine_point(xs, zs):
    c, s_ = math.cos(SHRINE_YAW), math.sin(SHRINE_YAW)
    return SHRINE_AT[0] + xs * c + zs * s_, SHRINE_AT[1] - xs * s_ + zs * c


def shrine_local(x, z):
    dx, dz = x - SHRINE_AT[0], z - SHRINE_AT[1]
    c, s_ = math.cos(SHRINE_YAW), math.sin(SHRINE_YAW)
    return dx * c - dz * s_, dx * s_ + dz * c


def in_shrine_court(x, z, pad=0.0):
    xs, zs = shrine_local(x, z)
    x0, x1, z0, z1 = SHRINE_COURT
    # a rounded rectangle (corner radius 4)
    qx = max(x0 + 4 - xs, xs - (x1 - 4), 0.0)
    qz = max(z0 + 4 - zs, zs - (z1 - 4), 0.0)
    return math.hypot(qx, qz) <= 4 + pad


CANOPY_R = {"BS_TreeElder": 21, "BS_TreeWeeping": 12, "BS_TreeLeaning": 9, "BS_TreeTwin": 14, "BS_TreeYoung": 7, "BS_TreeGnarled": 14}
CANOPY_AT = {"BS_TreeLeaning": (0, 9.3), "BS_TreeGnarled": (2.2, 0.2)}   # the canopy's centre off the trunk (pieces.json)

# the climb from the hub: stones (x, z, top, radius, piece) in island-local studs; Platforms are larger floating islets of terrain
# with a checkpoint each. Gaps are kept to what a first-rank player clears with a plain running jump (GameConfig.Qinggong: run 22,
# jump 7.2 high): see check_route().
HUB_START = (43.4, -346.1)       # where the hub's south-east avenue meets its rim (bearing 30, radius 250)


def build_route():
    stones, platforms = [], []
    # the hub's end: two flush stones on the verge from the Ring Road to the rim, then the climb
    seq = [
        # x, z, top, radius, piece
        (42.5, -337.5, 0.8, 4.2, "BS_SteppingStoneA"),
        (37.0, -327.0, 2.0, 4.0, "BS_SteppingStoneC"),
        (29.0, -317.0, 3.2, 4.6, "BS_SteppingStoneA"),
        (19.0, -308.0, 4.4, 4.2, "BS_SteppingStoneB"),
        (10.0, -298.5, 5.6, 4.0, "BS_SteppingStoneC"),
    ]
    stones += seq
    platforms.append({"Name": "PlatformA", "Centre": (3.0, -282.0), "Top": 7.0, "Radius": 11.0, "Depth": 26.0})
    seq = [
        (-1.0, -263.0, 8.2, 4.2, "BS_SteppingStoneA"),
        (4.0, -251.5, 9.4, 3.6, "BS_SteppingStoneC"),     # a leap: 7 studs edge to edge
        (14.0, -241.0, 10.6, 4.4, "BS_SteppingStoneB"),
        (25.0, -234.5, 11.6, 3.8, "BS_SteppingStoneC"),
    ]
    stones += seq
    platforms.append({"Name": "PlatformB", "Centre": (43.0, -224.0), "Top": 13.0, "Radius": 12.0, "Depth": 30.0})
    seq = [
        (49.0, -206.5, 11.0, 4.4, "BS_SteppingStoneA"),
        (44.5, -195.5, 8.8, 4.0, "BS_SteppingStoneB"),
    ]
    stones += seq
    return stones, platforms


STONES, PLATFORMS = build_route()

# the jump the Qinggong air leap opens (an optional shortcut): from Platform A straight up to Platform B's rim
LEAP_STONE = (22.0, -262.0, 13.5, 3.4, "BS_SteppingStoneC")


# ---------- the ground ----------
def ground(x, z):
    """(height over Y 200, material) or (None, None) off the island."""
    e = island_field(x, z)
    if e <= 0:
        return None, None
    h = LAWN
    grove = smoothstep(-60, -170, x)
    h += grove * (2.0 + 5.0 * fbm(x / 70.0, z / 70.0, 5))
    h += smoothstep(40, 150, z) * 3.0 * fbm(x / 60.0, z / 60.0, 7)
    p = 1.0 - smoothstep(55, 98, math.hypot(x - PLATEAU_AT[0], z - PLATEAU_AT[1]))
    h = lerp(h, PLATEAU, p)
    # a soft lip round the edge (the Lookout keeps its cliff)
    h -= (1.0 - smoothstep(0, 12, e)) * 3.0 * (1.0 - p)
    # the arrival and the lawn are level
    h = lerp(h, LAWN, smoothstep(-10, 2, 14 - math.hypot(x - ARRIVAL[0], z - ARRIVAL[1])))
    h = lerp(h, LAWN, smoothstep(-10, 0, zone_field(x, z)))
    # the pond's hollow, banks and bed
    pd = pond_field(x, z)
    h = lerp(h, 6.5, smoothstep(-22, -5, pd))
    if pd > -3:
        h = lerp(h, 4.0, smoothstep(-3, 0, pd))
        if pd > 0:
            h = 4.0 - min(6.5, pd * 0.45)
    # the bridge's ends are level with its deck's ends
    for s in (-1, 1):
        bx, bz = bridge_end(s)
        d = math.hypot(x - bx, z - bz)
        h = lerp(h, LAWN, smoothstep(9, 4, d))
    # material
    mat = "Grass"
    if pd > 0.6:
        mat = "Mud"
    elif pd > -2.5:
        mat = "Ground"
    elif p > 0.25 and e < 7:
        mat = "Rock"
    if mat == "Grass" and in_shrine_court(x, z):
        mat = "Cobblestone"   # the shrine's gravel court
    if mat == "Grass":
        zf = zone_field(x, z)
        if -4.0 < zf <= 0.0:
            mat = "Cobblestone"          # the Training Ground's border, inside its kerb
        elif path_dist(x, z) < 0 or math.hypot(x - ARRIVAL[0], z - ARRIVAL[1]) < 12:
            mat = "Cobblestone"
        else:
            for piece, tx, tz, yaw, sc in TREES:
                ox, oz = CANOPY_AT.get(piece, (0, 0))
                cx = tx + (ox * math.cos(yaw) + oz * math.sin(yaw)) * sc
                cz = tz + (-ox * math.sin(yaw) + oz * math.cos(yaw)) * sc
                if math.hypot(x - cx, z - cz) < CANOPY_R[piece] * sc * 0.75:
                    mat = "LeafyGrass"   # under the blossom: no grass blades, so the fallen petals show
                    break
    return h, mat


def bottom(x, z):
    """How deep the rock underside reaches at this column (negative, over Y 200): deepest under the middle, with hanging lobes."""
    e = max(0.0, island_field(x, z))
    # a tapering bowl (the deeper the farther in), ridged by noise, with hanging lobes under the Grove, the middle and the Lookout
    d = 9.0 + 0.5 * e + 18.0 * (fbm(x / 40.0, z / 40.0, 21) - 0.35) * smoothstep(0, 30, e)
    for cx, cz, depth, sigma in ((-215, 20, 30, 42), (20, 0, 26, 55), (200, -20, 30, 38), (-40, 130, 22, 34), (100, 60, 18, 30)):
        d += depth * math.exp(-((x - cx) ** 2 + (z - cz) ** 2) / (2 * sigma * sigma)) * smoothstep(0, 40, e)
    return -max(6.0, min(100.0, d))


def water(x, z):
    return WATER if pond_field(x, z) > -1.5 else None


# ---------- the grid ----------
def grid():
    pts = []
    for l in LOBES:
        for k in range(32):
            a = 2 * math.pi * k / 32
            pts.append(to_world(l[0] + l[2] * 1.06 * math.cos(a), l[1] + l[3] * 1.06 * math.sin(a)))
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    ox = math.floor(min(xs) / CELL) * CELL - CELL
    oz = math.floor(min(zs) / CELL) * CELL - CELL
    n = int(math.ceil(max(max(xs) - ox, max(zs) - oz) / CELL)) + 2
    return ox, oz, n


MATERIALS = ["Grass", "Ground", "Rock", "Cobblestone", "LeafyGrass", "Mud"]


def sample_grid():
    ox, oz, n = grid()
    H, M, Wt, B = [], [], [], []
    for j in range(n):
        for i in range(n):
            wx, wz = ox + (i + 0.5) * CELL, oz + (j + 0.5) * CELL
            x, z = to_local(wx, wz)
            h, m = ground(x, z)
            if h is None:
                H.append(None); M.append(0); Wt.append(None); B.append(None)
                continue
            # a narrow path or border covering part of the cell wins, so it stays continuous on the voxel grid
            if m == "Grass":
                for sx, sz in ((-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3), (1.3, 1.3)):
                    _, m2 = ground(*to_local(wx + sx, wz + sz))
                    if m2 == "Cobblestone":
                        m = "Cobblestone"
                        break
            H.append(h); M.append(MATERIALS.index(m) + 1)
            wl = water(x, z)
            Wt.append(wl if wl is not None and wl > h else None)
            B.append(bottom(x, z))
    # steep ground shows rock
    for j in range(1, n - 1):
        for i in range(1, n - 1):
            k = j * n + i
            if H[k] is None or MATERIALS[M[k] - 1] not in ("Grass", "LeafyGrass"):
                continue
            nb = [H[k + 1], H[k - 1], H[k + n], H[k - n]]
            if any(v is None for v in nb):
                continue
            slope = max(abs(nb[0] - nb[1]), abs(nb[2] - nb[3])) / (2 * CELL)
            if slope > 0.85:
                M[k] = MATERIALS.index("Rock") + 1
    return ox, oz, n, H, M, Wt, B


# ---------- placements ----------
def edge_points(field, level, step, jitter_seed, offset=0.0):
    """Points along the outline where field == level (marching rays from the shape's lobes), every ~step studs."""
    raise NotImplementedError


def outline(field, centre, radius_max, samples=360):
    """The outline of a star-shaped region round `centre`: (x, z) per bearing."""
    cx, cz = centre
    out = []
    for k in range(samples):
        a = 2 * math.pi * k / samples
        r = 0.0
        while r < radius_max and field(cx + math.cos(a) * r, cz + math.sin(a) * r) > 0:
            r += 0.5
        out.append((cx + math.cos(a) * r, cz + math.sin(a) * r))
    return out


def resample(loop, step):
    out, acc = [loop[0]], 0.0
    for k in range(1, len(loop) + 1):
        a, b = loop[k - 1], loop[k % len(loop)]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        acc += seg
        if acc >= step:
            out.append(b)
            acc = 0.0
    return out


def placements():
    kit = {}

    def add(name, x, z, y=None, yaw=0.0, scale=1.0):
        if y is None:
            y = ground(x, z)[0]
        kit.setdefault(name, []).append((x, y, z, yaw, scale))

    rnd = lambda k, s=0: _hash(k, 7, s)

    for k, (piece, x, z, yaw, sc) in enumerate(TREES):
        add(piece, x, z, ground(x, z)[0] - 0.4, yaw, sc)
        # its fallen petals, under the canopy
        ox, oz = CANOPY_AT.get(piece, (0, 0))
        cx = x + (ox * math.cos(yaw) + oz * math.sin(yaw)) * sc
        cz = z + (-ox * math.sin(yaw) + oz * math.cos(yaw)) * sc
        if pond_field(cx, cz) < -2:
            add("BS_PetalDrift", cx, cz, None, rnd(k) * 6.28, sc * (0.9 if CANOPY_R[piece] < 10 else 1.25))

    # the Training Ground's kerb: worn stones round its outline, open where the paths come in
    loop = outline(zone_field, ZONE_CENTRE, 90)
    kerb = resample(loop, 5.0)
    for k, (x, z) in enumerate(kerb):
        if path_dist(x, z) < 2.5:
            continue
        nx, nz = kerb[(k + 1) % len(kerb)]
        yaw = math.atan2(nx - x, nz - z) + math.pi / 2
        add("BS_KerbStone", x, z, LAWN - 0.15, yaw + (rnd(k, 3) - 0.5) * 0.12)
    # seat stones in a loose arc facing the pond (the lawn's west side)
    for k in range(7):
        a = math.radians(152 + k * 12)
        x, z = ZONE_CENTRE[0] + math.cos(a) * 44, ZONE_CENTRE[1] + math.sin(a) * 30
        if zone_field(x, z) > 5:
            add("BS_SeatStone", x, z, LAWN - 0.1, math.atan2(-52 - x, -40 - z) + (rnd(k, 5) - 0.5) * 0.4)

    # the pond: the bridge, edging rocks gathered at a few places (not evenly), lilies, reeds and plantain at the banks
    bx, bz = BRIDGE["Position"]
    add("BS_Bridge", bx, bz, LAWN, BRIDGE["Yaw"])
    pond_loop = [p for c in POND_LOBES for p in outline(pond_field, c, 80, 360)]
    pond_loop = [p for p in pond_loop if pond_field(p[0] * 1.0, p[1]) > -1.5 and pond_field(p[0], p[1]) < 1.5]
    ne, fe = bridge_end(-1), bridge_end(1)
    rock_spots = [(ne[0] - 5, ne[1] + 2, 6), (fe[0] + 5, fe[1] - 2, 6), (-160, -26, 9), (-138, 2, 6), (4, -50, 8), (-40, -6, 5), (-70, -74, 6)]
    k = 0
    for sx, sz, spread in rock_spots:
        near = sorted(pond_loop, key=lambda p: math.hypot(p[0] - sx, p[1] - sz))[:40]
        for m in range(3):
            px, pz = near[int(rnd(k, 9) * len(near))]
            if min(math.hypot(px - ne[0], pz - ne[1]), math.hypot(px - fe[0], pz - fe[1])) < 5:
                k += 1
                continue                       # leave the bridge's ends clear
            piece = ("BS_EdgeRockA", "BS_EdgeRockB", "BS_EdgeRockC")[(k + m) % 3]
            add(piece, px, pz, ground(px, pz)[0] - 0.5, rnd(k, 1) * 6.28, 0.8 + 0.5 * rnd(k, 2))
            k += 1
    lilies = 0
    for k in range(400):
        x, z = -165 + 180 * rnd(k, 31), -80 + 85 * rnd(k, 37)
        pd = pond_field(x, z)
        if pd < 4 or math.hypot(x - bx, z - bz) < 14:
            continue
        if lilies >= 26:
            break
        if any(math.hypot(x - e[0], z - e[2]) < 5 for n in ("BS_LilyPadA", "BS_LilyPadB", "BS_LilyPadCluster") for e in kit.get(n, [])):
            continue
        piece = ("BS_LilyPadA", "BS_LilyPadB", "BS_LilyPadCluster", "BS_LilyPadA")[lilies % 4]
        add(piece, x, z, WATER, rnd(k, 41) * 6.28)
        if lilies % 4 == 1:
            add("BS_LilyFlower", x + 0.6, z - 0.3, WATER + 0.02, rnd(k, 43) * 6.28)
        lilies += 1
    plants = 0
    for k, (x, z) in enumerate(resample(pond_loop, 9.0)):
        if math.hypot(x - bx, z - bz) < 18 or rnd(k, 51) < 0.45:
            continue
        piece = "BS_Reeds" if plants % 3 != 2 else "BS_WaterPlantain"
        # just inside the water line
        add(piece, x + (bx - x) * 0.04, z + (bz - z) * 0.04, WATER - 0.3, rnd(k, 53) * 6.28, 0.85 + 0.4 * rnd(k, 55))
        plants += 1
    # a line of stepping stones across the small pool (a second, playful crossing)
    for k, t in enumerate((0.2, 0.4, 0.6, 0.8)):
        x, z = lerp(-146, -120, t) + (rnd(k, 61) - 0.5) * 3, lerp(-44, 4, t)
        add("BS_SteppingStoneC", x, z, WATER + 0.55, rnd(k, 63) * 6.28, 0.62)
    # the shrine on the Lookout (its seats went: the hall stands there now)
    for piece, xs, zs, yaw in SHRINE_PIECES:
        x, z = shrine_point(xs, zs)
        lift = 0.06 if piece == "BS_ShrinePathSlab" else 0.0   # (the slabs' faces just over the gravel)
        add(piece, x, z, ground(x, z)[0] + lift, SHRINE_YAW + yaw)
    # the arrival: a pair of the big edge rocks either side of the landing, a petal drift on the paving
    add("BS_EdgeRockC", ARRIVAL[0] - 13, ARRIVAL[1] + 6, LAWN - 0.6, 0.6, 1.1)
    add("BS_EdgeRockB", ARRIVAL[0] + 12.5, ARRIVAL[1] + 3, LAWN - 0.5, 2.2, 1.0)
    return kit


def koi_paths():
    """Closed swimming loops in each lobe of the pond, 1 under the surface (the bed is deeper there)."""
    loops = []
    for cx, cz, a, b, rot, seed in ((-52, -40, 38, 18, 0.22, 1), (-40, -42, 22, 11, 0.22, 2), (-132, -20, 15, 11, -0.5, 3)):
        pts = []
        for k in range(16):
            t = 2 * math.pi * k / 16
            w = 0.85 + 0.3 * vnoise(k * 0.7, seed, seed)
            lx, lz = math.cos(t) * a * w, math.sin(t) * b * w
            c, s = math.cos(-rot), math.sin(-rot)
            pts.append((cx + lx * c - lz * s, cz + lx * s + lz * c))
        loops.append(pts)
    return loops


# ---------- checks ----------
JUMP_V = math.sqrt(2 * 196.2 * 7.2)     # StarterPlayer: JumpHeight 7.2, Gravity 196.2
RUN = 22.0                              # the first rank's run speed (GameConfig.Qinggong.Levels[1])


def plain_jump_reach(rise):
    """Horizontal studs a running first-rank player covers in a plain jump landing `rise` higher (None if too high)."""
    disc = JUMP_V * JUMP_V - 2 * 196.2 * rise
    if disc < 0:
        return None
    t = (JUMP_V + math.sqrt(disc)) / 196.2
    return RUN * t


def route_hops():
    """Each hop of the climb, hub to island: (from, to, edge gap, rise)."""
    pieces = [("HubRim", HUB_START[0], HUB_START[1], 0.0, 0.0)]
    seq = list(STONES[:5]) + [PLATFORMS[0]] + list(STONES[5:9]) + [PLATFORMS[1]] + list(STONES[9:])
    for p in seq:
        if isinstance(p, dict):
            pieces.append((p["Name"], p["Centre"][0], p["Centre"][1], p["Top"], p["Radius"] - 1.5))
        else:
            pieces.append((p[4], p[0], p[1], p[2], p[3] * 0.9))
    end = (ARRIVAL[0], ARRIVAL[1])
    # the island's edge on the line from the last stone to the arrival
    lx, lz = pieces[-1][1], pieces[-1][2]
    t = 0.0
    while island_field(lerp(lx, end[0], t), lerp(lz, end[1], t)) <= 0 and t < 1:
        t += 0.01
    ex, ez = lerp(lx, end[0], t), lerp(lz, end[1], t)
    pieces.append(("IslandEdge", ex, ez, ground(*end)[0] - 1.0, 0.0))
    hops = []
    for a, b in zip(pieces, pieces[1:]):
        gap = math.hypot(b[1] - a[1], b[2] - a[2]) - a[4] - b[4]
        hops.append((a[0], b[0], gap, b[3] - a[3]))
    return hops


def check_route():
    rows, worst = [], 1e9
    for a, b, gap, rise in route_hops():
        up = plain_jump_reach(rise)
        down = plain_jump_reach(-rise)
        margin = min(up - gap if up else -1, down - gap if down else -1)
        worst = min(worst, margin)
        rows.append("%-18s -> %-18s gap %5.1f rise %+5.1f  reach up %5.1f / back %5.1f  margin %4.1f" % (a, b, gap, rise, up or 0, down or 0, margin))
    return rows, worst


# ---------- writing ----------
def lua_num(v):
    return "false" if v is None else ("%.2f" % v)


def write_terrain(path):
    ox, oz, n, H, M, Wt, B = sample_grid()
    lines = [
        "-- Written by tools/blender/world/blossom_layout.py (the Blossom Sanctuary, 2026-11-16). Do not edit by hand.",
        "return {",
        '    Island = "%s",' % ISLAND,
        "    Centre = Vector3.new(%g, %g, %g)," % CENTRE,
        "    Turns = %.5f, -- quarter turns about the centre, each adding 90 degrees of bearing" % TURNS,
        "    BakedTurn = true, -- the grid below is already turned",
        "    Origin = Vector2.new(%g, %g), -- world X/Z of the grid's first corner" % (ox, oz),
        "    Cell = %d," % CELL,
        "    Size = %d," % n,
        "    Materials = { %s }," % ", ".join('"%s"' % m for m in MATERIALS),
    ]

    def chunked(name, vals):
        out = ["    %s = {" % name]
        for k in range(0, len(vals), n):
            out.append("        " + ", ".join(vals[k:k + n]) + ",")
        out.append("    },")
        return out
    lines += chunked("Heights", [lua_num(v) for v in H])
    lines += chunked("MaterialIndex", [str(v) for v in M])
    lines += chunked("WaterLevels", [lua_num(v) for v in Wt])
    lines.append("    -- how deep the rock underside reaches under each column (over Centre.Y), for WorldBuilder.buildTerrain's Bottoms")
    lines += chunked("Bottoms", [lua_num(v) for v in B])
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return n, sum(1 for h in H if h is not None)


def v3(x, y, z):
    return "Vector3.new(%.2f, %.2f, %.2f)" % (x, y, z)


def write_placements(path):
    kit = placements()
    L = ["-- Written by tools/blender/world/blossom_layout.py (the Blossom Sanctuary, 2026-11-16). Do not edit by hand.",
         "-- Island-local Roblox studs (local -Z faces the hub). BS_* are the sanctuary's pieces (assets/world/BlossomSanctuary),",
         "-- placed by WorldBuilder.placeKit; the rest is read by WorldBuilder.buildSanctuary and buildApproach.",
         "return {", "    Kit = {"]
    for name in sorted(kit):
        L.append("        %s = {" % name)
        for x, y, z, yaw, sc in kit[name]:
            extra = "" if abs(sc - 1) < 1e-6 else ", Scale = %.3f" % sc
            L.append("            { Position = %s, Yaw = %.4f%s }," % (v3(x, y, z), yaw, extra))
        L.append("        },")
    L.append("    },")
    L.append("    -- the Training Ground (GameConfig.TrainingStation): +50% Qi while cultivating inside this outline (island-local X/Z, the lawn")
    L.append("    -- at Floor), within Height studs of it; the kerb stones stand on it; its sign stands where the arrival's path reaches the lawn")
    L.append("    TrainingGround = {")
    L.append("        Floor = %.2f," % LAWN)
    L.append("        Height = %d," % ZONE_HEIGHT)
    L.append("        Outline = {")
    for x, z in resample(outline(zone_field, ZONE_CENTRE, 90, 720), 4.0):
        L.append("            Vector2.new(%.2f, %.2f)," % (x, z))
    L.append("        },")
    L.append("        Sign = %s," % v3(54, LAWN + 9.5, -62))
    L.append("    },")
    L.append("    -- the island's checkpoint (a fall off the island returns here): the arrival's landing, facing into the island")
    L.append("    Checkpoint = { Position = %s, Yaw = %.4f }," % (v3(ARRIVAL[0], LAWN, ARRIVAL[1] + 4), math.pi))
    L.append("    -- the climb from the hub (WorldBuilder.buildApproach): each stone's top centre, radius and cap piece; the platforms are")
    L.append("    -- floating islets of terrain, each with a checkpoint; HubStart is on the hub's verge at the end of its south-east avenue")
    L.append("    Approach = {")
    hx, hz = HUB_START
    L.append("        HubStart = { Position = %s, Yaw = %.4f }," % (v3(hx, 0.0, hz), 0.0))
    L.append("        Stones = {")
    for x, z, top, r, piece in STONES + [LEAP_STONE]:
        L.append('            { Position = %s, Radius = %.1f, Piece = "%s"%s },' % (v3(x, top, z), r, piece, ", Leap = true" if (x, z) == LEAP_STONE[:2] else ""))
    L.append("        },")
    L.append("        Platforms = {")
    for p in PLATFORMS:
        L.append('            { Name = "%s", Position = %s, Radius = %.1f, Depth = %.1f },' % (p["Name"], v3(p["Centre"][0], p["Top"], p["Centre"][1]), p["Radius"], p["Depth"]))
    L.append("        },")
    L.append("        -- what stands on the platforms (kit pieces, platform-local studs)")
    L.append("        Dressing = {")
    L.append('            { Platform = "PlatformA", Piece = "BS_TreeYoung", Position = Vector3.new(-4.5, 0, 3.5), Yaw = 1.2, Scale = 0.95 },')
    L.append('            { Platform = "PlatformA", Piece = "BS_PetalDrift", Position = Vector3.new(-3, 0, 2.5), Yaw = 0.5, Scale = 0.7 },')
    L.append('            { Platform = "PlatformA", Piece = "BS_SeatStone", Position = Vector3.new(4.5, 0, 4), Yaw = 3.6 },')
    L.append('            { Platform = "PlatformB", Piece = "BS_TreeGnarled", Position = Vector3.new(5.5, 0, -4.5), Yaw = 4.2, Scale = 0.75 },')
    L.append('            { Platform = "PlatformB", Piece = "BS_PetalDrift", Position = Vector3.new(4, 0, -2), Yaw = 2.0, Scale = 0.7 },')
    L.append('            { Platform = "PlatformB", Piece = "BS_EdgeRockB", Position = Vector3.new(-7.5, -0.4, 5.5), Yaw = 0.7, Scale = 0.8 },')
    L.append("        },")
    L.append("    },")
    L.append("    -- the koi's swimming loops (the pond's surface is at %.1f; they swim 1 under it, where they read through the water), and the pond's middle" % WATER)
    L.append("    Pond = {")
    L.append("        Water = %.2f," % WATER)
    L.append("        Centre = %s," % v3(-70, WATER, -36))
    L.append("        Koi = {")
    for loop in koi_paths():
        L.append("            { " + ", ".join(v3(x, WATER - 1.0, z) for x, z in loop) + " },")
    L.append("        },")
    L.append("    },")
    L.append("    -- the island's reach for WorldService (its ground runs this far from the centre)")
    L.append("    Reach = 335,")
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return sum(len(v) for v in kit.values())


# ---------- the sketch (a plain PNG, no imaging library) ----------
def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def sketch(path):
    S = 1.25                                  # pixels per stud
    X0, X1, Z0, Z1 = -360.0, 340.0, -380.0, 230.0
    w, h = int((X1 - X0) * S), int((Z1 - Z0) * S)
    px = bytearray(w * h * 3)
    sky = (34, 40, 56)
    COL = {"Grass": (104, 160, 86), "Ground": (128, 100, 74), "Rock": (120, 122, 130), "Cobblestone": (190, 182, 166),
           "LeafyGrass": (92, 138, 78), "Mud": (70, 56, 44)}

    def put(x, z, c, a=1.0):
        i, j = int((X1 - x) * S), int((Z1 - z) * S)  # seen from above: local -Z (the hub) at the bottom, local +X on the left
        if 0 <= i < w and 0 <= j < h:
            k = (j * w + i) * 3
            for m in range(3):
                px[k + m] = int(px[k + m] * (1 - a) + c[m] * a)

    for j in range(h):
        z = Z1 - (j + 0.5) / S
        for i in range(w):
            x = X1 - (i + 0.5) / S
            hgt, m = ground(x, z)
            if hgt is None:
                c = sky
            else:
                c = COL[m]
                shade = 0.82 + 0.018 * hgt
                c = tuple(min(255, int(v * shade)) for v in c)
                wl = water(x, z)
                if wl is not None and wl > hgt:
                    d = min(1.0, (wl - hgt) / 6.0)
                    c = tuple(int(c[k] * (1 - 0.75 * d) + (70, 170, 175)[k] * 0.75 * d) for k in range(3))
            k = (j * w + i) * 3
            px[k:k + 3] = bytes(c)

    def disc(x, z, r, c, a=1.0, ring=None):
        for dz in range(int(-r * S) - 1, int(r * S) + 2):
            for dx in range(int(-r * S) - 1, int(r * S) + 2):
                d = math.hypot(dx, dz) / S
                if d <= r and (ring is None or d >= r - ring):
                    put(x + dx / S, z + dz / S, c, a)

    def line(pts, c, width=1.0, a=1.0):
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            n = int(math.hypot(x1 - x0, z1 - z0) * S) + 1
            for k in range(n + 1):
                t = k / max(1, n)
                disc(lerp(x0, x1, t), lerp(z0, z1, t), width, c, a)

    # the hub's rim (an arc of radius 250 round the hub's centre) for scale
    hcx, hcz = to_local(0, 0)
    for k in range(1200):
        a = 2 * math.pi * k / 1200
        x, z = to_local(250 * math.cos(a), 250 * math.sin(a))
        if X0 < x < X1 and Z0 < z < Z1:
            disc(x, z, 1.2, (230, 230, 240))
    # the zone
    for x, z in outline(zone_field, ZONE_CENTRE, 90):
        disc(x, z, 0.9, (255, 210, 80))
    kit = placements()
    for name, entries in kit.items():
        for x, y, z, yaw, sc in entries:
            if name.startswith("BS_Tree"):
                r = CANOPY_R[name] * sc
                ox, oz = CANOPY_AT.get(name, (0, 0))
                cx = x + (ox * math.cos(yaw) + oz * math.sin(yaw)) * sc
                cz = z + (-ox * math.sin(yaw) + oz * math.cos(yaw)) * sc
                disc(cx, cz, r, (244, 176, 200), 0.55)
                disc(cx, cz, r, (200, 110, 150), 1.0, ring=0.9)
                disc(x, z, 1.4, (80, 54, 52))
            elif name == "BS_Bridge":
                for t in range(-15, 16):
                    for s in (-3.5, -2.5, -1.5, 0, 1.5, 2.5, 3.5):
                        put(x + t * math.sin(yaw) + s * math.cos(yaw), z + t * math.cos(yaw) - s * math.sin(yaw), (236, 228, 210))
            elif name == "BS_KerbStone":
                disc(x, z, 1.0, (236, 228, 210))
            elif name.startswith("BS_EdgeRock"):
                disc(x, z, 1.6 * sc, (200, 196, 186))
            elif name.startswith("BS_Lily"):
                disc(x, z, 1.2, (80, 140, 70))
            elif name in ("BS_Reeds", "BS_WaterPlantain"):
                disc(x, z, 1.0, (60, 120, 60))
            elif name in ("BS_SeatStone",):
                disc(x, z, 1.6, (236, 228, 210))
            elif name.startswith("BS_SteppingStone"):
                disc(x, z, 2.0, (236, 228, 210))
    for loop in koi_paths():
        for k, (x, z) in enumerate(loop):
            disc(x, z, 0.8, (240, 120, 50))
    for p in PLATFORMS:
        disc(p["Centre"][0], p["Centre"][1], p["Radius"], (110, 150, 92))
        disc(p["Centre"][0], p["Centre"][1], p["Radius"], (120, 122, 130), ring=1.5)
        disc(p["Centre"][0], p["Centre"][1], 1.6, (90, 200, 255))
    for x, z, top, r, piece in STONES + [LEAP_STONE]:
        disc(x, z, r, (236, 228, 210) if (x, z) != LEAP_STONE[:2] else (250, 200, 120))
    disc(HUB_START[0], HUB_START[1], 2.0, (90, 200, 255))
    disc(ARRIVAL[0], ARRIVAL[1] + 4, 2.0, (90, 200, 255))
    write_png(path, w, h, px)
    return w, h


def report():
    ox, oz, n, H, M, Wt, B = sample_grid()
    cells = sum(1 for v in H if v is not None)
    area = cells * CELL * CELL
    hub_area = math.pi * 248 ** 2
    rows, worst = check_route()
    # clearances from every other island
    others = {"Yggdrasil": ((0, 0), 250), "BeginnerIsle": ((-480, 24), 140), "JadeGrove": ((-384, -448), 160),
              "EmberPeak": ((-128, -696), 150), "MoonlitIsle": ((192, -804), 125), "OriginAbyss": ((596, -856), 165)}
    clear = {}
    for name, ((cx, cz), r) in others.items():
        best = 1e9
        for j in range(n):
            for i in range(n):
                if H[j * n + i] is not None:
                    wx, wz = ox + (i + 0.5) * CELL, oz + (j + 0.5) * CELL
                    best = min(best, math.hypot(wx - cx, wz - cz) - r)
        clear[name] = round(best)
    conflicts = []
    for piece, x, z, yaw, sc in TREES:
        if zone_field(x, z) > -6:
            conflicts.append("%s at (%d, %d) is in or at the Training Ground" % (piece, x, z))
        if pond_field(x, z) > -2:
            conflicts.append("%s at (%d, %d) stands in the pond" % (piece, x, z))
        if path_dist(x, z) < 1.5:
            conflicts.append("%s at (%d, %d) stands on a path" % (piece, x, z))
        if island_field(x, z) < 6:
            conflicts.append("%s at (%d, %d) is at the island's edge" % (piece, x, z))
        if in_shrine_court(x, z, pad=3):
            conflicts.append("%s at (%d, %d) stands in the shrine's court" % (piece, x, z))
    lows = [b for b in B if b is not None]
    return {
        "grid": {"origin": (ox, oz), "size": n, "cells": cells},
        "area_sq_studs": area, "hub_area_sq_studs": round(hub_area), "ratio_to_hub": round(area / hub_area, 2),
        "deepest_underside": min(lows), "turns": TURNS, "yaw_deg": math.degrees(YAW),
        "clearance_to_islands": clear, "route": rows, "route_worst_margin": round(worst, 2),
        "hub_start_world": to_world(*HUB_START), "arrival_world": to_world(*ARRIVAL),
        "conflicts": conflicts,
    }


if __name__ == "__main__":
    r = report()
    for row in r.pop("route"):
        print(row)
    print(json.dumps(r, indent=1, default=list))
    if "--write" in sys.argv:
        n, cells = write_terrain(os.path.join(REPO, "src", "worldbuild", "Terrain", ISLAND + ".lua"))
        count = write_placements(os.path.join(REPO, "src", "worldbuild", "Placements", ISLAND + ".lua"))
        os.makedirs(os.path.join(REPO, "renders", "blossom_sanctuary"), exist_ok=True)
        wh = sketch(os.path.join(REPO, "renders", "blossom_sanctuary", "plan_topdown.png"))
        print("WROTE terrain %dx%d (%d cells), %d placements, sketch %s" % (n, n, cells, count, wh))

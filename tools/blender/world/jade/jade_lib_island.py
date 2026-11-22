"""jade_lib_island: Jade Grove's expanded ground (2026-11-22): the terrain data, the named sites and the routes. Plain Python, no Blender.

The first foundation's layout (jade_island.py, read through jade_lib_oldmap) is the base and stays the source of every position the game depends on:
the Grove Gate and the bridge landing, the Mantis Arena, the three egg stands, the three relics, the checkpoint, the Sage's hermitage, the Bloom Glade,
the spring Hollow, the Elder knoll (the guardian tree's now) and the Ruin Court. The island grows only on the sides away from Ember Peak and the
bridge (north-west, west, south-west, south, north: `GROWTH`), and gains a plateau with a waterfall (Mistfall Heights), a pond, a stream in a gorge, a
dry rift, a western valley and a northern glen. Every new term is multiplied by `free(x, z)`, which is exactly 0 inside the protected discs round what the
game depends on, so there the height and the material are the old ones to the last digit (jade_lib_verify proves it cell by cell).

Coordinates: island-local studs, x east, z south, y up, the arena's centre at the origin, ground about 0 (world Y 200); the grid is the engine's own
4-stud voxel grid.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_oldmap as O  # noqa: E402

OLD = O.OLD
fbm, smoothstep, gauss = O.fbm, O.smoothstep, O.gauss
CENTRE = OLD.CENTRE
NAME = OLD.NAME

# ======================================================================================================================
# what the game depends on (all from the old layout, unchanged)
# ======================================================================================================================
ARENA, ARRIVAL, LANDING, GATE = OLD.ARENA, OLD.ARRIVAL, OLD.LANDING, OLD.GATE
GLADE, ELDER, HOLLOW, POOL, HERMITAGE, RUINS, RING_R = OLD.GLADE, OLD.ELDER, OLD.HOLLOW, OLD.HOLLOW_POOL, OLD.HERMITAGE, OLD.RUINS, OLD.RING_R

# discs inside which nothing changes: (x, z, radius); free() rises from 0 to 1 over the next 14 studs
PROTECT = [
    (0.0, 0.0, 76.0),                                  # the arena, its flagstone border and the path ring (level out to RING_R + 2 + 12)
    (LANDING[0], LANDING[1], 44.0),                   # the arrival terrace, the Grove Gate, the bridge's landing and the checkpoint
    (ARRIVAL[0], ARRIVAL[1], 30.0),
    (HERMITAGE[0], HERMITAGE[1], 32.0),
    (GLADE[0], GLADE[1], 36.0),
    (ELDER[0], ELDER[1], 38.0),
    (HOLLOW[0], HOLLOW[1], 32.0),
    (RUINS[0], RUINS[1], 32.0),
]


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t)), t


def poly_nearest(x, z, pts):
    """(distance to the polyline, arc length at the nearest point, total length)."""
    best = (1e9, 0.0)
    acc = 0.0
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d, t = _seg_dist(x, z, a, b)
        if d < best[0]:
            best = (d, acc + t * L)
        acc += L
    return best[0], best[1], total


def point_at(pts, s):
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= s:
            t = (s - acc) / L
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        acc += L
    a, b = pts[-2], pts[-1]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def free(x, z):
    m = 1.0
    for (cx, cz, r) in PROTECT:
        m = min(m, smoothstep(r, r + 14.0, math.hypot(x - cx, z - cz)))
    return m


# ======================================================================================================================
# the rim: the old one plus growth lobes
# ======================================================================================================================
def _bump(d, centre, width):
    diff = (d - centre + 180) % 360 - 180
    return math.exp(-(diff / width) ** 2)


# (bearing, studs, width): nothing toward Ember Peak (north-east) or the bridge (south-east)
GROWTH = [(-135, 58, 36), (180, 50, 30), (140, 44, 28), (104, 26, 22), (-88, 40, 26), (-112, 16, 20)]


def _east_keep(d):
    """1 on the old rim's own side (bearings -60 .. +76), falling to 0 over 24 degrees."""
    a = (d + 180) % 360 - 180
    return smoothstep(-84, -60, a) * (1.0 - smoothstep(76, 100, a))


def growth(theta):
    d = math.degrees(theta)
    return sum(amount * _bump(d, bearing, width) for bearing, amount, width in GROWTH) * (1.0 - _east_keep(d))


def rim2(theta):
    return OLD.rim(theta) + growth(theta)


# ======================================================================================================================
# sites of the new ground (island-local)
# ======================================================================================================================
DIR_F = (0.9, 0.436)                                    # the High Falls face south-east, toward the island's middle
PLATEAU_C = (-122.0, -124.0)
PLATEAU_A, PLATEAU_B, PLATEAU_TOP = 34.0, 28.0, 13.0
RAMP_DIR = (-0.436, 0.9)                                # the plateau's gentle flank (a walkable ramp) faces south-west


def _fall_point(u):
    return (PLATEAU_C[0] + DIR_F[0] * u, PLATEAU_C[1] + DIR_F[1] * u)


FALLS_LIP = _fall_point(PLATEAU_A * 0.80)               # the top of the cliff, where the stream leaves the plateau
FALLS_FOOT = _fall_point(PLATEAU_A * 1.0)
POND = (*_fall_point(PLATEAU_A + 9.0), 9.0)             # the Spirit Pond at the foot of the falls: centre and radius
SPRING = _fall_point(-PLATEAU_A * 0.45)
STREAM_TOP = [SPRING, _fall_point(-PLATEAU_A * 0.1), FALLS_LIP]
STREAM = [(POND[0] - 6.0, POND[1] + 7.0), (-98.0, -84.0), (-112.0, -66.0), (-130.0, -48.0), (-144.0, -28.0), (-152.0, -6.0), (-158.0, 16.0), (-164.0, 38.0), (-174.0, 58.0), (-196.0, 72.0), (-224.0, 82.0)]
W_POOL = (-178.0, 62.0, 8.0)
RIFT = [(-150.0, 124.0), (-120.0, 134.0), (-88.0, 146.0), (-54.0, 160.0)]
W_VALLEY = (-196.0, -30.0, 30.0)                       # the western valley: centre and radius of its bowl
STONE_CIRCLE = (-196.0, -30.0)
GLEN = (-14.0, -178.0, 22.0)
CLEARING = (-86.0, 176.0, 22.0)

# bank pads where the three forest bridges land: (x, z, radius, level)
# the root bridge crosses the gorge at stream arc length 66, the log bridge at its waist, the rope bridge the Rift of Roots


def _gorge_width(t):
    return 10.5 * (1.0 - 0.4 * math.exp(-((t - 0.52) / 0.07) ** 2))


def _gorge_depth(t):
    return 9.0 * smoothstep(0.05, 0.16, t) * (1.0 - smoothstep(0.76, 0.92, t))


def bridge_site(kind):
    """Endpoints, centre line, span and deck level of a forest bridge (island-local, deck level = the bank's ground)."""
    if kind == "root":
        t = 0.28
    elif kind == "log":
        t = 0.52
    if kind in ("root", "log"):
        tot = poly_nearest(0, 0, STREAM)[2]
        p, d = point_at(STREAM, t * tot)
        n = (-d[1], d[0])
        w = _gorge_width(t)
        half = w + 6.0
        a = (p[0] - n[0] * half, p[1] - n[1] * half)
        b = (p[0] + n[0] * half, p[1] + n[1] * half)
        return {"A": a, "B": b, "centre": p, "span": 2 * half, "dir": n, "gorge_w": w}
    a, b = (-84.0, 128.0), (-64.0, 170.0)      # the rope bridge over the Rift of Roots (set in bridge_rope())
    return {"A": a, "B": b}


# ======================================================================================================================
# the ground
# ======================================================================================================================
def _plateau_q(x, z):
    dx, dz = x - PLATEAU_C[0], z - PLATEAU_C[1]
    u = dx * DIR_F[0] + dz * DIR_F[1]
    v = -dx * DIR_F[1] + dz * DIR_F[0]
    q = math.hypot(u / PLATEAU_A, v / PLATEAU_B)
    return q * (1.0 + 0.09 * fbm(x / 28.0 + 5, z / 28.0 - 2, seed=71, octaves=2)), dx, dz


def plateau_h(x, z):
    q, dx, dz = _plateau_q(x, z)
    if q > 1.25:
        return 0.0
    m = max(0.0, (dx * RAMP_DIR[0] + dz * RAMP_DIR[1]) / max(math.hypot(dx, dz), 1e-6))
    w = 0.2 + 0.42 * smoothstep(0.6, 0.95, m)             # the cliff breaks over 20 % of the radius; on the south-west flank over 62 %: a ramp
    top = PLATEAU_TOP + 0.9 * fbm(x / 20.0 + 3, z / 20.0 + 8, seed=72, octaves=2)
    return top * smoothstep(1.0, 1.0 - w, q)


def _carve(d, w, depth, soft):
    return depth * (1.0 - smoothstep(w, w + soft, d))


def features(x, z, h):
    """The new ground: `h` (the old ground, without its rim lip) changed by the plateau, the ponds, the gorge, the rift, the valley, the glen, the clearing."""
    f = free(x, z)
    if f <= 0.0:
        return h
    d0 = h
    # --- Mistfall Heights ---
    h = h + plateau_h(x, z)
    # the spring's shallow bowl on the plateau
    ds_ = math.hypot(x - SPRING[0], z - SPRING[1])
    h -= 1.6 * (1.0 - smoothstep(3.0, 7.0, ds_))
    # the stream across the plateau to the lip: a shallow bed
    dt, st, tt = poly_nearest(x, z, STREAM_TOP)
    h -= 1.3 * (1.0 - smoothstep(2.0, 5.0, dt))
    # --- the Spirit Pond ---
    pd = math.hypot(x - POND[0], z - POND[1])
    h -= 4.8 * (1.0 - smoothstep(POND[2] - 2.0, POND[2] + 5.0, pd))
    # --- the stream and the Mosswater Gorge ---
    ds, s, tot = poly_nearest(x, z, STREAM)
    t = s / tot
    gw = _gorge_width(t)
    gd = _gorge_depth(t)
    h -= _carve(ds, gw, gd, 5.0)
    h -= 1.8 * (1.0 - smoothstep(2.5, 7.0, ds)) * smoothstep(0.02, 0.12, t)          # the stream's own bed
    wd = math.hypot(x - W_POOL[0], z - W_POOL[1])
    h -= 3.4 * (1.0 - smoothstep(W_POOL[2] - 1.0, W_POOL[2] + 5.0, wd))
    # --- the Rift of Roots (a dry chasm) ---
    dr, sr, tr = poly_nearest(x, z, RIFT)
    tr = sr / tr
    h -= _carve(dr, 13.0, 13.0 * smoothstep(0.0, 0.16, tr) * (1.0 - smoothstep(0.84, 1.0, tr)), 4.5)
    # --- the western valley: a bowl with a low ridge round it, level in the middle for the stone circle ---
    vd = math.hypot(x - W_VALLEY[0], z - W_VALLEY[1])
    h -= 2.8 * (1.0 - smoothstep(10.0, W_VALLEY[2] - 4.0, vd))
    h += 3.4 * math.exp(-((vd - (W_VALLEY[2] + 6.0)) / 7.0) ** 2)
    w = 1 - smoothstep(16.0, 24.0, vd)
    h = h * (1 - w) + (-1.2) * w
    # --- the northern glen and the south-western clearing: levelled floors ---
    gd2 = math.hypot(x - GLEN[0], z - GLEN[1])
    w = 1 - smoothstep(GLEN[2] * 0.55, GLEN[2], gd2)
    h = h * (1 - w) + 0.9 * w
    cd = math.hypot(x - CLEARING[0], z - CLEARING[1])
    w = 1 - smoothstep(CLEARING[2] * 0.6, CLEARING[2], cd)
    h = h * (1 - w) + 1.3 * w
    return d0 + (h - d0) * f


def base_free(x, z):
    """The old ground (jade_island._base) without its rim clamp and its rim lip, so it runs on past the old rim; identical to it inside."""
    J = OLD
    h = 3.0 * fbm(x / 42 + 11, z / 42 - 3, seed=51, octaves=4)
    h += 5.0 * gauss((x + 70) * 0.5, z + 110, 26) * (1 + 0.4 * fbm(x / 14, z / 14, seed=52, octaves=2))
    h += 3.0 * gauss(x - 112, (z - 20) * 0.6, 18)
    ex, ez, er = J.ELDER
    h += 7.0 * (1 - smoothstep(er * 0.35, er, math.hypot(x - ex, z - ez)))
    hx, hz, hr = J.HOLLOW
    d = math.hypot(x - hx, z - hz)
    bowl = 1 - smoothstep(hr * 0.55, hr, d)
    h = h * (1 - bowl) - 7.0 * bowl
    px, pz, pr = J.HOLLOW_POOL
    dp = math.hypot(x - px, z - pz) - pr
    if dp < 1.0:
        w = 1 - smoothstep(-2.0, 0.8, dp)
        h = h * (1 - w) + J.POOL_BED * w
    for (cx, cz, rad), lift, soft in ((J.LANDING, 0.4, 7), (J.GLADE, 1.0, 8), (J.RUINS, 0.5, 8), (J.HERMITAGE, 1.0, 8), ((*J.ARENA, J.RING_R + 2), J.ARENA_Y, 12)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    if J.arena_distance(x, z) > J.ARENA_EDGE:
        h -= 0.4 * (1 - smoothstep(2.4, 4.4, J.path_distance(x, z)))
    return h


def lip(r, R):
    return 3.4 * (1 - smoothstep(R - 1, R - 12, r)) ** 1.6


def ground(x, z):
    """Ground height (None outside the rim) before the material is chosen."""
    r = math.hypot(x, z)
    R = rim2(math.atan2(z, x))
    if r > R:
        return None
    h = features(x, z, base_free(x, z))
    return h - lip(r, R)


def height(x, z):
    h = ground(x, z)
    if h is None:
        return None, None
    a = OLD.arena_distance(x, z)
    if a < OLD.ARENA_EDGE:
        return h, "Sandstone" if a > OLD.ARENA_R else "LeafyGrass"
    e = 1.5
    hs = [ground(x + dx, z + dz) for dx, dz in ((e, 0), (-e, 0), (0, e), (0, -e))]
    hs = [v if v is not None else h for v in hs]
    slope = math.hypot(hs[0] - hs[1], hs[2] - hs[3]) / (2 * e)
    if OLD.path_distance(x, z) < 3.8:
        mat = "Mud"
    elif slope > 0.75 or OLD.pool_distance(x, z) < 1.0:
        mat = "Sandstone"
    else:
        mat = "LeafyGrass"
    if mat == "LeafyGrass" and free(x, z) > 0.0:
        # the stream's and the ponds' beds are mud
        ds = poly_nearest(x, z, STREAM)[0]
        pd = math.hypot(x - POND[0], z - POND[1])
        wd = math.hypot(x - W_POOL[0], z - W_POOL[1])
        if (ds < 5.0 and h < -0.8) or pd < POND[2] - 1.0 or wd < W_POOL[2] - 1.0:
            mat = "Mud"
    return h, mat


MATERIALS = OLD.MATERIALS      # LeafyGrass, Mud, Sandstone: Jade's own, nothing new
HALF = 236                      # the grid covers the island's centre +- this many studs
CELL = 4


def grid():
    """Samples the whole grid: (origin x, origin z, n, heights, material indices) in the engine's order (rows of x), exactly as worldlib does it."""
    centre = CENTRE
    corner_x = math.floor((centre[0] - HALF) / CELL) * CELL
    corner_z = math.floor((centre[2] - HALF) / CELL) * CELL
    n = int(math.ceil((centre[0] + HALF - corner_x) / CELL))
    n = max(n, int(math.ceil((centre[2] + HALF - corner_z) / CELL)))
    heights, mats = [], []
    priority = [("Mud", 2)]
    for j in range(n):
        for i in range(n):
            x = corner_x - centre[0] + (i + 0.5) * CELL
            z = corner_z - centre[2] + (j + 0.5) * CELL
            h, m = height(x, z)
            if h is not None:
                counts = {}
                for sx in (-0.33, 0, 0.33):
                    for sz in (-0.33, 0, 0.33):
                        _, sm = height(x + sx * CELL, z + sz * CELL)
                        if sm:
                            counts[sm] = counts.get(sm, 0) + 1
                for name, need in priority:
                    if counts.get(name, 0) >= need:
                        m = name
                        break
            heights.append(None if h is None else round(h, 2))
            mats.append(0 if h is None else MATERIALS.index(m) + 1)
    return corner_x, corner_z, n, heights, mats

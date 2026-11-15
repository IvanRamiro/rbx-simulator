"""The hub's ground after the redesign (the owner, 2026-11-15: "PROCEED WITH THAT LAYOUT"; plan renders/hub_redesign/LAYOUT_PLAN.md):
where everything stands, the terrain under it, its marble paving, the lamps and the placements WorldBuilder reads.

Layout, island-local studs (x east, z south; a bearing runs from +x toward +z, north is -90):
- the Tree Ring round the World Tree's mound (r 80-104), as before;
- six beast pens on a ring (r 168, bearings 60, 120, 180, -120, -60, 0), each with its owner's spawn pad on a short spur from the
  Tree Ring, 10 studs before the pen's board (src/worldbuild/Placements/Pastures.lua);
- the Ring Road (r 216-236) joining every avenue, bridge and the shops; six avenues out between the pens (south to the Arrival
  Plaza, north to the Hatching Sanctum, north-east the Market Avenue into the Market Square, south-west to the Qi Spring,
  north-west and south-east to the Ring Road);
- the Leaderboard at the head of the south avenue against the tree, the Hidden (Wandering) Merchant's dais opposite it;
- the Merchants' Terrace: new ground out of the north-east rim (ygg_island.terrace_reach), the Market Square and the three shops
  (hub_district.py), clear of the Origin Abyss bridge;
- an apron the deck's width from the Ring Road to each bridge's gate, unchanged lines (Placements/Bridges.lua);
- the root stair from the Ring Road to the great root's head (unchanged, at the south rim).

Lamps stand only where they mark something: a pair where an avenue reaches its place and a pair at each bridge's apron (18).

    import hub_ground as G
    G.export_terrain(); G.write_placements(spots); G.write_pastures()   # src/worldbuild/Terrain, Placements/Yggdrasil.lua, Pastures.lua
    objs = G.paving(coll, bands)                                       # the paving meshes (hub_district_stages.export)
"""
import math
import os
import random

import worldlib as W
import ygg_island as Y
import hub_celestial as H

TAU = 2 * math.pi
LIFT = 0.25                    # the paving's top over the levelled ground

RING = (80.0, 104.0)
LAPIS = (90.5, 93.5)
RING_ROAD = (216.0, 236.0)
ROAD_LAPIS = (225.2, 226.8)
PEN_R, PEN_BEARINGS, SPAWN_Z = 168.0, (60.0, 120.0, 180.0, -120.0, -60.0, 0.0), -48.0
PEN_AREAS = ("south-east ring", "south-west ring", "west ring", "north-west ring", "north-east ring", "east ring")
PEN_PLOT = (62.0, 84.0)        # the level-9 pen with its paving ring (54 x 76) and 4 studs round it
PEN_FOOTPRINT = (54.0, 76.0)   # (Pastures.lua Footprint: what PastureBuilder checks)
SPUR_TO = PEN_R - 37.0         # the pen's paving ring's front edge
LEADERBOARD = (0.0, 118.0)     # faces south (+Z), down the south avenue to the Arrival Plaza
MERCHANT = (0.0, -120.0)       # faces north (-Z), up the north avenue to the bridges
SANCTUM = (0.0, -178.0)        # the Hatching Sanctum (GameConfig.HatchingAltar), its front (+Z) toward the tree
SPRING = (-147.2, 85.0)        # the Qi Spring, facing the tree
SPIN_WHEEL = (253.7, -14.6)    # the Spin Wheel (SpinWheelBuilder), where the owner stood (2026-11-16), outside the Ring Road east, facing the tree
ARRIVAL = (0.0, 176.0, 24.0)   # the Arrival Plaza: the hub's main spawn (IslandSpawn)
GUIDE_SPOT = (10.0, 162.0)
ROOT_HEAD = (0.0, 241.0)
SQUARE = Y.MARKET_SQUARE
AVENUES = [   # (name, bearing, half width, from r, to r): each runs from the Tree Ring's edge to the Ring Road's
    ("South", 90.0, 10.0, RING[1], RING_ROAD[0]),
    ("North", -90.0, 10.0, RING[1], RING_ROAD[0]),
    ("Market", -30.0, 10.0, RING[1], RING_ROAD[0]),
    ("SouthWest", 150.0, 8.0, RING[1], RING_ROAD[0]),
    ("NorthWest", -150.0, 8.0, RING[1], RING_ROAD[0]),
    ("SouthEast", 30.0, 8.0, RING[1], RING_ROAD[0]),
]
SPUR_HALF = 6.0
APRON_HALF = 20.0
FORECOURT_HALF = 7.0
# the model footprints the terrain is levelled under and kept bare (grass grows up through meshes): centre x, z, radius
MODEL_DISCS = [(LEADERBOARD[0], LEADERBOARD[1], 13.2), (MERCHANT[0], MERCHANT[1], 15.2), (SANCTUM[0], SANCTUM[1], 23.8),
               (SPRING[0], SPRING[1], 14.8), (SQUARE[0], SQUARE[1], 4.4)]
HRP_OVER_FEET = 3.192


def polar(b, r):
    return (math.cos(math.radians(b)) * r, math.sin(math.radians(b)) * r)


def face_yaw(fx, fz):
    """The yaw that turns a piece's local +Z toward (fx, fz) (Roblox CFrame.Angles(0, yaw, 0))."""
    return math.atan2(fx, fz)


def pens():
    """(index, bearing, centre (x, z), yaw turning the spot's -Z toward the tree, spawn (x, z))."""
    out = []
    for i, b in enumerate(PEN_BEARINGS):
        cx, cz = polar(b, PEN_R)
        sx, sz = polar(b, PEN_R + SPAWN_Z)
        out.append((i + 1, b, (cx, cz), math.radians(90.0 - b), (sx, sz)))
    return out


def shops():
    """name -> (centre x, z, width, depth, yaw turning its front (+Z) toward the Market Square)."""
    out = {}
    for name, (x, z, w, d) in Y.DISTRICT.items():
        out[name] = (x, z, w, d, face_yaw(SQUARE[0] - x, SQUARE[1] - z))
    return out


def bridges():
    """route -> (exit x, z, bearing)."""
    return {name: (x, z, math.degrees(math.atan2(z, x))) for name, (x, z) in Y.EXITS.items()}


# ---------- what is paved ----------
def discs():
    """(x, z, radius, inner radius) of every paved round."""
    return [(ARRIVAL[0], ARRIVAL[1], ARRIVAL[2], 0.0), (SQUARE[0], SQUARE[1], SQUARE[2], 4.15), (SPRING[0], SPRING[1], 24.0, 14.55)]


def segments():
    """(a, b, half width, kind) of every straight paved run."""
    out = []
    for name, b, half, r0, r1 in AVENUES:
        r1 = math.sqrt(r1 * r1 - half * half) - 0.05     # (its corners stop at the Ring Road's inner edge, not over its kerb)
        out.append((polar(b, r0), polar(b, r1), half, "avenue"))
    for _, b, _, _, (sx, sz) in pens():
        out.append((polar(b, RING[1]), polar(b, SPUR_TO + 0.5), SPUR_HALF, "path"))
    out.append(((0.0, RING_ROAD[1]), ROOT_HEAD, SPUR_HALF, "path"))
    a_ = polar(-30.0, RING_ROAD[1])
    dx_, dz_ = SQUARE[0] - a_[0], SQUARE[1] - a_[1]
    out.append((a_, (SQUARE[0] - dx_ / math.hypot(dx_, dz_) * 0.5, SQUARE[1] - dz_ / math.hypot(dx_, dz_) * 0.5), 10.0, "avenue"))
    for name, (x, z, b) in bridges().items():
        out.append((polar(b, RING_ROAD[1]), polar(b, math.hypot(x, z) + 0.5), APRON_HALF, "apron"))
    for name, (x, z, w, d, yaw) in shops().items():
        fx, fz = SQUARE[0] - x, SQUARE[1] - z
        L = math.hypot(fx, fz)
        ux, uz = fx / L, fz / L
        door = (x + ux * (d / 2 - 0.3), z + uz * (d / 2 - 0.3))
        edge = (SQUARE[0] - ux * (SQUARE[2] - 1.0), SQUARE[1] - uz * (SQUARE[2] - 1.0))
        out.append((edge, door, FORECOURT_HALF, "path"))
    return out


def _seg(px, pz, a, b):
    vx, vz = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * vx + (pz - a[1]) * vz) / max(vx * vx + vz * vz, 1e-9)))
    return math.hypot(px - a[0] - vx * t, pz - a[1] - vz * t)


def _rect(px, pz, cx, cz, w, d, yaw):
    """Signed distance outside a rectangle (w along local x, d along local z) turned by yaw."""
    dx, dz = px - cx, pz - cz
    lx = dx * math.cos(yaw) - dz * math.sin(yaw)
    lz = dx * math.sin(yaw) + dz * math.cos(yaw)
    qx, qz = abs(lx) - w / 2, abs(lz) - d / 2
    return math.hypot(max(qx, 0), max(qz, 0)) + min(max(qx, qz), 0)


def paved_distance(x, z):
    """How far (x, z) lies outside the paving and the models' footprints (negative on them)."""
    r = math.hypot(x, z)
    best = abs(r - (RING[0] + RING[1]) / 2) - (RING[1] - RING[0]) / 2
    best = min(best, abs(r - (RING_ROAD[0] + RING_ROAD[1]) / 2) - (RING_ROAD[1] - RING_ROAD[0]) / 2)
    for cx, cz, R, _ in discs():
        best = min(best, math.hypot(x - cx, z - cz) - R)
    for cx, cz, R in MODEL_DISCS:
        best = min(best, math.hypot(x - cx, z - cz) - R)
    for a, b, half, _ in segments():
        best = min(best, _seg(x, z, a, b) - half)
    for _, _, _, _, (sx, sz) in pens():
        best = min(best, math.hypot(x - sx, z - sz) - 6.2)
    for name, (cx, cz, w, d, yaw) in shops().items():
        best = min(best, _rect(x, z, cx, cz, w + 1.0, d + 1.0, yaw))
    return best


def pen_distance(x, z):
    best = 1e9
    for _, b, (cx, cz), yaw, _ in pens():
        best = min(best, _rect(x, z, cx, cz, PEN_PLOT[0], PEN_PLOT[1], -yaw))
    return best


# ---------- the terrain ----------
def height(x, z):
    from worldlib import fbm, smoothstep
    r = math.hypot(x, z)
    R = Y.rim(math.atan2(z, x))
    if r > R:
        return None, None
    # a gentle lawn: soft swells away from the paving and the pens, level under and round them
    h = 0.55 * fbm(x / 60 + 2, z / 60 - 6, seed=81, octaves=4) + 0.2 * fbm(x / 19, z / 19, seed=83, octaves=3)
    d = paved_distance(x, z)
    level = min(smoothstep(0.0, 10.0, d), smoothstep(0.0, 8.0, pen_distance(x, z)))
    h *= level
    # the World Tree's root mound, as it was (its roots are shaped to it)
    w = 1 - smoothstep(Y.MOUND[0], Y.MOUND[1], r)
    h = h * (1 - w) + Y.MOUND[2] * w ** 0.8
    # the rim rounds off to the cliff (never under the paving: it stays dead level)
    h -= 3.2 * (1 - smoothstep(R - 1, R - 11, r)) ** 1.6 * smoothstep(0.0, 3.0, d)
    if d < 0.6:
        mat = "Cobblestone"   # pale stone under the marble and under every model (grass grows up through a mesh)
    else:
        mat = "Grass"
    return h, mat


def ground(x, z):
    return height(x, z)[0] or 0.0


def export_terrain(path=None):
    path = path or W.REPO + "/src/worldbuild/Terrain/Yggdrasil.lua"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return W.export_heightfield(Y.NAME, Y.CENTRE, 4, 396, height, Y.MATERIALS, path, priority=[("Cobblestone", 4), ("Ground", 2)], turns=Y.TURNS)


# ---------- the paving ----------
# Every flagstone is a shallow prism (its top and its four sides down into the grout bed), so each one touches what is under it.
STONE_DEPTH = 0.14


def _o(mb, pts, want, band, shade=0.85):
    H.W_oriented(mb, pts, want, band, shade)


def stone(mb, band, top, shade, depth=STONE_DEPTH):
    """A flagstone: top is its 4 top corners (Roblox points); its sides go down `depth`."""
    _o(mb, top, (0, 1, 0), band, shade)
    cx = sum(p[0] for p in top) / 4
    cz = sum(p[2] for p in top) / 4
    for k in range(4):
        a, b = top[k], top[(k + 1) % 4]
        n = ((a[0] + b[0]) / 2 - cx, 0, (a[2] + b[2]) / 2 - cz)
        _o(mb, [a, b, (b[0], b[1] - depth, b[2]), (a[0], a[1] - depth, a[2])], n, band, shade * 0.75)


def _y(x, z, dy=0.0):
    return ground(x, z) + LIFT + dy


def ring_courses(mb, glow, rnd, bands, centre, r0, r1, lapis=None, rune_every=None, kerb_out=True, kerb_in=False, b0=0.0, b1=360.0, gap=None,
                 grout=-0.06):
    """Concentric courses of marble flagstones round centre from r0 to r1 (between bearings b0 and b1), a grout bed under them, an
    optional lapis band edged in gold with rune glyphs, gold kerbs. gap(x, z) -> True skips a stone (another paving owns it)."""
    cx, cz = centre
    a0, a1 = math.radians(b0), math.radians(b1)

    def at(a, r, dy=0.0):
        x, z = cx + math.cos(a) * r, cz + math.sin(a) * r
        return (x, _y(x, z, dy), z)
    seg = max(12, int((a1 - a0) * r1 / 4.5))
    for k in range(seg):   # the grout bed, in pieces no longer than about 4.5 studs
        g0, g1 = a0 + (a1 - a0) * k / seg, a0 + (a1 - a0) * (k + 1) / seg
        steps = max(1, int((r1 - max(r0, 0.0)) / 4.5))
        for j in range(steps):
            ra = max(r0, 0.01) + (r1 - max(r0, 0.01)) * j / steps
            rb = max(r0, 0.01) + (r1 - max(r0, 0.01)) * (j + 1) / steps
            q = [at(g0, rb, grout), at(g1, rb, grout), at(g1, ra, grout), at(g0, ra, grout)]
            if gap and gap(q):
                continue
            _o(mb, q, (0, 1, 0), bands[H.SHADE], 0.35)
    r = r0 + (0.7 if kerb_in else 0.0)
    k = 0
    while r < r1 - (0.8 if kerb_out else 0.1):
        w = 3.0
        if lapis and r < lapis[1] + 0.3 and r + w > lapis[0] - 0.3:
            r = lapis[1] + 0.3
            continue
        top = min(r + w, r1 - (0.75 if kerb_out else 0.1))
        if lapis and r < lapis[0] - 0.3 < top:
            top = lapis[0] - 0.3
        n = max(6, int((a1 - a0) * (r + top) / 2 / 4.4))
        ph = rnd.uniform(0, 1.0)
        for i in range(n):
            t0, t1 = (i + ph * (k % 2)) / n, (i + 1 + ph * (k % 2)) / n
            if t1 > 1.0:
                continue
            g0, g1 = a0 + (a1 - a0) * t0 + 0.05 / max(r, 1), a0 + (a1 - a0) * t1 - 0.05 / max(r, 1)
            q = [at(g0, top - 0.06), at(g1, top - 0.06), at(g1, r + 0.06), at(g0, r + 0.06)]
            if gap and gap(q):
                continue
            band = bands[H.MARBLE] if (i + k) % 5 else bands[H.MARBLE2]
            stone(mb, band, q, 0.6 + 0.35 * ((i * 7 + k * 3) % 5) / 4)
        r = top
        k += 1
    if lapis:
        segl = max(12, int((a1 - a0) * lapis[1] / 4.4))
        for k2 in range(segl):
            g0, g1 = a0 + (a1 - a0) * k2 / segl, a0 + (a1 - a0) * (k2 + 1) / segl
            if gap and gap([at(g0, lapis[1] + 0.3), at(g1, lapis[1] + 0.3), at(g1, lapis[0] - 0.3), at(g0, lapis[0] - 0.3)]):
                continue
            stone(mb, bands[H.LAPIS], [at(g0, lapis[1] - 0.03, -0.02), at(g1, lapis[1] - 0.03, -0.02), at(g1, lapis[0] + 0.03, -0.02),
                                       at(g0, lapis[0] + 0.03, -0.02)], 0.75)
            for (ra, rb) in ((lapis[0] - 0.3, lapis[0]), (lapis[1], lapis[1] + 0.3)):
                stone(mb, bands[H.GOLD], [at(g0, rb, 0.01), at(g1, rb, 0.01), at(g1, ra, 0.01), at(g0, ra, 0.01)], 0.95, depth=0.17)
            if rune_every and k2 % rune_every == 0:
                rune(glow, bands, at((g0 + g1) / 2, (lapis[0] + lapis[1]) / 2, -0.02), (g0 + g1) / 2, k2)
    for flag, rr, sign in ((kerb_out, r1, 1), (kerb_in, r0, -1)):
        if not flag or rr <= 0:
            continue
        segk = max(12, int((a1 - a0) * rr / 4.4))
        for k2 in range(segk):
            g0, g1 = a0 + (a1 - a0) * k2 / segk, a0 + (a1 - a0) * (k2 + 1) / segk
            ra, rb = (rr - 0.7, rr) if sign > 0 else (rr, rr + 0.7)
            if gap and gap([at(g0, rb), at(g1, rb), at(g1, ra), at(g0, ra)]):
                continue
            stone(mb, bands[H.GOLD], [at(g0, rb, 0.12), at(g1, rb, 0.12), at(g1, ra, 0.12), at(g0, ra, 0.12)], 0.9, depth=1.1)


def rune(glow, bands, p, a, k):
    """A rune glyph set in the lapis: a diamond, or two bars."""
    x, y, z = p
    ca, sa = math.cos(a), math.sin(a)       # (a: the bearing along the band; the glyph lies across it)
    tx, tz = -sa, ca
    if k % 2 == 0:
        top = [(x + ca * 0.55, y + 0.05, z + sa * 0.55), (x + tx * 0.85, y + 0.05, z + tz * 0.85), (x - ca * 0.55, y + 0.05, z - sa * 0.55),
               (x - tx * 0.85, y + 0.05, z - tz * 0.85)]
        stone(glow, bands[H.GLOW], top, 1.0, depth=0.12)
    else:
        for o in (-0.3, 0.3):
            bxp, bzp = x + tx * o, z + tz * o
            top = [(bxp + ca * 0.5 + tx * 0.1, y + 0.05, bzp + sa * 0.5 + tz * 0.1), (bxp + ca * 0.5 - tx * 0.1, y + 0.05, bzp + sa * 0.5 - tz * 0.1),
                   (bxp - ca * 0.5 - tx * 0.1, y + 0.05, bzp - sa * 0.5 - tz * 0.1), (bxp - ca * 0.5 + tx * 0.1, y + 0.05, bzp - sa * 0.5 + tz * 0.1)]
            stone(glow, bands[H.GLOW], top, 1.0, depth=0.12)


def _outside_intervals(a, ux, uz, L, circles):
    """The parts [t0, t1] of the line a + u t (0 <= t <= L) outside every circle (cx, cz, R)."""
    cuts = [(0.0, L)]
    for cx, cz, R in circles:
        fx, fz = a[0] - cx, a[1] - cz
        bq = fx * ux + fz * uz
        cq = fx * fx + fz * fz - R * R
        disc = bq * bq - cq
        if disc <= 0:
            continue
        t1, t2 = -bq - math.sqrt(disc), -bq + math.sqrt(disc)
        nxt = []
        for s0, s1 in cuts:
            if t2 <= s0 or t1 >= s1:
                nxt.append((s0, s1))
                continue
            if t1 > s0:
                nxt.append((s0, t1))
            if t2 < s1:
                nxt.append((t2, s1))
        cuts = nxt
    return [(s0, s1) for s0, s1 in cuts if s1 - s0 > 0.3]


def strip(mb, glow, bands, a, b, half, kind, circles=(), rnd=None, grout=-0.08):
    """A straight paved run from a to b, half wide: rows of slabs either side of a lapis channel with runes (an avenue), plain
    slabs (a path), or broad slabs (a bridge's apron); gold kerbs along both edges."""
    rnd = rnd or random.Random(int(abs(a[0] * 7 + a[1] * 3 + b[0])))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz, ux

    def at(t, s, dy=0.0):
        x, z = a[0] + ux * t + nx * s, a[1] + uz * t + nz * s
        return (x, _y(x, z, dy), z)
    if kind == "avenue":
        lanes = [(-half + 0.75, -1.0), (1.0, half - 0.75)]
    else:
        lanes = [(-half + 0.75, half - 0.75)]
    pieces = []
    for s0, s1 in _outside_intervals(a, ux, uz, L, circles):
        n = max(1, round((s1 - s0) / 4.2))
        pieces += [(s0 + (s1 - s0) * j / n, s0 + (s1 - s0) * (j + 1) / n) for j in range(n)]
    for i, (t0, t1) in enumerate(pieces):
        # the grout bed, the slabs, the channel, the kerbs
        for s0 in [-half + j * 4.5 for j in range(int(math.ceil(2 * half / 4.5)))]:
            s1 = min(s0 + 4.5, half)
            _o(mb, [at(t0, s0, grout), at(t1, s0, grout), at(t1, s1, grout), at(t0, s1, grout)], (0, 1, 0), bands[H.SHADE], 0.35)
        for l0, l1 in lanes:
            width = l1 - l0
            cols = max(1, round(width / (4.2 if kind == "apron" else 3.2)))
            off = rnd.uniform(-0.6, 0.6) if i % 2 else 0.0
            edges = [l0] + [l0 + width * (c + 0.5 + off / width) / cols for c in range(cols - 1)] + [l1]
            for c, (e0, e1) in enumerate(zip(edges, edges[1:])):
                band = bands[H.MARBLE] if (i + c) % 4 else bands[H.MARBLE2]
                stone(mb, band, [at(t0 + 0.06, e0 + 0.06), at(t1 - 0.06, e0 + 0.06), at(t1 - 0.06, e1 - 0.06), at(t0 + 0.06, e1 - 0.06)],
                      rnd.uniform(0.62, 0.95))
        if kind == "avenue":
            stone(mb, bands[H.LAPIS], [at(t0, -0.95, -0.02), at(t1, -0.95, -0.02), at(t1, 0.95, -0.02), at(t0, 0.95, -0.02)], 0.72)  # (between the slabs, not touching)
            if i % 2 == 0:
                rune(glow, bands, at((t0 + t1) / 2, 0.0, -0.02), math.atan2(uz, ux) + math.pi / 2, i // 2)
        for sgn in (-1, 1):
            e0, e1 = (half - 0.7, half) if sgn > 0 else (-half, -half + 0.7)
            stone(mb, bands[H.GOLD], [at(t0, e0, 0.12), at(t1, e0, 0.12), at(t1, e1, 0.12), at(t0, e1, 0.12)], 0.9, depth=1.1)


def _on_ring(x, z, ring, pad=0.0):
    r = math.hypot(x, z)
    return ring[0] - pad < r < ring[1] + pad


def _in_any_disc(x, z, pad=0.0):
    for cx, cz, R, _ in discs():
        if math.hypot(x - cx, z - cz) < R + pad:
            return True
    for cx, cz, R in MODEL_DISCS:
        if math.hypot(x - cx, z - cz) < R + pad:
            return True
    for _, _, _, _, (sx, sz) in pens():
        if math.hypot(x - sx, z - sz) < 6.2 + pad:
            return True
    return False


def paving(coll, mat, bands):
    """HB_RingPlaza, HB_RingRoadNE/SE/SW/NW (each under Roblox's 20,000 triangles a mesh), HB_Plazas, HB_Avenues and HB_PavingRunes
    (the glow), in island coordinates. Returns the raw objects (hub_district.finish splits them by material)."""
    rnd = random.Random(2026)
    glow = W.MeshBuilder()
    out = []
    mb = W.MeshBuilder()
    # the Tree Ring: where the avenues and spurs meet it, it stays whole (they stop at its edge)
    ring_courses(mb, glow, rnd, bands, (0.0, 0.0), RING[0], RING[1], lapis=LAPIS, rune_every=2, kerb_in=True)
    out.append(mb.object("HB_RingPlaza", coll, mat))
    # the Ring Road, in four quarters; the Market Square owns where it crosses
    def sq(pts):
        return any(math.hypot(p[0] - SQUARE[0], p[2] - SQUARE[1]) < SQUARE[2] + 0.05 for p in pts)
    for name, b0, b1 in (("HB_RingRoadNE", -90.0, 0.0), ("HB_RingRoadSE", 0.0, 90.0), ("HB_RingRoadSW", 90.0, 180.0), ("HB_RingRoadNW", 180.0, 270.0)):
        mb = W.MeshBuilder()
        ring_courses(mb, glow, rnd, bands, (0.0, 0.0), RING_ROAD[0], RING_ROAD[1], lapis=ROAD_LAPIS, rune_every=6, kerb_in=True,
                     b0=b0, b1=b1, gap=sq)
        out.append(mb.object(name, coll, mat))
    # the plazas: the Arrival Plaza, the Market Square (round its centrepiece), the Qi Spring's court (round its plinth)
    mb = W.MeshBuilder()
    for cx, cz, R, inner in discs():
        lap = (R - 5.0, R - 3.4) if R >= 24 else None
        ring_courses(mb, glow, rnd, bands, (cx, cz), inner, R, lapis=lap, rune_every=3, kerb_in=inner > 0, grout=-0.07)
    out.append(mb.object("HB_Plazas", coll, mat))
    # the avenues, the spurs, the root stair, the aprons and the forecourts: each stops where a ring, a plaza or a model owns the ground
    mb = W.MeshBuilder()

    circles = [(cx, cz, R) for cx, cz, R, _ in discs()] + list(MODEL_DISCS) + [(sx, sz, 6.2) for _, _, _, _, (sx, sz) in pens()]
    for a, b, half, kind in segments():
        if kind == "apron":
            continue
        strip(mb, glow, bands, a, b, half, kind, circles=circles, grout=-0.08)
    out.append(mb.object("HB_Avenues", coll, mat))
    mb = W.MeshBuilder()
    for a, b, half, kind in segments():
        if kind == "apron":
            strip(mb, glow, bands, a, b, half, kind, circles=circles, grout=-0.09)
    out.append(mb.object("HB_Aprons", coll, mat))
    out.append(glow.object("HB_PavingRunes", coll, mat))
    return out


PAVING = ("HB_RingPlaza", "HB_RingRoadNE", "HB_RingRoadSE", "HB_RingRoadSW", "HB_RingRoadNW", "HB_Plazas", "HB_Avenues", "HB_Aprons", "HB_PavingRunes")


# ---------- the parapet along the Ring Road over the great root's cove ----------
PARAPET = (56.0, 86.0, RING_ROAD[1] + 0.9)    # from bearing, to bearing, radius


def parapet(coll, mat, bands):
    """HB_RingParapet: a marble balustrade along the Ring Road's outer edge where the rim comes close (the root's cove): posts every
    3 studs, a rail, gold caps on the posts that end it."""
    mb = W.MeshBuilder()
    b0, b1, r = PARAPET
    n = int(math.radians(b1 - b0) * r / 4.5)
    for k in range(n + 1):
        a = math.radians(b0 + (b1 - b0) * k / n)
        x, z = math.cos(a) * r, math.sin(a) * r
        y = _y(x, z)
        mb.box((x, y + 1.0, z), (0.7, 2.4, 0.7), bands[H.MARBLE], yaw=-a, u=0.5, top_shade=0.95, side_shade=0.75)
    pts = []
    for k in range(n * 3 + 1):
        a = math.radians(b0 + (b1 - b0) * k / (n * 3))
        x, z = math.cos(a) * r, math.sin(a) * r
        pts.append((x, _y(x, z) + 2.35, z))
    for p, q in zip(pts, pts[1:]):
        L = math.hypot(q[0] - p[0], q[2] - p[2])
        mb.box(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2), (0.55, 0.32, L + 0.02), bands[H.MARBLE],
               yaw=math.atan2(q[0] - p[0], q[2] - p[2]), u=0.5, top_shade=0.95, side_shade=0.75)
    for a in (math.radians(b0), math.radians(b1)):
        x, z = math.cos(a) * r, math.sin(a) * r
        y = _y(x, z)
        mb.box((x, y + 1.2, z), (1.3, 3.0, 1.3), bands[H.MARBLE], yaw=-a, u=0.5, top_shade=0.95, side_shade=0.75)
        mb.box((x, y + 2.78, z), (1.5, 0.2, 1.5), bands[H.GOLD], yaw=-a, u=0.5, top_shade=1.0, side_shade=0.85)
    return mb.object("HB_RingParapet", coll, mat)


# ---------- the lamps ----------
def lamp_layout():
    """(x, z, yaw) of every lamp: a pair where an avenue reaches its place, and a pair at each bridge's apron."""
    spots = []

    def pair(b, r, half):
        for side in (-1, 1):
            cx, cz = polar(b, r)
            nx, nz = -math.sin(math.radians(b)), math.cos(math.radians(b))
            x, z = cx + nx * side * (half + 2.2), cz + nz * side * (half + 2.2)
            spots.append((x, z, face_yaw(-x, -z)))
    pair(-90.0, SANCTUM[1] * -1 - 23.8 - 4.0, 10.0)          # the north avenue reaching the Sanctum
    pair(90.0, ARRIVAL[1] - ARRIVAL[2] - 4.0, 10.0)           # the south avenue reaching the Arrival Plaza
    pair(150.0, math.hypot(*SPRING) - 24.0 - 4.0, 8.0)        # the south-west avenue reaching the Qi Spring's court
    pair(-30.0, RING_ROAD[0] - 5.0, 10.0)                     # the Market Avenue, where it crosses to the square
    for name, (x, z, b) in bridges().items():
        pair(b, RING_ROAD[1] + 3.5, APRON_HALF)               # each bridge's apron, on the verge past the Ring Road
    return spots


# ---------- placements (staged for phase 3) ----------
def _lua_v3(x, y, z):
    return "Vector3.new(%.2f, %.2f, %.2f)" % (x, y, z)


def write_placements(spots, path=None):
    """src/worldbuild/Placements/Yggdrasil.lua. `spots`: hub_district.build()'s second result (each asset's signs, faces and spots)."""
    import re
    import hub_district as D
    path = path or W.REPO + "/src/worldbuild/Placements/Yggdrasil.lua"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = open(W.REPO + "/src/worldbuild/Placements/Yggdrasil.lua").read()
    keep = {}
    for name in ("SI_RootShelf", "SI_CradleFloor"):
        m = re.search(r"        %s = \{\n(.*?)\n        \}," % name, old, re.S)
        keep[name] = m.group(1)
    relic = re.search(r"    Relics = \{.*?\},", old).group(0)
    kit = {}

    def add(name, x, y, z, yaw=0.0):
        kit.setdefault(name, []).append((x, y, z, yaw))
    for name in PAVING + ("HB_RingParapet",):
        add(name, 0.0, 0.0, 0.0)
    for k, (x, z, yaw) in enumerate(lamp_layout()):
        add("HB_CrystalLamp", x, _y(x, z), z, yaw)
        add("HB_CrystalLampLight" if k % 2 == 0 else "HB_CrystalLampGlow", x, _y(x, z), z, yaw)
    for _, b, _, _, (sx, sz) in pens():
        yaw = face_yaw(math.cos(math.radians(b)), math.sin(math.radians(b)))     # facing its pen
        add("HB_SpawnPad", sx, ground(sx, sz), sz, yaw)
        add("HB_SpawnPadGlow", sx, ground(sx, sz), sz, yaw)
    add("HB_SquareCompass", SQUARE[0], ground(SQUARE[0], SQUARE[1]), SQUARE[1])
    add("HB_SquareCompassGlow", SQUARE[0], ground(SQUARE[0], SQUARE[1]), SQUARE[1])
    add("HB_SanctumPlinth", SANCTUM[0], LIFT, SANCTUM[1])
    sp_yaw = face_yaw(-SPRING[0], -SPRING[1])
    add("HB_SpringPlinth", SPRING[0], LIFT, SPRING[1], sp_yaw)
    add("HB_MerchantDais", MERCHANT[0], ground(*MERCHANT), MERCHANT[1], math.pi)
    add("HB_MerchantDaisGlow", MERCHANT[0], ground(*MERCHANT), MERCHANT[1], math.pi)
    L = ["-- Generated by tools/blender/world/hub_ground.py (the hub's redesign, 2026-11-15). Do not edit by hand.",
         "-- Island-local Roblox studs. Kit entries place each piece's authored origin. HB_* are the hub's (Yggdrasil_Celestial.fbx and",
         "-- Yggdrasil_District.fbx); SI_RootShelf / SI_CradleFloor are the great root's, kept from the hub before.", "return {", "    Kit = {"]
    for name in sorted(kit):
        L.append("        %s = {" % name)
        for x, y, z, yaw in kit[name]:
            L.append("            { Position = %s, Yaw = %.4f }," % (_lua_v3(x, y, z), yaw))
        L.append("        },")
    for name, body in keep.items():
        L += ["        %s = {" % name, body, "        },"]
    L.append("    },")
    L.append("    -- the shops' sites (the Merchants' Terrace): centre, size (width, depth) and the yaw that turns local +Z toward the Market Square")
    L.append("    Plots = {")
    for name, (x, z, w, d, yaw) in shops().items():
        L.append("        %s = { Centre = %s, Size = Vector2.new(%g, %g), Yaw = %.4f }," % (name, _lua_v3(x, ground(x, z), z), w, d, yaw))
    L.append("    },")
    L.append("    -- each shop's name board, where its prompt stands and its effects, in its site's frame (hub_district.py)")
    L.append("    Shops = {")
    shop_spots = {
        "Blacksmith": (spots["Blacksmith"]["Sign"], D.BS_SIGN_SIZE, D.BS_PROMPT,
                       [("Forge", D.BS_HEARTH), ("Smoke", (D.BS_TOWER[0], D.BS_TOWER[3] + 7.5, D.BS_TOWER[1]))]),
        "BuySell": (spots["BuySell"]["Sign"], D.BV_SIGN_SIZE, D.BV_PROMPT, [("Stones", (D.BV_DRUM[0] - D.BV_SCALE[0], D.BV_SCALE[2] + 1.0, D.BV_DRUM[1]))]),
        "Marketplace": (spots["Market"]["Sign"], D.MK_SIGN_SIZE, D.MK_PROMPT, [("Coins", D.MK_FX)]),
    }
    for name, (sc, ss, prompt, fx) in shop_spots.items():
        L.append("        %s = {" % name)
        L.append("            Sign = { Centre = Vector3.new(%g, %g, %g), Size = Vector2.new(%g, %g) }," % (sc[0], sc[1], sc[2], ss[0], ss[1]))
        L.append("            Prompt = Vector3.new(%g, %g, %g)," % prompt)
        L.append("            Fx = {")
        for kind, p in fx:
            L.append('                { Kind = "%s", Position = Vector3.new(%g, %g, %g) },' % (kind, p[0], p[1], p[2]))
        L.append("            },")
        L.append("        },")
    L.append("    },")
    L.append("    -- the hub's own spawn: the Arrival Plaza (for a player without a pen yet); each player's own spawn is before their pen")
    L.append("    Spawn = %s," % _lua_v3(ARRIVAL[0], _y(ARRIVAL[0], ARRIVAL[1]) + 1.98, ARRIVAL[1]))
    L.append("    -- the six pen spawn pads (HB_SpawnPad), in pen order: where each holder spawns, facing their pen (Pastures.lua Spawn)")
    L.append("    PenSpawns = {")
    for i, b, _, _, (sx, sz) in pens():
        L.append("        { Position = %s, Yaw = %.4f }," % (_lua_v3(sx, ground(sx, sz) + D.SP_TOP, sz), face_yaw(math.cos(math.radians(b)), math.sin(math.radians(b)))))
    L.append("    },")
    L.append("    -- the hub's people (hub_npcs.py): each one's HumanoidRootPart and the yaw that turns its face (-Z) where it looks")
    L.append("    Npcs = {")
    sh = shops()
    for npc, (site, (lx, ly, lz)) in (("Forgemaster", ("Blacksmith", D.BS_SMITH)), ("Curator", ("Marketplace", D.MK_CURATOR)),
                                     ("Appraiser", ("BuySell", D.BV_APPRAISER))):
        x, z, _, _, yaw = sh[site]
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        L.append("        %s = { Position = %s, Yaw = %.4f }," % (npc, _lua_v3(wx, ground(x, z) + ly + HRP_OVER_FEET, wz), yaw + math.pi))
    gx, gz = GUIDE_SPOT
    L.append("        Guide = { Position = %s, Yaw = %.4f }," % (_lua_v3(gx, _y(gx, gz) + HRP_OVER_FEET, gz), face_yaw(ARRIVAL[0] - gx, ARRIVAL[1] - gz) + math.pi))
    L.append("    },")
    L.append("    -- the Ascension Board (WorldBuilder.buildLeaderboard): at the head of the south avenue, facing the Arrival Plaza")
    L.append("    Leaderboard = { Centre = %s, Yaw = %.4f }," % (_lua_v3(LEADERBOARD[0], ground(*LEADERBOARD), LEADERBOARD[1]), face_yaw(0.0, 1.0)))
    L.append("    -- the Wandering Merchant's camp (MerchantService), on his dais (HB_MerchantDais, top %.2f over the ground), facing the bridges" % D.MD_TOP)
    L.append("    Merchant = { Centre = %s, Yaw = %.4f }," % (_lua_v3(MERCHANT[0], ground(*MERCHANT) + D.MD_TOP, MERCHANT[1]), face_yaw(0.0, -1.0)))
    L.append("    -- the Qi Spring (hub_celestial.qi_spring) on its new plinth, facing the tree; no channel or waterfall since the redesign")
    L.append("    QiSpring = { Centre = %s, Yaw = %.4f }," % (_lua_v3(SPRING[0], LIFT, SPRING[1]), sp_yaw))
    L.append("    -- the Spin Wheel (SpinWheelBuilder): its plinth's middle on the ground, outside the Ring Road east, facing the tree")
    L.append("    SpinWheel = { Centre = %s, Yaw = %.4f }," % (_lua_v3(SPIN_WHEEL[0], ground(*SPIN_WHEEL), SPIN_WHEEL[1]), face_yaw(-SPIN_WHEEL[0], -SPIN_WHEEL[1])))
    L.append("    " + relic.strip())
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return path


def write_pastures(path=None):
    """src/worldbuild/Placements/Pastures.lua: the pens on their ring, each with its spawn before it."""
    path = path or W.REPO + "/src/worldbuild/Placements/Pastures.lua"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = [
        "-- Generated by tools/blender/world/hub_ground.py (write_pastures; the hub's redesign, 2026-11-15). Do not edit by hand.",
        "-- The six beast pen spots on Yggdrasil: the ONE table of where pens stand, read by the builder (PastureBuilder: the paving ring, the",
        "-- gate, the board, the spawn) and by the server (PenService: each spot's area name and order; it gives players spots in this order).",
        "-- The pen's look and growth (shared/PenLayout, client/Pets/PenFence) are drawn in a spot's own frame.",
        "--   Area       what players are told (\"Your Beast Pasture: the south-east ring\")",
        "--   Centre     the spot's centre, island-local studs (the hub's ground is Y 0 here: the builder sets it on the terrain under it)",
        "--   Yaw        turns the spot's -Z (the pen's gate) toward the World Tree",
        "--   Footprint  the most ground the spot may use (X, Z studs): the largest pen level and its paving ring must fit (PastureBuilder checks)",
        "--   Spawn      where its holder spawns, spot-local, facing the pen: the pad 10 studs before the board's line (PastureBuilder puts a",
        "--              SpawnLocation there; PenService sets the holder's PenSpawn; WorldService spawns and returns them there)",
        "-- Six pens on a ring round the World Tree (r %g), clockwise from the south-east; players are given them in this order, so a small" % PEN_R,
        "-- server fills the two beside the Arrival Plaza first.",
    ]
    L = header + ["return {"]
    for (i, b, (cx, cz), yaw, _), area in zip(pens(), PEN_AREAS):
        L.append('    { Area = "%s", Centre = Vector3.new(%.2f, 0, %.2f), Yaw = %.4f, Footprint = Vector2.new(%g, %g), Spawn = Vector3.new(0, 0, %g) },'
                 % (area, cx, cz, yaw, PEN_FOOTPRINT[0], PEN_FOOTPRINT[1], SPAWN_Z))
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return path

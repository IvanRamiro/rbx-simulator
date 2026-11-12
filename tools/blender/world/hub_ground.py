"""The celestial hub's ground (the owner, 2026-11-12: everything but the World Tree rebuilt, "NO CHINESE"; style approved): where
everything stands, the terrain under it, its marble paving, and the placements WorldBuilder reads.

Layout, island-local studs (x east, z south; bearings from +x toward +z):
- a marble ring plaza round the tree's mound (r 80-104);
- five sites in a crescent round the south half, each on a round marble plaza facing the tree: the Hatching Sanctum (bearing 20),
  Buy & Sell (62), the Spawn (90), the Marketplace (118), the Blacksmith (148); a promenade arc joins them;
- an avenue out from the ring to each site and to each of the five bridges (bridgehead plazas where they land), and a path from the
  spawn to the great root;
- crystal lamps along every avenue and round the plazas, a few floating crystal clusters.

    import hub_ground as G
    G.export_terrain(); G.write_placements(); G.export()      # src/worldbuild/..., assets/world/Yggdrasil/Yggdrasil_Celestial.fbx
"""
import math
import random

import worldlib as W
import ygg_island as Y
import hub_celestial as H

TAU = 2 * math.pi
RING = (80.0, 104.0)
LAPIS = (90.5, 93.5)
SITES = {   # name: (bearing, radius from the island's centre, plaza radius, inner radius left unpaved under the building)
    "Hatching": (20.0, 152.0, 34.0, 18.5),
    "BuySell": (62.0, 152.0, 28.0, 0.0),
    "Spawn": (90.0, 140.0, 26.0, 0.0),
    "Marketplace": (118.0, 152.0, 26.0, 17.5),
    "Blacksmith": (148.0, 150.0, 26.0, 0.0),
    "QiSpring": (-10.0, 172.0, 24.0, 0.0),   # east of the tree, between the Origin bridge and the Sanctum (hub_celestial.qi_spring)
}
MERCHANT = (-88.5, 168.0)      # the Wandering Merchant's camp (bearing, radius): on the lawn between the Ember and Moonlit bridges'
                               # avenues, where everyone coming home from an island walks by (MerchantService)
CHANNEL_HALF = 1.5
MONUMENT = (104.0, 119.0, 9.0)  # the Ascension Board (hub_celestial.leaderboard): bearing, radius, its paved round's radius; beside
                                # the spawn plaza (left of an arriving player), facing the spawn; no avenue of its own
# the hub's people (tools/blender/npcs/hub_npcs.py): each keeper's spot in its building's frame (x, floor y, z, turn off facing
# the tree); the Guide's on the spawn plaza in island coordinates, facing whoever just arrived
NPC_SPOTS = {
    "Forgemaster": ("Blacksmith", (2.3, H.BS_FLOOR, -0.4), -0.25),      # beside the anvil, the hearth behind him
    "Curator": ("Marketplace", (4.8, 0.9, 3.0), 0.45),                 # by the great crystal egg, turned toward whoever comes in
    "Appraiser": ("BuySell", (2.4, 0.5, 7.2), 0.0),                    # behind the counter, before the vault door
}
GUIDE_SPOT = (7.0, 132.0)
HRP_OVER_FEET = 3.192             # the spring's overflow channel, out to the island's edge
BRIDGEHEAD_R = 24.0
AVENUE_HALF, BRIDGE_HALF, PATH_HALF = 6.0, 7.0, 4.0
LIFT = 0.25                    # the paving's top over the levelled ground


def polar(b, r):
    return (math.cos(math.radians(b)) * r, math.sin(math.radians(b)) * r)


def site_centre(name):
    b, r, _, _ = SITES[name]
    return polar(b, r)


def face_yaw(fx, fz):
    return math.atan2(fx, fz)


def bridgeheads():
    out = {}
    for name, (x, z) in Y.EXITS.items():
        r = math.hypot(x, z)
        out[name] = (x * (r - 10) / r, z * (r - 10) / r)
    return out


def discs():
    """(x, z, radius, inner radius) of every paved round: the sites and the bridgeheads."""
    out = []
    for name, (b, r, pr, inner) in SITES.items():
        x, z = polar(b, r)
        out.append((x, z, pr, inner))
    for x, z in bridgeheads().values():
        out.append((x, z, BRIDGEHEAD_R, 0.0))
    mx, mz = polar(MONUMENT[0], MONUMENT[1])
    out.append((mx, mz, MONUMENT[2], 0.0))
    return out


def roads():
    """(line, half width, kind) of every avenue and path."""
    out = []
    for name, (b, r, pr, _) in SITES.items():
        out.append(([polar(b, RING[1] - 1.0), polar(b, r - pr + 1.0)], AVENUE_HALF, "avenue"))
    for (x, z) in bridgeheads().values():
        b = math.degrees(math.atan2(z, x))
        r = math.hypot(x, z)
        out.append(([polar(b, RING[1] - 1.0), polar(b, r - BRIDGEHEAD_R + 1.0)], BRIDGE_HALF, "avenue"))
    sx, sz = site_centre("Spawn")
    out.append(([(sx, sz + SITES["Spawn"][2] - 1.0), (0.0, Y.ROOT_EXIT[1] - 8.0)], PATH_HALF, "path"))
    arc = [polar(20 + (148 - 20) * i / 32, 152.0) for i in range(33)]
    out.append((arc, PATH_HALF, "path"))
    return out


def channel_line():
    """The spring's overflow channel: from its basin's spout (local -Z, away from the tree) straight out to 1 stud short of the rim."""
    b, r, _, _ = SITES["QiSpring"]
    rim = Y.rim(math.radians(b))
    return [polar(b, r + H.QS_CURB_R - 0.2), polar(b, rim - 1.0)]


def _seg(px, pz, a, b):
    vx, vz = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((px - a[0]) * vx + (pz - a[1]) * vz) / max(vx * vx + vz * vz, 1e-9)))
    return math.hypot(px - a[0] - vx * t, pz - a[1] - vz * t)


def in_disc(x, z, pad=0.0):
    return any(math.hypot(x - cx, z - cz) < r + pad for cx, cz, r, _ in discs())


def paved_distance(x, z):
    """How far (x, z) lies outside the paving (negative on it)."""
    best = abs(math.hypot(x, z) - (RING[0] + RING[1]) / 2) - (RING[1] - RING[0]) / 2
    for cx, cz, r, _ in discs():
        best = min(best, math.hypot(x - cx, z - cz) - r)
    for line, half, _ in roads():
        for a, b in zip(line, line[1:]):
            best = min(best, _seg(x, z, a, b) - half)
    (ax, az), (bx, bz) = channel_line()
    best = min(best, _seg(x, z, (ax, az), (bx, bz)) - CHANNEL_HALF - 0.6)
    return best


# ---------- the terrain ----------
def height(x, z):
    from worldlib import fbm, smoothstep, gauss
    r = math.hypot(x, z)
    R = Y.rim(math.atan2(z, x))
    if r > R:
        return None, None
    h = 0.9 * fbm(x / 70 + 2, z / 70 - 6, seed=81, octaves=4) + 0.35 * fbm(x / 21, z / 21, seed=83, octaves=3)
    rocky = False
    for kx, kz, kr, kh in Y.KNOLLS:
        dome = gauss(x - kx, z - kz, kr * 0.5)
        h += kh * dome + 1.6 * dome * fbm(x / 8, z / 8, seed=85, octaves=3)
        rocky = rocky or dome > 0.5 and fbm(x / 11 + 5, z / 11, seed=87, octaves=3) > -0.05 + 0.4 * (1 - dome)
    # the World Tree's root mound, as it was (its roots are shaped to it)
    w = 1 - smoothstep(Y.MOUND[0], Y.MOUND[1], r)
    h = h * (1 - w) + Y.MOUND[2] * w ** 0.8
    # level under and round the paving, and bare earth under it (terrain grass grows up through a mesh)
    d = paved_distance(x, z)
    w = 1 - smoothstep(0.0, 9.0, d)
    h = h * (1 - w)
    h -= 3.2 * (1 - smoothstep(R - 1, R - 11, r)) ** 1.6
    mx, mz = polar(*MERCHANT)
    camp = math.hypot((x - mx) / 7.5, (z - mz - 1.5) / 6.0) + 0.12 * fbm(x / 3, z / 3, seed=91, octaves=2)
    if camp < 1.0:
        mat = "Ground"        # the Wandering Merchant's camp: worn bare (terrain grass grew up through his rug, seen in Play)
    elif d < 0.6:
        mat = "Cobblestone"   # pale stone under the marble: brown earth bled out round every edge (terrain blends over a 4-stud cell)
    elif rocky:
        mat = "Rock"
    else:
        mat = "Grass"
    return h, mat


def ground(x, z):
    return height(x, z)[0] or 0.0


def export_terrain(path=None):
    path = path or W.REPO + "/src/worldbuild/Terrain/Yggdrasil.lua"
    return W.export_heightfield(Y.NAME, Y.CENTRE, 4, 276, height, Y.MATERIALS, path, priority=[("Cobblestone", 4), ("Ground", 2)], turns=Y.TURNS)


# ---------- the paving ----------
def _o(mb, pts, want, band, shade=0.85):
    H.W_oriented(mb, pts, want, band, shade)


def courses(mb, rnd, bands, centre, r0, r1, lapis=None, kerb=True, inner_kerb=False):
    """Concentric courses of marble flagstones from r0 out to r1 round centre on the ground, dark grout under them, an optional
    lapis band (r, r) edged in gold, and a gold kerb with its outer face."""
    cx, cz = centre

    def at(a, r, dy=0.0):
        x, z = cx + math.cos(a) * r, cz + math.sin(a) * r
        return (x, ground(x, z) + LIFT + dy, z)
    seg = max(24, int(TAU * r1 / 4))
    for k in range(seg):    # the grout
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        _o(mb, [at(a0, r1, -0.03), at(a1, r1, -0.03), at(a1, max(r0, 0.01), -0.03), at(a0, max(r0, 0.01), -0.03)], (0, 1, 0), bands[H.SHADE], 0.35)
    r = r0 if r0 > 0 else 2.6
    if r0 <= 0:   # a round middle stone
        for k in range(12):
            a0, a1 = TAU * k / 12, TAU * (k + 1) / 12
            _o(mb, [at(0, 0, 0.0), at(a0, 2.5, 0.0), at(a1, 2.5, 0.0)], (0, 1, 0), bands[H.MARBLE], 0.9)
    k = 0
    while r < r1 - 0.8:
        w = 2.4
        if lapis and r < lapis[1] and r + w > lapis[0]:
            r = lapis[1]
            continue
        top = min(r + w, r1 - 0.7)
        n = max(10, int(TAU * r / 3.2))
        ph = rnd.uniform(0, TAU)
        for i in range(n):
            a0, a1 = ph + TAU * i / n + 0.05 / max(r, 1), ph + TAU * (i + 1) / n - 0.05 / max(r, 1)
            band = bands[H.MARBLE] if (i + k) % 5 else bands[H.MARBLE2]
            steps = max(1, int((a1 - a0) * r / 4))
            for s in range(steps):
                b0, b1 = a0 + (a1 - a0) * s / steps, a0 + (a1 - a0) * (s + 1) / steps
                _o(mb, [at(b0, top - 0.06), at(b1, top - 0.06), at(b1, r + 0.06), at(b0, r + 0.06)], (0, 1, 0), band, 0.6 + 0.35 * ((i * 7 + k * 3) % 5) / 4)
        r = top
        k += 1
    if lapis:
        for k2 in range(seg):
            a0, a1 = TAU * k2 / seg, TAU * (k2 + 1) / seg
            for (ra, rb, band, dy, sh) in ((lapis[0], lapis[1], H.LAPIS, 0.0, 0.75), (lapis[0] - 0.3, lapis[0], H.GOLD, 0.01, 0.95), (lapis[1], lapis[1] + 0.3, H.GOLD, 0.01, 0.95)):
                _o(mb, [at(a0, rb, dy), at(a1, rb, dy), at(a1, ra, dy), at(a0, ra, dy)], (0, 1, 0), bands[band], sh)
    if kerb:
        for k2 in range(seg):
            a0, a1 = TAU * k2 / seg, TAU * (k2 + 1) / seg
            mid = (a0 + a1) / 2
            _o(mb, [at(a0, r1, 0.12), at(a1, r1, 0.12), at(a1, r1 - 0.7, 0.12), at(a0, r1 - 0.7, 0.12)], (0, 1, 0), bands[H.GOLD], 0.9)
            o0, o1 = at(a0, r1, 0.12), at(a1, r1, 0.12)
            _o(mb, [o0, o1, (o1[0], o1[1] - 1.0, o1[2]), (o0[0], o0[1] - 1.0, o0[2])], (math.cos(mid), 0, math.sin(mid)), bands[H.SHADE], 0.6)
    if inner_kerb and r0 > 0:
        for k2 in range(seg):
            a0, a1 = TAU * k2 / seg, TAU * (k2 + 1) / seg
            mid = (a0 + a1) / 2
            _o(mb, [at(a0, r0 + 0.6, 0.12), at(a1, r0 + 0.6, 0.12), at(a1, r0, 0.12), at(a0, r0, 0.12)], (0, 1, 0), bands[H.GOLD], 0.9)
            i0, i1 = at(a0, r0, 0.12), at(a1, r0, 0.12)
            _o(mb, [i0, i1, (i1[0], i1[1] - 1.0, i1[2]), (i0[0], i0[1] - 1.0, i0[2])], (-math.cos(mid), 0, -math.sin(mid)), bands[H.SHADE], 0.6)


def avenue(mb, glow, bands, line, half, kind):
    """Marble slabs either side of a lapis channel (an avenue) or irregular slabs (a path), gold-edged, laid on the ground; rows
    on a plaza are left to it. glow: the channel's rune glyphs every 6 studs."""
    pts = []
    for a, b in zip(line, line[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, round(L / 3.0))
        for i in range(n + (1 if b is line[-1] else 0)):
            pts.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    rnd = random.Random(int(abs(line[0][0] * 7 + line[0][1] * 3)))

    def at(x, z, nx, nz, s, dy=0.0):
        px, pz = x + nx * s, z + nz * s
        return (px, ground(px, pz) + LIFT + dy, pz)
    run = 0.0
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        dx, dz = q[0] - p[0], q[1] - p[1]
        L = max(math.hypot(dx, dz), 1e-6)
        nx, nz = -dz / L, dx / L
        mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        run += L
        if in_disc(mx, mz, -0.5) or abs(math.hypot(mx, mz) - (RING[0] + RING[1]) / 2) < (RING[1] - RING[0]) / 2 - 0.5:
            continue
        P0, P1 = (p[0], p[1], nx, nz), (q[0], q[1], nx, nz)
        def quad(s0, s1, band, dy=0.0, sh=0.85):
            _o(mb, [at(*P0, s0, dy), at(*P1, s0, dy), at(*P1, s1, dy), at(*P0, s1, dy)], (0, 1, 0), bands[band], sh)
        quad(-half, half, H.SHADE, -0.03, 0.35)                       # grout
        if kind == "avenue":
            for side in (-1, 1):
                quad(side * 0.9, side * (half / 2), H.MARBLE if i % 4 else H.MARBLE2, 0.0, rnd.uniform(0.65, 0.95))
                quad(side * (half / 2 + 0.1), side * (half - 0.75), H.MARBLE, 0.0, rnd.uniform(0.65, 0.95))
            quad(-0.8, 0.8, H.LAPIS, -0.01, 0.7)
            if i % 2 == 0:
                cx_, cz_ = mx, mz
                y = ground(cx_, cz_) + LIFT + 0.01
                _o(glow, [(cx_ + dx / L * 0.9, y, cz_ + dz / L * 0.9), (cx_ + nx * 0.45, y, cz_ + nz * 0.45), (cx_ - dx / L * 0.9, y, cz_ - dz / L * 0.9),
                          (cx_ - nx * 0.45, y, cz_ - nz * 0.45)], (0, 1, 0), bands[H.GLOW], 1.0)
        else:
            cuts = sorted(rnd.uniform(-half * 0.5, half * 0.5) for _ in range(rnd.choice((1, 2))))
            edges = [-(half - 0.7)] + cuts + [half - 0.7]
            for s0, s1 in zip(edges, edges[1:]):
                quad(s0 + 0.06, s1 - 0.06, H.MARBLE, 0.0, rnd.uniform(0.6, 0.92))
        for side in (-1, 1):   # the gold edge and its face
            quad(side * (half - 0.7), side * half, H.GOLD, 0.1, 0.9)
            o0, o1 = at(*P0, side * half, 0.1), at(*P1, side * half, 0.1)
            _o(mb, [o0, o1, (o1[0], o1[1] - 1.0, o1[2]), (o0[0], o0[1] - 1.0, o0[2])], (nx * side, 0, nz * side), bands[H.SHADE], 0.6)


def runes(glow, bands, centre, r, count):
    """Rune glyphs set in a lapis band: a diamond, then two bars."""
    cx, cz = centre
    for k in range(count):
        a = TAU * k / count
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa, ca
        x, z = cx + ca * r, cz + sa * r
        y = ground(x, z) + LIFT + 0.02
        if k % 3 == 0:
            pts = [(x + ca * 0.9, y, z + sa * 0.9), (x + tx * 0.6, y, z + tz * 0.6), (x - ca * 0.9, y, z - sa * 0.9), (x - tx * 0.6, y, z - tz * 0.6)]
        else:
            pts = [(x + tx * 0.18 + ca * 0.8, y, z + tz * 0.18 + sa * 0.8), (x - tx * 0.18 + ca * 0.8, y, z - tz * 0.18 + sa * 0.8),
                   (x - tx * 0.18 - ca * 0.8, y, z - tz * 0.18 - sa * 0.8), (x + tx * 0.18 - ca * 0.8, y, z + tz * 0.18 - sa * 0.8)]
        _o(glow, pts, (0, 1, 0), bands[H.GLOW], 1.0)


def paving(coll, mat, bands):
    """HB_RingPlaza, HB_Plazas, HB_Avenues (each under Roblox's 20,000 triangles a mesh) and HB_PavingRunes (glow)."""
    rnd = random.Random(2026)
    glow = W.MeshBuilder()
    mb = W.MeshBuilder()
    courses(mb, rnd, bands, (0.0, 0.0), RING[0], RING[1], lapis=LAPIS, inner_kerb=True)
    runes(glow, bands, (0.0, 0.0), (LAPIS[0] + LAPIS[1]) / 2, 72)
    ring_obj = mb.object("HB_RingPlaza", coll, mat)
    mb = W.MeshBuilder()
    for cx, cz, r, inner in discs():
        lap = (r - 5.5, r - 3.5) if r >= 24 else None
        courses(mb, rnd, bands, (cx, cz), inner, r, lapis=lap)
        if lap:
            runes(glow, bands, (cx, cz), (lap[0] + lap[1]) / 2, int(TAU * r / 4.5))
    plazas = mb.object("HB_Plazas", coll, mat)
    mb = W.MeshBuilder()
    for line, half, kind in roads():
        avenue(mb, glow, bands, line, half, kind)
    avenues = mb.object("HB_Avenues", coll, mat)
    return [ring_obj, plazas, avenues, glow.object("HB_PavingRunes", coll, mat)]


# ---------- the lamps and the floating clusters ----------
CLUSTER_Y = 9.5


def cluster_mount(coll, mat, bands):
    mb = W.MeshBuilder()
    H.cluster_mount(mb, (0.0, CLUSTER_Y, 0.0), 5.2, bands[H.GOLD])
    return mb.object("HB_Cluster", coll, mat)


def cluster_glow(coll, mat, bands):
    mb = W.MeshBuilder()
    H.crystal_cluster(mb, (0.0, CLUSTER_Y, 0.0), 5.2, bands[H.GLOW])
    return mb.object("HB_ClusterGlow", coll, mat)


def lamp_light(coll, mat, bands):
    o = H.crystal_lamp_glow(coll, mat, bands)
    o.name = o.data.name = "HB_CrystalLampLight"
    return o


def lamp_layout():
    """(x, z, yaw) of every lamp: one pair per avenue, flanking it where it reaches its building or bridge (a gateway, not a
    fence). 73 lamps along the avenues, round the ring and round every plaza were far too many (the owner, 2026-11-12)."""
    spots = []
    for line, half, kind in roads():
        if kind != "avenue":
            continue
        (ax, az), (bx, bz) = line[0], line[-1]
        L = math.hypot(bx - ax, bz - az)
        dx, dz = (bx - ax) / L, (bz - az) / L
        d = L - 5.0
        for side in (-1, 1):
            x, z = ax + dx * d - dz * side * (half + 2.2), az + dz * d + dx * side * (half + 2.2)
            if paved_distance(x, z) >= 0.8 and math.hypot(x, z) <= 236:
                spots.append((x, z, face_yaw(-x, -z)))
    return spots


def spring_channel(coll, mat, bands):
    """HB_SpringChannel, in island coordinates: a marble channel with gold-capped walls carrying the spring's overflow to the edge,
    its bed stepping down with the ground (never up), the water in it see-through. Returns (object, the lip where it pours off)."""
    (ax, az), (bx, bz) = channel_line()
    L = math.hypot(bx - ax, bz - az)
    dx, dz = (bx - ax) / L, (bz - az) / L
    px, pz = -dz, dx
    n = max(2, int(L / 2.0))
    mb = W.MeshBuilder()
    bed = None
    pts = []
    for i in range(n + 1):
        x, z = ax + dx * L * i / n, az + dz * L * i / n
        g = ground(x, z) + LIFT
        bed = g if bed is None else min(bed, g)
        pts.append((x, bed, z))
    w_in, w_out, wall_h = CHANNEL_HALF - 0.45, CHANNEL_HALF, 0.75
    for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
        # the bed (under the water) and the two walls with their gold caps
        q = lambda x, y, z, s_: (x + px * s_, y, z + pz * s_)
        H.W_oriented(mb, [q(x0, y0, z0, -w_in), q(x0, y0, z0, w_in), q(x1, y1, z1, w_in), q(x1, y1, z1, -w_in)], (0, 1, 0), bands[H.LAPIS], 0.7)
        for side in (-1, 1):
            a_, b_ = side * w_in, side * w_out
            top0, top1 = y0 + wall_h, y1 + wall_h
            H.W_oriented(mb, [q(x0, top0, z0, a_), q(x0, top0, z0, b_), q(x1, top1, z1, b_), q(x1, top1, z1, a_)], (0, 1, 0), bands[H.GOLD], 1.0)
            H.W_oriented(mb, [q(x0, y0, z0, a_), q(x1, y1, z1, a_), q(x1, top1, z1, a_), q(x0, top0, z0, a_)], (-px * side, 0, -pz * side), bands[H.MARBLE], 0.8)
            H.W_oriented(mb, [q(x0, y0 - 0.6, z0, b_), q(x1, y1 - 0.6, z1, b_), q(x1, top1, z1, b_), q(x0, top0, z0, b_)], (px * side, 0, pz * side), bands[H.MARBLE], 0.85)
    # the end: a marble lip the water spills over
    x, y, z = pts[-1]
    H.W_oriented(mb, [(x + px * -w_out, y - 0.6, z + pz * -w_out), (x + px * w_out, y - 0.6, z + pz * w_out), (x + px * w_out, y + wall_h, z + pz * w_out),
                      (x + px * -w_out, y + wall_h, z + pz * -w_out)], (dx, 0, dz), bands[H.MARBLE], 0.8)
    water = W.MeshBuilder()
    for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
        q = lambda x, y, z, s_: (x + px * s_, y + 0.35, z + pz * s_)
        H.W_oriented(water, [q(x0, y0, z0, -w_in), q(x0, y0, z0, w_in), q(x1, y1, z1, w_in), q(x1, y1, z1, -w_in)], (0, 1, 0), bands[H.CRYSTAL], 0.9)
    lip = (x + dx * 0.2, y + 0.35, z + dz * 0.2)
    return [mb.object("HB_SpringChannel", coll, mat), water.object("HB_SpringChannelWater", coll, mat)], lip


def cluster_layout():
    """The floating crystal clusters: either side of the spawn's avenue, and over the lawns in the gaps between the avenues."""
    return []   # (removed, the owner 2026-11-12: "I think the floating crystals are not necessary you can remove it")


# ---------- placements ----------
def site_frame(name):
    x, z = site_centre(name)
    return x, z, face_yaw(-x, -z)


def write_placements(path=W.REPO + "/src/worldbuild/Placements/Yggdrasil.lua"):
    import re
    old = open(path).read()
    keep = {}
    for name in ("SI_RootShelf", "SI_CradleFloor"):
        m = re.search(r"        %s = \{\n(.*?)\n        \}," % name, old, re.S)
        keep[name] = m.group(1)
    relic = re.search(r"    Relics = \{.*?\},", old).group(0)
    L = ["-- Generated by tools/blender/world/hub_ground.py (the celestial hub, 2026-11-12). Do not edit by hand.",
         "-- Island-local Roblox studs. Kit entries place each piece's authored origin. HB_* are the hub's (Yggdrasil_Celestial.fbx);",
         "-- SI_RootShelf / SI_CradleFloor are the great root's, kept from the hub before.", "return {", "    Kit = {"]
    kit = {}

    def add(name, x, y, z, yaw=0.0):
        kit.setdefault(name, []).append((x, y, z, yaw))
    for name in ("HB_RingPlaza", "HB_Plazas", "HB_Avenues", "HB_PavingRunes", "HB_SpringChannel", "HB_SpringChannelWater"):
        add(name, 0.0, 0.0, 0.0)
    for k, (x, z, yaw) in enumerate(lamp_layout()):
        add("HB_CrystalLamp", x, ground(x, z) + LIFT, z, yaw)
        add("HB_CrystalLampLight" if k % 2 == 0 else "HB_CrystalLampGlow", x, ground(x, z) + LIFT, z, yaw)
    for k, (x, z) in enumerate(cluster_layout()):
        add("HB_Cluster", x, ground(x, z), z, k * 1.1)
        add("HB_ClusterGlow", x, ground(x, z), z, k * 1.1)
    for name in sorted(kit):
        L.append("        %s = {" % name)
        for x, y, z, yaw in kit[name]:
            L.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (x, y, z, yaw))
        L.append("        },")
    for name, body in keep.items():
        L += ["        %s = {" % name, body, "        },"]
    L.append("    },")
    L.append("    -- the shops' sites: centre, size (width, depth) and the yaw that turns local +Z toward the tree")
    L.append("    Plots = {")
    for name, size in (("Blacksmith", (24, 33)), ("BuySell", (36, 36)), ("Marketplace", (38, 38))):
        x, z, yaw = site_frame(name)
        L.append("        %s = { Centre = Vector3.new(%.2f, %.2f, %.2f), Size = Vector2.new(%g, %g), Yaw = %.4f }," % (name, x, LIFT, z, size[0], size[1], yaw))
    L.append("    },")
    L.append("    -- each shop's name board, where its prompt stands and its effects, in its site's frame (hub_celestial.py)")
    L.append("    Shops = {")
    shops = {
        "Blacksmith": (H.BS_SIGN, H.BS_PROMPT, [("Forge", H.BS_CORE), ("Smoke", H.BS_SMOKE)]),
        "BuySell": (H.BV_SIGN, H.BV_PROMPT, [("Stones", (-H.BV_PAN_X, H.BV_PAN_Y + 1.0, H.BV_C[1] + H.BV_R + 1.55))]),
        "Marketplace": (H.MK_SIGN, H.MK_PROMPT, [("Coins", (0.0, H.MK_EGG_Y, 0.0))]),
    }
    for name, ((sc, ss), prompt, fx) in shops.items():
        L.append("        %s = {" % name)
        L.append("            Sign = { Centre = Vector3.new(%g, %g, %.2f), Size = Vector2.new(%g, %g) }," % (sc[0], sc[1], sc[2] + 0.03, ss[0], ss[1]))
        L.append("            Prompt = Vector3.new(%g, %g, %g)," % prompt)
        L.append("            Fx = {")
        for kind, p in fx:
            L.append('                { Kind = "%s", Position = Vector3.new(%g, %g, %g) },' % (kind, p[0], p[1], p[2]))
        L.append("            },")
        L.append("        },")
    L.append("    },")
    sx, sz = site_centre("Spawn")
    L.append("    Spawn = Vector3.new(%.2f, %.2f, %.2f)," % (sx, LIFT + 1.98, sz))
    qx, qz, qyaw = site_frame("QiSpring")
    lip = SPRING_LIP or spring_channel_lip()
    L.append("    -- the Qi Spring (hub_celestial.qi_spring): its frame, and where its channel pours off the island (WorldBuilder.buildQiSpring)")
    L.append("    -- the hub's people (hub_npcs.py): each one's HumanoidRootPart and the yaw that turns its face (-Z) where it looks")
    L.append("    Npcs = {")
    for npc, (site, (lx, ly, lz), turn) in NPC_SPOTS.items():
        x, z, yaw = site_frame(site)
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        L.append("        %s = { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (npc, wx, LIFT + ly + HRP_OVER_FEET, wz, yaw + math.pi + turn))
    gx, gz = GUIDE_SPOT
    sx, sz = site_centre("Spawn")
    L.append("        Guide = { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (gx, ground(gx, gz) + LIFT + HRP_OVER_FEET, gz, face_yaw(sx - gx, sz - gz) + math.pi))
    L.append("    },")
    lx, lz = polar(MONUMENT[0], MONUMENT[1])
    sx, sz = site_centre("Spawn")
    L.append("    -- the Ascension Board (WorldBuilder.buildLeaderboard), facing the spawn")
    L.append("    Leaderboard = { Centre = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (lx, LIFT, lz, face_yaw(sx - lx, sz - lz)))
    mx, mz = polar(*MERCHANT)
    L.append("    -- the Wandering Merchant's camp (MerchantService: there for 10 minutes at the top of every hour), facing the tree")
    L.append("    Merchant = { Centre = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (mx, ground(mx, mz), mz, face_yaw(-mx, -mz)))
    L.append("    QiSpring = { Centre = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, SpillEnd = Vector3.new(%.2f, %.2f, %.2f) }," % (qx, LIFT, qz, qyaw, lip[0], lip[1], lip[2]))
    L.append("    " + relic.strip())
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return path


SPRING_LIP = None


def spring_channel_lip():
    import bpy
    coll = W.collection("Hub_ChannelProbe")
    objs, lip = spring_channel(coll, None, W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS)[1])
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    return lip


# ---------- the export ----------
def build():
    img, bands = W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS)
    mat = W.textured_material("Hub_CelestialMat", img)
    coll = W.collection("Hub_CelestialExport")
    W.clear_collection(coll)
    H.MARBLE_BAND, H.GOLD_BAND = bands[H.MARBLE], bands[H.GOLD]
    global SPRING_LIP
    objs = [fn(coll, mat, bands) for fn in H.BUILDINGS] + [lamp_light(coll, mat, bands)]
    objs += paving(coll, mat, bands)
    channel, SPRING_LIP = spring_channel(coll, mat, bands)
    objs += channel
    import hub_finish
    return hub_finish.finish(objs, bands, coll), img


def export():
    """assets/world/Yggdrasil/Yggdrasil_Celestial.fbx (+ its atlas PNG): every HB_ piece. Paving in island coordinates, everything else
    at the origin. WB.storeKit("Yggdrasil", <import>, "HB_Anchor")."""
    objs, img = build()
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Celestial.fbx"
    # (no texture: since the finish pass each mesh is one material, coloured in the game: WorldBuilder.MaterialLooks)
    W.export_batch(objs, path, image=None, anchor_name="HB_Anchor")
    return path, objs

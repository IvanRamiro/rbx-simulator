"""jade_lib_plants: Jade Grove's ground life (2026-11-22): ferns, broad leaves, flowers, lilies, grasses, glow-cap fungi, moss, logs and stumps.

  JG_Plant_Fern_Fountain_F1   a fountain of arching toothed fronds         JG_Plant_Fern_Crown_F2   a crown fern: a short fibrous stem, flat spreading fronds
  JG_Plant_BroadLeaf_L1       big taro-like leaves on long stalks          JG_Plant_FlowerBush_C1   a round bush of dark leaf with soft rose-white blooms
  JG_Plant_Orchid_O1          a jade orchid: an arching spike of star flowers over strap leaves
  JG_Plant_SpiritLily_P1 / P2 lily pads with open spirit lilies, for the pools   JG_Plant_Grass_G1 / G2  a meadow tuft and a tall arching grass
  JG_Mush_Parasol_M1 / Cluster_M3 / Funnel_M4 / Shelf_M2   glow-cap fungi: flat parasols, a cluster, trumpets, bracket shelves (small Neon accents, never lights)
  JG_Moss_Mat_M1 / M2         flat lumpy moss mats                       JG_Log_Fallen_L1, JG_Log_Stump_S1   a hollow fallen log and a cut stump with growth

Nothing here is an almond with a centre line, a dot at one end, a paired round shape or a tall rounded cap: flowers are open stars of narrow petals, caps are
broad and flat or open trumpets. Plants stay under 600 triangles; each is one mesh per material.
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU


def frond(P, base, direction, L, w, droop, rnd, mat="Fern", teeth=6, thick=0.05, up=(0.0, 1.0, 0.0)):
    """A pinnate frond: one arching blade whose width goes in and out like a row of leaflets."""
    ph = rnd.uniform(0, 1)

    def wf(t):
        env = math.sin(math.pi * min(1.0, t * 1.05)) ** 0.7
        tooth = 0.4 + 0.6 * abs(math.sin(math.pi * (teeth * t + ph)))
        return max(0.08, env * tooth) + 0.0
    P.put(C.blade(base, direction, L, w, droop=droop, thick=thick, segs=teeth, up=up, width_fn=wf), mat)


def knot(P, r, y=0.05, mat="Root"):
    """The root knot every leaf springs from (a small flat lump, so the fronds are joined to something)."""
    P.put(C.ellipsoid((0.0, y, 0.0), (r, r * 0.55, r), 7, 4, 0.12, 3), mat)


def fern_fountain(name, seed, n=8, L=(4.6, 6.6)):
    rnd = random.Random(seed)
    P = C.Piece(name)
    knot(P, 0.5)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.2, 0.2)
        lift = rnd.uniform(0.9, 1.5)
        frond(P, (math.cos(a) * 0.25, 0.1, math.sin(a) * 0.25), (math.cos(a), lift, math.sin(a)), rnd.uniform(*L), 1.1, rnd.uniform(0.42, 0.62), rnd, "Fern" if i % 3 else "FernBright", 6)
    return P


def fern_crown(name, seed, n=6):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # a short fibrous stem
    P.put(C.tube([(0, -0.3, 0), (0.1, 1.2, 0.0), (0.0, 3.1, 0.1)], lambda t: 0.62 - 0.22 * t, None, 7, per=3, wob=0.1, seed=seed), "Root")
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.15, 0.15)
        frond(P, (math.cos(a) * 0.3, 2.5, math.sin(a) * 0.3), (math.cos(a), 0.45, math.sin(a)), rnd.uniform(5.0, 6.8), 1.2, rnd.uniform(0.5, 0.75), rnd, "Fern" if i % 2 else "FernBright", 6)
    for i in range(3):
        a = TAU * i / 3 + 0.5
        frond(P, (math.cos(a) * 0.2, 2.9, math.sin(a) * 0.2), (math.cos(a) * 0.3, 1.0, math.sin(a) * 0.3), 3.4, 0.7, 0.25, rnd, "FernBright", 5)
    return P


def broad_leaf(name, seed, n=5):
    rnd = random.Random(seed)
    P = C.Piece(name)
    knot(P, 0.6)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.25, 0.25)
        d = rnd.uniform(0.0, 0.7)
        h = rnd.uniform(1.3, 2.6)
        base = (math.cos(a) * d, 0.0, math.sin(a) * d)
        tip = (math.cos(a) * (d + 1.3), h, math.sin(a) * (d + 1.3))
        P.put(C.tube([base, ((base[0] + tip[0]) / 2, h * 0.6, (base[2] + tip[2]) / 2), tip], 0.1, None, 4, per=2), "FernBright")
        P.put(C.blade(tip, (math.cos(a), 0.12, math.sin(a)), rnd.uniform(3.2, 4.2), rnd.uniform(1.3, 1.7), droop=0.32, thick=0.06, segs=3, mid=0.5, trough=0.22, keel=0.04), "Fern" if i % 2 else "LeafMid")
    return P


def bloom_star(P, c, R, rnd, mat="BloomWhite", petals=5, up=(0.0, 1.0, 0.0), centre="BloomGold"):
    """An open star of narrow pointed petals (never an almond with a line down it) round a small gold centre."""
    a0 = rnd.uniform(0, TAU)
    for k in range(petals):
        a = a0 + TAU * k / petals
        d = (math.cos(a) * 0.85 + up[0], 0.45 + up[1] * 0.5, math.sin(a) * 0.85 + up[2])
        P.put(C.blade(c, d, R, R * 0.46, droop=0.18, thick=0.035, segs=1, mid=0.5), mat)
    P.put(C.lathe([(0.0, 0.0), (R * 0.2, 0.02), (0.0, R * 0.2)], 5, c=(c[0], c[1] + 0.02, c[2])), centre)


def flower_bush(name, seed, blooms=6):
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(C.tube([(0, -0.2, 0), (0.1, 1.9, 0.0)], 0.3, None, 5, per=1), "Root")
    cells = []
    for k, (c, R) in enumerate((((0.0, 2.0, 0.0), 2.4), ((1.9, 1.5, 0.6), 1.7), ((-1.7, 1.4, -0.7), 1.7))):
        g = C.leaf_tier((0, 0, 0), R, R * 0.62, seg=8, lobes=4, ruffle=0.18, droop=0.5, seed=seed + k, under=0.5, bump=0.2)
        P.put(g, lambda n, ctr, c=c: "LeafDeep" if n[1] < 0.2 else "LeafMid", t=c, yaw=rnd.uniform(0, TAU))
        cells.append((c, R))
    for i in range(blooms):
        c, R = cells[i % len(cells)]
        a = rnd.uniform(0, TAU)
        r = rnd.uniform(0.25, 0.6) * R
        pos = (c[0] + math.cos(a) * r, c[1] + R * 0.62 * (0.8 - 0.5 * (r / R) ** 2) + 0.15, c[2] + math.sin(a) * r)
        bloom_star(P, pos, 0.85, rnd, "BloomRose" if i % 3 == 0 else "BloomWhite", 4)
    return P


def orchid(name, seed, flowers=5):
    rnd = random.Random(seed)
    P = C.Piece(name)
    knot(P, 0.4, 0.1, "Root")
    for i in range(5):
        a = TAU * i / 5 + rnd.uniform(-0.2, 0.2)
        P.put(C.blade((math.cos(a) * 0.15, 0.0, math.sin(a) * 0.15), (math.cos(a), 1.0, math.sin(a)), rnd.uniform(2.4, 3.4), 0.34, droop=0.5, thick=0.05, segs=3, mid=0.4, keel=0.03), "Fern")
    spike = [(0.0, 0.1, 0.0), (0.2, 1.8, 0.0), (0.9, 3.0, 0.2), (1.9, 3.5, 0.3)]
    P.put(C.tube(spike, lambda t: 0.07 - 0.03 * t, None, 4, per=3), "FernBright")
    pts = C.catmull(spike, 3)
    for k in range(flowers):
        t = 0.28 + 0.7 * k / (flowers - 1)
        p = pts[min(len(pts) - 1, int(t * (len(pts) - 1)))]
        size = 0.62 * (1.0 - 0.45 * k / flowers)
        bloom_star(P, (p[0], p[1] + 0.02, p[2] + 0.06), size * 1.15, rnd, "BloomWhite" if k % 2 else "BloomViolet", 4, centre="BloomGold")
    return P


def lily_pad(P, c, r, rnd, notch=0.5):
    n = 12
    poly = []
    for i in range(n):
        a = TAU * i / n
        rr = r * (1.0 + 0.05 * rnd.uniform(-1, 1))
        poly.append((math.cos(a) * rr, math.sin(a) * rr))
    # a pad with a wedge cut out, as a lily pad has: the polygon is walked around the notch
    k0 = rnd.randrange(n)
    poly = [p for i, p in enumerate(poly) if (i - k0) % n not in (0,)]
    P.put(C.prism(poly, 0.0, 0.1, c), "LeafMid")


def spirit_lily(P, c, rnd, scale=1.0):
    for tier, (n, L, lift, mat) in enumerate(((7, 1.25, 0.7, "BloomWhite"), (5, 0.95, 1.2, "BloomRose"))):
        a0 = rnd.uniform(0, TAU) + tier * 0.4
        for k in range(n):
            a = a0 + TAU * k / n
            P.put(C.blade((c[0], c[1] + 0.05, c[2]), (math.cos(a) * 0.8, lift, math.sin(a) * 0.8), L * scale, 0.42 * scale, droop=0.22, thick=0.04, segs=1, mid=0.55, trough=0.35), mat)
    P.put(C.lathe([(0.0, 0.0), (0.2 * scale, 0.02), (0.14 * scale, 0.32 * scale), (0.0, 0.36 * scale)], 6, c=(c[0], c[1] + 0.05, c[2])), "BloomGold")


def lilies(name, seed, pads=4, flowers=1):
    rnd = random.Random(seed)
    P = C.Piece(name)
    spots = []
    for i in range(pads):
        for _ in range(30):
            a = rnd.uniform(0, TAU)
            d = rnd.uniform(0.0, 2.6)
            r = rnd.uniform(0.9, 1.5)
            x, z = math.cos(a) * d, math.sin(a) * d
            if all(math.hypot(x - px, z - pz) > r + pr + 0.1 for px, pz, pr in spots):
                spots.append((x, z, r))
                break
    for (x, z, r) in spots:
        lily_pad(P, (x, 0.0, z), r, rnd)
        P.put(C.tube([(x, 0.05, z), (x * 0.5, -0.35, z * 0.5), (0.0, -0.7, 0.0)], 0.05, None, 4, per=2), "MossDeep")
    for k in range(min(flowers, len(spots))):
        x, z, r = spots[k]
        spirit_lily(P, (x, 0.1, z), rnd, 1.0)
    return P


def grass_tuft(name, seed, n=18, L=(2.6, 4.4), arch=0.4, w=0.3, radius=0.8):
    rnd = random.Random(seed)
    P = C.Piece(name)
    knot(P, radius * 1.2, 0.05, "Soil")
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(0.0, radius)
        lift = rnd.uniform(1.6, 3.2)
        P.put(C.blade((math.cos(a) * d, 0.0, math.sin(a) * d), (math.cos(a), lift, math.sin(a)), rnd.uniform(*L), w * rnd.uniform(0.8, 1.2), droop=arch * rnd.uniform(0.7, 1.3), thick=0.04, segs=2, mid=0.35),
              "Grass" if i % 4 else "GrassPale")
    return P


def parasol(c, R, stem_h, seed, tilt=None):
    """A broad flat parasol: a thin stem, a shallow cap with a scalloped rim (cap widest, flat: never a tall rounded cap), a glowing gill plate under it."""
    rnd = random.Random(seed)
    parts = []
    stem = C.lathe([(0.0, -0.1), (R * 0.17, 0.0), (R * 0.12, stem_h * 0.5), (R * 0.15, stem_h)], 6)
    cap = C.lathe([(0.0, stem_h - 0.02), (R * 0.9, stem_h - 0.1), (R * 1.0, stem_h + 0.06), (R * 0.82, stem_h + R * 0.2), (R * 0.4, stem_h + R * 0.28), (0.0, stem_h + R * 0.3)], 8,
                  mod=lambda th, k: 1.0 + 0.1 * math.sin(5 * th + seed) * (1 if k in (1, 2) else 0))
    gill = C.lathe([(0.0, stem_h - 0.08), (R * 0.84, stem_h - 0.08), (R * 0.84, stem_h - 0.14), (0.0, stem_h - 0.14)], 9)
    return stem, cap, gill


def mush_parasol(name, seed, n=1, R=1.7, stem=2.2):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for i in range(n):
        s, c, g = parasol((0, 0, 0), R * rnd.uniform(0.85, 1.1), stem * rnd.uniform(0.9, 1.15), seed + i)
        P.put(s, "CapPale")
        P.put(c, "CapPale")
        P.put(g, "GlowTeal")
    P.put(C.ellipsoid((0, -0.15, 0), (R * 1.0, 0.4, R * 1.0), 9, 4, 0.2, seed, flat=-0.3), lambda n, ctr: "Moss" if n[1] > 0 else "MossDeep")
    P.cyl((0, 0.8, 0), 0.8, 1.6)
    return P


def mush_cluster(name, seed, n=5):
    rnd = random.Random(seed)
    P = C.Piece(name)
    spots = []
    for i in range(n):
        for _ in range(30):
            a = rnd.uniform(0, TAU)
            d = rnd.uniform(0.0, 2.4)
            r = rnd.uniform(0.4, 1.0)
            x, z = math.cos(a) * d, math.sin(a) * d
            if all(math.hypot(x - px, z - pz) > r + pr + 0.05 for px, pz, pr in spots):
                spots.append((x, z, r))
                break
    for i, (x, z, r) in enumerate(spots):
        s, c, g = parasol((0, 0, 0), r, rnd.uniform(0.7, 1.5), seed + i)
        P.put(s, "CapPale", t=(x, 0.0, z))
        P.put(c, "CapPale", t=(x, 0.0, z))
        P.put(g, "GlowTeal", t=(x, 0.0, z))
    P.put(C.ellipsoid((0, -0.15, 0), (3.0, 0.4, 3.0), 10, 4, 0.2, seed, flat=-0.3), lambda n, ctr: "Moss" if n[1] > 0 else "MossDeep")
    return P


def mush_funnel(name, seed, n=4):
    """Open trumpets: a short stem widening into a wavy-lipped funnel (hollow throat), pale, with a glowing rim line."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.4, 0.4)
        d = rnd.uniform(0.2, 1.4) if i else 0.0
        h = rnd.uniform(1.1, 2.0)
        R = rnd.uniform(0.7, 1.05)
        prof = [(0.0, -0.1), (0.2, 0.0), (0.16, h * 0.5), (R * 0.55, h * 0.85), (R, h + 0.12), (R * 0.94, h + 0.16), (R * 0.5, h * 0.9), (0.0, h * 0.72)]
        g = C.lathe(prof, 9, mod=lambda th, k, s=rnd.random() * 6: 1.0 + (0.13 * math.sin(4 * th + s) if k >= 4 else 0.0))
        P.put(g, lambda n_, c_: "GlowTeal" if (c_[1] > 0.0 and n_[1] > 0.55 and math.hypot(c_[0], c_[2]) < 99 and False) else "CapPale", t=(math.cos(a) * d, 0.0, math.sin(a) * d))
    P.put(C.ellipsoid((0, -0.15, 0), (2.0, 0.35, 2.0), 9, 4, 0.2, seed, flat=-0.3), lambda n, ctr: "Moss" if n[1] > 0 else "MossDeep")
    return P


def mush_shelf(name, seed):
    """Three bracket shelves stacked on a trunk: D-shaped discs standing out from a bark stub (origin: the stub's surface, shelves open toward +x)."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(C.tube([(-0.6, -0.2, 0), (-0.55, 2.4, 0)], 0.62, None, 7, per=1), "Trunk")
    for k, (y, R) in enumerate(((0.4, 1.5), (1.15, 1.2), (1.85, 0.9))):
        seg = 9
        top = []
        for i in range(seg):
            a = math.pi * i / (seg - 1) - math.pi / 2
            top.append((math.cos(a) * R, math.sin(a) * R * 0.9))
        poly = top + [(-0.3, top[-1][1]), (-0.3, top[0][1])]
        g = C.prism(poly, 0.0, 0.22, (0.0, y, 0.0))
        P.put(g, lambda n, c: "CapPale" if n[1] > 0.5 else ("GlowTeal" if n[1] < -0.5 else "CapPale"))
    return P


def moss_mat(name, seed, R=3.0, n=1):
    P = C.Piece(name)
    P.put(C.ellipsoid((0, -0.08, 0), (R, 0.42, R * 0.82), 14, 4, 0.24, seed, flat=-0.28, yaw=seed), lambda nrm, ctr: "MossDeep" if nrm[1] < 0.3 else "Moss")
    P.put(C.ellipsoid((R * 0.35, -0.05, R * 0.3), (R * 0.45, 0.4, R * 0.4), 9, 4, 0.2, seed + 3, flat=-0.28), lambda nrm, ctr: "Moss")
    return P


def fallen_log(name, seed, L=9.0, R=1.15):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # the trunk lies along x: a slightly bent hollow cylinder (a thick wall, open at the broken end), moss along its top, a few snapped branch stubs
    rings = []
    stations = [(-L / 2, 1.0), (-L / 2 + 0.6, 1.0), (-L * 0.25, 1.04), (0.0, 1.0), (L * 0.25, 0.94), (L / 2 - 0.5, 0.88), (L / 2, 0.82)]
    for k, (x, sc) in enumerate(stations):
        y = R * sc + 0.1 + 0.18 * math.sin(k * 0.9)
        ring = []
        for i in range(9):
            a = TAU * i / 9
            w = 1.0 + 0.07 * C.noise3(k * 0.9, i * 0.6, seed, seed)
            ring.append((x, y + math.sin(a) * R * sc * w, math.cos(a) * R * sc * w))
        rings.append(ring)
    log = C.loft(rings, True, True)

    def mat(n, ctr):
        if n[1] > 0.5 and C.fbm3(ctr[0] * 0.3 + seed, 0.0, ctr[2] * 0.3, seed, 2) > -0.2:
            return "Moss"
        if abs(n[0]) > 0.9:
            return "Timber"
        return "Trunk"
    P.put(log, mat)
    # a dark hollow mouth at the broken end: a lathe cup pushed in
    P.put(C.lathe([(0.0, 0.0), (R * 0.62, 0.0), (R * 0.62, 0.9), (0.0, 0.9)], 8), "RockDark", t=(-L / 2 + 0.5, R + 0.1, 0.0), tilt=((0, 0, 1), -math.pi / 2))
    for k, (x, a, ln) in enumerate(((-1.4, 0.6, 1.1), (1.2, -0.5, 0.9), (2.9, 1.1, 0.7))):
        P.put(C.tube([(x, R * 1.6, math.sin(a) * R * 0.6), (x + 0.1, R * 1.6 + ln, math.sin(a) * (R * 0.6 + 0.3))], 0.22, 0.2, 5, per=1), "Trunk")
    # shelf fungi on its flank and a sprout from the top
    for k, x in enumerate((-2.2, 0.8)):
        P.put(C.lathe([(0.0, 0.0), (0.55, 0.0), (0.5, 0.18), (0.0, 0.2)], 8), "CapPale", t=(x, R * 1.0, R * 0.98), tilt=((1, 0, 0), -math.pi / 2 + 0.3))
    sx = 2.2
    P.put(C.tube([(sx, R * 1.9, 0.0), (sx + 0.1, R * 1.9 + 1.4, 0.1), (sx + 0.5, R * 1.9 + 2.5, 0.0)], 0.1, 0.09, 4, per=2), "FernBright")
    for b in range(3):
        a = TAU * b / 3 + 0.4
        P.put(C.blade((sx + 0.5, R * 1.9 + 2.4, 0.0), (math.cos(a), 0.7, math.sin(a)), 1.4, 0.45, droop=0.3, thick=0.04, segs=2), "LeafPale")
    P.box((0.0, R, 0.0), (L * 0.96, R * 1.9, R * 1.8), 0.0)
    return P


def stump(name, seed, R=1.8, H=2.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # a cut stump with concentric growth rings on its top (rings at one height so the top is flat), a flared foot and two roots
    prof = [(0.0, -0.4), (R * 1.35, -0.4), (R * 1.18, 0.3), (R * 0.98, H * 0.5), (R * 0.95, H), (R * 0.82, H), (R * 0.62, H), (R * 0.4, H), (R * 0.2, H), (0.0, H)]
    g = C.lathe(prof, 12, mod=lambda th, k: 1.0 + 0.06 * math.sin(3 * th + seed) * (1 if k < 5 else 0))

    def mat(n, ctr):
        if n[1] > 0.9:
            r = math.hypot(ctr[0], ctr[2])
            return "Timber" if int(r / (R * 0.2)) % 2 == 0 else "Trunk"
        if n[1] > 0.2 and C.fbm3(ctr[0] * 0.5 + seed, ctr[1] * 0.4, ctr[2] * 0.5, seed, 2) > 0.0:
            return "Moss"
        return "Trunk"
    P.put(g, mat)
    # a sprout and a ring of small shelf fungi
    P.put(C.tube([(R * 0.5, H - 0.1, R * 0.2), (R * 0.55, H + 1.0, R * 0.25), (R * 0.7, H + 1.8, R * 0.2)], 0.09, 0.08, 4, per=2), "FernBright")
    for b in range(3):
        a = TAU * b / 3
        P.put(C.blade((R * 0.7, H + 1.7, R * 0.2), (math.cos(a), 0.6, math.sin(a)), 1.2, 0.4, droop=0.3, thick=0.04, segs=2), "LeafPale")
    for k in range(4):
        a = TAU * k / 4 + 0.6
        P.put(C.lathe([(0.0, 0.0), (0.42, 0.0), (0.38, 0.14), (0.0, 0.15)], 7), "CapPale", t=(math.cos(a) * R * 1.0, 0.8 + 0.3 * k, math.sin(a) * R * 1.0), tilt=((math.sin(a), 0, -math.cos(a)), -1.3))
    P.cyl((0, H / 2, 0), R * 1.7, H)
    return P


def build_all():
    out = {}
    out["JG_Plant_Fern_Fountain_F1"] = fern_fountain("JG_Plant_Fern_Fountain_F1", 301)
    out["JG_Plant_Fern_Crown_F2"] = fern_crown("JG_Plant_Fern_Crown_F2", 311)
    out["JG_Plant_BroadLeaf_L1"] = broad_leaf("JG_Plant_BroadLeaf_L1", 321)
    out["JG_Plant_FlowerBush_C1"] = flower_bush("JG_Plant_FlowerBush_C1", 331)
    out["JG_Plant_Orchid_O1"] = orchid("JG_Plant_Orchid_O1", 341)
    out["JG_Plant_SpiritLily_P1"] = lilies("JG_Plant_SpiritLily_P1", 351, 4, 1)
    out["JG_Plant_SpiritLily_P2"] = lilies("JG_Plant_SpiritLily_P2", 361, 4, 2)
    out["JG_Plant_Grass_G1"] = grass_tuft("JG_Plant_Grass_G1", 371)
    out["JG_Plant_Grass_G2"] = grass_tuft("JG_Plant_Grass_G2", 381, 12, (4.6, 7.0), 0.28, 0.34, 0.9)
    out["JG_Mush_Parasol_M1"] = mush_parasol("JG_Mush_Parasol_M1", 391, 1, 1.9, 2.4)
    out["JG_Mush_Shelf_M2"] = mush_shelf("JG_Mush_Shelf_M2", 401)
    out["JG_Mush_Cluster_M3"] = mush_cluster("JG_Mush_Cluster_M3", 411)
    out["JG_Mush_Funnel_M4"] = mush_funnel("JG_Mush_Funnel_M4", 421)
    out["JG_Moss_Mat_M1"] = moss_mat("JG_Moss_Mat_M1", 431, 3.0)
    out["JG_Moss_Mat_M2"] = moss_mat("JG_Moss_Mat_M2", 441, 4.8)
    out["JG_Log_Fallen_L1"] = fallen_log("JG_Log_Fallen_L1", 451)
    out["JG_Log_Stump_S1"] = stump("JG_Log_Stump_S1", 461)
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-30s %5d tris  box %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), p.stats()))

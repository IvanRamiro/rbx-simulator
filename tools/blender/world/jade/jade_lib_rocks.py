"""jade_lib_rocks: Jade Grove's own stone (2026-11-22). Rounded, moss-draped, split and terraced: nothing like the basalt columns, the slate shards, the
lunar rock or the blossom garden's edge stones.

  JG_Rock_MossBoulders_B1 / B2   a cluster of squat, lumpy boulders with moss caps and a dark wet foot
  JG_Rock_LeaningSlab_L1 / L2    a tall slab leaning on its props, a broken top, fluted face, moss in its pockets
  JG_Rock_SplitStone_S1          an ancient boulder cloven in two, a sapling growing out of the cleft, its roots gripping both halves
  JG_Rock_TerraceStep_T1         stacked mossy shelves that climb in one-stud steps (walkable)
  JG_Rock_RiverStones_R1 / R2    smooth water-worn stones for streams and pool edges
  JG_Rock_Arch_A1                a small natural arch over a path (a hidden way in)
  JG_Rock_JadeVein_J1            an outcrop with seams of translucent jade

Feet sit a little under y = 0. Colliders are boxes inside the outline (rocks you walk on and bump into); the terraces' tops are exactly flat.
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU


def stone(c, r, seed, noise=0.3, flat=None, yaw=0.0, tilt=None, seg=9, rings=6, freq=1.0):
    """A lumpy boulder (flat-bottomed when `flat` is a height)."""
    return C.ellipsoid(c, r, seg, rings, noise, seed, flat=flat, yaw=yaw, tilt=tilt, freq=freq)


def rock_mat(seed, moss_n=0.52, moss_p=-0.1, wet_y=0.9, base_y=0.0, pale_n=0.8):
    """Rock by what a face looks at: moss on the upper faces in soft patches, a dark wet foot, a pale cap on the steepest tops."""
    def choose(n, ctr):
        if ctr[1] - base_y < wet_y and n[1] < 0.6:
            return "RockDark"
        if n[1] > moss_n and C.fbm3(ctr[0] * 0.2 + seed, ctr[1] * 0.2, ctr[2] * 0.2, seed, 2) > moss_p:
            return "Moss"
        if n[1] > pale_n:
            return "RockPale"
        return "Rock"
    return choose


def boulders(name, seed, layout):
    """layout: [(x, z, rx, ry, rz, yaw, noise)]"""
    rnd = random.Random(seed)
    P = C.Piece(name)
    for i, (x, z, rx, ry, rz, yaw, nz) in enumerate(layout):
        c = (x, ry * 0.18, z)
        P.put(stone(c, (rx, ry, rz), seed + i * 7, nz, flat=-0.35, yaw=yaw, seg=10, rings=6), rock_mat(seed + i, 0.5, -0.12, 1.0))
        # the mantle: a blanket of moss draped over the shoulders, its hem above the wet foot (slightly proud of the rock)
        if rx > 1.4:
            P.put(C.dome((x, ry * 0.2, z), (rx * 1.06, ry * 1.06, rz * 1.06), ry * 0.28, seg=10, rings=4, noise=nz * 1.1, seed=seed + i * 7, yaw=yaw), lambda n, ctr, s_=seed + i: "Moss" if n[1] > -0.05 else "MossDeep")
        if rx > 2.0:
            P.box((x, ry * 0.5, z), (rx * 1.35, ry * 1.0, rz * 1.35), yaw)
    return P


def leaning_slab(name, seed, h=13.0, w=5.6, t=1.9, lean=0.24, chip=0.22, companion=True):
    rnd = random.Random(seed)
    P = C.Piece(name)
    tilt = ((0, 0, 1), lean)
    slab = C.chunk((0, h / 2 - 0.4, 0), (w, h, t), seed, 0.04, taper=0.18, tilt=tilt, chip=chip)
    P.put(slab, rock_mat(seed, 0.3, -0.3, 1.4, -0.5, 0.9))
    # a broken top: a wedge sheared off and lying against the foot, and a split running down the face
    for k, off in enumerate((-1.9, -0.2, 1.7)):
        hh = h * rnd.uniform(0.5, 0.8)
        f = C.chunk((off * w / 5.6, hh / 2 - 0.2, t / 2 + 0.1), (0.8, hh, 0.4), seed + 3 + k, 0.05, tilt=tilt)
        P.put(f, "RockPale" if k != 1 else "RockDark")
    # moss pockets high on the slab (a ledge where the weather lodged)
    P.put(C.chunk((0.3 + math.sin(lean) * h * 0.62, h * 0.62, t * 0.62), (w * 0.62, 0.5, 0.9), seed + 9, 0.12, tilt=tilt), "Moss")
    P.put(stone((w * 0.55, 0.7, t * 1.6), (1.5, 0.9, 1.2), seed + 5, 0.3, flat=-0.3, seg=8, rings=5), rock_mat(seed + 5, 0.4, -0.1, 0.8))
    P.put(stone((-w * 0.2, 0.9, -t * 1.5), (1.9, 1.2, 1.5), seed + 8, 0.28, flat=-0.3, seg=9, rings=5), rock_mat(seed + 8, 0.4, -0.1, 0.8))
    P.box((0, h * 0.3, 0), (w * 0.9, h * 0.6, t * 1.2), 0.0)
    if companion:
        # a shorter slab leans the other way against the first: the two make a lean-to
        c2 = C.chunk((-w * 0.95, h * 0.28, t * 0.4), (w * 0.62, h * 0.56, t * 0.9), seed + 31, 0.05, taper=0.2, tilt=((0, 0, 1), -lean * 1.25), chip=0.3)
        P.put(c2, rock_mat(seed + 31, 0.3, -0.3, 1.2, -0.5, 0.9))
        P.box((-w * 0.95, h * 0.22, t * 0.4), (w * 0.5, h * 0.44, t * 0.8), 0.0)
    return P


def split_stone(name, seed):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # two halves of one boulder, parted by a V-shaped cleft, each with its own flat sheared face toward the other
    for sgn, i in ((-1, 0), (1, 1)):
        c = (sgn * 2.5, 2.6, 0.0)
        g = stone(c, (3.4, 3.3, 3.9), seed + i, 0.18, flat=-0.5, yaw=0.4 * sgn, tilt=((0, 0, 1), -0.16 * sgn), seg=12, rings=7)
        P.put(g, rock_mat(seed + i, 0.5, -0.05, 1.1, 0.0))
    P.box((-2.7, 2.4, 0.0), (4.2, 4.8, 5.2))
    P.box((2.7, 2.4, 0.0), (4.2, 4.8, 5.2))
    # the sapling grows out of the cleft: a bent trunk, a few thin boughs and two small leaf clouds
    path = [(0.0, 0.3, 0.0), (0.2, 3.0, 0.2), (-0.3, 6.2, 0.1), (0.4, 9.4, -0.2), (0.6, 11.6, 0.0)]
    P.put(C.tube(path, lambda t: 0.52 - 0.34 * t, None, 7, per=3, wob=0.05, seed=seed), "Trunk")
    for k, (hy, a) in enumerate(((5.2, 0.8), (7.6, 3.6), (9.3, 2.0))):
        e = (math.cos(a) * 2.6 + 0.2, hy + 1.8, math.sin(a) * 2.6)
        P.put(C.tube([(0.0, hy, 0.0), ((e[0]) * 0.5, hy + 0.7, e[2] * 0.5), e], lambda t: 0.26 - 0.14 * t, None, 5, per=2), "Trunk")
    for k, (c, R) in enumerate((((1.4, 9.8, 0.6), 3.4), ((-1.6, 8.3, -1.0), 2.7), ((0.6, 12.2, -0.4), 2.4))):
        g = C.leaf_tier((0, 0, 0), R, R * 0.55, seg=12, lobes=4, ruffle=0.22, droop=0.5, seed=seed + 20 + k, under=0.4, bump=0.2)

        def lm(n, ctr, c=c, k=k):
            if n[1] > 0.5:
                return "LeafPale" if C.fbm3(ctr[0] * 0.2 + k, ctr[1] * 0.2, ctr[2] * 0.2, seed, 2) > 0.22 else "LeafMid"
            return "LeafMid" if n[1] > -0.1 else "LeafDeep"
        P.put(g, lm, t=c, yaw=rnd.uniform(0, TAU))
    # roots grip both halves: draped from the cleft over the shoulders down to the ground
    for k, (sgn, a) in enumerate(((-1, 0.5), (-1, -0.6), (1, 0.4), (1, -0.5), (1, 1.4), (-1, 1.3))):
        pts = [(0.0, 1.2 + 0.07 * k, 0.0), (sgn * 1.3, 4.0, math.sin(a) * 1.5), (sgn * 4.0, 4.6, math.sin(a) * 3.0), (sgn * (5.6 + 0.4 * k), 0.8, math.sin(a) * 4.6 + math.cos(a))]
        P.put(C.tube(pts, lambda t: 0.4 - 0.22 * t, 0.3, 6, per=3, wob=0.06, seed=seed + 40 + k), "Root")
    return P


def terrace(name, seed, steps=4, rise=1.2, base=(15.0, 11.0), shrink=0.74):
    """Stacked shelves of rock, each `rise` higher, the tops exactly flat (walkable), their outlines irregular and hewn, moss along the lips.
    Origin on the ground at the front; the shelves climb toward +z."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    w, d = base
    z0 = -d / 2
    for k in range(steps):
        top = rise * (k + 1)
        cx = rnd.uniform(-0.7, 0.7) * (k > 0)
        cz = z0 + d / 2
        n = 11
        poly = []
        for i in range(n):
            a = TAU * i / n
            rr = 1.0 + 0.16 * math.sin(3 * a + k) + 0.1 * rnd.uniform(-1, 1)
            poly.append((math.cos(a) * w / 2 * rr, math.sin(a) * d / 2 * rr))
        thick = top + 1.4
        g = C.prism(poly, -1.4 - 0.13 * k, top, (cx, 0.0, cz))

        def m(nrm, ctr, top=top, k=k):
            if nrm[1] > 0.9:
                return "Moss" if C.fbm3(ctr[0] * 0.25 + k * 7, 0.0, ctr[2] * 0.25, seed, 2) > -0.25 else "RockPale"
            return "RockDark" if ctr[1] < top * 0.45 else "Rock"
        P.put(g, m)
        P.box((cx, top - 0.5, cz), (w * 0.78, 1.0, d * 0.78), 0.0)
        z0 += d * 0.58
        w *= shrink
        d *= shrink
    return P


def river_stones(name, seed, n=7, spread=3.4):
    rnd = random.Random(seed)
    P = C.Piece(name)
    placed = []
    for i in range(n):
        for _ in range(30):
            a = rnd.uniform(0, TAU)
            d = spread * math.sqrt(rnd.random())
            r = rnd.uniform(0.7, 1.9)
            x, z = math.cos(a) * d, math.sin(a) * d
            if all(math.hypot(x - px, z - pz) > r + pr + 0.15 for px, pz, pr in placed):
                placed.append((x, z, r))
                break
    for i, (x, z, r) in enumerate(placed):
        sq = rnd.uniform(0.4, 0.62)
        g = stone((x, r * sq * 0.45, z), (r, r * sq, r * rnd.uniform(0.7, 1.0)), seed + i, 0.07, flat=-r * sq * 0.5, yaw=rnd.uniform(0, TAU), seg=9, rings=5)

        def m(n, ctr, y0=r * sq):
            if n[1] > 0.75:
                return "RockPale"
            return "RockDark" if ctr[1] < y0 * 0.6 else "Rock"
        P.put(g, m)
        if r > 1.3:
            P.box((x, r * sq * 0.5, z), (r * 1.2, r * sq, r * 1.2), 0.0)
    return P


def arch(name, seed, span=9.0, height=9.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for sgn, i in ((-1, 0), (1, 1)):
        x = sgn * span / 2
        P.put(stone((x, height * 0.42, 0.0), (2.9, height * 0.52, 3.2), seed + i, 0.22, flat=-0.5, yaw=sgn * 0.3, seg=10, rings=7), rock_mat(seed + i, 0.55, -0.1, 1.2))
        P.box((x, height * 0.4, 0.0), (3.8, height * 0.8, 4.2), 0.0)
    # the lintel: a heavy bent slab resting on both shoulders, stooping in the middle
    rings = []
    for k in range(9):
        t = k / 8.0
        x = -span / 2 - 1.0 + (span + 2.0) * t
        y = height * 0.82 + 1.5 * math.sin(math.pi * t) - 0.7 * (1 - abs(2 * t - 1)) ** 1.5 * 0.0
        th = 2.4 - 0.9 * math.sin(math.pi * t)
        wd = 2.9 + 0.5 * math.sin(math.pi * t * 2 + seed)
        ring = []
        for a in range(8):
            ang = TAU * a / 8
            ring.append((x, y + math.sin(ang) * th * 0.5, math.cos(ang) * wd * (1 + 0.08 * C.noise3(k, a, seed, seed))))
        rings.append(ring)
    P.put(C.loft(rings, True, True), rock_mat(seed + 3, 0.5, -0.2, 1.2, 0.0, 0.7))
    P.put(stone((0.0, height * 0.82 + 2.5, 0.0), (3.6, 0.9, 2.2), seed + 5, 0.3, seg=9, rings=4), "Moss")
    return P


def jade_vein(name, seed):
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(stone((0.0, 2.2, 0.0), (4.4, 3.4, 3.6), seed, 0.26, flat=-0.4, seg=12, rings=7), rock_mat(seed, 0.6, 0.0, 1.0))
    P.put(stone((3.4, 1.0, 1.4), (2.0, 1.4, 1.7), seed + 1, 0.3, flat=-0.3, seg=9, rings=5), rock_mat(seed + 1, 0.6, 0.0, 0.8))
    # seams of jade: thin translucent slabs laid into the rock's face along two diagonals, standing a hair proud
    for k, (ang, y, wlen) in enumerate(((0.55, 2.4, 4.6), (-0.4, 1.4, 3.4), (0.2, 3.3, 2.4))):
        P.put(C.chunk((math.cos(1.3 + k) * 1.1, y, -2.5 + 0.3 * k), (wlen, 0.34, 0.5), seed + 8 + k, 0.05, tilt=((0, 0, 1), ang)), "JadeGlass")
    for k in range(3):
        a = 2.4 + k * 0.7
        P.put(C.chunk((math.cos(a) * 3.0, 3.1 - 0.4 * k, -math.sin(a) * 2.2), (0.7, 1.3, 0.7), seed + 20 + k, 0.1, tilt=((1, 0, 0), 0.4)), "Jade")
    P.box((0.0, 1.8, 0.0), (6.4, 3.6, 5.2), 0.0)
    return P


def build_all():
    out = {}
    out["JG_Rock_MossBoulders_B1"] = boulders("JG_Rock_MossBoulders_B1", 201, [(0, 0, 4.4, 4.4, 3.8, 0.3, 0.3), (5.0, 1.4, 2.8, 3.0, 2.6, 1.1, 0.32), (-3.4, 3.8, 2.2, 2.3, 2.0, 2.0, 0.3),
                                                                           (2.6, -3.9, 1.5, 1.5, 1.4, 0.5, 0.28), (-4.6, -2.2, 1.2, 1.2, 1.1, 0.0, 0.26)])
    out["JG_Rock_MossBoulders_B2"] = boulders("JG_Rock_MossBoulders_B2", 217, [(0, 0, 3.0, 5.4, 2.8, 0.9, 0.36), (3.8, -1.2, 3.6, 3.4, 3.0, 0.2, 0.3), (-2.9, 3.1, 1.9, 1.9, 1.8, 1.4, 0.3), (0.8, 4.4, 1.3, 1.3, 1.2, 0.0, 0.26)])
    out["JG_Rock_LeaningSlab_L1"] = leaning_slab("JG_Rock_LeaningSlab_L1", 221, 13.0, 5.6, 1.9, 0.24, 0.22)
    out["JG_Rock_LeaningSlab_L2"] = leaning_slab("JG_Rock_LeaningSlab_L2", 231, 9.0, 4.4, 1.6, -0.3, 0.3)
    out["JG_Rock_StandingSlab_L3"] = leaning_slab("JG_Rock_StandingSlab_L3", 243, 6.5, 3.0, 1.3, 0.06, 0.2, companion=False)
    out["JG_Rock_SplitStone_S1"] = split_stone("JG_Rock_SplitStone_S1", 241)
    out["JG_Rock_TerraceStep_T1"] = terrace("JG_Rock_TerraceStep_T1", 251)
    out["JG_Rock_RiverStones_R1"] = river_stones("JG_Rock_RiverStones_R1", 261, 7, 3.4)
    out["JG_Rock_RiverStones_R2"] = river_stones("JG_Rock_RiverStones_R2", 271, 5, 2.4)
    out["JG_Rock_Arch_A1"] = arch("JG_Rock_Arch_A1", 281)
    out["JG_Rock_JadeVein_J1"] = jade_vein("JG_Rock_JadeVein_J1", 291)
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-30s %5d tris  box %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), p.stats()))

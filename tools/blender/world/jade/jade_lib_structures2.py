"""jade_lib_structures2: the crafted versions of eight of Jade Grove's structures (2026-11-22, second pass after the review: "plain props" were not the bar). Forest-spirit
architecture, grown into the trees and stone: round fluted pillars with leaf capitals, layered shingle and thatch with curled ridge ends, lashed beams and woven walls,
broken courses and fallen blocks, roots and saplings taking the ruins back. No pagoda, no paifang, no dougong, no tiered eaves, no lanterns of a festival, no letters.

Every piece keeps its name, its footprint, its floor heights (shrine 2.0, hall 3.0, lookout 12.0), its stair risers (exactly 1.0) and the first pass's collision proxies (the boxes
and cylinders are the same numbers); only the visible forms are new.
"""
import math
import random

import jade_lib_core as C
import jade_lib_craft as K
import jade_lib_structures as S

TAU = C.TAU


def stone_mat(seed, thr=-0.1):
    return S.moss_top(seed, thr)


def leaf_cap(P, c, r, seed, mat="Stone", tilt=None, yaw=0.0):
    """A leaf capital: a flared bell with four leaf lobes curling out of its rim (a column's head), built at the origin and placed at c (tilt / yaw for a fallen one)."""
    Q = C.Piece("q")
    Q.put(C.lathe([(r * 0.8, 0.0), (r * 1.25, 0.28), (r * 1.4, 0.52), (0.0, 0.56)], 8, mod=lambda th, k: 1.0 + (0.12 * math.cos(4 * th) if k >= 1 else 0.0)), mat)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        Q.put(C.blade((math.cos(a) * r * 0.85, 0.2, math.sin(a) * r * 0.85), (math.cos(a) * 0.6, 0.9, math.sin(a) * 0.6), r * 1.1, r * 0.5, droop=0.35, thick=0.1, segs=1, mid=0.5), mat)
    P.add_piece(Q, t=c, yaw=yaw, tilt=tilt)


# ----------------------------------------------------------------------------------------------------------------------
def lantern(name, seed, tall):
    """The sprout lantern. The tall one (L1, two of them, by the shrines) is the rich version: a plinth with leaf bracts, a spiral-fluted stem with a node and two leaves, a lamp cage of four bowed ribs round an
    amber core, a cap of four seed leaves standing up and a curled finial. The short one (L2, fifteen along the trails) keeps the same silhouette with fewer parts."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    rich = tall
    H = 5.2 if tall else 3.4
    sg = 10 if rich else 6
    # plinth
    if rich:
        P.put(C.lathe([(0.0, -0.3), (1.05, -0.3), (1.05, 0.12), (0.92, 0.2), (0.88, 0.34), (0.7, 0.42), (0.0, 0.42)], sg), stone_mat(seed))
        for k in range(3):
            a = TAU * k / 3 + 0.4
            P.put(C.blade((math.cos(a) * 0.55, 0.38, math.sin(a) * 0.55), (math.cos(a), 0.45, math.sin(a)), 0.95, 0.34, droop=0.4, thick=0.07, segs=1), "Moss")
    else:
        P.put(C.lathe([(0.0, -0.3), (1.05, -0.3), (0.95, 0.2), (0.7, 0.42), (0.0, 0.42)], sg), stone_mat(seed))
    # stem: tapering, a swollen node halfway (rich: spiral flutes and two small leaves)
    stem_h = H * 0.56
    prof = [(0.0, 0.3), (0.36, 0.3), (0.3, stem_h * 0.45), (0.42, stem_h * 0.5), (0.3, stem_h * 0.56), (0.27, stem_h), (0.34, stem_h + 0.12), (0.0, stem_h + 0.12)]
    if rich:
        P.put(C.lathe(prof, 12, mod=lambda th, k: 1.0 - (0.09 * (0.5 + 0.5 * math.cos(6 * th + k * 0.7)) if k in (1, 2, 3, 5, 6) else 0.0)), "Stone")
    else:
        P.put(C.lathe([prof[0], prof[1], prof[2], (0.4, stem_h * 0.52), prof[5], prof[6], prof[7]], sg), "Stone")
    # the lamp: a base ring, four ribs bowed outward, a top ring, the amber core inside
    y0 = stem_h + 0.1
    lamp = H * 0.34
    if rich:
        P.put(C.lathe([(0.0, y0), (0.62, y0), (0.66, y0 + 0.18), (0.0, y0 + 0.18)], sg), "Stone")
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        pts = [(math.cos(a) * 0.5, y0 + 0.1, math.sin(a) * 0.5), (math.cos(a) * 0.78, y0 + lamp * 0.35, math.sin(a) * 0.78), (math.cos(a) * 0.78, y0 + lamp * 0.7, math.sin(a) * 0.78), (math.cos(a) * 0.5, y0 + lamp, math.sin(a) * 0.5)]
        if not rich:
            pts = [(math.cos(a) * 0.3, y0 + 0.02, math.sin(a) * 0.3), (math.cos(a) * 0.84, y0 + lamp * 0.5, math.sin(a) * 0.84), (math.cos(a) * 0.1, y0 + lamp + 0.08, math.sin(a) * 0.1)]
        P.put(C.tube(pts, 0.1, 0.1, 3, per=1), "Stone")
    if rich:
        P.put(C.lathe([(0.0, y0 + lamp - 0.05), (0.62, y0 + lamp - 0.05), (0.58, y0 + lamp + 0.15), (0.0, y0 + lamp + 0.15)], sg), "StoneDark")
    P.put(C.ellipsoid((0, y0 + lamp * 0.5, 0), (0.28, 0.4, 0.28), 6 if rich else 5, 4 if rich else 3), "GlowAmber")
    P.put(C.lathe([(0.0, y0 + lamp * 0.35), (0.14, y0 + lamp * 0.35), (0.14, y0 + lamp * 0.12), (0.0, y0 + lamp * 0.1)], 5 if rich else 4), "StoneDark")
    # the cap: seed leaves standing up (rich: two pairs and a curled finial; lean: one pair)
    top = y0 + lamp + 0.1
    for k in range(2 if rich else 1):
        a = k * math.pi / 2 + 0.3
        sgm = 2 if rich else 1
        P.put(C.blade((math.cos(a) * 0.1, top, math.sin(a) * 0.1), (math.cos(a), 1.5, math.sin(a)), 1.7, 0.78, droop=0.45, thick=0.2, segs=sgm, mid=0.55, keel=0.08), "Stone" if k else "Moss")
        P.put(C.blade((-math.cos(a) * 0.1, top + 0.02, -math.sin(a) * 0.1), (-math.cos(a), 1.5, -math.sin(a)), 1.5, 0.7, droop=0.45, thick=0.18, segs=sgm, mid=0.55, keel=0.08), "Stone")
    if rich:
        K.curl(P, (0, top + 0.1, 0), (0.2, 1.0, 0.1), 0.1, 1.2, 0.3, "Stone")
    P.cyl((0, H / 2, 0), 1.2, H)
    return P


# ----------------------------------------------------------------------------------------------------------------------
def waymarker(name, seed, kind):
    """Carved waymarker stones, no letters and no arrows: bands, a coil, a rounded hat of moss."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    if kind == 0:     # tall: a stepped footing, a tapering shaft with two carved bands and a coil, a mossy hat, a hanging root
        P.put(C.chunk((0, 0.25, 0), (2.4, 0.7, 1.9), seed, 0.04), stone_mat(seed))
        P.put(C.chunk((0, 2.3, 0), (1.7, 4.2, 1.2), seed + 1, 0.04, taper=0.22), stone_mat(seed + 1, 0.2))
        P.box((0, 2.0, 0), (1.5, 4.0, 1.0))
        for y in (1.1, 1.7):
            P.put(C.chunk((0, y, -0.5), (1.5, 0.14, 0.4), seed + 2 + int(y * 3), 0.02), "StoneDark")
        pts = [(math.cos(a) * (0.52 - 0.055 * a / 1.6), 3.15 + math.sin(a) * (0.52 - 0.055 * a / 1.6), -0.5) for a in [t * 0.5 for t in range(0, 15)]]
        P.put(C.tube(pts, 0.13, 0.1, 4, per=1, up=(0, 0, 1)), "StoneDark")
        P.put(C.lathe([(0.0, 4.2), (1.0, 4.2), (1.18, 4.42), (1.0, 4.74), (0.5, 4.9), (0.0, 4.92)], 10, mod=lambda th, k: 1.0 + 0.1 * math.sin(5 * th + k)), lambda n, c: "Moss" if n[1] > 0.3 else "Stone")
    elif kind == 1:   # low: three stacked stones, banded, a leaf-shaped cap slab
        for k, (y, w, d, h) in enumerate(((0.45, 2.0, 1.7, 0.9), (1.25, 1.7, 1.4, 0.8), (1.95, 1.3, 1.1, 0.7))):
            P.put(C.chunk((0.05 * k, y, 0.04 * k), (w, h, d), seed + k, 0.06, yaw=0.2 * k), stone_mat(seed + k, 0.1))
            P.put(C.chunk((0.05 * k, y, -d / 2 + 0.05), (w * 0.8, 0.12, 0.35), seed + 10 + k, 0.02, yaw=0.2 * k), "StoneDark")
        P.put(C.blade((0.0, 2.25, 0.0), (1.0, 0.1, 0.2), 1.9, 0.95, droop=0.15, thick=0.22, segs=3, mid=0.5, keel=0.06), "Stone")
        P.put(C.blade((0.0, 2.25, 0.0), (-1.0, 0.1, -0.2), 1.7, 0.85, droop=0.15, thick=0.2, segs=3, mid=0.5, keel=0.06), "Moss")
        P.box((0, 1.0, 0), (1.7, 2.0, 1.3))
    else:             # leaning: a pillar that tilts and ends in a crook (a bent-over top), banded, a ball of moss
        P.put(C.chunk((0, 0.3, 0), (1.9, 0.7, 1.5), seed, 0.05), stone_mat(seed))
        P.put(C.tube([(0.0, 0.4, 0.0), (0.2, 1.6, 0.0), (0.5, 2.7, 0.0), (1.0, 3.35, 0.0), (1.7, 3.3, 0.0)], lambda t: 0.62 - 0.22 * t, lambda t: 0.5 - 0.15 * t, 8, per=3, wob=0.05, seed=seed), stone_mat(seed + 1, 0.3))
        for y, xo in ((1.0, 0.12), (1.6, 0.18)):
            P.put(C.chunk((xo, y, -0.42), (1.0, 0.12, 0.34), seed + 3 + int(y * 4), 0.02), "StoneDark")
        P.put(C.ellipsoid((1.75, 3.0, 0.0), (0.7, 0.55, 0.6), 8, 5, 0.2, seed), "Moss")
        P.box((0.0, 1.4, 0.0), (1.3, 2.8, 0.9))
    return P


# ----------------------------------------------------------------------------------------------------------------------
def ruin_column(name, seed, kind):
    """A broken round pillar with a moulded base and flutes (the shaft snapped, a toppled drum at its foot) and a fallen length with a leaf capital."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    if kind == 0:
        g = K.fluted_column(4.2, 0.95, 0.78, flutes=5, seg=10, entasis=0.05, base=True, seed=seed, rings=2)
        P.put(g, stone_mat(seed, -0.25))
        # the broken head: a jagged cap of stone and the stump of a capital
        P.put(C.chunk((0.15, 4.35, 0.0), (1.5, 0.55, 1.3), seed + 3, 0.25, tilt=((0, 0, 1), 0.4), chip=0.35), "StoneDark")
        P.put(C.chunk((-0.2, 4.9, 0.1), (0.9, 0.7, 0.8), seed + 4, 0.3, tilt=((1, 0, 0), -0.5)), "Stone")
        # a drum fallen against the foot
        P.put(C.lathe([(0.0, 0.0), (0.78, 0.0), (0.76, 0.6), (0.0, 0.6)], 8), stone_mat(seed + 5), t=(1.7, 0.45, 0.4), tilt=((0, 0, 1), 1.2))
        P.cyl((0, 2.7, 0), 2.0, 5.4)
    else:
        L = 4.2
        # three drums of a fallen shaft, slightly out of line, fluted; a leaf capital lying beyond; rubble
        drums = ((-1.45, 1.55, 0.0), (0.0, 1.55, 0.18), (1.45, 1.55, -0.12))
        for k, (x, ln, dz) in enumerate(drums):
            d = C.lathe([(0.0, -ln / 2), (0.9, -ln / 2), (0.86, 0.0), (0.9, ln / 2), (0.0, ln / 2)], 12, mod=lambda th, kk: 1.0 - (0.07 * (0.5 + 0.5 * math.cos(6 * th)) if kk in (1, 2, 3) else 0.0))
            P.put(d, stone_mat(seed + k, -0.25), t=(x, 0.9, dz), tilt=((0, 0, 1), math.pi / 2 + 0.03 * k), yaw=0.0)
        leaf_cap(P, (3.35, 0.8, 0.2), 0.8, seed + 8, tilt=((0, 0, 1), math.pi / 2 - 0.15), yaw=0.2)
        P.put(C.chunk((-2.9, 0.4, 0.8), (1.0, 0.8, 0.9), seed + 9, 0.12, yaw=0.5), stone_mat(seed + 9))
        P.put(C.chunk((-0.4, 0.25, -1.0), (1.2, 0.5, 0.9), seed + 10, 0.15, yaw=1.0), "StoneDark")
        P.put(C.ellipsoid((0.1, 1.85, 0.0), (1.3, 0.3, 0.7), 8, 3, 0.2, seed), "Moss")
        P.box((0, 0.9, 0), (L, 1.8, 1.8))
    return P


# ----------------------------------------------------------------------------------------------------------------------
def offering_table(name="JG_Offering_Table_O1", seed=581):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # carved legs: a foot block, a waist, a capital block, each side; a top slab with a scalloped rim and a carved border; a bowl on a leaf-lipped pedestal
    for sx in (-1, 1):
        x = sx * 1.5
        P.put(C.chunk((x, 0.18, 0), (1.3, 0.4, 1.8), seed + sx, 0.03), stone_mat(seed + sx))
        P.put(C.chunk((x, 0.75, 0), (0.78, 0.8, 1.15), seed + 3 + sx, 0.03), stone_mat(seed + 4 + sx))
        P.put(C.chunk((x, 1.2, 0), (1.18, 0.34, 1.6), seed + 6 + sx, 0.03), "StoneDark")
        for k in range(3):
            P.put(C.chunk((x - 0.28 + k * 0.28, 0.75, -0.6), (0.1, 0.55, 0.12), seed + 12 + k + sx, 0.01), "StoneDark")
    n = 14
    poly = [(math.cos(TAU * i / n) * (2.3 + 0.14 * (i % 2)), math.sin(TAU * i / n) * (1.05 + 0.1 * (i % 2))) for i in range(n)]
    P.put(C.prism(poly, 1.33, 1.57, (0.0, 0.0, 0.0)), lambda nn, c: "Moss" if nn[1] > 0.8 and C.fbm3(c[0] * 0.5, 0, c[2] * 0.5, seed, 2) > 0.45 else "Stone")
    inner = [(math.cos(TAU * i / n) * 2.0, math.sin(TAU * i / n) * 0.82) for i in range(n)]
    P.put(C.prism(inner, 1.52, 1.62, (0.0, 0.0, 0.0)), "StoneDark")      # a carved border inset into the top
    # the bowl: a pedestal and a wide shallow bowl with a wavy leaf lip, an ember in it
    P.put(C.lathe([(0.0, 1.55), (0.3, 1.55), (0.22, 1.75), (0.3, 1.9), (0.62, 2.0), (0.7, 2.1), (0.6, 2.14), (0.0, 2.1)], 9, mod=lambda th, k: 1.0 + (0.1 * math.sin(6 * th) if k >= 5 else 0.0)), "RockDark", t=(-1.0, 0.0, 0.1))
    P.put(C.ellipsoid((-1.0, 2.1, 0.1), (0.2, 0.12, 0.2), 6, 3), "GlowAmber")
    # an incense stand on three legs with a perforated bowl, a small cairn, a cord of beads laid in a loop
    for k in range(3):
        a = TAU * k / 3
        P.put(C.tube([(1.6 + math.cos(a) * 0.32, 1.55, -0.5 + math.sin(a) * 0.32), (1.6 + math.cos(a) * 0.12, 2.1, -0.5 + math.sin(a) * 0.12)], 0.05, 0.04, 4, per=1), "Timber")
    P.put(C.lathe([(0.0, 2.05), (0.3, 2.1), (0.32, 2.3), (0.0, 2.32)], 8), "StoneDark", t=(1.6, 0.0, -0.5))
    P.put(C.ellipsoid((1.6, 2.38, -0.5), (0.1, 0.08, 0.1), 5, 3), "GlowAmber")
    for k, (x, z, r) in enumerate(((0.55, 0.45, 0.34), (0.55, 0.45, 0.24))):
        P.put(C.ellipsoid((x + 0.2, 1.62 + k * 0.24, z), (r, r * 0.9, r), 6, 3, 0.05, seed + k), "RockPale")
    pts = [(math.cos(a) * 0.55 + 0.1, 1.6, math.sin(a) * 0.3 - 0.45) for a in [t * 0.8 for t in range(0, 8)]]
    P.put(C.tube(pts, 0.05, 0.05, 3, per=1), "Cord")
    P.box((0, 0.8, 0), (4.4, 1.6, 2.0))
    return P


# ----------------------------------------------------------------------------------------------------------------------
def shrine_stone(name="JG_Shrine_Stone_H1", seed=501):
    """The East Shrine: a carved plinth with a moulded edge and recessed panels, four round fluted pillars with leaf capitals, a back slab carved with a coil, a layered
    shingle gable with curled ridge ends and bargeboards, a sapling and roots growing over it. Floor 2.0."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    fl = 2.0
    # plinth: two steps (collider boxes are the first pass's), a moulded cornice on each, corner blocks, step nosing, recessed panels
    P.put(C.chunk((0, 0.5, -0.4), (8.4, 1.0, 7.2), seed, 0.012), stone_mat(seed))
    P.put(C.chunk((0, 1.5, 0.4), (6.4, 1.0, 5.6), seed + 1, 0.012), stone_mat(seed + 1))
    P.box((0, 0.5, -0.4), (8.4, 1.0, 7.2))
    P.box((0, 1.5, 0.4), (6.4, 1.0, 5.6))
    P.put(C.chunk((0, 0.94, -0.4), (8.7, 0.18, 7.5), seed + 2, 0.01), "StoneDark")       # the first step's moulded edge
    P.put(C.chunk((0, 1.94, 0.4), (6.7, 0.18, 5.9), seed + 3, 0.01), "StoneDark")        # the second's
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.chunk((sx * 4.0, 0.45, -0.4 + sz * 3.4), (0.9, 1.0, 0.9), seed + 4 + sx + 2 * sz, 0.03), "Stone")
    for k in range(3):                                                                    # recessed panels on the front face of the first step (z = -4.0)
        P.put(C.chunk((-2.4 + k * 2.4, 0.5, -4.02), (1.7, 0.55, 0.22), seed + 10 + k, 0.01), "StoneDark")
    P.put(C.chunk((0.0, 1.5, -2.42), (3.2, 0.5, 0.22), seed + 14, 0.01), "StoneDark")
    P.put(C.chunk((0, 0.99, -4.25), (3.6, 0.16, 0.5), seed + 15, 0.01), "Stone")         # a worn nosing stone at the middle
    # four round pillars (fluted, tapering, a base and a leaf capital); the first pass's post boxes
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 2.2, 0.4 + sz * 1.9
            P.put(K.fluted_column(3.9, 0.36, 0.3, flutes=6, seg=12, entasis=0.04, base=True, rings=2), stone_mat(seed + 20 + sx), t=(x, fl, z))
            leaf_cap(P, (x, fl + 3.9, z), 0.3, seed + 30 + sx + 2 * sz)
            P.box((x, fl + 2.1, z), (0.7, 4.2, 0.7))
    # back slab carved with a coil; side slabs as low walls with a notched top
    P.put(C.chunk((0, fl + 1.8, 2.3), (4.0, 3.6, 0.5), seed + 40, 0.02), "StoneDark")
    P.box((0, fl + 1.8, 2.3), (4.0, 3.6, 0.5))
    pts = [(math.cos(a) * (0.9 - 0.09 * a / 1.6), fl + 2.0 + math.sin(a) * (0.9 - 0.09 * a / 1.6), 2.0) for a in [t * 0.7 for t in range(0, 16)]]
    P.put(C.tube(pts, 0.14, 0.1, 4, per=1, up=(0, 0, 1)), "Stone")
    for sx in (-1, 1):
        P.put(C.chunk((sx * 2.2, fl + 1.0, 0.4), (0.4, 2.0, 3.0), seed + 42 + sx, 0.02), "StoneDark")
        P.put(C.chunk((sx * 2.2, fl + 2.05, 1.2), (0.45, 0.2, 1.2), seed + 44 + sx, 0.05), "Stone")
        P.box((sx * 2.2, fl + 1.0, 0.4), (0.4, 2.0, 3.0))
    # the roof: eight overlapping rows of boards on each slope with a concave profile, a ridge beam, curled ridge ends, bargeboards, a moss mantle
    for sx in (-1, 1):                                            # wall plates on the pillar heads carry the roof
        P.put(S.bar((sx * 2.2, fl + 4.62, -1.85), (sx * 2.2, fl + 4.62, 2.5), 0.5, 0.3), "Timber")
    P.put(S.bar((-2.4, fl + 4.72, -1.5), (2.4, fl + 4.72, -1.5), 0.4, 0.26), "Timber")
    K.shingle_rows(P, (0.0, fl + 4.4, 0.4), 4.6, 6.2, 1.5, 8, 0.2, 0.0, seed + 50, "Shingle", 0.9, True, 0.35)
    P.put(C.tube([(0.0, fl + 5.95, -3.0), (0.0, fl + 5.95, 3.8)], 0.2, 0.2, 6, per=1), "Timber")
    K.curl(P, (0.0, fl + 5.95, 3.8), (0.0, 0.3, 1.0), 0.16, 1.3, 0.5, "Timber")
    K.curl(P, (0.0, fl + 5.95, -3.0), (0.0, 0.3, -1.0), 0.16, 1.3, 0.5, "Timber")
    for sx in (-1, 1):
        P.put(S.bar((sx * 0.1, fl + 5.95, -3.0), (sx * 3.3, fl + 4.35, -3.0), 0.18, 0.3), "Timber")     # bargeboards, front gable
        P.put(S.bar((sx * 0.1, fl + 5.95, 3.8), (sx * 3.3, fl + 4.35, 3.8), 0.18, 0.3), "Timber")
    # the altar slab and bowl, a cord across the front with leaf tassels
    P.put(C.chunk((0, fl + 0.6, 1.4), (2.6, 0.6, 1.2), seed + 60, 0.02), "Stone")
    P.put(C.lathe([(0.0, fl + 0.9), (0.55, fl + 0.95), (0.5, fl + 1.2), (0.0, fl + 1.15)], 8, c=(0, 0, 1.4)), "RockDark")
    P.put(C.ellipsoid((0, fl + 1.2, 1.4), (0.2, 0.12, 0.2), 6, 3), "GlowAmber")
    P.put(C.tube([(-2.2, fl + 3.7, -1.5), (-1.1, fl + 3.35, -1.6), (0, fl + 3.3, -1.6), (1.1, fl + 3.35, -1.6), (2.2, fl + 3.7, -1.5)], 0.07, None, 3, per=2), "Cord")
    for x in (-0.9, 0.0, 0.9):
        P.put(C.blade((x, fl + 3.3, -1.6), (0.0, -1.0, 0.0), 0.7, 0.22, droop=0.0, thick=0.04, segs=1, up=(0, 0, 1)), "LeafMid")
    # a sapling growing out of the back corner, its roots over the back slab and the roof
    P.put(C.tube([(1.6, fl + 0.2, 2.9), (1.8, fl + 3.0, 3.1), (2.2, fl + 6.0, 3.2), (2.5, fl + 8.0, 3.0)], lambda t: 0.3 - 0.14 * t, None, 6, per=3, wob=0.08, seed=seed), "Trunk")
    P.put(C.leaf_tier((0, 0, 0), 1.6, 0.9, seg=10, lobes=4, ruffle=0.2, droop=0.5, seed=seed + 2, under=0.4, bump=0.2), lambda n, c: "LeafMid" if n[1] > -0.1 else "LeafDeep", t=(2.5, fl + 8.0, 3.0))
    for k in range(2):
        P.put(C.tube([(1.7, fl + 0.4, 2.9), (1.2 - k * 0.8, fl + 1.5, 2.6), (0.4 - k * 1.3, fl + 3.2, 2.4)], 0.1, 0.06, 4, per=1), "Root")
    return P


# ----------------------------------------------------------------------------------------------------------------------
def shrine_hall(name="JG_Shrine_HallRuin_H2", seed=511):
    """The Old Grove hall: broken ashlar courses along the platform's edge, a stair with carved cheeks, six fluted pillars (some snapped, one fallen into drums), a back wall with a
    voussoir window and a fallen lintel, side walls with jagged tops, a rafter frame with a sagging ridge and a few shingle rows left, a tree growing through the roof, roots everywhere.
    Floor 3.0."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    fl = 3.0
    P.put(C.chunk((0, fl / 2 - 0.2, 1.0), (18.0, fl + 0.4, 13.0), seed, 0.012), stone_mat(seed, -0.2))
    P.box((0, fl / 2, 1.0), (18.0, fl, 13.0))
    # the platform's edge: a moulded plinth course and a row of ashlar blocks with gaps, some tilted, some fallen outward
    for side, (cx, cz, ln, yaw) in enumerate(((0.0, -5.7, 17.4, 0.0), (0.0, 7.7, 17.4, 0.0), (-8.7, 1.0, 12.4, math.pi / 2), (8.7, 1.0, 12.4, math.pi / 2))):
        n = int(ln / 1.9)
        for k in range(n):
            if rnd.random() < 0.28:
                continue
            u = -ln / 2 + (k + 0.5) * ln / n
            x, z = (cx + u, cz) if side < 2 else (cx, cz + u)
            P.put(C.chunk((x, fl + 0.18, z), (ln / n - 0.1, 0.42, 0.7), seed + 10 * side + k, 0.04, yaw=yaw if side >= 2 else 0.0, chip=0.15, tilt=((0, 0, 1), rnd.uniform(-0.05, 0.05))), stone_mat(seed + k + 30 * side))
    # the stair: two steps with carved cheek walls and a broken balustrade stub
    for k, (top, z0, wd) in enumerate(((1.0, -9.5, 7.2), (2.0, -7.5, 7.0))):
        P.put(C.box((0, top / 2 - 0.1, z0 + 1.0), (wd, top + 0.2, 2.0)), stone_mat(seed + k))
        P.box((0, top / 2, z0 + 1.0), (wd, top, 2.0))
        P.put(C.chunk((0, top - 0.04, z0 + 0.15), (wd + 0.2, 0.14, 0.34), seed + 3 + k, 0.01), "StoneDark")      # a worn nosing
    for sx in (-1, 1):
        P.put(C.chunk((sx * 3.95, 1.0, -7.8), (0.8, 2.2, 5.0), seed + 8 + sx, 0.04, tilt=((1, 0, 0), 0.0)), "StoneDark")
        P.put(C.chunk((sx * 3.95, 2.35, -8.5), (0.9, 0.55, 1.3), seed + 10 + sx, 0.12, yaw=0.3 * sx), "Stone")
        P.put(C.chunk((sx * 3.95, 2.0, -6.0), (0.9, 0.9, 0.9), seed + 12 + sx, 0.1), stone_mat(seed + 14 + sx))
    # the front row of pillars at the first pass's positions and heights (0 = fallen)
    heights = [4.2, 5.6, 0.0, 2.2, 5.0, 3.0]
    for i, x in enumerate((-7.0, -4.2, -1.4, 1.4, 4.2, 7.0)):
        P.put(C.lathe([(0.0, fl - 0.3), (0.77, fl - 0.3), (0.77, fl + 0.2), (0.7, fl + 0.6), (0.0, fl + 0.6)], 6), stone_mat(seed + i), t=(x, 0.0, -4.0))
        h = heights[i]
        if h > 0.5:
            col = K.fluted_column(h - 0.6, 0.45, 0.36, flutes=6, seg=12, entasis=0.05, base=False, rings=2)
            P.put(col, stone_mat(seed + 40 + i, -0.2), t=(x, fl + 0.5, -4.0))
            top = fl + 0.5 + h - 0.6
            if h > 4.0:
                leaf_cap(P, (x, top, -4.0), 0.36, seed + 50 + i)
            else:
                P.put(C.chunk((x + 0.05, top, -4.0), (0.95, 0.4, 0.9), seed + 60 + i, 0.22, tilt=((1, 0, 0), 0.4), chip=0.3), "StoneDark")      # a jagged break
            P.box((x, fl + 0.4 + h / 2, -4.0), (0.8, h, 0.8))
        else:
            for k, (dx, dz, ln) in enumerate(((0.0, 0.0, 1.3), (1.1, 1.5, 1.2))):
                d = C.lathe([(0.0, -ln / 2), (0.45, -ln / 2), (0.43, 0.0), (0.45, ln / 2), (0.0, ln / 2)], 8)
                P.put(d, stone_mat(seed + 70 + k), t=(x + dx, fl + 0.45, -4.0 + dz), tilt=((1, 0, 0), math.pi / 2 + 0.05 * k), yaw=0.3 * k)
    # the back wall: ashlar courses with an arched window (voussoirs), a fallen lintel; side walls stepped and jagged
    P.put(C.chunk((0, fl + 2.2, 6.6), (16.6, 4.4, 0.8), seed + 80, 0.02, chip=0.35), "StoneDark")
    P.box((0, fl + 2.0, 6.6), (16.6, 4.0, 0.8))
    for k in range(4):
        y = fl + 0.45 + k * 1.1
        for j in range(8):
            x = -7.4 + j * 2.1 + (0.5 if k % 2 else 0.0)
            if abs(x) < 1.7 and 1.0 < k < 4:
                continue
            if rnd.random() < 0.15 or (k == 4 and rnd.random() < 0.5):
                continue
            P.put(C.chunk((x, y, 6.15), (1.95, 0.86, 0.34), seed + 100 + k * 9 + j, 0.04), stone_mat(seed + 100 + k * 9 + j))
    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        P.put(C.chunk((math.cos(a) * 1.7, fl + 2.9 + math.sin(a) * 1.3, 6.15 + 0.04 * (k % 2)), (0.65, 0.6, 0.4 + 0.1 * (k % 2)), seed + 200 + k, 0.04, tilt=((0, 0, 1), math.pi / 2 - a)), "Stone")
    P.put(C.chunk((2.4, fl + 0.3, 3.2), (3.4, 0.7, 0.9), seed + 210, 0.06, yaw=0.55, tilt=((1, 0, 0), 0.11)), "Stone")       # the fallen lintel
    for sx in (-1, 1):
        P.put(C.chunk((sx * 8.5, fl + 1.45, 1.8), (0.8, 3.2, 9.0), seed + 220 + sx, 0.02, chip=0.4), "StoneDark")
        P.box((sx * 8.5, fl + 1.5, 1.8), (0.8, 3.0, 9.0))
        for k in range(4):
            P.put(C.chunk((sx * 8.5, fl + 3.1 + 0.3 * (k % 2), -1.7 + k * 2.6), (0.9, 0.5 + 0.4 * (k % 3), 1.4), seed + 230 + k + sx, 0.12), stone_mat(seed + 240 + k))
    # the rafter frame: tied beams across, rafters up to a sagging ridge, a few shingle rows, lashings; the front half has fallen across the floor
    for z in (0.8, 3.4, 6.0):
        P.put(S.bar((-8.6, fl + 5.5, z), (8.6, fl + 5.55, z), 0.4, 0.5), "Timber")
        for sx in (-1, 1):
            P.put(S.bar((sx * 8.6, fl + 5.5, z), (sx * 0.4, fl + 8.6 - (0.4 if z == 3.4 else 0.0), z), 0.3, 0.4), "Timber")
        if z == 3.4:
            for sx in (-8.0, 8.0):
                K.cord_wrap(P, (sx, fl + 5.5, z), 0.22, (1, 0, 0), 1, 0.26)
    for sx in (-1, 1):
        for z in (0.8, 3.4, 6.0):
            P.put(C.tube([(sx * 8.6, fl + 2.6, z), (sx * 8.6, fl + 5.6, z)], 0.3, 0.26, 5, per=1), "Timber")
    P.put(S.bar((0.0, fl + 8.6, 0.8), (0.0, fl + 8.2, 6.0), 0.3, 0.4), "Timber")
    K.shingle_rows(P, (0.0, fl + 5.5, 3.4), 16.6, 5.2, 2.85, 5, 0.16, 0.0, seed + 250, "Shingle", 0.0, True, 0.3)
    P.put(C.chunk((2.6, fl + 0.3, -1.2), (6.0, 0.5, 3.0), seed + 260, 0.05, tilt=((0, 0, 1), 0.2), yaw=0.3), "Shingle")
    P.put(S.bar((-5.0, fl + 0.15, -1.5), (1.0, fl + 0.3, 0.6), 0.5, 0.5), "Timber")
    # rubble, moss, a tree growing up through the roof gap and roots over the back wall
    for k in range(7):
        P.put(C.chunk((rnd.uniform(-6, 6), fl + 0.25, rnd.uniform(-2.5, 4)), (rnd.uniform(0.5, 1.2), 0.5, rnd.uniform(0.5, 1.0)), seed + 270 + k, 0.2, yaw=rnd.uniform(0, 3)), stone_mat(seed + 280 + k))
    P.put(C.tube([(-3.6, fl + 0.2, 3.0), (-3.4, fl + 3.0, 3.1), (-3.0, fl + 6.5, 3.3), (-2.8, fl + 10.0, 3.2)], lambda t: 0.55 - 0.3 * t, None, 7, per=3, wob=0.06, seed=seed), "Trunk")
    P.put(C.leaf_tier((0, 0, 0), 3.4, 1.8, seg=12, lobes=5, ruffle=0.2, droop=0.5, seed=seed + 4, under=0.4, bump=0.2), lambda n, c: "LeafMid" if n[1] > -0.1 else "LeafDeep", t=(-2.8, fl + 10.0, 3.2))
    for k in range(3):
        x = -5.5 + k * 5.5
        P.put(C.tube([(x, fl + 4.6, 6.5), (x + 0.3, fl + 3.0, 6.2), (x + 0.2, fl + 1.2, 6.0), (x + 0.6, fl + 0.3, 5.5)], 0.16, 0.08, 4, per=1), "Root")
    return P


# ----------------------------------------------------------------------------------------------------------------------
def hermitage_annex(name="JG_Hermitage_Annex_A1", seed=561):
    """A lean-to of lashed posts and tied beams, woven wattle walls, a layered thatch roof with a ragged hem, a plank floor, firewood, a lidded jar, a drying rack hung with herbs, a
    herb bed fenced with tied rails and stakes. Floor box 9 x 0.6 x 6 (top 0.5); posts at the first pass's places."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    # plank floor: six boards, a stone footing under each post
    for k in range(6):
        z = -2.5 + k * 1.0
        P.put(C.box((0, 0.2, z), (9.0, 0.6, 0.94)), "Plank" if k % 2 else "PlankDark")
    for x in (-3.6, 0.0, 3.6):                                   # three sleepers carry the boards
        P.put(C.box((x, 0.02, 0.0), (0.5, 0.44, 6.0)), "Timber")
    posts = ((-4.2, -2.6, 4.4), (4.2, -2.6, 4.4), (-4.2, 2.6, 3.0), (4.2, 2.6, 3.0))
    for (x, z, h) in posts:
        P.put(C.tube([(x, 0.0, z), (x * 1.0, h, z)], 0.28, 0.24, 7, per=1), "Timber")
        P.put(C.lathe([(0.0, -0.2), (0.55, -0.2), (0.5, 0.3), (0.0, 0.3)], 6, c=(x, 0.4, z)), stone_mat(seed))
        if z < 0:
            K.cord_wrap(P, (x, h - 0.4, z), 0.28, (0, 1, 0), 1, 0.3)
    for sx in (-1, 1):                                            # the first pass's proxies, unchanged: two posts a side, then the floor
        P.box((sx * 4.2, 2.0, -2.6), (0.6, 4.0, 0.6))
        P.box((sx * 4.2, 1.5, 2.6), (0.6, 3.0, 0.6))
    P.box((0, 0.3, 0), (9.0, 0.6, 6.0))
    # tied beams: the back and front plates, side plates, a ridge-pole; cross braces lashed
    P.put(S.bar((-4.4, 4.3, -2.6), (4.4, 4.3, -2.6), 0.4, 0.5), "Timber")
    P.put(S.bar((-4.4, 3.0, 2.6), (4.4, 3.0, 2.6), 0.4, 0.5), "Timber")
    for sx in (-1, 1):
        P.put(S.bar((sx * 4.2, 4.3, -2.6), (sx * 4.2, 3.0, 2.6), 0.36, 0.44), "Timber")
        P.put(S.bar((sx * 4.2, 0.6, -2.6), (sx * 4.2, 3.6, -0.4), 0.2, 0.2), "Timber")
    for x in (-2.8, -0.9, 1.0, 2.9):
        P.put(S.bar((x, 4.3, -2.6), (x, 3.0, 2.6), 0.22, 0.28), "Timber")
    # woven wattle: the back wall and the left side
    K.woven_panel(P, -3.9, 3.9, 0.6, 4.2, -2.6, rods=10, bands=4, seed=seed, axis="x")
    K.woven_panel(P, -2.3, 2.3, 0.6, 3.4, -4.2, rods=7, bands=4, seed=seed + 1, axis="z")
    # the roof: a single pitch falling to the front, eight rows of thatch laid on from the eave up, each with a ragged hem of grass blades
    for r in range(8):
        t = r / 7.0
        z = 2.9 - t * 5.5
        y = 3.05 + t * 1.45 + 0.12
        row = C.chunk((0, 0, 0), (10.6, 0.34, 1.05), seed + 40 + r, 0.04, tilt=((1, 0, 0), 0.23))
        P.put(row, lambda n, c, rr=r: "Moss" if n[1] > 0.7 and C.fbm3(c[0] * 0.3, c[2] * 0.3, rr, seed, 2) > 0.42 else "GrassPale", t=(0.0, y, z))
        for k in range(5):
            x = -4.4 + k * 2.2 + rnd.uniform(-0.1, 0.1)
            P.put(C.blade((x, y - 0.12, z + 0.45), (0.0, -0.8, 0.5), rnd.uniform(0.5, 0.9), 0.2, droop=0.0, thick=0.04, segs=1, up=(0, 0, 1)), "Grass" if k % 3 else "GrassPale")
    P.put(C.lathe([(0.0, -4.4), (0.34, -4.3), (0.38, -4.0), (0.34, 4.3), (0.0, 4.4)], 8), "GrassPale", t=(0.0, 4.55, -2.7), tilt=((0, 0, 1), math.pi / 2))
    # firewood (rests on the floor, rows touching), a lidded jar with a cord, a drying rack hung with herbs
    for r_ in range(2):
        for k in range(4 - r_):
            P.put(C.tube([(-3.8 + k * 0.62 + r_ * 0.31, 0.78 + r_ * 0.42, -2.2), (-3.8 + k * 0.62 + r_ * 0.31, 0.78 + r_ * 0.42, -0.4)], 0.3, 0.3, 5, per=1), "Timber")
    P.put(C.lathe([(0.0, 0.5), (0.5, 0.5), (0.78, 1.0), (0.84, 1.6), (0.6, 2.0), (0.4, 2.15), (0.0, 2.15)], 8, c=(3.0, 0, -1.4)), "Soil")
    P.put(C.lathe([(0.0, 2.1), (0.5, 2.1), (0.5, 2.3), (0.15, 2.4), (0.0, 2.45)], 8, c=(3.0, 0, -1.4)), "PlankDark")
    P.put(C.tube([(3.4, 1.7, -1.4), (3.5, 1.2, -1.1), (3.2, 0.9, -1.0)], 0.05, None, 4, per=2), "Cord")
    for x in (-1.0, 1.6):
        P.put(S.bar((x, 2.2, 2.2), (x, 0.5, 2.2), 0.2, 0.2), "Timber")
    P.put(S.bar((-1.0, 2.2, 2.2), (1.6, 2.2, 2.2), 0.18, 0.18), "Timber")
    for k in range(5):
        x = -0.7 + k * 0.5
        P.put(C.tube([(x, 2.2, 2.2), (x, 1.7, 2.2)], 0.025, 0.02, 3, per=1), "Cord")
        for a in (0.0, 2.1, 4.2):
            P.put(C.blade((x, 1.72, 2.2), (math.cos(a) * 0.3, -0.9, math.sin(a) * 0.3), 0.6, 0.16, droop=0.1, thick=0.03, segs=1), "Fern")
    # the herb bed in front: a frame of tied rails and stakes, soil, plants
    bx, bz = 0.0, 6.6
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.tube([(bx + sx * 3.2, 0.0, bz + sz * 1.5), (bx + sx * 3.2, 1.3, bz + sz * 1.5)], 0.12, 0.1, 5, per=1), "Timber")
    for sz in (-1, 1):
        P.put(S.bar((bx - 3.2, 0.7, bz + sz * 1.5), (bx + 3.2, 0.7, bz + sz * 1.5), 0.3, 0.5), "Timber")
    for sx in (-1, 1):
        P.put(S.bar((bx + sx * 3.2, 0.7, bz - 1.5), (bx + sx * 3.2, 0.7, bz + 1.5), 0.3, 0.5), "Timber")
    P.put(C.box((bx, 0.3, bz), (6.1, 0.7, 2.9)), "Soil")
    for k in range(6):
        a = TAU * k / 6
        P.put(C.blade((bx - 2.6 + (k % 5) * 1.3, 0.6, bz - 0.7 + (k // 5) * 1.4), (math.cos(a) * 0.5, 1.0, math.sin(a) * 0.5), rnd.uniform(0.9, 1.5), 0.3, droop=0.4, thick=0.04, segs=2), "FernBright")
    return P


# ----------------------------------------------------------------------------------------------------------------------
def lookout(name="JG_Lookout_Tower_T1", seed=571):
    """A lashed timber tower: four leaning posts on stone footings with cord at every joint, X braces, a plank platform at 12 with a woven-wattle railing, a hanging basket and lantern,
    a hip of thatch with a layered skirt and a curled finial, a stair of twelve one-stud steps with a rope handrail on posts, and a net under the platform's edge."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    H = 12.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.tube([(sx * 4.0, -0.5, sz * 4.0), (sx * 3.6, H, sz * 3.6)], 0.5, 0.42, 7, per=1), "Timber")
            P.put(C.lathe([(0.0, -0.4), (1.0, -0.4), (0.9, 0.4), (0.0, 0.4)], 6, c=(sx * 4.0, 0, sz * 4.0)), stone_mat(seed + sx))
            P.box((sx * 3.8, 6.0, sz * 3.8), (0.8, 12.0, 0.8))
            for y in (3.0, 10.9):
                xx = sx * (4.0 - 0.4 * (y + 0.5) / (H + 0.5))
                zz = sz * (4.0 - 0.4 * (y + 0.5) / (H + 0.5))
                K.cord_wrap(P, (xx, y, zz), 0.5 - 0.08 * y / H, (0, 1, 0), 1, 0.36)
    for lvl in (3.5, 7.5):
        for sx in (-1, 1):
            P.put(S.bar((sx * 3.9, lvl, -3.9), (sx * 3.7, lvl + 3.6, 3.9), 0.28, 0.28), "Timber")
            P.put(S.bar((sx * 3.7, lvl + 3.6, -3.9), (sx * 3.9, lvl, 3.9), 0.28, 0.28), "Timber")
            P.put(S.bar((-3.9, lvl, sx * 3.9), (3.9, lvl + 3.6, sx * 3.9), 0.22, 0.24), "Timber")
    for lvl in (3.5, 7.5, 11.0):                                  # tie beams round the tower at each level
        for sx in (-1, 1):
            P.put(S.bar((sx * (3.9 - 0.03 * lvl), lvl, -3.9), (sx * (3.9 - 0.03 * lvl), lvl, 3.9), 0.3, 0.3), "Timber")
            P.put(S.bar((-3.9, lvl, sx * (3.9 - 0.03 * lvl)), (3.9, lvl, sx * (3.9 - 0.03 * lvl)), 0.3, 0.3), "Timber")
    # the platform: nine boards, a rim beam, the railing with woven wattle between posts
    for k in range(9):
        P.put(C.box((0, H - 0.25, -4.0 + k * 1.0), (8.6, 0.5, 0.94)), "Plank" if k % 2 else "PlankDark")
    for x in (-3.0, 0.0, 3.0):                                   # joists under the boards
        P.put(C.box((x, H - 0.55, 0.0), (0.5, 0.5, 8.6)), "Timber")
    P.box((0, H - 0.5, 0), (8.6, 1.0, 8.6))
    for sx in (-1, 1):
        P.put(S.bar((sx * 4.1, H + 1.1, -4.1), (sx * 4.1, H + 1.1, 4.1), 0.2, 0.26), "Timber")
        P.put(S.bar((-4.1, H + 1.1, sx * 4.1), (4.1, H + 1.1, sx * 4.1), 0.2, 0.26), "Timber")
        P.put(S.bar((sx * 4.1, H + 0.35, -4.1), (sx * 4.1, H + 0.35, 4.1), 0.16, 0.2), "Timber")
        P.put(S.bar((-4.1, H + 0.35, sx * 4.1), (4.1, H + 0.35, sx * 4.1), 0.16, 0.2), "Timber")
        P.box((sx * 4.1, H + 0.55, 0), (0.3, 1.1, 8.2))
        P.box((0, H + 0.55, sx * 4.1), (8.2, 1.1, 0.3))
        K.woven_panel(P, -4.0, 4.0, H + 0.4, H + 1.05, sx * 4.1, rods=6, bands=2, rod_r=0.05, seed=seed + sx, axis="x")
        K.woven_panel(P, -4.0, 4.0, H + 0.4, H + 1.05, sx * 4.1, rods=6, bands=2, rod_r=0.05, seed=seed + 3 + sx, axis="z")
    # the stair: twelve steps of rise 1, tread 2, along the +x side from z = 19 to the landing at z = -3, two sloped stringers, a rope handrail on posts
    for k in range(12):
        top = k + 1
        z = 19.0 - 2.0 * k - 1.0
        P.put(C.box((6.2, top - 0.2, z), (3.2, 0.4, 2.0)), "Plank")
        P.box((6.2, top - 0.5, z), (3.2, 1.0, 2.0))
    for sx in (-1, 1):
        P.put(S.bar((6.2 + sx * 1.3, 0.0, 19.0), (6.2 + sx * 1.3, 11.6, -3.0), 0.4, 0.7), "Timber")
    P.put(C.box((5.4, H - 0.27, -3.4), (3.4, 0.5, 2.4)), "Plank")
    P.put(C.box((6.2, 0.5, 19.6), (3.0, 1.0, 1.2)), stone_mat(seed + 2))
    for k in range(0, 12, 3):
        top = k + 1
        z = 19.0 - 2.0 * k - 1.0
        P.put(C.tube([(7.7, top - 0.2, z), (7.7, top + 1.7, z)], 0.1, 0.09, 5, per=1), "Timber")
    P.put(C.tube([(7.7, 2.7, 17.0), (7.7, 5.4, 11.0), (7.7, 8.5, 5.0), (7.7, 11.6, -1.0)], 0.07, 0.07, 4, per=3), "Cord")
    # the roof: four posts, a hip of thatch (layered rows with a skirt), a ridge knot with a curled finial, a hanging basket and lantern, a net under the platform edge
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.tube([(sx * 3.2, H, sz * 3.2), (sx * 3.2, H + 5.5, sz * 3.2)], 0.2, 0.17, 6, per=1), "Timber")
            if sx == sz:
                K.cord_wrap(P, (sx * 3.2, H + 5.2, sz * 3.2), 0.2, (0, 1, 0), 1, 0.26)
    # the roof: one hip of thatch with a straight, slightly bellied slope (no upswept eave), laid in six small courses (a 0.1 step each), a ragged hem of blades
    y0, h0, rise = H + 5.3, 5.3, 2.4
    prof = [(h0 * 1.4142, y0), (h0 * 1.4142, y0 + 0.4)]
    n_c = 6
    for i in range(n_c):
        u = 1.0 - (i + 1) / float(n_c)
        h = h0 * u
        y = y0 + 0.4 + rise * (1.0 - u) ** 0.9
        prof.append(((h + 0.1) * 1.4142, y - 0.18))
        prof.append((h * 1.4142 if i < n_c - 1 else 0.0, y))
    P.put(C.lathe(prof, 4, phase=math.pi / 4), lambda n, c: "Moss" if n[1] > 0.5 and C.fbm3(c[0] * 0.35, c[2] * 0.35, 1.0, seed, 2) > 0.2 else "GrassPale")
    apex = y0 + 0.4 + rise
    for side in range(4):
        for j in range(3):
            tt = -3.3 + j * 3.3 + rnd.uniform(-0.2, 0.2)
            ax, az = ((tt, -h0), (h0, tt), (tt, h0), (-h0, tt))[side]
            nx, nz = ((0, -1), (1, 0), (0, 1), (-1, 0))[side]
            P.put(C.blade((ax - nx * 0.15, y0 + 0.28, az - nz * 0.15), (nx * 0.35, -0.9, nz * 0.35), rnd.uniform(0.7, 1.2), 0.5, droop=0.0, thick=0.05, segs=1), "Grass" if j % 2 else "GrassPale")
    P.put(C.tube([(0.0, H + 5.4, 0.0), (0.0, apex + 0.25, 0.0)], 0.32, 0.18, 6, per=1), "Timber")      # the king post the thatch is laid round
    K.curl(P, (0.0, apex + 0.2, 0.0), (0.2, 1.0, 0.1), 0.18, 1.3, 0.5, "Timber")
    P.put(C.tube([(1.8, H + 5.4, 1.8), (1.8, H + 4.2, 1.8)], 0.03, None, 3, per=1), "Cord")
    P.put(C.lathe([(0.0, 0.0), (0.4, 0.0), (0.5, 0.35), (0.0, 0.35)], 8), "PlankDark", t=(1.8, H + 3.9, 1.8))
    P.put(C.tube([(-1.8, H + 5.4, -1.8), (-1.8, H + 4.6, -1.8)], 0.03, None, 3, per=1), "Cord")
    P.put(C.ellipsoid((-1.8, H + 4.4, -1.8), (0.25, 0.3, 0.25), 6, 4), "GlowAmber")
    for sx in (-1, 1):
        P.put(C.tube([(sx * 4.2, H - 0.4, -4.0), (sx * 3.9, H - 2.2, -2.0), (sx * 3.8, H - 3.4, 0.0), (sx * 3.9, H - 2.2, 2.0), (sx * 4.2, H - 0.4, 4.0)], 0.06, 0.06, 4, per=3), "Cord")
    return P


def build_all():
    out = {}
    out["JG_Shrine_Stone_H1"] = shrine_stone()
    out["JG_Shrine_HallRuin_H2"] = shrine_hall()
    out["JG_Lantern_Sprout_L1"] = lantern("JG_Lantern_Sprout_L1", 521, True)
    out["JG_Lantern_Sprout_L2"] = lantern("JG_Lantern_Sprout_L2", 531, False)
    out["JG_Hermitage_Annex_A1"] = hermitage_annex()
    out["JG_Lookout_Tower_T1"] = lookout()
    out["JG_Waymarker_W1"] = waymarker("JG_Waymarker_W1", 561, 0)
    out["JG_Waymarker_W2"] = waymarker("JG_Waymarker_W2", 562, 1)
    out["JG_Waymarker_W3"] = waymarker("JG_Waymarker_W3", 563, 2)
    out["JG_Offering_Table_O1"] = offering_table()
    out["JG_Ruin_Column_C1"] = ruin_column("JG_Ruin_Column_C1", 571, 0)
    out["JG_Ruin_Column_C2"] = ruin_column("JG_Ruin_Column_C2", 572, 1)
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  box %s -> %s  colliders %d" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), len(p.colliders)))

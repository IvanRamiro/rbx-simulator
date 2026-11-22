"""jade_lib_structures: Jade Grove's built things (2026-11-22): weathered timber and moss-grown stone in a Japanese, Korean and original-fantasy vernacular
(plain steep gables with deep eaves, plank and bark-shingle roofs, round stone footings): no Chinese pagodas, upswept eaves, dragons, lanterns or lettering.

  JG_Shrine_Stone_H1        a small stone shrine: two stone steps, four posts, a roofed altar slab with an offering bowl      (floor 2.0)
  JG_Shrine_HallRuin_H2     a larger moss-grown hall ruin: a raised platform, a stair, broken posts, a half-fallen roof       (floor 3.0)
  JG_Lantern_Sprout_L1 / L2 a stone lantern of its own design: a short stone stem, a lamp box with an amber core, a cap of two leaf slabs (tall and short)
  JG_Gate_Branch_G1         a grove gate with no torii in it: two mossy posts and two living branches crossed into an arch
  JG_Stair_Stone_S4 / S8    weathered stairs, every riser exactly 1 stud, treads 2 deep, 8 wide, mossy cheeks (climb toward +z)
  JG_Path_Slab_P1 / P2 / P3 stepping slabs (round, long, irregular), sunk in the ground; decoration only
  JG_Hermitage_Annex_A1     a lean-to shed with a plank floor, firewood, a water jar and a raised herb bed, to stand beside the Sage's hermitage
  JG_Lookout_Tower_T1       a timber lookout: a stair of 12 one-stud risers up to an open platform 12 studs high with rails and a small shingle roof
  JG_Waymarker_W1 / W2 / W3 carved waymarker stones (bands and a spiral, no letters, no arrows)
  JG_Offering_Table_O1      a spirit offering table: a stone slab on two blocks, a bowl, a cairn, an incense stand with an amber point
  JG_Ruin_Column_C1 / C2    a broken round pillar and a fallen drum for the Ruin Court
  JG_Hidden_HollowTrunk_X1  a giant dead trunk, hollow, with an entrance and a floor and an inner niche (the hollow-tree shrine room)
  JG_Hidden_PavilionRuin_X2 a small pavilion in ruin: a stone floor, four footings, two standing posts, a fallen ridge

Every floor height and riser is a whole or half stud (the numeric check lists them). Colliders are boxes: steps, floors, posts, walls; roofs and
leaves never collide.
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU


# ----------------------------------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------------------------------
def ext(profile, z0, z1, c=(0, 0, 0), yaw=0.0):
    """A convex polygon [(x, y), ...] in the xy plane extruded along z from z0 to z1 (a gable, a beam end, a wedge)."""
    g = C.Geo()
    cs, sn = math.cos(yaw), math.sin(yaw)

    def P(x, y, z):
        return (c[0] + x * cs + z * sn, c[1] + y, c[2] - x * sn + z * cs)
    n = len(profile)
    cx = sum(p[0] for p in profile) / n
    cy = sum(p[1] for p in profile) / n
    for i in range(n):
        a, b = profile[i], profile[(i + 1) % n]
        g.face(P(a[0], a[1], z0), P(b[0], b[1], z0), P(b[0], b[1], z1), P(a[0], a[1], z1))
        g.face(P(a[0], a[1], z1), P(b[0], b[1], z1), P(cx, cy, z1))
        g.face(P(b[0], b[1], z0), P(a[0], a[1], z0), P(cx, cy, z0))
    return g


def bar(p0, p1, w, t, up=(0.0, 1.0, 0.0)):
    """A square-sectioned bar from p0 to p1 (w across, t thick)."""
    d = C.vnorm(C.vsub(p1, p0))
    side = C.vnorm(C.vcross(d, up)) if abs(C.vdot(d, up)) < 0.98 else (1.0, 0.0, 0.0)
    nrm = C.vcross(side, d)
    g = C.Geo()
    q = []
    for p in (p0, p1):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q.append((p[0] + side[0] * w / 2 * sx + nrm[0] * t / 2 * sy, p[1] + side[1] * w / 2 * sx + nrm[1] * t / 2 * sy, p[2] + side[2] * w / 2 * sx + nrm[2] * t / 2 * sy))
    for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        g.face(*[q[i] for i in idx])
    return g


def moss_top(seed, thr=-0.1):
    """Stone by what faces look at: moss on soft patches of the upward faces, dark in the low parts."""
    def choose(n, ctr):
        if n[1] > 0.7 and C.fbm3(ctr[0] * 0.3 + seed, ctr[1] * 0.3, ctr[2] * 0.3, seed, 2) > thr:
            return "Moss"
        if ctr[1] < 0.5 and n[1] < 0.6:
            return "StoneDark"
        return "Stone"
    return choose


def post(P, x, z, h, r=0.34, y0=0.0, seed=0, mat="Timber", sides=6):
    P.put(C.tube([(x, y0, z), (x, y0 + h, z)], r, r * 0.92, sides, per=1), mat)


def footing(P, x, z, r=0.62, h=0.5, y0=0.0, seed=0):
    P.put(C.lathe([(0.0, y0 - 0.3), (r * 1.1, y0 - 0.3), (r * 1.1, y0 + h * 0.4), (r, y0 + h), (0.0, y0 + h)], 8), moss_top(seed), t=(x, 0.0, z))


# ----------------------------------------------------------------------------------------------------------------------
# shrines
# ----------------------------------------------------------------------------------------------------------------------
def shrine_stone(name="JG_Shrine_Stone_H1", seed=501):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # two steps (rises of exactly 1) under a 6 x 6 floor at y = 2
    P.put(C.chunk((0, 0.5, -0.4), (8.4, 1.0, 7.2), seed, 0.015), moss_top(seed))
    P.put(C.chunk((0, 1.5, 0.4), (6.4, 1.0, 5.6), seed + 1, 0.015), moss_top(seed + 1))
    P.box((0, 0.5, -0.4), (8.4, 1.0, 7.2))
    P.box((0, 1.5, 0.4), (6.4, 1.0, 5.6))
    # four corner posts of stone, a back slab and two side slabs, a roof of two stone slabs under a moss ridge
    fl = 2.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.chunk((sx * 2.2, fl + 2.1, 0.4 + sz * 1.9), (0.7, 4.2, 0.7), seed + 5 + sx + 2 * sz, 0.03), moss_top(seed + sx))
            P.box((sx * 2.2, fl + 2.1, 0.4 + sz * 1.9), (0.7, 4.2, 0.7))
    P.put(C.chunk((0, fl + 1.8, 2.3), (4.0, 3.6, 0.5), seed + 11, 0.02), "StoneDark")
    P.box((0, fl + 1.8, 2.3), (4.0, 3.6, 0.5))
    for sx in (-1, 1):
        P.put(C.chunk((sx * 2.2, fl + 1.0, 0.4), (0.4, 2.0, 3.0), seed + 12 + sx, 0.02), "StoneDark")
        P.box((sx * 2.2, fl + 1.0, 0.4), (0.4, 2.0, 3.0))
    # the roof: two stone slabs meeting at a ridge, overhanging the front
    for sg in (-1, 1):
        P.put(C.chunk((sg * 1.55, fl + 4.75, 0.5), (3.4, 0.5, 6.4), seed + 20 + sg, 0.01, tilt=((0, 0, 1), -sg * 0.42)), lambda n, c: "Moss" if n[1] > 0.6 and C.fbm3(c[0] * 0.4, c[1], c[2] * 0.4, seed, 2) > -0.2 else "Stone")
    P.put(C.chunk((0, fl + 5.5, 0.5), (0.7, 0.45, 6.6), seed + 23, 0.02), "StoneDark")
    # the altar slab and its bowl, an ember (small Neon accent)
    P.put(C.chunk((0, fl + 0.6, 1.4), (2.6, 0.6, 1.2), seed + 24, 0.02), "Stone")
    P.put(C.lathe([(0.0, fl + 0.9), (0.55, fl + 0.95), (0.5, fl + 1.2), (0.0, fl + 1.15)], 8, c=(0, 0, 1.4)), "RockDark")
    P.put(C.ellipsoid((0, fl + 1.2, 1.4), (0.2, 0.12, 0.2), 6, 3), "GlowAmber")
    # a cord across the front and two hanging tassels (plain rope, no paper)
    P.put(C.tube([(-2.4, fl + 3.9, -1.5), (0, fl + 3.55, -1.6), (2.4, fl + 3.9, -1.5)], 0.09, None, 5, per=4), "Cord")
    return P


def shrine_hall(name="JG_Shrine_HallRuin_H2", seed=511):
    rnd = random.Random(seed)
    P = C.Piece(name)
    fl = 3.0
    # platform 18 x 13 whose top is y = 3; a front stair of three steps (rises 1)
    P.put(C.chunk((0, fl / 2 - 0.2, 1.0), (18.0, fl + 0.4, 13.0), seed, 0.012), moss_top(seed, -0.2))
    P.box((0, fl / 2, 1.0), (18.0, fl, 13.0))
    for k, (top, z0, wd) in enumerate(((1.0, -9.5, 7.2), (2.0, -7.5, 7.0))):
        P.put(C.box((0, top / 2 - 0.1, z0 + 1.0), (wd, top + 0.2, 2.0)), moss_top(seed + k))
        P.box((0, top / 2, z0 + 1.0), (wd, top, 2.0))
    # round footings and posts: the front row, a back wall of stone, two posts standing and four broken
    heights = [4.2, 5.6, 0.0, 2.2, 5.0, 3.0]
    for i, x in enumerate((-7.0, -4.2, -1.4, 1.4, 4.2, 7.0)):
        footing(P, x, -4.0, 0.7, 0.6, fl, seed + i)
        h = heights[i]
        if h > 0.5:
            P.put(C.tube([(x, fl + 0.4, -4.0), (x + 0.05, fl + 0.4 + h, -4.0)], 0.44, 0.38, 8, per=1), "Timber")
            # a broken top: a jagged cap
            P.put(C.chunk((x, fl + 0.4 + h, -4.0), (0.9, 0.35, 0.9), seed + 30 + i, 0.2, tilt=((1, 0, 0), 0.4)), "Timber")
            P.box((x, fl + 0.4 + h / 2, -4.0), (0.8, h, 0.8))
    P.put(C.chunk((0, fl + 2.2, 6.6), (16.6, 4.4, 0.8), seed + 40, 0.02, taper=0.0, chip=0.35), "StoneDark")
    P.box((0, fl + 2.0, 6.6), (16.6, 4.0, 0.8))
    for sx in (-1, 1):
        P.put(C.chunk((sx * 8.5, fl + 1.5, 1.8), (0.8, 3.0, 9.0), seed + 41 + sx, 0.02, chip=0.4), "StoneDark")
        P.box((sx * 8.5, fl + 1.5, 1.8), (0.8, 3.0, 9.0))
    # what is left of the roof: the rear half of a gable on its tie beams, the front half fallen across the floor
    P.put(ext([(-9.4, 0.0), (0.0, 3.4), (9.4, 0.0), (8.6, -0.5), (-8.6, -0.5)], 0.8, 7.6, (0, fl + 6.0, 0)), lambda n, c: "Moss" if n[1] > 0.5 and C.fbm3(c[0] * 0.3, c[1], c[2] * 0.3, seed, 2) > 0.0 else "Shingle")
    P.put(bar((-8.6, fl + 5.6, 0.8), (8.6, fl + 5.6, 0.8), 0.5, 0.6), "Timber")
    P.put(bar((-8.6, fl + 5.6, 7.4), (8.6, fl + 5.6, 7.4), 0.5, 0.6), "Timber")
    P.put(C.chunk((2.6, fl + 0.3, -1.2), (6.0, 0.5, 3.0), seed + 50, 0.05, tilt=((0, 0, 1), 0.2), yaw=0.3), "Shingle")
    P.put(bar((-5.0, fl + 0.15, -1.5), (1.0, fl + 0.3, 0.6), 0.5, 0.5), "Timber")
    P.put(C.chunk((-4.0, fl + 0.3, 3.0), (2.4, 0.6, 1.4), seed + 51, 0.1, yaw=0.5), moss_top(seed + 5))
    return P


# ----------------------------------------------------------------------------------------------------------------------
# lanterns, gate, stairs, slabs
# ----------------------------------------------------------------------------------------------------------------------
def lantern(name, seed, tall):
    P = C.Piece(name)
    H = 5.2 if tall else 3.4
    P.put(C.lathe([(0.0, -0.3), (1.0, -0.3), (1.0, 0.25), (0.78, 0.35), (0.0, 0.35)], 8), moss_top(seed))
    P.put(C.chunk((0, H * 0.34, 0), (0.55, H * 0.6, 0.55), seed + 1, 0.04), "Stone")
    lamp = H * 0.68
    P.put(C.chunk((0, lamp, 0), (1.3, 1.1, 1.3), seed + 2, 0.02), "Stone")
    # the lamp box is open on four faces: a glowing core sits in it
    P.put(C.chunk((0, lamp, 0), (0.5, 0.7, 0.5), seed + 3, 0.04), "GlowAmber")
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        P.put(C.chunk((sx * 0.5, lamp, sz * 0.5), (0.22 + 0.9 * abs(sz), 0.8 + 0.03 * (sx + 2 * sz), 0.22 + 0.9 * abs(sx)), seed + 4 + sx + 3 * sz, 0.02), "StoneDark")
    # a cap of two crossed leaf slabs (never a roof of curved eaves)
    for k in range(2):
        P.put(C.chunk((0, lamp + 0.85 + 0.05 * k, 0), (1.9, 0.18, 0.9), seed + 6 + k, 0.03, yaw=k * math.pi / 2 + 0.3 + 0.2 * k, tilt=((1, 0, 0), 0.05 * k)), lambda n, c: "Moss" if n[1] > 0.5 else "Stone")
    P.put(C.ellipsoid((0, lamp + 1.05, 0), (0.32, 0.2, 0.32), 6, 3), "Stone")
    P.cyl((0, H / 2, 0), 1.2, H)
    return P


def gate_branch(name="JG_Gate_Branch_G1", seed=541):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for sx in (-1, 1):
        P.put(C.chunk((sx * 3.4, 4.0, 0), (1.1, 8.4, 1.1), seed + sx, 0.04, taper=0.12), moss_top(seed + sx))
        P.box((sx * 3.4, 4.0, 0), (1.1, 8.0, 1.1))
        P.put(C.lathe([(0.0, -0.3), (1.0, -0.3), (0.9, 0.5), (0.0, 0.5)], 8, c=(sx * 3.4, 0, 0)), moss_top(seed + 3))
    # two living branches rise from the posts and cross over the opening
    for sx in (-1, 1):
        pts = [(sx * 3.4, 7.4, 0.0), (sx * 3.2, 9.6, 0.3), (sx * 1.2, 11.4, -0.2), (-sx * 1.8, 12.0, 0.2), (-sx * 4.4, 11.0, 0.0)]
        P.put(C.tube(pts, lambda t: 0.5 - 0.22 * t, None, 7, per=3, wob=0.06, seed=seed + sx), "Trunk")
        for k in range(3):
            a = rnd.uniform(0, TAU)
            c = (sx * rnd.uniform(0.5, 3.0), 11.4 + rnd.uniform(-0.3, 0.6), rnd.uniform(-0.5, 0.5))
            g = C.leaf_tier((0, 0, 0), 1.3, 0.6, seg=8, lobes=3, ruffle=0.2, droop=0.6, seed=seed + k + sx, under=0.4)
            P.put(g, lambda n, ctr: "LeafMid" if n[1] > 0 else "LeafDeep", t=c)
    for sx in (-1, 1):
        P.put(C.tube([(sx * 3.4, 6.0, 0.3), (sx * 3.7, 3.5, 0.4), (sx * 3.6, 0.2, 0.2)], 0.09, None, 4, per=2), "MossDeep")
    return P


def stairs(name, seed, n):
    P = C.Piece(name)
    run, rise, wid = 2.0, 1.0, 8.0
    for k in range(n):
        top = rise * (k + 1)
        z = k * run + run / 2
        P.put(C.box((0, top / 2 - 0.25, z), (wid, top + 0.5, run)), lambda nm, ctr, s=seed + k: "Moss" if nm[1] > 0.9 and C.fbm3(ctr[0] * 0.3 + s, 0, ctr[2] * 0.3, s, 2) > 0.1 else ("StoneDark" if nm[1] < 0.5 and ctr[1] < 0.6 else "Stone"))
        P.box((0, top / 2, z), (wid, top, run))
    # cheek stones: a rough low wall each side that rises with the stair
    for sx in (-1, 1):
        for k in range(0, n, 2):
            top = rise * (k + 2)
            z = k * run + run
            P.put(C.chunk((sx * (wid / 2 + 0.55), (top + 0.9) / 2 - 0.4, z), (1.1, top + 0.9, run * 2), seed + 20 + k * 3 + sx, 0.07), moss_top(seed + k))
    return P


def path_slab(name, seed, kind):
    P = C.Piece(name)
    rnd = random.Random(seed)
    if kind == 0:     # round
        pts = [(math.cos(TAU * i / 9) * 1.6 * (1 + 0.07 * rnd.uniform(-1, 1)), math.sin(TAU * i / 9) * 1.6 * (1 + 0.07 * rnd.uniform(-1, 1))) for i in range(9)]
    elif kind == 1:   # long
        pts = [(math.cos(TAU * i / 10) * 2.6 * (1 + 0.06 * rnd.uniform(-1, 1)), math.sin(TAU * i / 10) * 1.2 * (1 + 0.06 * rnd.uniform(-1, 1))) for i in range(10)]
    else:             # irregular
        pts = [(math.cos(TAU * i / 7) * (1.6 + 0.9 * rnd.random()), math.sin(TAU * i / 7) * (1.4 + 0.8 * rnd.random())) for i in range(7)]
    P.put(C.prism(pts, -0.45, 0.15), lambda n, c: ("Moss" if C.fbm3(c[0] * 0.8 + seed, 0, c[2] * 0.8, seed, 2) > 0.15 else "Stone") if n[1] > 0.9 else "StoneDark")
    return P


# ----------------------------------------------------------------------------------------------------------------------
# hermitage annex, lookout
# ----------------------------------------------------------------------------------------------------------------------
def hermitage_annex(name="JG_Hermitage_Annex_A1", seed=561):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # a plank floor 9 x 6 (top 0.5, decoration), four posts, a single-pitch shingle roof falling to the back
    P.put(C.box((0, 0.2, 0), (9.0, 0.6, 6.0)), lambda n, c: "Plank" if n[1] > 0.5 else "PlankDark")
    for sx in (-1, 1):
        post(P, sx * 4.2, -2.6, 4.4, 0.26, 0.0, seed, "Timber", 6)
        post(P, sx * 4.2, 2.6, 3.0, 0.26, 0.0, seed, "Timber", 6)
        P.box((sx * 4.2, 2.0, -2.6), (0.6, 4.0, 0.6))
        P.box((sx * 4.2, 1.5, 2.6), (0.6, 3.0, 0.6))
    P.put(C.chunk((0, 3.9, 0.0), (10.4, 0.34, 7.4), seed + 1, 0.0, tilt=((1, 0, 0), 0.24)), lambda n, c: "Moss" if n[1] > 0.6 and C.fbm3(c[0] * 0.3, 0, c[2] * 0.3, seed, 2) > 0.2 else "Shingle")
    P.put(bar((-4.4, 4.3, -2.6), (4.4, 4.3, -2.6), 0.4, 0.5), "Timber")
    P.put(bar((-4.4, 3.0, 2.6), (4.4, 3.0, 2.6), 0.4, 0.5), "Timber")
    # a stack of firewood, a water jar, a drying rack
    for r_ in range(3):
        for k in range(4 - r_):
            P.put(C.tube([(-3.8 + k * 0.62 + r_ * 0.31, 0.78 + r_ * 0.42, -2.2), (-3.8 + k * 0.62 + r_ * 0.31, 0.78 + r_ * 0.42, -0.4)], 0.3, 0.3, 6, per=1, caps=(True, True)), "Timber")
    P.put(C.lathe([(0.0, 0.5), (0.5, 0.5), (0.78, 1.0), (0.84, 1.6), (0.6, 2.0), (0.4, 2.15), (0.0, 2.15)], 10, c=(3.0, 0, -1.4)), "Soil")
    P.put(bar((-1.0, 2.0, 2.2), (-1.0, 0.5, 2.2), 0.2, 0.2), "Timber")
    P.put(bar((1.6, 2.0, 2.2), (1.6, 0.5, 2.2), 0.2, 0.2), "Timber")
    P.put(bar((-1.0, 2.0, 2.2), (1.6, 2.0, 2.2), 0.18, 0.18), "Timber")
    # the herb bed in front: a timber frame of soil and low plants
    bx, bz = 0.0, 6.6
    for sx in (-1, 1):
        P.put(bar((bx + sx * 3.2, 0.5, bz - 1.5), (bx + sx * 3.2, 0.5, bz + 1.5), 0.3, 0.9), "Timber")
    for sz in (-1, 1):
        P.put(bar((bx - 3.2, 0.5, bz + sz * 1.5), (bx + 3.2, 0.5, bz + sz * 1.5), 0.3, 0.9), "Timber")
    P.put(C.box((bx, 0.3, bz), (6.1, 0.7, 2.9)), "Soil")
    for k in range(9):
        a = TAU * k / 9
        P.put(C.blade((bx - 2.6 + (k % 5) * 1.3, 0.6, bz - 0.7 + (k // 5) * 1.4), (math.cos(a) * 0.5, 1.0, math.sin(a) * 0.5), rnd.uniform(0.9, 1.5), 0.3, droop=0.4, thick=0.04, segs=2), "FernBright")
    P.box((0, 0.3, 0), (9.0, 0.6, 6.0))
    return P


def lookout(name="JG_Lookout_Tower_T1", seed=571):
    rnd = random.Random(seed)
    P = C.Piece(name)
    H = 12.0
    # four posts leaning in a touch, cross braces, a platform 8 x 8 at y = 12, rails, a small shingle roof on four posts
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.tube([(sx * 4.0, -0.5, sz * 4.0), (sx * 3.6, H, sz * 3.6)], 0.5, 0.42, 6, per=1), "Timber")
            P.put(C.lathe([(0.0, -0.4), (1.0, -0.4), (0.9, 0.4), (0.0, 0.4)], 8, c=(sx * 4.0, 0, sz * 4.0)), moss_top(seed + sx))
            P.box((sx * 3.8, 6.0, sz * 3.8), (0.8, 12.0, 0.8))
    for lvl in (3.5, 7.5):
        for sx in (-1, 1):
            P.put(bar((sx * 3.9, lvl, -3.9), (sx * 3.7, lvl + 3.6, 3.9), 0.28, 0.28), "Timber")
            P.put(bar((sx * 3.7, lvl + 3.6, -3.9), (sx * 3.9, lvl, 3.9), 0.28, 0.28), "Timber")
    P.put(C.box((0, H - 0.25, 0), (8.6, 0.5, 8.6)), lambda n, c: "Plank" if n[1] > 0.5 else "PlankDark")
    P.box((0, H - 0.5, 0), (8.6, 1.0, 8.6))
    for sx in (-1, 1):
        P.put(bar((sx * 4.1, H + 1.1, -4.1), (sx * 4.1, H + 1.1, 4.1), 0.2, 0.26), "Timber")
        P.put(bar((-4.1, H + 1.1, sx * 4.1), (4.1, H + 1.1, sx * 4.1), 0.2, 0.26), "Timber")
        P.box((sx * 4.1, H + 0.55, 0), (0.3, 1.1, 8.2))
        P.box((0, H + 0.55, sx * 4.1), (8.2, 1.1, 0.3))
    # the stair: 12 steps of rise 1, tread 2, climbing along the +x side from z = 19 to the landing at z = -3, two sloped stringers under it
    for k in range(12):
        top = k + 1
        z = 19.0 - 2.0 * k - 1.0
        P.put(C.box((6.2, top - 0.2, z), (3.2, 0.4, 2.0)), "Plank")
        P.box((6.2, top - 0.5, z), (3.2, 1.0, 2.0))
    for sx in (-1, 1):
        P.put(bar((6.2 + sx * 1.3, 0.0, 19.0), (6.2 + sx * 1.3, 11.6, -3.0), 0.4, 0.7), "Timber")
    P.put(C.box((5.4, H - 0.27, -3.4), (3.4, 0.5, 2.4)), "Plank")
    P.put(C.box((6.2, 0.5, 19.6), (3.0, 1.0, 1.2)), moss_top(seed + 2))
    # the roof: four posts and a shallow shingle cap with a moss crest
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.put(C.tube([(sx * 3.2, H, sz * 3.2), (sx * 3.2, H + 5.5, sz * 3.2)], 0.2, 0.17, 5, per=1), "Timber")
    P.put(C.chunk((0, H + 5.7, 0), (8.6, 0.5, 8.6), seed + 3, 0.0, taper=0.8), "Shingle")
    P.put(C.ellipsoid((0, H + 6.3, 0), (1.2, 0.5, 1.2), 6, 3), "Moss")
    return P


# ----------------------------------------------------------------------------------------------------------------------
# waymarkers, offering table, ruin columns
# ----------------------------------------------------------------------------------------------------------------------
def waymarker(name, seed, kind):
    P = C.Piece(name)
    rnd = random.Random(seed)
    if kind == 0:
        P.put(C.chunk((0, 2.1, 0), (1.7, 4.4, 1.2), seed, 0.04, taper=0.22), moss_top(seed, 0.2))
        P.box((0, 2.0, 0), (1.5, 4.0, 1.0))
        for k, y in enumerate((1.2, 1.8)):
            P.put(C.box((0, y, -0.5), (1.4, 0.12, 0.3)), "StoneDark")
        # a spiral coil carved at the top of the face (a flattened tube winding in)
        pts = [(math.cos(a) * (0.5 - 0.06 * a / 1.6), 3.2 + math.sin(a) * (0.5 - 0.06 * a / 1.6), -0.5) for a in [t * 0.5 for t in range(0, 14)]]
        P.put(C.tube(pts, 0.13, 0.1, 4, per=1, up=(0, 0, 1)), "StoneDark")
    elif kind == 1:
        P.put(C.chunk((0, 1.1, 0), (1.9, 2.3, 1.5), seed, 0.05, taper=0.1), moss_top(seed, 0.2))
        P.box((0, 1.0, 0), (1.7, 2.0, 1.3))
        for k in range(3):
            P.put(C.box((-0.55 + k * 0.55, 1.5, -0.62), (0.16, 0.7, 0.3)), "StoneDark")
        P.put(C.chunk((0, 2.5, 0), (2.3, 0.4, 1.9), seed + 2, 0.03), "Moss")
    else:
        P.put(C.chunk((0, 1.5, 0), (1.5, 3.1, 1.1), seed, 0.05, taper=0.3, tilt=((0, 0, 1), 0.16)), moss_top(seed, 0.2))
        P.put(C.ellipsoid((0.3, 3.2, 0), (1.0, 0.5, 0.8), 8, 4, 0.12, seed), "Moss")
        P.put(C.box((0.05, 1.2, -0.45), (0.9, 0.12, 0.3)), "StoneDark")
        P.put(C.box((0.05, 1.7, -0.45), (0.9, 0.12, 0.3)), "StoneDark")
        P.box((0, 1.4, 0), (1.3, 2.8, 0.9))
    return P


def offering_table(name="JG_Offering_Table_O1", seed=581):
    P = C.Piece(name)
    for sx in (-1, 1):
        P.put(C.chunk((sx * 1.5, 0.55, 0), (1.0, 1.2, 1.6), seed + sx, 0.05), moss_top(seed + sx))
    P.put(C.chunk((0, 1.35, 0), (4.4, 0.45, 2.2), seed + 3, 0.025), lambda n, c: "Moss" if n[1] > 0.8 and C.fbm3(c[0] * 0.5, 0, c[2] * 0.5, seed, 2) > 0.35 else "Stone")
    P.put(C.lathe([(0.0, 1.55), (0.5, 1.6), (0.45, 1.85), (0.0, 1.8)], 8, c=(-1.0, 0, 0.1)), "RockDark")
    P.put(C.ellipsoid((-1.0, 1.82, 0.1), (0.14, 0.1, 0.14), 6, 3), "GlowAmber")
    for k, (x, z, r) in enumerate(((0.6, 0.4, 0.34), (0.6, 0.4, 0.26), (0.6, 0.4, 0.18))):
        P.put(C.ellipsoid((x + 0.4, 1.5 + k * 0.24, z), (r, r * 0.9, r), 8, 4, 0.05, seed + k), "RockPale")
    P.put(C.tube([(1.6, 1.55, -0.5), (1.6, 2.4, -0.5)], 0.06, 0.05, 4, per=1), "Timber")
    P.put(C.ellipsoid((1.6, 2.45, -0.5), (0.1, 0.08, 0.1), 5, 3), "GlowAmber")
    P.box((0, 0.8, 0), (4.4, 1.6, 2.0))
    return P


def ruin_column(name, seed, kind):
    P = C.Piece(name)
    if kind == 0:
        H = 5.4
        prof = [(0.0, -0.4), (1.25, -0.4), (1.1, 0.4), (0.95, 2.0), (0.9, H * 0.7), (0.92, H - 0.4), (0.7, H), (0.0, H - 0.1)]
        g = C.lathe(prof, 9, mod=lambda th, k: 1.0 + 0.06 * math.sin(3 * th + seed + k))
        P.put(g, moss_top(seed, -0.3))
        P.put(C.chunk((0.4, H, 0.0), (1.0, 0.5, 0.8), seed + 3, 0.2, tilt=((0, 0, 1), 0.5)), "StoneDark")
        P.cyl((0, H / 2, 0), 2.0, H)
    else:
        L = 4.2
        rings = []
        for k, x in enumerate((-L / 2, -L / 4, 0, L / 4, L / 2)):
            ring = [(x, 0.9 + math.sin(TAU * i / 9) * 0.92, math.cos(TAU * i / 9) * 0.92) for i in range(9)]
            rings.append(ring)
        P.put(C.loft(rings, True, True), moss_top(seed, -0.3))
        P.put(C.lathe([(0.0, 0.0), (0.7, 0.0), (0.6, 0.4), (0.0, 0.4)], 7, c=(L / 2 + 0.5, 0.5, 0.0)), "StoneDark", tilt=None)
        P.box((0, 0.9, 0), (L, 1.8, 1.8))
    return P


# ----------------------------------------------------------------------------------------------------------------------
# hidden set-piece shells
# ----------------------------------------------------------------------------------------------------------------------
def hollow_trunk(name="JG_Hidden_HollowTrunk_X1", seed=591):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # a thick-walled dead trunk 16 high: outer wall, an entrance arch cut into the south face, an inner floor (y = 0.5) and a niche; the wall is a ring of
    # six heavy buttress staves leaning together so the inside is open, topped by a ragged crown of broken stubs
    staves = 7
    for i in range(staves):
        a = TAU * i / staves
        if abs(((a - math.pi / 2 + math.pi) % TAU) - math.pi) < 0.46:
            continue   # the entrance: the stave facing +z is left out
        ca, sa = math.cos(a), math.sin(a)
        H = rnd.uniform(11.0, 17.0)
        R0 = 5.4
        pts = [(ca * (R0 + 1.2), -0.6, sa * (R0 + 1.2)), (ca * (R0 + 0.2), H * 0.35, sa * (R0 + 0.2)), (ca * (R0 - 0.5), H * 0.75, sa * (R0 - 0.5)), (ca * (R0 - 1.1), H, sa * (R0 - 1.1))]
        g = C.tube(pts, lambda t: 2.0 - 0.5 * t, lambda t: 1.55 - 0.4 * t, 8, per=3, wob=0.06, seed=seed + i, up=(0.0, 1.0, 0.0))
        P.put(g, lambda n, c, o=i: "Moss" if n[1] > 0.4 and C.fbm3(c[0] * 0.2 + o, c[1] * 0.2, c[2] * 0.2, seed, 2) > -0.1 else "Trunk")
        P.put(C.chunk((ca * (R0 - 1.1), H, sa * (R0 - 1.1)), (1.6, 0.6, 1.2), seed + 5 + i, 0.25, yaw=-a), "Trunk")
        P.box((ca * (R0 + 0.3), 5.0, sa * (R0 + 0.3)), (3.4, 10.0, 3.4), -a)
    # the arch: two roots curve over the doorway
    for sx in (-1, 1):
        P.put(C.tube([(sx * 2.4, -0.4, 6.0), (sx * 2.5, 3.4, 6.2), (sx * 1.2, 6.2, 5.9), (0.0, 6.8, 5.7)], lambda t: 0.9 - 0.4 * t, None, 7, per=3), "Root")
    # the floor: a round plank-and-stone floor at 0.5 with a moss rim, and the inner niche shrine
    P.put(C.lathe([(0.0, -0.4), (5.2, -0.4), (5.2, 0.4), (4.6, 0.5), (0.0, 0.5)], 14), moss_top(seed, -0.2))
    P.cyl((0, 0.05, 0), 10.0, 1.0)
    P.put(C.chunk((0, 1.0, -3.0), (2.4, 1.0, 1.4), seed + 20, 0.03), "Stone")
    P.put(C.lathe([(0.0, 1.5), (0.5, 1.55), (0.45, 1.8), (0.0, 1.75)], 8, c=(0, 0, -3.0)), "RockDark")
    P.put(C.ellipsoid((0, 1.78, -3.0), (0.16, 0.1, 0.16), 6, 3), "GlowAmber")
    # bracket fungi up the inner wall (glowing rims) and hanging moss
    for k in range(5):
        a = math.radians(200 + k * 28)
        y = 2.0 + 1.3 * k
        P.put(C.lathe([(0.0, 0.0), (0.7, 0.0), (0.62, 0.16), (0.0, 0.18)], 8), lambda n, c: "GlowTeal" if n[1] < -0.5 else "CapPale", t=(math.cos(a) * 3.6, y, math.sin(a) * 3.6))
    return P


def pavilion_ruin(name="JG_Hidden_PavilionRuin_X2", seed=601):
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(C.chunk((0, 0.5, 0), (13.0, 1.0, 13.0), seed, 0.012), moss_top(seed, -0.1))
    P.box((0, 0.5, 0), (13.0, 1.0, 13.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 4.2, sz * 4.2
            footing(P, x, z, 0.85, 0.7, 1.0, seed + sx)
            if (sx, sz) in ((-1, -1), (1, 1)):
                h = 6.0 if sx == -1 else 3.4
                P.put(C.tube([(x, 1.5, z), (x, 1.5 + h, z)], 0.46, 0.4, 8, per=1), "Timber")
                P.put(C.chunk((x, 1.5 + h, z), (1.0, 0.4, 0.9), seed + 7, 0.25, tilt=((1, 0, 0), 0.35)), "Timber")
                P.box((x, 1.5 + h / 2, z), (0.9, h, 0.9))
    P.put(bar((-4.4, 7.4, -4.2), (4.6, 7.0, -4.2), 0.5, 0.6), "Timber")
    P.put(C.chunk((1.0, 1.4, 1.8), (6.0, 0.4, 2.4), seed + 9, 0.05, tilt=((0, 0, 1), 0.18), yaw=0.5), "Shingle")
    P.put(bar((-2.0, 1.3, -1.0), (4.8, 1.8, 3.0), 0.5, 0.5), "Timber")
    for k in range(3):
        P.put(C.chunk((-1.5 + k * 3.2, 1.05, 5.6), (1.4, 0.4, 1.0), seed + 11 + k, 0.12, yaw=k), "StoneDark")
    return P


def build_all():
    out = {}
    out["JG_Shrine_Stone_H1"] = shrine_stone()
    out["JG_Shrine_HallRuin_H2"] = shrine_hall()
    out["JG_Lantern_Sprout_L1"] = lantern("JG_Lantern_Sprout_L1", 521, True)
    out["JG_Lantern_Sprout_L2"] = lantern("JG_Lantern_Sprout_L2", 531, False)
    out["JG_Gate_Branch_G1"] = gate_branch()
    out["JG_Stair_Stone_S4"] = stairs("JG_Stair_Stone_S4", 551, 4)
    out["JG_Stair_Stone_S8"] = stairs("JG_Stair_Stone_S8", 552, 8)
    out["JG_Path_Slab_P1"] = path_slab("JG_Path_Slab_P1", 553, 0)
    out["JG_Path_Slab_P2"] = path_slab("JG_Path_Slab_P2", 554, 1)
    out["JG_Path_Slab_P3"] = path_slab("JG_Path_Slab_P3", 555, 2)
    out["JG_Hermitage_Annex_A1"] = hermitage_annex()
    out["JG_Lookout_Tower_T1"] = lookout()
    out["JG_Waymarker_W1"] = waymarker("JG_Waymarker_W1", 561, 0)
    out["JG_Waymarker_W2"] = waymarker("JG_Waymarker_W2", 562, 1)
    out["JG_Waymarker_W3"] = waymarker("JG_Waymarker_W3", 563, 2)
    out["JG_Offering_Table_O1"] = offering_table()
    out["JG_Ruin_Column_C1"] = ruin_column("JG_Ruin_Column_C1", 571, 0)
    out["JG_Ruin_Column_C2"] = ruin_column("JG_Ruin_Column_C2", 572, 1)
    out["JG_Hidden_HollowTrunk_X1"] = hollow_trunk()
    out["JG_Hidden_PavilionRuin_X2"] = pavilion_ruin()
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-30s %5d tris  box %s -> %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi)))

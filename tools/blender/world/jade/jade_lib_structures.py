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

The shrine, the hall ruin, the lanterns, the annex, the lookout, the waymarkers, the offering table and the ruin columns are built in jade_lib_structures2.py (the crafted second pass:
fluted pillars with leaf capitals, shingle and thatch roofs, lashed timber, woven wattle, broken courses); this file keeps the helpers, the gate, stairs, path slabs and the two hidden shells
and lists every piece in build_all().

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
# lanterns, gate, stairs, slabs


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
# waymarkers, offering table, ruin columns


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
    import jade_lib_structures2 as S2    # the crafted shrine, hall ruin, lanterns, annex, lookout, waymarkers, offering table and ruin columns (second pass)
    out = {}
    out["JG_Shrine_Stone_H1"] = S2.shrine_stone()
    out["JG_Shrine_HallRuin_H2"] = S2.shrine_hall()
    out["JG_Lantern_Sprout_L1"] = S2.lantern("JG_Lantern_Sprout_L1", 521, True)
    out["JG_Lantern_Sprout_L2"] = S2.lantern("JG_Lantern_Sprout_L2", 531, False)
    out["JG_Gate_Branch_G1"] = gate_branch()
    out["JG_Stair_Stone_S4"] = stairs("JG_Stair_Stone_S4", 551, 4)
    out["JG_Stair_Stone_S8"] = stairs("JG_Stair_Stone_S8", 552, 8)
    out["JG_Path_Slab_P1"] = path_slab("JG_Path_Slab_P1", 553, 0)
    out["JG_Path_Slab_P2"] = path_slab("JG_Path_Slab_P2", 554, 1)
    out["JG_Path_Slab_P3"] = path_slab("JG_Path_Slab_P3", 555, 2)
    out["JG_Hermitage_Annex_A1"] = S2.hermitage_annex()
    out["JG_Lookout_Tower_T1"] = S2.lookout()
    out["JG_Waymarker_W1"] = S2.waymarker("JG_Waymarker_W1", 561, 0)
    out["JG_Waymarker_W2"] = S2.waymarker("JG_Waymarker_W2", 562, 1)
    out["JG_Waymarker_W3"] = S2.waymarker("JG_Waymarker_W3", 563, 2)
    out["JG_Offering_Table_O1"] = S2.offering_table()
    out["JG_Ruin_Column_C1"] = S2.ruin_column("JG_Ruin_Column_C1", 571, 0)
    out["JG_Ruin_Column_C2"] = S2.ruin_column("JG_Ruin_Column_C2", 572, 1)
    out["JG_Hidden_HollowTrunk_X1"] = hollow_trunk()
    out["JG_Hidden_PavilionRuin_X2"] = pavilion_ruin()
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-30s %5d tris  box %s -> %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi)))

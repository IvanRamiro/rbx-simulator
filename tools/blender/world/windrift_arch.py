"""windrift_arch: the buildings, bridges, stairs, walls and props of Windrift Hold (2026-11-23), built from windrift_kit. Plain Python, no Blender.

Every builder returns a WP: geometry split by material suffix (at most four), the invisible collision boxes (piece.col, in the piece's own frame), named marks and
the floor rectangles. Frames: x right, y up, z back (front = -Z); y = 0 is the floor (a floor mesh lies 0.5 over its terrain: the plan lifts it); feet sink below.
"""
import math
import random

import hq_kit as K
from hq_kit import vadd, vsub, vmul, vnorm, vlen, lerp, TAU
from windrift_kit import (WP, S_STONE, S_TIMBER, S_TILE, S_BRONZE, S_CLOTH, S_ROPE, S_PLANK, S_LAMP, S_BAMBOO, hex8, beam, post, cyl, rubble, stone_wall, stone_box,
                          roof_plane, roof_gable, roof_shed, roof_hip, cap_line, finial, stilt_bay, corbels, rope_line, catenary, awning, lean_piece, ring_band,
                          obox, tri_prism, wedge, seed_of, scaffold, ladder, bell, lantern_hang, bracket)

PI = math.pi


# ======================================================================================================================
# helpers
# ======================================================================================================================
def wall_run(P, a, b, y0, y1, thick=0.5, openings=(), batten=1.7, seed=1, suffix=S_TIMBER, solid=True, name="Wall", lean=(0.0, 0.0)):
    """A board-and-batten wall from a to b (x, z) between y0 and y1; `openings` = list of (s0, s1, oy0, oy1): doorways and windows (distances along the wall, heights
    over y0). Panels stand between openings, a header over each opening and a sill under each window; vertical battens stand proud of the boards. Collision: the solid
    panels (not the headers over a doorway, which are above head height)."""
    g = P.geo(suffix)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz, ux
    ops = sorted(openings)
    cuts = [0.0]
    for (s0, s1, o0, o1) in ops:
        cuts += [s0, s1]
    cuts.append(L)
    rng = random.Random(seed)

    def box_s(s0, s1, ya, yb, t, off=0.0):
        p0 = (a[0] + ux * s0 + nx * off, a[1] + uz * s0 + nz * off)
        p1 = (a[0] + ux * s1 + nx * off, a[1] + uz * s1 + nz * off)
        beam(g, (p0[0], (ya + yb) / 2, p0[1]), (p1[0], (ya + yb) / 2, p1[1]), t, yb - ya, up=(0, 1, 0))

    def solid_box(s0, s1, ya, yb, nm):
        if not solid:
            return
        pts = [(a[0] + ux * s + nx * o, a[1] + uz * s + nz * o) for s in (s0, s1) for o in (-thick / 2 - 0.1, thick / 2 + 0.1)]
        P.block(nm, min(p[0] for p in pts), max(p[0] for p in pts), ya, yb, min(p[1] for p in pts), max(p[1] for p in pts))
    # solid spans between openings
    for i in range(0, len(cuts) - 1, 2):
        s0, s1 = cuts[i], cuts[i + 1]
        if s1 - s0 < 0.3:
            continue
        box_s(s0, s1, y0, y1, thick)
        solid_box(s0, s1, y0, y1, name)
        n = int((s1 - s0) / batten)
        for k in range(1, n + 1):
            s = s0 + (s1 - s0) * k / (n + 1) + rng.uniform(-0.12, 0.12)
            beam(g, (a[0] + ux * s + nx * (thick / 2 + 0.04), y0 + 0.2, a[1] + uz * s + nz * (thick / 2 + 0.04)),
                 (a[0] + ux * s + nx * (thick / 2 + 0.04), y1 - 0.15, a[1] + uz * s + nz * (thick / 2 + 0.04)), 0.2, 0.12, up=(nx, 0, nz))
    for (s0, s1, o0, o1) in ops:
        if o1 < y1 - y0 - 0.05:
            box_s(s0 - 0.12, s1 + 0.12, y0 + o1, y1, thick)
            solid_box(s0, s1, y0 + o1 if o0 < 0.1 else y0 + o1, y1, name + "Header") if (o1 > 2.8 and False) else None
        if o0 > 0.05:
            box_s(s0 - 0.12, s1 + 0.12, y0, y0 + o0, thick)
            solid_box(s0, s1, y0, y0 + o0, name)


def plank_floor(P, x0, x1, z0, z1, y, thick=0.5, suffix=S_PLANK, name="Floor", joists=True, bottom=None):
    """A floor slab (top at y) with its joist ends showing along the two long edges; collision: one box; the footprint is recorded."""
    g = P.geo(suffix)
    K.box(g, x0, x1, y - thick, y, z0, z1)
    P.block(name, x0, x1, (y - thick - 1.0) if bottom is None else bottom, y, z0, z1)
    P.floor.append((x0, x1, z0, z1, y))
    if joists:
        gt = P.geo(S_TIMBER)
        n = max(2, int((x1 - x0) / 2.0))
        for i in range(n + 1):
            x = lerp(x0 + 0.3, x1 - 0.3, i / n)
            K.box(gt, x - 0.18, x + 0.18, y - thick - 0.55, y - thick, z0 - 0.25, z1 + 0.25)


def rail(P, a, b, y, h=1.1, every=3.0, post_w=0.28, suffix=S_TIMBER, rope=True, lean=(0.0, 0.0), sag=0.12, rope_suffix=S_TIMBER, skip_first=False):
    """A rope rail along a -> b (x, z) on a deck at height y: posts every ~`every`, two ropes (hand and knee), no collision (a rail you can fall through: the plan adds
    guards where it matters)."""
    g = P.geo(suffix)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(round(L / every)))
    pts_hand, pts_knee = [], []
    for i in range(n + 1):
        t = i / n
        x, z = lerp(a[0], b[0], t), lerp(a[1], b[1], t)
        if not (skip_first and i == 0):
            post(g, x, z, y - 0.1, y + h, post_w, lean=lean, taper=0.03)
        pts_hand.append((x, y + h - 0.1 - (sag * 4 * 0 if False else 0.0), z))
        pts_knee.append((x, y + h * 0.45, z))
    if rope:
        for pts in (pts_hand, pts_knee):
            for p0, p1 in zip(pts, pts[1:]):
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - sag, (p0[2] + p1[2]) / 2)
                rope_line(P, [p0, mid, p1], r=0.09, suffix=rope_suffix)


def steps_run(P, a, yaw, n, width, y0=0.0, tread=1.5, rise=1.0, suffix=S_STONE, name="Step", walls=False, seed=1):
    """A straight stair of n one-stud risers starting at a = (x, z) at height y0 and climbing along yaw (0 = +z): stone treads as slabs with rough fronts; collision: one box per
    step (rotated yaw is handled by the placement: this keeps steps axis-aligned in the piece frame: yaw 0 = along +z)."""
    g = P.geo(suffix)
    rng = random.Random(seed)
    for k in range(n):
        za, zb = a[1] + k * tread, a[1] + (k + 1) * tread
        yb = y0 + (k + 1) * rise
        rubble(g, a[0] - width / 2, a[0] + width / 2, y0 + k * rise - 0.4, yb, za - 0.05, zb + 0.02, rng, j=0.06)
        P.block(name, a[0] - width / 2, a[0] + width / 2, y0 + k * rise - 1.5, yb, za, zb)


# ======================================================================================================================
# shared building helpers
# ======================================================================================================================
def sub_roof(P, fn, t, yaw, **kw):
    """Builds a roof (or any sub-piece) with `fn(sub, **kw)` in its own frame (ridge along x) and merges it turned by yaw about y and moved by t."""
    sub = WP()
    out = fn(sub, **kw)
    P.absorb(sub, t=t, yaw=yaw)
    return out


def posts_grid(P, xs, z, y0, y1, w=0.7, lean=(0.0, 0.0), name="Post", band=None, taper=0.05, suffix=S_TIMBER):
    g = P.geo(suffix)
    gb = P.geo(S_BRONZE)
    for x in xs:
        post(g, x, z, y0, y1, w, lean=lean, taper=taper)
        P.block(name, x - w / 2 - 0.05, x + w / 2 + 0.05, y0, y1, z - w / 2 - 0.05, z + w / 2 + 0.05)
        if band is not None:
            ring_band(gb, x + lean[0] * (band - y0), band, z + lean[1] * (band - y0), w * 0.74, w * 0.74, band - 0.2, band + 0.2, seg=4, t=0.09, phase=PI / 4)


def chime(P, x, y, z, seed=1):
    """A bronze wind chime: a cord and a ring from the eave, five tubes of different lengths."""
    rng = random.Random(seed)
    gb, gt = P.geo(S_BRONZE), P.geo(S_TIMBER)
    beam(gt, (x, y + 1.1, z), (x, y - 0.8, z), 0.06, 0.06)
    ring_band(gb, x, y - 0.9, z, 0.55, 0.55, y - 1.0, y - 0.86, seg=8, t=0.08)
    for k_ in range(5):
        a_ = TAU * k_ / 5
        beam(gt, (x, y - 0.88, z), (x + 0.6 * math.cos(a_), y - 0.95, z + 0.6 * math.sin(a_)), 0.05, 0.05)
    for k in range(5):
        a = TAU * k / 5
        px, pz = x + 0.55 * math.cos(a), z + 0.55 * math.sin(a)
        ln = rng.uniform(0.9, 1.9)
        cyl(gb, (px, y - 0.9, pz), (px, y - 1.0 - ln, pz), 0.09, 0.09, seg=4)


def round_disc(P, x, y, z, r, nz=-1.0, suffix=S_BRONZE, t=0.2, seg=8):
    """A flat disc (a vent, a boss) facing +/-z at (x, y, z)."""
    g = P.geo(suffix)
    cyl(g, (x, y, z), (x, y, z + nz * t), r, r, seg=seg)


# ======================================================================================================================
# the Rain Hall: a hall over the waterfall (it straddles the gorge)
# ======================================================================================================================
def rain_hall():
    """The Hall of Falling Water: a long timber hall carried across the gorge on two deep trusses resting on stone abutments. Front: a plank wall with two doors and a lean-to
    porch over the left one; back (toward the falls): open to a rope-railed gallery overhanging the void on corbels. The roof is the hall's signature: it has settled, the
    ridge falls from 14.8 at the left end to 12.4 at the right and sits off the middle, the long slope drops over the gallery, a raised lantern box with its own little
    gable sits on the left of the ridge, the bronze-capped ridge ends in two finials that do not match. A bell hangs under a hood at the right gable. Span 13; the floor is
    1.5 over the pad; the gorge lies under the middle (x -6.5 .. 6.5)."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    X0, X1, Z0, Z1, FY = -15.5, 12.5, -6.5, 6.5, 0.0
    for (xa, xb) in ((X0 - 1.5, -6.9), (6.9, X1 + 0.5)):
        stone_box(gs, xa, xb, Z0 - 1.2, Z1 + 1.8, -4.6, FY - 0.55, seed=3 + int(xa), batter=0.35, course=(1.3, 1.9), blen=(3.0, 5.0))
        P.block("Abutment", xa, xb, -8.0, FY, Z0 - 1.2, Z1 + 1.8)
    for zz in (-5.2, 5.2):                                                          # the trusses
        beam(gt, (-8.4, -1.35, zz), (8.4, -1.35, zz), 0.9, 1.5)
        beam(gt, (-7.2, -2.9, zz), (7.2, -2.9, zz), 0.7, 0.7)
        beam(gt, (-7.6, -2.7, zz), (-0.2, -0.6, zz), 0.55, 0.55)
        beam(gt, (7.6, -2.7, zz), (0.2, -0.6, zz), 0.55, 0.55)
        beam(gt, (0.0, -3.0, zz), (0.0, -0.4, zz), 0.6, 0.6)
        for xx in (-7.6, 0.0, 7.6):
            ring_band(gb, xx, -2.4, zz, 0.42, 0.42, -2.6, -2.1, seg=4, t=0.1)
    for xx in (-4.2, 4.2):
        beam(gt, (xx, -1.6, -5.2), (xx, -1.6, 5.2), 0.55, 0.9)
    K.box(gt, X0, X1, FY - 0.55, FY, Z0, Z1)                                        # the deck (timber planks)
    K.box(gt, X0 + 1.0, X1 - 1.0, FY - 0.55, FY - 0.02, Z1, Z1 + 3.4)
    P.block("HallFloor", X0, X1, FY - 1.2, FY, Z0, Z1)
    P.block("Gallery", X0 + 1.0, X1 - 1.0, FY - 1.2, FY, Z1, Z1 + 3.4)
    P.floor.append((X0, X1, Z0, Z1, FY))
    P.floor.append((X0 + 1.0, X1 - 1.0, Z1, Z1 + 3.4, FY))
    corbels(P, X0 + 2.0, X1 - 2.0, Z1, FY - 0.55, 3.4, steps=3, w=0.5, direction=1.0)
    for z, yy in ((Z0, 8.9), (Z1, 8.3)):
        posts_grid(P, [-14.0, -6.5, -2.0, 2.0, 6.0, 12.0] if z < 0 else [-14.0, -9.0, -4.0, 4.0, 8.5, 12.0], z, FY, yy, 0.75, lean=(0.0, 0.0 if z < 0 else 0.015), band=FY + 1.8)
        beam(gt, (X0 - 0.4, yy, z), (X1 + 0.4, yy, z), 0.7, 0.9)
    wall_run(P, (X0 + 0.3, Z0), (X1 - 0.3, Z0), FY, 8.7, thick=0.45, openings=[(3.0, 7.0, 0.0, 4.4), (22.4, 26.4, 0.0, 4.4), (12.0, 14.2, 5.6, 7.4), (16.2, 18.4, 5.6, 7.4)],
             seed=2, name="FrontWall")
    wall_run(P, (X0 + 0.3, Z0), (X0 + 0.3, Z1), FY, 8.4, thick=0.45, openings=[(4.0, 8.5, 0.0, 4.2)], seed=4, name="EndWall")
    for dx in (-8.0, 7.3):                                                          # two steps in front of each door
        for k, (za, zb, top) in enumerate(((-9.6, -8.1, -1.0), (-8.1, -6.5, -0.0 - 0.0))):
            pass
    for (xa, xb) in ((-13.0, -7.4), (7.2, 11.8)):
        rubble(gs, xa, xb, -3.0, -1.0, -9.9, -7.6, random.Random(int(xa)), j=0.05)
        P.block("DoorStep", xa, xb, -3.0, -1.0, -9.9, -7.7)
    rail(P, (X0 + 1.2, Z1 + 3.3), (X1 - 1.2, Z1 + 3.3), FY, h=1.15, every=2.9)
    rail(P, (X0 + 1.2, Z1 + 3.3), (X0 + 1.2, Z1 + 0.4), FY, h=1.15, every=2.9, skip_first=True)
    rail(P, (X1 - 1.2, Z1 + 3.3), (X1 - 1.2, Z1 + 0.4), FY, h=1.15, every=2.9, skip_first=True)
    P.block("GalleryRail", X0 + 1.0, X1 - 1.0, FY, FY + 1.2, Z1 + 3.2, Z1 + 3.5)
    r = roof_gable(P, X0, X1, Z0 - 0.4, Z1 + 3.0, (9.0, 8.6), (7.6, 7.2), (1.2, 1.5), (14.8, 12.4), over=2.0, rake=(1.4, 0.8), seed=7)
    # the lantern box on the ridge (left third): slatted walls, a small gable across the ridge
    lx, lz = -8.5, 1.3
    K.box(gt, lx - 3.0, lx + 3.0, 10.4, 11.0, lz - 2.0, lz + 2.0)
    for i in range(7):
        xx = lx - 2.7 + i * 0.9
        K.box(gt, xx - 0.14, xx + 0.14, 11.0, 13.4, lz - 2.0, lz - 1.7)
        K.box(gt, xx - 0.14, xx + 0.14, 11.0, 13.4, lz + 1.7, lz + 2.0)
    sub = WP()
    roof_gable(sub, -2.3, 2.3, -2.4, 2.4, 13.4, 13.4, 0.0, 15.3, over=0.9, rake=(0.8, 0.8), seed=19, row=0.9, infill=False)
    P.absorb(sub, t=(lx, 0.0, lz), yaw=PI / 2)
    # the porch: a lean-to over the left door, on two posts
    sub = WP()
    roof_shed(sub, -3.4, 3.4, -3.8, 0.4, 4.2, 6.0, over=0.8, rake=(0.5, 0.5), seed=23, row=0.9)
    P.absorb(sub, t=(-10.2, 0.0, Z0 - 0.4))
    posts_grid(P, [-13.4, -7.0], Z0 - 3.6, FY, 4.5, 0.55, lean=(0.0, 0.02), band=1.6, name="PorchPost")
    beam(gt, (-13.8, 4.5, Z0 - 3.6), (-6.6, 4.5, Z0 - 3.6), 0.5, 0.6)
    # the bell hood at the right gable and a chime on the gallery's eave
    posts_grid(P, [X1 + 1.4], Z0 + 2.2, FY, 6.2, 0.5, lean=(-0.02, 0.0), name="BellPost")
    posts_grid(P, [X1 + 1.4], Z0 + 5.2, FY, 6.2, 0.5, lean=(-0.02, 0.0), name="BellPost")
    beam(gt, (X1 + 1.2, 6.0, Z0 + 2.2), (X1 + 1.2, 6.0, Z0 + 5.2), 0.5, 0.5)
    bell(P, X1 + 1.2, 5.8, Z0 + 3.7, r=0.9, h=1.5)
    chime(P, X0 + 6.0, 6.7, Z1 + 3.2, seed=3)
    chime(P, X1 - 5.0, 6.3, Z1 + 3.2, seed=5)
    P.marks["Falls"] = (0.0, 4.0, Z1 + 8.0)
    P.marks["Gallery"] = (0.0, FY + 1.0, Z1 + 1.8)
    P.marks["Bell"] = (X1 + 1.2, 5.8, Z0 + 3.7)
    P.lights.append((0.0, 6.0, 0.0))
    lean_piece(P, 0.012, 0.0, 2.0)
    return P


# ======================================================================================================================
# the Long Hold: the headquarters (on the centre pad)
# ======================================================================================================================
def hq():
    """The Long Hold, Windrift Hold's headquarters. A long timber hall on a battered slate podium: one huge leaning roof whose ridge falls from 15.6 on the left to 13.4
    on the right and whose front slope sweeps down over a deep porch to 5 studs, the back slope short and steep; at the left end a tower of three storeys whose upper
    storey overhangs on corbels, a steep hip roof and a bell; at the right a low annex under its own lean-to. A bronze ridge, chimes under the porch eave, a bell in the
    tower. Podium 3 over the pad (three one-stud risers up to the porch, left of the door). Footprint x -18.5..18.5, z -13.5..14.5."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    FY = 0.0
    stone_box(gs, -18.5, 18.5, -13.5, 14.5, -6.0, FY - 0.55, seed=9, batter=0.4, course=(1.5, 2.2), blen=(3.4, 5.6))
    P.block("Podium", -18.5, 18.5, -9.0, FY, -13.5, 14.5)
    K.box(gt, -18.0, 18.0, FY - 0.55, FY, -13.0, 14.0)
    P.floor.append((-18.5, 18.5, -13.5, 14.5, FY))
    # three steps up to the porch (the door is at x -4..2)
    rng = random.Random(5)
    for k, (za, zb, top) in enumerate(((-16.2, -14.7, -2.0), (-14.7, -13.2, -1.0))):
        rubble(gs, -6.5, 4.5, top - 1.6, top, za, zb + 0.05, rng, j=0.05)
        P.block("Step", -6.5, 4.5, top - 1.6, top, za, zb)
    # the hall: x -14.5 .. 10.5, z -6.5 .. 6.5, wall to 9
    HX0, HX1, HZ0, HZ1 = -14.5, 10.5, -6.5, 6.5
    posts_grid(P, [HX0 + 0.5 + i * 4.9 for i in range(6) if i != 3], HZ0, FY, 9.2, 0.8)       # (none in the doorway, x -4 .. 2.5)
    posts_grid(P, [HX0 + 0.5 + i * 4.9 for i in range(6)], HZ1, FY, 8.4, 0.8)
    beam(gt, (HX0 - 0.4, 9.2, HZ0), (HX1 + 0.4, 9.2, HZ0), 0.8, 1.0)
    beam(gt, (HX0 - 0.4, 8.4, HZ1), (HX1 + 0.4, 8.4, HZ1), 0.8, 1.0)
    wall_run(P, (HX0, HZ0), (HX1, HZ0), FY, 9.0, thick=0.5, openings=[(10.5, 17.0, 0.0, 5.6), (4.0, 6.6, 3.0, 6.0), (20.0, 22.6, 3.0, 6.0)], seed=12, name="FrontWall")
    wall_run(P, (HX0, HZ1), (HX1, HZ1), FY, 8.2, thick=0.5, openings=[(5.0, 7.4, 3.2, 6.0), (13.0, 15.4, 3.2, 6.0), (20.0, 22.4, 3.2, 6.0)], seed=13, name="BackWall")
    wall_run(P, (HX1, HZ0), (HX1, HZ1), FY, 8.6, thick=0.5, openings=[(4.5, 8.5, 0.0, 4.6)], seed=14, name="EndWallR")
    wall_run(P, (HX0, HZ0), (HX0, HZ1), FY, 8.6, thick=0.5, openings=[(4.5, 8.5, 0.0, 4.6)], seed=15, name="EndWallL")
    # the porch: low posts of different heights carrying the front eave, a rail between two of them
    ph = [5.0, 5.4, 5.2, 5.6, 5.0, 5.3, 5.1]
    posts_grid(P, [-13.0, -9.0, -5.0, 3.5, 7.5, 11.0], -12.0, FY, 5.2, 0.7, lean=(0.0, 0.03), band=1.4, name="PorchPost")
    beam(gt, (-14.0, 5.1, -12.0), (11.5, 5.1, -12.0), 0.7, 0.8)
    for x in (-10.0, 6.0):
        bracket(P, x, 4.4, -6.7, 4.8, h=1.6, along="z", direction=-1.0)
    chime(P, -2.0, 4.6, -12.0, seed=2)
    chime(P, 7.0, 4.4, -12.0, seed=8)
    # the roof
    roof_gable(P, HX0, HX1, -12.6, 7.0, (5.6, 5.2), (8.7, 8.3), (1.2, 1.0), (15.6, 13.4), over=1.8, rake=(1.8, 1.0), seed=31, row=1.05)
    # the tower (left end): three storeys, the upper one overhanging on corbels, a steep hip roof, a bell
    TX0, TX1, TZ0, TZ1 = -18.0, -11.0, 0.5, 8.5
    posts_grid(P, [TX0 + 0.5, TX1 - 0.5], TZ0 + 0.5, FY, 6.0, 0.8, lean=(0.012, 0.0))
    posts_grid(P, [TX0 + 0.5, TX1 - 0.5], TZ1 - 0.5, FY, 6.0, 0.8, lean=(0.012, 0.0))
    wall_run(P, (TX0, TZ0), (TX1, TZ0), FY, 6.0, thick=0.5, openings=[(2.0, 4.4, 2.0, 4.2)], seed=20, name="TowerWall")
    wall_run(P, (TX0, TZ1), (TX1, TZ1), FY, 6.0, thick=0.5, openings=[(2.0, 4.4, 2.0, 4.2)], seed=21, name="TowerWall")
    wall_run(P, (TX0, TZ0), (TX0, TZ1), FY, 6.0, thick=0.5, seed=22, name="TowerWall")
    K.box(gt, TX0 - 1.6, TX1 + 1.6, 6.0, 6.5, TZ0 - 1.6, TZ1 + 1.6)                                  # the overhanging floor
    P.block("TowerDeck", TX0 - 1.6, TX1 + 1.6, 5.4, 6.5, TZ0 - 1.6, TZ1 + 1.6)
    corbels(P, TX0 - 1.0, TX1 + 1.0, TZ0, 6.0, 1.6, steps=3, w=0.45, direction=-1.0)
    for sx in (TX0 - 1.1, TX1 + 1.1):
        for sz in (TZ0 - 1.1, TZ1 + 1.1):
            post(gt, sx, sz, 6.5, 12.0, 0.65, lean=(0.012, 0.0), taper=0.05)
    for z in (TZ0 - 1.1, TZ1 + 1.1):
        beam(gt, (TX0 - 1.3, 12.0, z), (TX1 + 1.3, 12.0, z), 0.6, 0.7)
    for x in (TX0 - 1.1, TX1 + 1.1):
        beam(gt, (x, 12.0, TZ0 - 1.3), (x, 12.0, TZ1 + 1.3), 0.6, 0.7)
    for z in (TZ0 - 1.1, TZ1 + 1.1):                                                                   # low rails round the top room, the room open above
        beam(gt, (TX0 - 1.1, 7.7, z), (TX1 + 1.1, 7.7, z), 0.3, 0.3)
        beam(gt, (TX0 - 1.1, 9.4, z), (TX1 + 1.1, 9.4, z), 0.3, 0.3)
    for x in (TX0 - 1.1, TX1 + 1.1):
        beam(gt, (x, 7.7, TZ0 - 1.1), (x, 7.7, TZ1 + 1.1), 0.3, 0.3)
        beam(gt, (x, 9.4, TZ0 - 1.1), (x, 9.4, TZ1 + 1.1), 0.3, 0.3)
    P.block("TowerRail", TX0 - 1.6, TX1 + 1.6, 6.5, 7.7, TZ0 - 1.7, TZ0 - 1.5)
    bell(P, (TX0 + TX1) / 2 - 0.2, 11.8, (TZ0 + TZ1) / 2, r=1.1, h=1.8)
    roof_hip(P, (TX0 + TX1) / 2, (TZ0 + TZ1) / 2, 5.6, 5.6, 12.0, 20.0, ridge=(0.8, 0.4), over=1.8, seed=41, row=0.95, rx=1.2)
    # the annex (right end): one storey under a lean-to falling away to the right
    AX0, AX1, AZ0, AZ1 = 11.0, 17.5, -4.5, 7.5
    posts_grid(P, [AX1 - 0.5], AZ0 + 0.5, FY, 4.6, 0.7, lean=(0.02, 0.0))
    posts_grid(P, [AX1 - 0.5], AZ1 - 0.5, FY, 4.6, 0.7, lean=(0.02, 0.0))
    wall_run(P, (AX0, AZ0), (AX1, AZ0), FY, 4.6, thick=0.45, openings=[(2.0, 4.6, 0.0, 3.6)], seed=24, name="AnnexWall")
    wall_run(P, (AX0, AZ1), (AX1, AZ1), FY, 4.6, thick=0.45, openings=[(2.2, 4.4, 1.6, 3.0)], seed=25, name="AnnexWall")
    wall_run(P, (AX1, AZ0), (AX1, AZ1), FY, 4.6, thick=0.45, openings=[(3.0, 6.0, 1.4, 3.2)], seed=26, name="AnnexWall")
    sub = WP()
    LA = AZ1 - AZ0 + 0.4
    roof_shed(sub, -LA / 2, LA / 2, AX1 - AX0 + 0.2, 0.0, 4.6, 8.2, over=1.6, rake=(0.6, 0.6), seed=27, row=0.95)
    P.absorb(sub, t=(AX0 - 0.2, 0.0, (AZ0 + AZ1) / 2), yaw=PI / 2)
    # (a chimney of stone on the annex: a stack with a bronze cap)
    stone_box(gs, 13.6, 15.2, 1.0, 2.6, 0.0, 10.0, seed=3, batter=0.1, course=(1.0, 1.6), blen=(1.6, 1.6))
    K.box(gb, 13.3, 15.5, 10.0, 10.5, 0.7, 2.9)
    P.block("Chimney", 13.5, 15.3, 0.0, 10.0, 0.9, 2.7)
    P.marks["Door"] = (-1.0, FY, -13.0)
    P.marks["Inside"] = (0.0, FY, 0.0)
    P.lights += [(-1.0, 4.2, -9.5), (-12.0, 4.0, -9.0)]
    lean_piece(P, 0.012, 0.004, 3.0)
    return P


# ======================================================================================================================
# the Eyrie: Elder Kang Dal's residence, cliff-hung
# ======================================================================================================================
def eyrie():
    """The Eyrie, the Elder's house on its ledge in the cliff. Three volumes at three heights that lean on one another: the main room under a big lean-to roof that rises to the
    cliff, a tea nook that juts out over the drop on stilts and corbels (its floor level with the main room, its stilts 14 long), and a drying loft, a tall racked tower with a
    steep shed roof. A rope-railed deck joins them. The ledge is 20 wide (x -33..-13), the piece is centred on it. Floor 0 = the ledge's floor mesh."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    FY = 0.0
    # a stone footing along the cliff foot and a low retaining lip at the ledge's front
    stone_box(gs, -9.5, 1.5, 0.8, 6.8, -3.0, FY - 0.45, seed=4, batter=0.3, course=(1.2, 1.8), blen=(2.8, 4.4))
    K.box(gt, -9.0, 1.0, FY - 0.45, FY, 1.3, 6.3)
    P.floor.append((-9.5, 1.5, 0.8, 6.8, FY))
    # main room x -9 .. 1, z 1.3 .. 6.3, walls 5, the roof leaning against the cliff (the lean-to rises toward +z)
    wall_run(P, (-9.0, 1.3), (1.0, 1.3), FY, 5.2, thick=0.45, openings=[(3.6, 6.2, 0.0, 4.2), (0.8, 2.6, 1.6, 3.6)], seed=31, name="EyrieFront")
    wall_run(P, (-9.0, 1.3), (-9.0, 6.3), FY, 5.0, thick=0.45, openings=[(1.0, 3.2, 1.6, 3.6)], seed=32, name="EyrieSide")
    wall_run(P, (1.0, 1.3), (1.0, 6.3), FY, 5.0, thick=0.45, openings=[(1.2, 4.0, 0.0, 4.0)], seed=33, name="EyrieSide")
    posts_grid(P, [-9.0, -4.0, 1.0], 1.3, FY, 5.4, 0.7, lean=(0.0, -0.02), band=1.4)
    sub = WP()
    roof_shed(sub, -9.0, 1.0, -0.4, 7.4, 5.4, 12.6, over=2.2, rake=(1.2, 1.2), seed=51, row=0.95)
    P.absorb(sub)
    # the deck in front, over the ledge's lip, on stilts down the cliff
    FZ0 = -6.4
    K.box(gt, -10.0, 5.0, FY - 0.45, FY, FZ0, 1.3)
    P.block("Deck", -10.0, 5.0, FY - 1.2, FY, FZ0, 1.3)
    P.floor.append((-10.0, 5.0, FZ0, 1.3, FY))
    for x in (-9.0, -2.0, 4.0):
        post(gt, x, FZ0 + 0.5, -15.0, FY - 0.45, 0.7, lean=(0.0, 0.05), taper=0.05)
    beam(gt, (-9.0, -9.0, FZ0 + 0.5), (-2.0, -3.0, FZ0 + 0.5), 0.4, 0.4)
    beam(gt, (-2.0, -9.0, FZ0 + 0.5), (-9.0, -3.0, FZ0 + 0.5), 0.4, 0.4)
    beam(gt, (-2.0, -9.0, FZ0 + 0.5), (4.0, -3.0, FZ0 + 0.5), 0.4, 0.4)
    beam(gt, (4.0, -9.0, FZ0 + 0.5), (-2.0, -3.0, FZ0 + 0.5), 0.4, 0.4)
    corbels(P, -9.0, 4.0, FZ0, FY - 0.45, 1.6, steps=2, w=0.45, direction=1.0)
    rail(P, (-10.0, FZ0), (-4.6, FZ0), FY, h=1.15, every=2.7, suffix=S_TIMBER)
    rail(P, (0.6, FZ0), (5.0, FZ0), FY, h=1.15, every=2.2, suffix=S_TIMBER)
    rail(P, (5.0, FZ0), (5.0, 1.2), FY, h=1.15, every=2.5, suffix=S_TIMBER, skip_first=True)
    P.block("DeckRail", -10.0, -4.6, FY, FY + 1.2, FZ0 - 0.1, FZ0 + 0.15)
    P.block("DeckRail", 0.6, 5.0, FY, FY + 1.2, FZ0 - 0.1, FZ0 + 0.15)
    # the tea nook (to the right of the deck, on stilts over the drop): x 5 .. 12, z -5 .. 1.3
    NX0, NX1, NZ0, NZ1 = 5.0, 11.5, -4.5, 1.3
    K.box(gt, NX0, NX1, FY - 0.45, FY, NZ0, NZ1)
    P.block("Nook", NX0, NX1, FY - 1.2, FY, NZ0, NZ1)
    P.floor.append((NX0, NX1, NZ0, NZ1, FY))
    for (x, z) in ((NX1 - 0.4, NZ0 + 0.4), (NX1 - 0.4, NZ1 - 0.4), (NX0 + 1.5, NZ0 + 0.4)):
        post(gt, x, z, -14.0, 4.8, 0.7, lean=(0.025, 0.0), taper=0.05)
    beam(gt, (NX1 - 0.4, -9.0, NZ0 + 0.4), (NX0 + 1.5, -3.0, NZ0 + 0.4), 0.4, 0.4)
    corbels(P, NZ0 + 0.5, NZ1 - 0.5, NX1, FY - 0.45, 1.8, steps=2, w=0.45, direction=1.0) if False else None
    wall_run(P, (NX0, NZ1), (NX1, NZ1), FY, 4.8, thick=0.4, openings=[(0.0, 1.0, 0.0, 4.8)], seed=34, name="NookWall")
    wall_run(P, (NX1, NZ0), (NX1, NZ1), FY, 4.8, thick=0.4, openings=[(0.9, 4.7, 0.0, 4.2)], seed=35, name="NookWall")
    wall_run(P, (NX0, NZ0), (NX1, NZ0), FY, 1.5, thick=0.35, seed=36, name="NookRail")
    posts_grid(P, [NX0 + 0.4], NZ0 + 0.4, FY, 4.8, 0.6, lean=(0.02, 0.0), name="NookPost")
    sub = WP()
    roof_gable(sub, NX0 - 0.6, NX1 + 1.2, NZ0 - 1.4, NZ1 + 1.0, 4.9, 5.4, 0.0, 8.8, over=1.2, rake=(0.8, 0.6), seed=61, row=0.9, infill=False, finials=False)
    P.absorb(sub)
    P.marks["Elder"] = (-4.0, FY + 0.5, 3.6)
    P.marks["Deck"] = (-3.0, FY + 0.5, -3.0)
    P.lights.append((-4.0, 3.4, 3.6))
    lean_piece(P, 0.01, 0.0, 2.0)
    return P


# ======================================================================================================================
# the Gallery of Blades: the weapon exhibition hall
# ======================================================================================================================
def gallery():
    """The Gallery of Blades. A long hall whose roof is a COMB of five gables of different heights across its front (valleys between them), a row of square display windows,
    and at the outer end a lantern room that hangs past the rim of the pad on stilts and corbels: the Crosscurrent Saber's cradle is there, in the air over the slope,
    in front of a round lattice window. Piece x -17 .. 24, z -8.5 .. 8.5; the floor is 1.5 over the pad."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    FY = 0.0
    PX0, PX1, PZ0, PZ1 = -16.0, 12.0, -7.5, 7.5
    stone_box(gs, PX0, PX1, PZ0, PZ1, -5.5, FY - 0.5, seed=17, batter=0.35, course=(1.4, 2.0), blen=(3.2, 5.4))
    P.block("Podium", PX0, PX1, -8.0, FY, PZ0, PZ1)
    K.box(gt, PX0 + 0.4, PX1 - 0.4, FY - 0.5, FY, PZ0 + 0.4, PZ1 - 0.4)
    P.floor.append((PX0, PX1, PZ0, PZ1, FY))
    # steps at the front (two risers) in front of the door at x -9 .. -5
    rng = random.Random(7)
    rubble(gs, -10.5, -3.5, -2.8, -1.0, -9.4, -7.3, rng, j=0.05)
    P.block("Step", -10.5, -3.5, -2.8, -1.0, -9.4, -7.5)
    rubble(gs, -10.5, -3.5, -2.8, -0.0, -9.4, -8.5, rng, j=0.04) if False else None
    # walls
    W0, W1, WZ0, WZ1 = -15.0, 11.0, -6.5, 6.5
    ys = 6.2
    px_ = [W0 + 0.4 + i * (W1 - W0 - 0.8) / 5 for i in range(6)]
    posts_grid(P, px_, WZ0, FY, ys + 0.6, 0.8)
    posts_grid(P, px_, WZ1, FY, ys, 0.8)
    wins = [(1.4 + i * 5.2, 3.8 + i * 5.2, 1.6, 4.4) for i in range(5)]
    wins = [(a, b, c, d) for (a, b, c, d) in wins if not (3.0 < a < 8.0)]
    wall_run(P, (W0, WZ0), (W1, WZ0), FY, ys, thick=0.5, openings=[(5.6, 10.2, 0.0, 4.6)] + [w for w in wins if not (4.0 < w[0] < 11.0)], seed=41, name="FrontWall")
    wall_run(P, (W0, WZ1), (W1, WZ1), FY, ys, thick=0.5, seed=42, name="BackWall")
    wall_run(P, (W0, WZ0), (W0, WZ1), FY, ys, thick=0.5, seed=43, name="EndWallL")
    # the comb roof: five gables across the front, ridges along z; eave heights at the six lines and ridge heights per bay
    ex = [W0 - 0.6, W0 + 5.9, W0 + 11.8, W0 + 17.7, W0 + 23.6, W1 + 0.6]
    ex = [W0 - 0.6 + (W1 - W0 + 1.2) * i / 5 for i in range(6)]
    ee = [5.6, 6.4, 5.8, 6.6, 6.0, 6.4]
    rr = [9.4, 10.6, 9.0, 11.4, 10.0]
    zf, zb = WZ0 - 2.2, WZ1 + 1.0
    for k in range(5):
        xm = (ex[k] + ex[k + 1]) / 2
        zf_r, zb_r = zf + 1.0 * (k % 2), zb - 0.6 * (k % 3 == 1)
        roof_plane(P, (ex[k], ee[k], zf), (ex[k], ee[k], zb), (xm, rr[k], zf_r), (xm, rr[k], zb_r), seed=80 + k, row=0.95)
        roof_plane(P, (ex[k + 1], ee[k + 1], zb), (ex[k + 1], ee[k + 1], zf), (xm, rr[k], zb_r), (xm, rr[k], zf_r), seed=90 + k, row=0.95)
        cap_line(P, (xm, rr[k] + 0.02, zf_r), (xm, rr[k] + 0.02, zb_r), w=0.5, h=0.34, piece=2.0)
        finial(P, (xm, rr[k] + 0.3, zf_r + 0.1), h=0.9 + 0.2 * (k % 3))
        tri_prism(gt, (ex[k] + 0.3, ee[k] - 0.3, WZ0 - 0.3), (ex[k + 1] - 0.3, ee[k + 1] - 0.3, WZ0 - 0.3), (xm, rr[k] - 0.4, WZ0 - 0.3), 0.35, (0, 0, 1.0))
        round_disc(P, xm, (ee[k] + rr[k]) / 2 - 0.1, WZ0 - 0.4, 0.7, nz=-1.0, t=0.32)
        for xx in (ex[k], ex[k + 1]):
            pass
    # the lantern room at the outer end: x 13.5 .. 22, z -4 .. 4.5, hanging on stilts and corbels
    LX0, LX1, LZ0, LZ1 = 11.0, 21.5, -4.0, 4.5
    K.box(gt, LX0, LX1, FY - 0.5, FY, LZ0, LZ1)
    P.block("LanternFloor", LX0, LX1, FY - 1.2, FY, LZ0, LZ1)
    P.floor.append((LX0, LX1, LZ0, LZ1, FY))
    for (x, z) in ((LX1 - 0.5, LZ0 + 0.5), (LX1 - 0.5, LZ1 - 0.5), (LX1 - 3.5, LZ0 + 0.5), (LX1 - 3.5, LZ1 - 0.5)):
        post(gt, x, z, -16.0, 6.6, 0.75, lean=(0.03, 0.0), taper=0.05)
        P.block("LanternPost", x - 0.4, x + 0.4, FY, 6.6, z - 0.4, z + 0.4)
    for z in (LZ0 + 0.5, LZ1 - 0.5):
        beam(gt, (LX1 - 3.5, -13.0, z), (LX1 - 0.5, -2.0, z), 0.4, 0.4)
        beam(gt, (LX1 - 0.5, -13.0, z), (LX1 - 3.5, -2.0, z), 0.4, 0.4)
    corbels(P, LZ0 + 0.6, LZ1 - 0.6, LX1, FY - 0.5, 1.8, steps=2, w=0.45, direction=1.0) if False else None
    wall_run(P, (LX0, LZ0), (LX1, LZ0), FY, 6.0, thick=0.4, openings=[(1.0, 4.2, 1.6, 4.6)], seed=44, name="LanternWall")
    wall_run(P, (LX0, LZ1), (LX1, LZ1), FY, 6.0, thick=0.4, openings=[(1.0, 4.2, 1.6, 4.6)], seed=45, name="LanternWall")
    wall_run(P, (LX1, LZ0), (LX1, LZ1), FY, 6.0, thick=0.4, openings=[(2.2, 6.2, 1.8, 5.0)], seed=46, name="LanternWall")
    for yy in (2.0, 3.4, 4.8):                                                                                 # the lattice of the great round window: cross bars behind the opening
        beam(gt, (LX1 - 0.1, yy + 0.4, LZ0 + 2.2), (LX1 - 0.1, yy + 0.4, LZ1 - 2.2), 0.14, 0.14) if False else None
    sub = WP()
    roof_gable(sub, LZ0 - 0.8, LZ1 + 0.8, -1.3 - 0.0, 1.3, 6.1, 6.1, 0.0, 9.4, over=1.0, rake=(1.2, 1.4), seed=101, row=0.9, infill=False)
    P.absorb(sub, t=((LX0 + LX1) / 2 + 1.0, 0.0, (LZ0 + LZ1) / 2), yaw=PI / 2) if False else None
    sub = WP()
    roof_gable(sub, LX0 - 1.2, LX1 + 1.6, LZ0 - 0.8, LZ1 + 0.8, 6.1, 5.9, 0.4, 9.6, over=1.2, rake=(0.8, 1.2), seed=101, row=0.9)
    P.absorb(sub)
    # a tall bronze-capped post at the very end with a hanging chime
    P.marks["Saber"] = (19.0, FY + 1.0, 0.0)
    P.marks["Door"] = (-7.0, FY, -8.5)
    P.lights += [(18.0, 3.6, 0.0), (-6.0, 3.4, 0.0)]
    lean_piece(P, 0.008, 0.0, 2.0)
    return P


PIECES_BIG0 = {"RainHall": rain_hall, "Hq": hq, "Eyrie": eyrie, "Gallery": gallery}


BUILDERS = {}


# ======================================================================================================================
# the hearth yard: the NPC gathering area
# ======================================================================================================================
def hearth_yard():
    """The Hearth Yard: a great stone fire ring with a bronze cauldron on a tripod, log benches round it, and over it a patchwork tent of cloth awnings hung from a leaning mast and
    eight leaning poles of different heights (two sectors left open to the sky, so the smoke leaves). Ten NPCs stand on a ring 4.4 from the fire (the plan's spots). Ground is
    the pad (y 0 = the ground; nothing here has a floor). Footprint about 22 x 22."""
    P = WP()
    gs, gt, gb, gc = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE), P.geo(S_CLOTH)
    rng = random.Random(61)
    K.box(gs, -11.5, 11.5, -0.95, -0.1, -11.5, 11.5)      # (a buried footing: it ties the yard's pieces into one body, and lies under the ground)
    # the fire ring: ten stones round a bed of ash, a stone apron
    n = 10
    for i in range(n):
        a = TAU * i / n + 0.1
        cx, cz = 2.5 * math.cos(a), 2.5 * math.sin(a)
        w = rng.uniform(1.4, 1.8)
        rubble(gs, cx - w / 2, cx + w / 2, -0.62 - 0.03 * i, rng.uniform(0.9, 1.3), cz - 0.7, cz + 0.7, rng, j=0.18)
    K.box(gs, -2.0, 2.0, -0.5, 0.15, -2.0, 2.0)
    P.block("FireRing", -3.4, 3.4, -0.6, 1.2, -3.4, 3.4)
    # the tripod and the cauldron (bronze): three legs leaning together, a chain, a pot of three tapering drums
    for k in range(3):
        a = TAU * k / 3 + 0.5
        cyl(gt, (2.2 * math.cos(a), -0.2, 2.2 * math.sin(a)), (0.08 * math.cos(a), 5.4, 0.08 * math.sin(a)), 0.2, 0.15, seg=5)
    beam(gt, (0.0, 5.4, 0.0), (0.0, 3.6, 0.0), 0.08, 0.08)
    cyl(gb, (0, 1.6, 0), (0, 2.4, 0), 0.8, 1.15, seg=8)
    cyl(gb, (0, 2.4, 0), (0, 3.3, 0), 1.15, 1.3, seg=8, caps=False)
    ring_band(gb, 0.0, 3.2, 0.0, 1.3, 1.3, 3.2, 3.5, seg=8, t=0.12)
    # log benches round it (laid on the ground, cut flat on top)
    for i in range(7):
        a = TAU * (i + 0.5) / 7 + 0.35
        if 0.9 < (i % 7) < 1.1:
            continue
        cx, cz = 6.6 * math.cos(a), 6.6 * math.sin(a)
        ln = rng.uniform(3.4, 4.6)
        ux, uz = -math.sin(a), math.cos(a)
        cyl(gt, (cx - ux * ln / 2, 0.42, cz - uz * ln / 2), (cx + ux * ln / 2, 0.45, cz + uz * ln / 2), 0.55, 0.5, seg=6)
        pts = [(cx + dx * ux - dz * uz, cz + dx * uz + dz * ux) for dx in (-ln / 2, ln / 2) for dz in (-0.55, 0.55)]
        P.block("Bench", min(p[0] for p in pts), max(p[0] for p in pts), 0.0, 1.0, min(p[1] for p in pts), max(p[1] for p in pts))
    # the mast and the poles
    mast_top = (1.4, 11.6, -0.8)
    post(gt, 1.4 - 0.12, -0.8, 0.0, 11.6, 0.8, lean=(0.012, 0.0), taper=0.18)
    P.block("Mast", 0.9, 1.9, 0.0, 6.0, -1.3, -0.3)
    ring_band(gb, 1.45, 10.4, -0.8, 0.5, 0.5, 10.2, 10.7, seg=4, t=0.1, phase=PI / 4)
    finial(P, (1.55, 11.6, -0.8), h=1.2)
    poles = []
    for k, (a_deg, r, h) in enumerate(((10, 10.0, 7.0), (55, 9.0, 8.6), (100, 10.6, 6.6), (145, 9.4, 8.0), (200, 10.2, 7.4), (250, 9.0, 8.8), (300, 10.4, 6.8), (340, 9.6, 8.2))):
        a = math.radians(a_deg)
        x, z = r * math.cos(a), r * math.sin(a)
        lx, lz = -math.cos(a) * 0.03, -math.sin(a) * 0.03
        post(gt, x, z, -0.3, h, 0.6, lean=(-lx * -1.0, -lz * -1.0), taper=0.08)
        P.block("Pole", x - 0.4, x + 0.4, 0.0, h, z - 0.4, z + 0.4)
        poles.append((x - lx * -h, h, z - lz * -h))
        ring_band(gb, x, 2.0, z, 0.35, 0.35, 1.9, 2.2, seg=4, t=0.07, phase=PI / 4)
    # the awnings: a panel between the mast's top and the tops of two neighbouring poles, hanging in a different sag; sectors 2-3 and 6-7 left open
    for k in range(8):
        if k in (2, 6):
            continue
        a0, a1 = poles[k], poles[(k + 1) % 8]
        m0 = (mast_top[0] + 0.15, mast_top[1] - 0.5 - 0.5 * (k % 3), mast_top[2] + 0.1 * k)
        m1 = (mast_top[0] - 0.15, mast_top[1] - 0.9 - 0.4 * ((k + 1) % 3), mast_top[2] - 0.1 * k)
        awning(P, [m0, m1, (a1[0], a1[1] - 0.4, a1[2]), (a0[0], a0[1] - 0.2, a0[2])], sag=0.7, seed=70 + k, panels=2, thick=0.08, drop=0.5)
        rope_line(P, [(a0[0], a0[1] - 0.2, a0[2]), (m0[0], m0[1] + 0.3, m0[2])], r=0.07, suffix=S_TIMBER)
    # the stack of firewood on the open side
    for i in range(3):
        for j in range(3 - i):
            cyl(gt, (-9.5 + j * 0.9 + i * 0.45, 0.3 + i * 0.68, 7.2), (-9.5 + j * 0.9 + i * 0.45, 0.3 + i * 0.68, 11.0), 0.5, 0.5, seg=6)
    P.block("Firewood", -9.9, -7.0, 0.0, 2.4, 7.0, 11.2)
    P.marks["Fire"] = (0.0, 0.6, 0.0)
    P.lights.append((0.0, 3.0, 0.0))
    P.floor.append((-12.0, 12.0, -12.0, 12.0, 0.0))
    lean_piece(P, 0.0, 0.0, 0.0)
    return P


# ======================================================================================================================
# the training grounds
# ======================================================================================================================
def log_yard():
    """The Log Yard: a field of fourteen standing logs of different heights (1.8 to 5.2), their tops cut on a slant, some tied across with rope, some leaning: stakes to strike
    and hop between. Ground = y 0; collision: a box per log (jumpable ones are 1.8 high). Footprint 17 x 11."""
    P = WP()
    gt, gr = P.geo(S_TIMBER), P.geo(S_ROPE)
    rng = random.Random(77)
    spots = [(-7.0, -3.5), (-4.0, -4.2), (-1.0, -3.0), (2.5, -4.0), (6.0, -3.2), (7.5, 0.3), (4.5, 1.0), (1.2, 0.6), (-2.0, 1.2), (-5.5, 0.4), (-7.8, 2.8), (-3.5, 4.0), (1.0, 4.4), (5.5, 4.0)]
    hs = [5.2, 3.0, 4.4, 1.8, 3.8, 2.4, 5.0, 3.4, 1.8, 4.2, 2.8, 5.0, 2.2, 3.6]
    tops = []
    for (x, z), h in zip(spots, hs):
        lean = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
        r0 = 0.62 + 0.05 * rng.random()
        cyl(gt, (x, -0.5, z), (x + lean[0] * h, h, z + lean[1] * h), r0, r0 * 0.88, seg=7, caps=True)
        tx, tz = x + lean[0] * h, z + lean[1] * h
        K.box(gt, tx - 0.18, tx + 0.18, h - 0.1, h + 0.12, tz - 0.18, tz + 0.18) if False else None
        P.block("Log", x - 0.55, x + 0.55, 0.0, h, z - 0.55, z + 0.55)
        tops.append((tx, h, tz))
        ring_band(gt, tx, h - 0.9, tz, r0 * 0.9, r0 * 0.9, h - 1.0, h - 0.7, seg=7, t=0.1)
    for a, b in ((0, 1), (2, 3), (6, 7), (10, 11), (11, 12), (5, 4)):
        pa, pb = tops[a], tops[b]
        rope_line(P, catenary((pa[0], pa[1] - 0.8, pa[2]), (pb[0], pb[1] - 0.8, pb[2]), 0.4, 3), r=0.1, suffix=S_ROPE)
    P.floor.append((-9.0, 9.0, -6.0, 6.0, 0.0))
    return P


def rope_course():
    """The Wire Course: six tall poles in two rows carrying taut ropes at two heights and three hanging lines with bars, a rope net on the low end, a balance log on two trestles
    (1.0 high) beside the course, a bronze ring on the first pole. Ground = y 0. Footprint 19 x 8."""
    P = WP()
    gt, gr, gb = P.geo(S_TIMBER), P.geo(S_ROPE), P.geo(S_BRONZE)
    rng = random.Random(83)
    xs = [-8.0, 0.0, 8.0]
    for z in (-2.4, 2.4):
        for i, x in enumerate(xs):
            h = (8.4, 9.6, 7.6)[i] + (0.6 if z > 0 else 0.0)
            post(gt, x, z, -0.5, h, 0.7, lean=(0.0, -0.025 if z > 0 else 0.025), taper=0.1)
            P.block("Pole", x - 0.45, x + 0.45, 0.0, h, z - 0.45, z + 0.45)
            ring_band(gb, x, 1.4, z, 0.52, 0.52, 1.3, 1.7, seg=4, t=0.09, phase=PI / 4)
    for z in (-2.4, 2.4):
        rope_line(P, catenary((-8.0, 8.0, z), (0.0, 9.0, z), 0.5, 5) + catenary((0.0, 9.0, z), (8.0, 7.0, z), 0.5, 5)[1:], r=0.09)
        rope_line(P, catenary((-8.0, 3.6, z), (0.0, 3.8, z), 0.35, 5) + catenary((0.0, 3.8, z), (8.0, 3.4, z), 0.35, 5)[1:], r=0.09)
    for x, drop in ((-4.0, 3.2), (2.0, 4.4), (5.6, 3.6)):
        rope_line(P, [(x, 8.4, 0.0), (x, 8.4 - drop, 0.0)], r=0.08)
        beam(gt, (x - 0.7, 8.4 - drop, 0.0), (x + 0.7, 8.4 - drop, 0.0), 0.2, 0.2)
    for i in range(7):                                                                  # the net at the first pair
        rope_line(P, [(-8.0, 0.4 + i * 0.9, -2.4), (-8.0, 0.4 + i * 0.9 + 0.2, 2.4)], r=0.07)
    rope_line(P, [(-8.0, 0.4, 0.0), (-8.0, 6.6, 0.0)], r=0.07)
    # the balance log on trestles, beside the course
    cyl(gt, (-9.0, 0.5, 6.2), (9.0, 0.5, 6.2), 0.5, 0.45, seg=7)
    for x in (-7.5, 0.0, 7.5):
        beam(gt, (x - 0.5, 0.0, 6.2 - 0.6), (x, 0.7, 6.2), 0.3, 0.3)
        beam(gt, (x + 0.5, 0.0, 6.2 - 0.6), (x, 0.7, 6.2), 0.3, 0.3)
        beam(gt, (x - 0.5, 0.0, 6.2 + 0.6), (x, 0.7, 6.2), 0.3, 0.3)
        beam(gt, (x + 0.5, 0.0, 6.2 + 0.6), (x, 0.7, 6.2), 0.3, 0.3)
    P.block("Balance", -9.0, 9.0, 0.0, 1.0, 5.7, 6.7)
    P.floor.append((-10.0, 10.0, -4.0, 8.0, 0.0))
    return P


def stone_ring():
    """The Stone Ring: a round sparring floor of fitted slabs (0.8 over the ground, walkable) inside a wall of boulders 1.8 high with four gaps (to enter by), and two leaning
    judge's posts with a bronze band. Radius 8.5. Ground = y 0."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    rng = random.Random(91)
    R = 7.6
    K.prism(gs, [(R * math.cos(TAU * i / 16), R * math.sin(TAU * i / 16)) for i in range(16)], -0.6, 0.8, caps="TB")
    P.block("Dais", -R + 0.6, R - 0.6, -0.6, 0.8, -R + 0.6, R - 0.6)
    # joints: a cross of flat slabs standing 0.05 proud, so the floor reads as slabs
    for i in range(3):
        K.box(gs, -R * 0.8, R * 0.8, 0.8, 0.9, -1.5 + i * 1.5 - 0.12, -1.5 + i * 1.5 + 0.12) if False else None
    n = 22
    for i in range(n):
        a = TAU * i / n
        if any(abs(((a - g) + PI) % TAU - PI) < 0.45 for g in (0.0, PI / 2, PI, 3 * PI / 2)):
            continue
        cx, cz = 8.4 * math.cos(a), 8.4 * math.sin(a)
        w = rng.uniform(1.8, 2.6)
        h = rng.uniform(1.4, 2.2)
        ux, uz = -math.sin(a), math.cos(a)
        ring = [(cx - ux * w / 2 - math.cos(a) * 1.3, cz - uz * w / 2 - math.sin(a) * 1.3), (cx + ux * w / 2 - math.cos(a) * 1.3, cz + uz * w / 2 - math.sin(a) * 1.3),
                (cx + ux * w / 2 + math.cos(a) * 0.9, cz + uz * w / 2 + math.sin(a) * 0.9), (cx - ux * w / 2 + math.cos(a) * 0.9, cz - uz * w / 2 + math.sin(a) * 0.9)]
        ring = [(x + rng.uniform(-0.15, 0.15), z + rng.uniform(-0.15, 0.15)) for x, z in ring]
        hex8(gs, [(x, -0.6, z) for x, z in ring] + [(x, h, z) for x, z in ring])
        P.block("RingWall", cx - w / 2 - 0.3, cx + w / 2 + 0.3, 0.0, h, cz - w / 2 - 0.3, cz + w / 2 + 0.3)
    for a in (0.7, 3.9):
        x, z = 8.2 * math.cos(a), 8.2 * math.sin(a)
        post(gt, x, z, 1.0, 5.4, 0.45, lean=(-0.05 * math.cos(a), -0.05 * math.sin(a)), taper=0.06)
        ring_band(gb, x - 0.05 * math.cos(a) * 3, 4.0, z - 0.05 * math.sin(a) * 3, 0.4, 0.4, 3.9, 4.2, seg=4, t=0.07, phase=PI / 4)
        P.block("JudgePost", x - 0.4, x + 0.4, 0.0, 5.0, z - 0.4, z + 0.4)
    P.floor.append((-R + 0.8, R - 0.8, -R + 0.8, R - 0.8, 0.8))
    return P


def swing_logs():
    """The Swing Frame: a gallows frame of two leaning A-frames and a high beam from which three heavy logs hang on ropes (to dodge and to strike). Ground = y 0. 12 x 4."""
    P = WP()
    gt, gr = P.geo(S_TIMBER), P.geo(S_ROPE)
    for x in (-5.5, 5.5):
        for z in (-1.4, 1.4):
            beam(gt, (x, -0.4, z * 1.5), (x * 0.92, 9.0, 0.0), 0.55, 0.55)
        P.block("Frame", x - 0.8, x + 0.8, 0.0, 6.0, -2.4, 2.4)
    beam(gt, (-6.0, 9.0, 0.0), (6.0, 9.0, 0.0), 0.7, 0.8)
    beam(gt, (-5.0, 7.0, 0.0), (5.0, 7.0, 0.0), 0.4, 0.4)
    for x, ln in ((-2.8, 5.4), (0.4, 6.2), (3.4, 4.8)):
        rope_line(P, [(x - 0.4, 9.0, 0.0), (x - 0.1, 9.0 - ln + 1.6, 0.0)], r=0.09)
        rope_line(P, [(x + 0.4, 9.0, 0.0), (x + 0.1, 9.0 - ln + 1.6, 0.0)], r=0.09)
        cyl(gt, (x, 9.0 - ln + 1.6 - 0.0, 0.0), (x + 0.1, 9.0 - ln - 1.4, 0.0), 0.7, 0.7, seg=7)
    P.floor.append((-7.0, 7.0, -3.0, 3.0, 0.0))
    return P


# ======================================================================================================================
# bridges
# ======================================================================================================================
def rope_bridge(L=20.0, w=4.6, sag=0.9, drop=0.0, tower_h=7.5, name="Bridge", seed=5, hang=4.0):
    """A suspension bridge along x from -L/2 (deck y 0) to +L/2 (deck y -drop): plank deck hung on stringers, two hand ropes and two main cables from timber A-frame towers at each
    end (two posts each side, braced, a bronze cap), hangers every `hang` studs, a rail guard. The deck sags `sag` in the middle; the deck's planks lie across (z). Collision: the
    deck in 1.5-stud boxes following the sag (steps of at most 0.25) and a guard along each edge. The towers stand on the abutment (the plan adds stone)."""
    P = WP()
    rng = random.Random(seed)
    gp, gt, gr, gb = P.geo(S_PLANK), P.geo(S_TIMBER), P.geo(S_ROPE), P.geo(S_BRONZE)

    def deck_y(x):
        t = (x + L / 2) / L
        return -drop * t - sag * 4 * t * (1 - t)
    n = int(L / 1.5)
    seg = L / n
    for i in range(n):
        xa, xb = -L / 2 + i * seg, -L / 2 + (i + 1) * seg
        xm = (xa + xb) / 2
        y = deck_y(xm)
        # two planks per segment, laid across, slightly different (a worn deck)
        for k in range(2):
            x0, x1 = xa + k * seg / 2 + 0.03, xa + (k + 1) * seg / 2 - 0.03
            yy = y + rng.uniform(-0.03, 0.03)
            hex8(gp, [(x0, yy - 0.34, -w / 2 - rng.uniform(0.0, 0.2)), (x1, yy - 0.34, -w / 2), (x1, yy - 0.34, w / 2), (x0, yy - 0.34, w / 2 + rng.uniform(0.0, 0.2)),
                      (x0, yy, -w / 2 - 0.1), (x1, yy, -w / 2), (x1, yy, w / 2), (x0, yy, w / 2 + 0.1)])
        P.block("Deck", xa, xb + 0.02, y - 1.2, y + 0.02, -w / 2, w / 2)
        P.block("Guard", xa, xb + 0.02, y, y + 1.2, -w / 2 - 0.3, -w / 2 + 0.05)
        P.block("Guard", xa, xb + 0.02, y, y + 1.2, w / 2 - 0.05, w / 2 + 0.3)
    for z in (-w / 2 + 0.1, w / 2 - 0.1):                                       # the stringers under the deck, the hand rope above
        pts = [(x, deck_y(x) - 0.45, z) for x in [-L / 2 + L * i / n for i in range(n + 1)]]
        for a, b in zip(pts, pts[1:]):
            cyl(gt, a, b, 0.17, 0.17, seg=4, caps=False)
    towers = (-L / 2, L / 2)
    top = {}
    for xt in towers:
        yb = deck_y(xt)
        for z in (-w / 2 - 0.55, w / 2 + 0.55):
            post(gt, xt, z, yb - 1.2, yb + tower_h, 0.62, lean=(0.04 if xt < 0 else -0.04, 0.045 if z < 0 else -0.045), taper=0.08)
            P.block("Tower", xt - 0.4, xt + 0.4, yb - 0.5, yb + tower_h, z - 0.4, z + 0.4)
        zt = w / 2 + 0.55 - 0.045 * (tower_h + 1.2) * 0.0
        beam(gt, (xt + (0.04 if xt < 0 else -0.04) * tower_h, yb + tower_h, -w / 2 - 0.55 + 0.045 * tower_h), (xt + (0.04 if xt < 0 else -0.04) * tower_h, yb + tower_h, w / 2 + 0.55 - 0.045 * tower_h), 0.5, 0.5)
        beam(gt, (xt, yb + 2.6, -w / 2 - 0.55), (xt, yb + 2.6, w / 2 + 0.55), 0.4, 0.4)
        ring_band(gb, xt + (0.04 if xt < 0 else -0.04) * tower_h * 0.9, yb + tower_h - 0.5, -w / 2 - 0.55 + 0.045 * tower_h * 0.9, 0.42, 0.42, yb + tower_h - 0.7, yb + tower_h - 0.3, seg=4, t=0.08, phase=PI / 4)
        ring_band(gb, xt + (0.04 if xt < 0 else -0.04) * tower_h * 0.9, yb + tower_h - 0.5, w / 2 + 0.55 - 0.045 * tower_h * 0.9, 0.42, 0.42, yb + tower_h - 0.7, yb + tower_h - 0.3, seg=4, t=0.08, phase=PI / 4)
        top[xt] = (xt + (0.04 if xt < 0 else -0.04) * tower_h, yb + tower_h)
    for z in (-w / 2 - 0.2, w / 2 + 0.2):                                     # the main cables: tower top to tower top hanging low, with hangers to the hand ropes
        a = (top[towers[0]][0], top[towers[0]][1] - 0.4, z * 0.8)
        b = (top[towers[1]][0], top[towers[1]][1] - 0.4, z * 0.8)
        cab = catenary(a, b, min(tower_h - 3.0, 4.0), 14)
        rope_line(P, cab, r=0.13)
        hand = [(x, deck_y(x) + 1.25, z) for x in [-L / 2 + L * i / n for i in range(n + 1)]]
        rope_line(P, hand, r=0.1)
        hx = -L / 2 + hang
        while hx < L / 2 - 1.0:
            t = (hx - a[0]) / (b[0] - a[0])
            cy = a[1] * (1 - t) + b[1] * t - min(tower_h - 3.0, 4.0) * 4 * t * (1 - t)
            rope_line(P, [(hx, cy, z * 0.8), (hx, deck_y(hx) + 1.25, z)], r=0.06)
            hx += hang
    P.floor.append((-L / 2, L / 2, -w / 2, w / 2, 0.0))
    P.marks["End"] = (L / 2, -drop, 0.0)
    return P


def gorge_bridge():
    return rope_bridge(L=14.5, w=4.4, sag=0.6, drop=0.0, tower_h=6.4, seed=5, hang=3.6)


def great_span():
    return rope_bridge(L=33.0, w=4.6, sag=1.6, drop=6.0, tower_h=7.6, seed=9, hang=4.4)


# ======================================================================================================================
# stairs, landings, walls, gates
# ======================================================================================================================
def stair_flight(n=11, width=6.0, tread=1.5):
    """A flight of n one-stud risers along +z from (x 0, z 0) at y 0 (the lowest tread's top is y 1): rubble treads, stepped flank walls a stud over the treads with a
    timber post and rope rail on both sides. Collision: a box per step and per flank block."""
    P = WP()
    gs, gt = P.geo(S_STONE), P.geo(S_TIMBER)
    rng = random.Random(100 + n)
    for k in range(n):
        za, zb = k * tread, (k + 1) * tread
        top = float(k + 1)
        rubble(gs, -width / 2, width / 2, top - 2.6, top, za - 0.04, zb + 0.02, rng, j=0.05)
        P.block("Step", -width / 2, width / 2, top - 2.6, top, za, zb + (0.4 if k == n - 1 else 0.0))
        for sx in (-1, 1):
            xa, xb = (width / 2 + 0.05, width / 2 + 1.25) if sx > 0 else (-width / 2 - 1.25, -width / 2 - 0.05)
            rubble(gs, xa, xb, top - 2.6, top + 0.9 + 0.05 * rng.random(), za - 0.04, zb + 0.02, rng, j=0.08)
            P.block("Flank", xa, xb, top - 2.6, top + 0.95, za, zb)
    # rails: posts on the flanks every 3 steps and a rope on the outside edge
    for sx in (-1, 1):
        x = sx * (width / 2 + 0.65)
        pts = []
        for k in range(0, n + 1, 3):
            z = min(k * tread, n * tread - 0.2)
            y = float(min(k, n - 1) + 1) + 0.95
            post(gt, x, z + 0.3, y - 0.1, y + 1.5, 0.3, taper=0.03)
            pts.append((x, y + 1.35, z + 0.3))
        rope_line(P, pts, r=0.09, suffix=S_TIMBER)
    P.floor.append((-width / 2, width / 2, 0.0, n * tread, 0.0))
    P.marks["Top"] = (0.0, float(n), n * tread)
    return P


def landing(w=6.0, d=5.0, h=3.0):
    """A stone landing: a rubble slab w x d, its top at y 0, buried h deep, a rope rail round the outer sides is left to the plan (the stairs' flanks meet it)."""
    P = WP()
    gs = P.geo(S_STONE)
    stone_box(gs, -w / 2 - 1.2, w / 2 + 1.2, 0.0, d, -h, -0.1, seed=12, batter=0.2, course=(1.1, 1.6), blen=(2.0, 3.4))
    P.block("Landing", -w / 2 - 1.2, w / 2 + 1.2, -h, 0.0, 0.0, d)
    P.floor.append((-w / 2, w / 2, 0.0, d, 0.0))
    return P


def cleft_stair():
    """The Cleft Stair: a timber stair hung in the gorge against its right wall, descending along +z: twelve one-stud risers from the pad's rim (y 0) to the Drip ledge
    (y -12), tread 1.5, 3.6 wide, plank treads on two long stringers braced to the rock by brackets, a rope rail on the void side. Starts at x 0, z 0."""
    P = WP()
    gt, gp, gr = P.geo(S_TIMBER), P.geo(S_PLANK), P.geo(S_ROPE)
    n, tread, w = 12, 1.5, 3.6
    for k in range(n):
        za, zb = k * tread, (k + 1) * tread
        top = -float(k + 1)
        K.box(gp, 0.0, w, top - 0.35, top, za, zb - 0.06)
        P.block("Step", 0.0, w, top - 1.6, top, za, zb)
    for x in (0.2, w - 0.2):
        beam(gt, (x, -0.3, -0.3), (x, -n - 0.9, n * tread), 0.45, 0.8, up=(0, 1, 0))
    for k in range(0, n, 3):
        z = k * tread + 0.4
        beam(gt, (0.0, -float(k + 1) - 0.4, z), (-1.2, -float(k + 1) + 0.6, z), 0.3, 0.3)
        beam(gt, (w, -float(k + 1) - 0.4, z), (w + 0.0, -float(k + 1) - 2.8, z + 0.0), 0.3, 0.3) if False else None
    x = w + 0.1
    pts = []
    for k in range(0, n + 1, 2):
        z = min(k * tread, n * tread - 0.3)
        y = -float(min(k, n - 1) + 1)
        post(gt, x, z + 0.2, y - 0.2, y + 1.3, 0.28, taper=0.03)
        pts.append((x, y + 1.15, z + 0.2))
    rope_line(P, pts, r=0.09, suffix=S_ROPE)
    P.block("Apron", -3.6, 0.3, -3.0, -0.4, -0.5, 3.5)      # (the stair stands 2 studs out from the slot's edge, where the 4-stud columns hang over it: an invisible apron bridges the lane's edge to the first step)
    P.floor.append((0.0, w, 0.0, n * tread, 0.0))
    P.marks["Bottom"] = (w / 2, -float(n), n * tread + 1.0)
    return P


def wall_rough(L=8.0, h=3.4):
    """A rubble wall L long, 1.6 thick at the foot and 1.1 at the top, h high, a timber coping with leaning posts every 4 studs: the courtyards' walls."""
    P = WP()
    gs, gt = P.geo(S_STONE), P.geo(S_TIMBER)
    stone_wall(gs, (-L / 2, 0.0), (L / 2, 0.0), h, 1.6, 1.2, y0=-1.2, course=(1.1, 1.5), blen=(2.2, 3.6), seed=int(L * 3) + 5, j=0.12)
    beam(gt, (-L / 2 - 0.2, h + 0.12, 0.0), (L / 2 + 0.2, h + 0.12, 0.0), 0.7, 0.35)
    n = max(2, int(L / 4.0) + 1)
    for i in range(n):
        x = -L / 2 + 0.4 + (L - 0.8) * i / (n - 1)
        post(gt, x, 0.0, h, h + 1.5 + 0.35 * (i % 2), 0.3, lean=(0.03 * (1 if i % 2 else -1), 0.0), taper=0.04)
    P.block("Wall", -L / 2, L / 2, -1.2, h, -0.85, 0.85)
    return P


def moss_gate():
    """The Moss Court's door: two leaning stone piers and a heavy timber lintel strapped in bronze, an opening 4 wide and 5.4 high; a low stone coping each side."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    for sx in (-1, 1):
        stone_box(gs, sx * 3.4 - 1.5, sx * 3.4 + 1.5, -1.5, 1.5, -1.2, 6.4, seed=7 + sx, batter=0.3, course=(1.1, 1.6), blen=(1.8, 3.0))
        P.block("Pier", sx * 3.4 - 1.6, sx * 3.4 + 1.6, -1.2, 6.4, -1.6, 1.6)
    beam(gt, (-5.4, 6.0, 0.0), (5.4, 6.4, 0.0), 1.1, 1.1)
    for sx in (-1, 1):
        ring_band(gb, sx * 3.6, 6.2, 0.0, 0.6, 0.62, 5.7, 6.7, seg=4, t=0.1, phase=PI / 4)
    beam(gt, (-2.6, 5.4, 0.0), (-1.0, 6.0, 0.0), 0.5, 0.5)
    beam(gt, (2.6, 5.4, 0.0), (1.0, 6.0, 0.0), 0.5, 0.5)
    P.block("Lintel", -5.4, 5.4, 5.6, 6.9, -0.6, 0.6)
    lean_piece(P, 0.0, 0.0, 0.0)
    return P


# ======================================================================================================================
# the Perch and the Drip shrine
# ======================================================================================================================
def perch_pavilion():
    """The Windbell Perch on the left ledge: an open pavilion on a low stone base, four leaning posts, a small hip roof, and the great bronze bell (1.8 radius) hung from the
    roof beam, its rope trailing to a post. Base 9 x 9, floor 0, 7 high."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    stone_box(gs, -4.8, 4.8, -4.8, 4.8, -2.4, -0.1, seed=14, batter=0.3, course=(1.1, 1.6), blen=(2.4, 4.0))
    K.box(gt, -4.4, 4.4, -0.45, 0.0, -4.4, 4.4)
    P.block("Base", -4.8, 4.8, -2.4, 0.0, -4.8, 4.8)
    P.floor.append((-4.8, 4.8, -4.8, 4.8, 0.0))
    for (x, z) in ((-3.4, -3.4), (3.4, -3.4), (-3.4, 3.4), (3.4, 3.4)):
        post(gt, x, z, 0.0, 6.4, 0.75, lean=(-0.012 * (1 if x > 0 else -1), -0.012 * (1 if z > 0 else -1)), taper=0.06)
        P.block("Post", x - 0.45, x + 0.45, 0.0, 6.4, z - 0.45, z + 0.45)
        ring_band(gb, x, 1.6, z, 0.45, 0.45, 1.5, 1.9, seg=4, t=0.08, phase=PI / 4)
    beam(gt, (-3.6, 6.1, 0.0), (3.6, 6.1, 0.0), 0.8, 0.9)
    for z in (-3.4, 3.4):
        beam(gt, (-3.6, 5.7, z), (3.6, 5.7, z), 0.6, 0.7)
    roof_hip(P, 0.0, 0.0, 3.8, 3.8, 6.3, 10.2, ridge=(0.5, 0.0), over=1.6, seed=111, row=0.95, rx=1.2)
    bell(P, 0.0, 6.0, 0.0, r=1.7, h=2.8)
    rope_line(P, [(0.0, 2.4, 0.6), (1.4, 1.0, 2.6), (3.0, 1.0, 3.2)], r=0.1, suffix=S_TIMBER)
    lean_piece(P, 0.01, 0.0, 1.0)
    return P


def drip_shrine():
    """The Drip Shrine on the ledge in the gorge: a stone niche (2.4 wide, 3 high) set in a low wall, a bronze bell hanging under a small timber hood roofed in tile, a stone
    bowl under the falls' drip. Floor 0, 6 wide."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    stone_wall(gs, (-3.0, 1.6), (3.0, 1.6), 3.0, 1.3, 1.0, y0=-1.0, course=(1.0, 1.4), blen=(1.6, 2.6), seed=44, gaps=[(2.1, 3.9)], j=0.1)
    K.box(gs, -1.4, 1.4, 3.0, 3.3, 1.0, 2.2)
    P.block("ShrineWall", -3.0, 3.0, -1.0, 3.0, 0.9, 2.3)
    post(gt, -1.3, 0.4, 0.0, 4.4, 0.4, lean=(0.0, 0.02), taper=0.04)
    post(gt, 1.3, 0.4, 0.0, 4.4, 0.4, lean=(0.0, 0.02), taper=0.04)
    sub = WP()
    roof_shed(sub, -1.9, 1.9, -0.6, 1.9, 4.2, 5.8, over=0.5, rake=(0.4, 0.4), seed=121, row=0.8, th=0.4)
    P.absorb(sub)
    bell(P, 0.0, 4.0, 0.5, r=0.7, h=1.2)
    ring_band(gs, 2.2, -0.2, 0.0, 0.8, 0.8, -0.2, 0.5, seg=8, t=0.25)
    P.block("Bowl", 1.2, 3.2, 0.0, 0.5, -1.0, 1.0)
    P.floor.append((-3.0, 3.0, -2.0, 1.6, 0.0))
    return P


# ======================================================================================================================
# props
# ======================================================================================================================
def bench():
    P = WP()
    gt = P.geo(S_TIMBER)
    K.box(gt, -2.3, 2.3, 1.15, 1.45, -0.5, 0.5)
    for x in (-1.7, 1.7):
        post(gt, x, 0.0, 0.0, 1.2, 0.4, d=0.9, lean=(0.0, 0.0), taper=0.0)
    beam(gt, (-1.7, 0.5, 0.0), (1.7, 0.5, 0.0), 0.2, 0.2)
    P.block("Bench", -2.4, 2.4, 0.0, 1.5, -0.55, 0.55)
    return P


def lantern_post():
    """A leaning timber post with an arm and a hanging lantern (the glow is the `Lamp` mesh); a bronze band; 5.6 high."""
    P = WP()
    gt, gb = P.geo(S_TIMBER), P.geo(S_BRONZE)
    post(gt, 0.0, 0.0, -0.3, 5.6, 0.5, lean=(0.03, 0.0), taper=0.06)
    beam(gt, (0.15, 5.1, 0.0), (1.9, 5.5, 0.0), 0.25, 0.3)
    beam(gt, (0.2, 4.0, 0.0), (1.4, 5.1, 0.0), 0.18, 0.18)
    ring_band(gb, 0.1, 3.0, 0.0, 0.32, 0.32, 2.9, 3.2, seg=4, t=0.07, phase=PI / 4)
    pos = lantern_hang(P, 1.9, 5.5, 0.0, h=1.3, w=0.85, cord=0.9)
    P.block("Post", -0.4, 0.5, 0.0, 5.6, -0.4, 0.4)
    P.lights.append(pos)
    return P


def banner_pole():
    """A 10-high leaning pole, a bronze cap, two cloth banners hung from yards of different length and a streamer; the plaza's banners are plain, these are the Hold's."""
    P = WP()
    gt, gb, gc = P.geo(S_TIMBER), P.geo(S_BRONZE), P.geo(S_CLOTH)
    post(gt, 0.0, 0.0, -0.4, 10.0, 0.5, lean=(0.025, 0.0), taper=0.08)
    finial(P, (0.25, 10.0, 0.0), h=1.0)
    for y, ln, w in ((9.0, 2.6, 4.6), (6.3, 1.8, 3.0)):
        beam(gt, (0.2, y, 0.0), (-w * 0.5, y + 0.2, 0.0), 0.18, 0.18)
        K.box(gb, -w * 0.5 - 0.1, -w * 0.5 + 0.1, y, y + 0.3, -0.1, 0.1) if False else None
        awning(P, [(0.3, y - 0.1, 0.0), (-w * 0.5 + 0.2, y + 0.1, 0.0), (-w * 0.5 + 0.1, y - ln, 0.0), (0.3, y - ln, 0.0)], sag=0.15, seed=int(y * 7), panels=3, thick=0.07, drop=0.45)
    P.block("Pole", -0.4, 0.6, 0.0, 10.0, -0.4, 0.4)
    return P


def weapon_rack():
    """A timber rack for the Gallery: two leaning uprights, three cross rails with bronze pegs; 4 wide, 4.4 high."""
    P = WP()
    gt, gb = P.geo(S_TIMBER), P.geo(S_BRONZE)
    for x in (-1.9, 1.9):
        post(gt, x, 0.0, -0.2, 4.4, 0.35, lean=(0.0, 0.03), taper=0.04)
    for y in (1.2, 2.5, 3.8):
        beam(gt, (-2.0, y, 0.15), (2.0, y, 0.15), 0.25, 0.25)
        for i in range(5):
            x = -1.5 + i * 0.75
            beam(gb, (x, y, 0.1), (x, y + 0.45, -0.2), 0.12, 0.12)
    P.block("Rack", -2.2, 2.2, 0.0, 4.4, -0.3, 0.4)
    return P


def cradle():
    """The Crosscurrent Saber's cradle: two carved timber uprights leaning together with a bronze crossbar and two bronze-lipped saddles, on a stone-footed timber base; the saber
    lies along x on the saddles at y 3.0 (the plan's SaberDisplay mark). 6 wide, 4.2 high."""
    P = WP()
    gt, gb, gs = P.geo(S_TIMBER), P.geo(S_BRONZE), P.geo(S_STONE)
    K.box(gs, -3.4, 3.4, -0.2, 0.5, -1.4, 1.4)
    P.block("Plinth", -3.4, 3.4, -0.2, 0.6, -1.4, 1.4)
    for x in (-2.3, 2.3):
        beam(gt, (x, 0.4, 0.0), (x * 0.82, 4.0, 0.0), 0.6, 0.45, up=(0, 0, 1))
        K.box(gb, x * 0.9 - 0.45, x * 0.9 + 0.45, 2.55, 2.85, -0.55, 0.55)
        beam(gb, (x * 0.84 - 0.4, 3.55, 0.0), (x * 0.84 + 0.4, 3.55, 0.0), 0.15, 0.15) if False else None
    for x in (-1.6, 1.6):
        K.box(gb, x - 0.4, x + 0.4, 2.85, 3.0, -0.4, 0.4)
        K.box(gb, x - 0.4, x - 0.25, 3.0, 3.35, -0.4, 0.4)
        K.box(gb, x + 0.25, x + 0.4, 3.0, 3.35, -0.4, 0.4)
    beam(gb, (-2.0, 4.1, 0.0), (2.0, 4.1, 0.0), 0.22, 0.22)
    P.marks["Saber"] = (0.0, 3.2, 0.0)
    return P


def waymarker():
    """A waymarker: three leaning stone slabs stacked against a timber post with a bronze band and a hooked top (a place name for people who read the road): 4.4 high."""
    P = WP()
    gs, gt, gb = P.geo(S_STONE), P.geo(S_TIMBER), P.geo(S_BRONZE)
    rng = random.Random(33)
    for i, (w, h, lean) in enumerate(((2.2, 3.4, 0.08), (1.6, 2.4, -0.1), (1.2, 1.6, 0.12))):
        rubble(gs, -w / 2 + i * 0.5 - 0.8, w / 2 + i * 0.5 - 0.8, -0.5 - 0.15 * i, h, -0.5 + i * 0.4, 0.5 + i * 0.4, rng, j=0.08)
    post(gt, 0.6, 0.0, -0.3, 4.4, 0.35, lean=(0.04, 0.0), taper=0.05)
    beam(gt, (0.75, 4.1, 0.0), (1.6, 3.6, 0.0), 0.2, 0.2)
    ring_band(gb, 0.7, 2.6, 0.0, 0.25, 0.25, 2.5, 2.8, seg=4, t=0.07, phase=PI / 4)
    P.block("Marker", -1.9, 1.0, 0.0, 3.4, -0.6, 1.2)
    return P


def scaffold_piece(w=6.0, d=5.0, h=12.0, bays=2, levels=3, seed=1):
    P = WP()
    scaffold(P, -w / 2, w / 2, -d / 2, d / 2, 0.0, h, bays=bays, levels=levels, seed=seed, lean=(0.012, 0.0))
    return P


def scaffold_a():
    return scaffold_piece(7.0, 4.5, 15.0, 3, 4, 3)


def scaffold_b():
    return scaffold_piece(4.5, 4.0, 10.0, 2, 3, 5)


def scaffold_c():
    return scaffold_piece(3.5, 3.0, 11.0, 1, 3, 8)


def rim_rail(L=8.0):
    """A rope rail along an edge: leaning posts every 2.7 studs, a hand rope and a knee rope (no collision: the plan puts a low guard box under it)."""
    P = WP()
    rail(P, (-L / 2, 0.0), (L / 2, 0.0), 0.0, h=1.2, every=2.7, lean=(0.0, 0.0))
    P.block("RimGuard", -L / 2, L / 2, 0.0, 1.2, -0.15, 0.15)
    return P


COURT_BUILDERS = {"RimRail8": lambda: rim_rail(8.0), "WallRough2": lambda: wall_rough(1.8), "WallRough3": lambda: wall_rough(3.2), "WallRough6": lambda: wall_rough(6.0),"GorgeBridge": gorge_bridge, "GreatSpan": great_span, "Flight11": lambda: stair_flight(11), "Landing": landing,
                  "CleftStair": cleft_stair, "WallRough8": lambda: wall_rough(8.0), "WallRough12": lambda: wall_rough(12.0), "MossGate": moss_gate}
PROP_BUILDERS = {"Bench": bench, "LanternPost": lantern_post, "BannerPole": banner_pole, "WeaponRack": weapon_rack, "Cradle": cradle, "Waymarker": waymarker,
                 "ScaffoldA": scaffold_a, "ScaffoldB": scaffold_b, "ScaffoldC": scaffold_c}
BUILDING_BUILDERS = {"RainHall": rain_hall, "Hq": hq, "Eyrie": eyrie, "Gallery": gallery, "HearthYard": hearth_yard, "LogYard": log_yard, "RopeCourse": rope_course,
                     "StoneRing": stone_ring, "SwingLogs": swing_logs, "PerchPavilion": perch_pavilion, "DripShrine": drip_shrine}

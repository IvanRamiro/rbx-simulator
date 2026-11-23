"""nightfall_arch: the buildings, stairs, walls, bridge and props of Nightfall Citadel (2026-11-23), built from nightfall_kit. Plain Python, no Blender.

Every builder returns an NP: geometry split by material suffix (at most four), the invisible collision boxes (piece.col axis-aligned, piece.rcol turned ones), named marks, light spots,
effect spots and the floor rectangles. Frames: x right, y up, z back (front = -Z); y = 0 is the floor (or the ground a ground-level piece stands on); feet sink below.
"""
import math
import random

import hq_kit as K
from hq_kit import vadd, vsub, vmul, vnorm, vlen, lerp, TAU
from nightfall_kit import (NP, S_STONE, S_TILE, S_IRON, S_CRIMSON, S_EMBER, S_TIMBER, hex8, beam, post, cyl, obox, tri_prism, frust, box, pyramid, cone, pprism, ring_slab, wslab,
                           bmass, merlons, spikes, slab, ribs, fascia, roof_gable, roof_hip, brazier, chain_swag, banner, iron_bars, seed_of)

PI = math.pi
TREAD = 1.5


# ======================================================================================================================
# walls with openings
# ======================================================================================================================
def wallv(g, a, b, y0, y1, tb, tt, side, end_a=0.0, end_b=0.0):
    """A battered wall whose INNER face is the vertical plane through the line a -> b (x, z each); it is tb thick at y0 and tt at y1, growing toward `side` (+1 = the left of
    a -> b, -1 = the right). end_a / end_b draw the ends in at the top (a mitre against the batter of the wall it meets). Returns the bottom footprint's bounding box."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz * side, ux * side
    a1 = (a[0] + ux * end_a, a[1] + uz * end_a)
    b1 = (b[0] - ux * end_b, b[1] - uz * end_b)
    hex8(g, [(a[0], y0, a[1]), (a[0] + nx * tb, y0, a[1] + nz * tb), (b[0] + nx * tb, y0, b[1] + nz * tb), (b[0], y0, b[1]),
             (a1[0], y1, a1[1]), (a1[0] + nx * tt, y1, a1[1] + nz * tt), (b1[0] + nx * tt, y1, b1[1] + nz * tt), (b1[0], y1, b1[1])])
    xs = [a[0], b[0], a[0] + nx * tb, b[0] + nx * tb]
    zs = [a[1], b[1], a[1] + nz * tb, b[1] + nz * tb]
    return min(xs), max(xs), min(zs), max(zs)


def wall_run(P, a, b, y0, y1, tb, tt, side, openings=(), name="Wall", end_a=0.0, end_b=0.0, suffix=S_STONE, solid=True, floor_y=None):
    """wallv with openings: (s0, s1, h) = a doorway from distance s0 to s1 along the wall, h high; the wall is split into solid spans and a lintel over each opening
    (battered like the wall). Collision boxes for the solid spans and the lintels."""
    g = P.geo(suffix)
    fy = y0 if floor_y is None else floor_y
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L

    def pt(s):
        return (a[0] + ux * s, a[1] + uz * s)

    def t_at(y):
        return tb + (tt - tb) * (y - y0) / (y1 - y0)
    cuts = [(0.0, True)]
    spans = []
    s_prev = 0.0
    first = True
    for (s0, s1, h) in sorted(openings):
        spans.append((s_prev, s0, end_a if first else 0.0, 0.0))
        first = False
        s_prev = s1
    spans.append((s_prev, L, end_a if first else 0.0, end_b))
    for (sa, sb, ea, eb) in spans:
        if sb - sa < 0.05:
            continue
        bb = wallv(g, pt(sa), pt(sb), y0, y1, tb, tt, side, ea, eb)
        if solid:
            P.block(name, bb[0], bb[1], y0 - 1.0, y1, bb[2], bb[3])
    for (s0, s1, h) in openings:
        bb = wallv(g, pt(s0), pt(s1), fy + h, y1, t_at(fy + h), tt, side, 0.0, 0.0)
        if solid:
            P.block(name + "Lintel", bb[0], bb[1], fy + h, y1, bb[2], bb[3])


def shell(P, x0, x1, z0, z1, y0, y1, tb, tt, doors=None, name="Wall", suffix=S_STONE):
    """A hollow battered shell on the rectangle x0..x1, z0..z1 (its outer faces slope in toward y1; the inner faces are vertical): `doors` = {"N": [(s0, s1, h)], ...} with
    N the front (z0) wall, E the right (x1), S the back (z1), W the left (x0); s runs along each wall in +x (N, S) or +z (E, W) from its corner."""
    doors = doors or {}
    d = tb - tt
    xi0, xi1, zi0, zi1 = x0 + tb, x1 - tb, z0 + tb, z1 - tb
    # front and back span the whole width (their ends mitred against the batter of the side walls); the sides run between them
    wall_run(P, (x0, zi0), (x1, zi0), y0, y1, tb, tt, -1, [(o[0], o[1], o[2]) for o in doors.get("N", [])], name, end_a=d, end_b=d, suffix=suffix, floor_y=0.0)
    wall_run(P, (x1, zi1), (x0, zi1), y0, y1, tb, tt, -1, [(o[0], o[1], o[2]) for o in doors.get("S", [])], name, end_a=d, end_b=d, suffix=suffix, floor_y=0.0)
    wall_run(P, (xi1, zi0), (xi1, zi1), y0, y1, tb, tt, -1, [(o[0], o[1], o[2]) for o in doors.get("E", [])], name, suffix=suffix, floor_y=0.0)
    wall_run(P, (xi0, zi1), (xi0, zi0), y0, y1, tb, tt, -1, [(o[0], o[1], o[2]) for o in doors.get("W", [])], name, suffix=suffix, floor_y=0.0)


def slit(P, x, y, z, nrm, w=0.42, h=2.3, suffix=S_IRON, t=0.18):
    """An iron arrow-slit plate on a wall face (nrm = (nx, nz) the face's outward direction): a dark vertical slot with a pointed head."""
    g = P.geo(suffix)
    if abs(nrm[0]) > 0.5:
        box(g, x - t / 2 if nrm[0] < 0 else x - 0.04, x + 0.04 if nrm[0] < 0 else x + t / 2, y, y + h, z - w / 2, z + w / 2)
    else:
        box(g, x - w / 2, x + w / 2, y, y + h, z - t / 2 if nrm[1] < 0 else z - 0.04, z + 0.04 if nrm[1] < 0 else z + t / 2)


# ======================================================================================================================
# stairs: solid stone ramps standing on the ground (their blocks reach down into it)
# ======================================================================================================================
def stair_flight(n=12, width=14.0, depth=1.6, flank=2.0, post_every=3, flank_h=1.5, rail=True):
    """A flight of n one-stud risers along +z from (x 0, z 0) at y 0, tread 1.5 (the lowest tread's top is y 1): every tread a solid stone block from its top down to -depth (the
    ground, or the landing under a high flight), a stepped flank wall each side of it standing flank_h over the treads with an iron spike post every `post_every` steps.
    Collision: a box per tread and per flank block."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    for k in range(n):
        za, zb = k * TREAD, (k + 1) * TREAD
        top = k + 1.0
        box(gs, -width / 2, width / 2, -depth, top, za, zb)
        P.block("Step", -width / 2, width / 2, -depth, top, za, zb)
        for sx in (-1, 1):
            xa, xb = (width / 2, width / 2 + flank) if sx > 0 else (-width / 2 - flank, -width / 2)
            box(gs, xa, xb, -depth, top + flank_h, za, zb)
            P.block("Flank", xa, xb, -depth, top + flank_h, za, zb)
            if rail and k % post_every == 1:
                cone(gi, (xa + xb) / 2, top + flank_h - 0.05, (za + zb) / 2, 0.36, 1.7, seg=4, phase=PI / 4)
    P.floor.append((-width / 2, width / 2, 0.0, n * TREAD, 0.0))
    P.marks["Top"] = (0.0, float(n), n * TREAD)
    return P


def stair_landing(width=14.0, length=6.0, depth=13.6, flank=2.0, flank_h=1.5):
    """A stone landing: width x length, its top at y 0, solid down to -depth, flank walls each side (as the flight's); collision one box."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    box(gs, -width / 2, width / 2, -depth, 0.0, 0.0, length)
    P.block("Landing", -width / 2, width / 2, -depth, 0.0, 0.0, length)
    for sx in (-1, 1):
        xa, xb = (width / 2, width / 2 + flank) if sx > 0 else (-width / 2 - flank, -width / 2)
        box(gs, xa, xb, -depth, flank_h, 0.0, length)
        P.block("Flank", xa, xb, -depth, flank_h, 0.0, length)
        cone(gi, (xa + xb) / 2, flank_h - 0.05, length / 2, 0.4, 2.0, seg=4, phase=PI / 4)
    P.floor.append((-width / 2, width / 2, 0.0, length, 0.0))
    return P


def stair_top(width=14.0, length=4.0, depth=13.6, flank=2.0, flank_h=1.5):
    """The platform between a stair's last tread and the terrace it climbs to: the same as a landing, its far end flush with the terrain."""
    return stair_landing(width, length, depth, flank, flank_h)


def upper_gate():
    """The gate at the head of the Great Stair: two battered pylons with iron spike crowns, an iron lintel between them hung with two crimson banners, on a stone platform 4 deep. Origin: the
    platform's front middle at the stair's top level."""
    P = NP()
    gs, gi, gc = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON)
    w, depth, L = 14.0, 13.6, 4.0
    box(gs, -w / 2 - 2.0, w / 2 + 2.0, -depth, 0.0, 0.0, L)
    P.block("Platform", -w / 2 - 2.0, w / 2 + 2.0, -depth, 0.0, 0.0, L)
    P.floor.append((-w / 2 - 2.0, w / 2 + 2.0, 0.0, L, 0.0))
    for sx in (-1, 1):
        cx = sx * 8.2
        bmass(P, cx - 1.9, cx + 1.9, 0.4, 4.2, -0.5, 14.0, 0.7, bands=(3.0, 7.5, 11.0), seed=40 + sx)
        P.block("Pylon", cx - 1.9, cx + 1.9, 0.0, 14.0, 0.4, 4.2)
        box(gi, cx - 1.1, cx + 1.1, 13.9, 14.6, 1.1, 3.5)
        pyramid(gi, cx, 2.3, 14.5, 1.0, 1.0, 3.8)
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            pyramid(gi, cx + dx * 1.35, 2.3 + dz * 1.35, 14.5, 0.28, 0.28, 1.9)
        box(gc, cx - 1.95, cx + 1.95, 10.4, 11.3, 0.35, 4.25)
    box(gi, -8.2, 8.2, 11.7, 12.9, 1.0, 3.6)
    for xx in (-3.3, 3.3):
        banner(P, xx, 11.7, 0.95, w=2.8, h=6.2, plane="xy")
    for i in range(7):
        x = lerp(-6.0, 6.0, i / 6)
        pyramid(gi, x, 2.3, 12.8, 0.3, 0.3, 1.3)
    P.marks["Front"] = (0.0, 0.0, 0.0)
    P.lights.append((0.0, 9.0, 1.6))
    return P


# ======================================================================================================================
# the walls: curtain modules and the bastion
# ======================================================================================================================
def curtain(L=12.0, h=7.6, tb=3.6, tt=2.7):
    """A curtain wall L long along x (centred), its outer (front) face toward -z: a battered stone wall h high with a string course, a buttress every 6 studs and a crest of merlons."""
    P = NP()
    gs = P.geo(S_STONE)
    d = tb - tt
    # centred on z = 0 with both faces battered
    hex8(gs, [(-L / 2, -1.2, -tb / 2 - 0.15), (L / 2, -1.2, -tb / 2 - 0.15), (L / 2, -1.2, tb / 2 + 0.15), (-L / 2, -1.2, tb / 2 + 0.15),
              (-L / 2, h, -tt / 2), (L / 2, h, -tt / 2), (L / 2, h, tt / 2), (-L / 2, h, tt / 2)])
    f = (h + 1.2)
    for yb in (2.4, 5.0):
        i = (tb - tt) / 2 * (yb + 1.2) / f
        box(gs, -L / 2, L / 2, yb, yb + 0.38, -tb / 2 - 0.15 + i - 0.2, tb / 2 + 0.15 - i + 0.2)
    n_b = max(1, int(round(L / 6.0)))
    for k in range(n_b + 1):
        x = -L / 2 + L * k / n_b
        bmass(P, x - 0.55, x + 0.55, -tb / 2 - 0.5, -tb / 2 + 0.55, -1.2, h - 0.8, 0.25, quoins=False, seed=k)
    tops = merlons(P, (-L / 2 + 0.1, 0.0), (L / 2 - 0.1, 0.0), h - 0.04, h=1.5, w=1.35, gap=1.0, thick=tt - 0.3)
    spikes(P, tops[::2], h=0.8, r=0.2, lift=-0.1)
    P.block("Curtain", -L / 2, L / 2, -1.2, h + 1.5, -tb / 2 - 0.15, tb / 2 + 0.15)
    return P


def bastion():
    """A six-sided drum tower: a battered stone body 13 high with string courses, an overhanging gallery with merlons, an iron crown of spikes and a fire bowl in the middle."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    R0, R1, H = 5.8, 4.8, 10.0                       # vertex radii at y -3 and at the gallery
    pprism(gs, 0.0, 0.0, -3.0, H, R0, seg=6, r_top=R1, caps=True)
    for yb in (1.8, 5.2):
        r = R0 + (R1 - R0) * (yb + 3.0) / (H + 3.0)
        pprism(gs, 0.0, 0.0, yb, yb + 0.42, r + 0.3, seg=6, r_top=r + 0.3, caps=True)
    # the gallery: a ring slab overhanging the wall, six corbels beneath, merlons round it
    RG = R1 + 1.2
    pprism(gs, 0.0, 0.0, H - 0.3, H + 1.3, RG, seg=6, r_top=RG, caps=True)
    for k in range(6):
        a = TAU * k / 6
        pprism(gs, math.cos(a) * (R1 - 0.1), math.sin(a) * (R1 - 0.1), H - 1.9, H - 0.2, 0.7, seg=4, r_top=0.4, caps=True, phase=a + PI / 4)
    pts = [(RG * 0.97 * math.cos(TAU * k / 6), RG * 0.97 * math.sin(TAU * k / 6)) for k in range(6)]
    top_pts = []
    for k in range(6):
        top_pts += merlons(P, pts[k], pts[(k + 1) % 6], H + 1.25, h=1.5, w=1.5, gap=1.1, thick=1.3)
    spikes(P, top_pts[::2], h=0.9, r=0.2)
    brazier(P, 0.0, H + 1.3, 0.0, bowl=1.5, stand=2.0, ember=True, light=False)
    P.block("Bastion", -R0, R0, -3.0, H + 1.3, -R0 * 0.866, R0 * 0.866)
    P.floor.append((-R0, R0, -R0 * 0.866, R0 * 0.866, 0.0))
    return P


# ======================================================================================================================
# props
# ======================================================================================================================
def brazier_tall():
    P = NP()
    gs = P.geo(S_STONE)
    bmass(P, -1.15, 1.15, -1.15, 1.15, -0.8, 0.7, 0.18, quoins=False)
    brazier(P, 0.0, 0.65, 0.0, bowl=1.35, stand=3.0, ember=True, light=True)
    P.block("Brazier", -1.2, 1.2, -0.8, 5.0, -1.2, 1.2)
    return P


def banner_pole(h=12.0, bw=2.6, bh=7.4):
    """A tall iron pole on a battered stone foot, a crossbar with a crimson banner hung from it, a spike on the top."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    bmass(P, -1.2, 1.2, -1.2, 1.2, -0.9, 1.3, 0.3, bands=(0.5,), quoins=False)
    cyl(gi, (0.0, 1.1, 0.0), (0.0, h, 0.0), 0.3, 0.22, seg=6)
    pyramid(gi, 0.0, 0.0, h - 0.1, 0.34, 0.34, 2.6)
    box(gi, -bw / 2 - 0.3, bw / 2 + 0.3, h - 1.2, h - 0.8, -0.14, 0.14)
    pyramid(gi, -bw / 2 - 0.3, 0.0, h - 1.15, 0.16, 0.16, 0.9)
    pyramid(gi, bw / 2 + 0.3, 0.0, h - 1.15, 0.16, 0.16, 0.9)
    banner(P, 0.0, h - 1.2, 0.0, w=bw, h=bh, plane="xy")
    P.block("Pole", -1.2, 1.2, -0.9, 3.0, -1.2, 1.2)
    return P


def parapet(L=12.0):
    """A low battered stone wall (2.2 high) with an iron spike every 2 studs, along x: the rim of the Upper Ward."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    hex8(gs, [(-L / 2, -1.0, -0.9), (L / 2, -1.0, -0.9), (L / 2, -1.0, 0.9), (-L / 2, -1.0, 0.9), (-L / 2, 2.2, -0.65), (L / 2, 2.2, -0.65), (L / 2, 2.2, 0.65), (-L / 2, 2.2, 0.65)])
    box(gs, -L / 2, L / 2, 1.0, 1.35, -1.0, 1.0)
    n = int(L / 2.0)
    for i in range(n + 1):
        x = lerp(-L / 2 + 0.3, L / 2 - 0.3, i / n)
        pyramid(gi, x, 0.0, 2.1, 0.2, 0.2, 1.35)
    P.block("Parapet", -L / 2, L / 2, -1.0, 2.3, -0.95, 0.95)
    return P


def weapon_rack(w=5.0):
    """An iron weapon rack: two uprights and two rails holding six spears and blades (iron), a crimson band on each; stands on the ground, faces -z."""
    P = NP()
    gi, gc = P.geo(S_IRON), P.geo(S_CRIMSON)
    for sx in (-1, 1):
        box(gi, sx * (w / 2) - 0.2, sx * (w / 2) + 0.2, -0.3, 3.6, -0.4, 0.4)
        pyramid(gi, sx * w / 2, 0.0, 3.5, 0.28, 0.28, 0.8)
    for yy in (1.0, 2.4):
        box(gi, -w / 2, w / 2, yy - 0.12, yy + 0.12, -0.3, 0.3)
    n = 6
    for i in range(n):
        x = lerp(-w / 2 + 0.6, w / 2 - 0.6, i / (n - 1))
        if i % 2 == 0:
            cyl(gi, (x, 0.2, 0.0), (x + 0.05, 4.4, 0.0), 0.11, 0.11, seg=4, caps=True)
            pyramid(gi, x + 0.05, 0.0, 4.3, 0.2, 0.12, 1.1)
        else:
            box(gi, x - 0.17, x + 0.17, 0.4, 4.0, -0.07, 0.07)
            pyramid(gi, x, 0.0, 3.95, 0.17, 0.07, 0.6)
        box(gc, x - 0.19, x + 0.19, 1.7, 2.0, -0.1, 0.1)
    P.block("Rack", -w / 2 - 0.2, w / 2 + 0.2, -0.3, 3.6, -0.5, 0.5)
    return P


def stake_row(n=4, gap=2.6):
    """A row of training stakes along x: each a stout iron-shod post 3.6 high with a crimson band and an iron cap spike."""
    P = NP()
    gs, gi, gc = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON)
    L = (n - 1) * gap
    for i in range(n):
        x = -L / 2 + i * gap
        bmass(P, x - 0.7, x + 0.7, -0.7, 0.7, -0.7, 0.5, 0.15, quoins=False)
        box(gs, x - 0.34, x + 0.34, 0.4, 3.4, -0.34, 0.34)
        box(gc, x - 0.38, x + 0.38, 1.9, 2.5, -0.38, 0.38)
        box(gi, x - 0.4, x + 0.4, 3.3, 3.7, -0.4, 0.4)
        pyramid(gi, x, 0.0, 3.65, 0.3, 0.3, 1.0)
    P.block("Stakes", -L / 2 - 0.8, L / 2 + 0.8, -0.7, 3.7, -0.8, 0.8)
    return P


def rack_shed():
    """An open lean-to for the training weapons: four iron-shod uprights, a near-black shed roof sloping back with a crimson fascia, two weapon racks under it. 12 wide, 4.4 deep, faces -z."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    W, D = 12.0, 4.4
    for x in (-W / 2 + 0.5, -W / 6, W / 6, W / 2 - 0.5):
        bmass(P, x - 0.45, x + 0.45, -D / 2 - 0.45, -D / 2 + 0.45, -0.7, 5.6, 0.1, quoins=False)
        P.block("Post", x - 0.45, x + 0.45, -0.7, 5.6, -D / 2 - 0.45, -D / 2 + 0.45)
    bmass(P, -W / 2, W / 2, D / 2 - 0.6, D / 2 + 0.4, -0.7, 5.4, 0.12, bands=(2.0,), quoins=False)
    P.block("BackWall", -W / 2, W / 2, -0.7, 5.4, D / 2 - 0.6, D / 2 + 0.4)
    # the shed roof: one slope from the front eave (z -D/2 - 1.2, y 5.2) up to the back (y 6.4)
    E = [(-W / 2 - 0.8, 5.0, -D / 2 - 1.3), (W / 2 + 0.8, 5.0, -D / 2 - 1.3)]
    Rr = [(-W / 2 - 0.8, 6.8, D / 2 + 0.6), (W / 2 + 0.8, 6.8, D / 2 + 0.6)]
    n = slab(P.geo(S_TILE), E[0], E[1], Rr[1], Rr[0], 0.5)
    ribs(P, E[0], E[1], Rr[1], Rr[0], n, gap=2.4)
    fascia(P, (E[0][0], E[0][1] - 0.05, E[0][2]), (E[1][0], E[1][1] - 0.05, E[1][2]), 0.5, 0.9)
    for (a, b) in ((E[0], Rr[0]), (E[1], Rr[1])):
        fascia(P, (a[0], a[1] - 0.05, a[2]), (b[0], b[1], b[2]), 0.45, 0.8, up=(1.0, 0.0, 0.0))
    spikes(P, [(x, 6.75, D / 2 + 0.6) for x in (-W / 2 + 0.5, 0.0, W / 2 - 0.5)], h=1.4, r=0.3)
    for x in (-W / 4, W / 4):
        rk = weapon_rack(4.6)
        P.absorb(rk, t=(x, 0.0, D / 2 - 1.2))
    P.floor.append((-W / 2, W / 2, -D / 2, D / 2, 0.0))
    return P


# ======================================================================================================================
# the buildings
# ======================================================================================================================
def tower_mass(P, x0, x1, z0, z1, y0, y1, b0, b1, bz0, bz1, bands=(), band_out=0.2, crimson_band=None, suffix=S_STONE):
    """A battered block with its own batter on each side (left, right, front, back) and string courses (stone) and optionally a crimson band at height `crimson_band`."""
    g = P.geo(suffix)
    h = y1 - y0
    frust(g, x0, x1, z0, z1, y0, y1, b0, b1, bz0, bz1)

    def ins(y, b):
        return b * (y - y0) / h
    for yb in bands:
        yy = y0 + yb
        frust(g, x0 + ins(yy, b0) - band_out, x1 - ins(yy, b1) + band_out, z0 + ins(yy, bz0) - band_out, z1 - ins(yy, bz1) + band_out, yy, yy + 0.42, band_out * 0.7)
    if crimson_band is not None:
        yy = y0 + crimson_band
        frust(P.geo(S_CRIMSON), x0 + ins(yy, b0) - band_out, x1 - ins(yy, b1) + band_out, z0 + ins(yy, bz0) - band_out, z1 - ins(yy, bz1) + band_out, yy, yy + 0.7, band_out * 0.7)


def gatehouse():
    """The gatehouse: two battered gate towers (8 x 12) either side of an 8-wide passage, a stone lintel over it hung with iron spikes, a gate loft (21 x 9.2) over the whole width under
    a hard gable roof, two spiked corner turrets, crimson bands and banners. Faces -z; origin on the ground in the passage's middle."""
    P = NP()
    gs, gt, gi, gc = P.geo(S_STONE), P.geo(S_TILE), P.geo(S_IRON), P.geo(S_CRIMSON)
    H = 12.5
    for sx in (-1, 1):
        x0, x1 = (4.0, 12.0) if sx > 0 else (-12.0, -4.0)
        if sx > 0:
            tower_mass(P, x0, x1, -6.0, 6.0, -1.5, H, 0.0, 1.1, 1.1, 1.1, bands=(3.0, 6.6, 10.0))
        else:
            tower_mass(P, x0, x1, -6.0, 6.0, -1.5, H, 1.1, 0.0, 1.1, 1.1, bands=(3.0, 6.6, 10.0))
        P.block("Tower", x0, x1, -1.5, H, -6.0, 6.0)
        # a stone pier along the passage's inner face at the front, quoin blocks up the outer corners
        for k, yq in enumerate((0.4, 2.6, 4.8, 7.0, 9.2, 11.0)):
            xa = (x1 - 1.9) if sx > 0 else x0
            xb = x1 if sx > 0 else (x0 + 1.9)
            xo0, xo1 = (x1 - 0.1 * (yq + 1.5) / 14 * 0, x1) if False else (0, 0)
        # slits on the outer face
    # the lintel: stone over the passage, spikes hung under it
    frust(gs, -4.6, 4.6, -5.3, 5.3, 7.7, 12.6, 0.0, 0.0, 0.4, 0.4)
    P.block("Lintel", -4.0, 4.0, 7.7, 12.6, -5.3, 5.3)
    for i in range(9):
        x = lerp(-3.4, 3.4, i / 8)
        pyramid(gi, x, -4.2, 7.9, 0.2, 0.2, -1.45)
        pyramid(gi, x, 4.2, 7.9, 0.2, 0.2, -1.45)
    box(gi, -3.9, 3.9, 7.5, 7.95, -4.4, -3.9)
    # the gate loft
    tower_mass(P, -10.5, 10.5, -4.7, 4.7, H - 0.2, 19.0, 0.7, 0.7, 0.7, 0.7, bands=(), crimson_band=0.3, band_out=0.25)
    P.block("Loft", -10.5, 10.5, H, 19.0, -4.7, 4.7)
    for x in (-7.0, -3.0, 3.0, 7.0):
        slit(P, x, 14.0, -4.7 + 0.45, (0.0, -1.0), w=0.5, h=2.8)
        slit(P, x, 14.0, 4.7 - 0.45, (0.0, 1.0), w=0.5, h=2.8)
    # the roof
    roof_gable(P, -10.5, 10.5, -4.7, 4.7, 19.0, 25.5, over=1.9, rake=1.7, th=0.6, rib_gap=2.4, wall_y=19.0, z_r=0.0)
    # the two corner turrets on the tower tops (spike crowns)
    for sx in (-1, 1):
        cx = sx * 11.1
        bmass(P, cx - 1.1, cx + 1.1, -5.0, -2.8, H - 0.3, 20.0, 0.35, bands=(3.0,), quoins=False)
        pyramid(gi, cx, -3.9, 19.9, 1.0, 1.0, 4.2)
        bmass(P, cx - 1.1, cx + 1.1, 2.8, 5.0, H - 0.3, 20.0, 0.35, bands=(3.0,), quoins=False)
        pyramid(gi, cx, 3.9, 19.9, 1.0, 1.0, 4.2)
        # merlons along the tower tops' outer edge
    for sx in (-1, 1):
        merlons(P, (sx * 10.9, -5.2), (sx * 10.9, 5.2), H - 0.04, h=1.4, w=1.3, gap=0.9, thick=1.2, skip=(0, 3, 4, 7) if False else ())
    # banners on the tower fronts
    for x in (-8.0, 8.0):
        banner(P, x, 12.0, -5.0, w=2.6, h=7.8, plane="xy", tilt=0.0786)
    P.lights.append((0.0, 6.0, -3.0))
    P.marks["Passage"] = (0.0, 0.0, 0.0)
    P.floor.append((-12.0, 12.0, -6.0, 6.0, 0.0))
    return P


def keep():
    """The Black Keep: a battered stone hall 34 x 28 (inside 24 x 18, 9.5 high, a door 6 wide in the front), a crenellated cornice, four spiked corner turrets and, rising from the middle
    and the back, a battered donjon with a crimson band, arrow slits, an overhanging gallery, a hip roof and an iron spire. The tallest thing on the mountain. Faces -z."""
    P = NP()
    gs, gt, gi, gc = P.geo(S_STONE), P.geo(S_TILE), P.geo(S_IRON), P.geo(S_CRIMSON)
    X, Z, H1, tb, tt = 17.0, 14.0, 9.5, 5.0, 4.05
    box(gs, -12.0, 12.0, -0.9, 0.0, -9.0, 9.0)
    P.block("Floor", -12.0, 12.0, -1.5, 0.0, -9.0, 9.0)
    P.floor.append((-X, X, -Z, Z, 0.0))
    shell(P, -X, X, -Z, Z, -1.0, H1, tb, tt, doors={"N": [(X - 3.0, X + 3.0, 7.6)]}, name="Wall")
    # the upper mass: the ceiling and a solid block up to the cornice
    xo, zo = X - (tb - tt) - 0.0, Z - (tb - tt)
    xo, zo = 12.0 + tt, 9.0 + tt
    frust(gs, -xo, xo, -zo, zo, H1, 14.2, 0.4)
    P.block("Upper", -xo, xo, H1, 14.2, -zo, zo)
    # string courses and a crimson band up the hall's walls
    for yb, suf in ((3.2, S_STONE), (6.6, S_STONE)):
        i = (tb - tt) * (yb + 1.0) / (H1 + 1.0)
        frust(P.geo(suf), -X + i - 0.22, X - i + 0.22, -Z + i - 0.22, Z - i + 0.22, yb, yb + 0.45, 0.18)
    # the cornice and the crenellated parapet
    frust(gs, -xo - 0.7, xo + 0.7, -zo - 0.7, zo + 0.7, 13.6, 14.7, 0.1, 0.1, 0.1, 0.1)
    xp, zp = xo - 0.25, zo - 0.25
    pts = []
    for a, b in (((-xp, -zp), (xp, -zp)), ((xp, -zp), (xp, zp)), ((xp, zp), (-xp, zp)), ((-xp, zp), (-xp, -zp))):
        pts += merlons(P, a, b, 14.65, h=1.6, w=1.45, gap=1.05, thick=1.5)
    spikes(P, pts[::3], h=0.9, r=0.2)
    # the four corner turrets: battered, banded, each under a spiked hip roof
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (xo - 2.3), sz * (zo - 2.3)
            bmass(P, cx - 2.7, cx + 2.7, cz - 2.7, cz + 2.7, H1 - 0.2, 21.5, 0.55, bands=(5.0, 9.0), seed=sx * 3 + sz)
            frust(gc, cx - 2.7 + 0.45, cx + 2.7 - 0.45, cz - 2.7 + 0.45, cz + 2.7 - 0.45, 18.6, 19.2, 0.1)
            roof_hip(P, cx, cz, 2.2, 2.2, 21.4, 26.0, over=1.1, rib_gap=0, spike=3.0)
    # the donjon: a tall battered block from the cornice up, back-weighted
    dz0, dz1 = -4.2, 8.6
    tower_mass(P, -7.4, 7.4, dz0, dz1, 14.0, 34.0, 1.9, 1.9, 1.9, 1.9, bands=(5.5, 12.0), crimson_band=0.0, band_out=0.28)
    P.block("Donjon", -7.4, 7.4, 14.0, 34.0, dz0, dz1)
    for x in (-3.6, 0.0, 3.6):
        slit(P, x, 20.0, dz0 + 1.9 * (21.5 - 14.0) / 20.0, (0.0, -1.0), w=0.5, h=3.0)
        slit(P, x, 27.0, dz0 + 1.9 * (28.5 - 14.0) / 20.0, (0.0, -1.0), w=0.5, h=3.0)
    for z in (0.0, 4.2):
        slit(P, -7.4 + 1.9 * (23.5 - 14.0) / 20.0, 22.0, z, (-1.0, 0.0), w=0.5, h=3.0)
        slit(P, 7.4 - 1.9 * (23.5 - 14.0) / 20.0, 22.0, z, (1.0, 0.0), w=0.5, h=3.0)
    # the gallery overhanging the donjon's top, crenellated, and the cap storey with its hip roof and the spire
    xg0, xg1, zg0, zg1 = -7.4 + 1.9 - 1.4, 7.4 - 1.9 + 1.4, dz0 + 1.9 - 1.4, dz1 - 1.9 + 1.4
    frust(gs, xg0, xg1, zg0, zg1, 33.8, 35.2, 0.0, 0.0, 0.0, 0.0)
    for k, (cxx, czz) in enumerate(((xg0, zg0), (xg1, zg0), (xg1, zg1), (xg0, zg1))):
        pass
    pts = []
    for a, b in (((xg0 + 0.6, zg0 + 0.6), (xg1 - 0.6, zg0 + 0.6)), ((xg1 - 0.6, zg0 + 0.6), (xg1 - 0.6, zg1 - 0.6)), ((xg1 - 0.6, zg1 - 0.6), (xg0 + 0.6, zg1 - 0.6)), ((xg0 + 0.6, zg1 - 0.6), (xg0 + 0.6, zg0 + 0.6))):
        pts += merlons(P, a, b, 35.15, h=1.4, w=1.4, gap=1.0, thick=1.2)
    spikes(P, pts[::2], h=0.9, r=0.2)
    xc0, xc1, zc0, zc1 = -5.0, 5.0, dz0 + 3.6, dz1 - 3.6
    bmass(P, xc0, xc1, zc0, zc1, 35.0, 40.4, 0.7, quoins=False)
    frust(gc, xc0 + 0.1, xc1 - 0.1, zc0 + 0.1, zc1 - 0.1, 35.4, 36.1, 0.0)
    roof_hip(P, 0.0, (zc0 + zc1) / 2, 5.0, (zc1 - zc0) / 2, 40.2, 47.8, over=1.9, rib_gap=2.2, ridge=0.0, spike=0.0)
    ym = 47.6
    zm = (zc0 + zc1) / 2
    cyl(gi, (0.0, ym, zm), (0.0, ym + 11.0, zm), 0.55, 0.16, seg=6)
    for yy, rr in ((ym + 1.5, 0.95), (ym + 4.5, 0.8), (ym + 7.5, 0.7)):
        pprism(gi, 0.0, zm, yy, yy + 0.35, rr, seg=6, r_top=rr, caps=True)
        for k in range(4):
            a = TAU * k / 4 + PI / 4
            cone(gi, math.cos(a) * rr * 0.9, yy + 0.3, zm + math.sin(a) * rr * 0.9, 0.16, 1.0, seg=4)
    pyramid(gi, 0.0, zm, ym + 10.9, 0.18, 0.18, 2.2)
    P.emit.append(("Embers", (0.0, ym + 5.0, zm)))
    # the door: a heavy iron-bound frame (iron jamb strips, spikes under the lintel) and two banners on the front wall
    for sx in (-1, 1):
        box(gi, sx * 3.0 - (0.45 if sx > 0 else -0.0) - (0.0 if sx > 0 else 0.45), sx * 3.0 + (0.0 if sx > 0 else 0.0) + (0.45 if sx > 0 else 0.0) * 0 + (0.0), 0.0, 7.0, -Z - 0.35 + 0.1 * 1.0, -Z + 0.5) if False else None
    iron_bars(P, -3.0, 3.0, 6.5, 7.55, -Z + 1.2, n=9, w=0.22, spike=-0.0 + 0.0001) if False else None
    for i in range(9):
        x = lerp(-2.7, 2.7, i / 8)
        pyramid(gi, x, -Z + 1.6, 7.7, 0.2, 0.2, -1.2)
    for x in (-9.0, 9.0):
        banner(P, x, 13.0, -13.1, w=3.0, h=8.6, plane="xy", tilt=0.1 * 1.0)
    # buttresses along the long sides
    for z in (-8.0, 0.0, 8.0):
        for sx in (-1, 1):
            xb = sx * (X - 0.1)
            frust(gs, min(xb, xb + sx * 1.5), max(xb, xb + sx * 1.5), z - 1.0, z + 1.0, -1.0, 12.5, 0.0, 0.0, 0.0, 0.0) if False else None
    P.lights.append((0.0, 6.5, -3.0))
    P.marks["Door"] = (0.0, 0.0, -Z)
    P.marks["Inside"] = (0.0, 0.0, -1.5)
    P.marks["Top"] = (0.0, ym + 13.0, zm)
    return P


def porch(P, x0, x1, y_e, y_r, z_from, z_to, over=1.5, rake=0.9):
    """A gabled porch hood whose ridge runs along z (the main roof's ridge runs along x): a sub-roof built with its ridge along x and turned a quarter. x0..x1 = its width, z_from (the
    front, smaller z) to z_to (where it runs into the main roof)."""
    sub = NP()
    roof_gable(sub, -(z_to), -(z_from), x0, x1, y_e, y_r, over=over, rake=rake, th=0.55, rib_gap=2.2, wall_y=y_e, z_r=(x0 + x1) / 2, fill_t=0.6)
    P.absorb(sub, yaw=PI / 2)


def armory():
    """The Armory (the weapon exhibition hall): a long battered stone hall 32 x 16 (inside 26 x 10, 8.5 high, a door 9 wide), a great gable roof 17 high with a crest of spikes and horns, an
    entrance porch under its own gable between two spiked piers, the Talon's plinth at the right end of the hall, a vault door in the back wall, weapon panels. Faces -z."""
    P = NP()
    gs, gt, gi, gc = P.geo(S_STONE), P.geo(S_TILE), P.geo(S_IRON), P.geo(S_CRIMSON)
    X, Z, H, tb, tt = 16.0, 8.0, 8.5, 3.0, 2.35
    box(gs, -13.0, 13.0, -0.9, 0.0, -5.0, 5.0)
    P.block("Floor", -13.0, 13.0, -1.5, 0.0, -5.0, 5.0)
    P.floor.append((-X, X, -Z, Z, 0.0))
    shell(P, -X, X, -Z, Z, -1.0, H, tb, tt, doors={"N": [(X - 4.5, X + 4.5, 6.8)]}, name="Wall")
    box(gs, -13.3, 13.3, 7.9, 8.5, -5.3, 5.3)
    P.block("Ceiling", -13.3, 13.3, 7.9, 8.5, -5.3, 5.3)
    xo, zo = 13.0 + tt, 5.0 + tt
    for yb in (2.8,):
        t = tb + (tt - tb) * (yb + 1.0) / (H + 1.0)
        frust(gs, -(13.0 + t) - 0.2, (13.0 + t) + 0.2, -(5.0 + t) - 0.2, (5.0 + t) + 0.2, yb, yb + 0.42, 0.14)
    t = tb + (tt - tb) * (7.0 + 1.0) / (H + 1.0)
    frust(gc, -(13.0 + t) - 0.22, (13.0 + t) + 0.22, -(5.0 + t) - 0.22, (5.0 + t) + 0.22, 7.0, 7.7, 0.12)
    roof_gable(P, -xo, xo, -zo, zo, H + 0.1, 16.8, over=2.0, rake=1.3, th=0.6, rib_gap=2.4, wall_y=H, z_r=0.0)
    # the porch between two piers
    for sx in (-1, 1):
        cx = sx * 6.2
        bmass(P, cx - 1.5, cx + 1.5, -10.0, -7.0, -1.0, 11.0, 0.4, bands=(3.0, 6.6), seed=70 + sx)
        P.block("Pier", cx - 1.5, cx + 1.5, 0.0, 11.0, -10.0, -7.0)
        pyramid(gi, cx, -8.5, 10.9, 1.0, 1.0, 2.6)
        frust(gc, cx - 1.45, cx + 1.45, -9.95, -7.05, 9.0, 9.6, 0.05)
    porch(P, -8.2, 8.2, 11.2, 15.6, -10.8, -1.0, over=1.4, rake=1.0)
    # the entrance: iron spikes under the lintel; two banners on the front wall either side of the porch
    for i in range(9):
        x = lerp(-4.1, 4.1, i / 8)
        pyramid(gi, x, -X * 0 - Z + 1.6, 7.9, 0.19, 0.19, -1.2)
    for x in (-12.0, 12.0):
        banner(P, x, 8.0, -Z - 0.0 + 0.55 - 0.1 * 0 - 0.0, w=2.6, h=6.6, plane="xy", tilt=0.06)
    # inside: the vault door in the back wall (left), two weapon panels, light
    box(gs, -10.8, -5.2, 0.0, 5.6, 4.5, 5.2)
    box(gi, -10.0, -6.0, 0.0, 4.7, 4.2, 4.6)
    box(gi, -10.3, -5.7, 2.1, 2.55, 4.1, 4.3)
    for xx in (-9.2, -6.8):
        for yy in (1.0, 3.5):
            pyramid(gi, xx, 4.2, yy, 0.16, 0.16, -0.18)
    P.block("VaultFrame", -10.8, -5.2, 0.0, 5.6, 4.5, 5.2)
    for xb in (-1.2, 3.6):
        box(gi, xb - 1.6, xb + 1.6, 1.3, 4.6, 4.6, 4.85)
        beam(gi, (xb - 1.3, 1.6, 4.5), (xb + 1.3, 4.3, 4.5), 0.1, 0.5)
        beam(gi, (xb - 1.3, 4.3, 4.5), (xb + 1.3, 1.6, 4.5), 0.1, 0.5)
        box(gc, xb - 0.3, xb + 0.3, 2.75, 3.15, 4.35, 4.65)
    P.lights.append((0.0, 6.0, -0.5))
    P.marks["Door"] = (0.0, 0.0, -Z)
    P.marks["Inside"] = (0.0, 0.0, 0.0)
    P.marks["Vault"] = (-8.0, 0.0, 2.8)
    P.marks["Display"] = (8.4, 1.75, 0.4)
    return P


def armory_marks():
    """The armory's marks in its own frame (built once; the plan reads the vault and the inside)."""
    global _ARM_MARKS
    if _ARM_MARKS is None:
        _ARM_MARKS = armory().marks
    return _ARM_MARKS


_ARM_MARKS = None


def talon_plinth():
    """The plinth that holds the Nightfall Talon: a battered stone block 7.6 x 2.8, 1.2 high, a crimson cloth under the blade, two iron cradles with spiked prongs, four spikes at the corners.
    The weapon lies along x at the mark `Display`."""
    P = NP()
    gs, gi, gc = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON)
    bmass(P, -3.8, 3.8, -1.4, 1.4, -0.4, 1.2, 0.25, bands=(0.5,), quoins=False)
    P.block("Plinth", -3.8, 3.8, -0.4, 1.2, -1.4, 1.4)
    box(gc, -3.2, 3.2, 1.15, 1.3, -0.62, 0.62)
    for x in (-1.9, 1.9):
        box(gi, x - 0.28, x + 0.28, 1.2, 2.0, -0.5, 0.5)
        beam(gi, (x, 1.9, -0.55), (x, 2.55, -0.1), 0.2, 0.2)
        beam(gi, (x, 1.9, 0.55), (x, 2.55, 0.1), 0.2, 0.2)
        pyramid(gi, x, -0.1, 2.5, 0.12, 0.12, 0.5)
        pyramid(gi, x, 0.1, 2.5, 0.12, 0.12, 0.5)
    for sx in (-1, 1):
        for sz in (-1, 1):
            pyramid(gi, sx * 3.5, sz * 1.15, 1.15, 0.2, 0.2, 1.5)
    P.marks["Display"] = (0.0, 1.75, 0.0)
    return P


def residence():
    """The Lord's tower: a battered stone tower 11 x 11 (a room 7 x 7 inside, a door 4.2 wide), a stone mass above it with a crimson band, an overhanging balcony ringed with iron spikes, an
    upper storey with arrow slits under a hard gable roof with horns and a crest, a small gabled porch over the door and an iron spire. Faces -z."""
    P = NP()
    gs, gt, gi, gc = P.geo(S_STONE), P.geo(S_TILE), P.geo(S_IRON), P.geo(S_CRIMSON)
    X, Hg, tb, tt = 5.5, 7.0, 2.0, 1.6
    box(gs, -3.5, 3.5, -0.9, 0.0, -3.5, 3.5)
    P.block("Floor", -3.5, 3.5, -1.5, 0.0, -3.5, 3.5)
    P.floor.append((-X, X, -X, X, 0.0))
    shell(P, -X, X, -X, X, -1.0, Hg, tb, tt, doors={"N": [(X - 2.1, X + 2.1, 5.6)]}, name="Wall")
    box(gs, -3.6, 3.6, Hg - 0.6, Hg, -3.6, 3.6)
    P.block("Ceiling", -3.6, 3.6, Hg - 0.6, Hg, -3.6, 3.6)
    xo = 3.5 + tt
    frust(gs, -xo, xo, -xo, xo, Hg, 14.0, 0.7)
    P.block("Upper", -xo, xo, Hg, 14.0, -xo, xo)
    for yb in (3.0,):
        t = tb + (tt - tb) * (yb + 1.0) / (Hg + 1.0)
        frust(gs, -(3.5 + t) - 0.2, 3.5 + t + 0.2, -(3.5 + t) - 0.2, 3.5 + t + 0.2, yb, yb + 0.4, 0.12)
    frust(gc, -4.75, 4.75, -4.75, 4.75, 12.9, 13.6, 0.08)
    # the balcony: a slab on corbels with an iron spike rail
    frust(gs, -6.4, 6.4, -6.4, 6.4, 13.9, 14.9, 0.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            pprism(gs, sx * 4.3, sz * 4.3, 12.2, 14.0, 1.0, seg=4, r_top=0.5, caps=True, phase=PI / 4)
    for a, b in (((-6.1, -6.1), (6.1, -6.1)), ((6.1, -6.1), (6.1, 6.1)), ((6.1, 6.1), (-6.1, 6.1)), ((-6.1, 6.1), (-6.1, -6.1))):
        beam(gi, (a[0], 15.9, a[1]), (b[0], 15.9, b[1]), 0.2, 0.2)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 1.8)
        for i in range(n + 1):
            x = lerp(a[0], b[0], i / n)
            z = lerp(a[1], b[1], i / n)
            box(gi, x - 0.1, x + 0.1, 14.8, 15.9, z - 0.1, z + 0.1)
            pyramid(gi, x, z, 15.8, 0.16, 0.16, 0.7)
    bmass(P, -4.2, 4.2, -4.2, 4.2, 14.8, 20.8, 0.6, bands=(2.4,), quoins=False)
    for x in (-2.0, 2.0):
        slit(P, x, 16.3, -4.2 + 0.1, (0.0, -1.0), w=0.45, h=2.6)
        slit(P, x, 16.3, 4.2 - 0.1, (0.0, 1.0), w=0.45, h=2.6)
        slit(P, -4.2 + 0.1, 16.3, x, (-1.0, 0.0), w=0.45, h=2.6)
        slit(P, 4.2 - 0.1, 16.3, x, (1.0, 0.0), w=0.45, h=2.6)
    roof_gable(P, -3.6, 3.6, -3.6, 3.6, 20.9, 27.6, over=2.3, rake=1.9, th=0.6, rib_gap=2.2, wall_y=20.8, z_r=0.0)
    cyl(gi, (0.0, 27.5, 0.0), (0.0, 33.0, 0.0), 0.34, 0.14, seg=6)
    pyramid(gi, 0.0, 0.0, 32.9, 0.14, 0.14, 1.8)
    for yy in (29.0, 31.0):
        pprism(gi, 0.0, 0.0, yy, yy + 0.28, 0.55, seg=6, r_top=0.55, caps=True)
    # the door's porch: a small gable on two stone posts
    for sx in (-1, 1):
        bmass(P, sx * 3.1 - 0.4, sx * 3.1 + 0.4, -X - 2.3, -X - 1.5, -1.0, 6.4, 0.08, quoins=False)
        P.block("PorchPost", sx * 3.1 - 0.4, sx * 3.1 + 0.4, 0.0, 6.4, -X - 2.3, -X - 1.5)
    porch(P, -3.8, 3.8, 6.4, 8.9, -X - 3.0, -X + 1.0, over=1.0, rake=0.6)
    P.lights.append((0.0, 5.0, 0.0))
    P.marks["Door"] = (0.0, 0.0, -X)
    P.marks["Inside"] = (0.0, 0.0, 0.0)
    return P


def arena():
    """The arena of the Trial of Strength: a round pit 24 across inside a battered stone ring wall 5.2 high with a crest of merlons and spikes, three gates (front, left, right) each between
    two spiked pylons under an iron lintel; the floor a black disc with a crimson ring and eight low stone plinths where the dummies stand, an iron plate in the middle. Origin: the pit's middle."""
    P = NP()
    gs, gi, gc = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON)
    Rin, Rout0, Rout1, H = ARENA_RIN, 14.6, 13.7, 5.2
    n = 24
    gates = (-PI / 2, 0.0, PI)                    # the angles (from +x toward +z) of the gates: toward -z (the gatehouse), +x, -x
    d = TAU / n

    def is_gate(a_mid):
        return any(abs(((a_mid - g_ + PI) % TAU) - PI) < math.radians(16.0) for g_ in gates)
    for k in range(n):
        a0, a1 = k * d, (k + 1) * d
        am = (a0 + a1) / 2
        if is_gate(am):
            continue
        ring_slab(gs, 0.0, 0.0, Rin, Rout0 + 0.2, -1.2, H, a0, a1, r_in_top=Rin, r_out_top=Rout1)
        rr = (Rin + Rout0) / 2
        P.rblock("Wall", rr * math.cos(am), rr * math.sin(am), Rout0 - Rin + 0.4, 2 * rr * math.tan(d / 2) + 0.3, -1.2, H, -am)
        if k % 2 == 0:
            ring_slab(gs, 0.0, 0.0, Rin + 0.35, Rout1 - 0.35, H - 0.05, H + 1.45, a0 + 0.05, a1 - 0.05, r_in_top=Rin + 0.5, r_out_top=Rout1 - 0.5)
        if k % 3 == 1:
            for fr in (0.5,):
                a = a0 + d * fr
                r = (Rin + Rout1) / 2
                pyramid(gi, r * math.cos(a), r * math.sin(a), H - 0.05, 0.22, 0.22, 1.6)
    # the string course round the outside
    for k in range(n):
        a0, a1 = k * d, (k + 1) * d
        if is_gate((a0 + a1) / 2):
            continue
        ring_slab(gs, 0.0, 0.0, Rin + 0.5, Rout0 + 0.55, 2.2, 2.62, a0, a1, r_out_top=Rout0 + 0.45 - 0.0)
    # the three gates: two pylons and an iron lintel, spiked, a crimson band on each pylon
    gr = (Rin + Rout0) / 2 + 0.2
    half = math.radians(17.0)
    for g_ in gates:
        pts = []
        for sg in (-1, 1):
            a = g_ + sg * half
            cx, cz = gr * math.cos(a), gr * math.sin(a)
            sub = NP()
            bmass(sub, -1.4, 1.4, -1.4, 1.4, -1.0, 8.0, 0.35, bands=(2.6, 5.4), quoins=False)
            cone(sub.geo(S_IRON), 0.0, 7.95, 0.0, 1.0, 3.0, seg=4, phase=PI / 4)
            frust(sub.geo(S_CRIMSON), -1.35, 1.35, -1.35, 1.35, 6.4, 7.0, 0.05)
            sub.block("Pylon", -1.4, 1.4, -1.0, 8.0, -1.4, 1.4)
            P.absorb(sub, t=(cx, 0.0, cz), yaw=0.0)
            pts.append((cx, cz))
        beam(gi, (pts[0][0], 6.7, pts[0][1]), (pts[1][0], 6.7, pts[1][1]), 0.8, 0.7)
        for i in range(5):
            t = (i + 0.5) / 5
            x, z = lerp(pts[0][0], pts[1][0], t), lerp(pts[0][1], pts[1][1], t)
            pyramid(gi, x, z, 7.0, 0.2, 0.2, 1.3)
    # the floor: a black disc, a crimson ring, eight plinths and a plate
    pprism(gs, 0.0, 0.0, -0.7, 0.04, Rin - 0.05, seg=24, r_top=Rin - 0.05, caps=True)
    m = 16
    for k in range(m):
        ring_slab(gc, 0.0, 0.0, 8.7, 9.4, 0.03, 0.1, k * TAU / m, (k + 1) * TAU / m)
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        pprism(gs, 8.0 * math.cos(a), 8.0 * math.sin(a), -0.2, 0.22, 1.0, seg=8, r_top=0.85, caps=True, phase=a)
        pprism(gc, 8.0 * math.cos(a), 8.0 * math.sin(a), 0.2, 0.27, 0.5, seg=8, r_top=0.5, caps=True, phase=a)
    pprism(gi, 0.0, 0.0, 0.02, 0.16, 1.5, seg=8, r_top=1.4, caps=True)
    P.floor.append((-Rout0, Rout0, -Rout0, Rout0, 0.0))
    P.marks["Centre"] = (0.0, 0.0, 0.0)
    return P


ARENA_RIN = 12.0


def ember_court():
    """The Ember Court, the gathering place: a stepped dais with a great iron fire bowl on a spiked tripod (a flame and a light), four stone benches on the diagonals, four spiked posts and three
    jagged standing stones behind the fire. The ten NPC places stand on a ring 6.2 round the fire. Origin: the fire's foot, on the ground."""
    P = NP()
    gs, gi = P.geo(S_STONE), P.geo(S_IRON)
    pprism(gs, 0.0, 0.0, -0.7, 0.04, 14.0, seg=24, r_top=14.0, caps=True)
    pprism(gs, 0.0, 0.0, -0.6, 0.42, 4.5, seg=8, r_top=4.2, caps=True, phase=TAU / 16)
    pprism(gs, 0.0, 0.0, 0.4, 0.9, 3.4, seg=8, r_top=3.2, caps=True, phase=TAU / 16)
    P.rblock("Dais", 0.0, 0.0, 8.4, 8.4, -0.6, 0.9, PI / 8)
    brazier(P, 0.0, 0.88, 0.0, bowl=2.0, stand=2.3, ember=True, light=True)
    for k in range(4):
        am = TAU * k / 4 + PI / 4
        ring_slab(gs, 0.0, 0.0, 8.0, 9.5, -0.5, 0.95, am - math.radians(17.0), am + math.radians(17.0), r_out_top=9.1)
        rr = 8.75
        P.rblock("Bench", rr * math.cos(am), rr * math.sin(am), 1.7, 5.2, -0.5, 0.95, -(am + PI / 2))
        for sg in (-1, 1):
            a = am + sg * math.radians(14.0)
            cone(gi, 8.75 * math.cos(a), 0.85, 8.75 * math.sin(a), 0.38, 2.4, seg=4, phase=a)
    for k, (a, h, lean) in enumerate(((math.radians(70.0), 9.0, 0.10), (math.radians(90.0), 11.5, -0.08), (math.radians(110.0), 8.0, 0.06))):
        r = 12.2
        cx, cz = r * math.cos(a), r * math.sin(a)
        sub = NP()
        frust(sub.geo(S_STONE), -1.2, 1.2, -1.0, 1.0, -0.9, h, 0.9, 0.9, 0.7, 0.7)
        pyramid(sub.geo(S_STONE), 0.0, 0.0, h - 0.05, 0.4, 0.3, 3.2, lean=(lean * 4.0, 0.0))
        sub.block("Stone", -1.2, 1.2, -0.9, h, -1.0, 1.0)
        P.absorb(sub, t=(cx, 0.0, cz), yaw=-a + PI / 2)
    P.floor.append((-9.5, 9.5, -9.5, 9.5, 0.0))
    return P


def chain_ring():
    """The training grounds' ring: eight iron posts 4.6 high on stone feet round a black stone disc, joined by two hanging chains each, a crimson ring inlaid in the disc. Origin: the middle."""
    P = NP()
    gs, gi, gc = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON)
    R = 8.0
    pprism(gs, 0.0, 0.0, -0.7, 0.04, 6.6, seg=16, r_top=6.6, caps=True)
    m = 16
    for k in range(m):
        ring_slab(gc, 0.0, 0.0, 4.3, 4.9, 0.03, 0.1, k * TAU / m, (k + 1) * TAU / m)
    pprism(gi, 0.0, 0.0, 0.02, 0.14, 1.2, seg=8, r_top=1.1, caps=True)
    posts = []
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        x, z = R * math.cos(a), R * math.sin(a)
        bmass(P, x - 0.85, x + 0.85, z - 0.85, z + 0.85, -0.8, 0.9, 0.2, quoins=False)
        box(gi, x - 0.36, x + 0.36, 0.8, 4.6, z - 0.36, z + 0.36)
        pyramid(gi, x, z, 4.55, 0.3, 0.3, 1.3)
        box(gc, x - 0.4, x + 0.4, 2.9, 3.35, z - 0.4, z + 0.4)
        P.block("Post", x - 0.85, x + 0.85, -0.8, 4.6, z - 0.85, z + 0.85)
        posts.append((x, z))
    for k in range(8):
        a, b = posts[k], posts[(k + 1) % 8]
        for yy, sag in ((3.9, 0.8), (2.2, 0.55)):
            chain_swag(P, (a[0], yy, a[1]), (b[0], yy, b[1]), sag=sag, links=4, size=0.6)
    P.floor.append((-R, R, -R, R, 0.0))
    return P


def chain_bridge(L=22.0, w=5.0, sag=0.5, tower_h=8.6):
    """The chain bridge over the fissure: an iron plank deck 22 long and 5 wide, four battered stone pylons with iron spike crowns, two heavy hanging chains and two hand chains (links of
    iron) joined by hanger rods, a crimson pennant on each pylon and a glowing seam under the deck. Along x, deck top y 0 at both ends (it sags half a stud in the middle). Collision: the
    deck in 1.5-stud boxes, a guard along each edge, the pylons."""
    P = NP()
    gs, gi, gc, ge = P.geo(S_STONE), P.geo(S_IRON), P.geo(S_CRIMSON), P.geo(S_EMBER)
    rng = random.Random(23)

    def deck_y(x):
        t = (x + L / 2) / L
        return -sag * 4 * t * (1 - t)
    n = int(L / 1.5)
    seg = L / n
    for i in range(n):
        xa, xb = -L / 2 + i * seg, -L / 2 + (i + 1) * seg
        y = deck_y((xa + xb) / 2)
        for k in range(2):
            x0, x1 = xa + k * seg / 2 + 0.03, xa + (k + 1) * seg / 2 - 0.03
            yy = y + rng.uniform(-0.02, 0.02)
            box(gi, x0, x1, yy - 0.4, yy, -w / 2, w / 2)
        P.block("Deck", xa, xb + 0.02, y - 1.2, y + 0.02, -w / 2, w / 2)
        P.block("Guard", xa, xb + 0.02, y, y + 1.3, -w / 2 - 0.3, -w / 2 + 0.05)
        P.block("Guard", xa, xb + 0.02, y, y + 1.3, w / 2 - 0.05, w / 2 + 0.3)
    for z in (-w / 2 + 0.15, w / 2 - 0.15):
        box(gi, -L / 2, L / 2, -0.95, -0.5, z - 0.2, z + 0.2)                       # the stringers under the deck
    box(ge, -L / 2 + 1.5, L / 2 - 1.5, -0.85, -0.6, -0.3, 0.3)                       # the glowing seam under the deck's middle
    top = {}
    for xt in (-L / 2 + 0.4, L / 2 - 0.4):
        for z in (-w / 2 - 0.9, w / 2 + 0.9):
            bmass(P, xt - 1.2, xt + 1.2, z - 1.2, z + 1.2, -2.0, tower_h, 0.45, bands=(2.6, 5.4), seed=int(xt + z * 7))
            P.block("Pylon", xt - 1.3, xt + 1.3, -2.0, tower_h, z - 1.3, z + 1.3)
            cone(gi, xt, tower_h - 0.05, z, 0.95, 3.0, seg=4, phase=PI / 4)
            frust(gc, xt - 1.1, xt + 1.1, z - 1.1, z + 1.1, tower_h - 2.0, tower_h - 1.4, 0.05)
        top[xt] = tower_h - 0.9
    tops = sorted(top)
    for z in (-w / 2 - 0.9, w / 2 + 0.9):
        a = (tops[0], top[tops[0]], z)
        b = (tops[1], top[tops[1]], z)
        chain_swag(P, a, b, sag=top[tops[0]] - 2.6, links=16, size=1.1)
        hand_a = (tops[0], 1.6 + deck_y(tops[0]), z)
        hand_b = (tops[1], 1.6 + deck_y(tops[1]), z)
        chain_swag(P, (tops[0], 1.7, z), (tops[1], 1.7, z), sag=-0.0 - sag * 0 + 0.3, links=16, size=0.7)
        hx = tops[0] + 3.4
        while hx < tops[1] - 2.0:
            t = (hx - tops[0]) / (tops[1] - tops[0])
            cy = top[tops[0]] - (top[tops[0]] - 2.6) * 4 * t * (1 - t)
            cyl(gi, (hx, cy - 0.1, z), (hx, 1.7 + 0.3 * 4 * t * (1 - t) * 0 - 0.9 * 0, z), 0.07, 0.07, seg=4, caps=False)
            hx += 3.4
    P.floor.append((-L / 2, L / 2, -w / 2, w / 2, 0.0))
    P.marks["End"] = (L / 2, 0.0, 0.0)
    P.lights.append((0.0, -1.8, 0.0))
    P.emit.append(("Embers", (-4.0, -6.0, 0.0)))
    P.emit.append(("Embers", (4.0, -6.0, 0.0)))
    return P


BUILDING_BUILDERS = {"Gatehouse": gatehouse, "Keep": keep, "Armory": armory, "Residence": residence, "Arena": arena, "Bastion": bastion, "EmberCourt": ember_court,
                     "ChainRing": chain_ring, "RackShed": rack_shed, "UpperGate": upper_gate}
COURT_BUILDERS = {"GreatFlight": lambda: stair_flight(12, 14.0, 1.6, 2.0), "GreatFlightHigh": lambda: stair_flight(12, 14.0, 13.6, 2.0), "GreatLanding": lambda: stair_landing(14.0, 6.0, 13.6, 2.0),
                  "PosternFlight": lambda: stair_flight(12, 4.4, 1.6, 1.1, flank_h=1.3, post_every=4), "PosternFlightHigh": lambda: stair_flight(12, 4.4, 13.6, 1.1, flank_h=1.3, post_every=4),
                  "PosternLanding": lambda: stair_landing(4.4, 4.0, 13.6, 1.1, 1.3), "BridgeFlight": lambda: stair_flight(8, 6.0, 9.6, 1.0, flank_h=1.3, post_every=3),
                  "BridgeTop": lambda: stair_landing(6.0, 4.0, 9.6, 1.0, 1.3), "ChainBridge": chain_bridge, "Curtain12": lambda: curtain(12.0), "Curtain6": lambda: curtain(6.0),
                  "Parapet12": lambda: parapet(12.0), "Parapet6": lambda: parapet(6.0)}
PROP_BUILDERS = {"BrazierTall": brazier_tall, "BannerPole": banner_pole, "WeaponRack": weapon_rack, "StakeRow": stake_row, "TalonPlinth": talon_plinth}

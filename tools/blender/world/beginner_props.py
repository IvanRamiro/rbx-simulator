"""The Beginner Isle's kit and placements, on the Starting Island's prop atlas (start_props.STRIPS), so
it shares Yggdrasil's uploaded texture. The pines, plum trees, rocks, flowers, lanterns and egg
pedestals are Yggdrasil's own pieces; these are the island's:

- BI_LionGate: a three-bay lacquered archway, drum stones at its feet, brackets under its roofs.
- BI_CourtPaving: the Lion Court's flagstones, ring on ring, a bronze paw print where the lion sits.
- BI_Hall: the Hall of First Breath, double-eaved, on a stepped plinth, lattice doors behind columns.
- BI_Pavilion: an open meditation pavilion with mats round a bronze censer.
- BI_Bell: the great bronze bell in a roofed timber frame, its log striker on ropes.
- BI_Dummy, BI_WeaponRack, BI_LiftingStones: the training yard's gear, each visibly used.

    import beginner_props as BP
    objs, img = BP.build(); BP.export(objs); BP.write_placements()
"""
import math
import random

import beginner_island as Y
import start_props as P
import worldlib as W
import ygg_props as YP
import ygg_shops as SH

TAU = 2 * math.pi
_FLOOR = SH.FLOOR


def roof_at(mb, bands, dx, dz, *args, **kw):
    """YP.tiled_roof moved to x = dx, z = dz: it builds round x = 0."""
    temp = W.MeshBuilder()
    eave, ridge, half, depth = args
    YP.tiled_roof(temp, bands, eave, ridge, half, depth, dz, **kw)
    base = len(mb.verts)
    mb.verts.extend(W.Vector((v.x + dx, v.y, v.z)) for v in temp.verts)
    mb.faces.extend([[i + base for i in f] for f in temp.faces])
    mb.uvs.extend(temp.uvs)


def post(mb, bands, x, z, top, r=0.7, foot=0.0, band=P.LACQUER, sides=8):
    """A round-ish post on a bronze shoe, under a bronze capital, standing on `foot`."""
    c = (x, 0, z)
    mb.lathe([(r, top - 0.3, 0.9), (r * 1.04, foot + 1.0, 0.6)], sides, bands[band], centre=c, phase=TAU / 16, cap_top=False, cap_bottom=False)
    mb.lathe([(r + 0.14, foot + 1.0, 0.9), (r + 0.34, foot + 0.6, 0.8), (r + 0.34, foot, 0.55)], sides, bands[P.BRONZE], centre=c, phase=TAU / 16, cap_top=True)
    mb.lathe([(r + 0.28, top, 1.0), (r + 0.28, top - 0.3, 0.8), (r + 0.04, top - 0.55, 0.6)], sides, bands[P.BRONZE], centre=c, phase=TAU / 16, cap_top=True)


def brackets(mb, bands, x0, x1, y, z, count):
    """A row of stepped dougong brackets carrying the roof."""
    for k in range(count):
        x = x0 + (x1 - x0) * (k + 0.5) / count
        mb.box((x, y, z), (0.8, 0.3, 0.8), bands[P.WOOD], u=0.4, top_shade=0.75, side_shade=0.6)
        mb.box((x, y + 0.3, z), (1.4, 0.3, 0.7), bands[P.LACQUER], u=0.5, top_shade=0.8, side_shade=0.65)
        mb.box((x, y + 0.6, z), (0.8, 0.3, 1.3), bands[P.JADE], u=0.5, top_shade=0.8, side_shade=0.6)


def drum_stone(mb, bands, x, z):
    """A carved drum on a block, set against a gate post's foot."""
    mb.box((x, 0.75, z), (2.0, 1.5, 2.0), bands[P.PALE], u=0.35, top_shade=0.85, side_shade=0.6)
    mb.lathe([(0.0, 3.05, 0.95), (0.8, 2.95, 0.9), (1.05, 2.5, 0.8), (1.05, 1.9, 0.7), (0.8, 1.5, 0.6)], 12, bands[P.PALE],
             centre=(x, 0, z), cap_top=False)
    mb.lathe([(1.08, 2.5, 0.95), (1.08, 2.32, 0.7)], 12, bands[P.BRONZE], centre=(x, 0, z), cap_top=False, cap_bottom=False)


def lion_gate(coll, mat, bands):
    """Walked through along Z. Centre bay 20 studs wide, side bays 10; the ridge at 25."""
    mb = W.MeshBuilder()
    for sx in (-1, 1):
        for x, top in ((10.0, 17.2), (20.0, 12.4)):
            post(mb, bands, sx * x, 0, top, r=0.95, band=P.LACQUER)
            mb.box((sx * x, 0.5, 0), (3.2, 1.0, 3.2), bands[P.PALE], u=0.3, top_shade=0.85, side_shade=0.6)
            # a carved drum stone either side of each post's foot
            for sz in (-1, 1):
                drum_stone(mb, bands, sx * x, sz * 2.2)
    # the beams: a pair over the centre, each with a painted panel between
    mb.box((0, 14.2, 0), (21.6, 1.1, 1.3), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    mb.box((0, 16.3, 0), (21.6, 1.1, 1.3), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    mb.box((0, 15.25, 0), (6.4, 1.0, 0.7), bands[P.BRONZE], u=0.5, top_shade=0.95, side_shade=0.8)
    for sx in (-1, 1):
        mb.box((sx * 6.9, 15.25, 0), (6.6, 1.0, 0.5), bands[P.JADE], u=0.5, top_shade=0.9, side_shade=0.75)
        mb.box((sx * 15, 10.3, 0), (11.4, 0.9, 1.1), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
        mb.box((sx * 15, 11.7, 0), (11.4, 0.7, 1.0), bands[P.JADE], u=0.5, top_shade=0.9, side_shade=0.75)
        brackets(mb, bands, sx * 10.4, sx * 19.6, 12.4, 0, 4)
    brackets(mb, bands, -9.6, 9.6, 17.0, 0, 8)
    roof_at(mb, bands, 0, 0, 18.4, 21.8, 13.6, 4.4, lift=1.8, cols=18, rows=4)
    for sx in (-1, 1):
        roof_at(mb, bands, sx * 15.2, 0, 13.6, 15.9, 7.4, 3.4, lift=1.0, cols=10, rows=3)
    # a bronze pearl on the ridge
    mb.lathe([(0.0, 23.7, 1.0), (0.45, 23.35, 0.95), (0.6, 22.9, 0.85), (0.36, 22.5, 0.7), (0.3, 21.9, 0.6)], 10, bands[P.BRONZE], centre=(0, 0, 0), cap_top=False)
    return mb.object("BI_LionGate", coll, mat)


def court_paving(coll, mat, bands):
    """Ring on ring of flagstones to the kerb at Y.ARENA_R, a jade ring and a bronze paw print at the
    middle, under where the lion sits. Decoration on the level terrain: nothing collides with it."""
    mb = W.MeshBuilder()
    rnd = random.Random(501)
    top, bot = 0.16, -0.5
    rings = [(8.5, 15.5, 12), (15.5, 23.5, 20), (23.5, 32.0, 28), (32.0, 41.0, 36), (41.0, 49.5, 44)]
    gap = 0.14
    for r0, r1, n in rings:
        phase = rnd.uniform(0, TAU)
        for k in range(n):
            a0, a1 = phase + TAU * k / n, phase + TAU * (k + 1) / n
            da = gap / ((r0 + r1) / 2)
            arc = []
            steps = 3
            for s in range(steps + 1):
                a = a0 + da + (a1 - a0 - 2 * da) * s / steps
                arc.append((math.cos(a) * (r1 - gap), math.sin(a) * (r1 - gap)))
            for s in range(steps, -1, -1):
                a = a0 + da + (a1 - a0 - 2 * da) * s / steps
                arc.append((math.cos(a) * (r0 + gap), math.sin(a) * (r0 + gap)))
            P.slab_tile(mb, arc, top - rnd.uniform(0, 0.07), bot, bands[P.PALE], rnd.uniform(0.1, 0.9), rnd.uniform(0.62, 0.9))
    # the kerb: long dark stones
    n = 48
    for k in range(n):
        a0, a1 = TAU * k / n + 0.006, TAU * (k + 1) / n - 0.006
        poly = [(math.cos(a0) * 52.0, math.sin(a0) * 52.0), (math.cos(a1) * 52.0, math.sin(a1) * 52.0),
                (math.cos(a1) * 49.7, math.sin(a1) * 49.7), (math.cos(a0) * 49.7, math.sin(a0) * 49.7)]
        P.slab_tile(mb, poly, top + 0.12, bot, bands[P.DARK], 0.5, rnd.uniform(0.5, 0.75))
    # the jade ring and the medallion
    # (flat faces, each told to face up: a lathe's flat ring comes out facing down, which is how this whole middle went unseen)
    def ring(r0, r1, y, band, shade, seg=48, centre=(0.0, 0.0)):
        cx, cz = centre
        for k in range(seg):
            a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
            pts = [(cx + math.cos(a0) * r1, y, cz + math.sin(a0) * r1), (cx + math.cos(a1) * r1, y, cz + math.sin(a1) * r1)]
            pts += [(cx + math.cos(a1) * r0, y, cz + math.sin(a1) * r0), (cx + math.cos(a0) * r0, y, cz + math.sin(a0) * r0)] if r0 > 0 else [(cx, y, cz)]
            P.oriented(mb, pts, (0, 1, 0), band, 0.5, [shade] * len(pts))
    ring(7.1, 8.3, top + 0.05, bands[P.JADE], 0.8)
    ring(0.0, 7.1, top + 0.02, bands[P.DARK], 0.5)
    # the paw print, pointing at the gate (toes toward the arrival)
    ax, az = math.cos(math.radians(Y.ARRIVAL_BEARING)), math.sin(math.radians(Y.ARRIVAL_BEARING))
    sx, sz = -az, ax
    y = top + 0.09
    ring(0.0, 3.0, y, bands[P.BRONZE], 0.95, seg=24, centre=(-ax * 0.8, -az * 0.8))
    for off, r in ((-2.9, 1.15), (-1.0, 1.3), (1.0, 1.3), (2.9, 1.15)):
        reach = 3.9 - 0.3 * abs(off)
        ring(0.0, r, y + 0.012, bands[P.BRONZE], 0.95, seg=16, centre=(ax * reach + sx * off, az * reach + sz * off))
    return mb.object("BI_CourtPaving", coll, mat)


def hall(coll, mat, bands):
    """Front toward +Z. A plinth 38 wide and 22 deep, three steps; six columns before lattice doors."""
    mb = W.MeshBuilder()
    H0 = 2.4                 # the floor, on the plinth
    # the stepped plinth, with a ramp of carved stone up the middle of the steps
    mb.box((0, H0 / 2 - 0.2, 0), (38, H0 + 0.4, 22), bands[P.PALE], u=0.3, top_shade=0.9, side_shade=0.6)
    for k, (w, z, h) in enumerate(((24, 12.5, 1.6), (26, 14.0, 0.8))):
        mb.box((0, h / 2 - 0.1, z), (w, h + 0.2, 1.6), bands[P.PALE], u=0.55 + 0.1 * k, top_shade=0.92, side_shade=0.62)
    for x in range(-18, 19, 3):                                # the balustrade's stubby posts along the sides
        if abs(x) > 11:
            mb.box((x, H0 + 0.55, 10.4), (0.5, 1.1, 0.5), bands[P.PALE], u=0.4, top_shade=0.95, side_shade=0.7)
    for sx in (-1, 1):
        mb.box((sx * 14.8, H0 + 0.95, 10.4), (6.8, 0.3, 0.6), bands[P.PALE], u=0.5, top_shade=0.9, side_shade=0.7)
    # the walls: red lacquer lower panels, paper lattice above, in bays between the columns
    wall_z = 4.8
    mb.box((0, H0 + 7.2, -6.8), (29.4, 14.4, 0.6), bands[P.LACQUER], u=0.5, top_shade=0.6, side_shade=0.6)
    for sx in (-1, 1):
        mb.box((sx * 14.5, H0 + 7.2, -1.0), (0.6, 14.4, 12.2), bands[P.LACQUER], u=0.5, top_shade=0.6, side_shade=0.6)
    for x in (-9.0, 0.0, 9.0):                                 # high windows along the back, so it is never a blank wall
        mb.box((x, H0 + 7.6, -7.15), (6.0, 5.4, 0.12), bands[P.PAPER], u=0.5, top_shade=0.9, side_shade=0.9)
        for c in range(1, 6):
            mb.box((x - 3.0 + c, H0 + 7.6, -7.25), (0.14, 5.4, 0.1), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
        mb.box((x, H0 + 7.6, -7.25), (6.0, 0.14, 0.1), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
        mb.box((x, H0 + 10.4, -7.3), (6.6, 0.3, 0.3), bands[P.BRONZE], u=0.5, top_shade=0.9, side_shade=0.7)
        mb.box((x, H0 + 4.8, -7.3), (6.6, 0.3, 0.3), bands[P.BRONZE], u=0.5, top_shade=0.9, side_shade=0.7)
    xs = [-14.5, -8.7, -2.9, 2.9, 8.7, 14.5]
    for a, b in zip(xs, xs[1:]):
        mid, w = (a + b) / 2, b - a - 1.3
        mb.box((mid, H0 + 1.6, wall_z), (w, 3.2, 0.4), bands[P.LACQUER], u=0.5, top_shade=0.7, side_shade=0.65)
        mb.box((mid, H0 + 6.9, wall_z), (w, 7.4, 0.2), bands[P.PAPER], u=0.5, top_shade=0.95, side_shade=0.95)
        for c in range(1, 6):
            mb.box((mid - w / 2 + w * c / 6, H0 + 6.9, wall_z + 0.14), (0.14, 7.4, 0.12), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
        for c in range(1, 8):
            mb.box((mid, H0 + 3.2 + 7.4 * c / 8, wall_z + 0.14), (w, 0.14, 0.12), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
        mb.box((mid, H0 + 3.25, wall_z + 0.2), (w, 0.3, 0.3), bands[P.BRONZE], u=0.5, top_shade=0.9, side_shade=0.7)
    # door pulls: a bronze ring either side of the centre bay's meeting
    for sx in (-1, 1):
        mb.lathe([(0.55, H0 + 4.6, 0.95), (0.55, H0 + 4.3, 0.7)], 10, bands[P.BRONZE], centre=(sx * 0.7, 0, wall_z + 0.3), cap_top=True, cap_bottom=True)
    # the columns and what they carry
    for x in xs:
        post(mb, bands, x, 8.2, H0 + 11.4, r=0.85, foot=H0, band=P.LACQUER, sides=10)
    for sz, length in ((8.2, 33.0), (wall_z, 31.0)):
        mb.box((0, H0 + 11.6, sz), (length, 0.9, 1.0), bands[P.LACQUER], u=0.5, top_shade=0.8, side_shade=0.7)
    brackets(mb, bands, -15.5, 15.5, H0 + 12.2, 8.2, 11)
    # the lower roof wraps the hall; the upper hall rises through it under its own, higher roof
    roof_at(mb, bands, 0, 0, H0 + 13.0, H0 + 17.2, 21.4, 11.6, lift=2.0, cols=30, rows=6)
    mb.box((0, H0 + 18.2, 0), (20, 4.6, 7.6), bands[P.LACQUER], u=0.5, top_shade=0.6, side_shade=0.55)
    mb.box((0, H0 + 18.4, 3.86), (19.6, 2.4, 0.1), bands[P.PAPER], u=0.5, top_shade=0.9, side_shade=0.9)
    for c in range(1, 14):
        mb.box((-9.8 + 19.6 * c / 14, H0 + 18.4, 3.94), (0.14, 2.4, 0.1), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
    brackets(mb, bands, -9.6, 9.6, H0 + 20.7, 3.9, 7)
    roof_at(mb, bands, 0, 0, H0 + 21.5, H0 + 26.5, 13.6, 7.0, lift=1.7, cols=20, rows=5)
    # the name board under the upper eave, and a pearl over all
    SH.name_board(mb, bands, ((0, H0 + 18.4, 4.1), (8.0, 1.8)))
    mb.lathe([(0.0, H0 + 29.2, 1.0), (0.55, H0 + 28.8, 0.95), (0.72, H0 + 28.25, 0.85), (0.42, H0 + 27.8, 0.7), (0.34, H0 + 26.9, 0.6)], 10, bands[P.BRONZE], cap_top=False)
    # a censer at the foot of the steps
    censer(mb, bands, 0, 19.5, 0.0, 1.0)
    return mb.object("BI_Hall", coll, mat)


def censer(mb, bands, x, z, y0, s):
    """A three-legged bronze censer with a domed lid."""
    c = (x, 0, z)
    for k in range(3):
        a = TAU * k / 3 + 0.5
        mb.box((x + math.cos(a) * 0.95 * s, y0 + 0.5 * s, z + math.sin(a) * 0.95 * s), (0.34 * s, 1.0 * s, 0.34 * s), bands[P.BRONZE], u=0.5, top_shade=0.8, side_shade=0.6)
    mb.lathe([(1.0 * s, y0 + 2.3 * s, 0.95), (1.3 * s, y0 + 2.0 * s, 0.9), (1.3 * s, y0 + 1.4 * s, 0.75), (0.9 * s, y0 + 0.9 * s, 0.55)], 12, bands[P.BRONZE], centre=c, cap_top=False)
    mb.lathe([(0.0, y0 + 3.3 * s, 1.0), (0.2 * s, y0 + 3.2 * s, 0.95), (0.3 * s, y0 + 2.95 * s, 0.9), (0.85 * s, y0 + 2.6 * s, 0.85), (1.05 * s, y0 + 2.3 * s, 0.75)], 12, bands[P.BRONZE], centre=c, cap_top=False)


def pavilion(coll, mat, bands):
    mb = W.MeshBuilder()
    y = 1.2
    mb.box((0, y / 2 - 0.3, 0), (15, y + 0.6, 15), bands[P.PALE], u=0.3, top_shade=0.9, side_shade=0.6)
    for sz, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)):            # a step on every side
        mb.box((sx * 8.1, 0.25, sz * 8.1), (6 if sz else 1.2, 0.6, 1.2 if sz else 6), bands[P.PALE], u=0.6, top_shade=0.92, side_shade=0.62)
    r = 5.2
    for sx in (-1, 1):
        for sz in (-1, 1):
            post(mb, bands, sx * r, sz * r, y + 8.2, r=0.55, foot=y)
    for sz in (-1, 1):
        mb.box((0, y + 8.4, sz * r), (11.6, 0.55, 0.7), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
        mb.box((sz * r, y + 8.4, 0), (0.7, 0.55, 11.6), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    for sz in (-1, 1):
        brackets(mb, bands, -4.4, 4.4, y + 8.8, sz * r, 4)
    roof_at(mb, bands, 0, 0, y + 9.7, y + 12.9, 8.2, 7.6, lift=1.3, cols=14, rows=5)
    mb.lathe([(0.0, y + 14.6, 1.0), (0.34, y + 14.3, 0.95), (0.44, y + 13.95, 0.85), (0.26, y + 13.65, 0.7), (0.22, y + 12.9, 0.6)], 8, bands[P.BRONZE], cap_top=False)
    # four mats round the censer
    censer(mb, bands, 0, 0, y, 0.55)
    for k in range(4):
        a = TAU * k / 4
        cx, cz = math.cos(a) * 3.2, math.sin(a) * 3.2
        mb.lathe([(0.0, y + 0.26, 0.95), (0.8, y + 0.24, 0.9), (1.0, y + 0.1, 0.7), (0.9, y + 0.01, 0.5)], 14, bands[P.LACQUER], centre=(cx, 0, cz), cap_top=False)
    return mb.object("BI_Pavilion", coll, mat)


def bell(coll, mat, bands):
    """The bell hangs in a timber frame under a small roof; a log on ropes strikes it from +Z."""
    mb = W.MeshBuilder()
    mb.box((0, 0.3, 0), (13, 0.9, 11), bands[P.PALE], u=0.35, top_shade=0.9, side_shade=0.6)
    for sx in (-1, 1):
        for sz in (-1, 1):
            post(mb, bands, sx * 5, sz * 4, 13.4, r=0.58, foot=0.7, band=P.WOOD)
        mb.box((sx * 5, 12.5, 0), (0.7, 0.7, 8.8), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.65)
    mb.box((0, 13.2, 0), (11.4, 0.8, 0.8), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.65)
    # the bell: flared at its lip, ribbed, its crown a bronze loop
    mb.lathe([(0.0, 12.0, 1.0), (1.5, 12.0, 0.95), (2.05, 11.4, 0.9), (2.2, 9.6, 0.82), (2.3, 7.4, 0.74), (2.7, 5.3, 0.66), (3.25, 4.1, 0.58), (3.2, 3.85, 0.42)], 20, bands[P.BRONZE], cap_top=False, cap_bottom=True)
    for y, r in ((10.3, 2.2), (8.3, 2.36), (5.5, 2.74)):
        mb.lathe([(r + 0.1, y + 0.16, 0.98), (r + 0.1, y - 0.16, 0.7)], 20, bands[P.BRONZE], cap_top=False, cap_bottom=False)
    mb.box((0, 12.45, 0), (0.7, 1.0, 0.7), bands[P.BRONZE], u=0.5, top_shade=0.95, side_shade=0.75)
    # the rows of bosses round its shoulder, as on a temple bell
    for row, (y, r) in enumerate(((10.0, 2.33), (9.0, 2.42))):
        for k in range(12):
            a = TAU * (k + 0.5 * row) / 12
            mb.lathe([(0.0, y + 0.22, 1.0), (0.18, y + 0.1, 0.95), (0.2, y - 0.14, 0.7)], 6, bands[P.BRONZE], centre=(math.cos(a) * r, 0, math.sin(a) * r), cap_top=False)
    # the striker log, on two ropes from the frame
    y, z = 6.6, 4.0
    W.mb_tube(mb, [(-0.0, y, z), (0.0, y, z + 3.4)], lambda t: 0.42, 8, bands[P.WOOD], per=2)
    for dz in (0.5, 2.9):
        W.mb_tube(mb, [(0, y + 0.3, z + dz), (0, 12.8, z + dz * 0.1)], lambda t: 0.07, 4, bands[P.BARK], per=2)
    roof_at(mb, bands, 0, 0, 14.0, 17.0, 7.4, 6.2, lift=1.2, cols=12, rows=4)
    return mb.object("BI_Bell", coll, mat)


def dummy(coll, mat, bands):
    """A wooden training dummy, worn pale where it gets hit."""
    mb = W.MeshBuilder()
    mb.box((0, 0.3, 0), (2.4, 0.6, 2.4), bands[P.PALE], u=0.3, top_shade=0.85, side_shade=0.6)
    mb.lathe([(0.0, 6.5, 0.95), (0.42, 6.4, 0.9), (0.58, 6.1, 0.82), (0.58, 4.8, 0.95), (0.6, 3.4, 0.7), (0.6, 2.6, 0.92), (0.62, 0.5, 0.5)], 10, bands[P.WOOD], cap_top=False)
    W.mb_tube(mb, [(-0.1, 4.95, 0.3), (-0.75, 5.0, 1.2), (-0.65, 5.1, 2.05)], lambda t: 0.17 - 0.05 * t, 6, bands[P.WOOD], per=4)
    W.mb_tube(mb, [(0.1, 4.75, 0.3), (0.75, 4.8, 1.2), (0.65, 4.9, 2.05)], lambda t: 0.17 - 0.05 * t, 6, bands[P.WOOD], per=4)
    W.mb_tube(mb, [(0.0, 3.8, 0.3), (0.0, 3.85, 1.9)], lambda t: 0.17 - 0.04 * t, 6, bands[P.WOOD], per=2)
    W.mb_tube(mb, [(0.0, 1.9, 0.3), (0.1, 1.5, 1.2), (0.25, 0.7, 1.45)], lambda t: 0.2 - 0.05 * t, 6, bands[P.WOOD], per=4)
    for y in (6.0, 3.0):                                         # rope lashings
        mb.lathe([(0.66, y + 0.14, 0.9), (0.66, y - 0.14, 0.6)], 10, bands[P.BARK], cap_top=False, cap_bottom=False)
    return mb.object("BI_Dummy", coll, mat)


def weapon_rack(coll, mat, bands):
    mb = W.MeshBuilder()
    for sx in (-1, 1):
        mb.box((sx * 4.2, 3.1, 0), (0.4, 6.2, 0.4), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.65)
        mb.box((sx * 4.2, 0.2, 0), (0.6, 0.4, 2.6), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.65)
    mb.box((0, 5.6, 0), (9.2, 0.34, 0.34), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    mb.box((0, 1.5, 0.4), (8.6, 0.3, 0.7), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.65)
    for k, x in enumerate((-3.2, -2.0, -0.8, 0.8, 2.0, 3.2)):
        lean = 0.12 * (k % 2)
        W.mb_tube(mb, [(x, 1.5, 0.45), (x, 8.0, 0.0 - lean)], lambda t: 0.1, 5, bands[P.WOOD], per=2)
        tip = (x, 8.0, -lean)
        mb.lathe([(0.0, tip[1] + 1.3, 1.0), (0.2, tip[1] + 0.3, 0.9), (0.09, tip[1], 0.7)], 4, bands[P.BRONZE], centre=(x, 0, -lean), cap_top=False)
        mb.lathe([(0.2, tip[1], 0.7), (0.2, tip[1] - 0.25, 0.5)], 6, bands[P.LACQUER], centre=(x, 0, -lean), cap_top=False, cap_bottom=False)
    return mb.object("BI_WeaponRack", coll, mat)


def lifting_stones(coll, mat, bands):
    """Stone padlocks of three sizes, the weights every sect starts its students on."""
    mb = W.MeshBuilder()
    for (x, z, s, yaw) in ((-1.9, 0.4, 1.0, 0.3), (0.7, -0.6, 0.78, -0.5), (2.5, 0.9, 0.58, 1.1)):
        ca, sa = math.cos(yaw), math.sin(yaw)
        mb.box((x, 0.75 * s, z), (2.4 * s, 1.5 * s, 1.0 * s), bands[P.PALE], yaw=yaw, u=0.4, top_shade=0.8, side_shade=0.6)
        for k in range(9):
            a = math.pi * k / 8
            b = math.pi * (k + 1) / 8
            if k == 8:
                break
            lx0, ly0, lx1, ly1 = math.cos(a) * 0.72 * s, math.sin(a) * 0.72 * s + 1.5 * s, math.cos(b) * 0.72 * s, math.sin(b) * 0.72 * s + 1.5 * s
            W.mb_tube(mb, [(x + lx0 * ca, ly0, z - lx0 * sa), (x + lx1 * ca, ly1, z - lx1 * sa)], lambda t: 0.16 * s, 5, bands[P.PALE], per=1)
    return mb.object("BI_LiftingStones", coll, mat)


PIECES = [lion_gate, court_paving, hall, pavilion, bell, dummy, weapon_rack, lifting_stones]


def build(only=None):
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    root = W.collection(Y.NAME)
    coll = W.collection("BI_Kit", root)
    W.clear_collection(coll)
    objs = [b(coll, mat, bands) for b in PIECES if only is None or b.__name__ == only]
    return objs, img


def export(objs, img):
    path = W.REPO + "/assets/world/BeginnerIsle/BeginnerIsle_Kit.fbx"
    W.export_batch(objs, path, image=img, anchor_name="BI_KitAnchor")
    return path


# ---------- placements ----------
def ground(x, z):
    h, _ = Y.height(x, z)
    return 0.0 if h is None else h


def _yaw_to(x, z, tx, tz):
    return math.atan2(tx - x, tz - z)


def _clear(x, z, rim_clear=8.0, path_clear=7.0):
    if math.hypot(x, z) < Y.RING_R + 8:
        return False
    if Y.edge_distance(x, z) < rim_clear or Y.path_distance(x, z) < path_clear:
        return False
    for (cx, cz), r in ((Y.GATE, 26), (Y.ARRIVAL, 20), (Y.YARD, Y.YARD_R + 6), (Y.PAVILION, Y.PAVILION_R + 9), (Y.BELL, 13), (Y.HALL, 30)):
        if math.hypot(x - cx, z - cz) < r:
            return False
    return True


def placements():
    rnd = random.Random(4242)
    kit = {}

    def put(name, x, z, yaw=0.0, scale=None, y=None):
        e = {"Position": (x, ground(x, z) if y is None else y, z), "Yaw": yaw}
        if scale:
            e["Scale"] = scale
        kit.setdefault(name, []).append(e)
    gx, gz = Y.GATE
    put("BI_LionGate", gx, gz, _yaw_to(gx, gz, *Y.ARRIVAL), y=0.0)
    put("BI_CourtPaving", 0, 0, 0.0, y=0.0)
    # the ground beyond its kerb, each piece authored in island coordinates (island_upgrades.py)
    put("BI_CourtApron", 0, 0, 0.0, y=0.0)
    put("BI_Roads", 0, 0, 0.0, y=0.0)
    put("BI_YardFloor", 0, 0, 0.0, y=0.0)
    hx, hz = Y.HALL
    put("BI_Hall", hx, hz, _yaw_to(hx, hz, 0, 0), y=0.0)
    px, pz = Y.PAVILION
    put("BI_Pavilion", px, pz, _yaw_to(px, pz, 0, 0), y=3.0)
    bx, bz = Y.BELL
    put("BI_Bell", bx, bz, _yaw_to(bx, bz, 0, 0), y=0.0)
    # the training yard: dummies in two ranks facing the racks, the racks along its outer edge
    yx, yz = Y.YARD
    b = math.atan2(yz, yx)
    ox, oz = math.cos(b), math.sin(b)             # outward
    sx, sz = -oz, ox
    for row, (d, xs) in enumerate(((-6.0, (-12, -4, 4, 12)), (4.0, (-8, 0, 8)))):
        for s in xs:
            x, z = yx + ox * d + sx * s, yz + oz * d + sz * s
            put("BI_Dummy", x, z, _yaw_to(x, z, yx + ox * 40, yz + oz * 40) + rnd.uniform(-0.12, 0.12), y=0.0)
    for s in (-11, 11):
        x, z = yx + ox * 15 + sx * s, yz + oz * 15 + sz * s
        put("BI_WeaponRack", x, z, _yaw_to(x, z, yx, yz), y=0.0)
    for (d, s) in ((13.0, 0.0), (-13.0, -15.0)):
        x, z = yx + ox * d + sx * s, yz + oz * d + sz * s
        put("BI_LiftingStones", x, z, rnd.uniform(0, TAU), y=0.0)
    # stone lanterns ringing the court, gaps left where the paths come in
    lamps = []
    for k in range(16):
        a = 11.25 + 22.5 * k
        x, z = Y.polar(a, 57.5)
        if Y.path_distance(x, z) < 6.0 or math.hypot(x - Y.GATE[0], z - Y.GATE[1]) < 12:
            continue
        lamps.append((x, z))
    for x, z in lamps:
        put("SI_StoneLantern", x, z, _yaw_to(x, z, 0, 0), y=0.0)
        put("SI_LanternLight", x, z, _yaw_to(x, z, 0, 0), y=0.0)
    # nature: the pines toward the rim, plum blossom nearer the buildings, rocks and flowers between
    taken = []

    def scatter(name, count, gap, inner=0.0, scale=(0.85, 1.25)):
        tries = 0
        placed = 0
        while placed < count and tries < count * 300:
            tries += 1
            a, r = rnd.uniform(0, TAU), 150 * math.sqrt(rnd.random())
            x, z = math.cos(a) * r, math.sin(a) * r
            if Y.height(x, z)[0] is None or not _clear(x, z) or r < inner:
                continue
            if any(math.hypot(x - tx, z - tz) < gap + tg for tx, tz, tg in taken):
                continue
            taken.append((x, z, gap * 0.5))
            put(name, x, z - 0.0, rnd.uniform(0, TAU), round(rnd.uniform(*scale), 3))
            placed += 1
    scatter("SI_SpiritPineA", 9, 15, inner=88)
    scatter("SI_SpiritPineB", 8, 15, inner=88)
    scatter("SI_BlossomTreeA", 7, 12)
    scatter("SI_BlossomTreeB", 5, 12)
    scatter("SI_MossRockA", 9, 7, scale=(0.7, 1.3))
    scatter("SI_MossRockB", 7, 7, scale=(0.7, 1.3))
    scatter("SI_FlowersWarm", 16, 4, scale=(0.9, 1.3))
    scatter("SI_FlowersWhite", 14, 4, scale=(0.9, 1.3))
    scatter("SI_FlowersViolet", 12, 4, scale=(0.9, 1.3))
    return kit


def write_placements(path=W.REPO + "/src/worldbuild/Placements/BeginnerIsle.lua"):
    kit = placements()
    lines = ["-- Generated by tools/blender/world/beginner_props.py. Do not edit by hand.",
             "-- Island-local Roblox studs. BI_* are this island's pieces, SI_* copies of Yggdrasil's templates.",
             "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for e in kit[name]:
            x, y, z = e["Position"]
            extra = ", Scale = %.3f" % e["Scale"] if "Scale" in e else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, e["Yaw"], extra))
        lines.append("        },")
    lines.append("    },")
    lines.append("    -- Yggdrasil's lotus pedestals (the eggs' first stands), behind the lion")
    lines.append("    EggStandPieces = { Pedestal = \"SI_EggPedestal\", GlowRing = \"SI_EggGlowRing\" },")
    lines.append("    EggStands = {")
    for eid, (x, z) in zip(YP.EGG_IDS, Y.EGG_SPOTS):
        lines.append("        { EggId = \"%s\", Position = Vector3.new(%.2f, 0.00, %.2f), Yaw = %.4f, EggRest = %.2f }," % (eid, x, z, _yaw_to(x, z, 0, 0), P.PEDESTAL_TOP))
    lines.append("    },")
    cx, cz = Y.GATE[0] + (0 - Y.GATE[0]) * 0.12, Y.GATE[1] + (0 - Y.GATE[1]) * 0.12
    lines.append("    Checkpoint = Vector3.new(%.2f, 0.65, %.2f)," % (cx, cz))
    lines.append("}")
    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path, {k: len(v) for k, v in kit.items()}

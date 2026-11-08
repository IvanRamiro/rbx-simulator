"""The outer islands brought up to the Beginner Isle's standard (the owner, November 5, 2026: "I already like the beginner Island
layout and design ... analyze and improve the other Island ... always keep the arena in the middle and the eggs").

What makes the Beginner Isle read: a crisp paved court with a kerb, one line from gate to court to a landmark behind it, open ground and
props gathered in groups. So each island gets, in its own materials and with its own idea (nothing here is a recoloured copy):

- Jade Grove: JG_ArenaFloor (mossy flagstones, jade inlay, a jade lotus at the middle), JG_Hermitage (the Sage's stilted bamboo hermitage).
- Ember Peak: EP_ArenaFloor (hexagonal basalt over lava, a cinnabar sun), EP_ArenaGlow (the lava in its seams and a broken ring of fire
  round it), EP_FirePylon + EP_PylonFire (basalt pylons holding fire high round the arena).
- Moonlit Isle: MI_ArenaFloor (a moon dial: marble, a band of night with the eight phases, a gold star), MI_MoonGate (a great porcelain and
  gold moon gate on the bay, behind the eggs).
- Origin Abyss: OA_ArenaFloor (broken temple slabs), OA_ArenaGlow (void light in the cracks, a spiral sigil), OA_Colonnade (what is left of
  the temple's colonnade, arcing round both flanks of the court).

Everything is unwrapped onto its island's existing atlas, so the one FBX brings no new textures: WorldBuilder.storeUpgrades points each piece
at the island's uploaded atlas. The floors don't collide, like the Beginner Isle's.

    import island_upgrades as U
    U.export()                       # assets/world/IslandUpgrades.fbx
"""
import math
import random

import bpy

import ember_island as E
import ember_meshes as EM
import jade_meshes as JM
import moon_meshes as MM
import origin_island as O
import origin_meshes as OM
import start_props as P
import worldlib as W

TAU = 2 * math.pi
TOP, BOT = 0.16, -0.5  # the floor stands this far above and below the level ground, like the Beginner Isle's
oriented = P.oriented


# ---------- shared shapes ----------
def ring_slabs(mb, rnd, rings, band_of, shade=(0.55, 0.85), gap=0.14, sink=0.07, u=None):
    """Ring on ring of curved flagstones. rings: (inner radius, outer radius, how many); band_of(ring index, slab index) -> a band.
    A slab is one texel of its strip: give `u` when the strip has spots a whole slab mustn't land on (the night sky's stars)."""
    for i, (r0, r1, n) in enumerate(rings):
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
            P.slab_tile(mb, arc, TOP - rnd.uniform(0, sink), BOT, band_of(i, k), rnd.uniform(0.1, 0.9) if u is None else u, rnd.uniform(*shade))


def kerb(mb, rnd, r0, r1, n, band, shade=(0.5, 0.75), lift=0.12):
    for k in range(n):
        a0, a1 = TAU * k / n + 0.006, TAU * (k + 1) / n - 0.006
        poly = [(math.cos(a0) * r1, math.sin(a0) * r1), (math.cos(a1) * r1, math.sin(a1) * r1),
                (math.cos(a1) * r0, math.sin(a1) * r0), (math.cos(a0) * r0, math.sin(a0) * r0)]
        P.slab_tile(mb, poly, TOP + lift, BOT, band, rnd.uniform(0.1, 0.9), rnd.uniform(*shade))


def disc(mb, r, y, band, seg=48, shade=0.6, u=0.5, centre=(0, 0)):
    """A flat disc facing up."""
    cx, cz = centre
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        oriented(mb, [(cx, y, cz), (cx + math.cos(a0) * r, y, cz + math.sin(a0) * r), (cx + math.cos(a1) * r, y, cz + math.sin(a1) * r)],
                 (0, 1, 0), band, u, [shade] * 3)


def annulus(mb, r0, r1, y, band, seg=64, shade=0.8, u=0.5, a_from=0.0, a_to=TAU):
    for k in range(seg):
        a0 = a_from + (a_to - a_from) * k / seg
        a1 = a_from + (a_to - a_from) * (k + 1) / seg
        oriented(mb, [(math.cos(a0) * r1, y, math.sin(a0) * r1), (math.cos(a1) * r1, y, math.sin(a1) * r1),
                      (math.cos(a1) * r0, y, math.sin(a1) * r0), (math.cos(a0) * r0, y, math.sin(a0) * r0)],
                 (0, 1, 0), band, u, [shade] * 4)


def petal(mb, a, r0, r1, half, y, band, shade=0.85, u=0.5):
    """A leaf-shaped inlay pointing out along angle a."""
    ca, sa = math.cos(a), math.sin(a)
    mid = (r0 + r1) * 0.45
    pts = [(ca * r0, sa * r0), (ca * mid - sa * half, sa * mid + ca * half), (ca * r1, sa * r1), (ca * mid + sa * half, sa * mid - ca * half)]
    oriented(mb, [(x, y, z) for x, z in pts], (0, 1, 0), band, u, [shade] * 4)


def roof(mb, centre, hx, hz, rise, band, lift=1.2, ridge=0.28, rows=5, seg=8, shade=(0.62, 0.92)):
    """A hipped roof with a concave pitch and upswept corners: tiled courses, each slightly different in shade."""
    cx, cy, cz = centre
    rnd = random.Random(int(hx * 13 + hz * 7))

    def point(side, s, t):
        x_half = hx + (hx * ridge - hx) * t
        z_half = hz + (hz * ridge - hz) * t
        y = cy + rise * t ** 1.5 + lift * abs(s) ** 4 * (1 - t) ** 2
        if side == 0:
            return (cx + s * x_half, y, cz + z_half)
        if side == 1:
            return (cx + x_half, y, cz - s * z_half)
        if side == 2:
            return (cx - s * x_half, y, cz - z_half)
        return (cx - x_half, y, cz + s * z_half)

    wants = [(0, 0.7, 0.7), (0.7, 0.7, 0), (0, 0.7, -0.7), (-0.7, 0.7, 0)]
    for side in range(4):
        for i in range(rows):
            t0, t1 = i / rows, (i + 1) / rows
            for j in range(seg):
                s0, s1 = -1 + 2 * j / seg, -1 + 2 * (j + 1) / seg
                sh = rnd.uniform(*shade)
                oriented(mb, [point(side, s0, t0), point(side, s1, t0), point(side, s1, t1), point(side, s0, t1)], wants[side], band,
                         rnd.uniform(0.1, 0.9), [sh * 0.8, sh * 0.8, sh, sh])
    # the eave's edge given some thickness, and the underside following it up to a flat ceiling
    soffit_t, drop = 0.42, 0.35
    ceiling = cy + rise * soffit_t ** 1.5 - 0.12
    x_in, z_in = hx + (hx * ridge - hx) * soffit_t, hz + (hz * ridge - hz) * soffit_t

    def inner(side, s):
        return {0: (cx + s * x_in, ceiling, cz + z_in), 1: (cx + x_in, ceiling, cz - s * z_in),
                2: (cx - s * x_in, ceiling, cz - z_in), 3: (cx - x_in, ceiling, cz + s * z_in)}[side]

    for side in range(4):
        out = (wants[side][0], 0, wants[side][2])
        for j in range(seg):
            s0, s1 = -1 + 2 * j / seg, -1 + 2 * (j + 1) / seg
            a, b = point(side, s0, 0), point(side, s1, 0)
            a2, b2 = (a[0], a[1] - drop, a[2]), (b[0], b[1] - drop, b[2])
            oriented(mb, [a, b, b2, a2], out, band, 0.5, [0.3] * 4)
            oriented(mb, [a2, b2, inner(side, s1), inner(side, s0)], (out[0] * 0.3, -1, out[2] * 0.3), band, 0.5, [0.22] * 4)
    oriented(mb, [(cx - x_in, ceiling, cz + z_in), (cx + x_in, ceiling, cz + z_in), (cx + x_in, ceiling, cz - z_in), (cx - x_in, ceiling, cz - z_in)], (0, -1, 0), band, 0.5, [0.2] * 4)
    top = cy + rise
    # the ridge cap, across the flat left at the top
    mb.box((cx, top + 0.02, cz), (max(hx, hz) * ridge * 2.05, 0.3, min(hx, hz) * ridge * 2.05), band, u=0.5, top_shade=0.9, side_shade=0.6)
    return top


def torus(mb, centre, R, r, band, seg=56, sides=8, a_from=0.0, a_to=TAU, taper=None, shade=0.85, yaw=0.0):
    """A ring standing upright, facing +Z (turned by yaw), from angle a_from to a_to (0 is +X, TAU/4 is straight up)."""
    cx, cy, cz = centre
    cs, sn = math.cos(yaw), math.sin(yaw)

    def p(a, b, rr):
        ring_x, ring_y = math.cos(a) * (R + math.cos(b) * rr), math.sin(a) * (R + math.cos(b) * rr)
        z = math.sin(b) * rr
        return (cx + ring_x * cs + z * sn, cy + ring_y, cz - ring_x * sn + z * cs)

    for i in range(seg):
        a0 = a_from + (a_to - a_from) * i / seg
        a1 = a_from + (a_to - a_from) * (i + 1) / seg
        r0 = r * (taper(i / seg) if taper else 1.0)
        r1 = r * (taper((i + 1) / seg) if taper else 1.0)
        for j in range(sides):
            b0, b1 = TAU * j / sides, TAU * (j + 1) / sides
            bm = (b0 + b1) / 2
            am = (a0 + a1) / 2
            want_x, want_y = math.cos(am) * math.cos(bm), math.sin(am) * math.cos(bm)
            want_z = math.sin(bm)
            want = (want_x * cs + want_z * sn, want_y, -want_x * sn + want_z * cs)
            oriented(mb, [p(a0, b0, r0), p(a1, b0, r1), p(a1, b1, r1), p(a0, b1, r0)], want, band, i / seg, [shade] * 4)


def column(mb, x, z, y0, y1, r, band, seg=8, flutes=False, foot=None):
    """A column on a plinth of its own band, its top and foot flared a little."""
    foot = foot or band
    rmod = (lambda th, k: 1.0 + 0.06 * math.cos(th * seg)) if flutes else None
    mb.lathe([(r * 0.92, y1, 0.8), (r, y1 - 0.5, 0.75), (r, y0 + 0.7, 0.55)], seg * (3 if flutes else 1), band, centre=(x, 0, z), rmod=rmod, cap_top=True)
    mb.lathe([(r + 0.32, y0 + 0.75, 0.75), (r + 0.5, y0 + 0.3, 0.6), (r + 0.5, y0 - 1.0, 0.45)], seg, foot, centre=(x, 0, z), cap_top=True)


# ---------- Jade Grove ----------
def jade_floor(coll, mat, bands):
    """Mossy flagstones with moss in their joints and every so often one of jade; a kerb of dark jade; a jade lotus under the Sage."""
    rnd = random.Random(611)
    mb = W.MeshBuilder()
    disc(mb, 49.8, TOP - 0.09, bands[JM.MOSS], seg=64, shade=0.5)
    rings = [(8.5, 16.0, 11), (16.0, 24.0, 18), (24.0, 32.5, 25), (32.5, 41.0, 31), (41.0, 49.6, 38)]

    def band_of(i, k):
        return bands[JM.JADE] if (i >= 1 and k % (9 + i) == 0) else bands[JM.STONE]

    ring_slabs(mb, rnd, rings, band_of, shade=(0.62, 0.95), gap=0.2)
    kerb(mb, rnd, 49.7, 52.0, 44, bands[JM.JADE], shade=(0.45, 0.65))
    annulus(mb, 7.2, 8.4, TOP + 0.05, bands[JM.GOLD], seg=48, shade=0.85)
    disc(mb, 7.2, TOP + 0.03, bands[JM.MOSS], seg=48, shade=0.42)
    for k in range(8):  # the lotus: outer petals, inner petals
        a = TAU * k / 8
        petal(mb, a, 1.6, 6.9, 1.5, TOP + 0.06, bands[JM.JADE], shade=0.85)
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        petal(mb, a, 0.8, 4.3, 1.05, TOP + 0.08, bands[JM.JADE], shade=1.0)
    disc(mb, 1.25, TOP + 0.1, bands[JM.GOLD], seg=16, shade=1.0)
    return mb.object("JG_ArenaFloor", coll, mat)


def jade_hermitage(coll, mat, bands):
    """The Sage's hermitage: a bamboo hut on stilts, open at the front (+Z), a low shrine inside, under a double roof of living leaves."""
    mb = W.MeshBuilder()
    deck_y = 2.6
    hx, hz = 9.0, 7.0
    bamboo, bark, leaf, stone, jade, gold = bands[JM.BAMBOO], bands[JM.BARK], bands[JM.LEAF], bands[JM.STONE], bands[JM.JADE], bands[JM.GOLD]
    # stilts down into the ground
    for x in (-hx + 0.8, 0.0, hx - 0.8):
        for z in (-hz + 0.8, 0.0, hz - 0.8):
            mb.lathe([(0.42, deck_y, 0.8), (0.46, -2.5, 0.5)], 8, bamboo, centre=(x, 0, z), cap_top=False)
    # the deck: planks across it
    for k in range(9):
        z = -hz + (k + 0.5) * (2 * hz / 9)
        mb.box((0, deck_y + 0.15, z), (2 * hx, 0.3, 2 * hz / 9 - 0.08), bark, u=(k * 0.11) % 1, top_shade=0.9 - 0.04 * (k % 3), side_shade=0.5)
    # the steps, at the front
    for k in range(3):
        top_y = deck_y - 0.05 - k * 0.8
        z = hz + 0.8 + k * 1.3
        mb.box((0, (top_y - 1.5) / 2, z), (8.0, top_y + 1.5, 1.5), stone, u=(k * 0.3) % 1, top_shade=0.85, side_shade=0.5)   # solid, down into the ground
    # posts: at the corners and either side of the opening
    posts = [(-hx + 0.6, -hz + 0.6), (hx - 0.6, -hz + 0.6), (-hx + 0.6, hz - 0.6), (hx - 0.6, hz - 0.6), (-3.8, hz - 0.6), (3.8, hz - 0.6), (-hx + 0.6, 0), (hx - 0.6, 0)]
    for x, z in posts:
        mb.lathe([(0.34, 10.0, 0.85), (0.38, deck_y + 0.3, 0.6)], 8, bamboo, centre=(x, 0, z), cap_top=False)
        for ny in (4.6, 7.4):  # bamboo's nodes
            mb.lathe([(0.45, ny + 0.1, 0.9), (0.45, ny - 0.1, 0.6)], 8, bamboo, centre=(x, 0, z), cap_top=False)
    # the back and side screens: culms side by side, stopping short of the eaves
    for k in range(25):
        x = -hx + 0.9 + k * (2 * hx - 1.8) / 24
        mb.lathe([(0.2, 7.0 + 0.2 * math.sin(k * 1.7), 0.8), (0.22, deck_y + 0.3, 0.55)], 6, bamboo, centre=(x, 0, -hz + 0.5), cap_top=True)
    for side in (-1, 1):
        for k in range(14):
            z = -hz + 1.0 + k * 0.42
            mb.lathe([(0.2, 7.0 + 0.2 * math.sin(k * 2.3), 0.8), (0.22, deck_y + 0.3, 0.55)], 6, bamboo, centre=(side * (hx - 0.5), 0, z), cap_top=True)
    # the beams carrying the roof
    for x in (-hx + 0.6, hx - 0.6):
        mb.box((x, 10.1, 0), (0.6, 0.5, 2 * hz), bark, u=0.3, top_shade=0.7, side_shade=0.5)
    for z in (-hz + 0.6, hz - 0.6):
        mb.box((0, 10.4, z), (2 * hx, 0.5, 0.6), bark, u=0.6, top_shade=0.7, side_shade=0.5)
    # the double roof, its leaves overhanging well
    top = roof(mb, (0, 10.5, 0), hx + 3.2, hz + 3.2, 3.2, leaf, lift=1.6, ridge=0.45)
    mb.lathe([(1.6, top + 0.3, 0.7), (1.8, top - 0.1, 0.5)], 8, bark, cap_top=True)  # a short drum between the roofs
    top2 = roof(mb, (0, top + 0.15, 0), 5.4, 4.2, 3.0, leaf, lift=1.1, ridge=0.2, rows=4, seg=6)
    mb.lathe([(0.0, top2 + 2.2, 1.0), (0.55, top2 + 1.5, 0.95), (0.3, top2 + 1.0, 0.8), (0.42, top2 + 0.5, 0.8), (0.65, top2 + 0.1, 0.6)], 10, jade, cap_top=False)
    # the shrine inside: a stone table, a censer, two jade lamps
    mb.box((0, deck_y + 0.9, -hz + 2.6), (6.0, 1.2, 2.0), stone, u=0.2, top_shade=0.8, side_shade=0.5)
    mb.lathe([(0.0, deck_y + 2.6, 1.0), (0.5, deck_y + 2.4, 0.9), (0.8, deck_y + 2.05, 0.75), (0.5, deck_y + 1.55, 0.6)], 10, gold, centre=(0, 0, -hz + 2.6), cap_top=False)
    for x in (-2.2, 2.2):
        mb.lathe([(0.0, deck_y + 2.5, 1.0), (0.42, deck_y + 2.2, 0.95), (0.3, deck_y + 1.55, 0.7)], 8, jade, centre=(x, 0, -hz + 2.6), cap_top=False)
    return mb.object("JG_Hermitage", coll, mat)


# ---------- Ember Peak ----------
def _hex_points(cx, cz, s):
    return [(cx + math.cos(TAU * k / 6 + TAU / 12) * s, cz + math.sin(TAU * k / 6 + TAU / 12) * s) for k in range(6)]


def ember_floor(coll, mat, bands):
    """Hexagonal column tops (the island's signature, seen from above), each its own height, with lava showing between them (EP_ArenaGlow lies
    under the seams); a kerb of obsidian; a cinnabar sun where the guardian stands."""
    rnd = random.Random(612)
    mb = W.MeshBuilder()
    s = 4.7
    w = math.sqrt(3) * s
    limit = 49.6
    q_max = int(limit / w) + 3
    for q in range(-q_max, q_max + 1):
        for r in range(-q_max, q_max + 1):
            cx = w * (q + r / 2)
            cz = 1.5 * s * r
            d = math.hypot(cx, cz)
            if d > limit + s or d < 7.5:
                continue
            pts = []
            for x, z in _hex_points(cx, cz, s - 0.17):
                pd = math.hypot(x, z)
                if pd > limit:
                    x, z = x * limit / pd, z * limit / pd
                pts.append((x, z))
            # clipped hexagons at the rim can collapse to slivers
            area = abs(sum(pts[i][0] * pts[(i + 1) % 6][1] - pts[(i + 1) % 6][0] * pts[i][1] for i in range(6))) / 2
            if area < 3:
                continue
            P.slab_tile(mb, pts, TOP - rnd.uniform(0, 0.09), BOT, bands[EM.BASALT], rnd.uniform(0.05, 0.95), rnd.uniform(0.85, 1.0))
    kerb(mb, rnd, 49.7, 52.0, 42, bands[EM.OBSIDIAN], shade=(0.7, 0.95))
    # the sun
    disc(mb, 7.6, TOP + 0.02, bands[EM.IRON], seg=48, shade=0.55)
    annulus(mb, 7.2, 8.2, TOP + 0.05, bands[EM.GOLD], seg=48, shade=0.85)
    for k in range(12):
        a = TAU * k / 12
        r1 = 6.9 if k % 2 == 0 else 5.2
        oriented(mb, [(math.cos(a - 0.26) * 2.6, TOP + 0.07, math.sin(a - 0.26) * 2.6), (math.cos(a) * r1, TOP + 0.07, math.sin(a) * r1),
                      (math.cos(a + 0.26) * 2.6, TOP + 0.07, math.sin(a + 0.26) * 2.6)], (0, 1, 0), bands[EM.CINNABAR], 0.5, [1.0] * 3)
    disc(mb, 2.7, TOP + 0.09, bands[EM.CINNABAR], seg=24, shade=1.0)
    return mb.object("EP_ArenaFloor", coll, mat)


def ember_glow(coll, mat, bands):
    """The lava: a sheet under the floor's seams, and a broken ring of fire in a shallow channel round the kerb, gapped where the paths come in."""
    mb = W.MeshBuilder()
    annulus(mb, 7.4, 49.8, TOP - 0.11, bands[EM.GLOW], seg=64)
    gaps = [E.ARRIVAL_BEARING] + [E._bearing_of(p[-1]) for p in E.PATHS[2:]]
    gaps = sorted(math.radians(g % 360) for g in gaps)
    half = math.radians(11)
    for i, g in enumerate(gaps):
        nxt = gaps[(i + 1) % len(gaps)] + (TAU if i == len(gaps) - 1 else 0)
        a0, a1 = g + half, nxt - half
        if a1 > a0:
            annulus(mb, 52.6, 53.8, -0.06, bands[EM.GLOW], seg=max(4, int((a1 - a0) / 0.06)), a_from=a0, a_to=a1)
    return mb.object("EP_ArenaGlow", coll, mat)


def ember_pylon(coll, mat, bands):
    """A bundle of tall basalt columns holding an iron fire bowl high up. EP_PylonFire is its flame."""
    rnd = random.Random(613)
    mb = W.MeshBuilder()
    centre_h = 11.0
    spots = [(0, 0, centre_h)] + [(math.cos(TAU * k / 6 + 0.3) * 1.75, math.sin(TAU * k / 6 + 0.3) * 1.75, rnd.uniform(5.0, 9.6)) for k in range(6)]
    for x, z, h in spots:
        mb.lathe([(0.0, h, 0.95), (1.0, h - 0.05, 0.95), (1.05, h - 0.3, 0.7), (1.05, -1.5, 0.45)], 6, bands[EM.BASALT], centre=(x, 0, z), phase=rnd.uniform(0, 1), u_repeat=0.6, cap_top=False)
    y = centre_h
    mb.lathe([(1.0, y + 1.5, 0.75), (2.2, y + 1.55, 0.9), (2.35, y + 1.25, 0.85), (1.6, y + 0.5, 0.6), (0.9, y - 0.2, 0.45)], 12, bands[EM.IRON], cap_top=True)
    return mb.object("EP_FirePylon", coll, mat)


def ember_pylon_fire(coll, mat, bands):
    mb = W.MeshBuilder()
    y = 12.5
    # tongues, like the braziers' fire but larger
    for dx, dz, h in ((0, 0, 4.6), (0.85, 0.5, 3.0), (-0.8, 0.55, 3.4), (0.1, -0.95, 3.0)):
        mb.lathe([(0.0, y + h, 1.0), (0.85, y + h * 0.4, 0.9), (1.05, y - 0.05, 0.8)], 7, bands[EM.GLOW], centre=(dx, 0, dz),
                 cap_top=False, cap_bottom=True, u_repeat=0.0)
    return mb.object("EP_PylonFire", coll, mat)


# ---------- Moonlit Isle ----------
# star-free spots of the night strip, stars being pale enough to turn a whole slab pale: the band, and the darker moons on it
NIGHT_SPOT = (0.25, (0.84, 0.84))
NIGHT_DARK = (0.25, 0.3)


def moon_floor(coll, mat, bands):
    """A moon dial. Pale marble inside, a band of the night sky round it holding the eight phases in pearl, gold rings, a gold star at the centre."""
    rnd = random.Random(614)
    mb = W.MeshBuilder()
    marble, night, gold, pearl = bands[MM.MARBLE], bands[MM.NIGHT], bands[MM.GOLD], bands[MM.PEARL]
    disc(mb, 49.8, TOP - 0.09, gold, seg=64, shade=0.55)
    ring_slabs(mb, rnd, [(8.5, 17.0, 16), (17.0, 26.0, 24), (26.0, 34.5, 32)], lambda i, k: marble, shade=(0.75, 1.0), gap=0.1, sink=0.03)
    annulus(mb, 34.5, 35.7, TOP - 0.005, gold, seg=64, shade=0.95)
    ring_slabs(mb, rnd, [(35.7, 49.6, 8)], lambda i, k: night, shade=NIGHT_SPOT[1], gap=0.1, sink=0.0, u=NIGHT_SPOT[0])
    kerb(mb, rnd, 49.7, 52.0, 48, marble, shade=(0.85, 1.0))
    annulus(mb, 51.0, 51.5, TOP + 0.135, gold, seg=64, shade=1.0)
    # the eight phases, in the night band
    r_phase, moon_r = 42.6, 4.6
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        cx, cz = math.cos(a) * r_phase, math.sin(a) * r_phase
        disc(mb, moon_r + 0.28, TOP + 0.02, gold, seg=24, shade=0.9, centre=(cx, cz))
        disc(mb, moon_r, TOP + 0.035, night, seg=24, shade=NIGHT_DARK[1], u=NIGHT_DARK[0], centre=(cx, cz))
        lit = (k + 0.5) / 8  # how far round the month: new at 0, full at 0.5
        phase = math.cos(lit * TAU)   # 1 new .. -1 full
        waxing = lit < 0.5
        outer_sign = 1 if waxing else -1
        pts_out, pts_in = [], []
        n = 12
        for i in range(n + 1):
            th = -math.pi / 2 + math.pi * i / n
            ox = math.cos(th) * moon_r * outer_sign
            oz = math.sin(th) * moon_r
            ix = math.cos(th) * moon_r * phase * outer_sign
            pts_out.append((ox, oz))
            pts_in.append((ix, oz))
        ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)

        def at(p):
            return (cx + p[0] * ca - p[1] * sa, TOP + 0.05, cz + p[0] * sa + p[1] * ca)

        for i in range(n):
            oriented(mb, [at(pts_out[i]), at(pts_out[i + 1]), at(pts_in[i + 1]), at(pts_in[i])], (0, 1, 0), pearl, 0.5, [1.0] * 4)
    # the centre: a gold ring, a dark well, a star
    annulus(mb, 7.3, 8.3, TOP + 0.05, gold, seg=48, shade=0.95)
    disc(mb, 7.4, TOP + 0.02, night, seg=48, shade=NIGHT_DARK[1], u=NIGHT_DARK[0])
    for k in range(8):
        a = TAU * k / 8
        r1 = 6.8 if k % 2 == 0 else 3.9
        oriented(mb, [(math.cos(a - 0.3) * 1.3, TOP + 0.07, math.sin(a - 0.3) * 1.3), (math.cos(a) * r1, TOP + 0.07, math.sin(a) * r1),
                      (math.cos(a + 0.3) * 1.3, TOP + 0.07, math.sin(a + 0.3) * 1.3)], (0, 1, 0), gold, 0.5, [1.0] * 3)
    disc(mb, 1.4, TOP + 0.09, pearl, seg=16, shade=1.0)
    return mb.object("MI_ArenaFloor", coll, mat)


def moon_gate(coll, mat, bands):
    """A great moon gate on the lip of the bay, behind the eggs: a porcelain ring banded in gold on a stepped marble plinth, a crescent on its
    crown, the empty sky seen through it. It faces +Z."""
    mb = W.MeshBuilder()
    marble, gold, porcelain, moonstone = bands[MM.MARBLE], bands[MM.GOLD], bands[MM.PORCELAIN], bands[MM.MOONSTONE]
    # the plinth, three broad steps, walkable and open through the ring
    for k, (w, d, y) in enumerate(((30.0, 15.0, 0.3), (24.0, 11.5, 1.05), (19.0, 8.0, 1.75))):
        mb.box((0, y, 0), (w, 0.75, d), marble, u=0.2 + k * 0.2, top_shade=0.95, side_shade=0.62)
        mb.box((0, y - 0.8, 0), (w, 0.85, d), marble, u=0.3, top_shade=0.7, side_shade=0.45)
    base = 2.1
    R, cy = 10.5, base + 12.0
    torus(mb, (0, cy, 0), R, 1.35, porcelain, seg=64, sides=10, shade=0.95)
    torus(mb, (0, cy, 1.05), R, 0.38, gold, seg=64, sides=6, shade=1.0)
    torus(mb, (0, cy, -1.05), R, 0.38, gold, seg=64, sides=6, shade=1.0)
    # its feet: two piers it rises from, either side
    for side in (-1, 1):
        x = side * (R - 0.2)
        mb.box((x, base + 2.2, 0), (3.6, 4.4, 3.6), marble, u=0.6, top_shade=0.95, side_shade=0.66)
        mb.box((x, base + 4.65, 0), (4.2, 0.5, 4.2), gold, u=0.4, top_shade=1.0, side_shade=0.75)
        mb.box((x, base + 0.3, 0), (4.4, 0.6, 4.4), gold, u=0.4, top_shade=0.9, side_shade=0.7)
        # a slender lantern pillar standing out to the side
        px = side * 13.2
        mb.lathe([(0.55, base + 8.6, 0.95), (0.62, base + 0.5, 0.65)], 10, porcelain, centre=(px, 0, 0), cap_top=True)
        mb.lathe([(0.0, base + 10.0, 1.0), (0.85, base + 9.5, 1.0), (0.9, base + 8.9, 0.95), (0.6, base + 8.55, 0.8)], 10, moonstone, centre=(px, 0, 0), cap_top=False)
        mb.lathe([(1.0, base + 0.9, 0.9), (1.1, base + 0.0, 0.7)], 10, gold, centre=(px, 0, 0), cap_top=True)
    # the crescent on its crown, horns up
    top = cy + R + 1.2
    torus(mb, (0, top + 3.4, 0), 3.2, 1.0, gold, seg=28, sides=8, a_from=math.radians(205), a_to=math.radians(335),
          taper=lambda t: 0.22 + 1.05 * math.sin(math.pi * t), shade=1.0)
    return mb.object("MI_MoonGate", coll, mat)


# ---------- Origin Abyss ----------
def origin_floor(coll, mat, bands):
    """A floor of worn temple slabs, heaved and broken, on the court. EP-style seams would read as Ember: here the light is in the cracks
    (OA_ArenaGlow). Kerb of obsidian; a dark seal at the middle."""
    rnd = random.Random(615)
    mb = W.MeshBuilder()
    rings = [(8.6, 15.0, 9), (15.0, 22.5, 13), (22.5, 30.5, 17), (30.5, 40.0, 21), (40.0, 49.6, 26)]
    disc(mb, 49.8, TOP - 0.14, bands[OM.OBSIDIAN], seg=64, shade=0.35)
    ring_slabs(mb, rnd, rings, lambda i, k: bands[OM.RUIN], shade=(0.55, 0.95), gap=0.22, sink=0.12)
    kerb(mb, rnd, 49.7, 52.0, 30, bands[OM.OBSIDIAN], shade=(0.7, 1.0))
    disc(mb, 8.6, TOP + 0.01, bands[OM.OBSIDIAN], seg=48, shade=0.55)
    annulus(mb, 7.6, 8.5, TOP + 0.04, bands[OM.BRONZE], seg=48, shade=0.85)
    return mb.object("OA_ArenaFloor", coll, mat)


def _crack(rnd, a, r0, r1, wander):
    pts = []
    n = max(3, int((r1 - r0) / 3.2))
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * t
        aa = a + rnd.uniform(-wander, wander) * (0 if i == 0 else 1) / max(r, 8) * 8
        pts.append((math.cos(aa) * r, math.sin(aa) * r))
    return pts


def _strip(mb, pts, width, y, band):
    for i in range(len(pts) - 1):
        ax, az = pts[i]
        bx, bz = pts[i + 1]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L, dx / L
        w0 = width * (1 - 0.7 * i / max(1, len(pts) - 1))
        w1 = width * (1 - 0.7 * (i + 1) / max(1, len(pts) - 1))
        oriented(mb, [(ax + nx * w0, y, az + nz * w0), (bx + nx * w1, y, bz + nz * w1), (bx - nx * w1, y, bz - nz * w1), (ax - nx * w0, y, az - nz * w0)],
                 (0, 1, 0), band, 0.5, [1.0] * 4)


def origin_glow(coll, mat, bands):
    """Void light: cracks branching out from the seal to the kerb, and a spiral sigil in the seal."""
    rnd = random.Random(616)
    mb = W.MeshBuilder()
    y = TOP + 0.03
    band = bands[OM.GLOW]
    for k in range(7):
        a = TAU * k / 7 + rnd.uniform(-0.2, 0.2)
        main = _crack(rnd, a, 8.6, rnd.uniform(34, 49), 0.14)
        _strip(mb, main, 0.24, y, band)
        for _ in range(2):  # branches off it
            i = rnd.randrange(1, len(main) - 1)
            bx, bz = main[i]
            ba = math.atan2(bz, bx) + rnd.choice((-1, 1)) * rnd.uniform(0.25, 0.5)
            r0 = math.hypot(bx, bz)
            _strip(mb, [(bx, bz)] + _crack(rnd, ba, r0 + 1.0, min(49.0, r0 + rnd.uniform(5, 11)), 0.1), 0.14, y, band)
    spiral = []
    for i in range(70):
        t = i / 69
        a = t * TAU * 2.6
        r = 0.7 + 6.3 * t
        spiral.append((math.cos(a) * r, math.sin(a) * r))
    y2 = TOP + 0.05
    for i in range(len(spiral) - 1):
        ax, az = spiral[i]
        bx, bz = spiral[i + 1]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L * 0.2, dx / L * 0.2
        oriented(mb, [(ax + nx, y2, az + nz), (bx + nx, y2, bz + nz), (bx - nx, y2, bz - nz), (ax - nx, y2, az - nz)], (0, 1, 0), band, 0.5, [1.0] * 4)
    return mb.object("OA_ArenaGlow", coll, mat)


# how much of each column is left, from the gate's side round to the back: runs still standing under their stone, then rubble
COLONNADE_HEIGHTS = {
    -1: (15.5, 15.5, 4.5, 11.0, 15.5, 15.5, 15.5, 7.5, 4.5),
    1: (7.5, 15.5, 15.5, 11.0, 4.5, 15.5, 15.5, 7.5, 11.0),
}


def _colonnade_bearings():
    """Two arcs round the court's flanks, at island scale, each column kept off the paths."""
    out = []
    for side in (-1, 1):
        for k in range(9):
            bearing = O.ARRIVAL_BEARING + side * (46 + k * 11.5)
            out.append((side, k, bearing))
    return out


def origin_colonnade(coll, mat, bands):
    """What's left of the temple: columns round both flanks of the court at radius 70, some whole and carrying a length of architrave, most
    broken at different heights. Placed at the island's origin: each stands on the ground beneath it."""
    rnd = random.Random(617)
    mb = W.MeshBuilder()
    ruin, obsidian = bands[OM.RUIN], bands[OM.OBSIDIAN]
    R = 70.0
    placed = []
    for side, k, bearing in _colonnade_bearings():
        a = math.radians(bearing)
        x, z = math.cos(a) * R, math.sin(a) * R
        if O.path_distance(x, z) < 6.5 or O.edge_distance(x, z) < 6:
            placed.append(None)
            continue
        g = O.height(x, z)[0]
        if g is None:
            placed.append(None)
            continue
        h = COLONNADE_HEIGHTS[side][k]
        placed.append((x, z, g, h, side))
        column(mb, x, z, g, g + h, 1.45, ruin, seg=8, flutes=True, foot=ruin)
        if h >= 15:
            mb.lathe([(2.05, g + h + 0.8, 0.85), (2.05, g + h + 0.1, 0.65), (1.5, g + h - 0.5, 0.55)], 8, ruin, centre=(x, 0, z), cap_top=True)
        else:  # a jagged break, with a shard of darker stone showing inside
            mb.lathe([(0.0, g + h + 0.75, 0.5), (0.9, g + h + 0.1, 0.45)], 5, obsidian, centre=(x, 0, z), cap_top=False)
    # architrave on neighbours both standing whole
    for a_, b_ in zip(placed, placed[1:]):
        if a_ and b_ and a_[3] >= 15 and b_[3] >= 15 and a_[4] == b_[4]:
            mx, mz = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
            dx, dz = b_[0] - a_[0], b_[1] - a_[1]
            L = math.hypot(dx, dz)
            yaw = math.atan2(-dz, dx)
            y = max(a_[2], b_[2]) + 15.5 + 1.5
            mb.box((mx, y, mz), (L + 3.4, 1.5, 2.6), ruin, yaw=yaw, u=rnd.uniform(0.1, 0.9), top_shade=0.8, side_shade=0.6)
    return mb.object("OA_Colonnade", coll, mat)


# ---------- paved ground that follows the land (the hub and the Beginner Isle) ----------
ROAD_LIFT = 0.24        # above the ground, under a road's whole width
ROAD_TILE = 5.0         # studs along a road per row of flagstones


def _resample(line, step):
    """A polyline's points every `step` studs, with the corners kept, so curves stay curves."""
    out = [line[0]]
    for a, b in zip(line, line[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, round(L / step))
        for i in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return out


def _line_distance(x, z, line):
    best = 1e9
    for a, b in zip(line, line[1:]):
        vx, vz = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * vx + (z - a[1]) * vz) / max(vx * vx + vz * vz, 1e-6)))
        best = min(best, math.hypot(x - a[0] - vx * t, z - a[1] - vz * t))
    return best


def road(mb, rnd, line, half, ground, stone, edge, others=(), covered=None, lift=ROAD_LIFT, shade=(0.55, 0.86)):
    """One road: rows of two flagstones with a dark kerb each side, every corner on the ground beneath it. A kerb is left out
    where it would cross another road (`others`, (line, half)) or a plaza (`covered(x, z)`), so junctions read as one surface."""
    points = _resample(line, ROAD_TILE)
    closed = math.hypot(points[0][0] - points[-1][0], points[0][1] - points[-1][1]) < 0.01
    frames = []
    count = len(points)
    for i, (x, z) in enumerate(points):
        if closed:
            ax, az = points[(i - 1) % (count - 1)]
            bx, bz = points[(i + 1) % (count - 1)]
        else:
            ax, az = points[max(0, i - 1)]
            bx, bz = points[min(count - 1, i + 1)]
        dx, dz = bx - ax, bz - az
        L = max(math.hypot(dx, dz), 1e-6)
        frames.append((x, z, -dz / L, dx / L))

    def at(frame, across, dy=0.0):
        x, z, nx, nz = frame
        px, pz = x + nx * across, z + nz * across
        return (px, ground(px, pz) + lift + dy, pz)

    def clear(frame, across):
        x, z, nx, nz = frame
        px, pz = x + nx * across, z + nz * across
        if covered and covered(px, pz):
            return False
        return all(_line_distance(px, pz, ol) > oh - 0.5 for ol, oh in others)

    kerb_width = 1.1
    for a, b in zip(frames, frames[1:]):
        for s0, s1 in ((-half + kerb_width, -0.06), (0.06, half - kerb_width)):
            sh = rnd.uniform(*shade)
            oriented(mb, [at(a, s0), at(b, s0), at(b, s1), at(a, s1)], (0, 1, 0), stone, rnd.uniform(0.1, 0.9), [sh] * 4)
        for side in (-1, 1):
            if clear(a, side * (half - 0.5)) and clear(b, side * (half - 0.5)):
                sh = rnd.uniform(0.45, 0.7)
                inner0, inner1 = at(a, side * (half - kerb_width), 0.07), at(b, side * (half - kerb_width), 0.07)
                outer0, outer1 = at(a, side * half, 0.07), at(b, side * half, 0.07)
                oriented(mb, [inner0, inner1, outer1, outer0], (0, 1, 0), edge, 0.5, [sh] * 4)
                drop0, drop1 = (outer0[0], outer0[1] - 0.9, outer0[2]), (outer1[0], outer1[1] - 0.9, outer1[2])
                oriented(mb, [outer0, outer1, drop1, drop0], (a[2] * side, 0, a[3] * side), edge, 0.5, [sh * 0.7] * 4)


def paved_disc(mb, rnd, centre, r0, r1, rings, ground, stone, edge, kerb=1.4, lift=0.2, shade=(0.55, 0.86), covered=None):
    """Rings of flagstones from r0 out to r1, then a dark kerb, on the ground beneath. `rings`: stones in each ring."""
    cx, cz = centre
    span = (r1 - kerb - r0) / len(rings)

    def at(a, r, dy=0.0):
        x, z = cx + math.cos(a) * r, cz + math.sin(a) * r
        return (x, ground(x, z) + lift + dy, z)

    for i, n in enumerate(rings):
        ra, rb = r0 + i * span + 0.07, r0 + (i + 1) * span - 0.07
        phase = rnd.uniform(0, TAU)
        steps = max(1, round(TAU * rb / n / 4))
        for k in range(n):
            a0, a1 = phase + TAU * k / n, phase + TAU * (k + 1) / n
            da = 0.08 / rb
            sh = rnd.uniform(*shade)
            u = rnd.uniform(0.1, 0.9)
            for s in range(steps):
                b0 = a0 + da + (a1 - a0 - 2 * da) * s / steps
                b1 = a0 + da + (a1 - a0 - 2 * da) * (s + 1) / steps
                oriented(mb, [at(b0, ra), at(b1, ra), at(b1, rb), at(b0, rb)], (0, 1, 0), stone, u, [sh] * 4)
    n = max(12, round(TAU * r1 / 5))
    for k in range(n):
        a0, a1 = TAU * k / n + 0.004, TAU * (k + 1) / n - 0.004
        mid = (a0 + a1) / 2
        if covered and covered(cx + math.cos(mid) * (r1 - 0.6), cz + math.sin(mid) * (r1 - 0.6)):
            continue
        sh = rnd.uniform(0.45, 0.7)
        oriented(mb, [at(a0, r1 - kerb, 0.08), at(a1, r1 - kerb, 0.08), at(a1, r1, 0.08), at(a0, r1, 0.08)], (0, 1, 0), edge, 0.5, [sh] * 4)
        o0, o1 = at(a0, r1, 0.08), at(a1, r1, 0.08)
        oriented(mb, [o0, o1, (o1[0], o1[1] - 0.9, o1[2]), (o0[0], o0[1] - 0.9, o0[2])], (math.cos(mid), 0, math.sin(mid)), edge, 0.5, [sh * 0.7] * 4)


# ---------- Yggdrasil ----------
def _hub_roads():
    """(line, half width) of every road on the hub, the Root Court's ring first."""
    import ygg_island as Y
    return [(line, 8.0 if k == 0 else 7.0) for k, line in enumerate(Y.PATHS)]


def _hub_plaza(x, z):
    """On the hub's other paving: the Qi Compass, a bridgehead."""
    import ygg_island as Y
    if math.hypot(x - Y.COMPASS[0], z - Y.COMPASS[1]) < Y.COMPASS[2] + 4:
        return True
    return any(math.hypot(x - bx, z - bz) < Y.BRIDGEHEAD_R + 2 for bx, bz in hub_bridgehead_centres())


def hub_bridgehead_centres():
    import ygg_island as Y
    out = []
    for x, z in Y.EXITS.values():
        r = math.hypot(x, z)
        out.append((x * (r - 10) / r, z * (r - 10) / r))
    return out


def hub_roads(coll, mat, bands):
    """The hub's paths as paved roads, instead of the blurred earth the 4-stud terrain gives: the Root Court's ring, the Spawn Walk,
    the Market lane, the way to each bridge. Decoration on the ground, like the Lion Court."""
    import ygg_island as Y
    rnd = random.Random(631)
    mb = W.MeshBuilder()
    ground = lambda x, z: Y.height(x, z)[0] or 0.0
    roads = _hub_roads()
    for k, (line, half) in enumerate(roads):
        others = [r for j, r in enumerate(roads) if j != k]
        road(mb, rnd, line, half, ground, bands[P.PALE], bands[P.DARK], others=others, covered=_hub_plaza, lift=ROAD_LIFT + 0.012 * k)
    return mb.object("YG_Roads", coll, mat)


def hub_bridgeheads(coll, mat, bands):
    """A crisp paved round where each bridge lands, in place of its jagged terrain edge."""
    import ygg_island as Y
    rnd = random.Random(632)
    mb = W.MeshBuilder()
    ground = lambda x, z: Y.height(x, z)[0] or 0.0
    for centre in hub_bridgehead_centres():
        paved_disc(mb, rnd, centre, 0.0, Y.BRIDGEHEAD_R + 3, (10, 18, 26), ground, bands[P.PALE], bands[P.DARK], lift=0.34)
    return mb.object("YG_Bridgeheads", coll, mat)


def hub_plot_edges(coll, mat, bands):
    """A kerbed band round each building's plot, over the jagged edge of its terrain paving; what's inside is left to the building."""
    import ygg_island as Y
    rnd = random.Random(633)
    mb = W.MeshBuilder()
    ground = lambda x, z: Y.height(x, z)[0] or 0.0
    roads = _hub_roads()
    for plot in Y.PLOTS.values():
        cx, cz, w, d, facing = plot
        a = math.radians(facing)
        fx, fz = math.cos(a), math.sin(a)      # out of its front
        sx, sz = -fz, fx                       # along the front

        layer = [0.0]   # each side a hair over the last, where they share a corner

        def at(u, v, dy=0.0):
            x, z = cx + sx * u + fx * v, cz + sz * u + fz * v
            return (x, ground(x, z) + 0.26 + layer[0] + dy, z)

        out, width = 2.5, 3.6
        hu, hv = w / 2, d / 2
        corners = [(-hu, -hv), (hu, -hv), (hu, hv), (-hu, hv)]
        for i in range(4):
            layer[0] = 0.012 * i
            (u0, v0), (u1, v1) = corners[i], corners[(i + 1) % 4]
            du, dv = (1 if u1 > u0 else -1 if u1 < u0 else 0), (1 if v1 > v0 else -1 if v1 < v0 else 0)
            nu, nv = dv, -du                    # outward, going round this way
            L = math.hypot(u1 - u0, v1 - v0) + 2 * out
            n = max(1, round(L / 4.0))
            su, sv = u0 - du * out, v0 - dv * out
            for k in range(n):
                t0, t1 = L * k / n + 0.05, L * (k + 1) / n - 0.05
                a0 = (su + du * t0, sv + dv * t0)
                a1 = (su + du * t1, sv + dv * t1)
                # where a road runs over this edge, the road wins
                mid = ((a0[0] + a1[0]) / 2 + nu * (out - 1.5), (a0[1] + a1[1]) / 2 + nv * (out - 1.5))
                mx, mz = cx + sx * mid[0] + fx * mid[1], cz + sz * mid[0] + fz * mid[1]
                if any(_line_distance(mx, mz, line) < half + 1.5 for line, half in roads):
                    continue
                inner = out - width
                sh = rnd.uniform(0.55, 0.86)
                oriented(mb, [at(a0[0] + nu * inner, a0[1] + nv * inner), at(a1[0] + nu * inner, a1[1] + nv * inner),
                              at(a1[0] + nu * (out - 1.0), a1[1] + nv * (out - 1.0)), at(a0[0] + nu * (out - 1.0), a0[1] + nv * (out - 1.0))],
                         (0, 1, 0), bands[P.PALE], rnd.uniform(0.1, 0.9), [sh] * 4)
                sh = rnd.uniform(0.45, 0.7)
                p0, p1 = at(a0[0] + nu * out, a0[1] + nv * out, 0.07), at(a1[0] + nu * out, a1[1] + nv * out, 0.07)
                oriented(mb, [at(a0[0] + nu * (out - 1.0), a0[1] + nv * (out - 1.0), 0.07), at(a1[0] + nu * (out - 1.0), a1[1] + nv * (out - 1.0), 0.07), p1, p0],
                         (0, 1, 0), bands[P.DARK], 0.5, [sh] * 4)
                wx, wz = sx * nu + fx * nv, sz * nu + fz * nv
                oriented(mb, [p0, p1, (p1[0], p1[1] - 0.9, p1[2]), (p0[0], p0[1] - 0.9, p0[2])], (wx, 0, wz), bands[P.DARK], 0.5, [sh * 0.7] * 4)
    return mb.object("YG_PlotEdges", coll, mat)


def hub_compass_ring(coll, mat, bands):
    """A paved ring round the Qi Compass, over its terrain paving's jagged edge."""
    import ygg_island as Y
    rnd = random.Random(634)
    mb = W.MeshBuilder()
    ground = lambda x, z: Y.height(x, z)[0] or 0.0
    cx, cz, r = Y.COMPASS
    paved_disc(mb, rnd, (cx, cz), r - 1.0, r + 4.2, (20,), ground, bands[P.PALE], bands[P.DARK], lift=0.2)
    return mb.object("YG_CompassRing", coll, mat)


# ---------- the Beginner Isle: its layout stays; its edges go from blurred to crisp ----------
def beginner_court(coll, mat, bands):
    import beginner_props as BP
    return BP.court_paving(coll, mat, bands)


def _beginner_ground(x, z):
    import beginner_island as B
    return B.height(x, z)[0] or 0.0


APRON_R = 67.5   # the paved round the Lion Court, out over its path


def beginner_apron(coll, mat, bands):
    """Two rings of darker flagstones outside the court's kerb, where the terrain's path made a blurred star."""
    rnd = random.Random(635)
    mb = W.MeshBuilder()
    paved_disc(mb, rnd, (0.0, 0.0), 52.0, APRON_R, (54, 62), _beginner_ground, bands[P.PALE], bands[P.DARK], lift=0.1, shade=(0.42, 0.62))
    return mb.object("BI_CourtApron", coll, mat)


def _beginner_yard_cover(x, z):
    import beginner_island as B
    return math.hypot(x, z) < APRON_R - 0.5 or math.hypot(x - B.YARD[0], z - B.YARD[1]) < B.YARD_R + 3


def beginner_roads(coll, mat, bands):
    """The ways off the court: to the gate, the Hall, the yard, the pavilion and the bell."""
    import beginner_island as B
    rnd = random.Random(636)
    mb = W.MeshBuilder()
    lines = [line for k, line in enumerate(B.PATHS) if k != 1]   # 1 is the ring, which the apron covers
    bearing = math.degrees(math.atan2(B.PAVILION[1], B.PAVILION[0]))
    pavilion_end = B.polar(bearing, 92 - B.PAVILION_R)
    # the pavilion's road stops at the foot of its knoll: the steps take over (beginner_pavilion_steps)
    lines = [[line[0], B.polar(bearing, STEPS_FOOT + 0.8)] if math.dist(line[-1], pavilion_end) < 0.01 else line for line in lines]
    for k, line in enumerate(lines):
        road(mb, rnd, line, 6.5, _beginner_ground, bands[P.PALE], bands[P.DARK], covered=_beginner_yard_cover,
             lift=0.2 + 0.01 * k, shade=(0.42, 0.62))
    return mb.object("BI_Roads", coll, mat)


STEPS_FOOT = 71.0       # where the pavilion's steps start, out from the court's centre
STEPS_TREADS = 8
STEPS_RUN = 1.5         # studs of each tread, and the rise (the knoll's top, 3 studs up, in eight): a character walks up without a hitch
STEPS_RISE = 0.39
STEPS_WIDTH = 11.0


def beginner_pavilion_steps(coll, mat, bands):
    """Stone steps up the pavilion's knoll, from the road's end to the pavilion's own front step, between dark cheek walls that
    step with them and end in a low post each side at the foot. Solid, down into the ground. It collides: it's walked on."""
    import beginner_island as B
    rnd = random.Random(638)
    mb = W.MeshBuilder()
    bearing = math.radians(math.degrees(math.atan2(B.PAVILION[1], B.PAVILION[0])))
    dx, dz = math.cos(bearing), math.sin(bearing)
    sx, sz = -dz, dx
    yaw = math.atan2(-dz, dx)   # a box's local x runs up the steps
    base = -1.6

    def block(along, across, top, run, width, band, top_shade, side_shade=0.55, u=None):
        r = STEPS_FOOT + along
        x, z = dx * r + sx * across, dz * r + sz * across
        mb.box((x, (top + base) / 2, z), (run, top - base, width), band, yaw=yaw, u=rnd.uniform(0.1, 0.9) if u is None else u,
               top_shade=top_shade, side_shade=side_shade)

    pale, dark, bronze = bands[P.PALE], bands[P.DARK], bands[P.BRONZE]
    for k in range(STEPS_TREADS):
        top = STEPS_RISE * (k + 1)
        run = STEPS_RUN + (0.0 if k < STEPS_TREADS - 1 else 1.0)     # the last one is a little landing, up to the pavilion's step
        block(STEPS_RUN * k + run / 2, 0.0, top, run + 0.02, STEPS_WIDTH, pale, rnd.uniform(0.78, 0.92))
        for side in (-1, 1):
            block(STEPS_RUN * k + run / 2, side * (STEPS_WIDTH / 2 + 0.55), top + 0.32, run + 0.02, 1.1, dark, rnd.uniform(0.55, 0.7), side_shade=0.45)
    # a low post each side at the foot, with a bronze cap
    for side in (-1, 1):
        x_along, across = 0.0, side * (STEPS_WIDTH / 2 + 0.55)
        block(x_along, across, 1.7, 1.7, 1.7, dark, 0.65, side_shade=0.5)
        block(x_along, across, 1.95, 1.2, 1.2, bronze, 0.95, side_shade=0.7)
    return mb.object("BI_PavilionSteps", coll, mat)


def beginner_yard(coll, mat, bands):
    """The training yard's floor: pale raked rings in a stone kerb, where the bare earth had a blurred edge."""
    import beginner_island as B
    rnd = random.Random(637)
    mb = W.MeshBuilder()
    paved_disc(mb, rnd, tuple(B.YARD[:2]), 0.0, B.YARD_R + 3.0, (8, 16, 24, 32), _beginner_ground, bands[P.PALE], bands[P.DARK], lift=0.14, shade=(0.3, 0.42))
    return mb.object("BI_YardFloor", coll, mat)


# ---------- the batches, one atlas each ----------
ISLANDS = {
    "JadeGrove": ("JadeGrove_Atlas", JM.STRIPS, [jade_floor, jade_hermitage]),
    "EmberPeak": ("EmberPeak_Atlas", EM.STRIPS, [ember_floor, ember_glow, ember_pylon, ember_pylon_fire]),
    "MoonlitIsle": ("MoonlitIsle_Atlas", MM.STRIPS, [moon_floor, moon_gate]),
    "OriginAbyss": ("OriginAbyss_Atlas", OM.STRIPS, [origin_floor, origin_glow, origin_colonnade]),
    "Yggdrasil": ("StartingIsland_PropAtlas", P.STRIPS, [hub_roads, hub_bridgeheads, hub_plot_edges, hub_compass_ring]),
    "BeginnerIsle": ("StartingIsland_PropAtlas", P.STRIPS, [beginner_court, beginner_apron, beginner_roads, beginner_yard, beginner_pavilion_steps]),
}


def build(island):
    """Builds one island's new pieces on its atlas; returns the objects."""
    atlas, strips, pieces = ISLANDS[island]
    img, bands = W.atlas_image(atlas, 512, strips)
    mat = W.textured_material(island + "_UpgradeMat", img)
    coll = W.collection("Upgrade_" + island)
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in pieces]


def export():
    """assets/world/IslandUpgrades.fbx: every new piece at the origin, UV'd on its island's atlas, with no textures of its own."""
    objs = []
    plain = bpy.data.materials.new("IslandUpgrade")
    for island in ISLANDS:
        for o in build(island):
            o.data.materials.clear()
            o.data.materials.append(plain)
            objs.append(o)
    W.export_batch(objs, W.REPO + "/assets/world/IslandUpgrades.fbx", anchor_name="IU_Anchor")
    return objs

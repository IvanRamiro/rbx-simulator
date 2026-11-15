"""The hub's redesign (2026-11-15; layout approved by the owner: "PROCEED WITH THAT LAYOUT"): the Merchants' Terrace's three shops,
the Market Square's centrepiece, the Leaderboard, the Hidden (Wandering) Merchant's dais, the spawn pads and the new plinths under the
Hatching Sanctum and the Qi Spring. Plan: renders/hub_redesign/LAYOUT_PLAN.md.

The celestial city's language (hub_celestial.py): white marble, lapis, gold and glowing sky-blue crystal; heavy, layered, bevelled
forms; no Chinese forms (no pagodas, curved tiled roofs, paifang, lanterns or motifs). Each building says what it is from across the
hub: the Market is a long open colonnade under a crystal dome, its counters set with eggs; the Blacksmith is a heavy vaulted hall in
front of a tall furnace tower with a burning crown; Buy & Sell is a gold-domed vault with a great balance on top.

Every piece is authored in Roblox studs at its own origin on y = 0, its front toward +Z (a shop's toward the Market Square). Names
keep the game's: WorldBuilder.Shops (HB_Blacksmith, HB_BlacksmithCore, HB_BlacksmithCrystal; HB_Market, HB_MarketCanopy,
HB_MarketGlow; HB_BuySell, HB_BuySellStones), WorldBuilder.Board (HB_Leaderboard, HB_LeaderboardGlow), so the builders, the
collision rules and the looks stay as they are; the new pieces (HB_MerchantDais, HB_SpawnPad, HB_SanctumPlinth, HB_SpringPlinth,
HB_SquareCompass and their glows) need entries of their own (LAYOUT_PLAN.md, phase 3).

The finish pass (finish()): each piece is split by material (<piece>__Marble, __Gold, __Lapis, ...; WorldBuilder.MaterialLooks
gives each a Roblox material, so nothing is uploaded), its square edges bevelled, cut on an 8-stud grid and given box-projected UVs
inside each cell (the Roblox material tiles once per 8 studs; no UV leaves 0-1), n-gons triangulated, smoothed by angle with
weighted normals.

    blender -b --factory-startup -P tools/blender/world/hub_district_run.py -- <stage>     (stages: build, qa, review, export)
"""
import math

import bpy
import bmesh

import worldlib as W
import hub_celestial as H

TAU = 2 * math.pi
B = None    # the atlas bands (set by build())

# ---------- shared helpers ----------


def bx(mb, band, c, s, yaw=0.0, top=0.95, side=0.72, bottom=False):
    mb.box(c, s, B[band], yaw=yaw, u=0.5, top_shade=top, side_shade=side, bottom=bottom)


def quad(mb, pts, normal, band, shade=0.8):
    H.W_oriented(mb, pts, normal, B[band], shade)


def rect_frame(mb, band, cx, cz, w, d, width, y_top, h, yaw=0.0):
    """A flat frame (a gold nosing): its top (y_top), outer and inner faces, round a w x d rectangle; it hangs h down."""
    cs, sn = math.cos(yaw), math.sin(yaw)

    def p(x, y, z):
        return (cx + x * cs + z * sn, y, cz - x * sn + z * cs)
    o = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    i = [(-w / 2 + width, -d / 2 + width), (w / 2 - width, -d / 2 + width), (w / 2 - width, d / 2 - width), (-w / 2 + width, d / 2 - width)]
    for k in range(4):
        j = (k + 1) % 4
        quad(mb, [p(o[k][0], y_top, o[k][1]), p(o[j][0], y_top, o[j][1]), p(i[j][0], y_top, i[j][1]), p(i[k][0], y_top, i[k][1])],
             (0, 1, 0), band, 0.95)
        mx, mz = (o[k][0] + o[j][0]) / 2, (o[k][1] + o[j][1]) / 2
        n = (mx * cs + mz * sn, 0, -mx * sn + mz * cs)
        quad(mb, [p(o[k][0], y_top, o[k][1]), p(o[j][0], y_top, o[j][1]), p(o[j][0], y_top - h, o[j][1]), p(o[k][0], y_top - h, o[k][1])], n, band, 0.8)
        quad(mb, [p(i[k][0], y_top, i[k][1]), p(i[j][0], y_top, i[j][1]), p(i[j][0], y_top - h, i[j][1]), p(i[k][0], y_top - h, i[k][1])],
             (-n[0], 0, -n[2]), band, 0.7)


def podium(mb, w, d, steps=2, rise=0.6, inset=1.2, sink=0.5):
    """Stacked marble steps, each with a gold nosing round its top edge. Returns the top floor's y."""
    for k in range(steps):
        sw, sd = w - 2 * inset * k, d - 2 * inset * k
        y0, y1 = (-sink if k == 0 else rise * k - 0.3), rise * (k + 1)
        bx(mb, H.MARBLE, (0, (y0 + y1) / 2, 0), (sw, y1 - y0, sd))
        rect_frame(mb, H.GOLD, 0, 0, sw + 0.1, sd + 0.1, 0.32, y1 + 0.04, 0.3)
    return rise * steps


def annulus(mb, band, r0, r1, y0, y1, seg=64, centre=(0.0, 0.0), top=0.95, side=0.7, phase=0.0):
    """A solid ring (r0 = 0: a disc): its outer wall, inner wall and top."""
    cx, cz = centre
    if r0 <= 0:
        mb.lathe([(r1, y1, top), (r1, y0, side)], seg, B[band], centre=(cx, 0, cz), cap_top=True, phase=phase)
        return
    mb.lathe([(r1, y1, top), (r1, y0, side)], seg, B[band], centre=(cx, 0, cz), cap_top=False, phase=phase)
    mb.lathe([(r0, y0, side), (r0, y1, top)], seg, B[band], centre=(cx, 0, cz), cap_top=False, phase=phase)
    H.ring(mb, r0, r1, y1, B[band], seg=seg, shade=top, centre=centre)


def round_podium(mb, radii, rise=0.6, sink=0.5, seg=72):
    """Round marble steps, each gold-edged. Returns the top's y."""
    for k, r in enumerate(radii):
        y0, y1 = (-sink if k == 0 else rise * k - 0.3), rise * (k + 1)
        annulus(mb, H.MARBLE, 0.0, r, y0, y1, seg=seg)
        annulus(mb, H.GOLD, r - 0.32, r + 0.05, y1 - 0.26, y1 + 0.04, seg=seg)
    return rise * len(radii)


def arch_band(mb, band, cx, cy, r_in, r_out, z0, z1, a0=0.0, a1=math.pi, seg=16, scale_y=1.0):
    """A curved solid band in the XY plane (an arch's ring of voussoirs), from depth z0 to z1."""
    pts = [(a0 + (a1 - a0) * k / seg) for k in range(seg + 1)]

    def at(a, r, z):
        return (cx + math.cos(a) * r, cy + math.sin(a) * r * scale_y, z)
    for a, b in zip(pts, pts[1:]):
        m = (a + b) / 2
        quad(mb, [at(a, r_out, z0), at(b, r_out, z0), at(b, r_out, z1), at(a, r_out, z1)], (math.cos(m), math.sin(m), 0), band, 0.9)
        quad(mb, [at(a, r_in, z0), at(b, r_in, z0), at(b, r_in, z1), at(a, r_in, z1)], (-math.cos(m), -math.sin(m), 0), band, 0.65)
        quad(mb, [at(a, r_in, z1), at(b, r_in, z1), at(b, r_out, z1), at(a, r_out, z1)], (0, 0, 1), band, 0.85)
        quad(mb, [at(a, r_in, z0), at(b, r_in, z0), at(b, r_out, z0), at(a, r_out, z0)], (0, 0, -1), band, 0.75)


def arched_wall(mb, band, x0, x1, y0, y_top, z0, z1, ocx, half, spring, seg=18):
    """A wall from x0 to x1 (y0..y_top, z0..z1, front face +Z) with a round-headed opening centred at ocx, half wide, its arch
    springing at `spring`: two piers, the spandrel over the arch, the soffit."""
    bx(mb, band, ((x0 + ocx - half) / 2, (y0 + y_top) / 2, (z0 + z1) / 2), (ocx - half - x0, y_top - y0, z1 - z0))
    bx(mb, band, ((x1 + ocx + half) / 2, (y0 + y_top) / 2, (z0 + z1) / 2), (x1 - ocx - half, y_top - y0, z1 - z0))
    angles = [math.pi * k / seg for k in range(seg + 1)]
    corner = math.atan2(y_top - spring, half)
    angles = sorted(set(angles + [corner, math.pi - corner]))

    def edge(a):    # where the ray from the arch's centre meets the opening's bounding rectangle
        c, s = math.cos(a), math.sin(a)
        t = min(half / abs(c) if abs(c) > 1e-6 else 1e9, (y_top - spring) / s if s > 1e-6 else 1e9)
        return (ocx + c * t, spring + s * t)
    for a, b in zip(angles, angles[1:]):
        pa = (ocx + math.cos(a) * half, spring + math.sin(a) * half)
        pb = (ocx + math.cos(b) * half, spring + math.sin(b) * half)
        qa, qb = edge(a), edge(b)
        for z, n in ((z1, 1), (z0, -1)):
            quad(mb, [(pa[0], pa[1], z), (pb[0], pb[1], z), (qb[0], qb[1], z), (qa[0], qa[1], z)], (0, 0, n), band, 0.85 if n > 0 else 0.7)
        m = (a + b) / 2
        quad(mb, [(pa[0], pa[1], z0), (pb[0], pb[1], z0), (pb[0], pb[1], z1), (pa[0], pa[1], z1)], (-math.cos(m), -math.sin(m), 0), band, 0.6)
    # the spandrel's top, level with the piers'
    quad(mb, [(ocx - half, y_top, z0), (ocx + half, y_top, z0), (ocx + half, y_top, z1), (ocx - half, y_top, z1)], (0, 1, 0), band, 0.95)


def tube(mb, pts, r, band, sides=8, shade=0.9, caps=True):
    """A tube along pts (Roblox studs), every face wound outward (hub_celestial.tube's winding flips with direction)."""
    from mathutils import Vector
    P = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 1, 0)))
        if side.length < 1e-4:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        up = side.cross(t).normalized()
        rr = r(i / (len(P) - 1)) if callable(r) else r
        rings.append([p + (side * math.cos(TAU * k / sides) + up * math.sin(TAU * k / sides)) * rr for k in range(sides)])
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            q = [rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]]
            mid = (P[i] + P[i + 1]) / 2
            out = sum(q, Vector()) / 4 - mid
            H.W_oriented(mb, [tuple(v) for v in q], tuple(out), band, shade)
    if caps:
        t0 = (P[0] - P[1]).normalized()
        t1 = (P[-1] - P[-2]).normalized()
        for ring_, c, n in ((rings[0], P[0], t0), (rings[-1], P[-1], t1)):
            for k in range(sides):
                H.W_oriented(mb, [tuple(c), tuple(ring_[k]), tuple(ring_[(k + 1) % sides])], tuple(n), band, shade)


def egg(mb, band, c, r):
    H.egg_shape(mb, c, r, B[band], seg=14)


def stand(mb, c, h, r=0.55):
    """A gold egg stand: a foot, a stem, a cup; returns the cup's top (where an egg sits)."""
    x, y, z = c
    mb.lathe([(r * 1.3, y + 0.22, 1.0), (r * 1.4, y - 0.05, 0.75)], 12, B[H.GOLD], centre=(x, 0, z), cap_top=True)
    mb.lathe([(0.12, y + h - 0.25, 0.95), (0.16, y + 0.2, 0.8)], 8, B[H.GOLD], centre=(x, 0, z), cap_top=False)
    mb.lathe([(r, y + h, 1.0), (r * 0.6, y + h - 0.12, 0.9), (0.18, y + h - 0.32, 0.8)], 12, B[H.GOLD], centre=(x, 0, z), cap_top=True)
    return y + h


def sign_panel(mb, cx, cy, z_face, w, h):
    """A name board on a wall whose face is at z_face: a gold frame sunk 0.12 into the wall, a lapis face proud of it. Returns the
    centre the game's text panel takes (WorldBuilder textPanel: a SurfaceGui on the face looking +Z)."""
    bx(mb, H.GOLD, (cx, cy, z_face + 0.08), (w + 0.8, h + 0.7, 0.4))
    bx(mb, H.LAPIS, (cx, cy, z_face + 0.3), (w, h, 0.12))
    return (cx, cy, round(z_face + 0.36 + 0.03, 3))


def finial(mb, x, y, z, h=1.2):
    """A small gold cap (a fluted bell on a collar) whose top is at y + h."""
    mb.lathe([(0.15, y + h, 1.0), (0.55, y + h * 0.55, 0.95), (0.45, y + 0.2, 0.85), (0.7, y, 0.8)], 12, B[H.GOLD], centre=(x, 0, z), cap_top=True)


# ======================================================================================================================
# The Market (the Crystal Market): an open colonnade under a crystal dome; counters set with eggs
# ======================================================================================================================
MK_W, MK_D = 48.0, 40.0
MK_FLOOR = 1.2
MK_COL_Z, MK_COL_TOP = 13.6, 13.4
MK_COLS = (-19.6, -11.8, -4.4, 4.4, 11.8, 19.6)
MK_BEAM = (13.4, 15.0, 12.0, 15.2)          # the architrave: y0, y1, z0, z1
MK_ROOF = (15.0, 16.2)
MK_DOME = (0.0, -2.0, 7.2, 16.1, 19.2, 26.0)  # x, z, radius, drum foot, drum top, apex
MK_COUNTER = (0.0, 0.2)                      # the central counter's centre (x, z); its front at z + 1.2
MK_SIGN_SIZE = (12.0, 1.5)
MK_PROMPT = (0.0, 2.6, 4.6)
MK_CURATOR = (0.0, MK_FLOOR, -2.6)
MK_FX = (0.0, 6.6, 0.2)


def market():
    mb, canopy, glow = W.MeshBuilder(), W.MeshBuilder(), W.MeshBuilder()
    floor = podium(mb, MK_W, MK_D)
    # a lapis runner from the front steps to the counter, gold edged
    bx(mb, H.LAPIS, (0, floor + 0.02, 9.4), (5.6, 0.12, 12.4))
    rect_frame(mb, H.GOLD, 0, 9.4, 6.2, 13.0, 0.3, floor + 0.09, 0.14)
    # the back wall, its three lapis niches and the side walls
    bx(mb, H.MARBLE, (0, (floor + MK_COL_TOP) / 2 - 0.02, -17.3), (42.8, MK_COL_TOP - floor + 0.1, 1.8))
    for x in (-12.0, 0.0, 12.0):
        bx(mb, H.LAPIS, (x, 7.4, -16.36), (7.0, 8.4, 0.2))
        rect_frame_v(mb, H.GOLD, x, 7.4, -16.3, 7.0, 8.4, 0.35, 0.22)
        top = stand(mb, (x, 3.4, -15.2), 2.2, r=0.75)
        egg(glow, H.GLOW, (x, top + 1.105 * 0.8 - 0.1, -15.2), 0.8)
        bx(mb, H.MARBLE, (x, 3.1, -15.4), (2.6, 0.6, 1.8))        # the stand's marble shelf, out of the wall
    for side in (-1, 1):
        bx(mb, H.MARBLE, (side * 20.7, (floor + MK_COL_TOP) / 2 - 0.02, -6.7), (1.8, MK_COL_TOP - floor + 0.1, 19.4))   # (butting the back wall)
        bx(mb, H.LAPIS, (side * 21.66, 7.6, -7.2), (0.2, 7.0, 14.0))     # the lapis panel on its outer face
        rect_frame_v(mb, H.GOLD, -7.2, 7.6, side * 21.6, 14.0, 7.0, 0.35, 0.22, axis="x", sign=side)
    # the colonnade: six columns in front, one more each side
    H.MARBLE_BAND, H.GOLD_BAND = B[H.MARBLE], B[H.GOLD]
    for x in MK_COLS:
        H.column(mb, x, MK_COL_Z, floor - 0.05, MK_COL_TOP, r=0.85)
    for side in (-1, 1):
        H.column(mb, side * 19.6, 4.6, floor - 0.05, MK_COL_TOP, r=0.85)
    # the architrave along the front and down each side, its gold frieze; the roof slab; the cornice
    y0, y1, z0, z1 = MK_BEAM
    bx(mb, H.MARBLE, (0, (y0 + y1) / 2, (z0 + z1) / 2), (45.2, y1 - y0, z1 - z0), bottom=True)
    for side in (-1, 1):
        bx(mb, H.MARBLE, (side * 20.5, (y0 + y1) / 2, (z0 + 2.0) / 2), (3.2, y1 - y0, z0 - 2.0 + 0.1), bottom=True)
    bx(mb, H.GOLD, (0, y0 + 0.25, z1 + 0.04), (45.4, 0.3, 0.2))
    sign = sign_panel(mb, 0.0, (y0 + y1) / 2 + 0.05, z1, *MK_SIGN_SIZE)
    r0, r1 = MK_ROOF
    bx(mb, H.MARBLE, (0, (r0 + r1) / 2, -1.7), (45.0, r1 - r0, 33.4), bottom=True)
    rect_frame(mb, H.GOLD, 0, -1.7, 45.3, 33.7, 0.4, r1 + 0.05, 0.55)
    # the ceiling: a lapis coffer in a gold frame under the dome
    bx(mb, H.LAPIS, (0, r0 - 0.05, -2.0), (13.0, 0.2, 13.0), bottom=True)
    # the attic over the front: a low marble parapet with gold coping and crystal acroteria at its ends
    bx(mb, H.MARBLE, (0, r1 + 0.6, 14.1), (44.0, 1.3, 1.0))
    bx(mb, H.GOLD, (0, r1 + 1.3, 14.1), (44.3, 0.18, 1.3))
    for side in (-1, 1):
        bx(mb, H.MARBLE, (side * 21.6, r1 + 1.4, 14.1), (1.6, 2.6, 1.6))
        finial(mb, side * 21.6, r1 + 2.7, 14.1, 0.9)
        H.gem(glow, (side * 21.6, r1 + 3.6 + 0.54 - 0.1, 14.1), 0.55, 0.9, B[H.GLOW], sides=6)
    # the dome: a marble drum with lapis windows, a gold ring, crystal glazing on gold ribs, a lantern and a crystal on top
    dx, dz, dr, dfoot, dtop, apex = MK_DOME
    annulus(mb, H.MARBLE, 0.0, dr, dfoot, dtop, seg=48, centre=(dx, dz))
    for k in range(12):
        a = TAU * (k + 0.5) / 12
        bx(mb, H.LAPIS, (dx + math.cos(a) * (dr - 0.05), (dfoot + dtop) / 2 + 0.2, dz + math.sin(a) * (dr - 0.05)), (1.1, 1.8, 0.3),
           yaw=math.atan2(math.cos(a), math.sin(a)))
    annulus(mb, H.GOLD, dr - 0.3, dr + 0.35, dtop - 0.05, dtop + 0.3, seg=48, centre=(dx, dz))
    rad = dr - 0.2
    prof = [(rad * math.cos(t), dtop + 0.25 + (apex - dtop) * math.sin(t), 0.95 - 0.25 * k / 10) for k, t in
            enumerate([math.pi / 2 * (1 - j / 10) for j in range(11)])]
    canopy.lathe([(max(p[0], 0.0), p[1], p[2]) for p in prof], 32, B[H.CRYSTAL], centre=(dx, 0, dz), cap_top=False)
    for k in range(8):
        a = TAU * k / 8
        pts = [(dx + math.cos(a) * (rad + 0.12) * math.cos(t), dtop + 0.25 + (apex - dtop + 0.12) * math.sin(t), dz + math.sin(a) * (rad + 0.12) * math.cos(t))
               for t in [math.pi / 2 * j / 10 for j in range(10)]]
        tube(mb, pts, 0.2, B[H.GOLD], sides=6, shade=1.0, caps=True)
    # the market's sign from afar: a great egg of light held up in a gold cradle on the dome
    mb.lathe([(0.9, apex + 1.0, 1.0), (1.3, apex + 0.6, 0.95), (1.45, apex + 0.1, 0.9), (1.9, apex - 0.3, 0.8)], 16, B[H.GOLD], centre=(dx, 0, dz), cap_top=True)
    egg_r = 1.45
    ey = apex + 1.0 + 1.105 * egg_r - 0.35
    egg(glow, H.GLOW, (dx, ey, dz), egg_r)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        tube(mb, [(dx + c * 0.7, apex + 0.9, dz + s_ * 0.7), (dx + c * 1.45, ey - 0.6, dz + s_ * 1.45), (dx + c * 1.5, ey + 0.4, dz + s_ * 1.5),
                  (dx + c * 1.15, ey + 1.0, dz + s_ * 1.15)], lambda f: 0.17 - 0.07 * f, B[H.GOLD], sides=6, shade=1.0)
    # the counters: the central one (the prompt is before it, the Curator behind it), and one along each side wall
    cx, cz = MK_COUNTER
    counter(mb, glow, cx, cz, 10.0, 2.4, floor, eggs=3)
    # two stalls out on the porch, either side of the way in, eggs on show under glass awnings on gold posts
    for side in (-1, 1):
        stall(mb, canopy, glow, side * 15.7, 16.5, floor)
    for side in (-1, 1):
        counter(mb, glow, side * 16.6, -6.8, 2.6, 10.0, floor, eggs=0, stones=True, yaw=0.0)
    return {"HB_Market": mb, "HB_MarketCanopy": canopy, "HB_MarketGlow": glow}, {"Sign": sign}


def rect_frame_v(mb, band, cx, cy, c, w, h, width, depth, axis="z", sign=1):
    """An upright frame round a w x h panel on a wall: on a wall facing +Z (axis "z", its face at z = c) or facing +/-X (axis "x")."""
    def p(u, v, d):
        if axis == "z":
            return (cx + u, cy + v, c + d)
        return (c + sign * d, cy + v, cx + u)
    n_out = (0, 0, 1) if axis == "z" else (sign, 0, 0)
    o = [(-w / 2 - width, -h / 2 - width), (w / 2 + width, -h / 2 - width), (w / 2 + width, h / 2 + width), (-w / 2 - width, h / 2 + width)]
    i = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    for k in range(4):
        j = (k + 1) % 4
        quad(mb, [p(*o[k], depth), p(*o[j], depth), p(*i[j], depth), p(*i[k], depth)], n_out, band, 0.95)
        mu, mv = (o[k][0] + o[j][0]) / 2, (o[k][1] + o[j][1]) / 2
        nn = (mu, mv, 0) if axis == "z" else (0, mv, mu)
        quad(mb, [p(*o[k], depth), p(*o[j], depth), p(*o[j], -0.05), p(*o[k], -0.05)], nn, band, 0.8)
        quad(mb, [p(*i[k], depth), p(*i[j], depth), p(*i[j], -0.05), p(*i[k], -0.05)], tuple(-v for v in nn), band, 0.7)


def stall(mb, canopy, glow, x, z, floor):
    """A porch stall: a marble counter set with three eggs, four slim gold posts and a glass awning sloping to the front."""
    counter(mb, glow, x, z, 4.6, 1.5, floor, eggs=2, pitch=2.2)
    y0, y1 = floor + 7.2, floor + 6.4
    for sx in (-1, 1):
        for sz, top in ((-1, y0), (1, y1)):
            px, pz = x + sx * 2.4, z + sz * 0.9
            mb.lathe([(0.11, top + 0.1, 1.0), (0.13, floor - 0.05, 0.8)], 8, B[H.GOLD], centre=(px, 0, pz), cap_top=True)
    # the awning: a gold frame and a glass pane, sloping down toward the square
    for sz, top in ((-1, y0), (1, y1)):
        tube(mb, [(x - 2.55, top, z + sz * 0.9), (x + 2.55, top, z + sz * 0.9)], 0.13, B[H.GOLD], sides=6, shade=1.0)
    for sx in (-1, 1):
        tube(mb, [(x + sx * 2.4, y0, z - 1.05), (x + sx * 2.4, y1, z + 1.05)], 0.12, B[H.GOLD], sides=6, shade=1.0)
    for face, dy in ((1, 0.06), (-1, -0.06)):
        H.W_oriented(canopy, [(x - 2.5, y0 + dy, z - 0.95), (x + 2.5, y0 + dy, z - 0.95), (x + 2.5, y1 + dy, z + 0.95), (x - 2.5, y1 + dy, z + 0.95)],
                     (0, face, 0.4 * face), B[H.CRYSTAL], 0.9)


def counter(mb, glow, cx, cz, w, d, floor, eggs=0, stones=False, yaw=0.0, pitch=3.0):
    """A marble counter, gold topped, a lapis panel on its front, eggs on gold stands or a crate of glowing stones on it."""
    top = floor + 3.3
    bx(mb, H.MARBLE, (cx, (floor - 0.05 + top) / 2, cz), (w, top - floor + 0.05, d))
    bx(mb, H.MARBLE, (cx, floor + 0.2, cz), (w + 0.4, 0.5, d + 0.4))                   # its plinth
    bx(mb, H.GOLD, (cx, top + 0.12, cz), (w + 0.4, 0.26, d + 0.4))
    if w >= d:
        bx(mb, H.LAPIS, (cx, floor + 1.75, cz + d / 2 + 0.03), (w - 1.2, 1.9, 0.16))
    else:
        for s in (-1, 1):
            bx(mb, H.LAPIS, (cx + s * (w / 2 + 0.03), floor + 1.75, cz), (0.16, 1.9, d - 1.2))
    for k in range(eggs):
        x = cx + (k - (eggs - 1) / 2) * pitch
        t = stand(mb, (x, top + 0.25, cz), 0.9, r=0.5)
        egg(glow, H.GLOW, (x, t + 1.105 * 0.48 - 0.08, cz), 0.48)
    if stones:
        for k in range(3):
            z = cz + (k - 1) * 3.0
            bx(mb, H.GOLD, (cx, top + 0.6, z), (1.8, 0.7, 2.2))                    # a gold-banded crate
            bx(mb, H.MARBLE, (cx, top + 0.62, z), (1.6, 0.74, 2.0))
            for j in range(4):
                a = TAU * j / 4 + k
                H.gem(glow, (cx + math.cos(a) * 0.4, top + 1.15, z + math.sin(a) * 0.5), 0.25, 0.45, B[H.GLOW], sides=5, twist=a)


# ======================================================================================================================
# The Blacksmith (the Celestial Forge): a vaulted hall before a furnace tower with a burning crown
# ======================================================================================================================
BS_W, BS_D = 40.0, 44.0
BS_FLOOR = 1.2
BS_HALL = (14.0, -10.0, 9.0)        # half width, back z, front z
BS_WALL_TOP, BS_VAULT_RISE = 14.4, 4.2
BS_ARCH = (4.6, 9.0)                # the front opening: half width, spring
BS_TOWER = (0.0, -16.0, 6.0, 30.0)  # x, z, half width (its flats), top of the shaft
BS_ANVIL = (0.0, 14.2)
BS_PROMPT = (0.0, 2.8, 17.2)
BS_SMITH = (2.8, BS_FLOOR, 14.0)
BS_HEARTH = (0.0, 3.6, -8.0)        # the Forge effect, in the hearth's mouth
BS_SIGN_SIZE = (10.0, 1.6)


def octagon_r(flat):
    return flat / math.cos(math.pi / 8)


def blacksmith():
    mb, core, crystal = W.MeshBuilder(), W.MeshBuilder(), W.MeshBuilder()
    floor = podium(mb, BS_W, BS_D)
    hw, zb, zf = BS_HALL
    t = 1.6
    # the slate footing round the hall: the soot-dark lower course a forge needs
    half = BS_ARCH[0]
    for s in (-1, 1):
        bx(mb, H.SLATE, (s * (hw - t / 2), floor + 1.0, (zb - 0.15 + zf - t - 0.15) / 2), (t + 0.3, 2.1, zf - t - zb))   # the sides
        bx(mb, H.SLATE, (s * (hw + 0.15 + half + 0.15) / 2, floor + 1.0, zf - t / 2), (hw - half, 2.1, t + 0.3))      # the front, to the opening
    bx(mb, H.SLATE, (0, floor + 1.0, zb + t / 2), (2 * hw - 2 * t - 0.4, 2.1, t + 0.3))                        # the back
    # the walls: back and sides plain, the front pierced by a great arch; corner buttresses
    bx(mb, H.MARBLE, (0, (floor + BS_WALL_TOP) / 2, zb + t / 2), (2 * hw, BS_WALL_TOP - floor + 0.1, t))
    for s in (-1, 1):   # (between the front and back walls: butting, not overlapping)
        bx(mb, H.MARBLE, (s * (hw - t / 2), (floor + BS_WALL_TOP) / 2, (zb + zf) / 2), (t, BS_WALL_TOP - floor + 0.1, zf - zb - 2 * t))
        for k in range(3):   # blind arches of lapis along each side, gold edged
            z = zb + 4.0 + k * 6.0
            bx(mb, H.LAPIS, (s * (hw + 0.02), 7.2, z), (0.2, 6.6, 3.2))
            bx(mb, H.GOLD, (s * (hw + 0.08), 10.65, z), (0.22, 0.3, 3.8))
            bx(mb, H.GOLD, (s * (hw + 0.08), 3.75, z), (0.22, 0.3, 3.8))
    half, spring = BS_ARCH
    arched_wall(mb, H.MARBLE, -hw, hw, floor - 0.05, BS_WALL_TOP + 0.05, zf - t, zf, 0.0, half, spring)
    arch_band(mb, H.GOLD, 0.0, spring, half - 0.02, half + 0.75, zf - 0.2, zf + 0.25, seg=18)
    for s in (-1, 1):   # the opening's gold jambs
        bx(mb, H.GOLD, (s * (half + 0.36), (floor + spring) / 2, zf + 0.02), (0.75, spring - floor, 0.46))
    H.gem(crystal, (0.0, spring + half + 0.75, zf + 0.35), 0.75, 1.25, B[H.GLOW], sides=6)   # the keystone crystal
    # the lunettes under the vault's ends, and the vault: lapis on gold ribs
    vx = hw + 0.6
    for z0, z1 in ((zf - t, zf), (zb, zb + t)):
        lunette(mb, H.MARBLE, 0.0, BS_WALL_TOP, hw, BS_VAULT_RISE * hw / vx, z0, z1)
    vault(mb, H.LAPIS, vx, BS_WALL_TOP, BS_VAULT_RISE, 0.6, zb - 0.4, zf + 0.4)
    for z in [zb + 0.2 + k * (zf - zb - 0.4) / 5 for k in range(6)]:
        tube(mb, [(math.cos(a) * (vx + 0.1), BS_WALL_TOP + math.sin(a) * (BS_VAULT_RISE + 0.1), z) for a in [math.pi * j / 14 for j in range(15)]],
               0.26, B[H.GOLD], sides=6, shade=1.0)
    sign = sign_panel(mb, 0.0, BS_WALL_TOP + 1.25, zf, *BS_SIGN_SIZE)
    # buttresses at the corners, stepped, gold capped
    for sx in (-1, 1):
        for z in (zb + 0.45, zf - 0.45):
            bx(mb, H.MARBLE, (sx * (hw + 0.4), (floor + 12.0) / 2, z), (2.6, 12.0 - floor, 2.5))
            bx(mb, H.MARBLE, (sx * (hw + 0.2), (12.0 + BS_WALL_TOP + 1.2) / 2, z), (2.0, BS_WALL_TOP + 1.2 - 12.0 + 0.1, 2.0))
            bx(mb, H.GOLD, (sx * (hw + 0.2), BS_WALL_TOP + 1.3, z), (2.3, 0.3, 2.3))
    # the furnace tower: an octagonal shaft, slate banded, glowing vents, a flared gold crown round a burning crystal
    tx, tz, flat, top = BS_TOWER
    sq = math.sqrt(2)
    # a battered slate foot, then the marble shaft tapering to the top, slate courses, a gold cornice
    mb.lathe([(flat * sq + 0.5, floor + 4.0, 0.8), (flat * sq + 1.3, floor - 0.05, 0.65)], 4, B[H.SLATE], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    f_low, f_high = flat, flat - 1.0

    def f_at(y):
        return f_low + (f_high - f_low) * (y - floor) / (top - floor)
    mb.lathe([(f_high * sq, top, 0.92), (f_low * sq, floor + 3.9, 0.7)], 4, B[H.MARBLE], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    for y in (13.0, 24.5):
        mb.lathe([((f_at(y) + 0.25) * sq, y + 0.55, 0.85), ((f_at(y) + 0.25) * sq, y - 0.55, 0.7)], 4, B[H.SLATE], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    for k in range(4):   # two tall glowing slits on every face near the top, gold lintels over them
        a = TAU * k / 4
        f = f_at(27.5)
        yaw = math.atan2(math.cos(a), math.sin(a))
        for off in (-1.6, 1.6):
            px, pz = tx + math.cos(a) * (f - 0.05) - math.sin(a) * off, tz + math.sin(a) * (f - 0.05) + math.cos(a) * off
            bx(core, H.GLOW, (px, 27.4, pz), (0.8, 3.2, 0.3), yaw=yaw)
            bx(mb, H.GOLD, (px + math.cos(a) * 0.08, 29.2, pz + math.sin(a) * 0.08), (1.4, 0.32, 0.3), yaw=yaw)
    # the furnace mouth on the face toward the square, over the hall's roof: a tall round-headed opening glowing behind steel
    # grate bars, in a gold arch (a round port read as a clock face)
    fe = f_at(21.0)
    zf_ = tz + fe
    mouth_w, mouth_y0, mouth_spring = 1.7, 18.9, 21.6
    bx(core, H.GLOW, (tx, (mouth_y0 + mouth_spring) / 2, zf_ - 0.02), (2 * mouth_w, mouth_spring - mouth_y0, 0.3))
    for k in range(12):
        a0, a1 = math.pi * k / 12, math.pi * (k + 1) / 12
        quad(core, [(tx, mouth_spring, zf_ + 0.13), (tx + math.cos(a0) * mouth_w, mouth_spring + math.sin(a0) * mouth_w, zf_ + 0.13),
                    (tx + math.cos(a1) * mouth_w, mouth_spring + math.sin(a1) * mouth_w, zf_ + 0.13)], (0, 0, 1), H.GLOW, 1.0)
        quad(core, [(tx + math.cos(a0) * mouth_w, mouth_spring + math.sin(a0) * mouth_w, zf_ - 0.17),
                    (tx + math.cos(a1) * mouth_w, mouth_spring + math.sin(a1) * mouth_w, zf_ - 0.17),
                    (tx + math.cos(a1) * mouth_w, mouth_spring + math.sin(a1) * mouth_w, zf_ + 0.13),
                    (tx + math.cos(a0) * mouth_w, mouth_spring + math.sin(a0) * mouth_w, zf_ + 0.13)],
             (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0), H.GLOW, 1.0)
    arch_band(mb, H.GOLD, tx, mouth_spring, mouth_w - 0.02, mouth_w + 0.55, zf_ - 0.3, zf_ + 0.32, seg=14)
    for sgn in (-1, 1):
        bx(mb, H.GOLD, (tx + sgn * (mouth_w + 0.26), (mouth_y0 - 0.2 + mouth_spring) / 2, zf_ + 0.01), (0.55, mouth_spring - mouth_y0 + 0.2, 0.62))
    bx(mb, H.GOLD, (tx, mouth_y0 - 0.25, zf_ + 0.05), (2 * mouth_w + 1.6, 0.5, 0.75))          # its sill
    for k in range(3):   # the grate: three steel bars over the glow
        x = tx + (k - 1) * 0.85
        bx(mb, H.STEEL, (x, (mouth_y0 + mouth_spring + 1.4) / 2, zf_ + 0.22), (0.2, mouth_spring + 1.4 - mouth_y0, 0.2))
    bx(mb, H.STEEL, (tx, 20.6, zf_ + 0.22), (2 * mouth_w + 0.1, 0.2, 0.2))
    r_high = f_high * sq
    # the crown (2026-11-15, after the first import: a flared square cap with prongs curling out read from afar as an upturned eave):
    # a gold cornice band flush with the shaft, then a round gold brazier, straight-sided, its rim rolled; four prongs rise from the
    # rim and curl INWARD into a cage holding the burning crystal; no flare, no corners, no overhang
    mb.lathe([((f_high + 0.35) * sq, top + 0.7, 1.0), ((f_high + 0.35) * sq, top - 0.2, 0.85)], 4, B[H.GOLD], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    br = f_high * 0.82
    mb.lathe([(br, top + 2.4, 0.95), (br + 0.15, top + 2.2, 1.0), (br, top + 2.0, 0.9), (br * 0.92, top + 0.65, 0.8)], 24, B[H.GOLD], centre=(tx, 0, tz), cap_top=False)
    mb.lathe([(br - 0.4, top + 2.05, 0.9), (br - 0.4, top + 1.1, 0.85)], 24, B[H.SLATE], centre=(tx, 0, tz), cap_top=True)   # the coals' bed inside
    for k in range(4):   # four gold prongs curling up and in round the burning crystal
        a = TAU * k / 4 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        pts = [(tx + c * (br - 0.1), top + 2.3, tz + s * (br - 0.1)), (tx + c * (br - 0.3), top + 4.0, tz + s * (br - 0.3)),
               (tx + c * 1.9, top + 5.6, tz + s * 1.9), (tx + c * 0.55, top + 6.2, tz + s * 0.55)]
        tube(mb, pts, lambda f: 0.36 - 0.18 * f, B[H.GOLD], sides=6, shade=1.0)
    H.gem(core, (tx, top + 3.4, tz), 1.35, 2.3, B[H.GLOW], sides=8)
    tube(mb, [(tx, top + 6.0, tz), (tx, top + 6.55, tz)], lambda f: 0.42 - 0.2 * f, B[H.GOLD], sides=8, shade=1.0)
    H.gem(crystal, (tx, top + 6.55 + 0.42 - 0.08, tz), 0.35, 0.7, B[H.GLOW], sides=6)
    # the hearth on the hall's back wall: a slate bed of glowing coals under a gold-mouthed arch and a slate hood
    hz = zb + t
    bx(mb, H.SLATE, (0, floor + 1.1, hz + 1.2), (7.0, 2.3, 2.5))
    bx(core, H.GLOW, (0, floor + 2.27, hz + 1.2), (6.0, 0.14, 1.9))
    bx(core, H.GLOW, (0, 4.4, hz + 0.04), (4.4, 3.4, 0.2))           # the fire's glow in the mouth
    arch_band(mb, H.GOLD, 0.0, 6.1, 2.2, 2.9, hz - 0.05, hz + 0.45, seg=12)
    for s in (-1, 1):
        bx(mb, H.GOLD, (s * 2.55, (floor + 2.1 + 6.1) / 2, hz + 0.2), (0.7, 6.1 - floor - 2.1, 0.5))
    bx(mb, H.SLATE, (0, 10.4, hz + 1.1), (8.4, 3.4, 2.4))
    bx(mb, H.SLATE, (0, 12.9, hz + 0.6), (5.4, 1.8, 1.4))
    bx(mb, H.GOLD, (0, 8.75, hz + 1.1), (8.7, 0.3, 2.6))
    # the anvil before the arch on a marble block, the quench trough, a rack of blades
    ax, az = BS_ANVIL
    bx(mb, H.MARBLE, (ax, floor + 0.95, az), (3.2, 1.9, 2.4))
    bx(mb, H.GOLD, (ax, floor + 1.9, az), (3.4, 0.2, 2.6))
    anvil(mb, ax, floor + 2.0, az)
    trough(mb, 7.0, az + 0.4, floor)
    blade_rack(mb, -8.4, zf + 0.3, floor)
    return {"HB_Blacksmith": mb, "HB_BlacksmithCore": core, "HB_BlacksmithCrystal": crystal}, {"Sign": sign}


def trough(mb, x, z, floor):
    """The quench trough: a marble basin (a floor and four walls), gold rimmed, its water a little under the rim."""
    bx(mb, H.MARBLE, (x, floor + 0.55, z), (4.2, 1.1, 2.2))
    for s in (-1, 1):
        bx(mb, H.MARBLE, (x, floor + 1.4, z + s * 0.95), (4.2, 0.8, 0.3))
        bx(mb, H.MARBLE, (x + s * 1.95, floor + 1.4, z), (0.3, 0.8, 1.6))
    rect_frame(mb, H.GOLD, x, z, 4.36, 2.36, 0.4, floor + 1.86, 0.2)
    bx(mb, H.CRYSTAL, (x, floor + 1.32, z), (3.56, 0.5, 1.56))       # the water (glass in the game)


def lunette(mb, band, cx, spring, half, rise, z0, z1, seg=18):
    """The half-ellipse wall under a vault's end, from the spring line up to the vault (faces +Z at z1, -Z at z0)."""
    pts = [(cx + math.cos(math.pi * k / seg) * half, spring + math.sin(math.pi * k / seg) * rise) for k in range(seg + 1)]
    for (ax_, ay), (bx_, by) in zip(pts, pts[1:]):
        for z, n in ((z1, 1), (z0, -1)):
            quad(mb, [(cx, spring, z), (ax_, ay, z), (bx_, by, z)], (0, 0, n), band, 0.85)


def vault(mb, band, half, spring, rise, t, z0, z1, seg=20):
    """A barrel vault along Z: its outer and inner skins, its two end strips and the strips along the spring lines."""
    def at(k, r_off, z):
        a = math.pi * k / seg
        return (math.cos(a) * (half - r_off), spring + math.sin(a) * (rise - r_off), z)
    for k in range(seg):
        a = math.pi * (k + 0.5) / seg
        n = (math.cos(a), math.sin(a), 0)
        quad(mb, [at(k, 0, z0), at(k + 1, 0, z0), at(k + 1, 0, z1), at(k, 0, z1)], n, band, 0.9)
        quad(mb, [at(k, t, z0), at(k + 1, t, z0), at(k + 1, t, z1), at(k, t, z1)], (-n[0], -n[1], 0), band, 0.55)
        quad(mb, [at(k, 0, z1), at(k + 1, 0, z1), at(k + 1, t, z1), at(k, t, z1)], (0, 0, 1), band, 0.8)
        quad(mb, [at(k, 0, z0), at(k + 1, 0, z0), at(k + 1, t, z0), at(k, t, z0)], (0, 0, -1), band, 0.7)
    for k in (0, seg):
        quad(mb, [at(k, 0, z0), at(k, t, z0), at(k, t, z1), at(k, 0, z1)], (0, -1, 0), band, 0.5)


def anvil(mb, x, y, z):
    """A smith's anvil in steel: a waisted foot, the body, the face, a tapering horn."""
    bx(mb, H.STEEL, (x, y + 0.25, z), (1.9, 0.5, 1.3))
    bx(mb, H.STEEL, (x, y + 0.75, z), (1.0, 0.6, 0.8))
    bx(mb, H.STEEL, (x - 0.15, y + 1.3, z), (2.2, 0.55, 1.05))
    tube(mb, [(x + 0.9, y + 1.32, z), (x + 1.5, y + 1.25, z), (x + 2.0, y + 1.12, z)], lambda f: 0.36 - 0.3 * f, B[H.STEEL], sides=8, shade=0.95)
    bx(mb, H.STEEL, (x - 1.5, y + 1.38, z), (0.5, 0.36, 0.8))


def blade_rack(mb, x, z, floor):
    """A gold rack on the front wall holding three steel swords, points down."""
    for dy in (2.2, 5.9):
        bx(mb, H.GOLD, (x, floor + dy, z + 0.12), (5.0, 0.3, 0.3))
    for s in (-1, 1):
        bx(mb, H.GOLD, (x + s * 2.4, floor + 4.0, z + 0.1), (0.3, 4.6, 0.32))
    for k in range(3):
        bxp = x + (k - 1) * 1.4
        bx(mb, H.STEEL, (bxp, floor + 3.3, z + 0.3), (0.36, 4.22, 0.08))         # the blade, against the bars
        bx(mb, H.GOLD, (bxp, floor + 5.5, z + 0.3), (1.2, 0.22, 0.28))           # the guard
        bx(mb, H.SLATE, (bxp, floor + 6.2, z + 0.3), (0.24, 1.2, 0.24))          # the grip
        bx(mb, H.GOLD, (bxp, floor + 6.9, z + 0.3), (0.4, 0.3, 0.4))             # the pommel


# ======================================================================================================================
# Buy & Sell (the Gilded Vault): a gold-domed vault with a great balance on top, a counter before its door
# ======================================================================================================================
BV_R = 19.6
BV_DRUM = (0.0, -2.0, 10.5, 14.0)       # x, z, radius, top
BV_DOME = (9.6, 15.6, 22.5)             # radius, foot, apex
BV_SCALE = (5.2, 28.2, 25.4)            # the pans' x, the beam's y, the pans' y
BV_DOOR_R = 3.4
BV_PROMPT = (0.0, 2.6, 17.8)
BV_APPRAISER = (0.0, 1.2, 11.9)
BV_SIGN_SIZE = (9.0, 1.3)


def buy_sell():
    mb, stones = W.MeshBuilder(), W.MeshBuilder()
    floor = round_podium(mb, (BV_R, BV_R - 1.3))
    dx, dz, dr, dtop = BV_DRUM
    # the drum: marble on a slate plinth, ten lapis pilasters with gold capitals, a gold belt, a marble attic
    annulus(mb, H.SLATE, 0.0, dr + 0.35, floor - 0.05, floor + 1.4, seg=60, centre=(dx, dz))
    annulus(mb, H.MARBLE, 0.0, dr, floor + 1.35, dtop, seg=60, centre=(dx, dz))
    for k in range(10):
        a = TAU * (k + 0.5) / 10 + math.pi / 2
        if abs(math.sin(a) - 1) < 0.2:
            continue      # (none over the door)
        px, pz = dx + math.cos(a) * (dr + 0.1), dz + math.sin(a) * (dr + 0.1)
        yaw = math.atan2(math.cos(a), math.sin(a))
        bx(mb, H.LAPIS, (px, (floor + 1.4 + dtop - 1.0) / 2, pz), (1.3, dtop - 1.0 - floor - 1.4, 0.5), yaw=yaw)
        bx(mb, H.GOLD, (px, dtop - 0.75, pz), (1.7, 0.5, 0.7), yaw=yaw)
    annulus(mb, H.GOLD, dr - 0.2, dr + 0.4, dtop - 0.2, dtop + 0.35, seg=60, centre=(dx, dz))
    dome_r, dome_foot, apex = BV_DOME
    annulus(mb, H.MARBLE, 0.0, dome_r, dtop + 0.3, dome_foot, seg=60, centre=(dx, dz))
    annulus(mb, H.GOLD, dome_r - 0.25, dome_r + 0.3, dome_foot - 0.15, dome_foot + 0.2, seg=60, centre=(dx, dz))
    prof = [(dome_r * 0.985 * math.cos(t), dome_foot + 0.15 + (apex - dome_foot) * math.sin(t), 1.0 - 0.3 * j / 12)
            for j, t in enumerate([math.pi / 2 * (1 - j / 12) for j in range(13)])]
    mb.lathe([(max(p[0], 0.0), p[1], p[2]) for p in prof], 40, B[H.GOLD], centre=(dx, 0, dz), cap_top=False)
    for k in range(10):   # the dome's ribs: raised gold
        a = TAU * k / 10
        pts = [(dx + math.cos(a) * (dome_r * 0.985 + 0.1) * math.cos(t), dome_foot + 0.15 + (apex - dome_foot + 0.1) * math.sin(t),
                dz + math.sin(a) * (dome_r * 0.985 + 0.1) * math.cos(t)) for t in [math.pi / 2 * j / 10 for j in range(9)]]
        tube(mb, pts, 0.16, B[H.GOLD], sides=6, shade=1.0)
    # the lantern on top and the balance over it
    annulus(mb, H.MARBLE, 0.0, 1.7, apex - 0.4, apex + 1.0, seg=24, centre=(dx, dz))
    annulus(mb, H.GOLD, 0.0, 2.0, apex + 0.95, apex + 1.3, seg=24, centre=(dx, dz))
    px_, beam_y, pan_y = BV_SCALE
    mb.lathe([(0.32, beam_y + 0.2, 1.0), (0.42, apex + 1.3, 0.8)], 10, B[H.GOLD], centre=(dx, 0, dz), cap_top=True)
    tube(mb, [(dx - px_ - 0.3, beam_y, dz), (dx, beam_y + 0.3, dz), (dx + px_ + 0.3, beam_y, dz)], 0.28, B[H.GOLD], sides=8, shade=1.0)
    H.gem(stones, (dx, beam_y + 0.9, dz), 0.45, 0.8, B[H.GLOW], sides=6)
    for s in (-1, 1):
        x = dx + s * px_
        for c in (-1, 1):   # the chains: three thin gold rods down to the pan's rim
            tube(mb, [(x, beam_y - 0.1, dz), (x + c * 1.15, pan_y + 0.15, dz)], 0.07, B[H.GOLD], sides=5, shade=1.0)
        tube(mb, [(x, beam_y - 0.1, dz), (x, pan_y + 0.15, dz + 1.15)], 0.07, B[H.GOLD], sides=5, shade=1.0)
        mb.lathe([(1.35, pan_y + 0.2, 1.0), (1.0, pan_y - 0.2, 0.9), (0.25, pan_y - 0.38, 0.8)], 16, B[H.GOLD], centre=(x, 0, dz), cap_top=True)
    for k in range(5):   # spirit stones heaped in the left pan, an egg in the right (beasts traded for stones)
        a = TAU * k / 5
        H.gem(stones, (dx - px_ + math.cos(a) * 0.4, pan_y + 0.2 + 0.24 - 0.08, dz + math.sin(a) * 0.4), 0.22, 0.4, B[H.GLOW], sides=5, twist=a)
    egg(mb, H.MARBLE, (dx + px_, pan_y + 0.2 + 1.105 * 0.55 - 0.1, dz), 0.55)
    # the vault door on the drum's front: a gold wheel of spokes and bolts in a marble portico
    door_z = dz + dr
    portico(mb, door_z, floor)
    door(mb, 0.0, floor + 4.6, door_z + 0.3)
    sign = sign_panel(mb, 0.0, BV_PORTICO[1] + 0.9, door_z + 3.6, *BV_SIGN_SIZE)
    # the counter before the door: a marble arc round the drum, gold topped, a lapis band, stones heaped on it
    arc_counter(mb, dx, dz, 15.7, 17.2, math.radians(64), math.radians(116), floor)
    for k in range(6):
        a = TAU * k / 6
        H.gem(stones, (-3.6 + math.cos(a) * 0.45, floor + 3.65, dz + 16.05 + math.sin(a) * 0.35), 0.24, 0.42, B[H.GLOW], sides=5, twist=a)
    H.gem(stones, (-3.6, floor + 3.6 + 0.36 - 0.08, dz + 16.05), 0.3, 0.6, B[H.GLOW], sides=5)
    return {"HB_BuySell": mb, "HB_BuySellStones": stones}, {"Sign": sign}


BV_PORTICO = (5.8, 11.6)      # the columns' x, the lintel's foot


def portico(mb, door_z, floor):
    """Two gold-capped marble columns and a deep lintel framing the vault door, reaching back into the drum; an attic over it."""
    H.MARBLE_BAND, H.GOLD_BAND = B[H.MARBLE], B[H.GOLD]
    cxp, foot = BV_PORTICO
    for s in (-1, 1):
        H.column(mb, s * cxp, door_z + 2.0, floor - 0.05, foot, r=0.8)
    bx(mb, H.MARBLE, (0, foot + 0.9, door_z + 1.0), (2 * cxp + 3.2, 1.8, 5.2), bottom=True)
    bx(mb, H.GOLD, (0, foot + 1.9, door_z + 1.0), (2 * cxp + 3.5, 0.22, 5.5))
    bx(mb, H.MARBLE, (0, foot + 2.5, door_z + 0.7), (2 * cxp + 1.0, 1.0, 4.2))
    bx(mb, H.GOLD, (0, foot + 3.05, door_z + 0.7), (2 * cxp + 1.3, 0.16, 4.5))
    finial(mb, 0.0, foot + 3.1, door_z + 2.2, 1.3)


def arc_counter(mb, cx, cz, r0, r1, a0, a1, floor, seg=14):
    """A curved counter: a marble arc (walls, ends and top) on a plinth, a gold top, a lapis band on its outer face."""
    top = floor + 3.3

    def sector(band, ra, rb, y0, y1, shade=0.85, grow=0.0):
        b0, b1 = a0 - grow, a1 + grow
        pts = [b0 + (b1 - b0) * k / seg for k in range(seg + 1)]
        P = lambda a, r, y: (cx + math.cos(a) * r, y, cz + math.sin(a) * r)
        for a, b in zip(pts, pts[1:]):
            m = (a + b) / 2
            quad(mb, [P(a, rb, y0), P(b, rb, y0), P(b, rb, y1), P(a, rb, y1)], (math.cos(m), 0, math.sin(m)), band, shade)
            quad(mb, [P(a, ra, y0), P(b, ra, y0), P(b, ra, y1), P(a, ra, y1)], (-math.cos(m), 0, -math.sin(m)), band, shade * 0.9)
            quad(mb, [P(a, ra, y1), P(b, ra, y1), P(b, rb, y1), P(a, rb, y1)], (0, 1, 0), band, 0.95)
        for a, sgn in ((b0, -1), (b1, 1)):
            quad(mb, [P(a, ra, y0), P(a, rb, y0), P(a, rb, y1), P(a, ra, y1)], (-math.sin(a) * sgn, 0, math.cos(a) * sgn), band, shade)
    sector(H.MARBLE, r0, r1, floor - 0.05, top)
    sector(H.MARBLE, r0 - 0.2, r1 + 0.2, floor - 0.05, floor + 0.45, grow=0.015)
    sector(H.GOLD, r0 - 0.2, r1 + 0.2, top - 0.05, top + 0.25, grow=0.015)
    sector(H.LAPIS, r1 - 0.1, r1 + 0.06, floor + 0.85, floor + 2.65, 0.75)


def disc_xy(mb, band, cx, cy, z, r, seg, normal_z, shade=0.9):
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        quad(mb, [(cx, cy, z), (cx + math.cos(a0) * r, cy + math.sin(a0) * r, z), (cx + math.cos(a1) * r, cy + math.sin(a1) * r, z)],
             (0, 0, normal_z), band, shade)


def door(mb, cx, cy, z):
    """The vault door: a thick gold disc, a raised rim, bolts round it, a spoked wheel at its middle."""
    R, seg = BV_DOOR_R, 40
    disc_xy(mb, H.GOLD, cx, cy, z + 0.45, R, seg, 1, 0.85)
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        m = (a0 + a1) / 2
        quad(mb, [(cx + math.cos(a0) * R, cy + math.sin(a0) * R, z - 0.4), (cx + math.cos(a1) * R, cy + math.sin(a1) * R, z - 0.4),
                  (cx + math.cos(a1) * R, cy + math.sin(a1) * R, z + 0.45), (cx + math.cos(a0) * R, cy + math.sin(a0) * R, z + 0.45)],
             (math.cos(m), math.sin(m), 0), H.GOLD, 0.8)
    tube(mb, [(cx + math.cos(TAU * k / 32) * (R - 0.35), cy + math.sin(TAU * k / 32) * (R - 0.35), z + 0.5) for k in range(33)], 0.18,
           B[H.GOLD], sides=6, shade=1.0, caps=False)
    for k in range(12):
        a = TAU * k / 12
        bx(mb, H.STEEL, (cx + math.cos(a) * (R - 0.9), cy + math.sin(a) * (R - 0.9), z + 0.5), (0.34, 0.34, 0.3))
    tube(mb, [(cx + math.cos(TAU * k / 24) * 1.25, cy + math.sin(TAU * k / 24) * 1.25, z + 1.05) for k in range(25)], 0.13,
           B[H.STEEL], sides=6, shade=1.0, caps=False)
    for k in range(6):
        a = TAU * k / 6
        tube(mb, [(cx + math.cos(a) * 0.3, cy + math.sin(a) * 0.3, z + 1.05), (cx + math.cos(a) * 1.25, cy + math.sin(a) * 1.25, z + 1.05)], 0.1, B[H.STEEL], sides=5, shade=1.0)
    tube(mb, [(cx, cy, z + 0.4), (cx, cy, z + 1.25)], 0.32, B[H.STEEL], sides=8, shade=1.0)


# ======================================================================================================================
# The Leaderboard (the Ascension Board): a broad board between two pylons under a gold arch and a star
# ======================================================================================================================
LB_DAIS = (13.0, 11.6)
LB_BOARD = (12.0, 16.4, 0.8)              # half width, top, half depth
LB_FACE = ((0.0, 8.6), (20.0, 10.4))      # the lapis face the rows are written on: centre (x, y), size
LB_TITLE = ((0.0, 15.35), (11.0, 1.35))
LB_STAR = (0.0, 21.3)


def leaderboard():
    mb, glow = W.MeshBuilder(), W.MeshBuilder()
    floor = round_podium(mb, LB_DAIS, rise=0.5)
    hw, top, hd = LB_BOARD
    bx(mb, H.MARBLE, (0, floor + 0.7, 0), (2 * hw + 1.4, 1.5, 2 * hd + 1.6))            # the plinth
    bx(mb, H.GOLD, (0, floor + 1.48, 0), (2 * hw + 1.7, 0.2, 2 * hd + 1.9))
    bx(mb, H.MARBLE, (0, (floor + 1.4 + top) / 2, 0), (2 * hw, top - floor - 1.4, 2 * hd))  # the board's slab
    bx(mb, H.GOLD, (0, top + 0.1, 0), (2 * hw + 0.3, 0.3, 2 * hd + 0.3))
    (fx, fy), (fw, fh) = LB_FACE
    bx(mb, H.GOLD, (fx, fy, hd - 0.05), (fw + 0.9, fh + 0.9, 0.4))
    bx(mb, H.LAPIS, (fx, fy, hd + 0.2), (fw, fh, 0.12))
    face = (fx, fy, round(hd + 0.26 + 0.03, 3))
    (tx, ty), (tw, th) = LB_TITLE
    bx(mb, H.GOLD, (tx, ty, hd - 0.05), (tw + 0.7, th + 0.6, 0.4))
    bx(mb, H.LAPIS, (tx, ty, hd + 0.2), (tw, th, 0.12))
    title = (tx, ty, round(hd + 0.26 + 0.03, 3))
    # the back: a gold medallion of the star in a lapis roundel
    disc_xy(mb, H.LAPIS, 0.0, 8.6, -hd - 0.02, 3.2, 32, -1, 0.8)
    tube(mb, [(math.cos(TAU * k / 32) * 3.2, 8.6 + math.sin(TAU * k / 32) * 3.2, -hd - 0.05) for k in range(33)], 0.2, B[H.GOLD],
           sides=6, shade=1.0, caps=False)
    # the pylons: tapering marble obelisks, gold capped
    for s in (-1, 1):
        x = s * (hw + 1.7)
        mb.lathe([(1.15, 17.8, 0.92), (1.5, floor + 1.6, 0.7)], 4, B[H.MARBLE], centre=(x, 0, 0), phase=math.pi / 4, cap_top=False)
        mb.lathe([(1.9, floor + 1.75, 0.95), (1.9, floor - 0.05, 0.7)], 4, B[H.MARBLE], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
        mb.lathe([(0.05, 19.6, 1.0), (1.35, 17.95, 0.9), (1.35, 17.7, 0.85)], 4, B[H.GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
        bx(mb, H.GOLD, (x, floor + 1.83, 0), (2.9, 0.22, 2.9))
    # the arch over the board, the star's mount at its crown
    pts = [(math.cos(math.pi * k / 24) * (hw + 0.4), top + 0.2 + math.sin(math.pi * k / 24) * 3.5, 0.0) for k in range(25)]
    tube(mb, pts, 0.34, B[H.GOLD], sides=8, shade=1.0, caps=True)
    sy = LB_STAR[1]
    tube(mb, [(math.cos(TAU * k / 20) * 1.15, sy + math.sin(TAU * k / 20) * 1.15, 0.0) for k in range(21)], 0.14, B[H.GOLD], sides=6, shade=1.0, caps=False)
    H.gem(glow, (0.0, sy, 0.0), 0.6, 0.9, B[H.GLOW], sides=6)
    for k in range(6):
        a = TAU * k / 6 + math.pi / 2
        H.shard(glow, (math.cos(a) * 0.4, sy + math.sin(a) * 0.4, 0.0), (math.cos(a), math.sin(a), 0.0), 1.2, 0.17, B[H.GLOW], twist=a)
    return {"HB_Leaderboard": mb, "HB_LeaderboardGlow": glow}, {"Face": face, "FaceSize": (fw, fh), "Title": title, "TitleSize": (tw, th),
                                                                "Star": (0.0, sy, 0.0)}


# ======================================================================================================================
# The Merchant's dais: a round dais with a crescent screen behind him and two crystal posts (it reads as a place when he is away)
# ======================================================================================================================
MD_R = (15.0, 13.6)
MD_TOP = 0.7


def merchant_dais():
    mb, glow = W.MeshBuilder(), W.MeshBuilder()
    annulus(mb, H.MARBLE, 0.0, MD_R[0], -0.5, 0.35, seg=80)
    annulus(mb, H.GOLD, MD_R[0] - 0.3, MD_R[0] + 0.05, 0.12, 0.39, seg=80)
    annulus(mb, H.MARBLE, 0.0, MD_R[1], 0.3, MD_TOP, seg=80)
    annulus(mb, H.GOLD, MD_R[1] - 0.3, MD_R[1] + 0.05, MD_TOP - 0.24, MD_TOP + 0.04, seg=80)
    annulus(mb, H.LAPIS, 11.6, 12.4, MD_TOP - 0.1, MD_TOP + 0.02, seg=80)
    # the crescent screen behind him (-Z), its top rising to the middle, lapis panels, gold coping
    seg, R, t = 20, 11.0, 0.9
    a0, a1 = math.radians(205), math.radians(335)
    coping = []
    for k in range(seg):
        a, b = a0 + (a1 - a0) * k / seg, a0 + (a1 - a0) * (k + 1) / seg
        ha = MD_TOP + 2.6 + 2.2 * math.sin(math.pi * k / seg)
        hb = MD_TOP + 2.6 + 2.2 * math.sin(math.pi * (k + 1) / seg)

        def P(ang, r, y):
            return (math.cos(ang) * r, y, math.sin(ang) * r)
        m = (a + b) / 2
        for r, n in ((R + t / 2, 1), (R - t / 2, -1)):
            quad(mb, [P(a, r, MD_TOP - 0.05), P(b, r, MD_TOP - 0.05), P(b, r, hb), P(a, r, ha)], (n * math.cos(m), 0, n * math.sin(m)), H.MARBLE, 0.8)
        quad(mb, [P(a, R - t / 2, ha), P(b, R - t / 2, hb), P(b, R + t / 2, hb), P(a, R + t / 2, ha)], (0, 1, 0), H.MARBLE, 0.95)
        coping.append(P(a, R, ha + 0.1))
        if 2 <= k < seg - 2 and k % 4 == 2:
            c = (a + b + (a1 - a0) / seg) / 2
            bx(mb, H.LAPIS, (math.cos(c) * (R - t / 2 - 0.02), MD_TOP + 2.0, math.sin(c) * (R - t / 2 - 0.02)), (2.6, 2.4, 0.16),
               yaw=math.atan2(math.cos(c), math.sin(c)))
    coping.append((math.cos(a1) * R, MD_TOP + 2.6 + 0.1, math.sin(a1) * R))
    tube(mb, coping, 0.3, B[H.GOLD], sides=6, shade=1.0, caps=True)
    for ang in (a0, a1):   # the screen's ends: the crystal posts
        x, z = math.cos(ang) * R, math.sin(ang) * R
        mb.lathe([(0.55, MD_TOP + 5.6, 0.95), (0.7, MD_TOP - 0.05, 0.7)], 10, B[H.MARBLE], centre=(x, 0, z), cap_top=True)
        annulus(mb, H.GOLD, 0.0, 0.85, MD_TOP + 5.5, MD_TOP + 5.85, seg=12, centre=(x, z))
        H.gem(glow, (x, MD_TOP + 5.85 + 0.54 - 0.1, z), 0.5, 0.9, B[H.GLOW], sides=6)
        annulus(mb, H.MARBLE, 0.0, 1.05, MD_TOP - 0.05, MD_TOP + 0.5, seg=12, centre=(x, z))
    return {"HB_MerchantDais": mb, "HB_MerchantDaisGlow": glow}, {"Top": MD_TOP}


# ======================================================================================================================
# The spawn pad: a low marble disc with a gold rim, a lapis ring, a star inlay pointing at the pen (+Z), a crystal at its back
# ======================================================================================================================
SP_R, SP_TOP = 6.0, 0.45


def star_prism(mb, band, n, r_out, r_in, y0, y1, long_point=1.0, phase=math.pi / 2):
    pts = []
    for k in range(2 * n):
        a = phase + math.pi * k / n
        r = r_out if k % 2 == 0 else r_in
        if k == 0:
            r *= long_point
        pts.append((math.cos(a) * r, math.sin(a) * r))
    for k in range(2 * n):
        quad(mb, [(0, y1, 0), (pts[k][0], y1, pts[k][1]), (pts[(k + 1) % (2 * n)][0], y1, pts[(k + 1) % (2 * n)][1])], (0, 1, 0), band, 1.0)
        a, b = pts[k], pts[(k + 1) % (2 * n)]
        quad(mb, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], ((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2), band, 0.8)


def spawn_pad():
    mb, glow = W.MeshBuilder(), W.MeshBuilder()
    annulus(mb, H.MARBLE, 0.0, SP_R, -0.4, SP_TOP, seg=48)
    annulus(mb, H.GOLD, SP_R - 0.32, SP_R + 0.05, SP_TOP - 0.22, SP_TOP + 0.05, seg=48)
    annulus(mb, H.LAPIS, 4.0, 4.7, SP_TOP - 0.1, SP_TOP + 0.02, seg=48)
    annulus(mb, H.GOLD, 3.82, 4.0, SP_TOP - 0.1, SP_TOP + 0.03, seg=48)
    annulus(mb, H.GOLD, 4.7, 4.88, SP_TOP - 0.1, SP_TOP + 0.03, seg=48)
    star_prism(glow, H.GLOW, 4, 2.6, 0.75, SP_TOP - 0.1, SP_TOP + 0.03, long_point=1.35)
    # the crystal set into the rim at the back, in a gold collar
    annulus(mb, H.GOLD, 0.0, 0.62, SP_TOP - 0.05, SP_TOP + 0.35, seg=12, centre=(0.0, -5.3))
    H.gem(glow, (0.0, SP_TOP + 0.95, -5.3), 0.42, 1.0, B[H.GLOW], sides=6)
    return {"HB_SpawnPad": mb, "HB_SpawnPadGlow": glow}, {"Top": SP_TOP}


# ======================================================================================================================
# The new plinths: a stepped marble apron round the Hatching Sanctum's dais and round the Qi Spring's platform
# ======================================================================================================================
def plinth_ring(mb, r_in, r_out, top, studs):
    annulus(mb, H.MARBLE, r_in, r_out, -0.5, top, seg=96)
    annulus(mb, H.GOLD, r_out - 0.35, r_out + 0.05, top - 0.25, top + 0.05, seg=96)
    mid = (r_in + r_out) / 2
    annulus(mb, H.LAPIS, mid - 0.45, mid + 0.45, top - 0.1, top + 0.02, seg=96)
    for k in range(studs):   # gold stars in the lapis band
        a = TAU * (k + 0.5) / studs
        bx(mb, H.GOLD, (math.cos(a) * mid, top + 0.0, math.sin(a) * mid), (0.5, 0.12, 0.5), yaw=a + math.pi / 4)


def sanctum_plinth():
    mb = W.MeshBuilder()
    plinth_ring(mb, H.DAIS[0][0] - 0.05, 23.6, 0.3, 24)     # under its first step (r 20, top 0.6)
    return {"HB_SanctumPlinth": mb}, {}


def spring_plinth():
    mb = W.MeshBuilder()
    plinth_ring(mb, H.QS_PLAT_R - 0.05, 14.6, 0.2, 16)       # round its platform (r 11.2, top 0.3)
    return {"HB_SpringPlinth": mb}, {}


# ======================================================================================================================
# The Market Square's centrepiece (restrained): a star compass, a low plinth, a fluted column and an armillary round a crystal
# ======================================================================================================================
def square_compass():
    mb, glow = W.MeshBuilder(), W.MeshBuilder()
    annulus(mb, H.MARBLE, 0.0, 4.2, -0.4, 0.5, seg=48)
    annulus(mb, H.GOLD, 3.9, 4.25, 0.25, 0.55, seg=48)
    annulus(mb, H.MARBLE, 0.0, 3.3, 0.45, 1.0, seg=48)
    annulus(mb, H.GOLD, 3.0, 3.35, 0.75, 1.05, seg=48)
    star_prism(mb, H.LAPIS, 8, 2.9, 1.1, 0.95, 1.08, long_point=1.0, phase=0.0)
    H.MARBLE_BAND, H.GOLD_BAND = B[H.MARBLE], B[H.GOLD]
    H.column(mb, 0.0, 0.0, 1.0, 4.6, r=0.62)
    c = 6.0
    for tilt in (0.45, -0.45):   # two gold rings crossing round the crystal, held by the column's capital
        pts = []
        for k in range(29):
            a = TAU * k / 28
            x, y = math.cos(a) * 1.55, math.sin(a) * 1.55
            pts.append((x * math.cos(tilt), c + y, x * math.sin(tilt)))
        tube(mb, pts, 0.09, B[H.GOLD], sides=6, shade=1.0, caps=False)
    tube(mb, [(0.0, 4.5, 0.0), (0.0, c - 1.5, 0.0)], 0.18, B[H.GOLD], sides=8, shade=1.0)
    H.gem(glow, (0.0, c - 0.15, 0.0), 0.55, 1.0, B[H.GLOW], sides=6)
    tube(mb, [(0.0, c - 1.6, 0.0), (0.0, c - 0.3, 0.0)], 0.07, B[H.GOLD], sides=5, shade=1.0)
    return {"HB_SquareCompass": mb, "HB_SquareCompassGlow": glow}, {}


ASSETS = {
    "Market": market,
    "Blacksmith": blacksmith,
    "BuySell": buy_sell,
    "Leaderboard": leaderboard,
    "MerchantDais": merchant_dais,
    "SpawnPad": spawn_pad,
    "SanctumPlinth": sanctum_plinth,
    "SpringPlinth": spring_plinth,
    "SquareCompass": square_compass,
}


# ======================================================================================================================
# The finish pass
# ======================================================================================================================
TILE = 8.0                      # studs per tile of a Roblox material's texture (the UVs repeat once per cell)
BEVEL = 0.06
BEVEL_ANGLE = math.radians(75)
SMOOTH_ANGLE = math.radians(62)
FLAT_UP = 0.94
SUFFIX = {H.MARBLE: "Marble", H.SHADE: "Shade", H.MARBLE2: "Marble", H.LAPIS: "Lapis", H.GOLD: "Gold",
          H.CRYSTAL: "Crystal", H.GLOW: "Glow", H.SLATE: "Slate", H.STEEL: "Steel"}
SINGLE = {"Glow", "Crystal"}     # pieces whose whole mesh is one material (a glow piece is Neon in the game: no split name)


def _band_of(v, bands):
    for k, (v0, v1) in bands.items():
        if min(v0, v1) - 1e-4 <= v <= max(v0, v1) + 1e-4:
            return k
    raise ValueError("uv v %.4f in no band" % v)


def _grid_cut(bm):
    """Cuts every face crossing an 8-stud grid plane (world aligned), so each face lies in one cell."""
    for axis in range(3):
        lo = min(v.co[axis] for v in bm.verts)
        hi = max(v.co[axis] for v in bm.verts)
        k0, k1 = math.floor(lo / TILE) + 1, math.ceil(hi / TILE) - 1
        for k in range(k0, k1 + 1):
            no = [0.0, 0.0, 0.0]
            no[axis] = 1.0
            co = [0.0, 0.0, 0.0]
            co[axis] = k * TILE
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)


def _uv_tiles(bm, anchored=False):
    """Box-projected UVs: each face takes the plane its normal is closest to, scaled to a tile per 8 studs, offset into its cell.
    anchored (faces already under a tile, not cut to the grid): the cell is moved just enough to hold the whole face."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [i for i in range(3) if i != ax]
        cen = f.calc_center_median()
        oa, ob = math.floor(cen[a] / TILE) * TILE, math.floor(cen[b] / TILE) * TILE
        if anchored:
            ca_ = [l.vert.co[a] for l in f.loops]
            cb_ = [l.vert.co[b] for l in f.loops]
            oa = min(max(oa, max(ca_) - TILE), min(ca_))
            ob = min(max(ob, max(cb_) - TILE), min(cb_))
        for l in f.loops:
            u = (l.vert.co[a] - oa) / TILE
            v = (l.vert.co[b] - ob) / TILE
            l[uv].uv = (min(max(u, 0.0), 1.0), min(max(v, 0.0), 1.0))


def _unweld_seams(bm):
    """Welding joins every corner that coincides, so two primitives that merely touch can end up sharing an edge they wind
    the same way (or three faces on one edge): split exactly those edges apart again."""
    bm.edges.ensure_lookup_table()
    bad = []
    for e in bm.edges:
        faces = e.link_faces
        if len(faces) > 2:
            bad.append(e)
        elif len(faces) == 2:
            a, b = e.verts
            dirs = []
            for f in faces:
                for l in f.loops:
                    if l.edge == e:
                        dirs.append(l.vert == a)
            if len(dirs) == 2 and dirs[0] == dirs[1]:
                bad.append(e)
    if bad:
        bmesh.ops.split_edges(bm, edges=bad)


def _finish_mesh(name, bm, suffix, coll, materials, paving=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    _unweld_seams(bm)
    if suffix not in SINGLE and not paving:
        bm.edges.ensure_lookup_table()
        sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) >= BEVEL_ANGLE]
        if sharp:
            bmesh.ops.bevel(bm, geom=sharp, offset=BEVEL, segments=1, profile=0.5, affect="EDGES", clamp_overlap=True)
    if not paving:
        _grid_cut(bm)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-6], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    _unweld_seams(bm)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    _uv_tiles(bm, anchored=paving)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = suffix != "Crystal"
    if suffix != "Crystal":
        me.set_sharp_from_angle(angle=SMOOTH_ANGLE)
    me.materials.append(materials[suffix])
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if suffix not in SINGLE:
        m = o.modifiers.new("Weighted", "WEIGHTED_NORMAL")
        m.mode = "FACE_AREA"
        m.keep_sharp = True
    return o


def finish(obj, bands, coll, materials, single=False, base=None, paving=False):
    """obj -> its finished meshes: one per material (<obj>__<Suffix>) or, single, the whole mesh under obj's own name."""
    me = obj.data
    uv = me.uv_layers.active.data
    groups = {}
    for p in me.polygons:
        k = _band_of(uv[p.loop_indices[0]].uv[1], bands)
        suffix = SUFFIX[k]
        if suffix == "Gold" and p.normal.z > FLAT_UP:
            suffix = "GoldFlat"
        groups.setdefault(suffix, []).append(p.index)
    out = []
    base = base or obj.name
    if single:
        bm = bmesh.new()
        bm.from_mesh(me)
        out.append(_finish_mesh(base, bm, "Crystal" if base == "HB_MarketCanopy" else "Glow", coll, materials, paving=paving))
    else:
        for suffix, polys in sorted(groups.items()):
            bm = bmesh.new()
            bm.from_mesh(me)
            keep = set(polys)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
            out.append(_finish_mesh(base + "__" + suffix, bm, suffix, coll, materials, paving=paving))
    bpy.data.objects.remove(obj, do_unlink=True)
    return out


# pieces that stay one mesh (the game gives them one look: WorldBuilder.Appearance)
SINGLE_PIECES = {"HB_MarketCanopy", "HB_MarketGlow", "HB_BlacksmithCore", "HB_BlacksmithCrystal", "HB_BuySellStones", "HB_LeaderboardGlow",
                 "HB_MerchantDaisGlow", "HB_SpawnPadGlow", "HB_SquareCompassGlow"}


def materials():
    """Preview materials (renders; the FBX carries their names only): roughly what each Roblox material reads as."""
    import hub_finish as F
    looks = {
        "Marble": F._mat("pv_marble", (0.86, 0.85, 0.83, 1), 0.3, veins=(1.1, (0.74, 0.75, 0.77, 1))),
        "Shade": F._mat("pv_shade", (0.62, 0.62, 0.62, 1), 0.4, veins=(1.1, (0.52, 0.53, 0.55, 1))),
        "Lapis": F._mat("pv_lapis", (0.03, 0.06, 0.26, 1), 0.3, veins=(1.4, (0.1, 0.17, 0.45, 1))),
        "Gold": F._mat("pv_gold", (0.85, 0.6, 0.2, 1), 0.32, metal=1.0),
        "GoldFlat": F._mat("pv_goldflat", (0.78, 0.55, 0.2, 1), 0.45),
        "Slate": F._mat("pv_slate", (0.06, 0.065, 0.08, 1), 0.7),
        "Steel": F._mat("pv_steel", (0.62, 0.64, 0.68, 1), 0.3, metal=1.0),
        "Crystal": F._mat("pv_crystal", (0.6, 0.82, 1.0, 1), 0.05, alpha=0.55),
        "Glow": F._mat("pv_glow", (0.75, 0.84, 0.95, 1), 0.2, emit=((0.8, 0.9, 1.0, 1), 2.0)),
    }
    return looks


def build(names=None):
    """Builds and finishes every asset (or the named ones). Returns {asset: [objects]}, {asset: spots}."""
    global B
    img, bands = W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS)
    B = bands
    H.MARBLE_BAND, H.GOLD_BAND = bands[H.MARBLE], bands[H.GOLD]
    mats = materials()
    root = W.collection("HubDistrict")
    out, spots = {}, {}
    for asset, fn in ASSETS.items():
        if names and asset not in names:
            continue
        coll = W.collection("HD_" + asset, root)
        W.clear_collection(coll)
        pieces, sp = fn()
        objs = []
        for name, mb in pieces.items():
            if not mb.faces:
                continue
            raw = mb.object(name + "_raw", coll, None)
            raw.name = raw.data.name = name + "_raw"
            objs += finish(raw, bands, coll, mats, single=name in SINGLE_PIECES, base=name)
        out[asset], spots[asset] = objs, sp
    # the glow pieces' look: their own preview (the core is the forge's fire)
    core = bpy.data.materials.get("pv_core") or __import__("hub_finish")._mat("pv_core", (1.0, 0.45, 0.1, 1), 0.2, emit=((1.0, 0.45, 0.1, 1), 4.0))
    for objs in out.values():
        for o in objs:
            if o.name == "HB_BlacksmithCore":
                o.data.materials[0] = core
    return out, spots


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def build_paving():
    """The paving and the parapet (hub_ground), finished: {group: [objects]}."""
    global B
    import hub_ground as G
    img, bands = W.atlas_image("Hub_CelestialAtlas", 512, H.HUB_STRIPS)
    B = bands
    mats = materials()
    root = W.collection("HubDistrict")
    coll = W.collection("HD_Paving", root)
    W.clear_collection(coll)
    raws = G.paving(coll, None, bands) + [G.parapet(coll, None, bands)]
    out = {}
    for raw in raws:
        name = raw.name
        raw.name = raw.data.name = name + "_raw"
        out[name] = finish(raw, bands, coll, mats, single=name == "HB_PavingRunes", base=name, paving=name != "HB_RingParapet")
    return out

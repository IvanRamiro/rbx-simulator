"""dawnspire_kit: the architecture kit for Dawnspire's territory (2026-11-22), built on hq_kit (the hall's kit, unchanged). Plain Python (no Blender);
every function returns a Piece (material suffix -> Geo) in Roblox studs, a piece's front is -Z, its origin is its own (y = 0 at its floor / base).

New forms (the hall has square hip roofs stacked five high; each building here gets its own silhouette):
    poly_roof / poly_storey   a regular n-gon pavilion roof with the hall's S-curve, corner lift, tile rows, eave discs and gold hips (hexagon: the tea
                              pavilion; octagon: the viewing tower; twelve sides: the garden's round pavilion)
    gable_roof                a long gable roof (the exhibition hall, the corridors, the gate house) with an upswept ridge, eave fascia and tile rows
    stepped_gable             a horse-head wall: a plaster gable end that climbs in tiled steps above the roof's slope
    house                     the Master's low courtyard house: a wide single storey, a deep curved hip roof, a recessed wall behind an open veranda
    wall modules              plain / round-window / moon-gate garden wall lengths with a tiled cap; a gate wall with a small gate roof
    screen_wall               a free-standing carved screen (cloud scrolls or waves and an abstract crane form)
    arch_bridge               a stepped arched stone bridge (1-stud risers, a flat crown, carved balustrade posts) over a gap
    props                     pillar lantern, low garden lantern, incense burner, stone bench, tea table with stools, weapon rack, training post, plum-blossom
                              posts, stone lifting weights, stage, exhibition bay and the Regent's plinth with its glass case
"""
import math

import hq_kit as K
from hq_kit import (Geo, Piece, Style, box, hexa, prism, lathe, tube, lerp, lerp3, vadd, vsub, vmul, vnorm, vcross, vdot, TAU, FACE_YAW)

ST = Style()
ST.timber = "Timber"        # warm pale wood: racks, posts, benches, the corridor's rafters
ST.case = "Case"            # the glass of a display case
ST.water = "Pool"


# ======================================================================================================================
# polygon roofs
# ======================================================================================================================
def _ngon(n, R, rot):
    return [(R * math.sin(rot + TAU * i / n), -R * math.cos(rot + TAU * i / n)) for i in range(n)]


def _psurf(E, T, face, u, s, ye, yt, k, flick, lift, flare, lift_len):
    n = len(E)
    e0, e1, t0, t1 = E[face], E[(face + 1) % n], T[face], T[(face + 1) % n]
    ex, ez = lerp(e0[0], e1[0], u), lerp(e0[1], e1[1], u)
    tx, tz = lerp(t0[0], t1[0], u), lerp(t0[1], t1[1], u)
    hx, hz = lerp(ex, tx, s), lerp(ez, tz, s)
    y = ye + (yt - ye) * (s ** k)
    fs = 0.12
    if s < fs:
        y += flick * (1 - s / fs) ** 2
    L = math.hypot(e1[0] - e0[0], e1[1] - e0[1])
    dc = min(u, 1 - u) * L
    Lc = min(0.45 * L, lift_len)
    w = max(0.0, 1 - dc / Lc) ** 2
    y += lift * w * (1 - s) ** 3
    corner = e0 if u < 0.5 else e1
    cn = math.hypot(corner[0], corner[1]) or 1.0
    fl = flare * w * (1 - s) ** 2
    return (hx + corner[0] / cn * fl, y, hz + corner[1] / cn * fl)


def poly_roof(st, n, R, Rt, ye, yt, rot=0.0, detail=1, pitch=1.6, shell=0.7, rib_h=0.18, k=1.5, flick=0.7, lift=1.2, flare=0.8, lift_len=7.0,
              finial=0.0, discs=True, ribs=True, horns=True):
    """A tiled pyramid-ish roof over a regular n-gon: eave circumradius R at height ye rising through an S-curve to circumradius Rt (0: a point) at yt.
    Roles: tile (shell, ribs, eave discs), gold (hip caps, horns, finial)."""
    P = Piece()
    gt, gg = P.geo(st.tile), P.geo(st.gold)
    E, T = _ngon(n, R, rot), _ngon(n, Rt, rot)
    us = [0.0, 0.05, 0.14, 0.3, 0.5, 0.7, 0.86, 0.95, 1.0] if detail >= 2 else ([0.0, 0.08, 0.25, 0.5, 0.75, 0.92, 1.0] if detail == 1 else [0.0, 0.15, 0.5, 0.85, 1.0])
    ss = [0.0, 0.05, 0.14, 0.3, 0.55, 0.8, 1.0] if detail >= 1 else [0.0, 0.1, 0.4, 1.0]
    cv = dict(k=k, flick=flick, lift=lift, flare=flare, lift_len=lift_len)

    def S(face, u, s):
        return _psurf(E, T, face, u, s, ye, yt, **cv)

    def under(p, s):
        return (p[0], p[1] - shell * (1 - 0.25 * s), p[2])
    sh = Geo()
    for face in range(n):
        T_ = [[sh.vert(S(face, u, s)) for s in ss] for u in us]
        U_ = [[sh.vert(under(S(face, u, s), s)) for s in ss] for u in us]
        for i in range(len(us) - 1):
            for j in range(len(ss) - 1):
                sh.face(T_[i][j], T_[i][j + 1], T_[i + 1][j + 1], T_[i + 1][j])
                sh.face(U_[i][j], U_[i + 1][j], U_[i + 1][j + 1], U_[i][j + 1])
            sh.face(T_[i][0], T_[i + 1][0], U_[i + 1][0], U_[i][0])
            sh.face(T_[i + 1][-1], T_[i][-1], U_[i][-1], U_[i + 1][-1])
    sh.weld()
    sh.cull_twins()
    gt.add(sh)
    if ribs:
        for face in range(n):
            e0, e1, t0, t1 = E[face], E[(face + 1) % n], T[face], T[(face + 1) % n]
            Le, Lt = math.hypot(e1[0] - e0[0], e1[1] - e0[1]), math.hypot(t1[0] - t0[0], t1[1] - t0[1])
            m = max(3, int(round(Le / pitch)))
            s_end = 0.0
            for s_try in [x / 100 for x in range(100, -1, -2)]:
                if (Le + (Lt - Le) * s_try) / m >= 0.6:
                    s_end = s_try
                    break
            if s_end < 0.2:
                continue
            top_s = s_end - 0.02
            rs = [top_s * q for q in ((0.0, 0.12, 0.3, 0.58, 1.0) if detail >= 2 else (0.0, 0.2, 0.55, 1.0))]
            for j in range(m):
                u = (j + 0.5) / m
                pts = [S(face, u, s_) for s_ in rs]
                frames = []
                for q in range(len(rs)):
                    p_prev = S(face, u, max(0.0, rs[q] - 0.02))
                    p_next = S(face, u, min(1.0, rs[q] + 0.02))
                    along = vnorm(vsub(p_next, p_prev))
                    du = vsub(S(face, min(1.0, u + 0.004), rs[q]), S(face, max(0.0, u - 0.004), rs[q]))
                    nrm = vnorm(vcross(du, along))
                    if nrm[1] < 0:
                        nrm = vmul(nrm, -1)
                    frames.append((vnorm(vcross(along, nrm)), nrm))
                tube(gt, pts, frames, [(-0.25, -0.05), (0.25, -0.05), (0.0, rib_h)], caps=True, skip_bottom=True)
                if discs:
                    p0, p1 = S(face, u, 0.0), S(face, u, 0.05)
                    K._eave_disc(gt, p0, vnorm(vsub(p0, p1)), frames[0][1], 0.28, detail)
    for face in range(n):         # gold hip caps (and horns) down every corner
        ss_h = [0.0, 0.06, 0.16, 0.34, 0.6, 0.85, 1.0] if detail >= 1 else [0.0, 0.25, 0.6, 1.0]
        pts, frames = [], []
        for s in ss_h:
            p = S(face, 0.0, s)
            along = vnorm(vsub(S(face, 0.0, min(1.0, s + 0.02)), S(face, 0.0, max(0.0, s - 0.02))))
            right = vnorm(vcross(along, (0.0, 1.0, 0.0)))
            upn = vnorm(vcross(right, along))
            if upn[1] < 0:
                upn = vmul(upn, -1)
            pts.append(vadd(p, vmul(upn, -0.05)))
            frames.append((right, upn))
        tube(gg, pts, frames, [(-0.34, 0.0), (0.34, 0.0), (0.0, 0.44)], caps=True)
        if horns and detail >= 1:
            K._corner_horn(gg, S(face, 0.0, 0.0), S(face, 0.0, 0.03), st)
    if finial and Rt == 0:
        K._finial(gg, (0.0, yt, 0.0), finial)
    return P


def _side_frames(n, R, rot):
    """For each side of the n-gon: (yaw, centre x, centre z, length, apothem): a module built along +x with its front at z = -apothem turned by yaw."""
    out = []
    a = R * math.cos(math.pi / n)
    L = 2 * R * math.sin(math.pi / n)
    for i in range(n):
        th = rot + TAU * (i + 0.5) / n            # direction (from the centre) of the side's middle: x = R sin, z = -R cos
        cx, cz = a * math.sin(th), -a * math.cos(th)
        out.append((th, cx, cz, L, a))
    return out


def poly_storey(st, n, R, y0, wall_h, hb, sides, rot=0.0, beam=1.3, col_seg=8, col_r=0.62, br_layers=1, plinth=0.0, lat=(2, 2), drop_open=False):
    """One storey on a regular n-gon: a column at every corner, a lower and an upper beam on every side, a bracket set on every column head, and per
    side (`sides`: a string of n letters) O open, R a railing 2.2 high, W a plaster wall with a lattice window. y0 the floor."""
    P = Piece()
    gp, gw = P.geo(st.paint), P.geo(st.wall)
    ytop = y0 + wall_h
    corners = _ngon(n, R, rot)
    for ci, (x, z) in enumerate(corners):
        if drop_open and sides[ci - 1] == "O" and sides[ci] == "O":          # a column between two open sides is left out (a wide entrance)
            continue
        P.add(K.pillar(st, wall_h, r0=col_r, r1=col_r * 0.88, foot=False, seg=col_seg, detail=0), t=(x, y0, z))
    for i, (th, cx, cz, L, a) in enumerate(_side_frames(n, R, rot)):
        yaw = th                                     # a module facing -Z turned by th faces outward (x = sin th, z = -cos th)
        mod = Piece()
        b = mod.geo(st.paint)
        inner = L + 0.0           # the beams run from column centre to column centre (they sink into the columns)
        for yb0, yb1, dep in ((wall_h - beam, wall_h - beam + 0.6, 0.55), (wall_h - beam + 0.6, wall_h, 0.45)):
            box(b, -inner / 2, inner / 2, yb0, yb1, -dep, dep, "TBNESW")
        kind = sides[i]
        if kind == "R":
            gm_, gg_ = mod.geo(st.stone), mod.geo(st.gold)
            ri = L / 2 - col_r * 0.5
            box(gm_, -ri, ri, 0.0, 1.7, -0.32, 0.32, "TNESW")
            box(gg_, -ri - 0.05, ri + 0.05, 1.7, 1.88, -0.4, 0.4, "TBNESW")
            box(gm_, -ri + 0.7, ri - 0.7, 0.55, 1.35, -0.38, -0.32, "TNESW")
        elif kind == "W":
            g1 = mod.geo(st.wall)
            wi = L - 2 * col_r - 0.1
            ow, oy0, oy1 = wi - 1.6, wall_h * 0.28, wall_h - beam - 0.5
            K._wall_with_opening(g1, -wi / 2, wi / 2, 0.0, wall_h - beam, 0.0, 0.7, -ow / 2, ow / 2, oy0, oy1)
            mod.add(K.lattice(st, ow - 0.1, oy1 - oy0 - 0.1, nx=lat[0] + 1, ny=lat[1], frame=0.2, bar=0.1), t=(0.0, oy0 + 0.05, 0.0))
        # moved up to the storey's height for the beams, the walls/rails sit on the floor: shift the lot by y0 (the beams were built at absolute y)
        P.add(_shift_up(mod, y0, wall_h), t=(cx, 0.0, cz), yaw=yaw)
        if hb > 0:
            P.add(K.bracket_set(st, layers=br_layers, w=min(hb * 0.75, 1.6), h=hb, reach=min(L * 0.3, 1.9), detail=0), t=(corners[i][0], ytop, corners[i][1]), yaw=rot + TAU * i / n)
    if plinth > 0:
        gs = P.geo(st.stone2)
        prism(gs, _ngon(n, R + 1.1, rot), y0 - plinth, y0, "T")
    return P


def _shift_up(mod, y0, wall_h):
    """The beams in `mod` are authored at absolute height (0 .. wall_h); walls and rails start at 0: all of it is lifted by y0."""
    out = Piece()
    out.add(mod, t=(0.0, y0, 0.0))
    return out


# ======================================================================================================================
# gable roofs and the horse-head wall
# ======================================================================================================================
def gable_roof(st, A, D, ye, yt, detail=1, pitch=1.5, shell=0.7, rib_h=0.18, k=1.45, flick=0.75, discs=True, ridge=True, rise_ends=0.0, horns=True,
               fascia=True, shell_only=False):
    """A gable roof over a rectangle: eave lines at z = -D and +D (height ye, upturned by `flick` at the edge) rising on an S-curve to the ridge (z = 0,
    height yt) along x from -A to A; the gable ends are vertical. Roles: tile, paint (the eave fascia), gold (ridge cap, the upswept ridge ends)."""
    P = Piece()
    gt, gp, gg = P.geo(st.tile), P.geo(st.paint), P.geo(st.gold)
    us = [i / max(2, int(round(2 * A / 2.2))) for i in range(max(2, int(round(2 * A / 2.2))) + 1)] if detail >= 2 else [0.0, 0.5, 1.0]
    ss = [0.0, 0.06, 0.16, 0.34, 0.6, 0.85, 1.0] if detail >= 1 else [0.0, 0.15, 0.5, 1.0]

    def S(side, u, s):
        x = lerp(-A, A, u)
        z = side * D * (1 - s)
        y = ye + (yt - ye) * (s ** k)
        if s < 0.12:
            y += flick * (1 - s / 0.12) ** 2
        return (x, y, z)

    def under(p, s):
        return (p[0], p[1] - shell * (1 - 0.2 * s), p[2])
    sh = Geo()
    arrs = {}
    for side in (-1, 1):
        T_ = [[sh.vert(S(side, u, s)) for s in ss] for u in us]
        U_ = [[sh.vert(under(S(side, u, s), s)) for s in ss] for u in us]
        arrs[side] = (T_, U_)
        for i in range(len(us) - 1):
            for j in range(len(ss) - 1):
                if side < 0:
                    sh.face(T_[i][j], T_[i][j + 1], T_[i + 1][j + 1], T_[i + 1][j])
                    sh.face(U_[i][j], U_[i + 1][j], U_[i + 1][j + 1], U_[i][j + 1])
                else:
                    sh.face(T_[i][j], T_[i + 1][j], T_[i + 1][j + 1], T_[i][j + 1])
                    sh.face(U_[i][j], U_[i][j + 1], U_[i + 1][j + 1], U_[i + 1][j])
            sh.face(T_[i + 1][0], U_[i + 1][0], U_[i][0], T_[i][0]) if side < 0 else sh.face(U_[i][0], U_[i + 1][0], T_[i + 1][0], T_[i][0])
        # the two gable ends of this side
        for i, end in ((0, -1), (len(us) - 1, 1)):
            for j in range(len(ss) - 1):
                if (side < 0) == (end < 0):
                    sh.face(T_[i][j], U_[i][j], U_[i][j + 1], T_[i][j + 1])
                else:
                    sh.face(T_[i][j], T_[i][j + 1], U_[i][j + 1], U_[i][j])
    sh.weld()
    sh.cull_twins()
    if shell_only:
        return sh
    gt.add(sh)
    for side in (-1, 1):
        m = max(3, int(round(2 * A / pitch)))
        rs = [0.0, 0.1, 0.3, 0.6, 0.93] if detail >= 1 else [0.0, 0.4, 0.93]
        for j in range(m):
            u = (j + 0.5) / m
            pts = [S(side, u, s_) for s_ in rs]
            frames = []
            for q in range(len(rs)):
                along = vnorm(vsub(S(side, u, min(1.0, rs[q] + 0.02)), S(side, u, max(0.0, rs[q] - 0.02))))
                nrm = vnorm(vcross((1.0, 0.0, 0.0), along)) if side > 0 else vnorm(vcross(along, (1.0, 0.0, 0.0)))
                if nrm[1] < 0:
                    nrm = vmul(nrm, -1)
                frames.append((vnorm(vcross(along, nrm)), nrm))
            tube(gt, pts, frames, [(-0.24, -0.05), (0.24, -0.05), (0.0, rib_h)], caps=True, skip_bottom=True)
            if discs:
                p0, p1 = S(side, u, 0.0), S(side, u, 0.05)
                K._eave_disc(gt, p0, vnorm(vsub(p0, p1)), frames[0][1], 0.27, detail)
    if fascia:
        for side in (-1, 1):
            z0 = side * D
            box(gp, -A + 0.1, A - 0.1, ye - shell - 0.05, ye - shell + 0.55, z0 - (0.12 if side < 0 else 0.5), z0 + (0.5 if side < 0 else 0.12), "TBNESW")
    if ridge:
        box(gg, -A + 0.03, A - 0.03, yt - 0.18, yt + 0.62, -0.5, 0.5, "TBNESW")
        if horns:
            for sx in (-1, 1):
                K._ridge_end(gg, (sx * A, yt + 0.62, 0.0), sx)
    return P


def stepped_gable(st, D, y_eave, y_ridge, steps=3, thick=1.1, x=0.0):
    """A horse-head gable wall: a plaster slab in the plane x = `x` (thickness `thick`) spanning z = -D..D whose top climbs from the eave line in
    `steps` tiled steps (each side) to above the ridge; each step is capped by a small tiled hip. Symmetric in z. Roles: wall, tile, gold."""
    P = Piece()
    gw, gt, gg = P.geo(st.wall), P.geo(st.tile), P.geo(st.gold)
    h0 = y_eave - 3.4
    wd = D / steps
    cols = []
    for j in range(2 * steps):
        z0, z1 = -D + wd * j, -D + wd * (j + 1)
        idx = min(steps - 1, int((D - abs((z0 + z1) / 2)) / wd))
        top = y_eave + (y_ridge + 1.0 - y_eave) * ((idx + 1) / steps) + 0.35
        cols.append([z0, z1, top])
    for c in cols:
        box(gw, x - thick / 2, x + thick / 2, h0, c[2], c[0], c[1], "TBNESW")
        z0, z1, top = c
        hexa(gt, [(x - thick / 2 - 0.4, z0 + 0.05), (x + thick / 2 + 0.4, z0 + 0.05), (x + thick / 2 + 0.4, z1 - 0.05), (x - thick / 2 - 0.4, z1 - 0.05)], top,
             [(x - 0.12, z0 + 0.3), (x + 0.12, z0 + 0.3), (x + 0.12, z1 - 0.3), (x - 0.12, z1 - 0.3)], top + 0.6, "TB0123")
        box(gg, x - thick / 2 - 0.42, x + thick / 2 + 0.42, top - 0.04, top + 0.06, z0 + 0.02, z1 - 0.02, "TBNESW")
    return P


# ======================================================================================================================
# helpers: extrusions along x, a wall with a round hole, sloped-bottom columns
# ======================================================================================================================
def prism_x(g, ring_yz, x0, x1):
    """Extrudes a convex polygon given in (y, z) along x from x0 to x1 (caps fanned from the centroid)."""
    n = len(ring_yz)
    area = sum(ring_yz[i][0] * ring_yz[(i + 1) % n][1] - ring_yz[(i + 1) % n][0] * ring_yz[i][1] for i in range(n))
    ring = ring_yz if area > 0 else list(reversed(ring_yz))
    a = [g.vert((x0, y, z)) for y, z in ring]
    b = [g.vert((x1, y, z)) for y, z in ring]
    cy = sum(p[0] for p in ring) / n
    cz = sum(p[1] for p in ring) / n
    ca, cb = g.vert((x0, cy, cz)), g.vert((x1, cy, cz))
    for i in range(n):
        j = (i + 1) % n
        g.face(a[i], b[i], b[j], a[j])
        g.face(ca, a[i], a[j])
        g.face(cb, b[j], b[i])
    K._orient_solid(g, len(g.f) - 3 * n)


def sloped_column(g, xa, xb, ya, yb, yt, z0, z1, ytb=None):
    """A solid column between x = xa and xb whose bottom runs from ya (at xa) to yb (at xb) and whose top is flat at yt (or ytb at xb)."""
    ytb = yt if ytb is None else ytb
    p = [g.vert((xa, ya, z0)), g.vert((xb, yb, z0)), g.vert((xb, yb, z1)), g.vert((xa, ya, z1)),
         g.vert((xa, yt, z0)), g.vert((xb, ytb, z0)), g.vert((xb, ytb, z1)), g.vert((xa, yt, z1))]
    g.face(p[0], p[3], p[2], p[1])        # bottom
    g.face(p[4], p[5], p[6], p[7])        # top
    g.face(p[0], p[1], p[5], p[4])        # z0 side
    g.face(p[2], p[3], p[7], p[6])        # z1 side
    g.face(p[3], p[0], p[4], p[7])        # xa end
    g.face(p[1], p[2], p[6], p[5])        # xb end
    K._orient_solid(g, len(g.f) - 6)


def wall_round_hole(g, x0, x1, y0, y1, cx, cy, r, z0, z1, seg=16):
    """A slab x0..x1, y0..y1, z0..z1 (facing -Z) with a round hole through it (centre cx, cy, radius r): front and back faces are fanned between the
    circle and the outline, the hole's inside and the four outer faces close it."""
    angs = sorted({TAU * k / seg for k in range(seg)} | {math.atan2(y1 - cy, x1 - cx) % TAU, math.atan2(y1 - cy, x0 - cx) % TAU,
                                                           math.atan2(y0 - cy, x0 - cx) % TAU, math.atan2(y0 - cy, x1 - cx) % TAU})

    def hit(a):
        c, s = math.cos(a), math.sin(a)
        t = 1e9
        if c > 1e-9:
            t = min(t, (x1 - cx) / c)
        if c < -1e-9:
            t = min(t, (x0 - cx) / c)
        if s > 1e-9:
            t = min(t, (y1 - cy) / s)
        if s < -1e-9:
            t = min(t, (y0 - cy) / s)
        return cx + c * t, cy + s * t
    m = len(angs)
    cf = [g.vert((cx + r * math.cos(a), cy + r * math.sin(a), z0)) for a in angs]
    cb = [g.vert((cx + r * math.cos(a), cy + r * math.sin(a), z1)) for a in angs]
    of = [g.vert((*hit(a), z0)) for a in angs]
    ob = [g.vert((*hit(a), z1)) for a in angs]
    for i in range(m):
        j = (i + 1) % m
        g.face(cf[i], of[i], of[j], cf[j])           # front (faces -z): counter-clockwise seen from -z
        g.face(cb[j], ob[j], ob[i], cb[i])           # back
        g.face(cf[j], cb[j], cb[i], cf[i])           # the hole's inside
        g.face(of[i], ob[i], ob[j], of[j])           # the outline's outer rim
    K._orient_solid(g, len(g.f) - 4 * m)


def _spiral(cx, cy, r0, turns, n=22, cw=1.0, a0=0.0, shrink=0.88):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + cw * TAU * turns * t
        r = r0 * (1.0 - shrink * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def relief_tube(g, pts2, z, rad=0.12, sect=5, taper=True):
    """A carved ribbon along a 2D path in the xy plane at depth z (facing -z), a small round section tapering toward the end."""
    n = len(pts2)
    centres = [(p[0], p[1], z) for p in pts2]
    frames = []
    for i in range(n):
        tg = vnorm(vsub(centres[min(i + 1, n - 1)], centres[max(i - 1, 0)]))
        rt = vnorm(vcross(tg, (0.0, 0.0, 1.0)))
        sc = rad * (1.0 - 0.55 * i / (n - 1)) if taper else rad
        frames.append((vmul(rt, sc), (0.0, 0.0, -sc)))
    sec = [(math.cos(TAU * k / sect), math.sin(TAU * k / sect)) for k in range(sect)]
    tube(g, centres, frames, sec, caps=True)


# ======================================================================================================================
# garden walls
# ======================================================================================================================
def _wall_core(P, st, L, H, plinth=0.8, t=0.9):
    gs, gm = P.geo(st.stone2), P.geo(st.stone)
    box(gs, -L / 2, L / 2, -1.5, plinth, -t / 2 - 0.2, t / 2 + 0.2, "TNESW")
    return t


def _wall_cap(P, st, L, H, t=0.9):
    gt, gg = P.geo(st.tile), P.geo(st.gold)
    ring = [(H, -t / 2 - 0.22), (H, t / 2 + 0.22), (H + 0.3, t / 2 + 0.08), (H + 0.85, 0.28), (H + 0.85, -0.28), (H + 0.3, -t / 2 - 0.08)]
    prism_x(gt, ring, -L / 2, L / 2)
    box(gg, -L / 2 + 0.03, L / 2 - 0.03, H + 0.8, H + 0.95, -0.3, 0.3, "TBNESW")
    nb = int(L // 3.0)
    for i in range(nb):                       # a few eave-end tile bumps along the cap's lower front edge (centred: the wall is symmetric)
        x = (i - (nb - 1) / 2.0) * 3.0
        box(gt, x - 0.3, x + 0.3, H - 0.14, H + 0.1, -t / 2 - 0.3, -t / 2 - 0.2, "TNESW")


def _pilaster(P, st, x, H):
    gm = P.geo(st.stone)
    box(gm, x - 0.4, x + 0.4, 0.0, H + 0.06, -0.65, 0.65, "TNESW")
    box(P.geo(st.gold), x - 0.46, x + 0.46, H - 0.2, H - 0.05, -0.7, 0.7, "TBNESW")


def wall_plain(st=ST, L=12.0, H=5.0):
    P = Piece()
    t = _wall_core(P, st, L, H)
    gw = P.geo(st.wall)
    box(gw, -L / 2 + 0.4, L / 2 - 0.4, 0.7, H, -t / 2, t / 2, "TBNESW")
    # two recessed panels' gold line on the face
    gg = P.geo(st.gold)
    for sx in (-1, 1):
        box(gg, sx * (L / 4) - L * 0.18, sx * (L / 4) + L * 0.18, 2.4, 2.46, -t / 2 - 0.03, -t / 2, "TBN")
    for x in (-L / 2 + 0.4, L / 2 - 0.4):
        _pilaster(P, st, x, H)
    _wall_cap(P, st, L, H, t)
    return P


def wall_window(st=ST, L=12.0, H=5.0, r=1.85):
    P = Piece()
    t = _wall_core(P, st, L, H)
    gw, gm, gg = P.geo(st.wall), P.geo(st.stone), P.geo(st.gold)
    seg = L / 2
    for sx in (-1, 1):
        cx = sx * (L / 4)
        wall_round_hole(gw, cx - seg / 2 + (0.4 if sx < 0 else 0.0), cx + seg / 2 - (0.4 if sx > 0 else 0.0), 0.7, H, cx, 3.0, r, -t / 2, t / 2, seg=12)
        flat_ring(gm, cx, 3.0, r + 0.3, 0.34, -t / 2 - 0.02, -1)            # a marble frame ring on each face (flat, one-sided)
        flat_ring(gm, cx, 3.0, r + 0.3, 0.34, t / 2 + 0.02, 1)
        box_bar(P.geo(st.paint), (cx - r + 0.1, 3.0), (cx + r - 0.1, 3.0), 0.09, 0.09)           # one cross bar: the lattice's spine
        box_bar(P.geo(st.paint), (cx, 3.0 - r + 0.1), (cx, 3.0 + r - 0.1), 0.09, 0.09)
    for x in (-L / 2 + 0.4, L / 2 - 0.4):
        _pilaster(P, st, x, H)
    _wall_cap(P, st, L, H, t)
    return P


def flat_ring(g, cx, cy, r_out, width, z, toward=-1, seg=14):
    """A single-sided flat ring (annulus) in the plane z, its face looking toward -z (toward=-1) or +z."""
    ro, ri = r_out, r_out - width
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        q = [g.vert((cx + ro * math.cos(a0), cy + ro * math.sin(a0), z)), g.vert((cx + ro * math.cos(a1), cy + ro * math.sin(a1), z)),
             g.vert((cx + ri * math.cos(a1), cy + ri * math.sin(a1), z)), g.vert((cx + ri * math.cos(a0), cy + ri * math.sin(a0), z))]
        if toward < 0:
            g.face(q[0], q[3], q[2], q[1])
        else:
            g.face(q[0], q[1], q[2], q[3])


def lathe_ring(g, cx, cy, r_out, width, zc, depth=0.3):
    """A ring (annulus) in the plane z = zc around (cx, cy) as a solid of the given depth, centred on zc; the ring is made on both faces of the wall."""
    for sgn in (-1, 1):
        K.lathe_xy(g, cx, cy, r_out, width, depth, 16, sgn * zc if sgn < 0 else sgn * zc)


def box_bar(g, a, b, w, d):
    """A thin bar in the wall's plane from a to b (xy), w wide, d deep (centred on z = 0)."""
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    ca, sa = math.cos(ang), math.sin(ang)
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    hw = w / 2
    ring = [(cx - ca * ln / 2 - sa * hw, cy - sa * ln / 2 + ca * hw), (cx + ca * ln / 2 - sa * hw, cy + sa * ln / 2 + ca * hw),
            (cx + ca * ln / 2 + sa * hw, cy + sa * ln / 2 - ca * hw), (cx - ca * ln / 2 + sa * hw, cy - sa * ln / 2 - ca * hw)]
    K._slab_xy(g, ring, -d / 2, d / 2)


def wall_moon(st=ST, L=12.0, H=7.6, r=3.1):
    """The moon-gate wall: a round doorway (centre 0.55 + r over the floor so its sill is a half-stud step), a marble ring with a gold band."""
    P = Piece()
    t = _wall_core(P, st, L, H)
    gw, gm, gg, ga = P.geo(st.wall), P.geo(st.stone), P.geo(st.gold), P.geo(st.paint)
    cy = 0.25 + r                                  # the circle's bottom lies 0.3 under the sill's top: the sill fills it, the doorway is 2.6 wide at the sill
    wall_round_hole(gw, -L / 2 + 0.4, L / 2 - 0.4, 0.0, H, 0.0, cy, r, -t / 2, t / 2, seg=20)
    box(gm, -r - 0.7, r + 0.7, 0.0, 0.55, -t / 2 - 0.38, t / 2 + 0.38, "TNESW")           # the sill
    for sgn in (-1, 1):
        K.lathe_xy(gm, 0.0, cy, r + 0.52, 0.5, 0.28, 20, sgn * (t / 2 + 0.02))
        K.lathe_xy(gg, 0.0, cy, r - 0.0, 0.1, 0.1, 20, sgn * (t / 2 + 0.3))
    for x in (-L / 2 + 0.4, L / 2 - 0.4):
        _pilaster(P, st, x, H)
    _wall_cap(P, st, L, H, t)
    return P


def wall_gate(st=ST, L=24.0, H=5.0, gate=8.0, gate_h=6.6):
    """The garden's cross wall: a central gateway (8 wide) under a small hip gate roof with two azure posts, a round window in each side panel."""
    P = Piece()
    half = L / 2
    side = (half - gate / 2)           # each side panel's length
    for sgn in (-1, 1):
        w = wall_window(st, L=side, H=H, r=1.7)
        # the window module has two windows: keep it simple and use a plain wall for narrow sides
        pan = wall_plain(st, L=side, H=H) if side < 9 else w
        P.add(pan, t=(sgn * (gate / 2 + side / 2), 0.0, 0.0))
    gp, gm, gg, gs = P.geo(st.paint), P.geo(st.stone), P.geo(st.gold), P.geo(st.stone2)
    for sgn in (-1, 1):
        x = sgn * (gate / 2 + 0.2)
        box(gm, x - 0.75, x + 0.75, 0.0, gate_h, -0.9, 0.9, "TNESW")
        box(gg, x - 0.85, x + 0.85, gate_h - 0.3, gate_h - 0.1, -1.0, 1.0, "TBNESW")
        box(gs, x - 0.95, x + 0.95, -1.5, 0.5, -1.1, 1.1, "TNESW")
    box(gp, -gate / 2 - 0.9, gate / 2 + 0.9, gate_h, gate_h + 0.9, -0.8, 0.8, "TBNESW")
    box(gg, -gate / 2 - 0.9, gate / 2 + 0.9, gate_h + 0.9, gate_h + 1.0, -0.9, 0.9, "TBNESW")
    roof = K.roof(st, gate / 2 + 3.2, 3.2, gate / 2 - 2.0, 0.0, gate_h + 1.0, gate_h + 3.4, detail=0, pitch=1.9, rafters=False, discs=False)
    P.add(roof)
    return P


# ======================================================================================================================
# the Master's house
# ======================================================================================================================
def house(st=ST, a=20.0, d=7.0, nbx=5, wall=6.4, hb=1.9, o=5.5, rise=5.2, ridge=12.5):
    """The Master's courtyard house, origin at the middle of its floor line (y = 0 the terrace's floor; the floor itself is 1 stud up on a podium): five bays
    (a = 20, 8 each), two deep, an open veranda in front (the columns of the front row, a recessed wall of lattice doors set 4.2 back), plaster side
    and rear walls with lattice windows, brackets on every column head, one deep curved hip roof."""
    P = Piece()
    gs, gm, gg, gp, gw = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold), P.geo(st.paint), P.geo(st.wall)
    # podium: granite foot, a marble top 1 stud over the terrace's floor, three steps' worth at the middle front (one riser, 1 stud)
    box(gs, -a - 2.4, a + 2.4, -3.0, 0.3, -d - 2.6, d + 1.6, "TNESW")
    box(gm, -a - 2.1, a + 2.1, 0.3, 1.0, -d - 2.3, d + 1.3, "TNESW")
    box(gg, -a - 2.14, a + 2.14, 0.62, 0.74, -d - 2.34, d + 1.34, "TBNESW")
    box(gm, -4.5, 4.5, 0.0, 0.3, -d - 4.0, -d - 2.3, "TNESW")           # the entrance step, one riser (the podium's own 1 stud and this 0.3 less 0.7 ...)
    box(gm, -4.5, 4.5, 0.3, 1.0, -d - 3.6, -d - 2.3, "TNESW")
    y0 = 1.0
    body = K.storey(st, a, d, y0, wall, hb, nbx, 2, open_faces=("N",), layers=1, mids=0, br_detail=0, col_detail=1, col_seg=10, beam=1.5, lat_cols=3, lat_rows=2)
    P.add(body)
    # the recessed front wall (set back 4.2 from the column line): a doorway 6.4 wide in the middle bay, lattice screens in the next bays, windows in the ends
    zf = -d + 4.2
    top = y0 + wall - 1.5
    wall_run(gw, -a + 0.9, a - 0.9, zf, y0, top, [(-3.2, 3.2, y0, top), (-11.1, -4.9, y0, top), (4.9, 11.1, y0, top), (-19.1, -12.9, y0 + 2.6, top - 0.6),
                                                       (12.9, 19.1, y0 + 2.6, top - 0.6)])
    scr = K.lattice(st, 6.2, top - y0, nx=3, ny=5, frame=0.26, bar=0.11)
    for x in (-8.0, 8.0):
        P.add(scr, t=(x, y0, zf - 0.05))
    win = K.lattice(st, 6.2, top - 0.6 - y0 - 2.6, nx=3, ny=2, frame=0.22, bar=0.1)
    for x in (-16.0, 16.0):
        P.add(win, t=(x, y0 + 2.6, zf - 0.05))
    leaf = K.door_leaf(st, 3.1, top - y0 - 0.2, studs=(2, 2))
    P.add(leaf, t=(-3.2, y0, zf + 0.4), yaw=math.pi)
    P.add(leaf, t=(3.2, y0, zf + 0.4), yaw=math.pi, mx=True)
    # a ceiling
    box(gp, -a + 1.0, a - 1.0, y0 + wall - 1.6, y0 + wall - 1.4, zf + 0.5, d - 0.6, "B")
    # the roof (a hip roof with a ridge; its curve is gentler and its eaves flatter than the hall's tiers)
    ye = y0 + wall + hb * 0.55
    P.add(K.roof(st, a + o, d + o, ridge, 0.0, ye, ye + rise, detail=1, pitch=3.0, rafters=False, k=1.3, flick=0.9, lift=1.7, flare=1.1, lift_len=9.0, ridge_horns=True))
    return P


def wall_run(g, x0, x1, z, y0, y1, openings=(), t=0.9):
    """Plaster along x at depth z with rectangular openings [(xa, xb, ya, yb)]."""
    cur = x0
    for (xa, xb, ya, yb) in sorted(openings):
        if xa > cur:
            box(g, cur, xa, y0, y1, z - t / 2, z + t / 2, "TBNESW")
        if ya > y0:
            box(g, xa, xb, y0, ya, z - t / 2, z + t / 2, "TNESW")
        if yb < y1:
            box(g, xa, xb, yb, y1, z - t / 2, z + t / 2, "TBNESW")
        cur = xb
    if cur < x1:
        box(g, cur, x1, y0, y1, z - t / 2, z + t / 2, "TBNESW")


def wing(st=ST, a=9.0, d=5.0, wall=5.2, hb=1.5, o=4.2, rise=4.0):
    """A side wing of the Master's court: three bays of 6, an open veranda on the N face (turn it 90 degrees to face the court), a doorway in the middle bay,
    lattice windows in the others, plaster elsewhere, a hip roof."""
    P = Piece()
    gs, gm, gg = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold)
    box(gs, -a - 2.0, a + 2.0, -3.0, 0.3, -d - 2.4, d + 1.4, "TNESW")
    box(gm, -a - 1.8, a + 1.8, 0.3, 1.0, -d - 2.2, d + 1.2, "TNESW")
    box(gg, -a - 1.84, a + 1.84, 0.62, 0.74, -d - 2.24, d + 1.24, "TBNESW")
    y0 = 1.0
    P.add(K.storey(st, a, d, y0, wall, hb, 3, 1, open_faces=("N",), layers=1, mids=0, br_detail=0, col_detail=0, col_seg=8, lat_cols=2, lat_rows=2))
    zf = -d + 2.4
    gw = P.geo(st.wall)
    top = y0 + wall - 1.5
    wall_run(gw, -a + 0.9, a - 0.9, zf, y0, top, [(-2.6, 2.6, y0, top), (-8.0, -4.0, y0 + 2.4, top - 0.5), (4.0, 8.0, y0 + 2.4, top - 0.5)])
    for x in (-6.0, 6.0):
        P.add(K.lattice(st, 4.0, top - 0.5 - y0 - 2.4, nx=3, ny=2, frame=0.2, bar=0.1), t=(x, y0 + 2.4, zf - 0.05))
    ye = y0 + wall + hb * 0.55
    P.add(K.roof(st, a + o, d + o, a - 4.2, 0.0, ye, ye + rise, detail=0, pitch=2.7, rafters=False, discs=False, k=1.3, flick=0.8, lift=1.4, flare=0.9))
    return P


# ======================================================================================================================
# pavilions and the tower
# ======================================================================================================================
def tea_pavilion(st=ST, n=6, R=5.6, wall=6.0, hb=1.6, sides="ORRORR"):
    """The tea terrace's hexagonal pavilion (origin: the middle of its floor; y = 0 the terrace's floor, the floor is 1 stud up): six columns, railings on
    four sides, an open way through on two, a hexagonal hip roof with a gold gourd finial."""
    P = Piece()
    gs, gm, gg = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold)
    rot = -math.pi / n
    prism(gs, _ngon(n, R + 1.9, rot), -3.0, 0.45, "T")
    prism(gm, _ngon(n, R + 1.5, rot), 0.4, 1.0, "T")
    y0 = 1.0
    P.add(poly_storey(st, n, R, y0, wall, hb, sides, rot=rot, col_seg=10, col_r=0.66))
    ye = y0 + wall + hb * 0.55
    P.add(poly_roof(st, n, R + 3.6, 0.0, ye, ye + 5.6, rot=rot, detail=1, pitch=2.9, finial=3.2, k=1.4, flick=0.9, lift=1.5, flare=1.0, lift_len=6.0))
    # a ceiling disc
    prism(P.geo(st.paint), _ngon(n, R - 0.6, rot), y0 + wall - 1.55, y0 + wall - 1.35, "B")
    return P


def round_pavilion(st=ST, n=12, R=4.7, wall=5.4, hb=0.0):
    """The garden's round pavilion: twelve slender columns on a circle, a low railing between all but two, a round conical roof with a gold finial."""
    P = Piece()
    gs, gm = P.geo(st.stone2), P.geo(st.stone)
    rot = -math.pi / n
    prism(gs, _ngon(n, R + 2.1, rot), -3.0, 0.45, "T")
    prism(gm, _ngon(n, R + 1.7, rot), 0.4, 1.0, "T")
    sides = "OORRROOORRRO"[:n]
    y0 = 1.0
    P.add(poly_storey(st, n, R, y0, wall, hb, sides, rot=rot, col_seg=8, col_r=0.48, br_layers=1, drop_open=True))
    ye = y0 + wall + hb * 0.55
    P.add(poly_roof(st, n, R + 2.9, 0.0, ye, ye + 5.2, rot=rot, detail=0, pitch=3.0, finial=3.0, k=1.5, flick=0.8, lift=0.9, flare=0.5, lift_len=4.0, horns=False, discs=False))
    prism(P.geo(st.paint), _ngon(n, R - 0.5, rot), y0 + wall - 1.4, y0 + wall - 1.2, "B")
    return P


def tower(st=ST):
    """The training yard's viewing tower: an octagon of three tiers (an open ground floor with railings and three ways in, latticed upper storeys, an open
    gallery under the top roof), upswept roofs, a gold finial; about 32 studs over its floor. Origin: the middle of its floor."""
    P = Piece()
    gs, gm = P.geo(st.stone2), P.geo(st.stone)
    n = 8
    rot = -math.pi / n
    prism(gs, _ngon(n, 11.0, rot), -3.0, 0.45, "T")
    prism(gm, _ngon(n, 9.2, rot), 0.4, 1.0, "T")
    tiers = [dict(R=7.2, wall=5.6, hb=1.5, o=3.4, rise=3.6, sides="OOROOORO", detail=0, lat=(2, 2)),
             dict(R=5.7, wall=4.4, hb=0.0, o=3.0, rise=3.3, sides="WOWOWOWO", detail=0, lat=(2, 2)),
             dict(R=4.4, wall=3.8, hb=0.0, o=2.6, rise=5.0, sides="OROROROR", detail=0, lat=(2, 1))]
    y = 1.0
    for i, t in enumerate(tiers):
        P.add(poly_storey(st, n, t["R"], y, t["wall"], t["hb"], t["sides"], rot=rot, col_seg=8 if i == 0 else 6, col_r=0.62 if i == 0 else 0.5, lat=t["lat"]))
        ye = y + t["wall"] + t["hb"] * 0.55
        top = tiers[i + 1]["R"] if i + 1 < len(tiers) else 0.0
        P.add(poly_roof(st, n, t["R"] + t["o"], top, ye, ye + t["rise"], rot=rot, detail=t["detail"], pitch=3.2, finial=3.6 if top == 0 else 0.0, k=1.4, flick=0.8,
                        lift=1.3, flare=0.9, lift_len=6.0, discs=(i == 0), horns=(i != 1)))
        y = ye + t["rise"]
    return P


def corridor(st=ST, L=8.0, W=5.2, h=4.6):
    """A covered corridor module (the tea terrace's): two rows of columns every 4, a gable roof along x, a lattice panel between the rear columns, an open
    front. Origin: the middle of its floor line, y = 0 the floor; length L along x."""
    P = Piece()
    gp, gm, gs, gw = P.geo(st.paint), P.geo(st.stone), P.geo(st.stone2), P.geo(st.timber)
    box(gs, -L / 2, L / 2, -2.0, 0.0, -W / 2 - 0.7, W / 2 + 0.7, "TNESW")
    n = int(L // 4) + 1
    for i in range(n):
        for z in (-W / 2, W / 2):
            P.add(K.pillar(st, h, r0=0.46, r1=0.4, foot=False, seg=8, detail=0), t=(-L / 2 + i * (L / (n - 1)), 0.0, z))
    for z in (-W / 2, W / 2):
        box(gp, -L / 2, L / 2, h - 0.2, h + 0.55, z - 0.4, z + 0.4, "TBNESW")
    for i in range(n - 1):
        x = -L / 2 + (i + 0.5) * (L / (n - 1))
        P.add(K.lattice(st, L / (n - 1) - 1.1, h - 1.7, nx=3, ny=2, frame=0.16, bar=0.09), t=(x, 0.5, W / 2))
        box(gm, x - 1.4, x + 1.4, 0.0, 1.0, W / 2 - 0.6, W / 2 + 0.6, "TNESW")           # a low stone sill under each lattice
    P.add(gable_roof(st, L / 2 + 0.2, W / 2 + 2.3, h + 0.6, h + 2.9, detail=1, pitch=1.7, k=1.35, flick=0.55, ridge=True, horns=False))
    return P


def yard_gate(st=ST, a=10.0, d=3.0, wall=7.0, hb=1.8):
    """The training yard's gate house: 3 bays (6, 8, 6), the middle one an open passage with its two door leaves thrown back, closed side bays with lattice
    windows, one gable roof with an upswept ridge. Origin: the middle of its floor line (y = 0 the terrace's floor, floor 0.5 up)."""
    P = Piece()
    gs, gm, gg, gp, gw = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold), P.geo(st.paint), P.geo(st.wall)
    box(gs, -a - 2.0, a + 2.0, -3.0, 0.2, -d - 2.4, d + 1.8, "TNESW")
    box(gm, -a - 1.7, a + 1.7, 0.2, 0.5, -d - 2.1, d + 1.5, "TNESW")
    y0 = 0.5
    xs = [-a, -4.0, 4.0, a]
    for x in xs:
        for z in (-d, d):
            P.add(K.pillar(st, wall, foot=True, seg=8, detail=0), t=(x, y0, z))
    top = y0 + 1.0 + wall - 1.5
    for z in (-d, d):
        box(gp, -a - 0.4, a + 0.4, y0 + 1.0 + wall - 1.5, y0 + 1.0 + wall - 0.8, z - 0.55, z + 0.55, "TBNESW")
        box(gp, -a - 0.4, a + 0.4, y0 + 1.0 + wall - 0.8, y0 + 1.0 + wall, z - 0.45, z + 0.45, "TBNESW")
    for sx in (-1, 1):                       # the side bays: a plaster wall with a lattice window on the front and back, solid sides
        x0, x1 = (-a, -4.0) if sx < 0 else (4.0, a)
        for z in (-d, d):
            wall_run(gw, x0 + 0.9, x1 - 0.9, z, y0 + 1.0, top, [(x0 + 1.5, x1 - 1.5, y0 + 3.4, top - 0.8)])
            P.add(K.lattice(st, (x1 - x0) - 3.2, top - 0.8 - y0 - 3.4, nx=3, ny=2, frame=0.2, bar=0.1), t=((x0 + x1) / 2, y0 + 3.4, z))
        box(gw, sx * a - 0.45, sx * a + 0.45, y0 + 1.0, top, -d + 0.9, d - 0.9, "TBNESW")
    leaf = K.door_leaf(st, 3.0, top - y0 - 1.2)
    for sx in (-1, 1):                       # the passage's two leaves thrown back against the inner faces of the middle columns' walls
        P.add(leaf, t=(sx * 3.9, y0 + 1.0, -d + 0.1), yaw=math.pi, mx=(sx > 0)) if False else None
    ye = y0 + 1.0 + wall + hb * 0.55
    P.add(gable_roof(st, a + 3.4, d + 4.6, ye, ye + 4.4, detail=1, pitch=2.4, k=1.4, flick=0.85, horns=True))
    # one set of brackets on each column head at the front and back
    br = K.bracket_set(st, layers=2, w=1.7, h=hb, reach=1.5, detail=0)
    for x in xs:
        P.add(br, t=(x, y0 + 1.0 + wall, -d))
        P.add(br, t=(x, y0 + 1.0 + wall, d), yaw=math.pi)
    return P


# ======================================================================================================================
# the weapon exhibition hall
# ======================================================================================================================
EXH = dict(nb=7, bay=6.0, d_col=9.0, d_front=4.5, d_rear=9.0, wall=7.8, hb=1.9, floor=2.0, A=22.1, D=12.5, rise=5.4)


def exhibition_hall(st=ST, e=EXH):
    """A long hall: seven bays (6 each, 42 long) behind a colonnade of eight columns, a podium two risers high, plaster walls with six latticed display
    windows and a central doorway 6 wide in the front wall, closed ends under horse-head stepped gables, a long gable roof with an upswept ridge, a
    coffered ceiling. Origin: the middle of the hall at the terrace floor (y = 0); the hall's floor is y = 2. Front is -Z."""
    P = Piece()
    gs, gm, gg, gp, gw = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold), P.geo(st.paint), P.geo(st.wall)
    a = e["nb"] * e["bay"] / 2
    dc, df, dr, wall, hb, y0 = e["d_col"], e["d_front"], e["d_rear"], e["wall"], e["hb"], e["floor"]
    # podium: granite foot, marble top at y 2, a gold line, two one-stud steps in front of the doorway (2 risers: terrace 0 -> 1 -> 2)
    box(gs, -a - 3.0, a + 3.0, -3.0, 0.4, -dc - 3.0, dr + 2.0, "TNESW")
    box(gm, -a - 2.7, a + 2.7, 0.4, y0, -dc - 2.7, dr + 1.7, "TNESW")
    box(gg, -a - 2.74, a + 2.74, y0 - 0.74, y0 - 0.62, -dc - 2.74, dr + 1.74, "TBNESW")
    box(gm, -6.0, 6.0, 0.0, 1.0, -dc - 4.4, -dc - 2.7, "TNESW")
    box(gg, -6.04, 6.04, 0.62, 0.74, -dc - 4.44, -dc - 2.7, "TBNESW")
    # columns
    for i in range(e["nb"] + 1):
        P.add(K.pillar(st, wall - 1.0, foot=True, seg=12, detail=2), t=(-a + i * e["bay"], y0, -dc))
    top = y0 + wall - 1.5
    for (z, dep) in ((-dc, 0.6), (-df, 0.5)):
        box(gp, -a - 0.4, a + 0.4, y0 + wall - 1.5, y0 + wall - 0.8, z - dep, z + dep, "TBNESW")
        box(gp, -a - 0.4, a + 0.4, y0 + wall - 0.8, y0 + wall, z - dep + 0.1, z + dep - 0.1, "TBNESW")
    for i in range(e["nb"] + 1):            # tie beams from the colonnade to the front wall
        x = -a + i * e["bay"]
        box(gp, x - 0.4, x + 0.4, y0 + wall - 1.4, y0 + wall - 0.1, -dc + 0.5, -df - 0.5, "TBNESW")
    for z0 in (-dc, -df):
        for x in [-a + i * e["bay"] for i in range(e["nb"] + 1)]:
            box(gg, x - 0.9, x + 0.9, y0 + wall - 0.5, y0 + wall - 0.05, z0 - 0.62 - 0.0, z0 - 0.45, "TBNESW") if z0 == -dc else None
    # brackets on the colonnade (heads: two layers; one lighter set in each bay)
    head = K.bracket_set(st, layers=2, w=1.7, h=e["hb"], reach=1.4, detail=1)
    mid = K.bracket_set(st, layers=1, w=1.3, h=e["hb"], reach=2.0, detail=0)
    for i in range(e["nb"] + 1):
        P.add(head, t=(-a + i * e["bay"], y0 + wall, -dc))
    for i in range(e["nb"]):
        P.add(mid, t=(-a + (i + 0.5) * e["bay"], y0 + wall, -dc))
    # the front wall: a doorway 6 wide in the middle bay, six display windows (lattice) in the others
    wins = [-18.0, -12.0, -6.0, 6.0, 12.0, 18.0]
    wall_run(gw, -a + 0.4, a - 0.4, -df, y0, top, [(-3.0, 3.0, y0, top)] + [(x - 2.3, x + 2.3, y0 + 1.3, top - 0.9) for x in wins], t=0.9)
    lat = K.lattice(st, 4.5, top - 0.9 - y0 - 1.3, nx=5, ny=3, frame=0.22, bar=0.1)
    for x in wins:
        P.add(lat, t=(x, y0 + 1.3, -df - 0.05))
    leaf = K.door_leaf(st, 3.0, top - y0 - 0.2, studs=(2, 2))
    P.add(leaf, t=(-3.0, y0, -df + 0.9), yaw=math.pi)
    P.add(leaf, t=(3.0, y0, -df + 0.9), yaw=math.pi, mx=True)
    # the rear wall and the closed ends
    wall_run(gw, -a - 0.9, a + 0.9, dr, y0, top, [], t=0.9)
    for sx in (-1, 1):
        box(gw, sx * (a + 0.2) - 0.45, sx * (a + 0.2) + 0.45, y0, top, -df, dr, "TBNESW")
    # a gold band along the rear wall at the display height and a plain gold line along the front wall's foot
    box(gg, -a, a, y0 + 3.3, y0 + 3.42, dr - 0.48, dr - 0.45, "TBS")
    # ceiling and gold coffer ribs
    cy = y0 + wall - 1.6
    box(gp, -a, a, cy, cy + 0.2, -df + 0.45, dr - 0.45, "B")
    for x in range(int(-a) + 6, int(a), 6):
        box(gg, x - 0.16, x + 0.16, cy - 0.05, cy, -df + 0.45, dr - 0.45, "BNESW")
    box(gg, -a, a, cy - 0.05, cy, 2.0 - 0.16, 2.0 + 0.16, "BNESW")
    # the floor's gold line from the door to the plinth
    box(gg, -0.16, 0.16, y0, y0 + 0.04, -df, -2.0, "TNESW")
    # the roof, the ridge's upswept ends, the stepped gables
    ye = y0 + wall + hb * 0.55
    P.add(gable_roof(st, e["A"], e["D"], ye, ye + e["rise"], detail=1, pitch=2.0, k=1.4, flick=0.8, horns=True))
    for sx in (-1, 1):
        P.add(stepped_gable(st, e["D"] - 0.5, ye, ye + e["rise"], steps=3, thick=1.1, x=sx * (e["A"] + 0.55)))
    return P


def exh_bay(st=ST):
    """One display bay against the exhibition hall's rear wall (6 wide, 1.6 deep; origin at its floor, back at z = 0): a marble stand with a gold edge, a timber
    frame on the wall carrying two swords and a spear (plain shapes), a blank gold plate."""
    P = Piece()
    gm, gg, gt, gs = P.geo(st.stone), P.geo(st.gold), P.geo(st.timber), P.geo(st.stone2)
    box(gs, -2.6, 2.6, 0.0, 0.25, -1.9, -0.0, "TNESW")
    box(gm, -2.4, 2.4, 0.25, 1.0, -1.7, -0.1, "TNESW")
    box(gg, -2.44, 2.44, 0.62, 0.74, -1.74, -0.06, "TBNESW")
    # the frame: two posts and two rails
    for x in (-2.2, 2.2):
        box(gt, x - 0.2, x + 0.2, 1.0, 6.2, -0.55, -0.15, "TNESW")
    for y in (2.4, 5.6):
        box(gt, -2.2, 2.2, y - 0.16, y + 0.16, -0.5, -0.2, "TBNESW")
    # two swords on the lower rail and a spear across the upper (a flat blade, a gold guard and a grip)
    for x in (-1.0, 1.0):
        box(gg, x - 0.5, x + 0.5, 2.9, 3.0, -0.62, -0.5, "TBNESW")
        box(gt, x - 0.07, x + 0.07, 2.4, 2.9, -0.62, -0.5, "TBNESW")
        prism_x_blade(gm, x, 3.0, 5.2, 0.17)
    box(gt, -1.9, 1.9, 5.15, 5.25, -0.62, -0.52, "TBNESW")
    box(gg, 1.9, 2.4, 5.1, 5.3, -0.64, -0.5, "TBNESW")
    box(gg, -0.45, 0.45, 0.4, 0.8, -1.75, -1.66, "TBNESW")
    return P


def slab_tri(g, ring, z0, z1):
    """A prism along z over a convex polygon in the xy plane with its caps fanned into triangles (no n-gons)."""
    n = len(ring)
    area = sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n))
    if area < 0:
        ring = list(reversed(ring))
    a = [g.vert((x, y, z0)) for x, y in ring]
    b = [g.vert((x, y, z1)) for x, y in ring]
    for i in range(n):
        j = (i + 1) % n
        g.face(a[i], a[j], b[j], b[i])
    for i in range(1, n - 1):
        g.face(a[0], a[i + 1], a[i])
        g.face(b[0], b[i], b[i + 1])


def prism_x_blade(g, x, y0, y1, hw):
    """A flat sword blade, a long thin pointed shape in the plane z = -0.5 (faces -z): from y0 to y1, half width hw, pointed."""
    pts = [(x - hw, y0), (x + hw, y0), (x + hw, y1 - 0.7), (x, y1), (x - hw, y1 - 0.7)]
    slab_tri(g, pts, -0.58, -0.5)


def regent_plinth(st=ST):
    """The plinth of the exclusive weapon (the Dawnspire Regent): a long marble base 18 x 5.2, 1 stud high (a step), two gold-capped cradle stands for the
    blade and a glass-like case (a transparent box in a gold frame) 16 x 4 x 4.4. Origin: the middle of the base's floor footprint. The Regent's marker
    (pos 0, 3.15, 0) lies along x."""
    P = Piece()
    gm, gg, gs, gc = P.geo(st.stone), P.geo(st.gold), P.geo(st.stone2), P.geo(st.case)
    box(gs, -9.3, 9.3, -1.0, 0.3, -2.9, 2.9, "TNESW")
    box(gm, -9.0, 9.0, 0.3, 1.0, -2.6, 2.6, "TNESW")
    box(gg, -9.04, 9.04, 0.62, 0.74, -2.64, 2.64, "TBNESW")
    for x in (-3.6, 3.6):
        box(gm, x - 0.8, x + 0.8, 1.0, 2.1, -0.8, 0.8, "TNESW")
        box(gg, x - 0.86, x + 0.86, 2.1, 2.3, -0.86, 0.86, "TNESW")
    # the case: four corner posts, eight bars between them (no two overlap), the glass between
    x0, x1, z0, z1, y0, y1 = -8.0, 8.0, -2.0, 2.0, 1.0, 5.4
    t = 0.18
    for (xa, xb, za, zb) in ((x0, x0 + t, z0, z0 + t), (x1 - t, x1, z0, z0 + t), (x0, x0 + t, z1 - t, z1), (x1 - t, x1, z1 - t, z1)):
        box(gg, xa, xb, y0, y1, za, zb, "TBNESW")
    for yy in (y0, y1 - t):
        box(gg, x0 + t, x1 - t, yy, yy + t, z0, z0 + t, "TBNESW")
        box(gg, x0 + t, x1 - t, yy, yy + t, z1 - t, z1, "TBNESW")
        box(gg, x0, x0 + t, yy, yy + t, z0 + t, z1 - t, "TBNESW")
        box(gg, x1 - t, x1, yy, yy + t, z0 + t, z1 - t, "TBNESW")
    box(gc, x0 + t, x1 - t, y0 + t, y1 - t, z0 + 0.02, z1 - 0.02, "TBNESW")
    return P


# ======================================================================================================================
# the arched stone bridge
# ======================================================================================================================
def arch_bridge(st=ST, L=28.0, rise=6, w=8.0, spring=5.0, thick=1.3):
    """A stepped arched stone bridge along x: origin the middle of the span at the deck's end level (y = 0 the floor at both ends). `rise` one-stud steps up
    on each side (treads (L - flat) / 2 / rise = 1.5 when flat = L - 3 rise), a flat crown, marble steps over a smooth arch ring whose soffit is a circular
    arc from the abutments (spring studs under the ends) to the crown, stepped cheek walls with gold caps and lotus-capped posts, a keystone."""
    P = Piece()
    gm, gg, gs = P.geo(st.stone), P.geo(st.gold), P.geo(st.stone2)
    tread = 1.5
    run = rise * tread
    flat = L - 2 * run
    assert flat > 2.0, "bridge too short for its rise"
    z0, z1 = -w / 2, w / 2
    crown_bot = rise - thick
    H = crown_bot + spring
    Rr = ((L / 2) ** 2 + H * H) / (2 * H)
    yc = crown_bot - Rr

    def bot(x):
        return yc + math.sqrt(max(Rr * Rr - x * x, 0.0))
    # breakpoints: every half tread on the ramps, the crown in a few
    xs = []
    x = -L / 2
    for k in range(rise):
        xs += [-L / 2 + k * tread, -L / 2 + (k + 0.5) * tread]
    xs += [-flat / 2, 0.0]
    xs += [flat / 2, flat / 2 + 0.0]
    xs = sorted(set(round(v, 6) for v in xs + [flat / 2 + k * tread for k in range(rise + 1)] + [flat / 2 + (k + 0.5) * tread for k in range(rise)] + [L / 2]))
    xs = [v for v in xs if -L / 2 <= v <= L / 2]

    def top(xm):
        if xm < -flat / 2:
            return min(rise, 1 + int((xm + L / 2 + 1e-9) // tread))
        if xm > flat / 2:
            return min(rise, 1 + int((L / 2 - xm - 1e-9) // tread))
        return rise
    for xa, xb in zip(xs, xs[1:]):
        xm = (xa + xb) / 2
        sloped_column(gm, xa, xb, bot(xa), bot(xb), top(xm), z0, z1)
    # the abutments: granite blocks under the ends
    for sx in (-1, 1):
        box(gs, sx * (L / 2) - (0.0 if sx < 0 else 2.2), sx * (L / 2) + (2.2 if sx < 0 else 0.0), -spring - 1.5, 0.0, z0 - 0.3, z1 + 0.3, "TBNESW") if False else None
    # a gold string-course along each side face of the arch ring (just under the steps) and a keystone at the crown
    for z in (z0 - 0.03, z1 + 0.03):
        pts = [(-L / 2 + i * L / 28.0) for i in range(29)]
        for xa, xb in zip(pts, pts[1:]):
            ya, yb = bot(xa) + 0.0, bot(xb) + 0.0
            if z < 0:
                gg.face(gg.vert((xa, ya - 0.08, z)), gg.vert((xb, yb - 0.08, z)), gg.vert((xb, yb + 0.12, z)), gg.vert((xa, ya + 0.12, z)))
            else:
                gg.face(gg.vert((xa, ya - 0.08, z)), gg.vert((xa, ya + 0.12, z)), gg.vert((xb, yb + 0.12, z)), gg.vert((xb, yb - 0.08, z)))
    box(gg, -1.0, 1.0, crown_bot - 0.45, crown_bot + 0.02, z0 - 0.06, z1 + 0.06, "TBNESW")
    # cheek walls (stepped with the treads, the crown in one piece) and posts
    ints = [(-L / 2 + (k - 1) * tread, -L / 2 + k * tread, float(k)) for k in range(1, rise + 1)] + [(-flat / 2, flat / 2, float(rise))] + \
           [(L / 2 - (k - 1) * tread - tread, L / 2 - (k - 1) * tread, float(k)) for k in range(rise, 0, -1)]
    ints = [(round(a_, 6), round(b_, 6), h_) for (a_, b_, h_) in ints]
    for z in (z0 - 0.4, z1 + 0.4):
        zl, zh = z - 0.4, z + 0.4
        for n_, (xa, xb, tp) in enumerate(ints):
            box(gm, xa, xb, tp, tp + 1.9, zl, zh, "TNESW")
            box(gg, xa, xb, tp + 1.9, tp + 2.1 + 0.004 * (n_ % 2), zl - 0.07, zh + 0.07, "TBNESW")
        for xp in sorted(set(round(v, 4) for v in [-L / 2 + 0.5, L / 2 - 0.5] + [-L / 2 + 0.5 + 3 * tread * i for i in range(1, rise // 2 + 1)] + [L / 2 - 0.5 - 3 * tread * i for i in range(1, rise // 2 + 1)])):
            tp = top(xp)
            box(gm, xp - 0.55, xp + 0.55, tp, tp + 2.6, z - 0.55, z + 0.55, "TNESW")
            lathe(gg, [(0.5, tp + 2.6), (0.36, tp + 2.85), (0.44, tp + 3.15), (0.0, tp + 3.6)], 6, cx=xp, cz=z, caps=False)
    return P


# ======================================================================================================================
# carved screen walls (original motifs: clouds, waves, a crane as an abstract carved form)
# ======================================================================================================================
def screen_wall(st=ST, kind="clouds", W=13.0, H=5.8):
    P = Piece()
    gs, gm, gg, gw, gt = P.geo(st.stone2), P.geo(st.stone), P.geo(st.gold), P.geo(st.wall), P.geo(st.tile)
    box(gs, -W / 2 - 1.2, W / 2 + 1.2, -1.5, 0.6, -1.6, 1.6, "TNESW")
    box(gm, -W / 2 - 0.9, W / 2 + 0.9, 0.6, 1.3, -1.3, 1.3, "TNESW")
    box(gg, -W / 2 - 0.94, W / 2 + 0.94, 1.22, 1.3, -1.34, 1.34, "TNESW")
    body_y0, body_y1 = 1.3, 1.3 + H
    box(gw, -W / 2, W / 2, body_y0, body_y1, -0.55, 0.55, "TBNESW")
    # a marble frame (border 0.6) on both faces and the gold line inside it
    for z, sgn in ((-0.55, -1), (0.55, 1)):
        zz0, zz1 = (z - 0.1, z) if sgn < 0 else (z, z + 0.1)
        for (x0, x1, y0, y1) in ((-W / 2, -W / 2 + 0.6, body_y0, body_y1), (W / 2 - 0.6, W / 2, body_y0, body_y1), (-W / 2 + 0.6, W / 2 - 0.6, body_y0, body_y0 + 0.6),
                                  (-W / 2 + 0.6, W / 2 - 0.6, body_y1 - 0.6, body_y1)):
            box(gm, x0, x1, y0, y1, zz0, zz1, "TBNESW")
        box(gg, -W / 2 + 0.6, W / 2 - 0.6, body_y0 + 0.6, body_y0 + 0.68, zz0 - (0.02 if sgn < 0 else 0), zz1 + (0 if sgn < 0 else 0.02), "TBNESW")
    # the cap: a tiled gable along x with a gold ridge, over the whole width
    ring = [(body_y1, -1.0), (body_y1, 1.0), (body_y1 + 0.35, 0.85), (body_y1 + 1.0, 0.28), (body_y1 + 1.0, -0.28), (body_y1 + 0.35, -0.85)]
    prism_x(gt, ring, -W / 2 - 0.5, W / 2 + 0.5)
    box(gg, -W / 2 - 0.47, W / 2 + 0.47, body_y1 + 0.95, body_y1 + 1.1, -0.3, 0.3, "TBNESW")
    cy = (body_y0 + body_y1) / 2 + 0.2
    zc = -0.6
    if kind == "clouds":
        # three rising cloud scrolls: a big double spiral (two spirals back to back, joined by a rising ribbon) in the middle, a smaller one each side
        for (cx, r0, a0) in ((0.0, 1.6, 0.4), (-4.0, 1.0, 1.0), (4.0, 1.0, 2.1)):
            relief_tube(gg, _spiral(cx - r0 * 0.9, cy, r0, 1.35, 16, 1.0, math.pi * 0.9), zc, 0.13, 4)
            relief_tube(gg, _spiral(cx + r0 * 0.9, cy - 0.15, r0 * 0.9, 1.3, 16, -1.0, math.pi * 0.1), zc, 0.13, 4)
            relief_tube(gg, [(cx - r0 * 0.9, cy - r0 * 0.1 - 0.9 * r0), (cx - 0.2 * r0, cy - 1.15 * r0), (cx + r0 * 0.4, cy - 1.0 * r0), (cx + r0 * 0.9, cy - 0.9 * r0 - 0.15)], zc, 0.1, 4, False)
        for k in range(4):                            # small cloud tails along the foot
            x = -5.4 + k * 3.6
            relief_tube(gg, _spiral(x, body_y0 + 1.5, 0.55, 1.2, 12, 1.0 if k % 2 else -1.0), zc, 0.09, 4)
    else:
        # waves: three rows of overlapping arcs, and above them a crane's sweeping neck and two raised wings, drawn as simple curves
        for row in range(3):
            y = body_y0 + 1.2 + row * 0.95
            off = 0.0 if row % 2 == 0 else 0.7
            for k in range(7):
                x = -W / 2 + 1.7 + off + k * 1.55
                if x > W / 2 - 1.6:
                    continue
                arc = [(x + 0.8 * math.cos(math.pi * (1 - t / 8.0)), y + 0.55 * math.sin(math.pi * (1 - t / 8.0))) for t in range(9)]
                relief_tube(gg, arc, zc, 0.07, 4, False)
        neck = [(-1.6, cy + 0.2), (-0.9, cy + 0.6), (0.0, cy + 1.3), (0.6, cy + 2.0), (0.95, cy + 2.35), (1.5, cy + 2.2), (1.9, cy + 1.95)]
        relief_tube(gg, neck, zc, 0.14, 5, True)
        for sgn in (-1, 1):
            for k in range(5):
                a = math.radians(14 + 17 * k)
                p0 = (0.15, cy + 0.55)
                p1 = (0.15 + sgn * (1.6 + 0.9 * math.cos(a)) * 1.1, cy + 0.55 + 1.05 * math.sin(a) + 0.4 * k * 0.3)
                relief_tube(gg, [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.25), p1], zc, 0.07, 4, True)
        relief_tube(gg, [(-0.5, cy + 0.2), (0.0, cy + 0.0), (0.5, cy + 0.15)], zc, 0.2, 5, False)      # the body
    return P


# ======================================================================================================================
# props
# ======================================================================================================================
def lantern_pillar(st=ST, h=7.4):
    """A tall slender stone lamp pillar (origin: its foot): a square stepped foot, an octagonal tapering shaft with a gold collar, an eight-sided lamp box
    (a small azure glow core between four marble posts), a flat-eaved octagonal cap with a gold gourd. About 7.4 high."""
    P = Piece()
    gm, gs, gg, gt, gl = P.geo(st.stone), P.geo(st.stone2), P.geo(st.gold), P.geo(st.tile), P.geo(st.glow)
    box(gs, -1.0, 1.0, 0.0, 0.4, -1.0, 1.0, "TNESW")
    box(gm, -0.72, 0.72, 0.4, 0.85, -0.72, 0.72, "TNESW")
    ys = h * 0.62
    lathe(gm, [(0.5, 0.85), (0.42, 1.6), (0.36, ys * 0.55), (0.4, ys - 0.2), (0.5, ys)], 8, caps=False)
    lathe(gg, [(0.38, 1.9), (0.5, 2.05), (0.38, 2.2)], 8, loop=True)
    prism(gm, _ngon(8, 1.0, math.pi / 8), ys, ys + 0.3, "T")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, z = 0.78 * math.cos(a), 0.78 * math.sin(a)
        box(gm, x - 0.15, x + 0.15, ys + 0.3, ys + 1.5, z - 0.15, z + 0.15, "TNESW")
    prism(gl, _ngon(8, 0.62, math.pi / 8), ys + 0.35, ys + 1.4, "TB")
    ye = ys + 1.5
    hexa(gt, [(1.25 * math.cos(math.pi / 4 + k * math.pi / 2) * 1.0, 1.25 * math.sin(math.pi / 4 + k * math.pi / 2)) for k in range(4)], ye - 0.05,
         [(0.35 * math.cos(math.pi / 4 + k * math.pi / 2), 0.35 * math.sin(math.pi / 4 + k * math.pi / 2)) for k in range(4)], ye + 0.9, "TB0123")
    lathe(gg, [(0.3, ye + 0.85), (0.22, ye + 1.05), (0.3, ye + 1.3), (0.0, ye + 1.75)], 6, caps=False)
    return P


def lantern_low(st=ST, h=3.4):
    """A low garden lantern (origin: its foot): a round foot, a stout waisted shaft, a round lamp box with an azure glow ring between stone ribs, a wide
    mushroom roof with a gold finial. About 3.4 high."""
    P = Piece()
    gm, gs, gg, gl, gt = P.geo(st.stone), P.geo(st.stone2), P.geo(st.gold), P.geo(st.glow), P.geo(st.tile)
    lathe(gs, [(0.9, 0.0), (0.9, 0.3), (0.7, 0.45)], 10, caps=True)
    lathe(gm, [(0.55, 0.45), (0.38, 0.9), (0.34, 1.3), (0.55, 1.55), (0.95, 1.65)], 10, caps=False)
    lathe(gl, [(0.55, 1.7), (0.6, 2.05), (0.55, 2.4)], 10, loop=True) if False else None
    prism(gl, _ngon(10, 0.5, 0.0), 1.68, 2.35, "TB")
    for k in range(5):
        a = TAU * k / 5
        box(gm, 0.52 * math.cos(a) - 0.1, 0.52 * math.cos(a) + 0.1, 1.65, 2.4, 0.52 * math.sin(a) - 0.1, 0.52 * math.sin(a) + 0.1, "TNESW")
    lathe(gt, [(1.1, 2.4), (1.15, 2.55), (0.75, 2.85), (0.35, 3.15), (0.0, 3.3)], 10, caps=False)
    lathe(gg, [(0.18, 3.2), (0.14, 3.4), (0.0, 3.65)], 6, caps=False)
    return P


def burner(st=ST):
    """A bronze tripod incense burner (origin: its base): a round granite foot, three curved legs, a squat bowl with a gold band, two upright handles
    (rings), a domed lid with a small finial. About 4.2 high, 2.6 across."""
    P = Piece()
    gs, gg = P.geo(st.stone2), P.geo(st.gold)
    lathe(gs, [(1.9, 0.0), (1.9, 0.35), (1.5, 0.5)], 12, caps=True)
    for k in range(3):
        a = TAU * k / 3
        pts = [(0.0, 0.0), (0.0, 0.0)]
        c, s = math.cos(a), math.sin(a)
        centres = [(c * 1.15, 0.5, s * 1.15), (c * 1.2, 0.95, s * 1.2), (c * 1.0, 1.35, s * 1.0)]
        frames = []
        for i in range(3):
            rt = (-s, 0.0, c)
            sc = 0.22 - 0.04 * i
            frames.append((vmul(rt, sc), (c * sc, 0.0, s * sc)))
        tube(gg, centres, frames, [(-1, -1), (1, -1), (1, 1), (-1, 1)], caps=True)
    lathe(gg, [(0.0, 1.3), (1.2, 1.35), (1.35, 1.9), (1.25, 2.6), (1.45, 2.95), (1.1, 3.0), (0.0, 3.0)], 14, caps=False)
    lathe(gg, [(1.15, 2.35), (1.5, 2.45), (1.15, 2.55)], 14, loop=True)
    for sgn in (-1, 1):
        K.lathe_xy(gg, sgn * 1.32, 2.95, 0.5, 0.12, 0.1, 8, 0.0)
    lathe(gg, [(1.0, 3.0), (0.7, 3.45), (0.25, 3.8), (0.0, 4.2)], 10, caps=False)
    return P


def bench(st=ST, L=5.0):
    """A stone bench (origin: the middle of its foot): a slab seat 1.3 high on two stepped cloud-scroll ends."""
    P = Piece()
    gm, gs, gg = P.geo(st.stone), P.geo(st.stone2), P.geo(st.gold)
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.55)
        box(gs, x - 0.55, x + 0.55, 0.0, 0.2, -0.7, 0.7, "TNESW")
        box(gm, x - 0.4, x + 0.4, 0.2, 1.05, -0.55, 0.55, "TNESW")
        box(gm, x - 0.5, x + 0.5, 0.9, 1.3, -0.6, 0.6, "TNESW")
    box(gm, -L / 2, L / 2, 1.05, 1.35, -0.62, 0.62, "TNESW")
    box(gg, -L / 2 + 0.05, L / 2 - 0.05, 1.3, 1.36, -0.66, 0.66, "TBNESW")
    return P


def tea_table(st=ST):
    """A round stone table (radius 1.7, 1.6 high) on a waisted pedestal with four drum stools round it (radius 0.75, 1.0 high). Origin: the table's foot."""
    P = Piece()
    gm, gs, gg = P.geo(st.stone), P.geo(st.stone2), P.geo(st.gold)
    lathe(gs, [(1.0, 0.0), (1.0, 0.25), (0.6, 0.3)], 12, caps=True)
    lathe(gm, [(0.55, 0.3), (0.36, 0.75), (0.5, 1.3), (1.7, 1.45), (1.75, 1.6), (0.0, 1.6)], 14, caps=False)
    lathe(gg, [(1.68, 1.5), (1.8, 1.6), (1.7, 1.66)], 14, loop=True)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        cx, cz = 3.0 * math.cos(a), 3.0 * math.sin(a)
        lathe(gm, [(0.7, 0.0), (0.6, 0.35), (0.5, 0.55), (0.62, 0.85), (0.75, 1.0), (0.0, 1.0)], 10, cx=cx, cz=cz, caps=False)
        lathe(gg, [(0.7, 0.9), (0.76, 0.98), (0.68, 1.02)], 10, cx=cx, cz=cz, loop=True)
    return P


def weapon_rack(st=ST, W=5.4, H=4.6):
    """A weapon rack for the training yard (origin: the middle of its foot, the weapons face -z): a timber base beam, two uprights with gold-capped tops, two
    rails, four spears in the lower slots and three swords hung from the top rail (plain shapes)."""
    P = Piece()
    gt, gg, gm = P.geo(st.timber), P.geo(st.gold), P.geo(st.stone)
    box(gt, -W / 2, W / 2, 0.0, 0.45, -0.7, 0.7, "TNESW")
    for x in (-W / 2 + 0.3, W / 2 - 0.3):
        box(gt, x - 0.22, x + 0.22, 0.45, H, -0.22, 0.22, "TNESW")
        lathe(gg, [(0.2, H - 0.15), (0.3, H), (0.22, H + 0.2), (0.3, H + 0.4), (0.0, H + 0.8)], 6, cx=x, cz=0.0, caps=False)
    for y in (1.5, 3.4):
        box(gt, -W / 2 + 0.3, W / 2 - 0.3, y - 0.14, y + 0.14, -0.3, 0.1, "TBNESW")
    for i in range(4):
        x = -1.65 + i * 1.1
        lathe(gt, [(0.09, 0.5), (0.09, 3.7), (0.1, 4.3)], 6, cx=x, cz=-0.38, caps=True)
        K._slab_xy(gg, [(x - 0.2, 4.25), (x + 0.2, 4.25), (x, 5.15)], -0.45, -0.31)
    for i in range(3):
        x = -1.1 + i * 1.1
        box(gg, x - 0.3, x + 0.3, 3.3, 3.4, -0.34, -0.26, "TBNESW")
        box(gt, x - 0.06, x + 0.06, 3.4, 3.9, -0.32, -0.28, "TBNESW")
        slab_tri(gg, [(x - 0.13, 0.9), (x + 0.13, 0.9), (x + 0.13, 3.3), (x, 3.45), (x - 0.13, 3.3)], -0.38, -0.3)
    return P


def training_post(st=ST):
    """A wooden training post on a round stone foot (origin: its foot): an octagonal post 5.2 high wrapped in three bands of white cloth with a gold cap."""
    P = Piece()
    gs, gt, gw, gg = P.geo(st.stone2), P.geo(st.timber), P.geo(st.cloth2), P.geo(st.gold)
    lathe(gs, [(1.0, 0.0), (1.0, 0.45), (0.7, 0.6)], 10, caps=True)
    lathe(gt, [(0.45, 0.55), (0.42, 3.0), (0.4, 5.1)], 8, caps=True)
    for y in (1.5, 2.6, 3.7):
        lathe(gw, [(0.45, y - 0.3), (0.55, y - 0.2), (0.55, y + 0.2), (0.45, y + 0.3)], 6, loop=True)
    lathe(gg, [(0.34, 4.95), (0.5, 5.08), (0.55, 5.2), (0.3, 5.45), (0.0, 5.6)], 8, caps=False)
    return P


def plum_posts(st=ST):
    """Plum-blossom posts (the martial yard's apparatus): nine round posts of three heights (2.8 in the middle, 2.0, 1.2) in the old five-point pattern, each
    capped with a small stone disc. Origin: the middle post's foot. 24 studs of play: posts 0.45 radius, 3 apart."""
    P = Piece()
    gs, gt, gg = P.geo(st.stone2), P.geo(st.timber), P.geo(st.gold)
    spots = [(0.0, 0.0, 2.8)] + [(3.4 * math.cos(a), 3.4 * math.sin(a), 2.0) for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2)] + \
            [(6.0 * math.cos(a), 6.0 * math.sin(a), 1.2) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]
    for (x, z, hgt) in spots:
        lathe(gs, [(0.7, 0.0), (0.7, 0.3), (0.5, 0.4)], 8, cx=x, cz=z, caps=True)
        lathe(gt, [(0.45, 0.35), (0.42, hgt - 0.1), (0.46, hgt)], 8, cx=x, cz=z, caps=True)
        lathe(gg, [(0.3, hgt - 0.1), (0.5, hgt), (0.5, hgt + 0.1), (0.0, hgt + 0.12)], 8, cx=x, cz=z, caps=False)
    return P


def stone_weights(st=ST):
    """A stone barbell for the training yard (origin: the middle of its foot, 4.4 long along x): two octagonal stone discs (radius 1.1) on a stone bar."""
    P = Piece()
    gs, gm = P.geo(st.stone2), P.geo(st.stone)
    ring = [(1.1 + 1.1 * math.sin(TAU * k / 8 + math.pi / 8), 1.1 * math.cos(TAU * k / 8 + math.pi / 8)) for k in range(8)]
    for sx in (-1, 1):
        prism_x(gs, ring, sx * 1.6 - 0.35, sx * 1.6 + 0.35)
    prism_x(gm, [(1.1 + 0.22 * math.sin(TAU * k / 6), 0.22 * math.cos(TAU * k / 6)) for k in range(6)], -2.2, 2.2)
    return P


def stage(st=ST, W=18.0, D=18.0, h=3.0):
    """The martial stage: a granite base, a marble top 3 studs up (three steps of 1 stud, treads 1.5, 8 wide, on the front), a gold ring and a gold square
    inlaid, four corner posts with gold caps, carved panels round the base. Origin: the middle of the stage at the yard's floor (y = 0)."""
    P = Piece()
    gs, gm, gg, gp = P.geo(st.stone2), P.geo(st.stone), P.geo(st.goldflat), P.geo(st.gold)
    box(gs, -W / 2 - 0.4, W / 2 + 0.4, -2.0, 0.5, -D / 2 - 0.4, D / 2 + 0.4, "TNESW")
    box(gm, -W / 2, W / 2, 0.5, h, -D / 2, D / 2, "TNESW")
    box(gm, -W / 2 - 0.25, W / 2 + 0.25, h - 0.5, h, -D / 2 - 0.25, D / 2 + 0.25, "TBNESW")
    for k in range(2):                       # the steps in front (z < 0): tops 2 and 1, then the stage at 3 (risers of 1 stud)
        z1 = -D / 2 - 0.25 - k * 1.5
        box(gm, -4.0, 4.0, 0.0, h - 1.0 - k, z1 - 1.5, z1, "TNESW")
    K.lathe_xy(gg, 0.0, 0.0, 6.2, 0.24, 0.04, 40, 0.0) if False else None
    ring = Geo()
    lathe(gg, [(6.0, h), (6.0, h + 0.04), (5.7, h + 0.04), (5.7, h)], 40, loop=True)
    box(gg, -5.0, 5.0, h, h + 0.06, -5.0, -4.8, "TNESW")
    box(gg, -5.0, 5.0, h, h + 0.06, 4.8, 5.0, "TNESW")
    box(gg, -5.0, -4.8, h, h + 0.06, -4.8, 4.8, "TNESW")
    box(gg, 4.8, 5.0, h, h + 0.06, -4.8, 4.8, "TNESW")
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (W / 2 - 0.9), sz * (D / 2 - 0.9)
            box(gm, x - 0.45, x + 0.45, h, h + 2.4, z - 0.45, z + 0.45, "TNESW")
            lathe(gp, [(0.5, h + 2.4), (0.36, h + 2.65), (0.46, h + 2.95), (0.0, h + 3.4)], 6, cx=x, cz=z, caps=False)
    for i in range(5):                        # carved panels round the base (a gold border, an inset)
        x = -W / 2 + (i + 0.5) * W / 5
        box(gp, x - 1.4, x + 1.4, 1.1, 1.18, -D / 2 - 0.03, -D / 2, "TBN")
        box(gp, x - 1.4, x + 1.4, 2.3, 2.38, -D / 2 - 0.03, -D / 2, "TBN")
    return P


def tea_pond(st=ST, W=14.0, D=8.0):
    """The tea terrace's koi pond (origin: its middle at the terrace's floor): a marble coping, a granite lip, still water (Glass) 0.35 below the coping."""
    P = Piece()
    gm, gs, gw, gg = P.geo(st.stone), P.geo(st.stone2), P.geo(st.water), P.geo(st.gold)
    t = 0.9
    box(gs, -W / 2 - 0.2, W / 2 + 0.2, -1.5, 0.3, -D / 2 - 0.2, D / 2 + 0.2, "TNESW")
    for (x0, x1, z0, z1) in ((-W / 2, W / 2, -D / 2, -D / 2 + t), (-W / 2, W / 2, D / 2 - t, D / 2), (-W / 2, -W / 2 + t, -D / 2 + t, D / 2 - t), (W / 2 - t, W / 2, -D / 2 + t, D / 2 - t)):
        box(gm, x0, x1, 0.3, 0.95, z0, z1, "TNESW")
        box(gg, x0 - 0.02, x1 + 0.02, 0.9, 0.95, z0 - 0.02, z1 + 0.02, "TBNESW") if False else None
    box(gw, -W / 2 + t, W / 2 - t, 0.3, 0.62, -D / 2 + t, D / 2 - t, "T")
    box(gs, -W / 2 + t, W / 2 - t, -1.0, 0.3, -D / 2 + t, D / 2 - t, "TBNESW")
    return P


def floor_slab(st=ST, x0=-10.0, x1=10.0, z0=-10.0, z1=10.0, ring=None, slab=4.0, depth=3.0):
    """A paved floor (marble with granite joints every `slab`), optional gold inlay: ring = (cx, cz, r) a gold ring flush with the floor."""
    P = K.paving(st, x0, x1, z0, z1, y_top=0.0, depth=depth, slab=slab)
    if ring:
        cx, cz, r = ring
        lathe(P.geo(st.goldflat), [(r, 0.0), (r, 0.05), (r - 0.4, 0.05), (r - 0.4, 0.0)], 48, cx=cx, cz=cz, loop=True)
        lathe(P.geo(st.goldflat), [(r * 0.45, 0.0), (r * 0.45, 0.05), (r * 0.45 - 0.3, 0.05), (r * 0.45 - 0.3, 0.0)], 32, cx=cx, cz=cz, loop=True)
    return P


# ======================================================================================================================
# stairs, rails, the causeway
# ======================================================================================================================
def _flight(P, st, n, width, z0, y0, tread=1.5, cheek=0.8, rill=False):
    """n steps (1-stud risers) from z0 (the foot, floor y0) along +z, `width` wide, with stepped cheek walls and gold caps; returns the next z."""
    gm, gg = P.geo(st.stone), P.geo(st.gold)
    hw = width / 2
    for k in range(1, n + 1):
        za, zb = z0 + (k - 1) * tread, z0 + k * tread
        top = y0 + k
        box(gm, -hw, hw, y0 - 1.0 if k == 1 else top - 1.0, top, za, zb, "TNESW")
        box(gg, -hw + 0.1, hw - 0.1, top - 0.82, top - 0.74, za - 0.04, za, "TBN")                           # a gold line on the riser
        for sx in (-1, 1):
            x0, x1 = (hw, hw + cheek) if sx > 0 else (-hw - cheek, -hw)
            box(gm, x0, x1, top - 1.0, top + 1.7, za, zb, "TNESW")
            box(gg, x0 - 0.06, x1 + 0.06, top + 1.7, top + 1.9, za - 0.03, zb + (0.03 if k == n else 0.0), "TBNESW")
    return z0 + n * tread


def stair_block(st=ST, n=4, width=12.0):
    """A short stair of n one-stud steps (treads 1.5) climbing along +z, width wide; origin: the foot's centre on the lower floor (y = 0)."""
    P = Piece()
    _flight(P, st, n, width, 0.0, 0.0)
    return P


def rear_stair(st=ST):
    """The gorge stair from the garden up to the Master's terrace: a flight of 9 steps (16 wide, treads 1.5), a landing 6 long, a second flight of 9, stepped
    cheek walls with gold caps, a rill each side (a stone channel with a stepped glass-like water ribbon that follows the steps). Origin: the foot's centre on
    the garden's floor (y = 0); it climbs 18 along +z over 33."""
    P = Piece()
    gm, gg, gw, gs = P.geo(st.stone), P.geo(st.gold), P.geo(st.water), P.geo(st.stone2)
    z = _flight(P, st, 9, 16.0, 0.0, 0.0)
    box(gm, -8.0, 8.0, 8.0, 9.0, z, z + 6.0, "TNESW")
    box(gg, -8.1, 8.1, 8.92, 9.0, z + 0.2, z + 5.8, "NESW") if False else None
    for sx in (-1, 1):
        x0, x1 = (8.0, 8.8) if sx > 0 else (-8.8, -8.0)
        box(gm, x0, x1, 8.0, 10.7, z, z + 6.0, "TNESW")
        box(gg, x0 - 0.06, x1 + 0.06, 10.7, 10.9, z, z + 6.0, "TBNESW")
    z2 = z + 6.0
    _flight(P, st, 9, 16.0, z2, 9.0)
    # the rills: outside each cheek wall, 2.4 wide: a stone bed that follows the steps, and a water ribbon 0.5 over it
    for sx in (-1, 1):
        xa, xb = (9.1, 11.5) if sx > 0 else (-11.5, -9.1)
        xo0, xo1 = (11.5, 12.3) if sx > 0 else (-12.3, -11.5)
        z_ = 0.0
        for k in range(1, 10):
            za, zb = (k - 1) * 1.5, k * 1.5
            box(gm, xa, xb, k - 1.0, k - 0.5, za, zb, "TNESW")
            box(gw, xa + 0.2, xb - 0.2, k - 0.5, k - 0.18, za, zb + (0.0 if k == 9 else 0.0), "TNESW")
            box(gm, xo0, xo1, k - 1.0, k + 0.5, za, zb, "TNESW")
        for k in range(1, 10):
            za, zb = z2 + (k - 1) * 1.5, z2 + k * 1.5
            box(gm, xa, xb, 9 + k - 1.0, 9 + k - 0.5, za, zb, "TNESW")
            box(gw, xa + 0.2, xb - 0.2, 9 + k - 0.5, 9 + k - 0.18, za, zb, "TNESW")
            box(gm, xo0, xo1, 9 + k - 1.0, 9 + k + 0.5, za, zb, "TNESW")
        box(gm, xa, xb, 8.0, 8.5, 13.5, z2, "TNESW")
        box(gw, xa + 0.2, xb - 0.2, 8.5, 8.82, 13.5, z2, "TNESW")
        box(gm, xo0, xo1, 8.0, 9.5, 13.5, z2, "TNESW")
    return P


def rail8(st=ST, L=8.0):
    """A plain parapet module for exposed terrace edges (origin: its middle at the floor; along x): a marble wall 1.6 high, 0.8 thick with a gold cap, a post
    with a gold cap at each end (the posts of neighbours coincide)."""
    P = Piece()
    gm, gg, gs = P.geo(st.stone), P.geo(st.gold), P.geo(st.stone2)
    box(gs, -L / 2, L / 2, -1.2, 0.2, -0.65, 0.65, "TNESW")
    box(gm, -L / 2, L / 2, 0.2, 1.7, -0.4, 0.4, "TNESW")
    box(gg, -L / 2, L / 2, 1.7, 1.9, -0.48, 0.48, "TBNESW")
    for x in (-L / 2, L / 2):
        box(gm, x - 0.55, x + 0.55, 0.2, 2.3, -0.55, 0.55, "TNESW")
        box(gg, x - 0.42, x + 0.42, 2.3, 2.45, -0.42, 0.42, "TNESW")
    return P


def landing(st=ST, W=9.0, D=5.0):
    """A marble landing slab 9 x 5 (origin: its middle at the floor; top at y = 0) with a gold edge, for a bridge's ends."""
    P = Piece()
    gm, gg = P.geo(st.stone), P.geo(st.gold)
    box(gm, -D / 2, D / 2, -2.5, 0.0, -W / 2, W / 2, "TNESW")
    box(gg, -D / 2 - 0.04, D / 2 + 0.04, -0.3, -0.18, -W / 2 - 0.04, W / 2 + 0.04, "TBNESW")
    return P


def causeway(st=ST):
    """The hall's rear opening: a marble causeway (x +-7.2) carrying the floor from the rear gate pavilion over the tiers' ledges to the garden, and the garden's
    south retaining wall (x +-36, z 38.4..40.6) with a gold cap. Authored in the PAD FRAME (origin = the pad frame's), the causeway's top at y = 9."""
    P = Piece()
    gm, gg, gs = P.geo(st.stone), P.geo(st.gold), P.geo(st.stone2)
    box(gm, -7.2, 7.2, 1.5, 9.0, 33.8, 40.8, "TNESW")
    box(gg, -7.24, 7.24, 8.6, 8.72, 33.8, 40.84, "TBNESW")
    for (x0, x1) in ((-36.0, -7.2), (7.2, 36.0)):
        box(gs, x0, x1, 2.0, 3.6, 38.2, 40.8, "TNESW")
        box(gm, x0, x1, 3.6, 9.4, 38.4, 40.6, "TNESW")
        box(gg, x0 - 0.05, x1 + 0.05, 9.4, 9.62, 38.32, 40.68, "TBNESW")
    for sx in (-1, 1):                      # end posts of the wall at the causeway's sides
        x = sx * 7.7
        box(gm, x - 0.55, x + 0.55, 3.6, 11.5, 38.3, 40.7, "TNESW")
        box(gg, x - 0.42, x + 0.42, 11.5, 11.9, 38.42, 40.58, "TNESW")
    return P

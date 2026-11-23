"""trial_props: the three hero props of the faction trials (2026-11-23). Plain Python, no Blender; trial_props_run.py makes the scenes, QA and the FBX.

  TrialGate   Orthodox, Trial of Discipline: a freestanding ceremonial gate over Dawnspire's 32-stud stair (five identical ones stand on it). Marble, Gold, Azure.
  TrialToken  Unorthodox, Trial of Three Tokens: a copper-rimmed disc with a glowing verdigris inlay in a notched timber stand on a mossy stone. Stone, Timber, Copper, Glow.
  TrialDummy  Demonic, Trial of Strength: an iron-and-timber training dummy for heavy blows (eight stand in Nightfall's arena). Iron, Crimson, Timber.

Built on the kits of the territories (hq_kit's Geo and lathe, windrift_kit's WP, hex8, obox, nightfall_kit's frust) and on none of their buildings.
Everything is authored in ROBLOX STUDS like the Nightfall kit: x right, y up, z back, a piece's FRONT is -Z, its origin on the ground at the middle of its footprint (the lowest
point is y = 0). No texture, no lettering, no symbol anywhere: the gate's number is drawn by code on the cap's plate (see GATE_PLATE).
"""
import math

from hq_kit import vadd, vsub, vmul, vnorm, vlen, vcross, vdot, lerp, TAU, lathe, Geo
from windrift_kit import WP, hex8, obox
from nightfall_kit import frust

# ---------------------------------------------------------------------------------------------------------------------------------
# the looks (Roblox material, colour) by piece and material suffix. TrialGate's are Dawnspire's own looks and TrialDummy's Nightfall's own (same names, same colours);
# TrialToken's Stone and Timber are Windrift's; Copper and Glow are new.
# ---------------------------------------------------------------------------------------------------------------------------------
LOOKS = {
    "TrialGate": {
        "Marble": {"Material": "Marble", "Color": [238, 236, 232]},
        "Gold": {"Material": "Metal", "Color": [255, 172, 48]},
        "Azure": {"Material": "SmoothPlastic", "Color": [38, 104, 204]},
    },
    "TrialToken": {
        "Stone": {"Material": "Slate", "Color": [62, 82, 74]},
        "Timber": {"Material": "Wood", "Color": [88, 66, 46]},
        "Copper": {"Material": "Metal", "Color": [196, 108, 58]},
        "Glow": {"Material": "Neon", "Color": [60, 212, 178], "CastShadow": False},
    },
    "TrialDummy": {
        "Iron": {"Material": "Metal", "Color": [78, 76, 92]},
        "Crimson": {"Material": "Fabric", "Color": [158, 24, 36], "CastShadow": False},
        "Timber": {"Material": "Wood", "Color": [52, 40, 36]},
    },
}
# the preview of a suffix in Blender: (colour, roughness, metallic, emission) per piece
PREVIEW = {
    "TrialGate": {"Marble": ((238, 236, 232), 0.28, 0.0, None), "Gold": ((255, 172, 48), 0.32, 1.0, None), "Azure": ((38, 104, 204), 0.4, 0.0, None)},
    "TrialToken": {"Stone": ((62, 82, 74), 0.8, 0.0, None), "Timber": ((88, 66, 46), 0.8, 0.0, None), "Copper": ((196, 108, 58), 0.32, 0.9, None),
                   "Glow": ((60, 212, 178), 0.2, 0.0, ((60, 212, 178), 1.6))},
    "TrialDummy": {"Iron": ((78, 76, 92), 0.35, 0.55, None), "Crimson": ((158, 24, 36), 0.85, 0.0, None), "Timber": ((52, 40, 36), 0.8, 0.0, None)},
}


# ---------------------------------------------------------------------------------------------------------------------------------
# solids
# ---------------------------------------------------------------------------------------------------------------------------------
def ring_xz(cx, cz, y, rx, rz, seg, phase=0.0):
    return [(cx + rx * math.cos(phase + TAU * k / seg), y, cz + rz * math.sin(phase + TAU * k / seg)) for k in range(seg)]


def _centroid(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


def loft(g, rings, caps=(True, True), closed=False):
    """A closed solid through rings of equal length (3D points, each ring in one winding): quads between neighbours, a fan from the centroid on each capped end; closed = the
    last ring joins the first (a torus: no caps). The winding is sorted out by Geo.orient() when the piece is finished."""
    n = len(rings[0])
    ids = [[g.vert(p) for p in r] for r in rings]
    pairs = list(zip(ids, ids[1:]))
    if closed:
        pairs.append((ids[-1], ids[0]))
    for a, b in pairs:
        for i in range(n):
            j = (i + 1) % n
            g.face(a[i], b[i], b[j], a[j])
    if not closed:
        if caps[0]:
            c = g.vert(_centroid(rings[0]))
            for i in range(n):
                g.face(c, ids[0][i], ids[0][(i + 1) % n])
        if caps[1]:
            c = g.vert(_centroid(rings[-1]))
            for i in range(n):
                g.face(c, ids[-1][(i + 1) % n], ids[-1][i])


def extrude_x(g, poly, x0, x1):
    """A polygon given as (z, y) pairs (convex, in one winding) extruded along x from x0 to x1."""
    loft(g, [[(x0, y, z) for (z, y) in poly], [(x1, y, z) for (z, y) in poly]])


def stud(g, p, nrm, r=0.09, h=0.07, seg=6, sink=0.03):
    """A rivet or boss: a seg-sided frustum on point p standing h out along the unit normal nrm (its foot sunk `sink` into the surface)."""
    ax = (0.0, 1.0, 0.0) if abs(nrm[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(ax, nrm))
    v = vcross(nrm, u)
    base = vsub(p, vmul(nrm, sink))
    top = vadd(p, vmul(nrm, h))
    rings = [[vadd(base, vadd(vmul(u, r * math.cos(TAU * k / seg)), vmul(v, r * math.sin(TAU * k / seg)))) for k in range(seg)],
             [vadd(top, vadd(vmul(u, r * 0.72 * math.cos(TAU * k / seg)), vmul(v, r * 0.72 * math.sin(TAU * k / seg)))) for k in range(seg)]]
    loft(g, rings)


def chain(g, a, b, sag, links, width=0.17, thick=0.07):
    """A hanging chain from a to b along a parabola sagging `sag`: `links` boxes, each one turned a quarter about the chain from the last, a little longer than its step so they
    overlap (a chain of flat and edge-on links)."""
    pts = []
    for i in range(links + 1):
        t = i / links
        p = vadd(vmul(a, 1 - t), vmul(b, t))
        pts.append((p[0], p[1] - sag * 4 * t * (1 - t), p[2]))
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        d = vsub(p1, p0)
        u = vnorm(d)
        n = (0.0, 0.0, 1.0)
        w = vnorm(vcross(n, u))
        if abs(vdot(w, w)) < 1e-6:
            w = (1.0, 0.0, 0.0)
        flat = (i % 2 == 0)
        hy, hz = (width / 2, thick / 2) if flat else (thick / 2, width / 2)
        # the box's axes: u along the link, then w (in the swag's plane, across) and n (out of it)
        obox(g, vmul(vadd(p0, p1), 0.5), u, w, n, vlen(d) / 2 * 1.18, hy, hz)


def dent_radial(g, axis_xz, centre, radius, depth, first=0):
    """An old dent: every vertex of g (from index `first`) within `radius` of `centre` is pushed `depth` toward the vertical axis through axis_xz (smooth fall-off)."""
    for i in range(first, len(g.v)):
        p = g.v[i]
        d = vlen(vsub(p, centre))
        if d < radius:
            f = (1.0 - d / radius) ** 2
            rx, rz = p[0] - axis_xz[0], p[2] - axis_xz[1]
            rl = math.hypot(rx, rz)
            if rl > 1e-6:
                k = depth * f
                g.v[i] = (p[0] - rx / rl * k, p[1], p[2] - rz / rl * k)


def dent_dir(g, centre, radius, depth, direction, first=0):
    """A dent in a plate: vertices within `radius` of `centre` move `depth` along `direction` (smooth fall-off)."""
    for i in range(first, len(g.v)):
        p = g.v[i]
        d = vlen(vsub(p, centre))
        if d < radius:
            f = (1.0 - d / radius) ** 2
            g.v[i] = vadd(p, vmul(direction, depth * f))


def vol_centroid(piece):
    """(volume, centroid) of a finished piece by tetrahedra from the origin (every solid is closed and outward wound after Geo.orient; overlaps count twice)."""
    vol, cx, cy, cz = 0.0, 0.0, 0.0, 0.0
    for g in piece.g.values():
        for f in g.f:
            p0 = g.v[f[0]]
            for j in range(1, len(f) - 1):
                p1, p2 = g.v[f[j]], g.v[f[j + 1]]
                v = vdot(p0, vcross(p1, p2)) / 6.0
                vol += v
                cx += v * (p0[0] + p1[0] + p2[0]) / 4.0
                cy += v * (p0[1] + p1[1] + p2[1]) / 4.0
                cz += v * (p0[2] + p1[2] + p2[2]) / 4.0
    return vol, ((cx / vol, cy / vol, cz / vol) if vol else (0.0, 0.0, 0.0))


# =================================================================================================================================
# TRIAL GATE
# =================================================================================================================================
GATE_PX = 10.2             # pillar centres at x = +-10.2
GATE_FOOT = (1.95, 1.4)   # the lower foot's half width and half depth
GATE_Y_LINTEL = 13.1       # the lintel's underside: the top of the clear opening
GATE_BELL_Y = 12.14        # the bell's lowest point (above the 12-stud clear height)
GATE_PLATE = dict(centre_front=(0.0, 15.18, -1.2), centre_back=(0.0, 15.18, 1.2), size=(4.4, 0.85), normal_front=(0.0, 0.0, -1.0), normal_back=(0.0, 0.0, 1.0),
                  note="a flat azure plate in a gilt frame on the raised middle storey, front faces -Z and back faces +Z: the gate's number goes here (drawn by code); size = width x height in studs")

SHAFT = [(1.0, 1.58), (2.8, 1.63), (5.4, 1.64), (8.0, 1.58), (10.4, 1.48), (12.0, 1.40)]    # (y, radius) of a pillar's shaft (a slight entasis)


def shaft_r(y):
    for (y0, r0), (y1, r1) in zip(SHAFT, SHAFT[1:]):
        if y0 <= y <= y1:
            return lerp(r0, r1, (y - y0) / (y1 - y0))
    return SHAFT[-1][1] if y > SHAFT[-1][0] else SHAFT[0][1]


def gate_pillar(P, cx, sx):
    """One pillar at x = cx (sx = +1 on the right, -1 on the left: the opening lies toward -sx): a two-step foot with a round plinth, a 12-sided shaft with an entasis and three
    gilt bands, and a bracket cluster of three stacked layers (a block, an arm across the gate's depth, an arm along its width reaching toward the opening, all above 12.7)."""
    gm, gg = P.geo("Marble"), P.geo("Gold")
    fx, fz = GATE_FOOT
    frust(gm, cx - fx, cx + fx, -fz, fz, 0.0, 0.5, 0.12)
    frust(gm, cx - fx + 0.2, cx + fx - 0.2, -fz + 0.18, fz - 0.18, 0.46, 0.9, 0.1)
    seg = 12
    loft(gm, [ring_xz(cx, 0.0, 0.86, 1.72, 1.72, seg), ring_xz(cx, 0.0, 1.12, 1.66, 1.66, seg)])           # the round plinth under the shaft
    loft(gm, [ring_xz(cx, 0.0, y, r, r, seg) for (y, r) in SHAFT])
    # gilt bands: a collar low on the shaft, a thin band at the middle, a neck band under the capital
    for (y0, y1, out, bev) in ((1.5, 2.1, 0.11, True), (6.2, 6.6, 0.09, False), (11.2, 12.0, 0.11, True)):
        if bev:
            ys = [y0, y1 - 0.14, y1]
            rs = [shaft_r(y0) + out, shaft_r(y1 - 0.14) + out, shaft_r(y1) - 0.02]
        else:
            ys = [y0, y1]
            rs = [shaft_r(y0) + out, shaft_r(y1) + out]
        loft(gg, [ring_xz(cx, 0.0, y, r, r, seg) for y, r in zip(ys, rs)])
    # the bracket cluster (a dougong in three plain layers): a square block, an arm across the depth, an arm along the width; gilt caps on the arms' ends
    d = -sx
    frust(gm, cx - 1.6, cx + 1.6, -1.4, 1.4, 11.96, 12.42, 0.08)
    frust(gm, cx - 0.42, cx + 0.42, -1.45, 1.45, 12.38, 12.76, 0.0)
    a, b = cx + d * 3.3, cx - d * GATE_FOOT[0]
    frust(gm, min(a, b), max(a, b), -0.42, 0.42, 12.72, 13.14, 0.0)
    for zz in (-1, 1):
        z0, z1 = sorted((zz * 1.45, zz * 1.59))
        frust(gg, cx - 0.5, cx + 0.5, z0, z1, 12.36, 12.78, 0.0)
    a, b = sorted((cx + d * 3.3, cx + d * 3.46))
    frust(gg, a, b, -0.5, 0.5, 12.68, 13.18, 0.0)


def gate_finial(P, x, y, s=1.0, tall=False):
    """A small gilt finial on a ridge: a base disc, a neck, a ball and a tip (one 8-sided lathe)."""
    gg = P.geo("Gold")
    prof = [(0.0, y), (0.3 * s, y), (0.3 * s, y + 0.1 * s), (0.14 * s, y + 0.18 * s), (0.3 * s, y + 0.36 * s), (0.3 * s, y + 0.5 * s), (0.12 * s, y + 0.66 * s)]
    prof += [(0.0, y + (1.05 if tall else 0.88) * s)]
    lathe(gg, prof, 8, cx=x, cz=0.0)


def gate_bell(P):
    """A small gilt bell hung on a bar under the lintel's middle: its lowest point is GATE_BELL_Y, above the 12-stud clear height."""
    gg = P.geo("Gold")
    y_top = GATE_Y_LINTEL + 0.05
    hex8(gg, [(-0.2, y_top - 0.22, -0.12), (0.2, y_top - 0.22, -0.12), (0.2, y_top - 0.22, 0.12), (-0.2, y_top - 0.22, 0.12), (-0.2, y_top, -0.12), (0.2, y_top, -0.12),
              (0.2, y_top, 0.12), (-0.2, y_top, 0.12)])
    prof = [(0.0, y_top - 0.12), (0.14, y_top - 0.12), (0.2, y_top - 0.34), (0.38, y_top - 0.44), (0.47, y_top - 0.62), (0.5, y_top - 0.8), (0.62, GATE_BELL_Y + 0.12),
            (0.67, GATE_BELL_Y + 0.02), (0.67, GATE_BELL_Y), (0.45, GATE_BELL_Y)]
    lathe(gg, prof, 10, cx=0.0, cz=0.0, caps=False)
    lathe(gg, [(0.0, y_top - 0.3), (0.05, y_top - 0.3), (0.05, GATE_BELL_Y + 0.4), (0.11, GATE_BELL_Y + 0.34), (0.11, GATE_BELL_Y + 0.12), (0.0, GATE_BELL_Y + 0.07)], 6, cx=0.0, cz=0.0)


WING_PROFILE = [(0.0, 15.58), (0.4, 15.2), (0.95, 14.98), (1.5, 14.86)]     # (|z|, y): a wing roof's concave slope from the ridge to the eave tip


def wing_roof(P, xa, xb, rib_xs):
    """A low tiled wing roof (ridge along x, a concave slope each side, a flat soffit) from x = xa to xb, raised ribs on both slopes at rib_xs, a gilt fascia and ridge."""
    ga, gg = P.geo("Azure"), P.geo("Gold")
    ye_b = 14.58
    prof = WING_PROFILE
    poly = [(-prof[-1][0], ye_b)] + [(-z, y) for (z, y) in reversed(prof[1:])] + [(0.0, prof[0][1])] + [(z, y) for (z, y) in prof[1:]] + [(prof[-1][0], ye_b)]
    extrude_x(ga, poly, xa, xb)
    for x in rib_xs:
        for sg in (-1, 1):
            rings = []
            for zz in (0.16, 0.42, 0.95, 1.36):
                y = None
                for (z0, y0_), (z1, y1_) in zip(prof, prof[1:]):
                    if z0 <= zz <= z1:
                        y = lerp(y0_, y1_, (zz - z0) / (z1 - z0))
                rings.append([(x - 0.18, y - 0.04, sg * zz), (x + 0.18, y - 0.04, sg * zz), (x, y + 0.17, sg * zz)])
            loft(ga, rings)
    for sg in (-1, 1):
        z0, z1 = sorted((sg * prof[-1][0] - 0.1, sg * prof[-1][0] + 0.1))
        frust(gg, xa, xb, z0, z1, ye_b + 0.02, prof[-1][1] + 0.06, 0.0)
    yr = prof[0][1]
    hex8(gg, [(xa, yr - 0.1, -0.26), (xb, yr - 0.1, -0.26), (xb, yr - 0.1, 0.26), (xa, yr - 0.1, 0.26), (xa, yr + 0.2, -0.16), (xb, yr + 0.2, -0.16), (xb, yr + 0.2, 0.16), (xa, yr + 0.2, 0.16)])


def gate():
    """Two stout marble pillars with bracket clusters, a heavy lintel, a painted azure frieze under two low tiled roofs, a raised middle storey carrying the number plate under a hip
    roof, gilt bands, finials and a hanging bell. Symmetrical both ways (the front and the back are the same)."""
    P = WP()
    gm, gg, ga = P.geo("Marble"), P.geo("Gold"), P.geo("Azure")
    for sx in (-1, 1):
        gate_pillar(P, sx * GATE_PX, sx)
    xe = GATE_PX + GATE_FOOT[0] - 0.05    # 12.1: the lintel ends flush with the feet
    # ---- the heavy lintel: a chamfered octagon section from pillar to pillar, gilt lines on both faces
    yl0, yl1 = GATE_Y_LINTEL, 14.15
    c = 0.12
    extrude_x(gm, [(-1.2, yl0 + c), (-1.2 + c, yl0), (1.2 - c, yl0), (1.2, yl0 + c), (1.2, yl1 - c), (1.2 - c, yl1), (-1.2 + c, yl1), (-1.2, yl1 - c)], -xe, xe)
    for sg in (-1, 1):
        z0, z1 = sorted((sg * 1.2 - sg * 0.01, sg * 1.2 + sg * 0.05))
        for (ya, yb) in ((13.3, 13.43), (13.84, 13.97)):
            frust(gg, -xe + 0.25, xe - 0.25, z0, z1, ya, yb, 0.0)
        frust(ga, -xe + 0.6, xe - 0.6, z0, z1, 13.47, 13.8, 0.0)           # the painted band between the gilt lines
    # ---- the painted frieze: an azure board with a gilt frame and gilt posts, over the lintel
    xf = xe - 0.45
    y_f0, y_f1 = 14.1, 14.72
    frust(ga, -xf, xf, -0.85, 0.85, y_f0, y_f1, 0.0)
    post_x = (6.3, 8.1, 9.9, xf)
    for sg in (-1, 1):
        zf = sg * 0.85
        z0, z1 = sorted((zf - sg * 0.03, zf + sg * 0.06))
        for (ya, yb) in ((y_f0, y_f0 + 0.12), (y_f1 - 0.12, y_f1)):
            frust(gg, -xf - 0.08, xf + 0.08, z0, z1, ya, yb, 0.0)
        for sx in (-1, 1):
            for px in post_x:
                frust(gg, sx * px - 0.12, sx * px + 0.12, z0, z1, y_f0, y_f1, 0.0)
    # ---- brackets under the low roofs: a tapered azure block under each panel, from the frieze toward the eave
    for sg in (-1, 1):
        for sx in (-1, 1):
            for px in (5.4, 7.2, 9.0, 11.0):
                x = sx * px
                zb0, zb1, zt0, zt1 = (0.8, 1.05, 0.8, 1.4) if sg > 0 else (-1.05, -0.8, -1.4, -0.8)
                hex8(ga, [(x - 0.26, 14.1, zb0), (x + 0.26, 14.1, zb0), (x + 0.26, 14.1, zb1), (x - 0.26, 14.1, zb1),
                          (x - 0.26, 14.62, zt0), (x + 0.26, 14.62, zt0), (x + 0.26, 14.62, zt1), (x - 0.26, 14.62, zt1)])
    # ---- the two low wing roofs (concave tiled slopes) with ribs, a gilt fascia and ridge, and a finial at each outer end
    x_in, x_out = 4.3, 12.3
    for sx in (-1, 1):
        xa, xb = sorted((sx * x_in, sx * x_out))
        wing_roof(P, xa, xb, [sx * 5.4, sx * 7.2, sx * 9.0, sx * 11.0])
        gate_finial(P, sx * (x_out - 0.35), WING_PROFILE[0][1] + 0.18, 0.9)
    # ---- the raised middle storey: an azure body with four gilt corner posts, the number plate framed in gilt on both faces
    xt, zt = 4.5, 1.2
    y_t0, y_t1 = 14.55, 15.8
    frust(ga, -xt, xt, -zt, zt, y_t0, y_t1, 0.0)
    for sx in (-1, 1):
        for sg in (-1, 1):
            xa, xb = sorted((sx * xt - 0.17, sx * xt + 0.17))
            za, zb = sorted((sg * zt - 0.17, sg * zt + 0.17))
            frust(gg, xa, xb, za, zb, y_t0, y_t1 + 0.04, 0.0)
    pw, ph = GATE_PLATE["size"]
    yc = GATE_PLATE["centre_front"][1]
    for sg in (-1, 1):
        zf = sg * zt
        z0, z1 = sorted((zf - sg * 0.03, zf + sg * 0.07))
        fr = 0.15
        for (a0, a1, b0, b1) in ((-pw / 2 - fr, pw / 2 + fr, yc + ph / 2, yc + ph / 2 + fr), (-pw / 2 - fr, pw / 2 + fr, yc - ph / 2 - fr, yc - ph / 2),
                                 (-pw / 2 - fr, -pw / 2, yc - ph / 2, yc + ph / 2), (pw / 2, pw / 2 + fr, yc - ph / 2, yc + ph / 2)):
            frust(gg, a0, a1, z0, z1, b0, b1, 0.0)
    # ---- the hip roof over the middle storey, its ribs, fascia and ridge, and two finials
    yh0, yh1 = 15.76, 16.4
    zh = 1.5
    frust(ga, -5.4, 5.4, -zh, zh, yh0, yh1, 2.45, 2.45, zh - 0.15, zh - 0.15)
    sl = (yh1 - yh0) / (zh - 0.15)
    for k in range(9):
        x = lerp(-4.4, 4.4, k / 8)
        for sg in (-1, 1):
            za, zb = sg * 0.3, sg * (zh - 0.14)
            ya, yb = yh1 - sl * (abs(za) - 0.15), yh1 - sl * (abs(zb) - 0.15)
            loft(ga, [[(x - 0.15, ya - 0.04, za), (x + 0.15, ya - 0.04, za), (x, ya + 0.12, za)], [(x - 0.15, yb - 0.04, zb), (x + 0.15, yb - 0.04, zb), (x, yb + 0.12, zb)]])
    for sg in (-1, 1):
        z0, z1 = sorted((sg * zh - 0.1, sg * zh + 0.1))
        frust(gg, -5.5, 5.5, z0, z1, yh0 + 0.02, yh0 + 0.3, 0.0)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 5.4 - 0.1, sx * 5.4 + 0.1))
        frust(gg, x0, x1, -zh, zh, yh0 + 0.02, yh0 + 0.3, 0.0)
    hex8(gg, [(-2.95, yh1 - 0.08, -0.26), (2.95, yh1 - 0.08, -0.26), (2.95, yh1 - 0.08, 0.26), (-2.95, yh1 - 0.08, 0.26),
              (-2.95, yh1 + 0.22, -0.16), (2.95, yh1 + 0.22, -0.16), (2.95, yh1 + 0.22, 0.16), (-2.95, yh1 + 0.22, 0.16)])
    gate_finial(P, -2.75, yh1 + 0.18, 0.9)
    gate_finial(P, 2.75, yh1 + 0.18, 0.9)
    gate_bell(P)
    P.marks["NumberPlateFront"] = GATE_PLATE["centre_front"]
    P.marks["NumberPlateBack"] = GATE_PLATE["centre_back"]
    P.marks["BellBottom"] = (0.0, GATE_BELL_Y, 0.0)
    return P


# =================================================================================================================================
# TRIAL TOKEN
# =================================================================================================================================
def _spiral(r0, r1, turns, n, start=math.pi * 0.5):
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 + (r1 - r0) * (t ** 0.85)
        a = start - TAU * turns * t
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def lash(g, cx, cy, cz, hx, hz, turns=3, pitch=0.13, t=0.06, h=0.09, tilt=0.3):
    """A rope lashing round an upright: `turns` thin bands round it, each leaning the opposite way from the last (a cross lashing), every one a closed collar a little larger than
    the post (half sizes hx, hz)."""
    for k in range(turns):
        sgn = 1.0 if k % 2 == 0 else -1.0
        w = hx + t + 0.012 * (k % 2)
        d = hz + t - 0.012 * (k % 2)
        y = cy + (k - (turns - 1) / 2) * pitch
        # corners in ring order (x0,z0) (x1,z0) (x1,z1) (x0,z1); the height of each corner follows x so the band leans
        def ring(dy):
            return [(cx - w, y + dy + sgn * tilt * (-w), cz - d), (cx + w, y + dy + sgn * tilt * w, cz - d), (cx + w, y + dy + sgn * tilt * w, cz + d), (cx - w, y + dy + sgn * tilt * (-w), cz + d)]
        loft(g, [ring(-h / 2), ring(h / 2)])


def token():
    P = WP()
    gs, gt, gc, gl = P.geo("Stone"), P.geo("Timber"), P.geo("Copper"), P.geo("Glow")
    # ---- the mossy stone: a flat-topped irregular slab, battered, its top edge chamfered; moss cushions drape its rim; two pebbles
    seg = 11
    rad = [1.62, 1.50, 1.42, 1.55, 1.66, 1.48, 1.36, 1.44, 1.60, 1.52, 1.40]

    def stone_ring(y, grow):
        return [((rad[k] + grow) * math.cos(0.2 + TAU * k / seg), y, (rad[k] + grow) * 0.84 * math.sin(0.2 + TAU * k / seg)) for k in range(seg)]
    loft(gs, [stone_ring(0.0, 0.0), stone_ring(0.18, 0.04), stone_ring(0.62, -0.06), stone_ring(0.8, -0.2)])
    for (mx, mz, mr, mh) in ((-0.95, -0.72, 0.6, 0.28), (0.95, -0.78, 0.46, 0.24), (-1.3, 0.4, 0.4, 0.22), (0.6, 0.8, 0.5, 0.26)):
        s = 7
        loft(gs, [ring_xz(mx, mz, 0.5, mr, mr * 0.9, s, 0.3), ring_xz(mx, mz, 0.68, mr * 0.86, mr * 0.78, s, 0.3), ring_xz(mx, mz, 0.62 + mh, mr * 0.46, mr * 0.42, s, 0.3)])
    for (px, pz, pr, ph_) in ((-1.62, -0.4, 0.34, 0.36), (1.62, 0.5, 0.3, 0.3)):
        loft(gs, [ring_xz(px, pz, 0.0, pr, pr * 0.9, 6, 0.5), ring_xz(px, pz, ph_ * 0.55, pr * 1.05, pr * 0.95, 6, 0.5), ring_xz(px, pz, ph_, pr * 0.62, pr * 0.55, 6, 0.5)])
    # ---- the notched stand on the stone's top (y 0.74): a sill with a groove the disc's rim stands in, two forked uprights, a crossbar, lashings and a rope loop
    y0 = 0.74
    hex8(gt, [(-1.3, y0, -0.4), (1.3, y0, -0.4), (1.3, y0, 0.4), (-1.3, y0, 0.4), (-1.25, y0 + 0.3, -0.38), (1.25, y0 + 0.3, -0.38), (1.25, y0 + 0.3, 0.38), (-1.25, y0 + 0.3, 0.38)])
    y_rail = y0 + 0.3
    for sg in (-1, 1):
        zc = sg * 0.27
        frust(gt, -1.15, 1.15, zc - 0.16, zc + 0.16, y_rail - 0.02, y_rail + 0.34, 0.0)
    cy = y_rail + 0.1 + 0.8                  # the disc's centre: its rim sinks 0.1 into the groove
    y_top_post = 2.9
    for sx in (-1, 1):
        xc = sx * 1.02
        for sg in (-1, 1):
            zc = sg * 0.255
            lean = -sx * 0.035                     # a degree or two out of true, toward the middle
            hex8(gt, [(xc - 0.17, y_rail - 0.02, zc - 0.14), (xc + 0.17, y_rail - 0.02, zc - 0.14), (xc + 0.17, y_rail - 0.02, zc + 0.14), (xc - 0.17, y_rail - 0.02, zc + 0.14),
                      (xc - 0.17 + lean, y_top_post, zc - 0.14), (xc + 0.17 + lean, y_top_post, zc - 0.14), (xc + 0.17 + lean, y_top_post, zc + 0.14), (xc - 0.17 + lean, y_top_post, zc + 0.14)])
    tl = 0.04                                      # the crossbar sits a hair high on the right
    hex8(gt, [(-1.45, y_top_post - 0.06, -0.27), (1.45, y_top_post - 0.06 + tl, -0.27), (1.45, y_top_post - 0.06 + tl, 0.27), (-1.45, y_top_post - 0.06, 0.27),
              (-1.45, y_top_post + 0.2, -0.27), (1.45, y_top_post + 0.2 + tl, -0.27), (1.45, y_top_post + 0.2 + tl, 0.27), (-1.45, y_top_post + 0.2, 0.27)])
    for sx in (-1, 1):
        lash(gt, sx * 1.02, y_top_post - 0.2, 0.0, 0.17, 0.4, turns=3)       # under the crossbar
        lash(gt, sx * 1.02, y_rail + 0.2, 0.0, 0.17, 0.4, turns=2)           # over the sill
    # the rope loop: a thin rope ring standing on the crossbar's middle, tied on with two wraps round the beam
    yb0, yb1 = y_top_post - 0.04, y_top_post + 0.22
    for xw in (-0.11, 0.11):
        frust(gt, xw - 0.045, xw + 0.045, -0.33, 0.33, yb0 - 0.07, yb1 + 0.07, 0.01)
    n = 14
    loop = [(0.17 * math.cos(TAU * i / n), yb1 + 0.24 + 0.22 * math.sin(TAU * i / n), 0.0) for i in range(n)]
    rings = []
    for i, c in enumerate(loop):
        a_, b_ = loop[(i - 1) % n], loop[(i + 1) % n]
        t = vnorm(vsub(b_, a_))
        rt = vnorm(vcross((0.0, 0.0, 1.0), t))
        up = vnorm(vcross(t, rt))
        rings.append([vadd(c, vadd(vmul(rt, 0.055 * math.cos(TAU * k / 5)), vmul(up, 0.055 * math.sin(TAU * k / 5)))) for k in range(5)])
    loft(gt, rings, closed=True)
    # ---- the disc: a copper body (a rim, a recessed field), the Glow inlay in the field, the copper wind-curl on the inlay. It stands in the XY plane, its front faces -Z.
    prof = [(0.0, -0.045), (0.58, -0.045), (0.6, -0.14), (0.7, -0.15), (0.79, -0.1), (0.8, -0.04), (0.8, 0.04), (0.79, 0.1), (0.7, 0.15), (0.6, 0.14), (0.58, 0.045), (0.0, 0.045)]
    tmp = Geo()
    lathe(tmp, [(r, z) for (r, z) in prof], 20, cx=0.0, cz=0.0, caps=False)
    base = len(gc.v)
    for (x, y, z) in tmp.v:                       # the lathe's axis (its y) becomes the disc's thickness (z)
        gc.v.append((x, cy + z, y))
    for f in tmp.f:
        gc.f.append(tuple(i + base for i in f))
    ring = lambda z: [(0.585 * math.cos(TAU * k / 20), cy + 0.585 * math.sin(TAU * k / 20), z) for k in range(20)]
    loft(gl, [ring(-0.082), ring(0.082)])
    sp = _spiral(0.07, 0.47, 1.45, 14)
    for zs in (-1.0, 1.0):
        rings = []
        for i, (px, py) in enumerate(sp):
            a, b = sp[max(0, i - 1)], sp[min(len(sp) - 1, i + 1)]
            t = vnorm((b[0] - a[0], b[1] - a[1], 0.0))
            nrm = (0.0, 0.0, zs)
            side = vnorm(vcross(nrm, t))
            w = lerp(1.0, 0.62, i / (len(sp) - 1)) * 0.075
            c = (px, cy + py, zs * 0.075)
            rings.append([vadd(c, vadd(vmul(side, -w), vmul(nrm, -0.01))), vadd(c, vadd(vmul(side, w), vmul(nrm, -0.01))), vadd(c, vadd(vmul(side, w * 0.7), vmul(nrm, 0.045))),
                          vadd(c, vadd(vmul(side, -w * 0.7), vmul(nrm, 0.045)))])
        loft(gc, rings)
    P.marks["DiscCentre"] = (0.0, cy, 0.0)
    return P


# =================================================================================================================================
# TRIAL DUMMY
# =================================================================================================================================
TORSO = [(1.9, 0.9), (2.0, 1.02), (2.58, 1.05), (2.72, 0.95), (2.84, 1.03), (3.52, 1.06), (3.66, 0.95), (3.78, 1.03), (4.4, 1.04), (4.55, 0.9)]    # (y, radius): three padded rolls
TORSO_MAX = 1.06
TORSO_Z = 0.9               # the torso's depth as a fraction of its width


def torso_r(y):
    for (y0, r0), (y1, r1) in zip(TORSO, TORSO[1:]):
        if y0 <= y <= y1:
            return lerp(r0, r1, (y - y0) / (y1 - y0))
    return TORSO[-1][1]


def dummy():
    """An iron-shod base, a thick timber post, a padded torso in three tied rolls wrapped in a worn crimson band, a riveted iron breastplate and back plate, a crossbeam for arms
    with chain loops and cloth tatters, a rounded iron helm with a visor slit, a few old dents. 4 wide, 6.6 high, 2.5 deep; its front faces -Z."""
    P = WP()
    gi, gc, gt = P.geo("Iron"), P.geo("Crimson"), P.geo("Timber")
    # ---- the base: an iron sole plate, a timber block on it, four iron corner boots, an iron top plate with a collar ring and rivets
    hex8(gi, [(-1.4, 0.0, -1.15), (1.4, 0.0, -1.15), (1.4, 0.0, 1.15), (-1.4, 0.0, 1.15), (-1.4, 0.14, -1.15), (1.4, 0.14, -1.15), (1.4, 0.14, 1.15), (-1.4, 0.14, 1.15)])
    frust(gt, -1.08, 1.08, -0.8, 0.8, 0.12, 0.72, 0.12)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 0.95, sx * 1.5))
            z0, z1 = sorted((sz * 0.7, sz * 1.22))
            frust(gi, x0, x1, z0, z1, 0.0, 0.78, 0.0, 0.0, 0.0, 0.0)
    frust(gi, -1.02, 1.02, -0.8, 0.8, 0.68, 0.8, 0.06)
    loft(gi, [ring_xz(0.0, 0.0, 0.76, 0.86, 0.86, 8, 0.39), ring_xz(0.0, 0.0, 1.0, 0.76, 0.76, 8, 0.39), ring_xz(0.0, 0.0, 1.3, 0.66, 0.66, 8, 0.39)])
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        stud(gi, (sx * 0.74, 0.8, sz * 0.58), (0.0, 1.0, 0.0), r=0.09, h=0.07)
    # ---- the post: a thick octagonal timber from the block up into the helm, an iron collar at the neck under the helm
    loft(gt, [ring_xz(0.0, 0.0, 0.7, 0.64, 0.64, 8, 0.39), ring_xz(0.0, 0.0, 5.12, 0.6, 0.6, 8, 0.39)])
    loft(gi, [ring_xz(0.0, 0.0, 4.6, 0.64, 0.64, 8, 0.39), ring_xz(0.0, 0.0, 4.9, 0.64, 0.64, 8, 0.39)])
    # ---- the padded torso (straw and leather in three tied rolls, ten flat sides, a flat facing front and back)
    tmp = Geo()
    lathe(tmp, [(r, y) for (y, r) in TORSO], 10, cx=0.0, cz=0.0)
    for (dy, ang, dp) in ((2.2, 2.0, 0.07), (3.2, 0.7, 0.06), (4.1, 3.9, 0.06)):
        rr = torso_r(dy)
        dent_radial(tmp, (0.0, 0.0), (rr * math.cos(ang), dy, rr * math.sin(ang)), 0.55, dp)
    gt.add(tmp, s=(1.0, 1.0, TORSO_Z))
    # ---- crimson cloth bands tied round the rolls (each leaning a little, a free tail hanging from its knot), and an iron hoop at the torso's top and foot
    def band(g, y, width, out, tilt, steps=10, inner=0.0):
        rings = []
        for k in range(steps):
            a = TAU * k / steps
            ca, sa = math.cos(a), math.sin(a)
            yy = y + tilt * ca
            r0 = torso_r(yy) + inner
            # the strap stands over the roll beside it as well as the tie it crosses (the torso bulges above and below the tie)
            r1 = max(torso_r(yy + dy_) for dy_ in (-width / 2, 0.0, width / 2)) + out
            ring = []
            for (rr, dy) in ((r0, -width / 2), (r1, -width / 2), (r1, width / 2), (r0, width / 2)):
                ring.append((rr * ca, yy + dy, rr * sa * TORSO_Z))
            rings.append(ring)
        loft(g, rings, closed=True)
    for (yb, wd, tl) in ((2.78, 0.44, 0.08), (3.72, 0.44, -0.08)):
        band(gc, yb, wd, 0.075, tl, inner=-0.03)
    # the free tails: a cloth strip hanging from the knot of the two lower bands, on the front left and the back right
    for (xk, zk, yk, ln) in ((-0.72, -0.62, 2.78, 0.95), (0.7, 0.64, 3.72, 0.85)):
        hex8(gc, [(xk - 0.17, yk - ln, zk - 0.03), (xk + 0.17, yk - ln + 0.14, zk - 0.03), (xk + 0.17, yk - ln + 0.14, zk + 0.03), (xk - 0.17, yk - ln, zk + 0.03),
                  (xk - 0.17, yk, zk - 0.03), (xk + 0.17, yk, zk - 0.03), (xk + 0.17, yk, zk + 0.03), (xk - 0.17, yk, zk + 0.03)])
    band(gi, 1.99, 0.22, 0.06, 0.0, inner=-0.03)
    band(gi, 4.46, 0.22, 0.06, 0.0, inner=-0.03)
    # ---- iron plates riveted on: a bent breastplate hugging the front flats, a plain plate on the back
    R = TORSO_MAX + 0.075               # beyond the torso's belly and the crimson bands
    plate_rows = [(2.95, 0.5), (3.2, 0.86), (4.0, 0.9), (4.26, 0.52)]
    angs = [math.radians(252 - 36), math.radians(252), math.radians(288), math.radians(288 + 36)]
    rings = []
    for (y, k) in plate_rows:
        inner = [(R * math.cos(a) * k, y, R * math.sin(a) * TORSO_Z) for a in angs]
        outer = [((R + 0.14) * math.cos(a) * k, y, (R + 0.14) * math.sin(a) * TORSO_Z) for a in angs]
        rings.append(inner + list(reversed(outer)))
    pg = Geo()
    loft(pg, rings)
    for (cx_, cy_, dp) in ((0.45, 3.45, 0.08), (-0.3, 3.95, 0.07)):
        dent_dir(pg, (cx_, cy_, -(R + 0.1) * TORSO_Z), 0.4, dp, (0.0, 0.0, 1.0))
    gi.add(pg)
    def plate_z(x, y):
        """The z of the breastplate's outer face at (x, y): along the bent outer line of the row at that height."""
        k = plate_rows[-1][1]
        for (ya, ka), (yb, kb) in zip(plate_rows, plate_rows[1:]):
            if ya <= y <= yb:
                k = lerp(ka, kb, (y - ya) / (yb - ya))
        pts = [((R + 0.14) * math.cos(a) * k, (R + 0.14) * math.sin(a) * TORSO_Z) for a in angs]
        for (xa, za), (xb, zb) in zip(pts, pts[1:]):
            if min(xa, xb) <= x <= max(xa, xb):
                return lerp(za, zb, (x - xa) / (xb - xa))
        return pts[0][1]
    for (sx, y) in ((-0.55, 3.4), (0.55, 3.4), (-0.55, 3.85), (0.55, 3.85), (0.0, 3.1), (0.0, 4.14)):
        stud(gi, (sx, y, plate_z(sx, y)), (0.0, 0.0, -1.0), r=0.085, h=0.07, sink=0.06)
    zb = (TORSO_MAX + 0.07) * TORSO_Z
    rings = []
    for (y, hw) in ((2.95, 0.4), (3.2, 0.64), (3.9, 0.64), (4.15, 0.4)):
        rings.append([(-hw, y, zb - 0.08), (hw, y, zb - 0.08), (hw, y, zb + 0.12), (-hw, y, zb + 0.12)])
    loft(gi, rings)
    for (sx, y) in ((-0.4, 3.3), (0.4, 3.3), (-0.4, 3.8), (0.4, 3.8)):
        stud(gi, (sx, y, zb + 0.12), (0.0, 0.0, 1.0), r=0.085, h=0.07)
    # ---- the crossbar (the arms): a timber beam through the shoulders, iron end caps and bands, crimson wraps and tatters, hooks and chain loops front and back
    hex8(gt, [(-1.9, 3.94, -0.3), (1.9, 3.94, -0.3), (1.9, 3.94, 0.3), (-1.9, 3.94, 0.3), (-1.9, 4.56, -0.3), (1.9, 4.56, -0.3), (1.9, 4.56, 0.3), (-1.9, 4.56, 0.3)])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 1.7, sx * 2.0))
        frust(gi, x0, x1, -0.36, 0.36, 3.9, 4.6, 0.04)
        xa, xb = sorted((sx * 1.08, sx * 1.34))                      # a crimson wrap round the arm
        frust(gc, xa, xb, -0.33, 0.33, 3.94, 4.56, 0.02)
        # a cloth tatter hanging from the arm's end: a flat strip with a slanted foot
        xc = sx * 1.7
        hex8(gc, [(xc - 0.22, 3.2, -0.04), (xc + 0.22, 3.2, -0.04), (xc + 0.22, 3.2, 0.04), (xc - 0.22, 3.2, 0.04), (xc - 0.22, 4.0, -0.04), (xc + 0.22, 4.0, -0.04),
                  (xc + 0.22, 4.0, 0.04), (xc - 0.22, 4.0, 0.04)] if sx > 0 else
             [(xc - 0.22, 3.4, -0.04), (xc + 0.22, 3.4, -0.04), (xc + 0.22, 3.4, 0.04), (xc - 0.22, 3.4, 0.04), (xc - 0.22, 4.0, -0.04), (xc + 0.22, 4.0, -0.04),
              (xc + 0.22, 4.0, 0.04), (xc - 0.22, 4.0, 0.04)])
    for sx in (-1, 1):
        for sg in (-1, 1):
            za = sg * 0.33
            ha, hb = (sx * 0.86, 4.1, za), (sx * 1.7, 4.1, za)
            for hk in (ha, hb):
                z0, z1 = sorted((sg * 0.26, sg * 0.4))
                frust(gi, hk[0] - 0.08, hk[0] + 0.08, z0, z1, hk[1] - 0.14, hk[1] + 0.1, 0.0)
            chain(gi, (ha[0], ha[1] - 0.06, sg * 0.4), (hb[0], hb[1] - 0.06, sg * 0.4), sag=0.62, links=6)
    # ---- the helm: a rounded iron dome of twelve flats in three parts so the visor slit is a real recess; a crest along the dome
    seg = 12
    ph0 = math.radians(15)
    helm = Geo()
    HS = 1.14
    lathe(helm, [(0.8 * HS, 4.98), (0.75 * HS, 5.12), (0.69 * HS, 5.4), (0.68 * HS, 5.58)], seg, phase=ph0)
    lathe(helm, [(0.73 * HS, 5.84), (0.67 * HS, 6.05), (0.5 * HS, 6.3), (0.24 * HS, 6.48), (0.0, 6.55)], seg, phase=ph0)
    # the core between the shells is dark timber, set back to r 0.4 over the front three flats: that recess is the visor slit; an iron band closes the gap round the sides and back
    core = []
    for yy in (5.52, 5.6, 5.82, 5.9):
        core.append([(math.cos(ph0 + TAU * k / seg) * (0.4 if 7 <= k <= 10 else 0.6), yy, math.sin(ph0 + TAU * k / seg) * (0.42 if 7 <= k <= 10 else 0.64)) for k in range(seg)])
    loft(gt, core)
    arc = []
    for k in range(10, 20):
        a_ = ph0 + TAU * k / seg
        arc.append([(r * math.cos(a_), y, r * math.sin(a_)) for (r, y) in ((0.62, 5.56), (0.76, 5.56), (0.76, 5.86), (0.62, 5.86))])
    loft(gi, arc)
    for (dy, ang, dp) in ((6.1, 1.1, 0.07), (5.3, 2.6, 0.06), (6.2, 4.5, 0.05)):
        rr = 0.62
        dent_radial(helm, (0.0, 0.0), (rr * math.cos(ang), dy, rr * math.sin(ang)), 0.42, dp)
    gi.add(helm)
    extrude_x(gi, [(-0.5, 6.0), (-0.25, 6.46), (0.1, 6.6), (0.5, 6.28), (0.46, 6.05), (0.0, 6.12)], -0.06, 0.06)
    return P


PIECES = {"TrialGate": gate, "TrialToken": token, "TrialDummy": dummy}


def key(name):
    return "Trial_Props_%s" % name

"""jade_lib_island: Jade Grove's expanded ground (2026-11-22): the terrain data, the named sites and the routes. Plain Python, no Blender.

The first foundation's layout (jade_island.py, read through jade_lib_oldmap) is the base and stays the source of every position the game depends on:
the Grove Gate and the bridge landing, the Mantis Arena, the three egg stands, the three relics, the checkpoint, the Sage's hermitage, the Bloom Glade,
the spring Hollow, the Elder knoll (the guardian tree's now) and the Ruin Court. The island grows only on the sides away from Ember Peak and the
bridge (north-west, west, south-west, south, north: `GROWTH`), and gains a plateau with a waterfall (Mistfall Heights), a pond, a stream in a gorge, a
dry rift, a western valley and a northern glen. Every new term is multiplied by `free(x, z)`, which is exactly 0 inside the protected discs round what the
game depends on, so there the height and the material are the old ones to the last digit (jade_lib_verify proves it cell by cell).

Coordinates: island-local studs, x east, z south, y up, the arena's centre at the origin, ground about 0 (world Y 200); the grid is the engine's own
4-stud voxel grid.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_oldmap as O  # noqa: E402

OLD = O.OLD
fbm, smoothstep, gauss = O.fbm, O.smoothstep, O.gauss
CENTRE = OLD.CENTRE
NAME = OLD.NAME

# ======================================================================================================================
# what the game depends on (all from the old layout, unchanged)
# ======================================================================================================================
ARENA, ARRIVAL, LANDING, GATE = OLD.ARENA, OLD.ARRIVAL, OLD.LANDING, OLD.GATE
GLADE, ELDER, HOLLOW, POOL, HERMITAGE, RUINS, RING_R = OLD.GLADE, OLD.ELDER, OLD.HOLLOW, OLD.HOLLOW_POOL, OLD.HERMITAGE, OLD.RUINS, OLD.RING_R

# discs inside which nothing changes: (x, z, radius); free() rises from 0 to 1 over the next 14 studs
PROTECT = [
    (0.0, 0.0, 76.0),                                  # the arena, its flagstone border and the path ring (level out to RING_R + 2 + 12)
    (LANDING[0], LANDING[1], 38.0),                   # the arrival terrace (radius 13 + 7), the Grove Gate, the bridge's landing and the checkpoint
    (ARRIVAL[0], ARRIVAL[1], 30.0),
    (HERMITAGE[0], HERMITAGE[1], 28.0),               # each feature's own footprint (its flat or bowl and its soft edge) plus 6 (the 4-stud cell's sample window reaches 2 beyond a centre)
    (GLADE[0], GLADE[1], 32.0),
    (ELDER[0], ELDER[1], 32.0),
    (HOLLOW[0], HOLLOW[1], 26.0),
    (RUINS[0], RUINS[1], 30.0),
]


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz)))
    return math.hypot(px - (ax + vx * t), pz - (az + vz * t)), t


def poly_nearest(x, z, pts):
    """(distance to the polyline, arc length at the nearest point, total length)."""
    best = (1e9, 0.0)
    acc = 0.0
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d, t = _seg_dist(x, z, a, b)
        if d < best[0]:
            best = (d, acc + t * L)
        acc += L
    return best[0], best[1], total


def point_at(pts, s):
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= s:
            t = (s - acc) / L
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        acc += L
    a, b = pts[-2], pts[-1]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def free(x, z):
    m = 1.0
    for (cx, cz, r) in PROTECT:
        m = min(m, smoothstep(r, r + 14.0, math.hypot(x - cx, z - cz)))
    return m


# ======================================================================================================================
# the rim: the old one plus growth lobes
# ======================================================================================================================
def _bump(d, centre, width):
    diff = (d - centre + 180) % 360 - 180
    return math.exp(-(diff / width) ** 2)


# (bearing, studs, width): nothing toward Ember Peak (north-east) or the bridge (south-east)
GROWTH = [(-135, 58, 36), (180, 50, 30), (135, 62, 30), (104, 34, 22), (-98, 40, 24), (-112, 16, 20)]


def _east_keep(d):
    """1 on the old rim's own side (bearings -72 .. +76), falling to 0 over 28 and 24 degrees."""
    a = (d + 180) % 360 - 180
    return smoothstep(-100, -72, a) * (1.0 - smoothstep(76, 100, a))


def growth(theta):
    d = math.degrees(theta)
    return sum(amount * _bump(d, bearing, width) for bearing, amount, width in GROWTH) * (1.0 - _east_keep(d))


def rim2(theta):
    return OLD.rim(theta) + growth(theta)


# ======================================================================================================================
# sites of the new ground (island-local)
# ======================================================================================================================
# Polish pass 2026-11-23: the owner saw the island in Studio and found its relief too gentle (the ground spanned -10.5 to +17.1 over 240 studs). Mistfall Heights now stands about
# 30 studs over the arena with cliffs on every side but the long south-west ramp, the Mosswater Gorge is a real cut (the bed reaches -13.9), and a rocky ridge (Mossback Ridge)
# rises 15 in the north. The numbers every piece reads (the High Falls' face, the second fall's rock, the pond) are collected here, so the models and the layout share one table.
DIR_F = (0.9, 0.436)                                    # the High Falls face south-east, toward the island's middle
FALLS_FOOT = (-91.4, -109.176)                          # where the High Falls' face meets the ground (unchanged since phase A: the grotto and the pond keep their place)
FOOT_LV = 1.0                                           # the ground level at the foot of the faces (a flat plaza)
FACE_BACK = 9.0                                         # the plateau's terrain starts this far behind a face's foot line (the face is a free-standing block in front of the cliff: its cave is open air)
FACE_W = 34.0                                           # the High Falls' face
FALLS_TOP = 30.5                                        # the ground on the plateau at the lip (the face's top)
FALLS_H = FALLS_TOP - FOOT_LV                           # the face piece's height (JG_Cliff_Grotto_G1)
LIP_Z = -1.4                                            # the lip mark's depth in the piece frame (in front of the brow)
PLATEAU_A, PLATEAU_B = 35.0, 31.0
PLATEAU_C = (FALLS_FOOT[0] - DIR_F[0] * (PLATEAU_A + FACE_BACK), FALLS_FOOT[1] - DIR_F[1] * (PLATEAU_A + FACE_BACK))
PLATEAU_TOP = FALLS_TOP - 0.2                           # the plateau's own level (absolute, not on top of the old ground): it is the surface of Mistfall Heights
RAMP_DIR = (-DIR_F[1], DIR_F[0])                        # across the plateau (v axis): south-west


def _fall_point(u):
    return (PLATEAU_C[0] + DIR_F[0] * u, PLATEAU_C[1] + DIR_F[1] * u)


def _uv(u, v):
    """A point of the plateau in its own frame (u toward the High Falls, v toward the ramp's side) -> island-local x, z."""
    return (PLATEAU_C[0] + DIR_F[0] * u + RAMP_DIR[0] * v, PLATEAU_C[1] + DIR_F[1] * u + RAMP_DIR[1] * v)


FALLS_LIP = (FALLS_FOOT[0] - DIR_F[0] * LIP_Z, FALLS_FOOT[1] - DIR_F[1] * LIP_Z)    # the water leaves the lip here (3.4 ... 1.4 in front of the foot line's origin)
POND_AHEAD = 15.0                                       # the pond's centre is this far in front of the foot
POND = (FALLS_FOOT[0] + DIR_F[0] * POND_AHEAD, FALLS_FOOT[1] + DIR_F[1] * POND_AHEAD, 19.0)   # the Spirit Pond: centre and the radius of its shore (the water's edge)
POND_WATER = FOOT_LV - 0.6                              # its surface
SPRING = _uv(-0.46 * PLATEAU_A, 0.0)
# the brook across the plateau to the lip (9 wide, widening into a basin over the last stretch), as points (x, z)
STREAM_TOP = [SPRING, _uv(-8.0, 3.0), _uv(2.0, -2.6), _uv(12.0, 2.2), _uv(22.0, -0.8), _uv(30.0, 0.6), FALLS_LIP]
BROOK_W = 4.5                                           # half the brook's width
BASIN_W = 12.4                                          # half the basin's width at the lip (the lip is 25 studs: Scale 3.5 x 3 curtains x 2.4)
STREAM = None                                           # set below (after the pond)

# the second fall: a narrow ribbon over the plateau's south-east shoulder into a plunge pool that drains into the stream's head
RIB_PHI = math.radians(50.0)
_rp = _uv(PLATEAU_A * math.cos(RIB_PHI), PLATEAU_B * math.sin(RIB_PHI))
_rn = (math.cos(RIB_PHI) / PLATEAU_A ** 2, math.sin(RIB_PHI) / PLATEAU_B ** 2)
_rnw = (DIR_F[0] * _rn[0] + RAMP_DIR[0] * _rn[1], DIR_F[1] * _rn[0] + RAMP_DIR[1] * _rn[1])
_rl = math.hypot(*_rnw)
RIB_DIR = (_rnw[0] / _rl, _rnw[1] / _rl)                # the ribbon fall faces this way (outward from the shoulder)
RIB_FOOT = (_rp[0] + RIB_DIR[0] * (FACE_BACK + 2.0), _rp[1] + RIB_DIR[1] * (FACE_BACK + 2.0))
RIB_W = 15.0                                            # the ribbon's rock face
RIB_TOP = 22.5                                          # its top (the lip level)
RIB_H = RIB_TOP - FOOT_LV
RIB_POOL = (RIB_FOOT[0] + RIB_DIR[0] * 8.0, RIB_FOOT[1] + RIB_DIR[1] * 8.0, 7.5)
RIB_BROOK = [SPRING, _uv(-4.0, 9.0), _uv(6.0, 17.0), None, None]          # filled in below: its last points reach the rib's lip


def _face_xz(p, foot, d):
    """(zl, xl): how far p is behind the face's foot line (negative in front of it) and how far across it (along the piece's +x)."""
    dx, dz = p[0] - foot[0], p[1] - foot[1]
    return -(dx * d[0] + dz * d[1]), -dx * d[1] + dz * d[0]


RIB_LIP = (RIB_FOOT[0] - RIB_DIR[0] * LIP_Z, RIB_FOOT[1] - RIB_DIR[1] * LIP_Z)
RIB_BROOK[3] = (RIB_FOOT[0] - RIB_DIR[0] * 14.0 + 0.0, RIB_FOOT[1] - RIB_DIR[1] * 14.0)
RIB_BROOK[4] = RIB_LIP



def _smooth(pts, per=8):
    """A Catmull-Rom curve through the control points (island-local x, z), so a walkway has no sharp corners (a path offset sideways kinks at one)."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(per):
            t = k / float(per)
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t * t + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t ** 3) for c in (0, 1)))
    out.append(tuple(pts[-1]))
    return out

# the long ramp up the south-west flank: a spur that climbs at about 20 degrees, from the root bridge's west bank round the plateau's south-west corner (island-local x, z)
RAMP_CENTRE = (-135.0, -87.0)                           # the ramp is a long arc (a gentle spiral, radius 33 to 42) round the plateau's south-west corner: bends no tighter than 26 studs keep the slope on the inside of a turn under 25 degrees
RAMP_CTRL = [(RAMP_CENTRE[0] + r * math.cos(math.radians(a)), RAMP_CENTRE[1] + r * math.sin(math.radians(a)))
             for a, r in ((116.0, 32.5), (132.0, 34.4), (150.0, 36.8), (168.0, 39.0), (186.0, 41.0), (204.0, 43.0), (224.0, 45.8), (240.5, 47.5))]
RAMP = _smooth(RAMP_CTRL, 10)
RAMP_HALF = 7.0                                         # the walkable band is 14 wide; its banks fall away at about 40 degrees
RAMP_EASE = (7.0, 6.0)                                  # the slope eases in over the first and out over the last stretch

# Mossback Ridge: a rocky ridge 15 high north of the plateau, steep on its north side, between the plateau and the glen
RIDGE = [(-114.0, -184.0), (-92.0, -192.0), (-72.0, -187.0), (-57.0, -174.0)]
RIDGE_TOP = 12.0

STREAM = [(POND[0] - 17.0 * 0.5, POND[1] + 17.0 * 0.86), (-98.0, -84.0), (-112.0, -66.0), (-130.0, -48.0), (-144.0, -28.0), (-152.0, -6.0), (-158.0, 16.0), (-164.0, 38.0), (-174.0, 58.0), (-196.0, 72.0), (-224.0, 82.0)]
W_POOL = (-178.0, 62.0, 8.0)
RIFT = [(-156.0, 128.0), (-124.0, 130.0), (-92.0, 138.0), (-62.0, 152.0)]
W_VALLEY = (-196.0, -30.0, 30.0)                       # the western valley: centre and radius of its bowl
STONE_CIRCLE = (-196.0, -30.0)
GLEN = (-14.0, -178.0, 22.0)
CLEARING = (-92.0, 164.0, 22.0)

# bank pads where the three forest bridges land: (x, z, radius, level)
# the root bridge crosses the gorge at stream arc length 66, the log bridge at its waist, the rope bridge the Rift of Roots


PADS = []          # (x, z, radius, level, soft): flat floors under structures and at bridge ends (jade_lib_sites fills it)
USE_PADS = [True]


def _gorge_width(t):
    return 10.5 * (1.0 - 0.4 * math.exp(-((t - 0.52) / 0.07) ** 2))


def _gorge_depth(t):
    """9 deep at the head (as phase A: the three cascade ledges stand on it), deepening downstream to about 15.5: the stream sits in a real cut."""
    return (9.0 * smoothstep(0.02, 0.075, t) + 6.6 * smoothstep(0.235, 0.34, t)) * (1.0 - smoothstep(0.76, 0.92, t))


def bridge_site(kind):
    """Endpoints, centre line, span and deck level of a forest bridge (island-local, deck level = the bank's ground)."""
    if kind == "root":
        t = 0.28
    elif kind == "log":
        t = 0.52
    if kind in ("root", "log"):
        tot = poly_nearest(0, 0, STREAM)[2]
        p, d = point_at(STREAM, t * tot)
        n = (-d[1], d[0])
        w = _gorge_width(t)
        half = w + 6.0
        a = (p[0] - n[0] * half, p[1] - n[1] * half)
        b = (p[0] + n[0] * half, p[1] + n[1] * half)
        return {"A": a, "B": b, "centre": p, "span": 2 * half, "dir": n, "gorge_w": w}
    a, b = (-84.0, 128.0), (-64.0, 170.0)      # the rope bridge over the Rift of Roots (set in bridge_rope())
    return {"A": a, "B": b}


# ======================================================================================================================
# the ground
# ======================================================================================================================
def _plateau_q(x, z):
    dx, dz = x - PLATEAU_C[0], z - PLATEAU_C[1]
    u = dx * DIR_F[0] + dz * DIR_F[1]
    v = -dx * DIR_F[1] + dz * DIR_F[0]
    q = math.hypot(u / PLATEAU_A, v / PLATEAU_B)
    return q * (1.0 + 0.07 * fbm(x / 28.0 + 5, z / 28.0 - 2, seed=71, octaves=2)), dx, dz


def _rect(p, foot, d, width, back=FACE_BACK, depth=64.0):
    """Signed distance inside the foyer rectangle behind a face (positive inside; the straight cliff edge is `back` behind the foot line)."""
    zl, xl = _face_xz(p, foot, d)
    return min(zl - back, width / 2.0 - abs(xl), depth - zl)


def _clip(p, foot, d, width, back=FACE_BACK):
    """No plateau in front of the straight edge, within the face's width and a little beyond it (the clip fades out sideways)."""
    zl, xl = _face_xz(p, foot, d)
    return zl - back + 1.2 * max(0.0, abs(xl) - (width / 2.0 + 2.0))


def plateau_sd(x, z):
    """How many studs inside Mistfall Heights' edge (negative outside): the old ellipse joined with the two faces' straight edges, never reaching in front of them."""
    q, dx, dz = _plateau_q(x, z)
    sd = (1.0 - q) * 31.0
    p = (x, z)
    sd = max(sd, _rect(p, FALLS_FOOT, DIR_F, FACE_W - 2.0), _rect(p, RIB_FOOT, RIB_DIR, RIB_W - 1.0, depth=40.0))
    sd = min(sd, _clip(p, FALLS_FOOT, DIR_F, FACE_W), _clip(p, RIB_FOOT, RIB_DIR, RIB_W))
    return sd


EDGE = 4.6                                              # the cliff band's width (studs): about 30 up over 4.6 is a sheer face


def plateau_top(x, z):
    """The plateau's surface: level at the falls' lip, gently rolling and domed toward its middle."""
    q, dx, dz = _plateau_q(x, z)
    lipk = smoothstep(32.0, 10.0, math.hypot(x - FALLS_LIP[0], z - FALLS_LIP[1]))
    n = 1.1 * fbm(x / 20.0 + 3, z / 20.0 + 8, seed=72, octaves=2)
    dome = 1.4 * (1.0 - smoothstep(0.1, 0.8, q))
    return PLATEAU_TOP + (n + dome) * (1.0 - lipk)


_BROOK = []
_RIBY = []
LIP_Y = FOOT_LV + FALLS_H - 1.1                         # the water's level at the High Falls' lip (the face's Lip mark)
RIB_LIP_Y = FOOT_LV + RIB_H - 0.9                       # the ribbon fall's lip


def _table(pts, y_of, tail=None):
    tot = poly_nearest(0, 0, pts)[2]
    out, y = [], None
    n = int(tot / 2.0) + 1
    for k in range(n + 1):
        s = min(tot, k * 2.0)
        p, _ = point_at(pts, s)
        t = y_of(p)
        y = t if y is None else min(y, t)
        out.append((s, y))
    if tail is not None:
        out[-1] = (tot, tail)
    return out


def _lookup(table, s):
    if s <= table[0][0]:
        return table[0][1]
    for (s0, y0), (s1, y1) in zip(table, table[1:]):
        if s <= s1:
            return y0 + (y1 - y0) * (s - s0) / max(1e-9, s1 - s0)
    return table[-1][1]


def brook_y(s):
    """The plateau brook's water level at arc length s (never rising downstream, 0.75 under the plateau's surface, ending at the High Falls' lip)."""
    if not _BROOK:
        _BROOK.extend(_table(STREAM_TOP, lambda p: plateau_top(p[0], p[1]) - 0.75, LIP_Y))
    return _lookup(_BROOK, s)


def rib_y(s, tot):
    """The ribbon's brook: level with the spring for the first 40 percent, then stepping down the gully to the ribbon's lip."""
    return brook_y(0.0) + (RIB_LIP_Y - brook_y(0.0)) * smoothstep(0.4, 0.97, s / tot)


def plateau_h(x, z, h):
    """h joined with the plateau: its surface inside, a cliff band at its edge, a scree skirt outside (none in front of a face: those have flat plazas)."""
    sd = plateau_sd(x, z)
    if sd < -12.0:
        return h
    e = smoothstep(0.0, EDGE, sd)
    top = plateau_top(x, z)
    p = (x, z)
    # the skirt: loose stone along the cliff foot, up to 2.4 high, thinning over 10 studs; none beside the faces' plazas
    near = max(smoothstep(24.0, 14.0, math.hypot(x - FALLS_FOOT[0] - DIR_F[0] * 12.0, z - FALLS_FOOT[1] - DIR_F[1] * 12.0)),
               smoothstep(20.0, 11.0, math.hypot(x - RIB_FOOT[0] - RIB_DIR[0] * 6.0, z - RIB_FOOT[1] - RIB_DIR[1] * 6.0)))
    skirt = 2.4 * (1.0 - smoothstep(0.0, 10.0, -sd)) * (1.0 - near) if sd < 0 else 0.0
    return h * (1.0 - e) + top * e + skirt * (1.0 - e)


def ramp_profile():
    """(arc length table, level table): the spur's centre line height by arc length, a straight 20-degree climb with eased ends, ending at the plateau's level."""
    tot = poly_nearest(0, 0, RAMP)[2]
    n = 400
    slope = []
    for k in range(n + 1):
        s = tot * k / n
        slope.append(smoothstep(0.0, RAMP_EASE[0], s) * (1.0 - smoothstep(tot - RAMP_EASE[1], tot, s)))
    area = sum(slope) * (tot / n)
    kk = (PLATEAU_TOP + 0.5) / area
    lv, acc = [0.0], 0.0
    for k in range(1, n + 1):
        acc += 0.5 * (slope[k] + slope[k - 1]) * kk * (tot / n)
        lv.append(acc)
    return tot, lv, kk


_RAMP = ramp_profile()


def ramp_level(s):
    tot, lv, kk = _RAMP
    f = max(0.0, min(1.0, s / tot)) * (len(lv) - 1)
    i = min(int(f), len(lv) - 2)
    return lv[i] + (lv[i + 1] - lv[i]) * (f - i)


def ramp_h(x, z, h):
    d, s, tot = poly_nearest(x, z, RAMP)
    if d > RAMP_HALF + 40.0:
        return h
    top = ramp_level(s)
    surf = top - 1.25 * max(0.0, d - RAMP_HALF)        # banks fall at about 40 degrees
    # a little cross-fall so the band is not a machined slab, never more than 0.12
    return max(h, surf)


def ridge_h(x, z, h):
    d, s, tot = poly_nearest(x, z, RIDGE)
    if d > 30.0:
        return h
    t = s / tot
    # which side: positive on the north (the outer, cliffed) side
    (qx, qz), dd = point_at(RIDGE, s)
    side = (x - qx) * dd[1] - (z - qz) * dd[0]          # (x - q) . (d.z, -d.x) : north when the ridge runs east
    prof = smoothstep(0.0, 0.26, t) * (1.0 - smoothstep(0.7, 1.0, t))
    noise = 0.85 + 0.3 * (fbm(x / 9.0 + 9, z / 9.0 - 4, seed=83, octaves=2) * 0.5 + 0.5)
    lat = 1.0 - (smoothstep(2.5, 8.5, d) if side > 0 else smoothstep(4.0, 16.0, d))
    crag = 2.6 * abs(fbm(x / 6.5 + 1, z / 6.5 + 7, seed=84, octaves=2)) * lat * lat
    r = RIDGE_TOP * prof * noise * lat + crag * prof
    return h + r


def _carve(d, w, depth, soft):
    return depth * (1.0 - smoothstep(w, w + soft, d))


def brook_half_width(t):
    """The plateau brook's half-width along its length (t 0..1): 4.5, opening into a basin over the last third."""
    return BROOK_W + (BASIN_W - BROOK_W) * smoothstep(0.64, 0.98, t)


def foyer(x, z, h):
    """The flat plazas at the faces' feet, the Spirit Pond's bowl and the ribbon's plunge pool (the ground there is made, not carved from the old swell)."""
    p = (x, z)
    # --- the High Falls: a plaza behind the foot line (the cave floor, FOOT_LV + 0.2: the cave's stone floor is 0.4 above it), the pond in front of it ---
    zl, xl = _face_xz(p, FALLS_FOOT, DIR_F)
    d = math.hypot(x - POND[0], z - POND[1])
    bowl = FOOT_LV - 3.1 * (1.0 - smoothstep(4.0, 24.0, d))
    # the apron: from just in front of the foot line to the straight edge, flat at the cave floor
    apron_w = smoothstep(-2.5, 1.0, zl) * (1.0 - smoothstep(FACE_W / 2.0 + 1.0, FACE_W / 2.0 + 7.0, abs(xl))) * (1.0 - smoothstep(FACE_BACK, FACE_BACK + 1.0, zl))
    g = bowl * (1.0 - apron_w) + (FOOT_LV + 0.2) * apron_w
    w = (1.0 - smoothstep(26.0, 44.0, d))
    w = max(w, apron_w)
    h = h * (1.0 - w) + g * w
    # --- the ribbon fall's plunge pool ---
    zl2, xl2 = _face_xz(p, RIB_FOOT, RIB_DIR)
    d2 = math.hypot(x - RIB_POOL[0], z - RIB_POOL[1])
    bowl2 = FOOT_LV - 2.4 * (1.0 - smoothstep(2.0, 12.5, d2))
    apron2 = smoothstep(-2.5, 1.0, zl2) * (1.0 - smoothstep(RIB_W / 2.0 + 1.0, RIB_W / 2.0 + 6.0, abs(xl2))) * (1.0 - smoothstep(FACE_BACK, FACE_BACK + 1.0, zl2))
    g2 = bowl2 * (1.0 - apron2) + (FOOT_LV - 0.4) * apron2
    w2 = max(1.0 - smoothstep(13.0, 24.0, d2), apron2)
    return h * (1.0 - w2) + g2 * w2


def rolling(x, z):
    """Broad swells on the sides of the island that grew (west, north-west, north, south-west, south): about 10 studs from trough to crest over 50 to 80 studs, nothing within 95 studs of the arena."""
    r = math.hypot(x, z)
    d = math.degrees(math.atan2(z, x))
    side = 1.0 - _east_keep(d)
    if side <= 0.0:
        return 0.0
    k = side * smoothstep(95.0, 125.0, r)
    return k * (7.5 * fbm(x / 52.0 + 21, z / 52.0 - 7, seed=91, octaves=2) + 1.0 * k)


def features(x, z, h):
    """The new ground: `h` (the old ground, without its rim lip) changed by the plateau and its ramp, the ridge, the ponds, the gorge, the rift, the valley, the glen, the clearing."""
    f = free(x, z)
    if f <= 0.0:
        return h
    d0 = h
    # --- the plazas and the pond first (they replace the old ground there), then Mistfall Heights, its ramp and the ridge on top ---
    h += rolling(x, z) * smoothstep(8.0, 26.0, poly_nearest(x, z, RAMP)[0])
    h = foyer(x, z, h)
    h = plateau_h(x, z, h)
    h = ramp_h(x, z, h)
    h = ridge_h(x, z, h)
    on_top = plateau_sd(x, z) > 2.0
    # the spring's bowl on the plateau, the brook across it to the lip (9 wide, opening into a basin) and the ribbon's gully: beds 0.9 under the water's level (jade_lib_sites draws the water at brook_y)
    if on_top:
        ds_ = math.hypot(x - SPRING[0], z - SPRING[1])
        w = 1.0 - smoothstep(3.0, 7.0, ds_)
        if w > 0.0:
            h = h * (1.0 - w) + min(h, brook_y(0.0) - 1.7) * w
        dt, st, tt = poly_nearest(x, z, STREAM_TOP)
        w = 1.0 - smoothstep(brook_half_width(st / tt), brook_half_width(st / tt) + 3.0, dt)
        if w > 0.0:
            h = h * (1.0 - w) + min(h, brook_y(st) - 0.9) * w
        dr2, sr2, tr2 = poly_nearest(x, z, RIB_BROOK)
        if dr2 < 12.0:
            gt = sr2 / tr2
            half = 2.4 + 1.2 * smoothstep(0.5, 1.0, gt)
            w = 1.0 - smoothstep(half, half + 2.8, dr2)
            if w > 0.0:
                h = h * (1.0 - w) + min(h, rib_y(sr2, tr2) - 0.9) * w
    # --- the stream and the Mosswater Gorge ---
    ds, s, tot = poly_nearest(x, z, STREAM)
    t = s / tot
    gw = _gorge_width(t)
    gd = _gorge_depth(t)
    h -= _carve(ds, gw, gd, 2.8)
    h -= 1.8 * (1.0 - smoothstep(2.5, 7.0, ds)) * smoothstep(0.02, 0.12, t)          # the stream's own bed
    wd = math.hypot(x - W_POOL[0], z - W_POOL[1])
    h -= 2.0 * (1.0 - smoothstep(W_POOL[2] - 1.0, W_POOL[2] + 5.0, wd))
    # --- the Rift of Roots (a dry chasm) ---
    dr, sr, tr = poly_nearest(x, z, RIFT)
    tr = sr / tr
    h -= _carve(dr, 13.0, 13.0 * smoothstep(0.0, 0.16, tr) * (1.0 - smoothstep(0.84, 1.0, tr)), 4.5)
    # --- the western valley: a bowl with a low ridge round it, level in the middle for the stone circle ---
    vd = math.hypot(x - W_VALLEY[0], z - W_VALLEY[1])
    h -= 2.8 * (1.0 - smoothstep(10.0, W_VALLEY[2] - 4.0, vd))
    h += 3.8 * math.exp(-((vd - (W_VALLEY[2] + 4.0)) / 5.5) ** 2)
    w = 1 - smoothstep(16.0, 24.0, vd)
    h = h * (1 - w) + (-1.2) * w
    # --- the northern glen and the south-western clearing: levelled floors ---
    gd2 = math.hypot(x - GLEN[0], z - GLEN[1])
    w = 1 - smoothstep(GLEN[2] * 0.55, GLEN[2], gd2)
    h = h * (1 - w) + 0.9 * w
    cd = math.hypot(x - CLEARING[0], z - CLEARING[1])
    w = 1 - smoothstep(CLEARING[2] * 0.6, CLEARING[2], cd)
    h = h * (1 - w) + 1.3 * w
    h = max(h, -13.9)       # no bed deeper than this: the engine builder writes a 22-stud shell (8 studs of terrain under the deepest bed)
    if USE_PADS[0]:
        for (px, pz, r, lev, soft) in PADS:
            w = 1 - smoothstep(r, r + soft, math.hypot(x - px, z - pz))
            if w > 0:
                h = h * (1 - w) + lev * w
    return d0 + (h - d0) * f


def base_free(x, z):
    """The old ground (jade_island._base) without its rim clamp and its rim lip, so it runs on past the old rim; identical to it inside."""
    J = OLD
    h = 3.0 * fbm(x / 42 + 11, z / 42 - 3, seed=51, octaves=4)
    h += 5.0 * gauss((x + 70) * 0.5, z + 110, 26) * (1 + 0.4 * fbm(x / 14, z / 14, seed=52, octaves=2))
    h += 3.0 * gauss(x - 112, (z - 20) * 0.6, 18)
    ex, ez, er = J.ELDER
    h += 7.0 * (1 - smoothstep(er * 0.35, er, math.hypot(x - ex, z - ez)))
    hx, hz, hr = J.HOLLOW
    d = math.hypot(x - hx, z - hz)
    bowl = 1 - smoothstep(hr * 0.55, hr, d)
    h = h * (1 - bowl) - 7.0 * bowl
    px, pz, pr = J.HOLLOW_POOL
    dp = math.hypot(x - px, z - pz) - pr
    if dp < 1.0:
        w = 1 - smoothstep(-2.0, 0.8, dp)
        h = h * (1 - w) + J.POOL_BED * w
    for (cx, cz, rad), lift, soft in ((J.LANDING, 0.4, 7), (J.GLADE, 1.0, 8), (J.RUINS, 0.5, 8), (J.HERMITAGE, 1.0, 8), ((*J.ARENA, J.RING_R + 2), J.ARENA_Y, 12)):
        w = 1 - smoothstep(rad, rad + soft, math.hypot(x - cx, z - cz))
        h = h * (1 - w) + lift * w
    if J.arena_distance(x, z) > J.ARENA_EDGE:
        h -= 0.4 * (1 - smoothstep(2.4, 4.4, J.path_distance(x, z)))
    return h


def lip(r, R):
    return 3.4 * (1 - smoothstep(R - 1, R - 12, r)) ** 1.6


def ground(x, z):
    """Ground height (None outside the rim) before the material is chosen."""
    r = math.hypot(x, z)
    R = rim2(math.atan2(z, x))
    if r > R:
        return None
    h = features(x, z, base_free(x, z))
    return h - lip(r, R)


def height(x, z):
    h = ground(x, z)
    if h is None:
        return None, None
    a = OLD.arena_distance(x, z)
    if a < OLD.ARENA_EDGE:
        return h, "Sandstone" if a > OLD.ARENA_R else "LeafyGrass"
    e = 1.5
    hs = [ground(x + dx, z + dz) for dx, dz in ((e, 0), (-e, 0), (0, e), (0, -e))]
    hs = [v if v is not None else h for v in hs]
    slope = math.hypot(hs[0] - hs[1], hs[2] - hs[3]) / (2 * e)
    if OLD.path_distance(x, z) < 3.8 or (TRAILS and free(x, z) > 0.0 and min(poly_nearest(x, z, t)[0] for t in TRAILS) < 3.0):
        mat = "Mud"
    elif slope > 0.75 or OLD.pool_distance(x, z) < 1.0:
        mat = "Sandstone"
    else:
        mat = "LeafyGrass"
    if mat == "LeafyGrass" and free(x, z) > 0.0:
        # the stream's and the ponds' beds are mud
        ds = poly_nearest(x, z, STREAM)[0]
        pd = math.hypot(x - POND[0], z - POND[1])
        wd = math.hypot(x - W_POOL[0], z - W_POOL[1])
        if (ds < 5.0 and h < -0.8) or pd < POND[2] - 1.0 or wd < W_POOL[2] - 1.0:
            mat = "Mud"
    return h, mat


TRAILS = []        # visible worn trails (Mud): lists of (x, z), set by jade_lib_sites
MATERIALS = OLD.MATERIALS      # LeafyGrass, Mud, Sandstone: Jade's own, nothing new
HALF = 236                      # the grid covers the island's centre +- this many studs
CELL = 4


def grid():
    """Samples the whole grid: (origin x, origin z, n, heights, material indices) in the engine's order (rows of x), exactly as worldlib does it."""
    centre = CENTRE
    corner_x = math.floor((centre[0] - HALF) / CELL) * CELL
    corner_z = math.floor((centre[2] - HALF) / CELL) * CELL
    n = int(math.ceil((centre[0] + HALF - corner_x) / CELL))
    n = max(n, int(math.ceil((centre[2] + HALF - corner_z) / CELL)))
    heights, mats = [], []
    priority = [("Mud", 2)]
    for j in range(n):
        for i in range(n):
            x = corner_x - centre[0] + (i + 0.5) * CELL
            z = corner_z - centre[2] + (j + 0.5) * CELL
            h, m = height(x, z)
            if h is not None:
                counts = {}
                for sx in (-0.33, 0, 0.33):
                    for sz in (-0.33, 0, 0.33):
                        _, sm = height(x + sx * CELL, z + sz * CELL)
                        if sm:
                            counts[sm] = counts.get(sm, 0) + 1
                for name, need in priority:
                    if counts.get(name, 0) >= need:
                        m = name
                        break
            heights.append(None if h is None else round(h, 2))
            mats.append(0 if h is None else MATERIALS.index(m) + 1)
    return corner_x, corner_z, n, heights, mats

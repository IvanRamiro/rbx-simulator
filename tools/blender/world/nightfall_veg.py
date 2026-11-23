"""Nightfall Citadel's own vegetation, rocks and paths (2026-11-23). Plain Python, no Blender (nightfall_veg_run.py turns the pieces into Blender objects,
renders, QA and FBX). Built on hq_kit's Geo/Piece, in ROBLOX STUDS (x right, y up, z back; a piece's FRONT is -Z), every piece at its own origin with
y = 0 the ground it stands on (feet may sink below). One mesh per piece per material suffix, named Nightfall_<Family>_<Piece>__<Suffix>; no textures:
each suffix takes a Roblox Material and Color from LOOKS.

The shape language is the Demonic territory's: UPRIGHT and ANGULAR. Every piece stands on a vertical axis (nothing leans to a wind), every edge is a hard
facet: trunks are 4 to 8 sided bars (some twisted like a rebar), limbs are straight segments with sharp elbows, foliage is thorns, spikes and iron leaves
(no leaf blobs, no clouds, no curves), stone is hexagonal columns with sheared tops, obsidian shards and battered spires. Colours: charred black, ash
grey, dark iron, deep crimson thorn tips and flowers, ember orange in cracks. This library imports nothing from another map's vegetation code
(hq_kit is the shared geometry container only); the primitives below are its own:

  ptube     a closed faceted tube along a POLYLINE (sharp mitred elbows, optional twist): trunks, limbs, stems, thorn vines
  spike     a closed pyramid or frustum with 3 to 6 sides: thorns, needles, grass blades, spearheads
  thorn     a spike in two materials: a dark stem and a crimson tip
  shard     a closed prism with a faceted, optionally skewed, pyramid tip: obsidian crystal
  convex    a closed convex solid from half-spaces: hexagonal columns, battered spires, chiselled tops, ember veins
  slab      a closed polygon slab: pavers and plates

TREES   Ashthorn (A1 the tiered candelabra, A2 the crowned thorn), Ironpine (B1 the twisted bar with spike stars, B2 the bolt), Shardtree (C1 the
        obsidian tree, C2 the sapling), Cinderstump (D1 the hollow ring of staves round an ember bed, D2 the three-claw stump), GiantBlackthorn (the landmark)
ROCKS   BasaltColumns, BasaltPalisade, ObsidianShards, SplitObelisk, EmberCone, EmberFangs, CragSpires, ShardScatter, and the paths BasaltPave, HexSteps
PLANTS  AshGrassA, AshGrassB, SpiderLilyA, SpiderLilyB, Thornbrake, ThornClimber, Spearleaf, Thornrose, Cinderbush, Ashcap, EmberCrust, AshDrift
"""
import math
import random

import hq_kit as K
from hq_kit import Geo, Piece, vadd, vsub, vmul, vdot, vcross, vnorm, vlen, lerp, TAU

# ======================================================================================================================
# the looks (Roblox Material + colour per material suffix: no texture, no upload)
# ======================================================================================================================
LOOKS = {
    # wood and bark
    "Char": {"Material": "Basalt", "Color": [36, 32, 36]},                        # charred black wood (trunks, limbs, thorn stems)
    "IronBark": {"Material": "CorrodedMetal", "Color": [58, 52, 58]},             # the iron pines' bark and spike stars
    "Thorn": {"Material": "SmoothPlastic", "Color": [172, 26, 36]},               # crimson thorn tips
    # ember
    "Ember": {"Material": "CrackedLava", "Color": [255, 96, 24], "CastShadow": False},   # glowing cracks, embers, lava seams
    # stone
    "Basalt": {"Material": "Basalt", "Color": [56, 52, 58]},                      # basalt columns, pavers, spires
    "Obsidian": {"Material": "Metal", "Color": [26, 24, 34]},                     # glassy black shards
    "Cinder": {"Material": "Asphalt", "Color": [40, 36, 40]},                     # burnt crust, plates, the dark ground patches
    # plants
    "AshBlade": {"Material": "Sand", "Color": [192, 184, 168], "CastShadow": False},   # bone-pale ash grass
    "AshPile": {"Material": "Sand", "Color": [128, 124, 126], "CastShadow": False},    # drifts of grey ash
    "AshCap": {"Material": "Concrete", "Color": [150, 146, 150]},                 # pale fungus caps and stalks
    "SpearBlade": {"Material": "Metal", "Color": [46, 46, 58]},                   # iron leaves
    "DeepCrimson": {"Material": "Fabric", "Color": [96, 10, 24]},                 # stems, roses, dark crimson leaves
    "Crimson": {"Material": "SmoothPlastic", "Color": [206, 28, 46], "CastShadow": False},   # spider lily
}

UP = (0.0, 1.0, 0.0)


def horiz(az):
    return (math.cos(az), 0.0, math.sin(az))


def dirv(az, el):
    """A unit vector at azimuth az about +Y (from +X toward +Z) and elevation el above the horizon."""
    return (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))


def pol(r, az, y=0.0):
    return (r * math.cos(az), y, r * math.sin(az))


def _rot(v, axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    return vadd(vadd(vmul(v, c), vmul(vcross(axis, v), s)), vmul(axis, vdot(axis, v) * (1 - c)))


def _basis(d):
    d = vnorm(d)
    a = (0.0, 1.0, 0.0) if abs(d[1]) < 0.92 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(a, d))
    v = vcross(d, u)
    return u, v


def _ring(c, u, v, r, sides, phase=0.0, sq=1.0):
    return [vadd(c, vadd(vmul(u, math.cos(phase + TAU * k / sides) * r), vmul(v, math.sin(phase + TAU * k / sides) * r * sq))) for k in range(sides)]


def _cap(g, ids, top):
    """Closes a ring: bottom caps run with the ring, top caps against it (the side quads run (k, k+1) up the ring)."""
    if len(ids) <= 4:
        g.face(*(list(reversed(ids)) if top else ids))
        return
    cx = sum(g.v[i][0] for i in ids) / len(ids)
    cy = sum(g.v[i][1] for i in ids) / len(ids)
    cz = sum(g.v[i][2] for i in ids) / len(ids)
    c = g.vert((cx, cy, cz))
    n = len(ids)
    for k in range(n):
        j = (k + 1) % n
        g.face(c, ids[j], ids[k]) if top else g.face(c, ids[k], ids[j])


# ======================================================================================================================
# faceted tubes, spikes, shards
# ======================================================================================================================
def ptube(g, pts, radii, sides=4, phase=0.0, twist=0.0, sq=1.0, caps=(True, True), miter=True, ref=None):
    """A closed tube along the polyline pts (a radius per point). The section turns by `twist` radians per ring (a twisted bar); at an elbow the ring
    stands on the bisector and is stretched in the bend's plane (a mitre), so a sharp corner keeps its thickness. Returns the rings."""
    n = len(pts)
    seg = [vnorm(vsub(pts[i + 1], pts[i])) for i in range(n - 1)]
    T = []
    for i in range(n):
        if i == 0:
            T.append(seg[0])
        elif i == n - 1:
            T.append(seg[-1])
        else:
            s = vadd(seg[i - 1], seg[i])
            T.append(vnorm(s) if vlen(s) > 1e-6 else seg[i])
    if ref is None:
        ref = (0.0, 0.0, 1.0) if abs(T[0][1]) > 0.9 else (0.0, 1.0, 0.0)
    Ns = [vnorm(vcross(vcross(T[0], ref), T[0]))]
    for i in range(1, n):
        ax = vcross(T[i - 1], T[i])
        if vlen(ax) > 1e-9:
            ang = math.acos(max(-1.0, min(1.0, vdot(T[i - 1], T[i]))))
            Ns.append(vnorm(_rot(Ns[-1], vnorm(ax), ang)))
        else:
            Ns.append(Ns[-1])
    Bs = [vnorm(vcross(T[i], Ns[i])) for i in range(n)]
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        stretch = 0.0
        m = None
        if miter and 0 < i < n - 1:
            c = vdot(T[i], seg[i - 1])
            if c < 0.9995:
                nb = vcross(seg[i - 1], seg[i])
                if vlen(nb) > 1e-6:
                    m = vcross(vnorm(nb), T[i])
                    stretch = min(1.0 / max(c, 0.4), 1.7) - 1.0
        ring = []
        for k in range(sides):
            a = phase + twist * i + TAU * k / sides
            w = vadd(vmul(Ns[i], math.cos(a) * r), vmul(Bs[i], math.sin(a) * r * sq))
            if m is not None:
                w = vadd(w, vmul(m, vdot(w, m) * stretch))
            ring.append(g.vert(vadd(p, w)))
        rings.append(ring)
    start = len(g.f)
    for i in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            g.face(rings[i][k], rings[i + 1][k], rings[i + 1][j], rings[i][j])
    if caps[0]:
        _cap(g, rings[0], False)
    if caps[1]:
        _cap(g, rings[-1], True)
    K._orient_solid(g, start)
    return rings


def spike(g, base, d, L, r, sides=3, phase=0.0, kink=None, rt=0.0, sq=1.0):
    """A closed pyramid (rt = 0) or frustum (rt > 0) from `base` along d, length L, base radius r. `kink` shifts the apex sideways (a hooked, irregular
    tip). Triangles: sides + (1 or 2) for a pyramid of 3 or 4 sides. Returns the apex."""
    d = vnorm(d)
    u, v = _basis(d)
    start = len(g.f)
    b = [g.vert(p) for p in _ring(base, u, v, r, sides, phase, sq)]
    tip = vadd(base, vmul(d, L))
    if kink:
        tip = vadd(tip, kink)
    if rt > 0:
        t = [g.vert(p) for p in _ring(tip, u, v, rt, sides, phase, sq)]
        for k in range(sides):
            j = (k + 1) % sides
            g.face(b[k], t[k], t[j], b[j])
        _cap(g, t, True)
    else:
        a = g.vert(tip)
        for k in range(sides):
            j = (k + 1) % sides
            g.face(b[k], a, b[j])
    _cap(g, b, False)
    K._orient_solid(g, start)
    return tip


def thorn(gb, gt, base, d, L, r, split=0.6, sides=3, phase=0.0):
    """A thorn of two materials: a stem (a frustum in gb, r down to 0.5 r) and a crimson tip (a pyramid in gt). Returns the apex."""
    d = vnorm(d)
    mid = vadd(base, vmul(d, L * split))
    spike(gb, base, d, L * split, r, sides, phase, rt=r * 0.5)
    return spike(gt, mid, d, L * (1 - split), r * 0.5, sides, phase)


def shard(g, base, d, L, r, sides=6, tipfrac=0.3, taper=0.88, skew=(0.0, 0.0, 0.0), phase=0.0):
    """An obsidian crystal: a prism of radius r (narrowing to taper * r) capped by a pyramid tip, the apex pushed sideways by `skew` for an irregular
    facet. 6 sides = 24 triangles, 5 sides = 20, 4 sides = 14."""
    d = vnorm(d)
    u, v = _basis(d)
    start = len(g.f)
    b = [g.vert(p) for p in _ring(base, u, v, r, sides, phase)]
    mid = vadd(base, vmul(d, L * (1 - tipfrac)))
    m = [g.vert(p) for p in _ring(mid, u, v, r * taper, sides, phase)]
    a = g.vert(vadd(vadd(base, vmul(d, L)), skew))
    for k in range(sides):
        j = (k + 1) % sides
        g.face(b[k], m[k], m[j], b[j])
        g.face(m[k], a, m[j])
    _cap(g, b, False)
    K._orient_solid(g, start)
    return vadd(base, vmul(d, L))


def trunk_at(pts, y):
    """The (x, z) of a trunk polyline at height y (linear between its knots, which rise monotonically)."""
    for i in range(len(pts) - 1):
        if pts[i][1] <= y <= pts[i + 1][1]:
            t = (y - pts[i][1]) / max(1e-6, pts[i + 1][1] - pts[i][1])
            return pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][2] + (pts[i + 1][2] - pts[i][2]) * t
    return pts[-1][0], pts[-1][2]


def radius_at(pts, radii, y):
    for i in range(len(pts) - 1):
        if pts[i][1] <= y <= pts[i + 1][1]:
            t = (y - pts[i][1]) / max(1e-6, pts[i + 1][1] - pts[i][1])
            return radii[i] + (radii[i + 1] - radii[i]) * t
    return radii[-1]


def surface_pt(pts, radii, y, az, k=1.0):
    """A point on a trunk's surface at height y, azimuth az (k times the radius)."""
    x, z = trunk_at(pts, y)
    r = radius_at(pts, radii, y) * k
    return (x + r * math.cos(az), y, z + r * math.sin(az))


def crack(g, pts, radii, az0, y0, y1, zig=0.35, steps=6, w=0.16, rise=0.06):
    """A glowing crack running up a trunk: a thin triangular rib that zigzags in azimuth, standing `rise` proud of the surface."""
    cp = []
    for i in range(steps + 1):
        t = i / steps
        y = y0 + (y1 - y0) * t
        az = az0 + zig * (1 if i % 2 else -1) * (0.4 + 0.6 * math.sin(math.pi * t))
        cp.append(surface_pt(pts, radii, y, az, 1.0 + rise / max(0.2, radius_at(pts, radii, y))))
    ptube(g, cp, [w] * (steps + 1), 3, phase=az0, caps=(True, True))


# ======================================================================================================================
# convex stone: half-space solids
# ======================================================================================================================
def pl(n, p):
    """The half-space with outward normal n whose boundary passes through point p."""
    n = vnorm(n)
    return (n, vdot(n, p))


def _clip(poly, n, e):
    """Sutherland-Hodgman: the part of the polygon with n . p <= e."""
    out = []
    m = len(poly)
    for i in range(m):
        a, b = poly[i], poly[(i + 1) % m]
        da, db = vdot(n, a) - e, vdot(n, b) - e
        if da <= 1e-9:
            out.append(a)
        if (da < -1e-9 and db > 1e-9) or (da > 1e-9 and db < -1e-9):
            t = da / (da - db)
            out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(len(a))))
    return out


def convex_polys(planes):
    """planes: [((nx, ny, nz), d)] meaning n . p <= d. Returns [(normal, [vertices CCW seen from outside])] for the convex solid they bound."""
    P = []
    for (n, d) in planes:
        l = vlen(n)
        n1, d1 = vnorm(n), d / l
        if any(vdot(n1, m) > 0.99999 and abs(d1 - e) < 1e-4 for (m, e) in P):
            continue
        P.append((n1, d1))
    polys = []
    for i, (n, d) in enumerate(P):
        a = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
        u = vnorm(vcross(n, a))
        v = vcross(n, u)
        c = vmul(n, d)
        R = 400.0
        poly = [vadd(c, vadd(vmul(u, sx * R), vmul(v, sy * R))) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for j, (m, e) in enumerate(P):
            if j == i:
                continue
            poly = _clip(poly, m, e)
            if len(poly) < 3:
                break
        if len(poly) < 3:
            continue
        clean = []
        for p in poly:
            if not clean or vlen(vsub(p, clean[-1])) > 1e-6:
                clean.append(p)
        if len(clean) > 1 and vlen(vsub(clean[0], clean[-1])) <= 1e-6:
            clean.pop()
        if len(clean) < 3:
            continue
        area = 0.0
        for k in range(1, len(clean) - 1):
            area += vlen(vcross(vsub(clean[k], clean[0]), vsub(clean[k + 1], clean[0]))) / 2
        if area < 1e-4:
            continue
        polys.append((n, clean))
    return polys


def add_convex(g, planes):
    """Adds the convex solid bounded by the planes to Geo g (faces triangulated, vertices shared within the solid; those closer than 0.02 are snapped
    together, clipping leaves slivers where three planes nearly meet). Returns the polygons."""
    polys = convex_polys(planes)
    reps = []

    def snap(p):
        for r in reps:
            if abs(r[0] - p[0]) < 0.02 and abs(r[1] - p[1]) < 0.02 and abs(r[2] - p[2]) < 0.02:
                return r
        reps.append(p)
        return p
    snapped = []
    for n, poly in polys:
        q = []
        for p in poly:
            r = snap(p)
            if not q or q[-1] != r:
                q.append(r)
        if len(q) > 1 and q[0] == q[-1]:
            q.pop()
        if len(set(q)) >= 3:
            snapped.append((n, q))
    start = len(g.f)
    cache = {}
    for n, poly in snapped:
        ids = []
        for p in poly:
            key = (round(p[0] / 1e-5), round(p[1] / 1e-5), round(p[2] / 1e-5))
            if key not in cache:
                cache[key] = g.vert(p)
            ids.append(cache[key])
        if len(ids) <= 4:
            g.face(*ids)
        else:
            for k in range(1, len(ids) - 1):
                g.face(ids[0], ids[k], ids[k + 1])
    K._orient_solid(g, start)
    return snapped


def inflate(planes, k, skip_down=True):
    out = []
    for n, d in planes:
        if skip_down and n[1] < -0.95:
            out.append((n, d))
        else:
            out.append((n, d + k * vlen(n)))
    return out


def ground(y=-0.5):
    """The plane that cuts a solid off at y (its foot sunk in the ground)."""
    return ((0.0, -1.0, 0.0), -y)


def polygon_planes(cx, cz, apothems, rot=0.0, taper=0.0):
    """One side plane per entry of apothems (the distance of that side from the centre (cx, cz)), the side k facing azimuth rot + k * TAU / n. taper > 0
    leans every side inward by that tangent (a battered, narrowing solid: the side moves in by taper per stud of height)."""
    n = len(apothems)
    out = []
    for k, a in enumerate(apothems):
        az = rot + TAU * k / n
        c, s = math.cos(az), math.sin(az)
        nrm = vnorm((c, taper, s))
        out.append((nrm, vdot(nrm, (cx + c * a, 0.0, cz + s * a))))
    return out


def top_plane(cx, cz, h, sx=0.0, sz=0.0):
    """A top face through (cx, h, cz) whose normal leans (sx, sz): a sheared, chiselled top."""
    n = vnorm((sx, 1.0, sz))
    return (n, vdot(n, (cx, h, cz)))


def xform(planes, ry=0.0, t=(0.0, 0.0, 0.0), rz=0.0):
    """Turns the solid about z by rz, then about y by ry (yaw), then moves it by t."""
    out = []
    for n, d in planes:
        x, y, z = n
        c, s = math.cos(rz), math.sin(rz)
        x, y = x * c - y * s, x * s + y * c
        c, s = math.cos(ry), math.sin(ry)
        x, z = x * c + z * s, -x * s + z * c
        n2 = (x, y, z)
        out.append((n2, d + vdot(n2, t)))
    return out


def slab(g, ring, y0, y1, bev=0.0):
    """A closed convex slab on a polygon ring ((x, z) points): wall from y0 to y1 - bev, an optional bevel ring inset by bev reaching the exact flat top at
    y1, caps fanned from the centroid."""
    n = len(ring)
    cx = sum(p[0] for p in ring) / n
    cz = sum(p[1] for p in ring) / n
    start = len(g.f)

    def shrink(p, k):
        dx, dz = p[0] - cx, p[1] - cz
        d = math.hypot(dx, dz) or 1.0
        return (p[0] - dx / d * k, p[1] - dz / d * k)
    bot = [g.vert((x, y0, z)) for (x, z) in ring]
    if bev > 0:
        mid = [g.vert((x, y1 - bev, z)) for (x, z) in ring]
        top = [g.vert((x, y1, z)) for (x, z) in [shrink(p, bev) for p in ring]]
        for i in range(n):
            j = (i + 1) % n
            g.face(bot[i], mid[i], mid[j], bot[j])
            g.face(mid[i], top[i], top[j], mid[j])
    else:
        top = [g.vert((x, y1, z)) for (x, z) in ring]
        for i in range(n):
            j = (i + 1) % n
            g.face(bot[i], top[i], top[j], bot[j])
    cb = g.vert((cx, y0, cz))
    ct = g.vert((cx, y1, cz))
    for i in range(n):
        j = (i + 1) % n
        g.face(cb, bot[i], bot[j])
        g.face(ct, top[j], top[i])
    K._orient_solid(g, start)


def hex_ring(cx, cz, a, rot=0.0):
    """The 6 corners of a regular hexagon of apothem a (flat sides facing rot + k * 60 degrees)."""
    R = a / math.cos(math.pi / 6)
    return [(cx + R * math.cos(rot + TAU * (k + 0.5) / 6), cz + R * math.sin(rot + TAU * (k + 0.5) / 6)) for k in range(6)]


# ======================================================================================================================
# checks that run in plain Python (before Blender): winding, open edges, degenerate faces
# ======================================================================================================================
def geo_problems(g):
    """(inconsistent directed edges, open edges, degenerate faces, zero-length edges) of one Geo."""
    directed = {}
    for f in g.f:
        for a, b in zip(f, f[1:] + f[:1]):
            directed[(a, b)] = directed.get((a, b), 0) + 1
    inc = sum(1 for c in directed.values() if c > 1)
    opened = sum(1 for (a, b) in directed if (b, a) not in directed)
    deg = 0
    zero = 0
    for f in g.f:
        for a, b in zip(f, f[1:] + f[:1]):
            if vlen(vsub(g.v[a], g.v[b])) < 1e-7:
                zero += 1
        p0 = g.v[f[0]]
        ar = 0.0
        for k in range(1, len(f) - 1):
            ar += vlen(vcross(vsub(g.v[f[k]], p0), vsub(g.v[f[k + 1]], p0))) / 2
        if ar < 1e-9:
            deg += 1
    return inc, opened, deg, zero


# ======================================================================================================================
# TREES
# ======================================================================================================================
def _roots(g, pts, radii, n, rng, L=3.6, r=0.6, y=1.5, sides=4, off=0.0):
    """Angular root claws gripping the ground: n spikes leaving the trunk at height y, heading out and down so their tips end just under the ground."""
    x0, z0 = trunk_at(pts, y)
    rr = radius_at(pts, radii, y)
    for i in range(n):
        az = off + TAU * i / n + rng.uniform(-0.2, 0.2)
        base = (x0 + math.cos(az) * rr * 0.6, y, z0 + math.sin(az) * rr * 0.6)
        d = vnorm((math.cos(az) * 0.85, -0.5 - rng.uniform(0.0, 0.12), math.sin(az) * 0.85))
        spike(g, base, d, L * rng.uniform(0.92, 1.12), r, sides, phase=az)


def _elbow_arm(gc, gt, p0, az, R, s, rng, barbs=True, spear=1.0):
    """A bare limb of the Ashthorn: it leaves the trunk almost level, turns a sharp elbow and climbs, and ends in a crimson-tipped spear; two barbs on it."""
    out = horiz(az)
    p1 = vadd(p0, vadd(vmul(out, 0.6 * R), (0.0, 0.25 + 0.08 * R, 0.0)))
    p2 = vadd(p1, vadd(vmul(out, 0.26 * R), (0.0, 0.45 * R + 0.6, 0.0)))
    ptube(gc, [p0, p1, p2], [0.34 * s, 0.26 * s, 0.17 * s], 4, phase=az)
    thorn(gc, gt, p2, vnorm(vadd(vmul(out, 0.18), UP)), (1.4 + 0.32 * R) * spear, 0.17 * s, 0.55, 3, phase=az)
    if barbs:
        b1 = vadd(p0, vmul(vsub(p1, p0), 0.55))
        spike(gc, b1, vnorm(vadd(vmul(out, 0.5), (0.0, -0.8, 0.0))), 0.9 * s + 0.3, 0.1 * s + 0.04, 3)
        spike(gc, p1, vnorm(vadd(out, (0.0, 0.3, rng.uniform(-0.2, 0.2)))), 0.8 * s + 0.3, 0.1 * s + 0.04, 3)


def ashthorn(variant):
    """The Ashthorn, a dead ash-black tree with crimson-tipped thorns, every part straight and sharp. A1, the tiered candelabra: a straight five-sided
    trunk 15 high carrying six tiers of bare limbs that leave it level, turn a sharp elbow and climb to a crimson spear (the reach shortens from 4.6 to
    1.5 going up, each tier turned 50 degrees from the one below), three spears crown it. A2, the crowned thorn: a short charred six-sided bole 6.6
    high ringed by three whorls of thorns and capped by a crown of nine kinked spears fanning up to 16 high."""
    P = Piece()
    rng = random.Random(100 + variant)
    gc = P.geo("Char")
    gt = P.geo("Thorn")
    if variant == 0:
        trunk = [(0.0, -0.7, 0.0), (0.25, 1.6, 0.1), (-0.1, 4.4, 0.25), (0.35, 7.6, -0.1), (0.0, 10.8, 0.15), (0.15, 13.6, 0.0), (0.0, 15.4, 0.0)]
        radii = [1.7, 1.25, 0.98, 0.76, 0.52, 0.34, 0.2]
        ptube(gc, trunk, radii, 5, phase=0.3)
        _roots(gc, trunk, radii, 4, rng, L=3.6, r=0.7, y=1.5)
        tiers = [(3.4, 4.6, 4), (5.5, 4.1, 4), (7.5, 3.5, 3), (9.4, 2.9, 3), (11.2, 2.2, 3), (12.9, 1.5, 2)]
        for i, (h, R, n) in enumerate(tiers):
            s = 0.55 + 0.5 * R / 4.6
            for k in range(n):
                az = 0.9 * i + TAU * k / n + rng.uniform(-0.18, 0.18)
                _elbow_arm(gc, gt, surface_pt(trunk, radii, h, az, 0.85), az, R * rng.uniform(0.92, 1.08), s, rng)
        top = trunk[-1]
        for (el, az, L) in ((90.0, 0.0, 3.4), (74.0, 0.6, 2.5), (74.0, 3.7, 2.5)):
            thorn(gc, gt, vadd(top, (0.0, -0.3, 0.0)), dirv(az, math.radians(el)), L, 0.2, 0.55, 3, phase=az)
    else:
        trunk = [(0.0, -0.7, 0.0), (0.0, 1.6, 0.0), (0.35, 4.2, 0.15), (0.1, 6.6, 0.0)]
        radii = [1.9, 1.5, 1.2, 0.95]
        ptube(gc, trunk, radii, 6, phase=0.2)
        _roots(gc, trunk, radii, 5, rng, L=3.8, r=0.8, y=1.6, sides=4)
        for (y, n, L, off) in ((1.9, 6, 1.5, 0.0), (3.5, 6, 1.35, 0.5), (5.1, 5, 1.2, 0.2)):
            for k in range(n):
                az = off + TAU * k / n + rng.uniform(-0.12, 0.12)
                thorn(gc, gt, surface_pt(trunk, radii, y, az, 0.9), dirv(az, math.radians(8.0)), L, 0.24, 0.55, 3, phase=az)
        crown = (trunk[-1][0], 6.3, trunk[-1][2])
        for i, (az, tilt, L) in enumerate(((0.0, 12.0, 9.2), (0.9, 24.0, 7.6), (1.9, 30.0, 8.4), (2.9, 26.0, 6.6), (3.9, 32.0, 8.0), (4.9, 22.0, 7.2), (5.7, 28.0, 6.2),
                                           (1.4, 8.0, 4.4), (4.4, 10.0, 4.0))):
            d = dirv(az, math.radians(90.0 - tilt))
            p0 = vadd(crown, vmul(horiz(az), 0.45))
            p1 = vadd(p0, vmul(d, L * 0.5))
            d2 = vnorm(vsub(d, vmul(horiz(az), 0.3)))
            p2 = vadd(p1, vmul(d2, L * 0.3))
            ptube(gc, [p0, p1, p2], [0.5, 0.36, 0.24], 4, phase=az)
            thorn(gc, gt, p2, d2, L * 0.28, 0.24, 0.4, 3, phase=az)
    return P


def _starburst(gn, gt, c, n, L, rng, el=(12.0, 70.0)):
    """A spike star on the end of a limb: n needles radiating from c in alternating low and high rays (a spiked ball), one more straight up with a crimson tip."""
    r = 0.075 * L
    for k in range(n):
        az = TAU * k / n + rng.uniform(-0.2, 0.2)
        e = math.radians(el[0] if k % 2 == 0 else el[1])
        spike(gn, c, dirv(az, e), L * rng.uniform(0.85, 1.1), r, 3, phase=az)
    thorn(gn, gt, c, UP, L * 1.15, r * 1.1, 0.55, 3)


def ironpine(variant):
    """The Ironpine, a twisted iron-bark pine. The trunk is a four-sided bar that turns on its own axis as it climbs (a twisted rebar), the limbs are
    shorter twisted bars, and the 'needles' are stars of straight iron spikes, a crimson tip on each star's top spike. B1, the mast: 17 high, five
    whorls of three limbs, each carrying a spike star, a large star at the top. B2, the bolt: a trunk that kinks twice like a lightning bolt, 14 high,
    a spike star at each of its three ends and a hooked stub."""
    P = Piece()
    rng = random.Random(200 + variant)
    gi = P.geo("IronBark")
    gn = gi                      # the needles are iron too: one MeshPart for bark and spikes
    gt = P.geo("Thorn")
    if variant == 0:
        ys = [-0.7, 0.8, 2.3, 3.8, 5.3, 6.8, 8.3, 9.8, 11.3, 12.8, 14.3, 15.8, 17.0]
        trunk = [(0.28 * math.sin(i * 1.3), y, 0.28 * math.cos(i * 1.7)) for i, y in enumerate(ys)]
        radii = [1.5] + [1.25 * (1 - i / 12.0) + 0.3 * (i / 12.0) for i in range(1, 13)]
        ptube(gi, trunk, radii, 4, phase=0.4, twist=0.32)
        _roots(gi, trunk, radii, 4, rng, L=3.6, r=0.62, y=1.5, sides=4)
        whorls = [(4.6, 3.6), (7.4, 3.2), (10.0, 2.8), (12.4, 2.3), (14.4, 1.8)]
        for i, (h, R) in enumerate(whorls):
            for k in range(3):
                az = 0.65 * i + TAU * k / 3 + rng.uniform(-0.15, 0.15)
                s = 0.6 + 0.4 * R / 3.6
                p0 = surface_pt(trunk, radii, h, az, 0.8)
                out = horiz(az)
                p1 = vadd(p0, vadd(vmul(out, 0.65 * R), (0.0, 0.55, 0.0)))
                p2 = vadd(p1, vadd(vmul(out, 0.35 * R), (0.0, 0.7, 0.0)))
                ptube(gi, [p0, p1, p2], [0.34 * s, 0.27 * s, 0.2 * s], 4, phase=az, twist=0.5)
                _starburst(gn, gt, p2, 7, 2.3 * s + 0.2, rng)
        _starburst(gn, gt, vadd(trunk[-1], (0.0, 0.1, 0.0)), 9, 3.3, rng, el=(14.0, 62.0))
    else:
        trunk = [(0.0, -0.7, 0.0), (0.1, 3.2, 0.0), (2.9, 5.4, 0.3), (2.9, 8.8, 0.3), (0.1, 10.9, -0.2), (0.1, 13.4, -0.2)]
        radii = [1.4, 1.1, 0.95, 0.82, 0.66, 0.42]
        ptube(gi, trunk, radii, 4, phase=0.4, twist=0.5)
        _roots(gi, trunk, radii, 5, rng, L=3.6, r=0.66, y=1.5, sides=4)
        s1 = [(2.9, 5.4, 0.3), (4.5, 6.0, 0.7), (5.4, 6.9, 0.9)]
        ptube(gi, [vadd(s1[0], (0.0, 0.0, 0.0)), s1[1], s1[2]], [0.5, 0.36, 0.26], 4, phase=0.4, twist=0.5)
        _starburst(gn, gt, vadd(s1[2], (0.0, 0.05, 0.0)), 7, 2.5, rng)
        s2 = [(0.1, 10.9, -0.2), (-1.6, 11.7, -0.5), (-2.5, 12.9, -0.4)]
        ptube(gi, s2, [0.46, 0.34, 0.24], 4, phase=0.4, twist=0.5)
        _starburst(gn, gt, vadd(s2[2], (0.0, 0.05, 0.0)), 7, 2.4, rng)
        _starburst(gn, gt, vadd(trunk[-1], (0.0, 0.1, 0.0)), 9, 3.2, rng, el=(14.0, 62.0))
        # a hooked stub on the lower kink, two spears out of the middle limb
        spike(gi, (2.9, 7.0, 0.3), vnorm((1.0, 0.25, 0.1)), 2.4, 0.34, 4, phase=0.4)
        spike(gn, (0.5, 4.2, 0.1), vnorm((-1.0, 0.6, 0.3)), 2.4, 0.2, 3)
    return P


def shardtree(variant):
    """The Shardtree, a tree grown of black glass. A faceted six-sided obsidian trunk branches in tiers of crystal prisms that climb at 40 to 55
    degrees, and its crown is a fan of five tall shards round a central one; small ember shards sit in the joints like buds. C1: 15 high, four tiers
    of branches. C2, the sapling: 8.5 high, three branches and a small crown."""
    P = Piece()
    rng = random.Random(300 + variant)
    go = P.geo("Obsidian")
    ge = P.geo("Ember")
    if variant == 0:
        trunk = [(0.0, -0.7, 0.0), (0.0, 2.4, 0.0), (0.15, 5.4, 0.05), (0.1, 7.5, 0.0)]
        radii = [1.55, 1.3, 1.02, 0.72]
        ptube(go, trunk, radii, 6, phase=0.2, twist=0.14)
        for i, (y, L) in enumerate(((2.6, 4.6), (4.0, 4.2), (5.4, 3.6), (6.6, 3.0))):
            for k in range(2):
                az = 1.1 * i + k * math.pi + rng.uniform(-0.25, 0.25)
                el = math.radians(rng.uniform(38.0, 55.0))
                base = surface_pt(trunk, radii, y, az, 0.6)
                shard(go, base, dirv(az, el), L, 0.36 + 0.07 * L, 5, 0.32, skew=vmul(horiz(az + 1.0), 0.3))
        for i in range(4):
            az = 0.5 + 1.7 * i
            y = (3.2, 4.4, 5.6, 6.2)[i]
            shard(ge, surface_pt(trunk, radii, y, az, 0.9), dirv(az, math.radians(20.0)), 1.5, 0.2, 4, 0.4)
        c = (0.1, 7.2, 0.0)
        shard(go, c, UP, 7.8, 0.62, 6, 0.3, skew=(0.2, 0.0, -0.15))
        for k, (L, tilt) in enumerate(((5.8, 18.0), (5.2, 24.0), (4.6, 14.0), (5.0, 28.0), (4.2, 20.0))):
            az = 0.4 + TAU * k / 5
            shard(go, vadd(c, vmul(horiz(az), 0.3)), dirv(az, math.radians(90.0 - tilt)), L, 0.44, 5, 0.32, skew=vmul(horiz(az + 1.5), 0.25))
    else:
        trunk = [(0.0, -0.7, 0.0), (0.0, 1.8, 0.0), (0.1, 3.8, 0.0)]
        radii = [1.0, 0.8, 0.55]
        ptube(go, trunk, radii, 6, phase=0.2, twist=0.12)
        for i, (y, L) in enumerate(((1.9, 3.2), (2.8, 2.8), (3.4, 2.4))):
            az = 0.8 + 2.1 * i
            shard(go, surface_pt(trunk, radii, y, az, 0.6), dirv(az, math.radians(44.0 + 4 * i)), L, 0.3 + 0.05 * L, 5, 0.32, skew=vmul(horiz(az + 1.0), 0.2))
        c = (0.1, 3.6, 0.0)
        shard(go, c, UP, 4.9, 0.46, 6, 0.3, skew=(0.15, 0.0, 0.1))
        for k, (L, tilt) in enumerate(((3.6, 20.0), (3.2, 26.0), (3.4, 16.0), (2.9, 30.0))):
            az = 0.6 + TAU * k / 4
            shard(go, vadd(c, vmul(horiz(az), 0.2)), dirv(az, math.radians(90.0 - tilt)), L, 0.32, 5, 0.32, skew=vmul(horiz(az + 1.5), 0.2))
        shard(ge, surface_pt(trunk, radii, 2.4, 3.6, 0.9), dirv(3.6, math.radians(20.0)), 1.3, 0.18, 4, 0.4)
    return P


def _stave(planes_h, az, Ri, Ro, h, slope, taper, gap=0.05, span=TAU / 6):
    """One wedge-shaped stave of a hollow stump: between inner radius Ri and outer radius Ro (battered by taper), azimuth az +- span / 2, top sheared by slope."""
    c = horiz(az)
    nrm = vnorm((c[0], taper, c[2]))
    outer = (nrm, vdot(nrm, (c[0] * Ro, 0.0, c[2] * Ro)))
    inner = ((-c[0], 0.0, -c[2]), -Ri)
    a_hi, a_lo = az + span / 2, az - span / 2
    t_hi = (-math.sin(a_hi), 0.0, math.cos(a_hi))
    t_lo = (-math.sin(a_lo), 0.0, math.cos(a_lo))
    side_hi = (t_hi, -gap)
    side_lo = (vmul(t_lo, -1.0), -gap)
    sx, sz = slope
    top = top_plane(c[0] * (Ri + Ro) / 2, c[2] * (Ri + Ro) / 2, h, sx, sz)
    return [outer, inner, side_hi, side_lo, top, ground()]


def cinderstump(variant):
    """The Cinderstump, the burnt stump of a tree the fire took down to its heart. D1, the hollow: six battered charred staves in a ring (outer radius
    3, inner 1.5), heights from 2.8 to 7.6 and every top sheared at its own angle, round a bed of glowing embers; ember cracks run up two staves and
    three ember-tipped thorns stand on the highest. D2, the three claws: three tall five-sided pillars of unequal height (11, 8.2, 5.5) pressed
    together, chiselled tops, an ember core showing in the gaps between them, root claws and two ember-tipped thorns."""
    P = Piece()
    rng = random.Random(400 + variant)
    gc = P.geo("Char")
    ge = P.geo("Ember")
    gt = ge                      # the thorns of a burnt stump are tipped with embers: one MeshPart less
    if variant == 0:
        heights = [7.6, 5.4, 3.4, 6.4, 4.4, 2.8]
        slopes = [(0.55, 0.1), (-0.3, 0.6), (0.2, -0.7), (-0.6, -0.2), (0.4, 0.5), (-0.1, -0.5)]
        for k in range(6):
            az = 0.3 + TAU * k / 6
            add_convex(gc, _stave(None, az, 1.5, 3.0, heights[k], slopes[k], 0.12))
        add_convex(ge, polygon_planes(0.0, 0.0, [1.25] * 8, rot=0.2, taper=0.55) + [top_plane(0.0, 0.0, 1.7, 0.1, 0.0), ground()])
        add_convex(ge, polygon_planes(0.5, -0.3, [0.5] * 5, rot=0.6, taper=0.3) + [top_plane(0.5, -0.3, 2.3, 0.2, 0.1), ground()])
        for k, az0 in ((0, 0.3), (3, 0.3 + TAU * 3 / 6)):
            c = horiz(az0 + TAU * k / 6 - 0.3)
            for dz, (y0, y1) in ((-0.28, (0.6, 4.4)), (0.4, (0.5, 3.0))):
                a = 0.3 + TAU * k / 6 + dz
                pts, w = [], 0.1
                for i in range(6):
                    t = i / 5.0
                    y = y0 + (y1 - y0) * t
                    zz = a + 0.12 * (1 if i % 2 else -1) * math.sin(math.pi * t)
                    r = 3.0 - 0.12 * y + 0.04
                    pts.append((r * math.cos(zz), y, r * math.sin(zz)))
                ptube(ge, pts, [0.13] * 6, 3, phase=a)
        for k in (0, 3, 1):
            az = 0.3 + TAU * k / 6
            nrm = vnorm((math.cos(az), 0.12, math.sin(az)))
            sx, sz = slopes[k]
            cx, cz = math.cos(az) * 2.25, math.sin(az) * 2.25
            y_top = heights[k] - (sx * 0.0 + sz * 0.0)
            thorn(gc, gt, (cx, y_top - 0.2, cz), UP, 2.4 if k == 0 else 1.9, 0.26, 0.55, 3, phase=az)
        for k in range(5):
            az = 0.5 + TAU * k / 5
            spike(gc, pol(2.6, az, 1.4), vnorm((math.cos(az) * 0.85, -0.5, math.sin(az) * 0.85)), 3.0, 0.55, 4, phase=az)
    else:
        spec = [((0.0, 0.0), 1.55, 11.0, (0.9, 0.3), 0.55), ((1.9, -0.95), 1.3, 8.2, (-0.7, 0.4), 1.1), ((1.15, 1.7), 1.1, 5.5, (0.2, -0.9), 0.2)]
        for (c, a, h, sl, rot) in spec:
            add_convex(gc, polygon_planes(c[0], c[1], [a, a * 0.93, a * 1.04, a * 0.97, a * 1.0], rot=rot, taper=0.06) + [top_plane(c[0], c[1], h, sl[0], sl[1]), ground()])
        add_convex(ge, polygon_planes(1.0, 0.1, [0.85] * 4, rot=0.2, taper=0.12) + [top_plane(1.0, 0.1, 3.4, 0.2, 0.2), ground()])
        _roots(gc, [(0.9, -0.7, 0.2), (0.9, 5.0, 0.2)], [2.2, 2.0], 5, rng, L=3.6, r=0.6, y=1.8, sides=4)
        thorn(gc, gt, (1.15, 5.2, 1.7), UP, 2.2, 0.26, 0.55, 3)
        thorn(gc, gt, (1.9, 7.9, -0.95), UP, 2.4, 0.28, 0.55, 3)
        for (y0, y1, a) in ((0.8, 8.6, 5.1), (0.8, 5.0, 3.9)):
            pts = []
            for i in range(7):
                t = i / 6.0
                y = y0 + (y1 - y0) * t
                zz = a + 0.16 * (1 if i % 2 else -1) * math.sin(math.pi * t)
                r = 1.45 + 0.06 * (1 - y / 12) - 0.06 * y + 0.04
                pts.append((r * math.cos(zz), y, r * math.sin(zz)))
            ptube(ge, pts, [0.13] * 7, 3, phase=a)
    return P


def giant_blackthorn():
    """The Black Heart, the landmark: a colossal dead thorn tree 47 high held up from the ground by six leaning talons of black stone. An eight-sided
    trunk (radius 3.1 at the foot, 0.55 at 35) climbs straight with a few small kinks; seven tiers of limbs leave it (reach 8.5 at the bottom, 3.4 at
    the top) as three-knuckle arms that turn up into crimson-tipped spears 5 to 2 long; a crown of one central spear and four kinked outer ones;
    five glowing ember cracks run up the trunk. Three meshes: Char (wood and talons), Thorn, Ember. The Char mesh is the one landmark's price."""
    P = Piece()
    rng = random.Random(777)
    gc = P.geo("Char")
    gt = P.geo("Thorn")
    ge = P.geo("Ember")
    gb = gc                      # the talons are the same black stone as the wood: one MeshPart less
    trunk = [(0.0, 2.5, 0.0), (0.4, 7.0, 0.2), (-0.2, 12.0, 0.3), (0.5, 17.0, -0.2), (0.0, 22.0, 0.2), (0.3, 27.0, 0.0), (0.0, 31.0, 0.0), (0.0, 35.0, 0.0)]
    radii = [3.1, 2.7, 2.3, 1.9, 1.5, 1.1, 0.8, 0.55]
    ptube(gc, trunk, radii, 8, phase=0.2)
    # six talons of black stone leaning in on the foot, and the mound they stand on
    for k in range(6):
        az = TAU * k / 6 + rng.uniform(-0.15, 0.15)
        h = rng.uniform(4.2, 7.4)
        R = rng.uniform(3.6, 4.6)
        base = polygon_planes(0.0, 0.0, [1.4, 1.2, 1.5, 1.3, 1.45], rot=rng.uniform(0, 1), taper=0.12) + [top_plane(0.0, 0.0, h, rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)), ground()]
        planes = xform(xform(base, 0.0, (R, 0.0, 0.0), rz=0.26), -az)
        add_convex(gb, planes)
    add_convex(gb, polygon_planes(0.0, 0.0, [5.6, 5.2, 5.8, 5.3, 5.6, 5.0, 5.7], rot=0.3, taper=0.45) + [top_plane(0.0, 0.0, 2.2, 0.0, 0.0), ground()])
    # limb tiers
    tiers = [(8.0, 8.5, 5), (11.5, 8.0, 5), (15.0, 7.2, 4), (18.5, 6.4, 4), (22.0, 5.4, 4), (25.5, 4.4, 3), (28.5, 3.4, 3)]
    for i, (h, R, n) in enumerate(tiers):
        s = 0.5 + 0.5 * R / 8.5
        for k in range(n):
            az = 0.8 * i + TAU * k / n + rng.uniform(-0.2, 0.2)
            Rk = R * rng.uniform(0.9, 1.1)
            p0 = surface_pt(trunk, radii, h, az, 0.85)
            out = horiz(az)
            p1 = vadd(p0, vadd(vmul(out, 0.5 * Rk), (0.0, 0.5 + 0.05 * Rk, 0.0)))
            p2 = vadd(p1, vadd(vmul(out, 0.3 * Rk), (0.0, 0.1 * Rk, 0.0)))
            p3 = vadd(p2, vadd(vmul(out, 0.12 * Rk), (0.0, 0.5 * Rk + 0.8, 0.0)))
            ptube(gc, [p0, p1, p2, p3], [0.95 * s, 0.75 * s, 0.55 * s, 0.38 * s], 4, phase=az)
            thorn(gc, gt, p3, vnorm(vadd(vmul(out, 0.15), UP)), 2.0 + 0.45 * Rk, 0.34 * s, 0.55, 3, phase=az)
            spike(gc, vadd(p0, vmul(vsub(p1, p0), 0.6)), vnorm(vadd(vmul(out, 0.5), (0.0, -0.8, 0.0))), 1.7 * s + 0.5, 0.2 * s + 0.08, 3)
            spike(gc, p2, vnorm(vadd(out, (0.0, 0.5, rng.uniform(-0.3, 0.3)))), 1.4 * s + 0.5, 0.18 * s + 0.08, 3)
    # the crown
    top = trunk[-1]
    ptube(gc, [vadd(top, (0.0, -0.5, 0.0)), (0.4, 38.0, 0.2), (0.1, 41.2, 0.0)], [0.55, 0.42, 0.28], 4, phase=0.3)
    thorn(gc, gt, (0.1, 41.2, 0.0), UP, 5.6, 0.28, 0.45, 3)
    for k, (tilt, L) in enumerate(((30.0, 10.0), (24.0, 8.6), (32.0, 9.2), (26.0, 8.0))):
        az = 0.4 + TAU * k / 4
        d = dirv(az, math.radians(90.0 - tilt))
        p0 = vadd(top, (0.0, -0.4, 0.0))
        p1 = vadd(p0, vmul(d, L * 0.5))
        d2 = vnorm(vsub(d, vmul(horiz(az), 0.35)))
        p2 = vadd(p1, vmul(d2, L * 0.3))
        ptube(gc, [p0, p1, p2], [0.5, 0.38, 0.26], 4, phase=az)
        thorn(gc, gt, p2, d2, L * 0.3, 0.26, 0.4, 3, phase=az)
    for i, az in enumerate((0.3, 1.5, 2.8, 4.0, 5.2)):
        crack(ge, trunk, radii, az, 4.5 + 0.7 * i, 20.0 + 1.8 * i, zig=0.22, steps=7, w=0.2, rise=0.08)
    return P


# ======================================================================================================================
# ROCKS AND PATHS
# ======================================================================================================================
def frustum(cx, cz, a0, y0, y1, taper=0.0, rot=0.0, n=4, tops=None, jit=None):
    """Planes of an n-sided solid between y0 and y1 whose sides are battered inward by `taper` per stud; a0 is the apothem AT y0. tops: an optional
    sheared top (sx, sz) instead of the flat one. jit: a list of n apothem factors."""
    ap = [(a0 + taper * y0) * (jit[k] if jit else 1.0) for k in range(n)]
    top = top_plane(cx, cz, y1, tops[0], tops[1]) if tops else top_plane(cx, cz, y1)
    return polygon_planes(cx, cz, ap, rot=rot, taper=taper) + [top, ((0.0, -1.0, 0.0), -y0)]


def hex_column(g, cx, cz, a, h, rot, tops, taper=0.0, y0=-0.5):
    add_convex(g, polygon_planes(cx, cz, [a] * 6, rot=rot, taper=taper) + [top_plane(cx, cz, h, tops[0], tops[1]), ground(y0)])


def basalt_columns():
    """The causeway: a cluster of hexagonal basalt columns of thirteen different heights, up to 8.6 in the middle and falling off to the edge, each one
    thinner than its cell (there is a gap between them), flat-sided and every top sheared to its own chisel. Stands upright, 9 across."""
    P = Piece()
    rng = random.Random(500)
    g = P.geo("Basalt")
    s = 2.3
    cells = []
    for j in range(-2, 3):
        for i in range(-2, 3):
            x = (i + 0.5 * (j % 2)) * s
            z = j * s * 0.866
            d = math.hypot(x - 0.3, z + 0.2)
            if d > 4.5:
                continue
            cells.append((x, z, d))
    for (x, z, d) in cells:
        h = 8.6 - 1.45 * d + rng.uniform(-0.8, 0.8)
        if h < 1.4:
            continue
        a = rng.uniform(0.74, 1.02)
        az = rng.uniform(0.0, TAU)
        mag = rng.uniform(0.45, 1.0)
        hex_column(g, x + rng.uniform(-0.06, 0.06), z + rng.uniform(-0.06, 0.06), a, h, rng.uniform(-0.12, 0.12), (mag * math.cos(az), mag * math.sin(az)), taper=0.012)
    return P


def basalt_palisade():
    """The palisade: nine hexagonal basalt columns in a row 18 long, heights 2.8 to 8.6 in no order, the tops chiselled, a battlement the mountain made. The
    row is a wall for a path's edge or the back of a court."""
    P = Piece()
    rng = random.Random(510)
    g = P.geo("Basalt")
    hs = [6.0, 3.4, 7.4, 4.5, 8.6, 5.1, 6.6, 2.8, 4.2]
    for i, h in enumerate(hs):
        x = (i - 4) * 2.2 + rng.uniform(-0.1, 0.1)
        hex_column(g, x, rng.uniform(-0.3, 0.3), rng.uniform(0.86, 1.04), h, rng.uniform(-0.1, 0.1), (rng.choice((-1, 1)) * rng.uniform(0.5, 1.0), rng.uniform(-0.3, 0.3)), taper=0.015)
    return P


def obsidian_shards():
    """The obsidian cluster: nine black glass shards rising out of a low mound of the same black stone, a central one 9 high and 0.95 thick, a ring of five at 12 to 22
    degrees from the vertical (4.6 to 7 long), a ring of four low ones (2.6 to 3.6); every tip skewed to its own facet. Upright, 6 across."""
    P = Piece()
    rng = random.Random(520)
    go = P.geo("Obsidian")
    gb = go                      # the mound is the same black stone: one MeshPart
    add_convex(gb, polygon_planes(0.0, 0.0, [2.9, 2.6, 3.0, 2.7, 2.9, 2.5, 3.0], rot=0.3, taper=0.5) + [top_plane(0.0, 0.0, 1.0), ground()])
    shard(go, (0.0, 0.5, 0.0), dirv(0.4, math.radians(87.0)), 9.0, 0.95, 6, 0.3, skew=(0.3, 0.0, -0.2))
    for k, (L, tilt) in enumerate(((6.4, 14.0), (5.0, 20.0), (7.0, 12.0), (4.6, 22.0), (5.8, 16.0))):
        az = 0.5 + TAU * k / 5
        shard(go, vadd(pol(1.25, az), (0.0, 0.4, 0.0)), dirv(az, math.radians(90.0 - tilt)), L, 0.58, 5, 0.32, skew=vmul(horiz(az + 1.4), 0.3), phase=az)
    for k, (L, tilt) in enumerate(((3.4, 30.0), (2.6, 34.0), (3.6, 28.0), (2.9, 32.0))):
        az = 1.2 + TAU * k / 4
        shard(go, vadd(pol(2.2, az), (0.0, 0.3, 0.0)), dirv(az, math.radians(90.0 - tilt)), L, 0.4, 4, 0.34, skew=vmul(horiz(az + 1.0), 0.2), phase=az)
    return P


def split_obelisk():
    """The split obelisk: a four-sided basalt shaft 11.6 high broken into three stacked parts that have slipped against each other (the middle shifted
    0.5 and turned 9 degrees, the top a sheared pyramid with an oblique break), a seam of ember glowing in each joint, and a fallen piece of shaft
    leaning at the foot. Upright."""
    P = Piece()
    gb = P.geo("Basalt")
    ge = P.geo("Ember")
    add_convex(gb, frustum(0.0, 0.0, 1.5, -0.5, 5.2, taper=0.045, rot=0.1))
    add_convex(gb, frustum(0.5, -0.25, 1.15, 5.3, 9.9, taper=0.05, rot=0.26))
    add_convex(gb, frustum(0.3, -0.35, 0.86, 10.0, 11.7, taper=0.34, rot=0.2, tops=(0.8, 0.25)))
    add_convex(ge, frustum(0.05, -0.05, 1.22, 5.18, 5.32, rot=0.42))
    add_convex(ge, frustum(0.4, -0.3, 0.92, 9.88, 10.02, rot=0.05))
    fall = xform(frustum(0.0, 0.0, 0.95, 0.0, 3.0, taper=0.04, rot=0.5, tops=(0.6, 0.0)), 0.0, (0.0, 0.0, 0.0), rz=0.9)
    fall = xform(fall, -0.3, (3.0, 0.2, 0.6)) + [ground(-0.35)]
    add_convex(gb, fall)
    return P


def ember_cone():
    """The ember cone: a battered eight-sided basalt cone 4 high and 7 across with a crater of glowing ember at its top (a raised disc), four ember cracks
    running down the flanks from the rim, three basalt shards on the rim and three low blocks at the foot. Upright, symmetrical in plan."""
    P = Piece()
    rng = random.Random(530)
    gb = P.geo("Basalt")
    ge = P.geo("Ember")
    taper = (3.4 - 1.15) / 4.0
    add_convex(gb, polygon_planes(0.0, 0.0, [3.4] * 8, rot=0.0, taper=taper) + [top_plane(0.0, 0.0, 4.0), ground()])
    add_convex(ge, frustum(0.0, 0.0, 1.0, 3.92, 4.18, rot=0.39, n=8))
    for k in range(4):
        az0 = TAU * (2 * k + 1) / 8 + 0.0
        pts = []
        for i in range(6):
            t = i / 5.0
            y = 3.85 - 2.6 * t
            zz = az0 + 0.08 * (1 if i % 2 else -1)
            r = 3.4 - taper * y + 0.05
            pts.append((r * math.cos(zz), y, r * math.sin(zz)))
        ptube(ge, pts, [0.15] * 6, 3, phase=az0)
    for k in range(3):
        az = 0.6 + 1.9 * k
        shard(gb, vadd(pol(1.35, az), (0.0, 3.8, 0.0)), dirv(az, math.radians(78.0)), 1.6 + 0.4 * k, 0.28, 4, 0.4, skew=vmul(horiz(az + 1.0), 0.15), phase=az)
    for (az, rr, a, h) in ((1.0, 4.1, 0.8, 1.1), (3.2, 4.3, 0.7, 0.9), (5.0, 4.2, 0.9, 1.3)):
        c = pol(rr, az)
        add_convex(gb, polygon_planes(c[0], c[2], [a, a * 0.9, a * 1.05, a * 0.95, a], rot=az, taper=0.1) + [top_plane(c[0], c[2], h, rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)), ground()])
    return P


def ember_fangs():
    """The ember fangs: two five-sided basalt fangs 7.2 and 5.4 high (battered, the tops chiselled to a point, leaning 3 degrees toward each other) with a
    hand's width between them where an ember core glows (2.9 high, its top broken), a few basalt chips at the foot. Upright, 6 across, 3.5 deep."""
    P = Piece()
    gb = P.geo("Basalt")
    ge = P.geo("Ember")
    f1 = xform(frustum(0.0, 0.0, 1.7, -0.5, 7.2, taper=0.11, rot=0.3, n=5, tops=(1.3, 0.2)), 0.0, (0.0, 0.0, 0.0), rz=-0.05)
    f1 = xform(f1, 0.0, (-1.55, 0.0, 0.0))
    f2 = xform(frustum(0.0, 0.0, 1.45, -0.5, 5.4, taper=0.12, rot=0.9, n=5, tops=(-1.2, 0.3)), 0.0, (0.0, 0.0, 0.0), rz=0.05)
    f2 = xform(f2, 0.0, (1.55, 0.0, 0.4))
    add_convex(gb, f1)
    add_convex(gb, f2)
    add_convex(ge, frustum(0.0, 0.2, 0.62, -0.4, 2.9, taper=0.12, rot=0.35, n=5, tops=(0.5, 0.4)))
    for (x, z, a, h, yaw) in ((-0.2, 1.9, 0.6, 0.9, 0.4), (3.0, -0.9, 0.55, 0.7, 1.0), (-3.3, 0.6, 0.5, 0.6, 0.2)):
        add_convex(gb, xform(polygon_planes(0.0, 0.0, [a, a * 1.1, a * 0.9, a], rot=0.3) + [top_plane(0.0, 0.0, h, 0.7, 0.3), ground()], yaw, (x, 0.0, z)))
    return P


def crag_spires():
    """The jagged crag: five battered five-sided spires of 13.5, 9.6, 8.5, 6.8 and 4.4 on a shared basalt massif 2.4 high, each tapering to a point and
    chopped by an oblique cut at one corner, a sixth small shard at the foot: the mountain's own teeth. Upright, 12 across."""
    P = Piece()
    rng = random.Random(540)
    g = P.geo("Basalt")
    add_convex(g, polygon_planes(0.3, 0.0, [5.9, 6.4, 5.6, 6.1, 5.8, 6.3, 5.5, 6.0, 5.7], rot=0.15, taper=0.42) + [top_plane(0.3, 0.0, 2.4, 0.0, 0.0), ground()])
    spec = [(-4.2, 0.7, 1.9, 8.5), (-1.7, -0.8, 2.3, 13.5), (0.8, 0.9, 1.8, 9.6), (3.0, -0.5, 1.6, 6.8), (4.9, 0.8, 1.35, 4.4), (-3.1, -2.4, 0.95, 3.2)]
    for k, (cx, cz, a, h) in enumerate(spec):
        taper = a / (h * 1.05)
        planes = frustum(cx, cz, a, -0.5, h, taper=taper, rot=0.3 * k + 0.1, n=5, jit=[rng.uniform(0.9, 1.1) for _ in range(5)])
        az = rng.uniform(0.0, TAU)
        n = vnorm((math.cos(az), 0.45, math.sin(az)))
        planes.append((n, vdot(n, (cx + math.cos(az) * a * 0.55, h * 0.6, cz + math.sin(az) * a * 0.55))))
        add_convex(g, planes)
    return P


def shard_scatter():
    """A scatter of obsidian: five standing shards (1.2 to 2.3 high, tilted up to 20 degrees) and ten chips lying flat or tilted on the ground, spread over
    a patch 6 across. No collision."""
    P = Piece()
    rng = random.Random(550)
    go = P.geo("Obsidian")
    for k, (r, az, L, tilt) in enumerate(((0.4, 0.5, 2.3, 8.0), (1.6, 2.1, 1.7, 16.0), (1.4, 3.9, 1.4, 20.0), (2.4, 5.0, 1.2, 14.0), (2.3, 1.1, 1.5, 18.0))):
        shard(go, vadd(pol(r, az), (0.0, -0.1, 0.0)), dirv(az + 0.8, math.radians(90.0 - tilt)), L, 0.24 + 0.05 * L, 4, 0.34, skew=vmul(horiz(az), 0.12), phase=az)
    for k in range(10):
        r = rng.uniform(0.6, 2.9)
        az = rng.uniform(0.0, TAU)
        L, W, H = rng.uniform(0.45, 0.95), rng.uniform(0.3, 0.6), rng.uniform(0.12, 0.28)
        box = [((1, 0, 0), L / 2), ((-1, 0, 0), L / 2), ((0, 0, 1), W / 2), ((0, 0, -1), W / 2), (vnorm((rng.uniform(-0.5, 0.5), 1.0, rng.uniform(-0.5, 0.5))), H), ((0, -1, 0), 1.0)]
        c = pol(r, az)
        add_convex(go, xform(box, rng.uniform(0.0, TAU), (c[0], 0.0, c[2]), rz=rng.uniform(-0.2, 0.2)) + [ground(-0.12 - 0.01 * k)])
    return P


def basalt_pave():
    """BasaltPave, a WALKABLE strip of hexagonal basalt pavers: eighteen flat-topped hexagons (apothem 0.78, a 0.1 gap) in six rows 8.6 long, 4 wide, every
    top at y 0.2 (+- 0.008), sunk to -0.4; the gaps show a slab of ember at y 0.1 under them (a glowing honeycomb). The rows repeat: chain pieces 8.63
    apart along z. Lay it with its origin 0.3 under the wanted top."""
    P = Piece()
    rng = random.Random(560)
    gb = P.geo("Basalt")
    ge = P.geo("Ember")
    a = 0.78
    s = 2 * a + 0.1
    Rz = s * 0.866
    for j in range(6):
        z = (j - 2.5) * Rz
        xs = [-s, 0.0, s] if j % 2 == 0 else [-s / 2, s / 2, 1.5 * s]
        for x in xs:
            top = 0.2 + rng.uniform(-0.008, 0.008)
            slab(gb, hex_ring(x - (0.0 if j % 2 == 0 else s / 4), z, a, 0.0), -0.4, top)
    slab(ge, [(-1.45, -4.0), (1.7, -4.0), (1.7, 4.0), (-1.45, 4.0)], -0.45, 0.10)
    return P


def hex_steps(variant):
    """HexSteps, WALKABLE stepping stones of basalt: big hexagonal slabs (apothem 1.35) laid in a line along z with gaps between them, tops at y 0.20 (flat),
    sunk to -0.4, joined by a buried bar under each gap (one mesh). A: four slabs in a straight way (16 long). B: five smaller slabs (apothem 1.15)
    on a slow curve (15 long). Lay the piece with its origin 0.3 under the wanted top."""
    P = Piece()
    rng = random.Random(570 + variant)
    g = P.geo("Basalt")
    if variant == 0:
        spec = [(0.3, -6.4, 1.35, 0.1), (-0.4, -2.1, 1.38, 0.5), (0.35, 2.1, 1.33, 0.9), (-0.3, 6.3, 1.36, 0.3)]
    else:
        spec = [(-1.8, -7.0, 1.15, 0.2), (-0.7, -3.6, 1.18, 0.6), (0.8, -0.3, 1.14, 0.1), (2.4, 2.9, 1.17, 0.5), (4.0, 6.1, 1.12, 0.8)]
    for i, (cx, cz, a, rot) in enumerate(spec):
        slab(g, hex_ring(cx, cz, a, rot), -0.4, 0.20, bev=0.04)
    for i in range(len(spec) - 1):
        (x0, z0, _, _), (x1, z1, _, _) = spec[i], spec[i + 1]
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
        ln = math.hypot(x1 - x0, z1 - z0) + 1.0
        yaw = math.atan2(x1 - x0, z1 - z0)
        box = [((1, 0, 0), 0.18), ((-1, 0, 0), 0.18), ((0, 1, 0), -0.30 + 0.01 * i), ((0, -1, 0), 0.5 + 0.01 * i), ((0, 0, 1), ln / 2), ((0, 0, -1), ln / 2)]
        add_convex(g, xform(box, yaw, (mx, 0.0, mz)))
    return P


# ======================================================================================================================
# PLANTS
# ======================================================================================================================
def blade(g, base, d, L, w, th, face=UP, bend=None, rings=1):
    """A closed pointed leaf of V section: width w, ridge height th toward `face`, length L along d. rings = 1: one segment (4 triangles); rings = 2: a
    second ring at 55 percent of the length, narrower, and the tip pushed by `bend` (10 triangles): a straight, stiff, slightly hooked blade."""
    d = vnorm(d)
    sv = vcross(d, face)
    if vlen(sv) < 1e-5:
        sv = vcross(d, (1.0, 0.0, 0.0))
    sv = vnorm(sv)
    f2 = vnorm(vcross(sv, d))

    def ring(c, k):
        return [g.vert(vadd(c, vmul(sv, -w * k / 2))), g.vert(vadd(c, vmul(sv, w * k / 2))), g.vert(vadd(c, vmul(f2, th * k)))]
    start = len(g.f)
    r0 = ring(base, 1.0)
    tip = vadd(base, vmul(d, L))
    if bend:
        tip = vadd(tip, bend)
    a = None
    if rings == 2:
        mid = vadd(vadd(base, vmul(d, L * 0.55)), vmul(bend, 0.3) if bend else (0.0, 0.0, 0.0))
        r1 = ring(mid, 0.6)
        for k in range(3):
            j = (k + 1) % 3
            g.face(r0[k], r1[k], r1[j], r0[j])
        top = r1
    else:
        top = r0
    a = g.vert(tip)
    for k in range(3):
        j = (k + 1) % 3
        g.face(top[k], a, top[j])
    _cap(g, r0, False)
    K._orient_solid(g, start)
    return tip


def ash_grass(variant):
    """Ash grass, bone-pale and stiff. A: a patch about 5 x 5, eight tufts of six straight blades standing up and a little out (1.6 to 2.8 high, the
    tips hooked), nothing combed. B: one tall sheaf 3 x 3 of fifteen blades fanning up to 4.6."""
    P = Piece()
    rng = random.Random(600 + variant)
    g = P.geo("AshBlade")
    if variant == 0:
        spots = [(-1.8, -1.5), (0.4, -1.9), (1.9, -0.8), (-1.9, 0.7), (0.1, 0.2), (-0.6, 1.9), (1.7, 1.7), (-2.4, -0.4)]
        for (x, z) in spots:
            x += rng.uniform(-0.15, 0.15)
            z += rng.uniform(-0.15, 0.15)
            for i in range(6):
                az = rng.uniform(0.0, TAU)
                L = rng.uniform(1.6, 2.8)
                d = dirv(az, math.radians(90.0 - rng.uniform(5.0, 24.0)))
                blade(g, (x + rng.uniform(-0.12, 0.12), -0.1, z + rng.uniform(-0.12, 0.12)), d, L, 0.34, 0.1, face=horiz(az), bend=vmul(horiz(az), L * 0.12) if i % 3 == 0 else None,
                      rings=2 if i % 3 == 0 else 1)
    else:
        for i in range(15):
            az = TAU * i / 15 + rng.uniform(-0.2, 0.2)
            L = rng.uniform(3.0, 4.6)
            r0 = rng.uniform(0.05, 0.45)
            blade(g, (r0 * math.cos(az), -0.1, r0 * math.sin(az)), dirv(az, math.radians(90.0 - rng.uniform(4.0, 22.0))), L, 0.4, 0.12, face=horiz(az),
                  bend=vmul(horiz(az), L * 0.1), rings=2)
    return P


def spider_lily(variant):
    """The crimson spider lily: slender dark stems with no leaves, each topped by a burst of long thin crimson filaments that rise, arch out and hook down.
    A: three flowers 2.6 to 3.4 tall, seven filaments each. B: a drift of seven short flowers (1.3 to 2.0), five filaments each."""
    P = Piece()
    rng = random.Random(610 + variant)
    gs = P.geo("DeepCrimson")
    gf = P.geo("Crimson")
    if variant == 0:
        spots = [(-0.7, -0.3, 2.9), (0.6, 0.5, 3.4), (0.3, -0.9, 2.6)]
        npet, sc = 7, 1.0
    else:
        spots = [(-1.3, -0.4, 1.5), (-0.5, 0.6, 1.9), (0.4, -0.5, 1.3), (1.2, 0.3, 1.7), (-0.2, -1.1, 1.4), (0.9, 1.1, 2.0), (-1.5, 1.0, 1.3)]
        npet, sc = 5, 0.62
    for (x, z, h) in spots:
        dx, dz = rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)
        top = (x + dx, h, z + dz)
        ptube(gs, [(x, -0.2, z), (x + dx * 0.5, h * 0.55, z + dz * 0.5), top], [0.07 * (0.6 + 0.4 * sc), 0.06 * (0.6 + 0.4 * sc), 0.05], 3, phase=x)
        for k in range(npet):
            az = TAU * k / npet + rng.uniform(-0.2, 0.2)
            p0 = vadd(top, (0.0, 0.0, 0.0))
            p1 = vadd(p0, vmul(dirv(az, math.radians(50.0)), 0.75 * sc))
            p2 = vadd(p1, vmul(dirv(az, math.radians(-30.0)), 0.55 * sc))
            if variant == 0:
                ptube(gf, [p0, p1, p2], [0.05, 0.04, 0.03], 3, phase=az)
            else:
                ptube(gf, [p0, vadd(p0, vmul(dirv(az, math.radians(38.0)), 0.8 * sc))], [0.05, 0.03], 3, phase=az)
    return P


def thornbrake():
    """The thornbrake: a low tangle 3 across and 1.6 high, six stems of dark crimson that rise from one root and fold in sharp zigzags, each set with
    thorns of the same dark crimson (about 20 in all). One box collider."""
    P = Piece()
    rng = random.Random(620)
    gs = P.geo("DeepCrimson")
    gt = gs
    for k in range(6):
        az = TAU * k / 6 + rng.uniform(-0.25, 0.25)
        p0 = (0.0, -0.1, 0.0)
        p1 = vadd(p0, vmul(dirv(az, math.radians(52.0)), 1.0))
        p2 = vadd(p1, vmul(dirv(az + 0.55 * (1 if k % 2 else -1), math.radians(14.0)), 0.9))
        p3 = vadd(p2, vmul(dirv(az - 0.35 * (1 if k % 2 else -1), math.radians(46.0)), 0.8))
        ptube(gs, [p0, p1, p2, p3], [0.15, 0.12, 0.09, 0.06], 3, phase=az)
        for (pa, pb, t) in ((p0, p1, 0.55), (p1, p2, 0.5), (p2, p3, 0.6)):
            c = vadd(pa, vmul(vsub(pb, pa), t))
            for sgn in (-1, 1):
                if sgn == 1 and t > 0.55 and k % 2:
                    continue
                spike(gt, c, vnorm(vadd(vmul(vcross(vsub(pb, pa), UP), 0.9 * sgn), (0.0, 0.7, 0.0))), 0.5, 0.075, 3)
    return P


def thorn_climber():
    """The thorn climber, a vine for a wall or post: a zigzag stem of dark crimson 6 high in one plane (x, y) with three tendrils and six dark leaves,
    thorns of the same dark crimson on both faces. 5 wide, 1.4 deep: stand it against a wall."""
    P = Piece()
    rng = random.Random(630)
    gs = P.geo("DeepCrimson")
    gt = gs
    knots = [(0.0, -0.3, 0.0), (0.45, 1.4, 0.0), (-0.4, 3.0, 0.0), (0.4, 4.6, 0.0), (-0.1, 6.0, 0.0)]
    ptube(gs, knots, [0.15, 0.13, 0.11, 0.09, 0.06], 3, phase=0.4)
    for i in range(len(knots) - 1):
        a, b = knots[i], knots[i + 1]
        for t, zs in ((0.3, 1.0), (0.7, -1.0)):
            c = vadd(a, vmul(vsub(b, a), t))
            spike(gt, c, vnorm((rng.uniform(-0.6, 0.6), 0.25, 1.0 * zs)), 0.6, 0.08, 3)
        c = vadd(a, vmul(vsub(b, a), 0.5))
        spike(gt, c, vnorm((1.0 if i % 2 == 0 else -1.0, 0.3, 0.0)), 0.5, 0.08, 3)
    for (ki, sx, L) in ((1, 1, 1.9), (2, -1, 2.0), (3, 1, 1.6)):
        p0 = knots[ki]
        p1 = vadd(p0, (sx * 1.0, 0.6, 0.15))
        p2 = vadd(p1, (sx * 0.7, 0.9, 0.0))
        ptube(gs, [p0, p1, p2], [0.09, 0.07, 0.05], 3, phase=0.4)
        spike(gt, p2, vnorm((sx * 0.5, 1.0, 0.0)), 0.55, 0.07, 3)
        blade(gs, vadd(p1, (0.0, 0.05, 0.0)), vnorm((sx * 0.3, 1.0, 0.8)), 1.0, 0.36, 0.1, face=(0.0, 0.0, 1.0))
        blade(gs, vadd(p1, (0.0, 0.05, 0.0)), vnorm((sx * 0.3, 1.0, -0.8)), 0.9, 0.34, 0.1, face=(0.0, 0.0, -1.0))
    return P


def spearleaf():
    """The spearleaf, an iron agave: thirteen stiff dark-iron leaves 2.4 to 3.6 long standing up from one root at 25 to 55 degrees from the vertical, a
    dark spike in the heart. 4 across, 3.4 high."""
    P = Piece()
    rng = random.Random(640)
    gl = P.geo("SpearBlade")
    gt = gl
    n = 13
    for k in range(n):
        az = TAU * k / n + rng.uniform(-0.12, 0.12)
        tilt = 25.0 + 30.0 * (k % 3) / 2.0 + rng.uniform(-4.0, 4.0)
        L = 2.4 + 1.2 * (1.0 - (k % 3) / 2.0) * rng.uniform(0.85, 1.0)
        blade(gl, (0.0, -0.1, 0.0), dirv(az, math.radians(90.0 - tilt)), L, 0.62, 0.2, face=horiz(az), bend=vmul(horiz(az), L * 0.1), rings=2)
    spike(gt, (0.0, 0.0, 0.0), UP, 2.0, 0.17, 3)
    return P


def thornrose():
    """The thornrose: three stalks (1.2 to 2.2 high) of dark crimson with thorns, each carrying a faceted bloom of eleven pointed petals (six
    outer, tilted out, five inner, standing) round a bud, all one dark crimson."""
    P = Piece()
    rng = random.Random(650)
    gs = P.geo("DeepCrimson")
    gt = gs
    for (x, z, h) in ((-0.6, 0.0, 1.7), (0.6, 0.3, 2.2), (0.2, -0.7, 1.2)):
        top = (x + rng.uniform(-0.08, 0.08), h, z)
        mid = (x + (top[0] - x) * 0.4 + 0.12, h * 0.5, z + 0.08)
        ptube(gs, [(x, -0.15, z), mid, top], [0.08, 0.065, 0.055], 3, phase=x)
        for (t, sg) in ((0.25, 1), (0.55, -1), (0.8, 1)):
            c = vadd((x, -0.15, z), vmul(vsub(top, (x, -0.15, z)), t))
            spike(gt, c, vnorm((0.8 * sg, 0.3, rng.uniform(-0.5, 0.5))), 0.42, 0.06, 3)
        for k in range(6):
            az = TAU * k / 6 + rng.uniform(-0.1, 0.1) + x
            blade(gs, vadd(top, (0.0, -0.05, 0.0)), dirv(az, math.radians(40.0)), 1.05, 0.62, 0.16, face=horiz(az), rings=1)
        for k in range(5):
            az = TAU * (k + 0.5) / 5 + x
            blade(gs, vadd(top, (0.0, 0.0, 0.0)), dirv(az, math.radians(72.0)), 0.85, 0.5, 0.14, face=horiz(az), rings=1)
        spike(gt, vadd(top, (0.0, 0.0, 0.0)), UP, 0.65, 0.12, 4)
    return P


def cinderbush():
    """The cinderbush: a low shrub of sixteen straight black sticks (1.4 to 2.6 long, 18 to 62 degrees from the vertical) bristling from one core, each
    tipped with an ember. 3 across, 2.4 high."""
    P = Piece()
    rng = random.Random(660)
    gc = P.geo("Cinder")
    ge = P.geo("Ember")
    for k in range(16):
        az = TAU * k / 16 + rng.uniform(-0.2, 0.2)
        tilt = rng.uniform(18.0, 62.0)
        L = rng.uniform(1.4, 2.6)
        thorn(gc, ge, (rng.uniform(-0.12, 0.12), -0.05, rng.uniform(-0.12, 0.12)), dirv(az, math.radians(90.0 - tilt)), L, 0.1, 0.86, 3, phase=az)
    return P


def ashcap():
    """Ashcap, a clump of pale fungus: five angular mushrooms (a five-sided stalk, a six-sided flat cone for a cap 0.7 to 1.3 across) and three small ones,
    all ash-grey. 3 across, 1.5 high."""
    P = Piece()
    rng = random.Random(670)
    g = P.geo("AshCap")
    spec = [(0.0, 0.0, 1.5, 1.3), (1.0, 0.6, 1.0, 0.95), (-0.9, 0.7, 0.9, 0.85), (-0.5, -0.9, 1.2, 1.0), (0.9, -0.8, 0.7, 0.75), (1.7, -0.1, 0.45, 0.45), (-1.6, -0.1, 0.5, 0.5), (0.3, 1.5, 0.4, 0.42)]
    for (x, z, h, R) in spec:
        ptube(g, [(x, -0.15, z), (x + rng.uniform(-0.05, 0.05), h * 0.5, z), (x, h, z)], [R * 0.2, R * 0.16, R * 0.17], 5, phase=x)
        spike(g, (x, h - 0.05, z), UP, R * 0.42, R, 6, phase=0.2 + z)
    return P


def ember_crust():
    """An ember crust, a ground patch: a 12-sided disc 6 across of ten cracked black plates (tops at 0.12, gaps 0.12 wide) over a slab of ember at 0.05,
    so the cracks between the plates glow. No collision; lay it on the ground (y 0.02)."""
    P = Piece()
    rng = random.Random(680)
    gc = P.geo("Cinder")
    ge = P.geo("Ember")
    R = 3.0
    seeds = [(0.1, 0.0)]
    tries = 0
    while len(seeds) < 10 and tries < 400:
        tries += 1
        r = R * math.sqrt(rng.uniform(0.0, 1.0)) * 0.92
        a = rng.uniform(0.0, TAU)
        c = (r * math.cos(a), r * math.sin(a))
        if all(math.hypot(c[0] - q[0], c[1] - q[1]) > 1.35 for q in seeds):
            seeds.append(c)
    disc = [(R * math.cos(TAU * (k + 0.5) / 12), 0.0, R * math.sin(TAU * (k + 0.5) / 12)) for k in range(12)]
    gap = 0.06
    for i, si in enumerate(seeds):
        poly = list(disc)
        for j, sj in enumerate(seeds):
            if i == j:
                continue
            nx, nz = sj[0] - si[0], sj[1] - si[1]
            ln = math.hypot(nx, nz)
            nx, nz = nx / ln, nz / ln
            e = nx * (si[0] + sj[0]) / 2 + nz * (si[1] + sj[1]) / 2 - gap
            poly = _clip(poly, (nx, 0.0, nz), e)
            if len(poly) < 3:
                break
        if len(poly) < 3:
            continue
        top = 0.12 + rng.uniform(-0.01, 0.01)
        slab(gc, [(p[0], p[2]) for p in poly], -0.1, top)
    slab(ge, [(p[0] * 0.97, p[2] * 0.97) for p in disc], -0.12, 0.05)
    return P


def ash_drift():
    """An ash drift, a ground patch: three low faceted heaps of grey ash (2.4, 1.6 and 1.4 across at the foot, 0.45, 0.32 and 0.28 high). No collision."""
    P = Piece()
    rng = random.Random(690)
    g = P.geo("AshPile")
    for (x, z, a, h) in ((0.0, 0.0, 1.5, 0.45), (2.0, 0.9, 1.0, 0.32), (-1.6, 0.8, 0.9, 0.28)):
        taper = (a - a * 0.4) / h
        add_convex(g, polygon_planes(x, z, [a * rng.uniform(0.9, 1.1) for _ in range(7)], rot=rng.uniform(0.0, 1.0), taper=taper) + [top_plane(x, z, h, rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2)), ground(-0.1)])
    return P


# ----------------------------------------------------------------------------------------------------------------------
# shells, z-fighting (plain-Python mirror of the asset QA's test) and the colliders
# ----------------------------------------------------------------------------------------------------------------------
def _shells(g):
    """Connected shells of a Geo (by shared vertex index): returns (shell id per vertex, number of shells)."""
    parent = list(range(len(g.v)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for f in g.f:
        r = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != r:
                parent[ri] = r
    ids = {}
    out = []
    for i in range(len(g.v)):
        r = find(i)
        ids.setdefault(r, len(ids))
        out.append(ids[r])
    return out, len(ids)


def zfight_pairs(g, eps=0.001):
    """The shell pairs that the asset QA would flag as z-fighting: triangles of two shells that face the same way (normals within 2.5 degrees), lie within
    eps of each other's plane and overlap (four sample points per triangle)."""
    shell, _ = _shells(g)
    tris = []
    for f in g.f:
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
    data = []
    grid = {}
    cell = 0.6
    for ti, (a, b, c) in enumerate(tris):
        A, B_, C = g.v[a], g.v[b], g.v[c]
        n = vcross(vsub(B_, A), vsub(C, A))
        ln = vlen(n)
        if ln < 1e-9:
            data.append(None)
            continue
        n = vmul(n, 1.0 / ln)
        data.append((A, B_, C, n))
        lo = [min(A[i], B_[i], C[i]) for i in range(3)]
        hi = [max(A[i], B_[i], C[i]) for i in range(3)]
        for ix in range(int(lo[0] // cell), int(hi[0] // cell) + 1):
            for iy in range(int(lo[1] // cell), int(hi[1] // cell) + 1):
                for iz in range(int(lo[2] // cell), int(hi[2] // cell) + 1):
                    grid.setdefault((ix, iy, iz), []).append(ti)
    pairs = set()
    for ti, d in enumerate(data):
        if d is None:
            continue
        A, B_, C, n = d
        cen = tuple((A[i] + B_[i] + C[i]) / 3 for i in range(3))
        for p in (cen, vadd(cen, vmul(vsub(A, cen), 0.6)), vadd(cen, vmul(vsub(B_, cen), 0.6)), vadd(cen, vmul(vsub(C, cen), 0.6))):
            key = (int(p[0] // cell), int(p[1] // cell), int(p[2] // cell))
            for tj in grid.get(key, ()):
                if tj == ti or data[tj] is None:
                    continue
                if shell[tris[ti][0]] == shell[tris[tj][0]]:
                    continue
                A2, B2, C2, n2 = data[tj]
                if vdot(n, n2) < 0.999:
                    continue
                dist = vdot(n2, vsub(p, A2))
                if abs(dist) > eps:
                    continue
                q = vsub(p, vmul(n2, dist))
                v0, v1, v2 = vsub(C2, A2), vsub(B2, A2), vsub(q, A2)
                d00, d01, d02, d11, d12 = vdot(v0, v0), vdot(v0, v1), vdot(v0, v2), vdot(v1, v1), vdot(v1, v2)
                den = d00 * d11 - d01 * d01
                if abs(den) < 1e-14:
                    continue
                u = (d11 * d02 - d01 * d12) / den
                v = (d00 * d12 - d01 * d02) / den
                if u >= -1e-6 and v >= -1e-6 and u + v <= 1 + 1e-6:
                    pairs.add((shell[tris[ti][0]], shell[tris[tj][0]]))
    return pairs


def decollide(g, tries=8):
    """Rolls one shell of every z-fighting pair a few degrees about its own long axis until the QA's test finds no pair (blades and thorns from one root can
    land on near-parallel faces by chance). Returns the number of shells turned."""
    turned = 0
    for it in range(tries):
        pairs = zfight_pairs(g)
        if not pairs:
            break
        shell, n = _shells(g)
        members = {}
        for i, sh in enumerate(shell):
            members.setdefault(sh, []).append(i)
        done = set()
        for a, b in sorted(pairs):
            sh = max(a, b) if it % 2 == 0 else min(a, b)
            if sh in done:
                continue
            done.add(sh)
            vs = members[sh]
            p0 = g.v[vs[0]]
            far = g.v[vs[-1]]
            axis = vnorm(vsub(far, p0)) if vlen(vsub(far, p0)) > 1e-6 else (0.0, 1.0, 0.0)
            ang = (0.07 + 0.03 * it) * (1 if (sh + it) % 2 else -1)
            for i in vs:
                g.v[i] = vadd(p0, _rot(vsub(g.v[i], p0), axis, ang))
            turned += 1
    return turned


def _shell_samples(g, which, shell_ids, per_edge=6):
    """Points sampled over the triangles of the shells in `which` (a barycentric grid), to measure a shell inside a height band."""
    pts = []
    for f in g.f:
        if shell_ids[f[0]] not in which:
            continue
        for k in range(1, len(f) - 1):
            a, b, c = g.v[f[0]], g.v[f[k]], g.v[f[k + 1]]
            n = per_edge
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    w = 1 - u - v
                    pts.append(tuple(a[q] * w + b[q] * u + c[q] * v for q in range(3)))
    return pts


def _band_boxes(pts, axis, lo, hi, step, shrink, min_size=0.3, ymin=0.0):
    """Cuts the points into bands along `axis` (0 x, 1 y, 2 z) and returns one box per non-empty band, shrunk across by the fraction `shrink` of its half sizes
    (never in height, so bands leave no gaps)."""
    out = []
    a = lo
    while a < hi - 1e-6:
        b = min(hi, a + step)
        sel = [p for p in pts if a <= p[axis] <= b]
        if len(sel) >= 3:
            lo3 = [min(p[i] for p in sel) for i in range(3)]
            hi3 = [max(p[i] for p in sel) for i in range(3)]
            c = [(lo3[i] + hi3[i]) / 2 for i in range(3)]
            h = [(hi3[i] - lo3[i]) / 2 * (1 - (0.0 if i == 1 else shrink)) for i in range(3)]
            bx = {"x0": round(c[0] - h[0], 2), "x1": round(c[0] + h[0], 2), "y0": round(max(ymin, c[1] - h[1]), 2), "y1": round(c[1] + h[1], 2),
                  "z0": round(c[2] - h[2], 2), "z1": round(c[2] + h[2], 2)}
            if bx["x1"] - bx["x0"] > min_size and bx["y1"] - bx["y0"] > min_size and bx["z1"] - bx["z0"] > min_size:
                out.append(bx)
        a = b
    return out


def _merge_boxes(boxes, tol=0.0):
    """Drops a box that lies wholly inside another."""
    keep = []
    for i, b in enumerate(boxes):
        inside = False
        for j, c in enumerate(boxes):
            if i != j and c["x0"] <= b["x0"] + tol and c["x1"] >= b["x1"] - tol and c["y0"] <= b["y0"] + tol and c["y1"] >= b["y1"] - tol and \
                    c["z0"] <= b["z0"] + tol and c["z1"] >= b["z1"] - tol and (c != b or j < i):
                inside = True
                break
        if not inside:
            keep.append(b)
    return keep


def trunk_boxes(piece, suffix, ymax, step=2.2, shrink=0.16, lo=None, hi=None, shell_no=None):
    """Boxes up the first shell of `suffix` (the trunk is always built first; shell_no names another shell): bands along y from the ground to ymax."""
    g = piece.g[suffix]
    shell, _ = _shells(g)
    pts = _shell_samples(g, {shell[0]} if shell_no is None else {shell_no}, shell)
    pts = [p for p in pts if p[1] <= ymax + 3.0]
    return _band_boxes(pts, 1, -0.4 if lo is None else lo, ymax if hi is None else hi, step, shrink, ymin=0.0)


def body_boxes(piece, suffixes=("Basalt",), step=2.6, shrink=0.12, min_h=0.9, tall=3.5, shells=None):
    """One set of boxes per stone body (each convex body is its own shell): bodies under min_h high are scenery and get none; a body taller than `tall` is
    cut into bands so a tapering spire is not boxed by its whole bounding box. shells: restrict to these shell numbers."""
    out = []
    for sfx in suffixes:
        g = piece.g.get(sfx)
        if not g:
            continue
        shell, n = _shells(g)
        for sh in range(n):
            if shells is not None and sh not in shells:
                continue
            pts = _shell_samples(g, {sh}, shell, per_edge=3)
            if not pts:
                continue
            top = max(p[1] for p in pts)
            if top < min_h:
                continue
            if top - min(p[1] for p in pts) > tall:
                out += _band_boxes(pts, 1, -0.4, top, step, shrink, ymin=0.0)
            else:
                out += _band_boxes(pts, 1, -0.6, top + 0.01, 100.0, shrink, ymin=0.0)
    return _merge_boxes(out)


# ======================================================================================================================
# registry, collision, meta
# ======================================================================================================================
TREES = {"AshthornA1": lambda: ashthorn(0), "AshthornA2": lambda: ashthorn(1), "IronpineB1": lambda: ironpine(0), "IronpineB2": lambda: ironpine(1),
         "ShardtreeC1": lambda: shardtree(0), "ShardtreeC2": lambda: shardtree(1), "CinderstumpD1": lambda: cinderstump(0), "CinderstumpD2": lambda: cinderstump(1),
         "GiantBlackthorn": giant_blackthorn}
ROCKS = {"BasaltColumns": basalt_columns, "BasaltPalisade": basalt_palisade, "ObsidianShards": obsidian_shards, "SplitObelisk": split_obelisk, "EmberCone": ember_cone,
         "EmberFangs": ember_fangs, "CragSpires": crag_spires, "ShardScatter": shard_scatter, "BasaltPave": basalt_pave, "HexStepsA": lambda: hex_steps(0),
         "HexStepsB": lambda: hex_steps(1)}
PLANTS = {"AshGrassA": lambda: ash_grass(0), "AshGrassB": lambda: ash_grass(1), "SpiderLilyA": lambda: spider_lily(0), "SpiderLilyB": lambda: spider_lily(1),
          "Thornbrake": thornbrake, "ThornClimber": thorn_climber, "Spearleaf": spearleaf, "Thornrose": thornrose, "Cinderbush": cinderbush, "Ashcap": ashcap,
          "EmberCrust": ember_crust, "AshDrift": ash_drift}
FAMILIES = [("Trees", TREES), ("Rocks", ROCKS), ("Plants", PLANTS)]
# where to use each piece, and the keep-out radius (studs) the placer should leave round it
USE = {
    "AshthornA1": ("the tiered candelabra: a dead black tree 18 high for court edges, stair sides and the lower ward, singly or in a loose line; the arms reach 5 studs each way, keep 4 studs clear of other trees", 4.0),
    "AshthornA2": ("the crowned thorn: a short grey bole with a fan of spears, 16 high and 8 across at the crown: gate sides, ledges and path forks; keep 4 studs clear", 4.0),
    "IronpineB1": ("the twisted iron pine: a mast 21 high with spike stars, 12 across: along walls and stairs and on terraces; keep 5 studs clear of other trees", 5.0),
    "IronpineB2": ("the bolt pine: a trunk that kinks like lightning, 17 high and 13 across: cliff edges, ledge corners and bridge heads, standing alone; keep 5 studs clear", 5.0),
    "ShardtreeC1": ("the obsidian tree: black glass branches, 15 high, 8 across: chasm rims, the fissure's lip and the keep's terrace; keep 4 studs clear", 4.0),
    "ShardtreeC2": ("the obsidian sapling: 8.5 high, 4 across: beside C1, on rock feet and along rims; keep 2 studs clear", 2.0),
    "CinderstumpD1": ("the hollow stump: a ring of burnt staves 7.6 high round glowing embers (the ring is hollow, a player can not enter it: the staves are boxed), 10 across: court corners and the training ground's edge; keep 3 studs clear; the ember bed glows by night", 3.0),
    "CinderstumpD2": ("the three-claw stump: pillars of 11, 8.2 and 5.5 with an ember core between them, 8.5 across: gate flanks and wall ends; keep 3 studs clear", 3.0),
    "GiantBlackthorn": ("THE landmark: one only: a 47 high dead thorn tree held by six stone talons (the mound and talons are part of the piece: set it on flat ground, 22 across), at the keep's court or the great stair's head; keep 14 studs clear all round", 14.0),
    "BasaltColumns": ("a causeway of hexagonal basalt columns up to 9.3 high, 9 across: against a wall or at a stair's side, the lower ward's edge; keep 2 studs clear", 2.0),
    "BasaltPalisade": ("a row of nine columns 18 long, 2.8 to 9.3 high: the back of a court, a path's edge or a rim, a natural battlement; keep 2 studs clear, yaw so its length runs along the edge", 2.0),
    "ObsidianShards": ("a cluster of nine black glass shards, the tallest 9.5, on a low basalt mound, 7 across: fissure lips, court centres and the arena's rim; keep 3 studs clear; the collision is the mound and the central core only", 3.0),
    "SplitObelisk": ("a broken obelisk 11.9 high with ember in its joints and a fallen piece (the fallen piece lies to +X of the shaft: yaw it away from a path): court markers and the gate's approach; keep 3 studs clear", 3.0),
    "EmberCone": ("an ember cone 6 high with a glowing crater and four glowing cracks, 10 across with its blocks: beside the fissure, on terraces and as a brazier-like landmark; keep 3 studs clear; the crater glows", 3.0),
    "EmberFangs": ("two basalt fangs 8.4 and 5.4 high with an ember core between them, 8 across: gate flanks, stair sides and the bridge heads; keep 2 studs clear", 2.0),
    "CragSpires": ("a crag of five spires up to 13.5 high on a massif 2.4 high, 13 across: backdrops, the edge of the upper ward and the cliff sides; keep 3 studs clear", 3.0),
    "ShardScatter": ("a scatter of obsidian shards (up to 2.3 high) and chips over a patch 6 across, no collision: rock feet, the fissure's edge and the training ground", 0.0),
    "BasaltPave": ("WALKABLE: a strip of hexagonal basalt pavers 4 wide and 9 long along z with a glowing honeycomb of ember in the gaps, every top at y 0.20: lay the piece with its origin 0.3 under the wanted top and no collision part (the mesh itself walks); chain end to end 8.63 apart along z", 0.0),
    "HexStepsA": ("WALKABLE: four hexagonal basalt stepping slabs along z, 4.2 apart (a straight way, 16 long); every top at y 0.20: lay the piece with its origin 0.3 under the wanted top, no collision part; the slabs are tied by buried bars", 0.0),
    "HexStepsB": ("WALKABLE: five smaller hexagonal slabs on a slow curve along z (15 long); tops at y 0.20; as HexStepsA", 0.0),
    "AshGrassA": ("a patch of bone-pale ash grass about 6 x 5 (stiff upright blades, nothing combed): open ground and slopes, no collision", 0.0),
    "AshGrassB": ("a tall tuft of ash grass 3.4 x 3.2 and 4.3 high: beside rocks, walls and stair feet, no collision", 0.0),
    "SpiderLilyA": ("three crimson spider lilies 2.6 to 4 high: the territory's flower; groups at gates, stair feet and the keep's court, no collision", 0.0),
    "SpiderLilyB": ("a drift of seven short crimson spider lilies (1.3 to 2.3 high), 3.6 across: along path edges and under trees, no collision", 0.0),
    "Thornbrake": ("a low thorn tangle 3.8 across and 1.7 high, crimson thorns: on slopes and under walls; keep 1 stud clear; one box collider", 1.0),
    "ThornClimber": ("a thorn vine for a wall, post or pillar, 5 wide, 7 high and 1.4 deep (z): stand it against a wall with its back to -Z... either face has thorns; no collision", 0.0),
    "Spearleaf": ("a spearleaf (dark iron agave) 4 across and 3.4 high: path sides, rock feet and the court's corners, no collision", 0.0),
    "Thornrose": ("three thornroses, deep crimson blooms on thorny stalks, 1.2 to 3 high: sparse accents among ash grass, no collision", 0.0),
    "Cinderbush": ("a cinderbush, black sticks tipped with embers, 3 across and 2.2 high: scree, rim edges and the fissure's side, no collision", 0.0),
    "Ashcap": ("a clump of pale angular fungus 4 across and 2 high: shaded corners and wall feet, no collision", 0.0),
    "EmberCrust": ("a ground patch 6 across: black cracked plates over glowing ember: lay on the ground at y 0.02 near the fissure and the arena, no collision", 0.0),
    "AshDrift": ("a ground patch of grey ash heaps 6 x 4, 0.5 high: wall feet and stair sides, no collision", 0.0),
}

# how many of each the placer is planned to use (the mix: 16 trees with the one giant, 24 rocks and path pieces, 60 plants)
PLAN = {"GiantBlackthorn": 1, "AshthornA1": 2, "AshthornA2": 2, "IronpineB1": 2, "IronpineB2": 1, "ShardtreeC1": 2, "ShardtreeC2": 2, "CinderstumpD1": 2, "CinderstumpD2": 2,
        "BasaltColumns": 2, "BasaltPalisade": 2, "ObsidianShards": 3, "SplitObelisk": 2, "EmberCone": 2, "EmberFangs": 2, "CragSpires": 2, "ShardScatter": 3, "BasaltPave": 2,
        "HexStepsA": 2, "HexStepsB": 2,
        "AshGrassA": 9, "AshGrassB": 7, "SpiderLilyA": 5, "SpiderLilyB": 5, "Thornbrake": 4, "ThornClimber": 4, "Spearleaf": 5, "Thornrose": 4, "Cinderbush": 5, "Ashcap": 3,
        "EmberCrust": 4, "AshDrift": 5}


def use_for(name):
    base = name.split("_", 2)[2]
    return USE.get(base, ("", 0.0))


# ----------------------------------------------------------------------------------------------------------------------
# colliders: simple invisible boxes in the piece frame (a little smaller than what is seen); crowns, plants and walkable paths have none
# ----------------------------------------------------------------------------------------------------------------------
def collision_for(name, piece):
    base = name.split("_", 2)[2]
    if base == "AshthornA1":
        return trunk_boxes(piece, "Char", 8.0, step=2.8, shrink=0.2)
    if base == "AshthornA2":
        return trunk_boxes(piece, "Char", 6.6, step=3.3, shrink=0.15)
    if base == "IronpineB1":
        return trunk_boxes(piece, "IronBark", 9.0, step=3.0, shrink=0.2)
    if base == "IronpineB2":
        return trunk_boxes(piece, "IronBark", 7.0, step=2.5, shrink=0.2)
    if base == "ShardtreeC1":
        return trunk_boxes(piece, "Obsidian", 7.5, step=3.0, shrink=0.18)
    if base == "ShardtreeC2":
        return trunk_boxes(piece, "Obsidian", 3.8, step=3.5, shrink=0.18)
    if base == "CinderstumpD1":
        return body_boxes(piece, ("Char",), min_h=1.4, tall=3.5, shells=set(range(6)))
    if base == "CinderstumpD2":
        return body_boxes(piece, ("Char",), min_h=1.4, tall=3.5, step=2.8, shells=set(range(3)))
    if base == "GiantBlackthorn":
        return trunk_boxes(piece, "Char", 22.0, step=3.6, shrink=0.14) + body_boxes(piece, ("Char",), min_h=1.4, tall=3.5, shells=set(range(1, 8)))
    if base in ("BasaltColumns", "BasaltPalisade", "EmberFangs"):
        return body_boxes(piece, ("Basalt",), min_h=1.4, tall=14.0)
    if base in ("CragSpires", "EmberCone"):
        return body_boxes(piece, ("Basalt",), min_h=1.4, tall=3.5, step=3.2)
    if base == "SplitObelisk":
        return body_boxes(piece, ("Basalt",), min_h=1.4, tall=3.5, step=3.0, shells=set(range(4)))
    if base == "ObsidianShards":
        return body_boxes(piece, ("Obsidian",), min_h=0.9, tall=3.5, shells={0}) + [{"x0": -1.3, "x1": 1.3, "y0": 0.0, "y1": 6.0, "z0": -1.3, "z1": 1.3}]
    if base == "Thornbrake":
        return [{"x0": -1.2, "x1": 1.2, "y0": 0.0, "y1": 1.0, "z0": -1.0, "z1": 1.2}]
    return []


def meta_for(name, piece):
    fam, base = name.split("_", 2)[1], name.split("_", 2)[2]
    lo, hi = piece.bounds()
    vs = [v for g in piece.g.values() for v in g.v]
    foot = [v for v in vs if v[1] < 1.2]
    use, keep = use_for(name)
    variant = base[-2:] if base[-2:] in ("A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2") else (base[-1] if base[-1] in "AB" and fam != "Trees" else "")
    walk = base.startswith(("BasaltPave", "HexSteps"))
    d = {"family": fam, "piece": base, "variant": variant, "tris": piece.tris(), "materials": {k: v for k, v in sorted(piece.stats().items())},
         "bounds_min": [round(c, 2) for c in lo], "bounds_max": [round(c, 2) for c in hi],
         "radius": round(max(math.hypot(v[0], v[2]) for v in foot), 2) if foot else 0.0, "crown_radius": round(max(math.hypot(v[0], v[2]) for v in vs), 2),
         "height": round(hi[1], 2), "collision": collision_for(name, piece), "use": use, "keepout": keep, "walkable": walk,
         "leans": "none (the piece stands upright on a vertical axis: place it at any yaw)", "plan_count": PLAN.get(base, 0)}
    if walk:
        tops = [v[1] for g in piece.g.values() for v in g.v if v[1] > 0.0]
        d["walk_top_min"] = round(min(tops), 3) if tops else 0.0
        d["walk_top_max"] = round(max(tops), 3) if tops else 0.0
    return d


def build_all(names=None):
    pieces = {}
    for fam, table in FAMILIES:
        for name, fn in table.items():
            full = "Nightfall_%s_%s" % (fam, name)
            if names and full not in names and name not in names:
                continue
            p = fn()
            p.finish()
            pieces[full] = p
    return {"pieces": pieces, "meta": {}, "looks": LOOKS}


def finish_meta(data):
    """meta of every piece, computed after the runner has settled the geometry (z-fight turns)."""
    data["meta"] = {n: meta_for(n, p) for n, p in data["pieces"].items()}
    return data


if __name__ == "__main__":
    total = 0
    data = finish_meta(build_all())
    for name, p in data["pieces"].items():
        lo, hi = p.bounds()
        total += p.tris()
        probs = {k: geo_problems(g) for k, g in p.g.items()}
        print("%-36s %5d tris  %s  bounds %s %s  boxes %d  problems %s" % (name, p.tris(), p.stats(), [round(v, 1) for v in lo], [round(v, 1) for v in hi],
                                                                         len(data["meta"][name]["collision"]), probs))
    print("sum of one of each", total)

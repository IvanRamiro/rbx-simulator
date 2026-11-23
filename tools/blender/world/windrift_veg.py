"""Windrift Hold's own vegetation, rocks and paths (2026-11-23). Plain Python, no Blender (windrift_veg_run.py turns the pieces into Blender objects,
renders, QA and FBX). Built on hq_kit's Geo/Piece, in ROBLOX STUDS (x right, y up, z back; a piece's FRONT is -Z), every piece at its own origin with
y = 0 the ground it stands on (feet may sink below). One mesh per piece per material suffix, named Windrift_<Family>_<Piece>__<Suffix>; no textures:
each suffix takes a Roblox Material and Color from LOOKS.

The shape language is ONE PREVAILING WIND, blowing toward +X in every piece's own frame. The territory's placer uses a yaw of about 0, so everything
leans, streams or combs the same way: crowns are flags (limbs and needles only on the lee side, the windward side bare or broken), grass is combed,
rocks lean and have a long scoured tail on the wind side, roots brace on the windward side. This library imports nothing from another map's
vegetation code (hq_kit is the shared geometry container only); the primitives below are its own:

  blade     a closed, tapering, bent leaf / needle / grass blade (a V-section or diamond section loft with a point), the unit of every foliage
  sweep     a closed tapered tube along a Catmull-Rom spine (trunks, limbs, roots, wands), with optional ridges and a twisting grain
  convex    a closed convex solid from half-spaces: quarried, flat-faced stone (slabs, boulders, fins, lintels) and its bronze seams
  slab      a closed irregular slab with a bevelled top (stepping stones, cobbles)

TREES   GaleCedar (A1 flagged, A2 cascade), BannerPine (B1 mast with flags, B2 snapped sail), CliffJuniper (C1 crawler, C2 corkscrew),
        Bronzeleaf (D1 windbroom, D2 lean-to), SplitSnag (E1, E2: a lightning-split pole with new growth), GiantCedar (the landmark)
ROCKS   CragTail, SlateSlab, StrataStack, VeinBoulder (A, B: bronze seams), Windgate, Fin, Scree (A, B), and the paths Steps (A, B), Cobble, PlankWalk
PLANTS  GaleGrass (A, B), Sedge, Gorse, Heather, JuniperCreeper, Cushion, Stonecrop, Thistle, WindStar, Lichen (A, B)
"""
import math
import random

import hq_kit as K
from hq_kit import Geo, Piece, vadd, vsub, vmul, vdot, vcross, vnorm, vlen, lerp, TAU

# ======================================================================================================================
# the looks (Roblox Material + colour per material suffix: no texture, no upload)
# ======================================================================================================================
LOOKS = {
    # wood
    "Bark": {"Material": "Wood", "Color": [58, 46, 38]},                         # dark bark
    "Deadwood": {"Material": "Wood", "Color": [118, 108, 94]},                   # silvered, wind-scoured wood (the split snag, the juniper's spar)
    "Plank": {"Material": "WoodPlanks", "Color": [84, 68, 52]},                  # weathered timber for the plank walk
    # foliage
    "Cedar": {"Material": "LeafyGrass", "Color": [72, 100, 54]},                 # earthy green
    "Needle": {"Material": "LeafyGrass", "Color": [30, 78, 64]},                 # dark jade pine needles
    "Juniper": {"Material": "LeafyGrass", "Color": [44, 90, 72]},                # blue-jade scale foliage
    "BronzeLeaf": {"Material": "LeafyGrass", "Color": [138, 102, 58]},           # muted bronze-brown leaf (not autumn orange)
    "Moss": {"Material": "Grass", "Color": [92, 112, 58]},                       # olive moss
    # ground plants
    "Grass": {"Material": "Grass", "Color": [96, 110, 58], "CastShadow": False},   # gale grass: olive straw
    "Reed": {"Material": "Grass", "Color": [82, 104, 60]},
    "Seed": {"Material": "SmoothPlastic", "Color": [104, 74, 50]},               # sedge seed spikes
    "Gorse": {"Material": "LeafyGrass", "Color": [58, 84, 50]},
    "Heather": {"Material": "LeafyGrass", "Color": [78, 92, 62]},
    "Crassula": {"Material": "LeafyGrass", "Color": [84, 124, 104]},             # stonecrop: teal-grey succulent
    "Lichen": {"Material": "Concrete", "Color": [112, 118, 80], "CastShadow": False},
    # flowers (muted accents: ochre, rose-brown, teal)
    "FlowerOchre": {"Material": "SmoothPlastic", "Color": [196, 152, 66]},
    "FlowerRose": {"Material": "SmoothPlastic", "Color": [166, 98, 94]},
    "FlowerTeal": {"Material": "SmoothPlastic", "Color": [74, 134, 132]},
    # stone
    "Slate": {"Material": "Slate", "Color": [52, 60, 58]},                       # dark slate green-grey
    "SlateStep": {"Material": "Slate", "Color": [46, 54, 52]},
    "Scree": {"Material": "Pebble", "Color": [70, 78, 72], "CastShadow": False},
    "Cobble": {"Material": "Cobblestone", "Color": [64, 68, 62]},
    "Bronze": {"Material": "Metal", "Color": [150, 112, 62]},                    # muted bronze seams and pegs
}

# ======================================================================================================================
# the wind
# ======================================================================================================================
WIND = (1.0, 0.0, 0.0)          # every piece leans, streams and combs toward +X (its own frame)
UP = (0.0, 1.0, 0.0)


def unit(yaw, pitch):
    """A unit vector yawed about +Y from +X (positive yaw turns toward -Z... a small angle either side of the wind) and pitched up (negative: droop)."""
    return (math.cos(yaw) * math.cos(pitch), math.sin(pitch), -math.sin(yaw) * math.cos(pitch))


# ======================================================================================================================
# curves and tubes
# ======================================================================================================================
def catmull(pts, per=4):
    """A Catmull-Rom curve through the knots, `per` samples per span (ends included)."""
    n = len(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for s in range(per):
            t = s / per
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t +
                                    (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in range(3)))
    out.append(tuple(pts[-1]))
    return out


def _rot(v, axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    return vadd(vadd(vmul(v, c), vmul(vcross(axis, v), s)), vmul(axis, vdot(axis, v) * (1 - c)))


def frames_along(pts, ref=None):
    """Parallel-transport frames (tangent, normal, binormal) at every point."""
    n = len(pts)
    T = [vnorm(vsub(pts[min(i + 1, n - 1)], pts[max(i - 1, 0)])) for i in range(n)]
    if ref is None:
        ref = (0.0, 0.0, 1.0) if abs(T[0][1]) > 0.9 else (0.0, 1.0, 0.0)
    N0 = vnorm(vcross(vcross(T[0], ref), T[0]))
    Ns = [N0]
    for i in range(1, n):
        ax = vcross(T[i - 1], T[i])
        if vlen(ax) > 1e-9:
            ang = math.acos(max(-1.0, min(1.0, vdot(T[i - 1], T[i]))))
            Ns.append(vnorm(_rot(Ns[-1], vnorm(ax), ang)))
        else:
            Ns.append(Ns[-1])
    Bs = [vnorm(vcross(T[i], Ns[i])) for i in range(n)]
    return T, Ns, Bs


def sweep(g, pts, radii, sides=6, mod=None, twist=0.0, squash=1.0, phase=0.0, caps=(True, True), ref=None):
    """A closed tapered tube along pts (a radius per point). mod(t, angle) -> a radius factor (ridges, flutes: the grain); twist turns the section per
    point (radians per ring); squash flattens the section's second axis."""
    n = len(pts)
    T, Ns, Bs = frames_along(pts, ref)
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        ring = []
        for k in range(sides):
            a = TAU * k / sides + phase + twist * i
            f = 1.0 if mod is None else mod(i / max(1, n - 1), TAU * k / sides + phase)
            ring.append(g.vert(vadd(p, vadd(vmul(Ns[i], math.cos(a) * r * f), vmul(Bs[i], math.sin(a) * r * f * squash)))))
        rings.append(ring)
    start = len(g.f)
    for i in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            g.face(rings[i][k], rings[i + 1][k], rings[i + 1][j], rings[i][j])
    for idx, ring, at in ((0, rings[0], pts[0]), (1, rings[-1], pts[-1])):
        if caps[idx]:
            c = g.vert(at)
            for k in range(sides):
                j = (k + 1) % sides
                if idx == 0:
                    g.face(c, ring[k], ring[j])
                else:
                    g.face(c, ring[j], ring[k])
    K._orient_solid(g, start)
    return rings


def taper(n, r0, r1, power=1.0, flare=0.0, flare_k=6.0):
    """n radii from r0 down to r1 with an optional exponential flare at the foot."""
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        out.append(lerp(r0, r1, t ** power) + flare * math.exp(-flare_k * t))
    return out


def limb(g, pts, r0, r1, sides=5, per=3, power=0.9, **kw):
    cv = catmull(pts, per)
    return sweep(g, cv, taper(len(cv), r0, r1, power), sides, **kw)


def spine_point(pts, t, per=4):
    """A point at fraction t (0..1) along the polyline of the Catmull curve through pts, and its tangent."""
    cv = catmull(pts, per)
    n = len(cv) - 1
    f = max(0.0, min(1.0, t)) * n
    i = min(n - 1, int(f))
    u = f - i
    p = tuple(cv[i][k] + (cv[i + 1][k] - cv[i][k]) * u for k in range(3))
    d = vnorm(vsub(cv[i + 1], cv[i]))
    return p, d


def grain(n=3, depth=0.10, spin=3.0):
    """A bark grain for sweep(): n ridges that wind round the trunk (spin radians over the length)."""
    return lambda t, a: 1.0 + depth * math.cos(n * (a - spin * t)) + 0.4 * depth * math.cos((n + 2) * a + 2.0 * t)


# ======================================================================================================================
# blades: the unit of foliage
# ======================================================================================================================
def _side_up(T, up):
    s = vcross(up, T)
    if vlen(s) < 1e-5:
        s = vcross((1.0, 0.0, 0.0) if abs(up[0]) < 0.9 else (0.0, 0.0, 1.0), T)
    s = vnorm(s)
    return s, vnorm(vcross(T, s))


def blade(g, base, d, L, w, th=None, bend=(0.0, 0.0, 0.0), up=UP, roll=0.0, prof=(0.55, 1.0), ring=3):
    """A closed, bent, tapering blade from `base` along direction d, length L, widest w. A closed loft of len(prof) rings and a point; `bend` is the offset
    of the tip from the straight line (the droop: it grows with the square of the distance). Section: ring 3 = a V-fold (flat under, ridge over, a
    leaf, a needle), ring 4 = a flat diamond (a plate). th = the ridge height / half thickness. roll turns the section about the blade.
    Triangles: ring 3: 6 per segment + 4 = 10 for two rings; ring 4: 8 per segment + 6."""
    n = len(prof)
    th = th if th is not None else w * 0.3
    if roll == 0.0:         # a small deterministic roll per blade, so two blades from one root never share a flat face (the QA's z-fighting test)
        h = math.sin(base[0] * 127.1 + base[1] * 311.7 + base[2] * 74.7 + L * 53.3 + w * 19.1) * 43758.5453
        roll = (h - math.floor(h) - 0.5) * (0.55 if ring == 3 else 0.22)
    pts = [vadd(vadd(base, vmul(d, L * k / n)), vmul(bend, (k / n) ** 2)) for k in range(n + 1)]
    rings = []
    for k in range(n):
        if k == 0:
            T = vnorm(vsub(pts[1], pts[0]))
        else:
            T = vnorm(vsub(pts[min(k + 1, n)], pts[k - 1]))
        s, u2 = _side_up(T, up)
        if roll:
            s, u2 = (vadd(vmul(s, math.cos(roll)), vmul(u2, math.sin(roll))), vadd(vmul(u2, math.cos(roll)), vmul(s, -math.sin(roll))))
        hw = w * prof[k] / 2
        ht = th * prof[k]
        p = pts[k]
        if ring == 3:
            ids = [g.vert(vadd(p, vmul(s, -hw))), g.vert(vadd(p, vmul(s, hw))), g.vert(vadd(p, vmul(u2, ht)))]
        else:
            ids = [g.vert(vadd(p, vmul(s, -hw))), g.vert(vadd(p, vmul(u2, ht))), g.vert(vadd(p, vmul(s, hw))), g.vert(vadd(p, vmul(u2, -ht)))]
        rings.append(ids)
    apex = g.vert(pts[n])
    start = len(g.f)
    m = ring
    for k in range(n - 1):
        for i in range(m):
            j = (i + 1) % m
            g.face(rings[k][i], rings[k + 1][i], rings[k + 1][j], rings[k][j])
    for i in range(m):
        j = (i + 1) % m
        g.face(rings[n - 1][j], rings[n - 1][i], apex)
    if m == 3:
        g.face(rings[0][0], rings[0][1], rings[0][2])
    else:
        g.face(rings[0][0], rings[0][1], rings[0][2], rings[0][3])
    K._orient_solid(g, start)
    return pts


def fan(g, base, yaw, pitch, n, spread, L, w, th=None, droop=0.3, rng=None, vary=0.25, lift=0.0, ring=3, prof=(0.55, 1.0), up=UP, roll_mode=0, spread_v=0.0):
    """n blades from one root, fanned `spread` radians across the yaw (centre ones longest), each drooping by droop * its length. roll_mode 0: V
    section up; 1: rolled by the fan angle (a bottle-brush). Returns nothing."""
    rng = rng or random.Random(1)
    for i in range(n):
        f = (i - (n - 1) / 2) / max(1, (n - 1) / 2) if n > 1 else 0.0
        yw = yaw + f * spread / 2 + rng.uniform(-0.08, 0.08)
        pt = pitch + lift * (1 - abs(f)) + spread_v * f * f * 0.5 + rng.uniform(-0.06, 0.06)
        ln = L * (1.0 - 0.28 * abs(f)) * (1.0 + rng.uniform(-vary, vary))
        d = unit(yw, pt)
        blade(g, base, d, ln, w * (1.0 + rng.uniform(-0.15, 0.15)), th, bend=(0.0, -droop * ln, 0.0), up=up, roll=(f * 0.8 if roll_mode else 0.0), prof=prof, ring=ring)


def loaf(g, base, d, L, R, flat=0.6, lumps=0.22, bend=(0.0, 0.0, 0.0), sides=6, seed=0):
    """A streamlined lumpy loaf of foliage: a closed loft along d (length L, with `bend` drooping the far end) whose radius swells then tapers to a
    point, flattened (flat < 1) and lobed (lumps): a knot of scale-leaf foliage trailing downwind."""
    pts = [vadd(vadd(base, vmul(d, L * t)), vmul(bend, t * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    radii = [R * 0.35, R * 0.92, R, R * 0.66, R * 0.1]
    ph = seed * 1.7
    sweep(g, pts, radii, sides, mod=lambda t, a: 1.0 + lumps * math.cos(3 * a + ph + 5 * t) + 0.5 * lumps * math.cos(5 * a + 2 * ph), squash=flat, ref=UP)


# ======================================================================================================================
# convex stone: half-space solids
# ======================================================================================================================
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
            out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return out


def convex_polys(planes):
    """planes: [((nx, ny, nz), d)] meaning n . p <= d. Returns [(normal, [vertices CCW seen from outside])] for the convex solid they bound."""
    P = []
    for (n, d) in planes:
        l = vlen(n)
        n1, d1 = vnorm(n), d / l
        if any(vdot(n1, m) > 0.99999 and abs(d1 - e) < 1e-4 for (m, e) in P):      # the same plane twice would make a twin face
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


def add_convex(g, planes, pick=None, extra=None):
    """Adds the convex solid bounded by the planes to Geo g (faces triangulated, vertices shared within the solid). pick(normal) -> a Geo or None
    for the face's own Geo: lets the top faces go to a second material (moss). Returns the polygons."""
    polys = convex_polys(planes)
    # snap vertices closer than 0.02 together (clipping leaves slivers where three planes nearly meet) so shared edges stay shared
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
    polys = snapped
    cache = {}
    start = {}
    for n, poly in polys:
        gg = (pick(n) if pick else None) or g
        if id(gg) not in start:
            start[id(gg)] = (gg, len(gg.f))
        ids = []
        for p in poly:
            key = (id(gg), round(p[0] / 1e-5), round(p[1] / 1e-5), round(p[2] / 1e-5))
            if key not in cache:
                cache[key] = gg.vert(p)
            ids.append(cache[key])
        if len(ids) <= 4:
            gg.face(*ids)
        else:
            for k in range(1, len(ids) - 1):
                gg.face(ids[0], ids[k], ids[k + 1])
    # a solid split over two Geos must be oriented as a whole: orient each by the volume of the whole solid (the sign of the first geo suffices as the
    # winding is outward by construction); a flip is only ever needed on a numerical accident, so check the whole solid on its own Geo when single
    if not pick:
        K._orient_solid(g, list(start.values())[0][1] if start else len(g.f))
    return polys


def rock_planes(spec):
    """A list of (normal, d) from compact specs: ('y-', d) etc. are written by hand in the pieces; this helper only offsets a list by `inflate`."""
    return spec


def inflate(planes, k, skip_down=True):
    out = []
    for n, d in planes:
        if skip_down and n[1] < -0.95:
            out.append((n, d))
        else:
            l = vlen(n)
            out.append((n, d + k * l))
    return out


def slab(g, ring, y0, y1, bev=0.08, inset_bottom=0.0):
    """A closed slab on an irregular star-shaped polygon `ring` ((x, z) points): a vertical wall from y0 to y1 - bev, a bevel ring inset by `bev`
    reaching the exact flat top at y1, caps fanned from the centroid. 6 triangles per ring point."""
    n = len(ring)
    cx = sum(p[0] for p in ring) / n
    cz = sum(p[1] for p in ring) / n
    start = len(g.f)

    def shrink(p, k):
        dx, dz = p[0] - cx, p[1] - cz
        d = math.hypot(dx, dz) or 1.0
        return (p[0] - dx / d * k, p[1] - dz / d * k)
    bot = [g.vert((x, y0, z)) for (x, z) in ring]
    mid = [g.vert((x, y1 - bev, z)) for (x, z) in ring]
    top = [g.vert((x, y1, z)) for (x, z) in [shrink(p, bev) for p in ring]]
    for i in range(n):
        j = (i + 1) % n
        g.face(bot[i], mid[i], mid[j], bot[j])
        g.face(mid[i], top[i], top[j], mid[j])
    cb = g.vert((cx, y0, cz))
    ct = g.vert((cx, y1, cz))
    for i in range(n):
        j = (i + 1) % n
        g.face(cb, bot[i], bot[j])
        g.face(ct, top[j], top[i])
    K._orient_solid(g, start)


def irregular_ring(cx, cz, rx, rz, n, rng, jitter=0.18, rot=0.0):
    """A star-shaped irregular polygon: n points round (cx, cz) with radii rx, rz scaled by a random factor each."""
    pts = []
    for k in range(n):
        a = rot + TAU * (k + rng.uniform(-0.2, 0.2)) / n
        f = 1.0 + rng.uniform(-jitter, jitter)
        pts.append((cx + math.cos(a) * rx * f, cz + math.sin(a) * rz * f))
    return pts


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
def _lee_limb(P, trunk_pts, s, dirv, length, r0, r1, bark="Bark", droop=0.5, up=1.0, sides=5, per=1):
    """A limb leaving the trunk at fraction s of its spine, heading along dirv, length `length`, rising `up` over its first third and dropping `droop` at
    the end. Returns the limb's knots (the root first)."""
    p, _ = spine_point(trunk_pts, s)
    d = vnorm(dirv)
    k = [vadd(p, vmul(d, -0.25)),
         vadd(p, vadd(vmul(d, length * 0.33), (0.0, up, 0.0))),
         vadd(p, vadd(vmul(d, length * 0.68), (0.0, up * 0.9 - droop * 0.35, 0.0))),
         vadd(p, vadd(vmul(d, length), (0.0, up * 0.5 - droop, 0.0)))]
    limb(P.geo(bark), k, r0, r1, sides=sides, per=per + 1)
    return k


def _sprays(gl, k, rng, fracs=(0.5, 0.78, 1.0), n=6, L=3.8, w=0.62, th=0.2, droop=0.42, spread=1.05, prof=(0.65, 1.0), ring=3, rows=2):
    """Combed sprays of blades along the outer part of a limb (knots k): each root fans downwind with a little yaw from the limb's own heading."""
    for f in fracs:
        p, d = spine_point(k, f, per=2)
        yaw = math.atan2(-d[2], max(d[0], 0.25)) * 0.5
        big = 0.75 + 0.5 * f
        fan(gl, p, yaw, -0.1 + 0.08 * (1 - f), n, spread, L * big, w, th, droop=droop, rng=rng_of(k, f), prof=prof, ring=ring)
        if rows > 1:
            fan(gl, vadd(p, (0.0, 0.18, 0.0)), yaw + 0.1, 0.22, max(3, n - 2), spread * 0.8, L * big * 0.72, w * 0.9, th, droop=droop * 0.8, rng=rng_of(k, f + 3), prof=prof, ring=ring)


def rng_of(k, f):
    return random.Random(int(abs(k[0][0] * 131 + k[-1][1] * 71 + k[-1][0] * 17 + f * 1000)) % 99991)


def gale_cedar(variant):
    """The wind-flagged cliff cedar. Growth rule: the trunk twists up and leans downwind with a spiral grain; every limb leaves it on the lee side and
    streams toward +X, ending in combed sprays of long narrow needles that droop; the windward side is bare, with broken stubs and a dead spar.
    A1: the flag, an upright S-curved tree 17 high whose four limbs and top tuft trail 12 studs. A2: the lee canopy, a stout leaning bole 7 high whose
    six limbs fan across the lee half only, a low wide drooping veil of needles (14 across) over bracing roots, the windward half bare."""
    P = Piece()
    rng = random.Random(110 + variant)
    gb = P.geo("Bark")
    gl = P.geo("Cedar")
    if variant == 0:
        trunk = [(0.0, -0.5, 0.0), (0.2, 1.4, 0.0), (0.7, 4.0, 0.1), (1.6, 7.0, -0.1), (2.9, 10.0, 0.0), (4.4, 12.4, 0.1), (6.0, 13.8, 0.0)]
        cv = catmull(trunk, 2)
        sweep(gb, cv, taper(len(cv), 1.2, 0.28, 0.8, flare=0.9, flare_k=9.0), 8, mod=grain(3, 0.13, 2.6))
        for (pts, r) in (([(-0.3, 0.7, 0.3), (-1.8, 0.5, 0.8), (-3.2, 0.0, 1.5), (-4.0, -0.5, 2.0)], 0.6),
                         ([(-0.3, 0.7, -0.3), (-1.9, 0.4, -0.9), (-3.4, -0.1, -1.6), (-4.2, -0.5, -2.1)], 0.55),
                         ([(-0.5, 0.6, 0.0), (-2.2, 0.35, 0.1), (-3.8, -0.2, 0.0), (-4.8, -0.6, 0.1)], 0.5),
                         ([(0.4, 0.5, -0.4), (1.6, 0.1, -1.0), (2.5, -0.4, -1.4)], 0.36)):
            limb(gb, pts, r, 0.1, sides=4, per=1)
        for (s, yw, ln) in ((0.36, math.pi * 0.85, 1.6), (0.54, -math.pi * 0.8, 1.3), (0.68, math.pi * 0.95, 1.0)):
            p, _ = spine_point(trunk, s)
            d = unit(yw, 0.25)
            limb(gb, [p, vadd(p, vmul(d, ln * 0.5)), vadd(p, vadd(vmul(d, ln), (0.0, 0.3, 0.0)))], 0.28, 0.08, sides=4, per=1)
        limb(gb, [(5.5, 13.2, 0.0), (5.2, 15.2, 0.1), (4.6, 17.2, 0.0)], 0.22, 0.04, sides=4, per=1)      # the dead spar
        limbs = [(0.3, (1.0, 0.3, 0.45), 7.8, 0.55, 0.14, 1.0, 0.6), (0.48, (1.0, 0.25, -0.5), 6.8, 0.46, 0.12, 0.9, 0.55),
                 (0.66, (1.0, 0.3, 0.35), 5.8, 0.4, 0.11, 0.8, 0.5), (0.84, (1.0, 0.35, -0.2), 4.6, 0.32, 0.1, 0.6, 0.4)]
        crown = trunk[-1]
    else:
        trunk = [(0.0, -0.5, 0.0), (0.3, 1.6, 0.0), (1.0, 3.6, 0.1), (2.0, 5.4, 0.1), (3.1, 6.6, 0.0)]
        cv = catmull(trunk, 2)
        sweep(gb, cv, taper(len(cv), 1.45, 0.55, 0.8, flare=1.0, flare_k=8.0), 8, mod=grain(3, 0.14, -2.4))
        for (pts, r) in (([(-0.2, 0.9, 0.3), (-1.4, 1.0, 0.9), (-2.8, 0.5, 1.6), (-3.6, -0.4, 2.2)], 0.65),
                         ([(-0.2, 0.9, -0.3), (-1.5, 1.1, -0.9), (-2.9, 0.4, -1.7), (-3.8, -0.4, -2.3)], 0.65),
                         ([(0.1, 0.7, 0.4), (-0.3, 0.9, 1.2), (-1.0, 0.4, 2.4), (-1.5, -0.4, 3.2)], 0.45),
                         ([(0.2, 0.6, -1.0), (-0.9, 0.7, -2.0), (-1.8, -0.1, -2.8), (-2.2, -0.6, -3.1)], 0.42),
                         ([(0.6, 0.5, 0.3), (1.6, 0.2, 1.1), (2.4, -0.4, 1.6)], 0.34)):
            limb(gb, pts, r, 0.1, sides=4, per=1)
        limb(gb, [spine_point(trunk, 0.6)[0], (-0.4, 4.7, 0.2), (-1.5, 4.9, 0.4), (-2.2, 4.5, 0.5)], 0.34, 0.08, sides=4, per=1)     # a broken windward stub
        # six limbs fanned across the lee half, each at its own pitch, long ones drooping their veils over the drop
        fanl = [(0.95, 0.35, 6.0), (0.55, 0.2, 8.4), (0.15, 0.4, 7.4), (-0.2, 0.15, 9.2), (-0.6, 0.32, 7.0), (-1.0, 0.25, 5.8)]
        limbs = []
        for i, (yw, pt, ln) in enumerate(fanl):
            sfr = 0.55 + 0.09 * i
            limbs.append((sfr, unit(yw, pt), ln, 0.42 - 0.03 * i, 0.12, 0.8 + 0.2 * (i % 2), 0.55))
        crown = trunk[-1]
    for (s, dv, length, r0, r1, up, drp) in limbs:
        k = _lee_limb(P, trunk, s, dv, length, r0, r1, droop=drp * 1.5, up=up * 0.9)
        if variant == 0:
            _sprays(gl, k, rng, n=5, w=0.74)
        else:
            _sprays(gl, k, rng, fracs=(0.62, 1.0), n=5, L=3.8, w=0.72, rows=2)
        p, d = spine_point(k, 1.0, per=2)
        for j in range(2):          # a veil hanging from the limb's end
            blade(gl, p, unit(rng.uniform(-0.4, 0.4), -1.1), 3.0 if variant else 2.8, 0.55, 0.16, bend=(1.0, -0.2, rng.uniform(-0.2, 0.2)), prof=(0.65, 1.0))
    fan(gl, crown, 0.1, 0.1, 7, 1.5, 3.9, 0.7, 0.2, droop=0.5, rng=rng, lift=0.5, prof=(0.65, 1.0))
    fan(gl, vadd(crown, (-0.2, -0.8, 0.0)), -0.1, -0.1, 6, 1.3, 4.2, 0.7, 0.2, droop=0.45, rng=rng, prof=(0.65, 1.0))
    return P


def banner_pine(variant):
    """The ridge pine. Growth rule: a tall straight mast with a thin spiral-grained trunk; its dark needles are borne only on the lee side, in flat
    hand-shaped plates (a fan of wide flat blades laid in one plane, longest in the middle) at irregular heights on short stalks, so the tree reads as
    a mast carrying pennants. The windward side has only dead stubs. B1: the mast, 25 high, seven pennants shortening toward the top. B2: the sail, a
    stout pine 17 high snapped at 12.5 (a splintered top), the pennants long below and short above, a revived leader curling up from the lee side."""
    P = Piece()
    rng = random.Random(210 + variant)
    gb = P.geo("Bark")
    gn = P.geo("Needle")
    if variant == 0:
        trunk = [(0.0, -0.5, 0.0), (0.1, 2.0, 0.0), (0.3, 6.0, 0.1), (0.7, 10.5, 0.0), (1.2, 15.0, 0.1), (1.9, 19.2, 0.0), (2.6, 23.0, 0.0)]
        cv = catmull(trunk, 2)
        sweep(gb, cv, taper(len(cv), 1.2, 0.14, 0.78, flare=0.8, flare_k=10.0), 7, mod=grain(3, 0.11, 3.0))
        flags = [(6.6, 6.8, 0.4), (9.6, 6.2, -0.45), (12.4, 5.4, 0.5), (15.0, 4.6, -0.3), (17.4, 3.8, 0.4), (19.8, 2.8, -0.2)]
        for (y0, yw, ln) in ((8.2, math.pi * 0.9, 1.6), (13.0, -math.pi * 0.85, 1.3), (17.5, math.pi * 0.95, 1.0)):
            p, _ = spine_point(trunk, (y0 + 0.5) / 23.5)
            d = unit(yw, 0.2)
            limb(gb, [p, vadd(p, vmul(d, ln * 0.5)), vadd(p, vadd(vmul(d, ln), (0.0, 0.2, 0.0)))], 0.2, 0.06, sides=4, per=1)
        for (s, dx, dz, r) in ((0.0, -1.8, 1.0, 0.45), (0.0, -1.7, -1.1, 0.4), (0.0, 1.4, -1.0, 0.32)):
            limb(gb, [(dx * 0.1, 0.7, dz * 0.12), (dx * 0.55, 0.45, dz * 0.55), (dx, -0.4, dz)], r, 0.1, sides=4, per=1)
        top = trunk[-1]
        fan(gn, top, 0.05, 0.9, 7, 1.0, 3.0, 0.55, 0.3, droop=0.1, rng=rng, ring=4, prof=(0.7, 1.0), roll_mode=1, lift=0.3)
        trunkf = trunk
    else:
        trunk = [(0.0, -0.5, 0.0), (0.05, 2.0, 0.0), (0.4, 5.5, 0.0), (0.9, 9.0, 0.0), (1.4, 12.6, 0.0)]
        cv = catmull(trunk, 2)
        sweep(gb, cv, taper(len(cv), 1.25, 0.7, 0.9, flare=0.9, flare_k=9.0), 8, mod=grain(3, 0.14, 2.4))
        for (ya, ln, yw) in ((0.0, 4.6, 0.05), (1.3, 3.4, 0.0), (2.6, 2.8, -0.05)):            # a splintered top: three torn staves
            blade(gb, vadd(trunk[-1], (0.0, -1.2 + ya * 0.2, 0.0)), unit(ya * 1.2 - 1.0, 1.25 - ya * 0.1), ln, 1.0, 0.5, bend=(0.3, 0.0, 0.0), ring=4, prof=(0.85, 0.7))
        for (pts, r) in (([(-0.3, 0.8, 0.3), (-1.7, 0.4, 0.8), (-3.0, -0.4, 1.4)], 0.55), ([(-0.3, 0.8, -0.3), (-1.8, 0.4, -0.9), (-3.1, -0.4, -1.5)], 0.5),
                         ([(0.5, 0.6, -0.4), (1.7, 0.1, -1.0), (2.5, -0.4, -1.3)], 0.35)):
            limb(gb, pts, r, 0.1, sides=4, per=1)
        flags = [(3.2, 7.4, 0.35), (5.0, 6.8, -0.4), (6.8, 6.0, 0.4), (8.6, 5.0, -0.3), (10.2, 4.0, 0.25), (11.6, 3.0, -0.1)]
        limb(gb, [(-0.6, 6.0, 0.0), (-2.2, 6.6, 0.3), (-3.6, 6.0, 0.6), (-4.8, 4.8, 0.7)], 0.3, 0.07, sides=4, per=2)     # a dead windward limb
        limb(gb, [(-3.0, 6.4, 0.45), (-3.8, 7.6, 0.6), (-4.2, 8.6, 0.6)], 0.14, 0.04, sides=4, per=1)
        k = [(0.95, 10.0, 0.0), (2.2, 11.2, 0.2), (3.5, 13.4, 0.1), (4.0, 15.8, 0.0), (3.7, 17.4, 0.0)]       # the revived leader
        limb(gb, k, 0.34, 0.08, sides=5, per=2)
        fan(gn, k[-1], 0.1, 1.0, 7, 1.1, 3.0, 0.55, 0.3, droop=0.1, rng=rng, ring=4, prof=(0.7, 1.0), roll_mode=1, lift=0.3)
        for f, ln in ((0.5, 3.4), (0.75, 2.8)):
            p, d = spine_point(k, f, per=2)
            fan(gn, p, 0.1, 0.05, 4, 0.9, ln, 0.9, 0.08, droop=0.2, rng=rng, ring=4, prof=(0.7, 1.0))
        trunkf = trunk
    for (y0, ln, zo) in flags:
        # the stalk then the pennant: a flat hand of blades laid in one plane, drooping a little, the middle ones longest
        p, _ = spine_point(trunkf, min(1.0, (y0 + 0.5) / (trunkf[-1][1] + 0.5)))
        stalk = [vadd(p, (-0.2, 0.0, 0.0)), vadd(p, (0.8, 0.1, zo * 1.2)), vadd(p, (1.7, 0.0, zo * 1.5))]
        limb(gb, stalk, 0.22, 0.12, sides=4, per=1)
        root = stalk[-1]
        tilt = 0.7 * (1 if zo > 0 else -1)
        upv = (0.0, math.cos(tilt), math.sin(tilt))
        fan(gn, root, zo * 0.5, 0.08, 7, 1.5, ln, 1.5, 0.1, droop=0.22, rng=rng, ring=4, prof=(0.7, 1.0), lift=0.05, up=upv, spread_v=0.5)
        fan(gn, vadd(root, (-0.2, 0.3, 0.0)), zo * 0.5 + 0.05, 0.2, 4, 1.0, ln * 0.64, 1.2, 0.08, droop=0.15, rng=rng, ring=4, prof=(0.7, 1.0), up=upv)
    return P


def cliff_juniper(variant):
    """The cliff juniper: silvered, twisted trunk clinging to the stone; foliage in flame-shaped knots strung along it, every knot streaming downwind.
    C1: the crawler, 12 long and 5 high: roots gripping at the windward end, the trunk wandering along the ground and rising to a swept head, a dead
    spar standing up behind. C2: the corkscrew, 8 high: a tight spiral trunk with a deadwood scar, three knots on the lee side and a swept top."""
    P = Piece()
    rng = random.Random(310 + variant)
    gd = P.geo("Deadwood")
    gj = P.geo("Juniper")
    if variant == 0:
        trunk = [(-3.6, -0.3, 0.1), (-2.6, 1.0, 0.5), (-1.2, 1.5, 0.3), (0.2, 1.1, -0.4), (1.8, 1.7, -0.6), (3.4, 2.6, -0.2), (4.8, 3.3, 0.2), (6.2, 3.8, 0.2)]
        cv = catmull(trunk, 3)
        sweep(gd, cv, taper(len(cv), 0.85, 0.2, 0.9, flare=0.5, flare_k=8.0), 6, mod=grain(3, 0.2, 4.5), twist=0.12)
        for (pts, r) in (([(-3.4, 0.5, 0.2), (-4.4, 0.2, 0.9), (-5.0, -0.5, 1.5)], 0.42), ([(-3.4, 0.5, 0.0), (-4.6, 0.1, -0.7), (-5.4, -0.5, -1.2)], 0.4),
                         ([(-2.4, 0.6, 0.5), (-2.8, 0.2, 1.6), (-3.2, -0.5, 2.3)], 0.32)):
            limb(gd, pts, r, 0.1, sides=4, per=1)
        limb(gd, [(-2.0, 1.4, 0.4), (-2.1, 2.8, 0.3), (-1.7, 4.2, 0.2), (-1.3, 5.1, 0.2)], 0.3, 0.06, sides=4, per=2)      # the dead spar
        limb(gd, [(1.8, 1.7, -0.6), (2.8, 2.3, -1.2), (4.0, 2.4, -1.6)], 0.22, 0.1, sides=4, per=1)
        knots = [(0.3, 0.3, 0.5, 1.0), (0.45, 0.5, -0.5, 1.2), (0.62, 0.25, 0.3, 1.1), (0.8, 0.4, -0.2, 1.0), (1.0, 0.45, 0.1, 0.9)]
        extra = [(4.0, 2.4, -1.6)]
    else:
        cvp = []
        for i in range(13):
            t = i / 12.0
            a = TAU * 1.5 * t + 0.6
            amp = 0.75 * (1 - 0.55 * t)
            cvp.append((amp * math.cos(a) + 1.6 * t * t * 2.2, -0.25 + 7.9 * t, amp * math.sin(a)))
        sweep(gd, cvp, taper(len(cvp), 0.8, 0.14, 0.95, flare=0.6, flare_k=9.0), 6, mod=grain(3, 0.22, 4.0), twist=0.2)
        trunk = cvp
        for (pts, r) in (([(-0.4, 0.6, 0.3), (-1.6, 0.2, 0.8), (-2.4, -0.5, 1.2)], 0.45), ([(-0.3, 0.6, -0.3), (-1.7, 0.1, -1.0), (-2.6, -0.5, -1.4)], 0.4),
                         ([(0.5, 0.5, 0.4), (1.5, 0.0, 1.1), (2.2, -0.5, 1.5)], 0.32)):
            limb(gd, pts, r, 0.1, sides=4, per=1)
        limb(gd, [(trunk[4][0], trunk[4][1], trunk[4][2]), (-0.5, 4.6, 0.9), (-1.2, 6.0, 1.0), (-1.4, 7.4, 0.9)], 0.25, 0.05, sides=4, per=2)   # a deadwood spar standing on the windward side
        knots = [(0.45, 0.4, 0.3, 1.1), (0.65, 0.3, -0.4, 1.1), (0.85, 0.25, 0.3, 1.0), (1.0, 0.5, 0.0, 1.0)]
        extra = []
    # the knots: lumpy flame-shaped loaves of scale foliage strung on the trunk, each trailing downwind, with a few narrow blades at the lee edge
    for ki, (s_, up, zo, sc) in enumerate(knots):
        i = int(s_ * (len(trunk) - 1))
        p = trunk[min(i, len(trunk) - 1)] if variant == 1 else spine_point(trunk, s_, per=3)[0]
        for row in range(3):
            yaw = zo * 0.3 + 0.35 * (row - 1)
            d = unit(yaw, 0.12 + 0.12 * row + up * 0.25)
            q = vadd(p, (0.0, 0.1 + 0.25 * row, 0.35 * (row - 1)))
            loaf(gj, q, d, 3.4 * sc * (1 - 0.18 * row), 1.0 * sc * (1 - 0.12 * row), flat=0.62, bend=(0.0, -0.5, 0.0), seed=ki * 3 + row)
        fan(gj, vadd(p, (1.8 * sc, 0.2, 0.0)), zo * 0.3, 0.05, 4, 1.4, 1.9, 0.5, 0.25, droop=0.2, rng=rng, ring=3, prof=(0.85, 1.0))
    for e in extra:
        loaf(gj, e, unit(-0.2, 0.1), 2.8, 0.8, flat=0.62, bend=(0.0, -0.4, 0.0), seed=11)
    return P


def bronzeleaf(variant):
    """The bronzeleaf, a small wind-trained tree with broad muted-bronze leaves. Growth rule: leaves hang in strings on whippy shoots that all point
    downwind, shed from the windward side first. D1: the windbroom, a low root crown throwing five arching wands 9 to 10 long, swept so far downwind
    that the tree reads as a feather duster blown flat. D2: the wind-pruned wedge, a short trunk at the windward end under a canopy that rises toward
    the lee: low where the wind hits it, tall on the far side, three leaf shelves of unequal length held on one long limb."""
    P = Piece()
    rng = random.Random(410 + variant)
    gb = P.geo("Bark")
    gl = P.geo("BronzeLeaf")

    def leaf(p, d, L=1.7, w=0.95, up=UP, roll=0.0):
        blade(gl, p, vnorm(d), L, w, 0.1, bend=(0.0, -0.35 * L, 0.0), up=up, roll=roll, prof=(0.75, 1.0), ring=4)
    if variant == 0:
        stems = [((0.0, 0.0, 0.0), [(0.2, 2.0, 0.2), (1.2, 4.4, 0.6), (3.0, 6.6, 0.9)], 0.3), ((0.0, 0.0, 0.0), [(0.4, 1.8, -0.3), (1.9, 3.6, -0.7), (4.6, 5.4, -1.0)], 0.3),
                 ((0.0, 0.0, 0.0), [(0.8, 1.6, 0.0), (2.8, 3.0, 0.3), (5.8, 4.2, 0.4)], 0.28), ((0.0, 0.0, 0.0), [(-0.1, 2.2, 0.5), (0.5, 5.0, 0.9), (1.6, 8.0, 0.8)], 0.26),
                 ((0.0, 0.0, 0.0), [(1.2, 1.2, -0.4), (3.8, 2.1, -0.8), (7.6, 2.8, -0.9)], 0.24)]
        for (st, pts, r) in stems:
            k = [(st[0], -0.4, st[2])] + pts
            limb(gb, k, r, 0.07, sides=5, per=2)
            cv = catmull(k, 3)
            n = len(cv)
            for q in range(5):          # leaf strings on the distal half: a pair at each of five stations, trailing downwind
                f = 0.42 + 0.14 * q
                i = min(n - 2, int(f * (n - 1)))
                p = cv[i]
                tan = vnorm(vsub(cv[i + 1], cv[i]))
                dl = vnorm(vadd(vmul(tan, 0.5), (0.9, -0.1, 0.0)))
                for sgn in (-1, 1):
                    leaf(p, vadd(dl, (0.0, 0.0, sgn * 0.55)), 1.5 + 0.3 * f, 0.9, roll=sgn * 0.4)
            leaf(cv[-1], vadd(vnorm(vsub(cv[-1], cv[-3])), (0.8, 0.0, 0.0)), 1.8, 0.95)
    else:
        trunk = [(-0.6, -0.5, 0.0), (-0.5, 1.0, 0.0), (-0.1, 2.0, 0.1), (0.6, 2.7, 0.0)]
        cv = catmull(trunk, 2)
        sweep(gb, cv, taper(len(cv), 1.0, 0.55, 0.9, flare=0.7, flare_k=8.0), 7, mod=grain(2, 0.15, 2.0))
        for (pts, r) in (([(-0.7, 0.7, 0.3), (-1.7, 0.4, 0.8), (-2.5, -0.4, 1.2)], 0.45), ([(-0.7, 0.7, -0.3), (-1.7, 0.3, -0.9), (-2.6, -0.4, -1.3)], 0.42)):
            limb(gb, pts, r, 0.1, sides=4, per=1)
        # three limbs rising toward the lee, the crown a wedge that is low where the wind meets it and tall on the far side
        spec = [((0.4, 2.5, 0.0), 0.30, 0.30, 8.6, 0.8), ((0.6, 2.6, 0.0), 0.52, -0.5, 7.0, 0.4), ((0.2, 2.2, 0.0), 0.80, 0.45, 5.0, -0.3)]
        for (root, elev, yw, ln, zs) in spec:
            d = unit(yw * 0.35, elev)
            k = [root, vadd(root, vmul(d, ln * 0.35)), vadd(root, vmul(d, ln * 0.7)), vadd(root, vmul(d, ln))]
            limb(gb, k, 0.4, 0.07, sides=5, per=2)
            cb = catmull(k, 3)
            for q in range(5):                       # a twig at each step, each carrying a fan of leaves trailing downwind
                t = 0.25 + 0.17 * q
                i = min(len(cb) - 2, int(t * (len(cb) - 1)))
                p = cb[i]
                for sgn in (-1, 1):
                    tw = [p, vadd(p, (0.5, 0.2, sgn * 0.9)), vadd(p, (0.9, 0.4, sgn * 1.5))]
                    limb(gb, tw, 0.1, 0.05, sides=3, per=1)
                    for lf in range(2):
                        blade(gl, tw[-1], vnorm((1.0, 0.1 + 0.2 * lf, sgn * (0.2 + 0.5 * lf))), 2.0, 1.15, 0.1, bend=(0.0, -0.6, 0.0), roll=0.35 * (2 * lf - 1), prof=(0.75, 1.0), ring=3)
            blade(gl, cb[-1], vnorm(vsub(cb[-1], cb[-4])), 2.2, 1.2, 0.1, bend=(0.0, -0.4, 0.0), prof=(0.75, 1.0), ring=3)
    return P


def split_snag(variant):
    """The split snag: a lightning-struck trunk, silvered and torn open lengthwise into staves of different height, with new growth taking over on the
    lee side: a living limb of dark leaves leaves the bole low down and streams downwind. E1: the standing split, 12 high, four staves round a hollow.
    E2: the fallen half, a 7 high stump whose torn half has slid out and leans downwind on it like a ramp, a sprout at its foot."""
    P = Piece()
    rng = random.Random(510 + variant)
    gd = P.geo("Deadwood")
    gl = P.geo("Cedar")
    if variant == 0:
        trunk = [(0.0, -0.5, 0.0), (0.05, 2.0, 0.0), (0.15, 5.0, 0.0)]
        cv = catmull(trunk, 3)
        sweep(gd, cv, taper(len(cv), 1.7, 1.25, 0.9, flare=0.9, flare_k=9.0), 9, mod=grain(4, 0.16, 1.5), caps=(True, True))
        staves = [(-0.3, 0.4, 1.1, 8.6, 1.7, 0.18), (0.7, -0.6, 1.2, 5.0, 1.5, -0.2), (-0.5, -0.7, 1.2, 4.2, 1.3, 0.35), (0.5, 0.7, 1.1, 2.9, 1.4, -0.1), (-0.9, 0.0, 1.0, 3.3, 1.1, -0.35),
                  (0.1, -0.1, 1.0, 5.8, 1.2, 0.5)]
        for (ox, oz, rr, ln, w, lean) in staves:
            d = vnorm((lean * 0.6 + ox * 0.15, 1.0, oz * 0.15))
            blade(gd, (ox, 3.7, oz), d, ln, w, 0.6, ring=4, prof=(0.9, 0.85), bend=(0.2 + lean * 0.5, 0.0, oz * 0.1))
        for (pts, r) in (([(-0.4, 0.7, 0.3), (-1.7, 0.4, 0.9), (-2.7, -0.5, 1.4)], 0.5), ([(-0.4, 0.7, -0.4), (-1.8, 0.3, -1.0), (-2.8, -0.5, -1.5)], 0.5),
                         ([(0.5, 0.6, 0.4), (1.7, 0.1, 1.1), (2.6, -0.5, 1.5)], 0.4), ([(0.7, 0.5, -0.4), (1.8, 0.0, -1.0), (2.7, -0.5, -1.4)], 0.38)):
            limb(gd, pts, r, 0.12, sides=4, per=1)
        for (ox, oz, ln, yw) in ((1.2, 0.6, 3.6, 0.2), (1.1, -0.7, 3.0, -0.3), (-1.2, 0.5, 2.6, 0.4), (-1.1, -0.6, 3.2, -0.2)):      # strips of torn bark peeling off the bole
            blade(gd, (ox, 0.4, oz), vnorm((ox * 0.25, 1.0, oz * 0.25)), ln, 0.9, 0.28, ring=4, prof=(1.0, 0.8), bend=(ox * 0.3, 0.0, oz * 0.3))
        # the new growth: a living limb on the lee side
        k = [(1.0, 2.2, 0.3), (2.4, 3.4, 0.6), (4.2, 4.0, 0.5), (6.0, 3.4, 0.4)]
        limb(gl, k, 0.34, 0.08, sides=5, per=2)
        _sprays(gl, k, rng, fracs=(0.4, 0.62, 0.82, 1.0), n=6, L=3.2, w=0.7)
        k3 = [(1.2, 0.9, 0.6), (2.4, 1.5, 1.0), (3.6, 1.5, 1.2)]
        limb(gl, k3, 0.2, 0.06, sides=4, per=2)
        _sprays(gl, k3, rng, fracs=(0.6, 1.0), n=6, L=2.6, w=0.6)
        k2 = [(1.0, 1.2, -0.4), (2.0, 1.9, -0.9), (3.6, 2.2, -1.2), (5.0, 1.6, -1.2)]
        limb(gl, k2, 0.22, 0.06, sides=4, per=2)
        _sprays(gl, k2, rng, fracs=(0.6, 1.0), n=5, L=2.6, w=0.6)
    else:
        trunk = [(0.0, -0.5, 0.0), (0.0, 2.5, 0.0), (-0.1, 6.0, 0.0)]
        cv = catmull(trunk, 3)
        sweep(gd, cv, taper(len(cv), 1.8, 1.3, 0.9, flare=0.8, flare_k=9.0), 9, mod=grain(4, 0.16, -1.5))
        blade(gd, (-0.2, 5.4, 0.0), vnorm((-0.2, 1.0, 0.1)), 2.8, 1.5, 0.6, ring=4, prof=(0.9, 0.8))
        blade(gd, (0.6, 5.2, 0.4), vnorm((0.1, 1.0, -0.1)), 1.9, 1.3, 0.5, ring=4, prof=(0.9, 0.8))
        # the torn half: a long flat slab sliding out downwind, its lower end on the ground
        blade(gd, (0.8, 6.2, 0.2), vnorm((1.0, -0.55, 0.0)), 8.0, 2.2, 0.7, ring=4, prof=(0.9, 0.95, 0.7), bend=(0.0, -0.6, 0.0), up=(0.0, 0.0, 1.0))
        for (pts, r) in (([(-0.4, 0.7, 0.4), (-1.7, 0.4, 1.0), (-2.7, -0.5, 1.5)], 0.5), ([(-0.4, 0.7, -0.4), (-1.8, 0.3, -1.0), (-2.8, -0.5, -1.5)], 0.5),
                         ([(0.5, 0.6, -0.5), (1.4, 0.1, -1.4), (2.2, -0.5, -1.8)], 0.38)):
            limb(gd, pts, r, 0.12, sides=4, per=1)
        for (ox, oz, ln, yw) in ((1.2, 0.6, 3.4, 0.2), (1.1, -0.7, 2.8, -0.3), (-1.3, 0.4, 2.4, 0.4), (-1.0, -0.6, 3.0, -0.2)):      # strips of torn bark peeling off the stump
            blade(gd, (ox, 0.4, oz), vnorm((ox * 0.25, 1.0, oz * 0.25)), ln, 0.9, 0.28, ring=4, prof=(1.0, 0.8), bend=(ox * 0.3, 0.0, oz * 0.3))
        blade(gd, (0.3, 5.6, -0.5), vnorm((0.1, 1.0, -0.2)), 1.6, 1.1, 0.4, ring=4, prof=(0.9, 0.8))
        k = [(5.8, 0.3, 0.6), (6.6, 1.6, 0.9), (8.0, 2.6, 0.8), (9.6, 2.6, 0.7)]
        limb(gl, k, 0.3, 0.07, sides=5, per=2)
        _sprays(gl, k, rng, fracs=(0.35, 0.55, 0.75, 0.9, 1.0), n=6, L=3.0, w=0.7)
        for (ox, oz, ln) in ((-0.9, 1.0, 3.0), (0.4, 1.2, 2.6)):
            blade(gd, (ox, 0.6, oz), vnorm((ox * 0.3, 1.0, oz * 0.3)), ln, 0.9, 0.28, ring=4, prof=(1.0, 0.8), bend=(ox * 0.3, 0.0, oz * 0.3))
        k2 = [(5.0, 0.2, -0.6), (6.2, 0.9, -1.1), (7.8, 1.4, -1.3)]
        limb(gl, k2, 0.2, 0.06, sides=4, per=2)
        _sprays(gl, k2, rng, fracs=(0.6, 1.0), n=5, L=2.4, w=0.6)
    return P



def giant_cedar():
    """The Windtorn Elder: the landmark. A colossal cliff cedar 47 high on a crag at the cliff edge: a stout, deeply fissured bole (radius 3.6) that rises 26
    studs and forks, the wind having taken everything on its windward side. Three arms leave the fork like an open hand pointing downwind (a lower arm 30
    long that sags out over the drop, an upper arm 24 long, a short snapped leader rising to a dead spar), each carrying drifts of long needles on its outer
    half; two bare, silvered antlers claw up and back on the windward side. The windward roots clamp over the crag and into the ground, the lee roots grip its
    back. Three meshes: Bark, Cedar, Slate (the crag). A single Cedar mesh over 3,000 triangles is the price of one flag of foliage in one material."""
    P = Piece()
    rng = random.Random(777)
    gb = P.geo("Bark")
    gl = P.geo("Cedar")
    gs = P.geo("Slate")
    # the crag the tree stands on: three bodies, top about 4.5 over the ground, the tree's foot sunk into its middle
    crag = ground_clip(box_pl(-9.5, 6.5, -2, 4.8, -6.8, 6.4) + [pl((-0.6, 0.8, 0.2), (-7.5, 3.8, 0)), pl((0.5, 0.85, -0.2), (4.5, 4.0, 0)), pl((-0.4, 0.4, -0.9), (-5, 2.5, -6.2)),
                                                                pl((0.0, 0.5, 0.85), (0, 2.8, 6.0)), pl((-1.0, 0.0, 0.5), (-9.5, 0, 3.0)), pl((0.8, 0.0, -0.6), (6.0, 0, -4.4)),
                                                                pl((-0.4, 0.9, 0.15), (-3.0, 4.8, 0)), pl((-0.3, 0.9, -0.5), (-4.0, 4.4, -3.5)), pl((0.4, 0.8, 0.5), (3.0, 4.2, 3.0)),
                                                                pl((-0.8, 0.5, -0.4), (-8.0, 3.0, -4.0)), pl((0.7, 0.6, 0.45), (5.5, 3.0, 4.0))], -0.5)
    add_convex(gs, crag)
    lee = ground_clip(box_pl(3.0, 13.0, -2, 2.4, -3.8, 4.2) + [pl((0.2, 0.9, 0.3), (4.0, 2.4, 0)), pl((1.0, 0.25, 0.1), (13.0, 0.0, 0)), pl((0.3, 0.0, -0.95), (9.0, 0, -3.0)),
                                                              pl((0.4, 0.0, 0.9), (9.0, 0, 3.0)), pl((0.3, 0.8, -0.5), (8.0, 1.8, -2.0)), pl((0.5, 0.7, 0.5), (10.0, 1.2, 2.0))], -0.46)
    add_convex(gs, lee)
    shoulder = ground_clip(box_pl(-13.0, -5.0, -2, 2.6, -5.5, 2.5) + [pl((-0.7, 0.7, 0.0), (-11.5, 2.2, 0)), pl((0.4, 0.9, -0.2), (-6.0, 2.6, 0)), pl((-0.5, 0.0, -0.85), (-9.0, 0, -5.4)),
                                                                     pl((-0.3, 0.8, 0.5), (-8.0, 2.4, 1.6)), pl((-0.9, 0.2, 0.3), (-13.0, 0.5, 0))], -0.42)
    add_convex(gs, shoulder)
    ledge = ground_clip(box_pl(-8.0, -3.0, -2, 1.2, 4.0, 8.8) + [pl((-0.5, 0.8, 0.5), (-5.0, 1.2, 7.0)), pl((0.2, 0.0, 0.97), (-5.0, 0, 8.8)), pl((-0.7, 0.0, 0.5), (-8.0, 0, 6.0))], -0.38)
    add_convex(gs, ledge)
    trunk = [(0.0, 3.0, 0.0), (0.3, 7.0, 0.0), (1.4, 13.0, 0.3), (3.0, 19.5, 0.0), (5.2, 26.0, -0.3)]
    cv = catmull(trunk, 3)
    sweep(gb, cv, taper(len(cv), 3.0, 1.9, 0.8, flare=1.6, flare_k=11.0), 10, mod=grain(4, 0.18, 3.0))
    roots = [([(-1.5, 4.2, 1.4), (-4.2, 4.6, 2.6), (-7.0, 3.6, 3.4), (-9.6, 1.6, 3.8), (-11.6, -0.6, 4.2)], 1.5),
             ([(-1.5, 4.2, -1.4), (-4.4, 4.7, -2.6), (-7.2, 3.8, -3.6), (-9.0, 1.8, -4.6), (-10.4, -0.5, -5.4)], 1.45),
             ([(-1.6, 4.0, 0.2), (-4.8, 4.9, 0.4), (-8.0, 4.0, -0.3), (-11.0, 2.2, 0.0), (-13.4, -0.4, 0.1)], 1.3),
             ([(-1.0, 4.0, 2.2), (-2.6, 4.6, 4.4), (-3.8, 3.4, 6.0), (-4.4, 1.0, 7.0), (-4.8, -0.6, 7.6)], 1.1),
             ([(-1.0, 4.0, -2.2), (-2.6, 4.5, -4.4), (-3.8, 3.2, -6.0), (-4.4, 0.8, -6.9)], 1.05),
             ([(1.8, 4.2, 1.6), (3.4, 4.0, 3.0), (4.6, 2.4, 4.6), (5.0, 0.4, 5.6)], 0.95),
             ([(1.8, 4.2, -1.6), (3.6, 4.1, -3.0), (5.0, 2.6, -4.0), (5.8, 0.4, -4.6)], 0.9),
             ([(2.0, 4.4, 0.0), (4.0, 4.0, 0.2), (6.0, 2.6, -0.3), (7.4, 0.2, 0.0)], 0.8)]
    for pts, r in roots:
        limb(gb, pts, r, 0.22, sides=5, per=2)
    fork = trunk[-1]
    arms = [([(3.6, 22.0, 0.2), (9.0, 24.0, 1.5), (16.0, 23.0, 2.6), (23.0, 19.5, 3.4), (30.0, 14.5, 3.6)], 1.7, 0.3),          # the lower arm sagging over the drop
            ([fork, (9.0, 30.0, -1.0), (14.5, 35.5, -2.4), (20.0, 37.0, -3.4), (25.5, 35.0, -4.0)], 1.5, 0.25),                 # the upper arm
            ([(2.4, 15.0, 0.4), (8.0, 16.4, 2.2), (14.0, 15.0, 4.6), (19.0, 11.0, 6.2)], 1.2, 0.22),                             # a low lee arm
            ([(8.5, 28.0, 0.6), (13.0, 30.0, 4.0), (18.0, 29.0, 7.4), (22.0, 25.5, 9.4)], 1.0, 0.2)]                             # a side arm swinging to +z
    for k, r0, r1 in arms:
        limb(gb, k, r0, r1, sides=7, per=3, mod=grain(3, 0.14, 2.0))
        _sprays(gl, k, rng, fracs=(0.5, 0.68, 0.84, 1.0), n=6, L=8.6, w=1.45, th=0.42, droop=0.42, spread=1.25, prof=(0.6, 1.0, 0.7), rows=2)
        p2, _ = spine_point(k, 1.0, per=2)
        for j in range(2):
            blade(gl, p2, unit(rng.uniform(-0.5, 0.5), -1.05), 6.5, 1.0, 0.3, bend=(2.4, -0.4, rng.uniform(-0.4, 0.4)), prof=(0.6, 1.0, 0.7))
    limb(gb, [fork, (5.6, 32.0, 0.5), (4.8, 39.0, 0.2), (3.6, 45.5, 0.0), (3.0, 47.0, 0.1)], 1.3, 0.1, sides=6, per=2, mod=grain(3, 0.16, -2.0))        # the snapped leader
    limb(gb, [(2.4, 20.0, -0.4), (0.0, 24.0, -1.2), (-2.6, 27.0, -1.0), (-4.6, 31.0, -0.4)], 0.55, 0.08, sides=5, per=2)                                # windward antlers
    limb(gb, [(3.0, 23.0, 0.3), (0.2, 27.5, 1.4), (-1.6, 32.0, 1.6), (-2.2, 36.0, 1.2)], 0.5, 0.07, sides=5, per=2)
    limb(gb, [(1.4, 12.5, -0.4), (-1.6, 14.0, -1.4), (-3.4, 15.2, -1.6)], 0.5, 0.12, sides=5, per=1)
    limb(gb, [(1.6, 15.5, 0.4), (-1.4, 17.5, 1.2), (-3.0, 18.6, 1.4)], 0.45, 0.12, sides=5, per=1)
    # a living sprig on the snapped leader's lee side
    k = [(4.6, 36.0, 0.2), (7.0, 38.0, 0.5), (10.0, 37.4, 0.6)]
    limb(gb, k, 0.4, 0.12, sides=5, per=2)
    _sprays(gl, k, rng, fracs=(0.6, 1.0), n=6, L=6.5, w=1.2, th=0.4, droop=0.4, spread=1.1, prof=(0.6, 1.0, 0.7), rows=1)
    return P


# ======================================================================================================================
# ROCKS AND PATHS
# ======================================================================================================================
def pl(n, p):
    """The half-space with outward normal n whose boundary passes through point p."""
    n = vnorm(n)
    return (n, vdot(n, p))


def box_pl(x0, x1, y0, y1, z0, z1):
    return [((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)]


def xform(planes, rz=0.0, ry=0.0, t=(0.0, 0.0, 0.0)):
    """Rotates the solid bounded by the planes about z by rz (a NEGATIVE angle leans the top toward +X), then about y by ry (yaw), then moves it by t."""
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


def ground_clip(planes, y):
    return planes + [((0.0, -1.0, 0.0), -y)]


def boulder_planes(rx, ry, rz, k, rng, jitter=0.12, up_bias=0.0):
    """Tangent planes of an ellipsoid (radii rx, ry, rz) in k jittered directions: a faceted boulder, the ground clip left to the caller."""
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(k):
        yv = 1 - 2 * (i + 0.5) / k
        r = math.sqrt(max(0.0, 1 - yv * yv))
        a = ga * i + rng.uniform(-0.25, 0.25)
        n = vnorm((math.cos(a) * r + rng.uniform(-0.12, 0.12), yv + rng.uniform(-0.1, 0.1) + up_bias, math.sin(a) * r + rng.uniform(-0.12, 0.12)))
        h = math.sqrt((rx * n[0]) ** 2 + (ry * n[1]) ** 2 + (rz * n[2]) ** 2)
        out.append((n, h * (1 + rng.uniform(-jitter, jitter))))
    return out


def prism_planes(cx, cz, y0, y1, radii, rot=0.0, bevel=0.15):
    """A convex polygon prism: one side plane per entry of radii (the distance of that side from the centre), a 45-degree bevel under the top edge."""
    n = len(radii)
    out = [((0, 1, 0), y1), ((0, -1, 0), -y0)]
    for k, r in enumerate(radii):
        a = rot + TAU * k / n
        c, s = math.cos(a), math.sin(a)
        out.append(((c, 0.0, s), c * cx + s * cz + r))
        k1 = 0.70710678
        out.append(((c * k1, k1, s * k1), (c * cx + s * cz + r - bevel) * k1 + y1 * k1))
    return out


def moss_pick(P, thr=0.9):
    gm = P.geo("Moss")
    return lambda n: gm if n[1] > thr else None


def seams(P, planes, specs, inflate_by=0.08, suffix="Bronze"):
    """Bronze seams: for each (normal, offset, thickness, along, lo, hi) the part of the rock (its planes pushed out by inflate_by) between two parallel planes
    and cut off along the direction `along` between lo and hi, so each seam is a raised band that starts and ends inside the rock's skin, not a hoop."""
    gb = P.geo(suffix)
    base = [(n, d) for (n, d) in planes if n[1] > -0.95]
    for i, (n, d0, t, along, lo, hi) in enumerate(specs):
        big = inflate(base, inflate_by + 0.012 * i)       # each seam stands a little differently proud, so crossing seams never share a face plane
        n = vnorm(n)
        al = vnorm(vsub(along, vmul(n, vdot(along, n))))
        add_convex(gb, big + [(n, d0 + t / 2), (vmul(n, -1.0), -d0 + t / 2), (al, hi), (vmul(al, -1.0), -lo), ((0.0, -1.0, 0.0), -0.5 - 0.25 * i)])


def slab_ring(cx, cz, w, d, rot, rng, cut=(0.12, 0.42)):
    """A convex slate-slab outline: a w x d rectangle with every corner cut off by a random amount, the edges slightly jittered, turned by rot."""
    pts = []
    corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    m = min(w, d)
    for i, (x, z) in enumerate(corners):
        px, pz = corners[i - 1]
        nx, nz = corners[(i + 1) % 4]
        c1, c2 = rng.uniform(*cut) * m, rng.uniform(*cut) * m
        a1 = (x + (px - x) / max(1e-6, math.hypot(px - x, pz - z)) * c1, z + (pz - z) / max(1e-6, math.hypot(px - x, pz - z)) * c1)
        a2 = (x + (nx - x) / max(1e-6, math.hypot(nx - x, nz - z)) * c2, z + (nz - z) / max(1e-6, math.hypot(nx - x, nz - z)) * c2)
        pts += [a1, a2]
    cs, sn = math.cos(rot), math.sin(rot)
    return [(cx + x * cs + z * sn + rng.uniform(-0.04, 0.04), cz - x * sn + z * cs + rng.uniform(-0.04, 0.04)) for (x, z) in pts]


def crag_tail(variant=0):
    """The crag and tail: a blunt dark crag stands to the wind (the windward face steep and a little overhung, notched into three strata), its crest a flat
    step, and from the crest a long smooth ramp of scoured slate runs 10 studs downwind, narrowing to a tongue that steps down in two flat ledges; a lower
    shoulder of broken slate and a ledge at the windward foot. Moss on the up-facing faces. 16 long, 5 high."""
    P = Piece()
    rng = random.Random(610)
    gs = P.geo("Slate")
    pick = moss_pick(P)
    body = ground_clip([pl((-0.97, 0.08, 0.15), (-3.0, 1.0, 0)), pl((-0.55, 0.8, -0.15), (-2.6, 3.6, 0)), pl((0.05, 1, 0.03), (0, 4.7, 0)), pl((0.42, 0.91, 0.05), (1.0, 4.5, 0)),
                        pl((0.1, 0, -1), (0, 0, -2.4)), pl((-0.4, 0.3, -0.85), (-2, 2, -2.0)), pl((-0.05, 0, 1), (0, 0, 2.5)), pl((-0.5, 0.35, 0.8), (-2, 2.5, 2.0)),
                        pl((0.18, 0, -0.98), (3, 0, -1.7)), pl((0.2, 0, 0.98), (3.2, 0, 1.8)), pl((1, 0.25, 0), (9.8, 0.2, 0)), pl((-0.3, -0.2, -0.9), (-1, 0, -2.3)),
                        pl((0.2, 0.55, -0.8), (0.0, 3.4, -2.0)), pl((-0.1, 0.6, 0.8), (0.5, 3.2, 2.1)), pl((-0.8, 0.45, 0.35), (-2.9, 2.8, 0.9)), pl((0.55, 0.78, 0.3), (2.2, 3.6, 0.8)),
                        pl((0.1, 0.55, -0.82), (2.5, 2.2, -1.5))], -0.5)
    add_convex(gs, body, pick)
    shoulder = ground_clip(box_pl(-4.6, 0.6, -2, 2.3, -4.4, -1.0) + [pl((-0.6, 0.8, 0.0), (-3.2, 2.0, 0)), pl((0.3, 0.9, -0.3), (0.0, 2.2, -2.8)), pl((-0.8, 0.0, -0.6), (-4.6, 0, -3.4)),
                                                                      pl((0.7, 0.0, -0.7), (0.4, 0, -4.2)), pl((-0.3, 0.7, 0.6), (-1.6, 2.0, -1.3))], -0.45)
    add_convex(gs, shoulder, pick)
    tongue = ground_clip(box_pl(5.0, 12.4, -2, 0.9, -1.1, 1.3) + [pl((0.2, 0.9, 0.3), (5.0, 0.9, 0)), pl((1, 0.18, 0.2), (12.4, 0.2, 0)), pl((0.3, 0.0, 0.95), (9.0, 0, 1.1)),
                                                                   pl((0.35, 0.0, -0.9), (9.0, 0, -0.7)), pl((0.0, 1.0, 0.0), (0, 0.9, 0))], -0.55)
    add_convex(gs, tongue, pick)
    step2 = ground_clip(box_pl(9.0, 15.4, -2, 0.42, -0.8, 0.9) + [pl((1, 0.2, 0.25), (15.4, 0.1, 0)), pl((0.2, 0.0, 0.95), (12.0, 0, 0.8))], -0.6)
    add_convex(gs, step2, pick)
    ledge = ground_clip(box_pl(-4.2, -2.2, -2, 1.3, 0.2, 3.6) + [pl((-0.9, 0.3, 0.2), (-4.2, 0.9, 0)), pl((0.3, 0.9, 0.2), (-3.0, 1.3, 0)), pl((-0.3, 0.0, 0.95), (-3, 0, 3.6))], -0.52)
    add_convex(gs, ledge, pick)
    chip = ground_clip(xform(box_pl(-0.7, 0.8, -1, 0.7, -0.5, 0.6) + [pl((0.3, 0.9, 0.2), (0, 0.7, 0))], 0.0, 0.5, (3.8, 0, 2.2)), -0.4)
    add_convex(gs, chip, pick)
    return P


def slate_slab():
    """The ramp slab: a great slate plank 9.6 long, 1 thick and 4.6 wide that has slid and come to rest slanting down toward the lee (its windward end 5.5 high
    on a boulder, its lee end sunk in the ground), a small rock under its middle; a flat scoured apron runs downwind from its foot under a scatter of broken
    plates, like pages blown off a stack. Moss on the flat up-facing faces."""
    P = Piece()
    rng = random.Random(620)
    gs = P.geo("Slate")
    pick = moss_pick(P)
    plank = box_pl(-4.8, 4.8, -0.5, 0.5, -2.3, 2.3) + [pl((0.7, 0.0, 0.7), (4.3, 0, 1.9)), pl((0.7, 0.0, -0.7), (4.6, 0, -1.6)), pl((-0.7, 0.0, 0.7), (-4.3, 0, 2.0)),
                                                       pl((-0.7, 0.0, -0.7), (-4.5, 0, -1.8)), pl((-0.25, 0.9, 0.15), (-3.8, 0.5, 0)), pl((0.3, 0.9, -0.2), (2.0, 0.5, -1.2)),
                                                       pl((0.0, -0.4, 0.9), (0, -0.5, 2.3)), pl((0.9, -0.3, 0.0), (4.8, -0.5, 0))]
    plank = ground_clip(xform(plank, -0.5, 0.12, (-0.4, 3.2, 0.0)), -0.45)
    add_convex(gs, plank, pick)
    prop = ground_clip(xform(boulder_planes(2.2, 2.7, 2.0, 15, rng, 0.14), 0.0, 0.3, (-3.7, 2.1, 0.2)), -0.4)
    add_convex(gs, prop, pick)
    prop2 = ground_clip(xform(boulder_planes(1.2, 1.3, 1.3, 9, rng, 0.14), 0.0, 0.8, (0.8, 1.2, 0.4)), -0.37)
    add_convex(gs, prop2, pick)
    apron = ground_clip(box_pl(4.8, 13.0, -2, 0.16, -2.2, 2.0) + [pl((1, 0.1, 0.3), (13.0, 0.0, 0)), pl((0.3, 0.0, 0.95), (9.0, 0, 1.9)), pl((0.25, 0.0, -0.95), (9.0, 0, -1.9)),
                                                                   pl((-0.4, 0.0, 0.9), (4.8, 0, 2.0)), pl((0.1, 0.9, 0.2), (8, 0.16, 0))], -0.38)
    add_convex(gs, apron, pick)
    for (x, z, w, d, h, yaw, tilt) in ((7.2, -1.2, 2.6, 2.0, 0.55, 0.25, -0.12), (9.7, 0.9, 2.0, 1.6, 0.4, -0.3, -0.1), (11.4, -0.5, 1.5, 1.2, 0.3, 0.5, -0.08), (8.2, 1.5, 1.4, 1.1, 0.3, -0.6, -0.1)):
        pn = ground_clip(xform(box_pl(-w / 2, w / 2, -1.0, h, -d / 2, d / 2) + [pl((0.2, 0.9, 0.2), (0, h, 0))], tilt, yaw, (x, 0.0, z)), -0.4 + 0.02 * x)
        add_convex(gs, pn, pick)
    return P


def strata_stack():
    """The strata stack: eight flat slabs of slate piled up like a tower of plates the gale has half pushed over: each slab wider across the wind than the one
    below is long, and pushed 0.6 to 0.9 further downwind, so the pile leans about 35 degrees to +X with a deep overhang on the lee side and a bare step
    windward; two chips have slid off its foot. Moss on the up-facing faces."""
    P = Piece()
    rng = random.Random(631)
    gs = P.geo("Slate")
    pick = moss_pick(P)
    y = -0.5
    sh = 0.0
    spec = [(3.0, 0.9), (2.6, 0.7), (2.5, 0.95), (2.2, 0.55), (2.1, 0.8), (1.8, 0.6), (1.5, 0.85), (1.15, 0.55)]
    for i, (r, th) in enumerate(spec):
        sh += 0.0 if i == 0 else rng.uniform(0.6, 0.95)
        radii = [r * rng.uniform(0.8, 1.1) * (1.35 if math.cos(TAU * k / 7) > 0.3 else 0.85) for k in range(7)]        # long across the wind (z), short along it (x)
        pp = prism_planes(sh, rng.uniform(-0.3, 0.3), y, y + th, radii, rot=0.1 * i, bevel=0.15)
        add_convex(gs, pp, pick)
        y += th - 0.04
    for (x, z, w, d, h, yaw) in ((5.6, 0.4, 1.7, 1.3, 0.45, 0.3), (6.5, -1.6, 1.2, 1.0, 0.35, -0.5)):
        pn = ground_clip(xform(box_pl(-w / 2, w / 2, -1.0, h, -d / 2, d / 2) + [pl((0.2, 0.9, 0.2), (0, h, 0))], -0.1, yaw, (x, 0.0, z)), -0.4 + 0.02 * x)
        add_convex(gs, pn, pick)
    return P


def vein_boulder(variant):
    """The bronze-veined rocks. A: a leaning monolith 7.5 high, an angular egg of dark slate tilted 16 degrees downwind with four muted-bronze seams of different
    thickness running slantwise across it, each ending inside the rock, and a small boulder at its foot. B: a boulder cloven through, the two halves leaning
    apart in a V that opens upward over a bronze core, the lee half the larger, a small boulder against its lee foot; moss on the cap of the windward half."""
    P = Piece()
    rng = random.Random(640 + variant)
    gs = P.geo("Slate")
    if variant == 0:
        pl_ = ground_clip(boulder_planes(2.1, 4.3, 2.0, 21, rng, 0.1), -0.5)
        pl_ = xform(pl_, -0.4, 0.4, (0.6, 3.6, 0.0))
        pl_ = ground_clip(pl_, -0.5)
        add_convex(gs, pl_)
        foot = ground_clip(xform(boulder_planes(3.3, 1.5, 2.7, 13, rng, 0.12), 0.0, 0.5, (0.9, 1.1, 0.1)), -0.45)         # a broad low foot the monolith stands in
        add_convex(gs, foot)
        ledge = ground_clip(xform(box_pl(-0.2, 3.6, -1, 0.8, -1.5, 1.5) + [pl((0.9, 0.2, 0.5), (3.6, 0.2, 1.2)), pl((0.9, 0.2, -0.5), (3.6, 0.2, -1.2)), pl((0.3, 0.9, 0.1), (1.5, 0.8, 0.0)),
                                                                          pl((0.0, -0.4, 0.9), (0, -1.0, 1.5))], -0.12, 0.4, (1.2, 3.6, 0.0)), 1.9)      # a shelf of rock thrust out downwind, at 1.9 and up
        add_convex(gs, ledge)
        n0 = vnorm((0.45, 0.35, 0.82))
        al = (0.82, 0.0, -0.45)
        seams(P, pl_, [(vnorm(vadd(n0, (0.06, 0.1, 0.0))), 0.2, 0.12, al, -3.4, 2.6), (n0, 1.1, 0.34, al, -2.4, 3.6), (vnorm(vadd(n0, (-0.08, 0.14, 0.05))), 1.9, 0.18, al, -3.6, 1.2),
                       (vnorm(vadd(n0, (0.1, -0.05, 0.0))), 2.8, 0.14, al, -1.4, 3.8)])
        pk = ground_clip(xform(boulder_planes(1.5, 1.0, 1.3, 9, rng, 0.12), 0.0, 0.2, (3.0, 0.7, -1.0)), -0.4)
        add_convex(gs, pk)
    else:
        gm = P.geo("Moss")
        base = boulder_planes(3.1, 3.3, 2.7, 21, rng, 0.1)
        base = xform(base, 0.0, 0.3, (0.0, 2.8, 0.0))
        g_ = 0.3
        cut = vnorm((1.0, 0.0, 0.18))
        hl = base + [(cut, -g_)]                       # the windward half: everything with cut . p <= -g
        hr = base + [(vmul(cut, -1.0), -g_)]           # the lee half
        hl = ground_clip(xform(hl, 0.15, 0.0, (0.0, 0.0, 0.0)), -0.5)
        hr = ground_clip(xform(hr, -0.12, 0.0, (0.0, 0.0, 0.0)), -0.55)
        add_convex(gs, hl, lambda n: gm if n[1] > 0.9 else None)
        add_convex(gs, hr)
        # the bronze core: the wedge between the two cut faces (turned with their halves), inside the boulder's skin, up to 2.4
        na, da = xform([(cut, -g_)], 0.15, 0.0, (0.0, 0.0, 0.0))[0]
        nb, db = xform([(vmul(cut, -1.0), -g_)], -0.12, 0.0, (0.0, 0.0, 0.0))[0]
        gb = P.geo("Bronze")
        add_convex(gb, inflate(ground_clip(base, -0.2), 0.05) + [(vmul(na, -1.0), -da + 0.03), (vmul(nb, -1.0), -db + 0.03), ((0.0, 1.0, 0.0), 2.4)])
        pk = ground_clip(xform(boulder_planes(1.4, 1.0, 1.2, 9, rng, 0.12), 0.0, 0.2, (4.0, 0.6, 1.0)), -0.4)
        add_convex(gs, pk)
    return P


def windgate():
    """The windgate: two uneven slate pillars (the lee one broken lower) carry a long lintel slab that has slipped and tilts down toward the lee; the opening,
    3.4 wide and 6.4 high, runs along z (a path may pass through, a player walks under the lintel); a flat apron of slate runs downwind from it under a spill of broken plates. Moss on the lintel."""
    P = Piece()
    rng = random.Random(650)
    gs = P.geo("Slate")
    pick = moss_pick(P)
    pa = ground_clip(xform(box_pl(-1.5, 1.5, -1, 7.6, -1.7, 1.7) + [pl((-0.4, 0.9, 0.1), (-1.0, 7.6, 0)), pl((0.5, 0.8, 0.2), (1.2, 7.3, 0)), pl((0.0, 0.0, -1.0), (0, 0, -1.6)),
                                                                   pl((-0.9, 0.0, -0.45), (-1.5, 0, -1.2)), pl((-0.7, 0.3, 0.6), (-1.5, 1.0, 1.7)), pl((0.2, 0.2, 0.95), (0.6, 3.5, 1.7)),
                                                                   pl((-0.8, 0.2, -0.5), (-1.5, 4.8, -1.0))], -0.06, 0.1, (-3.1, 0.0, 0.0)), -0.5)
    add_convex(gs, pa, pick)
    pb = ground_clip(xform(box_pl(-1.4, 1.4, -1, 6.4, -1.5, 1.6) + [pl((0.3, 0.9, 0.2), (0.5, 6.4, 0)), pl((-0.5, 0.8, -0.2), (-1.0, 6.2, 0)), pl((0.9, 0.0, 0.4), (1.4, 0, 1.2)),
                                                                   pl((0.0, 0.5, -0.85), (0, 5.4, -1.5)), pl((0.6, 0.35, -0.7), (1.3, 1.8, -1.3)), pl((-0.2, 0.7, 0.7), (0.2, 5.2, 1.4))],
                           0.04, -0.15, (3.2, 0.0, 0.1)), -0.46)
    add_convex(gs, pb, pick)
    lt = xform(box_pl(-5.3, 5.3, -0.8, 0.8, -1.9, 1.9) + [pl((0.15, 0.9, 0.3), (3.5, 0.8, 1.2)), pl((-0.9, 0.0, 0.1), (-5.3, 0.0, 0.0)), pl((0.9, 0.15, -0.1), (5.3, 0.0, 0.0)),
                                                         pl((0.0, 0.3, 0.95), (0, 0.4, 1.9)), pl((-0.3, 0.9, -0.2), (-3.5, 0.8, -0.6)), pl((0.0, -0.35, -0.94), (0, -0.4, -1.9)),
                                                         pl((0.35, 0.9, -0.1), (1.0, 0.8, 0.0))], -0.07, 0.04, (0.1, 7.35, 0.0))
    add_convex(gs, lt, pick)
    apron = ground_clip(box_pl(5.0, 13.0, -2, 0.16, -2.4, 2.4) + [pl((1, 0.1, 0.2), (13.0, 0.0, 0)), pl((0.3, 0.0, 0.95), (9.0, 0, 2.3)), pl((0.3, 0.0, -0.95), (9.0, 0, -2.3)),
                                                                   pl((-0.5, 0.0, 0.85), (5.0, 0, 2.2))], -0.36)
    add_convex(gs, apron, pick)
    for (x, z, w, d, h, yaw) in ((7.4, -1.6, 2.2, 1.8, 0.8, 0.4), (9.4, 0.8, 1.8, 1.5, 0.6, -0.3), (8.2, 1.9, 1.3, 1.1, 0.5, 0.6), (11.0, -0.4, 1.4, 1.1, 0.4, 0.2)):
        pn = ground_clip(xform(box_pl(-w / 2, w / 2, -1.0, h, -d / 2, d / 2) + [pl((0.25, 0.9, 0.2), (0, h, 0))], -0.1, yaw, (x, 0.0, z)), -0.4 + 0.015 * x)
        add_convex(gs, pn, pick)
    return P


def fin():
    """The comb of fins: five wind-chiselled slate blades in a row along the wind, each leaning 17 degrees downwind, the tallest 7.5 at the windward end and
    each next one smaller (to 2.5), so the group is a sawtooth ridge stepping down to +X; every blade has a steep clean windward edge, a long slope on its lee
    side, a serrated crest, thin at the top and thick at the foot, the faces broken into plates; two broken plates at the lee foot. Bare of moss."""
    P = Piece()
    rng = random.Random(660)
    gs = P.geo("Slate")
    for (sx, sz, sc, yaw, lean) in ((-2.6, 0.3, 1.0, 0.06, -0.30), (-0.2, -0.5, 0.78, -0.12, -0.26), (1.9, 0.4, 0.6, 0.1, -0.24), (3.7, -0.3, 0.46, -0.08, -0.2), (5.2, 0.3, 0.34, 0.14, -0.18)):
        H = 9.5 * sc
        fp = [pl((-8.5 * sc, 1.0, 0.0), (-1.6 * sc, 0.0, 0)), pl((0.928, 0.371, 0.0), (3.2 * sc, 0.0, 0)), pl((0.0, 0.06, 0.99), (0, 0, 0.9 * sc)), pl((0.0, 0.06, -0.99), (0, 0, -0.95 * sc)),
              pl((-0.5, 0.85, 0.15), (-0.9 * sc, H * 0.93, 0)), pl((0.55, 0.8, -0.2), (-0.2 * sc, H * 0.97, 0)), pl((0.1, 0.9, 0.35), (-0.5 * sc, H * 0.99, 0.1)),
              pl((-0.1, 0.07, -0.99), (0.0, H * 0.45, -0.8 * sc)), pl((0.2, 0.07, 0.98), (0.0, H * 0.3, 0.8 * sc)),
              pl((0.5, 0.86, 0.0), (0.7 * sc, H * 0.82, 0)), pl((0.3, 0.07, -0.95), (0.5 * sc, H * 0.6, -0.7 * sc)), pl((-0.7, 0.07, 0.7), (-1.2 * sc, H * 0.2, 0.6 * sc)),
              pl((0.9, 0.25, 0.35), (1.6 * sc, H * 0.35, 0.4 * sc)), pl((-0.65, 0.76, -0.1), (-1.1 * sc, H * 0.7, 0)),
              pl((0.35, 0.07, 0.93), (0.3 * sc, H * 0.5, 0.7 * sc)), pl((-0.4, 0.07, -0.92), (-0.3 * sc, H * 0.55, -0.6 * sc))]
        add_convex(gs, ground_clip(xform(fp, lean, yaw, (sx, 0.0, sz)), -0.5 + 0.03 * sc), None)
    for (x, z, w, d, h, yaw) in ((6.3, 0.2, 1.8, 1.4, 0.5, 0.3), (7.6, -0.6, 1.4, 1.0, 0.35, -0.4)):
        pn = ground_clip(xform(box_pl(-w / 2, w / 2, -1.0, h, -d / 2, d / 2) + [pl((0.2, 0.9, 0.2), (0, h, 0))], -0.1, yaw, (x, 0.0, z)), -0.4 + 0.02 * x)
        add_convex(gs, pn, None)
    return P


def scree(variant):
    """A scree fan on a flat bed of gravel: 12 angular slate chips, big and close at the windward end and smaller and further apart downwind, each chip lying
    tilted with its long side along the wind. A: a fan 9 long, 6 wide. B: a narrow drift 11 long, 3.6 wide."""
    P = Piece()
    rng = random.Random(670 + variant)
    gs = P.geo("Scree")
    if variant == 0:
        bed = irregular_ring(0.1, 0.0, 4.4, 2.9, 11, rng, jitter=0.14)
    else:
        bed = irregular_ring(0.0, 0.0, 5.4, 1.7, 12, rng, jitter=0.12)
    slab(gs, bed, -0.2, 0.05, bev=0.02)
    # standing shards at the windward end, tallest first, leaning downwind: the fan's back
    for (x, z, H, w, yw) in ((-3.9, 0.3, 2.3, 0.9, 0.2), (-3.1, -0.9, 1.7, 0.8, -0.3), (-2.5, 0.9, 1.3, 0.7, 0.4), (-1.8, -0.2, 0.9, 0.6, 0.0)) if variant == 0 else \
            ((-4.6, 0.2, 2.0, 0.8, 0.1), (-3.8, -0.5, 1.4, 0.7, -0.2), (-3.0, 0.4, 1.0, 0.6, 0.3)):
        sh = box_pl(-w / 2, w / 2, -1.0, H, -0.28, 0.28) + [pl((0.4, 0.9, 0.2), (0.2, H, 0.0)), pl((-0.5, 0.8, -0.1), (-0.3, H * 0.95, 0.0))]
        add_convex(gs, ground_clip(xform(sh, -0.3, yw, (x, 0.0, z)), -0.1), None)
    n = 12
    for i in range(n):
        f = i / (n - 1)
        if variant == 0:
            x = -3.4 + 7.0 * f ** 0.8 + rng.uniform(-0.4, 0.4)
            z = rng.uniform(-1, 1) * (0.5 + 2.0 * f)
        else:
            x = -4.6 + 9.2 * f + rng.uniform(-0.4, 0.4)
            z = rng.uniform(-1, 1) * (1.3 - 0.5 * f)
        sc = 1.0 - 0.55 * f
        L = rng.uniform(0.9, 1.5) * sc * 1.3
        W = rng.uniform(0.55, 0.95) * sc
        H = rng.uniform(0.2, 0.42) * sc + 0.1
        yaw = rng.uniform(-0.5, 0.5)
        tilt = rng.uniform(-0.25, 0.1)
        ch = box_pl(-L / 2, L / 2, -1.0, H, -W / 2, W / 2) + [pl((rng.uniform(-0.3, 0.3), 0.9, rng.uniform(-0.3, 0.3)), (0.0, H, 0.0))]
        add_convex(gs, ground_clip(xform(ch, tilt, yaw, (x, 0.0, z)), -0.12 - 0.012 * i), None)
    return P


def steps(variant):
    """Stepping slabs of dark slate, flat and walkable: every top is exactly y = 0.20 (the path sits 0.3 over the terrain); a slab is a convex slate plate
    (a rectangle with its corners knocked off) with a small bevel, sunk 0.35. A: four big slabs in a line along z, 4.2 apart (a straight way). B: five
    smaller slabs on a slow curve (a winding way). Set the piece's z axis along the path."""
    P = Piece()
    rng = random.Random(680 + variant)
    g = P.geo("SlateStep")
    if variant == 0:
        spec = [(0.2, -6.4, 3.1, 2.6), (-0.5, -2.1, 3.3, 2.7), (0.4, 2.1, 3.2, 2.6), (-0.3, 6.3, 3.0, 2.7)]
    else:
        spec = [(-1.8, -7.2, 2.4, 2.1), (-0.7, -3.7, 2.5, 2.2), (0.9, -0.4, 2.6, 2.2), (2.7, 2.8, 2.4, 2.1), (4.3, 6.2, 2.3, 2.1)]
    for i, (cx, cz, w, d) in enumerate(spec):
        ring = slab_ring(cx, cz, w, d, rng.uniform(-0.5, 0.5) + (0.3 * i if variant else 0.0), rng)
        slab(g, ring, -0.35, 0.20, bev=0.04)
    # a buried tie bar under each gap: it sits below the terrain and joins the slabs into one mesh (one MeshPart for the set)
    for i in range(len(spec) - 1):
        (x0, z0, _, _), (x1, z1, _, _) = spec[i], spec[i + 1]
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
        ln = math.hypot(x1 - x0, z1 - z0) + 1.0
        yaw = math.atan2(x1 - x0, z1 - z0)
        bar = xform(box_pl(-0.18, 0.18, -0.5 - 0.01 * i, -0.30 + 0.01 * i, -ln / 2, ln / 2), 0.0, yaw, (mx, 0.0, mz))
        add_convex(g, bar)
    return P


def cobble():
    """A worn cobble strip 2.8 wide and 8.6 long along z: 18 irregular six-sided cobbles set close, tops within 0.03 of y = 0.20, sunk 0.3."""
    P = Piece()
    rng = random.Random(690)
    g = P.geo("Cobble")
    slab(g, slab_ring(0.0, 0.2, 2.3, 8.2, 0.0, rng, cut=(0.05, 0.2)), -0.42, -0.04, bev=0.02)      # the packed bed the cobbles sit in (ties them into one piece)
    rows = 6
    k = 0
    for r in range(rows):
        z = -4.0 + r * 1.62 + rng.uniform(-0.1, 0.1)
        cols = 3 if r % 2 == 0 else 2
        for c in range(cols):
            x = (c - (cols - 1) / 2) * 1.0 + rng.uniform(-0.08, 0.08)
            ring = irregular_ring(x, z, 0.5 if cols == 3 else 0.58, 0.68, 6, rng, jitter=0.09, rot=rng.uniform(0, 1))
            top = 0.20 + rng.uniform(-0.025, 0.025)
            n = len(ring)
            ci = [g.vert((px, -0.3 - 0.01 * (k % 3), pz)) for (px, pz) in ring]
            ti = [g.vert((px, top, pz)) for (px, pz) in ring]
            start = len(g.f)
            for i in range(n):
                j = (i + 1) % n
                g.face(ci[i], ti[i], ti[j], ci[j])
            for i in range(1, n - 1):
                g.face(ti[0], ti[i + 1], ti[i])
                g.face(ci[0], ci[i], ci[i + 1])
            K._orient_solid(g, start)
            k += 1
    return P


def plank_walk():
    """A plank-and-peg walk 3.2 wide and 8.4 long along z: eight weathered planks laid across two log stringers, each pinned at both ends by a bronze peg;
    every plank top within 0.02 of y = 0.20."""
    P = Piece()
    rng = random.Random(700)
    gp = P.geo("Plank")
    gb = P.geo("Bronze")
    for i in range(8):
        z0 = -4.2 + i * 1.07
        top = 0.20 + rng.uniform(-0.012, 0.012)
        w = 3.1 + rng.uniform(-0.08, 0.08)
        K.box(gp, -w / 2, w / 2, 0.02, top, z0, z0 + 0.92, "TBNESW")
        for sx in (-1, 1):
            px = sx * (w / 2 - 0.28)
            pz = z0 + 0.46
            ring = [(px + 0.11 * math.cos(a), pz + 0.11 * math.sin(a)) for a in (0.4, 0.4 + math.pi / 2, 0.4 + math.pi, 0.4 + 1.5 * math.pi)]
            K.prism(gb, ring, top - 0.05, top + 0.1, "T")
    for sx in (-1.05, 1.05):
        K.box(gp, sx - 0.2, sx + 0.2, -0.35, 0.05, -4.4, 4.4, "TBNESW")
    return P


# ======================================================================================================================
# PLANTS
# ======================================================================================================================
def star(g, c, axis, n, r, w=None, th=0.05, phase=0.0, lift=0.0):
    """An open star of n narrow petals radiating from c in the plane perpendicular to `axis`, each petal a 4-triangle spike (a flat tetrahedron) of length r
    and width w, tipped up by `lift` along the axis. Nothing is closed in the middle: the petals share only their roots."""
    w = w if w is not None else r * 0.38
    a = vnorm(axis)
    u = vnorm(vcross(a, (0.0, 0.0, 1.0) if abs(a[2]) < 0.9 else (1.0, 0.0, 0.0)))
    v = vcross(a, u)
    for i in range(n):
        ang = phase + TAU * i / n
        d = vadd(vadd(vmul(u, math.cos(ang)), vmul(v, math.sin(ang))), vmul(a, lift + (0.0 if i % 2 == 0 else 0.22)))
        blade(g, vadd(c, vmul(d, 0.04)), vnorm(d), r, w, th, up=a, prof=(1.0,), ring=3)


def tussock(g, x, z, n, rng, L=(1.6, 2.6), w=0.3, lean=0.55, yaw=0.5, ring=3):
    """n grass blades from a root at (x, z), all combed toward +X: each leans `lean` of its length downwind and its tip bends further downwind."""
    for i in range(n):
        ln = rng.uniform(*L)
        d = vnorm((lean + rng.uniform(-0.12, 0.12), 1.0, rng.uniform(-yaw, yaw) * 0.35))
        bend = (ln * rng.uniform(0.35, 0.6), -ln * 0.12, rng.uniform(-0.1, 0.1))
        blade(g, (x + rng.uniform(-0.12, 0.12), -0.1, z + rng.uniform(-0.12, 0.12)), d, ln, w * rng.uniform(0.85, 1.15), w * 0.35, bend=bend, prof=(0.85, 1.0), ring=ring)


def gale_grass(variant):
    """Gale grass. A: a patch about 5 x 5: eight tussocks of 3 blades, every blade combed hard downwind and its tip streaming. B: one tall tussock 3 x 3 whose
    fourteen blades arch 2.4 to 4.2 and all trail to +X."""
    P = Piece()
    rng = random.Random(810 + variant)
    g = P.geo("Grass")
    if variant == 0:
        slab(g, irregular_ring(0.1, 0.0, 3.0, 2.8, 9, rng, jitter=0.12), -0.1, 0.03, bev=0.02)     # the root mat the tussocks stand on
        spots = [(-1.9, -1.6), (0.3, -1.9), (1.9, -0.9), (-1.8, 0.6), (0.2, 0.3), (-0.8, 2.0), (1.6, 1.8)]
        for (x, z) in spots:
            tussock(g, x + rng.uniform(-0.2, 0.2), z + rng.uniform(-0.2, 0.2), 3, rng)
    else:
        slab(g, irregular_ring(0.0, 0.0, 0.8, 0.8, 8, rng, jitter=0.1), -0.1, 0.03, bev=0.02)
        for i in range(9):
            a = TAU * i / 9 + rng.uniform(-0.2, 0.2)
            r0 = rng.uniform(0.05, 0.5)
            ln = rng.uniform(2.4, 4.2)
            d = vnorm((0.5 + 0.18 * math.cos(a), 1.0, 0.25 * math.sin(a)))
            blade(g, (r0 * math.cos(a), -0.1, r0 * math.sin(a)), d, ln, 0.34, 0.12, bend=(ln * 0.55, -ln * 0.2, 0.2 * math.sin(a) * ln * 0.2), prof=(0.8, 1.0, 0.6), ring=3)
    return P


def sedge():
    """Sedge for the water's edge: eight narrow stems 3 to 4.4 tall bending downwind, four of them carrying a brown seed spike."""
    P = Piece()
    rng = random.Random(820)
    gr = P.geo("Reed")
    gs = P.geo("Seed")
    slab(gr, irregular_ring(0.0, 0.0, 1.15, 1.15, 8, rng, jitter=0.1), -0.2, 0.04, bev=0.02)
    for i in range(6):
        x = rng.uniform(-0.9, 0.9)
        z = rng.uniform(-0.9, 0.9)
        ln = rng.uniform(3.0, 4.4)
        d = vnorm((0.3, 1.0, rng.uniform(-0.12, 0.12)))
        bend = (ln * 0.5, -ln * 0.1, rng.uniform(-0.2, 0.2))
        pts = blade(gr, (x, -0.15, z), d, ln, 0.26, 0.09, bend=bend, prof=(0.9, 0.9, 0.5), ring=3)
        if i % 2 == 0:
            tip = pts[-2]
            tan = vnorm(vsub(pts[-1], pts[-2]))
            limb(gs, [vsub(tip, vmul(tan, 0.15)), vadd(tip, vmul(tan, 0.4)), vadd(tip, vmul(tan, 0.95))], 0.11, 0.05, sides=3, per=1)
    return P


def gorse():
    """Gorse, wind-clipped: a dense spiky mound, low on the windward side and tall on the lee side, twenty thorn-spikes bristling out of a small core and
    raked downwind, a few ochre stars where the spikes end. 4.4 long, 2.4 high."""
    P = Piece()
    rng = random.Random(830)
    g = P.geo("Gorse")
    gf = P.geo("FlowerOchre")
    loaf(g, (-1.7, 0.0, 0.0), unit(0.0, 0.3), 3.6, 0.75, flat=0.9, lumps=0.2, bend=(0.0, -0.2, 0.0), sides=7, seed=3)
    tips = []
    for i in range(14):
        x = rng.uniform(-1.5, 1.0)
        z = rng.uniform(-0.45, 0.45)
        y = 0.45 + 0.22 * (x + 1.5)
        a = rng.uniform(-1.2, 1.2)
        d = vnorm((0.55 + 0.35 * math.cos(a), 0.75, 0.7 * math.sin(a)))
        ln = rng.uniform(1.2, 1.9) * (0.75 + 0.18 * (x + 1.5))
        pts = blade(g, (x, y, z), d, ln, 0.26, 0.1, bend=(0.25, -0.1, 0.0), prof=(0.9, 0.8), ring=3)
        tips.append(pts[-1])
    for q in (2, 6, 10):
        star(gf, tips[q], (0.2, 1.0, 0.0), 5, 0.34, 0.14, 0.04, phase=q)
    return P


def heather():
    """Heather: a wiry low tuft, seven fine wands bowing downwind, each ending in a short spike of rose-brown bells."""
    P = Piece()
    rng = random.Random(840)
    g = P.geo("Heather")
    gf = P.geo("FlowerRose")
    slab(g, irregular_ring(0.05, 0.0, 0.62, 0.62, 7, rng, jitter=0.1), -0.2, 0.12, bev=0.04)
    for i in range(6):
        a = TAU * i / 6
        x, z = 0.35 * math.cos(a), 0.35 * math.sin(a)
        ln = rng.uniform(1.5, 2.3)
        d = vnorm((0.45 + 0.1 * math.cos(a), 1.0, 0.2 * math.sin(a)))
        k = [(x, -0.1, z), vadd((x, -0.1, z), vmul(d, ln * 0.5)), vadd(vadd((x, -0.1, z), vmul(d, ln * 0.85)), (ln * 0.3, 0.0, 0.0))]
        limb(g, k, 0.07, 0.035, sides=3, per=1)
        tip = k[-1]
        for (back, up_, dz) in ((0.0, 0.0, 0.0), (0.3, 0.14, 0.1)):      # three small bells hanging from the wand's last stretch, mouths down and downwind
            blade(gf, vsub(tip, (back, up_ + 0.02, 0.0)), vnorm((0.35, -0.8, dz)), 0.34, 0.3, 0.2, prof=(1.0,), ring=3)
    return P


def juniper_creeper():
    """Creeping dwarf juniper: four lumpy scale-leaf loaves of different length fanned out of one root, all trailing downwind, hugging the ground; 4.5 long."""
    P = Piece()
    rng = random.Random(850)
    g = P.geo("Juniper")
    for i, (yw, ln, R, rise) in enumerate(((0.0, 4.4, 0.8, 0.12), (0.5, 3.5, 0.7, 0.16), (-0.55, 3.2, 0.68, 0.1), (0.95, 2.4, 0.55, 0.2), (-1.0, 2.2, 0.5, 0.18))):
        loaf(g, (-0.5 + 0.1 * i, 0.15, 0.0), unit(yw, rise), ln, R, flat=0.55, lumps=0.25, bend=(0.0, -0.3, 0.0), sides=5, seed=i + 2)
    return P


def cushion():
    """A cushion plant: a low faceted dome 2.8 across, five small rose-brown stars (five narrow petals each) sitting on it, tipped downwind."""
    P = Piece()
    rng = random.Random(860)
    g = P.geo("Moss")
    gf = P.geo("FlowerRose")
    pts = [(0.0, -0.2, 0.0), (0.0, 0.2, 0.0), (0.0, 0.55, 0.0), (0.0, 0.85, 0.0)]
    sweep(g, pts, [1.4, 1.35, 0.95, 0.35], 9, mod=lambda t, a: 1.0 + 0.16 * math.cos(3 * a + 1.0) + 0.08 * math.cos(5 * a), squash=0.9, ref=(1.0, 0.0, 0.0))
    for (x, z, h) in ((-0.3, 0.1, 0.84), (0.5, -0.4, 0.66), (0.35, 0.6, 0.6), (-0.8, -0.5, 0.48), (-0.7, 0.7, 0.45)):
        star(gf, (x, h + 0.05, z), (0.25, 1.0, 0.0), 5, 0.34, 0.15, 0.04, phase=x * 3)
    return P


def stonecrop():
    """Stonecrop in a crack: four rosettes of fat pointed teal-grey leaves (eight each) sitting in a row along the crack, the leaves cupped upward."""
    P = Piece()
    rng = random.Random(870)
    g = P.geo("Crassula")
    limb(g, [(-1.9, -0.02, 0.1), (-0.4, 0.0, -0.15), (0.55, 0.0, 0.15), (2.0, -0.02, -0.05)], 0.07, 0.07, sides=3, per=2)       # the creeping stem along the crack
    for (x, z, sc) in ((-1.3, 0.1, 0.9), (-0.4, -0.15, 1.1), (0.55, 0.15, 1.0), (1.4, -0.05, 0.8)):
        for i in range(8):
            a = TAU * i / 8 + x
            d = vnorm((math.cos(a) * 0.85, 0.45, math.sin(a) * 0.85))
            blade(g, (x, 0.0, z), d, 0.85 * sc, 0.42 * sc, 0.24 * sc, prof=(1.0,), ring=3, up=(0.0, 1.0, 0.0))
    return P


def thistle():
    """A mountain thistle: a stem 3.4 tall bowed downwind, a rosette of four spined leaves at its foot, a green calyx and a crown of nine narrow rose-violet
    petals standing up and out from it."""
    P = Piece()
    rng = random.Random(880)
    g = P.geo("Reed")
    gf = P.geo("FlowerRose")
    k = [(0.0, -0.2, 0.0), (0.2, 1.2, 0.0), (0.7, 2.5, 0.0), (1.2, 3.3, 0.0)]
    limb(g, k, 0.12, 0.08, sides=4, per=2)
    for i in range(4):
        a = TAU * i / 4 + 0.4
        blade(g, (0.0, 0.0, 0.0), vnorm((math.cos(a) * 0.8 + 0.3, 0.5, math.sin(a) * 0.8)), 1.3, 0.4, 0.14, bend=(0.35, -0.3, 0.0), prof=(0.8, 1.0), ring=3)
    top = k[-1]
    sweep(g, [vsub(top, (0.0, 0.18, 0.0)), top, vadd(top, (0.05, 0.28, 0.0))], [0.13, 0.28, 0.2], 5, ref=(0.0, 0.0, 1.0))
    for i in range(9):
        a = TAU * i / 9
        d = vnorm((math.cos(a) * 0.6 + 0.15, 1.0, math.sin(a) * 0.6))
        blade(gf, vadd(top, (0.03, 0.2, 0.0)), d, 0.6, 0.14, 0.05, prof=(1.0,), ring=3)
    return P


def wind_star():
    """Wind stars, a small mountain aster: four slender stems bowed downwind with a few grass-like leaves, each stem ending in an open star of eight narrow
    teal petals facing the lee."""
    P = Piece()
    rng = random.Random(890)
    g = P.geo("Reed")
    gf = P.geo("FlowerTeal")
    slab(g, irregular_ring(0.0, -0.2, 1.1, 1.0, 8, rng, jitter=0.1), -0.2, 0.04, bev=0.02)
    for i, (x, z, h) in enumerate(((-0.6, -0.3, 2.2), (0.0, 0.4, 2.8), (0.6, -0.4, 2.0))):
        k = [(x, -0.15, z), (x + 0.15, h * 0.5, z), (x + 0.55, h, z)]
        limb(g, k, 0.06, 0.04, sides=3, per=1)
        blade(g, (x, 0.0, z), vnorm((0.5, 1.0, 0.3 * (i - 1.5))), 1.1, 0.22, 0.08, bend=(0.5, -0.2, 0.0), prof=(0.9, 1.0), ring=3)
        star(gf, vadd(k[-1], (0.0, 0.04, 0.0)), (0.55, 0.45, 0.0), 7, 0.42, 0.14, 0.04, phase=i)
    return P


def lichen(variant):
    """A crust of lichen laid on rock or ground: flat lobed pads 0.07 high, A one 5 wide with two satellites, B a long band of four overlapping pads 8 by 2.5."""
    P = Piece()
    rng = random.Random(900 + variant)
    g = P.geo("Lichen")

    cnt = [0]

    def lobed(cx, cz, R, n, y0, y1, ratio=1.0):
        y0 = y0 - 0.006 * cnt[0]
        cnt[0] += 1
        ring = []
        for k in range(n):
            a = TAU * k / n
            f = 1.0 + 0.32 * math.cos(3 * a + cx) + 0.16 * math.cos(5 * a + cz) + rng.uniform(-0.08, 0.08)
            ring.append((cx + math.cos(a) * R * f, cz + math.sin(a) * R * f * ratio))
        slab(g, ring, y0, y1, bev=0.02)
    if variant == 0:
        lobed(0.0, 0.0, 1.8, 14, -0.04, 0.07)
        lobed(1.7, 0.9, 0.8, 8, -0.04, 0.05)
        lobed(-1.5, -1.1, 0.7, 8, -0.04, 0.05)
    else:
        for (x, z, R, yy) in ((-2.9, 0.0, 1.3, 0.06), (-1.1, 0.4, 1.3, 0.075), (0.7, -0.1, 1.3, 0.06), (2.5, 0.3, 1.2, 0.07)):
            lobed(x, z, R, 10, -0.04, yy, ratio=0.8)
    return P


PLANTS = {"GaleGrassA": lambda: gale_grass(0), "GaleGrassB": lambda: gale_grass(1), "Sedge": sedge, "Gorse": gorse, "Heather": heather, "JuniperCreeper": juniper_creeper,
          "Cushion": cushion, "Stonecrop": stonecrop, "Thistle": thistle, "WindStar": wind_star, "LichenA": lambda: lichen(0), "LichenB": lambda: lichen(1)}


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
    eps of each other's plane and overlap. Plain-Python mirror of the QA's test (four sample points per triangle)."""
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
    """Rolls one shell of every z-fighting pair a few degrees about its own long axis until the QA's test finds no pair (foliage blades from one root can
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
            sh = max(a, b)
            if sh in done:
                continue
            done.add(sh)
            vs = members[sh]
            p0 = g.v[vs[0]]
            axis = vnorm(vsub(g.v[vs[-1]], p0)) if vlen(vsub(g.v[vs[-1]], p0)) > 1e-6 else (1.0, 0.0, 0.0)
            ang = (0.07 + 0.03 * it) * (1 if (sh + it) % 2 else -1)
            for i in vs:
                g.v[i] = vadd(p0, _rot(vsub(g.v[i], p0), axis, ang))
            turned += 1
    return turned


# ======================================================================================================================
# registry, collision, meta
# ======================================================================================================================
TREES = {"GaleCedarA1": lambda: gale_cedar(0), "GaleCedarA2": lambda: gale_cedar(1), "BannerPineB1": lambda: banner_pine(0), "BannerPineB2": lambda: banner_pine(1),
         "CliffJuniperC1": lambda: cliff_juniper(0), "CliffJuniperC2": lambda: cliff_juniper(1), "BronzeleafD1": lambda: bronzeleaf(0), "BronzeleafD2": lambda: bronzeleaf(1),
         "SplitSnagE1": lambda: split_snag(0), "SplitSnagE2": lambda: split_snag(1), "GiantCedar": giant_cedar}
ROCKS = {"CragTail": crag_tail, "SlateSlab": slate_slab, "StrataStack": strata_stack, "VeinBoulderA": lambda: vein_boulder(0), "VeinBoulderB": lambda: vein_boulder(1),
         "Windgate": windgate, "Fin": fin, "ScreeA": lambda: scree(0), "ScreeB": lambda: scree(1), "StepsA": lambda: steps(0), "StepsB": lambda: steps(1), "Cobble": cobble,
         "PlankWalk": plank_walk}
FAMILIES = [("Trees", TREES), ("Rocks", ROCKS), ("Plants", PLANTS)]

# where to use each piece, and the keep-out radius (studs) the placer should leave round it
USE = {
    "GaleCedarA1": ("the flagged cliff cedar: on a ridge, a terrace corner or a cliff edge, standing alone; keep 5 studs clear of other trees (the limbs stream 13 studs to +X)", 5.0),
    "GaleCedarA2": ("the lee-canopy cedar: low and wide, over a drop or against a wall; its veils reach 8 studs either side of the line to +X, keep 7 studs clear", 7.0),
    "BannerPineB1": ("the tall mast pine: up a slope or beside stairs, singly or in a loose line across the wind; keep 4 studs clear", 4.0),
    "BannerPineB2": ("the snapped sail pine: ridge shoulders and terrace edges; keep 5 studs clear", 5.0),
    "CliffJuniperC1": ("the crawling juniper: on rock and at the foot of walls, its roots at the windward end (the foot sits on the ground; 14 long); keep 2 studs clear", 2.0),
    "CliffJuniperC2": ("the corkscrew juniper: beside steps, rocks and gates, a small accent 9 high; keep 3 studs clear", 3.0),
    "BronzeleafD1": ("the bronze windbroom: gardens, courts and pathsides, a small tree 9 long; keep 3 studs clear", 3.0),
    "BronzeleafD2": ("the bronze wind-pruned wedge: against walls and rock, a small tree 11 long; keep 3 studs clear", 3.0),
    "SplitSnagE1": ("the lightning-split pole: a dead landmark on a ridge or by a trail, 11 high; keep 3 studs clear", 3.0),
    "SplitSnagE2": ("the fallen half: a ruined stump with its torn half sliding downwind (the slab ramps 8 studs to +X); keep 3 studs clear", 3.0),
    "GiantCedar": ("THE landmark: one only, at the cliff edge of the territory (the crag is part of the piece, set it on the rim so the crown streams over the drop); keep 14 studs clear all round and 40 to +X", 14.0),
    "CragTail": ("a crag with a long scoured tail to +X: terrace edges and slopes, 16 long; keep 2 studs clear; the tail is low (under 1 stud) beyond x 6", 2.0),
    "SlateSlab": ("a plank-slab slanting down to +X on a boulder, with a scatter of plates downwind: against a terrace wall or a path edge; the underside is hollow, 18 long; keep 2 studs clear", 2.0),
    "StrataStack": ("a stack of plates leaning to +X: a path marker or a courtyard accent, 5 high; keep 2 studs clear", 2.0),
    "VeinBoulderA": ("a leaning bronze-veined monolith 7.5 high with a small boulder at its foot: courtyards, path forks, the stronghold's approaches; keep 2 studs clear", 2.0),
    "VeinBoulderB": ("a cloven boulder, the halves leaning apart over a bronze core (the cleft is 0.6 wide at the ground and opens upward): gate sides and trail corners; keep 2 studs clear", 2.0),
    "Windgate": ("a rock gate: the opening is about 3 wide and 6.4 high and runs along z: set it across a hidden path (yaw so the path runs through it); keep the opening clear; spill of plates to +X", 3.0),
    "Fin": ("a comb of five leaning slate fins stepping down from 7.4 to 2.5 toward +X, 14 long: cliff edges and the back of terraces; keep 2 studs clear", 2.0),
    "ScreeA": ("a scree fan 10 x 6: standing shards (up to 2.3 high) at the windward end stepping down to flat chips (under 0.5) downwind, no collision: on slopes and under rock walls", 0.0),
    "ScreeB": ("a narrow scree drift 11 x 3.5, three standing shards (up to 2 high) at the windward end then flat chips, no collision: along a path edge or a gully", 0.0),
    "StepsA": ("WALKABLE: four stepping slabs in a line along z, 4.2 apart (a straight way, 16 long); every top is at y 0.20: lay the piece with its origin 0.3 under the wanted top and no collision part (the mesh itself walks); the slabs are tied by buried bars", 0.0),
    "StepsB": ("WALKABLE: five smaller slabs on a slow curve along z (a winding way, 15 long); tops at y 0.20; as StepsA", 0.0),
    "Cobble": ("WALKABLE: a worn cobble strip 3 wide and 9 long along z, tops at y 0.20 within 0.03; chain end to end", 0.0),
    "PlankWalk": ("WALKABLE: a plank-and-peg walk 3.2 wide and 8.4 long along z, tops at y 0.20 within 0.02; chain end to end over rough or wet ground", 0.0),
    "GaleGrassA": ("a patch of gale grass about 7 x 6 (blades combed to +X): open ground and slopes, no collision", 0.0),
    "GaleGrassB": ("a tall grass tussock 5 x 2.5, blades to +X: beside rocks and walls, no collision", 0.0),
    "Sedge": ("sedge for the water's edge and wet hollows, 4 tall, no collision", 0.0),
    "Gorse": ("a wind-clipped gorse mound with ochre flowers: a big shrub, 4.4 x 2.4; keep 1 stud clear; one box collider", 1.0),
    "Heather": ("a heather tuft, small, no collision: rock feet and path sides", 0.0),
    "JuniperCreeper": ("a creeping dwarf juniper 4.5 long, hugging the ground; a big shrub, one low box collider; keep 1 stud clear", 1.0),
    "Cushion": ("a cushion plant with rose-brown stars, 3 across: on rock and path edges, no collision", 0.0),
    "Stonecrop": ("stonecrop in a crack, 4 long and under half a stud tall: along a rock's foot or a wall joint, no collision", 0.0),
    "Thistle": ("a mountain thistle, 4 tall: sparse accents among grass, no collision", 0.0),
    "WindStar": ("wind stars, a small teal aster, 3 tall: path sides and rock feet, no collision", 0.0),
    "LichenA": ("a lichen crust, 5 across and 0.1 high: lay on rock tops or ground (y 0.04), no collision", 0.0),
    "LichenB": ("a lichen band 8 x 2.5, 0.1 high: along rock faces and ground, no collision", 0.0),
}

# how many of each the placer is planned to use (the mix: 15 trees with the one giant, 24 rocks and path pieces, 60 plants)
PLAN = {"GiantCedar": 1, "GaleCedarA1": 2, "GaleCedarA2": 1, "BannerPineB1": 2, "BannerPineB2": 1, "CliffJuniperC1": 1, "CliffJuniperC2": 2, "BronzeleafD1": 1, "BronzeleafD2": 1,
        "SplitSnagE1": 2, "SplitSnagE2": 1,
        "CragTail": 3, "SlateSlab": 2, "StrataStack": 2, "VeinBoulderA": 2, "VeinBoulderB": 2, "Windgate": 1, "Fin": 2, "ScreeA": 2, "ScreeB": 2, "StepsA": 2, "StepsB": 2, "Cobble": 1, "PlankWalk": 1,
        "GaleGrassA": 10, "GaleGrassB": 4, "Sedge": 4, "Gorse": 3, "Heather": 5, "JuniperCreeper": 3, "Cushion": 8, "Stonecrop": 8, "Thistle": 5, "WindStar": 5, "LichenA": 3, "LichenB": 2}


def use_for(name):
    base = name.split("_", 2)[2]
    return USE.get(base, ("", 0.0))


# ----------------------------------------------------------------------------------------------------------------------
# colliders: simple invisible boxes in the piece frame (a little smaller than what is seen); crowns, plants and walkable paths have none
# ----------------------------------------------------------------------------------------------------------------------
def _shell_samples(g, shell_ids, which, per_edge=6):
    """Points sampled over the triangles of the shells in `which` (barycentric grid), to measure a shell inside a height band."""
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
    """Cuts the points into bands along `axis` (0 x, 1 y, 2 z) and returns one box per non-empty band, shrunk by the fraction `shrink` of its half sizes."""
    out = []
    a = lo
    while a < hi - 1e-6:
        b = min(hi, a + step)
        sel = [p for p in pts if a <= p[axis] <= b]
        if len(sel) >= 3:
            lo3 = [min(p[i] for p in sel) for i in range(3)]
            hi3 = [max(p[i] for p in sel) for i in range(3)]
            c = [(lo3[i] + hi3[i]) / 2 for i in range(3)]
            h = [(hi3[i] - lo3[i]) / 2 * (1 - (0.0 if i == 1 else shrink)) for i in range(3)]       # shrunk across, never in height (no gaps between bands)
            bx = {"x0": round(c[0] - h[0], 2), "x1": round(c[0] + h[0], 2), "y0": round(max(ymin, c[1] - h[1]), 2), "y1": round(c[1] + h[1], 2), "z0": round(c[2] - h[2], 2), "z1": round(c[2] + h[2], 2)}
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
            if i != j and c["x0"] <= b["x0"] + tol and c["x1"] >= b["x1"] - tol and c["y0"] <= b["y0"] + tol and c["y1"] >= b["y1"] - tol and c["z0"] <= b["z0"] + tol and c["z1"] >= b["z1"] - tol and (c != b or j < i):
                inside = True
                break
        if not inside:
            keep.append(b)
    return keep


def trunk_boxes(piece, suffix, ymax, step=2.2, shrink=0.16, axis=1, lo=None, hi=None):
    """Boxes up the first shell of `suffix` (the trunk is always built first): bands along y (or x for a crawling trunk), the trunk's height up to ymax."""
    g = piece.g[suffix]
    shell, _ = _shells(g)
    pts = _shell_samples(g, shell, {shell[0]})
    pts = [p for p in pts if p[1] <= ymax + 3.0]
    lo = lo if lo is not None else (-0.4 if axis == 1 else min(p[0] for p in pts))
    hi = hi if hi is not None else (ymax if axis == 1 else max(p[0] for p in pts))
    return _band_boxes(pts, axis, lo, hi, step, shrink, ymin=0.0)


def body_boxes(piece, suffixes=("Slate",), step=2.6, shrink=0.12, min_h=0.9, tall=3.0):
    """One set of boxes per stone body (each convex body is its own shell): bodies under min_h high are scenery and get none; a body taller than `tall` is cut
    into bands so a leaning slab is not boxed by its whole tilted bounding box."""
    out = []
    for sfx in suffixes:
        g = piece.g.get(sfx)
        if not g:
            continue
        shell, n = _shells(g)
        for sh in range(n):
            pts = _shell_samples(g, shell, {sh}, per_edge=3)
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


def collision_for(name, piece):
    base = name.split("_", 2)[2]
    if base.startswith("GaleCedarA1"):
        return trunk_boxes(piece, "Bark", 8.0)
    if base.startswith("GaleCedarA2"):
        return trunk_boxes(piece, "Bark", 7.0, step=2.0)
    if base.startswith("BannerPine"):
        return trunk_boxes(piece, "Bark", 8.0, step=3.0)
    if base == "CliffJuniperC1":
        return trunk_boxes(piece, "Deadwood", 5.0, step=2.4, axis=0, shrink=0.2)
    if base == "CliffJuniperC2":
        return trunk_boxes(piece, "Deadwood", 5.0, step=2.5, shrink=0.2)
    if base == "BronzeleafD1":
        return [{"x0": -0.3, "x1": 0.7, "y0": 0.0, "y1": 2.4, "z0": -0.6, "z1": 0.6}]
    if base == "BronzeleafD2":
        return trunk_boxes(piece, "Bark", 3.2, step=3.4)
    if base == "SplitSnagE1":
        return trunk_boxes(piece, "Deadwood", 5.5, step=2.8)
    if base == "SplitSnagE2":
        return trunk_boxes(piece, "Deadwood", 5.5, step=2.8) + [{"x0": 1.4, "x1": 4.6, "y0": 3.6, "y1": 5.6, "z0": -0.8, "z1": 1.0}, {"x0": 4.6, "x1": 8.0, "y0": 1.7, "y1": 3.9, "z0": -0.8, "z1": 1.0}]
    if base == "GiantCedar":
        return trunk_boxes(piece, "Bark", 22.0, step=3.6, shrink=0.14) + body_boxes(piece, ("Slate",), min_h=1.0)
    if base == "Fin":
        return body_boxes(piece, ("Slate",), min_h=1.6, tall=3.0, step=4.6)
    if base in ("CragTail", "SlateSlab", "StrataStack", "VeinBoulderA", "VeinBoulderB", "Windgate"):
        return body_boxes(piece, ("Slate",), min_h=1.4 if base != "StrataStack" else 1.0, tall=2.8)
    if base == "Gorse":
        return [{"x0": -1.5, "x1": 1.6, "y0": 0.0, "y1": 1.1, "z0": -0.6, "z1": 0.7}]
    if base == "JuniperCreeper":
        return [{"x0": -0.2, "x1": 2.9, "y0": 0.0, "y1": 0.8, "z0": -0.9, "z1": 0.9}]
    return []


def meta_for(name, piece):
    fam, base = name.split("_", 2)[1], name.split("_", 2)[2]
    lo, hi = piece.bounds()
    vs = [v for g in piece.g.values() for v in g.v]
    foot = [v for v in vs if v[1] < 1.2]
    use, keep = use_for(name)
    variant = base[-1] if base[-1] in "ABCDE" and base[-2:] in ("A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E1", "E2", "rA", "rB", "eA", "eB", "pA", "pB", "sA", "sB", "tA", "tB") else ""
    if base[-2:] in ("A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E1", "E2"):
        variant = base[-2:]
    elif base[-1] in "AB" and fam != "Trees":
        variant = base[-1]
    walk = base.startswith(("Steps", "Cobble", "PlankWalk"))
    d = {"family": fam, "piece": base, "variant": variant, "tris": piece.tris(), "materials": {k: v for k, v in sorted(piece.stats().items())},
         "bounds_min": [round(c, 2) for c in lo], "bounds_max": [round(c, 2) for c in hi],
         "radius": round(max(math.hypot(v[0], v[2]) for v in foot), 2) if foot else 0.0, "crown_radius": round(max(math.hypot(v[0], v[2]) for v in vs), 2),
         "height": round(hi[1], 2), "collision": collision_for(name, piece), "use": use, "keepout": keep, "walkable": walk,
         "leans": "+X (the prevailing wind: the crown, tail or blades stream toward +X in the piece's own frame)", "plan_count": PLAN.get(base, 0)}
    if walk:
        tops = [v[1] for g in piece.g.values() for v in g.v if v[1] > 0.0]
        d["walk_top_min"] = round(min(tops), 3) if tops else 0.0
        d["walk_top_max"] = round(max(tops), 3) if tops else 0.0
    return d


def build_all(names=None):
    pieces = {}
    meta = {}
    for fam, table in FAMILIES:
        for name, fn in table.items():
            full = "Windrift_%s_%s" % (fam, name)
            if names and full not in names and name not in names:
                continue
            p = fn()
            p.finish()
            pieces[full] = p
    return {"pieces": pieces, "meta": meta, "looks": LOOKS}


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
        print("%-36s %5d tris  %s  bounds %s %s  boxes %d  problems %s" % (name, p.tris(), p.stats(), [round(v, 1) for v in lo], [round(v, 1) for v in hi], len(data["meta"][name]["collision"]), probs))
    print("sum of one of each", total)

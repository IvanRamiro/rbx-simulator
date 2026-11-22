"""Dawnspire's own vegetation, garden rocks and ground cover (2026-11-22). Plain Python, no Blender (dawnspire_veg_run.py turns the pieces into
Blender objects, renders, QA and FBX). Built on hq_kit's Geo/Piece, in ROBLOX STUDS (x right, y up, z back; a piece's FRONT is -Z), every piece at
its own origin with y = 0 the ground it stands on (feet may sink below). One mesh per piece per material suffix, named
Dawnspire_<Family>_<Piece>__<Suffix>; no textures: each suffix takes a Roblox Material and Color from LOOKS.

This is a NEW library: it imports nothing from the Blossom Sanctuary's, the Jade Grove's or any other map's tree code (start_props, blossom_assets).
Every tree is a sect's cultivated GARDEN tree with its own growth rule:

  TierTree    a leader raised in horizontal tiers, each tier a scalloped cloud pad (pagoda-stepped crown, tall and narrow)
  PlinthTree  a clipped cloud-pruned tree rooted in a stone plinth beside a scholar's stone (low, lopsided, penjing)
  ArchTree    a PAIR of trunks arching over a path and meeting above it (an open, hollow silhouette: a living gate)
  BasinTree   a slender weeping-tip tree in a pot-like stone basin (a fountain of hanging blossom chains)
  BoundTree   an old gnarled tree, fluted trunk bound with silk ropes, split into limbs, one propped (a broad focal crown)

Blossom is built as layered cloud clusters: scalloped lofted pads and faceted puffs, split by face direction into two pale tints (top
`Blossom` near white, under faces `BlossomBlush` soft pink: much paler than the Blossom Sanctuary's rose).
"""
import math
import random

import hq_kit as K
from hq_kit import Geo, Piece, vadd, vsub, vmul, vdot, vcross, vnorm, vlen, lerp, TAU

# ======================================================================================================================
# the looks (Roblox Material + colour per material suffix: no texture, no upload)
# ======================================================================================================================
LOOKS = {
    "Bark": {"Material": "Wood", "Color": [100, 90, 98]},                       # cool blue-grey brown
    "BarkPale": {"Material": "Wood", "Color": [140, 132, 138]},                # silvery lichened bark (the old tree's burls)
    "Blossom": {"Material": "SmoothPlastic", "Color": [248, 231, 238]},         # pale white-pink
    "BlossomBlush": {"Material": "SmoothPlastic", "Color": [240, 199, 214]},    # the paler-pink second tint, for depth (under faces)
    "Stone": {"Material": "Limestone", "Color": [224, 220, 210]},              # scholar's rock, stepping stones, pebbles
    "Plinth": {"Material": "Marble", "Color": [238, 236, 232]},
    "PlinthBase": {"Material": "Granite", "Color": [176, 176, 184]},
    "Gold": {"Material": "Metal", "Color": [255, 172, 48]},
    "SilkWhite": {"Material": "Fabric", "Color": [240, 242, 250], "CastShadow": False},
    "SilkBlue": {"Material": "Fabric", "Color": [28, 62, 170], "CastShadow": False},
    "Soil": {"Material": "Slate", "Color": [62, 54, 58]},
    "Prop": {"Material": "WoodPlanks", "Color": [150, 126, 104]},              # the propping fork's lighter timber
    "AzaleaLeaf": {"Material": "LeafyGrass", "Color": [58, 112, 88]},
    "AzaleaBloom": {"Material": "SmoothPlastic", "Color": [250, 228, 238]},
    "PeonyWhite": {"Material": "SmoothPlastic", "Color": [250, 247, 247]},
    "PeonyBlush": {"Material": "SmoothPlastic", "Color": [242, 202, 218]},
    "Leaf": {"Material": "LeafyGrass", "Color": [66, 122, 96]},
    "Needle": {"Material": "LeafyGrass", "Color": [44, 94, 86]},
    "LotusPetal": {"Material": "SmoothPlastic", "Color": [246, 228, 238]},
    "LotusPad": {"Material": "LeafyGrass", "Color": [62, 118, 90]},
    "Water": {"Material": "Glass", "Color": [110, 190, 230], "Transparency": 0.5, "CastShadow": False},
    "IrisWhite": {"Material": "SmoothPlastic", "Color": [248, 248, 253]},
    "IrisLeaf": {"Material": "LeafyGrass", "Color": [84, 138, 108]},
    "PetalWhite": {"Material": "SmoothPlastic", "Color": [252, 248, 250], "CastShadow": False},
    "PetalPink": {"Material": "SmoothPlastic", "Color": [242, 204, 218], "CastShadow": False},
    "Gravel": {"Material": "Limestone", "Color": [214, 210, 198], "CastShadow": False},
    "Moss": {"Material": "LeafyGrass", "Color": [86, 142, 100]},
}


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


def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k] + t ** 3 * p3[k] for k in range(3)))
    return out


def _rot(v, axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    return vadd(vadd(vmul(v, c), vmul(vcross(axis, v), s)), vmul(axis, vdot(axis, v) * (1 - c)))


def frames_along(pts):
    """Parallel-transport frames (tangent, normal, binormal) at every point."""
    n = len(pts)
    T = [vnorm(vsub(pts[min(i + 1, n - 1)], pts[max(i - 1, 0)])) for i in range(n)]
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


def sweep(g, pts, radii, sides=6, mod=None, twist=0.0, squash=1.0, phase=0.0, caps=(True, True)):
    """A closed tapered tube along pts (radius per point). mod(t, angle) -> a radius factor (ridges, flutes); twist turns the section per point."""
    n = len(pts)
    T, Ns, Bs = frames_along(pts)
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


def torus_loop(g, centre, ax_u, ax_v, R, r, seg_u=14, seg_v=5, rfun=None):
    """A ring-shaped solid in the plane spanned by the unit vectors ax_u, ax_v (major radius R, minor radius r(a))."""
    rings = []
    for k in range(seg_u):
        a = TAU * k / seg_u
        ca, sa = math.cos(a), math.sin(a)
        d = vadd(vmul(ax_u, ca), vmul(ax_v, sa))
        nrm = vcross(ax_u, ax_v)
        rr = r if rfun is None else rfun(a)
        row = []
        for m in range(seg_v):
            b = TAU * m / seg_v
            row.append(g.vert(vadd(centre, vadd(vmul(d, R + rr * math.cos(b)), vmul(nrm, rr * math.sin(b))))))
        rings.append(row)
    start = len(g.f)
    for k in range(seg_u):
        j = (k + 1) % seg_u
        for m in range(seg_v):
            q = (m + 1) % seg_v
            g.face(rings[k][m], rings[j][m], rings[j][q], rings[k][q])
    K._orient_solid(g, start)


# ======================================================================================================================
# blossom masses: lobed pads and faceted puffs (closed solids split into two tints by face direction)
# ======================================================================================================================
_ICO = {}


def ico(level):
    if level in _ICO:
        return _ICO[level]
    t = (1 + math.sqrt(5)) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    v = [vnorm(p) for p in v]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2),
         (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache = {}
        nf = []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                cache[key] = len(v)
                v.append(vnorm(vmul(vadd(v[a], v[b]), 0.5)))
            return cache[key]
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    _ICO[level] = (v, f)
    return _ICO[level]


class Tones:
    """Receives closed shells and puts each face into the top or the under Geo of a tone pair by its outward normal."""

    def __init__(self, P, top="Blossom", under="BlossomBlush", thresh=-0.18):
        self.gt = P.geo(top)
        self.gu = P.geo(under)
        self.thresh = thresh

    def emit(self, verts, faces):
        vol = 0.0
        p0 = verts[faces[0][0]]
        for f in faces:
            for j in range(1, len(f) - 1):
                vol += vdot(vsub(verts[f[0]], p0), vcross(vsub(verts[f[j]], p0), vsub(verts[f[j + 1]], p0))) / 6.0
        if vol < 0:
            faces = [tuple(reversed(f)) for f in faces]
        maps = {}
        for f in faces:
            a, b, c = verts[f[0]], verts[f[1]], verts[f[2]]
            n = vnorm(vcross(vsub(b, a), vsub(c, a)))
            g = self.gu if n[1] < self.thresh else self.gt
            ids = []
            for i in f:
                key = (id(g), i)
                if key not in maps:
                    maps[key] = g.vert(verts[i])
                ids.append(maps[key])
            g.face(*ids)

    def puff(self, c, rx, ry, rz, rng, level=1, amp=0.2, yaw=0.0, flat_under=0.0):
        """A faceted lobed puff (icosphere, radially displaced by a few low-frequency waves)."""
        v0, f0 = ico(level)
        waves = [(rng.uniform(1.2, 3.2), rng.uniform(1.2, 3.2), rng.uniform(1.2, 3.2), rng.uniform(0, TAU)) for _ in range(3)]
        cy, sy = math.cos(yaw), math.sin(yaw)
        verts = []
        for d in v0:
            n = sum(math.sin(a * d[0] + b * d[1] + cc * d[2] + ph) for a, b, cc, ph in waves) / 3.0
            r = 1.0 + amp * n
            x, y, z = d[0] * r * rx, d[1] * r * ry, d[2] * r * rz
            if y < 0:
                y *= 1.0 - flat_under
            verts.append((c[0] + x * cy + z * sy, c[1] + y, c[2] - x * sy + z * cy))
        self.emit(verts, [tuple(f) for f in f0])

    def pad(self, c, R, h, rng, seg=10, lobes=5, amp=0.2, yaw=0.0, ratio=1.0, bump=0.12, sym=False):
        """A scalloped cloud pad: a flat-bottomed, domed disc whose rim is lobed (lobes scallops), a lofted closed solid (80 triangles at seg 10).
        c = the centre of the pad's middle plane; R the rim radius; h its full height; ratio stretches z against x."""
        prof = [(0.0, -0.5), (0.72, -0.42), (1.0, -0.02), (0.88, 0.36), (0.52, 0.7), (0.0, 0.82)]
        ph = 0.0 if sym else rng.uniform(0, TAU)
        ph2 = 0.0 if sym else rng.uniform(0, TAU)
        cy, sy = math.cos(yaw), math.sin(yaw)
        verts = []
        rings = []
        for (rr, yy) in prof:
            if rr == 0.0:
                verts.append((c[0], c[1] + yy * h, c[2]))
                rings.append(len(verts) - 1)
                continue
            row = []
            for k in range(seg):
                a = TAU * k / seg
                m = 1.0 + amp * math.cos(lobes * a + ph) + 0.35 * amp * math.cos((lobes + 2) * a + ph2)
                rad = R * rr * m
                x, z = rad * math.cos(a), rad * math.sin(a) * ratio
                y = yy * h + (bump * h * math.cos(lobes * a + (0.0 if sym else ph + 1.3)) * rr if yy > 0.2 else 0.0)
                verts.append((c[0] + x * cy + z * sy, c[1] + y, c[2] - x * sy + z * cy))
                row.append(len(verts) - 1)
            rings.append(row)
        faces = []
        for i in range(len(prof) - 1):
            L, U = rings[i], rings[i + 1]
            for k in range(seg):
                j = (k + 1) % seg
                if isinstance(L, int):
                    faces.append((L, U[j], U[k]))
                elif isinstance(U, int):
                    faces.append((L[k], L[j], U))
                else:
                    faces.append((L[k], L[j], U[j], U[k]))
        self.emit(verts, faces)


def cluster(T, c, R, h, rng, n_out=3, puffs=3, yaw0=0.0, seg=10, lobes=5, amp=0.2, spread=0.62, ratio=1.0):
    """A cloud cluster = one main pad plus n_out smaller pads round it at different heights and a few faceted puffs on top (overlapping lobed masses)."""
    T.pad(c, R * 0.74, h, rng, seg=seg, lobes=lobes, amp=amp, yaw=yaw0, ratio=ratio)
    for k in range(n_out):
        a = yaw0 + TAU * k / max(1, n_out) + rng.uniform(-0.3, 0.3)
        r = R * spread * rng.uniform(0.9, 1.1)
        T.pad((c[0] + math.cos(a) * r, c[1] + h * rng.uniform(-0.28, 0.12), c[2] - math.sin(a) * r * ratio), R * rng.uniform(0.36, 0.46), h * rng.uniform(0.7, 0.9), rng,
              seg=seg - 2 if seg > 8 else seg, lobes=max(3, lobes - 1), amp=amp, yaw=rng.uniform(0, TAU))
    for k in range(puffs):
        a = rng.uniform(0, TAU)
        r = R * rng.uniform(0.0, 0.42)
        T.puff((c[0] + math.cos(a) * r, c[1] + h * rng.uniform(0.42, 0.72), c[2] - math.sin(a) * r), R * rng.uniform(0.2, 0.3), h * rng.uniform(0.34, 0.5),
               R * rng.uniform(0.2, 0.3), rng, level=0, amp=0.25, yaw=rng.uniform(0, TAU))


# ======================================================================================================================
# stone parts shared by the trees: plinth, basin, a small garden stone
# ======================================================================================================================
def plinth(P, w=5.2, top=1.8):
    """A stepped marble plinth: a granite foot (sunk 0.4), a marble body with four recessed panels edged in gold, a capping slab with a low rim round
    a soil bed. Returns the soil level."""
    gs = P.geo("PlinthBase")
    gm = P.geo("Plinth")
    gg = P.geo("Gold")
    so = P.geo("Soil")
    h = w / 2
    K.box(gs, -h - 0.25, h + 0.25, -0.4, 0.45, -h - 0.25, h + 0.25, "TNESW")
    K.box(gm, -h + 0.15, h - 0.15, 0.45, top - 0.45, -h + 0.15, h - 0.15, "NESW")
    # recessed panels: a framed panel on each of the four faces (the face's own plane sunk 0.1) edged in gold
    for face in range(4):
        yaw = face * math.pi / 2
        pg, pm = Geo(), Geo()
        K.box(pm, -h * 0.56, h * 0.56, 0.75, top - 0.78, h - 0.15, h - 0.04, "TBNESW")
        K.box(pg, -h * 0.56 - 0.08, h * 0.56 + 0.08, 0.7, 0.78, h - 0.15, h - 0.0, "TBNESW")
        K.box(pg, -h * 0.56 - 0.08, h * 0.56 + 0.08, top - 0.86, top - 0.78, h - 0.15, h - 0.0, "TBNESW")
        gm.add(pm, yaw=yaw)
        gg.add(pg, yaw=yaw)
    K.box(gm, -h, h, top - 0.45, top, -h, h, "TNESW")
    # the rim round the bed (four low walls) and the soil
    t = 0.32
    K.box(gm, -h, h, top, top + 0.22, -h, -h + t, "TNESW")
    K.box(gm, -h, h, top, top + 0.22, h - t, h, "TNESW")
    K.box(gm, -h, -h + t, top, top + 0.22, -h + t, h - t, "TNESW")
    K.box(gm, h - t, h, top, top + 0.22, -h + t, h - t, "TNESW")
    K.box(so, -h + t, h - t, top - 0.05, top + 0.14, -h + t, h - t, "TNESW")
    return top + 0.14


def pedestal(P, top=3.3):
    """A tall vase-shaped marble pedestal (round, 4.4 across at the rim, a waisted stem and a gold band) with a soil bed in its mouth. Returns the soil level."""
    gm = P.geo("Plinth")
    gg = P.geo("Gold")
    gs = P.geo("PlinthBase")
    so = P.geo("Soil")
    K.lathe(gs, [(0.0, -0.4), (2.15, -0.4), (2.2, 0.15), (2.0, 0.45), (0.0, 0.45)], 12, caps=False)
    K.lathe(gm, [(1.85, 0.45), (1.45, 0.9), (1.2, 1.5), (1.45, 2.1), (1.95, 2.6), (2.1, 3.0), (2.2, top - 0.1), (2.05, top), (1.8, top - 0.1), (1.7, 2.8), (0.0, 2.8)], 12, caps=False)
    K.lathe(gg, [(1.22, 1.2), (1.34, 1.35), (1.22, 1.5)], 12, loop=True)
    K.lathe(so, [(0.0, top - 0.25), (1.72, top - 0.25), (1.72, top - 0.12), (1.0, top - 0.04), (0.0, top)], 12, caps=False)
    return top


def scholar_stone(g, c, h, w, rng, seed=1, flutes=5, yaw=0.0, lean=(0.0, 0.0)):
    """A small fluted garden stone (a lofted column, narrow at the foot, swelling then thinning, with deliberate flutes); c = foot centre."""
    n = 9
    pts = [(c[0] + lean[0] * (i / (n - 1)) ** 1.5 * h, c[1] + h * i / (n - 1), c[2] + lean[1] * (i / (n - 1)) ** 1.5 * h) for i in range(n)]
    ph = rng.uniform(0, TAU)

    def rf(t):
        return w * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.25 + t * 0.85)) ** 0.8) * (1 - 0.55 * t ** 2.4)

    def mod(t, a):
        return 1.0 + 0.22 * math.cos(flutes * a + 2.0 * t + ph) + 0.1 * math.cos(2 * a + 5 * t)
    sweep(g, pts, [rf(i / (n - 1)) for i in range(n)], 10, mod=mod, squash=0.8, phase=yaw)


def basin(P, R=1.75, with_gold=True):
    """A pot-like stone basin (Limestone-white Plinth marble): foot, bulging belly, a collar and an out-turned lip; a soil bed inside; a gold band on the belly."""
    gm = P.geo("Plinth")
    gg = P.geo("Gold")
    so = P.geo("Soil")
    prof = [(0.0, -0.2), (R * 0.56, -0.2), (R * 0.62, 0.35), (R * 0.5, 0.55), (R * 0.82, 0.95), (R * 1.0, 1.35), (R * 0.96, 1.75), (R * 0.84, 1.88), (R * 0.97, 2.0),
            (R * 1.04, 2.12), (R * 0.9, 2.2), (R * 0.84, 2.1), (R * 0.7, 1.9), (0.0, 1.9)]
    K.lathe(gm, prof, 14, caps=False)
    if with_gold:
        K.lathe(gg, [(R * 1.0 + 0.0, 1.05), (R * 1.0 + 0.1, 1.2), (R * 1.0, 1.35)], 14, loop=True)
    K.lathe(so, [(0.0, 1.88), (R * 0.72, 1.88), (R * 0.72, 1.96), (R * 0.4, 2.02), (0.0, 2.05)], 14, caps=False)
    return 2.0


# ======================================================================================================================
# tree 1: TierTree
# ======================================================================================================================
def tier_tree(variant):
    """Raised in tiers: a tall leader, a whorl of spokes at each tier, a scalloped cloud pad (and satellites) laid over each whorl, the pads shrinking
    upward like a stepped pagoda roof. A: four tiers, upright, centred, 18 tall; B: three tiers, a leaning leader, the pads staggered off-axis, 15 tall."""
    P = Piece()
    rng = random.Random(40 + variant)
    gb = P.geo("Bark")
    T = Tones(P)
    if variant == 0:
        H = 19.4
        tiers = [(5.8, 8.4, 2.3), (9.8, 6.9, 2.1), (13.6, 5.1, 1.9), (17.0, 3.3, 1.7)]
        lean = (0.0, 0.0)
        off = [(0, 0), (0, 0), (0, 0), (0, 0)]
        n_out = [4, 3, 3, 0]
        pad_ratio = 1.0
    else:
        H = 16.2
        tiers = [(5.0, 9.0, 2.4), (9.0, 6.6, 2.0), (13.0, 4.0, 1.7)]
        lean = (4.4, 1.0)
        off = [(-1.8, 0.0), (0.3, 0.0), (1.4, 0.0)]
        n_out = [3, 2, 0]
        pad_ratio = 0.62
    n_leader = 14
    # the leader: an S-curve, flared at the foot, tapering to the top pad
    pts = []
    for i in range(n_leader):
        t = i / (n_leader - 1)
        pts.append((lean[0] * t ** 1.6 + 0.45 * math.sin(t * 2.3 + variant), (H - 1.2) * t - 0.4, lean[1] * t ** 1.6 + 0.3 * math.sin(t * 1.7 + 1.0)))
    ridge = lambda t, a: 1.0 + 0.1 * math.cos(4 * a + 3 * t)
    sweep(gb, pts, taper(n_leader, 1.2, 0.22, 0.85, flare=0.5), 8, mod=ridge)
    # buttress roots (four, low, diving into the ground)
    for k in range(4):
        a = TAU * k / 4 + 0.5 + variant * 0.4
        limb(gb, [(math.cos(a) * 0.4, 0.9, math.sin(a) * 0.4), (math.cos(a) * 1.3, 0.35, math.sin(a) * 1.3), (math.cos(a) * 2.3, -0.25, math.sin(a) * 2.3)], 0.42, 0.14, sides=5, per=2)

    def leader_at(y):
        t = (y + 0.4) / (H - 1.2)
        t = max(0.0, min(1.0, t))
        return (lean[0] * t ** 1.6 + 0.45 * math.sin(t * 2.3 + variant), y, lean[1] * t ** 1.6 + 0.3 * math.sin(t * 1.7 + 1.0))
    for i, (y, R, h) in enumerate(tiers):
        lp = leader_at(y - 1.0)
        ox, oz = off[i]
        centre = (lp[0] + ox, y + h * 0.1, lp[2] + oz)
        yaw0 = i * 0.9 + variant * 0.6
        # the whorl: spokes from the leader to the pad centre and to each satellite
        ends = [centre]
        for k in range(n_out[i]):
            a = yaw0 + TAU * k / n_out[i]
            ends.append((centre[0] + math.cos(a) * R * 0.62, y - h * 0.05, centre[2] - math.sin(a) * R * 0.62))
        spokes = 3 if n_out[i] == 0 else n_out[i] + 1
        for k, e in enumerate(ends[:spokes]):
            a = vsub(e, lp)
            lowish = (lp[0] + a[0] * 0.5, lp[1] - 0.15 + 0.25, lp[2] + a[2] * 0.5)
            limb(gb, [lp, lowish, (e[0], e[1] - h * 0.18, e[2])], 0.34 * (1.1 - 0.15 * i), 0.1, sides=5, per=2)
        cluster(T, centre, R, h, rng, n_out=n_out[i], puffs=2 if i < len(tiers) - 1 else 3, yaw0=yaw0, seg=10, lobes=5, amp=0.2, spread=0.62, ratio=pad_ratio)
    return P


# ======================================================================================================================
# tree 2: PlinthTree
# ======================================================================================================================
def plinth_tree(variant):
    """Penjing on a plinth: a short gnarled trunk growing out of a soil bed beside a scholar's stone, trained into a few flat cloud-pruned pads on long
    horizontal limbs. A: a broad low plinth (5.2 x 1.8), a literati form, one slender curved trunk with small pads up its sides (9.4 tall); B: a tall vase-shaped pedestal
    (4.4 across, 3.3 tall), a semi-cascade: the trunk bows out over the pedestal's left edge and falls beside it while the main crown stands over the stone (9.7 tall)."""
    P = Piece()
    rng = random.Random(60 + variant)
    gb = P.geo("Bark")
    T = Tones(P)
    soil = plinth(P, 5.2, 1.8) if variant == 0 else pedestal(P, 3.3)
    gst = P.geo("Stone")
    if variant == 0:
        scholar_stone(gst, (1.35, soil - 0.1, 1.05), 2.3, 0.75, rng, flutes=5, yaw=0.4, lean=(0.2, -0.1))
        scholar_stone(gst, (1.95, soil - 0.1, 0.35), 1.25, 0.5, rng, flutes=4, yaw=1.1)
    else:
        scholar_stone(gst, (1.0, soil - 0.2, 0.7), 1.7, 0.55, rng, flutes=5, yaw=0.4, lean=(0.15, -0.1))
    ridge = lambda t, a: 1.0 + 0.16 * math.cos(3 * a + 5 * t) + 0.08 * math.cos(5 * a)
    if variant == 0:
        # literati form: one slender S-curved trunk, small clipped pads laid up its left and right in turn (tall and narrow over the broad plinth)
        trunk = [(-0.7, soil - 0.2, 0.3), (-0.9, soil + 1.4, 0.2), (-0.1, soil + 2.8, -0.1), (0.5, soil + 4.2, 0.1), (0.1, soil + 5.6, 0.0), (0.2, soil + 6.6, -0.1)]
        cv = catmull(trunk, 4)
        sweep(gb, cv, taper(len(cv), 0.62, 0.17, 0.8, flare=0.3), 8, mod=ridge, twist=0.05)
        limb(gb, [(-0.1, soil + 2.8, -0.1), (0.9, soil + 3.2, -0.4), (1.5, soil + 3.5, -0.3)], 0.24, 0.1, sides=5)
        limb(gb, [(0.5, soil + 4.2, 0.1), (-0.6, soil + 4.6, 0.5), (-1.3, soil + 4.9, 0.4)], 0.22, 0.1, sides=5)
        cluster(T, (1.7, soil + 3.7, -0.3), 1.9, 0.95, rng, n_out=2, puffs=1, seg=10, lobes=5, amp=0.18, spread=0.6, ratio=0.85)
        cluster(T, (-1.5, soil + 5.1, 0.4), 1.8, 0.9, rng, n_out=2, puffs=1, seg=10, lobes=5, amp=0.18, spread=0.6, ratio=0.85)
        cluster(T, (0.3, soil + 6.7, -0.1), 1.9, 0.95, rng, n_out=2, puffs=2, seg=10, lobes=4, amp=0.2, spread=0.6)
    else:
        f = 0.7
        Y = lambda h: soil + h * f
        trunk = [(0.4, soil - 0.2, 0.2), (0.7, Y(1.4), 0.1), (0.3, Y(3.0), -0.2), (-0.9, Y(4.0), -0.3), (-2.4, Y(3.7), -0.1), (-3.3, Y(2.2), 0.0), (-3.6, Y(0.7), 0.1)]
        cv = catmull(trunk, 4)
        sweep(gb, cv, taper(len(cv), 0.66, 0.16, 0.85, flare=0.3), 8, mod=ridge, twist=0.05)
        limb(gb, [(0.3, Y(3.0), -0.2), (0.9, Y(4.2), 0.2), (1.2, Y(5.4), 0.1), (1.0, Y(6.6), 0.0)], 0.36, 0.14, sides=5)
        limb(gb, [(0.9, Y(4.2), 0.2), (3.0, Y(5.0), 0.3), (5.2, Y(5.5), 0.3), (6.6, Y(5.5), 0.3)], 0.28, 0.1, sides=5)
        cluster(T, (1.0, Y(7.0), 0.0), 2.7, 1.25, rng, n_out=3, puffs=2, seg=10, lobes=5, amp=0.18, spread=0.62)
        cluster(T, (6.9, Y(5.9), 0.3), 2.3, 0.95, rng, n_out=2, puffs=1, seg=10, lobes=4, amp=0.18, spread=0.6, ratio=0.8)
        cluster(T, (-3.8, Y(0.9), 0.1), 2.1, 1.0, rng, n_out=2, puffs=1, seg=10, lobes=4, amp=0.18, spread=0.6)   # the cascade, beside the pedestal
    return P


# ======================================================================================================================
# tree 3: ArchTree (a pair)
# ======================================================================================================================
def arch_tree(variant):
    """A living gate: two trunks rise either side of a path (x axis across, the path runs along z) and meet over it; built as the right trunk and then
    its exact mirror. A: a LANCET ARCH, the trunks leaning in together and meeting at a point, the crowns fused in a blossom band that follows the arc
    (clear width 10 between the feet, 14 tall); B: a SQUARE PORTAL, two upright trunks that kink at the shoulder into near-horizontal lintel limbs
    meeting in a knot, a flat double-tier crown laid over the lintel and one cascade pad hanging at each shoulder (clear width 14, 13 tall)."""
    P = Piece()
    rng = random.Random(80 + variant)
    half = Piece()
    hb = half.geo("Bark")
    hT = Tones(half)
    ridge = lambda t, a: 1.0 + 0.12 * math.cos(3 * a + 4 * t + variant)
    if variant == 0:
        foot = 5.9
        ctrl = [(foot, -0.3, 0.2), (foot + 0.25, 3.2, 0.0), (foot - 0.2, 6.2, -0.15), (foot - 1.7, 8.9, 0.1), (foot - 3.8, 10.8, 0.0), (foot - 5.2, 11.4, -0.2), (0.3, 11.5, 0.0)]
        cv = catmull(ctrl, 4)
        sweep(hb, cv, taper(len(cv), 0.95, 0.4, 0.8, flare=0.45), 8, mod=ridge)
        for k in range(2):   # low roots
            a = -0.5 + k * 1.3
            limb(hb, [(foot + math.cos(a) * 0.3, 0.8, math.sin(a) * 0.3), (foot + math.cos(a) * 1.4, 0.2, math.sin(a) * 1.4), (foot + math.cos(a) * 2.2, -0.3, math.sin(a) * 2.2)], 0.4, 0.14, sides=5, per=2)
        spots = [0.38, 0.64]
        n = len(cv)
        for si, s_ in enumerate(spots):
            p = cv[int(s_ * (n - 1))]
            out = (0.0, 0.5, 0.9 if si % 2 == 0 else -0.9)
            end = (p[0] + 0.5 * (1 if si < 2 else -0.4), p[1] + 1.1 + 0.4 * si, p[2] + out[2] * 2.2)
            if si < 2:
                limb(hb, [p, vadd(p, (0.0, 0.4, out[2])), end], 0.24, 0.1, sides=5, per=2)
            cluster(hT, (end[0], max(end[1] + 0.9, 9.4) if si >= 1 else end[1] + 0.9, end[2]), 2.6, 1.5, rng, n_out=1 if si == 0 else 2, puffs=1, yaw0=si * 1.3, seg=9, lobes=5, amp=0.18, spread=0.6, ratio=0.9)
        # the keystone: a symmetric knot where the two trunks meet, and one symmetric cloud pad over it (the only masses on the axis)
        K.lathe(P.geo("Bark"), [(0.0, 10.7), (0.7, 10.95), (0.85, 11.5), (0.7, 12.05), (0.0, 12.3)], 8, caps=False)
        Tones(P).pad((0.0, 12.6, 0.0), 3.4, 1.5, rng, seg=10, lobes=4, amp=0.17, sym=True, ratio=0.85)
    else:
        foot = 8.0
        ctrl = [(foot, -0.3, -0.2), (foot + 0.35, 2.4, 0.1), (foot + 0.1, 5.0, 0.0), (foot - 0.5, 7.4, -0.1), (foot - 1.7, 8.9, 0.0), (foot - 3.6, 9.6, 0.1), (foot - 5.6, 9.8, 0.0),
                (foot - 7.4, 9.9, 0.05), (0.3, 9.9, 0.05)]
        cv = catmull(ctrl, 4)
        sweep(hb, cv, taper(len(cv), 1.05, 0.42, 0.7, flare=0.45), 8, mod=ridge)
        for k in range(2):
            a = 0.2 + k * 1.5
            limb(hb, [(foot + math.cos(a) * 0.3, 0.8, math.sin(a) * 0.3), (foot + math.cos(a) * 1.4, 0.2, math.sin(a) * 1.4), (foot + math.cos(a) * 2.2, -0.3, math.sin(a) * 2.2)], 0.4, 0.14, sides=5, per=2)
        # the outer shoulder limb: out and slightly down, a cascade pad hanging beyond the trunk
        limb(hb, [(foot + 0.3, 6.2, 0.0), (foot + 1.6, 6.6, 0.1), (foot + 2.6, 6.2, 0.1)], 0.3, 0.12, sides=5, per=2)
        cluster(hT, (foot + 2.9, 5.7, 0.1), 2.1, 1.1, rng, n_out=1, puffs=1, seg=9, lobes=4, amp=0.18, spread=0.6)
        # the crown: a flat tier laid along the lintel, a second smaller tier over it, short puffs hanging inside the shoulder
        def y_at(xq):
            best = min(cv, key=lambda p: abs(p[0] - xq))
            return best[1]
        for x in (6.9, 4.2):    # short stems from the lintel up into the crown's pads
            y0 = y_at(x)
            limb(hb, [(x, y0 - 0.2, 0.0), (x, y0 + 0.9, 0.0), (x, 10.5, 0.0)], 0.22, 0.16, sides=4, per=1)
        for x, R in ((6.9, 3.4), (4.2, 2.6)):
            cluster(hT, (x, 10.8, 0.0), R, 1.35, rng, n_out=1, puffs=1, seg=9, lobes=5, amp=0.17, spread=0.6, ratio=0.75)
        cluster(hT, (4.6, 12.5, 0.0), 2.5, 1.1, rng, n_out=1, puffs=0, seg=9, lobes=4, amp=0.17, spread=0.55, ratio=0.7)
        K.lathe(P.geo("Bark"), [(0.0, 9.1), (0.7, 9.35), (0.85, 9.9), (0.7, 10.45), (0.0, 10.7)], 8, caps=False)
        Tones(P).pad((0.0, 11.0, 0.0), 3.6, 1.4, rng, seg=10, lobes=4, amp=0.17, sym=True, ratio=0.75)
    P.add(half)
    P.add(half.mirrored())
    return P


# ======================================================================================================================
# tree 4: BasinTree
# ======================================================================================================================
def basin_tree(variant):
    """A slender weeping-tip tree in a pot-like stone basin: a thin curved trunk, a few arching limbs from the top that fall in long strands, each strand
    carrying a hanging chain of small teardrop blossom puffs, a cap of cloud pads on top. A: an even fountain (7 strands, 8.9 tall); B: a lopsided
    cascade, the trunk leaning, the strands all falling to one side (8.6 tall)."""
    P = Piece()
    rng = random.Random(100 + variant)
    gb = P.geo("Bark")
    T = Tones(P)
    soil = basin(P)
    ridge = lambda t, a: 1.0 + 0.1 * math.cos(3 * a + 5 * t)
    if variant == 0:
        trunk = [(0.0, soil - 0.2, 0.0), (0.15, soil + 1.6, 0.1), (-0.05, soil + 3.3, -0.1), (0.1, soil + 4.8, 0.05), (0.0, soil + 5.7, 0.0)]
        strands = [(TAU * k / 7 + 0.3) for k in range(7)]
        reach = 2.6
        top = (0.0, soil + 5.7, 0.0)
    else:
        trunk = [(-0.5, soil - 0.2, 0.2), (-0.7, soil + 1.5, 0.1), (-0.3, soil + 3.1, -0.2), (0.7, soil + 4.4, -0.3), (1.2, soil + 5.2, -0.3)]
        strands = [(-0.9 + 0.62 * k) for k in range(6)]   # a fan to the +x side
        reach = 2.9
        top = (1.2, soil + 5.2, -0.3)
    cv = catmull(trunk, 4)
    sweep(gb, cv, taper(len(cv), 0.42, 0.12, 0.85, flare=0.18), 7, mod=ridge)
    for si, a in enumerate(strands):
        # the limb rises from the upper trunk, arches out and falls: its tip hangs just clear above the basin's lip
        h0 = top[1] - 0.2 - (si % 3) * 0.5
        start = lerp3_y(top, h0 - 0.011 * si)
        r = reach * (0.8 + 0.25 * ((si * 37) % 5) / 4)
        ax, az = math.cos(a), -math.sin(a)
        p1 = (start[0] + ax * r * 0.45, h0 + 0.55, start[2] + az * r * 0.45)
        p2 = (start[0] + ax * r * 0.95, h0 + 0.25, start[2] + az * r * 0.95)
        drop = h0 - (soil + 1.15 + 0.5 * (si % 2))
        p3 = (start[0] + ax * (r * 1.15), h0 - drop * 0.55, start[2] + az * r * 1.15)
        p4 = (start[0] + ax * (r * 1.2), h0 - drop, start[2] + az * r * 1.2)
        pts = catmull([start, p1, p2, p3, p4], 3)
        sweep(gb, pts, taper(len(pts), 0.16, 0.045, 0.9), 5)
        # the chain: elongated teardrop puffs down the falling part
        chain = [p for p in pts[len(pts) // 2:]]
        m = len(chain)
        for q in range(m):
            if q % 2 == 1 and q != m - 1:
                continue
            pp = chain[q]
            sz = 0.5 - 0.2 * (q / max(1, m - 1))
            T.puff((pp[0], pp[1] - 0.3, pp[2]), sz, sz * 1.6, sz, rng, level=0, amp=0.2, yaw=rng.uniform(0, TAU))
        # a pad where the limb arches (the weeping cloud)
        pp = pts[len(pts) // 3]
        T.pad((pp[0], pp[1] + 0.35, pp[2]), 1.1, 0.9, rng, seg=8, lobes=4, amp=0.2, yaw=a)
    # the cap
    T.pad((top[0], top[1] + 0.5, top[2]), 1.7, 1.1, rng, seg=10, lobes=5, amp=0.2)
    T.puff((top[0] + 0.3, top[1] + 1.3, top[2]), 0.8, 0.6, 0.8, rng, level=0, amp=0.25)
    return P


def lerp3_y(p, y):
    return (p[0], y, p[2])


# ======================================================================================================================
# tree 5: BoundTree
# ======================================================================================================================
def bound_tree(variant):
    """The old focal tree: a thick, fluted, gnarled trunk on buttress roots, bound with silk bands (white, with a gold clasp and hanging blue tassels),
    a burl, splitting at about 4 into great limbs under a broad crown of cloud pads. A: three limbs, a forked prop under the long low limb (14 tall,
    13 across); B: two limbs and a low side limb, no prop (13 tall, 12 across)."""
    P = Piece()
    rng = random.Random(120 + variant)
    gb = P.geo("Bark")
    gp = P.geo("BarkPale")
    gs = P.geo("SilkWhite")
    gb2 = P.geo("SilkBlue")
    gg = P.geo("Gold")
    T = Tones(P)
    # trunk: twisting, fluted, swelling at the bands
    if variant == 0:
        trunk = [(0.0, -0.5, 0.0), (0.3, 1.2, -0.2), (-0.1, 2.6, 0.2), (0.2, 3.8, 0.0), (0.0, 4.6, 0.1)]
        r0 = 2.0
    else:
        trunk = [(0.0, -0.5, 0.0), (-0.4, 1.3, 0.2), (0.1, 2.7, 0.3), (0.5, 3.9, 0.1), (0.4, 4.7, 0.0)]
        r0 = 1.85
    cv = catmull(trunk, 4)
    n = len(cv)

    def rt(t):
        return lerp(r0, 1.05, t ** 0.7) + 0.7 * math.exp(-8 * t)

    def mod(t, a):
        return 1.0 + 0.2 * math.cos(5 * a + 3.2 * t + variant) + 0.08 * math.cos(3 * a - 4 * t)
    radii = [rt(i / (n - 1)) for i in range(n)]
    sweep(gb, cv, radii, 8, mod=mod, squash=0.92, twist=0.04)

    def trunk_at(t):
        i = max(0, min(n - 1, int(round(t * (n - 1)))))
        return cv[i], radii[i]
    # buttress roots
    for k in range(5):
        a = TAU * k / 5 + rng.uniform(-0.2, 0.2) + variant
        L = rng.uniform(3.2, 4.4)
        limb(gb, [(math.cos(a) * 0.8, 1.8, math.sin(a) * 0.8), (math.cos(a) * L * 0.5, 0.5, math.sin(a) * L * 0.5), (math.cos(a) * L, -0.6, math.sin(a) * L)],
             0.82, 0.18, sides=5, per=2, power=0.8)
    # a lichened burl
    T2 = Tones(P, top="BarkPale", under="Bark")
    bp, br = trunk_at(0.3)
    T2.puff((bp[0] - br * 0.88, bp[1] + 0.2, bp[2] - 0.5), 0.75, 0.9, 0.7, rng, level=1, amp=0.25)
    # silk bands round the trunk: white ropes with a gold clasp and four hanging blue tassels each
    for bi, t in enumerate((0.14, 0.27, 0.42)):
        c, r = trunk_at(t)
        R = r * 1.1 + 0.12
        torus_loop(gs, (c[0], c[1], c[2]), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), R, 0.17, seg_u=10, seg_v=4)
        if bi == 1:
            a0 = -math.pi / 2
            cx, cz = c[0] + math.cos(a0) * (R + 0.02), c[2] - math.sin(a0) * (R + 0.02)
            K.box(gg, cx - 0.22, cx + 0.22, c[1] - 0.22, c[1] + 0.22, cz - 0.16, cz + 0.04, "TBNESW")
            for q in range(3):
                a = TAU * q / 3 + 0.5
                x, z = c[0] + math.cos(a) * (R + 0.04), c[2] - math.sin(a) * (R + 0.04)
                ln = 1.3 + 0.3 * (q % 2)
                K.box(gb2, x - 0.09, x + 0.09, c[1] - 0.1 - ln, c[1] - 0.1, z - 0.035, z + 0.035, "TBNESW")
                K.box(gg, x - 0.075, x + 0.075, c[1] - ln - 0.28, c[1] - ln - 0.08, z - 0.06, z + 0.06, "TBNESW")
    # limbs and crown
    top, rtop = trunk_at(1.0)
    if variant == 0:
        limbs = [(0.3, (4.6, 8.0, 1.6), (6.4, 10.6, 3.0)), (3.9, (-4.0, 7.4, -2.8), (-6.2, 10.0, -3.8)), (-1.4, (0.8, 8.6, -4.6), (1.6, 11.6, -6.6))]
    else:
        limbs = [(0.5, (4.2, 8.2, -1.8), (6.0, 11.0, -2.8)), (3.6, (-4.4, 7.6, 2.0), (-6.4, 10.2, 3.6)), (-1.0, (0.2, 7.0, -4.6), (-1.0, 7.8, -6.6))]
    crowns = []
    limb_pts = []
    for ai, (a_, mid, end) in enumerate(limbs):
        p0 = (top[0] + 0.4 * math.cos(a_), top[1] - 0.8 - 0.3 * ai, top[2] + 0.4 * math.sin(a_))
        pts = catmull([p0, (top[0] * 0.6 + mid[0] * 0.4, top[1] + 1.4, top[2] * 0.6 + mid[2] * 0.4), mid, end], 3)
        sweep(gb, pts, taper(len(pts), 0.95, 0.24, 0.85), 6, mod=lambda t, a: 1.0 + 0.1 * math.cos(3 * a + 2 * t))
        # a side twig
        p = pts[int(0.55 * (len(pts) - 1))]
        e = (p[0] + (1.5 if ai % 2 else -1.5), p[1] + 1.4, p[2] + (1.2 if ai else -1.2))
        limb(gb, [p, ((p[0] + e[0]) / 2, p[1] + 0.9, (p[2] + e[2]) / 2), e], 0.26, 0.1, sides=5, per=1)
        crowns.append((e, 2.4))
        crowns.append((end, 3.7 - 0.2 * ai))
        limb_pts.append(pts)
    # the crown: clusters of cloud pads (largest on the limb ends) and a top pad
    for ci, (e, R) in enumerate(crowns):
        cluster(T, (e[0], e[1] + 0.6, e[2]), R, 1.9 if R > 3 else 1.5, rng, n_out=2, puffs=1, yaw0=ci * 0.8, seg=9, lobes=5, amp=0.18, spread=0.6, ratio=0.9)
    cluster(T, (top[0], top[1] + 4.6, top[2]), 3.0, 1.6, rng, n_out=2, puffs=1, seg=9, lobes=5, amp=0.18, spread=0.58)
    if variant == 0:
        # the propping fork under the long low limb (lighter timber, lashed with blue silk): its two arms end inside the limb above
        gprop = P.geo("Prop")
        lp = limb_pts[0]
        u1 = lp[int(0.5 * (len(lp) - 1))]
        u2 = lp[int(0.32 * (len(lp) - 1))]
        u1 = (u1[0], u1[1] - 0.45, u1[2])
        u2 = (u2[0], u2[1] - 0.5, u2[2])
        base = (u1[0] + 1.3, -0.1, u1[2] + 0.5)
        mid = (base[0] * 0.6 + u1[0] * 0.4, 3.2, base[2] * 0.6 + u1[2] * 0.4)
        limb(gprop, [base, mid, u1], 0.3, 0.2, sides=6, per=2)
        fork = (mid[0] + 0.0, 3.4, mid[2] + 0.0)
        limb(gprop, [(fork[0], fork[1], fork[2]), ((fork[0] + u2[0]) / 2, (fork[1] + u2[1]) / 2, (fork[2] + u2[2]) / 2 + 0.1), u2], 0.17, 0.12, sides=5, per=2)
        torus_loop(gb2, (mid[0], 3.6, mid[2]), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0.34, 0.09, seg_u=10, seg_v=4)
    return P


# ======================================================================================================================
TREES = {
    "TierTreeA": lambda: tier_tree(0), "TierTreeB": lambda: tier_tree(1),
    "PlinthTreeA": lambda: plinth_tree(0), "PlinthTreeB": lambda: plinth_tree(1),
    "ArchTreeA": lambda: arch_tree(0), "ArchTreeB": lambda: arch_tree(1),
    "BasinTreeA": lambda: basin_tree(0), "BasinTreeB": lambda: basin_tree(1),
    "BoundTreeA": lambda: bound_tree(0), "BoundTreeB": lambda: bound_tree(1),
}


# ======================================================================================================================
# garden rocks (scholar's rocks): lofted, fluted columns, perforated by ring-shaped lobes, pale limestone
# ======================================================================================================================
def flute_mod(n, depth, phase, twist=0.0, second=0.12):
    return lambda t, a: 1.0 + depth * math.cos(n * a + twist * t + phase) + second * math.cos((n - 2) * a - 2.0 * t + phase * 0.7)


def column(g, path, radii, sides, mod, squash=0.85, per=3, caps=(True, True), dome=0.0):
    """A lofted column along `path`; dome > 0 rounds the top: over the last `dome` of its length the radius follows a quarter circle."""
    pts = catmull(path, per)
    n = len(pts)
    rs = []
    for i in range(n):
        t = i / (n - 1)
        r = radii(t)
        if dome and t > 1 - dome:
            u = (t - (1 - dome)) / dome
            r *= math.sqrt(max(0.05, 1 - u * u))
        rs.append(r)
    sweep(g, pts, rs, sides, mod=mod, squash=squash, caps=caps)


def rock_a():
    """Scholar's rock A, tall and perforated: a twisting fluted spire (8.6 tall) with a lower lobe leaning against it and a ring-shaped bridge of stone
    between them, whose open middle is the perforation (a hole about 1.5 across, clear straight through along z)."""
    P = Piece()
    rng = random.Random(201)
    g = P.geo("Stone")
    column(g, [(0.0, -0.4, 0.0), (-0.2, 2.2, 0.1), (0.35, 4.6, -0.1), (0.1, 6.8, 0.15), (0.5, 8.6, 0.0)],
           lambda t: (1.55 - 0.7 * t) * (0.66 + 0.34 * math.sin(2.0 * math.pi * t + 0.6)) + 0.7 * math.exp(-9 * t) + 0.3, 14, flute_mod(5, 0.3, 0.4, 3.0), per=4, dome=0.16)
    column(g, [(2.9, -0.43, 0.1), (2.7, 1.6, 0.0), (2.9, 3.6, -0.1), (3.3, 5.1, 0.05)],
           lambda t: 1.0 * (1 - 0.5 * t ** 1.4) + 0.2 + 0.35 * math.exp(-8 * t), 12, flute_mod(4, 0.26, 1.7, 2.0), per=4, dome=0.2)
    torus_loop(g, (1.5, 4.2, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 1.45, 0.6, seg_u=14, seg_v=5,
               rfun=lambda a: 0.58 + 0.16 * math.cos(2 * a + 0.8) + 0.08 * math.cos(5 * a))
    # a low skirt of stone round the foot, buried
    Tones(P, "Stone", "Stone").puff((1.5, 0.0, 0.0), 3.6, 0.95, 1.9, rng, level=1, amp=0.22, flat_under=0.6)
    return P


def rock_b():
    """Scholar's rock B, a fluted pillar: a slender twisting column (9.2 tall) with seven deep flutes, a swollen head and a narrow waist, a short
    companion spire at its side and two fallen fragments at its foot."""
    P = Piece()
    rng = random.Random(202)
    g = P.geo("Stone")
    column(g, [(0.0, -0.4, 0.0), (0.2, 2.0, -0.15), (-0.15, 4.2, 0.1), (0.2, 6.4, 0.0), (0.0, 7.8, 0.1), (0.25, 9.2, 0.0)],
           lambda t: 1.3 * (0.62 + 0.38 * math.cos(math.pi * min(1.0, t * 1.5))) * (1 - 0.3 * t) + 0.45 * math.sin(math.pi * max(0.0, (t - 0.6) / 0.3)) * (t > 0.6) + 0.55 * math.exp(-9 * t) + 0.08, 16,
           flute_mod(7, 0.3, 0.2, 4.0), squash=0.9, per=4, dome=0.12)
    column(g, [(1.9, -0.45, 0.5), (1.8, 1.1, 0.4), (1.95, 2.6, 0.5), (2.1, 3.7, 0.45)],
           lambda t: 0.8 * (1 - 0.55 * t ** 1.2) + 0.15 + 0.25 * math.exp(-8 * t), 11, flute_mod(5, 0.26, 2.0, 2.0), per=4, dome=0.2)
    st = Tones(P, "Stone", "Stone")
    st.puff((-1.5, 0.0, -0.9), 1.0, 0.6, 0.8, rng, level=1, amp=0.3, flat_under=0.7)
    st.puff((1.0, 0.0, -1.4), 0.7, 0.45, 0.6, rng, level=0, amp=0.25, flat_under=0.7)
    return P


def rock_c():
    """Scholar's rock C, a pair of peaks (7.2 and 4.8 tall) 3.2 apart, joined by a broad saddle with a small perforation through it."""
    P = Piece()
    rng = random.Random(203)
    g = P.geo("Stone")
    column(g, [(-1.4, -0.4, 0.0), (-1.55, 2.0, 0.1), (-1.2, 4.4, -0.1), (-1.5, 7.2, 0.05)],
           lambda t: 1.75 * (1 - 0.7 * t) * (0.62 + 0.38 * math.sin(math.pi * (0.15 + t * 0.7))) + 0.25 + 0.7 * math.exp(-9 * t), 13, flute_mod(5, 0.29, 0.9, 3.0), per=4, dome=0.18)
    column(g, [(1.7, -0.43, 0.2), (1.9, 1.7, 0.0), (1.6, 3.4, 0.1), (1.9, 4.8, 0.0)],
           lambda t: 1.4 * (1 - 0.65 * t) * (0.62 + 0.38 * math.sin(math.pi * (0.15 + t * 0.7))) + 0.22 + 0.6 * math.exp(-9 * t), 12, flute_mod(4, 0.3, 2.3, 2.5), per=4, dome=0.22)
    torus_loop(g, (0.15, 1.9, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.95, 0.5, seg_u=12, seg_v=5, rfun=lambda a: 0.5 + 0.12 * math.cos(3 * a))
    Tones(P, "Stone", "Stone").puff((0.2, 0.2, 0.0), 3.9, 1.3, 1.7, rng, level=1, amp=0.2, flat_under=0.6)
    return P


def rock_d():
    """Scholar's rock D, low and wide with a cave (3.9 tall, 8 across): a thick stone arch whose opening is the cave's mouth, a rear mass closing the
    tunnel (a grotto), and two lobes at its flanks."""
    P = Piece()
    rng = random.Random(204)
    g = P.geo("Stone")
    path = [(-2.6, -0.4, -0.3), (-2.5, 1.2, -0.3), (-1.6, 2.5, -0.3), (0.0, 3.0, -0.3), (1.6, 2.4, -0.3), (2.5, 1.1, -0.3), (2.7, -0.4, -0.3)]
    column(g, path, lambda t: 1.0 * (0.8 + 0.2 * math.sin(math.pi * t * 3)) + 0.2 * math.sin(math.pi * t), 11, flute_mod(4, 0.2, 0.3, 2.0), squash=1.05, per=3)
    T = Tones(P, "Stone", "Stone")
    T.puff((0.0, 1.3, 1.6), 3.6, 1.8, 1.9, rng, level=1, amp=0.24, flat_under=0.5)
    T.puff((-3.4, 0.4, 0.5), 1.5, 1.0, 1.3, rng, level=1, amp=0.3, flat_under=0.6)
    T.puff((3.5, 0.3, 0.2), 1.3, 0.8, 1.2, rng, level=1, amp=0.3, flat_under=0.6)
    return P


def rock_e():
    """Scholar's rock E, a leaning natural arch (7 tall, 6 across at the feet, tilted about 11 degrees): one fluted stone band that rises, bends over and
    comes down again, thick at the feet and thin at the crown."""
    P = Piece()
    rng = random.Random(205)
    g = P.geo("Stone")
    tilt = math.radians(11)
    c, s = math.cos(tilt), math.sin(tilt)
    raw = [(-2.7, -0.5, 0.0), (-2.9, 1.8, 0.1), (-2.0, 4.2, 0.0), (0.2, 6.3, -0.1), (2.3, 4.6, 0.0), (3.0, 2.0, 0.1), (3.0, -0.5, 0.0)]
    path = [(x * c - y * s, x * s + y * c, z) for x, y, z in raw]
    path = [(x, y + 0.5 * (1 - c) * 0 + 0.0, z) for x, y, z in path]
    low = min(p[1] for p in path)
    path = [(x, y - low - 0.5, z) for x, y, z in path]
    column(g, path, lambda t: 0.85 + 0.85 * (1 - math.sin(math.pi * t)) ** 1.5 + 0.2 * math.sin(math.pi * t * 5), 14, flute_mod(5, 0.26, 1.1, 2.0), squash=1.0, per=5)
    T = Tones(P, "Stone", "Stone")
    T.puff((path[0][0], 0.0, 0.2), 1.5, 0.7, 1.2, rng, level=1, amp=0.3, flat_under=0.7)
    T.puff((path[-1][0], 0.0, 0.0), 1.4, 0.7, 1.1, rng, level=1, amp=0.3, flat_under=0.7)
    return P


def stepping_stone(variant):
    """A stepping stone (about 3 x 2.5 x 0.5, a hint of tilt): a twelve-sided slab, a rim noise of its own, top slightly crowned."""
    P = Piece()
    rng = random.Random(230 + variant)
    g = P.geo("Stone")
    rx, rz = (1.5, 1.25) if variant == 0 else ((1.35, 1.3) if variant == 1 else (1.55, 1.15))
    ring = []
    for k in range(12):
        a = TAU * k / 12
        m = 1.0 + 0.1 * rng.uniform(-1, 1)
        ring.append((math.cos(a) * rx * m, math.sin(a) * rz * m))
    K.prism(g, ring, -0.3, 0.3, "TB")
    # tilt: the top ring and the cap lean a little (the stone is set a degree or two off level) and the crown is raised
    tl = (0.05 * (variant - 1), 0.05 * (1 - variant % 2))
    g.v = [(x, y + (0.06 + 0.02 * math.cos(1.0) if y > 0.0 else 0.0) + tl[0] * x * (y > 0) + tl[1] * z * (y > 0), z) for (x, y, z) in g.v]
    return P


ROCKS = {"ScholarA": rock_a, "ScholarB": rock_b, "ScholarC": rock_c, "ScholarD": rock_d, "ScholarE": rock_e,
         "SteppingStoneA": lambda: stepping_stone(0), "SteppingStoneB": lambda: stepping_stone(1), "SteppingStoneC": lambda: stepping_stone(2)}


# ======================================================================================================================
# plants and ground cover
# ======================================================================================================================
def petal(g, base, d, up, length, width, lift=0.0, thick=0.05):
    """A flat eight-triangle petal (an elongated octahedron): base, direction d, up vector, length, width; the middle swells by `thick`, the tip lifts."""
    side = vnorm(vcross(d, up))
    up = vnorm(vcross(side, d))
    m = vadd(base, vmul(d, length * 0.5))
    tip = vadd(vadd(base, vmul(d, length)), vmul(up, lift))
    ids = [g.vert(base), g.vert(vadd(m, vmul(side, width / 2))), g.vert(tip), g.vert(vadd(m, vmul(side, -width / 2))),
           g.vert(vadd(m, vmul(up, thick))), g.vert(vadd(m, vmul(up, -thick)))]
    b, l, t, r, T_, B_ = ids
    start = len(g.f)
    for a, c_ in ((b, l), (l, t), (t, r), (r, b)):
        g.face(a, c_, T_)
        g.face(c_, a, B_)
    K._orient_solid(g, start)


def blades(g, pts_list, r0, sides=3):
    for pts in pts_list:
        cv = catmull(pts, 2)
        sweep(g, cv, taper(len(cv), r0, 0.015, 0.9), sides, squash=0.45)


def hedge(variant):
    """A clipped azalea hedge. 0: a straight 6 stud module (flat ends: modules chain end to end); 1: an end module (3 studs, a rounded end); 2: a corner
    (two 3.4 stud arms round a 1.4 stud radius). Clipped, scalloped top; white-pink blooms pressed into the face (each sits on the exact surface)."""
    P = Piece()
    rng = random.Random(250 + variant)
    gl = P.geo("AzaleaLeaf")
    gb = P.geo("AzaleaBloom")
    ry, rz, cy = 1.25, 1.0, 1.15
    sides = 12
    if variant == 0:
        path = [(-3.0 + i, cy, 0.0) for i in range(7)]
        rad = lambda t: 1.0
    elif variant == 1:
        path = [(0.0 + 0.5 * i, cy, 0.0) for i in range(7)]
        rad = lambda t: 1.0 if t < 0.55 else max(0.12, math.sqrt(max(0.0, 1 - ((t - 0.55) / 0.45) ** 2)))
    else:
        path = [(3.4, cy, 0.0), (2.2, cy, 0.0), (1.1, cy, 0.0), (0.45, cy, 0.45), (0.0, cy, 1.1), (0.0, cy, 2.2), (0.0, cy, 3.4)]
        rad = lambda t: 1.0
    sq = lambda a: (abs(math.cos(a)) ** 4 + abs(math.sin(a)) ** 4) ** -0.25 * 0.97
    mod = lambda t, a: sq(a) * (1.0 + 0.1 * max(0.0, math.cos(a)) * math.cos(TAU * 3 * t + 0.6))
    n = len(path)
    radii = [rad(i / (n - 1)) * ry for i in range(n)]
    sweep(gl, path, radii, sides, mod=mod, squash=rz / ry, phase=math.pi / 12)
    T_, Ns, Bs = frames_along(path)

    def surf(i, a):
        t = i / (n - 1)
        f = mod(t, a)
        r = radii[i]
        p = vadd(path[i], vadd(vmul(Ns[i], math.cos(a) * r * f), vmul(Bs[i], math.sin(a) * r * f * rz / ry)))
        nrm = vnorm(vadd(vmul(Ns[i], math.cos(a) / max(r, 1e-6) / 1.0), vmul(Bs[i], math.sin(a) / max(r * rz / ry, 1e-6))))
        return p, nrm
    count = {0: 14, 1: 7, 2: 14}[variant]
    done = []
    tries = 0
    while len(done) < count and tries < 500:
        tries += 1
        i = rng.randint(1, n - 2) if variant != 1 else rng.randint(1, 3)
        a = rng.choice((rng.uniform(-0.9, 0.9), rng.uniform(math.pi / 2 - 0.5, math.pi / 2 + 0.3), rng.uniform(-math.pi / 2 - 0.3, -math.pi / 2 + 0.5)))
        p, nrm = surf(i, a)
        if any(vlen(vsub(p, q)) < 0.6 for q in done):
            continue
        done.append(p)
        s_ = 0.17 + 0.05 * rng.random()
        sd = vnorm(vcross(nrm, (0.0, 1.0, 0.013) if abs(nrm[1]) < 0.95 else (1.0, 0.0, 0.013)))
        up2 = vnorm(vcross(sd, nrm))
        base = vsub(p, vmul(nrm, 0.05))
        ids = [gb.vert(vadd(base, vmul(sd, s_))), gb.vert(vadd(base, vmul(up2, s_))), gb.vert(vadd(base, vmul(sd, -s_))), gb.vert(vadd(base, vmul(up2, -s_))),
               gb.vert(vadd(p, vmul(nrm, s_ * 0.9))), gb.vert(vsub(base, vmul(nrm, 0.05)))]
        st_ = len(gb.f)
        for a1, b1 in ((0, 1), (1, 2), (2, 3), (3, 0)):
            gb.face(ids[a1], ids[b1], ids[4])
            gb.face(ids[b1], ids[a1], ids[5])
        K._orient_solid(gb, st_)
    return P


def peony_bed():
    """A kerbed peony bed (5 x 3.2): a marble kerb, a soil bed, three clumps (leaf fans) each with one cupped bloom of two petal rings and a gold heart."""
    P = Piece()
    rng = random.Random(270)
    gm = P.geo("Plinth")
    so = P.geo("Soil")
    gl = P.geo("Leaf")
    gw = P.geo("PeonyWhite")
    gp = P.geo("PeonyBlush")
    gg = P.geo("Gold")
    x1, z1, t = 2.5, 1.6, 0.4
    K.box(gm, -x1, x1, -0.2, 0.8, -z1, -z1 + t, "TNESW")
    K.box(gm, -x1, x1, -0.2, 0.8, z1 - t, z1, "TNESW")
    K.box(gm, -x1, -x1 + t, -0.2, 0.8, -z1 + t, z1 - t, "TNESW")
    K.box(gm, x1 - t, x1, -0.2, 0.8, -z1 + t, z1 - t, "TNESW")
    K.box(so, -x1 + t, x1 - t, 0.0, 0.55, -z1 + t, z1 - t, "TNESW")
    for ci, (cx, cz, sc) in enumerate(((-1.35, 0.1, 1.0), (0.3, -0.35, 1.15), (1.5, 0.3, 0.9))):
        base = (cx, 0.52, cz)
        for k in range(4):   # the leaf fan
            a = TAU * k / 4 + ci
            petal(gl, (cx, 0.5, cz), (math.cos(a), 0.55, math.sin(a)), (0.0, 1.0, 0.0), 1.15 * sc, 0.5, lift=0.1, thick=0.05)
        top = (cx, 0.5 + 0.9 * sc, cz)
        for ring, (n, ln, wd, pitch) in enumerate(((5, 0.55, 0.42, 0.55), (4, 0.4, 0.34, 0.95))):
            for k in range(n):
                a = TAU * k / n + ring * 0.6 + ci
                d = vnorm((math.cos(a) * math.cos(pitch), math.sin(pitch), math.sin(a) * math.cos(pitch)))
                petal(gw if ring == 0 else gp, vadd(top, vadd((0.0, -0.05 * ring, 0.0), vmul(d, 0.02 + 0.012 * k))), d, (0.0, 1.0, 0.0), ln * sc, wd * sc, lift=0.05, thick=0.05)
        K.box(gg, cx - 0.13, cx + 0.13, top[1] - 0.08, top[1] + 0.2, cz - 0.13, cz + 0.13, "TBNESW")
        limb(P.geo("Leaf"), [(cx, 0.45, cz), (cx, 0.7, cz), top], 0.05, 0.04, sides=3, per=1)
    return P


def dwarf_pine():
    """An ornamental dwarf pine, cloud-pruned: a twisting short trunk rooted in a mossy stone, three flat needle pads stepping up and to the side."""
    P = Piece()
    rng = random.Random(280)
    gb = P.geo("Bark")
    T = Tones(P, "Needle", "Needle")
    st = Tones(P, "Stone", "Stone")
    st.puff((0.2, 0.0, 0.1), 1.25, 0.55, 1.0, rng, level=1, amp=0.3, flat_under=0.7)
    cv = catmull([(0.0, 0.2, 0.0), (-0.2, 0.9, 0.1), (0.2, 1.6, 0.0), (0.05, 2.3, -0.1)], 3)
    sweep(gb, cv, taper(len(cv), 0.26, 0.1, 0.9, flare=0.12), 6, mod=lambda t, a: 1.0 + 0.15 * math.cos(3 * a + 4 * t))
    limb(gb, [(-0.1, 1.0, 0.1), (-0.8, 1.35, 0.2), (-1.35, 1.5, 0.15)], 0.13, 0.06, sides=4, per=1)
    limb(gb, [(0.2, 1.6, 0.0), (0.8, 1.9, -0.1), (1.35, 2.0, -0.2)], 0.12, 0.06, sides=4, per=1)
    T.pad((-1.45, 1.75, 0.15), 1.05, 0.55, rng, seg=8, lobes=5, amp=0.22, ratio=0.9)
    T.pad((1.45, 2.25, -0.2), 0.95, 0.5, rng, seg=8, lobes=5, amp=0.22, ratio=0.9)
    T.pad((0.05, 2.85, -0.1), 1.2, 0.6, rng, seg=8, lobes=5, amp=0.22)
    T.puff((0.1, 3.3, -0.1), 0.5, 0.3, 0.5, rng, level=0, amp=0.25)
    return P


def lotus_basin():
    """A round lotus basin (5.2 across, 1.1 tall): a stone ring with a rolled lip, still water (Glass), four lily pads and two lotus flowers of eight
    petals with a gold heart."""
    P = Piece()
    rng = random.Random(290)
    gm = P.geo("Plinth")
    gw = P.geo("Water")
    gp = P.geo("LotusPad")
    gl = P.geo("LotusPetal")
    gg = P.geo("Gold")
    R = 2.6
    K.lathe(gm, [(R * 0.86, -0.3), (R * 0.96, 0.0), (R, 0.5), (R * 1.0, 1.0), (R * 0.96, 1.15), (R * 0.88, 1.12), (R * 0.82, 0.95), (R * 0.84, 0.7), (R * 0.8, 0.0), (R * 0.8, -0.3)], 12, loop=True)
    # the water disc (a single sheet resting against the basin's inner wall at 0.85)
    ids = [gw.vert((math.cos(TAU * k / 12) * R * 0.822, 0.8, math.sin(TAU * k / 12) * R * 0.822)) for k in range(12)]
    c = gw.vert((0.0, 0.8, 0.0))
    for k in range(12):
        gw.face(c, ids[(k + 1) % 12], ids[k])
    for (x, z, r, rot) in ((-0.9, -0.5, 0.62, 0.3), (0.8, 0.9, 0.58, 1.9), (0.5, -0.95, 0.5, 3.4), (-0.6, 1.0, 0.5, 5.0)):
        ring = []
        for k in range(7):
            a = rot + 0.35 + (TAU - 0.7) * k / 6
            ring.append((x + math.cos(a) * r, z + math.sin(a) * r))
        ring.append((x, z))
        K.prism(gp, ring[:-1] + [(x + math.cos(rot) * 0.05, z + math.sin(rot) * 0.05)], 0.74, 0.86, "TB")
    for fi, (x, z) in enumerate(((0.1, 0.0), (-0.1, 1.05))):
        top = (x, 0.95 + 0.25 * fi, z)
        for ring, (n, ln, wd, pitch) in enumerate(((7, 0.62, 0.34, 0.5), (4, 0.45, 0.3, 0.95))):
            for k in range(n):
                a = TAU * k / n + ring * 0.4 + fi
                d = vnorm((math.cos(a) * math.cos(pitch), math.sin(pitch), math.sin(a) * math.cos(pitch)))
                petal(gl, vadd(top, vmul(d, 0.02 + 0.012 * k)), d, (0.0, 1.0, 0.0), ln, wd, lift=0.05, thick=0.045)
        K.box(gg, x - 0.14, x + 0.14, top[1] - 0.09, top[1] + 0.22, z - 0.14, z + 0.14, "TBNESW")
    return P


def white_iris():
    """A clump of white iris (about 2.4 across, 3.2 tall): seven arching sword leaves and three stems each with a flower of three upright and three
    falling petals."""
    P = Piece()
    rng = random.Random(300)
    gl = P.geo("IrisLeaf")
    gw = P.geo("IrisWhite")
    gg = P.geo("Gold")
    ps = []
    for k in range(7):
        a = TAU * k / 7 + 0.3
        ln = 2.0 + 0.5 * ((k * 3) % 4) / 3
        ps.append([(math.cos(a) * (0.05 + 0.07 * (k % 3)), -0.05 - 0.006 * k, math.sin(a) * (0.05 + 0.07 * (k % 3))), (math.cos(a) * 0.25, ln * 0.4, math.sin(a) * 0.25),
                   (math.cos(a) * (0.55 + 0.2 * (k % 2)), ln * 0.78, math.sin(a) * (0.55 + 0.2 * (k % 2))), (math.cos(a) * (1.05 + 0.3 * (k % 3) / 2), ln * 0.92, math.sin(a) * (1.05 + 0.3 * (k % 3) / 2))])
    blades(gl, ps, 0.13)
    for k, (sx, sz, h) in enumerate(((0.1, 0.0, 2.9), (-0.35, 0.3, 2.45), (0.4, -0.3, 2.2))):
        stem = catmull([(sx * 0.3, -0.12 - 0.013 * k, sz * 0.3), (sx * 0.6, h * 0.55, sz * 0.6), (sx, h, sz)], 2)
        sweep(gl, stem, taper(len(stem), 0.05, 0.035, 1.0), 4, phase=0.3 + 0.8 * k)
        top = (sx, h, sz)
        for q in range(3):
            a = TAU * q / 3 + k
            petal(gw, vadd(top, (math.cos(a) * 0.03, 0.0, math.sin(a) * 0.03)), vnorm((math.cos(a) * 0.35, 0.95, math.sin(a) * 0.35)), (0.0, 1.0, 0.0), 0.5, 0.3, lift=0.0, thick=0.04)
            petal(gw, vadd(top, (math.cos(a + 0.9) * 0.05, -0.02, math.sin(a + 0.9) * 0.05)), vnorm((math.cos(a + 0.9) * 0.9, -0.35, math.sin(a + 0.9) * 0.9)), (0.0, 1.0, 0.0), 0.5, 0.32, lift=-0.1, thick=0.04)
        K.box(gg, sx - 0.1, sx + 0.1, h - 0.08, h + 0.12, sz - 0.1, sz + 0.1, "TBNESW")
    return P


def shrub():
    """A clipped round shrub (about 3 across, 2.2 tall) of three overlapping lobes, with a scatter of white blooms."""
    P = Piece()
    rng = random.Random(310)
    T = Tones(P, "AzaleaLeaf", "AzaleaLeaf")
    gb = P.geo("AzaleaBloom")
    T.puff((0.0, 0.95, 0.0), 1.45, 1.15, 1.35, rng, level=1, amp=0.14, flat_under=0.6)
    T.puff((-0.85, 0.8, 0.35), 0.9, 0.8, 0.9, rng, level=0, amp=0.18, flat_under=0.6)
    T.puff((0.9, 0.75, -0.3), 0.85, 0.75, 0.85, rng, level=0, amp=0.18, flat_under=0.6)
    for k in range(8):
        a = rng.uniform(0, TAU)
        e = rng.uniform(0.2, 1.0)
        n = vnorm((math.cos(a) * (1 - e * 0.5), e * 0.9, math.sin(a) * (1 - e * 0.5)))
        loc = (n[0] * 1.38, 0.95 + n[1] * 1.12, n[2] * 1.28)
        s_ = 0.16
        sd = vnorm(vcross(n, (0.0, 1.0, 0.01)))
        up2 = vnorm(vcross(sd, n))
        base = vsub(loc, vmul(n, 0.06))
        ids = [gb.vert(vadd(base, vmul(sd, s_))), gb.vert(vadd(base, vmul(up2, s_))), gb.vert(vadd(base, vmul(sd, -s_))), gb.vert(vadd(base, vmul(up2, -s_))),
               gb.vert(vadd(loc, vmul(n, s_ * 0.9))), gb.vert(vsub(base, vmul(n, 0.06)))]
        st_ = len(gb.f)
        for a1, b1 in ((0, 1), (1, 2), (2, 3), (3, 0)):
            gb.face(ids[a1], ids[b1], ids[4])
            gb.face(ids[b1], ids[a1], ids[5])
        K._orient_solid(gb, st_)
    return P


def _inside_poly(x, z, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def petal_drift(variant):
    """A patch of fallen petals (7 to 10 across, 0.06 over the ground): a thin irregular pink carpet and petals hinged on it, pink and white, tilted off
    it. One connected sheet of geometry (every petal shares its base edge with the carpet)."""
    P = Piece()
    rng = random.Random(330 + variant)
    gc = P.geo("PetalPink")
    gw = P.geo("PetalWhite")
    R = (6.0, 7.4, 8.8)[variant]
    npet = (46, 56, 70)[variant]
    top = 0.06
    ring_t, ring_b = [], []
    n = 12
    shapes = [[0.62, 1.0, 0.82, 0.95, 0.55, 0.9, 1.0, 0.72, 0.9, 0.6, 1.0, 0.8],
              [0.9, 0.7, 1.0, 0.6, 0.95, 0.85, 0.65, 1.0, 0.75, 0.95, 0.6, 0.9],
              [1.0, 0.8, 0.62, 0.9, 1.0, 0.7, 0.95, 0.6, 0.85, 1.0, 0.74, 0.9]][variant]
    for k in range(n):
        a = TAU * k / n
        r = R * 0.62 * shapes[k]
        ring_t.append(gc.vert((math.cos(a) * r, top, math.sin(a) * r)))
        ring_b.append(gc.vert((math.cos(a) * r * 1.02, 0.018, math.sin(a) * r * 1.02)))
    ct, cb = gc.vert((0.0, top, 0.0)), gc.vert((0.0, 0.018, 0.0))
    for k in range(n):
        j = (k + 1) % n
        gc.face(ct, ring_t[j], ring_t[k])
        gc.face(cb, ring_b[k], ring_b[j])
        gc.face(ring_b[k], ring_t[k], ring_t[j], ring_b[j])
    # petals hinged on the carpet's top: pink and white, scattered inside the carpet
    placed = []
    tries = 0
    while len(placed) < npet and tries < 4000:
        tries += 1
        a = rng.uniform(0, TAU)
        r = R * 0.55 * math.sqrt(rng.uniform(0.0, 1.0))
        # stay inside the carpet's outline (its radius at that angle)
        x, z = math.cos(a) * r, math.sin(a) * r
        if not _inside_poly(x, z, [(math.cos(TAU * q / n) * R * 0.62 * shapes[q] * 0.8, math.sin(TAU * q / n) * R * 0.62 * shapes[q] * 0.8) for q in range(n)]):
            continue
        if any(math.hypot(x - px, z - pz) < 0.5 for px, pz in placed):
            continue
        placed.append((x, z))
    for i, (x, z) in enumerate(placed):
        ang = rng.uniform(0, TAU)
        d = (math.cos(ang), 0.0, math.sin(ang))
        sd = (-d[2], 0.0, d[0])
        ln = rng.uniform(0.4, 0.62)
        wd = ln * rng.uniform(0.6, 0.8)
        g = gw if (i % 3 == 0) else gc
        if g is gc:
            g = gw if i % 2 else P.geo("PetalPink")
        g = gw if i % 3 != 1 else gc
        b0 = g.vert((x - sd[0] * wd * 0.2, top, z - sd[2] * wd * 0.2))
        b1 = g.vert((x + sd[0] * wd * 0.2, top, z + sd[2] * wd * 0.2))
        o0 = g.vert((x + d[0] * ln - sd[0] * wd / 2, top + 0.07, z + d[2] * ln - sd[2] * wd / 2))
        o1 = g.vert((x + d[0] * ln + sd[0] * wd / 2, top + 0.07, z + d[2] * ln + sd[2] * wd / 2))
        m = g.vert((x + d[0] * ln * 0.55, top + 0.045, z + d[2] * ln * 0.55))
        s0 = len(g.f)
        g.face(b0, b1, o1, o0)
        # make the sheet face up
        f = g.f[-1]
        pa, pb, pc = (g.v[q] for q in f[:3])
        nn = vcross(vsub(pb, pa), vsub(pc, pa))
        if nn[1] < 0:
            g.f[-1] = tuple(reversed(f))
    return P


def gravel_rake(variant):
    """A raked gravel patch. 0: 6 x 4, six raked ridges flowing round a stone; 1: round, 6 across, three concentric ridges round a stone. The
    ridges are geometry."""
    P = Piece()
    rng = random.Random(350 + variant)
    gg = P.geo("Gravel")
    gs = P.geo("Stone")
    if variant == 0:
        K.box(gg, -3.0, 3.0, -0.05, 0.1, -2.0, 2.0, "TNESW")
        sx_, sz_ = 1.2, 0.0
        for i in range(6):
            z0 = -1.375 + 0.55 * i
            pts = []
            for q in range(7):
                x = -2.8 + 5.6 * q / 6
                s = 1.0 if z0 >= 0 else -1.0
                dz = s * 0.5 * math.exp(-((x - sx_) / 0.95) ** 2) * math.exp(-(abs(z0) / 1.05) ** 2)
                pts.append((x, 0.1, z0 + dz))
            sweep(gg, pts, [0.1] * 7, 4, squash=1.8, caps=(True, True), phase=math.pi / 4)
        Tones(P, "Stone", "Stone").puff((sx_, 0.12, 0.0), 0.62, 0.42, 0.5, rng, level=0, amp=0.28, flat_under=0.5)
    else:
        ring = [(math.cos(TAU * k / 12) * 3.0, math.sin(TAU * k / 12) * 3.0) for k in range(12)]
        K.prism(gg, ring, -0.05, 0.1, "TB")
        for r in (1.1, 1.8, 2.5):
            torus_loop(gg, (0.0, 0.1, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), r, 0.1, seg_u=14, seg_v=3)
        Tones(P, "Stone", "Stone").puff((0.0, 0.12, 0.0), 0.62, 0.45, 0.55, rng, level=1, amp=0.28, flat_under=0.5)
    return P


def moss_tuft(variant):
    """A tuft of moss (about 1.4 across, 0.4 tall): flattened faceted lobes."""
    P = Piece()
    rng = random.Random(370 + variant)
    T = Tones(P, "Moss", "Moss")
    for k in range(5 + variant):
        a = TAU * k / (5 + variant) + rng.uniform(-0.4, 0.4)
        r = 0.0 if k == 0 else 0.45 + 0.1 * rng.random()
        T.puff((math.cos(a) * r, 0.08, math.sin(a) * r), 0.36 + 0.1 * rng.random(), 0.17, 0.34, rng, level=0, amp=0.3, yaw=rng.uniform(0, TAU), flat_under=0.6)
    return P


PLANTS = {"AzaleaHedge6": lambda: hedge(0), "AzaleaHedgeEnd": lambda: hedge(1), "AzaleaHedgeCorner": lambda: hedge(2), "PeonyBed": peony_bed, "DwarfPine": dwarf_pine,
          "LotusBasin": lotus_basin, "WhiteIris": white_iris, "ClippedShrub": shrub,
          "PetalDriftA": lambda: petal_drift(0), "PetalDriftB": lambda: petal_drift(1), "PetalDriftC": lambda: petal_drift(2),
          "GravelRakeRect": lambda: gravel_rake(0), "GravelRakeRound": lambda: gravel_rake(1), "MossTuftA": lambda: moss_tuft(0), "MossTuftB": lambda: moss_tuft(1)}


FAMILIES = [("Trees", TREES), ("Rocks", ROCKS), ("Plants", PLANTS)]

USE = {
    "TierTree": "terrace and garden court focal tree: stands alone on a lawn or terrace corner, 8 studs of crown radius (lay a 10 stud keep-out)",
    "PlinthTree": "a prized specimen on its own plinth: on a court side, beside a pavilion or a path end; the plinth is the foot (set it on level paving)",
    "ArchTree": "straddles a stair or a path (the path runs along the piece's z axis, clear width 10 / 14 studs between the trunk feet): one per stair, bridge head or gate",
    "BasinTree": "a potted weeping tree for a court corner, terrace edge or beside a door; the basin sits on level paving",
    "BoundTree": "THE focal tree of the territory (the residence court or the main garden's heart): at most one or two; the prop and the silk ribbons are part of it",
    "ScholarA": "a scholar's rock for gardens, court corners and pond edges (perforated; the hole runs along z)",
    "ScholarB": "a fluted pillar rock for terrace edges and stair heads",
    "ScholarC": "a pair-of-peaks rock for the pond and the garden's rear",
    "ScholarD": "a low grotto rock for the water's edge (the cave mouth faces -z)",
    "ScholarE": "a leaning rock arch: a garden gateway over a path, or a pond feature (the opening runs along z)",
    "SteppingStone": "lawn and moss stepping stones: lay in a line, 4.5 studs apart, yaw randomly, sunk so the top is 0.2 over the ground",
    "AzaleaHedge6": "a 6 stud clipped hedge: chain end to end along a path or round a lawn",
    "AzaleaHedgeEnd": "closes a chain of hedge modules with a rounded end",
    "AzaleaHedgeCorner": "an L-shaped corner (two 3.4 stud arms) for a hedge that turns",
    "PeonyBed": "a kerbed peony bed on a court or a lawn edge",
    "DwarfPine": "an ornamental dwarf pine for terraces, beside rocks and on plinth corners",
    "LotusBasin": "a lotus basin for a court or the tea terrace (the Water sheet is Glass)",
    "WhiteIris": "a white iris clump at the water's edge, at the foot of a rock and beside steps",
    "ClippedShrub": "a clipped round shrub with white blooms: in pairs by doors and at path forks",
    "PetalDrift": "a patch of fallen petals on the ground under a cherry tree (no collision; lay on the terrain, y 0.06; sink 0.02)",
    "GravelRake": "a raked gravel garden patch (rectangle or round) with its stone, on a court or a terrace floor",
    "MossTuft": "a moss tuft at the foot of rocks, in stair joints and at the lawn's edge",
}


def use_for(name):
    base = name.split("_", 2)[2]
    for key, text in USE.items():
        if base.startswith(key):
            return text
    return ""


def _shift(piece, dx, dz):
    for g in piece.g.values():
        g.v = [(x + dx, y, z + dz) for (x, y, z) in g.v]


def _footprint_centre(piece, ymax):
    xs, zs = [], []
    for g in piece.g.values():
        for (x, y, z) in g.v:
            if y < ymax:
                xs.append(x)
                zs.append(z)
    return (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2


def _verts(piece):
    return [v for g in piece.g.values() for v in g.v]


def _box_of(vs, y0, y1, shrink, ymin_floor=0.0):
    sel = [v for v in vs if y0 <= v[1] <= y1]
    xs = [v[0] for v in sel]
    zs = [v[2] for v in sel]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    hx, hz = (max(xs) - min(xs)) / 2 * (1 - shrink), (max(zs) - min(zs)) / 2 * (1 - shrink)
    return {"x0": round(cx - hx, 2), "x1": round(cx + hx, 2), "y0": round(max(ymin_floor, y0), 2), "y1": round(y1, 2), "z0": round(cz - hz, 2), "z1": round(cz + hz, 2)}


def collision_for(name, piece):
    """Invisible colliders in the piece's frame, a little smaller than what you see: trunk or plinth or rock core. Ground cover and plants: none."""
    base = name.split("_", 2)[2]
    vs = _verts(piece)
    if base.startswith("TierTree"):
        return [_box_of(vs, -0.5, 5.0, 0.0) if False else {"x0": -0.95, "x1": 0.95, "y0": 0.0, "y1": 5.2, "z0": -0.95, "z1": 0.95}]
    if base.startswith("PlinthTree"):
        if base.endswith("A"):
            return [{"x0": -2.8, "x1": 2.8, "y0": 0.0, "y1": 2.0, "z0": -2.8, "z1": 2.8}]
        return [{"x0": -2.0, "x1": 2.0, "y0": 0.0, "y1": 3.2, "z0": -2.0, "z1": 2.0}]
    if base.startswith("ArchTree"):
        foot = 5.9 if base.endswith("A") else 8.0
        return [{"x0": s * foot - 0.85, "x1": s * foot + 0.85, "y0": 0.0, "y1": 4.0, "z0": -0.85, "z1": 0.85} for s in (-1, 1)]
    if base.startswith("BasinTree"):
        return [{"x0": -1.6, "x1": 1.6, "y0": 0.0, "y1": 2.0, "z0": -1.6, "z1": 1.6}]
    if base.startswith("BoundTree"):
        return [{"x0": -1.5, "x1": 1.5, "y0": 0.0, "y1": 4.2, "z0": -1.5, "z1": 1.5}]
    if base.startswith("Scholar"):
        lo, hi = piece.bounds()
        H = hi[1]
        if base == "ScholarD":
            return [_box_of(vs, 0.0, H * 0.85, 0.25) | {"z0": 0.2, "z1": round(hi[2] - 0.5, 2)}] + [
                {"x0": round(lo[0] + 0.6, 2), "x1": -1.6, "y0": 0.0, "y1": 2.4, "z0": -0.9, "z1": 0.9}, {"x0": 1.6, "x1": round(hi[0] - 0.6, 2), "y0": 0.0, "y1": 2.4, "z0": -0.9, "z1": 0.9}]
        if base == "ScholarE":
            legs = []
            for sgn in (-1, 1):
                sel = [v for v in vs if v[1] < 3.0 and v[0] * sgn > 0]
                xs, zs = [v[0] for v in sel], [v[2] for v in sel]
                legs.append({"x0": round(min(xs) + 0.35, 2), "x1": round(max(xs) - 0.35, 2), "y0": 0.0, "y1": 3.0, "z0": round(min(zs) + 0.3, 2), "z1": round(max(zs) - 0.3, 2)})
            return legs
        return [_box_of(vs, 0.0, H * 0.5, 0.28), _box_of(vs, H * 0.5, H * 0.72, 0.5)]
    return []


def meta_for(name, piece):
    fam, base = name.split("_", 2)[1], name.split("_", 2)[2]
    lo, hi = piece.bounds()
    vs = _verts(piece)
    foot = [v for v in vs if v[1] < 1.2]
    variant = base[-1] if base[-1] in "ABC" and base not in ("AzaleaHedge6",) else ""
    return {"family": fam, "piece": base, "variant": variant, "tris": piece.tris(), "materials": {k: v for k, v in sorted(piece.stats().items())},
            "bounds_min": [round(c, 2) for c in lo], "bounds_max": [round(c, 2) for c in hi],
            "radius": round(max(math.hypot(v[0], v[2]) for v in foot), 2) if foot else 0.0, "crown_radius": round(max(math.hypot(v[0], v[2]) for v in vs), 2),
            "height": round(hi[1], 2), "collision": collision_for(name, piece), "use": use_for(name)}


def build_all():
    pieces = {}
    meta = {}
    for fam, table in FAMILIES:
        for name, fn in table.items():
            p = fn()
            p.finish()
            full = "Dawnspire_%s_%s" % (fam, name)
            if fam == "Rocks" and not name.startswith("Stepping"):
                cx, cz = _footprint_centre(p, 0.8)
                _shift(p, -cx, -cz)
            pieces[full] = p
    for full, p in pieces.items():
        meta[full] = meta_for(full, p)
    return {"pieces": pieces, "meta": meta, "looks": LOOKS}


if __name__ == "__main__":
    total = 0
    for name, p in build_all()["pieces"].items():
        lo, hi = p.bounds()
        total += p.tris()
        print("%-40s %5d tris  %s  bounds %s %s" % (name, p.tris(), p.stats(), [round(v, 1) for v in lo], [round(v, 1) for v in hi]))
    print("sum of one of each", total)

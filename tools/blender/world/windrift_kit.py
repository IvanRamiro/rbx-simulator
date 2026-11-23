"""windrift_kit: the geometry kit of Windrift Hold, the Unorthodox territory (2026-11-23). Plain Python, no Blender.

Built on hq_kit's containers (Geo = indexed faces, Piece = material suffix -> Geo) and nothing else of the other territories' architecture: Dawnspire's
dougong brackets, flying eaves, marble and gold are not here. Windrift's shape language is its own:
  * dark-jade slate stone laid in battered rubble courses (stone_wall, podium), timber on stone, never marble;
  * overlapping roof tiles as SAWTOOTH COURSES (every course a thin wedge whose lip steps out over the one below, ragged at the ends, no two the same),
    roofs that lean: a long low slope one side and a short steep one the other, a ridge off the middle, ends that do not line up (roof_plane, gable);
  * timber frames that are racked a degree or two (lean_piece), stilts with X braces, stacked corbels under cantilevers, rope and bamboo scaffold,
    muted-bronze bands and caps on everything that matters (they join one `Bronze` mesh per piece).
Everything is authored in ROBLOX STUDS: x right, y up, z back (a piece's FRONT is -Z), the piece's origin at its floor line (y = 0 is the floor; podium
feet sink below). A piece has at most four material suffixes (Stone, Timber, Tile, Bronze, Cloth, Rope, Plank, Lamp, Bamboo: choose four).
Collision is never the visual mesh: every builder also lists invisible boxes (piece.col) and named points (piece.marks).
"""
import math
import random

import hq_kit as K
from hq_kit import Geo, Piece, vadd, vsub, vmul, vdot, vcross, vnorm, vlen, lerp, TAU

S_STONE, S_TIMBER, S_TILE, S_BRONZE = "Stone", "Timber", "Tile", "Bronze"
S_CLOTH, S_ROPE, S_PLANK, S_LAMP, S_BAMBOO, S_WATER = "Cloth", "Rope", "Plank", "Lamp", "Bamboo", "Water"


class WP(Piece):
    """A Piece that also carries its collision boxes (x0, x1, y0, y1, z0, z1, name), named points and light spots in its own frame."""

    def __init__(self):
        super().__init__()
        self.col = []
        self.marks = {}
        self.lights = []
        self.floor = []            # (x0, x1, z0, z1, y): walkable floors for the walk check and the paving (a footprint)

    def finish(self):
        """Drops faces that duplicate another face of the same mesh exactly (two builders that both made the same post at a corner), then Piece.finish."""
        for g in self.g.values():
            seen = set()
            keep = []
            for f in g.f:
                key = tuple(sorted((round(g.v[i][0] * 5000), round(g.v[i][1] * 5000), round(g.v[i][2] * 5000)) for i in f))
                if key in seen:
                    continue
                seen.add(key)
                keep.append(f)
            g.f = keep
        super().finish()
        self.resolve_planes()
        self.resolve_exact()
        return self

    def resolve_planes(self, passes=16, step=0.0045, tol=0.0028):
        """The asset QA fails two faces that lie in one plane, look the same way and overlap (z-fighting), also between two meshes of a piece. Solids of one building are
        often made to the same round numbers (a post and a wall plate, two courses of the same block height), so: every solid (a connected shell, across all meshes) that has
        an axis-aligned face in the plane of another solid's face, both facing the same way and overlapping, is moved a hair (4.5 thousandths of a stud) out along that face's
        normal; repeated until no pair is left. The moves are far below anything visible and a solid keeps overlapping what it overlapped."""
        for _ in range(passes):
            comp_of = {}
            comps = []
            for gi, g in enumerate(self.g.values()):
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
                roots = {}
                for i in range(len(g.v)):
                    roots.setdefault(find(i), []).append(i)
                for r, idx in roots.items():
                    comps.append((g, idx))
                    for i in idx:
                        comp_of[(id(g), i)] = len(comps) - 1
            faces = []
            for g in self.g.values():
                for f in g.f:
                    pts = [g.v[i] for i in f]
                    n = vcross(vsub(pts[1], pts[0]), vsub(pts[2], pts[0]))
                    ln = vlen(n)
                    if ln < 1e-9:
                        continue
                    n = (n[0] / ln, n[1] / ln, n[2] / ln)
                    d = n[0] * pts[0][0] + n[1] * pts[0][1] + n[2] * pts[0][2]
                    ax = max(range(3), key=lambda a: abs(n[a]))
                    o = [a for a in range(3) if a != ax]
                    faces.append((n, d, min(p[o[0]] for p in pts), max(p[o[0]] for p in pts), min(p[o[1]] for p in pts), max(p[o[1]] for p in pts),
                                  comp_of[(id(g), f[0])], ax))
            buckets = {}
            for fi, fc in enumerate(faces):
                key = (round(fc[0][0] * 40), round(fc[0][1] * 40), round(fc[0][2] * 40))
                buckets.setdefault(key, []).append(fi)
            moves = {}
            for key, idx in buckets.items():
                near = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            near += buckets.get((key[0] + dx, key[1] + dy, key[2] + dz), [])
                for fi in idx:
                    a = faces[fi]
                    for fj in near:
                        b = faces[fj]
                        if b[6] <= a[6] or b[7] != a[7]:
                            continue
                        if abs(a[1] - b[1]) > tol or a[0][0] * b[0][0] + a[0][1] * b[0][1] + a[0][2] * b[0][2] < 0.9999:
                            continue
                        if min(a[3], b[3]) - max(a[2], b[2]) > 0.0004 and min(a[5], b[5]) - max(a[4], b[4]) > 0.0004:
                            moves[b[6]] = a[0]
            if not moves:
                break
            st = step * (1.0 + 0.41 * (_ % 5))
            for ci, nrm in moves.items():
                g, idx = comps[ci]
                for i in idx:
                    p = g.v[i]
                    g.v[i] = (p[0] + nrm[0] * st, p[1] + nrm[1] * st, p[2] + nrm[2] * st)
        return self

    def resolve_exact(self, passes=14, step=0.0046, eps=0.0011):
        """The QA's own z-fighting test, replayed on the finished piece: sample points of every face (the centroid and the points 60 percent of the way to each corner of each
        triangle of both ways of cutting a quad), any other solid's face within eps of one of them that faces the same way (dot of the normals 0.999 or more) and whose plane
        carries the point inside it is a conflict; the later solid is moved `step` along that face's normal."""
        for ps in range(passes):
            faces = []
            comp_of = {}
            ncomp = 0
            gmap = {}
            for g in self.g.values():
                gmap[id(g)] = g
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
                roots = {}
                for i in range(len(g.v)):
                    roots.setdefault(find(i), ncomp + len(roots))
                for i in range(len(g.v)):
                    comp_of[(id(g), i)] = roots[find(i)]
                ncomp += len(roots)
                for f in g.f:
                    pts = [g.v[i] for i in f]
                    n = vcross(vsub(pts[1], pts[0]), vsub(pts[2], pts[0]))
                    ln = vlen(n)
                    if ln < 1e-9:
                        continue
                    n = (n[0] / ln, n[1] / ln, n[2] / ln)
                    faces.append((pts, n, comp_of[(id(g), f[0])]))
            cell = 1.0
            grid = {}
            for fi, (pts, n, cid) in enumerate(faces):
                lo = [min(p[a] for p in pts) - eps for a in range(3)]
                hi = [max(p[a] for p in pts) + eps for a in range(3)]
                for ix in range(int(math.floor(lo[0] / cell)), int(math.floor(hi[0] / cell)) + 1):
                    for iy in range(int(math.floor(lo[1] / cell)), int(math.floor(hi[1] / cell)) + 1):
                        for iz in range(int(math.floor(lo[2] / cell)), int(math.floor(hi[2] / cell)) + 1):
                            grid.setdefault((ix, iy, iz), []).append(fi)
            moves = {}

            def inside(q, pts):
                a = pts[0]
                for t in range(1, len(pts) - 1):
                    b, c = pts[t], pts[t + 1]
                    v0, v1, v2 = vsub(c, a), vsub(b, a), vsub(q, a)
                    d00, d01, d02, d11, d12 = vdot(v0, v0), vdot(v0, v1), vdot(v0, v2), vdot(v1, v1), vdot(v1, v2)
                    den = d00 * d11 - d01 * d01
                    if abs(den) < 1e-14:
                        continue
                    uu = (d11 * d02 - d01 * d12) / den
                    vv = (d00 * d12 - d01 * d02) / den
                    if uu >= -1e-6 and vv >= -1e-6 and uu + vv <= 1 + 1e-6:
                        return True
                return False
            for fi, (pts, n, ca) in enumerate(faces):
                tri_sets = [(pts[0], pts[1], pts[2])]
                if len(pts) == 4:
                    tri_sets += [(pts[0], pts[2], pts[3]), (pts[1], pts[2], pts[3]), (pts[0], pts[1], pts[3])]
                samples = []
                for (a, b, c) in tri_sets:
                    cen = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3)
                    samples.append(cen)
                    for v in (a, b, c):
                        samples.append((cen[0] + (v[0] - cen[0]) * 0.6, cen[1] + (v[1] - cen[1]) * 0.6, cen[2] + (v[2] - cen[2]) * 0.6))
                for p in samples:
                    for fj in grid.get((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell)), int(math.floor(p[2] / cell))), ()):
                        u = faces[fj]
                        if u[2] == ca:
                            continue
                        n2 = u[1]
                        if n[0] * n2[0] + n[1] * n2[1] + n[2] * n2[2] < 0.999:
                            continue
                        dist = n2[0] * (p[0] - u[0][0][0]) + n2[1] * (p[1] - u[0][0][1]) + n2[2] * (p[2] - u[0][0][2])
                        if abs(dist) > eps:
                            continue
                        q = (p[0] - n2[0] * dist, p[1] - n2[1] * dist, p[2] - n2[2] * dist)
                        if inside(q, u[0]):
                            if u[2] > ca:
                                moves[u[2]] = n2
                            else:
                                moves[ca] = n
            if not moves:
                break
            by_comp = {}
            for (gid, vi), cid in comp_of.items():
                by_comp.setdefault(cid, []).append((gid, vi))
            st = step * (1.0 + 0.37 * (ps % 4))
            for cid, nrm in moves.items():
                for (gid, vi) in by_comp[cid]:
                    g = gmap[gid]
                    p = g.v[vi]
                    g.v[vi] = (p[0] + nrm[0] * st, p[1] + nrm[1] * st, p[2] + nrm[2] * st)
        return self

    def block(self, name, x0, x1, y0, y1, z0, z1):
        self.col.append((x0, x1, y0, y1, z0, z1, name))

    def absorb(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0):
        """Merges another WP (geometry, boxes, marks) transformed by yaw about y then t. Boxes keep axis alignment only for yaw multiples of 90 degrees."""
        self.add(other, t=t, yaw=yaw, s=s)
        c, sn = math.cos(yaw), math.sin(yaw)
        for (x0, x1, y0, y1, z0, z1, n) in other.col:
            pts = [(px * c + pz * sn, -px * sn + pz * c) for px in (x0, x1) for pz in (z0, z1)]
            self.col.append((min(p[0] for p in pts) + t[0], max(p[0] for p in pts) + t[0], y0 + t[1], y1 + t[1], min(p[1] for p in pts) + t[2],
                             max(p[1] for p in pts) + t[2], n))
        for k, v in other.marks.items():
            x, z = v[0] * c + v[2] * sn, -v[0] * sn + v[2] * c
            self.marks[k] = (x + t[0], v[1] + t[1], z + t[2])
        return self


# ======================================================================================================================
# solids
# ======================================================================================================================
def hex8(g, p):
    """A solid from eight points: a bottom ring p0..p3 (as hq_kit.hexa: (x0,z0), (x1,z0), (x1,z1), (x0,z1)) and a top ring p4..p7 above them."""
    b = [g.vert(q) for q in p[:4]]
    t = [g.vert(q) for q in p[4:]]
    g.face(b[0], b[1], b[2], b[3])
    g.face(t[3], t[2], t[1], t[0])
    for i in range(4):
        j = (i + 1) % 4
        g.face(b[i], t[i], t[j], b[j])


def axes_of(a, b, up=(0.0, 1.0, 0.0)):
    """Orthonormal (u, v, w): u along a -> b, v the `up` made square to u, w = u x v."""
    u = vnorm(vsub(b, a))
    v = vsub(up, vmul(u, vdot(up, u)))
    if vlen(v) < 1e-6:
        v = vsub((1.0, 0.0, 0.0), vmul(u, u[0]))
    v = vnorm(v)
    return u, v, vcross(u, v)


def obox(g, c, ex, ey, ez, hx, hy, hz):
    """A box about centre c with axes ex, ey, ez (unit, right-handed) and half sizes."""
    def pt(sx, sy, sz):
        return vadd(c, vadd(vadd(vmul(ex, sx * hx), vmul(ey, sy * hy)), vmul(ez, sz * hz)))
    hex8(g, [pt(-1, -1, -1), pt(1, -1, -1), pt(1, -1, 1), pt(-1, -1, 1), pt(-1, 1, -1), pt(1, 1, -1), pt(1, 1, 1), pt(-1, 1, 1)])


def _jit(a, b):
    """A deterministic pair of numbers in -1..1 from two points (a few percent of size jitter so no two timbers share a face plane)."""
    s = math.sin(a[0] * 12.9898 + a[1] * 78.233 + a[2] * 37.719 + b[0] * 4.1414 + b[1] * 9.1317 + b[2] * 2.7183) * 43758.5453
    t = math.sin(a[0] * 3.1415 + a[1] * 5.3 + a[2] * 7.7 + b[0] * 1.31 + b[1] * 2.17 + b[2] * 3.9) * 24634.6345
    return (s - math.floor(s)) * 2 - 1, (t - math.floor(t)) * 2 - 1


def beam(g, a, b, w, h=None, up=(0.0, 1.0, 0.0), grow=0.0):
    """A square-sectioned timber from a to b (centre line): w across, h along `up` (default w). `grow` lengthens both ends."""
    h = w if h is None else h
    j = _jit(a, b)
    w, h = w * (1.0 + 0.035 * j[0]), h * (1.0 + 0.035 * j[1])
    u, v, ww = axes_of(a, b, up)
    a2, b2 = vsub(a, vmul(u, grow)), vadd(b, vmul(u, grow))
    L = vlen(vsub(b2, a2))
    obox(g, vmul(vadd(a2, b2), 0.5), u, v, ww, L / 2, h / 2, w / 2)


def post(g, x, z, y0, y1, w, lean=(0.0, 0.0), taper=0.0, d=None):
    """An upright timber (x, z at its base, `lean` = how far the top moves per stud of height), tapering by `taper` on each side at the top."""
    d = w if d is None else d
    jj = _jit((x, y0, z), (lean[0], y1, lean[1]))
    w, d = w * (1.0 + 0.03 * jj[0]), d * (1.0 + 0.03 * jj[1])
    h = y1 - y0
    tx, tz = x + lean[0] * h, z + lean[1] * h
    hw, hd = w / 2, d / 2
    t = taper
    hex8(g, [(x - hw, y0, z - hd), (x + hw, y0, z - hd), (x + hw, y0, z + hd), (x - hw, y0, z + hd),
             (tx - hw + t, y1, tz - hd + t), (tx + hw - t, y1, tz - hd + t), (tx + hw - t, y1, tz + hd - t), (tx - hw + t, y1, tz + hd - t)])


def cyl(g, a, b, r0, r1=None, seg=6, caps=True, phase=0.0):
    """A round pole from a to b (radius r0 at a, r1 at b)."""
    r1 = r0 if r1 is None else r1
    u, v, w = axes_of(a, b, (0.0, 1.0, 0.0) if abs(b[1] - a[1]) < vlen(vsub(b, a)) * 0.95 else (1.0, 0.0, 0.0))
    ra, rb = [], []
    for k in range(seg):
        th = phase + TAU * k / seg
        o = vadd(vmul(v, math.cos(th)), vmul(w, math.sin(th)))
        ra.append(g.vert(vadd(a, vmul(o, r0))))
        rb.append(g.vert(vadd(b, vmul(o, r1))))
    for k in range(seg):
        j = (k + 1) % seg
        g.face(ra[k], rb[k], rb[j], ra[j])
    if caps:
        ca, cb = g.vert(a), g.vert(b)
        for k in range(seg):
            j = (k + 1) % seg
            g.face(ca, ra[k], ra[j])
            g.face(cb, rb[j], rb[k])


def wedge(g, b0, b1, b2, b3, th, n):
    """A tapering course: the quad b0 b1 b2 b3 (b0-b1 the lower edge, b3-b2 the upper edge), thickness th at the lower edge and nothing at the upper (a triangular
    prism whose lip stands th over the surface along b0-b1), n the surface's up normal."""
    t0, t1 = vadd(b0, vmul(n, th)), vadd(b1, vmul(n, th))
    p = [g.vert(q) for q in (b0, b1, b2, b3, t0, t1)]
    # faces: lip (b0 b1 t1 t0), top (t0 t1 b2 b3), bottom (b0 b3 b2 b1), ends (b0 t0 b3), (b1 b2 t1)
    g.face(p[0], p[1], p[5], p[4])
    g.face(p[4], p[5], p[2], p[3])
    g.face(p[0], p[3], p[2], p[1])
    g.face(p[0], p[4], p[3])
    g.face(p[1], p[2], p[5])


def tri_prism(g, a, b, c, thick, nrm):
    """A thin triangular plate a b c with thickness `thick` along the unit normal `nrm` (centred)."""
    o = vmul(nrm, thick / 2)
    p = [g.vert(vsub(q, o)) for q in (a, b, c)] + [g.vert(vadd(q, o)) for q in (a, b, c)]
    g.face(p[0], p[2], p[1])
    g.face(p[3], p[4], p[5])
    for i in range(3):
        j = (i + 1) % 3
        g.face(p[i], p[j], p[j + 3], p[i + 3])


def ring_band(g, cx, cy, cz, rx, rz, y0, y1, seg=6, t=0.12, phase=0.0):
    """A thin round band (a ring of metal or rope) round a post at (cx, cz): outer radii rx, rz, wall thickness t, from y0 to y1."""
    prof_o, prof_i = [], []
    for k in range(seg):
        th = phase + TAU * k / seg
        prof_o.append((cx + (rx + t) * math.cos(th), cz + (rz + t) * math.sin(th)))
        prof_i.append((cx + rx * math.cos(th), cz + rz * math.sin(th)))
    ob = [g.vert((x, y0, z)) for x, z in prof_o]
    ot = [g.vert((x, y1, z)) for x, z in prof_o]
    ib = [g.vert((x, y0, z)) for x, z in prof_i]
    it = [g.vert((x, y1, z)) for x, z in prof_i]
    for k in range(seg):
        j = (k + 1) % seg
        g.face(ob[k], ot[k], ot[j], ob[j])        # outside
        g.face(ib[j], it[j], it[k], ib[k])        # inside
        g.face(ot[k], it[k], it[j], ot[j])        # top
        g.face(ob[j], ib[j], ib[k], ob[k])        # bottom


def rubble(g, x0, x1, y0, y1, z0, z1, rng, j=0.22):
    """A stone block: flat top and bottom, the four vertical edges moved by up to j so no two blocks are alike."""
    def q(x, z):
        return (x + rng.uniform(-j, j), z + rng.uniform(-j, j))
    ring = [q(x0, z0), q(x1, z0), q(x1, z1), q(x0, z1)]
    hex8(g, [(x, y0, z) for x, z in ring] + [(x, y1, z) for x, z in ring])


# ======================================================================================================================
# stone
# ======================================================================================================================
def stone_wall(g, a, b, h, t0, t1=None, y0=0.0, course=(0.9, 1.35), blen=(1.8, 3.6), seed=1, gaps=(), j=0.2, ybias=0):
    """A rubble wall from a to b (x, z each) standing on y0, h tall, t0 thick at its foot and t1 at its top (a batter), laid in staggered courses of random
    height and block length; `gaps` is a list of (s0, s1) distances along the wall left open (doorways). Returns the course tops used."""
    t1 = t0 if t1 is None else t1
    rng = random.Random(seed)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz, ux
    y = y0
    k = 0
    tops = []
    while y < y0 + h - 0.2:
        ch = min(rng.uniform(*course), y0 + h - y)
        if y0 + h - (y + ch) < 0.5:
            ch = y0 + h - y
        f = (y - y0) / h
        tt = lerp(t0, t1, f)
        tt2 = lerp(t0, t1, (y + ch - y0) / h)
        s = -rng.uniform(0.0, blen[1] * 0.7) if k % 2 else 0.0
        while s < L:
            ln = rng.uniform(*blen)
            s0, s1 = max(s, 0.0), min(s + ln, L)
            s += ln
            if s1 - s0 < 0.5:
                continue
            if any(s0 < g1 and s1 > g0 for (g0, g1) in gaps):
                continue
            # a block: footprint at its base uses thickness tt, the top tt2 (a batter): we keep tops flat by using the mean (small error, hidden by the jitter)
            tm = (tt + tt2) / 2
            cx0, cz0 = a[0] + ux * s0, a[1] + uz * s0
            cx1, cz1 = a[0] + ux * s1, a[1] + uz * s1
            ring = [(cx0 - nx * tm / 2, cz0 - nz * tm / 2), (cx1 - nx * tm / 2, cz1 - nz * tm / 2), (cx1 + nx * tm / 2, cz1 + nz * tm / 2), (cx0 + nx * tm / 2, cz0 + nz * tm / 2)]
            ring = [(x + rng.uniform(-j, j), z + rng.uniform(-j, j)) for x, z in ring]
            yb, yt = y - (0.012 + 0.024 * ybias + rng.uniform(0.0, 0.008)), y + ch + (0.012 + 0.024 * ybias + rng.uniform(0.0, 0.008))
            hex8(g, [(x, yb, z) for x, z in ring] + [(x, yt, z) for x, z in ring])
        y += ch
        tops.append(y)
        k += 1
    return tops


def stone_box(g, x0, x1, z0, z1, y0, y1, seed=1, batter=0.3, course=(0.9, 1.35), blen=(2.0, 3.8), skip=()):
    """A battered rubble mass (a podium, a pier): four walls of stone_wall round a core; `skip` names sides (N S E W) left without courses (against a cliff).
    The core is a plain solid so nothing is hollow; the courses stand proud of it."""
    h = y1 - y0
    hexa_core = [(x0 + 0.3, z0 + 0.3), (x1 - 0.3, z0 + 0.3), (x1 - 0.3, z1 - 0.3), (x0 + 0.3, z1 - 0.3)]
    K.hexa(g, hexa_core, y0 + 0.05, hexa_core, y1 - 0.07, "TB0123")
    sides = {"N": ((x0, z0), (x1, z0)), "E": ((x1, z0), (x1, z1)), "S": ((x1, z1), (x0, z1)), "W": ((x0, z1), (x0, z0))}
    for n, (a, b) in sides.items():
        if n in skip:
            continue
        # push each wall outward by half its foot thickness so the outer face stands on x0..x1; the courses' thickness 1.0 sits half in the core
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        ox, oz = -uz, ux                                   # for the rings above (x0,z0)->(x1,z0) this points -z? sides run clockwise from above: outward is (uz, -ux)
        ox, oz = uz, -ux
        off = 0.35
        a2, b2 = (a[0] - ox * off, a[1] - oz * off), (b[0] - ox * off, b[1] - oz * off)
        stone_wall(g, a2, b2, h, 1.1 + batter, 1.1, y0=y0, course=course, blen=blen, seed=seed + len(n) * 7 + ord(n), j=0.12, ybias="NESW".index(n))


# ======================================================================================================================
# roofs: sawtooth courses
# ======================================================================================================================
def _bil(p00, p10, p01, p11, s, t):
    """Bilinear point on the quad with eave edge p00-p10 (s along it) and ridge edge p01-p11, t from eave (0) to ridge (1)."""
    a = vadd(vmul(p00, 1 - s), vmul(p10, s))
    b = vadd(vmul(p01, 1 - s), vmul(p11, s))
    return vadd(vmul(a, 1 - t), vmul(b, t))


def roof_plane(P, E0, E1, R0, R1, seed=1, row=1.0, th=0.5, tile=S_TILE, under=S_TIMBER, under_th=0.45, seg=(2.4, 4.4), gap=0.04, ragged=0.35, flat_ridge=True):
    """One roof slope: eave edge E0 -> E1 (low), ridge edge R0 -> R1 (high), each a 3D point. A timber underlay plate and, over it, courses of tile wedges from the
    eave up: every course is cut into segments of random length (they do not line up from course to course), its lip stands th over the one below and its
    height jitters a little; the eave's lowest course is ragged. Returns the up normal."""
    rng = random.Random(seed)
    if vlen(vsub(R1, R0)) < 0.05:                       # a hip's ridge point: give it a hand's width so no face is degenerate
        d_ = vnorm(vsub(E1, E0))
        R0, R1 = vsub(R0, vmul(d_, 0.03)), vadd(R1, vmul(d_, 0.03))
    n = vnorm(vcross(vsub(E1, E0), vsub(R0, E0)))
    if n[1] < 0:
        n = vmul(n, -1.0)
    gu, gt = P.geo(under), P.geo(tile)
    # underlay: a plate under the tiles (its top is the surface the tiles lie on), seen from below as the roof's boards
    d = vmul(n, -under_th)
    hex8(gu, [vadd(E0, d), vadd(E1, d), vadd(R1, d), vadd(R0, d), E0, E1, R1, R0])
    slope_len = max(vlen(vsub(vmul(vadd(R0, R1), 0.5), vmul(vadd(E0, E1), 0.5))), 0.1)
    nrows = max(2, int(round(slope_len / row)))
    edge_len = max(vlen(vsub(E1, E0)), vlen(vsub(R1, R0)))
    for k in range(nrows):
        t0, t1 = k / nrows, min(1.0, (k + 1) / nrows + 0.07)
        s = -rng.uniform(0.0, seg[1]) / edge_len if k % 2 else 0.0
        first = True
        while s < 1.0:
            ln = rng.uniform(*seg) / edge_len
            s0, s1 = max(s, 0.0), min(s + ln, 1.0)
            s += ln
            if s1 - s0 < 0.25 / edge_len:
                continue
            e0, e1 = s0, s1
            if k == 0:                       # the ragged lowest course: segments shorter or longer by a hand's width
                t_low = rng.uniform(-0.03, 0.0) * ragged / max(0.1, slope_len / nrows)
            else:
                t_low = 0.0
            tt0 = t0 + (t_low if k == 0 else 0.0)
            if rng.random() < 0.045:        # a missing tile segment: the underlay shows
                continue
            e0 += gap / edge_len + ((0.04 + 0.023 * (k % 13) + rng.uniform(0.0, 0.01)) / edge_len if s0 <= 1e-9 else 0.0)
            if s1 >= 1.0 - 1e-9:
                e1 -= (0.03 + 0.021 * ((k * 5) % 11) + rng.uniform(0.0, 0.01)) / edge_len
            thk = th * rng.uniform(0.85, 1.2)
            sink = vmul(n, -(0.014 + 0.013 * (k % 4) + 0.003 * (int(s * 7) % 3)))
            b0, b1 = vadd(_bil(E0, E1, R0, R1, e0, max(tt0, 0.0)), sink), vadd(_bil(E0, E1, R0, R1, e1, max(tt0, 0.0)), sink)
            b2, b3 = vadd(_bil(E0, E1, R0, R1, e1, t1), sink), vadd(_bil(E0, E1, R0, R1, e0, t1), sink)
            wedge(gt, b0, b1, b2, b3, thk, n)
    return n


def cap_line(P, a, b, w=0.42, h=0.34, piece=2.0, gap=0.1, suffix=S_BRONZE, lift=-0.14):
    """A ridge or hip cap: short bronze caps end to end along a -> b (a small gap between), sitting `lift` over the line."""
    g = P.geo(suffix)
    L = vlen(vsub(a, b))
    n = max(1, int(round(L / piece)))
    u = vnorm(vsub(b, a))
    for i in range(n):
        p0 = vadd(a, vmul(u, L * i / n + gap / 2))
        p1 = vadd(a, vmul(u, L * (i + 1) / n - gap / 2))
        beam(g, vadd(p0, (0, lift + h / 2, 0)), vadd(p1, (0, lift + h / 2, 0)), w, h)


def finial(P, p, h=1.1, r=0.28, suffix=S_BRONZE, lean=(0.0, 0.0)):
    p = (p[0], p[1] - 0.2, p[2])
    """A small bronze finial: a stepped spike (three tapering drums) with a ball on top, at p."""
    g = P.geo(suffix)
    x, y, z = p
    cyl(g, (x, y, z), (x + lean[0] * h * 0.3, y + h * 0.3, z + lean[1] * h * 0.3), r * 1.3, r * 0.8, seg=5)
    cyl(g, (x + lean[0] * h * 0.3, y + h * 0.3, z + lean[1] * h * 0.3), (x + lean[0] * h * 0.75, y + h * 0.75, z + lean[1] * h * 0.75), r * 0.8, r * 0.45, seg=5)
    cyl(g, (x + lean[0] * h * 0.75, y + h * 0.75, z + lean[1] * h * 0.75), (x + lean[0] * h, y + h, z + lean[1] * h), r * 0.45, 0.0001, seg=5, caps=False)


def gable_plate(P, a, b, c, thick=0.4, nrm=(0.0, 0.0, 1.0), suffix=S_TIMBER):
    """A timber infill triangle at a gable end (corners a b c), thick along nrm."""
    tri_prism(P.geo(suffix), a, b, c, thick, nrm)


def _lr(v):
    return v if isinstance(v, tuple) else (v, v)


def roof_gable(P, x0, x1, zf, zb, y_ef, y_eb, z_r, y_r, over=1.8, rake=(0.9, 0.9), seed=1, row=1.0, th=0.5, lean_ridge=0.0, caps=True, bargeboard=True,
               infill=True, finials=True, wall_y=None):
    """A leaning gable roof over x0..x1: eaves at z = zf (front) and z = zb (back), the ridge at z = z_r, the slopes overhanging by `over` and the gable ends by `rake`.
    Heights may be a number or a (left end, right end) pair, so the ridge and the eaves can tilt along the roof (a roof that has settled); z_r may also be a pair, and
    lean_ridge shifts the ridge's right end in z. Everything is made of the piece's Tile, Timber and Bronze meshes. Returns the ridge's end points and the eaves."""
    yef, yeb, yr, zr = _lr(y_ef), _lr(y_eb), _lr(y_r), _lr(z_r)
    xa, xb = x0 - rake[0], x1 + rake[1]
    ends = []
    for k, xx in enumerate((xa, xb)):
        zr_k = zr[k] + (lean_ridge if k == 1 else 0.0)
        sf = (zf - zr_k, yef[k] - yr[k])
        sb = (zb - zr_k, yeb[k] - yr[k])
        Lf, Lb = math.hypot(*sf), math.hypot(*sb)
        F = (xx, yr[k] + sf[1] * (1 + over / Lf), zr_k + sf[0] * (1 + over / Lf))
        Bk = (xx, yr[k] + sb[1] * (1 + over / Lb), zr_k + sb[0] * (1 + over / Lb))
        R = (xx, yr[k], zr_k)
        ends.append((F, Bk, R))
    (F0, B0, R0), (F1, B1, R1) = ends
    roof_plane(P, F0, F1, R0, R1, seed=seed, row=row, th=th)
    roof_plane(P, B1, B0, R1, R0, seed=seed + 3, row=row, th=th)
    g = P.geo(S_TIMBER)
    if bargeboard:
        for (Fp, Bp, R) in ((F0, B0, R0), (F1, B1, R1)):
            beam(g, Fp, R, 0.3, 0.7, up=(1.0, 0.0, 0.0))
            beam(g, Bp, R, 0.3, 0.7, up=(1.0, 0.0, 0.0))
    if infill:
        for k, xx in enumerate((x0, x1)):
            zr_k = zr[k] + (lean_ridge if k == 1 else 0.0)
            pf = (xx, yef[k], zf)
            pb = (xx, yeb[k], zb)
            pr = (xx, yr[k] - 0.05, zr_k)
            gable_plate(P, pf, pb, pr, 0.35, (1.0, 0.0, 0.0))
    if caps:
        cap_line(P, (R0[0], R0[1] + 0.02, R0[2]), (R1[0], R1[1] + 0.02, R1[2]), w=0.55, h=0.36, piece=2.2, gap=0.12, lift=-0.14)
        if finials:
            finial(P, (R0[0] + 0.1, R0[1] + 0.3, R0[2]), h=1.5, lean=(-0.2, 0.0))
            finial(P, (R1[0] - 0.1, R1[1] + 0.3, R1[2]), h=1.1, lean=(0.2, 0.0))
    return dict(R0=R0, R1=R1, F0=F0, F1=F1, B0=B0, B1=B1)


def roof_shed(P, x0, x1, zl, zh, y_low, y_high, over=1.6, rake=(0.7, 0.7), seed=1, row=1.0, th=0.5, bargeboard=True, cap=True):
    """A single slope from the eave at z = zl (height y_low) up to z = zh (height y_high): a lean-to. The low eave overhangs by `over`."""
    s = (zl - zh, y_low - y_high)
    L = math.hypot(*s)
    e = (zh + s[0] * (1 + over / L), y_high + s[1] * (1 + over / L))
    xa, xb = x0 - rake[0], x1 + rake[1]
    E0, E1 = (xa, e[1], e[0]), (xb, e[1], e[0])
    R0, R1 = (xa, y_high, zh), (xb, y_high, zh)
    roof_plane(P, E0, E1, R0, R1, seed=seed, row=row, th=th)
    g = P.geo(S_TIMBER)
    if bargeboard:
        beam(g, E0, R0, 0.3, 0.7, up=(1.0, 0.0, 0.0))
        beam(g, E1, R1, 0.3, 0.7, up=(1.0, 0.0, 0.0))
    if cap:
        cap_line(P, (xa, y_high + 0.02, zh), (xb, y_high + 0.02, zh), w=0.5, h=0.32, piece=2.0)
    return dict(E0=E0, E1=E1, R0=R0, R1=R1)


def roof_hip(P, cx, cz, hx, hz, y_e, y_r, ridge=(0.0, 0.0), over=1.6, seed=1, row=1.0, th=0.5, rx=None, caps=True):
    """A hipped roof over a rectangle (centre cx, cz, half sizes hx, hz): four slopes meeting at a ridge segment of half length rx along x (0 = a pyramid), whose
    middle may be off-centre by `ridge`. Four planes, each of courses; the hips capped in bronze."""
    rx = 0.0 if rx is None else rx
    sx, sz = hx + over, hz + over
    k = (hx + over) / hx
    ye = y_e - (y_r - y_e) * (over / max(hz, 0.5)) * 0.5
    rcx, rcz = cx + ridge[0], cz + ridge[1]
    E = [(cx - sx, ye, cz - sz), (cx + sx, ye, cz - sz), (cx + sx, ye, cz + sz), (cx - sx, ye, cz + sz)]
    R = [(rcx - rx, y_r, rcz), (rcx + rx, y_r, rcz)]
    roof_plane(P, E[0], E[1], R[0], R[1], seed=seed, row=row, th=th)                     # front (south)
    roof_plane(P, E[2], E[3], R[1], R[0], seed=seed + 1, row=row, th=th)                 # back
    roof_plane(P, E[1], E[2], R[1], R[1], seed=seed + 2, row=row, th=th)                 # right hip
    roof_plane(P, E[3], E[0], R[0], R[0], seed=seed + 4, row=row, th=th)                 # left hip
    if caps:
        cap_line(P, R[0], R[1], w=0.5, h=0.34, piece=2.0) if rx > 0.2 else None
        for e, r in ((E[0], R[0]), (E[1], R[1]), (E[2], R[1]), (E[3], R[0])):
            cap_line(P, vadd(e, (0, 0.05, 0)), vadd(r, (0, 0.05, 0)), w=0.4, h=0.28, piece=2.0)
        finial(P, (rcx, y_r + 0.2, rcz), h=1.6)
    return dict(R=R, E=E)


# ======================================================================================================================
# frames, rails, cloth
# ======================================================================================================================
def stilt_bay(P, x0, x1, z, y0, y1, w=0.55, brace=True, seed=1, lean=(0.0, 0.0), suffix=S_TIMBER):
    """Two stilts at x0, x1 (depth z) from y0 up to y1 with a cross beam near the top and an X brace between them (a trestle)."""
    g = P.geo(suffix)
    post(g, x0, z, y0, y1, w, lean=lean, taper=0.04)
    post(g, x1, z, y0, y1, w, lean=lean, taper=0.04)
    beam(g, (x0, y1 - 0.5, z), (x1, y1 - 0.5, z), w * 0.9, w * 0.9)
    if brace:
        beam(g, (x0, y0 + 0.9, z), (x1, y1 - 1.6, z), w * 0.5, w * 0.5)
        beam(g, (x1, y0 + 0.9, z), (x0, y1 - 1.6, z), w * 0.5, w * 0.5)


def corbels(P, x0, x1, z, y, reach, steps=3, w=0.5, suffix=S_TIMBER, direction=-1.0):
    """Stacked corbels under a cantilever: `steps` beams along z, each projecting further than the one below (0.5 .. reach), from the wall at z outward
    (direction -1 = toward -z), spaced evenly in x0..x1 pairs."""
    g = P.geo(suffix)
    n = max(2, int((x1 - x0) / 2.4) + 1)
    for i in range(n):
        x = lerp(x0, x1, i / (n - 1))
        for s in range(steps):
            r = reach * (s + 1) / steps
            yy = y - 0.45 * (steps - 1 - s) - 0.2
            beam(g, (x, yy, z - direction * 0.3), (x, yy, z + direction * r), w, 0.5, up=(0, 1, 0))
        beam(g, (x, y - 0.3, z + direction * reach * 0.92), (x, y - 0.5 - 0.45 * (steps - 1) - reach * 0.7, z - direction * 0.15), w * 0.7, w * 0.7)   # the strut back to the wall


def rope_line(P, pts, r=0.1, seg=4, suffix=S_ROPE):
    """A rope along a list of 3D points (thin square-ish tubes, one per span)."""
    g = P.geo(suffix)
    for a, b in zip(pts, pts[1:]):
        cyl(g, a, b, r, r, seg=seg, caps=False, phase=0.4)


def catenary(a, b, sag, n):
    """n + 1 points from a to b hanging with `sag` at the middle (parabola)."""
    out = []
    for i in range(n + 1):
        t = i / n
        p = vadd(vmul(a, 1 - t), vmul(b, t))
        out.append((p[0], p[1] - sag * 4 * t * (1 - t), p[2]))
    return out


def awning(P, corners, sag=0.5, seed=1, suffix=S_CLOTH, thick=0.08, panels=3, drop=0.0):
    """A cloth sheet stretched between four points (a b c d in order), hanging with a sag in the middle and a scalloped hem: panels of cloth side by side, each a thin
    slab drooping a little differently (a patchwork); every panel is two thin triangular plates so it is always flat. corners = [a, b, c, d]: a-b the high edge, d-c the low edge."""
    rng = random.Random(seed)
    a, b, c, d = corners
    g = P.geo(suffix)
    for i in range(panels):
        s0, s1 = i / panels + 0.006, (i + 1) / panels - 0.006
        dr = drop * rng.uniform(0.0, 1.0)

        def pt(s, t):
            top = vadd(vmul(a, 1 - s), vmul(b, s))
            bot = vadd(vmul(d, 1 - s), vmul(c, s))
            p = vadd(vmul(top, 1 - t), vmul(bot, t))
            return (p[0], p[1] - sag * 4 * t * (1 - t) - (dr if t > 0.9 else 0.0), p[2])
        rows = 3
        for r in range(rows):
            t0, t1 = r / rows + 0.004, (r + 1) / rows - 0.004
            q = [pt(s0, t0), pt(s1, t0), pt(s1, t1), pt(s0, t1)]
            th = thick * (1.0 + 0.25 * rng.random())
            for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                n = vnorm(vcross(vsub(tri[1], tri[0]), vsub(tri[2], tri[0])))
                tri_prism(g, tri[0], tri[1], tri[2], th, n)


# ======================================================================================================================
# racking: a frame that has settled
# ======================================================================================================================
def lean_piece(P, kx=0.02, kz=0.0, y_from=0.0, sag_x=0.0):
    """Shears every vertex above y_from sideways by (kx, kz) per stud of height (a racked frame: a degree or two), and adds an optional sag (a slight bow in y by x)."""
    for g in P.g.values():
        g.v = [((p[0] + kx * max(0.0, p[1] - y_from)), p[1], (p[2] + kz * max(0.0, p[1] - y_from))) for p in g.v]
    for i, (x0, x1, y0, y1, z0, z1, n) in enumerate(P.col):
        pass


def seed_of(name):
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) % 100003


# ======================================================================================================================
# scaffolds, ladders, bells, lanterns, brackets
# ======================================================================================================================
def scaffold(P, x0, x1, z0, z1, y0, y1, bays=2, levels=3, seed=1, suffix=S_BAMBOO, rope=True, lean=(0.0, 0.0), r=0.2):
    """Bamboo scaffolding: round poles upright at the corners and between the bays, ledgers at each level in both directions, a diagonal brace or two, lashings
    of rope at the joints, a plank at one level. Poles are 6-sided. Lean makes the whole thing rake."""
    rng = random.Random(seed)
    g = P.geo(suffix)
    gr = P.geo(S_ROPE) if rope else None
    xs = [lerp(x0, x1, i / bays) for i in range(bays + 1)]
    zs = [z0, z1]
    h = y1 - y0
    for x in xs:
        for z in zs:
            top = y1 + rng.uniform(0.0, 1.4)
            cyl(g, (x, y0 - 0.3, z), (x + lean[0] * h, top, z + lean[1] * h), r, r * 0.8, seg=6, phase=rng.uniform(0, 1.0))
    for lv in range(1, levels + 1):
        y = y0 + h * lv / levels
        for z in zs:
            for a, b in zip(xs, xs[1:]):
                cyl(g, (a - 0.5, y + rng.uniform(-0.1, 0.1), z), (b + 0.5, y + rng.uniform(-0.1, 0.1), z), r * 0.85, seg=6, phase=rng.uniform(0, 1.0))
        for x in xs:
            cyl(g, (x, y, z0 - 0.4), (x, y, z1 + 0.4), r * 0.85, seg=6, phase=rng.uniform(0, 1.0))
        if gr is not None:
            for x in xs:
                for z in zs:
                    ring_band(gr, x + lean[0] * (y - y0), y, z + lean[1] * (y - y0), r * 1.2, r * 1.2, y - 0.18, y + 0.18, seg=5, t=0.07)
    for a, b in zip(xs, xs[1:]):
        cyl(g, (a, y0, z0), (b, y1 - h / levels, z0), r * 0.75, seg=6, phase=rng.uniform(0, 1.0))
        cyl(g, (b, y0, z1), (a, y1 - h / levels, z1), r * 0.75, seg=6, phase=rng.uniform(0, 1.0))


def ladder(P, x, z, y0, y1, yaw=0.0, w=1.5, suffix=S_TIMBER, rung=1.0, lean=0.22):
    """A rope-and-pole ladder leaning against a wall facing +z: two rails and rungs every `rung`."""
    g = P.geo(suffix)
    for sx in (-w / 2, w / 2):
        beam(g, (x + sx, y0, z - lean * (y1 - y0)), (x + sx, y1, z), 0.22, 0.22)
    n = int((y1 - y0) / rung)
    for i in range(1, n + 1):
        t = i / (n + 1)
        beam(g, (x - w / 2, y0 + (y1 - y0) * t, z - lean * (y1 - y0) * (1 - t)), (x + w / 2, y0 + (y1 - y0) * t, z - lean * (y1 - y0) * (1 - t)), 0.14, 0.14)


def bell(P, x, y, z, r=0.9, h=1.5):
    """A bronze bell hanging from (x, y, z) (y = the top): a lathe-like bell of three tapering drums with a flared lip and a clapper."""
    g = P.geo(S_BRONZE)
    cyl(g, (x, y + 0.12, z), (x, y - h * 0.45, z), r * 0.45, r * 0.7, seg=8)
    cyl(g, (x, y - h * 0.45, z), (x, y - h * 0.85, z), r * 0.7, r * 1.0, seg=8)
    cyl(g, (x, y - h * 0.85, z), (x, y - h, z), r * 1.0, r * 1.15, seg=8, caps=False)
    cyl(g, (x, y - h * 0.8, z), (x, y - h * 0.95, z), r * 0.1, r * 0.1, seg=4)
    cyl(g, (x, y - h * 0.9, z), (x, y - h * 1.05, z), r * 0.2, r * 0.3, seg=5)


def lantern_hang(P, x, y, z, h=1.4, w=0.9, glow=True, cord=1.6):
    """A hanging paper lantern: a cord from y down, a timber cap, a glowing body (Lamp), a timber foot. Returns the light position."""
    gt, gl = P.geo(S_TIMBER), P.geo(S_LAMP)
    beam(gt, (x, y, z), (x, y - cord, z), 0.07, 0.07)
    K.box(gt, x - w * 0.55, x + w * 0.55, y - cord - 0.14, y - cord, z - w * 0.55, z + w * 0.55)
    K.box(gl, x - w * 0.42, x + w * 0.42, y - cord - h - 0.1, y - cord - 0.14, z - w * 0.42, z + w * 0.42)
    K.box(gt, x - w * 0.55, x + w * 0.55, y - cord - h - 0.24, y - cord - h - 0.1, z - w * 0.55, z + w * 0.55)
    return (x, y - cord - h * 0.5, z)


def bracket(P, x, y, z, reach, h=1.6, along="z", direction=-1.0, suffix=S_TIMBER, w=0.45):
    """An L bracket under an eave or a balcony: a horizontal arm of length `reach` and a diagonal strut back to the wall."""
    g = P.geo(suffix)
    if along == "z":
        beam(g, (x, y, z), (x, y, z + direction * reach), w, w)
        beam(g, (x, y - h, z), (x, y - 0.1, z + direction * reach * 0.95), w * 0.7, w * 0.7)
    else:
        beam(g, (x, y, z), (x + direction * reach, y, z), w, w)
        beam(g, (x, y - h, z), (x + direction * reach * 0.95, y - 0.1, z), w * 0.7, w * 0.7)

"""The Orthodox sword's LOW game mesh with a hand-laid UV (run inside Blender): every part is a few clean islands in true proportion
(a blade face is a long strip, a facet of the bell a trapezoid, a tube a rectangle), so the colour map is orderly rectangles, nothing
nests, and the texel density goes where the detail is (the blade). The islands carry an integer face attribute "island" (piece * 1000 +
local id); pack_uv() packs them, weighted, into 0..1 with plain shelves.

Islands are in studs; a part's own faces never share an island with another part's.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import sword_orthodox_parts as P

Hm, W = P.Hm, P.W
V = Vector
TAU, PI = math.tau, math.pi
DUMP = 999

PIECE = dict(Blade=1, Collar=2, Shell=3, Core=4, Fuchi=5, Kashira=6, Ring=7, Cord=8, Knot=9, Pendant=10, Tassel=11)
WEIGHT = dict(Blade=1.55, Collar=1.0, Shell=1.0, Core=1.2, Fuchi=0.9, Kashira=0.9, Ring=0.85, Cord=0.85, Knot=0.6, Pendant=0.8, Tassel=0.8)
TANG_WEIGHT = 0.5          # the flat root of the blade inside the bell: seen only through the windows


class HiI(Hm.Hi):
    """A Hi mesh whose faces also carry an island id."""

    def __init__(self, piece):
        super().__init__()
        self.isl, self.cur, self.piece = [], 0, piece

    def f(self, idx, uv, mat=0):
        super().f(idx, uv, mat)
        self.isl.append(self.piece * 1000 + self.cur)

    def object(self, name, coll, materials, smooth=True, weld=1e-5):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        layer = me.uv_layers.new(name="UVMap")
        att = me.attributes.new("island", "INT", "FACE")
        for poly, uv, m in zip(me.polygons, self.uvs, self.mats):
            poly.material_index = m
            for li, c in zip(poly.loop_indices, uv):
                layer.data[li].uv = c
        att.data.foreach_set("value", self.isl)
        for m in materials:
            me.materials.append(m)
        me.validate()
        if weld:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
            bm.to_mesh(me)
            bm.free()
        for p in me.polygons:
            p.use_smooth = smooth
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        return o


# ---------- metric strips ----------
def strip_surface(hi, rings, island, mat=0, closed=True, loop_path=False, caps=(False, False), cap_islands=(None, None), raw=False):
    """A skin over `rings` with a metric UV: u the arc length round a ring (centred), v the distance along the path; so each part is one
    island in true proportion. Caps are fans, wound outward (the far cap the other way round): hidden ones go in the part's dump island,
    visible ones (cap_islands) get a planar island of their own."""
    nR, m = len(rings), len(rings[0])
    vs = [0.0]
    for k in range(1, nR):
        vs.append(vs[-1] + sum((rings[k][i] - rings[k - 1][i]).length for i in range(m)) / m)
    v_end = vs[-1] + (sum((rings[0][i] - rings[-1][i]).length for i in range(m)) / m if loop_path else 0.0)
    us = []
    for r in rings:
        arc = [0.0]
        for i in range(m):
            arc.append(arc[-1] + (r[(i + 1) % m] - r[i]).length)
        us.append([a - arc[-1] / 2 for a in arc])
    ids = [[hi.v(p) for p in r] for r in rings]
    hi.cur = island
    nK = nR if loop_path else nR - 1
    flip = False if raw else (not P.tube_outward(rings) if not loop_path else not _loop_outward(rings))      # raw: the rings run round a solid, in order
    for k in range(nK):
        k2 = (k + 1) % nR
        v0 = vs[k]
        v1 = vs[k + 1] if k + 1 < nR else v_end
        for i in range(m if closed else m - 1):
            j = (i + 1) % m
            quad = [ids[k][i], ids[k][j], ids[k2][j], ids[k2][i]]
            uv = [(us[k][i], v0), (us[k][i + 1], v0), (us[k2][i + 1], v1), (us[k2][i], v1)]
            if flip:
                quad, uv = quad[::-1], uv[::-1]
            hi.f(quad, uv, mat)
    for flag, ring, pts, far, isl in ((caps[0], ids[0], rings[0], False, cap_islands[0]), (caps[1], ids[-1], rings[-1], True, cap_islands[1])):
        if not flag:
            continue
        cen = P.centroid(pts)
        c = hi.v(cen)
        out = (P.centroid(rings[-1]) - P.centroid(rings[-2])) if far else (P.centroid(rings[0]) - P.centroid(rings[1]))
        hi.cur = DUMP if isl is None else isl
        for i in range(m):
            j = (i + 1) % m
            if isl is None:
                uv = [(0, 0), (0.01, 0), (0, 0.01)]
            else:
                a_, b_ = pts[i] - cen, pts[j] - cen
                uv = [(a_.x, a_.y), (b_.x, b_.y), (0.0, 0.0)]
            hi.facing([ring[i], ring[j], c], uv, tuple(out), mat)
    return hi


def _loop_outward(rings):
    """The same test for a ring of rings (a torus): the travel at ring 0 is toward ring 1."""
    return P.tube_outward(rings)


def tube_rings(pts, radius_fn, sides, per=4):
    curve = [V(p) for p in W.catmull([tuple(p) for p in pts], per)]
    fr = Hm.frames(curve)
    n = len(curve)
    rings = []
    for i, c in enumerate(curve):
        _, s, b = fr[i]
        r = radius_fn(i / (n - 1))
        rings.append([c + (s * math.cos(TAU * k / sides) + b * math.sin(TAU * k / sides)) * r for k in range(sides)])
    return rings


def torus_rings(centre, normal, R, r, n, sides):
    nrm = V(normal).normalized()
    ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
    s = nrm.cross(ref).normalized()
    t = nrm.cross(s)
    out = []
    for k in range(n):
        a = TAU * k / n
        radial = s * math.cos(a) + t * math.sin(a)
        mid = V(centre) + radial * R
        out.append([mid + radial * (r * math.cos(TAU * j / sides)) + nrm * (r * math.sin(TAU * j / sides)) for j in range(sides)])
    return out


# ---------- the parts ----------
def blade_low():
    """The blade's coarse rings, a UV that is two faces (flat top, flat bottom) in three segments along the blade and a short tang."""
    hi = HiI(PIECE["Blade"])
    ss = [-0.26, -0.2, -0.19, -0.03, 0.0, 0.12, 0.26, 0.40, 0.54, 0.68, 0.80, 0.88, 0.935, 0.975]
    seg_of = {0: -1, 1: -1}                                  # stations 0, 1 are the tang
    rings, secs = [], []
    for s in ss:
        z = P.Z_HILT - s * P.BLADE_LEN
        sec = P.blade_section(s if s < P.TANG_S else max(s, 0.0), False)
        secs.append(sec)
        rings.append([V((x, y, z)) for x, y, _ in sec])
    ids = [[hi.v(p) for p in r] for r in rings]
    m = len(rings[0])
    flip = not P.tube_outward(rings)
    bounds = [0.0, 0.46, 0.88, 1.01]

    def seg(s):
        if s < 0:
            return 0
        for q in range(3):
            if s < bounds[q + 1]:
                return q + 1
        return 3
    for k in range(len(ss) - 1):
        sg = seg(0.5 * (ss[k] + ss[k + 1]))
        for i in range(m):
            j = (i + 1) % m
            q = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
            side = 0 if sum(p.y for p in q) > 0 else 1
            hi.cur = sg * 2 + side
            quad, uv = [ids[k][i], ids[k][j], ids[k + 1][j], ids[k + 1][i]], [(p.x, -p.z) for p in q]
            if flip:
                quad, uv = quad[::-1], uv[::-1]
            hi.f(quad, uv)
    tid = hi.v(V((0.0, 0.0, P.Z_TIP)))
    for i in range(m):
        j = (i + 1) % m
        q = [rings[-1][i], rings[-1][j]]
        hi.cur = 3 * 2 + (0 if (q[0].y + q[1].y) >= 0 else 1)
        hi.facing([ids[-1][i], ids[-1][j], tid], [(q[0].x, -q[0].z), (q[1].x, -q[1].z), (0.0, -P.Z_TIP)], (0, 0, -1))
    hi.cur = DUMP
    c = hi.v(sum(rings[0], V((0, 0, 0))) / m)
    for i in range(m):
        hi.facing([ids[0][i], ids[0][(i + 1) % m], c], [(0, 0), (0.01, 0), (0, 0.01)], (0, 0, 1))
    return hi


def collar_low():
    """The collar with a real mouth: a bore just wider than the blade, a rolled lip, then the outside, wound in order round the solid. (A flat cap across the
    top would be baked from the blade lying under it, and the map would show the blade's section.)"""
    hi = HiI(PIECE["Collar"])
    N = 16
    z0 = P.Z_COLLAR0

    def ell(ax, ay, z):
        return [V((P.ell_rho(TAU * j / N, ax, ay) * math.cos(TAU * j / N), P.ell_rho(TAU * j / N, ax, ay) * math.sin(TAU * j / N), z)) for j in range(N)]
    rings = [ell(0.238, 0.088, z0 + 0.05), ell(0.238, 0.088, z0 + 0.014), ell(0.247, 0.142, z0 + 0.008)] + P.collar_rings(N)
    return strip_surface(hi, rings, 0, raw=True, caps=(False, True))


def core_low():
    hi = HiI(PIECE["Core"])
    rings, _, _ = P.core_rings(16, 9)
    return strip_surface(hi, rings, 0, caps=(True, True))


def _sets_low(piece, sets, visible):
    """visible: {(set index, 'a' or 'b')} the caps that can be seen; the rest are hidden fans."""
    hi = HiI(piece)
    for n, (rings, mat, ca, cb) in enumerate(sets):
        strip_surface(hi, rings, n, mat=mat, caps=(ca, cb), cap_islands=(10 + n if (n, "a") in visible else None, 20 + n if (n, "b") in visible else None))
    return hi


def fuchi_low():
    """The collar with a real mouth for the tang (a flat cap across its front would be baked from the tang lying under it, and the map would show
    the tang's section): a bore just wider than the tang, a lip, then the body, wound in order."""
    hi = HiI(PIECE["Fuchi"])
    N = 16
    z0 = P.Z_FUCHI0
    sets = P.fuchi_sets(N)

    def ell(ax, ay, z):
        return [V((P.ell_rho(TAU * j / N, ax, ay) * math.cos(TAU * j / N), P.ell_rho(TAU * j / N, ax, ay) * math.sin(TAU * j / N), z)) for j in range(N)]
    body, mat, _, _ = sets[0]
    strip_surface(hi, [ell(0.094, 0.044, z0 + 0.05), ell(0.094, 0.044, z0 + 0.014), ell(0.16, 0.12, z0 + 0.006)] + body, 0, mat=mat, raw=True)
    for n, (rings, mat, ca, cb) in enumerate(sets[1:], 1):
        strip_surface(hi, rings, n, mat=mat, caps=(ca, cb))
    return hi


def kashira_low():
    return _sets_low(PIECE["Kashira"], P.kashira_sets(16), {(2, "b")})


def ring_low():
    hi = HiI(PIECE["Ring"])
    return strip_surface(hi, torus_rings(V((0, 0, P.Z_RING)), V((0, 1, 0)), P.RING_R, 0.04, 24, 6), 0, loop_path=True)


def cord_low():
    hi = HiI(PIECE["Cord"])
    strip_surface(hi, torus_rings(V((0, 0, P.Z_RING + P.RING_R)), V((1, 0, 0)), 0.07, 0.024, 10, 6), 0, loop_path=True)
    for n, (z0, z1) in enumerate(((P.Z_CORD0 - 0.02, P.Z_KNOT - 0.07), (P.Z_KNOT + 0.07, P.Z_JADE0 + 0.02))):
        strip_surface(hi, tube_rings(P.cord_path(z0, z1, 6), lambda t: 0.034, 6, per=4), 1 + n, caps=(True, True))
    return hi


def knot_low():
    hi = HiI(PIECE["Knot"])
    cx = P.cord_x(P.Z_KNOT)
    pts = [V((cx, 0, P.Z_KNOT - 0.075)), V((cx, 0, P.Z_KNOT)), V((cx, 0, P.Z_KNOT + 0.075))]
    strip_surface(hi, tube_rings(pts, lambda t: 0.105 * math.sin(math.pi * (0.04 + 0.92 * t)) ** 0.7 + 0.002, 10, per=4), 0, mat=0, caps=(True, True))
    for n, dz in enumerate((-0.085, 0.085)):
        zc = P.Z_KNOT + dz
        rings = [[V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)]
                 for rr, z in ((0.030, zc - 0.018), (0.046, zc - 0.006), (0.046, zc + 0.006), (0.030, zc + 0.018))]
        strip_surface(hi, rings, 1 + n, mat=0)        # no caps: the cord runs through the bead
    return hi


def pendant_low():
    hi = HiI(PIECE["Pendant"])
    cx = P.cord_x((P.Z_JADE0 + P.Z_JADE1) / 2)
    zc = (P.Z_JADE0 + P.Z_JADE1) / 2 + 0.02
    hw, hl = 0.078, 0.14
    pts8 = [(0.55, 1.0), (1.0, 0.55), (1.0, -0.55), (0.55, -1.0), (-0.55, -1.0), (-1.0, -0.55), (-1.0, 0.55), (-0.55, 1.0)]

    def octa(sx, sz, y):
        return [V((cx + hw * sx * x, y, zc + hl * sz * z)) for x, z in pts8]
    jade = [octa(0.55, 0.62, 0.030), octa(0.86, 0.9, 0.022), octa(0.86, 0.9, -0.022), octa(0.55, 0.62, -0.030)]
    strip_surface(hi, jade, 0, caps=(False, False))
    for n, (ring, sgn) in enumerate(((jade[0], 1), (jade[-1], -1))):         # the two faces: planar islands
        c = hi.v(sum(ring, V((0, 0, 0))) / 8)
        ids = [hi.v(p) for p in ring]
        hi.cur = 1 + n
        for i in range(8):
            j = (i + 1) % 8
            a, b = ring[i], ring[j]
            hi.facing([ids[i], ids[j], c], [(sgn * (a.x - cx), a.z - zc), (sgn * (b.x - cx), b.z - zc), (0.0, 0.0)], (0, sgn, 0))
    frame = [octa(0.84, 0.88, 0.034), octa(1.0, 1.0, 0.030), octa(1.0, 1.0, -0.030), octa(0.84, 0.88, -0.034)]
    strip_surface(hi, frame, 3, mat=0)
    z_cap = zc - hl - 0.02
    cap = [[V((cx + rr * math.cos(TAU * j / 12), rr * 0.7 * math.sin(TAU * j / 12), z)) for j in range(12)]
           for rr, z in ((0.05, z_cap + 0.045), (0.036, z_cap + 0.02), (0.044, z_cap), (0.052, z_cap - 0.02))]
    strip_surface(hi, cap, 4, mat=0)
    return hi


def tassel_low():
    hi = HiI(PIECE["Tassel"])
    cx = P.cord_x(P.Z_TASSEL0)
    zt = P.Z_TASSEL0
    neck = [[V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)]
            for rr, z in ((0.03, zt), (0.05, zt + 0.02), (0.05, zt + 0.06), (0.04, zt + 0.085))]
    strip_surface(hi, neck, 0, caps=(True, False))
    bind = [[V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)]
            for rr, z in ((0.04, zt + 0.085), (0.06, zt + 0.11), (0.06, zt + 0.15), (0.075, zt + 0.19), (0.078, zt + 0.2))]
    strip_surface(hi, bind, 1)
    z0 = zt + 0.2
    N = 12
    rows = [(0.0, 0.07), (0.1, 0.08), (0.2, 0.076), (0.28, 0.062), (0.34, 0.04), (0.38, 0.012)]
    rings = []
    for k, (dz, rr) in enumerate(rows):
        ring = []
        for j in range(N):
            ln_j = 0.05 * (0.5 + 0.5 * math.sin(j * 2.3 + 1.0)) if k == len(rows) - 2 else 0.0
            ring.append(V((cx + rr * math.cos(TAU * j / N) + 0.006 * (k + 1), rr * 0.95 * math.sin(TAU * j / N), z0 + dz + ln_j)))
        rings.append(ring)
    strip_surface(hi, rings, 2, caps=(False, True))
    return hi


def shell_low():
    """The bell on the same rings as the high one, its UV laid facet by facet: every facet one column from the neck over the brim and
    back up the lining, in true size (u along the facet, v down the profile)."""
    rings, mats, n_out = P.shell_rings("low")
    hi = HiI(PIECE["Shell"])
    nR, N = len(rings), len(rings[0])
    kk = N // 8
    ids = [[hi.v(p) for p in r] for r in rings]
    # v: the distance down the profile along each facet's centre line
    vs = {}
    for f in range(8):
        pts = [r[f * kk] for r in rings]
        acc = [0.0]
        for q in range(1, nR):
            acc.append(acc[-1] + (pts[q] - pts[q - 1]).length)
        vs[f] = acc
    for k in range(nR - 1):
        for j in range(N):
            f = int(round((TAU * (j + 0.5) / N) / (PI / 4))) % 8
            th = f * PI / 4
            c, s = math.cos(th), math.sin(th)
            j2 = (j + 1) % N
            quad = [(k, j), (k, j2), (k + 1, j2), (k + 1, j)]
            uv = [((-rings[a][b].x * s + rings[a][b].y * c), vs[f][a]) for a, b in quad]
            hi.cur = f
            hi.f([ids[a][b] for a, b in quad], uv, mats[k])
    hi.cur = DUMP
    for far, ids_r, pts in ((False, ids[0], rings[0]), (True, ids[-1], rings[-1])):
        cen = hi.v(sum(pts, V((0, 0, 0))) / len(pts))
        for i in range(N):
            a, b = ids_r[i], ids_r[(i + 1) % N]
            hi.facing([a, b, cen], [(0, 0), (0.01, 0), (0, 0.01)], (0, 0, 1) if far else (0, 0, -1), mats[-1 if far else 0])      # the ceiling faces the mouth, the neck the point
    return hi


def window_cutters_low():
    """The cutters of the low bell, each with its own strip UV, so the faces the boolean makes in the wall (the window's edge) are laid out
    like any other: one small island per window."""
    hi = HiI(PIECE["Shell"])
    loop = P.window_arch(8)
    for f in range(8):
        th = f * PI / 4
        n = V((math.cos(th), math.sin(th), 0))
        t = V((-math.sin(th), math.cos(th), 0))
        rings = [[n * r + t * u + V((0, 0, z)) for u, z in loop] for r in (0.12, 1.3)]
        strip_surface(hi, rings, 100 + f, caps=(True, True))
    return hi


LOW = [("Blade", blade_low), ("Collar", collar_low), ("Shell", shell_low), ("Core", core_low), ("Fuchi", fuchi_low), ("Kashira", kashira_low),
       ("Ring", ring_low), ("Cord", cord_low), ("Knot", knot_low), ("Pendant", pendant_low), ("Tassel", tassel_low)]


# ---------- packing ----------
def pack_uv(obj, size=1024, gap_px=12, report=True):
    """Packs every island of `obj` (its "island" face attribute, UVs in studs) into 0..1: weighted by piece, rotated 90 degrees where it
    helps (never mirrored), plain shelves, the largest scale that fits."""
    me = obj.data
    nP = len(me.polygons)
    isl = np.zeros(nP, dtype=np.int32)
    me.attributes["island"].data.foreach_get("value", isl)
    totals = np.zeros(nP, dtype=np.int32)
    me.polygons.foreach_get("loop_total", totals)
    uvl = me.uv_layers.active
    uv = np.zeros(len(me.loops) * 2, dtype=np.float64)
    uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    loop_isl = np.repeat(isl, totals)
    names = {v: k for k, v in PIECE.items()}
    boxes = {}
    for i in np.unique(loop_isl):
        m = loop_isl == i
        lo, hi = uv[m].min(0), uv[m].max(0)
        piece, local = divmod(int(i), 1000)
        w = WEIGHT[names[piece]]
        if piece == PIECE["Blade"] and local < 2:
            w = TANG_WEIGHT
        if local == DUMP:
            w = 0.06
        boxes[int(i)] = (lo, hi, w)

    def try_fit(scale, order, land):
        items = []
        for i, (lo, hi, w) in boxes.items():
            bw, bh = (hi - lo) * w * scale + gap_px
            rot = (bh > bw) if land else (bw > bh)           # landscape or portrait: whichever the pass tries
            items.append((i, (bh, bw) if rot else (bw, bh), rot))
        items.sort(key=order)
        x = y = rowh = 0.0
        placed = {}
        for i, (bw, bh), rot in items:
            if bw > size or bh > size:
                return None
            if x + bw > size:
                x, y, rowh = 0.0, y + rowh, 0.0
            if y + bh > size:
                return None
            placed[i] = (x, y, rot)
            x += bw
            rowh = max(rowh, bh)
        return placed
    orders = (lambda t: -t[1][1], lambda t: -t[1][0], lambda t: -t[1][0] * t[1][1], lambda t: (-round(t[1][1] / 24), -t[1][0]))
    best = (0.0, None)
    for order in orders:
        for land in (True, False):
            lo_s, hi_s = 20.0, 900.0
            for _ in range(24):
                mid = (lo_s + hi_s) / 2
                r = try_fit(mid, order, land)
                if r is None:
                    hi_s = mid
                else:
                    lo_s = mid
                    if mid > best[0]:
                        best = (mid, r)
    scale, placed = best
    out = np.zeros_like(uv)
    for i, (lo, hi, w) in boxes.items():
        x, y, rot = placed[i]
        m = loop_isl == i
        q = (uv[m] - lo) * w * scale                  # px, from the island's lower-left
        if rot:                                       # turn 90 degrees (u, v) -> (v, umax - u): a rotation, not a mirror
            wpx = (hi[0] - lo[0]) * w * scale
            q = np.stack([q[:, 1], wpx - q[:, 0]], axis=1)
        out[m] = (q + np.array([x + gap_px / 2, y + gap_px / 2])) / size
    uvl.data.foreach_set("uv", out.ravel())
    if report:
        used = sum(((hi - lo) * w * scale).prod() for lo, hi, w in boxes.values()) / size ** 2
        print("pack: %d islands, scale %.0f px per weighted stud, %.0f%% of the map covered by islands" % (len(boxes), scale, used * 100))
    return scale

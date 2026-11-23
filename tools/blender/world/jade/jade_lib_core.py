"""jade_lib_core: the geometry kit of Jade Grove's own asset library (2026-11-22). Plain Python, no Blender, no other island's builders.

Everything is authored in ROBLOX STUDS (x right, y up, z back), every piece at its own origin with y = 0 at its foot. A piece is a `Piece`:
material suffix -> `Geo` (welded vertices, triangles and quads only). Primitives return a closed `Geo` shell (so its winding is fixed by the sign of
its volume, never by hand); `Piece.put(geo, material or chooser, ...)` merges a transformed copy, a chooser (normal, centre) -> suffix splits a
shell between materials by what its faces look at (up-facing faces moss, undersides dark: the colour is in the geometry, no texture anywhere).

The shape language is Jade Grove's own: leaning, twisting, draped and layered forms (ruffled leaf tiers with drooping tips, buttress fins,
spiral culms, cloven and terraced stone), not the hub's marble and brackets, not the other islands' columns and shards.

Conventions: `yaw` turns a point about +Y as CFrame.Angles(0, yaw, 0) does: x' = x cos + z sin, z' = -x sin + z cos.
"""
import math
import random

TAU = 2 * math.pi


# ======================================================================================================================
# vectors and noise
# ======================================================================================================================
def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    n = vlen(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 1.0, 0.0)


def vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 1.0 if x >= e1 else 0.0
    t = clamp((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def yaw_xz(x, z, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return x * c + z * s, -x * s + z * c


def rot_axis(p, axis, ang):
    """Rodrigues: p turned about the unit `axis` by `ang`."""
    c, s = math.cos(ang), math.sin(ang)
    d = vdot(axis, p)
    cr = vcross(axis, p)
    return (p[0] * c + cr[0] * s + axis[0] * d * (1 - c), p[1] * c + cr[1] * s + axis[1] * d * (1 - c), p[2] * c + cr[2] * s + axis[2] * d * (1 - c))


def _h3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2246822519 + seed * 3266489917) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise3(x, y, z, seed=0):
    """Smooth value noise in 0..1."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    sx, sy, sz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    out = 0.0
    for dz, wz in ((0, 1 - sz), (1, sz)):
        for dy, wy in ((0, 1 - sy), (1, sy)):
            for dx, wx in ((0, 1 - sx), (1, sx)):
                out += _h3(ix + dx, iy + dy, iz + dz, seed) * wx * wy * wz
    return out


def fbm3(x, y, z, seed=0, octaves=3):
    """Signed fractal noise, about -1..1."""
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * (noise3(x * freq, y * freq, z * freq, seed + o * 31) * 2 - 1)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def noise2(x, y, seed=0):
    return noise3(x, y, 0.37, seed)


def fbm2(x, y, seed=0, octaves=4):
    return fbm3(x, y, 0.37, seed, octaves)


# ======================================================================================================================
# geometry containers
# ======================================================================================================================
class Geo:
    """Welded indexed faces (triangles and quads only) in Roblox studs."""

    KEY = 1e4

    def __init__(self):
        self.v = []
        self.f = []
        self._k = {}

    def vid(self, p):
        k = (int(round(p[0] * self.KEY)), int(round(p[1] * self.KEY)), int(round(p[2] * self.KEY)))
        i = self._k.get(k)
        if i is None:
            i = len(self.v)
            self._k[k] = i
            self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return i

    def face(self, *pts):
        """Adds a triangle or quad from points; repeated corners are dropped, slivers refused."""
        ids = []
        for p in pts:
            i = self.vid(p)
            if not ids or ids[-1] != i:
                ids.append(i)
        if len(ids) > 1 and ids[0] == ids[-1]:
            ids.pop()
        if len(ids) < 3 or len(set(ids)) != len(ids):
            return False
        if len(ids) == 4:
            # a quad folded into a line or a triangle is split or dropped
            a = [self.v[i] for i in ids]
            if self._area(a[0], a[1], a[2]) < 1e-9 and self._area(a[0], a[2], a[3]) < 1e-9:
                return False
        elif self._area(*[self.v[i] for i in ids]) < 1e-9:
            return False
        self.f.append(tuple(ids))
        return True

    @staticmethod
    def _area(a, b, c):
        n = vcross(vsub(b, a), vsub(c, a))
        return 0.5 * vlen(n)

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def points(self, f):
        return [self.v[i] for i in f]

    def bounds(self):
        if not self.v:
            return (0, 0, 0), (0, 0, 0)
        xs, ys, zs = zip(*self.v)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def face_normal(self, f):
        pts = self.points(f)
        n = (0.0, 0.0, 0.0)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]), n[2] + (a[0] - b[0]) * (a[1] + b[1]))
        return vnorm(n)

    def face_centre(self, f):
        pts = self.points(f)
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), sum(p[2] for p in pts) / len(pts))

    # ---- topology ----
    def components(self):
        parent = list(range(len(self.v)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for f in self.f:
            for i in f[1:]:
                a, b = find(f[0]), find(i)
                if a != b:
                    parent[a] = b
        comps = {}
        for n, f in enumerate(self.f):
            comps.setdefault(find(f[0]), []).append(n)
        return list(comps.values())

    def open_edges(self):
        """Edges used by one face only (not watertight), and edges used by more than two."""
        count = {}
        for f in self.f:
            for k in range(len(f)):
                e = (min(f[k], f[(k + 1) % len(f)]), max(f[k], f[(k + 1) % len(f)]))
                count[e] = count.get(e, 0) + 1
        return sum(1 for c in count.values() if c == 1), sum(1 for c in count.values() if c > 2)

    def volume(self, face_ids):
        vol = 0.0
        for n in face_ids:
            pts = self.points(self.f[n])
            for k in range(1, len(pts) - 1):
                vol += vdot(pts[0], vcross(pts[k], pts[k + 1])) / 6.0
        return vol

    def orient(self):
        """Each connected shell is wound outward: a shell whose signed volume is negative is turned inside out."""
        for comp in self.components():
            if self.volume(comp) < 0:
                for n in comp:
                    self.f[n] = tuple(reversed(self.f[n]))
        return self

    # ---- merging ----
    def add(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0, tilt=None):
        """Merges a transformed copy of `other` as its own shell: scale (number or tuple), tilt (axis, angle) applied first, then yaw about Y, then
        translation. Its vertices are NOT welded to what is already here (two solids that touch must not share an edge)."""
        c, sn = math.cos(yaw), math.sin(yaw)
        sx, sy, sz = (s, s, s) if not isinstance(s, tuple) else s
        mirror = (sx * sy * sz) < 0
        base = len(self.v)
        for (x, y, z) in other.v:
            p = (x * sx, y * sy, z * sz)
            if tilt:
                p = rot_axis(p, tilt[0], tilt[1])
            self.v.append((p[0] * c + p[2] * sn + t[0], p[1] + t[1], -p[0] * sn + p[2] * c + t[2]))
        for f in other.f:
            fid = [i + base for i in f]
            if mirror:
                fid.reverse()
            self.f.append(tuple(fid))
        return self

    def bad_winding(self):
        """Directed edges used by more than one face (inconsistent winding) and edges used by one only (open)."""
        seen = {}
        for f in self.f:
            for k in range(len(f)):
                e = (f[k], f[(k + 1) % len(f)])
                seen[e] = seen.get(e, 0) + 1
        twice = sum(1 for c in seen.values() if c > 1)
        open_ = sum(1 for (a, b) in seen if (b, a) not in seen)
        return twice, open_

    def transform(self, fn):
        g = Geo()
        for f in self.f:
            g.face(*[fn(self.v[i]) for i in f])
        return g

    def compact(self):
        used = sorted({i for f in self.f for i in f})
        remap = {o: n for n, o in enumerate(used)}
        self.v = [self.v[i] for i in used]
        self.f = [tuple(remap[i] for i in f) for f in self.f]
        self._k = {}
        for i, p in enumerate(self.v):
            self._k[(int(round(p[0] * self.KEY)), int(round(p[1] * self.KEY)), int(round(p[2] * self.KEY)))] = i
        return self


class Piece:
    """A finished model: material suffix -> Geo, plus colliders, markers and notes for the placements."""

    def __init__(self, name):
        self.name = name
        self.g = {}
        self.colliders = []   # (kind, centre, size, yaw) in the piece's frame; kind "box" or "cyl" (size = (diameter, height, diameter))
        self.marks = {}       # name -> (position, yaw): lips of waterfalls, doors, stand spots ...
        self.notes = {}

    def geo(self, mat):
        return self.g.setdefault(mat, Geo())

    def put(self, shell, mat, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0, tilt=None, orient=True):
        """Merges a (closed) shell. `mat` is a suffix or a chooser (normal, centre) -> suffix, called on the transformed face."""
        if orient:
            shell.orient()
        if isinstance(mat, str):
            self.geo(mat).add(shell, t, yaw, s, tilt)
            return self
        tmp = Geo().add(shell, t, yaw, s, tilt)
        maps = {}
        for f in tmp.f:
            m = mat(tmp.face_normal(f), tmp.face_centre(f))
            if not m:
                continue
            g = self.geo(m)
            mp = maps.setdefault(m, {})
            ids = []
            for i in f:
                j = mp.get(i)
                if j is None:
                    j = len(g.v)
                    g.v.append(tmp.v[i])
                    mp[i] = j
                ids.append(j)
            g.f.append(tuple(ids))
        return self

    def add_piece(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0, tilt=None):
        for m, g in other.g.items():
            self.geo(m).add(g, t, yaw, s, tilt)
        c, sn = math.cos(yaw), math.sin(yaw)
        for kind, ctr, size, cy in other.colliders:
            x, y, z = ctr[0] * s, ctr[1] * s, ctr[2] * s
            self.colliders.append((kind, (x * c + z * sn + t[0], y + t[1], -x * sn + z * c + t[2]), (size[0] * s, size[1] * s, size[2] * s), cy + yaw))
        for k, (p, py) in other.marks.items():
            x, y, z = p[0] * s, p[1] * s, p[2] * s
            self.marks[k] = ((x * c + z * sn + t[0], y + t[1], -x * sn + z * c + t[2]), py + yaw)
        return self

    def merge(self, mapping):
        """Moves each source material's geometry into the destination material (`mapping` = {from suffix: to suffix}): fewer meshes per piece (each mesh is one MeshPart in the game).
        The shells stay separate (Geo.add does not weld), so nothing that touched stays welded."""
        for src, dst in mapping.items():
            if src in self.g and src != dst:
                g = self.g.pop(src)
                self.geo(dst).add(g)
        return self

    def tris(self):
        return sum(g.tris() for g in self.g.values())

    def bounds(self):
        lo = [1e9] * 3
        hi = [-1e9] * 3
        for g in self.g.values():
            if not g.f:
                continue
            a, b = g.bounds()
            lo = [min(lo[i], a[i]) for i in range(3)]
            hi = [max(hi[i], b[i]) for i in range(3)]
        return tuple(lo), tuple(hi)

    def stats(self):
        return {m: g.tris() for m, g in sorted(self.g.items())}

    def box(self, centre, size, yaw=0.0):
        self.colliders.append(("box", centre, size, yaw))
        return self

    def cyl(self, centre, diameter, height, yaw=0.0):
        self.colliders.append(("cyl", centre, (diameter, height, diameter), yaw))
        return self


# ======================================================================================================================
# curves and frames
# ======================================================================================================================
def catmull(points, per=4):
    pts = [tuple(p) for p in points]
    if len(pts) == 2:
        return [vlerp(pts[0], pts[1], k / float(per)) for k in range(per)] + [pts[1]]
    ext = [vsub(vmul(pts[0], 2), pts[1])] + pts + [vsub(vmul(pts[-1], 2), pts[-2])]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(per):
            t = s / float(per)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(3)))
    out.append(pts[-1])
    return out


def frames(curve, up=(0.0, 1.0, 0.0)):
    """Tangent, normal and binormal at each point of a curve (parallel transport; the first normal is the `up` vector squared to the tangent)."""
    n = len(curve)
    T = [vnorm(vsub(curve[min(i + 1, n - 1)], curve[max(i - 1, 0)])) for i in range(n)]
    ref = up if abs(vdot(T[0], up)) < 0.95 else (1.0, 0.0, 0.0)
    N = vnorm(vsub(ref, vmul(T[0], vdot(T[0], ref))))
    out = []
    for i in range(n):
        N = vsub(N, vmul(T[i], vdot(T[i], N)))
        N = vnorm(N)
        B = vcross(T[i], N)
        out.append((T[i], N, B))
    return out


def _fn(x):
    return x if callable(x) else (lambda t, x=x: x)


# ======================================================================================================================
# primitives: each returns a closed Geo shell
# ======================================================================================================================
def loft(rings, cap0=True, cap1=True, closed=True):
    """Quads between consecutive rings (lists of points, same length); the ends are capped by a fan to the ring's centre."""
    g = Geo()
    n = len(rings[0])
    last = n if closed else n - 1
    for r in range(len(rings) - 1):
        a, b = rings[r], rings[r + 1]
        for i in range(last):
            j = (i + 1) % n
            g.face(a[i], a[j], b[j], b[i])
    for flag, ring, first in ((cap0, rings[0], True), (cap1, rings[-1], False)):
        if flag:
            c = tuple(sum(p[k] for p in ring) / n for k in range(3))
            for i in range(n):
                if first:
                    g.face(ring[(i + 1) % n], ring[i], c)
                else:
                    g.face(ring[i], ring[(i + 1) % n], c)
    return g


def tube(path, rn, rb=None, sides=8, per=4, up=(0.0, 1.0, 0.0), caps=(True, True), wob=0.0, seed=0, smooth=True, twist=0.0, shape=None):
    """A tube along a Catmull-Rom path through `path`. rn / rb: radius along the normal and binormal (numbers or functions of t in 0..1; rb
    defaults to rn); wob: radial noise; twist: turns of the ring about the path over its length; shape(t, a) multiplies the radius at ring angle a."""
    curve = catmull(path, per) if smooth else list(path)
    fr = frames(curve, up)
    rn_f = _fn(rn)
    rb_f = rn_f if rb is None else _fn(rb)
    n = len(curve)
    rings = []
    for i, (c, (T, N, B)) in enumerate(zip(curve, fr)):
        t = i / float(n - 1)
        ring = []
        for k in range(sides):
            a = TAU * k / sides + twist * TAU * t
            w = 1.0 + wob * (noise3(i * 0.9 + seed, k * 1.7, seed * 0.3, seed) - 0.5) * 2
            if shape:
                w *= shape(t, a)
            ca, sa = math.cos(a), math.sin(a)
            ring.append((c[0] + (N[0] * ca * rn_f(t) + B[0] * sa * rb_f(t)) * w,
                         c[1] + (N[1] * ca * rn_f(t) + B[1] * sa * rb_f(t)) * w,
                         c[2] + (N[2] * ca * rn_f(t) + B[2] * sa * rb_f(t)) * w))
        rings.append(ring)
    return loft(rings, caps[0], caps[1])


def ellipsoid(c=(0, 0, 0), r=(1, 1, 1), seg=10, rings=6, noise=0.0, seed=0, flat=None, yaw=0.0, tilt=None, freq=1.0, bulge=None):
    """A lumpy ellipsoid (lat-long mesh with polar fans). noise: radial displacement (fraction of the radius, 3-D fractal noise at `freq`);
    flat = y below which the surface is cut flat (a boulder's buried base); bulge(theta, phi) multiplies the radius (ruffles, lobes)."""
    g = Geo()
    grid = []
    for k in range(rings + 1):
        phi = math.pi * k / rings          # 0 at the top pole
        ring = []
        for i in range(seg if 0 < k < rings else 1):
            th = TAU * i / seg
            x, y, z = math.sin(phi) * math.cos(th), math.cos(phi), math.sin(phi) * math.sin(th)
            w = 1.0
            if noise:
                w += noise * fbm3(x * freq * 1.7 + seed, y * freq * 1.7, z * freq * 1.7 - seed, seed, 2)
            if bulge:
                w *= bulge(th, phi)
            p = (x * r[0] * w, y * r[1] * w, z * r[2] * w)
            if flat is not None and p[1] < flat:
                p = (p[0], flat, p[2])
            if tilt:
                p = rot_axis(p, tilt[0], tilt[1])
            xs, zs = p[0] * math.cos(yaw) + p[2] * math.sin(yaw), -p[0] * math.sin(yaw) + p[2] * math.cos(yaw)
            ring.append((c[0] + xs, c[1] + p[1], c[2] + zs))
        grid.append(ring)
    for k in range(rings):
        a, b = grid[k], grid[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            if k == 0:
                g.face(a[0], b[j], b[i])
            elif k == rings - 1:
                g.face(a[i], a[j], b[0])
            else:
                g.face(a[i], a[j], b[j], b[i])
    return g


def dome(c, r, hem, seg=10, rings=4, noise=0.0, seed=0, yaw=0.0, freq=1.0):
    """The upper part of a lumpy ellipsoid down to the height `hem` (relative to its centre c), closed by a flat fan: a blanket thrown over a rock."""
    g = Geo()
    phi_h = math.acos(max(-1.0, min(1.0, hem / r[1])))
    grid = []
    for k in range(rings + 1):
        phi = phi_h * k / rings
        ring = []
        for i in range(seg if k > 0 else 1):
            th = TAU * i / seg
            x, y, z = math.sin(phi) * math.cos(th), math.cos(phi), math.sin(phi) * math.sin(th)
            w = 1.0 + (noise * fbm3(x * freq * 1.7 + seed, y * freq * 1.7, z * freq * 1.7 - seed, seed, 2) if noise else 0.0)
            p = (x * r[0] * w, y * r[1] * w if k < rings else hem, z * r[2] * w)
            xs, zs = p[0] * math.cos(yaw) + p[2] * math.sin(yaw), -p[0] * math.sin(yaw) + p[2] * math.cos(yaw)
            ring.append((c[0] + xs, c[1] + p[1], c[2] + zs))
        grid.append(ring)
    for k in range(rings):
        a, b = grid[k], grid[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            if k == 0:
                g.face(a[0], b[j], b[i])
            else:
                g.face(a[i], a[j], b[j], b[i])
    last = grid[-1]
    centre = (c[0], c[1] + hem, c[2])
    for i in range(seg):
        g.face(last[i], last[(i + 1) % seg], centre)
    return g


def lathe(profile, seg=10, c=(0, 0, 0), mod=None, phase=0.0):
    """Surface of revolution about +Y. profile: [(radius, y), ...] from the bottom up; radius 0 at an end closes it to a point, otherwise the end
    is capped flat. mod(theta, k) multiplies ring k's radius at angle theta."""
    rings = []
    for k, (r, y) in enumerate(profile):
        ring = []
        for i in range(seg):
            th = TAU * i / seg + phase
            rr = r * (mod(th, k) if mod else 1.0)
            ring.append((c[0] + math.cos(th) * rr, c[1] + y, c[2] + math.sin(th) * rr))
        rings.append(ring)
    g = Geo()
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            g.face(a[i], a[j], b[j], b[i])
    for first, ring, (r, y) in ((True, rings[0], profile[0]), (False, rings[-1], profile[-1])):
        cc = (c[0], c[1] + y, c[2])
        for i in range(seg):
            if first:
                g.face(ring[(i + 1) % seg], ring[i], cc)
            else:
                g.face(ring[i], ring[(i + 1) % seg], cc)
    return g


_BOX_N = [0]


def box(c, size, yaw=0.0, tilt=None, jit=True):
    """An axis box. Its four side faces are nudged by a different few thousandths each time (the top and bottom stay exact), so two boxes that share
    a plane never z-fight."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    if jit:
        _BOX_N[0] += 1
        k = _BOX_N[0]
        hx += 0.0035 * (1 + k % 5)
        hz += 0.0035 * (1 + (k * 3) % 5)
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]
    return _hexa(pts, c, yaw, tilt)


def _hexa(pts, c, yaw, tilt):
    g = Geo()
    cs, sn = math.cos(yaw), math.sin(yaw)
    q = []
    for p in pts:
        if tilt:
            p = rot_axis(p, tilt[0], tilt[1])
        q.append((c[0] + p[0] * cs + p[2] * sn, c[1] + p[1], c[2] - p[0] * sn + p[2] * cs))
    for idx in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        g.face(*[q[i] for i in idx])
    return g


def chunk(c, size, seed=0, jit=0.12, yaw=0.0, taper=0.0, tilt=None, chip=0.0):
    """A hewn block: a box whose eight corners are nudged (jit = fraction of the size) and whose top can taper in (taper) so no two are the same."""
    rnd = random.Random(seed)
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    pts = []
    for sy in (-1, 1):
        for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            k = (1 - taper) if sy > 0 else 1.0
            pts.append((sx * hx * k + rnd.uniform(-jit, jit) * size[0], sy * hy + rnd.uniform(-jit, jit) * size[1] * (0.6 if sy < 0 else 1.0), sz * hz * k + rnd.uniform(-jit, jit) * size[2]))
    if chip:
        p = list(pts[6])
        p[1] -= chip * size[1]
        pts[6] = tuple(p)
    return _hexa(pts, c, yaw, tilt)


def prism(poly, y0, y1, c=(0, 0, 0), yaw=0.0):
    """A convex polygon [(x, z), ...] (counter-clockwise seen from above is not required) extruded from y0 to y1."""
    g = Geo()
    cs, sn = math.cos(yaw), math.sin(yaw)

    def P(x, y, z):
        return (c[0] + x * cs + z * sn, c[1] + y, c[2] - x * sn + z * cs)
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cz = sum(p[1] for p in poly) / n
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        g.face(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]))
        g.face(P(a[0], y1, a[1]), P(b[0], y1, b[1]), P(cx, y1, cz))
        g.face(P(b[0], y0, b[1]), P(a[0], y0, a[1]), P(cx, y0, cz))
    return g


def blade(base, direction, length, width, droop=0.0, thick=0.05, segs=4, mid=0.38, up=(0.0, 1.0, 0.0), keel=0.0, trough=0.0, base_w=0.14, sweep=0.0, width_fn=None):
    """A closed leaf blade: a lanceolate strip, widest at `mid` of its length and a point at its end, rising along `direction` and falling away
    (droop: how far the tip falls, as a fraction of the length), solid from both sides (two surfaces `thick` apart that meet at the tip).
    keel lifts the midrib, trough lifts the two edges (a shallow gutter); sweep curves the tip sideways (fraction of the length)."""
    d = vnorm(direction)
    side = vnorm(vcross(d, up)) if abs(vdot(d, up)) < 0.98 else (1.0, 0.0, 0.0)
    pts = [base]
    cur = base
    for s in range(1, segs + 1):
        t = s / float(segs)
        dd = vnorm(vadd(vadd(d, vmul(up, -droop * t * 2.4)), vmul(side, sweep * t)))
        cur = vadd(cur, vmul(dd, length / segs))
        pts.append(cur)
    fr = frames(pts, up)
    a_exp = math.log(0.5) / math.log(mid)
    rows_t, rows_b = [], []
    for s, p in enumerate(pts):
        t = s / float(segs)
        T, N, B = fr[s]
        w = width * (base_w * (1 - t) + (1 - base_w) * math.sin(math.pi * (t ** a_exp)) if t < 1.0 else 0.0)
        if width_fn is not None:
            w = width * width_fn(t) if t < 1.0 else 0.0
        th = thick * (1.0 - t * t) if t < 1.0 else 0.0
        rt, rb = [], []
        for sg in (-1, 0, 1):
            lift = (keel if sg == 0 else trough * abs(sg)) * w
            off = vmul(B, sg * w)
            base_p = vadd(p, off)
            rt.append(vadd(base_p, vmul(N, th / 2 + lift)))
            rb.append(vadd(base_p, vmul(N, -th / 2 + lift * 0.0)))
        rows_t.append(rt)
        rows_b.append(rb)
    g = Geo()
    for s in range(segs):
        for k in range(2):
            g.face(rows_t[s][k], rows_t[s + 1][k], rows_t[s + 1][k + 1], rows_t[s][k + 1])
            g.face(rows_b[s][k], rows_b[s][k + 1], rows_b[s + 1][k + 1], rows_b[s + 1][k])
        g.face(rows_t[s][0], rows_b[s][0], rows_b[s + 1][0], rows_t[s + 1][0])
        g.face(rows_t[s][2], rows_t[s + 1][2], rows_b[s + 1][2], rows_b[s][2])
    g.face(rows_t[0][0], rows_t[0][1], rows_b[0][1], rows_b[0][0])
    g.face(rows_t[0][1], rows_t[0][2], rows_b[0][2], rows_b[0][1])
    return g


def cone_fan(apex, ring_pts):
    g = Geo()
    n = len(ring_pts)
    for i in range(n):
        g.face(ring_pts[i], ring_pts[(i + 1) % n], apex)
    return g


# ======================================================================================================================
# the leaf tier: Jade Grove's foliage form
# ======================================================================================================================
def leaf_tier(c, R, H, seg=16, lobes=5, ruffle=0.2, droop=0.42, seed=0, lean=(0.0, 0.0), flat=0.0, under=0.3, tip_len=(0.55, 1.0), bump=0.16):
    """A ruffled, scalloped leaf tier: a lumpy dome of leaf on top, a wavy rim (`lobes` scallops, `ruffle` deep) and a fringe of drooping leaf
    points hanging below it. R = radius, H = height of the dome above the rim, droop = how far the longest points hang (fraction of R), under
    = how much the underside is dished, bump = how lumpy the dome is. lean = (dx, dz) shifts the top over the rim; flat 0..1 flattens the dome
    into a plate. One closed shell."""
    rnd = random.Random(seed)
    ph, ph2 = rnd.uniform(0, TAU), rnd.uniform(0, TAU)
    jit = [rnd.uniform(-1, 1) for _ in range(seg)]
    tipk = [rnd.uniform(tip_len[0], tip_len[1]) if i % 2 == 0 else rnd.uniform(0.0, 0.16) for i in range(seg)]

    def w(th, i):
        return 1.0 + ruffle * math.sin(lobes * th + ph) + ruffle * 0.5 * math.sin((2 * lobes + 1) * th + ph2) + 0.07 * jit[i]
    top = 1.0 - 0.55 * flat
    prof = [(0.0, -under * H * 0.7), (0.5, -under * H), (0.9, -under * H * 0.55), (1.0, 0.0), (0.94, 0.42 * H * (1 + flat * 0.5)), (0.68, 0.82 * H * top + 0.15 * H * flat), (0.0, H * (1.0 - 0.1 * flat))]
    rings = []
    for k, (r, y) in enumerate(prof):
        ring = []
        for i in range(seg):
            th = TAU * i / seg
            ww = w(th, i) if 0 < k < len(prof) - 1 else 1.0
            rr = r * R * ww
            yy = y
            if k == 2:       # the fringe: every other point drops into a leaf tip, hanging from just inside the rim
                yy = y - droop * R * tipk[i]
                rr = r * R * ww * (1.0 + 0.05 * tipk[i])
            if k in (4, 5) and bump:
                n1 = noise3(math.cos(th) * 1.6 + seed, k * 0.9, math.sin(th) * 1.6, seed) - 0.5
                yy += bump * H * 2.0 * n1
                rr *= 1.0 + bump * n1
            lx = lean[0] * smoothstep(3, 6, k)
            lz = lean[1] * smoothstep(3, 6, k)
            ring.append((c[0] + math.cos(th) * rr + lx, c[1] + yy, c[2] + math.sin(th) * rr + lz))
        rings.append(ring)
    return loft(rings, True, True)


def apply_merges(pieces):
    """Applies jade_lib_looks.MERGE (the polish pass's part-count cuts) to a family's finished pieces; returns the same dict."""
    import jade_lib_looks as LK
    for name, piece in pieces.items():
        m = LK.MERGE.get(name)
        if m:
            piece.merge(m)
    return pieces

"""The Blossom Sanctuary's meshes (2026-11-16, the owner's directive: 22 Worked Builds/Blossom Sanctuary Directive.md).

"A professionally handcrafted cultivation sanctuary, not a generic garden asset pack": nature shaped by cultivators. One material
language for everything: dark plum-brown bark, rose and near-white blush blossom, warm ivory water-worn stone with moss where the
water touches, lilies and reeds in two greens, koi in four colours.

Every piece is authored in Roblox studs (worldlib.rb: Roblox Y up, the piece's front toward Roblox +Z) at its own origin: the ground
contact point under its base centre (y = 0 on the ground); the koi and the ripple at their centre. Each piece is split by material
into objects named <Piece>__<Material> (BS_TreeElder__Bark, BS_TreeElder__Blossom, ...). No textures: Studio sets each part's
Roblox material and colour from the suffix. UVs are box projected, one tile per 8 studs, every chart inside 0-1.

Construction, by kind:
- trees: a hand-placed skeleton per tree (trunk, limbs, the branches that carry each blossom mass), swept tubes with root flare,
  spiral bark ridges and wobble; each blossom mass is two metaball clouds (a pale crown over a rose under-layer), decimated to its
  budget. Nothing but the trunk comes below 7.5 studs (players walk under the canopies).
- stone: lathed and swept forms, worn by low-frequency noise, moss as a thin closed shell that sinks into the stone.
- water life and koi: lathed and lens-shaped forms; the koi's colour patches are cut out of the body's own surface.

    blender -b --factory-startup -P tools/blender/world/blossom_assets_run.py -- <stage> [pieces]
"""
import math
import random

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import worldlib as W

TAU = 2 * math.pi

# preview colours (sRGB 0-255); the game sets the final look from the suffix
COLOURS = {
    "Bark": (86, 60, 58), "Blossom": (232, 146, 176), "BlossomPale": (250, 216, 228), "Stone": (222, 212, 192),
    "Moss": (96, 126, 70), "Lily": (74, 124, 66), "LilyFlower": (252, 238, 242), "Reed": (102, 138, 78),
    "KoiWhite": (246, 243, 236), "KoiRed": (226, 82, 40), "KoiBlack": (32, 30, 32), "KoiGold": (240, 182, 72),
    "KoiFin": (250, 238, 226), "Ripple": (255, 255, 255),
}
TILE = 8.0
CANOPY_FLOOR = 7.5        # nothing but a trunk below this (studs above the ground)


# ======================================================================================================================
# Geometry in Roblox studs
# ======================================================================================================================
class Geo:
    """An indexed mesh in Roblox studs. closed: every island is watertight (its normals are recomputed outward)."""

    def __init__(self, closed=True):
        self.v, self.f, self.closed = [], [], closed

    def vert(self, p):
        self.v.append(Vector(p))
        return len(self.v) - 1

    def face(self, *idx):
        self.f.append(list(idx))

    def add(self, other):
        o = len(self.v)
        self.v += [p.copy() for p in other.v]
        self.f += [[i + o for i in f] for f in other.f]
        return self

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def bounds(self):
        lo = Vector((min(p.x for p in self.v), min(p.y for p in self.v), min(p.z for p in self.v)))
        hi = Vector((max(p.x for p in self.v), max(p.y for p in self.v), max(p.z for p in self.v)))
        return lo, hi

    def bvh(self):
        tri = []
        for f in self.f:
            for k in range(1, len(f) - 1):
                tri.append((f[0], f[k], f[k + 1]))
        return BVHTree.FromPolygons(self.v, tri, epsilon=0.0)

    def transform(self, fn):
        self.v = [Vector(fn(p)) for p in self.v]
        return self


def lerp(a, b, t):
    return a + (b - a) * t


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def yaw_vec(az, r=1.0, y=0.0):
    """A point at bearing az (radians, from +X toward +Z), radius r, height y."""
    return Vector((math.cos(az) * r, y, math.sin(az) * r))


# ---------- swept tubes ----------
def frames(curve):
    n = len(curve)
    T = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    N = (ref - T[0] * ref.dot(T[0])).normalized()
    out = []
    for i in range(n):
        N = (N - T[i] * N.dot(T[i])).normalized()
        out.append((T[i], N, T[i].cross(N)))
    return out


def resample(points, per):
    return [Vector(p) for p in W.catmull([Vector(p) for p in points], per)]


def arc_lengths(curve):
    L = [0.0]
    for a, b in zip(curve, curve[1:]):
        L.append(L[-1] + (b - a).length)
    return L


def tube(g, curve, rf, sides, cap0=True, cap1=True, tip=0.5, phase=0.0):
    """Sweeps a ring along `curve` (Vectors, Roblox studs). rf(t, s, d, c): the radius at curve fraction t, arc length s,
    world direction d of the ring vertex, centre c. Closed at both ends (a flat start cap, a short tip at the end)."""
    fr = frames(curve)
    L = arc_lengths(curve)
    rings = []
    for i, c in enumerate(curve):
        T, N, B = fr[i]
        t = L[i] / L[-1]
        ring = []
        for k in range(sides):
            a = TAU * k / sides + phase
            d = N * math.cos(a) + B * math.sin(a)
            ring.append(g.vert(c + d * rf(t, L[i], d, c)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            j = (k + 1) % sides
            g.face(rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k])
    if cap0:
        c = g.vert(curve[0] - fr[0][0] * 0.02)
        for k in range(sides):
            g.face(c, rings[0][(k + 1) % sides], rings[0][k])
    if cap1:
        r_end = (g.v[rings[-1][0]] - curve[-1]).length
        c = g.vert(curve[-1] + fr[-1][0] * r_end * tip)
        for k in range(sides):
            g.face(c, rings[-1][k], rings[-1][(k + 1) % sides])
    return rings


def bark_rf(r0, r1, ridges=0, ridge_depth=0.0, twist=0.0, wobble=0.06, seed=0, flare=None, taper=1.0, knots=()):
    """A bark radius function: taper r0 -> r1, spiral ridges (count, depth as a fraction, twist in turns over the length),
    a low-frequency wobble, an optional root flare (amp, lobes, height, phase) by height above the ground, and knots
    [(t, amp, width)] (burls)."""
    def rf(t, s, d, c):
        r = r0 + (r1 - r0) * (t ** taper)
        az = math.atan2(d.z, d.x)
        if ridges:
            ph = ridges * az + twist * TAU * t
            r *= 1.0 + ridge_depth * (abs(math.cos(ph * 0.5)) ** 0.6 * 2.0 - 1.0)
        if wobble:
            r *= 1.0 + wobble * W.fbm(az * 1.3 + seed, s * 0.35, seed, octaves=3)
        for kt, amp, width in knots:
            r *= 1.0 + amp * math.exp(-((t - kt) / width) ** 2)
        if flare:
            amp, lobes, height, fph = flare
            h = c.y
            f = (1.0 - smooth01(h / height)) ** 2
            lobe = max(0.0, math.cos(lobes * (az - fph))) ** 1.5
            r *= 1.0 + amp * f * (0.35 + 0.65 * lobe)
        return r
    return rf


# ---------- blossom clouds (metaballs, meshed and decimated) ----------
_MB = [0]
MB_SCALE = 0.575       # a lone ball of radius r meshes to a sphere of r * MB_SCALE (stiffness 2, threshold 0.6)


def _rb_inv(v):
    return Vector((v.x, v.z, -v.y))


def _clean_cloud(me):
    """A meshed cloud -> Geo: only its main body kept (a floret the metaball left apart is dropped), and whether it is a clean
    closed manifold with consistent winding."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    seen, islands = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            isl.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    drop = [v for isl in islands[1:] for v in isl]
    if drop:
        bmesh.ops.delete(bm, geom=drop, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ok = all(len(e.link_faces) == 2 for e in bm.edges)
    if ok:
        from collections import Counter
        directed = Counter((l.vert.index, l.link_loop_next.vert.index) for f in bm.faces for l in f.loops)
        ok = all(c == 1 for c in directed.values()) and all(f.calc_area() > 1e-8 for f in bm.faces)
    g = Geo()
    bm.verts.index_update()
    g.v = [_rb_inv(v.co) for v in bm.verts]
    g.f = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return g, ok


def cloud(balls, tris, res=None, squash=None, centre=None, noise=0.0, seed=0):
    """A closed organic mass: the merged surface of balls [(centre, radius)] (Roblox studs), decimated to about `tris`
    triangles. squash (sx, sy, sz) scales the result about `centre`."""
    _MB[0] += 1
    name = "BSmeta%d" % _MB[0]
    rmax = max(r for _, r in balls)
    mb = bpy.data.metaballs.new(name)
    mb.resolution = mb.render_resolution = res or max(0.12, rmax / 7.0)
    mb.threshold = 0.6
    for c, r in balls:
        e = mb.elements.new(type="BALL")
        e.co = W.rb(*c)
        e.radius = r / MB_SCALE
        e.stiffness = 2.0
    o = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(o)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    have = sum(len(p.vertices) - 2 for p in me.polygons)
    g = None
    for attempt in range(6):
        tmp = bpy.data.objects.new(name + "_d", me)
        bpy.context.scene.collection.objects.link(tmp)
        if have > tris:
            d = tmp.modifiers.new("Decimate", "DECIMATE")
            d.ratio = tris / have * (1.0 - 0.025 * attempt)
            d.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        bpy.data.objects.remove(tmp, do_unlink=True)
        g, ok = _clean_cloud(me2)
        bpy.data.meshes.remove(me2)
        if ok:
            break
    bpy.data.meshes.remove(me)
    if squash:
        cc = Vector(centre) if centre is not None else sum(g.v, Vector()) / len(g.v)
        g.transform(lambda p: Vector((cc.x + (p.x - cc.x) * squash[0], cc.y + (p.y - cc.y) * squash[1], cc.z + (p.z - cc.z) * squash[2])))
    if noise:
        cc = sum(g.v, Vector()) / len(g.v)
        g.transform(lambda p: p + (p - cc).normalized() * noise * W.fbm(p.x * 0.6 + p.y * 0.3, p.z * 0.6 - p.y * 0.2, seed, octaves=2))
    return g


# ======================================================================================================================
# Trees
# ======================================================================================================================
class Tree:
    """A tree under construction: its trunk(s), branches and blossom masses, kept apart so the checks can tell them apart."""

    def __init__(self, name, seed):
        self.name = name
        self.rng = random.Random(seed)
        self.seed = seed
        self.trunk = Geo()
        self.branches = Geo()
        self.limbs = []        # [(curve, radius fn of t)] that branches can grow from
        self.clouds = []       # [(tone, Geo, mass id)]
        self.masses = []       # [(centre, rx, ry)]
        self.axis = (0.0, 0.0)  # the crown's vertical axis (x, z): a mass's rose side faces it

    # --- skeleton ---
    def add_trunk(self, pts, rf, sides=14, per=4, cap0=True):
        curve = resample(pts, per)
        tube(self.trunk, curve, rf, sides, cap0=cap0)
        return curve

    def add_limb(self, pts, r0, r1, sides=9, per=4, trunk=False, ridges=0, ridge_depth=0.0, twist=0.0, wobble=0.07, knots=(),
                 taper=0.9):
        curve = resample(pts, per)
        rf = bark_rf(r0, r1, ridges, ridge_depth, twist, wobble, self.rng.randint(0, 999), knots=knots, taper=taper)
        tube(self.trunk if trunk else self.branches, curve, rf, sides)
        self.limbs.append((curve, lambda t, a=r0, b=r1: a + (b - a) * t))
        return curve

    def point_on(self, curve, t):
        L = arc_lengths(curve)
        s = t * L[-1]
        for i in range(len(curve) - 1):
            if L[i + 1] >= s:
                u = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
                return curve[i].lerp(curve[i + 1], u)
        return curve[-1].copy()

    def nearest_on_limbs(self, target, t_min=0.25, below=True, limbs=None):
        best = None
        for li, (curve, rad) in enumerate(limbs if limbs is not None else self.limbs):
            L = arc_lengths(curve)
            for i, p in enumerate(curve):
                t = L[i] / L[-1]
                if t < t_min:
                    continue
                d = (p - target).length
                if below and p.y > target.y + 0.5:
                    d += (p.y - target.y) * 2.0
                if best is None or d < best[0]:
                    best = (d, li, t, p.copy())
        return best

    def branch_to(self, target, start=None, limb=None, t=None, r_end=0.13, arch=0.15, side=0.0, sides=6, droop=0.0, per=2,
                  r_start=None, trunk=False):
        """A branch from a limb (nearest point, or the given limb and t) arching to `target`. Returns its curve."""
        target = Vector(target)
        if start is None:
            if limb is None:
                _, li, t, start = self.nearest_on_limbs(target)
                limb = li
            else:
                start = self.point_on(self.limbs[limb][0], t)
        start = Vector(start)
        parent_r = self.limbs[limb][1](t) if limb is not None else 0.3
        span = target - start
        n = span.length
        lateral = span.cross(Vector((0, 1, 0)))
        lateral = lateral.normalized() if lateral.length > 1e-6 else Vector((1, 0, 0))
        m1 = start.lerp(target, 0.35) + Vector((0, arch * n - droop * n * 0.3, 0)) + lateral * side * n * 0.5
        m2 = start.lerp(target, 0.7) + Vector((0, arch * n * 0.6 - droop * n, 0)) - lateral * side * n * 0.3
        r0 = r_start if r_start is not None else max(r_end * 1.3, min(parent_r * 0.75, 0.1 + 0.035 * n))
        return self.add_limb([start, m1, m2, target], r0, r_end, sides=sides, per=per, trunk=trunk)

    # --- blossom ---
    def mass(self, centre, rx, ry, rz=None, tris=(300, 140), florets=12, under=0.5, tone_top="BlossomPale", tone_under="Blossom",
             under_spread=1.0, lean=(0.0, 0.0)):
        """A blossom mass: a pale crown of merged core balls covered in florets (the bumpy cauliflower surface of massed
        flowers), over a lumpy rose under-layer that shows along its lower edge and underneath. lean (dx, dz): the crown's top
        drifts that way (wind, light). Returns the mass centre."""
        rng = self.rng
        c = Vector(centre)
        rz = rz or rx
        mid = len(self.masses)
        balls = []
        n_core = max(2, int(round(max(rx, rz) / ry * 1.2)))
        a0 = rng.uniform(0, TAU)
        core_r = ry * 0.95
        balls.append((c + Vector((0, ry * 0.1, 0)), core_r))
        for k in range(n_core):
            a = a0 + TAU * k / n_core + rng.uniform(-0.3, 0.3)
            rr = rng.uniform(0.42, 0.62)
            balls.append((c + Vector((math.cos(a) * (rx - core_r * 0.7) * rr * 1.6, rng.uniform(-0.15, 0.1) * ry,
                                      math.sin(a) * (rz - core_r * 0.7) * rr * 1.6)), core_r * rng.uniform(0.78, 0.95)))
        for k in range(florets):
            # florets over the upper and outer surface of the mass's ellipsoid (golden-angle spread, jittered)
            u = (k + 0.5) / florets
            el = math.asin(lerp(-0.25, 0.95, u))
            a = k * 2.39996 + rng.uniform(-0.3, 0.3)
            t = (el + math.pi / 2) / math.pi
            ce = math.cos(el)
            p = c + Vector((math.cos(a) * ce * rx * 0.8 + lean[0] * t, math.sin(el) * ry * 0.85, math.sin(a) * ce * rz * 0.8 + lean[1] * t))
            balls.append((p, ry * rng.uniform(0.4, 0.55)))
        r_min = min(r for _, r in balls)
        top = cloud(balls, tris[0], res=r_min / 2.6)
        self.clouds.append((tone_top, top, mid))
        if tris[1]:
            # the rose under-layer sits on the mass's inner underside (toward the crown's axis, where the shade falls)
            inward = Vector((self.axis[0] - c.x, 0, self.axis[1] - c.z))
            inward = inward.normalized() if inward.length > 1.0 else Vector((0, 0, 0))
            cu = c + inward * rx * 0.3 + Vector((0, -ry * under, 0))
            ub = [(cu, core_r * 0.85)]
            n_u = 3 + florets // 4
            for k in range(n_u):
                a = a0 + TAU * k / n_u + rng.uniform(-0.35, 0.35)
                rr = rng.uniform(0.35, 0.55) * under_spread
                ub.append((cu + Vector((math.cos(a) * rx * rr, rng.uniform(-0.2, 0.1) * ry, math.sin(a) * rz * rr)) + inward * rx * 0.12,
                           ry * rng.uniform(0.55, 0.7)))
            r_min = min(r for _, r in ub)
            und = cloud(ub, tris[1], res=r_min / 2.2)
            self.clouds.append((tone_under, und, mid))
        self.masses.append((c, rx, ry))
        return c

    def puff(self, centre, r, tris=60, tone="BlossomPale", n=5, flat=1.0):
        """A small loose clump (a few merged florets)."""
        rng = self.rng
        c = Vector(centre)
        balls = [(c, r * 0.62)]
        for k in range(n - 1):
            a = TAU * k / (n - 1) + rng.uniform(-0.4, 0.4)
            balls.append((c + Vector((math.cos(a) * r * 0.5, rng.uniform(-0.25, 0.3) * r, math.sin(a) * r * 0.5)), r * rng.uniform(0.4, 0.52)))
        g = cloud(balls, tris, res=r * 0.4 / 2.4, squash=(1.0, flat, 1.0) if flat != 1.0 else None, centre=c)
        self.clouds.append((tone, g, len(self.masses)))
        self.masses.append((c, r, r * 0.8 * flat))
        return c

    def pad(self, centre, rx, rz, ry, tris=(420, 160), wind=(1.0, 0.0), taper=0.4, yaw=0.0):
        """A flat sculpted plateau (a trained, windswept crown layer): a level slab of merged balls over an elliptic footprint,
        thinning and fraying downwind, its top bumped with florets, a rose under-slab inset beneath it."""
        rng = self.rng
        c = Vector(centre)
        mid = len(self.masses)
        wx, wz = wind
        cs, sn = math.cos(yaw), math.sin(yaw)
        balls = []
        step = ry * 1.05
        nx, nz = int(rx / step) + 1, int(rz / step) + 1
        for i in range(-nx, nx + 1):
            for j in range(-nz, nz + 1):
                u, v = i * step + (step * 0.5 if j % 2 else 0.0), j * step * 0.9
                e = (u / rx) ** 2 + (v / rz) ** 2
                if e > 0.78 * (1.0 + 0.32 * W.fbm(math.atan2(v / rz, u / rx) * 1.4 + 3.0, 0.5, self.seed + mid, octaves=2)):
                    continue
                down = (u * wx + v * wz) / max(rx, rz)
                r = ry * (1.0 - taper * max(0.0, down)) * rng.uniform(0.85, 1.05) * (1.0 - 0.25 * e)
                x, z = u * cs + v * sn, -u * sn + v * cs
                balls.append((c + Vector((x, rng.uniform(-0.08, 0.08) * ry + ry * 0.15 * (1 - e), z)), r))
        for k in range(int(rx * rz / (ry * ry) * 0.7)):
            a, rr = rng.uniform(0, TAU), math.sqrt(rng.uniform(0, 0.62))
            u, v = math.cos(a) * rx * rr, math.sin(a) * rz * rr
            x, z = u * cs + v * sn, -u * sn + v * cs
            balls.append((c + Vector((x + wx * 0.6, ry * rng.uniform(0.55, 0.95), z + wz * 0.6)), ry * rng.uniform(0.55, 0.8)))
        n_rim = int(math.pi * (rx + rz) / (ry * 1.25))
        for k in range(n_rim):
            a = TAU * k / n_rim + rng.uniform(-0.15, 0.15)
            u, v = math.cos(a) * rx * 0.86, math.sin(a) * rz * 0.86
            down = (u * wx + v * wz) / max(rx, rz)
            x, z = u * cs + v * sn, -u * sn + v * cs
            balls.append((c + Vector((x, ry * rng.uniform(-0.05, 0.3), z)), ry * rng.uniform(0.62, 0.82) * (1.0 - 0.3 * max(0.0, down))))
        r_min = min(r for _, r in balls)
        self.clouds.append(("BlossomPale", cloud(balls, tris[0], res=max(r_min / 2.2, 0.16)), mid))
        if tris[1]:
            ub = []
            for i in range(-nx, nx + 1):
                for j in range(-nz, nz + 1):
                    u, v = i * step * 1.2, j * step * 1.1
                    if (u / (rx * 0.82)) ** 2 + (v / (rz * 0.8)) ** 2 > 0.7:
                        continue
                    x, z = u * cs + v * sn, -u * sn + v * cs
                    ub.append((c + Vector((x - wx * 0.5, -ry * 0.62, z - wz * 0.5)), ry * rng.uniform(0.7, 0.85)))
            self.clouds.append(("Blossom", cloud(ub, tris[1], res=max(min(r for _, r in ub) / 2.2, 0.16)), mid))
        self.masses.append((c, rx, ry))
        return c

    def chain(self, beads, tris, tone):
        """A hanging run of blossom beads [(centre, radius)] merged into one lumpy cloud (a weeping strand's flowers)."""
        g = cloud([(Vector(c), r) for c, r in beads], tris, res=min(r for _, r in beads) / 2.4)
        self.clouds.append((tone, g, len(self.masses)))
        self.masses.append((Vector(beads[0][0]), beads[0][1], beads[0][1]))

    def sprig(self, near_mass, offset, r, tris=60, tone="BlossomPale"):
        """A loose clump breaking the outline beside a mass, on a short twig from the branch that carries that mass."""
        c0, rx, ry = self.masses[near_mass]
        c = c0 + Vector(offset)
        self.puff(c, r, tris, tone)
        self.branch_to(c + Vector((0, -r * 0.2, 0)), arch=0.05, r_end=0.08, sides=5, per=2)
        return c

    def parts(self):
        bark = Geo().add(self.trunk).add(self.branches)
        out = {"Bark": bark, "Blossom": Geo(), "BlossomPale": Geo()}
        for tone, g, _ in self.clouds:
            out[tone].add(g)
        return {k: v for k, v in out.items() if v.f}

    def report(self):
        """Canopy facts and the structural checks: every cloud carried by a branch (it intersects the bark, or the other
        cloud of its own mass that does), nothing but the trunk below the canopy floor."""
        bark = Geo().add(self.trunk).add(self.branches)
        bvh = bark.bvh()
        carried, unsupported = set(), []
        bv = [g.bvh() for _, g, _ in self.clouds]
        for i, (tone, g, mid) in enumerate(self.clouds):
            if bv[i].overlap(bvh):
                carried.add(i)
        for i, (tone, g, mid) in enumerate(self.clouds):
            if i in carried:
                continue
            if any(j in carried and self.clouds[j][2] == mid and bv[i].overlap(bv[j]) for j in range(len(self.clouds))):
                continue
            unsupported.append(i)
        lows = [min(p.y for p in g.v) for _, g, _ in self.clouds]
        low_branch = min(p.y for p in self.branches.v) if self.branches.v else None
        allc = Geo()
        for _, g, _ in self.clouds:
            allc.add(g)
        lo, hi = allc.bounds()
        return {"canopy_centre": [round((lo.x + hi.x) / 2, 2), round((lo.y + hi.y) / 2, 2), round((lo.z + hi.z) / 2, 2)],
                "canopy_lowest": round(min(lows), 2), "branch_lowest": round(low_branch, 2) if low_branch is not None else None,
                "canopy_size": [round(hi.x - lo.x, 1), round(hi.y - lo.y, 1), round(hi.z - lo.z, 1)],
                "clouds": len(self.clouds), "masses": len(self.masses), "unsupported_masses": sorted(set(unsupported))}


def root_buttresses(tree, n, r_out, r0, phase, rise=1.6, sink=-0.6, seed=0, lengths=None, bias=None, sides=6):
    """Buttress roots: from inside the trunk foot, out low over the ground and down into it (they read as the flare's
    continuation, not as claws: each leaves the trunk low and dives within its own length)."""
    rng = random.Random(seed)
    for k in range(n):
        az = phase + TAU * k / n + rng.uniform(-0.2, 0.2)
        ro = r_out * (lengths[k] if lengths else rng.uniform(0.82, 1.12))
        if bias:
            ro *= 1.0 + bias[0] * max(0.0, math.cos(az - bias[1]))
        bend = rng.uniform(-0.12, 0.12)
        pts = [yaw_vec(az, 0.25, rise), yaw_vec(az + bend * 0.4, ro * 0.45, rise * 0.3), yaw_vec(az + bend * 0.8, ro * 0.8, 0.05),
               yaw_vec(az + bend, ro, sink)]
        curve = resample(pts, 2)
        rf = bark_rf(r0, r0 * 0.4, 0, 0, 0, 0.1, seed + k, taper=0.55)
        tube(tree.trunk, curve, rf, sides, tip=0.25)


# ---------- the six trees ----------
def tree_elder():
    """The grove's matriarch: a thick twisting trunk on a broad buttressed foot, splitting at 8 into three great limbs that
    lean out into a wide umbrella of three tiers (an outer skirt at 21, a middle ring at 26, a crown at 30)."""
    T = Tree("BS_TreeElder", 11)
    rng = T.rng
    rf = bark_rf(2.05, 1.45, ridges=6, ridge_depth=0.1, twist=0.6, wobble=0.06, seed=3, flare=(0.42, 5, 3.0, 0.4))
    trunk = T.add_trunk([(0, -0.8, 0), (0.05, 1.5, 0.05), (0.5, 4.5, -0.3), (0.25, 7.0, 0.3), (-0.1, 9.6, 0.1)], rf, sides=18, per=3)
    T.limbs.append((trunk, lambda t: 1.7))
    root_buttresses(T, 5, 3.3, 0.85, 0.4, rise=1.7, seed=5)
    limbs = []
    for az_deg, reach, rise, swing in ((14, 15.0, 20.2, 1.8), (138, 10.5, 23.5, -1.4), (256, 15.5, 19.6, 1.2)):
        az = math.radians(az_deg)
        perp = Vector((-math.sin(az), 0, math.cos(az)))
        pts = [Vector((0, 7.7, 0)) + yaw_vec(az, 0.45),
               yaw_vec(az, reach * 0.2, 10.8) + perp * swing * 0.3,
               yaw_vec(az, reach * 0.48, rise * 0.72) + perp * swing,
               yaw_vec(az, reach * 0.76, rise * 0.92) - perp * swing * 0.5,
               yaw_vec(az, reach, rise)]
        limbs.append(T.add_limb(pts, 1.25, 0.34, sides=10, per=3, trunk=True, ridges=4, ridge_depth=0.07, twist=0.45, taper=0.75))
    T.add_limb([T.point_on(limbs[1], 0.3), Vector((-1.8, 17.5, 1.2)), Vector((-0.6, 23.5, 0.2)), Vector((0.6, 28.0, -0.4))],
               0.78, 0.3, sides=8, per=2)
    skirt = [(10, 15.5, 20.8, 6.4), (68, 15.0, 22.0, 5.8), (122, 16.0, 20.6, 6.2), (185, 14.0, 22.6, 5.6), (240, 16.5, 20.4, 6.6),
             (298, 15.0, 21.6, 6.0)]
    for az_deg, rr, y, rx in skirt:
        T.mass(yaw_vec(math.radians(az_deg), rr, y), rx, rng.uniform(2.4, 2.8), rx * rng.uniform(0.85, 1.0), tris=(380, 150), florets=10)
    for az_deg, rr, y, rx in ((40, 8.5, 26.0, 5.6), (132, 9.0, 25.6, 5.2), (214, 8.0, 26.6, 5.8), (312, 9.0, 25.8, 5.4)):
        T.mass(yaw_vec(math.radians(az_deg), rr, y), rx, rng.uniform(2.6, 3.0), rx * rng.uniform(0.85, 1.0), tris=(360, 140), florets=9)
    T.mass(yaw_vec(0.6, 1.5, 30.2), 5.4, 3.1, 5.0, tris=(360, 120), florets=9)
    n_main = len(T.masses)
    for k in range(n_main):
        c, rx, ry = T.masses[k]
        T.branch_to(c + Vector((0, -ry * 0.45, 0)), arch=0.16, side=rng.uniform(-0.3, 0.3), r_end=0.16)
    for m, off, r in ((0, (5.2, -1.6, 1.8), 1.5), (2, (-2.0, -1.8, 5.4), 1.4), (4, (-1.0, -1.2, -6.2), 1.6), (3, (-5.4, 1.0, -0.5), 1.3),
                      (7, (-3.5, 2.6, 2.5), 1.3)):
        T.sprig(m, off, r)
    return T


def tree_weeping():
    """A tall slender trunk with a gentle S and a spiral twist, opening at 18 into five arching limbs that spill their flowers
    in ten cascading veils: from each arch's tip and its middle a strand droops in a continuous arc, dressed in overlapping
    lobed scallops that merge into one soft draped sheet with a scalloped hem and a few gaps. Outer veils pale and long,
    inner veils rose and shorter; the lowest hem at 8.5."""
    T = Tree("BS_TreeWeeping", 23)
    rng = T.rng
    rf = bark_rf(0.95, 0.52, ridges=5, ridge_depth=0.09, twist=0.9, wobble=0.06, seed=7, flare=(0.45, 4, 2.0, 1.1))
    trunk = T.add_trunk([(0, -0.6, 0), (0.25, 4, 0.1), (-0.35, 9, 0.35), (0.25, 14, -0.25), (0.0, 18.6, 0.05)], rf, sides=12, per=2)
    T.limbs.append((trunk, lambda t: 0.8))
    root_buttresses(T, 4, 1.8, 0.5, 1.1, rise=0.9, seed=9, sides=5)
    arches = []
    for k in range(5):
        az = TAU * k / 5 + 0.35 + rng.uniform(-0.18, 0.18)
        reach = rng.uniform(9.5, 11.0)
        peak = rng.uniform(24.6, 25.8)
        pts = [Vector((0, 17.8, 0)) + yaw_vec(az, 0.15), yaw_vec(az, 2.2, 21.5), yaw_vec(az + 0.06, 4.6, peak),
               yaw_vec(az + 0.1, 7.6, peak - 0.7), yaw_vec(az + 0.14, reach, peak - 3.0)]
        arches.append((az, T.add_limb(pts, 0.42, 0.12, sides=5, per=2, taper=0.8)))
    for az_deg, rr, y, rx in ((20, 3.4, 25.0, 3.9), (110, 3.8, 24.6, 3.6), (195, 3.2, 25.2, 4.0), (285, 3.6, 24.7, 3.7)):
        T.mass(yaw_vec(math.radians(az_deg), rr, y), rx, 1.9, rx * 0.9, tris=(190, 40), florets=8)
    T.mass(Vector((0.2, 26.1, -0.2)), 3.4, 1.8, 3.2, tris=(180, 0), florets=7)
    for k in range(len(T.masses)):
        c, rx, ry = T.masses[k]
        T.branch_to(c + Vector((0, -ry * 0.4, 0)), arch=0.08, r_end=0.12, sides=4)
    for arch_i, (az, curve) in enumerate(arches):
        for t, outer in ((1.0, True), (0.6, False)):
            veil(T, T.point_on(curve, t), outer, rng)
    return T


def veil(T, top, outer, rng):
    """One cascading veil hung from `top` (a point on an arching limb): a strand drooping in a continuous arc (out, then
    down), and around it a sheet of overlapping blossom scallops in three columns (a merged metaball sheet, flattened
    across its face), the columns ending at different lengths (a scalloped hem), a few scallops missing low down (gaps)."""
    az = math.atan2(top.z, top.x)
    o = yaw_vec(az)
    tn = Vector((-o.z, 0, o.x))
    tip_y = rng.uniform(8.6, 10.4) if outer else rng.uniform(11.0, 13.6)
    drop = top.y - tip_y
    drift = rng.uniform(1.2, 2.0)
    sway = rng.uniform(-0.6, 0.6)

    def spine(u):
        # u 0..1 down the veil: out and over the arch first, then falling, swaying a little
        return top + o * (drift * math.sin(min(1.0, u * 1.6) * math.pi / 2)) + tn * sway * u * u + Vector((0, -drop * u, 0))
    path = [spine(u) for u in (0.0, 0.08, 0.22, 0.42, 0.62, 0.8, 0.92)]
    T.add_limb([top + Vector((0, 0.15, 0)) - o * 0.2] + path, 0.1, 0.05, sides=3, per=1, wobble=0.0)
    width = 1.15 if outer else 0.95
    ends = [rng.uniform(0.7, 0.86), 1.0, rng.uniform(0.76, 0.93)]
    if rng.random() < 0.5:
        ends = ends[::-1]
    balls = []
    rows = int(drop / 0.8) + 1
    for col, end in zip((-1, 0, 1), ends):
        for r_ in range(rows):
            u = r_ / max(rows - 1, 1)
            if u > end:
                break
            if col and 0.4 < u < end - 0.12 and rng.random() < 0.18:
                continue            # a gap in the veil
            # wide where it leaves the arch, narrowing toward the hem; the columns sit on an arc round the crown
            spread = width * (1.25 - 0.5 * u)
            lobe = 0.32 * (1 if (r_ + col) % 2 else -1)
            c = spine(u)
            R = max(3.0, math.hypot(c.x, c.z))
            ang = (col * spread + lobe) / R
            q = rot_y(Vector((c.x, 0.0, c.z)), -ang)
            depth = 0.28 * (1 if (r_ * 2 + col) % 3 == 0 else -0.5)
            p = Vector((q.x, c.y + rng.uniform(-0.12, 0.12), q.z)) + yaw_vec(math.atan2(q.z, q.x), depth)
            balls.append((p, lerp(0.92, 0.6, u) * rng.uniform(0.85, 1.12)))
    g = cloud(balls, 430 if outer else 360, res=0.21)

    # flatten the sheet a little across its face (toward the curved surface through the spine), keeping width and drape
    def flat(p):
        u = max(0.0, min(1.0, (top.y - p.y) / drop))
        c = spine(u)
        rad = Vector((p.x, 0, p.z)).normalized()
        d = math.hypot(p.x, p.z) - math.hypot(c.x, c.z)
        return p - rad * d * 0.35
    g.transform(flat)
    T.clouds.append(("BlossomPale" if outer else "Blossom", g, len(T.masses)))
    T.masses.append((top, width, drop))


def tree_leaning():
    """Leans 25 degrees toward its front, out over the pond: tension roots behind, the trunk bending back up at the top, a
    crown thrown forward (its centre ten studs out) that cascades toward the water, one counter-branch back for balance."""
    T = Tree("BS_TreeLeaning", 37)
    T.axis = (0.0, 10.5)
    rng = T.rng
    rf = bark_rf(1.2, 0.62, ridges=5, ridge_depth=0.1, twist=0.5, wobble=0.08, seed=13, flare=(0.55, 4, 2.4, -math.pi / 2))
    trunk = T.add_trunk([(0, -0.7, 0), (0.0, 1.4, 0.25), (0.15, 5.0, 1.9), (0.35, 9.0, 4.0), (0.1, 12.6, 6.0), (-0.1, 15.6, 7.1)],
                        rf, sides=13, per=3)
    T.limbs.append((trunk, lambda t: 1.0 - 0.4 * t))
    root_buttresses(T, 4, 2.4, 0.7, -math.pi / 2, rise=1.1, seed=17, bias=(0.5, -math.pi / 2))
    T.add_limb([trunk[-3], Vector((0.2, 17.5, 8.8)), Vector((0.0, 18.5, 11.5))], 0.55, 0.22, sides=7, per=3)
    T.add_limb([T.point_on(trunk, 0.85), Vector((0.6, 15.0, 11.0)), Vector((0.8, 14.0, 15.0)), Vector((0.9, 12.4, 18.2))],
               0.42, 0.14, sides=6, per=3)
    T.add_limb([T.point_on(trunk, 0.62), Vector((-0.5, 12.0, 2.6)), Vector((-1.0, 14.0, 0.6)), Vector((-1.3, 15.0, -0.8))],
               0.36, 0.13, sides=6, per=3)
    masses = [((0.0, 18.6, 10.6), 5.0, 2.4, 4.6, "BlossomPale"), ((-4.4, 17.0, 13.0), 3.9, 2.0, 3.6, "BlossomPale"),
              ((4.6, 16.6, 12.4), 4.0, 2.1, 3.7, "BlossomPale"), ((0.4, 15.0, 16.6), 3.8, 1.9, 3.5, "BlossomPale"),
              ((-2.0, 20.0, 6.6), 3.6, 1.9, 3.4, "BlossomPale"), ((3.0, 19.4, 7.2), 3.3, 1.8, 3.2, "BlossomPale"),
              ((0.9, 12.2, 19.4), 2.7, 1.5, 2.5, "BlossomPale"), ((0.2, 15.6, 10.4), 3.4, 1.7, 3.2, "Blossom"),
              ((-1.3, 15.6, -0.9), 3.0, 1.6, 2.8, "BlossomPale")]
    for c, rx, ry, rz, tone in masses:
        T.mass(c, rx, ry, rz, tris=(290, 90) if tone == "BlossomPale" else (200, 0), florets=9, lean=(0.0, 0.6), tone_top=tone)
    for k in range(len(T.masses)):
        c, rx, ry = T.masses[k]
        T.branch_to(c + Vector((0, -ry * 0.45, 0)), arch=0.12, side=rng.uniform(-0.3, 0.3), r_end=0.13)
    for m, off, r in ((3, (2.8, -1.8, 2.0), 1.2), (1, (-3.6, -1.0, 1.0), 1.1), (2, (3.5, 0.6, -1.5), 1.0)):
        T.sprig(m, off, r)
    return T


def tree_twin():
    """Two trunks from one root flare, twisting once round each other and parting: a tall oval crown, wider across the pair
    (about 28) than deep (18), a pale outer shell of overlapping masses round a rose core that shows in the gaps and beneath."""
    T = Tree("BS_TreeTwin", 51)
    T.axis = (-0.5, 0.0)
    rng = T.rng
    rfa = bark_rf(1.1, 0.48, ridges=5, ridge_depth=0.09, twist=0.7, wobble=0.07, seed=21, flare=(0.55, 3, 2.2, math.pi))
    rfb = bark_rf(1.0, 0.44, ridges=5, ridge_depth=0.09, twist=-0.7, wobble=0.07, seed=22, flare=(0.55, 3, 2.2, 0.0))
    a = T.add_trunk([(-0.55, -0.7, 0.15), (-0.6, 3.0, 0.55), (-2.2, 8.8, 0.3), (-4.1, 14.6, -0.3), (-5.0, 20.6, -0.5)], rfa, sides=11, per=3)
    b = T.add_trunk([(0.55, -0.7, -0.15), (0.65, 3.4, -0.5), (2.0, 8.4, -0.4), (3.3, 13.8, 0.4), (3.9, 18.4, 0.9)], rfb, sides=11, per=3)
    T.limbs += [(a, lambda t: 0.9 - 0.45 * t), (b, lambda t: 0.85 - 0.42 * t)]
    root_buttresses(T, 4, 2.3, 0.62, 0.3, rise=1.1, seed=27)
    T.add_limb([T.point_on(a, 0.8), Vector((-3.0, 21.5, 1.0)), Vector((-2.0, 25.5, 0.5))], 0.4, 0.17, sides=6, per=3)
    T.add_limb([T.point_on(b, 0.82), Vector((3.0, 21.0, -0.8)), Vector((2.6, 24.5, -0.6))], 0.38, 0.16, sides=6, per=3)
    # rose core (inside the shell, lower)
    for x, y, z, rx in ((-5.0, 15.5, 0.5, 4.6), (4.5, 15.0, -0.5, 4.4), (-0.5, 20.5, 0.0, 4.8)):
        T.mass(Vector((x, y, z)), rx, 2.6, rx * 0.85, tris=(160, 0), florets=7, tone_top="Blossom")
    # the pale shell: overlapping, irregular sizes, rising in an oval
    shell = [(-10.5, 13.8, 1.0, 3.8, 2.2), (9.8, 13.0, -1.2, 3.6, 2.1), (-4.0, 12.6, 4.6, 3.4, 1.9), (5.2, 12.2, -4.2, 3.0, 1.8),
             (-11.0, 18.6, -1.6, 4.0, 2.3), (10.8, 18.0, 1.6, 4.2, 2.4), (-4.2, 18.6, -5.2, 4.2, 2.3), (3.8, 18.8, 5.0, 4.4, 2.4),
             (-7.2, 23.4, 2.6, 4.2, 2.4), (7.6, 22.6, -2.0, 4.0, 2.3), (-1.2, 24.2, -3.6, 3.9, 2.3), (2.6, 24.4, 3.8, 3.6, 2.2),
             (-2.6, 27.4, 0.6, 3.4, 2.1), (3.2, 26.8, -0.8, 3.0, 2.0)]
    for x, y, z, rx, ry in shell:
        T.mass(Vector((x, y, z)), rx, ry, rx * rng.uniform(0.85, 1.0), tris=(200, 40), florets=rng.choice((7, 8, 9)))
    for k in range(len(T.masses)):
        c, rx, ry = T.masses[k]
        T.branch_to(c + Vector((0, -ry * 0.4, 0)), arch=0.2, side=rng.uniform(-0.25, 0.25), r_end=0.12, sides=4)
    return T


def tree_young():
    """A slim young tree: a smooth, gently curved stem and five slender branches, each holding its own small airy clump with
    sky between them."""
    T = Tree("BS_TreeYoung", 67)
    rf = bark_rf(0.44, 0.2, ridges=0, wobble=0.05, seed=31, flare=(0.35, 3, 1.1, 0.5))
    trunk = T.add_trunk([(0, -0.5, 0), (0.12, 3.0, 0.06), (-0.22, 7.0, 0.22), (0.16, 11.0, -0.12), (0.0, 13.6, 0.0)], rf, sides=9, per=3)
    T.limbs.append((trunk, lambda t: 0.4 - 0.18 * t))
    clumps = [((-5.0, 10.2, 1.6), 2.2, 1.35, 7.9), ((4.9, 10.9, -1.4), 2.0, 1.25, 8.6), ((-2.2, 13.4, -3.6), 2.1, 1.3, 10.2),
              ((3.1, 13.6, 3.2), 1.9, 1.2, 11.0), ((0.0, 14.8, -0.2), 1.8, 1.15, 13.4)]
    for c, rx, ry, y0 in clumps:
        c = Vector(c)
        T.mass(c, rx, ry, rx * 0.9, tris=(300, 90), florets=7)
        t = (y0 + 0.5) / 14.1
        T.branch_to(c + Vector((0, -0.5, 0)), start=T.point_on(trunk, t), limb=0, t=t, arch=0.22, r_end=0.07, sides=5,
                    r_start=0.16 if y0 < 13 else 0.13)
    for m, off, r in ((0, (-2.4, -0.6, -1.8), 0.85), (1, (2.2, 0.8, 1.6), 0.75), (3, (2.0, -0.6, 1.8), 0.75)):
        T.sprig(m, off, r, tris=50)
    return T


def tree_gnarled():
    """Short, very gnarled, windswept (the wind from -X): a squat trunk wrung into a corkscrew with burls, three twisted limbs
    reaching out level, and the crown held in three flat sculpted plateaus streaming downwind, as a cultivator trains it."""
    T = Tree("BS_TreeGnarled", 89)
    rng = T.rng
    rf = bark_rf(1.55, 0.95, ridges=7, ridge_depth=0.15, twist=1.3, wobble=0.12, seed=41, flare=(0.6, 4, 2.4, 2.2),
                 knots=((0.42, 0.18, 0.08), (0.72, 0.14, 0.07)))
    trunk = T.add_trunk([(0, -0.7, 0), (0.3, 1.5, 0.2), (-0.9, 3.5, 0.8), (0.2, 5.2, 1.1), (1.3, 6.6, 0.3), (1.0, 8.2, -0.4)], rf,
                        sides=15, per=3)
    T.limbs.append((trunk, lambda t: 1.3 - 0.4 * t))
    root_buttresses(T, 5, 2.8, 0.8, 2.2, rise=1.2, seed=43)
    T.add_limb([Vector((1.0, 7.4, -0.3)), Vector((3.2, 8.8, 0.9)), Vector((5.4, 9.1, 2.0)), Vector((8.6, 9.0, 0.4)),
                Vector((12.6, 9.6, 1.4))], 0.78, 0.22, sides=8, per=3, trunk=True, ridges=3, ridge_depth=0.1, twist=1.0,
               knots=((0.35, 0.15, 0.08),))
    T.add_limb([Vector((0.8, 7.6, -0.4)), Vector((-1.6, 9.6, -0.2)), Vector((-3.8, 11.0, -2.0)), Vector((-6.8, 12.0, -0.8)),
                Vector((-9.4, 12.5, -2.0))], 0.7, 0.2, sides=8, per=3, trunk=True, ridges=3, ridge_depth=0.1, twist=-0.9)
    T.add_limb([Vector((1.0, 7.8, -0.4)), Vector((1.8, 10.8, -0.9)), Vector((0.4, 13.2, 0.5)), Vector((2.2, 15.4, -0.4))],
               0.62, 0.2, sides=7, per=3, trunk=True, ridges=3, ridge_depth=0.1, twist=0.8)
    # three plateaus: low and long downwind, mid upwind, a small level top
    T.pad((8.6, 10.75, 1.0), 7.2, 4.6, 1.15, tris=(720, 220), yaw=-0.08)
    T.pad((-6.6, 13.7, -1.4), 5.3, 4.2, 1.1, tris=(560, 170), yaw=0.15)
    T.pad((1.8, 16.5, -0.3), 4.3, 3.5, 1.0, tris=(440, 130), yaw=-0.2)
    for k in range(len(T.masses)):
        c, rx, ry = T.masses[k]
        for off in ((-rx * 0.33, 0.15), (rx * 0.36, 0.8)):
            T.branch_to(c + Vector((off[0], -ry * 0.55, off[1])), arch=0.04, side=rng.uniform(-0.4, 0.4), r_end=0.12, sides=6)
    for m, off, r in ((0, (8.0, -0.2, 0.8), 1.1), (0, (3.0, -0.6, 4.4), 0.9), (1, (-5.6, 0.0, -0.4), 1.0)):
        T.sprig(m, off, r, tris=55)
    return T


TREES = {"BS_TreeElder": tree_elder, "BS_TreeWeeping": tree_weeping, "BS_TreeLeaning": tree_leaning, "BS_TreeTwin": tree_twin,
         "BS_TreeYoung": tree_young, "BS_TreeGnarled": tree_gnarled}


# ======================================================================================================================
# Shared primitives for stone, water life and koi
# ======================================================================================================================
def lathe(g, profile, seg, rmod=None, centre=(0.0, 0.0, 0.0), phase=0.0):
    """A closed surface of revolution about the vertical axis. profile [(r, y)] walks from the top pole outward and down to
    the bottom pole (r = 0 at a pole). rmod(theta, y, r) -> the radius actually used (irregular outlines, ovals)."""
    cx, cy, cz = centre
    rings = []
    for r, y in profile:
        if r <= 1e-9:
            rings.append(g.vert((cx, cy + y, cz)))
            continue
        ring = []
        for k in range(seg):
            th = TAU * k / seg + phase
            rr = rmod(th, y, r) if rmod else r
            ring.append(g.vert((cx + math.cos(th) * rr, cy + y, cz + math.sin(th) * rr)))
        rings.append(ring)
    _connect_rings(g, rings, seg, loop=False)
    return rings


def lathe_loop(g, loop, seg, rmod=None, centre=(0.0, 0.0, 0.0), phase=0.0):
    """A closed ring solid (a torus-like band): `loop` is a closed profile [(r, y)] revolved about the vertical axis."""
    cx, cy, cz = centre
    rings = []
    for r, y in loop:
        ring = []
        for k in range(seg):
            th = TAU * k / seg + phase
            yy = y(th) if callable(y) else y
            rr = rmod(th, yy, r) if rmod else r
            ring.append(g.vert((cx + math.cos(th) * rr, cy + yy, cz + math.sin(th) * rr)))
        rings.append(ring)
    _connect_rings(g, rings, seg, loop=True)
    return rings


def _connect_rings(g, rings, seg, loop):
    n = len(rings)
    for i in range(n if loop else n - 1):
        a, b = rings[i], rings[(i + 1) % n]
        if isinstance(a, int) and isinstance(b, int):
            continue
        if isinstance(a, int):
            for k in range(seg):
                g.face(a, b[(k + 1) % seg], b[k])
        elif isinstance(b, int):
            for k in range(seg):
                g.face(a[k], a[(k + 1) % seg], b)
        else:
            for k in range(seg):
                j = (k + 1) % seg
                g.face(a[k], a[j], b[j], b[k])


def superellipsoid_r(d, a, b, c, n):
    """Distance along unit direction d to the surface |x/a|^n + |y/b|^n + |z/c|^n = 1."""
    s = abs(d.x / a) ** n + abs(d.y / b) ** n + abs(d.z / c) ** n
    return s ** (-1.0 / n)


def blob(g, centre, rfn, n_theta, n_rings, floor=None):
    """A closed deformed sphere: radius rfn(direction) from `centre` (Roblox studs), poles on the vertical axis. floor: no
    vertex below this height (a flat bedding face). Returns (rings, point fn)."""
    c = Vector(centre)

    def point(el, th):
        d = Vector((math.cos(el) * math.cos(th), math.sin(el), math.cos(el) * math.sin(th)))
        p = c + d * rfn(d)
        if floor is not None and p.y < floor:
            p.y = floor
        return p
    rings = [g.vert(point(math.pi / 2, 0.0))]
    for i in range(1, n_rings):
        el = math.pi / 2 - math.pi * i / n_rings
        rings.append([g.vert(point(el, TAU * k / n_theta)) for k in range(n_theta)])
    rings.append(g.vert(point(-math.pi / 2, 0.0)))
    _connect_rings(g, rings, n_theta, loop=False)
    return rings, point


def moss_cap(g, centre, rfn, boundary, n_theta, n_rings=3, out=0.05, inn=0.14, floor=None):
    """A closed moss shell over a blob's top: every direction above boundary(theta) (an elevation), its outer face `out`
    above the stone, its inner face `inn` inside it (the rim crosses the stone surface, so it is seated, never floating)."""
    c = Vector(centre)

    def p(el, th, off):
        d = Vector((math.cos(el) * math.cos(th), math.sin(el), math.cos(el) * math.sin(th)))
        q = c + d * (rfn(d) + off)
        if floor is not None and q.y < floor:
            q.y = floor
        return q
    rings_o, rings_i = [g.vert(p(math.pi / 2, 0, out))], [g.vert(p(math.pi / 2, 0, -inn))]
    for i in range(1, n_rings + 1):
        ro, ri = [], []
        for k in range(n_theta):
            th = TAU * k / n_theta      # (on the stone's own meridians: the skin's chords run parallel to the stone's)
            el = math.pi / 2 - (math.pi / 2 - boundary(th)) * i / n_rings
            ro.append(g.vert(p(el, th, out)))
            ri.append(g.vert(p(el, th, -inn)))
        rings_o.append(ro)
        rings_i.append(ri)
    _connect_rings(g, rings_o, n_theta, loop=False)
    _connect_rings(g, rings_i[::-1], n_theta, loop=False)
    a, b = rings_o[-1], rings_i[-1]
    for k in range(n_theta):
        j = (k + 1) % n_theta
        g.face(a[k], b[k], b[j], a[j])


def lens(g, rim, thick, normal):
    """A thin closed leaf/petal/fin: a rim loop (Vectors) with a top and a bottom centre (thick apart along `normal`); the rim
    is knife-thin, the middle has body. Returns nothing."""
    cen = sum(rim, Vector()) / len(rim)
    n = Vector(normal).normalized()
    t = g.vert(cen + n * thick * 0.5)
    b = g.vert(cen - n * thick * 0.5)
    ids = [g.vert(p) for p in rim]
    m = len(ids)
    for k in range(m):
        g.face(t, ids[k], ids[(k + 1) % m])
        g.face(b, ids[(k + 1) % m], ids[k])


def rot_y(p, a):
    c, s = math.cos(a), math.sin(a)
    return Vector((p.x * c + p.z * s, p.y, -p.x * s + p.z * c))


def rot_x(p, a):
    c, s = math.cos(a), math.sin(a)
    return Vector((p.x, p.y * c - p.z * s, p.y * s + p.z * c))


def rot_z(p, a):
    c, s = math.cos(a), math.sin(a)
    return Vector((p.x * c - p.y * s, p.x * s + p.y * c, p.z))


def worn(seed, amp, freq=0.6):
    """A low-frequency wear function of (theta, y) for lathed stones: a radius factor."""
    def f(th, y, r):
        return r * (1.0 + amp * W.fbm(math.cos(th) * freq * 3 + seed, math.sin(th) * freq * 3 + y * 0.4, seed, octaves=3))
    return f


# ======================================================================================================================
# Stone: the bridge, stepping stones, edge rocks, kerb, seat (one language: warm ivory water-worn stone, moss at the water)
# ======================================================================================================================
DECK_HALF = 3.5
SPAN = 15.0
RISE = 3.2


def deck_y(z):
    """The deck's top: 0 at the ends (level, so no step), RISE at the middle, a smooth cosine ramp (steepest 18 degrees)."""
    z = max(-SPAN, min(SPAN, z))
    return RISE * (1.0 + math.cos(math.pi * z / SPAN)) / 2.0


def soffit_y(z):
    """The arch's underside: a segmental arc springing at -1.6 from z = +-9, crown 1.85 (the deck 1.35 deep there); level on
    the footings beyond."""
    half, spring, crown = 9.0, -1.6, 1.85
    if abs(z) >= half:
        return spring
    sag = crown - spring
    R = (half * half + sag * sag) / (2 * sag)
    return crown - R + math.sqrt(R * R - z * z)


def sweep(g, stations, section, closed_ends=True):
    """Sweeps a closed cross-section along Z: section(z) -> [(x, y)] (the same count every station), stations ascending.
    Closed with end caps (n-gons, triangulated later)."""
    rings = []
    for z in stations:
        rings.append([g.vert((x, y, z)) for x, y in section(z)])
    m = len(rings[0])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(m):
            j = (k + 1) % m
            g.face(a[k], a[j], b[j], b[k])
    if closed_ends:
        g.face(*rings[0][::-1])
        g.face(*rings[-1])
    return rings


def bridge():
    """An elegant low stone bridge: one segmental arch you can see through, a deck rising 3.2 over a 30-stud span with level
    ends, a fine carved band along both fascias and a moulded archivolt over the arch, rounded parapet curbs 1.2 tall that
    sweep up to 1.55 into four rounded end posts, each post carrying
    a small many-petalled rosette roundel toward the approach; water-worn footings to -4 with moss at the waterline."""
    stone, moss = Geo(), Geo()
    zs = [-SPAN + 30.0 * i / 22 for i in range(23)]
    zs = sorted(set([round(z, 4) for z in zs] + [-9.0, 9.0]))

    def body(z):
        t, b = deck_y(z), soffit_y(z)
        h = DECK_HALF
        # the fascia from the deck edge down: a crisp arris, a carved band (bead, fillet, bead), then the plain face
        side = [(h, t), (h, t - 0.2), (h + 0.16, t - 0.27), (h + 0.16, t - 0.4), (h + 0.07, t - 0.46), (h + 0.16, t - 0.52),
                (h + 0.16, t - 0.66), (h, t - 0.74), (h, b + 0.2), (h - 0.2, b)]
        # one way round: the right side top to bottom, then the left side bottom to top
        return side + [(-x, y) for x, y in side[::-1]]
    sweep(stone, zs, body)
    # the archivolt: a slim moulded band following the arch on both fascias (it stops where the arch springs)
    az_ = [-8.6 + 17.2 * i / 14 for i in range(15)]
    for sign in (1, -1):
        def arch_band(z, sign=sign):
            b = soffit_y(z)
            h = DECK_HALF - 0.06
            pts = [(h, b + 0.02), (h + 0.12, b + 0.06), (h + 0.14, b + 0.32), (h + 0.08, b + 0.46), (h, b + 0.5)]
            pts = [(x, y) for x, y in pts]
            return pts + [(h - 0.25, b + 0.5), (h - 0.25, b + 0.02)] if sign > 0 else \
                [(-x, y) for x, y in (pts + [(h - 0.25, b + 0.5), (h - 0.25, b + 0.02)])][::-1]
        sweep(stone, az_, arch_band)
    # parapet curbs (rounded tops), sunk 0.05 into the deck
    def curb(sign):
        def sec(z):
            t = deck_y(z) - 0.05
            # 1.2 tall along the span, sweeping up to 1.55 as it meets the end posts
            h = 1.2 + 0.35 * smooth01((abs(z) - 10.6) / 3.3)
            x0, x1 = 3.0 * sign, 3.48 * sign
            pts = [(x0, t), (x0, t + h - 0.22), (x0 + 0.06 * sign, t + h - 0.07), (x0 + 0.24 * sign, t + h), (x1 - 0.06 * sign, t + h - 0.07),
                   (x1, t + h - 0.22), (x1, t)]
            return pts if sign > 0 else pts[::-1]
        return sec
    cz = [-13.9 + 27.8 * i / 16 for i in range(17)]
    for sign in (1, -1):
        sweep(stone, cz, curb(sign))
    # end posts: rounded square shafts with a moulded cap and a low dome
    post_z = 14.25
    for sign_x in (1, -1):
        for sign_z in (1, -1):
            x, z = 3.24 * sign_x, post_z * sign_z
            base = deck_y(z) - 0.1
            prof = [(0.0, 2.32), (0.3, 2.22), (0.5, 1.98), (0.56, 1.84), (0.56, 1.7), (0.46, 1.62), (0.45, 0.16), (0.5, 0.04),
                    (0.0, -0.05)]

            def sq(th, y, r):
                # a rounded square (superellipse, n = 4)
                c, s_ = abs(math.cos(th)), abs(math.sin(th))
                return r / (c ** 4 + s_ ** 4) ** 0.25
            lathe(stone, prof, 12, sq, centre=(x, base, z), phase=math.pi / 12)
            # the rosette roundel on the post's outer face (toward the approach)
            ros = Geo()
            n_l = 12

            def lobes(th, y, r, n_l=n_l):
                return r * (0.8 + 0.2 * abs(math.cos(n_l * th / 2)) ** 0.7)
            lathe(ros, [(0.0, 0.1), (0.11, 0.075), (0.29, 0.035), (0.27, -0.08), (0.0, -0.08)], 24, lobes)
            face_z = z + sign_z * 0.44
            ros.transform(lambda p, sz=sign_z: rot_x(p, sz * math.pi / 2))
            ros.transform(lambda p, x=x, y=base + 0.95, z=face_z: Vector((p.x + x, p.y + y, p.z + z)))
            stone.add(ros)
    # footings: water-worn rounded masses under each end, down to -4, with a moss band at the waterline
    for sign_z in (1, -1):
        zc = 11.9 * sign_z
        a_, c_ = 4.15, 3.7

        def fp(th, y, r, a_=a_, c_=c_, seed=int(5 + sign_z)):
            c, s_ = math.cos(th), math.sin(th)
            base = 1.0 / ((abs(c) / a_) ** 3 + (abs(s_) / c_) ** 3) ** (1 / 3)
            return r * base * (1.0 + 0.04 * W.fbm(c * 2 + seed, s_ * 2 + y * 0.5, seed, octaves=2))
        prof = [(0.0, -1.3), (0.8, -1.32), (0.96, -1.5), (1.0, -2.1), (0.99, -3.0), (0.93, -3.75), (0.8, -4.0), (0.0, -4.0)]
        lathe(stone, prof, 20, fp, centre=(0, 0, zc))
        wl = lambda th, s_=sign_z: -2.15 + 0.32 * W.fbm(th * 2.2 + s_, 0.3, 77, octaves=3)
        loop = [(1.02, -2.62), (1.03, lambda th: wl(th) + 0.02), (0.955, lambda th: wl(th) + 0.07), (0.95, -2.68)]
        lathe_loop(moss, loop, 20, fp, centre=(0, 0, zc))
    return {"Stone": stone, "Moss": moss}, {}


def _stepping(rx, rz, thick, seed, seg=20, moss_y=(-1.05, -0.62)):
    """A flat-topped water-worn stepping stone: a level walking top at y = 0, a softly rounded worn edge, the body tapering
    below; a moss band round its sides at the waterline."""
    stone, moss = Geo(), Geo()

    def outline(th, y, r):
        c, s_ = math.cos(th), math.sin(th)
        k = 1.0 / math.sqrt((c / rx) ** 2 + (s_ / rz) ** 2)
        return r * k * (1.0 + 0.07 * W.fbm(c * 1.7 + seed, s_ * 1.7, seed, octaves=3))
    t = thick
    prof = [(0.0, 0.0), (0.72, 0.0), (0.88, -0.04), (0.97, -0.16), (1.0, -0.36), (0.97, -0.62 * t), (0.86, -0.92 * t),
            (0.7, -t), (0.0, -t)]
    lathe(stone, prof, seg, outline)
    lo, hi = moss_y
    wl = lambda th: hi + 0.12 * W.fbm(th * 1.3 + seed, 0.4, seed + 3, octaves=2)
    loop = [(0.985, lo), (1.03, lo + 0.04), (1.035, lambda th: wl(th)), (0.95, lambda th: wl(th) + 0.04), (0.9, lo + 0.05)]
    lathe_loop(moss, loop, seg, outline)
    return {"Stone": stone, "Moss": moss}, {}


def stepping_a():
    return _stepping(5.0, 4.7, 1.6, 101)


def stepping_b():
    return _stepping(6.0, 4.0, 1.6, 113)


def stepping_c():
    return _stepping(3.0, 2.85, 1.4, 127, seg=18, moss_y=(-0.95, -0.58))


def footprint(rx, rz, seed, n=8, cuts=2, yaw=0.0, centre=(0.0, 0.0)):
    """An irregular faceted footprint: n jittered corners, then `cuts` straight cuts (crisp breaks)."""
    rng = random.Random(seed)
    pts = []
    for k in range(n):
        a = TAU * (k + rng.uniform(-0.3, 0.3)) / n
        r = rng.uniform(0.8, 1.12)
        pts.append(Vector((math.cos(a) * rx * r, 0.0, math.sin(a) * rz * r)))
    for _ in range(cuts):
        phi = rng.uniform(0, TAU)
        dvec = Vector((math.cos(phi), 0, math.sin(phi)))
        lim = rng.uniform(0.6, 0.78) * (rx * abs(dvec.x) + rz * abs(dvec.z))
        pts = [p - dvec * (p.dot(dvec) - lim) if p.dot(dvec) > lim else p for p in pts]
    return [rot_y(p, yaw) + Vector((centre[0], 0, centre[1])) for p in pts]


def split_footprint(pts, origin, direction, gap):
    """Splits a footprint along a line (a crack): the two halves, each pulled back gap/2 from the line."""
    o, d = Vector((origin[0], 0, origin[1])), Vector((direction[0], 0, direction[1])).normalized()
    nrm = Vector((-d.z, 0, d.x))
    halves = []
    for side in (1, -1):
        out = []
        m = len(pts)
        for k in range(m):
            a, b = pts[k], pts[(k + 1) % m]
            da, db = side * (a - o).dot(nrm) - gap / 2, side * (b - o).dot(nrm) - gap / 2
            if da >= 0:
                out.append(a)
            if (da >= 0) != (db >= 0):
                out.append(a + (b - a) * (da / (da - db)))
        halves.append(out)
    return halves


def slab_tier(g, centre, rx, rz, y0, y1, seed, yaw=0.0, n=8, cuts=2, roll=0.28, batter=0.08, tilt=(0.0, 0.0), pts=None):
    """One stratum of a layered rock: an irregular faceted footprint (n corners, jittered, then cut by `cuts` straight
    planes for crisp breaks), near-vertical faces with a slight batter, the top edge water-worn (rolled over in two steps),
    the top a single gently tilted plane. Closed. Returns (footprint corners at the top, top height at the centre)."""
    rng = random.Random(seed + 7)
    if pts is None:
        pts = footprint(rx, rz, seed, n, cuts, yaw, centre)
    n = len(pts)
    c = sum(pts, Vector()) / n
    cx, cz = c.x, c.z
    rx = max((p - c).length for p in pts)
    rz = rx

    def ytop(p):
        return y1 + tilt[0] * (p.x - cx) + tilt[1] * (p.z - cz)

    def ring(scale, ydef):
        return [g.vert(c + (p - c) * scale + Vector((0, ydef(p), 0))) for p in pts]
    h = y1 - y0
    mid_j = [rng.uniform(-0.05, 0.09) for _ in pts]
    rings = [ring(1.0 + batter, lambda p: y0),
             [g.vert(c + (p - c) * (1.0 + batter * 0.5 + mid_j[i]) + Vector((0, y0 + h * 0.5, 0))) for i, p in enumerate(pts)],
             ring(1.0, lambda p: ytop(p) - roll),
             ring(1.0 - roll * 0.55 / max(rx, rz), lambda p: ytop(p) - roll * 0.28),
             ring(1.0 - roll * 1.0 / max(rx, rz), lambda p: ytop(p))]
    _connect_rings(g, rings, n, loop=False)
    g.face(*rings[0][::-1])
    g.face(*rings[-1])
    return pts, y1


def moss_patch(g, centre, r, y, seed, n=8, up=0.05, down=0.12, stretch=(1.0, 1.0)):
    """A thin irregular moss patch lying on a ledge (its top `up` above the stone, its underside `down` inside it)."""
    rng = random.Random(seed)
    cx, cz = centre
    top, bot = [], []
    for k in range(n):
        a = TAU * k / n + rng.uniform(-0.2, 0.2)
        rr = r * rng.uniform(0.55, 1.1)
        x, z = cx + math.cos(a) * rr * stretch[0], cz + math.sin(a) * rr * stretch[1]
        yy = y(x, z) if callable(y) else y
        top.append(g.vert((x, yy + up, z)))
        bot.append(g.vert((x, yy - down, z)))
    yc = y(cx, cz) if callable(y) else y
    keel = g.vert((cx, yc - down - 0.18, cz))       # (a shallow keel underneath: no face lies parallel to a stone face)
    g.face(*top)
    for k in range(n):
        j = (k + 1) % n
        g.face(top[k], bot[k], bot[j], top[j])
        g.face(keel, bot[j], bot[k])


def _tilted(y1, cx, cz, tilt):
    return lambda x, z: y1 + tilt[0] * (x - cx) + tilt[1] * (z - cz)


def edge_rock_a():
    """A low flat slab shelf: two broad strata, the upper set back so the lower makes a ledge toward the water; moss in the
    ledge's crevice and a small patch on the top."""
    stone, moss = Geo(), Geo()
    slab_tier(stone, (0.0, 0.0), 3.3, 2.5, -0.4, 1.2, 211, yaw=0.2, n=9, tilt=(0.02, -0.03))
    slab_tier(stone, (-0.7, -0.5), 2.4, 1.9, 1.05, 2.5, 212, yaw=-0.35, n=8, tilt=(-0.04, 0.03))
    moss_patch(moss, (1.6, 1.1), 0.75, _tilted(1.2, 0.0, 0.0, (0.02, -0.03)), 213, stretch=(1.4, 0.8))
    moss_patch(moss, (-0.3, 1.25), 0.5, _tilted(1.2, 0.0, 0.0, (0.02, -0.03)), 214)
    moss_patch(moss, (-1.2, -0.8), 0.55, _tilted(2.5, -0.7, -0.5, (-0.04, 0.03)), 215)
    return {"Stone": stone, "Moss": moss}, {"shading": {"Stone": (40.0, True)}}


def edge_rock_b():
    """A split boulder: one boulder on a low bedding stratum, cracked clean through along a long line, the two halves
    sharing one outline, one half settled lower and leaning away; moss runs along the crack's foot and on the ledge."""
    stone, moss = Geo(), Geo()
    slab_tier(stone, (0.0, 0.0), 3.3, 2.6, -0.4, 0.9, 223, yaw=0.1, n=9)
    whole = footprint(2.75, 2.15, 224, n=9, cuts=2, yaw=-0.2, centre=(0.1, -0.1))
    left, right = split_footprint(whole, (0.35, 0.0), (0.35, 1.0), 0.22)
    slab_tier(stone, None, 0, 0, 0.75, 4.0, 225, pts=left, tilt=(0.05, 0.02), batter=0.04)
    slab_tier(stone, None, 0, 0, 0.62, 3.55, 226, pts=right, tilt=(-0.07, 0.03), batter=0.04)
    for k, t in enumerate((-0.7, 0.1, 0.85)):
        x, z = 0.35 + 0.35 * t * 2.0, t * 2.0
        moss_patch(moss, (x, z), 0.32, 0.9, 227 + k, stretch=(0.6, 1.5))
    moss_patch(moss, (-2.6, 1.3), 0.5, 0.9, 231)
    moss_patch(moss, (1.9, 1.7), 0.45, 0.9, 232)
    return {"Stone": stone, "Moss": moss}, {"shading": {"Stone": (40.0, True)}}


def edge_rock_c():
    """A tall stacked stone: three strata of slate-like slabs, each shifted to one side and tilted on the one below (not
    centred: the ledges step down toward the water on one side), the top slab broken at an angle; moss on the ledges."""
    stone, moss = Geo(), Geo()
    slab_tier(stone, (0.0, 0.0), 3.5, 2.7, -0.4, 1.9, 239, yaw=0.0, n=8, cuts=3, tilt=(0.03, -0.02), batter=0.12)
    slab_tier(stone, (-0.9, -0.5), 2.5, 2.0, 1.72, 4.0, 240, yaw=0.7, n=7, cuts=2, tilt=(-0.07, 0.05), batter=0.1)
    slab_tier(stone, (-1.4, -0.7), 2.3, 1.55, 3.8, 6.0, 241, yaw=-0.45, n=7, cuts=2, tilt=(0.09, -0.05), batter=0.06)
    moss_patch(moss, (2.0, 0.6), 0.7, _tilted(1.9, 0.0, 0.0, (0.03, -0.02)), 242, stretch=(1.0, 1.3))
    moss_patch(moss, (1.0, 1.3), 0.45, _tilted(1.9, 0.0, 0.0, (0.03, -0.02)), 243)
    moss_patch(moss, (0.3, 0.4), 0.4, _tilted(4.0, -0.9, -0.5, (-0.07, 0.05)), 244)
    moss_patch(moss, (-1.8, -0.9), 0.4, _tilted(6.0, -1.4, -0.7, (0.09, -0.05)), 245)
    return {"Stone": stone, "Moss": moss}, {"shading": {"Stone": (40.0, True)}}


def kerb():
    """A low worn kerb: a rounded-rectangle section swept 4.5 long, its ends eased, the arrises softened by wear."""
    g = Geo()
    L, w, top, bot = 4.5, 1.4, 0.8, -0.12

    def sec(x):
        e = 1.0 - 0.12 * smooth01((abs(x) - (L / 2 - 0.25)) / 0.25)
        hw = w / 2 * e
        t = bot + (top - bot) * (0.97 + 0.03 * e)
        r = 0.16
        pts = [(hw, bot), (hw, t - r), (hw - r * 0.3, t - r * 0.3), (hw - r, t), (-hw + r, t), (-hw + r * 0.3, t - r * 0.3), (-hw, t - r),
               (-hw, bot)]
        n = W.fbm(x * 0.8, 0.3, 301, octaves=2) * 0.025
        return [(z * (1 + n), y + (n if y > 0.3 else 0.0)) for z, y in pts]
    xs = [-L / 2, -L / 2 + 0.25, -1.1, 0.0, 1.1, L / 2 - 0.25, L / 2]
    sw = Geo()
    sweep(sw, xs, sec)
    # the sweep runs along Z with sections in (x, y): turn it to run along X
    sw.transform(lambda p: Vector((p.z, p.y, -p.x)))
    g.add(sw)
    return {"Stone": g}, {}


def seat_stone():
    """A flat round meditation seat: a gently crowned top at 0.9, a soft rolled edge, a slight waist, bedded below ground."""
    g = Geo()
    prof = [(0.0, 0.92), (1.15, 0.9), (1.5, 0.84), (1.7, 0.66), (1.75, 0.36), (1.68, 0.08), (1.55, -0.15), (0.0, -0.15)]
    lathe(g, prof, 20, worn(331, 0.045))
    return {"Stone": g}, {}


# ======================================================================================================================
# Water life: lily pads, the open lily, reeds, water plantain, the fallen-petal drift
# ======================================================================================================================
def _pad(g, R, centre=(0.0, 0.0, 0.0), yaw=0.0, notch=0.2, n=16, tilt=(0.0, 0.0), seed=0):
    """A round lily pad with its notch running in to the stem point: slightly cupped (the rim lifts), 0.06 thick, closed."""
    cx, cy, cz = centre
    ang = [notch + (TAU - 2 * notch) * i / (n - 1) for i in range(n)]

    def P(r, a, top):
        wav = 1.0 + 0.035 * math.sin(a * 5 + seed) if r > 0 else 1.0
        rr = r * wav
        y = 0.03 + 0.06 * (r / R) ** 2 + 0.015 * math.sin(a * 3 + seed) * (r / R)
        if not top:
            y -= 0.06
        p = Vector((math.cos(a + yaw) * rr, y, math.sin(a + yaw) * rr))
        p = rot_x(p, tilt[0])
        p = rot_z(p, tilt[1])
        return p + Vector((cx, cy, cz))
    ct, cb = g.vert(P(0, 0, True)), g.vert(P(0, 0, False))
    t1 = [g.vert(P(R * 0.5, a, True)) for a in ang]
    t2 = [g.vert(P(R, a, True)) for a in ang]
    b1 = [g.vert(P(R * 0.5, a, False)) for a in ang]
    b2 = [g.vert(P(R, a, False)) for a in ang]
    for i in range(n - 1):
        g.face(ct, t1[i + 1], t1[i])
        g.face(t1[i], t1[i + 1], t2[i + 1], t2[i])
        g.face(cb, b1[i], b1[i + 1])
        g.face(b1[i + 1], b1[i], b2[i], b2[i + 1])
        g.face(t2[i], t2[i + 1], b2[i + 1], b2[i])
    for (tt1, tt2, bb1, bb2) in ((t1[0], t2[0], b1[0], b2[0]), (t1[-1], t2[-1], b1[-1], b2[-1])):
        g.face(ct, tt1, bb1, cb)
        g.face(tt1, tt2, bb2, bb1)


def lily_pad_a():
    g = Geo()
    _pad(g, 1.5, notch=0.2, n=16, seed=1)
    return {"Lily": g}, {}


def lily_pad_b():
    g = Geo()
    _pad(g, 1.1, yaw=1.9, notch=0.22, n=14, seed=4)
    return {"Lily": g}, {}


def lily_pad_cluster():
    """Three pads of mixed size: the smaller ones ride up over the big one's rim (tilted a few degrees, never coplanar)."""
    g = Geo()
    _pad(g, 1.35, (0.0, 0.0, 0.0), yaw=0.4, n=16, seed=2)
    _pad(g, 0.95, (1.95, 0.025, 0.75), yaw=2.6, n=14, tilt=(0.03, 0.07), seed=5)
    _pad(g, 0.65, (-0.6, 0.02, 1.7), yaw=4.4, n=12, tilt=(-0.08, -0.02), seed=7)
    return {"Lily": g}, {}


def _petal_rim(L, W_, tip_round=0.35):
    """A blunt, broad-tipped petal outline in its own plane (x across, z along; base at the origin): 6 rim points."""
    return [Vector((0.0, 0.0, 0.0)), Vector((W_ * 0.46, 0.0, L * 0.42)), Vector((W_ * 0.34, 0.0, L * 0.9)),
            Vector((0.0, 0.0, L)), Vector((-W_ * 0.34, 0.0, L * 0.9)), Vector((-W_ * 0.46, 0.0, L * 0.42))][::-1]


def lily_flower():
    """An open water lily, about 1.3 across: three rings of broad blunt petals opening from a low centre, the outer two
    LilyFlower, the inner ring rose-tinted; a small domed rose centre."""
    white, rose = Geo(), Geo()
    lathe(rose, [(0.0, 0.2), (0.12, 0.16), (0.15, 0.05), (0.0, 0.02)], 8)
    rings = [(10, 0.63, 0.31, 0.22, 0.0, white), (8, 0.5, 0.28, 0.62, 0.5, white), (7, 0.36, 0.21, 1.0, 0.25, rose)]
    for n, L, Wd, rise, ph, g in rings:
        for k in range(n):
            a = TAU * (k + ph) / n
            pts = []
            for q in _petal_rim(L, Wd):
                # cup each petal (its sides lift), then tilt it up by `rise` (radians) and turn it to its bearing
                cup = 0.18 * (q.x / (Wd * 0.5)) ** 2 * Wd
                v = Vector((q.x, cup + 0.06 * (q.z / L) ** 2, q.z))
                v = rot_x(v, -rise)
                v = Vector((v.x, v.y + 0.05, v.z + 0.04))
                pts.append(rot_y(v, -a + math.pi / 2))
            nrm = rot_y(rot_x(Vector((0, 1, 0)), -rise), -a + math.pi / 2)
            lens(g, pts, 0.035, nrm)
    return {"LilyFlower": white, "Blossom": rose}, {}


def reeds():
    """A clump of 15 slender reed blades, 3 to 5 tall, rising from one root point under the water: most arching gently out,
    three bent over near the top. No seed heads."""
    g = Geo()
    rng = random.Random(401)
    n = 15
    for i in range(n):
        az = TAU * i / n + rng.uniform(-0.3, 0.3)
        H = rng.uniform(3.0, 5.0)
        lean = rng.uniform(0.05, 0.3)
        out = yaw_vec(az)
        kink = i % 5 == 2
        base = Vector((rng.uniform(-0.12, 0.12), -0.42 - 0.025 * i, rng.uniform(-0.12, 0.12)))
        pts = [base, base + Vector((0, H * 0.45, 0)) + out * H * lean * 0.25, base + Vector((0, H * 0.8, 0)) + out * H * lean * 0.7]
        if kink:
            pts.append(pts[-1] + out * H * 0.12 + Vector((0, -H * 0.08, 0)))
        else:
            pts.append(base + Vector((0, H, 0)) + out * H * lean * 1.25)
        curve = resample(pts, 2)
        side = Vector((-math.sin(az), 0, math.cos(az)))
        rings = []
        m = len(curve)
        fr = frames(curve)
        for j, c in enumerate(curve[:-1]):
            t = j / (m - 1)
            w = 0.13 * (1 - t) ** 0.55 + 0.012
            T = fr[j][0]
            nrm = T.cross(side).normalized()
            rings.append([g.vert(c + side * w), g.vert(c + nrm * 0.03 * (1 - t * 0.7)), g.vert(c - side * w),
                          g.vert(c - nrm * 0.03 * (1 - t * 0.7))])
        _connect_rings(g, rings, 4, loop=False)
        tip = g.vert(curve[-1])
        last = rings[-1]
        for k in range(4):
            g.face(last[k], last[(k + 1) % 4], tip)
        b = rings[0]
        g.face(b[3], b[2], b[1], b[0])
    return {"Reed": g}, {}


def water_plantain():
    """Water plantain: seven broad, round-tipped leaves held up on slender stems (2 to 3 tall), tilted to the light, from
    one crown under the water."""
    g = Geo()
    rng = random.Random(433)
    for i in range(7):
        az = TAU * i / 7 + rng.uniform(-0.3, 0.3)
        H = rng.uniform(1.6, 2.5)
        out = yaw_vec(az)
        base = Vector((0.0, -0.35, 0.0)) + out * 0.08
        top = base + Vector((0, H, 0)) + out * rng.uniform(0.3, 0.7)
        stem = resample([base, base + Vector((0, H * 0.55, 0)) + out * 0.1, top], 2)
        tube(g, stem, lambda t, s, d, c: 0.045 - 0.015 * t, 4, tip=0.2)
        # the leaf: a broad rounded blade, its base on the stem top, held out and up, gently cupped
        L, Wd = rng.uniform(0.95, 1.25), 0.0
        Wd = L * rng.uniform(0.62, 0.72)
        rim = []
        for k in range(10):
            th = TAU * k / 10
            x = math.sin(th) * Wd * 0.5
            z = L * 0.5 - math.cos(th) * L * 0.5
            z += -0.06 * L * (1 - math.cos(th)) * 0  # (keep the tip round)
            y = 0.08 * (x / (Wd * 0.5)) ** 2 * Wd
            rim.append(Vector((x, y, z)))
        pitch = rng.uniform(0.35, 0.75)
        pts = [rot_y(rot_x(p, -pitch), -az + math.pi / 2) + top + Vector((0, -0.03, 0)) for p in rim]
        nrm = rot_y(rot_x(Vector((0, 1, 0)), -pitch), -az + math.pi / 2)
        # an inner ring for the leaf's camber (lifted along the normal)
        cen = sum(pts, Vector()) / len(pts)
        inner = [cen.lerp(p, 0.55) + nrm * 0.035 for p in pts]
        ids = [g.vert(p) for p in pts]
        iin = [g.vert(p) for p in inner]
        t_ = g.vert(cen + nrm * 0.05)
        b_ = g.vert(cen - nrm * 0.02)
        for k in range(10):
            j = (k + 1) % 10
            g.face(t_, iin[k], iin[j])
            g.face(iin[k], ids[k], ids[j], iin[j])
            g.face(b_, ids[j], ids[k])
    return {"Lily": g}, {}


def petal_drift():
    """About 200 fallen petals in an irregular drift some 16 across, denser at the middle: small rounded 5- and 6-sided
    petals (0.25-0.4 long) lying 0.03-0.12 above the ground, every one turned and tipped its own way and resting on a
    neighbour (they lie in little overlapping groups, as fallen petals do). Single-sided: they are only seen from above."""
    rose, pale = Geo(closed=False), Geo(closed=False)
    rng = random.Random(457)
    placed = []         # (centre, normal, radius)
    count = 0

    def outline_ok(x, z):
        a = math.atan2(z, x)
        return math.hypot(x, z) < 8.0 * (1.0 + 0.16 * W.fbm(math.cos(a) * 1.5, math.sin(a) * 1.5, 461, octaves=2))

    def petal(c, nrm, r, sides, yaw, g):
        # a rounded petal: an elongated 5/6-gon in the plane through c with normal nrm, facing up
        up = Vector(nrm).normalized()
        ax = Vector((math.cos(yaw), 0, math.sin(yaw)))
        ax = (ax - up * ax.dot(up)).normalized()
        bx = up.cross(ax).normalized()
        ids = []
        for k in range(sides):
            th = TAU * k / sides
            ids.append(g.vert(c + ax * math.cos(th) * r * 1.25 + bx * math.sin(th) * r * 0.8))
        # wound counter-clockwise seen from above (the face looks up)
        fn = (g.v[ids[1]] - g.v[ids[0]]).cross(g.v[ids[2]] - g.v[ids[0]])
        if fn.y < 0:
            ids = ids[::-1]
        for k in range(1, sides - 1):
            g.face(ids[0], ids[k], ids[k + 1])
    def clash(c, nrm, anchor):
        # a petal near another must not lie parallel to it (they would z-fight); its anchor is crossed on purpose
        for q, qn, qr in placed:
            if q is anchor:
                continue
            if (q - c).length < 0.48 and qn.angle(nrm) < 0.06:
                return True
        return False
    while count < 200:
        rr = abs(rng.gauss(0, 4.3))
        a = rng.uniform(0, TAU)
        x, z = math.cos(a) * rr, math.sin(a) * rr
        if not outline_ok(x, z) or any((Vector((x, 0.07, z)) - q).length < 0.5 for q, _, _ in placed):
            continue
        group = rng.choice((2, 2, 3, 3, 4))
        prev = None
        for m in range(group):
            for attempt in range(12):
                r = rng.uniform(0.11, 0.165)
                tilt = rng.uniform(0.07, 0.22)
                ta = rng.uniform(0, TAU)
                nrm = Vector((math.sin(tilt) * math.cos(ta), math.cos(tilt), math.sin(tilt) * math.sin(ta)))
                if prev is None:
                    c = Vector((x, rng.uniform(0.06, 0.08), z))
                else:
                    pc, pn, pr = prev
                    if nrm.angle(pn) < 0.12:
                        nrm = Vector((-pn.x, pn.y, -pn.z)).normalized()
                    d = yaw_vec(rng.uniform(0, TAU))
                    p = pc + d * pr * 0.45
                    p.y = pc.y - (pn.x * (p.x - pc.x) + pn.z * (p.z - pc.z)) / pn.y
                    d2 = yaw_vec(rng.uniform(0, TAU))
                    c = p + d2 * r * 0.4
                    c.y = p.y - (nrm.x * (c.x - p.x) + nrm.z * (c.z - p.z)) / nrm.y
                if not clash(c, nrm, prev[0] if prev else None):
                    break
            g = rose if (count + m) % 2 else pale
            petal(c, nrm, r, 5 if rng.random() < 0.5 else 6, rng.uniform(0, TAU), g)
            prev = (c, nrm, r)
            placed.append(prev)
            count += 1
            if count >= 200:
                break
    return {"Blossom": rose, "BlossomPale": pale}, {}


# ======================================================================================================================
# Koi (body and tail in one frame; the script swings the tail about TAIL_HINGE)
# ======================================================================================================================
KOI_NOSE, KOI_REAR = 1.6, -0.95
TAIL_HINGE = (0.0, 0.03, -0.85)
_KU = [0.0, 0.03, 0.1, 0.22, 0.38, 0.55, 0.72, 0.86, 1.0]
_KW = [0.0, 0.135, 0.225, 0.29, 0.322, 0.305, 0.245, 0.175, 0.118]
_KH = [0.0, 0.13, 0.235, 0.315, 0.35, 0.332, 0.272, 0.2, 0.15]
_KY = [-0.05, -0.045, -0.025, 0.0, 0.012, 0.014, 0.016, 0.022, 0.03]


def _interp(u, us, vs):
    for i in range(len(us) - 1):
        if us[i + 1] >= u:
            t = (u - us[i]) / (us[i + 1] - us[i])
            t = t * t * (3 - 2 * t) * 0.35 + t * 0.65
            return vs[i] + (vs[i + 1] - vs[i]) * t
    return vs[-1]


def koi_surface(u, th, off=0.0):
    """The body surface at (u: 0 nose .. 1 peduncle, th: 0 = +X side, pi/2 = the back)."""
    z = KOI_NOSE - u * (KOI_NOSE - KOI_REAR)
    hw = _interp(u, _KU, _KW) + off
    hh = _interp(u, _KU, _KH) + off
    yc = _interp(u, _KU, _KY)
    s = math.sin(th)
    belly = 0.86 if s < 0 else 1.0
    return Vector((math.cos(th) * hw, yc + s * hh * belly, z))


KOI_STYLE = {
    # base material, [(patch material, [(u, th, su, sth)] blobs, noise)]
    "Kohaku": ("KoiWhite", [("KoiRed", [(0.14, 1.57, 0.1, 0.95), (0.42, 1.35, 0.15, 1.0), (0.5, 2.2, 0.1, 0.7),
                                        (0.76, 1.65, 0.1, 0.85)], 0.35)]),
    "Showa": ("KoiBlack", [("KoiRed", [(0.2, 1.6, 0.1, 0.8), (0.5, 1.2, 0.11, 0.7), (0.62, 2.1, 0.08, 0.5)], 0.35),
                           ("KoiWhite", [(0.36, 4.6, 0.16, 0.9), (0.15, 3.6, 0.06, 0.4), (0.8, 4.9, 0.1, 0.8)], 0.3)]),
    "Ogon": ("KoiGold", []),
}


def _koi_mask(blobs, noise, u, th, seed):
    v = 0.0
    for bu, bt, su, st in blobs:
        dth = (th - bt + math.pi) % TAU - math.pi
        v = max(v, math.exp(-((u - bu) / su) ** 2 - (dth / st) ** 2))
    return v + noise * W.fbm(u * 6 + seed, th * 1.6, seed, octaves=2)


def koi_body(variant):
    base, patches = KOI_STYLE[variant]
    seed = {"Kohaku": 3, "Showa": 5, "Ogon": 7}[variant]
    us = [0.03, 0.075, 0.13, 0.2, 0.29, 0.38, 0.48, 0.58, 0.68, 0.78, 0.89, 1.0]
    seg = 14
    ths = [TAU * k / seg for k in range(seg)]
    # which material each cell takes, by its centre
    def material_at(u, th):
        best = base
        for mat, blobs, nz in patches:
            if _koi_mask(blobs, nz, u, th, seed) > 0.5:
                best = mat
        return best
    cells = {}
    for i in range(len(us) - 1):
        for k in range(seg):
            cells[(i, k)] = material_at((us[i] + us[i + 1]) / 2, ths[k] + math.pi / seg)
    # slide the vertices that sit on a colour boundary toward the patch's true edge (smooth outlines, same topology)
    param = {}
    for i, u in enumerate(us):
        for k in range(seg):
            mats = set()
            for di in (-1, 0):
                for dk in (-1, 0):
                    key = (i + di, (k + dk) % seg)
                    if key in cells:
                        mats.add(cells[key])
            pu, pt = u, ths[k]
            if len(mats) > 1 and 0 < i < len(us) - 1:
                best = None
                for mat, blobs, nz in patches:
                    if mat not in mats:
                        continue
                    m0 = _koi_mask(blobs, nz, u, ths[k], seed)
                    for ni, nk in ((i + 1, k), (i - 1, k), (i, k + 1), (i, k - 1)):
                        nu = us[min(max(ni, 0), len(us) - 1)]
                        nt = ths[k] + (TAU / seg) * (nk - k)
                        m1 = _koi_mask(blobs, nz, nu, nt, seed)
                        if (m0 - 0.5) * (m1 - 0.5) < 0:
                            t = min(0.42, max(0.0, (0.5 - m0) / (m1 - m0)))
                            if best is None or t < best[0]:
                                best = (t, nu, nt)
                if best:
                    t, nu, nt = best
                    pu, pt = u + (nu - u) * t, ths[k] + (nt - ths[k]) * t
            param[(i, k)] = (pu, pt)
    parts = {}
    verts = {}

    def gget(mat):
        return parts.setdefault(mat, Geo(closed=False))

    def vid(g, key, pos):
        d = verts.setdefault(id(g), {})
        if key not in d:
            d[key] = g.vert(pos)
        return d[key]
    pos = {key: koi_surface(*pt) for key, pt in param.items()}
    nose = Vector((0.0, _KY[0], KOI_NOSE))
    rear = Vector((0.0, _KY[-1], KOI_REAR - 0.03))
    for (i, k), mat in cells.items():
        g = gget(mat)
        j = (k + 1) % seg
        a, b, c, d = (i, k), (i, j), (i + 1, j), (i + 1, k)
        g.face(*[vid(g, key, pos[key]) for key in (a, d, c, b)])
    gb = gget(base)
    tip = gb.vert(nose)
    for k in range(seg):
        j = (k + 1) % seg
        gb.face(tip, vid(gb, (0, k), pos[(0, k)]), vid(gb, (0, j), pos[(0, j)]))
    end = gb.vert(rear)
    last = len(us) - 1
    for k in range(seg):
        j = (k + 1) % seg
        gb.face(end, vid(gb, (last, j), pos[(last, j)]), vid(gb, (last, k), pos[(last, k)]))
    # eyes (small dark domes, seated in the head), barbels (short, drooping from the mouth corners)
    eyes = Geo()
    for sx in (1, -1):
        th = 0.42 if sx > 0 else math.pi - 0.42
        p = koi_surface(0.13, th)
        nrm = (p - Vector((0, _interp(0.13, _KU, _KY), p.z))).normalized()
        blob(eyes, p - nrm * 0.012, lambda d: 0.042, 6, 4)
    if base == "KoiBlack":
        gget("KoiBlack")
    parts.setdefault("KoiBlack", Geo(closed=False)).add(eyes) if base != "KoiBlack" else gget("KoiBlack").add(eyes)
    barb = Geo()
    for sx in (1, -1):
        p0 = koi_surface(0.045, math.pi + sx * 0.0 if sx < 0 else 0.0)
        p0 = Vector((0.085 * sx, -0.075, KOI_NOSE - 0.1))
        pts = [p0 - Vector((0.03 * sx, -0.01, -0.02)), p0 + Vector((0.07 * sx, -0.05, -0.02)), p0 + Vector((0.11 * sx, -0.13, -0.09))]
        tube(barb, resample(pts, 1), lambda t, s, d, c: 0.02 - 0.012 * t, 3, tip=0.3)
    # (the barbels are closed tubes: merged into the base part, whose other faces are an open patchwork anyway)
    gb.add(barb)
    # fins (KoiFin): two pectorals, two pelvics, the dorsal along the back, the small anal fin
    fin = Geo()
    for sx in (1, -1):
        for (u0, spread, length, droop, back) in ((0.3, 0.32, 0.46, 0.55, 0.5), (0.62, 0.2, 0.3, 0.75, 0.6)):
            root = koi_surface(u0, -0.55 if sx > 0 else math.pi + 0.55)
            root = Vector((root.x * 0.8, root.y + 0.02, root.z))
            ax = Vector((sx * math.cos(droop), -math.sin(droop) * 0.5, -back)).normalized()
            up = Vector((0, 1, 0)).cross(ax).normalized()
            if up.length < 1e-6:
                up = Vector((1, 0, 0))
            rim = [root + Vector((0, 0, 0.07)), root - Vector((0, 0, 0.07))]
            for q in range(7):
                a = -spread + 2 * spread * q / 6
                rr = length * (0.82 + 0.18 * math.cos(a / spread * 1.2))
                rim.append(root + (ax * math.cos(a) + up * math.sin(a)) * rr)
            rim = [rim[0]] + rim[2:] + [rim[1]]
            nrm = (rim[2] - rim[0]).cross(rim[-2] - rim[0])
            lens(fin, rim, 0.022, nrm)
    # dorsal: a long low fin rising from the back, highest at the front, trailing edge rounded
    du = [0.34, 0.42, 0.52, 0.62, 0.72, 0.78]
    back = [koi_surface(u, math.pi / 2, -0.03) for u in du]
    tops = [back[0] + Vector((0, 0.22, -0.05)), back[1] + Vector((0, 0.24, -0.08)), back[2] + Vector((0, 0.2, -0.1)),
            back[3] + Vector((0, 0.15, -0.12)), back[4] + Vector((0, 0.09, -0.12)), back[5] + Vector((0, 0.035, -0.06))]
    lens(fin, back[::-1] + tops, 0.025, (1, 0, 0))
    au = [0.8, 0.86, 0.92]
    belly = [koi_surface(u, -math.pi / 2, -0.03) for u in au]
    lows = [belly[0] + Vector((0, -0.12, -0.06)), belly[1] + Vector((0, -0.13, -0.08)), belly[2] + Vector((0, -0.06, -0.06))]
    lens(fin, belly + lows[::-1], 0.02, (1, 0, 0))
    parts["KoiFin"] = fin
    return {k: v for k, v in parts.items() if v.f}, {"tail_hinge": list(TAIL_HINGE)}


def koi_tail(variant):
    """The tail, in the body's frame: the narrow peduncle (seated 0.15 deep in the body's rear, so it never gaps as it swings)
    and a broad, shallow-forked caudal fin with rounded lobes."""
    base = KOI_STYLE[variant][0]
    ped, fin = Geo(), Geo()
    hz = TAIL_HINGE[2]
    zs = [hz + 0.17, hz + 0.05, hz - 0.12, hz - 0.27, hz - 0.36]
    ws = [0.115, 0.1, 0.075, 0.06, 0.05]
    hs = [0.15, 0.135, 0.11, 0.1, 0.1]
    rings = []
    seg = 8
    for z, w, h in zip(zs, ws, hs):
        rings.append([ped.vert((math.cos(TAU * k / seg) * w, 0.03 + math.sin(TAU * k / seg) * h, z)) for k in range(seg)])
    _connect_rings(ped, [ped.vert((0, 0.03, zs[0] + 0.03))] + rings + [ped.vert((0, 0.03, zs[-1] - 0.04))], seg, loop=False)
    # caudal fin: a fan with two rounded lobes and a shallow notch
    z0 = zs[-2]
    outline = [(0.08, 0.0), (0.18, 0.12), (0.34, 0.26), (0.5, 0.37), (0.62, 0.4), (0.68, 0.33), (0.64, 0.2), (0.56, 0.08),
               (0.53, 0.0), (0.56, -0.08), (0.64, -0.2), (0.68, -0.33), (0.62, -0.4), (0.5, -0.37), (0.34, -0.26), (0.18, -0.12)]
    rim = [Vector((0.0, 0.03 + y, z0 - d * 0.74)) for d, y in outline]
    lens(fin, rim, 0.026, (1, 0, 0))
    return {base: ped, "KoiFin": fin}, {"tail_hinge": list(TAIL_HINGE)}


def ripple():
    """A thin ring for script-driven ripples: outer radius 1, inner 0.86, 0.02 thick, 32 segments, a flat top and a shallow
    vee beneath (the fewest triangles a closed 32-segment ring can have)."""
    g = Geo()
    lathe_loop(g, [(1.0, 0.01), (0.86, 0.01), (0.93, -0.01)], 32)
    return {"Ripple": g}, {}


# ======================================================================================================================
# Objects, UVs, shading
# ======================================================================================================================
def preview_material(suffix):
    name = "BS_" + suffix
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    r, g, b = (c / 255.0 for c in COLOURS[suffix])

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    col = (lin(r), lin(g), lin(b), 1.0)
    m.diffuse_color = col
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = {"Stone": 0.75, "Bark": 0.85, "Ripple": 0.2}.get(suffix, 0.6)
    if suffix == "KoiFin":
        bsdf.inputs["Alpha"].default_value = 0.6
    if suffix in ("Blossom", "BlossomPale", "LilyFlower"):
        bsdf.inputs["Subsurface Weight"].default_value = 0.15
    return m


def uv_charts(bm):
    """Box-projected UVs, one tile per TILE studs: faces grouped into charts by projection axis and adjacency, each chart
    no larger than a tile, placed at the tile's origin (so every UV lies inside 0-1)."""
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    axis = {}
    for f in bm.faces:
        n = f.normal
        axis[f.index] = max(range(3), key=lambda i: abs(n[i]))
    done = set()
    for f0 in bm.faces:
        if f0.index in done:
            continue
        ax = axis[f0.index]
        a, b = [i for i in range(3) if i != ax]
        chart, stack = [], [f0]
        lo = [min(v.co[a] for v in f0.verts), min(v.co[b] for v in f0.verts)]
        hi = [max(v.co[a] for v in f0.verts), max(v.co[b] for v in f0.verts)]
        done.add(f0.index)
        while stack:
            f = stack.pop()
            chart.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index in done or axis[g.index] != ax:
                        continue
                    nlo = [min(lo[0], min(v.co[a] for v in g.verts)), min(lo[1], min(v.co[b] for v in g.verts))]
                    nhi = [max(hi[0], max(v.co[a] for v in g.verts)), max(hi[1], max(v.co[b] for v in g.verts))]
                    if nhi[0] - nlo[0] > TILE or nhi[1] - nlo[1] > TILE:
                        continue
                    lo, hi = nlo, nhi
                    done.add(g.index)
                    stack.append(g)
        scale = max(TILE, hi[0] - lo[0], hi[1] - lo[1])
        for f in chart:
            for l in f.loops:
                l[uv].uv = ((l.vert.co[a] - lo[0]) / scale, (l.vert.co[b] - lo[1]) / scale)


def make_object(name, geo, suffix, coll, smooth_angle=80.0, weighted=False):
    bm = bmesh.new()
    vs = [bm.verts.new(W.rb(*p)) for p in geo.v]
    for f in geo.f:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    if geo.closed:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update()
    uv_charts(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    if smooth_angle < 179.0:
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    me.materials.append(preview_material(suffix))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if weighted:
        m = o.modifiers.new("Weighted", "WEIGHTED_NORMAL")
        m.mode = "FACE_AREA"
        m.keep_sharp = True
    return o


SHADING = {"Stone": (55.0, True), "Moss": (70.0, True), "Bark": (80.0, False), "Blossom": (180.0, False), "BlossomPale": (180.0, False),
           "LilyFlower": (180.0, False)}


def build_piece(piece, coll=None):
    """Builds one piece: {objects, meta}. The scene keeps only this piece's objects in its collection."""
    fn = PIECES[piece]
    coll = coll or W.collection("BS_" + piece.replace("BS_", ""))
    W.clear_collection(coll)
    res = fn()
    meta = {}
    if isinstance(res, Tree):
        parts = res.parts()
        meta.update(res.report())
    else:
        parts, extra = res
        meta.update(extra)
    objs = []
    for suffix, geo in sorted(parts.items()):
        ang, wt = meta.get("shading", {}).get(suffix) or SHADING.get(suffix, (80.0, False))
        objs.append(make_object("%s__%s" % (piece, suffix), geo, suffix, coll, ang, wt))
    return objs, meta


PIECES = {}
PIECES.update(TREES)
PIECES.update({
    "BS_Bridge": bridge, "BS_SteppingStoneA": stepping_a, "BS_SteppingStoneB": stepping_b, "BS_SteppingStoneC": stepping_c,
    "BS_EdgeRockA": edge_rock_a, "BS_EdgeRockB": edge_rock_b, "BS_EdgeRockC": edge_rock_c, "BS_KerbStone": kerb,
    "BS_SeatStone": seat_stone,
    "BS_LilyPadA": lily_pad_a, "BS_LilyPadB": lily_pad_b, "BS_LilyPadCluster": lily_pad_cluster, "BS_LilyFlower": lily_flower,
    "BS_Reeds": reeds, "BS_WaterPlantain": water_plantain, "BS_PetalDrift": petal_drift,
    "BS_KoiKohaku": lambda: koi_body("Kohaku"), "BS_KoiKohakuTail": lambda: koi_tail("Kohaku"),
    "BS_KoiShowa": lambda: koi_body("Showa"), "BS_KoiShowaTail": lambda: koi_tail("Showa"),
    "BS_KoiOgon": lambda: koi_body("Ogon"), "BS_KoiOgonTail": lambda: koi_tail("Ogon"),
    "BS_Ripple": ripple,
})


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def bbox_roblox(objs):
    pts = []
    for o in objs:
        pts += [o.matrix_world @ v.co for v in o.data.vertices]
    rb = [Vector((p.x, p.z, -p.y)) for p in pts]
    lo = [min(p[i] for p in rb) for i in range(3)]
    hi = [max(p[i] for p in rb) for i in range(3)]
    return [round(x, 2) for x in lo], [round(x, 2) for x in hi]


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.ops.outliner.orphans_purge(do_recursive=True)

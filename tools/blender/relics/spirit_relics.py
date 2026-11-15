"""The eleven Spirit Relics, modelled by hand in bmesh and baked: one reproducible headless build.

Each relic replaces the plain Neon cube the islands carried, and fits its island:
- IslandRoot (Yggdrasil): three World-Tree roots braid up out of a gnarled root knot, then open into a cage round a glowing amber
  seed, their tips curling out like claws; small golden leaves on short twigs.
- GroveHeart (Jade Grove): a cut emerald-jade heart held up by braided living vines rising from a mossy stone, moss tufts and leaves.
- JadeSeed (Jade Grove): a polished jade seed-pod carved with cloud scrolls, its four valves peeled open round a glowing lime kernel,
  a young sprout curling up out of it, on a gold calyx and a short jade stalk.
- WhisperingSpring (Jade Grove): a carved stone lotus basin; a ribbon of teal water spirals up out of it round a glowing pearl that
  rides a slender jet of water, droplets clinging to the ribbon.
- EmberHeart (Ember Peak): a heart of black obsidian split into plates along designed cracks (one point of impact), the molten
  core glowing between them, ember chips lodged in the cracks.
- AshenSigil (Ember Peak): an upright round tablet of ash-grey stone in a riveted dark-bronze ring with clasps, a flame finial and a
  cradle foot; its face carved with a glowing fire seal (a ring round three swirling flame tongues), its rim charred and chipped.
- CalderaCrown (Ember Peak): a crown of sharpened basalt columns on a polished obsidian band, every tip glowing like lava, a magma
  gem set at the front in a rock bezel.
- MoonMirror (Moonlit Isle): a round mirror of soft blue light in a moulded silver frame, cradled by a gold crescent moon, a moonstone
  in a pronged gold setting on top, a silver finial below.
- StarWell (Moonlit Isle): a miniature well of white marble blocks with a gold lip, brimming with starlight; a four-pointed sparkle
  star hovers above it, tied to the pool by two twisting threads of light and circled by a gold orbit ring.
- OriginAltar (Origin Abyss): a stepped octagonal obsidian dais on a cracked slate floor, a glowing spiral sigil rising into a vortex
  on top, ringed by leaning obsidian slabs carved with glowing marks (a gap at the front, one slab snapped, its top fallen outside).
- VoidShard (Origin Abyss): a jagged double-ended obsidian-glass shard with two smaller shards grown from its foot, split open by a
  zig-zag fissure that shows the violet core inside, bound by two gold chains.

Run headless, one stage per call (the work folder holds each relic's game pieces between stages):
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- clay <Id|all>     high and game meshes in clay
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- build <Id|all>    bake one relic (or all)
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- export            the FBX and the .blend
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- verify            re-import, QA (profile roblox), scans
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- review            the review sheet
    Blender -b --factory-startup -P tools/blender/relics/spirit_relics.py -- all
Environment: RELIC_WORK, a folder for working files (default renders/relics/_work); QA_CHECK_DIR, the folder holding the
mesh checker qa_check.py (verify stage, profile roblox).

Writes assets/relics/SpiritRelics.fbx and Relic_<Id>_{color,normal,roughness,metalness}.png, tools/blender/relics/SpiritRelics.blend
and renders/relics/SpiritRelics_review.png.

Layout: Z up, each relic faces -Y, 1 unit = 1 stud. Relic i stands on z = 0 at x = (i - 5) * 6. Per relic, Relic_<Id>_Body (one mesh,
one baked material), Relic_<Id>_Core (its main glow, a plain material in the glow colour: Neon in Studio), Relic_<Id>_Glow_<hex>
(small extra glows) and Relic_<Id>_Anchor (a 2 cm cube at the relic's visual centre, where the old cube's centre was). Every piece's
origin is its relic's anchor.
"""
import json
import math
import os
import random
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, geometry, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "relics")
BLEND = os.path.join(HERE, "SpiritRelics.blend")
FBX = os.path.join(OUT, "SpiritRelics.fbx")
SHEET = os.path.join(REPO, "renders", "relics", "SpiritRelics_review.png")
WORK = os.environ.get("RELIC_WORK") or os.path.join(REPO, "renders", "relics", "_work")
MAP = 1024
TAU = 2 * math.pi
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# Id, display name, glow colour (the colour each relic glowed as a cube, kept)
RELICS = (
    ("IslandRoot", "Root of the Island", (255, 165, 40)),
    ("GroveHeart", "Grove Heart", (40, 230, 120)),
    ("JadeSeed", "Jade Seed", (150, 255, 60)),
    ("WhisperingSpring", "Whispering Spring", (40, 220, 210)),
    ("EmberHeart", "Ember Heart", (255, 150, 30)),
    ("AshenSigil", "Ashen Sigil", (255, 200, 120)),
    ("CalderaCrown", "Caldera Crown", (255, 70, 20)),
    ("MoonMirror", "Moon Mirror", (150, 175, 255)),
    ("StarWell", "Star Well", (255, 225, 120)),
    ("OriginAltar", "Origin Altar", (185, 60, 255)),
    ("VoidShard", "Void Shard", (120, 60, 255)),
)
IDS = [r[0] for r in RELICS]
GLOW = {r[0]: r[2] for r in RELICS}
NAMES = {r[0]: r[1] for r in RELICS}
SPACING = 6.0
SCALE = {"IslandRoot": 1.12, "GroveHeart": 1.16, "EmberHeart": 2.0, "CalderaCrown": 1.2, "MoonMirror": 1.2, "OriginAltar": 1.24}


def hexof(rgb):
    return "%02x%02x%02x" % tuple(rgb)


def srgb(r, g, b):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


def lin(c):
    """A colour written as sRGB 0..1 to linear."""
    return tuple(srgb(*(x * 255 for x in c)))


def V(*a):
    return Vector(a)


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, Vector(axis))


def fbm(p, octaves=4, seed=0):
    p = Vector(p) + V(seed * 13.17, seed * 7.31, seed * 3.77)
    a, s, tot = 1.0, 1.0, 0.0
    for _ in range(octaves):
        tot += a * noise.noise(p * s)
        a *= 0.5
        s *= 2.03
    return tot


# =====================================================================================================================
# geometry kit: every piece is a closed solid of triangles and quads
# =====================================================================================================================
class Geo:
    """One body piece (or a glow): vertices, faces, a material, a per-vertex mask (0..1, read by the material) and a
    per-vertex texture space `tp` (tubes give it along-and-around coordinates, so bark ridges run along a root)."""

    def __init__(self, mat="GLOW", hard=False, bevel=0.0):
        self.co, self.faces, self.mask, self.tp = [], [], [], []
        self.mat, self.hard, self.bevel = mat, hard, bevel

    def v(self, p, mask=0.0, tp=None):
        self.co.append(Vector(p))
        self.mask.append(mask)
        self.tp.append(Vector(tp) if tp is not None else Vector(p))
        return len(self.co) - 1

    def f(self, idx):
        if len(set(idx)) == len(idx):
            self.faces.append(tuple(idx))

    def transform(self, m, start=0):
        m4 = m if len(m) == 4 else m.to_4x4()
        for i in range(start, len(self.co)):
            self.co[i] = m4 @ self.co[i]


def loft(g, rings, closed=True, cap0="flat", cap1="flat", masks=None, tps=None):
    """Joins rings of points into a solid. A ring of one point is a pole. Caps: 'flat' fans to the ring's centre, None
    leaves it open (only for rings that end on a pole)."""
    ids = []
    for k, ring in enumerate(rings):
        row = []
        for j, p in enumerate(ring):
            m = masks[k][j] if masks else 0.0
            t = tps[k][j] if tps else None
            row.append(g.v(p, m, t))
        ids.append(row)
    for k in range(len(ids) - 1):
        a, b = ids[k], ids[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            n = len(b)
            for j in range(n if closed else n - 1):
                g.f((a[0], b[j], b[(j + 1) % n]))
        elif len(b) == 1:
            n = len(a)
            for j in range(n if closed else n - 1):
                g.f((a[j], b[0], a[(j + 1) % n]))
        else:
            n = len(a)
            for j in range(n if closed else n - 1):
                g.f((a[j], b[j], b[(j + 1) % n], a[(j + 1) % n]))
    for ring, cap, rev in ((ids[0], cap0, True), (ids[-1], cap1, False)):
        if cap == "flat" and len(ring) > 2:
            c = sum((g.co[i] for i in ring), Vector()) / len(ring)
            mc = sum(g.mask[i] for i in ring) / len(ring)
            tc = sum((g.tp[i] for i in ring), Vector()) / len(ring)
            ci = g.v(c, mc, tc)
            n = len(ring)
            for j in range(n):
                g.f((ring[j], ring[(j + 1) % n], ci) if rev else (ring[(j + 1) % n], ring[j], ci))
    return ids


def catmull(pts, per=8):
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        return [lerp(pts[0], pts[-1], i / (per * 2)) for i in range(per * 2 + 1)]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def resample(pts, n):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    out, j = [], 0
    for i in range(n):
        s = L[-1] * i / (n - 1)
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = L[j + 1] - L[j]
        t = 0 if seg < 1e-9 else (s - L[j]) / seg
        out.append(lerp(pts[j], pts[j + 1], t))
    return out, L[-1]


def frames(pts, up=None, closed=False):
    n = len(pts)
    T = []
    for i in range(n):
        if closed:
            d = pts[(i + 1) % n] - pts[(i - 1) % n]
        else:
            d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        T.append(d.normalized())
    ref = Vector(up) if up is not None else Z
    if abs(T[0].dot(ref)) > 0.95:
        ref = X if abs(T[0].dot(X)) < 0.9 else Y
    if closed and up is not None:
        # a closed loop round an axis: the axis projected at every point, so the loop closes without a twist
        N = [(ref - t * ref.dot(t)).normalized() for t in T]
        return T, N, [t.cross(nn) for t, nn in zip(T, N)]
    N = [(ref - T[0] * ref.dot(T[0])).normalized()]
    for i in range(1, n):
        q = T[i - 1].rotation_difference(T[i])
        nn = q @ N[-1]
        nn = (nn - T[i] * nn.dot(T[i])).normalized()
        N.append(nn)
    B = [t.cross(nn) for t, nn in zip(T, N)]
    return T, N, B


def tube(g, path, radius, sides=8, n=None, section=None, rfn=None, tip0=False, tip1=True, up=None, closed=False, twist=0.0,
         per=8, mask=None, flat_caps=True, sides_fn=None):
    """A solid swept along a path (control points, smoothed). radius: float or f(t). section(t, theta) -> (x, y) on the unit
    circle's place (for flattened or square sections). rfn(t, theta) scales the radius (bark ridges in the high model).
    tip0/tip1 close an end on a point. Returns the sampled path."""
    pts = catmull(path, per) if not closed else catmull(list(path) + list(path[:3]), per)[per:per * (len(path) + 1) + 1]
    if closed:
        pts = pts[:-1]
    if n is None:
        n = len(pts)
    if not closed:
        pts, L = resample(pts, n)
    else:
        L = sum((pts[(i + 1) % len(pts)] - pts[i]).length for i in range(len(pts)))
        n = len(pts)
    T, N, B = frames(pts, up, closed)
    rings, masks, tps = [], [], []
    acc = 0.0
    for i, p in enumerate(pts):
        if i:
            acc += (pts[i] - pts[i - 1]).length
        t = i / (n - 1) if not closed else i / n
        r = radius(t) if callable(radius) else radius
        if (i == 0 and tip0) or (i == n - 1 and tip1):
            rings.append([p])
            masks.append([mask(t, 0) if mask else 0.0])
            tps.append([V(0, 0, acc)])
            continue
        ring, mr, tr = [], [], []
        for j in range(sides):
            th = TAU * j / sides + twist * t
            x, y = section(t, th) if section else (math.cos(th), math.sin(th))
            m = rfn(t, th) if rfn else 1.0
            ring.append(p + (N[i] * x + B[i] * y) * r * m)
            mr.append(mask(t, th) if mask else 0.0)
            tr.append(V(math.cos(th) * max(r, 0.02), math.sin(th) * max(r, 0.02), acc))
        rings.append(ring)
        masks.append(mr)
        tps.append(tr)
    if closed:
        rings.append(rings[0])
        masks.append(masks[0])
        tps.append(tps[0])
        loft(g, rings[:-1] + [rings[0]], cap0=None, cap1=None, masks=masks, tps=tps)
        _weld_last(g, len(rings[0]))
    else:
        loft(g, rings, cap0="flat" if flat_caps else None, cap1="flat" if flat_caps else None, masks=masks, tps=tps)
    return pts


def _weld_last(g, n):
    """A closed tube's last ring repeats its first: remap it onto the first ring and drop it."""
    last = list(range(len(g.co) - n, len(g.co)))
    # the first ring of this tube: find it by position
    first = []
    for i in last:
        p = g.co[i]
        for k in range(len(g.co) - n - 1, -1, -1):
            if (g.co[k] - p).length < 1e-9:
                first.append(k)
                break
    remap = dict(zip(last, first))
    g.faces = [tuple(remap.get(i, i) for i in f) for f in g.faces]
    del g.co[-n:], g.mask[-n:], g.tp[-n:]


def ring_path(c, axis, R, n=16, wob=None, phase=0.0):
    """Control points of a circle (or a wobbly loop) round axis."""
    axis = Vector(axis).normalized()
    a = (X if abs(axis.dot(X)) < 0.9 else Y).cross(axis).normalized()
    b = axis.cross(a)
    pts = []
    for i in range(n):
        th = TAU * i / n + phase
        r = R * (wob(th) if wob else 1.0)
        pts.append(Vector(c) + (a * math.cos(th) + b * math.sin(th)) * r)
    return pts


def torus(g, c, axis, R, r, nu=16, nv=6, section=None, wob=None, rfn=None, phase=0.0):
    tube(g, ring_path(c, axis, R, nu, wob, phase), r, sides=nv, section=section, closed=True, per=2, up=axis, rfn=rfn)


def superellipse(a, b, p=4.0):
    def sec(t, th):
        c, s = math.cos(th), math.sin(th)
        return (a * math.copysign(abs(c) ** (2 / p), c), b * math.copysign(abs(s) ** (2 / p), s))
    return sec


def lathe(g, profile, sides, c=(0, 0, 0), axis=Z, rfn=None, phase=0.0, mask=None):
    """Revolves (r, h) points round axis through c. r = 0 is a pole."""
    c = Vector(c)
    axis = Vector(axis).normalized()
    a = (X if abs(axis.dot(X)) < 0.9 else Y).cross(axis).normalized()
    if abs(axis.dot(Z)) > 0.99:
        a = X.copy()
    b = axis.cross(a)
    rings, masks, tps = [], [], []
    for k, (r, h) in enumerate(profile):
        if r <= 1e-9:
            rings.append([c + axis * h])
            masks.append([mask(k, 0.0) if mask else 0.0])
            tps.append([c + axis * h])
            continue
        ring, mr = [], []
        for j in range(sides):
            th = TAU * j / sides + phase
            m = rfn(k, th) if rfn else 1.0
            ring.append(c + axis * h + (a * math.cos(th) + b * math.sin(th)) * r * m)
            mr.append(mask(k, th) if mask else 0.0)
        rings.append(ring)
        masks.append(mr)
        tps.append(list(ring))
    loft(g, rings, masks=masks, tps=tps)


def blob(g, c, radii, nu=16, nv=10, fn=None, frame=None):
    """A deformed sphere. fn(direction) -> radius scale."""
    c = Vector(c)
    M = frame or Matrix.Identity(3)
    rings = []
    for i in range(nv + 1):
        ph = math.pi * i / nv
        if i == 0 or i == nv:
            d = V(0, 0, -1 if i == 0 else 1)
            s = fn(d) if fn else 1.0
            rings.append([c + M @ V(0, 0, d.z * radii[2] * s)])
            continue
        ring = []
        for j in range(nu):
            th = TAU * j / nu
            d = V(math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), -math.cos(ph))
            s = fn(d) if fn else 1.0
            ring.append(c + M @ V(d.x * radii[0] * s, d.y * radii[1] * s, d.z * radii[2] * s))
        rings.append(ring)
    loft(g, rings)


def offset_loop(loop, d):
    """Moves a closed 2D loop d to its left (inward for a counter-clockwise outline, outward from a clockwise hole)."""
    n = len(loop)
    out = []
    for i in range(n):
        p0, p1, p2 = loop[i - 1], loop[i], loop[(i + 1) % n]
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = V(-e0.y, e0.x)
        n1 = V(-e1.y, e1.x)
        m = (n0 + n1)
        if m.length < 1e-6:
            m = n0
        m.normalize()
        k = max(0.35, m.dot(n1))
        out.append(p1 + m * (d / k))
    return out


def area2(loop):
    return 0.5 * sum(loop[i - 1].x * loop[i].y - loop[i].x * loop[i - 1].y for i in range(len(loop)))


def slab(g, loops, depth, bevel, segs, frame, mask=0.0):
    """An outline (first loop counter-clockwise, further loops are holes) extruded `depth` along the frame's z, with a rounded
    bevel of `segs` steps. frame = (origin, x, y, z) or a 4x4 matrix."""
    loops = [[Vector((p[0], p[1])) for p in lp] for lp in loops]
    loops[0] = loops[0] if area2(loops[0]) > 0 else loops[0][::-1]
    for i in range(1, len(loops)):
        loops[i] = loops[i] if area2(loops[i]) < 0 else loops[i][::-1]
    if isinstance(frame, Matrix):
        M = frame
    else:
        o, fx, fy, fz = frame
        M = Matrix((list(fx) + [0], list(fy) + [0], list(fz) + [0], [0, 0, 0, 1])).transposed()
        M.translation = o
    prof = []
    b = min(bevel, depth / 2 - 1e-4)
    if b <= 0 or segs < 1:
        prof = [(0.0, 0.0), (0.0, depth)]
    else:
        for k in range(segs + 1):
            a = (math.pi / 2) * k / segs
            prof.append((b * (1 - math.sin(a)), b * (1 - math.cos(a))))
        for k in range(segs + 1):
            a = (math.pi / 2) * k / segs
            prof.append((b * (1 - math.cos(a)), depth - b + b * math.sin(a)))
    ringsets = []
    for inset, z in prof:
        rs = []
        for lp in loops:
            ol = offset_loop(lp, inset) if inset > 0 else lp
            rs.append([g.v(M @ V(p.x, p.y, z), mask) for p in ol])
        ringsets.append(rs)
    for k in range(len(ringsets) - 1):
        for li in range(len(loops)):
            a, bb = ringsets[k][li], ringsets[k + 1][li]
            n = len(a)
            for j in range(n):
                g.f((a[j], a[(j + 1) % n], bb[(j + 1) % n], bb[j]))
    for rs, top in ((ringsets[0], False), (ringsets[-1], True)):
        flat = [[g.co[i] for i in r] for r in rs]
        idx = [i for r in rs for i in r]
        local = [[(M.inverted() @ p).to_2d().to_3d() for p in r] for r in flat]
        tris = geometry.tessellate_polygon(local)
        for t in tris:
            a, bb, c = idx[t[0]], idx[t[1]], idx[t[2]]
            pa, pb, pc = (g.co[i] for i in (a, bb, c))
            nz = (M.to_3x3().inverted() @ (pb - pa).cross(pc - pa)).z
            if (nz > 0) != top:
                g.f((a, c, bb))
            else:
                g.f((a, bb, c))


def frame_of(origin, z, x_hint=X):
    z = Vector(z).normalized()
    x = Vector(x_hint)
    x = (x - z * x.dot(z))
    if x.length < 1e-6:
        x = Y - z * Y.dot(z)
    x.normalize()
    y = z.cross(x)
    return (Vector(origin), x, y, z)


def crystal(g, base, axis, length, radius, sides=6, tip=0.28, seed=0, taper=0.85, foot=0.7, jitter=0.16, tip_off=0.08,
            base_tip=False, base_len=0.2, twist=0.0):
    """A faceted crystal: a jittered prism, sharpened at the top (and the foot when base_tip)."""
    rnd = random.Random(seed)
    axis = Vector(axis).normalized()
    _, a, b, _ = frame_of(base, axis)
    angs = [TAU * j / sides + rnd.uniform(-0.25, 0.25) * TAU / sides for j in range(sides)]
    rads = [1 + rnd.uniform(-jitter, jitter) for _ in range(sides)]
    base = Vector(base)

    def ring(h, s, rot_=0.0):
        return [base + axis * h + (a * math.cos(t + rot_) + b * math.sin(t + rot_)) * radius * s * rr for t, rr in zip(angs, rads)]
    off = (a * rnd.uniform(-1, 1) + b * rnd.uniform(-1, 1)) * radius * tip_off
    rings = []
    if base_tip:
        rings.append([base - axis * base_len * length + off * 0.5])
        rings.append(ring(0.0, foot))
    else:
        rings.append(ring(0.0, foot))
    rings.append(ring(length * 0.18, 1.0, twist * 0.2))
    rings.append(ring(length * (1 - tip), taper, twist))
    rings.append([base + axis * length + off])
    loft(g, rings)


def leaf(g, base, direction, normal, length, width, thick=0.014, curl=0.25, steps=6, sides=6, shape=None, droop=0.0):
    """A leaf: a thin closed blade along its midline, rounded (no midrib, no almond outline)."""
    d = Vector(direction).normalized()
    nrm = (Vector(normal) - d * Vector(normal).dot(d)).normalized()
    side = d.cross(nrm).normalized()
    pts = []
    for i in range(steps + 1):
        t = i / steps
        bend = curl * t * t * length
        pts.append(Vector(base) + d * length * t + nrm * bend - Z * droop * t * t * length)
    wf = shape or (lambda t: math.sin(math.pi * min(1.0, t * 1.08)) ** 0.75 * (1 - 0.25 * t))

    def sec(t, th):
        w = max(0.04, wf(t))
        return (math.cos(th) * w, math.sin(th) * (thick / width) * (0.5 + 0.5 * w))
    tube(g, pts, width / 2, sides=sides, n=steps + 1, section=sec, tip0=False, tip1=True, up=nrm, per=2)


# =====================================================================================================================
# the relics
# =====================================================================================================================
class Relic:
    def __init__(self, hi):
        self.hi = hi
        self.body = []
        self.core = Geo("GLOW")
        self.glows = {}
        self.anchor = Vector()

    def piece(self, mat, hard=False, bevel=0.0):
        g = Geo(mat, hard, bevel)
        self.body.append(g)
        return g

    def glow(self, hexstr):
        if hexstr not in self.glows:
            self.glows[hexstr] = Geo("GLOW")
        return self.glows[hexstr]

    def q(self, lo, hi):
        return hi if self.hi else lo


def bark_rfn(seed, amp=0.17, k=3.0):
    """Ridged bark, the ridges running along the root, with knots."""
    def f(t, th):
        c, s = math.cos(th), math.sin(th)
        p = V(c * k, s * k, t * 2.2 + seed)
        r = 1 - abs(noise.noise(V(p.x, p.y, p.z * 0.35) + V(seed, 0, 0)))
        r = r * r
        knot = max(0.0, noise.noise(V(c * 1.2 + seed, s * 1.2, t * 6.0)) - 0.35) * 1.6
        return 1 + amp * (r - 0.5) + amp * 0.9 * knot + 0.03 * noise.noise(V(c * 9, s * 9, t * 30 + seed))
    return f


def r_island_root(hi):
    """A fist of World-Tree root clenched round an amber seed: a buttressed root ball, a twisted trunk of four roots that
    open into a cage round the seed and twist shut again above it, ending in short gnarled claws; golden leaves on twigs."""
    R = Relic(hi)
    q = R.q
    sc = V(0, 0, 1.86)
    sr = 0.4
    fib = []
    nf = 34
    for i in range(nf):
        zz = 1 - 2 * (i + 0.5) / nf
        rr = math.sqrt(1 - zz * zz)
        th = i * math.pi * (3 - math.sqrt(5))
        fib.append(V(math.cos(th) * rr, math.sin(th) * rr, zz))

    def seed_shape(d):
        best = min((d - f).length for f in fib)
        return 1 + 0.05 * (1 - min(1.0, best / 0.42)) ** 1.5
    blob(R.core, sc, (sr, sr, sr * 1.04), nu=18, nv=12, fn=seed_shape)
    R.anchor = sc.copy()

    def root_r(t):
        if t < 0.3:
            return lerp(0.2, 0.13, t / 0.3)
        if t < 0.72:
            return lerp(0.13, 0.085, (t - 0.3) / 0.42)
        return lerp(0.085, 0.03, (t - 0.72) / 0.28)

    sides = q(6, 40)
    top = sc + Z * (sr + 0.2)
    for k in range(4):
        ph = k * TAU / 4 + 0.3
        pts = []
        for i in range(5):
            t = i / 4
            a = ph + t * TAU * 0.42
            rr = 0.17 - 0.03 * t
            pts.append(V(math.cos(a) * rr, math.sin(a) * rr, 0.42 + t * 0.78))
        a0 = ph + TAU * 0.42
        for i in range(1, 7):
            t = i / 6
            pol = math.radians(152 - 122 * t)
            az = a0 + math.radians(70) * t
            off = sr + 0.075 + 0.03 * math.sin(math.pi * t)
            pts.append(sc + V(math.sin(pol) * math.cos(az) * off, math.sin(pol) * math.sin(az) * off, math.cos(pol) * off))
        az = a0 + math.radians(70)
        # twisting shut above the seed, then a short claw curling out and down
        for i in range(1, 4):
            t = i / 3
            a = az + t * math.radians(80)
            rr = lerp(0.2, 0.07, t)
            pts.append(top + V(math.cos(a) * rr, math.sin(a) * rr, -0.12 + t * 0.32))
        a = az + math.radians(80)
        o = V(math.cos(a), math.sin(a), 0)
        s = (1.0, 0.75, 0.9, 0.6)[k]
        tz = top.z + 0.2
        pts += [V(0, 0, tz) + o * 0.14 + Z * 0.16 * s, V(0, 0, tz) + o * 0.3 * s + Z * 0.22 * s, V(0, 0, tz) + o * 0.42 * s + Z * 0.12 * s,
                V(0, 0, tz) + o * 0.44 * s - Z * 0.02 * s]
        path = tube(R.piece("BARK"), pts, root_r, sides=sides, n=q(30, 300), rfn=bark_rfn(k * 3.1) if hi else None, per=5)
        if k < 3:
            # a twig of golden leaves from the cage
            j = int(len(path) * (0.42 + 0.06 * k))
            base = path[j]
            outd = V(base.x - sc.x, base.y - sc.y, 0).normalized()
            tang = Z.cross(outd)
            tw = [base, base + outd * 0.16 + Z * 0.06 + tang * 0.04, base + outd * 0.3 + Z * 0.14 + tang * 0.08]
            tube(R.piece("BARK"), tw, lambda t: 0.04 * (1 - t) + 0.014, sides=q(5, 16), n=q(5, 30), per=4)
            tip = tw[-1]
            for m, (dd, nn) in enumerate(((outd + Z * 0.5, -tang + Z * 0.4), (outd * 0.3 + tang + Z * 0.2, outd + Z), (outd * 0.4 - tang + Z * 0.7, outd + Z * 0.3))):
                leaf(R.piece("GOLDLEAF"), tip - outd * 0.03, dd, nn, 0.3 - 0.04 * m, 0.19, thick=0.02, curl=0.2, steps=q(4, 14), sides=q(6, 14))
    # the root ball and its buttress roots, short and heavy, arching down into the ground
    def knot(d):
        return 1 + 0.16 * noise.noise(d * 2.2 + V(3, 1, 0)) + 0.05 * noise.noise(d * 6)
    blob(R.piece("BARK"), V(0, 0, 0.4), (0.5, 0.5, 0.4), nu=q(12, 90), nv=q(8, 56), fn=knot)
    for k in range(6):
        a = k * TAU / 6 + 0.15
        d = V(math.cos(a), math.sin(a), 0)
        ln = (1.0, 0.8, 1.05, 0.85, 0.95, 0.78)[k]
        side = Z.cross(d) * (0.06 if k % 2 else -0.06)
        pts = [V(0, 0, 0.55) + d * 0.15, V(0, 0, 0.48) + d * 0.48 * ln, V(0, 0, 0.26) + d * 0.74 * ln + side, V(0, 0, 0.07) + d * 0.9 * ln + side * 1.5]
        tube(R.piece("BARK"), pts, lambda t: 0.06 + 0.16 * (1 - t) ** 1.1, sides=q(6, 32), n=q(7, 90), rfn=bark_rfn(10 + k) if hi else None, per=6)
    return R


def heart_outline(n, lobe=1.0, asym=0.0):
    """The classic heart curve, as (x, y) points counter-clockwise, about 1 wide, centred."""
    pts = []
    for i in range(n):
        t = TAU * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        if x < 0:
            x *= 1 + asym
        pts.append(V(x / 32, (y + 2.5) / 32))
    if area2(pts) < 0:
        pts = pts[::-1]
    return pts


def r_grove_heart(hi):
    R = Relic(hi)
    q = R.q
    hc = V(0, 0, 2.0)
    # the cut heart: girdle, crown and pavilion facets round a table on each face
    tilt = rot(Y, -8) @ rot(Z, 0)
    outl = heart_outline(22)
    W, D = 1.42, 0.66
    rings = []
    for s, yy in ((0.0, -0.5), (0.58, -0.43), (1.0, -0.16), (1.0, 0.16), (0.58, 0.43), (0.0, 0.5)):
        if s == 0:
            rings.append([hc + tilt @ V(0, yy * D, 0.05 * W)])
            continue
        rings.append([hc + tilt @ V(p.x * W * s, yy * D, p.y * W * s + (1 - s) * 0.05 * W) for p in outl])
    loft(R.core, rings)
    R.anchor = hc.copy()
    # the mossy stone it grows from
    def stone(d):
        return 1 + 0.12 * noise.noise(d * 1.8 + V(5, 2, 1)) + 0.05 * noise.noise(d * 5 + V(1, 1, 1))
    blob(R.piece("STONE"), V(0, 0, 0.28), (0.62, 0.54, 0.32), nu=q(12, 90), nv=q(8, 56), fn=stone)
    rnd = random.Random(7)
    for i in range(6):
        a = rnd.uniform(0, TAU)
        rr = rnd.uniform(0.25, 0.62)
        rr *= 0.86
        p = V(math.cos(a) * rr * 0.62 / 0.54, math.sin(a) * rr, 0)
        p.z = 0.28 + 0.32 * math.sqrt(max(0.05, 1 - (p.x / 0.62) ** 2 - (p.y / 0.54) ** 2)) - 0.03 + 0.017 * i
        s = rnd.uniform(0.16, 0.25)

        def tuft(d, sd=i):
            return 1 + 0.25 * abs(noise.noise(d * 4 + V(sd, 0, 0))) - 0.2 * max(0.0, -d.z)
        blob(R.piece("MOSS"), p, (s, s * 0.85, s * 0.32), nu=q(8, 36), nv=q(4, 22), fn=tuft)
    # braided vines: three strands twist up from the stone, part into six cradling the heart, their tips curl out
    sides = q(6, 28)
    vine_r = lambda t: 0.028 + 0.075 * (1 - t) ** 0.9  # noqa: E731
    for k in range(3):
        ph = k * TAU / 3
        pts = []
        for i in range(6):
            t = i / 5
            a = ph + t * TAU * 0.9
            pts.append(V(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.45 + t * 0.55))
        # each strand splits in two that run up the heart's sides (each branch braided on its own line, never coinciding)
        for side in (-1, 1):
            az = ph + TAU * 0.9 + side * 0.45
            br = [V(math.cos(ph + side * 0.22 + (i / 5) * TAU * 0.9) * (0.1 + 0.025 * side), math.sin(ph + side * 0.22 + (i / 5) * TAU * 0.9) * (0.1 + 0.025 * side),
                    0.42 + 0.014 * (k * 2 + (side + 1) // 2) + (i / 5) * 0.55) for i in range(6)]
            for i in range(1, 6):
                t = i / 5
                pol = math.radians(165 - 95 * t)
                rr = 0.66 * math.sin(pol) + 0.05
                br.append(hc + V(math.cos(az + side * 0.25 * t) * rr * 0.95, math.sin(az + side * 0.25 * t) * rr * 0.62, math.cos(pol) * 0.62))
            last = br[-1]
            o = (last - V(hc.x, hc.y, last.z)).normalized()
            br += [last + o * 0.06 + Z * 0.1, last + o * 0.16 + Z * 0.08, last + o * 0.2 - Z * 0.03]
            g = R.piece("VINE")
            path = tube(g, br, vine_r, sides=sides, n=q(22, 220), rfn=(lambda t, th, kk=k * 2 + side: 1 + 0.06 * noise.noise(V(math.cos(th) * 2, math.sin(th) * 2, t * 40 + kk))) if hi else None, per=5)
            # leaves along the strand
            for m, tt in enumerate((0.6, 0.82)):
                i0 = int(tt * (len(path) - 1))
                p = path[i0]
                d = (path[min(i0 + 1, len(path) - 1)] - path[i0 - 1]).normalized()
                o2 = (p - V(hc.x, hc.y, p.z)).normalized()
                leaf(R.piece("LEAF"), p, (o2 + d * 0.5 + Z * 0.2 * side), d, 0.27 - m * 0.04, 0.15, curl=0.3, steps=q(4, 14), sides=q(5, 14))
            # a moss tuft where the strand leaves the braid
    for i in range(3):
        a = i * TAU / 3 + 0.5
        p = V(math.cos(a) * 0.12, math.sin(a) * 0.12, 0.98)
        blob(R.piece("MOSS"), p, (0.13, 0.13, 0.08), nu=q(7, 30), nv=q(4, 18), fn=lambda d, s=i: 1 + 0.25 * abs(noise.noise(d * 4 + V(s, 4, 0))))
    return R


def r_jade_seed(hi):
    R = Relic(hi)
    q = R.q
    kc = V(0, 0, 1.78)
    # the kernel: round, in three soft lobes
    blob(R.core, kc, (0.47, 0.47, 0.44), nu=16, nv=10, fn=lambda d: 1 + 0.05 * math.cos(3 * math.atan2(d.y, d.x)) * (1 - d.z * d.z))
    R.anchor = kc.copy()
    # the stalk and the gold calyx
    lathe(R.piece("JADE"), [(0, 0.0), (0.2, 0.0), (0.24, 0.05), (0.18, 0.14), (0.12, 0.35), (0.14, 0.55), (0.2, 0.68), (0, 0.8)], q(14, 96))
    torus(R.piece("GOLD"), V(0, 0, 0.72), Z, 0.24, 0.06, nu=q(16, 96), nv=q(6, 24), section=superellipse(1.0, 1.0, 3.0))
    lathe(R.piece("GOLD"), [(0, 0.08), (0.24, 0.08), (0.26, 0.12), (0.22, 0.16), (0, 0.16)], q(14, 96))
    # four thick valves: closed round the kernel below, their pointed tips peeling back like a husk
    n_valves = 4
    PR, PZ, c0 = 0.66, 1.0, V(0, 0, 1.62)
    for k in range(n_valves):
        a0 = k * TAU / n_valves - math.pi / 2
        span = TAU / n_valves - math.radians(3)
        g = R.piece("JADE")
        nu, nv = q(7, 70), q(12, 120)
        rings_out, rings_in, mo = [], [], []
        for i in range(nv + 1):
            t = i / nv
            pol = math.radians(176 - 168 * t)
            s = max(0.0, (t - 0.36) / 0.64)
            width = 1.0 if t < 0.55 else max(0.08, 1 - ((t - 0.55) / 0.45) ** 1.3 * 0.92)
            width *= min(1.0, 0.35 + t * 6)
            row_o, row_i, row_m = [], [], []
            for j in range(nu + 1):
                u = j / nu
                w = (u - 0.5) * span * width
                az = a0 + w + 0.35 * s ** 2
                rad = V(math.cos(az), math.sin(az), 0)
                mid = V(math.cos(a0 + 0.35 * s ** 2), math.sin(a0 + 0.35 * s ** 2), 0)
                p = c0 + rad * math.sin(pol) * PR + Z * math.cos(pol) * PZ
                nrm = (rad * math.sin(pol) / PR + Z * math.cos(pol) / PZ).normalized()
                # the peel: the upper part bends outward and down
                p = p + mid * (1.05 * s ** 1.7) - Z * (0.75 * s ** 2.6)
                th = 0.1 * (0.75 + 0.25 * math.sin(math.pi * t)) * (1 - 0.5 * s)
                groove = scroll_groove(u, t, k) if hi else 0.0
                row_o.append(p + nrm * (th * 0.5 - 0.022 * groove))
                row_i.append(p - nrm * th * 0.5)
                row_m.append(groove)
            rings_out.append(row_o)
            rings_in.append(row_i)
            mo.append(row_m)
        _shell(g, rings_out, rings_in, mo)
    # the sprout, curling up out of the kernel, with two leaves
    sp = [kc + V(0, 0, 0.25), kc + V(0.05, 0, 0.75), kc + V(-0.05, 0.02, 1.15), kc + V(0.12, -0.02, 1.48), kc + V(0.36, -0.04, 1.6), kc + V(0.48, -0.05, 1.45), kc + V(0.4, -0.05, 1.32)]
    path = tube(R.piece("SPROUT"), sp, lambda t: 0.055 * (1 - t) + 0.016, sides=q(7, 24), n=q(18, 140), per=6)
    for (tt, dd, nn) in ((0.38, V(-1, -0.2, 0.55), V(0.3, -1, 0.4)), (0.55, V(1, 0.3, 0.5), V(-0.3, -1, 0.5))):
        i0 = int(tt * (len(path) - 1))
        leaf(R.piece("SPROUT"), path[i0], dd, nn, 0.5, 0.3, thick=0.024, curl=0.3, steps=q(6, 16), sides=q(6, 16))
    return R


def scroll_groove(u, t, k):
    """Cloud-scroll grooves carved on a valve, as a groove depth 0..1 at the valve's (across, up) coordinates."""
    best = 1.0
    # two spirals (scrolls) joined by a wave, mirrored left and right on alternate valves
    for cx, cy, s, turn in ((0.5, 0.3, 0.12, 1), (0.3, 0.5, 0.08, -1), (0.7, 0.5, 0.08, 1), (0.5, 0.64, 0.06, -1)):
        dx, dy = (u - cx) / 0.9, (t - cy)
        r = math.hypot(dx, dy)
        a = math.atan2(dy, dx) * turn
        # distance to the spiral r = s * (a + 2 pi n) / (2 pi * 1.6)
        pitch = s / 1.6
        for nloop in range(3):
            rs = pitch * ((a % TAU) / TAU + nloop)
            if rs <= s:
                best = min(best, abs(r - rs) / 0.012)
    # a rim groove following the valve edge
    edge = min(u, 1 - u) * 0.9
    best = min(best, abs(edge - 0.08) / 0.01)
    return max(0.0, 1 - best) ** 0.7


def _shell(g, outer, inner, masks):
    """A thick shell from two grids (rows by columns), closed along its four edges."""
    rows, cols = len(outer), len(outer[0])
    oi = [[g.v(p, masks[i][j]) for j, p in enumerate(r)] for i, r in enumerate(outer)]
    ii = [[g.v(p, masks[i][j]) for j, p in enumerate(r)] for i, r in enumerate(inner)]
    for i in range(rows - 1):
        for j in range(cols - 1):
            g.f((oi[i][j], oi[i][j + 1], oi[i + 1][j + 1], oi[i + 1][j]))
            g.f((ii[i][j], ii[i + 1][j], ii[i + 1][j + 1], ii[i][j + 1]))
    for i in range(rows - 1):
        g.f((oi[i][0], oi[i + 1][0], ii[i + 1][0], ii[i][0]))
        g.f((oi[i][-1], ii[i][-1], ii[i + 1][-1], oi[i + 1][-1]))
    for j in range(cols - 1):
        g.f((oi[0][j], ii[0][j], ii[0][j + 1], oi[0][j + 1]))
        g.f((oi[-1][j], oi[-1][j + 1], ii[-1][j + 1], ii[-1][j]))


def r_whispering_spring(hi):
    R = Relic(hi)
    q = R.q
    # the basin: a foot, a stem and a bowl, carved stone
    sides = q(20, 160)
    lathe(R.piece("STONE"), [(0, 0.0), (0.5, 0.0), (0.56, 0.05), (0.52, 0.12), (0.34, 0.2), (0.24, 0.34), (0.22, 0.42), (0.36, 0.5),
                             (0.62, 0.62), (0.8, 0.78), (0.9, 0.94), (0.92, 1.0), (0.86, 1.04), (0.78, 0.98), (0.6, 0.86), (0, 0.8)], sides)
    # two rows of carved lotus petals round the bowl
    for row, (n, h0, h1, r0, r1, w, out) in enumerate(((8, 0.5, 1.1, 0.42, 0.97, 0.56, 0.1), (8, 0.46, 0.88, 0.36, 0.8, 0.5, 0.08))):
        for k in range(n):
            a = k * TAU / n + (math.pi / n if row else 0)
            g = R.piece("STONE")
            nu, nv = q(2, 40), q(4, 48)
            outer, inner, mk = [], [], []
            for i in range(nv + 1):
                t = i / nv
                h = lerp(h0, h1, t)
                rr = lerp(r0, r1, t ** 0.8) + out * math.sin(math.pi * t)
                half = max(0.025, w * 0.5 * math.sin(math.pi * min(0.97, 0.12 + t * 0.95)) ** 0.6 * (1 - 0.8 * t ** 3))
                ro, ri, rm = [], [], []
                for j in range(nu + 1):
                    u = (j / nu - 0.5) * 2
                    az = a + u * half / max(rr, 0.2)
                    dirr = V(math.cos(az), math.sin(az), 0)
                    lift = 0.06 * (1 - u * u)
                    p = dirr * (rr + lift) + Z * h
                    ro.append(p + dirr * 0.035)
                    ri.append(p - dirr * 0.06)
                    rm.append(0.0)
                outer.append(ro)
                inner.append(ri)
                mk.append(rm)
            _shell(g, outer, inner, mk)
    # the water: a surface in the bowl, a jet in the middle, a ribbon spiralling up round the pearl
    lathe(R.piece("WATER"), [(0, 0.88), (0.84, 0.88), (0.86, 0.93), (0.6, 0.95), (0.3, 0.96), (0, 0.965)], q(20, 128))
    pc = V(0, 0, 2.05)
    pr = 0.3
    blob(R.core, pc, (pr, pr, pr), nu=18, nv=12)
    R.anchor = pc.copy()
    lathe(R.piece("WATER"), [(0, 0.9), (0.26, 0.9), (0.13, 1.02), (0.085, 1.25), (0.075, 1.55), (0.1, pc.z - pr - 0.04), (0.2, pc.z - pr + 0.04), (0.28, pc.z - pr + 0.1),
                             (0.2, pc.z - pr + 0.11), (0, pc.z - pr + 0.06)], q(8, 40))
    pts = []
    turns = 1.7
    for i in range(14):
        t = i / 13
        a = t * turns * TAU
        rr = 0.22 + 0.42 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.8
        z = 0.94 + t * 2.0
        pts.append(V(math.cos(a) * rr, math.sin(a) * rr, z))
    pts += [pts[-1] + V(-0.12, 0.08, 0.14), pts[-1] + V(-0.12, 0.2, 0.12)]

    def rib(t, th):
        w = 1.0 if t < 0.85 else max(0.15, 1 - (t - 0.85) / 0.15)
        return (math.cos(th) * w, math.sin(th) * 0.32 * (0.5 + 0.5 * w))
    path = tube(R.piece("WATER"), pts, lambda t: 0.16 * (1 - 0.55 * t) + (0.1 * (1 - t / 0.08) if t < 0.08 else 0), sides=q(8, 40), n=q(32, 260), section=rib, up=Z, per=5,
                rfn=(lambda t, th: 1 + 0.03 * math.sin(th * 2 + t * 60)) if hi else None)
    # droplets beading on the ribbon's outer edge
    for tt, s in ((0.3, 0.055), (0.5, 0.045), (0.66, 0.05), (0.8, 0.04)):
        i0 = int(tt * (len(path) - 1))
        p = path[i0]
        o = V(p.x, p.y, 0).normalized()
        blob(R.piece("WATER"), p + o * (0.05 * (1 - 0.5 * tt) + s * 0.55), (s, s, s * 1.15), nu=q(6, 24), nv=q(4, 16))
    return R


def r_ember_heart(hi):
    R = Relic(hi)
    q = R.q
    c = V(0, 0, 1.72)
    W, D = 1.5, 1.0
    tilt = rot(Z, -14) @ rot(Y, 9)
    outer = R.piece("OBSIDIAN", hard=True)
    heart_solid(outer, c, W, D, q(16, 220), q(9, 130), tilt, facets=True)
    inner = Geo()
    heart_solid(inner, c, W * 0.8, D * 0.74, q(12, 140), q(7, 80), tilt)
    heart_solid(R.core, c, W * 0.86, D * 0.8, 12, 8, tilt)
    R.anchor = c.copy()
    # the cracks: walls fanned out from the heart's centre along designed lines (one point of impact on the upper left lobe)
    I = (-0.3, 0.3)
    fronts = (
        (I, (-0.12, 0.08), (0.04, -0.12), (-0.02, -0.34), (0.03, -0.56), (0.0, -0.9)),
        (I, (-0.06, 0.4), (0.1, 0.38), (0.3, 0.5), (0.52, 0.42), (0.9, 0.5)),
        (I, (-0.52, 0.22), (-0.92, 0.3)),
        (I, (-0.42, 0.04), (-0.5, -0.16), (-0.9, -0.24)),
        ((0.04, -0.12), (0.26, -0.06), (0.46, -0.14), (0.9, -0.04)),
        (I, (-0.3, 0.6), (-0.2, 0.95)),
        ((0.115, 0.365), (0.24, 0.22), (0.46, 0.26), (0.62, 0.12), (0.92, 0.18)),
    )
    backs = (((-0.9, 0.1), (-0.3, 0.02), (0.05, 0.12), (0.4, -0.05), (0.9, -0.1)), ((0.05, 0.12), (0.12, -0.3), (-0.02, -0.9)))
    walls = []
    for lines, side in ((fronts, -1), (backs, 1)):
        for k, line in enumerate(lines):
            dirs = [(tilt @ V(x, side * 0.62, z)).normalized() for x, z in line]
            # run each wall a little past its start (by its own amount) so no two walls share a vertex
            ext = 0.12 + 0.035 * k + (0.02 if side > 0 else 0.0)
            dirs = [(dirs[0] + (dirs[0] - dirs[1]) * ext / max(1e-6, (dirs[0] - dirs[1]).length) * 0.12).normalized()] + dirs
            dense = []
            for a, b in zip(dirs, dirs[1:]):
                for t in np.linspace(0, 1, 4, endpoint=False):
                    dense.append(a.slerp(b, t) if hasattr(a, "slerp") else lerp(a, b, t).normalized())
            dense.append(dirs[-1])
            wide = 0.11 if line[0] == I else 0.07
            wg = Geo()
            n = len(dense)
            rings = []
            for i, d in enumerate(dense):
                a = dense[max(0, i - 1)]
                b = dense[min(n - 1, i + 1)]
                nn = d.cross(b - a).normalized()
                w = wide * (1 - 0.6 * i / (n - 1)) / 2
                p0, p1 = c + d * 0.2, c + d * 1.6
                rings.append([p0 - nn * w, p1 - nn * w, p1 + nn * w, p0 + nn * w])
            loft(wg, rings)
            walls.append(wg)
    R.cuts = [(outer, [inner] + walls, "near")]
    # ember chips lodged in the cracks
    chips = R.glow(hexof(GLOW["EmberHeart"]))
    rnd = random.Random(9)
    for (line, side, at) in ((fronts[0], -1, 2), (fronts[1], -1, 3), (fronts[3], -1, 2), (backs[0], 1, 2)):
        x, z = line[at]
        d = (tilt @ V(x, side * 0.62, z)).normalized()
        hit = _ray(outer, c, d)
        if hit is None:
            continue
        ax = (d + V(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3))).normalized()
        crystal(chips, hit - d * 0.15, ax, 0.27, 0.04, sides=4, tip=0.4, seed=rnd.randint(0, 99), foot=0.9)
    return R


def _ray(g, origin, d):
    bvh = BVHTree.FromPolygons([tuple(p) for p in g.co], [list(f) for f in g.faces])
    hit = bvh.ray_cast(Vector(origin), Vector(d))
    return hit[0]


def heart_solid(g, c, W, D, nu, nv, tilt, seed=3, facets=False):
    """A puffed 3D heart: the heart curve inflated."""
    outl = heart_outline(200, asym=0.06)
    cen = V(0, 0.12)
    ang = [math.atan2(p.y - cen.y, p.x - cen.x) for p in outl]
    rad = [(p - cen).length for p in outl]
    order = np.argsort(ang)
    A = np.array(ang)[order]
    Rr = np.array(rad)[order]

    def r_at(a):
        return float(np.interp(a, A, Rr, period=TAU))
    rings = []
    for i in range(nv + 1):
        ph = math.pi * i / nv - math.pi / 2       # -90 (back) .. 90 (front)
        if i in (0, nv):
            rings.append([c + tilt @ V(cen.x * W, (1 if i == nv else -1) * -D * 0.5, cen.y * W)])
            continue
        ring = []
        for j in range(nu):
            a = TAU * j / nu
            rr = r_at(a) * W * math.cos(ph) ** 0.75
            depth = math.sin(ph) * D * 0.5 * (0.75 + 0.25 * r_at(a) / 0.55)
            lump = 1 + 0.035 * noise.noise(V(math.cos(a) * 2, math.sin(a) * 2, ph) + V(seed, 0, 0))
            ring.append(c + tilt @ (V((cen.x + math.cos(a) * rr / W) * W * lump, -depth, (cen.y + math.sin(a) * rr / W) * W * lump)))
        rings.append(ring)
    if facets:
        # knapped: flat conchoidal facets cut into the surface (each a plane a little inside the surface point it is named for)
        rnd = random.Random(seed + 50)
        dirs = []
        for i in range(70):
            zz = rnd.uniform(-1, 1)
            ph = rnd.uniform(0, TAU)
            rr = math.sqrt(1 - zz * zz)
            dirs.append(V(math.cos(ph) * rr, math.sin(ph) * rr, zz))
        pts = [p for r in rings for p in r]
        cc = sum(pts, Vector()) / len(pts)
        ref = []
        for dk in dirs:
            best = max(pts, key=lambda p: (p - cc).normalized().dot(dk))
            ref.append((best - cc).length * 0.988)
        def cut(p):
            v = p - cc
            r0 = v.length
            if r0 < 1e-6:
                return p
            d = v / r0
            k = max(range(len(dirs)), key=lambda i: d.dot(dirs[i]))
            cosk = max(0.3, d.dot(dirs[k]))
            return cc + d * min(r0, ref[k] / cosk)
        rings = [[cut(p) for p in r] for r in rings]
    loft(g, rings)


def r_ashen_sigil(hi):
    R = Relic(hi)
    q = R.q
    tc = V(0, 0, 1.78)
    TR, TT = 1.12, 0.44                      # tablet radius and thickness
    sides = q(20, 256)
    rnd = random.Random(11)
    chips = [(rnd.uniform(0, TAU), rnd.uniform(0.04, 0.09), rnd.uniform(0.18, 0.4)) for _ in range(9)]

    def chip(th):
        d = 0.0
        for a, depth, w in chips:
            x = ((th - a + math.pi) % TAU - math.pi) / w
            if abs(x) < 1:
                d = max(d, depth * (1 - x * x))
        return 1 - d / TR - 0.006 * noise.noise(V(math.cos(th) * 4, math.sin(th) * 4, 0))

    # the stone disc, its axis along Y (front at -Y): a raised outer border, a recessed field, a charred rim
    prof = [(0, -TT / 2 + 0.06), (0.7, -TT / 2 + 0.06), (0.74, -TT / 2 + 0.03), (0.8, -TT / 2), (0.92, -TT / 2), (0.98, -TT / 2 + 0.03), (1.0, -TT / 2 + 0.08),
            (1.0, TT / 2 - 0.08), (0.98, TT / 2 - 0.03), (0.92, TT / 2), (0.8, TT / 2), (0.74, TT / 2 - 0.03), (0.7, TT / 2 - 0.05), (0, TT / 2 - 0.05)]
    if hi:
        prof = _densify(prof, 0.012)
    else:
        prof = prof[:1] + [(0.35, prof[0][1])] + prof[1:-1] + [(0.35, prof[-1][1])] + prof[-1:]
    g = R.piece("ASHSTONE")
    rings = []
    masks = []
    for r, yy in prof:
        if r == 0:
            rings.append([tc + Y * yy])
            masks.append([0.0])
            continue
        ring, mk = [], []
        for j in range(sides):
            th = TAU * j / sides
            rr = r * TR * (chip(th) if r > 0.9 else 1.0)
            p = V(math.cos(th) * rr, 0, math.sin(th) * rr)
            dy = 0.0
            if hi and r < 0.71 and yy < 0:
                dy = 0.02 * glyph_groove(p.x, p.z)
            if hi and r < 0.71 and yy > 0:
                dy = -0.015 * back_groove(p.x, p.z)
            ring.append(tc + p + Y * (yy + dy))
            mk.append(sstep(0.45, 1.0, r))
        rings.append(ring)
        masks.append(mk)
    loft(g, rings, masks=masks)
    # the bronze ring round the rim, riveted, and four clasps over the border
    ring_g = R.piece("BRONZE")
    tube(ring_g, ring_path(tc, Y, TR * 0.985 + 0.03, q(24, 128)), 1.0, sides=q(8, 28), closed=True, per=2, up=Y,
         section=lambda t, th: superellipse(TT * 0.6, 0.075, 4.0)(t, th))
    for k in range(8):
        th = TAU * k / 8 + TAU / 16
        d = V(math.cos(th), 0, math.sin(th))
        blob(R.piece("BRONZE"), tc + d * (TR * 0.985 + 0.1), (0.05, 0.05, 0.05), nu=q(5, 16), nv=q(3, 10),
             frame=Matrix((d, Y, d.cross(Y))).transposed())
    for k in range(4):
        th = math.radians(45 + 90 * k)
        d = V(math.cos(th), 0, math.sin(th))
        t2 = d.cross(Y).normalized()
        for side in (-1,):
            fr = frame_of(tc + d * (TR * 0.86) + Y * side * (TT / 2 - 0.02), Y * side, t2)
            slab(R.piece("BRONZE"), [[V(-0.1, -0.06), V(0.1, -0.06), V(0.08, 0.2), V(-0.08, 0.2)]], 0.06, 0.02, q(1, 4), fr)
    # the cradle foot and the flame finial
    lathe(R.piece("BRONZE"), [(0, 0.0), (0.42, 0.0), (0.46, 0.05), (0.4, 0.1), (0.22, 0.16), (0.14, 0.3), (0.16, 0.42), (0.26, 0.5), (0.3, 0.6), (0, 0.66)],
          q(12, 96))
    # the flame finial on top: a lathed stem and a three-tongue bronze flame
    top = tc + Z * (TR + 0.08)
    lathe(R.piece("BRONZE"), [(0, -0.05), (0.14, -0.05), (0.16, 0.0), (0.1, 0.06), (0.08, 0.12), (0.12, 0.18), (0, 0.22)], q(12, 64), c=top)
    for k, (dx, h, lean) in enumerate(((0.0, 0.46, 0), (-0.09, 0.3, -18), (0.09, 0.32, 18))):
        base = top + Z * 0.16 + X * dx
        d = rot(Y, lean) @ Z
        pts = [base, base + d * h * 0.4 + X * 0.03 * (1 if k != 1 else -1), base + d * h * 0.75 - X * 0.03 * (1 if k != 2 else -1), base + d * h]
        tube(R.piece("BRONZE"), pts, lambda t: 0.075 * math.sin(math.pi * (0.25 + 0.75 * t)) ** 0.6 * (1 - t) + 0.01, sides=q(6, 24), n=q(7, 60),
             section=lambda t, th: (math.cos(th), math.sin(th) * 0.55), up=Y, per=4)
    # the glowing seal on the front field: a ring round three swirling flame tongues and a centre, set into the stone
    face = tc.y - TT / 2 + 0.06
    torus(R.core, tc + Y * (face - 0.006), Y, SEAL["ring"], 1.0, nu=20, nv=4, section=superellipse(0.024, SEAL["ring_w"], 3.0))
    for k in range(3):
        pts = [V(math.cos(a) * rr, 0, math.sin(a) * rr) for a, rr, _ in seal_stroke(k, 6)]
        _flat_stroke(R.core, [tc + p + Y * (face - 0.008) for p in pts], lambda t: seal_width(t), Y, 0.032)
    blob(R.core, tc + Y * (face - 0.004), (SEAL["dot"], 0.03, SEAL["dot"]), nu=6, nv=4)
    for k in range(6):
        a = TAU * k / 6 + math.radians(30)
        p = tc + V(math.cos(a), 0, math.sin(a)) * SEAL["studs"] + Y * (face - 0.004)
        blob(R.glow(hexof(GLOW["AshenSigil"])), p, (0.04, 0.028, 0.04), nu=5, nv=3)
    R.anchor = tc.copy()
    return R


def _densify(prof, step):
    out = [prof[0]]
    for a, b in zip(prof, prof[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        for i in range(1, n + 1):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def glyph_groove(x, z):
    """The carved channel round the seal's inlays (0..1), on the tablet's front field (centred coordinates)."""
    r = math.hypot(x, z)
    d = abs(r - SEAL["ring"]) - SEAL["ring_w"] - 0.025
    for k in range(3):
        pts = seal_stroke(k, 40)
        for i, (a, rr, t) in enumerate(pts):
            d = min(d, math.hypot(x - math.cos(a) * rr, z - math.sin(a) * rr) - seal_width(t) - 0.025)
    d = min(d, r - SEAL["dot"] - 0.025)
    for k in range(6):
        aa = TAU * k / 6 + math.radians(30)
        d = min(d, math.hypot(x - math.cos(aa) * SEAL["studs"], z - math.sin(aa) * SEAL["studs"]) - 0.065)
    return max(0.0, 1 - abs(d) / 0.012) if d > -0.012 else 0.0


SEAL = {"ring": 0.64, "ring_w": 0.045, "r0": 0.15, "r1": 0.5, "sweep": 140, "w": 0.13, "dot": 0.1, "studs": 0.72}


def seal_stroke(k, n):
    """One of the seal's three flame tongues: (angle, radius, t) along it, from the centre outward."""
    a0 = TAU * k / 3 + math.radians(90)
    out = []
    for i in range(n + 1):
        t = i / n
        out.append((a0 + t * math.radians(SEAL["sweep"]), SEAL["r0"] + (SEAL["r1"] - SEAL["r0"]) * t, t))
    return out


def seal_width(t):
    return SEAL["w"] * math.sin(math.pi * min(1.0, 0.3 + t)) ** 0.8 * (1 - 0.8 * t) + 0.015


def back_groove(x, z):
    r = math.hypot(x, z)
    d = min(abs(r - 0.5), abs(r - 0.32), abs(r - 0.12))
    a = math.atan2(z, x)
    if 0.12 < r < 0.5:
        da = abs(((a * 8 / TAU) % 1) - 0.5) * TAU / 8 * r
        d = min(d, da)
    return max(0.0, 1 - d / 0.014)


def _flat_stroke(g, pts, width, normal, thick, n=None):
    """A flat tapered stroke lying on a plane (normal), as a thin closed solid."""
    nrm = Vector(normal).normalized()

    def sec(t, th):
        return (math.cos(th) * thick / max(0.02, width(t)), math.sin(th))
    tube(g, pts, width, sides=6, n=n or len(pts) + 4, section=lambda t, th: sec(t, th), up=nrm, tip0=False, tip1=True, per=3)


def r_caldera_crown(hi):
    R = Relic(hi)
    q = R.q
    bc = V(0, 0, 0.55)
    BR = 0.95
    # the obsidian band: a broad polished ring with a raised rim at top and bottom
    band = R.piece("OBSIDIAN", hard=True)
    tube(band, ring_path(bc, Z, BR, q(24, 160)), 1.0, sides=q(8, 40), closed=True, per=2, up=Z,
         section=superellipse(0.3, 0.12, 5.0), rfn=(lambda t, th: 1 + 0.01 * noise.noise(V(t * 30, th, 0))) if hi else None)
    # basalt columns, sharpened, leaning out; tallest at the front behind the gem
    rnd = random.Random(5)
    n = 9
    tips = R.glow(hexof(GLOW["CalderaCrown"]))
    for k in range(n):
        az = -math.pi / 2 + TAU * k / n
        front = (math.cos(az - (-math.pi / 2)) + 1) / 2          # 1 at the front, 0 at the back
        h = 0.85 + 1.25 * front ** 1.4 + rnd.uniform(-0.1, 0.1)
        rad = 0.2 + 0.06 * front
        d = V(math.cos(az), math.sin(az), 0)
        base = bc + d * (BR - 0.02) + Z * 0.1
        axis = (Z + d * (0.2 + 0.1 * (1 - front))).normalized()
        _column(R.piece("BASALT", hard=True, bevel=0.006), tips, base, axis, h, rad, seed=k + 3, hi=hi, bend=0.18 + 0.1 * (1 - front))
        # a short spur between spikes
        az2 = az + TAU / n / 2
        d2 = V(math.cos(az2), math.sin(az2), 0)
        h2 = 0.42 + 0.4 * ((math.cos(az2 + math.pi / 2) + 1) / 2) ** 1.4
        _column(R.piece("BASALT", hard=True, bevel=0.006), tips, bc + d2 * (BR + 0.01) + Z * 0.12, (Z + d2 * 0.4).normalized(), h2, 0.12, seed=k + 40, hi=hi, bend=0.3)
    # the magma gem at the front, in a rock bezel
    fd = V(0, -1, 0)
    gc = bc + fd * (BR + 0.1) + Z * 0.06
    lathe(R.piece("BASALT", hard=True, bevel=0.005), [(0, -0.08), (0.36, -0.08), (0.42, -0.02), (0.4, 0.06), (0.32, 0.1), (0, 0.08)], q(10, 10), c=gc, axis=fd)
    for k in range(6):
        a = TAU * k / 6 + math.pi / 6
        d = V(math.cos(a), 0, math.sin(a))
        crystal(R.piece("BASALT", hard=True, bevel=0.004), gc + d * 0.34 + fd * 0.03, (d * 0.25 + fd).normalized(), 0.18, 0.06, sides=4, tip=0.5, seed=60 + k)
    blob(R.core, gc + fd * 0.1, (0.27, 0.13, 0.33), nu=8, nv=4)
    R.anchor = bc + Z * 0.7
    return R


def _column(g, tips, base, axis, h, rad, seed, hi, bend=0.22):
    """A volcanic rock spike: six rough facets tapering all the way up and bending outward, red-hot toward the top; its
    glowing lava tip is a separate piece set over the end."""
    rnd = random.Random(seed)
    axis = Vector(axis).normalized()
    out = Vector((axis.x, axis.y, 0))
    out = out.normalized() if out.length > 1e-6 else X
    _, a, b, _ = frame_of(base, axis, out)
    angs = [TAU * j / 5 + rnd.uniform(-0.2, 0.2) for j in range(5)]
    rads = [1 + rnd.uniform(-0.14, 0.14) for _ in range(5)]
    cut = 0.74
    levels = [-0.1, 0.0, 0.3, 0.55, cut] if not hi else list(np.linspace(-0.1, cut, 18))

    def centre(t):
        return base + axis * (h * t) + out * (bend * h * max(0.0, t) ** 2)

    def ring(t):
        s = 1.0 - 0.62 * max(0.0, t) / cut
        tw = 0.25 * t
        return [centre(t) + (a * math.cos(an + tw) + b * math.sin(an + tw)) * rad * s * r for an, r in zip(angs, rads)]
    rings = [ring(t) for t in levels]
    rings.append([centre(cut + 0.03)])
    masks = [[sstep(0.35, cut, t)] * len(r) for t, r in zip(levels + [cut + 0.03], rings)]
    loft(g, rings, masks=masks)
    if not hi:
        t0 = cut - 0.08
        s = (1.0 - 0.62 * t0 / cut) * 1.16
        rr = [centre(t0) + (a * math.cos(an + 0.25 * t0) + b * math.sin(an + 0.25 * t0)) * rad * s * r for an, r in zip(angs, rads)]
        tip = centre(1.0) + (a * rnd.uniform(-1, 1) + b * rnd.uniform(-1, 1)) * rad * 0.08
        mid = [lerp(p, tip, 0.4) for p in rr]
        loft(tips, [rr, mid, [tip]])


def r_moon_mirror(hi):
    R = Relic(hi)
    q = R.q
    mc = V(0, 0, 1.75)
    MR = 0.82
    # the mirror face (the glow) and the silver frame: a moulded ring and a back plate
    lathe(R.core, [(0, -0.035), (MR + 0.02, -0.035), (MR + 0.02, 0.02), (0, 0.02)], 48, c=mc, axis=-Y)
    R.anchor = mc.copy()
    fr = R.piece("SILVER")
    tube(fr, ring_path(mc, Y, MR + 0.06, q(28, 192)), 1.0, sides=q(8, 36), closed=True, per=2, up=Y,
         section=lambda t, th: (0.09 * math.cos(th), 0.085 * math.sin(th) + 0.02 * math.cos(th) ** 2))
    lathe(R.piece("SILVER"), [(0, 0.0), (MR + 0.05, 0.0), (MR + 0.08, 0.05), (MR - 0.05, 0.11), (0.3, 0.14), (0, 0.15)], q(28, 192), c=mc + Y * 0.0, axis=Y,
          mask=(lambda k, th: 0.0))
    # a bead row on the frame's front
    for k in range(16):
        a = TAU * k / 16
        p = mc + V(math.cos(a), 0, math.sin(a)) * (MR + 0.06) - Y * 0.085
        blob(R.piece("SILVER"), p, (0.026, 0.026, 0.026), nu=q(5, 14), nv=q(3, 8))
    # the gold crescent cradling it, thick at the lower left, its horns reaching round
    off = V(-0.85, 0.3).normalized() * 0.34
    Ro, Ri = 1.16, MR + 0.1
    loop = _crescent(Ro, Ri, off, q(26, 160))
    slab(R.piece("GOLD"), [loop], 0.2, 0.05, q(1, 6), (mc + Y * 0.13, X, -Z, -Y))
    # small gold stars on the crescent's horns are left out: the horns end in points
    # the moonstone in a pronged gold setting on top
    top = mc + Z * (MR + 0.18)
    lathe(R.piece("GOLD"), [(0, -0.12), (0.12, -0.12), (0.24, -0.06), (0.27, 0.0), (0.24, 0.04), (0, 0.04)], q(12, 72), c=top + Z * 0.02, axis=-Y)
    sc = top - Y * 0.05 + Z * 0.02
    blob(R.piece("MOONSTONE"), sc, (0.2, 0.11, 0.24), nu=q(12, 64), nv=q(8, 40), frame=None)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        d = V(math.cos(a), 0, math.sin(a))
        p0 = top + Z * 0.02 + d * 0.24 - Y * 0.02
        tube(R.piece("GOLD"), [p0, p0 + d * 0.02 - Y * 0.08, p0 - d * 0.04 - Y * 0.13], 0.022, sides=q(5, 14), n=q(4, 16), up=Y, per=3)
    # a silver finial below
    bot = mc - Z * (MR + 0.12)
    lathe(R.piece("SILVER"), [(0, 0.06), (0.12, 0.06), (0.09, 0.0), (0.05, -0.1), (0.08, -0.16), (0.11, -0.22), (0.08, -0.3), (0.03, -0.36), (0, -0.42)],
          q(12, 64), c=bot, axis=Z)
    blob(R.piece("GOLD"), bot - Z * 0.2, (0.1, 0.1, 0.075), nu=q(10, 40), nv=q(6, 24))
    return R


def _crescent(Ro, Ri, off, n):
    """A crescent outline: inside the outer circle (centred at off) and outside the inner circle (centred at 0)."""
    # the outer circle's arc that lies outside the inner circle, then the inner arc back
    d = off.length
    # intersection angles on each circle
    a = (Ro * Ro - Ri * Ri + d * d) / (2 * d)
    hgt = math.sqrt(max(0.0, Ro * Ro - a * a))
    u = off / d
    pm = off - u * a          # point on the line between centres (from the outer centre toward 0)
    perp = V(-u.y, u.x)
    i1, i2 = pm + perp * hgt, pm - perp * hgt
    ao1 = math.atan2(i1.y - off.y, i1.x - off.x)
    ao2 = math.atan2(i2.y - off.y, i2.x - off.x)
    ai1 = math.atan2(i1.y, i1.x)
    ai2 = math.atan2(i2.y, i2.x)
    pts = []
    # outer arc from i1 to i2 the long way round (through the side away from the inner circle)
    away = math.atan2(u.y, u.x)
    def arc(c, r, a0, a1, through, n):
        # choose direction so the arc passes `through`
        span = (a1 - a0) % TAU
        mid = a0 + span / 2
        if math.cos(mid - through) < 0:
            span = span - TAU
        return [c + V(math.cos(a0 + span * k / n), math.sin(a0 + span * k / n)) * r for k in range(n + 1)]
    outer = arc(off, Ro, ao1, ao2, away, n)
    inner = arc(V(0, 0), Ri, ai2, ai1, away, n)
    pts = outer[:-1] + inner[:-1]
    return pts


def r_star_well(hi):
    R = Relic(hi)
    q = R.q
    sides = q(24, 192)
    # the well: a marble plinth, a ring of marble blocks, a gold band at the foot and a gold lip
    lathe(R.piece("MARBLE"), [(0, 0.0), (0.98, 0.0), (1.02, 0.04), (1.0, 0.1), (0.92, 0.14), (0, 0.14)], q(20, 192))
    rnd = random.Random(3)
    courses = ((0.12, 0.42), (0.42, 0.72))
    for ci, (z0, z1) in enumerate(courses):
        nb = 6
        for k in range(nb):
            a0 = TAU * k / nb + (math.pi / nb if ci else 0) + 0.012
            a1 = TAU * (k + 1) / nb + (math.pi / nb if ci else 0) - 0.012
            _block_arc(R.piece("MARBLE", hard=True), 0.6, 0.86 + rnd.uniform(-0.01, 0.01), z0 + 0.006, z1 - 0.006, a0, a1, q(2, 24), q(1, 5), hi)
    # a core ring behind the blocks so the well is solid where the blocks part
    lathe(R.piece("MARBLE"), [(0.58, 0.1), (0.84, 0.1), (0.84, 0.76), (0.58, 0.76)], q(16, 128))
    torus(R.piece("GOLD"), V(0, 0, 0.8), Z, 0.73, 1.0, nu=q(20, 192), nv=q(6, 28), section=superellipse(0.08, 0.17, 3.0))
    torus(R.piece("GOLD"), V(0, 0, 0.13), Z, 0.89, 1.0, nu=q(24, 192), nv=q(4, 20), section=superellipse(0.03, 0.03, 2.5))
    # the starlight brimming in the well
    g = R.glow(hexof(GLOW["StarWell"]))
    lathe(g, [(0, 0.78), (0.64, 0.78), (0.64, 0.83), (0.4, 0.845), (0, 0.85)], 24)
    # the star: a chunky four-point sparkle, concave sides, ridged front and back
    sc = V(0, 0, 2.3)
    tilt = rot(Y, 10)
    pts, tips = [], []
    per_pt = 6
    for i in range(8 * per_pt):
        a = TAU * i / (8 * per_pt) + math.pi / 2
        k = (i % per_pt) / per_pt
        arm = (i // per_pt)
        L = 0.92 if arm in (0, 4) else (0.7 if arm in (2, 6) else 0.3)
        f = abs(math.cos(math.pi * k))
        rr = 0.19 + (L - 0.19) * f ** 4.5
        pts.append(sc + tilt @ V(math.cos(a) * rr, 0, math.sin(a) * rr))
        if k == 0 and arm in (0, 2, 4, 6):
            tips.append(pts[-1])
    loft(R.core, [[sc + tilt @ V(0, -0.24, 0)], [sc + (p - sc) * 0.4 + tilt @ V(0, -0.13, 0) for p in pts], pts,
                  [sc + (p - sc) * 0.4 + tilt @ V(0, 0.13, 0) for p in pts], [sc + tilt @ V(0, 0.24, 0)]])
    R.anchor = sc.copy()
    # a slender gold arch over the well, like a well's frame; the star's side points are set into it
    left, right = tips[1], tips[3]
    if left.x > right.x:
        left, right = right, left
    arch = [V(-0.72, 0, 0.84), V(-0.8, 0, 1.5), lerp(sc, left, 0.95), V(-0.52, 0, 3.02), V(0, 0, 3.34), V(0.52, 0, 3.02), lerp(sc, right, 0.95),
            V(0.8, 0, 1.5), V(0.72, 0, 0.84)]
    tube(R.piece("GOLD"), arch, lambda t: 0.06 + 0.015 * math.cos(math.pi * (t - 0.5)) ** 8, sides=q(6, 20), n=q(26, 200), tip0=False, tip1=False, up=Y, per=6)
    for sx in (-1, 1):
        blob(R.piece("GOLD"), V(sx * 0.72, 0, 0.9), (0.08, 0.08, 0.06), nu=q(6, 24), nv=q(4, 12))
    blob(R.piece("GOLD"), V(0, 0, 3.4), (0.09, 0.09, 0.09), nu=q(6, 24), nv=q(4, 12))
    return R


def _block_arc(g, r0, r1, z0, z1, a0, a1, nu, nb, hi):
    """A curved marble block of the well ring, with chamfered edges."""
    b = 0.018
    prof = [(r0, z0 + b), (r0 + b, z0), (r1 - b, z0), (r1, z0 + b), (r1, z1 - b), (r1 - b, z1), (r0 + b, z1), (r0, z1 - b)]
    if hi:
        prof2 = []
        for (ra, za), (rb, zb) in zip(prof, prof[1:] + prof[:1]):
            for t in np.linspace(0, 1, 4, endpoint=False):
                prof2.append((ra + (rb - ra) * t, za + (zb - za) * t))
        prof = prof2
    rings = []
    for i in range(nu + 1):
        t = i / nu
        a = lerp(a0, a1, t)
        e = 1.0
        ring = []
        for r, z in prof:
            pull = 0.0
            if i == 0 or i == nu:
                pull = 0.0
            ring.append(V(math.cos(a) * r, math.sin(a) * r, z))
        rings.append(ring)
    # close the ends with a chamfer: shrink the end rings slightly
    def shrink(ring, s):
        c = sum(ring, Vector()) / len(ring)
        return [c + (p - c) * s for p in ring]
    da = (a1 - a0) * 0.02
    ra = [V(math.cos(a0 - da) * p.length * 1.0, 0, 0) for p in rings[0]]
    rings = [shrink(rings[0], 0.9)] + rings + [shrink(rings[-1], 0.9)]
    loft(g, rings)


def r_origin_altar(hi):
    R = Relic(hi)
    q = R.q
    rnd = random.Random(21)
    glow = R.glow(hexof(GLOW["OriginAltar"]))
    # the cracked slate floor, with void light in two cracks
    def floor_r(k, th):
        return 1 + 0.035 * noise.noise(V(math.cos(th) * 3, math.sin(th) * 3, 0))
    lathe(R.piece("SLATE", hard=True), [(0, 0.0), (1.85, 0.0), (1.9, 0.04), (1.86, 0.11), (0, 0.11)], q(20, 128), rfn=floor_r)
    for k, az in enumerate((-60, 150)):
        pts = []
        for i in range(7):
            t = i / 6
            a = math.radians(az + 14 * math.sin(t * 7 + k) + 6 * t)
            r = 1.3 + 0.5 * t
            pts.append(V(math.cos(a) * r, math.sin(a) * r, 0.105))
        _flat_stroke(glow, pts, lambda t: 0.035 * (1 - 0.7 * t) + 0.008, Z, 0.02)
    # the stepped octagonal dais
    for i, (ap, z0, z1) in enumerate(((1.18, 0.09, 0.34), (0.9, 0.33, 0.58), (0.64, 0.57, 0.82))):
        r = ap / math.cos(math.pi / 8)
        loop = [V(math.cos(TAU * k / 8 + math.pi / 8) * r, math.sin(TAU * k / 8 + math.pi / 8) * r) for k in range(8)]
        slab(R.piece("OBSIDIAN", hard=True), [loop], z1 - z0, 0.035, q(1, 4), (V(0, 0, z0), X, Y, Z))
    # the spiral sigil inlaid on the top, rising into a vortex at its centre
    top = 0.82
    pts = []
    for i in range(26):
        t = i / 25
        a = t * TAU * 2.2
        rr = 0.52 * (1 - t) + 0.07
        pts.append(V(math.cos(a) * rr, math.sin(a) * rr, top - 0.006))
    _flat_stroke(R.core, pts, lambda t: 0.075 * (1 - 0.45 * t) + 0.015, Z, 0.026, n=48)
    vort = []
    for i in range(16):
        t = i / 15
        a = -t * TAU * 1.7
        rr = 0.05 + 0.34 * t ** 1.2
        vort.append(V(math.cos(a) * rr, math.sin(a) * rr, top - 0.03 + t * 1.15))
    tube(R.core, vort, lambda t: 0.11 * (1 - t) ** 0.8 + 0.02, sides=6, n=36, section=lambda t, th: (math.cos(th) * 0.55, math.sin(th)), up=Z, tip0=False, tip1=True, per=3)
    R.anchor = V(0, 0, 1.2)
    # seven leaning slabs, open wide toward the front (-Y); one snapped, its top fallen on the floor
    kinds = (0, 2, 1, 3, 4, 0, 2)
    n = 7
    for k in range(n):
        az = math.radians(-90 + 52 + (360 - 104) * k / (n - 1))
        front = (math.cos(az + math.pi / 2) + 1) / 2
        h = 1.7 + 1.05 * (1 - front) + rnd.uniform(-0.1, 0.1)
        snapped = (k == 5)
        d = V(math.cos(az), math.sin(az), 0)
        base = d * 1.48
        lean = math.radians(rnd.uniform(11, 18))
        up = (Z * math.cos(lean) + d * math.sin(lean)).normalized()
        out = (d - up * d.dot(up)).normalized()
        side = up.cross(out).normalized()
        w, t = 0.7, 0.26
        hh = h * (0.5 if snapped else 1.0)
        _monolith(R.piece("OBSIDIAN", hard=True, bevel=0.008), base - up * 0.04, up, d, side, hh, w, t, rnd, snapped, hi)
        for m in range(2 if (h > 2.2 and not snapped) else 1):
            zc = 0.62 + m * 0.7
            tt = t * (1 - 0.18 * zc / hh) / 2
            c = base - up * 0.04 + up * zc - out * tt
            _mark(glow, c, -out, side, up, kinds[(k + m * 3) % 5], 0.22)
        if snapped:
            fb = d.normalized() * 1.72 + side * 0.2
            fup = (side * 0.95 + Z * 0.05).normalized()
            fout = Z
            _monolith(R.piece("OBSIDIAN", hard=True, bevel=0.008), V(fb.x, fb.y, 0.1) + Z * (t / 2 - 0.03) - fup * 0.45, fup, fout, None, h * 0.42, w * 0.9, t, rnd, True, hi,
                      broken_bottom=True)
    return R


def _monolith(g, base, up, out, side, h, w, t, rnd, snapped, hi, broken_bottom=False):
    """A tapered standing slab with chamfered edges: its faces flat, its top broken on a slant (jagged when snapped)."""
    out = (Vector(out) - up * Vector(out).dot(up)).normalized()
    side = up.cross(out).normalized()
    levels = [0.0, 0.4, 0.75, 1.0] if not hi else list(np.linspace(0, 1, 18))
    slant = rnd.uniform(0.18, 0.32) * (1 if rnd.random() > 0.5 else -1)
    peaks = [rnd.uniform(-0.08, 0.08) for _ in range(8)]
    wob = [rnd.uniform(-0.03, 0.03) for _ in range(4)]
    ch = 0.045
    shape = ((-1, -1 + ch / t * 2), (-1 + ch / w * 2, -1), (1 - ch / w * 2, -1), (1, -1 + ch / t * 2),
             (1, 1 - ch / t * 2), (1 - ch / w * 2, 1), (-1 + ch / w * 2, 1), (-1, 1 - ch / t * 2))
    rings = []
    for lv in levels:
        ww = w * (1 - 0.32 * lv) / 2 * (1 + float(np.interp(lv, [0, 0.4, 0.75, 1.0], wob)))
        tt = t * (1 - 0.18 * lv) / 2
        ring = []
        for j, (sx, sy) in enumerate(shape):
            zz = h * lv
            if lv == 1.0:
                zz = h * (1 - abs(slant) * 0.5) + slant * sx * w * 0.5 + (peaks[j] * (2.5 if snapped else 1.0))
            ring.append(base + up * zz + side * sx * ww + out * sy * tt)
        rings.append(ring)
    if broken_bottom:
        rings[0] = [p + up * rnd.uniform(-0.05, 0.05) for p in rings[0]]
    loft(g, rings)


def _mark(g, c, nrm, side, up, kind, s):
    """An abstract carved mark (no letters): a ring, a diamond, a chevron pair, three dots, a triangle; cut flat, set into
    the face (its back sunk 1 cm, its front 6 mm proud)."""
    nrm = Vector(nrm).normalized()
    fr = (Vector(c) - nrm * 0.01, Vector(side), Vector(up), nrm)

    def circ(r, n=12, ph=0.0):
        return [V(math.cos(TAU * i / n + ph) * r, math.sin(TAU * i / n + ph) * r) for i in range(n)]
    dep = 0.016
    if kind == 0:
        slab(g, [circ(0.55 * s), circ(0.3 * s)], dep, 0, 0, fr)
    elif kind == 1:
        slab(g, [circ(0.62 * s, 4, math.pi / 2), circ(0.3 * s, 4, math.pi / 2)], dep, 0, 0, fr)
    elif kind == 2:
        for oy in (-0.32, 0.32):
            pts = [V(-0.6, -0.2 + oy), V(0, 0.3 + oy), V(0.6, -0.2 + oy), V(0.6, 0.05 + oy), V(0, 0.55 + oy), V(-0.6, 0.05 + oy)]
            slab(g, [[p * s for p in pts]], dep, 0, 0, fr)
    elif kind == 3:
        for x, y in ((-0.42, -0.3), (0.42, -0.3), (0.0, 0.42)):
            slab(g, [[p + V(x, y) * s for p in circ(0.2 * s, 6)]], dep, 0, 0, fr)
    else:
        slab(g, [circ(0.62 * s, 3, math.pi / 2), circ(0.28 * s, 3, math.pi / 2)], dep, 0, 0, fr)


def _flat_stroke_closed(g, pts, w, nrm, thick):
    tube(g, pts, 1.0, sides=6, closed=True, per=2, up=nrm, section=superellipse(thick, w, 2.5))


def r_void_shard(hi):
    R = Relic(hi)
    q = R.q
    rnd = random.Random(31)
    axis = (rot(Y, 7) @ rot(X, -3) @ Z).normalized()
    base = V(0, 0, 0.62)
    _, ax_x, ax_y, _ = frame_of(base, axis, X)
    # the main shard: an irregular seven-sided crystal, double-ended
    main = R.piece("VOIDGLASS", hard=True, bevel=0.005)
    sides = 7
    angs = [TAU * j / sides + rnd.uniform(-0.2, 0.2) for j in range(sides)]
    rads = [1 + rnd.uniform(-0.2, 0.14) for _ in range(sides)]
    levels = ((0.0, 0.74), (0.35, 1.0), (0.85, 0.92), (1.3, 1.06), (1.85, 0.88), (2.3, 0.7))
    rings = [[base - axis * 0.55 + ax_x * 0.04]]
    for h, s in levels:
        jit = [1 + rnd.uniform(-0.1, 0.1) for _ in range(sides)]
        rings.append([base + axis * h + (ax_x * math.cos(a) + ax_y * math.sin(a)) * 0.43 * r * s * j for a, r, j in zip(angs, rads, jit)])
    rings.append([base + axis * 3.0 + ax_x * 0.07 - ax_y * 0.05])
    loft(main, rings)
    # two smaller shards grown from its foot
    # a twin point breaking from the upper body, leaning off to one side
    crystal(R.piece("VOIDGLASS", hard=True, bevel=0.004), base + axis * 1.75 + ax_x * 0.12, (axis + ax_x * 0.55).normalized(), 0.95, 0.19, sides=5, tip=0.4,
            seed=77, base_tip=True, base_len=0.5, jitter=0.2)
    for k, (az, lean, ln, rr) in enumerate(((140, 36, 1.15, 0.21), (-30, 46, 0.85, 0.17), (240, 52, 0.62, 0.13))):
        d = (ax_x * math.cos(math.radians(az)) + ax_y * math.sin(math.radians(az)))
        a2 = (axis * math.cos(math.radians(lean)) + d * math.sin(math.radians(lean))).normalized()
        crystal(R.piece("VOIDGLASS", hard=True, bevel=0.004), base + axis * 0.05 + d * 0.12, a2, ln, rr, sides=5, tip=0.35, seed=40 + k, base_tip=True, base_len=0.35)
    # the violet core inside, shown by the fissure
    crystal(R.core, base + axis * 0.55, axis, 2.0, 0.2, sides=6, tip=0.25, seed=5, base_tip=True, base_len=0.2, jitter=0.08)
    R.anchor = base + axis * 1.35
    # the fissure: a zig-zag wedge cut across the front, wide at the surface, narrow at the core
    path2 = [(-0.62, 0.55), (-0.2, 0.82), (-0.1, 1.08), (0.1, 1.24), (0.04, 1.5), (0.26, 1.72), (0.2, 1.96), (0.62, 2.26)]
    cut = Geo()
    rings = []
    n = len(path2)
    for i, (x, h) in enumerate(path2):
        a = V(*path2[max(0, i - 1)])
        b = V(*path2[min(n - 1, i + 1)])
        t2 = (b - a).normalized()
        nn = V(-t2.y, t2.x)
        w = 0.07 + 0.12 * math.sin(math.pi * i / (n - 1)) ** 0.8
        fwd = (-Y - axis * (-Y).dot(axis)).normalized()
        sidev = axis.cross(fwd).normalized()

        def P(xx, hh, depth):
            return base + sidev * xx + axis * hh + fwd * depth
        rings.append([P(x - nn.x * w, h - nn.y * w, 0.9), P(x + nn.x * w, h + nn.y * w, 0.9),
                      P(x + nn.x * w * 0.3, h + nn.y * w * 0.3, 0.1), P(x - nn.x * w * 0.3, h - nn.y * w * 0.3, 0.1)])
    loft(cut, rings)
    R.cuts = [(main, [cut], "near")]
    # two gold chains bound round the shard
    bvh = BVHTree.FromPolygons([tuple(p) for p in main.co], [list(f) for f in main.faces])
    for k, (h, tx, ty) in enumerate(((0.95, 14, -6), (2.05, -12, 8))):
        cc = base + axis * h
        nrm = (rot(ax_x, tx) @ rot(ax_y, ty) @ axis).normalized()
        _, u, v, _ = frame_of(cc, nrm, ax_x)
        pts = []
        for i in range(28):
            th = TAU * i / 28
            d = u * math.cos(th) + v * math.sin(th)
            hit = bvh.ray_cast(cc + d * 1.5, -d)
            r = (hit[0] - cc).length if hit[0] is not None else 0.4
            pts.append(cc + d * r)
        _chain(R, pts, nrm, cc, hi)
    return R


def _chain(R, pts, nrm, cc, hi):
    """Gold links round a closed loop of surface points: alternately flat on the surface and standing up from it."""
    q = R.q
    loop = catmull(list(pts) + list(pts[:3]), 4)[4:4 * (len(pts) + 1) + 1]
    L = sum((loop[(i + 1) % len(loop)] - loop[i]).length for i in range(len(loop)))
    n = max(8, int(round(L / 0.16)))
    if n % 2:
        n += 1
    cum = [0.0]
    for i in range(len(loop)):
        cum.append(cum[-1] + (loop[(i + 1) % len(loop)] - loop[i]).length)
    LL, WW, wr = 0.21, 0.11, 0.019
    for k in range(n):
        s = L * k / n
        j = max(0, min(len(loop) - 1, int(np.searchsorted(cum, s)) - 1))
        p = loop[j]
        T = (loop[(j + 1) % len(loop)] - loop[j - 1]).normalized()
        out = (p - cc)
        out = (out - nrm * out.dot(nrm)).normalized()
        B = T.cross(out).normalized()
        if k % 2 == 0:
            ctr, U = p + out * (wr * 0.4), B
        else:
            ctr, U = p + out * (WW / 2 - wr * 1.3), out
        ring = [ctr + T * math.cos(a) * LL / 2 + U * math.sin(a) * WW / 2 for a in np.linspace(0, TAU, q(8, 36), endpoint=False)]
        tube(R.piece("GOLD"), ring, wr, sides=q(3, 12), closed=True, per=1 if not hi else 2, up=U.cross(T))


BUILDERS = {
    "IslandRoot": r_island_root, "GroveHeart": r_grove_heart, "JadeSeed": r_jade_seed, "WhisperingSpring": r_whispering_spring,
    "EmberHeart": r_ember_heart, "AshenSigil": r_ashen_sigil, "CalderaCrown": r_caldera_crown, "MoonMirror": r_moon_mirror,
    "StarWell": r_star_well, "OriginAltar": r_origin_altar, "VoidShard": r_void_shard,
}


# =====================================================================================================================
# materials of the high model: each surface its own (bark, jade, stone, obsidian, metals, marble, water...)
# =====================================================================================================================
class NT:
    """Writes a material's node graph as expressions. Colours are given in sRGB 0..1."""

    def __init__(self, name):
        m = bpy.data.materials.new(name)
        if m.node_tree is None:
            m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.b = next(n for n in self.t.nodes if n.type == "BSDF_PRINCIPLED")
        self._tp = None
        self._geo = None
        self._mask = None

    def n(self, kind, **kw):
        nd = self.t.nodes.new(kind)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            if len(v) == 3 and getattr(sock, "type", "") == "RGBA":
                v = (*lin(v), 1.0)
            elif len(v) == 3 and getattr(sock, "type", "") == "VECTOR":
                pass
            sock.default_value = v
        else:
            self.t.links.new(v, sock)

    @property
    def tp(self):
        if self._tp is None:
            self._tp = self.n("ShaderNodeAttribute", attribute_name="tp").outputs["Vector"]
        return self._tp

    @property
    def mask(self):
        if self._mask is None:
            self._mask = self.n("ShaderNodeAttribute", attribute_name="mask").outputs["Fac"]
        return self._mask

    def geo(self, out):
        if self._geo is None:
            self._geo = self.n("ShaderNodeNewGeometry")
        return self._geo.outputs[out]

    def vmul(self, v, s):
        nd = self.n("ShaderNodeVectorMath", operation="MULTIPLY")
        self._in(nd.inputs[0], v)
        nd.inputs[1].default_value = s
        return nd.outputs[0]

    def noise(self, v, scale, detail=3.0, rough=0.55, dist=0.0):
        nd = self.n("ShaderNodeTexNoise")
        self._in(nd.inputs["Vector"], v)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        nd.inputs["Distortion"].default_value = dist
        return nd.outputs["Fac"]

    def voronoi(self, v, scale, feature="F1", out="Distance", rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        self._in(nd.inputs["Vector"], v)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Randomness"].default_value = rand
        return nd.outputs[out]

    def wave(self, v, scale, dist=6.0, detail=3.0, kind="BANDS", direction="X"):
        nd = self.n("ShaderNodeTexWave", wave_type=kind)
        try:
            nd.bands_direction = direction
        except Exception:
            pass
        self._in(nd.inputs["Vector"], v)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Distortion"].default_value = dist
        nd.inputs["Detail"].default_value = detail
        return nd.outputs["Fac"]

    def math(self, op, a, b=0.0, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(nd.inputs[0], a)
        self._in(nd.inputs[1], b)
        return nd.outputs[0]

    def add(self, a, b):
        return self.math("ADD", a, b)

    def mul(self, a, b):
        return self.math("MULTIPLY", a, b)

    def ridged(self, x):
        return self.math("SUBTRACT", 1.0, self.math("ABSOLUTE", self.math("SUBTRACT", self.mul(x, 2.0), 1.0)))

    def ramp(self, x, a, b):
        nd = self.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        self._in(nd.inputs["Value"], x)
        nd.inputs["From Min"].default_value = a
        nd.inputs["From Max"].default_value = b
        return nd.outputs["Result"]

    def lerpf(self, x, a, b):
        nd = self.n("ShaderNodeMapRange")
        self._in(nd.inputs["Value"], x)
        nd.inputs["To Min"].default_value = a
        nd.inputs["To Max"].default_value = b
        return nd.outputs["Result"]

    def mix(self, a, b, f):
        nd = self.n("ShaderNodeMix", data_type="RGBA")
        self._in(nd.inputs[0], f)
        self._in(nd.inputs[6], a)
        self._in(nd.inputs[7], b)
        return nd.outputs[2]

    def out(self, col, rough, metal=0.0, height=None, strength=0.3, dist=0.004, coat=0.0):
        passc = self.n("ShaderNodeMix", data_type="RGBA", name="COL")
        passc.name = "COL"
        passc.inputs[0].default_value = 0.0
        self._in(passc.inputs[6], col)
        self._in(self.b.inputs["Base Color"], passc.outputs[2])
        self._in(self.b.inputs["Emission Color"], passc.outputs[2])
        self.b.inputs["Emission Strength"].default_value = 0.0
        self._in(self.b.inputs["Roughness"], rough)
        met = self.n("ShaderNodeMath", operation="ADD")
        met.name = "MET"
        self._in(met.inputs[0], metal)
        met.inputs[1].default_value = 0.0
        self.t.links.new(met.outputs[0], self.b.inputs["Metallic"])
        if coat:
            self.b.inputs["Coat Weight"].default_value = coat
        if height is not None:
            bump = self.n("ShaderNodeBump")
            bump.inputs["Strength"].default_value = strength
            bump.inputs["Distance"].default_value = dist
            self._in(bump.inputs["Height"], height)
            self.t.links.new(bump.outputs["Normal"], self.b.inputs["Normal"])
        return self.m


def make_materials():
    M = {}
    # bark: deep ridges running along the root, pale ridge tops, lichen in patches
    m = NT("R_Bark")
    ridge = m.ridged(m.noise(m.vmul(m.tp, (5.0, 5.0, 0.8)), 1.0, 3.0, 0.5, 0.4))
    fine = m.noise(m.vmul(m.tp, (40.0, 40.0, 12.0)), 1.0, 4.0)
    crev = m.ramp(ridge, 0.45, 0.78)
    col = m.mix((0.03, 0.016, 0.009), (0.24, 0.14, 0.07), crev)
    col = m.mix(col, (0.46, 0.32, 0.18), m.ramp(ridge, 0.85, 0.98))
    col = m.mix(col, (0.36, 0.33, 0.2), m.mul(m.ramp(m.noise(m.tp, 2.2, 2.0), 0.6, 0.7), 0.45))
    M["BARK"] = m.out(col, m.lerpf(crev, 0.95, 0.74), 0.0, m.add(ridge, m.mul(fine, 0.3)), 0.9, 0.014)
    # gold leaf: warm gold, faint palmate veins
    m = NT("R_GoldLeaf")
    vein = m.ramp(m.voronoi(m.vmul(m.tp, (1, 1, 1)), 30.0, "DISTANCE_TO_EDGE"), 0.0, 0.06)
    col = m.mix((0.78, 0.5, 0.16), (1.0, 0.8, 0.38), vein)
    M["GOLDLEAF"] = m.out(col, m.lerpf(vein, 0.45, 0.28), 1.0, vein, 0.15, 0.002)
    # living vine: green-brown, fine lengthwise grain, lighter nodes
    m = NT("R_Vine")
    grain = m.noise(m.vmul(m.tp, (14.0, 14.0, 1.5)), 1.0, 3.0)
    col = m.mix((0.12, 0.16, 0.05), (0.33, 0.4, 0.13), m.ramp(grain, 0.4, 0.7))
    col = m.mix(col, (0.3, 0.2, 0.09), m.mul(m.ramp(m.noise(m.tp, 3.0), 0.55, 0.7), 0.6))
    M["VINE"] = m.out(col, 0.62, 0.0, grain, 0.35, 0.006)
    # moss: soft, fuzzy, matte
    m = NT("R_Moss")
    fz = m.noise(m.tp, 90.0, 4.0, 0.7)
    col = m.mix((0.06, 0.2, 0.03), (0.3, 0.5, 0.08), m.ramp(m.noise(m.tp, 8.0, 3.0), 0.35, 0.7))
    col = m.mix(col, (0.45, 0.6, 0.15), m.mul(m.ramp(fz, 0.6, 0.8), 0.6))
    M["MOSS"] = m.out(col, 0.97, 0.0, fz, 0.9, 0.006)
    # leaf: fresh green, lighter toward the tip
    m = NT("R_Leaf")
    sep = m.n("ShaderNodeSeparateXYZ")
    m._in(sep.inputs[0], m.tp)
    along = m.ramp(sep.outputs["Z"], 0.0, 0.25)
    col = m.mix((0.07, 0.3, 0.06), (0.34, 0.64, 0.14), along)
    M["LEAF"] = m.out(col, 0.45, 0.0, m.noise(m.tp, 60.0), 0.08, 0.002)
    # mossy stone (Grove Heart's foot)
    m = NT("R_Stone")
    nz = m.n("ShaderNodeSeparateXYZ")
    m._in(nz.inputs[0], m.geo("Normal"))
    top = m.ramp(nz.outputs["Z"], 0.45, 0.8)
    col = m.mix((0.2, 0.21, 0.19), (0.42, 0.42, 0.38), m.ramp(m.noise(m.tp, 6.0, 4.0), 0.3, 0.7))
    col = m.mix(col, (0.18, 0.36, 0.08), m.mul(top, m.ramp(m.noise(m.tp, 4.0, 3.0), 0.4, 0.55)))
    M["STONE"] = m.out(col, 0.9, 0.0, m.noise(m.tp, 22.0, 5.0), 0.5, 0.008)
    # jade: deep green clouded with paler jade, polished; carved grooves dark and duller
    m = NT("R_Jade")
    cl = m.noise(m.tp, 3.5, 5.0, 0.6, 0.3)
    col = m.mix((0.04, 0.33, 0.17), (0.36, 0.72, 0.48), m.ramp(cl, 0.4, 0.72))
    col = m.mix(col, (0.62, 0.86, 0.66), m.mul(m.ramp(m.noise(m.tp, 9.0, 3.0), 0.66, 0.78), 0.5))
    col = m.mix(col, (0.02, 0.14, 0.07), m.mask)
    M["JADE"] = m.out(col, m.lerpf(m.mask, 0.14, 0.42), 0.0, m.mul(m.mask, -1.0), 0.4, 0.01)
    # gold
    m = NT("R_Gold")
    pt = m.ramp(m.geo("Pointiness"), 0.42, 0.58)
    col = m.mix((0.62, 0.38, 0.1), (1.0, 0.77, 0.34), pt)
    col = m.mix(col, (1.0, 0.88, 0.55), m.mul(m.ramp(m.geo("Pointiness"), 0.56, 0.66), 0.6))
    M["GOLD"] = m.out(col, m.lerpf(m.noise(m.tp, 12.0), 0.18, 0.34), 1.0, m.noise(m.tp, 120.0), 0.04, 0.001)
    # a young sprout
    m = NT("R_Sprout")
    col = m.mix((0.18, 0.5, 0.06), (0.55, 0.85, 0.2), m.ramp(m.noise(m.tp, 5.0), 0.4, 0.7))
    M["SPROUT"] = m.out(col, 0.42, 0.0, m.noise(m.tp, 50.0), 0.06, 0.002)
    # carved limestone (the lotus basin): pale and warm, a blue-green patina in the hollows
    m = NT("R_Limestone")
    cav = m.ramp(m.geo("Pointiness"), 0.52, 0.42)
    col = m.mix((0.55, 0.53, 0.48), (0.78, 0.76, 0.7), m.ramp(m.noise(m.tp, 5.0, 4.0), 0.3, 0.7))
    col = m.mix(col, (0.22, 0.42, 0.38), m.mul(cav, 0.85))
    col = m.mix(col, (0.9, 0.89, 0.84), m.mul(m.ramp(m.geo("Pointiness"), 0.56, 0.66), 0.7))
    M["LIMESTONE"] = m.out(col, 0.78, 0.0, m.noise(m.tp, 30.0, 5.0), 0.35, 0.006)
    # water: clear teal, pale where it thins at the edges, glassy
    m = NT("R_Water")
    edge = m.ramp(m.geo("Pointiness"), 0.5, 0.62)
    col = m.mix((0.0, 0.42, 0.44), (0.1, 0.62, 0.62), m.ramp(m.noise(m.vmul(m.tp, (3.0, 3.0, 0.6)), 2.0, 2.0), 0.35, 0.65))
    col = m.mix(col, (0.62, 0.95, 0.9), edge)
    M["WATER"] = m.out(col, 0.04, 0.0, m.noise(m.vmul(m.tp, (6, 6, 1)), 4.0), 0.12, 0.01, coat=0.0)
    # obsidian: black glass with conchoidal ripples; heat creeps out of the cracks (mask)
    m = NT("R_Obsidian")
    rip = m.voronoi(m.tp, 6.0, "SMOOTH_F1")
    col = m.mix((0.016, 0.014, 0.018), (0.075, 0.07, 0.085), m.ramp(rip, 0.25, 0.6))
    heat = m.mask
    col = m.mix(col, (0.16, 0.03, 0.01), m.ramp(heat, 0.05, 0.4))
    col = m.mix(col, (0.62, 0.14, 0.02), m.ramp(heat, 0.6, 0.95))
    M["OBSIDIAN"] = m.out(col, m.lerpf(heat, 0.1, 0.55), 0.0, rip, 0.35, 0.01)
    # basalt: dark porous rock, grey on its edges, red-hot toward the tips (mask)
    m = NT("R_Basalt")
    pores = m.ramp(m.voronoi(m.tp, 60.0, "F1"), 0.05, 0.25)
    col = m.mix((0.03, 0.028, 0.027), (0.1, 0.095, 0.09), m.ramp(m.noise(m.tp, 10.0, 4.0), 0.3, 0.7))
    col = m.mix(col, (0.24, 0.22, 0.2), m.mul(m.ramp(m.geo("Pointiness"), 0.53, 0.62), 0.8))
    col = m.mix(col, (0.5, 0.1, 0.02), m.ramp(m.mask, 0.3, 1.0))
    M["BASALT"] = m.out(col, 0.88, 0.0, m.add(pores, m.mul(m.noise(m.tp, 20.0, 5.0), 0.4)), 0.6, 0.008)
    # ash stone: pale ash grey, cracked, charred black toward the rim (mask) with ember specks
    m = NT("R_AshStone")
    cr = m.ramp(m.voronoi(m.tp, 2.2, "DISTANCE_TO_EDGE"), 0.0, 0.018)
    col = m.mix((0.33, 0.32, 0.3), (0.55, 0.54, 0.51), m.ramp(m.noise(m.tp, 6.0, 5.0), 0.3, 0.7))
    col = m.mix(col, (0.24, 0.23, 0.22), m.mul(m.ramp(m.noise(m.tp, 1.5, 3.0), 0.5, 0.7), 0.6))
    col = m.mix((0.1, 0.09, 0.085), col, cr)
    char = m.ramp(m.add(m.mul(m.mask, 1.1), m.mul(m.noise(m.tp, 3.0, 4.0), 0.6)), 0.55, 1.05)
    col = m.mix(col, (0.03, 0.028, 0.026), char)
    col = m.mix(col, (0.7, 0.24, 0.04), m.mul(char, m.ramp(m.noise(m.tp, 30.0, 2.0), 0.72, 0.8)))
    M["ASHSTONE"] = m.out(col, m.lerpf(char, 0.82, 0.96), 0.0, m.add(cr, m.noise(m.tp, 25.0, 5.0)), 0.45, 0.008)
    # dark bronze, a green-black patina in the hollows, bright where worn
    m = NT("R_Bronze")
    p = m.geo("Pointiness")
    col = m.mix((0.22, 0.12, 0.055), (0.36, 0.22, 0.11), m.ramp(m.noise(m.tp, 8.0), 0.3, 0.7))
    col = m.mix(col, (0.07, 0.11, 0.08), m.ramp(p, 0.49, 0.42))
    col = m.mix(col, (0.72, 0.5, 0.28), m.ramp(p, 0.55, 0.65))
    M["BRONZE"] = m.out(col, m.lerpf(m.noise(m.tp, 14.0), 0.36, 0.55), m.lerpf(m.ramp(p, 0.42, 0.49), 0.3, 1.0), m.noise(m.tp, 70.0), 0.12, 0.002)
    # silver
    m = NT("R_Silver")
    p = m.geo("Pointiness")
    col = m.mix((0.46, 0.48, 0.53), (0.9, 0.91, 0.94), m.ramp(p, 0.44, 0.54))
    M["SILVER"] = m.out(col, m.lerpf(m.noise(m.tp, 10.0), 0.16, 0.3), 1.0, m.noise(m.tp, 140.0), 0.03, 0.001)
    # moonstone: milky, a blue sheen moving through it
    m = NT("R_Moonstone")
    sh = m.ramp(m.noise(m.tp, 5.0, 3.0, 0.5, 0.6), 0.4, 0.7)
    col = m.mix((0.86, 0.9, 0.98), (0.5, 0.66, 1.0), sh)
    M["MOONSTONE"] = m.out(col, 0.1, 0.0)
    # white marble with soft grey veins
    m = NT("R_Marble")
    vein = m.ridged(m.wave(m.vmul(m.tp, (1.0, 0.6, 1.4)), 1.6, 9.0, 4.0))
    col = m.mix((0.9, 0.89, 0.86), (0.97, 0.96, 0.94), m.ramp(m.noise(m.tp, 4.0), 0.3, 0.7))
    col = m.mix(col, (0.55, 0.56, 0.6), m.ramp(vein, 0.9, 0.99))
    M["MARBLE"] = m.out(col, m.lerpf(vein, 0.22, 0.3), 0.0, m.noise(m.tp, 40.0), 0.04, 0.002)
    # slate: dark, layered
    m = NT("R_Slate")
    lay = m.wave(m.vmul(m.tp, (1, 1, 1)), 6.0, 3.0, 3.0, "BANDS", "Z")
    col = m.mix((0.06, 0.06, 0.075), (0.15, 0.15, 0.17), m.ramp(lay, 0.3, 0.8))
    col = m.mix(col, (0.03, 0.03, 0.04), m.ramp(m.voronoi(m.tp, 3.0, "DISTANCE_TO_EDGE"), 0.02, 0.0))
    M["SLATE"] = m.out(col, 0.86, 0.0, m.add(lay, m.noise(m.tp, 30.0, 5.0)), 0.4, 0.008)
    # the altar's obsidian: black glass with a violet sheen
    m = NT("R_ObsidianViolet")
    rip = m.voronoi(m.tp, 5.0, "SMOOTH_F1")
    col = m.mix((0.018, 0.014, 0.026), (0.09, 0.07, 0.13), m.ramp(rip, 0.25, 0.6))
    col = m.mix(col, (0.3, 0.2, 0.42), m.mul(m.ramp(m.geo("Pointiness"), 0.55, 0.66), 0.7))
    M["OBSIDIANV"] = m.out(col, 0.12, 0.0, rip, 0.3, 0.01)
    # void glass: violet-black, brightening to violet toward the fissure (mask), fine inner sparks
    m = NT("R_VoidGlass")
    col = m.mix((0.02, 0.012, 0.04), (0.08, 0.04, 0.14), m.ramp(m.noise(m.tp, 2.5, 3.0), 0.3, 0.7))
    col = m.mix(col, (0.42, 0.16, 0.85), m.ramp(m.mask, 0.2, 0.95))
    col = m.mix(col, (0.62, 0.5, 1.0), m.mul(m.ramp(m.voronoi(m.tp, 30.0, "F1"), 0.06, 0.0), 0.7))
    col = m.mix(col, (0.4, 0.32, 0.55), m.mul(m.ramp(m.geo("Pointiness"), 0.56, 0.68), 0.5))
    M["VOIDGLASS"] = m.out(col, 0.06, 0.0, m.voronoi(m.tp, 4.0, "SMOOTH_F1"), 0.2, 0.01)
    return M


# which material each relic's stone-like pieces use (the builders name the family)
REMAP = {"WhisperingSpring": {"STONE": "LIMESTONE"}, "OriginAltar": {"OBSIDIAN": "OBSIDIANV"}}


def glow_material(hexstr):
    name = "Relic_Glow_" + hexstr
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    rgb = tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))
    c = (*srgb(*rgb), 1.0)
    b.inputs["Base Color"].default_value = c
    b.inputs["Emission Color"].default_value = c
    b.inputs["Emission Strength"].default_value = 3.0
    b.inputs["Roughness"].default_value = 0.5
    m.diffuse_color = c
    m["glow"] = hexstr
    return m


# =====================================================================================================================
# Blender objects
# =====================================================================================================================
def coll_of(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def ctx(obj, objs=None):
    objs = objs or [obj]
    return bpy.context.temp_override(active_object=obj, object=obj, selected_objects=objs, selected_editable_objects=objs)


def geo_object(name, geos, mats, coll, remap=None):
    verts, faces, fmat, masks, tps, hard = [], [], [], [], [], []
    names = []
    for g in geos:
        mname = (remap or {}).get(g.mat, g.mat)
        if mname not in names:
            names.append(mname)
        mi = names.index(mname)
        base = len(verts)
        verts += [tuple(p) for p in g.co]
        masks += g.mask
        tps += [tuple(p) for p in g.tp]
        for f in g.faces:
            faces.append([i + base for i in f])
            fmat.append(mi)
            hard.append(g.hard)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for mname in names:
        if mname in mats:
            me.materials.append(mats[mname])
        elif len(mname) == 6 and all(ch in "0123456789abcdef" for ch in mname):
            me.materials.append(glow_material(mname))
        else:
            me.materials.append(bpy.data.materials.get("Relic_Plain") or bpy.data.materials.new("Relic_Plain"))
    me.polygons.foreach_set("material_index", fmat)
    a = me.attributes.new("mask", "FLOAT", "POINT")
    a.data.foreach_set("value", masks)
    a = me.attributes.new("tp", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", [x for p in tps for x in p])
    a = me.attributes.new("hard", "BOOLEAN", "FACE")
    a.data.foreach_set("value", hard)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    outward(bm)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def outward(bm):
    """Every closed part faces outward: a part whose signed volume is negative is turned inside out again."""
    bm.faces.ensure_lookup_table()
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        part, stack = [], [f0]
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            part.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        vol = 0.0
        for f in part:
            vs = [v.co for v in f.verts]
            for i in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=part)


def bool_solver():
    items = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    for s in ("MANIFOLD", "EXACT"):
        if s in items:
            return s
    return items[0]


def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear()
    o.data = me
    bpy.data.meshes.remove(old)


def subtract(target, cutter_geos, coll, mats):
    cutters = []
    for i, cg in enumerate(cutter_geos):
        c = geo_object(target.name + "_cut%d" % i, [cg], mats, coll)
        c.data.materials.clear()
        c.data.materials.append(target.data.materials[0])
        c.hide_render = True
        cutters.append(c)
        md = target.modifiers.new("cut%d" % i, "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = bool_solver()
        md.object = c
    apply_mods(target)
    for c in cutters:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(target.data)
    bm.free()


def near_mask(o, cutter_geos, reach=0.09):
    """The material's mask from how near each vertex is to the cut surfaces (heat at the cracks, light at the fissure)."""
    vs, fs = [], []
    for g in cutter_geos:
        b = len(vs)
        vs += [tuple(p) for p in g.co]
        fs += [[i + b for i in f] for f in g.faces]
    bvh = BVHTree.FromPolygons(vs, fs)
    me = o.data
    out = []
    for v in me.vertices:
        hit = bvh.find_nearest(v.co)
        d = (hit[3] if hit[0] is not None else 9.0)
        out.append(max(0.0, 1 - d / reach))
    a = me.attributes.get("mask") or me.attributes.new("mask", "FLOAT", "POINT")
    if a.domain != "POINT":
        me.attributes.remove(a)
        a = me.attributes.new("mask", "FLOAT", "POINT")
    a.data.foreach_set("value", out)


def join(objs, name):
    objs = [o for o in objs if o]
    if len(objs) > 1:
        with ctx(objs[0], objs):
            bpy.ops.object.join()
    objs[0].name = name
    objs[0].data.name = name
    return objs[0]


def body_object(R, name, mats, coll, rid, hi):
    remap = REMAP.get(rid)
    cut_geos = [c[0] for c in getattr(R, "cuts", [])]
    rest = [g for g in R.body if not any(g is c for c in cut_geos)]
    objs = []
    if rest:
        objs.append(geo_object(name + "_rest", rest, mats, coll, remap))
    for tg, cutters, mode in getattr(R, "cuts", []):
        o = geo_object(name + "_cutpart", [tg], mats, coll, remap)
        subtract(o, cutters, coll, mats)
        if hi and mode == "near":
            near_mask(o, cutters[1:] if len(cutters) > 1 else cutters)
        a = o.data.attributes.get("hard")
        if a is not None:
            vals = [tg.hard] * len(o.data.polygons)
            a.data.foreach_set("value", vals)
        objs.append(o)
    o = join(objs, name)
    if hi:
        bevel_hard(o, R)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def bevel_hard(o, R):
    """The high model's hard edges get a small rounded bevel, which the normal bake carries to the game mesh."""
    widths = [g.bevel for g in R.body if g.bevel > 0]
    if not widths:
        return
    me = o.data
    hard = me.attributes.get("hard")
    hv = [False] * len(me.polygons)
    if hard is not None:
        hard.data.foreach_get("value", hv)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    lay = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    for e in bm.edges:
        if len(e.link_faces) == 2 and all(hv[f.index] for f in e.link_faces) and e.calc_face_angle(0.0) > math.radians(28):
            e[lay] = 1.0
    bm.to_mesh(me)
    bm.free()
    md = o.modifiers.new("bevel", "BEVEL")
    md.limit_method = "WEIGHT"
    md.width = max(widths)
    md.segments = 3
    md.harden_normals = False
    apply_mods(o)


def finish_low(o, hard_angle=42):
    """Triangulated, smooth with hard edges where hard pieces fold, unwrapped into one 0..1 atlas."""
    me = o.data
    hard = me.attributes.get("hard")
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    # a boolean's crossing cuts can leave a zero-thickness fin: pairs of sliver triangles on the same three corners; both go
    groups = {}
    for f in bm.faces:
        groups.setdefault(frozenset(v.index for v in f.verts), []).append(f)
    fins = [f for fs in groups.values() if len(fs) > 1 for f in fs]
    if fins:
        bmesh.ops.delete(bm, geom=fins, context="FACES_ONLY")
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    hv = [False] * len(me.polygons)
    hard = me.attributes.get("hard")
    if hard is not None:
        hard.data.foreach_get("value", hv)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and all(hv[f.index] for f in e.link_faces) and e.calc_face_angle(0.0) > math.radians(hard_angle):
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    unwrap(o, angle=hard_angle + 8)
    for name in ("mask", "tp", "hard", "bevel_weight_edge"):
        a = me.attributes.get(name)
        if a is not None:
            me.attributes.remove(a)


def unwrap(o, angle=50, margin=0.004):
    me = o.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    o.select_set(True)
    with ctx(o):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.select_all(action="SELECT")
        try:
            bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, shape_method="CONCAVE")
        except TypeError:
            bpy.ops.uv.pack_islands(margin=margin, rotate=True)
        bpy.ops.object.mode_set(mode="OBJECT")
    # pin every UV strictly inside 0..1
    uv = np.zeros(len(me.loops) * 2)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = np.clip(uv, 0.0005, 0.9995)
    me.uv_layers[0].data.foreach_set("uv", uv)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def cube(name, c, size, coll):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location = c
    return o


def fresh():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.node_groups, bpy.data.lights, bpy.data.cameras, bpy.data.curves, bpy.data.worlds):
        for x in list(block):
            block.remove(x)
    for im in list(bpy.data.images):
        if im.type not in ("RENDER_RESULT", "COMPOSITING"):
            bpy.data.images.remove(im)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)


def gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = True
            return kind
    return "CPU"


# =====================================================================================================================
# one relic: high model, game pieces, bake
# =====================================================================================================================
def build_pieces(rid, mats, bake=True):
    """Builds the relic's high model and game pieces at the origin; bakes the body's maps when asked. Returns the game
    pieces {"body", "core", "glows": [..], "anchor"} and the high object."""
    coll = coll_of("Relic_" + rid)
    lo = BUILDERS[rid](False)
    hi = BUILDERS[rid](True)
    body = body_object(lo, "Relic_%s_Body" % rid, mats, coll, rid, False)
    core = geo_object("Relic_%s_Core" % rid, [lo.core], mats, coll)
    core.data.materials.clear()
    core.data.materials.append(glow_material(hexof(GLOW[rid])))
    glows = []
    for hx, g in lo.glows.items():
        o = geo_object("Relic_%s_Glow_%s" % (rid, hx), [g], mats, coll)
        o.data.materials.clear()
        o.data.materials.append(glow_material(hx))
        glows.append(o)
    hio = body_object(hi, "Hi_%s" % rid, mats, coll, rid, True)
    # each relic at its size in studs (about 3 to 3.6 tall; the wide heart a little lower)
    s = SCALE.get(rid, 1.0)
    if s != 1.0:
        for o in [body, core, hio] + glows:
            o.data.transform(Matrix.Scale(s, 4))
        lo.anchor = lo.anchor * s
    # stand the relic on z = 0
    zmin = min(min(v.co.z for v in o.data.vertices) for o in [body, core] + glows)
    shift = Matrix.Translation((0, 0, -zmin))
    for o in [body, core, hio] + glows:
        o.data.transform(shift)
    anchor_at = lo.anchor + Vector((0, 0, -zmin))
    finish_low(body)
    for o in [core] + glows:
        finish_low(o, hard_angle=180)
        unwrap(o, 66)
    anchor = cube("Relic_%s_Anchor" % rid, (0, 0, 0), 0.02, coll)
    am = bpy.data.materials.get("Relic_Anchor") or bpy.data.materials.new("Relic_Anchor")
    anchor.data.materials.append(am)
    anchor.data.transform(Matrix.Translation(anchor_at))
    unwrap(anchor, 60)
    anchor.hide_render = True
    # every piece's origin at the anchor
    for o in [body, core, anchor] + glows:
        o.data.transform(Matrix.Translation(-anchor_at))
        o.location = anchor_at
    hio.data.transform(Matrix.Translation(-anchor_at))
    hio.location = anchor_at
    out = {"body": body, "core": core, "glows": glows, "anchor": anchor, "hi": hio}
    if bake:
        bake_body(rid, hio, body, [core] + glows + [anchor])
    return out


def _img(name, color):
    im = bpy.data.images.new(name, MAP, MAP, alpha=False, float_buffer=False)
    im.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return im


RAYS = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow")


def bake_body(rid, hio, body, others):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("RelicBakeWorld")
    sc.world.light_settings.distance = 0.22
    imgs = {k: _img("Relic_%s_%s" % (rid, k), k == "color") for k in ("color", "normal", "roughness", "metalness", "ao")}
    bm = bpy.data.materials.new("Relic_%s_BakeTarget" % rid)
    if bm.node_tree is None:
        bm.use_nodes = True
    nodes = {}
    for k, im in imgs.items():
        n = bm.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = im
        n.name = k
        nodes[k] = n
    body.data.materials.clear()
    body.data.materials.append(bm)
    for o in [body] + others:
        for r in RAYS:
            setattr(o, r, False)
    hmats = [m for m in hio.data.materials if m]
    bsdfs = [next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED") for m in hmats]

    def go(kind, key, samples, **kw):
        sc.cycles.samples = samples
        bm.node_tree.nodes.active = nodes[key]
        for x in bpy.context.view_layer.objects:
            x.select_set(False)
        hio.select_set(True)
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        with ctx(body, [hio, body]):
            bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=0.035, max_ray_distance=0.09, margin=16,
                                use_clear=True, target="IMAGE_TEXTURES", **kw)
    t0 = time.time()
    for b in bsdfs:
        b.inputs["Emission Strength"].default_value = 1.0
    go("EMIT", "color", 8)
    for m, b in zip(hmats, bsdfs):
        t = m.node_tree
        if t.nodes.get("MET") is None:
            continue
        t.links.new(t.nodes["MET"].outputs[0], b.inputs["Emission Color"])
    go("EMIT", "metalness", 4)
    for m, b in zip(hmats, bsdfs):
        t = m.node_tree
        if t.nodes.get("COL") is None:
            continue
        t.links.new(t.nodes["COL"].outputs[2], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 0.0
    go("ROUGHNESS", "roughness", 4)
    go("NORMAL", "normal", 8, normal_space="TANGENT")
    go("AO", "ao", 64)
    for o in [body] + others:
        for r in RAYS:
            setattr(o, r, True)
    # the ambient occlusion settles into the colour, gently
    n = MAP * MAP * 4
    col = np.zeros(n, dtype=np.float32)
    ao = np.zeros(n, dtype=np.float32)
    imgs["color"].pixels.foreach_get(col)
    imgs["ao"].pixels.foreach_get(ao)
    k = 0.5 + 0.5 * np.clip(ao[0::4], 0, 1)
    for c in range(3):
        col[c::4] *= k
    imgs["color"].pixels.foreach_set(col)
    imgs["color"].update()
    # the gutters: every pixel no island reached takes the colour of the nearest islands, so mip levels never bleed black
    rough = np.zeros(n, dtype=np.float32)
    imgs["roughness"].pixels.foreach_get(rough)
    col = np.zeros(n, dtype=np.float32)
    imgs["color"].pixels.foreach_get(col)
    filled = (rough.reshape(MAP, MAP, 4)[..., 0] > 0.004) | (col.reshape(MAP, MAP, 4)[..., :3].max(-1) > 0.004)
    for key in ("color", "normal", "roughness", "metalness"):
        px = np.zeros(n, dtype=np.float32)
        imgs[key].pixels.foreach_get(px)
        imgs[key].pixels.foreach_set(fill_gutters(px.reshape(MAP, MAP, 4), filled).ravel())
        imgs[key].update()
    os.makedirs(OUT, exist_ok=True)
    for key in ("color", "normal", "roughness", "metalness"):
        im = imgs[key]
        im.filepath_raw = os.path.join(OUT, "Relic_%s_%s.png" % (rid, key))
        im.file_format = "PNG"
        im.save()
    bpy.data.images.remove(imgs["ao"])
    bpy.data.materials.remove(bm)
    # the game material: the four maps, loaded back from the files
    gm = bpy.data.materials.new("Relic_%s_Mat" % rid)
    if gm.node_tree is None:
        gm.use_nodes = True
    t = gm.node_tree
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    loaded = {}
    for key in ("color", "normal", "roughness", "metalness"):
        old = imgs[key]
        bpy.data.images.remove(old)
        im = bpy.data.images.load(os.path.join(OUT, "Relic_%s_%s.png" % (rid, key)))
        im.name = "Relic_%s_%s" % (rid, key)
        if key != "color":
            im.colorspace_settings.name = "Non-Color"
        n = t.nodes.new("ShaderNodeTexImage")
        n.image = im
        n.name = key
        loaded[key] = n
    t.links.new(loaded["color"].outputs["Color"], b.inputs["Base Color"])
    t.links.new(loaded["roughness"].outputs["Color"], b.inputs["Roughness"])
    t.links.new(loaded["metalness"].outputs["Color"], b.inputs["Metallic"])
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(loaded["normal"].outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    body.data.materials.clear()
    body.data.materials.append(gm)
    print("BAKED", rid, round(time.time() - t0, 1), "s", flush=True)


def fill_gutters(px, mask):
    """Pixels outside mask take the blurred average of the pixels inside it, growing outward until all are filled."""
    out = px.copy()
    m = mask.astype(np.float32)
    for r in (2, 6, 16, 40, 100, 260):
        if m.min() > 0:
            break
        w = blur(m, r)
        acc = blur(out[..., :3] * m[..., None], r)
        take = (m == 0) & (w > 1e-4)
        out[..., :3][take] = acc[take] / w[take][:, None]
        m = np.where(take, 1.0, m)
    out[..., 3] = 1.0
    return out


def save_work(rid, pieces):
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(WORK, rid + ".blend")
    objs = {pieces["body"], pieces["core"], pieces["anchor"]} | set(pieces["glows"])
    if os.path.exists(path):
        os.remove(path)
    bpy.data.libraries.write(path, objs, compress=True)
    return path


def load_work(rid, coll, offset):
    path = os.path.join(WORK, rid + ".blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("Relic_%s_" % rid)]
    objs = [o for o in dst.objects if o]
    for o in objs:
        coll.objects.link(o)
        o.location = o.location + Vector(offset)
    return objs


# =====================================================================================================================
# review renders
# =====================================================================================================================
GLOW_PASS = [False]


def lab(bg=0.2):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("RelicLab") or bpy.data.worlds.new("RelicLab")
    if w.node_tree is None:
        w.use_nodes = True
    bgn = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bgn.inputs[0].default_value = (bg, bg, bg * 1.04, 1)
    bgn.inputs[1].default_value = 0.0 if GLOW_PASS[0] else 1.0
    sc.world = w
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_percentage = 100
    cam = bpy.data.objects.get("RelicCam")
    if cam is None:
        cam = bpy.data.objects.new("RelicCam", bpy.data.cameras.new("RelicCam"))
        sc.collection.objects.link(cam)
    sc.camera = cam
    for name, energy, color in (("Key", 900, (1.0, 0.96, 0.9)), ("Rim", 700, (0.86, 0.92, 1.0)), ("Fill", 260, (0.9, 0.93, 1.0))):
        if bpy.data.objects.get("RelicLab" + name) is None:
            li = bpy.data.lights.new("RelicLab" + name, "AREA")
            li.energy, li.color, li.size = energy, color, 4
            o = bpy.data.objects.new("RelicLab" + name, li)
            sc.collection.objects.link(o)
    return sc, cam


def place_lights(centre, scale):
    for name, d in (("Key", V(4, -5, 5.5)), ("Rim", V(-4.5, 5.5, 4.5)), ("Fill", V(-5.5, -3.5, 1.2))):
        o = bpy.data.objects["RelicLab" + name]
        o.location = Vector(centre) + d * scale
        o.data.size = 4 * scale
        o.rotation_euler = (Vector(centre) - o.location).to_track_quat("-Z", "Y").to_euler()


def bounds(objs):
    lo, hi = V(1e9, 1e9, 1e9), V(-1e9, -1e9, -1e9)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = V(min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z))
            hi = V(max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z))
    return lo, hi


def shoot(objs, yaw, pitch, path, w=640, h=640, samples=64, lens=60, fit=1.12, centre=None, ortho=None):
    sc, cam = lab()
    lo, hi = bounds(objs)
    c = centre or (lo + hi) / 2
    rad = (hi - lo).length / 2
    cam.data.lens = lens
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
    fov = 2 * math.atan(36 / 2 / lens)
    dist = rad * fit / math.sin(fov / 2) * (1.0 if w >= h else h / w)
    y, p = math.radians(yaw), math.radians(pitch)
    cam.location = c + V(math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)) * dist
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_end = dist * 4
    place_lights(c, max(0.6, rad / 2.2))
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.cycles.samples = samples
    sc.render.film_transparent = False
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def load_px(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.zeros(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)[::-1].copy()       # top row first


def save_px(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = arr.shape[:2]
    im = bpy.data.images.new("RelicOut", w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1], dtype=np.float32).ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    return path


def blur(a, r):
    if r < 1:
        return a
    for axis in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(a.ndim)], mode="edge"), axis=axis)
        n = a.shape[axis]
        if axis == 0:
            a = (c[2 * r + 1:2 * r + 1 + n] - c[:n]) / (2 * r + 1)
        else:
            a = (c[:, 2 * r + 1:2 * r + 1 + n] - c[:, :n]) / (2 * r + 1)
    return a


def bloom(px, emit_px, strength=0.9, radius=10):
    """Adds a soft glow round the glowing pieces (from a pass where only they show)."""
    g = emit_px[..., :3]
    out = px.copy()
    gl = blur(blur(g, radius), radius)
    gl2 = blur(blur(g, radius * 3), radius * 3)
    out[..., :3] = 1 - (1 - np.clip(out[..., :3], 0, 1)) * (1 - np.clip(gl * strength + gl2 * strength * 0.6, 0, 1))
    return out


def set_glow(objs, strength):
    for o in objs:
        for m in o.data.materials:
            if m and m.get("glow"):
                b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                b.inputs["Emission Strength"].default_value = strength


def glow_pass(objs, shot):
    """Renders the same shot with everything black but the glows, for the bloom."""
    sc = bpy.context.scene
    blk = bpy.data.materials.get("RelicBlack") or bpy.data.materials.new("RelicBlack")
    if blk.node_tree is None:
        blk.use_nodes = True
    b = next(n for n in blk.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.0
    saved = []
    for o in objs:
        if o.type != "MESH":
            continue
        if not any(m and m.get("glow") for m in o.data.materials):
            saved.append((o, list(o.data.materials)))
            o.data.materials.clear()
            o.data.materials.append(blk)
    w = sc.world
    wb = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND") if w else None
    old = wb.inputs[1].default_value if wb else 1
    if wb:
        wb.inputs[1].default_value = 0.0
    lights = [o for o in bpy.data.objects if o.type == "LIGHT"]
    for li in lights:
        li.hide_render = True
    GLOW_PASS[0] = True
    try:
        shot()
    finally:
        GLOW_PASS[0] = False
        for o, ms in saved:
            o.data.materials.clear()
            for m in ms:
                o.data.materials.append(m)
        if wb:
            wb.inputs[1].default_value = old
        for li in lights:
            li.hide_render = False


def clay(objs, wire=False):
    """Every piece in grey clay (keeping the body's baked normals when it has them); returns an undo."""
    saved = []
    cm = bpy.data.materials.get("RelicClay") or bpy.data.materials.new("RelicClay")
    if cm.node_tree is None:
        cm.use_nodes = True
    t = cm.node_tree
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1)
    b.inputs["Roughness"].default_value = 0.55
    if wire and not t.nodes.get("wire"):
        wn = t.nodes.new("ShaderNodeWireframe")
        wn.name = "wire"
        wn.use_pixel_size = True
        wn.inputs[0].default_value = 0.6
        mx = t.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs[6].default_value = (0.5, 0.5, 0.52, 1)
        mx.inputs[7].default_value = (0.04, 0.05, 0.08, 1)
        t.links.new(wn.outputs[0], mx.inputs[0])
        t.links.new(mx.outputs[2], b.inputs["Base Color"])
    for o in objs:
        if o.type != "MESH":
            continue
        saved.append((o, list(o.data.materials)))
        m = cm
        nmap = None
        for mm in o.data.materials:
            if mm and mm.node_tree and mm.node_tree.nodes.get("normal") and mm.node_tree.nodes["normal"].type == "TEX_IMAGE":
                nmap = mm.node_tree.nodes["normal"].image
        if nmap is not None:
            key = "RelicClayN_" + nmap.name + ("_w" if wire else "")
            m = bpy.data.materials.get(key)
            if m is None:
                m = cm.copy()
                m.name = key
                tt = m.node_tree
                bb = next(n for n in tt.nodes if n.type == "BSDF_PRINCIPLED")
                tx = tt.nodes.new("ShaderNodeTexImage")
                tx.image = nmap
                nm = tt.nodes.new("ShaderNodeNormalMap")
                tt.links.new(tx.outputs["Color"], nm.inputs["Color"])
                tt.links.new(nm.outputs["Normal"], bb.inputs["Normal"])
        if any(mm and mm.get("glow") for mm in o.data.materials):
            m = bpy.data.materials.get("RelicClayGlow") or cm.copy()
            m.name = "RelicClayGlow"
            bb = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            bb.inputs["Base Color"].default_value = (0.82, 0.8, 0.74, 1)
        o.data.materials.clear()
        o.data.materials.append(m)

    def undo():
        for o, ms in saved:
            o.data.materials.clear()
            for mm in ms:
                o.data.materials.append(mm)
    return undo


def render_bloomed(objs, yaw, pitch, path, **kw):
    shoot(objs, yaw, pitch, path, **kw)
    base = load_px(path)
    gp = path[:-4] + "_g.png"
    glow_pass(objs, lambda: shoot(objs, yaw, pitch, gp, **dict(kw, samples=16)))
    em = load_px(gp)
    os.remove(gp)
    out = bloom(base, em, 0.85, max(3, kw.get("w", 640) // 70))
    save_px(out, path)
    return out


# =====================================================================================================================
# stages
# =====================================================================================================================
VIEWS = (("front", 0, 8), ("three", 38, 14), ("side", 90, 6), ("back", 180, 10), ("top", 25, 60))


def stage_clay(rids):
    gpu()
    for rid in rids:
        fresh()
        mats = make_materials()
        P = build_pieces(rid, mats, bake=False)
        game = [P["body"], P["core"]] + P["glows"]
        hio = P["hi"]
        hio.hide_render = True
        set_glow(game, 1.1)
        tiles = []
        undo = clay(game)
        for _, yw, pt in VIEWS:
            tiles.append(load_px(shoot(game, yw, pt, os.path.join(WORK, "_t%d.png" % os.getpid()), 420, 420, 24)))
        undo()
        row_game = np.concatenate(tiles, 1)
        for o in game:
            o.hide_render = True
        hio.hide_render = False
        tiles = []
        for _, yw, pt in VIEWS:
            tiles.append(load_px(shoot([hio], yw, pt, os.path.join(WORK, "_t%d.png" % os.getpid()), 420, 420, 24)))
        row_hi = np.concatenate(tiles, 1)
        out = save_px(np.concatenate([row_game, row_hi], 0), os.path.join(WORK, rid + "_clay.png"))
        print("CLAY", rid, "tris", {o.name: tris(o) for o in game}, "hi", tris(hio), out, flush=True)


def stage_build(rids):
    gpu()
    report = {}
    for rid in rids:
        fresh()
        mats = make_materials()
        P = build_pieces(rid, mats, bake=True)
        game = [P["body"], P["core"]] + P["glows"]
        hio = P["hi"]
        me = hio.data
        bpy.data.objects.remove(hio, do_unlink=True)
        bpy.data.meshes.remove(me)
        path = save_work(rid, P)
        set_glow(game, 1.1)
        tiles = []
        for _, yw, pt in VIEWS:
            tiles.append(render_bloomed(game, yw, pt, os.path.join(WORK, "_t%d.png" % os.getpid()), w=420, h=420, samples=48))
        undo = clay(game)
        ctiles = [load_px(shoot(game, yw, pt, os.path.join(WORK, "_t%d.png" % os.getpid()), 420, 420, 24)) for _, yw, pt in VIEWS]
        undo()
        save_px(np.concatenate([np.concatenate(tiles, 1), np.concatenate(ctiles, 1)], 0), os.path.join(WORK, rid + "_game.png"))
        render_bloomed(game, 35, 12, os.path.join(WORK, rid + "_hero.png"), w=900, h=900, samples=96)
        report[rid] = {o.name: tris(o) for o in game + [P["anchor"]]}
        print("BUILT", rid, report[rid], path, flush=True)
    return report


def strip_fbx_paths(path):
    data = open(path, "rb").read()
    home = os.path.expanduser("~").encode()
    if home.startswith(b"/Users/") and len(home) > len(b"/Users/"):
        tail = len(home) - len(b"/Users/")
        neutral = b"/Users/user" + b"_" * (tail - 4) if tail >= 4 else b"/Users/" + b"u" * tail
        data = data.replace(home + b"/", neutral + b"/")
    open(path, "wb").write(data)
    return data.count(home + b"/")


def stage_export():
    fresh()
    coll = coll_of("SpiritRelics")
    allo = []
    for i, rid in enumerate(IDS):
        allo += load_work(rid, coll, ((i - 5) * SPACING, 0, 0))
    meshes = [o for o in allo if o.type == "MESH"]
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    os.makedirs(OUT, exist_ok=True)
    with ctx(meshes[0], meshes):
        bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
                                 apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE",
                                 add_leaf_bones=False, bake_anim=False)
    left = strip_fbx_paths(FBX)
    print("FBX", FBX, "home paths left", left, flush=True)
    save_blend()
    print("BLEND", BLEND, flush=True)


def save_blend():
    bpy.context.preferences.filepaths.save_version = 0
    sc = bpy.context.scene
    sc.render.filepath = "//" + "_" * 1020
    sc.render.filepath = "//"
    for w in list(bpy.data.worlds):
        bpy.data.worlds.remove(w)
    bpy.data.orphans_purge(do_recursive=True)
    for im in bpy.data.images:
        if im.source != "FILE":
            continue
        if not im.packed_file:
            im.pack()
        rel = "//../../../assets/relics/" + os.path.basename(im.filepath_raw)
        im.filepath_raw = "//" + "_" * 1000
        im.filepath_raw = rel
        for pf in im.packed_files:
            pf.filepath = rel
    if os.path.exists(BLEND):
        os.remove(BLEND)
    bpy.data.libraries.write(BLEND, {sc}, path_remap="NONE", compress=True)


def stage_verify():
    fresh()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=FBX)
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    rep = {"relics": {}, "tris_total": 0}
    for rid in IDS:
        mine = [o for o in objs if o.name.startswith("Relic_%s_" % rid)]
        lo, hi = bounds([o for o in mine if not o.name.endswith("_Anchor")])
        rep["relics"][rid] = {"parts": {o.name: tris(o) for o in mine},
                              "tris": sum(tris(o) for o in mine if not o.name.endswith("_Anchor")),
                              "size": [round(x, 3) for x in (hi - lo)],
                              "anchor": [round(x, 3) for x in next(o for o in mine if o.name.endswith("_Anchor")).matrix_world.translation],
                              "scale": sorted({tuple(round(s, 4) for s in o.scale) for o in mine}),
                              "uv_sets": sorted({len(o.data.uv_layers) for o in mine})}
        rep["tris_total"] += rep["relics"][rid]["tris"]
    qa_dir = os.environ.get("QA_CHECK_DIR")          # the folder holding the mesh checker qa_check.py
    if not qa_dir:
        raise SystemExit("set QA_CHECK_DIR to the folder holding qa_check.py")
    sys.path.insert(0, qa_dir)
    import qa_check
    # the relics' geometry together; the anchors (2 cm marker cubes, often in empty space at a relic's centre) each on their own
    geo = [o.name for o in objs if not o.name.endswith("_Anchor")]
    res = qa_check.run(objects=geo, profile="roblox")
    rep["qa_all"] = {k: res[k] for k in ("pass", "errors", "warnings", "ground_z")}
    rep["qa_per_relic"] = {}
    for rid in IDS:
        mine = [o.name for o in objs if o.name.startswith("Relic_%s_" % rid) and not o.name.endswith("_Anchor")]
        r = qa_check.run(objects=mine, profile="roblox")
        a = qa_check.run(objects=["Relic_%s_Anchor" % rid], profile="roblox")
        rep["qa_per_relic"][rid] = {"pass": r["pass"], "errors": r["errors"], "warnings": r["warnings"], "anchor_pass": a["pass"], "anchor_errors": a["errors"]}
    data = open(FBX, "rb").read()
    rep["fbx_scan"] = {w: data.count(w.encode()) for w in (os.path.expanduser("~") + "/", "/private/", "/tmp/")}
    os.makedirs(WORK, exist_ok=True)
    json.dump(rep, open(os.path.join(WORK, "verify.json"), "w"), indent=1, default=str)
    print("VERIFY", json.dumps(rep, indent=1, default=str), flush=True)
    return rep


def label_px(text, w, h, size=0.5, color=(0.92, 0.92, 0.95)):
    """A line of text as pixels (white on transparent), rendered with a text object."""
    sc = bpy.data.scenes.get("RelicLabel") or bpy.data.scenes.new("RelicLabel")
    for o in list(sc.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    cu = bpy.data.curves.new("RelicLabelText", "FONT")
    cu.body = text
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = size
    to = bpy.data.objects.new("RelicLabelText", cu)
    sc.collection.objects.link(to)
    m = bpy.data.materials.get("RelicLabelMat") or bpy.data.materials.new("RelicLabelMat")
    m.diffuse_color = (*color, 1)
    cu.materials.append(m)
    cam = bpy.data.objects.new("RelicLabelCam", bpy.data.cameras.new("RelicLabelCam"))
    sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = w / h
    cam.location = (0, 0, 5)
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "MATERIAL"
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    path = os.path.join(WORK, "_label%d.png" % os.getpid())
    sc.render.filepath = path
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    px = load_px(path)
    os.remove(path)
    bpy.data.objects.remove(to, do_unlink=True)
    bpy.data.curves.remove(cu)
    cd = cam.data
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cd)
    return px


def over(dst, src, x0, y0):
    h, w = src.shape[:2]
    a = src[..., 3:4]
    dst[y0:y0 + h, x0:x0 + w, :3] = dst[y0:y0 + h, x0:x0 + w, :3] * (1 - a) + src[..., :3] * a
    return dst


def canvas(w, h, c=0.1):
    a = np.zeros((h, w, 4), dtype=np.float32)
    a[..., :3] = c
    a[..., 3] = 1
    return a


def stage_review():
    gpu()
    fresh()
    coll = coll_of("SpiritRelics")
    per = {}
    allo = []
    for i, rid in enumerate(IDS):
        objs = load_work(rid, coll, ((i - 5) * SPACING, 0, 0))
        per[rid] = [o for o in objs if not o.name.endswith("_Anchor")]
        for o in objs:
            if o.name.endswith("_Anchor"):
                o.hide_render = True
        allo += per[rid]
    set_glow(allo, 1.1)
    TW = 600
    cols = 4
    tiles = []
    # a first small render settles the scene (the session's first render otherwise came out empty)
    for o in allo:
        o.hide_render = o not in per[IDS[0]]
    shoot(per[IDS[0]], 35, 12, os.path.join(WORK, "_warm%d.png" % os.getpid()), 64, 64, 4)
    os.remove(os.path.join(WORK, "_warm%d.png" % os.getpid()))
    for i, rid in enumerate(IDS):
        for o in allo:
            o.hide_render = o not in per[rid]
        px = render_bloomed(per[rid], 35, 12, os.path.join(WORK, "_tile.png"), w=TW, h=TW, samples=96)
        lab_ = label_px("%d  %s  -  %s" % (i + 1, NAMES[rid], rid), TW, 44, 0.42)
        tile = canvas(TW, TW + 44, 0.12)
        tile[:TW] = px
        over(tile, lab_, 0, TW)
        tiles.append(tile)
    for o in allo:
        o.hide_render = False
    # the 12th cell: the line-up's key
    key = canvas(TW, TW + 44, 0.12)
    for k, line in enumerate(("SPIRIT RELICS", "11 relics, baked 1024 maps", "glow pieces shown bright (Neon)", "row 2: all at the same scale",
                              "row 3: clay with wireframe", "1 unit = 1 stud")):
        over(key, label_px(line, TW, 50, 0.4 if k else 0.6), 0, 150 + k * 60)
    tiles.append(key)
    rows = [np.concatenate(tiles[r * cols:(r + 1) * cols], 1) for r in range(3)]
    grid = np.concatenate(rows, 0)
    Wd = grid.shape[1]
    # all eleven side by side at one scale, front three-quarter, orthographic
    lo, hi = bounds(allo)
    c = (lo + hi) / 2
    LH = 560
    span = (hi.x - lo.x) * 1.04
    line = render_bloomed(allo, 8, 6, os.path.join(WORK, "_line.png"), w=Wd, h=LH, samples=64, ortho=span, centre=c, lens=60)
    names = canvas(Wd, 40, 0.1)
    for i, rid in enumerate(IDS):
        x = int((((i - 5) * SPACING) - (c.x - span / 2)) / span * Wd)
        lp = label_px(NAMES[rid], 300, 40, 0.34)
        over(names, lp, max(0, min(Wd - 300, x - 150)), 0)
    undo = clay(allo, wire=True)
    wire = load_px(shoot(allo, 8, 6, os.path.join(WORK, "_wire.png"), Wd, LH, 32, ortho=span, centre=c))
    undo()
    head = canvas(Wd, 70, 0.08)
    over(head, label_px("SPIRIT RELICS  -  review sheet", Wd, 70, 0.55), 0, 0)
    sheet = np.concatenate([head, grid, canvas(Wd, 20, 0.08), line, names, canvas(Wd, 20, 0.08), wire, canvas(Wd, 10, 0.08)], 0)
    save_px(sheet, SHEET)
    print("SHEET", SHEET, sheet.shape, flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    stage = argv[0] if argv else "all"
    which = IDS if len(argv) < 2 or argv[1] == "all" else argv[1].split(",")
    os.makedirs(WORK, exist_ok=True)
    if stage == "clay":
        stage_clay(which)
    elif stage == "build":
        stage_build(which)
    elif stage == "export":
        stage_export()
    elif stage == "verify":
        stage_verify()
    elif stage == "review":
        stage_review()
    elif stage == "all":
        stage_build(IDS)
        stage_export()
        stage_verify()
        stage_review()
    print("DONE", stage, flush=True)

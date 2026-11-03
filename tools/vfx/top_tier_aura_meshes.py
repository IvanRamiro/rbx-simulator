"""The high realms' aura meshes (the owner's Tier 10 and Tier 12 brief, 2026-11-03, then a
signature piece for Divine, Cosmic, Void and Primordial), built as code (all of them are
procedural: rings, a cone band, shards, an icosphere, torus knots, a halo, flames, orbits, coils)
and written as OBJ for Studio's 3D Importer. Sizes are in studs, around the character's root
(y = 0 at the root; the feet are at about y = -3). Rings and knots are unwrapped along their
length (U from 0 to 1 round the circle or the knot), so a texture can scroll without a seam.
Shells seen from both sides are double-sided: each face written twice, the copy reversed.

    python3 top_tier_aura_meshes.py assets/aura/top_tier     (needs numpy)

One file per mesh (the importer merges a file's objects into one mesh):
  Tier 10   DaoRing_Outer.obj       an inverted cone band opening upward round the feet
            DaoRing_Inner.obj       four flat concentric rings, broken into arcs, under the feet
            LawPillars.obj          four tall twisted crystal shards round the body
  Tier 12   EventHorizon.obj        an icosphere, double-sided (a void shell round the body)
            OrbitalHelices.obj      two interlocked torus knots (thin tubes) orbiting the body
            TranscendenceCrown.obj  a halo behind the head: two rings, twelve spokes, nodes
  Tier 7    DivineFlameCrown.obj    ten curved flame tongues in a ring round the body
  Tier 8    CosmicOrrery.obj        three tilted orbit rings, each carrying small planets
  Tier 9    VoidShards.obj          jagged fragments of broken space floating in a ring
  Tier 11   PrimordialCoils.obj     two flat ribbon coils spiralling from the feet past the head
"""
import math
import os
import sys

import numpy as np

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


class Mesh:
    def __init__(self, name):
        self.name = name
        self.v, self.vt, self.f = [], [], []   # faces: [(vertex index, uv index), ...]

    def vert(self, p, uv):
        self.v.append(p)
        self.vt.append(uv)
        return len(self.v) - 1

    def quad(self, a, b, c, d, both=False):
        self.f.append([a, b, c, d])
        if both:
            self.f.append([d, c, b, a])

    def tri(self, a, b, c, both=False):
        self.f.append([a, b, c])
        if both:
            self.f.append([c, b, a])

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def write(path, meshes):
    with open(path, "w") as out:
        out.write("# Qi Aura Simulator: top-tier aura meshes (tools/vfx/top_tier_aura_meshes.py)\n")
        base = 0
        for m in meshes:
            out.write("o %s\ng %s\n" % (m.name, m.name))
            for p in m.v:
                out.write("v %.5f %.5f %.5f\n" % tuple(p))
            for uv in m.vt:
                out.write("vt %.5f %.5f\n" % tuple(uv))
            for f in m.f:
                out.write("f " + " ".join("%d/%d" % (base + i + 1, base + i + 1) for i in f) + "\n")
            base += len(m.v)


# a grid of vertices round a circle: rows of (radius, height); U round, V across the rows
def band(m, rows, segments, both):
    grid = []
    for j, (r, y) in enumerate(rows):
        line = []
        for i in range(segments + 1):          # the seam vertex repeats, with U = 1
            a = i / segments * math.tau
            line.append(m.vert((math.cos(a) * r, y, math.sin(a) * r), (i / segments, j / (len(rows) - 1))))
        grid.append(line)
    for j in range(len(rows) - 1):
        for i in range(segments):
            m.quad(grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i], both)


# ---------- Tier 10: Heavenly Dao ----------
def dao_outer():
    m = Mesh("DaoRing_Outer")
    rows = [(4.6 + 2.4 * k / 5, -2.9 + 2.6 * k / 5) for k in range(6)]   # widening as it rises
    band(m, rows, 48, both=True)
    return m


def dao_inner():
    m = Mesh("DaoRing_Inner")
    y = -2.85
    # (inner radius, outer radius, arcs, gap share): solid, broken, solid, finely broken
    for r0, r1, arcs, gap in ((2.4, 2.75, 1, 0), (3.2, 3.45, 8, 0.18), (3.9, 4.05, 1, 0), (4.35, 4.45, 24, 0.35)):
        steps = 40 // arcs if arcs > 1 else 40
        for k in range(arcs):
            start = k / arcs
            span = (1 / arcs) * (1 - gap)
            ring_in, ring_out = [], []
            for s in range(steps + 1):
                u = start + span * s / steps
                a = u * math.tau
                ring_in.append(m.vert((math.cos(a) * r0, y, math.sin(a) * r0), (u, 0)))
                ring_out.append(m.vert((math.cos(a) * r1, y, math.sin(a) * r1), (u, 1)))
            for s in range(steps):
                m.quad(ring_in[s], ring_out[s], ring_out[s + 1], ring_in[s + 1], both=True)
    return m


def law_pillars():
    m = Mesh("LawPillars")
    for k in range(4):
        a = k / 4 * math.tau + math.pi / 4
        base = np.array([math.cos(a) * 3.3, -2.6 + 0.6 * (k % 2), math.sin(a) * 3.3])
        out = np.array([math.cos(a), 0, math.sin(a)])
        height = 5.4 if k % 2 == 0 else 4.6
        rings = []
        levels = [(0.0, 0.0), (0.12, 0.3), (0.35, 0.36), (0.6, 0.3), (0.8, 0.2), (1.0, 0.0)]  # (along, radius)
        for li, (t, r) in enumerate(levels):
            centre = base + np.array([0, height * t, 0]) + out * (0.5 * t * t)   # leaning outward as it rises
            twist = t * 0.9
            ring = []
            for s in range(6):
                b = s / 6 * math.tau + twist
                p = centre + np.array([math.cos(b) * r, 0, math.sin(b) * r])
                ring.append(m.vert(tuple(p), (s / 6, t)))
            rings.append(ring)
        for li in range(len(levels) - 1):
            for s in range(6):
                m.quad(rings[li][s], rings[li][(s + 1) % 6], rings[li + 1][(s + 1) % 6], rings[li + 1][s])
    return m


# ---------- Tier 12: Eternal Transcendence ----------
def event_horizon():
    m = Mesh("EventHorizon")
    t = (1 + 5 ** 0.5) / 2
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
             (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    verts = [np.array(v) / np.linalg.norm(v) for v in verts]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
             (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(2):                                   # two subdivisions: 320 faces
        cache, nf = {}, []
        def mid(i, j):
            key = (min(i, j), max(i, j))
            if key not in cache:
                p = verts[i] + verts[j]
                verts.append(p / np.linalg.norm(p))
                cache[key] = len(verts) - 1
            return cache[key]
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nf
    radius = 3.2
    for a, b, c in faces:                                # flat per face: no UV seam across faces
        ids = []
        for i in (a, b, c):
            p = verts[i]
            u = 0.5 + math.atan2(p[2], p[0]) / math.tau
            v = 0.5 + math.asin(max(-1, min(1, p[1]))) / math.pi
            ids.append(m.vert(tuple(p * radius), (u, v)))
        m.tri(ids[0], ids[1], ids[2], both=True)         # 640 faces with the reversed copies
    return m


def tube(m, path, radius, sides):
    """a tube along a closed path (a list of points); U along it, V round it"""
    n = len(path)
    rings = []
    for i in range(n + 1):
        p = path[i % n]
        tangent = path[(i + 1) % n] - path[(i - 1) % n]
        tangent /= np.linalg.norm(tangent)
        side = np.cross(tangent, [0, 1, 0])
        if np.linalg.norm(side) < 1e-4:
            side = np.cross(tangent, [1, 0, 0])
        side /= np.linalg.norm(side)
        up = np.cross(side, tangent)
        ring = []
        for s in range(sides + 1):
            b = s / sides * math.tau
            q = p + (side * math.cos(b) + up * math.sin(b)) * radius
            ring.append(m.vert(tuple(q), (i / n, s / sides)))
        rings.append(ring)
    for i in range(n):
        for s in range(sides):
            m.quad(rings[i][s], rings[i + 1][s], rings[i + 1][s + 1], rings[i][s + 1])


def orbital_helices():
    m = Mesh("OrbitalHelices")
    for k, (p, q, tilt) in enumerate(((2, 3, 0.35), (3, 2, -0.5))):
        path = []
        for i in range(80):
            t = i / 80 * math.tau
            r = 3.6 + 0.9 * math.cos(q * t)
            x, z, y = r * math.cos(p * t), r * math.sin(p * t), 1.1 * math.sin(q * t)
            # tilted, so the two knots cross each other at an angle
            yy = y * math.cos(tilt) - z * math.sin(tilt)
            zz = y * math.sin(tilt) + z * math.cos(tilt)
            path.append(np.array([x, yy + 0.3 * k, zz]))
        tube(m, path, 0.07, 5)
    return m


def crown():
    m = Mesh("TranscendenceCrown")
    centre = np.array([0, 2.4, 0.9])                     # behind the head (the character faces -Z)
    def circle(r, n):
        return [centre + np.array([math.cos(i / n * math.tau) * r, math.sin(i / n * math.tau) * r, 0]) for i in range(n)]
    tube(m, circle(2.3, 48), 0.06, 5)
    tube(m, circle(1.65, 40), 0.045, 5)
    for i in range(12):
        a = i / 12 * math.tau
        d = np.array([math.cos(a), math.sin(a), 0])
        inner, outer = centre + d * 1.65, centre + d * (2.3 if i % 3 else 2.75)   # every third spoke reaches past the rim
        # a thin flat spoke
        side = np.array([-d[1], d[0], 0]) * 0.035
        ids = [m.vert(tuple(p), uv) for p, uv in ((inner - side, (0, 0)), (inner + side, (0, 1)), (outer + side, (1, 1)), (outer - side, (1, 0)))]
        m.quad(ids[0], ids[1], ids[2], ids[3], both=True)
        if i % 3 == 0:                                   # a diamond node at the long spokes' tips
            tip = outer + d * 0.16
            s = 0.13
            pts = [tip + d * s, tip + np.array([-d[1], d[0], 0]) * s, tip - d * s, tip - np.array([-d[1], d[0], 0]) * s]
            front, back = tip + np.array([0, 0, -s]), tip + np.array([0, 0, s])
            pi = [m.vert(tuple(p), (j / 4, 0.5)) for j, p in enumerate(pts)]
            fi, bi = m.vert(tuple(front), (0.5, 0)), m.vert(tuple(back), (0.5, 1))
            for j in range(4):
                m.tri(pi[j], pi[(j + 1) % 4], fi)
                m.tri(pi[(j + 1) % 4], pi[j], bi)
    return m


# ---------- signature pieces: Divine, Cosmic, Void, Primordial ----------
def sweep(m, path, profile, scales, closed=False, across=None):
    """a cross-section (2D points, x across, y through) swept along a path, scaled per sample;
    U along the path, V round the section. `across`, if given, is a direction per sample for the
    section's x axis (made square to the path); otherwise it is found from the path"""
    n = len(path)
    rings = []
    for i in range(n):
        p = path[i]
        tangent = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        tangent /= np.linalg.norm(tangent)
        if across is not None:
            side = np.array(across[i], dtype=float)
            side -= tangent * np.dot(side, tangent)
        else:
            side = np.cross(tangent, [0, 1, 0]) if abs(tangent[1]) < 0.95 else np.cross(tangent, [1, 0, 0])
        side /= np.linalg.norm(side)
        up = np.cross(side, tangent)
        k = scales[i]
        ring = [m.vert(tuple(p + (side * x + up * y) * k), (i / (n - 1), j / len(profile))) for j, (x, y) in enumerate(profile)]
        rings.append(ring)
    sides = len(profile)
    for i in range(n - 1):
        for j in range(sides):
            m.quad(rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % sides], rings[i][(j + 1) % sides])
    if not closed:                                       # cap both ends with a point
        for end, ring, step in ((path[0], rings[0], -1), (path[-1], rings[-1], 1)):
            c = m.vert(tuple(end), (0.5, 0.5))
            for j in range(sides):
                a, b = ring[j], ring[(j + 1) % sides]
                if step > 0:
                    m.tri(a, b, c)
                else:
                    m.tri(b, a, c)


def flame_crown():
    m = Mesh("DivineFlameCrown")
    lens = [(0.75, 0), (0.38, 0.08), (-0.38, 0.08), (-0.75, 0), (-0.38, -0.08), (0.38, -0.08)]   # a flattened tongue
    for k in range(10):
        a0 = k / 10 * math.tau
        tall = 1.0 if k % 2 == 0 else 0.78
        path, scales, across = [], [], []
        for i in range(10):
            t = i / 9
            a = a0 + 0.12 * math.sin(t * math.pi * 1.2)          # a slight sway as it rises
            r = 2.5 + 0.3 * math.sin(t * math.pi) - 0.4 * t * t  # bulging out, then curling in at the tip
            y = -1.4 + 4.8 * tall * t
            path.append(np.array([math.cos(a) * r, y, math.sin(a) * r]))
            scales.append(max(0.02, math.sin(min(t * 1.15, 1) * math.pi) ** 0.8 * (1 - 0.6 * t)))
            across.append((-math.sin(a), 0, math.cos(a)))         # broad side facing out from the body
        sweep(m, path, lens, scales, across=across)
    return m


def icosphere(m, centre, radius):
    t = (1 + 5 ** 0.5) / 2
    verts = [np.array(v) / np.linalg.norm(v) for v in [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
             (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
             (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    ids = [m.vert(tuple(centre + v * radius), (0.5 + math.atan2(v[2], v[0]) / math.tau, 0.5 + v[1] / 2)) for v in verts]
    for a, b, c in faces:
        m.tri(ids[a], ids[b], ids[c])


def orrery():
    m = Mesh("CosmicOrrery")
    for k, (rx, rz, tilt, spin, planets) in enumerate(((3.3, 2.9, 0.35, 0.0, 2), (4.1, 3.6, -0.6, 1.1, 3), (4.9, 4.4, 1.05, 2.3, 2))):
        rot = lambda v: np.array([
            v[0] * math.cos(spin) - v[2] * math.sin(spin),
            v[1],
            v[0] * math.sin(spin) + v[2] * math.cos(spin)])
        def orbit(t):
            x, z = math.cos(t) * rx, math.sin(t) * rz
            y, zz = z * math.sin(tilt), z * math.cos(tilt)
            return rot(np.array([x, y + 0.6, zz]))
        tube(m, [orbit(i / 48 * math.tau) for i in range(48)], 0.035, 4)
        for j in range(planets):
            icosphere(m, orbit((j / planets + 0.13 * k) * math.tau), 0.16 + 0.06 * ((j + k) % 2))
    return m


def void_shards():
    m = Mesh("VoidShards")
    rng = np.random.default_rng(9)
    for k in range(14):
        big = k < 8
        a = k / 8 * math.tau if big else rng.uniform(0, math.tau)
        r = 3.4 if big else rng.uniform(2.6, 4.6)
        centre = np.array([math.cos(a) * r, rng.uniform(-1.6, 2.4), math.sin(a) * r])
        length = rng.uniform(1.0, 1.7) if big else rng.uniform(0.35, 0.7)
        width = length * rng.uniform(0.28, 0.4)
        axis = rng.normal(size=3)
        axis[1] = abs(axis[1]) + 1.2                     # mostly upright, each at its own lean
        axis /= np.linalg.norm(axis)
        side = np.cross(axis, [0, 0, 1]); side /= np.linalg.norm(side)
        up = np.cross(axis, side)
        ring = []
        for j in range(5):                               # a jagged five-sided waist
            b = j / 5 * math.tau + rng.uniform(-0.3, 0.3)
            w = width * rng.uniform(0.6, 1.2)
            ring.append(m.vert(tuple(centre + (side * math.cos(b) + up * math.sin(b)) * w + axis * rng.uniform(-0.15, 0.15) * length), (j / 5, 0.5)))
        top = m.vert(tuple(centre + axis * length * rng.uniform(0.6, 1.0)), (0.5, 1))
        bottom = m.vert(tuple(centre - axis * length * rng.uniform(0.3, 0.7)), (0.5, 0))
        for j in range(5):
            m.tri(ring[j], ring[(j + 1) % 5], top)
            m.tri(ring[(j + 1) % 5], ring[j], bottom)
    return m


def primordial_coils():
    m = Mesh("PrimordialCoils")
    ribbon = [(0.32, 0.05), (0, 0.09), (-0.32, 0.05), (-0.32, -0.05), (0, -0.09), (0.32, -0.05)]   # a flat, rounded band
    for k in range(2):
        path, scales = [], []
        for i in range(64):
            t = i / 63
            a = k * math.pi + t * 1.6 * math.tau             # a long, sweeping climb
            r = 2.7 + 0.6 * t
            path.append(np.array([math.cos(a) * r, -2.8 + 7.4 * t, math.sin(a) * r]))
            scales.append(max(0.05, math.sin(min(t * 1.25, 1) * math.pi) ** 0.5 * (1.1 - 0.5 * t)))   # a tail, a body, a head
        sweep(m, path, ribbon, scales)
    return m


# one file per mesh: Studio's importer merges the objects of one OBJ into a single mesh, and these
# pieces turn on their own
for m in (dao_outer(), dao_inner(), law_pillars(), event_horizon(), orbital_helices(), crown(),
          flame_crown(), orrery(), void_shards(), primordial_coils()):
    write(os.path.join(OUT, m.name + ".obj"), [m])
    print("%-20s %5d triangles" % (m.name, m.tris()))

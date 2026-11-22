"""hq_kit: the shared kit for the three Murim faction headquarters (2026-11-22).

The Orthodox hall (orthodox_hq.py) is the architectural quality standard; the Unorthodox and Demonic headquarters reuse these primitives
with a different `Style` (materials and proportions) and their own plan. Plain Python, no Blender: every function builds geometry into a
`Piece` (material suffix -> `Geo`), authored in ROBLOX STUDS (x right, y up, z back; a module's FRONT is -Z), at its own origin (y = 0 at its
base). hq_blender.py turns Pieces into Blender objects, UVs, QA, renders and FBX.

API (all return a Piece unless said; `st` is a Style):
  Geo / Piece           mesh containers. Geo.add(other, t, yaw, s, mx), .mirrored(), .symmetrize(), .weld(), .orient(), .tris()
  box, hexa, prism, lathe, tube      raw solids appended to a Geo (box faces "TB" + "NESW" or 0-3; N is -Z, E +X)
  Style                  the materials (suffix names) and the proportions of one headquarters; subclass or edit for another
  pillar(st, h)          round column: granite foot + drum, entasis shaft, gold bands
  bracket_set(st, layers, h)   stacked bracket set (dougong): blocks, arms, inclined lever arm, gold edging
  roof(st, A, D, at, dt, ye, yt, ...)   tiled hip roof with an S-curve, corner lift and flare (flying eaves), tile rows as ribs, round
                         eave-end tiles, rafters in two layers, gold hip-ridge caps and corner horns; at = dt = 0 makes a pyramid roof
  lattice(st, w, h)      lattice window or screen panel; door_leaf(st, w, h) panelled door leaf with studs and a pull ring
  balustrade(st, L, h)   marble panel balustrade with post caps (along +x, 0..L)
  lantern(st, h)         stone pedestal lantern with a glow core; glow_cores keep it small
  banner(st, w, h)       hanging cloth banner with a gold rod, tassels and the crest in white
  crest(g, st, R, origin, U, V, N, thick)    the original crest (two rings, three rising blades, a ground bar) as relief
  paving(st, x0, x1, z0, z1)  court floor: marble with granite joints
  rock_mound(st, ring, y0, y1)   a layered rock mass; stair(st, ...)  steps; spire(st) crystal spire in a gold cradle with halo rings
  storey(st, a, d, y0, ...)      one storey (columns, beams, wall with windows, brackets) ; tower(st, ...) ; pavilion(st, ...)
Conventions: yaw turns a point about Y as CFrame.Angles(0, yaw, 0) does (x' = x cos + z sin, z' = -x sin + z cos); a module facing -Z turns to
face +X with yaw -pi/2, +Z with pi, -X with +pi/2 (FACE_YAW). Level of detail: `detail` 0 (far), 1, 2 (close) on roofs and brackets.
"""
import math

TAU = 2 * math.pi
FACE_YAW = {"N": 0.0, "E": -math.pi / 2, "S": math.pi, "W": math.pi / 2}


# ======================================================================================================================
# vectors
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


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def yaw_xz(x, z, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return x * c + z * s, -x * s + z * c


# ======================================================================================================================
# geometry containers
# ======================================================================================================================
class Geo:
    """Indexed faces (triangles and quads only) in Roblox studs."""

    def __init__(self):
        self.v = []
        self.f = []
        self.boxes = []          # (first vertex, 8): axis-aligned boxes made by hexa(): used to separate coplanar contact faces

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def face(self, *ids):
        self.f.append(tuple(ids))

    def tris(self):
        return sum(len(f) - 2 for f in self.f)

    def add(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0, mx=False):
        """Merges a transformed copy of `other`: optional mirror in x, scale, yaw about Y, then translation."""
        base = len(self.v)
        self.boxes += [(b0 + base, n) for (b0, n) in other.boxes]
        c, sn = math.cos(yaw), math.sin(yaw)
        sx, sy, sz = (s, s, s) if not isinstance(s, tuple) else s
        for (x, y, z) in other.v:
            if mx:
                x = -x
            x, y, z = x * sx, y * sy, z * sz
            self.v.append((x * c + z * sn + t[0], y + t[1], -x * sn + z * c + t[2]))
        for f in other.f:
            ids = [i + base for i in f]
            self.f.append(tuple(reversed(ids)) if mx else tuple(ids))
        return self

    def mirrored(self):
        g = Geo()
        return g.add(self, mx=True)

    def bounds(self):
        xs = [p[0] for p in self.v]
        ys = [p[1] for p in self.v]
        zs = [p[2] for p in self.v]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def transform(self, fn):
        self.v = [tuple(fn(p)) for p in self.v]
        return self

    # ---- cleaning ----
    def compact(self):
        """Drops unreferenced vertices and degenerate faces (repeated corner)."""
        faces = []
        for f in self.f:
            ids = []
            for i in f:
                if not ids or ids[-1] != i:
                    ids.append(i)
            if len(ids) > 1 and ids[0] == ids[-1]:
                ids.pop()
            if len(ids) >= 3 and len(set(ids)) == len(ids):
                faces.append(tuple(ids))
        used = sorted({i for f in faces for i in f})
        remap = {o: n for n, o in enumerate(used)}
        self.v = [self.v[i] for i in used]
        self.f = [tuple(remap[i] for i in f) for f in faces]
        return self

    def weld(self, eps=1e-5):
        """Merges vertices closer than eps (grid hash), then compacts."""
        key = {}
        remap = []
        for p in self.v:
            k = (round(p[0] / eps), round(p[1] / eps), round(p[2] / eps))
            if k not in key:
                key[k] = len(key)
            remap.append(key[k])
        nv = [None] * len(key)
        for i, p in enumerate(self.v):
            if nv[remap[i]] is None:
                nv[remap[i]] = p
        self.v = nv
        self.f = [tuple(remap[i] for i in f) for f in self.f]
        return self.compact()

    @staticmethod
    def _canon(ids):
        k = ids.index(min(ids))
        return tuple(ids[k:] + ids[:k])

    def cull_twins(self, eps=1e-5):
        """Removes pairs of coincident faces with opposite winding (contact faces between two solids), matched by coordinates."""
        def key(p):
            return (round(p[0] / eps), round(p[1] / eps), round(p[2] / eps))
        seen = {}
        dead = set()
        pts_of = []
        for n, f in enumerate(self.f):
            pts = [key(self.v[i]) for i in f]
            pts_of.append(pts)
            k = frozenset(pts)
            if len(k) < len(pts):
                continue
            found = None
            for m in seen.get(k, []):
                if m in dead:
                    continue
                if self._canon(pts_of[m]) == self._canon(list(reversed(pts))):
                    found = m
                    break
            if found is not None:
                dead.add(found)
                dead.add(n)
            else:
                seen.setdefault(k, []).append(n)
        if dead:
            self.f = [f for n, f in enumerate(self.f) if n not in dead]
            self.compact()
        return len(dead)

    def orient(self):
        """Flips every closed, consistently wound component whose signed volume is negative. Returns (components, closed, flipped)."""
        n = len(self.f)
        parent = list(range(len(self.v)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for f in self.f:
            r = find(f[0])
            for i in f[1:]:
                ri = find(i)
                if ri != r:
                    parent[ri] = r
        comps = {}
        for k, f in enumerate(self.f):
            comps.setdefault(find(f[0]), []).append(k)
        closed = flipped = 0
        for faces in comps.values():
            directed = {}
            for k in faces:
                f = self.f[k]
                for a, b in zip(f, f[1:] + f[:1]):
                    directed[(a, b)] = directed.get((a, b), 0) + 1
            ok = all(c == 1 for c in directed.values()) and all(directed.get((b, a), 0) == 1 for (a, b) in directed)
            if not ok:
                continue
            closed += 1
            vol = 0.0
            for k in faces:
                f = self.f[k]
                p0 = self.v[f[0]]
                for j in range(1, len(f) - 1):
                    vol += vdot(p0, vcross(self.v[f[j]], self.v[f[j + 1]])) / 6.0
            if vol < 0:
                flipped += 1
                for k in faces:
                    self.f[k] = tuple(reversed(self.f[k]))
        return len(comps), closed, flipped

    def finish(self):
        self.compact()
        self.cull_twins()
        self.orient()
        return self

    def symmetrize(self):
        """self + its mirror in x, welded; faces lying exactly on x = 0 that meet their twin are removed."""
        both = Geo()
        both.add(self)
        both.add(self, mx=True)
        both.weld()
        both.cull_twins()
        self.v, self.f = both.v, both.f
        return self


class Piece:
    """suffix -> Geo."""

    def __init__(self):
        self.g = {}

    def geo(self, suffix):
        if suffix not in self.g:
            self.g[suffix] = Geo()
        return self.g[suffix]

    def add(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0, mx=False):
        for suffix, g in other.g.items():
            self.geo(suffix).add(g, t, yaw, s, mx)
        return self

    def mirrored(self):
        p = Piece()
        return p.add(self, mx=True)

    def symmetrize(self):
        for g in self.g.values():
            g.symmetrize()
        return self

    def resolve_overlaps(self, eps=0.004):
        """Two boxes with a face on the same plane, looking the same way, overlapping in area would z-fight: the later one grows that face outward by
        eps (more for each further conflict). Works across all the piece's materials; boxes that are not axis aligned are left alone."""
        info = []
        for g in self.g.values():
            for (b0, n) in g.boxes:
                pts = g.v[b0:b0 + 8]
                xs = sorted({round(p[0], 5) for p in pts})
                ys = sorted({round(p[1], 5) for p in pts})
                zs = sorted({round(p[2], 5) for p in pts})
                if len(xs) > 2 or len(ys) > 2 or len(zs) > 2:
                    continue
                info.append((g, b0, (xs[0], xs[-1], ys[0], ys[-1], zs[0], zs[-1])))
        grid = {}

        def cells(b):
            return [(i, j, k) for i in range(int(b[0] // 8), int(b[1] // 8) + 1) for j in range(int(b[2] // 8), int(b[3] // 8) + 1)
                    for k in range(int(b[4] // 8), int(b[5] // 8) + 1)]
        for idx, (g, b0, bb) in enumerate(info):
            for cell in cells(bb):
                grid.setdefault(cell, []).append(idx)
        grow = {}

        def key(i):
            bb = info[i][2]
            vol = (bb[1] - bb[0]) * (bb[3] - bb[2]) * (bb[5] - bb[4])
            return (round(vol, 4), round(abs(bb[0] + bb[1]) / 2, 4), round((bb[2] + bb[3]) / 2, 4), round((bb[4] + bb[5]) / 2, 4))
        for idx, (g, b0, bb) in enumerate(info):
            near = set()
            for cell in cells(bb):
                near.update(grid[cell])
            for jdx in sorted(near):
                if jdx >= idx:
                    continue
                a = info[jdx][2]
                for ax in range(3):
                    o1, o2 = [i for i in range(3) if i != ax]
                    ov1 = min(bb[2 * o1 + 1], a[2 * o1 + 1]) - max(bb[2 * o1], a[2 * o1])
                    ov2 = min(bb[2 * o2 + 1], a[2 * o2 + 1]) - max(bb[2 * o2], a[2 * o2])
                    if ov1 <= 1e-4 or ov2 <= 1e-4:
                        continue
                    for side in (0, 1):
                        if abs(bb[2 * ax + side] - a[2 * ax + side]) < 1.5e-3:
                            # the box with the smaller canonical key (smaller volume, then nearer the axis...) grows: mirror-symmetric choice
                            who = idx if key(idx) <= key(jdx) else jdx
                            grow[(who, ax, side)] = grow.get((who, ax, side), 0) + 1
        for (idx, ax, side), k in grow.items():
            g, b0, bb = info[idx]
            plane = bb[2 * ax + side]
            d = eps * k * (1 if side else -1)
            for i in range(b0, b0 + 8):
                p = list(g.v[i])
                if abs(p[ax] - plane) < 1e-5:
                    p[ax] += d
                    g.v[i] = tuple(p)
        return len(grow)

    def finish(self):
        self.resolve_overlaps()
        for g in self.g.values():
            g.finish()
        self.g = {k: g for k, g in self.g.items() if g.f}
        return self

    def weld(self):
        for g in self.g.values():
            g.weld()
        return self

    def tris(self):
        return sum(g.tris() for g in self.g.values())

    def stats(self):
        return {k: g.tris() for k, g in sorted(self.g.items())}

    def bounds(self):
        los, his = [], []
        for g in self.g.values():
            if g.v:
                lo, hi = g.bounds()
                los.append(lo)
                his.append(hi)
        return tuple(min(p[i] for p in los) for i in range(3)), tuple(max(p[i] for p in his) for i in range(3))


# ======================================================================================================================
# style
# ======================================================================================================================
class Style:
    """Materials (the suffixes of the exported pieces) and proportions of one headquarters. Edit a copy for another faction."""
    stone = "Marble"        # white stone: columns, tier faces, balustrades, steps
    stone2 = "Granite"      # plinths, column feet, kerbs, joints
    tile = "Tile"           # roof tiles
    gold = "Gold"
    goldflat = "GoldFlat"   # gold faces that look straight up
    paint = "Azure"         # beams, brackets, round rafters, door leaves, lattice
    wall = "Plaster"        # walls, flying rafters
    glow = "AzureGlow"      # small accents only
    crystal = "Crystal"
    rock = "Stone"
    cloth = "SilkBlue"
    cloth2 = "SilkWhite"
    water = "Pool"
    # roofs
    roof_k = 1.45           # slope curve exponent (concave: steeper toward the top)
    flick = 0.8             # the eave edge's upturn (studs)
    lift = 1.5              # corner lift (studs) of the eave line and the hip ridge's lower end
    flare = 1.0             # how far the corner pushes out along its diagonal (studs)
    lift_len = 11.0         # length of the eave over which the lift builds up (studs)
    shell = 0.8             # roof shell thickness (studs)
    pitch = 1.2             # tile-row pitch (studs)
    rib_h = 0.2
    # frame
    col_r0 = 0.85
    col_r1 = 0.72
    col_bulge = 0.07


# ======================================================================================================================
# raw solids
# ======================================================================================================================
_FACE = {"N": 0, "E": 1, "S": 2, "W": 3}


def hexa(g, b, y0, t, y1, faces="TB0123"):
    """A solid between a bottom ring `b` at y0 and a top ring `t` at y1 (4 (x, z) corners each, standard order p0=(x0,z0), p1=(x1,z0),
    p2=(x1,z1), p3=(x0,z1)). Faces: B, T, and sides 0..3 (N, E, S, W)."""
    bi = [g.vert((x, y0, z)) for x, z in b]
    ti = [g.vert((x, y1, z)) for x, z in t]
    if b == t:
        g.boxes.append((bi[0], 8))
    if "B" in faces:
        g.face(bi[0], bi[1], bi[2], bi[3])
    if "T" in faces:
        g.face(ti[3], ti[2], ti[1], ti[0])
    for i in range(4):
        if str(i) in faces:
            j = (i + 1) % 4
            g.face(bi[i], ti[i], ti[j], bi[j])


def _faces(faces):
    return "".join(str(_FACE[c]) if c in _FACE else c for c in faces)


def box(g, x0, x1, y0, y1, z0, z1, faces="TBNESW"):
    ring = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    hexa(g, ring, y0, ring, y1, _faces(faces))


def box_c(g, cx, cy, cz, sx, sy, sz, faces="TBNESW"):
    box(g, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, faces)


def prism(g, ring, y0, y1, caps="TB"):
    """Extrudes a convex polygon (list of (x, z)) from y0 to y1; caps are fans from the centroid."""
    area = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))
    if area < 0:
        ring = list(reversed(ring))
    n = len(ring)
    bi = [g.vert((x, y0, z)) for x, z in ring]
    ti = [g.vert((x, y1, z)) for x, z in ring]
    cx = sum(p[0] for p in ring) / n
    cz = sum(p[1] for p in ring) / n
    for i in range(n):
        j = (i + 1) % n
        g.face(bi[i], ti[i], ti[j], bi[j])
    if "B" in caps:
        c = g.vert((cx, y0, cz))
        for i in range(n):
            g.face(c, bi[i], bi[(i + 1) % n])
    if "T" in caps:
        c = g.vert((cx, y1, cz))
        for i in range(n):
            g.face(c, ti[(i + 1) % n], ti[i])


def lathe(g, prof, seg, cx=0.0, cz=0.0, phase=0.0, loop=False, caps=True):
    """Surface of revolution about the vertical axis through (cx, cz): prof = [(r, y), ...] from bottom to top. loop: the profile is a closed
    loop (a torus-like solid: no caps). Rings run counter-clockwise in (x, z) so sides face outward."""
    rings = []
    for r, y in prof:
        if r < 1e-9:
            rings.append(g.vert((cx, y, cz)))
        else:
            rings.append([g.vert((cx + r * math.cos(phase + TAU * k / seg), y, cz + r * math.sin(phase + TAU * k / seg))) for k in range(seg)])
    pairs = list(zip(range(len(prof)), range(1, len(prof))))
    if loop:
        pairs.append((len(prof) - 1, 0))
    for a, b in pairs:
        L, U = rings[a], rings[b]
        for k in range(seg):
            j = (k + 1) % seg
            if isinstance(L, int) and isinstance(U, int):
                continue
            if isinstance(L, int):
                g.face(L, U[k], U[j])
            elif isinstance(U, int):
                g.face(L[k], U, L[j])
            else:
                g.face(L[k], U[k], U[j], L[j])
    if caps and not loop:
        if not isinstance(rings[0], int):
            c = g.vert((cx, prof[0][1], cz))
            for k in range(seg):
                g.face(c, rings[0][k], rings[0][(k + 1) % seg])
        if not isinstance(rings[-1], int):
            c = g.vert((cx, prof[-1][1], cz))
            for k in range(seg):
                g.face(c, rings[-1][(k + 1) % seg], rings[-1][k])


def _volume(g, start):
    vol = 0.0
    for fi in range(start, len(g.f)):
        f = g.f[fi]
        p0 = g.v[f[0]]
        for j in range(1, len(f) - 1):
            vol += vdot(p0, vcross(g.v[f[j]], g.v[f[j + 1]])) / 6.0
    return vol


def _orient_solid(g, start):
    """Faces start.. of g form one closed solid: flip them all when their signed volume is negative."""
    if _volume(g, start) < 0:
        for k in range(start, len(g.f)):
            g.f[k] = tuple(reversed(g.f[k]))


def tube(g, centres, frames, section, caps=True, skip_bottom=False):
    """Sweeps a 2D section (list of (right, up) pairs, a closed polygon) along `centres`; frames[i] = (right, up) vectors at each centre (they may be
    scaled to taper). The solid orients itself outward; skip_bottom then removes the faces of the section's first edge (a rib sunk into a roof)."""
    start = len(g.f)
    rings = []
    for c, (rt, up) in zip(centres, frames):
        rings.append([g.vert(vadd(c, vadd(vmul(rt, a), vmul(up, b)))) for a, b in section])
    n = len(section)
    kill = []
    mx = sum(p[0] for p in section) / n
    my = sum(p[1] for p in section) / n
    # the end caps fan from the section's centroid (so a rib sunk into a roof shares no vertex with it)
    cap0 = vadd(centres[0], vadd(vmul(frames[0][0], mx), vmul(frames[0][1], my)))
    cap1 = vadd(centres[-1], vadd(vmul(frames[-1][0], mx), vmul(frames[-1][1], my)))
    for i in range(len(rings) - 1):
        for k in range(n):
            j = (k + 1) % n
            if k == 0:
                kill.append(len(g.f) - start)
            g.face(rings[i][k], rings[i + 1][k], rings[i + 1][j], rings[i][j])
    if caps:
        c0 = g.vert(cap0)
        c1 = g.vert(cap1)
        for k in range(n):
            j = (k + 1) % n
            if k == 0:
                kill.append(len(g.f) - start)
            g.face(c0, rings[0][k], rings[0][j])
            if k == 0:
                kill.append(len(g.f) - start)
            g.face(c1, rings[-1][j], rings[-1][k])
    _orient_solid(g, start)
    if skip_bottom:
        dead = set(kill)
        g.f[start:] = [f for idx, f in enumerate(g.f[start:]) if idx not in dead]


# ======================================================================================================================
# columns
# ======================================================================================================================
def pillar(st, h=10.0, r0=None, r1=None, foot=True, seg=12, detail=2):
    """Round column; the shaft runs from y = base to base + h with entasis (a swelling in the lower third). detail 2: a granite foot (square
    plinth + drum, 1 stud tall: the shaft starts at y = 1), five rings, two gold bands; 1: a box foot, four rings, a top band; 0: a bare shaft
    from y = 0 with three rings. Origin at the foot's bottom centre."""
    r0 = r0 or st.col_r0
    r1 = r1 or st.col_r1
    P = Piece()
    base = 1.0 if foot else 0.0
    if foot:
        g = P.geo(st.stone2)
        if detail >= 2:
            box(g, -1.5, 1.5, 0.0, 0.35, -1.5, 1.5, "TNESW")
            lathe(g, [(1.28, 0.35), (1.3, 0.5), (1.18, 0.74), (1.0, 0.92), (r0 + 0.03, base)], seg, caps=False)
        elif detail == 1:
            box(g, -1.4, 1.4, 0.0, 0.35, -1.4, 1.4, "TNESW")
            lathe(g, [(1.2, 0.35), (1.0, 0.8), (r0 + 0.03, base)], seg, caps=False)
        else:
            box(g, -1.15, 1.15, 0.0, base, -1.15, 1.15, "TNESW")
    g = P.geo(st.stone)
    n = {2: 5, 1: 4, 0: 3}[detail]
    prof = []
    for k in range(n):
        t = k / (n - 1)
        r = lerp(r0, r1, t) + st.col_bulge * math.sin(math.pi * t) * (1 - 0.35 * t)
        prof.append((r, base + (h - 0.03) * t))
    lathe(g, prof, seg, caps=True)
    if detail >= 2:
        gg = P.geo(st.gold)
        bands = ((base + 0.55, r0), (base + h - 0.55, r1)) if detail >= 2 else ((base + h - 0.5, r1),)
        for y, r in bands:
            lathe(gg, [(r - 0.04, y - 0.3), (r + 0.1, y), (r - 0.04, y + 0.3)], 8, loop=True)
    return P


def drum_foot_only(st, seg=12):
    return pillar(st, 0.01, foot=True, seg=seg, ring_gold=False)


# ======================================================================================================================
# bracket sets
# ======================================================================================================================
def _dou(g, cx, y0, cz, w, d, h, flare=0.2):
    """A block (dou): a slightly flared box."""
    hexa(g, [(cx - w / 2 + flare / 2, cz - d / 2 + flare / 2), (cx + w / 2 - flare / 2, cz - d / 2 + flare / 2),
             (cx + w / 2 - flare / 2, cz + d / 2 - flare / 2), (cx - w / 2 + flare / 2, cz + d / 2 - flare / 2)], y0,
         [(cx - w / 2, cz - d / 2), (cx + w / 2, cz - d / 2), (cx + w / 2, cz + d / 2), (cx - w / 2, cz + d / 2)], y0 + h, "TB0123")


def bracket_set(st, layers=3, w=1.6, h=2.2, reach=1.3, detail=2):
    """A bracket set (dougong) on a column head: a base block (width w), then `layers` pairs of crossing arms (one along the facade, x, with a half
    length of 0.6 to 1.0 times `reach` growing upward, so neighbouring sets never overlap when they are 2 * reach apart; one reaching out in front,
    -z) separated by small blocks; the top reach ends in an inclined lever arm cut to a point with a gold shoe, and a flat board closes the top.
    Origin at the centre of the block's bottom; height h. detail 2 has every block, 1 fewer."""
    P = Piece()
    g = P.geo(st.paint)
    gd = P.geo(st.gold)
    unit = h / (0.9 + layers * 0.95 + 0.25)
    y = 0.0
    bd = unit * 0.9
    _dou(g, 0, y - 0.03, 0, w, w, bd + 0.03)
    y += bd
    for L in range(layers):
        rx = reach * (0.6 + 0.4 * L / max(1, layers - 1)) if layers > 1 else reach
        rz = w * (1.3 + 0.62 * L)
        t = unit * 0.5
        aw = w * 0.5
        box(g, -rx, rx, y, y + t, -aw / 2, aw / 2)
        if L == layers - 1:
            hexa(g, [(-aw / 2, -rz), (aw / 2, -rz), (aw / 2, rz * 0.4), (-aw / 2, rz * 0.4)], y + 0.02,
                 [(-aw / 2, -rz - 0.5 * w), (aw / 2, -rz - 0.5 * w), (aw / 2, rz * 0.4), (-aw / 2, rz * 0.4)], y + t - 0.02, "TB123")
            box(gd, -aw / 2 - 0.03, aw / 2 + 0.03, y - 0.03, y + t + 0.03, -rz - 0.5 * w - 0.05, -rz - 0.5 * w + 0.14, "TBNESW")
        else:
            box(g, -aw / 2, aw / 2, y + 0.02, y + t - 0.02, -rz, rz * 0.4, "TBNEW")
        y += t
        sh = unit * 0.45
        bw = min(w * 0.42, rx * 0.5)
        for sx in (-rx + bw / 2, rx - bw / 2):
            _dou(g, sx, y, 0, bw, bw, sh, 0.1)
        if L < layers - 1:
            _dou(g, 0, y, 0, bw, bw, sh, 0.1)
            if detail >= 2:
                _dou(g, 0, y - 0.03, -rz + bw / 2, bw, bw, sh + 0.03, 0.1)
        y += sh
    rt = reach
    box(g, -rt, rt, y, y + unit * 0.25, -w * 0.18, w * 0.18, "TNESW")
    return P


# ======================================================================================================================
# lattice and doors
# ======================================================================================================================
def lattice(st, w, h, depth=0.3, nx=None, ny=None, bar=0.13, frame=0.3, pattern="grid", glow_back=False):
    """A lattice panel in the plane z = 0 (x from -w/2 to w/2, y from 0 to h), azure frame and bars with gold corner pieces. pattern: grid (square
    lattice), ice (a diagonal bar grid) or rings (a grid with a gold ring in the middle)."""
    P = Piece()
    g = P.geo(st.paint)
    gd = P.geo(st.gold)
    d2 = depth / 2
    box(g, -w / 2, w / 2, 0, frame, -d2, d2)
    box(g, -w / 2, w / 2, h - frame, h, -d2, d2)
    box(g, -w / 2, -w / 2 + frame, frame, h - frame, -d2, d2, "TBNESW")
    box(g, w / 2 - frame, w / 2, frame, h - frame, -d2, d2, "TBNESW")
    ix0, ix1, iy0, iy1 = -w / 2 + frame, w / 2 - frame, frame, h - frame
    nx = nx or max(2, int(round((ix1 - ix0) / 1.0)))
    ny = ny or max(2, int(round((iy1 - iy0) / 1.0)))
    bz = d2 * 0.55
    if pattern == "grid" or pattern == "rings":
        for i in range(1, nx):
            x = lerp(ix0, ix1, i / nx)
            box(g, x - bar / 2, x + bar / 2, iy0, iy1, -bz, bz, "TBNESW")
        for j in range(1, ny):
            y = lerp(iy0, iy1, j / ny)
            box(g, ix0, ix1, y - bar / 2, y + bar / 2, -bz * 0.8, bz * 0.8, "TBNESW")
    else:   # ice: two diagonal families clipped to the opening (each bar is a thin box cut by the rectangle's extent)
        step = 1.2
        span = (ix1 - ix0) + (iy1 - iy0)
        k = step
        while k < span:
            # a bar along (1, 1): from the opening's edge to its opposite edge
            for sgn in (1, -1):
                pts = []
                # parametrise: points where the line x - ix0 = sgn * (y - iy0) + k' hits the rectangle
                x_a, y_a = ix0 + k, iy0
                x_b, y_b = ix0, iy0 + k
                if sgn == 1:
                    ax, ay, bx, by = x_a, y_a, x_b, y_b
                else:
                    ax, ay, bx, by = ix1 - k, iy0, ix1, iy0 + k
                # clip to the rectangle
                def clip(ax, ay, bx, by):
                    dx, dy = bx - ax, by - ay
                    t0, t1 = 0.0, 1.0
                    for p_, q_ in ((-dx, ax - ix0), (dx, ix1 - ax), (-dy, ay - iy0), (dy, iy1 - ay)):
                        if abs(p_) < 1e-9:
                            if q_ < 0:
                                return None
                            continue
                        r = q_ / p_
                        if p_ < 0:
                            t0 = max(t0, r)
                        else:
                            t1 = min(t1, r)
                    if t0 >= t1:
                        return None
                    return (ax + dx * t0, ay + dy * t0, ax + dx * t1, ay + dy * t1)
                seg_ = clip(ax, ay, bx, by)
                if seg_:
                    x0_, y0_, x1_, y1_ = seg_
                    ln = math.hypot(x1_ - x0_, y1_ - y0_)
                    if ln > 0.3:
                        cx, cy = (x0_ + x1_) / 2, (y0_ + y1_) / 2
                        ang = math.atan2(y1_ - y0_, x1_ - x0_)
                        ca, sa = math.cos(ang), math.sin(ang)
                        hw = bar / 2
                        ring = [(cx - ca * ln / 2 - sa * hw, cy - sa * ln / 2 + ca * hw), (cx + ca * ln / 2 - sa * hw, cy + sa * ln / 2 + ca * hw),
                                (cx + ca * ln / 2 + sa * hw, cy + sa * ln / 2 - ca * hw), (cx - ca * ln / 2 + sa * hw, cy - sa * ln / 2 - ca * hw)]
                        _slab_xy(g, ring, -bz, bz)
            k += step
    # gold corner pieces
    cp = frame * 1.3
    for sx in (-1, 1):
        for sy in (0, 1):
            x = sx * (w / 2 - frame * 0.15)
            y = frame * 0.15 if sy == 0 else h - frame * 0.15
            box(gd, x - cp / 2, x + cp / 2, y - cp / 2, y + cp / 2, -d2 - 0.03, -d2 + 0.03 + 0.0, "TBNESW")
    if pattern == "rings":
        ym = h / 2
        gg = P.geo(st.gold)
        lathe_xy(gg, 0.0, ym, 0.9, 0.12, 0.06, 12, -d2 - 0.02)
    return P


def _slab_xy(g, ring, z0, z1):
    """A prism along z over a convex polygon in the xy plane."""
    n = len(ring)
    area = sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n))
    if area < 0:
        ring = list(reversed(ring))
    a = [g.vert((x, y, z0)) for x, y in ring]
    b = [g.vert((x, y, z1)) for x, y in ring]
    for i in range(n):
        j = (i + 1) % n
        g.face(a[i], a[j], b[j], b[i])
    g.face(*reversed(a))
    g.face(*b)


def lathe_xy(g, cx, cy, r_out, width, thick, seg, z0):
    """A flat ring (annulus) in the xy plane, centre (cx, cy), width `width`, its visible face at z0 - thick (it faces -z) and its back at z0 (closed)."""
    ro, ri = r_out, r_out - width
    start = len(g.f)

    def pt(r, k, z):
        return g.vert((cx + r * math.cos(TAU * k / seg), cy + r * math.sin(TAU * k / seg), z))
    o0 = [pt(ro, k, z0) for k in range(seg)]
    i0 = [pt(ri, k, z0) for k in range(seg)]
    o1 = [pt(ro, k, z0 - thick) for k in range(seg)]
    i1 = [pt(ri, k, z0 - thick) for k in range(seg)]
    for k in range(seg):
        j = (k + 1) % seg
        g.face(o1[k], i1[k], i1[j], o1[j])
        g.face(o0[k], o1[k], o1[j], o0[j])
        g.face(i0[j], i1[j], i1[k], i0[k])
        g.face(o0[j], i0[j], i0[k], o0[k])
    _orient_solid(g, start)


def door_leaf(st, w, h, thick=0.45, studs=(2, 5)):
    """A panelled door leaf in the plane z = 0, hinge at x = 0 (the leaf runs to +x), azure with gold studs and a ring pull. The front is -z."""
    P = Piece()
    g = P.geo(st.paint)
    gd = P.geo(st.gold)
    t2 = thick / 2
    stile, rail = 0.55, 0.6
    box(g, 0, stile, 0, h, -t2, t2)
    box(g, w - stile, w, 0, h, -t2, t2)
    box(g, stile, w - stile, 0, rail, -t2, t2)
    box(g, stile, w - stile, h - rail, h, -t2, t2)
    # the middle rail and the two panels (lower solid with a raised centre, upper lattice-look bars)
    mid = h * 0.62
    box(g, stile, w - stile, mid - rail / 2, mid + rail / 2, -t2, t2)
    box(g, stile, w - stile, rail, mid - rail / 2, -t2 * 0.55, t2 * 0.55)
    box(g, stile + 0.35, w - stile - 0.35, rail + 0.35, mid - rail / 2 - 0.35, -t2 - 0.05, -t2 * 0.55, "TBNEW")
    bars = 4
    for i in range(1, bars):
        x = lerp(stile, w - stile, i / bars)
        box(g, x - 0.07, x + 0.07, mid + rail / 2, h - rail, -t2 * 0.6, t2 * 0.6, "TBNESW")
    box(g, stile, w - stile, mid + rail / 2, mid + rail / 2 + 0.01, -t2 * 0.6, t2 * 0.6, "T")
    # studs on the lower panel
    nx, ny = studs
    for i in range(nx):
        for j in range(ny):
            x = lerp(stile + 0.55, w - stile - 0.55, (i + 0.5) / nx if nx > 1 else 0.5)
            y = lerp(rail + 0.7, mid - rail / 2 - 0.7, (j + 0.5) / ny if ny > 1 else 0.5)
            _stud(gd, x, y, -t2 - 0.05)
    # the ring pull near the free edge
    lathe_xy(gd, w - stile - 0.55, mid - rail / 2 - 0.9, 0.42, 0.1, 0.1, 10, -t2 - 0.1)
    return P


def _stud(g, x, y, z):
    """A small gold dome stud on a face looking -z (a square pyramid)."""
    r, hgt = 0.16, 0.13
    a = [g.vert((x - r, y - r, z)), g.vert((x + r, y - r, z)), g.vert((x + r, y + r, z)), g.vert((x - r, y + r, z))]
    apex = g.vert((x, y, z - hgt))
    for i in range(4):
        j = (i + 1) % 4
        g.face(a[j], a[i], apex)


# ======================================================================================================================
# roofs
# ======================================================================================================================
def _surface(st, face, A, D, at, dt, ye, yt, u, s, k=None, flick=None, lift=None, flare=None, lift_len=None):
    """The roof's upper surface at (u along the face's eave from its first corner, s from the eave to the top): a point (x, y, z)."""
    k = st.roof_k if k is None else k
    flick = st.flick if flick is None else flick
    lift = st.lift if lift is None else lift
    flare = st.flare if flare is None else flare
    lift_len = st.lift_len if lift_len is None else lift_len
    E = [((-A, -D), (A, -D)), ((A, -D), (A, D)), ((A, D), (-A, D)), ((-A, D), (-A, -D))][face]
    T = [((-at, -dt), (at, -dt)), ((at, -dt), (at, dt)), ((at, dt), (-at, dt)), ((-at, dt), (-at, -dt))][face]
    ex, ez = lerp(E[0][0], E[1][0], u), lerp(E[0][1], E[1][1], u)
    tx, tz = lerp(T[0][0], T[1][0], u), lerp(T[0][1], T[1][1], u)
    hx, hz = lerp(ex, tx, s), lerp(ez, tz, s)
    y = ye + (yt - ye) * (s ** k)
    fs = 0.12
    if s < fs:
        y += flick * (1 - s / fs) ** 2
    L = math.hypot(E[1][0] - E[0][0], E[1][1] - E[0][1])
    dc = min(u, 1 - u) * L
    Lc = min(0.45 * L, lift_len)
    w = max(0.0, 1 - dc / Lc) ** 2
    y += lift * w * (1 - s) ** 3
    corner = E[0] if u < 0.5 else E[1]
    cn = math.hypot(corner[0], corner[1]) or 1.0
    fl = flare * w * (1 - s) ** 2
    hx += corner[0] / cn * fl
    hz += corner[1] / cn * fl
    return (hx, y, hz)


def _u_samples(n_mid=5):
    mids = [i / (n_mid + 1) for i in range(1, n_mid + 1)]
    ends = [0.0, 0.03, 0.08, 0.15, 0.25]
    left = ends
    right = [1 - e for e in reversed(ends)]
    out = sorted(set(left + [m for m in mids if 0.25 < m < 0.75] + right))
    return out


S_SAMPLES = [0.0, 0.04, 0.10, 0.20, 0.35, 0.55, 0.78, 1.0]


def roof(st, A, D, at, dt, ye, yt, detail=2, pitch=None, corner_horns=True, ridge_gold=True, rib_h=None, shell=None, finial=0.0, ridge_horns=True,
         rafters=True, discs=True, ribs=True, **curve):
    """A tiled hip roof: the eave tip rectangle (half sizes A x D, height ye) rises through an S-curved slope to the top rectangle (at x dt, height
    yt). at = dt = 0 gives a pyramid; dt = 0 a ridge along x. Returns a Piece in the tiers' own frame (x across, z deep, centred on the axis).
    Roles: tile (the shell, ribs, eave-end tiles), paint (soffit, round rafters), wall (flying rafters), gold (hip ridge caps, corner horns,
    ridge, finial)."""
    P = Piece()
    pitch = pitch or st.pitch
    rib_h = rib_h or st.rib_h
    shell = shell or st.shell
    gt = P.geo(st.tile)
    gp = P.geo(st.paint)
    gw = P.geo(st.wall)
    gg = P.geo(st.gold)
    if detail >= 2:
        us, ss = _u_samples(6), S_SAMPLES
    elif detail == 1:
        us, ss = _u_samples(4), [0.0, 0.06, 0.18, 0.4, 0.7, 1.0]
    else:
        us, ss = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0], [0.0, 0.12, 0.45, 1.0]

    def S(face, u, s):
        return _surface(st, face, A, D, at, dt, ye, yt, u, s, **curve)

    def under(p, s):
        return (p[0], p[1] - shell * (1 - 0.25 * s), p[2])

    # ---- the shell: top, underside, eave band, top rim (welded on its own: the four faces meet at the hip lines)
    sh = Geo()
    for face in range(4):
        T_ = [[sh.vert(S(face, u, s)) for s in ss] for u in us]
        U_ = [[sh.vert(under(S(face, u, s), s)) for s in ss] for u in us]
        for i in range(len(us) - 1):
            for j in range(len(ss) - 1):
                sh.face(T_[i][j], T_[i][j + 1], T_[i + 1][j + 1], T_[i + 1][j])
                sh.face(U_[i][j], U_[i + 1][j], U_[i + 1][j + 1], U_[i][j + 1])
            sh.face(T_[i][0], T_[i + 1][0], U_[i + 1][0], U_[i][0])
            sh.face(T_[i + 1][-1], T_[i][-1], U_[i][-1], U_[i + 1][-1])
    sh.weld()
    sh.cull_twins()
    gt.add(sh)
    # ---- tile rows (ribs) and the round eave-end tiles
    def face_len(face):
        E = [((-A, -D), (A, -D)), ((A, -D), (A, D)), ((A, D), (-A, D)), ((-A, D), (-A, -D))][face]
        T = [((-at, -dt), (at, -dt)), ((at, -dt), (at, dt)), ((at, dt), (-at, dt)), ((-at, dt), (-at, -dt))][face]
        return math.hypot(E[1][0] - E[0][0], E[1][1] - E[0][1]), math.hypot(T[1][0] - T[0][0], T[1][1] - T[0][1])
    for face in range(4 if ribs else 0):
        Le, Lt = face_len(face)
        n = max(3, int(round(Le / pitch)))
        # the rows stop where they would crowd each other (a hip end narrows to a point)
        s_end = 0.0
        for s_try in [x / 100 for x in range(100, -1, -2)]:
            if (Le + (Lt - Le) * s_try) / n >= 0.6:
                s_end = s_try
                break
        if s_end < 0.2:
            continue
        top_s = s_end - 0.02
        rs = [top_s * q for q in ((0.0, 0.1, 0.28, 0.55, 1.0) if detail >= 2 else (0.0, 0.18, 0.5, 1.0))]
        for j in range(n):
            u = (j + 0.5) / n
            pts = [S(face, u, s) for s in rs]
            frames = []
            for q in range(len(rs)):
                p_prev = S(face, u, max(0.0, rs[q] - 0.02))
                p_next = S(face, u, min(1.0, rs[q] + 0.02))
                along = vnorm(vsub(p_next, p_prev))
                du = vsub(S(face, min(1.0, u + 0.004), rs[q]), S(face, max(0.0, u - 0.004), rs[q]))
                nrm = vnorm(vcross(du, along))
                if nrm[1] < 0:
                    nrm = vmul(nrm, -1)
                right = vnorm(vcross(along, nrm))
                frames.append((right, nrm))
            tube(gt, pts, frames, [(-0.27, -0.05), (0.27, -0.05), (0.0, rib_h)], caps=True, skip_bottom=True)
            if discs:
                p0 = S(face, u, 0.0)
                p1 = S(face, u, 0.05)
                tdir = vnorm(vsub(p0, p1))
                _eave_disc(gt, p0, tdir, frames[0][1], 0.3, detail)
            if rafters and detail >= 2:
                # a round rafter under the shell (azure): a thin triangular bar
                q0 = under(S(face, u, 0.0), 0.0)
                q1 = under(S(face, u, 0.34), 0.34)
                a_dir = vnorm(vsub(q1, q0))
                rt = vnorm(vcross(a_dir, (0.0, 1.0, 0.0)))
                dn = vnorm(vcross(a_dir, rt))
                if dn[1] > 0:
                    dn = vmul(dn, -1)
                tube(gp, [q0, q1], [(rt, dn)] * 2, [(-0.16, 0.0), (0.16, 0.0), (0.0, 0.3)], caps=True, skip_bottom=True)
    # ---- gold hip ridges (caps) and the corner horns
    if ridge_gold:
        for face in range(4):
            if True:
                u = 0.0
                ss_h = [0.0, 0.05, 0.14, 0.3, 0.55, 0.8, 1.0] if detail >= 1 else [0.0, 0.2, 0.55, 1.0]
                pts, frames = [], []
                for s in ss_h:
                    p = S(face, u, s)
                    p_prev = S(face, u, max(0.0, s - 0.02))
                    p_next = S(face, u, min(1.0, s + 0.02))
                    along = vnorm(vsub(p_next, p_prev))
                    up = (0.0, 1.0, 0.0)
                    right = vnorm(vcross(along, up))
                    upn = vnorm(vcross(right, along))
                    if upn[1] < 0:
                        upn = vmul(upn, -1)
                    pts.append(vadd(p, vmul(upn, -0.06)))
                    frames.append((right, upn))
                width = 0.8
                sect = [(-width / 2, 0.0), (width / 2, 0.0), (0.0, 0.52)]
                start = len(gg.f)
                tube(gg, pts, frames, sect, caps=True)
                if corner_horns and detail >= 1:
                    _corner_horn(gg, S(face, 0.0, 0.0), S(face, 0.0, 0.03), st)
    if finial and at == 0 and dt == 0:
        _finial(gg, (0.0, yt, 0.0), finial)
    # ridge along x (dt = 0 and at > 0): a gold ridge cap with plain upswept ends
    if dt == 0 and at > 0 and ridge_gold:
        y_r = yt + 0.05
        n = 9
        pts = [(lerp(-at, at, i / (n - 1)), y_r, 0.0) for i in range(n)]
        frames = [((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))] * n
        # a roll-top ridge: wider and taller than the hip caps
        start = len(gg.f)
        box(gg, -at, at, y_r - 0.1, y_r + 0.7, -0.55, 0.55, "TBNESW")
        if ridge_horns:
            for sx in (-1, 1):
                _ridge_end(gg, (sx * at, y_r + 0.7, 0.0), sx)
    return P


def _eave_disc(g, p, tdir, nrm, r, detail):
    """A round eave-end tile (wadang): a hexagonal disc facing along tdir (outward and down the slope) with a low pyramid boss on its face."""
    up = vnorm(vsub((0.0, 1.0, 0.0), vmul(tdir, tdir[1])))
    rt = vnorm(vcross(tdir, up))
    c = vadd(p, vadd(vmul(up, 0.0), vmul(tdir, 0.04)))
    seg = 6
    thick = 0.16
    front, back = [], []
    for k in range(seg):
        a = TAU * k / seg + math.pi / seg
        d = vadd(vmul(rt, math.cos(a) * r), vmul(up, math.sin(a) * r))
        front.append(g.vert(vadd(c, vadd(d, vmul(tdir, thick / 2)))))
        back.append(g.vert(vadd(c, vadd(d, vmul(tdir, -thick / 2)))))
    apex = g.vert(vadd(c, vmul(tdir, thick / 2 + 0.1)))
    bc = g.vert(vadd(c, vmul(tdir, -thick / 2)))
    start = len(g.f)
    for k in range(seg):
        j = (k + 1) % seg
        g.face(apex, front[k], front[j])
    for k in range(seg):
        j = (k + 1) % seg
        g.face(front[k], back[k], back[j], front[j])
    for k in range(seg):
        j = (k + 1) % seg
        g.face(bc, back[j], back[k])
    _orient_solid(g, start)
    del g.f[len(g.f) - seg:]         # the back cap sits against the roof: dropped


def _corner_horn(g, p0, p1, st):
    """A gold upswept horn at a hip ridge's lower end: a tapering curved curl (no beast, no face), p0 the eave corner, p1 a point up the ridge."""
    along = vnorm(vsub(p0, p1))
    out = vnorm((along[0], 0.0, along[2]))
    n = 6
    pts, frames = [], []
    for i in range(n):
        t = i / (n - 1)
        pts.append(vadd(p0, vadd(vmul(out, -0.1 + 2.2 * t ** 0.9), (0.0, -0.12 + 2.2 * t ** 1.7 + 0.3 * t, 0.0))))
    for i in range(n):
        tg = vnorm(vsub(pts[min(i + 1, n - 1)], pts[max(i - 1, 0)]))
        rt = vnorm(vcross(tg, (0.0, 1.0, 0.0)))
        upn = vnorm(vcross(rt, tg))
        if upn[1] < 0:
            upn = vmul(upn, -1)
        t = i / (n - 1)
        sc = 0.5 * (1 - t) ** 0.75 + 0.05
        frames.append((vmul(rt, sc), vmul(upn, sc)))
    tube(g, pts, frames, [(-1.0, -0.9), (1.0, -0.9), (0.55, 0.9), (-0.55, 0.9)], caps=True)


def _ridge_end(g, p, sx):
    """The plain upswept end of a main ridge (a gold curl, no beast)."""
    n = 6
    pts, frames = [], []
    for i in range(n):
        t = i / (n - 1)
        pts.append(vadd(p, ((sx * (-0.4 + 1.6 * t * t)), -0.55 + 3.1 * t ** 0.9, 0.0)))
    for i in range(n):
        tg = vnorm(vsub(pts[min(i + 1, n - 1)], pts[max(i - 1, 0)]))
        rt = (0.0, 0.0, 1.0)
        upn = vnorm(vcross(rt, tg))
        if vdot(upn, (-sx, 0.0, 0.0)) < 0:
            upn = vmul(upn, -1)
        t = i / (n - 1)
        sc = 0.5 * (1 - t) ** 0.7 + 0.04
        frames.append((vmul(rt, sc), vmul(upn, sc)))
    start = len(g.f)
    tube(g, pts, frames, [(-1.0, -0.8), (1.0, -0.8), (0.7, 0.8), (-0.7, 0.8)], caps=True)


def _finial(g, base, h):
    """A gold stacked-gourd finial (baoding) on a pyramid roof's apex: base disc, two bulbs, a neck, a point."""
    x, y, z = base
    s = h / 4.0
    prof = [(0.0, y), (0.9 * s, y), (0.9 * s, y + 0.12 * s), (0.5 * s, y + 0.25 * s), (0.35 * s, y + 0.5 * s), (0.7 * s, y + 0.95 * s),
            (0.82 * s, y + 1.4 * s), (0.5 * s, y + 1.85 * s), (0.3 * s, y + 2.05 * s), (0.5 * s, y + 2.4 * s), (0.55 * s, y + 2.9 * s),
            (0.25 * s, y + 3.4 * s), (0.0, y + 4.0 * s)]
    lathe(g, prof, 8, cx=x, cz=z, caps=False)


# ======================================================================================================================
# balustrades, lanterns, banners
# ======================================================================================================================
def balustrade(st, L, h=2.6, post_every=4.0, thick=0.9):
    """Marble panel balustrade along +x from 0 to L (centre line z = 0): a foot rail, panels with a recessed centre between posts, a top rail and a
    gold lotus-bud cap on each post (a stacked round form). Posts at both ends and every `post_every`."""
    P = Piece()
    g = P.geo(st.stone)
    gd = P.geo(st.gold)
    n = max(1, int(round(L / post_every)))
    t2 = thick / 2
    pw = 0.7
    for i in range(n + 1):
        x = L * i / n
        box(g, x - pw / 2, x + pw / 2, 0.0, h - 0.55, -pw / 2, pw / 2, "TNESW")
        # the lotus-bud cap: a gold lathe
        prof = [(0.56, h - 0.55), (0.4, h - 0.25), (0.46, h + 0.1), (0.0, h + 0.62)]
        lathe(gd, prof, 6, cx=x, cz=0.0, caps=False)
    for i in range(n):
        x0 = L * i / n + pw / 2
        x1 = L * (i + 1) / n - pw / 2
        box(g, x0, x1, 0.0, 0.45, -t2, t2, "TNESW")                      # foot rail
        box(g, x0, x1, h - 1.0, h - 0.55, -t2 * 0.9, t2 * 0.9, "TNESW")  # top rail
        # the panel: a frame with a recessed centre
        box(g, x0, x1, 0.45, h - 1.0, -t2 * 0.45, t2 * 0.45, "TNESW")
        box(g, x0 + 0.25, x1 - 0.25, 0.7, h - 1.25, -t2 * 0.62, -t2 * 0.45, "TBN")
        box(g, x0 + 0.25, x1 - 0.25, 0.7, h - 1.25, t2 * 0.45, t2 * 0.62, "TBS")
    return P


def lantern(st, h=9.0, glow=True):
    """A stone pedestal lantern (origin: bottom centre): a stepped square base, a round shaft with a collar, an octagonal lamp house (four stone posts
    round an azure glow core), a small tiled roof with a gold finial. Marble and granite, gold rings, azure glow core (small)."""
    P = Piece()
    g = P.geo(st.stone)
    g2 = P.geo(st.stone2)
    gd = P.geo(st.gold)
    gt = P.geo(st.tile)
    box(g2, -1.25, 1.25, 0.0, 0.5, -1.25, 1.25, "TNESW")
    box(g, -0.95, 0.95, 0.5, 0.95, -0.95, 0.95, "TNESW")
    y_sh0, y_sh1 = 0.95, h * 0.55
    lathe(g, [(0.62, y_sh0), (0.4, y_sh0 + 1.2), (0.38, (y_sh0 + y_sh1) / 2), (0.62, y_sh1 - 0.3), (0.62, y_sh1)], 8, caps=False)
    lathe(gd, [(0.36, y_sh0 + 1.5), (0.5, y_sh0 + 1.65), (0.36, y_sh0 + 1.8)], 8, loop=True)
    yl0 = y_sh1
    prism(g, [(1.5 * math.cos(TAU * k / 8 + math.pi / 8), 1.5 * math.sin(TAU * k / 8 + math.pi / 8)) for k in range(8)], yl0, yl0 + 0.4, "T")
    house_h = h * 0.2
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(g, sx * 1.1 - 0.22, sx * 1.1 + 0.22, yl0 + 0.4, yl0 + 0.4 + house_h, sz * 1.1 - 0.22, sz * 1.1 + 0.22, "TNESW")
    if glow:
        gg = P.geo(st.glow)
        prism(gg, [(1.02 * math.cos(TAU * k / 8 + math.pi / 8), 1.02 * math.sin(TAU * k / 8 + math.pi / 8)) for k in range(8)], yl0 + 0.3, yl0 + 0.2 + house_h, "TB")
    yr = yl0 + 0.4 + house_h
    rr = 2.1
    top_y = yr + 1.3
    ring0 = [(rr * math.cos(TAU * k / 8 + math.pi / 8), rr * math.sin(TAU * k / 8 + math.pi / 8)) for k in range(8)]
    b = [gt.vert((x, yr + 0.12, z)) for x, z in ring0]
    b2 = [gt.vert((x * 0.8, yr - 0.1, z * 0.8)) for x, z in ring0]
    mid = [gt.vert((x * 0.62, yr + 0.45, z * 0.62)) for x, z in ring0]
    top = gt.vert((0.0, top_y, 0.0))
    ctr = gt.vert((0.0, yr - 0.1, 0.0))
    for k in range(8):
        j = (k + 1) % 8
        gt.face(b[k], mid[k], mid[j], b[j])
        gt.face(mid[k], top, mid[j])
        gt.face(b2[k], b[k], b[j], b2[j])
        gt.face(ctr, b2[k], b2[j])
    lathe(gd, [(0.34, top_y - 0.3), (0.26, top_y + 0.1), (0.34, top_y + 0.4), (0.0, top_y + 0.95)], 6, caps=False)
    return P


def banner(st, w, h, rod_over=0.9, two_sided=False, wave=0.05):
    """A hanging cloth banner (origin: the middle of the top rod; hangs down to y = -h; the front is -z): blue cloth with a gentle ripple, a white border
    and the crest in white, a gold top rod with end caps, a gold bottom bar and three tassels."""
    P = Piece()
    c = P.geo(st.cloth)
    cw = P.geo(st.cloth2)
    gd = P.geo(st.gold)
    nx, ny = 4, 10
    t = 0.2

    def zf(x, y):
        return wave * math.sin(y * 0.55 + 0.7) * (0.35 + 0.65 * (-y / h)) * math.cos(x * 0.45)
    front = [[c.vert((lerp(-w / 2, w / 2, i / nx), -h * j / ny, zf(lerp(-w / 2, w / 2, i / nx), -h * j / ny))) for j in range(ny + 1)] for i in range(nx + 1)]
    back = [[c.vert((lerp(-w / 2, w / 2, i / nx), -h * j / ny, zf(lerp(-w / 2, w / 2, i / nx), -h * j / ny) + t)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            c.face(front[i][j], front[i + 1][j], front[i + 1][j + 1], front[i][j + 1])
            c.face(back[i][j], back[i][j + 1], back[i + 1][j + 1], back[i + 1][j])
    for j in range(ny):
        c.face(front[0][j], front[0][j + 1], back[0][j + 1], back[0][j])
        c.face(front[nx][j], back[nx][j], back[nx][j + 1], front[nx][j + 1])
    for i in range(nx):
        c.face(front[i][0], back[i][0], back[i + 1][0], front[i + 1][0])
        c.face(front[i][ny], front[i + 1][ny], back[i + 1][ny], back[i][ny])
    # white border: thin strips just in front of the cloth (0.03), following the ripple at their centre lines
    bw = 0.42
    inset = 0.55
    def strip(x0, x1, y0, y1):
        zc = zf((x0 + x1) / 2, (y0 + y1) / 2)
        box(cw, x0, x1, y0, y1, zc - 0.095, zc + 0.045, "TBNESW")
    strip(-w / 2 + inset, -w / 2 + inset + bw, -h + inset + 0.2, -inset)
    strip(w / 2 - inset - bw, w / 2 - inset, -h + inset + 0.2, -inset)
    strip(-w / 2 + inset, w / 2 - inset, -inset - bw, -inset)
    strip(-w / 2 + inset, w / 2 - inset, -h + inset + 0.2, -h + inset + 0.2 + bw)
    # the crest in white, centred a little above the middle
    R = min(w * 0.3, h * 0.17)
    cy = -h * 0.42
    crest(cw, st, R, (0.0, cy, zf(0.0, cy) - 0.03), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0), 0.045, sink=0.05)
    # the rod, caps, the bottom bar and tassels
    lathe_x(gd, -w / 2 - rod_over * 0.5, w / 2 + rod_over * 0.5, 0.0, 0.1, 0.22, 8)
    for sx in (-1, 1):
        x = sx * (w / 2 + rod_over * 0.5)
        prof_x = [(0.0, 0.0), (0.3, 0.0), (0.3, 0.1), (0.2, 0.3), (0.0, 0.5)]
        lathe_axis_x(gd, x, 0.0, 0.1, prof_x, sx)
    lathe_x(gd, -w / 2 + 0.2, w / 2 - 0.2, -h - 0.1, 0.1, 0.16, 8)
    for i in range(3):
        x = lerp(-w / 2 + 0.9, w / 2 - 0.9, i / 2)
        box(gd, x - 0.12, x + 0.12, -h - 0.55, -h - 0.1, 0.0, 0.2, "TBNESW")
        box(cw, x - 0.1, x + 0.1, -h - 1.8, -h - 0.55, 0.02, 0.18, "TBNESW")
    return P


def lathe_x(g, x0, x1, y, z, r, seg):
    """A cylinder along x from x0 to x1 at (y, z)."""
    rings = []
    for x in (x0, x1):
        rings.append([g.vert((x, y + r * math.cos(TAU * k / seg), z + r * math.sin(TAU * k / seg))) for k in range(seg)])
    for k in range(seg):
        j = (k + 1) % seg
        g.face(rings[0][k], rings[0][j], rings[1][j], rings[1][k])
    c0 = g.vert((x0, y, z))
    c1 = g.vert((x1, y, z))
    for k in range(seg):
        j = (k + 1) % seg
        g.face(c0, rings[0][j], rings[0][k])
        g.face(c1, rings[1][k], rings[1][j])


def lathe_axis_x(g, x, y, z, prof, sx):
    """A lathe about an axis parallel to x through (y, z), starting at x, profile (r, along) with along going outward (sx = +1 or -1)."""
    seg = 8
    rings = []
    for r, a in prof:
        if r < 1e-9:
            rings.append(g.vert((x + sx * a, y, z)))
        else:
            rings.append([g.vert((x + sx * a, y + r * math.cos(TAU * k / seg), z + r * math.sin(TAU * k / seg))) for k in range(seg)])
    start = len(g.f)
    for a, b in zip(range(len(prof)), range(1, len(prof))):
        L, U = rings[a], rings[b]
        for k in range(seg):
            j = (k + 1) % seg
            if isinstance(U, int):
                g.face(L[k], L[j], U)
            elif isinstance(L, int):
                g.face(L, U[j], U[k])
            else:
                g.face(L[k], L[j], U[j], U[k])
    if not isinstance(rings[0], int):
        c = g.vert((x, y, z))
        for k in range(seg):
            g.face(c, rings[0][(k + 1) % seg], rings[0][k])
    _orient_solid(g, start)


# ======================================================================================================================
# the crest
# ======================================================================================================================
SINK = 0.0


def crest(g, st, R, origin, U, V, N, thick, sink=0.0):
    """The faction's original crest, as relief on a plane: two concentric rings, three rising blades (the middle one tallest, breaking through the
    inner ring) on a short ground bar. origin = its centre; U, V the plane's right and up unit vectors; N points toward the viewer; thick = relief
    height. Built from flat prisms: nothing on it reads as a face, a letter or a body part."""
    SINK = sink

    def P3(u, v, w=0.0):
        return vadd(origin, vadd(vmul(U, u * R), vadd(vmul(V, v * R), vmul(N, w))))

    def prism2(poly, w0, w1):
        n = len(poly)
        area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        if area < 0:
            poly = list(reversed(poly))
        a = [g.vert(P3(u, v, w0)) for u, v in poly]
        b = [g.vert(P3(u, v, w1)) for u, v in poly]
        start = len(g.f)
        for i in range(n):
            j = (i + 1) % n
            g.face(a[i], a[j], b[j], b[i])
        g.face(*reversed(a))
        g.face(*b)
        # the top (b) face should look along N
        f = g.f[len(g.f) - 1]
        p = [g.v[i] for i in f[:3]]
        nn = vcross(vsub(p[1], p[0]), vsub(p[2], p[0]))
        if vdot(nn, N) < 0:
            for k in range(start, len(g.f)):
                g.f[k] = tuple(reversed(g.f[k]))

    def ring(r_in, r_out, w1, seg=20):
        lt = Geo()
        lathe(lt, [(r_in * R, -SINK), (r_out * R, -SINK), (r_out * R, w1), (r_in * R, w1)], seg, loop=True)
        base = len(g.v)
        start = len(g.f)
        for (x, y, z) in lt.v:
            g.v.append(vadd(origin, vadd(vmul(U, x), vadd(vmul(V, z), vmul(N, y)))))
        for f in lt.f:
            g.f.append(tuple(i + base for i in f))
        _orient_solid(g, start)

    ring(0.90, 1.00, thick)
    ring(0.70, 0.76, thick)

    def blade(cx, base_v, apex_v, half_w, tilt_deg):
        t = math.radians(tilt_deg)
        h = apex_v - base_v
        pts = [(0.0, 0.0), (-half_w, 0.3 * h), (0.0, h), (half_w, 0.3 * h)]
        out = []
        for x, y in pts:
            xr = x * math.cos(t) - y * math.sin(t)
            yr = x * math.sin(t) + y * math.cos(t)
            out.append((cx + xr, base_v + yr))
        return out
    prism2(blade(0.0, -0.50, 0.86, 0.17, 0.0), -SINK - 0.012, thick * 1.8)
    prism2(blade(-0.40, -0.50, 0.40, 0.14, 13.0), -SINK - 0.024, thick * 1.5)
    prism2(blade(0.40, -0.50, 0.40, 0.14, -13.0), -SINK - 0.024, thick * 1.5)
    prism2([(-0.62, -0.60), (0.62, -0.60), (0.58, -0.52), (-0.58, -0.52)], -SINK - 0.048, thick * 1.2)


# ======================================================================================================================
# floors and stone
# ======================================================================================================================
def paving(st, x0, x1, z0, z1, y_top=0.0, depth=1.2, slab=4.0):
    """A paved floor: a marble slab (open underneath) with dark granite joints every `slab` studs (raised 0.03)."""
    P = Piece()
    g = P.geo(st.stone)
    box(g, x0, x1, y_top - depth, y_top, z0, z1, "TNESW")
    j = P.geo(st.stone2)
    nx = max(1, int(round((x1 - x0) / slab)))
    nz = max(1, int(round((z1 - z0) / slab)))
    for i in range(1, nx):
        x = lerp(x0, x1, i / nx)
        box(j, x - 0.07, x + 0.07, y_top - 0.02, y_top + 0.03, z0, z1, "TNESW")
    for k in range(1, nz):
        z = lerp(z0, z1, k / nz)
        box(j, x0, x1, y_top - 0.02, y_top + 0.04, z - 0.07, z + 0.07, "TNESW")
    return P


def _noise(x, y, z, seed):
    h = math.sin(x * 12.9898 + y * 78.233 + z * 37.719 + seed * 4.1414) * 43758.5453
    return h - math.floor(h)


def rock_mound(st, ring, y0, y1, levels=5, seed=1, jitter=0.9, inset=2.5, ledge=0.7, top_flat=0.6):
    """A layered rock mass over the outline `ring` ((x, z) list, counter-clockwise): `levels` strata from y0 up to y1, each ring pulled in by `inset`
    in all and shifted by hashed noise on |x| (so a mirror copy matches), alternate strata pushed out by `ledge`; the top is a fan to the centroid
    raised a little. Open underneath. Role: rock."""
    P = Piece()
    g = P.geo(st.rock)
    cx = sum(p[0] for p in ring) / len(ring)
    cz = sum(p[1] for p in ring) / len(ring)
    rings = []
    for lv in range(levels + 1):
        t = lv / levels
        y = lerp(y0, y1, t)
        shrink = inset * (t ** 1.2) + (ledge if lv % 2 == 1 else 0.0) * (1 - t) * -1.0
        row = []
        for i, (x, z) in enumerate(ring):
            dx, dz = x - cx, z - cz
            d = math.hypot(dx, dz) or 1.0
            n = _noise(abs(x), lv, z, seed)
            k = (d - shrink + (n - 0.5) * 2 * jitter * (0.4 + t)) / d
            dy = (_noise(abs(x), lv + 9, z, seed) - 0.5) * 0.6 * (t < 1.0)
            row.append(g.vert((cx + dx * k, y + dy if lv not in (0,) else y, cz + dz * k)))
        rings.append(row)
    n = len(ring)
    for lv in range(levels):
        for i in range(n):
            j = (i + 1) % n
            g.face(rings[lv][i], rings[lv + 1][i], rings[lv + 1][j], rings[lv][j])
    top = rings[-1]
    c = g.vert((cx, y1 + top_flat, cz))
    for i in range(n):
        j = (i + 1) % n
        g.face(c, top[j], top[i])
    return P


def spire(st, base_y=0.0, crystal_h=15.0, ring_r=9.0):
    """A faceted crystal spire in a gold lotus cradle with two halo rings (a gold ring standing in the xy plane behind the viewer's line, facing
    -z), four struts and eight small gold beads; a thin glowing core inside the crystal. Origin: the cradle's base centre. The crystal is glass
    (`crystal`); with glow off it still reads as a pale blue gem."""
    P = Piece()
    cr = P.geo(st.crystal)
    gd = P.geo(st.gold)
    gl = P.geo(st.glow)
    y0 = base_y + 1.2
    # hexagonal bipyramid, long: points at the ends, facets
    hexr = 1.55
    prof = [(0.0, y0), (hexr * 0.55, y0 + 1.6), (hexr, y0 + 3.2), (hexr, y0 + crystal_h * 0.62), (hexr * 0.62, y0 + crystal_h * 0.86), (0.0, y0 + crystal_h)]
    lathe(cr, prof, 6, phase=math.pi / 6, caps=False)
    # the core: a thinner hexagonal needle inside
    lathe(gl, [(0.0, y0 + 0.6), (0.34, y0 + 2.8), (0.34, y0 + crystal_h * 0.62), (0.0, y0 + crystal_h * 0.8)], 6, phase=math.pi / 6, caps=False)
    # cradle: base ring, a bowl of eight upswept petals
    lathe(gd, [(0.0, base_y), (2.2, base_y), (2.4, base_y + 0.3), (1.9, base_y + 0.7), (1.0, base_y + 1.0), (0.0, base_y + 1.0)], 16, caps=False)
    for k in range(8):
        a = TAU * k / 8
        ca, sa = math.cos(a), math.sin(a)
        pts = [(1.2 * ca, base_y + 0.7, 1.2 * sa), (1.9 * ca, base_y + 1.5, 1.9 * sa), (2.0 * ca, base_y + 2.7, 2.0 * sa), (1.35 * ca, base_y + 3.9, 1.35 * sa)]
        frames = []
        for i in range(4):
            tg = vnorm(vsub(pts[min(i + 1, 3)], pts[max(i - 1, 0)]))
            rt = (-sa, 0.0, ca)
            upn = vnorm(vcross(rt, tg))
            sc = (0.42, 0.14)
            frames.append((vmul(rt, 0.42 * (1 - i / 4.5)), vmul(upn, 0.14)))
        start = len(gd.f)
        tube(gd, pts, frames, [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)], caps=True)
    # halo rings in the xy plane, centred over the crystal's middle, facing -z
    cy = y0 + crystal_h * 0.52
    for R, r, seg in ((ring_r, 0.34, 56), (ring_r * 0.78, 0.2, 48)):
        _torus_xy(gd, 0.0, cy, R, r, seg, 6)
    # beads on the outer ring at the eight compass points (little gold diamonds)
    for k in range(8):
        a = TAU * k / 8 + math.pi / 8
        x, y = ring_r * math.cos(a), cy + ring_r * math.sin(a)
        prof = [(0.0, -0.75), (0.5, 0.0), (0.0, 0.75)]
        _bead(gd, x, y, a)
    # two struts: from the cradle's rim to the inner ring's bottom, and a short rod up through the top
    rin = ring_r * 0.78
    for sx in (-1, 1):
        a = (sx, 1.0)
        p0 = (sx * 1.9, base_y + 1.4, 0.0)
        p1 = (sx * rin * math.cos(math.radians(62)), cy - rin * math.sin(math.radians(62)), 0.0)
        _bar(gd, p0, p1, 0.16)
    return P


def _torus_xy(g, cx, cy, R, r, seg_u, seg_v):
    rings = []
    for k in range(seg_u):
        a = TAU * k / seg_u
        ca, sa = math.cos(a), math.sin(a)
        row = []
        for m in range(seg_v):
            b = TAU * m / seg_v
            rr = R + r * math.cos(b)
            row.append(g.vert((cx + rr * ca, cy + rr * sa, r * math.sin(b))))
        rings.append(row)
    start = len(g.f)
    for k in range(seg_u):
        j = (k + 1) % seg_u
        for m in range(seg_v):
            n = (m + 1) % seg_v
            g.face(rings[k][m], rings[j][m], rings[j][n], rings[k][n])
    _orient_solid(g, start)


def _bead(g, x, y, a):
    """A small gold diamond (octahedron) at (x, y) on a ring."""
    s = 0.52
    pts = [(x + s, y, 0.0), (x - s, y, 0.0), (x, y + s * 1.4, 0.0), (x, y - s * 1.4, 0.0), (x, y, s), (x, y, -s)]
    ids = [g.vert(p) for p in pts]
    for (i, j) in ((2, 0), (0, 3), (3, 1), (1, 2)):
        g.face(ids[i], ids[j], ids[4])
        g.face(ids[j], ids[i], ids[5])


def _bar(g, p0, p1, r):
    d = vnorm(vsub(p1, p0))
    ref = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
    rt = vnorm(vcross(d, ref))
    up = vnorm(vcross(rt, d))
    start = len(g.f)
    tube(g, [p0, p1], [(vmul(rt, r), vmul(up, r))] * 2, [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)], caps=True)
    _orient_solid(g, start)


# ======================================================================================================================
# composites: a storey, a stack of storeys with roofs, a pavilion
# ======================================================================================================================
def _wall_with_opening(g, x0, x1, y0, y1, zc, t, ox0, ox1, oy0, oy1):
    """A wall panel (plaster) facing -z, thickness t centred on zc, with a rectangular opening: four boxes around it."""
    z0, z1 = zc - t / 2, zc + t / 2
    box(g, x0, x1, y0, oy0, z0, z1, "TNESW")                  # sill
    box(g, x0, x1, oy1, y1, z0, z1, "TBNESW")                 # head
    box(g, x0, ox0, oy0, oy1, z0, z1, "TBNESW")               # left jamb
    box(g, ox1, x1, oy0, oy1, z0, z1, "TBNESW")               # right jamb


def _positions(a, d, nbx, nbz):
    """Column positions round a rectangle (corners included once)."""
    pts = []
    for i in range(nbx + 1):
        x = -a + 2 * a * i / nbx
        pts.append((x, -d))
        pts.append((x, d))
    for k in range(1, nbz):
        z = -d + 2 * d * k / nbz
        pts.append((-a, z))
        pts.append((a, z))
    return pts


def storey(st, a, d, y0, wall_h, hb, nbx, nbz, *, windows=True, open_faces=(), col_detail=0, layers=2, br_detail=1, mids=1, wall_t=0.9,
           beam=1.5, col_seg=8, lat_cols=3, lat_rows=2, rail=False, plinth=0.0):
    """One storey in the tier's own frame (x across, z deep, centred on the axis, front -Z): round columns on the rectangle with half sizes a, d
    from floor y0 up wall_h; plaster walls with a lattice window in each bay (faces listed in `open_faces`, any of "NESW", have no wall: open
    colonnades); a lower and an upper beam all round; bracket sets on every column head and `mids` between columns, 2 or 3 layers; an optional
    stone plinth ring `plinth` high. The roof is not included. Column radius follows st.col_r0/col_r1."""
    P = Piece()
    gw = P.geo(st.wall)
    gp = P.geo(st.paint)
    ytop = y0 + wall_h
    r = st.col_r0 * 0.95
    for (x, z) in _positions(a, d, nbx, nbz):
        P.add(pillar(st, wall_h - 0.0, r0=st.col_r0 * 0.92, r1=st.col_r1 * 0.95, foot=False, seg=col_seg, detail=col_detail), t=(x, y0, z))
    bays = {"N": (2 * a / nbx, nbx, d), "S": (2 * a / nbx, nbx, d), "E": (2 * d / nbz, nbz, a), "W": (2 * d / nbz, nbz, a)}
    if plinth > 0:
        gs = P.geo(st.stone2)
        # a granite ring under the storey: four boxes 2 wide centred on the column line
        box(gs, -a - 1.0, a + 1.0, y0 - plinth, y0, -d - 1.0, -d + 1.0, "TNESW")
        box(gs, -a - 1.0, a + 1.0, y0 - plinth, y0, d - 1.0, d + 1.0, "TNESW")
        box(gs, -a - 1.0, -a + 1.0, y0 - plinth, y0, -d + 1.0, d - 1.0, "TNESW")
        box(gs, a - 1.0, a + 1.0, y0 - plinth, y0, -d + 1.0, d - 1.0, "TNESW")
    for face in "NESW":
        bw, nb, dist = bays[face]
        yaw = FACE_YAW[face]
        for i in range(nb):
            u0 = -(nb * bw) / 2 + i * bw          # along the face's own x axis
            ucen = u0 + bw / 2
            gfa = Piece()
            if face not in open_faces:
                g1 = gfa.geo(st.wall)
                lo, hi = u0 + r + 0.05, u0 + bw - r - 0.05
                if windows:
                    ow = (hi - lo) - 1.2
                    oy0 = y0 + wall_h * 0.28
                    oy1 = ytop - beam - 0.55
                    _wall_with_opening(g1, lo, hi, y0, ytop - beam, 0.0, wall_t, ucen - ow / 2, ucen + ow / 2, oy0, oy1)
                    lat = lattice(st, ow - 0.1, oy1 - oy0 - 0.1, nx=lat_cols, ny=lat_rows, frame=0.22, bar=0.11)
                    gfa.add(lat, t=(ucen, oy0 + 0.05, 0.0))
                else:
                    box(g1, lo, hi, y0, ytop - beam, -wall_t / 2, wall_t / 2, "TBNESW")
            # (the bay panel was built in the face's frame: x along the face, z = 0 at the wall line, front -z): place it
            _place_face_piece(P, gfa, yaw, dist, 0.0)
    # beams
    for face in "NS":
        for yb0, yb1, depth in ((ytop - beam, ytop - beam + 0.7, 0.62), (ytop - beam + 0.7, ytop, 0.52)):
            zc = -d if face == "N" else d
            box(gp, -(a - 0.62), a - 0.62, yb0, yb1, zc - depth, zc + depth, "TBNESW")
    for face in "EW":
        for yb0, yb1, depth in ((ytop - beam, ytop - beam + 0.7, 0.62), (ytop - beam + 0.7, ytop, 0.52)):
            xc = a if face == "E" else -a
            box(gp, xc - depth, xc + depth, yb0, yb1, -(d + 0.45), d + 0.45, "TBNESW")
    # bracket sets
    if hb > 0:
        for face in "NESW":
            bw, nb, dist = bays[face]
            yaw = FACE_YAW[face]
            n_total = nb * (mids + 1) + 1
            spacing = bw / (mids + 1)
            proto = bracket_set(st, layers=layers, w=min(hb * 0.7, spacing * 0.8), h=hb, reach=spacing * 0.49, detail=br_detail)
            for k in range(n_total):
                u = -(nb * bw) / 2 + (nb * bw) * k / (n_total - 1)
                at_corner = abs(abs(u) - (nb * bw) / 2) < 1e-6
                if face in "EW" and at_corner:
                    continue
                x, z = yaw_xz(u, -dist, yaw)
                P.add(proto, t=(x, ytop, z), yaw=yaw)
    return P


def _place_face_piece(P, piece, yaw, dist, along):
    """A piece authored in a face's frame (x along the face, z = 0 on the wall line, front -z) put on that face of a tier (at distance `dist`
    from the axis, rotated by yaw)."""
    x, z = yaw_xz(0.0, -dist, yaw)
    P.add(piece, t=(x, 0.0, z), yaw=yaw)


def tiers_block(st, y0, tiers, *, top_finial=3.5, detail=1):
    """A stack of storeys with their roofs. tiers: list of dicts (outermost, lowest first) with a, d (column-line half sizes), wall (storey height),
    hb (bracket height), o (eave overhang past the column line), rise (roof rise from the eave tip to the roof's top), and optional layers,
    mids, nbx, nbz, windows, open (open faces), detail, br_detail, pitch, discs, rafters, finial, curve (roof curve overrides), ridge (the top
    tier ends in a ridge of this half length instead of a point). Each roof meets the next tier's wall (its top rectangle is that tier's column
    line). Returns (list of per-tier Pieces, list of per-tier info dicts: floor, eave tip, top y, eave half sizes, column-line half sizes)."""
    pieces = []
    info = []
    y = y0
    for i, t in enumerate(tiers):
        nxt = tiers[i + 1] if i + 1 < len(tiers) else None
        P = Piece()
        P.add(storey(st, t["a"], t["d"], y, t["wall"], t["hb"], t.get("nbx", 4), t.get("nbz", 2), windows=t.get("windows", True),
                     open_faces=t.get("open", ()), layers=t.get("layers", 2), mids=t.get("mids", 1), br_detail=t.get("br_detail", 1),
                     col_detail=t.get("col_detail", 0), lat_cols=t.get("lat_cols", 3), lat_rows=t.get("lat_rows", 2),
                     plinth=t.get("plinth", 0.0), col_seg=t.get("col_seg", 8)))
        ye = y + t["wall"] + t["hb"] * 0.55
        yt = ye + t["rise"]
        A, D = t["a"] + t["o"], t["d"] + t["o"]
        if nxt:
            at, dt = nxt["a"], nxt["d"]
        else:
            at, dt = t.get("ridge", 0.0), 0.0
        P.add(roof(st, A, D, at, dt, ye, yt, detail=t.get("detail", detail), pitch=t.get("pitch"), finial=0.0 if nxt else t.get("finial", top_finial),
                   discs=t.get("discs", True), rafters=t.get("rafters", True), **t.get("curve", {})))
        pieces.append(P)
        info.append({"floor": y, "eave": ye, "top": yt, "A": A, "D": D, "a": t["a"], "d": t["d"]})
        y = yt
    return pieces, info


def rock_blocks(st, cx, cz, rx, rz, y0, y1, n=10, seed=1, size=(3.0, 5.5), start=0.0):
    """Craggy blocks round an ellipse (centre cx, cz, radii rx, rz) from y0 to y1: each a box with its four top corners lifted by hashed noise and
    its footprint turned by a hashed yaw. They overlap the mass behind them: a rock face of boulders, not a smooth mound. Role: rock."""
    P = Piece()
    g = P.geo(st.rock)
    for i in range(n):
        a = start + K_TAU * i / n
        j = 0.85 + 0.3 * _noise(i, 2, seed, seed)
        bx, bz = cx + rx * j * math.cos(a), cz + rz * j * math.sin(a)
        w = size[0] + (size[1] - size[0]) * _noise(i, 3, seed, seed + 1)
        d = size[0] + (size[1] - size[0]) * _noise(i, 4, seed, seed + 2)
        hh = (y1 - y0) * (0.55 + 0.45 * _noise(i, 5, seed, seed + 3))
        yaw = TAU * _noise(i, 6, seed, seed + 4)
        c, s = math.cos(yaw), math.sin(yaw)
        base = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        top = [(x * (0.78 + 0.2 * _noise(i, 7 + k, seed, 1)), z * (0.78 + 0.2 * _noise(i, 11 + k, seed, 2))) for k, (x, z) in enumerate(base)]
        rot = lambda p: (bx + p[0] * c + p[1] * s, bz - p[0] * s + p[1] * c)
        ys = [y0 + hh * (0.82 + 0.18 * _noise(i, 15 + k, seed, 3)) for k in range(4)]
        b3 = [rot(p) for p in base]
        t3 = [rot(p) for p in top]
        bi = [g.vert((x, y0, z)) for x, z in b3]
        ti = [g.vert((x, ys[k], z)) for k, (x, z) in enumerate(t3)]
        for k in range(4):
            kk = (k + 1) % 4
            g.face(bi[k], ti[k], ti[kk], bi[kk])
        g.face(ti[3], ti[2], ti[1], ti[0])
    return P


K_TAU = TAU

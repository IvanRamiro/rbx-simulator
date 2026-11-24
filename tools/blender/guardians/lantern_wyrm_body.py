"""The Lantern Wyrm's long forms (run inside Blender): the body tube (neck, trunk and tail in one skin with its belly scutes and dorsal keel,
built ring by ring so a bone's bend has rings to turn), its ring-marks (photophores), the mane-frill and the tail fin (ribs and a double
skinned membrane), authored in Roblox studs in the straight bind and with the UVs the bake needs.

The body's UVs are made, not unwrapped: the tube is cut into four chunks along its length, each unrolled into a 1024 x 1024 cell of a
2048 map at 56 pixels a stud (isotropic: a scale is as long as it is wide whether it is on the thick neck or the thin tail); the seam
runs along the belly's middle, where nobody looks.
"""
import math

import egg_hi as Hm
import guardian_kit as G
from mathutils import Vector

import lantern_wyrm_bones as B

V = Vector
TAU = 2 * math.pi

U0 = -22.8                  # the tube starts inside the head's back
CHUNKS, LC = 4, 17.0        # four chunks of 17 studs: u from -22.8 to 45.2
U1 = U0 + CHUNKS * LC
PX_PER_STUD = 56.0
UVS = PX_PER_STUD / 2048.0  # uv per stud


def section(u, phi, grooves=True):
    """The body's cross-section at u, the angle phi round it (0 at the belly's middle, pi at the spine): a point (x, y) from the axis, in studs,
    its belly flatter than its back, scutes cut across the belly, a keel along the spine."""
    r = B.radius_at(u)
    rx, ry = 1.05, (0.9 if math.cos(phi) > 0 else 1.0)
    # the belly flattens: below the axis the section is a superellipse
    c, s = -math.cos(phi), math.sin(phi)
    k = 3.2 if c < 0 else 2.6
    d = (abs(s) ** k + abs(c) ** k) ** (1.0 / k)
    x, y = rx * r * s / d, ry * r * c / d
    if grooves:
        belly = max(0.0, math.cos(min(abs(phi), abs(TAU - phi)) / 0.85 * math.pi * 0.5)) if min(abs(phi), abs(TAU - phi)) < 0.85 else 0.0
        g = (u / 0.9) % 1.0
        groove = max(0.0, 1 - 7 * min(g, 1 - g))
        f = 1 - 0.06 * groove * belly
        keel = 0.07 * math.exp(-((phi - math.pi) / 0.18) ** 2) * (0.6 + 0.4 * (1 if ((u / 1.3) % 1.0) < 0.5 else 0.0))
        f += keel
        x, y = x * f, y * f
    return x, y


def uv_of(u, phi, mid_u):
    """The UV of a point of the tube: its chunk's cell, an isotropic unrolling."""
    c = max(0, min(CHUNKS - 1, int((mid_u - U0) // LC)))
    cx, cy = 0.25 + 0.5 * (c % 2), 0.25 + 0.5 * (c // 2)
    perim = TAU * max(B.radius_at(u), 0.08) * UVS
    local = u - (U0 + c * LC)
    return (cx + (phi / TAU - 0.5) * perim, cy + 0.236 - local * UVS)


def body_hi(du, sides, grooves=True, hi=None, mat=0):
    """The body tube as a Hi mesh (Roblox space): rings every du studs from U0 to U1, `sides` points round each; per-corner UVs. Returns (hi, n)."""
    hi = hi or Hm.Hi()
    n = int(round((U1 - U0) / du))
    rings = []
    for k in range(n + 1):
        u = U0 + k * du
        ring = []
        for j in range(sides):
            x, y = section(u, TAU * j / sides, grooves)
            ring.append(hi.v((x, B.Y0 + y, u)))
        rings.append(ring)
    for k in range(n):
        mid = U0 + (k + 0.5) * du
        for j in range(sides):
            j2 = (j + 1) % sides
            p = [(k, j, j), (k, j2, j + 1), (k + 1, j2, j + 1), (k + 1, j, j)]
            idx = [rings[a][b] for a, b, _ in p]
            uv = [uv_of(U0 + a * du, TAU * jj / sides, mid) for a, _, jj in p]
            # wound outward: the order (ring k, j) -> (k, j+1) -> (k+1, j+1) with the axis along +Z turns one way
            hi.facing(idx, uv, _out(U0 + k * du, TAU * (j + 0.5) / sides), mat)
    # the front end closes inside the head, the tail's end is a point
    return hi, n


def _out(u, phi):
    """Outward direction of the section at phi (Roblox space)."""
    return (math.sin(phi), -math.cos(phi), 0.0)


def body_weights(z):
    """{bone: weight} of a point of the tube at z along the bind axis: a hat between neighbouring bones' middles (two influences), eased."""
    chain = [(n, sum(B.bone_span(n)) / 2) for n in B.NECK[::-1]] + [("Head", sum(B.bone_span("Head")) / 2)]
    chain = [(n, c) for n, c in chain]
    # order along z, from the head's side to the tail's: Head, Neck8 .. Neck1, Body1 .. Tail11
    # (the hips themselves carry the vertices at the junction of neck and trunk, so the importer keeps the bone every other bone hangs from)
    chain = ([("Head", sum(B.bone_span("Head")) / 2)] + [(n, sum(B.bone_span(n)) / 2) for n in B.NECK[::-1]] + [("Hips", 0.0)]
             + [(n, sum(B.bone_span(n)) / 2) for n in B.SPINE_BACK])
    if z <= chain[0][1]:
        return {chain[0][0]: 1.0}
    if z >= chain[-1][1]:
        return {chain[-1][0]: 1.0}
    for (a, ca), (b, cb) in zip(chain, chain[1:]):
        if ca <= z <= cb:
            t = (z - ca) / (cb - ca)
            t = t * t * (3 - 2 * t)
            return {a: 1 - t, b: t}
    return {chain[-1][0]: 1.0}


# ---------- the photophores: ring-marks along the flanks ----------
RING_ANGLE = 0.62 * math.pi              # round the body from the belly (the flank, a little above the axis's level)
RING_U = [-19.0 + 2.1 * k for k in range(0, 30)]


def ring_groups():
    """Four groups from the tail up to the head, so the light can run along them: A tail, B back half of the trunk, C front half and shoulders, D neck."""
    return {"A": lambda u: u > 22.0, "B": lambda u: 8.0 < u <= 22.0, "C": lambda u: -5.0 < u <= 8.0, "D": lambda u: u <= -5.0}


def rings_hi(group):
    """The ring-marks of one group, both flanks: thin annuli lying on the skin, a hair proud of it. Returns a Hi."""
    hi = Hm.Hi()
    sel = ring_groups()[group]
    for u in RING_U:
        if not sel(u):
            continue
        for sign in (-1, 1):
            phi = RING_ANGLE if sign > 0 else TAU - RING_ANGLE
            x, y = section(u, phi, grooves=False)
            r = B.radius_at(u)
            c = V((x, B.Y0 + y, u))
            nrm = V((math.sin(phi) * 1.0, -math.cos(phi) * 0.9, 0)).normalized()
            fwd = V((0, 0, 1))
            side = nrm.cross(fwd).normalized()
            rin, rout = 0.12 + 0.05 * min(1.0, r / 2.6), 0.26 + 0.1 * min(1.0, r / 2.6)
            m = 12
            lift = 0.06
            ring_in = [hi.v(c + nrm * (lift + 0.02) + (fwd * math.cos(TAU * i / m) + side * math.sin(TAU * i / m)) * rin) for i in range(m)]
            ring_out = [hi.v(c - nrm * 0.05 + (fwd * math.cos(TAU * i / m) + side * math.sin(TAU * i / m)) * rout) for i in range(m)]
            for i in range(m):
                j = (i + 1) % m
                hi.facing([ring_in[i], ring_in[j], ring_out[j], ring_out[i]], [(i / m, 0), ((i + 1) / m, 0), ((i + 1) / m, 1), (i / m, 1)], tuple(nrm))
    return hi


# ---------- the mane-frill and the tail fin ----------
def _rib_points(k, sign):
    p, h, t = B.BONES[("Left" if sign < 0 else "Right") + "Frill%d" % (k + 1)]
    return V(h), V(t)


def _lay(a, b, f):
    return a.lerp(b, f)


def frill_hi(hi=None, thick=0.04, rows=6, across=4, ribs=True):
    """Both halves of the mane: for each side ten ribs (thin tapered tubes along the frill bones) and the membrane between neighbours, scalloped
    at its edge, as two layers 2 x thick apart facing opposite ways (Roblox draws only a face's front: the layers make it read from both
    sides). Returns (hi, weights) where weights maps each vertex index to {bone: weight}."""
    hi = hi or Hm.Hi()
    wts = {}

    def vert(p, w):
        i = hi.v(p)
        wts[i] = w
        return i

    for sign in (-1, 1):
        tag = "Left" if sign < 0 else "Right"
        names = B.FRILL[tag]
        for k in range(B.FRILL_N - 1):
            a0, a1 = _rib_points(k, sign)
            b0, b1 = _rib_points(k + 1, sign)
            grid = []
            for q in range(rows + 1):
                tq = q / rows
                row = []
                for f in range(across + 1):
                    ff = f / across
                    root = _lay(a0, b0, ff)
                    tip = _lay(a1, b1, ff)
                    # the scallop: the free edge is drawn back between the two rib tips
                    pull = math.sin(math.pi * ff) * 0.16 * tq ** 2
                    pt = _lay(root, tip, tq * (1 - pull))
                    row.append((pt, {names[k]: 1 - ff, names[k + 1]: ff}))
                grid.append(row)
            n_face = (V(grid[0][0][0]) - V(grid[0][-1][0])).cross(V(grid[-1][0][0]) - V(grid[0][0][0])).normalized()
            for layer, side in ((1, 1), (-1, -1)):
                off = n_face * (thick * layer)
                ids = [[vert(p + off, w) for p, w in row] for row in grid]
                for q in range(rows):
                    for f in range(across):
                        quad = [ids[q][f], ids[q][f + 1], ids[q + 1][f + 1], ids[q + 1][f]]
                        uv = [((k + f / across) / (B.FRILL_N - 1), q / rows), ((k + (f + 1) / across) / (B.FRILL_N - 1), q / rows),
                              ((k + (f + 1) / across) / (B.FRILL_N - 1), (q + 1) / rows), ((k + f / across) / (B.FRILL_N - 1), (q + 1) / rows)]
                        hi.facing(quad, uv, tuple(n_face * side), 0)
        if ribs:
            for k in range(B.FRILL_N):
                a0, a1 = _rib_points(k, sign)
                rad = lambda t, k=k: (0.2 - 0.14 * t) * (1.0 - 0.012 * k)
                _tube_w(hi, wts, [a0 + (a1 - a0) * (i / 4.0) for i in range(5)], rad, {names[k]: 1.0}, sides=5)
    return hi, wts


def _tube_w(hi, wts, pts, radius_fn, weights, sides=5):
    """A tapered tube through points with one weight set; records the vertices it adds."""
    before = len(hi.verts)
    Hm.htube(hi, [tuple(p) for p in pts], radius_fn, sides=sides, per=2, uv_scale=0.5, tip=True, wobble=0.0, mat=1)
    for i in range(before, len(hi.verts)):
        wts[i] = dict(weights)


def fin_hi(hi, wts, thick=0.04):
    """The tail's fin: a dorsal and a ventral blade along the last bones, rooted on the spine, swept back past the tip. Double layered like the
    frill, ribbed. Weights: the tail's last bones by position."""
    z0 = B.TAIL_END - 9.0
    zt = B.TAIL_END + 4.6

    def tail_w(z):
        w = body_weights(min(z, B.TAIL_END))
        return {k: v for k, v in w.items()}
    ribs = 7
    for sgn in (1,):                          # the dorsal blade (the tail lies on the ground, so there is no ventral one)
        pts_root, pts_tip = [], []
        for i in range(ribs):
            t = i / (ribs - 1)
            zr = z0 + (B.TAIL_END - 0.6 - z0) * t
            r = B.radius_at(zr)
            root = V((0, B.Y0 + sgn * r * 0.8, zr))
            height = (1.4 + 4.4 * math.sin(math.pi * (0.2 + 0.8 * t) ** 0.9)) * (1.0 if sgn > 0 else 0.0) + (0.0 if sgn > 0 else 0.3)
            tip = V((0, B.Y0 + sgn * (r * 0.8 + height), zr + 0.6 + 3.2 * t))
            pts_root.append((root, zr))
            pts_tip.append((tip, zr + 0.6 + 3.2 * t))
        rows = 4
        for i in range(ribs - 1):
            for layer in (1, -1):
                off = V((thick * layer, 0, 0))
                grid = []
                for q in range(rows + 1):
                    tq = q / rows
                    row = []
                    for f in (0, 1):
                        ra, za = pts_root[i + f]
                        ta, zt_ = pts_tip[i + f]
                        p = ra.lerp(ta, tq) + off
                        i0 = hi.v(p)
                        wts[i0] = tail_w(za)
                        row.append(i0)
                    grid.append(row)
                for q in range(rows):
                    hi.facing([grid[q][0], grid[q][1], grid[q + 1][1], grid[q + 1][0]], [(0, q / rows), (1, q / rows), (1, (q + 1) / rows), (0, (q + 1) / rows)],
                              (layer, 0, 0), 0)
        for i in range(ribs):
            ra, za = pts_root[i]
            ta, _ = pts_tip[i]
            _tube_w(hi, wts, [ra + (ta - ra) * (j / 3.0) for j in range(4)], lambda t: 0.12 - 0.08 * t, tail_w(za), sides=5)
    return hi, wts


# ---------- per-vertex attributes the shaders read ----------
def set_attr(obj, name, values):
    a = obj.data.attributes.get(name) or obj.data.attributes.new(name, "FLOAT", "POINT")
    a.data.foreach_set("value", [float(v) for v in values])


def body_attributes(obj, n, sides, du):
    """Along (-1 at the head .. 1 at the tail), BellyMask (1 on the ventral plates), DorsalMask (1 on the spine's stripe), per ring vertex."""
    along, belly, dorsal = [], [], []
    for k in range(n + 1):
        u = U0 + k * du
        for j in range(sides):
            phi = TAU * j / sides
            dist = min(phi, TAU - phi)
            along.append(max(-1.0, min(1.0, (u - 11.0) / 34.0)))
            belly.append(max(0.0, min(1.0, 0.5 + (0.85 - dist))))
            dorsal.append(math.exp(-((phi - math.pi) / 0.35) ** 2))
    set_attr(obj, "Along", along)
    set_attr(obj, "BellyMask", belly)
    set_attr(obj, "DorsalMask", dorsal)


def frill_attributes(obj, hi_materials):
    """RibMask: 1 on the ribs' vertices (the faces made with material index 1), 0 on the membrane."""
    me = obj.data
    mask = [0.0] * len(me.vertices)
    for poly in me.polygons:
        if poly.material_index == 1:
            for v in poly.vertices:
                mask[v] = 1.0
    set_attr(obj, "RibMask", mask)

"""Origin Abyss meshes, batch 1.

- The island atlas.
- The shattered underside (angular chunks with void light between them), the iron chains that
  bind the two halves across the rift, and the rift veil glowing deep in the rift.
- The broken bridge with its floating rubble.
- The Origin Altar: a monolith ring with rune glows around a stepped dais.
- The Void Shard and the floating ruin fragments that climb to it.
- Kit pieces: the Gate of Descent, the ruin fragments and the shard floor.
"""
import bpy, bmesh, math, random
import worldlib as W
import origin_island as O
import layout as L
import start_props as SP
import jade_meshes as JM

TAU = 2 * math.pi
oriented = SP.oriented


# ---------- atlas ----------
def _n(u, v, f, seed):
    a = u * TAU
    return W.fbm(math.cos(a) * f + 13, math.sin(a) * f + v * f * 2, seed=seed, octaves=3)


def _ramp(lo, hi, v, n, k=0.04):
    return tuple(max(0.0, min(1.0, lo[i] + (hi[i] - lo[i]) * v + k * n)) for i in range(3))


def slate(u, v):
    layers = 0.5 + 0.5 * math.sin(v * 70 + 3 * _n(u, v, 2, 201))
    return _ramp((0.1, 0.1, 0.13), (0.3, 0.29, 0.36), v * (0.75 + 0.25 * layers), _n(u, v, 6, 202), 0.04)


def obsidian(u, v):
    sheen = max(0.0, 1 - abs(v - 0.78) * 8) * 0.22
    c = _ramp((0.03, 0.02, 0.05), (0.14, 0.09, 0.2), v, _n(u, v, 5, 203), 0.03)
    return tuple(min(1.0, x + sheen * (0.7, 0.5, 1.0)[i]) for i, x in enumerate(c))


def void(u, v):
    return _ramp((0.18, 0.04, 0.36), (0.78, 0.48, 1.0), v, _n(u, v, 4, 204), 0.08)


def bronze(u, v):
    if _n(u, v, 12, 205) > 0.45:
        return (0.14, 0.24, 0.2)    # verdigris, rare and dark
    return _ramp((0.12, 0.08, 0.04), (0.38, 0.26, 0.13), v, _n(u, v, 7, 206), 0.04)   # old, dark bronze


def ruin(u, v):
    carved = abs(math.sin(u * TAU * 7)) < 0.06 or abs(math.sin(v * 22)) < 0.05
    c = _ramp((0.17, 0.16, 0.19), (0.36, 0.34, 0.37), v, _n(u, v, 6, 207), 0.05)
    return tuple(x * 0.6 for x in c) if carved else c


def iron(u, v):
    return _ramp((0.06, 0.06, 0.07), (0.3, 0.29, 0.3), v, _n(u, v, 9, 208), 0.05)


def gold(u, v):
    return _ramp((0.38, 0.28, 0.12), (0.72, 0.58, 0.3), v, _n(u, v, 7, 209), 0.05)


def glow(u, v):
    return (0.85, 0.6, 1.0)


def ash(u, v):
    return _ramp((0.2, 0.19, 0.21), (0.42, 0.4, 0.43), v, _n(u, v, 9, 210), 0.05)


def rune(u, v):
    mark = _n(u, v, 17, 211) > 0.5
    return (0.62, 0.34, 0.95) if mark else _ramp((0.08, 0.07, 0.1), (0.22, 0.2, 0.26), v, _n(u, v, 6, 212), 0.03)


def fracture(u, v):
    vein = max(0.0, 1 - abs(_n(u, v * 0.6, 4, 213)) * 12)
    c = _ramp((0.06, 0.05, 0.08), (0.24, 0.22, 0.28), v, _n(u, v, 5, 214), 0.04)
    return tuple(min(1.0, c[i] + vein * (0.4, 0.15, 0.6)[i]) for i in range(3))


STRIPS = [(80, slate), (48, obsidian), (48, void), (48, bronze), (64, ruin), (32, iron), (32, gold), (16, glow),
          (32, ash), (48, rune), (64, fracture)]
SLATE, OBSIDIAN, VOID, BRONZE, RUIN, IRON, GOLD, GLOW, ASH, RUNE, FRACTURE = range(11)


def ground(x, z):
    return O.height(x, z)[0]


def hull_chunk(bm_pts, rnd, cx, cz, half, y_top, y_bottom, jag=0.15):
    """Random points filling an angular box (for a convex hull)."""
    for _ in range(14):
        bm_pts.append((cx + rnd.uniform(-half, half) * (1 - jag * rnd.random()), rnd.uniform(y_bottom, y_top),
                       cz + rnd.uniform(-half, half) * (1 - jag * rnd.random())))
    for sx in (-1, 1):  # keep the top flat and wide so neighbouring chunks meet under the terrain
        for sz in (-1, 1):
            bm_pts.append((cx + sx * half, y_top, cz + sz * half))


def hulls_to_object(name, coll, mat, band, groups, top_y, bottom_y):
    """Merge convex hulls of point groups into one mesh, UV'd by depth in `band`."""
    bm = bmesh.new()
    for pts in groups:
        part = bmesh.new()
        for p in pts:
            part.verts.new(W.rb(*p))
        bmesh.ops.convex_hull(part, input=part.verts)
        me = bpy.data.meshes.new("tmp"); part.to_mesh(me); part.free()
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    uv = bm.loops.layers.uv.verify()
    v0, v1 = band
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((math.atan2(co.y, co.x) / TAU) % 1 * 3, v0 + (v1 - v0) * max(0.05, min(0.95, (co.z - bottom_y) / (top_y - bottom_y))))
        f.smooth = False
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


# ---------- underside ----------
UNDER_TOP = -2.6


def under_ground(p, gap=2.0):
    """Lowers a point to at least `gap` below the ground above it."""
    x, y, z = p
    g = ground(x, z)
    return (x, min(y, g - gap), z) if g is not None else p


def pull_inside(p, cx, cz, margin=2.5):
    """Moves a point toward (cx, cz) until it is `margin` inside the island, so no chunk pokes
    out past the coast or floors over the rift."""
    x, y, z = p
    for _ in range(12):
        if O.edge_distance(x, z) >= margin:
            break
        x, z = cx + (x - cx) * 0.8, cz + (z - cz) * 0.8
    return (x, y, z)


def under_chunks(coll, mat, bands):
    """Each half's underside broken into separate angular chunks: long under the middle of each
    half, short near its coast and its rift lip, with gaps between them."""
    rnd = random.Random(601)
    groups = []
    spacing = 11.0
    for j in range(-10, 11):
        for i in range(-10, 11):
            x = (i + (0.5 if j % 2 else 0)) * spacing
            z = j * spacing * 0.866
            e = O.edge_distance(x, z)
            if e < 3.5:
                continue
            depth = 12 + min(1.0, max(0.0, e) / 34) ** 0.8 * 60 + rnd.uniform(-6, 6)
            pts = []
            cx, cz = x + rnd.uniform(-1, 1), z + rnd.uniform(-1, 1)
            half = spacing * 0.42
            # tuck the top under the lowest ground above the chunk (the ground drops toward a lip)
            above = [ground(cx + sx * half, cz + sz * half) for sx, sz in ((0, 0), (-1, -1), (1, -1), (1, 1), (-1, 1))]
            top = min([UNDER_TOP] + [g - 2.0 for g in above if g is not None])
            hull_chunk(pts, rnd, cx, cz, half, top, top - depth)
            groups.append([under_ground(pull_inside(p, cx, cz)) for p in pts])
    # debris that has already broken away, drifting beneath the island
    for k in range(14):
        a = TAU * k / 14 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(18, 60)
        x, z = math.cos(a) * r, math.sin(a) * r
        if abs(O.side(x, z)) < 12:   # keep the space under the rift open
            continue
        top = -78 - rnd.uniform(0, 30) + r * 0.4
        size = rnd.uniform(2.5, 5.5)
        pts = []
        hull_chunk(pts, rnd, x, z, size, top, top - size * rnd.uniform(1.4, 2.6), jag=0.4)
        groups.append(pts)
    return hulls_to_object("OA_UnderChunks", coll, mat, bands[FRACTURE], groups, UNDER_TOP, UNDER_TOP - 110)


def void_core(coll, mat, bands):
    """The void light the chunks hang around (Neon in Roblox), one lobe under each half."""
    mb = W.MeshBuilder()
    for sign in (1, -1):
        nx, nz = -O.RIFT_DIR[1], O.RIFT_DIR[0]
        cx, cz = nx * sign * 34, nz * sign * 34
        rings = [(19, -6), (17, -20), (12, -36), (6, -50), (0.0, -58)]   # kept inside the chunks so it only shows through the gaps
        mb.lathe([(r, y, 1.0) for r, y in rings], 14, bands[GLOW], centre=(cx, 0, cz), cap_top=True, u_repeat=0.0)
    return mb.object("OA_VoidCore", coll, mat)


def chain_link(mb, centre, axis, side, half_len, half_w, r, band, segs=8, sides=4):
    """One closed oval link: a tube of radius r round an oval in the plane of axis and side. The
    oval's tightest bend (half_w^2 / half_len) must stay wider than r, or the tube folds."""
    assert half_w * half_w / half_len > r, "chain link too thick for its bend"
    normal = axis.cross(side).normalized()
    stations = []
    for i in range(segs):
        ang = TAU * i / segs
        p = centre + axis * math.cos(ang) * half_len + side * math.sin(ang) * half_w
        tangent = (-axis * math.sin(ang) * half_len + side * math.cos(ang) * half_w).normalized()
        out = tangent.cross(normal).normalized()
        if out.dot(p - centre) < 0:
            out = -out
        dirs = [out * math.cos(TAU * k / sides) + normal * math.sin(TAU * k / sides) for k in range(sides)]
        stations.append((p, dirs))
    for i in range(segs):
        (p0, d0), (p1, d1) = stations[i], stations[(i + 1) % segs]
        for k in range(sides):
            j = (k + 1) % sides
            quad = [tuple(p0 + d0[k] * r), tuple(p0 + d0[j] * r), tuple(p1 + d1[j] * r), tuple(p1 + d1[k] * r)]
            oriented(mb, quad, tuple(d0[k] + d0[j] + d1[k] + d1[j]), band, (k + 0.5) / sides, [0.9 if (d0[k] + d0[j]).y > 0 else 0.55] * 4)


def chain_links(mb, a, b, link_len, link_w, band, sag=0.0):
    """A chain of alternating links between points a and b (Roblox space), sagging in the middle."""
    a, b = W.Vector(a), W.Vector(b)
    d = b - a
    n = max(2, int(d.length / (link_len * 0.78)))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        p0 = a + d * t0 + W.Vector((0, -sag * 4 * t0 * (1 - t0), 0))
        p1 = a + d * t1 + W.Vector((0, -sag * 4 * t1 * (1 - t1), 0))
        axis = (p1 - p0).normalized()
        flat = axis.cross(W.Vector((0, 1, 0)))
        if flat.length < 1e-3:   # a vertical chain: any horizontal side will do
            flat = axis.cross(W.Vector((1, 0, 0)))
        side = flat.normalized() if k % 2 == 0 else axis.cross(flat).normalized()   # alternate links turn 90 degrees
        chain_link(mb, (p0 + p1) / 2, axis, side, link_len * 0.55, link_w, link_w * 0.3, band)


def rift_chains(coll, mat, bands):
    """Three great chains slung across the rift beneath the island, binding the halves."""
    mb = W.MeshBuilder()
    ax, az = O.RIFT_DIR
    nx, nz = -az, ax
    for along, depth, span in ((-30, -9, 24), (4, -14, 28), (34, -10, 24)):
        cx, cz = ax * along, az * along
        s = O.side(cx, cz)
        cx, cz = cx - nx * s, cz - nz * s   # centred on the meandering rift, anchored in the chunks either side
        a = (cx + nx * span, depth, cz + nz * span)
        b = (cx - nx * span, depth, cz - nz * span)
        chain_links(mb, a, b, 5.0, 1.6, bands[IRON], sag=5.0)
    return mb.object("OA_RiftChains", coll, mat)


def rift_veil(coll, mat, bands):
    """A tall glowing sheet deep inside the rift (Neon, translucent in Roblox), both faces."""
    mb = W.MeshBuilder()
    ax, az = O.RIFT_DIR
    nx, nz = -az, ax
    pts = []
    for k in range(-14, 15):
        along = k * 6.5
        x, z = ax * along, az * along
        for _ in range(3):   # settle onto the meandering centreline
            s = O.side(x, z)
            x, z = x - nx * s, z - nz * s
        if math.hypot(x, z) < O.rim(math.atan2(z, x)) - 5:   # only between the two halves, never past the coast
            pts.append((x, z))
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        q = [(x0, -9, z0), (x1, -9, z1), (x1, -48, z1), (x0, -48, z0)]
        oriented(mb, q, (nx, 0, nz), bands[GLOW], 0.5, [1.0, 1.0, 0.6, 0.6])
        oriented(mb, q, (-nx, 0, -nz), bands[GLOW], 0.5, [1.0, 1.0, 0.6, 0.6])
    return mb.object("OA_RiftVeil", coll, mat)


# ---------- the broken bridge ----------
# Each half starts this far inland (a fraction of the lip-to-lip span, about 7.5 studs), where the
# deck meets the ground level (measured in Studio: terrain smoothing rounds the ground down toward
# a lip). A solid abutment fills beneath each half out to the lip, then the deck stands proud of the
# lip on its buttress.
BRIDGE_INLAND = 0.4
DECK_ENDS = (0.1, 5.4)   # deck surface at the SE and NW inland ends


def broken_bridge(coll, mat, bands):
    """An ancient stone bridge from lip to lip with its middle fallen away (about 7.5 studs). One
    fallen block still hangs in the gap at deck height, leaving a short jump either side of it."""
    mb = W.MeshBuilder()
    a, b = O.BRIDGE_SE, O.BRIDGE_NW
    dx, dz = b[0] - a[0], b[1] - a[1]
    t_se, t_nw = -BRIDGE_INLAND, 1 + BRIDGE_INLAND
    y_se, y_nw = DECK_ENDS
    ya = y_se + (y_nw - y_se) * (0 - t_se) / (t_nw - t_se)   # deck height at each lip
    yb = y_se + (y_nw - y_se) * (1 - t_se) / (t_nw - t_se)
    L_ = math.hypot(dx, dz)
    ux, uz = dx / L_, dz / L_
    yaw = math.atan2(ux, uz)
    at = lambda t, dy, w: (a[0] + dx * t + uz * w, ya + (yb - ya) * t + dy, a[1] + dz * t - ux * w)
    rnd = random.Random(611)
    for t0, t1 in ((t_se, 0.3), (0.7, t_nw)):  # the two surviving halves, each anchored inland
        slab_between(mb, at(t0, -0.5, 0), at(t1, -0.5, 0), 2.1, 0.5, bands[RUIN], u=0.2)   # one sloping deck
        inland, broken = (t0, t1) if t0 < 0 else (t1, t0)
        for w in (-1.85, 1.85):   # low parapets, each snapped off a different distance short of the break
            stop = broken + (inland - broken) * rnd.uniform(0.05, 0.25)
            slab_between(mb, at(inland, 0.35, w), at(stop, 0.35, w), 0.25, 0.35, bands[RUIN], u=0.5)
        # a solid abutment from the inland end out to the lip, then a buttress under the overhang:
        # a wedge from the deck's underside down into the rift wall
        lip_t, mid_t = (0.02, 0.3) if t0 < 0 else (0.98, 0.7)
        slab_between(mb, at(inland, -3.0, 0), at(lip_t, -3.0, 0), 1.9, 2.0, bands[RUIN], u=0.3)
        left = [at(lip_t, -1.0, -1.4), at(mid_t, -1.0, -1.4), at(lip_t, -9.0, -1.4)]
        right = [at(lip_t, -1.0, 1.4), at(mid_t, -1.0, 1.4), at(lip_t, -9.0, 1.4)]
        oriented(mb, left, (-uz, 0, ux), bands[RUIN], 0.4, [0.6] * 3)
        oriented(mb, right, (uz, 0, -ux), bands[RUIN], 0.4, [0.6] * 3)
        out = (dx * (mid_t - lip_t), -0.6, dz * (mid_t - lip_t))   # the slanted underside faces down and out over the rift
        oriented(mb, [left[1], right[1], right[2], left[2]], out, bands[RUIN], 0.6, [0.55] * 4)
    x, z = a[0] + dx * 0.5, a[1] + dz * 0.5
    y = ya + (yb - ya) * 0.5 - 0.6
    mb.box((x, y, z), (3.0, 1.0, 2.0), bands[RUIN], yaw=yaw + 0.15, u=0.7, top_shade=0.9, side_shade=0.6, bottom=True)
    return mb.object("OA_BrokenBridge", coll, mat)


# ---------- the Origin Altar ----------
AX, AZ, AR = O.ALTAR
ALTAR_FLOOR = 7.0
DAIS_TOP = ALTAR_FLOOR + 2.4


RING_R = 13.0
SNAPPED = 3     # this monolith broke; its top lies on the ground outside the ring
TOPPLING = 7    # this one leans hard outward


def monoliths():
    """The ring's nine hewn slabs: position, size, lean and the slope of each cut top."""
    rnd = random.Random(621)
    out = []
    for k in range(9):
        a = TAU * k / 9 + 0.2 + rnd.uniform(-0.08, 0.08)
        o, tg = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        lean_out = 0.2 if k == TOPPLING else rnd.uniform(0.02, 0.09)
        lean_tan = rnd.uniform(-0.05, 0.05)
        out.append({
            "x": AX + o[0] * RING_R, "z": AZ + o[1] * RING_R, "out": o, "tan": tg,
            "h": rnd.uniform(3.5, 4.5) if k == SNAPPED else rnd.uniform(9.5, 13.5),
            "full": rnd.uniform(10, 12),
            "w": rnd.uniform(1.6, 2.3), "t": rnd.uniform(0.75, 1.0),
            "lean": (o[0] * lean_out + tg[0] * lean_tan, o[1] * lean_out + tg[1] * lean_tan),
            "cut": rnd.uniform(-1.4, 1.4),
            "glyphs": [rnd.randrange(len(GLYPHS)) for _ in range(3)],
        })
    return out


MONO_BASE = ALTAR_FLOOR - 1.5


def mono_point(m, y, sx, sz):
    """A point on monolith m at height y: sx across its width, sz through its thickness (-1..1)."""
    taper = 1 - 0.15 * (y - MONO_BASE) / (ALTAR_FLOOR + m["h"] - MONO_BASE)
    lx, lz = m["lean"][0] * (y - ALTAR_FLOOR), m["lean"][1] * (y - ALTAR_FLOOR)
    return (m["x"] + lx + (m["tan"][0] * m["w"] * sx + m["out"][0] * m["t"] * sz) * taper, y,
            m["z"] + lz + (m["tan"][1] * m["w"] * sx + m["out"][1] * m["t"] * sz) * taper)


def altar(coll, mat, bands):
    """The Origin Altar (island-local): a ring of nine hewn obsidian slabs around a three-step dais of
    ancient stone with a bronze inlay ring. The slabs lean; one has snapped and its top lies fallen
    outside the ring."""
    mb = W.MeshBuilder()
    rnd = random.Random(622)
    for r, y in ((7.5, ALTAR_FLOOR + 0.8), (5.6, ALTAR_FLOOR + 1.6), (3.8, DAIS_TOP)):
        mb.lathe([(r - 0.3, y, 0.95), (r, y - 0.15, 0.85), (r, ALTAR_FLOOR - 1.0, 0.5)], 24, bands[RUIN], centre=(AX, 0, AZ),
                 cap_top=True, u_repeat=2.0)
    for i in range(32):
        a0, a1 = TAU * i / 32, TAU * (i + 1) / 32
        p = lambda rr, a: (AX + math.cos(a) * rr, DAIS_TOP + 0.02, AZ + math.sin(a) * rr)
        oriented(mb, [p(2.4, a0), p(2.8, a0), p(2.8, a1), p(2.4, a1)], (0, 1, 0), bands[BRONZE], 0.5, [1.0] * 4)
    for k, m in enumerate(monoliths()):
        corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
        bot = [mono_point(m, MONO_BASE, sx, sz) for sx, sz in corners]
        if k == SNAPPED:
            tops = [ALTAR_FLOOR + m["h"] + rnd.uniform(-0.7, 0.7) for _ in corners]
        else:
            tops = [ALTAR_FLOOR + m["h"] + m["cut"] * sx for sx, _ in corners]   # a single slanted cut
        top = [mono_point(m, y, sx, sz) for y, (sx, sz) in zip(tops, corners)]
        for i in range(4):
            j = (i + 1) % 4
            sx, sz = corners[i][0] + corners[j][0], corners[i][1] + corners[j][1]
            normal = (m["tan"][0] * sx + m["out"][0] * sz, 0, m["tan"][1] * sx + m["out"][1] * sz)
            oriented(mb, [bot[i], bot[j], top[j], top[i]], normal, bands[OBSIDIAN], 0.3 + 0.07 * k, [0.3, 0.3, 0.9, 0.9])
        if k == SNAPPED:   # a jagged break, then the fallen top lying outward on the ground
            c = mono_point(m, ALTAR_FLOOR + m["h"] + 0.9, 0, 0)
            for i in range(4):
                oriented(mb, [top[i], top[(i + 1) % 4], c], (0, 1, 0), bands[OBSIDIAN], 0.5, [0.75] * 3)
            length = m["full"] - m["h"]
            d = RING_R + 2.5 + length / 2
            fx, fz = AX + m["out"][0] * d, AZ + m["out"][1] * d
            mb.box((fx, ground(fx, fz) + m["t"] - 0.5, fz), (m["w"] * 1.8, m["t"] * 2, length), bands[OBSIDIAN],
                   yaw=math.atan2(m["out"][0], m["out"][1]) + 0.25, u=0.6, top_shade=0.9, side_shade=0.6, bottom=True)
        else:
            oriented(mb, top, (0, 1, 0), bands[OBSIDIAN], 0.5, [1.0] * 4)
    return mb.object("OA_Altar", coll, mat)


# glyphs of the old script: invented seal-script marks, as strokes in a unit cell (u across, v up)
GLYPHS = [
    [(0.15, 0.85, 0.85, 0.85), (0.05, 0.6, 0.95, 0.6), (0.5, 0.85, 0.5, 0.6), (0.5, 0.6, 0.12, 0.0), (0.5, 0.6, 0.88, 0.0)],
    [(0.2, 0.3, 0.8, 0.3), (0.2, 0.7, 0.8, 0.7), (0.2, 0.3, 0.2, 0.7), (0.8, 0.3, 0.8, 0.7), (0.5, 0.7, 0.5, 1.0), (0.35, 0.0, 0.65, 0.3)],
    [(0.1, 0.1, 0.9, 0.1), (0.1, 0.1, 0.1, 0.55), (0.5, 0.1, 0.5, 0.95), (0.9, 0.1, 0.9, 0.55), (0.3, 0.75, 0.7, 0.75)],
    [(0.15, 0.9, 0.85, 0.9), (0.85, 0.9, 0.85, 0.2), (0.85, 0.2, 0.3, 0.2), (0.3, 0.2, 0.3, 0.6), (0.3, 0.6, 0.6, 0.6)],
    [(0.1, 0.95, 0.9, 0.95), (0.3, 0.95, 0.3, 0.0), (0.7, 0.95, 0.7, 0.4), (0.7, 0.4, 0.95, 0.15), (0.3, 0.5, 0.55, 0.5)],
]


def stroke(mb, a, b, normal, width, band):
    ax_, ay, az_ = a; bx, by, bz = b
    d = W.Vector((bx - ax_, by - ay, bz - az_)).normalized()
    side = d.cross(W.Vector(normal)).normalized() * width / 2
    q = [tuple(W.Vector(a) - side), tuple(W.Vector(b) - side), tuple(W.Vector(b) + side), tuple(W.Vector(a) + side)]
    oriented(mb, q, normal, band, 0.5, [1.0] * 4)


def altar_runes(coll, mat, bands):
    """The glowing parts of the altar (Neon in Roblox): glyphs cut into the inner face of each standing
    slab, and a spiral void sigil on the dais (the same spiral that turns inside the abyss eggs)."""
    mb = W.MeshBuilder()
    for k, m in enumerate(monoliths()):
        count = 1 if k == SNAPPED else 3
        for j in range(count):
            y0 = ALTAR_FLOOR + 1.8 + j * 2.5
            normal = (-m["out"][0], 0, -m["out"][1])
            def at(u, v):   # a point on the inner face, just proud of it
                x, y, z = mono_point(m, y0 + v * 1.6, (u - 0.5) * 1.1, -1)
                return (x - m["out"][0] * 0.04, y, z - m["out"][1] * 0.04)
            for u0, v0, u1, v1 in GLYPHS[m["glyphs"][j]]:
                stroke(mb, at(u0, v0), at(u1, v1), normal, 0.2, bands[GLOW])
    turns, r0, r1, n = 2.25, 0.25, 2.1, 54
    prev = None
    for i in range(n + 1):
        t = i / n
        a = TAU * turns * t
        r = r0 + (r1 - r0) * t
        p = (AX + math.cos(a) * r, DAIS_TOP + 0.04, AZ + math.sin(a) * r)
        if prev:
            stroke(mb, prev, p, (0, 1, 0), 0.16 + 0.14 * t, bands[GLOW])
        prev = p
    return mb.object("OA_AltarRunes", coll, mat)


# ---------- temple paving ----------
def temple_paving(coll, mat, bands):
    """Hewn paving slabs on the three temple terraces (gate, egg shrine, altar), laid in staggered
    rings. Stones are missing toward each terrace's worn edge, showing the slate beneath."""
    mb = W.MeshBuilder()
    rnd = random.Random(671)
    for (cx, cz, rad), lift, inner in ((O.GATE, 0.5, 0.0), (O.SHRINE, 0.8, 0.0), (O.ALTAR, ALTAR_FLOOR, 7.7)):
        r0 = inner
        while r0 < rad - 1.0:
            r1 = min(r0 + 2.6, rad - 0.4)
            n = max(5, round(TAU * (r0 + r1) / 2 / 2.8))
            offset = rnd.uniform(0, TAU)
            for k in range(n):
                if rnd.random() < 0.05 + 0.35 * (r1 / rad) ** 3:
                    continue
                a0 = offset + TAU * k / n + 0.12 / max(r1, 1)
                a1 = offset + TAU * (k + 1) / n - 0.12 / max(r1, 1)
                ra, rb = r0 + 0.12, r1 - 0.12
                if ra < 0.5:   # the centre stone
                    corners = [(rb, a0), (rb, a1), (0.0, 0.0)]
                else:
                    corners = [(ra, a0), (rb, a0), (rb, a1), (ra, a1)]
                poly = [(cx + math.cos(a) * r + rnd.uniform(-0.12, 0.12), cz + math.sin(a) * r + rnd.uniform(-0.12, 0.12))
                        for r, a in corners]
                top = lift + 0.12 + rnd.uniform(-0.05, 0.05)
                SP.slab_tile(mb, poly, top, lift - 0.3, bands[RUIN], rnd.random(), rnd.uniform(0.75, 0.95))
            r0 = r1
    return mb.object("OA_TemplePaving", coll, mat)


# ---------- the Void Shard and its climb ----------
# Each stage of the climb rises 49 studs: seven air leaps (Void Walker, peak 55) clear it with room
# to land; six (Divine Initiate, peak 48) fall short.
CLIMB_RISE = 49.0
FRAGMENT_TOPS = [ALTAR_FLOOR + CLIMB_RISE * k for k in (1, 2, 3)]
SHARD_FLOOR = FRAGMENT_TOPS[-1]     # the top of the climb, under the shard


def fragment_positions():
    """The climb: two fragments spiralling up around the shard's axis, then the shard floor
    directly beneath it. Each rises 49 studs: within seven air leaps' reach (55), out of six's (48)."""
    out = []
    for k, top in enumerate(FRAGMENT_TOPS[:2]):
        a = 0.6 + k * 2.1
        out.append(((AX + math.cos(a) * 24, top, AZ + math.sin(a) * 24), -a))
    out.append(((AX, SHARD_FLOOR, AZ), 0.0))
    return out


SHARD_C = SHARD_FLOOR + 30      # the shard's widest point
SHARD_CHAINS = [0.4 + k * TAU / 3 for k in range(3)]   # bearings of the chains that hold it to its floor
SHARD_ANCHOR_R = 5.5                                   # inside the floor's narrowest edge


def void_shard(coll, mat, bands):
    """The Void Shard: a towering crystal of obsidian glass above the climb's top, with splinters
    circling it (island-local)."""
    mb = W.MeshBuilder()
    c = (AX, SHARD_C, AZ)
    JM.crystal_prism(mb, c, (0.08, 1, 0.05), 30.0, 6.0, bands[OBSIDIAN], 1)
    JM.crystal_prism(mb, c, (-0.08, -1, -0.05), 16.0, 6.0, bands[OBSIDIAN], 2)
    for k in range(6):
        a = TAU * k / 6 + 0.3
        p = (AX + math.cos(a) * 12, SHARD_C - 6 + (k % 3) * 6, AZ + math.sin(a) * 12)
        JM.crystal_prism(mb, p, (math.cos(a) * 0.3, 1 if k % 2 else -1, math.sin(a) * 0.3), 6.0, 1.1, bands[VOID], 10 + k)
    return mb.object("OA_VoidShard", coll, mat)


def shard_chains(coll, mat, bands):
    """The three chains that hold the shard down to the floor beneath it."""
    mb = W.MeshBuilder()
    for a in SHARD_CHAINS:
        chain_links(mb, (AX + math.cos(a) * SHARD_ANCHOR_R, SHARD_FLOOR + 1.2, AZ + math.sin(a) * SHARD_ANCHOR_R),
                    (AX + math.cos(a) * 3.0, SHARD_C - 8, AZ + math.sin(a) * 3.0), 3.0, 0.9, bands[IRON])
    return mb.object("OA_ShardChains", coll, mat)


def shard_core(coll, mat, bands):
    """The light inside the shard (Neon in Roblox), seen through its translucent glass."""
    mb = W.MeshBuilder()
    c = (AX, SHARD_C, AZ)
    JM.crystal_prism(mb, c, (0.08, 1, 0.05), 26.0, 3.0, bands[GLOW], 3)
    JM.crystal_prism(mb, c, (-0.08, -1, -0.05), 13.0, 3.0, bands[GLOW], 4)
    return mb.object("OA_ShardCore", coll, mat)


def torn_underside(mb, poly, rnd, bands, depth):
    """Rock torn away beneath a floating slab: jittered rings narrowing to an off-centre point."""
    # Each deeper ring is the slab's outline scaled down as a whole and drifted off-centre, with only
    # a small wobble per corner: jittering corners independently twists the faces between rings.
    rings, centres = [], []
    for s, y in ((1.0, -1.2), (0.75, -1.2 - depth * 0.35), (0.45, -1.2 - depth * 0.7)):
        if s < 1:
            s *= rnd.uniform(0.9, 1.1)
        ox, oz = (rnd.uniform(-1.5, 1.5) * (1 - s), rnd.uniform(-1.5, 1.5) * (1 - s)) if s < 1 else (0.0, 0.0)
        wob = (lambda: rnd.uniform(0.95, 1.05)) if s < 1 else (lambda: 1.0)
        rings.append([(x * s * wob() + ox, y + (rnd.uniform(-0.6, 0.6) if s < 1 else 0), z * s * wob() + oz) for x, z in poly])
        centres.append(W.Vector((ox, y, oz)))
    n = len(poly)
    for k in range(len(rings) - 1):
        c = (centres[k] + centres[k + 1]) / 2
        for i in range(n):
            j = (i + 1) % n
            q = [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]]
            mid = W.Vector([sum(p[m] for p in q) / 4 for m in range(3)])
            out = mid - c
            out.y = -0.3   # sides of the torn rock: outward from the rings' centres, a little down
            oriented(mb, q, tuple(out), bands[FRACTURE], rnd.random(), [0.8 - 0.25 * k] * 4)
    tip = W.Vector((centres[-1].x + rnd.uniform(-0.8, 0.8), -1.2 - depth, centres[-1].z + rnd.uniform(-0.8, 0.8)))
    for i in range(n):
        j = (i + 1) % n
        tri = [rings[-1][i], rings[-1][j], tuple(tip)]
        mid = W.Vector([sum(p[m] for p in tri) / 3 for m in range(3)])
        out = mid - centres[-1]
        out.y = -0.6
        oriented(mb, tri, tuple(out), bands[FRACTURE], rnd.random(), [0.25] * 3)


def fragment_poly(rnd, size):
    return [(math.cos(TAU * i / 7 + rnd.uniform(-0.2, 0.2)) * size * rnd.uniform(0.8, 1.1),
             math.sin(TAU * i / 7 + rnd.uniform(-0.2, 0.2)) * size * rnd.uniform(0.8, 1.1)) for i in range(7)]


def ruin_fragment(coll, mat, bands):
    """A floating piece of the shattered temple (origin at its top centre): cracked paving, a
    snapped column at one edge and a fallen block, torn rock beneath with a dangling chain."""
    rnd = random.Random(631)
    mb = W.MeshBuilder()
    poly = fragment_poly(rnd, 6.0)
    SP.slab_tile(mb, poly, 0.0, -1.2, bands[RUIN], 0.4, 0.95)
    torn_underside(mb, poly, rnd, bands, 9.0)
    sx, sz = poly[2][0] * 0.72, poly[2][1] * 0.72
    h = 3.2
    mb.lathe([(0.95, h, 0.9), (1.05, h - 0.3, 0.85), (1.05, 0.0, 0.6)], 8, bands[RUIN], centre=(sx, 0, sz), cap_top=True, u_repeat=1.0)
    mb.box((poly[5][0] * 0.5, 0.55, poly[5][1] * 0.5), (1.6, 1.1, 3.4), bands[RUIN], yaw=1.1, u=0.6, top_shade=0.9, side_shade=0.6)
    chain_links(mb, (poly[0][0] * 0.4, -3.0, poly[0][1] * 0.4), (poly[0][0] * 0.45, -14.0, poly[0][1] * 0.45 + 0.4), 2.2, 0.7, bands[IRON])
    return mb.object("OA_RuinFragment", coll, mat)


def shard_floor(coll, mat, bands):
    """The top of the climb, beneath the Void Shard (origin at its top centre): a wider slab with
    the bronze rings the shard's chains are fastened to."""
    rnd = random.Random(641)
    mb = W.MeshBuilder()
    poly = fragment_poly(rnd, 8.5)
    SP.slab_tile(mb, poly, 0.0, -1.2, bands[RUIN], 0.4, 0.95)
    torn_underside(mb, poly, rnd, bands, 12.0)
    for a in SHARD_CHAINS:
        mb.lathe([(0.5, 1.3, 0.9), (0.9, 1.0, 0.95), (0.9, 0.0, 0.6)], 8, bands[BRONZE],
                 centre=(math.cos(a) * SHARD_ANCHOR_R, 0, math.sin(a) * SHARD_ANCHOR_R), cap_top=True, u_repeat=1.0)
    return mb.object("OA_ShardFloor", coll, mat)


# ---------- kit: the gate ----------
def slab_between(mb, a, b, half_w, half_h, band, u=0.5):
    """A rectangular beam from a to b (Roblox space), its width kept horizontal."""
    a, b = W.Vector(a), W.Vector(b)
    axis = (b - a).normalized()
    side = axis.cross(W.Vector((0, 1, 0))).normalized()
    up = side.cross(axis).normalized()
    if up.y < 0:
        up = -up
    corners = lambda c: [tuple(c + side * sx * half_w + up * sy * half_h) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    q0, q1 = corners(a), corners(b)
    for i in range(4):
        j = (i + 1) % 4
        mid = W.Vector([(q0[i][n] + q0[j][n]) / 2 for n in range(3)]) - a
        oriented(mb, [q0[i], q0[j], q1[j], q1[i]], tuple(mid), band, u + 0.1 * i, [0.9 if mid.dot(up) > 0 else 0.6] * 4)
    oriented(mb, q0, tuple(-axis), band, u, [0.75] * 4)
    oriented(mb, q1, tuple(axis), band, u, [0.75] * 4)


def gate_of_descent(coll, mat, bands):
    """The Gate of Descent (origin at ground centre; the path runs through it along Z): two massive
    carved pillars, one intact under its capital, one snapped at mid-height. The lintel cracked and
    dropped at that end, so it now lies slanted from the capital down onto the stump; rubble from
    the break lies at the foot."""
    mb = W.MeshBuilder()
    TALL, STUMP = 15.0, 8.0
    for side_, h in ((-1, TALL), (1, STUMP)):
        x = side_ * 6.5
        mb.lathe([(2.6, 1.2, 0.85), (3.0, 0.9, 0.75), (3.0, -1.5, 0.45)], 8, bands[RUIN], centre=(x, 0, 0), cap_top=True, u_repeat=1.0)
        mb.lathe([(2.0, h, 0.95), (2.1, h - 0.5, 0.9), (2.0, 1.2, 0.6)], 8, bands[RUIN], centre=(x, 0, 0), cap_top=(side_ < 0), u_repeat=1.5)
        if side_ < 0:
            mb.lathe([(3.1, h + 1.6, 1.0), (3.2, h + 1.2, 0.9), (2.3, h + 0.2, 0.75)], 8, bands[RUIN], centre=(x, 0, 0), cap_top=True, u_repeat=1.0)
        else:
            rnd = random.Random(651)   # the snapped top
            top = [(x + math.cos(TAU * i / 8) * 2.0, h + rnd.uniform(-0.8, 0.6), math.sin(TAU * i / 8) * 2.0) for i in range(8)]
            for i in range(8):
                oriented(mb, [top[i], top[(i + 1) % 8], (x, h + 0.2, 0)], (0, 1, 0), bands[RUIN], 0.5, [0.7] * 3)
    # the lintel: resting on the capital at one end, dropped onto the stump at the other, overhanging both
    a = W.Vector((-9.5, TALL + 2.6, 0.0))
    b = W.Vector((9.0, STUMP + 0.9, 0.6))
    slab_between(mb, a, b, 1.8, 1.0, bands[RUIN])
    rnd = random.Random(652)
    for k in range(5):   # rubble around the foot of the broken pillar, on the side away from the walkway
        ang = math.radians(-100 + 50 * k + rnd.uniform(-12, 12))
        d = rnd.uniform(3.8, 6.0)
        x, z = 6.5 + math.cos(ang) * d, math.sin(ang) * d
        size = rnd.uniform(1.0, 1.9)
        mb.box((x, size * 0.35, z), (size * 1.3, size * 0.9, size), bands[RUIN], yaw=rnd.uniform(0, 3), u=0.4,
               top_shade=0.9, side_shade=0.6)
    return mb.object("OA_GateOfDescent", coll, mat)


# ---------- placements ----------
def gate_frame():
    gx, gz = O.GATE[0], O.GATE[1]
    a, b = O.PATHS[0][0], O.PATHS[0][1]
    return (gx, ground(gx, gz) - 0.3, gz), math.atan2(b[0] - a[0], b[1] - a[1])


def relic_positions():
    return {
        "OriginAltar": (AX, DAIS_TOP + 3.0, AZ),
        "VoidShard": (AX, SHARD_FLOOR + 3.0, AZ),
    }


ISLAND_PIECES = [under_chunks, void_core, rift_chains, rift_veil, broken_bridge, altar, altar_runes, temple_paving, void_shard,
                 shard_core, shard_chains]
KIT_PIECES = [gate_of_descent, ruin_fragment, shard_floor]


def build():
    img, bands = W.atlas_image("OriginAbyss_Atlas", 512, STRIPS)
    mat = W.textured_material("OriginAbyss_Mat", img)
    root = W.collection(O.NAME)
    island = W.collection("OA_Island", root)
    kit = W.collection("OA_Kit", root)
    W.clear_collection(island); W.clear_collection(kit)
    return [f(island, mat, bands) for f in ISLAND_PIECES], [f(kit, mat, bands) for f in KIT_PIECES], img


def kit_entries():
    gate, gate_yaw = gate_frame()
    frags = fragment_positions()
    return {
        "OA_GateOfDescent": [(gate, gate_yaw, 1.0)],
        "OA_RuinFragment": [(p, y, 1.0) for p, y in frags[:2]],
        "OA_ShardFloor": [frags[2][0:2] + (1.0,)],
    }


def write_placements(extra_kit=None, extra_lines=(), path=W.REPO + "/src/worldbuild/Placements/OriginAbyss.lua"):
    kit = kit_entries()
    for name, entries in (extra_kit or {}).items():
        kit.setdefault(name, []).extend(entries)
    lines = ["-- Generated by tools/blender/world/origin_meshes.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin.", "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in kit[name]:
            extra = ", Scale = %.3f" % scale if abs(scale - 1) > 1e-6 else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, yaw, extra))
        lines.append("        },")
    lines.append("    },")
    lines += list(extra_lines)
    gx, gz = O.GATE[0], O.GATE[1]
    lines.append("    Checkpoint = Vector3.new(%.2f, %.2f, %.2f)," % (gx, ground(gx, gz) + 0.5, gz + 6))
    lines.append("    Relics = {")
    for rid, (x, y, z) in relic_positions().items():
        lines.append("        %s = Vector3.new(%.2f, %.2f, %.2f)," % (rid, x, y, z))
    lines.append("    },")
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def export():
    island, kit, img = build()
    out = W.REPO + "/assets/world/OriginAbyss/"
    W.export_batch(island, out + "OriginAbyss_Island.fbx", image=img, anchor_name="OA_Anchor")
    W.export_batch(kit, out + "OriginAbyss_Kit.fbx", anchor_name="OA_KitAnchor")
    import origin_props   # the set pieces add their kit entries and egg stands to the same placements file
    origin_props.write_all()
    return island + kit

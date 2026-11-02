"""Origin Abyss set pieces, batch 2. Uses the Origin Abyss atlas from origin_meshes.

- The egg shrine: three obsidian plinths cracked with void light, each cradled by thorny bronze
  branches (after the Origin Abyss egg design), under the Thorn Crown: seven great bronze
  branches rooted behind the shrine and arching over it.
- The fallen colossus: a giant stone head sunk into the ground on the back of its skull, its face
  turned up toward the path in, still wearing its thorned bronze circlet. Void light shows through its eyes and through a crack across its face.
- Ruins along the avenue: snapped columns and fallen column drums.
- Island dressing: void crystal clusters (glass around glowing cores) and slate rocks.
"""
import math, random
import worldlib as W
import origin_island as O
import origin_meshes as OM
import start_props as SP
import jade_meshes as JM

TAU = 2 * math.pi
V = W.Vector
oriented = SP.oriented
ground = OM.ground


# ---------- shared shapes ----------
def thorn(mb, base, out, along, length, width, band):
    """A three-sided thorn growing from `base` toward `out`, raked back along `along`."""
    base, out, along = V(base), V(out).normalized(), V(along).normalized()
    side = out.cross(along).normalized()
    tip = base + (out + along * 0.45).normalized() * length
    ring = [base + along * width, base - along * width * 0.5 + side * width * 0.87, base - along * width * 0.5 - side * width * 0.87]
    axis = (tip - base).normalized()
    for i in range(3):
        a, b = ring[i], ring[(i + 1) % 3]
        side_out = (a + b) / 2 - base
        side_out = (side_out - axis * side_out.dot(axis)).normalized()   # away from the thorn's own axis
        oriented(mb, [tuple(a), tuple(b), tuple(tip)], tuple(side_out + axis * 0.2), band, 0.5, [0.6, 0.6, 1.0])


def thorn_branch(mb, pts, r0, r1, band, rnd, spacing, thorn_len, sides=6, per=4, skip=None):
    """A tapering bronze branch along a smooth curve, with thorns spiralling round it.
    skip(position, direction) -> True leaves a thorn out (e.g. one pointing at the egg it cradles)."""
    curve = [V(p) for p in W.catmull(pts, per)]
    W.mb_tube(mb, pts, lambda t: r0 + (r1 - r0) * t, sides, band, per=per)
    run, k = 0.0, 0
    n = len(curve)
    for i in range(1, n - 1):
        run += (curve[i] - curve[i - 1]).length
        if run < spacing:
            continue
        run, k = 0.0, k + 1
        t = i / (n - 1)
        T = (curve[i + 1] - curve[i - 1]).normalized()
        ref = V((0, 1, 0)) if abs(T.y) < 0.9 else V((1, 0, 0))
        s = T.cross(ref).normalized()
        u = s.cross(T)
        ang = k * 2.4 + rnd.uniform(-0.4, 0.4)
        out = s * math.cos(ang) + u * math.sin(ang)
        r = r0 + (r1 - r0) * t
        if skip and skip(curve[i], out):
            continue
        thorn(mb, curve[i] + out * r * 0.8, out, -T, thorn_len * (1 - 0.55 * t), r * 0.55, band)


def closed_tube(mb, pts, r, sides, band):
    """A tube round a closed loop of points (no end caps, nothing left inside it)."""
    pts = [V(p) for p in pts]
    n = len(pts)
    centre = sum(pts, V((0, 0, 0))) / n
    rings = []
    for i in range(n):
        T = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        out = pts[i] - centre
        out = (out - T * out.dot(T)).normalized()
        up = T.cross(out)
        rings.append([out * math.cos(TAU * k / sides) + up * math.sin(TAU * k / sides) for k in range(sides)])
    for i in range(n):
        j = (i + 1) % n
        for k in range(sides):
            m = (k + 1) % sides
            quad = [tuple(pts[i] + rings[i][k] * r), tuple(pts[i] + rings[i][m] * r), tuple(pts[j] + rings[j][m] * r), tuple(pts[j] + rings[j][k] * r)]
            oriented(mb, quad, tuple(rings[i][k] + rings[i][m] + rings[j][k] + rings[j][m]), band, (k + 0.5) / sides, [0.85] * 4)


def drum_between(mb, a, b, r, sides, band, u=0.5, chamfer=0.25):
    """A column drum from a to b: a cylinder with chamfered, capped ends."""
    a, b = V(a), V(b)
    d = (b - a).normalized()
    ref = V((0, 1, 0)) if abs(d.y) < 0.9 else V((1, 0, 0))
    s = d.cross(ref).normalized()
    t = d.cross(s)
    dirs = [s * math.cos(TAU * k / sides) + t * math.sin(TAU * k / sides) for k in range(sides)]
    rings = [[tuple(c + q * rr) for q in dirs] for c, rr in ((a, r - chamfer), (a + d * chamfer, r), (b - d * chamfer, r), (b, r - chamfer))]
    for i in range(3):
        for k in range(sides):
            j = (k + 1) % sides
            mid = (dirs[k] + dirs[j]) / 2 + d * (-0.7 if i == 0 else 0.7 if i == 2 else 0.0)
            shade = 0.55 + 0.4 * max(0.0, mid.normalized().y)
            oriented(mb, [rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]], tuple(mid), band, u + 0.1 * k / sides, [shade] * 4)
    oriented(mb, rings[0], tuple(-d), band, u, [0.7] * sides)
    oriented(mb, rings[3], tuple(d), band, u, [0.7] * sides)


# ---------- the egg shrine ----------
SHRINE_FLOOR = O.ARENA_Y
PEDESTAL_TOP = 2.2      # the egg rests here
CRACK_FACES = (0, 3, 5)   # the plinth faces with void light showing through their cracks
PLINTH_R = 1.3            # the upper plinth's radius (8-sided)


def egg_pedestal(coll, mat, bands):
    """A two-tier obsidian plinth with a shallow cup for the egg, cradled by five thorny bronze
    branches that rise from the lower tier and flare outward past the egg's waist (origin at the
    ground; the egg rests at PEDESTAL_TOP)."""
    mb = W.MeshBuilder()
    rnd = random.Random(701)
    top = PEDESTAL_TOP
    mb.lathe([(0.9, top, 1.0), (1.4, top + 0.15, 0.95), (1.55, top - 0.1, 0.85), (PLINTH_R, top - 0.5, 0.7), (PLINTH_R, 0.9, 0.5),
              (1.8, 0.75, 0.8), (1.9, 0.0, 0.5), (1.9, -0.6, 0.3)], 8, bands[OM.OBSIDIAN], cap_top=True, u_repeat=2.0)
    for k in range(5):
        a = TAU * k / 5 + 0.3
        pts = []
        for r, y, twist in ((1.75, 0.8, 0.0), (1.6, top - 0.3, 0.15), (1.95, top + 1.5, 0.35), (2.45, top + 2.8, 0.55), (2.95, top + 3.3, 0.7)):
            pts.append((math.cos(a + twist) * r, y, math.sin(a + twist) * r))
        # no thorns on the inside of the cradle, where they would spike the egg
        inward = lambda p, d: d.dot(-V((p.x, 0, p.z)).normalized()) > 0.1
        thorn_branch(mb, pts, 0.2, 0.05, bands[OM.BRONZE], rnd, 0.55, 0.45, sides=5, per=3, skip=inward)
    return mb.object("OA_EggPedestal", coll, mat)


def egg_glow_ring(coll, mat, bands):
    """The stand's glow, coloured per egg in Roblox: a ring on the ground and the void light in the
    plinth's cracks."""
    mb = W.MeshBuilder()
    mb.lathe([(2.0, 0.06, 1.0), (2.4, 0.06, 1.0)], 32, bands[OM.GLOW], cap_top=False, u_repeat=0.0)
    rnd = random.Random(702)
    face_d = PLINTH_R * math.cos(math.pi / 8) + 0.03
    for f in CRACK_FACES:
        a = TAU * (f + 0.5) / 8
        n = V((math.cos(a), 0, math.sin(a)))
        tang = V((-math.sin(a), 0, math.cos(a)))
        y, off = 1.0, rnd.uniform(-0.15, 0.15)
        prev = n * face_d + tang * off + V((0, y, 0))
        while y < PEDESTAL_TOP - 0.6:
            y = min(PEDESTAL_TOP - 0.6, y + rnd.uniform(0.2, 0.35))
            off = max(-0.38, min(0.38, off + rnd.uniform(-0.25, 0.25)))
            p = n * face_d + tang * off + V((0, y, 0))
            OM.stroke(mb, tuple(prev), tuple(p), tuple(n), 0.09, bands[OM.GLOW])
            prev = p
    return mb.object("OA_EggGlowRing", coll, mat)


EGG_IDS = ["ForbiddenOriginEgg", "VoidRiftEgg", "PrimordialAbyssEgg"]


def egg_layout():
    """The three plinths in their arc at the Void Court's back, each facing the lair."""
    out = []
    for eid, (x, z) in zip(EGG_IDS, O.EGG_SPOTS):
        out.append((eid, x, z, math.atan2(O.LAIR[0] - x, O.LAIR[1] - z)))
    return out


CROWN_ROOT_R = 46.0   # where the Thorn Crown's branches root, on the court's rim behind the eggs


def thorn_crown(coll, mat, bands):
    """The Thorn Crown (island-local, placed at the island origin): seven great bronze branches rooted
    on the Void Court's rim behind the egg plinths, arching up and inward over them, high overhead.
    One has snapped short."""
    rnd = random.Random(711)
    mb = W.MeshBuilder()
    back = math.radians(O.BACK_BEARING)
    R0 = CROWN_ROOT_R
    for k in range(7):
        a = back + (k - 3) * 0.2 + rnd.uniform(-0.03, 0.03)
        drift = rnd.uniform(-0.05, 0.05)
        h = rnd.uniform(15.0, 19.0)
        at = lambda r, y, da=0.0: (math.cos(a + da) * r, SHRINE_FLOOR + y, math.sin(a + da) * r)
        pts = [at(R0 + 1.2, -1.2), at(R0 + 0.8, 4.0, drift * 0.3), at(R0 - 2.5, h * 0.75, drift * 0.6), at(R0 - 9.0, h, drift),
               at(R0 - 15.0, h - 3.0, drift * 1.4)]
        if k == 3:
            pts = pts[:3]   # snapped
        thorn_branch(mb, pts, 1.6, 0.3 if k != 3 else 0.9, bands[OM.BRONZE], rnd, 2.6, 2.4, sides=6, per=3)
        for j in range(3):   # roots gripping the ground
            ra = a + (j - 1) * 0.5 + rnd.uniform(-0.15, 0.15)
            base = V(at(R0 + 1.2, -0.2))
            p1 = base + V((math.cos(ra) * 1.6, 0.25, math.sin(ra) * 1.6))
            p2 = base + V((math.cos(ra) * 3.2, -0.5, math.sin(ra) * 3.2))
            W.mb_tube(mb, [tuple(base), tuple(p1), tuple(p2)], lambda t: 0.6 - 0.4 * t, 5, bands[OM.BRONZE], per=2)
    return mb.object("OA_ThornCrown", coll, mat)


# ---------- the fallen colossus ----------
HEAD = (5.0, 6.6, 5.6)      # half width, height and depth of the head as it once stood
HEAD_SINK = 1.6             # the head's centre above the ground it lies in
ROLL, PITCH = 0.28, -0.35   # sunk on the back of its skull, face turned up toward the path in, a little askew


def spow(x, e):
    return math.copysign(abs(x) ** e, x)


def band(x, a, b, soft=0.035):
    """1 between a and b, with soft edges: a carved feature's extent."""
    lo = max(0.0, min(1.0, (x - a + soft) / (2 * soft)))
    hi = max(0.0, min(1.0, (b + soft - x) / (2 * soft)))
    return lo * hi


HEAD_E = 0.45   # superellipsoid exponent: squared off rather than round


def face_uv(fx, fy):
    """(u, v) of the point a fraction fx across and fy up the face (-1..1 each). The squared head
    maps angle to position unevenly, so features and samples are laid out in these fractions."""
    inv = lambda f: math.copysign(math.asin(min(1.0, abs(f) ** (1 / HEAD_E))), f)
    return inv(fx), inv(fy)


def head_surface(u, v):
    """A point on the head before it fell (head space, centre at the origin, face toward +Z).
    u: bearing round the head from the face; v: elevation. A squared, carved guardian's head:
    a ledge of a brow, deep-cut eye sockets, a wedge of a nose, a straight mouth slot and a
    blocky chin, in planes rather than soft bumps so it reads as carved stone."""
    rx, ry, rz = HEAD
    cv = spow(math.cos(v), HEAD_E)
    fx, fy = cv * spow(math.sin(u), HEAD_E), spow(math.sin(v), HEAD_E)   # where on the face, -1..1
    base = V((rx * fx, min(ry * fy, ry * 0.84), rz * cv * spow(math.cos(u), HEAD_E)))
    # Carve along the surface's own normal (straight out of the flat face), not out from the
    # centre: on a squared head that slides the carving sideways and folds the surface over itself.
    k = 2 / HEAD_E
    raw = V((rx * fx, ry * fy, base.z))
    d = V(tuple(math.copysign(abs(c / r_) ** (k - 1), c) / r_ for c, r_ in zip(raw, (rx, ry, rz))))
    if base.y < raw.y:   # the flat-cut crown
        d = V((0, 1, 0))
    d = d.normalized() if d.length > 1e-9 else V((0, 0, 1))
    front = band(math.cos(u), 0.2, 2.0, 0.1)   # only the face carries the features
    nose = max(0.0, min(1.0, (0.26 - fy) / 0.4))  # the nose deepens from the brow down
    face = (1.4 * band(fx, -0.78, 0.78, 0.04) * band(fy, 0.24, 0.38, 0.03)                       # brow ledge
            - 2.0 * (band(fx, 0.16, 0.56, 0.04) + band(fx, -0.56, -0.16, 0.04)) * band(fy, 0.02, 0.21, 0.03)  # eye sockets
            + 2.0 * band(fx, -0.09, 0.09, 0.03) * band(fy, -0.2, 0.26, 0.03) * nose            # nose
            - 0.5 * band(fx, -0.2, 0.2, 0.03) * band(fy, -0.28, -0.21, 0.02)                   # shadow under the nose
            - 1.1 * band(fx, -0.38, 0.38, 0.03) * band(fy, -0.45, -0.37, 0.02)                 # mouth
            + 0.7 * band(fx, -0.42, 0.42, 0.04) * band(fy, -0.78, -0.56, 0.04))                # chin
    bump = (front * face
            + 0.9 * band(abs(u), 1.35, 1.65) * band(fy, -0.3, 0.35)                            # ears
            + 0.35 * band(fy, 0.6, 0.74, 0.04)                                                 # headdress band
            + 0.25 * W.fbm(u * 2.0 + 4, v * 2.0 - 3, seed=721, octaves=3))                    # weathering
    return base + d * bump


def head_to_local(p):
    """Head space -> the kit piece's space (origin on the ground under the head; face toward +Z,
    tipped back and a little askew)."""
    x, y, z = p
    x, y = x * math.cos(ROLL) - y * math.sin(ROLL), x * math.sin(ROLL) + y * math.cos(ROLL)
    y, z = y * math.cos(PITCH) - z * math.sin(PITCH), y * math.sin(PITCH) + z * math.cos(PITCH)
    return (x, y + HEAD_SINK, z)


def colossus(coll, mat, bands):
    """The fallen colossus's head: carved stone with a weathered face, and the remains of its
    thorned bronze circlet."""
    mb = W.MeshBuilder()
    rnd = random.Random(722)
    # evenly spaced across the face (in face fractions), sparse round the back of the skull
    us = [face_uv(-1 + 2 * j / 26, 0)[0] for j in range(27)] + [math.pi / 2 + math.pi * j / 10 for j in range(1, 10)]
    us = [(u + math.pi) % TAU - math.pi for u in us]
    vs = [face_uv(0, -0.97 + 1.94 * i / 29)[1] for i in range(30)]
    M = len(us)
    rings = [[head_to_local(head_surface(u, v)) for u in us] for v in vs]
    bottom, top = head_to_local((0, -HEAD[1], 0)), head_to_local((0, HEAD[1] * 0.84, 0))
    centre = V(head_to_local((0, 0, 0)))
    def shade(p):
        return 0.45 + 0.45 * max(0.0, min(1.0, (p[1] - centre.y + HEAD[0]) / (2 * HEAD[0])))
    # Wind every face the same way round the grid. Steep socket and nose walls face sideways, so
    # pointing each face away from the centre would flip some of them (Roblox culls back faces).
    # One vote over the whole head fixes which way round is outward.
    def grid_normal(poly):
        a, b, c = V(poly[0]), V(poly[1]), V(poly[-1])
        return (b - a).cross(c - a)
    quads = [[rings[i][j], rings[i][(j + 1) % M], rings[i + 1][(j + 1) % M], rings[i + 1][j]] for i in range(len(rings) - 1) for j in range(M)]
    vote = sum(grid_normal(q).dot(V([sum(p[n] for p in q) / 4 for n in range(3)]) - centre) for q in quads)
    sign = 1 if vote > 0 else -1
    for n, q in enumerate(quads):
        oriented(mb, q, tuple(grid_normal(q) * sign), bands[OM.RUIN], (n % M) / M, [shade(p) for p in q])
    for j in range(M):
        k = (j + 1) % M
        # the pole fans continue the same winding as the rings beside them
        lower = [rings[0][k], rings[0][j], bottom]
        upper = [rings[-1][j], rings[-1][k], top]
        oriented(mb, lower, tuple(grid_normal(lower) * sign), bands[OM.RUIN], 0.5, [0.3] * 3)
        oriented(mb, upper, tuple(grid_normal(upper) * sign), bands[OM.RUIN], 0.5, [shade(top)] * 3)
    # the circlet: a bronze band above the brow, with thorns; two have broken off short
    circlet_v = face_uv(0, 0.67)[1]
    loop = [head_to_local(head_surface(u, circlet_v) * 1.05) for u in [TAU * j / 20 for j in range(20)]]
    closed_tube(mb, loop, 0.32, 5, bands[OM.BRONZE])
    for k in range(7):
        u = TAU * k / 7 + 0.2
        base = V(head_to_local(head_surface(u, circlet_v)))
        out = (V(head_to_local(head_surface(u, circlet_v + 0.1) * 1.3)) - base).normalized()
        length = rnd.uniform(0.8, 1.2) if k in (2, 5) else rnd.uniform(2.2, 3.4)
        JM.crystal_prism(mb, tuple(base), tuple(out), length, 0.4, bands[OM.BRONZE])
    return mb.object("OA_Colossus", coll, mat)


# the crack of void light across the face, from the brow through the left eye to the jaw (face fractions)
FACE_CRACK = [(-0.85, 0.5), (-0.66, 0.37), (-0.5, 0.24), (-0.36, 0.12), (-0.3, -0.02), (-0.38, -0.16), (-0.27, -0.33),
              (-0.36, -0.5), (-0.29, -0.68)]


def colossus_eyes(coll, mat, bands):
    """Void light deep in the eye sockets and along the crack across the face (Neon in Roblox)."""
    mb = W.MeshBuilder()
    for fx in (-0.36, 0.36):
        c = V(head_to_local(head_surface(*face_uv(fx, 0.115))))
        n = (c - V(head_to_local((0, 0, 0)))).normalized()
        ref = V((0, 1, 0)) if abs(n.y) < 0.9 else V((1, 0, 0))
        s = n.cross(ref).normalized(); t = n.cross(s)
        # proud of the socket floor so it shows from the path, still well inside the 2-stud socket
        ring = [tuple(c + n * 0.7 + (s * math.cos(TAU * k / 7) * 0.85 + t * math.sin(TAU * k / 7) * 0.55)) for k in range(7)]
        oriented(mb, ring, tuple(n), bands[OM.GLOW], 0.5, [1.0] * 7)
    pts = [V(head_to_local(head_surface(*face_uv(fx, fy)) * 1.012)) for fx, fy in FACE_CRACK]
    centre = V(head_to_local((0, 0, 0)))
    for a, b in zip(pts, pts[1:]):
        OM.stroke(mb, tuple(a), tuple(b), tuple((a + b) / 2 - centre), 0.16, bands[OM.GLOW])
    return mb.object("OA_ColossusEyes", coll, mat)


# ---------- ruins and dressing ----------
def ruin_pillar(coll, mat, bands):
    """A carved column snapped off about 7 studs up (origin at the ground)."""
    rnd = random.Random(731)
    mb = W.MeshBuilder()
    h = 7.0
    mb.lathe([(1.35, 0.9, 0.85), (1.6, 0.6, 0.75), (1.6, -1.0, 0.45)], 8, bands[OM.RUIN], cap_top=True, u_repeat=1.0)
    mb.lathe([(1.05, h, 0.95), (1.1, h - 0.4, 0.9), (1.05, 0.9, 0.6)], 8, bands[OM.RUIN], cap_top=False, u_repeat=1.5)
    rim = [(math.cos(TAU * i / 8) * 1.05, h + rnd.uniform(-1.2, 0.5), math.sin(TAU * i / 8) * 1.05) for i in range(8)]
    for i in range(8):
        j = (i + 1) % 8
        oriented(mb, [(rim[i][0], h - 0.4, rim[i][2]), (rim[j][0], h - 0.4, rim[j][2]), rim[j], rim[i]],
                 (math.cos(TAU * (i + 0.5) / 8), 0, math.sin(TAU * (i + 0.5) / 8)), bands[OM.RUIN], 0.5, [0.9] * 4)
        oriented(mb, [rim[i], rim[j], (0.2, h + 0.1, -0.1)], (0, 1, 0), bands[OM.RUIN], 0.5, [0.75] * 3)
    return mb.object("OA_RuinPillar", coll, mat)


def fallen_drums(coll, mat, bands):
    """Three drums of a toppled column, lying where they rolled (origin at the ground, in the middle
    of the row; the row runs along X, about DRUMS_HALF either side)."""
    rnd = random.Random(732)
    mb = W.MeshBuilder()
    drums, x = [], 0.0
    for k in range(3):
        yaw, length, cz = rnd.uniform(-0.25, 0.25), rnd.uniform(1.6, 2.2), rnd.uniform(-0.5, 0.5)
        drums.append((x + length / 2, cz, yaw, length))
        x += length + rnd.uniform(0.3, 1.2)
    shift = (drums[0][0] + drums[-1][0]) / 2
    for k, (cx, cz, yaw, length) in enumerate(drums):
        dx, dz = math.cos(yaw) * length / 2, math.sin(yaw) * length / 2
        drum_between(mb, (cx - shift - dx, 0.85, cz - dz), (cx - shift + dx, 0.85, cz + dz), 1.05, 8, bands[OM.RUIN], u=0.3 * k)
    return mb.object("OA_FallenDrums", coll, mat)


DRUMS_HALF = 4.6


def crystal_set(rnd):
    """The void crystal cluster's crystals: (base, direction, length, radius)."""
    out = []
    for k in range(rnd.randint(4, 6)):
        a = rnd.uniform(0, TAU)
        lean = rnd.uniform(0.3, 0.9) if k else 0.12   # one tall crystal at the heart, the rest fanning out
        out.append(((math.cos(a) * 0.5, -0.3, math.sin(a) * 0.5), (math.cos(a) * lean, 1, math.sin(a) * lean),
                    rnd.uniform(1.8, 4.2) * (1.4 if k == 0 else 1.0), rnd.uniform(0.35, 0.65) * (1.4 if k == 0 else 1.0)))
    return out


def void_crystals(coll, mat, bands):
    """A cluster of void crystals breaking out of the slate (glass in Roblox, over OA_VoidCrystalGlow)."""
    mb = W.MeshBuilder()
    for n, (base, d, length, r) in enumerate(crystal_set(random.Random(741))):
        JM.crystal_prism(mb, base, d, length, r, bands[OM.OBSIDIAN])
    return mb.object("OA_VoidCrystals", coll, mat)


def void_crystal_glow(coll, mat, bands):
    """The light inside each crystal (Neon in Roblox), a slimmer core along the same axis."""
    mb = W.MeshBuilder()
    for n, (base, d, length, r) in enumerate(crystal_set(random.Random(741))):
        JM.crystal_prism(mb, base, d, length * 0.85, r * 0.45, bands[OM.GLOW])
    return mb.object("OA_VoidCrystalGlow", coll, mat)


def slate_rock(coll, mat, bands):
    return SP.hull_rock("OA_SlateRock", coll, mat, bands[OM.SLATE], [((0, 0.4, 0), (2.4, 1.0, 1.7)), ((1.2, 0.2, -0.7), (1.3, 0.8, 1.2))], 751)


PIECES = {
    "OA_EggPedestal": egg_pedestal, "OA_EggGlowRing": egg_glow_ring, "OA_ThornCrown": thorn_crown,
    "OA_Colossus": colossus, "OA_ColossusEyes": colossus_eyes, "OA_RuinPillar": ruin_pillar, "OA_FallenDrums": fallen_drums,
    "OA_VoidCrystals": void_crystals, "OA_VoidCrystalGlow": void_crystal_glow, "OA_SlateRock": slate_rock,
}


def build():
    img, bands = W.atlas_image("OriginAbyss_Atlas", 512, OM.STRIPS)
    mat = W.textured_material("OriginAbyss_Mat", img)
    root = W.collection(O.NAME)
    coll = W.collection("OA_Props", root)
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in PIECES.values()], img


# ---------- placement ----------
def keep_clear():
    """Places dressing must stay out of: the terraces, the bridge heads and the colossus."""
    zones = [(O.GATE[0], O.GATE[1], O.GATE[2] + 3), (O.ARENA[0], O.ARENA[1], O.RING_R + 5), (O.ALTAR[0], O.ALTAR[1], O.ALTAR[2] + 6),
             (O.COLOSSUS[0], O.COLOSSUS[1], 11), (O.ARRIVAL[0], O.ARRIVAL[1], 12)]
    zones += [(p[0], p[1], 6) for p, _ in O.bridge_pads()]
    return zones


def free(x, z, taken, gap, edge_min):
    if O.edge_distance(x, z) < edge_min or O.path_distance(x, z) < 3.5:
        return False
    if any(math.hypot(x - a, z - b) < r for a, b, r in keep_clear()):
        return False
    return all(math.hypot(x - tx, z - tz) >= max(gap, tg) for tx, tz, tg in taken)


def seat(x, z, radius):
    """The lowest ground under a piece's footprint (its centre and a ring at `radius`), and how much
    the ground varies there. Setting a piece on the lowest point keeps its downhill edge from
    floating on a slope; uphill it simply sits deeper."""
    hs = [ground(x, z)] + [ground(x + math.cos(TAU * k / 8) * radius, z + math.sin(TAU * k / 8) * radius) for k in range(8)]
    hs = [h for h in hs if h is not None]
    return min(hs), max(hs) - min(hs)


def drum_row(x, z, dx, dz):
    """Fallen drums lying in a row along (dx, dz), parallel to the avenue so they never block it.
    Returns (yaw, ground to seat on), or None where the ground along the row is too uneven or any
    part of the row would come within 2.5 studs of a path. The row runs along the piece's X axis,
    which yaw turns to (cos yaw, -sin yaw)."""
    L_ = math.hypot(dx, dz)
    dx, dz = dx / L_, dz / L_
    reach = DRUMS_HALF + 1.0
    if min(O.path_distance(x + dx * t, z + dz * t) for t in (-reach, -reach / 2, 0, reach / 2, reach)) < 2.5:
        return None
    pts = [(x + dx * t + dz * w, z + dz * t - dx * w) for t in (-DRUMS_HALF, 0, DRUMS_HALF) for w in (-1.1, 1.1)]
    hs = [ground(px, pz) for px, pz in pts]
    if None in hs or max(hs) - min(hs) > 0.6:
        return None
    return math.atan2(-dz, dx), min(hs)


def kit_entries():
    rnd = random.Random(2031)
    kit = {}

    def add(name, x, y, z, yaw=0.0, scale=1.0):
        kit.setdefault(name, []).append(((x, y, z), yaw, scale))
    add("OA_ThornCrown", 0, 0, 0)
    cx, cz = O.COLOSSUS
    look = O.PATHS[2][-1]   # the head faces the path that leads to it
    head_yaw = math.atan2(look[0] - cx, look[1] - cz)
    head_y, _ = seat(cx, cz, 5.5)
    add("OA_Colossus", cx, head_y, cz, head_yaw)
    add("OA_ColossusEyes", cx, head_y, cz, head_yaw)
    taken = []
    # the avenue from the gate to the bridge, lined with what is left of its colonnade
    line = O.PATHS[0]
    k = 0
    for (ax, az), (bx, bz) in zip(line, line[1:]):
        L_ = math.hypot(bx - ax, bz - az)
        for step in range(1, int(L_ // 8) + 1):
            t = step * 8 / L_
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            nx, nz = -(bz - az) / L_, (bx - ax) / L_
            for side in (-1, 1):
                k += 1
                x, z = px + nx * 5.0 * side, pz + nz * 5.0 * side
                if not free(x, z, taken, 4, 3.0) or rnd.random() < 0.25:
                    continue
                drums = drum_row(x, z, bx - ax, bz - az) if k % 3 == 0 else None
                if drums:
                    yaw, low = drums
                    add("OA_FallenDrums", x, low - 0.15, z, yaw)
                else:
                    scale = rnd.uniform(0.55, 1.15)
                    add("OA_RuinPillar", x, seat(x, z, 1.6 * scale)[0] - 0.2, z, rnd.uniform(0, TAU), scale)
                taken.append((x, z, 4))
    # void crystals along the rift's lips, where the void breaks through
    placed = 0
    for _ in range(4000):
        if placed >= 24:
            break
        x, z = rnd.uniform(-170, 170), rnd.uniform(-170, 170)
        lip = abs(O.side(x, z)) - O.rift_half(x, z)
        if not 4.0 < lip < 9.0 or not free(x, z, taken, 9, 4.0):
            continue
        yaw, scale = rnd.uniform(0, TAU), rnd.uniform(0.8, 1.6)
        y = seat(x, z, 1.4 * scale)[0] - 0.2
        add("OA_VoidCrystals", x, y, z, yaw, scale)
        add("OA_VoidCrystalGlow", x, y, z, yaw, scale)
        taken.append((x, z, 9))
        placed += 1
    for _ in range(4000):
        if placed >= 40:
            break
        x, z = rnd.uniform(-170, 170), rnd.uniform(-170, 170)
        if not free(x, z, taken, 12, 5.0):
            continue
        yaw, scale = rnd.uniform(0, TAU), rnd.uniform(0.7, 1.2)
        y = seat(x, z, 1.4 * scale)[0] - 0.2
        add("OA_VoidCrystals", x, y, z, yaw, scale)
        add("OA_VoidCrystalGlow", x, y, z, yaw, scale)
        taken.append((x, z, 12))
        placed += 1
    rocks = 0
    for _ in range(4000):
        if rocks >= 30:
            break
        x, z = rnd.uniform(-170, 170), rnd.uniform(-170, 170)
        if not free(x, z, taken, 9, 3.0):
            continue
        scale = rnd.uniform(0.7, 1.4)
        add("OA_SlateRock", x, seat(x, z, 2.4 * scale)[0] - 0.55, z, rnd.uniform(0, TAU), scale)
        taken.append((x, z, 9))
        rocks += 1
    return kit


def write_all():
    lines = ['    EggStandPieces = { Pedestal = "OA_EggPedestal", GlowRing = "OA_EggGlowRing" },', "    EggStands = {"]
    for eid, x, z, yaw in egg_layout():
        lines.append('        { EggId = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, EggRest = %.2f },'
                     % (eid, x, SHRINE_FLOOR, z, yaw, PEDESTAL_TOP))
    lines.append("    },")
    OM.write_placements(extra_kit=kit_entries(), extra_lines=lines)


def export():
    objs, img = build()
    W.export_batch(objs, W.REPO + "/assets/world/OriginAbyss/OriginAbyss_Props.fbx", anchor_name="OA_PropsAnchor")
    write_all()
    return objs

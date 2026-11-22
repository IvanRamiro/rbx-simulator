"""The Orthodox sword's parts (run inside Blender): every part is built twice from the same description, as a HIGH-detail
source (real bevels, grooves cut into the steel, a wrap of real bands) and as a clean hand-built LOW game mesh with a
tenth of the triangles. The bake (sword_orthodox.py) carries the difference onto the low mesh as normal and colour maps.

Authored in Roblox studs from the grip, the point toward -Z, the blade's flats facing +-Y and its edges +-X. Positions
(z, along the weapon):

    tip -5.75     yokote (where the point begins) -5.25     blade visible from -1.62 (the collar's top: "Hilt")
    collar -1.62 .. -1.34      pavilion guard: neck -1.38, rim -0.72, brim to -0.665 (a hollow faceted bell with its mouth
    toward the hand, eight arched windows through its wall, a gilt rib on every arris, a gilt border on every window)
    fuchi -0.93 .. -0.55       grip -0.55 .. 1.38 (the hand closes on -0.5 .. 0.5)      kashira 1.38 .. 1.62
    ring pommel (a faceted gilt ring, plane XZ) centre 1.92, radius 0.30      cord, knot, pendant, tassel to about 3.85
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = math.tau
PI = math.pi

# ---- the numbers (studs) ----
Z_TIP, Z_HILT = -5.75, -1.72                 # point; where the blade's steel starts to show
Z_YOKOTE = Z_HILT + (Z_TIP - Z_HILT) * 0.88  # where the point (kissaki) begins
Z_COLLAR0, Z_COLLAR1 = -1.72, -1.44
Z_NECK, Z_RIM, Z_BRIM = -1.44, -0.64, -0.585
Z_FUCHI0, Z_FUCHI1 = -0.88, -0.55
Z_GRIP0, Z_GRIP1 = -0.55, 1.38
Z_KASHIRA0, Z_KASHIRA1 = 1.38, 1.62
RING_R = 0.30
Z_RING = Z_KASHIRA1 + RING_R                  # the ring's centre
BLADE_A0 = 0.235                              # blade half-width at the collar
BLADE_H0 = 0.078                              # blade half-thickness at the collar
BLADE_LEN = Z_HILT - Z_TIP                    # 4.13 (positive)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------- mesh plumbing ----------
def orient(hi):
    """Turns every closed component of a Hi mesh outward (a component whose signed volume is negative has its faces
    reversed): rings and caps are written in one consistent order and fixed here, once, instead of by a facing test on
    every face (which fails on a groove or any other concave section)."""
    n = len(hi.verts)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for f in hi.faces:
        r = find(f[0])
        for i in f[1:]:
            parent[find(i)] = r
    edges = {}
    for f in hi.faces:
        for k in range(len(f)):
            e = (min(f[k], f[(k + 1) % len(f)]), max(f[k], f[(k + 1) % len(f)]))
            edges[e] = edges.get(e, 0) + 1
    open_roots = set()
    for (a, b), c in edges.items():
        if c != 2:
            open_roots.add(find(a))
    vol = {}
    for fi, f in enumerate(hi.faces):
        root = find(f[0])
        p0 = V(hi.verts[f[0]])
        s = 0.0
        for k in range(1, len(f) - 1):
            s += p0.dot(V(hi.verts[f[k]]).cross(V(hi.verts[f[k + 1]])))
        vol[root] = vol.get(root, 0.0) + s / 6.0
    for fi, f in enumerate(hi.faces):
        if find(f[0]) not in open_roots and vol[find(f[0])] < 0:
            hi.faces[fi] = f[::-1]
            hi.uvs[fi] = hi.uvs[fi][::-1]
    return hi


def newell(pts):
    """The normal of a polygon (Newell's method): the side it winds counter-clockwise to."""
    n = V((0, 0, 0))
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n += V(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    return n


def centroid(pts):
    return sum(pts, V((0, 0, 0))) / len(pts)


def tube_outward(rings):
    """True when a quad written ring-point i, i+1 then the same on the next ring faces outward: that holds when the ring's Newell normal and the
    direction of travel agree. A tube of convex rings is then wound outward by construction, whatever order its rings were written in."""
    return newell(rings[0]).dot(centroid(rings[1]) - centroid(rings[0])) > 0


def ring_surface(hi, rings, uvs=None, mat=0, closed=True, cap_a=False, cap_b=False, cap_uv=(0.5, 0.5), tube=True, cap_out=None):
    """A skin over `rings` (each a list of Roblox-space points, same length, in one order). `uvs[k]` is a list of per-point
    (u, v) for ring k (or None: u round, v by ring). Caps: a fan to the ring's mean point."""
    ids = [[hi.v(p) for p in r] for r in rings]
    m = len(rings[0])
    nseg = m if closed else m - 1
    flip = tube and not tube_outward(rings)           # wound outward by construction (tube=False: a bell's profile, oriented as a closed solid)
    for k in range(len(rings) - 1):
        for i in range(nseg):
            j = (i + 1) % m
            if uvs is not None:
                wrap_u = 1.0 if (closed and j == 0) else 0.0      # the seam: the last column runs on to u + 1
                ua, ub, uc, ud = uvs[k][i], uvs[k][j], uvs[k + 1][j], uvs[k + 1][i]
                uv = [ua, (ub[0] + wrap_u, ub[1]), (uc[0] + wrap_u, uc[1]), ud]
            else:
                uv = [(i / m, k / (len(rings) - 1)), ((i + 1) / m, k / (len(rings) - 1)), ((i + 1) / m, (k + 1) / (len(rings) - 1)), (i / m, (k + 1) / (len(rings) - 1))]
            quad = [ids[k][i], ids[k][j], ids[k + 1][j], ids[k + 1][i]]
            if flip:
                quad, uv = quad[::-1], uv[::-1]
            hi.f(quad, uv, mat[k] if isinstance(mat, (list, tuple)) else mat)
    for cap, ring, pts, out in ((cap_a, ids[0], rings[0], centroid(rings[0]) - centroid(rings[1])), (cap_b, ids[-1], rings[-1], centroid(rings[-1]) - centroid(rings[-2]))):
        if cap:
            c = hi.v(centroid(pts))
            for i in range(m):
                j = (i + 1) % m
                m_ = mat[0 if out is None else (0 if ring is ids[0] else -1)] if isinstance(mat, (list, tuple)) else mat
                if cap_out is not None:
                    out = cap_out[0 if ring is ids[0] else 1]
                hi.facing([ring[i], ring[j], c], [(0, 0), (1, 0), cap_uv], tuple(out), m_)
    return ids


def smooth_by_angle(obj, angle_deg):
    """Smooth shading with a hard edge wherever two faces meet at more than `angle_deg` (the facets and arrises stay crisp)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < lim
        else:
            e.smooth = True
    bm.to_mesh(me)
    bm.free()
    return obj


def make_object(hi, name, coll, materials, smooth_angle=35.0, orient_it=True, weld=1e-5):
    if orient_it:
        orient(hi)
    o = hi.object(name, coll, materials, smooth=True, weld=weld)
    if smooth_angle is not None:
        smooth_by_angle(o, smooth_angle)
    return o


# ---------- the blade ----------
TANG_S = -0.195          # below this the blade is its tang: a narrow bar that goes into the grip (the blade proper ends at a shoulder in the bell)
TANG_A, TANG_H = 0.085, 0.034


def blade_a(s):
    """Half-width at s (0 at the collar, 1 at the point)."""
    if s < TANG_S:
        return TANG_A
    if s <= 0.88:
        return BLADE_A0 - 0.083 * (max(s, 0.0) / 0.88) ** 1.15
    u = (s - 0.88) / 0.12
    return (BLADE_A0 - 0.083) * max(0.0, 1 - u ** 1.9) ** 0.62


def blade_h(s):
    """Half-thickness: a distal taper, thinner again through the point."""
    if s < TANG_S:
        return TANG_H
    h = BLADE_H0 * (1 - 0.5 * max(s, 0.0))
    if s > 0.88:
        h *= 1 - 0.7 * (s - 0.88) / 0.12
    return h


def blade_xb(s):
    """Where the shinogi (the break between the main flat and the edge bevel) lies, as a fraction of the half-width: it runs
    straight, and in the point it swings in to meet the ridge (the yokote line)."""
    if s <= 0.88:
        return 0.74
    return 0.74 - 0.62 * ((s - 0.88) / 0.12) ** 1.2


def groove_depth(s):
    """The twin grooves (soe-hi): a squared start under the collar, a long rounded run-out."""
    if s < -0.05 or s > 0.68:
        return 0.0
    if s < 0.58:
        return 1.0
    return math.sqrt(max(0.0, 1 - ((s - 0.58) / 0.10) ** 2))


def blade_section(s, grooves):
    """The blade's cross-section at s: [(x, y, plane)] going round once: top ridge, right top face, right edge, right bottom face,
    bottom ridge, left bottom face, left edge, left top face. plane: 0 ridge band, 1 main flat, 2 groove, 3 edge bevel."""
    a, h, xb = blade_a(s), blade_h(s), blade_xb(s)
    xa = 0.12
    ya, yb = 0.90 * h, 0.52 * h

    def yB(xf):
        return ya + (yb - ya) * (xf - xa) / max(1e-6, xb - xa)

    d = 0.011 * groove_depth(s) if grooves else 0.0
    half = [(0.0, h, 0), (xa * a, ya, 0)]
    if grooves:
        g0, g1, g2, g3 = (xa + (xb - xa) * f for f in (0.0, 0.08, 0.26, 0.34))
        half += [(g0 * a, yB(g0), 1), (g1 * a, yB(g1) - d, 2), (g2 * a, yB(g2) - d, 2), (g3 * a, yB(g3), 1)]
    half += [(xb * a, yb, 1), (a, 0.0, 3)]
    pts = []
    for x, y, p in half:                     # top, right side, ridge to edge
        pts.append((x, y, p))
    for x, y, p in reversed(half[1:-1]):     # bottom, right side, edge to ridge
        pts.append((x, -y, p))
    pts.append((0.0, -h, 0))
    for x, y, p in half[1:-1]:               # bottom, left side, ridge to edge
        pts.append((-x, -y, p))
    pts.append((-a, 0.0, 3))
    for x, y, p in reversed(half[1:-1]):     # top, left side, edge to ridge
        pts.append((-x, y, p))
    return pts


def blade(detail):
    """The blade: from a root hidden in the guard (z -0.66, a flat bar into the grip) to the point, rings along it."""
    hiq = detail == "hi"
    hi = Hm.Hi()
    ss = [-0.26, -0.2, -0.19]
    if hiq:
        ss += [k / 90 * 0.86 for k in range(0, 91)] + [0.86 + k / 40 * 0.14 * 0.985 for k in range(1, 41)]
        ss = sorted(set(round(x, 5) for x in ss))
    else:
        ss += [0.0, 0.14, 0.3, 0.46, 0.62, 0.78, 0.88, 0.935, 0.975]
    rings, uvs = [], []
    for s in ss:
        z = Z_HILT - s * BLADE_LEN if s >= 0 else Z_HILT - s * BLADE_LEN
        sec = blade_section(s if s < TANG_S else max(s, 0.0), hiq)
        a = max(blade_a(s if s < TANG_S else max(s, 0.0)), 1e-5)
        rings.append([V((x, y, z)) for x, y, _ in sec])
        k0 = 0.74 / blade_xb(s if s < TANG_S else max(s, 0.0))            # u runs so the shinogi is always at |u - 0.5| = 0.37
        uvs.append([(0.5 + x / (2 * a) * k0, -z * 0.5) for x, y, _ in sec])
    ring_surface(hi, rings, uvs, cap_a=True)
    # the point: a single vertex a hair in front of the last ring, on the ridge line
    last = rings[-1]
    tip = V((0.0, 0.0, Z_TIP))
    tid = hi.v(tip)
    ids = [hi.v(p) for p in last]
    m = len(last)
    for i in range(m):
        j = (i + 1) % m
        hi.facing([ids[i], ids[j], tid], [(0.5, 3.0), (0.5, 3.0), (0.5, 3.0)], (0, 0, -1))
    return hi


# ---------- the pavilion guard ----------
def oct_rho(th, R):
    """Polar radius of a regular octagon whose corner radius is R, flats facing 0, 45, 90 ... degrees."""
    ap = R * math.cos(PI / 8)
    return ap / math.cos(((th + PI / 8) % (PI / 4)) - PI / 8)


def ell_rho(th, ax, ay):
    return 1.0 / math.sqrt((math.cos(th) / ax) ** 2 + (math.sin(th) / ay) ** 2)


NECK_AX, NECK_AY = 0.285, 0.165               # the shell's neck is an ellipse that hugs the flat blade
S0 = 0.22                                     # where the cavity's ceiling is


def flare_R(s):
    """Corner radius of the octagon at s along the flare (0 at the neck, 1 at the rim)."""
    return 0.28 + 0.56 * s ** 2.3


def flare_z(s):
    return Z_NECK + (Z_RIM - Z_NECK) * s


def corner_lift(th):
    """1 at an octagon corner, 0 mid-facet: the eaves of the brim are swept up at the corners (a hanok roof's lift)."""
    return (0.5 + 0.5 * math.cos(8 * (th - PI / 8))) ** 1.6


EAVE = 0.04       # how far the corners of the brim rise toward the point


def ring_shape(s, R, z, N, wall=0.0, eave=0.0):
    """One ring of the shell at flare position s: an ellipse at the neck blended to the octagon (R = corner radius).
    eave: how much of the corner lift this ring carries."""
    w = smoothstep(0.0, 0.4, s)
    pts = []
    for j in range(N):
        th = TAU * j / N
        rho = (1 - w) * ell_rho(th, NECK_AX - wall, NECK_AY - wall) + w * oct_rho(th, R)
        pts.append(V((rho * math.cos(th), rho * math.sin(th), z - eave * EAVE * corner_lift(th))))
    return pts


def shell_rings(detail):
    """The hollow bell as rings, neck cap to ceiling cap: (rings, per-strip materials, n_outer): the outer wall, the brim (out, down), the
    inner wall back up to the ceiling. mat 0 silver (outside), 1 gilt (the lining)."""
    hiq = detail == "hi"
    k = 4 if hiq else 2
    N = 8 * k
    n_out = 24 if hiq else 8
    n_in = 16 if hiq else 5
    rings, mats = [], []
    for q in range(n_out):                              # outer wall, neck to rim (the eaves lift toward the rim)
        s = q / (n_out - 1)
        rings.append(ring_shape(s, flare_R(s), flare_z(s), N, eave=smoothstep(0.6, 1.0, s)))
    rims = (0.90, Z_RIM), (0.90, Z_BRIM)                # the brim: out, down
    rings.append(ring_shape(1.0, rims[0][0], rims[0][1], N, eave=1.0))
    rings.append(ring_shape(1.0, rims[1][0], rims[1][1], N, eave=1.0))
    mats += [0] * (n_out + 1)
    for q in range(n_in):                               # inner wall, mouth to ceiling
        s = 1.0 - (1.0 - S0) * q / (n_in - 1)
        rings.append(ring_shape(s, flare_R(s) - 0.045, flare_z(s) + 0.055, N, wall=0.045, eave=smoothstep(0.6, 1.0, s)))
    mats += [1] * n_in
    return rings, mats, n_out


def shell(detail):
    hi = Hm.Hi()
    rings, mats, _ = shell_rings(detail)
    ring_surface(hi, rings, mat=mats, cap_a=True, cap_b=True, tube=False, cap_out=((0, 0, -1), (0, 0, 1)))      # the neck's cap faces the point, the ceiling's the mouth
    return hi


WIN_S0, WIN_S1, WIN_W = 0.36, 0.90, 0.21


def window_arch(n=0):
    """The window cut through each facet: a tall trapezoid, wider at the rim than at the head, its corners chamfered (a lantern window, not a pointed
    arch: a pointed outline reads as a leaf in a texture). [(u, z)] round once; the head is toward the blade."""
    z0, z1 = flare_z(WIN_S0), flare_z(WIN_S1)
    bw, tw, c, cb = WIN_W / 2, WIN_W * 0.30, 0.03, 0.02
    return [(-bw + cb, z1), (bw - cb, z1), (bw, z1 - cb), (tw, z0 + c), (tw - c, z0), (-tw + c, z0), (-tw, z0 + c), (-bw, z1 - cb)]


def window_cutters(detail):
    """Eight prisms, one through each facet, radial; subtracted from the shell."""
    hiq = detail == "hi"
    hi = Hm.Hi()
    loop = window_arch()
    for f in range(8):
        th = f * PI / 4
        n = V((math.cos(th), math.sin(th), 0))
        t = V((-math.sin(th), math.cos(th), 0))
        rings = []
        for r in (0.12, 1.3):
            rings.append([n * r + t * u + V((0, 0, z)) for u, z in loop])
        ring_surface(hi, rings, cap_a=True, cap_b=True)
    return hi


def boolean_cut(target, cutter, name="cut"):
    md = target.modifiers.new(name, "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.operand_type = "OBJECT"
    md.object = cutter
    md.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(target.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = target.data
    target.modifiers.clear()
    target.data = me
    bpy.data.meshes.remove(old)
    return target


def corner_path(f, s0, s1, n, out=0.0):
    """A polyline along the arris of the flare at corner f (angle 22.5 + 45 f degrees), from s0 to s1, lifted `out` off the surface."""
    th = PI / 8 + f * PI / 4
    pts = []
    for q in range(n + 1):
        s = s0 + (s1 - s0) * q / n
        w = smoothstep(0.0, 0.4, s)
        rho = (1 - w) * ell_rho(th, NECK_AX, NECK_AY) + w * flare_R(s) + out
        pts.append(V((rho * math.cos(th), rho * math.sin(th), flare_z(s))))
    return pts


def window_border(f, n, lift):
    """The gilt border round window f: a closed polyline lying on the facet's face, `lift` out of it."""
    th = f * PI / 4
    nrm = V((math.cos(th), math.sin(th), 0))
    tan = V((-math.sin(th), math.cos(th), 0))
    pts = []
    for u, z in window_arch(n):
        s = (z - Z_NECK) / (Z_RIM - Z_NECK)
        w = smoothstep(0.0, 0.4, s)
        ap = flare_R(s) * math.cos(PI / 8)
        pts.append(nrm * (ap + lift) + tan * u + V((0, 0, z)))
    return pts


# ---------- the gilt dressing of the guard ----------
def collar_rings(N):
    prof = [(0.255, 0.150, Z_COLLAR0), (0.284, 0.170, Z_COLLAR0 + 0.012), (0.292, 0.176, Z_COLLAR0 + 0.04), (0.292, 0.176, Z_COLLAR0 + 0.09),
            (0.284, 0.170, Z_COLLAR0 + 0.105), (0.292, 0.176, Z_COLLAR0 + 0.12), (0.292, 0.176, Z_COLLAR0 + 0.2), (0.300, 0.182, Z_COLLAR0 + 0.235),
            (0.300, 0.182, Z_COLLAR1 + 0.02), (0.288, 0.170, Z_COLLAR1 + 0.06)]
    return [[V((ell_rho(TAU * j / N, ax, ay) * math.cos(TAU * j / N), ell_rho(TAU * j / N, ax, ay) * math.sin(TAU * j / N), z)) for j in range(N)] for ax, ay, z in prof]


def collar(detail):
    """The blade collar (habaki): a tall gilt sleeve round the blade where it leaves the guard: an ellipse that hugs the flat
    blade, a rolled lip at the top, a bead at the foot. mat 0 gilt."""
    hi = Hm.Hi()
    ring_surface(hi, collar_rings(40 if detail == "hi" else 16), cap_a=True, cap_b=True)
    return hi


def ribs(detail):
    """Gilt ribs along the eight arrises of the bell and a gilt border round each window (hi only: in the game mesh they are
    painted into the colour map and cut into the normal map; the low mesh's arrises are its edge). mat 0 gilt."""
    hi = Hm.Hi()
    for f in range(8):
        pts = corner_path(f, 0.18, 1.0, 14, out=0.004)
        Hm.htube(hi, pts, lambda t: 0.021 * (1 - 0.35 * t) + 0.004, sides=6, per=2, uv_scale=3.0, tip=False, wobble=0.0)
        loop = window_border(f, 0, 0.006)
        Hm.htube(hi, loop + loop[1:3], lambda t: 0.0105, sides=6, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    n = 96 if detail == "hi" else 48
    for s_, R_, z_, r_ in ((1.0, 0.90, (Z_RIM + Z_BRIM) / 2, 0.016), (0.16, flare_R(0.16) + 0.004, flare_z(0.16), 0.013)):
        ring = ring_shape(s_, R_, z_, n, eave=1.0 if s_ == 1.0 else 0.0)
        Hm.htube(hi, ring + ring[:3], lambda t, r_=r_: r_, sides=6, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    return hi


# ---------- the grip ----------
def sup(c, s, e):
    """A superellipse point factor: cos/sin raised to 2/e keeping the sign (e 2 = an ellipse, higher = squarer)."""
    return math.copysign(abs(c) ** (2.0 / e), c), math.copysign(abs(s) ** (2.0 / e), s)


GRIP_HX, GRIP_HY, GRIP_E = 0.168, 0.128, 2.6


def grip_half(z):
    """The grip's half-width and half-thickness at z: a swell under the hand, the ends drawing in."""
    u = (z - Z_GRIP0) / (Z_GRIP1 - Z_GRIP0)
    k = 1 + 0.07 * math.sin(PI * max(0.0, min(1.0, u)))
    return GRIP_HX * k, GRIP_HY * (1 + 0.5 * (k - 1))


def _arc_table(z, n=240):
    """Fractions of the grip's perimeter at height z, against the angle: so a band can be wound at a steady slope round a squarish oval."""
    ths = np.linspace(0.0, TAU, n + 1)
    pts = np.array([[grip_point(z, t).x, grip_point(z, t).y] for t in ths])
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    return ths, cum / cum[-1]


def theta_at(z, frac):
    ths, cum = _arc_table(z)
    return float(np.interp(frac % 1.0, cum, ths))


def frac_at(z, th):
    ths, cum = _arc_table(z)
    return float(np.interp(th % TAU, ths, cum))


def grip_point(z, th, off=0.0):
    hx, hy = grip_half(z)
    cx, sx = sup(math.cos(th), math.sin(th), GRIP_E)
    x, y = (hx + off) * cx, (hy + off) * sx
    return V((x, y, z))


def core_rings(N, nz):
    z0, z1 = Z_FUCHI0 + 0.05, Z_KASHIRA0 + 0.05
    return [[grip_point(z0 + (z1 - z0) * k / (nz - 1), TAU * j / N) for j in range(N)] for k in range(nz)], z0, z1


def grip_core(detail):
    """The wooden core under the ray-skin: an oval with a squarish shoulder, from inside the mouth to under the kashira. mat 0 ray-skin."""
    hiq = detail == "hi"
    N, nz = (40, 40) if hiq else (16, 9)
    rings, z0, z1 = core_rings(N, nz)
    hi = Hm.Hi()
    uvs = [[(j / N, (z0 + (z1 - z0) * k / (nz - 1)) * 2.0) for j in range(N)] for k in range(nz)]
    ring_surface(hi, rings, uvs, cap_a=True, cap_b=True)
    return hi


WRAP_TURNS = 8
WRAP_Z0, WRAP_Z1 = Z_GRIP0 + 0.02, Z_GRIP1 - 0.02
WRAP_HALF, WRAP_THICK = 0.05, 0.012


def wrap_cross_z(m):
    """z of the m-th crossing on the top face (the diamonds' corners); the windows lie midway."""
    return WRAP_Z0 + (WRAP_Z1 - WRAP_Z0) * m / WRAP_TURNS


def wrap(detail):
    """The silk wrap (tsukamaki, the diamond pattern): two flat bands wound against each other round the grip, one lying over
    the other at every crossing. mat 0 silk. Hi only: the game mesh carries it in its normal and colour maps."""
    import secret_kit as SK
    hi = Hm.Hi()
    n = WRAP_TURNS * 40
    prof = SK.bar_profile()
    for hand, lift in ((1, 0.0), (-1, 0.0075)):
        path = []
        for i in range(n + 1):
            q = i / n
            z = WRAP_Z0 + (WRAP_Z1 - WRAP_Z0) * q
            th = theta_at(z, frac_at(z, PI / 2) + hand * WRAP_TURNS * q)
            path.append(grip_point(z, th, WRAP_THICK + 0.001 + lift))

        def up(i, pts):
            p = pts[i]
            hx, hy = grip_half(p.z)
            return V((p.x / hx ** 2, p.y / hy ** 2, 0)).normalized()
        SK.sweep(hi, path, prof, lambda t: (WRAP_HALF, WRAP_THICK), up=up, cap_start=True, cap_end=True, uv_scale=1.0)
    return hi


def _oval_ring(N, ax, ay, z):
    out = []
    for j in range(N):
        th = TAU * j / N
        cx, sx = sup(math.cos(th), math.sin(th), GRIP_E)
        out.append(V((ax * cx, ay * sx, z)))
    return out


def fuchi_sets(N):
    """[(rings, mat, cap_a, cap_b)] of the front collar. mat 0 silver, 1 gilt."""
    body = [(0.200, 0.157, Z_FUCHI0), (0.214, 0.168, Z_FUCHI0 + 0.03), (0.205, 0.160, Z_FUCHI0 + 0.1), (0.194, 0.152, Z_FUCHI0 + 0.2),
            (0.192, 0.150, Z_FUCHI1 - 0.09), (0.19, 0.148, Z_FUCHI1 - 0.01)]
    band = [(0.194, 0.152, Z_FUCHI1 - 0.2), (0.208, 0.163, Z_FUCHI1 - 0.185), (0.208, 0.163, Z_FUCHI1 - 0.115), (0.194, 0.152, Z_FUCHI1 - 0.1)]
    lip = [(0.19, 0.148, Z_FUCHI1 - 0.01), (0.178, 0.138, Z_FUCHI1 + 0.01)]
    return [([_oval_ring(N, *b) for b in body], 0, True, False), ([_oval_ring(N, *b) for b in band], 1, False, False),
            ([_oval_ring(N, *b) for b in lip], 0, False, True)]


def fuchi(detail):
    """The front collar of the grip, tucked into the bell's mouth: silver with a gilt band. mat 0 silver, 1 gilt."""
    hi = Hm.Hi()
    for rings, mat, ca, cb in fuchi_sets(40 if detail == "hi" else 16):
        ring_surface(hi, rings, mat=mat, cap_a=ca, cap_b=cb)
    return hi


def kashira_sets(N):
    """[(rings, mat, cap_a, cap_b)] of the cap: silver, a gilt band at its foot and the gilt socket the ring hangs in."""
    band = [(0.19, 0.148, Z_KASHIRA0 - 0.02), (0.212, 0.166, Z_KASHIRA0 - 0.01), (0.212, 0.166, Z_KASHIRA0 + 0.045), (0.2, 0.158, Z_KASHIRA0 + 0.055)]
    body = [(0.2, 0.158, Z_KASHIRA0 + 0.055), (0.226, 0.178, Z_KASHIRA0 + 0.1), (0.228, 0.18, Z_KASHIRA0 + 0.16), (0.19, 0.15, Z_KASHIRA0 + 0.2),
            (0.14, 0.11, Z_KASHIRA0 + 0.235), (0.12, 0.09, Z_KASHIRA1)]
    block = [[V((x * 0.075, y * 0.05, z)) for x, y in ((1, 1), (-1, 1), (-1, -1), (1, -1))] for z in (Z_KASHIRA1 - 0.05, Z_KASHIRA1 + 0.04, Z_KASHIRA1 + 0.095)]
    return [([_oval_ring(N, *b) for b in band], 1, True, False), ([_oval_ring(N, *b) for b in body], 0, False, True), (block, 1, False, True)]


def kashira(detail):
    """The cap of the grip (kashira): silver, swelling to a shoulder and drawing in to the ring's socket, a gilt band at its foot. mat 0 silver, 1 gilt."""
    hi = Hm.Hi()
    for rings, mat, ca, cb in kashira_sets(40 if detail == "hi" else 16):
        ring_surface(hi, rings, mat=mat, cap_a=ca, cap_b=cb)
    return hi


def ring_pommel(detail):
    """The ring (hwan): a faceted gilt ring in the plane of the blade's flats, hung in the kashira's socket. mat 0 gilt."""
    import secret_kit as SK
    hi = Hm.Hi()
    SK.torus(hi, V((0, 0, Z_RING)), V((0, 1, 0)), RING_R, 0.04, n=56 if detail == "hi" else 24, sides=8 if detail == "hi" else 6, uv_scale=4.0)
    return hi


# ---------- the cord, the knot, the pendant, the tassel ----------
Z_CORD0 = Z_RING + RING_R + 0.03          # where the cord leaves the hitch on the ring's far side
Z_KNOT = Z_CORD0 + 0.36
Z_JADE0, Z_JADE1 = Z_KNOT + 0.19, Z_KNOT + 0.45
Z_TASSEL0 = Z_JADE1 + 0.02
TASSEL_LEN = 0.56


def cord_x(z):
    """The cord's gentle S in the flat plane."""
    u = (z - Z_CORD0) / (Z_TASSEL0 - Z_CORD0)
    return 0.13 * math.sin(PI * 1.35 * u) * (1 - 0.35 * u)


def cord_path(z0, z1, n):
    return [V((cord_x(z0 + (z1 - z0) * i / n), 0.0, z0 + (z1 - z0) * i / n)) for i in range(n + 1)]


def cord(detail):
    """The braided silk cord: a hitch round the ring, then two twisted strands (azure and white) down to the knot, and again from the
    knot to the pendant's cap. mat 0 azure silk, 1 white silk."""
    import secret_kit as SK
    hiq = detail == "hi"
    hi = Hm.Hi()
    SK.torus(hi, V((0, 0, Z_RING + RING_R)), V((1, 0, 0)), 0.07, 0.024, n=20 if hiq else 10, sides=6, mat=0, uv_scale=3.0)
    for z0, z1 in ((Z_CORD0 - 0.02, Z_KNOT - 0.07), (Z_KNOT + 0.07, Z_JADE0 + 0.02)):
        pts = cord_path(z0, z1, 6)
        if hiq:
            SK.strand(hi, [tuple(p) for p in pts], 0.05, turns=5.0 * (z1 - z0), strands=1, sides=5, per=6, mat=0, ratio=0.62)
            SK.strand(hi, [tuple(p) for p in pts], 0.05, turns=5.0 * (z1 - z0), strands=1, sides=5, per=6, mat=1, ratio=0.62, phase=PI)
        else:
            Hm.htube(hi, pts, lambda t: 0.034, sides=6, per=5, mat=0, uv_scale=3.0, tip=False, wobble=0.0)
    return hi


def knot(detail):
    """The maedeup, the knot of the cord: a (3,4) torus-knot cord wound into a ball on the cord's axis, with a gilt bead above and below.
    Hi: the real knot (mat 0 azure, 1 white for a second pass); low: the ball it is baked onto. mat 0 azure, 1 gilt."""
    hiq = detail == "hi"
    hi = Hm.Hi()
    cx = cord_x(Z_KNOT)
    R, r = 0.062, 0.038
    if hiq:
        p, q = 3, 4
        pts = []
        n = 160
        for i in range(n + 1):
            t = TAU * i / n
            rad = R + r * math.cos(q * t)
            pts.append(V((cx + rad * math.cos(p * t), rad * math.sin(p * t), Z_KNOT + 1.25 * r * math.sin(q * t))))
        Hm.htube(hi, pts, lambda t: 0.0155, sides=6, per=1, mat=0, uv_scale=6.0, tip=False, wobble=0.0)
    else:
        Hm.htube(hi, [V((cx, 0, Z_KNOT - 0.075)), V((cx, 0, Z_KNOT)), V((cx, 0, Z_KNOT + 0.075))],
                 lambda t: 0.105 * math.sin(math.pi * (0.04 + 0.92 * t)) ** 0.7 + 0.002, sides=10, per=4, mat=0, uv_scale=3.0, tip=False, wobble=0.0)
    for dz in (-0.085, 0.085):                      # gilt beads
        zc = Z_KNOT + dz
        rings = []
        for rr, z in ((0.030, zc - 0.018), (0.046, zc - 0.006), (0.046, zc + 0.006), (0.030, zc + 0.018)):
            rings.append([V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)])
        ring_surface(hi, rings, mat=1, cap_a=True, cap_b=True)
    return hi


def pendant(detail):
    """The pendant of the cord (norigae): a pale jade tablet, an elongated octagon with chamfered faces, in a gilt frame, hung from a
    gilt cap. mat 0 jade, 1 gilt."""
    hi = Hm.Hi()
    cx = cord_x((Z_JADE0 + Z_JADE1) / 2)
    zc = (Z_JADE0 + Z_JADE1) / 2 + 0.02
    hw, hl = 0.078, 0.14

    def octa(sx, sz, y):
        pts = [(0.55, 1.0), (1.0, 0.55), (1.0, -0.55), (0.55, -1.0), (-0.55, -1.0), (-1.0, -0.55), (-1.0, 0.55), (-0.55, 1.0)]
        return [V((cx + hw * sx * x, y, zc + hl * sz * z)) for x, z in pts]
    # the jade: a flat tablet, faces chamfered toward the rim
    ring_surface(hi, [octa(0.55, 0.62, 0.030), octa(0.86, 0.9, 0.022), octa(0.86, 0.9, -0.022), octa(0.55, 0.62, -0.030)], mat=0, cap_a=True, cap_b=True)
    # the frame: a gilt band round the rim
    ring_surface(hi, [octa(0.84, 0.88, 0.034), octa(1.0, 1.0, 0.030), octa(1.0, 1.0, -0.030), octa(0.84, 0.88, -0.034)], mat=1, cap_a=False, cap_b=False)
    # the cap and its bail
    z_cap = zc - hl - 0.02
    rings = []
    for rr, z in ((0.05, z_cap + 0.045), (0.036, z_cap + 0.02), (0.044, z_cap), (0.052, z_cap - 0.02)):
        rings.append([V((cx + rr * math.cos(TAU * j / 12), rr * 0.7 * math.sin(TAU * j / 12), z)) for j in range(12)])
    ring_surface(hi, rings, mat=1, cap_a=True, cap_b=True)
    return hi


def tassel(detail):
    """The tassel: silk threads (azure, white, a few gold) gathered under a gilt neck and a white silk binding and falling in a loose bundle.
    Hi: 40 real threads; low: a tapered bundle with a ragged end, painted by the bake. mat 0 azure, 1 white, 2 gold, 3 gilt."""
    import random
    hiq = detail == "hi"
    hi = Hm.Hi()
    cx = cord_x(Z_TASSEL0) + 0.0
    rnd = random.Random(7)
    zt = Z_TASSEL0
    # the gilt neck and the silk binding
    rings = []
    for rr, z in ((0.03, zt - 0.0), (0.05, zt + 0.02), (0.05, zt + 0.06), (0.04, zt + 0.085)):
        rings.append([V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)])
    ring_surface(hi, rings, mat=3, cap_a=True, cap_b=True)
    rings = []
    for rr, z in ((0.04, zt + 0.085), (0.06, zt + 0.11), (0.06, zt + 0.15), (0.075, zt + 0.19), (0.078, zt + 0.2)):
        rings.append([V((cx + rr * math.cos(TAU * j / 12), rr * math.sin(TAU * j / 12), z)) for j in range(12)])
    ring_surface(hi, rings, mat=1, cap_a=True, cap_b=True)
    z0 = zt + 0.2
    if hiq:
        core = [V((cx, 0.0, z0 - 0.02 + (TASSEL_LEN - 0.12) * k / 4)) for k in range(5)]
        Hm.htube(hi, core, lambda t: 0.034 * (1 - 0.45 * t) + 0.006, sides=8, per=3, mat=1, uv_scale=3.0, tip=True, wobble=0.0)
        for i in range(52):
            a = TAU * i / 52 + rnd.uniform(-0.1, 0.1)
            rho = 0.030 * math.sqrt(rnd.random()) + 0.006
            ln = TASSEL_LEN * (0.84 + 0.16 * rnd.random()) - 0.2
            mat = 2 if i % 13 == 6 else (1 if int(((a % TAU) / TAU) * 6) % 2 == 0 else 0)      # colour by sector: clean stripes round the bundle
            pts = [V((cx + rho * math.cos(a) * (1 - 0.75 * (k / 5) ** 2), rho * math.sin(a) * (1 - 0.75 * (k / 5) ** 2), z0 + ln * k / 5)) for k in range(6)]      # straight threads drawing in toward the tip: the game mesh is a tube and bakes clean stripes
            Hm.htube(hi, pts, lambda t: 0.0115 * (1 - 0.5 * t) + 0.003, sides=5, per=2, mat=mat, uv_scale=3.0, tip=True, wobble=0.0)
    else:
        N = 12
        rows = [(0.0, 0.07), (0.1, 0.082), (0.22, 0.078), (0.34, 0.068)]
        rings = []
        for k, (dz, rr) in enumerate(rows):
            ring = []
            for j in range(N):
                ln_j = 0.0
                if k == len(rows) - 1:
                    ln_j = 0.12 * (0.5 + 0.5 * math.sin(j * 2.3 + 1.0))
                ring.append(V((cx + rr * math.cos(TAU * j / N) + 0.006 * (k + 1), rr * 0.95 * math.sin(TAU * j / N), z0 + dz + ln_j)))
            rings.append(ring)
        ring_surface(hi, rings, mat=0, cap_a=True, cap_b=True)
    return hi

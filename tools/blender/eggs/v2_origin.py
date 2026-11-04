"""Origin Abyss's eggs, second generation (see egg_forge.py).

Forbidden Origin Egg, "the sealed thing": seal-stone carved with three rings of glyphs in a script
that belongs to no one, violet light in the cuts. Something inside is pushing: the stone is cracked,
and the cracks start at the seal. Real interlocking chains cross it in an X and belt its middle, and
where they meet a heavy bronze seal holds them, toothed like a lock's wheel, with a keyhole of light.

Void Rift Egg, "the tear": black glass, torn open. A jagged rift crosses the front and truly goes
in: the shell sinks away inside it to a deep field of stars and nebula. Its lips are rimmed with cold
light, and pieces of the shell, thick as real glass, drift away from the wound.

Primordial Abyss Egg, "deep time": stone laid down in real terraces, each layer its own rock. A great
ammonite is exposed on its front, ribbed, chambered, with a magenta seam of light winding in along the
coil. Time is literal here: a toothed bronze belt runs round it, and on its shoulder two big open
gears mesh together.
"""
import math

import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K

V = F.V
W = K.W
TAU = F.TAU


def lay_on(s0, v0, off=0.0):
    c, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()

    def fn(x, y, o=off):
        # the point on the egg straight behind (x, y) on the plane: the same projection Field.plane
        # paints with, so geometry laid this way lands exactly on what was painted, even far out
        base = c + e1 * x + e2 * y
        q = base
        for _ in range(8):
            ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
            vv = math.acos(max(-1, min(1, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi
            p = F.on(ss, vv)
            q = base + n * (p - c).dot(n)
        return F.on(ss, vv, o), F.normal(ss, vv)
    return fn


def frame(n):
    n = V(n).normalized()
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    return e1, e2


def ring_of(hi, c, n, r, h0, h1, sides=48, mat=0, r2=None):
    """A band round axis n at radius r from height h0 to h1 (r2: its radius at h1)."""
    e1, e2 = frame(n)
    r2 = r if r2 is None else r2
    a = [hi.v(c + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * r + V(n) * h0) for k in range(sides)]
    b = [hi.v(c + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * r2 + V(n) * h1) for k in range(sides)]
    for k in range(sides):
        q = (k + 1) % sides
        hi.f([a[k], a[q], b[q], b[k]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


def disc_steps(hi, c, n, profile, sides=48, mat=0):
    """A stack of rings through [(radius, height)]: for turned bronze."""
    e1, e2 = frame(n)
    rows = []
    for r, h in profile:
        rows.append([hi.v(c + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * r + V(n) * h) for k in range(sides)])
    for j in range(len(rows) - 1):
        for k in range(sides):
            q = (k + 1) % sides
            hi.f([rows[j][k], rows[j][q], rows[j + 1][q], rows[j + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


# ---------- Forbidden Origin Egg ----------
FO_LIGHT = "8a3cff"
FO_BANDS = (0.26, 0.5, 0.74)
FO_SEAL = (0.5, 0.5)
# an invented script: each glyph is a few strokes on a 0..1 square. Angular, no real writing.
FO_GLYPHS = (
    (((0.2, 0.1), (0.2, 0.9)), ((0.2, 0.5), (0.8, 0.9)), ((0.2, 0.5), (0.8, 0.1))),
    (((0.5, 0.05), (0.5, 0.95)), ((0.15, 0.3), (0.85, 0.7)), ((0.15, 0.7), (0.5, 0.45))),
    (((0.15, 0.85), (0.85, 0.85)), ((0.85, 0.85), (0.5, 0.1)), ((0.5, 0.1), (0.15, 0.85)), ((0.5, 0.6), (0.5, 0.4))),
    (((0.25, 0.1), (0.75, 0.1)), ((0.5, 0.1), (0.5, 0.65)), ((0.2, 0.9), (0.5, 0.65)), ((0.8, 0.9), (0.5, 0.65))),
    (((0.15, 0.2), (0.85, 0.2)), ((0.85, 0.2), (0.15, 0.8)), ((0.15, 0.8), (0.85, 0.8))),
    (((0.2, 0.15), (0.2, 0.85)), ((0.8, 0.15), (0.8, 0.85)), ((0.2, 0.5), (0.8, 0.5)), ((0.5, 0.5), (0.5, 0.95))),
    (((0.5, 0.05), (0.85, 0.5)), ((0.85, 0.5), (0.5, 0.95)), ((0.5, 0.95), (0.15, 0.5)), ((0.15, 0.5), (0.5, 0.05)), ((0.3, 0.5), (0.7, 0.5))),
    (((0.15, 0.1), (0.85, 0.9)), ((0.3, 0.75), (0.75, 0.25)), ((0.15, 0.9), (0.4, 0.9))),
)
FO_COUNT = 22       # glyphs per ring
FO_HALF = 0.034     # half a band's height, in v


def fo_glyph_mask(f, band_v):
    """Carved strokes of one ring of glyphs: a thick mask array (1 in a stroke)."""
    S, Vv = f.S, f.V
    fx = S * FO_COUNT
    cell = np.floor(fx)
    u = fx - cell
    w = (Vv - (band_v - FO_HALF)) / (2 * FO_HALF)
    inside = (w >= 0) & (w <= 1)
    out = np.zeros(S.shape)
    for g, strokes in enumerate(FO_GLYPHS):
        chosen = ((cell.astype(int) * 7 + int(band_v * 100) * 3) % len(FO_GLYPHS)) == g
        m = chosen & inside
        if not m.any():
            continue
        best = np.full(S.shape, 9.0)
        for a, b in strokes:
            d, _ = F.seg_dist(u[m], w[m], [a, b])
            best[m] = np.minimum(best[m], d)
        out = np.maximum(out, m * (1 - F.sstep(0.05, 0.085, best)))
    return out


def forbidden_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    grain = F.fbm(P, 5.0, 5, 0.55, seed=601)
    pit = F.fbm(P, 34.0, 3, seed=602)
    col = F.ramp(np.clip(0.44 + 0.55 * grain, 0, 1), [(0.0, "0b0c11"), (0.4, "171822"), (0.7, "262834"), (1.0, "3b3d4c")])
    height = 0.016 * grain + 0.004 * pit
    # bands: each ring of glyphs lies in a sunk channel with a raised edge each side
    channel = np.zeros(S.shape)
    edges = np.zeros(S.shape)
    glyph = np.zeros(S.shape)
    for b in FO_BANDS:
        d = np.abs(Vv - b)
        channel = np.maximum(channel, 1 - F.sstep(FO_HALF * 1.1, FO_HALF * 1.25, d))
        edges = np.maximum(edges, np.exp(-((d - FO_HALF * 1.45) / 0.0065) ** 2))
        glyph = np.maximum(glyph, fo_glyph_mask(f, b))
    x, y, front = f.plane(*FO_SEAL)
    near = np.hypot(x, y)
    # the seal's bed breaks into the middle ring
    keep = F.sstep(0.46, 0.52, near + (1 - np.clip(front, 0, 1)) * 3)
    glyph = glyph * keep
    # cracks start at the seal, branching outward, the light under them bleeding through
    warp = np.stack([F.fbm(P, 2.4, 3, seed=s) for s in (603, 604, 605)], -1) * 0.12
    _, edge, _ = F.voronoi(P + warp, 2.7, seed=606, jitter=1.0)
    w_ = 0.012 + 0.012 * np.clip(1 - near / 1.5, 0, 1)
    cracks = (1 - F.sstep(0.0, w_, edge)) * np.clip(1.3 - near / 1.6 - (1 - np.clip(front, 0, 1)) * 0.6, 0, 1)
    col = col * (1 - 0.26 * channel)[..., None]
    col = F.mix(col, np.array((0.22, 0.23, 0.28)), np.clip(edges, 0, 1) * 0.6)
    hot = F.mix(np.array((0.34, 0.08, 0.86)), np.array((0.72, 0.45, 1.0)), glyph)
    col = F.mix(col, hot, glyph)
    col = F.mix(col, np.array((0.5, 0.2, 1.0)), np.clip(cracks * 1.2, 0, 1))
    spill = F.blur(np.maximum(glyph, cracks), 7)
    col = col + np.array((0.1, 0.02, 0.26)) * (np.clip(spill * 1.5, 0, 1) * (1 - glyph))[..., None]
    height = height - 0.016 * channel + 0.012 * edges - 0.022 * glyph - 0.03 * np.clip(cracks, 0, 1)
    rough = np.clip(0.74 + 0.1 * grain - 0.34 * glyph, 0.1, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(S.shape), height


def fo_chain(hi, path, count, length, width, wire, mat=0, skip=None):
    """A chain along a closed or open list of points: oval wire links, each turned 90 degrees on the
    last so they really interlock."""
    n = len(path)
    dist = [0.0]
    for a, b in zip(path, path[1:]):
        dist.append(dist[-1] + (b[0] - a[0]).length)
    total = dist[-1]
    for k in range(count):
        d = total * (k + 0.5) / count
        i = next((j for j in range(n - 1) if dist[j + 1] >= d), n - 2)
        t = (d - dist[i]) / max(dist[i + 1] - dist[i], 1e-6)
        c = path[i][0].lerp(path[i + 1][0], t)
        if skip and (c - skip[0]).length < skip[1]:
            continue                # the chains end at the seal: they don't run over its face
        nn = path[i][1].lerp(path[i + 1][1], t).normalized()
        along = (path[i + 1][0] - path[i][0]).normalized()
        side = along.cross(nn).normalized()
        roll = math.pi / 2 if k % 2 else 0.0
        across = side * math.cos(roll) + nn * math.sin(roll)
        # lift the on-edge links' centre so they sit on the surface instead of cutting through it
        centre = c + nn * (wire + (width / 2 if k % 2 else 0.005))
        sides, steps = 6, 14
        rings = []
        for q in range(steps):
            a = TAU * q / steps
            # a stadium: straight sides, round ends
            ca, sa = math.cos(a), math.sin(a)
            p = along * (length / 2 - width / 2 + width / 2 * abs(ca)) * (1 if ca > 0 else -1) + across * (width / 2) * sa
            out = (along * ca + across * sa).normalized()
            tang = out.cross(along.cross(across)).normalized()
            third = along.cross(across).normalized()
            rings.append([hi.v(centre + p + (out * math.cos(TAU * r / sides) + third * math.sin(TAU * r / sides)) * wire) for r in range(sides)])
        for q in range(steps):
            nq = (q + 1) % steps
            for r in range(sides):
                nr = (r + 1) % sides
                hi.f([rings[q][r], rings[q][nr], rings[nq][nr], rings[nq][r]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


def fo_pieces(coll):
    bronze = Hm.mat_bronze("FO_Bronze")
    hi = Hm.Hi()
    # the belt chain, and the two diagonals crossing at the seal and again at the back
    belt = [(F.on(k / 80, 0.62, 0.012), F.normal(k / 80, 0.62)) for k in range(81)]
    fo_chain(hi, belt, 30, 0.255, 0.13, 0.024, skip=(F.on(*FO_SEAL), 0.5))
    for sign in (-1, 1):
        path = []
        for k in range(121):
            t = k / 120
            ss = (0.5 + sign * t) % 1.0
            vv = 0.5 + 0.34 * math.sin(TAU * t) * 1.0
            # one chain rides over the other where they cross at the back
            path.append((F.on(ss, vv, 0.012 + (0.06 if sign > 0 else 0.0) * math.exp(-((t - 0.5) / 0.05) ** 2)), F.normal(ss, vv)))
        fo_chain(hi, path, 34, 0.255, 0.13, 0.024, skip=(F.on(*FO_SEAL), 0.5))
    o = hi.object("FO_Chains", coll, [bronze], smooth=True)
    F.fix_normals(o)
    o["w"] = 1.2
    # the seal: turned bronze with a toothed wheel round it
    s = Hm.Hi()
    c, n = F.on(*FO_SEAL), F.normal(*FO_SEAL)
    disc_steps(s, c, n, [(0.45, -0.12), (0.45, 0.075), (0.41, 0.1), (0.385, 0.1), (0.37, 0.085), (0.3, 0.085), (0.285, 0.115), (0.2, 0.115), (0.18, 0.09), (0.09, 0.09), (0.0, 0.09)], sides=48)
    e1, e2 = frame(n)
    teeth = 18
    for k in range(teeth):
        a = TAU * (k + 0.5) / teeth
        r_ = e1 * math.cos(a) + e2 * math.sin(a)
        t_ = e1 * -math.sin(a) + e2 * math.cos(a)
        base = c + r_ * 0.44
        tip = c + r_ * 0.535
        quad = [base - t_ * 0.055, base + t_ * 0.055, tip + t_ * 0.03, tip - t_ * 0.03]
        lo = [s.v(p - n * 0.08) for p in quad]
        hi_ = [s.v(p + n * 0.065) for p in quad]
        for q in range(4):
            nq = (q + 1) % 4
            s.f([lo[q], lo[nq], hi_[nq], hi_[q]], [(0, 0), (1, 0), (1, 1), (0, 1)])
        s.f(hi_, [(0, 0), (1, 0), (1, 1), (0, 1)])
        s.f(lo[::-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # eight studs in the outer ring
    for k in range(8):
        a = TAU * k / 8
        F.rivet(s, c + (e1 * math.cos(a) + e2 * math.sin(a)) * 0.335 + n * 0.085, n, 0.032, rings=3, sides=8)
    seal = s.object("FO_Seal", coll, [bronze], smooth=False)
    F.fix_normals(seal)
    for p in seal.data.polygons:
        p.use_smooth = False
    seal["w"] = 2.0
    # the keyhole of light, and Neon in the strained cracks round it
    g = Hm.Hi()
    key = [(-0.05, 0.08), (0.05, 0.08), (0.07, 0.03), (0.035, -0.015), (0.06, -0.12), (-0.06, -0.12), (-0.035, -0.015), (-0.07, 0.03)]
    rim = [g.v(c + e1 * x + e2 * y + n * 0.098) for x, y in key]
    top = g.v(c + n * 0.104)
    for k in range(len(key)):
        g.f([rim[k], rim[(k + 1) % len(key)], top], [(0, 0), (1, 0), (0, 1)])
    # glyph strokes of the middle ring as Neon, the ones either side of the seal
    fn_strokes = []
    for k in range(FO_COUNT):
        ss0 = k / FO_COUNT
        if abs(((ss0 + 0.5 / FO_COUNT - FO_SEAL[0] + 0.5) % 1.0) - 0.5) * 6.3 < 0.62:
            continue
        strokes = FO_GLYPHS[(k * 7 + int(0.5 * 100) * 3) % len(FO_GLYPHS)]
        for a, b in strokes:
            pa = (ss0 + a[0] / FO_COUNT, FO_BANDS[1] - FO_HALF + a[1] * 2 * FO_HALF)
            pb = (ss0 + b[0] / FO_COUNT, FO_BANDS[1] - FO_HALF + b[1] * 2 * FO_HALF)
            pts = [(F.on((pa[0] + (pb[0] - pa[0]) * t / 3) % 1.0, pa[1] + (pb[1] - pa[1]) * t / 3, -0.012), F.normal((pa[0] + (pb[0] - pa[0]) * t / 3) % 1.0, pa[1] + (pb[1] - pa[1]) * t / 3)) for t in range(4)]
            F.prism(g, pts, 0.014, height=lambda w: w * 0.6)
    glow = F.fix_normals(g.object("FO_Light", coll, [K.glow_material(FO_LIGHT)], smooth=False, weld=0))
    return o, seal, glow


def forbidden_clay():
    coll = W.collection("ForbiddenOriginEggHi")
    shell = F.shell_mesh("FO_Shell", coll, 96, 64)
    o, seal, glow = fo_pieces(coll)
    return {x.name: F.tris(x) for x in (shell, o, seal, glow)}


def forbidden_build():
    coll = W.collection("ForbiddenOriginEggHi")
    f, col, rough, metal, height = forbidden_paint()
    mat = F.shell_material("FO_Stone", col, rough, metal)
    o, seal, glow = fo_pieces(coll)
    return F.assemble("ForbiddenOriginEgg", coll, mat, height, [o, seal], {FO_LIGHT: [glow]}, budget=9000, shell_frac=0.66, low_nu=64, low_nv=44, hard=35, ao_floor=0.55)


# ---------- Void Rift Egg ----------
VR_RIM = "3c64ff"
VR_AT = (0.5, 0.52)
# the tear: a crooked lightning fracture, not a neat lens. A centre line that zigzags, narrow nearly
# all its length, breaking wide only in its upper part, and laid diagonally across the front
_VR_CENTRE = (0.0, 0.09, -0.07, 0.13, -0.03, 0.17, 0.01, 0.15, -0.05, 0.07, -0.09, 0.03, -0.02)
_VR_WIDTH = (0.0, 0.05, 0.08, 0.19, 0.29, 0.3, 0.2, 0.11, 0.09, 0.05, 0.05, 0.025, 0.0)
_VR_YS = [1.08 - 2.16 * k / 12 for k in range(13)]
VR_LEFT = tuple((c - w - 0.025 * (k % 2), y) for k, (c, w, y) in enumerate(zip(_VR_CENTRE, _VR_WIDTH, _VR_YS)))
VR_RIGHT = tuple((c + w + 0.025 * ((k + 1) % 2), y + 0.03 * (k % 2)) for k, (c, w, y) in enumerate(zip(_VR_CENTRE, _VR_WIDTH, _VR_YS)))
VR_RIGHT = (VR_LEFT[0],) + VR_RIGHT[1:-1] + (VR_LEFT[-1],)


# the tears: the great one on the front, and a small one starting on the back, so that side has
# something happening as well
VR_TEARS = ((VR_AT, -0.62, 1.0), ((0.03, 0.62), 0.7, 0.42))


def vr_outline():
    return list(VR_LEFT) + list(VR_RIGHT[::-1])[1:-1]


def void_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    warp = np.stack([F.fbm(P, 1.4, 3, seed=s) for s in (621, 622, 623)], -1) * 0.22
    swirl = np.clip(F.fbm(P + warp, 1.6, 4, seed=624) * 1.3 + 0.5, 0, 1)
    # polished void glass: almost black, a faint blue and violet sheen moving through it
    col = F.ramp(swirl, [(0.0, "020209"), (0.5, "060716"), (0.8, "101331"), (1.0, "1d1f50")])
    height = np.zeros(S.shape)
    inside = np.zeros(S.shape, dtype=bool)
    d = np.full(S.shape, 9.0)
    x = np.zeros(S.shape)
    y = np.zeros(S.shape)
    front = np.zeros(S.shape)
    for at, roll, scale in VR_TEARS:
        xt, yt, ft = f.plane(at[0], at[1], roll=roll)
        fl = [(a * scale, b * scale) for a, b in vr_outline()]
        pts = fl + fl[:1]
        ins = np.zeros(xt.shape, dtype=bool)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            ins ^= ((ay > yt) != (by > yt)) & (xt < (bx - ax) * (yt - ay) / (by - ay + 1e-9) + ax)
        ins = ins & (ft > 0.1)
        dt, _ = F.seg_dist(xt, yt, fl, closed=True)
        dt = dt * (ft > 0.1) + 9.0 * (ft <= 0.1)
        closer = dt < d
        x, y, front = np.where(closer, xt, x), np.where(closer, yt, y), np.where(closer, ft, front)
        d = np.minimum(d, dt)
        inside = inside | ins
    depth = np.clip(d / 0.05, 0, 1) * inside
    # inside the tear: the deep, a field of stars and nebula with no surface at all
    deep = np.stack([x * 1.3, y * 1.3, np.full(x.shape, 7.0)], -1)
    neb = np.clip(F.fbm(deep, 1.8, 5, 0.55, seed=625) * 1.5 + 0.5, 0, 1)
    hue = np.clip(F.fbm(deep, 0.9, 2, seed=626) * 1.5 + 0.5, 0, 1)
    sky = F.mix(F.ramp(neb, [(0.0, "02021a"), (0.4, "0a0a4a"), (0.7, "2a1a9c"), (1.0, "6a44ff")]), F.ramp(neb, [(0.0, "04021a"), (0.4, "1a0a4a"), (0.7, "6a1a9c"), (1.0, "e05aff")]), hue)
    f1, _, cid = F.voronoi(deep, 15.0, seed=627)
    sky = F.mix(sky, np.array((0.9, 0.93, 1.0)), (1 - F.sstep(0.03, 0.08, f1)) * (cid > 0.5))
    f2, _, cid2 = F.voronoi(deep, 6.0, seed=628)
    sky = F.mix(sky, np.array((1.0, 1.0, 0.95)), (1 - F.sstep(0.02, 0.07, f2)) * (cid2 > 0.68))
    col = F.mix(col, sky * 1.25, F.sstep(0.0, 0.2, depth))
    # the shell's broken thickness: a lit band just inside the lip
    lip = np.exp(-(d / 0.018) ** 2) * inside
    col = F.mix(col, np.array((0.32, 0.42, 1.0)), lip)
    # cracks running out from the wound through the glass
    _, edge, _ = F.voronoi(P + warp * 0.5, 3.2, seed=629, jitter=1.0)
    crack = (1 - F.sstep(0.0, 0.016, edge)) * np.clip(1.0 - np.where(inside, 0, d) / 0.95, 0, 1) * (1 - inside) * (front > 0.1)
    col = F.mix(col, np.array((0.3, 0.4, 1.0)), crack * 0.85)
    glow = np.clip(F.blur((inside * 1.0), 26) * 1.5, 0, 1) * (1 - inside)
    col = col + np.array((0.04, 0.07, 0.32)) * glow[..., None]
    # the height: sinks hard inside, the lips pushed out as the glass tore
    outer_lip = np.exp(-(d / 0.09) ** 2) * (1 - inside)
    height = -0.34 * F.sstep(0.0, 0.5, depth) + 0.05 * outer_lip * (0.6 + 0.5 * np.clip(F.fbm(P, 9.0, 2, seed=630) + 0.5, 0, 1)) - 0.008 * crack
    rough = np.clip(0.06 + 0.5 * inside + 0.1 * crack, 0, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(S.shape), height


def vr_shard(hi, c, n, size, seed, mat=0):
    """A flake of the shell: an irregular plate with real thickness, curved a little, its broken edge
    showing."""
    rnd = np.random.default_rng(seed)
    e1, e2 = frame(n)
    # random twist on the drift
    tilt = (n + e1 * rnd.uniform(-0.5, 0.5) + e2 * rnd.uniform(-0.5, 0.5)).normalized()
    e1, e2 = frame(tilt)
    count = int(rnd.integers(5, 8))
    outline = []
    for k in range(count):
        a = TAU * k / count + rnd.uniform(-0.3, 0.3)
        r = size * rnd.uniform(0.55, 1.15)
        outline.append(e1 * math.cos(a) * r + e2 * math.sin(a) * r * 0.72)
    th = size * 0.2
    top = [hi.v(c + p + tilt * (th / 2 - p.length ** 2 * 0.3)) for p in outline]
    bot = [hi.v(c + p - tilt * (th / 2 + p.length ** 2 * 0.3)) for p in outline]
    ct = hi.v(c + tilt * th * 0.5)
    cb = hi.v(c - tilt * th * 0.5)
    for k in range(count):
        q = (k + 1) % count
        hi.f([top[k], top[q], ct], [(0, 0), (1, 0), (0, 1)], mat)
        hi.f([bot[q], bot[k], cb], [(0, 0), (1, 0), (0, 1)], mat)
        hi.f([top[q], top[k], bot[k], bot[q]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


def vr_pieces(coll):
    glass = Hm.mat_voidglass("VR_Glass")
    hi = Hm.Hi()
    fn = lay_on(*VR_AT)
    # drifting off the wound's right and left, biggest near it, farther and smaller on the way out
    flakes = ((0.42, 0.42, 0.17, 0.42), (0.52, 0.12, 0.22, 0.32), (0.62, -0.22, 0.15, 0.56), (0.36, -0.46, 0.18, 0.5), (0.3, 0.72, 0.13, 0.62), (0.72, 0.5, 0.11, 0.78),
              (0.82, -0.02, 0.12, 0.94), (0.86, -0.42, 0.08, 1.06), (-0.5, 0.28, 0.2, 0.44), (-0.58, -0.08, 0.13, 0.6), (-0.44, -0.44, 0.16, 0.54), (-0.32, 0.72, 0.11, 0.74), (-0.76, 0.42, 0.09, 0.94), (-0.8, -0.34, 0.08, 1.04))
    cr, sr = math.cos(-0.62), math.sin(-0.62)
    for k, (x, y, size, lift) in enumerate(flakes):
        p, n = fn(x * cr - y * sr, x * sr + y * cr, lift)
        vr_shard(hi, p, n, size, 640 + k)
    back = lay_on(0.03, 0.62)
    for k, (x, y, size, lift) in enumerate(((0.2, 0.18, 0.1, 0.32), (-0.24, -0.08, 0.12, 0.3), (0.34, -0.2, 0.07, 0.5), (-0.1, 0.36, 0.08, 0.56))):
        p, n = back(x, y, lift)
        vr_shard(hi, p, n, size, 660 + k)
    o = hi.object("VR_Flakes", coll, [glass], smooth=False)
    F.fix_normals(o)
    o["w"] = 3.0
    # the cold light along the two lips, in broken lengths
    g = Hm.Hi()
    for at, roll, scale in VR_TEARS:
        lay = lay_on(at[0], at[1])
        cr, sr = math.cos(roll), math.sin(roll)
        for lip in (VR_LEFT, VR_RIGHT):
            fine = []
            for (ax, ay), (bx, by) in zip(lip, lip[1:]):
                for t in range(5):
                    fine.append((ax + (bx - ax) * t / 5, ay + (by - ay) * t / 5))
            fine.append(lip[-1])
            # the same rotation the painted plane has: f.plane's roll turns its axes by +roll
            pts = []
            for x, y in fine:
                X, Y = x * scale, y * scale
                pts.append(lay(X * cr - Y * sr, X * sr + Y * cr, 0.024))
            F.prism(g, pts, lambda t: (0.02 * scale ** 0.5) * math.sin(math.pi * t) ** 0.4 + 0.003, height=lambda w: w * 0.35)
    rim = F.fix_normals(g.object("VR_Rim", coll, [K.glow_material(VR_RIM)], smooth=False, weld=0))
    return o, rim


def void_clay():
    coll = W.collection("VoidRiftEggHi")
    f, col, rough, metal, height = void_paint()
    shell = F.shell_mesh("VR_Shell", coll, 256, 160, height)
    o, rim = vr_pieces(coll)
    return {x.name: F.tris(x) for x in (shell, o, rim)}


def void_build():
    coll = W.collection("VoidRiftEggHi")
    f, col, rough, metal, height = void_paint()
    mat = F.shell_material("VR_Skin", col, rough, metal)
    o, rim = vr_pieces(coll)
    return F.assemble("VoidRiftEgg", coll, mat, height, [o], {VR_RIM: [rim]}, budget=1800, shell_frac=0.84, low_nu=96, low_nv=62, hard=25, shell_ext=0.3, shell_ray=0.65, ao_floor=0.9)


# ---------- Primordial Abyss Egg ----------
PA_SEAM = "ff3cb4"
PA_AT = (0.5, 0.5)
PA_TURNS = 2.6


def pa_spiral_r(a):
    """The ammonite's coil: a logarithmic spiral, a is the angle wound from the centre, returns its
    radius (0.56 at the outer edge)."""
    return 0.56 * math.exp((a - PA_TURNS * TAU) / (PA_TURNS * TAU) * 2.9)


def primordial_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    warp = F.fbm(P, 1.2, 3, seed=661) * 0.1 + F.fbm(P, 5.0, 2, seed=662) * 0.012
    # the strata: real terraces, each layer its own thickness and rock
    edges = np.array([0.0, 0.07, 0.11, 0.2, 0.24, 0.31, 0.37, 0.41, 0.5, 0.54, 0.6, 0.66, 0.7, 0.8, 0.84, 0.91, 1.01])
    yy = np.clip(Vv + warp, 0, 1)
    idx = np.clip(np.searchsorted(edges, yy) - 1, 0, len(edges) - 2)
    t = (yy - edges[idx]) / (edges[idx + 1] - edges[idx])
    tops = np.array((0.028, 0.0, 0.045, 0.012, 0.038, 0.004, 0.022, 0.05, 0.016, 0.034, 0.008, 0.042, 0.018, 0.03, 0.006, 0.024))
    grain = F.fbm(P * np.array((1.0, 2.6, 1.0)), 6.0, 4, seed=663)
    fine = F.fbm(P, 30.0, 3, seed=664)
    # each layer's face slopes, overhangs a little and is lipped at its top: terraces, not stripes
    face = np.clip(t * 1.1, 0, 1)
    height = tops[idx] + 0.03 * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.5 - 0.024 * (1 - F.sstep(0.0, 0.08, t)) + 0.01 * grain + 0.003 * fine
    # dark shale, ochre, rust, pale limestone, slate, a thin red iron bed: rocks you would see in a cliff
    palette = (("1f1a18", "3c302a"), ("9c7848", "c9a56c"), ("33241d", "573e30"), ("15141a", "2f2d36"), ("7d3f22", "b5622f"), ("bfae8e", "ded0ae"), ("23212a", "434050"), ("8a2e1c", "b8482a"),
               ("6f5a44", "9a8366"), ("16151a", "2c2a32"), ("a67c44", "d3a762"), ("2e2622", "4e4038"), ("c7b794", "e6d8b4"), ("331f1a", "5a3a2c"), ("1a1b22", "36384a"), ("6e4d33", "9c7350"))
    col = np.zeros(S.shape + (3,))
    tone = np.clip(0.5 + grain * 0.8, 0, 1)
    for k, (lo, hi_) in enumerate(palette):
        m = idx == k
        col[m] = F.mix(F.rgb(lo), F.rgb(hi_), tone[m])
    gap = 1 - F.sstep(0.0, 0.05, t)
    col = col * (1 - 0.72 * gap)[..., None]
    # fine sediment lines within each bed, and the joints that crack rock upright
    laminae = 0.5 + 0.5 * np.sin((yy * 300.0 + grain * 7.0))
    col = col * (0.84 + 0.26 * laminae)[..., None]
    height = height + 0.0025 * laminae
    _, jedge, _ = F.voronoi(P + np.stack([grain * 0.1, grain * 0.0, grain * 0.1], -1), 3.0, seed=665, jitter=1.0, stretch=(1.0, 0.45, 1.0))
    joint = 1 - F.sstep(0.0, 0.03, jedge)
    col = col * (1 - 0.68 * joint)[..., None]
    height = height - 0.016 * joint
    # the ammonite, exposed on the front: a flat-cleaned face with the coil in relief
    x, y, front = f.plane(*PA_AT)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    cleared = (1 - F.sstep(0.58, 0.64, r)) * (front > 0.2)
    k = 2.9 / (PA_TURNS * TAU)
    # how far along the coil: which whorl is this point in, and where within it
    w = (np.log(np.maximum(r, 1e-3) / 0.56) / k) / TAU        # 0 at the rim, negative going in
    u = (w - ang / TAU) % 1.0                                  # 0..1 across a whorl
    along = ang + (np.floor(w - ang / TAU) * TAU)
    # the shell's ribs: many, curved, running across each whorl
    ribs = 0.5 + 0.5 * np.cos(ang * 26.0 + np.log(np.maximum(r, 1e-3)) * 42.0)
    rounded = np.sin(np.pi * u) ** 0.55            # each whorl a rounded tube
    groove = 1 - F.sstep(0.0, 0.06, np.minimum(u, 1 - u))
    shell_h = 0.07 * rounded + 0.012 * ribs * rounded
    centre = 1 - F.sstep(0.015, 0.05, r)
    fossil = F.ramp(np.clip(0.34 + 0.48 * rounded + 0.16 * (ribs - 0.5) + fine * 0.2, 0, 1), [(0.0, "2e2015"), (0.35, "6c4f33"), (0.7, "b08d62"), (1.0, "e0c79c")])
    fossil = F.mix(fossil, np.array((0.04, 0.02, 0.02)), groove * 0.8)
    # the seam of light down the grooves
    seam = (1 - F.sstep(0.0, 0.03, np.minimum(u, 1 - u))) * (r > 0.03)
    fossil = F.mix(fossil, F.rgb("ff4ac0"), seam)
    col = F.mix(col, fossil, cleared)
    spill = F.blur(seam * cleared, 5)
    col = col + np.array((0.28, 0.02, 0.18)) * (np.clip(spill * 1.5, 0, 1) * (1 - seam))[..., None]
    height = height * (1 - cleared) + cleared * (shell_h - 0.012 - 0.03 * groove) + 0.02 * np.exp(-((r - 0.61) / 0.03) ** 2) * (front > 0.2)
    rough = np.clip(0.82 + 0.1 * grain - 0.25 * cleared - 0.3 * seam, 0.1, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(S.shape), height


def gear(hi, c, n, R, teeth, thick, up=None, mat=0, spokes=5):
    """An open cut gear: toothed rim, hub, spokes, axis pin. Sharp-edged and true: flanks tapered, rim
    a real width."""
    e1, e2 = frame(n)
    n = V(n).normalized()
    r_root = R * 0.88
    r_in = R * 0.7
    pts = []
    for k in range(teeth):
        a0 = TAU * k / teeth
        pitch = TAU / teeth
        for da, rr in ((0.02, r_root), (0.17, r_root), (0.3, R), (0.6, R), (0.73, r_root), (0.98, r_root)):
            a = a0 + pitch * da
            pts.append(e1 * math.cos(a) * rr + e2 * math.sin(a) * rr)
    N = len(pts)
    inner = [e1 * math.cos(TAU * k / N) * r_in + e2 * math.sin(TAU * k / N) * r_in for k in range(N)]
    f_o = [hi.v(c + p + n * thick / 2) for p in pts]
    f_i = [hi.v(c + p + n * thick / 2) for p in inner]
    b_o = [hi.v(c + p - n * thick / 2) for p in pts]
    b_i = [hi.v(c + p - n * thick / 2) for p in inner]
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for k in range(N):
        q = (k + 1) % N
        hi.f([f_i[k], f_o[k], f_o[q], f_i[q]], uv, mat)
        hi.f([b_o[k], b_i[k], b_i[q], b_o[q]], uv, mat)
        hi.f([f_o[k], b_o[k], b_o[q], f_o[q]], uv, mat)
        hi.f([b_i[k], f_i[k], f_i[q], b_i[q]], uv, mat)
    # the spokes and hub
    hub = R * 0.22
    disc_steps(hi, c, n, [(hub, -thick * 0.7), (hub, thick * 0.7), (hub * 0.72, thick * 0.9), (0.0, thick * 0.9)], sides=20, mat=mat)
    for k in range(spokes):
        a = TAU * k / spokes + 0.2
        d = e1 * math.cos(a) + e2 * math.sin(a)
        path = [(c + d * (hub * 0.8 + (r_in * 1.02 - hub * 0.8) * t / 3) - n * thick * 0.2, n) for t in range(4)]
        F.bar(hi, path, lambda t: R * 0.13 * (1 - 0.25 * t), thick * 0.55, mat=mat, foot=0.0)


def pa_pieces(coll):
    bronze = Hm.mat_bronze("PA_Bronze")
    hi = Hm.Hi()
    # the clockwork belt, cut round the egg below the ammonite's foot: two rails and teeth between
    v0 = 0.27
    F.bar(hi, F.along_shell((0, v0 + 0.03), (1, v0 + 0.03), 0.02, steps=64)[:-1], 0.04, 0.05, closed=True)
    F.bar(hi, F.along_shell((0, v0 - 0.03), (1, v0 - 0.03), 0.02, steps=64)[:-1], 0.04, 0.05, closed=True)
    teeth = 36
    for k in range(teeth):
        ss = k / teeth
        F.bar(hi, F.along_shell((ss, v0 - 0.024), (ss, v0 + 0.024), 0.03, steps=3), 0.038, 0.05, foot=0.0)
    # the two gears on the right shoulder, meshed: their rims overlap by the teeth's depth
    s1, v1 = 0.78, 0.74
    c1, n1 = F.on(s1, v1, 0.13), F.normal(s1, v1)
    R1, T1 = 0.46, 16
    gear(hi, c1, n1, R1, T1, 0.075)
    e1, e2 = frame(n1)
    R2, T2 = 0.29, 10
    d = (e1 * math.cos(-0.5) + e2 * math.sin(-0.5))
    c2 = c1 + d * (R1 * 0.94 + R2 * 0.9) + n1 * -0.05
    gear(hi, c2, n1, R2, T2, 0.075)
    # axles and a post down into the shell, so they are carried by something
    Hm.htube(hi, [c1 - n1 * 0.2, c1], lambda t: 0.06, sides=10, per=2, wobble=0, tip=False)
    Hm.htube(hi, [c2 - n1 * 0.22, c2], lambda t: 0.045, sides=10, per=2, wobble=0, tip=False)
    # a small third gear on the back, so it is not forgotten there
    s3, v3 = 0.12, 0.6
    c3, n3 = F.on(s3, v3, 0.1), F.normal(s3, v3)
    gear(hi, c3, n3, 0.3, 12, 0.07)
    Hm.htube(hi, [c3 - n3 * 0.2, c3], lambda t: 0.05, sides=10, per=2, wobble=0, tip=False)
    o = hi.object("PA_Works", coll, [bronze], smooth=False)
    F.fix_normals(o)
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.0
    # the seam of light winding in along the coil
    g = Hm.Hi()
    fn = lay_on(*PA_AT)
    pts = []
    steps = 170
    for i in range(steps + 1):
        a = PA_TURNS * TAU * (i / steps) + 0.25
        r = pa_spiral_r(a)
        # the spiral's angle in the plane runs with a
        x, y = math.cos(a) * r, math.sin(a) * r
        pts.append(fn(x, y, 0.012))
    F.prism(g, pts, lambda t: 0.016 + 0.032 * t, height=lambda w: w * 0.45)
    seam = F.fix_normals(g.object("PA_Seam", coll, [K.glow_material(PA_SEAM)], smooth=False, weld=0))
    return o, seam


def primordial_clay():
    coll = W.collection("PrimordialAbyssEggHi")
    f, col, rough, metal, height = primordial_paint()
    shell = F.shell_mesh("PA_Shell", coll, 256, 160, height)
    o, seam = pa_pieces(coll)
    return {x.name: F.tris(x) for x in (shell, o, seam)}


def primordial_build():
    coll = W.collection("PrimordialAbyssEggHi")
    f, col, rough, metal, height = primordial_paint()
    mat = F.shell_material("PA_Rock", col, rough, metal)
    o, seam = pa_pieces(coll)
    return F.assemble("PrimordialAbyssEgg", coll, mat, height, [o], {PA_SEAM: [seam]}, budget=7000, shell_frac=0.68, low_nu=72, low_nv=52, hard=30, ao_floor=0.55)

"""Yggdrasil's eggs, second generation (see egg_forge.py).

Beginner Qi Egg, "the first cut": a jeweller's cut laid over an egg. It has the three parts of a
real cut gem: a pavilion below, a crown above, and a knife-edged girdle between them, which is its
one strong line. Eight flutes spiral up the crown and down the pavilion in opposite directions, so
they meet at the girdle in chevrons, and Qi light sits down in the cuts: a ring in the groove of
the girdle and threads running in the valleys of the flutes. Nothing random: the identity is the
cut. The colour is faked refraction: each facet looks into the stone at its own angle and sees its
own slice of the light at the heart, so neighbouring facets disagree the way real gems do.

Spirit Breeze Egg, "the wind peels off the glaze": a wind-glazed porcelain. Cobalt deepening to the
base under a real crackle glaze, with hand-brushed ribbons of white slip standing proud of it. The
main ribbon crosses the front, and at the shoulder it stops being paint: it lifts off the egg as a
real blade of porcelain and curls in the air, and so do two smaller ones. A gold crescent on the
other shoulder cradles a breeze sigil on a dark roundel. It sits in a bed of carved ruyi clouds, each
lobe scrolled in gold.

Elemental Core Egg, "the reliquary": a fractured stone a goldsmith has been asked to hold shut. Dark
basalt plates split along real fractures with Qi bleeding out of them, brightest round the core. Over
it a forged angular cage: straight bars with chamfered shoulders, a belt of double rails, zigzag
lancets above and below, joints pinned by rivets, standing on four claws. Set in the front, in a hex
bezel with six prongs, a large cut crystal; round the belt, five cut stones, one per element.
"""
import math

import bmesh
import bpy
import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K

V = F.V
W = K.W


# ---------- Beginner Qi Egg ----------
BQ_RINGS = (0.06, 0.135, 0.225, 0.315, 0.395, 0.45, 0.535, 0.625, 0.715, 0.8, 0.875, 0.94)
BQ_GIRDLE = (4, 5)     # the two rings that make the girdle's band
BQ_N = 16
BQ_QI = "3fc6ff"


def bq_twist(v):
    lo, hi = BQ_RINGS[BQ_GIRDLE[0]], BQ_RINGS[BQ_GIRDLE[1]]
    if v <= lo:
        return -0.2 * (lo - v) / lo
    if v >= hi:
        return 0.24 * (v - hi) / (1 - hi)
    return 0.0


def bq_vertex(j, i, lift=0.0):
    v = BQ_RINGS[j]
    s = 0.5 + i / BQ_N + bq_twist(v)
    if j in BQ_GIRDLE:
        off = 0.05
    else:
        # the flutes: ridges and valleys in turn, deepest at the belly, gone by the poles
        fade = math.sin(math.pi * min(1.0, abs(v - 0.0) / 1.0)) ** 0.8
        off = (0.075 if i % 2 == 0 else -0.05) * fade
    return F.on(s % 1.0, v, off + lift)


def bq_mesh(name, coll, material=None):
    rings = len(BQ_RINGS)
    verts = [W.rb(*bq_vertex(j, i)) for j in range(rings) for i in range(BQ_N)]
    idx = lambda j, i: j * BQ_N + i % BQ_N
    faces = []
    for j in range(rings - 1):
        for i in range(BQ_N):
            a, b, c, d = idx(j, i), idx(j, i + 1), idx(j + 1, i + 1), idx(j + 1, i)
            # the diagonal runs from ridge to ridge, so each flute reads as long kites
            if (i + j) % 2 == 0:
                faces += [[a, b, c], [a, c, d]]
            else:
                faces += [[a, b, d], [b, c, d]]
    bottom = len(verts)
    verts.append(W.rb(0, 0.0, 0))
    top = len(verts)
    verts.append(W.rb(0, F.H + 0.03, 0))
    for i in range(BQ_N):
        faces.append([bottom, idx(0, i + 1), idx(0, i)])
        faces.append([top, idx(rings - 1, i), idx(rings - 1, i + 1)])
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if material:
        me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def bq_threads(coll):
    """Qi in the cuts: a ring round the girdle's groove, and a thread down every other valley,
    fading out toward the poles."""
    hi = Hm.Hi()
    lo, up = BQ_RINGS[BQ_GIRDLE[0]], BQ_RINGS[BQ_GIRDLE[1]]
    girdle = []
    for k in range(BQ_N * 4):
        s = k / (BQ_N * 4)
        girdle.append((F.on(s, (lo + up) / 2, 0.052), F.normal(s, (lo + up) / 2)))
    F.prism(hi, girdle, 0.032, height=lambda w: w * 0.28, closed=True)
    for i in range(1, BQ_N, 4):
        for rows in ((6, 7, 8, 9, 10), (3, 2, 1)):
            path = []
            for j in rows:
                path.append(bq_vertex(j, i if j not in BQ_GIRDLE else i, 0.004))
            pts = []
            for a, b in zip(path, path[1:]):
                for t in range(6):
                    q = a.lerp(b, t / 6)
                    pts.append((q, V((q.x, 0.2 * (q.y - 1.3), q.z)).normalized()))
            pts.append((path[-1], V((path[-1].x, 0.2 * (path[-1].y - 1.3), path[-1].z)).normalized()))
            F.prism(hi, pts, lambda t: 0.028 * (1 - t) ** 0.7, height=lambda w: w * 0.35)
    g = K.glow_material(BQ_QI)
    return hi.object("BQ_Threads", coll, [g], smooth=False, weld=0)


def bq_material():
    g = Hm._Graph("BQ_Crystal")
    geo = g.n("ShaderNodeNewGeometry")
    pos, tn = geo.outputs["Position"], geo.outputs["True Normal"]

    def vm(op, a, b=None, val=None):
        nd = g.n("ShaderNodeVectorMath", operation=op)
        for sock, x in ((nd.inputs[0], a), (nd.inputs[1], b)):
            if x is None:
                continue
            if isinstance(x, tuple):
                sock.default_value = x
            else:
                g.link(x, sock)
        if val is not None:
            next(s for s in nd.inputs if s.enabled and s.type == "VALUE").default_value = val
        return nd.outputs[0], nd.outputs[1]

    # looking in along the radial direction, tilted a little down: each facet bends it its own way
    radial = vm("MULTIPLY", pos, (1.0, 1.0, 0.25))[0]
    incoming = vm("NORMALIZE", vm("SUBTRACT", (0.0, 0.0, 0.35), radial)[0])[0]
    bent = vm("REFRACT", incoming, tn, val=1 / 1.75)[0]
    inside = vm("ADD", pos, vm("SCALE", bent, val=0.72)[0])[0]
    # the heart: light at the middle of the stone, falling off to deep cobalt
    d = vm("LENGTH", vm("MULTIPLY", vm("SUBTRACT", inside, (0.0, 0.0, 1.12))[0], (1.0, 1.0, 0.62))[0])[1]
    col = g.ramp(d, [(0.0, (0.5, 0.95, 1.0)), (0.1, (0.05, 0.62, 1.0)), (0.26, (0.006, 0.26, 0.98)),
                     (0.5, (0.002, 0.075, 0.6)), (0.9, (0.0008, 0.018, 0.2))])
    # internal planes: sharp-edged panes the facets see through
    panes = g.n("ShaderNodeTexVoronoi", **{"Scale": 3.4})
    g.link(inside, panes.inputs["Vector"])
    pane = g.ramp(g.bw(panes.outputs["Color"]), [(0.0, (0.28, 0.3, 0.42)), (0.4, (0.7, 0.72, 0.85)), (0.7, (1.3, 1.4, 1.5)), (1.0, (2.4, 2.6, 2.8))], "CONSTANT")
    nd = g.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    nd.inputs["Factor"].default_value = 0.8
    g.link(col, nd.inputs[6])
    g.link(pane, nd.inputs[7])
    col = nd.outputs[2]
    # every facet its own tone
    tone = g.n("ShaderNodeTexNoise", **{"Scale": 31.0, "Detail": 0.0})
    g.link(tn, tone.inputs["Vector"])
    shade = g.ramp(tone.outputs["Fac"], [(0.32, (0.22, 0.26, 0.42)), (0.5, (0.7, 0.75, 0.9)), (0.68, (1.45, 1.5, 1.55))])
    nd = g.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    nd.inputs["Factor"].default_value = 1.0
    g.link(col, nd.inputs[6])
    g.link(shade, nd.inputs[7])
    col = nd.outputs[2]
    # paler toward the crown, deeper toward the base
    z = g.sep(pos)[2]
    col = g.mix(g.math("MULTIPLY", g.math("DIVIDE", g.math("SUBTRACT", z, 1.9, clamp=True), 1.0), 0.35), col, (0.25, 0.7, 1.0))
    # the cut edges catch light
    point = g.ramp(geo.outputs["Pointiness"], [(0.5, (0, 0, 0)), (0.56, (1, 1, 1))])
    col = g.mix(g.math("MULTIPLY", g.bw(point), 0.75), col, (0.85, 0.97, 1.0))
    return g.finish(col, 0.1, 0.0)


def beginner_clay():
    coll = W.collection("BeginnerQiEggHi")
    low = bq_mesh("BQ_clay", coll)
    for p in low.data.polygons:
        p.use_smooth = False
    threads = bq_threads(coll)
    return low, threads


def beginner_build():
    """The whole egg: maps, FBX and a review sheet. Leaves it in the scene to look at."""
    coll = W.collection("BeginnerQiEggHi")
    mat = bq_material()
    hi = bq_mesh("BQ_Hi", coll, mat)
    Hm.apply_modifiers(hi, [("BEVEL", {"width": 0.016, "segments": 3, "limit_method": "ANGLE", "angle_limit": math.radians(4), "harden_normals": False})])
    for p in hi.data.polygons:
        p.use_smooth = False
    low = bq_mesh("BQ_Low", coll)
    for p in low.data.polygons:
        p.use_smooth = False
    F.unwrap_into(low, (0, 0, 1, 1), angle=20, margin=0.006)
    threads = bq_threads(coll)
    mat2, log = F.bake("BeginnerQiEgg", [(low, [hi], 0.05, 0.12)], [threads], samples=24)
    parts, total = F.export("BeginnerQiEgg", [low], {BQ_QI: [threads]}, coll, flat_body=True)
    return parts, total, log, hi


# ---------- Spirit Breeze Egg ----------
SB_SIGIL = "19b8ff"
# the ribbons: (start s, span, start v, rise, widest, phase); the last value says whether its end
# leaves the egg
SB_RIBBONS = (
    (0.06, 0.8, 0.2, 0.56, 0.058, 0.0, True),
    (0.2, 0.74, 0.09, 0.3, 0.03, 1.4, True),
    (0.72, 0.56, 0.5, 0.36, 0.04, 2.6, True),
    (0.12, 0.42, 0.44, 0.16, 0.012, 0.6, False),
    (0.5, 0.32, 0.14, 0.12, 0.01, 2.0, False),
)


# painted scrolls: (s, v, size, direction, line width)
SB_SCROLLS = ((0.62, 0.28, 0.13, 1, 0.012), (0.44, 0.2, 0.1, -1, 0.011), (0.78, 0.6, 0.11, -1, 0.011), (0.06, 0.32, 0.14, 1, 0.012),
              (0.2, 0.28, 0.12, -1, 0.011), (0.93, 0.28, 0.1, 1, 0.01), (0.6, 0.86, 0.075, 1, 0.009))
SB_SEAL = (0.385, 0.665)


def sb_centre(r, x):
    s0, span, v0, rise, wid, ph, _ = r
    return v0 + rise * (x ** 1.2) + 0.022 * np.sin(x * 5.0 + ph)


def sb_width(r, x):
    return r[4] * np.clip(np.sin(np.pi * np.clip(x, 0, 1) ** 0.75), 0, 1) ** 0.8


def spirit_breeze_paint():
    f = F.Field()
    S, Vv, P = f.S, f.V, f.P
    # the glaze: cobalt pooled at the base, thinning to pale at the crown, gently clouded
    cloud = F.fbm(P, 1.3, 3, seed=5)
    col = F.ramp(np.clip(Vv + cloud * 0.05, 0, 1), [(0.03, "173f92"), (0.2, "2467c2"), (0.45, "4a97df"), (0.72, "8ccbf0"), (0.97, "d0ecf8")])
    # the crackle: a coarse net and a fine one inside it, the glaze's lines stained darker
    _, edge1, _ = F.voronoi(P, 7.5, seed=11, jitter=1.0, stretch=(1.0, 0.72, 1.0))
    _, edge2, _ = F.voronoi(P, 19.0, seed=12, jitter=1.0)
    crack1 = 1 - F.sstep(0.0, 0.028, edge1)
    crack2 = (1 - F.sstep(0.0, 0.05, edge2)) * 0.35
    crack = np.maximum(crack1, crack2)
    col = F.mix(col, col * np.array((0.6, 0.7, 0.82)), crack * 0.6)
    height = -0.0015 * crack
    # the slip: ribbons of white, brushed, their edges breaking up into dry-brush streaks
    slip = np.zeros(S.shape)
    for r in SB_RIBBONS:
        x = ((S - r[0]) % 1.0) / r[1]
        inside = x <= 1.0
        dv = Vv - sb_centre(r, np.clip(x, 0, 1))
        # streaks running along the stroke, in stroke coordinates
        q = np.stack([x * 2.6 + r[5], dv * 42.0, np.full(x.shape, r[5])], -1)
        streak = F.fbm(q, 1.0, 3, seed=21)
        w = sb_width(r, x) * (1.0 + 0.32 * streak)
        m = 1 - F.sstep(w * 0.72, w, np.abs(dv))
        slip = np.maximum(slip, m * inside)
    # the brush's hairs: pale cobalt lines running along each ribbon, and a gold line on its upper edge
    hairs = np.zeros(S.shape)
    trim = np.zeros(S.shape)
    for r in SB_RIBBONS:
        x = ((S - r[0]) % 1.0) / r[1]
        inside = x <= 1.0
        dv = Vv - sb_centre(r, np.clip(x, 0, 1))
        w = np.maximum(sb_width(r, x), 1e-4)
        q = np.stack([x * 1.3 + r[5], dv / w * 3.4, np.full(x.shape, r[5] * 2)], -1)
        hairs = np.maximum(hairs, (F.sstep(0.06, 0.4, F.fbm(q, 1.0, 3, seed=23)) * inside * (np.abs(dv) < w)))
        if r[4] > 0.02:
            trim = np.maximum(trim, (1 - F.sstep(0.0035, 0.0065, np.abs(dv - w * 0.92))) * inside * F.sstep(0.03, 0.12, x) * (1 - F.sstep(0.9, 1.0, x)))
    white = F.mix(np.array((0.97, 0.98, 0.99)), np.array((0.52, 0.72, 0.93)), hairs * 0.85)
    # a shadow of pooled cobalt beside the slip, as glaze gathers against a raised stroke
    pool = np.clip(F.blur(slip, 7) - slip, 0, 1)
    col = F.mix(col, col * np.array((0.55, 0.65, 0.82)), np.clip(pool * 2.0, 0, 1))
    col = F.mix(col, white, slip)
    col = F.mix(col, np.array((0.96, 0.75, 0.32)), trim)
    height = height * (1 - slip * 0.7) + 0.012 * F.blur(slip, 1.5)
    # painted scrolls of wind in the open glaze, one line each, thinning as they wind in
    scrolls = np.zeros(S.shape)
    for s0, v0, size, turn, tw in SB_SCROLLS:
        x, y, front = f.plane(s0, v0)
        pts = []
        for i in range(70):
            t = i / 69
            a = turn * (t * F.TAU * 1.8)
            rr = size * (1 - 0.86 * t)
            pts.append((math.cos(a) * rr, math.sin(a) * rr))
        tail = [(pts[0][0] + size * 1.5 * (1 - i / 12), pts[0][1] - size * 0.7 * (1 - i / 12) ** 2) for i in range(12)]
        d, along = F.seg_dist(x, y, tail + pts)
        scrolls = np.maximum(scrolls, (1 - F.sstep(0.0, 1.0, d / (tw * (1.05 - 0.75 * along)))) * (front > 0.2))
    scrolls = scrolls * (1 - slip)
    col = F.mix(col, np.array((0.95, 0.97, 0.99)), scrolls * 0.92)
    height = height + 0.005 * F.blur(scrolls, 1)
    slip = np.maximum(slip, scrolls)
    # the sigil's dark roundel, ringed, on the left shoulder
    x, y, front = f.plane(*SB_SEAL)
    d = np.hypot(x, y)
    disc = (1 - F.sstep(0.27, 0.285, d)) * (front > 0)
    col = F.mix(col, F.ramp(np.clip(d / 0.28, 0, 1), [(0.0, "0a2a6e"), (0.7, "0e3a8a"), (1.0, "082060")]), disc)
    height = height * (1 - disc) - 0.008 * disc
    slip = slip * (1 - disc)
    # gold leaf: flecks drifting up off the crescent
    f1, _, cid = F.voronoi(P, 17.0, seed=41)
    near = np.exp(-(((x + 0.1) / 0.9) ** 2 + ((y - 0.2) / 0.8) ** 2)) * (front > 0)
    leaf = (1 - F.sstep(0.05, 0.09, f1)) * (cid > 1 - near * 0.5) * (1 - disc)
    col = F.mix(col, np.array((0.93, 0.74, 0.34)), leaf)
    rough = np.full(S.shape, 0.16) + 0.2 * slip + 0.1 * crack + 0.15 * leaf + 0.15 * trim
    metal = np.maximum(0.75 * leaf, 0.75 * trim)
    return f, col, rough, metal, height


def sb_ribbon_path(r, length, lift_from=0.7):
    """The ribbon's centre line on the shell, then leaving it as a scroll: a curve that winds
    tighter as it goes (a clothoid), like the curl on a breaking wave."""
    s0, span = r[0], r[1]
    path = []
    steps = 16
    for i in range(steps + 1):
        x = lift_from + (1 - lift_from) * i / steps
        vv = float(sb_centre(r, np.float64(x)))
        ss = (s0 + span * x) % 1.0
        path.append((F.on(ss, vv, 0.008 + 0.03 * (i / steps) ** 2), F.normal(ss, vv)))
    p, n = path[-1]
    T = (p - path[-3][0]).normalized()
    N = (n - T * n.dot(T)).normalized()
    phi, turn = 0.0, 0.0
    count = 44
    ds = length / count
    for i in range(count):
        t = i / (count - 1)
        turn = (0.7 + 9.5 * t ** 1.7) / max(length, 0.01) * 0.75
        phi += turn * ds
        p = p + (T * math.cos(phi) + N * math.sin(phi)) * ds
        path.append((p, N * math.cos(phi) - T * math.sin(phi)))
    return path


def sb_fin_material():
    g = Hm._Graph("SB_Fin")
    u, v, _ = g.sep(g.coords("UV"))
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    streak = g.n("ShaderNodeTexNoise", **{"Scale": 7.0, "Detail": 4.0})
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (10.0, 0.7, 1.0)
    g.link(g.coords("UV"), mp.inputs["Vector"])
    g.link(mp.outputs[0], streak.inputs["Vector"])
    col = g.ramp(streak.outputs["Fac"], [(0.35, (0.72, 0.84, 0.96)), (0.6, (0.95, 0.97, 0.99))])
    edge = g.math("GREATER_THAN", du, 0.44)
    col = g.mix(edge, col, (1.0, 0.72, 0.26))
    return g.finish(col, g.math("ADD", 0.2, g.math("MULTIPLY", edge, 0.1)), g.math("MULTIPLY", edge, 0.75), g.bump(streak.outputs["Fac"], 0.15, 0.003))


def sb_fins(coll):
    hi = Hm.Hi()
    for r, length in zip(SB_RIBBONS[:3], (1.25, 0.8, 0.95)):
        path = sb_ribbon_path(r, length)
        wid = r[4] * 2 * 1.9
        F.ribbon(hi, path, lambda t: wid * min(1.0, t * 5.0) ** 0.7 * (1 - t ** 2.4) ** 0.8 + 0.003, across=6)
    o = hi.object("SB_Fins", coll, [sb_fin_material()])
    Hm.solidify(o, 0.022)
    o["w"] = 1.4
    return o


def sb_crescent(coll, gold):
    hi = Hm.Hi()
    s0, v0 = SB_SEAL
    centre, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()

    def lay(x, y, off):
        # from the plane to the shell: along the normal until it meets the egg, then `off` above
        q = centre + e1 * x + e2 * y
        ss = (math.atan2(q.x, q.z) / F.TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi
        return F.on(ss, vv, off), F.normal(ss, vv)
    # the crescent: thick at its back (the viewer's left), tapering to two horns that open right
    rows = []
    steps, across = 54, 8
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(40 + 280 * t)
        wid = 0.2 * math.sin(math.pi * t) ** 0.8 + 0.004
        row = []
        for j in range(across + 1):
            k = -1 + 2 * j / across
            rad = 0.395 + 0.015 * math.cos(a - math.pi) + k * wid / 2
            cx, cy = math.cos(a) * rad, math.sin(a) * rad
            dome = 0.08 * math.sin(math.pi * t) ** 0.5 * (1 - k * k) ** 0.6
            p, _ = lay(cx, cy, 0.012 + dome)
            row.append(hi.v(p))
        rows.append(row)
    for i in range(steps):
        for j in range(across):
            q = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
            hi.facing(q, [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(n))
    # a scroll at the upper horn, its line thinning into the curl
    horn = (math.cos(math.radians(40)) * 0.395, math.sin(math.radians(40)) * 0.395)
    curl = []
    for i in range(30):
        t = i / 29
        a = math.radians(-60) + F.TAU * 1.5 * t
        r = 0.1 * (1 - 0.82 * t)
        curl.append(lay(horn[0] + 0.08 + r * math.cos(a), horn[1] + 0.03 + r * math.sin(a), 0.02)[0])
    Hm.htube(hi, curl, lambda t: 0.026 * (1 - 0.6 * t), sides=8, per=2, wobble=0)
    # a fine ring holding the roundel
    ring = [lay(math.cos(F.TAU * i / 48) * 0.285, math.sin(F.TAU * i / 48) * 0.285, 0.006)[0] for i in range(49)]
    Hm.htube(hi, ring, lambda t: 0.012, sides=6, per=1, wobble=0, tip=False)
    o = hi.object("SB_Crescent", coll, [gold])
    # the sigil: three wind strokes, each sweeping into a little hook
    sig = Hm.Hi()
    for k, (dy, L, hook) in enumerate(((0.11, 0.26, 1), (0.0, 0.36, -1), (-0.11, 0.22, 1))):
        pts = []
        for i in range(26):
            t = i / 25
            x = -L / 2 + L * t
            y = dy + 0.022 * math.sin(math.pi * t * 1.6)
            if t > 0.7:
                u = (t - 0.7) / 0.3
                a = u * math.pi * 1.25
                x = -L / 2 + L * 0.7 + math.sin(a) * 0.06
                y = dy + 0.022 + hook * (1 - math.cos(a)) * 0.05
            pts.append(lay(x, y, 0.002))
        F.prism(sig, pts, lambda t: 0.04 * (0.25 + 0.75 * math.sin(math.pi * t) ** 0.5), height=lambda w: w * 0.3)
    return o, sig.object("SB_Sigil", coll, [K.glow_material(SB_SIGIL)], smooth=False, weld=0)


def sb_clouds(coll, gold):
    spheres = []
    faces = []
    count = 7
    for k in range(count):
        a = F.TAU * (k + 0.5) / count
        out = V((math.sin(a), 0, math.cos(a)))
        side = V((0, 1, 0)).cross(out)
        ring = 0.84
        for dx, dy, r, stretch in ((0.0, 0.33, 0.33, 1.0), (-0.34, 0.23, 0.23, 0.95), (0.34, 0.23, 0.23, 0.95)):
            c = out * ring + side * dx + V((0, dy, 0))
            spheres.append((c, r, (1.0, 0.9, 1.0)))
            faces.append((c, r, (out + side * dx * 1.2 + V((0, 0.25, 0))).normalized()))
    bed = F.lobes("SB_Clouds", coll, Hm.mat_cloud("SB_Cloud"), spheres, voxel=0.018)
    bed["w"] = 1.6
    hi = Hm.Hi()
    for k, (c, r, out) in enumerate(faces):
        big = r > 0.28
        pts = F.sphere_spiral(c, r * 0.985, out, turns=1.8 if big else 1.4, reach=0.92)
        Hm.htube(hi, pts[::2], lambda t: (0.021 if big else 0.016) * (1 - 0.5 * t), sides=7, per=2, wobble=0)
    scroll = hi.object("SB_Scrolls", coll, [gold])
    return bed, scroll


def spirit_breeze_clay():
    coll = W.collection("SpiritBreezeEggHi")
    gold = Hm.mat_gold("SB_Gold")
    shell = F.shell_mesh("SB_Shell", coll, 96, 64)
    fins = sb_fins(coll)
    cres, sig = sb_crescent(coll, gold)
    bed, scroll = sb_clouds(coll, gold)
    return {o.name: F.tris(o) for o in (shell, fins, cres, sig, bed, scroll)}


def spirit_breeze_build():
    coll = W.collection("SpiritBreezeEggHi")
    gold = Hm.mat_gold("SB_Gold")
    f, col, rough, metal, height = spirit_breeze_paint()
    mat = F.shell_material("SB_Glaze", col, rough, metal)
    fins = sb_fins(coll)
    cres, sig = sb_crescent(coll, gold)
    bed, scroll = sb_clouds(coll, gold)
    return F.assemble("SpiritBreezeEgg", coll, mat, height, [fins, cres, bed, scroll], {SB_SIGIL: [sig]}, budget=8500)


# ---------- Elemental Core Egg ----------
EC_RING = "12d8ff"
EC_CORE_AT = (0.5, 0.45)
EC_V = (0.415, 0.485)        # the belt's two rails


def elemental_paint():
    f = F.Field()
    P = f.P
    # the fractures: big plates, their boundaries warped so no straight Voronoi walls show
    warp = np.stack([F.fbm(P, 2.2, 3, seed=s) for s in (1, 2, 3)], -1) * 0.13
    f1, edge, cid = F.voronoi(P + warp, 2.5, seed=7, jitter=1.0, stretch=(1.0, 0.85, 1.0))
    grain = F.fbm(P, 8.0, 5, 0.55, seed=4)
    fine = F.fbm(P, 28.0, 3, seed=5)
    width = 0.034 + 0.03 * np.clip(F.fbm(P, 3.0, 2, seed=6) + 0.2, 0, 1)
    crack = 1 - F.sstep(0.0, width, edge)
    hair = 1 - F.sstep(0.0, 0.05, F.ridged(P + warp, 5.0, 3, seed=9))
    hair = hair * (1 - crack) * F.sstep(0.05, 0.3, F.fbm(P, 2.0, 2, seed=10))
    height = 0.05 * (cid - 0.5) + 0.018 * grain + 0.004 * fine - 0.05 * crack - 0.012 * hair
    # chipped: each plate breaks away near its edge
    chip = F.sstep(width * 1.0, width * 2.6, edge) * 0.0 + (1 - F.sstep(width, width * 2.4, edge)) * (1 - crack)
    height = height - 0.016 * chip * np.clip(0.5 + fine * 1.4, 0, 1)
    tone = np.clip(0.42 + 0.5 * grain + 0.24 * (cid - 0.5), 0, 1)
    col = F.ramp(tone, [(0.0, "0f1216"), (0.35, "1d2229"), (0.65, "2f3641"), (1.0, "4a5361")])
    # mineral flecks, worn pale on the chipped edges
    col = F.mix(col, np.array((0.5, 0.56, 0.62)), chip * 0.5 * np.clip(0.5 + fine, 0, 1))
    col = F.mix(col, np.array((0.03, 0.035, 0.04)), hair * 0.75)
    # the Qi: strongest round the core, dying out toward the poles, patchy
    x, y, front = f.plane(*EC_CORE_AT)
    d = np.hypot(x, y * 0.9) + (1 - np.clip(front, 0, 1)) * 2.0
    reach = np.clip(1 - F.sstep(0.45, 2.3, d) + 0.5 * F.sstep(0.1, 0.45, F.fbm(P, 1.4, 2, seed=14)), 0, 1)
    qi = crack * reach
    hot = F.ramp(1 - np.clip(edge / np.maximum(width, 1e-4), 0, 1), [(0.0, "0a4f80"), (0.4, "12a7e6"), (0.8, "58eaff"), (1.0, "c6fbff")])
    col = F.mix(col, np.where(crack[..., None] > 0, hot, col), np.clip(qi * 1.5, 0, 1))
    spill = np.clip(F.blur(qi, 14) * 2.2, 0, 1) * (1 - crack)
    col = col + np.array((0.0, 0.2, 0.3)) * spill[..., None]
    rough = 0.82 - 0.35 * qi + 0.1 * np.clip(grain, -1, 1) * 0.5
    return f, np.clip(col, 0, 1), np.clip(rough, 0, 1), np.zeros(f.S.shape), height


def ec_cage(coll, gold):
    hi = Hm.Hi()
    joints = []
    W_, H_ = 0.05, 0.05
    lo, up = EC_V
    cs, cv = EC_CORE_AT
    gap = 0.075           # the belt stops either side of the bezel
    for v in (lo, up):
        F.bar(hi, F.along_shell((cs + gap, v), (cs + 1 - gap, v), 0.02, steps=70), 0.042, 0.042)
    # a low wall between the rails with square piercings left by short bars
    for k in range(1, 18):
        ss = cs + gap + (1 - 2 * gap) * k / 18
        F.bar(hi, F.along_shell((ss, lo), (ss, up), 0.02, steps=3), 0.018, 0.022)
    # the lancets: an upper and a lower zigzag, sharing their feet with the belt
    teeth = 6
    for k in range(teeth):
        a = cs + (k + 0.0) / teeth + 0.0833
        b = a + 0.5 / teeth
        c = a + 1.0 / teeth
        for (p, q, r) in (((a, up), (b, 0.8), (c, up)), ((a, lo), (b, 0.13), (c, lo))):
            # the front tooth's foot lands on the bezel; leave those legs to the bezel
            F.bar(hi, F.along_shell(p, q, 0.02, steps=10), W_, H_)
            F.bar(hi, F.along_shell(q, r, 0.02, steps=10), W_, H_ + 0.005)   # a hair prouder: crossing tops must not be coplanar
        joints += [(b, 0.8, 0.044), (b, 0.13, 0.04), (a, up, 0.036), (a, lo, 0.036)]
        # from each peak a strap to the crown, each valley a strap to the foot ring
        F.bar(hi, F.along_shell((b, 0.8), (b, 0.945), 0.018, steps=6), lambda t: 0.042 * (1 - 0.45 * t), 0.04)
        F.rivet(hi, F.on(b % 1.0, 0.095, 0.06), F.normal(b % 1.0, 0.095), 0.03)
    # rings at the crown and foot
    F.bar(hi, F.along_shell((0, 0.94), (1, 0.94), 0.02, steps=48)[:-1], 0.036, 0.046, closed=True)
    F.bar(hi, F.along_shell((0, 0.092), (1, 0.092), 0.02, steps=36)[:-1], 0.036, 0.046, closed=True)
    for s_, v_, r in joints:
        F.rivet(hi, F.on(s_ % 1.0, v_, 0.055), F.normal(s_ % 1.0, v_), r)
    return hi


def ec_bezel(hi):
    """The hex bezel round the core and its six prongs."""
    cs, cv = EC_CORE_AT
    c, n = F.on(cs, cv, 0.0), F.normal(cs, cv)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    R = 0.45
    corners = [c + (e1 * math.cos(F.TAU * (k + 0.5) / 6) + e2 * math.sin(F.TAU * (k + 0.5) / 6) * 1.08) * R for k in range(6)]
    for k in range(6):
        a, b = corners[k], corners[(k + 1) % 6]
        path = [(a.lerp(b, t / 8), n) for t in range(9)]
        F.bar(hi, path, 0.07, 0.085, foot=0.3)
        # a prong climbing from each corner over the stone's shoulder
        p0 = a
        toward = (c - a).normalized()
        pr = [(p0 + toward * (0.13 * t / 8) + n * (0.09 + 0.1 * math.sin(math.pi * t / 8 * 0.6)), (n + toward * -0.3).normalized()) for t in range(9)]
        F.bar(hi, pr, lambda t: 0.05 * (1 - 0.55 * t), 0.03)
    return c, n


def ec_crown_feet(hi):
    # a claw finial: six tapering spikes rising off the crown ring toward a point, gripping a gem
    top = V((0, F.H + 0.02, 0))
    for k in range(6):
        a = F.TAU * k / 6 + 0.26
        base = F.on((a / F.TAU) % 1.0, 0.93, 0.035)
        tip = top + V((math.sin(a) * 0.08, 0.2, math.cos(a) * 0.08))
        mid = base.lerp(tip, 0.5) + V((math.sin(a) * 0.06, 0.03, math.cos(a) * 0.06))
        Hm.htube(hi, [base, mid, tip], lambda t: 0.04 * (1 - 0.72 * t), sides=6, per=8, wobble=0)
    # four claws reaching down from the foot ring to the ground
    for k in range(4):
        a = F.TAU * (k + 0.5) / 4
        base = F.on(((a / F.TAU) + 0.0) % 1.0, 0.1, 0.03)
        out = V((math.sin(a), 0, math.cos(a)))
        knee = base + out * 0.22 + V((0, -0.02, 0))
        toe = V((base.x, 0.075, base.z)) + out * 0.3
        Hm.htube(hi, [base, knee, toe], lambda t: 0.06 * (1 - 0.3 * t), sides=8, per=8, wobble=0, tip=False)
        F.rivet(hi, toe + V((0, 0.02, 0)), (0, 1, 0), 0.05)


def ec_stones(coll):
    """The core and the five element stones: a separate piece each per material."""
    out = []
    cs, cv = EC_CORE_AT
    c, n = F.on(cs, cv, 0.02), F.normal(cs, cv)
    hi = Hm.Hi()
    F.cut_gem(hi, c, n, (0, 1, 0), 0.39, 0.25, sides=6, squash=0.92, base=0.25)
    core = F.fix_normals(hi.object("EC_CoreGem", coll, [F.gem_material("EC_CoreMat", (0.0, 0.2, 0.42), (0.0, 0.72, 0.95), (0.7, 1.0, 1.0), panes=5.0, pane_weight=0.1, axis=tuple(W.rb(*n)))], smooth=False, weld=1e-5))
    core["w"] = 0.0 + 1.5
    out.append(core)
    elements = (("Ruby", 0.2, (0.2, 0.0, 0.02), (0.85, 0.03, 0.08), (1.0, 0.45, 0.45)),
                ("Emerald", 0.33, (0.0, 0.1, 0.03), (0.02, 0.65, 0.22), (0.5, 1.0, 0.65)),
                ("Topaz", 0.67, (0.3, 0.1, 0.0), (1.0, 0.55, 0.04), (1.0, 0.9, 0.45)),
                ("Sapphire", 0.8, (0.0, 0.02, 0.2), (0.04, 0.2, 0.95), (0.5, 0.72, 1.0)),
                ("Amethyst", 0.0, (0.08, 0.0, 0.2), (0.45, 0.08, 0.85), (0.85, 0.6, 1.0)))
    for name, ss, dark, mid, light in elements:
        vv = sum(EC_V) / 2
        p, nn = F.on(ss, vv, 0.05), F.normal(ss, vv)
        h = Hm.Hi()
        F.cut_gem(h, p, nn, (0, 1, 0), 0.105, 0.075, sides=6, base=0.03)
        o = F.fix_normals(h.object("EC_" + name, coll, [F.gem_material("EC_" + name + "Mat", dark, mid, light, panes=30.0, depth=0.08)], smooth=False))
        o["w"] = 3.0
        out.append(o)
    return out


def ec_gold_pieces(coll, gold):
    hi = ec_cage(coll, gold)
    ec_bezel(hi)
    ec_crown_feet(hi)
    # settings for the five stones
    for ss in (0.2, 0.33, 0.67, 0.8, 0.0):
        vv = sum(EC_V) / 2
        p, nn = F.on(ss, vv, 0.03), F.normal(ss, vv)
        e1 = V((0, 1, 0)).cross(nn).normalized()
        e2 = nn.cross(e1).normalized()
        pts = [(p + (e1 * math.cos(F.TAU * k / 24) + e2 * math.sin(F.TAU * k / 24)) * 0.125, nn) for k in range(24)]
        F.bar(hi, pts, 0.035, 0.05, closed=True)
    o = hi.object("EC_Cage", coll, [gold], smooth=False)
    F.fix_normals(o)
    Hm.apply_modifiers(o, [("BEVEL", {"width": 0.006, "segments": 2, "limit_method": "ANGLE", "angle_limit": math.radians(35)})])
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.0
    return o


def ec_ring(coll):
    """A thread of Qi round the bezel's foot, where the stone meets the gold."""
    cs, cv = EC_CORE_AT
    c, n = F.on(cs, cv, 0.07), F.normal(cs, cv)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    hi = Hm.Hi()
    corners = [c + (e1 * math.cos(F.TAU * (k + 0.5) / 6) + e2 * math.sin(F.TAU * (k + 0.5) / 6) * 1.08) * 0.405 for k in range(6)]
    pts = []
    for k in range(6):
        a, b = corners[k], corners[(k + 1) % 6]
        for t in range(6):
            pts.append((a.lerp(b, t / 6), n))
    F.prism(hi, pts, 0.016, height=lambda w: w * 0.3, closed=True)
    return hi.object("EC_Ring", coll, [K.glow_material(EC_RING)], smooth=False, weld=0)


def elemental_clay():
    coll = W.collection("ElementalCoreEggHi")
    gold = Hm.mat_gold("EC_Gold")
    shell = F.shell_mesh("EC_Shell", coll, 96, 64)
    cage = ec_gold_pieces(coll, gold)
    stones = ec_stones(coll)
    ring = ec_ring(coll)
    return {o.name: F.tris(o) for o in [shell, cage, ring] + stones}


def elemental_build():
    coll = W.collection("ElementalCoreEggHi")
    gold = Hm.mat_gold("EC_Gold")
    f, col, rough, metal, height = elemental_paint()
    mat = F.shell_material("EC_Stone", col, rough, metal)
    cage = ec_gold_pieces(coll, gold)
    stones = ec_stones(coll)
    ring = ec_ring(coll)
    return F.assemble("ElementalCoreEgg", coll, mat, height, [cage] + stones, {EC_RING: [ring]}, budget=8000, shell_frac=0.62, hard=25, low_nu=72, low_nv=46)

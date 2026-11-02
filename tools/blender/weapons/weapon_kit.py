"""What the realm weapons share (run inside Blender): the Blacksmith's sword and spear for each realm
(GameConfig.WeaponTiers; one script per realm, tier01.py, tier02.py ...).

Each weapon is built like the flying sword (flying_sword.py) and the eggs: high-detail pieces with
procedural shaders, baked onto one game mesh ("Body"), plus Neon glow pieces, one per colour.

Authored in Roblox studs from the grip, where the hand holds it: the point toward -Z, a sword's
flats facing +-Y and its edges +-X. export() writes assets/weapons/<WeaponId>.fbx with its maps,
and src/worldbuild/Placements/Weapons/<WeaponId>.lua (its pieces' centres, where its blade or head
starts, "Hilt", and its point, "Tip"), which OutfitBuilder.storeWeapon reads.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eggs"))
import egg_bake as B  # noqa: E402
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402

W = K.W
V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(W.REPO, "assets", "weapons")
PLACEMENTS_DIR = os.path.join(W.REPO, "src", "worldbuild", "Placements", "Weapons")


# ---------- shapes ----------
def loft(hi, rings, mat=0, cap_start=True, cap_end=True, uv_scale=2.0):
    """A closed surface through cross-section rings [(centre, [points])], all of one size, listed
    from start to end; each face turned out from the axis. Ends capped as fans."""
    m = len(rings[0][1])
    ids = [[hi.v(p) for p in pts] for _, pts in rings]
    length = 0.0
    for k in range(len(rings) - 1):
        (c0, p0), (c1, p1) = rings[k], rings[k + 1]
        step = (c1 - c0).length
        for i in range(m):
            j = (i + 1) % m
            mid = (p0[i] + p0[j] + p1[i] + p1[j]) / 4
            out = mid - (c0 + c1) / 2
            axis = (c1 - c0).normalized() if step > 1e-6 else V((0, 0, 1))
            out = out - axis * out.dot(axis)
            if out.length < 1e-7:
                out = V((0, 1, 0))
            uv = [(i / m, length * uv_scale), ((i + 1) / m, length * uv_scale), ((i + 1) / m, (length + step) * uv_scale),
                  (i / m, (length + step) * uv_scale)]
            hi.facing([ids[k][i], ids[k][j], ids[k + 1][j], ids[k + 1][i]], uv, tuple(out), mat)
        length += step
    if cap_start:
        _cap(hi, rings[0][0], ids[0], rings[0][0] - rings[1][0], mat)
    if cap_end:
        _cap(hi, rings[-1][0], ids[-1], rings[-1][0] - rings[-2][0], mat)


def _cap(hi, centre, ids, outward, mat):
    c = hi.v(centre)
    m = len(ids)
    for i in range(m):
        hi.facing([ids[i], ids[(i + 1) % m], c], [(0, 0), (1, 0), (0.5, 1)], tuple(outward), mat)


def blob(hi, a, b, radius, sides=12, per=6, mat=0):
    """A rounded swelling from a to b (an eye, a crest, a cabochon)."""
    Hm.htube(hi, [V(a), (V(a) + V(b)) / 2, V(b)], lambda t: radius * math.sin(math.pi * (0.04 + 0.92 * t)) ** 0.7 + 0.002,
             sides=sides, per=per, mat=mat, uv_scale=3.0, tip=False, wobble=0.0)


def helix(hi, z0, z1, radius, turns, tube, phase=0.0, hand=1, mat=0, x=0.0, y=0.0):
    """A cord wound round the z axis (a grip's binding)."""
    n = max(24, int(turns * 24))
    pts = [V((x + radius * math.cos(phase + hand * TAU * turns * i / n), y + radius * math.sin(phase + hand * TAU * turns * i / n),
              z0 + (z1 - z0) * i / n)) for i in range(n + 1)]
    Hm.htube(hi, pts, lambda t: tube, sides=6, per=1, mat=mat, uv_scale=6.0, tip=False, wobble=0.0)


def disc(hi, centre, normal, radius, n=16, mat=0):
    """A flat disc facing `normal`."""
    nrm = V(normal).normalized()
    ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
    s = nrm.cross(ref).normalized()
    t = nrm.cross(s)
    c = hi.v(V(centre))
    ring = [hi.v(V(centre) + (s * math.cos(TAU * i / n) + t * math.sin(TAU * i / n)) * radius) for i in range(n)]
    for i in range(n):
        hi.facing([ring[i], ring[(i + 1) % n], c], [(0, 0), (1, 0), (0.5, 1)], tuple(nrm), mat)


def leaves(coll, name, materials, specs, thickness=0.02):
    """Leaf-shaped blades given thickness: specs are egg_hi.leaf keyword sets, each with "mat" (an
    index into materials). Marked as a sheet for make_low."""
    hi = Hm.Hi()
    for spec in specs:
        Hm.leaf(hi, **spec)
    o = Hm.solidify(hi.object(name, coll, materials, smooth=True), thickness)
    o["sheet"] = True   # make_low keeps more of thin sheets
    return o


def blade(hi, z0, z1, half_width, thickness, sway=None, twist=None, n=80, m=16, rib=0.35, mat=0, cap_start=True, cap_end=False):
    """A double-edged blade from z0 (its foot) to z1 (its point): half_width(t) and thickness(t),
    t 0 foot to 1 point, a raised ridge down its middle (rib), optionally swaying sideways (x) and
    twisting about its ridge. Returns surface(t, dx=0, side=1, lift=0.003): the point on its face
    (side +1 or -1) dx across from the ridge, lifted off it, for inlays."""
    sway = sway or (lambda t: 0.0)
    twist = twist or (lambda t: 0.0)

    def turned(cx, x, y, a):
        return cx + x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    rings = []
    for k in range(n + 1):
        t = k / n
        z = z0 + (z1 - z0) * t
        w, th, cx, a = max(0.0, half_width(t)), thickness(t), sway(t), twist(t)
        pts = []
        for i in range(m):
            ang = TAU * i / m
            c, s = math.cos(ang), math.sin(ang)
            y = math.copysign(th * abs(s) ** 0.9 * (1 + rib * math.exp(-(c / 0.15) ** 2)), s)
            x, y = turned(cx, w * c, y, a)
            pts.append(V((x, y, z)))
        rings.append((V((cx, 0, z)), pts))
    loft(hi, rings, mat=mat, cap_start=cap_start, cap_end=cap_end, uv_scale=1.0)

    def surface(t, dx=0.0, side=1, lift=0.003):
        w, th = max(1e-4, half_width(t)), thickness(t)
        c = max(-0.98, min(0.98, dx / w))
        y = th * (1 - c * c) ** 0.45 * (1 + rib * math.exp(-(c / 0.15) ** 2)) + lift
        x, y = turned(sway(t), w * c, side * y, twist(t))
        return V((x, y, z0 + (z1 - z0) * t))
    return surface


def ribbon(hi, surface, t0, t1, offset, half, sides=(1, -1), n=60, mat=0, lift=0.004):
    """An inlay lying on a blade's faces (surface, from blade()): from t0 to t1, centred offset(t)
    across from the ridge, half(t) wide each way."""
    for side in sides:
        rows = []
        for k in range(n + 1):
            t = t0 + (t1 - t0) * k / n
            c, h = offset(t), max(0.0, half(t))
            rows.append((surface(t, c - h, side, lift), surface(t, c + h, side, lift), surface(t, c, side, lift + 0.05) - surface(t, c, side, lift)))
        for k in range(n):
            (a, b, up), (c_, d, _) = rows[k], rows[k + 1]
            ids = [hi.v(a), hi.v(b), hi.v(d), hi.v(c_)]
            hi.facing(ids, [(0, k / n), (1, k / n), (1, (k + 1) / n), (0, (k + 1) / n)], tuple(up), mat)


def runes(hi, place, count, seed=0, tube=0.012, mat=0):
    """Rune glyphs of three or four strokes each, invented per seed: place(i, u, v) maps glyph i's
    unit square (u across, v along, 0..1) onto the surface."""
    import random
    rnd = random.Random(seed)
    for i in range(count):
        for _ in range(rnd.choice((3, 3, 4))):
            if rnd.random() < 0.5:   # a straight stroke
                a = (rnd.uniform(0.05, 0.95), rnd.uniform(0.05, 0.95))
                b = (rnd.uniform(0.05, 0.95), rnd.uniform(0.05, 0.95))
                pts = [place(i, *a), place(i, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2), place(i, *b)]
            else:                    # a hooked stroke
                cu, cv, r = rnd.uniform(0.3, 0.7), rnd.uniform(0.3, 0.7), rnd.uniform(0.2, 0.35)
                a0 = rnd.uniform(0, TAU)
                pts = [place(i, cu + r * math.cos(a0 + 1.6 * j / 4), cv + r * math.sin(a0 + 1.6 * j / 4)) for j in range(5)]
            Hm.htube(hi, pts, lambda t: tube, sides=5, per=2, mat=mat, uv_scale=3.0, tip=False, wobble=0.0)


def crystal(hi, base, tip, radius, sides=6, waist=0.3, phase=0.0, mat=0):
    """A faceted crystal from `base` to `tip`, widest (radius) a fraction `waist` along it. Returns
    the waist ring's points (for edge lines)."""
    b, t = V(base), V(tip)
    axis = (t - b).normalized()
    ref = V((0, 1, 0)) if abs(axis.y) < 0.9 else V((1, 0, 0))
    s = axis.cross(ref).normalized()
    u = axis.cross(s)

    def ring_at(f, r):
        c = b.lerp(t, f)
        return (c, [c + (s * math.cos(phase + TAU * i / sides) + u * math.sin(phase + TAU * i / sides)) * r for i in range(sides)])
    rings = [ring_at(0.0, radius * 0.25), ring_at(waist, radius), ring_at(waist + (1 - waist) * 0.35, radius * 0.85), ring_at(1.0, 0.002)]
    loft(hi, rings, mat=mat, uv_scale=3.0)
    return rings[1][1]


def ring(hi, centre, normal, radius, tube, n=48, sides=8, mat=0):
    """A torus: a ring of `radius` round `centre`, facing `normal`."""
    nrm = V(normal).normalized()
    ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
    s = nrm.cross(ref).normalized()
    t = nrm.cross(s)
    pts = [V(centre) + (s * math.cos(TAU * i / n) + t * math.sin(TAU * i / n)) * radius for i in range(n + 1)]
    Hm.htube(hi, pts + [pts[1]], lambda u: tube, sides=sides, per=1, mat=mat, uv_scale=3.0, tip=False, wobble=0.0)


def sphere(hi, centre, radius, sides=16, mat=0):
    c = V(centre)
    blob(hi, c - V((0, radius, 0)), c + V((0, radius, 0)), radius, sides=sides, per=8, mat=mat)


def flat(hi, outline, y, thickness, mat=0):
    """A flat plate in the XZ plane at height y: its outline [(x, z)] (convex or star-shaped about its
    centroid), both faces and its rim."""
    cx = sum(p[0] for p in outline) / len(outline)
    cz = sum(p[1] for p in outline) / len(outline)
    top = [V((x, y + thickness / 2, z)) for x, z in outline]
    bot = [V((x, y - thickness / 2, z)) for x, z in outline]
    loft(hi, [(V((cx, y - thickness / 2, cz)), bot), (V((cx, y + thickness / 2, cz)), top)], mat=mat, uv_scale=3.0)


# ---------- materials ----------
def _noise(g, scale, detail=4.0, distortion=0.0, coords=None):
    n = g.n("ShaderNodeTexNoise", **{"Scale": scale, "Detail": detail, "Distortion": distortion})
    g.link(coords if coords is not None else g.coords(), n.inputs["Vector"])
    return n.outputs["Fac"]


def _stripes(g, count, axis=0):
    """0..1 stripes across a piece's UV: axis 0 runs them along v (lengthwise grain round a tube)."""
    s = g.sep(g.coords("UV"))
    w = g.math("SINE", g.math("MULTIPLY", s[axis], TAU * count))
    return g.math("ADD", g.math("MULTIPLY", w, 0.5), 0.5)


def mat_celadon_steel(name="WpnCeladonSteel"):
    """Pale celadon-tinted steel, the parallel veins of a reed leaf running down it."""
    g = Hm._Graph(name)
    n = _noise(g, 14.0)
    veins = g.math("POWER", _stripes(g, 7), 6.0)
    col = g.ramp(n, [(0.3, (0.5, 0.6, 0.56)), (0.7, (0.68, 0.77, 0.72))])
    col = g.mix(g.math("MULTIPLY", veins, 0.35), col, (0.32, 0.42, 0.4))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, 0.26, 0.7, g.bump(g.math("ADD", n, g.math("MULTIPLY", veins, -0.6)), 0.12, 0.003))


def mat_reed(name="WpnReed", dark=(0.46, 0.34, 0.14), light=(0.8, 0.66, 0.34)):
    """Dried reed: straw gold with fine fibres along it."""
    g = Hm._Graph(name)
    fib = _stripes(g, 22)
    n = _noise(g, 9.0)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", n, 0.7), g.math("MULTIPLY", fib, 0.3)), [(0.25, dark), (0.75, light)])
    col = g.ao(col, 0.04, 0.4)
    return g.finish(col, 0.55, 0.0, g.bump(fib, 0.1, 0.003))


def mat_bamboo(name="WpnBamboo"):
    """A living culm: deep green with paler streaks along it, waxy."""
    g = Hm._Graph(name)
    streak = _noise(g, 1.0, 3.0, coords=g.math("MULTIPLY", g.sep(g.coords("UV"))[0], 9.0))
    n = _noise(g, 6.0)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", streak, 0.6), g.math("MULTIPLY", n, 0.4)),
                 [(0.3, (0.05, 0.17, 0.035)), (0.55, (0.11, 0.29, 0.06)), (0.8, (0.27, 0.42, 0.11))])
    col = g.ao(col, 0.05, 0.35)
    return g.finish(col, 0.34, 0.0, g.bump(streak, 0.05, 0.003))


def mat_sheath(name="WpnSheath"):
    """A bamboo shoot's sheath: papery straw-brown, mottled with dark spots."""
    g = Hm._Graph(name)
    vor = g.n("ShaderNodeTexVoronoi", **{"Scale": 14.0})
    g.link(g.coords(), vor.inputs["Vector"])
    spots = g.math("LESS_THAN", vor.outputs["Distance"], 0.16)
    n = _noise(g, 8.0)
    col = g.ramp(n, [(0.3, (0.5, 0.36, 0.17)), (0.7, (0.72, 0.56, 0.3))])
    col = g.mix(g.math("MULTIPLY", spots, 0.85), col, (0.17, 0.09, 0.04))
    return g.finish(g.ao(col, 0.03, 0.5), 0.7, 0.0)


def mat_plain(name, dark, light, rough=0.6, metal=0.0, scale=10.0, bump=0.06):
    """A simple surface between two colours (cords, cut wood, plumes, lacquer, thorns)."""
    g = Hm._Graph(name)
    n = _noise(g, scale)
    col = g.ao(g.ramp(n, [(0.3, dark), (0.7, light)]), 0.04, 0.45)
    return g.finish(col, rough, metal, g.bump(n, bump, 0.003))


def mat_cord(name, dark, light):
    """A wound cord: its twist shows as fine diagonal ridges."""
    g = Hm._Graph(name)
    s = g.sep(g.coords("UV"))
    twist = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", g.math("ADD", s[0], s[1]), TAU * 3)), 0.5), 0.5)
    col = g.ao(g.ramp(twist, [(0.0, dark), (1.0, light)]), 0.03, 0.45)
    return g.finish(col, 0.75, 0.0, g.bump(twist, 0.15, 0.003))


def mat_slate(name="WpnSlate"):
    """Dark blue-grey slate, split: rough grain, pale fracture lines."""
    g = Hm._Graph(name)
    n = _noise(g, 7.0, 6.0, 0.4)
    vor = g.n("ShaderNodeTexVoronoi", **{"Scale": 2.5, "feature": "DISTANCE_TO_EDGE"})
    g.link(g.coords(), vor.inputs["Vector"])
    cracks = g.math("LESS_THAN", vor.outputs["Distance"], 0.012)
    col = g.ramp(n, [(0.3, (0.03, 0.035, 0.05)), (0.7, (0.09, 0.1, 0.12))])
    col = g.mix(g.math("MULTIPLY", cracks, 0.35), col, (0.25, 0.27, 0.3))
    col = g.ao(col, 0.05, 0.4)
    return g.finish(col, 0.78, 0.0, g.bump(g.math("ADD", n, g.math("MULTIPLY", cracks, -0.5)), 0.35, 0.006))


def mat_stone(name="WpnStone", dark=(0.32, 0.31, 0.29), light=(0.52, 0.5, 0.46)):
    """Dressed stone: fine-grained, chisel-marked."""
    g = Hm._Graph(name)
    n = _noise(g, 16.0, 6.0)
    col = g.ao(g.ramp(n, [(0.3, dark), (0.7, light)]), 0.06, 0.35)
    return g.finish(col, 0.82, 0.0, g.bump(n, 0.25, 0.004))


def mat_celadon_jade(name="WpnCeladonJade"):
    """Celadon jade: pale blue-green, soft clouds of paler stone through it, polished."""
    g = Hm._Graph(name)
    n = _noise(g, 3.0, 5.0, 1.2)
    col = g.ramp(n, [(0.3, (0.16, 0.44, 0.44)), (0.55, (0.34, 0.64, 0.62)), (0.8, (0.62, 0.84, 0.8))])
    return g.finish(g.ao(col, 0.03, 0.55), 0.14, 0.0)


def mat_white_jade(name="WpnWhiteJade"):
    """White jade: milky, faint grey-green clouds through it, polished (the flying sword's guard)."""
    g = Hm._Graph(name)
    n = _noise(g, 3.0, 5.0, 1.2)
    col = g.ramp(n, [(0.35, (0.8, 0.84, 0.78)), (0.7, (0.92, 0.94, 0.9))])
    return g.finish(g.ao(col, 0.03, 0.55), 0.15, 0.0)


# ---------- export ----------
def export(weapon_id, kind, source, hi, glow, root, hilt, tip, budget=7000, size=1024, small=512):
    """Bakes and writes assets/weapons/<WeaponId>.fbx and its maps, and the placements file.
    glow: {hex: (piece name, [objects])}. hilt, tip: where the blade or head starts, and its point."""
    old = bpy.data.objects.get(weapon_id + "_Body")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(weapon_id, hi, root, budget)
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        B.bake(weapon_id, hi, low, size=size, small=small)
        parts = B.export(weapon_id, low, {h: objs for h, (_, objs) in glow.items()}, root)
    finally:
        B.EGG_DIR = saved
    names = {weapon_id + "_Body": ("Body", None)}
    for h, (piece, _) in glow.items():
        names[weapon_id + "_Glow_" + h] = (piece, h)
    lines = ["-- Generated by tools/blender/weapons/%s. Do not edit by hand." % source,
             "-- %s's pieces: centres as authored, in studs from the grip (where the hand holds it), its point" % weapon_id,
             "-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.",
             "return {",
             '    Kind = "%s",' % kind,
             "    Hilt = Vector3.new(%.3f, %.3f, %.3f), -- where the %s starts" % (*hilt, "blade" if kind == "Sword" else "head"),
             "    Tip = Vector3.new(%.3f, %.3f, %.3f)," % tuple(tip),
             "    Pieces = {"]
    report = {}
    for p in parts:
        pts = [V(K.rb_inv(*(p.matrix_world @ v.co))) for v in p.data.vertices]
        lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
        hi_ = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
        c = (lo + hi_) / 2
        piece, h = names[p.name]
        extra = ', Hex = "%s"' % h if h else ""
        lines.append("        %s = { Centre = Vector3.new(%.4f, %.4f, %.4f)%s }," % (piece, c.x, c.y, c.z, extra))
        report[piece] = ([round(x, 3) for x in c], [round(x, 3) for x in hi_ - lo], B.tris(p))
    lines += ["    },", "}", ""]
    os.makedirs(PLACEMENTS_DIR, exist_ok=True)
    with open(os.path.join(PLACEMENTS_DIR, weapon_id + ".lua"), "w") as f:
        f.write("\n".join(lines))
    return report


def clear():
    """Removes every weapon collection and object, leaving Blender's default Collection."""
    for c in list(bpy.data.collections):
        if c.name != "Collection":
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    for o in list(bpy.context.scene.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for s in list(bpy.data.scenes):
        if s != bpy.context.scene:
            bpy.data.scenes.remove(s)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

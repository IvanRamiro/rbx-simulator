"""Ember Peak's eggs, second generation (see egg_forge.py).

Inferno Egg, "eruption in progress": not a rock with glowing lines but a small volcano caught mid
blast. Basalt plates heaved apart, ash settled on their tops. The right shoulder has blown open into a
crater of lava; three rivers run from it down over the front, splitting and cooling from white-gold
through orange to a dull red crust. The plates from the crater are still in the air, big near the
hole and smaller as they fly.

Magma Heart Egg, "the geode": a shell of black crust broken open from the top, and what was inside
has grown out through the break: real crystal points of crimson garnet, a tall crown with its
companions, clusters flaring from the shoulders, small ones breaking through the crust lower down.
Molten veins run across the crimson, hottest where the points grow out of it.

Phoenix Ash Egg, "folded wings": the bird has not hatched, it is wrapped round itself. Rows of
overlapping crimson feather-scales in real relief, smaller toward the crown; two wings of layered
flame feathers (coverts, secondaries, primaries) sweep from the back and open around the egg; a crest
of long plumes streams back off the crown, and a gold flame burns on its breast.
"""
import math

import bmesh
import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K

V = F.V
W = K.W
TAU = F.TAU


def on_path(points, off=0.0):
    return [F.on(s % 1.0, v, off) for s, v in points]


# ---------- Inferno Egg ----------
IN_LAVA = "ff4a12"
IN_HOT = "ffa21e"
IN_CRATER = (0.72, 0.74)
# the rivers, from the crater's lip down the egg
IN_RIVERS = (
    ((0.68, 0.68), (0.63, 0.6), (0.6, 0.5), (0.54, 0.43), (0.52, 0.33), (0.47, 0.24), (0.47, 0.14)),
    ((0.74, 0.65), (0.77, 0.56), (0.74, 0.46), (0.76, 0.36), (0.73, 0.24), (0.74, 0.12)),
    ((0.6, 0.5), (0.5, 0.52), (0.42, 0.47), (0.37, 0.38), (0.31, 0.3), (0.3, 0.18)),
)


def in_river_dist(f):
    """Distance from every texel to the nearest river centre line (in egg units), and how far down
    that river it lies (0 at the crater, 1 at the end)."""
    best = np.full(f.S.shape, 9.0)
    along = np.zeros(f.S.shape)
    for r in IN_RIVERS:
        fine = [tuple(p) for p in K.W.catmull([(a, b, 0.0) for a, b in r], 8)]
        pts = np.array([(p[0], p[1]) for p in fine])
        # measure in units on the egg: s stretched by the girth, v by the height
        girth = 6.0 * np.sin(np.pi * np.clip(f.V, 0.05, 0.95))
        bests = np.full(f.S.shape, 9.0)
        al = np.zeros(f.S.shape)
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            px = ((f.S - ax + 0.5) % 1.0 - 0.5) * girth
            py = (f.V - ay) * 4.2
            ex = (bx - ax) * girth
            ey = (by - ay) * 4.2
            t = np.clip((px * ex + py * ey) / np.maximum(ex * ex + ey * ey, 1e-9), 0, 1)
            d = np.hypot(px - ex * t, py - ey * t)
            closer = d < bests
            bests = np.where(closer, d, bests)
            al = np.where(closer, (i + t) / (len(pts) - 1), al)
        closer = bests < best
        best = np.where(closer, bests, best)
        along = np.where(closer, al, along)
    return best, along


def inferno_paint():
    f = F.Field()
    P, Vv = f.P, f.V
    warp = np.stack([F.fbm(P, 2.0, 3, seed=s) for s in (201, 202, 203)], -1) * 0.14
    f1, edge, cid = F.voronoi(P + warp, 2.9, seed=204, jitter=1.0, stretch=(1.0, 0.85, 1.0))
    grain = F.fbm(P, 7.0, 5, 0.55, seed=205)
    fine = F.fbm(P, 26.0, 3, seed=206)
    width = 0.022 + 0.022 * np.clip(F.fbm(P, 2.6, 2, seed=207) + 0.3, 0, 1)
    seam = 1 - F.sstep(0.0, width, edge)
    height = 0.075 * (cid - 0.5) + 0.03 * grain + 0.006 * fine - 0.06 * seam
    # the rock: charcoal, with ash settling where the surface faces up, and heat crust by the seams
    tone = np.clip(0.42 + 0.55 * grain + 0.3 * (cid - 0.5), 0, 1)
    col = F.ramp(tone, [(0.0, "0b0908"), (0.4, "191412"), (0.75, "2c2421"), (1.0, "453a35")])
    up = np.clip(f.N[..., 1] + 0.1, 0, 1)
    ash = F.sstep(0.05, 0.42, F.fbm(P, 4.2, 4, seed=208) + up * 0.45) * (1 - seam)
    col = F.mix(col, F.ramp(np.clip(fine + 0.5, 0, 1), [(0.0, "4c4744"), (1.0, "8a8580")]), ash * 0.62)
    # the rivers, wandering a little and swelling
    wander = F.fbm(P, 3.2, 3, seed=209) * 0.03
    d, along = in_river_dist(f)
    d = d + wander
    wr = 0.075 * (1 - 0.55 * along) + 0.012
    river = 1 - F.sstep(wr * 0.65, wr, d)
    bank = (1 - F.sstep(wr, wr * 1.9, d)) * (1 - river)
    # the crater, blown out of the right shoulder
    x, y, front = f.plane(*IN_CRATER)
    cr = np.hypot(x, y) + 0.035 * F.fbm(P, 9.0, 3, seed=210) + (1 - np.clip(front, 0, 1)) * 2
    pit = 1 - F.sstep(0.26, 0.32, cr)
    lip = np.exp(-((cr - 0.36) / 0.055) ** 2) * (front > 0)
    height = height * (1 - pit) - 0.26 * F.blur(pit, 6) + 0.09 * lip
    height = height * (1 - river * 0.8) - 0.05 * river + 0.024 * bank
    # the heat: every seam glows a little, more near the crater and rivers, none far down the back
    near = np.exp(-(cr / 1.4) ** 2) + np.exp(-(d / 0.6) ** 2)
    heat = np.clip(seam * (0.35 + 1.0 * near), 0, 1)
    seam_col = F.ramp(1 - np.clip(edge / np.maximum(width, 1e-4), 0, 1), [(0.0, "2a0803"), (0.5, "a32106"), (0.85, "ff5a10"), (1.0, "ffb032")])
    col = F.mix(col, seam_col, heat)
    # river colour: white-gold at the centre, cooling along the way and toward its banks
    t = np.clip(d / np.maximum(wr, 1e-3), 0, 1)
    cool = np.clip(along * 0.55 + t * 0.75, 0, 1)
    crust = F.sstep(0.1, 0.4, F.fbm(P, 16.0, 3, seed=211) + cool * 0.45)
    lava = F.ramp(cool, [(0.0, "fff0a0"), (0.28, "ffc23a"), (0.55, "ff7a14"), (0.82, "e03208"), (1.0, "8a1604")])
    lava = F.mix(lava, np.array((0.12, 0.05, 0.03)), crust * 0.6 * cool)
    col = F.mix(col, lava, river)
    col = F.mix(col, np.array((0.36, 0.07, 0.015)), bank * 0.7)
    # the pool in the crater
    _, pool_edge, _ = F.voronoi(P, 16.0, seed=212)
    pool = F.ramp(np.clip(cr / 0.3 + (F.sstep(0.0, 0.05, pool_edge) - 0.5) * 0.4, 0, 1), [(0.0, "fff4b0"), (0.4, "ffc23a"), (0.8, "ff6a12"), (1.0, "b32206")])
    col = F.mix(col, pool, pit)
    spill = np.clip(F.blur(np.maximum(river, pit), 18) * 1.4, 0, 1) * (1 - np.maximum(river, pit))
    col = col + np.array((0.24, 0.05, 0.01)) * spill[..., None]
    rough = np.clip(0.72 + 0.2 * ash - 0.45 * np.maximum(river, pit) - 0.2 * heat, 0.1, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(f.S.shape), height, pit


def in_chunks(coll):
    """Plates from the crater, thrown up and out to the right along one arc: heavy ones close, small
    ones flying far, each its own shape."""
    mat = Hm.mat_obsidian("IN_Rock", heat_reach=0.035)
    hi = Hm.Hi()
    c, n = F.on(*IN_CRATER), F.normal(*IN_CRATER)
    side = V((0, 1, 0)).cross(n).normalized()
    flight = (n + V((0, 0.95, 0)) + side * 0.4).normalized()
    throw = [(0.36, 0.23, 0.0, 0.0), (0.62, 0.2, 0.17, 0.04), (0.92, 0.155, -0.15, 0.05), (1.2, 0.125, 0.06, 0.12), (1.5, 0.095, 0.22, 0.2), (1.76, 0.07, -0.1, 0.3), (2.0, 0.05, 0.11, 0.46)]
    for k, (dist, size, dx, drop) in enumerate(throw):
        p = c + flight * dist + side * dx - V((0, 1, 0)) * drop
        F.boulder(hi, p, size, seed=220 + k, stretch=(1.0, 0.65 + 0.2 * (k % 2), 0.85))
    # the broken rim: thick plates standing up round the crater's lip
    for k in range(9):
        a = TAU * k / 9 + 0.35
        e2 = n.cross(side).normalized()
        q = c + (side * math.cos(a) + e2 * math.sin(a)) * 0.37
        q = q - n * 0.02
        F.boulder(hi, q, 0.1 + 0.03 * (k % 3), seed=240 + k, stretch=(1.1, 0.9, 1.2))
    o = hi.object("IN_Chunks", coll, [mat], smooth=False)
    F.fix_normals(o)
    o["w"] = 2.5
    return o


def in_glow(coll, pit):
    """The hottest lava as Neon: threads down the rivers' centres and the crater's heart."""
    hi = Hm.Hi()
    for k, r in enumerate(IN_RIVERS):
        fine = W.catmull([(a, b, 0.0) for a, b in r], 7)
        pts = [(F.on(p[0] % 1.0, p[1], -0.02), F.normal(p[0] % 1.0, p[1])) for p in fine]
        F.prism(hi, pts, lambda t: 0.042 * (1 - 0.72 * t) ** 1.0, height=lambda w: w * 0.3)
    lava = hi.object("IN_LavaThreads", coll, [K.glow_material(IN_LAVA)], smooth=False, weld=0)
    c, n = F.on(*IN_CRATER), F.normal(*IN_CRATER)
    side = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(side).normalized()
    # a low dome of Neon in the pit's middle, its outline irregular
    h2 = Hm.Hi()
    cc = c - n * 0.24
    rim = []
    for k in range(18):
        a = TAU * k / 18
        r = 0.15 * (1 + 0.16 * math.sin(a * 3 + 1.0) + 0.1 * math.sin(a * 7))
        rim.append(h2.v(cc + (side * math.cos(a) + e2 * math.sin(a)) * r))
    top = h2.v(cc + n * 0.035)
    for k in range(18):
        h2.f([rim[k], rim[(k + 1) % 18], top], [(0, 0), (1, 0), (0, 1)])
    heart = F.fix_normals(h2.object("IN_Pool", coll, [K.glow_material(IN_HOT)], smooth=False, weld=0))
    return lava, heart


def inferno_clay():
    coll = W.collection("InfernoEggHi")
    f, col, rough, metal, height, pit = inferno_paint()
    shell = F.shell_mesh("IN_Shell", coll, 256, 160, height)
    ch = in_chunks(coll)
    lava, heart = in_glow(coll, pit)
    return {o.name: F.tris(o) for o in (shell, ch, lava, heart)}


def inferno_build():
    coll = W.collection("InfernoEggHi")
    f, col, rough, metal, height, pit = inferno_paint()
    mat = F.shell_material("IN_Basalt", col, rough, metal)
    ch = in_chunks(coll)
    lava, heart = in_glow(coll, pit)
    return F.assemble("InfernoEgg", coll, mat, height, [ch], {IN_LAVA: [lava], IN_HOT: [heart]}, budget=4500, shell_frac=0.72, low_nu=90, low_nv=60, shell_ext=0.2, shell_ray=0.45, hard=30)


# ---------- Magma Heart Egg ----------
MH_VEIN = "ff3214"
# the points: (s, v, length, radius, lean toward the crown 0..1). The crown first, then the clusters.
def _mh_layout():
    pts = [(0.5, 0.995, 1.35, 0.33, 1.0)]
    # three rings, each stepping down in size and leaning further out, so the crown reads as one
    # mass of crystal bursting through the top
    for count, v, L, r, lean, phase in ((5, 0.9, 1.0, 0.22, 0.72, 0.03), (7, 0.8, 0.68, 0.165, 0.46, 0.09), (9, 0.71, 0.42, 0.115, 0.26, 0.0)):
        for k in range(count):
            wob = math.sin(k * 2.4 + v * 9)
            pts.append(((k + 0.5) / count + phase + 0.018 * wob, v + 0.012 * math.cos(k * 1.7), L * (1 + 0.17 * wob), r * (1 + 0.1 * math.cos(k * 3.1)), lean))
    # two small clusters breaking through lower down
    for s_, v_ in ((0.37, 0.52), (0.86, 0.46)):
        for ds, dv, L, r in ((0.0, 0.0, 0.4, 0.115), (0.04, -0.035, 0.28, 0.085), (-0.035, -0.02, 0.24, 0.075)):
            pts.append((s_ + ds, v_ + dv, L, r, 0.15))
    return tuple(pts)


MH_POINTS = _mh_layout()


def magma_paint():
    f = F.Field()
    P, Vv = f.P, f.V
    warp = np.stack([F.fbm(P, 2.2, 3, seed=s) for s in (301, 302, 303)], -1) * 0.14
    # where the crust stops: a jagged broken edge, running high on the back and low at the front
    broken = 0.38 + 0.1 * np.cos(TAU * f.S + 0.8) + 0.12 * F.fbm(P, 3.2, 3, seed=304) + 0.03 * F.fbm(P, 16.0, 2, seed=305)
    crystal = F.sstep(broken - 0.004, broken + 0.004, Vv)
    edge_band = np.exp(-((Vv - broken) / 0.03) ** 2)
    # the crystal: a deep crimson garnet with broad internal planes
    _, wall, cid = F.voronoi(P + warp * 0.6, 3.6, seed=306, jitter=1.0)
    plane_tone = np.clip(0.2 + 0.7 * cid + 0.35 * F.fbm(P, 2.2, 3, seed=307), 0, 1)
    gem = F.ramp(plane_tone, [(0.0, "1f0106"), (0.4, "4a040e"), (0.7, "7c0916"), (0.92, "a81220"), (1.0, "c9232a")])
    # the molten veins, thin and branching, hottest near the points' roots
    lines = F.ridged(P + warp, 2.0, 3, 0.5, seed=308)
    wv = 0.009 + 0.01 * np.clip(F.fbm(P, 3.0, 2, seed=309) + 0.4, 0, 1)
    patches = F.sstep(0.0, 0.28, F.fbm(P, 1.7, 2, seed=312))     # veins only in places: the rest is clean stone
    vein = (1 - F.sstep(wv * 0.6, wv, lines)) * patches
    glow = (1 - F.sstep(wv, wv * 5.0, lines)) * 0.5 * patches
    hot = F.ramp(1 - np.clip(lines / wv, 0, 1), [(0.0, "c81e06"), (0.5, "ff6a12"), (1.0, "ffd76a")])
    gem = gem + np.array((0.3, 0.04, 0.0)) * glow[..., None]
    gem = F.mix(gem, hot, vein)
    height_gem = 0.018 * (cid - 0.5) * F.sstep(0.0, 0.07, wall) - 0.008 * vein
    # the crust: black, scaled, its plates curling at the broken edge
    f1, pl, pid = F.voronoi(P + warp, 6.0, seed=310, jitter=1.0, stretch=(1.0, 0.8, 1.0))
    grain = F.fbm(P, 12.0, 4, seed=311)
    crust = F.ramp(np.clip(0.3 + 0.5 * pid + 0.4 * grain, 0, 1), [(0.0, "070606"), (0.5, "151212"), (1.0, "2d2523")])
    gap = 1 - F.sstep(0.0, 0.05, pl)
    crust = F.mix(crust, F.ramp(np.clip(Vv / np.maximum(broken, 0.01), 0, 1), [(0.0, "230603"), (0.6, "6a1205"), (1.0, "e0420c")]), gap)
    height_crust = 0.065 + 0.034 * (pid - 0.5) + 0.012 * grain - 0.045 * gap
    # heat pooled round each point's root
    roots = np.zeros(Vv.shape)
    girth = 6.3 * np.sin(np.pi * np.clip(Vv, 0.03, 0.97))
    for s_, v_, length, radius, lean in MH_POINTS:
        dx = ((f.S - s_ + 0.5) % 1.0 - 0.5) * girth
        dy = (Vv - v_) * 4.2
        roots = np.maximum(roots, np.exp(-((np.hypot(dx, dy) / (radius * 1.9)) ** 2)))
    gem = F.mix(gem, F.ramp(roots, [(0.0, "9a0d1d"), (0.6, "ff4a12"), (1.0, "ffc24a")]), np.clip(roots * 1.2, 0, 1))
    col = F.mix(crust, gem, crystal)
    height = height_gem * crystal + height_crust * (1 - crystal) + 0.035 * edge_band * (1 - crystal)
    col = F.mix(col, np.array((0.95, 0.3, 0.05)), np.exp(-((Vv - broken) / 0.007) ** 2) * 0.8)
    rough = F.mix(0.75 + 0.1 * grain, 0.14 + 0.22 * vein, crystal)
    return f, np.clip(col, 0, 1), np.clip(rough, 0, 1), np.zeros(f.S.shape), height


def mh_material(name, dark, mid, light):
    """A crystal point: deep at its root, bright toward its tip, each face its own tone."""
    g = Hm._Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    tone = g.n("ShaderNodeTexNoise", **{"Scale": 37.0, "Detail": 0.0})
    g.link(geo.outputs["True Normal"], tone.inputs["Vector"])
    streak = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 5.0, "Roughness": 0.6})
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (5.0, 5.0, 0.6)
    g.link(geo.outputs["Position"], mp.inputs["Vector"])
    g.link(mp.outputs[0], streak.inputs["Vector"])
    v = g.math("ADD", g.math("MULTIPLY", tone.outputs["Fac"], 0.85), g.math("MULTIPLY", streak.outputs["Fac"], 0.4))
    col = g.ramp(g.math("SUBTRACT", v, 0.1), [(0.0, dark), (0.42, dark), (0.65, mid), (0.85, light), (1.0, light)])
    # paler toward the tips, deepest at the roots (world height), as a point fills with light
    z = g.sep(geo.outputs["Position"])[2]
    lift = g.math("MULTIPLY", g.math("SUBTRACT", z, 2.6, clamp=True), 0.42)
    col = g.mix(lift, col, (1.0, 0.18, 0.12))
    return g.finish(col, 0.08, 0.0)


def mh_points(coll):
    mat = mh_material("MH_Garnet", (0.14, 0.0, 0.012), (0.62, 0.004, 0.022), (1.0, 0.12, 0.07))
    hi = Hm.Hi()
    for k, (s_, v_, length, radius, lean) in enumerate(MH_POINTS):
        base = F.on(s_ % 1.0, min(v_, 0.998), 0.0)
        n = F.normal(s_ % 1.0, min(v_, 0.998))
        d = (n * (1 - lean) + V((0, 1, 0)) * lean + V((base.x, 0, base.z)).normalized() * 0.12 * lean).normalized() if v_ < 0.99 else V((0.04, 1, 0.02)).normalized()
        F.crystal(hi, base, d, length, radius, sides=6 if radius > 0.08 else 5, seed=320 + k, tip=0.28)
    o = hi.object("MH_Points", coll, [mat], smooth=False)
    F.fix_normals(o)
    Hm.apply_modifiers(o, [("BEVEL", {"width": 0.008, "segments": 2, "limit_method": "ANGLE", "angle_limit": math.radians(20)})])
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.0
    return o


def mh_veins(coll):
    """A few molten threads across the crimson, drawn up from the crust's edge to the points."""
    hi = Hm.Hi()
    routes = (((0.5, 0.4), (0.53, 0.47), (0.48, 0.54), (0.51, 0.62), (0.47, 0.7)), ((0.48, 0.54), (0.42, 0.56), (0.38, 0.53)), ((0.53, 0.47), (0.62, 0.52), (0.66, 0.6), (0.7, 0.68)),
              ((0.0, 0.42), (0.04, 0.5), (0.98, 0.56), (0.02, 0.66)), ((0.25, 0.4), (0.22, 0.52), (0.2, 0.68)), ((0.78, 0.38), (0.84, 0.44)), ((0.86, 0.5), (0.84, 0.6), (0.83, 0.7)))
    for r in routes:
        fine = W.catmull([(a, b, 0.0) for a, b in r], 8)
        pts = [(F.on(p[0] % 1.0, p[1], 0.002), F.normal(p[0] % 1.0, p[1])) for p in fine]
        F.prism(hi, pts, lambda t: 0.026 * math.sin(math.pi * (0.1 + 0.85 * t)) ** 0.7, height=lambda w: w * 0.3)
    return hi.object("MH_Veins", coll, [K.glow_material(MH_VEIN)], smooth=False, weld=0)


def magma_clay():
    coll = W.collection("MagmaHeartEggHi")
    shell = F.shell_mesh("MH_Shell", coll, 96, 64)
    p = mh_points(coll)
    v = mh_veins(coll)
    return {o.name: F.tris(o) for o in (shell, p, v)}


def magma_build():
    coll = W.collection("MagmaHeartEggHi")
    f, col, rough, metal, height = magma_paint()
    mat = F.shell_material("MH_Shell", col, rough, metal)
    p = mh_points(coll)
    v = mh_veins(coll)
    return F.assemble("MagmaHeartEgg", coll, mat, height, [p], {MH_VEIN: [v]}, budget=7000, shell_frac=0.66, low_nu=72, low_nv=48, hard=20)


# ---------- Phoenix Ash Egg ----------
PH_FLAME = "ff5a14"
PH_HOT = "ffa21e"
PH_AT = (0.5, 0.5)


def ph_flame_outline():
    """The flame on the breast as one closed outline in the plane: a central tongue and two side
    tongues curling away from it, rising from a point at the bottom."""
    centre = [(0.0, -0.36), (0.1, -0.28), (0.15, -0.15), (0.11, -0.02), (0.16, 0.04), (0.19, -0.04), (0.25, 0.05), (0.27, 0.19), (0.22, 0.3), (0.2, 0.2), (0.14, 0.12), (0.1, 0.2), (0.07, 0.32),
              (0.03, 0.45), (0.0, 0.58), (-0.03, 0.45), (-0.07, 0.32), (-0.1, 0.2), (-0.14, 0.12), (-0.2, 0.2), (-0.22, 0.3), (-0.27, 0.19), (-0.25, 0.05), (-0.19, -0.04), (-0.16, 0.04), (-0.11, -0.02), (-0.15, -0.15), (-0.1, -0.28)]
    return centre


def phoenix_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    # the scales: rows that get smaller toward the crown, each overlapping the row above it
    rows = 26.0
    t = (Vv ** 0.92) * rows
    row = np.floor(t)
    girth = np.maximum(np.sin(np.pi * np.clip(Vv, 0.02, 0.98)), 0.1)
    # scales per row: fewer near the poles, always a whole number so the row closes on itself
    count = np.maximum(np.round(30.0 * girth), 6.0)
    xs = S * count + 0.5 * (row % 2)
    cell = np.floor(xs)
    fx = xs - cell - 0.5                    # -0.5..0.5 across one scale
    fy = t - row                            # 0 at the scale's tip (below), 1 at its root
    # a pointed rounded tip: the scale's outline, with a ridge down its centre
    outline = np.abs(fx) * 2.0 - np.clip(fy * 1.6, 0, 1) ** 0.65
    body = 1 - F.sstep(-0.1, 0.02, outline)
    # height: rises toward its tip, so each lies over the row below
    h = (1 - fy) * 0.016 * body
    rib = 1 - F.sstep(0.0, 0.05, np.abs(fx))
    barb = 0.5 + 0.5 * np.sin((fy * 16.0 - np.abs(fx) * 26.0) * TAU * 0.5)
    h = h + 0.003 * rib * body + 0.0012 * barb * body
    height = h - 0.012 * (1 - body)
    # colour: crimson deep at the root of each scale, burning orange to pale gold toward its tip
    per = (np.sin((cell + row * 7.3) * 91.7) * 43758.5) % 1.0
    tipwards = np.clip((1 - fy) * 1.15 + (per - 0.5) * 0.25, 0, 1)
    col = F.ramp(tipwards, [(0.0, "3c0507"), (0.35, "7c0a0e"), (0.65, "bf1b10"), (0.88, "f0561a"), (1.0, "ffb54a")])
    col = col * (0.82 + 0.25 * rib[..., None])
    col = F.mix(np.array((0.05, 0.005, 0.005)), col, body)
    # ash: the lower scales burned darker, a soft smoke rising from the base
    ash = F.sstep(0.42, 0.05, Vv + F.fbm(P, 2.6, 3, seed=401) * 0.1)
    col = F.mix(col, col * np.array((0.3, 0.26, 0.26)), ash * 0.75)
    # the flame on the breast, raised in gold round a burning middle
    x, y, front = f.plane(*PH_AT)
    fl = ph_flame_outline()
    d, _ = F.seg_dist(x, y, fl, closed=True)
    # inside test: even-odd over the outline
    inside = np.zeros(x.shape, dtype=bool)
    pts = fl + fl[:1]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        crossing = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay + 1e-9) + ax)
        inside ^= crossing
    inside = inside & (front > 0.3)
    rim = (1 - F.sstep(0.012, 0.024, d)) * (front > 0.3)
    fill = inside * 1.0
    inner = F.ramp(np.clip((y + 0.36) / 0.9, 0, 1), [(0.0, "ffe89a"), (0.4, "ffae2e"), (0.8, "f05012"), (1.0, "9c1408")])
    col = F.mix(col, inner, fill)
    gold = F.mix(np.array((0.85, 0.58, 0.18)), np.array((1.0, 0.86, 0.44)), np.clip(0.5 + F.fbm(P, 20.0, 2, seed=402) * 0.7, 0, 1))
    col = F.mix(col, gold, rim)
    height = height * (1 - fill) * (1 - rim) + 0.012 * F.blur(fill, 2) + 0.024 * F.blur(rim, 1)
    rough = np.clip(0.34 - 0.08 * rib + 0.14 * ash + 0.0 * fill, 0.1, 1)
    metal = 0.85 * rim
    return f, np.clip(col, 0, 1), rough, metal, height


def ph_wrap(L, forward):
    """How much a feather must bend toward the egg to follow its curve for its length: a circle of
    the egg's radius falls away from its tangent by L^2 / 2R. `forward` says how much of the feather
    runs round the egg (those rising above the shoulder stay straighter)."""
    return -(L / (2 * F.R)) * 0.95 * forward


def ph_feathers(coll):
    feather = Hm.mat_feather("PH_Feather", base=(0.22, 0.004, 0.008), mid=(0.8, 0.022, 0.012), tip=(1.0, 0.2, 0.018))
    dark = Hm.mat_feather("PH_Covert", base=(0.12, 0.003, 0.006), mid=(0.42, 0.012, 0.012), tip=(0.95, 0.12, 0.016))
    wing, covert, crest = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        s0 = 0.5 + side * 0.34
        root = F.on(s0, 0.72)
        n = F.normal(s0, 0.72)
        toward = (F.on(0.5 + side * 0.29, 0.72) - root).normalized()
        up = n.cross(toward).normalized()
        if up.y < 0:
            up = -up
        # primaries: the long outer fan, wrapping round the egg with their tips lifting off it; the
        # uppermost rise above the shoulder and break the silhouette
        count = 12
        for k in range(count):
            t = k / (count - 1)
            a = math.radians(82 - 150 * t)
            L = 0.95 + 0.85 * math.sin(math.pi * (0.2 + 0.7 * t))
            forward = min(1.0, max(0.0, (math.radians(82) - a) / math.radians(42)))
            d = (toward * math.cos(a) + up * math.sin(a) + n * 0.12).normalized()
            b = root + d * 0.02 + n * (0.05 + 0.009 * k) + up * (0.15 - 0.42 * t)
            Hm.leaf(wing, b, d, n, L, 0.15 * (0.85 + 0.25 * math.sin(math.pi * t)), fold=0.16, curl=ph_wrap(L, forward) + 0.05, twist=-0.12 * side + 0.11 * ((k % 3) - 1), steps=14, across=4, shape=0.5)
        # secondaries: shorter, lying over the primaries' roots
        count = 9
        for k in range(count):
            t = k / (count - 1)
            a = math.radians(58 - 120 * t)
            L = 0.8 + 0.25 * math.sin(math.pi * t)
            forward = min(1.0, max(0.0, (math.radians(70) - a) / math.radians(40)))
            d = (toward * math.cos(a) + up * math.sin(a) + n * 0.1).normalized()
            b = root + d * 0.01 + n * (0.16 + 0.009 * k) + up * (0.12 - 0.3 * t)
            Hm.leaf(wing, b, d, n, L, 0.135, fold=0.14, curl=ph_wrap(L, forward) + 0.05, twist=-0.08 * side + 0.11 * ((k % 3) - 1), steps=11, across=4, shape=0.5)
        # coverts: a whole rosette of short feathers, overlapping all the way round the shoulder, so
        # the wing's root is feathered from behind as well as from in front
        for ring_, (count, reach, r0, phase) in enumerate(((13, 0.52, 0.2, 0.0), (9, 0.36, 0.27, 0.5), (5, 0.22, 0.32, 0.25))):
            for k in range(count):
                a = TAU * (k + phase) / count
                d = (toward * math.cos(a) + up * math.sin(a) + n * (0.12 + 0.1 * ring_)).normalized()
                b = root + d * 0.05 + n * (r0 + 0.008 * (k % 4))
                Hm.leaf(covert, b, d, n, reach, reach * 0.32, fold=0.12, curl=-0.14, twist=0.16 * ((k % 3) - 1), steps=8, across=4, shape=0.48)
    # the crest: a fan of plumes rising off the crown, broad enough to read from the front and
    # sweeping back at their tips
    for k, (x, L) in enumerate(((-0.42, 0.85), (-0.21, 1.2), (0.0, 1.45), (0.21, 1.2), (0.42, 0.85))):
        base = V((x * 0.22, F.H - 0.07, 0.0 + abs(x) * 0.02)) + V((0, 0, -0.004 * k))
        d = V((x * 0.95, 1.0, -0.2)).normalized()
        n = V((-x * 0.3, 0.2, 1.0))
        Hm.leaf(crest, base, d, n, L, 0.17 * (1.0 - abs(x) * 0.4), fold=0.2, curl=-0.3, twist=x * 0.6, steps=14, across=4, shape=0.56)
    for k, (x, L) in enumerate(((-0.3, 0.62), (0.0, 0.75), (0.3, 0.62))):
        base = V((x * 0.2, F.H - 0.03, 0.05))
        d = V((x * 1.0, 1.0, 0.1)).normalized()
        Hm.leaf(crest, base, d, (0, 0.1, 1.0), L, 0.11, fold=0.2, curl=-0.15, steps=10, across=4, shape=0.56)
    # the shoulders: a soft mound of down the feathers grow from, closing the gap to the shell
    mounds = []
    for side in (-1, 1):
        s0 = 0.5 + side * 0.34
        root, n = F.on(s0, 0.72), F.normal(s0, 0.72)
        mounds += [(root + n * 0.03, 0.22, (1.0, 1.0, 1.0))]
    g = Hm._Graph("PH_Down")
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 40.0, "Detail": 4.0})
    g.link(g.coords(), grain.inputs["Vector"])
    down = g.finish(g.ramp(grain.outputs["Fac"], [(0.35, (0.1, 0.004, 0.006)), (0.65, (0.34, 0.016, 0.012))]), 0.7, 0.0, g.bump(grain.outputs["Fac"], 0.5, 0.01))
    mound = F.lobes("PH_Shoulders", coll, down, mounds, voxel=0.03)
    mound["w"] = 0.35
    a = wing.object("PH_Wings", coll, [feather])
    Hm.solidify(a, 0.012)
    a["w"] = 1.5
    b = covert.object("PH_Coverts", coll, [dark])
    Hm.solidify(b, 0.012)
    b["w"] = 1.0
    c = crest.object("PH_Crest", coll, [feather])
    Hm.solidify(c, 0.012)
    c["w"] = 1.4
    return a, b, c, mound


def ph_flame_glow(coll):
    hi = Hm.Hi()
    c, n = F.on(*PH_AT), F.normal(*PH_AT)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()

    def lay(x, y, off):
        q = c + e1 * x + e2 * y
        ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * q.y / F.H))) / math.pi
        return F.on(ss, vv, off), F.normal(ss, vv)
    # the heart of the flame: a small tongue of fire inside the gold
    tongue = [(0.0, -0.22), (0.05, -0.16), (0.075, -0.05), (0.04, 0.07), (0.018, 0.2), (0.0, 0.32), (-0.018, 0.2), (-0.04, 0.07), (-0.075, -0.05), (-0.05, -0.16)]
    rim = [hi.v(lay(x, y, 0.016)[0]) for x, y in tongue]
    top = hi.v(lay(0, 0.0, 0.05)[0])
    for k in range(len(tongue)):
        hi.f([rim[k], rim[(k + 1) % len(tongue)], top], [(0, 0), (1, 0), (0, 1)])
    return F.fix_normals(hi.object("PH_Flame", coll, [K.glow_material(PH_HOT)], smooth=False, weld=0))


def phoenix_clay():
    coll = W.collection("PhoenixAshEggHi")
    shell = F.shell_mesh("PH_Shell", coll, 96, 64)
    a, b, c, m = ph_feathers(coll)
    g = ph_flame_glow(coll)
    return {o.name: F.tris(o) for o in (shell, a, b, c, m, g)}


def phoenix_build():
    coll = W.collection("PhoenixAshEggHi")
    f, col, rough, metal, height = phoenix_paint()
    mat = F.shell_material("PH_Scales", col, rough, metal)
    a, b, c, m = ph_feathers(coll)
    g = ph_flame_glow(coll)
    return F.assemble("PhoenixAshEgg", coll, mat, height, [a, b, c, m], {PH_HOT: [g]}, budget=10500, shell_frac=0.56, low_nu=56, low_nv=36, ao_floor=0.6)

"""The Murim Outfit (run inside Blender): a cultivator's robes made for the owner's avatar, worn
over it in game (src/server/OutfitService). An original design in the spirit of the owner's
reference: a white inner robe with a black standing collar and a white crossed collar (left over
right) embroidered in gold; a long open outer coat of gold silk deepening to dark brown at its
embroidered hem, with embroidered bands down its fronts and gold half-sleeves; wide white sleeves
with flared cuffs; a gold belt hung with a turquoise pendant, a pearl and a yellow tassel; loose dark
trousers; black boots with white soles and toe caps.

Built like the eggs: high-detail pieces with procedural shaders (fabric folds, brocade, embroidery)
baked onto one game mesh per piece (egg_bake.py). Each piece rides one R15 body part. The robe
skirt, the belt's tassel and the cuffs are skinned to small bone chains that the client sways
(src/client/OutfitSway.client.lua): the skirt's four panels follow the legs and trail as the
wearer moves.

Measures are the owner's avatar at rest (R15, blocky: height 0.9, width 0.81, depth 0.9), in
Roblox studs relative to the HumanoidRootPart, front toward -Z, measured in Play.

    import murim_outfit as O
    O.build()            # the high-detail pieces, in collection MurimOutfitHi
    O.export_all()       # bake every piece and write assets/outfits/MurimOutfit.fbx and the maps
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(W.REPO, "assets", "outfits")
NAME = "MurimOutfit"

# the owner's body at rest: centre and size of each part (root space)
BODY = {
    "Head": ((0, 1.443, 0), (1.191, 1.199, 1.191)),
    "UpperTorso": ((0, 0.204, 0), (1.615, 1.477, 0.907)),
    "LowerTorso": ((0, -0.717, 0), (1.622, 0.366, 0.907)),
    "LeftUpperArm": ((-1.215, 0.359, 0), (0.815, 1.081, 0.906)),
    "RightUpperArm": ((1.215, 0.359, 0), (0.815, 1.081, 0.906)),
    "LeftLowerArm": ((-1.215, -0.189, 0), (0.815, 0.973, 0.906)),
    "RightLowerArm": ((1.215, -0.189, 0), (0.815, 0.973, 0.906)),
    "LeftUpperLeg": ((-0.405, -1.296, 0), (0.81, 1.145, 0.897)),
    "RightUpperLeg": ((0.405, -1.296, 0), (0.81, 1.145, 0.897)),
    "LeftLowerLeg": ((-0.405, -2.028, 0), (0.81, 1.117, 0.897)),
    "RightLowerLeg": ((0.405, -2.028, 0), (0.81, 1.117, 0.897)),
    "LeftFoot": ((-0.405, -2.634, 0), (0.814, 0.275, 0.906)),
    "RightFoot": ((0.405, -2.634, 0), (0.814, 0.275, 0.906)),
}

WAIST = -0.55          # where the skirt hangs from (the belt covers the seam)
INNER_HEM = -2.12      # the white inner robe, to mid-shin
COAT_HEM = -2.46       # the gold coat, to just above the ankle
CHAIN = (WAIST, -1.15, -1.75)   # the skirt bones' heads


# ---------- shapes ----------
def se(t, a, b, p=4.0):
    """A rounded box (superellipse) of half-extents a (x) and b (z), at angle t from the front (-Z),
    and its outward normal."""
    s, c = math.sin(t), math.cos(t)
    x = math.copysign(abs(s) ** (2 / p), s) * a
    z = -math.copysign(abs(c) ** (2 / p), c) * b
    nx = math.copysign(abs(x / a) ** (p - 1), x) / a
    nz = math.copysign(abs(z / b) ** (p - 1), z) / b
    n = V((nx, 0, nz))
    return x, z, (n.normalized() if n.length > 1e-9 else V((0, 0, -1)))


def folds(t, v, seed, count, amp):
    """Soft vertical folds: deeper toward the hem (v 1), each fold its own width."""
    r = random.Random(seed)
    phases = [r.uniform(0, TAU) for _ in range(3)]
    k = count
    d = 0.55 * math.sin(k * t + phases[0]) + 0.3 * math.sin(k * 1.7 * t + phases[1]) + 0.15 * math.sin(k * 2.9 * t + phases[2])
    return amp(v) * d


def fine(levels, step=0.07):
    """Levels (y, a, b) interpolated every `step` studs, so folds have rows to show in."""
    out = [levels[0]]
    for (y0, a0, b0), (y1, a1, b1) in zip(levels, levels[1:]):
        n = max(1, int(abs(y1 - y0) / step))
        out += [(y0 + (y1 - y0) * k / n, a0 + (a1 - a0) * k / n, b0 + (b1 - b0) * k / n) for k in range(1, n + 1)]
    return out


def along_surface(t, a, b, p, toward):
    """The direction round a rounded box at angle t, toward larger (+1) or smaller (-1) angles."""
    x0, z0, _ = se(t, a, b, p)
    x1, z1, _ = se(t + toward * 0.01, a, b, p)
    return V((x1 - x0, 0, z1 - z0)).normalized()


def grid_faces(hi, rows, uv_rows, outward_fn, mat, closed=False):
    """Quads between rows of vertex indices (rows[j][i]); outward_fn(j, i) gives the side to face."""
    for j in range(len(rows) - 1):
        n = len(rows[j])
        for i in range(n if closed else n - 1):
            i2 = (i + 1) % n
            q = [rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]]
            uv = [uv_rows[j][i], uv_rows[j][i2 if i2 else n] if closed else uv_rows[j][i2],
                  uv_rows[j + 1][i2 if i2 else n] if closed else uv_rows[j + 1][i2], uv_rows[j + 1][i]]
            hi.facing(q, uv, tuple(outward_fn(j, i)), mat)


def tube_shell(hi, centre, levels, mat, n=48, p=4.0, seed=0, fold_count=0, fold_amp=None, cap_top=None, droop=None, shift=None, dome=None):
    """A closed rounded-box tube round a vertical axis through `centre` (x, z): levels are
    (y, a, b) from top to bottom. Optional folds; cap_top=(y, a, b) closes the top as a shoulder
    or yoke; droop(t) lowers the bottom ring (a hanging sleeve); shift(v) moves each level's
    centre by (dx, dz) (a cuff flaring away from the body); dome=height closes the top as a rounded
    dome (a sleeve's shoulder)."""
    cx, cz = centre
    rows, uvs = [], []
    total = len(levels) - 1
    for j, (y, a, b) in enumerate(levels):
        v = j / max(1, total)
        dx, dz = shift(v) if shift else (0.0, 0.0)
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, z, nrm = se(t, a, b, p)
            yy = y - (droop(t) * v if droop else 0.0)
            d = folds(t, v, seed, fold_count, fold_amp) if fold_count else 0.0
            pt = V((cx + dx + x, yy, cz + dz + z)) + nrm * d
            if i < n:
                row.append(hi.v(pt))
            uvrow.append((i / n * 3.0, j / max(1, total) * 2.0))
        rows.append(row)
        uvs.append(uvrow)

    def outward(j, i):
        t = TAU * (i + 0.5) / n
        return se(t, 1, 1, p)[2]
    grid_faces(hi, rows, uvs, outward, mat, closed=True)
    if dome:
        y0, a0, b0 = levels[0]
        prev, prev_uv = rows[0], uvs[0]
        steps = 5
        for k in range(1, steps):
            ph = (math.pi / 2) * k / steps
            a, b, y = a0 * math.cos(ph), b0 * math.cos(ph), y0 + dome * math.sin(ph)
            ring = [hi.v(V((cx + se(TAU * i / n, a, b, p)[0], y, cz + se(TAU * i / n, a, b, p)[1]))) for i in range(n)]
            ring_uv = [(i / n * 3.0, -0.15 * k) for i in range(n + 1)]
            grid_faces(hi, [ring, prev], [ring_uv, prev_uv], lambda j, i: (0, 1, 0), mat, closed=True)
            prev, prev_uv = ring, ring_uv
        top = hi.v(V((cx, y0 + dome, cz)))
        for i in range(n):
            hi.facing([prev[i], prev[(i + 1) % n], top], [(0, 0), (1, 0), (0.5, 1)], (0, 1, 0), mat)
    if cap_top:
        y, a, b = cap_top
        inner = [hi.v(V((cx + se(TAU * i / n, a, b, p)[0], y, cz + se(TAU * i / n, a, b, p)[1]))) for i in range(n)]
        uv_in = [(i / n * 3.0, -0.3) for i in range(n + 1)]
        grid_faces(hi, [inner, rows[0]], [uv_in, uvs[0]], lambda j, i: (0, 1, 0), mat, closed=True)
    return rows


def panel(hi, t0, t1, top, hem, a0, b0, a1, b1, mat, nu=22, nv=26, seed=0, fold_count=9, amp=0.06, p=4.0):
    """A skirt panel hanging from the waist between angles t0..t1 (radians from the front), its
    hem flaring out, soft folds deepening toward the hem. Returns its grid of points."""
    pts = []
    for j in range(nv + 1):
        v = j / nv
        f = v ** 1.15
        a, b = a0 + (a1 - a0) * f, b0 + (b1 - b0) * f
        row = []
        for i in range(nu + 1):
            u = i / nu
            t = t0 + (t1 - t0) * u
            x, z, nrm = se(t, a, b, p)
            y = top + (hem - top) * v + (0.035 * math.sin(t * 7 + seed) * v ** 3)
            d = folds(t, v, seed, fold_count, lambda vv: amp * (0.25 + 0.75 * vv))
            row.append(V((x, y, z)) + nrm * d)
        pts.append(row)
    rows = [[hi.v(pt) for pt in row] for row in pts]
    uvs = [[(i / nu * (t1 - t0) * 1.6, j / nv * 3.0) for i in range(nu + 1)] for j in range(nv + 1)]

    def outward(j, i):
        return se(t0 + (t1 - t0) * (i + 0.5) / nu, 1, 1, p)[2]
    grid_faces(hi, rows, uvs, outward, mat)
    return pts


def ribbon(hi, path, side_fn, width, lift, mat, out_fn):
    """A flat band along `path`: side_fn(k) the direction across it, out_fn(k) the side it faces.
    UVs: u across 0..1, v along in studs (embroidery repeats along it)."""
    left, right, uvl, uvr = [], [], [], []
    along = 0.0
    for k, p in enumerate(path):
        if k:
            along += (path[k] - path[k - 1]).length
        s = side_fn(k)
        o = out_fn(k)
        left.append(hi.v(p + o * lift))
        right.append(hi.v(p + s * width + o * lift))
        uvl.append((0.0, along * 2.2))
        uvr.append((1.0, along * 2.2))
    for k in range(len(path) - 1):
        hi.facing([left[k], right[k], right[k + 1], left[k + 1]], [uvl[k], uvr[k], uvr[k + 1], uvl[k + 1]], tuple(out_fn(k)), mat)


def sphere(hi, c, r, mat=0, nu=14, nv=8):
    rows = []
    for j in range(nv + 1):
        th = math.pi * j / nv
        rows.append([hi.v(V(c) + V((math.sin(th) * math.cos(TAU * i / nu), -math.cos(th), math.sin(th) * math.sin(TAU * i / nu))) * r)
                     for i in range(nu)])
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu
            mid = V((math.cos(TAU * (i + 0.5) / nu), 0, math.sin(TAU * (i + 0.5) / nu)))
            hi.facing([rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)],
                      tuple(mid + V((0, -math.cos(math.pi * (j + 0.5) / nv), 0))), mat)


# ---------- materials ----------
def mat_silk(name="OutfitSilkWhite", base=(0.86, 0.84, 0.8), deep=(0.5, 0.52, 0.6)):
    """White silk: warm white, its folds shading to a cool grey-blue, a faint tone-on-tone cloud
    damask woven through it, a soft sheen."""
    g = Hm._Graph(name)
    co = g.coords()
    dam = g.n("ShaderNodeTexVoronoi", **{"Scale": 9.0})
    g.link(co, dam.inputs["Vector"])
    motif = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", dam.outputs["Distance"], 0.32)), 0.035)
    col = g.mix(g.math("MULTIPLY", motif, 0.12), base, (0.74, 0.72, 0.7))
    a = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    a.inputs["Distance"].default_value = 0.12
    col = g.mix(g.math("POWER", g.math("SUBTRACT", 1.0, a.outputs["AO"], clamp=True), 0.8), col, deep)
    return g.finish(col, 0.42, 0.0, g.bump(motif, 0.05, 0.004))


def mat_brocade(name="OutfitGoldBrocade"):
    """Gold silk brocade: warm gold over the shoulders deepening through amber to dark brown at the
    hem (by height); small woven rosettes in a lighter, metallic gold scattered through it, a fine
    twill; folds darkened."""
    g = Hm._Graph(name)
    co = g.coords()
    z = g.sep(co)[2]           # Blender Z is Roblox Y; the ramp takes 0..1, so height is remapped into it
    rng = g.n("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = -2.5, 1.0
    g.link(z, rng.inputs["Value"])
    col = g.ramp(rng.outputs["Result"], [(0.0, (0.03, 0.016, 0.008)), (0.18, (0.12, 0.055, 0.016)), (0.38, (0.4, 0.21, 0.04)),
                                         (0.62, (0.7, 0.44, 0.09)), (1.0, (0.86, 0.6, 0.16))])
    vo = g.n("ShaderNodeTexVoronoi", **{"Scale": 11.0})
    g.link(co, vo.inputs["Vector"])
    ring = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", vo.outputs["Distance"], 0.24)), 0.035)
    dot = g.math("LESS_THAN", vo.outputs["Distance"], 0.06)
    pattern = g.math("MINIMUM", g.math("ADD", ring, dot), 1.0)
    twill = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL", **{"Scale": 90.0})
    g.link(co, twill.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", twill.outputs["Fac"], 0.08), col, (0.25, 0.14, 0.03))
    col = g.mix(g.math("MULTIPLY", pattern, 0.35), col, (1.0, 0.8, 0.36))
    col = g.ao(col, 0.1, 0.35)
    return g.finish(col, g.math("SUBTRACT", 0.4, g.math("MULTIPLY", pattern, 0.15)), g.math("ADD", 0.2, g.math("MULTIPLY", pattern, 0.35)),
                    g.bump(pattern, 0.1, 0.004))


def mat_trim(name="OutfitEmbroidery", ground=(0.3, 0.16, 0.03)):
    """An embroidered band (UV u across, v along): raised gold rosettes linked by a vine, between
    two gold border lines, on deep amber silk (or `ground`: white silk for the collar)."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    fv = g.math("SUBTRACT", g.math("FRACT", v), 0.5)
    du = g.math("SUBTRACT", u, 0.5)
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", fv, fv), g.math("MULTIPLY", du, du)))
    rosette = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", d, 0.22)), 0.06)
    heart = g.math("LESS_THAN", d, 0.08)
    vine = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", du, g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", v, 6.283)), 0.25))), 0.035)
    border = g.math("GREATER_THAN", g.math("ABSOLUTE", du), 0.42)
    gold = g.math("MINIMUM", g.math("ADD", g.math("ADD", rosette, heart), g.math("ADD", vine, border)), 1.0)
    col = g.mix(gold, ground, (1.0, 0.72, 0.24))
    col = g.ao(col, 0.05, 0.5)
    return g.finish(col, g.math("SUBTRACT", 0.55, g.math("MULTIPLY", gold, 0.3)), g.math("MULTIPLY", gold, 0.55), g.bump(gold, 0.35, 0.004))


def mat_cloth(name="OutfitDarkCloth", base=(0.028, 0.022, 0.02)):
    """Near-black cotton: a fine weave, folds a touch darker, worn ridges a touch lighter."""
    g = Hm._Graph(name)
    co = g.coords()
    weave = g.n("ShaderNodeTexNoise", **{"Scale": 60.0, "Detail": 2.0})
    g.link(co, weave.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", weave.outputs["Fac"], 0.5), base, tuple(c * 2.4 for c in base))
    col = g.ao(col, 0.1, 0.45)
    return g.finish(col, 0.78, 0.0, g.bump(weave.outputs["Fac"], 0.08, 0.003))


def mat_leather(name="OutfitLeather"):
    g = Hm._Graph(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 14.0, "Detail": 5.0, "Distortion": 0.6})
    g.link(co, n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.6), (0.016, 0.014, 0.014), (0.06, 0.05, 0.05))
    col = g.ao(col, 0.06, 0.5)
    return g.finish(col, g.math("ADD", 0.3, g.math("MULTIPLY", n.outputs["Fac"], 0.25)), 0.0, g.bump(n.outputs["Fac"], 0.2, 0.006))


def mat_flat(name, color, rough=0.6, metal=0.0):
    g = Hm._Graph(name)
    return g.finish(g.ao(g.mix(0.0, color, color), 0.05, 0.5), rough, metal)


def mat_thread(name="OutfitTassel", color=(0.95, 0.62, 0.06)):
    """Silk tassel threads (UV u across, v along): fine strands, darker between them."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    strand = g.math("SINE", g.math("MULTIPLY", u, 120.0))
    col = g.mix(g.math("MULTIPLY", g.math("ADD", strand, 1.0), 0.25), tuple(c * 0.55 for c in color), color)
    return g.finish(g.ao(col, 0.03, 0.6), 0.45, 0.0, g.bump(strand, 0.2, 0.002))


def mat_turquoise(name="OutfitTurquoise"):
    g = Hm._Graph(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 20.0, "Detail": 4.0, "Distortion": 1.2})
    g.link(co, n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.0, 0.32, 0.42)), (0.6, (0.06, 0.62, 0.72)), (0.8, (0.4, 0.85, 0.9))])
    return g.finish(g.ao(col, 0.03, 0.6), 0.15, 0.0)


def materials():
    return {
        "silk": mat_silk(), "brocade": mat_brocade(), "trim": mat_trim(), "trim_light": mat_trim("OutfitCollarEmbroidery", (0.8, 0.78, 0.74)), "cloth": mat_cloth(), "leather": mat_leather(),
        "sole": mat_flat("OutfitSole", (0.82, 0.8, 0.76)), "gold": Hm.mat_gold(), "black": mat_cloth("OutfitBlackSilk", (0.012, 0.012, 0.016)),
        "thread": mat_thread(), "jade": mat_turquoise(), "pearl": Hm.mat_pearl(),
    }


# ---------- pieces ----------
def fold_amp(base):
    return lambda v: base * (0.3 + 0.7 * v)


def torso(coll, M):
    silk, black, brocade, trim, collar = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    # the white inner robe round the torso, closing over the shoulders to the collar
    tube_shell(silk, (0, 0), fine([(0.93, 0.93, 0.545), (0.4, 0.94, 0.55), (-0.3, 0.94, 0.55), (-0.8, 0.935, 0.545)]), 0, n=64, p=5.0,
               seed=11, fold_count=6, fold_amp=fold_amp(0.012), cap_top=(0.97, 0.64, 0.6))
    # the black standing collar round the head's base
    tube_shell(black, (0, 0), [(1.06, 0.64, 0.62), (0.98, 0.655, 0.63), (0.9, 0.645, 0.62)], 0, n=40, p=3.0)

    def on_front(x, y, lift):
        a, b, p = 0.94, 0.55, 5.0
        z = -b * max(0.0, 1 - abs(x / a) ** p) ** (1 / p)
        return V((x, y, z - lift))
    # the crossed collar, left over right: the outer lapel from the left of the neck down to the
    # right waist, the under lapel from the right of the neck to the middle; embroidered bands
    for (x0, y0, x1, y1) in ((-0.32, 0.96, 0.66, -0.5), (0.32, 0.96, 0.02, 0.45)):
        path = [on_front(x0 + (x1 - x0) * k / 20, y0 + (y1 - y0) * k / 20, 0.014) for k in range(21)]
        across = (V((x1 - x0, y1 - y0, 0)).normalized()).cross(V((0, 0, -1)))
        if across.y > 0:
            across = -across
        ribbon(collar, path, lambda k: across, 0.26, 0.0, 0, lambda k: V((0, 0, -1)))
    back = [V((0.7 * math.sin(a), 0.96, 0.66 * math.cos(a))) for a in [math.radians(d) for d in range(-150, 151, 10)]]
    ribbon(collar, back, lambda k: V((0, 1, 0)), 0.1, 0.0, 0, lambda k: (back[k] * V((1, 0, 1))).normalized())
    # the gold coat over it, open at the front
    n, t0 = 64, math.radians(14)
    lv = fine([(0.99, 1.0, 0.61), (0.5, 1.0, 0.615), (0.0, 1.0, 0.615), (-0.45, 1.01, 0.62), (-0.85, 1.02, 0.63)])
    rows, uvs = [], []
    for j, (y, a, b) in enumerate(lv):
        row = []
        for i in range(n + 1):
            t = t0 + (TAU - 2 * t0) * i / n
            x, z, nrm = se(t, a, b, 4.5)
            row.append(brocade.v(V((x, y, z)) + nrm * folds(t, j / (len(lv) - 1), 21, 7, fold_amp(0.02))))
        rows.append(row)
        uvs.append([(i / n * 3, j / (len(lv) - 1) * 2) for i in range(n + 1)])
    grid_faces(brocade, rows, uvs, lambda j, i: se(t0 + (TAU - 2 * t0) * (i + 0.5) / n, 1, 1, 4.5)[2], 0)
    yoke = [brocade.v(V((se(t0 + (TAU - 2 * t0) * i / n, 0.7, 0.66, 3)[0], 1.02, se(t0 + (TAU - 2 * t0) * i / n, 0.7, 0.66, 3)[1])))
            for i in range(n + 1)]
    grid_faces(brocade, [yoke, rows[0]], [[(i / n * 3, -0.3) for i in range(n + 1)], uvs[0]], lambda j, i: (0, 1, 0), 0)
    # embroidered bands down both fronts, lying on the coat
    for sign in (-1, 1):
        t = sign * t0
        path, sides, outs = [], [], []
        for y, a, b in fine([(1.0, 1.0, 0.61), (-0.85, 1.02, 0.63)], 0.1):
            x, z, nrm = se(t, a, b, 4.5)
            path.append(V((x, y, z)))
            sides.append(along_surface(t, a, b, 4.5, sign))
            outs.append(nrm)
        ribbon(trim, path, lambda k: sides[k], 0.2, 0.014, 0, lambda k: outs[k])
    return Hm.solidify(silk.object("MO_TorsoSilk", coll, [M["silk"]]), 0.02), black.object("MO_TorsoCollar", coll, [M["black"]]), \
        Hm.solidify(brocade.object("MO_TorsoCoat", coll, [M["brocade"]]), 0.025), trim.object("MO_TorsoTrim", coll, [M["trim"]]), \
        collar.object("MO_TorsoLapels", coll, [M["trim_light"]])


# name: (t0, t1) for the inner robe, (t0, t1) for the coat, in degrees from the front. On a rounded
# box small angles near an axis open wide gaps (2 degrees is 0.38 studs at the back), so the back
# seam is closed and the inner robe's front split is 1 degree (about 0.26 studs)
SECTORS = {
    "FL": ((-89, -1), (-89, -16)), "FR": ((1, 89), (16, 89)),
    "BL": ((-180, -91), (-180, -91)), "BR": ((91, 180), (91, 180)),
}


def skirt(coll, M):
    silk, brocade, trim = Hm.Hi(), Hm.Hi(), Hm.Hi()
    r = math.radians
    for k, (name, ((i0, i1), (c0, c1))) in enumerate(SECTORS.items()):
        panel(silk, r(i0), r(i1), WAIST + 0.06, INNER_HEM, 0.97, 0.565, 1.16, 0.86, 0, nu=28, nv=34, seed=31 + k, fold_count=13, amp=0.085)
        pts = panel(brocade, r(c0), r(c1), WAIST, COAT_HEM, 1.02, 0.63, 1.36, 1.05, 0, nu=28, nv=38, seed=41 + k, fold_count=8, amp=0.085)
        # the embroidered hem, and the front edge on the front panels
        hem = pts[-1]
        up = [(pts[-3][i] - hem[i]).normalized() for i in range(len(hem))]
        ribbon(trim, hem, lambda q: up[q], 0.18, 0.016, 0, lambda q: se(r(c0) + (r(c1) - r(c0)) * q / (len(hem) - 1), 1, 1)[2])
        if name in ("FL", "FR"):
            col = len(pts[0]) - 1 if name == "FL" else 0
            nxt = col - 2 if name == "FL" else 2
            edge = [row[col] for row in pts]
            sides = [(row[nxt] - row[col]).normalized() for row in pts]
            out_t = r(c1) if name == "FL" else r(c0)
            ribbon(trim, edge, lambda q: sides[q], 0.2, 0.016, 0, lambda q: se(out_t, 1, 1)[2])
    return Hm.solidify(silk.object("MO_SkirtSilk", coll, [M["silk"]]), 0.02), Hm.solidify(brocade.object("MO_SkirtCoat", coll, [M["brocade"]]), 0.025), \
        trim.object("MO_SkirtTrim", coll, [M["trim"]])


PENDANT = V((-0.34, -0.66, -0.62))     # where the pendant's cord hangs from the belt
TASSEL_BOTTOM = -1.7


def inner_front(y):
    """How far forward the inner robe's front reaches at height y (its panels flare toward the hem)."""
    v = max(0.0, min(1.0, (WAIST + 0.06 - y) / (WAIST + 0.06 - INNER_HEM)))
    return 0.565 + (0.86 - 0.565) * v ** 1.15


def belt(coll, M):
    band, gold, jade, pearl, thread = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    tube_shell(band, (0, 0), [(-0.47, 0.955, 0.565), (-0.57, 0.96, 0.57), (-0.69, 0.955, 0.565)], 0, n=64, p=5.0)
    for k in range(7):                     # gold plaques along its front and sides
        t = math.radians(-75 + 25 * k)
        x, z, nrm = se(t, 0.97, 0.58, 5.0)
        c = V((x, -0.58, z)) + nrm * 0.012
        side = V((0, 1, 0)).cross(nrm).normalized()
        quad = [c + side * 0.1 + V((0, 0.07, 0)), c - side * 0.1 + V((0, 0.07, 0)), c - side * 0.1 - V((0, 0.07, 0)), c + side * 0.1 - V((0, 0.07, 0))]
        idx = [gold.v(q) for q in quad]
        gold.facing(idx, [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(nrm))
    # the pendant: a cord, a turquoise ring, a pearl, then the tassel
    cord = [PENDANT + V((0, -0.08 * k, -0.01 * k)) for k in range(5)]
    Hm.htube(gold, cord, lambda t: 0.012, sides=5, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    ring_c = PENDANT + V((0, -0.42, -0.05))
    ring = [ring_c + V((0.07 * math.sin(TAU * i / 20), 0.07 * math.cos(TAU * i / 20), 0)) for i in range(20)]
    Hm.htube(jade, ring + ring[:2], lambda t: 0.026, sides=8, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    sphere(pearl, PENDANT + V((0, -0.6, -0.05)), 0.055)
    cap = PENDANT + V((0, -0.68, -0.05))
    Hm.htube(gold, [cap + V((0, 0.02, 0)), cap + V((0, -0.06, 0))], lambda t: 0.04, sides=8, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    rnd = random.Random(77)
    for k in range(18):                    # the tassel's strands, fanning a little and resting on the robe
        a = TAU * k / 18
        start = cap + V((0.03 * math.cos(a), -0.06, 0.03 * math.sin(a)))
        y_end = TASSEL_BOTTOM + rnd.uniform(-0.04, 0.03)
        y_mid = (start.y + y_end) / 2
        mid = V((cap.x + 0.045 * math.cos(a), y_mid, -inner_front(y_mid) - 0.06 + 0.03 * math.sin(a)))
        end = V((cap.x + 0.07 * math.cos(a) + rnd.uniform(-0.01, 0.01), y_end, -inner_front(y_end) - 0.06 + 0.04 * math.sin(a)))
        Hm.htube(thread, [start, mid, end], lambda t: 0.011, sides=4, per=3, uv_scale=3.0, tip=True, wobble=0.0)
    return band.object("MO_BeltBand", coll, [M["gold"]]), gold.object("MO_BeltGold", coll, [M["gold"]]), \
        jade.object("MO_BeltJade", coll, [M["jade"]]), pearl.object("MO_BeltPearl", coll, [M["pearl"]]), thread.object("MO_BeltTassel", coll, [M["thread"]])


def sleeve(coll, M, side):
    """The upper sleeve (white, wide) under the coat's gold half-sleeve."""
    cx = side * 1.215
    white, coat, trim = Hm.Hi(), Hm.Hi(), Hm.Hi()
    # rounded (p 3) as far as the arm's corners allow (0.535 x 0.589 clears them by 10%)
    tube_shell(white, (cx, 0), fine([(0.9, 0.55, 0.6), (0.5, 0.6, 0.645), (0.0, 0.66, 0.7)]), 0, n=56, p=3.0, seed=51, fold_count=7,
               fold_amp=fold_amp(0.035), dome=0.12)
    tube_shell(coat, (cx, 0), fine([(0.92, 0.61, 0.655), (0.7, 0.64, 0.685), (0.42, 0.7, 0.745)]), 0, n=56, p=3.0, seed=52, fold_count=6,
               fold_amp=fold_amp(0.02), dome=0.16)
    hem = [V((cx + se(TAU * i / 56, 0.705, 0.75, 3.0)[0], 0.42, se(TAU * i / 56, 0.705, 0.75, 3.0)[1])) for i in range(57)]
    ribbon(trim, hem, lambda k: V((0, 1, 0)), 0.13, 0.014, 0, lambda k: se(TAU * k / 56, 1, 1, 3.0)[2])
    tag = "L" if side < 0 else "R"
    return Hm.solidify(white.object("MO_Sleeve" + tag + "Silk", coll, [M["silk"]]), 0.02), \
        Hm.solidify(coat.object("MO_Sleeve" + tag + "Coat", coll, [M["brocade"]]), 0.02), trim.object("MO_Sleeve" + tag + "Trim", coll, [M["trim"]])


CUFF_TOP, CUFF_MID = 0.25, -0.25


def cuff(coll, M, side):
    """The wide white cuff: a bell flaring out and down, less toward the body (it swings past the
    hips), its hem lower at the back, deep folds."""
    cx = side * 1.215
    white = Hm.Hi()
    levels = []
    for j in range(15):
        v = j / 14
        y = CUFF_TOP + (-0.78 - CUFF_TOP) * v
        levels.append((y, 0.55 + 0.24 * v ** 1.4, 0.6 + 0.25 * v ** 1.4))
    # it flares outward, front and back, but its body side stays by the arm: the centre moves out as
    # it widens; its hem hangs lower at the back
    tube_shell(white, (cx, 0.0), levels, 0, n=56, p=3.5, seed=61, fold_count=7, fold_amp=fold_amp(0.05),
               droop=lambda t: 0.14 * max(0.0, -math.cos(t)), shift=lambda v: (side * 0.24 * v ** 1.4, 0.05 * v))
    tag = "L" if side < 0 else "R"
    return (Hm.solidify(white.object("MO_Cuff" + tag, coll, [M["silk"]]), 0.02),)


def trousers(coll, M, side):
    cx = side * 0.405
    cloth = Hm.Hi()
    tube_shell(cloth, (cx, 0), fine([(-0.55, 0.5, 0.55), (-0.95, 0.53, 0.58), (-1.45, 0.56, 0.61), (-1.85, 0.53, 0.58), (-1.98, 0.5, 0.55)]), 0,
               n=48, p=4.0, seed=71 + side, fold_count=6, fold_amp=fold_amp(0.03))
    tag = "L" if side < 0 else "R"
    return (Hm.solidify(cloth.object("MO_Trouser" + tag, coll, [M["cloth"]]), 0.02),)


def boot(coll, M, side):
    cx = side * 0.405
    leather, cloth = Hm.Hi(), Hm.Hi()
    # the trousers bunched over the boot's top, then the shaft down to the ankle
    tube_shell(cloth, (cx, 0), fine([(-1.45, 0.53, 0.58), (-1.6, 0.56, 0.61), (-1.72, 0.53, 0.58)], 0.04), 0, n=48, p=4.0, seed=81, fold_count=7,
               fold_amp=lambda v: 0.03)
    tube_shell(leather, (cx, 0), fine([(-1.62, 0.5, 0.545), (-1.7, 0.48, 0.525), (-2.1, 0.47, 0.515), (-2.5, 0.47, 0.515), (-2.56, 0.47, 0.515)], 0.1), 0,
               n=48, p=6.0)
    tag = "L" if side < 0 else "R"
    return Hm.solidify(cloth.object("MO_BootCloth" + tag, coll, [M["cloth"]]), 0.02), leather.object("MO_Boot" + tag, coll, [M["leather"]])


def shoe(coll, M, side):
    cx = side * 0.405
    leather, sole = Hm.Hi(), Hm.Hi()
    # the foot of the boot: a rounded body over the foot, the toe reaching forward and turning up a little
    n = 40
    levels = [(-2.48, 0.48, 0.53, 0.0), (-2.6, 0.49, 0.55, -0.03), (-2.72, 0.49, 0.59, -0.06)]
    rows = []
    for (y, a, b, dz) in levels:
        row = []
        for i in range(n):
            t = TAU * i / n
            x, z, nrm = se(t, a, b, 5.0)
            front = max(0.0, -math.cos(t))
            row.append(leather.v(V((cx + x, y, z + dz - 0.12 * front ** 3))))
        rows.append(row)
    uvs = [[(i / n * 2, j * 0.5) for i in range(n + 1)] for j in range(len(levels))]
    grid_faces(leather, rows, uvs, lambda j, i: se(TAU * (i + 0.5) / n, 1, 1, 5.0)[2], 0, closed=True)
    # the white sole and toe cap
    ring = []
    for i in range(n):
        t = TAU * i / n
        x, z, nrm = se(t, 0.51, 0.63, 5.0)
        front = max(0.0, -math.cos(t))
        ring.append((cx + x, z - 0.06 - 0.12 * front ** 3, front))
    top = [sole.v(V((x, -2.71 + 0.06 * f ** 4, z))) for x, z, f in ring]
    bottom = [sole.v(V((x, -2.79 + 0.05 * f ** 4, z))) for x, z, f in ring]
    grid_faces(sole, [top, bottom], [[(i / n * 2, 0) for i in range(n + 1)], [(i / n * 2, 0.2) for i in range(n + 1)]],
               lambda j, i: se(TAU * (i + 0.5) / n, 1, 1, 3.0)[2], 0, closed=True)
    cb = sole.v(V((cx, -2.79, -0.06)))
    for i in range(n):
        sole.facing([bottom[i], bottom[(i + 1) % n], cb], [(0, 0), (1, 0), (0.5, 1)], (0, -1, 0))
    # toe cap: the front of the body's lowest ring wrapped in white
    cap_rows = []
    for (y, a, b, dz) in ((-2.58, 0.495, 0.555, -0.03), (-2.73, 0.5, 0.595, -0.06)):
        row = []
        for i in range(-8, 9):
            t = TAU * i / n
            x, z, nrm = se(t, a, b, 5.0)
            front = max(0.0, -math.cos(t))
            row.append(sole.v(V((cx + x, y, z + dz - 0.12 * front ** 3 - 0.004))))
        cap_rows.append(row)
    grid_faces(sole, cap_rows, [[(i / 16, j) for i in range(17)] for j in range(2)], lambda j, i: (0, 0, -1), 0)
    tag = "L" if side < 0 else "R"
    return leather.object("MO_Shoe" + tag, coll, [M["leather"]]), sole.object("MO_Sole" + tag, coll, [M["sole"]])


# piece name: (builder, body part, triangle budget, skinned)
def pieces():
    out = {
        "Torso": (torso, "UpperTorso", 9000, False),
        "Skirt": (skirt, "LowerTorso", 12000, True),
        "Belt": (belt, "LowerTorso", 5000, True),
    }
    for side, tag in ((-1, "Left"), (1, "Right")):
        out[tag + "Sleeve"] = ((lambda s: lambda c, M: sleeve(c, M, s))(side), tag + "UpperArm", 4500, False)
        out[tag + "Cuff"] = ((lambda s: lambda c, M: cuff(c, M, s))(side), tag + "LowerArm", 3500, True)
        out[tag + "Trouser"] = ((lambda s: lambda c, M: trousers(c, M, s))(side), tag + "UpperLeg", 2500, False)
        out[tag + "Boot"] = ((lambda s: lambda c, M: boot(c, M, s))(side), tag + "LowerLeg", 2500, False)
        out[tag + "Shoe"] = ((lambda s: lambda c, M: shoe(c, M, s))(side), tag + "Foot", 2000, False)
    return out


def build(only=None):
    M = materials()
    root = W.collection(NAME + "Hi")
    out = {}
    for name, (fn, part, budget, skinned) in pieces().items():
        if only and name not in only:
            continue
        coll = W.collection(NAME + "_" + name, root)
        W.clear_collection(coll)
        objs = [o for o in fn(coll, M)]
        for o in objs:
            if o.name.endswith(("Silk", "Coat")) or o.name.startswith(("MO_Cuff", "MO_Trouser", "MO_BootCloth")):
                o["sheet"] = True
        out[name] = (objs, coll, part, budget, skinned)
    return out


# ---------- skinning ----------
def _sector(x, z):
    return ("F" if z < 0 else "B") + ("L" if x < 0 else "R")


def bones_for(name):
    """[(bone, parent, head (root space), tail)] for a skinned piece."""
    if name == "Skirt":
        out = [("SkirtRoot", None, V((0, WAIST + 0.05, 0)), V((0, WAIST - 0.1, 0)))]
        for sec, ((i0, i1), (c0, c1)) in SECTORS.items():
            t = math.radians((c0 + c1) / 2)
            prev = "SkirtRoot"
            for k, y in enumerate(CHAIN):
                nxt = CHAIN[k + 1] if k + 1 < len(CHAIN) else COAT_HEM
                f0, f1 = (WAIST - y) / (WAIST - COAT_HEM), (WAIST - nxt) / (WAIST - COAT_HEM)
                x0, z0, _ = se(t, 1.02 + 0.34 * f0, 0.63 + 0.42 * f0)
                x1, z1, _ = se(t, 1.02 + 0.34 * f1, 0.63 + 0.42 * f1)
                bone = "Skirt%s%d" % (sec, k + 1)
                out.append((bone, prev, V((x0, y, z0)), V((x1, nxt, z1))))
                prev = bone
        return out
    if name == "Belt":
        top = PENDANT + V((0, -0.68, -0.05))
        mid = V((top.x, top.y - 0.25, -inner_front(top.y - 0.25) - 0.06))
        out = [("BeltRoot", None, V((0, -0.58, 0)), V((0, -0.7, 0))),
               ("Tassel1", "BeltRoot", PENDANT, top), ("Tassel2", "Tassel1", top, mid),
               ("Tassel3", "Tassel2", mid, V((top.x, TASSEL_BOTTOM, -inner_front(TASSEL_BOTTOM) - 0.06)))]
        return out
    side = -1 if name.startswith("Left") else 1
    cx = side * 1.215
    return [(name + "Root", None, V((cx, CUFF_TOP, 0)), V((cx, CUFF_MID, 0))),
            (name + "Hem", name + "Root", V((cx, CUFF_MID, 0)), V((cx, -0.8, 0)))]


def weights(name, p):
    """{bone: weight} for a game-mesh vertex at root-space point p."""
    if name == "Skirt":
        if p.y > WAIST:
            return {"SkirtRoot": 1.0}
        sec = _sector(p.x, p.z)
        heads = list(CHAIN) + [COAT_HEM]
        for k in range(len(CHAIN)):
            if heads[k] >= p.y >= heads[k + 1]:
                f = (heads[k] - p.y) / (heads[k] - heads[k + 1])
                if k + 1 < len(CHAIN) and f > 0.6:          # blend into the next bone over the last 40%
                    w = (f - 0.6) / 0.4
                    return {"Skirt%s%d" % (sec, k + 1): 1 - w, "Skirt%s%d" % (sec, k + 2): w}
                return {"Skirt%s%d" % (sec, k + 1): 1.0}
        return {"Skirt%s%d" % (sec, len(CHAIN)): 1.0}
    if name == "Belt":
        # the whole pendant swings from where its cord leaves the belt; the band stays put
        if p.y > PENDANT.y - 0.02 or math.hypot(p.x - PENDANT.x, p.z - PENDANT.z) > 0.3:
            return {"BeltRoot": 1.0}
        cap_y, mid_y = PENDANT.y - 0.68, PENDANT.y - 0.68 - 0.25
        if p.y > cap_y:
            return {"Tassel1": 1.0}
        if p.y > mid_y:
            f = (cap_y - p.y) / (cap_y - mid_y)
            return {"Tassel1": 1 - f, "Tassel2": f}
        f = min(1.0, (mid_y - p.y) / (mid_y - TASSEL_BOTTOM))
        return {"Tassel2": 1 - f, "Tassel3": f}
    f = max(0.0, min(1.0, (CUFF_TOP - p.y) / (CUFF_TOP + 0.8)))
    root, hem = name + "Root", name + "Hem"
    return {root: 1.0} if f < 0.4 else {root: 1 - (f - 0.4) / 0.6, hem: (f - 0.4) / 0.6}


def rig(name, low, coll):
    """An armature for a skinned piece, the game mesh parented to it with weights."""
    arm_data = bpy.data.armatures.new(name + "_Rig")
    arm = bpy.data.objects.new(name + "_Rig", arm_data)
    coll.objects.link(arm)
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    view_layer.objects.active = arm
    with B._ui_override(arm):
        bpy.ops.object.mode_set(mode="EDIT")
        made = {}
        for bone, parent, head, tail in bones_for(name):
            eb = arm_data.edit_bones.new(bone)
            eb.head, eb.tail = W.rb(*head), W.rb(*tail)
            if parent:
                eb.parent = made[parent]
            made[bone] = eb
        bpy.ops.object.mode_set(mode="OBJECT")
    for bone, *_ in bones_for(name):
        low.vertex_groups.new(name=bone)
    for v in low.data.vertices:
        w = low.matrix_world @ v.co
        p = V(K.rb_inv(*w))
        for bone, wt in weights(name, p).items():
            if wt > 1e-4:
                low.vertex_groups[bone].add([v.index], wt, "REPLACE")
    low.parent = arm
    md = low.modifiers.new("Armature", "ARMATURE")
    md.object = arm
    return arm


# ---------- export ----------
def export_all(only=None, report_path=None):
    """Bakes each piece's game mesh and writes assets/outfits/MurimOutfit.fbx (all pieces, skinned
    ones with their rigs) plus outfit_pieces.json (each piece's body part and authored centre)."""
    report = {}
    exported = []
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (hi, coll, part, budget, skinned) in build(only).items():
        piece_id = NAME + "_" + name
        old = bpy.data.objects.get(piece_id)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        # cloth is all thin sheets: decimate them enough to meet the piece's budget
        total = sum(B.tris(o) for o in hi)
        low = B.make_low(piece_id, hi, coll, budget, sheet_ratio=max(0.15, min(0.55, budget / max(1, total))))
        low.name = piece_id
        old_dir = K.EGG_DIR
        B.EGG_DIR = OUT_DIR
        try:
            B.bake(piece_id, hi, low, size=1024, small=512)
        finally:
            B.EGG_DIR = old_dir
        pts = [V(K.rb_inv(*(low.matrix_world @ v.co))) for v in low.data.vertices]
        lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi_ = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        objs = [low]
        if skinned:
            objs.append(rig(name, low, coll))
        exported += objs
        report[name] = {"Part": part, "Centre": [round(c, 4) for c in (lo + hi_) / 2], "Tris": B.tris(low), "Skinned": skinned}
    return report, exported


def write_fbx(objects):
    path = os.path.join(OUT_DIR, NAME + ".fbx")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE",
                             add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y",
                             secondary_bone_axis="X")
    return path


def write_report(report):
    with open(os.path.join(OUT_DIR, NAME + "_pieces.json"), "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)

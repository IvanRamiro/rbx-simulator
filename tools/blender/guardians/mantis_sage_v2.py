"""The Bamboo Mantis Sage, rebuilt on a real skeleton (the owner, 2026-11-05: "the mantis is okay but the hands or claw of mantis is kinda weird",
"please put rig, skeleton and more weight paint", "Make a realistic animations"). The same hermit sage become a mantis of living jade bamboo, with a
leaf robe, a mala, long brows and a leaf beard. It holds no egg: no guardian does, its three stands are behind it.

What changes is the anatomy. Each foreleg is what a real mantis has: a long coxa hanging from the prothorax, a thick spined femur, a tibia blade with a
hook that shuts against the femur like a jackknife, and a small tarsus at its end. Each walking leg is a femur rising from the thorax, a long tibia and
a tarsus lying on the ground. Bamboo doesn't bend, so limbs are rigid culms that turn at ball joints, as an insect's plates do; the abdomen and the
long prothorax flex, painted over several bones.

Authored in Roblox studs: standing, facing -Z, its feet on the ground at y = 0, its origin under the thorax, its left toward -X.
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

import egg_hi as Hm
import egg_kit as K
import guardian_kit as G
import pangu_v2 as P
import tiangou_v2 as T

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "MantisSage"
RIG = "MantisSageRig"
COLLECTION = "MantisSageV2"
OUT = G.OUT_DIR
PREFIX = "MantisSageV2_"
PUPIL_HEX, EDGE_HEX = "ff9000", "00c86e"
NODE = 2.6               # studs between bamboo nodes, on every culm (the bamboo shader draws them)
cone = G.cone


# ---------- materials and shapes: what the bamboo is made of ----------
def mat_bamboo(name="MantisBamboo", base=(0.08, 0.27, 0.09), light=(0.4, 0.58, 0.18), aged=(0.62, 0.55, 0.24)):
    """Living jade bamboo: fine fibres running along the culm (UV v, in studs), broad paler and
    darker streaks, patches aged toward straw, and at every node (every NODE studs) the pale waxy
    ring of bamboo over a dark seam."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    fibres_at = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, 40.0), fibres_at.inputs["X"])
    g.link(g.math("MULTIPLY", v, 0.5), fibres_at.inputs["Y"])
    fibres = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 6.0, "Roughness": 0.6})
    g.link(fibres_at.outputs[0], fibres.inputs["Vector"])
    co = g.coords()
    broad = g.n("ShaderNodeTexNoise", **{"Scale": 0.22, "Detail": 3.0})
    g.link(co, broad.inputs["Vector"])
    col = g.ramp(broad.outputs["Fac"], [(0.3, base), (0.7, light)])
    col = g.mix(g.math("MULTIPLY", fibres.outputs["Fac"], 0.35), col, tuple(c * 0.7 for c in base))
    patch = g.n("ShaderNodeTexNoise", **{"Scale": 0.45, "Detail": 4.0})
    g.link(co, patch.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", patch.outputs["Fac"], 0.58, clamp=True), 2.6), col, aged)
    # the nodes: distance (studs) to the nearest node along the culm
    f = g.math("FRACT", g.math("DIVIDE", v, NODE))
    d = g.math("MULTIPLY", g.math("MINIMUM", f, g.math("SUBTRACT", 1.0, f)), NODE)
    ring = g.math("SUBTRACT", 1.0, g.math("DIVIDE", d, 0.3), clamp=True)
    col = g.mix(g.math("MULTIPLY", ring, 0.55), col, (0.7, 0.76, 0.52))
    seam = g.math("LESS_THAN", d, 0.05)
    col = g.mix(g.math("MULTIPLY", seam, 0.7), col, tuple(c * 0.35 for c in base))
    col = g.ao(col, 0.15, 0.4)
    height = g.math("ADD", g.math("MULTIPLY", fibres.outputs["Fac"], 0.6), g.math("MULTIPLY", ring, 0.8))
    return g.finish(col, 0.38, 0.0, g.bump(height, 0.3, 0.02))


def mat_bamboo_leaf(name="MantisLeaf", stem=(0.05, 0.2, 0.07), mid=(0.14, 0.42, 0.13), tip=(0.3, 0.55, 0.18)):
    """A bamboo leaf: parallel veins along it (UV u across, v along), a pale midrib, deep green at
    the stem to fresher green, the tip and rim touched with straw."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, stem), (0.5, mid), (0.88, tip), (1.0, (0.55, 0.52, 0.2))])
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    midrib = g.math("LESS_THAN", du, 0.03)
    veins = g.math("LESS_THAN", g.math("FRACT", g.math("MULTIPLY", u, 16.0)), 0.12)
    col = g.mix(g.math("MAXIMUM", g.math("MULTIPLY", midrib, 0.65), g.math("MULTIPLY", veins, 0.22)), col, (0.45, 0.68, 0.3))
    rim = g.math("GREATER_THAN", du, 0.44)
    col = g.mix(g.math("MULTIPLY", rim, 0.4), col, (0.5, 0.48, 0.2))
    col = g.ao(col, 0.08, 0.45)
    nrm = g.bump(g.math("SUBTRACT", 1.0, g.math("MAXIMUM", midrib, g.math("MULTIPLY", veins, 0.5))), 0.25, 0.008)
    return g.finish(col, 0.45, 0.0, nrm)


def mat_eye(name="MantisEye"):
    """A compound eye: a dome of hexagonal-ish facets (Voronoi), each its own jade with a golden
    sheen toward the top, dark seams between them, glossy."""
    g = Hm._Graph(name)
    co = g.coords()
    cells = g.n("ShaderNodeTexVoronoi", **{"Scale": 9.0})
    g.link(co, cells.inputs["Vector"])
    tone = g.ramp(cells.outputs["Color"], [(0.0, (0.02, 0.16, 0.08)), (0.5, (0.06, 0.34, 0.16)), (1.0, (0.4, 0.42, 0.1))])
    edge = g.n("ShaderNodeTexVoronoi", **{"Scale": 9.0, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, edge.inputs["Vector"])
    seam = g.math("LESS_THAN", edge.outputs["Distance"], 0.06)
    col = g.mix(g.math("MULTIPLY", seam, 0.8), tone, (0.01, 0.05, 0.02))
    up = g.sep(co)[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", up, 0.2, clamp=True), 0.15), col, (0.75, 0.62, 0.16))
    nrm = g.bump(edge.outputs["Distance"], 0.45, 0.02)
    return g.finish(col, 0.12, 0.0, nrm)


def resample(pts, step=0.22):
    """Points along a smooth curve through `pts`, about `step` studs apart, ends included."""
    dense = [V(p) for p in W.catmull([tuple(p) for p in pts], 16)]
    at = [0.0]
    for a, b in zip(dense, dense[1:]):
        at.append(at[-1] + (b - a).length)
    count = max(2, round(at[-1] / step) + 1)
    out, j = [], 0
    for i in range(count):
        s = at[-1] * i / (count - 1)
        while j < len(dense) - 2 and at[j + 1] < s:
            j += 1
        span = at[j + 1] - at[j]
        out.append(dense[j].lerp(dense[j + 1], 0 if span <= 0 else (s - at[j]) / span))
    return out


def culm(hi, pts, r0, r1, sides=14, swell=None, mat=0, offset=0.0):
    """A bamboo culm through `pts`, its radius r0 to r1 (or swell(t) scaling it), pinched just
    before each node and ringed at it. UV v runs along it in studs, so the shader's nodes sit on
    the geometry's."""
    curve = resample(pts)
    length = sum((b - a).length for a, b in zip(curve, curve[1:]))

    def radius(t):
        s = t * length + offset
        f = (s / NODE) % 1.0
        d = min(f, 1 - f) * NODE
        base = (r0 + (r1 - r0) * t) * (swell(t) if swell else 1.0)
        return base * (1 + 0.1 * math.exp(-(d / 0.22) ** 2) - 0.035 * math.exp(-(d / 0.7) ** 2))

    Hm.htube(hi, curve, radius, sides=sides, per=1, mat=mat, uv_scale=1.0, tip=False, wobble=0.0)
    return curve


def cap(hi, centre, r, mat=0):
    G.sphere(hi, centre, r, nu=12, nv=8, mat=mat)


def leaf(hi, base, direction, normal, length, width, curl=0.0, twist=0.0, fold=0.18, shape=0.9):
    Hm.leaf(hi, base, direction, normal, length, width, mat=0, fold=fold, curl=curl, twist=twist, steps=14, across=4, shape=shape)


def sheet(hi, name, coll, mat, thickness=0.08):
    o = hi.object(name, coll, [mat])
    Hm.solidify(o, thickness)
    o["sheet"] = True
    return o


def mat_carved_jade(name, deep=(0.015, 0.2, 0.13), light=(0.13, 0.52, 0.36), vein=(0.42, 0.78, 0.58), rough=0.3):
    """Carved jade with real depth: deep green in the hollows, paler on what stands out, clouded and veined, so it never reads as flat paint."""
    g = Hm._Graph(name)
    co = g.coords()
    cloud = g.n("ShaderNodeTexNoise", **{"Scale": 0.55, "Detail": 5.0, "Roughness": 0.55})
    g.link(co, cloud.inputs["Vector"])
    col = g.ramp(cloud.outputs["Fac"], [(0.3, deep), (0.72, light)])
    marble = g.n("ShaderNodeTexNoise", **{"Scale": 0.9, "Detail": 8.0, "Roughness": 0.6, "Distortion": 1.8})
    g.link(co, marble.inputs["Vector"])
    veins = g.ramp(marble.outputs["Fac"], [(0.0, (0, 0, 0)), (0.482, (0, 0, 0)), (0.5, (1, 1, 1)), (0.518, (0, 0, 0)), (1.0, (0, 0, 0))])
    col = g.mix(g.math("MULTIPLY", g.bw(veins), 0.42), col, vein)
    col = g.ao(col, 0.45, 0.28)
    return g.finish(col, rough, 0.0, g.bump(marble.outputs["Fac"], 0.1, 0.02))


def materials():
    return {
        "bamboo": mat_bamboo(), "dark": mat_bamboo("MantisV2Dark", (0.13, 0.11, 0.04), (0.3, 0.24, 0.08), (0.42, 0.33, 0.13)),
        "leaf": mat_bamboo_leaf(), "robe": mat_bamboo_leaf("MantisV2Robe", (0.02, 0.1, 0.05), (0.05, 0.25, 0.1), (0.12, 0.38, 0.14)),
        "brow": mat_bamboo_leaf("MantisV2Brow", (0.3, 0.36, 0.2), (0.55, 0.58, 0.36), (0.78, 0.76, 0.56)), "eye": mat_eye(),
        "face": mat_carved_jade("MantisV2Face"), "blade": mat_carved_jade("MantisV2Blade", (0.008, 0.13, 0.09), (0.07, 0.38, 0.27), (0.35, 0.72, 0.54), 0.22),
        "claw": T.mat_plain("MantisV2Claw", (0.035, 0.03, 0.02), 0.32), "jade": Hm.mat_jade("MantisV2Jade"), "gold": Hm.mat_gold("MantisV2Gold"),
    }


# ---------- the skeleton: (parent, head, tail) ----------
_B = {
    "Root": (None, (0, 0, 0), (0, 2, 0)),
    "Hips": ("Root", (0, 13.3, 3.2), (0, 12.7, 6.4)),
    "Abd1": ("Hips", (0, 12.8, 6.0), (0, 12.7, 11.0)),
    "Abd2": ("Abd1", (0, 12.7, 11.0), (0, 11.9, 16.0)),
    "Abd3": ("Abd2", (0, 11.9, 16.0), (0, 10.4, 20.6)),
    "Abd4": ("Abd3", (0, 10.4, 20.6), (0, 8.4, 24.6)),
    "Pro1": ("Hips", (0, 13.8, 0.8), (0, 19.2, -2.4)),
    "Pro2": ("Pro1", (0, 19.2, -2.4), (0, 26.4, -6.5)),
    "Tassel": ("Pro2", (0, 17.4, -5.6), (0, 14.9, -5.9)),
    "Head": ("Pro2", (0, 26.4, -6.5), (0, 29.8, -8.2)),
    "Beard1": ("Head", (0, 25.0, -9.3), (0, 22.6, -9.6)),
    "Beard2": ("Beard1", (0, 22.6, -9.6), (0, 20.2, -9.4)),
    "RobeMid1": ("Hips", (0, 15.4, 2.2), (0, 15.3, 12.6)),
    "RobeMid2": ("RobeMid1", (0, 15.3, 12.6), (0, 13.6, 23.2)),
}


def _side(sign, tag):
    x = lambda v: v * sign
    b = {}
    # the foreleg, in the plane x = 2.3: a coxa hanging down and forward, the femur rising from it, the tibia reaching forward with its edge down
    S = V((x(2.3), 23.0, -4.6))
    Tr = S + V((0, -0.85, -0.527)).normalized() * 6.5
    Kn = Tr + V((0, 0.8, -0.6)) * 8.5
    K2 = Kn + V((0, -0.6, -0.8)) * 1.35          # the tibia hangs from the femur's underside, so it can shut against it
    Wr = K2 + V((0, 0.05, -1)).normalized() * 8.0
    Tp = Wr + V((0, 0.5, -3.0))
    b[tag + "Coxa"] = ("Pro2", tuple(S), tuple(Tr))
    b[tag + "Femur"] = (tag + "Coxa", tuple(Tr), tuple(Kn))
    b[tag + "Tibia"] = (tag + "Femur", tuple(K2), tuple(Wr))
    b[tag + "Tarsus"] = (tag + "Tibia", tuple(Wr + V((0, -0.12, 0))), tuple(Tp))
    b["Mid" + tag + "Femur"] = ("Hips", (x(2.0), 12.6, 1.8), (x(9.5), 16.2, -1.6))
    b["Mid" + tag + "Tibia"] = ("Mid" + tag + "Femur", (x(9.5), 16.2, -1.6), (x(12.4), 0.9, -5.2))
    b["Mid" + tag + "Tarsus"] = ("Mid" + tag + "Tibia", (x(12.4), 0.9, -5.2), (x(14.2), 0.4, -7.7))
    b["Hind" + tag + "Femur"] = ("Hips", (x(2.0), 12.3, 5.6), (x(10.6), 15.8, 10.4))
    b["Hind" + tag + "Tibia"] = ("Hind" + tag + "Femur", (x(10.6), 15.8, 10.4), (x(13.6), 0.9, 15.2))
    b["Hind" + tag + "Tarsus"] = ("Hind" + tag + "Tibia", (x(13.6), 0.9, 15.2), (x(15.4), 0.4, 17.8))
    b[tag + "Mand"] = ("Head", (x(0.55), 26.0, -9.3), (x(0.15), 24.9, -9.75))
    b[tag + "Ant1"] = ("Head", (x(0.6), 30.7, -9.0), (x(2.2), 34.9, -8.5))
    b[tag + "Ant2"] = (tag + "Ant1", (x(2.2), 34.9, -8.5), (x(5.0), 35.7, -2.0))
    b["Robe" + tag + "1"] = ("Hips", (x(1.4), 15.0, 2.5), (x(3.0), 14.5, 12.6))
    b["Robe" + tag + "2"] = ("Robe" + tag + "1", (x(3.0), 14.5, 12.6), (x(4.4), 12.7, 21.6))
    return b


_B.update(_side(-1, "Left"))
_B.update(_side(1, "Right"))
BONES = _B
LEGS = ("MidLeft", "MidRight", "HindLeft", "HindRight")
_KIDS = {}
for _n, (_p, _h, _t) in BONES.items():
    _KIDS.setdefault(_p, []).append(_n)
_REST = {n: V(BONES[n][2]) - V(BONES[n][1]) for n in BONES}


# ---------- the pieces ----------
PIECES = {"Skin": 19400, "Face": 5200, "Blades": 7000, "Robe": 6000, "Fine": 11000}
BAKES = {"Skin": dict(size=2048, small=1024, ray=0.22, extrusion=0.1), "Face": dict(size=1024, small=512, ray=0.2, extrusion=0.08),
         "Blades": dict(size=1024, small=512, ray=0.12, extrusion=0.05), "Robe": dict(size=1024, small=256, ray=0.08, extrusion=0.03), "Fine": dict(size=1024, small=256, ray=0.08, extrusion=0.03)}


def _mark(o, bone=None, chain=None, mix=None, falloff=1.6, keep=False):
    o["bone"], o["chain"], o["mix"], o["falloff"] = bone or "", ",".join(chain or ()), ",".join(mix[0] + mix[1]) + ":%g" % mix[2] if mix else "", falloff
    if keep:
        o["keep"] = True
    return o


def _blade(hi, teeth, glow, side, K2, Wr):
    """The tibia: a lens-section scythe with its edge on its underside, bowed along its back, drawn at its end into a hook that turns toward the femur.
    Two rows of teeth alternate along the edge. Everything rides the tibia bone."""
    t = (V(Wr) - V(K2)).normalized()
    u = V((0, -1, -0.05))
    u = (u - t * u.dot(t)).normalized()          # its underside
    s = t.cross(u).normalized()
    L = (V(Wr) - V(K2)).length
    hook = 2.6
    a0 = 0.6                                     # its rounded end reaches back past the hinge
    total = L + hook + a0
    step = 0.16
    n = int(total / step)
    back, heading = [], []
    p = V(K2) + u * 0.05 - t * a0
    ang = -0.11
    for i in range(n + 1):
        a = i * step
        back.append(p.copy())
        heading.append(ang)
        a1 = max(0.0, a - a0)
        ang = -0.11 + 0.24 * min(1.0, a1 / L) + (max(0.0, a1 - L * 0.8) / (total - a0 - L * 0.8)) ** 1.5 * 1.25
        p += (t * math.cos(ang) + u * math.sin(ang)) * step
    rings, edge = [], []
    sides = 16
    for i, c in enumerate(back):
        q = i / n
        a = q * total
        ang = heading[i]
        tan = t * math.cos(ang) + u * math.sin(ang)
        d_in = (-t * math.sin(ang) + u * math.cos(ang)).normalized()
        # the deepest about a third of the way along, thinning to a point at the hook; its other end rounded like the end of a capsule
        a1 = max(0.0, a - a0)
        depth = 0.8 + 0.85 * math.sin(math.pi * min(1.0, a1 / (L * 0.98))) ** (0.75 if a1 > L * 0.5 else 1.0)
        if a1 > L * 0.5:
            depth *= max(0.05, min(1.0, ((total - a) / (hook * 1.1)) ** 0.8))
        round_end = 0.1 + 0.9 * math.sqrt(max(0.0, 1 - (1 - min(1.0, a / 1.1)) ** 2))
        depth *= round_end
        thick = (0.56 * (1 - 0.72 * q) + 0.05) * round_end
        centre = c + d_in * depth * 0.5
        ring = []
        for k in range(sides + 1):
            b = TAU * k / sides
            ring.append(hi.v(centre + d_in * (depth * 0.5) * math.cos(b) + s * thick * math.sin(b) * (0.3 + 0.7 * abs(math.sin(b)))))
        rings.append(ring)
        edge.append((centre + d_in * (depth * 0.5), d_in, tan))
    for i in range(n):
        for k in range(sides):
            hi.f([rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]],
                 [(k / sides, i * step), ((k + 1) / sides, i * step), ((k + 1) / sides, (i + 1) * step), (k / sides, (i + 1) * step)], 0)
    tip = hi.v(edge[-1][0] + edge[-1][2] * 0.3)
    for k in range(sides):
        hi.f([rings[-1][k], rings[-1][k + 1], tip], [(k / sides, 0), ((k + 1) / sides, 0), ((k + 0.5) / sides, 0.1)], 0)
    first = hi.v(edge[0][0] - edge[0][1] * (0.5 * 0.8 * 0.1) - edge[0][2] * 0.04)
    for k in range(sides):
        hi.f([rings[0][k + 1], rings[0][k], first], [((k + 1) / sides, 0), (k / sides, 0), ((k + 0.5) / sides, 0.1)], 0)
    # the teeth: two rows, longer toward the hook, leaning toward the tip
    i = int((1.2 + a0) / step)
    row = 0
    while i < n - int(hook * 0.75 / step):
        e, d_in, tan = edge[i]
        off = s * (0.2 if row % 2 else -0.2)
        length = 0.42 + 0.34 * (i / n) + (0.14 if row % 3 == 0 else 0)
        cone(teeth, e - d_in * 0.22 + off, e + d_in * length + tan * 0.17 + off * 1.3, 0.15, sides=6)
        i += int(0.42 / step)
        row += 1
    Hm.htube(glow, [edge[j][0] - edge[j][1] * 0.04 for j in range(3 + int(a0 / step), n - 8, 4)], lambda q: 0.15 * (1 - 0.45 * q), sides=6, per=1, uv_scale=1.0, tip=True, wobble=0.0)


def _tarsus(hi, Wr, Tp):
    """A small jointed foot at the tibia's end: four beads drawing to two tiny claws."""
    a, b = V(Wr), V(Tp)
    pts = [a.lerp(b, q) + V((0, 0.2 * math.sin(math.pi * q), 0)) for q in (0, 0.33, 0.66, 1.0)]
    for k in range(3):
        Hm.htube(hi, [pts[k], pts[k + 1]], lambda q: 0.18 - 0.03 * k + 0.06 * math.sin(math.pi * q), sides=8, per=4, uv_scale=1.0, tip=False, wobble=0.0)
        G.sphere(hi, pts[k], 0.2 - 0.03 * k, nu=8, nv=6)
    for dx in (-0.12, 0.12):
        cone(hi, b, b + V((dx, -0.35, -0.42)), 0.08, sides=7)


def _femur_radius(q):
    return (0.84 + (0.56 - 0.84) * q) * (1 + 0.48 * math.sin(math.pi * q ** 0.8) ** 1.2)


def _spines(hi, a, b, n, sign, count=7, start=0.2, end=0.9):
    """A femur's two rows of spines along its underside, the middle ones longest, leaning toward the knee, rooted in its surface wherever it has thinned."""
    a, b = V(a), V(b)
    d = (b - a).normalized()
    for k in range(count):
        q = start + (end - start) * k / (count - 1)
        base = a.lerp(b, q)
        r = _femur_radius(q)
        big = 0.42 + 0.5 * math.sin(math.pi * q) ** 1.5
        for row, off in enumerate((-1, 1)):
            x_off = off * min(0.42, r * 0.62 * 0.62)
            length = big * (1.0 if (k + row) % 2 else 0.68)
            root = base + n * r * 0.78 + V((x_off, 0, 0))
            cone(hi, root, root + n * (r * 0.22 + 0.2 + length) + d * 0.18 + V((x_off * 0.3, 0, 0)), 0.16, sides=7)


def _face_groups():
    limb = T._limb
    groups = [(0.45, [
        ((0, 29.75, -8.0), (2.95, 1.2, 1.45), None),                 # across the top, between the eyes: the head's broad edge
        ((0, 28.5, -8.45), (2.15, 1.9, 1.3), None),                  # the cheeks, narrowing
        ((0, 27.05, -8.9), (1.35, 1.15, 0.95), None),
        ((0, 26.05, -9.15), (0.92, 0.8, 0.68), None),                # the small mouth at the triangle's point
        ((0, 28.5, -6.95), (1.75, 1.85, 1.15), None),                # the back of the skull
    ] + limb([(0, 29.5, -9.2), (0, 27.4, -9.6)], [(0.62, 0.5, 0.42), (0.5, 0.5, 0.36)]))]     # the frons, a keel down the face
    for side in (-1, 1):
        groups.append((0.22, limb([(side * 0.35, 30.3, -9.2), (side * 1.5, 30.75, -9.0), (side * 2.6, 31.05, -8.5)], [(0.36, 0.3, 0.3), (0.34, 0.26, 0.3), (0.2, 0.16, 0.2)])))     # the scowling ridge over each eye
    return groups


def tidy(obj, triangulate=False):
    """Faces wound outward, none collapsed, no n-gons. Unlike the older clean, it removes no small islands: a tooth here is only seven vertices."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    if triangulate:
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def build_hi():
    """The high-detail pieces, all in the bind pose: {piece: [objects]}, and the glow pieces {name: (object, hex, bone)}."""
    T.clear()
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    M = materials()
    pieces = {k: [] for k in PIECES}

    def add(piece, hi, name, mat, **kw):
        o = hi.object("MS2_" + name, coll, [mat])
        tidy(o)
        pieces[piece].append(_mark(o, **kw))

    def leafy(piece, hi, name, mat, thickness=0.08, **kw):
        pieces[piece].append(_mark(sheet(hi, "MS2_" + name, coll, mat, thickness), **kw))

    B = BONES
    # ---- the body: culms that flex along their bones
    h = Hm.Hi()
    culm(h, [(0, 13.8, 0.4), (0, 13.3, 3.6), (0, 12.6, 6.8)], 2.05, 2.15)
    cap(h, (0, 13.8, 0.75), 2.2)
    add("Skin", h, "Thorax", M["bamboo"], bone="Hips")
    h = Hm.Hi()
    culm(h, [(0, 12.8, 6.0), (0, 12.7, 11.0), (0, 11.9, 16.0), (0, 10.4, 20.6), (0, 8.4, 24.6)], 2.35, 0.95, swell=lambda t: (1 + 0.14 * math.sin(math.pi * min(1, t * 1.6))) * (0.8 + 0.2 * min(1.0, t * 14) ** 0.6))   # its mouth drawn in, inside the thorax
    cap(h, (0, 8.4, 24.6), 0.92)
    add("Skin", h, "Abdomen", M["bamboo"], chain=("Abd1", "Abd2", "Abd3", "Abd4"), falloff=2.2)
    h = Hm.Hi()
    culm(h, [(0, 13.6, 1.0), (0, 19.2, -2.4), (0, 23.0, -4.6), (0, 26.6, -6.6)], 1.6, 1.25, swell=lambda t: 1 + 0.2 * math.exp(-((t - 0.7) / 0.13) ** 2))
    cap(h, (0, 26.6, -6.6), 1.25)
    add("Skin", h, "Prothorax", M["bamboo"], chain=("Pro1", "Pro2"), falloff=2.4)
    h = Hm.Hi()
    Hm.htube(h, [(0, 14.5, 0.46), (0, 15.2, 0.03), (0, 15.84, -0.36), (0, 16.7, -0.88), (0, 17.63, -1.45)], lambda q: 1.52 + 0.53 * (1 - q) ** 1.6, sides=16, per=3, uv_scale=1.0, tip=False, wobble=0.0)
    add("Skin", h, "NeckSheath", M["bamboo"], bone="Pro1")
    # ---- the limbs: rigid culms turning at ball joints
    for side, tag in ((-1, "Left"), (1, "Right")):
        S, Tr, Kn, K2, Wr, Tp = V(B[tag + "Coxa"][1]), V(B[tag + "Femur"][1]), V(B[tag + "Femur"][2]), V(B[tag + "Tibia"][1]), V(B[tag + "Tibia"][2]), V(B[tag + "Tarsus"][2])
        h = Hm.Hi()
        culm(h, [S, S.lerp(Tr, 0.5), Tr], 1.2, 0.98, offset=0.6, swell=lambda t: 1 + 0.12 * math.sin(math.pi * t))
        cap(h, S, 1.3)
        cap(h, Tr, 1.08)
        add("Skin", h, tag + "Coxa", M["bamboo"], bone=tag + "Coxa")
        h = Hm.Hi()
        culm(h, [Tr, Tr.lerp(Kn, 0.5), Kn], 0.84, 0.56, offset=0.2, swell=lambda t: 1 + 0.48 * math.sin(math.pi * t ** 0.8) ** 1.2)
        cap(h, Tr, 1.02)
        cap(h, Kn, 0.62)
        cap(h, Kn.lerp(K2, 0.42), 0.74)                                          # the lobe the tibia hinges in
        # a real femur is deep and flat, not a round sausage: narrowed across, about its own axis
        h.verts[:] = [(side * 2.3 + (v[0] - side * 2.3) * 0.62, v[1], v[2]) for v in h.verts]
        add("Skin", h, tag + "Femur", M["bamboo"], bone=tag + "Femur")
        spines = Hm.Hi()
        _spines(spines, Tr, Kn, V((0, -0.6, -0.8)), side)
        add("Blades", spines, tag + "FemurSpines", M["claw"], bone=tag + "Femur", keep=True)
        hull, teeth, glow = Hm.Hi(), Hm.Hi(), Hm.Hi()
        _blade(hull, teeth, glow, side, K2, Wr)
        add("Blades", hull, tag + "Blade", M["blade"], bone=tag + "Tibia")
        add("Blades", teeth, tag + "Teeth", M["claw"], bone=tag + "Tibia", keep=True)
        foot = Hm.Hi()
        _tarsus(foot, B[tag + "Tarsus"][1], Tp)
        add("Blades", foot, tag + "Foot", M["dark"], bone=tag + "Tarsus", keep=True)
        for pair in ("Mid", "Hind"):
            leg = pair + tag
            hip, knee, ankle, toe = V(B[leg + "Femur"][1]), V(B[leg + "Tibia"][1]), V(B[leg + "Tarsus"][1]), V(B[leg + "Tarsus"][2])
            h = Hm.Hi()
            culm(h, [hip, hip.lerp(knee, 0.5) + V((0, 0.5, 0)), knee], 1.08, 0.8, offset=0.4)
            cap(h, hip, 1.22)
            cap(h, knee, 0.88)
            add("Skin", h, leg + "Femur", M["bamboo"], bone=leg + "Femur")
            h = Hm.Hi()
            culm(h, [knee, knee.lerp(ankle, 0.5) + V((side * 0.35, 0, -0.2 if pair == "Mid" else 0.2)), ankle], 0.82, 0.5, offset=1.1)
            cap(h, knee, 0.92)
            cap(h, ankle, 0.56)
            add("Skin", h, leg + "Tibia", M["bamboo"], bone=leg + "Tibia")
            h = Hm.Hi()
            d = (toe - ankle).normalized()
            pts = [ankle.lerp(toe, q) for q in (0, 0.35, 0.68, 1.0)]
            for k in range(3):
                Hm.htube(h, [pts[k], pts[k + 1]], lambda q: 0.42 - 0.07 * k + 0.08 * math.sin(math.pi * q), sides=8, per=4, uv_scale=1.0, tip=False, wobble=0.0)
                G.sphere(h, pts[k], 0.45 - 0.07 * k, nu=8, nv=6)
            for dz in (-0.28, 0.28):
                cone(h, toe, toe + d * 0.7 + V((d.z * dz * 2, -0.24, -d.x * dz * 2)), 0.15, sides=6)
            add("Skin", h, leg + "Foot", M["dark"], bone=leg + "Tarsus", keep=True)
            # young leaves sprouting at the knee: it is a living plant
            sprout = Hm.Hi()
            for k in (0, 1):
                leaf(sprout, knee + V((0, 0.5, 0.2 * k)), (side * 0.4, 1, 0.3 - 0.6 * k), (side * 0.3, 0.1, -1 + 2 * k), 2.6 - 0.4 * k, 0.33, curl=0.08)
            leafy("Fine", sprout, leg + "Sprout", M["leaf"], bone=leg + "Femur")
        sprout = Hm.Hi()
        leaf(sprout, S + V((side * 0.7, 0.4, 0.3)), (side * 0.8, 0.7, 0.3), (side * 0.2, 0.2, -1), 2.8, 0.36, curl=0.1)
        leafy("Fine", sprout, tag + "ShoulderLeaf", M["leaf"], bone=tag + "Coxa")
        pieces.setdefault("_glow", {})[tag + "Edge"] = (glow.object("MS2_" + tag + "Edge", coll, [K.glow_material(EDGE_HEX)], smooth=True), EDGE_HEX, tag + "Tibia")

    # ---- the head: a broad triangle with tall eyes at its top corners
    groups = _face_groups()
    face = G.blob("MS2_Face", coll, M["face"], P._rough_lobes(groups), voxel=0.07, smooth=0.7, rough=0.0, chisel="MantisV2Skin")
    T._settle(face, groups)
    G.soften(face, 3)
    T._settle(face, groups, passes=2)
    pieces["Face"].append(_mark(face, bone="Head"))
    eyes, glow_p, small = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        G.sphere(eyes, (side * 2.95, 30.0, -8.1), 1.0, nu=26, nv=18, radii=(1.28, 1.92, 1.38))
        G.sphere(glow_p, (side * 3.28, 29.85, -9.4), 0.3, nu=14, nv=10, radii=(0.36, 0.48, 0.11))
    for x_, y_ in ((0, 30.15), (-0.5, 29.8), (0.5, 29.8)):
        G.sphere(small, G.surface_along(face, V((x_, y_, -8.0)), V((0, 0, -1)), reach=4.0) + V((0, 0, 0.04)), 0.17, nu=8, nv=6)     # the ocelli, set on the face
    pieces["Face"].append(_mark(eyes.object("MS2_Eyes", coll, [M["eye"]]), bone="Head", keep=True))
    add("Face", small, "Ocelli", M["gold"], bone="Head", keep=True)
    pieces["_glow"]["Pupils"] = (glow_p.object("MS2_Pupils", coll, [K.glow_material(PUPIL_HEX)], smooth=True), PUPIL_HEX, "Head")

    # ---- the fine things: mouthparts, antennae, the sage's brows and beard, the topknot, the mala
    brows, crest, gold, beads = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side, tag in ((-1, "Left"), (1, "Right")):
        for k, (dy, dz, drop) in enumerate(((0.0, 0.0, 0.0), (0.22, 0.12, -0.5), (-0.2, -0.1, 0.45))):
            Hm.htube(brows, [(side * 0.45, 30.75 + dy, -9.42 + dz), (side * 2.2, 31.65 + dy, -9.62 + dz), (side * 4.15, 31.05 + dy, -8.95 + dz), (side * (4.85 + 0.1 * k), 29.25 + dy, -8.6 + dz), (side * (4.75 + 0.15 * k), 27.3 + drop, -8.65 + dz)],
                     lambda q: 0.21 * (1 - 0.8 * q ** 1.4), sides=7, per=6, uv_scale=0.12, tip=True, wobble=0.0)
        h = Hm.Hi()
        cone(h, B[tag + "Mand"][1], B[tag + "Mand"][2], 0.36, sides=8)
        Hm.htube(h, [(side * 0.92, 26.35, -9.0), (side * 1.32, 25.4, -9.4), (side * 1.2, 24.6, -9.9)], lambda q: 0.14 * (1 - 0.4 * q), sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)
        add("Fine", h, tag + "Mandible", M["dark"], bone=tag + "Mand", keep=True)
        h = Hm.Hi()
        Hm.htube(h, [B[tag + "Ant1"][1], (side * 1.0, 32.6, -9.6), B[tag + "Ant1"][2], (side * 3.8, 36.0, -5.5), B[tag + "Ant2"][2]], lambda q: 0.17 * (1 - 0.55 * q), sides=6, per=6, uv_scale=1.0, tip=True, wobble=0.0)
        add("Fine", h, tag + "Antenna", M["dark"], chain=(tag + "Ant1", tag + "Ant2"), falloff=1.6, keep=True)
    add("Fine", brows, "Brows", M["brow"], bone="Head", keep=True)
    beard = Hm.Hi()
    for side in (-1, 1):
        leaf(beard, (side * 0.32, 25.8, -8.9), (side * 0.12, -1, -0.1), (0, 0.1, -1), 5.2, 0.34, curl=0.06, twist=side * 0.5, fold=0.1)
    leaf(beard, (0, 25.7, -8.95), (0, -1, -0.03), (0, 0.05, -1), 5.8, 0.36, curl=0.05, fold=0.1)
    leafy("Fine", beard, "Beard", M["brow"], 0.06, chain=("Beard1", "Beard2"), falloff=1.4)
    for k in (-1, 0, 1):
        leaf(crest, (k * 0.22, 30.9, -7.5), (k * 0.35, 1, 0.25 + 0.1 * abs(k)), (k * 0.6, 0.1, -1), 3.6 - 0.4 * abs(k), 0.4, curl=0.12)
    leafy("Fine", crest, "Crest", M["leaf"], bone="Head")
    P._ring(gold, [V((0, 31.05, -7.5)) + V((0.4 * math.cos(TAU * i / 20), 0, 0.4 * math.sin(TAU * i / 20))) for i in range(20)], 0.12, sides=6)
    add("Fine", gold, "CrestRing", M["gold"], bone="Head", keep=True)
    centre, axis = V((0, 20.4, -3.0)), V((0, 5.0, -3.1)).normalized()
    across = V((1, 0, 0))
    front = axis.cross(across).normalized()
    front = -front if front.z > 0 else front
    count = 17
    lowest = None
    for k in range(count):
        a = TAU * k / count
        p = centre + (across * math.sin(a) + front * math.cos(a)) * 2.05 + V((0, -1.3 * max(0.0, math.cos(a)) ** 2, 0))
        G.sphere(beads, p, 0.55 if k else 0.78, nu=12, nv=8)
        lowest = lowest or p
    add("Fine", beads, "Mala", M["jade"], bone="Pro2", keep=True)
    tass = Hm.Hi()
    top = lowest + V((0, -0.78, 0))
    Hm.htube(tass, [top, top + V((0, -0.5, -0.05))], lambda q: 0.16, sides=8, per=2, uv_scale=2.0, tip=False, wobble=0.0)
    for j in range(8):
        a = TAU * j / 8
        b = top + V((0, -0.5, -0.05)) + V((0.14 * math.cos(a), 0, 0.14 * math.sin(a)))
        Hm.htube(tass, [b, b + V((0.08 * math.cos(a), -1.5, 0.08 * math.sin(a)))], lambda q: 0.07, sides=5, per=3, uv_scale=2.0, tip=True, wobble=0.0)
    add("Fine", tass, "Tassel", M["gold"], bone="Tassel", keep=True)
    tuft = Hm.Hi()
    for k in range(5):
        a = (k - 2) * 0.32
        leaf(tuft, (math.sin(a) * 0.3, 8.4, 24.4), (math.sin(a) * 0.8, -0.35, 1), (0, 1, 0.3), 3.6 - 0.3 * abs(k - 2), 0.42, curl=-0.08)
    leafy("Fine", tuft, "AbdomenTuft", M["leaf"], bone="Abd4")

    # ---- the robe: great leaves folded over the back like wings, a hidden fan of them under the outer ones
    robe = Hm.Hi()
    leaf(robe, (0, 15.35, 1.9), (0, 0.09, 1), (0, 1, -0.09), 21.5, 2.2, curl=-0.13, fold=0.2)
    leafy("Robe", robe, "RobeMid", M["robe"], 0.12, chain=("RobeMid1", "RobeMid2"), falloff=3.0, keep=True)
    for side, tag in ((-1, "Left"), (1, "Right")):
        for k, (base, d, nrm, length, width, twist, q) in enumerate((
                ((side * 0.9, 15.25, 2.1), (side * 0.09, 0.07, 1), (side * 0.35, 1, -0.07), 20.5, 2.0, 0.15, 0.4),
                ((side * 1.6, 15.0, 2.4), (side * 0.16, 0.04, 1), (side * 0.55, 1, -0.04), 18.8, 1.8, 0.25, 0.8),
                ((side * 1.75, 14.75, 3.0), (side * 0.22, 0.02, 1), (side * 0.65, 1.0, -0.02), 16.6, 1.35, 0.2, 1.0))):
            h = Hm.Hi()
            leaf(h, base, d, nrm, length, width, curl=-0.11, twist=side * twist)
            leafy("Robe", h, "Robe" + tag + str(k), M["robe"], 0.12, mix=(("RobeMid1", "RobeMid2"), ("Robe" + tag + "1", "Robe" + tag + "2"), q), falloff=3.0, keep=True)
    glows = pieces.pop("_glow")
    for o, _, _ in glows.values():
        tidy(o, triangulate=True)
        P._fit_uv(o)
    build_skeleton(coll)
    return pieces, glows


def build_skeleton(coll):
    data = bpy.data.armatures.new(RIG)
    arm = bpy.data.objects.new(RIG, data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for name, (parent, head, tail) in BONES.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = W.rb(*head), W.rb(*tail)
        made[name] = b
    for name, (parent, head, tail) in BONES.items():
        if parent:
            made[name].parent = made[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in data.bones:
        b.use_deform = b.name != "Root"
    return arm


# ---------- the weights ----------
def _distances(pts, names):
    import numpy as np
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    return np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)


def _chain_weights(pts, names, falloff):
    """Weights along a chain: each bone by how near it is, handed over gradually across the joint."""
    import numpy as np
    d = _distances(pts, names)
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[w < 0.03] = 0
    return w / w.sum(axis=1, keepdims=True)


def paint(obj):
    """Paints an object from its marks: one bone (a rigid plate), a chain (a culm or a leaf that flexes), or a mix of two chains (a leaf between two ribs of the fan)."""
    import numpy as np
    pts = P._points(obj)
    obj.vertex_groups.clear()
    groups = {b: obj.vertex_groups.new(name=b) for b in BONES}       # the same list in the same order on every object: joining keeps group numbers, not names
    table = {}
    if obj.get("bone"):
        table[obj["bone"]] = np.ones(len(pts))
    elif obj.get("chain"):
        names = obj["chain"].split(",")
        w = _chain_weights(pts, names, obj["falloff"])
        table.update({n: w[:, j] for j, n in enumerate(names)})
    elif obj.get("mix"):
        names, q = obj["mix"].split(":")
        names = names.split(",")
        q = float(q)
        a, b = names[:2], names[2:]
        wa, wb = _chain_weights(pts, a, obj["falloff"]), _chain_weights(pts, b, obj["falloff"])
        table.update({n: wa[:, j] * (1 - q) for j, n in enumerate(a)})
        table.update({n: wb[:, j] * q for j, n in enumerate(b)})
    for name, w in table.items():
        idx = np.nonzero(w > 1e-4)[0]
        for i in idx.tolist():
            groups[name].add([i], float(w[i]), "REPLACE")


def attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


def bind_review(pieces, glows):
    for objs in pieces.values():
        for o in objs:
            paint(o)
            attach(o)
    for o, _, bone in glows.values():
        o.vertex_groups.clear()
        o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
        attach(o)


def settle_weights(low):
    """The game mesh keeps the weights its high piece was painted with (reduction only blends them within one piece): normalised, four bones at most."""
    most, bare = 0, 0
    for v in low.data.vertices:
        w = sorted(((g.group, g.weight) for g in v.groups), key=lambda e: -e[1])
        keep = [e for e in w[:4] if e[1] > 0.015]
        total = sum(e[1] for e in keep)
        bare += total <= 0
        most = max(most, len(keep))
        kept = {e[0] for e in keep}
        for gi, _ in w:
            if gi not in kept:
                low.vertex_groups[gi].remove([v.index])
        for gi, x in keep:
            low.vertex_groups[gi].add([v.index], x / max(total, 1e-6), "REPLACE")
    used = {g.group for v in low.data.vertices for g in v.groups}
    for vg in [g for g in low.vertex_groups if g.index not in used]:
        low.vertex_groups.remove(vg)
    attach(low)
    return {"verts": len(low.data.vertices), "groups": len(low.vertex_groups), "max influences": most, "unweighted": bare}


# ---------- posing: rotations in Roblox axes, each on top of its parent, as the game's joints work ----------
_euler, _mat, _frame = P._euler, P._mat, P._frame
_rx = lambda deg: Matrix.Rotation(math.radians(deg), 3, "X")


def fk(pose, shift=(0, 0, 0)):
    out = {}

    def walk(name, parent):
        pa, head, tail = BONES[name]
        r = _mat(pose.get(name, (0, 0, 0)))
        if parent is None:
            world, at = r, V(head)
        else:
            pr, pp = out[parent]
            world = pr @ r
            at = pp + pr @ (V(head) - V(BONES[parent][1]))
            if name == "Hips":
                at = at + V(shift)
        out[name] = (world, at)
        for child in _KIDS.get(name, ()):
            walk(child, name)

    walk("Root", None)
    return out


def tail_of(state, name):
    r, at = state[name]
    return at + r @ _REST[name]


def set_pose(pose, shift=(0, 0, 0)):
    arm = bpy.data.objects[RIG]
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        rest = pb.bone.matrix_local.to_3x3()
        t = T.rb_rot(*pose.get(pb.name, (0, 0, 0)))
        pb.rotation_quaternion = (rest.inverted() @ t @ rest).to_quaternion()
        pb.location = (0, 0, 0)
    hips = arm.pose.bones["Hips"]
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips.location = hips.bone.matrix_local.to_3x3().inverted() @ (C @ V(shift))
    bpy.context.view_layer.update()


# ---------- the walking legs, solved: a femur that swings (yaw) and lifts (roll), a tibia that bends (roll). The game's planted feet solve the same three ----------
def _leg_point(hr, hp, leg, yaw, a, b):
    H, Kn, An = V(BONES[leg + "Femur"][1]), V(BONES[leg + "Tibia"][1]), V(BONES[leg + "Tarsus"][1])
    r1 = hr @ _mat((0, yaw, a))
    r2 = r1 @ _mat((0, 0, b))
    return hp + r1 @ (Kn - H) + r2 @ (An - Kn), r2


def solve_leg(pose, shift, leg, foot=(0, 0, 0, 0)):
    """foot = (dx, dy, dz, toe): where the ankle goes from where it stands, and how far the tarsus tips."""
    dx, dy, dz, toe = foot
    state = fk(pose, shift)
    hr, hp = state["Hips"][0], state[leg + "Femur"][1]
    target = V(BONES[leg + "Tarsus"][1]) + V((dx, dy, dz))
    x = [0.0, 0.0, 0.0]
    for _ in range(14):
        p, _r = _leg_point(hr, hp, leg, *x)
        e = target - p
        if e.length < 0.004:
            break
        J = []
        for k in range(3):
            y = list(x)
            y[k] += 0.5
            J.append((_leg_point(hr, hp, leg, *y)[0] - p) / 0.5)
        m = Matrix((J[0], J[1], J[2])).transposed()
        n = m.transposed() @ m + Matrix.Identity(3) * 1e-3
        step = n.inverted_safe() @ (m.transposed() @ e)
        x = [x[k] + max(-14.0, min(14.0, step[k])) for k in range(3)]
    p, r2 = _leg_point(hr, hp, leg, *x)
    pose[leg + "Femur"] = (0, x[0], x[1])
    pose[leg + "Tibia"] = (0, 0, x[2])
    pose[leg + "Tarsus"] = _euler(r2.inverted() @ _rx(toe))
    return (target - p).length


# ---------- the poses it holds ----------
def arm(body, coxa, femur, tibia, tarsus=68.0, sides=("Left", "Right")):
    """Both forelegs, mirrored: coxa and femur are (pitch, outward yaw, outward roll). Tibia 0 reaches forward as bound; negative shuts it (-118 is folded shut)."""
    for tag in sides:
        s = 1 if tag == "Left" else -1
        body[tag + "Coxa"] = (coxa[0], s * coxa[1], -s * coxa[2])
        body[tag + "Femur"] = (femur[0], s * femur[1], -s * femur[2])
        body[tag + "Tibia"] = (tibia, 0, 0)
        body[tag + "Tarsus"] = (tarsus, 0, 0)
    return body


def robe(body, spread, lift, mid=0.0, droop=0.0):
    """The robe's ribs: spread opens them outward, lift raises them off the back, mid raises the middle leaf, droop bends their tips down."""
    for tag, s in (("Left", 1), ("Right", -1)):
        body["Robe" + tag + "1"] = (-lift, -s * spread, -s * lift * 0.6)
        body["Robe" + tag + "2"] = (droop, -s * spread * 0.2, 0)
    body["RobeMid1"] = (-mid, 0, 0)
    body["RobeMid2"] = (droop * 0.8, 0, 0)
    return body


def _level_head(pose, shift, pitch=0.0, yaw=0.0, roll=0.0):
    """Its head holds its own line in the world while the body rocks under it, as a watching mantis's does."""
    state = fk(pose, shift)
    pose["Head"] = _euler(state["Pro2"][0].inverted() @ _mat((pitch, yaw, roll)))


STAND_SHIFT = (0, -0.3, 0)
GUARD = arm({"Pro1": (2, 0, 0), "Pro2": (0, 0, 0), "Abd2": (2, 0, 0)}, (6, 0, 2), (2, 0, 1), -102)
GUARD_HEAD = 0.0


def _posed(body, shift, head, feet=None):
    pose = dict(body)
    for leg in LEGS:
        solve_leg(pose, shift, leg, (feet or {}).get(leg, (0, 0, 0, 0)))
    _level_head(pose, shift, *(head if isinstance(head, tuple) else (head,)))
    return pose


def state_poses():
    stand = _posed(GUARD, STAND_SHIFT, GUARD_HEAD)
    states = {"Guardian": (dict(stand), STAND_SHIFT)}
    states["Returning"] = (_posed(GUARD, STAND_SHIFT, -6.0), STAND_SHIFT)
    # meditating: low on its legs, the forelegs shut in prayer under the chin, head bowed, antennae laid back, robe tight
    s = (0, -1.5, 0.3)
    body = arm({"Hips": (1, 0, 0), "Pro1": (5, 0, 0), "Pro2": (-3, 0, 0), "Abd1": (2, 0, 0), "Abd2": (4, 0, 0), "Abd3": (3, 0, 0), "LeftAnt1": (22, 0, 0), "RightAnt1": (22, 0, 0)}, (10, 0, 0), (2, 0, 0), -110)
    states["Dormant"] = (_posed(body, s, -24.0), s)
    states["Resting"] = (dict(states["Dormant"][0]), s)
    # weakened: sunk low, the blades let fall open with their hooks near the ground, head hanging, robe slack and tips dropped
    s = (0, -5.2, -0.6)
    body = robe(arm({"Hips": (-4, 0, 2), "Pro1": (-16, 0, -2), "Pro2": (-8, 0, 0), "Abd1": (1, 0, 0), "Abd2": (3, 0, 0), "Abd3": (2, 0, 0), "LeftMand": (0, 0, -8), "RightMand": (0, 0, 8), "LeftAnt1": (30, 0, 0), "RightAnt1": (24, 0, 0)},
                    (14, 0, 8), (-28, 0, 2), -82, 125.0), 4, 3, 2, 2)
    states["Weakened"] = (_posed(body, s, -30.0), s)
    # the threat display: up on its legs, reared, the forelegs raised wide with their spines showing, the robe flared like wings, the abdomen curled up, jaws open
    s = (0, 0.9, 0.6)
    body = robe(arm({"Hips": (-2, 0, 0), "Pro1": (10, 0, 0), "Pro2": (6, 0, 0), "Abd1": (-8, 0, 0), "Abd2": (-14, 0, 0), "Abd3": (-14, 0, 0), "Abd4": (-10, 0, 0),
                     "LeftMand": (0, 0, -16), "RightMand": (0, 0, 16), "LeftAnt1": (34, -10, 0), "RightAnt1": (34, 10, 0)}, (34, 18, 40), (10, 20, 34), -40, 40.0), 40, 46, 36, -8)
    states["Enraged"] = (_posed(body, s, 6.0), s)
    return stand, STAND_SHIFT, states


# ---------- the gaits ----------
# It walks on four legs in diagonal pairs, each hind a beat after its mid, rocking like a leaf in the wind as a real mantis does, its head held still in the
# world. It runs the same way, lower and stretched out, with the prothorax reaching forward. Each stride is measured: what a planted foot travels back
# under it, per share of the cycle it stays down.
GAITS = {
    "walk": {"reach": 6.4, "duty": 0.68, "lift": 2.8, "phase": {"MidLeft": 0.0, "HindRight": 0.07, "MidRight": 0.5, "HindLeft": 0.57},
             "hips": -0.7, "bob": 0.28, "roll": 3.4, "yaw": 3.0, "slide": 0.3, "pro": -3.0, "head": -2.0, "arm": (6, 0, 2), "femur": (2, 0, 1), "tibia": -104, "abd": 3.0, "robe": 5.0, "speed": 13},
    "run": {"reach": 7.0, "duty": 0.46, "lift": 4.2, "phase": {"MidLeft": 0.0, "HindRight": 0.05, "MidRight": 0.5, "HindLeft": 0.55},
            "hips": -1.6, "bob": 0.65, "roll": 2.2, "yaw": 2.0, "slide": 0.6, "pro": -14.0, "head": 8.0, "arm": (20, 0, 4), "femur": (6, 0, 3), "tibia": -106, "abd": 5.0, "robe": 14.0, "speed": 23},
}


def stride_of(g):
    return 2 * g["reach"] / g["duty"]


def _ease(u):
    return u * u * (3 - 2 * u)


def _step(g, p):
    """A foot through its cycle, p from touching down: (dz, dy, toe)."""
    reach, duty = g["reach"], g["duty"]
    if p < duty:
        return -reach + 2 * reach * (p / duty), 0.0, 0.0
    w = (p - duty) / (1 - duty)
    return reach - 2 * reach * _ease(w), g["lift"] * math.sin(math.pi * w) ** 0.9, 26.0 * math.sin(math.pi * w)


def gait_pose(name, phase):
    g = GAITS[name]
    w = TAU * phase
    roll = g["roll"] * math.sin(w)                     # it rolls toward the pair that holds it up
    yaw = g["yaw"] * math.sin(w + 0.8)
    bob = g["bob"] * math.cos(2 * w)
    shift = (0, g["hips"] + bob, g["slide"] * math.sin(2 * w + 0.6))
    body = arm(dict(GUARD), g["arm"], g["femur"], g["tibia"] + 3 * math.sin(w - 0.6))
    body.update({
        "Hips": (0, yaw, roll),
        "Pro1": (GUARD["Pro1"][0] + g["pro"] * 0.6, -yaw * 0.7, -roll * 0.65),
        "Pro2": (g["pro"] * 0.4, -yaw * 0.3, -roll * 0.35),
        "Abd1": (0, -yaw * 0.6 - g["abd"] * math.sin(w - 0.6) * 0.5, -roll * 0.3),
        "Abd2": (GUARD["Abd2"][0], g["abd"] * math.sin(w - 1.1) * 0.7, 0),
        "Abd3": (0, g["abd"] * math.sin(w - 1.7), 0),
        "Abd4": (0, g["abd"] * 1.3 * math.sin(w - 2.3), 0),
        "LeftAnt1": (8 + 3 * math.sin(2 * w), 0, 0), "RightAnt1": (8 + 3 * math.sin(2 * w + 0.5), 0, 0),
        "Tassel": (4 * math.sin(2 * w - 0.8), 0, 5 * math.sin(w - 0.8)),
    })
    robe(body, 0, g["robe"], g["robe"] * 0.6)
    pose = dict(body)
    for leg in LEGS:
        dz, dy, toe = _step(g, (phase - g["phase"][leg]) % 1)
        solve_leg(pose, shift, leg, (0, dy, dz, toe))
    _level_head(pose, shift, g["head"])
    return pose, shift


# ---------- the moves: each a list of keys over the guard, the legs solved every frame so a planted foot stays on its spot ----------
def _key(at, ease="smooth", body=None, shift=STAND_SHIFT, feet=None, head=0.0):
    b = dict(GUARD)
    b.update(body or {})
    return {"at": at, "ease": ease, "body": b, "shift": shift, "feet": feet or {}, "head": head}


def clip_pose(t, keys):
    if t >= keys[-1]["at"]:
        a = b = keys[-1]
        u = 0.0
    else:
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if t <= b["at"]:
                u = (t - a["at"]) / (b["at"] - a["at"])
                u = {"in": u * u * u, "out": 1 - (1 - u) ** 3, "smooth": _ease(u), "linear": u, "in2": u * u}[b["ease"]]
                break
    pose = {}
    for n in set(a["body"]) | set(b["body"]):
        x, y = a["body"].get(n, (0, 0, 0)), b["body"].get(n, (0, 0, 0))
        pose[n] = tuple(x[k] + (y[k] - x[k]) * u for k in range(3))    # as the game blends: angle by angle, so what's checked here is what plays
    shift = tuple(a["shift"][k] + (b["shift"][k] - a["shift"][k]) * u for k in range(3))
    for leg in LEGS:
        fa, fb = a["feet"].get(leg, (0, 0, 0, 0)), b["feet"].get(leg, (0, 0, 0, 0))
        solve_leg(pose, shift, leg, tuple(fa[k] + (fb[k] - fa[k]) * u for k in range(4)))
    ha, hb = a["head"], b["head"]
    if isinstance(ha, tuple) or isinstance(hb, tuple):
        ha = ha if isinstance(ha, tuple) else (ha, 0, 0)
        hb = hb if isinstance(hb, tuple) else (hb, 0, 0)
        _level_head(pose, shift, *(ha[k] + (hb[k] - ha[k]) * u for k in range(3)))
    else:
        _level_head(pose, shift, ha + (hb - ha) * u)
    return pose, shift


def _jaws(body, deg):
    body["LeftMand"], body["RightMand"] = (0, 0, -deg), (0, 0, deg)
    return body


def clips():
    out = {}
    # the scythes: it rocks back on its hind legs and draws both forelegs up and open; hangs there; then the whole front of it drops and the blades shoot out,
    # reaching low and forward, and snap shut on what they caught; it holds, and folds them back
    w = 0.6
    out["Scythe"] = [
        _key(0.0),
        _key(0.24, "smooth", robe(arm(_jaws({"Hips": (3, 0, 0), "Pro1": (8, 0, 0), "Abd1": (-3, 0, 0)}, 4), (20, 8, 16), (10, 4, 12), -60, 40), 4, 6, 3), (0, 0.1, 1.0), None, 2.0),
        _key(w - 0.14, "smooth", robe(arm(_jaws({"Hips": (5, 0, 0), "Pro1": (12, 0, 0), "Pro2": (6, 0, 0), "Abd1": (-5, 0, 0), "Abd2": (-4, 0, 0)}, 9), (36, 16, 42), (14, 14, 32), -30, 30), 12, 14, 8), (0, 0.5, 1.6), None, 4.0),
        _key(w, "in", robe(arm(_jaws({"Hips": (-10, 0, 0), "Pro1": (-20, 0, 0), "Pro2": (-10, 0, 0), "Abd1": (4, 0, 0), "Abd2": (4, 0, 0), "Beard1": (-14, 0, 0)}, 14), (38, -5, 2), (-40, -3, 0), -6, 60), 20, 20, 14, 8), (0, -2.8, -2.6), None, -18.0),
        _key(w + 0.1, "out", robe(arm(_jaws({"Hips": (-11, 0, 0), "Pro1": (-20, 0, 0), "Pro2": (-11, 0, 0), "Abd1": (5, 0, 0), "Abd2": (5, 0, 0), "Beard1": (-6, 0, 0)}, 10), (38, -5, 2), (-38, -3, 0), -66, 105), 16, 14, 10, 6), (0, -3.0, -2.7), None, -19.0),
        _key(w + 0.32, "smooth", robe(arm(_jaws({"Hips": (-8, 0, 0), "Pro1": (-14, 0, 0), "Pro2": (-8, 0, 0), "Abd1": (3, 0, 0)}, 6), (32, -3, 2), (-28, -2, 0), -78, 90), 6, 6, 4), (0, -2.2, -1.8), None, -14.0),
        _key(w + 0.75, "smooth", None, STAND_SHIFT, None, 0.0),
    ]
    # the blade wave: it coils low, shut tight; it rises as tall as it can with both blades crossed high over its head and the robe lifting; then it flings them
    # down and out, lunging, the robe flaring with the force of it; it holds, and gathers itself
    w = 0.9
    out["BladeWave"] = [
        _key(0.0),
        _key(w * 0.3, "smooth", robe(arm({"Hips": (-3, 0, 0), "Pro1": (-10, 0, 0), "Pro2": (-3, 0, 0), "Abd1": (3, 0, 0)}, (8, 0, 0), (2, 0, 0), -110, 68), 0, -2), (0, -1.8, 0.6), None, -14.0),
        _key(w - 0.14, "smooth", robe(arm(_jaws({"Hips": (5, 0, 0), "Pro1": (12, 0, 0), "Pro2": (6, 0, 0), "Abd1": (-6, 0, 0), "Abd2": (-6, 0, 0)}, 10), (40, 6, 22), (-28, 2, 8), 30, 0), 12, 20, 14), (0, 1.0, 1.2), None, 8.0),
        _key(w + 0.03, "in", robe(arm(_jaws({"Hips": (-10, 0, 0), "Pro1": (-20, 0, 0), "Pro2": (-12, 0, 0), "Abd1": (5, 0, 0), "Abd2": (5, 0, 0), "Beard1": (-16, 0, 0)}, 16), (42, 16, 30), (-26, 8, 22), 6, 40), 30, 20, 16, 6), (0, -2.6, -2.2), None, -14.0),
        _key(w + 0.4, "out", robe(arm(_jaws({"Hips": (-9, 0, 0), "Pro1": (-18, 0, 0), "Pro2": (-10, 0, 0), "Abd1": (4, 0, 0)}, 10), (38, 14, 26), (-24, 7, 20), 0, 40), 26, 14, 10, 6), (0, -2.4, -2.0), None, -12.0),
        _key(w + 1.1, "smooth", None, STAND_SHIFT, None, 0.0),
    ]
    # the leap: a deep crouch on loaded hind legs, the blades shut; the hinds drive and it goes up with the robe opening into wings, forelegs reaching, hind legs
    # trailing; on the way down its legs reach for the ground and its wings cup the air
    tuck = {"MidLeft": (0, 4.5, -6.0, 30), "MidRight": (0, 4.5, -6.0, 30), "HindLeft": (0, 3.2, 7.5, 34), "HindRight": (0, 3.2, 7.5, 34)}
    reach = {"MidLeft": (0, 1.2, -3.2, 14), "MidRight": (0, 1.2, -3.2, 14), "HindLeft": (0, 2.4, 1.6, 20), "HindRight": (0, 2.4, 1.6, 20)}
    fly = robe(arm(_jaws({"Hips": (-5, 0, 0), "Pro1": (-14, 0, 0), "Pro2": (-6, 0, 0), "Abd1": (2, 0, 0), "Abd2": (6, 0, 0), "Abd3": (6, 0, 0), "LeftAnt1": (36, 0, 0), "RightAnt1": (36, 0, 0)}, 8), (42, 6, 12), (-20, 2, 6), -4, 20), 40, 30, 22, 2)
    fall = robe(arm(_jaws({"Hips": (-10, 0, 0), "Pro1": (-6, 0, 0), "Pro2": (2, 0, 0), "Abd1": (-4, 0, 0), "Abd2": (-6, 0, 0)}, 6), (28, 6, 10), (2, 2, 6), -50, 40), 30, 34, 26, -4)
    out["Leap"] = [
        _key(0.0),
        _key(0.34, "smooth", robe(arm({"Hips": (4, 0, 0), "Pro1": (-8, 0, 0), "Pro2": (-4, 0, 0), "Abd1": (-8, 0, 0), "Abd2": (-6, 0, 0), "Abd3": (-4, 0, 0)}, (10, 0, 0), (2, 0, 0), -110, 68), 0, 12, 12), (0, -4.6, 0.8), None, -12.0),
        _key(0.5, "in2", robe(arm({"Hips": (-10, 0, 0), "Pro1": (-8, 0, 0)}, (24, 2, 4), (-6, 0, 2), -60, 40), 16, 18, 10), (0, 0.2, -1.0), None, 0.0),
        _key(0.82, "out", fly, (0, 0, 0), tuck, -4.0),
        _key(1.3, "smooth", fall, (0, 0, 0), reach, -8.0),
        _key(1.6, "smooth", fall, (0, -0.2, 0), reach, -8.0),
    ]
    # landing: the legs take it and it sinks deep, the robe flopping shut after it, the blades drawing in; it rises and folds them
    out["Land"] = [
        _key(0.0, "smooth", fall, (0, -0.2, 0), reach, -8.0),
        _key(0.13, "out", robe(arm(_jaws({"Hips": (-3, 0, 0), "Pro1": (-16, 0, 0), "Pro2": (-6, 0, 0), "Abd1": (5, 0, 0), "Abd2": (5, 0, 0), "Beard1": (-10, 0, 0)}, 6), (30, 4, 8), (-6, 0, 4), -70, 50), 10, 6, 4, 10), (0, -5.0, -0.6), None, -14.0),
        _key(0.42, "smooth", robe(arm({"Hips": (-1, 0, 0), "Pro1": (-6, 0, 0), "Abd1": (2, 0, 0)}, (14, 1, 3), (2, 0, 1), -96, 60), 2, 0), (0, -2.0, -0.2), None, -6.0),
        _key(0.9, "smooth", None, STAND_SHIFT, None, 0.0),
    ]
    # waking from meditation: the head lifts slowly, antennae rising one after the other, the shut blades part a little and close again with a click
    sit, sit_shift = state_poses()[2]["Dormant"]
    dorm = {k: v for k, v in sit.items() if k not in ("Head",) and not k.endswith(("Femur", "Tibia", "Tarsus")) or k in ("LeftFemur", "RightFemur", "LeftTibia", "RightTibia", "LeftTarsus", "RightTarsus")}
    out["Awaken"] = [
        _key(0.0, "smooth", dorm, sit_shift, None, -24.0),
        _key(0.55, "smooth", dict(dorm, LeftAnt1=(6, 0, 0)), (0, -1.2, 0.2), None, -10.0),
        _key(1.0, "smooth", arm(dict(dorm, LeftAnt1=(4, 0, 0), RightAnt1=(6, 0, 0)), (10, 2, 3), (2, 0, 1), -88, 60), (0, -0.7, 0.1), None, 2.0),
        _key(1.22, "in", arm(dict(dorm, LeftAnt1=(6, 0, 0), RightAnt1=(6, 0, 0)), (8, 1, 2), (2, 0, 1), -106, 68), (0, -0.5, 0), None, 3.0),
        _key(1.8, "smooth", None, STAND_SHIFT, None, 0.0),
    ]
    # faltering: a blow it can't take: the head whips aside, the front of it drops, the blades fall open; it sinks onto its legs
    weak_pose, weak_shift = state_poses()[2]["Weakened"]
    weak = {k: v for k, v in weak_pose.items() if k != "Head" and not k.startswith(("Mid", "Hind"))}
    out["Weaken"] = [
        _key(0.0),
        _key(0.2, "out", arm(_jaws({"Hips": (2, -4, 5), "Pro1": (8, 14, 4), "Pro2": (4, 8, 0)}, 14), (16, 4, 8), (8, 0, 4), -70, 40), (0.0, 0.0, 0.8), None, (6.0, 16.0, 10.0)),
        _key(0.62, "smooth", arm(dict(weak, Pro1=(-16, -4, -4)), (22, 2, 8), (-20, 0, 2), -82, 70), (0, -4.8, -0.4), None, (-34.0, -6.0, -6.0)),
        _key(1.7, "smooth", weak, weak_shift, None, -30.0),
    ]
    return out


# ---------- what the game plays: generated, never edited by hand ----------
_continuous, _lua = P._continuous, P._lua
MOVES_FPS = 30
STEPS = 32


def _joints():
    return [n for n in BONES if n != "Root"]


def _vals(pose, shift, base):
    out = {}
    for n in _joints():
        out[n] = list(_continuous(pose.get(n, (0, 0, 0)), base.get(n, (0, 0, 0))[:3]))
    out["Hips"] = out["Hips"] + [shift[1], shift[2]]
    return out


def _planted(keys):
    length = keys[-1]["at"]
    rows = {leg: [] for leg in LEGS}
    for f in range(int(length * MOVES_FPS) + 1):
        t = min(f / MOVES_FPS, length)
        a = b = keys[-1]
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if t <= b["at"]:
                break
        for leg in LEGS:
            ya, yb = a["feet"].get(leg, (0, 0, 0, 0))[1], b["feet"].get(leg, (0, 0, 0, 0))[1]
            rows[leg].append(0 if max(ya, yb) > 0.05 else 1)
    return rows


def blade_tips(pose, shift):
    """Where each blade's hook ends: the tibia's tip plus its hook, drawn in the same way as the mesh."""
    st = fk(pose, shift)
    out = {}
    for tag in ("Left", "Right"):
        r, a = st[tag + "Tibia"]
        rest = _REST[tag + "Tibia"]
        u = V((0, -1, -0.05))
        out[tag] = a + r @ (rest + rest.normalized() * 1.5 + u * 1.5)
    return out


def anchors():
    cl = clips()
    p, s = clip_pose(0.6, cl["Scythe"])
    tips = blade_tips(p, s)
    st = fk(p, s)
    out = {"ScytheLeft": tuple(round(c, 1) for c in tips["Left"]), "ScytheRight": tuple(round(c, 1) for c in tips["Right"])}
    p, s = clip_pose(0.93, cl["BladeWave"])
    st = fk(p, s)
    c = st["Pro2"][1]
    out["Wave"] = (0.0, round(c.y, 1), round(c.z - 4, 1))
    return out


def write_clips(path=None):
    path = path or os.path.join(W.REPO, "src", "client", "Guardians", "GuardianRigs", "MantisSageClips.lua")
    stand, s0, states = state_poses()
    base = {n: stand.get(n, (0, 0, 0)) for n in _joints()}
    lines = ["-- Generated by tools/blender/guardians/mantis_sage_v2.py (write_clips): do not edit by hand. Angles in degrees, [pitch, yaw, roll];",
             "-- the hips also carry [lift, slide]. Poses and Moves are whole poses; Gaits are changes from how it stands.", "local Clips = {}",
             "Clips.Fps = %d" % MOVES_FPS, "Clips.Steps = %d" % STEPS, "Clips.Anchors = " + _lua({k: list(v) for k, v in anchors().items()}),
             "Clips.Strides = " + _lua({n: stride_of(g) for n, g in GAITS.items()}), "Clips.Duty = " + _lua({n: g["duty"] for n, g in GAITS.items()}),
             "Clips.Phase = " + _lua({n: dict(g["phase"]) for n, g in GAITS.items()})]
    lines.append("Clips.Poses = {")
    for name, (pose, shift) in states.items():
        lines.append(name + "=" + _lua(_vals(pose, shift, base)) + ",")
    lines.append("}")
    standv = _vals(stand, s0, base)
    # (not written: the game never reads the standing pose; it is the Guardian pose, and the gaits are measured from it)
    lines.append("Clips.Gaits = {")
    for name in GAITS:
        table = {n: [] for n in _joints()}
        prev = base
        for f in range(STEPS):
            pose, shift = gait_pose(name, f / STEPS)
            v = _vals(pose, shift, prev)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            for n in _joints():
                table[n].append([v[n][k] - standv[n][k] for k in range(len(v[n]))])
        keep = {n: t for n, t in table.items() if any(abs(x) > 0.3 for row in t for x in row)}
        lines.append(name + "=" + _lua(keep) + ",")
    lines.append("}")
    cl = clips()
    lines.append("Clips.Moves = {")
    worst = {}
    for name, keys in cl.items():
        frames, prev = [], base
        length = keys[-1]["at"]
        for f in range(int(length * MOVES_FPS) + 1):
            pose, shift = clip_pose(min(f / MOVES_FPS, length), keys)
            v = _vals(pose, shift, prev)
            for n in _joints():
                d = max(abs(v[n][k] - prev[n][k]) for k in range(3))
                if f and d > worst.get(name, (0, ""))[0]:
                    worst[name] = (round(d, 1), n, f)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            frames.append(v)
        moved = [n for n in _joints() if any(abs(fr[n][k] - frames[0][n][k]) > 0.2 for fr in frames for k in range(3)) or abs(frames[0][n][0] - standv[n][0]) > 0.2]
        lines.append(name + "=" + _lua([{n: fr[n] for n in moved} for fr in frames]) + ",")
    lines.append("}")
    lines.append("Clips.Plants = {")
    for name, keys in cl.items():
        lines.append(name + "=" + _lua(_planted(keys)) + ",")
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    return {"bytes": os.path.getsize(path), "biggest step": worst, "anchors": anchors()}


# ---------- reviewing ----------
def _hide_rig():
    bpy.data.objects[RIG].hide_render = True


VIEWS = {"front": (0, 6), "three": (-38, 10), "left": (-90, 4), "back": (180, 8), "right": (90, 4), "top": (-90, 70)}


def _floor():
    if bpy.data.objects.get("MS2_Floor"):
        return
    me = bpy.data.meshes.new("MS2_Floor")
    me.from_pydata([W.rb(-70, 0, -70), W.rb(70, 0, -70), W.rb(70, 0, 70), W.rb(-70, 0, 70)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("MS2_Floor", me)
    bpy.context.scene.collection.objects.link(floor)


def review_form(path, pose=None, shift=(0, 0, 0), views=("front", "three", "left", "back", "right", "top"), size=560, columns=3, distance=118, centre=(0, 16, 5)):
    scene, cam = T._review_scene(size)
    _hide_rig()
    set_pose(pose or {}, shift)
    tmp = path + ".tile.png"
    tiles = []
    for v in views:
        yaw, pitch = VIEWS[v]
        tiles.append(T._shot(scene, cam, yaw, pitch, distance, W.rb(*centre), size, tmp))
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


def filmstrip(path, frames, yaw=-90, pitch=4, size=380, columns=6, distance=118, centre=(0, 15, 3)):
    scene, cam = T._review_scene(size)
    _hide_rig()
    _floor()
    tmp = path + ".tile.png"
    tiles = []
    for pose, shift in frames:
        set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, yaw, pitch, distance, W.rb(*centre), size, tmp))
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


# ---------- the final stage ----------
def make_lows(pieces):
    import egg_bake as B
    coll = bpy.data.collections[COLLECTION]
    lows = {}
    for name in PIECES:
        for o in pieces[name]:
            paint(o)
        low = B.make_low(PREFIX + name, pieces[name], coll, PIECES[name])
        low.name = PREFIX + name
        for b in BONES:
            low.vertex_groups.new(name=b)
        tidy(low)
        lows[name] = low
    return lows


def _group_of(bone):
    """Bones whose pieces are one solid thing bake together."""
    for prefix in ("Abd", "Pro", "Beard", "LeftAnt", "RightAnt", "RobeMid", "RobeLeft", "RobeRight"):
        if bone.startswith(prefix):
            return prefix
    return bone


def _islands(low):
    parent = list(range(len(low.data.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in low.data.edges:
        parent[find(e.vertices[0])] = find(e.vertices[1])
    out = {}
    for v in low.data.vertices:
        out.setdefault(find(v.index), []).append(v)
    return list(out.values())


def _bake_leaves(name, hi, low):
    """Leaves that lie on one another would catch each other's rays: every leaf is baked alone, its island matched to its leaf by where they sit."""
    import egg_bake as B
    bpy.context.scene.cycles.device = "GPU"
    saved_co = [v.co.copy() for v in low.data.vertices]
    centres = [(o, sum((v.co for v in o.data.vertices), V()) / len(o.data.vertices)) for o in hi]
    away = {o.name: V((90.0 * (i + 1), 0, 0)) for i, o in enumerate(hi)}
    for o in hi:
        o.location = away[o.name]
    for vs in _islands(low):
        c = sum((v.co for v in vs), V()) / len(vs)
        o = min(centres, key=lambda e: (e[1] - c).length)[0]
        for v in vs:
            v.co = v.co + away[o.name]
    low.data.update()
    bpy.context.view_layer.update()
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    try:
        B.bake(PREFIX + name, hi, low, samples=12, **BAKES[name])
    finally:
        B.EGG_DIR = saved
        for v, c in zip(low.data.vertices, saved_co):
            v.co = c
        low.data.update()
        for o in hi:
            o.location = (0, 0, 0)
        bpy.context.view_layer.update()


def bake_piece(name, hi, low):
    """Each limb is baked by itself, moved far from the others: a culm sits inside its neighbour at the joint, and what was hidden there comes into view when
    the joint turns, so it must not bake dark. The materials read object coordinates and UVs, so moving the objects changes nothing else."""
    import egg_bake as B
    bpy.context.scene.cycles.device = "GPU"
    names = {g.index: _group_of(g.name) for g in low.vertex_groups}
    keys = sorted(set(names.values()))
    offset = {k: V((90.0 * (i + 1), 0, 0)) for i, k in enumerate(keys)} if name in ("Skin", "Blades", "Fine") else {}
    if name == "Robe":
        return _bake_leaves(name, hi, low)
    saved_co = [v.co.copy() for v in low.data.vertices]

    def owner(weights):
        tally = {}
        for gi, w in weights:
            tally[names[gi]] = tally.get(names[gi], 0.0) + w
        return max(tally, key=tally.get) if tally else keys[0]

    if offset:
        for o in hi:                                                          # a whole piece moves together, by the limb that owns most of it
            lookup = {g.index: g.name for g in o.vertex_groups}
            o.location = offset[owner([(next(i for i, n in enumerate(low.vertex_groups.keys()) if n == lookup[g.group]), g.weight) for v in o.data.vertices for g in v.groups])]
        for vs in _islands(low):
            d = offset[owner([(g.group, g.weight) for v in vs for g in v.groups])]
            for v in vs:
                v.co = v.co + d
        low.data.update()
        bpy.context.view_layer.update()
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    try:
        B.bake(PREFIX + name, hi, low, samples=12, **BAKES[name])
    finally:
        B.EGG_DIR = saved
        for v, c in zip(low.data.vertices, saved_co):
            v.co = c
        low.data.update()
        for o in hi:
            o.location = (0, 0, 0)
        bpy.context.view_layer.update()


GAME_NAMES = {PREFIX + n: n for n in PIECES}
GAME_NAMES.update({"MS2_Pupils": "Pupils", "MS2_LeftEdge": "LeftEdge", "MS2_RightEdge": "RightEdge"})


def rig_all(pieces, lows, glows):
    out = {name: settle_weights(lows[name]) for name in PIECES}
    for o, _, bone in glows.values():
        o.vertex_groups.clear()
        o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
        attach(o)
    game = set(GAME_NAMES) | {RIG}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name not in game:
            o.hide_render = True
            o.hide_viewport = True
    return out


def tally():
    return {GAME_NAMES[o.name]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.name in GAME_NAMES}


def export():
    """assets/guardians/MantisSageV2.fbx: every game piece, skinned, and the skeleton, bound as modelled, the maps inside."""
    O = bpy.data.objects
    set_pose({})
    arm_ob = O[RIG]
    arm_ob.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    for src in GAME_NAMES:
        O[src].hide_viewport = False
        O[src].select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    for src, name in list(GAME_NAMES.items()):
        O[src].name = name
    path = os.path.join(OUT, "MantisSageV2.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X")
    return path, os.path.getsize(path) // 1024


def write_placement(path=None):
    """Placements/MantisSageSkinned.lua: how the store step fits the import."""
    path = path or os.path.join(W.REPO, "src", "worldbuild", "Placements", "MantisSageSkinned.lua")
    fit = {"Hips": BONES["Hips"][1], "Head": BONES["Head"][1], "HindLeftFemur": BONES["HindLeftFemur"][1], "MidRightTibia": BONES["MidRightTibia"][1]}
    vec = lambda v: "Vector3.new(%s)" % ", ".join("%.4g" % c for c in v)
    text = ["-- The Bamboo Mantis Sage with a skeleton (tools/blender/guardians/mantis_sage_v2.py writes this file, assets/guardians/MantisSageV2.fbx). Used by", "-- GuardianBuilder.storeSkinned.", "return {", '    Rig = "MantisSageSkinned",', "    Fit = {"]
    for k, v in fit.items():
        text.append("        %s = %s," % (k, vec(v)))
    text += ["    },", "    Glow = {", "        Pupils = Color3.fromRGB(255, 144, 0),", "        LeftEdge = Color3.fromRGB(0, 200, 110),", "        RightEdge = Color3.fromRGB(0, 200, 110),", "    },", "}", ""]
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(text))
    return path

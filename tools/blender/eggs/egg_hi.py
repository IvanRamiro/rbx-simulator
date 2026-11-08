"""High-detail egg building (run inside Blender): the sculpt-level source the game mesh is baked
from (egg_bake.py), the same way the sculpted pets are made.

Points are authored in Roblox space through egg_kit (x right, y up, the egg's front toward +z,
its bottom at the origin) and converted to Blender space when the mesh is built.

Builders (all add to a Hi mesh, which carries per-face materials and UVs):
- htube: a smooth tube along a curve with UVs running along it (u round, v along, in units), so
  bark grain follows the branch; optional knots.
- leaf: a curled, folded blade with UVs across (u) and along (v), for leaf and petal shaders.
- foliage: a lumpy, merged clump of leaves (voxel remeshed lobes), for tree crowns.

Materials (procedural Cycles shaders, baked to textures): jade, bark, leaf, blossom crystal,
petal, wood, heartwood, foliage, gold, obsidian, feather; for Moonlit Isle night sky, moon
silver, moonstone, pearl and cloud; for Origin Abyss seal-stone, bronze, void glass, strata and
fossil. Each has a node named "BAKE_ROUGH" and one named
"BAKE_METAL" whose first output is the value egg_bake bakes into the roughness and metalness maps.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import egg_kit as K

W = K.W
V = Vector
TAU = K.TAU


# ---------- mesh building ----------
class Hi:
    """Faces with per-corner UVs and a material index each, in Roblox space."""

    def __init__(self):
        self.verts, self.faces, self.uvs, self.mats = [], [], [], []

    def v(self, p):
        self.verts.append(tuple(W.rb(p[0], p[1], p[2])))
        return len(self.verts) - 1

    def f(self, idx, uv, mat=0):
        self.faces.append(list(idx))
        self.uvs.append(list(uv))
        self.mats.append(mat)

    def facing(self, idx, uv, outward, mat=0):
        """A face wound to face along `outward` (Roblox space): Roblox, like EEVEE, culls back
        faces, so open pieces such as gems must face the viewer."""
        a, b, c = (V(self.verts[i]) for i in idx[:3])
        if (b - a).cross(c - a).dot(W.rb(*outward)) < 0:
            idx, uv = list(idx)[::-1], list(uv)[::-1]
        self.f(idx, uv, mat)

    def object(self, name, coll, materials, smooth=True, weld=1e-5):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        layer = me.uv_layers.new(name="UVMap")
        for poly, uv, m in zip(me.polygons, self.uvs, self.mats):
            poly.material_index = m
            for li, c in zip(poly.loop_indices, uv):
                layer.data[li].uv = c
        for m in materials:
            me.materials.append(m)
        me.validate()
        if weld:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
            bm.to_mesh(me)
            bm.free()
        for p in me.polygons:
            p.use_smooth = smooth
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        return o


def apply_modifiers(obj, mods):
    """Adds modifiers [(type, {prop: value})] and applies them all, keeping the object."""
    for kind, props in mods:
        md = obj.modifiers.new(kind, kind)
        for k, v in props.items():
            setattr(md, k, v)
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    bpy.data.meshes.remove(old)
    return obj


def frames(curve):
    """Parallel-transported frames (tangent, side, binormal) along a curve: no flips."""
    n = len(curve)
    tangents = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = V((0, 1, 0)) if abs(tangents[0].y) < 0.9 else V((1, 0, 0))
    s = tangents[0].cross(ref).normalized()
    out = []
    for t in tangents:
        s = (s - t * s.dot(t)).normalized()
        out.append((t, s, t.cross(s)))
    return out


def htube(hi, pts, radius_fn, sides=10, per=6, mat=0, uv_scale=4.0, tip=True, knots=None, seed=0, wobble=1.0):
    """A smooth tube through `pts` (Roblox space). radius_fn(t), t 0..1 along it. knots: number of
    knobbly swellings along it (bark). wobble scales its uneven swelling and pinching (0: perfectly
    round, for polished pieces). UVs: u round the tube, v = length * uv_scale."""
    curve = [V(p) for p in W.catmull([tuple(p) for p in pts], per)]
    n = len(curve)
    fr = frames(curve)
    lengths = [0.0]
    for i in range(1, n):
        lengths.append(lengths[-1] + (curve[i] - curve[i - 1]).length)
    rnd = random.Random(seed)
    knot_at = [(rnd.uniform(0.08, 0.92), rnd.uniform(0, TAU), rnd.uniform(0.35, 0.65)) for _ in range(knots or 0)]
    rings = []
    for i, c in enumerate(curve):
        t_, s, b = fr[i]
        tt = i / (n - 1)
        r = radius_fn(tt)
        ring = []
        for k in range(sides + 1):
            a = TAU * k / sides
            bump = 0.0
            for kt, ka, kh in knot_at:   # a knot: a swelling on one side of the branch
                d = abs(tt - kt) / 0.045
                da = math.cos(a - ka)
                if d < 1 and da > 0:
                    bump += kh * (1 - d * d) * da * da
            bump += wobble * (0.07 * math.sin(a * 3 + tt * 23 + seed) + 0.05 * math.sin(tt * 61 + seed * 2))   # uneven, swelling and pinching
            ring.append(hi.v(c + (s * math.cos(a) + b * math.sin(a)) * r * (1 + bump)))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            v0, v1 = lengths[i] * uv_scale, lengths[i + 1] * uv_scale
            hi.f([rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]],
                 [(k / sides, v0), ((k + 1) / sides, v0), ((k + 1) / sides, v1), (k / sides, v1)], mat)
    if tip:
        end = curve[-1] + fr[-1][0] * radius_fn(1.0) * 1.5
        e = hi.v(end)
        v1 = lengths[-1] * uv_scale
        for k in range(sides):
            hi.f([rings[-1][k], rings[-1][k + 1], e], [(k / sides, v1), ((k + 1) / sides, v1), ((k + 0.5) / sides, v1 + 0.2)], mat)
    return curve


def leaf(hi, base, direction, normal, length, width, mat=0, fold=0.25, curl=0.2, twist=0.0, steps=10, across=4,
         shape=0.75, notch=0.0, cup=0.0):
    """A blade (leaf or petal): from `base` along `direction`, its face toward `normal`. Folded
    along the midrib (`fold`: the midrib sinks by fold * width), curled toward `normal` along its
    length, twisted by `twist` radians tip-wards, cupped across by `cup`. notch > 0 cuts a notch at
    the tip (petals). UVs: u across 0..1 (midrib at 0.5), v along 0..1. One-sided: give it
    thickness with solidify()."""
    d = V(direction).normalized()
    n = V(normal)
    n = (n - d * n.dot(d)).normalized()
    s0 = d.cross(n).normalized()
    b = V(base)
    grid = []
    for i in range(steps + 1):
        t = i / steps
        w = width * math.sin(math.pi * min(1.0, t * 0.97 + 0.03)) ** shape * (1.1 - 0.2 * t)
        tip_cut = notch * max(0.0, (t - 0.85) / 0.15)
        a = twist * t
        s = s0 * math.cos(a) + n.cross(s0) * math.sin(a) * -1
        nn = s.cross(d).normalized() * -1 if s.cross(d).dot(n) < 0 else s.cross(d).normalized()
        c = b + d * length * t + n * (curl * length * t * t)
        row = []
        for j in range(across + 1):
            x = -1 + 2 * j / across
            lift = -fold * w * (1 - abs(x)) + cup * w * x * x
            p = c + s * w * x + nn * lift - d * length * tip_cut * (1 - abs(x)) * 0.12
            row.append(hi.v(p))
        grid.append(row)
    for i in range(steps):
        for j in range(across):
            uv = [(j / across, i / steps), ((j + 1) / across, i / steps), ((j + 1) / across, (i + 1) / steps), (j / across, (i + 1) / steps)]
            q = [grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]
            pa, pb, pc = (V(hi.verts[q[k]]) for k in range(3))
            want = W.rb(*n)
            if (pb - pa).cross(pc - pa).dot(want) < 0:
                q, uv = q[::-1], uv[::-1]
            hi.f(q, uv, mat)


def solidify(obj, thickness=0.012):
    return apply_modifiers(obj, [("SOLIDIFY", {"thickness": thickness, "offset": 0.0, "use_even_offset": True})])


def foliage(name, coll, material, lobes, voxel=0.035, roughness=0.06):
    """A lumpy crown of leaves: lobes [(centre (Roblox space), radius)], merged by a voxel remesh
    and roughened so the outline breaks into leafy clumps."""
    bm = bmesh.new()
    for c, r in lobes:
        m = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
        for v in m["verts"]:
            v.co += W.rb(*c)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    tex = bpy.data.textures.get("FoliageClumps") or bpy.data.textures.new("FoliageClumps", "VORONOI")
    tex.noise_scale = 0.09
    apply_modifiers(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel}),
                        ("DISPLACE", {"texture": tex, "strength": roughness, "mid_level": 0.6, "texture_coords": "GLOBAL"}),
                        ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# ---------- procedural materials ----------
class _Graph:
    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m, self.t = m, m.node_tree
        for nd in list(self.t.nodes):
            self.t.nodes.remove(nd)
        self.out = self.t.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.t.nodes.new("ShaderNodeBsdfPrincipled")
        self.t.links.new(self.bsdf.outputs[0], self.out.inputs["Surface"])

    def n(self, kind, name=None, **values):
        nd = self.t.nodes.new(kind)
        if name:
            nd.name = nd.label = name
        for k, v in values.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
            else:
                nd.inputs[k].default_value = v
        return nd

    def link(self, a, b):
        self.t.links.new(a, b)

    def ramp(self, fac, stops, interp="LINEAR"):
        r = self.n("ShaderNodeValToRGB")
        r.color_ramp.interpolation = interp
        els = r.color_ramp.elements
        while len(els) > 1:
            els.remove(els[-1])
        els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
        for pos, col in stops[1:]:
            e = els.new(pos)
            e.color = (*col, 1)
        self.link(fac, r.inputs["Fac"])
        return r.outputs["Color"]

    def math(self, op, a, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                nd.inputs[i].default_value = x
            else:
                self.link(x, nd.inputs[i])
        return nd.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        if isinstance(fac, (int, float)):
            nd.inputs["Factor"].default_value = fac
        else:
            self.link(fac, nd.inputs["Factor"])
        for sock, x in ((nd.inputs[6], a), (nd.inputs[7], b)):
            if isinstance(x, tuple):
                sock.default_value = (*x, 1)
            else:
                self.link(x, sock)
        return nd.outputs[2]

    def ao(self, color, distance=0.12, floor=0.4):
        """Darkens crevices: the ambient occlusion is baked into the colour map. Local to each piece:
        while baking, the game mesh lies on the surface and would occlude everything."""
        a = self.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
        a.inputs["Distance"].default_value = distance
        k = self.math("MULTIPLY_ADD", a.outputs["AO"], 1 - floor)
        k.node.inputs[2].default_value = floor
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
        nd.inputs["Factor"].default_value = 1.0
        self.link(color, nd.inputs[6])
        self.link(k, nd.inputs[7])
        return nd.outputs[2]

    def bw(self, color):
        nd = self.n("ShaderNodeRGBToBW")
        self.link(color, nd.inputs[0])
        return nd.outputs[0]

    def bump(self, height, strength, distance=0.02, normal=None):
        b = self.n("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height, b.inputs["Height"])
        if normal is not None:
            self.link(normal, b.inputs["Normal"])
        return b.outputs["Normal"]

    def finish(self, color, roughness, metal=0.0, normal=None):
        self.link(color, self.bsdf.inputs["Base Color"])
        rough = self._value("BAKE_ROUGH", roughness)
        met = self._value("BAKE_METAL", metal)
        self.link(rough, self.bsdf.inputs["Roughness"])
        self.link(met, self.bsdf.inputs["Metallic"])
        if normal is not None:
            self.link(normal, self.bsdf.inputs["Normal"])
        return self.m

    def _value(self, name, x):
        """A named node whose output is the value (egg_bake bakes these into maps)."""
        nd = self.n("ShaderNodeMath", name=name, operation="ADD")
        nd.inputs[1].default_value = 0.0
        if isinstance(x, (int, float)):
            nd.inputs[0].default_value = x
        else:
            self.link(x, nd.inputs[0])
        return nd.outputs[0]

    def coords(self, kind="Object"):
        return self.n("ShaderNodeTexCoord").outputs[kind]

    def sep(self, vec):
        s = self.n("ShaderNodeSeparateXYZ")
        self.link(vec, s.inputs[0])
        return s.outputs


def mat_jade(name="EggJade"):
    """Cut jade: each facet its own green (random per island), soft marbling of paler veins,
    lighter toward the crown, bevelled facet edges, crevices darkened."""
    g = _Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    tone = g.ramp(geo.outputs["Random Per Island"], [(0.0, (0.004, 0.07, 0.025)), (0.3, (0.012, 0.17, 0.06)),
                                                      (0.65, (0.03, 0.3, 0.12)), (1.0, (0.1, 0.48, 0.24))])
    co = g.coords()
    cloud = g.n("ShaderNodeTexNoise", **{"Scale": 2.2, "Detail": 4.0, "Roughness": 0.5})
    g.link(co, cloud.inputs["Vector"])
    tone = g.mix(g.math("MULTIPLY", cloud.outputs["Fac"], 0.35), tone, (0.08, 0.42, 0.2))      # cloudy depth in the stone
    marble = g.n("ShaderNodeTexNoise", **{"Scale": 1.7, "Detail": 8.0, "Roughness": 0.6, "Distortion": 1.6})
    g.link(co, marble.inputs["Vector"])
    veins = g.ramp(marble.outputs["Fac"], [(0.0, (0, 0, 0)), (0.485, (0, 0, 0)), (0.5, (1, 1, 1)), (0.515, (0, 0, 0)), (1.0, (0, 0, 0))])
    col = g.mix(g.math("MULTIPLY", g.bw(veins), 0.28), tone, (0.3, 0.72, 0.48))
    z = g.sep(co)[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", z, 1.4, clamp=True), 0.25), col, (0.2, 0.62, 0.38))
    col = g.ao(col, 0.1, 0.35)
    bevel = g.n("ShaderNodeBevel", samples=8)
    bevel.inputs["Radius"].default_value = 0.03
    nrm = g.bump(marble.outputs["Fac"], 0.12, 0.01, bevel.outputs["Normal"])
    return g.finish(col, 0.14, 0.0, nrm)


def mat_bark(name="EggBark", moss=0.0, base=(0.13, 0.075, 0.035), ridge=(0.6, 0.42, 0.17)):
    """Gnarled bark: stringy ridges running along the branch (UV v), dark creases, bronze-gold
    catching the light on the ridges, optional moss on the upward faces."""
    g = _Graph(name)
    uv = g.coords("UV")
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (4.0, 0.9, 1.0)
    g.link(uv, mp.inputs["Vector"])
    wave = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", **{"Scale": 1.0, "Distortion": 11.0, "Detail": 8.0, "Detail Scale": 2.2, "Detail Roughness": 0.7})
    g.link(mp.outputs[0], wave.inputs["Vector"])
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 22.0, "Detail": 6.0, "Roughness": 0.6})
    g.link(g.coords(), fine.inputs["Vector"])
    blotch = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 3.0, "Roughness": 0.5})
    g.link(g.coords(), blotch.inputs["Vector"])
    h = g.math("ADD", g.math("ADD", g.math("MULTIPLY", wave.outputs["Fac"], 0.55), g.math("MULTIPLY", fine.outputs["Fac"], 0.25)),
               g.math("MULTIPLY", blotch.outputs["Fac"], 0.35))
    col = g.ramp(h, [(0.0, base), (0.45, tuple(0.5 * (a + b) for a, b in zip(base, ridge))), (0.8, ridge), (1.0, tuple(min(1, c * 1.25) for c in ridge))])
    if moss > 0:
        geo = g.n("ShaderNodeNewGeometry")
        up = g.sep(geo.outputs["Normal"])[2]
        mn = g.n("ShaderNodeTexNoise", **{"Scale": 5.0, "Detail": 4.0})
        g.link(g.coords(), mn.inputs["Vector"])
        mask = g.math("MULTIPLY", g.math("MULTIPLY", g.math("SUBTRACT", up, 0.35, clamp=True), 2.2),
                      g.math("SUBTRACT", g.math("MULTIPLY", mn.outputs["Fac"], 2.2), 0.8, clamp=True))
        mask = g.math("MINIMUM", g.math("MULTIPLY", mask, moss), 1.0)
        mossc = g.ramp(fine.outputs["Fac"], [(0.3, (0.12, 0.3, 0.04)), (0.7, (0.32, 0.55, 0.1))])
        col = g.mix(mask, col, mossc)
    col = g.ao(col, 0.08, 0.3)
    nrm = g.bump(h, 0.7, 0.02)
    # the ridges are polished by age: a little glossier than the creases
    return g.finish(col, g.math("SUBTRACT", 0.8, g.math("MULTIPLY", h, 0.3)), 0.0, nrm)


def mat_leaf(name="EggLeaf", base=(0.04, 0.24, 0.05), mid=(0.16, 0.52, 0.12), tip=(0.42, 0.78, 0.22), rib=(0.6, 0.85, 0.35)):
    """A leaf: darker at the stem, lighter toward the tip, a pale midrib and paired side veins
    (UV u across, v along), a darker rim, fine speckle."""
    g = _Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, base), (0.45, mid), (1.0, tip)])
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    midrib = g.math("LESS_THAN", du, 0.035)
    veins = g.math("LESS_THAN", g.math("MODULO", g.math("MULTIPLY", g.math("SUBTRACT", v, g.math("MULTIPLY", du, 1.3)), 7.0), 1.0), 0.09)
    veins = g.math("MULTIPLY", veins, g.math("LESS_THAN", du, 0.44))
    lines = g.math("MAXIMUM", midrib, g.math("MULTIPLY", veins, 0.7))
    col = g.mix(g.math("MULTIPLY", lines, 0.7), col, rib)
    rim = g.math("GREATER_THAN", du, 0.45)
    col = g.mix(g.math("MULTIPLY", rim, 0.45), col, tuple(c * 0.55 for c in base))
    sp = g.n("ShaderNodeTexNoise", **{"Scale": 40.0, "Detail": 3.0})
    g.link(g.coords(), sp.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", sp.outputs["Fac"], 0.18), col, tuple(c * 0.7 for c in mid))
    col = g.ao(col, 0.06, 0.45)
    nrm = g.bump(g.math("SUBTRACT", 1.0, lines), 0.35, 0.006)
    return g.finish(col, 0.5, 0.0, nrm)


def mat_crystal(name="EggBlossomCrystal", stops=None, vein=(0.95, 0.68, 0.22), crown=(1.0, 0.86, 0.93)):
    """Faceted blossom crystal (pink by default): a tone per facet, paler toward the crown,
    bevelled edges, and fine gold veins running through it like mended cracks (metallic)."""
    g = _Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    stops = stops or [(0.0, (0.72, 0.2, 0.5)), (0.4, (0.88, 0.38, 0.66)), (0.75, (0.96, 0.56, 0.78)), (1.0, (1.0, 0.76, 0.88))]
    col = g.ramp(geo.outputs["Random Per Island"], stops)
    co = g.coords()
    z = g.sep(co)[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", z, 1.4, clamp=True), 0.3), col, crown)
    vn = g.n("ShaderNodeTexNoise", **{"Scale": 1.3, "Detail": 3.0, "Roughness": 0.45, "Distortion": 0.3})
    g.link(co, vn.inputs["Vector"])
    vmask = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", vn.outputs["Fac"], 0.5)), 0.007)
    col = g.mix(vmask, col, vein)
    col = g.ao(col, 0.1, 0.45)
    bevel = g.n("ShaderNodeBevel", samples=8)
    bevel.inputs["Radius"].default_value = 0.025
    nrm = g.bump(g.math("SUBTRACT", 1.0, vmask), 0.25, 0.006, bevel.outputs["Normal"])
    return g.finish(col, 0.22, g.math("MULTIPLY", vmask, 0.5), nrm)   # the gold veins are half metal: fully metal, they read black


def mat_petal(name="EggPetal"):
    """A lotus petal: deep magenta at its base through pink to a near-white tip (UV v), fine
    veins running base to tip, a paler rim."""
    g = _Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, (0.55, 0.05, 0.32)), (0.35, (0.92, 0.32, 0.62)), (0.75, (1.0, 0.68, 0.86)), (1.0, (1.0, 0.92, 0.97))])
    w = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", **{"Scale": 9.0, "Distortion": 1.5, "Detail": 2.0})
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.15, 1.0)
    g.link(g.coords("UV"), mp.inputs["Vector"])
    g.link(mp.outputs[0], w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", w.outputs["Fac"], 0.6, clamp=True), 0.5), col, (0.75, 0.2, 0.5))
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    col = g.mix(g.math("MULTIPLY", g.math("GREATER_THAN", du, 0.44), 0.4), col, (1.0, 0.95, 0.98))
    col = g.ao(col, 0.06, 0.5)
    nrm = g.bump(w.outputs["Fac"], 0.15, 0.004)
    return g.finish(col, 0.42, 0.0, nrm)


def mat_gold(name="EggGold"):
    g = _Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 18.0, "Detail": 4.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.78, 0.52, 0.16)), (0.7, (1.0, 0.8, 0.38))])
    col = g.ao(col, 0.05, 0.35)
    # 0.6, not 1: fully metallic gold shows black wherever it has nothing bright to reflect
    return g.finish(col, 0.32, 0.6, g.bump(n.outputs["Fac"], 0.1, 0.004))


def mat_obsidian(name="EggObsidian", tones=None, vein=(1.0, 0.3, 0.02), vein_hot=(1.0, 0.68, 0.12), heat=(0.85, 0.16, 0.02),
                 heat_reach=0.16):
    """Volcanic rock plates: each plate its own dark tone (random per island), a faint glassy
    sheen, thin branching veins of molten lava running across them (bright orange with a yellow
    core), and the plates' edges and crevices heated red (ambient occlusion turned to heat).
    heat_reach is how far the heat reaches out of a crevice: an egg's scale by default; small
    rocks need much less, or every surface counts as a crevice."""
    g = _Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    tones = tones or [(0.0, (0.012, 0.008, 0.007)), (0.5, (0.028, 0.019, 0.016)), (1.0, (0.05, 0.034, 0.028))]
    col = g.ramp(geo.outputs["Random Per Island"], tones)
    co = g.coords()
    mott = g.n("ShaderNodeTexNoise", **{"Scale": 9.0, "Detail": 6.0, "Roughness": 0.6})
    g.link(co, mott.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", mott.outputs["Fac"], 0.5), col, tuple(c * 2.2 + 0.01 for c in tones[-1][1]))
    # lava veins: thin ridges of a distorted noise, branching across the plates
    vn = g.n("ShaderNodeTexNoise", **{"Scale": 2.2, "Detail": 4.0, "Roughness": 0.5, "Distortion": 0.4})
    g.link(co, vn.inputs["Vector"])
    patch = g.n("ShaderNodeTexNoise", **{"Scale": 1.6, "Detail": 2.0})      # veins run only in patches
    g.link(co, patch.inputs["Vector"])
    on_patch = g.math("GREATER_THAN", patch.outputs["Fac"], 0.5)
    d = g.math("ABSOLUTE", g.math("SUBTRACT", vn.outputs["Fac"], 0.5))
    vein_m = g.math("MULTIPLY", g.math("LESS_THAN", d, 0.013), on_patch)
    core_m = g.math("MULTIPLY", g.math("LESS_THAN", d, 0.005), on_patch)
    col = g.mix(vein_m, col, vein)
    col = g.mix(core_m, col, vein_hot)
    # heat: crevices (where the plates meet the glowing core) glow red instead of going dark
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = heat_reach
    hot = g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.55)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", hot, 1.4), 1.0), col, heat)
    bevel = g.n("ShaderNodeBevel", samples=8)
    bevel.inputs["Radius"].default_value = 0.02
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", mott.outputs["Fac"], 0.6), g.math("MULTIPLY", vein_m, -0.5)), 0.4, 0.008, bevel.outputs["Normal"])
    return g.finish(col, g.math("ADD", 0.3, g.math("MULTIPLY", mott.outputs["Fac"], 0.25)), 0.0, nrm)


def mat_feather(name="EggFeather", base=(0.62, 0.04, 0.015), mid=(1.0, 0.3, 0.03), tip=(1.0, 0.68, 0.12)):
    """A flame feather (UV u across, v along): fiery red at its root through orange to pale gold
    at its tip, a pale shaft down the middle, fine barbs angled up from the shaft, the edges
    darker."""
    g = _Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, base), (0.4, mid), (0.85, tip), (1.0, tuple(min(1.0, c * 1.4 + 0.05) for c in tip))])
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    shaft = g.math("LESS_THAN", du, 0.03)
    barbs = g.math("LESS_THAN", g.math("MODULO", g.math("MULTIPLY", g.math("SUBTRACT", v, g.math("MULTIPLY", du, 0.9)), 30.0), 1.0), 0.28)
    col = g.mix(g.math("MULTIPLY", barbs, 0.4), col, tuple(c * 0.45 for c in mid))
    col = g.mix(g.math("MULTIPLY", shaft, 0.7), col, tuple(min(1.0, c * 1.2 + 0.05) for c in tip))
    col = g.mix(g.math("MULTIPLY", g.math("GREATER_THAN", du, 0.42), 0.5), col, tuple(c * 0.6 for c in base))
    col = g.ao(col, 0.05, 0.45)
    nrm = g.bump(g.math("ADD", barbs, g.math("MULTIPLY", shaft, 2.0)), 0.3, 0.004)
    return g.finish(col, 0.45, 0.0, nrm)


def _stars(g, co, scale, size, keep):
    """Soft round stars scattered over the surface: a Voronoi cell in `keep` of them holds one,
    each its own size (up to `size` of a cell), fading from its centre. Returns 0..1."""
    vo = g.n("ShaderNodeTexVoronoi", **{"Scale": scale})
    g.link(co, vo.inputs["Vector"])
    rnd = g.sep(vo.outputs["Color"])
    radius = g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", rnd[0], 0.7), 0.3), size)
    glow = g.math("SUBTRACT", 1.0, g.math("DIVIDE", vo.outputs["Distance"], radius), clamp=True)
    return g.math("MULTIPLY", g.math("POWER", glow, 1.6), g.math("LESS_THAN", rnd[1], keep))


def mat_nightsky(name="EggNightSky", sky=None, nebula=None):
    """The night sky under glossy lacquer: midnight blue deepening toward the bottom, soft clouds
    of nebula (violet and teal) drifting through it, and stars of every size, a fine dust and a
    scattering of brighter ones. `sky` and `nebula` replace the colour stops (the void inside the
    Void Rift egg is darker and bluer)."""
    g = _Graph(name)
    co = g.coords()
    z = g.sep(co)[2]
    col = g.ramp(g.math("DIVIDE", z, K.H), sky or [(0.0, (0.002, 0.003, 0.018)), (0.45, (0.006, 0.012, 0.06)), (1.0, (0.016, 0.03, 0.13))])
    neb = g.n("ShaderNodeTexNoise", **{"Scale": 1.4, "Detail": 6.0, "Roughness": 0.58, "Distortion": 0.9})
    g.link(co, neb.inputs["Vector"])
    cloud = g.bw(g.ramp(neb.outputs["Fac"], [(0.45, (0, 0, 0)), (0.72, (1, 1, 1))]))
    hue = g.n("ShaderNodeTexNoise", **{"Scale": 0.9, "Detail": 2.0})
    g.link(co, hue.inputs["Vector"])
    nebula = g.ramp(hue.outputs["Fac"], nebula or [(0.35, (0.16, 0.03, 0.3)), (0.5, (0.07, 0.04, 0.26)), (0.65, (0.01, 0.13, 0.22))])
    col = g.mix(g.math("MULTIPLY", cloud, 0.6), col, nebula)
    dust = _stars(g, co, 34.0, 0.16, 0.45)
    bright = _stars(g, co, 9.0, 0.2, 0.4)
    col = g.mix(g.math("MULTIPLY", dust, 0.55), col, (0.7, 0.78, 1.0))
    col = g.mix(bright, col, (1.0, 0.97, 0.88))
    col = g.ao(col, 0.08, 0.5)
    return g.finish(col, 0.14, 0.0)


def mat_moonsilver(name="EggMoonSilver"):
    """The moon's own pale silver: soft grey-blue seas across it and faint crater rims, a gentle
    metallic sheen."""
    g = _Graph(name)
    co = g.coords()
    seas = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 4.0, "Roughness": 0.5})
    g.link(co, seas.inputs["Vector"])
    col = g.ramp(seas.outputs["Fac"], [(0.35, (0.86, 0.89, 0.97)), (0.55, (0.66, 0.71, 0.86)), (0.75, (0.42, 0.48, 0.67))])
    cr = g.n("ShaderNodeTexVoronoi", **{"Scale": 14.0})
    g.link(co, cr.inputs["Vector"])
    rim = g.math("MULTIPLY", g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", cr.outputs["Distance"], 0.3)), 0.05), 0.25)
    col = g.mix(rim, col, (0.95, 0.97, 1.0))
    col = g.ao(col, 0.06, 0.45)
    return g.finish(col, 0.3, 0.35, g.bump(g.math("ADD", seas.outputs["Fac"], rim), 0.15, 0.006))


def mat_moonstone(name="EggMoonstone"):
    """Moonstone: milky white with a blue and lavender sheen drifting through it in soft swirls,
    polished."""
    g = _Graph(name)
    co = g.coords()
    sw = g.n("ShaderNodeTexNoise", **{"Scale": 1.8, "Detail": 5.0, "Roughness": 0.55, "Distortion": 1.4})
    g.link(co, sw.inputs["Vector"])
    hue = g.n("ShaderNodeTexNoise", **{"Scale": 1.1, "Detail": 2.0})
    g.link(co, hue.inputs["Vector"])
    sheen = g.ramp(hue.outputs["Fac"], [(0.35, (0.5, 0.64, 0.98)), (0.65, (0.68, 0.56, 0.96))])
    col = g.mix(g.math("MULTIPLY", g.bw(g.ramp(sw.outputs["Fac"], [(0.38, (0, 0, 0)), (0.72, (1, 1, 1))])), 0.85), (0.8, 0.83, 0.92), sheen)
    col = g.ao(col, 0.08, 0.5)
    return g.finish(col, 0.12, 0.0)


def mat_pearl(name="EggPearl"):
    """Pearl: a warm white with soft iridescent clouds of rose, ice blue and pale gold."""
    g = _Graph(name)
    co = g.coords()
    a = g.n("ShaderNodeTexNoise", **{"Scale": 1.6, "Detail": 4.0, "Roughness": 0.5, "Distortion": 0.8})
    g.link(co, a.inputs["Vector"])
    tint = g.ramp(a.outputs["Fac"], [(0.3, (0.96, 0.72, 0.8)), (0.5, (0.96, 0.92, 0.86)), (0.7, (0.72, 0.84, 0.99)), (0.85, (0.98, 0.86, 0.6))])
    col = g.mix(0.8, (0.95, 0.93, 0.9), tint)
    col = g.ao(col, 0.08, 0.55)
    return g.finish(col, 0.2, 0.0)


def mat_cloud(name="EggCloud"):
    """A soft auspicious cloud: white, its folds shaded a cool blue instead of grey."""
    g = _Graph(name)
    a = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    a.inputs["Distance"].default_value = 0.15
    col = g.ramp(a.outputs["AO"], [(0.3, (0.42, 0.5, 0.85)), (0.75, (0.82, 0.86, 0.97)), (1.0, (0.97, 0.97, 1.0))])
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 8.0, "Detail": 3.0})
    g.link(g.coords(), fine.inputs["Vector"])
    return g.finish(col, 0.65, 0.0, g.bump(fine.outputs["Fac"], 0.08, 0.01))


def mat_bronze(name="EggBronze"):
    """Aged bronze: warm metal on the raised parts, a teal-green verdigris settled in the hollows
    (ambient occlusion turned to patina), like the shrine's thorn branches."""
    g = _Graph(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 14.0, "Detail": 4.0})
    g.link(co, n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.42, 0.24, 0.08)), (0.7, (0.66, 0.42, 0.16))])
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.05
    patina = g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.7)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", patina, 1.5), 1.0), col, (0.1, 0.32, 0.26))
    metal = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("MINIMUM", g.math("MULTIPLY", patina, 1.5), 1.0)), 0.6)
    return g.finish(col, g.math("ADD", 0.35, g.math("MULTIPLY", patina, 0.4)), metal, g.bump(n.outputs["Fac"], 0.1, 0.004))


def mat_voidglass(name="EggVoidGlass"):
    """Polished void glass: almost black indigo, a faint blue-violet sheen drifting through it."""
    g = _Graph(name)
    co = g.coords()
    sw = g.n("ShaderNodeTexNoise", **{"Scale": 1.5, "Detail": 4.0, "Roughness": 0.5, "Distortion": 1.2})
    g.link(co, sw.inputs["Vector"])
    col = g.ramp(sw.outputs["Fac"], [(0.35, (0.006, 0.006, 0.02)), (0.6, (0.018, 0.02, 0.07)), (0.8, (0.05, 0.04, 0.14))])
    col = g.ao(col, 0.08, 0.5)
    return g.finish(col, 0.08, 0.0)


def mat_fossil(name="EggFossil"):
    """A fossil shell: pale sandy stone with fine ribs running across it (UV v along the coil) and
    darker grooves between them."""
    g = _Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    rib = g.math("ABSOLUTE", g.math("SUBTRACT", g.math("FRACT", g.math("MULTIPLY", v, 1.0)), 0.5))
    col = g.ramp(rib, [(0.0, (0.2, 0.13, 0.08)), (0.25, (0.55, 0.42, 0.28)), (0.5, (0.78, 0.66, 0.48))])
    grit = g.n("ShaderNodeTexNoise", **{"Scale": 40.0, "Detail": 3.0})
    g.link(g.coords(), grit.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", grit.outputs["Fac"], 0.25), col, (0.3, 0.22, 0.14))
    col = g.ao(col, 0.05, 0.4)
    return g.finish(col, 0.6, 0.0, g.bump(rib, 0.5, 0.008))

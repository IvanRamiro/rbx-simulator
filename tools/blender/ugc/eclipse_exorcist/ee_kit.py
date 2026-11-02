"""Building blocks for the Eclipse Exorcist outfit (run inside Blender): a mesh builder in Blender
space, the cloth shapes, and the outfit's procedural materials.

Space: the Roblox blocky body as it imports from Roblox's BlockyCharacter.fbx, 1 unit = 1 stud,
Z up, the front toward -Y, the wearer's left toward +X. The body is boxes: the torso x -1..1,
y -0.5..0.5, z 0..2; the head 1.2 across, z 1.94..3.14; the arms x 1..2 (left) and -2..-1 (right),
z 0..2; the legs x 0..1 and -1..0, z -2..0 (the feet z -2..-1.7).

Every piece is built twice from the same shape functions: dense and folded (the source the maps
are baked from) and as the game mesh (clean quads within Roblox's 4,000-triangle budget).
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EGGS = os.path.join(REPO, "tools", "blender", "eggs")
WORLD = os.path.join(REPO, "tools", "blender", "world")
for p in (EGGS, WORLD):
    if p not in sys.path:
        sys.path.append(p)
import egg_bake as EB  # noqa: E402
import egg_hi as Hm  # noqa: E402  (its _Graph builds the shaders)
import worldlib as W  # noqa: E402

V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(REPO, "assets", "ugc", "EclipseExorcist")


smoothstep = W.smoothstep
collection = W.collection
clear_collection = W.clear_collection
tris = EB.tris


def levels(top, bottom, step):
    """Heights from top to bottom (both included), about `step` apart."""
    n = max(1, int(round(abs(top - bottom) / step)))
    return [top + (bottom - top) * k / n for k in range(n + 1)]


def override(objs, active):
    """A context for operators that need the 3D view, acting on `objs` with `active` active."""
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=win, area=area, region=region, active_object=active,
                                     selected_objects=objs, selected_editable_objects=objs, object=active)


# ---------- mesh building ----------
class Mesh:
    """Faces with per-corner UVs and a material index each (Blender space)."""

    def __init__(self):
        self.verts, self.faces, self.uvs, self.mats = [], [], [], []

    def v(self, p):
        self.verts.append((p[0], p[1], p[2]))
        return len(self.verts) - 1

    def face(self, idx, uv, mat=0, outward=None):
        """A face; wound to face along `outward` if given (Roblox culls back faces)."""
        if outward is not None:
            a, b, c = (V(self.verts[i]) for i in idx[:3])
            if (b - a).cross(c - a).dot(V(outward)) < 0:
                idx, uv = list(idx)[::-1], list(uv)[::-1]
        self.faces.append(list(idx))
        self.uvs.append(list(uv))
        self.mats.append(mat)

    def grid(self, pts, uvs, mat=0, closed=False, outward=None):
        """Quads over a grid of points pts[j][i] (rows j, columns i). closed: the columns wrap round.
        outward(j, i, centre) gives the side the face looks to (None: as wound)."""
        rows = [[self.v(p) for p in row] for row in pts]
        for j in range(len(rows) - 1):
            n = len(rows[j])
            for i in range(n if closed else n - 1):
                i2 = (i + 1) % n
                q = [rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]]
                uvi2 = i + 1
                uv = [uvs[j][i], uvs[j][uvi2], uvs[j + 1][uvi2], uvs[j + 1][i]]
                centre = (V(pts[j][i]) + V(pts[j][i2]) + V(pts[j + 1][i2]) + V(pts[j + 1][i])) / 4
                self.face(q, uv, mat, outward(j, i, centre) if outward else None)
        return rows

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
    return Hm.apply_modifiers(obj, mods)


def solidify(obj, thickness, lining_offset=1):
    """A closed shell: the surface given thickness inward, its inner face the next material (the
    lining), its rims the outer material."""
    return apply_modifiers(obj, [("SOLIDIFY", {"thickness": thickness, "offset": -1.0, "use_even_offset": True,
                                               "use_rim": True, "material_offset": lining_offset,
                                               "material_offset_rim": 0})])


# ---------- shapes ----------
def se(t, a, b, p=4.0):
    """A rounded box (superellipse) of half-extents a (x) and b (y) at angle t from the front (-Y),
    toward the wearer's left (+X) as t grows; its point and outward normal (in the XY plane)."""
    s, c = math.sin(t), math.cos(t)
    x = math.copysign(abs(s) ** (2 / p), s) * a
    y = -math.copysign(abs(c) ** (2 / p), c) * b
    nx = math.copysign(abs(x / a) ** (p - 1), x) / a if a else 0
    ny = math.copysign(abs(y / b) ** (p - 1), y) / b if b else 0
    n = V((nx, ny, 0))
    return x, y, (n.normalized() if n.length > 1e-9 else V((0, -1, 0)))


def folds(t, v, seed, count, amp):
    """Soft vertical folds round a garment: three waves of its own phase, deepening with amp(v)."""
    if not count:
        return 0.0
    r = random.Random(seed)
    ph = [r.uniform(0, TAU) for _ in range(3)]
    d = (0.55 * math.sin(count * t + ph[0]) + 0.3 * math.sin(count * 1.7 * t + ph[1])
         + 0.15 * math.sin(count * 2.9 * t + ph[2]))
    return amp(v) * d


def frames(curve):
    """Parallel-transported (tangent, side, up) frames along a curve: no flips."""
    n = len(curve)
    tangents = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = V((0, 0, 1)) if abs(tangents[0].z) < 0.9 else V((1, 0, 0))
    s = tangents[0].cross(ref).normalized()
    out = []
    for t in tangents:
        s = (s - t * s.dot(t)).normalized()
        out.append((t, s, t.cross(s)))
    return out


def resample(points, step):
    """A polyline resampled every `step` units (Catmull-Rom through the given points)."""
    pts = [V(p) for p in points]
    dense = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(12):
            t = k / 12
            t2, t3 = t * t, t * t * t
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    dense.append(pts[-1])
    out, acc = [dense[0]], 0.0
    for a, b in zip(dense, dense[1:]):
        seg = (b - a).length
        while acc + seg >= step:
            k = (step - acc) / seg
            a = a + (b - a) * k
            seg = (b - a).length
            out.append(a.copy())
            acc = 0.0
        acc += seg
    if (out[-1] - dense[-1]).length > step * 0.3:
        out.append(dense[-1])
    else:
        out[-1] = dense[-1]
    return out


def tube(mesh, curve, radius, sides, mat=0, cap=True, twist=0.0, uv_v=1.0):
    """A round tube along a curve: radius(k, n) per ring; twist turns the rings (radians per ring)."""
    fr = frames(curve)
    n = len(curve)
    pts, uvs = [], []
    along = 0.0
    for k, (c, (t, s, u)) in enumerate(zip(curve, fr)):
        if k:
            along += (curve[k] - curve[k - 1]).length
        r = radius(k, n)
        row, uvrow = [], []
        for i in range(sides + 1):
            a = TAU * i / sides + twist * k
            row.append(c + (s * math.cos(a) + u * math.sin(a)) * r)
            uvrow.append((i / sides, along * uv_v))
        pts.append(row[:-1])
        uvs.append(uvrow)

    def outward(j, i, centre):
        return centre - curve[j]
    rows = mesh.grid(pts, uvs, mat, closed=True, outward=outward)
    if cap:
        for end, k, d in ((rows[0], 0, -1), (rows[-1], n - 1, 1)):
            c = mesh.v(curve[k])
            for i in range(sides):
                mesh.face([end[i], end[(i + 1) % sides], c], [(0, 0), (1, 0), (0.5, 0.5)], mat, fr[k][0] * d)
    return rows


def torus(mesh, c, axis, side, ra, rb, minor, seg, sides, mat=0):
    """A closed ring: its loop in the plane of `axis` (the long way, half-length ra) and `side`
    (half-width rb), the wire `minor` thick."""
    axis, side = V(axis).normalized(), V(side).normalized()
    nrm = axis.cross(side).normalized()
    pts, uvs = [], []
    for i in range(seg):
        a = TAU * i / seg
        p = V(c) + axis * (ra * math.cos(a)) + side * (rb * math.sin(a))
        out = (axis * (math.cos(a) / ra) + side * (math.sin(a) / rb)).normalized()
        row = [p + (out * math.cos(TAU * k / sides) + nrm * math.sin(TAU * k / sides)) * minor for k in range(sides)]
        pts.append(row)
        uvs.append([(k / sides, i / seg) for k in range(sides + 1)])
    pts.append(pts[0])
    uvs.append([(k / sides, 1.0) for k in range(sides + 1)])
    rows = [[mesh.v(p) for p in row] for row in pts[:-1]]
    rows.append(rows[0])
    for i in range(seg):
        for k in range(sides):
            k2 = (k + 1) % sides
            q = [rows[i][k], rows[i][k2], rows[i + 1][k2], rows[i + 1][k]]
            uv = [uvs[i][k], uvs[i][k + 1], uvs[i + 1][k + 1], uvs[i + 1][k]]
            centre = (pts[i][k] + pts[i + 1][k2]) / 2
            a = TAU * (i + 0.5) / seg
            ring_c = V(c) + axis * (ra * math.cos(a)) + side * (rb * math.sin(a))
            mesh.face(q, uv, mat, centre - ring_c)


def cylinder(mesh, c, axis, up, side, radius, depth, n, mat=0):
    """A closed disc `depth` thick, centred on c, facing along axis."""
    axis = V(axis).normalized()
    front = [V(c) + axis * (depth / 2) + (V(up) * math.sin(TAU * i / n) + V(side) * math.cos(TAU * i / n)) * radius for i in range(n)]
    back = [p - axis * depth for p in front]
    fi = [mesh.v(p) for p in front]
    bi = [mesh.v(p) for p in back]
    fc, bc = mesh.v(V(c) + axis * (depth / 2)), mesh.v(V(c) - axis * (depth / 2))
    for i in range(n):
        i2 = (i + 1) % n
        u0, u1 = 0.5 + 0.5 * math.cos(TAU * i / n), 0.5 + 0.5 * math.cos(TAU * i2 / n)
        v0, v1 = 0.5 + 0.5 * math.sin(TAU * i / n), 0.5 + 0.5 * math.sin(TAU * i2 / n)
        mesh.face([fi[i], fi[i2], fc], [(u0, v0), (u1, v1), (0.5, 0.5)], mat, axis)
        mesh.face([bi[i2], bi[i], bc], [(u1, v1), (u0, v0), (0.5, 0.5)], mat, -axis)
        mesh.face([fi[i], bi[i], bi[i2], fi[i2]], [(i / n, 0), (i / n, 1), ((i + 1) / n, 1), ((i + 1) / n, 0)], mat,
                  (front[i] + front[i2]) / 2 - V(c))


# ---------- materials ----------
G = Hm._Graph


def _cloud_print(g, co, scale, thresh=0.55):
    """Stylised storm clouds: soft noise blobs cut into flat shapes with an inner outline ring,
    the way ink clouds are printed on silk. Returns (fill, outline) masks."""
    n = g.n("ShaderNodeTexNoise", **{"Scale": scale, "Detail": 1.5, "Roughness": 0.4, "Distortion": 0.25})
    g.link(co, n.inputs["Vector"])
    f = n.outputs["Fac"]
    fill = g.math("GREATER_THAN", f, thresh)
    ring = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", f, thresh + 0.06)), 0.012)
    swirl = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", f, thresh + 0.13)), 0.01)
    outline = g.math("MINIMUM", g.math("ADD", ring, swirl), 1.0)
    return fill, outline


def _fractures(g, co, scale, width):
    """Crimson eclipse fractures: the edges of a Voronoi crackle, broken by noise into streaks."""
    vo = g.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", **{"Scale": scale})
    g.link(co, vo.inputs["Vector"])
    edge = g.math("LESS_THAN", vo.outputs["Distance"], width)
    br = g.n("ShaderNodeTexNoise", **{"Scale": scale * 0.35, "Detail": 3.0})
    g.link(co, br.inputs["Vector"])
    streak = g.math("GREATER_THAN", br.outputs["Fac"], 0.6)
    return g.math("MULTIPLY", edge, streak), vo.outputs["Distance"]


def mat_eclipse_silk(name="EE_EclipseSilk"):
    """Black silk: a fine twill, folds deepening, a faint cool sheen; crimson fractures leaking
    through it (thickest low on the wearer's left, where the seal strains). Its storm clouds are
    printed on as decals (ee_robe.MOTIFS)."""
    g = G(name)
    co = g.coords()
    x, y, z = g.sep(co)
    tw = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL", **{"Scale": 38.0})
    g.link(co, tw.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", tw.outputs["Fac"], 0.18), (0.016, 0.015, 0.019), (0.04, 0.038, 0.045))
    frac, dist = _fractures(g, co, 2.6, 0.012)
    # the fractures gather toward the wearer's left and the hem
    lean = g.math("ADD", g.math("MULTIPLY", x, 0.35), g.math("MULTIPLY", z, -0.25))
    mask = g.math("MULTIPLY", frac, g.math("GREATER_THAN", lean, -0.05))
    glow = g.math("MULTIPLY", g.math("LESS_THAN", dist, 0.006), mask)
    col = g.mix(mask, col, (0.32, 0.0, 0.02))
    col = g.mix(glow, col, (0.85, 0.04, 0.05))
    col = g.ao(col, 0.1, 0.35)
    rough = g.math("SUBTRACT", 0.5, g.math("MULTIPLY", mask, 0.15))
    return g.finish(col, rough, 0.0, g.bump(g.math("ADD", tw.outputs["Fac"], g.math("MULTIPLY", mask, -2.0)), 0.06, 0.003))


def mat_lining(name="EE_CrimsonLining", dark=(0.22, 0.0, 0.015), light=(0.42, 0.01, 0.03)):
    """The lining (and the cuffs): deep crimson silk, a fine weave, its folds near black."""
    g = G(name)
    co = g.coords()
    w = g.n("ShaderNodeTexNoise", **{"Scale": 80.0, "Detail": 2.0})
    g.link(co, w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", w.outputs["Fac"], 0.6), dark, light)
    col = g.ao(col, 0.08, 0.25)
    return g.finish(col, 0.38, 0.0, g.bump(w.outputs["Fac"], 0.05, 0.002))


def mat_underskirt(name="EE_CrimsonUnderskirt"):
    """The underskirt: crimson silk scorched toward its ragged hem, as if the eclipse had burned it:
    the red deepening to black at the bottom in ink-like tongues, black fractures through it."""
    g = G(name)
    co = g.coords()
    x, y, z = g.sep(co)
    w = g.n("ShaderNodeTexNoise", **{"Scale": 80.0, "Detail": 2.0})
    g.link(co, w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", w.outputs["Fac"], 0.6), (0.3, 0.0, 0.02), (0.58, 0.02, 0.04))
    tongue = g.n("ShaderNodeTexNoise", **{"Scale": 3.5, "Detail": 4.0, "Distortion": 0.8})
    g.link(co, tongue.inputs["Vector"])
    # burn: from about z -0.9 down, broken upward in tongues by the noise
    burn = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", -0.85, z), 2.2), g.math("MULTIPLY", g.math("SUBTRACT", tongue.outputs["Fac"], 0.5), 1.4))
    burn = g.math("MINIMUM", g.math("MAXIMUM", burn, 0.0), 1.0)
    col = g.mix(burn, col, (0.02, 0.0, 0.0))
    frac, _ = _fractures(g, co, 4.0, 0.015)
    col = g.mix(g.math("MULTIPLY", frac, 0.85), col, (0.03, 0.0, 0.005))
    col = g.ao(col, 0.08, 0.3)
    return g.finish(col, g.math("ADD", 0.4, g.math("MULTIPLY", burn, 0.25)), 0.0, g.bump(w.outputs["Fac"], 0.05, 0.002))


def mat_stole(name="EE_StoleSilk"):
    """The white funeral stole (UV u across 0..1, v along in studs): bone-white silk, ink-wash
    clouds bleeding grey through it, a black border stripe and a thin crimson pinstripe down each
    edge, and a crimson seal stamp (a ring round an eclipse) near its end."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    co = g.coords()
    ink = g.n("ShaderNodeTexNoise", **{"Scale": 2.2, "Detail": 6.0, "Roughness": 0.6, "Distortion": 0.6})
    g.link(co, ink.inputs["Vector"])
    wash = g.ramp(ink.outputs["Fac"], [(0.42, (0.86, 0.84, 0.8)), (0.6, (0.55, 0.55, 0.58)), (0.72, (0.16, 0.16, 0.18))])
    fill, outline = _cloud_print(g, co, 2.4, 0.6)
    col = g.mix(g.math("MULTIPLY", outline, 0.85), wash, (0.08, 0.08, 0.1))
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    border = g.math("GREATER_THAN", du, 0.43)
    pin = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", du, 0.385)), 0.012)
    col = g.mix(border, col, (0.02, 0.02, 0.025))
    col = g.mix(pin, col, (0.6, 0.02, 0.04))
    # the seal stamp near the hanging end (v counts from the back end; STOLE_STAMP_V is set by the robe)
    sv = g.math("SUBTRACT", v, STOLE_STAMP_V)
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", sv, sv), g.math("MULTIPLY", g.math("MULTIPLY", du, 0.5), g.math("MULTIPLY", du, 0.5))))
    ring = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", d, 0.14)), 0.018)
    disc = g.math("LESS_THAN", d, 0.085)
    corona = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", d, 0.1)), 0.008)
    stamp = g.math("MINIMUM", g.math("ADD", ring, disc), 1.0)
    col = g.mix(stamp, col, (0.62, 0.02, 0.04))
    col = g.mix(g.math("MULTIPLY", disc, g.math("SUBTRACT", 1.0, corona)), col, (0.03, 0.0, 0.0))
    col = g.ao(col, 0.08, 0.45)
    return g.finish(col, 0.55, 0.0, g.bump(g.math("ADD", ink.outputs["Fac"], border), 0.04, 0.003))


STOLE_STAMP_V = 6.0   # set by the robe once the stole's length is known


def mat_trim(name="EE_CrimsonTrim"):
    """The crossed collar's band (UV u across, v along): crimson silk with a black border line and a
    running stitch, a slight sheen."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    col = (0.5, 0.0, 0.025)
    border = g.math("GREATER_THAN", du, 0.4)
    stitch = g.math("MULTIPLY", g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", du, 0.32)), 0.02),
                    g.math("GREATER_THAN", g.math("FRACT", g.math("MULTIPLY", v, 14.0)), 0.45))
    c = g.mix(border, col, (0.02, 0.015, 0.02))
    c = g.mix(stitch, c, (0.08, 0.02, 0.02))
    c = g.ao(c, 0.05, 0.4)
    return g.finish(c, 0.4, 0.0, g.bump(g.math("ADD", border, stitch), 0.2, 0.003))


def mat_silver(name="EE_Silver"):
    """Tarnished ritual silver: bright on the raised faces, darker in the engraving, fine brushing."""
    g = G(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 30.0, "Detail": 6.0})
    g.link(co, n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.35, (0.5, 0.5, 0.54)), (0.65, (0.86, 0.87, 0.9))])
    col = g.ao(col, 0.04, 0.25)
    # 0.7, not 1: fully metallic silver shows black where it has nothing bright to reflect
    return g.finish(col, 0.28, 0.7, g.bump(n.outputs["Fac"], 0.08, 0.002))


def mat_flat(name, color, rough=0.6, metal=0.0):
    g = G(name)
    return g.finish(g.ao(g.mix(0.0, color, color), 0.05, 0.5), rough, metal)


def mat_hakama(name="EE_Hakama"):
    """The hakama: charcoal silk with a fine black pinstripe running down it, its pleats' valleys
    deepening to black."""
    g = G(name)
    co = g.coords()
    x, y, z = g.sep(co)
    stripe = g.math("LESS_THAN", g.math("FRACT", g.math("MULTIPLY", g.math("ADD", x, g.math("MULTIPLY", y, 0.7)), 9.0)), 0.12)
    w = g.n("ShaderNodeTexNoise", **{"Scale": 70.0, "Detail": 2.0})
    g.link(co, w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", w.outputs["Fac"], 0.5), (0.05, 0.05, 0.058), (0.085, 0.085, 0.095))
    col = g.mix(g.math("MULTIPLY", stripe, 0.8), col, (0.012, 0.012, 0.014))
    col = g.ao(col, 0.1, 0.3)
    return g.finish(col, 0.55, 0.0, g.bump(g.math("ADD", w.outputs["Fac"], stripe), 0.04, 0.002))


def mat_wrap(name="EE_Kyahan"):
    """The shin wrappings: black cotton bandage, each turn's edge catching a little grey."""
    g = G(name)
    co = g.coords()
    w = g.n("ShaderNodeTexNoise", **{"Scale": 90.0, "Detail": 3.0})
    g.link(co, w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", w.outputs["Fac"], 0.7), (0.018, 0.018, 0.02), (0.07, 0.07, 0.075))
    col = g.ao(col, 0.05, 0.25)
    return g.finish(col, 0.8, 0.0, g.bump(w.outputs["Fac"], 0.12, 0.002))


def mat_cord(name="EE_Cord", base=(0.5, 0.0, 0.03), light=(0.85, 0.06, 0.07)):
    """Crimson silk cord (UV u round, v along): twisted fibres, the light catching each twist."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    twist = g.math("SINE", g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", u, 6.283), g.math("MULTIPLY", v, 9.0)), 1.0))
    fib = g.math("MULTIPLY", g.math("ADD", twist, 1.0), 0.5)
    col = g.mix(fib, (base[0] * 0.5, base[1] * 0.5, base[2] * 0.5), light)
    col = g.ao(col, 0.03, 0.4)
    return g.finish(col, 0.42, 0.0, g.bump(fib, 0.3, 0.002))


def mat_lacquer(name="EE_Lacquer"):
    """Black lacquered leather: deep black, a glossy sheen, faint creases."""
    g = G(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 22.0, "Detail": 5.0, "Distortion": 0.4})
    g.link(co, n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.4), (0.01, 0.01, 0.012), (0.04, 0.038, 0.045))
    col = g.ao(col, 0.05, 0.4)
    return g.finish(col, g.math("ADD", 0.22, g.math("MULTIPLY", n.outputs["Fac"], 0.15)), 0.0, g.bump(n.outputs["Fac"], 0.06, 0.003))


def mat_eclipse(name="EE_EclipseDisc"):
    """The eclipse: black lacquered metal, a thin crimson corona burning round its rim (UVs: the disc
    mapped 0..1 across)."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    du, dv = g.math("SUBTRACT", u, 0.5), g.math("SUBTRACT", v, 0.5)
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", du, du), g.math("MULTIPLY", dv, dv)))
    corona = g.math("MULTIPLY", g.math("GREATER_THAN", d, 0.36), g.math("LESS_THAN", d, 0.47))
    col = g.mix(corona, (0.01, 0.008, 0.01), (0.75, 0.02, 0.04))
    return g.finish(col, g.math("ADD", 0.15, g.math("MULTIPLY", corona, 0.3)), 0.4)


def mat_ofuda(name="EE_Ofuda"):
    """The ofuda tag (UV u across 0..1, v down 0..1): red paper, a black band at the top and the
    foot, a column of abstract black sigils down the middle (no real writing), a fine paper grain."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    co = g.coords()
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 120.0, "Detail": 2.0})
    g.link(co, grain.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", grain.outputs["Fac"], 0.35), (0.42, 0.01, 0.03), (0.66, 0.04, 0.06))
    bands = g.math("MAXIMUM", g.math("LESS_THAN", v, 0.07), g.math("GREATER_THAN", v, 0.94))
    # sigils: broken strokes of a distorted wave pattern, in a column down the middle
    sv = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, 3.0), sv.inputs[0])
    g.link(g.math("MULTIPLY", v, 7.0), sv.inputs[1])
    strokes = g.n("ShaderNodeTexWave", wave_type="BANDS", **{"Scale": 1.6, "Distortion": 4.5, "Detail": 1.0})
    g.link(sv.outputs[0], strokes.inputs["Vector"])
    ink = g.math("GREATER_THAN", strokes.outputs["Fac"], 0.6)
    column = g.math("MULTIPLY", g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), 0.3),
                    g.math("MULTIPLY", g.math("GREATER_THAN", v, 0.13), g.math("LESS_THAN", v, 0.7)))
    mark = g.math("MAXIMUM", bands, g.math("MULTIPLY", ink, column))
    col = g.mix(mark, col, (0.02, 0.01, 0.01))
    # a square black stamp near the foot: an outline round a dot
    su, sv2 = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), g.math("ABSOLUTE", g.math("SUBTRACT", v, 0.8))
    square = g.math("MULTIPLY", g.math("LESS_THAN", su, 0.22), g.math("LESS_THAN", sv2, 0.08))
    inner = g.math("MULTIPLY", g.math("LESS_THAN", su, 0.17), g.math("LESS_THAN", sv2, 0.055))
    frame = g.math("SUBTRACT", square, inner)
    col = g.mix(frame, col, (0.03, 0.01, 0.01))
    dot = g.math("LESS_THAN", g.math("ADD", g.math("MULTIPLY", su, su), g.math("MULTIPLY", sv2, sv2)), 0.0016)
    col = g.mix(dot, col, (0.03, 0.0, 0.0))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, 0.75, 0.0, g.bump(grain.outputs["Fac"], 0.05, 0.002))


def mat_paper(name="EE_ShidePaper"):
    """Shide paper: warm white washi, fibrous."""
    g = G(name)
    co = g.coords()
    f = g.n("ShaderNodeTexNoise", **{"Scale": 60.0, "Detail": 6.0, "Distortion": 1.5})
    g.link(co, f.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", f.outputs["Fac"], 0.4), (0.78, 0.76, 0.72), (0.95, 0.94, 0.9))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, 0.8, 0.0, g.bump(f.outputs["Fac"], 0.08, 0.002))


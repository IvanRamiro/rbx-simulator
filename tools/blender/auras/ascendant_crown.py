"""The Ascendant Sun Coronet: Realm 5's crown. It floats above the head, facing forward, with bloom
and a PointLight round it in the game.

Second design (2026-11-03). The owner called the first (six thin swept blades round a plain band)
"so ugly": plant-like, no focal point, no hierarchy. This one is built as real crowns are made:
shaped gold plates wrapped round a band.
  idea      the Ascendant rises toward the sun on a swallow's wings
  primary   a symmetric, regal silhouette rising to a centrepiece. At the front, a sun disc on a
            cloud base; on each side, three layered swallow feathers sweep up and back from it,
            tallest at the front and stepping down toward the sides (a soaring "W" round the sun).
            A slim rimmed band joins them.
  secondary the sun's raised inner ring and gem, its twelve rays (long and short), each feather's
            raised vane, cloud scrolls at the wing roots, a small cloud emblem at the back
  tertiary  a row of beads round the band; bevelled edges that catch the light
Every plate is drawn flat on the unrolled band (x along its circumference, y up, d outward), given
thickness, then wrapped onto the band's cylinder, which flares a little toward the top.
Units are studs (1 Blender unit = 1 stud), Z up; the front faces -Y. One mesh, one material.

    run inside Blender:  path = ".../tools/blender/auras/ascendant_crown.py"
                         exec(open(path).read(), {"__name__": "__main__", "__file__": path})
    then export(bpy.data.objects["AscendantCrown"]) writes assets/aura/ascendant/AscendantCrown.obj
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))  # the repository, from tools/blender/<folder>/
OUT = os.path.join(ROOT, "assets/aura/ascendant/AscendantCrown.obj")
COLL = "AscendantCrown"
TAU = math.tau

R = 0.6            # the band's radius
FLARE = 0.1        # the plates lean outward this much per stud of height
BAND_H = 0.13


def wrap(x, y, d):
    """unrolled band coordinates to space: x = 0 is the front (-Y)"""
    a = -math.pi / 2 + x / R
    r = R + FLARE * max(y, 0) + d
    return Vector((r * math.cos(a), r * math.sin(a), y))


def collection():
    old = bpy.data.collections.get(COLL)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    c = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(c)
    return c


def plate(coll, name, outline, d0, thick, bevel=0.007):
    """a gold plate: a flat outline (x, y) given thickness outward from d0, wrapped onto the band"""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, d0)) for x, y in outline]
    face = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    for v in ext["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z += thick
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    # enough vertices to follow the band's curve
    for _ in range(2):
        long_edges = [e for e in bm.edges if e.calc_length() > 0.12]
        if long_edges:
            bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=False)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for v in bm.verts:
        v.co = wrap(v.co.x, v.co.y, v.co.z)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if bevel:
        b = o.modifiers.new("Edge", "BEVEL")
        b.width = bevel
        b.segments = 1
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
    return o


def lens(centre_fn, width_fn, n=28, asym=0.0):
    """an outline round a centreline: the left edge up, the right edge back down"""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        c = centre_fn(t)
        e = 1e-3
        a, b = centre_fn(max(0, t - e)), centre_fn(min(1, t + e))
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        w = width_fn(t)
        left.append((c[0] + nx * w * (1 + asym), c[1] + ny * w * (1 + asym)))
        right.append((c[0] - nx * w * (1 - asym), c[1] - ny * w * (1 - asym)))
    pts = left + right[::-1]
    out = [pts[0]]
    for p in pts[1:]:                                    # no duplicate points (degenerate faces)
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-4:
            out.append(p)
    return out


def bezier(p0, p1, p2):
    return lambda t: ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                      (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def circle(cx, cy, r, n=40):
    return [(cx + r * math.cos(i * TAU / n), cy + r * math.sin(i * TAU / n)) for i in range(n)]


def gem(coll, name, x, y, d, radius):
    """a cabochon: flattened against the plate, set at (x, y) on the band"""
    bm = bmesh.new()
    # the small wing gems need fewer facets (the budget: Roblox takes up to 20,000 triangles)
    bmesh.ops.create_icosphere(bm, subdivisions=2 if radius > 0.04 else 1, radius=radius)
    a = -math.pi / 2 + x / R
    out = Vector((math.cos(a), math.sin(a), 0))
    for v in bm.verts:
        along = v.co.dot(out)
        v.co = v.co - out * along * 0.45                  # squashed toward the band
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location = wrap(x, y, d)
    return o


# ------------------------------------------------------------------- the parts ------------
def band(coll):
    """a rimmed band: lips at the top and bottom, a shallow channel between, closed inside"""
    bm = bmesh.new()
    seg = 72
    prof = [(0.0, -0.01), (0.0, 0.03), (0.025, 0.035), (0.032, 0.018), (BAND_H - 0.032, 0.018),
            (BAND_H - 0.025, 0.035), (BAND_H, 0.03), (BAND_H, -0.01)]       # (y, d) bottom to top
    rows = []
    for i in range(seg):
        x = i * TAU * R / seg
        rows.append([bm.verts.new(wrap(x, y, d)) for y, d in prof])
    n = len(prof)
    for i in range(seg):
        nxt = (i + 1) % seg
        for j in range(n):
            a, b = rows[i][j], rows[i][(j + 1) % n]
            c, d = rows[nxt][(j + 1) % n], rows[nxt][j]
            bm.faces.new((a, b, c, d))
    me = bpy.data.meshes.new("Band")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("Band", me)
    coll.objects.link(o)
    return [o]


def beads(coll):
    out = []
    n = 24
    for i in range(n):
        x = (i + 0.5) * TAU * R / n
        if min(abs(x), abs(TAU * R - x)) < 0.2 or abs(x - math.pi * R) < 0.15:   # none behind the suns' bases
            continue
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.019)
        me = bpy.data.meshes.new(f"Bead{i}")
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(f"Bead{i}", me)
        coll.objects.link(o)
        o.location = wrap(x, BAND_H / 2, 0.03)
        out.append(o)
    return out


def sun(coll, x0=0.0, s=1.0, tag=""):
    """the centrepiece: a cloud base on the band, the disc, its raised ring and gem, twelve rays"""
    parts = []
    cy = 0.47
    P = lambda pts: [(x0 + s * x, s * y) for x, y in pts]
    base = []
    for i in range(41):                                   # the cloud's three lobes, top edge
        t = i / 40
        base.append((-0.17 + 0.34 * t, 0.24 + 0.07 * math.sin(math.pi * t) + 0.03 * math.sin(3 * math.pi * t)))
    base = base[::-1] + [(-0.13, 0.06), (-0.06, 0.1), (0.0, 0.08), (0.06, 0.1), (0.13, 0.06)]
    parts.append(plate(coll, "SunBase" + tag, P(base), 0.02, 0.03))
    parts.append(plate(coll, "SunDisc" + tag, P(circle(0, cy, 0.17, 40)), 0.03, 0.03))
    parts.append(plate(coll, "SunRing" + tag, P(circle(0, cy, 0.125, 32)), 0.06, 0.012, bevel=0.004))
    for k in range(12):
        a = k * TAU / 12 + TAU / 24
        if math.sin(a) < -0.6:          # no rays down into the cloud base
            continue
        long = k % 2 == 0
        r0, r1 = 0.16, (0.37 if long else 0.29)
        w = 0.038 if long else 0.028
        c = lambda t, a=a, r0=r0, r1=r1: (math.cos(a) * (r0 + (r1 - r0) * t), cy + math.sin(a) * (r0 + (r1 - r0) * t))
        width = lambda t, w=w: w * (1 - t) ** 1.3 * min(1, t * 6 + 0.4) + 0.002     # broad at the disc, needle-sharp tip
        parts.append(plate(coll, f"Ray{k}{tag}", P(lens(c, width, n=10)), 0.025, 0.022, bevel=0))
    parts.append(gem(coll, "SunGem" + tag, x0, cy * s, 0.08, 0.07 * s))
    return parts


def wing(coll, side, x0=0.0, s=1.0, tag=""):
    """three layered swallow feathers sweeping up and back from beside the sun"""
    parts = []
    P = lambda pts: [(x0 + s * x, s * y) for x, y in pts]
    feathers = [  # root, control, tip, width, depth (front-most first)
        ((0.2, 0.2), (0.33, 0.78), (0.62, 1.02), 0.105, 0.05),
        ((0.27, 0.15), (0.46, 0.6), (0.82, 0.8), 0.09, 0.03),
        ((0.34, 0.1), (0.6, 0.4), (0.98, 0.52), 0.075, 0.012),
    ]
    for i, (p0, p1, p2, w, d) in enumerate(feathers):
        p0, p1, p2 = (side * p0[0], p0[1]), (side * p1[0], p1[1]), (side * p2[0], p2[1])
        c = bezier(p0, p1, p2)
        width = lambda t, w=w: w * (math.sin(math.pi * min(0.98, 0.08 + 0.92 * t ** 0.85)) ** 0.75) + 0.003
        # the outer (trailing) edge fuller than the leading one: a feather, not a leaf
        parts.append(plate(coll, f"Feather{side}{i}{tag}", P(lens(c, width, n=24, asym=-0.25 * side)), d, 0.026))
        vane = lambda t, w=w: w * 0.16 * math.sin(math.pi * min(1, 0.05 + t)) + 0.002
        cv = lambda t, c=c: c(0.04 + 0.82 * t)
        parts.append(plate(coll, f"Vane{side}{i}{tag}", P(lens(cv, vane, n=16)), d + 0.026, 0.014, bevel=0))
    # a cloud scroll where the wing springs from the band
    cx, cy = side * 0.2, 0.17
    spiral = lambda t: (cx + side * 0.075 * (1 - 0.75 * t) * math.cos(math.pi * 0.5 + 2.6 * math.pi * t),
                        cy + 0.075 * (1 - 0.75 * t) * math.sin(math.pi * 0.5 + 2.6 * math.pi * t))
    parts.append(plate(coll, f"Scroll{side}{tag}", P(lens(spiral, lambda t: 0.017 * (1 - 0.6 * t) + 0.002, n=44)), 0.06, 0.02, bevel=0))
    parts.append(gem(coll, f"WingGem{side}{tag}", x0 + s * side * 0.2, s * 0.17, 0.09, 0.028 * s))
    return parts


def back_emblem(coll):
    """a small cloud emblem at the back"""
    x0 = math.pi * R
    top = [(x0 - 0.13 + 0.26 * (i / 40), 0.2 + 0.06 * math.sin(math.pi * i / 40) + 0.025 * math.sin(3 * math.pi * i / 40)) for i in range(41)]
    pts = top[::-1] + [(x0 - 0.09, 0.08), (x0, 0.11), (x0 + 0.09, 0.08)]
    return [plate(coll, "BackCloud", pts, 0.02, 0.025)]


def build():
    coll = collection()
    back = math.pi * R
    parts = (band(coll) + beads(coll) + sun(coll) + wing(coll, 1) + wing(coll, -1)
             + sun(coll, back, 0.7, "Back") + wing(coll, 1, back, 0.7, "Back") + wing(coll, -1, back, 0.7, "Back"))
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    crown = bpy.context.view_layer.objects.active
    crown.name = "AscendantCrown"
    bm = bmesh.new()
    bm.from_mesh(crown.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(crown.data)
    bm.free()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    mat = bpy.data.materials.get("CrownClay") or bpy.data.materials.new("CrownClay")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    crown.data.materials.clear()
    crown.data.materials.append(mat)
    tris = sum(len(p.vertices) - 2 for p in crown.data.polygons)
    dims = crown.dimensions
    print(f"AscendantCrown: {tris} triangles, {len(crown.data.vertices)} vertices, size {dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} studs")
    return crown


def export(crown):
    bpy.ops.object.select_all(action="DESELECT")
    crown.select_set(True)
    bpy.context.view_layer.objects.active = crown
    bpy.ops.wm.obj_export(filepath=OUT, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                          export_materials=False, export_uv=True, export_normals=True, apply_modifiers=True)
    print("written", OUT)


if __name__ == "__main__":
    crown = build()

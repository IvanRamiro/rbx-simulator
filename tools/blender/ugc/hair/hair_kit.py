"""Building blocks for marketplace hair (run inside Blender): the head it is shaped on, the hair
shapes (a scalp cap combed toward a point, flattened tapering locks, ribbons), hair materials, and
the rigid-accessory export with its fit check.

Space: Roblox's blocky body as it imports from BlockyCharacter.fbx (as in the Eclipse Exorcist
tools): 1 unit = 1 stud, Z up, the front toward -Y, the wearer's left toward +X. The head is a
rounded block 1.2 across, z 1.94..3.14, centred on HEAD_C; HairAttachment is HAIR_ATT, on its top.

Every piece is built twice from the same shape functions (see ee_kit): `hi`, dense and grooved
strand by strand (the source the maps are baked from), and `low`, the game mesh within Roblox's
4,000-triangle budget for one rigid accessory.

The hair rules (create.roblox.com/docs/art/accessories/specifications, checked November 2026): one
watertight mesh, at most 4,000 triangles, textures up to 2,048, Material Plastic; for the Classic
body scale the mesh must fit 3 wide, 2 up and 3 down, 1.5 in front and 2 behind HairAttachment.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EE = os.path.join(REPO, "tools", "blender", "ugc", "eclipse_exorcist")
if EE not in sys.path:
    sys.path.append(EE)
import ee_bake as B  # noqa: E402
import ee_kit as K  # noqa: E402

V = Vector
TAU = K.TAU
OUT_ROOT = os.path.join(REPO, "assets", "ugc", "Hair")

HEAD_C = V((0.0, 0.0, 2.5375))
HAIR_ATT = V((0.0, 0.0, 3.144))
# the Classic hair box round HairAttachment: (min, max) per Blender axis (x: width, y: -front..+behind, z)
CLASSIC_BOX = ((-1.5, 1.5), (-1.5, 2.0), (-3.0, 2.0))

smoothstep = K.smoothstep


# ---------- the head ----------
def reference(ref_dir):
    """The blocky body from ref_dir/blocky/BlockyCharacter.fbx, kept hidden in the HairRef
    collection as HairRef_<Part> (once per Blender session). Returns the head."""
    coll = K.collection("HairRef")
    head = bpy.data.objects.get("HairRef_Head")
    if head:
        return head
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=os.path.join(ref_dir, "blocky", "BlockyCharacter.fbx"))
    new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
    # the parts hang from the armature, which turns them Z up: keep their world placement before it goes
    placed = {o.name: o.matrix_world.copy() for o in new}
    keep = [o for o in new if o.type == "MESH" and o.name.endswith("_Geo")]
    for o in keep:
        o.parent = None
        o.matrix_world = placed[o.name]
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in keep:
        name = o.name
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        o.name = "HairRef_" + name[:-4]
        o.hide_render = True
    return bpy.data.objects["HairRef_Head"]


def head_tree(head):
    """A BVH of the head in world space."""
    me = head.data.copy()
    me.transform(head.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    bpy.data.meshes.remove(me)
    return tree


def direction(a, el):
    """A direction from the head's centre: azimuth `a` from the front (-Y) toward the wearer's left
    (+X), elevation `el` above the horizontal (radians)."""
    return V((math.sin(a) * math.cos(el), -math.cos(a) * math.cos(el), math.sin(el)))


def on_head(tree, a, el):
    """(the point on the head's surface in that direction, its normal)."""
    d = direction(a, el)
    hit = tree.ray_cast(HEAD_C + d * 2.0, -d, 3.0)
    if hit[0] is None:
        raise ValueError("no head surface toward %.2f, %.2f" % (a, el))
    return hit[0], hit[1]


def table(points):
    """A function of x interpolated linearly over [(x, y)] (clamped at the ends)."""
    pts = sorted(points)

    def f(x):
        if x <= pts[0][0]:
            return pts[0][1]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return pts[-1][1]
    return f


# ---------- shapes ----------
def scalp(tree, cols, rows, hairline, offset, groove=None, mat=0, uv_u=6.0, uv_v=1.6):
    """The hair over the scalp, combed up from the hairline to the crown: one closed grid from the
    top (row 0, where every column meets) down to the hairline.
    hairline(a) is the hairline's elevation per azimuth; offset(a, t) the hair's height off the
    head (t: 0 at the crown, 1 at the hairline); groove(a, t) an extra height (the strands).
    UVs: u round the head, v down from the crown along the strands."""
    m = K.Mesh()
    pts, uvs = [], []
    for j in range(rows + 1):
        t = j / rows
        row, uvrow = [], []
        for i in range(cols + 1):
            a = TAU * i / cols
            el = math.pi / 2 - t * (math.pi / 2 - hairline(a))
            p, n = on_head(tree, a, min(el, math.pi / 2 - 1e-4))
            h = offset(a, t) + (groove(a, t) if groove else 0.0)
            row.append(p + n * h)
            uvrow.append((i / cols * uv_u, t * uv_v))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, mat, closed=True, outward=lambda j, i, c: c - HEAD_C)
    return m


def lock_frames(path, wide):
    """Frames along a lock: (tangent, width axis, depth axis); the width axis is `wide` (a fixed
    direction, or a function of the index) kept square to the lock."""
    n = len(path)
    out = []
    for k in range(n):
        t = (path[min(k + 1, n - 1)] - path[max(k - 1, 0)]).normalized()
        w = V(wide(k) if callable(wide) else wide)
        w = (w - t * w.dot(t))
        if w.length < 1e-6:
            w = t.orthogonal()
        w.normalize()
        out.append((t, w, t.cross(w)))
    return out


def lock(mesh, path, width, depth, sides, wide, mat=0, ridge=None, uv_v=1.0, tip=0.004, uv_norm=False,
         angles=None, under=1.0):
    """A lock of hair along `path`: an elliptical tube width(k, n) across (along `wide`) and
    depth(k, n) thick, tapering to a closed point. ridge(k, n, ang) adds height round it (strands).
    angles: the section's corners (radians; default `sides` evenly spaced); under: the share of
    the depth on the side away from the spine (a blade: flat underneath).
    UVs: u round the lock, v along it (in studs times uv_v, or 0..1 root to tip with uv_norm)."""
    fr = lock_frames(path, wide)
    n = len(path)
    pts, uvs = [], []
    along = 0.0
    for k, (c, (t, w, d)) in enumerate(zip(path, fr)):
        if k:
            along += (path[k] - path[k - 1]).length
        rw, rd = max(width(k, n), tip), max(depth(k, n), tip)
        row, uvrow = [], []
        for i in range(sides + 1):
            ang = angles[i % sides] if angles else TAU * i / sides
            sn = math.sin(ang)
            dirv = w * math.cos(ang) * rw + d * sn * rd * (under if sn < 0 else 1.0)
            if ridge:
                nrm = (w * math.cos(ang) * rd + d * math.sin(ang) * rw).normalized()
                dirv = dirv + nrm * ridge(k, n, ang)
            row.append(c + dirv)
            uvrow.append((i / sides, k / (n - 1) if uv_norm else along * uv_v))
        pts.append(row[:-1])
        uvs.append(uvrow)
    rows = mesh.grid(pts, uvs, mat, closed=True, outward=lambda j, i, cen: cen - path[j])
    for end, k, s in ((rows[0], 0, -1), (rows[-1], n - 1, 1)):
        c = mesh.v(path[k] + fr[k][0] * s * tip)
        for i in range(sides):
            mesh.face([end[i], end[(i + 1) % sides], c], [(0, 0), (1, 0), (0.5, 0.5)], mat, fr[k][0] * s)
    return rows


def clump(mesh, pts, width, thick, step, sides, mat=0, ridge=None, swell=0.35, root=0.55, flat=None):
    """An anime-style clump of hair through the control points `pts`: a lens-shaped lock (a
    diamond in the game mesh), widest about `swell` of the way along, pointed at its tip; its width
    lies along the head (square to the line from the head's centre) unless `flat` gives the width
    direction. UVs: u round the clump, v from 0 at the root to 1 at the tip."""
    path = K.resample(pts, step)
    if len(path) < 3:
        path = K.resample(pts, max(0.02, step / 3))
    n = len(path)

    def shape(k, nn):
        u = k / (nn - 1)
        grow = root + (1 - root) * math.sin(min(u / swell, 1.0) * math.pi / 2)
        return grow * (1 - smoothstep(swell, 1.0, u)) ** 1.15 if k < nn - 1 else 0.0   # a sharp point

    def wide(k):
        t = path[min(k + 1, n - 1)] - path[max(k - 1, 0)]
        if flat is not None:
            return flat
        return (path[k] - HEAD_C).cross(t)
    return lock(mesh, path, lambda k, nn: width * shape(k, nn), lambda k, nn: thick * shape(k, nn) ** 0.6,
                sides, wide, mat, ridge, uv_v=1.0, uv_norm=True)


def along(points, t):
    """The point a share `t` of the way along a polyline (by length)."""
    pts = [V(p) for p in points]
    seg = [(b - a).length for a, b in zip(pts, pts[1:])]
    goal = t * sum(seg)
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if goal <= L or L == 0:
            return a + (b - a) * (goal / L if L else 0.0)
        goal -= L
    return pts[-1].copy()


def mass(mesh, paths, rows, thick, mat=0, centre=HEAD_C, smooth=0.01):
    """A sculpted mass of hair: a surface swept through `paths` (one curve per column, across the
    mass, each from its root to its own tip, so the lower edge takes the shape the tips give it),
    given thickness thick(s, t) (s across 0..1, t root to tip 0..1) about that surface. Thickness 0
    on every edge closes it: the outer and inner faces meet there in one watertight shell.
    UVs: u across, v from root to tip."""
    cols = len(paths)
    curves = [K.resample([V(p) for p in c], smooth) for c in paths]
    mid = [[along(c, j / rows) for c in curves] for j in range(rows + 1)]

    def normal(j, i):
        a = mid[j][min(i + 1, cols - 1)] - mid[j][max(i - 1, 0)]
        b = mid[min(j + 1, rows)][i] - mid[max(j - 1, 0)][i]
        n = a.cross(b)
        if n.length < 1e-9:
            n = mid[j][i] - centre
        n.normalize()
        return n if n.dot(mid[j][i] - centre) >= 0 else -n
    nrm = [[normal(j, i) for i in range(cols)] for j in range(rows + 1)]
    outer, inner, uvs = [], [], []
    for j in range(rows + 1):
        orow, irow, uvrow = [], [], []
        for i in range(cols):
            h = thick(i / (cols - 1), j / rows) / 2
            orow.append(mid[j][i] + nrm[j][i] * h)
            irow.append(mid[j][i] - nrm[j][i] * h)
            uvrow.append((i / (cols - 1), j / rows))
        outer.append(orow)
        inner.append(irow)
        uvs.append(uvrow)
    mesh.grid(outer, uvs, mat, closed=False, outward=lambda j, i, c: nrm[j][i])
    mesh.grid(inner, uvs, mat, closed=False, outward=lambda j, i, c: -nrm[j][i])
    return mid


def lens(s, t, peak=1.0, root=0.12, tip=0.75):
    """A thickness profile for a mass: 0 on its edges, full across the middle, thinning toward its
    tips (from `tip` on) and opening quickly from its root."""
    across = math.sin(math.pi * s) ** 0.45
    down = math.sin(min(t / root, 1.0) * math.pi / 2) * (1 - smoothstep(tip, 1.0, t)) ** 0.8
    return peak * across * down


def lobes(c, centres, slope):
    """A tip length (or height) for column position c: the nearest lobe's value, rising by `slope`
    per unit away from it, so the edge comes to points at the lobes with notches between."""
    return min(v + slope * abs(c - x) for x, v in centres)


BLADE_LOW = [math.radians(a) for a in (90, 206, 334)]   # spine out, two edges: three sides


def strand(mesh, pts, width, thick, step, hi, mat=0, up=None, curl=0.0, flick=0.0, seed=0, swell=0.3, root=0.7):
    """A blade-shaped lock of hair (flat toward the head, a spine outward), the way anime hair is
    drawn: through the control points `pts`, `width` across and `thick` deep at its widest (about
    `swell` along), pointed at its tip. up(p) is its outward direction at a point (default: away
    from the head's centre). curl bends it sideways in an S as it falls; flick turns its tip out.
    Game mesh: three sides; high detail: a smooth blade with strand grooves.
    UVs: u round the lock, v from 0 at the root to 1 at the tip."""
    import random as _r
    rnd = _r.Random(seed)
    base = K.resample([V(p) for p in pts], 0.01)
    n0 = len(base)
    upf = up or (lambda p: (p - HEAD_C).normalized())
    ph = rnd.uniform(0, TAU)
    bent = []
    for k, p in enumerate(base):
        u = k / (n0 - 1)
        t = (base[min(k + 1, n0 - 1)] - base[max(k - 1, 0)]).normalized()
        o = upf(p)
        side = o.cross(t).normalized() if o.cross(t).length > 1e-6 else t.orthogonal().normalized()
        bent.append(p + side * (curl * math.sin(u * math.pi * 1.6 + ph) * u) + o * (flick * smoothstep(0.65, 1.0, u) ** 2))
    path = K.resample(bent, step)
    if len(path) < 4:
        path = K.resample(bent, max(0.02, (sum((b - a).length for a, b in zip(bent, bent[1:])) / 3.2)))
    n = len(path)

    def shape(k, nn):
        u = k / (nn - 1)
        grow = root + (1 - root) * math.sin(min(u / swell, 1.0) * math.pi / 2)
        return grow * (1 - smoothstep(swell, 1.0, u)) ** 1.2 if k < nn - 1 else 0.0

    def wide(k):
        t = path[min(k + 1, n - 1)] - path[max(k - 1, 0)]
        return upf(path[k]).cross(t)
    ridge = None
    if hi:
        g = [rnd.uniform(0, TAU) for _ in range(2)]

        def ridge(k, nn, ang):
            u = k / (nn - 1)
            return (0.0015 * abs(math.sin(ang * 9 + g[0] + 3 * u)) + 0.002 * abs(math.sin(ang * 3 + g[1])) + 0.0012) * (1 - u ** 4)
    return lock(mesh, path, lambda k, nn: width * shape(k, nn), lambda k, nn: thick * shape(k, nn) ** 0.5,
                16 if hi else 3, wide, mat, ridge, uv_norm=True, angles=None if hi else BLADE_LOW, under=0.3)


def ribbon(mesh, path, width, wide, mat=0, notch=0.0, cols=2):
    """A flat ribbon along `path`, width(k, n) across `wide` (a direction, or a function of the
    index: the ribbon twists as it turns). notch: the end is cut in a swallowtail that deep."""
    fr = lock_frames(path, wide)
    n = len(path)
    pts, uvs = [], []
    along = 0.0
    for k, (c, (t, w, d)) in enumerate(zip(path, fr)):
        if k:
            along += (path[k] - path[k - 1]).length
        hw = width(k, n) / 2
        row, uvrow = [], []
        for i in range(cols + 1):
            s = -1 + 2 * i / cols
            p = c + w * (s * hw)
            if k == n - 1 and notch:
                p = p - t * (notch * (1 - abs(s)))   # the swallowtail: the middle cut back
            row.append(p)
            uvrow.append((i / cols, along * 2.0))
        pts.append(row)
        uvs.append(uvrow)
    mesh.grid(pts, uvs, mat, closed=False, outward=lambda j, i, cen: fr[j][2])
    return mesh


# ---------- materials ----------
G = K.G


def mat_hair(name, dark=(0.006, 0.006, 0.009), light=(0.045, 0.047, 0.066), sheen=(0.11, 0.115, 0.15), strands=55.0,
             tip=None, tip_from=0.55):
    """Black hair (UVs: u across the strands, v along them, 0 at the root and 1 at the tip):
    fine strands of slightly different darkness, clumps catching a broken sheen on their upper
    faces, the clefts between locks going to black. tip: the colour the ends turn toward (each clump
    by its own amount)."""
    g = G(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    st = g.n("ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 3.0, "Roughness": 0.55})
    vec = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, strands), vec.inputs[0])
    g.link(g.math("MULTIPLY", v, 1.4), vec.inputs[1])
    g.link(vec.outputs[0], st.inputs["Vector"])
    fine = st.outputs["Fac"]
    clump = g.n("ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 1.0})
    vec2 = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, strands * 0.12), vec2.inputs[0])
    g.link(g.math("MULTIPLY", v, 0.5), vec2.inputs[1])
    g.link(vec2.outputs[0], clump.inputs["Vector"])
    col = g.mix(g.math("POWER", fine, 1.6), dark, light)
    # the sheen: where a clump faces up and its strands are lighter, broken along the strands
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    shine = g.math("MULTIPLY", g.math("SUBTRACT", up, 0.15, clamp=True),
                   g.math("MULTIPLY", g.math("SUBTRACT", clump.outputs["Fac"], 0.42, clamp=True), 3.0))
    shine = g.math("MULTIPLY", g.math("MINIMUM", shine, 1.0), g.math("SUBTRACT", fine, 0.25, clamp=True))
    col = g.mix(g.math("MINIMUM", shine, 0.5), col, sheen)
    if tip:
        each = g.math("ADD", 0.35, g.math("MULTIPLY", geo.outputs["Random Per Island"], 0.65))
        toward = g.math("MULTIPLY", g.math("SUBTRACT", v, tip_from, clamp=True), 1.0 / (1.0 - tip_from))
        tint = g.math("MULTIPLY", g.math("MULTIPLY", toward, toward), each)
        lit = g.mix(fine, tip, tuple(min(1.0, c * 1.8) for c in tip))
        col = g.mix(g.math("MINIMUM", tint, 0.9), col, lit)
    col = g.ao(col, 0.05, 0.12)
    rough = g.math("ADD", 0.46, g.math("MULTIPLY", fine, 0.2))   # a soft sheen, not wet plastic
    return g.finish(col, rough, 0.0, g.bump(fine, 0.35, 0.0015))


def mat_anime_hair(name, root=(0.004, 0.0026, 0.0032), body=(0.018, 0.011, 0.013), shine=(0.07, 0.046, 0.052),
                   tip=None, tip_from=0.5, band=(0.2, 0.42)):
    """Anime hair, shaded the way it is drawn (UVs: u round the lock, v from 0 at the root to 1 at
    the tip): dark at the root, the body a shade lighter, a soft highlight band about a third of
    the way down broken into fine strand lines (each lock's band a little higher or lower), the tip
    deepening again or, with `tip`, turning to that colour."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    geo = g.n("ShaderNodeNewGeometry")
    each = geo.outputs["Random Per Island"]
    col = g.mix(g.math("POWER", g.math("MINIMUM", g.math("MULTIPLY", v, 4.0), 1.0), 0.6), root, body)
    lines = g.n("ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 2.0, "Roughness": 0.4})
    vec = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, 46.0), vec.inputs[0])
    g.link(g.math("MULTIPLY", v, 1.2), vec.inputs[1])
    g.link(g.math("MULTIPLY", each, 9.0), vec.inputs[2])
    g.link(vec.outputs[0], lines.inputs["Vector"])
    fine = lines.outputs["Fac"]
    # the band: centred on mid, its own height per lock, soft at both ends, cut into strands
    mid = g.math("ADD", (band[0] + band[1]) / 2, g.math("MULTIPLY", g.math("SUBTRACT", each, 0.5), 0.14))
    half = (band[1] - band[0]) / 2
    d = g.math("DIVIDE", g.math("ABSOLUTE", g.math("SUBTRACT", v, mid)), half)
    soft = g.math("POWER", g.math("SUBTRACT", 1.0, g.math("MINIMUM", d, 1.0)), 1.5)
    streak = g.math("POWER", g.math("SUBTRACT", fine, 0.3, clamp=True), 0.8)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", g.math("MULTIPLY", soft, streak), 1.3), 1.0), col, shine)
    # fine strands all the way down, barely there
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", fine, 0.55, clamp=True), 0.5), col, body)
    deep = g.math("MULTIPLY", g.math("SUBTRACT", v, 0.75, clamp=True), 2.4)
    if tip:
        toward = g.math("POWER", g.math("MULTIPLY", g.math("SUBTRACT", v, tip_from, clamp=True), 1.0 / (1.0 - tip_from)), 1.3)
        amount = g.math("MULTIPLY", toward, g.math("ADD", 0.5, g.math("MULTIPLY", each, 0.5)))
        col = g.mix(g.math("MINIMUM", amount, 0.9), col, tip)
    else:
        col = g.mix(g.math("MINIMUM", deep, 0.5), col, root)
    col = g.ao(col, 0.04, 0.3)
    rough = g.math("SUBTRACT", 0.66, g.math("MULTIPLY", soft, 0.12))   # a soft sheen; glossier hair mirrors a dark sky as black
    return g.finish(col, rough, 0.0, g.bump(fine, 0.25, 0.001))


def mat_flat(name, color, rough=0.7):
    return K.mat_flat(name, color, rough)


def mat_silver(name, engrave_scale=26.0):
    """Polished silver with blackened engraving: cloud scrolls cut into it (the low places go dark),
    a fine polish on the raised faces."""
    g = G(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 60.0, "Detail": 4.0})
    g.link(co, n.inputs["Vector"])
    w = g.n("ShaderNodeTexWave", wave_type="RINGS", rings_direction="SPHERICAL",
            **{"Scale": engrave_scale, "Distortion": 6.0, "Detail": 2.0, "Detail Scale": 1.2})
    g.link(co, w.inputs["Vector"])
    cut = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", w.outputs["Fac"], 0.5)), 0.07)
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.8, 0.81, 0.85)), (0.7, (0.97, 0.97, 0.99))])
    col = g.mix(g.math("MULTIPLY", cut, 0.85), col, (0.05, 0.05, 0.06))
    col = g.ao(col, 0.03, 0.2)
    rough = g.math("ADD", 0.18, g.math("MULTIPLY", cut, 0.35))
    # 0.5, not 1: metallic silver mirrors a dark sky as a dark lump; this keeps it reading as silver
    return g.finish(col, rough, 0.5, g.bump(g.math("ADD", cut, g.math("MULTIPLY", n.outputs["Fac"], 0.1)), 0.25, 0.003))


def mat_silk(name, base=(0.32, 0.005, 0.018), light=(0.62, 0.025, 0.04), edge=(0.13, 0.0, 0.008)):
    """Crimson satin ribbon (UVs: u across, v along): smooth, a soft sheen down its middle that
    shifts gently along it, a darker woven border at both edges. No noise: at texture size a fine
    weave aliases into blotches."""
    g = G(name)
    u, v, _ = g.sep(g.coords("UV"))
    across = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), 2.0), clamp=True)
    drift = g.math("ADD", 0.75, g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", v, 2.2)), 0.25))
    sheen = g.math("MULTIPLY", g.math("POWER", across, 1.6), drift)
    col = g.mix(sheen, base, light)
    border = g.math("GREATER_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), 0.41)
    col = g.mix(g.math("MULTIPLY", border, 0.85), col, edge)
    # no ambient occlusion: on a thin strip it only bakes as cloudy noise
    return g.finish(col, g.math("SUBTRACT", 0.42, g.math("MULTIPLY", sheen, 0.12)), 0.0, g.bump(border, 0.12, 0.0015))


# ---------- baking ----------
def _centroid(o):
    vs = o.data.vertices
    return o.matrix_world @ (sum((v.co for v in vs), Vector()) / max(1, len(vs)))


def split_pairs(lows, his):
    """Splits every game-mesh piece and its high-detail piece into their separate parts (each
    clump, plate, ribbon) and pairs each low part with the high part nearest it, so each is baked
    from its own source only: a neighbour's rounder source would bleed into it where clumps
    overlap. Returns (low parts, pairs)."""
    def split(o):
        before = set(bpy.data.objects.keys())
        vl = bpy.context.view_layer
        bpy.ops.object.select_all(action="DESELECT")
        o.hide_set(False)
        o.select_set(True)
        vl.objects.active = o
        with K.override([o], o):
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.separate(type="LOOSE")
            bpy.ops.object.mode_set(mode="OBJECT")
        return [o] + [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
    by_base = {h.name.rsplit("_", 1)[0]: h for h in his}
    parts, pairs = [], []
    for lo in lows:
        hi = by_base[lo.name.rsplit("_", 1)[0]]
        lp, hp = split(lo), split(hi)
        hc = [(h, _centroid(h)) for h in hp]
        for p in lp:
            c = _centroid(p)
            best = min(hc, key=lambda t: (t[1] - c).length)[0]
            parts.append(p)
            pairs.append((p, [best]))
    return parts, pairs


def bake_occlusion(item, parts, out_dir, size=1024, samples=256, distance=0.12):
    """Ambient occlusion over the whole game mesh (every part in place), into
    out_dir/<item>_occlusion.png: the contact shadows between clumps that a per-part bake can't
    see."""
    scene = bpy.context.scene
    img = K.EB._image(item + "_Occlusion", size, False)
    mats = {m for p in parts for m in p.data.materials if m}
    nodes = []
    for m in mats:
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = img
        m.node_tree.nodes.active = n
        nodes.append((m, n))
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.world.light_settings.distance = distance
    try:
        vl = bpy.context.view_layer
        bpy.ops.object.select_all(action="DESELECT")
        for p in parts:
            p.hide_set(False)
            p.hide_render = False
            p.select_set(True)
        vl.objects.active = parts[0]
        bpy.ops.object.bake(type="AO", margin=6, use_clear=True, target="IMAGE_TEXTURES")
    finally:
        scene.render.engine = engine
        for m, n in nodes:
            m.node_tree.nodes.remove(n)
    path = os.path.join(out_dir, item + "_occlusion.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


def apply_occlusion(color_path, occlusion_path, floor=0.4, smooth=2):
    """Darkens the colour map by the occlusion (to `floor` at full occlusion). The occlusion is
    smoothed first (`smooth` passes of a 3 x 3 box): it is soft by nature, and its sampling grain
    shows as blotches on a bright colour (the crimson ribbon)."""
    import numpy as np
    col = bpy.data.images.load(color_path, check_existing=False)
    occ = bpy.data.images.load(occlusion_path, check_existing=False)
    occ.colorspace_settings.name = "Non-Color"
    w, h = col.size
    c = np.array(col.pixels[:], dtype=np.float32).reshape(h, w, 4)
    o = np.array(occ.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 0]
    for _ in range(smooth):
        p = np.pad(o, 1, mode="edge")
        o = sum(p[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)) / 9.0
    k = floor + (1 - floor) * o
    c[..., :3] *= k[..., None]
    col.pixels[:] = c.ravel()
    col.filepath_raw = color_path
    col.save()
    bpy.data.images.remove(col)
    bpy.data.images.remove(occ)


# ---------- maps ----------
def fill_background(path, value):
    """Fills a baked map's unused texels (exact black: nothing was baked there) with `value`, so a
    distant mip doesn't blend black into the islands' edges (a black normal points backwards and
    rims every lock in dark). Returns how many texels it filled."""
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"   # before touching pixels: setting it after resets them
    px = list(img.pixels)
    filled = 0
    for i in range(0, len(px), 4):
        if px[i] == 0.0 and px[i + 1] == 0.0 and px[i + 2] == 0.0:
            px[i:i + 3] = value
            filled += 1
    img.pixels[:] = px
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return filled


# ---------- export ----------
def roblox(p):
    """A Blender-space offset in Roblox's axes (studs): x mirrored, y up, z back."""
    return (-p.x, p.z, p.y)


def export_rigid(item, lows, out_dir):
    """Joins copies of the game-mesh pieces into one mesh named `item`, its origin at its bounds'
    centre (where Studio's importer puts the MeshPart), and writes out_dir/<item>.fbx. Returns the
    report: triangles, watertightness, the Classic-box fit, and the HairAttachment position inside
    the Handle in Roblox axes."""
    coll = K.collection(item + "_Export")
    K.clear_collection(coll)
    copies = []
    for o in lows:
        c = o.copy()
        c.data = o.data.copy()
        coll.objects.link(c)
        copies.append(c)
    vl = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for c in copies:
        c.hide_set(False)
        c.select_set(True)
    vl.objects.active = copies[0]
    with K.override(copies, copies[0]):
        bpy.ops.object.join()
    mesh = copies[0]
    if bpy.data.objects.get(item) and bpy.data.objects[item] is not mesh:
        bpy.data.objects.remove(bpy.data.objects[item], do_unlink=True)
    mesh.name = mesh.data.name = item
    assert mesh.name == item, mesh.name
    # origin at the bounds' centre
    bb = [mesh.matrix_world @ V(c) for c in mesh.bound_box]
    lo = V([min(p[i] for p in bb) for i in range(3)])
    hi = V([max(p[i] for p in bb) for i in range(3)])
    centre = (lo + hi) / 2
    mesh.data.transform(__import__("mathutils").Matrix.Translation(-centre))
    mesh.location = centre
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    open_edges = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    path = os.path.join(out_dir, item + ".fbx")
    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    vl.objects.active = mesh
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             bake_anim=False, mesh_smooth_type="FACE", path_mode="STRIP")
    rel_lo, rel_hi = lo - HAIR_ATT, hi - HAIR_ATT
    fits = all(CLASSIC_BOX[i][0] <= rel_lo[i] and rel_hi[i] <= CLASSIC_BOX[i][1] for i in range(3))
    report = {
        "item": item, "fbx": path, "tris": K.tris(mesh), "non_manifold_edges": open_edges,
        "size_studs": [round(abs(x), 3) for x in roblox(hi - lo)],
        "box_rel_hair_attachment": {"min": [round(x, 3) for x in rel_lo], "max": [round(x, 3) for x in rel_hi]},
        "fits_classic_box": fits,
        "hair_attachment_in_handle": [round(x, 4) for x in roblox(HAIR_ATT - centre)],
    }
    with open(os.path.join(out_dir, item + "_export.json"), "w") as f:
        json.dump(report, f, indent=1)
    return report


# ---------- review ----------
REVIEW_VIEWS = {"front": (0, -1, 0.12), "back": (0, 1, 0.12), "left": (1, 0, 0.12), "right": (-1, 0, 0.12),
                "top": (0, 0.15, 1), "three_quarter": (-0.75, -0.7, 0.35)}


def render_sheet(objects, out_path, target=(0.0, 0.35, 2.15), size=(700, 900), distance=10.5,
                 views=("front", "left", "back", "three_quarter"), cols=2, cycles=0):
    """Renders `objects` (and nothing else) from each of `views` (names in REVIEW_VIEWS, by default
    front, side, back and three-quarter) under neutral studio light into one sheet `cols` wide at
    out_path (EEVEE, or Cycles at `cycles` samples), in reading order. The scene is left as it was."""
    import numpy as np
    scene = bpy.context.scene
    show = set(objects)
    saved_hide = {o.name: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE"):
            o.hide_render = o.name not in show
    made = []

    def light(name, loc, energy, size_, color):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.color, d.size = energy, color, size_
        o = bpy.data.objects.new(name, d)
        scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        made.append(o)
    light("Review_Key", (-3, -4, 5), 900, 4, (1, 1, 1))
    light("Review_Fill", (4, -3, 3), 300, 5, (0.85, 0.9, 1.0))
    light("Review_Rim", (1, 5, 5), 900, 4, (1.0, 0.85, 0.85))
    cam = bpy.data.objects.new("Review_Cam", bpy.data.cameras.new("Review_Cam"))
    cam.data.lens = 60
    scene.collection.objects.link(cam)
    made.append(cam)
    saved = (scene.camera, scene.render.engine, scene.render.resolution_x, scene.render.resolution_y,
             scene.render.resolution_percentage, scene.render.filepath)
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    saved_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value)
    bg.inputs[0].default_value, bg.inputs[1].default_value = (0.05, 0.05, 0.06, 1), 0.6
    scene.camera = cam
    if cycles:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = cycles
    else:
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    tiles = []
    try:
        for name in views:
            d = V(REVIEW_VIEWS[name]).normalized()
            cam.location = V(target) + d * distance
            cam.rotation_euler = (V(target) - cam.location).to_track_quat("-Z", "Y").to_euler()   # the top view leans a little back, so "Y" stays defined
            path = out_path[:-4] + "_%d.png" % len(tiles)
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(path, check_existing=False)
            tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4))
            bpy.data.images.remove(im)
            os.remove(path)
    finally:
        for o in made:
            data, is_light = o.data, o.type == "LIGHT"
            bpy.data.objects.remove(o, do_unlink=True)
            (bpy.data.lights if is_light else bpy.data.cameras).remove(data)
        scene.camera, scene.render.engine, scene.render.resolution_x, scene.render.resolution_y = saved[:4]
        scene.render.resolution_percentage, scene.render.filepath = saved[4:]
        bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
        for n, v in saved_hide.items():
            if n in bpy.data.objects:
                bpy.data.objects[n].hide_render = v
    h, w = tiles[0].shape[:2]
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.ones((h * rows, w * cols, 4), dtype=np.float32)
    sheet[..., :3] = 0.05
    for k, tile in enumerate(tiles):        # reading order; image pixels run bottom-up
        r, c = divmod(k, cols)
        y0 = (rows - 1 - r) * h
        sheet[y0:y0 + h, c * w:(c + 1) * w] = tile
    out = bpy.data.images.new("Review_Sheet", w * cols, h * rows, alpha=True)
    out.pixels[:] = sheet.ravel()
    out.filepath_raw, out.file_format = out_path, "PNG"
    out.save()
    bpy.data.images.remove(out)
    return out_path

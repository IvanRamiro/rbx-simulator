"""What the three Murim faction secret weapons share (run inside Blender, headless):

    blender -b --factory-startup --python tools/blender/weapons/secret_orthodox.py -- build|clay|export|review

They are built like the realm weapons (weapon_kit.py): high-detail pieces with procedural shaders, baked onto one
game mesh ("Body"), plus Neon glow pieces, one per colour. This module adds what a hero prop needs on top of
that and what a headless run needs:

- sweep(): a faceted or smooth solid swept along a path (blades, peaks, jaws, spikes), cross-section by profile;
- strand(), cloth(), jewel(), spike(): twisted cords and rope, torn cloth, set stones, thorns;
- make_low(): the game mesh with a triangle target per piece (or a planar dissolve for hard-surface pieces) and
  flat shading where a piece is faceted;
- bake(): like egg_bake.bake, but the colour map is the material's Base Color (not the Diffuse pass, which
  multiplies by 1 - metallic and turns every metal muddy);
- export(): weapon_kit.export with those two swapped in, honouring SECRET_OUT_DIR / SECRET_PLACEMENTS_DIR so a
  test run never touches assets/ or src/;
- the review lab: clay views, material views of the baked game mesh, silhouettes, a hand proxy, contact sheets.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import weapon_kit as WK  # noqa: E402

B, Hm, K, W = WK.B, WK.Hm, WK.K, WK.W
V = Vector
TAU = math.tau
REPO = W.REPO
REVIEW = os.path.join(REPO, "renders", "faction_weapons")

OUT_DIR = os.environ.get("SECRET_OUT_DIR") or WK.OUT_DIR
PLACEMENTS_DIR = os.environ.get("SECRET_PLACEMENTS_DIR") or WK.PLACEMENTS_DIR
WK.OUT_DIR, WK.PLACEMENTS_DIR = OUT_DIR, PLACEMENTS_DIR


def _override(obj):
    """egg_bake's mode switches without a window (Blender -b has none that is usable)."""
    return bpy.context.temp_override(active_object=obj, object=obj, selected_objects=[obj], selected_editable_objects=[obj])


if bpy.app.background:
    B._ui_override = _override


def srgb(r, g, b):
    """sRGB 0-255 to linear, for shader colours that are given the way a painter reads them."""
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# ---------- shapes ----------
def sweep(hi, path, profile, scale, mat=0, up=(0, 1, 0), cap_start=True, cap_end=True, uv_scale=1.0):
    """A solid swept along `path` (Roblox space points), `profile` a convex cross-section [(a, b)] (a along
    the side axis, b along `up`, both about 1), scaled by scale(t) -> (sa, sb) or one number, t 0..1 along
    the path. `up` is a vector, or a function (i, points) -> vector (a band round a grip turns it radial). Faces are
    turned out from the axis, so the profile must be convex (a groove would face wrong)."""
    pts = [V(p) for p in path]
    n = len(pts)
    rings = []
    prev_side = None
    for i, c in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        t = t.normalized() if t.length > 1e-9 else V((0, 0, -1))
        upv = V(up(i, pts)) if callable(up) else V(up)
        side = t.cross(upv)
        if side.length < 1e-4:
            side = prev_side if prev_side is not None else V((1, 0, 0))
        side = side.normalized()
        prev_side = side
        u = side.cross(t).normalized()
        s = scale(i / max(1, n - 1))
        sa, sb = (s, s) if isinstance(s, (int, float)) else s
        rings.append((c, [c + side * (a * max(sa, 1e-4)) + u * (b * max(sb, 1e-4)) for a, b in profile]))
    WK.loft(hi, rings, mat=mat, cap_start=cap_start, cap_end=cap_end, uv_scale=uv_scale)
    return rings


def lens_profile(k=8, flat=0.0):
    """A rounded cross-section of 2k points (a unit lens, or a rounded rectangle with flat > 0)."""
    out = []
    for i in range(2 * k):
        a = TAU * i / (2 * k)
        c, s = math.cos(a), math.sin(a)
        if flat:
            c = math.copysign(abs(c) ** (1 - flat), c)
            s = math.copysign(abs(s) ** (1 - flat), s)
        out.append((c, s))
    return out


def hex_profile(top=0.55):
    """A flat hexagon: full width at the middle, `top` of it across the faces."""
    return [(1, 0), (top, 1), (-top, 1), (-1, 0), (-top, -1), (top, -1)]


def bar_profile():
    """A chamfered rectangle."""
    return [(1, 0.7), (0.7, 1), (-0.7, 1), (-1, 0.7), (-1, -0.7), (-0.7, -1), (0.7, -1), (1, -0.7)]


def torus(hi, centre, normal, radius, tube, n=32, sides=8, mat=0, arc=TAU, start=0.0, squash=1.0, uv_scale=3.0):
    """A closed ring (or, with arc < TAU, a split ring with capped ends): radius round `centre`, facing `normal`,
    `tube` thick (`squash` flattens the tube along the ring's normal). WK.ring overlaps itself at its seam, which
    the QA gate reads as z-fighting; this one closes cleanly."""
    nrm = V(normal).normalized()
    ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
    s = nrm.cross(ref).normalized()
    t = nrm.cross(s)
    c0 = V(centre)
    closed = arc >= TAU - 1e-6
    steps = n if closed else n + 1
    rings = []
    for k in range(steps):
        a = start + arc * k / n
        radial = s * math.cos(a) + t * math.sin(a)
        mid = c0 + radial * radius
        pos = [mid + radial * (tube * math.cos(TAU * j / sides)) + nrm * (tube * squash * math.sin(TAU * j / sides)) for j in range(sides)]
        rings.append((mid, [hi.v(p) for p in pos], pos, radial))
    cnt = len(rings)
    for k in range(cnt if closed else cnt - 1):
        r0, r1 = rings[k], rings[(k + 1) % cnt]
        for j in range(sides):
            j2 = (j + 1) % sides
            cen = (r0[0] + r1[0]) / 2
            face = (r0[2][j] + r0[2][j2] + r1[2][j2] + r1[2][j]) / 4
            quad = [r0[1][j], r0[1][j2], r1[1][j2], r1[1][j]]
            hi.facing(quad, [(k / n * uv_scale, j / sides), (k / n * uv_scale, (j + 1) / sides), ((k + 1) / n * uv_scale, (j + 1) / sides), ((k + 1) / n * uv_scale, j / sides)],
                      tuple(face - cen), mat)
    if not closed:
        for ring, sign in ((rings[0], 1), (rings[-1], -1)):
            cap = hi.v(ring[0])
            for j in range(sides):
                j2 = (j + 1) % sides
                hi.facing([ring[1][j], ring[1][j2], cap], [(0, 0), (1, 0), (0.5, 1)], tuple(ring[3].cross(nrm) * sign))


def tent(hi, apex, b1, b2, h, mat=0):
    """A folded mountain: a flat triangle (apex, b1, b2, Roblox space, in one horizontal plane) lifted into a ridge,
    its highest line running from the apex to the middle of the base, `h` up and down: four sloped facets and a
    vertical diamond for a back. Convex, closed, faces turned outward. Returns the top facets' (normal, centroid)."""
    a, p1, p2 = V(apex), V(b1), V(b2)
    m = (p1 + p2) / 2
    top, bot = m + V((0, h, 0)), m - V((0, h, 0))
    c = (a + p1 + p2 + m) / 4
    faces = [(a, p1, top), (a, top, p2), (a, bot, p1), (a, p2, bot), (p1, bot, top), (p2, top, bot)]
    out = []
    for f in faces:
        ids = [hi.v(q) for q in f]
        cen = sum(f, V((0, 0, 0))) / 3
        hi.facing(ids, [(0, 0), (1, 0), (0.5, 1)], tuple(cen - c), mat)
        if f[2] == top and f[0] == a:
            n = (f[1] - f[0]).cross(f[2] - f[0]).normalized()
            if n.y < 0:
                n = -n
            out.append((n, cen))
    return out


def _area2(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2


def ear_clip(poly):
    """Triangles (index triples) of a simple polygon [(x, y)], by ear clipping."""
    idx = list(range(len(poly)))
    ccw = _area2(poly) > 0
    out = []

    def cross(a, b, c):
        return (poly[b][0] - poly[a][0]) * (poly[c][1] - poly[a][1]) - (poly[b][1] - poly[a][1]) * (poly[c][0] - poly[a][0])

    def inside(o, a, b, c):
        d = [cross(a, b, o), cross(b, c, o), cross(c, a, o)]
        return all(x >= -1e-12 for x in d) if ccw else all(x <= 1e-12 for x in d)
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            cr = cross(a, b, c)
            if (cr <= 1e-12) if ccw else (cr >= -1e-12):
                continue
            if any(inside(o, a, b, c) for o in idx if o not in (a, b, c)):
                continue
            out.append((a, b, c))
            idx.pop(k)
            break
        else:
            break
    out.append(tuple(idx))
    return out


def plate(hi, outline, y, half, mat=0, uv_scale=1.0):
    """A flat plate in the XZ plane (outline [(x, z)], a simple polygon, any shape): its top and bottom `half` above
    and below height y, and its rim. Faces turned outward."""
    n = len(outline)
    top = [hi.v(V((x, y + half, z))) for x, z in outline]
    bot = [hi.v(V((x, y - half, z))) for x, z in outline]
    for a, b, c in ear_clip(outline):
        hi.facing([top[a], top[b], top[c]], [(outline[i][0] * uv_scale, outline[i][1] * uv_scale) for i in (a, b, c)], (0, 1, 0), mat)
        hi.facing([bot[a], bot[b], bot[c]], [(outline[i][0] * uv_scale, outline[i][1] * uv_scale) for i in (a, b, c)], (0, -1, 0), mat)
    ccw = _area2(outline) > 0
    run = 0.0
    for i in range(n):
        j = (i + 1) % n
        dx, dz = outline[j][0] - outline[i][0], outline[j][1] - outline[i][1]
        ln = math.hypot(dx, dz)
        nx, nz = (dz, -dx) if ccw else (-dz, dx)
        hi.facing([top[i], top[j], bot[j], bot[i]], [(run, 1), (run + ln, 1), (run + ln, 0), (run, 0)], (nx, 0, nz), mat)
        run += ln


def strip(hi, pts, y_top, y_bot, half_w, mat=0):
    """A flat ribbon laid along an open polyline [(x, z)] in the XZ plane, `half_w` each side, from y_bot up to y_top,
    its corners mitred (so it never doubles back on itself). Faces turned outward."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        p = V((pts[i][0], 0, pts[i][1]))
        ds = []
        if i > 0:
            ds.append((p - V((pts[i - 1][0], 0, pts[i - 1][1]))).normalized())
        if i < n - 1:
            ds.append((V((pts[i + 1][0], 0, pts[i + 1][1])) - p).normalized())
        ns = [V((d.z, 0, -d.x)) for d in ds]
        nb = sum(ns, V((0, 0, 0)))
        nb = nb.normalized() if nb.length > 1e-6 else ns[0]
        k = half_w / max(0.35, nb.dot(ns[0]))
        left.append(p + nb * k)
        right.append(p - nb * k)
    rows = []
    for a, b in zip(left, right):
        rows.append(((a.x, y_top, a.z), (b.x, y_top, b.z), (a.x, y_bot, a.z), (b.x, y_bot, b.z)))
    ids = [[hi.v(q) for q in r] for r in rows]
    cen = [(V(r[0]) + V(r[1])) / 2 for r in rows]
    for i in range(n - 1):
        a, b = ids[i], ids[i + 1]
        hi.facing([a[0], a[1], b[1], b[0]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 1, 0), mat)           # top
        hi.facing([a[2], a[3], b[3], b[2]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, -1, 0), mat)          # bottom
        out_l = V(rows[i][0]) - cen[i]
        out_r = V(rows[i][1]) - cen[i]
        hi.facing([a[0], b[0], b[2], a[2]], [(0, 0), (1, 0), (1, 1), (0, 1)], (out_l.x, 0, out_l.z), mat)
        hi.facing([a[1], b[1], b[3], a[3]], [(0, 0), (1, 0), (1, 1), (0, 1)], (out_r.x, 0, out_r.z), mat)
    for i, sign in ((0, -1), (n - 1, 1)):
        a = ids[i]
        d = (cen[min(n - 1, i + 1)] - cen[max(0, i - 1)]).normalized() * sign
        hi.facing([a[0], a[1], a[3], a[2]], [(0, 0), (1, 0), (1, 1), (0, 1)], (d.x, 0, d.z), mat)


def spike(hi, base, tip, radius, sides=5, mat=0, curve=None, belly=0.0):
    """A thorn: round at `base`, sharp at `tip`; `curve` bends its middle sideways (a vector)."""
    b, t = V(base), V(tip)
    mid = (b + t) / 2 + (V(curve) if curve else V((0, 0, 0)))
    Hm.htube(hi, [b, mid, t], lambda u: radius * (1 - u) ** (0.8 - belly) + 0.002, sides=sides, per=4, mat=mat, uv_scale=4.0, tip=True, wobble=0.0)


def pyramid(hi, base_pts, apex, mat=0):
    """A closed faceted pyramid: base polygon (convex, Roblox space), apex. Faces turned outward."""
    pts = [V(p) for p in base_pts]
    c = sum(pts, V((0, 0, 0))) / len(pts)
    a = V(apex)
    n = len(pts)
    ids = [hi.v(p) for p in pts]
    ai = hi.v(a)
    centre = (c + a) / 2
    for i in range(n):
        j = (i + 1) % n
        mid = (pts[i] + pts[j] + a) / 3
        hi.facing([ids[i], ids[j], ai], [(0, 0), (1, 0), (0.5, 1)], tuple(mid - centre), mat)
    base_id = hi.v(c)
    for i in range(n):
        j = (i + 1) % n
        hi.facing([ids[i], ids[j], base_id], [(0, 0), (1, 0), (0.5, 0.5)], tuple(c - a), mat)


def jewel(hi, centre, normal, long_axis, length, width, height, mat=0, bezel=None, rounded=0.5, rings=6):
    """A set stone: a domed rounded rectangle (not a round or an almond: a pair of round stones reads as eyes),
    `length` x `width` on the surface at `centre` facing `normal`, `height` proud of it. `bezel` is a material
    index for a raised rim round it (None: no rim)."""
    nrm = V(normal).normalized()
    ax = V(long_axis)
    ax = (ax - nrm * ax.dot(nrm)).normalized()
    side = nrm.cross(ax).normalized()
    c = V(centre)
    m = 16

    def ring_pts(f, h):
        out = []
        for i in range(m):
            a = TAU * i / m
            ca, sa = math.cos(a), math.sin(a)
            ca = math.copysign(abs(ca) ** (1 - rounded), ca)
            sa = math.copysign(abs(sa) ** (1 - rounded), sa)
            out.append(c + ax * (ca * length / 2 * f) + side * (sa * width / 2 * f) + nrm * h)
        return out
    stack = []
    for k in range(rings + 1):
        t = k / rings
        f = max(math.cos(t * math.pi / 2), 0.04)
        h = height * math.sin(t * math.pi / 2) - 0.003
        stack.append((c + nrm * h, ring_pts(f, h)))
    WK.loft(hi, stack, mat=mat, cap_start=True, cap_end=True, uv_scale=3.0)
    if bezel is not None:
        pts = ring_pts(1.12, height * 0.2)
        Hm.htube(hi, pts + [pts[0], pts[1]], lambda t: height * 0.32 + 0.004, sides=6, per=2, mat=bezel, uv_scale=3.0, tip=False, wobble=0.0)


def strand(hi, path, radius, turns=3.0, strands=2, sides=5, per=6, mat=0, ratio=0.62, phase=0.0, uv_scale=6.0):
    """A twisted cord or rope along `path`: `strands` tubes wound round its axis, `turns` full twists over it.
    radius is the whole cord's; each strand is `ratio` of it across."""
    curve = [V(p) for p in W.catmull([tuple(p) for p in path], per)]
    fr = Hm.frames(curve)
    n = len(curve)
    for s in range(strands):
        pts = []
        for i, c in enumerate(curve):
            _, side, bi = fr[i]
            a = phase + TAU * s / strands + TAU * turns * i / (n - 1)
            pts.append(c + (side * math.cos(a) + bi * math.sin(a)) * radius * (1 - ratio) * 0.9)
        Hm.htube(hi, pts, lambda t: radius * ratio * 0.5 + 0.002, sides=sides, per=1, mat=mat, uv_scale=uv_scale, tip=False, wobble=0.0)
    return curve


def cloth(hi, path, width, mat=0, up=(0, 1, 0), across=3, wave=0.0, wave_turns=1.5, rag=None, flutter=0.0, seed=0, uv_len=1.0):
    """A strip of cloth along `path` (Roblox space), `width(t)` wide, lying across `up` (its face turned toward
    the path's local side). `wave`: how far the strip ripples sideways in its own plane's normal; `rag(t, k)`:
    optional extra shortening of strip column k (0..across) at t, for a torn end. One-sided: solidify() it."""
    import random
    rnd = random.Random(seed)
    curve = [V(p) for p in path]
    n = len(curve)
    upv = V(up)
    lens = [0.0]
    for i in range(1, n):
        lens.append(lens[-1] + (curve[i] - curve[i - 1]).length)
    rows = []
    for i, c in enumerate(curve):
        t = (curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized()
        side = t.cross(upv)
        side = side.normalized() if side.length > 1e-4 else V((1, 0, 0))
        nrm = side.cross(t).normalized()
        f = i / (n - 1)
        w = width(f)
        row = []
        for j in range(across + 1):
            x = -1 + 2 * j / across
            p = c + side * (w * x / 2) + nrm * (wave * math.sin(TAU * wave_turns * f + 2.1 * x + seed) * (0.3 + f))
            if flutter:
                p = p + nrm * flutter * (rnd.random() - 0.5) * f
            row.append(p)
        rows.append((row, nrm))
    for i in range(n - 1):
        for j in range(across):
            if rag is not None and (rag(i / (n - 1), j) or rag((i + 1) / (n - 1), j)):
                continue
            (ra, na), (rb, _) = rows[i], rows[i + 1]
            quad = [ra[j], ra[j + 1], rb[j + 1], rb[j]]
            uv = [(j / across, lens[i] * uv_len), ((j + 1) / across, lens[i] * uv_len), ((j + 1) / across, lens[i + 1] * uv_len), (j / across, lens[i + 1] * uv_len)]
            ids = [hi.v(p) for p in quad]
            hi.facing(ids, uv, tuple(na), mat)


def thicken(obj, thickness, even=True):
    o = Hm.solidify(obj, thickness)
    o["sheet"] = True
    return o


def bevel(obj, width=0.01, segments=2, angle=35.0):
    """Bevels a hi piece's hard edges, so the bake carries them as bright edges."""
    return Hm.apply_modifiers(obj, [("BEVEL", {"width": width, "segments": segments, "limit_method": "ANGLE", "angle_limit": math.radians(angle), "affect": "EDGES"})])


def flat_shade(obj):
    for p in obj.data.polygons:
        p.use_smooth = False
    obj["flat"] = True
    return obj


# ---------- materials ----------
def mat_pbr(name, dark, light, rough=0.5, metal=0.0, grain=0.0, scale=18.0, bump=0.0, ao=0.04):
    """A plain surface between two colours, with noise in colour and (grain) in roughness."""
    g = Hm._Graph(name)
    n = WK._noise(g, scale)
    col = g.ao(g.ramp(n, [(0.3, dark), (0.7, light)]), ao, 0.45)
    r = g.math("ADD", rough, g.math("MULTIPLY", g.math("SUBTRACT", n, 0.5), grain)) if grain else rough
    return g.finish(col, r, metal, g.bump(n, bump, 0.003) if bump else None)


# ---------- the game mesh ----------
def _tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def _evaluated_copy(c):
    me = bpy.data.meshes.new_from_object(c.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = c.data
    c.modifiers.clear()
    c.data = me
    bpy.data.meshes.remove(old)


def make_low(weapon_id, hi_objects, coll, budget, sheet_ratio=0.55):
    """The game mesh. Per piece, by its custom properties: "keep" (whole), "target" (about that many triangles),
    "planar" (a planar dissolve at that angle, then triangulated: hard-surface pieces keep their facets and
    chamfers), "sheet" (thin: sheet_ratio of its triangles), "flat" (flat shading); the rest share what is left
    of `budget`. Joined, unwrapped."""
    fixed = 0
    shared = []
    for o in hi_objects:
        if o.get("keep"):
            fixed += _tris(o)
        elif o.get("target"):
            fixed += min(_tris(o), int(o["target"]))
        elif o.get("planar"):
            fixed += _tris(o) * 0.4
        elif o.get("sheet"):
            fixed += _tris(o) * sheet_ratio
        else:
            shared.append(o)
    solid_total = max(1, sum(_tris(o) for o in shared))
    ratio = max(0.02, min(1.0, (budget - fixed) / solid_total))
    pieces = []
    for o in hi_objects:
        c = B._copy(o, o.name + "_low")
        coll.objects.link(c)
        if o.get("keep"):
            pass
        elif o.get("planar"):
            md = c.modifiers.new("Dissolve", "DECIMATE")
            md.decimate_type = "DISSOLVE"
            md.angle_limit = math.radians(float(o["planar"]))
            md.use_dissolve_boundaries = False
            tr = c.modifiers.new("Tri", "TRIANGULATE")
            tr.min_vertices = 4
            _evaluated_copy(c)
            if o.get("target") and _tris(c) > int(o["target"]) * 1.15:
                md = c.modifiers.new("Decimate", "DECIMATE")
                md.decimate_type = "COLLAPSE"
                md.ratio = max(0.03, int(o["target"]) / _tris(c))
                md.use_collapse_triangulate = True
                _evaluated_copy(c)
        else:
            if o.get("target"):
                r = min(1.0, int(o["target"]) / max(1, _tris(o)))
            elif o.get("sheet"):
                r = sheet_ratio
            else:
                r = ratio
            if r < 0.999:
                md = c.modifiers.new("Decimate", "DECIMATE")
                md.decimate_type = "COLLAPSE"
                md.ratio = r
                md.use_collapse_triangulate = True
                _evaluated_copy(c)
        c["flat"] = bool(o.get("flat"))
        pieces.append(c)
    bm = bmesh.new()
    layer = bm.faces.layers.int.new("flat")
    for c in pieces:
        me = c.data.copy()
        me.transform(c.matrix_world)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f[layer] = 1 if c["flat"] else 0
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    me = bpy.data.meshes.new(weapon_id + "_Body")
    bm.faces.ensure_lookup_table()
    flats = [bool(f[layer]) for f in bm.faces]
    bm.to_mesh(me)
    bm.free()
    for p, fl in zip(me.polygons, flats):
        p.use_smooth = not fl
    for c in pieces:
        m = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(m)
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    low = bpy.data.objects.new(weapon_id + "_Body", me)
    coll.objects.link(low)
    B._unwrap(low)
    return low


def _route_color(materials):
    """Every material shows its Base Color as emission (to bake the colour map as it is, not as the Diffuse pass
    would turn it for a metal). Returns a function that puts the materials back."""
    undo = []
    for m in materials:
        t = m.node_tree
        out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
        bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
        old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        em = t.nodes.new("ShaderNodeEmission")
        sock = bsdf.inputs["Base Color"]
        if sock.links:
            t.links.new(sock.links[0].from_socket, em.inputs["Color"])
        else:
            em.inputs["Color"].default_value = sock.default_value
        t.links.new(em.outputs[0], out.inputs["Surface"])
        undo.append((t, out, old, em))

    def restore():
        for t, out, old, em in undo:
            t.nodes.remove(em)
            if old is not None:
                t.links.new(old, out.inputs["Surface"])
    return restore


def bake(weapon_id, hi_objects, low, size=1024, small=512, samples=16, extrusion=0.03, ray=0.1):
    """egg_bake.bake with the colour map from Base Color (see _route_color)."""
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    images = {"color": B._image(weapon_id + "_Color", size, True), "normal": B._image(weapon_id + "_Normal", size, False),
              "roughness": B._image(weapon_id + "_Roughness", small, False), "metalness": B._image(weapon_id + "_Metalness", small, False)}
    mat = B._baked_material(weapon_id, images)
    low.data.materials.clear()
    low.data.materials.append(mat)
    engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    hi_mats = {m for o in hi_objects for m in o.data.materials if m}
    rays = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow")
    saved_rays = {r: getattr(low, r) for r in rays}
    for r in rays:
        setattr(low, r, False)
    passes = [("color", "EMIT", "COLOR"), ("normal", "NORMAL", None), ("roughness", "EMIT", "BAKE_ROUGH"), ("metalness", "EMIT", "BAKE_METAL")]
    try:
        for key, kind, route in passes:
            mat.node_tree.nodes.active = mat.node_tree.nodes[key]
            restore = None
            if route == "COLOR":
                restore = _route_color(hi_mats)
            elif route:
                restore = B._route_value(hi_mats, route)
            bpy.ops.object.select_all(action="DESELECT")
            for o in hi_objects:
                o.select_set(True)
            low.select_set(True)
            view_layer.objects.active = low
            kw = dict(type=kind, use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=ray, margin=10,
                      use_clear=True, target="IMAGE_TEXTURES")
            if kind == "NORMAL":
                kw["normal_space"] = "TANGENT"
            try:
                bpy.ops.object.bake(**kw)
            finally:
                if restore:
                    restore()
    finally:
        scene.render.engine = engine
        for r, v in saved_rays.items():
            setattr(low, r, v)
    B.wire_baked(mat)
    assert B.EGG_DIR, "egg_bake.EGG_DIR: set the folder the maps go to"
    os.makedirs(B.EGG_DIR, exist_ok=True)
    for key, img in images.items():
        img.filepath_raw = os.path.join(B.EGG_DIR, weapon_id + "_" + key + ".png")
        img.file_format = "PNG"
        img.save()
    return images


def export(weapon_id, kind, source, hi, glow, root, hilt, tip, budget=4200, size=1024, small=512):
    """Bakes and writes the weapon: assets/weapons/<WeaponId>.fbx and its four maps, and the placements file
    (or SECRET_OUT_DIR / SECRET_PLACEMENTS_DIR). Returns weapon_kit.export's report."""
    saved = (B.make_low, B.bake, B.K.join)
    real_join = B.K.join

    def join(objects, name, coll):
        o = real_join(objects, name, coll)
        if "_Glow_" in name:          # the Neon pieces carry no texture, but their UVs must lie in 0-1 for the gate
            B._unwrap(o)
        return o
    B.make_low, B.bake, B.K.join = make_low, bake, join
    try:
        report = WK.export(weapon_id, kind, source, hi, glow, root, hilt, tip, budget=budget, size=size, small=small)
    finally:
        B.make_low, B.bake, B.K.join = saved
    scrub_paths(os.path.join(OUT_DIR, weapon_id + ".fbx"))
    lua = os.path.join(PLACEMENTS_DIR, weapon_id + ".lua")
    import re
    text = re.sub(r"^-- \w+ by ", "-- Built by ", open(lua).read(), count=1)
    open(lua, "w").write(text)
    return report


def scrub_paths(fbx):
    """The FBX remembers the absolute path its maps were copied from. The committed weapons carry /Users/user/...: the same
    length as the real home folder's name, so the file's length-prefixed strings stay valid. Done to the bytes, in place."""
    home = os.path.expanduser("~")
    user = os.path.basename(home)
    fake = ("user" + "x" * max(0, len(user) - 4))[:len(user)]
    if fake == user or len(fake) != len(user):
        return
    data = open(fbx, "rb").read()
    new = data.replace(("/Users/%s/" % user).encode(), ("/Users/%s/" % fake).encode())
    if new != data:
        open(fbx, "wb").write(new)


def fresh():
    """An empty scene: the startup cube, light and camera, and whatever a earlier job left, removed (a headless
    run starts from the factory file, but a live session may not)."""
    WK.clear()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def collection_tris(objs):
    return sum(_tris(o) for o in objs)

"""Shared building blocks for the egg models (run inside Blender).

Eggs are authored in egg units (the game scales them by 1.3 studs per unit when it places them on
a stand), in Roblox space through worldlib's MeshBuilder: x right, y up, the egg's front toward +z
(the FBX importer turns models 180 degrees, so +z here faces the player in the game). The egg's
bottom sits at the origin.

Export convention (WorldBuilder.placeEgg relies on it): every egg is one FBX,
assets/eggs/<EggId>.fbx, holding "<EggId>_Body" (atlas textured) and one "<EggId>_Glow_<rrggbb>"
part per glowing colour (Neon in the game). The eggs' auras are not meshes: they are particle
VFX built in Studio (src/worldbuild/EggAuraVFX.lua).
"""
import math
import os
import random
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "world"))
import worldlib as W  # noqa: E402

TAU = 2 * math.pi
V = W.Vector
REPO = W.REPO
EGG_DIR = os.path.join(REPO, "assets", "eggs")

def rb_inv(x, y, z):
    """Blender space -> Roblox space (the inverse of worldlib.rb)."""
    return (x, z, -y)


H = 2.7    # egg height
R = 1.02   # egg radius at its widest


# ---------- the egg's surface ----------
def egg_point(u, v, r=R, h=H, swell=0.13, offset=0.0):
    """A point on the egg (u: angle round from the front, 0..1; v: 0 at the bottom, 1 at the top)
    and the outward normal there. Wider below its middle, pointed above. `offset` pushes along the
    normal (for things laid on the shell)."""
    a = TAU * u
    t = math.pi * v
    y = h * (1 - math.cos(t)) / 2
    rad = r * math.sin(t) * (1 + swell * math.cos(t))
    dy = h * math.sin(t) / 2 * math.pi
    dr = r * math.pi * (math.cos(t) * (1 + swell * math.cos(t)) - swell * math.sin(t) ** 2)
    # normal of the profile curve (rad(t), y(t)) turned outward
    nr, ny = dy, -dr
    L = math.hypot(nr, ny) or 1.0
    nr, ny = nr / L, ny / L
    if v <= 1e-6:
        nr, ny = 0.0, -1.0
    if v >= 1 - 1e-6:
        nr, ny = 0.0, 1.0
    n = V((math.sin(a) * nr, ny, math.cos(a) * nr))
    p = V((math.sin(a) * rad, y, math.cos(a) * rad)) + n * offset
    return p, n


def shell(mb, band, nu=40, nv=28, u_repeat=1.0, offset=0.0, v_from=0.0, v_to=1.0, **egg):
    """The egg's skin as a quad grid. The strip's u runs once round the egg (times u_repeat) and
    its v from the bottom to the top, so a strip painted as a function of (u, v) maps onto the
    egg like a label."""
    v0b, v1b = band
    grid = [[egg_point(i / nu, v_from + (v_to - v_from) * j / nv, offset=offset, **egg)[0] for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            uv = []
            for (ii, jj) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                vv = v_from + (v_to - v_from) * jj / nv
                uv.append((u_repeat * ii / nu, v0b + (v1b - v0b) * vv))
            mb.face([tuple(p) for p in q], uv)


def crystal_plates(mb, band, sites, gap=0.9, lift=(0.0, 0.05), tilt=0.14, depth=0.1, seed=0, tones=6, peak=0.0, **egg):
    """The egg as cut crystal plates: one flat polygonal plate per site, its corners where the
    plate meets its neighbours (the centres of the triangles of the sites' hull, laid back on the
    egg). Each plate lies on its own slightly tilted plane that touches its highest corner, so
    no part of it dips under the shell; it is raised a little and shrunk toward its site so a
    seam opens round it, with walls down to `depth` under the shell (anything inside shows only
    through the seams). Each plate samples one tone of the strip (u), shaded by height (v).
    peak > 0 cuts each plate into facets rising to a ridge point set toward its upper end, so the
    facets catch the light differently, like cut crystal."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    for p in sites:
        bm.verts.new(W.rb(p.x, p.y, p.z))
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.verts.ensure_lookup_table()
    v0, v1 = band
    h = egg.get("h", H)

    def on_egg(q):
        # lay a point back onto the egg along the ray from the egg's axis at its height
        y = max(0.0, min(h, q.y))
        vv = math.acos(max(-1.0, min(1.0, 1 - 2 * y / h))) / math.pi
        uu = (math.atan2(q.x, q.z) / TAU) % 1.0
        return egg_point(uu, vv, **egg)

    for vert in bm.verts:
        site = V(rb_inv(*vert.co))
        faces = list(vert.link_faces)
        if len(faces) < 3:
            continue
        sn = egg_point((math.atan2(site.x, site.z) / TAU) % 1.0,
                       math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.0, min(h, site.y)) / h))) / math.pi, **egg)[1]
        ref = V((0, 1, 0)) if abs(sn.y) < 0.9 else V((1, 0, 0))
        e1 = sn.cross(ref).normalized()
        e2 = sn.cross(e1)
        corners = []
        for f in faces:
            c = V(rb_inv(*f.calc_center_median()))
            p, _ = on_egg(c)
            d = p - site
            corners.append((math.atan2(d.dot(e2), d.dot(e1)), p))
        corners = [p for _, p in sorted(corners, key=lambda t: t[0])]
        n = (sn + V((rnd.uniform(-tilt, tilt), rnd.uniform(-tilt, tilt), rnd.uniform(-tilt, tilt)))).normalized()
        c = sum(corners, V((0, 0, 0))) / len(corners)
        top_offset = max((p - c).dot(n) for p in corners + [site]) + rnd.uniform(*lift)
        plane = c + n * top_offset
        top = [plane + ((p - c) - n * (p - c).dot(n)) * gap for p in corners]
        tone = (rnd.randrange(tones) + 0.5) / tones
        shade = lambda p: v0 + (v1 - v0) * max(0.03, min(0.97, p.y / h * 0.85 + 0.1))
        if peak > 0:
            apex = plane + ((sum(top, V((0, 0, 0))) / len(top)) - plane) + n * peak + V((0, 1, 0)) * 0.04
            light = V((0.35, 0.8, 0.5)).normalized()
            for i in range(len(top)):
                j = (i + 1) % len(top)
                fn = (top[j] - top[i]).cross(apex - top[i])
                if fn.dot(n) < 0:
                    fn = -fn
                lit = 0.25 + 0.75 * max(0.0, fn.normalized().dot(light))
                W_oriented_uv(mb, [top[i], top[j], apex], tuple(fn), [(tone, v0 + (v1 - v0) * (0.08 + 0.88 * lit))] * 3)
        else:
            W_oriented_uv(mb, top, tuple(n), [(tone, shade(p)) for p in top])
        for i in range(len(top)):
            j = (i + 1) % len(top)
            ia = on_egg(corners[i])
            ib = on_egg(corners[j])
            bi = ia[0] - ia[1] * depth
            bj = ib[0] - ib[1] * depth
            out = (top[i] + top[j]) / 2 - c
            W_oriented_uv(mb, [top[i], top[j], bj, bi], tuple(out), [(tone, v0 + (v1 - v0) * 0.06)] * 4)
    bm.free()


def W_oriented_uv(mb, pts, normal, uvs):
    """A face wound to face along `normal`, with its own UV per corner."""
    a, b, c = V(pts[0]), V(pts[1]), V(pts[2])
    if (b - a).cross(c - a).dot(V(normal)) < 0:
        pts, uvs = list(reversed(pts)), list(reversed(uvs))
    mb.face([tuple(p) for p in pts], uvs)


def surface_sites(n, seed, **egg):
    """n points spread over the egg's surface (Fibonacci spiral in height), with jitter."""
    rnd = random.Random(seed)
    golden = math.pi * (3 - math.sqrt(5))
    out = []
    for k in range(n):
        y = 0.02 + 0.96 * (k + 0.5) / n          # even in height = even in area on an egg this round
        v = math.acos(1 - 2 * y) / math.pi
        u = (k * golden / TAU + rnd.uniform(-0.03, 0.03)) % 1.0
        out.append(egg_point(u, min(0.99, max(0.01, v + rnd.uniform(-0.015, 0.015))), **egg)[0])
    return out


def strip_between(mb, a, b, normal, width, band, u=0.5, lift=0.012):
    """A flat strip from a to b lying on a surface with the given normal, raised by lift."""
    a, b, n = V(a), V(b), V(normal).normalized()
    d = (b - a).normalized()
    s = d.cross(n).normalized() * width / 2
    a, b = a + n * lift, b + n * lift
    q = [tuple(a - s), tuple(b - s), tuple(b + s), tuple(a + s)]
    W_oriented(mb, q, tuple(n), band, u)


def W_oriented(mb, pts, normal, band, u, shade=1.0):
    """A face wound to face along `normal`, sampling one point of the band."""
    a, b, c = V(pts[0]), V(pts[1]), V(pts[2])
    if (b - a).cross(c - a).dot(V(normal)) < 0:
        pts = list(reversed(pts))
    v0, v1 = band
    mb.face([tuple(p) for p in pts], [(u, v0 + (v1 - v0) * shade)] * len(pts))


def tube(mb, pts, radius_fn, sides, band, per=4, closed=False):
    """A tube along a smooth curve; radius_fn(t) for t in 0..1. Closed tubes join their ends."""
    pts = [V(p) for p in pts]
    if closed:
        curve = [V(p) for p in W.catmull(pts + pts[:3], per)][per:per * (len(pts) + 1) + 1]
    else:
        curve = [V(p) for p in W.catmull(pts, per)]
    n = len(curve)
    rings = []
    ref = V((0, 1, 0))
    # the tube carries its frame along the curve (parallel transport), so it never flips where the
    # curve turns near vertical and cannot twist through itself
    if closed:
        tangents = [(curve[(i + 1) % n] - curve[i - 1]).normalized() for i in range(n)]
    else:
        tangents = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    r0 = ref if abs(tangents[0].dot(ref)) < 0.9 else V((1, 0, 0))
    carried = tangents[0].cross(r0).normalized()
    frames = []
    for T in tangents:
        carried = (carried - T * carried.dot(T)).normalized()
        frames.append(carried)
    twist = 0.0
    if closed:
        # carried once round, the frame comes back turned: spread that turn along the loop so
        # the tube meets itself without a kink
        back = (frames[-1] - tangents[0] * frames[-1].dot(tangents[0])).normalized()
        twist = math.atan2(frames[0].cross(back).dot(tangents[0]), frames[0].dot(back))
    for i, c in enumerate(curve):
        T = tangents[i]
        s = frames[i]
        if twist:
            a = -twist * i / n
            s = (s * math.cos(a) + T.cross(s) * math.sin(a)).normalized()
        up = s.cross(T).normalized()
        r = radius_fn(i / (n - 1))
        rings.append((c, [c + (s * math.cos(TAU * k / sides) + up * math.sin(TAU * k / sides)) * r for k in range(sides)]))
    v0, v1 = band
    count = n if closed else n - 1
    for i in range(count):
        (c0, r0_), (c1, r1_) = rings[i], rings[(i + 1) % n]
        for k in range(sides):
            j = (k + 1) % sides
            q = [r0_[k], r0_[j], r1_[j], r1_[k]]
            out = (q[0] + q[1] + q[2] + q[3]) / 4 - (c0 + c1) / 2
            W_oriented(mb, q, tuple(out), band, (k + 0.5) / sides, 0.35 + 0.6 * max(0.0, out.normalized().y * 0.5 + 0.5))
    if not closed:
        for end, (c, ring) in ((0, rings[0]), (1, rings[-1])):
            d = (rings[1][0] - rings[0][0]) if end == 0 else (rings[-1][0] - rings[-2][0])
            nrm = -d if end == 0 else d
            for k in range(sides):
                W_oriented(mb, [ring[k], ring[(k + 1) % sides], c], tuple(nrm), band, 0.5, 0.6)
    return curve


def ring(mb, centre, axis, radius, thick, band, segments=48, width=None, phase=0.0):
    """A flat ring (an annulus band of the given width, thick in the axis direction) round axis."""
    axis = V(axis).normalized()
    ref = V((0, 1, 0)) if abs(axis.y) < 0.9 else V((1, 0, 0))
    s = axis.cross(ref).normalized()
    t = axis.cross(s).normalized()
    c = V(centre)
    width = width if width is not None else thick
    ri, ro = radius - width / 2, radius + width / 2
    for k in range(segments):
        a0, a1 = phase + TAU * k / segments, phase + TAU * (k + 1) / segments
        d0 = s * math.cos(a0) + t * math.sin(a0)
        d1 = s * math.cos(a1) + t * math.sin(a1)
        for side in (-1, 1):
            off = axis * side * thick / 2
            q = [c + d0 * ri + off, c + d0 * ro + off, c + d1 * ro + off, c + d1 * ri + off]
            W_oriented(mb, q, tuple(axis * side), band, (k + 0.5) / segments, 1.0 if side > 0 else 0.7)
        for rr, sgn in ((ro, 1), (ri, -1)):
            q = [c + d0 * rr - axis * thick / 2, c + d1 * rr - axis * thick / 2, c + d1 * rr + axis * thick / 2, c + d0 * rr + axis * thick / 2]
            W_oriented(mb, q, tuple((d0 + d1) * sgn), band, (k + 0.5) / segments, 0.8)


def gem(mb, centre, normal, up, width, height, depth, band, crown=0.35):
    """A cut gem lying on a surface: a kite-shaped table rising to a point at its front, with a
    shallow pavilion behind it (the back half sinks into whatever it is set in)."""
    n, u = V(normal).normalized(), V(up).normalized()
    s = u.cross(n).normalized()
    u = n.cross(s).normalized()
    c = V(centre)
    rim = [c + u * height / 2, c + s * width / 2 + u * height * 0.08, c - u * height / 2, c - s * width / 2 + u * height * 0.08]
    mid = [c + (p - c) * 0.45 + n * depth * crown for p in rim]
    tip = c + n * depth
    back = c - n * depth * 0.6
    for i in range(4):
        j = (i + 1) % 4
        W_oriented(mb, [rim[i], rim[j], mid[j], mid[i]], tuple(((rim[i] + rim[j]) / 2 - c).normalized() + n * 0.6), band, (i + 0.5) / 4, 0.7)
        W_oriented(mb, [mid[i], mid[j], tip], tuple(n + ((mid[i] + mid[j]) / 2 - c).normalized() * 0.4), band, (i + 0.5) / 4, 1.0)
        W_oriented(mb, [rim[j], rim[i], back], tuple(((rim[i] + rim[j]) / 2 - c).normalized() - n * 0.6), band, 0.5, 0.4)


def shard(mb, base, direction, length, width, band, seed=0, sides=5, shade_tip=1.0):
    """A sharp crystal splinter: an irregular prism that tapers to a point."""
    rnd = random.Random(seed)
    d = V(direction).normalized()
    ref = V((0, 1, 0)) if abs(d.y) < 0.9 else V((1, 0, 0))
    s = d.cross(ref).normalized()
    t = d.cross(s).normalized()
    b = V(base)
    radii = [width * rnd.uniform(0.6, 1.0) for _ in range(sides)]
    angles = [TAU * k / sides + rnd.uniform(-0.25, 0.25) for k in range(sides)]
    ring0 = [b + (s * math.cos(a) + t * math.sin(a)) * r for a, r in zip(angles, radii)]
    shoulder = b + d * length * rnd.uniform(0.55, 0.72)
    ring1 = [shoulder + (s * math.cos(a) + t * math.sin(a)) * r * 0.75 for a, r in zip(angles, radii)]
    tip = b + d * length
    for k in range(sides):
        j = (k + 1) % sides
        out = (s * math.cos(angles[k]) + t * math.sin(angles[k]))
        W_oriented(mb, [ring0[k], ring0[j], ring1[j], ring1[k]], tuple(out), band, (k + 0.5) / sides, 0.55)
        W_oriented(mb, [ring1[k], ring1[j], tip], tuple(out + d), band, (k + 0.5) / sides, shade_tip)
        W_oriented(mb, [ring0[j], ring0[k], b - d * width * 0.5], tuple(-d), band, 0.5, 0.3)


def xiangyun(mb, centre, normal, up, size, band, thick=0.06, turns=1.3, flip=1):
    """A raised auspicious cloud ornament on a surface: three spiral curls of a tube, the middle
    one larger, joined by a sweeping base stroke."""
    n, u = V(normal).normalized(), V(up).normalized()
    s = u.cross(n).normalized() * flip
    u = n.cross(s).normalized()
    c = V(centre)
    for k, (dx, dy, r) in enumerate(((-0.42, 0.0, 0.26), (0.0, 0.16, 0.36), (0.44, 0.02, 0.24))):
        cc = c + (s * dx + u * dy) * size
        pts = []
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            a = TAU * turns * t + (math.pi if k == 1 else 0.0) * flip
            # the curl tightens only until it is about 2.5 tube-widths across, so the tube never
            # folds through itself at the centre
            rr = max(r * size * (1 - 0.82 * t), thick * 1.3)
            pts.append(cc + (s * math.cos(a) * flip + u * math.sin(a)) * rr + n * thick)
        tube(mb, pts, lambda t: thick * (1.0 - 0.5 * t), 5, band, per=1)
    base = [c + (s * x + u * (-0.22 - 0.05 * math.sin(math.pi * (x + 0.7) / 1.4))) * size + n * thick for x in (-0.7, -0.35, 0.0, 0.35, 0.7)]
    tube(mb, base, lambda t: thick * (0.6 + 0.4 * math.sin(math.pi * t)), 5, band, per=3)


# ---------- texturing ----------
def strip_fn(stops, noise=0.0, seed=0, freq=6.0):
    """A strip painted as a vertical gradient through colour stops [(v, (r, g, b)), ...]."""
    def fn(u, v):
        for (va, ca), (vb, cb) in zip(stops, stops[1:]):
            if va <= v <= vb:
                t = (v - va) / max(1e-6, vb - va)
                c = [ca[i] + (cb[i] - ca[i]) * t for i in range(3)]
                break
        else:
            c = list(stops[-1][1] if v > stops[-1][0] else stops[0][1])
        if noise:
            k = noise * W.fbm(u * freq * 3 + seed, v * freq, seed=seed, octaves=3)
            c = [max(0.0, min(1.0, x + k)) for x in c]
        return tuple(c)
    return fn


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------- export ----------
def glow_material(hexstr):
    """A flat emissive material named by its colour; objects using it become the egg's Neon parts."""
    name = "EggGlow_" + hexstr
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    for nd in list(t.nodes):
        t.nodes.remove(nd)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*[c ** 2.2 for c in rgb(hexstr)], 1)
    em.inputs["Strength"].default_value = 3.0
    t.links.new(em.outputs[0], out.inputs[0])
    m["glow"] = hexstr
    return m


def join(objects, name, coll):
    """Merge objects into one mesh object called name."""
    bm = bmesh.new()
    mats = []
    for o in objects:
        me = o.data.copy()
        me.transform(o.matrix_world)
        offset = len(mats)
        mats.extend(me.materials)
        for p in me.polygons:
            p.material_index += offset
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)   # zero-area faces at points and poles
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats[:1]:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def export_egg(egg_id, body_objects, glow_objects, image, coll):
    """Writes assets/eggs/<EggId>.fbx: <EggId>_Body (textured) and <EggId>_Glow_<hex> parts.
    glow_objects: {hexstr: [objects]}."""
    parts = [join(body_objects, egg_id + "_Body", coll)]
    for hexstr, objs in glow_objects.items():
        if objs:
            parts.append(join(objs, egg_id + "_Glow_" + hexstr, coll))
    W.export_batch(parts, os.path.join(EGG_DIR, egg_id + ".fbx"), image=image)
    for p in parts:
        me = p.data
        bpy.data.objects.remove(p, do_unlink=True)
        bpy.data.meshes.remove(me)

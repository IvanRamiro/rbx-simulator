"""Shared helpers for building the floating-island world in Blender.

Coordinates: island data is authored in Roblox studs (X east, Y up, Z south). Blender is Z-up,
so a Roblox point (x, y, z) lives at Blender (x, -z, y). 1 Blender unit = 1 stud.
"""
import bpy, bmesh, math, os
from mathutils import Vector

REPO = "/Users/ivan/qi-aura-simulator"


def rb(x, y, z):
    """Roblox studs -> Blender vector."""
    return Vector((x, -z, y))


def collection(name, parent=None):
    coll = bpy.data.collections.get(name)
    if not coll:
        coll = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(coll)
    return coll


def clear_collection(coll):
    for o in list(coll.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0 and isinstance(me, bpy.types.Mesh):
            bpy.data.meshes.remove(me)


def mesh_object(name, verts, faces, coll, uvs=None, smooth=True, material=None):
    """verts in Blender space; uvs: per-face list of per-corner (u, v) or None."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    if uvs is not None:
        layer = me.uv_layers.new(name="UVMap")
        for poly, fuv in zip(me.polygons, uvs):
            for li, uv in zip(poly.loop_indices, fuv):
                layer.data[li].uv = uv
    for p in me.polygons:
        p.use_smooth = smooth
    if material:
        me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


# ---------- deterministic value noise ----------
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise2(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy


def fbm(x, y, seed=0, octaves=4, lac=2.0, gain=0.5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * (noise2(x * freq, y * freq, seed + o * 17) * 2 - 1)
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return t * t * (3 - 2 * t)


def gauss(dx, dz, r):
    return math.exp(-(dx * dx + dz * dz) / (2 * r * r))


# ---------- heightfield export ----------
def export_heightfield(island, centre, cell, half_extent, sample, materials, path, priority=None, water=None, turns=0):
    """Sample the island top on a grid of `cell`-stud columns and write a Lua data module.

    sample(x, z) -> (height or None, material name) in island-local studs (x east, z south).
    water(x, z) -> terrain-water surface height (island-local) or None, for pools.
    The module holds Origin (world corner), Cell, Size, Heights (row-major, y offsets, 0 = none)
    and Materials (indices into the Materials list). Heights are stored relative to centre.Y.
    The grid is written unturned; `turns` (quarter turns, layout.py) is recorded for the builder,
    which turns the grid about the centre when it fills the terrain.
    """
    # Terrain:WriteVoxels needs the region on the world's 4-stud voxel grid, so each axis's grid
    # corner is snapped down to it independently (the grid then covers the half extent and a bit)
    corner_x = math.floor((centre[0] - half_extent) / cell) * cell
    corner_z = math.floor((centre[2] - half_extent) / cell) * cell
    n = int(math.ceil((centre[0] + half_extent - corner_x) / cell))
    n = max(n, int(math.ceil((centre[2] + half_extent - corner_z) / cell)))
    heights, mats, waters = [], [], []
    for j in range(n):
        for i in range(n):
            x = corner_x - centre[0] + (i + 0.5) * cell
            z = corner_z - centre[2] + (j + 0.5) * cell
            h, m = sample(x, z)
            if h is not None and priority:
                # a path or plaza that covers part of the cell wins over the base material,
                # so narrow features stay continuous on the 4-stud voxel grid
                counts = {}
                for sx in (-0.33, 0, 0.33):
                    for sz in (-0.33, 0, 0.33):
                        _, sm = sample(x + sx * cell, z + sz * cell)
                        if sm:
                            counts[sm] = counts.get(sm, 0) + 1
                for name, need in priority:
                    if counts.get(name, 0) >= need:
                        m = name
                        break
            if h is None:
                heights.append("false")
                mats.append("0")
            else:
                heights.append("%.2f" % h)
                mats.append(str(materials.index(m) + 1))
            wl = water(x, z) if (water and h is not None) else None
            waters.append("%.2f" % wl if wl is not None and wl > h else "false")
    lines = [
        "-- Generated by tools/blender/world (%s). Do not edit by hand." % island,
        "return {",
        '    Island = "%s",' % island,
        "    Centre = Vector3.new(%g, %g, %g)," % centre,
        "    Turns = %d, -- quarter turns about the centre, each adding 90 degrees of bearing" % turns,
        "    Origin = Vector2.new(%g, %g), -- world X/Z of the grid's first corner" % (corner_x, corner_z),
        "    Cell = %d," % cell,
        "    Size = %d," % n,
        "    Materials = { %s }," % ", ".join('"%s"' % m for m in materials),
    ]
    def chunked(name, vals):
        out = ["    %s = {" % name]
        for k in range(0, len(vals), n):
            out.append("        " + ", ".join(vals[k:k + n]) + ",")
        out.append("    },")
        return out
    lines += chunked("Heights", heights) + chunked("MaterialIndex", mats)
    if water:
        lines += chunked("WaterLevels", waters)
    lines += ["}", ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return n


# ---------- palette atlas ----------
def atlas_image(name, size, strips):
    """strips: list of (rows, colour_fn(u, v) -> (r, g, b)). Each strip spans the full width and
    `rows` pixel rows; returns the image and a dict strip index -> (v0, v1) in UV space."""
    import numpy as np
    img = bpy.data.images.get(name) or bpy.data.images.new(name, size, size, alpha=False)
    if img.size[0] != size:
        img.scale(size, size)
    px = np.zeros((size, size, 4), np.float32); px[..., 3] = 1
    bands, row = {}, 0
    for idx, (rows, fn) in enumerate(strips):
        for y in range(row, min(size, row + rows)):
            v = (y - row + 0.5) / rows
            for x in range(size):
                px[y, x, :3] = fn((x + 0.5) / size, v)
        bands[idx] = ((row + 1.5) / size, (row + rows - 1.5) / size)
        row += rows
    img.pixels.foreach_set(px.ravel())
    img.update()
    return img, bands


def textured_material(name, image):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    tex = t.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Linear"
    t.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(bsdf.outputs[0], out.inputs[0])
    return m


# ---------- curves and tubes ----------
def catmull(points, per=8):
    pts = [Vector(p) for p in points]
    pts = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-2])
    return out


def tube(name, coll, points, radius_fn, sides, mat, band, per=8, uv_repeat=1.0, wobble=0.0, seed=0, cap_end=True):
    """A tube along a Catmull-Rom curve (Blender-space points). radius_fn(t) with t in 0..1.
    UVs: u around the tube, v along it inside `band` (v0, v1). Returns the object."""
    curve = catmull(points, per)
    n = len(curve)
    T = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - T[0] * ref.dot(T[0])).normalized()
    verts, faces, uvs = [], [], []
    v0, v1 = band
    for i, c in enumerate(curve):
        nrm = (nrm - T[i] * nrm.dot(T[i])).normalized()
        bi = T[i].cross(nrm)
        t = i / (n - 1)
        r = radius_fn(t)
        for k in range(sides):
            a = 2 * math.pi * k / sides
            w = 1 + wobble * (noise2(i * 0.7 + seed, k * 1.3, seed) - 0.5)
            verts.append(c + (nrm * math.cos(a) + bi * math.sin(a)) * r * w)
    for i in range(n - 1):
        for k in range(sides):
            a = i * sides + k; b = i * sides + (k + 1) % sides
            c2 = (i + 1) * sides + (k + 1) % sides; d = (i + 1) * sides + k
            faces.append([a, b, c2, d])
            u0, u1 = k / sides * uv_repeat, (k + 1) / sides * uv_repeat
            va = v0 + (v1 - v0) * (i / (n - 1)); vb = v0 + (v1 - v0) * ((i + 1) / (n - 1))
            uvs.append([(u0, va), (u1, va), (u1, vb), (u0, vb)])
    if cap_end:
        tip = len(verts)
        verts.append(curve[-1] + T[-1] * radius_fn(1.0) * 0.8)
        for k in range(sides):
            faces.append([(n - 1) * sides + k, (n - 1) * sides + (k + 1) % sides, tip])
            uvs.append([(0, v1), (0, v1), (0, v1)])
    return mesh_object(name, verts, faces, coll, uvs=uvs, material=mat)


# ---------- export ----------
def export_batch(objects, fbx_path, image=None, anchor_name=None):
    """Export meshes to one FBX (Roblox-ready axes; 1 Blender unit = 1 stud). If anchor_name is
    given, a 1-stud cube at the Blender origin is included under that name so the imported model
    can be moved until the anchor sits on the island centre. Kit pieces are exported at the origin."""
    os.makedirs(os.path.dirname(fbx_path), exist_ok=True)
    if image is not None:
        image.filepath_raw = os.path.splitext(fbx_path)[0] + "_atlas.png"
        image.file_format = "PNG"
        image.save()
    extra = []
    if anchor_name:
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        me = bpy.data.meshes.new(anchor_name); bm.to_mesh(me); bm.free()
        a = bpy.data.objects.new(anchor_name, me)
        bpy.context.scene.collection.objects.link(a)
        extra.append(a)
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objects) + extra:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE")
    for a in extra:
        me = a.data; bpy.data.objects.remove(a, do_unlink=True); bpy.data.meshes.remove(me)


# ---------- mesh builder (one object per asset, authored in Roblox studs) ----------
class MeshBuilder:
    """Accumulates faces for a single mesh. Points are Roblox-space tuples (x, y, z); UVs are
    picked inside a palette band (v0, v1) so every face samples one atlas strip."""

    def __init__(self):
        self.verts, self.faces, self.uvs = [], [], []

    def face(self, pts, uv):
        base = len(self.verts)
        self.verts.extend(rb(*p) for p in pts)
        self.faces.append(list(range(base, base + len(pts))))
        self.uvs.append(uv)

    def quad(self, a, b, c, d, band, u=0.5, shade=(1.0, 1.0, 0.6, 0.6)):
        """shade: 0..1 position inside the band for each corner (1 = top of the strip)."""
        v0, v1 = band
        self.face([a, b, c, d], [(u, v0 + (v1 - v0) * s) for s in shade])

    def tri(self, a, b, c, band, u=0.5, shade=(1.0, 1.0, 1.0)):
        v0, v1 = band
        self.face([a, b, c], [(u, v0 + (v1 - v0) * s) for s in shade])

    def box(self, centre, size, band, yaw=0.0, u=0.5, top_shade=1.0, side_shade=0.6, bottom=False):
        cx, cy, cz = centre
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        cs, sn = math.cos(yaw), math.sin(yaw)

        def p(x, y, z):  # yaw about +Y, Roblox convention
            return (cx + x * cs + z * sn, cy + y, cz - x * sn + z * cs)
        t = [p(-hx, hy, -hz), p(hx, hy, -hz), p(hx, hy, hz), p(-hx, hy, hz)]
        b = [p(-hx, -hy, -hz), p(hx, -hy, -hz), p(hx, -hy, hz), p(-hx, -hy, hz)]
        self.quad(t[3], t[2], t[1], t[0], band, u, (top_shade,) * 4)
        for i in range(4):
            j = (i + 1) % 4
            self.quad(t[i], t[j], b[j], b[i], band, u, (side_shade, side_shade, side_shade * 0.6, side_shade * 0.6))
        if bottom:
            self.quad(b[0], b[1], b[2], b[3], band, u, (0.2,) * 4)

    def lathe(self, profile, seg, band, centre=(0, 0, 0), rmod=None, phase=0.0, u_repeat=1.0, cap_top=True, cap_bottom=False):
        """Surface of revolution. profile: [(radius, y, shade)] walked along the surface from the
        top centre outward and down (that order makes the normals face out).
        rmod(theta, k) scales the radius of ring k at angle theta (for petals, facets, wobble)."""
        cx, cy, cz = centre
        rings = []
        for k, (r, y, s) in enumerate(profile):
            ring = []
            for i in range(seg):
                th = TAU_ * i / seg + phase
                rr = r * (rmod(th, k) if rmod else 1.0)
                ring.append((cx + math.cos(th) * rr, cy + y, cz + math.sin(th) * rr))
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(seg):
                j = (i + 1) % seg
                ua, ub = u_repeat * i / seg, u_repeat * (i + 1) / seg
                self.quad(rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i], band, (ua + ub) / 2,
                          (profile[k][2], profile[k][2], profile[k + 1][2], profile[k + 1][2]))
        if cap_top and profile[0][0] > 0:
            top = (cx, cy + profile[0][1], cz)
            for i in range(seg):
                self.tri(rings[0][(i + 1) % seg], rings[0][i], top, band, 0.5, (profile[0][2],) * 3)
        if cap_bottom and profile[-1][0] > 0:
            bot = (cx, cy + profile[-1][1], cz)
            for i in range(seg):
                self.tri(rings[-1][i], rings[-1][(i + 1) % seg], bot, band, 0.5, (profile[-1][2],) * 3)
        return rings

    def object(self, name, coll, mat, smooth=False):
        o = mesh_object(name, self.verts, self.faces, coll, uvs=self.uvs, smooth=smooth, material=mat)
        if smooth:
            # every face was built with its own corners; weld them so shading flows across faces
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
            bm.to_mesh(o.data)
            bm.free()
            for poly in o.data.polygons:
                poly.use_smooth = True
        return o


TAU_ = 2 * math.pi


def mb_tube(mb, points, radius_fn, sides, band, per=6, u_repeat=1.0):
    """Adds a tube along a Catmull-Rom curve of Roblox-space points to a MeshBuilder (open ends
    are capped at the tip only). Returns the curve points."""
    curve = [Vector(p) for p in catmull(points, per)]
    n = len(curve)
    T = [(curve[min(i + 1, n - 1)] - curve[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - T[0] * ref.dot(T[0])).normalized()
    rings = []
    for i, c in enumerate(curve):
        nrm = (nrm - T[i] * nrm.dot(T[i])).normalized()
        bi = T[i].cross(nrm)
        r = radius_fn(i / (n - 1))
        rings.append([tuple(c + (nrm * math.cos(TAU_ * k / sides) + bi * math.sin(TAU_ * k / sides)) * r) for k in range(sides)])
    v0, v1 = band
    for i in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            quad = [rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]]
            mid = Vector([sum(p[q] for p in quad) / 4 for q in range(3)])
            out = mid - (curve[i] + curve[i + 1]) / 2
            nx = Vector(quad[1]) - Vector(quad[0]); ny = Vector(quad[3]) - Vector(quad[0])
            if nx.cross(ny).dot(out) < 0:
                quad = quad[::-1]
            u = u_repeat * (k + 0.5) / sides
            mb.face(quad, [(u, v0 + (v1 - v0) * (0.35 + 0.5 * (i / n)))] * 4)
    tip = tuple(curve[-1] + T[-1] * radius_fn(1.0) * 0.8)
    for k in range(sides):
        tri = [rings[-1][k], rings[-1][(k + 1) % sides], tip]
        a, b, c = (Vector(p) for p in tri)
        if (b - a).cross(c - a).dot(T[-1]) < 0:
            tri = tri[::-1]
        mb.face(tri, [(0.5, v1)] * 3)
    return curve

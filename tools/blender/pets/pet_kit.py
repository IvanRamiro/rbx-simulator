"""The workshop for the recreated pets: one smooth skin on a skeleton, painted high-detail, baked to one set of maps, exported for File > Import 3D.

Each pet's own script (tools/blender/pets/<pet>.py) holds its design and calls this. Faces -Y, Z up, 1 unit = 1 metre in Blender.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TAU = 2 * math.pi
scene = bpy.context.scene
PET, N, OUT, TOOLS, HI, GAME = None, None, None, None, None, None


def start(pet, egg):
    """Clears the start-up scene and names everything after this pet. Returns the collections for the high-detail model and the game mesh."""
    global PET, N, OUT, TOOLS, HI, GAME
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    PET, N = pet, pet + "_"
    trial = os.environ.get("PET_KIT_TRIAL")      # a folder that takes the maps, FBX and .blend, so a trial run leaves the real ones alone
    OUT = trial or os.path.join(ROOT, "assets/pets", egg)
    TOOLS = trial or os.path.join(ROOT, "tools/blender/pets", egg)
    HI, GAME = get_coll(pet + "_Hi"), get_coll(pet)
    return HI, GAME


# ---------- small tools ----------
def V(*a):
    return Vector(a)


def rgb(r, g, b):
    """sRGB 0-255 to linear."""
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return np.array((f(r), f(g), f(b)))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) else t
    return a * (1 - t) + b * t


def mir(v, side):
    return Vector((v.x * side, v.y, v.z))


def catmull(pts, per=10):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-2].copy())
    return out


def noise3(p, f, seed=0.0):
    x = p * f + seed
    return (np.sin(x[:, 0] * 1.3 + np.sin(x[:, 1] * 1.7 + seed) * 1.2) + np.sin(x[:, 1] * 1.1 + np.sin(x[:, 2] * 1.9) * 1.3) + np.sin(x[:, 2] * 1.5 + np.sin(x[:, 0] * 2.1) * 1.1)) / 3


def hash01(ix, iy, iz, seed=0):
    """A repeatable random 0..1 per integer cell."""
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / 0xFFFFFF


def value_noise(p, f, seed=0):
    """Smooth lattice noise, 0..1, for clouds."""
    q = p * f
    i = np.floor(q).astype(np.int64)
    t = q - i
    t = t * t * (3 - 2 * t)
    v = 0.0
    for dx in (0, 1):
        wx = t[:, 0] if dx else 1 - t[:, 0]
        for dy in (0, 1):
            wy = t[:, 1] if dy else 1 - t[:, 1]
            for dz in (0, 1):
                wz = t[:, 2] if dz else 1 - t[:, 2]
                v = v + wx * wy * wz * hash01(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return v


def fbm(p, f, octaves=5, seed=0):
    total, amp, norm = 0.0, 1.0, 0.0
    for k in range(octaves):
        total = total + amp * value_noise(p, f * 2 ** k, seed + k)
        norm += amp
        amp *= 0.52
    return total / norm


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()

    def ball(self, c, radii, seg=48, rings=32):
        m = Matrix.Translation(c) @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1))
        bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=m)

    def tube(self, pts, rfn, sides=16, flat=1.0, plane=V(1, 0, 0), caps=True):
        n = len(pts)
        rings = []
        for i, p in enumerate(pts):
            tan = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            side = plane - tan * tan.dot(plane)
            side = side.normalized() if side.length > 1e-5 else tan.orthogonal().normalized()
            up = tan.cross(side).normalized()
            r = rfn(i / (n - 1))
            rings.append([self.bm.verts.new(p + side * math.cos(TAU * k / sides) * r * flat + up * math.sin(TAU * k / sides) * r) for k in range(sides)])
        for i in range(n - 1):
            for k in range(sides):
                k2 = (k + 1) % sides
                self.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
        if caps:
            self.bm.faces.new(rings[0])
            self.bm.faces.new(list(reversed(rings[-1])))

    def sheet(self, point, thick, nu, nv):
        """A closed blade. point(u, v) on its middle surface."""
        bm = self.bm

        def P(i, j):
            return Vector(point(i / nu, j / nv))
        top, bot = [], []
        for i in range(nu + 1):
            rt, rb = [], []
            for j in range(nv + 1):
                p = P(i, j)
                du = P(min(i + 1, nu), j) - P(max(i - 1, 0), j)
                dv = P(i, min(j + 1, nv)) - P(i, max(j - 1, 0))
                nrm = du.cross(dv)
                nrm = nrm.normalized() if nrm.length > 1e-9 else V(0, 0, 1)
                t = thick(i / nu, j / nv) / 2
                rt.append(bm.verts.new(p + nrm * t))
                rb.append(bm.verts.new(p - nrm * t))
            top.append(rt)
            bot.append(rb)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
                bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j]))
        for i in range(nu):
            bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]))
            bm.faces.new((top[i + 1][nv], bot[i + 1][nv], bot[i][nv], top[i][nv]))
        for j in range(nv):
            bm.faces.new((top[0][j + 1], bot[0][j + 1], bot[0][j], top[0][j]))
            bm.faces.new((top[nu][j], bot[nu][j], bot[nu][j + 1], top[nu][j + 1]))

    def finish(self, name, coll, smooth_shade=True, recalc=True):
        if recalc:
            bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        if smooth_shade:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        return o


def apply_mods(o, mods):
    for kind, props in mods:
        md = o.modifiers.new(kind, kind)
        for k, v in props.items():
            setattr(md, k, v)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    old = o.data
    o.modifiers.clear()
    o.data = me
    bpy.data.meshes.remove(old)
    return o


def get_coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
    return c


def select_only(objs, active=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def tree_of(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def on_surface(tree, p, dirn, lift):
    loc, nrm, _, _ = tree.ray_cast(p - dirn * 0.5, dirn, 1.5)
    return (loc + nrm * lift) if loc else p


# ---------- painting: per vertex, baked to the maps later ----------
def verts(o):
    me = o.data
    p = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", p)
    return p.reshape(-1, 3)


def normals(o):
    me = o.data
    n = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertex_normals.foreach_get("vector", n)
    return n.reshape(-1, 3)


def set_verts(o, p):
    o.data.vertices.foreach_set("co", p.ravel())
    o.data.update()


def paint(o, color, rough, metal=None):
    me = o.data
    a = me.attributes.get("paint") or me.attributes.new("paint", "FLOAT_COLOR", "POINT")
    rgba = np.ones((len(color), 4))
    rgba[:, :3] = np.clip(color, 0, 1)
    a.data.foreach_set("color", rgba.ravel())
    b = me.attributes.get("rough") or me.attributes.new("rough", "FLOAT", "POINT")
    b.data.foreach_set("value", np.broadcast_to(rough, (len(color),)).astype(float))
    if metal is not None:
        c = me.attributes.get("metal") or me.attributes.new("metal", "FLOAT", "POINT")
        c.data.foreach_set("value", np.broadcast_to(metal, (len(color),)).astype(float))


def plain(o, colour, rough, metal=None):
    n = len(o.data.vertices)
    paint(o, np.broadcast_to(colour, (n, 3)), np.full(n, rough), None if metal is None else np.full(n, metal))


def nearest_on(path, points):
    """Per point: the fraction along a sampled path and the distance to it."""
    a = np.array([tuple(p) for p in path])
    ab = a[1:] - a[:-1]
    best_d = np.full(len(points), 1e9)
    best_f = np.zeros(len(points))
    L = (ab * ab).sum(1) + 1e-12
    for i in range(len(ab)):
        t = np.clip(((points - a[i]) * ab[i]).sum(1) / L[i], 0, 1)
        d = np.linalg.norm(points - (a[i] + ab[i] * t[:, None]), axis=1)
        take = d < best_d
        best_d[take] = d[take]
        best_f[take] = (i + t[take]) / len(ab)
    return best_f, best_d


def sheet_hi(point, thick, nu, nv, name, colour, rough, relief):
    m = Mesh()
    m.sheet(point, thick, nu, nv)
    o = m.finish(name, HI)
    # grid: (nu + 1) * (nv + 1) top and bottom pairs in order, then displace and paint by u, v
    count = (nu + 1) * (nv + 1) * 2
    uu = np.zeros(count)
    vv = np.zeros(count)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    P = verts(o)
    Nn = normals(o)
    set_verts(o, P + Nn * relief(uu, vv)[:, None])
    paint(o, colour(uu, vv), rough(uu, vv))
    return o


# ---------- eyes ----------
class EyeFrame:
    """An eyeball and its doll's lids. upper, lower: (edge, how far back it runs, in degrees; gap off the ball, in metres)."""

    def __init__(self, centre, axis, side, radius, upper, lower, tilt=7.0, shell=(14, 166)):
        self.side, self.centre, self.axis, self.radius = side, centre, axis, radius
        self.lids = {True: upper, False: lower}
        self.shell = (math.radians(shell[0]), math.radians(shell[1]))
        self.outer = (V(0, 0, 1).cross(self.axis)).normalized() * (-side)   # pointing out to its side of the head
        if self.outer.x * side < 0:
            self.outer = -self.outer
        self.up = self.axis.cross(self.outer).normalized()
        if self.up.z < 0:
            self.up = -self.up
        # the lids hinge on a line through the eye's centre, its outer end raised a little: a sly tilt to the whole opening
        t = math.radians(tilt)
        self.lid_up = (self.up * math.cos(t) - self.outer * math.sin(t)).normalized()
        self.hinge = self.axis.cross(self.lid_up).normalized()      # a turn this way about it lifts a lid

    def direction(self, az, el):
        return (self.axis * (math.cos(el) * math.cos(az)) + self.outer * (math.cos(el) * math.sin(az)) + self.up * math.sin(el)).normalized()

    def lid(self, phi, h):
        return (self.hinge * math.cos(h) + (self.axis * math.cos(phi) + self.lid_up * math.sin(phi)) * math.sin(h)).normalized()


def eye_coords(o, fr):
    """Per vertex of an eyeball: x, y across its face (-1..1), and how far round to the front."""
    P = verts(o) - np.array(tuple(fr.centre))
    d = P / np.linalg.norm(P, axis=1)[:, None]
    A, X, Y = np.array(tuple(fr.axis)), np.array(tuple(fr.outer)), np.array(tuple(fr.up))
    return (d * X).sum(1), (d * Y).sum(1), (d * A).sum(1)


def build_eye(fr, name):
    m = Mesh()
    q = fr.axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_uvsphere(m.bm, u_segments=220, v_segments=150, radius=fr.radius, matrix=Matrix.Translation(fr.centre) @ q)
    return m.finish(N + name + "EyeHi", HI)


def lid_patch(fr, upper, res=(96, 64), thick=0.0045):
    """A doll's eyelid: a slice of a shell round the ball, hung on the hinge, its edge a great circle. It closes by turning on the hinge,
    and everything past the edge is buried in the head at rest and stays buried when it turns."""
    e, far, gap = fr.lids[upper]
    h0, h1 = fr.shell

    def point(u, v):
        phi = math.radians(e + (far - e) * u ** 1.8)     # packed toward the edge, for the lash line
        return fr.centre + fr.lid(phi, h0 + (h1 - h0) * v) * (fr.radius + gap)

    m = Mesh()
    m.sheet(point, lambda u, v: thick, res[1], res[0])
    return m


def build_lid(fr, upper, name, skin, line, lower_share=0.5):
    """skin: its colour. line: the lash line's colour. Returns the object."""
    m = lid_patch(fr, upper)
    o = m.finish(N + name + "Hi", HI)
    nu, nv = 64, 96
    count = (nu + 1) * (nv + 1) * 2
    uu = np.zeros(count)
    vv = np.zeros(count)
    idx = 0
    for i in range(nu + 1):
        for j in range(nv + 1):
            for _ in range(2):
                uu[idx], vv[idx] = i / nu, j / nv
                idx += 1
    e, far, _ = fr.lids[upper]
    h0, h1 = fr.shell
    deg = abs(far - e) * uu ** 1.8     # degrees back from the edge
    outer = np.cos(h0 + (h1 - h0) * vv) * (1 if fr.hinge.dot(fr.outer) > 0 else -1)   # +1 at the outer corner
    col = np.broadcast_to(skin, (count, 3)).copy()
    if upper:
        w = 2.4 + 3.4 * np.maximum(outer, 0) ** 2
        col = mix(col, line, 1 - smooth(w, w + 1.5, deg))
    else:
        col = mix(col, line, (1 - smooth(1.1, 2.4, deg)) * lower_share)
    paint(o, col, np.full(count, 0.5))
    return o


def low_eye(fr, name, u_segments=22, v_segments=14):
    m = Mesh()
    q = fr.axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_uvsphere(m.bm, u_segments=u_segments, v_segments=v_segments, radius=fr.radius, matrix=Matrix.Translation(fr.centre) @ q)
    # only what can ever show: the back of the ball goes
    A = fr.axis
    dead = [f for f in m.bm.faces if all((v.co - fr.centre).normalized().dot(A) < -0.1 for v in f.verts)]
    bmesh.ops.delete(m.bm, geom=dead, context="FACES")
    return m.finish(name, GAME)


def low_lid(fr, upper, name):
    """One outward layer: nobody sees the inside of a lid."""
    e, far, gap = fr.lids[upper]
    h0, h1 = fr.shell
    nu, nv = (7, 14) if upper else (5, 10)
    m = Mesh()
    rows = [[m.bm.verts.new(fr.centre + fr.lid(math.radians(e + (far - e) * (i / nu) ** 1.3), h0 + (h1 - h0) * j / nv) * (fr.radius + gap)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            m.bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    me = bpy.data.meshes.new(name)
    m.bm.to_mesh(me)
    m.bm.free()
    p = me.polygons[0]
    if p.normal.dot(p.center - fr.centre) < 0:
        me.flip_normals()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    GAME.objects.link(o)
    return o


def glints(frames, coll, name, spots=((-22, 24, 0.024, 20), (17, -18, 0.0115, 12))):
    """Catch-lights per eye, on the eye's bone (a glow piece: Neon). Discs lying on the ball, seen from outside only. spots: az, el, radius, sides."""
    m = Mesh()
    bm = m.bm
    for tag, fr in frames.items():
        for az, el, r, sides in spots:
            d = fr.direction(math.radians(az), math.radians(el))
            a = d.orthogonal().normalized()
            b = d.cross(a).normalized()
            lift = fr.radius + 0.0012

            def on_ball(x, y):
                return fr.centre + (d + a * (x / lift) + b * (y / lift)).normalized() * lift
            centre = bm.verts.new(on_ball(0, 0))
            ring = [bm.verts.new(on_ball(math.cos(TAU * k / sides) * r, math.sin(TAU * k / sides) * r * 1.12)) for k in range(sides)]
            for k in range(sides):
                bm.faces.new((centre, ring[k], ring[(k + 1) % sides]))
    bm.normal_update()
    return m.finish(N + name, coll, smooth_shade=False, recalc=False)


# ---------- materials and the review stage ----------
def hi_material(ao_distance=0.10, ao_share=0.55):
    m = bpy.data.materials.new(PET + "_Hi")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    attr = t.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "paint"
    rough = t.nodes.new("ShaderNodeAttribute")
    rough.attribute_name = "rough"
    metal = t.nodes.new("ShaderNodeAttribute")
    metal.attribute_name = "metal"
    ao = t.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = ao_distance
    ao.only_local = True
    ao.samples = 16
    mul = t.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = ao_share
    t.links.new(attr.outputs["Color"], mul.inputs[6])
    t.links.new(ao.outputs["Color"], mul.inputs[7])
    t.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    t.links.new(rough.outputs["Fac"], bsdf.inputs["Roughness"])
    # the metal mask leaves through emission, only while it is baked: a metallic base colour would bake black
    t.links.new(metal.outputs["Fac"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.0
    return m


def glow_material():
    m = bpy.data.materials.new(PET + "_Glow")
    g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Emission Color"].default_value = (0.8, 1, 0.95, 1)
    g.inputs["Emission Strength"].default_value = 1.6
    return m


def stage_setup(world_colour=(0.42, 0.46, 0.5, 1)):
    for name, energy, rot in (("Key", 2.1, (55, 0, -35)), ("Fill", 0.8, (70, 0, 140)), ("Rim", 1.0, (120, 0, 20))):
        sun = bpy.data.lights.new(name, "SUN")
        sun.energy = energy
        so = bpy.data.objects.new(name, sun)
        scene.collection.objects.link(so)
        so.rotation_euler = tuple(math.radians(v) for v in rot)
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.node_tree.nodes["Background"].inputs[0].default_value = world_colour
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    cam = bpy.data.cameras.new("ShowCam")
    cam.lens = 70
    co = bpy.data.objects.new("ShowCam", cam)
    scene.collection.objects.link(co)
    scene.camera = co
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):      # the first GPU backend this machine has (else the CPU)
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            break
    else:
        prefs.compute_device_type = "NONE"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = "GPU"
    scene.cycles.samples = 28
    scene.view_settings.view_transform = "Standard"


def shots(prefix, views, target=(0, 0.12, 0.66), dist=5.0, size=540):
    """Each view: x, y, z (toward the camera), and optionally a distance and a target."""
    T = Vector(target)
    cam = bpy.data.objects["ShowCam"]
    scene.render.resolution_x = scene.render.resolution_y = size
    for k, view in enumerate(views):
        d = view[3] if len(view) > 3 else dist
        t = Vector(view[4]) if len(view) > 4 else T
        cam.location = t + V(view[0], view[1], view[2]).normalized() * d
        cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = prefix + "_%d.png" % k
        bpy.ops.render.render(write_still=True)


# ---------- the game mesh, its atlas and its maps ----------
def decimated(hi, name, target):
    me = hi.data.copy()
    o = bpy.data.objects.new(name, me)
    GAME.objects.link(o)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    apply_mods(o, [("DECIMATE", {"decimate_type": "COLLAPSE", "ratio": min(1.0, target / max(1, tris))})])
    for a in ("paint", "rough", "metal"):
        if o.data.attributes.get(a):
            o.data.attributes.remove(o.data.attributes[a])
    return o


def retopo_skin(hi, name, quads):
    """Even quads over the whole skin: no slivers for the bake to miss, and better bends."""
    me = hi.data.copy()
    o = bpy.data.objects.new(name, me)
    GAME.objects.link(o)
    for a in ("paint", "rough", "metal"):
        if o.data.attributes.get(a):
            o.data.attributes.remove(o.data.attributes[a])
    # QuadriFlow refuses a surface with a single edge under a tenth of a millimetre, which a voxel remesh can leave behind: fresh remesh, a light
    # smooth, weld what is left, and try again at a slightly different size if it still objects
    base = o.data.copy()
    res = {"CANCELLED"}
    for size in (0.0065, 0.0062, 0.0069, 0.0073, 0.0058):
        o.data = base.copy()
        apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": size, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 3})])
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0006)
        bm.to_mesh(o.data)
        bm.free()
        select_only([o])
        res = bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False, use_preserve_sharp=False, use_preserve_boundary=False, preserve_attributes=False, smooth_normals=False, mode="FACES", target_faces=quads, seed=3)
        print("QUADRIFLOW", size, res, len(o.data.polygons), "faces", flush=True)
        if "FINISHED" in res:
            break
    assert "FINISHED" in res and len(o.data.polygons) < quads * 1.5, "the skin was not retopologised"
    apply_mods(o, [("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def surface_gap(low, tree):
    """The furthest any vertex of the game mesh strays from the surface it stands for: a re-mesh that has gone wrong shows here, where the mesh checks see nothing."""
    worst = 0.0
    for v in low.data.vertices:
        hit = tree.find_nearest(v.co)
        if hit[0] is not None:
            worst = max(worst, hit[3])
    return worst


def low_sheet(point, thick, nu, nv, name):
    m = Mesh()
    m.sheet(point, thick, nu, nv)
    return m.finish(name, GAME)


def triangulate(lows):
    for o in lows.values():
        apply_mods(o, [("TRIANGULATE", {"quad_method": "BEAUTY", "ngon_method": "BEAUTY"})])


def uv_density(objs):
    """UV units per metre over these objects, as unwrapped so far."""
    area_3d, area_uv = 0.0, 0.0
    for o in objs:
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            area_3d += p.area
            loops = list(p.loop_indices)
            a = uv[loops[0]].uv
            for i in range(1, len(loops) - 1):
                b, c = uv[loops[i]].uv, uv[loops[i + 1]].uv
                area_uv += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
    return math.sqrt(area_uv / max(area_3d, 1e-9))


def scale_uv_to(o, polys, density):
    """Rescales these polygons' UVs to this many UV units per metre (the final pack fits the whole atlas to the map)."""
    uv = o.data.uv_layers.active.data
    area_3d, area_uv = 0.0, 0.0
    for p in polys:
        area_3d += p.area
        loops = list(p.loop_indices)
        a = uv[loops[0]].uv
        for i in range(1, len(loops) - 1):
            b, c = uv[loops[i]].uv, uv[loops[i + 1]].uv
            area_uv += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
    k = density / max(math.sqrt(area_uv / max(area_3d, 1e-9)), 1e-9)
    for p in polys:
        for l in p.loop_indices:
            uv[l].uv = uv[l].uv * k


def unwrap(lows, regions, scales, margin=0.008, angle=62, shape="CONCAVE", own_uv=None, texels=None):
    """One atlas. regions: (test(polygon), share) over the skin (lows["Skin"]), each projected apart, the last taking every other piece too. scales: {key: share}:
    what a player looks at gets more of the atlas. own_uv: {key: writer(object, density)}: a piece that lays out its own UVs, in true scale at that density, in place of the projection.
    texels: {key: relative density}: sets every piece and region to a true density instead (a region's share is then its density), since each projection run has a scale of its own."""
    objs = list(lows.values())
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    select_only(objs)
    skin = lows["Skin"]

    def project(select):
        for o in objs:
            for p in o.data.polygons:
                p.select = select(o, p)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")

    claimed, run = {}, {}      # [polygon] = its region's share, and the region (projection run) it came from
    for k, (test, share) in enumerate(regions):
        last = k == len(regions) - 1
        mine = [p.index for p in skin.data.polygons if p.index not in claimed and (last or test(p))]
        chosen = set(mine)
        project(lambda o, p: (p.index in chosen) if o is skin else last)
        for i in mine:
            claimed[i], run[i] = share, k
    if texels is not None:
        by_run = {}      # each projection run is scaled on its own, even when two share a density
        for i, k in run.items():
            by_run.setdefault(k, []).append(skin.data.polygons[i])
        for k, polys in by_run.items():
            scale_uv_to(skin, polys, regions[k][1])
        for key, o in lows.items():
            if key == "Skin":
                continue
            if own_uv and key in own_uv:
                own_uv[key](o, texels.get(key, 1.0))
            else:
                scale_uv_to(o, list(o.data.polygons), texels.get(key, 1.0))
    else:
        if own_uv:
            density = uv_density([o for key, o in lows.items() if key not in own_uv and key != "Skin"])
            for key, writer in own_uv.items():
                writer(lows[key], density)
        uv = skin.data.uv_layers.active.data
        for i, share in claimed.items():
            for l in skin.data.polygons[i].loop_indices:
                uv[l].uv = uv[l].uv * share
        for key, k in scales.items():
            d = lows[key].data.uv_layers.active.data
            for l in d:
                l.uv = l.uv * k
    select_only(objs)      # (a piece's own UV writer may have changed the selection)
    for o in objs:
        o.data.polygons.foreach_set("select", [True] * len(o.data.polygons))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin_method="FRACTION", margin=margin, rotate=True, scale=True, shape_method=shape)
    bpy.ops.object.mode_set(mode="OBJECT")


def uv_overlap_texels(me, size=1024):
    """How many texels of the map two different faces both claim. Above a few, one part's paint lands on another: tight packing can do this."""
    uv = me.uv_layers.active.data
    owner = np.full((size, size), -1, dtype=np.int32)
    clashes = 0
    for p in me.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        here = owner[ys[inside], xs[inside]]
        clashes += int((here >= 0).sum())
        owner[ys[inside], xs[inside]] = p.index
    return clashes


def bleed_gutters(images):
    """Fills the empty space between a map's pieces with each piece's own edge colour, right across the image. Otherwise the fill colour bleeds in as thin cracks along the seams once the
    engine shrinks the map. images[0] is the colour map: what it left at the fill colour (its commonest value, the pieces being a minority) is empty on every map."""
    def read(img):
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        return px.reshape(h, w, 4)
    base = read(images[0])
    packed = (np.round(base[..., :3] * 255).astype(np.int64) * (1, 256, 65536)).sum(2)
    values, counts = np.unique(packed, return_counts=True)
    empty = packed == values[np.argmax(counts)]
    for img in images:
        px = read(img)
        h, w = px.shape[:2]
        ys = (np.arange(h) * empty.shape[0] / h).astype(int)
        xs = (np.arange(w) * empty.shape[1] / w).astype(int)
        hole = empty[np.ix_(ys, xs)].copy()
        px[hole] = 0
        for _ in range(4096):
            if not hole.any():
                break
            known = (~hole).astype(np.float32)
            weight = np.zeros_like(known)
            total = np.zeros_like(px)
            for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
                k = np.roll(known, shift, axis)
                weight += k
                total += np.roll(px, shift, axis) * k[..., None]
            grow = hole & (weight > 0)
            px[grow] = total[grow] / weight[grow][..., None]
            hole[grow] = False
        px[..., 3] = 1.0
        img.pixels.foreach_set(px.ravel())
        img.update()


def bake_all(lows, pieces, hi_mat=None, size=1024, colour_size=None, far=("Skin",), fill=(0.6, 0.6, 0.6, 1), metal=False, reach=(0.012, 0.03), far_reach=(0.014, 0.045), reaches=None):
    """Every low piece from its own high piece, so neighbours can't project on each other. reaches: {key: (cage, ray)} for a piece that needs its own. Returns the material."""
    os.makedirs(OUT, exist_ok=True)

    def image(name, fill_with, colour, res):
        img = bpy.data.images.new(name, res, res, alpha=False)
        img.generated_color = fill_with
        if not colour:
            img.colorspace_settings.name = "Non-Color"
        return img
    colour_size = colour_size or size
    color = image(PET + "_Color", fill, True, colour_size)
    normal = image(PET + "_Normal", (0.5, 0.5, 1, 1), False, size)
    rough = image(PET + "_Roughness", (0.55, 0.55, 0.55, 1), False, size)
    m = bpy.data.materials.new(PET + "_Baked")
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    ci = t.nodes.new("ShaderNodeTexImage"); ci.image = color; ci.name = "ColorMap"
    ni = t.nodes.new("ShaderNodeTexImage"); ni.image = normal; ni.name = "NormalMap"
    ri = t.nodes.new("ShaderNodeTexImage"); ri.image = rough; ri.name = "RoughMap"
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(ci.outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(ni.outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    t.links.new(ri.outputs["Color"], bsdf.inputs["Roughness"])
    maps = [("DIFFUSE", "ColorMap", {"pass_filter": {"COLOR"}}, colour_size), ("NORMAL", "NormalMap", {"normal_space": "TANGENT"}, size), ("ROUGHNESS", "RoughMap", {}, size)]
    saves = [(color, "color"), (normal, "normal"), (rough, "roughness")]
    if metal:
        metal_img = image(PET + "_Metalness", (0, 0, 0, 1), False, size)
        mi = t.nodes.new("ShaderNodeTexImage"); mi.image = metal_img; mi.name = "MetalMap"
        t.links.new(mi.outputs["Color"], bsdf.inputs["Metallic"])
        maps.append(("EMIT", "MetalMap", {}, size))
        saves.append((metal_img, "metalness"))
    for o in lows.values():
        o.data.materials.clear()
        o.data.materials.append(m)
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    scene.cycles.samples = 16
    hi_bsdf = next(n for n in hi_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED") if hi_mat else None
    for kind, node, kw, res in maps:
        t.nodes.active = t.nodes[node]
        if hi_bsdf:
            hi_bsdf.inputs["Emission Strength"].default_value = 1.0 if kind == "EMIT" else 0.0
        for key, low in lows.items():
            select_only([pieces[key], low], low)
            cage, ray = (reaches or {}).get(key) or (far_reach if key in far else reach)
            bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=cage, max_ray_distance=ray, margin=max(4, res // 256), use_clear=False, target="IMAGE_TEXTURES", **kw)
    if hi_bsdf:
        hi_bsdf.inputs["Emission Strength"].default_value = 0.0
    bleed_gutters([img for img, _ in saves])
    for img, suffix in saves:
        img.filepath_raw = os.path.join(OUT, PET + "_" + suffix + ".png")
        img.file_format = "PNG"
        img.save()
        img.pack()
    return m


# ---------- the skeleton ----------
def weigh(obj, weights):
    """weights: list per vertex of {bone: w}: normalized, at most four, each above a hundredth."""
    groups = {g.name: g for g in obj.vertex_groups}
    for i, w in enumerate(weights):
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        top = [kv for kv in top if kv[1] >= 0.01] or top[:1]
        total = sum(v for _, v in top) or 1.0
        for bone, v in top:
            v /= total
            g = groups.get(bone)
            if not g:
                g = groups[bone] = obj.vertex_groups.new(name=bone)
            g.add([i], v, "REPLACE")


def rigid(obj, bone):
    obj.vertex_groups.clear()
    obj.vertex_groups.new(name=bone).add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def chain_weight(names, knots, f):
    """Shares of a chain of bones at a point f along it; knots: where each bone takes over."""
    if f <= knots[0]:
        return {names[0]: 1.0}
    if f >= knots[-1]:
        return {names[-1]: 1.0}
    for k in range(len(knots) - 1):
        if f <= knots[k + 1]:
            s = float(smooth(knots[k], knots[k + 1], f))
            return {names[k]: 1 - s, names[k + 1]: s}


def stress_report(rig, body, poses):
    """Every pose against the rest pose, edge by edge: how far any edge of the deformed mesh stretches or crushes. A tear or a collapse shows as a number before it shows in a render."""
    pose(rig, {})
    dg = bpy.context.evaluated_depsgraph_get()
    rest = body.evaluated_get(dg).to_mesh()
    edges = np.empty(len(rest.edges) * 2, dtype=np.int64)
    rest.edges.foreach_get("vertices", edges)
    edges = edges.reshape(-1, 2)
    co0 = np.empty(len(rest.vertices) * 3)
    rest.vertices.foreach_get("co", co0)
    co0 = co0.reshape(-1, 3)
    len0 = np.linalg.norm(co0[edges[:, 0]] - co0[edges[:, 1]], axis=1) + 1e-9
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, spec in poses.items():
        pose(rig, spec)
        dg = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg).to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        now = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
        ratio = now / len0
        gain = now - len0
        # a tiny edge can double and mean nothing: what a tear looks like is an edge that gained real length
        worst = int(np.argmax(gain))
        out[name] = {"most gained m": round(float(gain[worst]), 3), "at": tuple(round(float(v), 2) for v in co0[edges[worst, 0]]), "x": round(float(ratio[worst]), 1), "over 6cm gained": int((gain > 0.06).sum()), "crush under 0.25": int((ratio < 0.25).sum()), "edges": len(edges)}
        body.evaluated_get(dg).to_mesh_clear()
    pose(rig, {})
    return out


def armature(bones):
    """bones: (name, head, parent), a parent before its children."""
    arm = bpy.data.armatures.new(PET + "_Rig")
    rig = bpy.data.objects.new(PET + "_Rig", arm)
    GAME.objects.link(rig)
    select_only([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, parent in bones:
        b = arm.edit_bones.new(name)
        b.head = head
        b.tail = head + V(0, 0, 0.05)
        b.roll = 0
        b.use_deform = True
    for name, head, parent in bones:
        if parent:
            arm.edit_bones[name].parent = arm.edit_bones[parent]
            arm.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def join_into(lows, name):
    """One mesh, one material, one draw: every piece told apart by its bones."""
    objs = list(lows.values())
    body = lows["Skin"]
    select_only(objs, body)
    bpy.ops.object.join()
    body.name = N + name
    body.data.name = N + name
    return body


def bind(rig, objects):
    for o in objects:
        o.parent = rig
        md = o.modifiers.new("Rig", "ARMATURE")
        md.object = rig


def pose(rig, spec):
    """spec: bone: (axis (x, y, z), degrees, move (x, y, z)), all in the model's axes."""
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    for name, (axis, deg, move) in spec.items():
        pb = rig.pose.bones[name]
        B = pb.bone.matrix_local.to_3x3()
        pb.rotation_quaternion = (B.inverted() @ Matrix.Rotation(math.radians(deg), 3, Vector(axis)) @ B).to_quaternion()
        pb.location = B.inverted() @ Vector(move)
    bpy.context.view_layer.update()


def export_fbx(rig, body, glows, extras=()):
    """The FBX, as File > Import 3D wants it. glows: the Neon pieces: their UVs never show, but a mesh should have them. extras: other meshes that keep the baked material, such as see-through glass."""
    os.makedirs(OUT, exist_ok=True)
    pose(rig, {})
    plain_mat = bpy.data.materials.new(PET + "_GlowPiece")
    for o in glows:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
        o.data.materials.clear()
        o.data.materials.append(plain_mat)
    select_only([body] + list(extras) + list(glows) + [rig], rig)
    path = os.path.join(OUT, PET + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                             primary_bone_axis="Y", secondary_bone_axis="X")
    return path


def save_blend():
    """The .blend, beside its preview, with no path from this machine in it. Returns its path."""
    os.makedirs(TOOLS, exist_ok=True)
    path = os.path.join(TOOLS, PET + ".blend")
    bpy.context.preferences.filepaths.save_version = 0
    # the render output field keeps the last shot's path, and its old bytes after a shorter one: fill it to the end, then clear it
    render = bpy.context.scene.render
    render.filepath = "//" + "_" * 1020
    render.filepath = "//"
    # the baked maps are packed, but remember where they were written: keep that relative to the .blend
    for img in bpy.data.images:
        if img.filepath_raw and not img.filepath_raw.startswith("//"):
            img.filepath_raw = bpy.path.relpath(img.filepath_raw, start=TOOLS)
        for packed in img.packed_files:
            packed.filepath = img.filepath_raw
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    return path


def preview_dir():
    """Review renders go to renders/pets/<Egg>/ (git-ignored, local only), never beside the sources."""
    path = os.path.join(ROOT, "renders", "pets", os.path.basename(TOOLS))
    os.makedirs(path, exist_ok=True)
    return path


def save_all(preview_view):
    """The preview render (renders/pets/<Egg>/<Pet>_preview.png), and the .blend. Returns the .blend's path."""
    os.makedirs(TOOLS, exist_ok=True)
    out = preview_dir()
    shots(os.path.join(out, PET + "_preview"), [preview_view])
    os.replace(os.path.join(out, PET + "_preview_0.png"), os.path.join(out, PET + "_preview.png"))
    return save_blend()

"""The egg forge (run inside Blender): the egg pipeline. Everything is written to assets/eggs/,
the eggs the game uses (WorldBuilder places them from ServerStorage.EggMeshes).

What it does better than egg_bake.py, each fixing something seen on the first eggs in Studio:

- The shell has its own clean UV (one island, the seam at the back), so it gets most of the map
  and stays sharp. The first eggs were smart-projected into thousands of fragments and came out
  blurred.
- The shell is painted as arrays in texture space (Field): masks, heights and colours worked out
  exactly, with motifs drawn as distance fields on a plane laid against the egg, instead of noise
  that happens to land somewhere.
- The colour is baked from the materials' Base Color, not the Diffuse pass. The Diffuse pass
  multiplies by (1 - metallic), which is why gold came out dark and muddy.
- Shell and attachments are baked separately, so one can't print onto the other, then a real
  ambient occlusion pass over the whole model grounds each piece where it sits on another.

One egg at a time, and clear() after each. Convention as egg_kit: Roblox space (x right, y up, the
egg's front toward +z, its bottom at the origin), s runs round the egg with the front at 0.5 and
the seam at the back, v from the bottom (0) to the top (1).
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = Vector
H, R = K.H, K.R
OUT = os.path.join(K.REPO, "assets", "eggs")
TAU = 2 * math.pi


# ---------- housekeeping ----------
def clear():
    """Removes the asset from Blender: every object but the startup Camera and Light, every mesh,
    material, image and collection, the review scene and the orphans."""
    main = bpy.data.scenes.get("Scene") or bpy.data.scenes.new("Scene")
    if bpy.context.window.scene != main:
        bpy.context.window.scene = main
    for s in list(bpy.data.scenes):
        if s != main:
            bpy.data.scenes.remove(s)
    for o in list(bpy.data.objects):
        if o.name not in ("Camera", "Light"):
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.node_groups):
        for x in list(block):
            block.remove(x)
    for img in list(bpy.data.images):
        if img.type == "IMAGE":
            bpy.data.images.remove(img)
    for w in list(bpy.data.worlds):
        bpy.data.worlds.remove(w)
    bpy.data.orphans_purge(do_recursive=True)
    return {"objects": [o.name for o in bpy.data.objects], "meshes": len(bpy.data.meshes), "materials": len(bpy.data.materials),
            "images": [i.name for i in bpy.data.images]}


# ---------- the egg's surface, as arrays ----------
def shell_pos(s, v, r=R, h=H, swell=0.13):
    a = TAU * (s - 0.5)
    t = np.pi * v
    y = h * (1 - np.cos(t)) / 2
    rad = r * np.sin(t) * (1 + swell * np.cos(t))
    return np.stack([np.sin(a) * rad, y, np.cos(a) * rad], -1)


def shell_normal(s, v, r=R, h=H, swell=0.13):
    a = TAU * (s - 0.5)
    t = np.pi * v
    dy = h * np.sin(t) / 2 * np.pi
    dr = r * np.pi * (np.cos(t) * (1 + swell * np.cos(t)) - swell * np.sin(t) ** 2)
    L = np.maximum(np.hypot(dy, dr), 1e-9)
    nr, ny = dy / L, -dr / L
    return np.stack([np.sin(a) * nr, ny, np.cos(a) * nr], -1)


def on(s, v, off=0.0):
    """A point on (or `off` above) the shell, as a Vector."""
    p = shell_pos(np.float64(s), np.float64(v)) + shell_normal(np.float64(s), np.float64(v)) * off
    return V((float(p[0]), float(p[1]), float(p[2])))


def normal(s, v):
    n = shell_normal(np.float64(s), np.float64(v))
    return V((float(n[0]), float(n[1]), float(n[2])))


# ---------- noise ----------
def _hash(ix, iy, iz, seed, k):
    x = (ix.astype(np.int64) * 73856093 ^ iy.astype(np.int64) * 19349663 ^ iz.astype(np.int64) * 83492791 ^ (seed * 2654435761 + k * 40503)) & 0xFFFFFFFF
    x = (x ^ (x >> 13)) * 1274126177 & 0xFFFFFFFF
    x = (x ^ (x >> 16)) * 2246822519 & 0xFFFFFFFF
    return ((x ^ (x >> 13)) & 0xFFFFFF) / 0xFFFFFF


def noise(P, scale=1.0, seed=0):
    """Gradient noise, about -1..1."""
    p = P * scale
    i = np.floor(p)
    f = p - i
    u = f * f * f * (f * (f * 6 - 15) + 10)
    out = 0.0
    corners = []
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                ix, iy, iz = i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz
                g = np.stack([_hash(ix, iy, iz, seed, c) * 2 - 1 for c in range(3)], -1)
                d = f - np.array((dx, dy, dz), dtype=np.float64)
                corners.append((g * d).sum(-1))
    c = corners
    ux, uy, uz = u[..., 0], u[..., 1], u[..., 2]
    x00 = c[0] + (c[4] - c[0]) * ux
    x01 = c[1] + (c[5] - c[1]) * ux
    x10 = c[2] + (c[6] - c[2]) * ux
    x11 = c[3] + (c[7] - c[3]) * ux
    y0 = x00 + (x10 - x00) * uy
    y1 = x01 + (x11 - x01) * uy
    out = y0 + (y1 - y0) * uz
    return out * 1.6


def fbm(P, scale=1.0, octaves=4, gain=0.5, seed=0):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * noise(P, scale * 2 ** o, seed + o)
        norm += amp
        amp *= gain
    return total / norm


def ridged(P, scale=1.0, octaves=4, gain=0.5, seed=0):
    """0 at the ridge lines of noise, growing away: thin branching lines where it is small."""
    return np.abs(fbm(P, scale, octaves, gain, seed))


def voronoi(P, scale=1.0, seed=0, jitter=0.9, stretch=(1.0, 1.0, 1.0)):
    """Returns (F1, F2 - F1 (0 on the cell walls), a random 0..1 per cell). Cells are `1 / scale`
    across."""
    p = P * scale * np.array(stretch)
    i = np.floor(p)
    f1 = np.full(p.shape[:-1], 1e9)
    f2 = np.full(p.shape[:-1], 1e9)
    cid = np.zeros(p.shape[:-1])
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                ix, iy, iz = i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz
                c = np.stack([ix + 0.5 + (_hash(ix, iy, iz, seed, 0) - 0.5) * jitter,
                              iy + 0.5 + (_hash(ix, iy, iz, seed, 1) - 0.5) * jitter,
                              iz + 0.5 + (_hash(ix, iy, iz, seed, 2) - 0.5) * jitter], -1)
                d = np.sqrt(((c - p) ** 2).sum(-1))
                closer = d < f1
                f2 = np.where(closer, f1, np.minimum(f2, d))
                cid = np.where(closer, _hash(ix, iy, iz, seed, 3), cid)
                f1 = np.where(closer, d, f1)
    return f1, f2 - f1, cid


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)
    # colours have a last axis of 3 that the mask doesn't
    if t.ndim > 0 and ((a.ndim == 1 and a.shape[0] == 3) or (b.ndim == 1 and b.shape[0] == 3) or a.ndim > t.ndim or b.ndim > t.ndim):
        t = t[..., None]
    return a + (b - a) * t


def rgb(hexstr):
    return np.array([int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def ramp(x, stops):
    """Colour stops [(pos, "hex")], an array of positions in, an array of colours out."""
    pos = [p for p, _ in stops]
    cols = np.array([rgb(c) for _, c in stops])
    return np.stack([np.interp(x, pos, cols[:, k]) for k in range(3)], -1)


def blur(a, radius):
    """Three box blurs (close to a Gaussian); wraps round the egg, clamps at the poles. In texels."""
    r = max(1, int(radius))
    out = a
    for _ in range(3):
        c = np.cumsum(np.concatenate([out[:, -r - 1:], out, out[:, :r]], 1), 1)
        out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
        pad = np.concatenate([np.repeat(out[:1], r + 1, 0), out, np.repeat(out[-1:], r, 0)], 0)
        c = np.cumsum(pad, 0)
        out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    return out


# ---------- painting the shell ----------
class Field:
    """Arrays over the shell in texture space (row 0 is the bottom of the egg, column 0 the seam
    at the back)."""

    def __init__(self, w=1536, h=960):
        self.w, self.h = w, h
        s = (np.arange(w) + 0.5) / w
        v = (np.arange(h) + 0.5) / h
        self.S, self.V = np.meshgrid(s, v)
        self.P = shell_pos(self.S, self.V)
        self.N = shell_normal(self.S, self.V)
        self.Y = self.P[..., 1]

    def plane(self, s0, v0, up=(0, 1, 0), roll=0.0):
        """Coordinates on a plane laid against the egg at (s0, v0): x to the viewer's right, y up,
        in egg units, undistorted as seen from straight on. Returns (x, y, front), front > 0 only
        on the side of the egg facing the plane."""
        c = on(s0, v0)
        n = normal(s0, v0)
        e1 = V(up).cross(n).normalized()
        e2 = n.cross(e1).normalized()
        if roll:
            ca, sa = math.cos(roll), math.sin(roll)
            e1, e2 = e1 * ca + e2 * sa, e2 * ca - e1 * sa
        d = self.P - np.array(c)
        return (d * np.array(e1)).sum(-1), (d * np.array(e2)).sum(-1), (self.N * np.array(n)).sum(-1)


def seg_dist(x, y, pts, closed=False):
    """Distance to a polyline [(x, y), ...], and how far along it the nearest point is (0..1)."""
    pts = np.asarray(pts, dtype=np.float64)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    best = np.full(x.shape, 1e9)
    along = np.zeros(x.shape)
    lengths = np.hypot(*(pts[1:] - pts[:-1]).T)
    total = lengths.sum() or 1.0
    acc = 0.0
    for a, b, L in zip(pts[:-1], pts[1:], lengths):
        ab = b - a
        t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(L * L, 1e-12), 0, 1)
        d = np.hypot(x - a[0] - ab[0] * t, y - a[1] - ab[1] * t)
        closer = d < best
        best = np.where(closer, d, best)
        along = np.where(closer, (acc + t * L) / total, along)
        acc += L
    return best, along


def image(name, arr, color=True):
    """A float image from an array: an (h, w, 3) colour authored in sRGB, or an (h, w) value."""
    h, w = arr.shape[:2]
    img = bpy.data.images.new(name, w, h, float_buffer=True, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    if arr.ndim == 2:
        arr = np.repeat(arr[..., None], 3, -1)
    elif color:
        arr = np.where(arr <= 0.04045, arr / 12.92, ((np.clip(arr, 0, None) + 0.055) / 1.055) ** 2.4)
    rgba = np.concatenate([arr, np.ones((h, w, 1))], -1).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.update()
    img.pack()
    return img


def shell_material(name, color, rough, metal):
    """The shell's material, reading painted arrays. The colour image holds linear values because
    image() converted it."""
    g = Hm._Graph(name)
    uv = g.coords("UV")

    def tex(arr, suffix, is_color):
        n = g.n("ShaderNodeTexImage", image=image(name + suffix, arr, is_color))
        n.interpolation = "Cubic"
        g.link(uv, n.inputs["Vector"])
        return n.outputs["Color"]
    return g.finish(tex(color, "_C", True), g.bw(tex(rough, "_R", False)), g.bw(tex(metal, "_M", False)))


# ---------- geometry ----------
def _mesh(name, coll, verts, faces, loop_uv=None, material=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    if loop_uv is not None:
        layer = me.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", np.asarray(loop_uv, dtype=np.float32).ravel())
    if material:
        me.materials.append(material)
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    me.update()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def to_blender(P):
    return np.stack([P[..., 0], -P[..., 2], P[..., 1]], -1)


def sample(arr, s, v):
    """Bilinear lookup in a Field array at arrays of (s, v)."""
    h, w = arr.shape
    x = (s * w - 0.5) % w
    y = np.clip(v * h - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x1 = (x0 + 1) % w
    return (arr[y0, x0] * (1 - fx) + arr[y0, x1] * fx) * (1 - fy) + (arr[y0 + 1, x0] * (1 - fx) + arr[y0 + 1, x1] * fx) * fy


def shell_mesh(name, coll, nu, nv, height=None, material=None, uv_rect=(0, 0, 1, 1), offset=0.0):
    """The egg's skin as a grid from pole to pole, displaced by a Field array along the normal,
    its UVs laid straight into uv_rect (x0, y0, x1, y1)."""
    s = np.linspace(0, 1, nu + 1)
    v = np.linspace(0.003, 0.997, nv + 1)
    S, Vv = np.meshgrid(s, v)
    P = shell_pos(S, Vv) + shell_normal(S, Vv) * offset
    if height is not None:
        P = P + shell_normal(S, Vv) * sample(height, S, Vv)[..., None]
    verts = to_blender(P).reshape(-1, 3)
    bottom = len(verts)
    verts = np.vstack([verts, to_blender(np.array([[0.0, 0.0, 0.0], [0.0, H, 0.0]]))])
    idx = np.arange((nu + 1) * (nv + 1)).reshape(nv + 1, nu + 1)
    quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    faces = quads.tolist()
    x0, y0, x1, y1 = uv_rect
    uvs = np.stack([x0 + S * (x1 - x0), y0 + Vv * (y1 - y0)], -1).reshape(-1, 2)
    loop_uv = [uvs[quads.ravel()]]
    fan = []
    fuv = []
    for i in range(nu):
        # each fan's point sits at the rect's own edge, so its UV triangle has area
        mid_x = (uvs[idx[0, i]][0] + uvs[idx[0, i + 1]][0]) / 2
        fan.append([bottom, int(idx[0, i + 1]), int(idx[0, i])])
        fuv += [np.array((mid_x, y0)), uvs[idx[0, i + 1]], uvs[idx[0, i]]]
        fan.append([bottom + 1, int(idx[nv, i]), int(idx[nv, i + 1])])
        fuv += [np.array((mid_x, y1)), uvs[idx[nv, i]], uvs[idx[nv, i + 1]]]
    faces += fan
    loop_uv.append(np.array(fuv))
    return _mesh(name, coll, verts.tolist(), faces, np.vstack(loop_uv), material)


def prism(hi, pts, width, mat=0, height=None, closed=False):
    """A flat glowing inlay along a polyline of (point, normal) pairs: three-sided, sitting on the
    surface, tapered to points at open ends. `width` is a number or a function of 0..1."""
    wf = width if callable(width) else (lambda t: width)
    height = height or (lambda w: w * 0.45)
    n = len(pts)
    rings = []
    for i, (p, nrm) in enumerate(pts):
        a = pts[(i - 1) % n][0] if closed or i > 0 else p
        b = pts[(i + 1) % n][0] if closed or i < n - 1 else p
        side = (b - a).cross(nrm).normalized()
        w = wf(i / max(1, n - 1)) / 2
        rings.append([hi.v(p + side * w - nrm * w * 0.5), hi.v(p + nrm * height(w * 2)), hi.v(p - side * w - nrm * w * 0.5)])
    for i in range(n if closed else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        hi.f([r0[0], r1[0], r1[1], r0[1]], [(0, 0)] * 4, mat)
        hi.f([r0[1], r1[1], r1[2], r0[2]], [(0, 0)] * 4, mat)


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimated(obj, ratio, coll, name=None):
    me = obj.data.copy()
    me.transform(obj.matrix_world)
    c = bpy.data.objects.new(name or obj.name + "_low", me)
    coll.objects.link(c)
    if ratio < 0.999:
        md = c.modifiers.new("Decimate", "DECIMATE")
        md.decimate_type = "COLLAPSE"
        md.ratio = ratio
        md.use_collapse_triangulate = True
        new = bpy.data.meshes.new_from_object(c.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        old = c.data
        c.modifiers.clear()
        c.data = new
        bpy.data.meshes.remove(old)
    return c


def unwrap_into(obj, rect, angle=66, margin=0.004):
    """Unwraps a mesh into uv rect (x0, y0, x1, y1), keeping texels square: the islands are packed
    into a unit square stretched to the rect's shape, then squeezed back."""
    x0, y0, x1, y1 = rect
    me = obj.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    view_layer.objects.active = obj
    with B._ui_override(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
        bpy.ops.object.mode_set(mode="OBJECT")
    # the rect is `aspect` times as wide as tall: stretched by that much up v, the packer's unit
    # square squeezes back to square texels (so the islands may not be rotated)
    aspect = (x1 - x0) / (y1 - y0)
    layer = me.uv_layers[0]
    uv = np.zeros(len(me.loops) * 2)
    layer.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    uv[:, 1] *= aspect
    layer.data.foreach_set("uv", uv.ravel())
    with B._ui_override(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(margin=margin, rotate=(abs(aspect - 1) < 1e-3))
        bpy.ops.object.mode_set(mode="OBJECT")
    layer = me.uv_layers[0]
    uv = np.zeros(len(me.loops) * 2)
    layer.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    uv[:, 0] = x0 + uv[:, 0] * (x1 - x0)
    uv[:, 1] = y0 + uv[:, 1] * (y1 - y0)
    layer.data.foreach_set("uv", uv.ravel())
    me.update()


# ---------- baking ----------
def _route(materials, kind):
    """Every material shows one value as emission, to bake it: "color" (what goes into the
    Principled's Base Color) or a named value node. Returns a function that puts them back."""
    undo = []
    for m in materials:
        t = m.node_tree
        out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
        old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        em = t.nodes.new("ShaderNodeEmission")
        if kind == "color":
            bsdf = next((n for n in t.nodes if n.type == "BSDF_PRINCIPLED"), None)
            sock = bsdf.inputs["Base Color"] if bsdf else None
            if sock is not None and sock.links:
                t.links.new(sock.links[0].from_socket, em.inputs["Color"])
            elif sock is not None:
                em.inputs["Color"].default_value = sock.default_value
        else:
            src = t.nodes.get(kind)
            if src is not None:
                t.links.new(src.outputs[0], em.inputs["Color"])
            else:
                em.inputs["Color"].default_value = (0, 0, 0, 1)
        t.links.new(em.outputs[0], out.inputs["Surface"])
        undo.append((t, out, old, em))

    def restore():
        for t, out, old, em in undo:
            t.nodes.remove(em)
            if old is not None:
                t.links.new(old, out.inputs["Surface"])
    return restore


RAYS = ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow")


def _hide_from_rays(objs, hide=True):
    for o in objs:
        for r in RAYS:
            setattr(o, r, not hide)


def bake(egg_id, pairs, glow_objs=(), size=1024, small=512, samples=16, ao_samples=48, ao_reach=0.35, ao_floor=0.5, wear=None):
    """pairs: [(low object, [high objects], extrusion, ray distance)], each baked only from its own
    high objects. All high objects still shade each other in the AO pass. Maps saved to OUT."""
    os.makedirs(OUT, exist_ok=True)
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    images = {"color": B._image(egg_id + "_Color", size, True), "normal": B._image(egg_id + "_Normal", size, False),
              "roughness": B._image(egg_id + "_Roughness", small, False), "metalness": B._image(egg_id + "_Metalness", small, False),
              "ao": B._image(egg_id + "_AO", size, False)}
    mat = B._baked_material(egg_id, images)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("EggBakeWorld")
    scene.world.light_settings.distance = ao_reach
    saved_engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    lows = [p[0] for p in pairs]
    for low in lows:
        low.data.materials.clear()
        low.data.materials.append(mat)
    _hide_from_rays(lows)
    _hide_from_rays(glow_objs)
    all_mats = {m for _, hi, _, _ in pairs for o in hi for m in o.data.materials if m}
    passes = [("color", "EMIT", "color", samples), ("normal", "NORMAL", None, samples), ("roughness", "EMIT", "BAKE_ROUGH", 4),
              ("metalness", "EMIT", "BAKE_METAL", 4), ("ao", "AO", None, ao_samples)]
    log = {}
    try:
        import time
        for key, kind, route, n in passes:
            t0 = time.time()
            scene.cycles.samples = n
            mat.node_tree.nodes.active = mat.node_tree.nodes[key]
            restore = _route(all_mats, route) if route else None
            try:
                for i, (low, hi, ext, ray) in enumerate(pairs):
                    bpy.ops.object.select_all(action="DESELECT")
                    for o in hi:
                        o.select_set(True)
                    low.select_set(True)
                    view_layer.objects.active = low
                    kw = dict(type=kind, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray, margin=6,
                              use_clear=(i == 0), target="IMAGE_TEXTURES")
                    if kind == "NORMAL":
                        kw["normal_space"] = "TANGENT"
                    bpy.ops.object.bake(**kw)
            finally:
                if restore:
                    restore()
            log[key] = round(time.time() - t0, 1)
    finally:
        scene.render.engine = saved_engine
        _hide_from_rays(lows, False)
        _hide_from_rays(glow_objs, False)
    # the AO settles into the colour: contact shadows between pieces, kept coloured (not grey)
    n = size * size * 4
    col = np.zeros(n, dtype=np.float32)
    ao = np.zeros(n, dtype=np.float32)
    images["color"].pixels.foreach_get(col)
    images["ao"].pixels.foreach_get(ao)
    k = ao_floor + (1 - ao_floor) * np.clip(ao, 0, 1)
    col[0::4] *= k[0::4]
    col[1::4] *= k[0::4]
    col[2::4] *= k[0::4]
    images["color"].pixels.foreach_set(col)
    images["color"].update()
    node_ao = mat.node_tree.nodes["ao"]
    mat.node_tree.nodes.remove(node_ao)
    for key in ("color", "normal", "roughness", "metalness"):
        img = images[key]
        img.filepath_raw = os.path.join(OUT, egg_id + "_" + key + ".png")
        img.file_format = "PNG"
        img.save()
    bpy.data.images.remove(images["ao"])
    B.wire_baked(mat)
    return mat, log


def export(egg_id, lows, glows, coll, flat_body=False):
    """assets/eggs/<EggId>.fbx: the body and one Neon part per colour. Returns the parts and the
    triangle count."""
    body = K.join(lows, egg_id + "_Body", coll)
    mat = lows[0].data.materials[0]
    body.data.materials.clear()
    body.data.materials.append(mat)
    for p in body.data.polygons:
        p.material_index = 0
        p.use_smooth = not flat_body
    parts = [body]
    for hexstr, objs in glows.items():
        if objs:
            g = K.join(objs, egg_id + "_Glow_" + hexstr, coll)
            for p in g.data.polygons:
                p.use_smooth = False
            parts.append(g)
    W.export_batch(parts, os.path.join(OUT, egg_id + ".fbx"))
    return parts, sum(tris(p) for p in parts)


# ---------- review ----------
def lab(bg=0.22):
    scene = bpy.data.scenes.get("EggLab") or bpy.data.scenes.new("EggLab")
    if scene.camera is None:
        w = bpy.data.worlds.new("EggLabWorld")
        w.use_nodes = True
        b = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
        b.inputs[0].default_value = (bg, bg, bg * 1.03, 1)
        b.inputs[1].default_value = 1.0
        scene.world = w
        for name, loc, energy, color in (("Key", (4, -5, 6), 700, (1.0, 0.97, 0.92)), ("Rim", (-4, 6, 5), 500, (0.9, 0.95, 1.0))):
            light = bpy.data.lights.new("Lab" + name, "AREA")
            light.energy = energy
            light.color = color
            light.size = 4
            o = bpy.data.objects.new("Lab" + name, light)
            o.location = loc
            o.rotation_euler = (V((0, 0, 1.3)) - V(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.collection.objects.link(o)
        cam = bpy.data.cameras.new("LabCam")
        cam.lens = 70
        co = bpy.data.objects.new("LabCam", cam)
        scene.collection.objects.link(co)
        scene.camera = co
        scene.view_settings.view_transform = "Standard"
        scene.render.engine = "CYCLES"
        scene.cycles.device = "GPU"
        scene.cycles.use_denoising = True
        scene.render.image_settings.file_format = "PNG"
    return scene


def review(objects, path, views=("front", "three", "back", "top"), size=500, samples=48, centre=(0, 0, 1.4), distance=7.0, close=None):
    """Renders the views side by side into one PNG (Cycles, a neutral grey room)."""
    scene = lab()
    scene.cycles.samples = samples
    scene.render.resolution_x = scene.render.resolution_y = size
    window_scene = bpy.context.window.scene
    linked = []
    for o in objects:
        if o.name not in scene.collection.objects:
            scene.collection.objects.link(o)
            linked.append(o)
    yaws = {"front": (0, 10), "three": (38, 14), "right": (90, 8), "left": (-90, 8), "back": (180, 10), "top": (20, 62), "low": (15, -6)}
    tiles = []
    tmp = path + ".tile.png"
    bpy.context.window.scene = scene
    try:
        for view in views:
            yaw, pitch = yaws[view]
            y, p = math.radians(yaw), math.radians(pitch)
            d = close if (close and view == "close") else distance
            cam = scene.camera
            cam.location = V(centre) + V((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * d
            cam.rotation_euler = (V(centre) - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = tmp
            bpy.ops.render.render(write_still=True, scene=scene.name)
            im = bpy.data.images.load(tmp, check_existing=False)
            px = np.zeros(size * size * 4, dtype=np.float32)
            im.pixels.foreach_get(px)
            tiles.append(px.reshape(size, size, 4))
            bpy.data.images.remove(im)
    finally:
        bpy.context.window.scene = window_scene
        for o in linked:
            scene.collection.objects.unlink(o)
    sheet = np.concatenate(tiles, 1)
    out = bpy.data.images.new("EggReviewSheet", sheet.shape[1], sheet.shape[0], alpha=False)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


# ---------- whole eggs ----------
def ribbon(hi, path, width, across=6, dome=0.1, mat=0):
    """A sheet along a path of (point, normal) pairs: width(t) wide, domed across. UVs: u across
    (0..1), v along (0..1). Give it thickness with egg_hi.solidify."""
    n = len(path)
    rows = []
    for i, (p, nrm) in enumerate(path):
        a = path[max(i - 1, 0)][0]
        b = path[min(i + 1, n - 1)][0]
        side = (b - a).cross(nrm).normalized()
        w = width(i / (n - 1)) / 2
        rows.append([hi.v(p + side * (w * (-1 + 2 * j / across)) + nrm * (dome * w * (1 - (-1 + 2 * j / across) ** 2))) for j in range(across + 1)])
    for i in range(n - 1):
        for j in range(across):
            hi.f([rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]],
                 [(j / across, i / (n - 1)), ((j + 1) / across, i / (n - 1)), ((j + 1) / across, (i + 1) / (n - 1)), (j / across, (i + 1) / (n - 1))], mat)


def sphere_spiral(c, radius, out, turns=1.6, reach=1.0, steps=40):
    """Points of a spiral curling over a sphere's surface round the direction `out`, from `reach`
    radians off it in to the middle."""
    out = V(out).normalized()
    e1 = out.cross(V((0, 1, 0)) if abs(out.y) < 0.9 else V((1, 0, 0))).normalized()
    e2 = out.cross(e1)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        th = reach * (1 - 0.88 * t)
        ph = turns * TAU * t
        pts.append(V(c) + (out * math.cos(th) + (e1 * math.cos(ph) + e2 * math.sin(ph)) * math.sin(th)) * radius)
    return pts


def lobes(name, coll, material, spheres, voxel=0.016, smooth=4):
    """A soft shape melted from spheres [(centre, radius, (sx, sy, sz))] by a voxel remesh."""
    bm = bmesh.new()
    for c, r, st in spheres:
        m = bmesh.ops.create_icosphere(bm, subdivisions=4, radius=r)
        for v in m["verts"]:
            q = V((v.co.x * st[0], v.co.y * st[1], v.co.z * st[2]))
            v.co = W.rb(*(V(c) + V((q.x, q.y, q.z))))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    Hm.apply_modifiers(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel}), ("SMOOTH", {"factor": 0.5, "iterations": smooth})])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def harden(obj, angle=40):
    """Edges sharper than `angle` become hard. Call before unwrapping with the same angle, so every
    hard edge is also a UV seam and the normal map has no seam inside an island."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    limit = math.radians(angle)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > limit:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def assemble(egg_id, coll, shell_mat, height, pieces, glows, budget=8000, shell_frac=0.66, low_nu=64, low_nv=40, hi_nu=1024, hi_nv=640,
             shell_ext=0.08, shell_ray=0.2, att_ext=0.04, att_ray=0.14, samples=16, ao_floor=0.5, ao_reach=0.35, hard=None):
    """The usual egg: a painted shell, attachments (`pieces`, each with an optional obj["w"], its
    share of the triangle budget) and Neon parts ({hex: [objects]}). Bakes and exports."""
    hi_shell = shell_mesh(egg_id + "_ShellHi", coll, hi_nu, hi_nv, height, shell_mat)
    low_h = blur(height, height.shape[1] / 128) if height is not None else None
    low_shell = shell_mesh(egg_id + "_ShellLow", coll, low_nu, low_nv, low_h, None, (0.004, 0.004, 0.996, shell_frac - 0.006))
    pairs = [(low_shell, [hi_shell], shell_ext, shell_ray)]
    lows = [low_shell]
    if pieces:
        total = sum(tris(o) * o.get("w", 1.0) for o in pieces) or 1
        k = budget / total
        lp = [decimated(o, min(1.0, k * o.get("w", 1.0)), coll) for o in pieces]
        low_att = K.join(lp, egg_id + "_AttLow", coll)
        for c in lp:
            me = c.data
            bpy.data.objects.remove(c, do_unlink=True)
            bpy.data.meshes.remove(me)
        for p in low_att.data.polygons:
            p.use_smooth = True
        fix_normals(low_att)
        if hard:
            harden(low_att, hard)
        unwrap_into(low_att, (0.004, shell_frac + 0.006, 0.996, 0.996), angle=hard or 66)
        pairs.append((low_att, list(pieces), att_ext, att_ray))
        lows.append(low_att)
    glow_objs = [g for gs in glows.values() for g in gs]
    mat, log = bake(egg_id, pairs, glow_objs, samples=samples, ao_floor=ao_floor, ao_reach=ao_reach)
    parts, total = export(egg_id, lows, glows, coll)
    return parts, total, log


# ---------- hard-surface pieces ----------
def along_shell(a, b, off, steps=8):
    """Points and normals from (s, v) a to (s, v) b over the shell, `off` above it. s may run past
    1 or below 0."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        ss, vv = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        out.append((on(ss % 1.0, vv, off), normal(ss % 1.0, vv)))
    return out


def bar(hi, path, width, height, mat=0, bevel=0.2, closed=False, foot=0.02, solid=False):
    """A forged bar along a path of (point, normal) pairs: a flat-topped section with chamfered
    shoulders, sitting on the surface with its feet sunk into it. Caps its ends. `width` may be a
    function of 0..1."""
    wf = width if callable(width) else (lambda t: width)
    n = len(path)
    rings = []
    for i, (p, nrm) in enumerate(path):
        a = path[(i - 1) % n][0] if closed or i > 0 else p
        b = path[(i + 1) % n][0] if closed or i < n - 1 else p
        side = (b - a).cross(nrm).normalized()
        w = wf(i / max(1, n - 1)) / 2
        h = height
        sec = [(-w, -foot), (-w, h * (1 - bevel)), (-w * (1 - bevel), h), (w * (1 - bevel), h), (w, h * (1 - bevel)), (w, -foot)]
        rings.append([hi.v(p + side * x + nrm * y) for x, y in sec])
    k = 6
    count = n if closed else n - 1
    for i in range(count):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for j in range(k - 1):
            hi.f([r0[j], r0[j + 1], r1[j + 1], r1[j]], [(j / 5, 0), ((j + 1) / 5, 0), ((j + 1) / 5, 1), (j / 5, 1)], mat)
        if solid:       # for a bar in open air, not lying on anything: close its underside
            hi.f([r0[k - 1], r0[0], r1[0], r1[k - 1]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)
    if not closed:
        for r, flip in ((rings[0], False), (rings[-1], True)):
            idx = list(r)[::-1] if flip else list(r)
            hi.f(idx, [(0, 0)] * k, mat)


def rivet(hi, p, nrm, r, mat=0, rings=4, sides=10):
    """A domed rivet head on a surface."""
    nrm = V(nrm).normalized()
    e1 = nrm.cross(V((0, 1, 0)) if abs(nrm.y) < 0.9 else V((1, 0, 0))).normalized()
    e2 = nrm.cross(e1)
    grid = []
    for j in range(rings):
        th = (math.pi / 2) * j / rings
        grid.append([hi.v(p + (e1 * math.cos(TAU * k / sides) + e2 * math.sin(TAU * k / sides)) * r * math.cos(th) + nrm * r * 0.8 * math.sin(th)) for k in range(sides)])
    top = hi.v(p + nrm * r * 0.8)
    for j in range(rings - 1):
        for k in range(sides):
            q = [grid[j][k], grid[j][(k + 1) % sides], grid[j + 1][(k + 1) % sides], grid[j + 1][k]]
            hi.f(q, [(0, 0), (1, 0), (1, 1), (0, 1)], mat)
    for k in range(sides):
        hi.f([grid[-1][k], grid[-1][(k + 1) % sides], top], [(0, 0), (1, 0), (0.5, 1)], mat)


def cut_gem(hi, c, nrm, up, radius, dome, sides=6, mat=0, base=0.05, squash=1.0):
    """A cut stone lying on a surface: girdle, a crown of facets turned half a step, a flat table.
    `squash` narrows it across (for lozenges)."""
    nrm = V(nrm).normalized()
    u = (V(up) - nrm * V(up).dot(nrm)).normalized()
    s = u.cross(nrm).normalized()

    def ring(r, h, phase):
        return [hi.v(c + (s * math.cos(TAU * (k + phase) / sides) * squash + u * math.sin(TAU * (k + phase) / sides)) * r + nrm * h) for k in range(sides)]
    bottom = ring(radius, -base, 0.0)
    girdle = ring(radius, dome * 0.12, 0.0)
    mid = ring(radius * 0.74, dome * 0.68, 0.5)
    table = ring(radius * 0.44, dome, 0.0)
    centre = hi.v(c + nrm * dome)
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for k in range(sides):
        n = (k + 1) % sides
        hi.f([bottom[k], bottom[n], girdle[n], girdle[k]], uv, mat)
        hi.f([girdle[k], girdle[n], mid[k]], uv[:3], mat)
        hi.f([girdle[n], mid[n], mid[k]], uv[:3], mat)
        hi.f([mid[k], table[n], table[k]], uv[:3], mat)
        hi.f([mid[k], mid[n], table[n]], uv[:3], mat)
        hi.f([table[k], table[n], centre], uv[:3], mat)


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def gem_material(name, dark, mid, light, panes=11.0, depth=0.25, rough=0.08, pane_weight=0.55, axis=None):
    """A cut gem's look without transparency: each facet looks into the stone at its own angle
    (True Normal) and lands on its own tone, so neighbouring facets disagree. `axis` (Blender
    space, the way the stone faces) makes the facets that face out brightest and the shoulders
    darkest, the way a cut stone holds its light under the table. Colours are linear."""
    g = Hm._Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    pos, tn = geo.outputs["Position"], geo.outputs["True Normal"]
    add = g.n("ShaderNodeVectorMath", operation="SCALE")
    g.link(tn, add.inputs[0])
    add.inputs[3].default_value = -depth
    sum_ = g.n("ShaderNodeVectorMath", operation="ADD")
    g.link(pos, sum_.inputs[0])
    g.link(add.outputs[0], sum_.inputs[1])
    vo = g.n("ShaderNodeTexVoronoi", **{"Scale": panes})
    g.link(sum_.outputs[0], vo.inputs["Vector"])
    tone = g.n("ShaderNodeTexNoise", **{"Scale": 29.0, "Detail": 0.0})
    g.link(tn, tone.inputs["Vector"])
    v = g.math("ADD", g.math("MULTIPLY", g.bw(vo.outputs["Color"]), pane_weight), g.math("MULTIPLY", tone.outputs["Fac"], 0.75))
    if axis is not None:
        dot = g.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        g.link(tn, dot.inputs[0])
        dot.inputs[1].default_value = tuple(axis)
        v = g.math("ADD", g.math("MULTIPLY", v, 0.45), g.math("MULTIPLY", g.math("POWER", g.math("MAXIMUM", dot.outputs["Value"], 0.0), 3.0), 0.72))
    col = g.ramp(g.math("SUBTRACT", v, 0.12), [(0.0, dark), (0.4, dark), (0.62, mid), (0.82, light), (1.0, light)])
    return g.finish(col, rough, 0.0)


def crystal(hi, base, direction, length, radius, sides=6, tip=0.26, seed=0, mat=0, taper=0.82, lean=0.0):
    """A natural crystal point: a tapering prism of `sides` flat faces, with a slanted pyramid at its
    tip whose apex sits off the axis, as real quartz terminations do."""
    rnd = np.random.default_rng(seed)
    d = V(direction).normalized()
    ref = V((0, 1, 0)) if abs(d.y) < 0.9 else V((1, 0, 0))
    e1 = d.cross(ref).normalized()
    e2 = d.cross(e1)
    b = V(base)
    radii = [radius * rnd.uniform(0.8, 1.15) for _ in range(sides)]
    angs = [TAU * k / sides + rnd.uniform(-0.12, 0.12) for k in range(sides)]
    shoulder = b + d * length * (1 - tip)
    low = [hi.v(b - d * radius * 0.6 + (e1 * math.cos(a) + e2 * math.sin(a)) * r) for a, r in zip(angs, radii)]
    mid = [hi.v(shoulder + (e1 * math.cos(a) + e2 * math.sin(a)) * r * taper) for a, r in zip(angs, radii)]
    apex_off = e1 * rnd.uniform(-1, 1) * radius * 0.3 + e2 * rnd.uniform(-1, 1) * radius * 0.3
    apex = hi.v(b + d * length + apex_off)
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for k in range(sides):
        n = (k + 1) % sides
        hi.f([low[k], low[n], mid[n], mid[k]], uv, mat)
        hi.f([mid[k], mid[n], apex], uv[:3], mat)
    hi.f(low[::-1], [(0, 0)] * sides, mat)


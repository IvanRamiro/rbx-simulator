"""The review lab for the faction secret weapons (run inside Blender, headless): renders what a reviewer needs,
without touching anything open in Blender or anything outside renders/faction_weapons/.

- clay(): every hi piece in one neutral grey (glow pieces in their own flat colour), to judge shape alone;
- views from the six sides of the weapon as authored (Roblox axes: point toward -Z, flats +-Y, edges +-X);
- game(): hide the hi pieces and show the baked game mesh wearing its four maps, with the Neon pieces glowing;
- silhouettes: black on white at thumbnail size;
- a hand proxy and a Sword6 / Spear6 import, to judge grip, contact and scale;
- contact sheets.

Weapons point toward Blender +Y (Roblox -Z), up is Blender +Z (Roblox +Y).
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

import secret_kit as SK

V = Vector
REVIEW = SK.REVIEW

# camera direction, as the place the camera stands, in Roblox axes; and the image's up (the weapon's axis)
VIEWS = {
    "top": (0, 1, 0),        # looking down on the flat the player sees
    "bottom": (0, -1, 0),
    "edge_r": (1, 0, 0),     # from +X, the edge
    "edge_l": (-1, 0, 0),
    "tip": (0, 0, -1),       # from in front of the point
    "pommel": (0, 0, 1),
    "front34": (0.75, 0.55, -0.55),
    "back34": (-0.7, 0.5, 0.7),
}


def rb(v):
    """Roblox direction -> Blender."""
    return V((v[0], -v[2], v[1]))


def gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == kind
            return kind
    return "CPU"


def studio_env(w=1024, h=512):
    """A studio dome as a float image: a soft sky above, a dark floor, and a few softboxes, so a polished edge has
    something bright and something dark to reflect. Equirectangular: x azimuth, y elevation (top = up)."""
    img = bpy.data.images.get("SK_Env")
    if img is None:
        img = bpy.data.images.new("SK_Env", w, h, alpha=False, float_buffer=True)
    ys = (np.arange(h) + 0.5) / h
    el = (ys - 0.5) * math.pi                       # -pi/2 (down) .. pi/2 (up)
    base = np.zeros((h, w, 3), dtype=np.float32)
    up = np.clip((el + 0.15) / 1.0, 0, 1)
    sky = (0.16 + 0.55 * up ** 0.8)[:, None]
    floor = np.clip(0.05 + 0.1 * (el + math.pi / 2) / (math.pi / 2), 0, 1)[:, None]
    lum = np.where(el[:, None] > -0.05, sky, floor) * np.ones((1, w))
    base[:] = lum[..., None] * np.array([0.82, 0.9, 1.0], dtype=np.float32)
    xs = (np.arange(w) + 0.5) / w * 2 * math.pi - math.pi   # azimuth

    def box(az, e, daz, de, power, tint=(1, 1, 1)):
        d_az = np.abs((xs[None, :] - az + math.pi) % (2 * math.pi) - math.pi)
        m = (d_az < daz) & (np.abs(el[:, None] - e) < de)
        soft = np.clip(1 - np.maximum(d_az / daz, np.abs(el[:, None] - e) / de), 0, 1) ** 0.35
        base[...] += (m * soft)[..., None] * power * np.array(tint, dtype=np.float32)
    box(0.7, 0.8, 0.5, 0.3, 5.0, (1.0, 0.97, 0.92))      # key
    box(-2.4, 0.5, 0.35, 0.35, 3.5, (0.9, 0.95, 1.0))     # rim
    box(2.6, 0.2, 0.7, 0.12, 1.6)                         # long strip: a clean line down a polished edge
    box(-1.0, 0.05, 0.4, 0.1, 1.2, (1.0, 0.9, 0.8))       # low warm fill
    box(0.0, 1.35, 1.2, 0.2, 2.2)                         # top
    px = np.ones((h, w, 4), dtype=np.float32)
    px[..., :3] = base
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def _world(scene, sky=True, exposure=1.0):
    w = bpy.data.worlds.get("SK_World") or bpy.data.worlds.new("SK_World")
    w.use_nodes = True
    t = w.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputWorld")
    bg = t.nodes.new("ShaderNodeBackground")
    if sky:
        env = t.nodes.new("ShaderNodeTexEnvironment")
        env.image = studio_env()
        t.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = exposure
    else:
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 1.0
    t.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w


SKY = True     # silhouettes turn this off for a plain white world


def lab(sky=None, dark=False):
    """The review scene: Cycles, Standard view, a studio dome, three lights, a camera. Returns the scene."""
    sky = SKY if sky is None else sky
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    try:
        scene.cycles.device = "GPU"
        gpu()
    except Exception:
        scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    _world(scene, sky)
    cam = bpy.data.objects.get("SK_Cam")
    if cam is None:
        cam = bpy.data.objects.new("SK_Cam", bpy.data.cameras.new("SK_Cam"))
        scene.collection.objects.link(cam)
    scene.camera = cam
    return scene


def _lab_objects():
    return [o for o in bpy.data.objects if o.name.startswith("SK_")]


def bounds(objs):
    pts = []
    for o in objs:
        if o.type == "MESH":
            pts += [o.matrix_world @ v.co for v in o.data.vertices]
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def shoot(objs, view, size=(360, 640), samples=40, ortho=False, centre=None, span=None, lens=60, tag="shot", transparent=True, roll_up=None):
    """One render of the weapon from `view` (a name in VIEWS or a Roblox direction); returns pixels (top row first)."""
    scene = lab_scene()
    cam = scene.camera
    lo, hi = bounds(objs)
    c = V(centre) if centre is not None else (lo + hi) / 2
    diag = (hi - lo).length
    d = rb(VIEWS[view] if isinstance(view, str) else view).normalized()
    up_axis = V(roll_up) if roll_up is not None else V((0, 1, 0))
    if abs(d.dot(up_axis.normalized())) > 0.95:
        up_axis = V((0, 0, 1)) if abs(d.z) < 0.9 else V((0, 1, 0))
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.film_transparent = transparent
    cam.data.type = "ORTHO" if ortho else "PERSP"
    cam.data.lens = lens
    cam.data.sensor_fit = "VERTICAL"
    cam.data.clip_start = 0.05
    cam.data.clip_end = 100
    sp = span or diag * 1.08
    if ortho:
        cam.data.ortho_scale = sp
        dist = 30.0
    else:
        cam.data.sensor_height = 24.0
        dist = sp * 0.5 / math.tan(math.atan(12.0 / lens)) * 1.08 + diag * 0.3
    cam.location = c + d * dist
    # a camera looks down its -Z; its up is the weapon's axis in the image
    q = (c - cam.location).to_track_quat("-Z", "Y")
    cam.rotation_euler = q.to_euler()
    z_axis = -(c - cam.location).normalized()
    x_axis = up_axis.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    from mathutils import Matrix
    m = Matrix(((x_axis.x, y_axis.x, z_axis.x), (x_axis.y, y_axis.y, z_axis.y), (x_axis.z, y_axis.z, z_axis.z)))
    cam.rotation_euler = m.to_euler()
    scene.cycles.samples = samples
    os.makedirs(REVIEW, exist_ok=True)
    tmp = os.path.join(REVIEW, "_%s.png" % tag)
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp, check_existing=False)
    w, h = img.size
    px = np.zeros(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    os.remove(tmp)
    return px.reshape(h, w, 4)[::-1].copy()


def lab_scene():
    return lab()


def save_png(arr, path):
    """arr: top row first, RGBA float 0..1 (display values)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = arr.shape[:2]
    img = bpy.data.images.new("SK_Out", w, h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(arr[::-1], dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


def sheet(tiles, cols, pad=6, bg=(0.07, 0.075, 0.09, 1.0)):
    """Tiles (of any sizes) laid out in rows of `cols`, each in a cell as big as the biggest."""
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    th = max(t.shape[0] for t in tiles)
    tw = max(t.shape[1] for t in tiles)
    out = np.zeros((len(rows) * (th + pad) + pad, cols * (tw + pad) + pad, 4), dtype=np.float32)
    out[:] = bg
    bgv = np.array(bg, dtype=np.float32)
    for r, row in enumerate(rows):
        for c, t in enumerate(row):
            h, w = t.shape[:2]
            y, x = pad + r * (th + pad), pad + c * (tw + pad)
            a = t[..., 3:4]
            out[y:y + h, x:x + w] = t * a + bgv * (1 - a)
    out[..., 3] = 1.0
    return out


# ---------- looks ----------
class _Swap:
    def __init__(self, objs, mat):
        self.objs, self.mat, self.saved = objs, mat, []

    def __enter__(self):
        for o in self.objs:
            self.saved.append((o, [(i, p.material) for i, p in enumerate(o.material_slots)], [p.material_index for p in o.data.polygons]))
            for slot in o.material_slots:
                slot.material = self.mat(o, slot.material)
        return self

    def __exit__(self, *a):
        for o, slots, _ in self.saved:
            for i, m in slots:
                o.material_slots[i].material = m


def clay_material(name="SK_Clay", color=(0.62, 0.62, 0.64)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    t.links.new(bsdf.outputs[0], out.inputs[0])
    return m


def clay(objs):
    """Context manager: every piece in neutral grey, the glow ones left as they are."""
    base = clay_material()

    def pick(o, m):
        return m if (m is not None and m.get("glow")) else base
    return _Swap(objs, pick)


def glow_strength(objs, strength=6.0):
    for o in objs:
        for m in o.data.materials:
            if m and m.get("glow"):
                em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
                em.inputs["Strength"].default_value = strength


def black(objs):
    m = bpy.data.materials.get("SK_Black") or bpy.data.materials.new("SK_Black")
    m.use_nodes = True
    t = m.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0, 0, 0, 1)
    t.links.new(em.outputs[0], out.inputs[0])
    return _Swap(objs, lambda o, mm: m)


def set_visible(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_viewport = not on


# ---------- helpers for the comparison and the hand ----------
def hand_proxy(coll, name="SK_Hand"):
    """A fist round the grip and the start of the forearm, in Roblox axes (z along the grip): a box 0.55 x 0.5
    wide and 0.8 along, and a sleeve behind it. For judging grip, contact and clearance only."""
    import bmesh
    objs = []
    for nm, size, loc in (("fist", (0.58, 0.52, 0.8), (0, 0, 0.0)), ("wrist", (0.46, 0.4, 1.3), (0, 0, 1.0))):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]
            v.co.z *= size[1]   # Blender z = Roblox y
            v.co.y *= size[2]   # Blender y = -Roblox z
        me = bpy.data.meshes.new(name + nm)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name + nm, me)
        coll.objects.link(o)
        o.location = V((loc[0], -loc[2], loc[1]))
        m = bpy.data.materials.get("SK_Skin") or bpy.data.materials.new("SK_Skin")
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.8, 0.55, 0.42, 1)
        b.inputs["Roughness"].default_value = 0.7
        o.data.materials.append(m)
        mod = o.modifiers.new("b", "BEVEL")
        mod.width = 0.07
        mod.segments = 2
        objs.append(o)
    return objs


def import_game(fbx, offset=(0, 0, 0)):
    """Imports a weapon FBX (its maps are embedded or beside it) and moves it by `offset` (Roblox axes). Returns
    its objects."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx, axis_forward="-Z", axis_up="Y")
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.location += V((offset[0], -offset[2], offset[1]))
    return new

"""Renders each finished egg (assets/eggs_v2/<EggId>.fbx) to a transparent icon for the interface
(assets/ui/egg_icons/<EggId>.png; ids in egg_icons.json). Run inside Blender, one egg at a time:
each is imported, rendered and removed before the next.

    import egg_icons; egg_icons.render_all()
"""
import math
import os
import re

import bpy
from mathutils import Vector

REPO = "/Users/ivan/qi-aura-simulator"
EGGS = ["BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg", "JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg",
        "InfernoEgg", "MagmaHeartEgg", "PhoenixAshEgg", "CelestialEgg", "AstralSanctumEgg", "HeavenlyThroneEgg",
        "ForbiddenOriginEgg", "VoidRiftEgg", "PrimordialAbyssEgg"]
SIZE = 256


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.textures, bpy.data.node_groups, bpy.data.worlds):
        for x in list(block):
            block.remove(x)
    for img in list(bpy.data.images):
        if img.type == "IMAGE":
            bpy.data.images.remove(img)
    bpy.data.orphans_purge(do_recursive=True)


def _bounds(objs):
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def _glow(objs):
    for o in objs:
        m = re.search(r"_Glow_([0-9a-fA-F]{6})", o.name)
        if not m:
            continue
        h = m.group(1)
        rgb = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]
        mat = bpy.data.materials.new(o.name + "_glow")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*rgb, 1)
        em.inputs[1].default_value = 2.0
        nt.links.new(em.outputs[0], out.inputs[0])
        o.data.materials.clear()
        o.data.materials.append(mat)


def _light(name, kind, loc, target, energy, size, colour=(1, 1, 1)):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.color = colour
    if kind == "AREA":
        d.size = size
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def render(egg_id, out_dir, size=SIZE):
    clear()
    bpy.ops.import_scene.fbx(filepath="%s/assets/eggs_v2/%s.fbx" % (REPO, egg_id))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    _glow(objs)
    lo, hi = _bounds(objs)
    centre = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.01)
    # the egg's front: exported toward Roblox +z, which the FBX axes bring to Blender -y
    scene = bpy.context.scene
    cam_d = bpy.data.cameras.new("IconCam")
    cam_d.lens = 70
    cam = bpy.data.objects.new("IconCam", cam_d)
    scene.collection.objects.link(cam)
    yaw, pitch = math.radians(22), math.radians(10)
    dist = radius / math.sin(math.atan(18 / 70)) * 0.98
    view = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.location = centre + view * dist
    cam.rotation_euler = (-view).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    r = radius
    _light("Key", "AREA", centre + Vector((-1.6, -2.2, 2.2)) * r, centre, 60 * r * r, 2.5 * r)
    _light("Fill", "AREA", centre + Vector((2.2, -1.6, 0.4)) * r, centre, 18 * r * r, 3 * r, (0.85, 0.92, 1))
    _light("Rim", "AREA", centre + Vector((0.8, 2.4, 1.8)) * r, centre, 45 * r * r, 2 * r, (0.9, 0.95, 1))
    world = bpy.data.worlds.new("IconWorld")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1)
    bg.inputs[1].default_value = 0.55
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    os.makedirs(out_dir, exist_ok=True)
    scene.render.filepath = "%s/%s.png" % (out_dir, egg_id)
    bpy.ops.render.render(write_still=True)
    clear()
    return scene.render.filepath


def render_all(out_dir=None, ids=None):
    out_dir = out_dir or REPO + "/assets/ui/egg_icons"
    return [render(e, out_dir) for e in (ids or EGGS)]

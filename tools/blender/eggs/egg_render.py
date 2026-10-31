"""Presentation renders for the eggs, in their own Blender scene ("EggLab") so the island scenes are
never touched. Objects are linked into the scene's collection for the render and unlinked after.

    render(objects, path, view="front" | "three_quarter" | "back", size=(900, 900), distance=None, cycles=0)
    sheet(rows, path)   rows: [[objects of egg 1, objects of egg 2, ...], ...] laid out in a grid
"""
import math

import bpy
from mathutils import Euler, Vector

SCENE = "EggLab"
BG = (0.012, 0.016, 0.05)


def lab():
    scene = bpy.data.scenes.get(SCENE)
    if scene is None:
        scene = bpy.data.scenes.new(SCENE)
        world = bpy.data.worlds.new(SCENE + "_World")
        world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs[0].default_value = (*BG, 1)
        bg.inputs[1].default_value = 1.0
        scene.world = world
        for name, loc, energy, color in (("Key", (4, -5, 6), 900, (1.0, 0.96, 0.9)), ("Fill", (-6, -3, 3), 300, (0.75, 0.85, 1.0)),
                                         ("Rim", (0, 6, 5), 700, (0.8, 0.9, 1.0))):
            light = bpy.data.lights.new(SCENE + name, "AREA")
            light.energy = energy
            light.color = color
            light.size = 4
            o = bpy.data.objects.new(SCENE + name, light)
            o.location = loc
            o.rotation_euler = (Vector((0, 0, 1.3)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.collection.objects.link(o)
        cam = bpy.data.cameras.new(SCENE + "Cam")
        cam.lens = 70
        co = bpy.data.objects.new(SCENE + "Cam", cam)
        scene.collection.objects.link(co)
        scene.camera = co
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
    return scene


def frame(scene, centre, distance, view):
    cam = scene.camera
    yaw = {"front": 0.0, "three_quarter": math.radians(38), "back": math.pi}[view]
    pitch = math.radians(12)
    # Blender: the egg's front faces -Y (Roblox +Z)
    offset = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * distance
    cam.location = Vector(centre) + offset
    cam.rotation_euler = (Vector(centre) - cam.location).to_track_quat("-Z", "Y").to_euler()


def _bloom(scene, on):
    try:
        scene.eevee.use_bloom = on
    except AttributeError:
        pass


def render(objects, path, view="front", size=(900, 900), centre=(0, 0, 1.4), distance=8.5, cycles=0):
    """cycles > 0 renders with Cycles at that many samples (the high-detail shaders need it: bevel,
    ambient occlusion and per-facet variation are Cycles-only); otherwise EEVEE."""
    scene = lab()
    engine = scene.render.engine
    if cycles:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = cycles
        scene.cycles.use_denoising = True
    linked = []
    for o in objects:
        if o.name not in scene.collection.objects:
            scene.collection.objects.link(o)
            linked.append(o)
    frame(scene, centre, distance, view)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = path
    window_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    try:
        bpy.ops.render.render(write_still=True, scene=scene.name)
    finally:
        bpy.context.window.scene = window_scene
        scene.render.engine = engine
        for o in linked:
            scene.collection.objects.unlink(o)
    return path

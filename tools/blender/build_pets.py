"""Models the seven Beginner Qi Egg pets in Blender, in the concept art's
faceted low-poly crystal style, renders previews and exports one FBX per pet.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_pets.py -- [--renders DIR]

Each pet is built from low-poly primitives (icospheres, cones, tapered curves
and flat fins) so every face is a flat facet. Colours come from a small
palette texture: each face is mapped to a swatch, picked lighter for faces
that point up and darker for faces that point down, so the model shades like
cut crystal even under flat lighting.

Exported files (assets/pets):
    <PetId>.fbx            Objects: "<PetId>_Body" (textured with the palette)
                           and "<PetId>_Glow_<rrggbb>" pieces, which the game
                           turns into glowing Neon in that colour.
    <PetId>_palette.png    The palette texture (also embedded in the FBX).
Models face -Y with Z up in Blender (the FBX export turns them to face -Z,
Y up, like the game's pets) and are about 2.5 to 3 units long.
"""

import math
import os
import struct
import sys
import zlib

import bmesh
import bpy
from mathutils import Euler, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(ROOT, "assets", "pets")

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RENDER_DIR = args[args.index("--renders") + 1] if "--renders" in args else None

SWATCH = 8  # Pixels per palette swatch


# Scene ------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.view_settings.view_transform = "Standard"  # Show the palette colours as they are
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    world = bpy.data.worlds.new("World")
    world.color = (0.03, 0.035, 0.07)
    scene.world = world
    return scene


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def apply_transform(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def look_rotation(direction):
    """Rotation that turns +Z to point along `direction`."""
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_euler()


# A pet under construction ----------------------------------------------------------

class Pet:
    def __init__(self, pet_id, offset):
        self.pet_id = pet_id
        self.offset = Vector(offset)
        self.colors = []  # Unique body colours, in palette order
        self.parts = []  # (object, colour, glow)

    def color_index(self, color):
        if color not in self.colors:
            self.colors.append(color)
        return self.colors.index(color)

    def add(self, obj, color, glow=False):
        obj.location = obj.location + self.offset
        apply_transform(obj)
        for polygon in obj.data.polygons:
            polygon.use_smooth = False
        self.color_index(color)
        self.parts.append((obj, color, glow))
        return obj

    # Shapes ----------------------------------------------------------------------

    def gem(self, color, location, scale, rotation=(0, 0, 0), detail=1, glow=False):
        """A faceted, stretched icosphere (bodies, heads, eyes, gems)."""
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, radius=1, location=location)
        obj = bpy.context.active_object
        obj.scale = scale
        obj.rotation_euler = Euler([math.radians(a) for a in rotation])
        return self.add(obj, color, glow)

    def spike(self, color, base, tip, radius, sides=4, glow=False):
        """A faceted cone from `base` to a point at `tip` (horns, ears, claws)."""
        base, tip = Vector(base), Vector(tip)
        bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=radius, radius2=0, depth=(tip - base).length,
                                        location=(base + tip) / 2)
        obj = bpy.context.active_object
        obj.rotation_euler = look_rotation(tip - base)
        return self.add(obj, color, glow)

    def limb(self, color, base, tip, radius_base, radius_tip, sides=6, glow=False):
        """A tapered, faceted cylinder from `base` to `tip` (legs, necks)."""
        base, tip = Vector(base), Vector(tip)
        bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=radius_base, radius2=radius_tip,
                                        depth=(tip - base).length, location=(base + tip) / 2)
        obj = bpy.context.active_object
        obj.rotation_euler = look_rotation(tip - base)
        return self.add(obj, color, glow)

    def tube(self, color, points, radii, sides_res=1, length_res=2, glow=False):
        """A tapered tube along a smooth curve through `points` (tails, serpent bodies)."""
        curve = bpy.data.curves.new("Tube", "CURVE")
        curve.dimensions = "3D"
        spline = curve.splines.new("NURBS")
        spline.points.add(len(points) - 1)
        for point, co, radius in zip(spline.points, points, radii):
            point.co = (co[0], co[1], co[2], 1)
            point.radius = radius
        spline.use_endpoint_u = True
        spline.order_u = 3
        spline.resolution_u = length_res
        curve.bevel_depth = 1.0
        curve.bevel_resolution = sides_res
        curve.use_fill_caps = True
        obj = link(bpy.data.objects.new("Tube", curve))
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        obj = bpy.context.active_object
        return self.add(obj, color, glow)

    def fin(self, color, outline, thickness, location, rotation, glow=False):
        """A flat, slightly thick polygon (wings, fins, tail flukes, flames).
        `outline` is a list of (x, z) points in the fin's own flat plane."""
        mesh = bpy.data.meshes.new("Fin")
        bm = bmesh.new()
        front = [bm.verts.new((x, -thickness / 2, z)) for x, z in outline]
        back = [bm.verts.new((x, thickness / 2, z)) for x, z in outline]
        bm.faces.new(front)
        bm.faces.new(list(reversed(back)))
        count = len(outline)
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new((front[i], front[j], back[j], back[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        obj = link(bpy.data.objects.new("Fin", mesh))
        obj.location = location
        obj.rotation_euler = Euler([math.radians(a) for a in rotation])
        return self.add(obj, color, glow)

    def ring(self, color, location, radius, thickness, rotation, glow=True):
        bpy.ops.mesh.primitive_torus_add(major_segments=18, minor_segments=4, major_radius=radius,
                                         minor_radius=thickness, location=location)
        obj = bpy.context.active_object
        obj.rotation_euler = Euler([math.radians(a) for a in rotation])
        return self.add(obj, color, glow)

    def mirror(self, method, color, *args, **kwargs):
        """Builds a shape (positions given for the right side, +X), then adds an
        exact mirror image of it on the left side."""
        obj = method(color, *args, **kwargs)
        copy = obj.copy()
        copy.data = obj.data.copy()
        link(copy)
        bm = bmesh.new()
        bm.from_mesh(copy.data)
        for vert in bm.verts:
            vert.co.x = 2 * self.offset.x - vert.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces)  # Mirroring turns faces inside out
        bm.to_mesh(copy.data)
        bm.free()
        self.parts.append((copy, color, kwargs.get("glow", False)))
        return copy


# Palette texture and UVs ------------------------------------------------------------

def shades(color):
    r, g, b = color
    light = tuple(min(255, int(c + (255 - c) * 0.28)) for c in color)
    dark = tuple(int(c * 0.62) for c in color)
    return [light, color, dark]


def write_png(path, width, height, pixels):
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def build_palette(pet):
    """Writes the palette PNG: one column per colour, rows light / base / dark."""
    width, height = SWATCH * len(pet.colors), SWATCH * 3
    rows = []
    for row in range(height):
        shade = row // SWATCH
        line = bytearray()
        for column in range(width):
            line.extend(shades(pet.colors[column // SWATCH])[shade])
        rows.append(line)
    path = os.path.join(OUTPUT_DIR, pet.pet_id + "_palette.png")
    write_png(path, width, height, rows)
    return path


def map_faces(pet, obj, color):
    """Points every face at its colour's swatch, lighter when facing up."""
    column = pet.colors.index(color)
    count = len(pet.colors)
    # Primitives come with their own UVs; replace them so the palette mapping is the one used
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    uv_layer = obj.data.uv_layers.new(name="UVMap")
    for polygon in obj.data.polygons:
        normal_z = polygon.normal.z
        if normal_z > 0.45:
            shade = 0
        elif normal_z < -0.3:
            shade = 2
        else:
            # A few side facets catch the light, like cut crystal
            shade = 0 if (polygon.index * 7) % 9 == 0 else 1
        # Image rows run top to bottom, UV v runs bottom to top
        u = (column + 0.5) / count
        v = 1 - (shade + 0.5) / 3
        for loop_index in polygon.loop_indices:
            uv_layer.data[loop_index].uv = (u, v)


def finish(pet):
    """Joins the pet into "Body" plus one "Glow_<hex>" object per glow colour."""
    palette_path = build_palette(pet)
    image = bpy.data.images.load(palette_path)
    image.pack()
    material = bpy.data.materials.new(pet.pet_id + "Palette")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    principled = nodes["Principled BSDF"]
    material.node_tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    principled.inputs["Roughness"].default_value = 0.45

    groups = {}
    for obj, color, glow in pet.parts:
        map_faces(pet, obj, color)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        name = pet.pet_id + ("_Glow_%02x%02x%02x" % color if glow else "_Body")
        groups.setdefault(name, []).append(obj)

    finished = []
    for name, objects in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        joined = bpy.context.active_object
        joined.name = name
        joined.data.name = pet.pet_id + "_" + name
        finished.append(joined)
    pet.objects = finished
    return finished


# Pets --------------------------------------------------------------------------------

def aqua_wisp(pet):
    blue, light, deep, fin = (95, 190, 255), (165, 230, 255), (45, 120, 225), (130, 215, 255)
    pet.gem(blue, (0, 0, 0.75), (0.62, 0.66, 0.6), detail=2)  # Big round head-body
    pet.limb(blue, (0, 0.35, 0.72), (0, 1.0, 0.82), 0.42, 0.14, sides=7)  # Body tapering back
    pet.gem(light, (0, -0.22, 0.55), (0.42, 0.42, 0.3), detail=1)  # Pale chin and belly
    # Forked, flowing tail fin
    pet.fin(fin, [(0, 0), (0.55, 0.42), (0.35, 0.1), (0.62, -0.2), (0.12, -0.08)], 0.05, (0, 1.0, 0.82), (0, 0, 90), glow=True)
    # Swept dorsal fin and side fins
    pet.fin(fin, [(-0.25, 0), (0.15, 0.48), (0.35, 0.05)], 0.05, (0, 0.05, 1.3), (0, 0, 90), glow=True)
    pet.mirror(pet.fin, fin, [(0, 0), (0.48, -0.08), (0.3, -0.32)], 0.04, (0.55, 0.1, 0.62), (0, -25, 20), glow=True)
    # Big glossy eyes with highlights, rosy cheeks
    pet.mirror(pet.gem, (20, 35, 95), (0.22, -0.55, 0.85), (0.14, 0.07, 0.17), detail=2)
    pet.mirror(pet.gem, (255, 255, 255), (0.17, -0.61, 0.91), (0.045, 0.03, 0.045), detail=1, glow=True)
    pet.mirror(pet.gem, (255, 170, 210), (0.38, -0.5, 0.66), (0.08, 0.03, 0.05), detail=1)
    # Floating water droplets
    for location, size in [((0.75, -0.2, 1.35), 0.09), ((-0.8, 0.3, 1.1), 0.07), ((0.65, 0.8, 0.35), 0.06), ((-0.55, -0.45, 0.25), 0.05)]:
        pet.gem(light, location, (size, size, size * 1.3), detail=1, glow=True)


def ember_wyrm(pet):
    scales, dark, lava, ember, membrane = (75, 38, 36), (45, 24, 24), (255, 115, 35), (255, 200, 80), (235, 95, 35)
    pet.gem(scales, (0, 0.15, 0.78), (0.42, 0.64, 0.42), detail=1)  # Body
    pet.gem(lava, (0, 0.05, 0.6), (0.24, 0.5, 0.2), detail=1, glow=True)  # Glowing lava belly
    pet.limb(scales, (0, -0.3, 0.9), (0, -0.62, 1.32), 0.2, 0.14, sides=6)  # Neck
    pet.gem(scales, (0, -0.72, 1.44), (0.26, 0.3, 0.24), detail=1)  # Head
    pet.gem(scales, (0, -0.98, 1.38), (0.15, 0.2, 0.12), detail=1)  # Snout
    pet.mirror(pet.gem, lava, (0.11, -0.86, 1.5), (0.05, 0.035, 0.03), detail=1, glow=True)  # Glowing eyes
    # Swept-back horns, two pairs
    pet.mirror(pet.spike, lava, (0.1, -0.68, 1.58), (0.2, -0.38, 1.98), 0.07, sides=4)
    pet.mirror(pet.spike, lava, (0.16, -0.62, 1.5), (0.32, -0.4, 1.72), 0.05, sides=4)
    # Spines along the back
    for y, z, h in [(-0.25, 1.1, 0.2), (0.05, 1.08, 0.22), (0.35, 1.02, 0.2), (0.6, 0.95, 0.16)]:
        pet.spike(lava, (0, y, z), (0, y + 0.1, z + h), 0.06, sides=4)
    # Big bat wings with an orange membrane
    wing = [(0, 0), (0.55, 0.55), (1.15, 0.75), (0.95, 0.35), (1.0, 0.0), (0.72, 0.05), (0.62, -0.25), (0.35, -0.05)]
    pet.mirror(pet.fin, membrane, wing, 0.04, (0.18, 0.05, 1.05), (0, -25, 10))
    # Legs with claws
    for y in (-0.2, 0.45):
        pet.mirror(pet.limb, scales, (0.24, y, 0.62), (0.27, y - 0.05, 0.1), 0.14, 0.1, sides=6)
        pet.mirror(pet.spike, dark, (0.26, y - 0.08, 0.08), (0.26, y - 0.22, 0.04), 0.05, sides=4)
    # Tail curling up to a flame
    pet.tube(scales, [(0, 0.6, 0.72), (0, 1.0, 0.55), (0, 1.35, 0.65), (0, 1.5, 0.95), (0, 1.45, 1.2)], [0.2, 0.15, 0.1, 0.07, 0.05])
    pet.spike(lava, (0, 1.44, 1.15), (0, 1.48, 1.55), 0.12, sides=5, glow=True)
    pet.spike(ember, (0, 1.44, 1.2), (0.05, 1.42, 1.45), 0.07, sides=5, glow=True)
    # Glowing cracks on the flanks
    pet.mirror(pet.fin, lava, [(0, 0), (0.35, 0.08), (0.55, -0.05)], 0.02, (0.3, -0.05, 0.85), (0, 0, 80), glow=True)


def lunar_hopper(pet):
    fur, pale, face, glow = (165, 150, 238), (225, 220, 255), (200, 190, 255), (110, 140, 255)
    pet.gem(fur, (0, 0.12, 0.5), (0.4, 0.46, 0.46), detail=1)  # Round sitting body
    pet.gem(pale, (0, -0.15, 0.5), (0.27, 0.22, 0.33), detail=1)  # Chest
    pet.gem(face, (0, -0.32, 1.05), (0.34, 0.32, 0.31), detail=2)  # Head
    pet.gem(pale, (0, -0.58, 0.98), (0.15, 0.1, 0.11), detail=1)  # Muzzle
    pet.gem((255, 160, 200), (0, -0.67, 1.03), (0.04, 0.03, 0.03), detail=1)  # Nose
    pet.mirror(pet.gem, (20, 30, 90), (0.15, -0.58, 1.12), (0.09, 0.05, 0.11), detail=2)
    pet.mirror(pet.gem, (255, 255, 255), (0.12, -0.62, 1.17), (0.03, 0.02, 0.03), detail=1, glow=True)
    # Long ears with glowing inner sides
    pet.mirror(pet.limb, fur, (0.13, -0.25, 1.28), (0.24, -0.05, 2.05), 0.1, 0.03, sides=5)
    pet.mirror(pet.limb, glow, (0.13, -0.29, 1.32), (0.23, -0.1, 1.95), 0.05, 0.015, sides=4, glow=True)
    # Big hind legs, front paws and a fluffy tail
    pet.mirror(pet.gem, fur, (0.3, 0.2, 0.32), (0.16, 0.3, 0.22), detail=1)
    pet.mirror(pet.gem, pale, (0.3, -0.05, 0.08), (0.1, 0.22, 0.07), detail=1)
    pet.mirror(pet.limb, pale, (0.14, -0.28, 0.45), (0.15, -0.33, 0.08), 0.07, 0.06, sides=5)
    pet.gem(pale, (0, 0.6, 0.45), (0.14, 0.14, 0.14), detail=1)
    # Glowing star markings and floating stars
    pet.mirror(pet.fin, glow, [(0, 0), (0.25, 0.1), (0.4, -0.05), (0.2, -0.12)], 0.02, (0.4, 0.15, 0.55), (0, 0, 85), glow=True)
    for location in [(0.55, -0.4, 1.65), (-0.6, 0.2, 1.4), (0.5, 0.55, 1.0)]:
        pet.gem((235, 240, 255), location, (0.05, 0.05, 0.05), detail=1, glow=True)


def volt_fox(pet):
    fur, dark, white, spark = (255, 205, 50), (55, 45, 40), (255, 248, 225), (255, 240, 130)
    pet.gem(fur, (0, 0.15, 0.68), (0.3, 0.55, 0.3), detail=1)  # Body
    pet.gem(white, (0, -0.25, 0.68), (0.22, 0.18, 0.25), detail=1)  # White chest ruff
    pet.gem(fur, (0, -0.48, 1.08), (0.27, 0.27, 0.25), detail=1)  # Head
    pet.spike(white, (0, -0.65, 1.02), (0, -0.98, 0.98), 0.14, sides=5)  # Snout
    pet.gem(dark, (0, -0.98, 0.99), (0.035, 0.03, 0.03), detail=1)  # Nose
    pet.mirror(pet.gem, (70, 45, 20), (0.12, -0.7, 1.13), (0.07, 0.04, 0.07), detail=2)
    pet.mirror(pet.gem, (255, 255, 255), (0.1, -0.74, 1.16), (0.025, 0.02, 0.025), detail=1, glow=True)
    # Big pointed ears with dark tips
    pet.mirror(pet.spike, fur, (0.14, -0.42, 1.25), (0.3, -0.38, 1.75), 0.13, sides=4)
    pet.mirror(pet.spike, dark, (0.27, -0.39, 1.62), (0.3, -0.38, 1.78), 0.045, sides=4)
    # Legs with dark lightning "socks"
    for y in (-0.15, 0.45):
        pet.mirror(pet.limb, fur, (0.15, y, 0.55), (0.17, y, 0.28), 0.08, 0.06, sides=5)
        pet.mirror(pet.limb, dark, (0.17, y, 0.3), (0.17, y - 0.04, 0.02), 0.06, 0.05, sides=5)
    # A big, fluffy zig-zag lightning tail with a white tip
    pet.tube(fur, [(0, 0.6, 0.75), (0.15, 0.95, 1.0), (0.05, 1.1, 1.35), (0.25, 1.25, 1.6)], [0.13, 0.2, 0.2, 0.12])
    pet.spike(white, (0.24, 1.22, 1.55), (0.32, 1.3, 1.95), 0.13, sides=5)
    pet.fin(dark, [(0, 0), (0.3, 0.08), (0.15, -0.1), (0.4, -0.05)], 0.02, (0.24, 0.0, 0.8), (0, 0, 90))  # Body bolt marks
    pet.fin(dark, [(0, 0), (0.3, 0.08), (0.15, -0.1), (0.4, -0.05)], 0.02, (-0.24, 0.0, 0.8), (0, 0, 90))
    # Crackling sparks
    pet.fin(spark, [(0, 0), (0.12, 0.2), (0.06, 0.2), (0.18, 0.42), (0.02, 0.18), (0.08, 0.18)], 0.03, (0.45, 0.9, 1.8), (0, 0, 90), glow=True)
    pet.gem(spark, (-0.45, 0.2, 1.4), (0.05, 0.05, 0.05), detail=1, glow=True)


def golden_kirin(pet):
    gold, cream, jade, hoof = (240, 195, 80), (252, 240, 205), (110, 235, 210), (120, 85, 40)
    pet.gem(gold, (0, 0.15, 0.98), (0.3, 0.6, 0.32), detail=1)  # Body
    pet.limb(gold, (0, -0.32, 1.08), (0, -0.55, 1.55), 0.17, 0.12, sides=6)  # Neck
    pet.gem(gold, (0, -0.68, 1.65), (0.17, 0.27, 0.16), detail=1)  # Head
    pet.gem(cream, (0, -0.92, 1.6), (0.1, 0.16, 0.09), detail=1)  # Muzzle
    pet.mirror(pet.gem, jade, (0.11, -0.8, 1.72), (0.045, 0.03, 0.04), detail=1, glow=True)  # Jade eyes
    # Flowing cream mane
    for y, z in [(-0.62, 1.82), (-0.45, 1.6), (-0.3, 1.38)]:
        pet.fin(cream, [(0, 0), (0.35, 0.2), (0.25, -0.05), (0.42, -0.2)], 0.05, (0, y, z), (0, 0, 90))
    # Big branching golden antlers with glowing jade tips
    for side in (1, -1):
        base = Vector((0.08 * side, -0.62, 1.78))
        main_tip = Vector((0.32 * side, -0.45, 2.45))
        pet.limb(gold, base, main_tip, 0.04, 0.02, sides=4)
        for t, branch in [(0.4, Vector((0.42 * side, -0.62, 2.15))), (0.7, Vector((0.12 * side, -0.38, 2.4)))]:
            start = base.lerp(main_tip, t)
            pet.limb(gold, start, branch, 0.025, 0.012, sides=4)
            pet.gem(jade, tuple(branch), (0.035, 0.035, 0.035), detail=1, glow=True)
        pet.gem(jade, tuple(main_tip), (0.04, 0.04, 0.04), detail=1, glow=True)
    # Slender legs with dark hooves
    for y in (-0.2, 0.5):
        pet.mirror(pet.limb, gold, (0.15, y, 0.85), (0.16, y, 0.12), 0.085, 0.05, sides=5)
        pet.mirror(pet.gem, hoof, (0.16, y - 0.02, 0.08), (0.05, 0.06, 0.05), detail=1)
    # A flowing tail curling up, cream with a gold tip
    pet.tube(cream, [(0, 0.7, 1.05), (0, 1.05, 1.15), (0, 1.3, 1.4), (0, 1.2, 1.65), (0, 1.0, 1.6)], [0.1, 0.16, 0.14, 0.09, 0.03])
    pet.gem(jade, (0, -0.32, 0.95), (0.06, 0.03, 0.06), detail=1, glow=True)  # Chest swirl


def astral_whale(pet):
    deep, belly, crystal, star = (60, 85, 210), (205, 225, 255), (120, 115, 255), (235, 240, 255)
    pet.gem(deep, (0, -0.2, 0.82), (0.58, 0.82, 0.52), detail=2)  # Big rounded head
    pet.limb(deep, (0, 0.2, 0.84), (0, 1.0, 1.0), 0.46, 0.2, sides=8)  # Body tapering back
    pet.gem(belly, (0, -0.3, 0.6), (0.46, 0.72, 0.3), detail=1)  # Pale belly
    pet.limb(deep, (0, 0.95, 0.98), (0, 1.45, 1.25), 0.21, 0.07, sides=7)  # Tail stock rising
    # Wide glowing crystal flukes, swept back and tilted up
    fluke = [(0, -0.05), (0.42, 0.12), (0.8, 0.5), (0.72, 0.18), (0.4, -0.02)]
    pet.mirror(pet.fin, crystal, fluke, 0.04, (0.02, 1.43, 1.25), (-70, 0, 0), glow=True)
    # Crystal flippers sticking out to the sides, swept back and drooping a little
    flipper = [(0, -0.12), (0.5, 0.12), (0.62, 0.42), (0.28, 0.25), (0, 0.15)]
    pet.mirror(pet.fin, crystal, flipper, 0.04, (0.42, -0.4, 0.55), (-90, 25, 0), glow=True)
    for y, h in [(-0.45, 0.28), (-0.1, 0.42), (0.3, 0.32), (0.65, 0.2)]:
        pet.spike(crystal, (0, y, 1.25), (0, y + 0.12, 1.25 + h), 0.09, sides=4, glow=True)
    pet.mirror(pet.gem, (20, 25, 70), (0.42, -0.72, 0.85), (0.08, 0.05, 0.1), detail=2)
    pet.mirror(pet.gem, (255, 255, 255), (0.45, -0.76, 0.91), (0.03, 0.02, 0.03), detail=1, glow=True)
    for location in [(0.35, -0.4, 1.2), (-0.3, 0.1, 1.22), (0.25, 0.5, 1.12), (-0.4, -0.55, 1.05), (0.5, 0.0, 1.0)]:
        pet.gem(star, location, (0.035, 0.035, 0.035), detail=1, glow=True)


def origin_serpent(pet):
    silver, teal, deep_teal = (225, 232, 236), (60, 215, 185), (35, 120, 120)
    # A body coiling upward in a spiral, from the tail tip to the neck
    coil = [(0.1, 0.55, 0.12), (-0.25, 0.35, 0.2), (-0.32, -0.05, 0.35), (0.0, -0.32, 0.55), (0.32, -0.05, 0.75),
            (0.3, 0.35, 0.95), (0.0, 0.5, 1.15), (-0.25, 0.25, 1.35), (-0.15, -0.15, 1.5), (0.0, -0.45, 1.62)]
    pet.tube(silver, coil, [0.04, 0.08, 0.12, 0.15, 0.16, 0.16, 0.15, 0.14, 0.13, 0.12], sides_res=1, length_res=4)
    # Teal fins along the back of the coil
    for co in coil[2:-1]:
        pet.spike(teal, co, (co[0] * 0.85, co[1] + 0.08, co[2] + 0.28), 0.05, sides=4)
    pet.gem(deep_teal, coil[0], (0.06, 0.06, 0.06), detail=1)  # Tail tip
    # Dragon head with swept horns, glowing whiskers and eyes
    pet.gem(silver, (0, -0.65, 1.72), (0.17, 0.25, 0.15), detail=1)
    pet.gem(silver, (0, -0.88, 1.67), (0.1, 0.16, 0.08), detail=1)  # Snout
    pet.mirror(pet.spike, teal, (0.08, -0.58, 1.84), (0.24, -0.3, 2.12), 0.05, sides=4)
    pet.mirror(pet.spike, teal, (0.12, -0.55, 1.78), (0.32, -0.38, 1.9), 0.035, sides=4)
    pet.mirror(pet.limb, teal, (0.08, -0.98, 1.64), (0.42, -1.05, 1.5), 0.012, 0.004, sides=3, glow=True)
    pet.mirror(pet.gem, teal, (0.11, -0.8, 1.78), (0.04, 0.03, 0.035), detail=1, glow=True)
    # The origin orb, ringed
    pet.gem(teal, (0.5, -0.15, 2.2), (0.15, 0.15, 0.15), detail=2, glow=True)
    pet.ring(teal, (0.5, -0.15, 2.2), 0.3, 0.012, (70, 0, 20))


PETS = [
    ("AquaWisp", aqua_wisp),
    ("EmberWyrm", ember_wyrm),
    ("LunarHopper", lunar_hopper),
    ("VoltFox", volt_fox),
    ("GoldenKirin", golden_kirin),
    ("AstralWhale", astral_whale),
    ("OriginSerpent", origin_serpent),
]


# Rendering and export ------------------------------------------------------------------

def render(scene, name, location, target):
    camera_data = bpy.data.cameras.new("Camera")
    camera_data.lens = 60
    camera = link(bpy.data.objects.new("Camera", camera_data))
    camera.location = location
    direction = Vector(target) - Vector(location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.filepath = os.path.join(RENDER_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)


def export(pet):
    # Pets rebuilt by hand (tools/blender/<PetId>.blend) are exported with
    # export_pet.py instead; don't overwrite them with this generated version
    if os.path.exists(os.path.join(os.path.dirname(__file__), pet.pet_id + ".blend")):
        print("skipped", pet.pet_id, "(hand-built .blend exists)")
        return
    bpy.ops.object.select_all(action="DESELECT")
    for obj in pet.objects:
        obj.select_set(True)
        obj.location = obj.location - pet.offset  # Export each pet centred on the origin
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUTPUT_DIR, pet.pet_id + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_scale_options="FBX_SCALE_UNITS",
        path_mode="COPY",
        embed_textures=True,
        mesh_smooth_type="FACE",
    )
    for obj in pet.objects:
        obj.location = obj.location + pet.offset


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scene = reset_scene()
    pets = []
    for index, (pet_id, build) in enumerate(PETS):
        pet = Pet(pet_id, ((index - 3) * 3.2, 0, 0))
        build(pet)
        finish(pet)
        pets.append(pet)

    for pet in pets:
        export(pet)
        print("exported", pet.pet_id, [obj.name for obj in pet.objects])

    if RENDER_DIR:
        os.makedirs(RENDER_DIR, exist_ok=True)
        for pet in pets:
            # Only this pet in the picture
            for other in pets:
                for obj in other.objects:
                    obj.hide_render = other is not pet
            center = pet.offset + Vector((0, 0.1, 0.95))
            render(scene, pet.pet_id + "_threequarter", center + Vector((-3.2, -4.2, 1.6)), center)
            render(scene, pet.pet_id + "_side", center + Vector((-5.2, 0, 0.4)), center)
        for pet in pets:
            for obj in pet.objects:
                obj.hide_render = False
        scene.render.resolution_x = 2000
        scene.render.resolution_y = 700
        render(scene, "lineup", (0, -26, 4), (0, 0, 1))


main()

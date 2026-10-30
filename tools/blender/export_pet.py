"""Exports a hand-built pet (tools/blender/<PetId>.blend) for the game.

    /Applications/Blender.app/Contents/MacOS/Blender -b tools/blender/<PetId>.blend \
        -P tools/blender/export_pet.py -- <PetId> [--out assets/aura/<name>]

The pet is every mesh in the collection named <PetId>, built facing -Y with
Z up, each part coloured with plain materials (Principled BSDF base colour).
Materials with the custom property "glow" become glowing Neon in the game;
everything else is baked into one palette texture.

Writes (assets/pets):
    <PetId>.fbx            "<PetId>_Body" (palette textured) and one
                           "<PetId>_Glow_<rrggbb>" object per glow colour
    <PetId>_palette.png    The palette (also embedded in the FBX)
The working file is left untouched (nothing is saved).

Animated pets: --rig keeps each rig part separate instead of one body. Every
object carries a custom property "rig" naming its part (Body, Head, WingL...).
Each part becomes "<PetId>_<Part>" plus "<PetId>_<Part>_Glow_<rrggbb>", and
marker objects (custom property "marker") become tiny meshes the game reads
positions from: "Pivot_<Part>" -> "<PetId>_Pivot_<Part>" (the part's joint),
"Point_<Name>" -> "<PetId>_Point_<Name>" (an effect attachment).

Sculpted pets: --baked (implies --rig) keeps each part's own baked texture
material instead of the palette, and writes <PetId>_color.png and
<PetId>_normal.png next to the FBX.
"""

import os
import struct
import sys
import zlib

import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(ROOT, "assets", "pets")
SWATCH = 8  # Pixels per palette swatch

ARGS = sys.argv[sys.argv.index("--") + 1:]
PET_ID = ARGS[0]
# Aura pieces and other non-pet models: --out DIR writes the FBX there instead of assets/pets
if "--out" in ARGS:
    OUTPUT_DIR = os.path.join(ROOT, ARGS[ARGS.index("--out") + 1])
RIG = "--rig" in ARGS or "--baked" in ARGS
# Pets with a hand-baked texture (sculpted detail): keep their materials, skip the palette
BAKED = "--baked" in ARGS


def to_srgb(channel):
    channel = max(0.0, min(1.0, channel))
    return channel * 12.92 if channel <= 0.0031308 else 1.055 * channel ** (1 / 2.4) - 0.055


def base_color(material):
    """The material's base colour as 0-255 sRGB."""
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return tuple(round(to_srgb(c) * 255) for c in bsdf.inputs["Base Color"].default_value[:3])


def write_png(path, width, height, rows):
    raw = b"".join(b"\x00" + bytes(row) for row in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def join(objects, name):
    # The source part may already use the name; the game needs it exact
    for block in (bpy.data.objects, bpy.data.meshes):
        existing = block.get(name)
        if existing:
            existing.name = name + "_Source"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    joined.data.name = name
    return joined


def export_rig_parts(copies, is_glow):
    """Joins each rig part on its own (body and per-colour glow), and names the
    joint and effect markers so the game can find them."""
    exported = []
    parts = {}
    for obj in copies:
        kind = obj.get("marker")
        if kind:
            # Pivot_<Part> / Point_<Name>, as built; the copy may have gained a suffix
            label = obj.name.split(".")[0]
            exported.append(join([obj], PET_ID + "_" + label))
            continue
        parts.setdefault(obj.get("rig", "Body"), []).append(obj)
    for part, objects in parts.items():
        # Sort before joining: a join deletes all but one of the objects it merges
        solid = [obj for obj in objects if not is_glow(obj)]
        glow_groups = {}
        for obj in objects:
            if is_glow(obj):
                glow_groups.setdefault(base_color(obj.material_slots[0].material), []).append(obj)
        if solid:
            exported.append(join(solid, PET_ID + "_" + part))
        for color, group in glow_groups.items():
            exported.append(join(group, PET_ID + "_" + part + "_Glow_%02x%02x%02x" % color))
    return exported


def export_fbx(exported):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in exported:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUTPUT_DIR, PET_ID + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_scale_options="FBX_SCALE_UNITS",
        path_mode="COPY",
        embed_textures=True,
        mesh_smooth_type="FACE",
    )


def export_baked(copies, is_glow):
    """--baked: the solid parts keep their baked texture material (colour map,
    plus a normal map) and smooth shading; glow parts become flat Neon pieces.
    The textures are also written as <PetId>_color.png / _normal.png."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for image in bpy.data.images:
        for suffix in ("_Color", "_Normal"):
            if image.name == PET_ID + suffix:
                image.filepath_raw = os.path.join(OUTPUT_DIR, PET_ID + suffix.lower() + ".png")
                image.file_format = "PNG"
                image.save()
    exported = export_rig_parts(copies, is_glow)
    for obj in exported:
        if is_glow(obj):
            for polygon in obj.data.polygons:
                polygon.use_smooth = False
    export_fbx(exported)
    low = [min(v.co[i] for obj in exported for v in obj.data.vertices) for i in range(3)]
    high = [max(v.co[i] for obj in exported for v in obj.data.vertices) for i in range(3)]
    size = [h - l for h, l in zip(high, low)]
    print("EXPORTED", PET_ID, [obj.name for obj in exported],
          "tris", sum(len(p.vertices) - 2 for obj in exported for p in obj.data.polygons),
          "size", [round(s, 2) for s in size], "longest", round(max(size), 2))


def main():
    collection = bpy.data.collections[PET_ID]
    sources = [obj for obj in collection.all_objects if obj.type == "MESH" and not obj.hide_render]

    # Work on copies with their transforms applied
    copies = []
    for obj in sources:
        copy = obj.copy()
        copy.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(copy)
        copy.data.transform(obj.matrix_world)
        copy.matrix_world.identity()
        copies.append(copy)

    def is_glow(obj):
        materials = [slot.material for slot in obj.material_slots if slot.material]
        return bool(materials) and all(m.get("glow") for m in materials)

    body_parts = [obj for obj in copies if not is_glow(obj)]
    glow_groups = {}
    for obj in copies:
        if is_glow(obj):
            glow_groups.setdefault(base_color(obj.material_slots[0].material), []).append(obj)

    if BAKED:
        export_baked(copies, is_glow)
        return

    # Palette: one swatch per body colour
    colors = []
    for obj in body_parts:
        for slot in obj.material_slots:
            color = base_color(slot.material)
            if color not in colors:
                colors.append(color)
    width, height = SWATCH * len(colors), SWATCH
    rows = [bytearray(b"".join(bytes(colors[x // SWATCH]) for x in range(width))) for _ in range(height)]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    palette_path = os.path.join(OUTPUT_DIR, PET_ID + "_palette.png")
    write_png(palette_path, width, height, rows)

    # Point every face at its colour's swatch, before joining loses the materials
    for obj in body_parts:
        mesh = obj.data
        while mesh.uv_layers:
            mesh.uv_layers.remove(mesh.uv_layers[0])
        uv = mesh.uv_layers.new(name="UVMap")
        for polygon in mesh.polygons:
            column = colors.index(base_color(obj.material_slots[polygon.material_index].material))
            for loop in polygon.loop_indices:
                uv.data[loop].uv = ((column + 0.5) / len(colors), 0.5)

    image = bpy.data.images.load(palette_path)
    image.pack()
    palette = bpy.data.materials.new(PET_ID + "Palette")
    palette.use_nodes = True
    texture = palette.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    bsdf = next(n for n in palette.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    palette.node_tree.links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])

    for obj in body_parts:
        obj.data.materials.clear()
        obj.data.materials.append(palette)
    if RIG:
        exported = export_rig_parts(copies, is_glow)
    else:
        exported = [join(body_parts, PET_ID + "_Body")]
        for color, objects in glow_groups.items():
            exported.append(join(objects, PET_ID + "_Glow_%02x%02x%02x" % color))
    for obj in exported:
        for polygon in obj.data.polygons:
            polygon.use_smooth = False

    bpy.ops.object.select_all(action="DESELECT")
    for obj in exported:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUTPUT_DIR, PET_ID + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_scale_options="FBX_SCALE_UNITS",
        path_mode="COPY",
        embed_textures=True,
        mesh_smooth_type="FACE",
    )

    low = [min(v.co[i] for obj in exported for v in obj.data.vertices) for i in range(3)]
    high = [max(v.co[i] for obj in exported for v in obj.data.vertices) for i in range(3)]
    size = [h - l for h, l in zip(high, low)]
    print("EXPORTED", PET_ID, [obj.name for obj in exported],
          "faces", sum(len(obj.data.polygons) for obj in exported),
          "size", [round(s, 2) for s in size], "longest", round(max(size), 2))


main()

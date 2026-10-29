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
# Aura pieces and other non-pet models: --out DIR writes the FBX there instead
# of assets/pets, and skips the pet mesh data (src/shared/PetMeshData)
if "--out" in ARGS:
    OUTPUT_DIR = os.path.join(ROOT, ARGS[ARGS.index("--out") + 1])
WRITE_MESH_DATA = "--out" not in ARGS


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
    if WRITE_MESH_DATA:
        write_luau(exported, colors, [(h + l) / 2 for h, l in zip(high, low)])
    print("EXPORTED", PET_ID, [obj.name for obj in exported],
          "faces", sum(len(obj.data.polygons) for obj in exported),
          "size", [round(s, 2) for s in size], "longest", round(max(size), 2))


def number(value):
    text = "%.3f" % value
    text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def write_luau(exported, colors, center):
    """Writes src/shared/PetMeshData/<PetId>.lua: the same pet as triangles the
    game turns into meshes at runtime (EditableMesh), so no import is needed.
    Positions are in Roblox axes (facing -Z, Y up, +X right), centred on the
    model's bounding box, in studs before the game's pet scale."""
    import bmesh

    def to_roblox(co):
        # Blender: faces -Y, Z up, so its right is -X. Roblox: faces -Z, Y up, right +X.
        x, y, z = co[0] - center[0], co[1] - center[1], co[2] - center[2]
        return (-x, z, y)

    lines = [
        "-- Generated by tools/blender/export_pet.py from tools/blender/%s.blend; do not edit by hand." % PET_ID,
        "-- Positions: flat x, y, z list in studs (Roblox axes, facing -Z). Faces: flat triangle list",
        "-- of 1-based position indices. Body faces take FaceColors[i] from Colors; glow parts are Neon.",
        "return {",
    ]
    for obj in exported:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        uv = bm.loops.layers.uv.get("UVMap")
        index_of, positions, faces, face_colors = {}, [], [], []
        for face in bm.faces:
            ids = []
            for vert in face.verts:
                key = tuple(round(c, 3) for c in to_roblox(vert.co))
                if key not in index_of:
                    index_of[key] = len(index_of) + 1
                    positions.extend(key)
                ids.append(index_of[key])
            faces.extend(ids)
            if uv is not None:
                u = face.loops[0][uv].uv[0]
                face_colors.append(min(len(colors) - 1, int(u * len(colors))) + 1)
        bm.free()

        is_glow = "_Glow_" in obj.name
        lines.append("\t{")
        lines.append('\t\tName = "%s",' % obj.name)
        if is_glow:
            lines.append('\t\tGlow = "%s",' % obj.name.split("_Glow_")[1][:6])
        else:
            lines.append("\t\tColors = { %s }," % ", ".join('"%02x%02x%02x"' % c for c in colors))
            lines.append("\t\tFaceColors = { %s }," % ", ".join(str(c) for c in face_colors))
        lines.append("\t\tPositions = { %s }," % ", ".join(number(v) for v in positions))
        lines.append("\t\tFaces = { %s }," % ", ".join(str(i) for i in faces))
        lines.append("\t},")
    lines.append("}")
    folder = os.path.join(ROOT, "src", "shared", "PetMeshData")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, PET_ID + ".lua"), "w") as file:
        file.write("\n".join(lines) + "\n")


main()

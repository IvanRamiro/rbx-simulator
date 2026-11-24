"""The ornate banner round a nameplate's title (the owner, 2026-11-24: "something like this ... but don't copy that, while keeping the sheen and
typography"; a frame made of rectangles in Studio was rejected as "not premium", and the first render as "cheap"). Rendered art, an original design
built from geometry:

  * a plate of layers: a gold rim, a steel frame, a dark lacquer panel with a gold pinstripe, gold studs;
  * a prow at each end: three nested arrowheads (gold, steel, lacquer) with a jewel on a gold bezel;
  * a gold wing mount, and from it swept blades: bright steel edges, a gunmetal body, a gold inlay along the spine, serrated with barbs;
  * a crown: a faceted crystal with a glowing core on gold prongs, gold arches, steel claws, two side crystals, two beaded halo rings, floating shards,
    and a foot gem under the plate;
  * a four-pointed sparkle at each end of the words, and wisps of light behind the wings.

Two passes, so the game can tint the light to each title's colour and keep the sheen on the letters:
  steel  everything metal and lacquer, lit, on a transparent film (RGBA)
  light  only what glows (crystals, jewels, rings, sparkles, wisps), lit, on a transparent film: title_compose.py turns it into the tintable glow layer

    blender -b --factory-startup --python tools/blender/ui/title_banner.py -- <out folder> [--tier 4] [--length 4.2] [--width 12] [--part full] [--samples 96]

tier 1..4 picks what is drawn (1 plate and sparkles; 2 + prows, wing mounts and one blade a side; 3 + more blades with barbs and a small crown;
4 the full banner); part: full, cap (one end, --side -1 left or 1 right: its plate stub, prow, wing mount and wings), mid (the plate's plain middle strip, for the game to
stretch), crown (the crown and the foot gem alone). The game places the pieces round a title's words, so a long title needs no wider art.
Units: the plate is 0.7 high. The canvas is 12 units wide (2400 px) and 4 high (800 px): 200 px a unit.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."


def opt(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default


TIER = opt("--tier", 4)
LENGTH = opt("--length", 4.2)  # the plate's length between its prows' bases
PART = opt("--part", "full")
SIDE = opt("--side", -1)  # for --part cap: -1 the left end, 1 the right
SAMPLES = opt("--samples", 96)
PLATE_H = 0.7
CANVAS_W, CANVAS_H = opt("--width", 12.0), 4.0  # a long plate needs a wider canvas for the full banner (the game places the pieces, so it has no such limit)
PX = 200

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
objects = {"steel": [], "light": []}


# ---------- materials ----------
def material(name, base, metallic=0.0, roughness=0.3, emission=None, strength=0.0, coat=0.0, transmission=0.0, ior=1.45, specular=None):
    mat = bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*base, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    if specular is not None:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.04
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


GOLD = material("Gold", (1.0, 0.70, 0.24), metallic=1.0, roughness=0.20)
STEEL = material("Steel", (0.55, 0.59, 0.68), metallic=1.0, roughness=0.20)
GUNMETAL = material("Gunmetal", (0.075, 0.085, 0.115), metallic=1.0, roughness=0.32)
# (a dark panel the lettering reads on: little reflection, so the studio lights do not wash it grey; QA checks its brightness)
LACQUER = material("Lacquer", (0.002, 0.003, 0.010), metallic=0.0, roughness=0.30, specular=0.30)
GLASS = material("Glass", (0.80, 0.90, 1.0), roughness=0.03, emission=(0.8, 0.9, 1.0), strength=0.35, transmission=0.92, ior=1.75)
CORE = material("Core", (1, 1, 1), emission=(1, 1, 1), strength=7.0)
GLOW = material("Glow", (0.8, 0.9, 1.0), roughness=0.1, emission=(0.85, 0.93, 1.0), strength=1.1)
GLOW_SOFT = material("GlowSoft", (1, 1, 1), emission=(1, 1, 1), strength=0.4)


def mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return ob


def finish(ob, mats, kind, bevel=0.012, smooth=False):
    """Gives `ob` its materials (one, or a list: a blade takes edge then body), a bevel (it catches the light), and its pass."""
    for mat in (mats if isinstance(mats, (list, tuple)) else [mats]):
        ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
    for poly in ob.data.polygons:
        poly.use_smooth = smooth
    objects[kind].append(ob)
    return ob


# ---------- shapes ----------
def bez(p0, p1, p2, p3, t):
    a = [(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3]
    return Vector((sum(a[i] * p[0] for i, p in enumerate((p0, p1, p2, p3))), sum(a[i] * p[1] for i, p in enumerate((p0, p1, p2, p3))), 0))


def blade(name, ctrl, width, ridge=0.03, n=56, lift=0.0):
    """A two-tone blade along a cubic Bezier: widest near its base, tapering to a point. Bright edges, a body, a raised spine, the same below.
    Per sample: left edge, left shoulder, spine, right shoulder, right edge, then the underside's right shoulder, spine, left shoulder."""
    pts = [bez(*ctrl, i / n) for i in range(n + 1)]
    verts, faces, mats = [], [], []
    rows = []
    for i, p in enumerate(pts):
        t = i / n
        tangent = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        normal = Vector((-tangent.y, tangent.x, 0))
        w = width * (1 - t) ** 0.8 * (1 + 0.45 * math.sin(math.pi * min(t * 1.5, 1.0))) if i < n else 0.0
        r = ridge * (1 - t) ** 0.6
        z = Vector((0, 0, lift))
        base = len(verts)
        verts += [p + normal * w + z, p + normal * w * 0.55 + Vector((0, 0, r * 0.55)) + z, p + Vector((0, 0, r)) + z,
                  p - normal * w * 0.55 + Vector((0, 0, r * 0.55)) + z, p - normal * w + z,
                  p - normal * w * 0.55 - Vector((0, 0, r * 0.55)) + z, p - Vector((0, 0, r)) + z, p + normal * w * 0.55 - Vector((0, 0, r * 0.55)) + z]
        rows.append(base)
    order = [(0, 1, 0), (1, 2, 1), (2, 3, 1), (3, 4, 0), (4, 5, 0), (5, 6, 1), (6, 7, 1), (7, 0, 0)]  # (from, to, 0 edge / 1 body)
    for a_, b_ in zip(rows[:-1], rows[1:]):
        for i0, i1, m in order:
            faces.append((a_ + i0, b_ + i0, b_ + i1, a_ + i1))
            mats.append(m)
    ob = mesh_object(name, verts, faces)
    for poly, m in zip(ob.data.polygons, mats):
        poly.material_index = m
    return ob


def tangent_at(ctrl, t):
    return (bez(*ctrl, min(t + 0.02, 1)) - bez(*ctrl, max(t - 0.02, 0))).normalized()


def gem(name, radius, up, down, sides=8, squash=0.5, loc=(0, 0, 0), spin=0.0, mats=(GLASS,), kind="light"):
    """A faceted gem: a bipyramid with `sides` facets, squashed in depth."""
    verts = [(0, up, 0), (0, -down, 0)]
    for i in range(sides):
        a = 2 * math.pi * i / sides + spin
        verts.append((math.cos(a) * radius, 0, math.sin(a) * radius * squash))
    faces = []
    for i in range(sides):
        j = (i + 1) % sides
        faces += [(0, 2 + i, 2 + j), (1, 2 + j, 2 + i)]
    ob = mesh_object(name, verts, faces)
    ob.location = loc
    finish(ob, list(mats), kind, bevel=0, smooth=False)
    return ob


def jewel(name, radius, up, down, loc, sides=8):
    """A glowing gem: a glass shell with a bright core inside it."""
    gem(name, radius, up, down, sides, loc=loc)
    gem(name + "Core", radius * 0.42, up * 0.5, down * 0.5, sides, loc=(loc[0], loc[1], loc[2] + 0.005), mats=(CORE,))


def slab(name, x0, x1, y0, y1, z0, z1):
    verts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return mesh_object(name, verts, faces)


def prism(name, outline, z0, z1):
    n = len(outline)
    verts = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return mesh_object(name, verts, faces)


def ring(name, major, minor, rot_x, loc, mat, kind="light"):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=120, minor_segments=10)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (math.radians(rot_x), 0, 0)
    ob.location = loc
    ob.data.materials.append(mat)
    objects[kind].append(ob)
    return ob


def barbs(name, ctrl, width, outward, side, count=4, spread=26, kind="steel", mats=(STEEL, GUNMETAL)):
    """Small serrations along a blade's outer edge: short blades leaving it at an angle, getting shorter toward the tip."""
    for index in range(count):
        t = 0.2 + 0.5 * index / max(count - 1, 1)
        p = bez(*ctrl, t)
        tan = tangent_at(ctrl, t)
        angle = math.radians(spread * outward * side)
        d = Vector((tan.x * math.cos(angle) - tan.y * math.sin(angle), tan.x * math.sin(angle) + tan.y * math.cos(angle), 0))
        length = 0.55 * (1 - t) + 0.12
        c = [(p.x, p.y), (p.x + d.x * length * 0.35, p.y + d.y * length * 0.35), (p.x + d.x * length * 0.7 + tan.x * 0.04, p.y + d.y * length * 0.7 + tan.y * 0.04),
             (p.x + d.x * length + tan.x * 0.1, p.y + d.y * length + tan.y * 0.1)]
        finish(blade("%sBarb%d" % (name, index), c, width * 0.42 * (1 - t * 0.5), ridge=0.014, lift=0.004), list(mats), kind, bevel=0.004)


# ---------- the banner ----------
half = LENGTH / 2
H = PLATE_H
want_cap = PART in ("full", "cap")
want_crown = PART in ("full", "crown")

def plate_slab(name, x0, x1, y0, y1, z0, z1, mat, bevel, open_xs):
    """A slab whose bevel skips the edges lying on an open end (x in open_xs): a bevelled cut end would show as a faint line where two pieces meet."""
    ob = slab(name, x0, x1, y0, y1, z0, z1)
    mesh = ob.data
    def on_open_end(edge):  # an edge lying IN an open end's plane (both its ends at that x), not one running from end to end
        xa, xb = (mesh.vertices[v].co.x for v in edge.vertices)
        return abs(xa - xb) < 1e-6 and any(abs(xa - ox) < 1e-6 for ox in open_xs)
    weights = [0.0 if on_open_end(e) else 1.0 for e in mesh.edges]
    attr = mesh.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    attr.data.foreach_set("value", weights)
    ob.data.materials.append(mat)
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    mod.limit_method = "WEIGHT"
    objects["steel"].append(ob)
    return ob


def plate_segment(x0, x1, end_left, end_right, stud_xs):
    """A stretch of the plate between x0 and x1: a gold rim, a steel frame ring, the lacquer panel sunk inside it with a gold pinstripe, gold studs at
    stud_xs. An end is closed (a frame bar, a pinstripe end) only where the flag says; an open end continues into the next piece."""
    inner0, inner1 = x0 + (0.05 if end_left else 0.0), x1 - (0.05 if end_right else 0.0)
    opens = ([] if end_left else [x0]) + ([] if end_right else [x1])
    plate_slab("RimGold", x0, x1, -H / 2 - 0.07, H / 2 + 0.07, -0.07, 0.03, GOLD, 0.025, opens)
    # (the frame is a ring round the panel, four bars: a solid slab taller than the panel hid it from the camera, and the "dark" plate rendered as steel)
    plate_slab("FrameTop", x0, x1, H / 2 - 0.07, H / 2 + 0.02, 0.0, 0.06, STEEL, 0.015, opens)
    plate_slab("FrameBottom", x0, x1, -H / 2 - 0.02, -H / 2 + 0.07, 0.0, 0.06, STEEL, 0.015, opens)
    if end_left:
        plate_slab("FrameLeft", x0, x0 + 0.05, -H / 2 + 0.07, H / 2 - 0.07, 0.0, 0.06, STEEL, 0.01, [])
    if end_right:
        plate_slab("FrameRight", x1 - 0.05, x1, -H / 2 + 0.07, H / 2 - 0.07, 0.0, 0.06, STEEL, 0.01, [])
    plate_slab("Panel", inner0, inner1, -H / 2 + 0.07, H / 2 - 0.07, 0.0, 0.04, LACQUER, 0.004, opens)
    for y_ in (H / 2 - 0.10, -H / 2 + 0.10):
        plate_slab("Pinstripe", x0 + (0.09 if end_left else 0.0), x1 - (0.09 if end_right else 0.0), y_ - 0.011, y_ + 0.011, 0.04, 0.052, GOLD, 0.004, opens)
    if end_left:
        plate_slab("PinstripeEndL", x0 + 0.09 - 0.011, x0 + 0.09 + 0.011, -H / 2 + 0.10, H / 2 - 0.10, 0.04, 0.052, GOLD, 0.004, [])
    if end_right:
        plate_slab("PinstripeEndR", x1 - 0.09 - 0.011, x1 - 0.09 + 0.011, -H / 2 + 0.10, H / 2 - 0.10, 0.04, 0.052, GOLD, 0.004, [])
    for x_ in stud_xs:
        for y_ in (H / 2 + 0.035, -H / 2 - 0.035):
            gem("Stud", 0.026, 0.03, 0.03, sides=8, squash=1.0, loc=(x_, y_, 0.04), mats=(GOLD,), kind="steel")


# studs sit only near a plate's ends (a stretched middle would stretch them): every 0.42 units, the first 0.25 from the end, for 0.9 units
STUD_ZONE = [0.25 + 0.42 * i for i in range(3)]
if PART == "full":
    plate_segment(-half, half, True, True, [-half + z for z in STUD_ZONE] + [half - z for z in STUD_ZONE])
elif PART == "cap":
    # the end's plate stub: 0.8 units of plate with its closed end; the game overlaps the stretched middle strip under it
    if SIDE < 0:
        plate_segment(-half, -half + 0.8, True, False, [-half + z for z in STUD_ZONE])
    else:
        plate_segment(half - 0.8, half, False, True, [half - z for z in STUD_ZONE])
elif PART == "mid":
    plate_segment(-1.0, 1.0, False, False, [])

sides = (-1, 1) if PART == "full" else (SIDE,) if PART == "cap" else ()
for side in sides:
    xe = side * half
    if TIER >= 2:
        # three nested arrowheads: gold, steel, lacquer
        def arrow(extra, tipx):
            return [(xe, H / 2 + extra), (xe + side * 0.18, H / 2 + extra), (xe + side * tipx, 0.0), (xe + side * 0.18, -H / 2 - extra), (xe, -H / 2 - extra)]
        finish(prism("ProwGold%d" % side, arrow(0.10, 0.80), -0.08, 0.03), GOLD, "steel", bevel=0.025)
        finish(prism("ProwSteel%d" % side, arrow(0.05, 0.70), 0.0, 0.06), STEEL, "steel", bevel=0.015)
        finish(prism("ProwFace%d" % side, arrow(-0.03, 0.55), 0.0, 0.08), LACQUER, "steel", bevel=0.01)
        # a jewel on a gold bezel
        ring("Bezel%d" % side, 0.13, 0.03, 0, (xe + side * 0.30, 0, 0.11), GOLD, "steel")
        jewel("ProwJewel%d" % side, 0.10, 0.12, 0.12, (xe + side * 0.30, 0, 0.12), sides=6)
    # a four-pointed sparkle at the inner end of the words
    sx = xe - side * 0.34
    for k, (sw, sh) in enumerate(((0.26, 0.028), (0.028, 0.26))):
        spark = mesh_object("Spark%d_%d" % (side, k), [(sx - sw, 0, 0.11), (sx, sh, 0.11), (sx + sw, 0, 0.11), (sx, -sh, 0.11)], [(0, 1, 2, 3)])
        finish(spark, CORE, "light", bevel=0)
    if TIER < 2:
        continue
    # the wing mount: a gold hexagon with a gunmetal face, hiding where the blades meet
    mx = xe + side * 0.90
    hexagon = [(mx + math.cos(a) * 0.30, math.sin(a) * 0.34) for a in [math.radians(30 + 60 * i) for i in range(6)]]
    finish(prism("MountGold%d" % side, hexagon, -0.06, 0.12), GOLD, "steel", bevel=0.02)
    finish(prism("MountFace%d" % side, [(mx + (x - mx) * 0.62, y * 0.62) for x, y in hexagon], 0.0, 0.16), GUNMETAL, "steel", bevel=0.012)
    # the blades: Bezier points as (distance out, height), width at the base. The upper ones are built, then mirrored below (the art is the same
    # upside down). Each: bright edges, a gunmetal body, a gold inlay along its spine, barbs on its outer edge.
    base = mx + side * 0.18
    k = 0.70
    middle = [(0, 0.0), (1.2 * k, 0.09), (2.4 * k, -0.09), (3.6 * k, 0.0)]
    upper = [
        ([(0, 0.10), (0.9 * k, 0.06), (1.8 * k, 0.50), (2.7 * k, 1.28)], 0.17),
        ([(0, 0.20), (0.7 * k, 0.55), (1.5 * k, 0.95), (2.4 * k, 1.12)], 0.15),
        ([(0, 0.04), (1.3 * k, -0.02), (2.5 * k, 0.16), (3.6 * k, 0.60)], 0.14),
        ([(0, 0.26), (0.2 * k, 0.68), (0.55 * k, 1.0), (0.45 * k, 1.42)], 0.11),
    ]
    count = {2: 1, 3: 3, 4: 4}[TIER]

    def place(c, mirrored):
        return [(base + side * x, -y if mirrored else y) for x, y in c]

    blade_mid = place(middle, False)
    finish(blade("WingMid%d" % side, blade_mid, 0.19), [STEEL, GUNMETAL], "steel", bevel=0.008)
    finish(blade("WingMidInlay%d" % side, blade_mid, 0.045, ridge=0.012, lift=0.03), [GOLD, GOLD], "steel", bevel=0.004)
    for index, (ctrl, width) in enumerate(upper[:count]):
        for mirrored in (False, True):
            c = place(ctrl, mirrored)
            finish(blade("Wing%d_%d_%d" % (side, index, mirrored), c, width), [STEEL, GUNMETAL], "steel", bevel=0.008)
            finish(blade("Inlay%d_%d_%d" % (side, index, mirrored), c, width * 0.26, ridge=0.012, lift=0.03), [GOLD, GOLD], "steel", bevel=0.004)
            if TIER >= 3 and 0 < index < 3:
                barbs("W%d_%d_%d" % (side, index, mirrored), c, width, -1 if mirrored else 1, side, count=4)
    if TIER >= 4:  # wisps of light behind the wings: thin, long, flowing
        for mirrored in (False, True):
            for index, pts in enumerate((((0.2, 0.18), (1.0 * k, 0.95), (2.0 * k, 0.5), (3.1 * k, 1.4)), ((0.3, 0.1), (1.3 * k, 0.5), (2.3 * k, 0.1), (3.4 * k, 0.8)))):
                wisp = blade("Wisp%d_%d_%d" % (side, index, mirrored), place(pts, mirrored), 0.06, ridge=0.0, lift=-0.05)
                finish(wisp, GLOW_SOFT, "light", bevel=0)

if want_crown and TIER >= 3:
    top = H / 2 + 0.07
    # a gold setting on the plate, steel claws round the crystal, gold arches on either side
    finish(prism("CrownBase", [(-0.32, top - 0.03), (0.32, top - 0.03), (0.22, top + 0.13), (-0.22, top + 0.13)], -0.04, 0.12), GOLD, "steel", bevel=0.02)
    finish(blade("Spire", [(0, top + 0.1), (0, top + 0.5), (0, top + 0.85), (0, top + 1.2)], 0.10), [STEEL, GUNMETAL], "steel", bevel=0.008)
    for side in (-1, 1):
        for index, (reach, rise) in enumerate(((0.30, 0.78), (0.46, 0.5))):
            c = [(side * 0.10, top + 0.1), (side * reach, top + 0.16), (side * (reach + 0.12), top + rise * 0.65), (side * reach * 0.78, top + rise + 0.24)]
            finish(blade("Claw%d_%d" % (side, index), c, 0.07 + 0.012 * index), [STEEL, GUNMETAL], "steel", bevel=0.006)
        arch = [(side * 0.18, top + 0.06), (side * 0.75, top + 0.02), (side * 1.15, top + 0.25), (side * 1.3, top + 0.75)]
        finish(blade("Arch%d" % side, arch, 0.10), [GOLD, GOLD], "steel", bevel=0.008)
        finish(blade("ArchInlay%d" % side, arch, 0.03, ridge=0.01, lift=0.025), [STEEL, STEEL], "steel", bevel=0.004)
    jewel("Crystal", 0.25, 0.66, 0.40, (0, top + 0.62, 0.1))
    if TIER >= 4:
        for side in (-1, 1):
            jewel("CrystalSide%d" % side, 0.13, 0.40, 0.26, (side * 0.80, top + 0.30, 0.1), sides=6)
        for index, (major, tilt, minor) in enumerate(((0.82, 76, 0.016), (0.64, 62, 0.012))):
            ring("Halo%d" % index, major, minor, tilt, (0, top + 0.62, 0.12), GLOW)
            for b in range(36):  # beads on the ring
                a = 2 * math.pi * b / 36
                pos = (math.cos(a) * major, top + 0.62 + math.sin(a) * major * math.cos(math.radians(tilt)), 0.12)
                gem("HaloBead", 0.022, 0.03, 0.03, sides=4, squash=1.0, loc=pos, mats=(CORE,))
        shards = ((-1.35, 0.4, 0.07), (1.4, 0.55, 0.06), (-0.95, 1.0, 0.05), (1.0, 1.1, 0.07), (-1.7, 0.75, 0.045), (1.75, 0.3, 0.05), (-0.55, 1.25, 0.035), (0.6, 1.3, 0.04))
        for index, (x_, y_, r_) in enumerate(shards):
            s = gem("Shard%d" % index, r_, r_ * 2.6, r_ * 1.4, sides=4, loc=(x_, top + y_, 0.08), mats=(GLASS,))
            s.rotation_euler = (0, 0, math.radians(18 * (index - 3)))
        # the foot: a small gem in a gold cradle under the plate
        finish(prism("FootBase", [(-0.18, -H / 2 - 0.07), (0.18, -H / 2 - 0.07), (0.10, -H / 2 - 0.22), (-0.10, -H / 2 - 0.22)], -0.04, 0.1), GOLD, "steel", bevel=0.015)
        jewel("Foot", 0.12, 0.14, 0.32, (0, -H / 2 - 0.46, 0.08), sides=6)

# ---------- camera, lights, render ----------
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = CANVAS_W
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, 0, 10)
scene.collection.objects.link(cam)
scene.camera = cam

world = bpy.data.worlds.new("World")
scene.world = world
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.12, 0.15, 0.24, 1)
bg.inputs["Strength"].default_value = 0.35


def area(name, loc, size, power, color=(1, 1, 1), size_y=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.size = size
    data.shape = "RECTANGLE"
    data.size_y = size_y or size
    data.color = color
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    scene.collection.objects.link(ob)
    ob.visible_camera = False
    ob.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


# the lights are far away (6 times the distance, 36 times the power) so the lighting is the same across the banner: the game joins separate pieces, and a
# piece lit differently at its end than the middle strip would show a step at every seam
FAR = 6.0
area("Key", (-3.5 * FAR, 3.4 * FAR, 5.0 * FAR), 3.0 * FAR, 420 * FAR * FAR, (1.0, 0.95, 0.86))
area("Rim", (4.5 * FAR, 2.6 * FAR, 3.0 * FAR), 2.5 * FAR, 380 * FAR * FAR, (0.7, 0.82, 1.0))
area("Fill", (0.0, -3.2 * FAR, 4.0 * FAR), 5.0 * FAR, 70 * FAR * FAR, (0.8, 0.85, 1.0), 1.5 * FAR)
area("Strip", (0.0, 1.2 * FAR, 2.8 * FAR), 7.0 * FAR, 190 * FAR * FAR, (1, 1, 1), 0.3 * FAR)
area("Under", (0.0, -1.5 * FAR, 1.6 * FAR), 5.0 * FAR, 55 * FAR * FAR, (1.0, 0.85, 0.7), 0.6 * FAR)

scene.render.engine = "CYCLES"
cy = scene.cycles
cy.samples = SAMPLES
cy.use_denoising = True
try:
    cy.denoiser = "OPENIMAGEDENOISE"
except TypeError:
    pass
cy.max_bounces = 10
cy.glossy_bounces = 6
cy.transmission_bounces = 8
cy.sample_clamp_indirect = 6
cy.device = "CPU"
scene.render.resolution_x = int(CANVAS_W * PX)
scene.render.resolution_y = int(CANVAS_H * PX)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except TypeError:
    scene.view_settings.view_transform = "Standard"

os.makedirs(OUT, exist_ok=True)
name = "title_tier%d_%s" % (TIER, PART + ("L" if SIDE < 0 else "R") if PART == "cap" else PART)

# the steel pass: lit, transparent; the glowing objects hidden
for ob in objects["light"]:
    ob.hide_render = True
scene.render.film_transparent = True
scene.render.filepath = os.path.join(OUT, name + "_steel.png")
bpy.ops.render.render(write_still=True)

# the light pass: only the glowing objects, lit (a crystal's facets differ), on a transparent film; the steel is a holdout (it hides the light behind it)
for ob in objects["light"]:
    ob.hide_render = False
for ob in objects["steel"]:
    ob.is_holdout = True
scene.render.filepath = os.path.join(OUT, name + "_light.png")
bpy.ops.render.render(write_still=True)
print("wrote", name, "objects", len(bpy.data.objects))

"""jade_lib_view: review renders of Jade Grove's ground and its landmarks (polish pass 2026-11-23). Headless Blender only:

    blender -b --factory-startup -P tools/blender/world/jade/jade_lib_view.py -- <view> [out.png]

The terrain is the island's own ground function sampled every 2 studs (vertex colours by the game's terrain materials), with the library's pieces standing where the plan puts them
(paint colours from jade_lib_looks) and flat water. Views are named in VIEWS. Evidence goes to renders/jade_grove_library/polish/, never committed.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import jade_lib_blender as B  # noqa: E402
import jade_lib_forest as F  # noqa: E402
import jade_lib_island as I  # noqa: E402
import jade_lib_sites as S  # noqa: E402

REPO = B.REPO
OUT = os.path.join(REPO, "renders", "jade_grove_library", "polish")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

GROUND = {"LeafyGrass": (86, 140, 66), "Mud": (112, 88, 62), "Sandstone": (150, 146, 128)}


def terrain_object(step=2.0, box=None, lift=0.0):
    x0, x1, z0, z1 = box if box else (-I.HALF, I.HALF, -I.HALF, I.HALF)
    nx, nz = int((x1 - x0) / step) + 1, int((z1 - z0) / step) + 1
    bm = bmesh.new()
    grid = {}
    cols = {}
    for j in range(nz):
        for i in range(nx):
            x, z = x0 + i * step, z0 + j * step
            h, m = I.height(x, z)
            if h is None:
                continue
            grid[(i, j)] = bm.verts.new(B.rb(x, h + lift, z))
            cols[(i, j)] = (m, h)
    for j in range(nz - 1):
        for i in range(nx - 1):
            q = [grid.get((i, j)), grid.get((i + 1, j)), grid.get((i + 1, j + 1)), grid.get((i, j + 1))]
            if all(q):
                try:
                    bm.faces.new(q[::-1])
                except ValueError:
                    pass
    bm.normal_update()
    me = bpy.data.meshes.new("terrain")
    bm.to_mesh(me)
    bm.free()
    colors = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    # colours per vertex (the mesh keeps the vertex order of creation)
    order = sorted(grid.keys(), key=lambda k: (k[1], k[0]))
    vi = 0
    for k in order:
        m, h = cols[k]
        r, g, b = GROUND[m]
        # a little height tint: the highest ground paler, the low ground deeper
        t = max(-1.0, min(1.0, h / 30.0))
        k2 = 1.0 + 0.18 * t
        colors.data[vi].color = (B.lin(min(255, r * k2)), B.lin(min(255, g * k2)), B.lin(min(255, b * k2)), 1.0)
        vi += 1
    for p in me.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.new("terrain_mat")
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    me.materials.append(mat)
    o = bpy.data.objects.new("terrain", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def water_disc(x, z, y, r, name="water"):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=64, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = water_material()
    me.materials.append(m)
    o.location = B.rb(x, y, z)
    return o


def water_ribbon(pts, width, name="stream", lift=0.0):
    bm = bmesh.new()
    left, right = [], []
    for k, p in enumerate(pts):
        a = pts[max(0, k - 1)]
        b = pts[min(len(pts) - 1, k + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        y = p[2] + lift
        left.append(bm.verts.new(B.rb(p[0] + nx * width / 2, y, p[1] + nz * width / 2)))
        right.append(bm.verts.new(B.rb(p[0] - nx * width / 2, y, p[1] - nz * width / 2)))
    for k in range(len(pts) - 1):
        try:
            bm.faces.new([left[k], left[k + 1], right[k + 1], right[k]])
        except ValueError:
            pass
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(water_material())
    return o


def water_material():
    m = bpy.data.materials.get("jl_water_view")
    if m:
        return m
    m = bpy.data.materials.new("jl_water_view")
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (B.lin(70), B.lin(170), B.lin(160), 1.0)
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["Alpha"].default_value = 0.75
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def falls_sheet(lip, drop, width, name="falls"):
    """A flat pale-blue sheet where a waterfall hangs (a stand-in for the engine's beams): top at the lip, `drop` studs tall, `width` across, facing the viewer along the falls' direction."""
    bm = bmesh.new()
    d = I.DIR_F
    nx, nz = -d[1], d[0]
    out = 1.8
    ax, az = lip[0] + d[0] * out, lip[2] + d[1] * out
    pts = [(ax - nx * width / 2, lip[1], az - nz * width / 2), (ax + nx * width / 2, lip[1], az + nz * width / 2),
           (ax + nx * width * 0.55, lip[1] - drop, az + nz * width * 0.55 + 0.0), (ax - nx * width * 0.55, lip[1] - drop, az - nz * width * 0.55)]
    vs = [bm.verts.new(B.rb(*p)) for p in pts]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.get("jl_falls_view") or bpy.data.materials.new("jl_falls_view")
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.86, 0.95, 0.97, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Alpha"].default_value = 0.72
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    me.materials.append(m)
    return o


def build_scene(pieces=True, box=None, only=None):
    B.clear_scene()
    pl = F.build()
    I.USE_PADS[0] = True
    coll = B.new_collection("view")
    terrain_object(2.0, box)
    items = []
    if pieces:
        P = S.pieces()
        for piece, lst in pl.place.items():
            if only and not any(piece.startswith(o) for o in only):
                continue
            for e in lst:
                if box and not (box[0] - 10 <= e["x"] <= box[1] + 10 and box[2] - 10 <= e["z"] <= box[3] + 10):
                    continue
                items.append((P[piece], (e["x"], e["y"], e["z"]), e["yaw"], e["scale"]))
        objs = B.place_scene(items, coll)
        B.set_mode(objs, "paint")
    for d in pl.water["discs"]:
        water_disc(d["x"], d["z"], d["y"], d["r"], d["name"])
    for s in pl.water["streams"]:
        water_ribbon(s["pts"], s["width"], s["name"])
    for f in ([] if "nofalls" in ARGS else pl.falls):
        if f["name"] in ("HighFalls", "RibbonFall") or f["name"].startswith("Cascade"):
            sc = f.get("scale", 1.0) * f.get("curtains", 1)
            falls_sheet(f["lip"], f["drop"], 2.4 * sc if f["name"] in ("HighFalls", "RibbonFall") else 2.4, f["name"])
    return pl


VIEWS = {
    # name: (camera in island-local studs (x, y, z), target, lens, res)
    "aerial_nw": ((60.0, 150.0, 120.0), (-120.0, 8.0, -90.0), 38.0, (1400, 900)),
    "aerial_se": ((-250.0, 160.0, -250.0), (-100.0, 10.0, -60.0), 38.0, (1400, 900)),
    "aerial_all": ((330.0, 360.0, 330.0), (-20.0, 0.0, 0.0), 40.0, (1400, 1000)),
    "falls_front": ((-60.0, 12.0, -78.0), (-96.0, 14.0, -112.0), 28.0, (1200, 1200)),
    "falls_pond": ((-64.0, 6.0, -92.0), (-96.0, 16.0, -112.0), 22.0, (1200, 1200)),
    "cave": ((-87.6, 3.4, -107.3), (-96.0, 4.0, -111.4), 34.0, (1200, 900)),
    "ribbon_front": ((-100.0, 8.0, -60.0), (-120.0, 11.0, -90.0), 30.0, (1200, 1200)),
    "ramp_walk": ((-150.0, 4.0, -52.0), (-172.0, 14.0, -90.0), 34.0, (1200, 900)),
    "gorge": ((-118.0, 8.0, -34.0), (-142.0, -8.0, -48.0), 34.0, (1200, 900)),
    "ridge": ((-80.0, 10.0, -150.0), (-92.0, 8.0, -190.0), 36.0, (1200, 900)),
    "plateau_top": ((-150.0, 36.0, -118.0), (-118.0, 28.0, -128.0), 32.0, (1200, 900)),
}


def render(view, path, pl=None):
    cam_pos, target, lens, res = VIEWS[view]
    scene = B.setup_render(res, 24)
    B.set_world((0.62, 0.72, 0.84), 1.0)
    B.set_sun(3.6, (-52, 0, 40))
    cam = B.add_camera("cam_" + view, B.rb(*cam_pos), B.rb(*target), lens)
    B.shoot(cam, path)
    print("wrote", path)


def main():
    view = ARGS[0] if ARGS else "aerial_all"
    path = ARGS[1] if len(ARGS) > 1 else os.path.join(OUT, "view_%s.png" % view)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    nopieces = "terrain" in ARGS
    only = [a[5:] for a in ARGS if a.startswith("only=")] or None
    box = None
    if view.startswith(("aerial_nw", "aerial_se")) or view in ("falls_front", "falls_pond", "cave", "ribbon_front", "ramp_walk", "gorge", "ridge", "plateau_top"):
        box = (-236, 20, -236, 60)
    build_scene(not nopieces, box, only)
    render(view, path)


if __name__ == "__main__":
    main()

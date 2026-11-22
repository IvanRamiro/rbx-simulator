"""jade_lib_blender: the Blender side of Jade Grove's library (headless only, `blender -b --factory-startup --python ...`; never the open window).

Turns Pieces into Blender objects (named <Piece>__<Suffix>, authored in studs, Roblox (x, y, z) -> Blender (x, -z, y)), one box-projected UV
chart set per mesh (the set exists so the mesh imports; no texture is ever applied), clay / paint / black-silhouette materials, the six-view
review sheets, the QA call (blender-asset-qa, profile roblox), the FBX export (a 1-stud anchor cube JL_Anchor at the origin, machine paths
scrubbed to /Users/user) and the re-import check.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_looks as LK  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QA_DIR = os.environ.get("JL_QA_DIR")     # the folder of the asset-QA skill's qa_check.py (see the library's vault note)
KIT_DIR = os.environ.get("JL_KIT_DIR")   # the folder of the environment-kits skill's kit_check.py
TILE = 8.0

ROUGH = {"Wood": 0.8, "WoodPlanks": 0.75, "Rock": 0.9, "Cobblestone": 0.85, "LeafyGrass": 0.85, "SmoothPlastic": 0.42, "Glass": 0.05, "Neon": 0.2,
         "Fabric": 0.95, "Mud": 0.95, "Limestone": 0.8}


def rb(x, y, z):
    return Vector((x, -z, y))


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def preview_material(suffix, glow=True):
    key = "jl_" + suffix + ("" if glow else "_off")
    m = bpy.data.materials.get(key)
    if m:
        return m
    mat, (r, g, b), extra = LK.LOOKS[suffix]
    m = bpy.data.materials.new(key)
    col = (lin(r), lin(g), lin(b), 1.0)
    m.diffuse_color = col
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = ROUGH.get(mat, 0.7)
    if mat == "Neon" and glow:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = 5.0
    if "Transparency" in extra:
        bsdf.inputs["Alpha"].default_value = 1.0 - extra["Transparency"]
        m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else None
    return m


def clay_material():
    m = bpy.data.materials.get("jl_clay")
    if not m:
        m = bpy.data.materials.new("jl_clay")
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (0.64, 0.62, 0.58, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.88
    return m


def black_material():
    m = bpy.data.materials.get("jl_black")
    if not m:
        m = bpy.data.materials.new("jl_black")
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        nt.links.new(em.outputs[0], out.inputs[0])
    return m


def uv_charts(bm):
    """Box-projected UVs, one tile per TILE studs: faces grouped into charts by dominant axis and adjacency, each chart at most a tile across,
    every UV inside 0-1 (overlaps are allowed and harmless: nothing is textured)."""
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    axis = {f.index: max(range(3), key=lambda i: abs(f.normal[i])) for f in bm.faces}
    done = set()
    for f0 in bm.faces:
        if f0.index in done:
            continue
        ax = axis[f0.index]
        a, b = [i for i in range(3) if i != ax]
        chart, stack = [], [f0]
        lo = [min(v.co[a] for v in f0.verts), min(v.co[b] for v in f0.verts)]
        hi = [max(v.co[a] for v in f0.verts), max(v.co[b] for v in f0.verts)]
        done.add(f0.index)
        while stack:
            f = stack.pop()
            chart.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index in done or axis[g.index] != ax:
                        continue
                    nlo = [min(lo[0], min(v.co[a] for v in g.verts)), min(lo[1], min(v.co[b] for v in g.verts))]
                    nhi = [max(hi[0], max(v.co[a] for v in g.verts)), max(hi[1], max(v.co[b] for v in g.verts))]
                    if nhi[0] - nlo[0] > TILE or nhi[1] - nlo[1] > TILE:
                        continue
                    lo, hi = nlo, nhi
                    done.add(g.index)
                    stack.append(g)
        scale = max(TILE, hi[0] - lo[0], hi[1] - lo[1])
        for f in chart:
            for l in f.loops:
                l[uv].uv = ((l.vert.co[a] - lo[0]) / scale, (l.vert.co[b] - lo[1]) / scale)


def mesh_from_geo(name, geo, suffix):
    bm = bmesh.new()
    vs = [bm.verts.new(rb(*p)) for p in geo.v]
    for f in geo.f:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.normal_update()
    uv_charts(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(LK.SMOOTH.get(suffix, LK.DEFAULT_SMOOTH)))
    me.materials.append(preview_material(suffix))
    return me


def piece_objects(piece, coll, name=None):
    """One object per material, named <name>__<suffix>, at the origin."""
    out = []
    for suffix, geo in sorted(piece.g.items()):
        if not geo.f:
            continue
        me = mesh_from_geo("%s__%s" % (name or piece.name, suffix), geo, suffix)
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        out.append(o)
    return out


def place_scene(items, coll, name_prefix="s"):
    """items: (piece, (x, y, z), yaw, scale) in studs; returns the objects (meshes shared by copies)."""
    meshes, objs = {}, []
    for piece, pos, yaw, sc in items:
        for suffix, geo in sorted(piece.g.items()):
            if not geo.f:
                continue
            key = (piece.name, suffix)
            if key not in meshes:
                meshes[key] = mesh_from_geo("%s__%s" % key, geo, suffix)
            o = bpy.data.objects.new("%s__%s" % key, meshes[key])
            o.location = rb(*pos)
            o.rotation_euler = (0.0, 0.0, yaw)
            if sc != 1.0:
                o.scale = (sc,) * 3
            coll.objects.link(o)
            objs.append(o)
    return objs


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def new_collection(name="jl"):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def set_mode(objs, mode):
    """clay (one neutral material), paint (the preview colours) or black (a flat black silhouette)."""
    for o in objs:
        suffix = o.name.partition("__")[2].split(".")[0]
        o.data.materials.clear()
        if mode == "clay":
            o.data.materials.append(clay_material())
        elif mode == "black":
            o.data.materials.append(black_material())
        else:
            o.data.materials.append(preview_material(suffix))


# ----------------------------------------------------------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------------------------------------------------------
def setup_render(res=(960, 720), samples=20):
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    try:
        scene.eevee.taa_render_samples = samples
    except AttributeError:
        pass
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    return scene


def set_world(color=(0.55, 0.62, 0.7), strength=1.0):
    scene = bpy.context.scene
    world = bpy.data.worlds.get("JLWorld") or bpy.data.worlds.new("JLWorld")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (color[0], color[1], color[2], 1)
    bg.inputs["Strength"].default_value = strength


def set_sun(energy=3.2, rot=(-48, 0, 30), color=(1.0, 0.97, 0.92)):
    sun = bpy.data.objects.get("JLSun")
    if not sun:
        sun = bpy.data.objects.new("JLSun", bpy.data.lights.new("JLSun", "SUN"))
        bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = energy
    sun.data.color = color
    sun.data.angle = math.radians(6)
    sun.rotation_euler = tuple(math.radians(a) for a in rot)


def add_camera(name, loc, target, lens=50.0, ortho=None):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    cam.data.clip_end = 4000
    cam.data.clip_start = 0.5
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def shoot(cam, path):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def ground_disc(radius, mode="paint"):
    """A flat ground under the piece (y = 0), so burying and floating are visible."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=48, radius=radius)
    me = bpy.data.meshes.new("jl_ground")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("jl_ground", me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.get("jl_groundmat")
    if not m:
        m = bpy.data.materials.new("jl_groundmat")
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (lin(64) * 0.9, lin(96) * 0.9, lin(58) * 0.9, 1.0) if mode == "paint" else (0.36, 0.36, 0.36, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
    me.materials.append(m)
    o.location = (0, 0, -0.04)
    return o


def bbox_roblox(objs):
    pts = []
    for o in objs:
        pts += [o.matrix_world @ v.co for v in o.data.vertices]
    rbp = [Vector((p.x, p.z, -p.y)) for p in pts]
    lo = [min(p[i] for p in rbp) for i in range(3)]
    hi = [max(p[i] for p in rbp) for i in range(3)]
    return [round(x, 3) for x in lo], [round(x, 3) for x in hi]


VIEWS = ["front", "back", "left", "right", "top", "q3"]


def six_views(objs, out_prefix, res=(420, 420), mode="paint", ground=True, samples=16):
    """Renders the six standard views (orthographic front, back, left, right, top, and a three-quarter perspective) of what is in the scene
    and stitches them into out_prefix + '_<mode>.png' (3 x 2)."""
    lo, hi = bbox_roblox(objs)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    dx, dy, dz = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
    big = max(dx, dy, dz, 1.0)
    setup_render(res, samples)
    set_world((0.56, 0.62, 0.70) if mode == "paint" else (0.5, 0.5, 0.5), 1.0)
    set_sun()
    gr = None
    if ground:
        gr = ground_disc(max(dx, dz) * 0.8 + 2.0, mode)
    D = big * 3.0
    sc = big * 1.14
    cams = {
        "front": (rb(c[0], c[1], c[2] - D), rb(*c), sc),
        "back": (rb(c[0], c[1], c[2] + D), rb(*c), sc),
        "left": (rb(c[0] - D, c[1], c[2]), rb(*c), sc),
        "right": (rb(c[0] + D, c[1], c[2]), rb(*c), sc),
        "top": (rb(c[0], c[1] + D, c[2]), rb(*c), max(dx, dz, 1.0) * 1.14),
    }
    paths = []
    for name in VIEWS:
        if name == "q3":
            cam = add_camera("cam_q3", rb(c[0] + 0.55 * D, c[1] + 0.32 * D, c[2] - 0.62 * D), rb(*c), lens=44.0)
        else:
            loc, tgt, scale = cams[name]
            cam = add_camera("cam_" + name, loc, tgt, ortho=scale)
        p = out_prefix + "_v_%s.png" % name
        shoot(cam, p)
        paths.append(p)
    stitch(paths, 3, out_prefix + "_%s.png" % mode)
    for p in paths:
        os.remove(p)
    if gr:
        bpy.data.objects.remove(gr, do_unlink=True)


def contact_view(objs, path, res=(360, 360), mode="paint", view="q3", ground=True):
    """One view of what is in the scene (for a family's contact sheet)."""
    lo, hi = bbox_roblox(objs)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    dx, dy, dz = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
    big = max(dx, dy, dz, 1.0)
    setup_render(res, 12)
    set_world((0.56, 0.62, 0.70) if mode == "paint" else (0.5, 0.5, 0.5), 1.0)
    set_sun()
    gr = ground_disc(max(dx, dz) * 0.7 + 2.0, mode) if ground else None
    D = big * 3.0
    if view == "q3":
        cam = add_camera("cam_c", rb(c[0] + 0.55 * D, c[1] + 0.32 * D, c[2] - 0.62 * D), rb(*c), lens=44.0)
    else:
        cam = add_camera("cam_c", rb(c[0], c[1], c[2] - D), rb(*c), ortho=big * 1.14)
    shoot(cam, path)
    if gr:
        bpy.data.objects.remove(gr, do_unlink=True)


def load_pixels(path):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def save_pixels(px, path):
    h, w = px.shape[0], px.shape[1]
    img = bpy.data.images.new("out", w, h, alpha=False)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def stitch(paths, cols, out, pad=4):
    import numpy as np
    imgs = [load_pixels(p) for p in paths]
    h, w = imgs[0].shape[0], imgs[0].shape[1]
    rows = (len(imgs) + cols - 1) // cols
    sheet = np.ones((rows * h + (rows - 1) * pad, cols * w + (cols - 1) * pad, 4), np.float32) * 0.04
    for i, im in enumerate(imgs):
        r, k = divmod(i, cols)
        y0 = (rows - 1 - r) * (h + pad)     # (image rows run bottom to top)
        sheet[y0:y0 + h, k * (w + pad):k * (w + pad) + w] = im
    save_pixels(sheet, out)


def silhouette_image(objs_by_name, path, size=160, view="front", pad=0.06):
    """A black silhouette on white, orthographic, framed on its own height (so the proportions read at thumbnail size)."""
    objs = [o for lst in objs_by_name for o in lst]
    lo, hi = bbox_roblox(objs)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    big = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], 1.0) * (1 + pad * 2)
    setup_render((size, size), 6)
    set_world((1.0, 1.0, 1.0), 1.0)
    set_sun(0.0)
    set_mode(objs, "black")
    D = big * 3
    if view == "front":
        cam = add_camera("cam_sil", rb(c[0], c[1], c[2] - D), rb(*c), ortho=big)
    else:
        cam = add_camera("cam_sil", rb(c[0] + D, c[1], c[2]), rb(*c), ortho=big)
    shoot(cam, path)


# ----------------------------------------------------------------------------------------------------------------------
# QA and export
# ----------------------------------------------------------------------------------------------------------------------
def qa_module():
    if not QA_DIR:
        raise SystemExit("JL_QA_DIR must name the folder of the asset QA's qa_check.py")
    sys.path.insert(0, QA_DIR)
    import qa_check
    return qa_check


ACCEPT = (
    ("UV overlap", "no texture is ever applied: the UV set exists so the mesh imports; charts are box projections that overlap by design"),
    ("open boundary", "hidden undersides and buried feet (a closed bottom would only add hidden triangles)"),
    ("non-manifold", "shells that meet along an edge or a corner (a root on a trunk)"),
    ("duplicate verts", "welded within a shell; two shells that touch share a position"),
    ("hidden back-to-back", "faces of two solids resting on each other (a few per stack)"),
    ("fully enclosed", "an inner part (a glow core, a seed in its husk) sits inside another shell on purpose"),
    ("lowest point", "pieces stand slightly in the ground on purpose (buried feet)"),
)


def accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def run_qa(pieces, names=None):
    """qa_check (profile roblox, eps 0.001, tol 0.002) on every piece; returns (all pass, lines)."""
    qa = qa_module()
    clear_scene()
    coll = new_collection("qa")
    lines = []
    all_pass = True
    result = {}
    for piece in pieces:
        objs = piece_objects(piece, coll)
        if not objs:
            continue
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
        t = {o.name: tris(o) for o in objs}
        all_pass &= r["pass"]
        lines.append("%s: %s, %d triangles, %d errors" % (piece.name, "PASS" if r["pass"] else "FAIL", sum(t.values()), len(r["errors"])))
        for k, v in sorted(t.items()):
            lines.append("    %-44s %6d" % (k, v))
        for e in r["errors"]:
            lines.append("    ERROR %s" % e)
        seen = set()
        for w in r["warnings"]:
            why = accepted(w)
            if why:
                if why not in seen:
                    lines.append("    accepted warning(s): %s" % why)
                    seen.add(why)
            else:
                lines.append("    WARNING %s" % w)
        result[piece.name] = (r["pass"], sum(t.values()))
        for o in objs:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    return all_pass, lines, result


def scrub(path):
    """Machine paths in an exported file read /Users/user (same length: binary-safe); stale bytes after a shorter path are zeroed."""
    b = bytearray(open(path, "rb").read())
    home = os.path.expanduser("~").encode()
    if len(home) != len(b"/Users/user"):
        raise SystemExit("scrub: the home path is not the same length as /Users/user: fix by hand")
    i = b.find(home)
    while i != -1:
        b[i:i + len(home)] = b"/Users/user"
        j = i + len(home)
        while j < len(b) and b[j] != 0:
            j += 1
        k = j
        while k < len(b) and k - j < 1024 and b[k:k + 16] != b"\x00" * 16:
            b[k] = 0
            k += 1
        i = b.find(home, i + 1)
    open(path, "wb").write(bytes(b))
    return b.find(home) == -1


def export_fbx(objs, fbx_path, anchor="JL_Anchor"):
    """One FBX (Roblox-ready axes; 1 Blender unit = 1 stud) with a 1-stud anchor cube at the origin, exactly as worldlib.export_batch does it."""
    os.makedirs(os.path.dirname(fbx_path), exist_ok=True)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(anchor)
    bm.to_mesh(me)
    bm.free()
    a = bpy.data.objects.new(anchor, me)
    bpy.context.scene.collection.objects.link(a)
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objs) + [a]:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE")
    bpy.data.objects.remove(a, do_unlink=True)
    bpy.data.meshes.remove(me)


def verify_fbx(path, expect):
    """Imports the FBX again and compares every object's triangle count and box (Roblox axes) with what was exported."""
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if "JL_Anchor" not in got:
        problems.append("no JL_Anchor")
    for name, (tr, lo, hi) in expect.items():
        o = got.get(name)
        if o is None:
            problems.append("missing " + name)
            continue
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        t = sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
        l2, h2 = bbox_roblox([o])
        if t != tr:
            problems.append("%s tris %d != %d" % (name, t, tr))
        if max(abs(a - b) for a, b in zip(lo + hi, l2 + h2)) > 0.02:
            problems.append("%s box %s %s != %s %s" % (name, l2, h2, lo, hi))
    extra = sorted(set(got) - set(expect) - {"JL_Anchor"})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems

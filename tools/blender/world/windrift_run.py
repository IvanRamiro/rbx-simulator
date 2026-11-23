"""Headless runner for Windrift Hold's architecture (windrift_arch.py, windrift.py). Never the open Blender window.

    HQ_QA_SCRIPT=<blender-asset-qa>/scripts/qa_check.py \
    blender -b --factory-startup -P tools/blender/world/windrift_run.py -- <stage> [piece names]
      sides       six-side clay and paint renders of the named pieces (default: every building) (renders/windrift/six_<piece>_<clay|paint>.png)
      look        the compound on its terrain: aerial, from the plaza's stair, per area (renders/windrift/look_*.png)
      silhouette  black silhouettes of every building in a row (renders/windrift/silhouettes_buildings.png)
      qa          asset QA (profile roblox) on every piece, written to renders/windrift/qa.txt
      export      FBX files into assets/world/MurimCrossing/Windrift/ (Windrift_Buildings, _Courts, _Props), pieces.json and the placements Lua
Scratch output goes to renders/windrift/ (local, never committed). HQ_QA_SCRIPT names the blender-asset-qa qa_check.py.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402

import hq_blender as B  # noqa: E402
import worldlib as W  # noqa: E402
import windrift as D  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "look"
NAMES = ARGS[1:]
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "windrift")
OUT = os.path.join(REPO, "assets", "world", "MurimCrossing", "Windrift")
os.makedirs(RENDERS, exist_ok=True)

# the preview colours of the architecture's suffixes (what the game's Roblox material will read as): colour, roughness, metallic, emission, alpha
for suffix, look in D.ARCH_LOOKS.items():
    c = look["Color"]
    mat = look["Material"]
    metal = 0.55 if mat in ("CorrodedMetal", "Metal") else 0.0
    rough = {"CorrodedMetal": 0.55, "Metal": 0.35, "Neon": 0.2, "Glass": 0.05, "Fabric": 0.85, "Slate": 0.8, "Wood": 0.8, "WoodPlanks": 0.75}.get(mat, 0.7)
    emit = ((c[0], c[1], c[2]), 5.0) if mat == "Neon" else None
    B.PREVIEW[suffix] = (tuple(c), rough, metal, emit, 0.5 if mat == "Glass" else None)


def veg_previews(looks):
    for suffix, l in looks.items():
        key = "v_" + suffix
        if key not in B.PREVIEW:
            B.PREVIEW[key] = (tuple(l["Color"]), 0.7, 1.0 if l["Material"] == "Metal" else 0.0, None, (1.0 - l.get("Transparency", 0.0)) if "Transparency" in l else None)


def veg_material(suffix):
    return B.preview_material("v_" + suffix)


# ---------------------------------------------------------------------------------------------------------------------------------
# the scene
# ---------------------------------------------------------------------------------------------------------------------------------
def terrain_object(coll, x0=-92.0, x1=92.0, z0=-52.0, z1=90.0):
    """The ground of the region as a smooth mesh (the island's 4-stud cells, joined at their centres), coloured by surface material, in the pad frame."""
    import murim_layout as M
    import windrift_plan as PL
    g = PL.grid()
    ox, oz, n = g["ox"], g["oz"], g["n"]
    pts = {}
    for j in range(n):
        for i in range(n):
            k = j * n + i
            h = g["H"][k]
            if h is None:
                continue
            wx, wz = ox + (i + 0.5) * M.CELL, oz + (j + 0.5) * M.CELL
            lx, lz = M.to_local(wx, wz)
            px, pz = D.T.to_pad(lx, lz)
            if x0 <= px <= x1 and z0 <= pz <= z1:
                pts[(i, j)] = (px, h - D.Y0, pz, M.MATERIALS[g["M"][k] - 1])
    bm = bmesh.new()
    vid = {}
    layer = bm.loops.layers.color.new("Col")
    for key, (px, y, pz, mat) in pts.items():
        vid[key] = bm.verts.new(W.rb(px, y, pz))
    for (i, j) in pts:
        quad = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if all(q in vid for q in quad):
            try:
                f = bm.faces.new([vid[q] for q in quad])
            except ValueError:
                continue
            col = PL.COLOURS.get(pts[(i, j)][3], (120, 120, 126))
            for l in f.loops:
                l[layer] = (B.lin(col[0]), B.lin(col[1]), B.lin(col[2]), 1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("terrain")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.new("terrain_m")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n_ for n_ in nt.nodes if n_.type == "BSDF_PRINCIPLED")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    me.materials.append(mat)
    o = bpy.data.objects.new("terrain", me)
    coll.objects.link(o)
    return o


def build_scene(mode="paint", with_terrain=True, with_veg=True, plan=None):
    B.clear_scene()
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    P = plan or D.build_all()
    coll = bpy.data.collections.new("Windrift")
    bpy.context.scene.collection.children.link(coll)
    objs = []
    meshes = {}
    for p in P.placements:
        piece = P.pieces[p["piece"]]
        for suffix, geo in sorted(piece.g.items()):
            key = (p["piece"], suffix)
            if key not in meshes:
                meshes[key] = B.mesh_from_geo("%s__%s" % key, geo, suffix)
            o = bpy.data.objects.new("%s__%s" % key, meshes[key])
            o.location = W.rb(p["x"], p["y"], p["z"])
            o.rotation_euler = (0.0, 0.0, p["yaw"])
            sx = p.get("scale_x", 1.0) * p.get("scale", 1.0)
            if abs(sx - 1.0) > 1e-9 or p.get("scale", 1.0) != 1.0:
                o.scale = (sx, p.get("scale", 1.0), p.get("scale", 1.0))
            coll.objects.link(o)
            objs.append(o)
    if with_veg:
        import windrift_veg as V
        vd = V.build_all()
        veg_previews(vd["looks"])
        for v in P.veg:
            piece = vd["pieces"][v["piece"]]
            for suffix, geo in sorted(piece.g.items()):
                key = (v["piece"], suffix)
                if key not in meshes:
                    me = B.mesh_from_geo("%s__%s" % key, geo, "Stone")
                    me.materials.clear()
                    me.materials.append(veg_material(suffix))
                    meshes[key] = me
                o = bpy.data.objects.new("VEG_%s__%s" % key, meshes[key])
                o.location = W.rb(v["x"], v["y"], v["z"])
                o.rotation_euler = (0.0, 0.0, v["yaw"])
                if v.get("scale", 1.0) != 1.0:
                    o.scale = (v["scale"],) * 3
                coll.objects.link(o)
                objs.append(o)
    if with_terrain:
        terrain_object(coll)
    if mode == "clay":
        for o in objs:
            o.data.materials.clear()
            o.data.materials.append(B.clay_material())
    return P, objs


def shoot_set(views, prefix, res=(1400, 900), world=(0.55, 0.62, 0.72), sun_az=-35, lens=40):
    B.setup_render(res, samples=20)
    B.set_world(world, 1.0)
    B.set_sun(3.4, (-50, 0, sun_az), (1, 0.97, 0.92))
    for name, (loc, tgt, ln) in views.items():
        cam = B.add_camera("cam_" + name, B.rbv(*loc), B.rbv(*tgt), lens=ln or lens)
        B.shoot(cam, os.path.join(RENDERS, "%s_%s.png" % (prefix, name)))


def look():
    P, objs = build_scene()
    views = D.LOOK_VIEWS
    if NAMES:
        views = {k: v for k, v in views.items() if k in NAMES}
    shoot_set(views, "look")
    print("looked")


SIDE_CAMS = {"front": (0.0, 0.16, -1.0), "back": (0.0, 0.16, 1.0), "left": (-1.0, 0.16, 0.0), "right": (1.0, 0.16, 0.0), "q3": (-0.75, 0.55, -0.9), "top": (0.0, 1.0, -0.01)}


def sides():
    P = D.build_all()
    names = NAMES or [n for n, p in sorted(P.pieces.items()) if D.family_of(n) == "Buildings"]
    for mode in ("clay", "paint"):
        for name in names:
            B.clear_scene()
            for me in list(bpy.data.meshes):
                bpy.data.meshes.remove(me)
            coll = bpy.data.collections.new("c")
            bpy.context.scene.collection.children.link(coll)
            piece = P.pieces[name]
            objs = B.piece_objects(name, piece, coll)
            B.set_material_mode(objs, "clay" if mode == "clay" else "paint", True)
            lo, hi = piece.bounds()
            cx, cy, cz = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
            span = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
            B.setup_render((640, 520), samples=12)
            B.set_world((0.55, 0.62, 0.72) if mode == "paint" else (0.5, 0.5, 0.5), 1.0)
            B.set_sun(3.4, (-52, 0, -30), (1, 0.97, 0.92))
            shots = []
            for tag, (dx, dy, dz) in SIDE_CAMS.items():
                if tag == "top":
                    cam = bpy.data.objects.new("cam_top", bpy.data.cameras.new("cam_top"))
                    bpy.context.scene.collection.objects.link(cam)
                    cam.data.type = "ORTHO"
                    cam.data.ortho_scale = span * 1.15
                    cam.data.clip_end = 2000
                    cam.location = (cx, -cz, hi[1] + span * 2)
                    cam.rotation_euler = (0.0, 0.0, 0.0)
                else:
                    cam = B.add_camera("cam_" + tag, B.rbv(cx + dx * span * 1.35, cy + dy * span * 1.0, cz + dz * span * 1.35), B.rbv(cx, cy, cz), lens=50)
                path = os.path.join(RENDERS, "tmp_%s_%s.png" % (name, tag))
                B.shoot(cam, path)
                shots.append(path)
            sheet(shots, os.path.join(RENDERS, "six_%s_%s.png" % (name, mode)))
    print("six sides done")


def load_pixels(path):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def save_pixels(px, path):
    img = bpy.data.images.new("out", px.shape[1], px.shape[0], alpha=False)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def sheet(paths, out, cols=3):
    import numpy as np
    tiles = [load_pixels(p) for p in paths]
    h, w = tiles[0].shape[0], tiles[0].shape[1]
    rows = []
    for r in range(0, len(tiles), cols):
        row = tiles[r:r + cols]
        while len(row) < cols:
            row.append(np.ones_like(tiles[0]) * 0.05)
        rows.append(np.concatenate(row, axis=1))
    save_pixels(np.concatenate(rows, axis=0), out)
    for p in paths:
        os.remove(p)


def silhouette():
    """Every building's black silhouette from the front in a row (no two the same)."""
    import numpy as np
    B.setup_render((300, 300), samples=6)
    B.set_world((1.0, 1.0, 1.0), 1.0)
    B.set_sun(0.0, (-50, 0, 0))
    P = D.build_all()
    names = NAMES or [n for n, p in sorted(P.pieces.items()) if D.family_of(n) == "Buildings"]
    shots = []
    for name in names:
        B.clear_scene()
        for me in list(bpy.data.meshes):
            bpy.data.meshes.remove(me)
        coll = bpy.data.collections.new("c")
        bpy.context.scene.collection.children.link(coll)
        piece = P.pieces[name]
        B.piece_objects(name, piece, coll)
        B.set_material_mode(bpy.data.objects[:], "black")
        lo, hi = piece.bounds()
        cx, cy, cz = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        bpy.context.scene.collection.objects.link(cam)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.08
        cam.data.clip_end = 3000
        cam.location = (cx, 500.0 - cz, cy)
        cam.rotation_euler = (math.pi / 2, 0.0, math.pi)
        path = os.path.join(RENDERS, "tmp_sil_%s.png" % name)
        B.shoot(cam, path)
        shots.append(path)
    tiles = [load_pixels(p) for p in shots]
    out = np.concatenate(tiles, axis=1)
    save_pixels(np.ascontiguousarray(out), os.path.join(RENDERS, "silhouettes_buildings.png"))
    for p in shots:
        os.remove(p)
    print("silhouettes")


# ---------------------------------------------------------------------------------------------------------------------------------
# QA and export
# ---------------------------------------------------------------------------------------------------------------------------------
ACCEPT = (
    ("UV overlap", "no texture is ever applied: the UV set exists so the mesh imports, charts are box projections that overlap by design"),
    ("open boundary", "hidden undersides, contact faces, buried feet and single-sided flat rings (a closed bottom would only add hidden triangles)"),
    ("non-manifold", "two solids that meet along an edge or a corner (a beam on a post)"),
    ("duplicate verts", "the corners of two solids that touch share a position"),
    ("hidden back-to-back", "faces of two solids resting on each other (a few per stack)"),
    ("fully enclosed", "a small solid sits inside another on purpose"),
    ("lowest point", "the pieces' feet are buried below the floor on purpose (they stand in the ground)"),
)


def accepted(w):
    for key, why in ACCEPT:
        if key in w:
            return why
    return None


def run_qa(names=None):
    P = D.build_all()
    B.clear_scene()
    coll = bpy.data.collections.new("qa")
    bpy.context.scene.collection.children.link(coll)
    qa = B.qa_module()
    lines = ["Windrift Hold architecture: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece", ""]
    all_pass = True
    for name in sorted(P.pieces):
        if names and name not in names:
            continue
        objs = piece_objects(name, P.pieces[name], coll)
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
        t = {o.name: B.tris(o) for o in objs}
        all_pass &= r["pass"]
        lines.append("%s: %s, %d triangles, %d errors" % (name, "PASS" if r["pass"] else "FAIL", sum(t.values()), len(r["errors"])))
        for k, v in sorted(t.items()):
            lines.append("    %-46s %6d" % (k, v))
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
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    lines.insert(1, "Overall: %s" % ("PASS (zero errors on every piece)" if all_pass else "FAIL"))
    with open(os.path.join(RENDERS, "qa.txt" if not names else "qa_partial.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if l.endswith("errors") or l.startswith("Overall") or "ERROR" in l or "WARNING" in l))
    return all_pass


def prune_zfight(objs, eps=0.00105, passes=10):
    """The asset QA fails two same-facing faces that overlap in one plane; a few survive the kit's own resolver (shallow-angle crossings of two roof courses). This replays the
    QA's test on the piece's meshes and deletes the later face of each pair (a face hidden inside the roof, a hair from the one that stays): nothing visible changes. Returns
    how many faces were deleted."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    total = 0
    for _ in range(passes):
        verts, tris, meta = [], [], []
        for oi, o in enumerate(objs):
            me = o.data
            bm_t = bmesh.new()
            bm_t.from_mesh(me)
            bm_t.faces.ensure_lookup_table()
            res = bmesh.ops.triangulate(bm_t, faces=bm_t.faces[:])
            fmap = res["face_map"]
            base = len(verts)
            verts += [o.matrix_world @ v.co for v in bm_t.verts]
            bm_t.verts.ensure_lookup_table()
            for f in bm_t.faces:
                orig = fmap.get(f)
                pidx = orig.index if orig is not None else f.index
                tris.append(tuple(base + v.index for v in f.verts))
                meta.append((oi, pidx, f.normal.copy()))
            bm_t.free()
        if not tris:
            return total
        bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
        sets = [set(t) for t in tris]
        kill = set()
        for ti, t in enumerate(tris):
            a, b, c = (verts[i] for i in t)
            n = meta[ti][2]
            if n.length < 0.5:
                continue
            cen = (a + b + c) / 3
            for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
                for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                    if tj is None or tj == ti or (sets[ti] & sets[tj]):
                        continue
                    n2 = meta[tj][2]
                    if n.dot(n2) < 0.999:
                        continue
                    a2, b2, c2 = (verts[i] for i in tris[tj])
                    q = p - n2 * n2.dot(p - a2)
                    v0, v1, v2 = c2 - a2, b2 - a2, q - a2
                    d00, d01, d02, d11, d12 = v0.dot(v0), v0.dot(v1), v0.dot(v2), v1.dot(v1), v1.dot(v2)
                    den = d00 * d11 - d01 * d01
                    if abs(den) < 1e-14:
                        continue
                    uu, vv = (d11 * d02 - d01 * d12) / den, (d00 * d12 - d01 * d02) / den
                    if uu >= -1e-6 and vv >= -1e-6 and uu + vv <= 1 + 1e-6:
                        late = max((meta[ti][0], meta[ti][1]), (meta[tj][0], meta[tj][1]))
                        kill.add(late)
        if not kill:
            return total
        by_obj = {}
        for (oi, pi) in kill:
            by_obj.setdefault(oi, set()).add(pi)
        for oi, polys in by_obj.items():
            bm = bmesh.new()
            bm.from_mesh(objs[oi].data)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in polys], context="FACES_ONLY")
            bm.to_mesh(objs[oi].data)
            bm.free()
            total += len(polys)
    return total


def piece_objects(name, piece, coll):
    """The piece's objects (one per material) with the QA's z-fighting pairs pruned: what QA, the FBX and the triangle counts all see."""
    objs = B.piece_objects(name, piece, coll)
    prune_zfight(objs)
    return objs


def verify_fbx(path, expect):
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if "WR_Anchor" not in got:
        problems.append("no WR_Anchor")
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
        l2, h2 = B.bbox_roblox([o])
        if t != tr:
            problems.append("%s tris %d != %d" % (name, t, tr))
        if max(abs(a - b) for a, b in zip(lo + hi, l2 + h2)) > 0.02:
            problems.append("%s box %s %s != %s %s" % (name, l2, h2, lo, hi))
    extra = sorted(set(got) - set(expect) - {"WR_Anchor"})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems


def export():
    if not run_qa():
        raise SystemExit("QA failed: nothing exported")
    P = D.build_all()
    os.makedirs(OUT, exist_ok=True)
    report = {}
    for fam, fname in D.FILES.items():
        B.clear_scene()
        coll = bpy.data.collections.new("exp")
        bpy.context.scene.collection.children.link(coll)
        objs_all, expect = [], {}
        for key in sorted(P.pieces):
            if D.family_of(key) != fam:
                continue
            objs = piece_objects(key, P.pieces[key], coll)
            for o in objs:
                lo, hi = B.bbox_roblox([o])
                expect[o.name] = (B.tris(o), lo, hi)
            objs_all += objs
        path = os.path.join(OUT, fname + ".fbx")
        W.export_batch(objs_all, path, image=None, anchor_name="WR_Anchor")
        B.scrub(path)
        problems = verify_fbx(path, expect)
        report[fam] = {"fbx": os.path.relpath(path, REPO), "objects": sorted(expect), "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok"}
        print("EXPORTED", path, len(expect), "objects", "verify:", problems or "ok")
    boxes = {}
    for n, piece in P.pieces.items():
        lo, hi = piece.bounds()
        boxes[n] = {"min": [round(v, 2) for v in lo], "max": [round(v, 2) for v in hi], "tris": piece.tris(), "materials": piece.stats()}
    with open(os.path.join(OUT, "pieces.json"), "w") as f:
        json.dump({"frame": "pad frame: origin at the Unorthodox pad's centre (+0.5 up); every piece at its own origin, front -Z; anchor WR_Anchor", "files": report, "pieces": boxes}, f, indent=1)
    import windrift_lua as L
    L.write(P)
    print("EXPORT_DONE")


def main():
    {"look": look, "sides": sides, "silhouette": silhouette, "qa": lambda: run_qa(NAMES or None), "export": export}[STAGE]()


if __name__ == "__main__":
    main()

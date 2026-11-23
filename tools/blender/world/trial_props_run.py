"""Headless runner for the faction trials' three hero props (trial_props.py). Never the open Blender window.

    HQ_QA_SCRIPT=<blender-asset-qa>/scripts/qa_check.py \
    blender -b --factory-startup -P tools/blender/world/trial_props_run.py -- <stage> [piece names]
      look     angle sheets (and wireframes) of each piece: renders/trial/look_<piece>.png and wire_<piece>.png
      sheet    the contact sheet of the three side by side at one scale beside a 5-stud R15 silhouette: renders/trial/trial_props_sheet.png
      qa       asset QA (profile roblox) on every piece, written to renders/trial/qa.txt
      measure  the numbers: sizes, triangles, materials, the gate's clear opening measured from the mesh, the dummy's centre of mass, the pivots
      export   assets/world/MurimCrossing/Trial/Trial_Props.fbx and pieces.json, then the re-import check
Scratch output goes to renders/trial/ (local, never committed). It reuses nightfall_run's QA helpers (prune_zfight, the accepted-warning table, the image sheet) by import.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import hq_blender as B  # noqa: E402
import worldlib as W  # noqa: E402
import nightfall_run as NR  # noqa: E402
import trial_props as T  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "look"
NAMES = ARGS[1:] or sorted(T.PIECES)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RENDERS = os.path.join(REPO, "renders", "trial")
OUT = os.path.join(REPO, "assets", "world", "MurimCrossing", "Trial")
FBX = os.path.join(OUT, "Trial_Props.fbx")
ANCHOR = "TR_Anchor"
os.makedirs(RENDERS, exist_ok=True)

# per-piece preview materials: B.PREVIEW key "<Piece>_<suffix>" = (colour, roughness, metallic, emission, alpha)
for _piece, _looks in T.PREVIEW.items():
    for _suffix, (_c, _rough, _metal, _emit) in _looks.items():
        B.PREVIEW["%s_%s" % (_piece, _suffix)] = (_c, _rough, _metal, _emit, None)


def build(names=None):
    """The finished pieces {name: WP}."""
    out = {}
    for n in names or sorted(T.PIECES):
        p = T.PIECES[n]()
        p.finish()
        ground(p)
        out[n] = p
    return out


def ground(piece):
    """Lowers or lifts the finished piece so its lowest point is exactly y = 0 (the kit's z-fight nudges move a bottom face a few thousandths): the origin is on the ground."""
    lo = piece.bounds()[0][1]
    if abs(lo) > 1e-9:
        for g in piece.g.values():
            g.v = [(x, y - lo, z) for (x, y, z) in g.v]


def piece_objects(name, piece, coll):
    """One object per material named Trial_Props_<Piece>__<Suffix>, the QA's z-fighting pairs pruned: what QA, the FBX and the counts all see."""
    objs = []
    for suffix, geo in sorted(piece.g.items()):
        if not geo.f:
            continue
        me = B.mesh_from_geo("%s__%s" % (T.key(name), suffix), geo, "%s_%s" % (name, suffix))
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        objs.append(o)
    NR.prune_zfight(objs)
    return objs


def reset():
    B.clear_scene()
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    coll = bpy.data.collections.new("trial")
    bpy.context.scene.collection.children.link(coll)
    return coll


# ---------------------------------------------------------------------------------------------------------------------------------
# looks
# ---------------------------------------------------------------------------------------------------------------------------------
VIEWS = {"front": (0.0, 0.12, -1.0), "q3": (-0.8, 0.35, -0.9), "q3b": (0.85, 0.3, -0.8), "side": (-1.0, 0.12, 0.0), "back": (0.0, 0.15, 1.0), "high": (-0.4, 0.95, -0.7)}


def camera_for(piece, tag, d, fill=1.15, lens=50):
    lo, hi = piece.bounds()
    cx, cy, cz = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    span = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    dist = span * 1.55 * fill
    v = Vector(d).normalized()
    return B.add_camera("cam_" + tag, B.rbv(cx + v.x * dist, cy + v.y * dist, cz + v.z * dist), B.rbv(cx, cy, cz), lens=lens)


def sheet_keep(paths, out, cols=3):
    """NR.sheet without deleting the tiles (so a single view can be looked at on its own)."""
    import numpy as np
    tiles = [NR.load_pixels(p) for p in paths]
    rows = []
    for r in range(0, len(tiles), cols):
        row = tiles[r:r + cols]
        while len(row) < cols:
            row.append(np.ones_like(tiles[0]) * 0.05)
        rows.append(np.concatenate(row, axis=1))
    NR.save_pixels(np.concatenate(rows, axis=0), out)


def look(names=None, wire=True):
    P = build(names or NAMES)
    for name, piece in P.items():
        coll = reset()
        objs = piece_objects(name, piece, coll)
        B.setup_render((640, 640), samples=16)
        B.set_world((0.62, 0.66, 0.74), 1.0)
        B.set_sun(3.6, (-52, 0, -30), (1, 0.97, 0.92))
        shots = []
        for tag, d in VIEWS.items():
            cam = camera_for(piece, tag, d)
            path = os.path.join(RENDERS, "tmp_%s_%s.png" % (name, tag))
            B.shoot(cam, path)
            shots.append(path)
        sheet_keep(shots, os.path.join(RENDERS, "look_%s.png" % name))
        if wire:
            # the topology: a light solid with its edges drawn over it by a wireframe modifier (slot 1 = the dark edge material)
            thick = {"TrialGate": 0.045, "TrialDummy": 0.012, "TrialToken": 0.008}[name]
            for o in objs:
                o.data.materials.clear()
                o.data.materials.append(B.clay_material())
                o.data.materials.append(B.black_material())
                md = o.modifiers.new("wire", "WIREFRAME")
                md.thickness = thick
                md.use_replace = False
                md.material_offset = 1
            B.set_world((0.95, 0.95, 0.95), 1.0)
            wire_shots = []
            for tag in ("front", "q3"):
                cam = camera_for(piece, "w" + tag, VIEWS[tag], lens=60)
                path = os.path.join(RENDERS, "tmpw_%s_%s.png" % (name, tag))
                B.shoot(cam, path)
                wire_shots.append(path)
            sheet_keep(wire_shots, os.path.join(RENDERS, "wire_%s.png" % name), cols=2)
    print("looked", list(P))


# ---------------------------------------------------------------------------------------------------------------------------------
# close-ups (eye, target in studs) for the details: judged by eye
# ---------------------------------------------------------------------------------------------------------------------------------
CLOSE = {
    "TrialGate": {"pillar_top": ((-4.0, 12.6, -8.0), (-9.0, 12.8, 0.0)), "tower": ((-3.0, 16.5, -9.0), (0.0, 15.6, 0.0)), "low": ((0.0, 3.0, -28.0), (0.0, 9.0, 0.0)),
                  "side": ((-24.0, 10.0, 0.0), (0.0, 10.0, 0.0)), "wing": ((10.0, 16.0, -7.0), (9.0, 14.9, 0.0)), "under": ((0.0, 4.0, -9.0), (0.0, 13.0, 0.0))},
    "TrialDummy": {"head": ((0.0, 6.2, -4.6), (0.0, 5.6, 0.0)), "chest": ((-1.5, 3.9, -5.0), (0.0, 3.5, 0.0)), "base": ((-3.5, 2.2, -4.5), (0.0, 0.5, 0.0)),
                   "arm": ((3.6, 4.4, -3.4), (1.6, 3.9, 0.0)), "back": ((2.0, 3.8, 5.5), (0.0, 3.5, 0.0)), "eye": ((0.0, 1.6, -9.0), (0.0, 3.2, 0.0))},
    "TrialToken": {"disc": ((-0.8, 2.3, -4.2), (0.0, 1.95, 0.0)), "stand": ((-3.6, 2.5, -4.0), (0.0, 1.8, 0.0)), "far15": ((0.0, 3.0, -15.0), (0.0, 1.8, 0.0)),
                   "side": ((-5.0, 1.8, -0.8), (0.0, 1.7, 0.0)), "top": ((0.0, 7.0, -3.0), (0.0, 1.0, 0.0)), "back": ((2.0, 2.4, 4.0), (0.0, 1.8, 0.0))},
}


def closeups(names=None):
    P = build(names or NAMES)
    for name, piece in P.items():
        coll = reset()
        piece_objects(name, piece, coll)
        B.setup_render((640, 640), samples=16)
        B.set_world((0.62, 0.66, 0.74), 1.0)
        B.set_sun(3.6, (-52, 0, -30), (1, 0.97, 0.92))
        shots = []
        for tag, (eye, tgt) in CLOSE[name].items():
            cam = B.add_camera("cam_" + tag, B.rbv(*eye), B.rbv(*tgt), lens=50)
            path = os.path.join(RENDERS, "tmpc_%s_%s.png" % (name, tag))
            B.shoot(cam, path)
            shots.append(path)
        sheet_keep(shots, os.path.join(RENDERS, "close_%s.png" % name))
    print("closeups", list(P))


# ---------------------------------------------------------------------------------------------------------------------------------
# the contact sheet: the three props at one scale beside a 5-stud R15 silhouette (orthographic, the front and a three-quarter view)
# ---------------------------------------------------------------------------------------------------------------------------------
R15_PARTS = [(-0.5, 0.5, 0.0, 2.0, -0.5, 0.5), (0.0, 1.0, 0.0, 2.0, -0.5, 0.5),                  # legs (x0, x1, y0, y1, z0, z1)
             (-1.0, 1.0, 2.0, 4.0, -0.5, 0.5),                                                    # torso
             (-2.0, -1.0, 2.0, 4.0, -0.5, 0.5), (1.0, 2.0, 2.0, 4.0, -0.5, 0.5),                   # arms
             (-0.6, 0.6, 4.0, 5.0, -0.6, 0.6)]                                                    # head (the whole figure is 5 studs tall)
SHEET_ORDER = [("R15", 0.0), ("TrialToken", -5.6), ("TrialDummy", -11.4), ("TrialGate", -27.0)]    # +x is to the left in a front view, so these read left to right


def add_box(coll, name, x0, x1, y0, y1, z0, z1, mat, dx=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.scale = (x1 - x0, z1 - z0, y1 - y0)
    o.location = B.rbv(dx + (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    me.materials.append(mat)
    coll.objects.link(o)
    return o


def contact_sheet():
    import numpy as np
    P = build()
    coll = reset()
    grey = bpy.data.materials.new("sheet_silhouette")
    grey.use_nodes = True
    bsdf = next(n for n in grey.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.07, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    ground = bpy.data.materials.new("sheet_ground")
    ground.use_nodes = True
    gb = next(n for n in ground.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gb.inputs["Base Color"].default_value = (0.42, 0.40, 0.36, 1.0)
    gb.inputs["Roughness"].default_value = 0.95
    add_box(coll, "ground", -52.0, 8.0, -0.5, 0.0, -14.0, 14.0, ground)
    for (name, dx) in SHEET_ORDER:
        if name == "R15":
            for i, (x0, x1, y0, y1, z0, z1) in enumerate(R15_PARTS):
                add_box(coll, "R15_%d" % i, x0, x1, y0, y1, z0, z1, grey, dx=dx)
            continue
        for o in piece_objects(name, P[name], coll):
            o.location = B.rbv(dx, 0.0, 0.0)
    B.setup_render((1920, 820), samples=24)
    B.set_world((0.66, 0.70, 0.78), 1.0)
    B.set_sun(3.4, (-48, 0, -28), (1, 0.97, 0.92))
    shots = []
    centre = (-19.0, 8.6, 0.0)
    for tag, az in (("three_quarter", 38.0), ("front", 0.0)):
        a = math.radians(az)
        eye = (centre[0] - 300.0 * math.sin(a), centre[1] + 40.0, centre[2] - 300.0 * math.cos(a))
        cam = B.add_camera("cam_" + tag, B.rbv(*eye), B.rbv(*centre), ortho=(46.0 if tag == "front" else 50.0))
        cam.data.clip_end = 4000
        path = os.path.join(RENDERS, "tmps_%s.png" % tag)
        B.shoot(cam, path)
        shots.append(path)
    tiles = [NR.load_pixels(p) for p in shots]
    out = np.concatenate(tiles, axis=0)               # the first tile is the bottom row of the image
    NR.save_pixels(np.ascontiguousarray(out), os.path.join(RENDERS, "trial_props_sheet.png"))
    for p in shots:
        os.remove(p)
    print("sheet written")


# ---------------------------------------------------------------------------------------------------------------------------------
# sizes and measurements
# ---------------------------------------------------------------------------------------------------------------------------------
def size_of(piece):
    lo, hi = piece.bounds()
    return [round(hi[i] - lo[i], 3) for i in range(3)], [round(v, 3) for v in lo], [round(v, 3) for v in hi]


def gate_opening(piece):
    """The clear opening measured from the finished mesh: the widest x interval around x = 0 that no triangle crosses, at every height from the ground to the lintel (sampled
    every 0.02), and the lowest height at which a triangle enters the central 16-stud width. Triangles are tested by their x-extent over each height slice, any z."""
    tris = []
    for g in piece.g.values():
        for f in g.f:
            for j in range(1, len(f) - 1):
                tris.append((g.v[f[0]], g.v[f[j]], g.v[f[j + 1]]))
    # for each height y, the x intervals the surface occupies (the triangle's intersection with the plane y)
    def spans_at(y):
        out = []
        for (a, b, c) in tris:
            ys = (a[1], b[1], c[1])
            if min(ys) > y or max(ys) < y:
                continue
            pts = []
            for p, q in ((a, b), (b, c), (c, a)):
                if (p[1] - y) * (q[1] - y) <= 0 and abs(p[1] - q[1]) > 1e-12:
                    t = (y - p[1]) / (q[1] - p[1])
                    pts.append(p[0] + (q[0] - p[0]) * t)
                elif abs(p[1] - y) < 1e-12 and abs(q[1] - y) < 1e-12:
                    pts += [p[0], q[0]]
            if pts:
                out.append((min(pts), max(pts)))
        return out
    worst_w, worst_y, h_clear = 1e9, 0.0, None
    y = 0.0
    top_free = None
    while y <= 13.6:
        sp = spans_at(y)
        left = max([hi for (lo, hi) in sp if hi <= 0.0] + [-1e9]) if sp else -1e9
        right = min([lo for (lo, hi) in sp if lo >= 0.0] + [1e9]) if sp else 1e9
        # an interval that straddles zero blocks the middle completely
        blocked = any(lo < 0.0 < hi for (lo, hi) in sp)
        w = 0.0 if blocked else (right - left)
        if y < 12.0 and w < worst_w:
            worst_w, worst_y = w, y
        if h_clear is None and (blocked or (right < 8.0) or (left > -8.0)) and y > 0.2:
            h_clear = y
        y = round(y + 0.02, 3)
    return {"min_clear_width_0_to_12": round(worst_w, 3), "at_height": worst_y, "lowest_intrusion_into_central_16": h_clear}


def measure():
    P = build()
    lines = []
    for name, piece in P.items():
        sz, lo, hi = size_of(piece)
        vol, com = T.vol_centroid(piece)
        lines.append("%s: size %s (x, y, z) min %s max %s, %d triangles, %d materials %s" % (name, sz, lo, hi, piece.tris(), len(piece.g), piece.stats()))
        lines.append("    volume centroid %s (overlaps counted twice), lowest y %.4f" % ([round(c, 3) for c in com], lo[1]))
    g = gate_opening(P["TrialGate"]) if "TrialGate" in P else None
    lines.append("gate clear opening: %s" % g)
    text = "\n".join(lines)
    print(text)
    open(os.path.join(RENDERS, "measure.txt"), "w").write(text + "\n")



# ---------------------------------------------------------------------------------------------------------------------------------
# QA (blender-asset-qa, profile roblox), exactly as nightfall_run does it
# ---------------------------------------------------------------------------------------------------------------------------------
def run_qa(names=None):
    P = build(names)
    coll = reset()
    qa = B.qa_module()
    lines = ["Trial props: asset QA (blender-asset-qa qa_check.py, profile roblox, eps 0.001, tol 0.002) per piece", ""]
    all_pass = True
    for name in sorted(P):
        objs = piece_objects(name, P[name], coll)
        r = qa.run(objects=[o.name for o in objs], profile="roblox", eps=0.001, tol=0.002)
        t = {o.name: B.tris(o) for o in objs}
        all_pass &= r["pass"]
        lines.append("%s: %s, %d triangles, %d materials, %d errors" % (name, "PASS" if r["pass"] else "FAIL", sum(t.values()), len(t), len(r["errors"])))
        for k, v in sorted(t.items()):
            lines.append("    %-46s %6d" % (k, v))
        for e in r["errors"]:
            lines.append("    ERROR %s" % e)
        seen = set()
        for w in r["warnings"]:
            why = NR.accepted(w)
            if why:
                if why not in seen:
                    lines.append("    accepted warning(s): %s" % why)
                    seen.add(why)
            else:
                lines.append("    WARNING %s" % w)
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    lines.insert(1, "Overall: %s" % ("PASS (zero errors on every piece)" if all_pass else "FAIL"))
    text = "\n".join(lines) + "\n"
    open(os.path.join(RENDERS, "qa.txt"), "w").write(text)
    print(text)
    return all_pass


# ---------------------------------------------------------------------------------------------------------------------------------
# export: the FBX, the re-import check, pieces.json
# ---------------------------------------------------------------------------------------------------------------------------------
def verify_fbx(path, expect):
    """Re-imports the FBX into an empty scene: every object's triangles and its bounding box (in studs, Roblox axes) must equal what was exported, the anchor must be there and nothing
    else may be. Returns a list of problems (empty = ok)."""
    B.clear_scene()
    bpy.ops.import_scene.fbx(filepath=path)
    got = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    problems = []
    if ANCHOR not in got:
        problems.append("no " + ANCHOR)
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
    extra = sorted(set(got) - set(expect) - {ANCHOR})
    if extra:
        problems.append("unexpected objects %s" % extra)
    return problems, got


def union_centroid(piece, step=0.1):
    """The centre of mass of the piece as ONE solid of uniform density (overlaps counted once): a grid of points, each inside if it lies inside any closed solid of the piece
    (parity of a ray against that solid alone). Returns (volume, (x, y, z))."""
    from mathutils.bvhtree import BVHTree
    solids = []
    for g in piece.g.values():
        parent = list(range(len(g.v)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for f in g.f:
            r = find(f[0])
            for i in f[1:]:
                parent[find(i)] = r
        comps = {}
        for f in g.f:
            comps.setdefault(find(f[0]), []).append(f)
        for faces in comps.values():
            idx = sorted({i for f in faces for i in f})
            remap = {o: n for n, o in enumerate(idx)}
            vs = [Vector(g.v[i]) for i in idx]
            tris = []
            for f in faces:
                for j in range(1, len(f) - 1):
                    tris.append((remap[f[0]], remap[f[j]], remap[f[j + 1]]))
            lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
            hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
            solids.append((lo, hi, BVHTree.FromPolygons(vs, tris, epsilon=0.0)))
    lo, hi = piece.bounds()
    n = 0
    sx = sy = sz = 0.0
    d = Vector((0.137, 0.271, 0.953)).normalized()
    x = lo[0] + step / 2
    while x < hi[0]:
        y = lo[1] + step / 2
        while y < hi[1]:
            z = lo[2] + step / 2
            while z < hi[2]:
                p = Vector((x, y, z))
                for (a, b, tree) in solids:
                    if a.x <= x <= b.x and a.y <= y <= b.y and a.z <= z <= b.z:
                        hits, q = 0, p.copy()
                        for _ in range(48):
                            loc, _, _, _ = tree.ray_cast(q, d)
                            if loc is None:
                                break
                            hits += 1
                            q = loc + d * 1e-5
                        if hits % 2 == 1:
                            n += 1
                            sx += x
                            sy += y
                            sz += z
                            break
                z += step
            y += step
        x += step
    if not n:
        return 0.0, (0.0, 0.0, 0.0)
    return n * step ** 3, (sx / n, sy / n, sz / n)


def export():
    if not run_qa():
        raise SystemExit("QA failed: nothing exported")
    P = build()
    os.makedirs(OUT, exist_ok=True)
    coll = reset()
    objs_all, expect = [], {}
    for name in sorted(P):
        for o in piece_objects(name, P[name], coll):
            lo, hi = B.bbox_roblox([o])
            expect[o.name] = (B.tris(o), lo, hi)
            objs_all.append(o)
    W.export_batch(objs_all, FBX, image=None, anchor_name=ANCHOR)
    B.scrub(FBX)
    problems, got = verify_fbx(FBX, expect)
    print("EXPORTED", FBX, len(expect), "objects", "verify:", problems or "ok")
    pieces = {}
    for name, piece in P.items():
        sz, lo, hi = size_of(piece)
        entry = {"min": [round(v, 2) for v in lo], "max": [round(v, 2) for v in hi], "size": [round(v, 2) for v in sz], "tris": piece.tris(), "materials": piece.stats(),
                 "front": "-Z", "pivot": "origin on the ground at the middle of the footprint (the lowest point is y = 0)"}
        entry["marks"] = {k: [round(c, 3) for c in v] for k, v in sorted(piece.marks.items())}
        pieces[T.key(name)] = entry
    pieces[T.key("TrialGate")]["number_plate"] = {"centre_front": list(T.GATE_PLATE["centre_front"]), "centre_back": list(T.GATE_PLATE["centre_back"]), "size": list(T.GATE_PLATE["size"]),
                                                   "normal_front": list(T.GATE_PLATE["normal_front"]), "normal_back": list(T.GATE_PLATE["normal_back"]), "note": T.GATE_PLATE["note"]}
    pieces[T.key("TrialGate")]["clear_opening"] = gate_opening(P["TrialGate"])
    vol, com = union_centroid(P["TrialDummy"])
    pieces[T.key("TrialDummy")]["centre_of_mass"] = {"uniform_density_overlaps_once": [round(c, 3) for c in com], "volume": round(vol, 2),
                                                     "bounding_box_centre_y": round(sum(size_of(P["TrialDummy"])[1][1:2] + size_of(P["TrialDummy"])[2][1:2]) / 2, 3)}
    report = {"Props": {"fbx": os.path.relpath(FBX, REPO), "objects": sorted(expect) + [ANCHOR], "tris": sum(v[0] for v in expect.values()), "verify": problems or "ok"}}
    doc = {"frame": "authoring frame: x right, y up, z back, the front is -Z; every piece at its own origin (on the ground, at the middle of its footprint); anchor " + ANCHOR +
                    " (a 1-stud cube at the origin). One MeshPart per material per piece, named Trial_Props_<Piece>__<Suffix>",
           "looks": T.LOOKS, "files": report, "pieces": pieces}
    with open(os.path.join(OUT, "pieces.json"), "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("EXPORT_DONE", "COM", com)
    if problems:
        raise SystemExit("verify failed: %s" % problems)


def main():
    {"look": lambda: look(), "close": lambda: closeups(), "sheet": contact_sheet, "measure": measure, "qa": lambda: run_qa(), "export": export}.get(STAGE, lambda: print("unknown stage", STAGE))()


if __name__ == "__main__":
    main()

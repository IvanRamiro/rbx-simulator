"""The Spirit Crane (Rare, Spiritual energy; Spirit Breeze Egg), rigged: the existing crane, exactly as it was modelled and baked, given a skeleton.

The crane's look is kept as it is (owner, 2026-11-16: "I also preferred the old crane design, you just need to redo it to apply the rigs and
animation"): the same game pieces, the same UVs, the same baked colour and normal maps, the same glow pieces. Only how it moves changes. It was a
jointed pet (eight rigid parts turning on pivots); it becomes a skinned one, as the pipeline's recent pets are: one mesh on a skeleton, with
    - a neck of four bones and the head, so its S-curve bends smoothly instead of hinging at one point;
    - each wing a chain of four bones, swinging out from the folded pose to a spread wing that beats and flexes at the wrist;
    - each leg a hip, a knee, a heel that bends backward as a bird's does, and a foot that stays flat on the ground as it walks;
    - a tail of three bones for the streamers, a chest that breathes, a crest that flutters.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/spirit_crane.py -- [rig|all] [review dir]

rig: build and check the skeleton, the weights, every pose and the walk, with renders (nothing is written into the project). all: also the .blend
and the FBX (into PET_KIT_TRIAL when it is set, else tools/blender/pets/SpiritBreezeEgg/ and assets/pets/SpiritBreezeEgg/). It reads the crane's
own .blend (tools/blender/pets/SpiritBreezeEgg/SpiritCrane.blend): its game pieces (collection SpiritCrane) are copied, never changed, so the file
can be rebuilt any number of times; the bake sources (SpiritCrane_Src, SpiritCrane_Hi) stay in it untouched. The colour and normal maps are the
ones already in assets/pets/SpiritBreezeEgg/ (byte for byte the maps the old FBX carried). Faces -Y, Z up, 1 unit = 1 metre, +X is its left.

What touches what (unchanged from the jointed crane): the neck's collar sits in the breast and the head on the neck's top; the feathered thighs
come out of the belly; each folded wing's root lies on its shoulder; the tail's base is in the rump. Where two pieces overlap, both take the same
weights, so they move as one and no seam can open.

Two clean-ups the skin needed, neither changing the look: the mesh is triangulated exactly as Blender already drew its quads; and the 755 pairs
of faces the old model had lying in one plane on each other (stacked feather cards, cards on the skin, each eye's layers under its iris: they
shimmered in the engine, and fail the QA's z-fighting test) are parted, keeping what shows (lift_coplanar). The game side (the PetRig profile,
its animate function and the special) is written from this file's printed tables: the walk, the crouch, the stances, SOLE.
"""
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import V, chain_weight, mir, smooth, weigh

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "rig"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET, EGG = "SpiritCrane", "SpiritBreezeEgg"
N = PET + "_"
ROOT = pet_kit.ROOT
SOURCE = os.path.join(ROOT, "tools/blender/pets", EGG, PET + ".blend")
MAPS = {"SpiritCrane_Color": os.path.join(ROOT, "assets/pets", EGG, "SpiritCrane_color.png"),
        "SpiritCrane_Normal": os.path.join(ROOT, "assets/pets", EGG, "SpiritCrane_normal.png")}

# ---------- the file: the crane's own .blend, its game pieces copied into a collection of their own ----------
bpy.ops.wm.open_mainfile(filepath=SOURCE, load_ui=False)
scene = bpy.context.scene
pet_kit.scene = scene
trial = os.environ.get("PET_KIT_TRIAL")
pet_kit.PET, pet_kit.N = PET, N
pet_kit.OUT = trial or os.path.join(ROOT, "assets/pets", EGG)
pet_kit.TOOLS = trial or os.path.join(ROOT, "tools/blender/pets", EGG)
for old in [c for c in bpy.data.collections if c.name == N + "Game"]:       # a previous build: rebuilt from the pieces each time
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)
for arm in [a for a in bpy.data.armatures if a.users == 0]:
    bpy.data.armatures.remove(arm)
GAME = bpy.data.collections.new(N + "Game")
scene.collection.children.link(GAME)
pet_kit.GAME = GAME
pet_kit.HI = GAME
for lc in bpy.context.view_layer.layer_collection.children:      # only the rigged crane is seen and rendered
    lc.exclude = lc.name != GAME.name

SOLIDS = ("Body", "Neck", "Head", "LegL", "LegR", "WingL", "WingR", "Tail")


def to_srgb(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def glow_hex(o):
    bsdf = next(n for n in o.data.materials[0].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return "%02x%02x%02x" % tuple(round(to_srgb(c) * 255) for c in bsdf.inputs["Base Color"].default_value[:3])


def copy_piece(src, name):
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    o.data.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    GAME.objects.link(o)
    o.data.transform(src.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    for k in list(o.keys()):
        del o[k]
    return o


def gather():
    """Copies of the crane's game pieces: solids by part, glow pieces joined by part and colour (as the old export named them)."""
    src = bpy.data.collections[PET]
    solids = {part: copy_piece(bpy.data.objects[N + part + "Low"], N + part + "Piece") for part in SOLIDS}
    groups = {}
    for o in src.objects:
        if o.type != "MESH" or o.get("marker") or o.name.endswith("Low"):
            continue
        groups.setdefault((o.get("rig", "Body"), glow_hex(o)), []).append(o)
    glows = {}
    for (part, hexa), objs in sorted(groups.items()):
        pieces = [copy_piece(o, "%s%s_Glow_%s" % (N, part, hexa) + ("" if k == 0 else ".x%d" % k)) for k, o in enumerate(objs)]
        g = pieces[0]
        if len(pieces) > 1:
            pet_kit.select_only(pieces, g)
            with bpy.context.temp_override(active_object=g, selected_editable_objects=pieces, selected_objects=pieces):
                bpy.ops.object.join()
            g = bpy.context.view_layer.objects.active
        g.name = g.data.name = "%s%s_Glow_%s" % (N, part, hexa)
        g.data.polygons.foreach_set("use_smooth", [False] * len(g.data.polygons))      # (flat Neon, as the old export made them)
        glows[(part, hexa)] = g
    return solids, glows


# ---------- the skeleton ----------
NECK_BONES = [("Neck1", V(0, -0.31, 1.24)), ("Neck2", V(0, -0.405, 1.43)), ("Neck3", V(0, -0.41, 1.62)), ("Neck4", V(0, -0.44, 1.82)), ("Head", V(0, -0.53, 2.0))]
NECK_LINE = pet_kit.catmull([V(0, -0.27, 1.12)] + [p for _, p in NECK_BONES] + [V(0, -0.6, 2.03)], 12)
CREST = V(0, -0.5, 2.11)
CHEST = V(0, -0.22, 1.16)
WING = [V(0.15, -0.2, 1.24), V(0.19, 0.12, 1.22), V(0.2, 0.42, 1.19), V(0.22, 0.62, 1.16)]        # (left) shoulder, along the folded wing to its tip
WING_Y = (0.0, 0.2, 0.3, 0.45, 0.53, 0.6)                                                        # where each wing bone hands over to the next (y)
LEG = [V(0.09, 0.04, 1.06), V(0.098, 0.085, 0.74), V(0.1, 0.1, 0.57), V(0.1, 0.0, 0.06)]          # (left) hip, knee (at the thigh's feathered end), heel, ankle
TAIL = [V(0, 0.28, 1.15), V(0, 0.55, 1.15), V(0, 0.85, 1.08)]


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, 0, 1.1), "Root"), ("Chest", CHEST.copy(), "Body")]
    parent = "Body"
    for name, at in NECK_BONES:
        bones.append((name, at.copy(), parent))
        parent = name
    bones.append(("Crest", CREST.copy(), "Head"))
    for side, tag in ((1, "L"), (-1, "R")):
        parent = "Body"
        for k, at in enumerate(WING):
            bones.append(("Wing%s%d" % (tag, k + 1), mir(at, side), parent))
            parent = "Wing%s%d" % (tag, k + 1)
        parent = "Body"
        for k, at in enumerate(LEG):
            name = ("Leg%s%d" % (tag, k + 1)) if k < 3 else "Foot" + tag
            bones.append((name, mir(at, side), parent))
            parent = name
    parent = "Body"
    for k, at in enumerate(TAIL):
        bones.append(("Tail%d" % (k + 1), at.copy(), parent))
        parent = "Tail%d" % (k + 1)
    return pet_kit.armature(bones)


# ---------- weights: one rule per region, by where a point is, so overlapping pieces take the same weights ----------
NECK_NAMES = ["Body", "Neck1", "Neck2", "Neck3", "Neck4", "Head"]


def neck_knots():
    f, _ = pet_kit.nearest_on(NECK_LINE, np.array([tuple(p) for _, p in NECK_BONES]))
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [f[0] - 0.015] + mids + [f[-1] + 0.02]


def neck_weight(p, f, d, knots):
    return chain_weight(NECK_NAMES, knots, float(f))


def crest_share(p):
    return float(smooth(2.1, 2.17, p[2])) * float(smooth(-0.6, -0.54, p[1]))


def wing_weight(tag, p):
    y = p[1]
    names = ["Wing%s%d" % (tag, k + 1) for k in range(4)]
    a, b, c, d, e, g = WING_Y
    if y <= a:
        return {names[0]: 1.0}
    if y <= b:
        s = float(smooth(a, b, y))
        return {names[0]: 1 - s, names[1]: s}
    if y <= c:
        return {names[1]: 1.0}
    if y <= d:
        s = float(smooth(c, d, y))
        return {names[1]: 1 - s, names[2]: s}
    if y <= e:
        return {names[2]: 1.0}
    s = float(smooth(e, g, y))
    return {names[2]: 1 - s, names[3]: s}


def leg_weight(tag, p):
    """The feathered thigh rigid on the hip bone; the knee and the heel short joints, as a bird's are; the foot and toes rigid."""
    names = ["Leg%s1" % tag, "Leg%s2" % tag, "Leg%s3" % tag, "Foot" + tag]
    z = p[2]
    for k, (top, bottom) in enumerate(((0.78, 0.72), (0.6, 0.545), (0.095, 0.05))):
        if z >= top:
            return {names[k]: 1.0}
        if z > bottom:
            s = float(smooth(top, bottom, z))
            return {names[k]: 1 - s, names[k + 1]: s}
    return {names[3]: 1.0}


def tail_weight(p):
    y = p[1]
    if y <= 0.42:
        return {"Tail1": 1.0}
    if y <= 0.62:
        s = float(smooth(0.42, 0.62, y))
        return {"Tail1": 1 - s, "Tail2": s}
    if y <= 0.72:
        return {"Tail2": 1.0}
    if y <= 0.92:
        s = float(smooth(0.72, 0.92, y))
        return {"Tail2": 1 - s, "Tail3": s}
    return {"Tail3": 1.0}


def body_weight(p):
    """Rigid, but for a soft front that breathes."""
    c = math.exp(-(((p[0]) / 0.2) ** 2 + ((p[1] + 0.3) / 0.14) ** 2 + ((p[2] - 1.12) / 0.16) ** 2)) * 0.7
    return {"Body": 1 - c, "Chest": c} if c > 0.02 else {"Body": 1.0}


def head_weight(p, f, d, knots):
    """The head's own piece: the part of it on the neck's top follows the neck as the neck's piece does there; the crest's plumes on their own bone."""
    if p[2] < 2.06 and d < 0.09:
        w = neck_weight(p, f, d, knots)
    else:
        w = {"Head": 1.0}
    c = crest_share(p)
    if c > 0.01:
        w = {k: v * (1 - c) for k, v in w.items()}
        w["Crest"] = w.get("Crest", 0) + c
    return w


def weights_for(part, P):
    knots = neck_knots()
    f, d = pet_kit.nearest_on(NECK_LINE, P)
    out = []
    for i, p in enumerate(P):
        if part == "Body":
            out.append(body_weight(p))
        elif part == "Neck":
            out.append(neck_weight(p, f[i], d[i], knots))
        elif part == "Head":
            out.append(head_weight(p, f[i], d[i], knots))
        elif part in ("WingL", "WingR"):
            out.append(wing_weight(part[-1], p))
        elif part in ("LegL", "LegR"):
            out.append(leg_weight(part[-1], p))
        elif part == "Tail":
            out.append(tail_weight(p))
    return out


PIECES = SOLIDS


def bind_all(solids, glows, rig):
    for part, o in solids.items():
        weigh(o, weights_for(part, pet_kit.verts(o)))
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(part)] * len(o.data.polygons))
    for (part, hexa), g in glows.items():
        P = pet_kit.verts(g)
        if part == "Head":
            # the crest's glowing tips ride the crest; the lotus, the eyes' rings, irises and glints the head
            weigh(g, [{"Crest": 1.0} if hexa == "95eded" else {"Head": 1.0} for p in P])
        else:
            weigh(g, weights_for(part, P))
    body = pet_kit.join_into(dict(Skin=solids["Body"], **{k: v for k, v in solids.items() if k != "Body"}), "Body")
    # triangulated as Blender already draws it (each quad split on its first diagonal, as its loop triangles are), so the crane looks as it did,
    # and the QA's check, the parting below and the engine all see the very same triangles
    for o in [body] + list(glows.values()):
        o.data.calc_loop_triangles()
        before_tris = {tuple(sorted(lt.vertices)) for lt in o.data.loop_triangles}
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="FIXED", ngon_method="EAR_CLIP")
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        after_tris = {tuple(sorted(p.vertices)) for p in o.data.polygons}
        if after_tris != before_tris:
            print("TRIANGULATION differs from the drawn triangles on", o.name, len(after_tris - before_tris), "of", len(after_tris), flush=True)
    found, left = lift_coplanar([body] + list(glows.values()))
    for o in [body] + list(glows.values()):       # (and nothing loose left by the deletions)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    print("COPLANAR faces lifted apart: pairs found", found, "left", left, flush=True)
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


def qa_tris(me):
    """The mesh's triangles as the QA's z-fighting test makes them (bmesh's own triangulation, which is not the loop triangles'), each with the
    polygon it comes from: (vertices, polygon, normal, area, centre). The mesh itself keeps its quads."""
    bm = bmesh.new()
    bm.from_mesh(me)
    layer = bm.faces.layers.int.new("poly")
    for f in bm.faces:
        f[layer] = f.index
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    out = [(tuple(v.index for v in f.verts), f[layer], f.normal.copy(), f.calc_area(), f.calc_center_median()) for f in bm.faces]
    bm.free()
    return out


def coplanar_pairs(objs, eps=0.001):
    """Triangles lying on each other, facing the same way, within eps (the QA's z-fighting test): (object, its own vertices) for each, with the area."""
    from mathutils.geometry import area_tri, intersect_point_tri
    verts, tris, meta = [], [], []
    for o in objs:
        me = o.data
        base = len(verts)
        verts += [v.co.copy() for v in me.vertices]
        for tv, poly, nrm, area, cen in qa_tris(me):
            tris.append(tuple(base + i for i in tv))
            meta.append((o, tv, nrm, area, cen, poly))
    tree = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    sets = [set(t) for t in tris]
    pairs = set()
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = meta[ti][2]
        if n.length < 0.5:
            continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, 0.6), cen.lerp(b, 0.6), cen.lerp(c, 0.6)):
            for _, _, tj, _ in tree.find_nearest_range(p, eps):
                if tj is None or tj == ti or sets[ti] & sets[tj] or n.dot(meta[tj][2]) < 0.999:
                    continue
                a2, b2, c2 = (verts[i] for i in tris[tj])
                if intersect_point_tri(p - meta[tj][2] * meta[tj][2].dot(p - a2), a2, b2, c2):
                    pairs.add((min(ti, tj), max(ti, tj)))
    return [(meta[i], meta[j]) for i, j in pairs]


def islands_of(o):
    """Each vertex's connected piece (a feather card, an eye's disc, a skin), and each piece's size."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    own = [-1] * len(bm.verts)
    sizes = []
    for v in bm.verts:
        if own[v.index] >= 0:
            continue
        k = len(sizes)
        stack, n = [v], 0
        own[v.index] = k
        while stack:
            w = stack.pop()
            n += 1
            for e in w.link_edges:
                x = e.other_vert(w)
                if own[x.index] < 0:
                    own[x.index] = k
                    stack.append(x)
        sizes.append(n)
    bm.free()
    return own, sizes


NUDGE = 0.0012      # metres a piece is lifted off (or pressed under) another per round
NEAR, FAR = 0.006, 0.03     # a press moves its piece fully this near the faces it touched, fading out by this far
CARD_NEAR, CARD_FAR = 0.006, 0.03     # a card's lift likewise (spread wider, it bared the dark underside of the card beneath)


def piece_data(objs):
    isl = {o.name: islands_of(o) for o in objs}
    extent = {}
    for o in objs:
        own, sizes = isl[o.name]
        lo, hi = {}, {}
        for i, v in enumerate(o.data.vertices):
            k = own[i]
            lo[k] = Vector(map(min, lo.get(k, v.co), v.co))
            hi[k] = Vector(map(max, hi.get(k, v.co), v.co))
        for k in lo:
            extent[(o.name, k)] = (hi[k] - lo[k]).length
    return isl, extent


def under_of(A, B, isl, extent):
    """Of two faces lying together, which belongs underneath (what shows is the other): a glowing piece shows over a plain one larger than it (an
    eye's dark layers under its iris, a tail card under its lit tip), a plain one smaller than it shows over it (the pupil); of two alike, the
    smaller shows (the detail laid on the larger)."""
    na, nb = (A[0].name, isl[A[0].name][0][A[1][0]]), (B[0].name, isl[B[0].name][0][B[1][0]])
    ga, gb = "_Glow_" in na[0], "_Glow_" in nb[0]
    if ga != gb:
        plain, lit = (A, B) if gb else (B, A)
        pn = (plain[0].name, isl[plain[0].name][0][plain[1][0]])
        ln = (lit[0].name, isl[lit[0].name][0][lit[1][0]])
        return plain if extent[pn] >= extent[ln] else lit
    return A if extent[na] >= extent[nb] else B


def card_shade(objs, isl, nodes):
    """Each card's mean brightness in the baked colour map, over its own UVs."""
    img = bpy.data.images[PET + "_Color"]
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    out = {}
    for name in {n[0] for n in nodes}:
        me = bpy.data.objects[name].data
        uv = me.uv_layers.active.data
        own = isl[name][0]
        acc = {}
        for poly in me.polygons:
            node = (name, own[poly.vertices[0]])
            if node not in nodes:
                continue
            for l in poly.loop_indices:
                u, v = uv[l].uv
                c = px[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w)))]
                a = acc.setdefault(node, [0.0, 0])
                a[0] += float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
                a[1] += 1
        for node, (t, n) in acc.items():
            out[node] = t / n
    return out


def stack_cards(objs, isl, cards, rounds=60):
    """The feather cards of the folded wings and the tail lie in rows, each in the very plane of the next. Where two lie together, one is lifted
    off the other, outward from the crane's middle: only there (the lift fades out within 3 cm, so the rest of the card stays put), and never
    turned (turned, or lifted whole, a card's edge cut through its neighbour, whose dark underside then showed in flecks and stripes). The paler
    card of a pair goes over the darker (the pale feathers are what shows over the slate ones), each a layer of 1.2 mm over the one under it, a
    row only alternating between layers; again until no two lie together. Returns the pairs found at first."""
    shade = card_shade(objs, isl, cards)
    middle = sum((v.co for o in objs for v in o.data.vertices), Vector((0, 0, 0))) / sum(len(o.data.vertices) for o in objs)
    way = {}
    found = None
    for _ in range(rounds):
        pairs = [(A, B) for A, B in coplanar_pairs(objs) if (A[0].name, isl[A[0].name][0][A[1][0]]) in cards and (B[0].name, isl[B[0].name][0][B[1][0]]) in cards]
        found = len(pairs) if found is None else found
        if os.environ.get("CRANE_DEBUG"):
            same = sum(1 for A, B in pairs if A[0] is B[0] and isl[A[0].name][0][A[1][0]] == isl[B[0].name][0][B[1][0]])
            print("STACK", len(pairs), "same card", same, flush=True)
        if not pairs:
            break
        link = {}
        for A, B in pairs:
            na, nb = (A[0].name, isl[A[0].name][0][A[1][0]]), (B[0].name, isl[B[0].name][0][B[1][0]])
            link.setdefault(na, set()).add(nb)
            link.setdefault(nb, set()).add(na)
            for node, face in ((na, A), (nb, B)):
                if node not in way:
                    way[node] = face[2] if face[2].dot(face[4] - middle) >= 0 else -face[2]
        touch, lean = {}, {}
        for A, B in pairs:
            for face in (A, B):
                node = (face[0].name, isl[face[0].name][0][face[1][0]])
                touch.setdefault(node, []).append(tuple(face[4]))
                # the lift goes along the faces as they lie now (a curved card's own normal turns along it), the side kept that it first went
                n = face[2] if face[2].dot(way[node]) >= 0 else -face[2]
                lean[node] = lean.get(node, Vector((0, 0, 0))) + n
        layer = {}
        for node in sorted(link, key=lambda n: (round(shade.get(n, 0.5), 3), n[0], n[1])):
            taken = {layer[m] for m in link[node] if m in layer}
            layer[node] = next(c for c in range(len(link) + 1) if c not in taken)
        for node, c in layer.items():
            if c == 0:
                continue
            # only near where it lies on the other: the lift fades out within 3 cm, so the rest of the card stays exactly where it was
            d = lean[node].normalized() * (NUDGE * c)
            at = np.array(touch[node])
            own = isl[node[0]][0]
            me = bpy.data.objects[node[0]].data
            for i, v in enumerate(me.vertices):
                if own[i] == node[1]:
                    wgt = 1.0 - float(smooth(CARD_NEAR, CARD_FAR, float(np.min(np.linalg.norm(at - np.array(tuple(v.co)), axis=1)))))
                    if wgt > 0:
                        v.co += d * wgt
            me.update()
    return found


def drop_covered(objs, isl, extent, eps=0.001):
    """A face lying wholly under another piece, in the same plane and facing the same way, can never be seen: it is deleted (the QA's own remedy
    for a hidden duplicate). Only wholly covered faces: every sample of the face (its middle, near its corners and edges) must lie within 1 mm
    of the covering piece's surface, facing the same way; a face that shows anywhere stays. Returns how many went."""
    pairs = coplanar_pairs(objs)
    under = {}
    for A, B in pairs:
        U = under_of(A, B, isl, extent)
        O = B if U is A else A
        under.setdefault((U[0].name, U[1]), set()).add((O[0].name, isl[O[0].name][0][O[1][0]]))
    trees = {}

    def tree_for(node):
        if node not in trees:
            name, k = node
            me = bpy.data.objects[name].data
            own = isl[name][0]
            tris = [t[0] for t in qa_tris(me) if own[t[0][0]] == k]
            trees[node] = BVHTree.FromPolygons([v.co for v in me.vertices], tris, epsilon=0.0)
        return trees[node]
    dead = {}
    for (name, tri), overs in under.items():
        me = bpy.data.objects[name].data
        corners = [me.vertices[i].co.copy() for i in tri]
        n = (corners[1] - corners[0]).cross(corners[2] - corners[0])
        if n.length < 1e-12:
            continue
        n.normalize()
        mid = sum(corners, Vector((0, 0, 0))) / 3
        samples = [mid] + [mid.lerp(c, 0.95) for c in corners] + [corners[k].lerp(corners[(k + 1) % 3], 0.5).lerp(mid, 0.05) for k in range(3)]
        if all("_Glow_" in node[0] for node in overs):
            # under a glowing tip sleeved over a card's end: what lies in its surface is hidden by it, out to where the sleeve ends (a face
            # crossing that edge keeps its outer part showing: those, nearly all inside, are judged by their middle and corners drawn in)
            samples = [mid] + [mid.lerp(c, 0.7) for c in corners]
        ok = True
        for p in samples:
            hit = False
            for node in overs:
                loc, nrm, _, dist = tree_for(node).find_nearest(p, eps)
                if loc is not None and nrm.dot(n) > 0.999:
                    hit = True
                    break
            if not hit:
                ok = False
                break
        if ok:
            dead.setdefault(name, set()).add(tri)
    count = 0
    for name, tris in dead.items():
        o = bpy.data.objects[name]
        by_poly = {}
        for tv, poly, *_ in qa_tris(o.data):
            by_poly.setdefault(poly, []).append(tv in tris)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        gone = [bm.faces[i] for i, flags in by_poly.items() if all(flags)]       # (a quad goes only when both its halves are covered)
        bmesh.ops.delete(bm, geom=gone, context="FACES_ONLY")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        count += len(gone)
    return count


def press_under(objs, rounds=40):
    """What is left: the piece underneath pressed 1.2 mm under the other, only near where they touch (the press fades out within 3 cm, so
    nothing else moves); again until none is left. A big skin is never pressed: what lies on it is raised instead. A piece keeps the way it was
    first sent (a layer pressed under an eye's iris that then meets the skin under it goes on under the skin, never back up into the iris), so
    every piece only ever moves one way and the parting always ends."""
    way, pressed = {}, {}
    for _ in range(rounds):
        isl, extent = piece_data(objs)
        pairs = coplanar_pairs(objs)
        if not pairs:
            return 0
        middle = sum((v.co for o in objs for v in o.data.vertices), Vector((0, 0, 0))) / sum(len(o.data.vertices) for o in objs)
        marks = {}
        for A, B in pairs:
            U = under_of(A, B, isl, extent)
            O = B if U is A else A
            un = (U[0].name, isl[U[0].name][0][U[1][0]])
            on = (O[0].name, isl[O[0].name][0][O[1][0]])
            n = O[2] if O[2].dot(O[4] - middle) >= 0 else -O[2]       # the side that shows
            fixed_u = "_Glow_" in un[0] or isl[un[0]][1][un[1]] > 300
            fixed_o = "_Glow_" in on[0] or isl[on[0]][1][on[1]] > 300
            if un in way or (not fixed_u and on not in way):
                node, face, d = un, U, -n
            elif not fixed_o:
                node, face, d = on, O, n
            else:
                node, face, d = un, U, -n
            if node in way:
                d = way[node]
            if pressed.get(node, 0) >= 2:
                continue
            marks.setdefault(node, []).append((face[4], d))
        # a piece another lies under waits its turn (were both to move, a row of them would sink together and never part)
        overs = set()
        for A, B in pairs:
            U = under_of(A, B, isl, extent)
            O = B if U is A else A
            un, on = (U[0].name, isl[U[0].name][0][U[1][0]]), (O[0].name, isl[O[0].name][0][O[1][0]])
            if un in way and on in way:
                overs.add(on)
        for node, ms in marks.items():
            if node in overs:
                continue
            if node in way:
                d = way[node]
            else:
                ref = ms[0][1]
                d = sum(((m[1] if m[1].dot(ref) >= 0 else -m[1]) for m in ms), Vector((0, 0, 0)))
                if d.length < 1e-9:
                    continue
                d = d.normalized()
                way[node] = d
            at = np.array([tuple(m[0]) for m in ms])
            own = isl[node[0]][0]
            me = bpy.data.objects[node[0]].data
            for i, v in enumerate(me.vertices):
                if own[i] != node[1]:
                    continue
                wgt = 1.0 - float(smooth(NEAR, FAR, float(np.min(np.linalg.norm(at - np.array(tuple(v.co)), axis=1)))))
                if wgt > 0:
                    v.co += d * (NUDGE * wgt)
            me.update()
            pressed[node] = pressed.get(node, 0) + 1
    return len(coplanar_pairs(objs))


def part_eyes(objs, isl, extent):
    """Each eye is a nest of pieces: a dark mask round it (the largest), a rim ring, a dark disc inside the ring, a pupil on the disc (the
    smallest), and over them the glowing iris and turquoise rings. The mask runs on under the disc, the disc under the iris and the pupil, in the
    very same plane. What shows is kept: the disc, which shows nowhere (the iris covers it to the rim ring), and the mask's faces lying in it are
    deleted, and the pupil comes 1.2 mm forward, over the iris. Returns what was done."""
    done = []
    iris = [o for o in objs if o.name.endswith("_Glow_edce76")]
    if not iris:
        return done
    iris = iris[0]
    own_i, sizes_i = isl[iris.name]
    body = next(o for o in objs if "_Glow_" not in o.name)
    own, sizes = isl[body.name]
    P = np.array([tuple(v.co) for v in body.data.vertices])
    owns = np.array(own)
    for k in range(len(sizes_i)):
        Q = np.array([tuple(v.co) for i, v in enumerate(iris.data.vertices) if own_i[i] == k])
        c = Q.mean(0)
        near = [j for j in range(len(sizes)) if sizes[j] < 300 and np.linalg.norm(P[owns == j].mean(0) - c) < 0.05]
        if len(near) < 4:
            continue
        near.sort(key=lambda j: -extent[(body.name, j)])
        mask, pupil = near[0], near[-1]
        ext_iris = extent[(iris.name, k)]
        dome = min(near[1:-1], key=lambda j: abs(extent[(body.name, j)] - ext_iris))
        me = body.data
        # the dome's surface, to find the mask's faces lying in it
        me.calc_loop_triangles()
        dome_tris = [tuple(lt.vertices) for lt in me.loop_triangles if own[lt.vertices[0]] == dome]
        tree = BVHTree.FromPolygons([v.co for v in me.vertices], dome_tris, epsilon=0.0)
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        gone = []
        for f in bm.faces:
            if own[f.verts[0].index] != mask:
                continue
            loc, nrm, _, dist = tree.find_nearest(f.calc_center_median(), 0.0015)
            if loc is not None and abs(nrm.dot(f.normal)) > 0.99:
                gone.append(f)
        # the eye's facing, turned outward from the head. The dark disc goes (the iris covers it to the rim ring, so it shows nowhere; behind it
        # lies the head's own surface, 1.5 mm back, too near to part it from), and the pupil comes 1.2 mm forward, over the iris
        ring = [j for j in near[1:-1] if j != dome][0]
        R_ = P[owns == ring]
        w, vecs = np.linalg.eigh(np.cov((R_ - R_.mean(0)).T))
        axis = Vector(vecs[:, 0]).normalized()          # (the rim ring is flat: its normal is the eye's facing)
        if axis.x * (1 if c[0] > 0 else -1) < 0:
            axis = -axis
        for v in bm.verts:
            if own[v.index] == pupil:
                v.co += axis * NUDGE
        gone += [f for f in bm.faces if own[f.verts[0].index] == dome]
        bmesh.ops.delete(bm, geom=gone, context="FACES_ONLY")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(me)
        bm.free()
        me.update()
        done.append((len(gone), dome, pupil, mask))
        isl[body.name] = islands_of(body)            # (vertex numbers changed)
        own, sizes = isl[body.name]
        P = np.array([tuple(v.co) for v in body.data.vertices])
        owns = np.array(own)
        for j in range(len(sizes)):
            pts = P[owns == j]
            extent[(body.name, j)] = float(np.linalg.norm(pts.max(0) - pts.min(0)))
    return done


def lift_coplanar(objs):
    """The crane was modelled with some surfaces lying exactly on others: the feather cards of each folded wing and of the tail in rows, each in
    the plane of the next; small cards flat on the skin; the layers of each eye under its glowing iris; the wing and tail cards under their
    glowing tips. Such faces shimmer in the engine (and fail the QA's z-fighting test). They are parted, keeping what shows:
        - each eye's hidden dark disc goes and its pupil comes forward (part_eyes);
        - the cards are lifted apart where they touch, the paler over the darker (stack_cards);
        - a face wholly hidden under another goes (drop_covered);
        - the rest is pressed a millimetre under what shows over it, near where they touch (press_under); a glowing tip still lying on its card
          is swollen a hair; the last few faces lying (nearly) wholly under another go, the one over the others lifted off them there.
    Returns the pairs found at first and how many are left; prints what was done."""
    first = len(coplanar_pairs(objs))
    isl, extent = piece_data(objs)
    eyes = part_eyes(objs, isl, extent)
    isl, extent = piece_data(objs)
    before = {o.name: [v.co.copy() for v in o.data.vertices] for o in objs}       # (after the eyes' deletions: vertex numbers hold from here)
    # every small plain piece is a card here: the wings' and the tail's feathers, the little cards laid on the body (a skin is larger)
    cards = {(o.name, k) for o in objs if "_Glow_" not in o.name for k, n in enumerate(isl[o.name][1]) if n <= 300}
    card_pairs = stack_cards(objs, isl, cards)
    moved_cards = max((v.co - before[o.name][i]).length for o in objs for i, v in enumerate(o.data.vertices))
    tris_before = sum(len(o.data.polygons) for o in objs)
    gone = drop_covered(objs, isl, extent)
    if gone:
        before = {o.name: [v.co.copy() for v in o.data.vertices] for o in objs}
    if os.environ.get("CRANE_DEBUG"):
        from collections import Counter
        isl2, ext2 = piece_data(objs)
        pr = coplanar_pairs(objs)
        print("AFTERDROP", len(pr), Counter((A[0].name[-6:], isl2[A[0].name][1][isl2[A[0].name][0][A[1][0]]], B[0].name[-6:], isl2[B[0].name][1][isl2[B[0].name][0][B[1][0]]]) for A, B in pr).most_common(12), flush=True)
    left = press_under(objs)
    swollen = 0
    swelled = set()
    for _ in range(12):
        # the last: a glowing tip sleeved over its card's end, say. What shows is swollen a hair (1.2 mm out along its own normals), so it
        # covers the other on every side
        pairs = coplanar_pairs(objs)
        if not pairs:
            break
        isl, extent = piece_data(objs)
        grow = set()
        for A, B in pairs:
            U = under_of(A, B, isl, extent)
            O = B if U is A else A
            grow.add((O[0].name, isl[O[0].name][0][O[1][0]]))
        for name, k in grow:
            if (name, k) in swelled:
                continue
            swelled.add((name, k))
            me = bpy.data.objects[name].data
            own = isl[name][0]
            nrm = [v.normal.copy() for v in me.vertices]
            for i, v in enumerate(me.vertices):
                if own[i] == k:
                    v.co += nrm[i] * NUDGE
            me.update()
            swollen += 1
    # the very last few: a face lying (nearly all of it) under the one that shows over it goes; where it shows more than a little, the one over
    # it is lifted off it there instead (1.2 mm, fading out within 3 cm); again until none is left
    last = 0
    for _ in range(12):
        pairs = coplanar_pairs(objs)
        if not pairs:
            break
        isl, extent = piece_data(objs)
        if os.environ.get("CRANE_DEBUG"):
            print("LASTROUND", len(pairs), flush=True)
        middle = sum((v.co for o in objs for v in o.data.vertices), Vector((0, 0, 0))) / sum(len(o.data.vertices) for o in objs)
        trees = {}
        dead, lifts = {}, {}
        for A, B in pairs:
            U = under_of(A, B, isl, extent)
            O = B if U is A else A
            on = (O[0].name, isl[O[0].name][0][O[1][0]])
            if on not in trees:
                me = O[0].data
                own = isl[on[0]][0]
                trees[on] = BVHTree.FromPolygons([v.co for v in me.vertices], [t[0] for t in qa_tris(me) if own[t[0][0]] == on[1]], epsilon=0.0)
            um = U[0].data
            corners = [um.vertices[i].co for i in U[1]]
            mid = sum(corners, Vector((0, 0, 0))) / 3
            samples = [mid] + [mid.lerp(c, 0.95) for c in corners] + [corners[k].lerp(corners[(k + 1) % 3], 0.5).lerp(mid, 0.05) for k in range(3)]
            covered = sum(1 for p in samples if (lambda h: h[0] is not None and abs(h[1].dot(U[2])) > 0.99)(trees[on].find_nearest(p, 0.0015)))
            if covered >= 6:
                dead.setdefault(U[0].name, set()).add(U[5])
            else:
                n = O[2] if O[2].dot(O[4] - middle) >= 0 else -O[2]
                lifts.setdefault(on, []).append((O[4], n))
        for name, polys in dead.items():
            o = bpy.data.objects[name]
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in polys], context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bm.to_mesh(o.data)
            bm.free()
            o.data.update()
            last += len(polys)
        if dead:
            continue          # (vertex numbers changed: the lifts are found again next round)
        for (name, k), ms in lifts.items():
            ref = ms[0][1]
            d = sum(((m[1] if m[1].dot(ref) >= 0 else -m[1]) for m in ms), Vector((0, 0, 0))).normalized() * NUDGE
            at = np.array([tuple(m[0]) for m in ms])
            own = isl[name][0]
            me = bpy.data.objects[name].data
            for i, v in enumerate(me.vertices):
                if own[i] == k:
                    wgt = 1.0 - float(smooth(NEAR, FAR, float(np.min(np.linalg.norm(at - np.array(tuple(v.co)), axis=1)))))
                    if wgt > 0:
                        v.co += d * wgt
            me.update()
    pairs = coplanar_pairs(objs)
    if pairs:
        # and any still left: the face underneath goes, whatever shows of it (a few faces, at the edges of stacked feather cards)
        isl, extent = piece_data(objs)
        dead = {}
        for A, B in pairs:
            U = under_of(A, B, isl, extent)
            dead.setdefault(U[0].name, set()).add(U[5])
        for name, polys in dead.items():
            o = bpy.data.objects[name]
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in polys], context="FACES")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
            bm.to_mesh(o.data)
            bm.free()
            o.data.update()
            last += len(polys)
    left = len(coplanar_pairs(objs))
    if os.environ.get("CRANE_DEBUG"):
        from collections import Counter
        isl2, ext2 = piece_data(objs)
        pr = coplanar_pairs(objs)
        print("LEFT", Counter((A[0].name[-6:], isl2[A[0].name][1][isl2[A[0].name][0][A[1][0]]], round(ext2[(A[0].name, isl2[A[0].name][0][A[1][0]])], 3), tuple(round(x, 2) for x in A[4]),
                              B[0].name[-6:], isl2[B[0].name][1][isl2[B[0].name][0][B[1][0]]]) for A, B in pr).most_common(20), flush=True)
    glow_moved = max([(v.co - before[o.name][i]).length for o in objs if "_Glow_" in o.name for i, v in enumerate(o.data.vertices) if i < len(before[o.name])] or [0])
    print("COPLANAR eyes (mask faces deleted, disc, pupil, mask)", eyes, "card pairs", card_pairs, "(cards lifted, most mm %.1f)" % (moved_cards * 1000), "hidden faces deleted", gone, "of", tris_before,
          "pieces swollen", swollen, "glow pieces moved most mm %.2f" % (glow_moved * 1000), "last faces deleted", last, "left", left, flush=True)
    return first, left


# ---------- poses: in the game's axes, as PetRig's tables are written. Turns x, y, z: +x lifts what points forward and swings a hanging limb
# forward; +y turns it to its left; +z rolls it. ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def game_matrix(rx, ry, rz):
    return Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def sym(table):
    out = dict(table)
    for name, v in table.items():
        m = re.match(r"^(Wing|Leg|Foot)L(\d?)$", name)
        if m and m.group(1) + "R" + m.group(2) not in table:
            out[m.group(1) + "R" + m.group(2)] = (v[0], -v[1], -v[2]) + tuple(v[3:])
    return out


def wing_spec(open_, flap, bend, hand, tip, sweep=0.0):
    """Both wings: open_ (0..1) swings each out of its fold to a spread wing, flap (radians, + up) beats it about the body's long axis, bend/hand/tip
    flex its outer parts (+ up), sweep (+ back) folds it back. In PetRig: WingX1 = CFrame.Angles(0, 0, -s * flap) * CFrame.Angles(OPEN_X * o, s * OPEN_Y * o, 0)
    with s = 1 left, -1 right; the outer bones CFrame.Angles(0, s * flex, 0)."""
    out = {}
    for tag, s in (("L", 1), ("R", -1)):
        m = game_matrix(0, 0, -s * flap) @ game_matrix(OPEN_X * open_, s * OPEN_Y * open_ + s * sweep, 0)
        axis, angle = m.to_quaternion().to_axis_angle()
        out["Wing%s1" % tag] = (tuple(axis), math.degrees(angle), (0, 0, 0))
        for k, a in ((2, bend), (3, hand), (4, tip)):
            out["Wing%s%d" % (tag, k)] = game_turn(0, s * a, 0)
    return out


OPEN_X, OPEN_Y = -1.05, -1.48        # the spread: 60 degrees of roll so the wing lies near level, 85 of swing out from the fold (left; the right mirrors y)


def legs2(l, r):
    """Each leg's three turns (hip, knee, heel), its foot turned back level."""
    out = {}
    for tag, a in (("L", l), ("R", r)):
        for k in range(3):
            out["Leg%s%d" % (tag, k + 1)] = (a[k], 0, 0)
        out["Foot" + tag] = (-sum(a), 0, 0)
    return out


def foot_at(rig, tag):
    return rig.matrix_world @ rig.pose.bones["Foot" + tag].head


def solve_leg(rig, base, tag, target, start=(0.0, 0.0, 0.0), cost_w=(1.0, 3.0, 1.0), pitch=0.0):
    """Hip, knee and heel turns that put the foot (its ankle) at target (y, z) with the body posed as base: a small simplex search. The knee is
    dear (it sits inside the feathered thigh; a bird walks on its hip and heel), the heel cheap."""
    other = "R" if tag == "L" else "L"

    def cost(xs):
        pet_kit.pose(rig, spec({**base, **{("Leg%s%d" % (tag, k + 1)): (xs[k], 0, 0) for k in range(3)}, "Foot" + tag: (-sum(xs) - pitch, 0, 0)}))
        p = foot_at(rig, tag)
        return (p.z - target[1]) ** 2 * 4 + (p.y - target[0]) ** 2 + 0.0004 * sum(w * x * x for w, x in zip(cost_w, xs))

    pts = [np.array(start, dtype=float)] + [np.array(start, dtype=float) + np.eye(3)[k] * 0.3 for k in range(3)]
    vals = [cost(p) for p in pts]
    for _ in range(300):
        order = np.argsort(vals)
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        c = sum(pts[:-1]) / 3
        r = c + (c - pts[-1])
        fr = cost(r)
        if fr < vals[0]:
            e = c + 2 * (c - pts[-1])
            fe = cost(e)
            pts[-1], vals[-1] = (e, fe) if fe < fr else (r, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = r, fr
        else:
            k = c + 0.5 * (pts[-1] - c)
            fk = cost(k)
            if fk < vals[-1]:
                pts[-1], vals[-1] = k, fk
            else:
                pts = [pts[0] + 0.5 * (p - pts[0]) for p in pts]
                vals = [cost(p) for p in pts]
    i = int(np.argmin(vals))
    return tuple(round(float(v), 3) for v in pts[i]), vals[i]


# its walk: an elegant high step. Each foot slides back flat on the ground, then is lifted high and swung forward; left and right half a cycle apart.
# The body bobs a little, lowest as a foot comes down (its neck takes the bob back in the game, so the head rides level).
WALK_N, WALK_DUTY, WALK_REACH, WALK_LIFT = 16, 0.58, 0.14, 0.12
WALK_BOB = 0.012


def walk_path(t):
    if t < WALK_DUTY:
        return -WALK_REACH + 2 * WALK_REACH * t / WALK_DUTY, 0.0
    s = (t - WALK_DUTY) / (1 - WALK_DUTY)
    return WALK_REACH - 2 * WALK_REACH * (0.5 - 0.5 * math.cos(math.pi * s)), math.sin(math.pi * s) ** 0.8


def walk_bob(g):
    return -WALK_BOB * math.cos(4 * math.pi * g)


def find_walk(rig):
    pet_kit.pose(rig, {})
    rest = foot_at(rig, "L")
    rows, start = [], (0.0, 0.0, 0.0)
    for k in range(WALK_N + 1):
        t = (k % WALK_N) / WALK_N
        dy, up = walk_path(t)
        base = {"Body": (0, 0, 0, (0, walk_bob(t), 0))}
        a, c = solve_leg(rig, base, "L", (rest.y + dy, rest.z + up * WALK_LIFT), start)
        start = a
        if k < WALK_N:
            rows.append((a, c))
        else:
            rows[0] = (a, c)
    return rows


def walk_table(rows, g):
    out = {"Body": (0, 0, 0, (0, walk_bob(g), 0))}
    for tag, lead in (("L", 0.0), ("R", 0.5)):
        t = ((g + lead) % 1.0) * WALK_N
        i, w = int(t) % WALK_N, t - int(t)
        a, c = rows[i][0], rows[(i + 1) % WALK_N][0]
        ang = [a[j] * (1 - w) + c[j] * w for j in range(3)]
        for j in range(3):
            out["Leg%s%d" % (tag, j + 1)] = (ang[j], 0, 0)
        out["Foot" + tag] = (-sum(ang), 0, 0)
    return out


# its stances (left values; sym() mirrors the right)
NECK_UP = {"Neck1": (0.12, 0, 0), "Neck2": (0.1, 0, 0), "Neck3": (0.06, 0, 0), "Neck4": (0.05, 0, 0), "Head": (0.45, 0, 0), "Crest": (-0.15, 0, 0)}   # skyward
NECK_FORWARD = {"Body": (-0.06, 0, 0), "Neck1": (-0.7, 0, 0), "Neck2": (-0.28, 0, 0), "Neck3": (0.2, 0, 0), "Neck4": (0.25, 0, 0), "Head": (0.53, 0, 0),
                "Crest": (-0.3, 0, 0)}                                                                                # stretched out ahead in flight, the head level
LEGS_TRAIL = sym({"LegL1": (-1.25, 0, 0), "LegL2": (0.05, 0, 0), "LegL3": (-0.08, 0, 0), "FootL": (-0.25, 0, 0)})   # in flight, drawn up and trailed straight back under the tail, as a crane flies
TAIL_FLY = {"Tail1": (-0.2, 0, 0), "Tail2": (-0.08, 0, 0), "Tail3": (-0.05, 0, 0)}      # lifted over the trailing legs (+x lowers what points back)
TAIL_UP = {"Tail1": (-0.25, 0, 0), "Tail2": (-0.12, 0, 0), "Tail3": (-0.08, 0, 0)}
GLANCE = {"Neck2": (0.0, 0.18, 0), "Neck3": (0.0, 0.25, 0), "Neck4": (0.04, 0.3, 0.05), "Head": (0.05, 0.4, 0.12)}
PREEN = sym({"Neck1": (-0.1, 0.3, 0), "Neck2": (-0.25, 0.45, 0), "Neck3": (-0.35, 0.5, 0.1), "Neck4": (-0.3, 0.45, 0.1), "Head": (-0.4, 0.35, 0.25)})
BOW = {"Body": (-0.2, 0, 0), "Neck1": (-0.35, 0, 0), "Neck2": (-0.25, 0, 0), "Neck3": (0.05, 0, 0), "Neck4": (0.15, 0, 0), "Head": (0.2, 0, 0), "Tail1": (0.25, 0, 0),
       "LegL1": (0.2, 0, 0), "LegR1": (0.2, 0, 0)}      # (the legs turned back against the body's pitch, so the feet stay flat where they stand)


def pose_library(walk, crouch):
    lib = {
        "Fold": {},
        "Glance": spec(GLANCE),
        "Preen": spec({k: v for k, v in PREEN.items() if not k.endswith("R")}),
        "NeckUp": spec(NECK_UP),
        "Bow": spec(BOW),
        "Ruffle": {**wing_spec(0.12, 0.1, 0.05, 0.05, 0.05), **spec({"Tail1": (0.1, 0.12, 0), "Tail2": (0, 0.15, 0), "Crest": (0, 0.2, 0.15)})},
        "HalfOpen": wing_spec(0.5, 0.15, 0.0, -0.1, -0.1),
        "Open": wing_spec(1.0, 0.0, 0.0, 0.0, 0.0),
        "FlapUp": {**wing_spec(1.0, 0.65, -0.15, -0.2, -0.25), **spec({**NECK_FORWARD, **LEGS_TRAIL, **TAIL_FLY})},
        "FlapDown": {**wing_spec(1.0, -0.55, 0.12, 0.25, 0.3), **spec({**NECK_FORWARD, **LEGS_TRAIL, **TAIL_FLY})},
        "Glide": {**wing_spec(1.0, 0.08, -0.04, 0.0, 0.05), **spec({**NECK_FORWARD, **LEGS_TRAIL, **TAIL_FLY})},
        "Halo": {**wing_spec(1.0, 0.75, 0.0, -0.15, -0.2), **spec({**NECK_UP, **TAIL_UP})},
        "Crouch": spec(crouch),
        "HopAir": {**wing_spec(0.75, 0.45, -0.1, -0.15, -0.2), **spec({**legs2((0.35, 0.3, -0.75), (0.35, 0.3, -0.75)), **TAIL_UP, "Neck1": (0.1, 0, 0), "Head": (0.2, 0, 0)})},
    }
    for k in range(8):
        lib["Walk%d" % k] = spec(walk_table(walk, k / 8))
    return lib


CROUCH_DROP = 0.08


def find_crouch(rig):
    """Its crouch before a hop: the body down, the heels bent, the feet where they stood."""
    pet_kit.pose(rig, {})
    rest = foot_at(rig, "L")
    base = {"Body": (-0.08, 0, 0, (0, -CROUCH_DROP, 0)), "Neck1": (-0.1, 0, 0), "Head": (0.1, 0, 0)}
    a, c = solve_leg(rig, base, "L", (rest.y, rest.z), (0.2, 0.0, -0.4), pitch=base["Body"][0])
    out = {**base, **legs2(a, a)}
    for tag in "LR":
        out["Foot" + tag] = (-(sum(a) + base["Body"][0]), 0, 0)
    return out, c


# ---------- checks ----------
def posed(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def dominant(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in o.data.vertices]


class Checker:
    """What must never pass through what, in any pose: the wings through the body, the neck or each other; the legs through the wings or the
    tail; the head through the body; and the seams: pieces lying together at rest (the neck's collar in the breast, the head on the neck, the
    thighs in the belly, the wings' roots on the shoulders, the tail in the rump) must not pull apart."""

    def __init__(self, body):
        self.body = body
        me = body.data
        fp = np.zeros(len(me.polygons), dtype=int)
        me.attributes["piece"].data.foreach_get("value", fp)
        me.calc_loop_triangles()
        self.tris = [tuple(lt.vertices) for lt in me.loop_triangles]
        self.piece = [PIECES[fp[lt.polygon_index]] for lt in me.loop_triangles]
        vpiece = [""] * len(me.vertices)
        for t, pc in zip(self.tris, self.piece):
            for v in t:
                vpiece[v] = pc
        self.vpiece = vpiece
        co0 = posed(body)
        self.co0 = co0

        def faces(test):
            return [i for i, pc in enumerate(self.piece) if test(pc, i)]
        rootish = lambda i, c, r: min(np.linalg.norm(co0[v] - c) for v in self.tris[i]) > r      # noqa: E731
        sh = {t: np.array(tuple(mir(WING[0], s))) for t, s in (("L", 1), ("R", -1))}
        self.wing = {t: faces(lambda pc, i, t=t: pc == "Wing" + t and rootish(i, sh[t], 0.12)) for t in "LR"}
        self.body_f = faces(lambda pc, i: pc == "Body")
        self.neck_f = faces(lambda pc, i: pc == "Neck" and co0[self.tris[i][0]][2] > 1.33)
        self.head_f = faces(lambda pc, i: pc == "Head")
        self.leg_f = faces(lambda pc, i: pc in ("LegL", "LegR") and co0[self.tris[i][0]][2] < 0.7)
        self.tail_f = faces(lambda pc, i: pc == "Tail" and co0[self.tris[i][0]][1] > 0.4)
        # the seams: every vertex within 6 mm of another piece's surface at rest
        trees = {}
        for pc in PIECES:
            fs = [i for i, q in enumerate(self.piece) if q == pc]
            trees[pc] = (BVHTree.FromPolygons([tuple(c) for c in co0], [self.tris[i] for i in fs]), fs)
        pairs = []
        roots = {"WingL": (mir(WING[0], 1), 0.13), "WingR": (mir(WING[0], -1), 0.13), "Tail": (TAIL[0], 0.16)}
        for v, pc in enumerate(vpiece):
            for other, (tree, fs) in trees.items():
                if other == pc or not pc:
                    continue
                # a wing lies along the flank and the tail over the rump: only where they are rooted is a seam (the rest is meant to lift away)
                far = [k for k in (pc, other) if k in roots and (Vector(co0[v]) - roots[k][0]).length > roots[k][1]]
                if far:
                    continue
                hit = tree.find_nearest(Vector(co0[v]), 0.006)
                if hit[0] is not None:
                    tri = self.tris[fs[hit[2]]]
                    pairs.append((v, tri, pc, other))
        self.seams = pairs
        self.seam_rest = self._seam_dist(co0)

    def _seam_dist(self, co):
        out = np.zeros(len(self.seams))
        for k, (v, tri, pc, other) in enumerate(self.seams):
            a, b, c = co[tri[0]], co[tri[1]], co[tri[2]]
            n = np.cross(b - a, c - a)
            ln = np.linalg.norm(n)
            out[k] = abs(np.dot(co[v] - a, n / ln)) if ln > 1e-12 else np.linalg.norm(co[v] - a)
        return out

    def run(self):
        co = posed(self.body)

        def hits(fa, fb):
            if not fa or not fb:
                return 0
            ta = BVHTree.FromPolygons([tuple(c) for c in co], [self.tris[f] for f in fa])
            tb = BVHTree.FromPolygons([tuple(c) for c in co], [self.tris[f] for f in fb])
            return len(ta.overlap(tb))
        w = self.wing["L"] + self.wing["R"]
        gap = self._seam_dist(co) - self.seam_rest
        worst = int(np.argmax(gap)) if len(gap) else 0
        return {"wings x body": hits(w, self.body_f), "wings x neck": hits(w, self.neck_f), "wings x head": hits(w, self.head_f),
                "wing x wing": hits(self.wing["L"], self.wing["R"]), "legs x wings": hits(self.leg_f, w), "legs x tail": hits(self.leg_f, self.tail_f),
                "head x body": hits(self.head_f, self.body_f), "neck x wings": 0,
                "seam opens mm": round(float(gap.max()) * 1000, 1) if len(gap) else 0.0,
                "at": "%s/%s" % (self.seams[worst][2], self.seams[worst][3]) if len(gap) else "",
                "low z": round(float(co[:, 2].min()), 4)}


def worse(now, rest):
    return {k: v for k, v in now.items() if isinstance(v, int) and v > rest.get(k, 0) + 2}


def probe(rig, body, bones):
    """Which way each turn moves a bone's vertices (mm), to check the signs the tables use."""
    groups = {g.name: g.index for g in body.vertex_groups}
    for bone in bones:
        gi = groups[bone]
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
        pet_kit.pose(rig, {})
        c0 = posed(body)[idx].mean(0)
        row = []
        for k, axis in enumerate("xyz"):
            turn = [0.0, 0.0, 0.0]
            turn[k] = 0.4
            pet_kit.pose(rig, spec({bone: tuple(turn)}))
            d = (posed(body)[idx].mean(0) - c0) * 1000
            row.append("%s+ (%d,%d,%d)" % (axis, round(d[0]), round(d[1]), round(d[2])))
        print("PROBE", bone, len(idx), "verts", " ".join(row), flush=True)
    pet_kit.pose(rig, {})


# ---------- review renders, inside this file's scene (lights and camera made for them, removed before saving) ----------
REVIEW_OBJS = []
REVIEW_HIDDEN = []


def review_stage():
    for name, e, rot in (("RevKey", 2.4, (55, 0, -35)), ("RevFill", 0.8, (70, 0, 140)), ("RevRim", 1.0, (120, 0, 20))):
        l = bpy.data.lights.new(name, "SUN")
        l.energy = e
        o = bpy.data.objects.new(name, l)
        GAME.objects.link(o)
        o.rotation_euler = [math.radians(v) for v in rot]
        REVIEW_OBJS.append(o)
    for o in scene.collection.objects:          # the file's own lights stay out of the review
        if o.type == "LIGHT" and not o.hide_render:
            o.hide_render = True
            REVIEW_HIDDEN.append(o)
    cam = bpy.data.objects.new("RevCam", bpy.data.cameras.new("RevCam"))
    cam.data.lens = 60
    GAME.objects.link(cam)
    REVIEW_OBJS.append(cam)
    scene.camera = cam
    w = bpy.data.worlds.new("RevWorld")
    REVIEW_OBJS.append(w)
    scene.world = w
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.45, 0.5, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except TypeError:
        pass
    scene.cycles.samples = 24
    scene.view_settings.view_transform = "Standard"
    return cam


def glow_look(glows):
    for g in glows:
        h = g.name.split("_Glow_")[1][:6]
        m = bpy.data.materials.new("Rev" + h)
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        c = pet_kit.rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        b.inputs["Emission Strength"].default_value = 1.5
        g.data.materials.clear()
        g.data.materials.append(m)


def shot(cam, path, view, size=480):
    d = Vector(view[:3]).normalized()
    t = Vector(view[4])
    cam.location = t + d * view[3]
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


T = (0, 0.15, 1.05)
VIEWS = [(0, -1, 0.1, 5.2, T), (0.65, -0.7, 0.25, 5.2, T), (1, 0, 0.08, 5.2, T), (0, 1, 0.12, 5.2, T), (-0.62, 0.62, 0.45, 5.2, T),
         (0.55, -0.8, 0.15, 1.8, (0, -0.55, 1.95))]
GAME_CAM = (0.5, 0.75, 0.55, 7.0, (0, 0.1, 1.1))       # where a player's camera sees its pet: behind and above


def use_asset_maps():
    """The body's maps are the files in assets/ (identical to what the old FBX carried): the FBX embeds them from there."""
    for name, path in MAPS.items():
        img = bpy.data.images[name]
        if img.packed_file:
            img.unpack(method="REMOVE")
        img.filepath = path
        img.reload()


if __name__ == "__main__":
    solids, glows = gather()
    rig = skeleton()
    body = bind_all(solids, glows, rig)
    glow_list = list(glows.values())
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    print("BODY", body.name, "tris", tris, "glows", {g.name: sum(len(p.vertices) - 2 for p in g.data.polygons) for g in glow_list}, flush=True)
    print("BONES", len(rig.data.bones), [b.name for b in rig.data.bones], flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + glow_list for v in o.data.vertices),
          "UNWEIGHTED", sum(1 for o in [body] + glow_list for v in o.data.vertices if not v.groups), flush=True)
    zs = [v.co.z for o in [body] + glow_list for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    bottom = min(lo, -0.025)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE (box middle with the RootPart, down to the feet)", round((hi + bottom) / 2 - lo, 4), flush=True)
    for name in ("Body", "Neck1", "Head", "Crest", "WingL1", "WingL4", "LegL1", "FootL", "Tail1", "Tail3"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    probe(rig, body, ("Neck2", "Head", "WingL1", "WingL3", "LegL1", "LegL3", "Tail2", "Crest"))

    chk = Checker(body)
    print("SEAM PAIRS", len(chk.seams), flush=True)
    pet_kit.pose(rig, {})
    rest = chk.run()
    print("POSE Rest", rest, flush=True)
    walk = find_walk(rig)
    print("WALK fit worst", max(r[1] for r in walk), flush=True)
    print("WALK = { " + ", ".join("{ %g, %g, %g }" % r[0] for r in walk) + " }", flush=True)
    crouch, cfit = find_crouch(rig)
    print("CROUCH fit", cfit, "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in (v[:3] + (tuple(v[3]) if len(v) > 3 else ())))) for b, v in sorted(crouch.items())) + " }", flush=True)
    lib = pose_library(walk, crouch)
    for name, sp in lib.items():
        pet_kit.pose(rig, sp)
        r = chk.run()
        print("POSE", name, worse(r, rest) or "clean", "seam opens mm", r["seam opens mm"], r["at"], "low z", r["low z"], flush=True)
    # the foot on the ground through the walk: its lowest point, every step, against standing
    groups = {g.name: g.index for g in body.vertex_groups}
    feet = {t: [v.index for v in body.data.vertices if any(g.group == groups["Foot" + t] and g.weight > 0.5 for g in v.groups)] for t in "LR"}
    pet_kit.pose(rig, {})
    co = posed(body)
    stand = {t: float(co[feet[t], 2].min()) for t in "LR"}
    planted = []
    for k in range(WALK_N):
        g = k / WALK_N
        pet_kit.pose(rig, spec(walk_table(walk, g)))
        co = posed(body)
        for t, lead in (("L", 0.0), ("R", 0.5)):
            if ((g + lead) % 1.0) < WALK_DUTY:
                planted.append(abs(float(co[feet[t], 2].min()) - stand[t]))
    print("WALK planted foot off the ground, worst mm", round(max(planted) * 1000, 2), "stand", {t: round(v, 4) for t, v in stand.items()}, flush=True)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    # the transitions the game blends through
    lib_r = dict(lib, Rest={})
    for na, nb in (("Rest", "Open"), ("Open", "FlapUp"), ("FlapUp", "FlapDown"), ("Rest", "FlapUp"), ("Rest", "Halo"), ("Rest", "HopAir"), ("Rest", "Preen"), ("Crouch", "HopAir")):
        bad = {}
        seam = 0.0
        for k in range(11):
            a, b = lib_r[na], lib_r[nb]
            mixed = {}
            for bone in set(a) | set(b):
                qa = Matrix.Rotation(math.radians(a[bone][1]), 3, Vector(a[bone][0])).to_quaternion() if bone in a else Matrix.Identity(3).to_quaternion()
                qb = Matrix.Rotation(math.radians(b[bone][1]), 3, Vector(b[bone][0])).to_quaternion() if bone in b else Matrix.Identity(3).to_quaternion()
                ma = Vector(a[bone][2]) if bone in a else Vector((0, 0, 0))
                mb = Vector(b[bone][2]) if bone in b else Vector((0, 0, 0))
                axis, angle = qa.slerp(qb, k / 10).to_axis_angle()
                mixed[bone] = (tuple(axis), math.degrees(angle), tuple(ma.lerp(mb, k / 10)))
            pet_kit.pose(rig, mixed)
            r = chk.run()
            seam = max(seam, r["seam opens mm"])
            for key, v in worse(r, rest).items():
                bad[key] = max(bad.get(key, 0), v)
        print("TRANSITION", na, "->", nb, bad or "clean", "seam opens mm", seam, flush=True)
    if "probeonly" in ARGS:
        raise SystemExit(0)

    # renders: the rested crane, its poses and its walk
    os.makedirs(REVIEW, exist_ok=True)
    cam = review_stage()
    use_asset_maps()
    saved_mats = {g.name: list(g.data.materials) for g in glow_list}
    glow_look(glow_list)
    pet_kit.pose(rig, {})
    if "shots" in ARGS:
        for k, v in enumerate(VIEWS):
            shot(cam, os.path.join(REVIEW, "rest_%d.png" % k), v)
        side = (1, 0.0, 0.1, 5.4, (0, 0.1, 1.0))
        three = (0.62, -0.72, 0.28, 5.6, (0, 0.1, 1.05))
        above = (0.45, 0.55, 0.7, 6.2, (0, 0.1, 1.15))
        for name, view in (("Open", above), ("FlapUp", three), ("FlapDown", three), ("Glide", above), ("Halo", three), ("Halo", (0, -1, 0.15, 5.6, (0, 0.1, 1.2))),
                           ("Crouch", side), ("HopAir", three), ("Preen", three), ("Glance", (0.4, -0.9, 0.2, 2.6, (0, -0.4, 1.7))), ("Bow", side), ("Ruffle", three),
                           ("FlapUp", GAME_CAM), ("Glide", GAME_CAM), ("Open", (0.35, -0.9, 0.55, 2.4, (0.25, -0.15, 1.25))), ("Glide", (1, 0.05, 0.05, 5.2, (0, 0.2, 1.1))),
                           ("Walk2", (1, -0.25, 0.1, 2.2, (0.1, 0.05, 0.85))), ("Walk6", (1, -0.25, 0.1, 2.2, (0.1, 0.05, 0.85))), ("Preen", (0.6, -0.7, 0.3, 2.4, (0, -0.3, 1.3)))):
            pet_kit.pose(rig, lib[name])
            shot(cam, os.path.join(REVIEW, "pose%s_%d.png" % (name, abs(hash(view)) % 1000)), view, 420)
        # close looks where pieces meet: the tail's root as it bows, the neck's base as it preens, the hips and wing roots in flight
        for name, view, tag in (("Bow", (-0.55, 0.8, 0.45, 1.6, (0, 0.3, 1.15)), "tailroot"), ("Preen", (-0.3, -0.9, 0.2, 1.4, (0, -0.33, 1.25)), "neckbase"),
                                ("Glide", (0.6, 0.2, -0.75, 2.0, (0.05, 0.15, 1.0)), "hips"), ("FlapUp", (0.2, -0.6, 0.75, 2.0, (0.2, -0.15, 1.25)), "wingroot"),
                                ("FlapDown", (0.3, -0.9, -0.2, 2.0, (0.2, -0.15, 1.2)), "wingroot2"), ("Crouch", (1, -0.2, 0.0, 1.8, (0.1, 0.05, 0.6)), "heels")):
            pet_kit.pose(rig, lib[name])
            shot(cam, os.path.join(REVIEW, "close_%s.png" % tag), view, 420)
        for k in range(8):
            pet_kit.pose(rig, lib["Walk%d" % k])
            shot(cam, os.path.join(REVIEW, "walk%d.png" % k), side, 360)
        pet_kit.pose(rig, {})
    for g in glow_list:
        g.data.materials.clear()
        for m in saved_mats[g.name]:
            g.data.materials.append(m)
    for m in [m for m in bpy.data.materials if m.name.startswith("Rev") and m.users == 0]:
        bpy.data.materials.remove(m)
    for o in REVIEW_HIDDEN:
        o.hide_render = False
    for o in REVIEW_OBJS:
        if isinstance(o, bpy.types.Object):
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            bpy.data.worlds.remove(o)

    if STAGE == "all":
        pet_kit.pose(rig, {})
        for g in glow_list:
            if not g.data.uv_layers:
                g.data.uv_layers.new(name="UVMap")
        # the FBX: the game reads its pieces by name, so for the export the bake source's own "SpiritCrane_Body" steps aside
        aside = []
        for block in (bpy.data.objects, bpy.data.meshes):
            other = block.get(N + "Body")
            if other is not None and other is not body and other is not body.data:
                other.name = N + "Body_Aside"
                aside.append((other, N + "Body"))
        body.name = body.data.name = N + "Body"
        fbx = pet_kit.export_fbx(rig, body, glow_list)
        raw = open(fbx, "rb").read()
        fixed = raw.replace(b"/Users/ivan/", b"/Users/user/")
        if fixed != raw:
            open(fbx, "wb").write(fixed)
        print("FBX", fbx, os.path.getsize(fbx) // 1024, "KB", flush=True)
        body.name = body.data.name = N + "BodyRigged"
        for other, name in aside:
            other.name = name
        for g in glow_list:
            g.data.materials.clear()
            for m in saved_mats[g.name]:
                g.data.materials.append(m)
        for name in MAPS:
            bpy.data.images[name].pack()
        # the file: its view layer showing the rigged crane; the sources kept beside it, excluded
        path = pet_kit.save_blend()
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("DONE", flush=True)

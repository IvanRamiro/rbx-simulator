"""Yggdrasil's island meshes: the atlas, the underside the World Tree's roots hold, and the great
root that winds down the south cliffs to the Root of the Island's cradle.

The underside is the Starting Island's stacked strata at Yggdrasil's scale. Seven roots come up out
of the meadow near the rim, grip the edge and run down the strata's stepped corners to the taproot
under the island's centre. The underside's lowest point stays above world Y 75: the PDS kit lies
below (its highest part at Y 69.5).

    import ygg_meshes
    objs, img, report = ygg_meshes.build()    # in Blender: the tree and the underside
    ygg_meshes.export(objs, img)              # assets/world/Yggdrasil/Yggdrasil_Island.fbx

(The hub's buildings, paving and lamps are the celestial city's: hub_celestial.py and hub_ground.py.)
"""
import math

import bpy

import worldlib as W
import ygg_island as Y
import start_meshes as M

TAU = 2 * math.pi
LOWEST = -124.0      # nothing below this (world Y 76)

# ---------- atlas ----------
def ash_bark(u, v):
    """Pale, silvered ash bark: deep vertical fissures across u, moss toward the foot (v 0)."""
    a = u * TAU
    fissure = abs(math.sin(a * 9 + 1.8 * W.fbm(math.cos(a) * 3, math.sin(a) * 3 + v * 2, seed=201, octaves=3)))
    grain = W.fbm(math.cos(a) * 11 + v * 6, math.sin(a) * 11, seed=203, octaves=3)
    ridge = W.smoothstep(0.18, 0.7, fissure)
    base = [0.21 + 0.27 * ridge, 0.19 + 0.25 * ridge, 0.17 + 0.21 * ridge]
    moss = (1 - W.smoothstep(0.0, 0.22, v)) * (0.6 + 0.4 * grain)
    green = (0.25, 0.36, 0.18)
    return tuple(max(0.0, min(1.0, base[i] * (1 - moss * 0.6) + green[i] * moss * 0.6 + 0.035 * grain)) for i in range(3))


def root_bark(u, v):
    a = u * TAU
    fissure = abs(math.sin(a * 5 + 1.5 * W.fbm(math.cos(a) * 2, math.sin(a) * 2 + v * 3, seed=211, octaves=3)))
    g = W.fbm(math.cos(a) * 8 + v * 4, math.sin(a) * 8, seed=213, octaves=3)
    r = W.smoothstep(0.2, 0.8, fissure)
    c = (0.2 + 0.18 * r, 0.17 + 0.15 * r, 0.14 + 0.11 * r)
    return tuple(max(0.0, c[i] + 0.04 * g + (0.03 if i == 1 else 0)) for i in range(3))


def canopy(u, v):
    """Left half: deep jade leaves, shadowed underneath (v 0) to sunlit on top (v 1). Right half:
    the same leaves gilded toward the top, for the pads that catch the most sun."""
    g = W.fbm(u * 23, v * 7, seed=221, octaves=3)
    if u < 0.5:
        c = (0.11 + 0.24 * v, 0.27 + 0.36 * v, 0.15 + 0.15 * v)
    else:
        gold = W.smoothstep(0.55, 1.0, v)
        c = (0.12 + 0.22 * v + 0.45 * gold, 0.28 + 0.32 * v + 0.18 * gold, 0.14 + 0.1 * v)
    return tuple(max(0.0, min(1.0, c[i] + 0.05 * g)) for i in range(3))


STRIPS = [(176, M.strata_colour), (64, ash_bark), (48, M.moss_colour), (64, M.stone_colour), (96, canopy), (64, root_bark)]
BAND_NAMES = ["STRATA", "BARK", "MOSS", "STONE", "CANOPY", "ROOT"]


def build_atlas():
    img, bands = W.atlas_image("Yggdrasil_Atlas", 512, STRIPS)
    return img, {name: bands[i] for i, name in enumerate(BAND_NAMES)}


# ---------- underside: stacked strata ----------
# (scale of the rim outline, x/z offset, top y, bottom y)
SLABS = [(1.0, (0, 0), -1.6, -30.0), (0.82, (-12, 8), -26.0, -56.0), (0.64, (16, -6), -50.0, -80.0),
         (0.46, (20, 14), -74.0, -98.0), (0.3, (12, 8), -94.0, -104.0)]
CRAG = 1.2           # the crags under each slab, relative to the Starting Island's
SEG = 180


def slab(coll, mat, band, name, scale, offset, top, bottom, seed):
    """One rock slab: a rim-shaped plate with a cliff wall and a craggy underside."""
    v0, v1 = band
    depth = -SLABS[-1][3]
    vt, vb = v0 + (v1 - v0) * (-top / depth) * 0.9, v0 + (v1 - v0) * (-bottom / depth) * 0.9
    verts, faces, uvs = [], [], []
    rings = []
    for layer, (y, inset, jag) in enumerate(((top, 0.0, 0.0), (top - 0.35 * (top - bottom), 2.4, 0.6), (bottom, 12.0, 1.0))):
        ring = []
        for i in range(SEG):
            th = TAU * i / SEG
            lobe = 12.0 * W.fbm(math.cos(th) * 1.6 + seed, math.sin(th) * 1.6 - seed, seed=seed + 3, octaves=2)
            R = Y.rim(th) * scale + (0.8 if scale == 1.0 and layer == 0 else (lobe if scale < 1.0 else 0))
            n = W.fbm(math.cos(th) * 6 + seed, math.sin(th) * 6 - seed, seed=seed, octaves=3)
            r = max(2.0, R - inset * (1 + 1.4 * abs(n)) + 3.5 * n * (layer > 0))
            yy = y - jag * (7.0 * abs(W.fbm(math.cos(th) * 13 - seed, math.sin(th) * 13, seed=seed + 5, octaves=3)) ** 1.3)
            ring.append(len(verts))
            verts.append(W.rb(offset[0] + math.cos(th) * r, yy, offset[1] + math.sin(th) * r))
        rings.append(ring)
    for (ra, rb_), (va, vb_) in zip(zip(rings, rings[1:]), ((vt, vt + (vb - vt) * 0.4), (vt + (vb - vt) * 0.4, vb))):
        for i in range(SEG):
            j = (i + 1) % SEG
            faces.append([ra[i], rb_[i], rb_[j], ra[j]])
            uvs.append([(6 * i / SEG, va), (6 * i / SEG, vb_), (6 * (i + 1) / SEG, vb_), (6 * (i + 1) / SEG, va)])
    under = [rings[2]]
    for level, (frac, drop) in enumerate(((0.62, 4.5 * CRAG), (0.28, 7.0 * CRAG))):
        ring = []
        for i in range(SEG):
            th = TAU * i / SEG
            base = verts[rings[2][i]]
            cx, cy = offset[0], -offset[1]
            crag = abs(W.fbm(math.cos(th) * 8 + level * 3 + seed, math.sin(th) * 8, seed=seed + 9, octaves=3))
            p = (base.x - cx) * frac + cx, (base.y - cy) * frac + cy
            ring.append(len(verts))
            verts.append(W.Vector((p[0], p[1], max(LOWEST + 6, bottom - drop - 9.0 * CRAG * crag ** 1.6))))
        under.append(ring)
    vu = min(v1, vb + 0.03)
    for ra, rb_ in zip(under, under[1:]):
        for i in range(SEG):
            j = (i + 1) % SEG
            faces.append([ra[j], ra[i], rb_[i], rb_[j]])
            uvs.append([(6 * (i + 1) / SEG, vb), (6 * i / SEG, vb), (6 * i / SEG, vu), (6 * (i + 1) / SEG, vu)])
    mid = len(verts)
    verts.append(W.rb(offset[0], max(LOWEST + 6, bottom - 11.0 * CRAG), offset[1]))
    for i in range(SEG):
        j = (i + 1) % SEG
        faces.append([under[-1][j], under[-1][i], mid])
        uvs.append([(6 * i / SEG, vu), (6 * (i + 1) / SEG, vu), (6 * (i + 0.5) / SEG, vu)])
    top_mid = len(verts)
    verts.append(W.rb(offset[0], top, offset[1]))
    for i in range(SEG):
        faces.append([rings[0][i], rings[0][(i + 1) % SEG], top_mid])
        uvs.append([(0, vt), (0, vt), (0, vt)])
    return W.mesh_object(name, verts, faces, coll, uvs=uvs, material=mat)


def build_crust(coll, mat, bands):
    return [slab(coll, mat, bands["STRATA"], "YG_Slab%d" % k, sc, off, top, bot, 130 + 7 * k)
            for k, (sc, off, top, bot) in enumerate(SLABS)]


def corner_r(k, theta):
    """How far out slab k's wall can reach along a bearing (its outline wanders up to ~6 studs)."""
    sc, (ox, oz), _, _ = SLABS[k]
    return sc * Y.rim(theta) + ox * math.cos(theta) + oz * math.sin(theta) + 6.0


# ---------- the roots that hold the island ----------
# Clear of the bridges' aprons (40 wide at bearings 177, -131, -100, -76.5, -55), the great root's cove (55-90) and the Merchants'
# Terrace's shops: the hub's redesign (2026-11-15) moved root 0 from bearing 0 to 14 (the terrace's south shoulder), root 4 from
# -124 to -121 (off the Jade Grove apron) and root 6 from -30 to -18 (between the Market and Buy & Sell, on the terrace's rim).
GRIP_BEARINGS = (14, 45, 110, 152, -121, -113, -18)
TAPROOT = [(0, -86, 0), (6, -100, -4), (-4, -110, 5), (2, -118, 1)]


def grip_points(bearing):
    th = math.radians(bearing)
    R = Y.rim(th)
    def at(r, y, swing=0.0):
        a = th + swing
        return (math.cos(a) * r, y, math.sin(a) * r)
    # under the meadow until past the Ring Road (its outer edge 236; the rim is at least 248 there), breaking the surface about 9
    # studs in from the edge, over the lip and down the cliff (the roots crossed the meadow from R - 62 before the redesign)
    pts = [at(R - 30, -24), at(R - 18, -18.5), at(R - 9, -12.5), at(R - 3, -6.2), at(R + 2, -3.2), at(R + 6.5, -12), at(R + 4, -32, 0.01)]
    for k in range(1, len(SLABS)):
        _, _, _, bottom = SLABS[k]
        pts.append(at(corner_r(k, th) + 7, bottom - 3, 0.02 * k))
    pts.append(at(40, -104, 0.12))
    pts.append(at(14, -108, 0.2))
    return pts


def build_grip_roots(coll, mat, bands):
    return [W.tube("YG_GripRoot%d" % k, coll, [W.rb(*p) for p in grip_points(b)], lambda t: 11.0 - 6.0 * t ** 0.7,
                   14, mat, bands["ROOT"], per=6, uv_repeat=2.0, wobble=0.22, seed=300 + k)
            for k, b in enumerate(GRIP_BEARINGS)]


def build_taproot(coll, mat, bands):
    return W.tube("YG_Taproot", coll, [W.rb(*p) for p in TAPROOT], lambda t: 27 - 24 * t ** 0.9, 20, mat, bands["ROOT"],
                  per=6, uv_repeat=3.0, wobble=0.3, seed=330)


# ---------- the great root down to the Root of the Island ----------
# (bearing, radius, y) along the root's centre line, from where it rises out of the south meadow
PATH_ROOT_POLAR = [(90, 230, -3.0), (89, 246, -2.2), (85, 260, -8), (79, 266, -19), (72, 264, -30), (66, 257, -40),
                   (61, 241, -50), (57, 223, -60), (55, 206, -70), (57, 191, -78), (59, 182, -84)]
CRADLE_POLAR = (60, 177, -86.5)        # the woven floor's top
RELIC_RISE = 4.5                        # the relic floats this far over the floor


def polar3(b, r, y):
    a = math.radians(b)
    return (math.cos(a) * r, y, math.sin(a) * r)


PATH_ROOT = [polar3(*p) for p in PATH_ROOT_POLAR]
CRADLE_FLOOR = polar3(*CRADLE_POLAR)
RELIC = (CRADLE_FLOOR[0], CRADLE_FLOOR[1] + RELIC_RISE, CRADLE_FLOOR[2])


def path_root_radius(t):
    return 6.0 + (3.4 - 6.0) * t ** 0.8


def build_path_root(coll, mat, bands):
    return W.tube("YG_PathRoot", coll, [W.rb(*p) for p in PATH_ROOT], path_root_radius, 14, mat, bands["ROOT"],
                  per=8, uv_repeat=1.5, wobble=0.18, seed=341)


def build_cradle_roots(coll, mat, bands):
    """Roots that hang from the strata above the cradle and curl round it into a bowl."""
    cx, cy, cz = CRADLE_FLOOR
    objs = []
    for k in range(5):
        a0 = TAU * k / 5 + 0.4
        pts = [(cx + math.cos(a0) * 9, cy + 40, cz + math.sin(a0) * 9)]   # out of the strata above
        for y, rad, twist in ((cy + 19, 12, 0.4), (cy + 9, 8.5, 0.9), (cy + 0.5, 7.5, 1.4)):
            a = a0 + twist
            pts.append((cx + math.cos(a) * rad, y, cz + math.sin(a) * rad))
        a = a0 + 2.6
        pts.append((cx + math.cos(a) * 11.5, cy - 4.5, cz + math.sin(a) * 11.5))
        pts.append((cx + math.cos(a + 0.25) * 15, cy + 5, cz + math.sin(a + 0.25) * 15))
        objs.append(W.tube("YG_CradleRoot%d" % k, coll, [W.rb(*p) for p in pts], lambda t: 6.0 - 4.2 * t ** 0.8, 12, mat,
                           bands["ROOT"], per=6, uv_repeat=1.0, wobble=0.25, seed=350 + k))
    return objs


def shelf_placements(count=16):
    """Island-local transforms for the root shelves (SI_RootShelf): evenly down the great root, each on
    its top, its open side turned off the root's line."""
    curve = W.catmull([W.rb(*p) for p in PATH_ROOT], 16)
    lengths = [0.0]
    for a, b in zip(curve, curve[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    out = []
    for i in range(count):
        target = lengths[-1] * (i + 0.5) / count
        k = next(j for j in range(len(lengths)) if lengths[j] >= target)
        p = curve[k]
        radius = path_root_radius(lengths[k] / lengths[-1])
        tangent = (curve[min(k + 1, len(curve) - 1)] - curve[max(k - 1, 0)]).normalized()
        out.append(((p.x, p.z + radius * 0.85, -p.y), math.atan2(tangent.y, tangent.x)))
    return out


# ---------- build and export ----------
def clearance_report(objs):
    """How close the great root and the cradle come to the strata (studs between surfaces)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    crust = [BVHTree.FromObject(o, dg) for o in objs if o.name.startswith("YG_Slab")]
    curve = W.catmull([W.rb(*p) for p in PATH_ROOT], 16)
    worst = 1e9
    for i, p in enumerate(curve):
        r = path_root_radius(i / (len(curve) - 1))
        for tree in crust:
            hit = tree.find_nearest(p)
            if hit[0] is not None:
                worst = min(worst, hit[3] - r)
    lowest = min((o.matrix_world @ v.co).z for o in objs for v in o.data.vertices)
    return {"path_root_gap": round(worst, 2), "lowest": round(lowest, 2)}


def build():
    import ygg_tree
    img, bands = build_atlas()
    mat = W.textured_material("Yggdrasil_Mat", img)
    root = W.collection(Y.NAME)
    under = W.collection("YG_Underside", root)
    tree = W.collection("YG_Tree", root)
    W.clear_collection(under)
    W.clear_collection(tree)
    objs = build_crust(under, mat, bands) + build_grip_roots(under, mat, bands)
    objs += [build_taproot(under, mat, bands), build_path_root(under, mat, bands)] + build_cradle_roots(under, mat, bands)
    objs += ygg_tree.build(tree, mat, bands)
    return objs, img, clearance_report(objs)


# ---------- Roblox-ready (the hub's redesign, 2026-11-15: every re-exported piece passes the asset QA's roblox profile) ----------
CHANGED_BY_REDESIGN = ["YG_Slab%d" % k for k in range(len(SLABS))] + ["YG_GripRoot%d" % k for k in range(len(GRIP_BEARINGS))]


def roblox_ready(objs):
    """Folds every face's UVs into 0-1 (the atlas tiles: a whole-number shift changes nothing; a face across a tile edge is moved
    to fit), gives faces sampled at one point (the slabs' hidden tops, the roots' tips) a small map of their own inside their
    strip, and winds the closed slabs outward."""
    import bmesh
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uv = bm.loops.layers.uv.active
        if o.name.startswith("YG_Slab"):
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            us = [l[uv].uv.x for l in f.loops]
            vs = [l[uv].uv.y for l in f.loops]
            area = sum(us[i] * vs[(i + 1) % len(us)] - us[(i + 1) % len(us)] * vs[i] for i in range(len(us)))
            if abs(area) < 1e-9:
                n = f.normal
                ax = max(range(3), key=lambda i: abs(n[i]))
                a, b = [i for i in range(3) if i != ax]
                pa = [l.vert.co[a] for l in f.loops]
                pb = [l.vert.co[b] for l in f.loops]
                span = max(max(pa) - min(pa), max(pb) - min(pb), 1e-6)
                vc = min(max(sum(vs) / len(vs), 0.006), 0.994)
                for l, x, y in zip(f.loops, pa, pb):
                    l[uv].uv = (0.5 + (x - min(pa)) / span * 0.01, vc - 0.005 + (y - min(pb)) / span * 0.01)
                continue
            for axis, vals in ((0, us), (1, vs)):
                off = math.floor(min(vals) + 1e-6)
                if max(vals) - off > 1.0:
                    off = max(vals) - 1.0
                for l in f.loops:
                    c = l[uv].uv
                    c[axis] = min(max(c[axis] - off, 0.0), 1.0)
        bm.to_mesh(o.data)
        bm.free()


def export_underside(objs, path=None):
    """assets/world/Yggdrasil/Yggdrasil_Underside.fbx: only the pieces the redesign changed (the strata on the new rim and the
    re-routed grip roots), Roblox-ready, at the island's centre (anchor YG_Anchor), with no texture: in Studio they take the
    Yggdrasil atlas the underside already has (TextureID), so nothing is uploaded."""
    pieces = [o for o in objs if o.name in CHANGED_BY_REDESIGN]
    roblox_ready(pieces)
    path = path or W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Underside.fbx"
    W.export_batch(pieces, path, image=None, anchor_name="YG_Anchor")
    return path, pieces


def export(objs, img):
    folder = W.REPO + "/assets/world/Yggdrasil"
    W.export_batch(objs, folder + "/Yggdrasil_Island.fbx", image=img, anchor_name="YG_Anchor")
    return folder

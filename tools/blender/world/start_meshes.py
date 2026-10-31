"""Starting Island meshes: the stratified underside, hanging spires, the Root of the Island
root bundle with its relic cradle, the root ledges that spiral down to it, and the island atlas."""
import bpy, math, os, random
from mathutils import Vector
import worldlib as W
import start_island as S

TAU = 2 * math.pi
DEPTH = 96            # underside depth below the rim
TIP = (10, 8)         # where the underside's lowest point sits (x, z)
RIM_DROP = 1.6        # the underside's top ring sits this far below the terrain rim


# ---------- atlas ----------
def _tile_noise(u, v, freq, seed):
    # horizontally periodic fbm: sample on a circle in u
    a = u * TAU
    return W.fbm(math.cos(a) * freq + 11, math.sin(a) * freq + v * freq * 2.2, seed=seed, octaves=4)


def strata_colour(u, v):
    # v: 0 = rim (top) -> 1 = deepest tip
    n = _tile_noise(u, v, 2.6, 5)
    fine = _tile_noise(u, v * 4, 7.0, 9)
    if v < 0.05:  # dark soil band under the grass lip, with root threads
        base = (0.24, 0.17, 0.11)
        return tuple(max(0, c + 0.04 * n) for c in base)
    bands = [(0.48, 0.47, 0.5), (0.4, 0.41, 0.46), (0.52, 0.49, 0.45), (0.36, 0.37, 0.43), (0.45, 0.45, 0.5)]
    k = (v * 9 + 0.4 * n) % len(bands)
    a, b = bands[int(k)], bands[(int(k) + 1) % len(bands)]
    t = W.smoothstep(0.75, 1.0, k - int(k))
    c = [a[i] + (b[i] - a[i]) * t for i in range(3)]
    dark = 0.18 * v  # deeper rock is darker and cooler
    return tuple(max(0, min(1, c[i] * (1 - dark) + 0.05 * fine - (0.02 if i == 0 else 0))) for i in range(3))


def bark_colour(u, v):
    g = _tile_noise(u, v * 0.3, 9.0, 31)
    return (0.33 + 0.06 * g, 0.24 + 0.05 * g, 0.16 + 0.03 * g)


def moss_colour(u, v):
    g = _tile_noise(u, v, 5.0, 41)
    return (0.24 + 0.05 * g, 0.42 + 0.07 * g, 0.2 + 0.03 * g)


def stone_colour(u, v):
    g = _tile_noise(u, v, 6.0, 51)
    return (0.68 + 0.05 * g, 0.66 + 0.05 * g, 0.62 + 0.04 * g)


def foliage_colour(u, v):
    # left half: greens (shadow -> sun), right half: blossom pinks
    if u < 0.5:
        return (0.18 + 0.22 * v, 0.36 + 0.26 * v, 0.17 + 0.12 * v)
    return (0.62 + 0.3 * v, 0.38 + 0.3 * v, 0.46 + 0.26 * v)


STRIPS = [(176, strata_colour), (64, bark_colour), (48, moss_colour), (64, stone_colour), (96, foliage_colour), (64, bark_colour)]
STRATA, BARK, MOSS, STONE, FOLIAGE, TRUNK = range(6)


def build_atlas():
    img, bands = W.atlas_image("StartingIsland_Atlas", 512, STRIPS)
    return img, bands


# ---------- underside: stacked rock slabs held by the island's roots ----------
# (scale of the rim outline, x/z offset, top y, bottom y) for each sedimentary slab
SLABS = [(1.0, (0, 0), -1.6, -15.0), (0.82, (-6, 4), -13.0, -27.0), (0.64, (8, -3), -24.0, -37.0), (0.46, (10, 7), -34.0, -46.0), (0.3, (6, 4), -43.0, -52.0)]
CRUST_DEPTH = 52.0
RELIC = (12, -80, 6)          # Root of the Island relic, floating in the cradle (island-local)
CRADLE_FLOOR = (12, -84.5, 6)  # top of the woven-root floor players stand on beside the relic
COLUMN = (8, 5)               # braided root column axis (x, z)


def slab(coll, mat, bands, name, scale, offset, top, bottom, seed):
    """One rock slab: a rim-shaped plate with a cliff wall and a craggy underside."""
    seg = 96
    v0, v1 = bands[STRATA]
    vt, vb = v0 + (v1 - v0) * (-top / CRUST_DEPTH) * 0.9, v0 + (v1 - v0) * (-bottom / CRUST_DEPTH) * 0.9
    verts, faces, uvs = [], [], []
    rings = []
    for layer, (y, inset, jag) in enumerate(((top, 0.0, 0.0), (top - 0.35 * (top - bottom), 1.2, 0.6), (bottom, 7.0, 1.0))):
        ring = []
        for i in range(seg):
            th = TAU * i / seg
            lobe = 7.0 * W.fbm(math.cos(th) * 1.6 + seed, math.sin(th) * 1.6 - seed, seed=seed + 3, octaves=2)
            R = S.rim(th) * scale + (0.6 if scale == 1.0 and layer == 0 else (lobe if scale < 1.0 else 0))
            n = W.fbm(math.cos(th) * 4 + seed, math.sin(th) * 4 - seed, seed=seed, octaves=3)
            r = max(2.0, R - inset * (1 + 1.4 * abs(n)) + 2.2 * n * (layer > 0))
            yy = y - jag * (5.0 * abs(W.fbm(math.cos(th) * 9 - seed, math.sin(th) * 9, seed=seed + 5, octaves=3)) ** 1.3)
            ring.append(len(verts))
            verts.append(W.rb(offset[0] + math.cos(th) * r, yy, offset[1] + math.sin(th) * r))
        rings.append(ring)
    for (ra, rb_), (va, vb_) in zip(zip(rings, rings[1:]), ((vt, vt + (vb - vt) * 0.4), (vt + (vb - vt) * 0.4, vb))):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([ra[i], rb_[i], rb_[j], ra[j]])
            uvs.append([(3 * i / seg, va), (3 * i / seg, vb_), (3 * (i + 1) / seg, vb_), (3 * (i + 1) / seg, va)])
    # craggy underside: two inner rings hanging lower, with stalactite-like crags
    under = [rings[2]]
    for level, (frac, drop) in enumerate(((0.62, 4.5), (0.28, 7.0))):
        ring = []
        for i in range(seg):
            th = TAU * i / seg
            base = verts[rings[2][i]]
            cx, cy = offset[0], -offset[1]
            crag = abs(W.fbm(math.cos(th) * 6 + level * 3 + seed, math.sin(th) * 6, seed=seed + 9, octaves=3))
            p = (base.x - cx) * frac + cx, (base.y - cy) * frac + cy
            ring.append(len(verts))
            verts.append(W.Vector((p[0], p[1], bottom - drop - 9.0 * crag ** 1.6)))
        under.append(ring)
    for ra, rb_ in zip(under, under[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([ra[j], ra[i], rb_[i], rb_[j]])
            uvs.append([(3 * (i + 1) / seg, vb), (3 * i / seg, vb), (3 * i / seg, min(v1, vb + 0.03)), (3 * (i + 1) / seg, min(v1, vb + 0.03))])
    mid = len(verts)
    verts.append(W.rb(offset[0], bottom - 11.0, offset[1]))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([under[-1][j], under[-1][i], mid])
        uvs.append([(3 * i / seg, min(v1, vb + 0.03)), (3 * (i + 1) / seg, min(v1, vb + 0.03)), (3 * (i + 0.5) / seg, min(v1, vb + 0.03))])
    top_mid = len(verts)
    verts.append(W.rb(offset[0], top, offset[1]))
    for i in range(seg):
        faces.append([rings[0][i], rings[0][(i + 1) % seg], top_mid])
        uvs.append([(0, vt), (0, vt), (0, vt)])
    return W.mesh_object(name, verts, faces, coll, uvs=uvs, material=mat)


def build_crust(coll, mat, bands):
    return [slab(coll, mat, bands, "SI_Slab%d" % k, sc, off, top, bot, 30 + 7 * k) for k, (sc, off, top, bot) in enumerate(SLABS)]


def root_radius(r0, r1):
    return lambda t: r0 + (r1 - r0) * t ** 0.8


def build_roots(coll, mat, bands):
    """Six colossal roots braid into a column under the island and splay into the relic cradle."""
    band = bands[BARK]
    objs = []
    cx, cz = COLUMN
    rx, ry, rz = RELIC
    for k in range(6):
        a0 = TAU * k / 6 + 0.3
        R = S.rim(a0)
        start = (cx + math.cos(a0) * R * 0.2, -44.0, cz + math.sin(a0) * R * 0.2)
        pts = [start]
        for step, (y, rad, twist) in enumerate(((-54, 13, 0.5), (-63, 8.5, 1.1), (-71, 6.5, 1.7), (-77, 5.5, 2.3), (-81, 6.5, 2.8))):
            a = a0 + twist
            pts.append((cx + math.cos(a) * rad, y, cz + math.sin(a) * rad))
        # splay out and curl up to form the cradle bowl around the relic
        a = a0 + 3.2
        pts.append((rx + math.cos(a) * 10, ry - 7, rz + math.sin(a) * 10))
        pts.append((rx + math.cos(a + 0.25) * 12.5, ry + 1.5, rz + math.sin(a + 0.25) * 12.5))
        objs.append(W.tube("SI_Root%d" % k, coll, [W.rb(*p) for p in pts], root_radius(8.0, 1.6), 12, mat, band,
                           per=6, uv_repeat=1.0, wobble=0.25, seed=k * 13))
    return objs


PATH_ROOT = [(90, -2.5, 33), (99, -12, 42), (93, -30, 54), (70, -48, 52), (44, -62, 40), (26, -73, 24), (16, -80, 12)]


def build_path_root(coll, mat, bands):
    return W.tube("SI_PathRoot", coll, [W.rb(*p) for p in PATH_ROOT], root_radius(6.0, 3.2), 12, mat, bands[BARK],
                  per=8, uv_repeat=1.0, wobble=0.2, seed=7)


def path_shelf_spots(count=9):
    """Shelf positions along the path root: evenly descending from the rim to the cradle."""
    curve = W.catmull([W.rb(*p) for p in PATH_ROOT], 16)
    lengths = [0.0]
    for a, b in zip(curve, curve[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    spots = []
    for i in range(count):
        target = lengths[-1] * (i + 0.6) / (count + 0.4)
        k = next(j for j in range(len(lengths)) if lengths[j] >= target)
        spots.append(curve[k])
    return spots


SIDE_ROOTS = [
    ([(-24, -30, -26), (-42, -40, -38), (-56, -44, -44)], (-60, -47, -46), 12),
    ([(30, -28, 36), (44, -40, 50), (52, -48, 56)], (55, -51, 58), 9),
    ([(-36, -26, 34), (-52, -36, 46), (-62, -42, 52)], (-66, -44, 54), 10),
]


def boulder(coll, mat, bands, name, centre, radius, seed):
    rnd = random.Random(seed)
    pts = [W.rb(centre[0] + math.cos(t) * math.sin(p) * radius * (0.75 + 0.5 * rnd.random()),
                centre[1] + math.cos(p) * radius * 0.8 * (0.8 + 0.4 * rnd.random()),
                centre[2] + math.sin(t) * math.sin(p) * radius * (0.75 + 0.5 * rnd.random()))
           for t, p in ((rnd.uniform(0, TAU), math.acos(rnd.uniform(-1, 1))) for _ in range(46))]
    import bmesh
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    v0, v1 = bands[STRATA]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    layer = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv = ((math.atan2(co.y - (-centre[2]), co.x - centre[0]) / TAU) % 1, v0 + (v1 - v0) * (0.4 + 0.4 * (centre[1] + radius - co.z) / (2 * radius)))
        poly.use_smooth = False
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def build_side_roots(coll, mat, bands):
    out = []
    for k, (pts, bcentre, brad) in enumerate(SIDE_ROOTS):
        out.append(W.tube("SI_SideRoot%d" % k, coll, [W.rb(*p) for p in pts], root_radius(6.0, 3.0), 10, mat, bands[BARK], per=6, wobble=0.25, seed=40 + k))
        out.append(boulder(coll, mat, bands, "SI_Boulder%d" % k, bcentre, brad, 60 + k))
    return out


# ---------- walkable pieces (one mesh each, placed many times) ----------
def shelf_mesh(coll, mat, bands, name="SI_RootShelf"):
    """A bracket-fungus shelf: flat walkable top (about 9 x 7 studs), layered rim, tapering underside.
    Built around its own origin (top centre); placed along the path root."""
    v0, v1 = bands[MOSS]
    seg, verts, faces, uvs = 20, [], [], []
    top_ring, mid_ring, low_ring = [], [], []
    for i in range(seg):
        a = math.pi * (i / (seg - 1)) - math.pi / 2  # half-ellipse opening toward +X
        x, y = math.cos(a) * 5.0 + 0.5, math.sin(a) * 4.0
        top_ring.append(len(verts)); verts.append(W.Vector((x, y, 0.0)))
        mid_ring.append(len(verts)); verts.append(W.Vector((x * 1.06, y * 1.06, -0.7)))
        low_ring.append(len(verts)); verts.append(W.Vector((x * 0.55 - 0.6, y * 0.55, -2.2)))
    c = len(verts); verts.append(W.Vector((0.4, 0, 0.0)))
    back_low = len(verts); verts.append(W.Vector((-1.6, 0, -2.6)))
    for i in range(seg - 1):
        faces.append([top_ring[i], top_ring[i + 1], c]); uvs.append([(0.3, v1), (0.3, v1), (0.3, v1)])
        for ra, rb_, vv in ((top_ring, mid_ring, v1 - 0.02), (mid_ring, low_ring, v0 + 0.02)):
            faces.append([ra[i + 1], ra[i], rb_[i], rb_[i + 1]]); uvs.append([(0.6, vv), (0.6, vv), (0.6, vv), (0.6, vv)])
        faces.append([low_ring[i + 1], low_ring[i], back_low]); uvs.append([(0.8, v0), (0.8, v0), (0.8, v0)])
    # close the flat back against the root
    faces.append([top_ring[0], c, top_ring[-1]][::-1]); uvs.append([(0.3, v1)] * 3)
    me_obj = W.mesh_object(name, [W.Vector(v) for v in verts], faces, coll, uvs=uvs, smooth=False, material=mat)
    return me_obj


def cradle_floor_mesh(coll, mat, bands, name="SI_CradleFloor"):
    """Woven-root floor inside the cradle: a shallow dish players stand on beside the relic."""
    v0, v1 = bands[BARK]
    seg, verts, faces, uvs = 24, [], [], []
    rings = []
    for k, (r, z) in enumerate(((0.0, 0.0), (3.5, 0.1), (7.0, 0.5), (7.6, -0.6), (5.0, -2.4))):
        ring = []
        for i in range(seg):
            a = TAU * i / seg
            rr = r * (1 + 0.06 * math.sin(a * 5 + k))
            ring.append(len(verts)); verts.append(W.Vector((math.cos(a) * rr, math.sin(a) * rr, z)))
        rings.append(ring)
    for ra, rb_ in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([ra[i], ra[j], rb_[j], rb_[i]][::-1] if False else [ra[i], rb_[i], rb_[j], ra[j]])
            uvs.append([(i / seg * 2, v0), (i / seg * 2, v1), ((i + 1) / seg * 2, v1), ((i + 1) / seg * 2, v0)])
    return W.mesh_object(name, [W.Vector(v) for v in verts], faces, coll, uvs=uvs, smooth=True, material=mat)


def shelf_placements(count=12):
    """World-local transforms (Roblox studs, island-local) for each shelf: position of the walkable
    top centre and the yaw that turns the shelf's open side away from the path root."""
    curve = W.catmull([W.rb(*p) for p in PATH_ROOT], 16)
    lengths = [0.0]
    for a, b in zip(curve, curve[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    out = []
    for i in range(count):
        target = lengths[-1] * (i + 0.5) / count
        k = next(j for j in range(len(lengths)) if lengths[j] >= target)
        p = curve[k]
        t = lengths[k] / lengths[-1]
        radius = 6.0 + (3.2 - 6.0) * t ** 0.8
        tangent = (curve[min(k + 1, len(curve) - 1)] - curve[max(k - 1, 0)]).normalized()
        yaw = math.atan2(tangent.y, tangent.x)
        # Roblox local position of the shelf top: on top of the root
        out.append(((p.x, p.z + radius * 0.85, -p.y), yaw))
    return out


def write_placements(path=W.REPO + "/src/worldbuild/Placements/StartingIsland.lua"):
    """Island-local transforms for the kit pieces, read by WorldBuilder.placeKit."""
    lines = ["-- Generated by tools/blender/world/start_meshes.py. Do not edit by hand.",
             "-- Island-local Roblox studs; each entry places a kit piece's authored origin.", "return {",
             "    SI_RootShelf = {"]
    for pos, yaw in shelf_placements(12):
        lines.append("        { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (pos[0], pos[1], pos[2], yaw))
    lines += ["    },",
              "    SI_CradleFloor = { { Position = Vector3.new(%g, %g, %g), Yaw = 0 } }," % CRADLE_FLOOR,
              "    Relic = Vector3.new(%g, %g, %g)," % RELIC, "}", ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))

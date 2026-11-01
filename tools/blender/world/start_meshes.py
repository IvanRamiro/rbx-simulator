"""The Starting Island's mesh atlas and its two walkable kit pieces, the root shelf (SI_RootShelf)
and the cradle floor (SI_CradleFloor), which Yggdrasil places along its great root. Yggdrasil's
atlas (ygg_meshes) also reuses the strata, moss and stone colours here. The Starting Island's own
underside was retired with it (2026-11-01)."""
import bpy, math, os, random
from mathutils import Vector
import worldlib as W

TAU = 2 * math.pi


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

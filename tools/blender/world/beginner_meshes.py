"""The Beginner Isle's underside: Yggdrasil's stacked rock in a smaller form (it is the hub's neighbour),
the strata stepping in as they go down, craggy beneath, with old pine roots gripping the rim.

    import beginner_meshes as M
    objs, img = M.build()     # in Blender
    M.export(objs, img)       # assets/world/BeginnerIsle/BeginnerIsle_Island.fbx
"""
import math

import beginner_island as Y
import start_meshes as SM
import worldlib as W

TAU = 2 * math.pi


def root_bark(u, v):
    a = u * TAU
    fissure = abs(math.sin(a * 5 + 1.5 * W.fbm(math.cos(a) * 2, math.sin(a) * 2 + v * 3, seed=451, octaves=3)))
    g = W.fbm(math.cos(a) * 8 + v * 4, math.sin(a) * 8, seed=453, octaves=3)
    r = W.smoothstep(0.2, 0.8, fissure)
    c = (0.13 + 0.15 * r, 0.1 + 0.12 * r, 0.08 + 0.09 * r)
    return tuple(max(0.0, c[i] + 0.04 * g) for i in range(3))


STRIPS = [(256, SM.strata_colour), (64, root_bark)]
STRATA, ROOT = 0, 1


def build_atlas():
    return W.atlas_image("BeginnerIsle_Atlas", 512, STRIPS)


# (scale of the rim outline, x/z offset, top y, bottom y)
SLABS = [(1.0, (0, 0), -1.6, -20.0), (0.84, (-7, 5), -16.0, -36.0), (0.66, (9, -4), -32.0, -52.0),
         (0.46, (10, 7), -48.0, -66.0), (0.26, (5, 3), -62.0, -74.0)]
SEG = 150


def slab(coll, mat, band, name, scale, offset, top, bottom, seed):
    v0, v1 = band
    depth = -SLABS[-1][3]
    vt, vb = v0 + (v1 - v0) * (-top / depth) * 0.9, v0 + (v1 - v0) * (-bottom / depth) * 0.9
    verts, faces, uvs = [], [], []
    rings = []
    for y, inset, jag in ((top, 0.0, 0.0), (top - 0.4 * (top - bottom), 1.8, 0.5), (bottom, 8.0, 1.0)):
        ring = []
        for i in range(SEG):
            th = TAU * i / SEG
            lobe = 11.0 * W.fbm(math.cos(th) * 1.8 + seed, math.sin(th) * 1.8 - seed, seed=seed + 3, octaves=2)
            R = Y.rim(th) * scale + (0.8 if scale == 1.0 and inset == 0 else (lobe if scale < 1.0 else 0))
            n = W.fbm(math.cos(th) * 7 + seed, math.sin(th) * 7 - seed, seed=seed, octaves=3)
            r = max(2.0, R - inset * (1 + 1.6 * abs(n)) + 4.0 * n * (inset > 0))
            yy = y - jag * 8.0 * abs(W.fbm(math.cos(th) * 13 - seed, math.sin(th) * 13, seed=seed + 5, octaves=3)) ** 1.3
            ring.append(len(verts))
            verts.append(W.rb(offset[0] + math.cos(th) * r, yy, offset[1] + math.sin(th) * r))
        rings.append(ring)
    for (ra, rb_), (va, vb_) in zip(zip(rings, rings[1:]), ((vt, vt + (vb - vt) * 0.4), (vt + (vb - vt) * 0.4, vb))):
        for i in range(SEG):
            j = (i + 1) % SEG
            faces.append([ra[i], rb_[i], rb_[j], ra[j]])
            uvs.append([(4 * i / SEG, va), (4 * i / SEG, vb_), (4 * (i + 1) / SEG, vb_), (4 * (i + 1) / SEG, va)])
    under = [rings[2]]
    for level, (frac, drop) in enumerate(((0.62, 5.0), (0.28, 8.0))):
        ring = []
        for i in range(SEG):
            th = TAU * i / SEG
            base = verts[rings[2][i]]
            cx, cy = offset[0], -offset[1]
            crag = abs(W.fbm(math.cos(th) * 8 + level * 3 + seed, math.sin(th) * 8, seed=seed + 9, octaves=3))
            ring.append(len(verts))
            verts.append(W.Vector(((base.x - cx) * frac + cx, (base.y - cy) * frac + cy, bottom - drop - 10.0 * crag ** 1.6)))
        under.append(ring)
    vu = min(v1, vb + 0.03)
    for ra, rb_ in zip(under, under[1:]):
        for i in range(SEG):
            j = (i + 1) % SEG
            faces.append([ra[j], ra[i], rb_[i], rb_[j]])
            uvs.append([(4 * (i + 1) / SEG, vb), (4 * i / SEG, vb), (4 * i / SEG, vu), (4 * (i + 1) / SEG, vu)])
    mid = len(verts)
    verts.append(W.rb(offset[0], bottom - 12.0, offset[1]))
    for i in range(SEG):
        j = (i + 1) % SEG
        faces.append([under[-1][j], under[-1][i], mid])
        uvs.append([(4 * i / SEG, vu), (4 * (i + 1) / SEG, vu), (4 * (i + 0.5) / SEG, vu)])
    top_mid = len(verts)
    verts.append(W.rb(offset[0], top, offset[1]))
    for i in range(SEG):
        faces.append([rings[0][i], rings[0][(i + 1) % SEG], top_mid])
        uvs.append([(0, vt), (0, vt), (0, vt)])
    return W.mesh_object(name, verts, faces, coll, uvs=uvs, material=mat)


# clear of the bridge (bearing ~165), the hall's back and the bell
GRIP_BEARINGS = (30, 78, 118, 212, 258, 318)


def corner_r(k, theta):
    sc, (ox, oz), _, _ = SLABS[k]
    return sc * Y.rim(theta) + ox * math.cos(theta) + oz * math.sin(theta) + 4.0


def grip_points(bearing):
    th = math.radians(bearing)
    R = Y.rim(th)

    def at(r, y, swing=0.0):
        a = th + swing
        return (math.cos(a) * r, y, math.sin(a) * r)
    pts = [at(R - 20, -5), at(R - 11, -2), at(R - 3, -1.2), at(R + 3, -3), at(R + 5, -11), at(R + 3, -19, 0.01)]
    pts.append(at(corner_r(1, th) + 3, SLABS[1][3] - 1, 0.03))
    pts.append(at(corner_r(1, th) - 6, SLABS[1][3] - 6, 0.05))   # and back into the rock
    return pts


def build():
    img, bands = build_atlas()
    mat = W.textured_material("BeginnerIsle_Mat", img)
    root = W.collection(Y.NAME)
    coll = W.collection("BI_Underside", root)
    W.clear_collection(coll)
    objs = [slab(coll, mat, bands[STRATA], "BI_Slab%d" % k, sc, off, top, bot, 460 + 7 * k)
            for k, (sc, off, top, bot) in enumerate(SLABS)]
    objs += [W.tube("BI_GripRoot%d" % k, coll, [W.rb(*p) for p in grip_points(b)], lambda t: 6.0 - 3.6 * t ** 0.7, 12, mat,
                    bands[ROOT], per=5, uv_repeat=1.5, wobble=0.25, seed=480 + k)
             for k, b in enumerate(GRIP_BEARINGS)]
    return objs, img


def export(objs, img):
    path = W.REPO + "/assets/world/BeginnerIsle/BeginnerIsle_Island.fbx"
    W.export_batch(objs, path, image=img, anchor_name="BI_Anchor")
    return path

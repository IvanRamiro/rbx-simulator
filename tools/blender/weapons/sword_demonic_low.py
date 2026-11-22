"""The Demonic sword's game mesh (run inside Blender, headless): built from the same parametric functions as the high-detail source,
at game density, so every edge loop is placed where the silhouette needs it (the blade's S line, the point's scoop, the guard's
arms) and the UVs can be laid out by hand.

    build_low(coll, mat) -> (objects, report)     the pieces, joined into one mesh "SecretDemonic_Body" by join_low
    unwrap_low(obj, blade_scale)                   the blade's belt UVs by hand, everything else by Blender, packed together at one
                                                   texel density

The wrap's ribbons, the guard's face plates and end caps, the engraving and the fuller's floor are not geometry here: the bake
carries them (normal map and colour).
"""
import math

import bmesh
import bpy
import numpy as np

import sword_demonic_blade as BL
import sword_demonic_grip as GR
import sword_demonic_guard as GD
import sword_demonic_kit as KT
import sword_demonic_profile as P

TAU = math.tau


def tube(m, pts, radii, sides=6, mat=0, caps=(True, True), per=4):
    """A round tube along the polyline pts (k, 3), radius interpolated from radii (k,), the path smoothed (Catmull-Rom)."""
    from sword_demonic_profile import catmull
    pts = np.asarray(pts, dtype=np.float64)
    path = catmull(pts, per)
    rad = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(radii)), radii)
    n = len(path)
    tang = np.gradient(path, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    ref = np.array([0.0, 1.0, 0.0])
    side = np.cross(tang[0], ref)
    if np.linalg.norm(side) < 1e-4:
        side = np.array([1.0, 0.0, 0.0])
    side /= np.linalg.norm(side)
    rings = []
    ang = np.linspace(0, TAU, sides, endpoint=False)
    for i in range(n):
        side = side - tang[i] * np.dot(side, tang[i])
        side /= np.linalg.norm(side)
        up = np.cross(tang[i], side)
        rings.append(path[i] + (np.cos(ang)[:, None] * side + np.sin(ang)[:, None] * up) * rad[i])
    ring = np.stack(rings)                 # (n, sides, 3)
    uu = np.broadcast_to(np.linspace(0, 1, sides, endpoint=False)[None, :], (n, sides))
    vv = np.broadcast_to(np.linspace(0, 1, n)[:, None] * 3.0, (n, sides))
    # a straight strip in studs (round the tube, along it), closing on a repeated first column
    ring2 = np.concatenate([ring, ring[:, :1]], axis=1)
    per = TAU * float(np.mean(rad))
    seglen = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    uu = np.broadcast_to(np.linspace(0, per, sides + 1)[None, :], (n, sides + 1))
    vv = np.broadcast_to(seglen[:, None], (n, sides + 1))
    idx = m.grid(ring2, np.stack([uu, vv], axis=-1), mat=mat)
    idx = idx[:, :-1]
    if caps[0]:
        m.fan(idx[0], path[0], mat=mat, flip=True)
    if caps[1]:
        m.fan(idx[-1], path[-1] + tang[-1] * rad[-1] * 0.6, mat=mat)


def cord_low(m):
    import math as _m
    far = GR.RING_Z + GR.RING_R
    coil = []
    for i in range(0, 13):
        a = TAU * 1.5 * i / 12
        coil.append((-0.075 + 0.15 * i / 12, 0.115 * _m.sin(a), far + 0.115 * _m.cos(a)))
    tube(m, coil, [0.046] * 13, sides=5, per=1, caps=(False, False))
    tails = [
        [(0.075, 0.115 * _m.sin(TAU * 1.5), far + 0.115 * _m.cos(TAU * 1.5)), (0.10, -0.12, far + 0.24), (0.13, -0.28, far + 0.42), (0.12, -0.42, far + 0.58)],
        [(-0.07, 0.0, far + 0.12), (-0.09, -0.10, far + 0.30), (-0.14, -0.24, far + 0.48), (-0.10, -0.36, far + 0.64)],
    ]
    import random
    rnd = random.Random(7)
    for t in tails:
        tube(m, t, [0.07, 0.07, 0.066, 0.06], sides=6, per=2, caps=(False, False))
        end = np.array(t[-1])
        for k in range(5):
            d = np.array([rnd.uniform(-0.06, 0.06), rnd.uniform(-0.12, 0.0), rnd.uniform(0.06, 0.22)])
            a0 = end + np.array([rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 0.0])
            b = end + d * rnd.uniform(0.8, 1.4)
            tube(m, [a0, (a0 + b) / 2, b], [0.026, 0.02, 0.005], sides=3, per=1, caps=(False, False))


def _mark_belt(o, kind=1):
    """Marks the object's faces as a hand-laid belt UV island (1: the blade, 2: the ring)."""
    me = o.data
    attr = me.attributes.new("isblade", "INT", "FACE")
    attr.data.foreach_set("value", np.full(len(me.polygons), kind, dtype=np.int32))


def build_low(coll, mat):
    """The low pieces as objects; the blade's faces are marked (attribute "isblade") and carry the belt UVs."""
    objs = []

    def piece(name, fn, smooth_sharp=50.0, belt=0):
        m = KT.Mesh()
        fn(m)
        o = m.object(name + "_low", coll, [mat], sharp_deg=smooth_sharp, uv_name="UVMap")
        if belt:
            _mark_belt(o, belt)
        objs.append(o)
        return o
    piece("blade", lambda m: BL.blade(m, "low", uvmode="belt"), 40.0, belt=1)
    piece("guard", lambda m: GD.core(m, "low", belt=True), 50.0, belt=3)
    piece("habaki", lambda m: GD.habaki(m, "low", belt=True), 50.0, belt=4)
    piece("grip", lambda m: (GR.grip_core_low(m), GR.fuchi(m, "low"), GR.kashira(m, "low")), 50.0, belt=5)
    piece("ring", lambda m: GR.ring(m, "low"), 50.0, belt=2)
    piece("ringstem", lambda m: GR.ring_stem(m, "low"), 50.0, belt=5)
    piece("cord", cord_low, 50.0, belt=5)
    return objs


def tri_counts(objs):
    return {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}


def join_low(objs, name, coll):
    import egg_kit as K
    low = K.join(objs, name, coll)
    me = low.data
    # one UV set: keep the first ("UVMap")
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    return low


BELTS = {1: (1.85, P.L), 2: (0.58, 2 * math.pi * GR.RING_R), 3: (1.9, 3.15), 4: (2.0, 0.62), 5: (1.0, 1.0)}     # 5: strips already in studs     # (studs round, studs along) of each hand-laid belt island


def unwrap_low(low, margin=0.006):
    """Non-belt faces by smart projection; each belt's UVs (the blade's and the ring's: straight strips, so no ring-shaped islands) scaled
    to the same density; all packed together, islands as boxes."""
    import secret_kit as SK
    me = low.data
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    view_layer.objects.active = low
    belt = np.zeros(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", belt)
    belt = belt.reshape(-1, 2)
    kind = np.zeros(len(me.polygons), dtype=np.int32)
    if "isblade" in me.attributes:
        me.attributes["isblade"].data.foreach_get("value", kind)
    with SK.B._ui_override(low):
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(me)
        lay = bm.faces.layers.int.get("isblade")
        for f in bm.faces:
            f.select = (f[lay] == 0)
        bmesh.update_edit_mesh(me)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002)
        bpy.ops.object.mode_set(mode="OBJECT")
    uv = np.zeros(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    # the density smart_project gave the others: uv area per stud^2
    area3, areauv = 0.0, 0.0
    loop_kind = np.zeros(len(me.loops), dtype=np.int32)
    for pi, p in enumerate(me.polygons):
        li = list(p.loop_indices)
        if kind[pi]:
            loop_kind[li] = kind[pi]
            continue
        pts = uv[li]
        a = 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(li)][1] - pts[(i + 1) % len(li)][0] * pts[i][1] for i in range(len(li))))
        area3 += p.area
        areauv += a
    k = math.sqrt(areauv / area3) if area3 > 1e-9 else 0.12
    for kd, (across, along) in BELTS.items():
        sel = loop_kind == kd
        uv[sel, 0] = belt[sel, 0] * across * k
        uv[sel, 1] = belt[sel, 1] * along * k
    me.uv_layers[0].data.foreach_set("uv", uv.ravel())
    with SK.B._ui_override(low):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(margin=margin, rotate=True, shape_method="AABB")
        bpy.ops.object.mode_set(mode="OBJECT")
    return k


def density(low):
    """Texels per stud at 1024, per piece group (blade / others), from the packed UVs."""
    me = low.data
    uv = np.zeros(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    isb = np.zeros(len(me.polygons), dtype=np.int32)
    if "isblade" in me.attributes:
        me.attributes["isblade"].data.foreach_get("value", isb)
    out = {}
    for tag, sel in (("blade", True), ("others", False)):
        a3 = au = 0.0
        for pi, p in enumerate(me.polygons):
            if bool(isb[pi] == 1) != sel:
                continue
            li = list(p.loop_indices)
            pts = uv[li]
            au += 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(li)][1] - pts[(i + 1) % len(li)][0] * pts[i][1] for i in range(len(li))))
            a3 += p.area
        out[tag] = round(1024 * math.sqrt(au / max(a3, 1e-9)), 1)
    return out

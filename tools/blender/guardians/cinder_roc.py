"""The Cinder Roc, the fire-bird of Ember Peak: model, skeleton, weights, maps, export (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/cinder_roc.py -- <stage> [--out DIR]

An enormous, proud, predatory bird of the volcano, the Peng of the old tales burned black: a heron's S of a neck on an eagle's heavy hooked
beak, a deep chest, thick feathered trousers over scaled shanks, four-toed feet with obsidian scythe talons, a crest of ember plumes
swept back like flames, a train of five long tail ribbons, two wings built on a real arm (shoulder, upper arm, forearm, wrist, hand)
carrying primaries like curved obsidian blades, secondaries, tertials and coverts, with magma along the feather edges. Charcoal
plumage glowing ember-orange in its underfeathers, cracked basalt armour on the crown, the shoulders, the wrists and the ankles.
The owner's brief (2026-11-23) and the silhouette study (cinder_roc_study.py) decided the shape.

Authored in Roblox studs: facing -Z, feet on the ground at y = 0, left is -X. Bound with the wings spread (a wing deforms best from
there), the body in the stance it holds awake. It holds no egg: no guardian does.

Stages (each builds what it needs):  form | review | bind | stress | ...  (see main at the bottom)
The motion (poses, gaits, the moves, the clips) is cinder_roc_motion.py.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../eggs", "../world", "."):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, sub)))
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402
import guardian_kit as G  # noqa: E402
import tiangou_v2 as T  # noqa: E402
import cinder_roc_feathers as F  # noqa: E402
import cinder_roc_materials as Mt  # noqa: E402
from cinder_roc_bones import *  # noqa: E402,F401,F403
from cinder_roc_bones import BONES, LEG_BONES, PRIM_ANGLES, PRIM_LENGTHS, PRIM_ROOTS, SEC_LENGTHS, SEC_ROOTS, joints, wing_frame, _trail, _unit  # noqa: E402

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "CinderRoc"
RIG = "CinderRocRig"
OUT = G.OUT_DIR
REPO = W.REPO

def _clay(name="CinderClay", rgb=(0.40, 0.40, 0.44)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


# ---------------------------------------------------------------- the soft forms of the body (the skin)
limb = T._limb


def _body_groups():
    """The body as groups of soft forms: (how softly the group's forms melt together, its forms). Roblox studs."""
    g = []
    # the trunk: a deep barrel, the keel forward and low, the shoulders a broad hump, the back sweeping to a tapered rump
    g.append((1.0, [
        ((0, 11.9, 2.4), (2.5, 2.4, 3.0), None), ((0, 13.0, -0.4), (3.2, 2.9, 3.4), None), ((0, 14.4, -3.4), (3.5, 3.5, 3.3), None),
        ((0, 13.7, -6.0), (2.3, 2.7, 2.2), None), ((0, 15.4, -3.9), (3.4, 2.2, 2.8), None), ((0, 14.5, 0.6), (2.8, 2.3, 3.0), None),
        ((0, 11.4, 4.2), (1.7, 1.4, 2.4), None), ((0, 14.4, -5.8), (2.1, 2.3, 1.9), None),
    ]))
    # the neck: a heron's S, forward out of the chest, back and up, forward again under the skull; thick at the root, fine at the top
    g.append((1.3, limb([(0, 14.3, -5.0), (0, 16.3, -7.6), (0, 18.3, -7.8), (0, 19.4, -7.9), (0, 19.8, -8.7)],
                        [(2.3, 2.2, 2.2), (1.4, 1.4, 1.4), (0.98, 0.98, 0.98), (0.9, 0.9, 0.9), (0.9, 0.9, 0.9)])))
    # the head: a heavy brow over a deep-set stare, cheeks, and the hooked upper beak
    g.append((0.38, [
        ((0, 20.0, -9.3), (1.75, 1.55, 2.1), None), ((0, 20.5, -10.6), (1.65, 0.72, 1.25), None),
        ((-1.15, 19.5, -10.0), (0.7, 0.9, 1.3), None), ((1.15, 19.5, -10.0), (0.7, 0.9, 1.3), None), ((0, 19.6, -11.2), (1.15, 1.0, 1.25), None),
    ] + limb([(0, 19.7, -10.7), (0, 19.4, -12.5), (0, 18.6, -14.2), (0, 17.4, -15.0)],
             [(1.15, 1.2, 1.35), (1.0, 1.05, 1.25), (0.58, 0.75, 0.85), (0.1, 0.2, 0.2)])))
    for sign in (-1, 1):
        x = lambda v: v * sign
        # the leg: a thick thigh and knee, the trouser mass falling behind it, the shin to the hock, the bare scaled shank, the foot
        g.append((0.9, [((x(3.3), 10.4, -0.4), (1.9, 2.5, 2.2), None), ((x(3.45), 8.8, -2.1), (1.55, 1.55, 1.55), None), ((x(3.5), 7.8, 1.2), (1.5, 2.6, 1.5), None)]
                  + limb([(x(3.4), 8.4, -2.4), (x(3.4), 3.8, 1.0)], [(1.35, 1.35, 1.35), (0.95, 0.95, 0.95)])
                  + limb([(x(3.4), 3.8, 1.0), (x(3.4), 1.0, -1.9)], [(0.95, 0.95, 0.95), (0.78, 0.74, 0.74)])
                  + [((x(3.4), 1.1, -2.3), (1.5, 0.68, 1.35), None)]))
        toes = []
        for dx in (-1, 0, 1):
            toes += limb([(x(3.4 + 0.5 * dx), 1.03, -2.3), (x(3.4 + 1.4 * dx), 0.89, -4.7), (x(3.4 + 2.0 * dx), 0.77, -6.0)], [(0.6, 0.55, 0.6), (0.46, 0.42, 0.46), (0.34, 0.32, 0.34)])
        toes += limb([(x(3.4), 1.15, -1.7), (x(3.4), 0.93, -0.2), (x(3.4), 0.83, 0.9)], [(0.6, 0.55, 0.6), (0.46, 0.42, 0.46), (0.32, 0.3, 0.32)])
        g.append((0.3, toes))
    # the root of the tail
    g.append((0.5, limb([(0, 12.4, 2.6), (0, 12.0, 5.0)], [(2.0, 1.6, 2.0), (1.2, 0.9, 1.2)])))
    return g


def _mandible_groups():
    return [(0.3, limb([(0, 19.0, -10.0), (0, 18.5, -11.8), (0, 18.2, -13.3)], [(0.9, 0.62, 1.05), (0.68, 0.52, 0.95), (0.18, 0.26, 0.42)]))]


def _rough(groups):
    return T._form_lobes.__wrapped__(groups) if hasattr(T._form_lobes, "__wrapped__") else _lobes_of(groups)


def _lobes_of(groups):
    out = []
    for _, lobes in groups:
        for lobe in lobes:
            if lobe[0] == "seg":
                _, a, b, ra, rb = lobe
                for k in range(5):
                    t = k / 4
                    out.append((tuple(V(a).lerp(V(b), t)), tuple(ra[n] + (rb[n] - ra[n]) * t for n in range(3)), None))
            else:
                out.append(lobe)
    return out


def build_skeleton(coll):
    data = bpy.data.armatures.new(RIG)
    arm = bpy.data.objects.new(RIG, data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for name, (parent, head, tail) in BONES.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = W.rb(*head), W.rb(*tail)
        made[name] = b
    for name, (parent, head, tail) in BONES.items():
        if parent:
            made[name].parent = made[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in data.bones:
        b.use_deform = b.name != "Root"
    return arm


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_form(voxel=0.14):
    """The skin in clay, and the skeleton: the first thing to judge."""
    T.clear()
    coll = bpy.data.collections.new("CinderRoc")
    bpy.context.scene.collection.children.link(coll)
    groups = _body_groups()
    skin = G.blob("CR_Skin", coll, _clay(), _lobes_of(groups), voxel=voxel, smooth=0.75, rough=0.0, chisel="CinderChisel")
    T._settle(skin, groups)
    G.soften(skin, 6)
    T._settle(skin, groups, passes=2)
    mg = _mandible_groups()
    jaw = G.blob("CR_Jaw", coll, _clay(), _lobes_of(mg), voxel=voxel * 0.7, smooth=0.75, rough=0.0, chisel="CinderChisel")
    T._settle(jaw, mg)
    G.soften(jaw, 4)
    for o in (skin, jaw):
        for p in o.data.polygons:
            p.use_smooth = True
    build_skeleton(coll)
    return {"skin": tris(skin), "jaw": tris(jaw), "bones": len(BONES)}



# ---------------------------------------------------------------- the parts, in clay colours first
CLAY = {"skin": (0.34, 0.34, 0.38), "feather": (0.20, 0.20, 0.24), "plate": (0.45, 0.40, 0.34), "magma": (1.0, 0.45, 0.05), "ember": (0.9, 0.42, 0.12),
        "horn": (0.07, 0.07, 0.08)}


REAL = {}          # the real materials, once made (see use_real_materials); until then every part wears a clay colour


WANT_REAL = False


def use_real_materials():
    REAL.clear()
    REAL.update(Mt.all_materials())


def _mat(kind):
    if kind in REAL:
        return REAL[kind]
    return _clay("CinderClay_" + kind, CLAY.get(kind, CLAY["feather"]))


def _hi_object(hi, name, coll, kind, smooth=True, keep=True):
    o = hi.object(name, coll, [_mat(kind)], smooth=smooth, weld=0)
    o["keep"] = keep
    return o


def _plate(name, coll, lobes, voxel=0.1):
    o = G.blob(name, coll, _mat("plate"), lobes, voxel=voxel, smooth=0.5, rough=0.05, chisel="CinderBasalt")
    o["keep"] = False
    return o


def _plate_veins(plates, seed):
    """Thin molten veins wandering over armour plates: a Neon piece (the plates' own cracks are baked colour)."""
    import random
    rnd = random.Random(seed)
    hi = Hm.Hi()
    for k, plate in enumerate(plates):
        pts = [V(K.rb_inv(*(plate.matrix_world @ v.co))) for v in plate.data.vertices]
        tops = sorted(pts, key=lambda q: -q.y)[: max(8, len(pts) // 12)]
        starts = [(rnd.choice(tops), V((rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3), rnd.uniform(-1, 1)))) for _ in range(3)]
        G.veins(hi, plate, starts, random.Random(seed + k), steps=7, step=0.55, radius=0.075, lift=0.05)
    return hi


def build_parts(coll):
    """Every high-detail part except the body's soft skin: {piece: [objects]}."""
    parts = {}
    right, shoulder_lobes, wrist_lobes = F.build_wing(None, coll)
    wr = {k: _hi_object(h, "CR_R_" + k, coll, "feather" if k in ("flight", "covert") else "arm" if k == "arm" else "horn" if k == "claws" else "magma") for k, h in right.items()}
    wr["shoulder"] = _plate("CR_R_Shoulder", coll, shoulder_lobes)
    wr["wrist"] = _plate("CR_R_Wrist", coll, wrist_lobes, voxel=0.08)
    wr["veins"] = _hi_object(_plate_veins([wr["shoulder"], wr["wrist"]], 31), "CR_R_Veins", coll, "magma")
    wl = {k: F.mirror(o, o.name.replace("CR_R_", "CR_L_")) for k, o in wr.items()}
    parts["WingR"], parts["WingL"] = wr, wl
    tail = F.build_tail(coll, None)
    parts["Tail"] = {"tail": _hi_object(tail["tail"], "CR_Tail", coll, "tailfeather"), "glow": _hi_object(tail["glow"], "CR_TailGlow", coll, "magma")}
    crest = F.build_crest(coll, None)
    parts["Crest"] = {"crest": _hi_object(crest["crest"], "CR_Crest", coll, "ember"), "glow": _hi_object(crest["glow"], "CR_CrestGlow", coll, "magma")}
    return parts


def _talons():
    """Obsidian scythe talons: three on each foot's toes and the great one on the hallux."""
    hi = Hm.Hi()
    for sign in (-1, 1):
        for dx in (-1, 0, 1):
            tip = V((sign * (3.4 + 2.0 * dx), 0.77, -6.05))
            p0 = tip + V((0, 0.12, 0.35))
            Hm.htube(hi, [p0, p0 + V((sign * 0.12 * dx, 0.0, -0.9)), p0 + V((sign * 0.2 * dx, -0.3, -1.7)), p0 + V((sign * 0.26 * dx, -0.62, -2.2))],
                     lambda t: 0.40 * (1 - t) ** 0.8 + 0.03, sides=7, per=5, uv_scale=1.0, tip=True, wobble=0.0)
        base = V((sign * 3.4, 0.99, 0.3))
        Hm.htube(hi, [base, base + V((0, 0.2, 1.1)), base + V((0, 0.0, 2.1)), base + V((0, -0.5, 2.8))], lambda t: 0.5 * (1 - t) ** 0.8 + 0.03, sides=8, per=5, uv_scale=1.0, tip=True, wobble=0.0)
    return hi


def _eyes(skin):
    iris, pupil, lids = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        normal = V((side * 0.78, 0.05, -0.62)).normalized()
        seat = G.surface_along(skin, V((side * 0.7, 20.05, -10.3)), normal, reach=5.0)
        G.eye(iris, pupil, lids, seat, normal, (-side * 0.5, -0.1, -1), 0.62, 0.34, tilt=0.4, bulge=0.12, lid=0.65, droop=0.6, lower=0.2, slit=0.2, pupil_height=0.8)
    return iris, pupil, lids


def _skin_lobes():
    crown = [((0, 20.95, -9.4), (1.45, 0.5, 1.8), None), ((-0.85, 20.75, -10.7), (0.8, 0.4, 0.9), None), ((0.85, 20.75, -10.7), (0.8, 0.4, 0.9), None),
             ((0, 21.05, -8.2), (1.0, 0.45, 1.1), None), ((-1.25, 20.3, -9.0), (0.45, 0.8, 1.1), None), ((1.25, 20.3, -9.0), (0.45, 0.8, 1.1), None)]
    ankles = []
    for sign in (-1, 1):
        ankles.append([((sign * 3.4, 3.9, 1.75), (1.25, 1.2, 0.85), None), ((sign * 3.4, 5.0, 1.45), (1.1, 0.95, 0.75), None), ((sign * 3.4, 2.9, 1.25), (1.05, 0.9, 0.7), None),
                       ((sign * 4.25, 3.9, 1.1), (0.5, 1.0, 0.9), None), ((sign * 2.55, 3.9, 1.1), (0.5, 1.0, 0.9), None)])
    return crown, ankles


def build_all(voxel=0.14):
    """Every high-detail part: {piece: {name: object}}."""
    info = build_form(voxel)
    if WANT_REAL:
        use_real_materials()
    coll = bpy.data.collections["CinderRoc"]
    skin = bpy.data.objects["CR_Skin"]
    parts = build_parts(coll)
    body, nfeathers = F.build_body_feathers(skin)
    crown, ankles = _skin_lobes()
    iris, pupil, lids = _eyes(skin)
    parts["Skin"] = {"skin": skin, "jaw": bpy.data.objects["CR_Jaw"], "contour": _hi_object(body, "CR_Contour", coll, "feather"),
                     "crown": _plate("CR_Crown", coll, crown, voxel=0.08), "ankleL": _plate("CR_AnkleL", coll, ankles[0], voxel=0.08), "ankleR": _plate("CR_AnkleR", coll, ankles[1], voxel=0.08),
                     "talons": _hi_object(_talons(), "CR_Talons", coll, "horn"), "lids": _hi_object(lids, "CR_Lids", coll, "horn")}
    skin_parts = parts["Skin"]
    skin_parts["veins"] = _hi_object(_plate_veins([skin_parts["crown"], skin_parts["ankleL"], skin_parts["ankleR"]], 17), "CR_BodyVeins", coll, "magma")
    parts["Eyes"] = {"iris": _hi_object(iris, "CR_Eyes", coll, "eyes", keep=True), "pupil": _hi_object(pupil, "CR_Pupils", coll, "horn")}
    for name in ("CR_Skin", "CR_Jaw"):
        o = bpy.data.objects[name]
        o.data.materials.clear()
        o.data.materials.append(_mat("skin"))
    info["contour feathers"] = nfeathers
    return info, parts


def build_preview():
    info, parts = build_all()
    return info, {k: {n: tris(o) for n, o in objs.items()} for k, objs in parts.items()}


# ---------------------------------------------------------------- the weights
def _points(obj):
    """The vertices of obj in Roblox space, as an array."""
    import numpy as np
    n = len(obj.data.vertices)
    co = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)


def _distances(pts, names):
    import numpy as np
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    return np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)


def _write_groups(obj, names, keep):
    obj.vertex_groups.clear()
    for j, nm in enumerate(names):
        idx = [int(i) for i in (keep[:, j] > 0).nonzero()[0]]
        if idx:
            vg = obj.vertex_groups.new(name=nm)
            for i in idx:
                vg.add([i], float(keep[i, j]), "REPLACE")


def bind_distance(obj, names, falloff=1.0, mask=None, influences=4, bias=None):
    """Weights from each vertex's distance to the bones in `names` (segments head to tail): the nearest bone leads, the others share by a
    Gaussian of how much farther they are. mask: {bone: boolean array of the vertices that bone may reach}; bias: {bone: studs added}."""
    import numpy as np
    pts = _points(obj)
    d = _distances(pts, names)
    for j, nm in enumerate(names):
        if nm.startswith("Left"):
            d[pts[:, 0] > 0.3, j] = 1e6
        elif nm.startswith("Right"):
            d[pts[:, 0] < -0.3, j] = 1e6
        if mask and nm in mask:
            d[~mask[nm], j] = 1e6
        if bias and nm in bias:
            d[:, j] += bias[nm]
    blocked = d.min(axis=1) >= 1e5          # no bone may reach it: the nearest takes it whole, masks ignored
    if blocked.any():
        free = _distances(pts[blocked], names)
        for j, nm in enumerate(names):
            if nm.startswith("Left"):
                free[pts[blocked][:, 0] > 0.3, j] = 1e6
            elif nm.startswith("Right"):
                free[pts[blocked][:, 0] < -0.3, j] = 1e6
        d[blocked] = free
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[d >= 1e5] = 0
    order = np.argsort(-w, axis=1)[:, :influences]
    keep = np.zeros_like(w)
    rows = np.arange(len(w))[:, None]
    keep[rows, order] = w[rows, order]
    keep[keep < 0.03] = 0
    keep /= np.maximum(keep.sum(axis=1, keepdims=True), 1e-9)
    _write_groups(obj, names, keep)
    return keep


def bind_rigid(obj, bone):
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")


def attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


BODY_BONES = ["Hips", "Spine", "Chest", "Neck1", "Neck2", "Neck3", "Head", "TailBase"] + [t + n for t in ("Left", "Right") for n in ("Clavicle",) + LEG_BONES]


def body_mask(pts):
    """Where each bone of the body may reach: the trunk's bones keep to the trunk, a leg's to its leg, so a thigh does not drag the belly."""
    import numpy as np
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    ax = np.abs(x)
    m = {
        "Hips": (z > -1.4) & (y > 9.6) & (ax < 5.2),
        "Spine": (z > -5.0) & (z < 2.0) & (y > 10.2) & (ax < 5.6),
        "Chest": (z < -2.0) & (y > 10.6) & (y < 17.8) & (ax < 5.8),
        "Neck1": (y > 14.0) & (z < -4.0) & (y < 17.8) & (ax < 3.4),
        "Neck2": (y > 16.0) & (z < -6.0) & (y < 19.6) & (ax < 2.8),
        "Neck3": (y > 17.8) & (z < -6.2) & (z > -10.0) & (ax < 2.4),
        "Head": (z < -7.2) & (y > 18.0),
        "TailBase": (z > 3.4) & (y > 10.4),
    }
    for sign, tag in ((-1, "Left"), (1, "Right")):
        m[tag + "Clavicle"] = (ax > 2.0) & (y > 12.6) & (z < -1.6) & (z > -7.4)
        m[tag + "Thigh"] = (y < 12.8) & (ax > 0.9)
        m[tag + "Shin"] = (y < 9.4) & (ax > 1.4)
        m[tag + "Tarsus"] = (y < 4.8) & (ax > 1.8)
        m[tag + "Foot"] = (y < 1.8) & (z < -0.8) & (ax > 1.4)
        m[tag + "Toes"] = (y < 1.7) & (z < -3.6)
        m[tag + "Hallux"] = (y < 1.4) & (z > -1.9) & (z < 1.6) & (ax > 1.8)
        m[tag + "Trouser"] = (y < 11.8) & (y > 5.2) & (z > -1.0) & (ax > 1.4)
    return m


def bind_body(obj, falloff=1.2):
    return bind_distance(obj, BODY_BONES, falloff, mask=body_mask(_points(obj)))


def wing_bones(tag):
    return [tag + n for n in ("Clavicle", "UpperArm", "Forearm", "Hand") + tuple("Prim%d%s" % (g, c) for g in range(1, 6) for c in "AB") + tuple("Sec%d%s" % (g, c) for g in (1, 2) for c in "AB")]


TAIL_BONES = ["TailBase", "Tail0A", "Tail0B", "Tail0C"] + [t + "Tail%d%s" % (g, c) for t in ("Left", "Right") for g in (1, 2) for c in "AB"]
CREST_BONES = ["CrestA", "CrestB"] + [t + "Crest" + c for t in ("Left", "Right") for c in "AB"]
FOOT_BONES = [t + n for t in ("Left", "Right") for n in ("Toes", "Hallux")]


# ---------------------------------------------------------------- the game meshes: each piece's objects reduced, weighted, joined
def _reduce(obj, target):
    now = tris(obj)
    if target and now > target:
        m = obj.modifiers.new("Reduce", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = max(0.02, target / now)
        m.use_collapse_triangulate = True
        me = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        old = obj.data
        obj.modifiers.clear()
        obj.data = me
        bpy.data.meshes.remove(old)
    for p in obj.data.polygons:
        p.use_smooth = True


def _copy(obj, name):
    me = obj.data.copy()
    me.transform(obj.matrix_world)
    c = bpy.data.objects.new(name, me)
    bpy.data.collections["CinderRoc"].objects.link(c)
    return c


def _clean(obj, normals=True):
    """What Roblox needs of a mesh: no doubled vertices, none collapsed, faces wound outward (not for open sheets, whose winding is the
    one they were built with)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    if normals:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def drop_zfighting(lows, eps=0.001):
    """Where two triangles of the asset lie on one plane (within eps) facing the same way and overlap, one of them is hidden under the other
    and z-fights with it: the later one is removed (the same test blender-asset-qa makes). Every piece is triangulated first."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    objs = list(lows.values())
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    verts, tris, meta = [], [], []
    for oi, o in enumerate(objs):
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            tris.append(tuple(base + i for i in p.vertices))
            meta.append((oi, p.index, p.normal.copy()))
    bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    tri_sets = [set(t) for t in tris]
    drop = set()
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = meta[ti][2]
        if n.length < 0.5:
            continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or tri_sets[ti] & tri_sets[tj]:
                    continue
                n2 = meta[tj][2]
                if n.dot(n2) < 0.999:
                    continue
                a2, b2, c2 = (verts[i] for i in tris[tj])
                q = p - n2 * n2.dot(p - a2)
                v0, v1, v2 = c2 - a2, b2 - a2, q - a2
                d00, d01, d02, d11, d12 = v0.dot(v0), v0.dot(v1), v0.dot(v2), v1.dot(v1), v1.dot(v2)
                inv = d00 * d11 - d01 * d01
                if abs(inv) < 1e-12:
                    continue
                u, w = (d11 * d02 - d01 * d12) / inv, (d00 * d12 - d01 * d02) / inv
                if u >= -1e-6 and w >= -1e-6 and u + w <= 1 + 1e-6:
                    drop.add(max(ti, tj))
    per = {}
    for ti in drop:
        per.setdefault(meta[ti][0], set()).add(meta[ti][1])
    for oi, faces in per.items():
        bm = bmesh.new()
        bm.from_mesh(objs[oi].data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in faces], context="FACES")
        bm.to_mesh(objs[oi].data)
        bm.free()
    return len(drop)


def _wing_plan(side):
    tag = "Left" if side == "L" else "Right"
    return [("Wing" + side, "flight", None, ("dist", wing_bones(tag), 0.7)), ("Wing" + side, "covert", None, ("dist", wing_bones(tag), 0.7)),
            ("Wing" + side, "arm", None, ("dist", wing_bones(tag)[:4], 1.0)), ("Wing" + side, "claws", None, ("rigid", tag + "Hand")),
            ("Wing" + side, "shoulder", 600, ("rigid", tag + "Clavicle")), ("Wing" + side, "wrist", 450, ("rigid", tag + "Forearm"))]


def piece_plan():
    """Each game piece: its high-detail objects as (piece, key, target triangles or None to keep whole, how it is weighted)."""
    return {
        "Skin": [("Skin", "skin", 7000, "body"), ("Skin", "jaw", 700, ("rigid", "Jaw")), ("Skin", "crown", 600, ("rigid", "Head")),
                 ("Skin", "ankleL", 520, ("rigid", "LeftTarsus")), ("Skin", "ankleR", 520, ("rigid", "RightTarsus")), ("Skin", "lids", 560, ("rigid", "Head")),
                 ("Skin", "talons", None, ("dist", FOOT_BONES, 0.25))],
        "Plumage": [("Skin", "contour", None, "body")],
        "WingL": _wing_plan("L"),
        "WingR": _wing_plan("R"),
        "Tail": [("Tail", "tail", None, ("dist", TAIL_BONES, 0.9))],
        "Crest": [("Crest", "crest", None, ("dist", CREST_BONES, 0.8))],
        "Eyes": [("Eyes", "iris", None, ("rigid", "Eyes"))],
        "Pupils": [("Eyes", "pupil", None, ("rigid", "Eyes"))],
        "Magma": [("WingL", "magma", None, ("dist", wing_bones("Left"), 0.7)), ("WingR", "magma", None, ("dist", wing_bones("Right"), 0.7)),
                  ("Tail", "glow", None, ("dist", TAIL_BONES, 0.9)), ("Crest", "glow", None, ("dist", CREST_BONES, 0.8)),
                  ("Skin", "veins", None, ("dist", ["Head", "LeftTarsus", "RightTarsus", "LeftShin", "RightShin"], 0.4)),
                  ("WingR", "veins", None, ("dist", ["RightClavicle", "RightForearm"], 0.4)), ("WingL", "veins", None, ("dist", ["LeftClavicle", "LeftForearm"], 0.4))],
    }


def make_low(piece, parts, plan):
    """The game mesh of one piece: its high-detail objects copied, reduced, weighted, joined into one object named CinderRoc_<piece>."""
    made = []
    for src_piece, key, target, how in plan[piece]:
        src = parts[src_piece][key]
        c = _copy(src, "low_%s_%s_%s" % (piece, src_piece, key))
        _reduce(c, target)
        _clean(c, normals=key != "contour")
        if how == "body":
            bind_body(c)
        elif how[0] == "rigid":
            bind_rigid(c, how[1])
        elif how[0] == "dist":
            bind_distance(c, how[1], how[2])
        made.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in made:
        c.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    if len(made) > 1:
        bpy.ops.object.join()
    low = bpy.context.view_layer.objects.active
    low.name = NAME + "_" + piece
    low.data.name = low.name
    for p in low.data.polygons:
        p.use_smooth = True
    return low


def make_all_lows(parts):
    plan = piece_plan()
    lows = {piece: make_low(piece, parts, plan) for piece in plan}
    lows_dropped = drop_zfighting(lows)
    print("hidden coplanar triangles removed:", lows_dropped)
    return lows


# ---------------------------------------------------------------- review renders
VIEWS = {"front": (0, 6), "three": (-38, 10), "left": (-90, 4), "right": (90, 4), "back": (180, 6), "top": (0, 88), "low": (-30, -10)}


def review(path, views=("three", "left", "front", "back", "right", "top"), size=420, columns=3, distance=96, centre=(0, 12, 2), hide=()):
    scene, cam = T._review_scene(size)
    arm = bpy.data.objects.get(RIG)
    if arm:
        arm.hide_render = True
    tmp = path + ".tile.png"
    tiles = [T._shot(scene, cam, *VIEWS[v], distance, W.rb(*centre), size, tmp) for v in views]
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


def bones_report():
    out = {"bones": len(BONES)}
    xs = [h[0] for n, (p, h, t) in BONES.items()] + [t[0] for n, (p, h, t) in BONES.items()]
    out["x extent"] = (round(min(xs), 2), round(max(xs), 2))
    return out


def setup_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type != "CPU" for d in prefs.devices):
                for d in prefs.devices:
                    d.use = True
                bpy.context.scene.cycles.device = "GPU"
                return kind
        except (TypeError, RuntimeError):
            continue
    return "CPU"


def look(path, shots=None, size=640, samples=48, columns=3, hide=("CinderRocRig",)):
    """Colour renders of the high-detail model with its real shaders, in a dim volcanic light with a warm key."""
    import numpy as np
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    kind = setup_gpu()
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    world = bpy.data.worlds.get("CinderWorld") or bpy.data.worlds.new("CinderWorld")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.42, 0.44, 0.50, 1)
    bg.inputs[1].default_value = 0.9
    scene.world = world
    for name, energy, rot, col in (("CRKey", 4.0, (50, 0, 35), (1.0, 0.86, 0.7)), ("CRRim", 2.5, (65, 0, 215), (0.7, 0.8, 1.0))):
        if not bpy.data.objects.get(name):
            d = bpy.data.lights.new(name, "SUN")
            d.energy = energy
            d.color = col
            o = bpy.data.objects.new(name, d)
            o.rotation_euler = tuple(math.radians(a) for a in rot)
            scene.collection.objects.link(o)
    cam = bpy.data.objects.get("CRCam")
    if not cam:
        data = bpy.data.cameras.new("CRCam")
        data.lens = 60
        cam = bpy.data.objects.new("CRCam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    for h in hide:
        if bpy.data.objects.get(h):
            bpy.data.objects[h].hide_render = True
    shots = shots or [(-38, 10, 100, (0, 13, 0)), (-90, 4, 100, (0, 13, 0)), (0, 6, 100, (0, 13, 0)), (-50, 8, 26, (0, 19, -9)), (-70, 10, 24, (3.4, 3, -1)), (-30, 22, 40, (14, 15.5, -2))]
    tmp = path + ".tile.png"
    tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in shots]
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return kind


# ---------------------------------------------------------------- maps, the skeleton's weights kept, the FBX
BAKES = {"Skin": dict(size=2048, small=1024, ray=0.3, extrusion=0.14), "Plumage": dict(size=2048, small=1024, ray=0.12, extrusion=0.05), "WingL": dict(size=1024, small=512, ray=0.12, extrusion=0.05),
         "WingR": dict(size=1024, small=512, ray=0.12, extrusion=0.05), "Tail": dict(size=512, small=256, ray=0.1, extrusion=0.04),
         "Crest": dict(size=512, small=256, ray=0.1, extrusion=0.04)}
NEON = {"Eyes": Mt.EYE_HEX, "Pupils": Mt.PUPIL_HEX, "Magma": Mt.MAGMA_HEX}


def _fit_uv(obj):
    """A Neon piece wears no map, but Roblox wants its UVs inside the square."""
    uv = obj.data.uv_layers.active
    if not uv:
        obj.data.uv_layers.new(name="UVMap")
        return
    us = [d.uv.x for d in uv.data]
    vs = [d.uv.y for d in uv.data]
    su, sv = max(max(us) - min(us), 1e-6), max(max(vs) - min(vs), 1e-6)
    u0, v0 = min(us), min(vs)
    for d in uv.data:
        d.uv = ((d.uv.x - u0) / su, (d.uv.y - v0) / sv)


def bake_all(parts, lows, only=None):
    import egg_bake as B
    plan = piece_plan()
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    os.makedirs(OUT, exist_ok=True)
    setup_gpu()
    try:
        for piece, spec in BAKES.items():
            if only and piece not in only:
                continue
            hi = [parts[sp][key] for sp, key, _, _ in plan[piece]]
            for o in hi + [lows[piece]]:
                o.hide_viewport = False
                o.hide_render = False
            B._unwrap(lows[piece])
            B.bake("CinderRoc_" + piece, hi, lows[piece], samples=12, **spec)
            for o in hi:
                o.hide_viewport = True
                o.hide_render = True
    finally:
        B.EGG_DIR = saved
    for piece in NEON:
        _fit_uv(lows[piece])


GAME_NAMES = {"Skin": "Skin", "Plumage": "Plumage", "WingL": "WingL", "WingR": "WingR", "Tail": "Tail", "Crest": "Crest", "Eyes": "Eyes", "Pupils": "Pupils", "Magma": "Magma"}


def scrub_fbx(path):
    """The FBX remembers the absolute folder its maps were copied from. Done to the bytes, in place, each machine path becomes filler of
    the same length (so the file's length-prefixed strings stay valid): nothing of this machine is left in it."""
    data = open(path, "rb").read()
    for what in sorted({REPO, os.path.expanduser("~")}, key=len, reverse=True):
        data = data.replace(what.encode(), b"x" * len(what))
    open(path, "wb").write(data)
    return sum(data.lower().count(w) for w in (os.path.basename(os.path.expanduser("~")).lower().encode(), b"/users/"))


def export_fbx(lows):
    """assets/guardians/CinderRoc.fbx: every game piece, skinned, and the skeleton, bound as modelled. The maps go in with it."""
    import cinder_roc_motion as M
    M.set_pose({})
    arm = bpy.data.objects[RIG]
    arm.hide_render = False
    arm.hide_viewport = False
    bpy.ops.object.select_all(action="DESELECT")
    for piece, name in GAME_NAMES.items():
        o = lows[piece]
        o.name = name
        o.hide_viewport = False
        o.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT, NAME + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS",
                             path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                             primary_bone_axis="Y", secondary_bone_axis="X")
    left = scrub_fbx(path)
    return path, os.path.getsize(path) // 1024, "machine path hits left: %d" % left


ADD_BONE_FLIP = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, -1)))


def addbone_cframe(parent, bone):
    """A bone's place under its parent as Roblox's importer gives it: Blender's bone-local value with X and Z flipped, in position and
    rotation alike (checked against the two AddBones of PanguSkinned, which it reproduces to five places)."""
    arm = bpy.data.objects[RIG]
    rel = arm.data.bones[parent].matrix_local.inverted() @ arm.data.bones[bone].matrix_local
    pos = ADD_BONE_FLIP @ rel.to_translation()
    rot = ADD_BONE_FLIP @ rel.to_3x3() @ ADD_BONE_FLIP
    return [round(x, 5) for x in (*pos, *[rot[i][j] for i in range(3) for j in range(3)])]


def bone_use(lows):
    """For each bone, the pieces that weight to it and how many bones each of those pieces uses (a piece with one bone is single-bone: the
    importer drops a bone only such pieces use)."""
    use = {}
    for piece, o in lows.items():
        names = {g.name for g in o.vertex_groups}
        weighted = set()
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight > 0:
                    weighted.add(o.vertex_groups[g.group].name)
        for n in weighted:
            use.setdefault(n, []).append((piece, len(weighted)))
    return use


def write_placements(path, lows):
    use = bone_use(lows)
    need = [n for n in BONES if n != "Root" and not any(count > 1 for _, count in use.get(n, []))]
    glow = {"Magma": Mt.MAGMA_HEX, "Eyes": Mt.EYE_HEX, "Pupils": Mt.PUPIL_HEX}
    rgb = lambda h: "Color3.fromRGB(%d, %d, %d)" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda v: "Vector3.new(%s)" % ", ".join(("%.4f" % c).rstrip("0").rstrip(".") for c in v)
    lines = ["-- The Cinder Roc, Ember Peak's guardian, with a skeleton (tools/blender/guardians/cinder_roc.py, assets/guardians/CinderRoc.fbx). Used by",
             "-- GuardianBuilder.storeSkinned for the guardian EmberXuanwu (the id stays: saves, records and quests key off it).",
             "return {", '    Rig = "CinderRocSkinned",', "    Fit = {"]
    for name in ("Hips", "Head", "LeftThigh", "RightShin"):
        lines.append("        %s = %s," % (name, f(BONES[name][1])))
    lines += ["    },",
              "    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, from Blender's rest pose. The",
              "    -- import is a half turn about Y: a bone-local value is Blender's with X and Z flipped, in position and rotation alike.",
              "    AddBones = {"]
    for n in need:
        parent = BONES[n][0]
        c = addbone_cframe(parent, n)
        lines.append('        %s = { Parent = "%s", CFrame = CFrame.new(%s) },' % (n, parent, ", ".join(("%g" % x) for x in c)))
    lines += ["    },", "    Glow = {"]
    for k, h in glow.items():
        lines.append("        %s = %s," % (k, rgb(h)))
    lines += ["    },", "}"]
    with open(path, "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    return need


def write_report(path, lows, parts):
    import json
    arm = bpy.data.objects[RIG]
    use = bone_use(lows)
    rep = {"Pieces": {}, "Bones": len([n for n in BONES if n != "Root"]), "Joints": len(joints())}
    lo = V((1e9, 1e9, 1e9))
    hi = -lo
    for piece, o in lows.items():
        pts = _points(o)
        rep["Pieces"][GAME_NAMES[piece]] = {"Triangles": tris(o), "Vertices": len(o.data.vertices), "BonesUsed": len({n for n, lst in use.items() if any(p == piece for p, _ in lst)}),
                                            "Glow": ("#" + NEON[piece]) if piece in NEON else None, "Size": [round(float(x), 2) for x in (pts.max(axis=0) - pts.min(axis=0))]}
        lo = V(map(min, lo, pts.min(axis=0)))
        hi = V(map(max, hi, pts.max(axis=0)))
    rep["Bounds"] = {"Min": [round(x, 2) for x in lo], "Max": [round(x, 2) for x in hi]}
    rep["Triangles"] = sum(p["Triangles"] for p in rep["Pieces"].values())
    rep["MeshParts"] = len(rep["Pieces"])
    with open(path, "w", encoding="utf8") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    return rep


def run_qa(lows, profile="roblox"):
    """blender-asset-qa on each game piece (the folder of its qa_check.py in $CINDER_QA_DIR)."""
    qa_dir = os.environ.get("CINDER_QA_DIR")
    if not qa_dir:
        return "skipped: set CINDER_QA_DIR to the folder holding qa_check.py"
    sys.path.insert(0, qa_dir)
    import qa_check
    names = [GAME_NAMES[p] for p in lows]
    r = qa_check.run(objects=names, profile=profile)            # one asset: its pieces are judged together (the eyes sit in the head)
    return {"pass": r["pass"], "errors": r["errors"], "warnings": r["warnings"][:24], "zfighting": str(r.get("zfighting"))[:1800], "floating": str(r.get("floating"))[:600]}


def build_final(out_blend=None, placements=None, report=None):
    info, parts, lows = build_lows(real=True)
    bake_all(parts, lows)
    path = export_fbx(lows)
    notes = {}
    if placements:
        notes["AddBones"] = write_placements(placements, lows)
    if report:
        notes["report"] = write_report(report, lows, parts)
    notes["qa"] = run_qa(lows)
    if out_blend:
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    return info, count(lows), path, notes


def build_lows(real=False):
    """The high-detail parts, then each game piece reduced and weighted (no maps yet), the skeleton ready to pose."""
    global WANT_REAL
    WANT_REAL = real
    info, parts = build_all()
    lows = make_all_lows(parts)
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o not in lows.values():
            o.hide_render = True
            o.hide_viewport = True
    for name, o in lows.items():
        attach(o)
        o.data.materials.clear()
        o.data.materials.append(_mat({"Skin": "skin", "Plumage": "feather", "WingL": "feather", "WingR": "feather", "Tail": "ember", "Crest": "ember", "Magma": "magma", "Eyes": "magma", "Pupils": "horn"}[name]))
    return info, parts, lows


def count(lows):
    out, infl = {}, 0
    for k, o in lows.items():
        out[k] = tris(o)
        infl = max(infl, max((len(v.groups) for v in o.data.vertices), default=0))
    out["total"] = sum(out.values())
    out["max influences"] = infl
    return out


def stress(path, size=420):
    """The skeleton bent to what the fight asks of it, in clay."""
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    print(count(lows))
    folded = M.FOLDED
    rows = [("bound", {}, (0, 0)),
            ("wings folded", M.stance(wings=(folded, folded))[0], (0, 0)),
            ("deep crouch", M.stance({"Hips": (-14, 0, 0), "Spine": (6, 0, 0), "Chest": (10, 0, 0), "Neck1": (-10, 0, 0), "Neck2": (14, 0, 0), "Head": (10, 0, 0)}, (-3.6, 0.6), (folded, folded))[0], (-3.6, 0.6))]
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    for name, pose, shift in rows:
        M.set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, -38, 8, 100, W.rb(0, 12, 0), size, tmp))
        tiles.append(T._shot(scene, cam, -90, 4, 100, W.rb(0, 12, 0), size, tmp))
        tiles.append(T._shot(scene, cam, 0, 6, 100, W.rb(0, 12, 0), size, tmp))
    T._sheet(tiles, 3, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def wing_gallery(path, size=380):
    """The wing postures the moves are built from, in clay: from the front three-quarter, from above."""
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    postures = [("bound", {}, {}), ("folded", M.FOLDED, M.FOLDED),
                ("half", dict(sweep=-25, lift=18, bank=-15, elbow=40, wrist=-45, fan=0.7), dict(sweep=-25, lift=18, bank=-15, elbow=40, wrist=-45, fan=0.7)),
                ("raised", dict(sweep=-30, lift=72, bank=-25, elbow=25, wrist=-20, fan=0.9), dict(sweep=-30, lift=72, bank=-25, elbow=25, wrist=-20, fan=0.9)),
                ("down", dict(sweep=-20, lift=-62, bank=20, elbow=10, wrist=-5, fan=0.8), dict(sweep=-20, lift=-62, bank=20, elbow=10, wrist=-5, fan=0.8)),
                ("scythe cocked / contact", dict(sweep=-70, lift=40, bank=-25, elbow=10, wrist=-5, fan=1.1), dict(sweep=110, lift=2, bank=10, elbow=0, wrist=0, fan=0.1))]
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    for name, wl, wr in postures:
        pose, shift, _ = M.build_pose(wl=wl, wr=wr)
        M.set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, -32, 18, 105, W.rb(0, 14, 0), size, tmp))
        tiles.append(T._shot(scene, cam, -90, 3, 105, W.rb(0, 14, 0), size, tmp))
        tiles.append(T._shot(scene, cam, 0, 84, 105, W.rb(0, 14, 0), size, tmp))
    T._sheet(tiles, 3, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def fold_test(path, size=380):
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    variants = [dict(sweep=-52, lift=-3, bank=-50, elbow=130, wrist=-130, fan=0.05, sec_fan=0.1),
                dict(sweep=-45, lift=2, bank=-62, elbow=124, wrist=-126, fan=0.0, sec_fan=0.0),
                dict(sweep=-58, lift=-6, bank=-40, elbow=134, wrist=-136, fan=0.0, sec_fan=0.05)]
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    for v in variants:
        pose, shift, _ = M.build_pose(wl=v, wr=v)
        M.set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, 140, 18, 80, W.rb(0, 14, 2), size, tmp))
        tiles.append(T._shot(scene, cam, -90, 4, 80, W.rb(0, 14, 2), size, tmp))
        tiles.append(T._shot(scene, cam, -35, 22, 80, W.rb(0, 14, 2), size, tmp))
    T._sheet(tiles, 3, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def strips(names, out_dir, frames=8, size=300, side_only=False):
    """A strip of frames of each move from three-quarter and from the side (the lows in clay), for judging the motion by eye."""
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    scene, cam = T._review_scene(size)
    allm = M.moves()
    allm.update({"state_" + k: [v] for k, v in M.states().items()})
    for name in names:
        keys = allm[name]
        end = keys[-1]["t"]
        times = M.STRIP_TIMES.get(name) or [end * i / (frames - 1) for i in range(frames)]
        tiles = []
        views = ((-38, 12, 100, (0, 13, -2)), (-90, 4, 100, (0, 13, -2)))
        if side_only:
            views = views[1:]
        for yaw, pitch, dist, centre in views:
            for t in times:
                pose, shift, _ = M.sample(keys, t)
                M.set_pose(pose, shift)
                tiles.append(T._shot(scene, cam, yaw, pitch, dist, W.rb(*centre), size, os.path.join(out_dir, "_t.png")))
        T._sheet(tiles, len(times), os.path.join(out_dir, "strip_%s.png" % name), size)
    return times


# ---------------------------------------------------------------- numeric checks
def skin_arrays(lows):
    """Per piece: the bind vertices (Roblox space), each vertex's four bones and weights."""
    import numpy as np
    names = list(BONES)
    index = {n: i for i, n in enumerate(names)}
    out = {}
    for piece, o in lows.items():
        n = len(o.data.vertices)
        bi = np.zeros((n, 4), dtype=np.int64)
        w = np.zeros((n, 4))
        gname = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            for k, g in enumerate(sorted(v.groups, key=lambda x: -x.weight)[:4]):
                bi[v.index, k] = index[gname[g.group]]
                w[v.index, k] = g.weight
        out[piece] = (_points(o), bi, w)
    return out, names


def skinned(arrs, names, pose, shift):
    """Every piece's vertices under a pose: linear blend skinning about each bone's head, as the game's bones do."""
    import numpy as np
    import cinder_roc_motion as M
    st = M.fk(pose, shift)
    R = np.array([np.array(st[n][0]) for n in names])
    H = np.array([list(st[n][1]) for n in names])
    H0 = np.array([BONES[n][1] for n in names])
    out = {}
    for piece, (v, bi, w) in arrs.items():
        p = np.zeros_like(v)
        for k in range(4):
            b = bi[:, k]
            p += w[:, k:k + 1] * (H[b] + np.einsum("nij,nj->ni", R[b], v - H0[b]))
        out[piece] = p
    return out


def rot_angle(a, b):
    import cinder_roc_motion as M
    return math.degrees((M.mat(a).inverted() @ M.mat(b)).to_quaternion().angle)


def twist_about(e, axis):
    import cinder_roc_motion as M
    q = M.mat(e).to_quaternion()
    deg = math.degrees(2 * math.atan2(V((q.x, q.y, q.z)).dot(axis), q.w))
    return (deg + 180) % 360 - 180


def run_checks():
    import numpy as np
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    arrs, names = skin_arrays(lows)
    report = {"tris": count(lows)}
    mirror_err = 0.0
    for n, (p, h, t) in BONES.items():
        if n.startswith("Left"):
            q = BONES["Right" + n[4:]]
            mirror_err = max(mirror_err, (V(h) - V((-q[1][0], q[1][1], q[1][2]))).length, (V(t) - V((-q[2][0], q[2][1], q[2][2]))).length)
    report["bind symmetry error (studs)"] = round(mirror_err, 5)
    allm = M.moves()
    sts = M.state_tables()
    base = {n: (0, 0, 0) for n in M.JOINTS}
    guardian = M.full(*sts["Guardian"], base)
    targets = {"WingScythe": "Guardian", "CinderGale": "Guardian", "TalonDive": "Guardian", "Land": "Guardian", "Awaken": "Guardian", "Enrage": "Enraged", "Weaken": "Weakened"}
    ends = {"WingScythe": 1.9, "CinderGale": 2.5, "TalonDive": 1.95, "Land": 0.9, "Awaken": 2.8, "Enrage": 1.4, "Weaken": 1.9}
    contact = {"WingScythe": 0.8, "CinderGale": 1.3, "TalonDive": 0.9, "Land": 0.0, "Weaken": 0.95, "Enrage": 0.98}
    twist_axes = {n: M.rest_dir(n) for n in ("LeftUpperArm", "LeftForearm", "LeftHand", "RightUpperArm", "RightForearm", "RightHand", "Neck1", "Neck2", "Neck3", "Head", "LeftThigh", "RightThigh")}
    moves_report = {}
    for name, keys in allm.items():
        frames, plants = M.bake_move(keys)
        res = {"frames": len(frames), "length s": ends[name]}
        low_y, low_who = 9e9, ""
        step_max, step_who = 0.0, ""
        slide = 0.0
        height_err = 0.0
        tw = {n: 0.0 for n in twist_axes}
        prev_tips = None
        tipspeed = []
        prev = None
        for f, fr in enumerate(frames):
            t = f / 30.0
            pose = {n: tuple(v[:3]) for n, v in fr.items()}
            shift = (fr["Hips"][3], fr["Hips"][4])
            airborne = name == "TalonDive" and 0.9 < t < 1.9
            sk = skinned(arrs, names, pose, shift)
            if not airborne:
                for piece, p in sk.items():
                    if piece in ("Eyes", "Pupils"):
                        continue
                    mi = int(np.argmin(p[:, 1]))
                    if p[mi, 1] < low_y:
                        low_y, low_who = float(p[mi, 1]), "%s (%s)" % (piece, names[int(arrs[piece][1][mi, int(np.argmax(arrs[piece][2][mi]))])])
            st = M.fk(pose, shift)
            tips = {n: M.tip(st, n) for n in BONES if n != "Root"}
            if prev_tips:
                for n, v in tips.items():
                    d = (v - prev_tips[n]).length
                    if d > step_max:
                        step_max, step_who = d, "%s frame %d" % (n, f)
            prev_tips = tips
            for n, ax in twist_axes.items():
                tw[n] = max(tw[n], abs(twist_about(fr[n][:3], ax)))
            for tag, i in (("Left", 0), ("Right", 1)):
                if plants[f][i]:
                    ball = st[tag + "Foot"][1]
                    height_err = max(height_err, abs(ball.y - M.BALL_REST.y))
                    if prev and prev[2][i] and prev[3] is not None:
                        slide = max(slide, math.hypot(ball.x - prev[3][tag].x, ball.z - prev[3][tag].z))
            prev = (f, fr, plants[f], {"Left": st["LeftFoot"][1], "Right": st["RightFoot"][1]})
            tipspeed.append((tips["RightPrim2B"], tips["LeftPrim2B"], st["Hips"][1]))
        res["lowest vertex y (studs, ground moves)"] = round(low_y, 2)
        res["lowest vertex belongs to"] = low_who
        res["biggest bone-end step (studs per frame)"] = (round(step_max, 2), step_who)
        res["foot slide per planted frame (studs, max)"] = round(slide, 3)
        res["planted ball height error (studs, max)"] = round(height_err, 3)
        res["max twist (deg): wings, neck, hips"] = {k: round(v, 1) for k, v in tw.items() if v > 20}
        res["start pose vs Guardian (max deg)"] = round(max(rot_angle(guardian[n][:3], frames[0][n][:3]) for n in M.JOINTS), 1)
        tgt = M.full(*sts[targets[name]], base)
        res["end pose vs %s (max deg, bone)" % targets[name]] = max((round(rot_angle(tgt[n][:3], frames[-1][n][:3]), 1), n) for n in M.JOINTS)
        if name in contact:
            at = int(round(contact[name] * 30))
            if name == "WingScythe":
                sp = [(tipspeed[i + 1][0] - tipspeed[i][0]).length for i in range(len(tipspeed) - 1)]
                peak = int(np.argmax(sp)) + 1
                res["wing-tip speed peak frame / contact frame"] = (peak, at, round(max(sp) * 30, 0))
            elif name == "CinderGale":
                dy = [tipspeed[i][0].y - tipspeed[i + 1][0].y for i in range(len(tipspeed) - 1)]
                res["wing-tip downstroke peak frame / contact frame"] = (int(np.argmax(dy)) + 1, at, round(max(dy) * 30, 0))
            elif name == "TalonDive":
                first = next((i for i, pl in enumerate(plants) if not (pl[0] and pl[1])), None)
                res["first frame with a foot in the air / leave-ground frame"] = (first, at)
            elif name in ("Weaken", "Enrage"):
                hy = [t[2].y for t in tipspeed]
                acc = [abs(hy[i + 1] - hy[i]) for i in range(len(hy) - 1)]
                res["hips fastest drop frame / contact frame"] = (int(np.argmax(acc)) + 1, at)
            elif name == "Land":
                hy = [t[2].y for t in tipspeed]
                res["hips lowest frame (crush)"] = (int(np.argmin(hy)), "touchdown frame 0")
        moves_report[name] = res
    report["moves"] = moves_report
    gaits = {}
    for name in M.GAITS:
        g = M.GAITS[name]
        frames, prev = [], guardian
        slip, hgt, lowy = [0.0, 0.0], [0.0, 0.0], 9e9
        stride = M.stride_of(g)
        zs = {"Left": [], "Right": []}
        n = 48
        first = None
        for i in range(n + 1):
            ph = (i / n) % 1.0
            pose, shift, pl = M.gait_key(name, ph)
            sk = skinned(arrs, names, pose, shift)
            lowy = min(lowy, min(float(p[:, 1].min()) for k, p in sk.items() if k not in ("Eyes", "Pupils")))
            st = M.fk(pose, shift)
            if i == 0:
                first = {k: tuple(v) for k, v in pose.items()}
            if i == n:
                loop = max(rot_angle(first[b], pose[b]) for b in first)
            for tag, off in (("Left", 0.0), ("Right", 0.5)):
                p_ = (ph + off) % 1.0
                if p_ < g["stance"] * 0.9 and i < n:
                    ball = st[tag + "Foot"][1]
                    tau_ = ph + (1.0 if ph < off else 0.0)          # time through the cycle, unwrapped from the foot's own touchdown
                    zs[tag].append((ball.z - stride * tau_, ball.y))
        for k, tag in enumerate(("Left", "Right")):
            zz = [a for a, b in zs[tag]]
            hh = [b for a, b in zs[tag]]
            slip[k] = max(zz) - min(zz)
            hgt[k] = max(hh) - min(hh)
        gaits[name] = {"stride (studs)": round(stride, 2), "stance share": g["stance"], "planted-foot slip (studs, L/R)": [round(x, 3) for x in slip],
                       "planted-foot height drift (studs, L/R)": [round(x, 3) for x in hgt], "lowest vertex y": round(lowy, 2), "loop closing (max deg, frame 0 vs 1)": round(loop, 4)}
    report["gaits"] = gaits
    states_report = {}
    for name, (pose, shift) in sts.items():
        sk = skinned(arrs, names, {n: tuple(v) for n, v in pose.items()}, shift)
        states_report[name] = round(min(float(p[:, 1].min()) for k, p in sk.items() if k not in ("Eyes", "Pupils")), 2)
    report["lowest vertex y per state pose"] = states_report
    return report


def state_sheet(path, size=330):
    """Every state pose and the two idle flourishes, from three-quarter and from the side, in clay."""
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    sts = M.state_tables()
    names = ["Guardian", "Dormant", "Weakened", "Enraged", "Returning", "Display", "Preen"]
    for yaw, pitch in ((-38, 12), (-90, 4)):
        for n in names:
            pose, shift = sts[n]
            M.set_pose({k: tuple(v) for k, v in pose.items()}, shift)
            tiles.append(T._shot(scene, cam, yaw, pitch, 85, W.rb(0, 12, -1), size, tmp))
    T._sheet(tiles, len(names), path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


def dormant_test(path, size=330):
    import cinder_roc_motion as M
    info, parts, lows = build_lows()
    scene, cam = T._review_scene(size)
    tmp = path + ".tile.png"
    tiles = []
    D = M.states()["Dormant"]
    variants = [dict(Chest=(-6, -10, 0), Neck1=(-20, -30, 0), Neck2=(24, -40, 0), Neck3=(14, -30, 0), Head=(4, -30, 0)),
                dict(Chest=(-6, -12, 0), Neck1=(-10, -40, 0), Neck2=(12, -50, 0), Neck3=(4, -30, 0), Head=(0, -30, 0)),
                dict(Chest=(-8, -14, 0), Neck1=(-6, -55, 0), Neck2=(8, -60, 0), Neck3=(0, -40, 0), Head=(-8, -20, 0))]
    for v in variants:
        k = M.merge(D, dict(body=v))
        pose, shift, _ = M.build_pose(body=k["body"], shift=k["shift"], wl=k["wl"], wr=k["wr"], feet=k["feet"], tail=k["tail"], crest=k["crest"])
        M.set_pose(pose, shift)
        for yaw, pitch in ((-38, 14), (-90, 4), (60, 24)):
            tiles.append(T._shot(scene, cam, yaw, pitch, 60, W.rb(0, 11, -1), size, tmp))
    T._sheet(tiles, 3, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    stage = argv[0] if argv else "form"
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(REPO, "renders", "cinder_roc")
    os.makedirs(out_dir, exist_ok=True)
    if stage == "look":
        WANT_REAL = True
        print(build_preview())
        print(look(os.path.join(out_dir, "look.png"), size=560, samples=40))
    if stage == "preview":
        print(build_preview())
        review(os.path.join(out_dir, "preview.png"), size=420, distance=110, centre=(0, 13, 2))
    if stage == "form":
        print(build_form())
        review(os.path.join(out_dir, "form.png"), size=420, distance=70, centre=(0, 12, -1))
        print(bones_report())
    if stage == "final":
        blend = os.path.join(out_dir, "CinderRoc_final.blend")
        pl = argv[argv.index("--placements") + 1] if "--placements" in argv else None
        rp = argv[argv.index("--report") + 1] if "--report" in argv else None
        import json
        print("FINAL " + json.dumps(build_final(blend, pl, rp), default=str))
    if stage == "stress":
        stress(os.path.join(out_dir, "stress.png"))
    if stage == "wings":
        wing_gallery(os.path.join(out_dir, "wings.png"))
    if stage == "fold":
        fold_test(os.path.join(out_dir, "fold.png"))
    if stage == "strip":
        names = argv[1].split(",")
        print(strips(names, out_dir, side_only="--side" in argv))
    if stage == "checks":
        import json
        rep = run_checks()
        print("CHECKS " + json.dumps(rep, indent=1, default=str))
    if stage == "clips":
        import cinder_roc_motion as M
        path = argv[1] if len(argv) > 1 else os.path.join(out_dir, "CinderRocClips.lua")
        print(M.write_clips(path))
    if stage == "scrub":
        print("scrubbed, hits left:", scrub_fbx(os.path.join(OUT, NAME + ".fbx")))
    if stage == "states":
        state_sheet(os.path.join(out_dir, "states.png"))
    if stage == "dormant":
        dormant_test(os.path.join(out_dir, "dormant.png"))

"""The review lab for the Demonic sword (run inside Blender, headless): the same plumbing as secret_lab.py (imported, not edited) with
three lighting setups and a real R15 hand stand-in.

- "clay": a dark grey room, a big soft key beside the camera, a faint fill and a rim, a matte grey material: form, nothing else;
- "neutral": the studio dome (soft sky, a few softboxes): plain material view;
- "dramatic": a nearly black room, one hard cold rim from behind and a low warm key: what a polished bevel and a black blade do
  in the dark;
- r15_hand(): the blocky R15 right hand and lower arm at their true size, placed as CombatFx holds the weapon.

Everything renders to renders/faction_weapons_v2/Demonic/ (local, never committed). Roblox axes (point toward -Z).
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

import secret_kit as SK
import secret_lab as L
import sword_demonic_text as T

V = Vector
REPO = SK.REPO
REVIEW = os.environ.get("SD_REVIEW") or os.path.join(REPO, "renders", "faction_weapons_v2", "Demonic")
L.REVIEW = REVIEW
SK.REVIEW = REVIEW
MODE = "clay"


def set_mode(mode):
    global MODE
    MODE = mode


def _env(mode, w=1024, h=512):
    name = "SD_Env_" + mode
    img = bpy.data.images.get(name)
    if img is not None:
        return img
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True)
    ys = (np.arange(h) + 0.5) / h
    el = (ys - 0.5) * math.pi
    xs = (np.arange(w) + 0.5) / w * 2 * math.pi - math.pi
    base = np.zeros((h, w, 3), dtype=np.float32)

    def box(az, e, daz, de, power, tint=(1, 1, 1)):
        d_az = np.abs((xs[None, :] - az + math.pi) % (2 * math.pi) - math.pi)
        m = (d_az < daz) & (np.abs(el[:, None] - e) < de)
        soft = np.clip(1 - np.maximum(d_az / daz, np.abs(el[:, None] - e) / de), 0, 1) ** 0.35
        base[...] += (m * soft)[..., None] * power * np.array(tint, dtype=np.float32)
    if mode == "dramatic":
        base[:] = 0.012
        box(2.4, 0.35, 0.18, 0.55, 14.0, (0.55, 0.7, 1.0))     # a hard cold strip behind
        box(-0.6, -0.1, 0.5, 0.12, 2.2, (1.0, 0.55, 0.3))      # a low warm key
        box(0.2, 0.9, 0.3, 0.15, 3.0, (0.9, 0.9, 1.0))         # a small overhead card
    else:
        up = np.clip((el + 0.15) / 1.0, 0, 1)
        sky = (0.16 + 0.55 * up ** 0.8)[:, None]
        floor = np.clip(0.05 + 0.1 * (el + math.pi / 2) / (math.pi / 2), 0, 1)[:, None]
        lum = np.where(el[:, None] > -0.05, sky, floor) * np.ones((1, w))
        base[:] = lum[..., None] * np.array([0.82, 0.9, 1.0], dtype=np.float32)
        box(0.7, 0.8, 0.5, 0.3, 5.0, (1.0, 0.97, 0.92))
        box(-2.4, 0.5, 0.35, 0.35, 3.5, (0.9, 0.95, 1.0))
        box(2.6, 0.2, 0.7, 0.12, 1.6)
        box(-1.0, 0.05, 0.4, 0.1, 1.2, (1.0, 0.9, 0.8))
        box(0.0, 1.35, 1.2, 0.2, 2.2)
    px = np.ones((h, w, 4), dtype=np.float32)
    px[..., :3] = base
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def _lights(scene, mode):
    cam = scene.camera
    for o in [o for o in bpy.data.objects if o.name.startswith("SK_Light")]:
        bpy.data.objects.remove(o, do_unlink=True)
    if mode != "clay":
        return
    target = V((0, 0, -11.0))       # the subject, in the camera's own space (it looks down its -Z)
    specs = (("Key", V((-7.0, 4.5, -2.0)), 2600.0, 5.0, (1.0, 0.97, 0.93)),
             ("Fill", V((6.0, -2.0, -1.0)), 300.0, 8.0, (0.85, 0.9, 1.0)),
             ("Rim", V((3.0, 4.0, -19.0)), 2200.0, 5.0, (0.9, 0.95, 1.0)))
    for nm, loc, power, size, col in specs:
        ld = bpy.data.lights.new("SK_Light" + nm, "AREA")
        ld.energy, ld.size, ld.color = power, size, col
        o = bpy.data.objects.new("SK_Light" + nm, ld)
        scene.collection.objects.link(o)
        o.parent = cam
        o.location = loc
        o.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()


def _world(scene, sky=True, exposure=1.0):
    w = bpy.data.worlds.get("SD_World") or bpy.data.worlds.new("SD_World")
    w.use_nodes = True
    t = w.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    out = t.nodes.new("ShaderNodeOutputWorld")
    bg = t.nodes.new("ShaderNodeBackground")
    if not sky:
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 1.0
        _lights(scene, "none")
    elif MODE == "clay":
        bg.inputs["Color"].default_value = (0.055, 0.058, 0.07, 1)
        bg.inputs["Strength"].default_value = 1.0
        _lights(scene, "clay")
    else:
        env = t.nodes.new("ShaderNodeTexEnvironment")
        env.image = _env(MODE)
        t.links.new(env.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = exposure
        _lights(scene, MODE)
    t.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w


L._world = _world

# re-export the plumbing
lab, shoot, sheet, save_png, bounds, black, clay, clay_material, set_visible = (L.lab, L.shoot, L.sheet, L.save_png, L.bounds, L.black, L.clay,
                                                                                L.clay_material, L.set_visible)


def shoot_view(objs, view, size=(360, 640), samples=40, ortho=False, centre=None, span=None, lens=60, mode=None):
    if mode:
        set_mode(mode)
    L.lab()
    return L.shoot(objs, view, size=size, samples=samples, ortho=ortho, centre=centre, span=span, lens=lens)


# ---------- the R15 hand stand-in ----------
# the real sizes (tools/blender/animation/r15_rig.py): RightHand 0.81 x 0.27 x 0.91, RightLowerArm 0.82 x 0.97 x 0.91, the grip
# attachment at the hand's (0, -0.137, 0), the weapon turned by -10 degrees about X in the hand's frame (GripAttachment -90 times
# CombatFx's GRIP_TURN 80 for a sword), the wrist: the forearm's (0, -0.463, 0) joined to the hand's (0, 0.114, 0)
HAND = (0.81, 0.27, 0.91)
FOREARM = (0.82, 0.97, 0.91)
GRIP_IN_HAND = V((0, -0.137, 0))
WRIST_FOREARM = V((0, -0.463, 0))
WRIST_HAND = V((0, 0.114, 0))


def hand_frame():
    """Hand-frame (x, y, z) points to the weapon's Roblox frame: a point p_h in the hand's frame is at R^-1 (p_h - grip) in the
    weapon's, with R the weapon's rotation in the hand (Rx(-10 degrees))."""
    a = math.radians(-10.0)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return R, np.array(GRIP_IN_HAND)


def hand_boxes():
    """The hand's and forearm's boxes in the weapon's Roblox frame: [(name, centre (3,), size (3,), rotation matrix (3,3))]
    where the matrix takes box-local axes to the weapon's axes."""
    R, grip = hand_frame()
    Rinv = R.T
    hand_c = np.zeros(3)                                         # the hand's centre in the hand's frame
    fore_c = hand_c + np.array(WRIST_HAND) - np.array(WRIST_FOREARM)   # wrist: forearm point (0,-0.463,0) is hand point (0,0.114,0)
    # forearm centre = hand centre + hand's (0,0.114,0) - forearm's (0,-0.463,0) taken as hand-frame offsets
    fore_c = hand_c + np.array(WRIST_HAND) + np.array([0, 0.463, 0])
    out = []
    for name, c, size in (("hand", hand_c, HAND), ("forearm", fore_c, FOREARM)):
        out.append((name, Rinv @ (c - grip), np.array(size), Rinv))
    return out


def r15_hand(coll, alpha=0.4):
    """The two boxes as Blender objects (rounded a little), semi-transparent; returns them."""
    import bmesh
    objs = []
    mat = bpy.data.materials.get("SD_Skin") or bpy.data.materials.new("SD_Skin")
    mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.8, 0.55, 0.42, 1)
    b.inputs["Roughness"].default_value = 0.7
    b.inputs["Alpha"].default_value = alpha
    for name, c, size, Rm in hand_boxes():
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]
            v.co.y *= size[2]       # Blender y = -Roblox z
            v.co.z *= size[1]       # Blender z = Roblox y
        me = bpy.data.meshes.new("SD_" + name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("SD_" + name, me)
        coll.objects.link(o)
        # the box's orientation: a rotation by +10 degrees about the Roblox X axis (Rinv = Rx(+10)), which in Blender is the same
        # rotation about X (x is shared, the sense is kept by the y/z swap with the sign on y)
        ang = math.atan2(Rm[2, 1], Rm[1, 1])
        o.rotation_euler = (ang, 0, 0)
        o.location = V((c[0], -c[2], c[1]))
        o.data.materials.append(mat)
        md = o.modifiers.new("b", "BEVEL")
        md.width = 0.06
        md.segments = 2
        objs.append(o)
    return objs


def min_distance(points_rb, boxes=None):
    """The smallest signed distance from Roblox-space points (N, 3) to the hand's and forearm's boxes (negative inside)."""
    boxes = boxes or hand_boxes()
    best = np.full(len(points_rb), np.inf)
    for _, c, size, Rm in boxes:
        local = (points_rb - c) @ Rm        # into the box's own axes
        q = np.abs(local) - size / 2
        outside = np.linalg.norm(np.maximum(q, 0), axis=1)
        inside = np.minimum(np.max(q, axis=1), 0)
        best = np.minimum(best, outside + inside)
    return best

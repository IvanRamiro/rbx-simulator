"""An exact stand-in for the game's R15 character, in Blender: a real armature with the joint offsets
measured in Play (2026-11-04), controllers keyed on empties, and two-bone IK for the arms and legs.

Author a move by animating the WEAPON through space (grip position, where it points): the hands, arms
and legs follow it, so its path is what you meant, both hands stay on a spear's shaft, and the feet
stay planted. Each frame is baked to the rotation each game joint needs (AnimationConstraint.Transform:
Part1 = Part0 * C0 * Transform * C1:Inverse(), every C0 and C1 unrotated), written to Lua by export().

Space: all authoring values are Roblox's, relative to the HumanoidRootPart: +X the character's right,
+Y up, -Z ahead, the floor at Y -2.774. Blender shows it as (x, -z, y): ahead is +Y.
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

V = Vector
FLOOR = -2.774
ANKLE_Y = -2.54     # a flat foot's ankle
FPS = 60
SCENE_FPS = 120     # keys land on this finer grid, so a tenth of a second can be split

# name: parent part, part, C0 position in parent, C1 position in part
JOINTS = {
    "Root": (None, "LowerTorso", (0, -0.9, 0), (0, -0.183, 0)),
    "Waist": ("LowerTorso", "UpperTorso", (0, 0.183, 0), (0, -0.738, 0)),
    "Neck": ("UpperTorso", "Head", (0, 0.738, 0), (0, -0.583, 0)),
    "RightShoulder": ("UpperTorso", "RightUpperArm", (0.808, 0.52, 0), (-0.408, 0.365, 0)),
    "RightElbow": ("RightUpperArm", "RightLowerArm", (0, -0.309, 0), (0, 0.239, 0)),
    "RightWrist": ("RightLowerArm", "RightHand", (0, -0.463, 0), (0, 0.114, 0)),
    "LeftShoulder": ("UpperTorso", "LeftUpperArm", (-0.808, 0.52, 0), (0.408, 0.365, 0)),
    "LeftElbow": ("LeftUpperArm", "LeftLowerArm", (0, -0.309, 0), (0, 0.239, 0)),
    "LeftWrist": ("LeftLowerArm", "LeftHand", (0, -0.463, 0), (0, 0.114, 0)),
    "RightHip": ("LowerTorso", "RightUpperLeg", (0.405, -0.183, 0), (0, 0.396, 0)),
    "RightKnee": ("RightUpperLeg", "RightLowerLeg", (0, -0.377, 0), (0, 0.355, 0)),
    "RightAnkle": ("RightLowerLeg", "RightFoot", (0, -0.512, 0), (0, 0.094, 0)),
    "LeftHip": ("LowerTorso", "LeftUpperLeg", (-0.405, -0.183, 0), (0, 0.396, 0)),
    "LeftKnee": ("LeftUpperLeg", "LeftLowerLeg", (0, -0.377, 0), (0, 0.355, 0)),
    "LeftAnkle": ("LeftLowerLeg", "LeftFoot", (0, -0.512, 0), (0, 0.094, 0)),
}
SIZES = {
    "LowerTorso": (1.62, 0.37, 0.91), "UpperTorso": (1.62, 1.48, 0.91), "Head": (1.19, 1.2, 1.19),
    "RightUpperArm": (0.82, 1.08, 0.91), "RightLowerArm": (0.82, 0.97, 0.91), "RightHand": (0.81, 0.27, 0.91),
    "LeftUpperArm": (0.82, 1.08, 0.91), "LeftLowerArm": (0.82, 0.97, 0.91), "LeftHand": (0.81, 0.27, 0.91),
    "RightUpperLeg": (0.81, 1.14, 0.9), "RightLowerLeg": (0.81, 1.12, 0.9), "RightFoot": (0.81, 0.28, 0.91),
    "LeftUpperLeg": (0.81, 1.14, 0.9), "LeftLowerLeg": (0.81, 1.12, 0.9), "LeftFoot": (0.81, 0.28, 0.91),
}
GRIP_IN_HAND = V((0, -0.137, 0))
# a weapon's axes in the hand: GripAttachment (-90 about X) times GRIP_TURN (CombatFx)
WEAPON_IN_HAND = {
    "Sword": Matrix.Rotation(math.radians(-90), 3, "X") @ Matrix.Rotation(math.radians(80), 3, "X"),
    "Spear": Matrix.Rotation(math.radians(-90), 3, "X"),
}
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # Roblox -> Blender
# False keeps the sword's and spear's clips exactly as the owner approved them, baked before this was found: their
# hands land up to 0.4 studs from the keyed spot. The punches use the exact arms.
EXACT_ARMS = False


def rx(d): return Matrix.Rotation(math.radians(d), 3, "X")
def ry(d): return Matrix.Rotation(math.radians(d), 3, "Y")
def rz(d): return Matrix.Rotation(math.radians(d), 3, "Z")
def angles(x=0, y=0, z=0): return rx(x) @ ry(y) @ rz(z)   # CFrame.Angles


def point_limb(direction):
    """PoseController's pointLimb: the rotation that swings -Y onto `direction`."""
    down, d = V((0, -1, 0)), V(direction).normalized()
    axis = down.cross(d)
    if axis.length < 1e-4:
        return Matrix.Identity(3)
    return Matrix.Rotation(math.acos(max(-1, min(1, down.dot(d)))), 3, axis.normalized())


def rest_centres():
    """Each part's centre at rest, in the HumanoidRootPart's space."""
    out = {None: V((0, 0, 0))}
    for name, (parent, part, c0, c1) in JOINTS.items():
        out[part] = out[parent] + V(c0) - V(c1)
    return out


def fk(transforms, root_pos=(0, 0, 0)):
    """World (root-space) rotation and centre of every part, from game joint rotations."""
    rot, pos = {None: Matrix.Identity(3)}, {None: V((0, 0, 0))}
    for name, (parent, part, c0, c1) in JOINTS.items():
        t = transforms.get(name, Matrix.Identity(3))
        pivot = pos[parent] + rot[parent] @ V(c0)
        if name == "Root":
            pivot = pivot + V(root_pos)
        rot[part] = rot[parent] @ t
        pos[part] = pivot - rot[part] @ V(c1)
    return rot, pos


def aim(direction, up=(0, 1, 0)):
    """A weapon's rotation: its -Z along `direction`, its +Y as near `up` as that allows."""
    z = -V(direction).normalized()
    y = (V(up) - z * V(up).dot(z))
    if y.length < 1e-3:
        y = V((0, 0, 1)) - z * z.z
    y.normalize()
    x = y.cross(z)
    return Matrix((x, y, z)).transposed()


def two_bone(root, target, a, b, hint):
    """(elbow or knee position, reach ratio): the bend toward `hint` that puts the end on the target."""
    d = target - root
    dist = d.length
    ratio = dist / (a + b)
    dist = min(dist, (a + b) * 0.9995)
    dist = max(dist, abs(a - b) + 1e-3)
    u = d.normalized()
    side = V(hint) - u * V(hint).dot(u)
    side = side.normalized() if side.length > 1e-4 else V((0, 0, -1))
    along = (a * a - b * b + dist * dist) / (2 * dist)
    return root + u * along + side * math.sqrt(max(0, a * a - along * along)), ratio


def limb_rots(shoulder, elbow, wrist, bend_sign, hint):
    """Upper and lower limb rotations: -Y down each length, the hinge on X. A limb's far part folds
    toward -Z for an arm (bend_sign -1), +Z for a leg (bend_sign +1)."""
    du, dl = (elbow - shoulder).normalized(), (wrist - elbow).normalized()
    perp = dl - du * dl.dot(du)
    if perp.length < 1e-3:
        perp = V(hint) - du * V(hint).dot(du)
    perp.normalize()
    yu = -du
    zu = perp if bend_sign > 0 else -perp
    x = yu.cross(zu).normalized()
    upper = Matrix((x, yu, x.cross(yu))).transposed()
    yl = -dl
    lower = Matrix((x, yl, x.cross(yl))).transposed()
    return upper, lower


# ---------- the Blender side: controllers keyed on empties ----------
CONTROLS = ["Pelvis", "Chest", "Head", "Weapon", "LeftHandCtl", "RightFootCtl", "LeftFootCtl", "RightPole", "LeftPole", "RightKneeHint", "LeftKneeHint"]


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for x in list(block):
            block.remove(x)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)


def build_controls():
    scene = bpy.context.scene
    scene.render.fps = SCENE_FPS
    out = {}
    for name in CONTROLS:
        o = bpy.data.objects.new(name, None)
        o.empty_display_size = 0.25
        o.rotation_mode = "QUATERNION"
        scene.collection.objects.link(o)
        out[name] = o
    return out


_last_quat = {}


def key(control, t, pos=None, rot=None):
    """A key on a controller at t seconds: pos (Roblox studs), rot (a Roblox rotation matrix)."""
    frame = round(t * SCENE_FPS) + 1
    if pos is not None:
        control.location = C @ V(pos)
        control.keyframe_insert("location", frame=frame)
    if rot is not None:
        q = (C @ rot @ C.transposed()).to_quaternion()
        last = _last_quat.get(control.name)
        if last is not None and last.dot(q) < 0:
            q = -q
        _last_quat[control.name] = q
        control.rotation_quaternion = q
        control.keyframe_insert("rotation_quaternion", frame=frame)


def read(control):
    m = control.matrix_world
    return C.transposed() @ m.to_translation(), C.transposed() @ m.to_3x3().normalized() @ C


def solve(controls, weapon_kind, left_rel=None):
    """This frame's game joints from the controllers. Returns (joint rotations, root position, parts'
    rot and pos, the worst reach ratio of each limb)."""
    pelvis_pos, pelvis_rot = read(controls["Pelvis"])
    _, chest_rot = read(controls["Chest"])
    _, head_rot = read(controls["Head"])
    weapon_pos, weapon_rot = read(controls["Weapon"])
    rot, pos, t, reach = {None: Matrix.Identity(3)}, {None: V((0, 0, 0))}, {}, {}
    # Root: pelvis_pos is the offset of the Root joint's pivot
    root_pivot = V(JOINTS["Root"][2]) + pelvis_pos
    rot["LowerTorso"] = pelvis_rot
    pos["LowerTorso"] = root_pivot - pelvis_rot @ V(JOINTS["Root"][3])
    t["Root"] = pelvis_rot

    def attach(name, r):
        parent, part, c0, c1 = JOINTS[name]
        pivot = pos[parent] + rot[parent] @ V(c0)
        rot[part] = r
        pos[part] = pivot - r @ V(c1)
        t[name] = rot[parent].transposed() @ r
        return pivot

    attach("Waist", chest_rot)
    attach("Neck", head_rot)

    # the right hand: fixed to the weapon. The left: on it (a spear), or its own controller (a sword)
    w_in_h = WEAPON_IN_HAND[weapon_kind]
    r_hand = weapon_rot @ w_in_h.transposed()
    r_hand_c = weapon_pos - r_hand @ GRIP_IN_HAND
    if left_rel is not None:
        l_hand = weapon_rot @ left_rel[0]
        l_hand_c = weapon_pos + weapon_rot @ left_rel[1]
    else:
        l_hand_c, l_hand = read(controls["LeftHandCtl"])

    def arm(side, hand_rot, hand_c, pole):
        sn, en, wn = side + "Shoulder", side + "Elbow", side + "Wrist"
        parent, upper_part, c0, c1 = JOINTS[sn]
        shoulder = pos[parent] + rot[parent] @ V(c0)
        wrist = hand_c + hand_rot @ V(JOINTS[wn][3])
        a = (V(JOINTS[sn][3]) - V((JOINTS[sn][3][0], 0, 0))).length + V(JOINTS[en][2]).length  # .365 + .309
        b = V(JOINTS[en][3]).length + V(JOINTS[wn][2]).length                                   # .239 + .463
        elbow, ratio = two_bone(shoulder, wrist, a, b, pole)
        upper, lower = limb_rots(shoulder, elbow, wrist, -1, pole)
        if EXACT_ARMS:
            # the shoulder joint sits at the torso's edge, to the side of the arm's own line, so the arm's line starts
            # from there turned with the arm: a few passes put the hand where it was asked to be
            side_offset = -V(JOINTS[sn][3]).x
            for _ in range(4):
                start = shoulder + upper @ V((side_offset, 0, 0))
                elbow, ratio = two_bone(start, wrist, a, b, pole)
                upper, lower = limb_rots(start, elbow, wrist, -1, pole)
        reach[side + "Arm"] = ratio
        attach(sn, upper)
        attach(en, lower)
        # the arm's far joint lands where the solver put it; the hand keeps its rotation
        attach(wn, hand_rot)

    arm("Right", r_hand, r_hand_c, read(controls["RightPole"])[0])
    arm("Left", l_hand, l_hand_c, read(controls["LeftPole"])[0])

    def leg(side, hint):
        hn, kn, an = side + "Hip", side + "Knee", side + "Ankle"
        parent = JOINTS[hn][0]
        hip = pos[parent] + rot[parent] @ V(JOINTS[hn][2])
        ankle, foot_rot = read(controls[side + "FootCtl"])
        a = V(JOINTS[hn][3]).length + V(JOINTS[kn][2]).length
        b = V(JOINTS[kn][3]).length + V(JOINTS[an][2]).length
        knee, ratio = two_bone(hip, ankle, a, b, hint)
        reach[side + "Leg"] = ratio
        upper, lower = limb_rots(hip, knee, ankle, 1, hint)
        attach(hn, upper)
        attach(kn, lower)
        attach(an, foot_rot)

    leg("Right", read(controls["RightKneeHint"])[0])
    leg("Left", read(controls["LeftKneeHint"])[0])
    return t, pelvis_pos, rot, pos, reach


def rel_between(a, b, t0, t1):
    """A left hand's hold on the shaft, easing from one stance's to another's between two times."""
    qa, qb = a[0].to_quaternion(), b[0].to_quaternion()

    def at(t):
        x = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
        x = x * x * (3 - 2 * x)
        return (qa.slerp(qb, x).to_matrix(), a[1].lerp(b[1], x))
    return at


def weapon_path(weapon_pos, weapon_rot, tip_z):
    return weapon_pos + weapon_rot @ V((0, 0, tip_z))


def bake(controls, weapon_kind, length, tip_z, left_rel=None, on_frame=None):
    """Steps through the clip at FPS. Returns a list of per-frame dicts."""
    scene = bpy.context.scene
    frames = []
    n = int(round(length * FPS))
    worst = {}
    for i in range(n + 1):
        f = i * (SCENE_FPS / FPS) + 1
        scene.frame_set(int(f))
        rel = left_rel(i / FPS) if callable(left_rel) else left_rel
        t, root, rot, pos, reach = solve(controls, weapon_kind, rel)
        for k, v in reach.items():
            worst[k] = max(worst.get(k, 0), v)
        wp, wr = read(controls["Weapon"])
        frames.append({"t": t, "root": root.copy(), "tip": weapon_path(wp, wr, tip_z), "grip": wp.copy(), "rot": rot, "pos": pos})
        if on_frame:
            on_frame(i, rot, pos, wp, wr)
    return frames, worst


# ---------- the proxy, for review ----------
def proxy_material(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    m.diffuse_color = (*rgb, 1)
    return m


def box_object(name, size, mat):
    # size is Roblox (x, y, z); the mesh is in Blender's axes (x, -z, y)
    half = [size[0] / 2, size[2] / 2, size[1] / 2]
    vs = [(x, y, z) for x in (-half[0], half[0]) for y in (-half[1], half[1]) for z in (-half[2], half[2])]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    me.update()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_mode = "QUATERNION"
    return o


def build_proxy(weapon_kind, weapon_len, butt_z):
    """Boxes the size of the game's parts, and the weapon: posed by pose_proxy each review frame."""
    skin = proxy_material("Skin", (0.75, 0.72, 0.68))
    torso = proxy_material("Torso", (0.2, 0.4, 0.8))
    legs = proxy_material("Legs", (0.25, 0.25, 0.32))
    steel = proxy_material("Steel", (0.95, 0.75, 0.25))
    out = {}
    for part, size in SIZES.items():
        mat = torso if "Torso" in part else (legs if ("Leg" in part or "Foot" in part) else skin)
        out[part] = box_object("P_" + part, size, mat)
    length = abs(weapon_len - butt_z)
    w = box_object("P_Weapon", (0.14 if weapon_kind == "Spear" else 0.5, 0.14, length), steel)
    w["mid"] = (weapon_len + butt_z) / 2
    out["Weapon"] = w
    return out


def pose_proxy(proxy, rot, pos, wp, wr):
    for part, o in proxy.items():
        if part == "Weapon":
            r = wr
            c = wp + wr @ V((0, 0, o["mid"]))
        else:
            r, c = rot[part], pos[part]
        o.location = C @ c
        o.rotation_quaternion = (C @ r @ C.transposed()).to_quaternion()


def setup_review(size=420):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.72, 0.78, 0.86)
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    cam = bpy.data.cameras.new("ReviewCam")
    cam.lens = 45
    o = bpy.data.objects.new("ReviewCam", cam)
    scene.collection.objects.link(o)
    scene.camera = o
    floor = box_object("Floor", (40, 0.02, 40), proxy_material("Floor", (0.55, 0.57, 0.6)))
    floor.location = C @ V((0, FLOOR - 0.01, 0))
    return o


def look_from(cam, rb_pos, rb_target):
    cam.location = C @ V(rb_pos)
    cam.rotation_euler = (C @ V(rb_target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def to_lua(clips, path, stamp="tools/blender/animation"):
    """clips: {name: {"frames": [...], "extra": {...}}}: per joint, at FPS, quaternions as x, y, z, w."""
    joints = list(JOINTS.keys())
    lines = ["-- Generated by %s from the keyed moves in Blender. Do not edit by hand." % stamp,
             "-- Per clip: Length (s), per joint a flat list of x, y, z, w per frame at Fps; RootPos x, y, z per frame.",
             "return {", "    Fps = %d," % FPS, "    Clips = {"]
    for name, clip in clips.items():
        fr = clip["frames"]
        lines.append("        %s = {" % name)
        lines.append("            Length = %.3f," % ((len(fr) - 1) / FPS))
        for k, v in clip.get("extra", {}).items():
            lines.append("            %s = %s," % (k, v))
        for j in joints:
            vals = []
            for f in fr:
                q = f["t"][j].to_quaternion()
                vals += ["%.3f" % q.x, "%.3f" % q.y, "%.3f" % q.z, "%.3f" % q.w]
            lines.append("            %s = { %s }," % (j, ", ".join(vals)))
        rp = []
        for f in fr:
            rp += ["%.3f" % f["root"].x, "%.3f" % f["root"].y, "%.3f" % f["root"].z]
        lines.append("            RootPos = { %s }," % ", ".join(rp))
        lines.append("        },")
    lines += ["    },", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))

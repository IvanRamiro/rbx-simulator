"""The stances the game already has (PoseController), for the moves to start from and end in: the
owner approved the spear's. Ported number for number."""
from mathutils import Matrix, Vector

import r15_rig as R

V = Vector
deg = R.angles
pl = R.point_limb


def spear_stance(drop, yaw, waist, neck, arms, legs):
    return {
        "Root": R.ry(yaw), "root_pos": (0, drop, 0), "Waist": waist, "Neck": neck,
        "RightShoulder": pl(arms[0]), "RightElbow": arms[1], "RightWrist": arms[2],
        "LeftShoulder": pl(arms[3]), "LeftElbow": arms[4],
        "LeftHip": pl(legs[0]) @ legs[1], "LeftKnee": legs[2], "LeftAnkle": legs[3],
        "RightHip": pl(legs[4]) @ legs[5], "RightKnee": legs[6], "RightAnkle": legs[7],
    }


SPEAR_READY = spear_stance(-0.6, -62, deg(0, -8, 0), deg(0, 55, 0),
    [(-0.64, -0.64, -0.43), deg(50), deg(-25, 15, -45), (0.18, -0.37, -0.91), deg(0)],
    [(-0.68, -0.27, -0.68), deg(0, 30, 0), deg(-60), deg(-20, 15, 20),
     (0.97, -0.24, 0), deg(0, -75, 0), deg(-60), deg(0, 45, -20)])
SPEAR_LOW = spear_stance(-0.8, -55, deg(-6, -5, 0), deg(0, 45, 0),
    [(-0.45, 0.89, 0), deg(130), deg(-45, 0, 45), (0.41, -0.41, -0.82), deg(30)],
    [(-0.83, 0, -0.55), deg(0, 60, 0), deg(-70), deg(-20, 0, 0),
     (0.87, -0.44, 0.22), deg(0, -60, 0), deg(-20), deg(-20, 15, -40)])


def sword_ready():
    # arms-only in the game; the root and feet its slashes settle toward
    return {
        "Root": Matrix.Identity(3), "root_pos": (0, -0.15, 0), "Waist": deg(0, 12, 0), "Neck": Matrix.Identity(3),
        "RightShoulder": pl((0.3, -0.75, -0.59)), "RightElbow": deg(55), "RightWrist": deg(-10),
        "LeftShoulder": pl((-0.32, -0.85, 0.42)), "LeftElbow": deg(30),
    }


def capture(stance, kind):
    """The stance as controller values."""
    t = {k: v for k, v in stance.items() if k != "root_pos"}
    rot, pos = R.fk(t, stance["root_pos"])
    w_in_h = R.WEAPON_IN_HAND[kind]
    wr = rot["RightHand"] @ w_in_h
    wp = pos["RightHand"] + rot["RightHand"] @ R.GRIP_IN_HAND

    def pivot(part, j):
        return pos[part] + rot[part] @ V(R.JOINTS[j][3])

    out = {
        "pelvis_pos": V(stance["root_pos"]), "pelvis_rot": rot["LowerTorso"], "chest_rot": rot["UpperTorso"], "head_rot": rot["Head"],
        "wp": wp, "wr": wr,
        "left_rel": (wr.transposed() @ rot["LeftHand"], wr.transposed() @ (pos["LeftHand"] - wp)),
        "lhand": (pos["LeftHand"], rot["LeftHand"]),
    }
    for side in ("Right", "Left"):
        s = pos["UpperTorso"] + rot["UpperTorso"] @ V(R.JOINTS[side + "Shoulder"][2])
        e = pivot(side + "LowerArm", side + "Elbow")
        wr_p = pivot(side + "Hand", side + "Wrist")
        out[side + "_pole"] = e - (s + wr_p) / 2
        if side + "Hip" in stance:
            h = pos["LowerTorso"] + rot["LowerTorso"] @ V(R.JOINTS[side + "Hip"][2])
            k = pivot(side + "LowerLeg", side + "Knee")
            a = pivot(side + "Foot", side + "Ankle")
            out[side + "_knee"] = k - (h + a) / 2
            out[side + "_foot"] = (a, rot[side + "Foot"])
    return out

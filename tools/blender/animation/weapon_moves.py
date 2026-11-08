"""The sword's and spear's strikes and the bare-handed punches, keyed in Blender on the R15 rig (r15_rig). One clip at a time:
build, bake, review, clear.

    import weapon_moves as M
    M.build("SpearThrust")          # keys one clip and reviews it: writes a contact sheet
    M.export_all()                  # every clip, to src/client/Character/WeaponClips.lua

The owner's notes (2026-11-04): the spear's grip is right, but its slash "goes in different direction"
and its thrust "didn't make a good impression because it lasted a second". The sword is "fine now, but I
need a better movement". So: the slash sweeps one wide way, right to left round the body, and its light is
fitted to where the tip truly went; the thrust coils, lunges with a real step, and holds its reach.
"""
import math
import os
import tempfile

import bpy
import numpy as np
from mathutils import Vector

import r15_rig as R
import stances as S

V = Vector
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))  # the repository, from tools/blender/<folder>/
ANKLE = R.ANKLE_Y
SPEAR_TIP, SWORD_TIP = -6.0, -4.6
SPEAR_BUTT, SWORD_BUTT = 2.2, 0.4


def d(x, y, z):
    return V((x, y, z)).normalized()


def foot(x, z, yaw=0, lift=0, pitch=0):
    return (V((x, ANKLE + lift, z)), R.ry(yaw) @ R.rx(pitch))


class Clip:
    def __init__(self, kind, stance=None):
        self.c = R.build_controls()
        self.kind = kind
        self.ref = stance
        R._last_quat.clear()

    def pose(self, t, p, lead=None):
        """p: controller values. lead: seconds each body part goes ahead of the weapon (overlap: the
        hips start the move, the chest follows, the weapon whips after)."""
        lead = lead or {}
        ht = max(0, t - lead.get("pelvis", 0))
        ct = max(0, t - lead.get("chest", 0))
        ft = max(0, t - lead.get("feet", 0))
        R.key(self.c["Pelvis"], ht, p["pelvis_pos"], p["pelvis_rot"])
        R.key(self.c["Chest"], ct, None, p["chest_rot"])
        R.key(self.c["Head"], ct, None, p["head_rot"])
        R.key(self.c["Weapon"], t, p["wp"], p["wr"])
        R.key(self.c["RightPole"], t, p["Right_pole"])
        R.key(self.c["LeftPole"], t, p["Left_pole"])
        R.key(self.c["RightKneeHint"], ht, p["Right_knee"])
        R.key(self.c["LeftKneeHint"], ht, p["Left_knee"])
        R.key(self.c["RightFootCtl"], ft, p["Right_foot"][0], p["Right_foot"][1])
        R.key(self.c["LeftFootCtl"], ft, p["Left_foot"][0], p["Left_foot"][1])
        if "lhand" in p:
            R.key(self.c["LeftHandCtl"], ct, p["lhand"][0], p["lhand"][1])


def edit(base, **changes):
    p = dict(base)
    p.update(changes)
    return p


# ---------- the spear ----------
def spear_thrust():
    guard = S.capture(S.SPEAR_READY, "Spear")
    low = S.capture(S.SPEAR_LOW, "Spear")
    clip = Clip("Spear")
    knee_f = (0.12, 0.2, -0.5)
    lead = {"pelvis": 0.015, "chest": 0.008, "feet": 0.025}

    clip.pose(0.0, guard)
    # coiled: the weight sinks back onto the rear leg, the shaft draws straight back along its line
    coil = edit(guard,
        pelvis_pos=V((0.05, -0.74, 0.42)), pelvis_rot=R.ry(-74), chest_rot=R.ry(-84), head_rot=R.ry(14) @ R.rx(-3),
        wp=guard["wp"] + V((0.08, -0.12, 0.92)), wr=R.aim(d(0.0, 0.05, -1)),
        Right_foot=foot(0.5, 1.42, -70), Left_foot=foot(-0.12, -1.28, -30))
    clip.pose(0.11, coil, lead)
    clip.pose(0.15, edit(coil, wp=coil["wp"] + V((0, 0, 0.1)), pelvis_pos=coil["pelvis_pos"] + V((0, -0.03, 0.07))), lead)
    # driving: the front foot is already flying, the hips go first
    drive = edit(coil,
        pelvis_pos=V((-0.02, -0.62, -0.5)), pelvis_rot=R.ry(-52), chest_rot=R.ry(-68), head_rot=R.ry(4) @ R.rx(-2),
        wp=V((0.55, -0.42, -0.95)), wr=R.aim(d(-0.01, 0.0, -1)),
        Left_foot=foot(-0.14, -2.1, -25, lift=0.3, pitch=10), Right_foot=foot(0.45, 0.72, -60))
    clip.pose(0.185, drive, lead)
    # the reach: hips square, the back leg straightening, the shaft level and the whole body behind it
    reach = edit(coil,
        pelvis_pos=V((-0.05, -0.56, -1.3)), pelvis_rot=R.ry(-48), chest_rot=R.ry(-64) @ R.rx(-4), head_rot=R.rx(-5),
        wp=V((0.05, -0.3, -1.85)), wr=R.aim(d(-0.012, 0.0, -1)),
        Left_foot=foot(-0.16, -2.85, -18), Right_foot=foot(0.42, 0.2, -68),
        Right_knee=V(knee_f), Left_knee=V((0.05, 0.3, -0.5)))
    clip.pose(0.215, reach, lead)
    # it hangs there: the body sinks into the blow, the shaft still humming from the stop
    hold1 = edit(reach, pelvis_pos=reach["pelvis_pos"] + V((0, -0.05, -0.06)), wp=reach["wp"] + V((0, -0.03, -0.07)), wr=R.aim(d(-0.012, 0.022, -1)))
    clip.pose(0.245, hold1)
    clip.pose(0.275, edit(hold1, wr=R.aim(d(-0.012, -0.014, -1))))
    clip.pose(0.305, edit(hold1, wr=R.aim(d(-0.012, 0.009, -1))))
    hold2 = edit(hold1, wr=R.aim(d(-0.012, 0.0, -1)), pelvis_pos=reach["pelvis_pos"] + V((0, -0.03, -0.03)))
    clip.pose(0.40, hold2)
    # the pull back: the shaft first, then the body, the feet stepping home one after the other
    back = edit(hold2,
        pelvis_pos=V((0.0, -0.8, -0.55)), pelvis_rot=R.ry(-52), chest_rot=R.ry(-60), head_rot=R.ry(10) @ R.rx(-3),
        wp=V((0.6, -0.3, -0.9)), wr=R.aim(d(0.1, -0.12, -1)),
        Left_foot=foot(-0.18, -2.1, -22), Right_foot=foot(0.5, 0.9, -72, lift=0.22, pitch=-12))
    clip.pose(0.52, back)
    clip.pose(0.66, edit(low, Left_foot=foot(-0.2, -1.75, -22, lift=0.12), Right_knee=V(knee_f), Left_knee=V((0.05, 0.3, -0.5))))
    clip.pose(0.85, edit(low, Right_knee=V(knee_f), Left_knee=V((0.05, 0.3, -0.5))))
    return clip, 0.85, R.rel_between(guard["left_rel"], low["left_rel"], 0.5, 0.68), {"Hit": 0.2, "Swing": (0.16, 0.235)}


def spun(base, delta, pivot=V((0, -0.3, 0))):
    """The weapon carried round the body by `delta` degrees, positive to the striker's left."""
    r = R.ry(delta)
    return pivot + r @ (base - pivot)


def spear_slash():
    guard = S.capture(S.SPEAR_READY, "Spear")
    low = S.capture(S.SPEAR_LOW, "Spear")
    clip = Clip("Spear")
    lead = {"pelvis": 0.014, "chest": 0.006}
    knees = dict(Right_knee=V((0.2, 0.3, 0.15)), Left_knee=V((0.1, 0.3, -0.3)))

    def at(delta, drop=-0.7, tilt=0.0, grip_up=0.1, lean=0.0, chest_extra=0.0, rf=(0.49, 1.33, -70), lf=(-0.09, -1.34, -30), push=0.0):
        """delta: where the shaft points, degrees round from straight ahead (+ to the left). The body
        turns with it: guard yaw -62 is delta 0."""
        yaw = -62 + delta
        return edit(guard, **knees, **{
            "pelvis_pos": V((0.0, drop, push)),
            "pelvis_rot": R.ry(yaw),
            "chest_rot": R.ry(yaw - 8 + chest_extra) @ R.rz(lean),
            "head_rot": R.ry(delta * 0.75) @ R.rx(-3),
            "wp": spun(guard["wp"], delta) + V((0, grip_up, push)),
            "wr": R.ry(delta) @ R.rx(tilt) @ guard["wr"],
            "Right_foot": foot(rf[0], rf[1], rf[2]),
            "Left_foot": foot(lf[0], lf[1], lf[2]),
        })

    clip.pose(0.0, edit(low, **knees))
    # wound up to the right: the tip behind the right shoulder's line, low
    clip.pose(0.13, at(-108, drop=-0.82, tilt=-5, grip_up=-0.05, chest_extra=-14, rf=(0.62, 1.2, -95), lf=(-0.09, -1.34, -55)), lead)
    clip.pose(0.165, at(-100, drop=-0.84, tilt=-5, grip_up=-0.06, chest_extra=-16, rf=(0.62, 1.2, -95), lf=(-0.09, -1.34, -55)), lead)
    # one sweep, right to left, nearly level, gathering speed
    clip.pose(0.205, at(-55, drop=-0.74, tilt=-1, grip_up=0.08, chest_extra=-6, rf=(0.6, 1.15, -80), lf=(-0.1, -1.4, -40)), lead)
    clip.pose(0.24, at(0, drop=-0.66, tilt=2, grip_up=0.14, chest_extra=-5, rf=(0.56, 1.05, -55), lf=(-0.14, -1.45, -20), push=-0.25), lead)
    clip.pose(0.275, at(55, drop=-0.68, tilt=3, grip_up=0.14, chest_extra=-4, lean=2, rf=(0.45, 0.8, -30), lf=(-0.2, -1.3, 0), push=-0.3), lead)
    clip.pose(0.33, at(100, drop=-0.76, tilt=4, grip_up=0.1, chest_extra=-2, lean=3, rf=(0.3, 0.55, -5), lf=(-0.28, -1.05, 15), push=-0.25), lead)
    # the weight of the shaft carries on, then the body catches it
    clip.pose(0.44, at(116, drop=-0.8, tilt=2, grip_up=0.05, chest_extra=-3, lean=2, rf=(0.3, 0.55, -5), lf=(-0.28, -1.05, 15), push=-0.15))
    clip.pose(0.62, at(50, drop=-0.72, tilt=-1, grip_up=0.0, rf=(0.42, 1.0, -45), lf=(-0.15, -1.5, -15)))
    clip.pose(0.85, edit(guard, **knees))
    return clip, 0.85, R.rel_between(low["left_rel"], guard["left_rel"], 0.0, 0.12), {"Hit": 0.235, "Swing": (0.175, 0.34)}


# ---------- the sword ----------
FEET_READY = dict(Right_foot=foot(0.62, -0.6, -8), Left_foot=foot(-0.62, 0.5, 15))
SWORD_KNEES = dict(Right_knee=V((0.1, 0.2, -0.5)), Left_knee=V((-0.1, 0.2, -0.5)))
SWORD_POLES = dict(Right_pole=V((0.7, -0.5, 0.2)), Left_pole=V((-0.7, -0.5, 0.2)))


def sword_ready_pose():
    c = S.capture(S.sword_ready(), "Sword")
    return edit(c, **FEET_READY, **SWORD_KNEES)


def sword_key(ready, grip, point, up, pelvis_y=0, pelvis_z=0, yaw=0, chest=0, lean=0, pitch=0, head=None, lhand=None, rf=None, lf=None, pole=None):
    p = edit(ready,
        pelvis_pos=V((0, -0.15 + pelvis_y, pelvis_z)),
        pelvis_rot=R.ry(yaw),
        chest_rot=R.ry(chest) @ R.rx(pitch) @ R.rz(lean),
        head_rot=R.ry(head if head is not None else chest * 0.35) @ R.rx(pitch * 0.5),
        wp=V(grip), wr=R.aim(point, up))
    if lhand:
        p["lhand"] = (V(lhand), R.ry(chest) @ R.rx(-30))
    if rf:
        p["Right_foot"] = foot(*rf)
    if lf:
        p["Left_foot"] = foot(*lf)
    if pole:
        p["Right_pole"] = V(pole)
    return p


def sword_a():
    """A diagonal cut, high on the right down across the body to low on the left."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.025, "chest": 0.012}
    clip.pose(0.0, ready)
    clip.pose(0.1, sword_key(ready, (1.5, 1.05, 0.05), d(0.45, 0.72, 0.52), (0.4, 0.5, -0.7), pelvis_y=-0.12, pelvis_z=0.15, yaw=-22, chest=-40, head=-8,
        lhand=(-1.2, -0.05, -0.75), rf=(0.62, -0.5, -18), lf=(-0.62, 0.6, 5), pole=(0.9, 0.4, 0.4)), lead)
    clip.pose(0.135, sword_key(ready, (1.42, 1.02, -0.32), d(0.72, 0.68, -0.05), (0.4, 0.5, -0.7), pelvis_y=-0.17, pelvis_z=0.05, yaw=-14, chest=-28, head=-6,
        lhand=(-1.25, -0.2, -0.5), rf=(0.62, -0.5, -18), lf=(-0.62, 0.6, 5), pole=(0.9, 0.3, 0.3)), lead)
    clip.pose(0.17, sword_key(ready, (0.72, 0.42, -1.5), d(0.42, 0.42, -0.8), (0.4, 0.7, 0.55), pelvis_y=-0.3, pelvis_z=-0.3, yaw=4, chest=-4, head=0, pitch=-5,
        lhand=(-1.35, -0.45, 0.0), rf=(0.62, -1.05, -8, 0.16), lf=(-0.62, 0.45, 10), pole=(0.8, -0.3, 0.3)), lead)
    clip.pose(0.205, sword_key(ready, (-0.25, -0.3, -1.65), d(-0.62, -0.42, -0.66), (0.45, 0.65, -0.6), pelvis_y=-0.42, pelvis_z=-0.55, yaw=20, chest=26, head=8, pitch=-8,
        lhand=(-1.45, -0.6, 0.55), rf=(0.62, -1.35, -2), lf=(-0.62, 0.35, 15), pole=(0.5, -0.8, 0.2)), lead)
    clip.pose(0.27, sword_key(ready, (-0.95, -0.72, -0.9), d(-0.9, -0.42, 0.08), (0.2, 0.75, -0.6), pelvis_y=-0.46, pelvis_z=-0.55, yaw=28, chest=44, head=10, pitch=-9,
        lhand=(-1.5, -0.55, 0.8), rf=(0.62, -1.35, -2), lf=(-0.62, 0.35, 15), pole=(0.5, -0.8, 0.3)))
    clip.pose(0.36, sword_key(ready, (-0.85, -0.6, -0.95), d(-0.85, -0.3, 0.15), (0.2, 0.75, -0.6), pelvis_y=-0.38, pelvis_z=-0.42, yaw=24, chest=36, head=8, pitch=-6,
        lhand=(-1.5, -0.55, 0.7), rf=(0.62, -1.2, -4), lf=(-0.62, 0.42, 15), pole=(0.5, -0.8, 0.3)))
    clip.pose(0.56, ready)
    return clip, 0.56, None, {"Hit": 0.19, "Swing": (0.14, 0.27)}


def sword_b():
    """The backhand: low on the left, rising across the body to high on the right."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.025, "chest": 0.012}
    start = sword_key(ready, (-0.85, -0.6, -0.95), d(-0.85, -0.3, 0.15), (0.2, 0.75, -0.6), pelvis_y=-0.38, pelvis_z=-0.42, yaw=24, chest=36, head=8, pitch=-6,
        lhand=(-1.5, -0.55, 0.7), rf=(0.62, -1.2, -4), lf=(-0.62, 0.42, 15), pole=(0.5, -0.8, 0.3))
    clip.pose(0.0, start)
    clip.pose(0.09, sword_key(ready, (-0.95, -0.55, -0.45), d(-0.8, -0.32, 0.5), (0.2, 0.8, -0.5), pelvis_y=-0.44, pelvis_z=-0.25, yaw=36, chest=56, head=14, pitch=-4,
        lhand=(-1.4, -0.3, 0.75), rf=(0.62, -0.9, -2), lf=(-0.62, 0.55, 22), pole=(0.3, -0.7, 0.6)), lead)
    clip.pose(0.125, sword_key(ready, (-0.75, -0.52, -0.9), d(-0.86, -0.36, -0.18), (0.2, 0.8, -0.5), pelvis_y=-0.46, pelvis_z=-0.25, yaw=30, chest=46, head=12, pitch=-4,
        lhand=(-1.4, -0.3, 0.6), rf=(0.62, -0.9, -2), lf=(-0.62, 0.55, 22), pole=(0.3, -0.7, 0.6)), lead)
    clip.pose(0.16, sword_key(ready, (0.1, -0.2, -1.65), d(0.05, -0.05, -1), (-0.3, 0.75, 0.25), pelvis_y=-0.34, pelvis_z=-0.5, yaw=6, chest=8, head=2, pitch=-3,
        lhand=(-1.45, -0.5, 0.2), rf=(0.62, -1.2, -5), lf=(-0.62, 0.45, 12), pole=(0.7, -0.5, 0.2)), lead)
    clip.pose(0.195, sword_key(ready, (0.95, 0.55, -1.25), d(0.72, 0.5, -0.48), (-0.5, 0.75, -0.1), pelvis_y=-0.2, pelvis_z=-0.55, yaw=-18, chest=-28, head=-6,
        lhand=(-1.35, -0.55, 0.6), rf=(0.62, -1.3, -12), lf=(-0.62, 0.35, 5), pole=(0.9, 0.0, 0.1)), lead)
    clip.pose(0.26, sword_key(ready, (1.5, 1.05, -0.55), d(0.85, 0.5, 0.15), (-0.5, 0.8, 0.0), pelvis_y=-0.08, pelvis_z=-0.5, yaw=-30, chest=-46, head=-10, pitch=3,
        lhand=(-1.2, -0.5, 0.8), rf=(0.62, -1.3, -16), lf=(-0.62, 0.35, 0), pole=(0.95, 0.3, 0.15)))
    clip.pose(0.35, sword_key(ready, (1.42, 0.95, -0.65), d(0.78, 0.55, 0.05), (-0.5, 0.8, 0.0), pelvis_y=-0.12, pelvis_z=-0.42, yaw=-26, chest=-38, head=-8, pitch=2,
        lhand=(-1.25, -0.5, 0.7), rf=(0.62, -1.15, -14), lf=(-0.62, 0.4, 3), pole=(0.95, 0.3, 0.15)))
    clip.pose(0.56, ready)
    return clip, 0.56, None, {"Hit": 0.178, "Swing": (0.13, 0.26)}


def sword_c():
    """The finisher: rising onto the toes, the blade high behind the head, then everything down on one line."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.02, "chest": 0.01}
    start = sword_key(ready, (1.42, 0.95, -0.65), d(0.78, 0.55, 0.05), (-0.5, 0.8, 0.0), pelvis_y=-0.12, pelvis_z=-0.42, yaw=-26, chest=-38, head=-8, pitch=2,
        lhand=(-1.25, -0.5, 0.7), rf=(0.62, -1.15, -14), lf=(-0.62, 0.4, 3), pole=(0.95, 0.3, 0.15))
    clip.pose(0.0, start)
    clip.pose(0.13, sword_key(ready, (0.55, 1.75, 0.2), d(0.1, 0.55, 0.83), (0, 0.8, -0.6), pelvis_y=0.3, pelvis_z=0.15, yaw=-12, chest=-14, head=-2, pitch=10,
        lhand=(-0.8, 0.55, -0.65), rf=(0.62, -0.7, -8, 0.12), lf=(-0.62, 0.8, 8), pole=(1.0, 0.6, 0.0)), lead)
    clip.pose(0.175, sword_key(ready, (0.5, 1.88, -0.05), d(0.08, 0.92, 0.38), (0, 0.4, -0.9), pelvis_y=0.34, pelvis_z=0.12, yaw=-10, chest=-12, head=-2, pitch=12,
        lhand=(-0.75, 0.6, -0.75), rf=(0.62, -0.7, -8, 0.18), lf=(-0.62, 0.8, 8), pole=(1.0, 0.6, 0.0)), lead)
    clip.pose(0.215, sword_key(ready, (0.42, 1.2, -1.3), d(0.02, 0.66, -0.75), (0, 0.75, 0.66), pelvis_y=-0.08, pelvis_z=-0.5, yaw=-4, chest=-4, head=0, pitch=0,
        lhand=(-1.1, -0.05, -0.2), rf=(0.62, -1.4, -5, 0.22), lf=(-0.62, 0.6, 8), pole=(0.9, 0.1, 0.1)), lead)
    clip.pose(0.25, sword_key(ready, (0.2, -0.45, -1.72), d(-0.02, -0.5, -0.86), (0, 0.86, -0.5), pelvis_y=-0.72, pelvis_z=-0.95, yaw=2, chest=2, head=0, pitch=-14,
        lhand=(-1.3, -0.6, 0.55), rf=(0.62, -1.9, -2), lf=(-0.62, 0.35, 10), pole=(0.8, -0.5, 0.2)), lead)
    clip.pose(0.33, sword_key(ready, (0.15, -0.72, -1.6), d(-0.03, -0.62, -0.78), (0, 0.78, -0.62), pelvis_y=-0.82, pelvis_z=-1.0, yaw=3, chest=3, head=0, pitch=-17,
        lhand=(-1.35, -0.75, 0.6), rf=(0.62, -1.9, -2), lf=(-0.62, 0.35, 10), pole=(0.8, -0.5, 0.2)))
    clip.pose(0.44, sword_key(ready, (0.2, -0.65, -1.55), d(-0.03, -0.55, -0.83), (0, 0.8, -0.55), pelvis_y=-0.72, pelvis_z=-0.9, yaw=3, chest=3, head=0, pitch=-13,
        lhand=(-1.35, -0.7, 0.55), rf=(0.62, -1.75, -2), lf=(-0.62, 0.42, 10), pole=(0.8, -0.5, 0.2)))
    clip.pose(0.62, ready)
    return clip, 0.62, None, {"Hit": 0.235, "Swing": (0.18, 0.28)}


# ---------- bare hands ----------
def shoulder_of(side, pelvis_pos, pelvis_rot, chest_rot):
    pivot = V(R.JOINTS["Root"][2]) + pelvis_pos
    lower = pivot - pelvis_rot @ V(R.JOINTS["Root"][3])
    waist = lower + pelvis_rot @ V(R.JOINTS["Waist"][2])
    upper = waist - chest_rot @ V(R.JOINTS["Waist"][3])
    return upper + chest_rot @ V(R.JOINTS[side + "Shoulder"][2])


def punch(side):
    """A straight punch, for a player with no weapon: one hand, then the other on the next strike. The hips turn first,
    the shoulder follows, and the fist arrives last, then snaps back to the guard. side: 1 the right hand, -1 the left."""
    clip = Clip("Sword")
    lead = {"pelvis": 0.014, "chest": 0.007}
    # feet: the opposite foot ahead of the punching hand
    front, back = foot(-0.42 * side, -0.62, -14 * side), foot(0.46 * side, 0.55, 28 * side)
    ahead = foot(-0.42 * side, -0.95, -14 * side)

    def pose(pelvis_pos, pelvis_yaw, chest_yaw, pitch, hit_hand, other_hand, step=False):
        pelvis_pos = V(pelvis_pos)
        pelvis_rot = R.ry(pelvis_yaw * side) @ R.rx(pitch * 0.5)
        chest_rot = R.ry(chest_yaw * side) @ R.rx(pitch)
        head_rot = R.ry(chest_yaw * side * 0.15) @ R.rx(-3)
        hit_name = "Right" if side == 1 else "Left"
        other_name = "Left" if side == 1 else "Right"

        def hand(name, spot):
            sign = 1 if name == "Right" else -1
            centre = V((spot[0] * sign, spot[1], spot[2]))
            direction = centre - shoulder_of(name, pelvis_pos, pelvis_rot, chest_rot)
            return centre, R.point_limb(direction)

        hands = {hit_name: hand(hit_name, hit_hand), other_name: hand(other_name, other_hand)}
        wr = hands["Right"][1] @ R.WEAPON_IN_HAND["Sword"]
        feet_left, feet_right = (front if side == 1 else back), (back if side == 1 else front)
        if step:
            feet_left, feet_right = (ahead if side == 1 else back), (back if side == 1 else ahead)
        return {
            "pelvis_pos": pelvis_pos, "pelvis_rot": pelvis_rot, "chest_rot": chest_rot, "head_rot": head_rot,
            "wp": hands["Right"][0] + hands["Right"][1] @ R.GRIP_IN_HAND, "wr": wr, "lhand": hands["Left"],
            "Right_pole": V((0.8, -0.6, 0.25)), "Left_pole": V((-0.8, -0.6, 0.25)),
            "Right_knee": V((0.1, 0.2, -1)), "Left_knee": V((-0.1, 0.2, -1)),
            "Right_foot": feet_right, "Left_foot": feet_left,
        }

    guard = pose((0, -0.38, 0), 0, 0, -6, (0.5, 0.42, -0.78), (0.5, 0.45, -0.72))
    clip.pose(0.0, guard)
    clip.pose(0.055, pose((0, -0.44, 0.1), -14, -24, -6, (0.74, 0.28, -0.22), (0.45, 0.46, -0.85)), lead)
    clip.pose(0.11, pose((0, -0.5, -0.38), 20, 38, -10, (0.16, 0.5, -2.62), (0.68, 0.25, -0.12), step=True), lead)
    clip.pose(0.165, pose((0, -0.52, -0.42), 22, 40, -11, (0.14, 0.48, -2.68), (0.68, 0.24, -0.1), step=True))
    clip.pose(0.25, pose((0, -0.46, -0.2), 8, 14, -8, (0.42, 0.45, -1.5), (0.56, 0.36, -0.5), step=True))
    clip.pose(0.4, guard)
    return clip, 0.4, None, {"Hit": 0.1}


def punch_right():
    return punch(1)


def punch_left():
    return punch(-1)


CLIPS = {"PunchRight": punch_right, "PunchLeft": punch_left, "SpearThrust": spear_thrust, "SpearSlash": spear_slash, "SwordA": sword_a, "SwordB": sword_b, "SwordC": sword_c}


UNARMED = ("PunchRight", "PunchLeft")


def fit_crescent(frames, swing):
    """The arc the tip really drew, in the root's space: the plane, the circle in it and the middle."""
    a, b = int(swing[0] * R.FPS), int(swing[1] * R.FPS)
    pts = np.array([list(f["tip"]) for f in frames[a:b + 1]])
    mean = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - mean)
    u, v, n = vt[0], vt[1], vt[2]
    xy = np.c_[(pts - mean) @ u, (pts - mean) @ v]
    A = np.c_[2 * xy, np.ones(len(xy))]
    sol = np.linalg.lstsq(A, (xy ** 2).sum(axis=1), rcond=None)[0]
    centre2 = sol[:2]
    radius = math.sqrt(max(1e-4, sol[2] + centre2 @ centre2))
    centre = mean + u * centre2[0] + v * centre2[1]
    mid = pts[len(pts) // 2]
    bulge = (mid - centre) / np.linalg.norm(mid - centre)
    # the sweep's own direction, so the normal is the same way round for every clip
    if np.cross(pts[0] - centre, pts[-1] - centre) @ n < 0:
        n = -n
    return {"Centre": centre, "Radius": radius, "Face": n, "Bulge": bulge}


def run(name, review=True, out=None, cam_from=(9, 3.5, -11), cam_to=(0, -0.6, -2.2), times=None):
    R.clear()
    spec = CLIPS[name]
    kind = "Spear" if name.startswith("Spear") else "Sword"
    R.EXACT_ARMS = name in UNARMED
    clip, length, left_rel, extra = spec()
    tip = SPEAR_TIP if kind == "Spear" else SWORD_TIP
    bake_frames, worst = R.bake(clip.c, kind, length, tip, left_rel)
    if "Cycle" in extra:     # a looping clip: only its middle cycle
        a, b = int(round(extra["Cycle"][0] * R.FPS)), int(round(extra["Cycle"][1] * R.FPS))
        bake_frames = bake_frames[a:b + 1]
        length = (b - a) / R.FPS
    result = {"frames": bake_frames, "extra": extra, "length": length, "worst": worst, "kind": kind,
        "crescent": fit_crescent(bake_frames, extra["Swing"]) if "Swing" in extra else None}
    if review:
        path = out or os.path.join(tempfile.gettempdir(), "weapon_moves", name + ".png")      # a review sheet: never in assets/
        contact_sheet(result, kind, path, cam_from, cam_to, times)
        result["path"] = path
    return result


def contact_sheet(result, kind, path, cam_from, cam_to, times=None, size=340):
    """A row of poses, with the tip's whole path drawn as a ribbon of small boxes."""
    frames = result["frames"]
    proxy = R.build_proxy(kind, SPEAR_TIP if kind == "Spear" else SWORD_TIP, SPEAR_BUTT if kind == "Spear" else SWORD_BUTT)
    if R.EXACT_ARMS:     # the unarmed clips: no weapon to review
        proxy["Weapon"].hide_render = True
    cam = R.setup_review(size)
    R.look_from(cam, cam_from, cam_to)
    scene = bpy.context.scene
    mat = R.proxy_material("Path", (1.0, 0.15, 0.1))
    for i, f in enumerate(frames):
        if i % 2 == 0 and not R.EXACT_ARMS:
            b = R.box_object("Tip%d" % i, (0.12, 0.12, 0.12), mat)
            b.location = R.C @ f["tip"]
    length = result["length"]
    times = times or [round(length * k / 11, 3) for k in range(12)]
    tiles = []
    tmp = path + ".tile.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for t in times:
        f = frames[min(len(frames) - 1, int(round(t * R.FPS)))]
        # the weapon's frame
        g = f["grip"]
        wr = None
        offset = result["extra"]["Cycle"][0] if "Cycle" in result["extra"] else 0
        scene.frame_set(int(round((t + offset) * R.FPS)) * (R.SCENE_FPS // R.FPS) + 1)
        _, wr = R.read(bpy.data.objects["Weapon"])
        R.pose_proxy(proxy, f["rot"], f["pos"], g, wr)
        bpy.context.view_layer.update()
        scene.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(tmp, check_existing=False)
        px = np.zeros(size * size * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        tiles.append(px.reshape(size, size, 4))
        bpy.data.images.remove(im)
    rows = [np.concatenate(tiles[i:i + 6], axis=1) for i in range(0, len(tiles), 6)]
    sheet = np.concatenate(rows[::-1], axis=0)
    h, w = sheet.shape[:2]
    out = bpy.data.images.new("Sheet", w, h)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    if os.path.exists(tmp):
        os.remove(tmp)


def report(name, res):
    c = res["crescent"]
    if not c:
        return "%s %.2fs worst %s" % (name, res["length"], {k: round(v, 2) for k, v in res["worst"].items()})
    return "%s %.2fs worst %s crescent centre %s r %.2f face %s bulge %s" % (
        name, res["length"], {k: round(v, 2) for k, v in res["worst"].items()},
        [round(float(x), 2) for x in c["Centre"]], c["Radius"], [round(float(x), 2) for x in c["Face"]], [round(float(x), 2) for x in c["Bulge"]])


def export_all(path=None):
    path = path or REPO + "/src/client/Character/WeaponClips.lua"
    out = {}
    lines = []
    for name in CLIPS:
        res = run(name, review=False)
        c = res["crescent"]
        if not c:
            out[name] = {"frames": res["frames"], "extra": {"Hit": "%.3f" % res["extra"]["Hit"]} if "Hit" in res["extra"] else {}}
            lines.append(report(name, res))
            R.clear()
            continue
        extra = dict(Hit="%.3f" % res["extra"]["Hit"], SwingStart="%.3f" % res["extra"]["Swing"][0], SwingEnd="%.3f" % res["extra"]["Swing"][1],
            Crescent="{ Centre = Vector3.new(%.2f, %.2f, %.2f), Radius = %.2f, Face = Vector3.new(%.3f, %.3f, %.3f), Bulge = Vector3.new(%.3f, %.3f, %.3f) }" % (
                *[float(x) for x in c["Centre"]], float(c["Radius"]), *[float(x) for x in c["Face"]], *[float(x) for x in c["Bulge"]]))
        out[name] = {"frames": res["frames"], "extra": extra}
        lines.append(report(name, res))
        R.clear()
    R.to_lua(out, path)
    return lines

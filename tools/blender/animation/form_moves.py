"""The combat forms' own strikes (2026-11-24, shared/FormRules): keyed on the same R15 rig and with the same helpers as weapon_moves.py, which keeps the
original seven clips (Crescent's SwordA, SwordB, SwordC are the sword's balanced form; the spear thrust and slash are Lancer's; the punches are Fist's).

    import form_moves as F      # (after weapon_moves: this registers its clips there)
    M.run("GaleSwift")          # one clip and its contact sheet
    M.export_all()              # every clip, old and new, to src/client/Character/WeaponClips.lua

The rules of the set (each clip is played retimed to its strike's cooldown, FormRules x the weapon's cooldown, never past 0.75x to 1.8x, so a clip is
keyed near its real length):
  * a chain's strikes are keyed to follow each other: a strike starts where the one before it ended, and only a chain's last strike returns to the ready
    pose (the game blends a clip into the next, and back to the ready pose when the chain stops);
  * "Hit" is the frame the blade connects; "Swing" the span the light is drawn over (its crescent is fitted to the tip's real path there);
  * a body turn is absolute (yaw of the pelvis, of the chest), and the weapon is placed in the root's space, so a spin turns the weapon's place by the
    same angle (ring()).
"""
import weapon_moves as M

R, S, V, d, edit, foot = M.R, M.S, M.V, M.d, M.edit, M.foot
sword_key, sword_ready_pose, Clip = M.sword_key, M.sword_ready_pose, M.Clip

LEAD = {"pelvis": 0.02, "chest": 0.01}


def ring(ready, a, h=0.45, reach=1.0, yaw_share=0.8, pelvis_y=0.0, pelvis_z=0.0, pitch=0, lift=0.0, lean=0, feet=True, base=(0.85, 0.05, -0.55), up=(0, 1, 0)):
    """The blade held level, turned `a` degrees to the left of its place at the start: right of centre and a little ahead, pointing outward.
    The body turns the same way (the chest all the way, the pelvis `yaw_share` of it), the feet pivoting a little behind."""
    rot = R.ry(a)
    grip = rot @ V((base[0] * reach * 0.9, h, base[2] * reach * 1.6))
    point = rot @ d(*base)
    kw = {}
    if feet:
        kw = dict(rf=(0.62, -0.6, -8 + a * 0.55, lift), lf=(-0.62, 0.5, 15 + a * 0.55, lift))
    return sword_key(ready, tuple(grip), point, up, pelvis_y=pelvis_y, pelvis_z=pelvis_z, yaw=a * yaw_share - 20, chest=a - 35, head=a - 30, pitch=pitch, lean=lean,
        lhand=tuple(rot @ V((-0.5, h - 0.05, -0.75))), **kw)


# ---------- Gale: fast and flowing ----------
def gale_swift():
    """A quick level cut from the right across to the left."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    clip.pose(0.0, ready)
    clip.pose(0.07, sword_key(ready, (1.3, 0.5, -0.1), d(0.85, 0.1, -0.5), (0, 1, 0), pelvis_y=-0.2, pelvis_z=0.1, yaw=-20, chest=-38, head=-10,
        lhand=(-1.0, 0.1, -0.7), rf=(0.62, -0.5, -16), lf=(-0.62, 0.55, 8), pole=(0.9, 0.2, 0.3)), LEAD)
    clip.pose(0.115, sword_key(ready, (0.3, 0.45, -1.6), d(0.15, 0.05, -1), (0, 1, 0), pelvis_y=-0.3, pelvis_z=-0.45, yaw=2, chest=0, head=0, pitch=-4,
        lhand=(-1.2, 0.0, -0.3), rf=(0.62, -1.1, -4, 0.1), lf=(-0.62, 0.45, 12), pole=(0.8, -0.2, 0.2)), LEAD)
    clip.pose(0.165, sword_key(ready, (-1.0, 0.3, -1.25), d(-0.85, 0.0, -0.5), (0, 1, 0), pelvis_y=-0.34, pelvis_z=-0.5, yaw=22, chest=42, head=10, pitch=-5,
        lhand=(-1.35, -0.1, 0.2), rf=(0.62, -1.2, 0), lf=(-0.62, 0.4, 18), pole=(0.6, -0.5, 0.3)), LEAD)
    clip.pose(0.25, sword_key(ready, (-1.05, 0.25, -1.05), d(-0.88, -0.05, -0.4), (0, 1, 0), pelvis_y=-0.3, pelvis_z=-0.45, yaw=20, chest=38, head=9, pitch=-4,
        lhand=(-1.4, -0.1, 0.3), rf=(0.62, -1.15, 0), lf=(-0.62, 0.42, 18), pole=(0.6, -0.5, 0.3)))
    clip.pose(0.34, sword_key(ready, (-1.0, 0.25, -1.0), d(-0.88, -0.05, -0.4), (0, 1, 0), pelvis_y=-0.28, pelvis_z=-0.42, yaw=18, chest=34, head=8,
        lhand=(-1.4, -0.1, 0.3), rf=(0.62, -1.1, 0), lf=(-0.62, 0.42, 18), pole=(0.6, -0.5, 0.3)))
    return clip, 0.34, None, {"Hit": 0.115, "Swing": (0.07, 0.2)}


def gale_cross():
    """The return: from the left back across to the right, rising a little."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    start = sword_key(ready, (-1.0, 0.25, -1.0), d(-0.88, -0.05, -0.4), (0, 1, 0), pelvis_y=-0.28, pelvis_z=-0.42, yaw=18, chest=34, head=8,
        lhand=(-1.4, -0.1, 0.3), rf=(0.62, -1.1, 0), lf=(-0.62, 0.42, 18), pole=(0.6, -0.5, 0.3))
    clip.pose(0.0, start)
    clip.pose(0.06, sword_key(ready, (-1.1, 0.3, -0.7), d(-0.9, 0.0, 0.1), (0, 1, 0), pelvis_y=-0.3, pelvis_z=-0.3, yaw=28, chest=50, head=14,
        lhand=(-1.45, -0.1, 0.5), rf=(0.62, -0.9, 0), lf=(-0.62, 0.5, 22), pole=(0.5, -0.5, 0.4)), LEAD)
    clip.pose(0.11, sword_key(ready, (0.1, 0.55, -1.65), d(0.05, 0.12, -1), (0, 1, 0), pelvis_y=-0.3, pelvis_z=-0.5, yaw=2, chest=2, head=0, pitch=-3,
        lhand=(-1.25, 0.0, 0.0), rf=(0.62, -1.2, -4), lf=(-0.62, 0.45, 12), pole=(0.8, -0.2, 0.2)), LEAD)
    clip.pose(0.16, sword_key(ready, (1.35, 0.85, -1.05), d(0.88, 0.2, -0.4), (0, 1, 0), pelvis_y=-0.2, pelvis_z=-0.5, yaw=-24, chest=-44, head=-10, pitch=-2,
        lhand=(-1.2, 0.1, 0.4), rf=(0.62, -1.25, -14), lf=(-0.62, 0.35, 4), pole=(0.95, 0.2, 0.2)), LEAD)
    clip.pose(0.24, sword_key(ready, (1.4, 0.9, -0.85), d(0.9, 0.2, -0.3), (0, 1, 0), pelvis_y=-0.2, pelvis_z=-0.45, yaw=-26, chest=-46, head=-10,
        lhand=(-1.2, 0.1, 0.5), rf=(0.62, -1.2, -15), lf=(-0.62, 0.35, 3), pole=(0.95, 0.2, 0.2)))
    clip.pose(0.34, sword_key(ready, (1.35, 0.8, -0.8), d(0.88, 0.15, -0.3), (0, 1, 0), pelvis_y=-0.18, pelvis_z=-0.4, yaw=-24, chest=-42, head=-9,
        lhand=(-1.2, 0.1, 0.5), rf=(0.62, -1.15, -14), lf=(-0.62, 0.38, 4), pole=(0.95, 0.2, 0.2)))
    return clip, 0.34, None, {"Hit": 0.11, "Swing": (0.06, 0.19)}


def gale_spin():
    """A full turn on the spot with the blade held level: the cut comes round the body."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    r = lambda a, **kw: ring(ready, a, **kw)
    clip.pose(0.0, sword_key(ready, (1.35, 0.8, -0.8), d(0.88, 0.15, -0.3), (0, 1, 0), pelvis_y=-0.18, pelvis_z=-0.4, yaw=-24, chest=-42, head=-9,
        lhand=(-1.2, 0.1, 0.5), rf=(0.62, -1.15, -14), lf=(-0.62, 0.38, 4), pole=(0.95, 0.2, 0.2)))
    clip.pose(0.05, r(-25, pelvis_y=-0.3, lean=4), LEAD)
    clip.pose(0.10, r(45, pelvis_y=-0.32), LEAD)
    clip.pose(0.14, r(125, pelvis_y=-0.3), LEAD)
    clip.pose(0.18, r(205, pelvis_y=-0.28), LEAD)
    clip.pose(0.22, r(285, pelvis_y=-0.3), LEAD)
    clip.pose(0.265, r(345, pelvis_y=-0.34), LEAD)
    clip.pose(0.32, r(372, pelvis_y=-0.36, pelvis_z=-0.15))
    clip.pose(0.42, r(378, pelvis_y=-0.3, pelvis_z=-0.1))
    return clip, 0.42, None, {"Hit": 0.11, "Swing": (0.07, 0.29)}


def gale_rush():
    """A long step in under the guard and a rising diagonal cut, low right to high left."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    clip.pose(0.0, ring(ready, 378, pelvis_y=-0.3, pelvis_z=-0.1))
    clip.pose(0.07, sword_key(ready, (1.25, -0.2, 0.1), d(0.55, 0.0, 0.8), (0, 1, 0), pelvis_y=-0.5, pelvis_z=0.25, yaw=-26, chest=-44, head=-8, pitch=6,
        lhand=(-0.9, -0.1, -0.2), rf=(0.62, -0.2, -18), lf=(-0.62, 0.8, 4), pole=(0.95, 0.1, 0.1)), LEAD)
    clip.pose(0.115, sword_key(ready, (0.55, 0.1, -1.9), d(0.2, 0.18, -1), (0, 1, 0), pelvis_y=-0.55, pelvis_z=-1.0, yaw=-4, chest=-6, head=0, pitch=-6,
        lhand=(-1.2, -0.2, -0.3), rf=(0.62, -2.0, -6, 0.12), lf=(-0.62, 0.35, 10), pole=(0.8, -0.3, 0.2)), LEAD)
    clip.pose(0.16, sword_key(ready, (-0.55, 0.95, -1.7), d(-0.6, 0.45, -0.65), (0.3, 0.9, 0), pelvis_y=-0.62, pelvis_z=-1.1, yaw=16, chest=30, head=8, pitch=-8,
        lhand=(-1.35, 0.1, 0.1), rf=(0.62, -2.05, 0), lf=(-0.62, 0.3, 14), pole=(0.6, -0.5, 0.2)), LEAD)
    clip.pose(0.24, sword_key(ready, (-0.75, 1.0, -1.45), d(-0.7, 0.45, -0.45), (0.3, 0.9, 0), pelvis_y=-0.6, pelvis_z=-1.05, yaw=18, chest=34, head=8, pitch=-7,
        lhand=(-1.4, 0.1, 0.2), rf=(0.62, -2.0, 0), lf=(-0.62, 0.32, 14), pole=(0.6, -0.5, 0.2)))
    clip.pose(0.34, sword_key(ready, (-0.75, 0.95, -1.4), d(-0.7, 0.4, -0.45), (0.3, 0.9, 0), pelvis_y=-0.55, pelvis_z=-0.98, yaw=16, chest=30, head=7,
        lhand=(-1.4, 0.1, 0.2), rf=(0.62, -1.95, 0), lf=(-0.62, 0.34, 14), pole=(0.6, -0.5, 0.2)))
    return clip, 0.34, None, {"Hit": 0.15, "Swing": (0.085, 0.22)}


def gale_storm():
    """The finisher: crouch, leap, and a spin in the air with the blade out level, landing low."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    clip.pose(0.0, sword_key(ready, (-0.75, 0.95, -1.4), d(-0.7, 0.4, -0.45), (0.3, 0.9, 0), pelvis_y=-0.55, pelvis_z=-0.98, yaw=16, chest=30, head=7,
        lhand=(-1.4, 0.1, 0.2), rf=(0.62, -1.95, 0), lf=(-0.62, 0.34, 14), pole=(0.6, -0.5, 0.2)))
    # down and gathered, the blade drawn in to the right hip
    clip.pose(0.09, edit(ring(ready, -35, h=0.1, reach=0.8, pelvis_y=-0.72, pitch=6, feet=False), Right_foot=foot(0.62, -0.5, -25), Left_foot=foot(-0.62, 0.5, 5)), LEAD)
    # up: off the ground, the blade swung out level
    clip.pose(0.17, edit(ring(ready, 10, h=0.6, reach=1.1, pelvis_y=0.35, feet=False), Right_foot=foot(0.62, -0.5, 0, 0.35), Left_foot=foot(-0.62, 0.5, 15, 0.3)), LEAD)
    for t, a, y in ((0.23, 110, 0.5), (0.29, 210, 0.55), (0.35, 310, 0.5), (0.41, 400, 0.3)):
        clip.pose(t, edit(ring(ready, a, h=0.6, reach=1.15, pelvis_y=y, feet=False), Right_foot=foot(0.62, -0.5, a * 0.5, 0.3), Left_foot=foot(-0.62, 0.5, a * 0.5 + 15, 0.25)), LEAD)
    # down hard: the blade low and out, the knees bent
    clip.pose(0.5, edit(ring(ready, 440, h=0.0, reach=1.15, pelvis_y=-0.78, pelvis_z=-0.2, pitch=-8, feet=False), Right_foot=foot(0.8, -0.9, 212), Left_foot=foot(-0.8, 0.8, 232)), LEAD)
    clip.pose(0.62, edit(ring(ready, 440, h=-0.05, reach=1.15, pelvis_y=-0.7, pelvis_z=-0.15, pitch=-6, feet=False), Right_foot=foot(0.75, -0.85, 212), Left_foot=foot(-0.75, 0.75, 232)))
    clip.pose(0.85, ready)
    return clip, 0.85, None, {"Hit": 0.23, "Swing": (0.15, 0.48)}


# ---------- Mountain: slow and heavy ----------
def heavy_key(ready, grip, point, up, **kw):
    kw.setdefault("lhand", (-0.9, 0.4, -0.6))
    return sword_key(ready, grip, point, up, **kw)


def mountain_cut():
    """A great diagonal cut: the blade drawn far back over the right shoulder, the whole body behind it."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.04, "chest": 0.02}
    clip.pose(0.0, ready)
    clip.pose(0.12, heavy_key(ready, (1.3, 0.95, 0.15), d(0.55, 0.78, 0.3), (0.4, 0.5, -0.7), pelvis_y=-0.3, pelvis_z=0.3, yaw=-30, chest=-56, head=-12, pitch=4,
        lhand=(-0.9, 0.55, -0.3), rf=(0.7, -0.3, -24), lf=(-0.62, 0.8, 8), pole=(0.95, 0.5, 0.3)), lead)
    clip.pose(0.2, heavy_key(ready, (1.35, 1.0, 0.2), d(0.55, 0.8, 0.25), (0.4, 0.5, -0.7), pelvis_y=-0.38, pelvis_z=0.35, yaw=-32, chest=-60, head=-12, pitch=5,
        lhand=(-0.9, 0.6, -0.2), rf=(0.7, -0.3, -26), lf=(-0.62, 0.8, 8), pole=(0.95, 0.5, 0.3)), lead)
    clip.pose(0.245, heavy_key(ready, (0.6, 0.5, -1.7), d(0.35, 0.3, -0.85), (0.4, 0.7, 0.5), pelvis_y=-0.62, pelvis_z=-0.7, yaw=6, chest=0, head=0, pitch=-6,
        lhand=(-1.3, 0.0, -0.1), rf=(0.7, -1.7, -6, 0.1), lf=(-0.62, 0.55, 12), pole=(0.8, -0.2, 0.2)), lead)
    clip.pose(0.285, heavy_key(ready, (-0.9, -0.6, -1.3), d(-0.85, -0.4, -0.3), (0.2, 0.75, -0.6), pelvis_y=-0.85, pelvis_z=-0.95, yaw=30, chest=52, head=10, pitch=-10,
        lhand=(-1.5, -0.55, 0.6), rf=(0.7, -1.95, -2), lf=(-0.62, 0.35, 20), pole=(0.5, -0.8, 0.3)), lead)
    clip.pose(0.40, heavy_key(ready, (-0.95, -0.7, -1.2), d(-0.85, -0.4, -0.2), (0.2, 0.75, -0.6), pelvis_y=-0.9, pelvis_z=-0.95, yaw=30, chest=52, head=10, pitch=-11,
        lhand=(-1.5, -0.6, 0.6), rf=(0.7, -1.95, -2), lf=(-0.62, 0.35, 20), pole=(0.5, -0.8, 0.3)))
    clip.pose(0.55, heavy_key(ready, (-0.95, -0.7, -1.2), d(-0.85, -0.4, -0.2), (0.2, 0.75, -0.6), pelvis_y=-0.86, pelvis_z=-0.92, yaw=28, chest=50, head=10, pitch=-10,
        lhand=(-1.5, -0.6, 0.6), rf=(0.7, -1.9, -2), lf=(-0.62, 0.35, 20), pole=(0.5, -0.8, 0.3)))
    return clip, 0.55, None, {"Hit": 0.27, "Swing": (0.2, 0.34)}


def mountain_chop():
    """The backswing and a straight chop down the middle: the blade lifted in front, then dropped through."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.04, "chest": 0.02}
    clip.pose(0.0, heavy_key(ready, (-0.95, -0.7, -1.2), d(-0.85, -0.4, -0.2), (0.2, 0.75, -0.6), pelvis_y=-0.86, pelvis_z=-0.92, yaw=28, chest=50, head=10, pitch=-10,
        lhand=(-1.5, -0.6, 0.6), rf=(0.7, -1.9, -2), lf=(-0.62, 0.35, 20), pole=(0.5, -0.8, 0.3)))
    # the blade swung up the left side and over, the body rising onto its toes
    clip.pose(0.1, heavy_key(ready, (-0.4, 0.95, -0.8), d(-0.2, 0.9, -0.3), (0, 0.4, -0.9), pelvis_y=-0.3, pelvis_z=-0.35, yaw=8, chest=12, head=0, pitch=6,
        lhand=(-1.0, 0.6, -0.6), rf=(0.7, -1.2, -6), lf=(-0.62, 0.5, 14), pole=(0.9, 0.3, 0.2)), lead)
    clip.pose(0.19, heavy_key(ready, (0.3, 1.25, -0.4), d(0.1, 0.97, -0.2), (0, 0.2, -1), pelvis_y=0.15, pelvis_z=-0.1, yaw=-4, chest=-6, head=-2, pitch=14,
        lhand=(-0.95, 0.75, -0.4), rf=(0.7, -0.8, -6, 0.1), lf=(-0.62, 0.7, 10, 0.05), pole=(1.0, 0.6, 0.0)), lead)
    clip.pose(0.255, heavy_key(ready, (0.3, 1.25, -1.0), d(0.05, 0.7, -0.7), (0, 0.8, 0.6), pelvis_y=-0.3, pelvis_z=-0.6, yaw=0, chest=0, head=0, pitch=-2,
        lhand=(-1.0, 0.45, -0.5), rf=(0.7, -1.5, -4, 0.12), lf=(-0.62, 0.55, 10), pole=(0.9, 0.1, 0.1)), lead)
    clip.pose(0.295, heavy_key(ready, (0.25, -0.65, -1.7), d(0.02, -0.6, -0.8), (0, 0.85, -0.5), pelvis_y=-0.88, pelvis_z=-1.0, yaw=2, chest=2, head=0, pitch=-16,
        lhand=(-1.2, -0.6, -0.4), rf=(0.7, -2.0, -2), lf=(-0.62, 0.35, 10), pole=(0.8, -0.5, 0.2)), lead)
    clip.pose(0.42, heavy_key(ready, (0.22, -0.8, -1.55), d(0.02, -0.7, -0.7), (0, 0.8, -0.55), pelvis_y=-0.92, pelvis_z=-1.02, yaw=3, chest=3, head=0, pitch=-18,
        lhand=(-1.2, -0.65, -0.4), rf=(0.7, -2.0, -2), lf=(-0.62, 0.35, 10), pole=(0.8, -0.5, 0.2)))
    clip.pose(0.55, heavy_key(ready, (0.22, -0.75, -1.5), d(0.02, -0.65, -0.75), (0, 0.8, -0.55), pelvis_y=-0.86, pelvis_z=-0.95, yaw=3, chest=3, head=0, pitch=-16,
        lhand=(-1.2, -0.6, -0.4), rf=(0.7, -1.95, -2), lf=(-0.62, 0.38, 10), pole=(0.8, -0.5, 0.2)))
    return clip, 0.55, None, {"Hit": 0.285, "Swing": (0.22, 0.36)}


def mountain_fall():
    """The finisher: the whole body gathers, leaps, and the blade comes down like a falling mountain: a deep landing, the blade driven forward and low."""
    ready = sword_ready_pose()
    clip = Clip("Sword")
    lead = {"pelvis": 0.04, "chest": 0.02}
    clip.pose(0.0, heavy_key(ready, (0.22, -0.75, -1.5), d(0.02, -0.65, -0.75), (0, 0.8, -0.55), pelvis_y=-0.86, pelvis_z=-0.95, yaw=3, chest=3, head=0, pitch=-16,
        lhand=(-1.2, -0.6, -0.4), rf=(0.7, -1.95, -2), lf=(-0.62, 0.38, 10), pole=(0.8, -0.5, 0.2)))
    # the gather: crouched low, the blade drawn back behind the body, both hands on it
    clip.pose(0.2, heavy_key(ready, (0.9, 0.1, 0.55), d(0.35, 0.3, 0.9), (0, 0.9, -0.4), pelvis_y=-0.8, pelvis_z=0.4, yaw=-12, chest=-20, head=-4, pitch=10,
        lhand=(-0.6, 0.2, 0.2), rf=(0.62, -0.4, -12), lf=(-0.62, 0.8, 8), pole=(0.95, 0.2, 0.1)), lead)
    clip.pose(0.38, heavy_key(ready, (0.7, 0.1, 0.65), d(0.3, 0.3, 0.9), (0, 0.9, -0.4), pelvis_y=-0.86, pelvis_z=0.45, yaw=-14, chest=-22, head=-5, pitch=12,
        lhand=(-0.6, 0.2, 0.3), rf=(0.62, -0.4, -12), lf=(-0.62, 0.8, 8), pole=(0.95, 0.2, 0.1)), lead)
    # the leap: both feet off the ground, the blade lifted to the sky behind the head
    clip.pose(0.55, heavy_key(ready, (0.45, 1.8, 0.3), d(0.1, 0.97, 0.2), (0, 0.4, -0.9), pelvis_y=0.85, pelvis_z=0.05, yaw=-6, chest=-10, head=-2, pitch=18,
        lhand=(-0.95, 0.95, -0.1), rf=(0.62, -0.6, -8, 0.6), lf=(-0.62, 0.5, 12, 0.5), pole=(1.0, 0.8, 0.0)), lead)
    clip.pose(0.66, heavy_key(ready, (0.4, 1.95, 0.1), d(0.05, 0.95, 0.3), (0, 0.4, -0.9), pelvis_y=1.05, pelvis_z=-0.1, yaw=-4, chest=-6, head=0, pitch=20,
        lhand=(-0.95, 1.0, -0.1), rf=(0.62, -0.7, -8, 0.8), lf=(-0.62, 0.45, 12, 0.7), pole=(1.0, 0.8, 0.0)), lead)
    # the fall: the blade comes down and forward, the body dropping with it
    clip.pose(0.74, heavy_key(ready, (0.3, 1.0, -1.4), d(0.03, 0.35, -0.94), (0, 0.9, 0.4), pelvis_y=0.1, pelvis_z=-0.7, yaw=2, chest=2, head=0, pitch=-4,
        lhand=(-1.0, 0.5, -0.5), rf=(0.62, -1.5, -4, 0.3), lf=(-0.62, 0.4, 10, 0.2), pole=(0.9, 0.2, 0.1)), lead)
    clip.pose(0.795, heavy_key(ready, (0.22, -0.7, -1.9), d(0.02, -0.5, -0.87), (0, 0.9, -0.4), pelvis_y=-0.98, pelvis_z=-1.15, yaw=2, chest=3, head=0, pitch=-20,
        lhand=(-1.2, -0.7, -0.5), rf=(0.7, -2.15, -2), lf=(-0.62, 0.3, 10), pole=(0.8, -0.6, 0.2)), lead)
    clip.pose(0.95, heavy_key(ready, (0.2, -0.85, -1.8), d(0.02, -0.55, -0.83), (0, 0.9, -0.4), pelvis_y=-1.02, pelvis_z=-1.18, yaw=2, chest=3, head=0, pitch=-22,
        lhand=(-1.25, -0.8, -0.4), rf=(0.7, -2.15, -2), lf=(-0.62, 0.3, 10), pole=(0.8, -0.6, 0.2)))
    clip.pose(1.1, heavy_key(ready, (0.2, -0.8, -1.7), d(0.02, -0.55, -0.83), (0, 0.9, -0.4), pelvis_y=-0.95, pelvis_z=-1.1, yaw=2, chest=3, head=0, pitch=-20,
        lhand=(-1.25, -0.75, -0.4), rf=(0.7, -2.05, -2), lf=(-0.62, 0.32, 10), pole=(0.8, -0.6, 0.2)))
    clip.pose(1.3, ready)
    return clip, 1.3, None, {"Hit": 0.795, "Swing": (0.7, 0.88)}


NEW = {"GaleSwift": gale_swift, "GaleCross": gale_cross, "GaleSpin": gale_spin, "GaleRush": gale_rush, "GaleStorm": gale_storm,
       "MountainCut": mountain_cut, "MountainChop": mountain_chop, "MountainFall": mountain_fall}
M.CLIPS.update(NEW)

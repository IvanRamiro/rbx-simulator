"""Combat VFX textures, drawn procedurally (run with Blender's Python: it has numpy). Like the
Qinggong textures, each is white with its shape in the alpha channel, so the game tints it per
realm.

- QiPalm: the print of a palm of Qi, the great hand a Qi Palm strike throws forward: a broad palm
  and five fingers outlined by a bright rim of Qi fading inward, the palm's lines, and a spiral of
  Qi at its heart.
- QiSlash: a crescent of sword light, sharp along its outer edge and fading in a soft wake
  behind it, thinning to points at both ends.
- BambooLeaf: a single bamboo leaf, long and lance-shaped, tip up, a fine midrib and faint parallel
  veins: the leaves the Bamboo Mantis Sage sheds and throws (tinted per effect).

Run (headless, so the open Blender scene is untouched):
    Blender -b --python-expr "import sys; sys.path.insert(0, '<repo>/tools/blender/vfx'); import combat_textures; combat_textures.build_all()"
Writes PNGs to assets/vfx/combat/.
"""
import math
import os

import numpy as np

import qinggong_textures as Q

OUT = os.path.join(Q.REPO, "assets", "vfx", "combat")


def save(name, alpha):
    """Q.save, into this module's folder."""
    saved = Q.OUT
    Q.OUT = OUT
    try:
        return Q.save(name, alpha)
    finally:
        Q.OUT = saved


def capsule(px, py, ax, ay, bx, by, r):
    """Signed distance to a capsule from (ax, ay) to (bx, by), radius r."""
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - (ax + vx * t), py - (ay + vy * t)) - r


def smooth_union(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def qi_palm(size=1024):
    x, y = Q.grid(size)
    # the palm: a rounded block, a little wider at the knuckles
    d = capsule(x, y, 0.0, -0.42, 0.0, -0.02, 0.36)
    d = smooth_union(d, capsule(x, y, -0.18, -0.05, 0.2, -0.05, 0.3), 0.12)
    # four fingers fanning slightly, the middle longest, and the thumb out to the side
    for fx, length, lean, r in ((-0.27, 0.5, -0.1, 0.085), (-0.09, 0.62, -0.03, 0.09), (0.09, 0.58, 0.03, 0.088), (0.26, 0.44, 0.1, 0.08)):
        d = smooth_union(d, capsule(x, y, fx, 0.05, fx + lean, 0.05 + length, r), 0.06)
    d = smooth_union(d, capsule(x, y, 0.3, -0.3, 0.62, 0.0, 0.095), 0.1)
    inside = Q.smoothstep(0.012, -0.012, d)
    rim = np.exp(-((d + 0.025) / 0.03) ** 2)                 # the bright rim, just inside the edge
    # a spiral of Qi at its heart, thinning toward its centre
    sd, st = Q.spiral_distance(x, y, 0.0, -0.2, 0.015, 0.21, 2.2, 0.0)
    spiral = Q.line(sd, 0.008 + 0.014 * st, 0.02) * (np.hypot(x, y + 0.2) < 0.225)
    alpha = np.clip(rim * 1.0 + inside * 0.24 + spiral * 0.8, 0, 1)
    alpha = np.maximum(alpha, Q.glow(rim, 8) * 0.5)        # a soft halo outside the rim
    save("QiPalm", alpha)


def qi_slash(size=512):
    x, y = Q.grid(size)
    # a crescent: between two circles, the outer edge sharp, the inner side fading as a wake
    r = np.hypot(x, y + 0.3)
    outer = 0.92
    edge = Q.smoothstep(outer + 0.01, outer - 0.01, r)
    wake = np.clip(1 - (outer - r) / 0.38, 0, 1) ** 2.2
    ang = np.arctan2(x, y + 0.3)
    taper = Q.smoothstep(1.15, 0.2, np.abs(ang))             # thinning to points at both ends
    core = np.exp(-((r - (outer - 0.025 * taper)) / (0.006 + 0.02 * taper)) ** 2)
    alpha = np.clip((wake * edge * 0.85 * taper + core * taper ** 0.5), 0, 1)
    save("QiSlash", alpha)


def bamboo_leaf(size=256):
    x, y = Q.grid(size)
    t = (y + 1) / 2                                           # 0 at the stem, 1 at the tip
    half = 0.21 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.6) ** 0.8 * Q.smoothstep(0.0, 0.14, t) + 0.01   # a short stalk, widest near it, a long tapering tip
    d = np.abs(x + 0.04 * np.sin(t * 3.0)) - half             # a slight sway along it
    inside = Q.smoothstep(0.012, -0.012, d) * (t > 0.02) * (t < 0.995)
    midrib = Q.line(np.abs(x + 0.04 * np.sin(t * 3.0)), 0.01, 0.012)
    veins = 0.5 + 0.5 * np.cos((x + 0.04 * np.sin(t * 3.0)) / np.maximum(half, 0.02) * np.pi * 3.5)
    alpha = inside * (0.86 + 0.1 * veins) * (1 - 0.25 * midrib)
    save("BambooLeaf", alpha)


def build_all():
    os.makedirs(OUT, exist_ok=True)
    qi_palm()
    qi_slash()
    bamboo_leaf()
    return sorted(os.listdir(OUT))

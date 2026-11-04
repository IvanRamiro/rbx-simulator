"""The interface's gold ornaments (the owner's reference, 2026-11-04: dark panels with gold trim, "but not
too much"), original drawings on a cloud-scroll motif:

    Corner.png     a window's top-left corner: two tapering arms and a curl of cloud; turned for the others
    EmblemRing.png the gold ring round the Cultivation dock's emblem
    LotusSit.png   the emblem itself: a cultivator seated in the lotus

    python3 tools/ui/draw_frame.py    # needs numpy and Pillow; writes assets/ui/frame/
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "ui", "frame")
SS = 8  # drawn this much larger, then reduced, for clean edges


def gold(mask):
    """Gold over a mask: bright along the top of each stroke, deep below, with a dark rim to lift it off anything."""
    h, w = mask.shape
    shifted = np.roll(mask, 3 * SS // 4, axis=0)
    light = np.clip(mask - shifted, 0, 1)                 # upper edges catch the light
    v = np.linspace(0, 1, h)[:, None]
    base = np.array([1.0, 0.80, 0.40])[None, None] * (1 - 0.32 * v[..., None])
    rgb = base + light[..., None] * np.array([0.5, 0.42, 0.3])[None, None]
    return np.clip(rgb, 0, 1)


def finish(hi, name, size):
    """hi: the strokes, as an 'L' image at SS times the size."""
    mask = np.asarray(hi, np.float32) / 255
    rim = np.asarray(hi.filter(ImageFilter.MaxFilter(2 * (SS // 2) + 1)), np.float32) / 255
    rgb = gold(mask)
    dark = np.array([0.20, 0.12, 0.05])
    out = dark[None, None] * (1 - mask[..., None]) + rgb * mask[..., None]
    px = np.dstack([out, rim])
    im = Image.fromarray((px * 255 + 0.5).astype(np.uint8)).resize((size, size) if isinstance(size, int) else size, Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name))
    return im


def stroke(draw, pts, w0, w1, n):
    """A polyline tapering from w0 to w1, in fractions of n."""
    count = len(pts)
    for i, (x, y) in enumerate(pts):
        t = i / max(1, count - 1)
        r = (w0 + (w1 - w0) * t) * n / 2
        draw.ellipse((x * n - r, y * n - r, x * n + r, y * n + r), fill=255)


def line(a, b, count=60):
    return [(a[0] + (b[0] - a[0]) * i / (count - 1), a[1] + (b[1] - a[1]) * i / (count - 1)) for i in range(count)]


def spiral(cx, cy, r0, r1, a0, turns, count=120):
    return [(cx + (r0 + (r1 - r0) * i / (count - 1)) * math.cos(a0 + turns * 2 * math.pi * i / (count - 1)),
             cy + (r0 + (r1 - r0) * i / (count - 1)) * math.sin(a0 + turns * 2 * math.pi * i / (count - 1))) for i in range(count)]


def diamond(draw, cx, cy, r, n):
    draw.polygon([(cx * n, (cy - r) * n), ((cx + r * 0.7) * n, cy * n), (cx * n, (cy + r) * n), ((cx - r * 0.7) * n, cy * n)], fill=255)


def corner():
    n = 128 * SS
    hi = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(hi)
    # the two arms along the edges, tapering away from the corner
    stroke(d, line((0.14, 0.09), (0.97, 0.09)), 0.052, 0.008, n)
    stroke(d, line((0.09, 0.14), (0.09, 0.97)), 0.052, 0.008, n)
    # a thin inner line that stops short
    stroke(d, line((0.30, 0.19), (0.66, 0.19)), 0.02, 0.004, n)
    stroke(d, line((0.19, 0.30), (0.19, 0.66)), 0.02, 0.004, n)
    # the cloud: a curl each way from the corner's point
    stroke(d, spiral(0.31, 0.27, 0.115, 0.018, math.radians(205), 1.15), 0.034, 0.016, n)
    stroke(d, spiral(0.27, 0.31, 0.115, 0.018, math.radians(245), -1.15), 0.034, 0.016, n)
    diamond(d, 0.095, 0.095, 0.085, n)
    diamond(d, 0.72, 0.19, 0.03, n)
    diamond(d, 0.19, 0.72, 0.03, n)
    return finish(hi, "Corner.png", 128)


def emblem_ring():
    """The gold ring round the Cultivation dock's emblem: a band, a fine inner line and eight small points."""
    n = 256 * SS
    hi = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(hi)
    c = n / 2

    def circle(r, value):
        d.ellipse((c - r * n, c - r * n, c + r * n, c + r * n), fill=value)

    circle(0.445, 255)
    circle(0.395, 0)
    circle(0.372, 255)
    circle(0.360, 0)
    for k in range(8):
        a = math.radians(k * 45 - 90)
        size = 0.062 if k % 2 == 0 else 0.04
        x, y = 0.5 + math.cos(a) * 0.452, 0.5 + math.sin(a) * 0.452
        tangent = (-math.sin(a), math.cos(a))
        radial = (math.cos(a), math.sin(a))
        pts = [(x + radial[0] * size * 1.0, y + radial[1] * size * 1.0), (x + tangent[0] * size * 0.55, y + tangent[1] * size * 0.55),
               (x - radial[0] * size * 0.8, y - radial[1] * size * 0.8), (x - tangent[0] * size * 0.55, y - tangent[1] * size * 0.55)]
        d.polygon([(px * n, py * n) for px, py in pts], fill=255)
    return finish(hi, "EmblemRing.png", 256)


def lotus_sit():
    """The Cultivation dock's emblem: a cultivator seated in the lotus, hands resting in the lap, in pale gold
    with a soft glow. The gaps between arm and body keep the pose readable at a small size."""
    n = 256 * SS
    hi = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(hi)

    def both(fn):
        fn(1)
        fn(-1)

    def mx(x, side):
        return 0.5 + (x - 0.5) * side

    # the head and its topknot
    d.ellipse(((0.5 - 0.082) * n, (0.215 - 0.09) * n, (0.5 + 0.082) * n, (0.215 + 0.09) * n), fill=255)
    d.ellipse(((0.5 - 0.034) * n, (0.1 - 0.034) * n, (0.5 + 0.034) * n, (0.1 + 0.034) * n), fill=255)
    stroke(d, line((0.5, 0.28), (0.5, 0.34), 12), 0.075, 0.085, n)
    # the body, narrowing to the waist
    d.polygon([(0.385 * n, 0.345 * n), (0.615 * n, 0.345 * n), (0.59 * n, 0.5 * n), (0.565 * n, 0.68 * n), (0.435 * n, 0.68 * n), (0.41 * n, 0.5 * n)], fill=255)
    stroke(d, line((0.395, 0.355), (0.605, 0.355), 20), 0.055, 0.055, n)

    def arm(side):
        pts = line((mx(0.375, side), 0.365), (mx(0.285, side), 0.54), 30) + line((mx(0.285, side), 0.54), (mx(0.45, side), 0.665), 30)
        stroke(d, pts, 0.07, 0.05, n)

    both(arm)
    stroke(d, line((0.42, 0.67), (0.58, 0.67), 20), 0.05, 0.05, n)   # the hands, together in the lap

    def leg(side):
        # the thigh out to the knee, then the shin folded back across under the other leg
        stroke(d, line((mx(0.46, side), 0.7), (mx(0.17, side), 0.8), 40), 0.125, 0.095, n)
        stroke(d, line((mx(0.17, side), 0.81), (mx(0.66, side), 0.86), 40), 0.095, 0.06, n)

    both(leg)
    mask = np.asarray(hi, np.float32) / 255
    rgb = np.ones(mask.shape + (3,), np.float32)
    v = np.linspace(0, 1, mask.shape[0])[:, None]
    rgb[..., 0] = 1.0
    rgb[..., 1] = 0.95 - 0.13 * v
    rgb[..., 2] = 0.78 - 0.34 * v
    # a soft glow behind the figure
    glow = np.asarray(hi.filter(ImageFilter.GaussianBlur(5 * SS)), np.float32) / 255
    alpha = np.maximum(mask, glow * 0.55)
    px = np.dstack([rgb, alpha])
    im = Image.fromarray((px * 255 + 0.5).astype(np.uint8)).resize((256, 256), Image.LANCZOS)
    im.save(os.path.join(OUT, "LotusSit.png"))
    return im


if __name__ == "__main__":
    corner(), emblem_ring(), lotus_sit()
    print("written", os.path.abspath(OUT))

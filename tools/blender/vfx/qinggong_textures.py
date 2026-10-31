"""Qinggong leap VFX textures, drawn procedurally (run inside Blender: its Python has numpy).

Every texture is white with the shape in its alpha channel, so the game tints it per realm
(azure, jade, gold, violet) and the particles add light (LightEmission 1).

- QiFormation: the circular Qi formation that blooms under a jump: rings, a band of auspicious
  cloud curls, a tick ring and a three-armed vortex at its heart.
- QiShockwave: a ring with a sharp leading edge, a soft wake and broken wind streaks.
- QiClouds: a 2x2 flipbook of four auspicious clouds (xiangyun): round lobes with a bright
  rim and spiral curls inside, trailing wisps underneath.
- QiSpike: a sharp spike of Qi (vertical, for VelocityParallel particles: the texture's up
  follows the particle's velocity).
- QiStreak: a thin wind streak with a bright head (vertical, as above).
- QiRibbon: a band of flowing silk for trails, stretched over the trail's length.

Run:
    import sys; sys.path.insert(0, "<repo>/tools/blender/vfx")
    import qinggong_textures; qinggong_textures.build_all()
Writes PNGs to assets/vfx/qinggong/.
"""
import math
import os
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(REPO, "assets", "vfx", "qinggong")


# ---------- helpers ----------
def grid(w, h=None):
    """Coordinates from -1 to 1 (x right, y up), one value per pixel centre."""
    h = h or w
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = (np.arange(h) + 0.5) / h * 2 - 1
    return np.meshgrid(xs, ys)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def line(d, width, soft):
    """Intensity of a line at distance d from its centre."""
    return 1.0 - smoothstep(width * 0.5, width * 0.5 + soft, np.abs(d))


def box_blur(a, r):
    """Box blur of radius r (pixels) along both axes, via running sums."""
    if r < 1:
        return a
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r + 1, r)
        p = np.pad(a, pad, mode="constant")
        c = np.cumsum(p, axis=axis)
        if axis == 0:
            a = (c[2 * r + 1:, :] - c[:-2 * r - 1, :]) / (2 * r + 1)
        else:
            a = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return a


def glow(a, r):
    """A soft gaussian-like glow: three box blurs."""
    for _ in range(3):
        a = box_blur(a, r)
    return a


def noise1(t, octaves, seed):
    """Smooth periodic 1D noise for angles: t in radians, a sum of sines with fixed phases."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(t)
    amp = 1.0
    for k in range(octaves):
        freq = 2 ** k * rng.integers(3, 6)
        out += amp * np.sin(t * freq + rng.uniform(0, 2 * math.pi))
        amp *= 0.5
    return out / 1.9


def spiral_distance(px, py, cx, cy, r0, r1, turns, phase, handed=1):
    """Distance from points to an Archimedean spiral centred at (cx, cy), from radius r0 at the
    centre out to r1, over `turns` turns. Returns (distance, t along the spiral 0..1)."""
    dx, dy = px - cx, py - cy
    r = np.hypot(dx, dy)
    a = (np.arctan2(dy, dx) * handed - phase) % (2 * math.pi)
    pitch = (r1 - r0) / (turns * 2 * math.pi)
    best = np.full_like(r, 9.0)
    best_t = np.zeros_like(r)
    for k in range(int(math.ceil(turns)) + 1):
        ang = a + 2 * math.pi * k
        rs = r0 + pitch * ang
        t = ang / (turns * 2 * math.pi)
        valid = t <= 1.0
        d = np.where(valid, np.abs(r - rs), 9.0)
        take = d < best
        best = np.where(take, d, best)
        best_t = np.where(take, t, best_t)
    return best, best_t


def save(name, alpha, rgb=None):
    """Write an RGBA PNG: white (or rgb) with the given alpha. alpha rows run bottom to top."""
    import bpy
    h, w = alpha.shape
    rgba = np.ones((h, w, 4), dtype=np.float32)
    if rgb is not None:
        rgba[..., :3] = rgb
    rgba[..., 3] = np.clip(alpha, 0, 1)
    img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h, alpha=True)
    if img.size[0] != w or img.size[1] != h:
        img.scale(w, h)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(rgba.ravel())
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


# ---------- textures ----------
def qi_formation(size=1024):
    x, y = grid(size)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    px = 2.0 / size
    a = np.zeros_like(r)
    # rings
    a = np.maximum(a, line(r - 0.945, 0.010, 2 * px))
    a = np.maximum(a, line(r - 0.875, 0.028, 2 * px) * (0.85 + 0.15 * np.cos(th * 24)))
    a = np.maximum(a, line(r - 0.585, 0.008, 2 * px))
    a = np.maximum(a, line(r - 0.505, 0.014, 2 * px))
    # tick ring between 0.6 and 0.66: 48 ticks, every fourth one long
    seg = (th / (2 * math.pi) * 48) % 1.0
    k = np.floor((th / (2 * math.pi) * 48) % 48)
    tick = line((seg - 0.5) / 48 * 2 * math.pi * r, 0.010, 2 * px)
    long_ = (k % 4) == 0
    reach = np.where(long_, 0.70, 0.655)
    a = np.maximum(a, tick * (r > 0.60) * (r < reach))
    # a band of eight auspicious cloud curls, each a spiral with a tail sweeping round the band
    band = np.zeros_like(r)
    for i in range(8):
        ang = i * 2 * math.pi / 8
        cx, cy = 0.77 * math.cos(ang), 0.77 * math.sin(ang)
        d, t = spiral_distance(x, y, cx, cy, 0.004, 0.072, 1.6, ang + 1.2)
        band = np.maximum(band, line(d, 0.016 - 0.006 * t, 2 * px))
        # the tail: an arc sweeping round the band from the curl's outer edge, thinning to a point
        rel = (th - ang) % (2 * math.pi)
        tail = (rel > 0.0) * (rel < 0.6)
        tail_w = 0.016 * (1 - rel / 0.6) + 0.002
        band = np.maximum(band, tail * line(r - (0.835 - rel * 0.06), tail_w, 2 * px))
    a = np.maximum(a, band)
    # the vortex: three arms spiralling from the heart out to the inner ring
    for i in range(3):
        d, t = spiral_distance(x, y, 0, 0, 0.03, 0.44, 0.85, i * 2 * math.pi / 3, handed=-1)
        a = np.maximum(a, line(d, 0.05 * (1 - t) + 0.008, 3 * px) * (r < 0.46) * (0.55 + 0.45 * (1 - t)))
    a = np.maximum(a, 1 - smoothstep(0.0, 0.06, r))
    a *= 1 - smoothstep(0.955, 0.98, r)
    a = np.clip(a + glow(a, 6) * 0.55, 0, 1)
    return save("QiFormation", a)


def qi_shockwave(size=512):
    x, y = grid(size)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    px = 2.0 / size
    edge = 0.9
    front = 1 - smoothstep(edge, edge + 3 * px, r)                        # sharp leading edge
    wake = np.exp(-np.clip(edge - r, 0, None) / 0.05)                     # short wake inward
    ring = front * wake * (r > edge - 0.3)
    streaks = 0.6 + 0.4 * np.clip(noise1(th, 4, 7) * 1.4, -1, 1)
    gaps = smoothstep(-0.55, -0.25, noise1(th, 2, 11))                    # broken in a few places
    a = ring * streaks * (0.4 + 0.6 * gaps)
    a = np.maximum(a, line(r - (edge - 0.012), 0.016, 2 * px) * (0.5 + 0.5 * gaps))
    # a fainter second ring of wind just behind the front
    a = np.maximum(a, line(r - (edge - 0.13), 0.01, 3 * px) * 0.45 * smoothstep(-0.2, 0.4, noise1(th, 3, 23)))
    a = np.clip(a + glow(a, 3) * 0.35, 0, 1)
    return save("QiShockwave", a)


# four cloud shapes: lobes (x, y, radius, curl turns) listed back to front, the tail's side
CLOUD_SHAPES = [
    ([(-0.2, 0.16, 0.2, 1.4), (0.16, 0.2, 0.17, 1.3), (0.32, -0.04, 0.2, 1.5), (-0.06, -0.08, 0.27, 1.75)], 1),
    ([(0.24, 0.18, 0.17, 1.3), (-0.3, 0.02, 0.19, 1.4), (0.05, 0.06, 0.25, 1.7), (0.3, -0.1, 0.16, 1.3)], -1),
    ([(0.0, 0.24, 0.18, 1.4), (-0.28, -0.02, 0.21, 1.5), (0.26, -0.02, 0.21, 1.5), (0.0, -0.1, 0.24, 1.7)], 1),
    ([(-0.3, 0.12, 0.16, 1.3), (-0.02, 0.2, 0.2, 1.5), (0.26, 0.06, 0.18, 1.4), (-0.12, -0.1, 0.23, 1.7), (0.2, -0.14, 0.17, 1.3)], -1),
]
CLOUD_SCALE = 1.4   # the cloud fills most of its cell


def cloud_cell(size, seed, shape):
    """One auspicious cloud in a square cell, white with alpha. Its lobes are spiral curls that
    overlap in layers (each nearer lobe hides the lines of the ones behind it), and a tapering
    tail sweeps away from its base."""
    rng = np.random.default_rng(seed)
    x, y = grid(size)
    x, y = x / CLOUD_SCALE, y / CLOUD_SCALE + 0.06   # draw at CLOUD_SCALE, nudged to centre the tail too
    px = 2.0 / size / CLOUD_SCALE
    lobes, flip = shape
    lobes = [(cx * flip + rng.uniform(-0.02, 0.02), cy + rng.uniform(-0.02, 0.02), rad * rng.uniform(0.95, 1.05), turns)
             for cx, cy, rad, turns in lobes]
    a = np.zeros_like(x)
    for cx, cy, rad, turns in lobes:
        d = np.hypot(x - cx, y - cy)
        inside = 1 - smoothstep(rad - px, rad + px, d)
        rim = line(d - rad + 0.016, 0.03, 2 * px)
        # the curl: from near the centre out until it meets the rim
        sd, t = spiral_distance(x, y, cx, cy, rad * 0.05, rad * 0.86, turns, rng.uniform(0, 2 * math.pi), handed=flip)
        curl = line(sd, 0.03 * (0.45 + 0.55 * t), 2 * px) * (d < rad)
        fill = 0.3 + 0.25 * smoothstep(cy - rad, cy + rad, y)
        lines = np.maximum(rim, curl)
        a = a * (1 - inside) + inside * np.maximum(fill, lines)
        a = np.maximum(a, rim)
    # the tail: a tapering stroke that leaves the lowest lobe on its side and sweeps out, curling
    # up at its tip, which stops just inside the cell
    side = [l for l in lobes if -flip * l[0] >= -0.05] or lobes
    sx, sy, srad, _ = min(side, key=lambda l: l[1] - l[2])
    x0, y0 = sx, sy - srad * 0.8
    x_end = -flip * (0.94 / CLOUD_SCALE - 0.04)
    tx = np.linspace(0.0, 1.0, 64)
    path = [(x0 + (x_end - x0) * t, y0 - 0.05 * math.sin(math.pi * t) + 0.16 * t ** 3) for t in tx]
    tail = np.zeros_like(x)
    for (x0, y0), (x1, y1), t in zip(path, path[1:], tx):
        vx, vy = x1 - x0, y1 - y0
        L = math.hypot(vx, vy)
        s_ = np.clip(((x - x0) * vx + (y - y0) * vy) / (L * L), 0, 1)
        dd = np.hypot(x - (x0 + vx * s_), y - (y0 + vy * s_))
        tail = np.maximum(tail, line(dd, 0.05 * (1 - t) + 0.006, 2 * px))
    a = np.maximum(a, tail * 0.9)
    a = np.clip(a + glow(a, max(2, size // 128)) * 0.35, 0, 1)
    m = int(size * 0.04)   # a clear margin so mipmaps never bleed into the next frame
    a[:m, :] = 0; a[-m:, :] = 0; a[:, :m] = 0; a[:, -m:] = 0
    return a


def qi_clouds(size=1024):
    cell = size // 2
    sheet = np.zeros((size, size))
    seeds = [3, 17, 29, 41]
    for i, s in enumerate(seeds):
        cx, cy = i % 2, 1 - i // 2      # flipbook frames read left to right, top to bottom
        sheet[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell] = cloud_cell(cell, s, CLOUD_SHAPES[i])
    return save("QiClouds", sheet)


def qi_spike(size=256):
    x, y = grid(size)
    t = (y + 1) / 2                                   # 0 at the bottom, 1 at the tip
    half = 0.16 * (1 - t) ** 1.35 * smoothstep(0.0, 0.18, t) + 0.004
    body = 1 - smoothstep(half * 0.6, half, np.abs(x))
    core = line(x, 0.03 * (1 - t) + 0.006, 0.01)
    a = np.maximum(body * (0.45 + 0.55 * t), core) * smoothstep(0.0, 0.25, t) * (1 - smoothstep(0.97, 1.0, t))
    a = np.clip(a + glow(a, 3) * 0.5, 0, 1)
    return save("QiSpike", a)


def qi_streak(size=128):
    x, y = grid(size)
    t = (y + 1) / 2                                   # the head is at the top
    w = 0.05 * smoothstep(0.0, 0.9, t) + 0.01
    a = line(x, w, 0.04) * smoothstep(0.0, 0.85, t) * (1 - smoothstep(0.93, 1.0, t))
    a = np.clip(a + glow(a, 2) * 0.4, 0, 1)
    return save("QiStreak", a)


def qi_ribbon(w=512, h=128):
    """Silk for trails (stretched over the whole trail, head at the left): one flowing band with
    bright edges and wind streaks running along it, breaking into dashes toward the tail."""
    x, y = grid(w, h)
    u = (x + 1) / 2
    px = 2.0 / h
    sway = 0.12 * np.sin(2 * math.pi * (u * 1.3 + 0.1))
    v = y - sway
    body = (1 - smoothstep(0.55, 0.8, np.abs(v))) * 0.38
    edges = line(np.abs(v) - 0.66, 0.06, 3 * px)
    rng = np.random.default_rng(5)
    streaks = np.zeros_like(x)
    for k in range(7):
        lane = rng.uniform(-0.5, 0.5)
        dash = smoothstep(-0.2, 0.3, np.sin(2 * math.pi * (u * rng.uniform(2, 5) + rng.uniform(0, 1))))
        keep = np.where(u < 0.45, 1.0, dash)               # solid near the head, dashed toward the tail
        streaks = np.maximum(streaks, line(v - lane, 0.035, 2 * px) * keep * rng.uniform(0.5, 0.9))
    a = np.maximum(np.maximum(body, edges), streaks)
    a = np.clip(a + box_blur(a, 2) * 0.3, 0, 1)
    return save("QiRibbon", a)


def build_all():
    return [qi_formation(), qi_shockwave(), qi_clouds(), qi_spike(), qi_streak(), qi_ribbon()]

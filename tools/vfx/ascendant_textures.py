"""Realm 5's own textures (the owner: "create your own assets ... more option better results",
2026-11-03). Each carries its own colour, white-hot to the owner's gold (255,170,40) to deep amber,
so its emitter's Color is white. Flipbooks are 4x4 cells of 256 in a 1024 sheet, OneShot; every
frame's content stays inside 80% of its cell (a clear margin, so neighbouring cells never bleed in).

    python3 ascendant_textures.py assets/aura/ascendant     (needs Pillow and numpy)

  GoldRippleLiquid.png  4x4  a crest of liquid gold rolls outward, a softer swell behind it,
                             wobbling and breaking up at the end
  GoldRippleWaves.png   4x4  three thin water rings travel outward one after another
  GoldSmoke.png         4x4  a puff billows, tears and thins; dark amber inside, gold-lit edges
  LightPillar.png       512  a tall thin shaft of light, white-hot core, soft gold falloff,
                             fading at both ends (FacingCameraWorldUp, Squash for height)
"""
import math
import os
import sys

import numpy as np
from PIL import Image

OUT = sys.argv[1]
# review boards go to renders/aura (git-ignored), never beside the uploaded textures
PREVIEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "renders", "aura")
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
CELL = 256
TAU = math.tau
rng = np.random.default_rng(55)

WHITE = np.array([255, 245, 215], dtype=float)
GOLD = np.array([255, 170, 40], dtype=float)
AMBER = np.array([200, 95, 15], dtype=float)


def colourise(i):
    """intensity (0..~2) to RGBA: amber when faint, the owner's gold, white-hot at the core"""
    lo = np.clip(i / 0.55, 0, 1)[..., None]
    hot = np.clip((i - 0.8) / 0.7, 0, 1)[..., None]
    rgb = AMBER * (1 - lo) + GOLD * lo
    rgb = rgb * (1 - hot) + WHITE * hot
    a = np.clip(i, 0, 1)
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(n, cells, seed):
    r = np.random.default_rng(seed)
    g = Image.fromarray((r.random((cells, cells)) * 255).astype(np.uint8))
    return np.asarray(g.resize((n, n), Image.BICUBIC), dtype=float) / 255


def fbm(n, cells, seed, octaves=4):
    tot, amp, w = np.zeros((n, n)), 1.0, 0.0
    for o in range(octaves):
        tot += value_noise(n, cells * 2 ** o, seed + o) * amp
        w += amp
        amp *= 0.5
    return tot / w


# a cell's coordinates: -1..1 maps to 80% of the cell (the clear margin)
yy, xx = np.mgrid[0:CELL, 0:CELL].astype(float)
X = (xx - CELL / 2) / (CELL * 0.4)
Y = (yy - CELL / 2) / (CELL * 0.4)
RAD = np.hypot(X, Y)
ANG = np.arctan2(Y, X)
EDGE = 1 - smoothstep(0.92, 1.0, RAD)        # nothing past the clear margin


def angular(freq, seed):
    r = np.random.default_rng(seed)
    v = sum((1 / k) * np.cos(k * ANG + r.random() * TAU) for k in range(1, freq + 1))
    return (v - v.min()) / (v.max() - v.min())


def sheet(frame_fn, name):
    out = np.zeros((CELL * 4, CELL * 4, 4), dtype=np.uint8)
    for f in range(16):
        t = f / 15
        cell = colourise(frame_fn(t, f) * EDGE)
        r, c = divmod(f, 4)
        out[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = cell
    Image.fromarray(out).save(os.path.join(OUT, name))
    return out


def ripple_liquid(t, f):
    r0 = 0.12 + 0.8 * (1 - (1 - t) ** 1.6)                 # rolls out fast, easing
    wob = (angular(7, 3) - 0.5) * 0.05 * (0.3 + t)
    d = RAD - r0 - wob
    crest = np.exp(-(d / (0.025 + 0.03 * t)) ** 2)
    swell = np.exp(-((d + 0.12 + 0.06 * t) / (0.07 + 0.05 * t)) ** 2) * 0.45
    fade = (1 - t) ** 1.1 * smoothstep(0, 0.08, t)
    breakup = 1 - smoothstep(0.55, 1.0, t) * (1 - smoothstep(0.35, 0.75, angular(11, 4)))
    return (crest * 1.6 + swell) * fade * breakup


def ripple_waves(t, f):
    i = np.zeros_like(RAD)
    for k in range(3):
        tk = t * 1.35 - k * 0.2                              # three rings, one after another
        if tk <= 0 or tk >= 1:
            continue
        r0 = 0.1 + 0.85 * tk
        d = RAD - r0 - (angular(5, 10 + k) - 0.5) * 0.03
        ring = np.exp(-(d / 0.018) ** 2) * 1.3 + np.exp(-((d + 0.05) / 0.04) ** 2) * 0.25
        i += ring * (1 - tk) ** 1.3 * smoothstep(0, 0.1, tk) * (0.6 + 0.4 * angular(9, 20 + k))
    return i


rng.random(78)  # the draws of a retired texture (GoldRippleSparkle): kept so every texture after it comes out the same


WARP_A = fbm(512, 4, 71)
WARP_B = fbm(512, 4, 72)
WARP_A += 0.5 - WARP_A.mean()               # centred, so the puff stays mid-cell
WARP_B += 0.5 - WARP_B.mean()
BODY = fbm(512, 6, 73)
TEAR = fbm(512, 9, 74)


def sample(field, x, y):
    """bilinear lookup of a square field at coordinates in -1..1 (wrapping)"""
    n = field.shape[0]
    fx = (x * 0.5 + 0.5) * (n - 1)
    fy = (y * 0.5 + 0.5) * (n - 1)
    x0, y0 = np.floor(fx).astype(int) % n, np.floor(fy).astype(int) % n
    x1, y1 = (x0 + 1) % n, (y0 + 1) % n
    tx, ty = fx - np.floor(fx), fy - np.floor(fy)
    top = field[y0, x0] * (1 - tx) + field[y0, x1] * tx
    bottom = field[y1, x0] * (1 - tx) + field[y1, x1] * tx
    return top * (1 - ty) + bottom * ty


def smoke(t, f):
    """a puff that boils outward and curls (a domain-warped outline), tears into wisps as it ages,
    and is lit along its edges by the circle's gold: the edge is where its density falls off"""
    swirl = 0.8 * t
    cs, sn = math.cos(swirl), math.sin(swirl)
    rx, ry = X * cs - Y * sn, X * sn + Y * cs
    amp = 0.3 + 0.4 * t
    wx = rx + (sample(WARP_A, rx * 0.6, ry * 0.6) - sample(WARP_A, 0, 0)) * amp      # zero at the centre: the puff stays mid-cell
    wy = ry + (sample(WARP_B, rx * 0.6 + 0.3, ry * 0.6) - sample(WARP_B, 0.3, 0)) * amp
    r = np.hypot(wx, wy)
    radius = 0.68 + 0.27 * t
    shape = 1 - smoothstep(radius * 0.45, radius, r)
    dens = shape * (0.5 + 0.5 * sample(BODY, wx * 0.8, wy * 0.8 + t * 0.3))
    erode = smoothstep(0.15 + 0.55 * t, 0.35 + 0.55 * t, sample(TEAR, wx, wy - t * 0.2) + (1 - shape) * 0.2)
    dens *= 1 - (1 - erode) * min(1, max(0, t - 0.2) * 1.4)
    dens *= (1 - t ** 1.6) * smoothstep(0, 0.12, t + 0.05)
    # the lit edge: brightest where the density thins toward the outline
    edge = shape * (1 - shape) * 4
    return dens * 0.75 + edge * dens * 1.4


for fn, name in ((ripple_liquid, "GoldRippleLiquid.png"), (ripple_waves, "GoldRippleWaves.png"), (smoke, "GoldSmoke.png")):
    sheet(fn, name)

# the light pillar: one image, the shaft upright
N = 512
py, px = np.mgrid[0:N, 0:N].astype(float)
u = (px - N / 2) / (N / 2)
v = (py - N / 2) / (N / 2)
along = smoothstep(1.0, 0.55, np.abs(v)) * (0.85 + 0.15 * np.cos(v * 9))
streak = 0.75 + 0.25 * np.asarray(Image.fromarray((rng.random((48, 1)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), dtype=float) / 255
core = np.exp(-(u / 0.02) ** 2) * 1.8 + np.exp(-(u / 0.08) ** 2) * 0.6 + np.exp(-(u / 0.25) ** 2) * 0.2
pillar = core * along * streak * (1 - smoothstep(0.9, 1.0, np.abs(u)))
Image.fromarray(colourise(pillar)).save(os.path.join(OUT, "LightPillar.png"))


# the crown's bloom: a soft halo of warm light behind it (Bloom is screen-wide in Roblox, so the
# crown carries its own), with faint long rays
H = 512
hy, hx = np.mgrid[0:H, 0:H].astype(float)
hu, hv = (hx - H / 2) / (H / 2), (hy - H / 2) / (H / 2)
hr = np.hypot(hu, hv)
ha = np.arctan2(hv, hu)
halo = np.exp(-(hr / 0.32) ** 2) * 0.9 + np.exp(-(hr / 0.6) ** 2) * 0.35
rays = (0.5 + 0.5 * np.cos(ha * 8)) ** 10 * np.exp(-(hr / 0.55) ** 2) * 0.12
glow = (halo + rays) * (1 - smoothstep(0.85, 1.0, hr))
Image.fromarray(colourise(glow * 0.9)).save(os.path.join(OUT, "CrownGlow.png"))

# a preview of every sheet on a dark ground, for review
def preview(name):
    a = np.asarray(Image.open(os.path.join(OUT, name)), dtype=float)
    bg = np.array([12, 18, 40], dtype=float)
    al = a[..., 3:] / 255
    return np.clip(bg * (1 - al) + a[..., :3] * al * 1.25, 0, 255).astype(np.uint8)


tiles = [Image.fromarray(preview(n)).resize((512, 512)) for n in
         ("GoldRippleLiquid.png", "GoldRippleWaves.png", "GoldSmoke.png", "LightPillar.png")]
board = Image.new("RGB", (512 * 4 + 30, 512), (40, 40, 40))
for k, tile in enumerate(tiles):
    board.paste(tile, (k * 522, 0))
board.save(os.path.join(PREVIEWS, "Realm5Textures_preview.png"))
print("written:", sorted(n for n in os.listdir(OUT) if n.endswith(".png")))

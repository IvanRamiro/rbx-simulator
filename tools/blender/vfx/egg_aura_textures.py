"""Egg aura textures (the auras are built in src/worldbuild/EggAuraVFX.lua), drawn procedurally (run inside Blender: its Python has numpy). White with the
shape in alpha, tinted per egg in the game. Single frames only (the auras use no flipbooks).

Ground formations, one per egg:
- SigilWindRose (Spirit Breeze): six wind arms sweeping round a still centre, inside a ring of
  cloud-curl dashes.
- SigilWuxing (Elemental Core): the five-element cycle: five element rings joined by the
  generating pentagon and the overcoming star, round a diamond core.

Jade Grove formations:
- SigilJadeLeaf (Jade Spirit): a vine ring sprouting leaves round a six-leaf rosette of jade, its
  leaves joined by a fine inner ring.
- SigilBlossom (Bloomwood): a blossom mandala: five broad petals round a small five-petal heart,
  a ring of petal-tip beads between two fine rings.
- SigilTreeRings (Ancient Grove): the growth rings of an ancient tree, uneven and slightly off
  centre, crossed by roots that branch outward through them.

- AuraVortex (Ancient Grove): a soft vortex of five thin arms of Qi, fading as they sweep out
  from a still eye.
- AuraBloomLight (Bloomwood): a bloom of light: soft rays fanning out in petal-shaped lobes round a
  bright heart.
  (VFX Studio's swirl vortex and radial burst have no alpha, only white on black, so they cannot
  sit on a SurfaceGui plane: these replace them.)

Ember Peak formations and particles:
- SigilFissure (Inferno): a caldera: broken rings of crust round a molten eye, jagged fissures
  branching out through them.
- SigilCrystalForge (Magma Heart): six long crystal points round an inner hexagon, a ring of
  forge ticks, and a molten heart.
- SigilPhoenix (Phoenix Ash): a phoenix with spread wings of feathers and a long tail, inside a
  ring of flame tongues licking outward.
- SigilCrustRing (Inferno): a ring of dark basalt crust broken into uneven segments, molten lava
  glowing in the breaks and heating the crust's edges red, a thin broken thread of lava inside it.
  Coloured, not white: the crust must stay dark against the glow.
- AuraAsh: one flake of ash, irregular and thin at its edges (tinted grey in the game).
- AuraSpark: one spark: a hot core with a short soft tail toward the bottom, with real alpha so it
  keeps its colour over a bright sky without light emission (the library's dots are white on black
  and only work additively); used along the particle's velocity, it reads as a streak.
- AuraSlash: one thick slash: a crescent swelling to its full stroke mid-arc and tapering to
  sharp points, a solid core with soft edges and a faint glow (tinted in the game).
- AuraFlameTongue: one flame tongue, hot at its root, curling as it rises (single frame).
- AuraRock: a chunk of obsidian with lava veins, modelled and rendered in Blender.

Rings:
- AuraQiRing (Beginner Qi): a bold band of Qi with a fine inner thread strung with Qi beads, and six comet streaks
  riding just outside it, so the ring visibly flows as it turns (bold enough to read in daylight,
  which VFX Studio's hairline rings do not).

- AuraElementBand (Elemental Core): a gyroscope band: twin rails with a bright band between,
  broken by five element nodes (a ring round a bead), one per element of the cycle beneath.

Beams:
- AuraStream (Elemental Core): an element stream that tiles along its length: a bright core
  with two filaments braiding round it and packets of energy riding along it (scrolled by the
  beam's TextureSpeed).
- AuraVessel (Magma Heart): a molten artery that tiles along its length, coloured (not white): a
  white-hot core inside a blood-red body darkening to soft edges, the vessel weaving a little,
  with pulses of heat swelling the core as they ride along it. The beams scroll it up and tint it
  only along their length (dim at the root, full at the crown).

Particles and floating objects (Jade Grove):
- AuraPetal: one blossom petal, notched at its tip, with a faint midrib.
- AuraBlossom: a five-petal blossom with a stamen ring, for floating billboards.

Particles and floating objects:
- AuraFeather: a soft feather with its vane lines.
- AuraCloud: one auspicious cloud.
- AuraCrystal: a faceted crystal shard, modelled and rendered in Blender (near-white facets with
  bright edges, so it tints to any colour), floated round the eggs as a billboard.

Writes PNGs to assets/vfx/eggs/.
"""
import math
import os

import numpy as np

import qinggong_textures as Q

OUT = os.path.join(Q.REPO, "assets", "vfx", "eggs")
grid, smoothstep, line, glow, spiral_distance = Q.grid, Q.smoothstep, Q.line, Q.glow, Q.spiral_distance


def save(name, alpha, rgb=None):
    Q.OUT = OUT
    return Q.save(name, alpha, rgb)


def segment(x, y, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(x - (ax + vx * t), y - (ay + vy * t))


def sigil_wind_rose(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = line(r - 0.92, 0.01, 2 * px)
    # a ring of cloud-curl dashes: short arcs each ending in a small curl
    for k in range(10):
        ang = k * math.tau / 10
        rel = (th - ang) % math.tau
        a = np.maximum(a, line(r - 0.82, 0.014, 2 * px) * (rel < 0.38))
        cx, cy = 0.82 * math.cos(ang + 0.38), 0.82 * math.sin(ang + 0.38)
        d, t = spiral_distance(x, y, cx, cy, 0.004, 0.045, 1.2, ang)
        a = np.maximum(a, line(d, 0.012, 2 * px))
    # six wind arms sweeping from the still centre out to the ring, thinning as they go
    for k in range(6):
        d, t = spiral_distance(x, y, 0, 0, 0.12, 0.74, 0.55, k * math.tau / 6, handed=-1)
        a = np.maximum(a, line(d, 0.05 * (1 - t) ** 1.2 + 0.006, 3 * px) * (r > 0.1) * (r < 0.76))
    a = np.maximum(a, line(r - 0.1, 0.012, 2 * px))
    a *= 1 - smoothstep(0.94, 0.97, r)
    return save("SigilWindRose", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def sigil_wuxing(size=768):
    x, y = grid(size)
    r = np.hypot(x, y)
    px = 2.0 / size
    a = np.maximum(line(r - 0.94, 0.014, 2 * px), line(r - 0.88, 0.006, 2 * px))
    nodes = [(0.66 * math.cos(math.pi / 2 + k * math.tau / 5), 0.66 * math.sin(math.pi / 2 + k * math.tau / 5)) for k in range(5)]
    for k, (nx, ny) in enumerate(nodes):
        d = np.hypot(x - nx, y - ny)
        a = np.maximum(a, line(d - 0.14, 0.016, 2 * px))          # each element's ring
        a = np.maximum(a, line(d - 0.09, 0.006, 2 * px) * 0.8)
        bx, by = nodes[(k + 1) % 5]                               # the generating cycle (pentagon)
        a = np.maximum(a, line(segment(x, y, nx, ny, bx, by), 0.01, 2 * px) * (d > 0.14) * (np.hypot(x - bx, y - by) > 0.14))
        cx, cy = nodes[(k + 2) % 5]                               # the overcoming cycle (star)
        a = np.maximum(a, line(segment(x, y, nx, ny, cx, cy), 0.006, 2 * px) * 0.75 * (d > 0.14) * (np.hypot(x - cx, y - cy) > 0.14))
    ax_, ay_ = np.abs(x), np.abs(y)                               # the diamond core
    a = np.maximum(a, line(ax_ / 0.13 + ay_ / 0.18 - 1, 0.12, 0.05))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilWuxing", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def qi_ring(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = line(r - 0.86, 0.024, 3 * px)                                        # the band
    a = np.maximum(a, line(r - 0.785, 0.006, 2 * px) * 0.6)                  # a fine inner thread...
    for k in range(12):                                                      # ...strung with Qi beads
        ang = (k + 0.5) * math.tau / 12
        d = np.abs(x - 0.785 * math.cos(ang)) + np.abs(y - 0.785 * math.sin(ang))
        a = np.maximum(a, line(d, 0.04, 3 * px))
    for k in range(6):                                                       # comets: a soft head, a long tapering tail
        rel = (th - k * math.tau / 6) % math.tau
        t = np.clip(rel / 0.95, 0, 1)
        width = 0.032 * smoothstep(0, 0.05, t) * (1 - t) ** 0.8 + 0.002
        a = np.maximum(a, line(r - 0.93, width, 2 * px) * (rel < 0.95) * (1 - t) ** 0.6)
    a *= 1 - smoothstep(0.97, 0.99, r)
    return save("AuraQiRing", np.clip(a + glow(a, 6) * 0.7, 0, 1))


def element_band(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    nodes = [(0.87 * math.cos(math.pi / 2 + k * math.tau / 5), 0.87 * math.sin(math.pi / 2 + k * math.tau / 5)) for k in range(5)]
    near = np.min([np.hypot(x - nx, y - ny) for nx, ny in nodes], axis=0)
    gap = smoothstep(0.075, 0.095, near)                                     # the band breaks round each node
    a = np.maximum(line(r - 0.81, 0.008, 2 * px), line(r - 0.93, 0.008, 2 * px)) * gap
    a = np.maximum(a, line(r - 0.87, 0.03, 3 * px) * gap)
    a = np.maximum(a, line(near - 0.06, 0.014, 2 * px))                      # each node: a ring...
    a = np.maximum(a, 1 - smoothstep(0.02, 0.03, near))                      # ...round a bead
    a *= 1 - smoothstep(0.97, 0.99, r)
    return save("AuraElementBand", np.clip(a + glow(a, 6) * 0.7, 0, 1))


def stream(w=512, h=128):
    x, y = grid(w, h)
    u = (x + 1) / 2                                   # every term has whole periods in u, so it tiles
    px = 2.0 / h
    core = line(y, 0.14, 0.14) * 0.75
    braids = np.maximum(line(y - 0.5 * np.sin(2 * math.pi * 2 * u), 0.06, 3 * px),
                        line(y + 0.5 * np.sin(2 * math.pi * 2 * u), 0.06, 3 * px)) * 0.8
    packets = smoothstep(0.55, 0.95, np.cos(2 * math.pi * 3 * u)) * (1 - smoothstep(0.05, 0.4, np.abs(y)))
    a = np.maximum(np.maximum(core, braids), packets)
    halo = glow(np.concatenate([a, a, a], axis=1), 3)[:, w:2 * w]   # blurred across the seam, so it tiles
    return save("AuraStream", np.clip(a + halo * 0.5, 0, 1) * (1 - smoothstep(0.85, 1, np.abs(y))))


def vessel(w=512, h=128):
    x, y = grid(w, h)
    u = (x + 1) / 2                                   # every term has whole periods in u, so it tiles
    t = 2 * math.pi * u
    yv = y - 0.1 * np.sin(t * 2 + 0.6) - 0.05 * np.sin(t * 5 + 2.1)   # the vessel weaves a little
    pulse = smoothstep(0.35, 1, 0.6 * np.cos(t * 3) + 0.4 * np.cos(t * 7 + 1.3))   # heat riding along it
    body = 1 - smoothstep(0.45, 0.92, np.abs(yv))
    core = np.exp(-(yv / (0.06 + 0.05 * pulse)) ** 2)            # the white-hot thread
    inner = np.exp(-(yv / 0.3) ** 2)                              # molten glow round it
    strands = 0.8 + 0.2 * np.sin(yv * 24 + 1.8 * np.sin(t * 3 + 0.4) + 0.9 * np.sin(t * 5))   # flow lines along it
    heat = np.clip(core * (0.75 + 0.25 * pulse) + 0.6 * inner * strands * (0.65 + 0.35 * pulse) + 0.2 * body, 0, 1)
    # a ramp from a dark rim through blood red and orange to white-hot
    stops = [(0, (0.22, 0.02, 0.03)), (0.35, (0.8, 0.07, 0.05)), (0.7, (1, 0.42, 0.1)), (1, (1, 0.93, 0.72))]
    rgb = np.zeros(heat.shape + (3,))
    for (k0, c0), (k1, c1) in zip(stops, stops[1:]):
        f = np.clip((heat - k0) / (k1 - k0), 0, 1)[..., None]
        inside = ((heat >= k0) & (heat <= k1))[..., None]
        rgb = np.where(inside, np.array(c0) + (np.array(c1) - np.array(c0)) * f, rgb)
    return save("AuraVessel", np.clip(body * (0.75 + 0.25 * strands) + core, 0, 1), rgb)


def sigil_jade_leaf(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    # the vine ring, wavering as it goes round
    wav = 0.83 + 0.015 * np.sin(th * 9)
    a = line(r - wav, 0.022, 3 * px)
    a = np.maximum(a, line(r - 0.95, 0.008, 2 * px))
    # leaves sprouting from the vine, alternating in and out
    for k in range(18):
        ang = k * math.tau / 18
        out = 1 if k % 2 else -1
        bx, by = 0.83 * math.cos(ang), 0.83 * math.sin(ang)
        d_ang = ang + out * 0.0 + 0.5            # each leaf leans along the vine
        dx, dy = math.cos(ang) * out * 0.55 + math.cos(d_ang + math.pi / 2) * 0.45, math.sin(ang) * out * 0.55 + math.sin(d_ang + math.pi / 2) * 0.45
        L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
        # leaf as a lens: distance along and across its axis
        u = (x - bx) * dx + (y - by) * dy
        v = -(x - bx) * dy + (y - by) * dx
        length = 0.1
        t = np.clip(u / length, 0, 1)
        half = 0.034 * np.sin(np.pi * t) ** 0.8
        inside = (u > 0) * (u < length) * (np.abs(v) < half)
        a = np.maximum(a, inside * 0.85)
        a = np.maximum(a, line(v, 0.004, px) * (u > 0) * (u < length * 0.9))
    # the six-leaf rosette
    for k in range(6):
        ang = k * math.tau / 6 + math.pi / 2
        dx, dy = math.cos(ang), math.sin(ang)
        u = x * dx + y * dy
        v = -x * dy + y * dx
        t = np.clip((u - 0.12) / 0.46, 0, 1)
        half = 0.13 * np.sin(np.pi * t) ** 0.9
        edge = line(np.abs(v) - half, 0.014, 2 * px) * (u > 0.12) * (u < 0.58)
        a = np.maximum(a, edge)
        a = np.maximum(a, line(v, 0.008, 2 * px) * (u > 0.12) * (u < 0.55))           # midrib
        for vk in (0.25, 0.45, 0.65):                                                      # side veins
            c = 0.12 + 0.46 * vk
            a = np.maximum(a, line(np.abs(v) - (u - c) * 0.9, 0.005, px) * (u > c) * (np.abs(v) < half) * 0.8)
    a = np.maximum(a, line(r - 0.6, 0.008, 2 * px) * 0.7)
    a = np.maximum(a, 1 - smoothstep(0.05, 0.08, r))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilJadeLeaf", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def sigil_blossom(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = np.maximum(line(r - 0.94, 0.01, 2 * px), line(r - 0.8, 0.008, 2 * px))
    # beads between the rings, one per petal tip and between
    for k in range(20):
        ang = k * math.tau / 20 + math.pi / 2
        d = np.hypot(x - 0.87 * math.cos(ang), y - 0.87 * math.sin(ang))
        a = np.maximum(a, 1 - smoothstep(0.014, 0.022, d) if k % 4 == 0 else line(d - 0.016, 0.006, px))
    # five broad petals, each notched at its tip, with veins fanning from the base
    for k in range(5):
        ang = k * math.tau / 5 + math.pi / 2
        dx, dy = math.cos(ang), math.sin(ang)
        u = x * dx + y * dy
        v = -x * dy + y * dx
        t = np.clip((u - 0.16) / 0.6, 0, 1)
        half = 0.3 * np.sin(np.pi * np.clip(t * 0.85 + 0.08, 0, 1)) ** 0.7
        notch = 0.06 * np.exp(-(v / 0.05) ** 2) * (t > 0.85)
        outline = line(np.maximum(np.abs(v) - half, u - 0.76 + notch), 0.014, 2 * px) * (u > 0.16)
        a = np.maximum(a, outline)
        for fan in (-0.5, -0.25, 0.0, 0.25, 0.5):
            a = np.maximum(a, line(v - fan * (u - 0.2), 0.004, px) * (u > 0.22) * (u < 0.66) * (np.abs(v) < half * 0.9) * 0.7)
    # the heart: a small five-petal flower with a stamen ring
    for k in range(5):
        ang = k * math.tau / 5 + math.pi / 2 + math.pi / 5
        d = np.hypot(x - 0.1 * math.cos(ang), y - 0.1 * math.sin(ang))
        a = np.maximum(a, line(d - 0.06, 0.01, 2 * px))
    a = np.maximum(a, 1 - smoothstep(0.03, 0.045, r))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilBlossom", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def sigil_tree_rings(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    # growth rings: uneven, wider on one side, drifting off centre as the tree grew
    a = np.zeros_like(x)
    for k in range(9):
        rr = 0.1 + 0.095 * k
        cx, cy = 0.03 * math.sin(k * 0.7), -0.025 * k / 9
        rk = np.hypot(x - cx, y - cy)
        thk = np.arctan2(y - cy, x - cx)
        wob = rr * (1 + 0.05 * np.sin(thk * 3 + k) + 0.03 * np.sin(thk * 7 - k * 2))
        a = np.maximum(a, line(rk - wob, 0.007 if k % 3 else 0.014, 2 * px) * (0.6 + 0.4 * (k % 3 == 0)))
    # roots: from the heart out through the rings, each branching once
    rng = np.random.default_rng(81)
    for k in range(7):
        ang = k * math.tau / 7 + rng.uniform(-0.2, 0.2)
        pts = [(0.12 * math.cos(ang), 0.12 * math.sin(ang))]
        a_ = ang
        for i in range(8):
            a_ += rng.uniform(-0.3, 0.3)
            px_, py_ = pts[-1]
            pts.append((px_ + 0.1 * math.cos(a_), py_ + 0.1 * math.sin(a_)))
        for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
            a = np.maximum(a, line(segment(x, y, ax, ay, bx, by), 0.026 * (1 - i / 9) + 0.004, 2 * px))
        bx0, by0 = pts[4]
        b_ = a_ + rng.choice([-0.8, 0.8])
        prev = (bx0, by0)
        for i in range(3):
            nxt = (prev[0] + 0.09 * math.cos(b_), prev[1] + 0.09 * math.sin(b_))
            a = np.maximum(a, line(segment(x, y, prev[0], prev[1], nxt[0], nxt[1]), 0.012 * (1 - i / 4), 2 * px))
            prev = nxt
            b_ += rng.uniform(-0.3, 0.3)
    a = np.maximum(a, line(r - 0.95, 0.012, 2 * px))
    a = np.maximum(a, 1 - smoothstep(0.04, 0.06, r))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilTreeRings", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def vortex(size=768):
    x, y = grid(size)
    r = np.hypot(x, y)
    px = 2.0 / size
    a = np.zeros_like(x)
    for k in range(5):
        d, t = spiral_distance(x, y, 0, 0, 0.1, 0.95, 0.6, k * math.tau / 5)
        a = np.maximum(a, line(d, 0.032 * (1 - t) + 0.006, 3 * px) * (1 - t) ** 0.9 * (r > 0.08))
    a = np.maximum(a, line(r - 0.1, 0.014, 2 * px) * 0.8)
    a *= 1 - smoothstep(0.85, 0.98, r)
    return save("AuraVortex", np.clip(a + glow(a, 6) * 0.5, 0, 1))


def bloom_light(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    lobes = 0.5 + 0.5 * np.cos(5 * (th - math.pi / 2))
    reach = 0.45 + 0.45 * lobes ** 1.5
    petals = (1 - smoothstep(reach * 0.5, reach, r)) * (0.35 + 0.65 * lobes)
    rays = (0.5 + 0.5 * np.cos(40 * th)) ** 6 * (1 - smoothstep(0.2, 0.92, r)) * 0.45
    heart = 1 - smoothstep(0.05, 0.2, r)
    a = np.maximum(np.maximum(petals * 0.55, rays), heart)
    a *= 1 - smoothstep(0.9, 0.99, r)
    return save("AuraBloomLight", np.clip(a + glow(a, 6) * 0.3, 0, 1))


def sigil_fissure(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    rng = np.random.default_rng(111)
    a = np.zeros_like(x)
    # broken rings of crust: arcs with gaps, each ring at its own wobble
    for k, (rr, gaps) in enumerate(((0.3, 5), (0.55, 7), (0.8, 9))):
        wob = rr * (1 + 0.04 * np.sin(th * (3 + k) + k))
        keep = (np.sin(th * gaps + k * 1.7) > -0.55)
        a = np.maximum(a, line(r - wob, 0.016 - 0.003 * k, 2 * px) * keep)
    a = np.maximum(a, line(r - 0.95, 0.01, 2 * px))
    # jagged fissures branching outward from the eye
    for k in range(9):
        ang = k * math.tau / 9 + rng.uniform(-0.2, 0.2)
        pts = [(0.12 * math.cos(ang), 0.12 * math.sin(ang))]
        a_ = ang
        for i in range(9):
            a_ += rng.uniform(-0.55, 0.55)
            px_, py_ = pts[-1]
            pts.append((px_ + 0.095 * math.cos(a_), py_ + 0.095 * math.sin(a_)))
        for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
            a = np.maximum(a, line(segment(x, y, ax, ay, bx, by), 0.024 * (1 - i / 10) + 0.004, 2 * px))
        if k % 2 == 0:
            bx0, by0 = pts[4]
            b_ = a_ + rng.choice([-0.9, 0.9])
            prev = (bx0, by0)
            for i in range(3):
                nxt = (prev[0] + 0.08 * math.cos(b_), prev[1] + 0.08 * math.sin(b_))
                a = np.maximum(a, line(segment(x, y, prev[0], prev[1], nxt[0], nxt[1]), 0.012 * (1 - i / 4), 2 * px))
                prev = nxt
                b_ += rng.uniform(-0.4, 0.4)
    a = np.maximum(a, 1 - smoothstep(0.07, 0.11, r))           # the molten eye
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilFissure", np.clip(a + glow(a, 6) * 0.6, 0, 1))


def crust_ring(size=768, segments=13, seed=9):
    x, y = grid(size)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    px = 2.0 / size
    rnd = np.random.default_rng(seed)
    wobble = Q.noise1(th, 3, seed)
    r0 = 0.7 + 0.025 * wobble + 0.008 * Q.noise1(th * 7, 2, seed + 6)
    r1 = 0.9 + 0.03 * Q.noise1(th + 1.0, 3, seed + 1) + 0.012 * Q.noise1(th * 9, 2, seed + 7)   # a chipped rim
    band = smoothstep(r0 - 2 * px, r0 + 2 * px, r) * (1 - smoothstep(r1 - 2 * px, r1 + 2 * px, r))
    # the breaks: uneven angles, narrow and jagged (zigzagging as they cross the band), each its own
    # width; `gap` is the distance to the nearest (image units)
    cuts = (np.arange(segments) + rnd.uniform(-0.35, 0.35, segments)) * 2 * math.pi / segments
    widths = rnd.uniform(0.006, 0.02, segments)
    gap = np.full_like(r, 9.0)
    for k, (c, w) in enumerate(zip(cuts, widths)):
        jag = 0.03 * Q.noise1(r * 14 + k, 2, seed + 10 + k) + 0.01 * Q.noise1(r * 45 + k, 2, seed + 30 + k)
        d = np.abs((th - c - jag + math.pi) % (2 * math.pi) - math.pi) * r - w
        gap = np.minimum(gap, d)
    crack = 1 - smoothstep(0, 7 * px, gap)                          # molten, fading out of each break
    core = 1 - smoothstep(0, 1.5 * px, gap)                         # its white-hot middle
    # fine fissures meandering across the crust, glowing faintly
    fissure = line(Q.noise1(th * 6 + r * 14, 3, seed + 5), 0.012, 2 * px) * smoothstep(-0.3, 0.3, Q.noise1(th * 3, 2, seed + 8))
    rim_heat = 1 - smoothstep(0, 0.035, np.minimum(r - r0, r1 - r))  # the crust's edges heated red
    mott = Q.noise1(th * 23 + r * 31, 3, seed + 3) * 0.5 + Q.noise1(th * 57 + r * 71, 2, seed + 9) * 0.5
    tone = np.clip(0.09 + 0.06 * mott, 0.03, 0.18)
    thread = line(r - (0.63 + 0.012 * wobble), 0.008, 2 * px) * smoothstep(-0.2, 0.4, Q.noise1(th * 2, 2, seed + 4))
    heat = np.clip(np.maximum.reduce([crack * 0.8 + core * 0.2, rim_heat * 0.45 * band, fissure * 0.55 * band, thread]), 0, 1)
    rock = np.stack([tone * 1.1, tone * 0.85, tone * 0.8], axis=-1)
    stops = [(0, None), (0.35, (0.55, 0.06, 0.02)), (0.7, (1, 0.4, 0.06)), (1, (1, 0.9, 0.6))]
    rgb = rock.copy()
    for (k0, c0), (k1, c1) in zip(stops, stops[1:]):
        f = np.clip((heat - k0) / (k1 - k0), 0, 1)[..., None]
        a = rock if c0 is None else np.array(c0)
        rgb = np.where(((heat >= k0) & (heat <= k1))[..., None], a + (np.array(c1) - a) * f, rgb)
    alpha = np.clip(np.maximum(band, thread) + glow(crack * band, 4) * 0.5, 0, 1)
    return save("SigilCrustRing", alpha, rgb)


def spark(size=128):
    x, y = grid(size)
    # an elongated drop: round at the top (the leading end), tapering into a tail below
    yy = np.where(y > 0, y / 0.32, y / 0.95)
    d = np.hypot(x / (0.22 + 0.1 * smoothstep(-1, 0.3, y)), yy)
    body = 1 - smoothstep(0.55, 1.0, d)
    core = 1 - smoothstep(0.0, 0.45, np.hypot(x / 0.16, (y - 0.08) / 0.2))
    return save("AuraSpark", np.clip(body * 0.75 + core * 0.25, 0, 1) ** 0.9)


def slash(size=512, radius=0.66, thickness=0.26, sweep=(15, 205)):
    x, y = grid(size)
    r = np.hypot(x, y)
    th = np.degrees(np.arctan2(y, x)) % 360
    a0, a1 = sweep
    t = np.clip((th - a0) / (a1 - a0), 0, 1)
    inside = (th >= a0) & (th <= a1)
    # the stroke swells to its full thickness a little past the middle and tapers to points
    half = 0.5 * thickness * np.sin(math.pi * t ** 0.85) * inside
    d = np.abs(r - radius)
    px = 2.0 / size
    body = 1 - smoothstep(half * 0.55, half + 1.5 * px, d)
    core = 1 - smoothstep(0, half * 0.45 + px, d)
    halo = 1 - smoothstep(half, half + 0.06, d)
    stroke = (body * 0.85 + core * 0.15) * smoothstep(0, 2 * px, half)   # nothing where the stroke has no width
    return save("AuraSlash", np.clip(np.maximum(stroke, halo * 0.22 * inside), 0, 1))


def ash(size=128, seed=21):
    x, y = grid(size)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    edge = 0.62 + 0.2 * Q.noise1(th, 3, seed) + 0.06 * Q.noise1(th * 3, 2, seed + 1)
    body = 1 - smoothstep(edge - 0.08, edge, r)
    thin = 0.85 + 0.15 * Q.noise1(th * 4, 2, seed + 2)                 # unevenly thin, not a glow
    return save("AuraAsh", body * thin)


def sigil_crystal_forge(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = np.maximum(line(r - 0.94, 0.012, 2 * px), line(r - 0.88, 0.006, 2 * px))
    for k in range(36):                                          # forge ticks between the rings
        ang = k * math.tau / 36
        rel = np.abs(((th - ang + math.pi) % math.tau) - math.pi)
        a = np.maximum(a, (rel < 0.012 + 0.008 * (k % 3 == 0)) * (r > 0.885) * (r < 0.935) * 1.0)
    for k in range(6):                                           # six crystal points, faceted
        ang = k * math.tau / 6 + math.pi / 2
        dx, dy = math.cos(ang), math.sin(ang)
        u = x * dx + y * dy
        v = -x * dy + y * dx
        t = (u - 0.24) / 0.6
        half = 0.11 * (1 - np.abs(2 * t - 0.6) / 1.4).clip(0, 1) ** 0.9
        inside = (t > 0) * (t < 1) * (np.abs(v) < half)
        a = np.maximum(a, line(np.abs(v) - half, 0.012, 2 * px) * (t > 0) * (t < 1))
        a = np.maximum(a, line(v, 0.006, px) * (t > 0.05) * (t < 0.95) * 0.8)      # the facet ridge
        a = np.maximum(a, inside * 0.22)
    hexd = np.maximum.reduce([np.abs(x * math.cos(k * math.pi / 3) + y * math.sin(k * math.pi / 3)) for k in range(3)])
    a = np.maximum(a, line(hexd - 0.22, 0.012, 2 * px))
    a = np.maximum(a, 1 - smoothstep(0.08, 0.12, r))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilCrystalForge", np.clip(a + glow(a, 5) * 0.55, 0, 1))


def sigil_phoenix(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    # a ring of flame tongues licking outward
    tongues = 0.86 + 0.07 * np.abs(np.sin(th * 12)) ** 3
    a = line(r - 0.78, 0.012, 2 * px)
    a = np.maximum(a, line(r - tongues, 0.01, 2 * px) * (np.abs(np.sin(th * 12)) > 0.15))
    a = np.maximum(a, (r > 0.78) * (r < tongues) * 0.18)
    # the phoenix: body down the middle, head with a crest, two wings of feathers fanning up and out
    body = (x / 0.075) ** 2 + ((y - 0.02) / 0.24) ** 2
    a = np.maximum(a, 1 - smoothstep(0.85, 1.0, body))                                             # body
    a = np.maximum(a, 1 - smoothstep(0.05, 0.065, np.hypot(x, y - 0.3)))                           # head
    for k, ang in enumerate((1.4, 1.65, 1.9)):                                                    # crest
        dx, dy = math.cos(ang), math.sin(ang)
        u = x * dx + (y - 0.33) * dy
        v = -x * dy + (y - 0.33) * dx
        a = np.maximum(a, (1 - smoothstep(0.008, 0.016, np.abs(v) + 0.03 * np.clip(u / 0.16, 0, 1))) * (u > 0) * (u < 0.16))
    for side in (1, -1):
        for k in range(7):                                                                          # wing feathers
            ang = math.radians(8 + 11 * k)                     # spread out sideways and up
            dx, dy = side * math.cos(ang), math.sin(ang)
            bx, by = side * 0.06, 0.1
            u = (x - bx) * dx + (y - by) * dy
            v = -(x - bx) * dy + (y - by) * dx
            length = 0.34 + 0.3 * math.sin(math.pi * (k + 1) / 8)
            t = np.clip(u / length, 0, 1)
            half = 0.045 * np.sin(np.pi * t) ** 0.8
            a = np.maximum(a, (1 - smoothstep(half * 0.7, half, np.abs(v))) * (u > 0) * (u < length) * 0.85)
    for k in range(5):                                                                              # tail
        ang = -math.pi / 2 + (k - 2) * 0.22
        dx, dy = math.cos(ang), math.sin(ang)
        u = x * dx + (y + 0.17) * dy
        v = -x * dy + (y + 0.17) * dx
        length = 0.42 - 0.06 * abs(k - 2)
        t = np.clip(u / length, 0, 1)
        half = 0.035 * np.sin(np.pi * t) ** 0.7
        a = np.maximum(a, (1 - smoothstep(half * 0.7, half, np.abs(v))) * (u > 0) * (u < length) * 0.8)
    a *= 1 - smoothstep(0.95, 0.99, r)
    return save("SigilPhoenix", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def flame_tongue(size=256):
    x, y = grid(size)
    t = np.clip((y + 0.85) / 1.75, 0, 1)                             # 0 at its root, 1 at its tip
    sway = 0.13 * np.sin(t * 5.0) * t ** 1.3
    half = 0.36 * np.sqrt(np.sin(np.pi * np.clip(t * 0.92 + 0.08, 0, 1))) * (1 - 0.55 * t)
    d = np.abs(x - sway)
    body = (1 - smoothstep(half * 0.5, half + 0.02, d)) * (y > -0.85)
    a = body * (1 - t) ** 0.6 * smoothstep(0.0, 0.1, t)             # hottest (most opaque) near the root
    a = np.maximum(a, (1 - smoothstep(0.0, half * 0.45, d)) * (1 - t) ** 1.5 * smoothstep(0.0, 0.1, t))
    return save("AuraFlameTongue", np.clip(a, 0, 1))


def petal(size=256):
    x, y = grid(size)
    t = np.clip((y + 0.92) / 1.84, 0, 1)                        # base near the bottom, tip near the top
    half = 0.5 * t ** 0.75 * (1 - t ** 4) ** 0.45                 # a teardrop: narrow base, broad near the tip
    notch = 0.14 * np.exp(-(x / 0.1) ** 2)
    body = (1 - smoothstep(half - 0.03, half, np.abs(x))) * (1 - smoothstep(0.93 - notch, 0.97 - notch, t)) * (y > -0.92)
    a = body * (0.65 + 0.35 * t)                                 # paler (more opaque) toward the tip
    a = a * (1 - 0.15 * line(x, 0.015, 0.02) * (t < 0.75))       # a faint midrib
    return save("AuraPetal", np.clip(a + glow(a, 2) * 0.2, 0, 1))


def blossom(size=256):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    lobe = 0.5 + 0.5 * np.cos(5 * (th - math.pi / 2))
    rim = 0.55 + 0.37 * lobe ** 0.6
    notch = 0.1 * np.exp(-(((th - math.pi / 2) * 5 / math.tau + 0.5) % 1.0 - 0.5) ** 2 / 0.0015)
    body = 1 - smoothstep(rim - notch - 0.012, rim - notch, r)
    a = body * 0.8
    a = np.maximum(a, line(r - 0.22, 0.03, 2 * px))                      # the stamen ring
    for k in range(10):
        ang = k * math.tau / 10
        d = np.hypot(x - 0.3 * math.cos(ang), y - 0.3 * math.sin(ang))
        a = np.maximum(a, 1 - smoothstep(0.025, 0.04, d))
    a = a * (1 - 0.35 * (1 - smoothstep(0.08, 0.16, r)))                 # a softer heart
    return save("AuraBlossom", np.clip(a + glow(a, 3) * 0.35, 0, 1))


def feather(size=256):
    x, y = grid(size)
    t = (y + 1) / 2
    width = 0.42 * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.8 * (1 - 0.3 * t)
    bend = 0.12 * (t - 0.5) ** 2
    xs = x - bend
    vane = 1 - smoothstep(width * 0.85, width, np.abs(xs))
    barbs = 0.65 + 0.35 * np.abs(np.sin((y * 26 + np.abs(xs) * 10)))
    shaft = line(xs, 0.025, 0.01) * (t > 0.02)
    a = np.maximum(vane * barbs * (t > 0.08) * 0.85, shaft)
    return save("AuraFeather", np.clip(a + glow(a, 2) * 0.3, 0, 1))


def rock(size=256):
    """Renders a chunk of obsidian with lava veins (a real Blender mesh with the eggs' obsidian
    shader) to a transparent PNG, for rock billboards and debris particles."""
    import sys
    sys.path.insert(0, os.path.join(Q.REPO, "tools", "blender", "eggs"))
    import bpy
    import egg_hi as Hm
    import egg_render as R
    import eggs_ember as E
    coll = bpy.data.collections.get("VFXSprites") or bpy.data.collections.new("VFXSprites")
    old = bpy.data.objects.get("AuraRockMesh")
    if old:
        bpy.data.objects.remove(old)
    hi = Hm.Hi()
    E.rock(hi, (0, 0.4, 0), 0.45, seed=7, stretch=(1.0, 0.8, 0.9), n=18)
    obj = hi.object("AuraRockMesh", coll, [Hm.mat_obsidian("AuraRockMat")], smooth=False, weld=0)
    scene = R.lab()
    scene.render.film_transparent = True
    path = os.path.join(OUT, "AuraRock.png")
    from mathutils import Vector
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    centre = sum(corners, Vector()) / 8
    R.render([obj], path, view="three_quarter", size=(size, size), centre=tuple(centre), distance=2.3, cycles=32)
    scene.render.film_transparent = False
    return path


def cloud(size=512):
    return save("AuraCloud", Q.cloud_cell(size, 3, Q.CLOUD_SHAPES[0]))


def crystal(size=512):
    """Renders a faceted crystal shard (a real Blender mesh) to a transparent PNG."""
    import bpy
    import sys
    sys.path.insert(0, os.path.join(Q.REPO, "tools", "blender", "eggs"))
    import egg_kit as K
    import egg_render as R
    mb = K.W.MeshBuilder()
    # a double-pointed crystal with two small splinters growing from its waist
    K.shard(mb, (0, -0.1, 0), (0.05, 1, 0.12), 1.35, 0.38, (0.5, 0.5), seed=7, sides=6)
    K.shard(mb, (0, 0.0, 0), (-0.05, -1, -0.12), 0.85, 0.36, (0.5, 0.5), seed=8, sides=6)
    K.shard(mb, (0.22, -0.1, 0.05), (0.7, 1, 0.2), 0.75, 0.15, (0.5, 0.5), seed=9, sides=5)
    K.shard(mb, (-0.2, 0.05, -0.05), (-0.8, 0.4, -0.15), 0.6, 0.13, (0.5, 0.5), seed=11, sides=5)
    coll = bpy.data.collections.get("VFXSprites") or bpy.data.collections.new("VFXSprites")
    old = bpy.data.objects.get("AuraCrystalMesh")
    if old:
        bpy.data.objects.remove(old)
    mat = bpy.data.materials.get("AuraCrystalMat") or bpy.data.materials.new("AuraCrystalMat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.85, 0.92, 1.0, 1)
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Emission Color"].default_value = (0.55, 0.7, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 0.35
    obj = mb.object("AuraCrystalMesh", coll, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    scene = R.lab()
    scene.render.film_transparent = True
    path = os.path.join(OUT, "AuraCrystal.png")
    os.makedirs(OUT, exist_ok=True)
    R.render([obj], path, view="three_quarter", size=(size, size), centre=(0, 0, 0.3), distance=5.2)
    scene.render.film_transparent = False
    return path


def build_all():
    return [sigil_wind_rose(), sigil_wuxing(), sigil_jade_leaf(), sigil_blossom(), sigil_tree_rings(), petal(), blossom(), vortex(), bloom_light(), sigil_fissure(), sigil_crystal_forge(), sigil_phoenix(), crust_ring(), ash(), spark(), slash(), flame_tongue(), rock(), qi_ring(), element_band(), stream(), vessel(), feather(), cloud(), crystal()]

"""Yggdrasil's eggs, first made for the Starting Island (after the 15-egg concept sheet).

- Beginner Qi Egg: an egg of cut blue crystal, its facets catching the light in different blues,
  with Qi light glowing along the cuts and leaking through a few cracked facets.
- Spirit Breeze Egg: a sky-blue egg brushed with white wind lines, a gold crescent swirl on its
  shoulder holding a glowing breeze sigil, resting on a bed of gold-rimmed auspicious clouds.
- Elemental Core Egg: a dark cracked stone egg in an angular gold cage, a large cyan core crystal
  set in its front, smaller gems round the belt, and Qi light seeping through the cracks.
"""
import math
import random

import egg_kit as K

W = K.W
V = K.V
TAU = K.TAU
H, R = K.H, K.R


# ---------- atlas ----------
def crystal(u, v):
    """Six tones of blue crystal across u (each plate picks one), from ice-white to deep cobalt,
    lighter toward the top of the egg."""
    tones = [(0.78, 0.93, 1.0), (0.36, 0.66, 1.0), (0.14, 0.38, 0.92), (0.52, 0.8, 1.0), (0.08, 0.22, 0.7), (0.24, 0.52, 0.96)]
    c = tones[min(5, int(u * 6))]
    k = 0.6 + 0.4 * v
    return tuple(min(1.0, x * k + 0.1 * v * v) for x in c)


def breeze(u, v):
    """Sky-blue porcelain, deeper at the base, brushed with broad white wind bands that sweep
    diagonally round the egg and thin out into fine trailing lines."""
    base = K.strip_fn([(0.0, (0.16, 0.42, 0.82)), (0.45, (0.38, 0.66, 0.95)), (1.0, (0.7, 0.88, 1.0))])(u, v)
    phase = v * 5.0 + 0.7 * math.sin(u * TAU * 2 + v * 3.0) + u * 3.0
    f = phase % 1.0
    band = max(0.0, 1 - abs(f - 0.5) / 0.16) ** 1.5          # the broad bands
    fine = max(0.0, 1 - abs(((phase * 3) % 1.0) - 0.5) / 0.05) * 0.5   # fine lines between them
    taper = 0.55 + 0.45 * math.sin(u * TAU * 2 + v * 5)
    w = min(1.0, (band + fine) * taper)
    return tuple(min(1.0, b + (0.97 - b) * w) for b in base)


def gold(u, v):
    return K.strip_fn([(0.0, (0.42, 0.26, 0.06)), (0.5, (0.86, 0.62, 0.2)), (0.85, (1.0, 0.86, 0.45)), (1.0, (1.0, 0.95, 0.75))])(u, v)


def cloud(u, v):
    return K.strip_fn([(0.0, (0.62, 0.72, 0.86)), (0.6, (0.9, 0.94, 1.0)), (1.0, (1.0, 1.0, 1.0))])(u, v)


def stone(u, v):
    """Dark blue-grey stone with a network of thin dark cracks. Noise runs in arc length round
    the egg and height up it, so it is even in every direction (the seam sits at the back)."""
    x, y = ((u + 0.5) % 1.0) * TAU * R, v * H
    base = K.strip_fn([(0.0, (0.15, 0.17, 0.23)), (0.6, (0.28, 0.31, 0.4)), (1.0, (0.4, 0.43, 0.53))])(u, v)
    mottle = 0.06 * W.fbm(x * 1.6 + 3, y * 1.6, seed=32, octaves=3)
    crack = abs(W.fbm(x * 1.1 + 7, y * 1.1, seed=33, octaves=3))
    dark = max(0.0, 1 - crack / 0.03)
    return tuple(max(0.0, min(1.0, (c + mottle) * (1 - 0.7 * dark))) for c in base)


STRIPS = [(96, crystal), (128, breeze), (64, gold), (48, cloud), (128, stone)]
CRYSTAL, BREEZE, GOLD, CLOUD, STONE = range(5)


def atlas():
    img, bands = W.atlas_image("EggsStart_Atlas", 512, STRIPS)
    return img, bands, W.textured_material("EggsStart_Mat", img)


# ---------- Beginner Qi Egg ----------
QI_EDGE = "3fc6ff"   # the Qi core glowing through the seams


def beginner_qi(coll, mat, bands):
    """Long irregular plates of cut crystal over a core of Qi light that glows through the seams."""
    mb = W.MeshBuilder()
    sites = K.surface_sites(46, seed=11)
    K.crystal_plates(mb, bands[CRYSTAL], sites, gap=0.93, lift=(0.0, 0.02), tilt=0.07, depth=0.12, seed=12, peak=0.07)
    body = mb.object("BQ_Plates", coll, mat)
    core = W.MeshBuilder()
    K.shell(core, (0.5, 0.5), nu=28, nv=18, offset=-0.05)
    g = core.object("BQ_Core", coll, K.glow_material(QI_EDGE))
    return [body], {QI_EDGE: [g]}


# ---------- Spirit Breeze Egg ----------
SB_SIGIL = "56d8ff"


def spirit_breeze(coll, mat, bands):
    mb = W.MeshBuilder()
    K.shell(mb, bands[BREEZE], nu=44, nv=30)
    body = mb.object("SB_Shell", coll, mat, smooth=True)
    gold = W.MeshBuilder()
    glow = W.MeshBuilder()
    # the gold crescent on the egg's right shoulder, opening toward the front, with a curl at its tip
    cu, cv = 0.19, 0.58
    arc = []
    for i in range(22):
        a = math.radians(-150 + 300 * i / 21)
        p, _ = K.egg_point(cu + 0.2 * math.cos(a) * 0.55, cv + 0.22 * math.sin(a), offset=0.05)
        arc.append(p)
    K.tube(gold, arc, lambda x: 0.075 * (0.3 + 0.7 * math.sin(math.pi * x)), 7, bands[GOLD], per=2)
    curl = []
    for i in range(18):
        x = i / 17
        a = math.radians(150) + TAU * 1.15 * x
        rr = 0.075 * (1 - 0.8 * x)
        p, _ = K.egg_point(cu + 0.2 * math.cos(math.radians(150)) * 0.55 + rr * math.cos(a) * 0.9, cv + 0.22 * math.sin(math.radians(150)) + rr * math.sin(a), offset=0.05)
        curl.append(p)
    K.tube(gold, curl, lambda x: 0.05 * (1 - 0.6 * x), 6, bands[GOLD], per=2)
    # the breeze sigil cradled in the crescent: three sweeping wind strokes
    for k, (dv, length) in enumerate(((0.08, 0.13), (0.0, 0.17), (-0.08, 0.12))):
        stroke = []
        for i in range(10):
            x = i / 9
            p, nn = K.egg_point(cu - 0.02 + (x - 0.5) * length + 0.01 * k, cv + dv + 0.025 * math.sin(math.pi * x), offset=0.02)
            stroke.append(p)
        for a, b in zip(stroke, stroke[1:]):
            K.strip_between(glow, a, b, K.egg_point(cu, cv)[1], 0.045 * (1.2 - abs(k - 1) * 0.3), (0.5, 0.5), lift=0.0)
    # the bed of clouds: five puffs round the base, each a cluster of round lobes with gold curls
    clouds = W.MeshBuilder()
    for k in range(5):
        u = (k + 0.5) / 5 + 0.04
        p, n = K.egg_point(u, 0.16)
        base = V((p.x, 0.24, p.z)) * 1.0
        out = V((p.x, 0, p.z)).normalized()
        for j, (dx, dy, rr) in enumerate(((-0.34, 0.0, 0.27), (0.0, 0.14, 0.36), (0.35, 0.0, 0.26), (0.06, -0.1, 0.28))):
            side = out.cross(V((0, 1, 0))).normalized()
            cc = base + side * dx + V((0, dy, 0)) + out * 0.16
            clouds.lathe([(0.0, rr, 1.0), (rr * 0.7, rr * 0.72, 0.95), (rr, 0.0, 0.8), (rr * 0.72, -rr * 0.68, 0.55), (0.0, -rr * 0.9, 0.4)],
                         10, bands[CLOUD], centre=tuple(cc), cap_top=False, u_repeat=1.0)
        # a gold curl on the cloud's face
        K.xiangyun(gold, base + out * 0.5 + V((0, 0.05, 0)), out, (0, 1, 0), 0.56, bands[GOLD], thick=0.03, flip=1 if k % 2 else -1)
    g = gold.object("SB_Gold", coll, mat)
    c = clouds.object("SB_Clouds", coll, mat, smooth=True)
    s_ = glow.object("SB_Sigil", coll, K.glow_material(SB_SIGIL))
    return [body, g, c], {SB_SIGIL: [s_]}


# ---------- Elemental Core Egg ----------
EC_CORE = "2ee6ff"
EC_CRACK = "1f8dff"


def raised_plate(mb, outline, band, lift=0.05, base=0.012, rings=4):
    """A gold plate lying on the egg: outline is a convex list of (u, v) on the shell. Its face
    follows the shell's curve (rings of points between the outline and its centre, each laid on
    the egg) `lift` off the shell, with walls down to `base`."""
    cu = sum(u for u, _ in outline) / len(outline)
    cv = sum(v for _, v in outline) / len(outline)
    grid = []
    for r in range(rings + 1):
        t = 1 - r / rings
        grid.append([K.egg_point(cu + (u - cu) * t, cv + (v - cv) * t, offset=lift) for u, v in outline])
    centre, cn = K.egg_point(cu, cv, offset=lift)
    m = len(outline)
    for r in range(rings):
        for i in range(m):
            j = (i + 1) % m
            if r == rings - 1:
                K.W_oriented(mb, [grid[r][i][0], grid[r][j][0], centre], tuple(cn), band, 0.5, 0.62)
            else:
                K.W_oriented(mb, [grid[r][i][0], grid[r][j][0], grid[r + 1][j][0], grid[r + 1][i][0]], tuple(grid[r][i][1]), band, 0.5, 0.62)
    bot = [K.egg_point(u, v, offset=base)[0] for u, v in outline]
    for i in range(m):
        j = (i + 1) % m
        K.W_oriented(mb, [grid[0][i][0], grid[0][j][0], bot[j], bot[i]], tuple((grid[0][i][0] + grid[0][j][0]) / 2 - centre), band, 0.5, 0.45)


def elemental_core(coll, mat, bands):
    mb = W.MeshBuilder()
    K.shell(mb, bands[STONE], nu=44, nv=30)
    body = mb.object("EC_Shell", coll, mat, smooth=True)
    gold = W.MeshBuilder()
    glow = W.MeshBuilder()
    lo, hi = 0.4, 0.5      # the belt's lower and upper edges
    # the belt: a broad gold band standing off the shell, with a rolled rim along each edge
    K.shell(gold, bands[GOLD], nu=48, nv=3, offset=0.045, v_from=lo, v_to=hi)
    for v in (lo, hi):
        rim = [K.egg_point(i / 48, v, offset=0.05)[0] for i in range(48)]
        K.tube(gold, rim, lambda x: 0.03, 6, bands[GOLD], per=1, closed=True)
    # pointed plates: tall ones rising toward the crown, short ones hanging below the belt
    for k in range(10):
        u = k / 10 + 0.05
        if abs(((u + 0.5) % 1.0) - 0.5) < 0.09:
            continue   # the front is the core's
        w = 0.042
        tall = k % 2 == 0
        rise = 0.36 if tall else 0.22
        raised_plate(gold, [(u - w, hi), (u - w * 0.9, hi + rise * 0.45), (u, hi + rise), (u + w * 0.9, hi + rise * 0.45), (u + w, hi)], bands[GOLD])
        drop = 0.2 if tall else 0.13
        raised_plate(gold, [(u - w * 0.8, lo), (u + w * 0.8, lo), (u, lo - drop)], bands[GOLD])
        if tall:   # a strap from the tall plate's tip to the crown
            strap = [K.egg_point(u, hi + rise + (0.94 - hi - rise) * i / 6, offset=0.045)[0] for i in range(7)]
            K.tube(gold, strap, lambda x: 0.032 * (1 - 0.35 * x), 6, bands[GOLD], per=2)
            gp, gn = K.egg_point(u, hi + rise * 0.55, offset=0.06)
            K.gem(glow, gp, gn, (0, 1, 0), 0.07, 0.1, 0.045, (0.5, 0.5))
    # the crown: a cap with six claws
    gold.lathe([(0.0, H + 0.08, 1.0), (0.14, H + 0.03, 0.95), (0.25, H - 0.08, 0.8), (0.3, H - 0.18, 0.7), (0.24, H - 0.24, 0.5)],
               12, bands[GOLD], cap_top=False, u_repeat=1.0)
    for k in range(6):
        a = TAU * k / 6 + 0.26
        base = V((math.sin(a) * 0.27, H - 0.14, math.cos(a) * 0.27))
        K.shard(gold, base, (math.sin(a) * 0.5, 1.0, math.cos(a) * 0.5), 0.22, 0.045, bands[GOLD], seed=k, sides=4)
    # the core: a large cut crystal in a pointed diamond bezel at the front
    cv = (lo + hi) / 2
    cp, cn = K.egg_point(0.0, cv, offset=0.03)
    up = V((0, 1, 0))
    side = up.cross(cn).normalized()
    upn = cn.cross(side).normalized()
    diamond = [cp + upn * 0.5, cp + side * 0.34, cp - upn * 0.42, cp - side * 0.34]
    frame = []
    for i in range(4):
        a, b = diamond[i], diamond[(i + 1) % 4]
        for t in range(4):
            frame.append(a + (b - a) * t / 4 + cn * 0.06)
    K.tube(gold, frame, lambda x: 0.045, 6, bands[GOLD], per=2, closed=True)   # per=2 rounds the corners so the tube never folds
    K.gem(glow, cp + cn * 0.04, cn, (0, 1, 0), 0.5, 0.74, 0.26, (0.5, 0.5))
    # gems on the belt either side of the core and round the back
    for u in (0.16, 0.84, 0.38, 0.62):
        gp, gn = K.egg_point(u, cv, offset=0.075)
        K.gem(glow, gp, gn, (0, 1, 0), 0.11, 0.15, 0.06, (0.5, 0.5))
    # Qi seeping through cracks that run out from the core into the stone
    cracks = W.MeshBuilder()
    rnd = random.Random(41)
    for k, a0 in enumerate((40, 140, 215, 320, 95)):
        u, v = 0.0, cv
        a = math.radians(a0 + rnd.uniform(-10, 10))
        prev = None
        for i in range(10):
            a += rnd.uniform(-0.5, 0.5)
            u += math.cos(a) * 0.02
            v += math.sin(a) * 0.05
            if not 0.07 < v < 0.9:
                break
            p, n = K.egg_point(u, v, offset=0.006)
            inside_belt = lo - 0.01 < v < hi + 0.01
            if prev is not None and i > 2 and not inside_belt:
                K.strip_between(cracks, prev[0], p, n, 0.03 * (1 - i / 12), (0.5, 0.5), lift=0.0)
            prev = (p, n)
    g = gold.object("EC_Gold", coll, mat)
    core = glow.object("EC_Core", coll, K.glow_material(EC_CORE))
    cr = cracks.object("EC_Cracks", coll, K.glow_material(EC_CRACK))
    return [body, g], {EC_CORE: [core], EC_CRACK: [cr]}


EGGS = {"BeginnerQiEgg": beginner_qi, "SpiritBreezeEgg": spirit_breeze, "ElementalCoreEgg": elemental_core}


def build(only=None):
    img, bands, mat = atlas()
    root = W.collection("Eggs")
    out = {}
    for egg_id, fn in EGGS.items():
        if only and egg_id not in only:
            continue
        coll = W.collection(egg_id, root)
        W.clear_collection(coll)
        body, glow = fn(coll, mat, bands)
        out[egg_id] = (body, glow, coll)
    return out, img


def export_all():
    """Builds and exports the three eggs."""
    eggs, img = build()
    for egg_id, (body, glow, coll) in eggs.items():
        K.export_egg(egg_id, body, glow, img, coll)
    return list(eggs)

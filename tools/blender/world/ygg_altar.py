"""Yggdrasil's Hatching Altar, on the prop atlas (start_props.STRIPS) like the shops: where every egg
carried home from a guardian's stands is hatched (PetService; GameConfig.HatchingAltar places it).

The idea: the World Tree cradles what is brought home to it. Five of its roots break out of the
ground round a round dais of pale stone and arch up over it, curling inward like the fingers of a
cupped hand. Under them, on a bronze stem, a jade lotus opens round a pool of golden Qi: the
cradle, where an egg is laid to hatch. Between the roots stand five seal stones of jade, one for
each island an egg can come from, each set with a gem in that island's glow (Yggdrasil, Jade
Grove, Ember Peak, Moonlit Isle, Origin Abyss).

Authored round its centre on the ground, its front toward +Z (where the steps and the prompt are).
CRADLE is where the egg is laid, PROMPT where the prompt stands, FX where the game adds its motes.

    import ygg_altar; objs = ygg_altar.build(); ygg_altar.export(objs)   # assets/world/Yggdrasil/Yggdrasil_Altar.fbx
"""
import math

import worldlib as W
import start_props as P
import ygg_props as YP

TAU = 2 * math.pi
TIER1, TIER2 = 0.9, 1.7          # the dais's two tops
R1, R2 = 11.0, 8.6               # their radii
POOL_Y = 4.15                    # the Qi pool's surface in the lotus
CRADLE = (0.0, POOL_Y, 0.0)
PROMPT = (0.0, 3.2, 3.2)
FX = [("Motes", (0.0, POOL_Y + 0.3, 0.0))]
SEALS = ["Yggdrasil", "Jade", "Ember", "Moonlit", "Origin"]   # round the rim from the front, between the roots
ROOT_BEARINGS = [TAU * (k + 0.5) / 5 + math.pi / 2 for k in range(5)]   # bearings (from +X toward +Z) of the five roots
SEAL_BEARINGS = [TAU * k / 5 + math.pi / 2 for k in range(5)]           # the front (+Z) seal first


def _polar(bearing, r, y):
    return (math.cos(bearing) * r, y, math.sin(bearing) * r)


def dais(mb, bands):
    """Two round tiers of pale stone, a bronze band round the upper edge, steps at the front."""
    mb.lathe([(0.0, TIER2, 1.0), (R2 - 0.3, TIER2, 1.0), (R2, TIER2 - 0.25, 0.85), (R2, TIER1, 0.6)], 40, bands[P.PALE], cap_top=False)
    mb.lathe([(R2, TIER1, 1.0), (R1 - 0.3, TIER1, 1.0), (R1, TIER1 - 0.25, 0.85), (R1, -0.6, 0.55)], 48, bands[P.PALE], cap_top=False)
    mb.lathe([(R2 + 0.12, TIER2 - 0.05, 1.0), (R2 + 0.12, TIER2 - 0.45, 0.7)], 40, bands[P.BRONZE], cap_top=False)
    for k, (z, y, w) in enumerate(((R1 + 1.2, 0.3, 6.0), (R1 + 2.4, -0.15, 6.8))):
        mb.box((0, y, z), (w, 0.9, 1.4), bands[P.PALE], u=0.4, top_shade=0.95, side_shade=0.65)


def cradle(mb, bands):
    """The bronze stem and the jade lotus round the pool."""
    mb.lathe([(1.4, 2.6, 1.0), (0.9, 2.3, 0.85), (0.7, TIER2 + 0.3, 0.7), (1.6, TIER2, 0.6)], 16, bands[P.BRONZE], cap_top=False)
    # the lotus: two rings of pointed petals opening round the pool, the inner ring offset
    mb.lathe([(2.6, POOL_Y - 0.2, 0.6), (1.6, 3.2, 0.7), (1.3, 2.5, 0.6)], 24, bands[P.JADE], cap_top=False)    # its heart, under the pool
    for ring, (count, base_r, length, width, rise, phase) in enumerate(((9, 2.0, 3.3, 2.7, 0.6, 0.0), (9, 1.7, 2.8, 2.3, 0.85, 0.5))):
        for k in range(count):
            petal(mb, bands[P.JADE], TAU * (k + phase) / count, base_r, 2.7 + 0.35 * ring, length, width, rise)


def petal(mb, band, bearing, base_r, base_y, length, width, rise):
    """A lotus petal: from its base on the heart out and up to a point, cupped, both faces."""
    out = (math.cos(bearing), 0.0, math.sin(bearing))
    side = (-math.sin(bearing), 0.0, math.cos(bearing))
    steps = 6
    rows = []
    for i in range(steps + 1):
        t = i / steps
        reach = base_r + length * t * (1 - 0.25 * t)
        y = base_y + length * rise * t ** 1.4
        half = width * 0.5 * math.sin(math.pi * min(1.0, 0.15 + t * 0.95)) ** 0.5 * (1 - t ** 5)      # broad, rounding to a soft point
        cup = 0.35 * width * (1 - (1 - t) ** 2) * 0.5
        row = []
        for f in (-1.0, 0.0, 1.0):
            lift = cup * (1 - f * f) * -1          # the middle dips: a cupped petal
            row.append((out[0] * reach + side[0] * half * f, y + lift + 0.12 * f * f, out[2] * reach + side[2] * half * f))
        rows.append(row)
    for i in range(steps):
        for j in range(2):
            quad = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
            shade = [0.55 + 0.45 * (i / steps)] * 2 + [0.55 + 0.45 * ((i + 1) / steps)] * 2
            P.oriented(mb, quad, (out[0] * -0.4, 1.0, out[2] * -0.4), band, 0.5, shade)
            P.oriented(mb, quad, (out[0] * 0.4, -1.0, out[2] * 0.4), band, 0.5, [0.45] * 4)


def roots(mb, bands):
    """Five roots of the World Tree breaking out round the dais and arching over it, gnarled, each
    curling in at its tip like a finger, a rootlet or two splitting off along it."""
    for k, b in enumerate(ROOT_BEARINGS):
        lean = 0.15 * math.sin(k * 2.1)
        kink = 0.35 * math.cos(k * 1.7)
        pts = [_polar(b, R1 + 1.8, -0.9), _polar(b + lean * 0.2, R1 - 0.2 + kink, 1.4), _polar(b + lean * 0.5, R2 - 0.2, 4.6 + kink),
               _polar(b + lean * 0.8, 6.8, 7.9), _polar(b + lean, 4.6, 9.9), _polar(b + lean * 1.2, 2.8, 10.2), _polar(b + lean * 1.3, 2.0, 9.2),
               _polar(b + lean * 1.25, 2.6, 8.6)]
        gnarl = lambda t, k=k: (1.75 * (1 - 0.8 * t ** 0.8)) * (1 + 0.12 * math.sin(t * 23 + k) * (1 - t))
        _tube(mb, pts, gnarl, 10, bands[P.BARK])
        # a rootlet splitting off along it, reaching down to the dais
        mid = _polar(b + lean * 0.5, R2 + 0.4, 4.0 + kink)
        side = 1 if k % 2 else -1
        _tube(mb, [mid, _polar(b + side * 0.16, R2 - 0.6, 2.8), _polar(b + side * 0.22, R2 - 1.6, TIER2 + 0.1)], lambda t: 0.6 * (1 - 0.7 * t),
              7, bands[P.BARK])
        # its foot spreading into the ground
        for sd in (-1, 1):
            foot = [_polar(b, R1 + 1.0, 0.2), _polar(b + sd * 0.12, R1 + 2.8, -0.4), _polar(b + sd * 0.2, R1 + 4.2, -0.9)]
            _tube(mb, foot, lambda t: 0.85 * (1 - 0.6 * t), 7, bands[P.BARK])


def _tube(mb, points, radius_fn, sides, band):
    """worldlib.mb_tube, kept off the band's top edge (as ygg_shops.tube)."""
    v0, v1 = band
    return W.mb_tube(mb, points, radius_fn, sides, (v0, v1 - 0.15 * (v1 - v0)), per=6)


def seals(mb, bands):
    """Five seal stones of jade round the upper tier's rim, each a hexagonal post with a bronze cap
    holding its gem's setting."""
    for b in SEAL_BEARINGS:
        x, _, z = _polar(b, R2 - 1.0, 0)
        mb.lathe([(0.75, 3.1, 1.0), (0.8, 2.9, 0.9), (0.8, TIER2 + 0.2, 0.7), (1.0, TIER2, 0.6)], 6, bands[P.JADE], centre=(x, 0, z),
                 phase=b, cap_top=False)
        mb.lathe([(0.0, 3.55, 1.0), (0.55, 3.45, 0.95), (0.95, 3.15, 0.8), (0.9, 3.0, 0.7)], 12, bands[P.BRONZE], centre=(x, 0, z),
                 cap_top=False)


def seal_gems(coll, mat, bands):
    """Each seal's gem, its own piece so the game can light it in its island's glow."""
    out = []
    for name, b in zip(SEALS, SEAL_BEARINGS):
        mb = W.MeshBuilder()
        x, _, z = _polar(b, R2 - 1.0, 0)
        mb.lathe([(0.0, 4.35, 1.0), (0.32, 4.0, 1.0), (0.42, 3.75, 1.0), (0.0, 3.45, 1.0)], 8, bands[P.PAPER], centre=(x, 0, z),
                 cap_top=False)
        out.append(mb.object("YG_AltarGem" + name, coll, mat))
    return out


def pool(coll, mat, bands):
    """The pool of golden Qi in the lotus."""
    mb = W.MeshBuilder()
    mb.lathe([(0.0, POOL_Y, 1.0), (2.45, POOL_Y, 1.0), (2.45, POOL_Y - 0.3, 1.0)], 32, bands[P.PAPER], cap_top=False)
    return mb.object("YG_AltarPool", coll, mat)


def altar(coll, mat, bands):
    mb = W.MeshBuilder()
    dais(mb, bands)
    cradle(mb, bands)
    seals(mb, bands)
    return mb.object("YG_Altar", coll, mat)


def altar_roots(coll, mat, bands):
    mb = W.MeshBuilder()
    roots(mb, bands)
    return mb.object("YG_AltarRoots", coll, mat)


def build():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Altar", W.collection("Yggdrasil"))
    W.clear_collection(coll)
    return [altar(coll, mat, bands), altar_roots(coll, mat, bands), pool(coll, mat, bands)] + seal_gems(coll, mat, bands)


def export(objs):
    """assets/world/Yggdrasil/Yggdrasil_Altar.fbx (WB.storeKit("Yggdrasil", <import>, "YG_AltarAnchor"))."""
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Altar.fbx"
    W.export_batch(objs, path, image=YP.atlas_image(), anchor_name="YG_AltarAnchor")
    return path

"""Ember Peak eggs (after the 15-egg concept sheet), built like the Jade Grove eggs: high-detail
pieces with procedural shaders (egg_hi.py) baked onto a game mesh (egg_bake.py), glowing parts
kept as separate Neon pieces.

- Inferno Egg: plates of dark volcanic rock with molten lava glowing in the seams between them
  and in thin veins across them, their edges heated red; chunks of rock breaking away from its
  right shoulder and flying off up and out.
- Magma Heart Egg: a core of cut crimson crystal grown through with crystal shards: a tall crown
  crystal on top, shards flaring outward and upward round it, the largest at the base, with
  ember-hot chips glowing between them.
- Phoenix Ash Egg: a crimson shell veined with molten gold, wrapped in two wings of flame
  feathers that sweep up and curl forward round it, a crest of feathers on its crown, and a
  glowing phoenix flame on its front in a gold rim.

    import eggs_ember as E
    E.build()           # the high-detail eggs, in collections InfernoEggHi, ...
    E.export_all()      # bake and export: assets/eggs/<EggId>.fbx plus its maps
"""
import math
import random

import bmesh
import bpy

import egg_bake as B
import egg_hi as Hm
import egg_kit as K
import eggs_jade as J

W = K.W
V = K.V
TAU = K.TAU
H, R = K.H, K.R
on, normal_at, surface_path, uv_of = J.on, J.normal_at, J.surface_path, J.uv_of


def rock(hi, centre, size, seed, mat=0, stretch=(1.0, 1.0, 1.0), n=14):
    """An irregular chunk of rock: the convex hull of jittered points round `centre`."""
    rnd = random.Random(seed)
    c = V(centre)
    pts = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        a = golden * i + rnd.uniform(-0.3, 0.3)
        d = V((math.cos(a) * r * stretch[0], y * stretch[1], math.sin(a) * r * stretch[2]))
        pts.append(c + d * size * rnd.uniform(0.7, 1.15))
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    idx = {v: hi.v(v.co) for v in bm.verts if v.link_faces}
    for f in bm.faces:
        out = f.calc_center_median() - c
        hi.facing([idx[v] for v in f.verts], [(0, 0), (1, 0), (1, 1)][:len(f.verts)] + [(0, 1)] * (len(f.verts) - 3), tuple(out), mat)
    bm.free()


# ---------- Inferno Egg ----------
IN_LAVA = "ff4a12"     # molten lava in the seams


def inferno(coll, M):
    mb = W.MeshBuilder()
    sites = K.surface_sites(24, seed=81) + [K.egg_point(0.0, 0.0)[0]]
    K.crystal_plates(mb, (0.5, 0.5), sites, gap=0.93, lift=(0.0, 0.03), tilt=0.1, depth=0.12, seed=82, peak=0.09)
    plates = mb.object("IN_Plates", coll, M["obsidian"])
    plates["keep"] = True
    core = W.MeshBuilder()
    K.shell(core, (0.5, 0.5), nu=32, nv=20, offset=-0.06)
    lava = core.object("IN_Lava", coll, K.glow_material(IN_LAVA))
    # chunks breaking away from the right shoulder: small ones close to it, larger ones flung
    # further out and up
    rocks = Hm.Hi()
    rnd = random.Random(83)
    for k in range(11):
        t = k / 10
        # an arc off the right shoulder: out to the right first, then rising, scattered
        u = 0.22 + rnd.uniform(-0.04, 0.04)
        v = 0.62 + rnd.uniform(-0.12, 0.12)
        p, n = K.egg_point(u, v, offset=0.16)
        p = p + V((0.95 * t + rnd.uniform(-0.12, 0.12), 0.7 * t * t + rnd.uniform(-0.15, 0.2), rnd.uniform(-0.25, 0.25) * t))
        rock(rocks, p, 0.09 + 0.13 * t + rnd.uniform(-0.02, 0.04), seed=84 + k, stretch=(1.0, 0.75 + 0.45 * rnd.random(), 0.85))
    chunks = rocks.object("IN_Chunks", coll, [M["obsidian"]], smooth=False, weld=0)
    chunks["keep"] = True
    return [plates, chunks], {IN_LAVA: [lava]}


# ---------- Magma Heart Egg ----------
MH_CORE = "ff3214"     # the crimson core glowing through the seams
MH_EMBER = "ff6a12"    # ember-hot chips between the shards


def magma_heart(coll, M):
    mb = W.MeshBuilder()
    sites = K.surface_sites(30, seed=91) + [K.egg_point(0.0, 0.0)[0]]
    K.crystal_plates(mb, (0.5, 0.5), sites, gap=0.95, lift=(0.0, 0.02), tilt=0.08, depth=0.1, seed=92, peak=0.1)
    plates = mb.object("MH_Plates", coll, M["crimson"])
    plates["keep"] = True
    core = W.MeshBuilder()
    K.shell(core, (0.5, 0.5), nu=32, nv=20, offset=-0.05)
    glow = core.object("MH_Core", coll, K.glow_material(MH_CORE))
    shards = W.MeshBuilder()
    rnd = random.Random(93)
    band = (0.5, 0.5)
    # rings of shards: (count, v, length, width, how far they lean out, phase)
    rings = ((10, 0.13, 1.4, 0.27, 1.1, 0.0), (9, 0.3, 1.15, 0.23, 0.75, 0.5), (8, 0.5, 0.9, 0.19, 0.5, 0.2), (6, 0.72, 0.72, 0.15, 0.32, 0.7))
    for count, v, length, width, lean, phase in rings:
        for k in range(count):
            u = (k + phase) / count + rnd.uniform(-0.02, 0.02)
            front = abs(((u + 0.5) % 1.0) - 0.5)
            if v > 0.3 and front < 0.07:
                continue              # leave the front of the core open
            p, n = K.egg_point(u, v, offset=-0.1)
            out = V((n.x, 0, n.z)).normalized()
            d = (out * lean + V((0, 1, 0))).normalized()
            K.shard(shards, p, d, length * rnd.uniform(0.85, 1.15), width * rnd.uniform(0.85, 1.15), band, seed=94 + k + int(v * 100), sides=5)
    # the crown crystal and its four companions
    K.shard(shards, K.egg_point(0, 0.93, offset=-0.2)[0], (0.02, 1, 0.03), 1.5, 0.24, band, seed=990, sides=6)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        d = (V((math.sin(a), 0, math.cos(a))) * 0.35 + V((0, 1, 0))).normalized()
        K.shard(shards, K.egg_point(k / 4 + 0.06, 0.86, offset=-0.1)[0], d, 0.9, 0.16, band, seed=991 + k, sides=5)
    crystals = shards.object("MH_Shards", coll, M["crimson"])
    crystals["keep"] = True
    # ember-hot chips nestled between the base shards
    embers = W.MeshBuilder()
    for k in range(8):
        u = (k + 0.5) / 8
        p, n = K.egg_point(u, 0.1, offset=0.05)
        out = V((n.x, 0, n.z)).normalized()
        K.shard(embers, p, (out * 0.9 + V((0, 1, 0))).normalized(), 0.32, 0.07, band, seed=1100 + k, sides=4)
    ember = embers.object("MH_Embers", coll, K.glow_material(MH_EMBER))
    return [plates, crystals], {MH_CORE: [glow], MH_EMBER: [ember]}


# ---------- Phoenix Ash Egg ----------
PA_FLAME = "ff5a14"    # the phoenix flame on the front
PA_HEART = "ffa21e"    # its hot heart


def flame_outline(cu, cv, w, h, n_side=10):
    """A phoenix flame in (u, v): a tall central tongue between two tongues curling out and up from
    its shoulders, closed along a rounded base. Star-shaped from (cu, cv - 0.25 h)."""
    pts = []

    def tongue(x0, y0, x1, y1, bend, k):
        return [(x0 + (x1 - x0) * t + bend * math.sin(math.pi * t), y0 + (y1 - y0) * t) for t in (i / k for i in range(k + 1))]
    # base, left side, left tongue, central tongue, right tongue, right side
    base_l, base_r = (-0.45, -0.5), (0.45, -0.5)
    path = [(-0.0, -0.62)]
    path += [base_l, (-0.55, -0.15)]
    path += tongue(-0.55, -0.15, -0.95, 0.55, -0.12, 4)[1:]                 # up the left tongue
    path += tongue(-0.95, 0.55, -0.3, 0.05, 0.1, 4)[1:]                     # down its inner edge
    path += tongue(-0.3, 0.05, 0.0, 1.0, -0.08, 5)[1:]                      # up the central tongue
    path += tongue(0.0, 1.0, 0.3, 0.05, -0.08, 5)[1:]                       # and down
    path += tongue(0.3, 0.05, 0.95, 0.55, 0.1, 4)[1:]                       # up the right tongue
    path += tongue(0.95, 0.55, 0.55, -0.15, -0.12, 4)[1:]                   # down its outer edge
    path += [base_r]
    for x, y in path:
        pts.append((cu + x * w, cv + y * h))
    return pts


def wing(hi, side, mat, rnd):
    """Feathers rooted along the egg's side sweeping up and out like a wing raised over it: the
    top ones nearly upright and longest, the lower ones reaching out sideways, their tips curling
    out like tongues of flame. Three layers, the inner ones shorter."""
    layers = ((8, 1.35, 0.17, 0.05, -0.05), (7, 1.0, 0.15, 0.1, -0.02), (6, 0.7, 0.13, 0.15, 0.01))
    for layer, (count, length, width, lift, back) in enumerate(layers):
        for k in range(count):
            t = k / (count - 1)                    # 0 at the bottom of the wing, 1 at the top
            v = 0.3 + 0.42 * t
            u = (side * (0.21 + 0.025 * layer) + back * side) % 1.0
            p, n = K.egg_point(u, v, offset=lift)
            phi = math.radians(78 - 66 * t)        # from the vertical: the top feathers rise
            d = V((side * math.sin(phi), math.cos(phi), -0.25)).normalized()
            size = length * (0.62 + 0.48 * t) * rnd.uniform(0.92, 1.08)
            Hm.leaf(hi, p, d, V((side * -0.35, 0.1, 1)), size, width * (0.85 + 0.3 * t), mat, fold=0.14, curl=-0.22,
                    twist=side * rnd.uniform(0.15, 0.4), steps=12, across=4, shape=1.1)


def phoenix_ash(coll, M):
    mb = Hm.Hi()
    shell_mb = W.MeshBuilder()
    K.shell(shell_mb, (0.5, 0.5), nu=48, nv=32)
    shell = shell_mb.object("PA_Shell", coll, M["embershell"], smooth=True)
    shell["keep"] = True
    rnd = random.Random(101)
    feathers = Hm.Hi()
    for side in (1, -1):
        wing(feathers, side, 0, rnd)
    # the crest on the crown: feathers fanning up and back
    for k in range(6):
        a = math.radians(-50 + 100 * k / 5)
        p = on(0.5 + 0.05 * math.sin(a), 0.9, 0.0)
        d = V((math.sin(a) * 0.5, 1.0, -0.45)).normalized()
        Hm.leaf(feathers, p, d, V((0, 0.3, 1)), rnd.uniform(0.75, 0.95), 0.11, 0, fold=0.1, curl=-0.3, twist=rnd.uniform(-0.3, 0.3),
                steps=10, across=4, shape=1.1)
    # tail feathers sweeping out low at the back
    for k in range(5):
        a = math.radians(-40 + 80 * k / 4)
        p = on(0.5 + 0.06 * math.sin(a), 0.22, 0.04)
        d = V((math.sin(a) * 0.8, -0.15, -1.0)).normalized()
        Hm.leaf(feathers, p, d, V((0, 1, 0)), rnd.uniform(0.7, 0.85), 0.12, 0, fold=0.1, curl=0.3, steps=10, across=4, shape=1.1)
    feathers_obj = Hm.solidify(feathers.object("PA_Feathers", coll, [M["feather"]]), 0.014)
    feathers_obj["sheet"] = True
    # the phoenix flame on the front in a gold rim
    outline = flame_outline(0.0, 0.47, 0.09, 0.22)
    centre = on(0.0, 0.47 - 0.05, 0.08)
    cn = normal_at(0.0, 0.42)
    flame, heart, gold = Hm.Hi(), Hm.Hi(), Hm.Hi()
    rim = [flame.v(on(u, v, 0.07)) for u, v in outline]
    c = flame.v(centre + cn * 0.03)
    for i in range(len(rim)):
        flame.facing([rim[i], rim[(i + 1) % len(rim)], c], [(0, 0)] * 3, cn)
    inner = flame_outline(0.0, 0.45, 0.045, 0.11)
    hrim = [heart.v(on(u, v, 0.1)) for u, v in inner]
    hc = heart.v(on(0.0, 0.42, 0.12))
    for i in range(len(hrim)):
        heart.facing([hrim[i], hrim[(i + 1) % len(hrim)], hc], [(0, 0)] * 3, cn)
    ring = [on(u, v, 0.08) for u, v in outline]
    Hm.htube(gold, ring + ring[:1], lambda t: 0.018, sides=7, per=2, uv_scale=3.0, tip=False)
    g = gold.object("PA_Gold", coll, [M["gold"]])
    fl = flame.object("PA_Flame", coll, [K.glow_material(PA_FLAME)], smooth=False)
    ht = heart.object("PA_Heart", coll, [K.glow_material(PA_HEART)], smooth=False)
    return [shell, feathers_obj, g], {PA_FLAME: [fl], PA_HEART: [ht]}


EGGS = {"InfernoEgg": (inferno, 12000), "MagmaHeartEgg": (magma_heart, 14000), "PhoenixAshEgg": (phoenix_ash, 15000)}


def materials():
    return {
        "obsidian": Hm.mat_obsidian(),
        # linear colours: crimson on screen is deep in linear terms
        "crimson": Hm.mat_crystal("EggCrimsonCrystal", stops=[(0.0, (0.07, 0.0, 0.004)), (0.35, (0.18, 0.004, 0.01)),
                                                              (0.7, (0.38, 0.01, 0.018)), (1.0, (0.65, 0.04, 0.03))], vein=(1.0, 0.32, 0.03), crown=(0.85, 0.1, 0.04)),
        "embershell": Hm.mat_obsidian("EggEmberShell", tones=[(0.0, (0.16, 0.006, 0.004)), (1.0, (0.26, 0.012, 0.008))],
                                      vein=(1.0, 0.62, 0.12), vein_hot=(1.0, 0.88, 0.45), heat=(0.85, 0.25, 0.04)),
        "feather": Hm.mat_feather(base=(0.38, 0.008, 0.003), mid=(0.92, 0.1, 0.008), tip=(1.0, 0.42, 0.025)),
        "gold": Hm.mat_gold(),
    }


def build(only=None):
    M = materials()
    root = W.collection("EggsHi")
    out = {}
    for egg_id, (fn, budget) in EGGS.items():
        if only and egg_id not in only:
            continue
        coll = W.collection(egg_id + "Hi", root)
        W.clear_collection(coll)
        hi, glow = fn(coll, M)
        out[egg_id] = (hi, glow, coll, budget)
    return out


def export_all(only=None):
    report = {}
    for egg_id, (hi, glow, coll, budget) in build(only).items():
        old = bpy.data.objects.get(egg_id + "_Body")
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        low = B.make_low(egg_id, hi, coll, budget)
        B.bake(egg_id, hi, low)
        parts = B.export(egg_id, low, glow, coll)
        report[egg_id] = (B.tris(low), [p.name for p in parts])
    return report

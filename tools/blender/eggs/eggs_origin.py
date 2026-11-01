"""Origin Abyss eggs, built like the Moonlit Isle eggs (eggs_moon.py): high-detail pieces with
procedural shaders (egg_hi.py) baked onto a game mesh (egg_bake.py), glowing parts kept as
separate Neon pieces. Each is its own form, after its name and the pets it hatches:

- Forbidden Origin Egg: the sealed egg. Ancient seal-stone ringed with bands of glowing violet
  seal-script glyphs, bound by two bronze chains crossing over its front, locked where they cross
  by a bronze seal medallion with a glowing rune.
- Void Rift Egg: the egg torn open. A shell of black void glass split by a jagged rift down its
  front, the torn edges glowing blue; through it, the hollow inside is a starry void with a
  glowing heart floating in it; fragments of the shell drift just off the tear.
- Primordial Abyss Egg: the first egg. Banded primordial stone, a great fossil ammonite coiled
  on its front with magenta light in its spiral seam and its mouth, a bronze clockwork belt of
  gear teeth round its base and two small gears set in its shoulders (time: the Eternal
  Clockwork Dragon).

The shrine's thorn branches curve up close round each egg: anything on the shell stays within
about 0.2 egg units of it below the egg's middle (measured by raycasts on the placed pedestal).

    import eggs_origin as E
    E.build()           # the high-detail eggs, in collections ForbiddenOriginEggHi, ...
    E.export_all()      # bake and export: assets/eggs/<EggId>.fbx plus its maps
"""
import math
import random

import bpy

import egg_bake as B
import egg_hi as Hm
import egg_kit as K
import eggs_jade as J
import eggs_moon as Mo

W = K.W
V = K.V
TAU = K.TAU
H, R = K.H, K.R
on, normal_at = J.on, J.normal_at
sphere, star, uv_path = Mo.sphere, Mo.star, Mo.uv_path


def tube(hi, pts, r, sides=6, mat=0, tip=False):
    return Hm.htube(hi, pts, lambda t: r, sides=sides, per=1, uv_scale=3.0, tip=tip, wobble=0.0, mat=mat)


def box(hi, centre, normal, along, size, mat=0):
    """A small block on a surface: `size` (across, along, out) on the frame of `normal` and `along`."""
    n = V(normal).normalized()
    a = V(along)
    a = (a - n * a.dot(n)).normalized()
    s = a.cross(n).normalized()
    c = V(centre)
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    corner = {}
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                corner[(i, j, k)] = hi.v(c + s * sx * i + a * sy * j + n * sz * k)
    for axis, vec in ((0, s), (1, a), (2, n)):
        for sign in (-1, 1):
            quad = []
            for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                key = [0, 0, 0]
                key[axis] = sign
                others = [x for x in range(3) if x != axis]
                key[others[0]], key[others[1]] = p, q
                quad.append(corner[tuple(key)])
            hi.facing(quad, [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(vec * sign), mat)


def grid(hi, u0, u1, v0, v1, off, nu, nv, inward=False, mat=0):
    """A patch of the egg's surface (u0..u1, v0..v1) `off` above it, facing out (or in)."""
    rows = [[hi.v(on(u0 + (u1 - u0) * i / nu, v0 + (v1 - v0) * j / nv, off)) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            n = normal_at(u0 + (u1 - u0) * (i + 0.5) / nu, v0 + (v1 - v0) * (j + 0.5) / nv)
            hi.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]],
                      [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)],
                      tuple(-n if inward else n), mat)


# ---------- Forbidden Origin Egg ----------
FO_RUNE = "643cff"     # the seal-script glyphs and the seal's rune (Neon turns b04fff and even 7a3cff pink)

# strokes of seal-script glyphs, in a unit cell
STROKES = [
    [(0.5, 0.08), (0.5, 0.92)], [(0.1, 0.5), (0.9, 0.5)], [(0.12, 0.88), (0.88, 0.88)], [(0.12, 0.12), (0.88, 0.12)],
    [(0.15, 0.12), (0.15, 0.88)], [(0.85, 0.12), (0.85, 0.88)], [(0.2, 0.82), (0.72, 0.82), (0.72, 0.3), (0.45, 0.18)],
    [(0.2, 0.68), (0.5, 0.38), (0.8, 0.68)], [(0.3, 0.3), (0.3, 0.62), (0.7, 0.62), (0.7, 0.3), (0.3, 0.3)],
    [(0.15, 0.5), (0.5, 0.85), (0.85, 0.5)],
]


def glyph(hi, uc, vc, width_u, height_v, rnd, off, r, strokes=None):
    for st in strokes or rnd.sample(STROKES, rnd.randint(3, 4)):
        pts = [(uc + (x - 0.5) * width_u, vc + (y - 0.5) * height_v) for x, y in st]
        tube(hi, uv_path(pts, off, per=4), r, sides=5)


def chain_path(sign, n=240):
    """A chain round the egg: crossing the other at its front (and back), rising over one shoulder."""
    return [(i / n, 0.5 + sign * 0.2 * math.sin(TAU * i / n)) for i in range(n + 1)]


def chain(hi, sign, rnd, off=0.034, spacing=0.1, mat=0):
    """Oval links along the path, each turned a quarter from the last."""
    path = uv_path(chain_path(sign), off, per=1)
    dist = [0.0]
    for a, b in zip(path, path[1:]):
        dist.append(dist[-1] + (b - a).length)
    total = dist[-1]
    count = int(total / spacing)
    k = 0
    for i in range(count):
        d = (i + 0.5) * total / count
        while dist[k + 1] < d:
            k += 1
        f = (d - dist[k]) / max(1e-9, dist[k + 1] - dist[k])
        c = path[k].lerp(path[k + 1], f)
        t = (path[k + 1] - path[k]).normalized()
        u_, v_ = J.uv_of(c)
        n = normal_at(u_, v_)
        side = t.cross(n).normalized()
        across = n if i % 2 == 0 else side          # alternate links stand up / lie flat
        loop = [c + t * math.cos(TAU * j / 10) * 0.058 + across * math.sin(TAU * j / 10) * 0.032 for j in range(10)]
        tube(hi, loop + loop[:2], 0.012, sides=5, mat=mat)


def forbidden_origin(coll, M):
    mb = W.MeshBuilder()
    K.shell(mb, (0.5, 0.5), nu=64, nv=40)
    shell = mb.object("FO_Shell", coll, M["sealstone"], smooth=True)
    shell["keep"] = True
    rnd = random.Random(131)
    runes = Hm.Hi()
    # two bands of seal script all the way round, every glyph its own
    for vc, count, h in ((0.27, 20, 0.06), (0.72, 15, 0.055)):
        for k in range(count):
            glyph(runes, (k + 0.5) / count, vc, 0.66 / count, h, rnd, 0.016, 0.0095)
    bronze = Hm.Hi()
    for sign in (1, -1):
        chain(bronze, sign, rnd)
    # the seal where they cross: a domed bronze medallion in a ring, a rune glowing on its face
    sn = normal_at(0.0, 0.5)
    sc = on(0.0, 0.5, 0.075)
    ring = [on(0.022 * math.sin(TAU * i / 28), 0.5 + 0.034 * math.cos(TAU * i / 28), 0.055) for i in range(28)]
    tube(bronze, ring + ring[:2], 0.03, sides=8)
    face = [on(0.021 * math.sin(TAU * i / 28), 0.5 + 0.032 * math.cos(TAU * i / 28), 0.07) for i in range(28)]
    rim = [bronze.v(p) for p in face]
    dome = bronze.v(sc + sn * 0.02)
    for i in range(28):
        bronze.facing([rim[i], rim[(i + 1) % 28], dome], [(0, 0), (1, 0), (0.5, 1)], tuple(sn))
    glyph(runes, 0.0, 0.5, 0.024, 0.04, rnd, 0.1, 0.009,
          strokes=[[(0.5, 0.05), (0.5, 0.95)], [(0.15, 0.65), (0.5, 0.35), (0.85, 0.65)], [(0.2, 0.2), (0.8, 0.2)]])
    b = bronze.object("FO_Bronze", coll, [M["bronze"]])
    g = runes.object("FO_Runes", coll, [K.glow_material(FO_RUNE)], smooth=False)
    return [shell, b], {FO_RUNE: [g]}


# ---------- Void Rift Egg ----------
VR_LIGHT = "3c64ff"    # the rift's torn edges and the heart inside (a deeper blue: Neon washed 646eff to lavender)
RIFT_V = (0.13, 0.9)
DEPTH = 0.09           # the shell's thickness at the tear


def rift(v):
    """The tear's left and right edges (u) at height v, or None where the shell is whole. It runs
    from low on the egg's right to high on its left, gaping in the middle, its edges jagged."""
    v0, v1 = RIFT_V
    if v <= v0 or v >= v1:
        return None
    t = (v - v0) / (v1 - v0)
    uc = 0.075 - 0.16 * t
    w = 0.08 * math.sin(math.pi * t) ** 0.75
    jag = lambda side: w * 0.4 * (0.6 * math.sin(t * 43 + side * 2.1) + 0.4 * math.sin(t * 101 + side * 4.7))
    return uc - w - jag(1), uc + w + jag(-1)


def edges(v):
    e = rift(v)
    if e is None:
        v0, v1 = RIFT_V
        t = 0.0 if v <= v0 else 1.0
        uc = 0.075 - 0.16 * t
        return uc, uc
    return e


def shard_piece(hi, u, v, lift, rnd, thick=0.03):
    """A jagged fragment of shell: an irregular five- to seven-sided piece of the surface lifted
    `lift` off it, with a back and edges, so it reads as broken glass rather than a tile."""
    n_pts = rnd.randint(5, 7)
    outline = []
    for k in range(n_pts):
        a = TAU * k / n_pts + rnd.uniform(-0.3, 0.3)
        rr = rnd.uniform(0.45, 1.0)
        outline.append((u + math.cos(a) * rr * 0.022, v + math.sin(a) * rr * 0.03))
    n = normal_at(u, v)
    front = [hi.v(on(pu, pv, lift)) for pu, pv in outline]
    back = [hi.v(on(pu, pv, lift - thick)) for pu, pv in outline]
    cf, cb = hi.v(on(u, v, lift + 0.006)), hi.v(on(u, v, lift - thick))
    for k in range(n_pts):
        j = (k + 1) % n_pts
        hi.facing([front[k], front[j], cf], [(0, 0), (1, 0), (0.5, 1)], tuple(n))
        hi.facing([back[j], back[k], cb], [(0, 0), (1, 0), (0.5, 1)], tuple(-n))
        side = on(*outline[k], lift) + on(*outline[j], lift) - on(u, v, lift) * 2
        hi.facing([front[k], back[k], back[j], front[j]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(side))


def void_rift(coll, M):
    nu, nv = 80, 52            # the shell is kept whole at this resolution: the game mesh stays under Roblox's 20k triangles
    glass, cavity, light = Hm.Hi(), Hm.Hi(), Hm.Hi()
    rows, inner = [], []
    for j in range(nv + 1):
        v = j / nv
        ul, ur = edges(v)
        us = [ur + (ul + 1.0 - ur) * i / nu for i in range(nu + 1)]     # from the right edge round the back to the left
        rows.append([glass.v(on(u, v, 0.0)) for u in us])
        inner.append([cavity.v(on(u, v, -DEPTH)) for u in us])
    for j in range(nv):
        v = (j + 0.5) / nv
        for i in range(nu):
            u = edges(v)[1] + (edges(v)[0] + 1.0 - edges(v)[1]) * (i + 0.5) / nu
            n = normal_at(u, v)
            glass.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(n))
            cavity.facing([inner[j][i], inner[j][i + 1], inner[j + 1][i + 1], inner[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(-n))
    # the torn edges: walls from the surface down to the cavity, glowing
    for j in range(nv):
        va, vb = j / nv, (j + 1) / nv
        if rift(va) is None and rift(vb) is None:
            continue
        for side in (0, 1):
            ua, ub = edges(va)[side], edges(vb)[side]
            quad = [light.v(on(ua, va, 0.004)), light.v(on(ub, vb, 0.004)), light.v(on(ub, vb, -DEPTH - 0.004)), light.v(on(ua, va, -DEPTH - 0.004))]
            mid_v = (va + vb) / 2
            centre = sum(edges(mid_v)) / 2
            facing = on(centre, mid_v) - on((ua + ub) / 2, mid_v)
            light.facing(quad, [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(facing))
    sh = glass.object("VR_Shell", coll, [M["voidglass"]])
    sh["keep"] = True
    cv = cavity.object("VR_Void", coll, [M["void"]])   # seen only through the tear: decimated
    # its heart, floating in the void
    sphere(light, V((0.0, H * 0.5, -0.1)), 0.17)
    # fragments of shell drifting off the tear
    frags = Hm.Hi()
    rnd = random.Random(141)
    for k, (t, side, lift) in enumerate(((0.22, 1, 0.14), (0.38, 0, 0.2), (0.55, 1, 0.22), (0.7, 0, 0.17), (0.84, 1, 0.12))):
        v = RIFT_V[0] + (RIFT_V[1] - RIFT_V[0]) * t
        ul, ur = edges(v)
        u = (ur + 0.028) if side else (ul - 0.028)
        shard_piece(frags, u, v, lift, rnd)
    fr = frags.object("VR_Fragments", coll, [M["voidglass"]], smooth=False)
    fr["keep"] = True
    li = light.object("VR_Light", coll, [K.glow_material(VR_LIGHT)], smooth=False)
    return [sh, cv, fr], {VR_LIGHT: [li]}


# ---------- Primordial Abyss Egg ----------
PA_SEAM = "ff3cb4"     # the light in the ammonite's seam and mouth, and the gears' hubs


def surface_uv(x, y, v_centre=0.5):
    """A point on the front given in units across (x) and up (y) from (u 0, v_centre)."""
    v = v_centre + y / 4.2
    radius = K.egg_point(0.25, v)[0].x
    return x / (TAU * radius), v


def ammonite(hi, seam, mat_shell=0):
    """A fossil ammonite in relief: a coil whose tube widens as it winds out, half sunk in the
    stone; a glowing line in the seam between its whorls and a glowing mouth."""
    turns, r_out, r_in = 2.5, 0.5, 0.035
    theta_max = turns * TAU
    b = math.log(r_out / r_in) / theta_max
    steps = 150
    coil, radii, seam_pts = [], [], []
    for i in range(steps + 1):
        th = theta_max * i / steps
        r = r_in * math.exp(b * th)
        tr = 0.31 * r
        x, y = math.cos(th) * r, math.sin(th) * r
        u, v = surface_uv(x, y)
        coil.append(on(u, v, tr * 0.45))
        radii.append(tr)
        if th > TAU:
            ri = r - tr
            su, sv = surface_uv(math.cos(th) * ri, math.sin(th) * ri)
            seam_pts.append(on(su, sv, 0.012))
    Hm.htube(hi, coil, lambda t: radii[min(steps, int(round(t * steps)))], sides=12, per=1, uv_scale=22.0, tip=False, wobble=0.0, mat=mat_shell)
    tube(seam, seam_pts, 0.012, sides=5)
    # the mouth: a glowing disc closing the open end of the coil
    end, before = coil[-1], coil[-2]
    axis = (end - before).normalized()
    ref = V((0, 0, 1)) if abs(axis.z) < 0.9 else V((1, 0, 0))
    s = axis.cross(ref).normalized()
    t2 = axis.cross(s).normalized()
    rim = [seam.v(end + (s * math.cos(TAU * k / 16) + t2 * math.sin(TAU * k / 16)) * radii[-1] * 0.92) for k in range(16)]
    c = seam.v(end + axis * 0.004)
    for k in range(16):
        seam.facing([rim[k], rim[(k + 1) % 16], c], [(0, 0), (1, 0), (0.5, 1)], tuple(axis))


def gear(hi, glow, uc, vc, radius_u, radius_v, teeth=10):
    """A small gear set in the shell: a toothed ring, four spokes and a glowing hub."""
    ring = [on(uc + radius_u * math.sin(TAU * i / 32), vc + radius_v * math.cos(TAU * i / 32), 0.022) for i in range(32)]
    tube(hi, ring + ring[:2], 0.016, sides=6)
    for k in range(teeth):
        a = TAU * k / teeth
        uu, vv = uc + radius_u * 1.18 * math.sin(a), vc + radius_v * 1.18 * math.cos(a)
        p = on(uu, vv, 0.022)
        radial = p - on(uc, vc, 0.022)
        box(hi, p, normal_at(uu, vv), radial, (0.035, 0.04, 0.03))
    for k in range(4):
        a = TAU * k / 4 + 0.4
        tube(hi, uv_path([(uc, vc), (uc + radius_u * math.sin(a), vc + radius_v * math.cos(a))], 0.022, per=4), 0.01, sides=5)
    sphere(glow, on(uc, vc, 0.022), 0.03)


def primordial_abyss(coll, M):
    mb = W.MeshBuilder()
    K.shell(mb, (0.5, 0.5), nu=64, nv=40)
    shell = mb.object("PA_Shell", coll, M["strata"], smooth=True)
    shell["keep"] = True
    fossil, seam, bronze = Hm.Hi(), Hm.Hi(), Hm.Hi()
    ammonite(fossil, seam)
    # the clockwork belt round its base: a band between two rims, gear teeth standing out of it
    grid(bronze, 0.0, 1.0, 0.225, 0.265, 0.016, 96, 2)
    for v in (0.222, 0.268):
        rim = [on(i / 96, v, 0.02) for i in range(96)]
        tube(bronze, rim + rim[:2], 0.016, sides=6)
    for k in range(40):
        u = (k + 0.5) / 40
        box(bronze, on(u, 0.245, 0.03), normal_at(u, 0.245), (0, 1, 0), (0.05, 0.03, 0.05))
    for side in (-1, 1):
        gear(bronze, seam, side * 0.2, 0.66, 0.026, 0.03)
    fo = fossil.object("PA_Fossil", coll, [M["fossil"]])
    fo["keep"] = True
    br = bronze.object("PA_Bronze", coll, [M["bronze"]])
    sm = seam.object("PA_Seam", coll, [K.glow_material(PA_SEAM)], smooth=False)
    return [shell, fo, br], {PA_SEAM: [sm]}


EGGS = {"ForbiddenOriginEgg": (forbidden_origin, 17000), "VoidRiftEgg": (void_rift, 16000), "PrimordialAbyssEgg": (primordial_abyss, 16000)}


def materials():
    return {
        "sealstone": Hm.mat_sealstone(),
        "bronze": Hm.mat_bronze(),
        "voidglass": Hm.mat_voidglass(),
        "void": Hm.mat_nightsky("EggVoid", sky=[(0.0, (0.0, 0.0, 0.006)), (0.5, (0.002, 0.006, 0.03)), (1.0, (0.004, 0.01, 0.05))],
                                nebula=[(0.35, (0.02, 0.06, 0.32)), (0.5, (0.01, 0.02, 0.12)), (0.65, (0.08, 0.02, 0.3))]),
        "strata": Hm.mat_strata(),
        "fossil": Hm.mat_fossil(),
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

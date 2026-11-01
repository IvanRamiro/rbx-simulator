"""Moonlit Isle eggs, built like the Jade Grove and Ember Peak eggs: high-detail pieces with
procedural shaders (egg_hi.py) baked onto a game mesh (egg_bake.py), glowing parts kept as
separate Neon pieces. Each is its own form, after its name:

- Celestial Egg: a piece of the night sky, glossy midnight lacquer with nebula clouds and stars
  in it, cradled in a silver crescent moon (a glowing pearl on its high horn) and crossed by a
  gold constellation of glowing stars.
- Astral Sanctum Egg: a moonstone shrine. Violet starlight shines out of six pointed-arch windows
  framed in gold, small gold stars between them, under a ribbed gold dome whose spire holds a
  glowing orb.
- Heavenly Throne Egg: a pearl egg wearing a small gold crown, seated on a cushion of soft cloud,
  a gold mandorla full of rays rising behind it as the throne's back, a glowing jewel at its
  point.

    import eggs_moon as E
    E.build()           # the high-detail eggs, in collections CelestialEggHi, ...
    E.export_all()      # bake and export: assets/eggs/<EggId>.fbx plus its maps
"""
import math
import random

import bpy

import egg_bake as B
import egg_hi as Hm
import egg_kit as K
import eggs_jade as J

W = K.W
V = K.V
TAU = K.TAU
H, R = K.H, K.R
on, normal_at = J.on, J.normal_at


def sphere(hi, centre, radius, mat=0, nu=18, nv=10):
    c = V(centre)
    dirs = [[V((math.sin(math.pi * j / nv) * math.cos(TAU * i / nu), -math.cos(math.pi * j / nv), math.sin(math.pi * j / nv) * math.sin(TAU * i / nu)))
             for i in range(nu + 1)] for j in range(nv + 1)]
    rows = [[hi.v(c + d * radius) for d in row] for row in dirs]
    for j in range(nv):
        for i in range(nu):
            q = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            out = dirs[j][i] + dirs[j][i + 1] + dirs[j + 1][i + 1] + dirs[j + 1][i]
            hi.facing(q, [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)], tuple(out), mat)


def star(hi, centre, normal, up, length, mat=0, inner=0.34, rise=0.3):
    """A four-pointed star lying on a surface, its points along `up` and across, rising to a
    faceted peak."""
    n = V(normal).normalized()
    u = V(up)
    u = (u - n * u.dot(n)).normalized()
    s = u.cross(n).normalized()
    c = V(centre)
    rim = [hi.v(c + (u * math.cos(TAU * k / 8) + s * math.sin(TAU * k / 8)) * (length if k % 2 == 0 else length * inner)) for k in range(8)]
    peak = hi.v(c + n * length * rise)
    for k in range(8):
        hi.facing([rim[k], rim[(k + 1) % 8], peak], [(0, 0), (1, 0), (0.5, 1)], tuple(n), mat)


def uv_path(points, off, per=12):
    """A path over the shell through (u, v) points, interpolated in (u, v) so it stays on the
    surface (a curve through the 3D points alone would cut under it)."""
    out = []
    for (u0, v0), (u1, v1) in zip(points, points[1:]):
        out += [on(u0 + (u1 - u0) * i / per, v0 + (v1 - v0) * i / per, off) for i in range(per)]
    return out + [on(*points[-1], off)]


# ---------- Celestial Egg ----------
CE_STAR = "ffc23a"     # the constellation's stars
CE_PEARL = "4f9dff"    # the pearl on the crescent's horn


def crescent_path(gap, r_max, high=0.74, low=0.46, n=64):
    """The crescent's spine and radius, round the egg's silhouette (the x-y plane): up its left
    side to the high horn, round under it, up its right side to the low horn. The inner edge keeps
    `gap` off the shell; the outer edge swells to r_max * 2 at the bottom of the curve."""
    pts, radii = [], []
    for i in range(n + 1):
        t = i / n
        s = -high + (high + low) * t                 # left side negative, right positive
        u = 0.75 if s < 0 else 0.25
        p, nrm = K.egg_point(u, abs(s))
        r = 0.012 + r_max * math.sin(math.pi * t) ** 0.85
        pts.append(V((p.x, p.y, 0.0)) + V((nrm.x, nrm.y, 0.0)).normalized() * (gap + r))
        radii.append(r)
    return pts, radii


def celestial(coll, M):
    sky = W.MeshBuilder()
    K.shell(sky, (0.5, 0.5), nu=64, nv=40)
    shell = sky.object("CE_Shell", coll, M["nightsky"], smooth=True)
    shell["keep"] = True
    # the crescent moon it lies in
    pts, radii = crescent_path(0.05, 0.17)
    moon = Hm.Hi()
    Hm.htube(moon, pts, lambda t: radii[min(len(radii) - 1, int(round(t * (len(radii) - 1))))], sides=18, per=1, uv_scale=1.0,
             tip=True, wobble=0.0)
    crescent = moon.object("CE_Crescent", coll, [M["moonsilver"]])
    crescent["keep"] = True
    # its pearl, resting in the high horn's tip
    pearl = Hm.Hi()
    sphere(pearl, pts[1], 0.1)
    # the constellation: glowing stars joined by fine gold lines over the front
    marks = [(-0.085, 0.66, 0.075), (-0.035, 0.735, 0.05), (0.03, 0.7, 0.09), (0.078, 0.6, 0.06), (0.058, 0.5, 0.075), (0.11, 0.42, 0.05)]
    stars = Hm.Hi()
    for u, v, size in marks:
        star(stars, on(u, v, 0.02), normal_at(u, v), (0, 1, 0), size)
    lines = Hm.Hi()
    for (u0, v0, _), (u1, v1, _) in zip(marks, marks[1:]):
        Hm.htube(lines, uv_path([(u0, v0), (u1, v1)], 0.012), lambda t: 0.009, sides=5, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    gold = lines.object("CE_Lines", coll, [M["gold"]])
    gold["keep"] = True
    st = stars.object("CE_Stars", coll, [K.glow_material(CE_STAR)], smooth=False)
    pe = pearl.object("CE_Pearl", coll, [K.glow_material(CE_PEARL)], smooth=False)
    return [shell, crescent, gold], {CE_STAR: [st], CE_PEARL: [pe]}


# ---------- Astral Sanctum Egg ----------
AS_LIGHT = "643cff"    # the astral light inside, through its windows and in the spire's orb (8a4dff showed pink as Neon)


def window_outline(uc, w=0.05, v0=0.3, vs=0.54, va=0.665, n_side=5, n_arch=7):
    """A pointed (equilateral) arch window in (u, v): straight sides up to its springing line,
    then two arcs meeting at its point."""
    left = [(uc - w, v0 + (vs - v0) * i / n_side) for i in range(n_side + 1)]
    arch_l = []
    for i in range(1, n_arch + 1):
        phi = math.radians(60) * i / n_arch
        arch_l.append((uc + w - 2 * w * math.cos(phi), vs + (va - vs) * math.sin(phi) / math.sin(math.radians(60))))
    arch_r = [(2 * uc - x, y) for x, y in reversed(arch_l[:-1])]
    right = [(uc + w, y) for _, y in reversed(left)]
    return left + arch_l + arch_r + right


def arch_half(v, w, vs, va):
    """The window's half-width (in u) at height v: straight below vs, an equilateral arch above."""
    if v <= vs:
        return w
    phi = math.asin(min(1.0, (v - vs) / (va - vs) * math.sin(math.radians(60))))
    return max(0.0, 2 * w * math.cos(phi) - w)


def window_pane(hi, uc, off, w=0.05, v0=0.3, vs=0.54, va=0.665, nx=6, ny=18, mat=0):
    """The glass of a window as a grid laid on the shell, so it follows its curve."""
    rows = []
    for j in range(ny + 1):
        v = v0 + (va - v0) * j / ny
        half = arch_half(v, w, vs, va)
        rows.append([hi.v(on(uc + half * (-1 + 2 * i / nx), v, off)) for i in range(nx + 1)])
    for j in range(ny):
        v = v0 + (va - v0) * (j + 0.5) / ny
        for i in range(nx):
            hi.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)],
                      tuple(normal_at(uc, v)), mat)


def astral_sanctum(coll, M):
    stone = W.MeshBuilder()
    K.shell(stone, (0.5, 0.5), nu=64, nv=40)
    shell = stone.object("AS_Shell", coll, M["moonstone"], smooth=True)
    shell["keep"] = True
    gold, panes = Hm.Hi(), Hm.Hi()
    tube = lambda pts, r, closed=False: Hm.htube(gold, pts + (pts[:2] if closed else []), lambda t: r, sides=7, per=1, uv_scale=3.0,
                                                  tip=False, wobble=0.0)
    for k in range(6):
        uc = k / 6
        outline = window_outline(uc)
        window_pane(panes, uc, 0.01)
        tube([on(u, v, 0.024) for u, v in outline], 0.022, closed=True)
        tube(uv_path([(uc, 0.3), (uc, 0.565)], 0.022), 0.012)                                          # mullion
        tube([on(uc + 0.016 * math.sin(TAU * i / 12), 0.6 + 0.024 * math.cos(TAU * i / 12), 0.02) for i in range(12)], 0.009, closed=True)  # its tracery ring
        tube(uv_path([(uc - 0.062, 0.285), (uc + 0.062, 0.285)], 0.03), 0.02)                        # the sill
        star(gold, on(uc + 1 / 12, 0.47, 0.015), normal_at(uc + 1 / 12, 0.47), (0, 1, 0), 0.07)       # a gold star between windows
    # the plinth bands round its foot
    tube([on(i / 64, 0.2, 0.02) for i in range(64)], 0.035, closed=True)
    tube([on(i / 64, 0.235, 0.012) for i in range(64)], 0.014, closed=True)
    # the dome: a gold cap over its crown with a rim and eight ribs
    dome_mb = W.MeshBuilder()
    K.shell(dome_mb, (0.5, 0.5), nu=48, nv=12, offset=0.012, v_from=0.8, v_to=1.0)
    dome = dome_mb.object("AS_Dome", coll, M["gold"], smooth=True)
    dome["keep"] = True
    tube([on(i / 64, 0.8, 0.02) for i in range(64)], 0.03, closed=True)
    for k in range(8):
        tube(uv_path([(k / 8, 0.81), (k / 8, 0.975)], 0.022), 0.014)
    # the spire: a collar, a slender spike through a glowing orb
    top = V((0, H, 0))
    sphere(gold, top + V((0, 0.03, 0)), 0.05)
    Hm.htube(gold, [top + V((0, 0.05, 0)), top + V((0, 0.2, 0)), top + V((0, 0.46, 0))], lambda t: 0.028 * (1 - 0.8 * t), sides=8, per=4,
             uv_scale=3.0, tip=True, wobble=0.0)
    orb = Hm.Hi()
    sphere(orb, top + V((0, 0.22, 0)), 0.065)
    g = gold.object("AS_Gold", coll, [M["gold"]])
    g["keep"] = True
    pn = panes.object("AS_Windows", coll, [K.glow_material(AS_LIGHT)], smooth=False)
    ob = orb.object("AS_Orb", coll, [K.glow_material(AS_LIGHT)], smooth=False)
    return [shell, dome, g], {AS_LIGHT: [pn, ob]}


# ---------- Heavenly Throne Egg ----------
HT_GLOW = "ffa31a"     # the mandorla's inner light, the crown's jewels and the jewel at its point
MANDORLA_Z = -1.22     # the throne's back stands just behind the egg
M_BOTTOM, M_TOP, M_HALF = 0.1, 3.55, 1.42


def mandorla_half(y, inset=0.0):
    """The mandorla's half-width at height y: a pointed oval, widest a little below its middle."""
    t = (y - M_BOTTOM) / (M_TOP - M_BOTTOM)
    if t <= 0 or t >= 1:
        return 0.0
    return max(0.0, M_HALF * math.sin(math.pi * t ** 1.15) - inset)


def mandorla_path(inset, z, n=60, from_t=0.06):
    """The pointed oval from low on its left, over its point, to low on its right (its foot is in
    the clouds)."""
    pts = []
    for i in range(n + 1):
        a = i / n
        t = from_t + (1 - from_t) * (2 * a if a <= 0.5 else 2 * (1 - a))
        y = M_BOTTOM + (M_TOP - M_BOTTOM) * t
        side = -1 if a <= 0.5 else 1
        x = side * mandorla_half(y, inset)
        if inset and abs(t - 1) < 1e-9:
            y -= inset * 1.6                         # the inner line's point sits inside the frame's
        pts.append(V((x, y, z)))
    return pts


def heavenly_throne(coll, M):
    pearl_mb = W.MeshBuilder()
    K.shell(pearl_mb, (0.5, 0.5), nu=64, nv=40)
    shell = pearl_mb.object("HT_Shell", coll, M["pearl"], smooth=True)
    shell["keep"] = True
    gold, glow = Hm.Hi(), Hm.Hi()
    # its crown: a band near the top with seven tines, each tipped with a jewel
    ring = [on(i / 64, 0.86, 0.018) for i in range(64)]
    Hm.htube(gold, ring + ring[:2], lambda t: 0.028, sides=8, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    for k in range(7):
        u = k / 7
        p, n = K.egg_point(u, 0.86, offset=0.02)
        d = (V((n.x, 0, n.z)).normalized() * 0.32 + V((0, 1, 0))).normalized()
        length = 0.24 if k == 0 else 0.17
        tip = p + d * length
        Hm.htube(gold, [p, p + d * length * 0.5, tip], lambda t: 0.03 * (1 - 0.5 * t), sides=7, per=3, uv_scale=3.0, tip=False, wobble=0.0)
        sphere(glow, tip + d * 0.03, 0.042 if k == 0 else 0.034)
    # a gold sun on its front: an eight-pointed burst in a ring round a glowing cabochon, with a
    # curling flourish to either side
    sun_u, sun_v = 0.0, 0.47
    sn = normal_at(sun_u, sun_v)
    sc = on(sun_u, sun_v, 0.012)
    star(gold, sc, sn, (0, 1, 0), 0.34, inner=0.3, rise=0.12)
    star(gold, sc, sn, (1, 1, 0), 0.25, inner=0.3, rise=0.12)
    du, dv = 0.026, 0.044                            # the ring's radius (about 0.18) in u and v
    sun_ring = [on(sun_u + du * math.sin(TAU * i / 32), sun_v + dv * math.cos(TAU * i / 32), 0.05) for i in range(32)]
    Hm.htube(gold, sun_ring + sun_ring[:2], lambda t: 0.018, sides=7, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    sphere(glow, on(sun_u, sun_v, -0.03), 0.11)
    for side in (-1, 1):
        curl = [(side * 0.04, 0.455), (side * 0.09, 0.43), (side * 0.14, 0.45), (side * 0.155, 0.49), (side * 0.13, 0.51), (side * 0.115, 0.495)]
        smooth = [(p.x, p.y) for p in W.catmull([(u, v, 0.0) for u, v in curl], 6)]
        Hm.htube(gold, [on(u, v, 0.02) for u, v in smooth], lambda t: 0.02 * (1 - 0.6 * t), sides=6, per=1, uv_scale=3.0, tip=True, wobble=0.0)
    # the cushion of cloud it sits on, swelling into armrests at its sides
    rnd = random.Random(121)
    lobes = []
    for k in range(16):
        a = TAU * k / 16
        front = math.cos(a)                          # 1 at the front
        side = abs(math.sin(a))
        rr = 0.86 + 0.08 * side + rnd.uniform(-0.04, 0.04)
        y = 0.16 + 0.12 * side - 0.05 * max(0.0, front) + rnd.uniform(-0.03, 0.03)
        lobes.append(((math.sin(a) * rr, y, math.cos(a) * rr), 0.26 + 0.06 * side + rnd.uniform(-0.02, 0.03)))
    for sx in (-1, 1):
        lobes += [((sx * 1.12, 0.48, -0.15), 0.25), ((sx * 1.18, 0.7, -0.38), 0.2), ((sx * 1.08, 0.82, -0.62), 0.15)]
    lobes += [((0, 0.2, -1.05), 0.3), ((-0.55, 0.22, -1.0), 0.27), ((0.55, 0.22, -1.0), 0.27),        # round the mandorla's foot,
              ((0, 0.34, -1.3), 0.27)]                                                               # hiding the frame's ends
    cloud = Hm.foliage("HT_Cloud", coll, M["cloud"], lobes, voxel=0.03, roughness=0.012)
    # the mandorla: a gold frame, a glowing inner line, rays fanning from behind the egg
    frame = mandorla_path(0.0, MANDORLA_Z)
    Hm.htube(gold, frame, lambda t: 0.055, sides=10, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(glow, mandorla_path(0.11, MANDORLA_Z + 0.03), lambda t: 0.022, sides=6, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    hub = V((0, 1.45, MANDORLA_Z - 0.02))
    for k in range(15):
        a = math.radians(-112 + 224 * k / 14)       # from up, round both sides; none down into the clouds
        d = V((math.sin(a), math.cos(a), 0))
        reach = 0.0
        while reach < 3.0:
            q = hub + d * (reach + 0.02)
            if abs(q.x) >= mandorla_half(q.y, 0.2) or q.y >= M_TOP - 0.35:
                break
            reach += 0.02
        start = 0.95 if k % 2 == 0 else 1.2
        if reach - start < 0.15:
            continue
        Hm.htube(gold, [hub + d * start, hub + d * (start + reach) / 2, hub + d * reach], lambda t: 0.048 * (1 - 0.85 * t), sides=6, per=2,
                 uv_scale=3.0, tip=True, wobble=0.0)
    # the jewel at its point, set on a gold star
    apex = V((0, M_TOP + 0.04, MANDORLA_Z + 0.02))
    star(gold, apex, (0, 0, 1), (0, 1, 0), 0.24, rise=0.2)
    sphere(glow, apex + V((0, 0, 0.05)), 0.065)
    g = gold.object("HT_Gold", coll, [M["gold"]])
    g["keep"] = True
    gl = glow.object("HT_Glow", coll, [K.glow_material(HT_GLOW)], smooth=False)
    return [shell, cloud, g], {HT_GLOW: [gl]}


EGGS = {"CelestialEgg": (celestial, 12000), "AstralSanctumEgg": (astral_sanctum, 15000), "HeavenlyThroneEgg": (heavenly_throne, 16000)}


def materials():
    return {
        "nightsky": Hm.mat_nightsky(),
        "moonsilver": Hm.mat_moonsilver(),
        "moonstone": Hm.mat_moonstone(),
        "pearl": Hm.mat_pearl(),
        "cloud": Hm.mat_cloud(),
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

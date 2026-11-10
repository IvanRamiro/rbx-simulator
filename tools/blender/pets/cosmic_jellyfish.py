"""The Cosmic Jellyfish (Uncommon, Nebulae; Celestial Egg): "A drifting scrap of nebula with no thoughts at all, and yet it always knows where you are."

A new creature. A real see-through glass bell with a small nebula slowly turning inside it, rose and amber gas with teal at its edges, four gold horseshoes on it as a real moon jelly has. It has no eyes (the owner's decision), and
no thoughts, and yet its bell leans gently toward you wherever you stand. Frilled arms and six long tentacles hang below.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/cosmic_jellyfish.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, tentacle tips near z = 0. The maps go to assets/pets/CelestialEgg/.

What touches what: eight canals run along the inside of the glass from the nebula, buried in it, to the glass lip, buried in that, so the nebula hangs from them and can turn; the stem's top is buried in the nebula; the arms' roots in the stem;
each tentacle's root is sunk into the lip. The glass is its own mesh, the game sets it see-through.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "CosmicJellyfish"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "CelestialEgg")

# ---------- the frame of it ----------
ZM, R0, H0 = 1.62, 0.66, 0.56       # the margin's height, the bell's radius and its height over the margin
LOBE0 = -math.pi / 2                # a lappet straight ahead; so a notch each side of it
RIM_TH = [-math.pi / 2 + math.radians(22.5 + 45 * k) for k in range(8)]      # the notches: each rim section's bone
LOBE_TH = {"FL": math.radians(-45), "L": 0.0, "BL": math.radians(45), "BR": math.radians(135), "R": math.pi, "FR": math.radians(-135)}
TENT_END = {"FL": 0.34, "L": 0.05, "BL": 0.22, "BR": 0.14, "R": 0.38, "FR": 0.10}
TENTS = list(LOBE_TH)
ZH, RH, HH = 1.84, 0.40, 0.20       # the nebula: height, radius, half height


# ---------- surfaces ----------
def outer(t, f):
    """The bell's outer surface. t: angle round it. f: 0 at the crown, 1 at the margin."""
    phi = f * math.pi / 2
    lobe = np.cos(8 * (t - LOBE0))
    edge = f ** 5
    rad = R0 * (1 + edge * (0.045 * lobe - 0.015) - 0.018 * f ** 14)
    r = rad * np.sin(phi) ** 0.88
    z = ZM + H0 * np.maximum(np.cos(phi), 0.0) ** 1.12 - 0.03 * edge * (1 + lobe) / 2
    return r * np.cos(t), r * np.sin(t), z


def inner(t, f):
    x, y, z = outer(t, f)
    phi = f * math.pi / 2
    th = 0.012 + 0.085 * (1 - f) ** 1.5
    return x - np.sin(phi) * np.cos(t) * th, y - np.sin(phi) * np.sin(t) * th, z - np.cos(phi) * th


def rings_mesh(name, coll, top, rings, bottom, smooth_shade=True):
    """A closed form from one pole through its rings (each nt points, in order) to the other. Vertices stay in this order: 0 is the first pole, then ring by ring, the last is the other pole."""
    m = Mesh()
    bm = m.bm
    a = bm.verts.new(top)
    grid = []
    for ring in rings:
        grid.append([bm.verts.new(tuple(p)) for p in ring])
    b = bm.verts.new(bottom)
    nt = len(rings[0])
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((a, grid[0][j], grid[0][j2]))
        for i in range(len(grid) - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]))
        bm.faces.new((grid[-1][j], b, grid[-1][j2]))
    return m.finish(name, coll, smooth_shade=smooth_shade)


def glass_rows(fo, fi, nt):
    t = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    rings = []
    for f in fo:
        rings.append(np.stack(outer(t, np.full(nt, f)), axis=1))
    for f in fi:
        rings.append(np.stack(inner(t, np.full(nt, f)), axis=1))
    return rings, t


def build_glass(name, coll, fo, fi, nt):
    rings, t = glass_rows(fo, fi, nt)
    top = tuple(float(c[0]) for c in outer(np.array([0.0]), np.array([0.0])))
    bottom = tuple(float(c[0]) for c in inner(np.array([0.0]), np.array([0.0])))
    return rings_mesh(name, coll, top, rings, bottom)


def glass_coords(fo, fi, nt):
    """Per vertex of a glass mesh: its angle, f, and whether it is the inner surface."""
    t = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    tt = [0.0]
    ff = [0.0]
    ins = [0.0]
    for f in fo:
        tt += list(t)
        ff += [f] * nt
        ins += [0.0] * nt
    for f in fi:
        tt += list(t)
        ff += [f] * nt
        ins += [1.0] * nt
    tt.append(0.0)
    ff.append(0.0)
    ins.append(1.0)
    return np.array(tt), np.array(ff), np.array(ins)


FO_HI = list(np.linspace(0.008, 1.0, 150))
FI_HI = list(np.linspace(1.0, 0.012, 90))
NT_HI = 720
FO_LOW = [0.12, 0.26, 0.4, 0.52, 0.62, 0.72, 0.8, 0.87, 0.93, 0.97, 1.0]
FI_LOW = [1.0, 0.92, 0.8, 0.66, 0.5, 0.3, 0.12]
NT_LOW = 48


def heart_rings(nt, rows):
    t = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    out = []
    for i in range(1, rows):
        v = i / rows
        r = RH * (1 + 0.055 * np.cos(4 * t + 0.6)) * math.sin(math.pi * v) ** 0.8
        z = ZH + HH * math.cos(math.pi * v) * np.ones(nt)
        out.append(np.stack((r * np.cos(t), r * np.sin(t), z), axis=1))
    return out


def build_heart(name, coll, nt, rows):
    return rings_mesh(name, coll, (0, 0, ZH + HH), heart_rings(nt, rows), (0, 0, ZH - HH))


# ---------- the arms: frilled ribbons ----------
ARM_TH = [math.radians(45 + 90 * k) for k in range(4)]
ARM_LEN = (0.66, 0.74, 0.62, 0.70)


def arm_path(k):
    a = ARM_TH[k]
    pts = []
    for z, r, spin in ((1.5, 0.045, 0.0), (1.38, 0.13, 0.12), (1.22, 0.19, 0.45), (1.06, 0.22, 0.85), (0.9, 0.205, 1.3), (ARM_LEN[k], 0.17, 1.8)):
        pts.append(V(r * math.cos(a + spin), r * math.sin(a + spin) + 0.02 * (1.47 - z), z))
    return catmull(pts, 8)


def along(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def arm_point(k, fine):
    path = arm_path(k)

    def point(u, v):
        p = along(path, u)
        tan = (along(path, min(u + 0.02, 1)) - along(path, max(u - 0.02, 0))).normalized()
        out = V(p.x, p.y, 0)
        out = out.normalized() if out.length > 1e-5 else V(1, 0, 0)
        side = (out - tan * tan.dot(out)).normalized()
        nrm = tan.cross(side).normalized()
        w = 2 * v - 1
        width = 0.066 * math.sin(math.pi * (0.06 + 0.94 * u)) ** 0.6 * (1 - 0.2 * u) + 0.012
        taper = 0.4 + 0.6 * math.sin(math.pi * u)
        wave = 0.042 * w * w * math.sin(TAU * 6 * u + k * 1.7) * taper
        if fine:
            wave += 0.012 * w ** 4 * math.sin(TAU * 21 * u + k) * taper
        return p + side * width * w + nrm * wave
    return point


def closed_ribbon(point, thick, nu, nv, name, coll):
    """The high-detail ribbon: closed, or the edge shows its dark inside as a black line. Returns it and per vertex its u."""
    m = Mesh()
    m.sheet(point, lambda u, v: thick, nu, nv)
    uu = np.repeat(np.repeat(np.arange(nu + 1) / nu, nv + 1), 2)
    return m.finish(name, coll), uu


def open_ribbon(point, thick, nu, nv, name, coll):
    """Upper and lower faces, not joined at the edge: joined, the shading rounds over the edge and bends the bake's rays off the ribbon. Returns the object and per vertex its u."""
    m = Mesh()
    bm = m.bm
    uu = []
    up, lo = [], []
    for i in range(nu + 1):
        ru, rl = [], []
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            p = Vector(point(u, v))
            du = Vector(point(min(u + 1 / nu, 1), v)) - Vector(point(max(u - 1 / nu, 0), v))
            dv = Vector(point(u, min(v + 1 / nv, 1))) - Vector(point(u, max(v - 1 / nv, 0)))
            nrm = du.cross(dv)
            nrm = nrm.normalized() if nrm.length > 1e-9 else V(0, 0, 1)
            ru.append(bm.verts.new(p + nrm * thick / 2))
            rl.append(bm.verts.new(p - nrm * thick / 2))
            uu += [u, u]
        up.append(ru)
        lo.append(rl)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((up[i][j], up[i + 1][j], up[i + 1][j + 1], up[i][j + 1]))
            bm.faces.new((lo[i][j + 1], lo[i + 1][j + 1], lo[i + 1][j], lo[i][j]))
    return m.finish(name, coll, recalc=False), np.array(uu)


# ---------- the tentacles ----------
def tent_path(key):
    th = LOBE_TH[key]
    root_r = R0 * 0.965
    c, s = math.cos(th), math.sin(th)
    tang = V(-s, c, 0)
    zr = float(outer(np.array([th]), np.array([1.0]))[2][0]) + 0.025
    ze = TENT_END[key]
    ph = sum(ord(ch) for ch in key) * 0.7
    pts = []
    for i in range(9):
        f = i / 8
        r = root_r * (1 - 0.2 * f ** 0.8) + 0.055 * math.sin(5.5 * f + ph) * f
        w = 0.07 * math.sin(4.5 * f + ph * 1.3) * f
        pts.append(V(r * c, r * s, zr + (ze - zr) * f) + tang * w + V(0, 0.26 * f * f, 0))
    return catmull(pts, 6)


def tent_radius(f):
    return 0.0055 + 0.0135 * (1 - f) ** 0.9


def build_tents(name, coll, sides, step, bead=False):
    m = Mesh()
    which, ff = [], []
    for index, key in enumerate(TENTS):
        path = tent_path(key)
        pts = path[::step]
        if pts[-1] != path[-1]:
            pts.append(path[-1])
        rows = len(pts)
        m.tube(pts, tent_radius, sides=sides, flat=0.9, plane=V(1, 0, 0))
        for i in range(rows):
            for j in range(sides):
                which.append(index)
                ff.append(i / (rows - 1))
    return m.finish(name, coll), np.array(which), np.array(ff)


# ---------- the stem, the canals, the horseshoes ----------
STEM = [V(0, 0, 1.76), V(0, 0, 1.62), V(0, 0, 1.43)]


def build_stem(name, coll, sides):
    m = Mesh()
    m.tube(catmull(STEM, 4), lambda f: 0.15 - 0.09 * f ** 0.6, sides=sides)
    return m.finish(name, coll)


def canal_path(k):
    th = RIM_TH[k]
    c, s = math.cos(th), math.sin(th)
    pts = [V((RH - 0.05) * c, (RH - 0.05) * s, ZH + 0.01)]
    for f in (0.56, 0.68, 0.8, 0.9, 0.97):
        x, y, z = inner(np.array([th]), np.array([f]))
        pts.append(V(float(x[0]) - 0.012 * c, float(y[0]) - 0.012 * s, float(z[0]) - 0.012))
    x, y, z = outer(np.array([th]), np.array([0.995]))      # its end is buried in the glass lip
    pts.append(V(float(x[0]) - 0.006 * c, float(y[0]) - 0.006 * s, float(z[0])))
    return catmull(pts, 4)


def canal_radius(f):
    return 0.0115 - 0.003 * f


def build_canals(name, coll, sides, step):
    m = Mesh()
    which, ff = [], []
    for k in range(8):
        path = canal_path(k)
        pts = path[::step]
        if pts[-1] != path[-1]:
            pts.append(path[-1])
        m.tube(pts, canal_radius, sides=sides)
        for i in range(len(pts)):
            for j in range(sides):
                which.append(k)
                ff.append(i / (len(pts) - 1))
    return m.finish(name, coll), np.array(which), np.array(ff)


def clover_path(k, tree, lift):
    a = math.radians(45 + 90 * k)
    c = V(0.205 * math.cos(a), 0.205 * math.sin(a), 0)
    pts = []
    for i in range(15):
        g = a + math.radians(35) + math.radians(290) * i / 14
        p = c + V(0.088 * math.cos(g), 0.088 * math.sin(g), 0)
        hit = tree.ray_cast(V(p.x, p.y, 3.0), V(0, 0, -1), 3.0)[0]
        pts.append(V(p.x, p.y, (hit.z if hit else ZH + HH * 0.7) + lift))
    return pts


def build_clover(tree, name, coll, sides, lift):
    m = Mesh()
    for k in range(4):
        m.tube(clover_path(k, tree, lift), lambda f: 0.0145 * (0.55 + 0.45 * math.sin(math.pi * f)), sides=sides)
    return m.finish(name, coll, smooth_shade=False)


# ---------- paint ----------
ROSE, AMBER, TEAL, DUSK = rgb(232, 72, 128), rgb(255, 170, 84), rgb(30, 176, 180), rgb(70, 26, 96)
NIGHT, PEARL, LILAC, MIST = rgb(26, 12, 58), rgb(250, 240, 248), rgb(206, 180, 244), rgb(190, 232, 240)
VIOLET = rgb(128, 84, 226)


def worley(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2 + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                d1 = np.minimum(d1, d)
    return d1


def paint_heart(o):
    """An emission nebula, not a galaxy: glowing rose and amber gas, teal where it thins, dark pillars of dust standing in it. It turns, so it is not the same from any side."""
    P = verts(o)
    Nn = normals(o)
    a = (fbm(P, 2.2, 3, 41) - 0.5)[:, None]
    gas = fbm(P + a * 0.7, 3.2, 4, 7)
    hot = fbm(P + a * 0.5 + 4.0, 2.8, 4, 19)
    cold = fbm(P - a * 0.6 + 9.0, 3.4, 3, 29)
    col = mix(DUSK, ROSE, smooth(0.3, 0.62, gas))
    col = mix(col, rgb(40, 150, 176), smooth(0.48, 0.72, cold) * (1 - smooth(0.42, 0.62, hot)) * 0.85)
    col = mix(col, AMBER, smooth(0.5, 0.72, hot) * smooth(0.36, 0.6, gas) * 0.9)
    col = mix(col, rgb(255, 232, 196), smooth(0.66, 0.84, hot) * smooth(0.5, 0.7, gas) * 0.7)
    lane = 1 - np.abs(2 * fbm(P + a * 0.4 + 2.0, 3.8, 3, 53) - 1)
    col = mix(col, DUSK * 0.55, smooth(0.86, 0.99, lane) * 0.7)
    d = worley(P, 44.0, 61)
    thick = smooth(0.42, 0.62, fbm(P, 6.5, 3, 71))
    stars = (1 - smooth(0.04, 0.1, d)) * thick
    col = mix(col, rgb(255, 252, 240), stars)
    disp = 0.014 * (gas - 0.5)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, 0.55)


def paint_glass(o, t, f, ins):
    """Pale, because it is seen through: lilac at the crown, cool at the shoulder, the rim nearly white. Sixteen fine canals, a ring near the margin, a few stars caught in it."""
    P = verts(o)
    Nn = normals(o)
    col = mix(LILAC, MIST, smooth(0.2, 0.75, f))
    col = mix(col, PEARL, smooth(0.86, 0.99, f))
    rib = np.abs(np.sin(8 * (t - LOBE0)))
    lines = (1 - smooth(0.0, 0.05, rib)) * smooth(0.3, 0.5, f)
    col = mix(col, rgb(120, 96, 210), lines * 0.55)
    ring = np.exp(-((f - 0.9) / 0.012) ** 2)
    col = mix(col, rgb(230, 110, 170), ring * 0.8)
    d = worley(P, 30.0, 11)
    stars = (1 - smooth(0.03, 0.075, d)) * (1 - ins) * smooth(0.5, 0.62, fbm(P, 5.0, 3, 13))
    col = mix(col, np.array((1.0, 1.0, 1.0)), stars)
    ripple = fbm(P, 16.0, 3, 23)
    disp = (0.0022 * (1 - smooth(0.0, 0.1, rib)) * smooth(0.25, 0.45, f) + 0.0016 * (ripple - 0.5)) * (1 - 2 * ins)
    set_verts(o, P + Nn * disp[:, None])
    paint(o, col, 0.14 + 0.1 * smooth(0.9, 1.0, f))


def paint_stem(o):
    P = verts(o)
    paint(o, mix(mix(ROSE, DUSK, 0.3), ROSE, smooth(1.72, 1.5, P[:, 2])), 0.42)


def paint_arm(o, u, k):
    """Rose gas in the middle of each ribbon, its frilled edge pale, going to teal toward the end."""
    P = verts(o)
    gas = fbm(P, 9.0, 4, 31 + k)
    col = mix(ROSE, rgb(255, 176, 196), smooth(0.35, 0.68, gas))
    col = mix(col, VIOLET, smooth(0.42, 0.72, u))
    col = mix(col, TEAL, smooth(0.72, 1.0, u))
    fine = np.sin(u * TAU * 21 + k) * 0.5 + 0.5
    col = col * (0.86 + 0.14 * fine)[:, None]
    paint(o, col, 0.36)


def paint_tents(o, which, ff):
    """Pale near the rim, through rose, to a teal tip, with a band of stinging cells every so often: little bright beads."""
    P = verts(o)
    Nn = normals(o)
    col = mix(mix(ROSE, PEARL, 0.45), ROSE, smooth(0.02, 0.28, ff))
    col = mix(col, VIOLET, smooth(0.34, 0.62, ff))
    col = mix(col, TEAL, smooth(0.66, 0.98, ff))
    beads = np.sin(ff * 150 + which * 2.1) * 0.5 + 0.5
    bright = smooth(0.76, 0.95, beads)
    col = mix(col, rgb(255, 240, 248), bright * 0.65)
    set_verts(o, P + Nn * (0.0018 * bright)[:, None])
    paint(o, col, 0.32)


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_heart(N + "HeartHi", HI, 512, 160)
    if not clay:
        paint_heart(pieces["Skin"])
    pieces["Glass"] = build_glass(N + "GlassHi", HI, FO_HI, FI_HI, NT_HI)
    if not clay:
        t, f, ins = glass_coords(FO_HI, FI_HI, NT_HI)
        paint_glass(pieces["Glass"], t, f, ins)
    pieces["Stem"] = build_stem(N + "StemHi", HI, 24)
    pieces["Canals"], _, _ = build_canals(N + "CanalsHi", HI, 10, 1)
    for k in range(4):
        o, u = closed_ribbon(arm_point(k, True), 0.006, 200, 30, N + "Arm%dHi" % k, HI)
        pieces["Arm%d" % k] = o
        if not clay:
            paint_arm(o, u, k)
    o, which, ff = build_tents(N + "TentsHi", HI, 10, 1)
    pieces["Tents"] = o
    if not clay:
        paint_tents(o, which, ff)
        paint_stem(pieces["Stem"])
        plain(pieces["Canals"], rgb(120, 225, 225), 0.3)
    glows = {"Clover": build_clover(tree_of(pieces["Skin"]), N + "Clover_Glow_ffb04a", HI, 8, 0.009)}
    return pieces, glows, data


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 1.4
        o.data.materials.append(m)
        o.visible_shadow = False


def see_through(mat, amount):
    """For the review only: the glass as the game shows it."""
    m = mat.copy()
    m.name = PET + "_GlassShow"
    t = m.node_tree
    bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
    tr = t.nodes.new("ShaderNodeBsdfTransparent")
    mx = t.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = amount
    t.links.new(bsdf.outputs[0], mx.inputs[1])
    t.links.new(tr.outputs[0], mx.inputs[2])
    # the game doesn't draw a face turned away from the camera
    geo = t.nodes.new("ShaderNodeNewGeometry")
    cull = t.nodes.new("ShaderNodeMixShader")
    t.links.new(geo.outputs["Backfacing"], cull.inputs[0])
    t.links.new(mx.outputs[0], cull.inputs[1])
    t.links.new(tr.outputs[0], cull.inputs[2])
    t.links.new(cull.outputs[0], out.inputs["Surface"])
    return m


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.06, 1.08)
GLASS_SHOW = 0.58
EXTRA = [(0.2, -0.95, 0.12, 3.6, (0, -0.1, 1.82)), (0.5, -0.85, -0.05, 1.8, (0.18, -0.56, 1.64)), (0, -0.2, 1, 3.2, (0, 0, 1.85)), (0.55, -0.7, -0.75, 3.4, (0, 0, 1.55)), (0.7, -0.7, 0.05, 3.4, (0, -0.02, 1.05)), (0.8, 0.6, 0, 3.4, (0.1, 0.25, 0.42))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.26, 0.30, 0.40, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.06, ao_share=0.4)
    glass_mat = see_through(mat, GLASS_SHOW)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(glass_mat if key == "Glass" else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=8.2, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Glass": 0.55, "Stem": 0.8, "Canals": 0.8, "Tents": 1.0, "Arm0": 1.0, "Arm1": 1.0, "Arm2": 1.0, "Arm3": 1.0}
HEART_DENSITY = 1.5
META = {}


def glass_uv(o, density):
    """Two clean discs, seen from above and from below, each laid out from the crown at its true distance down the bell. The nebula shows through the rest; the glass needs little of the map."""
    me = o.data
    uv = me.uv_layers.active.data
    P = verts(o)
    no, ni, nt = len(FO_LOW), len(FI_LOW), NT_LOW
    apex_o, apex_i = 0, len(P) - 1
    t = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    rings = P[1:-1].reshape(no + ni, nt, 3)
    run = np.linalg.norm(rings[0] - P[apex_o], axis=1).mean()
    arc_o = [run]
    for i in range(1, no):
        run += np.linalg.norm(rings[i] - rings[i - 1], axis=1).mean()
        arc_o.append(run)
    lip = run + np.linalg.norm(rings[no] - rings[no - 1], axis=1).mean()
    run = np.linalg.norm(rings[no + ni - 1] - P[apex_i], axis=1).mean()
    arc_i = {no + ni - 1: run}
    for i in range(no + ni - 2, no - 1, -1):
        run += np.linalg.norm(rings[i] - rings[i + 1], axis=1).mean()
        arc_i[i] = run

    def place(v, inner_side):
        if v == apex_o or v == apex_i:
            return (9.0, 0.5) if inner_side else (0.5, 0.5)
        ring, j = (v - 1) // nt, (v - 1) % nt
        if inner_side:
            a = arc_i[ring] * density * 0.9
            return (9.0 + a * math.cos(t[j]), 0.5 + a * math.sin(t[j]))
        a = (arc_o[ring] if ring < no else lip) * density
        return (0.5 + a * math.cos(t[j]), 0.5 + a * math.sin(t[j]))
    for poly in me.polygons:
        vs = list(poly.vertices)
        # a face is on the inner surface if none of it is outer; the lip's faces belong to the outer disc
        inner_side = all(v == apex_i or (v != apex_o and (v - 1) // nt >= no) for v in vs)
        for l, v in zip(poly.loop_indices, vs):
            uv[l].uv = place(v, inner_side)


def build_low(pieces, data):
    lows = {"Skin": build_heart(N + "HeartLow", GAME, 28, 12)}
    lows["Glass"] = build_glass(N + "Glass", GAME, FO_LOW, FI_LOW, NT_LOW)
    m = Mesh()
    m.tube(catmull(STEM, 1), lambda f: 0.15 - 0.09 * f ** 0.6, sides=8)
    lows["Stem"] = m.finish(N + "StemLow", GAME)
    lows["Canals"], META["CanalWhich"], META["CanalF"] = build_canals(N + "CanalsLow", GAME, 4, 4)
    for k in range(4):
        lows["Arm%d" % k], META["ArmU%d" % k] = open_ribbon(arm_point(k, False), 0.006, 36, 2, N + "Arm%dLow" % k, GAME)
    lows["Tents"], META["TentWhich"], META["TentF"] = build_tents(N + "TentsLow", GAME, 5, 4)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
def rim_of_lobe(key):
    want = LOBE_TH[key] - math.radians(22.5)
    return min(range(8), key=lambda k: abs(((RIM_TH[k] - want + math.pi) % TAU) - math.pi))


def rim_share(t):
    u = ((t - RIM_TH[0]) % TAU) / (math.pi / 4)
    k = int(u) % 8
    s = float(smooth(0.0, 1.0, u - int(u)))
    return {"Rim%d" % k: 1 - s, "Rim%d" % ((k + 1) % 8): s}


TENT_KNOTS = (0.02, 0.34, 0.66)
ARM_KNOTS = (0.12, 0.42, 0.72)


def skeleton(data):
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, 0, ZM), "Root"), ("Apex", V(0, 0, ZM + H0 * 0.72), "Body"), ("Nebula", V(0, 0, ZH), "Body")]
    for k in range(8):
        th = np.array([RIM_TH[k]])
        x, y, z = outer(th, np.array([0.5]))
        bones.append(("Rim%d" % k, V(float(x[0]), float(y[0]), float(z[0])), "Body"))
    for k in range(4):
        path = arm_path(k)
        parent = "Body"
        for tag, f in zip("abc", ARM_KNOTS):
            name = "A%d%s" % (k, tag)
            bones.append((name, along(path, f), parent))
            parent = name
    for key in TENTS:
        path = tent_path(key)
        parent = "Rim%d" % rim_of_lobe(key)
        for tag, f in zip("abc", TENT_KNOTS):
            name = "T%s%s" % (key, tag)
            bones.append((name, along(path, f), parent))
            parent = name
    return armature(bones)


def bind_all(lows, rig, glows, data):
    t, f, ins = glass_coords(FO_LOW, FI_LOW, NT_LOW)
    w = []
    for i in range(len(t)):
        fi = float(f[i])
        sa = 1 - float(smooth(0.2, 0.4, fi))
        sr = float(smooth(0.42, 0.66, fi))
        row = {}
        if sa > 0:
            row["Apex"] = sa
        if 1 - sa - sr > 0:
            row["Body"] = 1 - sa - sr
        if sr > 0:
            for b, v in rim_share(float(t[i])).items():
                row[b] = v * sr
        w.append(row)
    weigh(lows["Glass"], w)
    rigid(lows["Skin"], "Nebula")
    rigid(lows["Stem"], "Body")
    canal = []
    for k, g in zip(META["CanalWhich"], META["CanalF"]):
        s = float(smooth(0.35, 0.8, g))
        canal.append({"Body": 1 - s, "Rim%d" % int(k): s} if s > 0 else {"Body": 1.0})
    weigh(lows["Canals"], canal)
    for k in range(4):
        names = ["Body"] + ["A%d%s" % (k, tag) for tag in "abc"]
        weigh(lows["Arm%d" % k], [chain_weight(names, (0.02,) + ARM_KNOTS, float(u)) for u in META["ArmU%d" % k]])
    tent = []
    for which, g in zip(META["TentWhich"], META["TentF"]):
        key = TENTS[int(which)]
        tent.append(chain_weight(["T%s%s" % (key, tag) for tag in "abc"], TENT_KNOTS, float(g)))
    weigh(lows["Tents"], tent)
    glass = lows.pop("Glass")
    rigid(glows["Clover"], "Nebula")
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body, glass] + list(glows.values()))
    return body, glass


# poses in the game's axes (+X turn: a limb's far end swings forward; +Y: turns to its left; +Z rolls): the same numbers its animation uses
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def rim_pose(rad, apex=0.0):
    """Every rim section turned on its own tangent: positive draws the margin in."""
    out = {"Apex": ((0, 0, 1), 0, (0, 0, apex))}
    for k in range(8):
        c, s = math.cos(RIM_TH[k]), math.sin(RIM_TH[k])
        out["Rim%d" % k] = ((-s, c, 0), math.degrees(rad), (0, 0, 0))
    return out


def trail(rx, per=1.0):
    out = {}
    for key in TENTS:
        for tag, m in zip("abc", (0.5, 1.0, 1.2)):
            out["T%s%s" % (key, tag)] = game_turn(rx * m * per, 0, 0)
    for k in range(4):
        for tag, m in zip("abc", (0.5, 0.9, 1.1)):
            out["A%d%s" % (k, tag)] = game_turn(rx * m * per * 0.7, 0, 0)
    return out


def pose_library():
    return {"Contract": {**rim_pose(0.42, 0.05), **trail(0.12)}, "Flare": {**rim_pose(-0.22, -0.02), **trail(-0.1)}, "Streaming": {"Body": game_turn(-0.5, 0, 0), **rim_pose(0.14), **trail(-0.34)},
            "Spin": {"Nebula": game_turn(0, 1.3, 0)}, "Sway": {("T%sb" % key): game_turn(0.2, 0.3, 0.2) for key in TENTS}}


if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    mat = hi_material(ao_distance=0.06, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.26, 0.30, 0.40, 1))
    lows = build_low(pieces, data)
    material = glows["Clover"].data.materials[0]
    bpy.data.objects.remove(glows["Clover"], do_unlink=True)
    glows["Clover"] = build_clover(tree_of(lows["Skin"]), N + "Clover_Glow_ffb04a", HI, 5, 0.006)      # on the game mesh itself
    glows["Clover"].data.materials.append(material)
    glows["Clover"].visible_shadow = False
    TEXELS_ALL = dict(TEXELS)
    unwrap(lows, [(None, HEART_DENSITY)], {}, shape="CONCAVE", angle=52, texels=TEXELS_ALL, margin=0.006, own_uv={"Glass": glass_uv})
    arm_reach = {"Arm%d" % k: (0.03, 0.07) for k in range(4)}
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.4, 0.3, 0.55, 1), far=("Skin",), reach=(0.012, 0.03), far_reach=(0.022, 0.06), reaches={"Glass": (0.018, 0.045), "Canals": (0.014, 0.03), "Stem": (0.02, 0.05), "Tents": (0.012, 0.028), **arm_reach})
    baked = lows["Glass"].data.materials[0]
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton(data)
    body, glass = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    print("GLASS tris", sum(len(p.vertices) - 2 for p in glass.data.polygons), "dims", tuple(round(v, 2) for v in glass.dimensions), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), max(len(v.groups) for v in glass.data.vertices), flush=True)
    print("UV OVERLAP TEXELS body", uv_overlap_texels(body.data, 1024), "glass", uv_overlap_texels(glass.data, 1024), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    show = see_through(baked, GLASS_SHOW)
    glass.data.materials[0] = show
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=8.2, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS body", name, row, flush=True)
    for name, row in pet_kit.stress_report(rig, glass, {k: lib[k] for k in ("Contract", "Flare", "Streaming")}).items():
        print("STRESS glass", name, row, flush=True)
    wide = (0.72, -0.62, 0.15, 7.6, VIEW_AT)
    close = (0.2, -0.95, 0.02, 2.6, (0, -0.3, 1.66))
    for name, view in (("Contract", wide), ("Flare", wide), ("Streaming", (1, 0.05, 0.1, 7.6, VIEW_AT)), ("Spin", (0, -0.3, 1, 3.2, (0, 0, 1.85))), ("Sway", wide)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    os.makedirs(pet_kit.TOOLS, exist_ok=True)
    out = pet_kit.preview_dir()
    shots(os.path.join(out, PET + "_preview"), [(0.62, -0.72, 0.28, 7.6, VIEW_AT)])
    os.replace(os.path.join(out, PET + "_preview_0.png"), os.path.join(out, PET + "_preview.png"))
    glass.data.materials[0] = baked
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = pet_kit.save_blend()      # before the export, which takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values()), extras=[glass]), flush=True)
    print("DONE", flush=True)

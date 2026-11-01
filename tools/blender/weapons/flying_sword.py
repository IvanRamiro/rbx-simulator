"""The flying sword (run inside Blender): the sword a cultivator rides in sword flight
(src/server/FlightService). Its idea is a blade whose cutting edge is Qi: an original design,
built so its identity is in the shape, readable from above while it is ridden.

- The spine: a narrow dark-gold blade down the middle, ridged, with cloud scrolls raised along it.
- The Qi edge (the "Edge" glow piece): translucent glowing Qi forming the whole cutting edge,
  narrow at the guard and flaring wider toward the tip in soft flame licks; the point itself is
  pure Qi, reaching past the spine. Recoloured in game to the rider's realm.
- A bright inlaid line (the "Core" glow piece) along each side of the spine's top.
- The hilt, gold and white like the owner's Murim robes: a guard of flame-cloud wings swept back
  round a white-jade disc in a gold rim, a white silk grip bound in gold cord, and a gold flame
  finial for a pommel. (The ribbon streaming from it is a Trail added in game.)

Authored in Roblox studs, lying flat, its tip toward -Z (the rider's front), its flat face up:
the origin is where the rider's feet stand, on the spine. Built like the eggs: high-detail pieces
with procedural shaders baked onto one game mesh (egg_bake.py); the glow pieces are separate.

    import flying_sword as S
    S.build()        # the high-detail sword, in collection FlyingSwordHi
    S.export()       # bake and write assets/weapons/FlyingSword.fbx and its maps
"""
import math
import os

import bpy
from mathutils import Vector

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(W.REPO, "assets", "weapons")
NAME = "FlyingSword"
EDGE = "4b8cff"          # the Qi edge as exported (the game sets the realm's colour)
CORE = "9cc4ff"          # the inlaid lines

GUARD_Z = 1.9            # where the blade meets the guard (the hilt runs on toward +Z)
SPINE_TIP_Z = -3.55      # where the spine ends; the Qi edges meet in a point beyond it
TIP_Z = -4.45
THICK = 0.13             # the spine's thickness at its ridge
TOP = THICK / 2          # its top: where the feet stand


def t_of(z):
    return (GUARD_Z - z) / (GUARD_Z - TIP_Z)


def spine_half(z):
    """The spine's half-width: narrowing from the guard, closing to a point at SPINE_TIP_Z."""
    t = (GUARD_Z - z) / (GUARD_Z - SPINE_TIP_Z)
    if t >= 1:
        return 0.0
    w = 0.22 * (1 - 0.3 * t)
    if t > 0.8:
        w *= math.sqrt(max(0.0, 1 - ((t - 0.8) / 0.2) ** 2))
    return max(0.0, w)


def edge_outer(z):
    """How far the Qi edge reaches from the blade's centre line: narrow at the guard, flaring
    toward the tip in four flame licks, then sweeping in to the point."""
    t = t_of(z)
    base = 0.27 + 0.26 * (t ** 1.4)
    licks = 0.07 * max(0.0, math.sin(t * 4 * math.pi + 0.6)) ** 2 * min(1.0, t * 3)
    w = base + licks
    tip = 0.72
    if t > tip:
        f = (t - tip) / (1 - tip)
        w *= math.cos(f * math.pi / 2) ** 0.8
    return max(0.0, w)


def spine(hi):
    """The spine's cross-section: a flat-topped ridge bevelled down to its sides, where the Qi
    edges meet it."""
    n = 80
    zs = [GUARD_Z - (GUARD_Z - SPINE_TIP_Z) * i / n for i in range(n + 1)]

    def section(z):
        w = max(spine_half(z), 0.002)
        k = w / 0.22
        t, r = TOP * max(0.25, k), 0.06 * k
        return [(-w, -t * 0.55), (-w, t * 0.55), (-r, t), (r, t), (w, t * 0.55), (w, -t * 0.55), (r, -t), (-r, -t)]
    rows = [[hi.v(V((x, y, z))) for x, y in section(z)] for z in zs]
    m = 8
    for j in range(n):
        sec = section(zs[j])
        for i in range(m):
            i2 = (i + 1) % m
            out = V((sec[i][0] + sec[i2][0], sec[i][1] + sec[i2][1], 0))
            if out.length < 1e-6:
                out = V((0, 1, 0))
            hi.facing([rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]], [(i / m, j / n), ((i + 1) / m, j / n),
                      ((i + 1) / m, (j + 1) / n), (i / m, (j + 1) / n)], (out.x, out.y, 0), 0)
    c = hi.v(V((0, 0, GUARD_Z)))
    for i in range(m):
        hi.facing([rows[0][(i + 1) % m], rows[0][i], c], [(0, 0), (1, 0), (0.5, 0)], (0, 0, 1), 0)


def scrolls(hi):
    """Cloud scrolls raised along the spine's top: a curl, alternating sides, with a sweeping tail."""
    for k in range(7):
        zc = GUARD_Z - 0.45 - k * 0.66
        w = spine_half(zc)
        if w < 0.12:
            continue
        side = 1 if k % 2 == 0 else -1
        size = w / 0.22
        pts = []
        for i in range(26):
            a = TAU * 1.3 * i / 25
            r = 0.13 * (1 - 0.75 * i / 25) * size
            pts.append(V((side * (0.03 + r * math.cos(a)) * size, TOP + 0.014, zc + r * math.sin(a))))
        Hm.htube(hi, pts, lambda t: 0.022 * (1 - 0.4 * t), sides=6, per=1, uv_scale=3.0, tip=True, wobble=0.0)
        # a sweeping stroke leading back to the next curl, so the scrolls read as one cloud band
        Hm.htube(hi, [V((side * 0.16 * size, TOP + 0.014, zc)), V((0.0, TOP + 0.014, zc + 0.3)), V((-side * 0.1 * size, TOP + 0.014, zc + 0.6))],
                 lambda t: 0.018 * (1 - 0.6 * t), sides=6, per=6, uv_scale=3.0, tip=True, wobble=0.0)


def qi_edges(hi):
    """Both Qi edges as one piece: from the spine's side out to the flame-licked edge, thick at the
    spine, thin at the edge; beyond the spine's end they meet in the point."""
    n = 110
    zs = [GUARD_Z - 0.02 - (GUARD_Z - 0.02 - TIP_Z) * i / n for i in range(n + 1)]
    for side in (-1, 1):
        top_in, top_out, bot_in, bot_out = [], [], [], []
        for z in zs:
            inner = max(spine_half(z) - 0.01, 0.0)
            outer = max(edge_outer(z), inner + 0.002)
            ti = TOP * 0.5 * max(0.3, spine_half(z) / 0.22 + 0.3)
            top_in.append(hi.v(V((side * inner, ti, z))))
            bot_in.append(hi.v(V((side * inner, -ti, z))))
            top_out.append(hi.v(V((side * outer, 0.008, z))))
            bot_out.append(hi.v(V((side * outer, -0.008, z))))
        for j in range(n):
            uv = [(0, j / n), (1, j / n), (1, (j + 1) / n), (0, (j + 1) / n)]
            hi.facing([top_in[j], top_out[j], top_out[j + 1], top_in[j + 1]], uv, (0, 1, 0), 0)
            hi.facing([bot_in[j], bot_out[j], bot_out[j + 1], bot_in[j + 1]], uv, (0, -1, 0), 0)
            hi.facing([top_out[j], bot_out[j], bot_out[j + 1], top_out[j + 1]], uv, (side, 0, 0), 0)
        hi.facing([top_in[0], top_out[0], bot_out[0], bot_in[0]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, 1), 0)


def core_lines(hi):
    """A bright line inlaid along each side of the spine's top."""
    n = 60
    for side in (-1, 1):
        left, right = [], []
        for i in range(n + 1):
            z = GUARD_Z - 0.15 - (GUARD_Z - 0.15 - (SPINE_TIP_Z + 0.5)) * i / n
            k = spine_half(z) / 0.22
            x = side * spine_half(z) * 0.78
            y = TOP * 0.62 * max(0.3, k) + 0.006
            left.append(hi.v(V((x - 0.018 * k, y, z))))
            right.append(hi.v(V((x + 0.018 * k, y, z))))
        for i in range(n):
            hi.facing([left[i], right[i], right[i + 1], left[i + 1]], [(0, 0), (1, 0), (1, 1), (0, 1)], (side * 0.4, 1, 0), 0)


def guard(gold, jade):
    """Flame-cloud wings swept back from a white-jade disc set in a gold rim."""
    zc = GUARD_Z + 0.16
    rim = [V((0.27 * math.sin(TAU * i / 40), 0.0, zc + 0.27 * math.cos(TAU * i / 40))) for i in range(40)]
    Hm.htube(gold, rim + rim[:2], lambda t: 0.07, sides=10, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    for sign in (1, -1):
        ring = [jade.v(V((0.24 * math.sin(TAU * i / 32), sign * 0.06, zc + 0.24 * math.cos(TAU * i / 32)))) for i in range(32)]
        c = jade.v(V((0, sign * 0.1, zc)))
        for i in range(32):
            jade.facing([ring[i], ring[(i + 1) % 32], c], [(0, 0), (1, 0), (0.5, 1)], (0, sign, 0), 0)
    edge_top = [jade.v(V((0.24 * math.sin(TAU * i / 32), 0.06, zc + 0.24 * math.cos(TAU * i / 32)))) for i in range(32)]
    edge_bot = [jade.v(V((0.24 * math.sin(TAU * i / 32), -0.06, zc + 0.24 * math.cos(TAU * i / 32)))) for i in range(32)]
    for i in range(32):
        i2 = (i + 1) % 32
        out = V((math.sin(TAU * (i + 0.5) / 32), 0, math.cos(TAU * (i + 0.5) / 32)))
        jade.facing([edge_top[i], edge_top[i2], edge_bot[i2], edge_bot[i]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(out), 0)
    # the wings: two broad flame tongues each, out from the rim and sweeping back toward the hilt,
    # their tips curling up and in (thin tongues read as spider legs)
    for side in (-1, 1):
        for k, (reach, back, r) in enumerate(((0.62, 0.42, 0.13), (0.42, 0.62, 0.1))):
            pts = []
            for i in range(16):
                t = i / 15
                x = side * (0.22 + reach * math.sin(t * math.pi * 0.6) - 0.12 * t ** 3)
                z = zc - 0.12 + 0.08 * k + back * t ** 1.6
                y = 0.04 + 0.14 * t ** 2
                pts.append(V((x, y, z)))
            Hm.htube(gold, pts, lambda t, r=r: r * (1 - 0.85 * t ** 1.3), sides=10, per=2, uv_scale=3.0, tip=True, wobble=0.0)


def hilt(gold, silk):
    z0 = GUARD_Z + 0.42
    grip = 1.15
    Hm.htube(silk, [V((0, 0, z0)), V((0, 0, z0 + grip / 2)), V((0, 0, z0 + grip))], lambda t: 0.13, sides=14, per=6, uv_scale=6.0, tip=False, wobble=0.0)
    for zz in (z0, z0 + grip):
        Hm.htube(gold, [V((0, 0, zz - 0.07)), V((0, 0, zz + 0.07))], lambda t: 0.16, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    cord = [V((0.138 * math.cos(TAU * 5 * i / 120), 0.138 * math.sin(TAU * 5 * i / 120), z0 + 0.08 + (grip - 0.16) * i / 120)) for i in range(121)]
    Hm.htube(gold, cord, lambda t: 0.018, sides=5, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    # the flame finial: three tongues rising back from a gold bulb
    zp = z0 + grip + 0.14
    Hm.htube(gold, [V((0, 0, z0 + grip)), V((0, 0, zp)), V((0, 0, zp + 0.06))], lambda t: 0.12 * math.sin(math.pi * (0.25 + 0.75 * t)) + 0.04,
             sides=12, per=3, uv_scale=3.0, tip=False, wobble=0.0)
    for k, a in enumerate((-0.5, 0.0, 0.5)):
        length = 0.42 if k == 1 else 0.3
        pts = [V((math.sin(a) * 0.06, 0.02, zp + 0.05)), V((math.sin(a) * 0.14, 0.05, zp + length * 0.5)),
               V((math.sin(a) * 0.12 - a * 0.05, 0.12, zp + length))]
        Hm.htube(gold, pts, lambda t: 0.06 * (1 - 0.85 * t), sides=8, per=4, uv_scale=3.0, tip=True, wobble=0.0)


def mat_dark_gold(name="SwordDarkGold"):
    """Dark antique gold for the spine: deep bronze-gold, lighter on the raised parts."""
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 22.0, "Detail": 4.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.24, 0.14, 0.04)), (0.7, (0.42, 0.26, 0.08))])
    col = g.ao(col, 0.04, 0.45)
    return g.finish(col, 0.34, 0.5, g.bump(n.outputs["Fac"], 0.08, 0.003))


def mat_white_silk(name="SwordGripSilk"):
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 60.0, "Detail": 2.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.3), (0.86, 0.84, 0.8), (0.7, 0.68, 0.66))
    return g.finish(g.ao(col, 0.03, 0.5), 0.5, 0.0)


def mat_white_jade(name="SwordWhiteJade"):
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 5.0, "Distortion": 1.2})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.35, (0.82, 0.86, 0.8)), (0.7, (0.92, 0.94, 0.9))])
    return g.finish(g.ao(col, 0.03, 0.55), 0.15, 0.0)


def build():
    root = W.collection(NAME + "Hi")
    W.clear_collection(root)
    spine_hi, scroll_hi, gold, silk, jade = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    edge, core = Hm.Hi(), Hm.Hi()
    spine(spine_hi)
    scrolls(scroll_hi)
    guard(gold, jade)
    hilt(gold, silk)
    qi_edges(edge)
    core_lines(core)
    hi = [spine_hi.object("FS_Spine", root, [mat_dark_gold()], smooth=False), scroll_hi.object("FS_Scrolls", root, [Hm.mat_gold()]),
          gold.object("FS_Gold", root, [Hm.mat_gold()]), silk.object("FS_Grip", root, [mat_white_silk()]),
          jade.object("FS_Jade", root, [mat_white_jade()], smooth=False)]
    for o in hi:
        o["keep"] = True
    e = edge.object("FS_Edge", root, [K.glow_material(EDGE)], smooth=True)
    c = core.object("FS_Core", root, [K.glow_material(CORE)], smooth=False)
    return hi, {EDGE: [e], CORE: [c]}, root


def export():
    hi, glow, root = build()
    old = bpy.data.objects.get(NAME + "_Body")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(NAME, hi, root, 9000)
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        B.bake(NAME, hi, low, size=1024, small=512)
        parts = B.export(NAME, low, glow, root)
    finally:
        B.EGG_DIR = saved
    centres = {}
    for p in parts:
        pts = [V(K.rb_inv(*(p.matrix_world @ v.co))) for v in p.data.vertices]
        lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
        hi_ = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
        centres[p.name] = ([round(c, 4) for c in (lo + hi_) / 2], [round(c, 4) for c in hi_ - lo], B.tris(p))
    return centres

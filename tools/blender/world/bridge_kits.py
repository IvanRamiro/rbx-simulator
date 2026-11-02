"""Themed kits for the bridges between the islands (run inside Blender), built like the eggs:
high-detail pieces with procedural Cycles shaders, baked (egg_bake) onto one game mesh per kit,
then split back into one mesh per piece that all wear the kit's baked maps. Glowing parts stay
separate pieces named "<Piece>_Glow_<rrggbb>" (Neon in the game).

Every kit is built to the bridges' measures (layout.py): a deck DECK_WIDTH studs wide whose top is
at y = 0, the deck section SECTION studs long from z = +SECTION/2 to -SECTION/2 (the builder
stretches it to each piece of the walkable deck). Pieces are authored in Roblox space (x right,
y up, z toward the viewer) round their own origin, then built side by side along X, PIECE_GAP
studs apart, so one bake covers them all.

    import bridge_kits as BK
    BK.build("Jade")          # the high-detail pieces, in collection JadeBridgeHi
    BK.export("Jade")         # bake and export assets/world/Bridges/JadeBridge.fbx (+ maps), and
                              # write src/worldbuild/Placements/BridgeKits.lua (piece offsets)
    BK.export("Moon", extra=True)   # the level deck added later: MoonBridgeExtra.fbx

Kits:
- Jade (Jade Grove): a plank walk on two stringers, jade posts with carved caps, wooden rails with
  vines and leaves winding along the top rail; under it every few sections a cross-beam whose roots
  curl down to a hanging jade lantern; at the start a gate of jade pillars under a pagoda lintel.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "eggs")):
    if p not in sys.path:
        sys.path.insert(0, p)
import egg_bake as B  # noqa: E402
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402
import layout as L  # noqa: E402

W = K.W
V = Vector
TAU = math.tau
DECK_WIDTH = L.DECK_WIDTH
SECTION = L.SEGMENT
PIECE_GAP = 60
OUT_DIR = os.path.join(W.REPO, "assets", "world", "Bridges")


# ---------- geometry ----------
def box(hi, centre, size, mat=0, yaw=0.0, pitch=0.0, roll=0.0):
    """A box (Roblox space): `size` (x, y, z) round `centre`, turned by yaw (about y), then
    pitch (about x) and roll (about z), in radians."""
    cx, cy, cz = centre
    sx, sy, sz = (s / 2 for s in size)

    def turn(x, y, z):
        y, z = y * math.cos(pitch) - z * math.sin(pitch), y * math.sin(pitch) + z * math.cos(pitch)
        x, y = x * math.cos(roll) - y * math.sin(roll), x * math.sin(roll) + y * math.cos(roll)
        x, z = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)
        return x + cx, y + cy, z + cz

    corners = [turn(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    idx = [hi.v(c) for c in corners]
    faces = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]
    for f, n in faces:
        out = turn(*n)
        out = (out[0] - cx, out[1] - cy, out[2] - cz)
        hi.facing([idx[i] for i in f], [(0, 0), (1, 0), (1, 1), (0, 1)], out, mat)


def prism(hi, centre, radius, height, sides=8, mat=0, taper=1.0, yaw=0.0):
    """An upright prism (Roblox space), its bottom at centre's y, its top `taper` times as wide."""
    cx, cy, cz = centre
    bot = [hi.v((cx + math.cos(yaw + TAU * k / sides) * radius, cy, cz + math.sin(yaw + TAU * k / sides) * radius)) for k in range(sides)]
    top = [hi.v((cx + math.cos(yaw + TAU * k / sides) * radius * taper, cy + height, cz + math.sin(yaw + TAU * k / sides) * radius * taper)) for k in range(sides)]
    for k in range(sides):
        a = yaw + TAU * (k + 0.5) / sides
        hi.facing([bot[k], bot[(k + 1) % sides], top[(k + 1) % sides], top[k]], [(0, 0), (1, 0), (1, 1), (0, 1)], (math.cos(a), 0, math.sin(a)), mat)
    hi.facing(bot[::-1], [(0, 0)] * sides, (0, -1, 0), mat)
    hi.facing(top, [(0, 0)] * sides, (0, 1, 0), mat)


def curved_beam(hi, ox, span, y, lift, height, depth, segments=24, mat=0, z=0.0):
    """A beam across `span` studs centred on ox, its top line rising by `lift` toward both ends
    (y + lift * |2t - 1|^3), one smooth piece (no steps at the joints)."""
    rings = []
    for k in range(segments + 1):
        t = k / segments
        x = ox - span / 2 + span * t
        yc = y + lift * (abs(t * 2 - 1) ** 3)
        rings.append([hi.v((x, yc + dy, z + dz)) for dy, dz in ((-height / 2, -depth / 2), (height / 2, -depth / 2), (height / 2, depth / 2), (-height / 2, depth / 2))])
    for k in range(segments):
        a, b = rings[k], rings[k + 1]
        for f in range(4):
            g = (f + 1) % 4
            hi.facing([a[f], b[f], b[g], a[g]], [(0, 0), (1, 0), (1, 1), (0, 1)], _face_out(f), mat)
    hi.facing(rings[0][::-1], [(0, 0)] * 4, (-1, 0, 0), mat)
    hi.facing(rings[-1], [(0, 0)] * 4, (1, 0, 0), mat)


def _face_out(f):
    # the side between corners f and f+1 of the cross-section (bottom-back, top-back, top-front, bottom-front)
    return [(0, 0, -1), (0, 1, 0), (0, 0, 1), (0, -1, 0)][f]


def chamfer(obj, width=0.08, segments=1):
    """Bevel the hard edges (they catch the light like worked wood and stone) and keep the piece
    whole in the game mesh: simple solids are cheap, and decimating them leaves the bake nothing to
    hit (black streaks)."""
    obj["keep"] = True
    return Hm.apply_modifiers(obj, [("BEVEL", {"width": width, "segments": segments, "limit_method": "ANGLE"})])


def vine(hi_vine, hi_leaf, start, end, seed, turns=3.0, radius=0.32, leaf_every=0.45, thickness=0.09, leaf=(0.55, 0.85)):
    """A vine winding round a rail (or down a pillar) from start to end (Roblox space), full of leaves."""
    rnd = random.Random(seed)
    s, e = V(start), V(end)
    axis = e - s
    length = axis.length
    d = axis.normalized()
    ref = V((0, 1, 0)) if abs(d.y) < 0.9 else V((1, 0, 0))
    side = d.cross(ref).normalized()
    up = side.cross(d).normalized()
    pts = []
    n = max(8, int(length * 2))
    for i in range(n + 1):
        t = i / n
        a = TAU * turns * t + seed
        r = radius * (0.85 + 0.3 * math.sin(t * 11 + seed))
        pts.append(tuple(s + axis * t + side * math.cos(a) * r + up * math.sin(a) * r))
    Hm.htube(hi_vine, pts, lambda t: thickness * (1.15 - 0.45 * t), sides=6, per=2, uv_scale=3.0, tip=True, seed=seed)
    k = 0.0
    while k < length:
        t = k / length
        a = TAU * turns * t + seed
        base = s + axis * t + side * math.cos(a) * radius + up * math.sin(a) * radius
        out = (side * math.cos(a) + up * math.sin(a)).normalized()
        direction = (out + d * rnd.uniform(-0.4, 0.6) + V((0, rnd.uniform(-0.5, 0.4), 0))).normalized()
        normal = (V((0, 1, 0)) + out * 0.4).normalized()
        Hm.leaf(hi_leaf, tuple(base), tuple(direction), tuple(normal), rnd.uniform(*leaf), rnd.uniform(0.2, 0.3),
                fold=0.2, curl=0.3, twist=rnd.uniform(-0.6, 0.6), steps=6, across=2)
        k += leaf_every * rnd.uniform(0.7, 1.3)


def hanging_vine(hi_vine, hi_leaf, top, drop, seed, sway=0.6):
    """A vine trailing down from `top` for `drop` studs, swaying, leaves along it."""
    rnd = random.Random(seed)
    t0 = V(top)
    pts = [tuple(t0 + V((math.sin(i * 0.9 + seed) * sway * i / 6, -drop * i / 6, math.cos(i * 0.7 + seed) * sway * 0.5 * i / 6))) for i in range(7)]
    Hm.htube(hi_vine, pts, lambda t: 0.07 * (1 - 0.5 * t), sides=6, per=4, uv_scale=3.0, tip=True, seed=seed)
    curve = [V(p) for p in W.catmull(pts, 4)]
    for i in range(1, len(curve) - 1, 2):
        c = curve[i]
        a = rnd.uniform(0, TAU)
        out = V((math.cos(a), 0, math.sin(a)))
        Hm.leaf(hi_leaf, tuple(c), tuple((out + V((0, -0.4, 0))).normalized()), (0, 1, 0), rnd.uniform(0.5, 0.8), rnd.uniform(0.2, 0.28),
                fold=0.2, curl=0.3, twist=rnd.uniform(-0.6, 0.6), steps=6, across=2)


# ---------- materials (scaled for studs, not eggs) ----------
def mat_planks(name="BridgePlanks", along="X", tones=None):
    """Weathered planks: long grain along `along` (X across the deck, Y for beams running down the
    bridge), a tone per plank (each its own mesh island), dark knots, worn pale edges, crevices
    darkened."""
    g = Hm._Graph(name)
    co = g.coords()
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.12, 2.2, 2.2) if along == "X" else (2.2, 0.12, 2.2)
    g.link(co, mp.inputs["Vector"])
    grain = g.n("ShaderNodeTexWave", wave_type="RINGS", **{"Scale": 1.0, "Distortion": 6.0, "Detail": 6.0, "Detail Scale": 1.4})
    g.link(mp.outputs[0], grain.inputs["Vector"])
    geo = g.n("ShaderNodeNewGeometry")
    tones = tones or [(0.0, (0.19, 0.1, 0.045)), (0.35, (0.3, 0.17, 0.075)), (0.7, (0.4, 0.25, 0.11)), (1.0, (0.5, 0.33, 0.16))]
    tone = g.ramp(geo.outputs["Random Per Island"], tones)
    col = g.mix(g.math("MULTIPLY", grain.outputs["Fac"], 0.4), tone, (0.14, 0.07, 0.03))
    knots = g.n("ShaderNodeTexVoronoi", feature="F1", **{"Scale": 0.9})
    g.link(co, knots.inputs["Vector"])
    knot = g.math("LESS_THAN", knots.outputs["Distance"], 0.05)
    col = g.mix(g.math("MULTIPLY", knot, 0.8), col, (0.08, 0.04, 0.02))
    wear = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 5.0})
    g.link(co, wear.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", wear.outputs["Fac"], 0.55, clamp=True), 1.0), col, (0.55, 0.42, 0.28))
    col = g.ao(col, 0.25, 0.25)
    bevel = g.n("ShaderNodeBevel", samples=8)
    bevel.inputs["Radius"].default_value = 0.05
    nrm = g.bump(g.math("ADD", grain.outputs["Fac"], g.math("MULTIPLY", knot, 0.6)), 0.5, 0.02, bevel.outputs["Normal"])
    return g.finish(col, 0.8, 0.0, nrm)


def mat_jade_stone(name="BridgeJade"):
    """Carved jade for posts and pillars: Hm.mat_jade's marbling, a little coarser for studs."""
    return Hm.mat_jade(name)


def rescale(mat, factor):
    """Coarsen an egg material for bridge scale: every Object-coordinate input is divided by
    `factor` (the egg shaders' detail is sized for 4-stud eggs, a bridge is 20 studs across)."""
    t = mat.node_tree
    for nd in list(t.nodes):
        if nd.type != "TEX_COORD":
            continue
        for link in list(nd.outputs["Object"].links):
            mp = t.nodes.new("ShaderNodeVectorMath")
            mp.operation = "SCALE"
            mp.inputs["Scale"].default_value = 1.0 / factor
            to = link.to_socket
            t.links.remove(link)
            t.links.new(nd.outputs["Object"], mp.inputs[0])
            t.links.new(mp.outputs[0], to)
    return mat


def basalt(name, vein=(0.75, 0.18, 0.02), vein_hot=(1.0, 0.55, 0.1), heat=(0.07, 0.022, 0.016), tones=None, factor=3.0, heat_reach=0.04):
    """Dark volcanic rock at bridge scale: Hm.mat_obsidian coarsened, its molten veins in patches,
    only the deepest crevices warmed (a wide heat turns the whole rock to hot clay)."""
    return rescale(Hm.mat_obsidian(name, tones=tones, vein=vein, vein_hot=vein_hot, heat=heat, heat_reach=heat_reach), factor)


# ---------- the Jade kit ----------
JADE_LANTERN = "38d97a"


def jade_deck(ox, mats):
    """One deck section: planks across on two stringers, edged by fascia boards; at its +z end a
    pair of jade posts (the next section's pair closes the other end); between them wooden rails
    with a lattice of slats; vines winding along the top rails and trailing over the edges."""
    rnd = random.Random(301)
    planks, beams, jade, vines, leaves = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    half = SECTION / 2
    n = 10
    pitch = SECTION / n
    edge = DECK_WIDTH / 2
    for k in range(n):
        z = half - pitch * (k + 0.5)
        length = DECK_WIDTH - 1.6 + rnd.uniform(-0.2, 0.2)
        box(planks, (ox + rnd.uniform(-0.1, 0.1), -0.2 + rnd.uniform(-0.03, 0.03), z), (length, 0.4, pitch - 0.14),
            yaw=rnd.uniform(-0.008, 0.008), roll=rnd.uniform(-0.006, 0.006))
    for x in (-edge + 0.4, edge - 0.4):
        box(beams, (ox + x, -0.25, 0), (0.8, 1.1, SECTION + 0.02))             # fascia over the plank ends
    for x in (-DECK_WIDTH * 0.33, 0.0, DECK_WIDTH * 0.33):
        box(beams, (ox + x, -1.1, 0), (1.0, 1.2, SECTION + 0.02))              # stringers
    box(beams, (ox, -1.25, 0), (DECK_WIDTH - 2.0, 0.8, 1.0))                   # a cross-tie
    rail_x = edge - 0.45
    for side in (-1, 1):
        x = ox + side * rail_x
        prism(jade, (x, -0.8, half), 0.62, 4.1, sides=8, taper=0.9, yaw=math.pi / 8)
        prism(jade, (x, 3.3, half), 0.85, 0.45, sides=8, taper=1.0, yaw=math.pi / 8)
        prism(jade, (x, 3.75, half), 0.65, 0.7, sides=8, taper=0.12, yaw=math.pi / 8)
        prism(jade, (x, 0.2, half), 0.78, 0.35, sides=8, taper=1.0, yaw=math.pi / 8)     # a carved band low on the post
        box(beams, (x, 3.0, 0), (0.6, 0.5, SECTION + 0.02))                    # top rail
        box(beams, (x, 0.75, 0), (0.45, 0.4, SECTION + 0.02))                  # bottom rail
        for k in range(1, 10):                                                 # the lattice of slats
            z = half - SECTION * k / 10
            box(beams, (x, 1.85, z), (0.22, 1.85, 0.22))
        box(beams, (x, 1.85, 0), (0.18, 0.18, SECTION - 0.6))                  # and a rail through their middles
        vine(vines, leaves, (x, 3.05, half - 0.7), (x, 3.05, -half + 0.3), seed=11 + side, turns=2.4, radius=0.4)
        for k, z in enumerate((half - 3.0, -1.0 + rnd.uniform(-1, 1), -half + 2.4)):
            hanging_vine(vines, leaves, (x + side * 0.5, -0.3, z), rnd.uniform(2.5, 5.5), seed=30 + k * 7 + side)
    objs = [planks.object("JadeDeck_Planks", mats.coll, [mats.planks], smooth=False),
            beams.object("JadeDeck_Beams", mats.coll, [mats.beams], smooth=False),
            jade.object("JadeDeck_Jade", mats.coll, [mats.jade], smooth=False),
            vines.object("JadeDeck_Vines", mats.coll, [mats.vine]),
            leaves.object("JadeDeck_Leaves", mats.coll, [mats.leaf])]
    for o in objs[:3]:
        chamfer(o, 0.07)
    Hm.solidify(objs[4], 0.02)
    objs[4]["sheet"] = True
    return objs, []


def jade_support(ox, mats):
    """Under the deck: a heavy cross-beam braced to the stringers, whose two roots curl down and
    twine into a hanging jade lantern with a glowing core; vines trailing from it."""
    beams, jade, roots, leaves, glow = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    box(beams, (ox, -2.3, 0), (DECK_WIDTH - 0.5, 1.3, 1.4))
    for side in (-1, 1):
        box(beams, (ox + side * 4.2, -3.6, 0), (0.7, 3.6, 0.7), roll=side * 0.75)   # braces
        pts = [(ox + side * 8.0, -2.4, 0), (ox + side * 6.4, -4.0, 0.4), (ox + side * 3.5, -6.4, -0.3), (ox + side * 1.3, -8.3, 0.2), (ox + side * 0.4, -9.2, 0)]
        Hm.htube(roots, pts, lambda t: 0.55 * (1 - 0.5 * t), sides=10, per=6, uv_scale=2.0, tip=False, knots=4, seed=40 + side)
        vine(roots, leaves, (ox + side * 7.2, -3.0, 0.2), (ox + side * 1.4, -8.0, 0.0), seed=50 + side, turns=1.8, radius=0.62, leaf_every=0.4)
        hanging_vine(roots, leaves, (ox + side * 5.0, -2.9, 0.6), 4.5, seed=60 + side)
    # the lantern: a roofed cap, six jade ribs round a glowing core, a base and a finial
    prism(jade, (ox, -10.0, 0), 1.0, 0.8, sides=6, taper=0.6)
    prism(jade, (ox, -10.9, 0), 2.1, 0.9, sides=6, taper=0.45)
    for k in range(6):
        a = TAU * k / 6
        box(jade, (ox + math.cos(a) * 1.55, -13.4, math.sin(a) * 1.55), (0.36, 4.6, 0.36))
    prism(jade, (ox, -16.1, 0), 1.8, 0.7, sides=6, taper=1.15)
    prism(jade, (ox, -17.5, 0), 0.5, 1.4, sides=6, taper=1.9)
    prism(glow, (ox, -15.6, 0), 1.2, 4.6, sides=6, taper=1.0)
    hanging_vine(roots, leaves, (ox + 1.6, -16.2, 0.4), 3.0, seed=77)
    objs = [beams.object("JadeSupport_Beams", mats.coll, [mats.beams], smooth=False),
            jade.object("JadeSupport_Jade", mats.coll, [mats.jade], smooth=False),
            roots.object("JadeSupport_Roots", mats.coll, [mats.vine]),
            leaves.object("JadeSupport_Leaves", mats.coll, [mats.leaf])]
    chamfer(objs[0], 0.1)
    chamfer(objs[1], 0.06)
    Hm.solidify(objs[3], 0.02)
    objs[3]["sheet"] = True
    return objs, [glow.object("JadeSupport_Glow_" + JADE_LANTERN, mats.coll, [K.glow_material(JADE_LANTERN)], smooth=False)]


def jade_gate(ox, mats):
    """The gate at the bridge's start: two thick jade pillars on plinths, banded with carving and
    wound with vines, under a two-tier pagoda lintel with sweeping upturned ends, a jade panel
    between the tiers carrying a leaf emblem."""
    beams, jade, vines, leaves = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    px = DECK_WIDTH / 2 + 1.8
    for side in (-1, 1):
        x = ox + side * px
        box(jade, (x, -0.2, 0), (3.6, 1.6, 3.6))                               # plinth
        prism(jade, (x, 0.6, 0), 1.75, 1.0, sides=8, taper=0.82, yaw=math.pi / 8)
        prism(jade, (x, 1.6, 0), 1.35, 13.6, sides=8, taper=0.9, yaw=math.pi / 8)
        for y in (3.6, 8.6, 13.2):
            prism(jade, (x, y, 0), 1.5, 0.55, sides=8, taper=1.0, yaw=math.pi / 8)
        prism(jade, (x, 15.2, 0), 1.6, 0.8, sides=8, taper=1.1, yaw=math.pi / 8)  # capital
        vine(vines, leaves, (x + 0.3 * side, 1.2, 0.4), (x, 14.8, 0.3), seed=70 + side, turns=4.5, radius=1.45, leaf_every=0.35)
    curved_beam(beams, ox, DECK_WIDTH + 10.0, 16.6, 2.2, 1.3, 2.4)
    curved_beam(beams, ox, DECK_WIDTH + 13.0, 20.4, 3.2, 1.2, 3.0)
    box(jade, (ox, 18.4, 0), (DECK_WIDTH - 2.0, 2.2, 1.2))                     # the panel between the tiers
    for side in (-1, 1):
        box(beams, (ox + side * (DECK_WIDTH / 2 - 0.5), 18.4, 0), (0.8, 2.4, 1.6))
    disc = [jade.v((ox + math.cos(TAU * k / 20) * 2.3, 18.4 + math.sin(TAU * k / 20) * 2.3, 0.85)) for k in range(20)]
    back = [jade.v((ox + math.cos(TAU * k / 20) * 2.3, 18.4 + math.sin(TAU * k / 20) * 2.3, -0.85)) for k in range(20)]
    jade.facing(disc, [(0, 0)] * 20, (0, 0, 1))
    jade.facing(back[::-1], [(0, 0)] * 20, (0, 0, -1))
    for k in range(20):
        jade.facing([disc[k], back[k], back[(k + 1) % 20], disc[(k + 1) % 20]], [(0, 0), (1, 0), (1, 1), (0, 1)],
                    (math.cos(TAU * (k + 0.5) / 20), math.sin(TAU * (k + 0.5) / 20), 0))
    for z in (0.9, -0.9):
        Hm.leaf(leaves, (ox, 16.7, z), (0, 1, 0), (0, 0, z), 3.4, 1.1, fold=0.25, curl=0.05, steps=12, across=4)
    gold = Hm.Hi()
    for z in (0.95, -0.95):   # a gold rim round the emblem, both faces
        pts = [(ox + math.cos(TAU * k / 32) * 2.35, 18.4 + math.sin(TAU * k / 32) * 2.35, z) for k in range(33)]
        Hm.htube(gold, pts, lambda t: 0.17, sides=6, per=1, uv_scale=2.0, tip=False)
    objs = [beams.object("JadeGate_Beams", mats.coll, [mats.beams], smooth=False),
            jade.object("JadeGate_Jade", mats.coll, [mats.jade], smooth=False),
            vines.object("JadeGate_Vines", mats.coll, [mats.vine]),
            leaves.object("JadeGate_Leaves", mats.coll, [mats.leaf]),
            gold.object("JadeGate_Gold", mats.coll, [mats.gold], smooth=True)]
    objs[4]["keep"] = True
    chamfer(objs[0], 0.1)
    chamfer(objs[1], 0.07)
    Hm.solidify(objs[3], 0.03)
    objs[3]["sheet"] = True
    return objs, []


# ---------- the Ember kit ----------
EMBER_LAVA = "ff5a14"
HEX_R = 12 / (4 * math.sqrt(3))       # four rows of hexes per section: the pattern tiles from section to section


def ember_deck(ox, mats):
    """One deck section of basalt column tops, molten lava glowing in the seams between them (a
    glowing bed under the columns), edged by a wall of basalt columns of uneven heights."""
    rnd = random.Random(401)
    rock, glow = Hm.Hi(), Hm.Hi()
    half = SECTION / 2
    r = HEX_R
    col = 0
    x = -DECK_WIDTH / 2 + 1.8
    while x <= DECK_WIDTH / 2 - 1.8 + 1e-6:
        shift = (col % 2) * r * math.sqrt(3) / 2
        z = -half + shift
        while z < half - 1e-6:
            top = -rnd.uniform(0.0, 0.12)
            prism(rock, (ox + x, top - 1.4, z), r * 0.93, 1.4, sides=6, taper=0.98, yaw=0.0)
            z += r * math.sqrt(3)
        x += 1.5 * r
        col += 1
    box(glow, (ox, -0.55, 0), (DECK_WIDTH - 5.0, 0.3, SECTION))               # the molten bed showing through the seams (not out at the edges)
    box(rock, (ox, -1.9, 0), (DECK_WIDTH - 1.2, 1.0, SECTION))                 # the bridge's body under it
    for side in (-1, 1):
        k = 0
        z = half - 0.75
        while z > -half:
            h = rnd.uniform(2.3, 3.6)
            prism(rock, (ox + side * (DECK_WIDTH / 2 - 0.85), -2.2, z), 0.86, h + 2.2, sides=6, taper=0.97, yaw=rnd.uniform(0, 1))
            z -= 1.5
            k += 1
    objs = [rock.object("EmberDeck_Rock", mats.coll, [mats.rock], smooth=False)]
    chamfer(objs[0], 0.06)
    return objs, [glow.object("EmberDeck_Glow_" + EMBER_LAVA, mats.coll, [K.glow_material(EMBER_LAVA)], smooth=False)]


def ember_support(ox, mats):
    """Basalt columns hanging under the deck like the island's organ pipes, lava dripping from
    their tips."""
    rnd = random.Random(402)
    rock, glow = Hm.Hi(), Hm.Hi()
    spots = [(0, 0, 1.4, 12), (-2.6, 1.2, 1.1, 8), (2.5, -1.0, 1.2, 9.5), (-4.8, -0.8, 0.9, 5.5), (4.9, 0.9, 1.0, 6.5),
             (-1.3, -2.2, 0.9, 7), (1.4, 2.1, 0.85, 5), (-6.6, 0.4, 0.8, 4), (6.8, -0.3, 0.8, 3.5)]
    spread = DECK_WIDTH / 20                                                    # the cluster spreads with the deck
    for x, z, rr, length in spots:
        x *= spread
        prism(rock, (ox + x, -2.4 - length, z), rr, length, sides=6, taper=1.05, yaw=rnd.uniform(0, 1))
        prism(glow, (ox + x, -2.4 - length - 0.6, z), rr * 0.45, 0.65, sides=6, taper=1.6)   # a molten drip at the tip
    objs = [rock.object("EmberSupport_Rock", mats.coll, [mats.rock], smooth=False)]
    chamfer(objs[0], 0.08)
    return objs, [glow.object("EmberSupport_Glow_" + EMBER_LAVA, mats.coll, [K.glow_material(EMBER_LAVA)], smooth=False)]


def ember_gate(ox, mats):
    """Two towering clusters of basalt columns under a great basalt slab split by a molten crack,
    two columns leaning out from its ends like horns."""
    rnd = random.Random(403)
    rock, glow = Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        cx = ox + side * (DECK_WIDTH / 2 + 2.2)
        for dx, dz, rr, h in ((0, 0, 1.5, 17), (side * 1.9, 1.0, 1.1, 13.5), (side * 1.6, -1.3, 1.0, 11), (-side * 1.4, 1.2, 0.9, 9), (side * 0.2, -1.9, 0.9, 14.5)):
            prism(rock, (cx + dx, -1.0, dz), rr, h + 1.0, sides=6, taper=0.96, yaw=rnd.uniform(0, 1))
    box(rock, (ox, 17.4, 0), (DECK_WIDTH + 9.0, 2.8, 3.4))
    box(rock, (ox, 15.6, 0), (DECK_WIDTH + 4.0, 1.0, 2.6))
    # the molten crack down the slab's face, front and back
    pts = [(-DECK_WIDTH / 2 - 3.5, 17.6), (-6, 17.1), (-2.5, 17.9), (1.5, 17.0), (5.5, 17.7), (DECK_WIDTH / 2 + 3.5, 17.3)]
    for z in (1.72, -1.72):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            box(glow, (ox + (x0 + x1) / 2, (y0 + y1) / 2, z), (math.hypot(x1 - x0, y1 - y0) + 0.1, 0.32, 0.08), roll=math.atan2(y1 - y0, x1 - x0))
    for side in (-1, 1):
        prism(rock, (ox + side * (DECK_WIDTH / 2 + 3.0), 18.4, 0), 1.0, 5.5, sides=6, taper=0.55)
    objs = [rock.object("EmberGate_Rock", mats.coll, [mats.rock], smooth=False)]
    chamfer(objs[0], 0.1)
    return objs, [glow.object("EmberGate_Glow_" + EMBER_LAVA, mats.coll, [K.glow_material(EMBER_LAVA)], smooth=False)]


# ---------- the Moon kit ----------
MOON_GLOW = "b9a8ff"


def moon_slope():
    """The Moonlit stairway's flights all climb at one slope (layout.py): the stair section is
    built for it."""
    nodes = L.bridge_nodes("MoonlitRoute")
    best = 0.0
    for a, b in zip(nodes, nodes[1:]):
        d = math.hypot(b[0] - a[0], b[2] - a[2])
        best = max(best, math.atan2(abs(b[1] - a[1]), d))
    return best


def crescent(hi, centre, radius, width=0.42, start=0.25, end=0.75, segments=20, axis="z"):
    """A crescent moon: a tube along an arc that thickens in its middle, facing along `axis`."""
    cx, cy, cz = centre
    pts = []
    for k in range(segments + 1):
        a = math.pi * 2 * (start + (end - start) * k / segments)
        if axis == "z":
            pts.append((cx + math.cos(a) * radius, cy + math.sin(a) * radius, cz))
        elif axis == "y":
            pts.append((cx + math.cos(a) * radius, cy, cz + math.sin(a) * radius))
        else:
            pts.append((cx, cy + math.sin(a) * radius, cz + math.cos(a) * radius))
    Hm.htube(hi, pts, lambda t: width * (0.15 + 0.85 * math.sin(math.pi * t)), sides=8, per=1, uv_scale=2.0, tip=False)


def moon_stair(ox, mats):
    """One section of the stairway. Its treads and posts are built level (the world's frame) and then
    turned so the climb runs along the section's -z, as the builder lays it along the slope; its
    stringers and gold handrail are built straight in the section's own frame. Moonstone treads
    with gold nosings between the stringers, slim moonstone posts with gold crescents at its low
    end, a gold handrail."""
    from mathutils import Matrix, Vector as Vec
    theta = moon_slope()
    run, rise = SECTION * math.cos(theta), SECTION * math.sin(theta)
    n = max(4, round(rise / 0.75))
    stone, gold = Hm.Hi(), Hm.Hi()           # built level, then turned
    frame_stone, frame_gold = Hm.Hi(), Hm.Hi()   # built in the section's frame
    inner = DECK_WIDTH - 2.6
    for i in range(n):
        z0 = run / 2 - run * i / n
        z1 = run / 2 - run * (i + 1) / n
        top = -rise / 2 + rise * (i + 0.5) / n + 0.35   # the walking plane runs through the treads' middles
        box(stone, (ox, top - 0.9, (z0 + z1) / 2), (inner, 1.8, abs(z1 - z0) + 0.02))
        box(gold, (ox, top - 0.06, z0 - 0.12), (inner - 0.4, 0.14, 0.26))     # the gold nosing
    for side in (-1, 1):
        x = ox + side * (DECK_WIDTH / 2 - 0.65)
        prism(stone, (x, -rise / 2 + 0.6, run / 2 - 0.4), 0.36, 3.0, sides=8, taper=0.85)     # plumb once laid
        crescent(gold, (x, -rise / 2 + 4.0, run / 2 - 0.4), 0.55, width=0.16, axis="x")
        box(frame_stone, (x, -0.4, 0), (1.3, 2.6, SECTION + 0.02))           # stringer
        box(frame_gold, (x, 0.95, 0), (1.42, 0.14, SECTION + 0.02))          # its gold trim
        box(frame_gold, (x, 3.0, 0), (0.24, 0.24, SECTION + 0.02))           # handrail
    turned = [stone.object("MoonStair_Treads", mats.coll, [mats.stone], smooth=False),
              gold.object("MoonStair_Nosings", mats.coll, [mats.gold], smooth=False)]
    for o in turned:
        chamfer(o, 0.05)
        o.data.transform(Matrix.Translation(Vec((-ox, 0, 0))))
        o.data.transform(Matrix.Rotation(-theta, 4, "X"))  # checked: the risers come out plumb, the tread tops level
        o.data.transform(Matrix.Translation(Vec((ox, 0, 0))))
    framed = [frame_stone.object("MoonStair_Stringers", mats.coll, [mats.stone], smooth=False),
              frame_gold.object("MoonStair_Rails", mats.coll, [mats.gold], smooth=False)]
    for o in framed:
        chamfer(o, 0.05)
    return turned + framed, []


def moon_support(ox, mats):
    """Under the stairway: a moonstone crescent hanging on two gold chains, a moon lantern glowing
    in its arms."""
    stone, gold, glow = Hm.Hi(), Hm.Hi(), Hm.Hi()
    cy, cr = -9.5, 4.6                    # the crescent hangs below the deck, its horns up
    for side in (-1, 1):
        hx = ox + side * cr * math.cos(math.radians(14))   # the horn tips (the arc runs 194..346 deg)
        top, bottom = -1.0, cy - cr * math.sin(math.radians(14))
        links = max(3, int((top - bottom) / 0.8))
        for k in range(links):                                                 # chain links, alternating planes
            y = top - (top - bottom) * (k + 0.5) / links
            ring = [(hx + (math.cos(TAU * j / 12) * 0.26 if k % 2 else 0), y + math.sin(TAU * j / 12) * 0.48,
                     (math.cos(TAU * j / 12) * 0.26 if k % 2 == 0 else 0)) for j in range(13)]
            Hm.htube(gold, ring, lambda t: 0.08, sides=5, per=1, uv_scale=2.0, tip=False)
    crescent(stone, (ox, cy, 0), cr, width=1.15, start=0.54, end=0.96, segments=26, axis="z")
    crescent(gold, (ox, cy, 0.0), cr + 0.55, width=0.22, start=0.56, end=0.94, segments=26, axis="z")
    prism(glow, (ox, cy - 2.6, 0), 0.95, 1.9, sides=12, taper=0.5)            # a moon lantern cradled in its arms
    prism(gold, (ox, cy - 0.7, 0), 1.1, 0.25, sides=12, taper=0.8)
    objs = [stone.object("MoonSupport_Stone", mats.coll, [mats.stone]),
            gold.object("MoonSupport_Gold", mats.coll, [mats.gold])]
    objs[0]["keep"] = True
    objs[1]["keep"] = True
    return objs, [glow.object("MoonSupport_Glow_" + MOON_GLOW, mats.coll, [K.glow_material(MOON_GLOW)], smooth=False)]


def moon_gate(ox, mats):
    """The gate at the stairway's foot: two moonstone pillars ringed in gold, under a great gold
    crescent whose horns rise above them, a moon lantern at its heart."""
    stone, gold, glow = Hm.Hi(), Hm.Hi(), Hm.Hi()
    px = DECK_WIDTH / 2 + 1.6
    for side in (-1, 1):
        x = ox + side * px
        prism(stone, (x, -0.6, 0), 1.9, 1.2, sides=12, taper=0.85)
        prism(stone, (x, 0.6, 0), 1.25, 14.0, sides=12, taper=0.88)
        for y in (0.9, 7.0, 14.0):
            ring = [(x + math.cos(TAU * k / 24) * 1.25 * (1 - 0.12 * y / 14), y, math.sin(TAU * k / 24) * 1.25 * (1 - 0.12 * y / 14)) for k in range(25)]
            Hm.htube(gold, ring, lambda t: 0.14, sides=6, per=1, uv_scale=2.0, tip=False)
        prism(stone, (x, 14.6, 0), 1.6, 0.9, sides=12, taper=1.1)
    # a great crescent resting on the pillar caps, its horns rising past them
    span = px + 0.6
    cy = 15.5 - span * math.sin(math.radians(10))
    crescent(gold, (ox, cy, 0), span / math.cos(math.radians(10)), width=1.3, start=0.03, end=0.47, segments=44, axis="z")
    crescent(stone, (ox, cy, -0.3), span / math.cos(math.radians(10)) - 1.3, width=0.7, start=0.07, end=0.43, segments=40, axis="z")
    box(gold, (ox, 15.9, 0), (DECK_WIDTH + 2.0, 0.55, 0.9))                    # a gold beam between the caps
    for k in range(5):                                                         # a chain to the lantern
        ring = [(ox + (math.cos(TAU * j / 12) * 0.2 if k % 2 else 0), 15.4 - k * 0.6 + math.sin(TAU * j / 12) * 0.36,
                 (math.cos(TAU * j / 12) * 0.2 if k % 2 == 0 else 0)) for j in range(13)]
        Hm.htube(gold, ring, lambda t: 0.06, sides=5, per=1, uv_scale=2.0, tip=False)
    prism(gold, (ox, 12.2, 0), 1.0, 0.3, sides=12, taper=0.7)
    prism(glow, (ox, 10.0, 0), 0.75, 2.2, sides=12, taper=1.2)
    objs = [stone.object("MoonGate_Stone", mats.coll, [mats.stone]),
            gold.object("MoonGate_Gold", mats.coll, [mats.gold])]
    objs[0]["keep"] = True
    objs[1]["keep"] = True
    return objs, [glow.object("MoonGate_Glow_" + MOON_GLOW, mats.coll, [K.glow_material(MOON_GLOW)], smooth=False)]


# ---------- the Origin kit ----------
VOID_GLOW = "a35cff"


def ruin_stone(name, vein=(0.22, 0.08, 0.38), tones=None):
    """Ancient worn slate at bridge scale: Hm.mat_obsidian's plates and veins in the Origin Abyss's
    greys, the veins violet void light instead of lava, no heat in the crevices."""
    tones = tones or [(0.0, (0.022, 0.021, 0.027)), (0.5, (0.04, 0.038, 0.048)), (1.0, (0.07, 0.065, 0.08))]
    # the veins sparse and deep violet: the void light belongs in the cracks (the Neon pieces), not
    # scribbled over every face
    return rescale(Hm.mat_obsidian(name, tones=tones, vein=vein, vein_hot=(0.5, 0.25, 0.85), heat=(0.03, 0.028, 0.036), heat_reach=0.04), 6.0)


def mat_bronze(name="OriginBridgeBronze"):
    """Old dark bronze going green in its hollows."""
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 5.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.3, (0.1, 0.065, 0.03)), (0.7, (0.3, 0.2, 0.09))])
    a = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    a.inputs["Distance"].default_value = 0.15
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, a.outputs["AO"], clamp=True), 1.6), col, (0.12, 0.24, 0.19))
    return g.finish(col, 0.45, 0.55, g.bump(n.outputs["Fac"], 0.2, 0.01))


def cracked_slab(stone, glow, ox, centre, size, seed, cracks=3):
    """A worn stone slab split by void cracks: the slab's pieces pulled a little apart, a thin
    glowing sheet in each crack."""
    rnd = random.Random(seed)
    cx, cy, cz = centre
    sx, sy, sz = size
    cuts = sorted(rnd.uniform(-sx / 2 + 1.5, sx / 2 - 1.5) for _ in range(cracks))
    edges = [-sx / 2] + cuts + [sx / 2]
    for a, b in zip(edges, edges[1:]):
        lean = rnd.uniform(-0.05, 0.05)
        box(stone, (ox + cx + (a + b) / 2, cy - abs(lean) * 2, cz), (b - a - 0.28, sy, sz - rnd.uniform(0, 0.3)), roll=lean,
            yaw=rnd.uniform(-0.012, 0.012))
    for c in cuts:
        box(glow, (ox + cx + c, cy - 0.15, cz), (0.18, sy - 0.25, sz - 0.6), yaw=rnd.uniform(-0.15, 0.15))


def origin_deck(ox, mats):
    """One deck section of the ancient bridge: worn paving slabs split by void cracks, a broken
    stone parapet of uneven blocks with a gap or two, bronze bands on its posts."""
    rnd = random.Random(501)
    stone, glow, bronze = Hm.Hi(), Hm.Hi(), Hm.Hi()
    half = SECTION / 2
    rows = 3
    for r in range(rows):
        z = half - SECTION * (r + 0.5) / rows
        cracked_slab(stone, glow, ox, (0, -0.45, z), (DECK_WIDTH - 2.2, 0.9, SECTION / rows - 0.12), seed=510 + r, cracks=rnd.choice((1, 2, 2, 3)))
    box(stone, (ox, -1.8, 0), (DECK_WIDTH - 1.4, 1.8, SECTION))                # the bridge's body
    for side in (-1, 1):
        x = ox + side * (DECK_WIDTH / 2 - 0.7)
        z = half
        k = 0
        while z > -half + 0.5:
            length = rnd.uniform(1.6, 2.6)
            if rnd.random() < 0.15 and k > 0:                                  # a fallen block: a gap in the parapet
                z -= length
                k += 1
                continue
            h = rnd.uniform(1.8, 2.6)
            box(stone, (x, -0.1 + h / 2, z - length / 2), (1.3, h + 0.2, length - 0.12), yaw=rnd.uniform(-0.03, 0.03),
                roll=rnd.uniform(-0.03, 0.03))
            z -= length
            k += 1
        prism(stone, (x, -0.2, half - 0.2), 0.95, 3.4, sides=8, taper=0.85)   # a post at the section's end
        for y in (0.6, 2.3):
            prism(bronze, (x, y, half - 0.2), 1.0, 0.3, sides=8, taper=1.0)
    objs = [stone.object("OriginDeck_Stone", mats.coll, [mats.stone], smooth=False),
            bronze.object("OriginDeck_Bronze", mats.coll, [mats.bronze], smooth=False)]
    chamfer(objs[0], 0.09)
    chamfer(objs[1], 0.04)
    return objs, [glow.object("OriginDeck_Glow_" + VOID_GLOW, mats.coll, [K.glow_material(VOID_GLOW)], smooth=False)]


def origin_support(ox, mats):
    """Under the deck: an arch of stone voussoirs, cracked, with broken chunks hanging off it on
    old bronze chains, void light leaking from the cracks."""
    rnd = random.Random(502)
    stone, glow, bronze = Hm.Hi(), Hm.Hi(), Hm.Hi()
    span = DECK_WIDTH - 1.0
    blocks = 9
    pts = [(-span / 2 + span * k / blocks, -2.6 - 3.4 * math.sin(math.pi * k / blocks)) for k in range(blocks + 1)]
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):                 # an arch hanging under the deck, its blocks on its curve
        length = math.hypot(x1 - x0, y1 - y0)
        box(stone, (ox + (x0 + x1) / 2, (y0 + y1) / 2, 0), (length + 0.08, 1.8, 2.2), roll=math.atan2(y1 - y0, x1 - x0))
        if k in (2, 6):
            box(glow, (ox + x1, y1, 0), (0.16, 1.6, 1.9), roll=math.atan2(y1 - y0, x1 - x0))
    for x in (-span / 2 + 0.5, span / 2 - 0.5):                                  # the arch's springers meet the deck's body
        box(stone, (ox + x, -2.4, 0), (1.6, 1.6, 2.4))
    for x, drop, sz in ((-5.5, 4.5, 1.6), (0.6, 6.5, 2.1), (5.8, 3.6, 1.3)):
        top = -2.6 - 3.4 * math.sin(math.pi * (x + span / 2) / span) - 0.6    # hung from the arch's underside
        links = int(drop / 0.75)
        for k in range(links):
            y = top - k * 0.75
            ring = [(ox + x + (math.cos(TAU * j / 12) * 0.22 if k % 2 else 0), y + math.sin(TAU * j / 12) * 0.4,
                     (math.cos(TAU * j / 12) * 0.22 if k % 2 == 0 else 0)) for j in range(13)]
            Hm.htube(bronze, ring, lambda t: 0.08, sides=5, per=1, uv_scale=2.0, tip=False)
        cy = top - links * 0.75 - sz * 0.5
        box(stone, (ox + x, cy, 0), (sz, sz * 1.2, sz * 0.9), yaw=rnd.uniform(0, 1), roll=rnd.uniform(-0.3, 0.3))
        box(glow, (ox + x, cy, 0), (sz * 0.12, sz * 1.0, sz * 0.7), yaw=rnd.uniform(0, 1))
    objs = [stone.object("OriginSupport_Stone", mats.coll, [mats.stone], smooth=False),
            bronze.object("OriginSupport_Bronze", mats.coll, [mats.bronze])]
    chamfer(objs[0], 0.1)
    objs[1]["keep"] = True
    return objs, [glow.object("OriginSupport_Glow_" + VOID_GLOW, mats.coll, [K.glow_material(VOID_GLOW)], smooth=False)]


def origin_gate(ox, mats):
    """A ruined temple gate: two massive square pillars of stacked stone, one broken short, a
    lintel cracked through its middle and sagging, a void rune glowing on it, bronze bands."""
    rnd = random.Random(503)
    stone, glow, bronze = Hm.Hi(), Hm.Hi(), Hm.Hi()
    px = DECK_WIDTH / 2 + 2.0
    for side, height in ((-1, 17.0), (1, 13.5)):
        x = ox + side * px
        box(stone, (x, -0.2, 0), (4.4, 1.6, 4.4))
        y = 0.6
        while y < height:
            h = rnd.uniform(2.4, 3.4)
            box(stone, (x + rnd.uniform(-0.12, 0.12), y + h / 2, rnd.uniform(-0.12, 0.12)), (3.0, h - 0.1, 3.0), yaw=rnd.uniform(-0.05, 0.05))
            y += h
        for by in (2.0, height - 1.5):
            box(bronze, (x, by, 0), (3.2, 0.35, 3.2))
        if side == 1:                                                          # the broken pillar's jagged top
            for k in range(4):
                box(stone, (x + rnd.uniform(-0.8, 0.8), y + 0.4, rnd.uniform(-0.8, 0.8)), (1.0, 1.4, 1.0), yaw=rnd.uniform(0, 1), roll=rnd.uniform(-0.4, 0.4))
    # the lintel: two halves meeting in a crack over the gate, resting on the taller pillar and on
    # a bronze-banded stone block the broken one still carries
    box(stone, (ox + px, 14.6, 0), (3.4, 2.2, 3.4))
    gap = 0.7                              # the halves meet at a narrow crack (overlapping, they would bake black inside each other)
    for side, roll in ((-1, -0.04), (1, 0.06)):
        inner, outer = gap / 2, px + 1.3
        box(stone, (ox + side * (inner + outer) / 2, 18.4 - (0.3 if side == 1 else 0), 0), (outer - inner, 2.6, 3.4), roll=roll)
    box(glow, (ox, 18.25, 0), (gap + 0.3, 2.3, 3.0))                           # void light in the crack
    # a void rune on the lintel's face: a broken ring round a spiral
    for z in (1.72, -1.72):
        for k in range(18):
            if k % 6 == 5:
                continue
            a = TAU * k / 18
            box(glow, (ox - 3.5 + math.cos(a) * 1.1, 18.4 + math.sin(a) * 1.1, z), (0.2, 0.35, 0.05), roll=a)
        for k in range(10):
            a = 0.9 * k
            r = 0.15 + 0.08 * k
            box(glow, (ox - 3.5 + math.cos(a) * r, 18.4 + math.sin(a) * r, z), (0.16, 0.22, 0.05), roll=a)
    objs = [stone.object("OriginGate_Stone", mats.coll, [mats.stone], smooth=False),
            bronze.object("OriginGate_Bronze", mats.coll, [mats.bronze], smooth=False)]
    chamfer(objs[0], 0.12)
    chamfer(objs[1], 0.04)
    return objs, [glow.object("OriginGate_Glow_" + VOID_GLOW, mats.coll, [K.glow_material(VOID_GLOW)], smooth=False)]


class _Mats:
    pass


# ---------- added later (the extra kits) ----------


def moon_deck(ox, mats):
    """A level section of the Moonlit bridge (it climbs only gently since the islands were levelled):
    moonstone pavers with gold seams between the stringers, the stair's slim posts with gold
    crescents at its end, and the gold handrail."""
    stone, gold = Hm.Hi(), Hm.Hi()
    inner = DECK_WIDTH - 2.6
    n = 4
    half = SECTION / 2
    for i in range(n):
        z0, z1 = half - SECTION * i / n, half - SECTION * (i + 1) / n
        box(stone, (ox, -0.9, (z0 + z1) / 2), (inner, 1.8, SECTION / n - 0.1))
        box(gold, (ox, -0.02, z0 - 0.05), (inner - 0.4, 0.1, 0.16))           # a gold seam between pavers
    for side in (-1, 1):
        x = ox + side * (DECK_WIDTH / 2 - 0.65)
        prism(stone, (x, 0.0, half - 0.4), 0.36, 3.0, sides=8, taper=0.85)
        crescent(gold, (x, 3.4, half - 0.4), 0.55, width=0.16, axis="x")
        box(stone, (x, -0.4, 0), (1.3, 2.6, SECTION + 0.02))                  # stringer
        box(gold, (x, 0.95, 0), (1.42, 0.14, SECTION + 0.02))                 # its gold trim
        box(gold, (x, 3.0, 0), (0.24, 0.24, SECTION + 0.02))                  # handrail
    objs = [stone.object("MoonDeck_Stone", mats.coll, [mats.stone], smooth=False),
            gold.object("MoonDeck_Gold", mats.coll, [mats.gold], smooth=False)]
    for o in objs:
        chamfer(o, 0.05)
    return objs, []


KITS = {
    "Jade": [("Deck", jade_deck), ("Support", jade_support), ("Gate", jade_gate)],
    "Ember": [("Deck", ember_deck), ("Support", ember_support), ("Gate", ember_gate)],
    "Origin": [("Deck", origin_deck), ("Support", origin_support), ("Gate", origin_gate)],
    "Moon": [("Stair", moon_stair), ("Support", moon_support), ("Gate", moon_gate)],
}

# The pieces added after the kits were baked, each theme's baked on its own (<Theme>BridgeExtra.fbx)
# so the kits already in the game keep their maps.
EXTRA_KITS = {
    "Moon": [("Deck", moon_deck)],
}


def materials(theme, coll):
    m = _Mats()
    m.coll = coll
    if theme == "Jade":
        m.planks = mat_planks("JadeBridgePlanks", "X")
        m.beams = mat_planks("JadeBridgeBeams", "Y", tones=[(0.0, (0.15, 0.08, 0.035)), (1.0, (0.3, 0.18, 0.08))])
        m.jade = mat_jade_stone("JadeBridgeJade")
        m.vine = Hm.mat_bark("JadeBridgeVine", moss=0.6, base=(0.05, 0.1, 0.03), ridge=(0.2, 0.32, 0.1))
        m.leaf = Hm.mat_leaf("JadeBridgeLeaf")
        m.gold = Hm.mat_gold("JadeBridgeGold")
    elif theme == "Moon":
        m.stone = rescale(Hm.mat_crystal("MoonBridgeStone", stops=[(0.0, (0.62, 0.64, 0.75)), (0.5, (0.78, 0.8, 0.9)), (1.0, (0.92, 0.93, 0.98))],
                                         vein=(0.55, 0.6, 0.95), crown=(0.95, 0.96, 1.0)), 2.5)
        m.gold = Hm.mat_gold("MoonBridgeGold")
    elif theme == "Origin":
        m.stone = ruin_stone("OriginBridgeStone")
        m.bronze = mat_bronze("OriginBridgeBronze")
    elif theme == "Ember":
        m.rock = basalt("EmberBridgeBasalt", tones=[(0.0, (0.02, 0.018, 0.017)), (0.5, (0.045, 0.04, 0.037)), (1.0, (0.08, 0.07, 0.065))])
    return m


def build(theme, extra=False):
    """The kit's high-detail pieces (or its extra kit's), side by side along X. Returns
    {piece: (objects, glow objects)} and their collection."""
    coll = W.collection(theme + ("BridgeExtraHi" if extra else "BridgeHi"))
    W.clear_collection(coll)
    mats = materials(theme, coll)
    out = {}
    for k, (piece, fn) in enumerate((EXTRA_KITS if extra else KITS)[theme]):
        out[piece] = fn(k * PIECE_GAP, mats)
    return out, coll


# ---------- bake and export ----------
BUDGET = {"Jade": 16000, "Ember": 16000, "Moon": 12000, "Origin": 14000}      # triangles for the whole kit's game meshes (the deck repeats dozens of times)
EXTRA_BUDGET = 14000


def _split(low, coll, theme, pieces):
    """One game mesh per piece, by which PIECE_GAP column its faces sit in; all keep the baked
    material."""
    import bmesh
    out = []
    for k, piece in enumerate(pieces):
        bm = bmesh.new()
        bm.from_mesh(low.data)
        bm.faces.ensure_lookup_table()
        far = [f for f in bm.faces if round(f.calc_center_median().x / PIECE_GAP) != k]
        bmesh.ops.delete(bm, geom=far, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")   # no stray vertices: they would stretch the bounds
        name = theme + piece
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(low.data.materials[0])
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        out.append(o)
    return out


def _roblox_bounds(obj):
    """Bounding box centre and size of obj in Roblox axes (Blender (x, y, z) is Roblox (x, z, -y))."""
    ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = V((min(v.x for v in ws), min(v.y for v in ws), min(v.z for v in ws)))
    hi = V((max(v.x for v in ws), max(v.y for v in ws), max(v.z for v in ws)))
    c, s = (lo + hi) / 2, hi - lo
    return (c.x, c.z, -c.y), (s.x, s.z, s.y)


def write_offsets(entries, path=None):
    """src/worldbuild/Placements/BridgeKits.lua: for each kit piece (and glow piece), where its mesh's
    centre sits relative to the piece's origin (the deck's top centre) and the mesh's size, so the
    builder can stand it on the deck and stretch a deck section to any length."""
    path = path or os.path.join(W.REPO, "src", "worldbuild", "Placements", "BridgeKits.lua")
    existing = {}
    if os.path.exists(path):
        import re
        for theme, body in re.findall(r"\n    (\w+) = \{\n(.*?)\n    \},", open(path).read(), re.S):
            existing[theme] = body
    for theme, rows in entries.items():
        # pieces exported now replace their old rows; the theme's other pieces keep theirs
        new = {row.split("=")[0].strip(): row for row in rows}
        old = [row for row in existing.get(theme, "").split("\n") if row.strip() and row.split("=")[0].strip() not in new]
        existing[theme] = "\n".join(old + rows)
    lines = ["-- Generated by tools/blender/world/bridge_kits.py (export): the bridge kits' pieces. Offset is the",
             "-- mesh's centre relative to the piece's origin (the deck's top centre, the section's middle), Size",
             "-- the mesh's size as imported; a deck section is " + str(SECTION) + " studs long (the builder stretches it).",
             "return {", f"    SectionLength = {SECTION},"]
    for theme in sorted(existing):
        lines += [f"    {theme} = {{", existing[theme], "    },"]
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def export(theme, size=2048, extra=False):
    """Bakes and exports a theme's kit, or with `extra` its extra kit (<Theme>BridgeExtra.fbx and maps)."""
    built, coll = build(theme, extra)
    pieces = [p for p, _ in (EXTRA_KITS if extra else KITS)[theme]]
    hi_objs = [o for p in pieces for o in built[p][0]]
    glow_objs = [o for p in pieces for o in built[p][1]]
    name = theme + ("BridgeExtra" if extra else "Bridge")
    old = bpy.data.objects.get(name + "_Body")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(name, hi_objs, coll, EXTRA_BUDGET if extra else BUDGET[theme], sheet_ratio=0.25)
    os.makedirs(OUT_DIR, exist_ok=True)
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR                     # the maps go next to the kit's FBX
    try:
        B.bake(name, hi_objs, low, size=size, small=1024, extrusion=0.04, ray=0.12)
    finally:
        B.EGG_DIR = saved
    bodies = _split(low, coll, theme, pieces)
    rows, report = [], {}
    for k, (piece, body) in enumerate(zip(pieces, bodies)):
        origin = (k * PIECE_GAP, 0.0, 0.0)
        c, s = _roblox_bounds(body)
        rows.append(f"        {piece} = {{ Offset = Vector3.new({c[0] - origin[0]:.3f}, {c[1]:.3f}, {c[2]:.3f}), Size = Vector3.new({s[0]:.3f}, {s[1]:.3f}, {s[2]:.3f}) }},")
        report[body.name] = B.tris(body)
        for g in built[piece][1]:
            gname = g.name.split("_Glow_")
            g.name = theme + piece + "_Glow_" + gname[1]
            gc, gs = _roblox_bounds(g)
            hexstr = gname[1]
            rows.append(f'        {piece}Glow = {{ Hex = "{hexstr}", Offset = Vector3.new({gc[0] - origin[0]:.3f}, {gc[1]:.3f}, {gc[2]:.3f}), Size = Vector3.new({gs[0]:.3f}, {gs[1]:.3f}, {gs[2]:.3f}) }},')
            report[g.name] = B.tris(g)
    W.export_batch(bodies + glow_objs, os.path.join(OUT_DIR, name + ".fbx"))
    bpy.data.objects.remove(low, do_unlink=True)
    return report, write_offsets({theme: rows})

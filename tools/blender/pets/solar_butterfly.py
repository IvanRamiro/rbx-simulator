"""The Solar Butterfly (Uncommon, Solar energy; Magma Heart Egg, also in the Phoenix Ash Egg): "Its wings store a whole afternoon of sun and spend it slowly
after dark."

A swallowtail of sunset glass (the owner's choice, 2026-11-09), in a design language of its own: a stained-glass window with the sun behind it. A slender,
smooth, dark body; a small head with big glossy dark eyes rimmed in honey gold; long thin antennae ending in gold clubs; three pairs of fine black legs.
Its wings are angular, the hindwings drawn out into long swallow tails. They are glass held in black lead: veins and cross-veins frame panes that run
from noon gold at the root through amber to sunset red at the edge, each pane a little its own colour; a black margin set with gold lunules; and on each
hindwing, above the tail, a sun-disc eyespot that glows.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/solar_butterfly.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. The maps go to assets/pets/MagmaHeartEgg/.

What touches what: head, thorax and abdomen are one fused body; the eyes are half sunk in the head; the antennae, legs and wings are their own pieces, rooted
inside the head or thorax; each eyespot (a glow piece) is a thin lens passing through its hindwing.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (Matrix and Vector: the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "SolarButterfly"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "MagmaHeartEgg")

# ---------- colours: noon to sunset ----------
NOON, AMBER, SUNSET, DUSK = rgb(255, 210, 76), rgb(250, 146, 38), rgb(226, 72, 36), rgb(160, 40, 64)
LEAD, BODY, BODY_SHEEN, GOLD = rgb(22, 14, 12), rgb(30, 22, 20), rgb(92, 70, 56), rgb(242, 196, 84)
GLINT_HEX, EYESPOT_HEX = "ffffff", "ff8a1e"

# ---------- the frame of it ----------
HEAD, HEAD_R = V(0, -0.205, 0.605), (0.04, 0.042, 0.04)
THORAX, THORAX_R = V(0, -0.13, 0.6), (0.042, 0.07, 0.048)
ABDOMEN = catmull([V(0, -0.07, 0.595), V(0, 0.03, 0.586), V(0, 0.13, 0.571), V(0, 0.22, 0.552)], 10)
EYE_R = 0.026
EYE_C = V(0.03, -0.228, 0.615)
EYE_AXIS = V(0.75, -0.6, 0.2).normalized()
ANTENNA = [V(0.012, -0.232, 0.636), V(0.03, -0.29, 0.7), V(0.06, -0.36, 0.77), V(0.09, -0.42, 0.82)]
LEGS = (("F", V(0.014, -0.165, 0.58), V(0.034, -0.19, 0.556), V(0.04, -0.205, 0.53)),       # short and tucked under the thorax
        ("M", V(0.016, -0.13, 0.576), V(0.038, -0.13, 0.553), V(0.044, -0.125, 0.527)),
        ("B", V(0.014, -0.098, 0.578), V(0.036, -0.08, 0.555), V(0.042, -0.06, 0.529)))
# the wings (its left; mirrored). Each: its root, how the sheet's v maps onto the angle round the root (outward is 0, backward is +), the outline's reach
# at each angle, and how much it rises toward the tip
WING = {
    "Fore": (V(0.0, -0.155, 0.625), ((0, -0.14), (1, 1.3)),     # (rooted on the centre line: the wing's inner edge lies inside the thorax)
             ((-0.14, 0.62), (0.0, 0.6), (0.2, 0.53), (0.45, 0.46), (0.7, 0.38), (0.95, 0.27), (1.15, 0.17), (1.3, 0.12)), 0.08),
    "Hind": (V(0.0, -0.1, 0.6), ((0, 0.15), (0.5, 0.88), (0.58, 0.96), (0.8, 1.16), (1, 1.48)),     # (ending short of straight back: the two never meet)
             ((0.15, 0.34), (0.35, 0.46), (0.6, 0.5), (0.85, 0.47), (1.0, 0.42), (1.2, 0.34), (1.36, 0.25), (1.48, 0.13)), 0.06),
}
TAIL_PHI, TAIL_HALF, TAIL_EXTRA = 1.06, 0.055, 0.22
WING_THICK = 0.004
EYESPOT = (0.74, 0.86, 0.026)          # on each hindwing: how far out (u), its angle, its radius
FORE_VEINS = (-0.06, 0.1, 0.26, 0.42, 0.58, 0.76, 0.96, 1.14)
HIND_VEINS = (0.3, 0.5, 0.7, 0.88, 1.06, 1.24, 1.42)


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


# ---------- the wings ----------
def wing_phi(key, v):
    return prof(WING[key][1], v)


def wing_reach(key, phi):
    base = prof(WING[key][2], phi)
    if key == "Hind":
        base *= 1 + 0.035 * math.cos((phi - 0.15) * 22)                          # a scalloped margin
        base += TAIL_EXTRA * (1 - float(smooth(TAIL_HALF * 0.55, TAIL_HALF, abs(phi - TAIL_PHI))))      # the swallow tail
    return base


def wing_point(key, side, u, v):
    """u: from the root out to the edge; v: round from the leading edge to the trailing. Raised a little toward the tip, each wing a little cupped."""
    root, _, _, lift = WING[key]
    phi = wing_phi(key, v)
    r = wing_reach(key, phi) * (0.06 + 0.94 * u)
    x, y = math.cos(phi) * r, math.sin(phi) * r
    rr = min(r, 0.5)
    z = lift * (rr / 0.5) ** 1.2 - 0.25 * max(0.0, r - 0.5) ** 1.3 - 0.012 * math.sin(math.pi * v) * u ** 2      # the tails droop a little past the wing
    return V(root.x * side + side * x, root.y + y, root.z + z)


def wing_thick(u, v):
    return WING_THICK * (1 - 0.4 * u)


def sheet_uv(nu, nv):
    uu, vv = [], []
    for i in range(nu + 1):
        for j in range(nv + 1):
            uu += [i / nu, i / nu]
            vv += [j / nv, j / nv]
    return np.array(uu), np.array(vv)


WING_RES = {"Fore": (70, 140), "Hind": (70, 160)}
WING_LOW = {"Fore": (10, 30), "Hind": (10, 40)}


def build_wing(key, side, name, coll, nu, nv):
    m = Mesh()
    m.sheet(lambda u, v: tuple(wing_point(key, side, u, v)), wing_thick, nu, nv)
    return m.finish(name, coll)


def paint_wing(o, key, nu, nv):
    """Stained glass: panes from noon gold at the root to sunset red at the edge, each a little its own colour, held in black lead; a black margin set
    with gold lunules; the tail black with a gold streak; the eyespot's dark ring and red halo round its glowing disc."""
    uu, vv = sheet_uv(nu, nv)
    phi = np.array([wing_phi(key, v) for v in vv])
    reach = np.array([wing_reach(key, p) for p in phi])
    r = reach * (0.06 + 0.94 * uu)
    hind = key == "Hind"
    veins = np.array(HIND_VEINS if hind else FORE_VEINS)
    # the panes
    col = mix(mix(np.broadcast_to(NOON, (len(uu), 3)), AMBER, smooth(0.18, 0.55, uu)), SUNSET, smooth(0.5, 0.88, uu))
    if hind:
        col = mix(col, DUSK, smooth(0.7, 0.95, uu) * 0.5)
    cell = np.searchsorted(veins, phi) * 3 + (uu > 0.42) + (uu > 0.66)
    jitter = hash01(cell.astype(np.int64), np.full(len(uu), 7, dtype=np.int64), np.full(len(uu), 1 if hind else 0, dtype=np.int64), 5)
    col = col * (0.78 + 0.34 * jitter)[:, None]                                    # each pane its own piece of glass
    col = mix(col, col * 1.18, smooth(0.0, 0.5, (np.sin(phi * 40 + uu * 9) * 0.5 + 0.5)) * 0.08)     # the glass's ripple
    # the lead: radial veins, the discal cross-vein, the root and the margin
    d = np.min(np.abs(r[:, None] * np.sin(phi[:, None] - veins[None, :])), axis=1)
    width = 0.0032 + 0.003 * (1 - uu)
    lead = 1 - smooth(width * 0.8, width * 1.3, d)
    cross = (1 - smooth(0.0025, 0.004, np.abs(r - reach * (0.06 + 0.94 * 0.42)))) * (phi > veins[0]) * (phi < veins[-2])
    cross = np.maximum(cross, (1 - smooth(0.0022, 0.0036, np.abs(r - reach * (0.06 + 0.94 * 0.66)))))      # a second row of leading
    root = 1 - smooth(0.1, 0.16, uu)
    margin = smooth(0.82, 0.86, uu)
    if hind:
        in_tail = (1 - smooth(TAIL_HALF * 0.9, TAIL_HALF * 1.2, np.abs(phi - TAIL_PHI))) * smooth(0.44, 0.49, r)
        margin = np.maximum(margin, in_tail)
    dark = np.clip(np.maximum.reduce([lead, cross, root, margin]), 0, 1)
    col = mix(col, LEAD, dark)
    # gold lunules in the margin, one between each pair of veins; the tail's gold streak
    mids = (veins[:-1] + veins[1:]) / 2
    lun = np.zeros(len(uu))
    for m in mids:
        c_r = np.interp(m, phi[np.argsort(phi)], reach[np.argsort(phi)]) * (0.06 + 0.94 * 0.92)
        dd = np.hypot(r * np.cos(phi) - c_r * math.cos(m), r * np.sin(phi) - c_r * math.sin(m))
        lun = np.maximum(lun, 1 - smooth(0.009, 0.014, dd))
    if hind:
        lun *= 1 - in_tail
        streak = in_tail * (1 - smooth(0.003, 0.0055, r * np.abs(np.sin(phi - TAIL_PHI)))) * smooth(0.5, 0.55, r)
        lun = np.maximum(lun, streak)
        # the eyespot: a dark ring and a red halo round where the glowing disc sits
        u0, p0, er = EYESPOT
        c_r = wing_reach(key, p0) * (0.06 + 0.94 * u0)
        dd = np.hypot(r * np.cos(phi) - c_r * math.cos(p0), r * np.sin(phi) - c_r * math.sin(p0))
        col = mix(col, SUNSET * 1.1, (1 - smooth(er * 1.7, er * 2.0, dd)))
        col = mix(col, LEAD, (1 - smooth(er * 1.3, er * 1.45, dd)))
        col = mix(col, GOLD, (1 - smooth(er * 0.95, er * 1.05, dd)))
    col = mix(col, GOLD, lun * 0.95)
    paint(o, np.clip(col, 0, 1), 0.28 + 0.3 * dark, np.zeros(len(uu)))


def eyespot_frame(side):
    """Where the eyespot sits on its hindwing, and the wing's normal there."""
    u0, p0, _ = EYESPOT
    hw = WING["Hind"]
    v0 = float(np.interp(p0, [k[1] for k in hw[1]], [k[0] for k in hw[1]]))
    c = wing_point("Hind", side, u0, v0)
    du = wing_point("Hind", side, u0 + 0.01, v0) - wing_point("Hind", side, u0 - 0.01, v0)
    dv = wing_point("Hind", side, u0, v0 + 0.01) - wing_point("Hind", side, u0, v0 - 0.01)
    n = du.cross(dv).normalized()
    if n.z < 0:
        n = -n
    return c, n


def build_eyespots(name, coll, seg=32, rings=12):
    """A thin lens through each hindwing at its eyespot, so it glows on both faces; thicker than the wing, never level with it."""
    m = Mesh()
    _, _, er = EYESPOT
    for side in (1, -1):
        c, n = eyespot_frame(side)
        q = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0,
                                  matrix=Matrix.Translation(c) @ q @ Matrix.Diagonal((er, er, WING_THICK * 1.6, 1)))
    return m.finish(name, coll)


# ---------- the body ----------
def abdomen_radius(f):
    return 0.03 * (1 - 0.55 * f) * math.sqrt(max(0.0, 1 - float(smooth(0.9, 1.0, f)) ** 2)) + 0.004


def build_body():
    m = Mesh()
    m.ball(HEAD, HEAD_R, 40, 28)
    m.ball(THORAX, THORAX_R, 40, 28)
    m.tube(ABDOMEN, abdomen_radius, sides=28)
    m.ball(HEAD + V(0, -0.036, -0.006), (0.018, 0.012, 0.016), 20, 12)      # the face, a little forward
    for side in (1, -1):
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.04,) * 3, 24, 16)     # the socket
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0022, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def antenna_path(side, per=10):
    return catmull([mir(p, side) for p in ANTENNA], per)


def antenna_radius(f):
    shaft = 0.0026 * (1 - 0.2 * f)
    club = 0.0065 * math.sin(math.pi * min(1.0, max(0.0, (f - 0.8) / 0.2)) * 0.5 + 0.0) if f > 0.8 else 0.0
    end = math.sqrt(max(0.0, 1 - float(smooth(0.94, 1.0, f)) ** 2))
    return (shaft + club) * (0.35 + 0.65 * end)


def build_antennae(name, coll, sides=12, per=10):
    m = Mesh()
    m.bm.verts.layers.float.new("along")
    al = m.bm.verts.layers.float["along"]
    for side in (1, -1):
        path = antenna_path(side, per)
        before = set(m.bm.verts)
        m.tube(path, antenna_radius, sides=sides)
        new = [v for v in m.bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[al] = float(ff)
    return m.finish(name, coll)


def leg_path(knots, side, per=6):
    return catmull([mir(p, side) for p in knots], per)


def build_legs(name, coll, sides=8, per=6):
    m = Mesh()
    for _, *knots in LEGS:
        for side in (1, -1):
            m.tube(leg_path(knots, side, per), lambda f: 0.0034 * (1 - 0.4 * f) + 0.0008, sides=sides)
    return m.finish(name, coll)


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices))
    a.data.foreach_get("value", out)
    return out


def paint_body(o):
    """Smooth and dark: a warm sheen where it faces up, two gold lines down the thorax, gold bands along the abdomen's sides."""
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    col = mix(np.broadcast_to(BODY, (len(P), 3)), BODY_SHEEN, smooth(0.3, 0.95, Nn[:, 2]) * 0.5)
    on_thorax = np.linalg.norm((P - np.array(tuple(THORAX))) / np.array(THORAX_R), axis=1) < 1.15
    stripes = (1 - smooth(0.003, 0.005, np.abs(np.abs(x) - 0.018))) * on_thorax * (Nn[:, 2] > 0.2)
    # a fine gold line down each side of the abdomen, a swallowtail's, never a wasp's bands
    on_abd = (y > -0.06)
    side_line = (1 - smooth(0.12, 0.22, np.abs(Nn[:, 2] + 0.05))) * smooth(0.5, 0.8, np.abs(Nn[:, 0])) * on_abd
    col = mix(col, GOLD, np.clip(stripes + side_line * 0.85, 0, 1))
    paint(o, col, 0.32 - 0.1 * smooth(0.3, 0.95, Nn[:, 2]), np.zeros(len(P)))


def paint_antennae(o):
    f = read_tag(o, "along")
    col = mix(np.broadcast_to(LEAD, (len(f), 3)), GOLD, smooth(0.8, 0.86, f))
    paint(o, col, 0.4 - 0.15 * smooth(0.8, 0.86, f), np.zeros(len(f)))


def eye_paint(o, fr):
    """A glossy dark bead: near-black, warm toward its rim, a ring of honey gold round it."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(58, 30, 14), rgb(10, 6, 4), smooth(0.85, 0.2, r))
    col = mix(col, rgb(226, 160, 60), smooth(0.86, 0.94, r) * (1 - smooth(0.97, 1.05, r)))
    paint(o, col, np.full(len(px), 0.04), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
def eye_frames():
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        frames[tag] = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, (40.0, 120.0, 0.002), (-40.0, -128.0, 0.002))      # (no lids: an insect's eye)
    return frames


def build_hi(clay=False):
    pieces = {"Skin": build_body()}
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
    pieces["Antennae"] = build_antennae(N + "AntennaeHi", HI)
    pieces["Legs"] = build_legs(N + "LegsHi", HI)
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            pieces[key + tag] = build_wing(key, side, N + key + tag + "Hi", HI, *WING_RES[key])
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-26, 30, 0.006, 12), (24, -16, 0.0028, 8))),
             "Eyespots": build_eyespots(N + "Eyespots_Glow_" + EYESPOT_HEX, HI)}
    if not clay:
        paint_body(pieces["Skin"])
        paint_antennae(pieces["Antennae"])
        plain(pieces["Legs"], LEAD, 0.45)
        for key in ("Fore", "Hind"):
            for tag in "LR":
                paint_wing(pieces[key + tag], key, *WING_RES[key])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.0, 0.62)
FACE_AT = (0, -0.22, 0.62)
EXTRA = [(0, -1, 0.1, 0.4, FACE_AT), (0.62, -0.75, 0.25, 0.4, FACE_AT), (0.35, -0.9, 0.2, 0.2, tuple(EYE_C)), (0.05, 0.05, 1, 1.4, (0.3, 0.0, 0.62)),
         (0.8, 0.3, 0.3, 1.0, (0.3, 0.3, 0.62))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 1500
SCALES = {"EyeL": 2.5, "EyeR": 2.5, "Antennae": 0.8, "Legs": 0.5, "ForeL": 1.0, "ForeR": 1.0, "HindL": 1.0, "HindR": 1.0}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 24, 16)
    lows["Antennae"] = build_antennae(N + "AntennaeLow", GAME, 6, 4)
    lows["Legs"] = build_legs(N + "LegsLow", GAME, 5, 2)
    for key in ("Fore", "Hind"):
        for side, tag in ((1, "L"), (-1, "R")):
            lows[key + tag] = low_sheet(lambda u, v, k=key, s=side: tuple(wing_point(k, s, u, v)), wing_thick, *WING_LOW[key], N + key + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
ABD_BONES = ["Abd1", "Abd2", "Abd3"]
ABD_F = (0.05, 0.4, 0.72)


def wing_mid(key, side):
    return wing_point(key, side, 0.45, 0.35)


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", THORAX.copy(), "Root"), ("Head", HEAD + V(0, 0.03, 0), "Body")]
    parent = "Body"
    for name, f in zip(ABD_BONES, ABD_F):
        bones.append((name, path_at(ABDOMEN, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        path = antenna_path(side, 10)
        bones += [("Ant" + tag + "1", mir(ANTENNA[0], side), "Head"), ("Ant" + tag + "2", path_at(path, 0.35), "Ant" + tag + "1")]
        for key in ("Fore", "Hind"):
            root = mir(WING[key][0], side)
            bones += [(key + tag + "1", root, "Body"), (key + tag + "2", wing_mid(key, side), key + tag + "1")]
    return armature(bones)


def bind_all(lows, rig, glows):
    P = verts(lows["Skin"])
    f, _ = nearest_on(ABDOMEN, P)
    head_d = np.linalg.norm((P - np.array(tuple(HEAD))) / np.array((0.05, 0.05, 0.05)), axis=1)
    out = []
    for p, ff, hd in zip(P, f, head_d):
        if p[1] < -0.06:
            w = {"Body": 1.0}
            if hd < 1.2:
                t = float(smooth(1.2, 0.85, hd))
                w = {"Body": 1 - t, "Head": t} if t < 0.999 else {"Head": 1.0}
        else:
            w = chain_weight(["Body"] + ABD_BONES, (0.0, 0.15, 0.55, 0.85), float(ff))
        out.append(w)
    weigh(lows["Skin"], out)
    rigid(lows["EyeL"], "Head")
    rigid(lows["EyeR"], "Head")
    rigid(lows["Legs"], "Body")
    at = read_tag(lows["Antennae"], "along")
    weigh(lows["Antennae"], [chain_weight(["Ant%s1" % ("L" if p[0] > 0 else "R"), "Ant%s2" % ("L" if p[0] > 0 else "R")], (0.25, 0.45), float(a))
                             for p, a in zip(verts(lows["Antennae"]), at)])
    for key in ("Fore", "Hind"):
        for tag in "LR":
            uu, _ = sheet_uv(*WING_LOW[key])
            weigh(lows[key + tag], [chain_weight([key + tag + "1", key + tag + "2"], (0.33, 0.57), float(u)) for u in uu])
    weigh(glows["Glints"], [{"Head": 1.0} for _ in verts(glows["Glints"])])
    weigh(glows["Eyespots"], [{"HindL2" if p[0] > 0 else "HindR2": 1.0} for p in verts(glows["Eyespots"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateSolarButterfly uses. +Z (a turn about its length) lowers its left wing
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def wings(raise_, bend=0.0, hind_lag=0.0):
    """Both pairs raised by raise_ (radians; negative lowers), the outer half bent by bend."""
    out = {}
    for tag, up in (("L", -1), ("R", 1)):
        out["Fore%s1" % tag] = (0, 0, up * raise_)
        out["Fore%s2" % tag] = (0, 0, up * bend)
        out["Hind%s1" % tag] = (0, 0, up * (raise_ - hind_lag))
        out["Hind%s2" % tag] = (0, 0, up * bend * 0.8)
    return out


def pose_library():
    return {"Up": spec(wings(0.95, 0.15)), "Down": spec(wings(-0.5, -0.12, 0.08)), "Closed": spec(wings(1.3)), "Bask": spec(wings(-0.12)),
            "Look": spec({"Head": (0.2, 0.4, 0.15)}), "Curl": spec({"Abd1": (-0.12, 0, 0), "Abd2": (-0.12, 0, 0), "Abd3": (-0.15, 0, 0)}),
            "Antennae": spec({"AntL1": (0.3, 0.2, 0), "AntR1": (0.3, -0.2, 0), "AntL2": (0.2, 0, 0), "AntR2": (0.2, 0, 0)})}


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames)
    unwrap(lows, [(lambda p: p.center.y < -0.17, 2.0), (None, 1.0)], SCALES, margin=0.008)
    wing_reach_ = {k + t: (0.006, 0.018) for k in ("Fore", "Hind") for t in "LR"}
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.9, 0.55, 0.2, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.006, 0.015),
             reaches={**wing_reach_, "Antennae": (0.003, 0.008), "Legs": (0.003, 0.008)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in ("Glints", "Eyespots"):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-26, 30, 0.006, 10), (24, -16, 0.0028, 6))),
             "Eyespots": build_eyespots(N + "Eyespots_Glow_" + EYESPOT_HEX, GAME, 16, 6)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    leg_tip = min(mir(k[-1], 1).z for _, *k in LEGS)
    print("Z range", round(lo, 4), round(hi, 4), "box middle", round((hi + lo) / 2, 4), "LEG SOLE metres below the box middle", round((hi + lo) / 2 - (leg_tip - 0.0035), 4), flush=True)
    for name in ("Body", "Head", "ForeL1", "HindL2"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    wide = (0.62, -0.72, 0.35, 2.4, VIEW_AT)
    front = (0, -1, 0.15, 2.4, VIEW_AT)
    for name, view in (("Up", front), ("Down", front), ("Closed", wide), ("Bask", wide), ("Look", wide), ("Curl", (1, 0, 0.1, 2.0, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.35, 2.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

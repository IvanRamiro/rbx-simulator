"""The Aqua Wisp (Common, Water; the starter pet, Beginner Qi Egg): "A droplet that learned to think while falling. It follows anyone whose Qi runs as calm
as still water."

Recreated (November 9, 2026; the old model was a droplet blob): a water seahorse (the owner's choice), in a design language of its own: a current made into a
creature. A small seahorse spirit of living water: a crown of curling wave-crests tipped with foam on its head, big gentle ocean eyes, a long snout ending
in a little round mouth, a proud chest and a round belly ringed with soft bands, its tail curling forward into a spiral. A fan of see-through fin on its
back that never stops rippling, two little fins behind its cheeks like ears, and leafy fin-fronds down its back that sway like water weed. Deep sea-blue
on its back going to clear aqua, pale as foam on its belly, light from the surface netting over it in bright lines.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/aqua_wisp.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game meshes, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. It hovers: the lowest point of its tail's spiral is at about z = 0.05. +X is its left. The maps go to
assets/pets/BeginnerQiEgg/.

What touches what: head, snout, body and tail are one fused skin; the eyes sit in their sockets under their lids; the wave-crests root in the crown of its
head; the fins and fronds (their own see-through mesh) root inside the skin.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "AquaWisp"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: the sea from its floor to its foam ----------
DEEP, SEA, AQUA, SHALLOW, FOAM = rgb(18, 70, 168), rgb(32, 128, 214), rgb(60, 196, 232), rgb(150, 232, 244), rgb(236, 252, 255)
LIGHT_NET = rgb(196, 248, 255)
MOUTH = rgb(20, 46, 96)
LASH = rgb(12, 40, 104)
GLINT_HEX = "ffffff"

# ---------- the frame of it ----------
# the body's line, from the nape of its neck down through chest and belly to the end of its tail's spiral
# (drawn first as a real seahorse it read as a pencil with a pipe for a nose: a big round head, a short snout, a plump belly and a bold fin read as a pet)
SPINE = catmull([V(0, 0.065, 0.765), V(0, 0.08, 0.68), V(0, 0.065, 0.59), V(0, 0.05, 0.5), V(0, 0.07, 0.41), V(0, 0.1, 0.33), V(0, 0.112, 0.25),
                 V(0, 0.092, 0.17), V(0, 0.042, 0.112), V(0, -0.02, 0.1), V(0, -0.062, 0.135), V(0, -0.068, 0.188), V(0, -0.038, 0.213),
                 V(0, -0.012, 0.198)], 10)
SPINE_R = ((0, 0.068), (0.08, 0.08), (0.17, 0.09), (0.26, 0.086), (0.34, 0.072), (0.45, 0.054), (0.55, 0.042), (0.65, 0.031), (0.78, 0.022),
           (0.9, 0.016), (1, 0.011))
HEAD = V(0, -0.01, 0.8)
HEAD_R = (0.085, 0.094, 0.088)
SNOUT = [V(0, -0.075, 0.784), V(0, -0.125, 0.774), V(0, -0.162, 0.774), V(0, -0.182, 0.781)]     # short, a little turned up at its mouth
EYE_R = 0.032
EYE_C = V(0.058, -0.05, 0.826)
EYE_AXIS = V(0.62, -0.75, 0.2).normalized()
LID_UP, LID_LOW = (44.0, 118.0, 0.0026), (-46.0, -126.0, 0.0022)
LID_TILT = 4.0
BLINK_U, BLINK_L = 56.0, 28.0
IRIS, PUPIL = 0.88, 0.42
# the crown: three wave-crests curling back off its head
CRESTS = [(0.0, 1.25), (0.034, 1.0), (-0.034, 1.0)]
# the dorsal fin's root along its back (low to high, as fractions down the spine), and the fronds: where each roots, its length and width
DORSAL = (0.32, 0.1)
FRONDS = [(0.0, 0.09, 0.034), (0.055, 0.08, 0.03), (0.46, 0.072, 0.026), (0.56, 0.062, 0.022), (0.65, 0.052, 0.018)]


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def path_tan(path, f, reach=0.02):
    """Its direction at f, measured over a stretch either side: a single segment's direction jumps from one to the next, and a fin rooted along it
    zigzagged and folded over itself."""
    return (path_at(path, min(1.0, f + reach)) - path_at(path, max(0.0, f - reach))).normalized()


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    core.tube(SPINE, lambda f: prof(SPINE_R, f), sides=40, flat=1.0)
    core.ball(V(0, -0.028, 0.53), (0.092, 0.094, 0.12))          # the round belly, out in front
    core.ball(V(0, 0.022, 0.65), (0.082, 0.08, 0.08))            # the proud chest
    core.ball(SPINE[-1], (0.012, 0.012, 0.012), 12, 8)
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 40, 28)                                              # the head
    fine.ball(HEAD + V(0, -0.03, 0.045), (0.065, 0.062, 0.05))                   # a high, round brow
    fine.tube(catmull(SNOUT, 6), lambda f: 0.036 - 0.012 * f, sides=28, flat=1.0)  # the short snout
    fine.ball(SNOUT[-1] + V(0, -0.003, 0.001), (0.026, 0.013, 0.024))           # its little round mouth
    for side in (1, -1):
        fine.ball(V(side * 0.046, -0.04, 0.778), (0.044, 0.055, 0.05))          # the cheek
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(V(side * 0.05, -0.048, 0.86), (0.03, 0.034, 0.014))           # the brow: the lids' hidden edges stay under it
    fine.tube([HEAD + V(0, 0.04, -0.03), SPINE[0]], lambda f: 0.066, sides=24)  # the head onto the nape
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- the crown of wave-crests ----------
def crest_path(x, k):
    """A wave rising off its head and curling over backward, foam at its lip."""
    base = HEAD + V(x, -0.012, 0.072)
    pts = []
    for j in range(13):
        t = j / 12
        a = math.pi * 1.25 * t                       # the curl, turning over backward
        r = 0.05 * k * (1 - 0.45 * t)
        pts.append(base + V(x * 1.4 * t, 0.045 * k * t + r * math.sin(a) * 0.9, r * (1 - math.cos(a)) * 0.9 + 0.012 * k * t))
    return pts


def build_crests(name, coll, sides=20, per=3):
    m = Mesh()
    bm = m.bm
    bm.verts.layers.float.new("along")
    al = bm.verts.layers.float["along"]
    for x, k in CRESTS:
        path = catmull(crest_path(x, k), per)
        before = set(bm.verts)
        m.tube(path, lambda f, k=k: (0.017 * (1 - f) ** 0.8 + 0.0035) * (0.8 + 0.2 * k), sides=sides, flat=0.55)
        m.ball(path[-1], (0.0045 * (0.8 + 0.2 * k),) * 3, sides, max(6, sides // 2))
        new = [v for v in bm.verts if v not in before]
        f, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, f):
            v[al] = float(ff)
    return m.finish(name, coll)


# ---------- fins and fronds ----------
def dorsal_point(u, v):
    """The fan on its back: u from its root out to its scalloped edge, v along its root, low to high."""
    f = DORSAL[0] + (DORSAL[1] - DORSAL[0]) * v
    root = path_at(SPINE, f)
    tan = path_tan(SPINE, f)
    back = V(0, 1, 0) - tan * tan.y
    back = back.normalized()
    r = prof(SPINE_R, f)
    # a rounded fan, tallest a little above its middle (with an even height it read as a plank)
    # (its shortest rows lay along the skin and cut through it in streaks: its ends are kept clear of the skin)
    height = (0.17 * math.sin(math.pi * (0.1 + 0.8 * v)) ** 1.2 + 0.025)     # a clean edge: scallops crinkled it back on itself where the fan turns
    out = (back * 0.8 + V(0, 0, -0.25 + 0.95 * v)).normalized()       # its rays spread from the root like a fan's (parallel, it read as a panel)
    p = root + back * (r * 0.9) + out * (height * u)
    return tuple(p)


def pec_point(side):
    root = V(side * 0.058, 0.034, 0.77)                 # sunk in the skin (rooted at its surface, it floated clear of it)

    def point(u, v):
        # a small fan behind its cheek, spread out and back like an ear
        a = math.radians(-50 + 100 * v)
        d = (V(side * 0.8, 0.6, 0) * math.cos(a) + V(0, 0, 1) * math.sin(a)).normalized()
        length = 0.065 * (1 - 0.15 * (0.5 - 0.5 * math.cos(TAU * 4 * v)) * u)
        return tuple(root + d * (length * u + 0.004))
    return point


def frond_point(f, length, width, side):
    """A leafy frond down its back, rooted on the ridge, lying back and drooping, its edge rippled like a water weed's."""
    root = path_at(SPINE, f)
    tan = path_tan(SPINE, f)
    back = (V(0, 1, 0) - tan * tan.y).normalized()
    r = prof(SPINE_R, f)
    start = root + back * (r * 0.75)
    lie = (back * 0.8 - tan * 0.55).normalized()

    def point(u, v):
        w = width * math.sin(math.pi * (0.06 + u * 0.86)) ** 0.7 * (1 + 0.1 * math.sin(math.pi * 5 * u))     # (to zero at its tip, its last row collapsed)
        droop = V(0, 0, -0.35 * length * u * u)
        return tuple(start + lie * (length * u) + droop + V(side * 0.004 * u * u, 0, 0) + tan * ((v - 0.5) * 2 * w))
    return point


def fin_thick(u, v):
    return 0.0032 * (1 - u) ** 0.6 + 0.0012


def build_fins_hi():
    """The see-through fins as one mesh (dorsal fan, two pectoral fans, the fronds). Each vertex carries its part ("part": 0 dorsal, 1 left pectoral,
    2 right pectoral, 3 + k frond k) and how far out it is ("u")."""
    sheets = [(dorsal_point, 70, 90)]
    for side in (1, -1):
        sheets.append((pec_point(side), 30, 40))
    for k, (f, length, width) in enumerate(FRONDS):
        sheets.append((frond_point(f, length, width, 1 if k % 2 == 0 else -1), 36, 18))
    return sheets


def fin_mesh(sheets, name, coll, scale=1.0):
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("part")
    bm.verts.layers.float.new("u")
    pl, ul = bm.verts.layers.int["part"], bm.verts.layers.float["u"]
    for index, (point, nu, nv) in enumerate(sheets):
        nu, nv = max(2, int(nu * scale)), max(2, int(nv * scale))
        before = len(bm.verts)
        m.sheet(point, fin_thick, nu, nv)
        bm.verts.ensure_lookup_table()
        k = before
        for i in range(nu + 1):
            for j in range(nv + 1):
                for _ in range(2):
                    bm.verts[k][pl], bm.verts[k][ul] = index, i / nu
                    k += 1
    return m.finish(name, coll)


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


# ---------- paint ----------
def cells(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point (light netting on water is the edges between cells)."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                d1 = np.where(nearer, d, d1)
    return d1, d2


def light_net(P, Nn, top_share=0.6):
    """Sunlight through a rippling surface, netted over it in soft, wavering bright lines: strongest where it faces up and back. (Sharp, even cells
    read as cracked marble, or as scales on its dark back.)"""
    warp = np.stack([fbm(P, 9.0, 3, 21), fbm(P, 9.0, 3, 22), fbm(P, 9.0, 3, 23)], axis=1) - 0.5
    Q = P + warp * 0.05
    d1, d2 = cells(Q * np.array([1.0, 1.0, 0.75]), 22.0, 3)
    e1, e2 = cells(Q, 40.0, 9)
    net = (1 - smooth(0.0, 0.16, d2 - d1)) ** 1.6 * 0.85 + (1 - smooth(0.0, 0.1, e2 - e1)) ** 1.6 * 0.3
    facing = smooth(-0.4, 0.8, Nn[:, 2] * top_share + Nn[:, 1] * (1 - top_share))
    return np.clip(net, 0, 1) * (0.35 + 0.65 * facing)


def paint_skin(o):
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    head = 1 - smooth(0.1, 0.13, np.linalg.norm((Pv - np.array(tuple(HEAD + V(0, -0.03, 0)))) / np.array((1.0, 1.25, 1.0)), axis=1))
    f, dist = nearest_on(SPINE, Pv)
    # the sea's depth on it: deep blue down its back, clear aqua on its sides, pale as foam on its belly and throat
    back = smooth(-0.2, 0.75, Nn[:, 1] * 0.8 + Nn[:, 2] * 0.3)
    front = smooth(0.1, 0.75, -Nn[:, 1]) * (1 - head * 0.6) * smooth(0.72, 0.6, z) * smooth(0.25, 0.4, z)
    col = mix(np.broadcast_to(AQUA, (len(Pv), 3)), SEA, smooth(0.0, 0.6, back))
    col = mix(col, DEEP, smooth(0.55, 1.0, back) * 0.55)          # (full deep blue down its back read as a reptile's)
    col = mix(col, mix(SHALLOW, FOAM, smooth(0.5, 1.0, front) * 0.55), smooth(0.05, 0.5, front))     # (pure foam-white read as a plastic belly)
    # the head: sea-blue on top, aqua cheeks, the snout going pale to its mouth
    snout_f, snout_d = nearest_on(catmull(SNOUT, 6), Pv)
    snout = (1 - smooth(0.04, 0.05, snout_d)) * smooth(0.1, 0.4, snout_f)
    col = mix(col, mix(AQUA, SHALLOW, smooth(0.5, 1.0, snout_f)), snout * 0.8)
    mouth = (1 - smooth(0.006, 0.0105, np.linalg.norm((Pv - np.array(tuple(SNOUT[-1] + V(0, -0.017, 0.001)))) / np.array((1.0, 2.2, 1.0)), axis=1)))
    col = mix(col, MOUTH, mouth)
    # freckles of light under its eyes
    freckles = np.zeros(len(Pv))
    for side in (1, -1):
        for dx, dy, dz in ((0.0, 0.0, 0.0), (0.012, 0.012, -0.006), (-0.01, 0.016, -0.004)):
            c = np.array(tuple(mir(EYE_C, side) + V(side * (0.002 + dx), -0.006 + dy, -0.043 + dz)))
            freckles = np.maximum(freckles, 1 - smooth(0.0035, 0.0055, np.linalg.norm(Pv - c, axis=1)))
    col = mix(col, FOAM, freckles * 0.85)
    # soft ring bands down its body and tail (none on the head)
    bands = 0.5 + 0.5 * np.cos(TAU * f * 26)
    band = smooth(0.82, 0.98, bands) * (1 - head) * smooth(0.02, 0.07, f)
    col = mix(col, SHALLOW, band * 0.35 * (1 - front * 0.5))
    # sunlight netted over it
    net = light_net(Pv, Nn) * (1 - 0.5 * front) * (1 - 0.55 * head)      # (strong on its face, it read as veins)
    col = mix(col, LIGHT_NET, net * (0.5 - 0.15 * smooth(0.6, 1.0, back)))
    relief = band * 0.0012 + net * 0.0003 - mouth * 0.001
    set_verts(o, Pv + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.22 - 0.08 * net + 0.1 * front, np.zeros(len(Pv)))


def paint_crests(o):
    along = read_tag(o, "along")
    col = mix(np.broadcast_to(SEA, (len(along), 3)), AQUA, smooth(0.0, 0.45, along))
    col = mix(col, FOAM, smooth(0.6, 0.95, along))
    paint(o, col, np.full(len(along), 0.2), np.zeros(len(along)))


def paint_fins(o, sheets):
    """Clear shallow water, aqua at their roots; pale rays fanning out through them, their edges catching the light like foam."""
    part, u = read_tag(o, "part"), read_tag(o, "u")
    Pv = verts(o)
    vv = np.zeros(len(Pv))
    # v across each sheet, recovered in the order the sheet wrote its vertices
    start = 0
    for index, (point, nu, nv) in enumerate(sheets):
        count = (nu + 1) * (nv + 1) * 2
        j = (np.arange(count) // 2) % (nv + 1)
        vv[start:start + count] = j / nv
        start += count
    dorsal = part == 0
    pec = (part == 1) | (part == 2)
    frond = part >= 3
    rays = np.where(dorsal, smooth(0.8, 0.97, 0.5 + 0.5 * np.cos(TAU * vv * 7)), 0.0)
    rays = np.where(pec, smooth(0.75, 0.95, 0.5 + 0.5 * np.cos(TAU * vv * 4.5)), rays)
    rays = np.where(frond, 1 - smooth(0.04, 0.12, np.abs(vv - 0.5)), rays) * smooth(0.05, 0.25, u)
    edge = smooth(0.8, 1.0, u)
    col = mix(np.broadcast_to(AQUA, (len(Pv), 3)), SHALLOW, smooth(0.0, 0.5, u))
    col = mix(col, FOAM, np.clip(rays * 0.7 + edge * 0.8, 0, 1))
    paint(o, np.clip(col, 0, 1), np.full(len(Pv), 0.15), np.zeros(len(Pv)))


def eye_paint(o, fr):
    """An ocean eye: deep navy at its heart going to bright sea-blue at its rim, fine rays through it, a round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(8, 20, 54), (len(px), 3)).copy()
    iris = mix(rgb(30, 80, 190), rgb(70, 200, 245), smooth(0.4, 0.85, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.88 + 0.12 * np.sin(azi * 30 + np.sin(azi * 4) * 1.4))[:, None]
    iris = mix(iris, iris * 0.65, smooth(-0.2, 0.8, py / IRIS) * 0.4)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(10, 30, 80), smooth(IRIS - 0.1, IRIS - 0.02, r) * (1 - smooth(IRIS - 0.02, IRIS, r)))
    col = mix(col, rgb(4, 10, 28), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SEA, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SEA, LASH, lower_share=0.7)
    pieces["Crests"] = build_crests(N + "CrestsHi", HI)
    data["fin_sheets"] = build_fins_hi()
    pieces["Fins"] = fin_mesh(data["fin_sheets"], N + "FinsHi", HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0062, 12), (20, -18, 0.0028, 8)))}
    if not clay:
        paint_skin(skin)
        paint_crests(pieces["Crests"])
        paint_fins(pieces["Fins"], data["fin_sheets"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.25), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.4, -0.5, -0.8)]
VIEW_AT = (0, 0.0, 0.47)
FACE_AT = (0, -0.08, 0.8)
EXTRA = [(0, -1, 0.08, 0.7, FACE_AT), (0.75, -0.6, 0.2, 0.7, FACE_AT), (1, -0.1, 0.1, 0.75, FACE_AT), (0.5, -0.85, 0.1, 0.32, tuple(EYE_C)),
         (0.9, 0.4, 0.3, 1.0, (0, 0.08, 0.52)), (0.8, -0.3, 0.1, 0.9, (0, 0.02, 0.16))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.03, 0.06, 0.12, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.3)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    print("DONE", flush=True)


# ---------- the game meshes ----------
SKIN_QUADS = 3400
SCALES = {"EyeL": 2.6, "EyeR": 2.6, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Crests": 1.4, "Fins": 0.9}


def build_low(pieces, frames, data):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    lows["Crests"] = build_crests(N + "CrestsLow", GAME, 8, 1)
    lows["Fins"] = fin_mesh(data["fin_sheets"], N + "FinsLow", GAME, scale=0.2)
    triangulate(lows)
    return lows


def flatten_normals(o, pad=4):
    """The fins' share of the normal map made flat: their relief is a fraction of a millimetre, and baked on slender sheets it comes out turned away
    (dark notches)."""
    img = bpy.data.images[PET + "_Normal"]
    if img.packed_file:                  # (edited while packed, the packed copy keeps the old pixels: the .blend and the FBX would disagree with the PNG)
        img.unpack(method="REMOVE")
        img.reload()
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    mask = np.zeros((h, w), dtype=bool)
    uv = o.data.uv_layers.active.data
    for p in o.data.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * (w, h) for i in loops[:3]]
        lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - pad, 0, (w - 1, h - 1))
        hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + pad, 0, (w - 1, h - 1))
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        for p0, p1 in ((a, b), (b, c), (c, a)):
            e = p1 - p0
            t = np.clip(((qx - p0[0]) * e[0] + (qy - p0[1]) * e[1]) / max(e @ e, 1e-12), 0, 1)
            inside |= np.hypot(qx - p0[0] - e[0] * t, qy - p0[1] - e[1] * t) <= pad
        mask[ys[inside], xs[inside]] = True
    px[mask] = (0.5, 0.5, 1.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.save()
    img.pack()
    return int(mask.sum())


# ---------- the skeleton ----------
# down its spine: neck, chest, belly, and six bones down the tail to the heart of its spiral (fractions down SPINE)
CHAIN = [("Neck", 0.0), ("Chest", 0.1), ("Body", 0.25), ("Tail1", 0.4), ("Tail2", 0.5), ("Tail3", 0.6), ("Tail4", 0.7), ("Tail5", 0.8), ("Tail6", 0.9)]
CHAIN_NAMES = [n for n, _ in CHAIN]
CHAIN_MIDS = tuple((CHAIN[k][1] + CHAIN[k + 1][1]) / 2 for k in range(len(CHAIN) - 1)) + (1.05,)
HEAD_BONE = V(0, 0.02, 0.78)                  # where its head turns on its neck
CREST_BONE = HEAD + V(0, -0.01, 0.07)
PEC = {1: V(0.058, 0.034, 0.77), -1: V(-0.058, 0.034, 0.77)}
DORSAL_V = (0.15, 0.5, 0.85)                  # the fin's three bones along its root


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", path_at(SPINE, 0.25), "Root"), ("Chest", path_at(SPINE, 0.1), "Body"), ("Neck", path_at(SPINE, 0.0), "Chest"),
             ("Head", HEAD_BONE.copy(), "Neck"), ("Crest", CREST_BONE.copy(), "Head")]
    parent = "Body"
    for name, f in CHAIN[3:]:
        bones.append((name, path_at(SPINE, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head"),
                  ("Pec" + tag, PEC[side].copy(), "Head")]
    for k, v in enumerate(DORSAL_V):
        bones.append(("Dorsal%d" % (k + 1), Vector(dorsal_point(0.0, v)), "Body"))
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (HEAD + V(0, -0.04, 0.0), (0.11, 0.16, 0.1))


def skin_weights(Pv):
    f, _ = nearest_on(SPINE, Pv)
    hz = np.linalg.norm((Pv - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    out = []
    for i in range(len(Pv)):
        w = chain_weight(CHAIN_NAMES, CHAIN_MIDS, float(f[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.85, hz[i])))
        out.append(w)
    return out


def fin_weights(o, sheets):
    """The dorsal fan rippling on its three bones, held to the body at its root; each pectoral fin on its own bone; each frond with the spine where it
    grows."""
    part, u = read_tag(o, "part"), read_tag(o, "u")
    vv = np.zeros(len(part))
    start = 0
    for index, (point, nu, nv) in enumerate(sheets):
        nu, nv = max(2, int(nu * 0.2)), max(2, int(nv * 0.2))
        count = (nu + 1) * (nv + 1) * 2
        vv[start:start + count] = ((np.arange(count) // 2) % (nv + 1)) / nv
        start += count
    out = []
    for i in range(len(part)):
        k = int(part[i])
        if k == 0:
            root_f = DORSAL[0] + (DORSAL[1] - DORSAL[0]) * vv[i]
            body = chain_weight(CHAIN_NAMES, CHAIN_MIDS, root_f)
            fin = chain_weight(["Dorsal1", "Dorsal2", "Dorsal3"], ((DORSAL_V[0] + DORSAL_V[1]) / 2, (DORSAL_V[1] + DORSAL_V[2]) / 2, 2.0), float(vv[i]))
            out.append(blend(body, fin, float(smooth(0.0, 0.3, u[i]))))
        elif k in (1, 2):
            out.append({"PecL" if k == 1 else "PecR": 1.0})
        else:
            out.append(chain_weight(CHAIN_NAMES, CHAIN_MIDS, FRONDS[k - 3][0]))
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    for tag in ("L", "R"):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Crests"], "Crest")
    fins = lows.pop("Fins")
    weigh(fins, fin_weights(fins, data["fin_sheets"]))
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    fins.name = fins.data.name = N + "Fins"
    pet_kit.bind(rig, [body, fins] + list(glows.values()))
    return body, fins


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left): the same numbers as PetRig's AW tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def tail(curl):
    """+ curls the tail tighter (its spiral rolls forward), - lets it out."""
    return {"Tail%d" % k: (-curl * (0.5 + 0.1 * k), 0, 0) for k in range(1, 7)}


CURL = tail(0.35)
UNCURL = tail(-0.3)
LEAN = {"Body": (-0.35, 0, 0), "Chest": (-0.1, 0, 0), "Head": (0.25, 0, 0), **tail(-0.15)}
NOD = {"Neck": (0.25, 0, 0), "Head": (0.3, 0, 0)}
LOOK = {"Neck": (0.1, 0.35, 0), "Head": (0.15, 0.45, 0.15)}
TWIST = {"Body": (0, 0.4, 0), "Chest": (0, 0.2, 0), **{"Tail%d" % k: (0, -0.15, 0.1) for k in range(1, 7)}}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    wave = {"Dorsal1": (0, 0.45, 0), "Dorsal2": (0, -0.45, 0), "Dorsal3": (0, 0.45, 0)}
    flap = {"PecL": (0, 0.6, 0.3), "PecR": (0, -0.6, -0.3)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-6, -5), "Curl": spec(CURL), "Uncurl": spec(UNCURL), "Lean": spec(LEAN), "Nod": spec(NOD),
            "Look": spec(LOOK), "Twist": spec(TWIST), "Wave": spec(wave), "Flap": spec(flap), "Crest": spec({"Crest": (0.25, 0, 0.15)})}


if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.3)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.34, 0.42, 1))
    lows = build_low(pieces, frames, data)
    unwrap(lows, [(lambda p: p.center.z > 0.72, 1.8), (None, 1.0)], SCALES, margin=0.009, angle=38)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.24, 0.62, 0.86, 1), far=("Skin",), reach=(0.004, 0.01),
             far_reach=(0.008, 0.02), reaches={"Fins": (0.0015, 0.004), "Crests": (0.003, 0.008)})
    print("FIN NORMALS FLATTENED", flatten_normals(lows["Fins"]), "texels", flush=True)
    lows["Fins"].data.polygons.foreach_set("use_smooth", [False] * len(lows["Fins"].data.polygons))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0062, 10), (20, -18, 0.0028, 6)))}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body, fins = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "FINS tris", sum(len(p.vertices) - 2 for p in fins.data.polygons),
          "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in (body, fins) for v in o.data.vertices), flush=True)
    for o in (body, fins):
        print("UV OVERLAP TEXELS", o.name, uv_overlap_texels(o.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body, fins] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "box middle (the root at 0 counted)", round(max(hi, 0) / 2, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Head", "Crest", "Body", "Tail6"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name, row in pet_kit.stress_report(rig, fins, lib).items():
        print("STRESS FINS", name, row, flush=True)
    side = (1, -0.05, 0.08, 2.4, VIEW_AT)
    face = (0.25, -0.95, 0.1, 0.7, FACE_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Curl", side), ("Uncurl", side), ("Lean", side), ("Nod", side), ("Look", face), ("Twist", side),
                       ("Wave", (0.6, 0.7, 0.2, 1.6, VIEW_AT)), ("Flap", face), ("Crest", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.25, 2.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values()), extras=[fins]), flush=True)
    print("DONE", flush=True)

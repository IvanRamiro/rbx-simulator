"""The Orthodox sword's silhouette study (run inside Blender, headless):

    blender -b --factory-startup --python tools/blender/weapons/sword_orthodox_study.py

Each candidate is a quick 3D proxy (one shared blade, so the eye compares guard, hilt, pommel and cord) in the weapon's own
authored studs (point toward -Z, flats +-Y, edges +-X), drawn in flat black on white from the flat the player sees, from the
edge and from a three-quarter view, at thumbnail size and larger. A guard is a plate PERPENDICULAR to the blade, so from the
side it is only a bar: the study judges what survives that, which is why candidates that lean on a face-on outline fail it.

Writes renders/faction_weapons_v2/Orthodox/silhouette_study.png and silhouette_thumbs.png (local, never committed).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import sword_orthodox_board as BD  # noqa: E402
import weapon_kit as WK  # noqa: E402

Hm, W = WK.Hm, WK.W
V = Vector
TAU = math.tau
REPO = W.REPO
REVIEW = os.path.join(REPO, "renders", "faction_weapons_v2", "Orthodox")
TIP_Z, FOOT_Z, GRIP0, GRIP1 = -5.75, -1.10, -0.55, 1.55
BLACK = None


def black_mat():
    m = bpy.data.materials.get("ST_Black") or bpy.data.materials.new("ST_Black")
    return m


def blade_w(t):
    if t < 0.86:
        return 0.22 - 0.058 * t / 0.86
    u = (t - 0.86) / 0.14
    return 0.162 * (1 - u ** 1.7) ** 0.62


def blade_t(t):
    return 0.075 * (1 - 0.55 * t) + 0.006


def plate_xy(hi, outline, z, th):
    """A plate perpendicular to the blade at height z: outline(angle) -> radius (x, y), `th` thick. Returns nothing."""
    n = 72
    rings = []
    for zz in (z - th / 2, z + th / 2):
        pts = []
        for i in range(n):
            a = TAU * i / n
            r = outline(a)
            rx, ry = r if isinstance(r, tuple) else (r, r)
            pts.append(V((rx * math.cos(a), ry * math.sin(a), zz)))
        rings.append((V((0, 0, zz)), pts))
    WK.loft(hi, rings, uv_scale=1.0)


def lobed(rx, ry, lobes=4, depth=0.12, phase=0.0):
    return lambda a: (rx * (1 + depth * math.cos(lobes * a + phase)), ry * (1 + depth * math.cos(lobes * a + phase)))


def turned(hi, prof, sides=24):
    """A solid of revolution about the blade axis: prof [(radius, z)] from one end to the other (a lathe-turned fitting)."""
    pts = [V((0, 0, prof[0][1]))]
    rings = []
    for r, z in prof:
        rings.append((V((0, 0, z)), [V((max(r, 0.003) * math.cos(TAU * i / sides), max(r, 0.003) * math.sin(TAU * i / sides), z)) for i in range(sides)]))
    WK.loft(hi, rings, uv_scale=1.0)


def cord(hi, z0, sway=0.15, length=1.7, brush=0.2, x0=0.0):
    pts = [V((x0 + sway * math.sin(math.pi * 1.1 * k / 6), -0.01 * k, z0 + length * 0.55 * k / 6)) for k in range(7)]
    Hm.htube(hi, pts, lambda t: 0.024, sides=6, per=3, uv_scale=3.0, tip=False, wobble=0.0)
    end = pts[-1]
    Hm.htube(hi, [end, end + V((0, 0, 0.05)), end + V((0.0, 0, length * 0.46))], lambda t: 0.1 * math.sin(math.pi * (0.18 + 0.8 * t)) ** 0.6 + 0.006,
             sides=10, per=3, uv_scale=3.0, tip=True, wobble=0.0)
    WK.blob(hi, end - V((0, 0, 0.01)), end + V((0, 0, 0.17)), 0.065)


def proxy(letter):
    """The candidate's solid pieces (one Hi) in the weapon's frame."""
    hi = Hm.Hi()
    WK.blade(hi, FOOT_Z - 0.02, TIP_Z, blade_w, blade_t, rib=0.3, n=60, m=12)
    Hm.htube(hi, [V((0, 0, GRIP0)), V((0, 0, 0.5)), V((0, 0, GRIP1))], lambda t: 0.155 + 0.02 * math.sin(math.pi * t), sides=14, per=6,
             uv_scale=1.0, tip=False, wobble=0.0)
    if letter == "A":       # the plain katana-like read: a round tsuba, a ball
        plate_xy(hi, lambda a: 0.85, -0.95, 0.09)
        turned(hi, [(0.25, -1.55), (0.22, -1.0), (0.2, -0.95)])
        WK.sphere(hi, V((0, 0, GRIP1 + 0.1)), 0.2)
        cord(hi, GRIP1 + 0.3)
    elif letter == "B":     # a lobed plate on a tall collar, a flared cap and a ring (the leading line)
        plate_xy(hi, lobed(1.0, 0.72, 4, 0.1), -0.95, 0.1)
        turned(hi, [(0.2, -1.62), (0.28, -1.55), (0.24, -1.25), (0.21, -1.0), (0.26, -0.9)])
        turned(hi, [(0.19, GRIP1 - 0.1), (0.3, GRIP1 + 0.02), (0.22, GRIP1 + 0.12), (0.16, GRIP1 + 0.16)])
        WK.ring(hi, V((0, 0, GRIP1 + 0.56)), (0, 1, 0), 0.4, 0.04, n=40, sides=8)
        cord(hi, GRIP1 + 0.9, 0.13)
    elif letter == "C":     # the brief's starting point: oval guard, flared lotus-bud pommel
        plate_xy(hi, lambda a: (1.0, 0.45), -0.95, 0.09)
        turned(hi, [(0.25, -1.55), (0.22, -1.0)])
        turned(hi, [(0.17, GRIP1), (0.29, GRIP1 + 0.2), (0.3, GRIP1 + 0.42), (0.14, GRIP1 + 0.64), (0.01, GRIP1 + 0.72)])
        cord(hi, GRIP1 + 0.72)
    elif letter == "D":     # the hourglass hilt: a bell-flare guard, a waist, a bell-flare cap
        turned(hi, [(0.21, -1.5), (0.25, -1.28), (0.4, -1.0), (0.72, -0.82), (0.78, -0.78), (0.2, -0.78)])
        turned(hi, [(0.2, GRIP1 - 0.35), (0.3, GRIP1 - 0.12), (0.5, GRIP1 + 0.18), (0.54, GRIP1 + 0.22), (0.1, GRIP1 + 0.22)])
        cord(hi, GRIP1 + 0.22)
    elif letter == "E":     # swept wings in the flat plane (the first attempt's family, curved)
        for s in (1, -1):
            pts = [V((s * 0.2, 0, -0.9)), V((s * 0.7, 0, -1.0)), V((s * 1.2, 0, -1.4)), V((s * 1.45, 0, -2.0))]
            Hm.htube(hi, pts, lambda t: 0.06 * (1 - t) + 0.012, sides=6, per=6, uv_scale=2.0, tip=True, wobble=0.0)
        WK.sphere(hi, V((0, 0, GRIP1 + 0.1)), 0.2)
        cord(hi, GRIP1 + 0.3)
    elif letter == "F":     # three stepped discs
        for r, z in ((0.95, -0.88), (0.7, -0.97), (0.45, -1.06)):
            plate_xy(hi, lambda a, r=r: r, z, 0.07)
        WK.ring(hi, V((0, 0, GRIP1 + 0.46)), (0, 1, 0), 0.34, 0.04, n=40, sides=8)
        turned(hi, [(0.19, GRIP1 - 0.1), (0.27, GRIP1 + 0.02), (0.16, GRIP1 + 0.12)])
        cord(hi, GRIP1 + 0.8, 0.13)
    elif letter == "G":     # a spool: two discs and a barrel, a flat-faced cap
        plate_xy(hi, lambda a: 0.8, -0.9, 0.07)
        plate_xy(hi, lambda a: 0.8, -1.3, 0.07)
        turned(hi, [(0.3, -1.34), (0.3, -0.86)])
        turned(hi, [(0.18, GRIP1 - 0.05), (0.42, GRIP1 + 0.06), (0.42, GRIP1 + 0.16), (0.2, GRIP1 + 0.2)])
        cord(hi, GRIP1 + 0.2)
    elif letter == "I":     # a bell-mouth guard: a concave flare opening toward the hand, a thin rolled rim; a long waist; a slim cap and a ring
        turned(hi, [(0.2, -1.78), (0.24, -1.6), (0.3, -1.38), (0.42, -1.16), (0.62, -0.98), (0.86, -0.86), (0.9, -0.82), (0.86, -0.8), (0.3, -0.8)])
        turned(hi, [(0.17, GRIP1 - 0.1), (0.26, GRIP1 + 0.02), (0.2, GRIP1 + 0.12), (0.14, GRIP1 + 0.16)])
        WK.ring(hi, V((0, 0, GRIP1 + 0.56)), (0, 1, 0), 0.4, 0.04, n=40, sides=8)
        cord(hi, GRIP1 + 0.9, 0.13)
    elif letter == "K":     # the same long flare, FACETED (eight planes, hard arrises, a stepped rim): a pavilion roof turned over, not a flower
        turned(hi, [(0.2, -1.78), (0.23, -1.62), (0.29, -1.4), (0.4, -1.18), (0.58, -1.0), (0.82, -0.88), (0.9, -0.86), (0.9, -0.8), (0.3, -0.8)], sides=8)
        turned(hi, [(0.17, GRIP1 - 0.1), (0.26, GRIP1 + 0.02), (0.2, GRIP1 + 0.12), (0.14, GRIP1 + 0.16)], sides=8)
        WK.ring(hi, V((0, 0, GRIP1 + 0.56)), (0, 1, 0), 0.4, 0.04, n=40, sides=8)
        cord(hi, GRIP1 + 0.9, 0.13)
    elif letter == "J":     # the same bell, a thin lobed plate under it, a tall flared cap (no ring)
        turned(hi, [(0.2, -1.78), (0.24, -1.6), (0.3, -1.38), (0.42, -1.16), (0.58, -1.0), (0.66, -0.92), (0.66, -0.9), (0.3, -0.9)])
        plate_xy(hi, lobed(1.0, 0.8, 4, 0.1), -0.86, 0.08)
        turned(hi, [(0.16, GRIP1 - 0.2), (0.2, GRIP1 - 0.05), (0.3, GRIP1 + 0.12), (0.26, GRIP1 + 0.3), (0.12, GRIP1 + 0.46), (0.02, GRIP1 + 0.5)])
        cord(hi, GRIP1 + 0.5)
    elif letter == "H":     # a shallow bowl guard
        turned(hi, [(0.21, -1.4), (0.26, -1.15), (0.55, -1.0), (0.95, -0.93), (0.97, -0.88), (0.5, -0.92), (0.2, -0.98)])
        WK.sphere(hi, V((0, 0, GRIP1 + 0.12)), 0.22)
        cord(hi, GRIP1 + 0.34)
    return hi


LETTERS = "ABCDEFGHIJK"
NAMES = {
    "A": "Round tsuba, ball pommel",
    "B": "Lobed plate on tall collar, flared cap, ring",
    "C": "Oval guard, lotus-bud pommel (the brief)",
    "D": "Hourglass hilt (bell guard, bell cap)",
    "E": "Swept wings in the flat plane",
    "F": "Three stepped discs, ring",
    "G": "Spool guard, flat-faced cap",
    "H": "Shallow bowl guard, ball",
    "I": "Bell-mouth guard, long waist, slim cap and ring",
    "J": "Bell guard over a lobed plate, tall cap",
    "K": "Faceted pavilion flare, waist, slim cap, ring",
}
VERDICTS = {
    "A": "A katana read: a thin bar from the side, a ball. The stranger's 'generic sword'.",
    "B": "Handsome face-on, but from the side the plate is a bar and the sword is a cross with a ring. Generic from the flat.",
    "C": "The brief's bud pommel: soft, a bar guard, and Sword6 already ends in a lotus bud. Weakest.",
    "D": "A silhouette from every side, but a turned chess-piece (two bulbs): a prop, not a weapon.",
    "E": "Swept wings: the best flat view of the lot, nothing from the edge. The first attempt's family. Out.",
    "F": "Stepped discs: stacked bars, a crown in three-quarter. Out.",
    "G": "A spool: a bobbin. Out.",
    "H": "A shallow bowl: a sombrero, it hides the collar and reads as a sabre hilt. Out.",
    "I": "The long smooth flare is the most elegant line here, but it is a flower (a calyx): Sword6 is already a sword growing from a lotus. Out as drawn.",
    "J": "A bell on a plate: busy, and a squat read. Out.",
    "K": "I, faceted: eight planes with hard arrises read as a pavilion roof turned over (carved metal, architecture), not a flower. The only line that is unmistakable at 60 px AND not a cross. Chosen.",
}
CHOSEN = "K"


def scene_setup(size):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.film_transparent = False
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = bpy.data.worlds.get("ST_World") or bpy.data.worlds.new("ST_World")
    w.use_nodes = False
    w.color = (1, 1, 1)
    sc.world = w
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (0, 0, 0)
    sh.show_object_outline = False
    sh.background_type = "WORLD"
    return sc


def shoot_sil(objs, direction, size, ortho=True, span=None, centre=None):
    """Black on white from `direction` (Roblox axes), weapon axis up the image. Returns an RGBA array (top row first)."""
    sc = bpy.context.scene
    cam = bpy.data.objects.get("ST_Cam")
    if cam is None:
        cam = bpy.data.objects.new("ST_Cam", bpy.data.cameras.new("ST_Cam"))
        sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = size
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = V(centre) if centre is not None else (lo + hi) / 2
    d = V((direction[0], -direction[2], direction[1])).normalized()
    cam.data.type = "ORTHO" if ortho else "PERSP"
    cam.data.sensor_fit = "VERTICAL"
    sp = span or (hi.y - lo.y) * 1.04
    if ortho:
        cam.data.ortho_scale = sp
    else:
        cam.data.lens = 70
        cam.data.sensor_height = 24
    cam.data.clip_start, cam.data.clip_end = 0.1, 200
    dist = 40.0 if ortho else sp * 0.5 / (12.0 / 70) * 1.04 + 4
    cam.location = c + d * dist
    zax = d
    up = V((0, 0, 1)) if abs(d.z) < 0.9 else V((0, 1, 0))
    up = V((0, 1, 0)) if True else up           # the weapon's axis (Blender +Y) up the image
    if abs(d.dot(up)) > 0.95:
        up = V((0, 0, 1))
    xax = up.cross(zax).normalized()
    yax = zax.cross(xax).normalized()
    cam.rotation_euler = Matrix(((xax.x, yax.x, zax.x), (xax.y, yax.y, zax.y), (xax.z, yax.z, zax.z))).to_euler()
    tmp = os.path.join(REVIEW, "_sil.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp, check_existing=False)
    w, h = img.size
    arr = np.zeros(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    os.remove(tmp)
    return arr.reshape(h, w, 4)[::-1].copy()


# ---------- the blade study: six outlines of the blade alone (flat view), on the chosen flare, same length ----------
BLADES = {
    "1  Ken: parallel, long convex point": lambda t: (0.23 - 0.07 * t / 0.86) if t < 0.86 else 0.16 * (1 - ((t - 0.86) / 0.14) ** 1.7) ** 0.62,
    "2  Spire: one long straight-edged taper": lambda t: 0.25 * (1 - t) ** 0.92 + 0.002,
    "3  Leaf: a belly at two thirds (xiphos)": lambda t: 0.19 + 0.06 * math.sin(math.pi * min(1, t * 1.1) ** 0.8) if t < 0.62 else 0.25 * (1 - ((t - 0.62) / 0.38) ** 1.35) ** 0.8,
    "4  Shouldered: a forte, a step, a lean blade": lambda t: (0.26 if t < 0.17 else 0.205 - 0.05 * (t - 0.17) / 0.7) if t < 0.87 else 0.155 * (1 - ((t - 0.87) / 0.13) ** 1.6) ** 0.6,
    "5  Lute: the edges bow in and out (a Bronze Age dagger)": lambda t: (0.205 + 0.03 * math.sin(TAU * t * 0.9) - 0.05 * t) if t < 0.85 else (0.205 + 0.03 * math.sin(TAU * 0.85 * 0.9) - 0.05 * 0.85) * (1 - ((t - 0.85) / 0.15) ** 1.7) ** 0.62,
    "6  Broad parallel, chisel point (a sabre)": lambda t: 0.3 if t < 0.93 else 0.3 * (1 - (t - 0.93) / 0.07) + 0.001,
}
BLADE_VERDICTS = {
    "1": "Calm, noble, the long taper reads as one clean sweep; slender at the base. Kept (with the taper of 2 started earlier).",
    "2": "The tallest, most needle-like: a spire. But the straight triangle reads as a lance or dagger, not a sword.",
    "3": "A leaf: a Greek or Roman sword. Wrong culture, and Sword6 is already a leaf.",
    "4": "The step gives the base weight and a tell, but it breaks the clean line and looks like a tool.",
    "5": "The most surprising and the most Korean (the Bronze Age dagger), but a wavy edge fights 'perfectly straight' and 'orthodox'.",
    "6": "The Demonic's family: broad and blunt. Out.",
}


def blade_study():
    keys = list(BLADES)
    n = len(keys)
    cw, ch = 215, 470
    cv = BD.Canvas(n * (cw + 6) + 6, ch + 110, bg=(0.93, 0.93, 0.94, 1.0))
    cv.text("Orthodox sword: six blade outlines, black on grey, same length (4.65 studs), over the chosen flared hilt. Chosen: 1, taper begun earlier.", 8, 6, 15, (0.1, 0.1, 0.12, 1))
    sc = 48.0
    for i, key in enumerate(keys):
        x0 = 6 + i * (cw + 6)
        chosen = key.startswith("1")
        cv.rect(x0, 30, cw, ch + 70, (0.82, 0.9, 0.82, 1) if chosen else (0.86, 0.86, 0.89, 1))
        f0 = BLADES[key]

        def f(t, f0=f0):
            return f0(min(t, 0.99999))
        ts = [k / 60 for k in range(61)]
        right = [(x0 + 70 + f(t) * sc, 50 + (1 - t) * 4.65 * sc) for t in ts]
        left = [(x0 + 70 - f(t) * sc, 50 + (1 - t) * 4.65 * sc) for t in ts]
        base_y = 50 + 4.65 * sc
        cv.polygon(right + list(reversed(left)), (0.02, 0.02, 0.025, 1))
        flare = [(0.2, -1.78), (0.23, -1.62), (0.29, -1.4), (0.4, -1.18), (0.58, -1.0), (0.82, -0.88), (0.9, -0.86), (0.9, -0.8)]
        pts = [(x0 + 70 + r * sc, base_y + (z + 1.1) * sc * -1 + 0 * z) for r, z in flare]
        # z -1.78 is 0.68 above the foot at -1.1: the flare sits over the foot
        pts = [(x0 + 70 + r * sc, base_y - (-1.1 - z) * sc) for r, z in flare]
        poly = pts + [(2 * (x0 + 70) - x, y) for x, y in reversed(pts)]
        cv.polygon(poly, (0.02, 0.02, 0.025, 1))
        cv.polygon([(x0 + 70 - 0.15 * sc, base_y + 0.3 * sc), (x0 + 70 + 0.15 * sc, base_y + 0.3 * sc), (x0 + 70 + 0.15 * sc, base_y + 2.2 * sc), (x0 + 70 - 0.15 * sc, base_y + 2.2 * sc)], (0.02, 0.02, 0.025, 1))
        cv.text(key, x0 + 6, 33, 12, (0.05, 0.1, 0.2, 1))
        words, line, y = BLADE_VERDICTS[key[0]], "", ch + 10
        for w in words.split():
            if len(line + " " + w) > 40:
                cv.text(line, x0 + 6, y, 12, (0.15, 0.15, 0.2, 1))
                y += 15
                line = w
            else:
                line = (line + " " + w).strip()
        cv.text(line, x0 + 6, y, 12, (0.15, 0.15, 0.2, 1))
        # a thumbnail
        cv.paste(cv.px[50:50 + int(4.65 * sc) + 120, int(x0 + 20):int(x0 + 120), :].copy()[::3, ::3] * 0 + 0, 0, 0) if False else None
    print("blade study:", cv.save(os.path.join(REVIEW, "blade_study.png")))


def run():
    os.makedirs(REVIEW, exist_ok=True)
    blade_study()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    root = W.collection("StudyHi")
    scene_setup((300, 700))
    mat = black_mat()
    objs = {}
    for L in LETTERS:
        hi = proxy(L)
        ob = hi.object("ST_" + L, root, [mat], smooth=True)
        ob.hide_render = True
        objs[L] = ob
    views = (("flat", (0, 1, 0), True), ("edge", (1, 0, 0), True), ("3/4", (0.75, 0.55, -0.55), False))
    # one fixed frame for every candidate: the same scale, so sizes compare
    span_all = 10.4
    centre = V((0, -(TIP_Z + 4.2) / 2 + 0.0, 0)) if False else None
    tiles = {}
    for L in LETTERS:
        objs[L].hide_render = False
        for name, d, ortho in views:
            tiles[(L, name)] = shoot_sil([objs[L]], d, (260, 600), ortho=ortho, span=span_all, centre=V((0, -(TIP_Z + 3.9) / 2, 0)))
        objs[L].hide_render = True
    # thumbnail test, at a real thumbnail: 150 and 80 px tall
    thumbs = {}
    for L in LETTERS:
        objs[L].hide_render = False
        for name, d, ortho in views:
            thumbs[(L, name)] = shoot_sil([objs[L]], d, (60, 150), ortho=ortho, span=span_all, centre=V((0, -(TIP_Z + 3.9) / 2, 0)))
        objs[L].hide_render = True
    # sheet
    cw, ch, pad = 3 * 150 + 20, 330, 6
    cols = 4
    rows = (len(LETTERS) + cols - 1) // cols
    cv = BD.Canvas(cols * (cw + pad) + pad, rows * (ch + 215 + pad) + pad + 28, bg=(0.93, 0.93, 0.94, 1.0))
    cv.text("Orthodox sword: eleven candidate silhouettes. Black on white, same scale: the flat the player sees, the edge, three-quarter. Chosen one in green.",
            pad, 6, 15, (0.1, 0.1, 0.12, 1))
    for idx, L in enumerate(LETTERS):
        r, c = divmod(idx, cols)
        x0, y0 = pad + c * (cw + pad), 28 + pad + r * (ch + 215 + pad)
        chosen = L == CHOSEN
        cv.rect(x0, y0, cw, ch + 215, (0.82, 0.9, 0.82, 1) if chosen else (0.86, 0.86, 0.89, 1))
        for k, (name, d, ortho) in enumerate(views):
            t = tiles[(L, name)]
            small = t[::2, ::2]                      # 130 x 300
            cv.paste(small, x0 + 6 + k * 150, y0 + 24)
        cv.text("%s  %s%s" % (L, NAMES[L], "   CHOSEN" if chosen else ""), x0 + 6, y0 + 4, 13, (0.05, 0.1, 0.2, 1))
        line, y = "", y0 + 334
        for w in VERDICTS[L].split():
            if len(line + " " + w) > 62:
                cv.text(line, x0 + 6, y, 12, (0.15, 0.15, 0.2, 1))
                y += 15
                line = w
            else:
                line = (line + " " + w).strip()
        cv.text(line, x0 + 6, y, 12, (0.15, 0.15, 0.2, 1))
        for k, (name, d, ortho) in enumerate(views):
            cv.paste(thumbs[(L, name)][::1, ::1], x0 + 6 + k * 150 + 40, y0 + 334 + 56)
    print("study sheet:", cv.save(os.path.join(REVIEW, "silhouette_study.png")))
    # thumbnails only, one row per view
    cv2 = BD.Canvas(len(LETTERS) * 70 + 10, 3 * 160 + 24, bg=(1, 1, 1, 1))
    for k, (name, d, ortho) in enumerate(views):
        for idx, L in enumerate(LETTERS):
            cv2.paste(thumbs[(L, name)], 6 + idx * 70, 4 + k * 160)
    for idx, L in enumerate(LETTERS):
        cv2.text(L, 6 + idx * 70 + 26, 3 * 160 + 4, 14, (0, 0, 0, 1))
    print("thumbnails:", cv2.save(os.path.join(REVIEW, "silhouette_thumbs.png")))


if __name__ == "__main__":
    run()

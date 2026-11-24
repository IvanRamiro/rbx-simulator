"""The Abyssal Lantern Wyrm, stage 1: the reference and silhouette study (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/lantern_wyrm_study.py -- [out_folder]

Eight candidate bodies for the boss of the Origin Abyss, each built from the same parts the real model will use (a tapering serpent tube
along a space curve, a deep dragon head with swept horns, a stalk and lantern, a frill fan, two barbels) and rendered as a black
silhouette in orthographic views: from the side, from three-quarters, from above. They are judged for the myth first (a long
dragon crossed with an anglerfish: would anyone call it a snake?), then for the fight: it must read at 60 studs, the lantern must be the
eye's first stop, the frill must read as a weapon open and as a mane shut, and the whole must fit an 80-stud court with its back to
three plinths (the body stays out of the 18 studs behind the root).

Reference read before drawing (nothing copied: each is a fact about how such creatures are built):
  - lateral undulation of real snakes (Hu et al. 2009 and the Jayne papers found through PubMed Central: the bending wave travels
    tail-ward along the body while every point of it slides along the path the head laid down; the head stays steadier than the tail);
  - the Han-era "nine resemblances" of the Chinese dragon (Wang Fu, via the Wikipedia article): antlers, a long deep head with a broad
    eminence on the brow, a snake's neck, carp scales, a pearl under the chin; the early bronze and jade dragons are COILED;
  - the deep-sea anglerfish (WHOI, Wikipedia): the lure (esca) sits on a stalk (illicium) that rises from the brow and hangs before the
    mouth; its light is cold blue-green there, kept WARM gold here, the boss's identity; a dragonfish carries photophores along its flanks;
  - puddle-knight and Unity/Unreal threads on snake bodies: the head's recorded path read back at each segment's distance is the
    dependable way to make a body follow (chained followers drift apart and split).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../eggs", "../world", "."):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, sub)))
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402
from lantern_wyrm_curve import Curve  # noqa: E402

W = K.W
V = Vector
REPO = W.REPO


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for x in list(block):
            block.remove(x)


def ell(hi, centre, radii, nu=14, nv=9, rot=None):
    c = V(centre)
    rot = rot or Matrix.Identity(3)
    rows = []
    for j in range(nv + 1):
        th = math.pi * j / nv
        row = []
        for i in range(nu):
            a = 2 * math.pi * i / nu
            d = V((math.sin(th) * math.cos(a) * radii[0], -math.cos(th) * radii[1], math.sin(th) * math.sin(a) * radii[2]))
            row.append(hi.v(c + rot @ d))
        rows.append(row)
    for j in range(nv):
        for i in range(nu):
            k = (i + 1) % nu
            hi.f([rows[j][i], rows[j][k], rows[j + 1][k], rows[j + 1][i]], [(0, 0)] * 4)


def tube(hi, pts, radius_fn, sides=10, per=4):
    Hm.htube(hi, [tuple(p) for p in pts], radius_fn, sides=sides, per=per, uv_scale=1.0, tip=True, wobble=0.0)


def sheet(hi, a_pts, b_pts):
    """A strip of quads between two polylines (a frill's membrane from its root to its edge)."""
    for i in range(len(a_pts) - 1):
        ids = [hi.v(a_pts[i]), hi.v(a_pts[i + 1]), hi.v(b_pts[i + 1]), hi.v(b_pts[i])]
        hi.f(ids, [(0, 0)] * 4)
        hi.f(ids[::-1], [(0, 0)] * 4)


# ---------- the parts, in Roblox studs (x right, y up, the front toward -Z) ----------
def radius(t):
    """The body's radius from the tail tip (t = 0) to the neck's top (t = 1): thin tail, a girth of 2.6, a neck of 1.5."""
    if t < 0.5:
        return 0.12 + 2.5 * math.sin(0.5 * math.pi * t / 0.5) ** 1.3
    if t < 0.68:
        return 2.62
    return 2.62 - 1.12 * ((t - 0.68) / 0.32) ** 1.2


def head(hi, base, direction, size=1.0, open_mouth=False):
    """A deep dragon head: skull, muzzle, jaw, two swept horns, two barbels, from the neck's top along `direction`."""
    d = V(direction).normalized()
    side = d.cross(V((0, 1, 0)))
    if side.length < 1e-3:
        side = V((1, 0, 0))
    side.normalize()
    up = side.cross(d)
    rot = Matrix((d, up, side)).transposed()          # local X along the head
    b = V(base)

    def at(a, h, w=0.0):
        return b + d * a * size + up * h * size + side * w * size
    # the head's own frame: ellipsoids elongated along local X
    ell(hi, at(1.6, 0.2), (2.6 * size, 1.5 * size, 1.5 * size), rot=rot)                           # skull and brow
    ell(hi, at(5.4, -0.15), (3.3 * size, 1.0 * size, 1.05 * size), rot=rot)                        # the long muzzle
    ell(hi, at(4.6, -1.15 - (0.7 if open_mouth else 0)), (3.1 * size, 0.55 * size, 0.95 * size), rot=rot)   # the jaw
    for sg in (-1, 1):
        tube(hi, [at(1.0, 1.2, sg * 0.8), at(-0.6, 2.6, sg * 1.6), at(-3.2, 3.4, sg * 2.4), at(-5.4, 3.0, sg * 3.0)], lambda t: 0.36 * (1 - t) ** 0.8 + 0.04)   # the horns, swept back
        tube(hi, [at(7.6, -0.4, sg * 0.9), at(5.0, -0.2, sg * 2.4), at(1.0, -0.5, sg * 4.2), at(-3.0, -1.6, sg * 5.0), at(-7.0, -3.4, sg * 5.4)], lambda t: 0.1 * (1 - t) + 0.025)  # barbels
    return at


def lantern(hi, at, rise=3.2, reach=4.4, drop=0.4, size=1.0):
    """The stalk: up from the brow, over, and down before the face; the lamp at its end."""
    pts = [at(1.4, 1.4), at(1.6, 1.4 + rise * 0.8), at(1.9 + reach * 0.4, 1.4 + rise), at(1.9 + reach, 1.4 + rise * 0.7 - drop)]
    tube(hi, pts, lambda t: 0.26 - 0.1 * t, sides=6, per=6)
    ell(hi, pts[-1] + V((0, -0.2, 0)), (0.8 * size, 0.8 * size, 0.8 * size), nu=10, nv=7)


def frill(hi, curve, s0, s1, n, length_fn, back=0.5, spread=0.0, lateral=0.0):
    """A fan of ribs along the spine between arc lengths s0 and s1: the membrane between their tips. `lateral` pushes the ribs out sideways."""
    roots, tips = [], []
    for i in range(n):
        s = s0 + (s1 - s0) * i / (n - 1)
        p = curve.at(s)
        tg = curve.tangent(s)
        up = V((0, 1, 0)) - tg * tg.y
        up = up.normalized() if up.length > 0.2 else V((0, 0, 1))
        side = tg.cross(up)
        L = length_fn(i / (n - 1))
        d = (up * math.cos(spread) + tg * back * -1 + side * lateral).normalized()
        roots.append(p + up * 1.2)
        tips.append(p + up * 1.2 + d * L)
    sheet(hi, roots, tips)


def build(spec, name):
    """One candidate: the spine's control points run from the tail tip to the neck's top."""
    hi = Hm.Hi()
    ctrl = [V(p) for p in spec["spine"]]
    cv = Curve(ctrl, per=14)
    n = int(cv.length / 0.9)
    pts = [cv.at(cv.length * i / n) for i in range(n + 1)]
    tube(hi, pts, lambda t: radius(t) * spec.get("girth", 1.0), sides=10, per=1)
    top = ctrl[-1]
    at = head(hi, top, spec["head"], size=spec.get("hsize", 1.0), open_mouth=spec.get("open", False))
    lantern(hi, at, **spec.get("lantern", {}))
    for fr in spec.get("frills", []):
        sa, sb = fr["from"], fr["to"]
        frill(hi, cv, cv.length * sa, cv.length * sb, 14, fr["len"], back=fr.get("back", 0.5), lateral=fr.get("lateral", 0.0))
        if fr.get("lateral", 0.0):
            frill(hi, cv, cv.length * sa, cv.length * sb, 14, fr["len"], back=fr.get("back", 0.5), lateral=-fr.get("lateral", 0.0))
    for extra in spec.get("extra", []):
        extra(hi)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (0.01, 0.01, 0.015, 1)
    o = hi.object(name, bpy.context.scene.collection, [mat], smooth=False, weld=0)
    return o, cv


def zig(n, amp, z0, z1, y0, y1):
    """A zigzag pile on the ground: n crossings between x = +amp and -amp from z0 to z1."""
    out = []
    for k in range(n + 1):
        t = k / n
        out.append((amp * (1 if k % 2 == 0 else -1), y0 + (y1 - y0) * t, z0 + (z1 - z0) * t))
    return out


def spiral(turns, r0, r1, cz, y0, y1, a0=0.0, steps=14):
    out = []
    for i in range(int(turns * steps) + 1):
        t = i / max(1, int(turns * steps))
        a = a0 + 2 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        out.append((r * math.cos(a), y0 + (y1 - y0) * t, cz + r * math.sin(a)))
    return out


def candidates():
    mane = lambda t: 5.5 + 3 * math.sin(math.pi * min(1, t * 1.15)) * (1 - 0.5 * t)
    return {
        # A: the swan: a raised S of neck, a lateral pile behind it, the lantern on a stalk before the face, a shut-able mane along the neck
        "A swan": dict(spine=zig(3, 7.5, 16, 4, 0.6, 2.4) + [(0, 2.6, 0), (0, 4, -4.5), (0, 9, -6.5), (0, 14, -4.5), (0, 19, -1), (0, 23, -1.5), (0, 25.4, -6)],
                       head=(-0.1, -0.2, -1), frills=[dict(**{"from": 0.62, "to": 0.97, "len": mane, "back": 0.6})]),
        # B: the cobra tower: the neck straight up, a hood open round the head, a spiral under it
        "B cobra": dict(spine=spiral(1.25, 7, 4.2, 2, 0.6, 3.0, a0=0.4) + [(0, 3, 0), (0, 9, 0.4), (0, 16, 0), (0, 22, -0.5), (0, 27, -1.2)],
                        head=(0.0, -0.3, -1), frills=[dict(**{"from": 0.78, "to": 0.99, "len": lambda t: 10 - 3 * abs(t - 0.5), "back": 0.15, "lateral": 0.9})],
                        lantern=dict(rise=2.4, reach=3.2, drop=1.4)),
        # C: the ambusher: the neck low and forward, the head near the ground, a long dorsal sail, the lantern ahead like a lure
        "C ambush": dict(spine=zig(3, 8, 24, 8, 0.6, 2.2) + [(0, 2.6, 0), (0, 3.2, -6), (0, 4.4, -12), (0, 5.2, -18), (0, 6.2, -23)],
                         head=(0, -0.12, -1), hsize=1.1, open=True, frills=[dict(**{"from": 0.36, "to": 0.97, "len": lambda t: 4.5 - 2.5 * abs(t - 0.5), "back": 0.2})],
                         lantern=dict(rise=2.0, reach=6.5, drop=1.0)),
        # D: the arch: the neck reared and bowed over, the head pointing down, the lantern swinging near the ground
        "D arch": dict(spine=zig(3, 7, 18, 6, 0.6, 2.4) + [(0, 2.6, 0), (0, 10, 2), (0, 18, 0.5), (0, 22.5, -5), (0, 21.5, -12), (0, 17, -16)],
                       head=(-0.0, -0.8, -0.55), frills=[dict(**{"from": 0.66, "to": 0.96, "len": lambda t: 5 + 2 * t, "back": 0.9})],
                       lantern=dict(rise=1.4, reach=3.0, drop=3.8)),
        # E: the totem: a stacked coil, the neck an S above it
        "E totem": dict(spine=spiral(1.7, 6.2, 3.8, 0, 0.6, 8.2, a0=0.2, steps=12) + [(0, 8.5, 0), (0, 13, -2.4), (0, 18, 0), (0, 22.5, -2.5), (0, 25, -6)],
                        head=(0, -0.15, -1), frills=[dict(**{"from": 0.72, "to": 0.98, "len": mane, "back": 0.5})]),
        # F: the ribbon: swimming through the air in three arches, the head high and forward
        "F ribbon": dict(spine=[(0, 8 + 7 * math.sin(0.5 * k), 36 - 3.4 * k) for k in range(0, 14)] + [(0, 14, -8), (0, 17, -12), (0, 20, -15)],
                         head=(0, 0.15, -1), girth=0.9, frills=[dict(**{"from": 0.7, "to": 0.97, "len": lambda t: 4.5, "back": 0.4})]),
        # G: the ring: coiled round the court's centre with the neck and head rising over the ring's front
        "G ring": dict(spine=spiral(1.0, 9.5, 8.8, 0, 0.6, 2.4, a0=-1.2, steps=12) + [(0, 2.6, -9), (0, 7, -10.5), (0, 13, -9), (0, 18, -10.5), (0, 22, -14)],
                       head=(0, -0.25, -1), frills=[dict(**{"from": 0.72, "to": 0.98, "len": mane, "back": 0.6})]),
        # H: the mane: a short heavy neck, a vast round mane about the head like a lion's, the pile behind
        "H mane": dict(spine=zig(3, 7.5, 16, 4, 0.6, 2.4) + [(0, 2.6, 0), (0, 6, -3), (0, 10.5, -2.5), (0, 14.5, -5), (0, 17, -9.5)],
                       head=(0, -0.3, -1), hsize=1.15, girth=1.1,
                       frills=[dict(**{"from": 0.8, "to": 0.99, "len": lambda t: 11 - 4 * abs(t - 0.5), "back": 0.05, "lateral": 1.0})]),
    }


def review_scene(size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "FLAT"
    sh.color_type = "MATERIAL"
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.92, 0.93, 0.95)
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    data = bpy.data.cameras.new("StudyCam")
    data.type = "ORTHO"
    cam = bpy.data.objects.new("StudyCam", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return scene, cam, data


def shot(scene, cam, data, yaw, pitch, centre, scale, size, tmp):
    import numpy as np
    y, p = math.radians(yaw), math.radians(pitch)
    c = V(centre)
    cam.location = c + V((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * 160
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    data.ortho_scale = scale
    bpy.context.view_layer.update()
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp, check_existing=False)
    px = np.zeros(size * size * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(size, size, 4)


def run(out_dir, size=440):
    import numpy as np
    clear()
    scene, cam, data = review_scene(size)
    tmp = os.path.join(out_dir, "_t.png")
    names = list(candidates())
    rows = []
    for name in names:
        clear()
        scene, cam, data = review_scene(size)
        o, cv = build(candidates()[name], name)
        o.matrix_world = Matrix.Identity(4)
        # Roblox space is converted by the Hi helper: the object is already in Blender space
        c = W.rb(0, 12, -5)
        tiles = [shot(scene, cam, data, -90, 0, c, 62, size, tmp), shot(scene, cam, data, -35, 18, c, 62, size, tmp), shot(scene, cam, data, 0, 90, W.rb(0, 6, 6), 60, size, tmp)]
        rows.append(np.concatenate(tiles, axis=1))
    sheet_img = np.concatenate(rows, axis=0)
    h, w = sheet_img.shape[:2]
    img = bpy.data.images.new("Study", w, h)
    img.pixels.foreach_set(sheet_img.ravel())
    img.filepath_raw = os.path.join(out_dir, "study.png")
    img.file_format = "PNG"
    img.save()
    if os.path.exists(tmp):
        os.remove(tmp)
    return names


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[0] if argv else os.path.join(REPO, "renders", "lantern_wyrm", "study")
    os.makedirs(out, exist_ok=True)
    print("STUDY", run(out))

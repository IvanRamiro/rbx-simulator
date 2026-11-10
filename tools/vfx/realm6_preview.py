"""Offline previews of the Realm 6 elements, rendered straight from tools/vfx/realm6_elements.py (no Studio): a dark
stage, a stand-in dummy, and the element's Beams, ParticleEmitters and Trails drawn the way Roblox draws them, closely
enough to judge composition, scale, colour and layering (not a pixel match: bloom, lighting and Roblox's exact drag and
squash curves are approximated).

    python3 tools/vfx/realm6_preview.py <Element|All> <out.png> [view] [time]
        view: back (default: the gameplay camera, behind and above), front, side, top
        time: seconds into the effect (default 12, steady state)

Conventions mirrored from Studio (measured, see the vault): a Beam lays its texture's vertical axis along its length,
the image's top at Attachment0 and its bottom at Attachment1; curve handles along each attachment's X (Attachment0 + X0 *
CurveSize0, Attachment1 - X1 * CurveSize1); with FaceCamera off its width runs along the attachments' Y. A Trail lays the
texture's horizontal axis along its length. A ParticleEmitter on an Attachment emits along the attachment's +Y.
"""
import math
import os
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realm6_elements as E  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W, H = 1280, 720
VIEWS = {
    "back": ((0.0, 8.5, 15.0), (0.0, 3.0, 0.0)),
    "front": ((0.0, 5.0, -15.0), (0.0, 3.2, 0.0)),
    "side": ((-16.0, 5.0, 0.5), (0.0, 3.2, 0.5)),
    "top": ((0.01, 22.0, 0.5), (0.0, 0.0, 0.0)),
    "far": ((0.0, 16.0, 30.0), (0.0, 8.0, 0.0)),
}


# ---- maths --------------------------------------------------------------------------------------------------------
def v3(*a):
    return np.array(a, dtype=np.float64)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


class Camera:
    def __init__(self, eye, target, fov=62.0):
        self.eye = v3(*eye)
        f = unit(v3(*target) - self.eye)
        up = v3(0, 1, 0) if abs(f[1]) < 0.99 else v3(0, 0, -1)
        r = unit(np.cross(f, up))
        self.f, self.r, self.u = f, r, np.cross(r, f)
        self.focal = (H / 2) / math.tan(math.radians(fov) / 2)

    def project(self, p):
        d = np.asarray(p) - self.eye
        z = d @ self.f
        z = np.maximum(z, 0.05)
        x = W / 2 + (d @ self.r) / z * self.focal
        y = H / 2 - (d @ self.u) / z * self.focal
        return x, y, z


# ---- sequences ----------------------------------------------------------------------------------------------------
def ns_eval(seq, t, rnd=0.0):
    keys = seq[1]
    t = min(max(t, 0.0), 1.0)
    for (t0, *a), (t1, *b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            v = a[0] + (b[0] - a[0]) * f
            env = (a[1] if len(a) > 1 else 0) + ((b[1] if len(b) > 1 else 0) - (a[1] if len(a) > 1 else 0)) * f
            return v + env * rnd
    return keys[-1][1]


def cs_eval(seq, t):
    keys = seq[1]
    t = min(max(t, 0.0), 1.0)
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return np.array([a[i] + (b[i] - a[i]) * f for i in range(3)]) / 255.0
    return np.array(keys[-1][1]) / 255.0


# ---- textures -----------------------------------------------------------------------------------------------------
_TEX = {}


def texture(name):
    if name not in _TEX:
        im = Image.open(os.path.join(ROOT, E.TEXTURES[name][0])).convert("RGBA")
        _TEX[name] = np.asarray(im, dtype=np.float32) / 255.0
    return _TEX[name]


def sample(tex, u, v, wrap_v=False, wrap_u=False):
    h, w = tex.shape[:2]
    u = np.mod(u, 1.0) if wrap_u else np.clip(u, 0.0, 1.0)
    v = np.mod(v, 1.0) if wrap_v else np.clip(v, 0.0, 1.0)
    x = u * (w - 1)
    y = v * (h - 1)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1) if not wrap_u else (x0 + 1) % w
    y1 = np.minimum(y0 + 1, h - 1) if not wrap_v else (y0 + 1) % h
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    a = tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx
    b = tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx
    return a * (1 - fy) + b * fy


# ---- the canvas ---------------------------------------------------------------------------------------------------
class Canvas:
    def __init__(self, cam):
        self.cam = cam
        self.items = []
        self.img = self.stage()

    def stage(self):
        im = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(im)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=(int(40 + 60 * t), int(80 + 70 * t), int(160 + 50 * t)))
        # the platform: a 25-stud square at y = 0
        corners = [v3(-12.7, 0, -12.7), v3(12.7, 0, -12.7), v3(12.7, 0, 12.7), v3(-12.7, 0, 12.7)]
        pts = []
        for c in corners:
            x, y, _ = self.cam.project(c)
            pts.append((float(x), float(y)))
        d.polygon(pts, fill=(14, 22, 70))
        return np.asarray(im, dtype=np.float32) / 255.0

    def add(self, depth, fn):
        self.items.append((depth, fn))

    def tri(self, P, UV, tex, color, alpha, le, wrap_v=False, wrap_u=False):
        """A textured triangle: P screen (3x2), UV (3x2), colour (3,), alpha (3,) per vertex."""
        xmin, xmax = int(max(math.floor(P[:, 0].min()), 0)), int(min(math.ceil(P[:, 0].max()), W - 1))
        ymin, ymax = int(max(math.floor(P[:, 1].min()), 0)), int(min(math.ceil(P[:, 1].max()), H - 1))
        if xmax < xmin or ymax < ymin:
            return
        ys, xs = np.mgrid[ymin : ymax + 1, xmin : xmax + 1].astype(np.float64) + 0.5
        (x0, y0), (x1, y1), (x2, y2) = P
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            return
        l0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
        l1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            return
        u = l0 * UV[0, 0] + l1 * UV[1, 0] + l2 * UV[2, 0]
        v = l0 * UV[0, 1] + l1 * UV[1, 1] + l2 * UV[2, 1]
        a = (l0 * alpha[0] + l1 * alpha[1] + l2 * alpha[2])[m]
        s = sample(tex, u[m], v[m], wrap_v, wrap_u)
        ta = s[:, 3] * a
        rgb = s[:, :3] * color[None, :]
        region = self.img[ymin : ymax + 1, xmin : xmax + 1]
        px = region[m]
        px = px * (1 - (ta * (1 - le))[:, None]) + rgb * ta[:, None]
        region[m] = px

    def render(self):
        for depth, fn in sorted(self.items, key=lambda it: -it[0]):
            fn()
        img = np.clip(self.img, 0, 1)
        return Image.fromarray((img * 255).astype(np.uint8))


# ---- the stand-in dummy -------------------------------------------------------------------------------------------
BOXES = [  # (centre, half size): legs, torso, arms, head, in the character frame (the dummy is 5 studs tall)
    ((-0.42, 1.0, 0.0), (0.4, 1.0, 0.42)), ((0.42, 1.0, 0.0), (0.4, 1.0, 0.42)),
    ((0.0, 2.85, 0.0), (0.85, 0.85, 0.45)), ((-1.22, 2.85, 0.0), (0.36, 0.85, 0.4)), ((1.22, 2.85, 0.0), (0.36, 0.85, 0.4)),
    ((0.0, 4.3, 0.0), (0.5, 0.55, 0.5)),
]


def add_dummy(cv):
    cam = cv.cam
    for c, hs in BOXES:
        c, hs = v3(*c), v3(*hs)

        def draw(c=c, hs=hs):
            im = Image.fromarray((np.clip(cv.img, 0, 1) * 255).astype(np.uint8))
            d = ImageDraw.Draw(im)
            faces = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]
            for axis, sgn in faces:
                n = np.zeros(3)
                n[axis] = sgn
                centre = c + n * hs
                if (centre - cam.eye) @ n >= 0:
                    continue
                o = [i for i in range(3) if i != axis]
                pts = []
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    p = centre.copy()
                    p[o[0]] += a * hs[o[0]]
                    p[o[1]] += b * hs[o[1]]
                    x, y, _ = cam.project(p)
                    pts.append((float(x), float(y)))
                shade = 14 + int(10 * max(0, n @ unit(v3(0.3, 1, 0.5))))
                d.polygon(pts, fill=(shade, shade, shade + 8))
            cv.img = np.asarray(im, dtype=np.float32) / 255.0

        cv.add(float(cam.project(c)[2]), draw)


# ---- beams --------------------------------------------------------------------------------------------------------
def bezier(p0, p1, p2, p3, t):
    a = (1 - t) ** 3
    b = 3 * (1 - t) ** 2 * t
    c = 3 * (1 - t) * t * t
    d = t ** 3
    return a * p0 + b * p1 + c * p2 + d * p3


def add_beam(cv, beam, atts, time):
    cam = cv.cam
    A0, A1 = atts[beam["a0"]], atts[beam["a1"]]
    p0, p3 = v3(*A0["pos"]), v3(*A1["pos"])
    p1 = p0 + v3(*A0["x"]) * beam["CurveSize0"]
    p2 = p3 - v3(*A1["x"]) * beam["CurveSize1"]
    n = max(8, beam["Segments"] * 4, int(max(beam["Width0"], beam["Width1"]) / 0.5))
    tex = texture(beam["Texture"][1])
    stretch = beam["TextureMode"][2] == "Stretch"
    length = sum(np.linalg.norm(bezier(p0, p1, p2, p3, (k + 1) / n) - bezier(p0, p1, p2, p3, k / n)) for k in range(n))
    scroll = beam["TextureSpeed"] * time
    rows = []
    for k in range(n + 1):
        t = k / n
        p = bezier(p0, p1, p2, p3, t)
        tan = unit(bezier(p0, p1, p2, p3, min(t + 1e-3, 1)) - bezier(p0, p1, p2, p3, max(t - 1e-3, 0)))
        if beam["FaceCamera"]:
            side = unit(np.cross(tan, p - cam.eye))
        else:
            side = unit((1 - t) * v3(*A0["y"]) + t * v3(*A1["y"]))
        w = (1 - t) * beam["Width0"] + t * beam["Width1"]
        vv = (t * beam["TextureLength"] if stretch else t * length / beam["TextureLength"]) - scroll
        colour = cs_eval(beam["Color"], t) * beam["Brightness"]
        alpha = 1 - ns_eval(beam["Transparency"], t)
        rows.append((p - side * w / 2, p + side * w / 2, vv, colour, alpha, p))
    le = beam["LightEmission"]
    cols = max(1, int(max(beam["Width0"], beam["Width1"]) / 0.5))  # wide beams split across too (the GPU is perspective-correct)
    for (l0, r0, v0, c0, a0, m0), (l1, r1, v1, c1, a1, m1) in zip(rows[:-1], rows[1:]):
        colour = (c0 + c1) / 2
        for q in range(cols):
            f0, f1 = q / cols, (q + 1) / cols
            quad = [l0 + (r0 - l0) * f0, l0 + (r0 - l0) * f1, l1 + (r1 - l1) * f1, l1 + (r1 - l1) * f0]
            uvs = [(f0, v0), (f1, v0), (f1, v1), (f0, v1)]
            al = [a0, a0, a1, a1]
            depth = float(cam.project(sum(quad) / 4)[2])

            def draw(quad=quad, uvs=uvs, colour=colour, al=al):
                sp = np.array([cam.project(qq)[:2] for qq in quad], dtype=np.float64)
                uv = np.array(uvs, dtype=np.float64)
                alv = np.array(al)
                for i, j, k in ((0, 1, 2), (0, 2, 3)):
                    cv.tri(sp[[i, j, k]], uv[[i, j, k]], tex, colour, alv[[i, j, k]], le, wrap_v=True)

            cv.add(depth, draw)


# ---- motion (mirrors src/client/Auras/Realm6Motion.lua) -----------------------------------------------------------
def motion_positions(m, t):
    """(A, B, cycle) for a moving attachment pair at time t."""
    s_total = t / E.VORTEX["period"] + m["phase"]
    cycle = math.floor(s_total)
    p, _ = E.helix(m["arm"], s_total - cycle)
    a = v3(*p)
    return a, a + v3(0, m["width"], 0), cycle


def attachment_at(name, atts, motion, t):
    for m in motion:
        if name in (m["a"], m["b"]):
            a, b, _ = motion_positions(m, t)
            return (a if name == m["a"] else b), v3(0, 1, 0)
    A = atts[name]
    return v3(*A["pos"]), v3(*A["y"])


# ---- trails -------------------------------------------------------------------------------------------------------
def add_trail(cv, trail, motion, time):
    cam = cv.cam
    m = next(x for x in motion if x["trail"] == trail["name"])
    life = trail["Lifetime"]
    tex = texture(trail["Texture"][1])
    _, _, cycle_now = motion_positions(m, time)
    samples = []
    steps = 40
    for k in range(steps + 1):
        age = k / steps * life
        a, b, cyc = motion_positions(m, time - age)
        if cyc != cycle_now:  # the driver clears the trail when a comet starts its run again
            break
        samples.append((age / life, a, b))
    if len(samples) < 2:
        return
    rows = []
    for i, (f, a, b) in enumerate(samples):
        c = (a + b) / 2
        nxt = samples[min(i + 1, len(samples) - 1)][1:]
        prv = samples[max(i - 1, 0)][1:]
        tan = unit((nxt[0] + nxt[1]) / 2 - (prv[0] + prv[1]) / 2)
        side = unit(np.cross(tan, c - cam.eye)) if trail["FaceCamera"] else unit(b - a)
        w = np.linalg.norm(b - a) * ns_eval(trail["WidthScale"], f)
        rows.append((c - side * w / 2, c + side * w / 2, f, cs_eval(trail["Color"], f) * trail["Brightness"],
                     1 - ns_eval(trail["Transparency"], f), c))
    le = trail["LightEmission"]
    for (l0, r0, f0, c0, a0, m0), (l1, r1, f1, c1, a1, m1) in zip(rows[:-1], rows[1:]):
        quad = [l0, r0, r1, l1]
        uvs = [(f0, 0), (f0, 1), (f1, 1), (f1, 0)]  # the texture's horizontal axis along the trail
        colour = (c0 + c1) / 2
        al = [a0, a0, a1, a1]
        depth = float(cam.project((m0 + m1) / 2)[2])

        def draw(quad=quad, uvs=uvs, colour=colour, al=al):
            sp = np.array([cam.project(q)[:2] for q in quad], dtype=np.float64)
            uv = np.array(uvs, dtype=np.float64)
            alv = np.array(al)
            for i, j, k in ((0, 1, 2), (0, 2, 3)):
                cv.tri(sp[[i, j, k]], uv[[i, j, k]], tex, colour, alv[[i, j, k]], le, wrap_u=True)

        cv.add(depth, draw)


# ---- particles ----------------------------------------------------------------------------------------------------
def rotate_about(v, axis, ang):
    axis = unit(axis)
    return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * (axis @ v) * (1 - math.cos(ang))


def add_emitter(cv, em, atts, motion, time):
    cam = cv.cam
    rng = np.random.default_rng(zlib.crc32(em["name"].encode()))
    rate = em["Rate"]
    lo, hi = em["Lifetime"][1], em["Lifetime"][2]
    tex = texture(em["Texture"][1])
    layout = em.get("FlipbookLayout", ("E", "", "None"))[2]
    cells = {"None": 1, "Grid2x2": 2, "Grid4x4": 4}[layout]
    mode = em.get("FlipbookMode", ("E", "", "Loop"))[2]
    drag = em["Drag"] * math.log(2)
    acc = v3(*em["Acceleration"][1:])
    sx, sz = math.radians(em["SpreadAngle"][1]), math.radians(em["SpreadAngle"][2])
    count = int(hi * rate) + 2
    offset = rng.random()
    for k in range(count):
        te = time - (k + offset) / rate
        life = rng.uniform(lo, hi)
        r = rng.random(8)
        age = time - te
        if age < 0 or age > life:
            continue
        f = age / life
        p0, ydir = attachment_at(em["parent"], atts, motion, te)
        A = atts[em["parent"]]
        xdir = v3(*A["x"])
        zdir = unit(np.cross(xdir, ydir))
        d = rotate_about(rotate_about(ydir, xdir, (r[0] * 2 - 1) * sx), zdir, (r[1] * 2 - 1) * sz)
        speed = em["Speed"][1] + (em["Speed"][2] - em["Speed"][1]) * r[2]
        v0 = d * speed
        if drag > 1e-6:
            e = math.exp(-drag * age)
            pos = p0 + v0 * (1 - e) / drag + acc * (age / drag - (1 - e) / drag ** 2)
            vel = v0 * e + acc * (1 - e) / drag
        else:
            pos = p0 + v0 * age + 0.5 * acc * age * age
            vel = v0 + acc * age
        size = max(ns_eval(em["Size"], f, r[3] * 2 - 1), 0.0)
        alpha = 1 - ns_eval(em["Transparency"], f)
        if size <= 1e-3 or alpha <= 1e-3:
            continue
        colour = cs_eval(em["Color"], f) * em["Brightness"]
        rot = math.radians(em["Rotation"][1] + (em["Rotation"][2] - em["Rotation"][1]) * r[4]
                           + (em["RotSpeed"][1] + (em["RotSpeed"][2] - em["RotSpeed"][1]) * r[5]) * age)
        if cells > 1:
            frame = min(int(f * cells * cells), cells * cells - 1) if mode == "OneShot" else int(r[6] * cells * cells)
        else:
            frame = 0
        squash = ns_eval(em["Squash"], f) if "Squash" in em else 0.0
        orient = em["Orientation"][2]
        depth = float(cam.project(pos)[2]) - em.get("ZOffset", 0)

        def draw(pos=pos, vel=vel, size=size, alpha=alpha, colour=colour, rot=rot, frame=frame, squash=squash, orient=orient):
            x, y, z = cam.project(pos)
            px = size * cam.focal / z
            hgt = px * (1 + squash * 0.6)
            wid = px / (1 + squash * 0.25)
            if orient == "VelocityParallel":
                x2, y2, _ = cam.project(pos + unit(vel) * 0.5)
                ang = math.atan2(x2 - x, -(y2 - y))
            else:
                ang = rot
            ca, sa = math.cos(ang), math.sin(ang)
            upv = np.array([sa, -ca]) * hgt / 2
            rtv = np.array([ca, sa]) * wid / 2
            c = np.array([x, y])
            quad = np.array([c - rtv + upv, c + rtv + upv, c + rtv - upv, c - rtv - upv])  # top-left, top-right, bottom...
            cr, cc = divmod(frame, cells)
            u0, u1 = cc / cells, (cc + 1) / cells
            v0_, v1_ = cr / cells, (cr + 1) / cells
            uv = np.array([(u0, v0_), (u1, v0_), (u1, v1_), (u0, v1_)])
            al = np.array([alpha] * 4)
            for i, j, kk in ((0, 1, 2), (0, 2, 3)):
                cv.tri(quad[[i, j, kk]], uv[[i, j, kk]], tex, colour, al[[i, j, kk]], em["LightEmission"])

        cv.add(depth, draw)


# ---- an element ---------------------------------------------------------------------------------------------------
def render(names, out, view="back", time=12.0, title=None):
    cam = Camera(*VIEWS[view])
    cv = Canvas(cam)
    add_dummy(cv)
    for spec in names:
        name, _, part = spec.partition(":")  # "Sigils:Rosette" renders only the pieces whose names hold "Rosette"
        el = E.ELEMENTS[name]()
        atts = {a["name"]: a for a in el["attachments"]}
        motion = el.get("motion", [])
        keep = (lambda n: part in n) if part else (lambda n: True)
        for b in el["beams"]:
            if keep(b["name"]):
                add_beam(cv, b, atts, time)
        for t in el["trails"]:
            if keep(t["name"]):
                add_trail(cv, t, motion, time)
        for em in el["emitters"]:
            if keep(em["name"]):
                add_emitter(cv, em, atts, motion, time)
    im = cv.render()
    if title:
        ImageDraw.Draw(im).text((14, 12), title, fill=(235, 235, 240))
    im.save(out)
    return out


if __name__ == "__main__":
    which = sys.argv[1]
    out = sys.argv[2]
    view = sys.argv[3] if len(sys.argv) > 3 else "back"
    t = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0
    names = E.ORDER if which == "All" else which.split(",")
    print(render(names, out, view, t, title="%s  (%s view, t = %.1f s; offline preview)" % (which, view, t)))

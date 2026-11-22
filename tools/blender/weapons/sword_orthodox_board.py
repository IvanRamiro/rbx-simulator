"""A tiny 2D drawing kit for the Orthodox sword's review boards (run inside Blender, headless): the research board,
the silhouette study, the maps sheet. Blender has no PIL here, so this is numpy: anti-aliased polygons, lines, discs,
and text rendered through a Blender text object (Workbench, flat). Review images only: nothing here is ever a game texture.
"""
import math
import os
import tempfile

import bpy
import numpy as np
from mathutils import Vector

_TEXT_CACHE = {}


class Canvas:
    """An RGBA float canvas, top row first; drawing coordinates are pixels, y down."""

    def __init__(self, w, h, bg=(0.07, 0.075, 0.09, 1.0), ss=3):
        self.w, self.h, self.ss = w, h, ss
        self.px = np.zeros((h, w, 4), dtype=np.float32)
        self.px[:] = bg

    # ---- shapes (anti-aliased by coverage supersampling) ----
    def _coverage(self, mask_fn, bbox):
        x0, y0, x1, y1 = bbox
        x0, y0 = max(0, int(math.floor(x0)) - 1), max(0, int(math.floor(y0)) - 1)
        x1, y1 = min(self.w, int(math.ceil(x1)) + 1), min(self.h, int(math.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0:
            return None
        s = self.ss
        xs = x0 + (np.arange((x1 - x0) * s) + 0.5) / s
        ys = y0 + (np.arange((y1 - y0) * s) + 0.5) / s
        gx, gy = np.meshgrid(xs, ys)
        m = mask_fn(gx, gy).astype(np.float32)
        cov = m.reshape(y1 - y0, s, x1 - x0, s).mean((1, 3))
        return x0, y0, x1, y1, cov

    def _blend(self, cov_pack, color):
        if cov_pack is None:
            return
        x0, y0, x1, y1, cov = cov_pack
        a = (cov * color[3])[..., None]
        self.px[y0:y1, x0:x1, :3] = self.px[y0:y1, x0:x1, :3] * (1 - a) + np.array(color[:3], dtype=np.float32) * a

    def polygon(self, pts, color, holes=()):
        """Even-odd filled polygon (and holes: more polygons cut out of it), pts in pixels."""
        loops = [np.array(pts, dtype=np.float64)] + [np.array(h, dtype=np.float64) for h in holes]
        allp = np.concatenate(loops)
        bbox = (allp[:, 0].min(), allp[:, 1].min(), allp[:, 0].max(), allp[:, 1].max())

        def inside(gx, gy):
            res = np.zeros(gx.shape, dtype=bool)
            for loop in loops:
                n = len(loop)
                for i in range(n):
                    xa, ya = loop[i]
                    xb, yb = loop[(i + 1) % n]
                    if ya == yb:
                        continue
                    cond = ((ya > gy) != (yb > gy)) & (gx < (xb - xa) * (gy - ya) / (yb - ya) + xa)
                    res ^= cond
            return res
        self._blend(self._coverage(inside, bbox), color)

    def disc(self, cx, cy, r, color, hole=0.0):
        def inside(gx, gy):
            d = (gx - cx) ** 2 + (gy - cy) ** 2
            return (d <= r * r) & (d >= hole * hole)
        self._blend(self._coverage(inside, (cx - r, cy - r, cx + r, cy + r)), color)

    def line(self, a, b, color, width=1.0):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        ln2 = dx * dx + dy * dy or 1e-9
        hw = width / 2

        def inside(gx, gy):
            t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / ln2, 0, 1)
            return (gx - (ax + t * dx)) ** 2 + (gy - (ay + t * dy)) ** 2 <= hw * hw
        self._blend(self._coverage(inside, (min(ax, bx) - hw, min(ay, by) - hw, max(ax, bx) + hw, max(ay, by) + hw)), color)

    def polyline(self, pts, color, width=1.0, closed=False):
        n = len(pts)
        for i in range(n - 1 + (1 if closed else 0)):
            self.line(pts[i], pts[(i + 1) % n], color, width)

    def rect(self, x, y, w, h, color):
        self.px[int(y):int(y + h), int(x):int(x + w), :3] = self.px[int(y):int(y + h), int(x):int(x + w), :3] * (1 - color[3]) + np.array(color[:3]) * color[3]

    def paste(self, tile, x, y):
        """An RGBA tile composited at (x, y)."""
        h, w = tile.shape[:2]
        x, y = int(x), int(y)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        t = tile[y0 - y:y1 - y, x0 - x:x1 - x]
        a = t[..., 3:4]
        self.px[y0:y1, x0:x1, :3] = self.px[y0:y1, x0:x1, :3] * (1 - a) + t[..., :3] * a

    def text(self, s, x, y, size=16, color=(0.9, 0.92, 0.95, 1.0), anchor="tl"):
        tile = text_tile(s, size)
        h, w = tile.shape[:2]
        ox = x - (w if "r" in anchor else w / 2 if "c" in anchor else 0)
        oy = y - (h if "b" in anchor else 0)
        t = tile.copy()
        t[..., :3] = np.array(color[:3], dtype=np.float32)
        t[..., 3] = t[..., 3] * color[3]
        self.paste(t, ox, oy)
        return w, h

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        save_png(self.px, path)
        return path


def text_tile(s, px=16):
    """White text on transparent, `px` pixels tall (cap height about 0.7 of that), via a Blender text object."""
    key = (s, px)
    if key in _TEXT_CACHE:
        return _TEXT_CACHE[key]
    scene = bpy.context.scene
    keep = {k: getattr(scene.render, k) for k in ("engine", "resolution_x", "resolution_y", "film_transparent", "filepath", "resolution_percentage")}
    cam_keep = scene.camera
    hidden = [(o, o.hide_render) for o in bpy.data.objects]
    for o, _ in hidden:
        o.hide_render = True       # the factory cube, a weapon in the scene: none of it may show behind a label
    cu = bpy.data.curves.new("BT", "FONT")
    cu.body = s
    cu.size = 1.0
    ob = bpy.data.objects.new("BT", cu)
    scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    w = max(0.2, x1 - x0)
    cam = bpy.data.cameras.new("BTC")
    cam.type = "ORTHO"
    cam.sensor_fit = "HORIZONTAL"
    cam.ortho_scale = w + 0.3
    co = bpy.data.objects.new("BTC", cam)
    scene.collection.objects.link(co)
    co.location = (x0 + w / 2, 0.3, 5)
    scene.camera = co
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.film_transparent = True
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = max(4, int((w + 0.3) * px * 0.78))
    scene.render.resolution_y = max(4, int(px * 1.3))
    cam.shift_y = 0.0
    sh = scene.display.shading
    sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (1, 1, 1)
    tmp = os.path.join(tempfile.gettempdir(), "_sw_text_%d.png" % os.getpid())
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp, check_existing=False)
    wd, ht = img.size
    arr = np.zeros(wd * ht * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    os.remove(tmp)
    arr = arr.reshape(ht, wd, 4)[::-1].copy()
    for k, v in keep.items():
        setattr(scene.render, k, v)
    scene.camera = cam_keep
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.objects.remove(co, do_unlink=True)
    for o, h in hidden:
        o.hide_render = h
    bpy.data.curves.remove(cu)
    bpy.data.cameras.remove(cam)
    _TEXT_CACHE[key] = arr
    return arr


def save_png(arr, path):
    """arr: top row first, RGBA float 0..1 display values (sRGB)."""
    h, w = arr.shape[:2]
    img = bpy.data.images.new("BoardOut", w, h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    a = np.ascontiguousarray(arr[::-1], dtype=np.float32)
    a[..., 3] = 1.0
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


def load_png(path):
    """An image file as RGBA float, top row first (display values)."""
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "sRGB"
    w, h = img.size
    a = np.zeros(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1].copy()

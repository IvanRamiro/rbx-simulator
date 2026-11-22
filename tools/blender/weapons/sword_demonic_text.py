"""Labels for the Demonic sword's review sheets (run inside Blender, headless): text drawn by a Workbench render of font
objects in a scene of its own, returned as a transparent RGBA array (top row first) to lay over a numpy sheet. Review images
only: nothing here ever reaches a game texture.
"""
import bpy
import numpy as np


def layer(w, h, items):
    """items: [(x, y, text, size_px, (r, g, b))], x and y in pixels from the sheet's top-left (the text's top-left corner).
    Returns an (h, w, 4) float array, straight alpha, top row first."""
    scene = bpy.data.scenes.new("SDText")
    objs = []
    try:
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x, scene.render.resolution_y = w, h
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        scene.display.shading.light = "FLAT"
        scene.display.shading.color_type = "OBJECT"
        scene.display.render_aa = "8"
        cam_data = bpy.data.cameras.new("SDTextCam")
        cam = bpy.data.objects.new("SDTextCam", cam_data)
        scene.collection.objects.link(cam)
        cam_data.type = "ORTHO"
        cam_data.sensor_fit = "HORIZONTAL"
        cam_data.ortho_scale = w / 100.0
        cam.location = (w / 200.0, -h / 200.0, 10.0)
        scene.camera = cam
        for x, y, text, size, col in items:
            cur = bpy.data.curves.new("SDT", "FONT")
            cur.body = text
            cur.size = size / 100.0 * 0.78
            cur.align_x, cur.align_y = "LEFT", "TOP"
            o = bpy.data.objects.new("SDT", cur)
            scene.collection.objects.link(o)
            o.location = (x / 100.0, -y / 100.0, 0.0)
            o.color = (*col, 1.0)
            objs.append(o)
        import tempfile
        import os
        path = os.path.join(tempfile.gettempdir(), "sd_text_%d.png" % os.getpid())
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=scene.name)
        img = bpy.data.images.load(path, check_existing=False)
        iw, ih = img.size
        px = np.zeros(iw * ih * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        os.remove(path)
        return px.reshape(ih, iw, 4)[::-1].copy()
    finally:
        for o in objs:
            c = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.curves.remove(c)
        bpy.data.scenes.remove(scene)


def over(base, text_layer):
    """Lays a label layer over a sheet (both (h, w, 4) float, display values)."""
    a = text_layer[..., 3:4]
    out = base.copy()
    out[..., :3] = text_layer[..., :3] * a + base[..., :3] * (1 - a)
    out[..., 3] = 1.0
    return out

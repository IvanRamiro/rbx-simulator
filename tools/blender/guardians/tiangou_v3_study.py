"""Tiangou v3, stage 1: the reference and silhouette study (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/tiangou_v3_study.py -- [out_folder]

Eight candidate bodies for the Moon-Eater, each built from the parts the real model uses (fused lobes for the body, head and ears, white fire
for the ruff and the plume, the eclipse behind the shoulders) and drawn as a black silhouette from the side, from three-quarters and from
the front. Judged for the myth first (would anyone call it just a dog? a heavenly hound that eats the moon needs a mass of fire and an
eclipse to read), then for the fight: it must read at 60 studs, load its haunches for a lunge, rear for a howl, and fit a court with its back
to three plinths.

Reference read before drawing (nothing copied; each is a fact about how such things are built):
  - Tiangou (Wikipedia and the pages it lists): a black dog or a meteor that eats the moon in an eclipse; the people drive it off with drums;
    in the Shan Hai Jing a white-headed fox-like spirit. Kept: a dog's body, the dark coat, white fire at the head; the eclipse is ours.
  - Dog gait (the Malinois study on HAL, the sled-dog gallop paper on arXiv, a review of epaxial muscles): the gallop is two suspension phases a
    stride with one dorsoventral bend of the spine (flexed with the feet gathered, extended at full reach); the hind feet land first in a rotary
    gallop (hind, hind, fore on the same side, fore).
  - Canine anatomy (veterinary pages on the hind limb and on digitigrade stance): the stifle in front, the hock behind, the pastern and toes
    flat on the ground; the elbow behind the shoulder, the carpus in front.
  - Quadruped rigging guides (Softimage's quadruped and tail pages, School of Motion): the spine runs along the body, the blades move on their
    own, a tail is a chain of springs that lags the body.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../eggs", "../world", "."):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, sub)))
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402
import guardian_kit as G  # noqa: E402
import tiangou_v2 as T  # noqa: E402
import tiangou_v3_model as Md  # noqa: E402

W = K.W
V = Vector

VARIANTS = {
    "A warden": {},
    "B mastiff": dict(cw=1.28, cd=1.15, neck=[(0, 12.0, -6.8), (0, 13.2, -9.0), (0, 14.2, -11.2), (0, 15.0, -13.4)], neck_r=(3.4, 2.7), head_at=(0, 15.0, -13.4), nose=(0, 13.2, -20.4), legs=0.86, front_r=1.2, back_r=1.15, ruff=0.8),
    "C sighthound": dict(cw=0.8, cd=0.86, neck_r=(2.2, 1.5), hs=0.82, legs=1.14, front_r=0.7, back_r=0.7, ruff=0.5, plume=0.6),
    "D hyena": dict(withers=1.5, croup=-1.3, neck=[(0, 13.6, -6.8), (0, 14.8, -9.2), (0, 15.2, -11.6), (0, 14.8, -13.8)], head_at=(0, 14.8, -13.8), nose=(0, 12.7, -21.2), neck_r=(3.2, 2.4), ruff=1.2),
    "E lion-hound": dict(cw=1.12, ruff=2.0, hs=1.1, neck_r=(3.3, 2.5), plume=1.3),
    "F prowler": dict(withers=1.3, croup=-0.6, neck=[(0, 12.9, -7.0), (0, 13.5, -9.4), (0, 13.8, -11.8), (0, 13.6, -14.2)], head_at=(0, 13.6, -14.2), nose=(0, 11.6, -21.6), legs=0.9, ruff=1.3),
    "G bear-hound": dict(cw=1.32, cd=1.12, withers=1.7, hs=1.18, neck=[(0, 12.9, -7.0), (0, 14.2, -8.6), (0, 15.2, -10.4), (0, 15.8, -12.4)], head_at=(0, 15.8, -12.4), nose=(0, 14.2, -19.2), neck_r=(3.5, 3.0)),
    "H spire": dict(neck=[(0, 12.9, -7.0), (0, 15.3, -8.6), (0, 18.0, -10.2), (0, 20.0, -12.0)], head_at=(0, 20.0, -12.0), nose=(0, 18.6, -19.2), neck_r=(2.6, 1.7), legs=1.05),
}


def variant(name, voxel=0.34):
    P = Md.default_params()
    P.update(VARIANTS[name])
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    mat = bpy.data.materials.get("StudyBlack") or bpy.data.materials.new("StudyBlack")
    lobes = Md.body_lobes(P)
    objs = [G.blob("body", coll, mat, lobes, voxel=voxel, smooth=0.5, rough=0.0, chisel="TG3Chisel"), G.blob("skull", coll, mat, Md.skull_lobes(P), voxel=0.2, smooth=0.5, rough=0.0, chisel="TG3Chisel"),
            G.blob("jaw", coll, mat, Md.jaw_lobes(P), voxel=0.2, smooth=0.5, rough=0.0, chisel="TG3Chisel")]
    f = Md.build_fire(P)
    objs.append(f.hi.object("fire", coll, [mat], weld=0))
    disc = Md.eclipse_disc().object("disc", coll, [mat], weld=0)
    outer, spans, core = Md.corona(P)
    objs += [disc, outer.object("corona", coll, [mat], weld=0), core.object("core", coll, [mat], weld=0)]
    for o in bpy.context.scene.objects:
        o.hide_render = o.name not in {x.name for x in coll.objects}
    return coll


def silhouette_scene(size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (0.0, 0.0, 0.0)
    sh.show_shadows = sh.show_cavity = sh.show_specular_highlight = False
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.86, 0.88, 0.92)
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    cam = bpy.data.objects.get("TG3Cam")
    if not cam:
        data = bpy.data.cameras.new("TG3Cam")
        data.lens = 70
        cam = bpy.data.objects.new("TG3Cam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    return scene, cam


def run(out_dir, names=None, size=300):
    scene, cam = silhouette_scene(size)
    tmp = os.path.join(out_dir, "_s.png")
    rows = []
    for name in names or VARIANTS:
        coll = variant(name)
        for o in bpy.context.scene.objects:
            o.hide_render = o.name not in {x.name for x in coll.objects}
        tiles = [T._shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in ((-90, 3, 92, (0, 14, -1)), (-38, 14, 92, (0, 14, -1)), (0, 4, 92, (0, 14, 0)))]
        rows.append(tiles)
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    flat = [t for r in rows[::-1] for t in r]
    T._sheet(flat, 3, os.path.join(out_dir, "study.png"), size)
    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[0] if argv else os.path.join(W.REPO, "renders", "tiangou_v3", "study")
    os.makedirs(out, exist_ok=True)
    only = argv[1].split(",") if len(argv) > 1 else None
    run(out, only)

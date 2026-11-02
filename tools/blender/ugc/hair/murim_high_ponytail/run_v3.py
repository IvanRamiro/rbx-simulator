"""The Murim High Ponytail (third design) pipeline (run inside Blender, with this folder and
tools/blender/ugc/hair on sys.path):

    import run_v3; run_v3.run("/path/to/roblox_ref")            # writes assets/ugc/Hair/MurimHighPonytail
    import run_v3; run_v3.run("/path/to/roblox_ref", out_dir)    # or anywhere else (a check run)

roblox_ref holds Roblox's reference downloads (BlockyCharacter.fbx, see hair_kit.reference). Steps:
the head; the locks, ornament and ribbon built as the game mesh and as the high-detail source
(v3_locks); one shared UV layout; each part baked from its own source only; the occlusion over
the whole game mesh into the colour map; the maps' empty texels filled; the rigid export with its
fit report.
"""
import os

import hair_kit as H
import v3_locks as L

K, B = H.K, H.B
ITEM = "MurimHighPonytail"
OUT = os.path.join(H.OUT_ROOT, ITEM)


def build(ref_dir):
    """The game mesh and the high-detail source. Returns (lows, his)."""
    tree = H.head_tree(H.reference(ref_dir))
    mats = L.materials()
    lows = L.build(tree, "low", mats) + L.build_details("low", mats)
    his = L.build(tree, "hi", mats) + L.build_details("hi", mats)
    return lows, his


def run(ref_dir, out_dir=None, size=1024, samples=32):   # fewer samples bake the shaders' occlusion as noise
    out_dir = out_dir or OUT
    lows, his = build(ref_dir)
    saved = K.OUT_DIR
    K.OUT_DIR = out_dir
    try:
        B.unwrap(lows, lining_names=())
        parts, pairs = H.split_pairs(lows, his)          # each part from its own source only
        B.bake(ITEM, pairs, size=size, small=size // 2, samples=samples, extrusion=0.1, ray=0.22)   # alone per part: rays may reach far
    finally:
        K.OUT_DIR = saved
    base = os.path.join(out_dir, ITEM)
    # soft contact shadow only: a deep floor ringed the mane in black where locks hover just over it
    occlusion = H.bake_occlusion(ITEM, parts, out_dir, size, distance=0.05)
    H.apply_occlusion(base + "_color.png", occlusion, floor=0.6)
    os.remove(occlusion)   # an intermediate: it lives in the colour map now
    H.fill_background(base + "_normal.png", (0.5, 0.5, 1.0))
    H.fill_background(base + "_roughness.png", (0.55, 0.55, 0.55))
    return H.export_rigid(ITEM, parts, out_dir)

"""The Murim High Ponytail pipeline (run inside Blender, with this folder and tools/blender/ugc/hair on
sys.path):

    import run; run.run("/path/to/roblox_ref")            # writes assets/ugc/Hair/MurimHighPonytail
    import run; run.run("/path/to/roblox_ref", out_dir)    # or anywhere else (a check run)

roblox_ref holds Roblox's reference downloads (BlockyCharacter.fbx, see hair_kit.reference). Steps:
the head; the hair built twice (high-detail and game mesh); unwrapped and baked into one texture
set; exported as one rigid mesh with its fit report. Uploading the maps and making the Accessory in
Studio are separate (see the vault note "Murim High Ponytail").
"""
import os

import hair_kit as H
import ponytail as P

K, B = H.K, H.B
OUT = os.path.join(H.OUT_ROOT, "MurimHighPonytail")


def build(ref_dir):
    """The two versions of the hair, in the MurimHighPonytail collection. Returns (lows, his)."""
    tree = H.head_tree(H.reference(ref_dir))
    root = K.collection(P.ITEM)
    lo = K.collection(P.ITEM + "_Low", root)
    hi = K.collection(P.ITEM + "_Hi", root)
    K.clear_collection(lo)
    K.clear_collection(hi)
    M = P.materials()
    return P.pieces("low", lo, M, tree), P.pieces("hi", hi, M, tree)


def run(ref_dir, out_dir=None, size=1024, samples=16):
    out_dir = out_dir or OUT
    lows, his = build(ref_dir)
    saved = K.OUT_DIR
    K.OUT_DIR = out_dir
    try:
        B.unwrap(lows, lining_names=("MHP_HairInside",))
        parts, pairs = H.split_pairs(lows, his)    # each clump from its own source only
        B.bake(P.ITEM, pairs, size=size, small=size // 2, samples=samples, extrusion=0.06, ray=0.14)
    finally:
        K.OUT_DIR = saved
    base = os.path.join(out_dir, P.ITEM)
    H.apply_occlusion(base + "_color.png", H.bake_occlusion(P.ITEM, parts, out_dir, size), floor=0.35)
    lows = parts
    H.fill_background(base + "_normal.png", (0.5, 0.5, 1.0))
    H.fill_background(base + "_roughness.png", (0.55, 0.55, 0.55))
    return H.export_rigid(P.ITEM, lows, out_dir)

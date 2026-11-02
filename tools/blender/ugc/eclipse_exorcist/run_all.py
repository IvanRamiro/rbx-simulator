"""The whole Eclipse Exorcist pipeline in one go (run inside Blender, with this folder on sys.path):

    import run_all; run_all.run("/path/to/roblox_ref")            # writes assets/ugc/EclipseExorcist
    import run_all; run_all.run("/path/to/roblox_ref", out_dir)    # or anywhere else (a check run)

roblox_ref holds Roblox's reference downloads (see ee_export.setup_reference). Steps: the reference;
each item built twice (high-detail and game mesh) with the robe's printed motifs; each item unwrapped
and baked; the robe and hakama exported as layered clothing on the blocky body, the seal cord as
layered clothing worn over the robe. Returns the export reports. Uploading the maps and setting the
accessories up in Studio are separate (see the vault's Worked Builds note).
"""
import ee_bake as B
import ee_export as X
import ee_kit as K
import ee_pants as Pn
import ee_robe as R
import ee_waist as Wt


def run(ref_dir, out_dir=None):
    saved = K.OUT_DIR
    if out_dir:
        K.OUT_DIR = out_dir
    try:
        return _run(ref_dir)
    finally:
        K.OUT_DIR = saved


def _run(ref_dir):
    report = {"reference": X.setup_reference(ref_dir)}
    root = K.collection("EclipseExorcist")
    built = {}
    for key, mod, lining in (("EE_Robe", R, ("EE_CrimsonLining",)), ("EE_Hakama", Pn, ("EE_HakamaInside",)), ("EE_SealCord", Wt, ())):
        lo = K.collection(key + "_Low", root)
        hi = K.collection(key + "_Hi", root)
        K.clear_collection(lo)
        K.clear_collection(hi)
        M = mod.materials()
        lows = mod.pieces("low", lo, M)
        his = mod.pieces("hi", hi, M)
        decals = mod.decals(his, hi)[0] if mod is R else []
        B.unwrap(lows, lining_names=lining)
        size, small, ext, ray = ((2048, 1024, 0.06, 0.16) if mod is R else (1024, 512, 0.05, 0.12) if mod is Pn else (1024, 512, 0.03, 0.08))
        B.bake(key, B.pairs_by_name(lows, his, decals), size=size, small=small, samples=10, extrusion=ext, ray=ray)
        built[key] = lows
    exp = K.collection("EE_Export", root)

    def copies(objs):
        out = []
        for o in objs:
            c = o.copy()
            c.data = o.data.copy()
            exp.objects.link(c)
            out.append(c)
        return out
    report["EE_Robe"] = X.layered("EE_Robe", copies(built["EE_Robe"]), X.robe_weights, "Blocky_BodyFront_Att", "BodyFront_Att")
    report["EE_Hakama"] = X.layered("EE_Hakama", copies(built["EE_Hakama"]), X.pants_weights, "Blocky_WaistCenter_Att", "WaistCenter_Att")
    report["EE_SealCord"] = X.layered("EE_SealCord", copies(built["EE_SealCord"]), X.seal_weights, "Blocky_WaistCenter_Att",
                                      "WaistCenter_Att", inner_source="EE_Robe_OuterCage")
    return report

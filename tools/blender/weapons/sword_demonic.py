"""The Demonic faction's secret weapon (run inside Blender, headless): id SecretDemonic, a sword.

    blender -b --factory-startup --python tools/blender/weapons/sword_demonic.py -- clay|export|review|all

Design in one paragraph. A massive one-edged blade built like a forward-weighted chopper: a drawn-in neck swelling to a broad head, the
back scooped into a cove behind the point and ground to a second edge, the point a hooked talon; shinogi-zukuri section (ridge, plane,
face), a square-ended fuller engraved with smoke lines, blackened and blued steel, a mirror-polished edge bevel and a hard temper line
of leaning flame tongues. A thick crescent slab guard of dark iron that sweeps forward and cradles the blade's bronze collar, with
engraved bronze face plates, a keel down each face and bronze caps on its ends. A ray-skin grip bound in blood-red cord in the diamond
wrap, a bronze collar and cap, a heavy flat-sided iron ring pommel (the Korean ring-pommel idea) engraved with one flowing line, and a
short ragged red cord. No glow piece: the geometry and the metal carry it.

Files (all in tools/blender/weapons/): this script; sword_demonic_profile.py (the blade's outline numbers, shared with the study),
_blade, _guard, _grip, _kit (parametric mesh tools), _mat (the shaders), _low (the game mesh and its UVs), _lab and _review (the review
renders), _text (labels), _study (the research board and the silhouette study). Run the study with
`-- research|silhouettes` and the rest with `-- clay|export|review`. The weapon's authored convention is the realm weapons': studs from the
grip, the point toward -Z, flats +-Y, edges +-X; the blade bows toward +X with the back on the inside.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402
import sword_demonic_blade as BL  # noqa: E402
import sword_demonic_grip as GR  # noqa: E402
import sword_demonic_guard as GD  # noqa: E402
import sword_demonic_kit as KT  # noqa: E402
import sword_demonic_profile as P  # noqa: E402

V = Vector
WK, W = SK.WK, SK.W
WEAPON_ID = "SecretDemonic"


def real_mats():
    import sword_demonic_mat as MT
    return {"steel": MT.mat_blade(), "iron": MT.mat_iron(), "bronze": MT.mat_bronze(), "skin": MT.mat_skin(), "silk": MT.mat_silk(),
            "cord": MT.mat_cord(), "ring": MT.mat_iron("SdRingIron", line_col=(176, 128, 70))}


def build_hi(coll, mats):
    """The high-detail source: a list of objects, one per material family."""
    import egg_hi as Hm
    objs = []

    def piece(name, fn, mat, **props):
        m = KT.Mesh()
        fn(m)
        o = m.object(name, coll, [mat])
        for k, v in props.items():
            o[k] = v
        objs.append(o)
        return o

    def blade(m):
        BL.blade(m, "hi")
        BL.bohi_patch(m, 1.0)
        BL.bohi_patch(m, -1.0)
    piece("DS_Blade", blade, mats["steel"])
    piece("DS_GuardIron", lambda m: GD.core(m, "hi"), mats["iron"])
    piece("DS_GuardBronze", lambda m: (GD.plates(m, "hi"), GD.habaki(m, "hi")), mats["bronze"])
    piece("DS_GripCore", lambda m: GR.grip_core(m, "hi"), mats["skin"])
    piece("DS_GripWrap", lambda m: GR.wrap(m, "hi"), mats["silk"])
    piece("DS_Fittings", lambda m: (GR.fuchi(m, "hi"), GR.kashira(m, "hi")), mats["bronze"])
    piece("DS_Ring", lambda m: (GR.ring(m, "hi"), GR.ring_stem(m, "hi")), mats["ring"])
    cord = Hm.Hi()
    GR.cord_parts(cord)
    objs.append(cord.object("DS_Cord", coll, [mats["cord"]], smooth=True))
    return objs


def clay_mats():
    from secret_lab import clay_material
    c = clay_material()
    return {k: c for k in ("steel", "iron", "bronze", "skin", "silk", "cord", "ring")}


def build(clay_only=False):
    SK.fresh()
    root = W.collection("SecretDemonicHi")
    W.clear_collection(root)
    mats = clay_mats() if clay_only else real_mats()
    objs = build_hi(root, mats)
    return objs, {}, root


OUT_DIR = SK.OUT_DIR
PLACEMENTS_DIR = SK.PLACEMENTS_DIR


def hilt_tip():
    x, z = P.tip_xz()
    return (0.0, 0.0, P.Z0), (x, 0.0, z)


def write_placements(low, hilt, tip):
    import egg_kit as K
    pts = [V(K.rb_inv(*(low.matrix_world @ v.co))) for v in low.data.vertices]
    lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
    hi_ = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
    c = (lo + hi_) / 2
    lines = ["-- Built by tools/blender/weapons/sword_demonic.py. Do not edit by hand.",
             "-- %s's pieces: centres as authored, in studs from the grip (where the hand holds it), its point" % WEAPON_ID,
             "-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.",
             "return {",
             '    Kind = "Sword",',
             "    Hilt = Vector3.new(%.3f, %.3f, %.3f), -- where the blade starts" % hilt,
             "    Tip = Vector3.new(%.3f, %.3f, %.3f)," % tip,
             "    Pieces = {",
             "        Body = { Centre = Vector3.new(%.4f, %.4f, %.4f) }," % (c.x, c.y, c.z),
             "    },", "}", ""]
    os.makedirs(PLACEMENTS_DIR, exist_ok=True)
    with open(os.path.join(PLACEMENTS_DIR, WEAPON_ID + ".lua"), "w") as f:
        f.write("\n".join(lines))
    return [round(x, 3) for x in c], [round(x, 3) for x in (hi_ - lo)]


def make_game(hi_objs, root, size=1024, small=512, normal_size=None):
    """Builds the game mesh, unwraps it, bakes the four maps from the high-detail source and writes the FBX and placements."""
    import sword_demonic_low as LOW
    from secret_lab import clay_material
    dummy = clay_material("SD_Dummy")
    low_objs = LOW.build_low(root, dummy)
    counts = LOW.tri_counts(low_objs)
    low = LOW.join_low(low_objs, WEAPON_ID + "_Body", root)
    for o in low_objs:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(me)
    k = LOW.unwrap_low(low)
    dens = LOW.density(low)
    tris = sum(len(p.vertices) - 2 for p in low.data.polygons)
    SK.B.EGG_DIR = OUT_DIR
    os.makedirs(OUT_DIR, exist_ok=True)
    SK.bake(WEAPON_ID, hi_objs, low, size=size, small=small)
    SK.B.export(WEAPON_ID, low, {}, root)
    SK.scrub_paths(os.path.join(OUT_DIR, WEAPON_ID + ".fbx"))
    hilt, tip = hilt_tip()
    centre, dims = write_placements(low, hilt, tip)
    return low, dict(pieces=counts, tris=tris, density=dens, centre=centre, size=dims)


CLOSE = (("front34", (0.0, 0.0, -1.2), 3.2), ("top", (0.0, 0.0, -1.2), 3.2), ("front34", (0.0, 0.0, 0.9), 2.8), ("edge_r", (0.0, 0.0, -1.0), 3.2))


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["export"])[0] if "--" in sys.argv else "export"
    if stage in ("clay",):
        import sword_demonic_review as RV
        objs, glow, root = build(clay_only=True)
        RV.clay(objs)
    if stage in ("export", "all"):
        import time
        t0 = time.time()
        objs, glow, root = build()
        low, info = make_game(objs, root)
        print("EXPORT", info, "in", round(time.time() - t0, 1), "s")
    if stage in ("review", "all"):
        import sword_demonic_review as RV
        RV.run("all")

-- Built by tools/blender/weapons/secret_unorthodox.py. Do not edit by hand.
-- SecretUnorthodox's pieces: centres as authored, in studs from the grip (where the hand holds it), its point
-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.
return {
    Kind = "Spear",
    Hilt = Vector3.new(0.000, 0.000, -4.120), -- where the head starts
    Tip = Vector3.new(0.384, 0.000, -6.740),
    Pieces = {
        Body = { Centre = Vector3.new(0.0822, -0.2809, -1.4266) },
        Glow = { Centre = Vector3.new(0.2342, 0.0000, -5.3641), Hex = "ff7418" },
    },
}

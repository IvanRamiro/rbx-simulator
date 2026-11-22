-- Built by tools/blender/weapons/secret_demonic.py. Do not edit by hand.
-- SecretDemonic's pieces: centres as authored, in studs from the grip (where the hand holds it), its point
-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.
return {
    Kind = "Sword",
    Hilt = Vector3.new(0.000, 0.000, -2.192), -- where the blade starts
    Tip = Vector3.new(0.561, 0.000, -5.453),
    Pieces = {
        Body = { Centre = Vector3.new(-0.0001, -0.3326, -1.7097) },
        Glow = { Centre = Vector3.new(0.2704, 0.0000, -2.9191), Hex = "ff4010" },
    },
}

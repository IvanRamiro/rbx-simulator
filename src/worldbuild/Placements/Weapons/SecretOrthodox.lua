-- Built by tools/blender/weapons/sword_orthodox.py. Do not edit by hand.
-- SecretOrthodox's pieces: centres as authored, in studs from the grip (where the hand holds it), its point
-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.
return {
    Kind = "Sword",
    Hilt = Vector3.new(0.000, 0.000, -1.720), -- where the blade starts
    Tip = Vector3.new(0.000, 0.000, -5.750),
    Pieces = {
        Body = { Centre = Vector3.new(0.0000, 0.0000, -1.0400) },
    },
}

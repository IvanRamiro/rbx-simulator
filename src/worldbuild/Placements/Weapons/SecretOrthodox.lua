-- Built by tools/blender/weapons/secret_orthodox.py. Do not edit by hand.
-- SecretOrthodox's pieces: centres as authored, in studs from the grip (where the hand holds it), its point
-- toward -Z. Glow pieces are found by colour (Hex). Read by OutfitBuilder.storeWeapon.
return {
    Kind = "Sword",
    Hilt = Vector3.new(0.000, 0.000, -1.100), -- where the blade starts
    Tip = Vector3.new(0.000, 0.000, -5.100),
    Pieces = {
        Body = { Centre = Vector3.new(0.0001, -0.7464, -1.7733) },
        Glow = { Centre = Vector3.new(0.0000, 0.0000, -2.7434), Hex = "1e8cff" },
    },
}

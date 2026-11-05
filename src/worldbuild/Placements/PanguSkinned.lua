-- Pangu the World-Splitter with a skeleton (tools/blender/guardians/pangu_v2.py, assets/guardians/PanguV2.fbx). Used by
-- GuardianBuilder.storeSkinned. The glow pieces: the void in his cracks and on his axe's edge, his eyes, and their dark pupils.
return {
    Rig = "PanguSkinned",
    Fit = {
        Hips = Vector3.new(0, 18.2, 0.2),
        Head = Vector3.new(0, 33.2, -0.6),
        LeftThigh = Vector3.new(-4.2, 17.4, 0.2),
        RightShin = Vector3.new(4.5, 9.6, -0.5),
    },
    -- The importer drops a bone that only single-bone pieces use (a hundredth of a vertex on a second bone doesn't save it). These
    -- are put back on the same bind, from Blender's rest pose. The import is a half turn about Y: a bone-local value is Blender's
    -- with X and Z flipped, in position and rotation alike (checked against the bones that survive, off the centre line too).
    AddBones = {
        Axe = { Parent = "RightHand", CFrame = CFrame.new(0.0608, 1.91996, -0.00703, 0.488049, 0.742959, 0.458061, -0.742959, 0.078206, 0.664752, 0.458061, -0.664752, 0.590156) },
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 2.21622, 1.61271, 1, 0, 0, 0, 0.039968, -0.999201, 0, 0.999201, 0.039968) },
    },
    Glow = {
        BodyVoid = Color3.fromRGB(140, 40, 255),
        AxeVoid = Color3.fromRGB(140, 40, 255),
        Eyes = Color3.fromRGB(154, 100, 255),
        Pupils = Color3.fromRGB(6, 2, 12),
    },
}

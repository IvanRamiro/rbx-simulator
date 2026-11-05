-- Tiangou the Moon-Eater with a skeleton (tools/blender/guardians/tiangou_v2.py, assets/guardians/TiangouV2.fbx). Used by
-- GuardianBuilder.storeSkinned. The glow pieces ride their bones whole: the black disc and the pupils are dark Neon.
return {
    Rig = "TiangouSkinned",
    Fit = {
        Hips = Vector3.new(0, 15.0, 8.6),
        Head = Vector3.new(0, 21.2, -13.6),
        LeftBackUpper = Vector3.new(-2.6, 14.1, 9.0),
    },
    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, measured in Blender
    -- (the same in the guardian's axes except that Z flips, as a surviving bone proves: Neck2 to Head).
    AddBones = {
        Jaw = { Parent = "Head", CFrame = CFrame.new(0, 1.80922, 0.35599, 1, 0, 0, 0, 0.999779, -0.021036, 0, 0.021036, 0.999779) },
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 2.86622, -1.42031, 1, 0, 0, 0, 0.999703, 0.024383, 0, -0.024383, 0.999703) },
    },
    Glow = {
        Eclipse = Color3.fromRGB(5, 7, 12),
        Corona = Color3.fromRGB(220, 239, 255),
        Eyes = Color3.fromRGB(255, 154, 0),
        Pupils = Color3.fromRGB(10, 4, 0),
    },
}

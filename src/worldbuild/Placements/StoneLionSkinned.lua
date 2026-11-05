-- The Awakened Stone Lion with a skeleton (tools/blender/guardians/stone_lion_v2.py writes this file, assets/guardians/StoneLionV2.fbx). Used by
-- GuardianBuilder.storeSkinned. The importer drops a bone that only single-bone pieces use: these go back on the same bind.
return {
    Rig = "StoneLionSkinned",
    Fit = {
        Hips = Vector3.new(0, 16.9, 14.5),
        Head = Vector3.new(0, 22.4, -14),
        BackLeftThigh = Vector3.new(-4.6, 15.4, 13.2),
        FrontRightLower = Vector3.new(5.2, 8.2, -4),
    },
    AddBones = {
        Jaw = { Parent = "Head", CFrame = CFrame.new(0, 2.08986, 1.92677, 1, 0, 0, 0, 0.995242, -0.0974317, 0, 0.0974317, 0.995242) },
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 5.16409, -1.335, 1, 0, 0, 0, 0.990181, 0.13979, 0, -0.13979, 0.990181) },
    },
    Glow = {
        Eyes = Color3.fromRGB(0, 110, 255),
        Pupils = Color3.fromRGB(6, 16, 28),
        Orb = Color3.fromRGB(0, 160, 95),
    },
}

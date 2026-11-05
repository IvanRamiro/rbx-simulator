-- The Bamboo Mantis Sage with a skeleton (tools/blender/guardians/mantis_sage_v2.py writes this file, assets/guardians/MantisSageV2.fbx). Used by
-- GuardianBuilder.storeSkinned.
return {
    Rig = "MantisSageSkinned",
    Fit = {
        Hips = Vector3.new(0, 13.3, 3.2),
        Head = Vector3.new(0, 26.4, -6.5),
        HindLeftFemur = Vector3.new(-2, 12.3, 5.6),
        MidRightTibia = Vector3.new(9.5, 16.2, -1.6),
    },
    Glow = {
        Pupils = Color3.fromRGB(255, 144, 0),
        LeftEdge = Color3.fromRGB(0, 200, 110),
        RightEdge = Color3.fromRGB(0, 200, 110),
    },
}

-- Tiangou the Moon-Eater, rebuilt, with a skeleton (tools/blender/guardians/tiangou_v3.py, assets/guardians/TiangouV3.fbx).
-- Used by GuardianBuilder.storeSkinned for the guardian Tiangou once it is wired (the live Tiangou keeps Placements/TiangouSkinned.lua until then).
return {
    Rig = "TiangouV3Skinned",
    Fit = {
        Hips = Vector3.new(0, 12, 5.6),
        Head = Vector3.new(0, 16.5, -14),
        BackLeftThigh = Vector3.new(-2.55, 11.6, 4.6),
        FrontRightLower = Vector3.new(2.6, 7, -7),
    },
    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, from Blender's rest pose. The
    -- import is a half turn about Y: a bone-local value is Blender's with X and Z flipped, in position and rotation alike.
    AddBones = {
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 3.21631, -1.25515, 1, 0, 0, 0, 0.98058, 0.19612, 0, -0.19612, 0.98058) },
    },
    Glow = {
        Eclipse = Color3.fromRGB(5, 7, 12),
        Corona = Color3.fromRGB(220, 239, 255),
        CoronaCore = Color3.fromRGB(255, 233, 168),
        Eyes = Color3.fromRGB(255, 178, 30),
        Pupils = Color3.fromRGB(10, 4, 8),
    },
}

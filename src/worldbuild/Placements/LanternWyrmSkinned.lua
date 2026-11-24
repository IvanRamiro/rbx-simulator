-- The Abyssal Lantern Wyrm, the Origin Abyss's guardian, with a skeleton (tools/blender/guardians/lantern_wyrm.py, assets/guardians/LanternWyrm.fbx).
-- Used by GuardianBuilder.storeSkinned for the guardian Pangu (the id stays: saves, records and quests key off it).
return {
    Rig = "LanternWyrmSkinned",
    Fit = {
        Hips = Vector3.new(0, 2.6, 0),
        Head = Vector3.new(0, 2.6, -22),
        Tail6 = Vector3.new(0, 2.6, 33.1),
        RightFrill5 = Vector3.new(1.2433, 4.1914, -9.4),
    },
    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, from Blender's rest pose. The
    -- import is a half turn about Y: a bone-local value is Blender's with X and Z flipped, in position and rotation alike.
    AddBones = {
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 3.5, -0.4, 1, 0, 0, 0, 1, 0, 0, 0, 1) },
    },
    Glow = {
        Lantern = Color3.fromRGB(255, 178, 26),
        Eyes = Color3.fromRGB(255, 223, 128),
        RingsA = Color3.fromRGB(58, 214, 255),
        RingsB = Color3.fromRGB(58, 214, 255),
        RingsC = Color3.fromRGB(58, 214, 255),
        RingsD = Color3.fromRGB(58, 214, 255),
    },
}

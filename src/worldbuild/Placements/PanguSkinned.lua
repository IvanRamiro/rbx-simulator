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
    -- The importer drops a bone that no multi-bone piece weights: here Eyes, and the Head bone itself (the importer let the Head piece take its place and hung the jaw,
    -- the lure and the barbels on the piece, where they would not follow the neck). They are put back on the same bind, from Blender's rest pose
    -- (parent.matrix_local.inverted() @ bone.matrix_local, turned a half turn about Y: X and Z flipped, in position and rotation alike; checked against the bones that
    -- survive: Neck8 and LeftFrill1 match to six places). Adopt gives each hanging bone its place under the new Head. GuardianBuilder.storeSkinned reads this.
    AddBones = {
        Head = {
            Parent = "Neck8",
            CFrame = CFrame.new(0, 2.75, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1),
            Adopt = {
                Jaw = CFrame.new(0, 2.299999, 0.6, 1, 0, 0, 0, 0.998793, -0.049121, 0, 0.049121, 0.998793),
                Lure1 = CFrame.new(0, 3, -1.4, 1, 0, 0, 0, 0.152057, 0.988372, 0, -0.988372, 0.152057),
                LeftBarbelA1 = CFrame.new(0.55, 7, 0.25, -0.516722, 0.85361, -0.065945, -0.85361, -0.519589, -0.037114, -0.065945, 0.037114, 0.997133),
                LeftBarbelB1 = CFrame.new(0.55, 7.4, 0.9, 0.733334, 0.133333, -0.666666, -0.133333, -0.933333, -0.333333, -0.666666, 0.333333, -0.666666),
                RightBarbelA1 = CFrame.new(-0.55, 7, 0.25, -0.516722, -0.85361, 0.065944, 0.85361, -0.519589, -0.037113, 0.065944, 0.037113, 0.997133),
                RightBarbelB1 = CFrame.new(-0.55, 7.4, 0.9, 0.733333, -0.133333, 0.666666, 0.133333, -0.933333, -0.333333, 0.666666, 0.333333, -0.666666),
            },
        },
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

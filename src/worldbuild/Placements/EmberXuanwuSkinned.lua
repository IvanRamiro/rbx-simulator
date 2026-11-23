-- The Cinder Roc, Ember Peak's guardian, with a skeleton (tools/blender/guardians/cinder_roc.py, assets/guardians/CinderRoc.fbx). Used by
-- GuardianBuilder.storeSkinned for the guardian EmberXuanwu (the id stays: saves, records and quests key off it).
return {
    Rig = "CinderRocSkinned",
    Fit = {
        Hips = Vector3.new(0, 12.1, 2.6),
        Head = Vector3.new(0, 19.7, -8.6),
        LeftThigh = Vector3.new(-3.4, 11.5, 0.8),
        RightShin = Vector3.new(3.4, 8.4, -2.4),
    },
    -- The importer drops a bone that only single-bone pieces use. These are put back on the same bind, from Blender's rest pose. The
    -- import is a half turn about Y: a bone-local value is Blender's with X and Z flipped, in position and rotation alike.
    AddBones = {
        Eyes = { Parent = "Head", CFrame = CFrame.new(0, 1.84877, -0.91217, 1, 0, 0, 0, 0.97732, 0.21175, 0, -0.21175, 0.97732) },
    },
    Glow = {
        Magma = Color3.fromRGB(255, 122, 20),
        Eyes = Color3.fromRGB(255, 164, 42),
        Pupils = Color3.fromRGB(10, 3, 0),
    },
}

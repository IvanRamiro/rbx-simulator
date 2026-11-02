-- Origin Abyss's guardian, Pangu the World-Splitter (tools/blender/guardians/pangu.py): his
-- pieces' centres as authored, in studs from his origin, the ground between his feet (front toward
-- -Z, his left toward -X). Each piece rides a segment, which turns about its pivot. Glow pieces are
-- found by segment and colour: the void in his cracks (one per segment), his eyes and their dark Neon
-- pupils. Used by GuardianBuilder.store.
return {
    Pieces = {
        Body = { Segment = "Body", Centre = Vector3.new(-0.0042, 14.8778, 0.0500) },
        BodyVoid = { Segment = "Body", Centre = Vector3.new(-0.3275, 18.5696, 0.2318), Hex = "8c28ff" },
        Chest = { Segment = "Chest", Centre = Vector3.new(-0.0771, 26.3314, 3.0507) },
        ChestVoid = { Segment = "Chest", Centre = Vector3.new(-0.0145, 26.3446, 0.2533), Hex = "8c28ff" },
        Head = { Segment = "Head", Centre = Vector3.new(0.0000, 36.0116, 1.1033) },
        HeadVoid = { Segment = "Head", Centre = Vector3.new(0.0445, 35.5222, -2.6360), Hex = "8c28ff" },
        Eyes = { Segment = "Head", Centre = Vector3.new(0.0021, 35.3633, -2.7067), Hex = "9a64ff" },
        Pupils = { Segment = "Head", Centre = Vector3.new(0.0021, 35.3662, -2.8258), Hex = "06020c" },
        LeftUpperArm = { Segment = "LeftUpperArm", Centre = Vector3.new(-7.4224, 28.0807, 0.3546) },
        LeftUpperArmVoid = { Segment = "LeftUpperArm", Centre = Vector3.new(-7.7925, 26.7030, 0.7854), Hex = "8c28ff" },
        LeftForearm = { Segment = "LeftForearm", Centre = Vector3.new(-6.9280, 24.0426, -3.0455) },
        LeftForearmVoid = { Segment = "LeftForearm", Centre = Vector3.new(-7.4600, 23.2514, -1.7146), Hex = "8c28ff" },
        RightUpperArm = { Segment = "RightUpperArm", Centre = Vector3.new(7.5245, 28.0714, 0.3000) },
        RightUpperArmVoid = { Segment = "RightUpperArm", Centre = Vector3.new(8.3159, 26.7094, 0.2146), Hex = "8c28ff" },
        RightForearm = { Segment = "RightForearm", Centre = Vector3.new(8.2237, 32.1093, -1.4337) },
        RightForearmVoid = { Segment = "RightForearm", Centre = Vector3.new(7.9344, 32.3761, -0.2662), Hex = "8c28ff" },
        LeftThigh = { Segment = "LeftThigh", Centre = Vector3.new(-3.2067, 14.2874, 0.0381) },
        LeftThighVoid = { Segment = "LeftThigh", Centre = Vector3.new(-4.1590, 14.6853, 0.0119), Hex = "8c28ff" },
        LeftShin = { Segment = "LeftShin", Centre = Vector3.new(-3.5575, 5.6492, -0.5556) },
        LeftShinVoid = { Segment = "LeftShin", Centre = Vector3.new(-3.9210, 6.9005, 0.9805), Hex = "8c28ff" },
        RightThigh = { Segment = "RightThigh", Centre = Vector3.new(3.2065, 14.2899, 0.0326) },
        RightThighVoid = { Segment = "RightThigh", Centre = Vector3.new(3.3263, 11.4686, -0.6213), Hex = "8c28ff" },
        RightShin = { Segment = "RightShin", Centre = Vector3.new(3.5577, 5.6563, -0.5486) },
        RightShinVoid = { Segment = "RightShin", Centre = Vector3.new(4.6343, 3.4558, 0.1112), Hex = "8c28ff" },
    },
    -- Parent nil: hangs from the root
    Pivots = {
        Body = { Position = Vector3.new(0.0, 18.0, 0.0) },
        Chest = { Parent = "Body", Position = Vector3.new(0.0, 21.1, 0.2) },
        Head = { Parent = "Chest", Position = Vector3.new(0.0, 32.7, -0.2) },
        LeftUpperArm = { Parent = "Chest", Position = Vector3.new(-7.0, 30.9, 0.2) },
        LeftForearm = { Parent = "LeftUpperArm", Position = Vector3.new(-8.6, 24.1, 1.2) },
        RightUpperArm = { Parent = "Chest", Position = Vector3.new(7.0, 30.9, 0.2) },
        RightForearm = { Parent = "RightUpperArm", Position = Vector3.new(8.8, 24.1, 1.0) },
        LeftThigh = { Parent = "Body", Position = Vector3.new(-3.2, 17.7, 0.2) },
        LeftShin = { Parent = "LeftThigh", Position = Vector3.new(-3.5, 9.4, -0.5) },
        RightThigh = { Parent = "Body", Position = Vector3.new(3.2, 17.7, 0.2) },
        RightShin = { Parent = "RightThigh", Position = Vector3.new(3.5, 9.4, -0.5) },
    },
    Glow = {
        BodyVoid = { Color = Color3.fromRGB(140, 40, 255) },
        ChestVoid = { Color = Color3.fromRGB(140, 40, 255) },
        HeadVoid = { Color = Color3.fromRGB(140, 40, 255) },
        Eyes = { Color = Color3.fromRGB(154, 100, 255) },
        Pupils = { Color = Color3.fromRGB(6, 2, 12) },
        LeftUpperArmVoid = { Color = Color3.fromRGB(140, 40, 255) },
        LeftForearmVoid = { Color = Color3.fromRGB(140, 40, 255) },
        RightUpperArmVoid = { Color = Color3.fromRGB(140, 40, 255) },
        RightForearmVoid = { Color = Color3.fromRGB(140, 40, 255) },
        LeftThighVoid = { Color = Color3.fromRGB(140, 40, 255) },
        LeftShinVoid = { Color = Color3.fromRGB(140, 40, 255) },
        RightThighVoid = { Color = Color3.fromRGB(140, 40, 255) },
        RightShinVoid = { Color = Color3.fromRGB(140, 40, 255) },
    },
    -- The bronze (belt, bands, horn rings) is metal; the chest and thighs have none (Metalness "").
    Maps = (function()
        local ids = {
            Body = { "rbxassetid://130647440025129", "rbxassetid://78319530336980", "rbxassetid://89061546820070", "rbxassetid://124868164647193" },
            Chest = { "rbxassetid://83776567062937", "rbxassetid://79427803196913", "rbxassetid://106023855819648" },
            Head = { "rbxassetid://90662778163418", "rbxassetid://106475688212746", "rbxassetid://125092936833957", "rbxassetid://74881339838114" },
            LeftUpperArm = { "rbxassetid://79572728180174", "rbxassetid://97125508980609", "rbxassetid://87588586328974", "rbxassetid://113475613245901" },
            LeftForearm = { "rbxassetid://119863023334822", "rbxassetid://108673679809817", "rbxassetid://87081842842503", "rbxassetid://104845739883559" },
            RightUpperArm = { "rbxassetid://132168005545947", "rbxassetid://95283078633948", "rbxassetid://130476204926752", "rbxassetid://123283175835624" },
            RightForearm = { "rbxassetid://108117645649644", "rbxassetid://101177504182690", "rbxassetid://103437300840563", "rbxassetid://89563441649685" },
            LeftThigh = { "rbxassetid://78194611987385", "rbxassetid://79442093921501", "rbxassetid://78325934708357" },
            LeftShin = { "rbxassetid://134769061566948", "rbxassetid://81671187284671", "rbxassetid://135437584072059", "rbxassetid://132058193040835" },
            RightThigh = { "rbxassetid://132851911452344", "rbxassetid://93884716375577", "rbxassetid://85086425037533" },
            RightShin = { "rbxassetid://137178724898748", "rbxassetid://119659179301491", "rbxassetid://107771838538139", "rbxassetid://107148474837162" },
        }
        local maps = {}
        for piece, m in ids do
            maps[piece] = { Color = m[1], Normal = m[2], Roughness = m[3], Metalness = m[4] or "" }
        end
        return maps
    end)(),
}

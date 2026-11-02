-- Moonlit Isle's guardian, Tiangou the Moon-Eater (tools/blender/guardians/tiangou.py): its pieces'
-- centres as authored, in studs from its origin, the ground under its body (front toward -Z, its
-- left toward -X). Each piece rides a segment, which turns about its pivot. Glow pieces are found by
-- segment and colour: the eclipse's black disc and the pupils are dark Neon (it renders flat black),
-- the corona white fire. Used by GuardianBuilder.store.
return {
    Pieces = {
        Body = { Segment = "Body", Centre = Vector3.new(0.0000, 18.0830, 0.3452) },
        Eclipse = { Segment = "Body", Centre = Vector3.new(0.0000, 27.5000, -3.5000), Hex = "05070c" },
        Corona = { Segment = "Body", Centre = Vector3.new(-0.8422, 29.2726, -3.2761), Hex = "dcefff" },
        Neck = { Segment = "Neck", Centre = Vector3.new(0.1767, 16.5239, -9.1050) },
        Head = { Segment = "Head", Centre = Vector3.new(0.0000, 24.3750, -17.4474) },
        Eyes = { Segment = "Head", Centre = Vector3.new(-0.0014, 22.9853, -17.5453), Hex = "ff9a00" },
        Pupils = { Segment = "Head", Centre = Vector3.new(-0.0014, 23.0111, -17.6522), Hex = "0a0400" },
        Jaw = { Segment = "Jaw", Centre = Vector3.new(0.0017, 20.6918, -18.9694) },
        Tail = { Segment = "Tail", Centre = Vector3.new(0.2822, 20.1014, 15.5441) },
        TailTip = { Segment = "TailTip", Centre = Vector3.new(0.0847, 24.5639, 20.1200) },
        FrontLeftUpper = { Segment = "FrontLeftUpper", Centre = Vector3.new(-2.9991, 11.9654, -6.1998) },
        FrontLeftLower = { Segment = "FrontLeftLower", Centre = Vector3.new(-3.2032, 4.8593, -6.5636) },
        FrontRightUpper = { Segment = "FrontRightUpper", Centre = Vector3.new(2.9997, 11.9671, -6.2008) },
        FrontRightLower = { Segment = "FrontRightLower", Centre = Vector3.new(3.2037, 4.8598, -6.5636) },
        BackLeftUpper = { Segment = "BackLeftUpper", Centre = Vector3.new(-3.0001, 12.0984, 7.8196) },
        BackLeftLower = { Segment = "BackLeftLower", Centre = Vector3.new(-3.3551, 4.8611, 8.6450) },
        BackRightUpper = { Segment = "BackRightUpper", Centre = Vector3.new(3.0018, 12.0973, 7.8166) },
        BackRightLower = { Segment = "BackRightLower", Centre = Vector3.new(3.3572, 4.8596, 8.6436) },
    },
    -- Parent nil: hangs from the root
    Pivots = {
        Body = { Position = Vector3.new(0.0, 14.0, 1.0) },
        Neck = { Parent = "Body", Position = Vector3.new(0.0, 16.5, -8.4) },
        Head = { Parent = "Neck", Position = Vector3.new(0.0, 21.2, -13.8) },
        Jaw = { Parent = "Head", Position = Vector3.new(0.0, 21.3, -16.8) },
        Tail = { Parent = "Body", Position = Vector3.new(0.0, 15.6, 10.6) },
        TailTip = { Parent = "Tail", Position = Vector3.new(0.0, 20.5, 17.5) },
        FrontLeftUpper = { Parent = "Body", Position = Vector3.new(-3.0, 13.5, -6.5) },
        FrontLeftLower = { Parent = "FrontLeftUpper", Position = Vector3.new(-3.2, 8.5, -6.0) },
        FrontRightUpper = { Parent = "Body", Position = Vector3.new(3.0, 13.5, -6.5) },
        FrontRightLower = { Parent = "FrontRightUpper", Position = Vector3.new(3.2, 8.5, -6.0) },
        BackLeftUpper = { Parent = "Body", Position = Vector3.new(-3.0, 13.6, 8.6) },
        BackLeftLower = { Parent = "BackLeftUpper", Position = Vector3.new(-3.4, 8.5, 6.0) },
        BackRightUpper = { Parent = "Body", Position = Vector3.new(3.0, 13.6, 8.6) },
        BackRightLower = { Parent = "BackRightUpper", Position = Vector3.new(3.4, 8.5, 6.0) },
    },
    Glow = {
        Eclipse = { Color = Color3.fromRGB(5, 7, 12) },
        Corona = { Color = Color3.fromRGB(220, 239, 255) },
        Eyes = { Color = Color3.fromRGB(255, 154, 0) },
        Pupils = { Color = Color3.fromRGB(10, 4, 0) },
    },
    -- Only the lower legs (silver claws) have metal; elsewhere Metalness is "".
    -- The first upload of most pieces rendered grey (the neck and jaw's did not): those are
    -- re-uploads with one corner pixel changed.
    Maps = (function()
        local ids = {
            Body = { "rbxassetid://70540436160965", "rbxassetid://107322227159176", "rbxassetid://134239004861626" },
            Neck = { "rbxassetid://122236126384310", "rbxassetid://130025819509539", "rbxassetid://119685709288664" },
            Head = { "rbxassetid://80580881770310", "rbxassetid://121990305656744", "rbxassetid://82668766799006" },
            Jaw = { "rbxassetid://77111200120677", "rbxassetid://75928500104466", "rbxassetid://133953030134925" },
            Tail = { "rbxassetid://140178287802594", "rbxassetid://110820824296903", "rbxassetid://71147159536997" },
            TailTip = { "rbxassetid://78825988418117", "rbxassetid://98043700897869", "rbxassetid://116926536039944" },
            FrontLeftUpper = { "rbxassetid://100038003995289", "rbxassetid://136762544182907", "rbxassetid://103564949087910" },
            FrontLeftLower = { "rbxassetid://78580543911461", "rbxassetid://107604981995911", "rbxassetid://100103882608178", "rbxassetid://119397083368517" },
            FrontRightUpper = { "rbxassetid://127173653826314", "rbxassetid://134660417064342", "rbxassetid://136203922024064" },
            FrontRightLower = { "rbxassetid://96225343882663", "rbxassetid://70754437287147", "rbxassetid://121154125655507", "rbxassetid://112065047561881" },
            BackLeftUpper = { "rbxassetid://97542741236215", "rbxassetid://117949178913890", "rbxassetid://100287085925242" },
            BackLeftLower = { "rbxassetid://124937983896549", "rbxassetid://138818115402740", "rbxassetid://123821133330759", "rbxassetid://85669822000222" },
            BackRightUpper = { "rbxassetid://125044846929884", "rbxassetid://134886904435346", "rbxassetid://91743772004271" },
            BackRightLower = { "rbxassetid://122220555517753", "rbxassetid://110591063645248", "rbxassetid://101853018645671", "rbxassetid://104426016862038" },
        }
        local maps = {}
        for piece, m in ids do
            maps[piece] = { Color = m[1], Normal = m[2], Roughness = m[3], Metalness = m[4] or "" }
        end
        return maps
    end)(),
}

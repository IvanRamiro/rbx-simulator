-- Yggdrasil's guardian, the Awakened Stone Lion (tools/blender/guardians/stone_lion.py): its
-- pieces' centres as authored, in studs from its origin, the ground under its chest (front toward
-- -Z, its left toward -X). Each piece rides a segment, which turns about its pivot. Orb and Eyes are
-- the glow pieces, found by colour (Hex). Used by GuardianBuilder.store.
return {
    Pieces = {
        Body = { Segment = "Body", Centre = Vector3.new(0.0068, 18.3041, -1.7744) },
        BodyCurls = { Segment = "Body", Centre = Vector3.new(0.0158, 19.9758, -2.4750) },
        Orb = { Segment = "Body", Centre = Vector3.new(0.0000, 16.0000, -14.3500), Hex = "2fe6c8" },
        Head = { Segment = "Head", Centre = Vector3.new(0.0087, 27.1051, -14.0477) },
        HeadCurls = { Segment = "Head", Centre = Vector3.new(0.0075, 27.4220, -13.4039) },
        Eyes = { Segment = "Head", Centre = Vector3.new(0.0000, 26.8000, -18.0000), Hex = "39d8ff" },
        Jaw = { Segment = "Jaw", Centre = Vector3.new(0.0232, 21.1729, -17.4823) },
        Tail = { Segment = "Tail", Centre = Vector3.new(0.0022, 18.0445, 10.8420) },
        TailCurls = { Segment = "Tail", Centre = Vector3.new(-0.1113, 23.9898, 12.6505) },
        FrontLeftUpper = { Segment = "FrontLeftUpper", Centre = Vector3.new(-4.4045, 12.1209, -6.5088) },
        FrontLeftLower = { Segment = "FrontLeftLower", Centre = Vector3.new(-4.6002, 5.7828, -8.5900) },
        FrontRightUpper = { Segment = "FrontRightUpper", Centre = Vector3.new(4.4007, 12.1074, -6.5054) },
        FrontRightLower = { Segment = "FrontRightLower", Centre = Vector3.new(4.5974, 5.7844, -8.5877) },
        BackLeftUpper = { Segment = "BackLeftUpper", Centre = Vector3.new(-4.4964, 9.5222, 7.6339) },
        BackLeftLower = { Segment = "BackLeftLower", Centre = Vector3.new(-4.4995, 3.5035, 7.6104) },
        BackRightUpper = { Segment = "BackRightUpper", Centre = Vector3.new(4.4983, 9.5195, 7.6347) },
        BackRightLower = { Segment = "BackRightLower", Centre = Vector3.new(4.5070, 3.4786, 7.6048) },
    },
    -- deeper than the exported colours, which Neon blooms to one flat cyan
    Glow = {
        Eyes = { Color = Color3.fromRGB(0, 110, 255), Scale = Vector3.new(1, 0.45, 0.8) },
        Orb = { Color = Color3.fromRGB(0, 160, 95) },
    },
    -- Parent nil: hangs from the root
    Pivots = {
        Body = { Position = Vector3.new(0, 14, 0) },
        Head = { Parent = "Body", Position = Vector3.new(0, 22, -10) },
        Jaw = { Parent = "Head", Position = Vector3.new(0, 22.8, -14.5) },
        Tail = { Parent = "Body", Position = Vector3.new(0, 16, 9.5) },
        FrontLeftUpper = { Parent = "Body", Position = Vector3.new(-4.4, 15, -6.5) },
        FrontLeftLower = { Parent = "FrontLeftUpper", Position = Vector3.new(-4.6, 8.5, -7) },
        FrontRightUpper = { Parent = "Body", Position = Vector3.new(4.4, 15, -6.5) },
        FrontRightLower = { Parent = "FrontRightUpper", Position = Vector3.new(4.6, 8.5, -7) },
        BackLeftUpper = { Parent = "Body", Position = Vector3.new(-4.3, 14, 6.4) },
        BackLeftLower = { Parent = "BackLeftUpper", Position = Vector3.new(-4.5, 4.6, 9.6) },
        BackRightUpper = { Parent = "Body", Position = Vector3.new(4.3, 14, 6.4) },
        BackRightLower = { Parent = "BackRightUpper", Position = Vector3.new(4.5, 4.6, 9.6) },
    },
    -- granite is a shared flat 0.82 roughness map; only the Body (gold collar) has its own roughness and metalness
    Maps = (function()
        local granite = "rbxassetid://136380863427532"
        local ids = {
            Body = { "rbxassetid://73571242740389", "rbxassetid://137823804730923", "rbxassetid://138509106462198", "rbxassetid://76603684915314" },
            BodyCurls = { "rbxassetid://102770924973008", "rbxassetid://118895832628062" },
            Head = { "rbxassetid://77416026404097", "rbxassetid://129764854844847" },
            HeadCurls = { "rbxassetid://118173877310163", "rbxassetid://138466064520747" },
            Jaw = { "rbxassetid://84283870569568", "rbxassetid://98412106173410" },
            Tail = { "rbxassetid://134953883424265", "rbxassetid://103731131786172" },
            TailCurls = { "rbxassetid://93748616520184", "rbxassetid://116839290049389" },
            FrontLeftUpper = { "rbxassetid://104942928672924", "rbxassetid://97600327643336" },
            FrontLeftLower = { "rbxassetid://118300104726398", "rbxassetid://108286679570505" },
            FrontRightUpper = { "rbxassetid://104202343832421", "rbxassetid://104135008834351" },
            FrontRightLower = { "rbxassetid://106744026934127", "rbxassetid://71460908406620" },
            BackLeftUpper = { "rbxassetid://101588276979183", "rbxassetid://124194705566527" },
            BackLeftLower = { "rbxassetid://72043440253930", "rbxassetid://120516651789952" },
            BackRightUpper = { "rbxassetid://120849952624899", "rbxassetid://133812441815556" },
            BackRightLower = { "rbxassetid://70453828250454", "rbxassetid://75794052893138" },
        }
        local maps = {}
        for piece, m in ids do
            maps[piece] = { Color = m[1], Normal = m[2], Roughness = m[3] or granite, Metalness = m[4] or "" }
        end
        return maps
    end)(),
}

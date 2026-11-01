-- Jade Grove's guardian, the Bamboo Mantis Sage (tools/blender/guardians/mantis_sage.py): its
-- pieces' centres as authored, in studs from its origin, the ground under its thorax (front toward
-- -Z, its left toward -X). Each piece rides a segment, which turns about its pivot. Glow pieces are
-- found by segment and colour. Used by GuardianBuilder.store.
return {
    Pieces = {
        Body = { Segment = "Body", Centre = Vector3.new(0.0000, 11.0554, 13.8851) },
        Mantle = { Segment = "Mantle", Centre = Vector3.new(0.0000, 15.2572, 13.5930) },
        Neck = { Segment = "Neck", Centre = Vector3.new(0.0000, 20.3534, -2.7498) },
        Head = { Segment = "Head", Centre = Vector3.new(0.0000, 29.1416, -6.1216) },
        Pupils = { Segment = "Head", Centre = Vector3.new(0.0000, 29.9000, -9.2500), Hex = "ff9000" },
        LeftArmUpper = { Segment = "LeftArmUpper", Centre = Vector3.new(-2.6787, 19.4246, -7.1400) },
        LeftArmBlade = { Segment = "LeftArmBlade", Centre = Vector3.new(-2.1000, 19.8154, -10.8265) },
        LeftEdge = { Segment = "LeftArmBlade", Centre = Vector3.new(-1.9726, 20.6392, -10.2106), Hex = "00c86e" },
        RightArmUpper = { Segment = "RightArmUpper", Centre = Vector3.new(2.6787, 19.4246, -7.1400) },
        RightArmBlade = { Segment = "RightArmBlade", Centre = Vector3.new(2.1000, 19.8154, -10.8265) },
        RightEdge = { Segment = "RightArmBlade", Centre = Vector3.new(1.9726, 20.6392, -10.2106), Hex = "00c86e" },
        MidLeftUpper = { Segment = "MidLeftUpper", Centre = Vector3.new(-5.7520, 15.3300, 0.1700) },
        MidLeftLower = { Segment = "MidLeftLower", Centre = Vector3.new(-11.3473, 8.2886, -4.0160) },
        MidRightUpper = { Segment = "MidRightUpper", Centre = Vector3.new(5.7520, 15.3300, 0.1700) },
        MidRightLower = { Segment = "MidRightLower", Centre = Vector3.new(11.3473, 8.2886, -4.0160) },
        HindLeftUpper = { Segment = "HindLeftUpper", Centre = Vector3.new(-6.3020, 14.9800, 7.9300) },
        HindLeftLower = { Segment = "HindLeftLower", Centre = Vector3.new(-12.4965, 8.1086, 13.2033) },
        HindRightUpper = { Segment = "HindRightUpper", Centre = Vector3.new(6.3020, 14.9800, 7.9300) },
        HindRightLower = { Segment = "HindRightLower", Centre = Vector3.new(12.4965, 8.1086, 13.2033) },
    },
    -- Parent nil: hangs from the root
    Pivots = {
        Body = { Position = Vector3.new(0, 12.6, 3.0) },
        Mantle = { Parent = "Body", Position = Vector3.new(0, 16.8, 3.5) },
        Neck = { Parent = "Body", Position = Vector3.new(0, 13.6, 1.0) },
        Head = { Parent = "Neck", Position = Vector3.new(0, 26.8, -7.0) },
        LeftArmUpper = { Parent = "Neck", Position = Vector3.new(-1.9, 23.0, -4.6) },
        LeftArmBlade = { Parent = "LeftArmUpper", Position = Vector3.new(-2.1, 15.5, -10.0) },
        RightArmUpper = { Parent = "Neck", Position = Vector3.new(1.9, 23.0, -4.6) },
        RightArmBlade = { Parent = "RightArmUpper", Position = Vector3.new(2.1, 15.5, -10.0) },
        MidLeftUpper = { Parent = "Body", Position = Vector3.new(-2.0, 12.6, 1.8) },
        MidLeftLower = { Parent = "MidLeftUpper", Position = Vector3.new(-9.5, 16.2, -1.6) },
        MidRightUpper = { Parent = "Body", Position = Vector3.new(2.0, 12.6, 1.8) },
        MidRightLower = { Parent = "MidRightUpper", Position = Vector3.new(9.5, 16.2, -1.6) },
        HindLeftUpper = { Parent = "Body", Position = Vector3.new(-2.0, 12.3, 5.6) },
        HindLeftLower = { Parent = "HindLeftUpper", Position = Vector3.new(-10.6, 15.8, 10.4) },
        HindRightUpper = { Parent = "Body", Position = Vector3.new(2.0, 12.3, 5.6) },
        HindRightLower = { Parent = "HindRightUpper", Position = Vector3.new(10.6, 15.8, 10.4) },
    },
    Glow = {
        Pupils = { Color = Color3.fromRGB(255, 144, 0) },
        LeftEdge = { Color = Color3.fromRGB(0, 200, 110) },
        RightEdge = { Color = Color3.fromRGB(0, 200, 110) },
    },
    -- Roughness is flat per material (bamboo 0.38, leaf 0.45, jade 0.14) except on the Head and Neck,
    -- the only pieces with metal. Some colour and normal maps broke on upload (clients render the
    -- piece grey) and are re-uploads with one corner pixel changed.
    Maps = (function()
        local bamboo, leaf, jade = "rbxassetid://117761128526315", "rbxassetid://94743403834731", "rbxassetid://140307857549956"
        local ids = {
            Body = { "rbxassetid://100645344391799", "rbxassetid://129696709912561", bamboo },
            Mantle = { "rbxassetid://130605369031049", "rbxassetid://122544226461031", leaf },
            Neck = { "rbxassetid://108994481443497", "rbxassetid://81270987746177", "rbxassetid://125095087950320", "rbxassetid://103187298576665" },
            Head = { "rbxassetid://133143990318330", "rbxassetid://74997207071602", "rbxassetid://106965955918926", "rbxassetid://133665913524969" },
            LeftArmUpper = { "rbxassetid://135382039653992", "rbxassetid://113314583905381", bamboo },
            RightArmUpper = { "rbxassetid://98495437703174", "rbxassetid://79677433518042", bamboo },
            LeftArmBlade = { "rbxassetid://89392875432433", "rbxassetid://128652024763920", jade },
            RightArmBlade = { "rbxassetid://103517423453711", "rbxassetid://123012737624766", jade },
            MidLeftUpper = { "rbxassetid://124946496936846", "rbxassetid://124352271391163", bamboo },
            MidLeftLower = { "rbxassetid://101905353444590", "rbxassetid://128178006660664", bamboo },
            MidRightUpper = { "rbxassetid://74228287456568", "rbxassetid://117780794767492", bamboo },
            MidRightLower = { "rbxassetid://83074616024951", "rbxassetid://110592393192364", bamboo },
            HindLeftUpper = { "rbxassetid://92692560796915", "rbxassetid://132326868071606", bamboo },
            HindLeftLower = { "rbxassetid://136970192619499", "rbxassetid://118364519158820", bamboo },
            HindRightUpper = { "rbxassetid://97728922069365", "rbxassetid://82543797815934", bamboo },
            HindRightLower = { "rbxassetid://122364005979939", "rbxassetid://124900813141118", bamboo },
        }
        local maps = {}
        for piece, m in ids do
            maps[piece] = { Color = m[1], Normal = m[2], Roughness = m[3], Metalness = m[4] or "" }
        end
        return maps
    end)(),
}

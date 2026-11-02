-- Ember Peak's guardian, the Ember Xuanwu (tools/blender/guardians/ember_xuanwu.py): its pieces'
-- centres as authored, in studs from its origin, the ground under its shell (front toward -Z, its
-- left toward -X). Each piece rides a segment, which turns about its pivot; the basalt Shell rides
-- the Body with its own maps. Glow pieces are found by segment and colour (the dark Neon pupils
-- render as black slits). Used by GuardianBuilder.store.
return {
    Pieces = {
        Body = { Segment = "Body", Centre = Vector3.new(0.3958, 9.3499, 0.5940) },
        Shell = { Segment = "Body", Centre = Vector3.new(0.1720, 14.8802, 1.5532) },
        Magma = { Segment = "Body", Centre = Vector3.new(0.2777, 13.9500, 0.9830), Hex = "ff4600" },
        Neck = { Segment = "Neck", Centre = Vector3.new(0.0082, 8.9275, -14.5451) },
        Head = { Segment = "Head", Centre = Vector3.new(0.0053, 12.0852, -23.3498) },
        Eyes = { Segment = "Head", Centre = Vector3.new(0.0000, 12.1000, -23.4000), Hex = "ffa000" },
        Pupils = { Segment = "Head", Centre = Vector3.new(0.0000, 12.1140, -23.4856), Hex = "1c0700" },
        Throat = { Segment = "Head", Centre = Vector3.new(0.0000, 9.4000, -22.4000), Hex = "ff4600" },
        Jaw = { Segment = "Jaw", Centre = Vector3.new(0.0050, 9.2505, -23.7440) },
        SerpentNeck = { Segment = "SerpentNeck", Centre = Vector3.new(-7.9940, 20.9970, 1.0240) },
        SerpentLava = { Segment = "SerpentNeck", Centre = Vector3.new(-8.1491, 20.8452, 0.7924), Hex = "ff4600" },
        SerpentHead = { Segment = "SerpentHead", Centre = Vector3.new(-5.0000, 27.4068, -14.0884) },
        SerpentEyes = { Segment = "SerpentHead", Centre = Vector3.new(-5.0000, 27.9500, -15.9000), Hex = "ffc800" },
        SerpentPupils = { Segment = "SerpentHead", Centre = Vector3.new(-5.0000, 27.9744, -15.9415), Hex = "1c0700" },
        SerpentMouth = { Segment = "SerpentHead", Centre = Vector3.new(-5.0000, 26.5500, -15.6000), Hex = "ff4600" },
        Tail = { Segment = "Tail", Centre = Vector3.new(0.0132, 4.9665, 18.3642) },
        FrontLeftUpper = { Segment = "FrontLeftUpper", Centre = Vector3.new(-9.9268, 6.0661, -9.2494) },
        FrontLeftLower = { Segment = "FrontLeftLower", Centre = Vector3.new(-12.7925, 3.2411, -11.8740) },
        FrontRightUpper = { Segment = "FrontRightUpper", Centre = Vector3.new(9.9290, 6.0705, -9.2560) },
        FrontRightLower = { Segment = "FrontRightLower", Centre = Vector3.new(12.7954, 3.2382, -11.8701) },
        BackLeftUpper = { Segment = "BackLeftUpper", Centre = Vector3.new(-9.7784, 5.6669, 11.3726) },
        BackLeftLower = { Segment = "BackLeftLower", Centre = Vector3.new(-12.3076, 3.0428, 12.8205) },
        BackRightUpper = { Segment = "BackRightUpper", Centre = Vector3.new(9.7770, 5.6686, 11.3749) },
        BackRightLower = { Segment = "BackRightLower", Centre = Vector3.new(12.2993, 3.0475, 12.8127) },
    },
    -- Parent nil: hangs from the root
    Pivots = {
        Body = { Position = Vector3.new(0.0, 7.0, 1.5) },
        Neck = { Parent = "Body", Position = Vector3.new(0.0, 8.6, -12.0) },
        Head = { Parent = "Neck", Position = Vector3.new(0.0, 10.4, -18.6) },
        Jaw = { Parent = "Head", Position = Vector3.new(0.0, 9.6, -20.6) },
        SerpentNeck = { Parent = "Body", Position = Vector3.new(-7.37, 13.55, 13.41) },
        SerpentHead = { Parent = "SerpentNeck", Position = Vector3.new(-5.0, 27.2, -12.6) },
        Tail = { Parent = "Body", Position = Vector3.new(0.0, 5.6, 16.4) },
        FrontLeftUpper = { Parent = "Body", Position = Vector3.new(-8.6, 6.4, -8.6) },
        FrontLeftLower = { Parent = "FrontLeftUpper", Position = Vector3.new(-12.4, 5.2, -10.6) },
        FrontRightUpper = { Parent = "Body", Position = Vector3.new(8.6, 6.4, -8.6) },
        FrontRightLower = { Parent = "FrontRightUpper", Position = Vector3.new(12.4, 5.2, -10.6) },
        BackLeftUpper = { Parent = "Body", Position = Vector3.new(-8.6, 6.0, 10.8) },
        BackLeftLower = { Parent = "BackLeftUpper", Position = Vector3.new(-12.0, 4.8, 12.6) },
        BackRightUpper = { Parent = "Body", Position = Vector3.new(8.6, 6.0, 10.8) },
        BackRightLower = { Parent = "BackRightUpper", Position = Vector3.new(12.0, 4.8, 12.6) },
    },
    Glow = {
        Magma = { Color = Color3.fromRGB(255, 110, 0) },
        Eyes = { Color = Color3.fromRGB(255, 160, 0) },
        Pupils = { Color = Color3.fromRGB(28, 7, 0) },
        Throat = { Color = Color3.fromRGB(255, 110, 0) },
        SerpentEyes = { Color = Color3.fromRGB(255, 200, 0) },
        SerpentPupils = { Color = Color3.fromRGB(28, 7, 0) },
        SerpentMouth = { Color = Color3.fromRGB(255, 110, 0) },
        SerpentLava = { Color = Color3.fromRGB(255, 110, 0) },
    },
    -- Nothing on it is metal (Metalness ""); roughness varies (ash on the basalt, the crust's cracks).
    -- The SerpentHead's first upload rendered grey on clients: its maps are re-uploads with one corner
    -- pixel changed.
    Maps = (function()
        local ids = {
            Shell = { "rbxassetid://100370614147187", "rbxassetid://136602794716240", "rbxassetid://119368882681433" },
            Body = { "rbxassetid://128384881915998", "rbxassetid://117842589609351", "rbxassetid://125532819980068" },
            Neck = { "rbxassetid://99626560856823", "rbxassetid://82818269886764", "rbxassetid://140234558926853" },
            Head = { "rbxassetid://132043394784815", "rbxassetid://94501936154112", "rbxassetid://121511415529682" },
            Jaw = { "rbxassetid://107978035454593", "rbxassetid://86047034021642", "rbxassetid://82583692761905" },
            SerpentNeck = { "rbxassetid://82547755088886", "rbxassetid://106986207288691", "rbxassetid://116764829713485" },
            SerpentHead = { "rbxassetid://82214490342294", "rbxassetid://137322614081606", "rbxassetid://102969092853423" },
            Tail = { "rbxassetid://101319583277644", "rbxassetid://74991978231511", "rbxassetid://112190060594514" },
            FrontLeftUpper = { "rbxassetid://83422693839130", "rbxassetid://106504439309563", "rbxassetid://136711125288775" },
            FrontLeftLower = { "rbxassetid://81316185627538", "rbxassetid://124277092371796", "rbxassetid://72833554843704" },
            FrontRightUpper = { "rbxassetid://117899171922551", "rbxassetid://104514624111591", "rbxassetid://106931466997902" },
            FrontRightLower = { "rbxassetid://130995709541171", "rbxassetid://101076106785896", "rbxassetid://107562598008031" },
            BackLeftUpper = { "rbxassetid://116619511351733", "rbxassetid://133351371105610", "rbxassetid://76337624024024" },
            BackLeftLower = { "rbxassetid://97400871524031", "rbxassetid://104394343102457", "rbxassetid://85611025235371" },
            BackRightUpper = { "rbxassetid://109711790245310", "rbxassetid://70973953608615", "rbxassetid://75887786705445" },
            BackRightLower = { "rbxassetid://71630498006822", "rbxassetid://108969716647802", "rbxassetid://83197991429188" },
        }
        local maps = {}
        for piece, m in ids do
            maps[piece] = { Color = m[1], Normal = m[2], Roughness = m[3], Metalness = "" }
        end
        return maps
    end)(),
}

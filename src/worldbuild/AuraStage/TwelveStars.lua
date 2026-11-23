-- TWELVE STARS: a prototype for the top of the realm ladder (the owner's go-ahead, 2026-11-23: "yeah sure go ahead"; a fresh idea, not one of his earlier requests).
-- NOT in the game: this is dev-stage code (ServerStorage.WorldBuild.AuraStage, copied into ServerStorage.DevStage.AuraTwelveStars) for judging the idea in motion
-- before anything is wired into RealmAura.
--
-- The idea: an Eternal Transcendence cultivator carries every realm they have passed through. Twelve small stars light up one by one over their head, each in the colour of
-- its realm (jade, teal, gold, blue, orange, silver, crimson, violet, ice blue, rose, lava, and the twelfth, the current realm, a burning prismatic gem), and thin lines draw
-- from star to star into a constellation: the Ascent (a climbing zigzag), the Lotus (a six-petalled star) or the Gate (an arch). The constellation hangs facing the viewer,
-- holds, shimmers, then comes apart: the stars fall in turn into the chest, each landing as a flash of its colour and a bell tone, the last with a swell. Then a rest, then the next
-- shape. A very slight cool shift of the sky while it plays (full quality only).
--
-- Cost (one aura): 13 particle emitters (one per star, one at the chest), up to 12 beams (hairlines), 1 point light, 1 small mesh part (the twelfth star's gem), 3 sounds,
-- and 13 invisible anchored specks that the particles ride on.
-- Reduced Effects: a short quick version, no sky, one sound. Phone (Low): half the sparks, no sky.
--
--   local handle = TwelveStars.start(rootPart, { Reduced = false, Low = false, Sky = true, Sounds = true, Shape = 0, Gem = <MeshPart template>, FaceToward = nil, Speed = 1, Gap = 7 })
--   handle.destroy()
-- Shape 0 cycles the three; 1, 2 or 3 holds one. FaceToward (a Vector3) makes it face a fixed point instead of the camera (for screenshots). Speed < 1 is slow motion.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local AuraConfig = require(ReplicatedStorage:WaitForChild("AuraConfig"))

local TEX = {
    Star = "rbxassetid://12363796862",  -- a four-point star glint (the owner's body aura's BodyStar)
}
local SOUND = {
    Bell = "rbxassetid://9126072453",   -- the bright bell-tone ding the game already uses (SoundCatalog SecureDing, from 0.25 s)
    Harp = "rbxassetid://1840525370",   -- Harp Glissando (C), the game's rising run (from 0.3 s)
}
-- a pentatonic climb over a bit more than two octaves: one bell tone per star, the twelfth the highest
local NOTES = { 0.6, 0.675, 0.75, 0.9, 1.0, 1.2, 1.35, 1.5, 1.8, 2.0, 2.4, 2.7 }

-- The three constellations: 12 points each (x -1 to 1, y 0 to 1), drawn as a path from the first star to the twelfth; a closed one also joins the twelfth to the first.
local function lotus()
    local pts = {}
    for k = 0, 11 do
        local a = math.rad(90 - k * 30)
        local r = if k % 2 == 0 then 1.0 else 0.48
        table.insert(pts, { math.cos(a) * r, 0.5 + math.sin(a) * r * 0.5 })
    end
    return pts
end
local SHAPES = {
    { Name = "Ascent", Closed = false, Points = {
        { -1.00, 0.00 }, { -0.78, 0.20 }, { -0.58, 0.06 }, { -0.36, 0.30 }, { -0.16, 0.16 }, { 0.06, 0.44 },
        { 0.24, 0.30 }, { 0.44, 0.60 }, { 0.60, 0.48 }, { 0.78, 0.80 }, { 0.88, 0.66 }, { 1.00, 1.00 } } },
    { Name = "Lotus", Closed = true, Points = lotus() },
    { Name = "Gate", Closed = false, Points = {
        { -0.62, 0.00 }, { -0.62, 0.28 }, { -0.62, 0.56 }, { -0.54, 0.80 }, { -0.30, 0.95 }, { -0.10, 1.00 },
        { 0.10, 1.00 }, { 0.30, 0.95 }, { 0.54, 0.80 }, { 0.62, 0.56 }, { 0.62, 0.28 }, { 0.62, 0.00 } } },
}

local CENTRE_HEIGHT = 10.5   -- studs over the root part: the constellation's middle
local WIDTH, HEIGHT, DEPTH = 5.2, 8.0, 1.1 -- half width, full height, depth wobble (studs)
local CHEST = Vector3.new(0, 1.2, 0)

local function easeOut(t)
    return 1 - (1 - t) ^ 3
end
local function easeIn(t)
    return t * t
end
local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end

local TwelveStars = {}

function TwelveStars.start(root, options)
    options = options or {}
    local reduced = options.Reduced == true
    local low = options.Low == true
    local useSounds = options.Sounds ~= false
    local useSky = options.Sky ~= false and not reduced and not low
    local speed = options.Speed or 1
    local gap = options.Gap or 7
    local fixedShape = options.Shape or 0
    local faceToward = options.FaceToward

    -- the timeline of one cycle, in seconds
    local APPEAR_FROM = if reduced then 0.2 else 1.0
    local APPEAR_EVERY = if reduced then 0.16 else 0.52
    local HOLD = if reduced then 1.6 else 4.0
    local FALL_EVERY = if reduced then 0.08 else 0.23
    local FALL_TIME = if reduced then 0.6 else 1.1
    local DRAW_TIME = if reduced then 0.2 else 0.45
    local appearEnd = APPEAR_FROM + 11 * APPEAR_EVERY + 0.45 -- the twelfth is up and the whole constellation pulses
    local fallFrom = appearEnd + HOLD
    local fallEnd = fallFrom + 11 * FALL_EVERY + FALL_TIME
    local cycleLength = fallEnd + (if reduced then 2 else gap)

    -- ---------- instances ----------
    local folder = Instance.new("Folder")
    folder.Name = "TwelveStars"
    local carrier = Instance.new("Part") -- rides on the root; every attachment's Position is a world offset from the root
    carrier.Name = "Carrier"
    carrier.Size = Vector3.new(0.2, 0.2, 0.2)
    carrier.Transparency = 1
    carrier.Anchored = true
    carrier.CanCollide, carrier.CanQuery, carrier.CanTouch = false, false, false
    carrier.CastShadow = false
    carrier.CFrame = CFrame.new(root.Position)
    carrier.Parent = folder

    local function attachment(name, parent)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Parent = parent or carrier
        return a
    end
    local function tinyPart(name)
        local part = Instance.new("Part") -- (an invisible anchored speck: particles locked to it move with it)
        part.Name = name
        part.Size = Vector3.new(0.1, 0.1, 0.1)
        part.Transparency = 1
        part.Anchored = true
        part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
        part.CastShadow = false
        part.CFrame = CFrame.new(root.Position)
        part.Parent = folder
        return part
    end

    local stars = {}
    for i = 1, 12 do
        local tier = AuraConfig.Tiers[i]
        local hot, main = tier.Palette.Hot, tier.Palette.Main
        local part = tinyPart("Star" .. i)
        local star = { hot = hot, main = main, part = part, att = attachment("Anchor", part), pos = Vector3.zero, state = "hidden", appearAt = 0, fallAt = 0, fallFrom = Vector3.zero, side = Vector3.zero }
        local e = Instance.new("ParticleEmitter")
        e.Name = "Glint"
        e.Texture = TEX.Star
        e.Color = ColorSequence.new(Color3.new(1, 1, 1):Lerp(hot, 0.82), main)
        e.LightEmission = 1
        e.LightInfluence = 0
        e.Transparency = seq({ { 0, 1 }, { 0.12, 0.08 }, { 0.72, 0.22 }, { 1, 1 } })
        e.Lifetime = NumberRange.new(2.0, 2.6)
        e.Speed = NumberRange.new(0)
        e.Rotation = NumberRange.new(-10, 10)
        e.RotSpeed = NumberRange.new(-8, 8)
        e.ZOffset = 0.5
        e.Rate = 0
        e.LockedToPart = true
        e.Enabled = false
        e.Parent = star.att
        star.glint = e
        star.size = if i == 12 then 5.0 else 2.7
        stars[i] = star
    end

    local chestAtt = attachment("Chest")
    chestAtt.Position = CHEST
    local chestEmitter = Instance.new("ParticleEmitter")
    chestEmitter.Name = "ChestFlash"
    chestEmitter.Texture = TEX.Star
    chestEmitter.LightEmission = 1
    chestEmitter.LightInfluence = 0
    chestEmitter.Size = seq({ { 0, 1.0 }, { 0.18, 3.8 }, { 1, 0 } })
    chestEmitter.Transparency = seq({ { 0, 0.05 }, { 0.6, 0.3 }, { 1, 1 } })
    chestEmitter.Lifetime = NumberRange.new(0.55, 0.9)
    chestEmitter.Speed = NumberRange.new(2, 8)
    chestEmitter.SpreadAngle = Vector2.new(180, 180)
    chestEmitter.Rotation = NumberRange.new(0, 90)
    chestEmitter.Drag = 3
    chestEmitter.Rate = 0
    chestEmitter.Parent = chestAtt

    local chestLight = Instance.new("PointLight")
    chestLight.Range = 14
    chestLight.Brightness = 0
    chestLight.Shadows = false
    chestLight.Parent = carrier

    local edges = {}
    local shapeEdges = 12
    for k = 1, shapeEdges do
        local a0 = stars[k].att
        local tip = attachment("Tip" .. k)
        local b = Instance.new("Beam")
        b.Name = "Line" .. k
        b.Attachment0, b.Attachment1 = a0, tip
        local following = stars[k % 12 + 1]
        b.Color = ColorSequence.new(stars[k].hot, following.hot)
        b.LightEmission = 1
        b.LightInfluence = 0
        b.FaceCamera = true
        b.Segments = 1
        b.Width0, b.Width1 = 0.2, 0.2
        b.Transparency = NumberSequence.new(1)
        b.Enabled = false
        b.Parent = carrier
        edges[k] = { beam = b, tip = tip, from = k, to = k % 12 + 1, drawAt = math.huge, fade = 0 }
    end

    local gem
    if options.Gem then
        gem = options.Gem:Clone()
        gem.Name = "EternalStar"
        gem.Anchored = true
        gem.CanCollide, gem.CanQuery, gem.CanTouch = false, false, false
        gem.CastShadow = false
        gem.Massless = true
        gem.Material = Enum.Material.Glass
        gem.Size = Vector3.new(1.05, 1.9, 1.05)
        gem.Transparency = 1
        gem.Parent = folder
    end

    local sounds = {}
    if useSounds then
        for k = 1, 3 do
            local s = Instance.new("Sound")
            s.Name = "Bell" .. k
            s.SoundId = SOUND.Bell
            s.RollOffMode = Enum.RollOffMode.InverseTapered
            s.RollOffMinDistance = 14
            s.RollOffMaxDistance = 80
            s.Parent = carrier
            sounds[k] = s
        end
    end
    local harp
    if useSounds then
        harp = Instance.new("Sound")
        harp.Name = "Harp"
        harp.SoundId = SOUND.Harp
        harp.Volume = 0
        harp.RollOffMode = Enum.RollOffMode.InverseTapered
        harp.RollOffMinDistance = 14
        harp.RollOffMaxDistance = 80
        harp.Parent = carrier
    end
    local soundNext = 0
    local function bell(note, volume)
        if not useSounds then
            return
        end
        soundNext = soundNext % 3 + 1
        local s = sounds[soundNext]
        s.PlaybackSpeed = note
        s.Volume = volume
        s.TimePosition = 0.25
        s:Play()
    end

    local sky
    if useSky then
        sky = Instance.new("ColorCorrectionEffect")
        sky.Name = "TwelveStarsSky"
        sky.Enabled = true
        sky.Parent = Lighting
    end
    local function skyTo(on, seconds)
        if sky then
            TweenService:Create(sky, TweenInfo.new(seconds, Enum.EasingStyle.Sine), {
                TintColor = if on then Color3.fromRGB(232, 236, 255) else Color3.new(1, 1, 1),
                Brightness = if on then -0.05 else 0,
                Saturation = if on then 0.16 else 0,
            }):Play()
        end
    end

    folder.Parent = Workspace

    -- ---------- the cycle ----------
    local shapeIndex = 0
    local cycleStart = os.clock()
    local shape = SHAPES[1]
    local up = Vector3.yAxis
    local toward = Vector3.new(0, 0, 1)
    local skyOn = false
    local pulsed = false
    local arrivals = {}   -- stars that have landed this cycle
    local lastPulse = -10 -- the chest light's last landing time

    local function startCycle()
        shapeIndex = if fixedShape ~= 0 then fixedShape else shapeIndex % #SHAPES + 1
        shape = SHAPES[shapeIndex]
        cycleStart = os.clock()
        pulsed = false
        skyOn = false
        arrivals = {}
        for i, star in stars do
            star.state = "hidden"
            star.glint.Enabled = false
            star.glint.Rate = 0
            star.appearAt = APPEAR_FROM + (i - 1) * APPEAR_EVERY
            star.fallAt = fallFrom + (i - 1) * FALL_EVERY
            local p = shape.Points[i]
            local wob = math.sin(i * 2.1 + shapeIndex * 1.3)
            star.target = { (p[1]) * WIDTH, (p[2] - 0.5) * HEIGHT, wob * DEPTH }
            star.side = Vector3.new(math.cos(i * 1.7), 0, math.sin(i * 1.7)) * 2.2
        end
        for k, edge in edges do
            edge.beam.Enabled = false
            edge.fade = 0
            if k < 12 then
                edge.drawAt = APPEAR_FROM + k * APPEAR_EVERY -- the line from star k to star k+1 draws as star k+1 appears
            elseif shape.Closed then
                edge.drawAt = APPEAR_FROM + 11 * APPEAR_EVERY + 0.25 -- the closing line, once the twelfth is up
            else
                edge.drawAt = math.huge
            end
        end
        if gem then
            gem.Transparency = 1
        end
    end
    startCycle()

    local function place(star, t)
        -- the star's offset from the root, in the viewer's frame (right, up, toward)
        local right = up:Cross(toward)
        local base = Vector3.new(0, CENTRE_HEIGHT, 0) + right * star.target[1] + up * star.target[2] + toward * star.target[3]
        return base + up * (math.sin(t * 0.9 + star.target[1]) * 0.12)
    end

    local connection
    connection = RunService.RenderStepped:Connect(function(dt)
        if not root.Parent then
            return
        end
        local rootPos = root.Position
        carrier.CFrame = CFrame.new(rootPos)
        local now = (os.clock() - cycleStart) * speed
        if now >= cycleLength then
            startCycle()
            now = 0
        end

        -- the viewer: the camera, or a fixed point
        local viewer = faceToward or (Workspace.CurrentCamera and Workspace.CurrentCamera.CFrame.Position) or (rootPos + Vector3.new(0, 0, 20))
        local flat = Vector3.new(viewer.X - rootPos.X, 0, viewer.Z - rootPos.Z)
        if flat.Magnitude > 0.5 then
            toward = toward:Lerp(flat.Unit, 1 - math.exp(-dt * 3)).Unit
        end

        if useSky then
            local wantSky = now > 0.4 and now < fallEnd - 1.5
            if wantSky ~= skyOn then
                skyOn = wantSky
                skyTo(wantSky, 2.2)
            end
        end

        for i, star in stars do
            if star.state == "hidden" and now >= star.appearAt then
                star.state = "lit"
                star.glint.Size = seq({ { 0, 0 }, { 0.12, star.size }, { 0.7, star.size * 0.82 }, { 1, 0 } })
                star.glint.Lifetime = NumberRange.new(2.0, 2.6)
                star.glint.LockedToPart = true
                star.glint.Rate = if low then 0.7 else 1.1
                star.glint.Enabled = true
                star.glint:Emit(1)
                -- the first light of a star flashes: its brightness pops and settles
                star.glint.Brightness = 2.2
                TweenService:Create(star.glint, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 1 }):Play()
                if i == 12 then
                    bell(NOTES[i], 0.62)
                    if gem then
                        gem.Transparency = 0.12
                    end
                elseif not reduced then
                    bell(NOTES[i], 0.4)
                end
            end
            if star.state == "lit" and now >= star.fallAt then
                star.state = "falling"
                star.fallFrom = star.pos
                star.glint.LockedToPart = false
                star.glint.Lifetime = NumberRange.new(0.4, 0.55)
                star.glint.Size = seq({ { 0, star.size * 0.3 }, { 1, 0 } })
                star.glint.Rate = if low then 14 else 30
                if not reduced then
                    bell(NOTES[i] * 0.5, 0.16)
                end
            end
            if star.state == "lit" then
                star.pos = place(star, now)
            elseif star.state == "falling" then
                local p = math.clamp((now - star.fallAt) / FALL_TIME, 0, 1)
                local u = easeIn(p)
                local from = star.fallFrom
                local control = (from + CHEST) / 2 + star.side + Vector3.new(0, 1.2, 0)
                local a, b = from:Lerp(control, u), control:Lerp(CHEST, u)
                star.pos = a:Lerp(b, u)
                if p >= 1 then
                    star.state = "gone"
                    star.glint.Rate = 0
                    -- it lands in the chest: a flash of its colour, a pulse of light, a tone
                    chestEmitter.Color = ColorSequence.new(Color3.new(1, 1, 1):Lerp(star.hot, 0.8), star.main)
                    chestEmitter:Emit(if low then 5 elseif i == 12 then 26 else 11)
                    chestLight.Color = star.hot
                    lastPulse = os.clock()
                    chestLight.Brightness = if i == 12 then 4 else 2.2
                    arrivals[i] = true
                    if i == 12 then
                        if gem then
                            gem.Transparency = 1
                        end
                        if useSounds and harp then
                            harp.Volume = 0.55
                            harp.PlaybackSpeed = 1
                            harp.TimePosition = 0.3
                            harp:Play()
                        end
                        bell(NOTES[12], 0.5)
                    elseif not reduced then
                        bell(NOTES[i] * 1.0, 0.2)
                    end
                end
            end
            if star.state ~= "hidden" and star.state ~= "gone" then
                star.part.CFrame = CFrame.new(rootPos + star.pos)
            end
        end

        -- the lines: each draws out from one star to the next as the next appears, fades when either end starts to fall
        for k, edge in edges do
            local a, b = stars[edge.from], stars[edge.to]
            local active = edge.drawAt < math.huge and now >= edge.drawAt and a.state ~= "hidden" and b.state ~= "hidden" and a.state ~= "gone" and b.state ~= "gone"
            if active then
                local p = math.clamp((now - edge.drawAt) / DRAW_TIME, 0, 1)
                edge.tip.Position = a.pos:Lerp(b.pos, easeOut(p))
                local fadeOut = 0
                if a.state == "falling" or b.state == "falling" then
                    fadeOut = math.clamp((now - math.min(a.fallAt, b.fallAt)) / 0.35, 0, 1)
                end
                local shimmer = 0.1 + 0.07 * math.sin(now * 3 + k * 0.8)
                edge.beam.Transparency = NumberSequence.new(shimmer + (1 - shimmer) * math.max(fadeOut, 1 - math.min(1, p * 3)))
                edge.beam.Enabled = true
            elseif edge.beam.Enabled then
                edge.beam.Enabled = false
            end
        end

        -- the twelfth star's gem: turns, and its colour walks through the twelve realms
        if gem and stars[12].state ~= "hidden" and stars[12].state ~= "gone" then
            local s = stars[12]
            gem.CFrame = CFrame.new(rootPos + s.pos) * CFrame.Angles(0, now * 1.4, math.sin(now * 0.9) * 0.12)
            local f = (now * 0.35) % 12
            local i0 = math.floor(f) % 12 + 1
            local i1 = i0 % 12 + 1
            gem.Color = stars[i0].hot:Lerp(stars[i1].hot, f - math.floor(f))
            s.glint.Color = ColorSequence.new(Color3.new(1, 1, 1):Lerp(gem.Color, 0.8), gem.Color)
        end

        -- the whole constellation pulses once when the twelfth is up
        if not pulsed and now >= appearEnd - 0.1 then
            pulsed = true
            for _, star in stars do
                if star.state == "lit" then
                    star.glint.Brightness = 1.8
                    TweenService:Create(star.glint, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 1 }):Play()
                end
            end
        end

        -- the chest light settles
        if chestLight.Brightness > 0 then
            chestLight.Brightness = math.max(0, chestLight.Brightness * math.exp(-dt * 5) - dt * 0.2)
        end
    end)

    local handle = {}
    function handle.destroy()
        if connection then
            connection:Disconnect()
            connection = nil
        end
        folder:Destroy()
        if sky then
            sky:Destroy()
        end
    end
    function handle.info()
        return { Shape = shape.Name, Cycle = cycleLength, Elapsed = (os.clock() - cycleStart) * speed }
    end
    return handle
end

return TwelveStars

-- BLACK TEMPEST: a prototype of a wide-area, ominous aura (the owner, 2026-11-23: "a completely different one ... like the one in Sol's RNG, wide area effects, ominous aura,
-- with black and red lightning, sharp spread in all directions"). NOT in the game: dev-stage code (ServerStorage.WorldBuild.AuraStage, copied into ServerStorage.DevStage.AuraBlackTempest).
-- Nothing here is any existing realm's aura, and none of its motifs is taken from one.
--
-- What it is, from the ground up (radius about 40 studs, so it takes the space round the cultivator, not just their body):
--   * a wide stain of black smoke on the ground under a faint red glow, red embers rising out of it; the ground is the aura's floor
--   * a dark red-black storm cloud ceiling overhead (the Tribulation's own cloud recipe) whose underside flashes red
--   * BLACK-AND-RED LIGHTNING: jagged bolts (a black core in normal blend, a red glow in additive over it) that strike outward in every direction, low and wide
--     or climbing into the cloud, now and then forking; and cracks of red lightning that run along the ground and linger
--   * SHARP SPIKES: straight, tapering black shards tipped red that stab out in all directions and snap back
--   * a RUPTURE every 12 to 20 s (and when it awakens): every spike and a ring of bolts at once, a crackling shockwave along the ground, a flash in the cloud, a flash of light,
--     a boom, a short shake
--   * the AWAKENING: for 2.4 s darkness is drawn in from all sides while the screen dims, then the first rupture
--   * ominous presence: black smoke off the body, red embers, red glowing eyes
--   * the viewer's screen darkens and reddens the nearer they are (a colour grade driven by distance), so walking into it is felt
-- Cost (one aura, full quality): 11 emitters, 14 beams (the spikes), 28 trails (10 bolts and 4 cracks, two each), 1 light, 6 sounds, about 25 invisible anchored parts.
-- Reduced Effects: half the bolts and spikes, 40% of the particles, no shake, no screen grade, no flashes. Phone (Low): about 60% of the bolts and spikes, half the particles.
--
--   local handle = BlackTempest.start(rootPart, { Reduced = false, Low = false, Sounds = true, Grade = true, Shake = true, Speed = 1, Scale = 1, Gap = 16, Eyes = true })
--   handle.awaken()  handle.surge()  handle.destroy()
local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local TEX = {
    Smoke = "rbxassetid://113821949376919",  -- the base aura's ground smoke (BaseSmoke)
    Cloud = "rbxassetid://16867371255",       -- the Tribulation's billowy cloud, a 4x4 flipbook
    Spark = "rbxassetid://9997556038",        -- a small round spark (BodySpark)
    Glow = "rbxassetid://135169457468310",    -- the project's glow
    SoftGlow = "rbxassetid://243664672",      -- a soft round glow (the PDS kit): across a trail it is a bright heart fading to nothing at the edges
    ShockRing = "rbxassetid://6900421398",    -- a crackling electric ring (PDS Rings)
}
local SOUND = { -- the game's own storm sounds (SoundCatalog: the Tribulation and the guardians)
    Gather = "rbxassetid://9120032392",   -- thunder rolling in
    Storm = "rbxassetid://9119806923",    -- a deep pulsing rumble
    Strike = "rbxassetid://9114246605",   -- the crack
    Boom = "rbxassetid://9113551995",     -- and its boom
    Split = "rbxassetid://9116282875",    -- lightning tears the sky
}
local BLACK = Color3.fromRGB(12, 2, 6)
local DEEP = Color3.fromRGB(78, 6, 16)
local RED = Color3.fromRGB(228, 22, 38)
local HOT = Color3.fromRGB(255, 96, 72)

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end
local function easeOut(t)
    return 1 - (1 - t) ^ 3
end
local function rand(a, b)
    return a + (b - a) * math.random()
end

-- a point on a direction: azimuth (radians) and elevation (radians)
local function direction(azimuth, elevation)
    local c = math.cos(elevation)
    return Vector3.new(math.cos(azimuth) * c, math.sin(elevation), math.sin(azimuth) * c)
end

-- a jagged path from an origin along a direction
local function boltPath(origin, dir, length, steps, jitter)
    local side = dir:Cross(Vector3.yAxis)
    if side.Magnitude < 0.1 then
        side = Vector3.xAxis
    end
    side = side.Unit
    local side2 = dir:Cross(side).Unit
    local pts = { origin }
    for k = 1, steps do
        local f = k / steps
        local p = origin + dir * (length * f)
        local j = jitter * length * (1 - 0.45 * f)
        if k < steps then
            p += side * ((math.random() - 0.5) * 2 * j) + side2 * ((math.random() - 0.5) * 2 * j)
        else
            p += side * ((math.random() - 0.5) * j)
        end
        table.insert(pts, p)
    end
    return pts
end

local BlackTempest = {}

function BlackTempest.start(root, options)
    options = options or {}
    local reduced = options.Reduced == true
    local low = options.Low == true
    local useSounds = options.Sounds ~= false
    local useGrade = options.Grade ~= false and not reduced
    local useShake = options.Shake ~= false and not reduced
    local speed = options.Speed or 1
    local scale = options.Scale or 1
    local gap = options.Gap or 16
    local eyes = options.Eyes ~= false

    local BOLTS = if reduced then 5 elseif low then 6 else 10
    local CRACKS = if reduced then 2 elseif low then 3 else 4
    local SPIKES = if reduced then 6 elseif low then 8 else 14
    local RATE = if reduced then 0.4 elseif low then 0.5 else 1
    local GATHER = 2.4 -- seconds of darkness drawn in before the first rupture
    local REACH = 40 * scale -- the aura's radius

    -- ---------- instances ----------
    local folder = Instance.new("Folder")
    folder.Name = "BlackTempest"
    local function speck(name, size, parent)
        local part = Instance.new("Part")
        part.Name = name
        part.Size = size or Vector3.new(0.2, 0.2, 0.2)
        part.Transparency = 1
        part.Anchored = true
        part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
        part.CastShadow = false
        part.CFrame = CFrame.new(root.Position)
        part.Parent = parent or folder
        return part
    end
    local center = speck("Center")                                   -- rides on the root; its attachments' Positions are world offsets
    local ground = speck("Ground", Vector3.new(REACH * 1.1, 0.2, REACH * 1.1)) -- the floor layers (a disc of emitters)
    local cloud = speck("Cloud", Vector3.new(REACH * 1.25, 2, REACH * 1.25))
    local gather = speck("Gather", Vector3.new(REACH * 1.2, REACH * 1.2, REACH * 1.2))
    local function attachment(name, parent, position)
        local a = Instance.new("Attachment")
        a.Name = name
        a.Position = position or Vector3.zero
        a.Parent = parent
        return a
    end
    local function emitter(parent, props)
        local e = Instance.new("ParticleEmitter")
        for k, v in props do
            e[k] = v
        end
        e.Rate = (props.Rate or 0) * RATE
        e.Parent = parent
        return e
    end
    local flat = { Orientation = Enum.ParticleOrientation.VelocityPerpendicular, EmissionDirection = Enum.NormalId.Top, Speed = NumberRange.new(0.001), SpreadAngle = Vector2.new(2, 2) }
    local function withFlat(props)
        for k, v in flat do
            if props[k] == nil then
                props[k] = v
            end
        end
        return props
    end

    local idleEmitters = {}
    local function idle(e)
        e.Enabled = false
        table.insert(idleEmitters, e)
        return e
    end

    -- the floor: black smoke, a faint red glow under it, embers rising
    idle(emitter(ground, withFlat({
        Name = "DarkMist", Texture = TEX.Smoke, Color = ColorSequence.new(Color3.fromRGB(34, 4, 10), Color3.fromRGB(96, 10, 22)), LightEmission = 0.06, LightInfluence = 0.1,
        Size = seq({ { 0, 8 * scale }, { 1, 26 * scale } }), Transparency = seq({ { 0, 1 }, { 0.18, 0.3 }, { 0.75, 0.5 }, { 1, 1 } }),
        Lifetime = NumberRange.new(4, 6), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-6, 6), Rate = 7,
        Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
    })))
    idle(emitter(ground, withFlat({
        Name = "EmberGlow", Texture = TEX.Glow, Color = ColorSequence.new(RED, DEEP), LightEmission = 1, LightInfluence = 0, Brightness = 2.4,
        Size = seq({ { 0, 14 * scale }, { 1, 30 * scale } }), Transparency = seq({ { 0, 1 }, { 0.3, 0.82 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2.5, 4), Rate = 1.6, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
    })))
    idle(emitter(ground, {
        Name = "Embers", Texture = TEX.Spark, Color = ColorSequence.new(HOT, RED), LightEmission = 1, LightInfluence = 0,
        Size = seq({ { 0, 0.55 }, { 1, 0 } }), Transparency = seq({ { 0, 0.1 }, { 0.8, 0.3 }, { 1, 1 } }),
        Lifetime = NumberRange.new(2, 3.6), Speed = NumberRange.new(3, 10), SpreadAngle = Vector2.new(25, 25), Acceleration = Vector3.new(0, 5, 0), Drag = 0.6,
        EmissionDirection = Enum.NormalId.Top, Rate = 22, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
    }))
    -- the storm ceiling and its flash
    idle(emitter(cloud, {
        Name = "Storm", Texture = TEX.Cloud, FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        Color = ColorSequence.new(Color3.fromRGB(26, 4, 9), Color3.fromRGB(96, 12, 26)), LightEmission = 0.05, LightInfluence = 0.15,
        Size = seq({ { 0, 14 * scale }, { 1, 30 * scale } }), Transparency = seq({ { 0, 1 }, { 0.25, 0.15 }, { 0.8, 0.3 }, { 1, 1 } }),
        Lifetime = NumberRange.new(3.5, 5), Speed = NumberRange.new(0.5, 2), SpreadAngle = Vector2.new(180, 10), RotSpeed = NumberRange.new(-12, 12),
        Rotation = NumberRange.new(0, 360), Rate = 20, Shape = Enum.ParticleEmitterShape.Disc, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
    }))
    local cloudFlash = emitter(cloud, {
        Name = "CloudFlash", Texture = TEX.Glow, Color = ColorSequence.new(HOT, RED), LightEmission = 1, LightInfluence = 0, Brightness = 2,
        Size = NumberSequence.new(40 * scale), Transparency = seq({ { 0, 0.5 }, { 1, 1 } }), Lifetime = NumberRange.new(0.35, 0.5), Speed = NumberRange.new(0), Rate = 0,
    })
    local ambientLight = Instance.new("PointLight") -- the aura lights its own surroundings a dull red, day or night
    ambientLight.Name = "AmbientRed"
    ambientLight.Color = Color3.fromRGB(210, 24, 36)
    ambientLight.Range = 75 * scale
    ambientLight.Brightness = 0
    ambientLight.Shadows = false
    ambientLight.Parent = ground
    local cloudLight = Instance.new("PointLight")
    cloudLight.Color = RED
    cloudLight.Range = 70
    cloudLight.Brightness = 0
    cloudLight.Shadows = false
    cloudLight.Parent = cloud
    -- the awakening's inward rush of darkness
    local gatherEmitter = emitter(gather, {
        Name = "Gather", Texture = TEX.Smoke, Color = ColorSequence.new(BLACK, DEEP), LightEmission = 0, LightInfluence = 0,
        Size = seq({ { 0, 6 * scale }, { 1, 0 } }), Transparency = seq({ { 0, 1 }, { 0.2, 0.3 }, { 1, 0.9 } }), Lifetime = NumberRange.new(1.5, 2.1),
        Speed = NumberRange.new(14 * scale, 20 * scale), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30), Rate = 0,
        Shape = Enum.ParticleEmitterShape.Sphere, ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
    })
    -- the rupture's shockwave, crackling along the ground
    local shock = emitter(ground, withFlat({
        Name = "Shock", Texture = TEX.ShockRing, Color = ColorSequence.new(HOT, RED), LightEmission = 1, LightInfluence = 0, Brightness = 3,
        Size = seq({ { 0, 3 }, { 1, REACH * 1.9 } }), Transparency = seq({ { 0, 0.05 }, { 0.65, 0.35 }, { 1, 1 } }), Lifetime = NumberRange.new(0.85, 1),
        Rotation = NumberRange.new(0, 360), Rate = 0,
    }))
    -- the body: black smoke, embers, and red eyes
    local bodyAtt = attachment("Body", center, Vector3.new(0, -0.5, 0))
    idle(emitter(bodyAtt, {
        Name = "BodySmoke", Texture = TEX.Smoke, Color = ColorSequence.new(BLACK, DEEP), LightEmission = 0, LightInfluence = 0.2,
        Size = seq({ { 0, 2.2 }, { 1, 6 } }), Transparency = seq({ { 0, 1 }, { 0.2, 0.35 }, { 1, 1 } }), Lifetime = NumberRange.new(1.4, 2.2),
        Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(20, 20), EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 3, 0),
        Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-30, 30), Rate = 10, Shape = Enum.ParticleEmitterShape.Box,
    }))
    idle(emitter(bodyAtt, {
        Name = "BodyEmbers", Texture = TEX.Spark, Color = ColorSequence.new(HOT, RED), LightEmission = 1, LightInfluence = 0,
        Size = seq({ { 0, 0.35 }, { 1, 0 } }), Transparency = seq({ { 0, 0.1 }, { 1, 1 } }), Lifetime = NumberRange.new(1, 2),
        Speed = NumberRange.new(2, 6), SpreadAngle = Vector2.new(30, 30), EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 4, 0), Rate = 14,
    }))
    local head = root.Parent and root.Parent:WaitForChild("Head", 4)
    if eyes and head and head:IsA("BasePart") then
        for _, side in { -1, 1 } do
            local eye = Instance.new("Attachment")
            eye.Name = "Eye"
            eye.Position = Vector3.new(0.27 * side, 0.12, -0.6)
            eye.Parent = head
            idle(emitter(eye, {
                Name = "EyeGlow", Texture = TEX.Glow, Color = ColorSequence.new(HOT, RED), LightEmission = 1, LightInfluence = 0, Brightness = 3, LockedToPart = true,
                Size = NumberSequence.new(0.8), Transparency = seq({ { 0, 1 }, { 0.15, 0.1 }, { 0.8, 0.2 }, { 1, 1 } }), Lifetime = NumberRange.new(0.9, 1.1), Speed = NumberRange.new(0), Rate = 3,
            }))
        end
    end

    -- the lightning: a pool of bolts, each a head part that is walked along a jagged path with a black core trail and a red glow trail behind it
    local function makeBolt(lingering)
        local headPart = speck("BoltHead")
        local a0 = attachment("A0", headPart, Vector3.new(0, 0.45, 0))
        local a1 = attachment("A1", headPart, Vector3.new(0, -0.45, 0))
        local life = (if lingering then 1.6 else 0.36) / speed
        local core = Instance.new("Trail")
        core.Name = "Core"
        core.Attachment0, core.Attachment1 = a0, a1
        core.Color = ColorSequence.new(BLACK)
        core.LightEmission, core.LightInfluence = 0, 0
        core.Lifetime = life
        core.FaceCamera = true
        core.Texture = TEX.SoftGlow
        core.TextureMode = Enum.TextureMode.Stretch
        core.MinLength = 0.05
        core.Transparency = seq({ { 0, 0.02 }, { 0.65, 0.12 }, { 1, 1 } })
        core.WidthScale = seq(if lingering then { { 0, 3.4 }, { 1, 1.4 } } else { { 0, 3.0 }, { 1, 1.0 } })
        core.Enabled = false
        core.Parent = headPart
        local glow = Instance.new("Trail")
        glow.Name = "Glow"
        glow.Attachment0, glow.Attachment1 = a0, a1
        glow.Color = ColorSequence.new(Color3.fromRGB(255, 150, 120), RED)
        glow.LightEmission, glow.LightInfluence = 1, 0
        glow.Lifetime = life
        glow.FaceCamera = true
        glow.Texture = TEX.SoftGlow
        glow.TextureMode = Enum.TextureMode.Stretch
        glow.MinLength = 0.05
        glow.Transparency = seq({ { 0, 0.0 }, { 0.6, 0.25 }, { 1, 1 } })
        glow.WidthScale = seq(if lingering then { { 0, 1.5 }, { 1, 0.5 } } else { { 0, 1.7 }, { 1, 0.5 } })
        glow.Enabled = false
        glow.Parent = headPart
        return { head = headPart, core = core, glow = glow, active = false, pts = nil, n = 0, t = 0, dur = 0.14, lingering = lingering }
    end
    local bolts, cracks = {}, {}
    for _ = 1, BOLTS do
        table.insert(bolts, makeBolt(false))
    end
    for _ = 1, CRACKS do
        table.insert(cracks, makeBolt(true))
    end
    local function fireBolt(bolt, pts, duration)
        bolt.pts, bolt.n, bolt.t, bolt.dur, bolt.active = pts, #pts, 0, duration, true
        bolt.head.CFrame = CFrame.new(pts[1])
        bolt.core.Enabled = true
        bolt.glow.Enabled = true
    end
    local function freeBolt(pool)
        for _, b in pool do
            if not b.active then
                return b
            end
        end
        return nil
    end

    -- the spikes: straight tapering shards from the body outward
    local spikes = {}
    local spikeColour = ColorSequence.new({ ColorSequenceKeypoint.new(0, BLACK), ColorSequenceKeypoint.new(0.55, DEEP), ColorSequenceKeypoint.new(1, RED) })
    for i = 1, SPIKES do
        local base = attachment("SpikeBase" .. i, center, Vector3.new(0, 1.2, 0))
        local tip = attachment("SpikeTip" .. i, center, Vector3.new(0, 1.2, 0))
        local beam = Instance.new("Beam")
        beam.Name = "Spike" .. i
        beam.Attachment0, beam.Attachment1 = base, tip
        beam.Color = spikeColour
        beam.LightEmission = 0.3
        beam.LightInfluence = 0
        beam.FaceCamera = true
        beam.Segments = 1
        beam.Width0, beam.Width1 = 0.85, 0
        beam.Transparency = NumberSequence.new(0.05)
        beam.Enabled = false
        beam.Parent = center
        table.insert(spikes, { beam = beam, tip = tip, base = base, active = false, dir = Vector3.yAxis, len = 10, t = 0 })
    end

    -- sounds
    local sounds = {}
    local function newSound(name, id, volume, looped)
        local s = Instance.new("Sound")
        s.Name = name
        s.SoundId = id
        s.Volume = volume
        s.Looped = looped or false
        s.RollOffMode = Enum.RollOffMode.InverseTapered
        s.RollOffMinDistance = 25
        s.RollOffMaxDistance = 160
        s.Parent = center
        return s
    end
    local stormLoop, gatherSound, boom, split
    local strikes = {}
    if useSounds then
        stormLoop = newSound("StormLoop", SOUND.Storm, 0, true)
        gatherSound = newSound("Gather", SOUND.Gather, 1.1)
        boom = newSound("Boom", SOUND.Boom, 1.3)
        split = newSound("Split", SOUND.Split, 0.9)
        for k = 1, 3 do
            table.insert(strikes, newSound("Strike" .. k, SOUND.Strike, 0.5))
        end
    end
    local strikeNext = 0
    local function crack(volume, pitch)
        if #strikes == 0 then
            return
        end
        strikeNext = strikeNext % #strikes + 1
        local s = strikes[strikeNext]
        s.Volume = volume
        s.PlaybackSpeed = pitch
        s:Play()
    end

    -- the screen grade, driven by how near the viewer is
    local grade
    if useGrade then
        grade = Instance.new("ColorCorrectionEffect")
        grade.Name = "BlackTempestGrade"
        grade.Parent = Lighting
    end
    local gradeStrength = 0

    folder.Parent = Workspace

    -- ---------- the clock ----------
    local clock = 0
    local phase = "idle" -- "gather" while the darkness is drawn in
    local phaseStart = -100
    local nextBolt, nextSpike, nextCrack, nextFlash, nextSurge = 0, 0, 0, 0, math.huge
    local groundY = root.Position.Y - 3
    local nextGround = 0
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { folder, root.Parent }

    local function groundAt(x, z, fallback)
        local hit = Workspace:Raycast(Vector3.new(x, fallback + 10, z), Vector3.new(0, -50, 0), rayParams)
        return if hit then hit.Position.Y else fallback
    end

    local function lightFlash(amount, fade)
        if reduced then
            return
        end
        cloudLight.Brightness = amount
        TweenService:Create(cloudLight, TweenInfo.new(fade, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
    end

    local function shake(amount, seconds)
        if not useShake then
            return
        end
        local camera = Workspace.CurrentCamera
        if not camera or (camera.CFrame.Position - center.Position).Magnitude > REACH * 1.2 then
            return
        end
        local started = os.clock()
        local name = "BlackTempestShake"
        RunService:UnbindFromRenderStep(name)
        RunService:BindToRenderStep(name, Enum.RenderPriority.Camera.Value + 1, function()
            local t = os.clock() - started
            if t > seconds then
                RunService:UnbindFromRenderStep(name)
                return
            end
            local k = amount * (1 - t / seconds)
            camera.CFrame *= CFrame.new((math.random() - 0.5) * k, (math.random() - 0.5) * k, 0)
        end)
    end

    -- a bolt out of the body: low and wide, or climbing into the cloud; sometimes it forks
    local function strikeBolt(azimuth, elevation, length, allowFork)
        local bolt = freeBolt(bolts)
        if not bolt then
            return
        end
        local origin = center.Position + Vector3.new(0, 1.5, 0)
        local dir = direction(azimuth, elevation)
        local pts = boltPath(origin, dir, length, 8, 0.075)
        fireBolt(bolt, pts, 0.14)
        if allowFork and math.random() < 0.45 then
            local branch = freeBolt(bolts)
            if branch then
                local k = math.random(3, 5)
                local turn = azimuth + (if math.random() < 0.5 then -1 else 1) * rand(0.5, 0.9)
                local bdir = direction(turn, elevation + rand(-0.2, 0.3))
                fireBolt(branch, boltPath(pts[k], bdir, length * rand(0.3, 0.5), 5, 0.1), 0.1)
            end
        end
    end
    local function strikeCrack(azimuth, length)
        local crackBolt = freeBolt(cracks)
        if not crackBolt then
            return
        end
        local pts = {}
        local steps = 10
        local dir = direction(azimuth, 0)
        local side = Vector3.new(-dir.Z, 0, dir.X)
        for k = 0, steps do
            local f = k / steps
            local p = center.Position + dir * (length * f) + side * ((math.random() - 0.5) * length * 0.1 * (if k == 0 then 0 else 1))
            table.insert(pts, Vector3.new(p.X, groundAt(p.X, p.Z, groundY) + 0.25, p.Z))
        end
        fireBolt(crackBolt, pts, 0.32)
    end
    local function stab(azimuth, elevation, length)
        for _, s in spikes do
            if not s.active then
                s.active, s.t, s.dir, s.len = true, 0, direction(azimuth, elevation), length
                s.base.Position = Vector3.new(0, 1.2, 0) + direction(azimuth + 1.6, 0) * rand(0, 0.5)
                s.tip.Position = s.base.Position
                s.beam.Enabled = true
                return
            end
        end
    end

    local function rupture(big)
        -- every spike and a ring of bolts at once, in all directions
        local golden = 2.39996
        for i = 1, #spikes do
            local f = (i - 0.5) / #spikes
            stab(i * golden, math.asin(math.clamp(-0.05 + f * 0.95, -0.2, 1)), rand(16, 30) * scale * (if big then 1.2 else 1))
        end
        local ring = math.min(#bolts, if big then 8 else 5)
        for i = 1, ring do
            strikeBolt(i * (math.pi * 2 / ring) + rand(-0.2, 0.2), rand(0.0, 0.25), rand(26, 40) * scale, false)
        end
        for i = 1, math.min(#cracks, 4) do
            strikeCrack(i * (math.pi * 2 / 4) + rand(-0.4, 0.4), rand(30, 44) * scale)
        end
        shock:Emit(1)
        cloudFlash:Emit(if reduced then 1 else 3)
        lightFlash(if big then 10 else 7, 0.7)
        shake(if big then 0.8 else 0.5, 0.45)
        if gradeStrength > 0 and grade then
            grade.Brightness = 0.12 -- a flash of the screen; the grade settles back on the next frames
        end
        if useSounds then
            boom.PlaybackSpeed = rand(0.85, 1)
            boom:Play()
            crack(0.9, rand(0.85, 1))
            if big then
                split.TimePosition = 1.3
                split:Play()
            end
        end
    end

    local function awaken()
        phase, phaseStart = "gather", clock
        for _, e in idleEmitters do
            e.Enabled = false
        end
        gatherEmitter.Rate = 95 * RATE
        if useSounds then
            gatherSound:Play()
            stormLoop.Volume = 0
            stormLoop:Play()
        end
        nextSurge = math.huge
    end

    -- ---------- the loop ----------
    local connection
    connection = RunService.RenderStepped:Connect(function(rawDt)
        if not root.Parent then
            return
        end
        local dt = rawDt * speed
        clock += dt
        local rootPos = root.Position
        center.CFrame = CFrame.new(rootPos)
        if clock >= nextGround then
            nextGround = clock + 0.6
            groundY = groundAt(rootPos.X, rootPos.Z, rootPos.Y - 3)
        end
        ground.CFrame = CFrame.new(rootPos.X, groundY + 0.1, rootPos.Z)
        cloud.CFrame = CFrame.new(rootPos.X, groundY + 27 * scale, rootPos.Z)
        gather.CFrame = CFrame.new(rootPos.X, groundY + 8, rootPos.Z)

        -- the awakening, then the idle storm
        local t = clock - phaseStart
        if phase == "gather" then
            if t >= GATHER then
                phase = "idle"
                gatherEmitter.Rate = 0
                for _, e in idleEmitters do
                    e.Enabled = true
                end
                rupture(true)
                nextBolt, nextSpike, nextCrack, nextFlash = clock + 0.5, clock + 0.3, clock + 1.2, clock + 1
                nextSurge = clock + gap + rand(-3, 3)
                TweenService:Create(ambientLight, TweenInfo.new(2.5), { Brightness = if reduced then 0.6 else 1.1 }):Play()
                if useSounds then
                    TweenService:Create(stormLoop, TweenInfo.new(2.5), { Volume = if reduced then 0.25 else 0.5 }):Play()
                end
            elseif useSounds and not reduced and math.random() < 0.02 then
                lightFlash(rand(1.5, 3), 0.3) -- thunder flickering in the gathering dark
            end
        elseif phase == "idle" then
            if clock >= nextBolt then
                nextBolt = clock + rand(0.22, 0.8) / (if low then 0.7 else 1)
                local up = math.random() < 0.38
                strikeBolt(rand(0, math.pi * 2), if up then rand(0.5, 1.25) else rand(-0.08, 0.3), rand(14, 40) * scale, true)
                if useSounds and math.random() < 0.3 then
                    crack(rand(0.25, 0.5), rand(0.9, 1.2))
                end
            end
            if clock >= nextSpike then
                nextSpike = clock + rand(0.12, 0.45)
                stab(rand(0, math.pi * 2), if math.random() < 0.5 then rand(-0.05, 0.3) else rand(0.3, 1.3), rand(8, 22) * scale)
            end
            if clock >= nextCrack then
                nextCrack = clock + rand(1.2, 2.6)
                strikeCrack(rand(0, math.pi * 2), rand(18, 40) * scale)
            end
            if clock >= nextFlash and not reduced then
                nextFlash = clock + rand(0.6, 2.2)
                cloudFlash:Emit(1)
                lightFlash(rand(2.5, 5), 0.35)
            end
            if clock >= nextSurge then
                nextSurge = clock + gap + rand(-4, 4)
                rupture(false)
            end
        end

        -- the bolts walk their paths
        for _, pool in { bolts, cracks } do
            for _, b in pool do
                if b.active then
                    b.t += dt
                    local idx = math.min(b.n, 1 + math.floor(b.t / b.dur * (b.n - 1) + 0.5))
                    b.head.CFrame = CFrame.new(b.pts[idx])
                    if b.t >= b.dur then
                        b.core.Enabled = false
                        b.glow.Enabled = false
                        b.active = false
                    end
                end
            end
        end
        -- the spikes stab out, hold, snap back
        for _, s in spikes do
            if s.active then
                s.t += dt
                local grow, hold, back = 0.06, 0.1, 0.14
                local k
                if s.t < grow then
                    k = easeOut(s.t / grow)
                elseif s.t < grow + hold then
                    k = 1
                elseif s.t < grow + hold + back then
                    k = 1 - (s.t - grow - hold) / back
                else
                    s.active = false
                    s.beam.Enabled = false
                    k = 0
                end
                if s.active then
                    s.tip.Position = s.base.Position + s.dir * (s.len * k)
                end
            end
        end

        -- the screen grade: darker and redder the nearer the viewer is, and only once the dark has begun to gather
        if grade then
            local camera = Workspace.CurrentCamera
            local near = 0
            if camera then
                near = math.clamp(1 - ((camera.CFrame.Position - rootPos).Magnitude - REACH * 0.5) / (REACH * 1.6), 0, 1)
            end
            local ramp = if phase == "gather" then math.clamp(t / GATHER, 0, 1) else 1
            local target = near * ramp
            gradeStrength += (target - gradeStrength) * math.min(1, dt * 3)
            local s = gradeStrength
            grade.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(255, 224, 224), s)
            grade.Brightness += (-0.045 * s - grade.Brightness) * math.min(1, dt * 7)
            grade.Contrast = 0.1 * s
            grade.Saturation = -0.18 * s
        end
    end)

    awaken()

    local handle = {}
    function handle.awaken()
        awaken()
    end
    function handle.surge()
        if phase == "idle" then
            rupture(false)
        end
    end
    function handle.destroy()
        if connection then
            connection:Disconnect()
            connection = nil
        end
        RunService:UnbindFromRenderStep("BlackTempestShake")
        folder:Destroy()
        if grade then
            grade:Destroy()
        end
    end
    function handle.info()
        return { Phase = phase, Clock = clock, Grade = gradeStrength, NextSurge = nextSurge - clock }
    end
    return handle
end

return BlackTempest
